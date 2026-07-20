from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BACKEND_DIR = Path(__file__).parent
DEFAULT_OUT_DIR = BACKEND_DIR / "docbank_pdfs"

# DocBank (https://github.com/doc-analysis/DocBank) is a document-layout-analysis
# dataset built from arXiv papers. The full 500k-page dataset is only distributed
# via HuggingFace, but the repo ships a 100-sample preview directly in git. Each
# sample page has two PDF renders: "_black" (the plain document, as it would
# actually appear) and "_color" (the same page with each word's text recolored
# uniquely, used internally by DocBank to align OCR output to layout boxes). We
# only want one PDF per document to benchmark real-world extraction, so this
# fetches the "_black" variant.
API_LISTING_URL = (
    "https://api.github.com/repos/doc-analysis/DocBank/contents/"
    "DocBank_samples/DocBank_samples?per_page=1000"
)
MAX_AVAILABLE = 100  # size of the sample directory; there is no larger set on GitHub


def list_pdf_files() -> list[dict]:
    req = urllib.request.Request(API_LISTING_URL, headers={"User-Agent": "fetch-docbank-pdfs"})
    with urllib.request.urlopen(req) as resp:
        entries = json.load(resp)
    return [e for e in entries if e["name"].endswith("_black.pdf")]


def fetch_one(entry: dict, out_dir: Path) -> str:
    req = urllib.request.Request(entry["download_url"], headers={"User-Agent": "fetch-docbank-pdfs"})
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
    (out_dir / entry["name"]).write_bytes(data)
    return entry["name"]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=MAX_AVAILABLE,
                         help=f"Number of .pdf files to save (default: all {MAX_AVAILABLE} available)")
    parser.add_argument("--out-dir", type=str, default=str(DEFAULT_OUT_DIR), help="Directory to write .pdf files to")
    parser.add_argument("--workers", type=int, default=8, help="Concurrent download threads (default: 8)")
    args = parser.parse_args()

    if args.count > MAX_AVAILABLE:
        print(f"Note: only {MAX_AVAILABLE} DocBank sample .pdf files are available on GitHub "
              f"(the full dataset is HuggingFace-only); capping --count at {MAX_AVAILABLE}.")
        args.count = MAX_AVAILABLE

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    already = {p.name for p in out_dir.glob("*.pdf")}
    if len(already) >= args.count:
        print(f"{out_dir} already has {len(already)} files (>= --count {args.count}); nothing to do.")
        return

    print("Listing available DocBank sample files ...")
    try:
        entries = list_pdf_files()
    except Exception as e:
        print(f"Error: failed to list DocBank files from GitHub: {e}", file=sys.stderr)
        sys.exit(1)

    entries = [e for e in entries if e["name"] not in already][: args.count - len(already)]
    print(f"Fetching {len(entries)} DocBank .pdf file(s) into {out_dir} ...")

    saved = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch_one, entry, out_dir): entry for entry in entries}
        for future in as_completed(futures):
            entry = futures[future]
            try:
                future.result()
                saved += 1
                if saved % 10 == 0 or saved == len(entries):
                    print(f"  [{saved}/{len(entries)}] saved")
            except Exception as e:
                print(f"  warning: failed to fetch {entry['name']}: {e}", file=sys.stderr)

    print(f"Done. {saved} new file(s) saved, {len(already) + saved} total in {out_dir}.")


if __name__ == "__main__":
    main()
