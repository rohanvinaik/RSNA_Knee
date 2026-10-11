"""Geometry for the proposed object toolkit, through Chapter 1's actual study reader.

Reads all labeled studies, including their pixels. Reports native spacing, the physical width of
the demonstrated 8-place tiles, superior projection and true ordered-stack extent. No segmentation
or diagnostic label decision is made here. The complete receipt contains geometry only, no pixels.
"""

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from knee.study.corpus import open_corpus, read_study
from knee.study.tables import labeled_uids

corpus = open_corpus(Path("data/raw"))
uids = labeled_uids(corpus.tables)
records = []
errors = []
for uid in uids:
    try:
        study = read_study(corpus, uid)
        for series in study.series:
            geometry = series.geometry
            row = series.row
            record = {
                "view": [
                    row.anatomical_plane,
                    row.fluid_sensitive,
                    row.fat_suppression,
                ],
                "stack": list(series.stack),
            }
            if series.volume is not None and geometry is not None:
                orientation = geometry.orientation[0]
                record.update(
                    shape=list(series.volume.shape),
                    spacing_min=float(geometry.spacing.min()),
                    spacing_max=float(geometry.spacing.max()),
                    tile8_min_mm=float(8 * geometry.spacing.min()),
                    tile8_max_mm=float(8 * geometry.spacing.max()),
                    si_inplane=float(np.hypot(orientation[2], orientation[5])),
                    normal_z=float(geometry.normal[2]),
                    orientation_spread=float(geometry.orientation_spread),
                    extent_mm=float(np.ptp(geometry.along_normal)),
                )
            records.append(record)
    except Exception as exc:
        errors.append({"uid": uid, "type": type(exc).__name__, "message": str(exc)})

by_view = defaultdict(list)
for record in records:
    by_view[tuple(record["view"])].append(record)
summary = {
    "studies_attempted": len(uids),
    "series_read": len(records),
    "errors": errors,
    "views": [],
}
for view, rows in sorted(by_view.items()):
    geometries = [row for row in rows if "shape" in row]
    result = {
        "view": view,
        "series": len(rows),
        "stackable_with_geometry": len(geometries),
    }
    for field in [
        "spacing_min",
        "spacing_max",
        "tile8_min_mm",
        "tile8_max_mm",
        "si_inplane",
        "normal_z",
        "orientation_spread",
        "extent_mm",
    ]:
        values = np.asarray([row[field] for row in geometries])
        result[field] = (
            [float(values.min()), float(np.median(values)), float(values.max())]
            if values.size
            else []
        )
    summary["views"].append(result)

receipt = Path("data/measurements/object-toolkit-geometry.json")
receipt.parent.mkdir(parents=True, exist_ok=True)
receipt.write_text(json.dumps({"summary": summary, "records": records}, indent=2))
print(json.dumps(summary, indent=2))
print("Receipt:", receipt)
