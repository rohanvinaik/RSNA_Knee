"""Small parts read over their own outline: the part's existing producer, on its located slice (W12).

When recall cannot settle a question, the thesis returns it to the structure's own path (What an
<Object> Is §11.2) and spends fine work only where the coarse reading points (§13.4). Rohan's
decision (SQUINT_TRAINING_BUILD §10): the small parts the 10 mm squint cannot isolate are read over
their own outline whenever one of their questions is decided, once per part per study and shared by
every question; until then their comparison may only grade within "open". Here a located part asks
its named, existing native producer to resolve it on the slice the squint located; the support the
producer finds becomes a territory (origin ``residual_native_support``, mapped to tiles exactly as
the teacher cases' saved outlines are) and the territory writer the teacher cases are written with
(``squint_profiles.profile_territory`` and ``refine_territory``) writes its 10 mm and 2 mm banks over
that support. That reading replaces the part's expected-area reading (``own_outline``); the replaced
profile is kept beside it. Finer histograms alone are not every anatomical measurement.

THE PRODUCERS (``PRODUCERS``). The medial and lateral menisci, the MCL, the femoral and tibial
cartilage and the joint fluid are named by the original coronal rule of ``knee.objects.assignments``
(RESOLVING_THE_PARTS §5; the module note's MENISCI, MCL, ARTICULAR CARTILAGE and JOINT FLUID
paragraphs): on a fat-suppressed coronal slice the femur and tibia are the deepest territory and the
deepest one above or below it along the leg, the joint is what lies between them; the menisci are the
thick low signal touching the joint, the piece nearest each end, sided toward the other knee from
the header's word for which knee; the MCL is the low signal on the medial meniscus's side joining
both bones; the cartilage is the joint's places brighter than the bones' marrow within its reach of
a bone, named for the nearer bone; the fluid is the white four times the marrow's light touching the
joint or a bone. The lens is ``knee.objects.interiors.interior_regions`` on the squint's own lens
scope (``lens_scope``), the field is ``read_field`` and the naming is ``assign_plane``: the same
calls, scope and constants the runner's ``name_plane`` makes for a slice, pinned equal by the tests.
One naming of a slice serves every part named on it, once per study. Nothing here is a new detector.

THE REGION. The squint points to a series and a slice (the request's ``tile_window``). The rule's
identities are defined over the leg on that slice: its femur and tibia are the slice's deepest
territories, and a meniscus is named by the end of the whole joint it lies at. A crop narrower than
the leg changes those identities (W12's record, proof study: a joint-level band split the femur
into two condyle territories and named a piece by the notch "lateral meniscus"), so the producer
reads the located slice within the squint's lens scope, never the whole series and never another
series. Whether the support lies inside the request's window is recorded, not decisive: the window
is an address from the squint, the support is the part's own place by its rule. Over-reach, stated
and not chased: the definitions were demonstrated on the middle slice; on the proof study's located
off-middle slices the named medial meniscus (slice 18, where the rule's femur is a full-height
medial territory) and MCL (slice 12) were the medial condyle's dark subchondral band above the
articular line (W12's record).

Parts without a producer here are named in ``UNAVAILABLE`` with their existing rule and what it
needs that the squint route does not hold; they return ``procedure_unavailable`` and write nothing,
never a finer histogram in their place.

READINGS HELD. A profile's source says which readings it holds (``held_readings``): each reading is
its procedure, series, scale and address (a tile window, or a territory with its origin, roles and
native support digest). A request for a reading the part already holds returns ``already_measured``
and writes nothing; the own-outline step runs once per part per study, and a second call returns
its first answer without reading again.

Every refusal has a named code (``squint_interfaces.RESIDUAL_CODES``) and a named reason.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from knee.collapse.noise import background_split, finite_values
from knee.collapse.physical import PlaneFrame
from knee.collapse.squint_stack import SquintStack
from knee.diagnosis.squint_interfaces import (
    RESIDUAL_REQUEST_SCHEMA,
    RESIDUAL_RESULT_SCHEMA,
    ROLE_OBJECT,
    ROLE_UNQUERIED,
    TERRITORY_PROCEDURE,
    leg_map_code,
    residual_request_code,
    residual_result_code,
    territory_code,
)
from knee.objects.assignments import (
    OBJECT_CODES,
    assign_plane,
    axes_in_plane,
    margin,
    read_field,
)
from knee.objects.interiors import full_frame_scope, interior_regions, lens_scope
from knee.study.series import Series

__all__ = [
    "FINE_TILE_MM",
    "LENS_PROMINENCE_MM",
    "OWN_OUTLINE_REASON",
    "OWN_OUTLINE_SCHEMA",
    "PRODUCERS",
    "UNAVAILABLE",
    "Producer",
    "held_readings",
    "holds_reading",
    "own_outline",
    "producer_for",
    "producer_table",
    "reading_identity",
    "residual_record",
    "run_residual",
]

#: The lens's interior peaks are prominent by 3 mm: the runner's ``PROMINENCE_MM``
#: (scripts/run_interiors.py; RESOLVING_THE_PARTS §3 lens 4). Pinned equal by the tests.
LENS_PROMINENCE_MM = 3.0
#: The paired finer rung the territory writer refines at, the 2 mm of
#: ``squint_questions.CHEAP_SCALES_MM`` and ``refine_territory``'s default.
FINE_TILE_MM = 2.0
#: The reason a request carries when the pipeline reads a small part over its own outline.
OWN_OUTLINE_REASON = "small_part_own_outline"
OWN_OUTLINE_SCHEMA = "knee.squint-own-outline/v1"
_V1_PROCEDURE = "knee.squint-profile/scan-tercile-v1"
_RESULT_PRECEDENCE = (
    "measured",
    "already_measured",
    "no_compatible_reading",
    "deadline_before_residual",
    "object_region_unavailable",
    "procedure_unavailable",
)
_NAMINGS = "_residual_slice_namings"


@dataclass(frozen=True, slots=True)
class Producer:
    """One part's existing native producer, as the squint route can invoke it."""

    lens: str
    object_code: str
    code_keys: tuple[str, ...]
    definition: str
    inputs: tuple[str, ...]
    squint_route_has: tuple[str, ...]
    cost: str
    region: str
    view: str


