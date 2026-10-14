"""Run the interiors operation on one study, name the plain objects, and draw both.

For each series of the study, as the second build's route did (`objects/analysis.py`,
`_measure_series`): the regime's background split, the middle slice, its plane frame, and
`read_interiors` with the frame's spacing and the retained basis as its metric. Then
`assign_plane` names what the pictures show: air, skin, femur, tibia, joint, patella and menisci,
the menisci sided by the header's own word for which knee it is. The arrays the
renderers read are saved per series with their digests in a receipt; `object_interiors.draw`, the
renderer that drew the proof figure, draws the interiors, and `object_assignments.draw` draws the
named objects.

An object the middle slice does not show is named on its own main slice (AGENTS.md, the method's
first step), saved in a run of its own and drawn beside the others: so far the fibula
(`find_fibula`), named there beside the tibia it was found against and nothing else. The middle
slice's run and pictures are unchanged by it.

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
from knee.collapse.squint_stack import read_squint_stack
from knee.objects.assignments import (
    OBJECT_CODES,
    assign_plane,
    fibula_block,
    fibula_code,
    fibula_on_slice,
    main_slice,
)
from knee.objects.interiors import EDGE_KINDS, TRACE_CODES, read_interiors
from knee.study.corpus import LOCAL_ROOT, open_corpus, read_study
from knee.study.series import Series, selected_slice

ROOT = Path(__file__).resolve().parent.parent
PROMINENCE_MM = 3.0
OFFSETS_MM = (-3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0)
# The squint that points to where an object must be: tiles 10 mm wide, about a 16 x 16 grid on
# these fields (Rohan, 2026-10-12: «a 16x16 grid costs literally (n)^(1/2), for EVERYTHING»).
SQUINT_TILE_MM = 10.0


def digest(array: np.ndarray) -> str:
    """The renderer's own check on a saved array: its dtype, shape and bytes."""
    return sha256(
        array.dtype.str.encode() + str(array.shape).encode() + array.tobytes()
    ).hexdigest()


def plane_frame(series: Series, index: int) -> PlaneFrame | str:
    """One slice's frame in the scanner's millimetres, or why its header does not read as one."""
    geometry = series.geometry
    if geometry is None:
        return "geometry_unreadable"
    try:
        return PlaneFrame.from_dicom(
            geometry.position[index],
            geometry.orientation[index],
            geometry.spacing[index],
        )
    except ValueError as error:
        return f"geometry_unreadable: {error}"


def measure(series: Series) -> tuple[dict, dict[str, np.ndarray]] | str:
    """One series' interiors and named objects at its middle slice, or why no plane was read."""
    if series.volume is None:
        return "no_stacked_volume"
    if series.geometry is None:
        return "geometry_unreadable"
    index = selected_slice(len(series.volume), None)
    if index is None:
        return "slice_unavailable"
    frame = plane_frame(series, index)
    if isinstance(frame, str):
        return frame
    regime = read_regime(series)
    split = regime.background_split if regime is not None else float("nan")
    # The header's own word for which knee this is ("R", "L", or blank); it sides the menisci.
    knee = str(getattr(series.slices[index].header, "Laterality", "") or "").strip()
    return name_plane(series, index, series.volume[index], frame, split, knee)


def name_plane(
    series: Series,
    index: int,
    plane: np.ndarray,
    frame: PlaneFrame,
    split: float,
    knee: str,
) -> tuple[dict, dict[str, np.ndarray]]:
    """One slice's interiors and its named objects, as the record and arrays the renderers read."""
    axes = frame.basis_lps / frame.spacing_rc
    reading = read_interiors(
        plane,
        frame.spacing_rc,
        split,
        PROMINENCE_MM,
        np.asarray(OFFSETS_MM),
        "reference",
        metric_rc=axes.T @ axes,
    )
    assignment = assign_plane(plane, reading, frame.basis_lps, knee)
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
            "knee": knee,
            "codes": assignment.codes,
            "femur": assignment.femur,
            "tibia": assignment.tibia,
            "patella": assignment.patella,
            "menisci": assignment.menisci,
            "peaks": [asdict(peak) for peak in assignment.peaks],
        },
    }
    return record, arrays


