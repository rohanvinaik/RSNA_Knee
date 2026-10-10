"""Select parser-labeled POSITIVE studies at scale and build fetch jobs.

Per finding: first K positives by sorted UID (deterministic), union-deduped.
Excludes the gold-labeled 58 and the true-normal 80. Requires the canonical
sagittal fluid-sensitive fat-suppressed series with >=15 slices.

These studies feed PROTOTYPES ONLY (label source: report_parser_v3).
Evaluation stays on gold labels — the split is by label source, so every
future lens read is fully out-of-sample.

Usage: python tools/select_positive_pool.py [--k 60]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

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
    p.add_argument("--k", type=int, default=60)
    p.add_argument("--dest", type=Path, default=Path("data/dicom_positives"))
    args = p.parse_args()

    pseudo = pd.read_csv("data/pseudo_labels.csv")
    series = pd.read_csv("data/train_series.csv")
    gold = set(json.loads(Path("data/dicom/manifest.json").read_text()))
    normals = set(json.loads(Path("data/dicom_normals/manifest.json").read_text()))
    pool = pseudo[
        ~pseudo.StudyInstanceUID.isin(gold | normals)
        & (pseudo.coverage == "terms_found")
    ]

    chosen: set = set()
    for f in FINDINGS:
        chosen.update(pool[pool[f] == 1].StudyInstanceUID.sort_values().head(args.k))
    print(f"K={args.k}: {len(chosen)} unique candidate studies; listing series...")

    by_uid = pool.set_index("StudyInstanceUID")
    manifest, jobs = {}, []
    kept = 0
    for study in sorted(chosen):
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
            "labels": {f: int(by_uid.loc[study, f]) for f in FINDINGS},
            "label_source": "report_parser_v3",
        }
        for fi in files:
            dest = args.dest / study / series_uid / fi["name"]
            jobs.append((fi["relativeUrl"], str(dest), int(fi["totalBytes"])))
        kept += 1
        if kept % 25 == 0:
            print(f"  listed {kept}", flush=True)

    args.dest.mkdir(parents=True, exist_ok=True)
    (args.dest / "manifest.json").write_text(json.dumps(manifest, indent=1))
    (args.dest / "jobs.json").write_text(json.dumps(jobs))
    per_f = {f: sum(m["labels"][f] for m in manifest.values()) for f in FINDINGS}
    print(
        f"selected {kept} studies, {len(jobs)} slices "
        f"({sum(j[2] for j in jobs) / 1e9:.2f} GB)"
    )
    print(f"prototype positives per finding: {per_f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
