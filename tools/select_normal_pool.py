"""Select the true-normal pool from parser pseudo-labels and build fetch jobs.

Picks N all-negative (parser: every finding 0, coverage=terms_found) studies
that carry a sagittal fluid-sensitive fat-suppressed series, sorted by UID
for reproducibility. Lists each chosen series' slice files via the (healthy)
tree endpoint and writes a jobs file for tools/fetch_from_bundle.py — the
ranged reader that never touches the rate-limited download API.

Usage: python tools/select_normal_pool.py [--n 80]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from fetch_labeled_studies import list_series_files, pick_series

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


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n", type=int, default=80)
    p.add_argument("--dest", type=Path, default=Path("data/dicom_normals"))
    args = p.parse_args()

    pseudo = pd.read_csv("data/pseudo_labels.csv")
    series = pd.read_csv("data/train_series.csv")
    manifest_labeled = json.loads(Path("data/dicom/manifest.json").read_text())

    allneg = pseudo[
        (pseudo[FINDINGS].sum(axis=1) == 0)
        & (pseudo.coverage == "terms_found")
        & (~pseudo.StudyInstanceUID.isin(manifest_labeled.keys()))
    ].sort_values("StudyInstanceUID")
    print(
        f"candidate normals: {len(allneg)}; taking first {args.n} with sagittal-FS series"
    )

    manifest = {}
    jobs = []
    taken = 0
    for study in allneg.StudyInstanceUID:
        if taken >= args.n:
            break
        series_uid, facet = pick_series(series, study)
        if series_uid is None or facet != "sagittal_fs":
            continue
        files = list_series_files(study, series_uid)
        if len(files) < 15:
            continue
        manifest[study] = {
            "series": series_uid,
            "facet": facet,
            "n_slices": len(files),
            "labels": {f: 0 for f in FINDINGS},
            "label_source": "report_parser_v3",
        }
        for fi in files:
            dest = args.dest / study / series_uid / fi["name"]
            jobs.append((fi["relativeUrl"], str(dest), int(fi["totalBytes"])))
        taken += 1
        if taken % 10 == 0:
            print(f"  listed {taken}/{args.n}")

    args.dest.mkdir(parents=True, exist_ok=True)
    (args.dest / "manifest.json").write_text(json.dumps(manifest, indent=1))
    (args.dest / "jobs.json").write_text(json.dumps(jobs))
    print(
        f"selected {taken} studies, {len(jobs)} slices "
        f"({sum(j[2] for j in jobs) / 1e9:.2f} GB) -> {args.dest}/jobs.json"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
