"""Is there imaged air to measure sigma from, and does the intensity law look Rician?

Reads a handful of series' pixels. Tests: (a) does a decoder work locally, (b) is there a
distinct air population, (c) what does the Rayleigh estimator give vs the robust median one,
(d) is a numerical zero present (which would mean zero != fill is a live concern).
"""

from pathlib import Path

import numpy as np
import pydicom

from knee.study.tables import labeled_uids, read_tables

ROOT = Path("data/raw")
SERIES_DIR = ROOT / "train_series"

tables = read_tables(ROOT)
labeled = sorted(labeled_uids(tables))

shown = 0
for uid in labeled:
    study = tables.studies[uid]
    for s in study.series:
        if (s.anatomical_plane, s.fluid_sensitive, s.fat_suppression) != (
            "Axial",
            "1",
            "1",
        ):
            continue
        directory = SERIES_DIR / s.study_uid / s.series_uid
        paths = sorted(directory.glob("*.dcm"))
        if not paths:
            continue
        mid = paths[len(paths) // 2]
        try:
            ds = pydicom.dcmread(mid)
            px = ds.pixel_array.astype(np.float64)
        except Exception as exc:
            print(f"{uid[:12]}  DECODE FAILED: {type(exc).__name__}: {str(exc)[:70]}")
            shown += 1
            break

        flat = px.ravel()
        n_zero = int((flat == 0).sum())
        # Corner patches: most likely air, away from the leg.
        h, w = px.shape
        c = min(h, w) // 8
        corners = np.concatenate(
            [
                px[:c, :c].ravel(),
                px[:c, -c:].ravel(),
                px[-c:, :c].ravel(),
                px[-c:, -c:].ravel(),
            ]
        )
        # Rayleigh estimators on the corner sample
        ray = float(np.sqrt((corners**2).sum() / (2 * corners.size)))
        med = (
            float(np.median(corners) / np.sqrt(2 * np.log(2)))
            if np.median(corners) > 0
            else 0.0
        )

        print(
            f"{uid[:12]}  {h}x{w}  "
            f"range {flat.min():.0f}-{flat.max():.0f}  "
            f"p50 {np.percentile(flat, 50):.0f}  p99 {np.percentile(flat, 99):.0f}  "
            f"zeros {100 * n_zero / flat.size:.2f}%  |  "
            f"corner med {np.median(corners):.1f} p99 {np.percentile(corners, 99):.0f}  "
            f"sigma: rayleigh {ray:.1f} median-est {med:.1f}"
        )
        shown += 1
        break
    if shown >= 8:
        break
