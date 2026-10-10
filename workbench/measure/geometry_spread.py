"""How hard is the alignment? Per-view geometry spread across the labeled studies.

Headers only (stop_before_pixels), so no decoder is needed and nothing large is read.
"""

from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

import pydicom

from knee.study.tables import labeled_uids, read_tables

ROOT = Path("data/raw")
SERIES_DIR = ROOT / "train_series"

tables = read_tables(ROOT)
labeled = labeled_uids(tables)

# view -> list of per-series geometry facts
facts: dict[tuple, list[dict]] = defaultdict(list)

for uid in labeled:
    study = tables.studies[uid]
    for s in study.series:
        directory = SERIES_DIR / s.study_uid / s.series_uid
        if not directory.is_dir():
            continue
        paths = sorted(directory.glob("*.dcm"))
        if not paths:
            continue
        # first and last file only: enough for extent, spacing, matrix
        try:
            first = pydicom.dcmread(paths[0], stop_before_pixels=True)
            last = pydicom.dcmread(paths[-1], stop_before_pixels=True)
        except Exception as exc:
            facts[("UNREADABLE",)].append({"err": str(exc)[:60]})
            continue
        view = (s.anatomical_plane, s.fluid_sensitive, s.fat_suppression)
        rows = getattr(first, "Rows", None)
        cols = getattr(first, "Columns", None)
        ps = getattr(first, "PixelSpacing", None)
        st = getattr(first, "SliceThickness", None)
        sbs = getattr(first, "SpacingBetweenSlices", None)
        p0 = getattr(first, "ImagePositionPatient", None)
        p1 = getattr(last, "ImagePositionPatient", None)
        extent = None
        if p0 is not None and p1 is not None:
            # strict: a short ImagePositionPatient would silently truncate the sum and
            # under-report the extent, and the extent is this probe's recorded finding.
            extent = (
                sum((float(a) - float(b)) ** 2 for a, b in zip(p0, p1, strict=True))
                ** 0.5
            )
        facts[view].append(
            {
                "n": len(paths),
                "rows": int(rows) if rows else None,
                "cols": int(cols) if cols else None,
                "ps": float(ps[0]) if ps else None,
                "fov": float(ps[0]) * int(rows) if ps and rows else None,
                "thick": float(st) if st is not None else None,
                "gap": float(sbs) if sbs is not None else None,
                "extent": extent,
            }
        )


def spread(values):
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return "none"
    return f"min {vals[0]:.1f}  med {median(vals):.1f}  max {vals[-1]:.1f}"


print(f"labeled studies: {len(labeled)}\n")
for view in sorted(facts, key=lambda v: -len(facts[v])):
    rows = facts[view]
    if view == ("UNREADABLE",):
        print(f"UNREADABLE: {len(rows)}")
        continue
    print(f"{view!s:30s}  {len(rows)} series")
    print(f"   slices per series : {spread([r['n'] for r in rows])}")
    print(f"   matrix rows       : {Counter(r['rows'] for r in rows).most_common(4)}")
    print(f"   in-plane mm/px    : {spread([r['ps'] for r in rows])}")
    print(f"   field of view mm  : {spread([r['fov'] for r in rows])}")
    print(f"   slice thickness mm: {spread([r['thick'] for r in rows])}")
    print(f"   stack extent mm   : {spread([r['extent'] for r in rows])}")
    print()
