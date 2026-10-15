"""The one run: every study it is given, read whole; each part of the knee named on it, or the
reason it is not; every reading kept.

For each series of a study: its background split, read once over the whole series, the level the
lens reads low signal under (`knee.collapse.noise.background_split`); the squint over every slice,
made once and kept with the series; the middle slice (the standard first slice,
`docs/RESOLVING_THE_PARTS.md` §8), its plane frame, and `read_interiors` with the frame's spacing
and the retained basis as its metric. Then
`assign_plane` names what the pictures show, each part by its paragraph in
`knee.objects.assignments`: air, skin, femur, tibia, joint, the patella (by its light, with fat
suppression), the menisci (sided by the header's own word for which knee it is), the articular
cartilage, the PCL, the MCL, the joint's fluid, Hoffa's fat pad, the suprapatellar fat and the fat
under the skin. Once
every series of the study is read, each middle slice is read with its partner's, the other sequence's slice of the
same place (`partner_of`, `read_with_partner`, and `knee.objects.assignments.with_partner`): bones
both name, where both agree; a part only the partner names, laid on. Then the extensor tendons are
named on the sagittal slice without fat suppression, where their band is plain, from the dark bands
its PCL was read from and the patella laid on from its partner, and laid onto that partner
(`name_the_extensor_tendons`); then the rest of the field on each slice without fat suppression,
the fat under the skin where its skin was laid on, and muscle, outside every part named and the
white its partner sees as fluid where that partner is fat-suppressed and fluid-sensitive, each
laid onto the partner (`name_the_rest_of_the_field`); no lens is read again. The arrays the renderers
read, and the squint's, are saved per series with their digests in a receipt;
`object_interiors.draw`, the renderer that drew the proof figure, draws the interiors, and
`object_assignments.draw` draws the named objects.

An object the middle slice does not show is named on its own main slice (AGENTS.md, the method's
first step), saved in a run of its own, one record per part and series, and drawn beside the
others. A part's own slice is read for its lens and its field only (`read_part_slice`: the leg, the
air and the skin, the territories' peaks, which way the slice faces), since the part's rule reads
nothing more; every other part of a slice's naming is not named there. Each slice's lens, field
and naming are made once (`lens_of`, `field_of`, `name_plane`), and what its rules weigh a place
against is its shared measure (`measures_of`), read once. The fibula (`find_fibula`) is named
there beside the tibia it was found against and nothing else. It reads the series' kept squint, but it still reads the interiors lens again on the block of
every slice that holds it, which the method forbids; the ledger counts those readings
(`fibula.lens_readings`) until its main slice comes from the squint. The ACL (`acl_slice`) is
named on the middle slice's neighbour on the knee's outer side, between the femur and the tibia
carried there from the middle slice. Its slice is chosen by place, from the header's word for which
knee, not read off the squint; the lens is read once more, on that slice of each sagittal series
(`acl.lens_readings`); the ACL is named where fat is suppressed and laid onto the other sequence's
slice of the same place (`find_part`, `lay_part`). The LCL (`lcl_slice`) is named on the coronal
slice through the place where it attaches on the fibula, the fibula being the one found on its
main slice, its places handed on from there (`find_fibula`); the lens is read once more, on that slice
of each coronal series (`lcl.lens_readings`); the LCL is named where fat is not suppressed and laid
onto the other sequence's slice of the same place. A series' silence on a main-slice part is kept
as `<series uid>:<part>`.

THE BACK OF THE KNEE is named on the series the leg runs through, an axial one. Where the header
names the knee there, the femur and the tibia named on the study's middle slices where the leg
runs in the plane are put in the scanner's millimetres once, with the notch's plane from the
middle sagittal slice (`leg_of`, the `leg` product), and carried by place onto each slice a part
is named on (`carry_onto`, the `carried` product). The medial gastrocnemius head is named on the
middle slice, whose lens the run has already read, behind the bone's inner condyle
(`name_the_back_of_the_knee`), before the records are saved. The semimembranosus tendon is named
on its own slice, the top of the tibia just below the joint line, found by carrying the leg onto
each slice of the series (`semimembranosus_slice`); the lens is read once more there
(`semimembranosus.lens_readings`), and the tendon is laid onto the other sequence's slice of the
same place where that one finds none.

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
with `--draw`, from the saved run, after its study is in the receipt; the drawing layer is imported
only then, so a run that draws nothing never loads it.

Run from anywhere: `.venv/bin/python scripts/run_interiors.py --study-uid <uid> [<uid> ...]`;
`--labeled` for every labelled study whose series are all on disk; `--split test` (or `train`) for
every study of that split whose series are all on disk, the test split being the studies a Kaggle
kernel is given; `--root` for where the competition's files are (where a kernel mounts them,
`knee.study.corpus.KAGGLE_ROOT`, when that exists, else `data/raw`); `--draw` for the pictures.
"""

import argparse
import json
import os
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, fields
from functools import cache
from itertools import repeat
from pathlib import Path
from typing import Any

import numpy as np

from knee.collapse.noise import background_split, finite_values
from knee.collapse.physical import PlaneFrame
from knee.collapse.squint_stack import SquintStack, read_squint_stack
from knee.compute.contracts import handed_on
from knee.objects.assignments import (
    FLUID_BRIGHTER,
    NAMED,
    OBJECT_CODES,
    SLICE_PARTS,
    Field,
    Measures,
    PlaneAssignment,
    acl_code,
    acl_on_slice,
    anterior_synovial_recess,
    assign_plane,
    bursa_code,
    bursa_on_slice,
    capsule_at_side_recesses,
    capsule_code,
    carried_bone,
    extensor_tendons,
    fat_under_the_skin,
    fibula_block,
    fibula_code,
    fibula_on_slice,
    gastrocnemius_code,
    gastrocnemius_head,
    inner_condyle,
    laid_by,
    lcl_attachment,
    lcl_code,
    lcl_on_slice,
    main_slice,
    margin,
    muscle_bodies,
    muscle_code,
    outer_step,
    places_from,
    places_on_slice,
    read_field,
    region_holding,
    semimembranosus_code,
    semimembranosus_on_slice,
    slice_through,
    subcutaneous_code,
    synovium_code,
    tendon_code,
    tibia_top_slice,
    with_partner,
)
from knee.objects.interiors import (
    EDGE_KINDS,
    TRACE_CODES,
    InteriorReading,
    interior_regions,
    read_interiors,
)
from knee.receipt import digest, merged_receipt
from knee.study.corpus import (
    KAGGLE_ROOT,
    LOCAL_ROOT,
    Corpus,
    open_corpus,
    read_study,
    series_directory,
)
from knee.study.series import Series, selected_slice
from knee.study.tables import SPLIT_FOLDER, labeled_uids, split_uids
from knee.telemetry import Event, computing, ledger, once, recording
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
DRAWN_NAMES = ("objects", "codes", "peaks", "femur", "tibia", "patella")
# The parts named on a main slice of their own; a series' silence on each is `<series uid>:<part>`.
MAIN_PARTS = ("fibula", "acl", "lcl", "semimembranosus")


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


def frame_reading(series: Series, z: int) -> PlaneFrame | ValueError:
    """One slice's frame in the scanner's millimetres, or the error its header raised: made once
    per slice and handed to every stage that asks for it (the squint, which reads every slice's
    first, then the middle slice and each part's own slice)."""

    def make() -> PlaneFrame | ValueError:
        reads("series", ("geometry",), "frame")
        geometry = series.geometry
        if geometry is None:
            return ValueError("the series has no geometry")
        try:
            return PlaneFrame.from_dicom(
                geometry.position[z], geometry.orientation[z], geometry.spacing[z]
            )
        except ValueError as error:
            return error

    return once("frame", (series.row.series_uid, z), make)


def plane_frame(series: Series, index: int) -> PlaneFrame | str:
    """One slice's frame (`frame_reading`), or why its header does not read as one."""
    if series.geometry is None:
        return "geometry_unreadable"
    frame = frame_reading(series, index)
    return f"geometry_unreadable: {frame}" if isinstance(frame, ValueError) else frame


def finite_of(series: Series) -> np.ndarray:
    """Which of a series' stored values are finite, (Z, R, C): read once for the series and handed
    to the background split, the squint and every lens read on its slices."""
    return once(
        "finite", series.row.series_uid, lambda: np.isfinite(np.asarray(series.volume))
    )


