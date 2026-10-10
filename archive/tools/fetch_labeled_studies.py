"""Fetch DICOMs for the explicitly-labeled training studies (operational script).

Downloads ONE series per labeled study — Sagittal / Fluid_Sensitive=1 /
Fat_Suppression=1, the canonical fluid-sensitive knee series (fallback: any
fluid-sensitive series) — for the make-or-break test. Never bulk-downloads:
the full competition is ~570GB; this pulls ~58 studies x ~1 series.

Mechanics: Kaggle's tree endpoint lists per-directory files; DownloadDataFile
302s to a signed GCS URL which must be fetched WITHOUT the Authorization
header (GCS rejects bearer tokens on signed URLs — verified 2026-08-28).
Resumable: existing files with matching byte size are skipped.

Usage:
  python tools/fetch_labeled_studies.py [--dest data/dicom] [--workers 8]
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

API = "https://api.kaggle.com/v1/competitions.CompetitionApiService"
COMP = "rsna-knee-abnormality-detection"
FINDINGS = [
    "ACL",
    "MCL",
    "Medial Meniscus",
    "Lateral Meniscus",
    "Medial OA",
    "Lateral OA",
    "PF OA",
    "Effusion",
    "Synovitis",
    "Baker's",
    "Contusion",
    "Fracture",
]


def token() -> str:
    tok = os.environ.get("KAGGLE_API_TOKEN")
    if not tok:
        tok = (Path.home() / ".kaggle" / "token").read_text().strip()
    return tok


def api_post(path: str, body: dict) -> dict:
    req = urllib.request.Request(
        f"{API}/{path}",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {token()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def list_series_files(study: str, series: str) -> list:
    """All slice files under train_series/<study>/<series> (paged)."""
    files, page_token = [], None
    while True:
        body: dict = {
            "competitionName": COMP,
            "path": f"train_series/{study}/{series}",
            "pageSize": 200,
        }
        if page_token:
            body["pageToken"] = page_token
        out = api_post("ListDataTreeFiles", body)
        files.extend(out.get("files", []))
        page_token = out.get("nextPageToken")
        if not page_token:
            return files


class _NoAuthRedirect(urllib.request.HTTPRedirectHandler):
    """Follow the 302 to GCS but DROP the Authorization header."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None:
            new.headers.pop("Authorization", None)
        return new


_opener = urllib.request.build_opener(_NoAuthRedirect)


def download_file(rel_url: str, dest: Path, expect_bytes: int, retries: int = 4) -> str:
    if dest.exists() and dest.stat().st_size == expect_bytes:
        return "skip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_err: Exception | None = None
    for attempt in range(retries):
        # politeness jitter: never present as a request burst (429 lesson,
        # 2026-08-28 — the account is shared across concurrent sessions)
        time.sleep(0.2 + random.random() * 0.4)
        req = urllib.request.Request(
            f"{API}/DownloadDataFile",
            data=json.dumps({"competitionName": COMP, "fileName": rel_url}).encode(),
            headers={
                "Authorization": f"Bearer {token()}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            # timeout is per-socket-op, not total: a stalled connection on a
            # flaky link raises instead of hanging the worker forever
            with _opener.open(req, timeout=90) as r:
                tmp = dest.with_suffix(".part")
                with open(tmp, "wb") as f:
                    while chunk := r.read(1 << 18):
                        f.write(chunk)
                tmp.rename(dest)
            return "ok"
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (404, 429):
                # rate-limit territory (Kaggle surfaces throttling as 429 on
                # the legacy path and 404s on this RPC): back off HARD
                time.sleep(60.0 * (attempt + 1))
        except Exception as e:  # noqa: BLE001 — flaky-link retry, last error re-raised
            last_err = e
    raise RuntimeError(f"failed after {retries} attempts: {last_err}")


def pick_series(series_df: pd.DataFrame, study: str) -> tuple:
    """Sagittal fluid-sensitive fat-suppressed series, else any fluid-sensitive.

    Returns (series_uid, facet_code) with named facet codes, or (None, "none").
    """
    rows = series_df[series_df.StudyInstanceUID == study]
    sag = rows[
        (rows.Anatomical_Plane == "Sagittal")
        & (rows.Fluid_Sensitive == 1)
        & (rows.Fat_Suppression == 1)
    ]
    if len(sag):
        return sag.iloc[0].SeriesInstanceUID, "sagittal_fs"
    fluid = rows[rows.Fluid_Sensitive == 1]
    if len(fluid):
        return fluid.iloc[0].SeriesInstanceUID, "fluid_fallback"
    return None, "none"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dest", type=Path, default=Path("data/dicom"))
    p.add_argument("--workers", type=int, default=8)
    args = p.parse_args()

    jobs_cache = args.dest / "jobs.json"
    if jobs_cache.exists():
        # listings are immutable competition data: cache them so resumable
        # sweeps skip ~5 min of sequential API calls per restart
        cached = json.loads(jobs_cache.read_text())
        jobs = [(u, Path(d), int(b)) for u, d, b in cached]
        print(f"loaded {len(jobs)} slice jobs from cache (listing skipped)")
    else:
        data = Path(__file__).resolve().parent.parent / "data"
        train = pd.read_csv(data / "train.csv")
        series = pd.read_csv(data / "train_series.csv")

        labeled = train.dropna(subset=FINDINGS, how="all")
        print(f"labeled studies: {len(labeled)}")

        manifest = {}
        jobs = []
        for study in labeled.StudyInstanceUID:
            series_uid, facet = pick_series(series, study)
            if series_uid is None:
                print(f"WARN no fluid-sensitive series for {study}", file=sys.stderr)
                continue
            files = list_series_files(study, series_uid)
            labels = {
                f: (None if pd.isna(v) else int(v))
                for f, v in labeled[labeled.StudyInstanceUID == study][FINDINGS]
                .iloc[0]
                .items()
            }
            manifest[study] = {
                "series": series_uid,
                "facet": facet,
                "n_slices": len(files),
                "labels": labels,
            }
            for fi in files:
                dest = args.dest / study / series_uid / fi["name"]
                jobs.append((fi["relativeUrl"], dest, int(fi["totalBytes"])))
            print(f"  {study[-12:]}: {len(files)} slices ({facet})")

        (args.dest).mkdir(parents=True, exist_ok=True)
        with open(args.dest / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=1)
        with open(jobs_cache, "w") as f:
            json.dump([(u, str(d), b) for u, d, b in jobs], f)

    print(f"downloading {len(jobs)} slices with {args.workers} workers...")
    done = skipped = failed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(download_file, u, d, b): u for u, d, b in jobs}
        for fut in as_completed(futs):
            try:
                r = fut.result()
                done += r == "ok"
                skipped += r == "skip"
            except Exception as e:  # noqa: BLE001 — operational script, log and continue
                failed += 1
                print(f"FAIL {futs[fut]}: {e}", file=sys.stderr)
            if (done + skipped + failed) % 200 == 0:
                print(f"  {done} downloaded, {skipped} skipped, {failed} failed")

    print(f"DONE: {done} downloaded, {skipped} skipped, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