_CORONAL_NAMING = "knee.objects.assignments.assign_plane/fat-suppressed-coronal-slice"
_CORONAL_INPUTS = (
    "the located slice's acquired signal (native_series.volume[z])",
    "the series' background split (the leg map's recorded split, else measured once)",
    "the squint's lens scope for that slice (lens_scope over the 10 mm tiles)",
    "the slice's frame (geometry), black margin and field",
    "the header's word for which knee (Laterality) and the series' tags",
)
_CORONAL_HAS = (
    "read_study_squints keeps native_series (volume, geometry, slice headers, tags)",
    "the series' SquintStack (maximum, coverage, bounds_rc) for the lens scope",
    "study['leg_maps'] (squint_leg.leg_maps) with the measured background split",
)
_CORONAL_COST = (
    "per located slice, shared by every part named on it: one scoped interior_regions (EDT, "
    "h-maxima, watershed), read_field and assign_plane; per part one profile_territory and "
    "one 2 mm refine_territory"
)
_CORONAL_REGION = (
    "the located slice within the squint's lens scope; the rule's femur, tibia and joint "
    "ends are defined over the leg on that slice"
)
_CORONAL_VIEW = (
    "fat-suppressed slice with side to side and along the leg in its plane (coronal); "
    "the definitions lay the fat-bright twin's parts from it"
)


def _coronal(object_code: str, code_keys: tuple[str, ...], definition: str) -> Producer:
    return Producer(
        lens=_CORONAL_NAMING,
        object_code=object_code,
        code_keys=code_keys,
        definition=definition,
        inputs=_CORONAL_INPUTS,
        squint_route_has=_CORONAL_HAS,
        cost=_CORONAL_COST,
        region=_CORONAL_REGION,
        view=_CORONAL_VIEW,
    )


_MENISCUS_KEYS = ("femur", "joint", "meniscus", "meniscus_side")
PRODUCERS: Mapping[str, Producer] = {
    "medial_meniscus": _coronal(
        "medial_meniscus",
        _MENISCUS_KEYS,
        "RESOLVING_THE_PARTS §5 menisci; assignments module note MENISCI: the thick low "
        "signal touching the joint, the piece nearest each end, the medial toward the other "
        "knee from the header",
    ),
    "lateral_meniscus": _coronal(
        "lateral_meniscus",
        _MENISCUS_KEYS,
        "RESOLVING_THE_PARTS §5 menisci; assignments module note MENISCI: the piece nearest "
        "the joint's end away from the other knee",
    ),
    "mcl": _coronal(
        "mcl",
        (*_MENISCUS_KEYS, "mcl"),
        "RESOLVING_THE_PARTS §5 MCL; assignments ligament_on_the_inner_side: the low signal "
        "outside every part named on the medial meniscus's side of the joint's middle, the "
        "largest piece reaching within 2 mm of both bones",
    ),
    "femoral_cartilage": _coronal(
        "femoral_cartilage",
        ("femur", "joint", "cartilage"),
        "RESOLVING_THE_PARTS §5 articular cartilage; assignments cartilage_on: the joint's "
        "places brighter than the bones' marrow (1.5 times) within 3 mm of a bone, the "
        "femur's where the femur is nearer",
    ),
    "tibial_cartilage": _coronal(
        "tibial_cartilage",
        ("femur", "joint", "cartilage"),
        "RESOLVING_THE_PARTS §5 articular cartilage; assignments cartilage_on: the joint's "
        "places brighter than the bones' marrow (1.5 times) within 3 mm of a bone, the "
        "tibia's where the tibia is nearer",
    ),
    "joint_fluid": _coronal(
        "joint_fluid",
        ("femur", "joint", "joint_fluid"),
        "RESOLVING_THE_PARTS §5 joint fluid; assignments fluid_in_the_recesses: outside every "
        "part named but the joint, four times the marrow's light, the pieces touching the "
        "joint or within 2 mm of a bone (fluid-sensitive, fat-suppressed)",
    ),
}