def margin_of(series_uid: str, z: int, plane: np.ndarray) -> np.ndarray:
    """One slice's black margin (`margin`), found once per slice and handed to every stage that
    asks: the slice's naming, its reading with its partner, and each part laid onto or from it."""
    return once("margin", (series_uid, z), lambda: margin(plane))


def matched(
    onto_series: Series,
    onto: dict,
    onto_frame: PlaneFrame,
    onto_shape: tuple[int, int],
    source: dict,
    source_frame: PlaneFrame,
    source_plane: np.ndarray,
) -> np.ndarray | str:
    """The places of one slice (`onto`, its record) matched to those of another slice of the same
    knee (`source`), by `places_from`: made once for the pair, in this direction, and handed to
    every stage that lays a reading across (the partner reading, the tendons, the rest of the
    field, a part laid onto its own slice); or why not: this slice's thickness is not in its
    header ("no_slice_thickness"), or the two are not the same place ("not_the_same_place")."""

    def make() -> np.ndarray | str:
        reads("series", ("slice_thickness_mm",), "match")
        thickness = onto_series.slice_thickness_mm[onto["slice_index"]]
        if thickness is None:
            return "no_slice_thickness"
        places = places_from(
            ~margin_of(source["series_uid"], source["slice_index"], source_plane),
            source_frame,
            onto_frame,
            onto_shape,
            thickness,
        )
        return "not_the_same_place" if places is None else places

    key = (
        onto["series_uid"],
        onto["slice_index"],
        source["series_uid"],
        source["slice_index"],
    )
    return once("match", key, make)


@dataclass(frozen=True, slots=True)
class Measured:
    """One series as `measure` read it: the record and arrays the run keeps, its squint, the named
    objects of its middle slice, and that slice's frame."""

    series: Series
    record: dict
    arrays: dict[str, np.ndarray]
    stack: SquintStack
    assignment: PlaneAssignment
    frame: PlaneFrame


def measure(series: Series) -> Measured | str:
    """One series' readings: its background split and its squint, each read once over the whole
    series, and the interiors and named objects at its middle slice; or why no plane was read.
    Which of its values are finite, and every slice's frame, are read once here and handed to the
    split, the squint and the lens."""
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
    finite = finite_of(series)
    # The background split: the valley after the background's mode in the series' own histogram
    # (`knee.collapse.noise.background_split`), the level the lens reads low signal under.
    reads("series", ("volume",), "background")
    split = background_split(finite_values(series.volume, finite))
    handed("background", ("split",))
    # The squint, made once for the series and kept with it for any stage to consult; it records
    # its own reading of the series and its counted work on the ledger. It reads every slice's
    # frame, made once for the squint and every stage after it.
    reads("series", ("volume", "geometry", "row", "stack"), "squint_stack")
    stack = read_squint_stack(
        series, SQUINT_TILE_MM, lambda z: frame_reading(series, z), finite
    )
    handed("squint_stack", field_names(stack))
    # The header's own word for which knee this is ("R", "L", or blank); it sides the menisci.
    reads("series", ("slices",), "naming")
    knee = str(getattr(series.slices[index].header, "Laterality", "") or "").strip()
    record, arrays, assignment = name_plane(
        series, index, series.volume[index], frame, split, knee
    )
    record["squint"] = {
        "code": stack.code,
        "why": stack.why,
        "tile_mm": stack.tile_mm,
        "tile_shape_rc": list(stack.tile_shape_rc),
    }
    for name in SQUINT_ARRAYS:
        arrays[f"squint_{name}"] = np.asarray(getattr(stack, name))
    return Measured(series, record, arrays, stack, assignment, frame)


def lens_of(
    series: Series,
    index: int,
    plane: np.ndarray,
    frame: PlaneFrame,
    split: float,
    reader: str | None = None,
) -> tuple[np.ndarray, InteriorReading, dict]:
    """One slice's lens reading, made once per slice and handed to every stage that asks for that
    slice (its naming, and a part named on it, whose slice may be the middle slice or another
    part's): the acquired plane, the interiors, and what the record says of them. `reader` is the
    part whose own slice this is, whose lens readings the ledger counts."""

    def read() -> tuple[np.ndarray, InteriorReading, dict]:
        reads("series", ("volume", "row", "slices"), "interiors")
        reads("background", ("split",), "interiors")
        axes = frame.basis_lps / frame.spacing_rc
        reading = read_interiors(
            plane,
            frame.spacing_rc,
            split,
            PROMINENCE_MM,
            np.asarray(OFFSETS_MM),
            BACKEND,
            metric_rc=axes.T @ axes,
            available=finite_of(series)[index],
        )
        handed("interiors", field_names(reading))
        ledger.record(
            "interiors.work", planes=1, territories=int(reading.labels.max(initial=0))
        )
        if reader is not None:
            ledger.record(f"{reader}.lens_readings", planes=1)
        interiors = {
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
        }
        # frozen, as the interiors' own fields are: every stage that reads the slice is handed it
        return handed_on(plane.copy()), reading, interiors

    return once("lens", (series.row.series_uid, index), read)


def field_of(
    series: Series,
    index: int,
    plane: np.ndarray,
    frame: PlaneFrame,
    reading: InteriorReading,
) -> Field:
    """One slice's field (`read_field`: the leg, the air and the skin, the territories' peaks, which
    way the slice faces), made once per slice and handed to its naming and to any part named on
    it, which reads nothing more."""
    uid = series.row.series_uid

    def read() -> Field:
        reads("interiors", ("dark", "labels", "distance_mm"), "field")
        field = read_field(
            plane, reading, frame.basis_lps, margin_of(uid, index, plane)
        )
        handed("field", field_names(field))
        return field

    return once("field", (uid, index), read)


def measures_of(uid: str, index: int, plane: np.ndarray, frame: PlaneFrame) -> Measures:
    """One slice's shared measures (`knee.objects.assignments.Measures`), kept under its series and
    index: each stage that weighs a place on the slice is handed what an earlier one read there."""
    return Measures((uid, index), plane, frame.basis_lps)


def slice_record(
    series: Series,
    index: int,
    split: float,
    knee: str,
    lens: tuple[np.ndarray, InteriorReading, dict],
    field: Field,
) -> tuple[dict, dict[str, np.ndarray]]:
    """The record and arrays one slice's reading makes before a part is named on it: the lens's
    arrays and what the record says of them, the field's names and peaks, and every part of a
    slice's naming (`SLICE_PARTS`) not named there, until the stage that names one says so."""
    acquired, reading, interiors = lens
    arrays = {
        "acquired_plane": acquired,
        "b1_dark": reading.dark,
        "b1_available": reading.available,
        "b1_distance_mm": reading.distance_mm,
        "b1_markers": reading.markers,
        "b1_labels": reading.labels,
        "b1_edge_points_rc": reading.edge_points_rc,
        "b1_edge_normals_rc": reading.edge_normals_rc,
        "b1_trace_codes": reading.trace_codes,
        "b1_trace_points_rc": reading.trace_points_rc,
        "a1_objects": field.objects,
    }
    row = series.row
    record = {
        "series_uid": row.series_uid,
        "view": [row.anatomical_plane, row.fluid_sensitive, row.fat_suppression],
        "slice_index": index,
        "source_plane": series.slices[index].path.name,
        "background_split": split,
        "interiors": dict(interiors),
        "assignments": {
            "knee": knee,
            "codes": dict.fromkeys(SLICE_PARTS, "not_named_on_this_slice"),
            "femur": None,
            "tibia": None,
            "patella": None,
            "peaks": [asdict(peak) for peak in field.peaks],
        },
    }
    return record, arrays


def name_plane(
    series: Series,
    index: int,
    plane: np.ndarray,
    frame: PlaneFrame,
    split: float,
    knee: str,
) -> tuple[dict, dict[str, np.ndarray], PlaneAssignment]:
    """A middle slice read and named: its lens (`lens_of`) and its field (`field_of`), and the parts
    named on it alone (`assign_plane`, with the slice's shared measures), each made once per slice;
    the record and arrays the renderers read, and the named objects themselves."""
    uid = series.row.series_uid
    lens = lens_of(series, index, plane, frame, split)
    field = field_of(series, index, plane, frame, lens[1])

    def name() -> PlaneAssignment:
        reads("field", field_names(field), "naming")
        reads("interiors", ("dark", "labels"), "naming")
        fat_suppressed = (
            int(series.row.fat_suppression) == 1
        )  # the tags are stored as text
        fluid_sensitive = int(series.row.fluid_sensitive) == 1
        assignment = assign_plane(
            plane,
            lens[1],
            frame.basis_lps,
            knee,
            fat_suppressed,
            fluid_sensitive,
            margin_of(uid, index, plane),
            field,
            measures_of(uid, index, plane, frame),
        )
        handed("naming", field_names(assignment))
        return assignment

    assignment = once("naming", (uid, index), name)
    record, arrays = slice_record(series, index, split, knee, lens, field)
    arrays["a1_objects"] = assignment.objects
    # a copy: the stages after this change the record's codes, never the slice's own
    record["assignments"].update(
        codes=dict(assignment.codes),
        femur=assignment.femur,
        tibia=assignment.tibia,
        patella=assignment.patella,
    )
    return record, arrays, assignment


