"""The one run: every study it is given, read whole; each part of the knee named on it, or the
reason it is not; every reading kept.

For each series of a study: its background split, read once over the whole series, the level the
lens reads low signal under (`knee.collapse.noise.background_split`); the squint over every slice,
made once and kept with the series; the middle slice (the standard first slice,
`docs/RESOLVING_THE_PARTS.md` §8), its plane frame, and its lens: the territories (`interior_regions`),
and for a run that draws, the border readings across them too (`read_interiors`, with the frame's
spacing and the retained basis as its metric), which only the pictures read. Then
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
there beside the tibia it was found against and nothing else. Its slice is not searched with the lens:
its corridor (the tibia's outer back, below its top) is read through the whole depth cheaply
(`fibula_profile`: the kept squint's tiles, whose extrema exclude exactly what they can, and a finer
block reading of the corridor's window where they cannot; a slice the tibia cannot be told on is
unknown, never empty), and the lens and the established rule (`fibula_on_slice`) run only on the planes
the profile points to, the maximum of each run of support with every tie kept (`fibula.lens_readings`
counts them), and the transfer's twin slice. The fibula's support in the scanner's millimetres with its
ends, the head's continuation outward, what is unknown and every plane it was identified on are kept
with it (`a3_fibula_*`), and what each view says of it by provenance, native, laid and projected
(`knee.collapse.observations`). One value (`FibulaFound`) is handed to the LCL and to the biceps femoris
tendon, and the fibula is laid onto the other sequence's slice of the same place (`fibula_twin`). The ACL (`acl_slice`) is
named on the middle slice's neighbour on the knee's outer side, between the femur and the tibia
carried there from the middle slice. Its slice is chosen by place, from the header's word for which
knee, not read off the squint; the lens is read once more, on that slice of each sagittal series
(`acl.lens_readings`); the ACL is named where fat is suppressed and laid onto the other sequence's
slice of the same place (`find_part`, `lay_part`). The LCL (`lcl_slice`) is named on the coronal
slice through the place where it attaches on the fibula, the fibula being the one found on its
main slice, its places handed on from there (`find_fibula`); the lens is read once more, on that slice
of each coronal series (`lcl.lens_readings`); the LCL is named where fat is not suppressed and laid
onto the other sequence's slice of the same place. The biceps femoris tendon
(`biceps_femoris_slice`) is named on a fat-bright sagittal series' slice just beyond the fibular
head's lateral face, from the fibula already found: its native main slice is recovered from the
fibula's places, its marrow light read there once in both acquisitions (the twin's by the scanner's
millimetres, never by equal indices), and the walk outward to the head's edge (`lateral_to_the_head`)
asks for a slice's head only when it reaches it, each kept in the record. The lens is read once
more on the slice chosen (`biceps_femoris_tendon.lens_readings`) and the rule reads the light of
the two acquisitions, with the places the twin or the native margin never saw left unseen (NaN);
the mask is laid onto the twin's slice of the same place (`find_part`, `lay_parts`) with its own
decision. A series' silence on a main-slice part is kept as `<series uid>:<part>`.

THE BACK OF THE KNEE is named on the series the leg runs through, an axial one. Where the header
names the knee there, the femur and the tibia named on the study's middle slices where the leg
runs in the plane are put in the scanner's millimetres once, with the notch's plane from the
middle sagittal slice (`leg_of`, the `leg` product), and carried by place onto each slice a part
is named on (`carry_onto`, the `carried` product). Both gastrocnemius heads are named on the
middle slice, whose lens the run has already read, each behind its corresponding condyle on
its side of the notch (`name_the_back_of_the_knee`), sharing the carried leg, before the records
are saved. The semimembranosus tendon is named
on its own slice, the top of the tibia just below the joint line, found by carrying the leg onto
each slice of the series (`semimembranosus_slice`); the lens is read once more there
(`semimembranosus.lens_readings`), and the tendon is laid onto the other sequence's slice of the
same place where that one finds none. That group (the tendon, the semitendinosus and the
gracilis) is resolved once, after the study's leg and the back of the knee and before the middle
slices are saved (`find_part`), and not again among the later main parts: its records are saved
and its silences kept as ever. The SARTORIUS is named on each middle axial that is
fat-suppressed and fluid-sensitive (`name_sartorius`) from the gracilis's places, the first
native gracilis of that group put in the scanner's millimetres once (`gracilis_source`) and
projected onto the axial as a location target; no lens is read again, and the contrast over the
slice is read once, there.

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
prominence 3 mm, and border offsets from -3 to 3 mm in 0.5 mm steps. The border readings, read only
to draw, sample their profiles with the JIT twin of the profile sampler, as that run used; its
records are the reference's, checked run against run on all 58 labelled studies, 2026-10-14: 336
series, every saved array the same.

Studies are measured in parallel, one worker process each, and each saves its own arrays; the main
process alone writes the receipts, in the order the studies were asked for. Pictures are drawn only
with `--draw`, from the saved run, after its study is in the receipt; the drawing layer is imported
only then, so a run that draws nothing never loads it. What only the pictures read is read only
then too: a run that draws nothing, the one a kernel runs, reads no border.

Run from anywhere: `.venv/bin/python scripts/run_interiors.py --study-uid <uid> [<uid> ...]`;
`--labeled` for every labelled study whose series are all on disk; `--split test` (or `train`) for
every study of that split whose series are all on disk, the test split being the studies a Kaggle
kernel is given; `--root` for where the competition's files are (where a kernel mounts them,
`knee.study.corpus.KAGGLE_ROOT`, when that exists, else `data/raw`); `--draw` for the pictures.
"""

import argparse
import json
import os
from collections.abc import Callable, Collection, Iterable, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, fields, replace
from functools import cache
from itertools import repeat
from pathlib import Path
from typing import Any

import numpy as np
from scipy import ndimage as ndi

from knee.collapse.bones import (
    AMBIGUOUS,
    IDENTIFIED,
    OUTCOMES,
    TIE,
    Naming,
    marrow_body,
    name_territory,
    section_extent,
    tiles_around,
    tiles_touched,
)
from knee.collapse.joint import (
    BRIGHT,
    DARK,
    FLUID,
    LIGAMENT,
    POINTS_AT,
    block_support,
    compartment,
    horn_pieces,
    joint_reach,
    levels,
)
from knee.collapse.noise import background_split, finite_values
from knee.collapse.observations import (
    PROVENANCES,
    Observation,
    Unresolved,
    describe_objects,
    tally,
    unresolved_rows,
)
from knee.collapse.observations import rows as observation_rows
from knee.collapse.patella import femur_landmarks, in_front_of_the_femur
from knee.collapse.physical import PlaneFrame
from knee.collapse.posterior import (
    FOLLOWED,
    START_NAMES,
    STOP_NAMES,
    Trace,
    cross_extent_mm,
    leg_axis,
    trace_tube,
)
from knee.collapse.profile import (
    CLIPPED_BY_THE_SCAN,
    FineReading,
    block_centres_rc,
    block_holds,
    block_medians,
    block_pixels,
    confirmations,
    could_hold_level_in_reach,
    depth_offsets_mm,
    footprint_reach,
    pack_fine_readings,
    positive_runs,
    run_maxima,
    run_neighbours,
    run_slabs_mm,
    slab_gaps_mm,
    support_intervals_mm,
)
from knee.collapse.recess import (
    anterior_pocket,
    gutter_landmarks,
    patellofemoral_interval,
    side_gutters,
)
from knee.collapse.squint_stack import SquintStack, read_squint_stack
from knee.compute.contracts import handed_on
from knee.objects.assignments import (
    BONE_MM,
    FIBULA_BELOW_MM,
    FIBULA_POINTER_STATUS,
    FLUID_BRIGHTER,
    FOUR_NEIGHBOURS,
    HEAD_SLICE_STATUS,
    LIGAMENT_SMOOTH_MM,
    LIKE_THE_FEMUR,
    LIKE_THE_TIBIA,
    MENISCUS_THICKNESS_MM,
    NAMED,
    OBJECT_CODES,
    PATELLA_ABOVE_MM,
    RETINACULA,
    SHELL_MM,
    SLICE_PARTS,
    Field,
    Measures,
    PlaneAssignment,
    acl_code,
    acl_on_slice,
    anterior_synovial_recess,
    assign_plane,
    band_joining,
    between_along_the_leg,
    bursa_code,
    bursa_on_slice,
    capsule_at_side_recesses,
    capsule_code,
    carried_bone,
    cartilage_code,
    cartilage_on,
    dark_bands,
    dark_tendon_bodies,
    enclosed_darkness,
    end_pieces,
    extensor_tendons,
    fat_pad_code,
    fat_under_the_skin,
    fibula_code,
    fibula_corridor,
    fibula_like_head,
    fibula_on_slice,
    fibula_pointer,
    fluid_code,
    fluid_in_the_recesses,
    gastrocnemius_code,
    gastrocnemius_head,
    gracilis_on_slice,
    head_area_mm2,
    iliotibial_band_on_slice,
    inner_condyle,
    laid_by,
    lateral_to_the_head,
    lcl_attachment,
    lcl_code,
    lcl_on_slice,
    ligament_on_the_inner_side,
    main_slice,
    margin,
    mcl_code,
    meniscus_code,
    meniscus_side,
    muscle_bodies,
    muscle_code,
    native_dark_bodies,
    outer_step,
    patella_code,
    patella_peak,
    patella_piece,
    pcl_code,
    places_from,
    places_on_slice,
    popliteal_lumens,
    popliteus_in_notch,
    projected_places,
    proximal_biceps_on_slice,
    read_field,
    region_holding,
    relative_signal,
    rest_of_the_patellas_territory,
    retinacular_walls,
    sartorius_on_slice,
    semimembranosus_code,
    semimembranosus_on_slice,
    semitendinosus_on_slice,
    side_code,
    slice_through,
    subcutaneous_code,
    suprapatellar_pads,
    synovium_code,
    tendon_code,
    thick_parts,
    tibia_top_slice,
    twin_marrow_light,
    white_as_fluid,
    with_partner,
)
from knee.objects.interiors import (
    EDGE_KINDS,
    TRACE_CODES,
    InteriorReading,
    InteriorRegions,
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
MAIN_PARTS = (
    "fibula",
    "acl",
    "lcl",
    "semimembranosus",
    "semitendinosus",
    "gracilis",
    "patellar_retinacula",
    *RETINACULA,
    "popliteus_tendon",
    "biceps_femoris_tendon",
)
# The biceps femoris tendon's own slice is found on the fat-bright sagittal series, and its mask is
# laid onto the fat-suppressed twin's slice of the same place: the twin's decision until then.
BICEPS = "biceps_femoris_tendon"
FIBULA_UNREADABLE = "abstain_fibula_corridor_unreadable"
FIBULA_LAID_WHEN = "abstain_marrow_suppressed_with_the_fat"
# What a run of support touches at each end, from the neighbouring slice's pointer status.
RUN_END_NAMES = {
    CLIPPED_BY_THE_SCAN: "clipped_by_the_scan",
    FIBULA_POINTER_STATUS["not_read"]: "beyond_the_corridor",
    FIBULA_POINTER_STATUS["none"]: "observed_end",
    FIBULA_POINTER_STATUS["unreadable"]: "unresolved",
    FIBULA_POINTER_STATUS["cut"]: "unresolved",
    FIBULA_POINTER_STATUS["body"]: "continues",
}
# A pointer run the established rule did not confirm on any plane it was read on is a candidate, not
# the bone's extent: a status of its own in the confirmed support, never body, never none.
UNCONFIRMED_CANDIDATE = max(FIBULA_POINTER_STATUS.values()) + 1
RUN_END_NAMES[UNCONFIRMED_CANDIDATE] = "unconfirmed_candidate"
# What the established rule said of one run of the pointer's support, from the planes read for it.
RUN_CONFIRMATION = {
    "confirmed_by_the_native_rule": 1,
    "rejected_by_the_native_rule": 2,
    "not_read_natively": 3,
}
# The lens readings of a plane the profile pointed to that is not the selected one, kept as made.
OTHER_PLANE_READINGS = ("labels", "distance_mm", "dark", "markers", "available")
BICEPS_LAID_WHEN = "abstain_mask_not_laid_from_the_fat_bright_native_view"
# Parts sharing another part's selected slice and its readings.
MAIN_COMPANIONS = {
    "lcl": ("popliteus_tendon",),
    "semimembranosus": ("semitendinosus", "gracilis"),
    "patellar_retinacula": RETINACULA,
}
# The joint's boundaries: each the field it is handed on as, and the part it names.
JOINT_BOUNDARIES = (
    ("recess", "anterior_synovial_recess"),
    ("lining", "synovium"),
    ("capsule", "joint_capsule"),
)


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


def measure(series: Series, drawn: bool) -> Measured | str:
    """One series' readings: its background split and its squint, each read once over the whole
    series, and the interiors and named objects at its middle slice; or why no plane was read.
    Which of its values are finite, and every slice's frame, are read once here and handed to the
    split, the squint and the lens. `drawn` says whether the study's pictures will be drawn, the
    only reader of the middle slice's border readings."""
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
        series, index, series.volume[index], frame, split, knee, borders=drawn
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
    *,
    borders: bool = False,
) -> tuple[np.ndarray, InteriorRegions, dict]:
    """One slice's lens reading, made once per slice and handed to every stage that asks for that
    slice (its naming, and a part named on it, whose slice may be the middle slice or another
    part's): the acquired plane, the interiors, and what the record says of them. `reader` is the
    part whose own slice this is, whose lens readings the ledger counts.

    With `borders` the border readings across the territories are read too (`read_interiors`).
    Only the pictures read them, so only a middle slice of a run that draws asks for them; every
    other reading is the territories alone (`interior_regions`, the same arrays), and a run that
    draws nothing reads no border. The middle slices are read first (`measure`), so a part's slice
    that is a middle slice is handed the middle slice's lens."""

    def read() -> tuple[np.ndarray, InteriorRegions, dict]:
        reads("series", ("volume", "row", "slices"), "interiors")
        reads("background", ("split",), "interiors")
        reading: InteriorRegions
        if borders:
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
        else:
            reading = interior_regions(
                plane,
                frame.spacing_rc,
                split,
                PROMINENCE_MM,
                available=finite_of(series)[index],
            )
        handed("interiors", field_names(reading))
        ledger.record(
            "interiors.work", planes=1, territories=int(reading.labels.max(initial=0))
        )
        if reader is not None:
            ledger.record(f"{reader}.lens_readings", planes=1)
        interiors: dict[str, Any] = {
            "code": reading.code,
            "territories": int(reading.labels.max(initial=0)),
        }
        # what the border readings found, where they were read
        if isinstance(reading, InteriorReading):
            interiors.update(
                edge_counts={
                    kind: int(np.count_nonzero(reading.edge_kinds == value))
                    for kind, value in EDGE_KINDS.items()
                },
                trace_counts={
                    code: int(np.count_nonzero(reading.trace_codes == value))
                    for code, value in TRACE_CODES.items()
                },
                backend=BACKEND,
            )
        # frozen, as the interiors' own fields are: every stage that reads the slice is handed it
        return handed_on(plane.copy()), reading, interiors

    return once("lens", (series.row.series_uid, index), read)


def field_of(
    series: Series,
    index: int,
    plane: np.ndarray,
    frame: PlaneFrame,
    reading: InteriorRegions,
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
    lens: tuple[np.ndarray, InteriorRegions, dict],
    field: Field,
) -> tuple[dict, dict[str, np.ndarray]]:
    """The record and arrays one slice's reading makes before a part is named on it: the lens's
    arrays and what the record says of them, the field's names and peaks, and every part of a
    slice's naming (`SLICE_PARTS`) not named there, until the stage that names one says so. The
    border readings are kept where the lens read them, for the pictures."""
    acquired, reading, interiors = lens
    arrays = {
        "acquired_plane": acquired,
        "b1_dark": reading.dark,
        "b1_available": reading.available,
        "b1_distance_mm": reading.distance_mm,
        "b1_markers": reading.markers,
        "b1_labels": reading.labels,
    }
    if isinstance(reading, InteriorReading):
        arrays.update(
            b1_edge_points_rc=reading.edge_points_rc,
            b1_edge_normals_rc=reading.edge_normals_rc,
            b1_trace_codes=reading.trace_codes,
            b1_trace_points_rc=reading.trace_points_rc,
        )
    arrays["a1_objects"] = field.objects
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
    *,
    borders: bool,
) -> tuple[dict, dict[str, np.ndarray], PlaneAssignment]:
    """A middle slice read and named: its lens (`lens_of`, with its border readings when `borders`,
    for a run that draws) and its field (`field_of`), and the parts named on it alone
    (`assign_plane`, with the slice's shared measures), each made once per slice; the record and
    arrays the renderers read, and the named objects themselves."""
    uid = series.row.series_uid
    lens = lens_of(series, index, plane, frame, split, borders=borders)
    # the middle slices are read before any part's slice, so a run that draws reads their borders
    if borders and not isinstance(lens[1], InteriorReading):
        raise RuntimeError("middle_slice_lens_read_without_its_borders")
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
    once for every slice it is carried onto. The native named patella is retained too."""

    femur_lps: np.ndarray
    tibia_lps: np.ndarray
    notch_origin_lps: np.ndarray | None
    notch_normal: np.ndarray | None
    patella_lps: np.ndarray


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
    faces is its naming's (`PlaneAssignment.in_plane`), read once. The patella comes from the
    first native identification, without resampling its laid twin."""
    reads("partner", ("objects", "codes"), "leg")
    reads("naming", ("in_plane",), "leg")
    femur, tibia = [np.zeros((0, 3))], [np.zeros((0, 3))]
    patella = np.zeros((0, 3))
    notch_origin = notch_normal = None
    for other in measured:
        sides_in_plane, _, leg_in_plane = other.assignment.in_plane
        if not leg_in_plane:
            continue
        objects = other.arrays["a1_objects"]
        for name, found in (("femur", femur), ("tibia", tibia)):
            places = np.argwhere(objects == OBJECT_CODES[name]).astype(float)
            found.append(other.frame.to_patient(places))
        # The native FS definition supplies one patella, rather than resampling its laid twin.
        if (
            not len(patella)
            and other.record["assignments"]["codes"].get("patella") == "identified"
        ):
            places = np.argwhere(objects == OBJECT_CODES["patella"]).astype(float)
            patella = other.frame.to_patient(places)
        if notch_origin is None and not sides_in_plane:
            normal = other.frame.normal()
            notch_origin = other.frame.origin_lps
            notch_normal = normal if normal[0] > 0 else -normal
    leg = Leg(
        np.concatenate(femur),
        np.concatenate(tibia),
        notch_origin,
        notch_normal,
        patella,
    )
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


def name_the_back_of_the_knee(own: Measured, leg: Leg | None) -> dict[str, str]:
    """Both gastrocnemius heads named on this series' middle slice (their paragraphs in
    `knee.objects.assignments`), from the lens the run has already read there and the study's leg
    carried onto it (`carry_onto`), which is carried only once its first three descriptions hold,
    so nothing is carried that no part reads; each head's code, or why the bones were not carried.
    Both use the same operations on opposite physical sides. No lens is read again."""
    assigned = own.record["assignments"]
    names = ("medial_gastrocnemius", "lateral_gastrocnemius")
    for name in names:
        assigned[name] = None
    vessel_names = ("popliteal_artery", "popliteal_vein")
    vessel_codes = assigned["codes"]
    vessel_shape = own.arrays["b1_labels"].shape
    own.arrays["a2_popliteal_artery"] = np.zeros(vessel_shape, dtype=bool)
    own.arrays["a2_popliteal_vein"] = np.zeros(vessel_shape, dtype=bool)
    for name in vessel_names:
        assigned[name] = None
        vessel_codes[name] = "not_named_on_this_slice"

    def abstain_vessels(code: str) -> None:
        for vessel in vessel_names:
            vessel_codes[vessel] = code

    knee = assigned["knee"]
    reads("series", ("row",), "gastrocnemius")
    reads("naming", ("in_plane",), "gastrocnemius")
    # the tag is stored as text
    fat_suppressed = int(own.series.row.fat_suppression) == 1
    code = gastrocnemius_code(
        not own.assignment.in_plane[2], knee, fat_suppressed, True, True, True, True
    )
    if code != "identified":
        abstain_vessels(code)
        return dict.fromkeys(names, code)
    if leg is None:
        abstain_vessels("abstain_no_bone_carried")
        return dict.fromkeys(names, "abstain_no_bone_carried")
    reads("series", ("slice_thickness_mm",), "gastrocnemius")
    thickness = own.series.slice_thickness_mm[own.record["slice_index"]]
    if thickness is None:
        abstain_vessels("abstain_no_slice_thickness")
        return dict.fromkeys(names, "no_slice_thickness")
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
        code = gastrocnemius_code(
            True, knee, True, bool(bone.any()), notch is not None, False, False
        )
        abstain_vessels(code)
        return dict.fromkeys(names, code)
    reads("naming", ("peaks",), "gastrocnemius")
    reads("interiors", ("labels",), "gastrocnemius")
    labels = own.arrays["b1_labels"]
    peaks = own.assignment.peaks
    # the inner side is toward the other knee: the patient's left for a right knee
    inner_mm = notch if knee == "R" else -notch
    # a copy: the names the slice made alone (`Measured.assignment`) stay as made
    objects = own.arrays["a1_objects"].copy()
    head_codes = {}
    head_masks = {}
    head_peaks = {}
    condyles = {}
    lateral_codes = {
        "abstain_no_inner_condyle": "abstain_no_outer_condyle",
        "abstain_no_body_behind_the_inner_condyle": "abstain_no_body_behind_the_outer_condyle",
    }
    placed_any = False
    for name, toward in ((names[0], inner_mm), (names[1], -inner_mm)):
        condyle = inner_condyle(peaks, labels, bone, toward)
        head = np.zeros(labels.shape, dtype=bool)
        if condyle is not None:
            head = gastrocnemius_head(
                peaks, labels, bone, condyle, carried.back_mm, toward
            )
        condyles[name] = condyle
        head_masks[name] = head
        placed = head & (objects == 0)
        objects[placed] = OBJECT_CODES[name]
        assigned[name] = int(labels[head].max()) if head.any() else None
        if head.any():
            territory = int(labels[head].max())
            head_peaks[name] = next(
                peak for peak in peaks if peak.territory == territory
            )
        placed_any |= bool(placed.any())
        code = gastrocnemius_code(
            True, knee, True, True, True, condyle is not None, bool(placed.any())
        )
        head_codes[name] = lateral_codes.get(code, code) if name == names[1] else code
    own.arrays["a1_objects"] = objects
    if placed_any:
        handed("gastrocnemius", ("region",))

    if not all(
        head_codes.get(name) == "identified" and name in head_peaks for name in names
    ):
        abstain_vessels("abstain_requires_both_gastrocnemius_heads")
        return head_codes
    condyle_peaks = [condyles[name] for name in names]
    if any(peak is None for peak in condyle_peaks):
        abstain_vessels("abstain_requires_both_gastrocnemius_heads")
        return head_codes

    reads(
        "carried",
        ("back_mm", "toward_left_mm"),
        "popliteal_lumens",
    )
    reads("naming", ("peaks",), "popliteal_lumens")
    reads("interiors", ("labels",), "popliteal_lumens")
    head_side = [float(inner_mm[head_peaks[name].peak_rc]) for name in names]
    front_of_condyles = max(
        float(carried.back_mm[peak.peak_rc])
        for peak in condyle_peaks
        if peak is not None
    )
    behind_heads = max(float(carried.back_mm[head_masks[name]].max()) for name in names)
    corridor = (
        (inner_mm > min(head_side))
        & (inner_mm < max(head_side))
        & (carried.back_mm > front_of_condyles)
        & (carried.back_mm < behind_heads)
    )
    depth = enclosed_darkness(own.arrays["acquired_plane"])
    handed("popliteal_lumens", ("enclosed_darkness", "corridor"))
    reads("popliteal_lumens", ("enclosed_darkness", "corridor"), "popliteal_lumens")
    artery, vein, components, vessel_code = popliteal_lumens(
        depth, corridor, carried.back_mm, np.asarray(own.frame.spacing_rc)
    )
    own.arrays.update(
        a2_enclosed_darkness=depth,
        a2_vessel_corridor=corridor,
        a2_closed_lumens=components,
        a2_popliteal_artery=artery,
        a2_popliteal_vein=vein,
    )
    for name in vessel_names:
        vessel_codes[name] = vessel_code
    # every closed lumen the rule weighed is kept with the reading; no stage reads them
    handed("popliteal_lumens", ("components",))
    if vessel_code == "identified":
        handed("popliteal_lumens", ("artery", "vein"))
    return head_codes


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
        product="tendons",
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
        product="rest_of_the_field",
    )
    for name, code in laid.items():
        if code is not None:
            partner.record["assignments"]["codes"][name] = code


def name_joint_boundaries(own: Measured, partner: Measured | None) -> None:
    """Locate the anterior recess, its lining surface, and the side recesses' capsular wall.

    Save separate masks where tissue surfaces coexist with fluid or collateral structures.
    Reuse the white reading, shared physical positions, and the pair's physical-place match.
    Each part the slice identifies is handed on, and read by the partner where it is laid on.
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
    parts = tuple(
        (field, name, mask, code)
        for (field, name), mask, code in zip(
            JOINT_BOUNDARIES,
            (recess, lining, capsule),
            (recess_code, lining_code, wall_code),
            strict=True,
        )
    )
    for _, name, mask, code in parts:
        own.arrays[f"a2_{name}"] = mask
        codes[name] = code
    identified = tuple(field for field, _, _, code in parts if code == "identified")
    if not identified:
        return
    handed("joint_boundaries", identified)
    if partner is None:
        return
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
    reads("joint_boundaries", identified, "partner")
    for _, name, mask, code in parts:
        if code != "identified":
            continue
        placed = laid_by(mask.astype(np.int16), source) == 1
        partner.arrays[f"a2_{name}"] = placed
        partner.record["assignments"]["codes"][name] = (
            "laid_from_its_partner"
            if placed.any()
            else "abstain_outside_partner_picture"
        )


def name_suprapatellar_pads(own: Measured, partner: Measured | None) -> None:
    """Separate the two pads from their named combined field and the two acquired signals.
    Only the FS source resolves them; the same physical-place matches carry its result back."""
    reads("series", ("row",), "suprapatellar_pads")
    reads("naming", ("in_plane",), "suprapatellar_pads")
    reads("partner", ("objects", "codes"), "suprapatellar_pads")
    plane = own.arrays["acquired_plane"]
    names = ("quadriceps_fat_pad", "prefemoral_fat_pad")
    fields = (*names, "suprapatellar_recess_ridge")
    for name in fields:
        own.arrays[f"a2_{name}"] = np.zeros(plane.shape, dtype=bool)
    codes = own.record["assignments"]["codes"]

    def refuse(code: str) -> None:
        for name in names:
            codes[name] = code

    sagittal = own.assignment.in_plane[1] and own.assignment.in_plane[2]
    if not sagittal:
        refuse("abstain_not_a_sagittal_slice")
        return
    if not (
        int(own.series.row.fat_suppression) == 1
        and int(own.series.row.fluid_sensitive) == 1
    ):
        refuse("abstain_requires_fluid_sensitive_fat_suppression")
        return
    combined = own.arrays["a1_objects"] == OBJECT_CODES["suprapatellar_fat"]
    if not combined.any():
        refuse("abstain_no_suprapatellar_fat")
        return
    if partner is None or int(partner.series.row.fat_suppression) != 0:
        refuse("abstain_no_non_fat_suppressed_twin")
        return
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
        refuse("abstain_" + source)
        return
    reads("series", ("volume",), "relative_signal")
    paired = laid_by(partner.arrays["acquired_plane"].astype(np.float64), source)
    paired[source < 0] = np.nan
    handed("paired_light", ("signal",))
    reads("paired_light", ("signal",), "relative_signal")
    ratio = relative_signal(plane, paired)
    handed("signal_ratio", ("value",))
    reads("signal_ratio", ("value",), "suprapatellar_pads")
    shared = measures_of(
        own.record["series_uid"], own.record["slice_index"], plane, own.frame
    )
    anterior, posterior, ridge, code = suprapatellar_pads(
        ratio, combined, own.frame.basis_lps, shared.along(1)
    )
    own.arrays["a2_nonfs_signal"] = paired
    own.arrays["a2_relative_signal"] = ratio
    for name, mask in zip(fields, (anterior, posterior, ridge), strict=True):
        own.arrays[f"a2_{name}"] = mask
    refuse(code)
    if code != "identified":
        return
    handed("suprapatellar_pads", fields)
    reverse = matched(
        partner.series,
        partner.record,
        partner.frame,
        partner.arrays["acquired_plane"].shape,
        own.record,
        own.frame,
        plane,
    )
    if isinstance(reverse, str):
        return
    reads("suprapatellar_pads", fields, "partner")
    for name in fields:
        placed = laid_by(own.arrays[f"a2_{name}"].astype(np.int16), reverse) == 1
        partner.arrays[f"a2_{name}"] = placed
        if name in names:
            partner.record["assignments"]["codes"][name] = (
                "laid_from_its_partner"
                if placed.any()
                else "abstain_outside_partner_picture"
            )


def name_iliotibial_band(own: Measured, partner: Measured | None) -> None:
    """Read the ITB on the existing middle coronal, then lay its trace onto the twin.
    The middle slice's native fat and bone names provide the targets; no lens is read again.
    FS targets are initialized before non-FS sources, as for the joint boundaries.
    """
    plane = own.arrays["acquired_plane"]
    reads("series", ("row",), "iliotibial_band")
    reads("partner", ("objects", "codes"), "iliotibial_band")
    reads("interiors", ("available",), "iliotibial_band")
    mask, readings, code = iliotibial_band_on_slice(
        plane,
        own.arrays["a1_objects"],
        own.arrays["b1_available"],
        own.frame.basis_lps,
        own.record["assignments"]["knee"],
        int(own.series.row.fat_suppression) == 1,
        measures=measures_of(
            own.record["series_uid"], own.record["slice_index"], plane, own.frame
        ),
    )
    own.arrays["a2_iliotibial_band"] = mask
    for name, value in readings.items():
        own.arrays[f"a2_itb_{name}"] = value
    own.record["assignments"]["codes"]["iliotibial_band"] = code
    if code != "identified":
        return
    handed("iliotibial_band", ("region",))
    if partner is None or int(partner.series.row.fat_suppression) != 1:
        return
    laid = lay_parts(
        partner,
        (partner.record, partner.arrays, partner.frame),
        (own.record, own.arrays, own.frame),
        ("iliotibial_band",),
        product="iliotibial_band",
    )
    partner.record["assignments"]["codes"]["iliotibial_band"] = (
        laid["iliotibial_band"] or "abstain_outside_partner_picture"
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
    semitendinosus = np.zeros(labels.shape, dtype=bool)
    st_code = "abstain_no_semimembranosus_reference"
    gracilis = np.zeros(labels.shape, dtype=bool)
    gr_code = "abstain_no_semimembranosus_reference"
    if toward_left is not None:
        # the inner side is toward the other knee: the patient's left for a right knee
        inner_mm = toward_left if knee == "R" else -toward_left
        condyle = inner_condyle(
            field.peaks, labels, carried.femur | carried.tibia, inner_mm
        )
        if condyle is not None:
            spacing = np.asarray(frame.spacing_rc)
            shared = measures_of(uid, z, plane, frame)
            reads("interiors", ("dark",), "hamstring_bodies")
            reads("carried", ("back_mm", "toward_left_mm"), "hamstring_bodies")
            bodies = dark_tendon_bodies(
                arrays["b1_dark"],
                # the places neither the air, the skin nor the black margin hold
                (field.objects == 0) & ~margin_of(uid, z, plane),
                spacing,
                carried.back_mm,
                inner_mm,
            )
            handed("hamstring_bodies", field_names(bodies))
            arrays["a2_dark_tendon_candidates"] = bodies.labels
            arrays["a2_dark_tendon_back_mm"] = bodies.back_mm
            arrays["a2_dark_tendon_inner_mm"] = bodies.inner_mm
            reads("hamstring_bodies", field_names(bodies), "semimembranosus")
            tendon = semimembranosus_on_slice(
                bodies,
                labels == condyle.territory,
                condyle,
                carried.back_mm,
                inner_mm,
                spacing,
                shared,
            )
            reads("hamstring_bodies", field_names(bodies), "semitendinosus")
            reads("semimembranosus", ("region",), "semitendinosus")
            reads("carried", ("back_mm", "toward_left_mm"), "semitendinosus")
            reads("field", ("peaks",), "semitendinosus")
            semitendinosus, st_code = semitendinosus_on_slice(
                bodies, tendon, condyle, carried.back_mm, inner_mm, spacing, shared
            )
            if tendon.any() and semitendinosus.any():
                reads("interiors", ("dark",), "native_hamstring_bodies")
                reads(
                    "carried", ("back_mm", "toward_left_mm"), "native_hamstring_bodies"
                )
                native_bodies = native_dark_bodies(
                    arrays["b1_dark"],
                    (field.objects == 0) & ~margin_of(uid, z, plane),
                    carried.back_mm,
                    inner_mm,
                )
                handed("native_hamstring_bodies", field_names(native_bodies))
                reads("native_hamstring_bodies", field_names(native_bodies), "gracilis")
                reads("semimembranosus", ("region",), "gracilis")
                reads("semitendinosus", ("region",), "gracilis")
                gracilis, gr_readings, gr_code = gracilis_on_slice(
                    native_bodies,
                    tendon,
                    semitendinosus,
                    carried.back_mm,
                    inner_mm,
                    spacing,
                    knee,
                    shared,
                )
                for name, value in gr_readings.items():
                    arrays[f"a2_gracilis_{name}"] = value
            elif tendon.any():
                gr_code = "abstain_no_semitendinosus_reference"
    arrays["a2_gracilis"] = gracilis
    record["assignments"]["codes"]["gracilis"] = gr_code
    if gr_code == "identified":
        handed("gracilis", ("region",))
    arrays["a2_semitendinosus"] = semitendinosus
    record["assignments"]["codes"]["semitendinosus"] = st_code
    if st_code == "identified":
        handed("semitendinosus", ("region",))
    # The tendons share this slice; the middle slice keeps its own tissue names.
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
        reads("bursal_fluid", ("white",), "bursa")
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
    if bursal.any():
        handed("bursa", ("region",))
    record["assignments"]["codes"]["gastrocnemius_semimembranosus_bursa"] = bursa_code(
        bright,
        tendon is not None and bool(tendon.any()),
        bool(posterior.any()),
        bool(bursal.any()),
    )
    record["main_slice"] = {"object": "semimembranosus"}
    return record, arrays, frame


# What the sartorius rule reads of its own readings, and what it keeps without reading.
SARTORIUS_READ = (
    "gracilis_target",
    "smooth",
    "surround",
    "lightness",
    "grey_bodies",
    "body_inner_mm",
    "body_back_mm",
    "body_size_pixels",
    "eligible_ids",
    "target_distance_mm",
    "eligible_reach_mm",
)
SARTORIUS_KEPT = (
    "gracilis_source_lps",
    "surround_window_pixels",
    "gracilis_source_separation_mm",
    "body_status",
)


def gracilis_source(
    measured: list[Measured], found: list[tuple[dict, dict[str, np.ndarray]]]
) -> np.ndarray | str:
    """The gracilis's places in the scanner's millimetres, put there once from the first of the
    study's semimembranosus-group records (`find_part`, the ones that name the tendon) whose
    gracilis its own lens named (`identified`, not one laid from a partner), through the frame of
    the slice it was named on (`plane_frame`); or why there are none. Handed on to every middle
    axial's sartorius, which projects them (`name_sartorius`): they are a location there, not a
    mask."""
    for record, arrays in found:
        if record["assignments"]["codes"].get("gracilis") != "identified":
            continue
        reads("gracilis", ("region",), "gracilis_places")
        places = np.argwhere(arrays["a2_gracilis"])
        if not len(places):
            continue
        series = next(
            m.series for m in measured if m.record["series_uid"] == record["series_uid"]
        )
        frame = plane_frame(series, record["slice_index"])
        if isinstance(frame, str):
            return "abstain_gracilis_source_geometry_unreadable"
        handed("gracilis_places", ("lps",))
        return frame.to_patient(places.astype(float))
    return "abstain_no_native_gracilis"


def name_sartorius(own: Measured, source: np.ndarray | str) -> None:
    """The sartorius named on this series' middle slice where the leg does not run in its plane, an
    axial one, fat-suppressed and fluid-sensitive (its paragraph in `knee.objects.assignments`),
    from the lens already read there and the gracilis's places (`gracilis_source`, `source`, or why
    there are none) projected onto it. Its mask is separate (`a2_sartorius`) and every reading the
    rule made is kept beside it (`a2_sartorius_<reading>`); the slice's own names are left as they
    are. The contrast over the slice is read at most once, and only once the cheap prerequisites
    hold; no lens is read again."""
    plane = own.arrays["acquired_plane"]
    own.arrays["a2_sartorius"] = np.zeros(plane.shape, dtype=bool)
    codes = own.record["assignments"]["codes"]
    reads("naming", ("in_plane",), "sartorius")
    reads("series", ("row",), "sartorius")
    if own.assignment.in_plane[2]:
        codes["sartorius"] = "abstain_leg_runs_in_the_plane"
        return
    if not (
        int(own.series.row.fat_suppression) == 1
        and int(own.series.row.fluid_sensitive) == 1
    ):
        codes["sartorius"] = "abstain_requires_fluid_sensitive_fat_suppression"
        return
    if isinstance(source, str):
        codes["sartorius"] = source
        return
    uid, index = own.record["series_uid"], own.record["slice_index"]
    reads("interiors", ("dark", "available"), "sartorius")
    reads("gracilis_places", ("lps",), "sartorius")
    mask, readings, code = sartorius_on_slice(
        plane,
        own.arrays["b1_dark"],
        ~own.arrays["b1_available"] | margin_of(uid, index, plane),
        source,
        own.frame,
        own.record["assignments"]["knee"],
        measures_of(uid, index, plane, own.frame),
    )
    own.arrays["a2_sartorius"] = mask
    for name, value in readings.items():
        own.arrays[f"a2_sartorius_{name}"] = value
    codes["sartorius"] = code
    made = [name for name in (*SARTORIUS_READ, *SARTORIUS_KEPT) if name in readings]
    handed("sartorius_readings", made)
    reads(
        "sartorius_readings",
        [name for name in made if name in SARTORIUS_READ],
        "sartorius",
    )
    if "lightness" in readings:
        ledger.record("sartorius.contrast_readings", planes=1)
    if code == "identified":
        handed("sartorius", ("region",))


def retinacula_z(
    own: Measured, leg: Leg | None, patella_centre: np.ndarray | None
) -> tuple[int, list[float], str] | str:
    """The axial slice through the already named patella (the retinacula's bootstrap), its slices'
    thicknesses and the knee's side, or why this series has none: the one statement of the selection,
    read by the retinacula stage and by the recess family's extra planes alike."""
    reads("naming", ("in_plane",), "patellar_retinacula")
    reads("series", ("row",), "patellar_retinacula")
    if own.assignment.in_plane[2]:
        return "abstain_leg_runs_in_the_plane"
    knee = own.record["assignments"]["knee"]
    if knee not in ("R", "L"):
        return "abstain_header_names_no_knee"
    if not (
        int(own.series.row.fat_suppression) == 1
        and int(own.series.row.fluid_sensitive) == 1
    ):
        return "abstain_requires_fluid_sensitive_fat_suppression"
    if leg is None:
        return "abstain_no_bone_carried"
    if patella_centre is None:
        return "abstain_no_patella_carried"
    if not len(leg.femur_lps):
        return "abstain_no_femur_carried"
    reads("patella", ("centre_lps",), "patellar_retinacula")
    reads("leg", ("femur_lps", "patella_lps"), "patellar_retinacula")
    reads("series", ("volume", "geometry", "slice_thickness_mm"), "patellar_retinacula")
    volume, geometry = own.series.volume, own.series.geometry
    if volume is None or geometry is None:
        return "abstain_no_readable_series"
    thicknesses = own.series.slice_thickness_mm
    if any(t is None for t in thicknesses):
        return "abstain_no_slice_thickness"
    thickness_values = [float(t) for t in thicknesses if t is not None]
    z = slice_through(
        patella_centre, geometry.position, own.frame.normal(), thickness_values
    )
    if z is None:
        return "abstain_patella_off_the_slices"
    return z, thickness_values, str(knee)


def retinacula_slice(
    own: Measured, leg: Leg | None, patella_centre: np.ndarray | None
) -> tuple[dict, dict[str, np.ndarray], PlaneFrame] | str:
    """The axial slice through the already named patella, read once for both retinacula."""
    chosen = retinacula_z(own, leg, patella_centre)
    if isinstance(chosen, str) or leg is None:
        return chosen if isinstance(chosen, str) else "abstain_no_bone_carried"
    z, thickness_values, knee = chosen
    return retinacula_on(own, leg, z, thickness_values, knee, "patellar_retinacula")


def retinacula_on(
    own: Measured,
    leg: Leg,
    z: int,
    thickness_values: list[float],
    knee: str,
    reader: str,
) -> tuple[dict, dict[str, np.ndarray], PlaneFrame] | str:
    """The existing retinacula rule (`retinacular_walls`) on ONE axial slice `z` of a series: its
    lens and field (once per slice, so a plane another family read is handed on), the carried femur
    and patella on it, the white the fluid-to-marrow relation reads, and both walls with their
    decisions. `reader` is the stage whose lens readings the ledger counts."""
    volume = own.series.volume
    if volume is None:
        return "abstain_no_readable_series"
    frame = plane_frame(own.series, z)
    if isinstance(frame, str):
        return frame
    reads("background", ("split",), "patellar_retinacula")
    record, arrays, field = read_part_slice(
        own.series,
        z,
        volume[z],
        frame,
        own.record["background_split"],
        knee,
        reader,
    )
    reads("interiors", ("labels", "available"), "patellar_retinacula")
    reads("field", ("peaks", "objects"), "patellar_retinacula")
    plane = arrays["acquired_plane"]
    femur, _ = leg_on(leg, own.series, z, frame, plane.shape, thickness_values[z])
    patella = places_on_slice(leg.patella_lps, frame, plane.shape, thickness_values[z])
    available = (
        arrays["b1_available"]
        & (field.objects == 0)
        & ~margin_of(own.record["series_uid"], z, plane)
    )
    shared = measures_of(own.record["series_uid"], z, plane, frame)
    marrow_places = femur & available
    light = shared.light(marrow_places) if marrow_places.any() else 0.0
    white = (
        (plane > FLUID_BRIGHTER * light) & available
        if light > 0
        else np.zeros(plane.shape, bool)
    )
    handed("retinacular_fluid", ("white",))
    reads("retinacular_fluid", ("white",), "patellar_retinacula")
    back, side = shared.along(1), shared.along(0)
    inner = side if knee == "R" else -side
    readings, codes = retinacular_walls(
        plane,
        white,
        arrays["b1_labels"],
        field.peaks,
        patella,
        femur,
        frame.basis_lps,
        back,
        inner,
        np.asarray(frame.spacing_rc),
        available,
        shared,
    )
    arrays["a2_retinacula_carried_patella"] = patella
    arrays["a2_retinacula_carried_femur"] = femur
    arrays["a2_retinacula_field_objects"] = field.objects
    for name, value in readings.items():
        arrays[f"a2_{name}"] = value
    # This record names the two walls; the field's air/skin remain retained as readings above.
    arrays["a1_objects"] = np.zeros(plane.shape, dtype=np.int8)
    record["assignments"]["codes"].update(codes)
    record["assignments"]["codes"]["patellar_retinacula"] = (
        "identified"
        if any(code in NAMED for code in codes.values())
        else "abstain_no_retinacular_wall"
    )
    record["main_slice"] = {"object": "patellar_retinacula"}
    return record, arrays, frame


@dataclass(frozen=True)
class FibulaProfile:
    """The fibula's cheap profile through depth, one entry per slice of the series, stack order:
    the pointer's status (`FIBULA_POINTER_STATUS`), the area in square millimetres of the largest
    whole body that could be the fibula (0.0 where measured absent, NaN where it is not read, not
    readable or cut), that body's middle in the scanner's millimetres (NaN where none) and how many
    bodies could be it; the corridor's squint tiles and those of them that could hold marrow-like
    light (the extrema over every tile a finer block with a pixel in the tile can touch do not
    exclude it); the native window the finer reading ran over (-1 where none) and the block's size
    in millimetres (NaN where none) and in native pixels (-1 where none); the finer readings
    themselves, one per slice read (`fine`: the block medians and the pointer's body and tibia
    reference bodies on that block grid, at their own small resolution); and what it was read
    against: the tibia's marrow light on the middle slice, the tibia's top and its middle in the
    scanner's millimetres."""

    status: np.ndarray
    area_mm2: np.ndarray
    centroid_lps: np.ndarray
    candidates: np.ndarray
    corridor: np.ndarray
    could: np.ndarray
    window_rc: np.ndarray
    cell_mm: np.ndarray
    block_px: np.ndarray
    fine: tuple[FineReading, ...]
    light: float
    top_mm: float
    middle_lps: np.ndarray


def fibula_profile(
    series: Series,
    stack: SquintStack,
    tibia: np.ndarray,
    middle_rc: tuple[int, int],
    light: float,
    top_mm: float,
    middle_lps: np.ndarray,
    knee: str,
) -> FibulaProfile:
    """The fibula's cheap profile through the series' depth: where each slice's corridor holds a body
    that could be the fibula (`fibula_pointer`), read without the lens.

    On each slice the corridor's squint tiles (`fibula_corridor`: the tibia's outer back, below its
    top) are first asked, by their minimum and maximum, whether any could hold a block as bright as
    the tibia's marrow. A block's median is taken over its footprint, which can cross into the next
    tile, so a tile is asked over every tile a block with a pixel in it can touch
    (`footprint_reach`, `could_hold_level_in_reach`, the block's size from the slice's own pixel
    pitch), never over its own extrema alone: where none can and no tile in reach was unseen, the
    corridor holds no marrow-like body (measured absent, 0.0); where none can but a tile in reach was
    not seen, nothing is said (NaN). Otherwise the finer reading runs over the window of the tiles that could,
    with `BONE_MM` of context round them so that the tibia's reference body and a whole body lie in
    it (`block_medians` at `LIGAMENT_SMOOTH_MM`, the length over which the light is read as uniform
    and not speckled), and the pointer reads that, with the tibia's carried places and its middle
    (`middle_rc`, the deepest peak of its territory on the middle slice) as its two anchors. A slice whose corridor is empty is not read: it
    lies wholly off the corridor, which says nothing of the fibula and is not zero either. The
    unseen places of a slice (`seen_native`) are NaN in the blocks, never darkness. The counts of
    slices read finely and excluded by the tiles are on the ledger (`fibula.cheap_readings`,
    `fibula.tile_exclusions`)."""
    reads("squint_stack", ("minimum", "maximum", "centres_lps", "bounds_rc"), "fibula")
    depth = int(stack.median.shape[0])
    tiles = stack.median.shape[1:]
    status = np.full(depth, FIBULA_POINTER_STATUS["not_read"], dtype=np.int8)
    area = np.full(depth, np.nan)
    centroid = np.full((depth, 3), np.nan)
    candidates = np.zeros(depth, dtype=np.int32)
    corridor = np.zeros((depth, *tiles), dtype=bool)
    could = np.zeros((depth, *tiles), dtype=bool)
    window_rc = np.full((depth, 4), -1, dtype=np.int32)
    cell_mm = np.full((depth, 2), np.nan)
    cell_px = np.full((depth, 2), -1, dtype=np.int32)
    fine: list[FineReading] = []
    reach_of: dict[tuple[int, int], Any] = {}
    low, high = LIKE_THE_TIBIA
    finely = excluded = 0
    middle = np.zeros(tibia.shape, dtype=bool)
    middle[middle_rc] = True
    # a marrow light that is not a positive finite number is no anchor to ask the tiles against: a
    # comparison with it is false for every tile, which would read as an exclusion, so no corridor
    # slice is excluded or read on it
    anchored = bool(np.isfinite(light) and light > 0)
    for z in range(depth):
        corridor[z] = fibula_corridor(stack.centres_lps[z], top_mm, middle_lps, knee)
        if not corridor[z].any():
            continue
        frame = plane_frame(series, z)
        if isinstance(frame, str) or not anchored:
            status[z] = FIBULA_POINTER_STATUS["unreadable"]
            continue
        # a block is read over its footprint, which crosses tile boundaries: ask over every tile
        # a block with a pixel in the corridor's tile can touch, never over the tile alone
        block = block_pixels(frame.spacing_rc, LIGAMENT_SMOOTH_MM)
        if block not in reach_of:
            reach_of[block] = footprint_reach(stack.bounds_rc, block)
        possible, unseen_tiles = could_hold_level_in_reach(
            stack.minimum[z],
            stack.maximum[z],
            low * light,
            high * light,
            reach_of[block],
        )
        could[z] = corridor[z] & possible
        if not could[z].any():
            if (corridor[z] & unseen_tiles).any():
                status[z] = FIBULA_POINTER_STATUS["unreadable"]
            else:
                status[z], area[z] = FIBULA_POINTER_STATUS["none"], 0.0
                excluded += 1
            continue
        plane, unseen = seen_native(series, z, "fibula")
        rows, cols = plane.shape
        spacing = np.asarray(frame.spacing_rc)
        bounds = stack.bounds_rc[could[z]]
        reach = np.ceil(BONE_MM / spacing).astype(int)
        window = (
            max(0, int(bounds[:, 0].min()) - int(reach[0])),
            min(rows, int(bounds[:, 1].max()) + int(reach[0])),
            max(0, int(bounds[:, 2].min()) - int(reach[1])),
            min(cols, int(bounds[:, 3].max()) + int(reach[1])),
        )
        reading = block_medians(
            plane, unseen, frame.spacing_rc, LIGAMENT_SMOOTH_MM, window
        )
        centres = frame.to_patient(block_centres_rc(reading).reshape(-1, 2)).reshape(
            *reading.median.shape, 3
        )
        cut = np.zeros(reading.median.shape, dtype=bool)
        cut[0, :] = window[0] > 0
        cut[-1, :] = window[1] < rows
        cut[:, 0] = window[2] > 0
        cut[:, -1] = window[3] < cols
        point = fibula_pointer(
            reading.median,
            np.asarray(reading.block_mm),
            centres,
            block_holds(tibia, reading),
            block_holds(middle, reading),
            light,
            top_mm,
            middle_lps,
            knee,
            cut,
        )
        finely += 1
        status[z], area[z], centroid[z] = (
            point.status,
            point.area_mm2,
            point.centroid_lps,
        )
        candidates[z] = point.candidates
        window_rc[z], cell_mm[z], cell_px[z] = (
            window,
            reading.block_mm,
            reading.block_px,
        )
        # kept as made, at its own small resolution: the block medians and the bodies drawn on them
        fine.append(
            FineReading(
                z,
                reading.window_rc,
                reading.block_px,
                reading.block_mm,
                reading.median,
                point.body,
                point.tibia,
            )
        )
    ledger.record("fibula.cheap_readings", planes=finely)
    ledger.record("fibula.tile_exclusions", planes=excluded)
    handed("fibula_profile", ("status", "area_mm2"))
    # kept, not read: no stage after the pointer reads the blocks or the bodies it drew
    handed("fibula_profile", ("fine",))
    return FibulaProfile(
        status,
        area,
        centroid,
        candidates,
        corridor,
        could,
        window_rc,
        cell_mm,
        cell_px,
        tuple(fine),
        float(light),
        float(top_mm),
        np.asarray(middle_lps, dtype=np.float64),
    )


def finite_or_none(value: float) -> float | None:
    """A measured number, or None where it is NaN: an unknown is never written as a value."""
    return float(value) if np.isfinite(value) else None


def fibula_support(
    series: Series,
    middle: PlaneFrame,
    frame: PlaneFrame,
    main_z: int,
    profile: FibulaProfile,
    pointed: tuple[list[tuple[int, int]], list[np.ndarray], list[int]],
    planes: list[int],
    accepted: tuple[int, ...],
    places: np.ndarray | None,
    marrow: float,
    knee: str,
) -> tuple[dict, dict[str, np.ndarray], list[str]]:
    """The fibula's support through depth, as measured: its record, its arrays and what is not known.

    Three things are kept apart. The RAW POINTER SUPPORT is the profile's runs (`fibula_profile`,
    `positive_runs`), a cheap marrow-like body through depth; each run says what the established
    rule (`planes` it was read on, `accepted` those it identified the fibula on) made of the planes
    read for it: confirmed, rejected or not read. The CONFIRMED EXTENT is only what a native reading
    holds: the slices the rule identified it on, the confirmed pointer runs, and the head's outward
    continuation from the selected slice (`lateral_to_the_head`, the biceps femoris tendon's walk, made
    once for both: `head_walk`), a walk that stays connected to the identified slice. A pointer run the
    rule rejected on every plane read for it is not the bone's extent; it is a named unresolved
    candidate range (`unresolved_candidate_ranges`) with its envelope, and in the confirmed
    support's status it is `UNCONFIRMED_CANDIDATE`, neither body nor measured absent. The head's body
    on each slice it walked is kept, with its target, even where the biceps femoris tendon later
    abstains.

    The runs are given in the scanner's millimetres along the series' normal from the selected slice
    (`depth_offsets_mm`) as ENVELOPES over the sampled slabs (`support_intervals_mm`), never dense
    occupancy: each run keeps its sampled slabs and the gaps between them (`run_slabs_mm`,
    `slab_gaps_mm`), nothing interpolated, and for each end what it touches (`run_neighbours`: the
    scan's edge, a slice measured empty, a slice not read or not readable). A slice the profile
    could not read and the head did not settle is named unknown, never empty, and not read is never
    measured empty. The corridor it was read in, the frame it was measured from and the profile's
    finer readings at their own small resolution (`pack_fine_readings`, ragged, with each slice's
    window, block size and shape) are kept. Support is not a segmentation and joins no slices the
    readings did not."""
    runs, maxima, confirm = pointed
    depth = len(profile.status)
    reads("series", ("geometry", "slice_thickness_mm"), "fibula")
    origins = np.asarray(
        [np.asarray(p, dtype=float) for p in series.geometry.position]
        if series.geometry is not None
        else [],
        dtype=float,
    )
    known = [None if t is None else float(t) for t in series.slice_thickness_mm]
    thick = np.asarray([np.nan if t is None else t for t in known], dtype=float)
    sound = (
        origins.ndim == 2
        and origins.shape == (depth, 3)
        and bool(np.all(np.isfinite(origins)))
        and len(thick) == depth
    )
    normal = middle.normal()
    offsets = (
        depth_offsets_mm(origins, normal, main_z) if sound else np.full(depth, np.nan)
    )
    head_area = np.full(depth, np.nan)
    head_status = np.zeros(depth, dtype=np.int8)
    walk_code, face = "abstain_no_front_to_back_places", None
    walk: HeadWalk | None = None
    if places is not None and sound:
        walk = head_walk(series, places, knee, origins, normal, known, lambda: marrow)
        reads("head_walk", ("areas", "status"), "fibula")
        face, head_area, head_status, walk_code = (
            walk.face,
            walk.areas,
            walk.status,
            walk.code,
        )
    ledger.record("fibula.head_readings", planes=int(np.isfinite(head_area).sum()))
    # what the established rule made of the planes read for each pointer run
    read_planes, identified = set(planes), {int(z) for z in accepted}
    run_planes: list[list[int]] = []
    confirmation = np.zeros(len(runs), dtype=np.int8)
    for i, ((start, stop), peaks) in enumerate(zip(runs, maxima, strict=True)):
        here = sorted(
            {int(z) for z in peaks}
            | {int(z) for z in confirm if z in (start - 1, stop)}
        )
        run_planes.append(here)
        if any(z in identified for z in here):
            confirmation[i] = RUN_CONFIRMATION["confirmed_by_the_native_rule"]
        elif any(z in read_planes for z in here):
            confirmation[i] = RUN_CONFIRMATION["rejected_by_the_native_rule"]
        else:
            confirmation[i] = RUN_CONFIRMATION["not_read_natively"]
    confirmed_code = RUN_CONFIRMATION["confirmed_by_the_native_rule"]
    names_of = {value: key for key, value in RUN_CONFIRMATION.items()}
    combined = profile.status.copy()
    for (start, stop), code in zip(runs, confirmation, strict=True):
        if code != confirmed_code:
            combined[start:stop] = UNCONFIRMED_CANDIDATE
    combined[head_status == HEAD_SLICE_STATUS["head_still_a_disc"]] = (
        FIBULA_POINTER_STATUS["body"]
    )
    combined[head_status == HEAD_SLICE_STATUS["head_no_longer_a_disc"]] = (
        FIBULA_POINTER_STATUS["none"]
    )
    # a plane the established rule identified the fibula on is native support, whatever else says
    native = np.asarray(sorted(identified), dtype=np.int32)
    contradicted = native[
        head_status[native] == HEAD_SLICE_STATUS["head_no_longer_a_disc"]
    ]
    combined[native] = FIBULA_POINTER_STATUS["body"]
    held = (combined == FIBULA_POINTER_STATUS["body"]).astype(float)
    extent = positive_runs(held)
    ends = run_neighbours(extent, combined)
    pointer_ends = run_neighbours(runs, profile.status)
    intervals = (
        support_intervals_mm(offsets, thick, extent)
        if sound
        else np.full((len(extent), 2), np.nan)
    )
    pointer_intervals = (
        support_intervals_mm(offsets, thick, runs)
        if sound
        else np.full((len(runs), 2), np.nan)
    )
    slab = np.column_stack((offsets - thick / 2.0, offsets + thick / 2.0))
    unresolved = (FIBULA_POINTER_STATUS["unreadable"], FIBULA_POINTER_STATUS["cut"])
    unknown = [int(z) for z in np.flatnonzero(np.isin(combined, unresolved))]
    ambiguities = ["only_the_pointed_planes_are_resolved_the_rest_is_support"]
    if len(extent) > 1:
        ambiguities.append("support_is_disjoint")
    if unknown:
        ambiguities.append("slices_the_profile_could_not_read_are_unknown_not_empty")
    if confirm:
        ambiguities.append(
            "a_maximum_beside_a_cut_body_was_read_whole_on_the_full_slice"
        )
    if confirmations(
        runs, maxima, profile.status, (FIBULA_POINTER_STATUS["unreadable"],)
    ):
        # nothing can tell a larger body there from the tibia's own place: named, not confirmed
        ambiguities.append(
            "a_maximum_lies_beside_an_unreadable_slice_a_larger_body_is_not_ruled_out"
        )
    if places is None:
        ambiguities.append("front_to_back_is_not_in_plane_so_no_head_continuation")
    disagree = np.flatnonzero(
        (profile.status == FIBULA_POINTER_STATUS["none"])
        & (head_status == HEAD_SLICE_STATUS["head_still_a_disc"])
    )
    if disagree.size:
        ambiguities.append("the_pointer_and_the_head_disagree")
    if contradicted.size:
        ambiguities.append("the_native_rule_and_the_head_disagree")
    if (confirmation == RUN_CONFIRMATION["rejected_by_the_native_rule"]).any():
        ambiguities.append(
            "a_pointer_run_the_native_rule_rejected_is_not_confirmed_extent"
        )
    if (confirmation == RUN_CONFIRMATION["not_read_natively"]).any():
        ambiguities.append("a_pointer_run_not_read_natively_is_not_confirmed_extent")

    def described(spans, neighbours, spans_mm):
        found = []
        for (a, b), end, (lo, hi) in zip(spans, neighbours, spans_mm, strict=True):
            order = (
                np.argsort(offsets[a:b], kind="stable") if sound else np.arange(b - a)
            )
            slabs = (
                run_slabs_mm(offsets, thick, [(a, b)])[0] if sound else np.empty((0, 2))
            )
            found.append(
                {
                    "slices": [int(a), int(b) - 1],
                    "envelope_mm": [finite_or_none(lo), finite_or_none(hi)],
                    "sampled_slices": [int(a + i) for i in order],
                    "slabs_mm": [[finite_or_none(v) for v in row] for row in slabs],
                    "gaps_mm": [
                        finite_or_none(v)
                        for v in (slab_gaps_mm(slabs) if len(slabs) else [])
                    ],
                    "occupancy": "envelope_over_the_sampled_slabs_never_dense",
                    "ends": [RUN_END_NAMES[int(e)] for e in end],
                }
            )
        return found

    raw = described(runs, pointer_ends, pointer_intervals)
    for entry, here, code in zip(raw, run_planes, confirmation, strict=True):
        entry["planes_read_for_it"] = here
        entry["native_rule"] = names_of[int(code)]
    candidates = []
    for i, ((a, b), entry) in enumerate(zip(runs, raw, strict=True)):
        if confirmation[i] != confirmed_code:
            candidates.append(
                {
                    **entry,
                    "why": entry["native_rule"],
                    "pointer_area_mm2_greatest": float(
                        np.nanmax(profile.area_mm2[a:b])
                    ),
                }
            )
    support = {
        "source": {
            "series_uid": series.row.series_uid,
            "selected_slice": int(main_z),
            "normal": [float(v) for v in normal],
            "frame_origin_lps": [float(v) for v in frame.origin_lps],
        },
        "corridor": {
            "tibia_light": float(profile.light),
            "tibia_top_mm": float(profile.top_mm),
            "tibia_middle_lps": [float(v) for v in profile.middle_lps],
            "side": knee,
            "below_the_tibias_top_mm": float(FIBULA_BELOW_MM),
            "behind_the_tibias_middle": True,
            "block_mm": float(LIGAMENT_SMOOTH_MM),
            "context_mm": float(BONE_MM),
        },
        "pointer_runs": raw,
        "pointer_representatives": [[int(z) for z in peaks] for peaks in maxima],
        "native_resolved_slices": [int(z) for z in native],
        "head": {
            "walk": walk_code,
            "face_slice": None if face is None else int(face),
            "slices": [
                int(z)
                for z in np.flatnonzero(
                    head_status == HEAD_SLICE_STATUS["head_still_a_disc"]
                )
            ],
            "walked": [] if walk is None else [int(z) for z in walk.walked],
            "codes": {}
            if walk is None
            else {
                str(z): head[2] for z, head in zip(walk.walked, walk.heads, strict=True)
            },
        },
        "confirmed_extent": described(extent, ends, intervals),
        "unresolved_candidate_ranges": candidates,
        "unknown_slices": unknown,
    }
    walked = () if walk is None else walk.walked
    arrays: dict[str, np.ndarray] = {
        "a3_fibula_profile_status": profile.status,
        "a3_fibula_profile_area_mm2": profile.area_mm2,
        "a3_fibula_profile_centroid_lps": profile.centroid_lps,
        "a3_fibula_profile_candidates": profile.candidates,
        "a3_fibula_profile_corridor_tiles": profile.corridor,
        "a3_fibula_profile_could_tiles": profile.could,
        "a3_fibula_profile_window_rc": profile.window_rc,
        "a3_fibula_profile_block_mm": profile.cell_mm,
        "a3_fibula_profile_block_px": profile.block_px,
        "a3_fibula_reference_light": np.asarray(profile.light, dtype=np.float64),
        "a3_fibula_reference_top_mm": np.asarray(profile.top_mm, dtype=np.float64),
        "a3_fibula_reference_middle_lps": profile.middle_lps,
        "a3_fibula_pointer_runs": np.asarray(runs, dtype=np.int32).reshape(-1, 2),
        "a3_fibula_pointer_run_ends": pointer_ends.astype(np.int32),
        "a3_fibula_pointer_run_envelope_mm": pointer_intervals,
        "a3_fibula_pointer_run_confirmation": confirmation,
        "a3_fibula_pointer_planes": np.asarray(planes, dtype=np.int32),
        "a3_fibula_native_resolved_slices": native,
        "a3_fibula_head_area_mm2": head_area,
        "a3_fibula_head_status": head_status,
        "a3_fibula_head_walked_slices": np.asarray(walked, dtype=np.int32),
        "a3_fibula_head_bodies": np.stack([h[0] for h in walk.heads])
        if walk is not None and walk.heads
        else np.zeros((0, 0, 0), dtype=bool),
        "a3_fibula_head_targets": np.stack([h[1] for h in walk.heads])
        if walk is not None and walk.heads
        else np.zeros((0, 0, 0), dtype=bool),
        "a3_fibula_support_status": combined,
        "a3_fibula_support_runs": np.asarray(extent, dtype=np.int32).reshape(-1, 2),
        "a3_fibula_support_run_ends": ends.astype(np.int32),
        "a3_fibula_support_run_envelope_mm": intervals,
        "a3_fibula_depth_offsets_mm": offsets,
        "a3_fibula_slice_thickness_mm": thick,
        "a3_fibula_slab_mm": slab,
        "a3_fibula_slice_origins_lps": origins if sound else np.empty((0, 3)),
        "a3_fibula_series_normal": normal,
        "a3_fibula_source_origin_lps": np.asarray(frame.origin_lps, dtype=np.float64),
        "a3_fibula_source_basis_lps": np.asarray(frame.basis_lps, dtype=np.float64),
    }
    for name, value in pack_fine_readings(profile.fine).items():
        arrays[f"a3_fibula_fine_{name}"] = value
    handed("fibula_profile", ("support", "head"))
    return support, arrays, ambiguities


@dataclass(frozen=True)
class FibulaFound:
    """The fibula as found, the one value every stage after it is handed: the main slice's record
    and arrays and its frame; the fibula's places in the scanner's millimetres (`physical`, always;
    `places`, the same where front to back lies in the slice's plane so its front edge can be read,
    else None, which the LCL and the biceps femoris tendon need); the marrow's light over those
    places on that slice (NaN where none is seen); the series and slice it was found on; every plane
    the established rule identified it on (slice, area in square millimetres, pixels); and, once the
    transfer onto the same place of the other sequence is read, that slice's series, index and the
    marrow's light there (None, None, NaN until then, and where it cannot be)."""

    record: dict
    arrays: dict[str, np.ndarray]
    frame: PlaneFrame
    places: np.ndarray | None
    physical: np.ndarray
    light: float
    series_uid: str
    slice_index: int
    resolved: tuple[tuple[int, float, int], ...]
    twin_uid: str | None = None
    twin_index: int | None = None
    twin_light: float = float("nan")


def fibula_head(
    series: Series, z: int, places: np.ndarray, light: float
) -> tuple[np.ndarray, np.ndarray, str, float]:
    """The fibular head's body on native slice z (`fibula_like_head`), the places it was sought
    from (the fibula's, projected onto the slice, `projected_places`), the reading's code and the
    body's area in square millimetres (`head_area_mm2`: NaN where it cannot be said, 0.0 where it
    was measured absent). Made once for the series, the slice, the places and the marrow's light
    it was read against: the fibula's continuation and the biceps femoris tendon's walk are
    handed the same reading, and no head is measured twice."""

    def read() -> tuple[np.ndarray, np.ndarray, str, float]:
        frame = plane_frame(series, z)
        plane, unseen = seen_native(series, z, "fibula_head")
        if isinstance(frame, str):
            none = np.zeros(plane.shape, dtype=bool)
            return none, none, "geometry_unreadable", float("nan")
        target = projected_places(places, frame, plane.shape)
        body, code = fibula_like_head(np.where(unseen, np.nan, plane), target, light)
        area = head_area_mm2(body, code, np.asarray(frame.spacing_rc))
        handed("fibula_head", ("body", "area"))
        return body, target, code, area

    return once(
        "fibula_head",
        (series.row.series_uid, z, digest(places), repr(float(light))),
        read,
    )


@dataclass(frozen=True)
class HeadWalk:
    """The outward walk to the fibular head's lateral face, made once (`head_walk`): `face` the
    first slice where the head is no longer a disc (None where the walk found none), `areas` and
    `status` per native slice (NaN and `HEAD_SLICE_STATUS["unread"]` where it never went), `code`
    its reading, `walked` the slices it asked a head of in the order it asked, `heads` the shared
    reading of each (`fibula_head`: body, target, code, area) and `light` the marrow's light the
    heads were read against (None where the walk never reached a head): every head it measured, kept
    for each consumer even where a later consumer abstains."""

    face: int | None
    areas: np.ndarray
    status: np.ndarray
    code: str
    walked: tuple[int, ...]
    heads: tuple[tuple[np.ndarray, np.ndarray, str, float], ...]
    light: float | None


def head_walk(
    series: Series,
    places: np.ndarray,
    knee: str,
    origins: np.ndarray,
    normal: np.ndarray,
    thicknesses: Sequence[float | None],
    light_of: Callable[[], float],
) -> HeadWalk:
    """The walk to the head's lateral face (`lateral_to_the_head`) with every head it measured, made
    once for the measurement it is: the series, the fibula's places, the knee's side, the slices'
    origins and thicknesses and the series' normal, and the marrow's light the heads are read
    against. `light_of` gives that light and is asked only when the walk reaches its first head,
    so a walk that abstains before any head reads nothing for it. The fibula's continuation and the
    biceps femoris tendon's rule are each handed the same value when all of those are the same; a
    walk read against another light, and one over other places, series or thicknesses, is another
    walk, never an alias."""
    base = (
        series.row.series_uid,
        digest(np.asarray(places, dtype=np.float64)),
        knee,
        digest(np.asarray(origins, dtype=np.float64)),
        digest(np.asarray(normal, dtype=np.float64)),
        tuple(None if t is None else float(t) for t in thicknesses),
    )

    def make() -> HeadWalk:
        walked: list[int] = []
        heads: list[tuple[np.ndarray, np.ndarray, str, float]] = []
        used: list[float] = []

        def area(z: int) -> float:
            light = float(light_of())
            used.append(light)
            head = fibula_head(series, z, places, light)
            reads("fibula_head", ("area",), "head_walk")
            walked.append(int(z))
            heads.append(head)
            return head[3]

        face, areas, status, code = lateral_to_the_head(
            places, origins, normal, thicknesses, knee, area
        )
        handed("head_walk", ("face", "areas", "status", "heads"))
        return HeadWalk(
            face,
            areas,
            status,
            code,
            tuple(walked),
            tuple(heads),
            used[0] if used else None,
        )

    # The walks made for this measurement, by the light each was read against (None where it read
    # no head, which holds for any light). The light is asked of only when an earlier walk of the
    # same measurement shows this one will reach a head: the conditions before the first head
    # do not depend on it.
    walks: dict[str | None, HeadWalk] = once("head_walk_index", base, dict)
    if None in walks:
        ledger.record("head_walk.handed_on")
        return walks[None]
    if walks:
        wanted = repr(float(light_of()))
        if wanted in walks:
            ledger.record("head_walk.handed_on")
            return walks[wanted]
    made = make()
    walks[None if made.light is None else repr(made.light)] = made
    ledger.record("head_walk.made")
    return made


def retain_fibula_profile(
    record: dict,
    arrays: dict[str, np.ndarray],
    profile: FibulaProfile,
    pointed: Sequence[int],
    read_at: dict[int, tuple],
    outcome: str,
) -> None:
    """Keep what the profile and the pointed planes measured when no fibula was named: with no main
    record, the series' own middle record (`record`, `arrays`, saved by the caller) is where the
    finer readings, the profile and every pointed plane's lens readings stay, under the same
    names a named fibula's record uses, with the outcome beside them. Nothing is read from them
    afterwards; they are kept, as the named case's are."""
    arrays.update(
        {
            "a3_fibula_profile_status": profile.status,
            "a3_fibula_profile_area_mm2": profile.area_mm2,
            "a3_fibula_profile_centroid_lps": profile.centroid_lps,
            "a3_fibula_profile_candidates": profile.candidates,
            "a3_fibula_profile_window_rc": profile.window_rc,
            "a3_fibula_profile_block_mm": profile.cell_mm,
            "a3_fibula_profile_block_px": profile.block_px,
            "a3_fibula_reference_light": np.asarray(profile.light, dtype=np.float64),
        }
    )
    for name, value in pack_fine_readings(profile.fine).items():
        arrays[f"a3_fibula_fine_{name}"] = value
    planes = list(read_at)
    arrays["a3_fibula_other_plane_slices"] = np.asarray(planes, dtype=np.int32)
    for name in OTHER_PLANE_READINGS:
        if planes:
            arrays[f"a3_fibula_other_plane_{name}"] = np.stack(
                [read_at[z][1][f"b1_{name}"] for z in planes]
            )
    record["fibula_profile_retained"] = {
        "outcome": outcome,
        "pointed_slices": [int(z) for z in pointed],
        "lens_read_slices": [int(z) for z in planes],
        "note": "no fibula named: the measured profile, finer readings and pointed planes' lens readings are kept here and read by nothing",
    }
    handed("fibula", ("other_planes",))


def find_fibula(
    series: Series,
    record: dict,
    arrays: dict[str, np.ndarray],
    stack: SquintStack,
) -> FibulaFound | str:
    """The fibula named on its main slice, from the middle slice's tibia, as a `FibulaFound` with its
    places in the scanner's millimetres where front to back lies in that slice's plane, so its
    front edge can be read (what the LCL's slice is found from, one leg, one set of objects); or why
    it was not named.

    The middle slice is the bootstrap, as ever: its tibia gives the tibia's light, its top and its
    middle. The fibula's corridor is then read through the whole depth of the series cheaply
    (`fibula_profile`: the kept squint's tiles, and a finer reading of the corridor's native
    window where the tiles cannot exclude it), never the lens. The lens (`read_part_slice`) and the
    established rule (`fibula_on_slice`, the fibula's description: the region that looks like the
    tibia, well below its top and behind its middle, apart from the tibia and whole) run only on the
    planes the profile points to: the slice or slices where each run of support reaches its maximum,
    every tie kept, and a slice beside such a maximum where the corridor window cut a body, whose
    whole the full slice can tell (`confirmations`). The profile points only where the tibia can be
    told from the bone beside it, which is the established rule's own reference, so the rule is
    never run on a plane whose reference it cannot read. It is named on the one of them where its
    region is largest (`main_slice`). The profile's support, with its ends in the scanner's millimetres, the
    head's continuation outward from that slice, and what is not known are kept beside it."""
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
    index = record["slice_index"]
    middle = plane_frame(series, index)
    if volume is None or isinstance(middle, str):
        return "geometry_unreadable"
    reads("naming", ("peaks",), "fibula")
    top_mm = float(middle.to_patient(np.argwhere(tibia).astype(float))[:, 2].max())
    peak = next(p for p in assigned["peaks"] if p["territory"] == assigned["tibia"])
    middle_rc = (int(peak["peak_rc"][0]), int(peak["peak_rc"][1]))
    middle_lps = middle.to_patient(np.asarray([middle_rc], dtype=float))[0]
    reads("squint_stack", ("code",), "fibula")
    if stack.code != "present":
        return f"squint_{stack.code}"
    reads("background", ("split",), "fibula")
    split = record["background_split"]
    uid = series.row.series_uid
    tibia_light = float(
        measures_of(uid, index, arrays["acquired_plane"], middle).light(tibia)
    )
    profile = fibula_profile(
        series, stack, tibia, middle_rc, tibia_light, top_mm, middle_lps, knee
    )
    reads("fibula_profile", ("status", "area_mm2"), "fibula")
    runs = positive_runs(profile.area_mm2)
    maxima = run_maxima(profile.area_mm2, runs)
    unresolved = (FIBULA_POINTER_STATUS["unreadable"], FIBULA_POINTER_STATUS["cut"])
    # A body the window cut is read whole on the full slice, which tells more. A slice the tibia
    # cannot be told on is not: the established rule reads the same tibia there, so it would name
    # whatever dark tissue lies behind it, and it is left unknown.
    confirm = confirmations(
        runs, maxima, profile.status, (FIBULA_POINTER_STATUS["cut"],)
    )
    pointed = sorted({int(z) for peaks in maxima for z in peaks} | set(confirm))
    if not pointed:
        outcome = (
            FIBULA_UNREADABLE
            if np.isin(profile.status, unresolved).any()
            else fibula_code(knee, True, False, False)
        )
        retain_fibula_profile(record, arrays, profile, pointed, {}, outcome)
        return outcome
    ledger.record("fibula.pointed_planes", planes=len(pointed))
    # The detailed reading, only where the profile points: the lens on the full slice, then the
    # established rule on its territories.
    read_at: dict[int, tuple] = {}
    for z in pointed:
        frame = plane_frame(series, z)
        if isinstance(frame, str):
            continue
        part_record, part_arrays, part_field = read_part_slice(
            series, z, volume[z], frame, split, knee, "fibula"
        )
        labels = part_arrays["b1_labels"]
        rows, cols = np.indices(labels.shape)
        places_lps = frame.to_patient(
            np.column_stack((rows.ravel(), cols.ravel())).astype(float)
        ).reshape(*labels.shape, 3)
        territory, area = fibula_on_slice(
            labels,
            np.asarray(volume[z], dtype=float),
            frame.spacing_rc[0] * frame.spacing_rc[1],
            places_lps,
            tibia,
            middle_lps,
            np.zeros(
                labels.shape, dtype=bool
            ),  # the full slice has no crop to cut a body
        )
        read_at[z] = (
            part_record,
            part_arrays,
            part_field,
            frame,
            labels,
            territory,
            area,
        )
    planes = list(read_at)
    chosen = main_slice([read_at[z][6] for z in planes])
    if chosen is None:
        outcome = fibula_code(knee, True, False, False)
        retain_fibula_profile(record, arrays, profile, pointed, read_at, outcome)
        return outcome
    main_z = planes[chosen]
    part_record, part_arrays, part_field, frame, labels, territory, area = read_at[
        main_z
    ]
    tibia_here = region_holding(labels, tibia)
    # On its main slice only the fibula is named, beside the tibia it was found against; each is
    # drawn whole as the full slice's own region. The middle slice's other objects are not named
    # here: their rules belong to the middle slice.
    objects = np.zeros(labels.shape, dtype=np.int8)
    objects[tibia_here] = OBJECT_CODES["tibia"]
    objects[labels == territory] = OBJECT_CODES["fibula"]
    part_arrays["a1_objects"] = objects
    main_assigned = part_record["assignments"]
    codes = main_assigned["codes"]
    codes["tibia"] = "carried_from_the_middle_slice"
    codes["fibula"] = "identified"
    main_assigned.update(tibia=int(labels[tibia_here][0]), fibula=int(territory))
    # Where front to back lies in the main slice's plane (its field's `in_plane`), the fibula's front
    # edge can be read, and its places in millimetres are what the LCL's slice is found from.
    reads("field", ("in_plane",), "fibula")
    mask = objects == OBJECT_CODES["fibula"]
    physical = frame.to_patient(np.argwhere(mask).astype(float))
    places = physical if part_field.in_plane[1] else None
    plane, unseen = seen_native(series, main_z, "fibula")
    support_px = projected_places(physical, frame, plane.shape) & ~unseen
    marrow = (
        float(measures_of(uid, main_z, plane, frame).light(support_px))
        if support_px.any()
        else float("nan")
    )
    resolved = tuple(
        (z, float(read_at[z][6]), int(np.count_nonzero(read_at[z][4] == read_at[z][5])))
        for z in planes
        if read_at[z][5] is not None
    )
    support, support_arrays, ambiguities = fibula_support(
        series,
        middle,
        frame,
        main_z,
        profile,
        (runs, maxima, confirm),
        planes,
        tuple(z for z in planes if read_at[z][5] is not None),
        places,
        marrow,
        knee,
    )
    # a bone's thin ends run off the picture or into the black margin the scan never filled
    around = ndi.binary_dilation(mask, structure=FOUR_NEIGHBOURS) & ~mask
    edge = bool(
        (around & unseen).any()
        or mask[0].any()
        or mask[-1].any()
        or mask[:, 0].any()
        or mask[:, -1].any()
    )
    if edge:
        ambiguities.append("section_runs_to_the_picture_edge_or_unseen_places")
    best = max(read_at[z][6] for z in planes)
    if sum(read_at[z][6] == best for z in planes) > 1:
        ambiguities.append("detailed_planes_tie_for_the_largest_region")
    part_arrays.update(support_arrays)
    part_arrays["a3_fibula_places_lps"] = physical
    part_arrays["a3_fibula_detailed_slices"] = np.asarray(planes, dtype=np.int32)
    part_arrays["a3_fibula_detailed_areas_mm2"] = np.asarray(
        [read_at[z][6] for z in planes], dtype=np.float64
    )
    part_arrays["a3_fibula_detailed_regions"] = np.stack(
        [
            read_at[z][4] == read_at[z][5]
            if read_at[z][5] is not None
            else np.zeros(labels.shape, bool)
            for z in planes
        ]
    )
    part_arrays["a3_fibula_marrow_light"] = np.asarray(marrow, dtype=np.float64)
    # Every plane the profile pointed to was read in full (the lens, the field, the rule), and the
    # selected one's readings are this record's own arrays. The others' lens readings are kept too,
    # the very arrays the lens made, stacked in the order of `a3_fibula_other_plane_slices`, with the
    # territory the rule chose on each plane (-1 where none) in the order of the detailed planes.
    others = [z for z in planes if z != main_z]
    part_arrays["a3_fibula_detailed_territories"] = np.asarray(
        [-1 if read_at[z][5] is None else int(read_at[z][5]) for z in planes],
        dtype=np.int32,
    )
    part_arrays["a3_fibula_other_plane_slices"] = np.asarray(others, dtype=np.int32)
    for name in OTHER_PLANE_READINGS:
        kept = [read_at[z][1][f"b1_{name}"] for z in others]
        part_arrays[f"a3_fibula_other_plane_{name}"] = (
            np.stack(kept)
            if kept
            else np.empty((0, *labels.shape), dtype=part_arrays[f"b1_{name}"].dtype)
        )
    handed("fibula", ("other_planes",))
    pointed_planes = []
    for row, z in enumerate(planes):
        other = others.index(z) if z in others else None
        plane_record = read_at[z][0]
        pointed_planes.append(
            {
                "slice": int(z),
                "detailed_row": row,
                "selected": z == main_z,
                "territory": None if read_at[z][5] is None else int(read_at[z][5]),
                "area_mm2": float(read_at[z][6]),
                "identified": read_at[z][5] is not None,
                # where this plane's own lens readings are: this record's `b1_*` for the selected
                # plane, else a row of each `a3_fibula_other_plane_*` stack
                "readings": {
                    "arrays": [
                        f"b1_{name}"
                        if other is None
                        else f"a3_fibula_other_plane_{name}"
                        for name in OTHER_PLANE_READINGS
                    ],
                    "row": other,
                },
                "interiors": plane_record["interiors"],
                "peaks": plane_record["assignments"]["peaks"],
            }
        )
    part_record["main_slice"] = {
        "object": "fibula",
        "selected_slice": int(main_z),
        "pointed_slices": [int(z) for z in planes],
        "confirmed_slices": [int(z) for z in confirm],
        "detailed_areas_mm2": {str(z): float(read_at[z][6]) for z in planes},
        "pointed_planes": pointed_planes,
        "support": support,
        "ambiguities": ambiguities,
        "status_codes": {
            **FIBULA_POINTER_STATUS,
            "unconfirmed_candidate": UNCONFIRMED_CANDIDATE,
        },
        "run_confirmation_codes": dict(RUN_CONFIRMATION),
    }
    handed("fibula", ("main_slice", "region", "places", "light"))
    return FibulaFound(
        part_record,
        part_arrays,
        frame,
        places,
        physical,
        marrow,
        uid,
        int(main_z),
        resolved,
    )


def fibula_twin(
    own: Measured, twin: Measured, fibula: FibulaFound
) -> tuple[dict, dict[str, np.ndarray], int, float, int] | str:
    """The fibula laid onto the same place of the other sequence (one leg, one set of objects): that
    sequence's slice through the fibula's main slice (`biceps_twin`: found by the scanner's
    millimetres, never by equal indices, and its places matched once), read for its lens and field
    only (`read_part_slice`), and the fibula laid onto its regions by the pair's one match
    (`lay_parts`, the way every part named in one sequence is laid onto the other). The twin's own
    decision stays what it was (`FIBULA_LAID_WHEN`) until the lay. Returns the twin's record and
    arrays, its slice index, the marrow's light over the fibula's places as the twin sees them (NaN
    where it sees none), and how many of the twin's pixels have no place on the native slice and
    so are left out; or why it could not be laid."""
    laid = biceps_twin(own, twin, fibula.slice_index, "fibula")
    if isinstance(laid, str):
        return laid
    light_map, index = laid
    series = twin.series
    volume = series.volume
    frame = plane_frame(series, index)
    if volume is None or isinstance(frame, str):
        return "geometry_unreadable"
    reads("background", ("split",), "fibula")
    record, arrays, _ = read_part_slice(
        series,
        index,
        volume[index],
        frame,
        twin.record["background_split"],
        twin.record["assignments"]["knee"],
        "fibula",
    )
    # on this slice the fibula is the native one's, laid; until then nothing is named
    arrays["a1_objects"] = np.zeros(arrays["acquired_plane"].shape, dtype=np.int8)
    codes = record["assignments"]["codes"]
    codes["fibula"] = FIBULA_LAID_WHEN
    record["main_slice"] = {
        "object": "fibula",
        "native_series_uid": fibula.record["series_uid"],
        "native_slice_index": int(fibula.record["slice_index"]),
    }
    placed = lay_parts(
        twin,
        (record, arrays, frame),
        (fibula.record, fibula.arrays, fibula.frame),
        ("fibula",),
        product="fibula",
    )["fibula"]
    if placed != "laid_from_its_partner":
        return placed or "abstain_no_fibula_in_the_twins_picture"
    codes["fibula"] = placed
    source = matched(
        series,
        record,
        frame,
        arrays["acquired_plane"].shape,
        fibula.record,
        fibula.frame,
        fibula.arrays["acquired_plane"],
    )
    unmapped = (
        int(np.count_nonzero(source < 0)) if isinstance(source, np.ndarray) else -1
    )
    plane, unseen = seen_native(own.series, fibula.slice_index, "fibula")
    support = projected_places(fibula.physical, fibula.frame, plane.shape) & ~unseen
    return record, arrays, index, twin_marrow_light(light_map, support), unmapped


def slab_thicknesses(series: Series) -> tuple[list[float], str | None]:
    """Each slice's thickness in millimetres, or why a series cannot say it (no stacked volume, no
    geometry, a slice without a thickness): the fact a slab, or a projection onto a slice, needs."""
    if series.volume is None:
        return [], "no_stacked_volume"
    if series.geometry is None:
        return [], "geometry_unreadable"
    thick = list(series.slice_thickness_mm)
    if not thick or any(t is None for t in thick):
        return [], "no_slice_thickness"
    return [float(t) for t in thick], None


@dataclass(frozen=True)
class AxialRead:
    """What one axial slice's own lens territories say under the fibula's places on its slab: the
    series, view and slice; the `code` (`territory_holding_most`, `tie`, `unavailable`,
    `no_territory_under_the_places` or `empty_target`); the slab's thickness, the slice's frame, how
    many of the fibula's places lie within the slab (`on_slab_points`), the other slices holding
    exactly as many (`tied_slices`, none broken silently), the mean distance of the on-slab places
    from the plane (None where there are none to measure), and how many seen target pixels they
    fall on. The readings (None where no slice was read, as for `empty_target`): the lens's labels
    and availability, the on-slab target pixels, the territory holding most of them (empty on a tie
    or where none holds any) and its label; `hits` (territory label -> seen target pixels) and
    `tied_labels` (the territories sharing the most)."""

    series_uid: str
    view: tuple[str, str, str]
    slice_index: int
    code: str
    thickness_mm: float
    frame: PlaneFrame
    on_slab_points: int
    tied_slices: tuple[int, ...]
    off_plane_mm: float | None
    target_pixels: int
    hits: dict[int, int]
    tied_labels: tuple[int, ...] = ()
    labels: np.ndarray | None = None
    available: np.ndarray | None = None
    target: np.ndarray | None = None
    region: np.ndarray | None = None
    label: int | None = None


def axial_territory(
    series: Series,
    index: int,
    frame: PlaneFrame,
    split: float,
    physical: np.ndarray,
    thickness: float,
) -> tuple[
    np.ndarray, np.ndarray, np.ndarray, np.ndarray, int | None, str, dict, tuple
]:
    """The lens territory of axial slice `index` holding most of the places of `physical` (scanner
    millimetres) that lie within its slab (`places_on_slice`; the places off the slab are not
    projected): the lens's labels and availability, the on-slab target pixels, the region, its
    label (None where none), the code, the seen target pixels each territory holds and the
    territories tied for the most. Only the lens is read (`lens_of`, once per slice and shared with
    anything else that reads that slice), never the field. Made once for the series, the slice, the
    places and the settings, so every view whose places are the same reads it once."""

    def read() -> tuple:
        plane = np.asarray(series.volume[index])
        _, reading, _ = lens_of(series, index, plane, frame, split, "fibula")
        reads("interiors", ("labels", "available"), "fibula_axial")
        labels = reading.labels
        available = np.asarray(reading.available, dtype=bool)
        target = places_on_slice(physical, frame, labels.shape, thickness)
        seen = target & available
        held = labels[seen & (labels > 0)]
        counts = np.bincount(held) if held.size else np.zeros(0, dtype=np.int64)
        hits = {int(k): int(v) for k, v in enumerate(counts) if v}
        tied = (
            tuple(int(k) for k in np.flatnonzero(counts == counts.max()))
            if held.size
            else ()
        )
        region = np.zeros(labels.shape, dtype=bool)
        label = None
        if not seen.any():
            code = "unavailable"
        elif not held.size:
            code = "no_territory_under_the_places"
        elif len(tied) > 1:
            code = "tie"
        else:
            region = region_holding(labels, seen)
            label = tied[0]
            code = "territory_holding_most"
        handed("fibula_axial", ("target", "region"))
        return (
            labels,
            available,
            handed_on(target),
            handed_on(region),
            label,
            code,
            hits,
            tied if len(tied) > 1 else (),
        )

    return once(
        "fibula_axial",
        (
            series.row.series_uid,
            index,
            digest(physical),
            repr(float(thickness)),
            repr(float(split)),
        ),
        read,
    )


def fibula_axial(other: Measured, physical: np.ndarray) -> list[AxialRead] | str:
    """The fibula's places (`physical`, scanner millimetres) read against one axial series: the
    slice the places' centre selects, of those whose slab (half its thickness about the slice's
    origin along its own normal) holds any of them (every slice at the same distance is read and
    names the others, `tied_slices`; each slice's own count is its `on_slab_points`),
    with only the places within the slab mapped onto its pixels and the lens territory holding
    most of them (`axial_territory`). No place on any slab is `empty_target` (nothing is read, and
    the slice named is the nearest to the places' middle). Why the series cannot be asked at all
    (no volume, geometry or thickness, a frame its header does not give) is the returned string,
    an unknown and never an absence. The slabs are the slices' own, so reversed or oblique stacks
    need no assumption."""
    series = other.series
    thick, why = slab_thicknesses(series)
    if why is not None:
        return why
    volume = series.volume
    if volume is None or len(thick) != len(volume):
        return "no_slice_thickness"
    frames: list[PlaneFrame] = []
    for z in range(len(volume)):
        frame = plane_frame(series, z)
        if isinstance(frame, str):
            return frame
        frames.append(frame)
    points = np.asarray(physical, dtype=np.float64)
    offsets = np.stack([np.abs((points - f.origin_lps) @ f.normal()) for f in frames])
    on = offsets <= (np.asarray(thick) / 2.0)[:, None]
    counts = on.sum(axis=1)
    uid, view = series.row.series_uid, tuple(other.record["view"])
    if int(counts.max()) == 0:
        finite = points[np.isfinite(points).all(axis=1)]
        nearest, distance = 0, None
        if finite.size:
            middle = finite.mean(axis=0)
            away = [abs(float((middle - f.origin_lps) @ f.normal())) for f in frames]
            nearest, distance = int(np.argmin(away)), float(min(away))
        return [
            AxialRead(
                uid,
                view,
                nearest,
                "empty_target",
                thick[nearest],
                frames[nearest],
                0,
                (),
                distance,
                0,
                {},
            )
        ]
    # The plane is the one the places' centre selects: of the slices whose slab holds any of the
    # places, the one nearest their centre along its own normal. (The slice holding the most places
    # is a plateau where a section is long, not a place.) Equal distances are tied, none dropped.
    finite = points[np.isfinite(points).all(axis=1)]
    middle = finite.mean(axis=0)
    centre = np.asarray(
        [abs(float((middle - f.origin_lps) @ f.normal())) for f in frames]
    )
    holding = np.flatnonzero(counts > 0)
    nearest_centre = float(centre[holding].min())
    tied_slices = tuple(
        int(z)
        for z in holding
        if np.isclose(centre[z], nearest_centre, rtol=0, atol=1e-9)
    )
    split = float(other.record["background_split"])
    out = []
    for z in tied_slices:
        labels, available, target, region, label, code, hits, tied = axial_territory(
            series, z, frames[z], split, points, thick[z]
        )
        out.append(
            AxialRead(
                uid,
                view,
                z,
                code,
                thick[z],
                frames[z],
                int(counts[z]),
                tuple(t for t in tied_slices if t != z),
                float(offsets[z][on[z]].mean()),
                int(np.count_nonzero(target & available)),
                hits,
                tied,
                labels,
                available,
                target,
                region,
                label,
            )
        )
    return out


def retain_fibula_axial(
    fibula: FibulaFound, axial: list[AxialRead]
) -> list[Observation]:
    """Keep what the axial readings measured inside the fibula's own record and arrays, and say each
    as a native reading: the source's frame (`a3_fibula_source_*`, beside the physical places
    `a3_fibula_places_lps`) and, for every slice read, one row of the `a3_fibula_axial_*` arrays,
    indexed by `a3_fibula_axial_slices`: the lens labels, availability, on-slab target pixels and
    the region, each a flat array of the slices' pixels in row order (`a3_fibula_axial_shapes` and
    `_offsets` cut row i out as `[offsets[i]:offsets[i + 1]].reshape(shapes[i])`, for axial series
    whose pictures differ in size), with each slice's origin, basis, normal, thickness and on-slab
    point count. The record's `axial_evidence` names, per reading, its series, slice, row, code and
    territory counts. Nothing reads these afterwards; the record is saved by the caller (the ledger
    lists the territory and target as produced and read by no stage, retained only)."""
    if not axial:
        return []
    arrays, record = fibula.arrays, fibula.record
    # the record already keeps the source frame's origin and basis under these names (the support's
    # own arrays); the normal is the one fact added, and nothing kept is written over
    arrays.setdefault(
        "a3_fibula_source_origin_lps",
        np.asarray(fibula.frame.origin_lps, dtype=np.float64),
    )
    arrays.setdefault(
        "a3_fibula_source_basis_lps",
        np.asarray(fibula.frame.basis_lps, dtype=np.float64),
    )
    arrays.setdefault("a3_fibula_source_normal_lps", fibula.frame.normal())
    kept = [a for a in axial if a.labels is not None]
    if kept:
        shapes = np.asarray([np.shape(a.labels) for a in kept], dtype=np.int32)
        sizes = shapes[:, 0].astype(np.int64) * shapes[:, 1]
        arrays["a3_fibula_axial_slices"] = np.asarray(
            [a.slice_index for a in kept], dtype=np.int32
        )
        arrays["a3_fibula_axial_shapes"] = shapes
        arrays["a3_fibula_axial_offsets"] = np.concatenate(([0], np.cumsum(sizes)))
        for name in ("labels", "available", "target", "region"):
            arrays[f"a3_fibula_axial_{name}"] = np.concatenate(
                [getattr(a, name).ravel() for a in kept]
            )
        arrays["a3_fibula_axial_origin_lps"] = np.stack(
            [a.frame.origin_lps for a in kept]
        )
        arrays["a3_fibula_axial_basis_lps"] = np.stack(
            [a.frame.basis_lps for a in kept]
        )
        arrays["a3_fibula_axial_normal_lps"] = np.stack(
            [a.frame.normal() for a in kept]
        )
        arrays["a3_fibula_axial_thickness_mm"] = np.asarray(
            [a.thickness_mm for a in kept], dtype=np.float64
        )
        arrays["a3_fibula_axial_on_slab_points"] = np.asarray(
            [a.on_slab_points for a in kept], dtype=np.int64
        )
    artifact = record.get("artifact")
    evidence: list[dict] = []
    out: list[Observation] = []
    row = 0
    for a in axial:
        here = None
        if a.labels is not None:
            here = row
            row += 1
        region = 0 if a.region is None else int(np.count_nonzero(a.region))
        evidence.append(
            {
                "series_uid": a.series_uid,
                "view": list(a.view),
                "slice": a.slice_index,
                "row": here,
                "code": a.code,
                "thickness_mm": a.thickness_mm,
                "on_slab_points": a.on_slab_points,
                "tied_slices": list(a.tied_slices),
                "target_pixels": a.target_pixels,
                "territory_hits": {str(k): v for k, v in sorted(a.hits.items())},
                "tied_labels": list(a.tied_labels),
                "label": a.label,
                "region_pixels": region,
            }
        )
        said = (
            "a lens territory of this axial slice under the fibula's places within its slab: "
            "a reading, not the bone's boundary; places off the slab are not projected"
        )
        if here is not None:
            # the support is a flat packed boolean array: the row's places are its slice of it,
            # and the lens territory's number is in the companion labelled array, not a selector
            said += (
                f"; row {here} is a3_fibula_axial_region[a3_fibula_axial_offsets[{here}]:"
                f"a3_fibula_axial_offsets[{here + 1}]] reshaped to a3_fibula_axial_shapes[{here}]"
            )
            if a.label is not None:
                said += (
                    f"; the territory's number ({a.label}) is the value of the same slice "
                    "of a3_fibula_axial_labels"
                )
        if a.tied_slices:
            said += f"; slices {list(a.tied_slices)} hold as many places"
        if a.tied_labels:
            said += (
                f"; territories {list(a.tied_labels)} hold as many pixels, none chosen"
            )
        out.append(
            Observation(
                "fibula",
                "native",
                "reading",
                a.series_uid,
                a.view,
                (a.slice_index,),
                a.code,
                a.target_pixels,
                a.off_plane_mm,
                "a3_fibula_axial_region"
                if here is not None
                else "a3_fibula_places_lps",
                said,
                artifact,
                here,
                None,
            )
        )
    record["axial_evidence"] = evidence
    return out


def fibula_observations(
    own: Measured,
    fibula: FibulaFound,
    partner: Measured | None,
    twin: tuple | str | None,
    measured: list[Measured],
) -> tuple[list[Observation], list[Unresolved]]:
    """What each view says of the fibula, by where the saying comes from (`knee.collapse.observations`),
    derived from the records and masks the run made and counting nothing again; and what could not be
    said, kept as an unknown with its code and never as an absence.

    Native: each plane the established rule identified it on (resolved; the selected one's places
    are `a1_objects` where it is the fibula's code, another's are one row of
    `a3_fibula_detailed_regions`), each plane the profile pointed to and the rule rejected (a reading,
    one row of `a3_fibula_other_plane_labels`), and the cheap readings of its body through depth: the
    pointer's runs, confirmed or not by the rule, and the head's outward continuation (readings: no
    boundary claimed, and the support is not the bone's section; the slices index the profile's
    own per-slice arrays). Laid: the same place of the other sequence, with the pixels of that
    picture the match has no place for left out. Projected: its places in the scanner's millimetres
    onto the slice of every other series nearest them, however far off its plane (targets: where a
    native question may be asked, never a boundary seen there); which of them lie on a slice, between
    slices or beyond the scan is each target's code. Native again, for every other axial series
    (`fibula_axial`): the slice whose slab holds most of the places, and the lens territory holding
    most of the places within that slab, kept as the `a3_fibula_axial_*` arrays of the fibula's own
    record (`retain_fibula_axial`: retained, read by no stage) and said as readings, never a
    boundary. Every observation names the artifact that holds
    its support (`record["artifact"]`, as `save` made it), and the row or label that selects its
    places in it. A transfer that failed, a partner the study does not have and a series whose
    geometry cannot place a projection are `Unresolved`, each with its code."""
    view = tuple(own.record["view"])
    uid = fibula.series_uid
    native_artifact = fibula.record.get("artifact")
    detailed = [int(z) for z in fibula.arrays.get("a3_fibula_detailed_slices", ())]
    others = [int(z) for z in fibula.arrays.get("a3_fibula_other_plane_slices", ())]
    identified = {int(z) for z, _, _ in fibula.resolved}
    out: list[Observation] = []
    for z, _, pixels in fibula.resolved:
        selected = z == fibula.slice_index
        out.append(
            Observation(
                "fibula",
                "native",
                "resolved",
                uid,
                view,
                (z,),
                "identified",
                pixels,
                0.0,
                "a1_objects" if selected else "a3_fibula_detailed_regions",
                "the section on this slice, not the whole bone",
                native_artifact,
                None if selected else detailed.index(z),
                OBJECT_CODES["fibula"] if selected else None,
            )
        )
    for z in detailed:
        if z not in identified:
            out.append(
                Observation(
                    "fibula",
                    "native",
                    "reading",
                    uid,
                    view,
                    (z,),
                    "pointed_plane_rejected_by_the_native_rule",
                    None,
                    0.0,
                    "a3_fibula_other_plane_labels",
                    "the plane was read in full and the established rule named no fibula on it",
                    native_artifact,
                    others.index(z),
                )
            )
    runs = fibula.arrays.get("a3_fibula_pointer_runs", np.empty((0, 2), dtype=np.int32))
    confirmed_run = (
        fibula.arrays.get("a3_fibula_pointer_run_confirmation", np.zeros(len(runs)))
        == RUN_CONFIRMATION["confirmed_by_the_native_rule"]
    )
    head = np.flatnonzero(
        fibula.arrays["a3_fibula_head_status"] == HEAD_SLICE_STATUS["head_still_a_disc"]
    )
    for name, slices, support, note in (
        (
            "pointer_body",
            np.asarray(
                [
                    z
                    for (a, b), ok in zip(runs, confirmed_run, strict=True)
                    if ok
                    for z in range(a, b)
                ],
                dtype=int,
            ),
            "a3_fibula_profile_area_mm2",
            (
                "a cheap marrow-like body through depth, on a run the native rule confirmed: "
                "no boundary, and not the bone's whole extent"
            ),
        ),
        (
            "pointer_body_unconfirmed",
            np.asarray(
                [
                    z
                    for (a, b), ok in zip(runs, confirmed_run, strict=True)
                    if not ok
                    for z in range(a, b)
                ],
                dtype=int,
            ),
            "a3_fibula_profile_area_mm2",
            (
                "a cheap marrow-like body through depth on a run the native rule did not "
                "confirm: a candidate, not the bone's extent"
            ),
        ),
        (
            "head_still_a_disc",
            head,
            "a3_fibula_head_area_mm2",
            (
                "the head's body walked outward from the identified slice: no boundary, and "
                "not the bone's whole extent"
            ),
        ),
    ):
        if slices.size:
            out.append(
                Observation(
                    "fibula",
                    "native",
                    "reading",
                    uid,
                    view,
                    tuple(int(z) for z in slices),
                    name,
                    None,
                    None,
                    support,
                    note,
                    native_artifact,
                )
            )
    unresolved: list[Unresolved] = []
    laid_uid = None
    if partner is None:
        unresolved.append(
            Unresolved("fibula", "laid", None, None, "none_of_the_other_sequence")
        )
    elif isinstance(twin, str):
        unresolved.append(
            Unresolved(
                "fibula",
                "laid",
                partner.series.row.series_uid,
                tuple(partner.record["view"]),
                twin,
            )
        )
    elif isinstance(twin, tuple):
        record, arrays, index, _, unmapped = twin
        laid_uid = partner.series.row.series_uid
        frame = plane_frame(partner.series, index)
        off = (
            float(
                abs((fibula.physical.mean(axis=0) - frame.origin_lps) @ frame.normal())
            )
            if not isinstance(frame, str)
            else None
        )
        out.append(
            Observation(
                "fibula",
                "laid",
                "resolved",
                laid_uid,
                tuple(partner.record["view"]),
                (index,),
                record["assignments"]["codes"]["fibula"],
                int(np.count_nonzero(arrays["a1_objects"] == OBJECT_CODES["fibula"])),
                off,
                "a1_objects",
                f"the same place of the other sequence by the pair's match; {unmapped} pixels "
                "of its picture have no place on the native slice and are left out",
                record.get("artifact"),
                None,
                OBJECT_CODES["fibula"],
            )
        )
    skip = {own.record["series_uid"], laid_uid}
    middle = fibula.physical.mean(axis=0)
    axial_series = 0
    axial_reads: list[AxialRead] = []
    for other in measured:
        series = other.series
        other_uid, other_view = series.row.series_uid, tuple(other.record["view"])
        if other_uid in skip:
            continue
        if other_view[0].lower() == "axial":
            # native evidence from this series' own territories, beside (never instead of) the
            # projected target below
            axial_series += 1
            got = fibula_axial(other, fibula.physical)
            if isinstance(got, str):
                unresolved.append(
                    Unresolved("fibula", "native", other_uid, other_view, got)
                )
            else:
                axial_reads.extend(got)
        thick, why = slab_thicknesses(series)
        if why is not None:
            unresolved.append(
                Unresolved("fibula", "projected", other_uid, other_view, why)
            )
            continue
        origins = np.asarray(
            [np.asarray(p, dtype=float) for p in series.geometry.position]
        )
        normal = other.frame.normal()
        signed = (middle - origins) @ normal
        nearest = int(np.argmin(np.abs(signed)))
        along = origins @ normal
        low = float(along.min()) - float(thick[int(np.argmin(along))]) / 2.0
        high = float(along.max()) + float(thick[int(np.argmax(along))]) / 2.0
        distance = float(abs(signed[nearest]))
        if distance <= float(thick[nearest]) / 2.0:
            where = "on_the_slice"
        elif not low <= float(middle @ normal) <= high:
            where = "beyond_the_scan"
        else:
            where = "between_slices"
        frame = plane_frame(series, nearest)
        if isinstance(frame, str):
            unresolved.append(
                Unresolved("fibula", "projected", other_uid, other_view, frame)
            )
            continue
        out.append(
            Observation(
                "fibula",
                "projected",
                "target",
                other_uid,
                other_view,
                (nearest,),
                where,
                int(
                    np.count_nonzero(
                        projected_places(
                            fibula.physical, frame, series.volume[nearest].shape
                        )
                    )
                ),
                distance,
                "a3_fibula_places_lps",
                "a location target projected from the fibula's places: where a native question may "
                "be asked, not a boundary seen on this slice",
                native_artifact,
            )
        )
    if not axial_series:
        unresolved.append(Unresolved("fibula", "native", None, None, "no_axial_series"))
    out.extend(retain_fibula_axial(fibula, axial_reads))
    return out, unresolved


# -- THE BONES: the femur's and the tibia's marrow body through depth, pointed planes, extent ----
# The carried places are thinned to a lattice of half a finer block before they are projected for
# the cheap profile, so that every block of the finer reading holds a place; the pointed planes are
# named against the carried places whole.
BONE_PLACES_STEP_MM = LIGAMENT_SMOOTH_MM / 2.0


def thinned(points_lps: np.ndarray) -> np.ndarray:
    """The places of a bone on a lattice of `BONE_PLACES_STEP_MM`: one place per cell, the cell's
    own corner, so the cheap profile projects thousands of places and not every pixel's. Places that
    are not finite are not places."""
    points = np.asarray(points_lps, dtype=np.float64).reshape(-1, 3)
    points = points[np.isfinite(points).all(axis=1)]
    if not len(points):
        return points
    cells = np.unique(np.rint(points / BONE_PLACES_STEP_MM).astype(np.int64), axis=0)
    return cells * BONE_PLACES_STEP_MM


def bone_footprint(
    series: Series,
    z: int,
    frame: PlaneFrame,
    shape: tuple[int, int],
    places: np.ndarray,
    key: str,
) -> np.ndarray:
    """The pixels of slice z that a bone's carried `places` project onto along the slice's normal
    (`projected_places`, however far off the plane): where the bone could lie there, an upper bound
    and not its section. Made once for the series, the slice and the places (`key`, their digest)."""
    return once(
        "bone_footprint",
        (series.row.series_uid, z, key),
        lambda: handed_on(projected_places(places, frame, shape)),
    )


@dataclass(frozen=True)
class BoneProfile:
    """A bone's cheap profile through depth, one entry per slice of the series in stack order: the
    pointer's status (`FIBULA_POINTER_STATUS`, the same words), the supported broad marrow-body
    area in square millimetres (0.0 measured absent, NaN not read, not readable or cut), how many
    separate pieces the body has, whether a piece was merged with the other bone's places; the
    corridor's tiles (the bone's carried places and one tile round them), those of them that could
    hold marrow-like light and those the tiles' own extrema confirm wholly in the level; the native
    window of the finer reading, its block in millimetres and pixels (-1 where none) and the finer
    readings themselves (`fine`; the reference body on each block grid is the bone's own carried
    footprint); and the marrow light everything was read against."""

    status: np.ndarray
    area_mm2: np.ndarray
    pieces: np.ndarray
    merged: np.ndarray
    corridor: np.ndarray
    could: np.ndarray
    confirmed: np.ndarray
    window_rc: np.ndarray
    cell_mm: np.ndarray
    block_px: np.ndarray
    fine: tuple[FineReading, ...]
    light: float


def bone_profile(
    series: Series,
    stack: SquintStack,
    places: np.ndarray,
    others: np.ndarray,
    light: float,
    name: str,
    own_footprint: Callable[[int, PlaneFrame, tuple[int, int]], np.ndarray]
    | None = None,
    level: tuple[float, float] = LIKE_THE_TIBIA,
) -> BoneProfile:
    """One bone's cheap profile through the series' whole depth, without the lens.

    On each slice the corridor is the tiles the bone's carried `places` project onto and one tile
    round them (`tiles_touched`, `tiles_around`); no tile of it, and the bone's places lie off the
    picture: not read. A bone whose place is a relation to another (the patella, in front of the
    femur) gives `own_footprint` (slice, frame, shape -> the pixels where it could lie there), read
    in place of the projection of `places`; every other step is the same. The tiles' extrema over every tile a finer block with a pixel in the tile can
    touch (`could_hold_level_in_reach`, as the fibula's profile asks) say where the level of the
    bone's marrow, a quarter either way of its own `light` (`LIKE_THE_TIBIA`), cannot be: none can
    and none was blind, the corridor holds no marrow body (measured absent); none can but a tile in
    reach was unseen, unreadable. Where every tile that could is wholly inside the level (its own
    minimum and maximum are) the tiles confirm, and the body is the tiles', at the tile's own
    resolution, read by `carried_bone` against the bone's own tiles. Otherwise the finer reading
    runs over the window of the tiles that could, with `BONE_MM` of context (`block_medians` at
    `LIGAMENT_SMOOTH_MM`) and `marrow_body` reads it. A light that is not positive and finite is no
    anchor: every slice of the corridor is unreadable and none is excluded. Counts of both readings
    are on the ledger (`bones.cheap_readings`, `bones.tile_confirmations`,
    `bones.tile_exclusions`)."""
    reads("squint_stack", ("minimum", "maximum", "coverage", "bounds_rc"), name)
    depth = int(stack.median.shape[0])
    tiles = stack.median.shape[1:]
    bounds = stack.bounds_rc
    shape = (int(bounds[..., 1].max()), int(bounds[..., 3].max()))
    tile_px = (bounds[..., 1] - bounds[..., 0]) * (bounds[..., 3] - bounds[..., 2])
    status = np.full(depth, FIBULA_POINTER_STATUS["not_read"], dtype=np.int8)
    area = np.full(depth, np.nan)
    pieces = np.zeros(depth, dtype=np.int32)
    merged = np.zeros(depth, dtype=bool)
    corridor = np.zeros((depth, *tiles), dtype=bool)
    could = np.zeros((depth, *tiles), dtype=bool)
    confirmed = np.zeros((depth, *tiles), dtype=bool)
    window_rc = np.full((depth, 4), -1, dtype=np.int32)
    cell_mm = np.full((depth, 2), np.nan)
    cell_px = np.full((depth, 2), -1, dtype=np.int32)
    fine: list[FineReading] = []
    reach_of: dict[tuple[int, int], Any] = {}
    low, high = level
    anchored = bool(np.isfinite(light) and light > 0)
    own_key, other_key = digest(places), digest(others)
    finely = excluded = by_tiles = 0
    for z in range(depth):
        frame = plane_frame(series, z)
        if isinstance(frame, str):
            status[z] = FIBULA_POINTER_STATUS["unreadable"]
            continue
        foot = (
            bone_footprint(series, z, frame, shape, places, own_key)
            if own_footprint is None
            else own_footprint(z, frame, shape)
        )
        if not foot.any():
            continue  # the bone's places lie off this slice's picture: nothing is said
        near = tiles_touched(foot, bounds)
        # a bone's footprint is an upper bound, so one tile of context is read round it; a
        # relation's corridor is already every tile that can hold a place of it
        corridor[z] = tiles_around(near) if own_footprint is None else near
        if not anchored:
            status[z] = FIBULA_POINTER_STATUS["unreadable"]
            continue
        block = block_pixels(frame.spacing_rc, LIGAMENT_SMOOTH_MM)
        if block not in reach_of:
            reach_of[block] = footprint_reach(bounds, block)
        lows, highs = stack.minimum[z], stack.maximum[z]
        possible, blind = could_hold_level_in_reach(
            lows, highs, low * light, high * light, reach_of[block]
        )
        could[z] = corridor[z] & possible
        inside = (
            np.isfinite(lows)
            & np.isfinite(highs)
            & (lows >= low * light)
            & (highs <= high * light)
        )
        confirmed[z] = corridor[z] & inside
        if not could[z].any():
            if (corridor[z] & blind).any():
                status[z] = FIBULA_POINTER_STATUS["unreadable"]
            else:
                status[z], area[z] = FIBULA_POINTER_STATUS["none"], 0.0
                excluded += 1
            continue
        other_foot = bone_footprint(series, z, frame, shape, others, other_key)
        if not (corridor[z] & blind).any() and (could[z] == confirmed[z]).all():
            # the tiles confirm: the body is the tiles', at the tile's own resolution
            by_tiles += 1
            other_near = tiles_touched(other_foot, bounds)
            kept = carried_bone(ndi.label(could[z])[0], near)
            body = kept & ~other_near
            merged[z] = bool((kept & other_near).any())
            pieces[z] = int(ndi.label(body)[1])
            seen_px = float(np.nansum((stack.coverage[z] * tile_px)[body]))
            total = seen_px * float(np.prod(frame.spacing_rc))
            status[z], area[z] = (
                (FIBULA_POINTER_STATUS["body"], total)
                if total > 0
                else (FIBULA_POINTER_STATUS["none"], 0.0)
            )
            cell_px[z] = stack.tile_shape_rc
            cell_mm[z] = np.asarray(stack.tile_shape_rc) * np.asarray(frame.spacing_rc)
            continue
        plane, unseen = seen_native(series, z, name)
        rows, cols = plane.shape
        spacing = np.asarray(frame.spacing_rc)
        held = bounds[could[z]]
        context = np.ceil(BONE_MM / spacing).astype(int)
        window = (
            max(0, int(held[:, 0].min()) - int(context[0])),
            min(rows, int(held[:, 1].max()) + int(context[0])),
            max(0, int(held[:, 2].min()) - int(context[1])),
            min(cols, int(held[:, 3].max()) + int(context[1])),
        )
        reading = block_medians(
            plane, unseen, frame.spacing_rc, LIGAMENT_SMOOTH_MM, window
        )
        open_edge = np.zeros(reading.median.shape, dtype=bool)
        open_edge[0, :] = window[0] > 0
        open_edge[-1, :] = window[1] < rows
        open_edge[:, 0] |= window[2] > 0
        open_edge[:, -1] |= window[3] < cols
        mine = block_holds(foot, reading)
        # a relation's corridor cuts the pieces where it ends: marrow-like blocks beyond it (the
        # femur's own marrow, in front of which the patella lies) never join a piece to the body
        median = (
            reading.median
            if own_footprint is None
            else np.where(mine, reading.median, np.nan)
        )
        got = marrow_body(
            median,
            reading.block_mm,
            light,
            level,
            mine,
            block_holds(other_foot, reading),
            open_edge,
        )
        finely += 1
        pieces[z], merged[z] = got.pieces, got.merged
        if got.cut:
            status[z] = FIBULA_POINTER_STATUS["cut"]
        elif got.area_mm2 > 0:
            status[z], area[z] = FIBULA_POINTER_STATUS["body"], got.area_mm2
        else:
            status[z], area[z] = FIBULA_POINTER_STATUS["none"], 0.0
        window_rc[z], cell_mm[z], cell_px[z] = (
            window,
            reading.block_mm,
            reading.block_px,
        )
        fine.append(
            FineReading(
                z,
                reading.window_rc,
                reading.block_px,
                reading.block_mm,
                reading.median,
                got.body,
                mine,
            )
        )
    ledger.record(f"{name}.cheap_readings", planes=finely)
    ledger.record(f"{name}.tile_confirmations", planes=by_tiles)
    ledger.record(f"{name}.tile_exclusions", planes=excluded)
    handed("bone_profile", ("status", "area_mm2"))
    # kept, not read: no stage after the profile reads the blocks or the bodies it drew
    handed("bone_profile", ("fine",))
    return BoneProfile(
        status,
        area,
        pieces,
        merged,
        corridor,
        could,
        confirmed,
        window_rc,
        cell_mm,
        cell_px,
        tuple(fine),
        float(light),
    )


@dataclass(frozen=True)
class BonePlane:
    """One plane the profile pointed to, as it was read: its `slice`, whether it is the series'
    `middle` slice (the bootstrap's own naming of the bone, `IDENTIFIED`), the `code` (an outcome of
    `knee.collapse.bones.OUTCOMES`, or `unreadable_geometry`), the lens's `labels` and `available`
    there (None for the middle slice, whose own arrays hold them, and where the frame cannot be
    read), the `region` named (the bone's whole section on the middle slice) and the `naming`."""

    slice: int
    middle: bool
    code: str
    labels: np.ndarray | None
    available: np.ndarray | None
    region: np.ndarray
    naming: Naming | None


@dataclass(frozen=True)
class BoneRead:
    """One bone in one series, as `read_bone` read it: the profile, the planes it pointed to, how
    the bone came out (`outcome`: identified, ambiguous, unresolved, unreadable, no_body_found), the
    record's description of it (`record`, plain data) and the arrays it keeps (`arrays`, named
    `a3_<bone>_*`; the lens's labels of the pointed planes are kept once for both bones by
    `keep_bone_planes`)."""

    bone: str
    profile: BoneProfile
    planes: tuple[BonePlane, ...]
    outcome: str
    record: dict
    arrays: dict[str, np.ndarray]
    sections: tuple[tuple[int, np.ndarray, PlaneFrame], ...]


def body_pixels(fine: FineReading, shape: tuple[int, int]) -> np.ndarray:
    """A finer reading's marrow body on the plane's own pixels (`shape`): each block's pixels over
    its window, nothing outside the window."""
    r0, r1, c0, c1 = fine.window_rc
    wide = np.repeat(
        np.repeat(fine.body, fine.block_px[0], axis=0), fine.block_px[1], axis=1
    )
    found = np.zeros(shape, dtype=bool)
    found[r0:r1, c0:c1] = wide[: r1 - r0, : c1 - c0]
    return found


def series_depth(
    series: Series, middle: PlaneFrame, index: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
    """A series' slice origins (empty where unsound), thicknesses (NaN where a header gives none),
    each slice's place along the middle slice's normal in the scanner's millimetres
    (`depth_offsets_mm`, whatever order and spacing the stack has; NaN where unsound), and whether
    the geometry is sound: finite origins for every slice."""
    reads("series", ("geometry", "slice_thickness_mm"), "bones")
    depth = len(series.volume) if series.volume is not None else 0
    origins = np.asarray(
        [np.asarray(p, dtype=float) for p in series.geometry.position]
        if series.geometry is not None
        else [],
        dtype=float,
    )
    thick = np.asarray(
        [np.nan if t is None else float(t) for t in series.slice_thickness_mm],
        dtype=float,
    )
    sound = bool(
        origins.ndim == 2
        and origins.shape == (depth, 3)
        and np.all(np.isfinite(origins))
        and len(thick) == depth
    )
    offsets = (
        depth_offsets_mm(origins, middle.normal(), index)
        if sound
        else np.full(depth, np.nan)
    )
    return (origins if sound else np.empty((0, 3))), thick, offsets, sound


def describe_runs(
    runs: list[tuple[int, int]],
    status: np.ndarray,
    offsets: np.ndarray,
    thick: np.ndarray,
    sound: bool,
) -> tuple[list[dict], np.ndarray, np.ndarray]:
    """The profile's runs of support as ENVELOPES over their sampled slabs, never dense occupancy:
    for each its slices, its envelope along the series' normal in the scanner's millimetres
    (`support_intervals_mm`), the sampled slabs and the gaps between them (`run_slabs_mm`,
    `slab_gaps_mm`) and what each end touches (`run_neighbours`: the scan's edge, a measured
    absence, an unread or unreadable slice). Also the ends and envelopes as arrays."""
    ends = run_neighbours(runs, status)
    spans = (
        support_intervals_mm(offsets, thick, runs)
        if sound
        else np.full((len(runs), 2), np.nan)
    )
    found = []
    for (a, b), end, (lo, hi) in zip(runs, ends, spans, strict=True):
        slabs = run_slabs_mm(offsets, thick, [(a, b)])[0] if sound else np.empty((0, 2))
        found.append(
            {
                "slices": [int(a), int(b) - 1],
                "envelope_mm": [finite_or_none(lo), finite_or_none(hi)],
                "slabs_mm": [[finite_or_none(v) for v in row] for row in slabs],
                "gaps_mm": [
                    finite_or_none(v)
                    for v in (slab_gaps_mm(slabs) if len(slabs) else [])
                ],
                "occupancy": "envelope_over_the_sampled_slabs_never_dense",
                "ends": [RUN_END_NAMES[int(e)] for e in end],
            }
        )
    return found, ends, spans


def read_bone(
    own: Measured,
    bone: str,
    places: np.ndarray,
    others: np.ndarray,
    extra_planes: Collection[int] = (),
) -> BoneRead | str:
    """One bone of one series: the cheap profile of its marrow body through the whole depth
    (`bone_profile`), the pointed planes (each run of support's maximum, every tie kept, every run
    kept, and the slice beside a maximum where the window cut the body: `positive_runs`,
    `run_maxima`, `confirmations`), and on only those planes the lens (`lens_of`, once per slice, so
    a plane another family already read is handed on) against the bone's carried places
    (`name_territory`, the established `carried_bone`); the series' middle slice is the bootstrap's
    own naming and is not read again. Its physical extent along the leg is the heights of the
    sections named (the middle slice's and every pointed plane that identified it), each end
    observed, clipped by the scan or unresolved (`section_extent`); the pointed planes' places
    along the stack's normal in the scanner's millimetres are kept. Or why the series cannot be
    read for this bone: a string code, an unknown and never an absence.

    `extra_planes` are planes the OTHER bone was pointed to: the joint lies between the two, so a
    plane that points for one is asked of both (`name_the_bones`). The lens is the one already read
    for it (`lens_of`, once per slice), and only where this bone's own profile read a marrow body
    finely there (a bone's identity needs its body: a plane without one stays unasked, not absent).

    Only a series without fat suppression is profiled (its marrow is the light the level is read
    against; a fat-suppressed twin is handed the bone by place); and only one that named the bone
    on its middle slice, whose marrow light is the anchor."""
    series, record = own.series, own.record
    uid = series.row.series_uid
    mask = own.arrays["a1_objects"] == OBJECT_CODES[bone]
    if record["assignments"][bone] is None or not mask.any():
        return "bone_not_named_on_the_middle_slice"
    if int(series.row.fat_suppression) != 0:  # the tag is stored as text
        return "fat_suppressed_not_profiled"
    reads("squint_stack", ("code",), "bones")
    if own.stack.code != "present":
        return f"squint_{own.stack.code}"
    if series.volume is None:
        return "no_stacked_volume"
    if not len(places):
        return "no_carried_places"
    index = record["slice_index"]
    light = float(
        measures_of(uid, index, own.arrays["acquired_plane"], own.frame).light(mask)
    )
    profile = once(
        "bone_profile",
        (uid, bone, digest(places), digest(others), light),
        lambda: bone_profile(
            series, own.stack, thinned(places), thinned(others), light, "bones"
        ),
    )
    reads("bone_profile", ("status", "area_mm2"), "bones")
    runs = positive_runs(profile.area_mm2)
    maxima = run_maxima(profile.area_mm2, runs)
    confirm = confirmations(
        runs, maxima, profile.status, (FIBULA_POINTER_STATUS["cut"],)
    )
    pointed = sorted({int(z) for peaks in maxima for z in peaks} | set(confirm))
    held_body = {f.index for f in profile.fine}
    pointed = sorted(set(pointed) | {int(z) for z in extra_planes if z in held_body})
    split = float(record["background_split"])
    own_key, other_key = digest(places), digest(others)
    shape = np.shape(own.arrays["acquired_plane"])
    read_planes: list[BonePlane] = []
    fine_of = {f.index: f for f in profile.fine}
    for z in pointed:
        if z == index:
            read_planes.append(BonePlane(z, True, "identified", None, None, mask, None))
            continue
        frame = plane_frame(series, z)
        if isinstance(frame, str):
            read_planes.append(
                BonePlane(
                    z,
                    False,
                    "unreadable_geometry",
                    None,
                    None,
                    np.zeros(shape, dtype=bool),
                    None,
                )
            )
            continue
        _, reading, _ = lens_of(
            series, z, np.asarray(series.volume[z]), frame, split, "bones"
        )
        reads("interiors", ("labels", "available"), "bones")
        naming = name_territory(
            reading.labels,
            reading.available,
            bone_footprint(series, z, frame, shape, places, own_key),
            bone_footprint(series, z, frame, shape, others, other_key),
            body_pixels(fine_of[z], shape) if z in fine_of else None,
        )
        read_planes.append(
            BonePlane(
                z,
                False,
                naming.code,
                reading.labels,
                np.asarray(reading.available, dtype=bool),
                naming.region,
                naming,
            )
        )
    sections: list[tuple[int, np.ndarray, PlaneFrame]] = [(index, mask, own.frame)]
    sections += [
        (p.slice, p.region, plane_frame(series, p.slice))
        for p in read_planes
        if not p.middle and p.code == IDENTIFIED
    ]
    sections = [s for s in sections if not isinstance(s[2], str)]
    if not pointed:
        outcome = (
            "unreadable"
            if np.isin(
                profile.status,
                (FIBULA_POINTER_STATUS["unreadable"], FIBULA_POINTER_STATUS["cut"]),
            ).any()
            else "no_body_found"
        )
    elif any(p.code == IDENTIFIED for p in read_planes):
        outcome = "identified"
    elif any(p.code in (AMBIGUOUS, TIE) for p in read_planes):
        outcome = "ambiguous"
    else:
        outcome = "unresolved"
    origins, thick, offsets, sound = series_depth(series, own.frame, index)
    described, ends, spans = describe_runs(runs, profile.status, offsets, thick, sound)
    named = {p.slice for p in read_planes if p.code == IDENTIFIED}
    asked = {p.slice for p in read_planes}
    rule = np.zeros(len(runs), dtype=np.int8)
    for i, ((a, b), peaks) in enumerate(zip(runs, maxima, strict=True)):
        here = sorted(
            {int(z) for z in peaks} | {int(z) for z in confirm if z in (a - 1, b)}
        )
        described[i]["planes_read_for_it"] = here
        rule[i] = (
            RUN_CONFIRMATION["confirmed_by_the_native_rule"]
            if any(z in named for z in here)
            else RUN_CONFIRMATION["rejected_by_the_native_rule"]
            if any(z in asked for z in here)
            else RUN_CONFIRMATION["not_read_natively"]
        )
        described[i]["native_rule"] = {v: k for k, v in RUN_CONFIRMATION.items()}[
            int(rule[i])
        ]
    # the extent along the leg: the heights of the sections named, each end observed, clipped or not
    # The bone's supported body is what the extent is read from: the marrow body the profile drew
    # (its finer blocks, upsampled to the plane's pixels) inside the region named; where the profile
    # kept no finer reading there (the tiles confirmed it), the region named.
    fine_at = {f.index: f for f in profile.fine}
    heights = []
    skipped = []
    for z, region, frame in sections:
        rows, cols = np.shape(region)
        if z in fine_at:
            region = region & body_pixels(fine_at[z], (rows, cols))
            if not region.any():
                skipped.append(z)
                continue
        r, c = np.indices((rows, cols))
        up = frame.to_patient(np.column_stack((r.ravel(), c.ravel())).astype(float))[
            :, 2
        ]
        available = (
            own.arrays["b1_available"]
            if z == index
            else next(p.available for p in read_planes if p.slice == z)
        )
        got = section_extent(
            region, up.reshape(rows, cols), available, float(max(frame.spacing_rc))
        )
        if got is not None:
            heights.append((z, *got))
    extent: dict[str, Any] = {
        "along": "the scanner's z, up (millimetres)",
        "sections": [
            {"slice": z, "low_mm": lo, "high_mm": hi, "low_end": le, "high_end": he}
            for z, lo, hi, le, he in heights
        ],
        "sections_without_a_body_in_the_region": skipped,
    }
    if heights:
        low = min(heights, key=lambda h: h[1])
        high = max(heights, key=lambda h: h[2])
        extent.update(
            low_mm=low[1],
            low_end=low[3],
            high_mm=high[2],
            high_end=high[4],
            note="the extent of the sections named: the bone beyond a named plane's own is not "
            "claimed, and an end that is clipped or unresolved is a bound, not the bone's end",
        )
    landmarks = {
        "femur": {
            "femur_lower_end_mm": extent.get("low_mm"),
            "end": extent.get("low_end"),
        },
        "tibia": {"tibia_top_mm": extent.get("high_mm"), "end": extent.get("high_end")},
    }[bone]
    ambiguities = []
    if profile.merged.any():
        ambiguities.append(
            "a_piece_joined_the_other_bones_places_only_its_own_blocks_count"
        )
    if (rule == RUN_CONFIRMATION["rejected_by_the_native_rule"]).any():
        ambiguities.append("a_run_the_native_rule_rejected_is_not_the_bones_extent")
    if (rule == RUN_CONFIRMATION["not_read_natively"]).any():
        ambiguities.append("a_run_not_read_natively_is_not_the_bones_extent")
    unknown = [
        int(z)
        for z in np.flatnonzero(
            np.isin(
                profile.status,
                (FIBULA_POINTER_STATUS["unreadable"], FIBULA_POINTER_STATUS["cut"]),
            )
        )
    ]
    if unknown:
        ambiguities.append("slices_the_profile_could_not_read_are_unknown_not_empty")
    if not sound:
        ambiguities.append("slice_geometry_unsound_so_no_physical_depth")
    names = {value: key for key, value in FIBULA_POINTER_STATUS.items()}
    pointed_rows = []
    for p in read_planes:
        pointed_rows.append(
            {
                "slice": p.slice,
                "middle": p.middle,
                "code": p.code,
                "labels": [] if p.naming is None else list(p.naming.labels),
                "tied_labels": [] if p.naming is None else list(p.naming.tied),
                "shared_labels": [] if p.naming is None else list(p.naming.shared),
                "territory_hits": {}
                if p.naming is None
                else {str(k): v for k, v in sorted(p.naming.hits.items())},
                "region_pixels": int(np.count_nonzero(p.region)),
                "position_mm": finite_or_none(offsets[p.slice]) if sound else None,
            }
        )
    record_part = {
        "bone": bone,
        "outcome": outcome,
        "marrow_light": finite_or_none(profile.light),
        "level_of_the_light": list(LIKE_THE_TIBIA),
        "block_mm": float(LIGAMENT_SMOOTH_MM),
        "context_mm": float(BONE_MM),
        "status_codes": dict(FIBULA_POINTER_STATUS),
        "pointer_runs": described,
        "pointer_representatives": [[int(z) for z in peaks] for peaks in maxima],
        "confirmed_slices": [int(z) for z in confirm],
        "pointed_planes": pointed_rows,
        "extent": extent,
        "landmarks": landmarks,
        "unknown_slices": unknown,
        "ambiguities": ambiguities,
        "slice_status": {
            names[int(c)]: int(np.count_nonzero(profile.status == c))
            for c in np.unique(profile.status)
        },
    }
    pointed_origin = origins[pointed] if sound and pointed else np.empty((0, 3))
    arrays: dict[str, np.ndarray] = {
        f"a3_{bone}_profile_status": profile.status,
        f"a3_{bone}_profile_area_mm2": profile.area_mm2,
        f"a3_{bone}_profile_pieces": profile.pieces,
        f"a3_{bone}_profile_merged": profile.merged,
        f"a3_{bone}_profile_corridor_tiles": profile.corridor,
        f"a3_{bone}_profile_could_tiles": profile.could,
        f"a3_{bone}_profile_confirmed_tiles": profile.confirmed,
        f"a3_{bone}_profile_window_rc": profile.window_rc,
        f"a3_{bone}_profile_block_mm": profile.cell_mm,
        f"a3_{bone}_profile_block_px": profile.block_px,
        f"a3_{bone}_reference_light": np.asarray(profile.light, dtype=np.float64),
        f"a3_{bone}_pointer_runs": np.asarray(runs, dtype=np.int32).reshape(-1, 2),
        f"a3_{bone}_pointer_run_ends": ends.astype(np.int32),
        f"a3_{bone}_pointer_run_envelope_mm": spans,
        f"a3_{bone}_pointer_run_native_rule": rule,
        f"a3_{bone}_depth_offsets_mm": offsets,
        f"a3_{bone}_slice_thickness_mm": thick,
        f"a3_{bone}_pointed_slices": np.asarray(pointed, dtype=np.int32),
        f"a3_{bone}_pointed_origin_lps": pointed_origin,
        f"a3_{bone}_pointed_position_mm": offsets[pointed]
        if sound and pointed
        else np.empty(0),
        f"a3_{bone}_pointed_along_normal_mm": (pointed_origin @ own.frame.normal())
        if len(pointed_origin)
        else np.empty(0),
        f"a3_{bone}_leg_extent_mm": np.asarray(
            [extent.get("low_mm", np.nan), extent.get("high_mm", np.nan)],
            dtype=np.float64,
        ),
        f"a3_{bone}_source_normal_lps": own.frame.normal(),
    }
    for name, value in pack_fine_readings(profile.fine).items():
        arrays[
            f"a3_{bone}_fine_{'carried_footprint' if name == 'tibia_reference' else name}"
        ] = value
    handed("bones", ("pointed", "sections", "extent", "landmarks"))
    return BoneRead(
        bone, profile, tuple(read_planes), outcome, record_part, arrays, tuple(sections)
    )


def keep_bone_planes(own: Measured, bones: dict[str, BoneRead]) -> None:
    """Keep what the pointed planes read inside the series' own middle arrays: for both bones, the
    lens's labels and availability of every pointed plane but the middle slice (which holds its
    own), once per plane whichever bone pointed to it (`a3_bone_plane_{slices,labels,available}`,
    stacked in slice order), and for each bone its pointed planes (`a3_<bone>_plane_slices`), the
    region named on each (`_region`, stacked; empty where nothing was named), the outcome of each
    (`_outcome`, an index into `OUTCOMES`, -1 where the geometry was unreadable) and the row of the
    shared stack holding its lens (`_lens_row`, -1 where none). The primary plane's mask is the
    middle slice's `a1_objects` and is never copied. Saving is not reading: nothing reads these."""
    shape = np.shape(own.arrays["acquired_plane"])
    lens: dict[int, BonePlane] = {}
    for read in bones.values():
        for p in read.planes:
            if not p.middle and p.labels is not None:
                lens.setdefault(p.slice, p)
    order = sorted(lens)
    own.arrays["a3_bone_plane_slices"] = np.asarray(order, dtype=np.int32)
    for name, pick in (
        ("labels", lambda p: p.labels),
        ("available", lambda p: p.available),
    ):
        own.arrays[f"a3_bone_plane_{name}"] = (
            np.stack([pick(lens[z]) for z in order])
            if order
            else np.empty((0, *shape), dtype=np.int32 if name == "labels" else bool)
        )
    for bone, read in bones.items():
        mine = [p for p in read.planes if not p.middle]
        own.arrays[f"a3_{bone}_plane_slices"] = np.asarray(
            [p.slice for p in mine], dtype=np.int32
        )
        own.arrays[f"a3_{bone}_plane_region"] = (
            np.stack([p.region for p in mine])
            if mine
            else np.empty((0, *shape), dtype=bool)
        )
        own.arrays[f"a3_{bone}_plane_outcome"] = np.asarray(
            [OUTCOMES.index(p.code) if p.code in OUTCOMES else -1 for p in mine],
            dtype=np.int8,
        )
        own.arrays[f"a3_{bone}_plane_lens_row"] = np.asarray(
            [order.index(p.slice) if p.slice in lens else -1 for p in mine],
            dtype=np.int32,
        )
        own.arrays.update(read.arrays)
    handed("bones", ("planes",))


def lay_bone_sections(
    own: Measured, twin: Measured, read: BoneRead
) -> list[tuple[int, int | None, str, np.ndarray | None, float | None]]:
    """Each section of the bone named in `own` laid onto the same place of the twin: the twin's
    slice through the section's plane (by the scanner's millimetres, never equal indices:
    `slice_through`), the pair's one match of places (`matched`, shared with every other part laid
    across) and the section's region carried onto the twin's pixels (`laid_by`), the places the
    match cannot map left out. Returns (native slice, twin slice or None, code, laid mask or None,
    distance of the section's places from the twin's plane or None); the code is
    `laid_from_its_partner` or why not, and is never an absence."""
    series, other = own.series, twin.series
    out: list[tuple[int, int | None, str, np.ndarray | None, float | None]] = []
    known = [] if other.geometry is None else list(other.slice_thickness_mm)
    for z, region, frame in read.sections:
        if other.geometry is None or other.volume is None:
            out.append((z, None, "geometry_unreadable", None, None))
            continue
        if not known or any(t is None for t in known):
            out.append((z, None, "no_slice_thickness", None, None))
            continue
        origins = np.asarray(
            [np.asarray(p, dtype=float) for p in other.geometry.position]
        )
        index = slice_through(
            frame.origin_lps, origins, twin.frame.normal(), [float(t) for t in known]
        )
        if index is None:
            out.append((z, None, "twin_has_no_slice_at_this_place", None, None))
            continue
        twin_frame = plane_frame(other, index)
        if isinstance(twin_frame, str):
            out.append((z, index, twin_frame, None, None))
            continue
        source = matched(
            other,
            {"series_uid": other.row.series_uid, "slice_index": index},
            twin_frame,
            np.shape(other.volume[index]),
            {"series_uid": series.row.series_uid, "slice_index": z},
            frame,
            np.asarray(series.volume[z]),
        )
        if isinstance(source, str):
            out.append((z, index, source, None, None))
            continue
        laid = (source >= 0) & laid_by(region, source) & finite_of(other)[index]
        places = frame.to_patient(np.argwhere(region).astype(float))
        off = float(
            abs((places.mean(axis=0) - twin_frame.origin_lps) @ twin_frame.normal())
        )
        if not laid.any():
            out.append(
                (z, index, "nothing_of_the_section_lands_on_the_twin", None, off)
            )
            continue
        out.append((z, index, "laid_from_its_partner", laid, off))
    return out


def bone_target(
    places: np.ndarray, other: Measured
) -> tuple[int, str, float, int] | str:
    """Where a bone's `places` (scanner millimetres) project onto another series: its nearest slice
    along that series' own normal, whether they lie on it, between slices or beyond the scan, how
    far off its plane, and how many pixels they project onto; or why the series cannot say
    (`slab_thicknesses`, an unreadable frame). A location, never a boundary."""
    series = other.series
    thick, why = slab_thicknesses(series)
    if why is not None:
        return why
    origins = np.asarray([np.asarray(p, dtype=float) for p in series.geometry.position])
    normal = other.frame.normal()
    middle = places.mean(axis=0)
    signed = (middle - origins) @ normal
    nearest = int(np.argmin(np.abs(signed)))
    along = origins @ normal
    low = float(along.min()) - float(thick[int(np.argmin(along))]) / 2.0
    high = float(along.max()) + float(thick[int(np.argmax(along))]) / 2.0
    distance = float(abs(signed[nearest]))
    if distance <= float(thick[nearest]) / 2.0:
        where = "on_the_slice"
    elif not low <= float(middle @ normal) <= high:
        where = "beyond_the_scan"
    else:
        where = "between_slices"
    frame = plane_frame(series, nearest)
    if isinstance(frame, str):
        return frame
    count = int(
        np.count_nonzero(
            projected_places(places, frame, np.shape(series.volume[nearest]))
        )
    )
    return nearest, where, distance, count


def name_the_bones(
    measured: list[Measured],
    partners: list[Measured | None],
    leg: Leg | None,
    study_uid: str,
) -> None:
    """The femur and the tibia through the stacks (`read_bone`) of every series that names them on
    its middle slice without fat suppression, and what each view says of them, kept in the series'
    own middle records and arrays (saved by the caller), never a record of its own.

    Native: the middle slice (the accepted bootstrap, `a1_objects`, resolved), each pointed plane
    the carried places named a territory on (resolved; one row of `a3_<bone>_plane_region`), each
    pointed plane that did not (a reading with its code, one row of the shared
    `a3_bone_plane_labels`) and the profile's support through depth (readings; the slices index
    `a3_<bone>_profile_area_mm2`). Laid: every named section onto the same place of the other
    sequence (`lay_bone_sections`, stacked in the twin's `a3_<bone>_laid_region`). Projected: the
    largest named section's places onto the slice of every other series nearest them (targets,
    never a boundary). What could not be said is an `Unresolved` with its code; a series whose
    middle slice does not name the bone, a fat-suppressed series, and a study with no partner are
    named, never skipped. Each series' record gets `bones` (outcome and extent per bone),
    `observations`, `observations_by_provenance` and `observations_unresolved`. The extent and
    landmarks (the femur's lower end, the tibia's top, each pointed plane's place along the stack's
    normal) are produced and no stage reads them: the existing consumers (the fibula's corridor, the
    carried leg) read the middle slice's bones and are not changed by them."""
    carried = leg if leg is not None else leg_of(measured)
    places = {"femur": carried.femur_lps, "tibia": carried.tibia_lps}
    results = []
    for own in measured:
        read = {
            bone: read_bone(own, bone, places[bone], places[other])
            for bone, other in (("femur", "tibia"), ("tibia", "femur"))
        }
        # the joint lies between them: a plane that pointed for one bone is asked of the other too,
        # on the lens already read for it and its own profile's marrow body (the profile is the
        # same once-made value)
        pointed_for = {
            b: {p.slice for p in r.planes}
            for b, r in read.items()
            if isinstance(r, BoneRead)
        }
        for bone, other in (("femur", "tibia"), ("tibia", "femur")):
            if bone in pointed_for and other in pointed_for:
                more = pointed_for[other] - pointed_for[bone]
                if more:
                    read[bone] = read_bone(
                        own, bone, places[bone], places[other], extra_planes=more
                    )
        for r in read.values():
            if isinstance(r, BoneRead):
                ledger.record("bones.pointed_planes", planes=len(r.planes))
        results.append(read)
    said: list[tuple[list[Observation], list[Unresolved]]] = [
        ([], []) for _ in measured
    ]
    for i, own in enumerate(measured):
        uid, view = own.record["series_uid"], tuple(own.record["view"])
        artifact = str(artifact_of(study_uid, own.record))
        here, missing = said[i]
        found = {b: r for b, r in results[i].items() if isinstance(r, BoneRead)}
        if found:
            keep_bone_planes(own, found)
        own.record["bones"] = {
            "outcomes": list(OUTCOMES),
            "codes": {
                b: (r.outcome if isinstance(r, BoneRead) else r)
                for b, r in results[i].items()
            },
            **{b: r.record for b, r in found.items()},
        }
        partner = partners[i]
        at = (
            None
            if partner is None
            else next(j for j, m in enumerate(measured) if m is partner)
        )
        skip = {uid} | (
            {partner.record["series_uid"]} if partner is not None else set()
        )
        for bone, read in results[i].items():
            if isinstance(read, str):
                missing.append(Unresolved(bone, "native", uid, view, read))
                continue
            index = own.record["slice_index"]
            rows = [p for p in read.planes if not p.middle]
            for p in read.planes:
                if p.middle:
                    here.append(
                        Observation(
                            bone,
                            "native",
                            "resolved",
                            uid,
                            view,
                            (index,),
                            IDENTIFIED,
                            int(np.count_nonzero(p.region)),
                            0.0,
                            "a1_objects",
                            "the middle slice's own naming (the bootstrap), the section on this slice, not the whole bone",
                            artifact,
                            None,
                            OBJECT_CODES[bone],
                        )
                    )
            for row, p in enumerate(rows):
                if p.code == IDENTIFIED:
                    here.append(
                        Observation(
                            bone,
                            "native",
                            "resolved",
                            uid,
                            view,
                            (p.slice,),
                            IDENTIFIED,
                            int(np.count_nonzero(p.region)),
                            0.0,
                            f"a3_{bone}_plane_region",
                            "the carried places name these lens territories here: the section on this plane, not the whole bone",
                            artifact,
                            row,
                            None,
                        )
                    )
                else:
                    held = None if p.naming is None else p.naming.labels
                    here.append(
                        Observation(
                            bone,
                            "native",
                            "reading",
                            uid,
                            view,
                            (p.slice,),
                            p.code,
                            None,
                            0.0,
                            "a3_bone_plane_labels",
                            "the plane was pointed to and read in full; no territory is named the bone here",
                            artifact,
                            int(own.arrays[f"a3_{bone}_plane_lens_row"][row])
                            if p.labels is not None
                            else None,
                            held[0] if held and len(held) == 1 else None,
                        )
                    )
            runs = read.arrays[f"a3_{bone}_pointer_runs"]
            rule = read.arrays[f"a3_{bone}_pointer_run_native_rule"]
            for name, wanted in (
                ("pointer_body", True),
                ("pointer_body_unconfirmed", False),
            ):
                slices = tuple(
                    int(z)
                    for (a, b), code in zip(runs, rule, strict=True)
                    if (code == RUN_CONFIRMATION["confirmed_by_the_native_rule"])
                    == wanted
                    for z in range(a, b)
                )
                if slices:
                    here.append(
                        Observation(
                            bone,
                            "native",
                            "reading",
                            uid,
                            view,
                            slices,
                            name,
                            None,
                            None,
                            f"a3_{bone}_profile_area_mm2",
                            "a cheap marrow-body area through depth: no boundary, and not the bone's whole extent",
                            artifact,
                        )
                    )
            # laid: every named section onto the same place of the other sequence
            if partner is None or at is None:
                missing.append(
                    Unresolved(bone, "laid", None, None, "none_of_the_other_sequence")
                )
            else:
                twin_view = tuple(partner.record["view"])
                laid = lay_bone_sections(own, partner, read)
                kept = [item for item in laid if item[3] is not None]
                # a twin that is laid onto from more than one series keeps each one's rows
                # under its own name, so no row ever points into another's array
                laid_name = source_prefix(
                    f"a3_{bone}_laid", partner.arrays, own.series.row.series_uid
                )
                partner.arrays[f"{laid_name}_native_slices"] = np.asarray(
                    [k[0] for k in kept], dtype=np.int32
                )
                partner.arrays[f"{laid_name}_slices"] = np.asarray(
                    [k[1] for k in kept], dtype=np.int32
                )
                partner.arrays[f"{laid_name}_region"] = (
                    np.stack([k[3] for k in kept])
                    if kept
                    else np.empty(
                        (0, *np.shape(partner.arrays["acquired_plane"])), dtype=bool
                    )
                )
                partner_artifact = str(artifact_of(study_uid, partner.record))
                row = 0
                for z, twin_index, code, mask, off in laid:
                    if mask is None or twin_index is None:
                        missing.append(
                            Unresolved(
                                bone,
                                "laid",
                                partner.record["series_uid"],
                                twin_view,
                                code,
                            )
                        )
                        continue
                    said[at][0].append(
                        Observation(
                            bone,
                            "laid",
                            "resolved",
                            partner.record["series_uid"],
                            twin_view,
                            (twin_index,),
                            code,
                            int(np.count_nonzero(mask)),
                            off,
                            f"{laid_name}_region",
                            f"the section named on native slice {z} laid by the pair's match of places; pixels with no place on the native slice are left out",
                            partner_artifact,
                            row,
                            None,
                        )
                    )
                    row += 1
            # projected: the largest section's places, onto every other series' nearest slice
            if read.sections:
                z, region, frame = max(
                    read.sections, key=lambda s: int(np.count_nonzero(s[1]))
                )
                from_middle = z == index
                source_row = None if from_middle else [p.slice for p in rows].index(z)
                physical = frame.to_patient(np.argwhere(region).astype(float))
                for other in measured:
                    other_uid = other.record["series_uid"]
                    if other_uid in skip:
                        continue
                    other_view = tuple(other.record["view"])
                    target = bone_target(physical, other)
                    if isinstance(target, str):
                        missing.append(
                            Unresolved(bone, "projected", other_uid, other_view, target)
                        )
                        continue
                    nearest, where, distance, count = target
                    here.append(
                        Observation(
                            bone,
                            "projected",
                            "target",
                            other_uid,
                            other_view,
                            (nearest,),
                            where,
                            count,
                            distance,
                            "a1_objects" if from_middle else f"a3_{bone}_plane_region",
                            f"a location target projected from the section named on slice {z} (its places are the region the support names, in the frame of that slice): where a native question may be asked, not a boundary seen on this slice",
                            artifact,
                            source_row,
                            OBJECT_CODES[bone] if from_middle else None,
                        )
                    )
    for own, (here, missing) in zip(measured, said, strict=True):
        own.record["observations"] = observation_rows(here)
        own.record["observations_by_provenance"] = tally(here)
        own.record["observations_unresolved"] = unresolved_rows(missing)


# -- THE PATELLA: its marrow body through depth, pointed planes, and what the extensor mechanism ----
# and the fat pads read on each of them -----------------------------------------------------------
# What the patella's rule (`patella_code`) can say on a pointed plane; the index is what the saved
# outcome array holds (-1: the plane's geometry could not be read).
PATELLA_OUTCOMES = (
    "identified",
    "abstain_front_to_back_runs_through_the_plane",
    "abstain_no_femur",
    "abstain_fat_as_bright_as_marrow",
    "abstain_no_peak_in_front_of_the_femur",
    "abstain_nothing_like_the_femur_at_its_peak",
)
UNREADABLE_GEOMETRY = "unreadable_geometry"
# The tendons, and the pads the seam parts.
TENDONS = ("patellar_tendon", "quadriceps_tendon")
PAD_FIELDS = ("quadriceps_fat_pad", "prefemoral_fat_pad", "suprapatellar_recess_ridge")
# A squint tile stands for a patch this wide: its centre is in front of the femur when any of the
# tile can be, half a tile either way.
PATELLA_TILE_MARGIN_MM = SQUINT_TILE_MM / 2.0


@dataclass(frozen=True)
class PatellaPlane:
    """One plane the profile pointed to, as the patella's own rule read it: its `slice`, whether it
    is the series' `middle` slice (the bootstrap's own naming, not read again), the patella's
    `code` (`PATELLA_OUTCOMES`, or `UNREADABLE_GEOMETRY`), the `codes` of the parts the plane's
    naming made (`PLANE_PARTS`), what the carried places named of the femur and the tibia
    (`femur`, `tibia`: `knee.collapse.bones` outcomes), the lens's `labels` and `available`, the
    plane's own naming `objects` (int8, `OBJECT_CODES`: the bones, the joint, the patella, the
    fluid and the two pads beside the patella; the tendons are laid on afterwards), the
    `peak` the patella was read at and the femur's marrow `light`, and how many pixels of the
    profile's marrow body the patella holds (`body_held`, None where the profile read none here)."""

    slice: int
    middle: bool
    code: str
    codes: dict[str, str]
    femur: str
    tibia: str
    labels: np.ndarray | None
    available: np.ndarray | None
    objects: np.ndarray | None
    peak: tuple[int, int] | None
    light: float | None
    body_held: int | None


def patella_corridor(
    series: Series,
    z: int,
    frame: PlaneFrame,
    shape: tuple[int, int],
    landmarks: tuple[float, float],
) -> np.ndarray:
    """The pixels of slice z in front of the femur and no higher than `PATELLA_ABOVE_MM` above its
    lowest carried place (`in_front_of_the_femur`): where the patella can lie there, an upper bound
    and never its section. Made once for the series, the slice and the landmarks."""

    def make() -> np.ndarray:
        rows, cols = np.indices(shape)
        places = frame.to_patient(
            np.column_stack((rows.ravel(), cols.ravel())).astype(float)
        ).reshape(*shape, 3)
        return handed_on(in_front_of_the_femur(places, *landmarks))

    return once("patella_corridor", (series.row.series_uid, z, landmarks), make)


def patella_plane(
    own: Measured,
    z: int,
    femur_lps: np.ndarray,
    tibia_lps: np.ndarray,
    keys: tuple[str, str],
    body: np.ndarray | None,
    reader: str = "patella",
) -> PatellaPlane:
    """The patella's established rule, and the fat beside it, on ONE pointed plane of a
    fat-suppressed series: the lens (`lens_of`, once per slice: a plane another family already
    read is handed on) and its field (`field_of`); the femur and the tibia named by the carried
    places (`name_territory`, the established `carried_bone`); the patella by `patella_peak` and
    `patella_piece` against that femur's marrow light, as `assign_plane` reads them; then the
    joint, the joint's fluid, Hoffa's fat pad and the suprapatellar fat as it names them, so that
    the pads are the rest of the patella's territory outside every part named. Nothing here is a
    new definition, and the rest of `assign_plane` is not run. `body` is the profile's marrow
    body on this plane's pixels, kept against the piece as a second measurement."""
    series, record = own.series, own.record
    uid = series.row.series_uid
    frame = plane_frame(series, z)
    if isinstance(frame, str):
        return PatellaPlane(
            z,
            False,
            UNREADABLE_GEOMETRY,
            {},
            "",
            "",
            None,
            None,
            None,
            None,
            None,
            None,
        )
    plane = np.asarray(series.volume[z])
    _, reading, _ = lens_of(
        series, z, plane, frame, float(record["background_split"]), reader
    )
    field = field_of(series, z, plane, frame, reading)
    reads("interiors", ("labels", "available"), reader)
    reads("field", ("objects", "peaks", "leg"), reader)
    shape = plane.shape
    labels, available = reading.labels, np.asarray(reading.available, dtype=bool)
    femur_foot = bone_footprint(series, z, frame, shape, femur_lps, keys[0])
    tibia_foot = bone_footprint(series, z, frame, shape, tibia_lps, keys[1])
    femur = name_territory(labels, available, femur_foot, tibia_foot)
    tibia = name_territory(labels, available, tibia_foot, femur_foot)
    none = np.zeros(shape, dtype=bool)
    femur_places = femur.region if femur.code == IDENTIFIED else none
    tibia_places = tibia.region if tibia.code == IDENTIFIED else none
    objects = field.objects.copy()
    objects[femur_places] = OBJECT_CODES["femur"]
    objects[tibia_places] = OBJECT_CODES["tibia"]
    basis = frame.basis_lps
    spacing = np.linalg.norm(basis, axis=0)
    front_in_plane = bool(field.in_plane[1])
    outside = margin_of(uid, z, plane)
    measures = measures_of(uid, z, plane, frame)
    bones_named = bool(femur_places.any() and tibia_places.any())
    if bones_named:
        joint = (
            between_along_the_leg(femur_places, tibia_places, basis)
            & (objects == 0)
            & ~outside
        )
        objects[joint] = OBJECT_CODES["joint"]
    # the patella: the deepest peak in front of the femur, the piece as bright as its marrow
    peak = (
        patella_peak(field.peaks, femur_places, basis)
        if front_in_plane and femur_places.any()
        else None
    )
    light = float(measures.light(femur_places)) if femur_places.any() else None
    piece = none
    if peak is not None and light is not None:
        piece = patella_piece(plane, labels, peak, light, spacing) & (objects == 0)
    codes = {
        "patella": patella_code(
            front_in_plane,
            bool(femur_places.any()),
            True,
            peak is not None,
            bool(piece.any()),
        )
    }
    territory = (
        peak.territory
        if peak is not None and codes["patella"] == "identified"
        else None
    )
    if territory is not None:
        objects[piece] = OBJECT_CODES["patella"]
    # the joint's fluid: white against the bones' marrow, in the joint's recesses
    fluid_bright = int(series.row.fluid_sensitive) == 1
    white = (
        white_as_fluid(plane, objects, measures)
        if fluid_bright and bones_named
        else None
    )
    fluid = none
    if white is not None:
        fluid = fluid_in_the_recesses(
            white, objects, field.leg, outside, spacing, measures
        )
    codes["joint_fluid"] = fluid_code(fluid_bright, bones_named, bool(fluid.any()))
    objects[fluid] = OBJECT_CODES["joint_fluid"]
    # Hoffa's fat pad and the suprapatellar fat: the rest of the patella's territory beyond it
    patella_places = objects == OBJECT_CODES["patella"]
    for name, upward in (("hoffa_fat_pad", False), ("suprapatellar_fat", True)):
        pad = none
        if front_in_plane and territory is not None:
            pad = rest_of_the_patellas_territory(
                labels, territory, patella_places, objects, basis, upward, measures
            )
        codes[name] = fat_pad_code(
            front_in_plane, True, territory is not None, bool(pad.any()), upward
        )
        objects[pad] = OBJECT_CODES[name]
    held = (
        None
        if body is None
        else int(np.count_nonzero(body & (objects == OBJECT_CODES["patella"])))
    )
    handed("patella_plane", ("objects",))
    return PatellaPlane(
        z,
        False,
        codes["patella"],
        codes,
        femur.code,
        tibia.code,
        labels,
        available,
        handed_on(objects),
        None if peak is None else (int(peak.peak_rc[0]), int(peak.peak_rc[1])),
        light,
        held,
    )


@dataclass(frozen=True)
class TwinReading:
    """What the other sequence's slice through one pointed plane says beside the plane: the twin's
    `slice` (None where it has none) and the `code` (`read`, or why not: an unknown, never an
    absence); on the twin's own pixels the `objects` the plane's naming laid on (the bones, the
    patella, both pads), the dark `bands` its light reads there, the two tendons `patellar` and
    `quadriceps` (the extensor mechanism's established rule) and the `pads` laid on; their
    `tendon_codes`; `off_mm` the patella's distance from the twin's plane; and, on the plane's
    own pixels, its naming with the tendons laid on (`fs_objects`), the paired acquisitions'
    `ratio` and the seam the pads are parted about (`anterior`, `posterior`, `ridge`) with
    their `pad_code`."""

    slice: int | None
    code: str
    objects: np.ndarray | None
    bands: np.ndarray | None
    patellar: np.ndarray | None
    quadriceps: np.ndarray | None
    tendon_codes: dict[str, str]
    off_mm: float | None
    pads: tuple[np.ndarray, np.ndarray, np.ndarray] | None
    fs_objects: np.ndarray
    ratio: np.ndarray | None
    seam: tuple[np.ndarray, np.ndarray, np.ndarray] | None
    pad_code: str


def twin_reading(
    own: Measured, twin: Measured | None, plane: PatellaPlane
) -> TwinReading:
    """The extensor tendons and the two suprapatellar pads on ONE pointed plane, from the other
    sequence's slice through the same place (found by the scanner's millimetres, never equal
    indices: `slice_through`), by the established rules and the pair's matches of places
    (`matched`, once per direction and pair): the plane's bones, patella and pads laid onto the twin;
    there the dark bands (`dark_bands`) and the tendon joining the patella and the tibia
    (`extensor_tendons`: below the patella the patellar tendon, above it the quadriceps tendon),
    read once for the twin's slice and the naming laid on it; the tendons laid back onto the plane
    (where nothing holds the place but the fat beside the patella, as `lay_parts` does) and the
    seam of the paired acquisitions' ratio (`relative_signal`, `suprapatellar_pads`) in the
    suprapatellar fat that is left. No lens is read on the twin. Every failure is a code, and the
    plane's own reading is kept beside it."""
    if plane.objects is None:
        raise ValueError("a_pointed_plane_that_was_read")
    objects = np.asarray(plane.objects)

    def failed(code: str, index: int | None = None) -> TwinReading:
        return TwinReading(
            index,
            code,
            None,
            None,
            None,
            None,
            dict.fromkeys(TENDONS, code),
            None,
            None,
            objects,
            None,
            None,
            code,
        )

    if twin is None:
        return failed("none_of_the_other_sequence")
    other = twin.series
    thick, why = slab_thicknesses(other)
    if why is not None:
        return failed(why)
    frame = plane_frame(own.series, plane.slice)
    if isinstance(frame, str):
        return failed(frame)
    origins = np.asarray([np.asarray(p, dtype=float) for p in other.geometry.position])
    index = slice_through(frame.origin_lps, origins, twin.frame.normal(), thick)
    if index is None:
        return failed("twin_has_no_slice_at_this_place")
    twin_frame = plane_frame(other, index)
    if isinstance(twin_frame, str):
        return failed(twin_frame, index)
    uid, twin_uid = own.series.row.series_uid, other.row.series_uid
    here = {"series_uid": uid, "slice_index": plane.slice}
    there = {"series_uid": twin_uid, "slice_index": index}
    plane_here = np.asarray(own.series.volume[plane.slice])
    plane_there = np.asarray(other.volume[index])
    forward = matched(
        other, there, twin_frame, plane_there.shape, here, frame, plane_here
    )
    if isinstance(forward, str):
        return failed(forward, index)
    backward = matched(
        own.series, here, frame, plane_here.shape, there, twin_frame, plane_there
    )
    if isinstance(backward, str):
        return failed(backward, index)
    # the plane's naming laid on the twin, where the twin has places of it
    laid = laid_by(objects, forward)
    named = np.zeros(plane_there.shape, dtype=np.int8)
    for name in ("femur", "tibia", "patella", "hoffa_fat_pad", "suprapatellar_fat"):
        named[laid == OBJECT_CODES[name]] = OBJECT_CODES[name]
    seen = finite_of(other)[index]
    named[~seen] = 0  # a place the twin never saw holds nothing laid on it
    spacing = np.linalg.norm(twin_frame.basis_lps, axis=0)
    measures = measures_of(twin_uid, index, plane_there, twin_frame)

    def read() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        reads("series", ("volume",), "patella_tendons")
        bands = dark_bands(
            plane_there,
            named,
            spacing,
            margin_of(twin_uid, index, plane_there),
            measures,
        )
        below, above = extensor_tendons(
            bands, named, spacing, twin_frame.basis_lps, measures
        )
        handed("patella_tendons", ("bands", "region"))
        return handed_on(bands), below, above

    bands, patellar, quadriceps = once(
        "patella_tendons", (twin_uid, index, digest(named)), read
    )
    reads("patella_tendons", ("bands",), "patella_extensor_rule")
    reads("patella_tendons", ("region",), "patella_tendons_laid")
    reads("patella_plane", ("objects",), "patella_twin")
    ends = bool(
        (named == OBJECT_CODES["patella"]).any()
        and (named == OBJECT_CODES["tibia"]).any()
    )
    front = bool(own.assignment.in_plane[1])
    tendon_codes = {
        name: tendon_code(front, False, ends, bool(mask.any()), above)
        for name, mask, above in (
            ("patellar_tendon", patellar, False),
            ("quadriceps_tendon", quadriceps, True),
        )
    }
    # the tendons laid back onto the plane, where nothing holds the place but the fat pads
    fat = (OBJECT_CODES["hoffa_fat_pad"], OBJECT_CODES["suprapatellar_fat"])
    named_here = objects.copy()
    open_to_them = np.isin(named_here, (0, *fat))
    for name, mask in (
        ("patellar_tendon", patellar),
        ("quadriceps_tendon", quadriceps),
    ):
        placed = (laid_by(mask.astype(np.int8), backward) == 1) & open_to_them
        named_here[placed] = OBJECT_CODES[name]
    # the pads: the seam of the paired acquisitions' ratio inside the suprapatellar fat left
    combined = named_here == OBJECT_CODES["suprapatellar_fat"]
    ratio = None
    seam = None
    pad_code = "abstain_no_suprapatellar_fat"
    if combined.any():
        paired = laid_by(plane_there.astype(np.float64), backward)
        paired[backward < 0] = np.nan
        ratio = relative_signal(plane_here, paired)
        back_mm = measures_of(uid, plane.slice, plane_here, frame).along(1)
        anterior, posterior, ridge, pad_code = suprapatellar_pads(
            ratio, combined, frame.basis_lps, back_mm
        )
        seam = (anterior, posterior, ridge)
    # what the plane named, laid onto the twin's slice by the same match

    def onto_twin(mask: np.ndarray) -> np.ndarray:
        return (laid_by(mask.astype(np.int16), forward) == 1) & seen

    pads = (
        None
        if seam is None
        else (onto_twin(seam[0]), onto_twin(seam[1]), onto_twin(seam[2]))
    )
    places = frame.to_patient(
        np.argwhere(objects == OBJECT_CODES["patella"]).astype(float)
    )
    off = (
        float(abs((places.mean(axis=0) - twin_frame.origin_lps) @ twin_frame.normal()))
        if len(places)
        else None
    )
    return TwinReading(
        index,
        "read",
        named,
        bands,
        patellar,
        quadriceps,
        tendon_codes,
        off,
        pads,
        named_here,
        ratio,
        seam,
        pad_code,
    )


@dataclass(frozen=True)
class PatellaRead:
    """The patella in one series, as `read_patella` read it: the cheap `profile` through depth, the
    `planes` it pointed to (the middle slice's bootstrap among them where it was), the twin's reading
    beside each plane that named the patella (`twins`, aligned with the planes but the middle one;
    None where none was asked), how the bone came out (`outcome`), the record's description
    (`record`, plain data), the arrays it keeps on the series (`arrays`, `a3_patella_*`; what the
    twin keeps is `patella_twin_arrays`) and the sections named (`sections`: slice, region,
    frame), the middle slice's bootstrap among them where it names the patella."""

    profile: BoneProfile
    planes: tuple[PatellaPlane, ...]
    twins: tuple[TwinReading | None, ...]
    outcome: str
    record: dict
    arrays: dict[str, np.ndarray]
    sections: tuple[tuple[int, np.ndarray, PlaneFrame], ...]


def stack_of(items: list[np.ndarray], shape: tuple[int, int], dtype: Any) -> np.ndarray:
    """A stack of equal planes (n, R, C), empty (0, R, C) for none: one row per read plane."""
    return np.stack(items) if items else np.empty((0, *shape), dtype=dtype)


def patella_arrays(
    own: Measured, planes: list[PatellaPlane], twins: list[TwinReading | None]
) -> dict[str, np.ndarray]:
    """The planes' own readings as stacks, one row per pointed plane but the middle slice (whose
    arrays hold its own): the plane's `slices` and `outcome` (an index into `PATELLA_OUTCOMES`, -1
    where the geometry was unreadable), the lens's `labels` and `available`, its naming `objects`
    (with the tendons laid on where the twin was read), the femur's marrow `light`, the `peak_rc` the
    patella was read at and `body_held` (-1 where none), and the pads: the seam's `pad_anterior`,
    `pad_posterior` and `pad_ridge` and the paired acquisitions' `relative_signal`."""
    shape = np.shape(own.arrays["acquired_plane"])
    zero, nothing = np.zeros(shape, dtype=bool), np.full(shape, np.nan)
    arrays: dict[str, np.ndarray] = {
        "a3_patella_plane_slices": np.asarray(
            [p.slice for p in planes], dtype=np.int32
        ),
        "a3_patella_plane_outcome": np.asarray(
            [
                PATELLA_OUTCOMES.index(p.code) if p.code in PATELLA_OUTCOMES else -1
                for p in planes
            ],
            dtype=np.int8,
        ),
        "a3_patella_plane_light": np.asarray(
            [np.nan if p.light is None else p.light for p in planes], dtype=np.float64
        ),
        "a3_patella_plane_peak_rc": np.asarray(
            [(-1, -1) if p.peak is None else p.peak for p in planes], dtype=np.int32
        ).reshape(len(planes), 2),
        "a3_patella_plane_body_held": np.asarray(
            [-1 if p.body_held is None else p.body_held for p in planes], dtype=np.int32
        ),
        "a3_patella_plane_labels": stack_of(
            [
                np.zeros(shape, np.int32) if p.labels is None else p.labels
                for p in planes
            ],
            shape,
            np.int32,
        ),
        "a3_patella_plane_available": stack_of(
            [zero if p.available is None else p.available for p in planes], shape, bool
        ),
    }
    objects, ratio = [], []
    seams: list[list[np.ndarray]] = [[], [], []]
    for plane, twin in zip(planes, twins, strict=True):
        named = (
            twin.fs_objects
            if twin is not None
            else (plane.objects if plane.objects is not None else None)
        )
        objects.append(np.zeros(shape, np.int8) if named is None else np.asarray(named))
        ratio.append(nothing if twin is None or twin.ratio is None else twin.ratio)
        for held, made in zip(
            seams,
            twin.seam if twin is not None and twin.seam is not None else (zero,) * 3,
            strict=True,
        ):
            held.append(made)
    arrays["a3_patella_plane_objects"] = stack_of(objects, shape, np.int8)
    arrays["a3_patella_plane_relative_signal"] = stack_of(ratio, shape, np.float64)
    for field, held in zip(("anterior", "posterior", "ridge"), seams, strict=True):
        arrays[f"a3_patella_plane_pad_{field}"] = stack_of(held, shape, bool)
    return arrays


def patella_twin_arrays(
    twin: Measured,
    planes: list[PatellaPlane],
    twins: list[TwinReading | None],
    prefix: str,
) -> dict[str, np.ndarray]:
    """What the twin's slices through the pointed planes say, as stacks on the twin's own pixels,
    named `<prefix>_*`, one row per plane whose twin was read: the plane's slice (`from_slices`)
    and the twin's (`slices`), the plane's naming laid on (`objects`), the dark `bands`, both
    tendons and the pads laid on. (The prefix names the series that asked, so two sequences
    asking one twin never overwrite each other.)"""
    shape = np.shape(twin.arrays["acquired_plane"])
    zero = np.zeros(shape, dtype=bool)
    rows = [
        (p, t)
        for p, t in zip(planes, twins, strict=True)
        if t is not None and t.code == "read"
    ]
    arrays: dict[str, np.ndarray] = {
        f"{prefix}_from_slices": np.asarray([p.slice for p, _ in rows], dtype=np.int32),
        f"{prefix}_slices": np.asarray(
            [-1 if t.slice is None else t.slice for _, t in rows], dtype=np.int32
        ),
        f"{prefix}_objects": stack_of(
            [
                np.zeros(shape, np.int8) if t.objects is None else t.objects
                for _, t in rows
            ],
            shape,
            np.int8,
        ),
        f"{prefix}_bands": stack_of(
            [
                np.zeros(shape, np.int32) if t.bands is None else t.bands
                for _, t in rows
            ],
            shape,
            np.int32,
        ),
        f"{prefix}_patellar_tendon": stack_of(
            [zero if t.patellar is None else t.patellar for _, t in rows], shape, bool
        ),
        f"{prefix}_quadriceps_tendon": stack_of(
            [zero if t.quadriceps is None else t.quadriceps for _, t in rows],
            shape,
            bool,
        ),
    }
    for k, field in enumerate(("anterior", "posterior", "ridge")):
        arrays[f"{prefix}_pad_{field}"] = stack_of(
            [zero if t.pads is None else t.pads[k] for _, t in rows], shape, bool
        )
    return arrays


def read_patella(
    own: Measured,
    partner: Measured | None,
    femur_lps: np.ndarray,
    tibia_lps: np.ndarray,
) -> PatellaRead | str:
    """The patella of one series through the whole depth: the cheap profile of its marrow body in
    front of the femur (`bone_profile`, with the corridor of `patella_corridor` and the femur's
    light), the pointed planes (each run's maximum, every tie, every run, and the slice beside a
    maximum the window cut: `positive_runs`, `run_maxima`, `confirmations`), and on only those planes
    the established rule (`patella_plane`) and, beside each plane that names the patella, the
    extensor tendons and the pads (`twin_reading`); the middle slice is the bootstrap's own naming
    and is not read again. The extent along the leg is the heights of the sections named, each end
    observed, clipped by the scan or unresolved (`section_extent`), and the planes' places along the
    stack's normal; the patella is ONE bone, so every named plane is one more section of it. Or why
    the series cannot be read: a string code, an unknown and never an absence. The patella is
    named by its light, so only a fat-suppressed series that runs front to back in the plane and
    names the femur on its middle slice is profiled (the existing `patella_code`'s own refusals)."""
    series, record = own.series, own.record
    uid = series.row.series_uid
    index = record["slice_index"]
    objects = own.arrays["a1_objects"]
    mask = objects == OBJECT_CODES["femur"]
    refusal = patella_code(
        bool(own.assignment.in_plane[1]),
        bool(record["assignments"]["femur"] is not None and mask.any()),
        int(series.row.fat_suppression) == 1,
        True,
        True,
    )
    if refusal != "identified":
        return refusal
    reads("squint_stack", ("code",), "patella")
    if own.stack.code != "present":
        return f"squint_{own.stack.code}"
    if series.volume is None:
        return "no_stacked_volume"
    landmarks = femur_landmarks(femur_lps)
    if landmarks is None:
        return "no_carried_places"
    light = float(
        measures_of(uid, index, own.arrays["acquired_plane"], own.frame).light(mask)
    )
    profile = bone_profile(
        series,
        own.stack,
        np.empty((0, 3)),
        thinned(np.concatenate((femur_lps, tibia_lps))),
        light,
        "patella",
        lambda z, frame, shape: patella_corridor(series, z, frame, shape, landmarks),
        LIKE_THE_FEMUR,
    )
    reads("bone_profile", ("status", "area_mm2"), "patella")
    runs = positive_runs(profile.area_mm2)
    maxima = run_maxima(profile.area_mm2, runs)
    confirm = confirmations(
        runs, maxima, profile.status, (FIBULA_POINTER_STATUS["cut"],)
    )
    pointed = sorted({int(z) for peaks in maxima for z in peaks} | set(confirm))
    ledger.record("patella.pointed_planes", planes=len(pointed))
    shape = np.shape(own.arrays["acquired_plane"])
    keys = (digest(femur_lps), digest(tibia_lps))
    fine_of = {f.index: f for f in profile.fine}
    planes: list[PatellaPlane] = []
    twins: list[TwinReading | None] = []
    for z in pointed:
        if z == index:
            code = record["assignments"]["codes"].get("patella", "")
            planes.append(
                PatellaPlane(
                    z, True, code, {}, "", "", None, None, None, None, None, None
                )
            )
            continue
        got = patella_plane(
            own,
            z,
            femur_lps,
            tibia_lps,
            keys,
            body_pixels(fine_of[z], shape) if z in fine_of else None,
        )
        planes.append(got)
        twins.append(
            twin_reading(own, partner, got)
            if got.code == "identified" and got.objects is not None
            else None
        )
    # the bootstrap's own naming of the patella is a section whether or not the profile pointed to it
    sections: list[tuple[int, np.ndarray, PlaneFrame]] = []
    middle = objects == OBJECT_CODES["patella"]
    if record["assignments"]["codes"].get("patella") == "identified" and middle.any():
        sections.append((index, middle, own.frame))
    for p in planes:
        frame = plane_frame(series, p.slice)
        if isinstance(frame, str) or p.middle:
            continue
        if p.code == "identified" and p.objects is not None:
            reads("patella_plane", ("objects",), "patella")
            sections.append((p.slice, p.objects == OBJECT_CODES["patella"], frame))
    if not pointed:
        outcome = (
            "unreadable"
            if np.isin(
                profile.status,
                (FIBULA_POINTER_STATUS["unreadable"], FIBULA_POINTER_STATUS["cut"]),
            ).any()
            else "no_body_found"
        )
    elif any(p.code == "identified" for p in planes):
        outcome = "identified"
    else:
        outcome = "unresolved"
    origins, thick, offsets, sound = series_depth(series, own.frame, index)
    described, ends, spans = describe_runs(runs, profile.status, offsets, thick, sound)
    named = {p.slice for p in planes if p.code == "identified"}
    asked = {p.slice for p in planes}
    rule = np.zeros(len(runs), dtype=np.int8)
    for i, ((a, b), peaks) in enumerate(zip(runs, maxima, strict=True)):
        here = sorted(
            {int(z) for z in peaks} | {int(z) for z in confirm if z in (a - 1, b)}
        )
        described[i]["planes_read_for_it"] = here
        rule[i] = (
            RUN_CONFIRMATION["confirmed_by_the_native_rule"]
            if any(z in named for z in here)
            else RUN_CONFIRMATION["rejected_by_the_native_rule"]
            if any(z in asked for z in here)
            else RUN_CONFIRMATION["not_read_natively"]
        )
        described[i]["native_rule"] = {v: k for k, v in RUN_CONFIRMATION.items()}[
            int(rule[i])
        ]
    # the extent along the leg: the heights of every section named, each end observed or not
    heights = []
    for z, region, frame in sections:
        rows, cols = np.shape(region)
        r, c = np.indices((rows, cols))
        up = frame.to_patient(np.column_stack((r.ravel(), c.ravel())).astype(float))[
            :, 2
        ]
        available = (
            own.arrays["b1_available"]
            if z == index
            else next(p.available for p in planes if p.slice == z)
        )
        got_extent = section_extent(
            region, up.reshape(rows, cols), available, float(max(frame.spacing_rc))
        )
        if got_extent is not None:
            heights.append((z, *got_extent))
    extent: dict[str, Any] = {
        "along": "the scanner's z, up (millimetres)",
        "sections": [
            {"slice": z, "low_mm": lo, "high_mm": hi, "low_end": le, "high_end": he}
            for z, lo, hi, le, he in heights
        ],
        "lateral_positions_mm": [
            finite_or_none(offsets[z]) if sound else None for z, _, _ in sections
        ],
    }
    if heights:
        low = min(heights, key=lambda h: h[1])
        high = max(heights, key=lambda h: h[2])
        extent.update(
            lower_pole_mm=low[1],
            lower_pole_end=low[3],
            upper_pole_mm=high[2],
            upper_pole_end=high[4],
            note="the extent of the sections named: the patella beyond a named plane's own is not "
            "claimed, and an end that is clipped or unresolved is a bound, not the bone's end",
        )
    unknown = [
        int(z)
        for z in np.flatnonzero(
            np.isin(
                profile.status,
                (FIBULA_POINTER_STATUS["unreadable"], FIBULA_POINTER_STATUS["cut"]),
            )
        )
    ]
    ambiguities = []
    if (rule == RUN_CONFIRMATION["rejected_by_the_native_rule"]).any():
        ambiguities.append("a_run_the_native_rule_rejected_is_not_the_patellas_extent")
    if (rule == RUN_CONFIRMATION["not_read_natively"]).any():
        ambiguities.append("a_run_not_read_natively_is_not_the_patellas_extent")
    if unknown:
        ambiguities.append("slices_the_profile_could_not_read_are_unknown_not_empty")
    if not sound:
        ambiguities.append("slice_geometry_unsound_so_no_physical_depth")
    ambiguities.append(
        "the_corridor_is_every_place_in_front_of_the_femurs_carried_places_an_upper_bound"
    )
    rows_in = [p for p in planes if not p.middle]
    names = {value: key for key, value in FIBULA_POINTER_STATUS.items()}
    pointed_rows = []
    twin_of = {id(p): t for p, t in zip(rows_in, twins, strict=True)}
    for p in planes:
        row = {
            "slice": p.slice,
            "middle": p.middle,
            "code": p.code,
            "codes": dict(p.codes),
            "femur": p.femur,
            "tibia": p.tibia,
            "marrow_light": None if p.light is None else finite_or_none(p.light),
            "peak_rc": None if p.peak is None else list(p.peak),
            "profile_body_in_the_patella_pixels": p.body_held,
            "patella_pixels": int(
                np.count_nonzero(
                    objects == OBJECT_CODES["patella"]
                    if p.middle
                    else (p.objects == OBJECT_CODES["patella"])
                    if p.objects is not None
                    else 0
                )
            ),
            "position_mm": finite_or_none(offsets[p.slice]) if sound else None,
        }
        if not p.middle:
            twin = twin_of[id(p)]
            row["twin"] = (
                None
                if twin is None
                else {
                    "slice": twin.slice,
                    "code": twin.code,
                    "tendon_codes": dict(twin.tendon_codes),
                    "pad_code": twin.pad_code,
                    "patella_off_the_twin_plane_mm": twin.off_mm,
                }
            )
        pointed_rows.append(row)
    record_part = {
        "outcome": outcome,
        "marrow_light": finite_or_none(profile.light),
        "level_of_the_light": list(LIKE_THE_FEMUR),
        "block_mm": float(LIGAMENT_SMOOTH_MM),
        "context_mm": float(BONE_MM),
        "corridor": {
            "front_y_mm": landmarks[0],
            "femur_lowest_z_mm": landmarks[1],
            "above_the_lowest_mm": float(PATELLA_ABOVE_MM),
            "tile_margin_mm": float(PATELLA_TILE_MARGIN_MM),
            "frame": "the scanner's LPS millimetres: y toward the back, z toward the head",
        },
        "outcomes": list(PATELLA_OUTCOMES),
        "status_codes": dict(FIBULA_POINTER_STATUS),
        "pointer_runs": described,
        "pointer_representatives": [[int(z) for z in peaks] for peaks in maxima],
        "confirmed_slices": [int(z) for z in confirm],
        "pointed_planes": pointed_rows,
        "extent": extent,
        "unknown_slices": unknown,
        "ambiguities": ambiguities,
        "slice_status": {
            names[int(c)]: int(np.count_nonzero(profile.status == c))
            for c in np.unique(profile.status)
        },
    }
    pointed_origin = origins[pointed] if sound and pointed else np.empty((0, 3))
    arrays: dict[str, np.ndarray] = {
        "a3_patella_profile_status": profile.status,
        "a3_patella_profile_area_mm2": profile.area_mm2,
        "a3_patella_profile_pieces": profile.pieces,
        "a3_patella_profile_merged": profile.merged,
        "a3_patella_profile_corridor_tiles": profile.corridor,
        "a3_patella_profile_could_tiles": profile.could,
        "a3_patella_profile_confirmed_tiles": profile.confirmed,
        "a3_patella_profile_window_rc": profile.window_rc,
        "a3_patella_profile_block_mm": profile.cell_mm,
        "a3_patella_profile_block_px": profile.block_px,
        "a3_patella_reference_light": np.asarray(profile.light, dtype=np.float64),
        "a3_patella_pointer_runs": np.asarray(runs, dtype=np.int32).reshape(-1, 2),
        "a3_patella_pointer_run_ends": ends.astype(np.int32),
        "a3_patella_pointer_run_envelope_mm": spans,
        "a3_patella_pointer_run_native_rule": rule,
        "a3_patella_depth_offsets_mm": offsets,
        "a3_patella_slice_thickness_mm": thick,
        "a3_patella_pointed_slices": np.asarray(pointed, dtype=np.int32),
        "a3_patella_pointed_origin_lps": pointed_origin,
        "a3_patella_pointed_position_mm": offsets[pointed]
        if sound and pointed
        else np.empty(0),
        "a3_patella_pole_extent_mm": np.asarray(
            [extent.get("lower_pole_mm", np.nan), extent.get("upper_pole_mm", np.nan)],
            dtype=np.float64,
        ),
        "a3_patella_corridor_landmarks_lps": np.asarray(landmarks, dtype=np.float64),
        "a3_patella_source_normal_lps": own.frame.normal(),
    }
    for name, value in pack_fine_readings(profile.fine).items():
        arrays[
            f"a3_patella_fine_{'corridor' if name == 'tibia_reference' else name}"
        ] = value
    arrays.update(patella_arrays(own, rows_in, twins))
    handed("patella", ("pointed", "sections", "extent", "planes", "twins"))
    return PatellaRead(
        profile,
        tuple(planes),
        tuple(twins),
        outcome,
        record_part,
        arrays,
        tuple(sections),
    )


def source_prefix(base: str, arrays: dict[str, np.ndarray], source_uid: str) -> str:
    """The name under which a series' readings are laid onto a twin's arrays: `base` for the first
    source, and `base` with the source's FULL series uid (its exact identity, never an abbreviation)
    where the twin already holds another source's, so that a twin laid onto from several series
    keeps every source's arrays addressable and no row ever points into another's."""
    return f"{base}_{source_uid}" if f"{base}_slices" in arrays else base


def coded_label(name: str, support: str) -> int | None:
    """The label that selects `name`'s places in the array `support`, or None. A label selects only
    in an array coded by `OBJECT_CODES` (`a1_objects` and the plane stacks' `..._objects`); a
    boolean mask, such as a twin's tendon, has none and is addressed by its row alone."""
    return OBJECT_CODES[name] if support.endswith("objects") else None


def observe(
    name: str,
    provenance: str,
    kind: str,
    on: Measured,
    slices: tuple[int, ...],
    code: str,
    count: int | None,
    off_plane_mm: float | None,
    support: str,
    note: str,
    artifact: str,
    row: int | None = None,
    label: int | None = None,
) -> Observation:
    """One observation of `name` in the series `on`, its series and view read from its record."""
    return observe_in(
        on.record,
        name,
        provenance,
        kind,
        slices,
        code,
        count,
        off_plane_mm,
        support,
        note,
        artifact,
        row,
        label,
    )


def observe_in(
    record: dict,
    name: str,
    provenance: str,
    kind: str,
    slices: tuple[int, ...],
    code: str,
    count: int | None,
    off_plane_mm: float | None,
    support: str,
    note: str,
    artifact: str,
    row: int | None = None,
    label: int | None = None,
) -> Observation:
    """One observation of `name` in the series a record (a middle slice's or a part's own slice's)
    belongs to, its series and view read from the record."""
    return Observation(
        name,
        provenance,
        kind,
        record["series_uid"],
        tuple(record["view"]),
        slices,
        code,
        count,
        off_plane_mm,
        support,
        note,
        artifact,
        row,
        label,
    )


def keep_observations(
    own: Measured, here: list[Observation], missing: list[Unresolved]
) -> None:
    """Add observations to the ones a series' record already holds (`name_the_bones` writes the
    bones'), counted again by provenance: earlier rows stay as written, in their order."""
    keep_on_record(own.record, here, missing)


def keep_on_record(
    record: dict, here: list[Observation], missing: list[Unresolved]
) -> None:
    """`keep_observations` for any record: a middle slice's or a part's own slice's."""
    rows = [*record.get("observations", []), *observation_rows(here)]
    counts = dict.fromkeys(PROVENANCES, 0)
    for row in rows:
        counts[row["provenance"]] += 1
    record["observations"] = rows
    record["observations_by_provenance"] = counts
    record["observations_unresolved"] = [
        *record.get("observations_unresolved", []),
        *unresolved_rows(missing),
    ]


def retinacula_feed(
    measured: list[Measured], leg: Leg, read: PatellaRead
) -> list[dict]:
    """Whether the patella's sections across planes could feed the axial retinacula slice, as a
    READING kept beside its consumer: the centre of every section named against the centre of the
    first native identification (`Leg.patella_lps`), and for each axial series the slice through
    each. The retinacula stage reads the centre of every section (`retinacula_centre`), the
    patella's whole observed extent in place of the one plane that named it first; where no
    section was named it keeps the first identification's."""
    if not len(leg.patella_lps) or not read.sections:
        return []
    points = np.concatenate(
        [
            frame.to_patient(np.argwhere(region).astype(float))
            for _, region, frame in read.sections
        ]
    )
    used, wider = leg.patella_lps.mean(axis=0), points.mean(axis=0)
    found = []
    for other in measured:
        if other.assignment.in_plane[2] or other.series.geometry is None:
            continue
        thick, why = slab_thicknesses(other.series)
        if why is not None:
            found.append({"series_uid": other.record["series_uid"], "unreadable": why})
            continue
        position = other.series.geometry.position
        normal = other.frame.normal()
        now = slice_through(used, position, normal, thick)
        then = slice_through(wider, position, normal, thick)
        found.append(
            {
                "series_uid": other.record["series_uid"],
                "slice_from_the_centre_the_stage_reads": now,
                "slice_from_every_section": then,
                "same_slice": now == then,
            }
        )
    return [
        {
            "centre_the_stage_reads_lps": [float(v) for v in used],
            "centre_of_every_section_lps": [float(v) for v in wider],
            "shift_mm": float(np.linalg.norm(wider - used)),
            "axial": found,
            "wired": True,
        }
    ]


def name_the_patella(
    measured: list[Measured],
    partners: list[Measured | None],
    leg: Leg | None,
    study_uid: str,
) -> None:
    """The patella through the stacks (`read_patella`) of every fat-suppressed series that runs
    front to back in the plane and names the femur on its middle slice, with the extensor tendons,
    Hoffa's fat pad and the two suprapatellar pads read on the planes it names, kept in the series'
    own middle records and arrays (saved by the caller) beside the observations the bones made.

    Native: the middle slice's own naming of each part (the bootstrap), the patella on each pointed
    plane (resolved where the carried places name it, else a reading with its code), Hoffa's fat
    pad, the suprapatellar fat and the two pads (`quadriceps_fat_pad`, `prefemoral_fat_pad`) on
    each plane where the established rules read them, and the two tendons on the twin's slice
    through each plane (read there from the bands, with the plane's patella and bones laid on).
    Laid: the patella, both fat pads and the pads onto the twin's slice, and the tendons onto the
    plane. Projected: the patella and each tendon onto every other series' nearest slice (a target
    for a native question, never a boundary): on an axial series the tendons' cross-section is
    that question, which no rule yet reads, and is named unresolved. What could not be said is an
    `Unresolved` with its code, an unknown and never an absence; pads on planes the patella does
    not name are unknown, not absent. The extent and what the retinacula could read are kept and
    nothing reads them: the retinacula stage keeps its own centre."""
    carried = leg if leg is not None else leg_of(measured)
    results = [
        read_patella(own, partners[i], carried.femur_lps, carried.tibia_lps)
        for i, own in enumerate(measured)
    ]
    where = {id(m): i for i, m in enumerate(measured)}
    said: list[tuple[list[Observation], list[Unresolved]]] = [
        ([], []) for _ in measured
    ]
    for i, own in enumerate(measured):
        read = results[i]
        uid, view = own.record["series_uid"], tuple(own.record["view"])
        here, missing = said[i]
        artifact = str(artifact_of(study_uid, own.record))
        if isinstance(read, str):
            own.record["patella"] = {"outcomes": list(PATELLA_OUTCOMES), "code": read}
            missing.append(Unresolved("patella", "native", uid, view, read))
            continue
        partner = partners[i]
        at = None if partner is None else where[id(partner)]
        index = own.record["slice_index"]
        codes = own.record["assignments"]["codes"]
        rows_in = [p for p in read.planes if not p.middle]
        twins = list(read.twins)
        own.arrays.update(read.arrays)
        prefix = "a3_patella_twin"
        if partner is not None:
            prefix = source_prefix(prefix, partner.arrays, uid)
            partner.arrays.update(patella_twin_arrays(partner, rows_in, twins, prefix))
        own.record["patella"] = {
            **read.record,
            "twin_arrays_prefix": prefix if partner is not None else None,
            "retinacula_feed": retinacula_feed(measured, carried, read),
        }
        handed("patella", ("retinacula_feed",))
        got: set[str] = set()
        # the middle slice: the bootstrap's own naming of each part, as the run made it
        for name in ("patella", "hoffa_fat_pad", "suprapatellar_fat"):
            if codes.get(name) == "identified":
                got.add(name)
                here.append(
                    observe(
                        name,
                        "native",
                        "resolved",
                        own,
                        (index,),
                        "identified",
                        int(
                            np.count_nonzero(
                                own.arrays["a1_objects"] == OBJECT_CODES[name]
                            )
                        ),
                        0.0,
                        "a1_objects",
                        "the middle slice's own naming (the bootstrap): the part on this slice, not the whole",
                        artifact,
                        None,
                        OBJECT_CODES[name],
                    )
                )
        for name in PAD_FIELDS[:2]:
            if codes.get(name) == "identified":
                got.add(name)
                here.append(
                    observe(
                        name,
                        "native",
                        "resolved",
                        own,
                        (index,),
                        "identified",
                        int(np.count_nonzero(own.arrays[f"a2_{name}"])),
                        0.0,
                        f"a2_{name}",
                        "the middle slice's own naming (the bootstrap), parted about the seam of the paired acquisitions",
                        artifact,
                    )
                )
        for name in TENDONS:
            if codes.get(name) in NAMED and codes.get(name) != "identified":
                got.add(name)
                here.append(
                    observe(
                        name,
                        "laid",
                        "resolved",
                        own,
                        (index,),
                        str(codes[name]),
                        int(
                            np.count_nonzero(
                                own.arrays["a1_objects"] == OBJECT_CODES[name]
                            )
                        ),
                        None,
                        "a1_objects",
                        "longitudinal course: laid from the twin's slice of the same place by the pair's match",
                        artifact,
                        None,
                        OBJECT_CODES[name],
                    )
                )
        # the pointed planes: the rules read on each, row by row of the stacks kept
        reason: dict[str, set[str]] = {
            n: set()
            for n in (
                "patella",
                "hoffa_fat_pad",
                "suprapatellar_fat",
                *TENDONS,
                *PAD_FIELDS[:2],
            )
        }
        objects = own.arrays["a3_patella_plane_objects"]
        twin_row = 0
        patella_sections: list[tuple[int, np.ndarray, PlaneFrame, str, int | None]] = []
        if codes.get("patella") == "identified":
            middle = own.arrays["a1_objects"] == OBJECT_CODES["patella"]
            patella_sections.append((index, middle, own.frame, "a1_objects", None))
        tendon_sources: dict[
            str, list[tuple[int, np.ndarray, PlaneFrame, str, int | None, int]]
        ] = {n: [] for n in TENDONS}
        twin_artifact = (
            str(artifact_of(study_uid, partner.record)) if partner is not None else ""
        )
        for row, (p, t) in enumerate(zip(rows_in, twins, strict=True)):
            for name, why in p.codes.items():
                if name in reason:
                    reason[name].add(why)
            if p.code != "identified":
                held = None if p.labels is None else row
                here.append(
                    observe(
                        "patella",
                        "native",
                        "reading",
                        own,
                        (p.slice,),
                        p.code,
                        None,
                        0.0,
                        "a3_patella_plane_labels",
                        "the plane was pointed to and read in full; no patella is named here",
                        artifact,
                        held,
                    )
                )
                continue
            frame = plane_frame(own.series, p.slice)
            got.add("patella")
            region = objects[row] == OBJECT_CODES["patella"]
            here.append(
                observe(
                    "patella",
                    "native",
                    "resolved",
                    own,
                    (p.slice,),
                    "identified",
                    int(np.count_nonzero(region)),
                    0.0,
                    "a3_patella_plane_objects",
                    "the established rule names the patella here: the section on this plane, not the whole bone",
                    artifact,
                    row,
                    OBJECT_CODES["patella"],
                )
            )
            if not isinstance(frame, str):
                patella_sections.append(
                    (p.slice, region, frame, "a3_patella_plane_objects", row)
                )
            for name in ("hoffa_fat_pad", "suprapatellar_fat"):
                if p.codes.get(name) == "identified":
                    got.add(name)
                    here.append(
                        observe(
                            name,
                            "native",
                            "resolved",
                            own,
                            (p.slice,),
                            "identified",
                            int(np.count_nonzero(objects[row] == OBJECT_CODES[name])),
                            0.0,
                            "a3_patella_plane_objects",
                            "the rest of the patella's territory beyond it along the leg, on this plane only; the plane's pads beside the patella beyond it are unknown, not absent",
                            artifact,
                            row,
                            OBJECT_CODES[name],
                        )
                    )
            if t is None:
                continue
            for name in TENDONS:
                reason[name].add(t.tendon_codes[name])
            for name in PAD_FIELDS[:2]:
                reason[name].add(t.pad_code)
            if t.code != "read":
                continue
            for k, (name, field) in enumerate(
                zip(PAD_FIELDS[:2], ("anterior", "posterior"), strict=True)
            ):
                if t.seam is not None and t.pad_code == "identified":
                    got.add(name)
                    here.append(
                        observe(
                            name,
                            "native",
                            "resolved",
                            own,
                            (p.slice,),
                            "identified",
                            int(np.count_nonzero(t.seam[k])),
                            0.0,
                            f"a3_patella_plane_pad_{field}",
                            "the suprapatellar fat parted about the internal seam of the paired acquisitions' ratio; the seam is `a3_patella_plane_pad_ridge`, no membrane thickness",
                            artifact,
                            row,
                        )
                    )
            if partner is None or at is None or t.slice is None or t.objects is None:
                continue  # a read twin has all of them; this only narrows the types
            twin_frame = plane_frame(partner.series, t.slice)
            for name in ("patella", "hoffa_fat_pad", "suprapatellar_fat"):
                if p.codes.get(name) != "identified":
                    continue
                count = int(np.count_nonzero(t.objects == OBJECT_CODES[name]))
                if count:
                    said[at][0].append(
                        observe(
                            name,
                            "laid",
                            "resolved",
                            partner,
                            (t.slice,),
                            "laid_from_its_partner",
                            count,
                            t.off_mm,
                            f"{prefix}_objects",
                            f"the part named on native slice {p.slice} laid by the pair's match of places; places the twin never saw are left out",
                            twin_artifact,
                            twin_row,
                            OBJECT_CODES[name],
                        )
                    )
                else:
                    said[at][1].append(
                        Unresolved(
                            name,
                            "laid",
                            partner.record["series_uid"],
                            tuple(partner.record["view"]),
                            "nothing_of_the_part_lands_on_the_twin",
                        )
                    )
            if t.pads is not None:
                for name, field, mask in zip(
                    PAD_FIELDS[:2], ("anterior", "posterior"), t.pads, strict=False
                ):
                    if np.any(mask):
                        said[at][0].append(
                            observe(
                                name,
                                "laid",
                                "resolved",
                                partner,
                                (t.slice,),
                                "laid_from_its_partner",
                                int(np.count_nonzero(mask)),
                                t.off_mm,
                                f"{prefix}_pad_{field}",
                                f"the pad parted on native slice {p.slice} laid by the pair's match of places",
                                twin_artifact,
                                twin_row,
                            )
                        )
            for name, field, mask in (
                ("patellar_tendon", "patellar_tendon", t.patellar),
                ("quadriceps_tendon", "quadriceps_tendon", t.quadriceps),
            ):
                if t.tendon_codes[name] != "identified" or mask is None:
                    continue
                got.add(name)
                said[at][0].append(
                    observe(
                        name,
                        "native",
                        "resolved",
                        partner,
                        (t.slice,),
                        "identified",
                        int(np.count_nonzero(mask)),
                        0.0,
                        f"{prefix}_{field}",
                        f"longitudinal course: the dark band joining the patella and the tibia read on this slice, with the bones and the patella of native slice {p.slice} laid on; no cross-section",
                        twin_artifact,
                        twin_row,
                    )
                )
                if not isinstance(twin_frame, str):
                    tendon_sources[name].append(
                        (
                            t.slice,
                            mask,
                            twin_frame,
                            f"{prefix}_{field}",
                            twin_row,
                            int(np.count_nonzero(mask)),
                        )
                    )
                placed = int(np.count_nonzero(objects[row] == OBJECT_CODES[name]))
                if placed:
                    here.append(
                        observe(
                            name,
                            "laid",
                            "resolved",
                            own,
                            (p.slice,),
                            "laid_from_its_partner",
                            placed,
                            t.off_mm,
                            "a3_patella_plane_objects",
                            "longitudinal course: laid onto this plane by the pair's match, only where nothing but the fat beside the patella held the place",
                            artifact,
                            row,
                            OBJECT_CODES[name],
                        )
                    )
            twin_row += 1
        # the middle slice's existing tendons on the twin, a candidate source for the targets too
        if partner is not None:
            pcodes = partner.record["assignments"]["codes"]
            for name in TENDONS:
                if pcodes.get(name) == "identified":
                    got.add(name)
                    mask = partner.arrays["a1_objects"] == OBJECT_CODES[name]
                    said[at][0].append(
                        observe(
                            name,
                            "native",
                            "resolved",
                            partner,
                            (partner.record["slice_index"],),
                            "identified",
                            int(np.count_nonzero(mask)),
                            0.0,
                            "a1_objects",
                            "longitudinal course: the middle slice's own naming (the bootstrap), from the dark bands with the patella laid on from the fat-suppressed twin",
                            twin_artifact,
                            None,
                            OBJECT_CODES[name],
                        )
                    )
                    tendon_sources[name].append(
                        (
                            partner.record["slice_index"],
                            mask,
                            partner.frame,
                            "a1_objects",
                            None,
                            int(np.count_nonzero(mask)),
                        )
                    )
                else:
                    reason[name].add(str(pcodes.get(name)))
        # what no plane read is unknown: each part with no native saying names why, never absent
        for name, codes_here in reason.items():
            if name in got:
                continue
            if not codes_here:
                codes_here = {"no_plane_pointed_to_read_it"}
            on_partner = name in TENDONS and partner is not None
            who = partner if on_partner and partner is not None else own
            said[where[id(who)]][1].append(
                Unresolved(
                    name,
                    "native",
                    who.record["series_uid"],
                    tuple(who.record["view"]),
                    "|".join(sorted(codes_here)),
                )
            )
        # projected: the largest section of the patella, and of each tendon, onto every other series
        skip = {uid} | (
            {partner.record["series_uid"]} if partner is not None else set()
        )
        projections: list[
            tuple[
                str,
                tuple[int, np.ndarray, PlaneFrame, str, int | None],
                str,
                int | None,
            ]
        ] = []
        if patella_sections:
            best = max(patella_sections, key=lambda s: int(np.count_nonzero(s[1])))
            projections.append(
                (
                    "patella",
                    best,
                    artifact,
                    coded_label("patella", best[3]),
                )
            )
        for name in TENDONS:
            if tendon_sources[name]:
                best_t = max(tendon_sources[name], key=lambda s: s[5])
                projections.append(
                    (
                        name,
                        best_t[:5],
                        twin_artifact,
                        coded_label(name, best_t[3]),
                    )
                )
        for name, (
            z,
            region,
            frame,
            support,
            source_row,
        ), source_artifact, label in projections:
            physical = frame.to_patient(np.argwhere(region).astype(float))
            for other in measured:
                other_uid = other.record["series_uid"]
                if other_uid in skip:
                    continue
                other_view = tuple(other.record["view"])
                cross = name in TENDONS and not other.assignment.in_plane[2]
                if cross:
                    said[where[id(other)]][1].append(
                        Unresolved(
                            name,
                            "native",
                            other_uid,
                            other_view,
                            "cross_section_not_read_no_rule_reads_the_axial",
                        )
                    )
                target = bone_target(physical, other)
                if isinstance(target, str):
                    said[where[id(other)]][1].append(
                        Unresolved(name, "projected", other_uid, other_view, target)
                    )
                    continue
                nearest, place, distance, count = target
                said[where[id(other)]][0].append(
                    observe(
                        name,
                        "projected",
                        "target",
                        other,
                        (nearest,),
                        place,
                        count,
                        distance,
                        support,
                        f"a location target projected from {name} on slice {z} ({'where its cross-section may be asked' if cross else 'its longitudinal course'}): where a native question may be asked, not a boundary seen on this slice",
                        source_artifact,
                        source_row,
                        label,
                    )
                )
    for m, (here, missing) in zip(measured, said, strict=True):
        if here or missing:
            keep_observations(m, here, missing)


# -- THE JOINT: the sided menisci, the articular cartilage, the cruciates and the collaterals -----
# The joint is what lies between the femur and the tibia (its existing definition), asked of every
# slice from the bones' carried places; four separate quantities of its corridor
# (`knee.collapse.joint`) each point at the planes where one property is worth a native reading.
SIDED_MENISCI = ("medial_meniscus", "lateral_meniscus", "meniscus")
JOINT_PARTS = (
    *SIDED_MENISCI,
    "femoral_cartilage",
    "tibial_cartilage",
    "mcl",
    "pcl",
    "acl",
)
# Each part's existing rule, by the key of its code in a plane's codes.
JOINT_RULE = {
    "medial_meniscus": "meniscus",
    "lateral_meniscus": "meniscus",
    "meniscus": "meniscus",
    "femoral_cartilage": "cartilage",
    "tibial_cartilage": "cartilage",
    "mcl": "mcl",
    "pcl": "pcl",
    "acl": "acl",
}
JOINT_NOT_READ = FIBULA_POINTER_STATUS["not_read"]
JOINT_NONE = FIBULA_POINTER_STATUS["none"]
JOINT_BODY = FIBULA_POINTER_STATUS["body"]
JOINT_UNREADABLE = FIBULA_POINTER_STATUS["unreadable"]
HORNS = "horn_candidates"
CARTILAGE_CANDIDATES = "cartilage_candidates"


@dataclass(frozen=True)
class JointProfile:
    """The joint's cheap profile through depth, one entry per slice of the series in stack order, one
    profile per quantity (`knee.collapse.joint.QUANTITIES`, never combined): the pointer's `status`
    (`FIBULA_POINTER_STATUS`, the same words; "none" is a measured absence, "unreadable" is unknown)
    and the `area_mm2` of the 2 mm blocks of the corridor that read the quantity (0.0 measured absent,
    NaN not read or unreadable; with `unseen_blocks` it is a lower bound); the blocks of the corridor
    seen and not (`seen_blocks`, `unseen_blocks`, -1 where no finer reading was made), the corridor's
    `corridor_px` (its reach, pixels) and its tiles, and for each quantity the tiles that could hold
    its level; the native window of the finer reading, its block in millimetres and pixels, the finer
    readings themselves (`fine`; its `body` is the blocks that hold a place of the corridor's reach)
    and the level each quantity was read at (None: no usable anchor)."""

    names: tuple[str, ...]
    status: dict[str, np.ndarray]
    area_mm2: dict[str, np.ndarray]
    seen_blocks: np.ndarray
    unseen_blocks: np.ndarray
    corridor_px: np.ndarray
    corridor: np.ndarray
    could: dict[str, np.ndarray]
    window_rc: np.ndarray
    cell_mm: np.ndarray
    block_px: np.ndarray
    fine: tuple[FineReading, ...]
    level: dict[str, tuple[float, float] | None]


def joint_profile(
    series: Series,
    stack: SquintStack,
    femur_places: np.ndarray,
    tibia_places: np.ndarray,
    level: dict[str, tuple[float, float] | None],
    names: tuple[str, ...],
    own_reach: Callable[[int, PlaneFrame, tuple[int, int]], np.ndarray] | None = None,
    name: str = "joint",
    bones_unestablished: np.ndarray | None = None,
) -> JointProfile:
    """The joint's four-quantity profile through the series' whole depth, without the lens.

    A family whose compartment is a relation to parts already located (the recesses, in front of the
    femur and behind the patella) gives `own_reach` (slice, frame, shape -> the pixels where it can lie
    there), read in place of the joint's own corridor; every other step is the same, under the ledger
    name `name`. `bones_unestablished` (one flag per slice) marks the slices where the bones' family
    did not natively identify both bones (`bones_identified_at`): the joint is what lies between
    them, so no corridor is read there and no lens is asked for it (counted
    `joint.slices_without_both_bones_identified`; nothing is said of such a slice: it is unknown,
    not a joint-free one).

    On each slice the corridor is where the joint can lie there (`joint_reach`: the carried femur's
    and tibia's places projected onto the slice, `bone_footprint`, the places between them along the
    leg and their reach); no place of it on the slice, nothing is said (not read). The squint's tile
    extrema over every tile a 2 mm block with a place of the corridor can touch (`could_hold_level_in_reach`,
    as the bones' and the fibula's profiles ask) say, per quantity, where its level cannot be: none can
    and no unseen tile is in reach, a measured absence (`none`); none can but one is, unreadable. Where
    some can, ONE finer reading of the window of the tiles that could (`block_medians` at
    `LIGAMENT_SMOOTH_MM`) gives every wanted quantity its area over the blocks that hold a place of
    the corridor (`block_support`): a positive area is `body` (a lower bound where blocks were
    unseen), zero with every block seen is `none`, zero with an unseen block is unreadable. A level
    with no usable anchor (`level` None) leaves every slice of the corridor unreadable for that
    quantity and excludes nothing. Counts are on the ledger (`joint.cheap_readings`,
    `joint.tile_exclusions`)."""
    reads("squint_stack", ("minimum", "maximum", "bounds_rc"), name)
    depth = int(stack.median.shape[0])
    tiles = stack.median.shape[1:]
    bounds = stack.bounds_rc
    shape = (int(bounds[..., 1].max()), int(bounds[..., 3].max()))
    status = {q: np.full(depth, JOINT_NOT_READ, dtype=np.int8) for q in names}
    area = {q: np.full(depth, np.nan) for q in names}
    seen_blocks = np.full(depth, -1, dtype=np.int32)
    unseen_blocks = np.full(depth, -1, dtype=np.int32)
    corridor_px = np.zeros(depth, dtype=np.int32)
    corridor = np.zeros((depth, *tiles), dtype=bool)
    could = {q: np.zeros((depth, *tiles), dtype=bool) for q in names}
    window_rc = np.full((depth, 4), -1, dtype=np.int32)
    cell_mm = np.full((depth, 2), np.nan)
    cell_px = np.full((depth, 2), -1, dtype=np.int32)
    fine: list[FineReading] = []
    reach_of: dict[tuple[int, int], Any] = {}
    femur_key, tibia_key = digest(femur_places), digest(tibia_places)
    finely = excluded = lacking = 0
    for z in range(depth):
        if bones_unestablished is not None and bool(bones_unestablished[z]):
            lacking += 1
            continue
        frame = plane_frame(series, z)
        if isinstance(frame, str):
            for q in names:
                status[q][z] = JOINT_UNREADABLE
            continue
        if own_reach is not None:
            reach = own_reach(z, frame, shape)
        else:
            _, reach = joint_reach(
                bone_footprint(series, z, frame, shape, femur_places, femur_key),
                bone_footprint(series, z, frame, shape, tibia_places, tibia_key),
                frame.basis_lps,
                np.asarray(frame.spacing_rc),
            )
        if not reach.any():
            continue  # the bones' places leave no joint on this slice: nothing is said
        corridor_px[z] = int(np.count_nonzero(reach))
        near = tiles_touched(reach, bounds)
        corridor[z] = near
        block = block_pixels(frame.spacing_rc, LIGAMENT_SMOOTH_MM)
        if block not in reach_of:
            reach_of[block] = footprint_reach(bounds, block)
        lows, highs = stack.minimum[z], stack.maximum[z]
        wanted: dict[str, tuple[float, float]] = {}
        for q in names:
            at = level[q]
            if at is None:
                status[q][z] = JOINT_UNREADABLE
                continue
            possible, blind = could_hold_level_in_reach(
                lows, highs, at[0], at[1], reach_of[block]
            )
            could[q][z] = near & possible
            if could[q][z].any():
                wanted[q] = at
            elif (near & blind).any():
                status[q][z] = JOINT_UNREADABLE
            else:
                status[q][z], area[q][z] = JOINT_NONE, 0.0
                excluded += 1
        if not wanted:
            continue
        held_tiles = np.zeros(tiles, dtype=bool)
        for q in wanted:
            held_tiles |= could[q][z]
        held = bounds[held_tiles]
        plane, unseen = seen_native(series, z, name)
        rows, cols = plane.shape
        # the far edge is one block wider, so a block with a place in the last tile is not cut
        window = (
            int(held[:, 0].min()),
            min(rows, int(held[:, 1].max()) + block[0] - 1),
            int(held[:, 2].min()),
            min(cols, int(held[:, 3].max()) + block[1] - 1),
        )
        reading = block_medians(
            plane, unseen, frame.spacing_rc, LIGAMENT_SMOOTH_MM, window
        )
        blocks = block_holds(reach, reading)
        got, seen_n, unseen_n = block_support(
            reading.median, blocks, reading.block_mm, wanted
        )
        finely += 1
        seen_blocks[z], unseen_blocks[z] = seen_n, unseen_n
        for q in wanted:
            if got[q] > 0:
                status[q][z], area[q][z] = JOINT_BODY, got[q]
            elif unseen_n:
                status[q][z] = JOINT_UNREADABLE  # an unseen block: unknown, not absent
            else:
                status[q][z], area[q][z] = JOINT_NONE, 0.0
        window_rc[z], cell_mm[z], cell_px[z] = (
            window,
            reading.block_mm,
            reading.block_px,
        )
        fine.append(
            FineReading(
                z,
                reading.window_rc,
                reading.block_px,
                reading.block_mm,
                reading.median,
                blocks,
                blocks,
            )
        )
    ledger.record(f"{name}.cheap_readings", planes=finely)
    ledger.record(f"{name}.tile_exclusions", planes=excluded)
    ledger.record(f"{name}.slices_without_both_bones_identified", planes=lacking)
    handed(f"{name}_profile", ("status", "area_mm2"))
    # kept, not read: no stage after the profile reads the blocks or the corridor it drew
    handed(f"{name}_profile", ("fine",))
    return JointProfile(
        names,
        status,
        area,
        seen_blocks,
        unseen_blocks,
        corridor_px,
        corridor,
        could,
        window_rc,
        cell_mm,
        cell_px,
        tuple(fine),
        level,
    )


@dataclass(frozen=True)
class JointPlane:
    """One plane the profile pointed to, as the existing rules read it: its `slice`, whether it is the
    series' `middle` slice (the bootstrap's own naming, not read again), `code` ("read", or
    `UNREADABLE_GEOMETRY`), the `codes` each existing rule gave there (`meniscus`, `meniscus_side`,
    `cartilage`, `pcl`, `mcl`, `acl`, and the readings `horns`, `cartilage_reading` where the
    existing rule's gate refuses the plane), what the carried places named of the femur and the tibia
    (`femur`, `tibia`: `knee.collapse.bones` outcomes), the lens's `labels` and `available`, the
    plane's naming `objects` (int8, `OBJECT_CODES`), the `reading` stack of candidates the existing
    rules do not license there (the horns, the cartilage on a sagittal plane) and `horn_end` (1 the
    piece at the front of the joint, 2 at the back), the sagittal plane's `compartment` and its place
    toward the patient's left of the notch (`toward_left_mm`), the femur's marrow `light` and the
    quantities that pointed here (`asked`)."""

    slice: int
    middle: bool
    code: str
    codes: dict[str, str]
    femur: str
    tibia: str
    labels: np.ndarray | None
    available: np.ndarray | None
    objects: np.ndarray | None
    reading: np.ndarray | None
    horn_end: np.ndarray | None
    compartment: str | None
    toward_left_mm: float | None
    light: float | None
    asked: tuple[str, ...]


def joint_plane(
    own: Measured,
    z: int,
    femur_lps: np.ndarray,
    tibia_lps: np.ndarray,
    keys: tuple[str, str],
    asked: tuple[str, ...],
    toward_left_mm: float | None,
) -> JointPlane:
    """The existing rules of the sided menisci, the cartilage, the PCL, the ACL and the MCL on ONE
    pointed plane: the lens (`lens_of`, once per slice, so a plane the bones or another family read is
    handed on) and its field (`field_of`); the femur and the tibia named by the carried places
    (`name_territory`, the established `carried_bone`), the joint between them as `assign_plane`
    makes it; then each rule as `assign_plane` orders them, from the same operations: the menisci (the
    thick low signal touching the joint, the piece nearest each end, sided by the header), the
    cartilage (fat suppression), the PCL (no fat suppression), the MCL, and the ACL as `acl_slice`
    reads it, from the bones carried to the plane. A rule's own gate is kept as its code: on a sagittal
    plane the menisci and the cartilage are refused (side to side runs through the plane) and what the
    same operation finds there (`horn_pieces`, `cartilage_on`) is only a reading, in `reading`, never
    a name. Nothing here is a new definition, and the rest of `assign_plane` is not run."""
    series, record = own.series, own.record
    uid = series.row.series_uid
    frame = plane_frame(series, z)
    if isinstance(frame, str):
        return JointPlane(
            z,
            False,
            UNREADABLE_GEOMETRY,
            {},
            "",
            "",
            None,
            None,
            None,
            None,
            None,
            None,
            toward_left_mm,
            None,
            asked,
        )
    plane = np.asarray(series.volume[z])
    _, lens, _ = lens_of(
        series, z, plane, frame, float(record["background_split"]), "joint"
    )
    field = field_of(series, z, plane, frame, lens)
    reads("interiors", ("labels", "available", "dark"), "joint")
    reads("field", ("objects", "peaks", "leg"), "joint")
    shape = plane.shape
    labels, available = lens.labels, np.asarray(lens.available, dtype=bool)
    femur_foot = bone_footprint(series, z, frame, shape, femur_lps, keys[0])
    tibia_foot = bone_footprint(series, z, frame, shape, tibia_lps, keys[1])
    femur = name_territory(labels, available, femur_foot, tibia_foot)
    tibia = name_territory(labels, available, tibia_foot, femur_foot)
    none = np.zeros(shape, dtype=bool)
    femur_places = femur.region if femur.code == IDENTIFIED else none
    tibia_places = tibia.region if tibia.code == IDENTIFIED else none
    objects = field.objects.copy()
    objects[femur_places] = OBJECT_CODES["femur"]
    objects[tibia_places] = OBJECT_CODES["tibia"]
    basis = frame.basis_lps
    spacing = np.linalg.norm(basis, axis=0)
    sides_in_plane, front_in_plane, _ = field.in_plane
    fat_suppressed = int(series.row.fat_suppression) == 1  # the tag is stored as text
    knee = str(record["assignments"]["knee"])
    outside = margin_of(uid, z, plane)
    measures = measures_of(uid, z, plane, frame)
    bones_named = bool(femur_places.any() and tibia_places.any())
    if bones_named:
        objects[
            between_along_the_leg(femur_places, tibia_places, basis)
            & (objects == 0)
            & ~outside
        ] = OBJECT_CODES["joint"]
    joint = objects == OBJECT_CODES["joint"]
    codes: dict[str, str] = {}
    # the menisci, as `assign_plane` reads them
    menisci = 0
    if sides_in_plane and joint.any():
        pieces, _ = ndi.label(
            thick_parts(lens.dark & ~outside, spacing, MENISCUS_THICKNESS_MM)
        )
        touching = np.unique(
            pieces[ndi.binary_dilation(joint, structure=FOUR_NEIGHBOURS) & (pieces > 0)]
        )
        pieces, count = ndi.label(np.isin(pieces, touching) & (pieces > 0))
        leftward = measures.along(0)
        for piece, toward_left in end_pieces(
            pieces, count, leftward, float(leftward[joint].mean())
        ):
            side = meniscus_side(knee, toward_left)
            name = "meniscus" if side == "meniscus" else f"{side}_meniscus"
            objects[pieces == piece] = OBJECT_CODES[name]
            menisci += 1
    codes["meniscus"] = meniscus_code(sides_in_plane, joint.any(), menisci)
    codes["meniscus_side"] = side_code(knee, menisci)
    # the cartilage: a fat-suppressed plane side to side runs in
    femoral = tibial = none
    if sides_in_plane and fat_suppressed and joint.any():
        femoral, tibial = cartilage_on(plane, objects, spacing, measures)
    codes["cartilage"] = cartilage_code(
        sides_in_plane,
        fat_suppressed,
        bool(joint.any()),
        bool(femoral.any() or tibial.any()),
    )
    objects[femoral] = OBJECT_CODES["femoral_cartilage"]
    objects[tibial] = OBJECT_CODES["tibial_cartilage"]
    # the PCL: a sagittal plane without fat suppression, the thick dark band joining the bones
    pcl = none
    if front_in_plane and not fat_suppressed and bones_named:
        pcl = band_joining(
            dark_bands(plane, objects, spacing, outside, measures),
            objects == OBJECT_CODES["femur"],
            objects == OBJECT_CODES["tibia"],
            spacing,
            measures,
        ) & np.isin(objects, (0, OBJECT_CODES["joint"]))
    # a ligament inside the joint is enclosed by the picture: a band that runs to the picture's own
    # edge is the dark soft tissue behind the knee, which reaches the bones' posterior corners
    edge = np.zeros(shape, dtype=bool)
    edge[0], edge[-1], edge[:, 0], edge[:, -1] = True, True, True, True
    runs_off = bool(pcl.any() and (pcl & edge).any())
    if runs_off:
        pcl = none
    codes["pcl"] = (
        "abstain_band_runs_to_the_picture_edge"
        if runs_off
        else pcl_code(front_in_plane, fat_suppressed, bones_named, bool(pcl.any()))
    )
    objects[pcl] = OBJECT_CODES["pcl"]
    # the MCL: the low signal left on the medial meniscus's side that joins the bones
    medial = bool((objects == OBJECT_CODES["medial_meniscus"]).any())
    mcl = none
    if sides_in_plane and medial:
        mcl = ligament_on_the_inner_side(lens.dark, objects, basis, outside, measures)
    codes["mcl"] = mcl_code(sides_in_plane, medial, bool(mcl.any()))
    objects[mcl] = OBJECT_CODES["mcl"]
    # the ACL, as `acl_slice` reads it, from the bones carried to this plane by place
    acl = none
    if front_in_plane and fat_suppressed and bones_named:
        acl = acl_on_slice(
            labels, field.peaks, femur_places, tibia_places, basis, outside
        )
    # an ACL lies BETWEEN the bones: a territory that holds the carried bones' own places is a lens
    # territory leaking over a bone (seen on the lateral planes), kept unnamed
    leaks = bool(acl.any() and (acl & (femur_places | tibia_places)).any())
    if leaks:
        acl = none
    codes["acl"] = (
        "abstain_region_holds_the_bones_places"
        if leaks
        else acl_code(
            front_in_plane, knee, bones_named, fat_suppressed, bool(acl.any())
        )
    )
    objects[acl & np.isin(objects, (0, OBJECT_CODES["joint"]))] = OBJECT_CODES["acl"]
    # what the same operations find where the existing rule's gate refuses the plane: readings only
    candidates = np.zeros(shape, dtype=np.int8)
    ends = np.zeros(shape, dtype=np.int8)
    side = compartment(knee, np.nan if toward_left_mm is None else toward_left_mm)
    name = "meniscus" if side == "meniscus" else f"{side}_meniscus"
    if front_in_plane and not sides_in_plane:
        if joint.any():
            kept, ends = horn_pieces(
                lens.dark, joint, outside, spacing, measures.along(1)
            )
            candidates[kept] = OBJECT_CODES[name]
            codes["horns"] = (
                HORNS if kept.any() else "abstain_no_thick_low_signal_in_the_joint"
            )
        else:
            codes["horns"] = "abstain_no_joint"
        if fat_suppressed and joint.any():
            femoral, tibial = cartilage_on(plane, objects, spacing, measures)
            candidates[femoral] = OBJECT_CODES["femoral_cartilage"]
            candidates[tibial] = OBJECT_CODES["tibial_cartilage"]
            codes["cartilage_reading"] = (
                CARTILAGE_CANDIDATES
                if femoral.any() or tibial.any()
                else "abstain_nothing_bright_against_the_bones"
            )
    light = float(measures.light(femur_places)) if femur_places.any() else None
    handed("joint_plane", ("objects",))
    return JointPlane(
        z,
        False,
        "read",
        codes,
        femur.code,
        tibia.code,
        labels,
        available,
        handed_on(objects),
        candidates,
        ends,
        side if front_in_plane and not sides_in_plane else None,
        toward_left_mm,
        light,
        asked,
    )


@dataclass(frozen=True)
class JointTwin:
    """What the other sequence's slice through one pointed plane holds of the plane's parts: the
    twin's `slice` (None where it has none), the `code` ("read", or why not: an unknown, never an
    absence), the plane's parts laid onto the twin's own pixels (`objects`, int8) and the distance of
    their places from the twin's plane (`off_mm`). No lens is read on the twin."""

    slice: int | None
    code: str
    objects: np.ndarray | None
    off_mm: float | None


def joint_twin(own: Measured, twin: Measured | None, plane: JointPlane) -> JointTwin:
    """A pointed plane's named parts (`JOINT_PARTS`) laid onto the other sequence's slice through the
    same place, by the scanner's millimetres (never equal indices: `slice_through`) and the pair's one
    match of places (`matched`, shared with every other part laid across); the places the twin never
    saw hold nothing laid on them. Every failure is a code."""
    if plane.objects is None:
        raise ValueError("a_pointed_plane_that_was_read")
    objects = np.asarray(plane.objects)
    parts = [OBJECT_CODES[name] for name in JOINT_PARTS]
    if twin is None:
        return JointTwin(None, "none_of_the_other_sequence", None, None)
    other = twin.series
    thick, why = slab_thicknesses(other)
    if why is not None:
        return JointTwin(None, why, None, None)
    frame = plane_frame(own.series, plane.slice)
    if isinstance(frame, str):
        return JointTwin(None, frame, None, None)
    origins = np.asarray([np.asarray(p, dtype=float) for p in other.geometry.position])
    index = slice_through(frame.origin_lps, origins, twin.frame.normal(), thick)
    if index is None:
        return JointTwin(None, "twin_has_no_slice_at_this_place", None, None)
    twin_frame = plane_frame(other, index)
    if isinstance(twin_frame, str):
        return JointTwin(index, twin_frame, None, None)
    uid, twin_uid = own.series.row.series_uid, other.row.series_uid
    plane_here = np.asarray(own.series.volume[plane.slice])
    plane_there = np.asarray(other.volume[index])
    forward = matched(
        other,
        {"series_uid": twin_uid, "slice_index": index},
        twin_frame,
        plane_there.shape,
        {"series_uid": uid, "slice_index": plane.slice},
        frame,
        plane_here,
    )
    if isinstance(forward, str):
        return JointTwin(index, forward, None, None)
    reads("joint_plane", ("objects",), "joint_twin")
    laid = laid_by(objects, forward)
    named = np.where(np.isin(laid, parts), laid, 0).astype(np.int8)
    named[~finite_of(other)[index]] = (
        0  # a place the twin never saw holds nothing laid on it
    )
    places = frame.to_patient(np.argwhere(np.isin(objects, parts)).astype(float))
    off = (
        float(abs((places.mean(axis=0) - twin_frame.origin_lps) @ twin_frame.normal()))
        if len(places)
        else None
    )
    return JointTwin(index, "read", named, off)


# What a run of a quantity's support says once the existing rule read the planes read for it.
JOINT_RUN_RULE = {
    **RUN_CONFIRMATION,
    "candidates_only_the_existing_rule_does_not_license_the_plane": 4,
}
# The rule each quantity points at, in a plane's codes.
JOINT_POINTED_RULE = {
    DARK: "meniscus",
    LIGAMENT: "pcl",
    BRIGHT: "cartilage",
    FLUID: "acl",
}
JOINT_CANDIDATE_KEY = {DARK: "horns", BRIGHT: "cartilage_reading"}
JOINT_CANDIDATE_CODE = {DARK: HORNS, BRIGHT: CARTILAGE_CANDIDATES}


def says_of(plane: JointPlane, quantity: str, middle_codes: dict[str, str]) -> str:
    """What the existing rule a quantity points at said on one plane read for it: "confirmed" (the
    rule named it), "candidates" (only the reading its gate refuses), "rejected" (read, nothing) or
    "not_read" (the plane is the middle slice, whose own naming has no rule for it)."""
    rule = JOINT_POINTED_RULE[quantity]
    if plane.middle:
        code = middle_codes.get(rule)
        return (
            "confirmed"
            if code in NAMED
            else "not_read"
            if quantity == FLUID
            else "rejected"
        )
    if plane.codes.get(rule) == "identified":
        return "confirmed"
    key = JOINT_CANDIDATE_KEY.get(quantity)
    if key is not None and plane.codes.get(key) == JOINT_CANDIDATE_CODE[quantity]:
        return "candidates"
    return "rejected"


def joint_arrays(
    own: Measured,
    profile: JointProfile,
    planes: list[JointPlane],
    twins: list[JointTwin | None],
    pointed: list[int],
    runs: dict[str, list[tuple[int, int]]],
    origins: np.ndarray,
    offsets: np.ndarray,
    sound: bool,
    thick: np.ndarray,
) -> dict[str, np.ndarray]:
    """What the joint's profile and pointed planes keep, named `a3_joint_*`, in the series' own middle
    arrays: per quantity its status and area through depth, the tiles that could hold its level, its
    runs and their ends and envelopes; the corridor's pixels and tiles and the finer readings at their
    own resolution (ragged, nothing padded); the pointed slices' places along the stack's normal; and,
    one row per pointed plane but the middle slice (whose naming is `a1_objects`), the plane's naming
    `objects`, the `reading` candidates, the `horn_end` and the place toward the left of the notch. The
    lens's labels of a plane the bones already kept are not copied: `bone_lens_row` names its row of
    `a3_bone_plane_labels`; the others are one row of `a3_joint_plane_labels`."""
    shape = np.shape(own.arrays["acquired_plane"])
    rows_in = [p for p in planes if not p.middle]
    pointed_origin = origins[pointed] if sound and pointed else np.empty((0, 3))
    arrays: dict[str, np.ndarray] = {
        "a3_joint_corridor_px": profile.corridor_px,
        "a3_joint_corridor_tiles": profile.corridor,
        "a3_joint_seen_blocks": profile.seen_blocks,
        "a3_joint_unseen_blocks": profile.unseen_blocks,
        "a3_joint_profile_window_rc": profile.window_rc,
        "a3_joint_profile_block_mm": profile.cell_mm,
        "a3_joint_profile_block_px": profile.block_px,
        "a3_joint_depth_offsets_mm": offsets,
        "a3_joint_slice_thickness_mm": thick,
        "a3_joint_pointed_slices": np.asarray(pointed, dtype=np.int32),
        "a3_joint_pointed_origin_lps": pointed_origin,
        "a3_joint_pointed_position_mm": offsets[pointed]
        if sound and pointed
        else np.empty(0),
        "a3_joint_pointed_along_normal_mm": (pointed_origin @ own.frame.normal())
        if len(pointed_origin)
        else np.empty(0),
        "a3_joint_source_normal_lps": own.frame.normal(),
    }
    for q in profile.names:
        at = profile.level[q]
        arrays[f"a3_joint_{q}_status"] = profile.status[q]
        arrays[f"a3_joint_{q}_area_mm2"] = profile.area_mm2[q]
        arrays[f"a3_joint_{q}_could_tiles"] = profile.could[q]
        arrays[f"a3_joint_{q}_level"] = np.asarray(
            (np.nan, np.nan) if at is None else at, dtype=np.float64
        )
        _, ends, spans = describe_runs(
            runs[q], profile.status[q], offsets, thick, sound
        )
        arrays[f"a3_joint_{q}_runs"] = np.asarray(runs[q], dtype=np.int32).reshape(
            -1, 2
        )
        arrays[f"a3_joint_{q}_run_ends"] = ends.astype(np.int32)
        arrays[f"a3_joint_{q}_run_envelope_mm"] = spans
    for name, value in pack_fine_readings(profile.fine).items():
        if name != "tibia_reference":
            arrays[
                f"a3_joint_fine_{'reach_blocks' if name == 'pointer_body' else name}"
            ] = value
    bone_slices = [int(z) for z in own.arrays.get("a3_bone_plane_slices", ())]
    own_rows = [
        p for p in rows_in if p.labels is not None and p.slice not in bone_slices
    ]
    zero = np.zeros(shape, dtype=bool)
    arrays["a3_joint_plane_slices"] = np.asarray(
        [p.slice for p in rows_in], dtype=np.int32
    )
    arrays["a3_joint_plane_bone_lens_row"] = np.asarray(
        [bone_slices.index(p.slice) if p.slice in bone_slices else -1 for p in rows_in],
        dtype=np.int32,
    )
    own_slices = [p.slice for p in own_rows]
    arrays["a3_joint_plane_lens_row"] = np.asarray(
        [own_slices.index(p.slice) if p.slice in own_slices else -1 for p in rows_in],
        dtype=np.int32,
    )
    arrays["a3_joint_plane_labels"] = stack_of(
        [np.asarray(p.labels) for p in own_rows], shape, np.int32
    )
    arrays["a3_joint_plane_available"] = stack_of(
        [zero if p.available is None else p.available for p in own_rows], shape, bool
    )
    arrays["a3_joint_plane_objects"] = stack_of(
        [
            np.zeros(shape, np.int8) if p.objects is None else np.asarray(p.objects)
            for p in rows_in
        ],
        shape,
        np.int8,
    )
    arrays["a3_joint_plane_reading"] = stack_of(
        [
            np.zeros(shape, np.int8) if p.reading is None else np.asarray(p.reading)
            for p in rows_in
        ],
        shape,
        np.int8,
    )
    arrays["a3_joint_plane_horn_end"] = stack_of(
        [
            np.zeros(shape, np.int8) if p.horn_end is None else np.asarray(p.horn_end)
            for p in rows_in
        ],
        shape,
        np.int8,
    )
    arrays["a3_joint_plane_toward_left_mm"] = np.asarray(
        [np.nan if p.toward_left_mm is None else p.toward_left_mm for p in rows_in],
        dtype=np.float64,
    )
    arrays["a3_joint_plane_light"] = np.asarray(
        [np.nan if p.light is None else p.light for p in rows_in], dtype=np.float64
    )
    return arrays


@dataclass(frozen=True)
class JointRead:
    """The joint in one series, as `read_joint` read it: the `profile` through depth, the planes it
    pointed to (`planes`, the middle slice's bootstrap among them where it was), the twin's laying
    beside each plane but the middle one (`twins`), how it came out (`outcome`), the record's
    description (`record`, plain data) and the arrays it keeps on the series (`arrays`)."""

    profile: JointProfile
    planes: tuple[JointPlane, ...]
    twins: tuple[JointTwin | None, ...]
    outcome: str
    record: dict
    arrays: dict[str, np.ndarray]


def read_joint(own: Measured, partner: Measured | None, leg: Leg) -> JointRead | str:
    """The joint of one series through the whole depth: the four-quantity profile of its corridor
    (`joint_profile`, from the bones' carried places, the series' background split and the bones'
    marrow light), each quantity's pointed planes (the maximum of each run of support, every tie, every
    run, and the slice beside a maximum that was unreadable: `positive_runs`, `run_maxima`,
    `confirmations`), and on only those planes the existing rules (`joint_plane`) with the plane's
    parts laid onto the twin's slice of the same place (`joint_twin`); the series' middle slice is the
    bootstrap's own naming and is not read again. Or why the series cannot be read: a string code, an
    unknown and never an absence. Only a series the leg runs along is read (a sagittal or coronal
    one) that named both bones on its middle slice."""
    series, record = own.series, own.record
    uid = series.row.series_uid
    if not own.assignment.in_plane[2]:
        return "abstain_leg_runs_through_the_plane"
    objects = own.arrays["a1_objects"]
    femur_mask = objects == OBJECT_CODES["femur"]
    tibia_mask = objects == OBJECT_CODES["tibia"]
    assigned = record["assignments"]
    if (
        assigned["femur"] is None
        or assigned["tibia"] is None
        or not (femur_mask.any() and tibia_mask.any())
    ):
        return "bones_not_named_on_the_middle_slice"
    reads("squint_stack", ("code",), "joint")
    if own.stack.code != "present":
        return f"squint_{own.stack.code}"
    if series.volume is None:
        return "no_stacked_volume"
    femur_lps, tibia_lps = leg.femur_lps, leg.tibia_lps
    if not len(femur_lps) or not len(tibia_lps):
        return "no_carried_places"
    index = record["slice_index"]
    measures = measures_of(uid, index, own.arrays["acquired_plane"], own.frame)
    fat_suppressed = int(series.row.fat_suppression) == 1  # the tag is stored as text
    level = levels(
        float(record["background_split"]),
        float(measures.light(femur_mask)),
        float(measures.light(femur_mask | tibia_mask)),
    )
    names = (DARK, BRIGHT, FLUID) if fat_suppressed else (DARK, LIGAMENT)
    established = bones_identified_at(own, partner)
    profile = joint_profile(
        series,
        own.stack,
        femur_lps,
        tibia_lps,
        level,
        names,
        bones_unestablished=None
        if established is None
        else np.asarray([z not in established for z in range(len(series.volume))]),
    )
    reads("joint_profile", ("status", "area_mm2"), "joint")
    runs: dict[str, list[tuple[int, int]]] = {}
    maxima: dict[str, list[np.ndarray]] = {}
    confirm: dict[str, list[int]] = {}
    pointed_by: dict[int, list[str]] = {}
    for q in names:
        runs[q] = positive_runs(profile.area_mm2[q])
        maxima[q] = run_maxima(profile.area_mm2[q], runs[q])
        confirm[q] = confirmations(
            runs[q], maxima[q], profile.status[q], (JOINT_UNREADABLE,)
        )
        for z in {int(z) for peaks in maxima[q] for z in peaks} | set(confirm[q]):
            pointed_by.setdefault(z, []).append(q)
    pointed = sorted(pointed_by)
    ledger.record("joint.pointed_planes", planes=len(pointed))
    keys = (digest(femur_lps), digest(tibia_lps))
    sagittal = not own.assignment.in_plane[0]
    planes: list[JointPlane] = []
    twins: list[JointTwin | None] = []
    for z in pointed:
        asked = tuple(pointed_by[z])
        if z == index:
            planes.append(
                JointPlane(
                    z,
                    True,
                    "bootstrap",
                    {},
                    "",
                    "",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    asked,
                )
            )
            continue
        left = None
        place = plane_frame(series, z)
        if (
            sagittal
            and not isinstance(place, str)
            and leg.notch_origin_lps is not None
            and leg.notch_normal is not None
        ):
            left = float((place.origin_lps - leg.notch_origin_lps) @ leg.notch_normal)
        got = joint_plane(own, z, femur_lps, tibia_lps, keys, asked, left)
        planes.append(got)
        twins.append(
            joint_twin(own, partner, got)
            if got.code == "read" and got.objects is not None
            else None
        )
    origins, thick, offsets, sound = series_depth(series, own.frame, index)
    middle_codes = record["assignments"]["codes"]
    asked_of = {p.slice: p for p in planes}
    quantity_rows: dict[str, dict] = {}
    for q in names:
        described, _, _ = describe_runs(
            runs[q], profile.status[q], offsets, thick, sound
        )
        for i, ((a, b), peaks) in enumerate(zip(runs[q], maxima[q], strict=True)):
            here = sorted(
                {int(z) for z in peaks}
                | {int(z) for z in confirm[q] if z in (a - 1, b)}
            )
            said = [says_of(asked_of[z], q, middle_codes) for z in here]
            described[i]["planes_read_for_it"] = here
            described[i]["native_rule"] = (
                "confirmed_by_the_native_rule"
                if "confirmed" in said
                else "candidates_only_the_existing_rule_does_not_license_the_plane"
                if "candidates" in said
                else "rejected_by_the_native_rule"
                if "rejected" in said
                else "not_read_natively"
            )
        at = profile.level[q]
        quantity_rows[q] = {
            "points_at": POINTS_AT[q],
            "level": None
            if at is None
            else [None if np.isinf(v) else float(v) for v in at],
            "status": {
                name: int(np.count_nonzero(profile.status[q] == code))
                for name, code in FIBULA_POINTER_STATUS.items()
                if np.count_nonzero(profile.status[q] == code)
            },
            "pointer_runs": described,
            "pointer_representatives": [[int(z) for z in peaks] for peaks in maxima[q]],
            "confirmed_slices": [int(z) for z in confirm[q]],
            "unknown_slices": [
                int(z) for z in np.flatnonzero(profile.status[q] == JOINT_UNREADABLE)
            ],
        }
    rows_in = [p for p in planes if not p.middle]
    twin_of = {id(p): t for p, t in zip(rows_in, twins, strict=True)}
    pointed_rows = []
    for p in planes:
        row: dict[str, Any] = {
            "slice": p.slice,
            "middle": p.middle,
            "pointed_by": list(p.asked),
            "code": p.code,
            "codes": dict(p.codes),
            "femur": p.femur,
            "tibia": p.tibia,
            "compartment": p.compartment,
            "toward_left_of_the_notch_mm": p.toward_left_mm,
            "femur_marrow_light": None if p.light is None else finite_or_none(p.light),
            "position_mm": finite_or_none(offsets[p.slice]) if sound else None,
            "parts_pixels": {
                name: int(np.count_nonzero(p.objects == OBJECT_CODES[name]))
                for name in JOINT_PARTS
                if p.objects is not None
                and np.count_nonzero(p.objects == OBJECT_CODES[name])
            },
        }
        if not p.middle:
            twin = twin_of[id(p)]
            row["twin"] = (
                None
                if twin is None
                else {"slice": twin.slice, "code": twin.code, "off_mm": twin.off_mm}
            )
        pointed_rows.append(row)
    if not pointed:
        outcome = (
            "unreadable"
            if any((profile.status[q] == JOINT_UNREADABLE).any() for q in names)
            else "no_support_found"
        )
    else:
        outcome = "read"
    ambiguities = [
        "the_corridor_is_where_the_bones_carried_places_leave_a_joint_an_upper_bound_never_a_section",
        "a_quantity_is_support_never_a_name_the_existing_rules_name_on_the_pointed_planes_only",
    ]
    if any(profile.unseen_blocks > 0):
        ambiguities.append("blocks_never_seen_make_an_area_a_lower_bound")
    if any(row["unknown_slices"] for row in quantity_rows.values()):
        ambiguities.append("slices_the_profile_could_not_read_are_unknown_not_empty")
    if not sound:
        ambiguities.append("slice_geometry_unsound_so_no_physical_depth")
    record_part = {
        "outcome": outcome,
        "block_mm": float(LIGAMENT_SMOOTH_MM),
        "reach_mm": float(SHELL_MM),
        "quantities": quantity_rows,
        "run_rule_codes": dict(JOINT_RUN_RULE),
        "status_codes": dict(FIBULA_POINTER_STATUS),
        "pointed_planes": pointed_rows,
        "ambiguities": ambiguities,
    }
    arrays = joint_arrays(
        own, profile, planes, twins, pointed, runs, origins, offsets, sound, thick
    )
    handed("joint", ("pointed", "planes", "twins"))
    return JointRead(profile, tuple(planes), tuple(twins), outcome, record_part, arrays)


def sided_menisci(
    own: Measured, read: JointRead, bodies: list[dict], names: tuple[str, ...]
) -> dict[str, dict]:
    """ONE sided meniscus is its coronal body and its sagittal horns, kept as separate descriptions
    of the same object: for each compartment, the planes that named its body (where the coronal rules
    name it) and the planes whose horn candidates lie in its compartment, with the pixels of each.
    A compartment with neither is kept empty: unknown, not absent."""
    found: dict[str, dict] = {
        name: {"coronal_body": [], "sagittal_horns": []} for name in names
    }
    for body in bodies:
        found.setdefault(body["object"], {"coronal_body": [], "sagittal_horns": []})[
            "coronal_body"
        ].append({k: v for k, v in body.items() if k != "object"})
    rows_in = [p for p in read.planes if not p.middle]
    for row, p in enumerate(rows_in):
        if p.codes.get("horns") != HORNS or p.reading is None or p.horn_end is None:
            continue
        name = (
            "meniscus"
            if p.compartment in (None, "meniscus")
            else f"{p.compartment}_meniscus"
        )
        found.setdefault(name, {"coronal_body": [], "sagittal_horns": []})[
            "sagittal_horns"
        ].append(
            {
                "slice": p.slice,
                "row": row,
                "toward_left_of_the_notch_mm": p.toward_left_mm,
                "front_pixels": int(np.count_nonzero(p.horn_end == 1)),
                "back_pixels": int(np.count_nonzero(p.horn_end == 2)),
                "provenance": "native",
                "kind": "reading",
            }
        )
    return found


def joint_twin_arrays(
    twin: Measured,
    planes: list[JointPlane],
    twins: list[JointTwin | None],
    prefix: str,
) -> dict[str, np.ndarray]:
    """What the twin's slices through the pointed planes hold of the planes' parts, as a stack on the
    twin's own pixels, named `<prefix>_*`, one row per plane whose twin was read: the plane's slice
    (`from_slices`), the twin's (`slices`) and the parts laid on (`objects`, `OBJECT_CODES`). (The
    prefix names the series that asked, so two sequences asking one twin never overwrite each
    other.)"""
    shape = np.shape(twin.arrays["acquired_plane"])
    rows = [
        (p, t)
        for p, t in zip(planes, twins, strict=True)
        if t is not None and t.code == "read"
    ]
    return {
        f"{prefix}_from_slices": np.asarray([p.slice for p, _ in rows], dtype=np.int32),
        f"{prefix}_slices": np.asarray(
            [-1 if t.slice is None else t.slice for _, t in rows], dtype=np.int32
        ),
        f"{prefix}_objects": stack_of(
            [
                np.zeros(shape, np.int8) if t.objects is None else t.objects
                for _, t in rows
            ],
            shape,
            np.int8,
        ),
    }


# What a rule says of a plane its own gate refuses by orientation or by sequence: expected, so no
# reading is made of it (the plane's codes keep it).
JOINT_GATES = (
    "abstain_side_to_side_runs_through_the_plane",
    "abstain_front_to_back_runs_through_the_plane",
    "abstain_not_brighter_than_marrow_without_fat_suppression",
    "abstain_marrow_as_dark_as_a_ligament_with_fat_suppression",
    "abstain_not_walled_off_without_fat_suppression",
)
JOINT_NOTES = {
    "meniscus": "the existing menisci description names the dark wedge on this coronal plane: the body's section here, not the whole meniscus (its horns are the sagittal planes' readings)",
    "cartilage": "the layer on this bone in the joint on this plane: the section here, not the whole surface",
    "mcl": "the low signal left on the medial meniscus's side that joins the bones, on this coronal plane: the section here",
    "pcl": "the thick uniformly dark band joining the bones on this sagittal plane: the section here",
    "acl": "the region walled off by fluid whose peak lies in the joint on this sagittal plane, the bones carried here by place: the section here",
}


def bones_identified_at(own: Measured, partner: Measured | None) -> set[int] | None:
    """The slices of `own`'s stack where the bones' family natively identified BOTH the femur and
    the tibia (`a3_<bone>_plane_outcome` identified, and the middle slice, the bootstrap's own
    naming), read from the series' own bone arrays where it was profiled and otherwise from its
    twin's, at the twin's slice through the same place (`slice_through`: a warranted same-place
    transfer of the identity, not a projection). None where no series of the pair was profiled."""
    source = own if "a3_femur_plane_slices" in own.arrays else partner
    if source is None or "a3_femur_plane_slices" not in source.arrays:
        return None
    reads("bones", ("planes",), "joint")
    both: set[int] | None = None
    for bone in ("femur", "tibia"):
        named = {int(source.record["slice_index"])} | {
            int(z)
            for z, outcome in zip(
                source.arrays[f"a3_{bone}_plane_slices"],
                source.arrays[f"a3_{bone}_plane_outcome"],
                strict=True,
            )
            if int(outcome) == OUTCOMES.index(IDENTIFIED)
        }
        both = named if both is None else both & named
    assert both is not None
    if source is own:
        return both
    other = source.series
    origins = np.asarray([np.asarray(q, dtype=float) for q in other.geometry.position])
    thick = [float("nan") if t is None else float(t) for t in other.slice_thickness_mm]
    normal = source.frame.normal()
    depth = len(own.series.volume) if own.series.volume is not None else 0
    found: set[int] = set()
    for z in range(depth):
        place = plane_frame(own.series, z)
        if isinstance(place, str):
            continue
        at = slice_through(place.origin_lps, origins, normal, thick)
        if at is not None and at in both:
            found.add(z)
    return found


def name_the_joint(
    measured: list[Measured],
    partners: list[Measured | None],
    leg: Leg | None,
    study_uid: str,
) -> None:
    """The sided menisci, the articular cartilage, the cruciates and the MCL through the stacks
    (`read_joint`) of every series the leg runs along that names both bones on its middle slice,
    kept in the series' own middle records and arrays (saved by the caller) beside the observations
    the bones and the patella made.

    Native: the middle slice's own naming of each part (the bootstrap), each part on each pointed
    plane where its existing rule names it (resolved, one row of `a3_joint_plane_objects`), what a
    rule found where its gate refuses the plane (the horn candidates of a sagittal plane in its
    compartment, the cartilage there: readings, never names, one row of `a3_joint_plane_reading`),
    and a rule that read a plane it was pointed to and named nothing (a reading with its code). Laid:
    each pointed plane's parts onto the other sequence's slice of the same place
    (`joint_twin`, `<prefix>_objects` of the twin). Projected: each part's largest section onto the
    slice of every other series nearest it (a target for a native question, never a boundary; the
    coronal body of a meniscus onto the sagittal series is where its horns are asked). One sided
    meniscus is its coronal body and its sagittal horns: the same object name carries both, and the
    record lists them apart per compartment (`sided_menisci`). What could not be said is an
    `Unresolved` with its code: a part no pointed plane named, a lateral plane beyond the compartment,
    a series the leg runs through, is unknown and never absent. The profile and every plane are kept
    and no stage reads them: the existing consumers (the MCL and the cartilage on the middle slice,
    the cruciates' own slices) are not changed by them."""
    carried = leg if leg is not None else leg_of(measured)
    results = [read_joint(own, partners[i], carried) for i, own in enumerate(measured)]
    where = {id(m): i for i, m in enumerate(measured)}
    said: list[tuple[list[Observation], list[Unresolved]]] = [
        ([], []) for _ in measured
    ]
    for i, own in enumerate(measured):
        read = results[i]
        uid, view = own.record["series_uid"], tuple(own.record["view"])
        here, missing = said[i]
        artifact = str(artifact_of(study_uid, own.record))
        if isinstance(read, str):
            own.record["joint"] = {"code": read, "quantities": list(POINTS_AT)}
            missing.append(Unresolved("joint", "native", uid, view, read))
            continue
        partner = partners[i]
        at = None if partner is None else where[id(partner)]
        index = own.record["slice_index"]
        assigned = own.record["assignments"]
        codes = assigned["codes"]
        sided = (
            SIDED_MENISCI[:2] if assigned["knee"] in ("R", "L") else SIDED_MENISCI[2:]
        )
        wanted = (*sided, *JOINT_PARTS[3:])
        rows_in = [p for p in read.planes if not p.middle]
        twins = list(read.twins)
        own.arrays.update(read.arrays)
        # the joint lies between the bones: a pointed plane's names are resolved only where the
        # bones' family natively identified both bones at that place (marrow body agreeing with the
        # territory); elsewhere the existing rules' decisions are kept as readings, never names
        confirmed_at = bones_identified_at(own, partner)
        prefix = "a3_joint_twin"
        if partner is not None:
            prefix = source_prefix(prefix, partner.arrays, uid)
            partner.arrays.update(joint_twin_arrays(partner, rows_in, twins, prefix))
        twin_artifact = (
            str(artifact_of(study_uid, partner.record)) if partner is not None else ""
        )
        got: set[str] = set()
        reason: dict[str, set[str]] = {name: set() for name in wanted}
        bodies: list[dict] = []
        sections: dict[
            str, list[tuple[int, np.ndarray, PlaneFrame, str, int | None]]
        ] = {name: [] for name in wanted}
        # the middle slice: the bootstrap's own naming of each part, as the run made it
        middle = own.arrays["a1_objects"]
        for name in wanted:
            if name == "acl":
                continue  # the ACL is named on its own slice, not the middle (see `joint_existing`)
            code = codes.get(JOINT_RULE[name])
            mask = middle == OBJECT_CODES[name]
            reason[name].add(str(code))
            if code in NAMED and mask.any():
                got.add(name)
                native = code == "identified"
                here.append(
                    observe(
                        name,
                        "native" if native else "laid",
                        "resolved",
                        own,
                        (index,),
                        str(code),
                        int(np.count_nonzero(mask)),
                        0.0 if native else None,
                        "a1_objects",
                        "the middle slice's own naming (the bootstrap): the section on this slice, not the whole part",
                        artifact,
                        None,
                        OBJECT_CODES[name],
                    )
                )
                sections[name].append((index, mask, own.frame, "a1_objects", None))
                if name in SIDED_MENISCI:
                    bodies.append(
                        {
                            "object": name,
                            "slice": index,
                            "row": None,
                            "pixels": int(np.count_nonzero(mask)),
                            "provenance": "native" if native else "laid",
                            "kind": "resolved",
                            "code": str(code),
                        }
                    )
        # the pointed planes: the rules read on each, row by row of the stacks kept
        stack_objects = own.arrays["a3_joint_plane_objects"]
        stack_reading = own.arrays["a3_joint_plane_reading"]
        twin_row = 0
        for row, (p, t) in enumerate(zip(rows_in, twins, strict=True)):
            if p.code != "read":
                missing.append(Unresolved("joint", "native", uid, view, p.code))
                continue
            frame = plane_frame(own.series, p.slice)
            for name in wanted:
                reason[name].add(str(p.codes[JOINT_RULE[name]]))
                mask = stack_objects[row] == OBJECT_CODES[name]
                count = int(np.count_nonzero(mask))
                if not count:
                    continue
                # the cruciates on the extra planes were found, on the proof, to outline soft tissue
                # behind the knee and over the tibia: the existing rule's decision is kept as a
                # reading (never resolved, never projected) until a relation tells them apart
                unconfirmed = confirmed_at is None or p.slice not in confirmed_at
                cruciate = name in ("pcl", "acl") or unconfirmed
                if not cruciate:
                    got.add(name)
                here.append(
                    observe(
                        name,
                        "native",
                        "reading" if cruciate else "resolved",
                        own,
                        (p.slice,),
                        str(p.codes[JOINT_RULE[name]]),
                        count,
                        0.0,
                        "a3_joint_plane_objects",
                        JOINT_NOTES[JOINT_RULE[name]]
                        + (
                            "; a reading only: the existing rule's decision on an additional plane, not validated anatomy"
                            if name in ("pcl", "acl")
                            else "; a reading only: the bones' family did not natively identify both bones at this place, so the joint between them is not established here"
                            if unconfirmed
                            else ""
                        ),
                        artifact,
                        row,
                        OBJECT_CODES[name],
                    )
                )
                if not isinstance(frame, str) and not cruciate:
                    sections[name].append(
                        (p.slice, mask, frame, "a3_joint_plane_objects", row)
                    )
                if name in SIDED_MENISCI:
                    bodies.append(
                        {
                            "object": name,
                            "slice": p.slice,
                            "row": row,
                            "pixels": count,
                            "provenance": "native",
                            "kind": "reading" if unconfirmed else "resolved",
                            "code": str(p.codes["meniscus"]),
                        }
                    )
            # a rule that read a plane it was pointed to and named nothing: a reading with its code
            for quantity, rule, name in (
                (DARK, "meniscus", "meniscus"),
                (DARK, "mcl", "mcl"),
                (BRIGHT, "cartilage", "cartilage"),
                (LIGAMENT, "pcl", "pcl"),
                (FLUID, "acl", "acl"),
            ):
                code = str(p.codes[rule])
                resolved = any(
                    np.any(stack_objects[row] == OBJECT_CODES[w])
                    for w in wanted
                    if JOINT_RULE[w] == rule
                )
                if (
                    quantity in p.asked
                    and code != "identified"
                    and code not in JOINT_GATES
                    and not resolved
                ):
                    here.append(
                        observe(
                            name,
                            "native",
                            "reading",
                            own,
                            (p.slice,),
                            code,
                            None,
                            0.0,
                            "a3_joint_plane_objects",
                            f"the plane was pointed to by the {quantity} quantity and read in full; the existing rule names nothing here",
                            artifact,
                            row,
                        )
                    )
            # what the same operations find where the rule's gate refuses the plane: readings only
            for key, code in (
                ("horns", HORNS),
                ("cartilage_reading", CARTILAGE_CANDIDATES),
            ):
                if p.codes.get(key) != code:
                    continue
                for name in (
                    (
                        "meniscus"
                        if p.compartment in (None, "meniscus")
                        else f"{p.compartment}_meniscus",
                    )
                    if key == "horns"
                    else ("femoral_cartilage", "tibial_cartilage")
                ):
                    count = int(
                        np.count_nonzero(stack_reading[row] == OBJECT_CODES[name])
                    )
                    if not count:
                        continue
                    here.append(
                        observe(
                            name,
                            "native",
                            "reading",
                            own,
                            (p.slice,),
                            code,
                            count,
                            0.0,
                            "a3_joint_plane_reading",
                            "meniscal horns on a sagittal plane in the compartment its place toward the left of the notch names (`a3_joint_plane_horn_end`: 1 the front end of the joint, 2 the back): the existing menisci description with the plane's own in-plane axis, whose rule is gated to side-to-side planes, so a candidate and never a name; the other planes of the compartment are unknown, not absent"
                            if key == "horns"
                            else "the cartilage rule's operation on a sagittal plane, whose rule is gated to side-to-side planes: a candidate layer, never a name",
                            artifact,
                            row,
                            OBJECT_CODES[name],
                        )
                    )
            # laid: the plane's parts onto the twin's slice of the same place
            if t is None:
                continue
            present = [
                name
                for name in wanted
                if np.any(stack_objects[row] == OBJECT_CODES[name])
                and name not in ("pcl", "acl")
                and confirmed_at is not None
                and p.slice in confirmed_at
            ]
            if t.code != "read" or t.objects is None or t.slice is None:
                for name in present:
                    missing.append(
                        Unresolved(
                            name,
                            "laid",
                            None if partner is None else partner.record["series_uid"],
                            None if partner is None else tuple(partner.record["view"]),
                            t.code,
                        )
                    )
                continue
            if partner is None or at is None:
                continue
            for name in present:
                count = int(np.count_nonzero(t.objects == OBJECT_CODES[name]))
                if count:
                    said[at][0].append(
                        observe(
                            name,
                            "laid",
                            "resolved",
                            partner,
                            (t.slice,),
                            "laid_from_its_partner",
                            count,
                            t.off_mm,
                            f"{prefix}_objects",
                            f"the part named on native slice {p.slice} laid by the pair's match of places; places the twin never saw are left out",
                            twin_artifact,
                            twin_row,
                            OBJECT_CODES[name],
                        )
                    )
                else:
                    said[at][1].append(
                        Unresolved(
                            name,
                            "laid",
                            partner.record["series_uid"],
                            tuple(partner.record["view"]),
                            "nothing_of_the_part_lands_on_the_twin",
                        )
                    )
            twin_row += 1
        # what no plane named is unknown, each part naming why, never absent
        for name in wanted:
            if name not in got:
                missing.append(
                    Unresolved(
                        name,
                        "native",
                        uid,
                        view,
                        "|".join(
                            sorted(reason[name] or {"no_plane_pointed_to_read_it"})
                        ),
                    )
                )
        # projected: each part's largest section onto every other series' nearest slice
        skip = {uid} | (
            {partner.record["series_uid"]} if partner is not None else set()
        )
        for name in wanted:
            if not sections[name]:
                continue
            z, region, frame, support, source_row = max(
                sections[name], key=lambda s: int(np.count_nonzero(s[1]))
            )
            physical = frame.to_patient(np.argwhere(region).astype(float))
            for other in measured:
                other_uid = other.record["series_uid"]
                if other_uid in skip:
                    continue
                other_view = tuple(other.record["view"])
                target = bone_target(physical, other)
                if isinstance(target, str):
                    said[where[id(other)]][1].append(
                        Unresolved(name, "projected", other_uid, other_view, target)
                    )
                    continue
                nearest, place, distance, count = target
                said[where[id(other)]][0].append(
                    observe(
                        name,
                        "projected",
                        "target",
                        other,
                        (nearest,),
                        place,
                        count,
                        distance,
                        support,
                        f"a location target projected from {name} on slice {z} of the series it was named in: where a native question may be asked (the coronal body of a meniscus onto a sagittal series: where its horns are), not a boundary seen on this slice",
                        artifact,
                        source_row,
                        OBJECT_CODES[name] if support == "a1_objects" else None,
                    )
                )
        for planned in read.record["pointed_planes"]:
            # what the recess family reads: a plane's menisci are names only where the bones are
            planned["bones_identified_at_this_place"] = (
                None
                if confirmed_at is None
                else bool(planned["middle"] or planned["slice"] in confirmed_at)
            )
        own.record["joint"] = {
            **read.record,
            "twin_arrays_prefix": prefix if partner is not None else None,
            "sided_menisci": sided_menisci(own, read, bodies, sided),
            "existing_slices": [],
        }
    for m, (here, missing) in zip(measured, said, strict=True):
        if here or missing:
            keep_observations(m, here, missing)


def joint_existing(
    measured: list[Measured],
    found: dict[str, list[tuple[dict, dict[str, np.ndarray]]]],
    study_uid: str,
) -> None:
    """The ACL's and the LCL's own slices as observations of the series they lie in, beside the
    planes `name_the_joint` pointed to: the middle slice's outer neighbour (the ACL) and the coronal
    slice through the fibula's attachment (the LCL) stay valid observations, and the extra planes add
    to them, never replace them. Each is the part's own rule's naming on its slice (resolved where it
    named it itself, laid where its partner did), the artifact the main run saved it in; the record's
    `joint.existing_slices` lists them. Called once the parts are found, so the observations are
    appended after those `name_the_joint` made, earlier rows untouched."""
    by_uid = {m.record["series_uid"]: m for m in measured}
    for part, records in found.items():
        for record, arrays in records:
            own = by_uid.get(record["series_uid"])
            if own is None:
                continue
            code = record["assignments"]["codes"].get(part)
            mask = arrays["a1_objects"] == OBJECT_CODES[part]
            if code not in NAMED or not mask.any():
                continue
            native = code == "identified"
            keep_observations(
                own,
                [
                    observe(
                        part,
                        "native" if native else "laid",
                        "resolved",
                        own,
                        (int(record["slice_index"]),),
                        str(code),
                        int(np.count_nonzero(mask)),
                        0.0 if native else None,
                        "a1_objects",
                        "the part's own slice, its existing rule's naming there (the main run's record): the section on this slice, not the whole part",
                        str(artifact_of(study_uid, record)),
                        None,
                        OBJECT_CODES[part],
                    )
                ],
                [],
            )
            if isinstance(own.record.get("joint"), dict):
                own.record["joint"].setdefault("existing_slices", []).append(
                    {
                        "part": part,
                        "slice": int(record["slice_index"]),
                        "code": str(code),
                        "pixels": int(np.count_nonzero(mask)),
                    }
                )


# -- THE RECESSES: the anterior recess and its lining, the joint fluid, the side recesses' capsule and
# the patellar retinacula ---------------------------------------------------------------------------
# What points here is a squint tile whose MAXIMUM can hold fluid (four times the bones' marrow), read
# only inside the compartment the earlier families located (`knee.collapse.recess`); the existing
# definitions (`anterior_synovial_recess`, `joint_fluid`, `capsule_at_side_recesses`,
# `retinacular_walls`) run only on the planes it points to, on lens readings the earlier families
# already made wherever they read the plane.
RECESS_PARTS = {
    "anterior": (
        ("anterior_synovial_recess", "recess"),
        ("synovium", "lining"),
        ("joint_fluid", "fluid"),
    ),
    "side": (("joint_capsule", "capsule"), ("joint_fluid", "fluid")),
    "retinacula": ((RETINACULA[0], "medial_wall"), (RETINACULA[1], "lateral_wall")),
}
# Why a slice's corridor was not read, by the code kept per slice (`a3_recess_slice_reason`): 0 is a
# slice whose corridor was read (or none was asked for), the rest are named unknowns, never absence.
RECESS_REASONS = (
    "read",
    "patella_measured_absent_there",
    "patella_support_unknown_there",
    "patella_corridor_not_read_there",
    "no_earlier_family_read_it",
    "both_menisci_not_named_there",
    "no_femur_there",
    "patella_not_on_this_slab",
    "femur_not_on_this_slab",
    "interval_empty",
    "corridor_empty_on_this_slice",
)
RECESS_SOURCES = ("patella_plane_row", "joint_plane_row", "read_here", "retinacula_on")
RECESS_NOTES = {
    "anterior_synovial_recess": "the existing recess rule (the largest whole white body behind the patella, in front of the femur and above the patella's lower end) on this plane: the section here, fluid in the named compartment, not the whole synovial compartment",
    "synovium": "the fat-facing half of that body's boundary, sampled on the cavity side: it localizes the lining and measures no membrane thickness; kept apart from the cavity",
    "joint_fluid": "white as fluid (four times the bones' marrow) outside every part named but the joint, in the pieces touching the joint or within 2 mm of a bone: the section here",
    "joint_capsule": "the dark wall outside a side recess, beside it and over its height, on this coronal plane: where the rule reads low signal next to the recess, not the capsule's envelope; a neighbour's band bounds the search, it does not establish the wall",
    RETINACULA[
        0
    ]: "the whole tied minimum band outboard of the selected recess on this axial plane (darker than the recess beside it): the wall's section here, neither its thickness nor its course",
    RETINACULA[
        1
    ]: "the whole tied minimum band outboard of the selected recess on this axial plane (darker than the recess beside it): the wall's section here, neither its thickness nor its course",
}


def plane_places(frame: PlaneFrame, shape: tuple[int, int]) -> np.ndarray:
    """Every pixel's place in the scanner's millimetres, (R, C, 3)."""
    rows, cols = np.indices(shape)
    return frame.to_patient(
        np.column_stack((rows.ravel(), cols.ravel())).astype(float)
    ).reshape(*shape, 3)


@dataclass(frozen=True)
class RecessPlane:
    """One plane the fluid pointer asked for, as the existing definitions read it: its `slice`, whether
    it is the series' `middle` slice (the bootstrap's own naming, not read again), the `kind` of
    compartment (`RECESS_PARTS`), the `code` ("read", "bootstrap", `UNREADABLE_GEOMETRY` or the
    retinacula rule's refusal), what each part's rule said (`codes`, by the part's name), where its
    parts came from (`source`: `RECESS_SOURCES`, and `source_row` the row of the earlier family's
    stack it reused, -1 where none), the part `masks` on the plane's pixels (the white, the cavity, the
    lining, the fluid, the capsule, the retinacula's recess, strip and wall), small readings `values`
    (the wall's per-section minima, the interval), the naming `objects` and the lens's `labels` and
    `available` where this stage read them itself (None where the earlier family's are kept), and
    what pointed here (`asked`)."""

    slice: int
    middle: bool
    kind: str
    code: str
    codes: dict[str, str]
    source: str
    source_row: int
    masks: dict[str, np.ndarray]
    values: dict[str, np.ndarray]
    objects: np.ndarray | None
    labels: np.ndarray | None
    available: np.ndarray | None
    asked: tuple[str, ...]


def recess_blank(
    z: int,
    kind: str,
    code: str,
    asked: tuple[str, ...],
    middle: bool = False,
    codes: dict[str, str] | None = None,
) -> RecessPlane:
    """A plane the stage could not read, or the bootstrap's own: no masks, the code says why."""
    return RecessPlane(
        z, middle, kind, code, codes or {}, "", -1, {}, {}, None, None, None, asked
    )


def recess_anterior_plane(
    own: Measured,
    z: int,
    leg: Leg,
    keys: tuple[str, str],
    patella_rows: dict[int, int],
    asked: tuple[str, ...],
) -> RecessPlane:
    """The anterior recess, its lining and the joint's fluid on ONE pointed sagittal plane of a
    fat-suppressed fluid-sensitive series, by the existing rules: the plane's naming is the patella
    family's own row where it read this plane (`a3_patella_plane_objects`, its lens handed on), else
    `patella_plane` makes it here (the lens made once, counted for this stage); the white is
    `white_as_fluid`, the recess and its fat-facing lining `anterior_synovial_recess`, the fluid the
    plane's own `joint_fluid`. Nothing here is a new definition."""
    series = own.series
    uid = series.row.series_uid
    frame = plane_frame(series, z)
    if isinstance(frame, str):
        return recess_blank(z, "anterior", UNREADABLE_GEOMETRY, asked)
    plane = np.asarray(series.volume[z])
    labels = available = None
    row = patella_rows.get(z, -1)
    if row >= 0:
        reads("patella_plane", ("objects",), "recess")
        objects = np.asarray(own.arrays["a3_patella_plane_objects"][row])
        source = RECESS_SOURCES[0]
    else:
        got = patella_plane(own, z, leg.femur_lps, leg.tibia_lps, keys, None, "recess")
        if got.objects is None:
            return recess_blank(z, "anterior", UNREADABLE_GEOMETRY, asked)
        objects, labels, available = got.objects, got.labels, got.available
        source = RECESS_SOURCES[2]
    measures = measures_of(uid, z, plane, frame)
    femur = objects == OBJECT_CODES["femur"]
    tibia = objects == OBJECT_CODES["tibia"]
    has_patella = bool((objects == OBJECT_CODES["patella"]).any())
    none = np.zeros(plane.shape, dtype=bool)
    white = white_as_fluid(plane, objects, measures)
    recess = lining = none
    if has_patella and femur.any() and white is not None:
        recess, lining = anterior_synovial_recess(
            white, objects, frame.basis_lps, measures
        )
    fluid = objects == OBJECT_CODES["joint_fluid"]
    recess_code = synovium_code(
        True, True, has_patella, bool(femur.any()), bool(recess.any())
    )
    codes = {
        "anterior_synovial_recess": recess_code,
        "synovium": recess_code
        if lining.any() or recess_code != "identified"
        else "abstain_no_fat_facing_surface",
        "joint_fluid": fluid_code(
            True, bool(femur.any() and tibia.any()), bool(fluid.any())
        ),
    }
    handed("recess_plane", ("masks",))
    return RecessPlane(
        z,
        False,
        "anterior",
        "read",
        codes,
        source,
        row,
        {
            "white": none if white is None else white,
            "recess": recess,
            "lining": lining,
            "fluid": fluid,
        },
        {},
        None if row >= 0 else handed_on(objects),
        labels,
        available,
        asked,
    )


def recess_side_plane(
    own: Measured,
    z: int,
    objects: np.ndarray,
    row: int,
    asked: tuple[str, ...],
) -> RecessPlane:
    """The side recesses' capsule and the joint's fluid on ONE pointed coronal plane of a
    fat-suppressed fluid-sensitive series the joint family already read (`objects`, its naming, the
    lens handed on): the white is `white_as_fluid`, the wall `capsule_at_side_recesses` (the largest
    recess outboard of each meniscus, the dark wall outside it) and the fluid
    `fluid_in_the_recesses`, by the existing rules."""
    series, record = own.series, own.record
    uid = series.row.series_uid
    frame = plane_frame(series, z)
    if isinstance(frame, str):
        return recess_blank(z, "side", UNREADABLE_GEOMETRY, asked)
    plane = np.asarray(series.volume[z])
    _, lens, _ = lens_of(
        series, z, plane, frame, float(record["background_split"]), "recess"
    )
    field = field_of(series, z, plane, frame, lens)
    reads("interiors", ("dark", "available"), "recess")
    reads("field", ("leg",), "recess")
    reads("joint_plane", ("objects",), "recess")
    measures = measures_of(uid, z, plane, frame)
    spacing = np.asarray(frame.spacing_rc)
    femur = objects == OBJECT_CODES["femur"]
    tibia = objects == OBJECT_CODES["tibia"]
    menisci = all(
        (objects == OBJECT_CODES[name]).any()
        for name in ("medial_meniscus", "lateral_meniscus")
    )
    none = np.zeros(plane.shape, dtype=bool)
    white = white_as_fluid(plane, objects, measures)
    capsule = fluid = none
    if white is not None and femur.any() and menisci:
        capsule = capsule_at_side_recesses(
            lens.dark, white, objects, frame.basis_lps, spacing, measures
        )
    if white is not None:
        fluid = fluid_in_the_recesses(
            white, objects, field.leg, margin_of(uid, z, plane), spacing, measures
        )
    codes = {
        "joint_capsule": capsule_code(
            True, True, bool(femur.any()), menisci, bool(capsule.any())
        ),
        "joint_fluid": fluid_code(
            True, bool(femur.any() and tibia.any()), bool(fluid.any())
        ),
    }
    handed("recess_plane", ("masks",))
    return RecessPlane(
        z,
        False,
        "side",
        "read",
        codes,
        RECESS_SOURCES[1],
        row,
        {"white": none if white is None else white, "capsule": capsule, "fluid": fluid},
        {},
        None,
        None,
        None,
        asked,
    )


def recess_axial_plane(
    own: Measured,
    z: int,
    leg: Leg,
    thick: list[float],
    knee: str,
    asked: tuple[str, ...],
) -> RecessPlane:
    """Both patellar retinacula on ONE axial plane, by the existing rule on its own plane
    (`retinacula_on`: the lens made once per slice, the carried patella and femur on it, the white,
    the recess either side of the patella, the outboard minimum band). Its refusal is the plane's
    code, and what it read of the white and the carried places stays with it."""
    got = retinacula_on(own, leg, z, thick, knee, "recess")
    if isinstance(got, str):
        return recess_blank(z, "retinacula", got, asked)
    record, arrays, _ = got
    names = {"positive_inner": RETINACULA[0], "negative_inner": RETINACULA[1]}
    masks = {
        "white": arrays["a2_retinacula_white"],
        "patella": arrays["a2_retinacula_carried_patella"],
        "femur": arrays["a2_retinacula_carried_femur"],
        "interval": arrays["a2_retinacula_posterior_interval"],
    }
    values: dict[str, np.ndarray] = {
        "interval_bounds_mm": arrays["a2_retinacula_posterior_interval_bounds_mm"],
        "femur_peak_depth_mm": arrays["a2_retinacula_femur_peak_depth_mm"],
    }
    for side, name in names.items():
        wall = "medial_wall" if name == RETINACULA[0] else "lateral_wall"
        stem = wall.removesuffix("_wall")
        masks[f"{stem}_recess"] = arrays[f"a2_retinacula_{side}_selected_recess"]
        masks[f"{stem}_strip"] = arrays[f"a2_retinacula_{side}_strip"]
        masks[wall] = arrays[f"a2_{name}"]
        for key in ("row_minimum", "adjacent_white_median", "row_status"):
            values[f"{stem}_{key}"] = arrays[f"a2_retinacula_{side}_{key}"]
    codes = {name: str(record["assignments"]["codes"][name]) for name in names.values()}
    handed("recess_plane", ("masks",))
    return RecessPlane(
        z,
        False,
        "retinacula",
        "read",
        codes,
        RECESS_SOURCES[3],
        -1,
        masks,
        values,
        None,
        arrays["b1_labels"],
        arrays["b1_available"],
        asked,
    )


@dataclass(frozen=True)
class RecessTwin:
    """What the other sequence's slice through one pointed plane holds of the plane's parts: the
    twin's `slice` (None where it has none), the `code` ("read", or why not: an unknown, never an
    absence), the part masks laid onto the twin's own pixels (`masks`) and the distance of their
    places from the twin's plane (`off_mm`). No lens is read on the twin."""

    slice: int | None
    code: str
    masks: dict[str, np.ndarray] | None
    off_mm: float | None


def recess_twin(
    own: Measured, twin: Measured | None, plane: RecessPlane, parts: tuple[str, ...]
) -> RecessTwin:
    """The named parts' masks of a pointed plane (`parts`: mask names) laid onto the other sequence's
    slice through the same place, by the scanner's millimetres (never equal indices: `slice_through`)
    and the pair's one match of places (`matched`); the places the twin never saw hold nothing laid
    on them. Every failure is a code."""
    if twin is None:
        return RecessTwin(None, "none_of_the_other_sequence", None, None)
    other = twin.series
    thick, why = slab_thicknesses(other)
    if why is not None:
        return RecessTwin(None, why, None, None)
    frame = plane_frame(own.series, plane.slice)
    if isinstance(frame, str):
        return RecessTwin(None, frame, None, None)
    origins = np.asarray([np.asarray(p, dtype=float) for p in other.geometry.position])
    index = slice_through(frame.origin_lps, origins, twin.frame.normal(), thick)
    if index is None:
        return RecessTwin(None, "twin_has_no_slice_at_this_place", None, None)
    twin_frame = plane_frame(other, index)
    if isinstance(twin_frame, str):
        return RecessTwin(index, twin_frame, None, None)
    uid, twin_uid = own.series.row.series_uid, other.row.series_uid
    plane_there = np.asarray(other.volume[index])
    forward = matched(
        other,
        {"series_uid": twin_uid, "slice_index": index},
        twin_frame,
        plane_there.shape,
        {"series_uid": uid, "slice_index": plane.slice},
        frame,
        np.asarray(own.series.volume[plane.slice]),
    )
    if isinstance(forward, str):
        return RecessTwin(index, forward, None, None)
    reads("recess_plane", ("masks",), "recess_twin")
    seen = finite_of(other)[index]
    laid = {
        name: (laid_by(plane.masks[name].astype(np.int16), forward) == 1) & seen
        for name in parts
        if name in plane.masks
    }
    points = [
        frame.to_patient(np.argwhere(plane.masks[name]).astype(float))
        for name in parts
        if name in plane.masks and plane.masks[name].any()
    ]
    places = np.concatenate(points) if points else np.empty((0, 3))
    off = (
        float(abs((places.mean(axis=0) - twin_frame.origin_lps) @ twin_frame.normal()))
        if len(places)
        else None
    )
    return RecessTwin(index, "read", laid, off)


@dataclass(frozen=True)
class RecessRead:
    """The recess family in one series, as `read_recess` read it: the `kind` of compartment, the
    `profile` of the fluid pointer through depth, the `planes` it pointed to (the middle slice's
    bootstrap among them where it was), the twin's laying beside each plane but the middle one
    (`twins`), how it came out (`outcome`), the record's description (`record`, plain data) and the
    arrays it keeps on the series (`arrays`)."""

    kind: str
    profile: JointProfile
    planes: tuple[RecessPlane, ...]
    twins: tuple[RecessTwin | None, ...]
    outcome: str
    record: dict
    arrays: dict[str, np.ndarray]


def patella_sections_lps(own: Measured) -> list[np.ndarray]:
    """The places of every section of the patella the patella family named on this series: the
    middle slice's own naming and each pointed plane that identified it, each in the scanner's
    millimetres (one array per section). Empty when none was named."""
    sections: list[np.ndarray] = []
    codes = own.record["assignments"]["codes"]
    middle = own.arrays["a1_objects"] == OBJECT_CODES["patella"]
    if codes.get("patella") in NAMED and middle.any():
        sections.append(own.frame.to_patient(np.argwhere(middle).astype(float)))
    rows = [p for p in own.record["patella"]["pointed_planes"] if not p["middle"]]
    stack = own.arrays.get("a3_patella_plane_objects")
    for row, p in enumerate(rows):
        frame = plane_frame(own.series, int(p["slice"]))
        if p["code"] != "identified" or stack is None or isinstance(frame, str):
            continue
        mask = stack[row] == OBJECT_CODES["patella"]
        if mask.any():
            sections.append(frame.to_patient(np.argwhere(mask).astype(float)))
    return sections


def recess_corridor(
    own: Measured,
    kind: str,
    leg: Leg,
    patella_centre: np.ndarray | None,
    why: np.ndarray,
) -> tuple[Callable[[int, PlaneFrame, tuple[int, int]], np.ndarray], dict] | str:
    """The compartment the fluid pointer is read in, by the relation the existing definition states
    for it, from parts the earlier families located: `own_reach` for `joint_profile` (slice, frame,
    shape -> the pixels where it can lie there) and the landmarks it was read by; or why the
    compartment is not located here (a code, never an absence). `why` receives, for each slice no
    corridor was read on, the index into `RECESS_REASONS`."""
    reason = {name: i for i, name in enumerate(RECESS_REASONS)}
    if kind == "anterior":
        info = own.record.get("patella")
        status = own.arrays.get("a3_patella_profile_status")
        if not isinstance(info, dict) or "pointed_planes" not in info or status is None:
            return "abstain_patella_not_profiled"
        sections = patella_sections_lps(own)
        if not sections:
            return "abstain_no_patella_section_named"
        femur = leg.femur_lps[np.isfinite(leg.femur_lps).all(axis=1)]
        if not len(femur):
            return "abstain_no_femur_carried"
        back = float(min(np.median(s[:, 1]) for s in sections))
        low = float(min(s[:, 2].min() for s in sections))
        femur_back = float(np.median(femur[:, 1]))
        marks = FIBULA_POINTER_STATUS

        def anterior(z: int, frame: PlaneFrame, shape: tuple[int, int]) -> np.ndarray:
            held = int(status[z])
            if held in (marks["body"], marks["cut"]):
                return anterior_pocket(
                    plane_places(frame, shape), back, femur_back, low
                )
            why[z] = reason[
                "patella_measured_absent_there"
                if held == marks["none"]
                else "patella_support_unknown_there"
                if held == marks["unreadable"]
                else "patella_corridor_not_read_there"
            ]
            return np.zeros(shape, dtype=bool)

        return anterior, {
            "patella_back_y_mm": back,
            "patella_lowest_z_mm": low,
            "femur_back_y_mm": femur_back,
            "patella_sections": len(sections),
            "frame": "the scanner's LPS millimetres: y toward the back, z toward the head",
        }
    if kind == "side":
        stack = own.arrays.get("a3_joint_plane_objects")
        joint = own.record.get("joint")
        if (
            stack is None
            or not isinstance(joint, dict)
            or "pointed_planes" not in joint
        ):
            return "abstain_joint_not_read"
        both = ("medial_meniscus", "lateral_meniscus")
        located: dict[int, np.ndarray] = {}
        middle = own.arrays["a1_objects"]
        if all((middle == OBJECT_CODES[n]).any() for n in both):
            located[int(own.record["slice_index"])] = middle
        rows = [p for p in joint["pointed_planes"] if not p["middle"]]
        read_rows = {int(p["slice"]) for p in rows}
        for row, p in enumerate(rows):
            if (
                p["code"] == "read"
                and p.get("bones_identified_at_this_place") is True
                and all((stack[row] == OBJECT_CODES[n]).any() for n in both)
            ):
                located[int(p["slice"])] = np.asarray(stack[row])
        if not located:
            return "abstain_no_plane_names_both_menisci"

        def side(z: int, frame: PlaneFrame, shape: tuple[int, int]) -> np.ndarray:
            objects = located.get(z)
            if objects is None:
                why[z] = reason[
                    "both_menisci_not_named_there"
                    if z in read_rows
                    else "no_earlier_family_read_it"
                ]
                return np.zeros(shape, dtype=bool)
            places = plane_places(frame, shape)
            first = objects == OBJECT_CODES[both[0]]
            second = objects == OBJECT_CODES[both[1]]
            femur = objects == OBJECT_CODES["femur"]
            if not femur.any():
                why[z] = reason["no_femur_there"]
                return np.zeros(shape, dtype=bool)
            held = gutter_landmarks(
                places[first][:, 0],
                places[second][:, 0],
                places[first][:, 2],
                places[second][:, 2],
            )
            span = places[femur][:, 0]
            if held is None or not np.isfinite(span).any():
                why[z] = reason["corridor_empty_on_this_slice"]
                return np.zeros(shape, dtype=bool)
            return side_gutters(
                places,
                held[0],
                held[1],
                (float(np.nanmin(span)), float(np.nanmax(span))),
            )

        return side, {
            "slices_naming_both_menisci": sorted(located),
            "slices_the_joint_family_read": sorted(read_rows),
            "frame": "the scanner's LPS millimetres: x toward the left, z toward the head",
        }
    chosen = retinacula_z(own, leg, patella_centre)
    if isinstance(chosen, str):
        return chosen
    _, thick, _ = chosen
    patella_points = np.asarray(leg.patella_lps, dtype=np.float64)
    femur_points = np.asarray(leg.femur_lps, dtype=np.float64)

    def axial(z: int, frame: PlaneFrame, shape: tuple[int, int]) -> np.ndarray:
        half = thick[z] / 2.0
        mine = patella_points[
            np.abs((patella_points - frame.origin_lps) @ frame.normal()) <= half
        ]
        theirs = femur_points[
            np.abs((femur_points - frame.origin_lps) @ frame.normal()) <= half
        ]
        mine = mine[np.isfinite(mine).all(axis=1)]
        theirs = theirs[np.isfinite(theirs).all(axis=1)]
        if not len(mine):
            why[z] = reason["patella_not_on_this_slab"]
            return np.zeros(shape, dtype=bool)
        if not len(theirs):
            why[z] = reason["femur_not_on_this_slab"]
            return np.zeros(shape, dtype=bool)
        reach = patellofemoral_interval(
            plane_places(frame, shape),
            float(mine[:, 1].mean()),
            float(np.median(theirs[:, 1])),
            (float(theirs[:, 0].min()), float(theirs[:, 0].max())),
        )
        if not reach.any():
            why[z] = reason["interval_empty"]
        return reach

    return axial, {
        "frame": "the scanner's LPS millimetres: x toward the left, y toward the back",
        "bootstrap_slice": int(chosen[0]),
    }


def recess_says(plane: RecessPlane, middle_codes: dict[str, str]) -> str:
    """What the existing rules said of one plane read for the fluid: "confirmed" (some part was
    named), "rejected" (read, nothing named) or "not_read" (the plane is a bootstrap's own, whose
    stage is not run again here and whose naming is read from its codes where it has them)."""
    codes = plane.codes if not plane.middle else middle_codes
    if plane.middle and not codes:
        return "not_read"
    if any(code == "identified" for code in codes.values()):
        return "confirmed"
    return "not_read" if plane.middle else "rejected"


def stacked(
    rows: list[dict[str, np.ndarray]], key: str, shape: tuple[int, ...], dtype: Any
) -> np.ndarray:
    """One named reading of each row of a stack, (n, ...): a row without it is zero (NaN for a
    float), never a copy of another's."""
    blank = (
        np.full(shape, np.nan)
        if np.dtype(dtype).kind == "f"
        else np.zeros(shape, dtype)
    )
    return (
        np.stack([np.asarray(r.get(key, blank), dtype=dtype) for r in rows])
        if rows
        else np.empty((0, *shape), dtype=dtype)
    )


def recess_arrays(
    own: Measured,
    kind: str,
    profile: JointProfile,
    planes: list[RecessPlane],
    pointed: list[int],
    runs: list[tuple[int, int]],
    origins: np.ndarray,
    offsets: np.ndarray,
    sound: bool,
    thick: np.ndarray,
    why: np.ndarray,
) -> dict[str, np.ndarray]:
    """What the recess family keeps in the series' own middle arrays, named `a3_recess_*`: the fluid
    pointer's status and area through depth, the tiles that could hold the level, its runs with their
    ends and envelopes, the corridor's pixels and tiles, the finer readings at their own resolution
    (ragged, nothing padded), why each slice's corridor was not read, the pointed slices' places along
    the stack's normal; and, one row per pointed plane but the bootstrap's own, the plane's slice, the
    stack it reused or `read_here` (`a3_recess_plane_source`, `_source_row`), every part mask and small
    reading as a stack, and the naming and lens this stage read itself (`_objects`, `_labels`,
    `_available`, with the rows `_objects_row`, `_lens_row`; -1 where the earlier family's are kept)."""
    shape = np.shape(own.arrays["acquired_plane"])
    rows_in = [p for p in planes if not p.middle]
    pointed_origin = origins[pointed] if sound and pointed else np.empty((0, 3))
    at = profile.level[FLUID]
    _, ends, spans = describe_runs(runs, profile.status[FLUID], offsets, thick, sound)
    arrays: dict[str, np.ndarray] = {
        "a3_recess_profile_status": profile.status[FLUID],
        "a3_recess_profile_area_mm2": profile.area_mm2[FLUID],
        "a3_recess_profile_could_tiles": profile.could[FLUID],
        "a3_recess_profile_level": np.asarray(
            (np.nan, np.nan) if at is None else at, dtype=np.float64
        ),
        "a3_recess_corridor_px": profile.corridor_px,
        "a3_recess_corridor_tiles": profile.corridor,
        "a3_recess_seen_blocks": profile.seen_blocks,
        "a3_recess_unseen_blocks": profile.unseen_blocks,
        "a3_recess_profile_window_rc": profile.window_rc,
        "a3_recess_profile_block_mm": profile.cell_mm,
        "a3_recess_profile_block_px": profile.block_px,
        "a3_recess_pointer_runs": np.asarray(runs, dtype=np.int32).reshape(-1, 2),
        "a3_recess_pointer_run_ends": ends.astype(np.int32),
        "a3_recess_pointer_run_envelope_mm": spans,
        "a3_recess_slice_reason": why,
        "a3_recess_depth_offsets_mm": offsets,
        "a3_recess_slice_thickness_mm": thick,
        "a3_recess_pointed_slices": np.asarray(pointed, dtype=np.int32),
        "a3_recess_pointed_origin_lps": pointed_origin,
        "a3_recess_pointed_position_mm": offsets[pointed]
        if sound and pointed
        else np.empty(0),
        "a3_recess_source_normal_lps": own.frame.normal(),
    }
    for name, value in pack_fine_readings(profile.fine).items():
        if name != "tibia_reference":
            arrays[
                f"a3_recess_fine_{'reach_blocks' if name == 'pointer_body' else name}"
            ] = value
    arrays["a3_recess_plane_slices"] = np.asarray(
        [p.slice for p in rows_in], dtype=np.int32
    )
    arrays["a3_recess_plane_source"] = np.asarray(
        [RECESS_SOURCES.index(p.source) if p.source else -1 for p in rows_in],
        dtype=np.int8,
    )
    arrays["a3_recess_plane_source_row"] = np.asarray(
        [p.source_row for p in rows_in], dtype=np.int32
    )
    mask_names = sorted({n for p in rows_in for n in p.masks})
    for n in mask_names:
        arrays[f"a3_recess_plane_{n}"] = stacked(
            [p.masks for p in rows_in], n, shape, bool
        )
    value_names = sorted({n for p in rows_in for n in p.values})
    for n in value_names:
        first = next(p.values[n] for p in rows_in if n in p.values)
        arrays[f"a3_recess_plane_value_{n}"] = stacked(
            [p.values for p in rows_in],
            n,
            np.shape(first),
            np.asarray(first).dtype,
        )
    objects_rows = [p for p in rows_in if p.objects is not None]
    lens_rows = [p for p in rows_in if p.labels is not None]
    arrays["a3_recess_plane_objects_row"] = np.asarray(
        [objects_rows.index(p) if p in objects_rows else -1 for p in rows_in],
        dtype=np.int32,
    )
    arrays["a3_recess_plane_lens_row"] = np.asarray(
        [lens_rows.index(p) if p in lens_rows else -1 for p in rows_in], dtype=np.int32
    )
    arrays["a3_recess_plane_objects"] = (
        np.stack([np.asarray(p.objects) for p in objects_rows])
        if objects_rows
        else np.empty((0, *shape), dtype=np.int8)
    )
    arrays["a3_recess_plane_labels"] = (
        np.stack([np.asarray(p.labels) for p in lens_rows])
        if lens_rows
        else np.empty((0, *shape), dtype=np.int32)
    )
    arrays["a3_recess_plane_available"] = (
        np.stack([np.asarray(p.available, dtype=bool) for p in lens_rows])
        if lens_rows
        else np.empty((0, *shape), dtype=bool)
    )
    return arrays


def read_recess(
    own: Measured,
    partner: Measured | None,
    leg: Leg,
    patella_centre: np.ndarray | None,
    feed: dict[str, int | None],
) -> RecessRead | str:
    """The fluid of one fat-suppressed fluid-sensitive series through the whole depth: the pointer
    (`joint_profile` over the compartment the earlier families located, `recess_corridor`: the
    squint tiles whose maximum can hold fluid, then the 2 mm blocks that read it), each run's pointed
    planes (the maximum of each run, every tie, every run, and the slice beside a maximum that was
    unreadable: `positive_runs`, `run_maxima`, `confirmations`), and on only those planes the
    existing rules (`recess_anterior_plane` on a sagittal series, `recess_side_plane` on a coronal one,
    `recess_axial_plane` on an axial one), with the plane's parts laid onto the twin's slice of the
    same place (`recess_twin`); the series' bootstrap slice is not read again. `feed` is the axial
    slice the patella family's extent-based centre selects, per series: an axial series reads it too
    where it is not the bootstrap's (an additional plane, never a replacement). Or why the series
    cannot be read: a string code, an unknown and never an absence."""
    series, record = own.series, own.record
    uid = series.row.series_uid
    reads("series", ("row",), "recess")
    if not (
        int(series.row.fat_suppression) == 1 and int(series.row.fluid_sensitive) == 1
    ):
        return "abstain_fluid_not_bright_on_this_sequence"
    sides, front, along = own.assignment.in_plane
    kind = (
        "anterior"
        if front and along
        else "side"
        if sides and along
        else "retinacula"
        if not along
        else ""
    )
    if not kind:
        return "abstain_plane_not_read_by_a_relation"
    reads("squint_stack", ("code",), "recess")
    if own.stack.code != "present":
        return f"squint_{own.stack.code}"
    if series.volume is None:
        return "no_stacked_volume"
    index = record["slice_index"]
    objects = own.arrays["a1_objects"]
    femur_mask = objects == OBJECT_CODES["femur"]
    tibia_mask = objects == OBJECT_CODES["tibia"]
    measures = measures_of(uid, index, own.arrays["acquired_plane"], own.frame)
    if kind == "retinacula":
        if not len(leg.femur_lps):
            return "no_carried_places"
        thick_here, why_not = slab_thicknesses(series)
        if why_not is not None:
            return why_not
        femur_on, _ = leg_on(
            leg, series, index, own.frame, femur_mask.shape, thick_here[index]
        )
        anchored = femur_on & own.arrays["b1_available"]
        femur_light = (
            float(measures.light(anchored)) if anchored.any() else float("nan")
        )
        bones_light = femur_light
    else:
        assigned = record["assignments"]
        if (
            assigned["femur"] is None
            or assigned["tibia"] is None
            or not (femur_mask.any() and tibia_mask.any())
        ):
            return "bones_not_named_on_the_middle_slice"
        femur_light = float(measures.light(femur_mask))
        bones_light = float(measures.light(femur_mask | tibia_mask))
    depth = len(series.volume)
    why = np.zeros(depth, dtype=np.int8)
    got = recess_corridor(own, kind, leg, patella_centre, why)
    if isinstance(got, str):
        return got
    own_reach, landmarks = got
    level = levels(float(record["background_split"]), femur_light, bones_light)
    profile = joint_profile(
        series,
        own.stack,
        np.empty((0, 3)),
        np.empty((0, 3)),
        {FLUID: level[FLUID]},
        (FLUID,),
        own_reach,
        "recess",
    )
    reads("recess_profile", ("status", "area_mm2"), "recess")
    status = profile.status[FLUID]
    # a slice whose corridor was empty without a named reason says so
    empty = RECESS_REASONS.index("corridor_empty_on_this_slice")
    why[(status == JOINT_NOT_READ) & (why == 0)] = empty
    runs = positive_runs(profile.area_mm2[FLUID])
    maxima = run_maxima(profile.area_mm2[FLUID], runs)
    confirm = confirmations(runs, maxima, status, (JOINT_UNREADABLE,))
    ledger.record("recess.unread_slices", planes=int(np.count_nonzero(why)))
    asked_by: dict[int, list[str]] = {}
    for z in {int(z) for peaks in maxima for z in peaks} | set(confirm):
        asked_by.setdefault(z, []).append("fluid")
    bootstrap = index
    thick_values: list[float] = []
    knee = str(record["assignments"]["knee"])
    if kind == "retinacula":
        chosen = retinacula_z(own, leg, patella_centre)
        if isinstance(chosen, str):
            return chosen
        bootstrap, thick_values, knee = chosen
        reads("patella", ("retinacula_feed",), "recess")
        wider = feed.get(uid)
        if wider is not None and wider != bootstrap:
            asked_by.setdefault(int(wider), []).append("patella_extent_centre")
    pointed = sorted(asked_by)
    ledger.record("recess.pointed_planes", planes=len(pointed))
    keys = (digest(leg.femur_lps), digest(leg.tibia_lps))
    patella_rows: dict[int, int] = {}
    side_rows: dict[int, int] = {}
    if kind == "anterior":
        for row, p in enumerate(
            p for p in record["patella"]["pointed_planes"] if not p["middle"]
        ):
            patella_rows[int(p["slice"])] = row
    if kind == "side":
        for row, p in enumerate(
            p for p in record["joint"]["pointed_planes"] if not p["middle"]
        ):
            side_rows[int(p["slice"])] = row
    planes: list[RecessPlane] = []
    twins: list[RecessTwin | None] = []
    parts = tuple(name for _, name in RECESS_PARTS[kind])
    for z in pointed:
        asked = tuple(asked_by[z])
        if z == bootstrap:
            planes.append(recess_blank(z, kind, "bootstrap", asked, True))
            continue
        if kind == "anterior":
            got_plane = recess_anterior_plane(own, z, leg, keys, patella_rows, asked)
        elif kind == "side":
            stack = own.arrays["a3_joint_plane_objects"]
            row = side_rows.get(z, -1)
            got_plane = (
                recess_side_plane(own, z, np.asarray(stack[row]), row, asked)
                if row >= 0
                else recess_blank(z, kind, "no_earlier_family_read_it", asked)
            )
        else:
            got_plane = recess_axial_plane(own, z, leg, thick_values, knee, asked)
        planes.append(got_plane)
        twins.append(
            recess_twin(own, partner, got_plane, parts)
            if got_plane.code == "read" and kind != "retinacula"
            else None
        )
    origins, thick, offsets, sound = series_depth(series, own.frame, index)
    middle_codes = {
        name: str(record["assignments"]["codes"].get(name, ""))
        for name, _ in RECESS_PARTS[kind]
    }
    if kind == "retinacula":
        middle_codes = {}
    read_by = {p.slice: p for p in planes}
    described, _, _ = describe_runs(runs, status, offsets, thick, sound)
    for i, ((a, b), peaks) in enumerate(zip(runs, maxima, strict=True)):
        here = sorted(
            {int(z) for z in peaks} | {int(z) for z in confirm if z in (a - 1, b)}
        )
        said = [recess_says(read_by[z], middle_codes) for z in here]
        described[i]["planes_read_for_it"] = here
        described[i]["native_rule"] = (
            "confirmed_by_the_native_rule"
            if "confirmed" in said
            else "rejected_by_the_native_rule"
            if "rejected" in said
            else "not_read_natively"
        )
    rows_in = [p for p in planes if not p.middle]
    twin_of = {id(p): t for p, t in zip(rows_in, twins, strict=True)}
    pointed_rows = []
    for p in planes:
        row_record: dict[str, Any] = {
            "slice": p.slice,
            "middle": p.middle,
            "pointed_by": list(p.asked),
            "code": p.code,
            "codes": dict(p.codes),
            "source": p.source or None,
            "source_row": p.source_row if p.source_row >= 0 else None,
            "position_mm": finite_or_none(offsets[p.slice]) if sound else None,
            "parts_pixels": {
                name: int(np.count_nonzero(p.masks[name]))
                for name in (*parts, "white")
                if name in p.masks and np.count_nonzero(p.masks[name])
            },
        }
        if not p.middle:
            twin = twin_of[id(p)]
            row_record["twin"] = (
                None
                if twin is None
                else {"slice": twin.slice, "code": twin.code, "off_mm": twin.off_mm}
            )
        pointed_rows.append(row_record)
    outcome = (
        "read"
        if pointed
        else "unreadable"
        if (status == JOINT_UNREADABLE).any()
        else "no_support_found"
    )
    ambiguities = [
        "a_tile_maximum_points_it_never_names_a_pocket_and_the_blocks_that_read_the_level_are_support_not_a_name",
        "the_corridor_is_the_relation_the_existing_definition_states_read_on_the_carried_places_an_upper_bound_never_a_section",
        "a_neighbours_band_bounds_the_search_for_a_thin_wall_it_does_not_establish_the_wall_throughout_the_band",
    ]
    if any(profile.unseen_blocks > 0):
        ambiguities.append("blocks_never_seen_make_an_area_a_lower_bound")
    if (status == JOINT_UNREADABLE).any():
        ambiguities.append("slices_the_profile_could_not_read_are_unknown_not_empty")
    if np.count_nonzero(why):
        ambiguities.append(
            "slices_whose_corridor_was_not_read_are_unknown_not_empty_see_slice_reason"
        )
    if not sound:
        ambiguities.append("slice_geometry_unsound_so_no_physical_depth")
    names = {value: key for key, value in FIBULA_POINTER_STATUS.items()}
    record_part = {
        "kind": kind,
        "outcome": outcome,
        "points_at": "tiles whose maximum can hold fluid (four times the bones' marrow), then 2 mm blocks that read it, inside the compartment the earlier families located",
        "level": None
        if level[FLUID] is None
        else [None if np.isinf(v) else float(v) for v in level[FLUID]],
        "block_mm": float(LIGAMENT_SMOOTH_MM),
        "status": {
            names[int(c)]: int(np.count_nonzero(status == c)) for c in np.unique(status)
        },
        "reasons_not_read": {
            RECESS_REASONS[int(c)]: int(np.count_nonzero(why == c))
            for c in np.unique(why)
            if c
        },
        "reason_codes": list(RECESS_REASONS),
        "source_codes": list(RECESS_SOURCES),
        "corridor": landmarks,
        "pointer_runs": described,
        "pointer_representatives": [[int(z) for z in peaks] for peaks in maxima],
        "confirmed_slices": [int(z) for z in confirm],
        "unknown_slices": [int(z) for z in np.flatnonzero(status == JOINT_UNREADABLE)],
        "pointed_planes": pointed_rows,
        "ambiguities": ambiguities,
        "status_codes": dict(FIBULA_POINTER_STATUS),
    }
    if kind == "retinacula":
        record_part["bootstrap_slice"] = int(bootstrap)
        record_part["patella_extent_centre_slice"] = feed.get(uid)
    arrays = recess_arrays(
        own, kind, profile, planes, pointed, runs, origins, offsets, sound, thick, why
    )
    handed("recess", ("pointed", "planes", "twins"))
    return RecessRead(
        kind, profile, tuple(planes), tuple(twins), outcome, record_part, arrays
    )


def recess_twin_arrays(
    twin: Measured,
    planes: list[RecessPlane],
    twins: list[RecessTwin | None],
    prefix: str,
    parts: tuple[str, ...],
) -> dict[str, np.ndarray]:
    """What the twin's slices through the pointed planes hold of the planes' parts, as stacks on the
    twin's own pixels, named `<prefix>_*`, one row per plane whose twin was read: the plane's slice
    (`from_slices`), the twin's (`slices`) and each part's mask. (The prefix names the series that
    asked, so two sequences asking one twin never overwrite each other.)"""
    shape = np.shape(twin.arrays["acquired_plane"])
    rows = [
        (p, t)
        for p, t in zip(planes, twins, strict=True)
        if t is not None and t.code == "read"
    ]
    found: dict[str, np.ndarray] = {
        f"{prefix}_from_slices": np.asarray([p.slice for p, _ in rows], dtype=np.int32),
        f"{prefix}_slices": np.asarray(
            [-1 if t.slice is None else t.slice for _, t in rows], dtype=np.int32
        ),
    }
    for name in parts:
        found[f"{prefix}_{name}"] = stack_of(
            [
                t.masks[name]
                if t.masks is not None and name in t.masks
                else np.zeros(shape, bool)
                for _, t in rows
            ],
            shape,
            bool,
        )
    return found


def retinacula_centre(
    measured: list[Measured], patella_centre: np.ndarray | None
) -> np.ndarray | None:
    """The place the axial retinacula slice is chosen through: the centre of every patella section
    the patella family named across planes (`retinacula_feed`, kept on the record that made it),
    else the first identification's centre. The retinacula's own rules still decide on that slice."""
    for m in measured:
        info = m.record.get("patella")
        for entry in (
            (info.get("retinacula_feed") or []) if isinstance(info, dict) else []
        ):
            reads("patella", ("retinacula_feed",), "patellar_retinacula")
            return np.asarray(entry["centre_of_every_section_lps"], dtype=float)
    return patella_centre


def recess_feed(measured: list[Measured]) -> dict[str, int | None]:
    """The axial slice the patella family's extent-based centre selects, for each axial series it
    named (`record["patella"]["retinacula_feed"]`, the first series that holds one): read by the
    recess family as an additional plane, never in place of the retinacula stage's own slice."""
    found: dict[str, int | None] = {}
    for m in measured:
        info = m.record.get("patella")
        entries = info.get("retinacula_feed") if isinstance(info, dict) else None
        for entry in entries or []:
            for axial in entry.get("axial", []):
                if "slice_from_every_section" in axial:
                    found.setdefault(
                        axial["series_uid"], axial["slice_from_every_section"]
                    )
        if found:
            break
    return found


def name_the_recess(
    measured: list[Measured],
    partners: list[Measured | None],
    leg: Leg | None,
    patella_centre: np.ndarray | None,
    study_uid: str,
) -> list[tuple[list[Observation], list[Unresolved]]]:
    """The anterior recess and its lining, the joint's fluid, the side recesses' capsule and the
    patellar retinacula through the stacks (`read_recess`) of every fat-suppressed fluid-sensitive
    series, kept in the series' own middle records and arrays (saved by the caller) beside the
    observations the earlier families made.

    Native: the middle slice's own naming of each part (the bootstrap), each part on each pointed
    plane where its existing rule names it (resolved, one row of the `a3_recess_plane_*` stacks), and a
    rule that read a pointed plane and named nothing (a reading with its code, never an absence), and
    the pointer's support through depth (a reading: no boundary, no name). Laid: each pointed plane's
    parts onto the other sequence's slice of the same place (`recess_twin`, `<prefix>_<part>` of the
    twin). Projected: each part's largest section onto the slice of every other series nearest it (a
    target for a native question, never a boundary). The cavity, its lining, the fluid, the capsule
    and each retinaculum are separate objects with separate decisions. What could not be said is an
    `Unresolved` with its code: a part no pointed plane named, a slice whose compartment no earlier
    family located, a series whose sequence does not show fluid, is unknown and never absent. The
    profile and every plane are kept; the one thing read downstream is the patella family's
    extent-based centre (`retinacula_feed`), which adds an axial plane and replaces nothing. The
    observations are returned per series, in the order of `measured`, for `keep_recess` to append
    once the ACL's and the LCL's own slices are, so every earlier row stays an unchanged prefix."""
    carried = leg if leg is not None else leg_of(measured)
    feed = recess_feed(measured)
    results = [
        read_recess(own, partners[i], carried, patella_centre, feed)
        for i, own in enumerate(measured)
    ]
    where = {id(m): i for i, m in enumerate(measured)}
    said: list[tuple[list[Observation], list[Unresolved]]] = [
        ([], []) for _ in measured
    ]
    for i, own in enumerate(measured):
        read = results[i]
        uid, view = own.record["series_uid"], tuple(own.record["view"])
        here, missing = said[i]
        artifact = str(artifact_of(study_uid, own.record))
        if isinstance(read, str):
            own.record["recess"] = {"code": read}
            missing.append(Unresolved("recess", "native", uid, view, read))
            continue
        partner = partners[i]
        at = None if partner is None else where[id(partner)]
        index = own.record["slice_index"]
        codes = own.record["assignments"]["codes"]
        kind = read.kind
        parts = RECESS_PARTS[kind]
        mask_names = tuple(mask for _, mask in parts)
        rows_in = [p for p in read.planes if not p.middle]
        twins = list(read.twins)
        own.arrays.update(read.arrays)
        prefix = "a3_recess_twin"
        if partner is not None and kind != "retinacula":
            prefix = source_prefix(prefix, partner.arrays, uid)
            partner.arrays.update(
                recess_twin_arrays(partner, rows_in, twins, prefix, mask_names)
            )
        twin_artifact = (
            str(artifact_of(study_uid, partner.record)) if partner is not None else ""
        )
        got: set[str] = set()
        reason: dict[str, set[str]] = {name: set() for name, _ in parts}
        sections: dict[
            str, list[tuple[int, np.ndarray, PlaneFrame, str, int | None]]
        ] = {name: [] for name, _ in parts}
        # the series' bootstrap: the middle slice's own naming (the retinacula's own slice is read
        # by its stage, after this one, and joins the observations then: `recess_existing`)
        if kind != "retinacula":
            middle = own.arrays["a1_objects"]
            for name, _ in parts:
                code = codes.get(name)
                reason[name].add(str(code))
                held = (
                    middle == OBJECT_CODES[name]
                    if name == "joint_fluid"
                    else own.arrays.get(f"a2_{name}")
                )
                if code not in NAMED or held is None or not np.any(held):
                    continue
                got.add(name)
                native = code == "identified"
                here.append(
                    observe(
                        name,
                        "native" if native else "laid",
                        "resolved",
                        own,
                        (index,),
                        str(code),
                        int(np.count_nonzero(held)),
                        0.0 if native else None,
                        "a1_objects" if name == "joint_fluid" else f"a2_{name}",
                        "the middle slice's own naming (the bootstrap): the section on this slice, not the whole part",
                        artifact,
                        None,
                        OBJECT_CODES[name] if name == "joint_fluid" else None,
                    )
                )
                sections[name].append(
                    (
                        index,
                        np.asarray(held, dtype=bool),
                        own.frame,
                        "a1_objects" if name == "joint_fluid" else f"a2_{name}",
                        None,
                    )
                )
        twin_row = 0
        for row, (p, t) in enumerate(zip(rows_in, twins, strict=True)):
            if p.code != "read":
                missing.append(Unresolved("recess", "native", uid, view, p.code))
                continue
            frame = plane_frame(own.series, p.slice)
            for name, mask_name in parts:
                code = p.codes.get(name, "")
                reason[name].add(str(code))
                mask = p.masks.get(mask_name)
                count = 0 if mask is None else int(np.count_nonzero(mask))
                if code == "identified" and count:
                    got.add(name)
                    here.append(
                        observe(
                            name,
                            "native",
                            "resolved",
                            own,
                            (p.slice,),
                            "identified",
                            count,
                            0.0,
                            f"a3_recess_plane_{mask_name}",
                            RECESS_NOTES[name],
                            artifact,
                            row,
                        )
                    )
                    if not isinstance(frame, str) and mask is not None:
                        sections[name].append(
                            (p.slice, mask, frame, f"a3_recess_plane_{mask_name}", row)
                        )
                else:
                    here.append(
                        observe(
                            name,
                            "native",
                            "reading",
                            own,
                            (p.slice,),
                            str(code),
                            None,
                            0.0,
                            f"a3_recess_plane_{mask_name}",
                            "the plane was pointed to by the fluid pointer and read in full by the existing rule; it names nothing here (never an absence of the part elsewhere)",
                            artifact,
                            row,
                        )
                    )
            if t is None:
                continue
            if t.code != "read" or t.masks is None or t.slice is None:
                for name, _ in parts:
                    if p.codes.get(name) == "identified":
                        missing.append(
                            Unresolved(
                                name,
                                "laid",
                                None
                                if partner is None
                                else partner.record["series_uid"],
                                None
                                if partner is None
                                else tuple(partner.record["view"]),
                                t.code,
                            )
                        )
                continue
            if partner is None or at is None:
                continue
            for name, mask_name in parts:
                if p.codes.get(name) != "identified":
                    continue
                count = int(np.count_nonzero(t.masks.get(mask_name, 0)))
                if count:
                    said[at][0].append(
                        observe(
                            name,
                            "laid",
                            "resolved",
                            partner,
                            (t.slice,),
                            "laid_from_its_partner",
                            count,
                            t.off_mm,
                            f"{prefix}_{mask_name}",
                            f"the part named on native slice {p.slice} laid by the pair's match of places; places the twin never saw are left out",
                            twin_artifact,
                            twin_row,
                        )
                    )
                else:
                    said[at][1].append(
                        Unresolved(
                            name,
                            "laid",
                            partner.record["series_uid"],
                            tuple(partner.record["view"]),
                            "nothing_of_the_part_lands_on_the_twin",
                        )
                    )
            twin_row += 1
        # the pointer's own support through depth: a reading with no name and no boundary
        positive = tuple(
            int(z)
            for z in np.flatnonzero(read.arrays["a3_recess_profile_area_mm2"] > 0)
        )
        if positive:
            here.append(
                observe(
                    "joint_fluid",
                    "native",
                    "reading",
                    own,
                    positive,
                    "pointer_fluid_support",
                    None,
                    None,
                    "a3_recess_profile_area_mm2",
                    "2 mm blocks at the fluid level inside the compartment the earlier families located, area through depth: support that points, no boundary and no name; the planes it asked are read by the existing rules",
                    artifact,
                )
            )
        for name, _ in parts:
            if name not in got:
                missing.append(
                    Unresolved(
                        name,
                        "native",
                        uid,
                        view,
                        "|".join(
                            sorted(reason[name] or {"no_plane_pointed_to_read_it"})
                        ),
                    )
                )
        skip = {uid} | (
            {partner.record["series_uid"]} if partner is not None else set()
        )
        for name, _ in parts:
            usable = [s for s in sections[name] if s[1].any()]
            if not usable:
                continue
            z, region, frame, support, source_row = max(
                usable, key=lambda s: int(np.count_nonzero(s[1]))
            )
            physical = frame.to_patient(np.argwhere(region).astype(float))
            for other in measured:
                other_uid = other.record["series_uid"]
                if other_uid in skip:
                    continue
                other_view = tuple(other.record["view"])
                target = bone_target(physical, other)
                if isinstance(target, str):
                    said[where[id(other)]][1].append(
                        Unresolved(name, "projected", other_uid, other_view, target)
                    )
                    continue
                nearest, place, distance, count = target
                said[where[id(other)]][0].append(
                    observe(
                        name,
                        "projected",
                        "target",
                        other,
                        (nearest,),
                        place,
                        count,
                        distance,
                        support,
                        f"a location target projected from {name} on slice {z} of the series it was named in: where a native question about the compartment may be asked, not a boundary seen on this slice",
                        artifact,
                        source_row,
                        OBJECT_CODES[name] if support == "a1_objects" else None,
                    )
                )
        own.record["recess"] = {
            **read.record,
            "twin_arrays_prefix": prefix
            if partner is not None and kind != "retinacula"
            else None,
            "existing_slices": [],
        }
    for own, partner in zip(measured, partners, strict=True):
        # the twin's bootstrap, where the pair laid the recess and the capsule onto it
        sibling = None if partner is None else results[where[id(partner)]]
        if sibling is None or isinstance(sibling, str):
            continue
        for name, _ in RECESS_PARTS[sibling.kind]:
            code = own.record["assignments"]["codes"].get(name)
            held = (
                own.arrays["a1_objects"] == OBJECT_CODES[name]
                if name == "joint_fluid"
                else own.arrays.get(f"a2_{name}")
            )
            if code in NAMED and held is not None and np.any(held):
                said[where[id(own)]][0].append(
                    observe(
                        name,
                        "laid",
                        "resolved",
                        own,
                        (int(own.record["slice_index"]),),
                        str(code),
                        int(np.count_nonzero(held)),
                        None,
                        "a1_objects" if name == "joint_fluid" else f"a2_{name}",
                        "the middle slice's part, laid from the other sequence's own naming by the pair's match (the bootstrap)",
                        str(artifact_of(study_uid, own.record)),
                        None,
                        OBJECT_CODES[name] if name == "joint_fluid" else None,
                    )
                )
    return said


def keep_recess(
    measured: list[Measured], said: list[tuple[list[Observation], list[Unresolved]]]
) -> None:
    """The recess family's observations appended to each series' record, after every earlier
    family's (`keep_observations`: earlier rows stay as written, in their order)."""
    for m, (here, missing) in zip(measured, said, strict=True):
        if here or missing:
            keep_observations(m, here, missing)


def recess_existing(
    measured: list[Measured],
    found: list[tuple[dict, dict[str, np.ndarray]]],
    study_uid: str,
) -> None:
    """The retinacula stage's own slice (the axial slice through the patella centre) as observations of
    the axial series it lies in, beside the planes `name_the_recess` pointed to: the bootstrap stays a
    valid observation and the extra planes add to it, never replace it. Each wall is the existing
    rule's naming on that slice (the main run's record); the record's `recess.existing_slices` lists
    it. Called once the retinacula are found, so the observations are appended after those
    `name_the_recess` made, earlier rows untouched."""
    by_uid = {m.record["series_uid"]: m for m in measured}
    for record, arrays in found:
        own = by_uid.get(record["series_uid"])
        if own is None:
            continue
        for name in RETINACULA:
            code = record["assignments"]["codes"].get(name)
            mask = arrays.get(f"a2_{name}")
            if code not in NAMED or mask is None or not mask.any():
                continue
            keep_observations(
                own,
                [
                    observe(
                        name,
                        "native",
                        "resolved",
                        own,
                        (int(record["slice_index"]),),
                        str(code),
                        int(np.count_nonzero(mask)),
                        0.0,
                        f"a2_{name}",
                        "the retinacula stage's own slice (the main run's record): the wall's section on this slice, not its course",
                        str(artifact_of(study_uid, record)),
                    )
                ],
                [],
            )
            if isinstance(own.record.get("recess"), dict):
                own.record["recess"].setdefault("existing_slices", []).append(
                    {
                        "part": name,
                        "slice": int(record["slice_index"]),
                        "code": str(code),
                        "pixels": int(np.count_nonzero(mask)),
                    }
                )


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
    reads("fibula", ("places",), "lcl")
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
    arrays["a2_lcl_carried_femur"] = femur
    if fat_suppressed:
        arrays["a2_popliteus_tendon"] = np.zeros(labels.shape, dtype=bool)
        codes["popliteus_tendon"] = "abstain_requires_the_nonfs_notch_view"
    else:
        reads("lcl", ("region",), "popliteus_tendon")
        popliteus, notch_readings, popliteus_code = popliteus_in_notch(femur, lcl)
        arrays["a2_popliteus_tendon"] = popliteus
        for name, value in notch_readings.items():
            arrays[f"a2_popliteus_{name}"] = value
        codes["popliteus_tendon"] = popliteus_code
        if popliteus.any():
            handed("popliteus_tendon", ("region",))
    lcl_assigned.update(lcl=int(labels[lcl].max()) if lcl.any() else None)
    lcl_record["main_slice"] = {"object": "LCL"}
    return lcl_record, arrays, frame


def seen_native(
    series: Series, z: int, stage: str = BICEPS
) -> tuple[np.ndarray, np.ndarray]:
    """One native slice's stored light and the places it has none for (not finite, or the black
    margin the reconstruction never filled), read once per slice and handed to every stage that
    asks: the fibula's cheap profile, the head's body, the reference light, the biceps femoris
    tendon's rule (`stage` is the asker, whose read the ledger records when it is the first). The
    rule is given the light with the unseen places NaN, so no place it never saw reads as
    darkness."""

    def read() -> tuple[np.ndarray, np.ndarray]:
        reads("series", ("volume",), stage)
        uid = series.row.series_uid
        raw = np.asarray(series.volume[z], dtype=np.float64)
        return handed_on(raw), handed_on(~np.isfinite(raw) | margin_of(uid, z, raw))

    return once("biceps_native_light", (series.row.series_uid, z), read)


def biceps_twin(
    native: Measured, twin: Measured, z: int, stage: str = BICEPS
) -> tuple[np.ndarray, int] | str:
    """The fat-suppressed twin's light laid onto the pixels of the native slice `z`, NaN where the
    twin has no say (outside its picture or in its black margin), and the twin's own slice index;
    or why not. The twin's slice is the one whose plane passes through the native slice's place,
    found by the scanner's millimetres and never by equal indices (`slice_through`); the pair is
    matched once, native pixels onto the twin's (`matched`)."""

    def read() -> tuple[np.ndarray, int] | str:
        series, other = native.series, twin.series
        frame = plane_frame(series, z)
        reads("series", ("geometry", "slice_thickness_mm", "volume"), stage)
        if isinstance(frame, str) or other.geometry is None or other.volume is None:
            return "geometry_unreadable"
        known = [float(t) for t in other.slice_thickness_mm if t is not None]
        if len(known) != len(other.slice_thickness_mm):
            return "abstain_no_slice_thickness"
        origins = np.asarray(
            [np.asarray(p, dtype=float) for p in other.geometry.position]
        )
        index = slice_through(frame.origin_lps, origins, twin.frame.normal(), known)
        if index is None:
            return "abstain_twin_has_no_slice_at_this_place"
        twin_frame = plane_frame(other, index)
        if isinstance(twin_frame, str):
            return twin_frame
        plane = other.volume[index]
        raw, _ = seen_native(series, z, stage)
        source = matched(
            series,
            {"series_uid": series.row.series_uid, "slice_index": z},
            frame,
            raw.shape,
            {"series_uid": other.row.series_uid, "slice_index": index},
            twin_frame,
            plane,
        )
        if isinstance(source, str):
            return f"abstain_{source}"
        laid = laid_by(np.asarray(plane, dtype=np.float64), source)
        handed("biceps_twin", ("laid",))
        return handed_on(np.where(source >= 0, laid, np.nan)), index

    return once("biceps_twin", (native.series.row.series_uid, z), read)


def biceps_native(
    own: Measured,
    twin: Measured | None,
    fibula_lps: np.ndarray | None,
    fibula: FibulaFound | None = None,
) -> tuple[dict, dict[str, np.ndarray], PlaneFrame, str, int] | str:
    """The biceps femoris tendon's slice on a fat-bright series, read (its paragraph in
    `knee.objects.assignments`), with its twin's series and slice: from the fibula already found
    (`find_fibula`), whose places recover its main slice here, and whose marrow light there, in both
    acquisitions, is read once and handed on when `fibula` is the shared value of this very series
    and twin (`FibulaFound`), else read here (once); the head's body on each slice is the shared
    reading (`fibula_head`), made once for the fibula's continuation and this walk alike; then the
    walk outward to the head's lateral face
    (`lateral_to_the_head`), which asks for a slice's head only when it reaches it, each kept; and
    on the slice it chooses, the lens and field once (`read_part_slice`) and the rule
    (`proximal_biceps_on_slice`) with that same head. Or why it was not read. Every head the walk
    measured, its areas and status per slice (NaN and unread where the walk never went), the lights
    and the twin as laid are kept in the arrays beside the rule's own readings."""
    series, record = own.series, own.record
    uid = series.row.series_uid
    knee = record["assignments"]["knee"]
    reads("fibula", ("places",), BICEPS)
    if fibula_lps is None:
        return "abstain_no_fibula"
    if twin is None:
        return "abstain_no_fat_suppressed_twin"
    reads("series", ("geometry", "slice_thickness_mm", "volume"), BICEPS)
    geometry, volume = series.geometry, series.volume
    thicknesses = series.slice_thickness_mm
    if geometry is None or volume is None:
        return "geometry_unreadable"
    origins = np.asarray([np.asarray(p, dtype=float) for p in geometry.position])
    if (
        origins.ndim != 2
        or origins.shape[1] != 3
        or not np.all(np.isfinite(origins))
        or len(thicknesses) != len(origins)
        or len(volume) != len(origins)
    ):
        return "geometry_unreadable"
    normal = own.frame.normal()
    places = np.asarray(fibula_lps, dtype=np.float64)
    other = twin

    def reference() -> tuple[int | None, float, float, str | None]:
        """The fibula's native main slice, its marrow light there in both acquisitions and, if the
        twin could not be read there, why: made once, when the walk first asks for a head."""

        def read() -> tuple[int | None, float, float, str | None]:
            none = float("nan")
            if (
                fibula is not None
                and fibula.places is places
                and fibula.series_uid == uid
                and fibula.twin_uid == other.series.row.series_uid
                and np.isfinite(fibula.twin_light)
            ):
                # the fibula's own stage read both lights on its main slice: not read again
                reads("fibula", ("slice_index", "light", "twin_light"), BICEPS)
                return fibula.slice_index, fibula.light, fibula.twin_light, None
            main = slice_through(
                places.mean(axis=0), origins, normal, [float(t) for t in thicknesses]
            )
            if main is None:
                return main, none, none, "abstain_no_slice_holds_the_fibula"
            frame = plane_frame(series, main)
            if isinstance(frame, str):
                return main, none, none, frame
            plane, unseen = seen_native(series, main)
            support = projected_places(places, frame, plane.shape) & ~unseen
            light = (
                float(measures_of(uid, main, plane, frame).light(support))
                if support.any()
                else none
            )
            laid = biceps_twin(own, other, main)
            if isinstance(laid, str):
                return main, light, none, laid
            reads("biceps_twin", ("laid",), "biceps_reference")
            return main, light, twin_marrow_light(laid[0], support), None

        return once("biceps_reference", uid, read)

    # The walk is the fibula's own (`fibula_support`) when it is the same measurement: the same
    # series, places, knee, geometry and marrow light. It is handed here whole, every head it measured
    # included; the light is asked of the reference only when the walk reaches a head.
    walk = head_walk(
        series, places, knee, origins, normal, thicknesses, lambda: reference()[1]
    )
    reads("head_walk", ("face", "areas", "status", "heads"), BICEPS)
    z, areas, status, law = walk.face, walk.areas, walk.status, walk.code
    heads = dict(zip(walk.walked, walk.heads, strict=True))
    ledger.record(f"{BICEPS}.head_readings", planes=len(heads))
    if z is None:
        if law == "abstain_head_unreadable_on_the_way" and heads:
            return list(heads.values())[-1][2]  # why the head could not be read there
        return law
    main, light, twin_light, why = reference()
    frame = plane_frame(series, z)
    if isinstance(frame, str):
        return frame
    laid = biceps_twin(own, other, z)
    if isinstance(laid, str):
        return laid
    if why is not None or main is None:
        return why or "abstain_no_slice_holds_the_fibula"
    twin_light_map, twin_index = laid
    reads("background", ("split",), BICEPS)
    part_record, arrays, _ = read_part_slice(
        series, z, volume[z], frame, record["background_split"], knee, BICEPS
    )
    plane, unseen = seen_native(series, z)
    body = heads[z][0]
    reads("fibula_head", ("body",), BICEPS)
    reads("biceps_twin", ("laid",), BICEPS)
    mask, readings, code = proximal_biceps_on_slice(
        np.where(unseen, np.nan, plane),
        twin_light_map,
        frame.basis_lps,
        light,
        twin_light,
        body,
        int(series.row.fat_suppression) == 1,
        measures_of(uid, z, plane, frame),
    )
    walked = list(heads)
    arrays["a1_objects"] = np.zeros(plane.shape, dtype=np.int8)
    arrays["a2_biceps_femoris_tendon"] = mask
    for name, value in readings.items():
        arrays[f"a2_biceps_{name}"] = value
    arrays.update(
        a2_biceps_head_slices=np.asarray(walked, dtype=np.int32),
        a2_biceps_head_bodies=np.stack([heads[w][0] for w in walked]),
        a2_biceps_head_targets=np.stack([heads[w][1] for w in walked]),
        a2_biceps_head_areas_mm2=np.asarray(areas, dtype=np.float64),
        a2_biceps_head_slice_status=np.asarray(status, dtype=np.int8),
        a2_biceps_fibula_main_slice=np.asarray(main, dtype=np.int32),
        a2_biceps_selected_slice=np.asarray(z, dtype=np.int32),
        a2_biceps_twin_slice=np.asarray(twin_index, dtype=np.int32),
        a2_biceps_reference_light=np.asarray(light, dtype=np.float64),
        a2_biceps_reference_twin_light=np.asarray(twin_light, dtype=np.float64),
        a2_biceps_fibula_places_lps=places,
        a2_biceps_twin_laid=twin_light_map,
        a2_biceps_native_unseen=unseen,
    )
    part_record["assignments"]["codes"][BICEPS] = code
    part_record["main_slice"] = {
        "object": BICEPS,
        "fibula_main_slice": int(main),
        "selected_slice": int(z),
        "twin_series_uid": other.series.row.series_uid,
        "twin_slice_index": int(twin_index),
        "head_codes": {str(w): heads[w][2] for w in walked},
    }
    return part_record, arrays, frame, other.series.row.series_uid, twin_index


def biceps_femoris_slice(
    own: Measured,
    measured: list[Measured],
    fibula_lps: np.ndarray | None,
    fibula: FibulaFound | None = None,
) -> tuple[dict, dict[str, np.ndarray], PlaneFrame] | str:
    """The biceps femoris tendon's slice of one series, read once for the pair: on the fat-bright
    series by `biceps_native` (kept for its twin, made by whichever of the two asks first), and on
    its fat-suppressed twin the slice of the same place in the scanner's millimetres, read for its
    lens and field only, to which `find_part` lays the native mask (`lay_parts`); or why it was not
    read: no fibula, no twin, no view, no head, no tendon."""
    reads("series", ("row",), BICEPS)
    fat_suppressed = (
        int(own.series.row.fat_suppression) == 1
    )  # the tag is stored as text
    if fat_suppressed:
        native_at = partner_of(
            measured, next(i for i, m in enumerate(measured) if m is own)
        )
        if native_at is None:
            return "abstain_no_fat_bright_native_view"
    else:
        native_at = own
    twin = partner_of(
        measured, next(i for i, m in enumerate(measured) if m is native_at)
    )
    native = once(
        "biceps_native",
        native_at.series.row.series_uid,
        lambda: biceps_native(native_at, twin, fibula_lps, fibula),
    )
    if isinstance(native, str):
        return native
    record, arrays, frame, twin_uid, twin_index = native
    if not fat_suppressed:
        return record, arrays, frame
    if twin_uid != own.series.row.series_uid:
        return "abstain_the_native_view_has_another_twin"
    volume = own.series.volume
    twin_frame = plane_frame(own.series, twin_index)
    if volume is None or isinstance(twin_frame, str):
        return "geometry_unreadable"
    reads("background", ("split",), BICEPS)
    twin_record, twin_arrays, _ = read_part_slice(
        own.series,
        twin_index,
        volume[twin_index],
        twin_frame,
        own.record["background_split"],
        own.record["assignments"]["knee"],
        BICEPS,
    )
    # on this slice the mask is the native one's, laid; until then nothing is named
    twin_arrays["a1_objects"] = np.zeros(twin_arrays["acquired_plane"].shape, np.int8)
    twin_arrays["a2_biceps_femoris_tendon"] = np.zeros(
        twin_arrays["acquired_plane"].shape, dtype=bool
    )
    twin_record["assignments"]["codes"][BICEPS] = BICEPS_LAID_WHEN
    twin_record["main_slice"] = {
        "object": BICEPS,
        "native_series_uid": record["series_uid"],
        "native_slice_index": int(record["slice_index"]),
    }
    return twin_record, twin_arrays, twin_frame


# -- THE POSTERIOR FAMILY: what the views say of the back of the knee's parts --------------------
# The two gastrocnemius heads, the popliteal lumens, the three hamstring tendons, the sartorius and
# the bursa are named by their own rules on the axial slices (`name_the_back_of_the_knee`,
# `semimembranosus_slice`, `name_sartorius`), the popliteus tendon and the biceps femoris tendon
# on their own slices, the iliotibial band on the middle coronal. Those rules and their slices
# are untouched. This is the one place that says what each of them made, by where the saying
# comes from (`knee.collapse.observations`), and asks the one cheap question the data can
# answer about the others' continuation (`knee.collapse.posterior`).
#
# What is read and what is not. A tube (a tendon or a vessel: dark; the bursa's fluid: bright on a
# fluid-sensitive fat-suppressed view) is followed along the leg on the nearest slice of every
# series the leg runs through, from where its cross-section projects, on the light already read
# for the biceps femoris tendon (`seen_native`: made once per slice), with no lens or field. A
# muscle belly (the heads, the sartorius) and the iliotibial band, the popliteus and the biceps
# femoris tendon, which already are longitudinal on their own slices, get their native, laid and
# projected observations and no continuation: nothing here claims one.
#
# Two passes. The first runs before the middle records and the semimembranosus group's are
# saved (the trace arrays are kept in the record that holds the cross-section's mask and are saved
# with it); the second runs after the lateral parts are found and adds rows only.

# the product and field the ledger knows a part's mask by (`handed` where the part was made)
POSTERIOR_PRODUCT = {
    "medial_gastrocnemius": ("gastrocnemius", "region"),
    "lateral_gastrocnemius": ("gastrocnemius", "region"),
    "popliteal_artery": ("popliteal_lumens", "artery"),
    "popliteal_vein": ("popliteal_lumens", "vein"),
    "sartorius": ("sartorius", "region"),
    "iliotibial_band": ("iliotibial_band", "region"),
    "semimembranosus": ("semimembranosus", "region"),
    "semitendinosus": ("semitendinosus", "region"),
    "gracilis": ("gracilis", "region"),
    "gastrocnemius_semimembranosus_bursa": ("bursa", "region"),
    "popliteus_tendon": ("popliteus_tendon", "region"),
    BICEPS: (BICEPS, "region"),
}
# (part, the array of a record that holds its places, whether that array is coded by OBJECT_CODES)
EARLY_MIDDLE_PARTS = (
    ("medial_gastrocnemius", "a1_objects", True),
    ("lateral_gastrocnemius", "a1_objects", True),
    ("popliteal_artery", "a2_popliteal_artery", False),
    ("popliteal_vein", "a2_popliteal_vein", False),
    ("sartorius", "a2_sartorius", False),
)
LATE_MIDDLE_PARTS = (("iliotibial_band", "a2_iliotibial_band", False),)
# The context the middle slices already name (`a1_objects`): said natively or laid, where named, as
# the middle slice's own naming and no more: no slice is claimed ideal for them, they are not
# projected onto other series, and nothing is followed. Bone marrow is a property of each named
# bone's interior, not an object here.
CONTEXT_MIDDLE_PARTS = (
    ("joint", "a1_objects", True),
    ("meniscus", "a1_objects", True),
    ("air", "a1_objects", True),
    ("skin", "a1_objects", True),
    ("subcutaneous_fat", "a1_objects", True),
    ("muscle", "a1_objects", True),
)
CONTEXT_PARTS = frozenset(name for name, _, _ in CONTEXT_MIDDLE_PARTS)
# a part's own slice's record, by the part it is the main slice of
MAIN_RECORD_PARTS = {
    "semimembranosus": (
        ("semimembranosus", "a1_objects", True),
        ("semitendinosus", "a2_semitendinosus", False),
        ("gracilis", "a2_gracilis", False),
        (
            "gastrocnemius_semimembranosus_bursa",
            "a2_gastrocnemius_semimembranosus_bursa",
            False,
        ),
    ),
    "lcl": (("popliteus_tendon", "a2_popliteus_tendon", False),),
    BICEPS: ((BICEPS, "a2_biceps_femoris_tendon", False),),
}
# what `find_part` already keeps as a silence, by series, when these parts abstain on a main slice
SILENT_BY_FIND_PART = frozenset(
    ("semimembranosus", "semitendinosus", "gracilis", "popliteus_tendon", BICEPS)
)
POSTERIOR_PARTS = frozenset(
    name
    for parts in (EARLY_MIDDLE_PARTS, LATE_MIDDLE_PARTS, *MAIN_RECORD_PARTS.values())
    for name, _, _ in parts
)
# the tubes that are followed, and whether each is dark (a tendon, an enclosed lumen) or bright
POSTERIOR_TUBES = {
    "semimembranosus": True,
    "semitendinosus": True,
    "gracilis": True,
    "popliteal_artery": True,
    "popliteal_vein": True,
    "gastrocnemius_semimembranosus_bursa": False,
}


@dataclass(frozen=True)
class PosteriorSource:
    """One native saying of a part, to project and to follow from: the record and arrays that hold
    its places, their slice's frame, the places, which array and label say them, the artifact
    that will hold them and how many there are."""

    name: str
    record: dict
    arrays: dict[str, np.ndarray]
    frame: PlaneFrame
    mask: np.ndarray
    support: str
    label: int | None
    artifact: str
    pixels: int


def posterior_sayings(
    record: dict,
    arrays: dict[str, np.ndarray],
    frame: PlaneFrame | str,
    parts: tuple[tuple[str, str, bool], ...],
    study_uid: str,
    by_silence: bool,
) -> tuple[list[Observation], list[Unresolved], list[PosteriorSource], set[str]]:
    """What one record says of each of `parts`, from its own codes and masks and counting nothing
    again: a part its rule named on this slice is native and resolved, one laid from its
    partner is laid and resolved, one the rule was asked and refused is an `Unresolved` with its
    code (kept as the refusal `find_part` already holds where `by_silence`, so it is said once).
    Returns the observations, the unresolved, the native sources, and the parts laid here."""
    codes = record["assignments"]["codes"]
    artifact = str(artifact_of(study_uid, record))
    uid, view, index = (
        record["series_uid"],
        tuple(record["view"]),
        record["slice_index"],
    )
    seen: list[Observation] = []
    unplaced: list[Unresolved] = []
    sources: list[PosteriorSource] = []
    laid: set[str] = set()
    for name, support, coded in parts:
        code = codes.get(name)
        if code is None or code == "not_named_on_this_slice":
            continue  # the rule was never asked of this record: nothing to say
        if code not in NAMED:
            if not by_silence:
                unplaced.append(Unresolved(name, "native", uid, view, str(code)))
            continue
        if name in POSTERIOR_PRODUCT:
            product, field = POSTERIOR_PRODUCT[name]
            reads(product, (field,), "posterior_index")
        array = arrays[support]
        mask = array == OBJECT_CODES[name] if coded else np.asarray(array, dtype=bool)
        pixels = int(np.count_nonzero(mask))
        if not pixels:
            unplaced.append(
                Unresolved(name, "native", uid, view, "named_without_a_place_on_it")
            )
            continue
        label = OBJECT_CODES[name] if coded else None
        if code == "laid_from_its_partner":
            laid.add(name)
            seen.append(
                observe_in(
                    record,
                    name,
                    "laid",
                    "resolved",
                    (index,),
                    str(code),
                    pixels,
                    None,
                    support,
                    "laid from the other sequence's slice of the same place by the pair's "
                    "match; the places the match cannot map are left out",
                    artifact,
                    None,
                    label,
                )
            )
            continue
        seen.append(
            observe_in(
                record,
                name,
                "native",
                "resolved",
                (index,),
                str(code),
                pixels,
                0.0,
                support,
                "the middle slice's own naming of this context, with no claim that this "
                "slice is its best: what the slice shows of it, not the whole"
                if name in CONTEXT_PARTS
                else "the established rule names it on this slice: its section here, not its "
                "whole extent or boundary",
                artifact,
                None,
                label,
            )
        )
        if not isinstance(frame, str) and name not in CONTEXT_PARTS:
            sources.append(
                PosteriorSource(
                    name, record, arrays, frame, mask, support, label, artifact, pixels
                )
            )
    return seen, unplaced, sources, laid


def read_trace(
    other: Measured, z: int, physical: np.ndarray, dark: bool
) -> tuple[Trace, np.ndarray] | str | None:
    """The tube whose cross-section lies at `physical` (scanner millimetres), followed along the
    leg on slice `z` of another series (`knee.collapse.posterior.trace_tube`), with the traced
    places in millimetres; None where the leg does not run in that slice (an axial one: nothing
    to ask there), or why it cannot be read (an unreadable frame, no width). The light is the
    slice's own, the places it never saw NaN (`seen_native`, made once)."""
    frame = plane_frame(other.series, z)
    if isinstance(frame, str):
        return frame
    along = leg_axis(frame.basis_lps)
    if along is None:
        return None
    axis, toward_head = along
    width = cross_extent_mm(physical, frame.basis_lps, axis)
    if width is None:
        return "target_has_no_finite_place"
    spacing = float(np.linalg.norm(frame.basis_lps[:, 1 - axis]))
    half = max(1, round(width / 2.0 / spacing))
    raw, unseen = seen_native(other.series, z, "posterior")
    reads("series", ("volume", "geometry"), "posterior")
    start = frame.to_native(physical).mean(axis=0)
    got = trace_tube(
        np.where(unseen, np.nan, raw),
        axis,
        toward_head,
        (float(start[0]), float(start[1])),
        half,
        dark,
    )
    ledger.record("posterior.trace_readings", planes=1)
    return got, (
        frame.to_patient(got.points_rc) if len(got.points_rc) else np.empty((0, 3))
    )


def trace_rows(
    source: PosteriorSource,
    leg: Leg | None,
    traces: list[tuple[Measured, int, float, Trace, np.ndarray]],
) -> list[tuple[Measured, Observation]]:
    """Keep every trace of one part in the arrays of the record that holds its cross-section (flat
    packed: `..._offsets` cuts trace i's places out of `..._points_lps`, `..._light`, `..._flank`;
    `..._slices`, `..._starts` and `..._stops` are per trace, the integers named by
    `START_NAMES` and `STOP_NAMES`), and say each as a native reading on the slice it was read on."""
    name = source.name
    prefix = f"a3_posterior_trace_{name}"
    sizes = [len(t[4]) for t in traces]
    arrays = source.arrays
    arrays[f"{prefix}_points_lps"] = np.concatenate([t[4] for t in traces])
    arrays[f"{prefix}_light"] = np.concatenate([t[3].light for t in traces])
    arrays[f"{prefix}_flank"] = np.concatenate([t[3].flank for t in traces])
    arrays[f"{prefix}_offsets"] = np.concatenate(([0], np.cumsum(sizes))).astype(
        np.int64
    )
    arrays[f"{prefix}_slices"] = np.asarray([t[1] for t in traces], dtype=np.int32)
    arrays[f"{prefix}_starts"] = np.asarray(
        [START_NAMES.index(t[3].start) for t in traces], dtype=np.int8
    )
    arrays[f"{prefix}_stops"] = np.asarray(
        [
            [
                STOP_NAMES.index(t[3].toward_head or STOP_NAMES[0]),
                STOP_NAMES.index(t[3].toward_feet or STOP_NAMES[0]),
            ]
            for t in traces
        ],
        dtype=np.int8,
    )
    top = (
        float(leg.tibia_lps[:, 2].max())
        if leg is not None and len(leg.tibia_lps)
        else np.nan
    )
    low = (
        float(leg.femur_lps[:, 2].min())
        if leg is not None and len(leg.femur_lps)
        else np.nan
    )
    arrays.setdefault("a3_posterior_context_up_mm", np.asarray([top, low]))
    handed(
        "posterior_trace",
        ("points", "light", "flank", "offsets", "slices", "starts", "stops", "context"),
    )
    reads("posterior_trace", ("points", "starts", "stops"), "posterior_index")
    out: list[tuple[Measured, Observation]] = []
    dark = POSTERIOR_TUBES[name]
    for k, (other, z, distance, got, points) in enumerate(traces):
        if got.start == FOLLOWED:
            height = f"z {points[:, 2].min():.1f} to {points[:, 2].max():.1f} mm"
            stops = f"toward the head it {got.toward_head}, toward the feet it {got.toward_feet}"
        else:
            height = "no place held"
            stops = "the relation did not hold at the projected place (the tube may lie off this slice)"
        out.append(
            (
                other,
                observe_in(
                    other.record,
                    name,
                    "native",
                    "reading",
                    (z,),
                    "tube_followed" if got.start == FOLLOWED else got.start,
                    len(points),
                    distance,
                    f"{prefix}_points_lps",
                    f"a cheap ridge followed along the leg from the cross-section's projected place "
                    f"({'darker' if dark else 'brighter'} than an equally wide strip on each side): "
                    f"{stops}; {height}; a pointer, not the part's boundary or full course; "
                    f"row {k} is points_lps[offsets[{k}]:offsets[{k + 1}]] of {prefix}_*; "
                    "a3_posterior_context_up_mm holds the tibia's top and the femur's lowest place",
                    source.artifact,
                    k,
                ),
            )
        )
    return out


def index_posterior(
    measured: list[Measured],
    middle_parts: tuple[tuple[str, str, bool], ...],
    main_records: list[tuple[dict, dict[str, np.ndarray]]],
    study_uid: str,
    leg: Leg | None,
    traced: bool,
) -> None:
    """Say, for each of the posterior family's parts, what every view of the study says of it: its
    native and laid sayings (`posterior_sayings`) on the middle records (`middle_parts`) and on the
    part's own slices (`main_records`), a projected target on every other series' nearest slice from
    its largest native section (a location to ask, never a boundary; skipped on the series that
    hold it laid), and, for a tube where `traced`, the continuation read on each series the leg runs
    through (`read_trace`). The rows are appended to the records of the series they are about."""
    by_uid = {m.record["series_uid"]: m for m in measured}
    sources: dict[str, list[PosteriorSource]] = {}
    laid_on: dict[str, set[str]] = {}

    def take(record, arrays, frame, parts, by_silence):
        seen, unplaced, native, laid = posterior_sayings(
            record, arrays, frame, parts, study_uid, by_silence
        )
        keep_on_record(record, seen, unplaced)
        for source in native:
            sources.setdefault(source.name, []).append(source)
        for name in laid:
            laid_on.setdefault(name, set()).add(record["series_uid"])

    for own in measured:
        take(own.record, own.arrays, own.frame, middle_parts, False)
    for record, arrays in main_records:
        parts = MAIN_RECORD_PARTS.get(str(record["main_slice"]["object"]).lower())
        own = by_uid.get(record["series_uid"])
        if parts is None or own is None:
            continue
        frame = plane_frame(own.series, record["slice_index"])
        take(
            record,
            arrays,
            frame,
            tuple(
                p
                for p in parts
                if p[0] not in SILENT_BY_FIND_PART
                or record["assignments"]["codes"].get(p[0]) in NAMED
            ),
            True,
        )

    def slot(added, other):
        return added.setdefault(other.record["series_uid"], (other, [], []))

    for name, found in sources.items():
        best = max(found, key=lambda s: s.pixels)
        physical = best.frame.to_patient(np.argwhere(best.mask).astype(float))
        dark = POSTERIOR_TUBES.get(name)
        traces: list[tuple[Measured, int, float, Trace, np.ndarray]] = []
        added: dict[str, tuple[Measured, list[Observation], list[Unresolved]]] = {}

        for other in measured:
            uid = other.record["series_uid"]
            if uid == best.record["series_uid"] or uid in laid_on.get(name, ()):
                continue
            view = tuple(other.record["view"])
            target = bone_target(physical, other)
            if isinstance(target, str):
                slot(added, other)[2].append(
                    Unresolved(name, "projected", uid, view, target)
                )
                continue
            nearest, place, distance, count = target
            slot(added, other)[1].append(
                observe_in(
                    other.record,
                    name,
                    "projected",
                    "target",
                    (nearest,),
                    place,
                    count,
                    distance,
                    best.support,
                    f"a location target projected from {name} on slice "
                    f"{best.record['slice_index']} of series {best.record['series_uid'][-8:]}: where "
                    "a native question may be asked, not a boundary seen on this slice",
                    best.artifact,
                    None,
                    best.label,
                )
            )
            if not traced or dark is None:
                continue
            if not dark and not (
                int(other.series.row.fat_suppression) == 1
                and int(other.series.row.fluid_sensitive) == 1
            ):
                slot(added, other)[2].append(
                    Unresolved(
                        name,
                        "native",
                        uid,
                        view,
                        "fluid_is_not_bright_in_this_sequence",
                    )
                )
                continue
            if place == "beyond_the_scan":
                slot(added, other)[2].append(
                    Unresolved(name, "native", uid, view, "target_beyond_the_scan")
                )
                continue
            got = read_trace(other, nearest, physical, dark)
            if isinstance(got, str):
                slot(added, other)[2].append(Unresolved(name, "native", uid, view, got))
            elif got is not None:
                traces.append((other, nearest, distance, got[0], got[1]))
        if traces:
            for other, row in trace_rows(best, leg, traces):
                slot(added, other)[1].append(row)
        for other, here, missing in added.values():
            keep_observations(other, here, missing)


def posterior_silences(measured: list[Measured], silences: dict[str, str]) -> None:
    """The posterior parts a series was asked and refused on a slice of their own, said as
    unresolved on that series: the silences `find_part` kept, by `<series uid>:<part>`, are
    the refusals; nothing is added to them and the part is not called absent."""
    by_uid = {m.record["series_uid"]: m for m in measured}
    for key, code in silences.items():
        uid, _, name = key.rpartition(":")
        own = by_uid.get(uid)
        if own is None or name not in POSTERIOR_PARTS:
            continue
        keep_observations(
            own,
            [],
            [Unresolved(name, "native", uid, tuple(own.record["view"]), str(code))],
        )


def lay_parts(
    own: Measured,
    read: tuple[dict, dict[str, np.ndarray], PlaneFrame],
    partner: tuple[dict, dict[str, np.ndarray], PlaneFrame],
    parts: tuple[str, ...],
    yields: tuple[int, ...] = (),
    onto_borders: bool = False,
    *,
    product: str,
) -> dict[str, str | None]:
    """Lay the parts the other sequence's slice of the same place names onto this series' slice,
    by the pair's one match (`matched`), onto this slice's own regions that nothing else holds but
    the parts in `yields`, and with `onto_borders` onto the places between its regions too, where
    its lens leaves a thin dark band out of every region: for each part, "laid_from_its_partner",
    why it was not laid, or None when nothing was laid. Once the places match, the region laid is
    read here: `<product>.region`, read by the partner."""
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
    reads(product, ("region",), "partner")
    laid = laid_by(partner_arrays["a1_objects"], source)
    # a copy: a slice's objects may still be the names it made alone
    objects = arrays["a1_objects"].copy()
    open_to_them = np.isin(objects, (0, *yields))
    if not onto_borders:
        open_to_them &= arrays["b1_labels"] > 0
    codes: dict[str, str | None] = {}
    for part in parts:
        mask = partner_arrays.get(f"a2_{part}")
        if mask is not None:
            reads(part, ("region",), "partner")
            placed = (source >= 0) & laid_by(mask, source) & arrays["b1_available"]
            arrays[f"a2_{part}"] = placed
            codes[part] = "laid_from_its_partner" if placed.any() else None
            continue
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
    laid_when: str | None,
) -> tuple[list[tuple[dict, dict[str, np.ndarray]]], dict[str, str]]:
    """A part named on its own slice in each series (`read_slice`: `acl_slice`, `lcl_slice`), and
    laid from the sequence that names it onto the other sequence's slice of the same place where
    that one abstains with `laid_when` (`lay_part`): the slices that name it, each record with its
    arrays, and every other series' silence, keyed `<series uid>:<part>`."""
    read: dict[int, tuple[dict, dict[str, np.ndarray], PlaneFrame]] = {}
    silences: dict[str, str] = {}
    companions = MAIN_COMPANIONS.get(part, ())
    for index, own in enumerate(measured):
        result = read_slice(own)
        if isinstance(result, str):
            for name in (part, *companions):
                silences[f"{own.record['series_uid']}:{name}"] = result
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
                laid = lay_parts(
                    own, read[index], read[at], (part, *companions), product=part
                )
                for name, code in laid.items():
                    codes[name] = code or codes[name]
        for name in companions:
            if codes[name] not in NAMED:
                # This tendon requires the semimembranosus; retain the upstream reason when
                # that reference fails. The two retinacula have independent decisions.
                silences[f"{record['series_uid']}:{name}"] = (
                    codes[part]
                    if part == "semimembranosus" and codes[part] not in NAMED
                    else codes[name]
                )
        if codes[part] in NAMED:
            handed(part, ("main_slice", "region"))
            found.append((record, arrays))
        else:
            silences[f"{own.record['series_uid']}:{part}"] = codes[part]
    return found, silences


def artifact_of(study_uid: str, record: dict) -> Path:
    """Where `save` puts one record's arrays, relative to its run: the study's folder and the series'
    uid, with the part's name when it is a main slice's. Known before the save, so an observation can
    name the artifact that will hold its places."""
    part = record.get("main_slice", {}).get("object")
    name = record["series_uid"] if part is None else f"{record['series_uid']}-{part}"
    return Path(study_uid) / f"{name}.npz"


def save(run_dir: Path, study_uid: str, record: dict, arrays: dict) -> dict:
    """Save one record's arrays in the run and note them, with their digests, on the record. A main
    slice's arrays are named for its part as well, since one series may hold several. Saving is not
    reading: what is kept here declares no read, so a value no stage reads stays on the list of
    what no stage reads (the module note, TELEMETRY)."""
    artifact = artifact_of(study_uid, record)
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
    objects: dict | None = None,
) -> None:
    """Merge one study into the run's receipt (`knee.receipt.merged_receipt`): its records,
    silences and telemetry replace what the receipt held for it, and every other study's stay."""
    path = run_dir / "receipt.json"
    old = json.loads(path.read_text()) if path.exists() else None
    receipt = merged_receipt(
        old, REQUEST, study_uid, series_uids, records, unread, telemetry, objects
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
            reading = measure(series, drawn)
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
            name_suprapatellar_pads(own, partner)
        # Initialize FS refusals before a non-FS source lays its separate ITB mask onto them.
        for own, partner in sorted(
            zip(measured, partners, strict=True),
            key=lambda pair: int(pair[0].series.row.fat_suppression),
            reverse=True,
        ):
            name_iliotibial_band(own, partner)
        # The back of the knee, on the series the leg runs through: the study's leg, its bones in
        # the scanner's millimetres, made once where the header names the knee there, and carried
        # onto the slices its parts are named on; both heads on the middle slice, from the
        # lens already read there, before the records are saved, so it is saved and drawn.
        leg = None
        reads("naming", ("in_plane",), "leg")
        if any(
            not own.assignment.in_plane[2]
            and own.record["assignments"]["knee"] in ("R", "L")
            for own in measured
        ):
            leg = leg_of(measured)
        patella_centre = None
        if leg is not None and len(leg.patella_lps):
            reads("leg", ("patella_lps",), "patella_centre")
            patella_centre = leg.patella_lps.mean(axis=0)
            handed("patella", ("centre_lps",))
        for own in measured:
            own.record["assignments"]["codes"].update(
                name_the_back_of_the_knee(own, leg)
            )
        # The semimembranosus group (the tendon, the semitendinosus and the gracilis) is resolved
        # once here, ahead of the middle slices' save below, since the sartorius on a middle axial
        # reads the gracilis's physical places from it: its records are saved and its silences
        # kept exactly as the later main parts' are, and it is not read again after them.
        found, silences = find_part(
            measured,
            "semimembranosus",
            lambda own: semimembranosus_slice(own, leg),
            "abstain_no_tendon_at_the_back_inner_corner",
        )
        # kept in order but written once, after the posterior family has added what it keeps in
        # their arrays (`index_posterior`)
        group_found = found
        for part_record, _ in group_found:
            main_records.append(part_record)
        main_unread.update(silences)
        source = gracilis_source(measured, found)
        for own in measured:
            name_sartorius(own, source)
        # The femur and the tibia through the stacks, pointed planes only, kept in the middle records.
        name_the_bones(measured, partners, leg, study_uid)
        # The patella through the stacks, with the extensor tendons and the fat pads on the planes
        # it names, kept beside the bones' records and observations.
        name_the_patella(measured, partners, leg, study_uid)
        # The joint (the sided menisci, the cartilage, the cruciates and the MCL) through the
        # stacks, from the bones' carried places, kept beside the bones' and the patella's records.
        name_the_joint(measured, partners, leg, study_uid)
        # The recesses, their lining and fluid, the side recesses' capsule and the retinacula through
        # the stacks, from the compartments those families located, kept beside their records.
        recess_said = name_the_recess(
            measured, partners, leg, patella_centre, study_uid
        )
        # The posterior family: what the views say of the heads, the lumens, the sartorius and the
        # semimembranosus group with the bursa, and each tube's continuation along the leg; then
        # the group's records are written once, with the arrays that continuation added.
        index_posterior(measured, EARLY_MIDDLE_PARTS, group_found, study_uid, leg, True)
        for part_record, part_arrays in group_found:
            save(main_run, study_uid, part_record, part_arrays)
        # The fibula, found on its main slice from the profile's pointed planes.
        found_fibulas: list[tuple[Measured, FibulaFound]] = []
        for own in measured:
            fibula = find_fibula(own.series, own.record, own.arrays, own.stack)
            records.append(save(run_dir, study_uid, own.record, own.arrays))
            if isinstance(fibula, str):
                main_unread[f"{own.record['series_uid']}:fibula"] = fibula
            else:
                # written once, whole, after its twin, axial and consumer fields are complete;
                # the artifact is known before the write, so observations can name it
                fibula.record["artifact"] = str(artifact_of(study_uid, fibula.record))
                main_records.append(fibula.record)
                found_fibulas.append((own, fibula))
        # It is one leg: the fibula found in one sequence is laid onto the same place of the other,
        # and every view's saying of it is kept by where it comes from. Then the fibula, one value,
        # is handed to the LCL and the biceps femoris tendon: the first series, in the study's
        # order, to name it where its front edge can be read.
        shared_fibulas: list[FibulaFound] = []
        for own, fibula in found_fibulas:
            partner = partner_of(
                measured, next(i for i, m in enumerate(measured) if m is own)
            )
            twin = None if partner is None else fibula_twin(own, partner, fibula)
            if isinstance(twin, tuple) and partner is not None:
                twin_record, twin_arrays, twin_index, twin_light, _ = twin
                main_records.append(save(main_run, study_uid, twin_record, twin_arrays))
                main_unread.pop(f"{partner.record['series_uid']}:fibula", None)
                fibula = replace(
                    fibula,
                    twin_uid=partner.record["series_uid"],
                    twin_index=twin_index,
                    twin_light=twin_light,
                )
                handed("fibula", ("twin_light",))
            elif isinstance(twin, str):
                fibula.record["main_slice"]["transfer"] = twin
            seen, unplaced = fibula_observations(own, fibula, partner, twin, measured)
            fibula.record["observations"] = observation_rows(seen)
            fibula.record["observations_by_provenance"] = tally(seen)
            fibula.record["observations_unresolved"] = unresolved_rows(unplaced)
            save(main_run, study_uid, fibula.record, fibula.arrays)
            shared_fibulas.append(fibula)
        shared = next((f for f in shared_fibulas if f.places is not None), None)
        fibula_lps = None if shared is None else shared.places
        existing: dict[str, list[tuple[dict, dict[str, np.ndarray]]]] = {}
        for part, read_slice, laid_when in (
            ("acl", acl_slice, "abstain_not_walled_off_without_fat_suppression"),
            (
                "lcl",
                lambda own: lcl_slice(own, fibula_lps),
                "abstain_not_parted_from_the_fat_with_fat_suppression",
            ),
            (
                "patellar_retinacula",
                lambda own: retinacula_slice(
                    own, leg, retinacula_centre(measured, patella_centre)
                ),
                None,
            ),
            (
                BICEPS,
                lambda own: biceps_femoris_slice(own, measured, fibula_lps, shared),
                BICEPS_LAID_WHEN,
            ),
        ):
            found, silences = find_part(measured, part, read_slice, laid_when)
            existing[part] = found
            for part_record, part_arrays in found:
                main_records.append(save(main_run, study_uid, part_record, part_arrays))
            main_unread.update(silences)
        # The ACL's and the LCL's own slices stay observations beside the joint's pointed planes.
        joint_existing(
            measured,
            {part: existing[part] for part in ("acl", "lcl") if part in existing},
            study_uid,
        )
        # The recess family's observations follow every earlier family's, then the retinacula's own
        # slice, which stays an observation beside the recess family's planes.
        keep_recess(measured, recess_said)
        recess_existing(measured, existing.get("patellar_retinacula", []), study_uid)
        # The lateral parts found after the middle records were written (the iliotibial band, the
        # popliteus tendon, the biceps femoris tendon), and every refusal of the posterior family.
        index_posterior(
            measured,
            (*LATE_MIDDLE_PARTS, *CONTEXT_MIDDLE_PARTS),
            [*existing.get("lcl", []), *existing.get(BICEPS, [])],
            study_uid,
            leg,
            False,
        )
        posterior_silences(measured, main_unread)
        # The renderers read the saved run, when they draw it: their reads are its last.
        if drawn and records:
            reads("interiors", DRAWN_INTERIORS, "draw")
            reads("naming", DRAWN_NAMES, "draw")
            # what a slice read with its partner keeps, in place of its own objects and codes
            reads("partner", ("objects", "codes"), "draw")
            # the back of the knee's part, which a middle slice the leg runs through names
            if any(
                r["assignments"]["codes"].get(name) == "identified"
                for r in records
                for name in ("medial_gastrocnemius", "lateral_gastrocnemius")
            ):
                reads("gastrocnemius", ("region",), "draw")
            # the lumens between the heads, which that slice names
            if any(
                r["assignments"]["codes"].get(name) == "identified"
                for r in records
                for name in ("popliteal_artery", "popliteal_vein")
            ):
                reads("popliteal_lumens", ("artery", "vein"), "draw")
            # the joint's boundaries, each where a slice names it
            boundaries = tuple(
                field
                for field, name in JOINT_BOUNDARIES
                if any(r["assignments"]["codes"].get(name) in NAMED for r in records)
            )
            if boundaries:
                reads("joint_boundaries", boundaries, "draw")
            if any(
                r["assignments"]["codes"].get("quadriceps_fat_pad") in NAMED
                for r in records
            ):
                reads(
                    "suprapatellar_pads",
                    (
                        "quadriceps_fat_pad",
                        "prefemoral_fat_pad",
                        "suprapatellar_recess_ridge",
                    ),
                    "draw",
                )
            if any(
                r["assignments"]["codes"].get("iliotibial_band") in NAMED
                for r in records
            ):
                reads("iliotibial_band", ("region",), "draw")
            # the sartorius, which a middle axial names from the gracilis's places
            if any(
                r["assignments"]["codes"].get("sartorius") in NAMED for r in records
            ):
                reads("sartorius", ("region",), "draw")
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
            if any(
                r["assignments"]["codes"].get("semitendinosus") in NAMED
                for r in main_records
            ):
                reads("semitendinosus", ("region",), "draw")
            if any(
                r["assignments"]["codes"].get("popliteus_tendon") in NAMED
                for r in main_records
            ):
                reads("popliteus_tendon", ("region",), "draw")
            if any(
                r["assignments"]["codes"].get("gracilis") in NAMED for r in main_records
            ):
                reads("gracilis", ("region",), "draw")
            # the bursa, which the semimembranosus tendon's slice names
            if any(
                r["assignments"]["codes"].get("gastrocnemius_semimembranosus_bursa")
                == "identified"
                for r in main_records
            ):
                reads("bursa", ("region",), "draw")
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
        # what the views say of each object, grouped by object, provenance and property: the
        # operation's output of anatomy, kept in the interiors receipt beside its records
        "objects": describe_objects(records + main_records),
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
        result["objects"],
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
    root: Path,
) -> list[Path]:
    """Draw one study from the saved run, once it is in the receipts; return its pictures. The
    renderers are imported here, so a run that draws nothing never loads the drawing layer."""
    import object_assignments
    import object_bones
    import object_interiors
    import object_joint
    import object_patella
    import object_recess

    uid = result["study_uid"]
    pictures: list[Path] = []
    if result["records"]:
        object_interiors.draw(run_dir, uid, out)
        object_assignments.draw(run_dir, uid, assignments_out)
        pictures += [out / "series.png", assignments_out / "series.png"]
        # the femur's and the tibia's profile and pointed planes, from the series' own pixels
        volumes = {
            x.row.series_uid: x.volume for x in read_study(opened(root), uid).series
        }
        pictures += object_bones.draw(run_dir, uid, out / "bones", lambda u: volumes[u])
        # the patella's profile and pointed planes, and the tendons and pads read beside them
        pictures += object_patella.draw(
            run_dir, uid, out / "patella", lambda u: volumes[u]
        )
        # the joint's four profiles, its pointed planes and what the existing rules read on them
        pictures += object_joint.draw(run_dir, uid, out / "joint", lambda u: volumes[u])
        # the fluid pointer's profile, its pointed planes and what the existing rules read on them
        pictures += object_recess.draw(
            run_dir, uid, out / "recess", lambda u: volumes[u]
        )
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
    seen = ", ".join(
        f"{name} {len(entry['native_series'])}/"
        f"{sum(len(v) for kinds in entry['observations'].values() for v in kinds.values())}"
        for name, entry in result["objects"].items()
    )
    print(
        f"  objects (series that resolved it natively/properties kept): {seen}",
        flush=True,
    )
    print(f"  computed once and handed on: {shared or 'nothing'}", flush=True)
    if args.draw:
        for picture in draw_study(
            result,
            args.run,
            args.out / uid,
            args.assignments_out / uid,
            args.main_run,
            args.main_out / uid,
            args.root,
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
        help="development only: draw each study's pictures, and read what only they read (each "
        "middle slice's border readings); off by default, as in competition, where a run reads "
        "no border",
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
