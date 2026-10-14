"""Run the pipeline on one or more studies: chapter 1 reads each whole, every reading is kept, the
plain objects are named, and both are drawn.

For each series of a study, as the second build's route did (`objects/analysis.py`,
`_measure_series`): the regime key, read once over the whole series and kept whole; the squint
over every slice, made once and kept with the series; the middle slice, its plane frame, and
`read_interiors` with the frame's spacing and the retained basis as its metric. Then
`assign_plane` names what the pictures show: air, skin, femur, tibia, joint and menisci, the
menisci sided by the header's own word for which knee it is; the patella abstains until a lens
holds it whole. The arrays the renderers read, and the squint's, are saved per series with their
digests in a receipt; `object_interiors.draw`, the renderer that drew the proof figure, draws the
interiors, and `object_assignments.draw` draws the named objects.

An object the middle slice does not show is named on its own main slice (AGENTS.md, the method's
first step), saved in a run of its own and drawn beside the others: so far the fibula
(`find_fibula`), named there beside the tibia it was found against and nothing else. It reads the
series' kept squint, but it still reads the interiors lens again on the block of every slice that
holds it, which the method forbids; the ledger counts those readings (`fibula.lens_readings`)
until its main slice comes from the squint.

THE RECEIPT KEEPS EVERY STUDY (`knee.receipt.merged_receipt`): a study run again replaces only its
own records. Studies run one after another in one process; two processes writing one run folder
would still lose each other's records.

TELEMETRY (`knee.telemetry`, the founder's central place for it): each study runs with the ledger
on. Every stage records, field by field, what it handed on (`<product>.<field>.produced`) and, at
the point of reading, what it read (`<product>.<field>.consumed_by.<stage>`), with its counted
work beside. The receipt keeps each study's events and totals, and every field produced and read
by no stage (`knee.telemetry.route.unread_products`), which the run also prints: kept in the
record is not read by a stage. The reads are declared by this driver at its call sites, the
renderers' included (`DRAWN_INTERIORS`, `DRAWN_NAMES`); no stage records its own reads, so the
check is as true as those declarations and no truer.

The settings are the proof run's own (`data/measurements/codex-wiring-rereview-20261012`):
prominence 3 mm, and border offsets from -3 to 3 mm in 0.5 mm steps. The backend is the JIT twin
of the profile sampler, as that run used; its records are the reference's, checked run against run
on all 58 labelled studies, 2026-10-14: 336 series, every saved array the same.

Studies are measured in parallel, one worker process each, and each saves its own arrays; the main
process alone writes the receipts, in the order the studies were asked for. Pictures are drawn only
with `--draw`, from the saved run, after its study is in the receipt.

Run from anywhere: `.venv/bin/python scripts/run_interiors.py --study-uid <uid> [<uid> ...]`, or
`--labeled` for every labelled study whose series are all on disk; `--draw` for the pictures.
"""

import argparse
import json
import os
from collections.abc import Iterable, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, fields
from hashlib import sha256
from itertools import repeat
from pathlib import Path
from typing import Any

import numpy as np

import object_assignments
import object_interiors
from knee.collapse.physical import PlaneFrame
from knee.collapse.regime import read_regime
from knee.collapse.squint_stack import SquintStack, read_squint_stack
from knee.objects.assignments import (
    OBJECT_CODES,
    assign_plane,
    fibula_block,
    fibula_code,
    fibula_on_slice,
    main_slice,
)
from knee.objects.interiors import EDGE_KINDS, TRACE_CODES, read_interiors
from knee.receipt import merged_receipt
from knee.study.corpus import (
    LOCAL_ROOT,
    Corpus,
    open_corpus,
    read_study,
    series_directory,
)
from knee.study.series import Series, selected_slice
from knee.study.tables import labeled_uids
from knee.telemetry import Event, ledger, recording
from knee.telemetry.route import unread_products