def read_part_slice(
    series: Series,
    index: int,
    plane: np.ndarray,
    frame: PlaneFrame,
    split: float,
    knee: str,
    reader: str | None = None,
) -> tuple[dict, dict[str, np.ndarray], Field]:
    """A part's own slice read: its lens (`lens_of`) and its field (`field_of`), each made once per
    slice, and nothing else named on it, since the part's own rule names it and reads nothing more;
    every other part of a slice's naming is not named there. `reader` is the part, whose lens
    readings the ledger counts."""
    lens = lens_of(series, index, plane, frame, split, reader)
    field = field_of(series, index, plane, frame, lens[1])
    record, arrays = slice_record(series, index, split, knee, lens, field)
    return record, arrays, field


def partner_of(measured: list[Measured], index: int) -> Measured | None:
    """The series whose middle slice is the same place in the other sequence: the first of the same
    plane with the other fat-suppression tag that `laid_on` finds on the same plane. None when there
    is none."""
    reads("series", ("row",), "partner")
    own = measured[index]
    for other in measured:
        same = other.series.row.anatomical_plane == own.series.row.anatomical_plane
        other_sequence = (
            other.series.row.fat_suppression != own.series.row.fat_suppression
        )
        if other is not own and same and other_sequence:
            return other
    return None


def read_with_partner(own: Measured, partner: Measured) -> str:
    """Read one series' middle slice with its partner's (`with_partner`), keeping the result in its
    record and arrays; or say why it was not: the two slices are not the same place, or this
    slice's thickness is not in its header to say so. The two slices' places are matched once
    (`matched`), and every later stage that lays a reading across reuses the match."""
    plane = own.arrays["acquired_plane"]
    source = matched(
        own.series,
        own.record,
        own.frame,
        plane.shape,
        partner.record,
        partner.frame,
        partner.arrays["acquired_plane"],
    )
    if isinstance(source, str):
        return source
    reads("naming", ("objects", "codes", "peaks"), "partner")
    reads("interiors", ("labels",), "partner")
    objects, codes = with_partner(
        own.assignment,
        own.arrays["b1_labels"],
        own.frame.basis_lps,
        margin_of(own.record["series_uid"], own.record["slice_index"], plane),
        laid_by(partner.assignment.objects, source),
        partner.assignment.codes,
    )
    handed("partner", ("objects", "codes"))
    own.arrays["a1_objects"] = objects
    own.record["assignments"]["codes"] = codes
    # A bone the two slices do not agree on, or one laid on from the partner, has no territory of
    # this slice's own.
    for name in ("femur", "tibia", "patella"):
        if codes.get(name) not in ("identified", "agreed_with_its_partner"):
            own.record["assignments"][name] = None
    return "read_with_" + partner.record["series_uid"]


def leg_on(
    leg: "Leg",
    series: Series,
    z: int,
    frame: PlaneFrame,
    shape: tuple[int, int],
    thickness: float,
) -> tuple[np.ndarray, np.ndarray]:
    """The leg's femur and tibia carried by place onto one slice of a series the leg runs through
    (`places_on_slice`): made once per slice and handed to every stage that asks for it (the
    search for the top of the tibia, and the back of the knee's parts on their slices)."""
    return once(
        "leg_on_slice",
        (series.row.series_uid, z),
        lambda: (
            places_on_slice(leg.femur_lps, frame, shape, thickness),
            places_on_slice(leg.tibia_lps, frame, shape, thickness),
        ),
    )


@dataclass(frozen=True, slots=True)
class Leg:
    """The femur and the tibia named on a study's middle slices where the leg runs in the plane, in
    the scanner's millimetres, and the notch's plane, where the first middle sagittal slice passes
    (None without one), its normal toward the patient's left: one leg, one set of objects, made
    once for every slice it is carried onto."""

    femur_lps: np.ndarray
    tibia_lps: np.ndarray
    notch_origin_lps: np.ndarray | None
    notch_normal: np.ndarray | None


@dataclass(frozen=True, slots=True)
class Carried:
    """The leg's bones carried onto one slice the leg runs through: the femur's and the tibia's
    places there, each place's position toward the back, and its distance toward the patient's
    left of the notch (None when the study has no sagittal slice)."""

    femur: np.ndarray
    tibia: np.ndarray
    back_mm: np.ndarray
    toward_left_mm: np.ndarray | None


def leg_of(measured: list[Measured]) -> Leg:
    """The study's leg: the femur and the tibia of its middle slices where the leg runs in the
    plane, as their partner reading left them, in the scanner's millimetres; and the notch's plane
    from the first of them that side to side runs through, a sagittal one. Which way each slice
    faces is its naming's (`PlaneAssignment.in_plane`), read once."""
    reads("partner", ("objects",), "leg")
    reads("naming", ("in_plane",), "leg")
    femur, tibia = [np.zeros((0, 3))], [np.zeros((0, 3))]
    notch_origin = notch_normal = None
    for other in measured:
        sides_in_plane, _, leg_in_plane = other.assignment.in_plane
        if not leg_in_plane:
            continue
        objects = other.arrays["a1_objects"]
        for name, found in (("femur", femur), ("tibia", tibia)):
            places = np.argwhere(objects == OBJECT_CODES[name]).astype(float)
            found.append(other.frame.to_patient(places))
        if notch_origin is None and not sides_in_plane:
            normal = other.frame.normal()
            notch_origin = other.frame.origin_lps
            notch_normal = normal if normal[0] > 0 else -normal
    leg = Leg(np.concatenate(femur), np.concatenate(tibia), notch_origin, notch_normal)
    handed("leg", field_names(leg))
    return leg


def carry_onto(
    leg: Leg,
    series: Series,
    z: int,
    frame: PlaneFrame,
    shape: tuple[int, int],
    thickness: float,
) -> Carried:
    """The leg's bones carried by place onto one slice the leg runs through (`leg_on`, made once
    per slice), with each place's position toward the back and toward the patient's left of the
    notch."""
    reads(
        "leg", ("femur_lps", "tibia_lps", "notch_origin_lps", "notch_normal"), "carry"
    )
    femur, tibia = leg_on(leg, series, z, frame, shape, thickness)
    rows, cols = np.indices(shape)
    places = frame.to_patient(
        np.column_stack((rows.ravel(), cols.ravel())).astype(float)
    ).reshape(*shape, 3)
    toward_left = None
    if leg.notch_origin_lps is not None and leg.notch_normal is not None:
        toward_left = (places - leg.notch_origin_lps) @ leg.notch_normal
    carried = Carried(femur, tibia, places[..., 1], toward_left)
    handed("carried", field_names(carried))
    return carried


