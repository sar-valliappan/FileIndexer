import argparse
import csv
import hashlib
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from config import Settings
from file_processor import FileProcessor
from generate_embedding import GenerateEmbedding

BACKEND_DIR = Path(__file__).parent
RESULTS_DIR = BACKEND_DIR / "benchmarks"
RESULTS_CSV = RESULTS_DIR / "results.csv"
RESULTS_MD = RESULTS_DIR / "results.md"

CSV_FIELDS = [
    "timestamp", "commit", "branch", "note",
    "num_files", "total_bytes", "total_chunks", "avg_chunk_chars",
    "extract_s", "hash_s", "chunk_s", "embed_s", "db_add_s", "total_s",
    "mb_per_s", "chunks_per_s", "files_per_s",
]


def collect_files(directory: Path, extensions: list[str], limit: int | None) -> list[Path]:
    files = []
    for ext in extensions:
        files.extend(directory.rglob(f"*{ext}"))
    if limit:
        files = files[:limit]
    return files


def git_info() -> tuple[str, str]:
    def run(args):
        try:
            return subprocess.check_output(
                args, cwd=BACKEND_DIR, stderr=subprocess.DEVNULL
            ).decode().strip()
        except Exception:
            return "unknown"
    return run(["git", "rev-parse", "--short", "HEAD"]), run(["git", "branch", "--show-current"])


@dataclass
class StageTimes:
    extract: float = 0.0
    hash: float = 0.0
    chunk: float = 0.0
    embed: float = 0.0
    db_add: float = 0.0

    @property
    def total(self) -> float:
        return self.extract + self.hash + self.chunk + self.embed + self.db_add


def run_benchmark(file_paths: list[Path], verbose: bool) -> dict:
    processor = FileProcessor()
    embedder = GenerateEmbedding()

    with tempfile.TemporaryDirectory() as tmp_str:
        chroma_dir = Path(tmp_str) / "chroma"
        client = chromadb.PersistentClient(
            path=str(chroma_dir), settings=ChromaSettings(anonymized_telemetry=False)
        )
        collection = client.get_or_create_collection(
            name="benchmark", metadata={"hnsw:space": "cosine"}
        )

        # Warm up the model so first-call load time doesn't skew results.
        embedder.embed_query("warm up")

        times = StageTimes()
        total_chunks = 0
        total_bytes = 0

        for i, path in enumerate(file_paths):
            t0 = time.perf_counter()
            text = processor.process_file(path)
            t1 = time.perf_counter()
            times.extract += t1 - t0

            if not text or not text.strip():
                continue

            # Mirrors Indexer.get_file_hash, which re-extracts the file to hash it.
            processor.process_file(path)
            file_hash = hashlib.sha256(text.encode()).hexdigest()
            t2 = time.perf_counter()
            times.hash += t2 - t1

            chunks = processor.chunk_text(text)
            t3 = time.perf_counter()
            times.chunk += t3 - t2

            total_chunks += len(chunks)
            total_bytes += path.stat().st_size

            embeddings = embedder.generate_embeddings(chunks)
            t4 = time.perf_counter()
            times.embed += t4 - t3

            ids = [f"{path}::{idx}::{file_hash}" for idx in range(len(chunks))]
            metadatas = [{"file_path": str(path), "chunk_index": idx} for idx in range(len(chunks))]
            collection.add(documents=chunks, embeddings=embeddings, metadatas=metadatas, ids=ids)
            t5 = time.perf_counter()
            times.db_add += t5 - t4

            if verbose:
                print(f"  [{i + 1}/{len(file_paths)}] {path.name}: {len(chunks)} chunks")

    return {
        "num_files": len(file_paths),
        "total_bytes": total_bytes,
        "total_chunks": total_chunks,
        "times": times,
    }


def print_summary(result: dict) -> None:
    times: StageTimes = result["times"]
    total_bytes = result["total_bytes"]
    total_chunks = result["total_chunks"]
    num_files = result["num_files"]
    total_s = times.total

    mb = total_bytes / (1024 * 1024)
    avg_chunk_chars = total_bytes / total_chunks if total_chunks else 0

    print()
    print("=" * 52)
    print("  BENCHMARK RESULTS")
    print("=" * 52)
    print(f"  Files:              {num_files}")
    print(f"  Total size:         {mb:.2f} MB")
    print(f"  Total chunks:       {total_chunks}")
    print(f"  Avg chunk size:     {avg_chunk_chars:.0f} chars")
    print("-" * 52)
    stage_rows = [
        ("Extract text", times.extract),
        ("Hash file", times.hash),
        ("Chunk text", times.chunk),
        ("Generate embeddings", times.embed),
        ("Write to ChromaDB", times.db_add),
    ]
    for label, secs in stage_rows:
        pct = (secs / total_s * 100) if total_s else 0
        print(f"  {label:<22} {secs:>8.3f}s  ({pct:5.1f}%)")
    print("-" * 52)
    print(f"  {'TOTAL':<22} {total_s:>8.3f}s")
    print()
    if total_s > 0:
        print(f"  Throughput: {mb / total_s:.2f} MB/s | "
              f"{total_chunks / total_s:.1f} chunks/s | "
              f"{num_files / total_s:.2f} files/s")
    print("=" * 52)