_NOT_ENABLED = "not enabled in this residual increment"
UNAVAILABLE: Mapping[str, str] = {
    "femur": (
        "existing rule: assign_plane's bone pairing on a slice where the leg runs in the "
        "plane; bone resolution in the squint route belongs to the structural anchors (W9)"
    ),
    "tibia": (
        "existing rule: assign_plane's bone pairing on a slice where the leg runs in the "
        "plane; bone resolution in the squint route belongs to the structural anchors (W9)"
    ),
    "fibula": (
        "existing rule: find_fibula on its own fat-bright sagittal slice, pointed by the "
        "squint corridor below the tibia (fibula_corridor, fibula_pointer, fibula_on_slice); "
        "needs the tibia named on the series' middle slice, which the squint route lacks"
    ),
    "patella": (
        "existing rule: assign_plane on a fat-suppressed sagittal slice (the deepest peak in "
        "front of the femur's lower end, as bright as its marrow); " + _NOT_ENABLED
    ),
    "acl": (
        "existing rule: acl_on_slice on its own slice beside the middle slice, with the femur "
        "and tibia carried from the series' middle-slice naming (carried_bone); the squint "
        "route has no middle-slice naming to carry"
    ),
    "pcl": (
        "existing rule: assign_plane on a non-fat-suppressed sagittal slice (the thick, "
        "uniformly dark band joining both bones); the coronal naming this executor runs does "
        "not name it; " + _NOT_ENABLED
    ),
    "joint": (
        "existing rule: assign_plane, what lies between the femur and tibia along the leg; a "
        "large part, read at squint scale"
    ),
    "patellar_cartilage": (
        "existing reader: patellofemoral_surface_reading on a fluid-sensitive fat-suppressed "
        "slice that names the patella and femur (a sagittal naming); " + _NOT_ENABLED
    ),
    "trochlear_cartilage": (
        "existing reader: patellofemoral_surface_reading on a fluid-sensitive fat-suppressed "
        "slice that names the patella and femur (a sagittal naming); " + _NOT_ENABLED
    ),
    "anterior_synovial_recess": (
        "existing rule: anterior_synovial_recess on a fat-suppressed sagittal slice that names "
        "the femur and patella; " + _NOT_ENABLED
    ),
    "synovium": (
        "existing rule: the anterior recess's lining edge (anterior_synovial_recess) on a "
        "fat-suppressed sagittal slice that names the femur and patella; "
        + _NOT_ENABLED
    ),
    "joint_capsule": (
        "existing rule: capsule_at_side_recesses on a fluid-sensitive coronal slice that names "
        "both menisci; " + _NOT_ENABLED
    ),
    "quadriceps_fat_pad": (
        "existing rule: suprapatellar_pads on the fat-suppressed sagittal with its fat-bright "
        "twin matched by place (relative_signal); needs that matched pair; "
        + _NOT_ENABLED
    ),
    "prefemoral_fat_pad": (
        "existing rule: suprapatellar_pads on the fat-suppressed sagittal with its fat-bright "
        "twin matched by place (relative_signal); needs that matched pair; "
        + _NOT_ENABLED
    ),
    "gastrocnemius_semimembranosus_bursa": (
        "existing rule: bursa_on_slice on the semimembranosus tendon's own axial slice "
        "(tibia_top_slice, found by carrying the leg's bones by place); the squint route "
        "holds no carried bones"
    ),
    "medial_gastrocnemius": (
        "existing rule: name_the_back_of_the_knee on the fat-suppressed axial middle slice "
        "with the femur and tibia carried by place and the notch from the middle sagittal; "
        "the squint route holds no carried bones"
    ),
    "semimembranosus": (
        "existing rule: semimembranosus_slice on the tibia's top axial slice, found by "
        "carrying the leg's bones by place; the squint route holds no carried bones"
    ),
}


def producer_for(subject: object) -> Producer | None:
    """The object's producer, or None when it is named in ``UNAVAILABLE`` or unknown."""
    return PRODUCERS.get(subject) if isinstance(subject, str) else None


def producer_table() -> dict[str, Any]:
    """The table, JSON-safe: each object's producer or its named unavailability."""
    rows: dict[str, Any] = {}
    for subject, producer in sorted(PRODUCERS.items()):
        rows[subject] = {
            "status": "available",
            "lens": producer.lens,
            "definition": producer.definition,
            "view": producer.view,
            "inputs": list(producer.inputs),
            "squint_route_has": list(producer.squint_route_has),
            "cost": producer.cost,
            "region": producer.region,
        }
    for subject, reason in sorted(UNAVAILABLE.items()):
        rows[subject] = {"status": "procedure_unavailable", "reason": reason}
    return rows


# ---------------------------------------------------------------------------
# readings held by a profile
# ---------------------------------------------------------------------------


def _sha256_json(value: object) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def reading_identity(
    procedure: str, series_uid: str, scale_mm: float, address: Mapping[str, Any]
) -> dict[str, Any]:
    """One reading: its procedure, series, scale and address, JSON-safe."""
    return {
        "procedure": procedure,
        "series_uid": series_uid,
        "scale_mm": float(scale_mm),
        "address": dict(address),
    }


def _key(identity: Mapping[str, Any]) -> str:
    return json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=True)


def _territory_address(territory: Mapping[str, Any]) -> dict[str, Any]:
    """A territory's address as a reading's: origin, window, roles, shares, support digest."""
    support = territory.get("native_support_address")
    return {
        "kind": "territory",
        "origin": territory.get("origin"),
        "tile_window": list(territory.get("tile_window") or ()),
        "roles_sha256": _sha256_json(territory.get("roles")),
        "object_share_sha256": _sha256_json(territory.get("object_share")),
        # The mask's digest names its bits only; its slices, offset and shape place it.
        "support": {
            key: support.get(key)
            for key in ("slices", "offset_rc", "shape", "mask_sha256")
        }
        if isinstance(support, Mapping)
        else None,
    }


def _leaf_identity(source: Mapping[str, Any]) -> dict[str, Any] | None:
    """The identity of one writer call's source, or None when it is not attributable."""
    procedure = source.get("procedure")
    context = source.get("series_context")
    context = context if isinstance(context, Mapping) else {}
    territory = source.get("territory")
    series_uid = context.get("series_uid")
    if not isinstance(series_uid, str) and isinstance(territory, Mapping):
        series_uid = territory.get("series_uid")
    if not isinstance(procedure, str) or not isinstance(series_uid, str):
        return None
    refined = source.get("refinement") is True
    scale = source.get("fine_tile_mm") if refined else context.get("tile_mm")
    if isinstance(scale, bool) or not isinstance(scale, (int, float)):
        return None
    if isinstance(territory, Mapping):
        address = _territory_address(territory)
    else:
        window = source.get("coarse_window") if refined else source.get("window")
        if not isinstance(window, (list, tuple)):
            return None
        address = {"kind": "tile_window", "window": [int(value) for value in window]}
    return reading_identity(procedure, series_uid, float(scale), address)