def name_the_back_of_the_knee(own: Measured, leg: Leg | None) -> str:
    """The medial gastrocnemius head named on this series' middle slice (its paragraph in
    `knee.objects.assignments`), from the lens the run has already read there and the study's leg
    carried onto it (`carry_onto`), which is carried only once its first three descriptions hold,
    so nothing is carried that no part reads; its code, or why the bones were not carried. No
    lens is read again."""
    assigned = own.record["assignments"]
    knee = assigned["knee"]
    reads("series", ("row",), "gastrocnemius")
    reads("naming", ("in_plane",), "gastrocnemius")
    # the tag is stored as text
    fat_suppressed = int(own.series.row.fat_suppression) == 1
    code = gastrocnemius_code(
        not own.assignment.in_plane[2], knee, fat_suppressed, True, True, True, True
    )
    if code != "identified" or leg is None:
        return code
    reads("series", ("slice_thickness_mm",), "gastrocnemius")
    thickness = own.series.slice_thickness_mm[own.record["slice_index"]]
    if thickness is None:
        return "no_slice_thickness"
    carried = carry_onto(
        leg,
        own.series,
        own.record["slice_index"],
        own.frame,
        own.arrays["acquired_plane"].shape,
        float(thickness),
    )
    reads("carried", ("femur", "tibia", "back_mm", "toward_left_mm"), "gastrocnemius")
    bone = carried.femur | carried.tibia
    notch = carried.toward_left_mm
    if not bone.any() or notch is None:
        return gastrocnemius_code(
            True, knee, True, bool(bone.any()), notch is not None, False, False
        )
    reads("naming", ("peaks",), "gastrocnemius")
    reads("interiors", ("labels",), "gastrocnemius")
    labels = own.arrays["b1_labels"]
    # the inner side is toward the other knee: the patient's left for a right knee
    inner_mm = notch if knee == "R" else -notch
    condyle = inner_condyle(own.assignment.peaks, labels, bone, inner_mm)
    head = np.zeros(labels.shape, dtype=bool)
    if condyle is not None:
        head = gastrocnemius_head(
            own.assignment.peaks, labels, bone, condyle, carried.back_mm, inner_mm
        )
    # a copy: the names the slice made alone (`Measured.assignment`) stay as made
    objects = own.arrays["a1_objects"].copy()
    placed = head & (objects == 0)
    objects[placed] = OBJECT_CODES["medial_gastrocnemius"]
    own.arrays["a1_objects"] = objects
    assigned["medial_gastrocnemius"] = int(labels[head].max()) if head.any() else None
    if placed.any():
        handed("gastrocnemius", ("region",))
    return gastrocnemius_code(
        True, knee, True, True, True, condyle is not None, bool(placed.any())
    )


def name_the_extensor_tendons(own: Measured, partner: Measured | None) -> None:
    """The patellar and quadriceps tendons named on this series' middle slice where their band is
    plain (their paragraph in `knee.objects.assignments`): a sagittal slice without fat
    suppression, from the dark bands its PCL was read from (`PlaneAssignment.bands`) and the
    patella laid on from its partner, the fat-suppressed slice of the same place; then laid onto
    that partner by place, where its fat pads beside the patella yield to them. Each slice's codes
    are set; no lens is read again."""
    reads("naming", ("bands",), "tendons")
    bands = own.assignment.bands
    if bands is None:
        return
    reads("partner", ("objects",), "tendons")
    # a copy: the names the slice made alone (`Measured.assignment`) stay as made
    objects = own.arrays["a1_objects"].copy()
    patellar, quadriceps = extensor_tendons(
        bands,
        objects,
        np.asarray(own.frame.spacing_rc),
        own.frame.basis_lps,
        measures_of(
            own.record["series_uid"],
            own.record["slice_index"],
            own.arrays["acquired_plane"],
            own.frame,
        ),
    )
    ends = bool(
        (objects == OBJECT_CODES["patella"]).any()
        and (objects == OBJECT_CODES["tibia"]).any()
    )
    codes = own.record["assignments"]["codes"]
    for name, tendon, above in (
        ("patellar_tendon", patellar, False),
        ("quadriceps_tendon", quadriceps, True),
    ):
        objects[tendon] = OBJECT_CODES[name]
        codes[name] = tendon_code(True, False, ends, bool(tendon.any()), above)
    own.arrays["a1_objects"] = objects
    if not (patellar.any() or quadriceps.any()):
        return
    handed("tendons", ("region",))
    if partner is None:
        return
    fat = (OBJECT_CODES["hoffa_fat_pad"], OBJECT_CODES["suprapatellar_fat"])
    laid = lay_parts(
        partner,
        (partner.record, partner.arrays, partner.frame),
        (own.record, own.arrays, own.frame),
        ("patellar_tendon", "quadriceps_tendon"),
        fat,
        # with fat suppression the band is the border between two of the lens's regions
        onto_borders=True,
    )
    for name, code in laid.items():
        if code is not None:
            partner.record["assignments"]["codes"][name] = code


def partner_white(own: Measured, partner: Measured | None) -> np.ndarray:
    """At this series' middle slice's places, where its partner, the other sequence's slice of the
    same place, sees white as fluid: the white the partner kept where it is fat-suppressed and
    fluid-sensitive (`PlaneAssignment.white`), laid on by the pair's one match (`matched`). None
    of it where there is no such partner, this slice's thickness is not in its header, the two are
    not the same place, or the partner's picture does not reach: there nothing tells fluid apart."""
    none = np.zeros(own.arrays["acquired_plane"].shape, dtype=bool)
    if partner is None:
        return none
    reads("naming", ("white",), "rest_of_the_field")
    white = partner.assignment.white
    if white is None:
        return none
    source = matched(
        own.series,
        own.record,
        own.frame,
        none.shape,
        partner.record,
        partner.frame,
        partner.arrays["acquired_plane"],
    )
    if isinstance(source, str):
        return none
    return laid_by(white.astype(np.int8), source) == 1


def name_the_rest_of_the_field(own: Measured, partner: Measured | None) -> None:
    """The rest of the field (their paragraphs in `knee.objects.assignments`), the fat under the
    skin and then muscle, on this series' middle slice where fat is not suppressed, once it is read
    with its partner: the fat where the slice read the skin only once its partner's was laid on,
    from its light; muscle on every such slice, outside every part named and the white its partner
    sees as fluid where that partner is fat-suppressed and fluid-sensitive (`partner_white`, laid
    on only where muscle can be named). The femur's marrow light both weigh their places against
    is the slice's shared measure (`measures_of`), read once, and each part a slice names from its
    own light is laid onto its partner by the pair's one match. No lens is read again."""
    reads("series", ("row",), "rest_of_the_field")
    # the tags are stored as text
    if int(own.series.row.fat_suppression) == 1:
        return
    reads("partner", ("objects", "codes"), "rest_of_the_field")
    codes = own.record["assignments"]["codes"]
    # a copy: the names the slice made alone (`Measured.assignment`) stay as made
    objects = own.arrays["a1_objects"].copy()
    plane = own.arrays["acquired_plane"]
    spacing = np.asarray(own.frame.spacing_rc)
    measures = measures_of(
        own.record["series_uid"], own.record["slice_index"], plane, own.frame
    )
    femur_named = bool((objects == OBJECT_CODES["femur"]).any())
    air_named = bool((objects == OBJECT_CODES["air"]).any())
    laid_skin = codes.get("subcutaneous_fat") == "abstain_no_skin" and bool(
        (objects == OBJECT_CODES["skin"]).any()
    )
    if laid_skin:
        fat = fat_under_the_skin(plane, objects, spacing, measures)
        objects[fat] = OBJECT_CODES["subcutaneous_fat"]
        codes["subcutaneous_fat"] = subcutaneous_code(
            False, True, femur_named, bool(fat.any())
        )
    # muscle is named only where the slice names air and the femur, so only there is the white
    # its partner sees laid on
    white = (
        partner_white(own, partner)
        if air_named and femur_named
        else np.zeros(plane.shape, dtype=bool)
    )
    muscle = muscle_bodies(
        plane,
        objects,
        spacing,
        margin_of(own.record["series_uid"], own.record["slice_index"], plane),
        white,
        measures,
    )
    objects[muscle] = OBJECT_CODES["muscle"]
    codes["muscle"] = muscle_code(False, air_named, femur_named, bool(muscle.any()))
    own.arrays["a1_objects"] = objects
    # only a slice that names them from its own light lays them on: one they were laid onto does
    # not lay them back
    parts = tuple(
        name
        for name in ("subcutaneous_fat", "muscle")
        if codes.get(name) == "identified"
    )
    if not parts:
        return
    handed("rest_of_the_field", ("region",))
    if partner is None:
        return
    laid = lay_parts(
        partner,
        (partner.record, partner.arrays, partner.frame),
        (own.record, own.arrays, own.frame),
        parts,
    )
    for name, code in laid.items():
        if code is not None:
            partner.record["assignments"]["codes"][name] = code