def log_results(result: dict, note: str) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    times: StageTimes = result["times"]
    total_s = times.total
    total_bytes = result["total_bytes"]
    total_chunks = result["total_chunks"]
    mb = total_bytes / (1024 * 1024)
    commit, branch = git_info()

    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "commit": commit,
        "branch": branch,
        "note": note,
        "num_files": result["num_files"],
        "total_bytes": total_bytes,
        "total_chunks": total_chunks,
        "avg_chunk_chars": round(total_bytes / total_chunks, 1) if total_chunks else 0,
        "extract_s": round(times.extract, 4),
        "hash_s": round(times.hash, 4),
        "chunk_s": round(times.chunk, 4),
        "embed_s": round(times.embed, 4),
        "db_add_s": round(times.db_add, 4),
        "total_s": round(total_s, 4),
        "mb_per_s": round(mb / total_s, 3) if total_s else 0,
        "chunks_per_s": round(total_chunks / total_s, 2) if total_s else 0,
        "files_per_s": round(result["num_files"] / total_s, 3) if total_s else 0,
    }

    is_new = not RESULTS_CSV.exists()
    with open(RESULTS_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow(row)

    render_markdown()
    print(f"\nLogged to {RESULTS_CSV.relative_to(BACKEND_DIR.parent)} "
          f"and {RESULTS_MD.relative_to(BACKEND_DIR.parent)}")


def render_markdown() -> None:
    if not RESULTS_CSV.exists():
        return
    with open(RESULTS_CSV, newline="") as f:
        rows = list(csv.DictReader(f))

    header = ["timestamp", "commit", "note", "files", "MB", "chunks",
              "extract_s", "hash_s", "chunk_s", "embed_s", "db_add_s", "total_s",
              "MB/s", "chunks/s"]
    lines = [
        "# Indexing Benchmark History",
        "",
        "Generated by `backend/benchmark.py`. Do not edit by hand.",
        "",
        "| " + " | ".join(header) + " |",
        "|" + "|".join(["---"] * len(header)) + "|",
    ]
    for r in rows:
        mb = int(r["total_bytes"]) / (1024 * 1024)
        note = r["note"] or "-"
        lines.append(
            "| " + " | ".join([
                r["timestamp"], r["commit"], note, r["num_files"],
                f"{mb:.2f}", r["total_chunks"], r["extract_s"], r["hash_s"],
                r["chunk_s"], r["embed_s"], r["db_add_s"], r["total_s"],
                r["mb_per_s"], r["chunks_per_s"],
            ]) + " |"
        )
    RESULTS_MD.write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", type=str, required=True,
                         help="Directory of real files to benchmark against")
    parser.add_argument("--num-files", type=int, default=None,
                         help="Limit to the first N matching files found in --dir (default: all)")
    parser.add_argument("--note", type=str, default="",
                         help="Description of the change being benchmarked, saved to the log")
    parser.add_argument("--no-log", action="store_true",
                         help="Print results only, don't append to benchmarks/results.csv")
    parser.add_argument("--verbose", action="store_true", help="Print per-file progress")
    args = parser.parse_args()

    settings = Settings()

    directory = Path(args.dir).expanduser().resolve()
    if not directory.is_dir():
        print(f"Error: {directory} is not a directory", file=sys.stderr)
        sys.exit(1)
    file_paths = collect_files(directory, settings.VALID_FILE_EXTENSIONS, args.num_files)
    if not file_paths:
        print(f"Error: no files with extensions {settings.VALID_FILE_EXTENSIONS} found in {directory}", file=sys.stderr)
        sys.exit(1)
    print(f"Benchmarking against {len(file_paths)} real file(s) from {directory}")

    result = run_benchmark(file_paths, args.verbose)

    print_summary(result)
    if not args.no_log:
        log_results(result, args.note)


if __name__ == "__main__":
    main()