def _walk(source: object, found: dict[str, dict[str, Any]], depth: int = 0) -> None:
    if not isinstance(source, Mapping) or depth > 64:
        return
    for item in source.get("readings", ()) or ():
        if isinstance(item, Mapping):
            found.setdefault(_key(item), dict(item))
    lineage = source.get("lineage")
    if isinstance(lineage, Sequence) and not isinstance(lineage, (str, bytes)):
        for item in lineage:
            _walk(item, found, depth + 1)
        return
    identity = _leaf_identity(source)
    if identity is not None:
        found.setdefault(_key(identity), identity)


def held_readings(profile: object) -> list[dict[str, Any]]:
    """Every attributable reading a profile holds, from its source and lineage, sorted."""
    if not isinstance(profile, Mapping):
        return []
    found: dict[str, dict[str, Any]] = {}
    _walk(profile.get("source"), found)
    return [found[key] for key in sorted(found)]


def holds_reading(
    profile: object, *, series_uid: str, window: Sequence[int], scale_mm: float
) -> bool:
    """Whether a profile already holds the v1 squint reading of this series window and scale."""
    wanted = _key(
        reading_identity(
            _V1_PROCEDURE,
            series_uid,
            scale_mm,
            {"kind": "tile_window", "window": [int(value) for value in window]},
        )
    )
    return any(_key(item) == wanted for item in held_readings(profile))


