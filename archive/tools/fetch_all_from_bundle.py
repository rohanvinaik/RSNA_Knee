"""Fetch every DICOM of the competition into data/ by ranged reads on the signed bundle URL (operational).

The bundle is one zip on GCS (265 GB compressed, about 570 GB unpacked). Nothing is downloaded whole: the central
directory is read once through a buffered ranged reader, then each member is fetched by its own ranged GET,
inflated, and checked against the CRC and size in the central directory before it is renamed into place.

- Layout: each member lands at data/<member path>, so data/train_series/<study>/<series>/<slice>.dcm mirrors the
  competition's own layout. The existing CSVs in data/ are not touched.
- Order: the 58 labeled studies first, then the example test studies, then the rest of the training studies.
- Resume: a member whose file already exists with the right size is skipped, so a rerun continues where it stopped.
- Expiry: on HTTP 400/401/403 the URL is re-minted with tools/mint_bundle_url.py, at most once per five minutes.
- Disk: the run stops cleanly when free space falls below 60 GB.
- Lease: the PID is in data/fetch_all.pid while the run lives, progress in data/fetch_all.log, failures in
  data/fetch_all.failed. Stop it with: kill "$(cat data/fetch_all.pid)".

Neither the token nor the URL is ever printed.

Usage (from the repo root): .venv/bin/python -u tools/fetch_all_from_bundle.py [--labeled-only]
With --labeled-only, only the labeled studies' slices are fetched (the founder, 2026-10-10: "we can just get the
labeled ones").
"""

from __future__ import annotations

import csv
import http.client
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.parse
import zipfile
import zlib
from pathlib import Path

DATA = Path("data")
URL_FILE = DATA / "rsna_bundle_url.txt"
PID_FILE = DATA / "fetch_all.pid"
FAILED_FILE = DATA / "fetch_all.failed"
WORKERS = int(os.environ.get("FETCH_WORKERS", "16"))
STOP_FREE_BYTES = 60 * 10**9
READ_AHEAD = 8 << 20
REMINT_MIN_INTERVAL_S = 300


class Expired(Exception):
    """The signed URL answered with a client error: it has expired or been refused."""


class RangedHTTP:
    """One keep-alive HTTPS connection doing Range GETs against the current signed URL."""

    def __init__(self, url: str) -> None:
        self.set_url(url)

    def set_url(self, url: str) -> None:
        parts = urllib.parse.urlsplit(url)
        self.host = parts.hostname or ""
        self.path = parts.path + ("?" + parts.query if parts.query else "")
        self.conn: http.client.HTTPSConnection | None = None

    def get(self, start: int, end_inclusive: int) -> bytes:
        for attempt in range(6):
            try:
                if self.conn is None:
                    self.conn = http.client.HTTPSConnection(self.host, timeout=120)
                self.conn.request("GET", self.path, headers={"Range": f"bytes={start}-{end_inclusive}"})
                resp = self.conn.getresponse()
                body = resp.read()
                if resp.status == 206:
                    return body
                if resp.status in (400, 401, 403):
                    raise Expired(str(resp.status))
                raise OSError(f"HTTP {resp.status}")
            except Expired:
                raise
            except (OSError, http.client.HTTPException):
                self.conn = None
                time.sleep(min(30, 2 ** attempt))
        raise OSError("ranged GET failed after retries")


class RangedFile:
    """A read-only, seekable file over the bundle, with a read-ahead buffer, so zipfile can read the directory."""

    def __init__(self, http_: RangedHTTP) -> None:
        self.http = http_
        self.size = self._total_size()
        self.pos = 0
        self.buf_start = 0
        self.buf = b""

    def _total_size(self) -> int:
        self.http.conn = self.http.conn or http.client.HTTPSConnection(self.http.host, timeout=120)
        self.http.conn.request("GET", self.http.path, headers={"Range": "bytes=0-0"})
        resp = self.http.conn.getresponse()
        resp.read()
        if resp.status != 206:
            raise Expired(str(resp.status))
        return int(resp.headers["Content-Range"].rpartition("/")[2])

    def seekable(self) -> bool:
        return True

    def readable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, offset: int, whence: int = 0) -> int:
        base = {0: 0, 1: self.pos, 2: self.size}[whence]
        self.pos = max(0, base + offset)
        return self.pos

    def read(self, n: int = -1) -> bytes:
        if n is None or n < 0:
            n = self.size - self.pos
        n = min(n, self.size - self.pos)
        if n <= 0:
            return b""
        lo, hi = self.pos, self.pos + n
        if not (self.buf_start <= lo and hi <= self.buf_start + len(self.buf)):
            end = min(self.size, lo + max(n, READ_AHEAD))
            self.buf = self.http.get(lo, end - 1)
            self.buf_start = lo
        out = self.buf[lo - self.buf_start : hi - self.buf_start]
        self.pos = hi
        return out