ROOT = Path(__file__).resolve().parent.parent
PROMINENCE_MM = 3.0
OFFSETS_MM = (-3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0)
# The squint that points to where an object must be: tiles 10 mm wide, about a 16 x 16 grid on
# these fields (Rohan, 2026-10-12: «a 16x16 grid costs literally (n)^(1/2), for EVERYTHING»).
SQUINT_TILE_MM = 10.0
# The profile sampler's JIT twin; its records are the reference's (the contract's SAME).
BACKEND = "jit"
REQUEST = {
    "prominence_mm": PROMINENCE_MM,
    "offsets_mm": list(OFFSETS_MM),
    "slice_index": None,
    "backend": BACKEND,
}
# The squint's arrays, kept with each series as `squint_<name>`.
SQUINT_ARRAYS = ("median", "minimum", "maximum", "coverage", "centres_lps", "bounds_rc")
# What the two renderers read, from the saved run, of the interiors and of the names.
DRAWN_INTERIORS = (
    "code",
    "dark",
    "available",
    "distance_mm",
    "markers",
    "labels",
    "edge_points_rc",
    "edge_normals_rc",
    "edge_kinds",
    "trace_codes",
    "trace_points_rc",
)
DRAWN_NAMES = ("objects", "codes", "peaks", "femur", "tibia")


def handed(product: str, names: Iterable[str]) -> None:
    """The route's record that a stage handed `product` on, field by field."""
    for name in names:
        ledger.record(f"{product}.{name}.produced")


def reads(product: str, names: Iterable[str], stage: str) -> None:
    """The route's record, at the point of reading, of which fields of `product` `stage` read."""
    for name in names:
        ledger.record(f"{product}.{name}.consumed_by.{stage}")


def field_names(value: Any) -> list[str]:
    """The fields of a stage's product, a dataclass, in their declared order."""
    return [field.name for field in fields(value)]


def digest(array: np.ndarray) -> str:
    """The renderer's own check on a saved array: its dtype, shape and bytes."""
    return sha256(
        array.dtype.str.encode() + str(array.shape).encode() + array.tobytes()
    ).hexdigest()


def plane_frame(series: Series, index: int) -> PlaneFrame | str:
    """One slice's frame in the scanner's millimetres, or why its header does not read as one."""
    reads("series", ("geometry",), "frame")
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


def measure(
    series: Series,
) -> tuple[dict, dict[str, np.ndarray], SquintStack] | str:
    """One series' readings: the regime key and the squint, each kept whole, and the interiors and
    named objects at its middle slice; or why no plane was read."""
    reads("series", ("volume", "geometry"), "measure")
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
    reads("series", ("volume", "slices", "row"), "regime")
    regime = read_regime(series)
    if regime is not None:
        handed("regime", field_names(regime))
    split = regime.background_split if regime is not None else float("nan")
    # The squint, made once for the series and kept with it for any stage to consult; it records
    # its own reading of the series and its counted work on the ledger.
    reads("series", ("volume", "geometry", "row", "stack"), "squint_stack")
    stack = read_squint_stack(series, SQUINT_TILE_MM)
    handed("squint_stack", field_names(stack))
    # The header's own word for which knee this is ("R", "L", or blank); it sides the menisci.
    reads("series", ("slices",), "naming")
    knee = str(getattr(series.slices[index].header, "Laterality", "") or "").strip()
    record, arrays = name_plane(series, index, series.volume[index], frame, split, knee)
    record["regime"] = None if regime is None else asdict(regime)
    record["squint"] = {
        "code": stack.code,
        "why": stack.why,
        "tile_mm": stack.tile_mm,
        "tile_shape_rc": list(stack.tile_shape_rc),
    }
    for name in SQUINT_ARRAYS:
        arrays[f"squint_{name}"] = np.asarray(getattr(stack, name))
    return record, arrays, stack


