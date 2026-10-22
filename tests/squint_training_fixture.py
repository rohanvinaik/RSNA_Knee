"""Tiny extraction inputs for tests that stub inference, never readiness checks."""

from __future__ import annotations

import csv
import zipfile
from collections.abc import Sequence
from pathlib import Path


def make_training_raw_fixture(root: Path, study_uids: Sequence[str]) -> Path:
    """Write matching raw files, series rows and trusted source ZIP inventory.

    The bytes intentionally exercise the input/checkpoint boundary rather than
    DICOM decoding: tests that call a real decoder need their real-image fixture.
    """
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    files = []
    for index, uid in enumerate(dict.fromkeys(study_uids), start=1):
        series_uid = f"1.2.826.0.1.3680043.8.498.9999.{index}"
        relative = Path("train_series") / uid / series_uid / "x.dcm"
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(bytes(128) + b"DICM" + uid.encode("ascii"))
        files.append(relative)
        rows.append(
            {
                "StudyInstanceUID": uid,
                "SeriesInstanceUID": series_uid,
                "Fluid_Sensitive": "0",
                "Fat_Suppression": "0",
                "Anatomical_Plane": "Sagittal",
            }
        )
    with (root / "train_series.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "StudyInstanceUID",
                "SeriesInstanceUID",
                "Fluid_Sensitive",
                "Fat_Suppression",
                "Anatomical_Plane",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    with zipfile.ZipFile(root.with_suffix(".zip"), "w") as archive:
        for relative in files:
            archive.write(root / relative, relative.as_posix())
    return root