def name_joint_boundaries(own: Measured, partner: Measured | None) -> None:
    """Locate the anterior recess, its lining surface, and the side recesses' capsular wall.

    Save separate masks where tissue surfaces coexist with fluid or collateral structures.
    Reuse the white reading, shared physical positions, and the pair's physical-place match.
    """
    reads("series", ("row",), "joint_boundaries")
    reads("naming", ("in_plane", "white"), "joint_boundaries")
    reads("partner", ("objects", "codes"), "joint_boundaries")
    objects = own.arrays["a1_objects"]
    codes = own.record["assignments"]["codes"]
    sagittal = own.assignment.in_plane[1] and own.assignment.in_plane[2]
    coronal = own.assignment.in_plane[0] and own.assignment.in_plane[2]
    bright = (
        int(own.series.row.fat_suppression) == 1
        and int(own.series.row.fluid_sensitive) == 1
    )
    has_patella = bool((objects == OBJECT_CODES["patella"]).any())
    has_femur = bool((objects == OBJECT_CODES["femur"]).any())
    has_menisci = all(
        (objects == OBJECT_CODES[name]).any()
        for name in ("medial_meniscus", "lateral_meniscus")
    )
    white = own.assignment.white
    recess = lining = capsule = np.zeros(objects.shape, dtype=bool)
    measures = measures_of(
        own.record["series_uid"],
        own.record["slice_index"],
        own.arrays["acquired_plane"],
        own.frame,
    )
    if sagittal and bright and has_patella and has_femur and white is not None:
        recess, lining = anterior_synovial_recess(
            white,
            objects,
            own.frame.basis_lps,
            measures,
        )
    if coronal and bright and has_femur and has_menisci and white is not None:
        reads("interiors", ("dark",), "joint_boundaries")
        capsule = capsule_at_side_recesses(
            own.arrays["b1_dark"],
            white,
            objects,
            own.frame.basis_lps,
            np.asarray(own.frame.spacing_rc),
            measures,
        )
    recess_code = synovium_code(
        sagittal, bright, has_patella, has_femur, bool(recess.any())
    )
    lining_code = (
        recess_code
        if lining.any() or recess_code != "identified"
        else "abstain_no_fat_facing_surface"
    )
    wall_code = capsule_code(
        coronal, bright, has_femur, has_menisci, bool(capsule.any())
    )
    parts = (
        ("anterior_synovial_recess", recess, recess_code),
        ("synovium", lining, lining_code),
        ("joint_capsule", capsule, wall_code),
    )
    for name, mask, code in parts:
        own.arrays[f"a2_{name}"] = mask
        codes[name] = code
    handed("joint_boundaries", ("recess", "lining", "capsule"))
    if partner is None or not any(code == "identified" for _, _, code in parts):
        return
    reads("joint_boundaries", ("recess", "lining", "capsule"), "partner")
    source = matched(
        partner.series,
        partner.record,
        partner.frame,
        partner.arrays["acquired_plane"].shape,
        own.record,
        own.frame,
        own.arrays["acquired_plane"],
    )
    if isinstance(source, str):
        return
    for name, mask, code in parts:
        if code != "identified":
            continue
        placed = laid_by(mask.astype(np.int16), source) == 1
        partner.arrays[f"a2_{name}"] = placed
        partner.record["assignments"]["codes"][name] = (
            "laid_from_its_partner"
            if placed.any()
            else "abstain_outside_partner_picture"
        )


def semimembranosus_slice(
    own: Measured, leg: Leg | None
) -> tuple[dict, dict[str, np.ndarray], PlaneFrame] | str:
    """The semimembranosus tendon's slice of one series, read (its paragraph in
    `knee.objects.assignments`): the slice through the top of the tibia, just below the joint
    line, found by carrying the study's leg onto each slice of the series (no lens; `leg_on`, each
    slice's once), where the lens is then read once more; the tendon named at the tibia's
    back-inner corner; or why it was not read."""
    assigned = own.record["assignments"]
    knee = assigned["knee"]
    reads("naming", ("in_plane",), "semimembranosus")
    code = semimembranosus_code(
        not own.assignment.in_plane[2], knee, True, True, True, True, True
    )
    if code != "identified" or leg is None:
        return code
    reads("leg", ("tibia_lps", "notch_origin_lps"), "semimembranosus")
    if not len(leg.tibia_lps) or leg.notch_origin_lps is None:
        return semimembranosus_code(
            True, knee, bool(len(leg.tibia_lps)), False, False, False, False
        )
    reads("series", ("volume", "geometry", "slice_thickness_mm"), "semimembranosus")
    volume, thicknesses = own.series.volume, own.series.slice_thickness_mm
    if volume is None:
        return "no_stacked_volume"
    femur_held, tibia_held, up_mm = [], [], []
    for z in range(len(volume)):
        frame, thickness = plane_frame(own.series, z), thicknesses[z]
        shape = np.asarray(volume[z]).shape
        held = [False, False]
        if not isinstance(frame, str) and thickness is not None:
            held = [
                bool(places.any())
                for places in leg_on(leg, own.series, z, frame, shape, thickness)
            ]
        femur_held.append(held[0])
        tibia_held.append(held[1])
        up_mm.append(0.0 if isinstance(frame, str) else float(frame.origin_lps[2]))
    z = tibia_top_slice(femur_held, tibia_held, up_mm)
    frame = None if z is None else plane_frame(own.series, z)
    if z is None or frame is None or isinstance(frame, str):
        return semimembranosus_code(True, knee, True, True, False, False, False)
    reads("background", ("split",), "semimembranosus")
    record, arrays, field = read_part_slice(
        own.series,
        z,
        volume[z],
        frame,
        own.record["background_split"],
        knee,
        "semimembranosus",
    )
    labels, plane = arrays["b1_labels"], arrays["acquired_plane"]
    uid = own.series.row.series_uid
    carried = carry_onto(
        leg, own.series, z, frame, labels.shape, float(thicknesses[z] or 0.0)
    )
    reads("carried", ("femur", "tibia", "back_mm", "toward_left_mm"), "semimembranosus")
    reads("field", ("peaks", "objects"), "semimembranosus")
    toward_left = carried.toward_left_mm
    condyle = tendon = None
    if toward_left is not None:
        # the inner side is toward the other knee: the patient's left for a right knee
        inner_mm = toward_left if knee == "R" else -toward_left
        condyle = inner_condyle(
            field.peaks, labels, carried.femur | carried.tibia, inner_mm
        )
        if condyle is not None:
            tendon = semimembranosus_on_slice(
                arrays["b1_dark"],
                # the places neither the air, the skin nor the black margin hold
                (field.objects == 0) & ~margin_of(uid, z, plane),
                labels == condyle.territory,
                condyle,
                carried.back_mm,
                inner_mm,
                np.asarray(frame.spacing_rc),
                measures_of(uid, z, plane, frame),
            )
    # On its slice only the tendon is named; the slice's other parts belong to the middle slice.
    objects = np.zeros(labels.shape, dtype=np.int8)
    if tendon is not None:
        objects[tendon] = OBJECT_CODES["semimembranosus"]
    arrays["a1_objects"] = objects
    record["assignments"]["codes"]["semimembranosus"] = semimembranosus_code(
        True, knee, True, True, True, condyle is not None, bool(objects.any())
    )
    # The bursa reads this same slice and its already carried leg; no lens is read again.
    bright = (
        int(own.series.row.fat_suppression) == 1
        and int(own.series.row.fluid_sensitive) == 1
    )
    posterior = np.zeros(labels.shape, dtype=bool)
    bursal = np.zeros(labels.shape, dtype=bool)
    if (
        bright
        and tendon is not None
        and tendon.any()
        and condyle is not None
        and toward_left is not None
    ):
        posterior = gastrocnemius_head(
            field.peaks,
            labels,
            carried.femur | carried.tibia,
            condyle,
            carried.back_mm,
            inner_mm,
        )
        shared = measures_of(uid, z, plane, frame)
        marrow = shared.light(carried.femur | carried.tibia)
        white = (
            (plane > FLUID_BRIGHTER * marrow)
            if marrow > 0
            else np.zeros(labels.shape, dtype=bool)
        )
        arrays["a2_fluid_signal"] = white
        handed("bursal_fluid", ("white",))
        reads("carried", ("back_mm", "toward_left_mm"), "bursa")
        bursal = bursa_on_slice(
            white,
            tendon,
            posterior,
            carried.back_mm,
            inner_mm,
            np.asarray(frame.spacing_rc),
            shared,
        )
    arrays["a2_gastrocnemius_semimembranosus_bursa"] = bursal
    handed("bursa", ("region",))
    record["assignments"]["codes"]["gastrocnemius_semimembranosus_bursa"] = bursa_code(
        bright,
        tendon is not None and bool(tendon.any()),
        bool(posterior.any()),
        bool(bursal.any()),
    )
    record["main_slice"] = {"object": "semimembranosus"}
    return record, arrays, frame