def name_plane(
    series: Series,
    index: int,
    plane: np.ndarray,
    frame: PlaneFrame,
    split: float,
    knee: str,
) -> tuple[dict, dict[str, np.ndarray]]:
    """One slice's interiors and its named objects, as the record and arrays the renderers read."""
    reads("series", ("volume", "row", "slices"), "interiors")
    reads("regime", ("background_split",), "interiors")
    axes = frame.basis_lps / frame.spacing_rc
    reading = read_interiors(
        plane,
        frame.spacing_rc,
        split,
        PROMINENCE_MM,
        np.asarray(OFFSETS_MM),
        BACKEND,
        metric_rc=axes.T @ axes,
    )
    handed("interiors", field_names(reading))
    ledger.record(
        "interiors.work", planes=1, territories=int(reading.labels.max(initial=0))
    )
    reads("interiors", ("dark", "labels", "distance_mm"), "naming")
    assignment = assign_plane(plane, reading, frame.basis_lps, knee)
    handed("naming", field_names(assignment))
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
            "backend": BACKEND,
        },
        "assignments": {
            "knee": knee,
            "codes": assignment.codes,
            "femur": assignment.femur,
            "tibia": assignment.tibia,
            "menisci": assignment.menisci,
            "peaks": [asdict(peak) for peak in assignment.peaks],
        },
    }
    return record, arrays


def find_fibula(
    series: Series,
    record: dict,
    arrays: dict[str, np.ndarray],
    stack: SquintStack,
) -> tuple[dict, dict[str, np.ndarray]] | str:
    """The fibula named on its main slice, from the middle slice's tibia, or why it was not.

    The series' kept squint points to where the fibula must be (`fibula_block`: below the tibia's
    top, on the knee's outer side of its middle). The interiors lens then reads that block again
    on each slice that holds it, which the method forbids and the ledger counts
    (`fibula.lens_readings`); the fibula there is the region that looks like the tibia, well below
    its top and behind its middle, apart from the tibia (`fibula_on_slice`); and it is named on
    the slice where that region is largest.
    """
    assigned = record["assignments"]
    knee = assigned["knee"]
    reads("series", ("row",), "fibula")
    fat_suppressed = int(series.row.fat_suppression) == 1  # the tag is stored as text
    reads("naming", ("tibia",), "fibula")
    code = fibula_code(knee, assigned["tibia"] is not None, fat_suppressed, True)
    if code != "identified":
        return code
    volume = series.volume
    middle = plane_frame(series, record["slice_index"])
    if volume is None or isinstance(middle, str):
        return "geometry_unreadable"
    reads("naming", ("objects", "peaks"), "fibula")
    tibia = arrays["a1_objects"] == OBJECT_CODES["tibia"]
    top_mm = float(middle.to_patient(np.argwhere(tibia).astype(float))[:, 2].max())
    peak = next(p for p in assigned["peaks"] if p["territory"] == assigned["tibia"])
    middle_lps = middle.to_patient(np.asarray([peak["peak_rc"]], dtype=float))[0]
    reads("squint_stack", ("code",), "fibula")
    if stack.code != "present":
        return f"squint_{stack.code}"
    reads("squint_stack", ("centres_lps", "bounds_rc"), "fibula")
    reads("regime", ("background_split",), "fibula")
    reads("series", ("volume",), "fibula")
    split = record["background_split"]
    areas: list[float] = []
    found: list[tuple[int, int, np.ndarray, np.ndarray] | None] = []
    readings = 0
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
            BACKEND,
            metric_rc=axes.T @ axes,
        )
        readings += 1
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
    # The method forbids this: the lens read again on the block of every slice that holds it.
    ledger.record("fibula.lens_readings", planes=readings)
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
        menisci=0,
        tibia=tibia_region,
        fibula=fibula_region,
    )
    main_record["main_slice"] = {
        "object": "fibula",
        "areas_mm2": [round(area, 1) for area in areas],
    }
    handed("fibula", ("main_slice", "region"))
    return main_record, main_arrays


