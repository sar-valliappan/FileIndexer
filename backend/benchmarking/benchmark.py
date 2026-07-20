import argparse
import csv
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).parent
sys.path.insert(0, str(BACKEND_DIR.parent))

from config import Settings
from indexer import Indexer

RESULTS_DIR = BACKEND_DIR / "benchmarks"
RESULTS_CSV = RESULTS_DIR / "results.csv"
RESULTS_MD = RESULTS_DIR / "results.md"

CORPORA = {
    "txt": (BACKEND_DIR / "gutenberg_texts", [".txt"]),
    "pdf": (BACKEND_DIR / "docbank_pdfs", [".pdf"]),
}

CSV_FIELDS = [
    "timestamp", "commit", "branch", "note", "corpus",
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


def instrument(indexer: Indexer, times: StageTimes, counts: dict, num_files: int, verbose: bool) -> None:
    """Wrap the real Indexer's stage methods with timers, without changing its logic."""
    state = {"path": None}

    orig_process_file = indexer.file_processor.process_file

    def timed_process_file(path, *a, **kw):
        t0 = time.perf_counter()
        result = orig_process_file(path, *a, **kw)
        times.extract += time.perf_counter() - t0
        state["path"] = path
        return result

    indexer.file_processor.process_file = timed_process_file

    orig_get_file_hash = indexer.get_file_hash

    def timed_get_file_hash(file_text, *a, **kw):
        t0 = time.perf_counter()
        result = orig_get_file_hash(file_text, *a, **kw)
        times.hash += time.perf_counter() - t0
        return result

    indexer.get_file_hash = timed_get_file_hash

    orig_chunk_text = indexer.file_processor.chunk_text

    def timed_chunk_text(text, *a, **kw):
        t0 = time.perf_counter()
        chunks = orig_chunk_text(text, *a, **kw)
        times.chunk += time.perf_counter() - t0
        counts["total_chunks"] += len(chunks)
        counts["files_seen"] += 1
        path = state["path"]
        if path is not None:
            counts["total_bytes"] += path.stat().st_size
            if verbose:
                print(f"  [{counts['files_seen']}/{num_files}] {path.name}: {len(chunks)} chunks")
        return chunks

    indexer.file_processor.chunk_text = timed_chunk_text

    orig_generate_embeddings = indexer.generate_embedding.generate_embeddings

    def timed_generate_embeddings(chunks, *a, **kw):
        t0 = time.perf_counter()
        result = orig_generate_embeddings(chunks, *a, **kw)
        times.embed += time.perf_counter() - t0
        return result

    indexer.generate_embedding.generate_embeddings = timed_generate_embeddings

    orig_add = indexer.collection.add

    def timed_add(*a, **kw):
        t0 = time.perf_counter()
        result = orig_add(*a, **kw)
        times.db_add += time.perf_counter() - t0
        return result

    indexer.collection.add = timed_add


def run_benchmark(file_paths: list[Path], verbose: bool) -> dict:
    with tempfile.TemporaryDirectory() as tmp_str:
        chroma_dir = Path(tmp_str) / "chroma"
        indexer = Indexer(chroma_dir=str(chroma_dir), collection_name="benchmark")

        # Warm up the model so first-call load time doesn't skew results.
        indexer.generate_embedding.embed_query("warm up")

        times = StageTimes()
        counts = {"total_chunks": 0, "total_bytes": 0, "files_seen": 0}
        instrument(indexer, times, counts, len(file_paths), verbose)

        indexer.index_files(file_paths)

    return {
        "num_files": len(file_paths),
        "total_bytes": counts["total_bytes"],
        "total_chunks": counts["total_chunks"],
        "times": times,
    }


def print_summary(result: dict, title: str = "BENCHMARK RESULTS") -> None:
    times: StageTimes = result["times"]
    total_bytes = result["total_bytes"]
    total_chunks = result["total_chunks"]
    num_files = result["num_files"]
    total_s = times.total

    mb = total_bytes / (1024 * 1024)
    avg_chunk_chars = total_bytes / total_chunks if total_chunks else 0

    print()
    print("=" * 52)
    print(f"  {title}")
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

def log_results(result: dict, note: str = "", corpus: str = "") -> None:
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
        "corpus": corpus,
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
    ]

    corpora = sorted({r.get("corpus") or "-" for r in rows})
    for corpus in corpora:
        corpus_rows = [r for r in rows if (r.get("corpus") or "-") == corpus]
        corpus_rows.sort(key=lambda r: r["timestamp"])

        lines.append(f"## {corpus} corpus")
        lines.append("")
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join(["---"] * len(header)) + "|")
        for r in corpus_rows:
            mb = int(r["total_bytes"]) / (1024 * 1024)
            note = r.get("note") or "-"
            timestamp = datetime.fromisoformat(r["timestamp"]).strftime("%Y-%m-%d %H:%M")
            lines.append(
                "| " + " | ".join([
                    timestamp, r["commit"], note, r["num_files"],
                    f"{mb:.2f}", r["total_chunks"], r["extract_s"], r["hash_s"],
                    r["chunk_s"], r["embed_s"], r["db_add_s"], r["total_s"],
                    r["mb_per_s"], r["chunks_per_s"],
                ]) + " |"
            )
        lines.append("")
    RESULTS_MD.write_text("\n".join(lines).rstrip() + "\n")