def find_fibula(
    series: Series, record: dict, arrays: dict[str, np.ndarray]
) -> tuple[dict, dict[str, np.ndarray]] | str:
    """The fibula named on its main slice, from the middle slice's tibia, or why it was not.

    As the method says: the squint points to where the fibula must be (`fibula_block`: below the
    tibia's top, on the knee's outer side of its middle); the interiors lens reads only that block
    on each slice that holds it; the fibula there is the region that looks like the tibia, well
    below its top and behind its middle, apart from the tibia (`fibula_on_slice`); and it is named
    on the slice where that region is largest.
    """
    assigned = record["assignments"]
    knee = assigned["knee"]
    fat_suppressed = int(series.row.fat_suppression) == 1  # the tag is stored as text
    code = fibula_code(knee, assigned["tibia"] is not None, fat_suppressed, True)
    if code != "identified":
        return code
    volume = series.volume
    middle = plane_frame(series, record["slice_index"])
    if volume is None or isinstance(middle, str):
        return "geometry_unreadable"
    tibia = arrays["a1_objects"] == OBJECT_CODES["tibia"]
    top_mm = float(middle.to_patient(np.argwhere(tibia).astype(float))[:, 2].max())
    peak = next(p for p in assigned["peaks"] if p["territory"] == assigned["tibia"])
    middle_lps = middle.to_patient(np.asarray([peak["peak_rc"]], dtype=float))[0]
    stack = read_squint_stack(series, SQUINT_TILE_MM)
    if stack.code != "present":
        return f"squint_{stack.code}"
    split = record["background_split"]
    areas: list[float] = []
    found: list[tuple[int, int, np.ndarray, np.ndarray] | None] = []
    for z in range(len(volume)):
        block = fibula_block(stack.centres_lps[z], top_mm, middle_lps, knee)
        frame = plane_frame(series, z)
        if not block.any() or isinstance(frame, str):
            areas.append(0.0)
            found.append(None)
            continue
        bounds = stack.bounds_rc[block]
        r0, r1 = int(bounds[:, 0].min()), int(bounds[:, 1].max())
        c0, c1 = int(bounds[:, 2].min()), int(bounds[:, 3].max())
        axes = frame.basis_lps / frame.spacing_rc
        reading = read_interiors(
            volume[z][r0:r1, c0:c1],
            frame.spacing_rc,
            split,
            PROMINENCE_MM,
            np.asarray(OFFSETS_MM),
            "reference",
            metric_rc=axes.T @ axes,
        )
        rows, cols = np.mgrid[r0:r1, c0:c1]
        places_lps = frame.to_patient(
            np.column_stack((rows.ravel(), cols.ravel())).astype(float)
        ).reshape(r1 - r0, c1 - c0, 3)
        # The block's border where it is not the picture's own edge: where the block cuts.
        cut = np.zeros((r1 - r0, c1 - c0), dtype=bool)
        cut[0, :] |= r0 > 0
        cut[-1, :] |= r1 < volume[z].shape[0]
        cut[:, 0] |= c0 > 0
        cut[:, -1] |= c1 < volume[z].shape[1]
        territory, area = fibula_on_slice(
            reading.labels,
            np.asarray(volume[z][r0:r1, c0:c1], dtype=float),
            frame.spacing_rc[0] * frame.spacing_rc[1],
            places_lps,
            tibia[r0:r1, c0:c1],
            middle_lps,
            cut,
        )
        areas.append(area)
        if territory is None:
            found.append(None)
            continue
        held = reading.labels[tibia[r0:r1, c0:c1] & (reading.labels > 0)]
        tibia_here = reading.labels == int(np.argmax(np.bincount(held)))
        found.append((r0, c0, reading.labels == territory, tibia_here))
    chosen = main_slice(areas)
    if chosen is None:
        return fibula_code(knee, True, False, False)
    frame = plane_frame(series, chosen)
    held_on_main = found[chosen]
    if isinstance(frame, str) or held_on_main is None:
        return "geometry_unreadable"
    main_record, main_arrays = name_plane(
        series, chosen, volume[chosen], frame, split, knee
    )
    # On its main slice only the fibula is named, beside the tibia it was found against; each is
    # drawn whole as the full slice's own region. The middle slice's other objects are not named
    # here: their rules belong to the middle slice.
    r0, c0, fibula_place, tibia_place = held_on_main
    labels = main_arrays["b1_labels"]

    def region_of(place: np.ndarray) -> int | None:
        mask = np.zeros(labels.shape, dtype=bool)
        mask[r0 : r0 + place.shape[0], c0 : c0 + place.shape[1]] = place
        under = labels[mask & (labels > 0)]
        return int(np.argmax(np.bincount(under))) if under.size else None

    fibula_region, tibia_region = region_of(fibula_place), region_of(tibia_place)
    if fibula_region is None or fibula_region == tibia_region:
        return fibula_code(knee, True, False, False)
    objects = np.zeros(labels.shape, dtype=np.int8)
    if tibia_region is not None:
        objects[labels == tibia_region] = OBJECT_CODES["tibia"]
    objects[labels == fibula_region] = OBJECT_CODES["fibula"]
    main_arrays["a1_objects"] = objects
    main_assigned = main_record["assignments"]
    codes = {name: "not_named_on_this_slice" for name in main_assigned["codes"]}
    codes["tibia"] = "carried_from_the_middle_slice"
    codes["fibula"] = "identified"
    main_assigned.update(
        codes=codes,
        femur=None,
        patella=None,
        menisci=0,
        tibia=tibia_region,
        fibula=fibula_region,
    )
    main_record["main_slice"] = {
        "object": "fibula",
        "areas_mm2": [round(area, 1) for area in areas],
    }
    return main_record, main_arrays


