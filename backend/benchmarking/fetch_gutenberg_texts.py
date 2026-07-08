from __future__ import annotations

import argparse
import random
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from gutenbergpy.gutenbergcachesettings import GutenbergCacheSettings
from gutenbergpy.textget import get_text_by_id, strip_headers

BACKEND_DIR = Path(__file__).parent
DEFAULT_OUT_DIR = BACKEND_DIR / "gutenberg_texts"

# Gutenberg book IDs run from 1 up to roughly this as of 2026; sampling from
# this range keeps a mix of short and long, old and new public-domain texts.
MAX_KNOWN_ID = 74000
MIN_CHARS = 500  # skip near-empty results (cover pages, missing texts, etc.)


def fetch_one(book_id: int) -> str | None:
    """Download + clean one book. Returns the text, or None if unavailable."""
    try:
        raw = get_text_by_id(book_id)
    except Exception:
        return None
    try:
        text = strip_headers(raw).decode("utf-8", errors="replace").strip()
    except Exception:
        return None
    if len(text) < MIN_CHARS:
        return None
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=500, help="Number of .txt files to save (default: 500)")
    parser.add_argument("--out-dir", type=str, default=str(DEFAULT_OUT_DIR), help="Directory to write .txt files to")
    parser.add_argument("--workers", type=int, default=8, help="Concurrent download threads (default: 8)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible sampling")
    parser.add_argument("--min-id", type=int, default=1)
    parser.add_argument("--max-id", type=int, default=MAX_KNOWN_ID)
    args = parser.parse_args()

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Cache raw downloads (gzip'd) outside the output dir so out_dir only
    # ever contains clean .txt files.
    cache_dir = out_dir.parent / ".gutenberg_raw_cache"
    GutenbergCacheSettings.TEXT_FILES_CACHE_FOLDER = str(cache_dir)

    already = {p.stem for p in out_dir.glob("*.txt")}
    needed = args.count - len(already)
    if needed <= 0:
        print(f"{out_dir} already has {len(already)} files (>= --count {args.count}); nothing to do.")
        return

    rng = random.Random(args.seed)
    candidates = list(range(args.min_id, args.max_id + 1))
    rng.shuffle(candidates)
    candidates = [c for c in candidates if str(c) not in already]

    saved = 0
    tried = 0
    lock = threading.Lock()
    print(f"Fetching {needed} more Gutenberg text(s) into {out_dir} ...")

    cand_iter = iter(candidates)

    def next_batch(n):
        batch = []
        for _ in range(n):
            try:
                batch.append(next(cand_iter))
            except StopIteration:
                break
        return batch

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending = {}
        for book_id in next_batch(args.workers * 4):
            pending[pool.submit(fetch_one, book_id)] = book_id

        while pending and saved < needed:
            for future in as_completed(list(pending)):
                book_id = pending.pop(future)
                tried += 1
                text = future.result()
                if text is not None:
                    (out_dir / f"{book_id}.txt").write_text(text, encoding="utf-8")
                    with lock:
                        saved += 1
                    if saved % 25 == 0 or saved == needed:
                        print(f"  [{saved}/{needed}] saved (book id {book_id}, {len(text)} chars, {tried} tried)")

                if saved >= needed:
                    break

                more = next_batch(1)
                for bid in more:
                    pending[pool.submit(fetch_one, bid)] = bid

                if not pending and saved < needed and not more:
                    break

    if saved < needed:
        print(f"Warning: only saved {saved}/{needed} requested files; ran out of candidate IDs "
              f"in range [{args.min_id}, {args.max_id}]. Try raising --max-id.", file=sys.stderr)
    else:
        print(f"Done. {saved} new file(s) saved, {len(already) + saved} total in {out_dir} "
              f"({tried} IDs tried).")


if __name__ == "__main__":
    main()