def labeled_studies() -> set[str]:
    csv.field_size_limit(10**9)
    out: set[str] = set()
    with open(DATA / "train.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["Medial Meniscus"].strip() not in ("", "nan", "NaN"):
                out.add(row["StudyInstanceUID"])
    return out


def safe_dest(name: str) -> Path:
    parts = Path(name).parts
    if Path(name).is_absolute() or ".." in parts:
        raise ValueError(f"unsafe member path: {name}")
    return DATA.joinpath(*parts)


def member_bytes(http_: RangedHTTP, zi: zipfile.ZipInfo) -> bytes:
    name_len = len(zi.orig_filename.encode("utf-8"))
    first = http_.get(zi.header_offset, zi.header_offset + 30 + name_len + 1024 + zi.compress_size - 1)
    if first[:4] != b"PK\x03\x04":
        raise OSError("bad local header signature")
    n = int.from_bytes(first[26:28], "little")
    m = int.from_bytes(first[28:30], "little")
    start = 30 + n + m
    need = start + zi.compress_size
    if len(first) < need:
        first += http_.get(zi.header_offset + len(first), zi.header_offset + need - 1)
    data = first[start:need]
    if zi.compress_type == zipfile.ZIP_STORED:
        raw = data
    elif zi.compress_type == zipfile.ZIP_DEFLATED:
        d = zlib.decompressobj(-15)
        raw = d.decompress(data) + d.flush()
    else:
        raise OSError(f"unsupported compression {zi.compress_type}")
    if len(raw) != zi.file_size or zlib.crc32(raw) != zi.CRC:
        raise OSError("size or CRC mismatch")
    return raw


class Run:
    def __init__(self, todo: list[zipfile.ZipInfo]) -> None:
        self.todo = todo
        self.next = 0
        self.lock = threading.Lock()
        self.url = URL_FILE.read_text(encoding="utf-8").strip()
        self.url_version = 0
        self.last_mint = 0.0
        self.done = 0
        self.bytes = 0
        self.failed = 0
        self.stop = threading.Event()
        self.started = time.monotonic()

    def take(self) -> zipfile.ZipInfo | None:
        with self.lock:
            if self.stop.is_set() or self.next >= len(self.todo):
                return None
            zi = self.todo[self.next]
            self.next += 1
            return zi

    def remint(self, seen_version: int) -> None:
        with self.lock:
            if self.url_version != seen_version:
                return
            wait = REMINT_MIN_INTERVAL_S - (time.monotonic() - self.last_mint)
            if wait > 0:
                time.sleep(wait)
            result = subprocess.run(
                [sys.executable, "tools/mint_bundle_url.py"], capture_output=True, text=True, check=False
            )
            print("remint:", result.stdout.strip().replace("\n", " | "), flush=True)
            self.url = URL_FILE.read_text(encoding="utf-8").strip()
            self.url_version += 1
            self.last_mint = time.monotonic()

    def worker(self) -> None:
        version = self.url_version
        http_ = RangedHTTP(self.url)
        since_disk_check = 0
        while (zi := self.take()) is not None:
            if version != self.url_version:
                version = self.url_version
                http_.set_url(self.url)
            dest = safe_dest(zi.filename)
            last = "the signed URL kept answering with a client error"
            for _ in range(3):
                try:
                    raw = member_bytes(http_, zi)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    part = dest.with_name(dest.name + ".part")
                    part.write_bytes(raw)
                    part.rename(dest)
                    with self.lock:
                        self.done += 1
                        self.bytes += len(raw)
                    break
                except Expired:
                    self.remint(version)
                    version = self.url_version
                    http_.set_url(self.url)
                except (OSError, ValueError) as e:
                    last = str(e)
                    time.sleep(1)
            else:
                with self.lock:
                    self.failed += 1
                    with open(FAILED_FILE, "a", encoding="utf-8") as f:
                        f.write(f"{zi.filename}\t{last[:200]}\n")
            since_disk_check += 1
            if since_disk_check >= 200:
                since_disk_check = 0
                if shutil.disk_usage(DATA).free < STOP_FREE_BYTES:
                    print("STOP: free space below 60 GB", flush=True)
                    self.stop.set()

    def report(self) -> None:
        while not self.stop.wait(60):
            self.print_progress()

    def print_progress(self) -> None:
        with self.lock:
            done, nbytes, failed, total = self.done, self.bytes, self.failed, len(self.todo)
        elapsed = max(1.0, time.monotonic() - self.started)
        rate = done / elapsed
        eta_min = (total - done - failed) / rate / 60 if rate > 0 else float("inf")
        free_gb = shutil.disk_usage(DATA).free / 1e9
        print(
            f"{done}/{total} files ({nbytes / 1e9:.1f} GB) | {failed} failed | {rate:.0f} files/s | "
            f"ETA {eta_min:.0f} min | free {free_gb:.0f} GB",
            flush=True,
        )


def main() -> int:
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    try:
        url = URL_FILE.read_text(encoding="utf-8").strip()
        directory = zipfile.ZipFile(RangedFile(RangedHTTP(url)))
        infos = [zi for zi in directory.infolist() if zi.filename.endswith(".dcm")]
        print(f"bundle: {len(infos)} DICOM members, {sum(z.file_size for z in infos) / 1e9:.1f} GB unpacked", flush=True)
        print("first members:", ", ".join(z.filename[:60] for z in infos[:2]), flush=True)
        labeled = labeled_studies()

        def priority(zi: zipfile.ZipInfo) -> int:
            parts = zi.filename.split("/")
            if any(p in labeled for p in parts):
                return 0
            return 1 if "test_series" in parts else 2

        todo = [z for z in infos if not (safe_dest(z.filename).exists() and safe_dest(z.filename).stat().st_size == z.file_size)]
        todo.sort(key=priority)
        if "--labeled-only" in sys.argv[1:]:
            todo = [z for z in todo if priority(z) == 0]
            print("labeled studies only", flush=True)
        print(f"to fetch: {len(todo)} (labeled studies first: {sum(1 for z in todo if priority(z) == 0)})", flush=True)
        run = Run(todo)
        threads = [threading.Thread(target=run.worker, daemon=True) for _ in range(WORKERS)]
        reporter = threading.Thread(target=run.report, daemon=True)
        for t in threads:
            t.start()
        reporter.start()
        for t in threads:
            t.join()
        run.stop.set()
        run.print_progress()
        print("DONE" if run.failed == 0 and run.next >= len(todo) else "STOPPED with work left; rerun to resume", flush=True)
        return 0 if run.failed == 0 else 1
    finally:
        PID_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
