"""Mint a fresh signed URL for the competition's full data bundle, and check it (operational).

Asks the Kaggle API for the whole bundle without following the redirect, so the signed GCS URL is captured rather than
downloaded. The URL is written to data/rsna_bundle_url.txt (gitignored). Neither the token nor the URL is ever
printed: only the HTTP statuses, the host, and the bundle's total size from a one-byte ranged read.

The token is KAGGLE_API_TOKEN, read from the environment or from ~/Projects/Kaggle_Killer/.env.
Signed URLs expire after some hours; re-run this when a fetch starts failing with 4xx.

Usage: .venv/bin/python tools/mint_bundle_url.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.kaggle.com/v1/competitions.CompetitionApiService/DownloadDataFiles"
COMP = "rsna-knee-abnormality-detection"
ENV_FILE = Path.home() / "Projects" / "Kaggle_Killer" / ".env"
OUT = Path("data/rsna_bundle_url.txt")


def token() -> str:
    tok = os.environ.get("KAGGLE_API_TOKEN", "")
    if tok:
        return tok
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition("=")
        if key.strip() == "KAGGLE_API_TOKEN":
            return value.strip().strip('"').strip("'")
    raise SystemExit("KAGGLE_API_TOKEN not found in the environment or the .env file")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):  # noqa: ANN002, ANN003, ANN201
        return None


def mint() -> str:
    req = urllib.request.Request(
        API,
        data=json.dumps({"competitionName": COMP}).encode(),
        headers={"Authorization": f"Bearer {token()}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.build_opener(NoRedirect).open(req, timeout=60)
    except urllib.error.HTTPError as e:
        location = e.headers.get("Location", "")
        print("mint: HTTP", e.code, "| redirect present:", bool(location))
        if e.code in (301, 302, 303, 307, 308) and location:
            return location
        raise SystemExit(f"mint failed: HTTP {e.code}") from None
    raise SystemExit("mint: no redirect returned")


def check(url: str) -> None:
    req = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
    with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310 - the signed GCS URL just minted
        total = r.headers.get("Content-Range", "").rpartition("/")[2]
        print("check: HTTP", r.status, "| host:", urllib.parse.urlsplit(url).hostname, "| bundle bytes:", total)


def main() -> int:
    url = mint()
    check(url)
    OUT.write_text(url + "\n", encoding="utf-8")
    print("written:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
