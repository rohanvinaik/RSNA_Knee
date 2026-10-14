"""Fetch members of the competition's data bundle into data/raw/ by ranged reads (operational).

The bundle is one zip behind a signed URL that the Kaggle API mints. Nothing is downloaded whole: the zip's central
directory is read through a buffered ranged reader, then each selected member is fetched by its own ranged GET,
inflated, checked against the size and CRC-32 the central directory records, and renamed into place, so
data/raw/<member path> mirrors the competition's own layout. A member already on disk is kept only when its size
and CRC-32 match; otherwise it is fetched again.

Reused from archive/tools/mint_bundle_url.py and archive/tools/fetch_all_from_bundle.py (2026-10-09), which fetched
the 58 labeled studies' 10,528 slices with no failure. It reads members exactly, checked by CRC, without the 265 GB
download, so it is kept rather than rewritten; this version selects members by prefix and writes under data/raw/.

The token is KAGGLE_API_TOKEN, from the environment or ~/Projects/Kaggle_Killer/.env. Neither the token nor the
signed URL is ever printed.

Usage (from the repo root): .venv/bin/python tools/fetch_from_bundle.py <member prefix> [<member prefix> ...]
For example: .venv/bin/python tools/fetch_from_bundle.py test_series/ train.csv
"""

from __future__ import annotations

import http.client
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import zlib
from pathlib import Path

API = "https://api.kaggle.com/v1/competitions.CompetitionApiService/DownloadDataFiles"
COMPETITION = "rsna-knee-abnormality-detection"
ENV_FILE = Path.home() / "Projects" / "Kaggle_Killer" / ".env"
RAW = Path("data/raw")
READ_AHEAD = 8 << 20
REDIRECTS = (301, 302, 303, 307, 308)


class Expired(Exception):
    """The signed URL answered with a client error: it has expired or been refused."""