def _records(located: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Every residual record kept for one part: its own-outline step's and any other's."""
    own = located.get("own_outline")
    found = list(own.get("results", ()) or ()) if isinstance(own, Mapping) else []
    found.extend(located.get("residual", ()) or ())
    return [record for record in found if isinstance(record, Mapping)]


def _held_keys(located: object) -> set[str]:
    if not isinstance(located, Mapping):
        return set()
    keys = {_key(item) for item in held_readings(located.get("profile"))}
    for record in _records(located):
        if record.get("code") == "measured":
            keys.update(_key(item) for item in record.get("readings", ()) or ())
    return keys


def _answered(located: object) -> dict[tuple[str, str, tuple[int, ...]], Mapping]:
    """(lens, series, slices) this object's residual already answered, with that answer.

    The producer reads the whole located slice, so a second request for the same producer,
    series and slices has the same answer: a measured one is held (``already_measured``), a
    refused one keeps its code, and neither is computed again.
    """
    if not isinstance(located, Mapping):
        return {}
    answered: dict[tuple[str, str, tuple[int, ...]], Mapping] = {}
    for record in _records(located):
        if (
            record.get("code") in ("measured", "no_compatible_reading")
            and isinstance(record.get("lens"), str)
            and isinstance(record.get("series_uid"), str)
        ):
            key = (
                record["lens"],
                record["series_uid"],
                tuple(int(z) for z in record.get("slices", ())),
            )
            answered.setdefault(key, record)
    return answered


# ---------------------------------------------------------------------------
# the producer on one located slice
# ---------------------------------------------------------------------------


def _series_by_uid(study: object, series_uid: str) -> dict[str, Any] | None:
    rows = study.get("series", ()) if isinstance(study, Mapping) else ()
    for row in rows if isinstance(rows, Sequence) else ():
        if isinstance(row, dict) and row.get("series_uid") == series_uid:
            return row
    return None


def _leg_map(study: dict, series: dict) -> tuple[dict | None, str, float]:
    """The series' shared leg map: the study's, else measured once for the study and kept."""
    maps = study.get("leg_maps") if isinstance(study, dict) else None
    started = time.perf_counter()
    source = "study_shared"
    if maps is None:
        try:
            from knee.diagnosis.squint_leg import leg_maps
        except ImportError:
            return None, "leg_map_producer_unavailable", 0.0
        try:
            maps = leg_maps(study)
        except (TypeError, ValueError) as error:
            return None, f"leg_map_unavailable:{error}", time.perf_counter() - started
        study["leg_maps"] = maps
        source = "measured_by_residual_and_kept_for_the_study"
    seconds = time.perf_counter() - started
    leg = maps.get(series["series_uid"]) if isinstance(maps, Mapping) else None
    if leg is None:
        return None, "leg_map_missing_for_series", seconds
    return leg, source, seconds


def _split(series: dict, leg: Mapping[str, Any]) -> tuple[float, str]:
    """The series' background split: the leg map's recorded measurement, else measured."""
    provenance = leg.get("provenance")
    record = (
        provenance.get("background_split") if isinstance(provenance, Mapping) else None
    )
    if isinstance(record, Mapping) and record.get("code") == "measured":
        value = record.get("value")
        if (
            not isinstance(value, bool)
            and isinstance(value, (int, float))
            and math.isfinite(value)
        ):
            return float(value), "leg_map_recorded_background_split"
    supplied = series.get("background_split")
    if (
        not isinstance(supplied, bool)
        and isinstance(supplied, (int, float))
        and math.isfinite(supplied)
    ):
        return float(supplied), "series_supplied_background_split"
    native = series.get("native_series")
    volume = getattr(native, "volume", None)
    if volume is None:
        return float("nan"), "native_volume_unavailable"
    return float(background_split(finite_values(volume))), "measured_background_split"


def _frame(native: Series, z: int) -> PlaneFrame | None:
    geometry = native.geometry
    if geometry is None:
        return None
    try:
        return PlaneFrame.from_dicom(
            geometry.position[z], geometry.orientation[z], geometry.spacing[z]
        )
    except (IndexError, ValueError):
        return None


def _scope(stack: SquintStack, z: int, split: float, shape: tuple[int, int]):
    """The squint's lens scope for one slice, as the runner's ``lens_scopes_of`` makes it."""
    if stack.code != "present":
        return full_frame_scope(shape, reason=stack.why or stack.code)
    try:
        return lens_scope(
            stack.maximum[z], stack.coverage[z], stack.bounds_rc, split, shape
        )
    except ValueError as error:
        return full_frame_scope(
            shape,
            reason=f"invalid squint scope inputs: {error}",
            tile_shape=np.shape(stack.maximum[z]),
        )


def _name_slice(
    native: Series, stack: SquintStack, z: int, split: float, frame: PlaneFrame
) -> tuple[Any, dict[str, Any]]:
    """The located slice named as the runner's ``name_plane`` names a slice, without drawing."""
    if native.volume is None:
        raise ValueError("native_volume_unavailable")
    plane = native.volume[z]
    scope = _scope(stack, z, split, (int(plane.shape[0]), int(plane.shape[1])))
    reading = interior_regions(
        plane,
        frame.spacing_rc,
        split,
        LENS_PROMINENCE_MM,
        available=np.isfinite(plane),
        scope=scope,
    )
    outside = margin(plane)
    field = read_field(plane, reading, frame.basis_lps, outside)
    knee = str(getattr(native.slices[z].header, "Laterality", "") or "").strip()
    assignment = assign_plane(
        plane,
        reading,
        frame.basis_lps,
        knee,
        int(native.row.fat_suppression) == 1,
        int(native.row.fluid_sensitive) == 1,
        outside,
        field,
        None,
    )
    r0, r1, c0, c1 = (int(value) for value in scope.window_rc)
    evidence = {
        "slice": z,
        "knee": knee,
        "lens_code": reading.code,
        "territories": int(reading.labels.max(initial=0)),
        "scope_code": scope.code,
        "scope_reason": scope.reason,
        "scope_window_rc": [r0, r1, c0, c1],
        "scope_window_pixels": max(0, r1 - r0) * max(0, c1 - c0),
        "full_frame_pixels": int(plane.size),
        "femur_territory": assignment.femur,
        "tibia_territory": assignment.tibia,
        "codes": dict(assignment.codes),
        "named_pixels": {
            name: int(np.count_nonzero(assignment.objects == code))
            for name, code in OBJECT_CODES.items()
            if name != "unassigned" and np.any(assignment.objects == code)
        },
    }
    return assignment, evidence


def _named_slice(
    study: dict,
    native: Series,
    stack: SquintStack,
    z: int,
    split: float,
    frame: PlaneFrame,
) -> tuple[Any, dict[str, Any], bool]:
    """One slice's naming, made once per study and handed to every part named on it.

    Kept on the study record (runtime-only, released with the study), keyed by the series,
    the slice and the split it was read under. Returns whether this call made it.
    """
    namings = study.setdefault(_NAMINGS, {}) if isinstance(study, dict) else {}
    key = (native.row.series_uid, int(z), float(split))
    held = namings.get(key)
    if held is not None:
        return held[0], held[1], False
    assignment, evidence = _name_slice(native, stack, z, split, frame)
    namings[key] = (assignment, evidence)
    return assignment, evidence, True


def _territory(
    study_uid: str,
    series: dict,
    subject: str,
    supports: dict[int, np.ndarray],
    leg: Mapping[str, Any],
    provenance: dict[str, Any],
) -> dict[str, Any]:
    """Map the found support to tiles exactly as teacher supports are mapped; origin residual."""
    from knee.diagnosis.squint_support import teacher_territory

    per_slice = []
    for z in sorted(supports):
        mask = supports[z]
        rows, cols = np.nonzero(mask)
        mapped = teacher_territory(
            study_uid,
            series,
            subject,
            {
                "code": "resolved",
                "mask": mask,
                "bbox": (
                    int(rows.min()),
                    int(rows.max()) + 1,
                    int(cols.min()),
                    int(cols.max()) + 1,
                ),
                "source_address": {
                    "target_series_uid": series["series_uid"],
                    "observation_slices": [z],
                    "address_kind": "native_rc",
                    "producer": provenance["lens"],
                },
                "provenance": {"resolver": "residual_native_producer"},
            },
            z,
            dict(leg),
        )
        if mapped.get("code") != "resolved":
            return {"code": mapped.get("code", "support_unmapped")}
        per_slice.append(mapped)
    if len(per_slice) == 1:
        territory = dict(per_slice[0])
    else:
        territory = _stacked(per_slice)
    territory["origin"] = "residual_native_support"
    territory["provenance"] = {
        **provenance,
        "tile_mapping": (
            "squint_support.teacher_territory: tiles the support covers are object tiles, "
            "one ring of context tiles, tiles the leg map calls outside suppressed"
        ),
        "mapped_slices": [int(z) for z in sorted(supports)],
    }
    code = territory_code(territory, grid_shape=series["stack"].median.shape)
    if code != "valid":
        return {"code": code}
    return territory


def _stacked(per_slice: list[dict[str, Any]]) -> dict[str, Any]:
    """Several one-slice territories as one window; tiles no slice queried stay unqueried."""
    windows = [item["tile_window"] for item in per_slice]
    z0 = min(w[0] for w in windows)
    z1 = max(w[1] for w in windows)
    r0 = min(w[2] for w in windows)
    r1 = max(w[3] for w in windows)
    c0 = min(w[4] for w in windows)
    c1 = max(w[5] for w in windows)
    roles = np.full((z1 - z0, r1 - r0, c1 - c0), ROLE_UNQUERIED, dtype=np.int8)
    share = np.full(roles.shape, np.nan, dtype=np.float64)
    masks = []
    for item in per_slice:
        w = item["tile_window"]
        address = (
            slice(w[0] - z0, w[1] - z0),
            slice(w[2] - r0, w[3] - r0),
            slice(w[4] - c0, w[5] - c0),
        )
        roles[address] = item["roles"]
        share[address] = item["object_share"]
        masks.append(item["native_support"])
    top = min(m["offset_rc"][0] for m in masks)
    left = min(m["offset_rc"][1] for m in masks)
    bottom = max(m["offset_rc"][0] + m["mask"].shape[1] for m in masks)
    right = max(m["offset_rc"][1] + m["mask"].shape[2] for m in masks)
    stack = np.zeros((len(masks), bottom - top, right - left), dtype=np.bool_)
    for index, m in enumerate(masks):
        sr, sc = m["offset_rc"][0] - top, m["offset_rc"][1] - left
        stack[index, sr : sr + m["mask"].shape[1], sc : sc + m["mask"].shape[2]] = m[
            "mask"
        ][0]
    first = per_slice[0]
    return {
        **{k: v for k, v in first.items() if k not in ("tile_window", "roles")},
        "tile_window": [z0, z1, r0, r1, c0, c1],
        "roles": roles,
        "object_share": share,
        "native_support": {
            "mask": stack,
            "slices": [int(m["slices"][0]) for m in masks],
            "offset_rc": [int(top), int(left)],
        },
        "key_planes": {
            key: value
            for item in per_slice
            for key, value in (item.get("key_planes") or {}).items()
        },
    }


def _support_address(territory: Mapping[str, Any]) -> dict[str, Any]:
    support = territory["native_support"]
    return {
        "slices": [int(z) for z in support["slices"]],
        "offset_rc": [int(v) for v in support["offset_rc"]],
        "shape": [int(v) for v in support["mask"].shape],
        "support_count": int(np.count_nonzero(support["mask"])),
        "mask_sha256": hashlib.sha256(support["mask"].tobytes()).hexdigest(),
    }


def _in_window_share(
    stack: SquintStack, window: Sequence[int], supports: dict[int, np.ndarray]
) -> float:
    """The share of support pixels inside the request's tile window (an address check only)."""
    z0, z1, r0, r1, c0, c1 = (int(v) for v in window)
    bounds = np.asarray(stack.bounds_rc)
    pr0, pr1 = int(bounds[r0, 0, 0]), int(bounds[r1 - 1, 0, 1])
    pc0, pc1 = int(bounds[0, c0, 2]), int(bounds[0, c1 - 1, 3])
    total = inside = 0
    for z, mask in supports.items():
        total += int(np.count_nonzero(mask))
        if z0 <= z < z1:
            inside += int(np.count_nonzero(mask[pr0:pr1, pc0:pc1]))
    return inside / total if total else 0.0


def run_residual(
    request: Mapping[str, Any],
    study: dict[str, Any],
    objects: Mapping[str, Any],
    *,
    deadline: float | None = None,
) -> dict[str, Any]:
    """Run one part's existing producer on its located slice and write banks over its support.

    ``request`` is a ``squint_interfaces`` residual request (a malformed one raises
    ``ValueError`` with the validator's code); the pipeline builds it for a located part, with
    reason ``OWN_OUTLINE_REASON`` (``own_outline`` does this for every located region).
    ``objects`` is read, never written; ``study`` keeps the shared leg maps and slice namings.
    The result carries the territory, the merged 10 mm and 2 mm territory profile, the readings
    it holds and the cost. Codes, in order of the checks: ``procedure_unavailable`` (no
    producer, another lens, or a view the definition does not read), ``already_measured``,
    ``deadline_before_residual``, ``object_region_unavailable``, ``no_compatible_reading`` (the
    producer named no support, or no compatible bank could be written) and ``measured``. Never a
    full-anatomy run, never a guessed support.
    """
    started = time.perf_counter()
    code = residual_request_code(request)
    if code != "valid":
        raise ValueError(f"residual_request_invalid:{code}")
    subject = request["subject"]
    series_uid = request["series_uid"]
    window = [int(v) for v in request["tile_window"]]
    slices = list(range(window[0], window[1]))
    cost: dict[str, Any] = {
        "native_slices_read": 0,
        "native_slices_shared": 0,
        "native_pixels_read": 0,
    }

    def result(outcome: str, reason: str, **extra: Any) -> dict[str, Any]:
        cost["seconds"] = time.perf_counter() - started
        value = {
            "schema": RESIDUAL_RESULT_SCHEMA,
            "code": outcome,
            "reason": reason,
            "subject": subject,
            "lens": request["lens"],
            "question_id": request["question_id"],
            "series_uid": series_uid,
            "slices": slices,
            "request": {k: request[k] for k in sorted(request)},
            "cost": cost,
            **extra,
        }
        checked = residual_result_code(value)
        if checked != "valid":
            raise RuntimeError(f"residual_result_invalid:{checked}")
        return value

    producer = producer_for(subject)
    if producer is None:
        return result(
            "procedure_unavailable",
            UNAVAILABLE.get(subject, "no_existing_bounded_native_producer_named"),
        )
    if request["lens"] != producer.lens:
        return result(
            "procedure_unavailable", "request_lens_is_not_this_objects_producer"
        )
    located = objects.get(subject) if isinstance(objects, Mapping) else None
    previous = _answered(located).get((producer.lens, series_uid, tuple(slices)))
    if previous is not None and previous["code"] == "measured":
        return result(
            "already_measured", "same_producer_series_and_slices_already_held"
        )
    if previous is not None:
        return result(
            previous["code"], "same_request_already_answered:" + str(previous["reason"])
        )
    if deadline is not None and time.monotonic() >= deadline:
        return result(
            "deadline_before_residual", "study_deadline_reached_before_the_run"
        )
    series = _series_by_uid(study, series_uid)
    if series is None:
        return result("object_region_unavailable", "series_not_in_study")
    native = series.get("native_series")
    stack = series.get("stack")
    if (
        not isinstance(native, Series)
        or native.volume is None
        or native.geometry is None
        or not isinstance(stack, SquintStack)
    ):
        return result(
            "object_region_unavailable", "native_series_or_squint_unavailable"
        )
    if stack.code != "present" or np.ndim(stack.median) != 3:
        return result("object_region_unavailable", f"squint_{stack.code}")
    depth, rows, cols = (int(n) for n in stack.median.shape)
    _z0, z1, _r0, r1, _c0, c1 = window
    if z1 > depth or r1 > rows or c1 > cols or z1 > len(native.volume):
        return result("object_region_unavailable", "window_outside_squint_grid")
    if str(native.row.fat_suppression) != "1":
        return result(
            "procedure_unavailable",
            "definition_names_these_on_the_fat_suppressed_coronal; laying onto the "
            "fat-bright twin is not run by this executor",
        )
    frames: dict[int, PlaneFrame] = {}
    for z in slices:
        frame = _frame(native, z)
        if frame is None:
            return result("object_region_unavailable", "slice_geometry_unreadable")
        frames[z] = frame
    sides, _front, along = axes_in_plane(frames[slices[0]].basis_lps)
    if not (sides and along):
        return result(
            "procedure_unavailable",
            "rule_reads_a_slice_with_side_to_side_and_the_leg_in_its_plane (coronal)",
        )
    leg, leg_source, leg_seconds = _leg_map(study, series)
    cost.update(leg_maps=leg_source, leg_maps_seconds=leg_seconds)
    if leg is None:
        return result("no_compatible_reading", leg_source)
    leg_code = leg_map_code(leg, grid_shape=stack.median.shape)
    if leg_code != "valid":
        return result("no_compatible_reading", leg_code)
    split, split_source = _split(series, leg)
    cost["background_split_source"] = split_source
    if not math.isfinite(split):
        return result(
            "no_compatible_reading", f"background_split_unavailable:{split_source}"
        )

    producer_started = time.perf_counter()
    supports: dict[int, np.ndarray] = {}
    evidence = []
    label = OBJECT_CODES[producer.object_code]
    for z in slices:
        try:
            assignment, named, made = _named_slice(
                study, native, stack, z, split, frames[z]
            )
        except (TypeError, ValueError) as error:
            cost["producer_seconds"] = time.perf_counter() - producer_started
            return result("object_region_unavailable", f"producer_refused:{error}")
        if made:
            cost["native_slices_read"] += 1
            cost["native_pixels_read"] += named["scope_window_pixels"]
        else:
            cost["native_slices_shared"] += 1
        evidence.append(named)
        mask = assignment.objects == label
        if mask.any():
            supports[z] = np.asarray(mask, dtype=np.bool_)
    cost["producer_seconds"] = time.perf_counter() - producer_started
    cost["full_frame_pixels"] = sum(item["full_frame_pixels"] for item in evidence)
    producer_record = {
        "lens": producer.lens,
        "definition": producer.definition,
        "background_split": split,
        "slices": evidence,
    }
    if not supports:
        codes = evidence[0]["codes"]
        reason = f"{producer.object_code}_not_named:" + ",".join(
            f"{key}={codes.get(key)}" for key in producer.code_keys
        )
        return result("no_compatible_reading", reason, producer=producer_record)

    writer_started = time.perf_counter()
    territory = _territory(
        study.get("study_uid", ""),
        series,
        subject,
        supports,
        leg,
        {
            "lens": producer.lens,
            "question_id": request["question_id"],
            "request_tile_window": window,
            "request_reason": request["reason"],
            "background_split": split,
            "background_split_source": split_source,
            "leg_map_rule": leg.get("rule"),
        },
    )
    if "schema" not in territory:
        return result(
            "no_compatible_reading",
            f"support_not_mappable:{territory['code']}",
            producer=producer_record,
        )
    support_address = _support_address(territory)
    address = _territory_address(
        {
            **territory,
            "roles": territory["roles"].tolist(),
            "object_share": np.where(
                np.isfinite(territory["object_share"]), territory["object_share"], None
            ).tolist(),
            "native_support_address": support_address,
        }
    )
    readings = [
        reading_identity(TERRITORY_PROCEDURE, series_uid, stack.tile_mm, address),
        reading_identity(TERRITORY_PROCEDURE, series_uid, FINE_TILE_MM, address),
    ]
    held = _held_keys(located)
    if any(_key(item) in held for item in readings):
        return result(
            "already_measured",
            "same_reading_already_held",
            producer=producer_record,
            readings=readings,
        )
    from knee.diagnosis.squint_profiles import (
        merge_profiles,
        profile_territory,
        refine_territory,
    )

    try:
        coarse = profile_territory(series, territory, leg, subject=subject)
        fine = refine_territory(
            series, territory, leg, subject=subject, tile_mm=FINE_TILE_MM
        )
        profile = merge_profiles((coarse, fine), subject=subject)
    except (TypeError, ValueError) as error:
        return result(
            "no_compatible_reading",
            f"territory_writer_refused:{error}",
            producer=producer_record,
        )
    cost["writer_seconds"] = time.perf_counter() - writer_started
    if not profile["banks"]:
        return result(
            "no_compatible_reading",
            "territory_writer_wrote_no_bank",
            producer=producer_record,
        )
    profile["source"]["readings"] = readings
    profile["source"]["residual"] = {
        "lens": producer.lens,
        "question_id": request["question_id"],
        "series_uid": series_uid,
        "slices": slices,
        "support": support_address,
    }
    return result(
        "measured",
        "native_support_found",
        territory=territory,
        profile=profile,
        readings=readings,
        support=support_address,
        support_in_request_window_share=_in_window_share(stack, window, supports),
        object_tiles=int(np.count_nonzero(territory["roles"] == ROLE_OBJECT)),
        producer=producer_record,
    )


# ---------------------------------------------------------------------------
# the consumer side: one part read over its own outline, once per study
# ---------------------------------------------------------------------------


def residual_record(result: Mapping[str, Any]) -> dict[str, Any]:
    """A result without its runtime arrays: what the study evidence retains."""
    record = {
        key: result[key]
        for key in (
            "code",
            "reason",
            "subject",
            "lens",
            "question_id",
            "series_uid",
            "slices",
            "readings",
            "support",
            "support_in_request_window_share",
            "object_tiles",
            "producer",
            "cost",
        )
        if key in result
    }
    record["request_tile_window"] = list(result["request"]["tile_window"])
    profile = result.get("profile")
    if isinstance(profile, Mapping):
        record["profile_bank_count"] = len(profile.get("banks", {}))
    return record


def own_outline(
    subject: str,
    study: dict[str, Any],
    objects: dict[str, Any],
    *,
    deadline: float | None = None,
    question_id: str = OWN_OUTLINE_REASON,
) -> dict[str, Any]:
    """Read one located part over its own outline, once per study, and replace its reading.

    Rohan's decision (SQUINT_TRAINING_BUILD §10): a small part is read over its own outline
    whenever one of its questions is decided, once per part per study, shared by every
    question. Each located region becomes a residual request (reason ``OWN_OUTLINE_REASON``)
    for the part's producer; the measured regions' territory profiles, one per series and
    slice, together replace the part's expected-area profile, which is kept beside it as
    ``expected_area_profile``. A part without a producer, or with no measured region, keeps
    its profile and the named reason. The returned record is JSON-safe and is kept as
    ``located['own_outline']``; a second call returns it again, reading nothing.
    """
    started = time.perf_counter()
    located = objects.get(subject) if isinstance(objects, Mapping) else None
    if isinstance(located, dict) and isinstance(located.get("own_outline"), Mapping):
        first = located["own_outline"]
        return {
            **first,
            "code": "already_measured"
            if first["code"] == "measured"
            else first["code"],
            "reason": "own_outline_already_read_for_this_part_in_this_study",
            "first_code": first["code"],
            "repeat": True,
            "results": [],
            "cost": {
                "seconds": 0.0,
                "native_slices_read": 0,
                "native_slices_shared": 0,
            },
        }
    producer = producer_for(subject)
    results: list[dict[str, Any]] = []

    def finish(code: str, reason: str, replaced: bool) -> dict[str, Any]:
        costs = [item.get("cost") or {} for item in results]
        record = {
            "schema": OWN_OUTLINE_SCHEMA,
            "code": code,
            "reason": reason,
            "subject": subject,
            "lens": producer.lens if producer is not None else None,
            "question_id": question_id,
            "profile_replaced": replaced,
            "results": results,
            "cost": {
                "seconds": time.perf_counter() - started,
                "regions": len(results),
                "native_slices_read": sum(
                    c.get("native_slices_read", 0) for c in costs
                ),
                "native_slices_shared": sum(
                    c.get("native_slices_shared", 0) for c in costs
                ),
                "native_pixels_read": sum(
                    c.get("native_pixels_read", 0) for c in costs
                ),
                "producer_seconds": sum(c.get("producer_seconds", 0.0) for c in costs),
                "writer_seconds": sum(c.get("writer_seconds", 0.0) for c in costs),
                "leg_maps_seconds": sum(c.get("leg_maps_seconds", 0.0) for c in costs),
            },
        }
        if isinstance(located, dict):
            located["own_outline"] = record
        return record

    if producer is None:
        return finish(
            "procedure_unavailable",
            UNAVAILABLE.get(subject, "no_existing_bounded_native_producer_named")
            if isinstance(subject, str)
            else "subject_invalid",
            False,
        )
    if not isinstance(located, dict):
        return finish("object_region_unavailable", "part_not_located", False)
    regions = located.get("regions", [])
    measured = []
    answered: dict[tuple[str, tuple[int, ...]], dict[str, Any]] = {}
    for region in regions:
        if not isinstance(region, Mapping):
            continue
        window = region.get("window", region.get("source_window"))
        request = {
            "schema": RESIDUAL_REQUEST_SCHEMA,
            "question_id": question_id or OWN_OUTLINE_REASON,
            "subject": subject,
            "series_uid": region.get("series_uid"),
            "reason": OWN_OUTLINE_REASON,
            "lens": producer.lens,
            "tile_window": list(window) if isinstance(window, (list, tuple)) else None,
        }
        code = residual_request_code(request)
        if code != "valid":
            results.append(
                {
                    "code": "object_region_unavailable",
                    "reason": code,
                    "series_uid": region.get("series_uid"),
                }
            )
            continue
        slices = tuple(range(int(window[0]), int(window[1])))
        same = answered.get((request["series_uid"], slices))
        if same is not None:
            # The producer reads the whole located slice: another window on it is the
            # same reading, already answered in this call and not read again.
            results.append(
                {
                    "code": "already_measured"
                    if same["code"] == "measured"
                    else same["code"],
                    "reason": "same_series_and_slices_already_read_for_this_part",
                    "subject": subject,
                    "lens": producer.lens,
                    "series_uid": request["series_uid"],
                    "slices": list(slices),
                    "request_tile_window": list(window),
                }
            )
            continue
        outcome = run_residual(request, study, objects, deadline=deadline)
        record = residual_record(outcome)
        results.append(record)
        answered[(request["series_uid"], slices)] = record
        if outcome["code"] == "measured":
            measured.append(outcome)
    if not results:
        return finish("object_region_unavailable", "no_located_region", False)
    if not measured:
        codes = [item.get("code") for item in results]
        overall = next(
            (code for code in _RESULT_PRECEDENCE if code in codes),
            "object_region_unavailable",
        )
        return finish(overall, "no_region_measured", False)
    from knee.diagnosis.squint_profiles import merge_profiles

    profiles = [item["profile"] for item in measured]
    profile = (
        profiles[0] if len(profiles) == 1 else merge_profiles(profiles, subject=subject)
    )
    profile["source"]["readings"] = held_readings(profile)
    located["expected_area_profile"] = located.get("profile")
    located["profile"] = profile
    return finish("measured", "own_outline_replaced_expected_area_profile", True)