def find_fibula(
    series: Series,
    record: dict,
    arrays: dict[str, np.ndarray],
    stack: SquintStack,
) -> tuple[dict, dict[str, np.ndarray], np.ndarray | None] | str:
    """The fibula named on its main slice, from the middle slice's tibia, with its places in the
    scanner's millimetres where front to back lies in that slice's plane, so its front edge can be
    read (what the LCL's slice is found from, one leg, one set of objects; None where it does not);
    or why it was not named.

    The series' kept squint points to where the fibula must be (`fibula_block`: below the tibia's
    top, on the knee's outer side of its middle). The lens's territories (`interior_regions`, not
    its border readings, which the fibula does not read) are then read again on that block of
    each slice that holds it, which the method forbids and the ledger counts
    (`fibula.lens_readings`); the fibula there is the region that looks like the tibia, well below
    its top and behind its middle, apart from the tibia (`fibula_on_slice`); and it is named on
    the slice where that region is largest.
    """
    assigned = record["assignments"]
    knee = assigned["knee"]
    reads("series", ("row",), "fibula")
    fat_suppressed = int(series.row.fat_suppression) == 1  # the tag is stored as text
    reads("naming", ("tibia", "objects"), "fibula")
    tibia = arrays["a1_objects"] == OBJECT_CODES["tibia"]
    tibia_named = assigned["tibia"] is not None and bool(tibia.any())
    code = fibula_code(knee, tibia_named, fat_suppressed, True)
    if code != "identified":
        return code
    volume = series.volume
    middle = plane_frame(series, record["slice_index"])
    if volume is None or isinstance(middle, str):
        return "geometry_unreadable"
    reads("naming", ("peaks",), "fibula")
    top_mm = float(middle.to_patient(np.argwhere(tibia).astype(float))[:, 2].max())
    peak = next(p for p in assigned["peaks"] if p["territory"] == assigned["tibia"])
    middle_lps = middle.to_patient(np.asarray([peak["peak_rc"]], dtype=float))[0]
    reads("squint_stack", ("code",), "fibula")
    if stack.code != "present":
        return f"squint_{stack.code}"
    reads("squint_stack", ("centres_lps", "bounds_rc"), "fibula")
    reads("background", ("split",), "fibula")
    reads("series", ("volume",), "fibula")
    split = record["background_split"]
    finite = finite_of(series)
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
        # the territories only: the fibula reads no border reading
        reading = interior_regions(
            volume[z][r0:r1, c0:c1],
            frame.spacing_rc,
            split,
            PROMINENCE_MM,
            available=finite[z][r0:r1, c0:c1],
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
    main_record, main_arrays, main_field = read_part_slice(
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
    codes = main_assigned["codes"]
    codes["tibia"] = "carried_from_the_middle_slice"
    codes["fibula"] = "identified"
    main_assigned.update(tibia=tibia_region, fibula=fibula_region)
    main_record["main_slice"] = {
        "object": "fibula",
        "areas_mm2": [round(area, 1) for area in areas],
    }
    handed("fibula", ("main_slice", "region"))
    # Where front to back lies in the main slice's plane (its field's `in_plane`), the fibula's
    # front edge can be read, and its places in millimetres are what the LCL's slice is found from.
    reads("field", ("in_plane",), "fibula")
    places = (
        frame.to_patient(np.argwhere(objects == OBJECT_CODES["fibula"]).astype(float))
        if main_field.in_plane[1]
        else None
    )
    return main_record, main_arrays, places


def acl_slice(own: Measured) -> tuple[dict, dict[str, np.ndarray], PlaneFrame] | str:
    """The ACL's slice of one series, read (the ACL's paragraph in `knee.objects.assignments`): the
    middle slice's neighbour on the knee's outer side, chosen by place from the header and not read
    off the squint, with the femur and the tibia carried there from the middle slice, and the ACL
    named where fat is suppressed; or why it was not read."""
    series, record = own.series, own.record
    knee = record["assignments"]["knee"]
    reads("naming", ("in_plane",), "acl")
    front_in_plane = own.assignment.in_plane[1]
    reads("partner", ("objects",), "acl")
    before = own.arrays["a1_objects"]
    femur_before = before == OBJECT_CODES["femur"]
    tibia_before = before == OBJECT_CODES["tibia"]
    bones = bool(femur_before.any() and tibia_before.any())
    code = acl_code(front_in_plane, knee, bones, True, True)
    if code != "identified":
        return code
    reads("series", ("volume",), "acl")
    volume = series.volume
    if volume is None or len(volume) < 2:
        return "no_slice_beside_the_middle"
    middle = record["slice_index"]
    step = 1 if middle + 1 < len(volume) else -1
    neighbour = plane_frame(series, middle + step)
    if isinstance(neighbour, str):
        return neighbour
    toward_left = step * float(neighbour.origin_lps[0] - own.frame.origin_lps[0])
    z = middle + outer_step(knee, toward_left)
    if not 0 <= z < len(volume):
        return "no_slice_on_the_outer_side"
    frame = plane_frame(series, z)
    if isinstance(frame, str):
        return frame
    reads("background", ("split",), "acl")
    plane = volume[z]
    acl_record, arrays, field = read_part_slice(
        series, z, plane, frame, record["background_split"], knee, "acl"
    )
    labels = arrays["b1_labels"]
    measures = measures_of(series.row.series_uid, z, plane, frame)
    femur = carried_bone(labels, femur_before, measures)
    tibia = carried_bone(labels, tibia_before, measures)
    carried = bool(femur.any() and tibia.any())
    fat_suppressed = int(series.row.fat_suppression) == 1  # the tag is stored as text
    acl = np.zeros(labels.shape, dtype=bool)
    if carried and fat_suppressed:
        reads("field", ("peaks",), "acl")
        acl = acl_on_slice(
            labels,
            field.peaks,
            femur,
            tibia,
            frame.basis_lps,
            margin_of(series.row.series_uid, z, plane),
        )
    # On its slice only the ACL is named, between the bones it was found between; the middle
    # slice's other objects are not named here: their rules belong to the middle slice.
    objects = np.zeros(labels.shape, dtype=np.int8)
    objects[femur] = OBJECT_CODES["femur"]
    objects[tibia] = OBJECT_CODES["tibia"]
    objects[acl] = OBJECT_CODES["acl"]
    arrays["a1_objects"] = objects
    assigned = acl_record["assignments"]
    codes = assigned["codes"]
    codes["femur"] = codes["tibia"] = "carried_from_the_middle_slice"
    codes["acl"] = acl_code(True, knee, carried, fat_suppressed, bool(acl.any()))
    assigned.update(acl=int(labels[acl].max()) if acl.any() else None)
    acl_record["main_slice"] = {"object": "ACL"}
    return acl_record, arrays, frame


def lcl_slice(
    own: Measured, fibula_lps: np.ndarray | None
) -> tuple[dict, dict[str, np.ndarray], PlaneFrame] | str:
    """The LCL's slice of one series, read (the LCL's paragraph in `knee.objects.assignments`): the
    slice through the place on the fibula's head where the LCL attaches, the fibula being the one
    its own rule named on its main slice, carried by place; the femur carried there from the middle
    slice; and the LCL named where fat is not suppressed; or why it was not read."""
    series, record = own.series, own.record
    assigned = record["assignments"]
    reads("naming", ("in_plane",), "lcl")
    sides_in_plane = own.assignment.in_plane[0]
    reads("partner", ("objects",), "lcl")
    femur_before = own.arrays["a1_objects"] == OBJECT_CODES["femur"]
    bones = bool(femur_before.any()) and assigned["tibia"] is not None
    named = fibula_lps is not None
    code = lcl_code(sides_in_plane, named, bones, True, False, True, True)
    if code != "identified" or fibula_lps is None:
        return code
    reads("fibula", ("main_slice", "region"), "lcl")
    reads("series", ("geometry", "slice_thickness_mm", "volume"), "lcl")
    geometry, volume, thicknesses = (
        series.geometry,
        series.volume,
        series.slice_thickness_mm,
    )
    if geometry is None or volume is None:
        return "geometry_unreadable"
    known = [float(t) for t in thicknesses if t is not None]
    if len(known) != len(thicknesses):
        return "no_slice_thickness"
    origins = np.asarray([np.asarray(p, dtype=float) for p in geometry.position])
    z = slice_through(lcl_attachment(fibula_lps), origins, own.frame.normal(), known)
    if z is None:
        return lcl_code(True, True, True, False, False, True, True)
    frame = plane_frame(series, z)
    if isinstance(frame, str):
        return frame
    reads("background", ("split",), "lcl")
    lcl_record, arrays, _ = read_part_slice(
        series,
        z,
        volume[z],
        frame,
        record["background_split"],
        assigned["knee"],
        "lcl",
    )
    labels = arrays["b1_labels"]
    measures = measures_of(series.row.series_uid, z, arrays["acquired_plane"], frame)
    femur = carried_bone(labels, femur_before, measures)
    fibula_places = places_on_slice(fibula_lps, frame, labels.shape, known[z])
    fibula = region_holding(labels, fibula_places)
    fat_suppressed = int(series.row.fat_suppression) == 1  # the tag is stored as text
    reads("naming", ("tibia", "peaks"), "lcl")
    peak = next(p for p in assigned["peaks"] if p["territory"] == assigned["tibia"])
    tibia_middle = own.frame.to_patient(np.asarray([peak["peak_rc"]], dtype=float))[0]
    lcl = np.zeros(labels.shape, dtype=bool)
    if femur.any() and fibula.any() and not fat_suppressed:
        rows, cols = np.indices(labels.shape)
        across = (
            frame.origin_lps[0]
            + frame.basis_lps[0, 0] * rows
            + frame.basis_lps[0, 1] * cols
        )
        lcl = lcl_on_slice(
            labels,
            femur,
            fibula,
            across,
            float(tibia_middle[0]),
            float(fibula_lps[:, 0].mean()),
            np.asarray(frame.spacing_rc),
            measures,
        )
    # On its slice only the LCL is named, with the fibula's own places carried from its main slice;
    # the regions of the femur and of the fibula are its targets, never its names, since on a T1
    # the fibula's head may share a region with the tibia.
    objects = np.zeros(labels.shape, dtype=np.int8)
    objects[fibula_places] = OBJECT_CODES["fibula"]
    objects[lcl] = OBJECT_CODES["lcl"]
    arrays["a1_objects"] = objects
    lcl_assigned = lcl_record["assignments"]
    codes = lcl_assigned["codes"]
    codes["fibula"] = "carried_from_its_main_slice"
    codes["lcl"] = lcl_code(
        True,
        True,
        bool(femur.any()),
        True,
        fat_suppressed,
        bool(fibula.any()),
        bool(lcl.any()),
    )
    lcl_assigned.update(lcl=int(labels[lcl].max()) if lcl.any() else None)
    lcl_record["main_slice"] = {"object": "LCL"}
    return lcl_record, arrays, frame


def lay_parts(
    own: Measured,
    read: tuple[dict, dict[str, np.ndarray], PlaneFrame],
    partner: tuple[dict, dict[str, np.ndarray], PlaneFrame],
    parts: tuple[str, ...],
    yields: tuple[int, ...] = (),
    onto_borders: bool = False,
) -> dict[str, str | None]:
    """Lay the parts the other sequence's slice of the same place names onto this series' slice,
    by the pair's one match (`matched`), onto this slice's own regions that nothing else holds but
    the parts in `yields`, and with `onto_borders` onto the places between its regions too, where
    its lens leaves a thin dark band out of every region: for each part, "laid_from_its_partner",
    why it was not laid, or None when nothing was laid."""
    record, arrays, frame = read
    partner_record, partner_arrays, partner_frame = partner
    source = matched(
        own.series,
        record,
        frame,
        arrays["acquired_plane"].shape,
        partner_record,
        partner_frame,
        partner_arrays["acquired_plane"],
    )
    if isinstance(source, str):
        return dict.fromkeys(parts, source)
    laid = laid_by(partner_arrays["a1_objects"], source)
    # a copy: a slice's objects may still be the names it made alone
    objects = arrays["a1_objects"].copy()
    open_to_them = np.isin(objects, (0, *yields))
    if not onto_borders:
        open_to_them &= arrays["b1_labels"] > 0
    codes: dict[str, str | None] = {}
    for part in parts:
        code = OBJECT_CODES[part]
        placed = (laid == code) & open_to_them
        objects[placed] = code
        codes[part] = "laid_from_its_partner" if placed.any() else None
    arrays["a1_objects"] = objects
    return codes


def find_part(
    measured: list[Measured],
    part: str,
    read_slice: Callable[
        [Measured], tuple[dict, dict[str, np.ndarray], PlaneFrame] | str
    ],
    laid_when: str,
) -> tuple[list[tuple[dict, dict[str, np.ndarray]]], dict[str, str]]:
    """A part named on its own slice in each series (`read_slice`: `acl_slice`, `lcl_slice`), and
    laid from the sequence that names it onto the other sequence's slice of the same place where
    that one abstains with `laid_when` (`lay_part`): the slices that name it, each record with its
    arrays, and every other series' silence, keyed `<series uid>:<part>`."""
    read: dict[int, tuple[dict, dict[str, np.ndarray], PlaneFrame]] = {}
    silences: dict[str, str] = {}
    for index, own in enumerate(measured):
        result = read_slice(own)
        if isinstance(result, str):
            silences[f"{own.record['series_uid']}:{part}"] = result
        else:
            read[index] = result
    found = []
    for index, (record, arrays, _) in read.items():
        own = measured[index]
        codes = record["assignments"]["codes"]
        if codes[part] == laid_when:
            partner = partner_of(measured, index)
            at = next((i for i, m in enumerate(measured) if m is partner), None)
            if at in read and read[at][0]["assignments"]["codes"][part] == "identified":
                laid = lay_parts(own, read[index], read[at], (part,))[part]
                codes[part] = laid or codes[part]
        if codes[part] in NAMED:
            handed(part, ("main_slice", "region"))
            found.append((record, arrays))
        else:
            silences[f"{own.record['series_uid']}:{part}"] = codes[part]
    return found, silences


def save(run_dir: Path, study_uid: str, record: dict, arrays: dict) -> dict:
    """Save one record's arrays in the run and note them, with their digests, on the record. A main
    slice's arrays are named for its part as well, since one series may hold several."""
    part = record.get("main_slice", {}).get("object")
    name = record["series_uid"] if part is None else f"{record['series_uid']}-{part}"
    artifact = Path(study_uid) / f"{name}.npz"
    if "a2_synovium" in arrays:
        reads("joint_boundaries", ("recess", "lining", "capsule"), "save")
    if "a2_gastrocnemius_semimembranosus_bursa" in arrays:
        reads("bursa", ("region",), "save")
    if "a2_fluid_signal" in arrays:
        reads("bursal_fluid", ("white",), "save")
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
    work, the run's totals, every product produced and read by no stage, and, kind by kind, how
    many values were made once (`knee.telemetry.once`) and how often a made one was handed on."""
    by_name: dict[str, dict[str, int]] = {}
    computed: dict[str, dict[str, int]] = {}
    for event in events:
        entry = by_name.setdefault(event.name, {"times": 0})
        entry["times"] += 1
        for key, value in event.counts.items():
            entry[key] = entry.get(key, 0) + value
        for ending in ("made", "handed_on"):
            if event.name.endswith(f".{ending}"):
                kind = event.name[: -len(ending) - 1]
                tally = computed.setdefault(kind, {"made": 0, "handed_on": 0})
                tally[ending] += 1
    return {
        "events": by_name,
        "totals": totals,
        "read_by_no_stage": list(unread_products(event.name for event in events)),
        "computed_once": computed,
    }


def named_parts(records: list[dict], main_records: list[dict]) -> dict[str, int]:
    """How many of the study's series named each object, on its middle slice or on the object's own
    main slice."""
    named: dict[str, int] = {}
    for record in records + main_records:
        for name, code in record["assignments"]["codes"].items():
            if code in NAMED or code == "from_the_header":
                named[name] = named.get(name, 0) + 1
    return named


def measure_study(
    corpus: Corpus, study_uid: str, run_dir: Path, main_run: Path, drawn: bool
) -> dict:
    """Measure every series of one study with the ledger on and save its arrays; return what the
    receipts take (its records, silences and telemetry) and what it named. Writes no receipt, so
    studies can be measured side by side. `drawn` says whether its pictures will be drawn, since
    only then do the renderers read what they read. Within the study a value two stages need is
    made once and handed on (`knee.telemetry.once`), and released when the study is done."""
    (run_dir / study_uid).mkdir(parents=True, exist_ok=True)
    (main_run / study_uid).mkdir(parents=True, exist_ok=True)
    with recording() as led, computing():
        study = read_study(corpus, study_uid)
        ledger.record(
            "study.produced",
            series=len(study.series),
            slices=sum(len(series.slices) for series in study.series),
        )
        records, unread = [], {}
        main_records, main_unread = [], {}
        measured: list[Measured] = []
        for series in study.series:
            handed("series", field_names(series))
            reading = measure(series)
            if isinstance(reading, str):
                unread[series.row.series_uid] = reading
            else:
                measured.append(reading)
        # Each middle slice is read with its partner's, the other sequence's slice of the same
        # place, on the names each made alone (`Measured.assignment`, which this never changes);
        # then saved.
        partners = [partner_of(measured, index) for index in range(len(measured))]
        for own, partner in zip(measured, partners, strict=True):
            own.record["assignments"]["partner"] = (
                "none_of_the_other_sequence"
                if partner is None
                else read_with_partner(own, partner)
            )
        # The extensor tendons, on the sagittal slice without fat suppression, from the bands its
        # PCL was read from and the patella its partner laid on; then laid onto that partner. Then
        # the rest of the field on each slice without fat suppression: the fat under the skin where
        # its partner laid the skin on, and muscle, outside every part named and the white its
        # partner sees as fluid where that partner is fat-suppressed and fluid-sensitive; each laid
        # onto that partner.
        for own, partner in zip(measured, partners, strict=True):
            name_the_extensor_tendons(own, partner)
        for own, partner in zip(measured, partners, strict=True):
            name_the_rest_of_the_field(own, partner)
        # Fat-suppressed sources locate the recess and its lining; transfer after each
        # target has its own abstention, so a later target cannot overwrite a transferred mask.
        for own, partner in sorted(
            zip(measured, partners, strict=True),
            key=lambda pair: int(pair[0].series.row.fat_suppression),
        ):
            name_joint_boundaries(own, partner)
        # The back of the knee, on the series the leg runs through: the study's leg, its bones in
        # the scanner's millimetres, made once where the header names the knee there, and carried
        # onto the slices its parts are named on; the medial head on the middle slice, from the
        # lens already read there, before the records are saved, so it is saved and drawn.
        leg = None
        reads("naming", ("in_plane",), "leg")
        if any(
            not own.assignment.in_plane[2]
            and own.record["assignments"]["knee"] in ("R", "L")
            for own in measured
        ):
            leg = leg_of(measured)
        for own in measured:
            own.record["assignments"]["codes"]["medial_gastrocnemius"] = (
                name_the_back_of_the_knee(own, leg)
            )
        # The fibula found on its main slice is handed to the LCL, which ends on it: the first
        # series, in the study's order, to name it where its front edge can be read.
        fibula_lps = None
        for own in measured:
            fibula = find_fibula(own.series, own.record, own.arrays, own.stack)
            records.append(save(run_dir, study_uid, own.record, own.arrays))
            if isinstance(fibula, str):
                main_unread[f"{own.record['series_uid']}:fibula"] = fibula
            else:
                fibula_record, fibula_arrays, placed = fibula
                main_records.append(
                    save(main_run, study_uid, fibula_record, fibula_arrays)
                )
                if fibula_lps is None:
                    fibula_lps = placed
        for part, read_slice, laid_when in (
            ("acl", acl_slice, "abstain_not_walled_off_without_fat_suppression"),
            (
                "lcl",
                lambda own: lcl_slice(own, fibula_lps),
                "abstain_not_parted_from_the_fat_with_fat_suppression",
            ),
            (
                "semimembranosus",
                lambda own: semimembranosus_slice(own, leg),
                "abstain_no_tendon_at_the_back_inner_corner",
            ),
        ):
            found, silences = find_part(measured, part, read_slice, laid_when)
            for part_record, part_arrays in found:
                main_records.append(save(main_run, study_uid, part_record, part_arrays))
            main_unread.update(silences)
        # The renderers read the saved run, when they draw it: their reads are its last.
        if drawn and records:
            reads("interiors", DRAWN_INTERIORS, "draw")
            reads("naming", DRAWN_NAMES, "draw")
            # what a slice read with its partner keeps, in place of its own objects and codes
            reads("partner", ("objects", "codes"), "draw")
            # the back of the knee's part, which a middle slice the leg runs through names
            if any(
                r["assignments"]["codes"].get("medial_gastrocnemius") == "identified"
                for r in records
            ):
                reads("gastrocnemius", ("region",), "draw")
            # the extensor tendons, which the sagittal middle slices name
            if any(
                r["assignments"]["codes"].get(name) in NAMED
                for r in records
                for name in ("patellar_tendon", "quadriceps_tendon")
            ):
                reads("tendons", ("region",), "draw")
            # the rest of the field, the fat under the skin and muscle, which a slice without fat
            # suppression names
            if any(
                r["assignments"]["codes"].get(name) in NAMED
                for r in records
                for name in ("subcutaneous_fat", "muscle")
            ):
                reads("rest_of_the_field", ("region",), "draw")
        if drawn:
            for part in sorted(
                {r["main_slice"]["object"].lower() for r in main_records}
            ):
                reads(part, ("main_slice", "region"), "draw")
        telemetry = ledger_reading(led.events(), led.totals())
    series_uids = [series.row.series_uid for series in study.series]
    return {
        "study_uid": study_uid,
        "series_uids": series_uids,
        "records": records,
        "unread": unread,
        "main_records": main_records,
        "main_unread": main_unread,
        # the main receipt's own keys, so a part's old silence goes when the study is read again;
        # a bare series uid clears what was kept before the silences were kept per part
        "main_keys": series_uids
        + [f"{uid}:{part}" for uid in series_uids for part in MAIN_PARTS],
        "telemetry": telemetry,
        "named": named_parts(records, main_records),
    }


@cache
def opened(root: Path) -> Corpus:
    """The corpus at `root`, opened once per process, its decoders checked and its tables read
    once, for every study the process measures."""
    return open_corpus(root)


def measure_study_at(
    root: Path, study_uid: str, run_dir: Path, main_run: Path, drawn: bool
) -> dict:
    """`measure_study` in a worker process, from the corpus it opened once (`opened`)."""
    return measure_study(opened(root), study_uid, run_dir, main_run, drawn)


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
        main_run,
        uid,
        result["main_keys"],
        result["main_records"],
        result["main_unread"],
        None,
    )


def draw_study(
    result: dict,
    run_dir: Path,
    out: Path,
    assignments_out: Path,
    main_run: Path,
    main_out: Path,
) -> list[Path]:
    """Draw one study from the saved run, once it is in the receipts; return its pictures. The
    renderers are imported here, so a run that draws nothing never loads the drawing layer."""
    import object_assignments
    import object_interiors

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


def on_disk(corpus: Corpus, uids: Iterable[str]) -> list[str]:
    """The given studies whose series are all on disk, in the order given."""
    found = []
    for uid in uids:
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
    shared = ", ".join(
        f"{kind} {tally['made']} made, {tally['handed_on']} handed on"
        for kind, tally in result["telemetry"]["computed_once"].items()
    )
    print(uid, flush=True)
    print(f"  named, by series: {parts or 'nothing'}", flush=True)
    print(f"  produced and read by no stage: {unread or 'none'}", flush=True)
    print(f"  computed once and handed on: {shared or 'nothing'}", flush=True)
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
    which.add_argument(
        "--split",
        choices=sorted(SPLIT_FOLDER),
        help="every study of one split whose series are all on disk; a kernel is given the test split",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=KAGGLE_ROOT if KAGGLE_ROOT.is_dir() else ROOT / LOCAL_ROOT,
        help="the competition's files: where a kernel mounts them when that exists, else data/raw",
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
    corpus = opened(args.root)
    if args.labeled:
        uids = on_disk(corpus, labeled_uids(corpus.tables))
    elif args.split:
        uids = on_disk(corpus, split_uids(corpus.tables, args.split))
    else:
        uids = args.study_uid
    workers = max(1, min(args.workers, len(uids)))
    if workers == 1:
        for uid in uids:
            report(measure_study(corpus, uid, args.run, args.main_run, args.draw), args)
        return
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = pool.map(
            measure_study_at,
            repeat(args.root),
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