def save(run_dir: Path, study_uid: str, record: dict, arrays: dict) -> dict:
    """Save one record's arrays in the run and note them, with their digests, on the record."""
    artifact = Path(study_uid) / f"{record['series_uid']}.npz"
    np.savez_compressed(run_dir / artifact, allow_pickle=False, **arrays)
    record["study_uid"] = study_uid
    record["artifact"] = str(artifact)
    record["arrays"] = {name: {"digest": digest(a)} for name, a in arrays.items()}
    return record


def plain(value: object) -> object:
    """A NumPy number as the plain number JSON holds; anything else is refused by name."""
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"not_json_serializable: {type(value).__name__}")


def write_receipt(
    run_dir: Path,
    study_uid: str,
    series_uids: list[str],
    records: list[dict],
    unread: dict[str, str],
    telemetry: dict | None,
) -> None:
    """Merge one study into the run's receipt (`knee.receipt.merged_receipt`): its records,
    silences and telemetry replace what the receipt held for it, and every other study's stay."""
    path = run_dir / "receipt.json"
    old = json.loads(path.read_text()) if path.exists() else None
    receipt = merged_receipt(
        old, REQUEST, study_uid, series_uids, records, unread, telemetry
    )
    path.write_text(json.dumps(receipt, indent=2, default=plain) + "\n")


def ledger_reading(events: Sequence[Event], totals: dict[str, int]) -> dict:
    """One study's telemetry: each event's name with how often it came and its summed counted
    work, the run's totals, and every product produced and read by no stage."""
    by_name: dict[str, dict[str, int]] = {}
    for event in events:
        entry = by_name.setdefault(event.name, {"times": 0})
        entry["times"] += 1
        for key, value in event.counts.items():
            entry[key] = entry.get(key, 0) + value
    return {
        "events": by_name,
        "totals": totals,
        "read_by_no_stage": list(unread_products(event.name for event in events)),
    }


def named_parts(records: list[dict], main_records: list[dict]) -> dict[str, int]:
    """How many of the study's series named each object; the fibula, how many main slices."""
    named: dict[str, int] = {}
    for record in records:
        for name, code in record["assignments"]["codes"].items():
            if code in ("identified", "from_the_header"):
                named[name] = named.get(name, 0) + 1
    if main_records:
        named["fibula"] = len(main_records)
    return named


def measure_study(
    corpus: Corpus, study_uid: str, run_dir: Path, main_run: Path, drawn: bool
) -> dict:
    """Measure every series of one study with the ledger on and save its arrays; return what the
    receipts take (its records, silences and telemetry) and what it named. Writes no receipt, so
    studies can be measured side by side. `drawn` says whether its pictures will be drawn, since
    only then do the renderers read what they read."""
    (run_dir / study_uid).mkdir(parents=True, exist_ok=True)
    (main_run / study_uid).mkdir(parents=True, exist_ok=True)
    with recording() as led:
        study = read_study(corpus, study_uid)
        ledger.record(
            "study.produced",
            series=len(study.series),
            slices=sum(len(series.slices) for series in study.series),
        )
        records, unread = [], {}
        main_records, main_unread = [], {}
        for series in study.series:
            handed("series", field_names(series))
            measured = measure(series)
            if isinstance(measured, str):
                unread[series.row.series_uid] = measured
                continue
            record, arrays, stack = measured
            fibula = find_fibula(series, record, arrays, stack)
            records.append(save(run_dir, study_uid, record, arrays))
            if isinstance(fibula, str):
                main_unread[record["series_uid"]] = fibula
            else:
                main_records.append(save(main_run, study_uid, *fibula))
        # The renderers read the saved run, when they draw it: their reads are its last.
        if drawn and records:
            reads("interiors", DRAWN_INTERIORS, "draw")
            reads("naming", DRAWN_NAMES, "draw")
        if drawn and main_records:
            reads("fibula", ("main_slice", "region"), "draw")
        telemetry = ledger_reading(led.events(), led.totals())
    return {
        "study_uid": study_uid,
        "series_uids": [series.row.series_uid for series in study.series],
        "records": records,
        "unread": unread,
        "main_records": main_records,
        "main_unread": main_unread,
        "telemetry": telemetry,
        "named": named_parts(records, main_records),
    }


