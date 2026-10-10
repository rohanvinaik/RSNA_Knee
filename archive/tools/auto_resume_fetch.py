"""Rate-limit-aware auto-resume for the labeled-study fetch (operational).

Phase 1: probe DownloadDataFile every 10 min until it answers a clean 302
(the endpoint flaps 404/429 while throttled — only 302 means open).
Phase 2: gentle sweeps of tools/fetch_labeled_studies.py (3 workers; the
fetcher itself adds jittered pacing and hard backoff on 404/429) until all
slices land or sweeps stop making progress.

Exit codes: 0 = all studies complete · 2 = endpoint never opened in 12h ·
3 = sweeps exhausted with slices still missing.
Run under tools/fetch_watchdog.sh for process-death resilience.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.kaggle.com/v1/competitions.CompetitionApiService/DownloadDataFile"
COMP = "rsna-knee-abnormality-detection"


def _token() -> str:
    return (
        os.environ.get("KAGGLE_API_TOKEN")
        or (Path.home() / ".kaggle" / "token").read_text().strip()
    )


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def endpoint_ok() -> bool:
    req = urllib.request.Request(
        API,
        data=json.dumps({"competitionName": COMP, "fileName": "train.csv"}).encode(),
        headers={
            "Authorization": f"Bearer {_token()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        urllib.request.build_opener(_NoRedirect).open(req, timeout=30)
    except urllib.error.HTTPError as e:
        return e.code == 302
    except Exception:  # noqa: BLE001 — network flake counts as not-open
        return False
    return False


def n_complete() -> tuple[int, int]:
    m = json.loads(Path("data/dicom/manifest.json").read_text())
    done = sum(
        1
        for s, meta in m.items()
        if len(list((Path("data/dicom") / s / meta["series"]).glob("*.dcm")))
        == meta["n_slices"]
    )
    return done, len(m)


def main() -> int:
    for probe in range(72):  # up to 12h
        if endpoint_ok():
            print(f"endpoint recovered after {probe} probes", flush=True)
            break
        print(f"probe {probe}: still limited, sleeping 10 min", flush=True)
        time.sleep(600)
    else:
        print("endpoint never recovered in 12h", flush=True)
        return 2

    prev_done = -1
    for sweep in range(10):
        r = subprocess.run(
            [
                sys.executable,
                "-u",
                "tools/fetch_labeled_studies.py",
                "--dest",
                "data/dicom",
                "--workers",
                "3",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        tail = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "?"
        done, total = n_complete()
        print(f"sweep {sweep}: {tail} | {done}/{total} studies complete", flush=True)
        if done == total:
            print(f"FINAL: {done}/{total} studies complete", flush=True)
            return 0
        if done == prev_done and "0 failed" not in tail:
            # no forward progress: re-enter probe mode rather than hammer
            print("no progress this sweep — re-probing endpoint", flush=True)
            if not endpoint_ok():
                for probe in range(36):  # up to 6 more hours
                    if endpoint_ok():
                        break
                    time.sleep(600)
        prev_done = done
        time.sleep(120)

    done, total = n_complete()
    print(f"FINAL: {done}/{total} studies complete (sweeps exhausted)", flush=True)
    return 0 if done == total else 3


if __name__ == "__main__":
    raise SystemExit(main())