def print_comparison(results: dict) -> None:
    """Print extract-stage times side by side across corpora, since that's the
    stage whose cost varies most by file type (e.g. .txt vs .pdf)."""
    print()
    print("=" * 52)
    print("  EXTRACTION COMPARISON")
    print("=" * 52)
    for name, result in results.items():
        times: StageTimes = result["times"]
        num_files = result["num_files"]
        per_file = times.extract / num_files if num_files else 0
        print(f"  {name:<6} extract_s: {times.extract:>8.4f}s total, "
              f"{per_file * 1000:>8.3f}ms/file ({num_files} files)")
    print("=" * 52)


def run_and_log(name: str, file_paths: list[Path], args) -> dict:
    print(f"\nBenchmarking '{name}' corpus: {len(file_paths)} file(s)")
    result = run_benchmark(file_paths, args.verbose)
    print_summary(result, title=f"BENCHMARK RESULTS ({name})")
    if not args.no_log:
        log_results(result, note=args.note, corpus=name)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", type=str, default=None,
                         help="Directory of real files to benchmark against. If omitted, runs the "
                              "named corpora selected by --corpus instead (split by file type).")
    parser.add_argument("--corpus", choices=[*CORPORA.keys(), "all"], default="all",
                         help="Which named corpus/corpora to run when --dir is not given: "
                              f"{', '.join(CORPORA.keys())}, or 'all' (default) to run each separately.")
    parser.add_argument("--num-files", type=int, default=None,
                         help="Limit to the first N matching files found per corpus (default: all)")
    parser.add_argument("--note", type=str, default="",
                         help="Description of the change being benchmarked, saved to the log")
    parser.add_argument("--no-log", action="store_true",
                         help="Print results only, don't append to benchmarks/results.csv")
    parser.add_argument("--verbose", action="store_true", help="Print per-file progress")
    args = parser.parse_args()

    if args.dir:
        settings = Settings()
        directory = Path(args.dir).expanduser().resolve()
        if not directory.is_dir():
            print(f"Error: {directory} is not a directory", file=sys.stderr)
            sys.exit(1)
        file_paths = collect_files(directory, settings.VALID_FILE_EXTENSIONS, args.num_files)
        if not file_paths:
            print(f"Error: no files with extensions {settings.VALID_FILE_EXTENSIONS} found in {directory}", file=sys.stderr)
            sys.exit(1)
        run_and_log(directory.name, file_paths, args)
        return

    names = list(CORPORA.keys()) if args.corpus == "all" else [args.corpus]
    results = {}
    for name in names:
        directory, extensions = CORPORA[name]
        if not directory.is_dir():
            print(f"Skipping '{name}' corpus: {directory} not found "
                  f"(run fetch_{'gutenberg' if name == 'txt' else 'docbank'}_*.py first)", file=sys.stderr)
            continue
        file_paths = collect_files(directory, extensions, args.num_files)
        if not file_paths:
            print(f"Skipping '{name}' corpus: no {extensions} files found in {directory}", file=sys.stderr)
            continue
        results[name] = run_and_log(name, file_paths, args)

    if not results:
        print("Error: no corpora available to benchmark.", file=sys.stderr)
        sys.exit(1)
    if len(results) > 1:
        print_comparison(results)


if __name__ == "__main__":
    main()