def save(run_dir: Path, study_uid: str, record: dict, arrays: dict) -> dict:
    """Save one record's arrays in the run and note them, with their digests, on the record."""
    artifact = Path(study_uid) / f"{record['series_uid']}.npz"
    np.savez_compressed(run_dir / artifact, allow_pickle=False, **arrays)
    record["study_uid"] = study_uid
    record["artifact"] = str(artifact)
    record["arrays"] = {name: {"digest": digest(a)} for name, a in arrays.items()}
    return record


def write_receipt(run_dir: Path, records: list[dict], unread: dict[str, str]) -> None:
    """The run's receipt: its settings, its records, and why any series was not read."""
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


def run(
    study_uid: str,
    run_dir: Path,
    out: Path,
    assignments_out: Path,
    main_run: Path,
    main_out: Path,
) -> list[Path]:
    """Measure every series of one study, save the runs, draw them, and return the series pictures."""
    study = read_study(open_corpus(ROOT / LOCAL_ROOT), study_uid)
    (run_dir / study_uid).mkdir(parents=True, exist_ok=True)
    (main_run / study_uid).mkdir(parents=True, exist_ok=True)
    records, unread = [], {}
    main_records, main_unread = [], {}
    for series in study.series:
        measured = measure(series)
        if isinstance(measured, str):
            unread[series.row.series_uid] = measured
            continue
        record, arrays = measured
        fibula = find_fibula(series, record, arrays)
        records.append(save(run_dir, study_uid, record, arrays))
        if isinstance(fibula, str):
            main_unread[record["series_uid"]] = fibula
        else:
            main_records.append(save(main_run, study_uid, *fibula))
    write_receipt(run_dir, records, unread)
    write_receipt(main_run, main_records, main_unread)
    object_interiors.draw(run_dir, study_uid, out)
    object_assignments.draw(run_dir, study_uid, assignments_out)
    pictures = [out / "series.png", assignments_out / "series.png"]
    if main_records:
        object_assignments.draw(main_run, study_uid, main_out)
        pictures.append(main_out / "series.png")
    return pictures


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
    parser.add_argument(
        "--main-run", type=Path, default=ROOT / "data/measurements/main-slices"
    )
    parser.add_argument(
        "--main-out", type=Path, default=ROOT / "data/pictures/main-slices"
    )
    args = parser.parse_args()
    pictures = run(
        args.study_uid,
        args.run,
        args.out / args.study_uid,
        args.assignments_out / args.study_uid,
        args.main_run,
        args.main_out / args.study_uid,
    )
    for picture in pictures:
        print(picture)


if __name__ == "__main__":
    main()