def measure_study_at(
    root: Path, study_uid: str, run_dir: Path, main_run: Path, drawn: bool
) -> dict:
    """`measure_study` in a worker process, which opens the corpus at `root` itself."""
    return measure_study(open_corpus(root), study_uid, run_dir, main_run, drawn)


def keep(result: dict, run_dir: Path, main_run: Path) -> None:
    """Merge one study's result into the run's two receipts: the one writer of either."""
    uid, series_uids = result["study_uid"], result["series_uids"]
    write_receipt(
        run_dir,
        uid,
        series_uids,
        result["records"],
        result["unread"],
        result["telemetry"],
    )
    write_receipt(
        main_run, uid, series_uids, result["main_records"], result["main_unread"], None
    )


def draw_study(
    result: dict,
    run_dir: Path,
    out: Path,
    assignments_out: Path,
    main_run: Path,
    main_out: Path,
) -> list[Path]:
    """Draw one study from the saved run, once it is in the receipts; return its pictures."""
    uid = result["study_uid"]
    pictures: list[Path] = []
    if result["records"]:
        object_interiors.draw(run_dir, uid, out)
        object_assignments.draw(run_dir, uid, assignments_out)
        pictures += [out / "series.png", assignments_out / "series.png"]
    if result["main_records"]:
        object_assignments.draw(main_run, uid, main_out)
        pictures.append(main_out / "series.png")
    return pictures


def on_disk(corpus: Corpus) -> list[str]:
    """Every labelled study whose series are all on disk, in the table's order."""
    found = []
    for uid in labeled_uids(corpus.tables):
        study = corpus.tables.studies[uid]
        if all(series_directory(corpus, study, s).is_dir() for s in study.series):
            found.append(uid)
    return found


def report(result: dict, args: argparse.Namespace) -> None:
    """Keep one study in the receipts, draw it when asked, and say what it named and what no
    stage read."""
    keep(result, args.run, args.main_run)
    uid = result["study_uid"]
    parts = ", ".join(f"{name} {count}" for name, count in result["named"].items())
    unread = ", ".join(result["telemetry"]["read_by_no_stage"])
    print(uid, flush=True)
    print(f"  named, by series: {parts or 'nothing'}", flush=True)
    print(f"  produced and read by no stage: {unread or 'none'}", flush=True)
    if args.draw:
        for picture in draw_study(
            result,
            args.run,
            args.out / uid,
            args.assignments_out / uid,
            args.main_run,
            args.main_out / uid,
        ):
            print(f"  {picture}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    which = parser.add_mutually_exclusive_group(required=True)
    which.add_argument("--study-uid", nargs="+")
    which.add_argument(
        "--labeled",
        action="store_true",
        help="every labelled study whose series are all on disk",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=os.cpu_count() or 1,
        help="studies measured side by side, one process each",
    )
    parser.add_argument(
        "--draw",
        action="store_true",
        help="draw each study's pictures from the saved run",
    )
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
    root = ROOT / LOCAL_ROOT
    corpus = open_corpus(root)
    uids = on_disk(corpus) if args.labeled else args.study_uid
    workers = max(1, min(args.workers, len(uids)))
    if workers == 1:
        for uid in uids:
            report(measure_study(corpus, uid, args.run, args.main_run, args.draw), args)
        return
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = pool.map(
            measure_study_at,
            repeat(root),
            uids,
            repeat(args.run),
            repeat(args.main_run),
            repeat(args.draw),
        )
        # In the order asked; this process alone writes the receipts.
        for result in results:
            report(result, args)


if __name__ == "__main__":
    main()