def token() -> str:
    tok = os.environ.get("KAGGLE_API_TOKEN", "")
    if tok:
        return tok
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition("=")
        if key.strip() == "KAGGLE_API_TOKEN":
            return value.strip().strip('"').strip("'")
    raise SystemExit("KAGGLE_API_TOKEN is in neither the environment nor the .env file")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def mint() -> str:
    """Ask the Kaggle API for the bundle without following its redirect, and return the signed URL."""
    request = urllib.request.Request(
        API,
        data=json.dumps({"competitionName": COMPETITION}).encode(),
        headers={
            "Authorization": f"Bearer {token()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        urllib.request.build_opener(_NoRedirect).open(request, timeout=60)
    except urllib.error.HTTPError as err:
        location = err.headers.get("Location", "")
        if err.code in REDIRECTS and location:
            print(
                "mint: HTTP",
                err.code,
                "| signed URL received (not printed)",
                flush=True,
            )
            return location
        raise SystemExit(f"mint failed: HTTP {err.code}") from None
    raise SystemExit("mint: the API answered without a redirect")


class RangedHTTP:
    """One keep-alive HTTPS connection doing Range GETs against the current signed URL."""

    def __init__(self, url: str) -> None:
        self.conn: http.client.HTTPSConnection | None = None
        self.set_url(url)

    def set_url(self, url: str) -> None:
        parts = urllib.parse.urlsplit(url)
        self.host = parts.hostname or ""
        self.path = parts.path + ("?" + parts.query if parts.query else "")
        self.conn = None

    def get(self, start: int, end_inclusive: int) -> bytes:
        for attempt in range(6):
            try:
                if self.conn is None:
                    self.conn = http.client.HTTPSConnection(self.host, timeout=120)
                self.conn.request(
                    "GET",
                    self.path,
                    headers={"Range": f"bytes={start}-{end_inclusive}"},
                )
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
                time.sleep(min(30, 2**attempt))
        raise OSError("ranged GET failed after retries")

    def total_size(self) -> int:
        """The bundle's size in bytes, from a one-byte ranged read."""
        if self.conn is None:
            self.conn = http.client.HTTPSConnection(self.host, timeout=120)
        self.conn.request("GET", self.path, headers={"Range": "bytes=0-0"})
        resp = self.conn.getresponse()
        resp.read()
        if resp.status != 206:
            raise Expired(str(resp.status))
        return int(resp.headers["Content-Range"].rpartition("/")[2])


class RangedFile:
    """A read-only, seekable file over the bundle, with a read-ahead buffer, so zipfile can read the directory."""

    def __init__(self, http_: RangedHTTP) -> None:
        self.http = http_
        self.size = http_.total_size()
        self.pos = 0
        self.buf_start = 0
        self.buf = b""

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

    def read(self, n: int | None = -1) -> bytes:
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


def safe_dest(name: str) -> Path:
    parts = Path(name).parts
    if Path(name).is_absolute() or ".." in parts:
        raise ValueError(f"unsafe member path: {name}")
    return RAW.joinpath(*parts)


def member_bytes(http_: RangedHTTP, zi: zipfile.ZipInfo) -> bytes:
    """One member's bytes, inflated and checked against the central directory's size and CRC-32."""
    name_len = len(zi.orig_filename.encode("utf-8"))
    first = http_.get(
        zi.header_offset, zi.header_offset + 30 + name_len + 1024 + zi.compress_size - 1
    )
    if first[:4] != b"PK\x03\x04":
        raise OSError("bad local header signature")
    start = (
        30
        + int.from_bytes(first[26:28], "little")
        + int.from_bytes(first[28:30], "little")
    )
    need = start + zi.compress_size
    if len(first) < need:
        first += http_.get(zi.header_offset + len(first), zi.header_offset + need - 1)
    data = first[start:need]
    if zi.compress_type == zipfile.ZIP_STORED:
        raw = data
    elif zi.compress_type == zipfile.ZIP_DEFLATED:
        inflater = zlib.decompressobj(-15)
        raw = inflater.decompress(data) + inflater.flush()
    else:
        raise OSError(f"unsupported compression {zi.compress_type}")
    if len(raw) != zi.file_size or zlib.crc32(raw) != zi.CRC:
        raise OSError("size or CRC mismatch")
    return raw


def on_disk_matches(zi: zipfile.ZipInfo) -> bool:
    dest = safe_dest(zi.filename)
    return (
        dest.is_file()
        and dest.stat().st_size == zi.file_size
        and zlib.crc32(dest.read_bytes()) == zi.CRC
    )


def main(prefixes: list[str]) -> int:
    if not prefixes:
        print(__doc__)
        return 2
    http_ = RangedHTTP(mint())
    directory = zipfile.ZipFile(RangedFile(http_))
    members = [
        zi
        for zi in directory.infolist()
        if not zi.is_dir() and zi.filename.startswith(tuple(prefixes))
    ]
    present = [zi for zi in members if on_disk_matches(zi)]
    todo = [zi for zi in members if zi not in present]
    print(
        f"selected {len(members)} members ({sum(z.file_size for z in members) / 1e6:.1f} MB); "
        f"on disk with matching size and CRC-32: {len(present)}; to fetch: {len(todo)}",
        flush=True,
    )
    fetched = failed = 0
    for zi in todo:
        try:
            try:
                raw = member_bytes(http_, zi)
            except Expired:
                http_.set_url(mint())
                raw = member_bytes(http_, zi)
        except (OSError, ValueError) as err:
            failed += 1
            print(f"failed: {zi.filename}: {err}", flush=True)
            continue
        dest = safe_dest(zi.filename)
        dest.parent.mkdir(parents=True, exist_ok=True)
        part = dest.with_name(dest.name + ".part")
        part.write_bytes(raw)
        part.rename(dest)
        fetched += 1
    print(f"fetched {fetched}, failed {failed}, kept {len(present)}", flush=True)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
