"""Fetch remaining DICOM slices via ranged reads on the signed bundle URL.

The competition bundle (570GB zip) lives on GCS behind a signed URL that
honors Range requests. This pulls ONLY the members we need (the labeled
studies' slices, ~1GB) with zero Kaggle API traffic — the per-file API path
is rate-limited and structurally slow (one API mint + cold GCS connection
per 500KB file); this path is one signed URL + ranged GCS reads.

URL provenance: captured from the browser's Download All click (cookie
session), saved in data/rsna_bundle_url.txt. Signed URLs expire (~6h) — on
HTTP 4xx, re-mint via the browser and update the file.

Usage:
  python tools/fetch_from_bundle.py [--workers 4] [--dest data/dicom]
"""

from __future__ import annotations

import argparse
import json
import queue
import sys
import threading
from pathlib import Path

from remotezip import RemoteZip

BUNDLE_URL_FILE = Path("data/rsna_bundle_url.txt")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dest", type=Path, default=Path("data/dicom"))
    p.add_argument("--workers", type=int, default=4)
    p.add_argument(
        "--jobs", type=Path, default=None, help="jobs json (default <dest>/jobs.json)"
    )
    args = p.parse_args()

    url = BUNDLE_URL_FILE.read_text().strip()
    jobs_file = args.jobs if args.jobs else args.dest / "jobs.json"
    jobs = json.loads(jobs_file.read_text())

    todo = []
    for member, dest_str, expect in jobs:
        dest = Path(dest_str)
        if not (dest.exists() and dest.stat().st_size == expect):
            todo.append((member, dest, expect))
    print(f"{len(jobs)} slices total; {len(todo)} to fetch", flush=True)
    if not todo:
        print("DONE: nothing to fetch", flush=True)
        return 0

    q: queue.Queue = queue.Queue()
    for item in todo:
        q.put(item)
    ok, fail = [], []
    lock = threading.Lock()

    def worker() -> None:
        # one RemoteZip per thread: each keeps its own connection; the
        # central directory is fetched per instance (~100MB for 820K
        # entries) — accepted cost, amortized over the whole run
        try:
            rz = RemoteZip(url)
        except Exception as e:  # noqa: BLE001
            with lock:
                fail.append(("<open>", str(e)))
            return
        while True:
            try:
                member, dest, expect = q.get_nowait()
            except queue.Empty:
                return
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with (
                    rz.open(member) as src,
                    open(dest.with_suffix(".part"), "wb") as out,
                ):
                    while chunk := src.read(1 << 20):
                        out.write(chunk)
                got = dest.with_suffix(".part").stat().st_size
                if got != expect:
                    raise OSError(f"size mismatch: got {got}, want {expect}")
                dest.with_suffix(".part").rename(dest)
                with lock:
                    ok.append(member)
                    if len(ok) % 100 == 0:
                        print(f"  {len(ok)}/{len(todo)} fetched", flush=True)
            except Exception as e:  # noqa: BLE001
                with lock:
                    fail.append((member, str(e)))

    threads = [threading.Thread(target=worker) for _ in range(args.workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"DONE: {len(ok)} fetched, {len(fail)} failed", flush=True)
    for m, e in fail[:5]:
        print(f"  FAIL {m[-40:]}: {e[:120]}", file=sys.stderr, flush=True)
    return 0 if not fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
