"""Run the interiors operation on one study, name the plain objects, and draw both.

For each series of the study, as the second build's route did (`objects/analysis.py`,
`_measure_series`): the regime's background split, the middle slice, its plane frame, and
`read_interiors` with the frame's spacing and the retained basis as its metric. Then
`assign_plane` names what the pictures show: air, skin, femur, tibia and joint. The arrays the
renderers read are saved per series with their digests in a receipt; `object_interiors.draw`, the
renderer that drew the proof figure, draws the interiors, and `object_assignments.draw` draws the
named objects.

The settings are the proof run's own (`data/measurements/codex-wiring-rereview-20261012`):
prominence 3 mm, and border offsets from -3 to 3 mm in 0.5 mm steps. The backend is the plain
reference; that run used its JIT twin, whose records the contract states are the same.

Run from anywhere: `.venv/bin/python scripts/run_interiors.py --study-uid <uid>`.
"""

import argparse
import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

import numpy as np

import object_assignments
import object_interiors
from knee.collapse.physical import PlaneFrame
from knee.collapse.regime import read_regime
from knee.objects.assignments import assign_plane
from knee.objects.interiors import EDGE_KINDS, TRACE_CODES, read_interiors
from knee.study.corpus import LOCAL_ROOT, open_corpus, read_study
from knee.study.series import Series, selected_slice

ROOT = Path(__file__).resolve().parent.parent
PROMINENCE_MM = 3.0
OFFSETS_MM = (-3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0)


def digest(array: np.ndarray) -> str:
    """The renderer's own check on a saved array: its dtype, shape and bytes."""
    return sha256(
        array.dtype.str.encode() + str(array.shape).encode() + array.tobytes()
    ).hexdigest()


def measure(series: Series) -> tuple[dict, dict[str, np.ndarray]] | str:
    """One series' interiors and named objects at its middle slice, or why no plane was read."""
    if series.volume is None:
        return "no_stacked_volume"
    if series.geometry is None:
        return "geometry_unreadable"
    index = selected_slice(len(series.volume), None)
    if index is None:
        return "slice_unavailable"
    geometry = series.geometry
    try:
        frame = PlaneFrame.from_dicom(
            geometry.position[index],
            geometry.orientation[index],
            geometry.spacing[index],
        )
    except ValueError as error:
        return f"geometry_unreadable: {error}"
    regime = read_regime(series)
    split = regime.background_split if regime is not None else float("nan")
    axes = frame.basis_lps / frame.spacing_rc
    plane = series.volume[index]
    reading = read_interiors(
        plane,
        frame.spacing_rc,
        split,
        PROMINENCE_MM,
        np.asarray(OFFSETS_MM),
        "reference",
        metric_rc=axes.T @ axes,
    )
    assignment = assign_plane(plane, reading, frame.basis_lps)
    arrays = {
        "acquired_plane": plane.copy(),
        "b1_dark": reading.dark,
        "b1_available": reading.available,
        "b1_distance_mm": reading.distance_mm,
        "b1_markers": reading.markers,
        "b1_labels": reading.labels,
        "b1_edge_points_rc": reading.edge_points_rc,
        "b1_edge_normals_rc": reading.edge_normals_rc,
        "b1_trace_codes": reading.trace_codes,
        "b1_trace_points_rc": reading.trace_points_rc,
        "a1_objects": assignment.objects,
    }
    row = series.row
    record = {
        "series_uid": row.series_uid,
        "view": [row.anatomical_plane, row.fluid_sensitive, row.fat_suppression],
        "slice_index": index,
        "source_plane": series.slices[index].path.name,
        "background_split": split,
        "interiors": {
            "code": reading.code,
            "territories": int(reading.labels.max(initial=0)),
            "edge_counts": {
                kind: int(np.count_nonzero(reading.edge_kinds == value))
                for kind, value in EDGE_KINDS.items()
            },
            "trace_counts": {
                code: int(np.count_nonzero(reading.trace_codes == value))
                for code, value in TRACE_CODES.items()
            },
            "backend": "reference",
        },
        "assignments": {
            "codes": assignment.codes,
            "femur": assignment.femur,
            "tibia": assignment.tibia,
            "patella": assignment.patella,
            "menisci": assignment.menisci,
            "peaks": [asdict(peak) for peak in assignment.peaks],
        },
    }
    return record, arrays


def run(
    study_uid: str, run_dir: Path, out: Path, assignments_out: Path
) -> tuple[Path, Path]:
    """Measure every series of one study, save the run, draw it, and return the two series pictures."""
    study = read_study(open_corpus(ROOT / LOCAL_ROOT), study_uid)
    (run_dir / study_uid).mkdir(parents=True, exist_ok=True)
    records, unread = [], {}
    for series in study.series:
        measured = measure(series)
        if isinstance(measured, str):
            unread[series.row.series_uid] = measured
            continue
        record, arrays = measured
        artifact = Path(study_uid) / f"{record['series_uid']}.npz"
        np.savez_compressed(run_dir / artifact, allow_pickle=False, **arrays)
        record["study_uid"] = study_uid
        record["artifact"] = str(artifact)
        record["arrays"] = {name: {"digest": digest(a)} for name, a in arrays.items()}
        records.append(record)
    receipt = {
        "request": {
            "prominence_mm": PROMINENCE_MM,
            "offsets_mm": list(OFFSETS_MM),
            "slice_index": None,
            "backend": "reference",
        },
        "records": records,
        "unread": unread,
    }
    (run_dir / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    object_interiors.draw(run_dir, study_uid, out)
    object_assignments.draw(run_dir, study_uid, assignments_out)
    return out / "series.png", assignments_out / "series.png"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-uid", required=True)
    parser.add_argument(
        "--run", type=Path, default=ROOT / "data/measurements/interiors"
    )
    parser.add_argument("--out", type=Path, default=ROOT / "data/pictures/interiors")
    parser.add_argument(
        "--assignments-out", type=Path, default=ROOT / "data/pictures/assignments"
    )
    args = parser.parse_args()
    pictures = run(
        args.study_uid,
        args.run,
        args.out / args.study_uid,
        args.assignments_out / args.study_uid,
    )
    for picture in pictures:
        print(picture)


if __name__ == "__main__":
    main()
