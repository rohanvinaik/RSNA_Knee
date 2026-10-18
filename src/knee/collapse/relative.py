"""The knee's 3D geometry: key planes -> one physical position -> vectors between objects -> where to look in each image.

(`docs/RELATIVE_POSITION_MAP.md` §0 and §8.8.) Pure, deterministic geometry and bookkeeping: no statistics, no
anatomy, no fitted numbers, no pixels. It holds MEASUREMENTS AND GEOMETRY ONLY; the anatomical ideal and the
studies' variation are separate inputs the caller grounds and supplies.

**Key plane** (`KeyPlane`). Rohan, 2026-10-17: «The "key slice" is just the one slice, seperately for each of the 3
different views [...] where the anatomy is most obvious.» A key plane is one object's selected slice in one
orientation, held as its physical plane (unit normal n and offset d, n·p = d, in the DICOM patient frame, LPS
millimetres) with its source series and native slice, the precision of its place (half the step to its
neighbour, NaN where unknown), and why and by whom it was selected. A selection that could not be made keeps its
outcome: `refused`, `tied` (with the tied candidates, never one picked), `absent_in_view` (the caller says the
object is not in that view), `not_supplied` (nobody was asked or read: unknown, never an absence), or
`invalid:<code>` where the geometry given cannot be a plane (zero, nonfinite or misshapen normal, no or
contradictory offset). The orientation LABEL says which view the plane was selected in; it never decides a
coordinate: the position is solved from the planes' actual normals and offsets, so oblique acquisitions work and
no raw axis index is read.

**Position** (`reference_position`). Three selected planes, one per orientation, give the object's reference
position by solving N p = d: the point on all three. Each coordinate's authority is its view's key plane; nothing
here reads a centroid, a section, a mask or an average. Fewer usable planes give a PARTIAL position: the
constraints that are known (a plane, or a line for two) and no point. Each orientation not usable says why, by
its own code (`problems`), and a repeated orientation (two planes for one view) is refused rather than pooled or
arbitrarily chosen. Singular means linear-algebra rank loss at floating precision (`numpy.linalg.matrix_rank`'s
tolerance, s_max * max(shape) * eps), not an anatomical threshold; the condition number and the per-axis precision
bound |N^-1| · (plane precisions) are kept. Reversing a plane's normal and offset together leaves the position
unchanged.

**Pair vectors** (`pair_vectors`, `reversed_vector`, `compose`). For every ordered pair of complete positions of
one study (one patient frame, so no coordinate mixing), the displacement in millimetres, its magnitude, unit
direction, the displacement and distance as proportions of an explicit positive finite knee scale
(`knee_scale`; unknown stays `scale_unknown`, never invented), and, where the header names the knee, the
displacement in the common anatomical orientation (medial, posterior, superior: a left knee is mirrored so both
knees read alike; an unnamed knee gives `knee_unknown`). v(b->a) is exactly -v(a->b); v(a->b) + v(b->c) is
v(a->c). Each carries the source planes of both ends. This is not the ideal map.

**Ideal and study kept apart.** `IdealVector` is anatomy's (the caller's grounded, sourced) displacement of one
object from another in the anatomical orientation; `expected_point` turns an OBSERVED anchor position and an ideal
vector into an `ExpectedPoint`, a different type from `Position`, so an expectation can never be passed on as an
observed position. The cohort's range and standard deviation are likewise the caller's own typed input.

**Translation** (`locate_in_image`). A point's slice in one image is the one whose plane lies physically nearest
(not a raw index; stacks may be unequal, reversed or oblique), its in-plane native (row, column) by that slice's
own frame (`PlaneFrame`), its signed off-plane distance, and whether it lies inside the stack and the image:
`outside_stack`, `outside_image` (with the clipped place), `tied_slices` (equidistant to floating precision:
none is picked) and `extent_unknown` are named, never silently clipped. It guides the search; it never decides.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from knee.collapse.physical import PlaneFrame

ORIENTATIONS = ("sagittal", "coronal", "axial")
PATIENT_FRAME = "LPS"
ANATOMICAL_AXES = ("medial", "posterior", "superior")

SELECTED = "selected"
REFUSED = "refused"
TIED = "tied"
ABSENT = "absent_in_view"
NOT_SUPPLIED = "not_supplied"
INVALID = "invalid:"
UNRESOLVED_OUTCOMES = (REFUSED, TIED, ABSENT, NOT_SUPPLIED)
REPEATED = "repeated_orientation"

COMPLETE = "complete"
PARTIAL = "partial"
SINGULAR = "singular_planes"
NONFINITE = "nonfinite_solution"
MIXED = "mixed_objects"

EPS = float(np.finfo(np.float64).eps)
NAN = float("nan")

Triple = tuple[float, float, float]


def _vec(values) -> np.ndarray | None:
    try:
        v = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError):
        return None
    return v if v.shape == (3,) else None


def _triple(v) -> Triple:
    return (float(v[0]), float(v[1]), float(v[2]))


@dataclass(frozen=True)
class KeyPlane:
    """One object's selected plane in one orientation, or the named outcome of a selection that gave none.

    `normal` is the unit normal and `offset_mm` the d of n·p = d (patient frame, LPS mm); both are None / NaN
    unless the outcome is `selected`. `precision_mm` is the plane's known place (half the slice step), NaN where
    unknown. `candidates` lists the (series, slice) addresses a `tied` selection could not choose between.
    """

    object: str
    orientation: str
    outcome: str
    series_uid: str = ""
    slice: int = -1
    normal: Triple | None = None
    offset_mm: float = NAN
    precision_mm: float = NAN
    reason: str = ""
    provenance: str = ""
    candidates: tuple[tuple[str, int], ...] = ()

    @property
    def usable(self) -> bool:
        return self.outcome == SELECTED

    def address(self) -> dict:
        return {
            "orientation": self.orientation,
            "outcome": self.outcome,
            "series_uid": self.series_uid,
            "slice": self.slice,
            "normal": list(self.normal) if self.normal is not None else None,
            "offset_mm": None if math.isnan(self.offset_mm) else self.offset_mm,
            "precision_mm": None
            if math.isnan(self.precision_mm)
            else self.precision_mm,
            "reason": self.reason,
            "provenance": self.provenance,
            "candidates": [list(c) for c in self.candidates],
        }


def key_plane(
    object: str,
    orientation: str,
    *,
    series_uid: str,
    slice: int,
    normal,
    origin_lps=None,
    offset_mm: float | None = None,
    precision_mm: float = NAN,
    reason: str = "",
    provenance: str = "",
) -> KeyPlane:
    """A selected plane from its physical normal and exactly one of a point on it (`origin_lps`) or its offset d
    (n·p = d for the normal as given). Geometry that cannot be a plane is kept as `invalid:<code>`; nothing is
    repaired."""
    base: dict[str, Any] = {
        "object": object,
        "orientation": orientation,
        "series_uid": series_uid,
        "slice": int(slice),
        "reason": reason,
        "provenance": provenance,
    }

    def bad(code: str) -> KeyPlane:
        return KeyPlane(outcome=INVALID + code, **base)

    if orientation not in ORIENTATIONS:
        return bad("unknown_orientation")
    n = _vec(normal)
    if n is None:
        return bad("normal_shape")
    if not np.all(np.isfinite(n)):
        return bad("normal_nonfinite")
    big = float(np.max(np.abs(n)))
    if big == 0.0:
        return bad("normal_zero")
    scaled = n / big
    scaled_length = float(np.linalg.norm(scaled))
    unit = scaled / scaled_length
    if (origin_lps is None) == (offset_mm is None):
        return bad(
            "origin_and_offset_both_given"
            if origin_lps is not None
            else "origin_or_offset_missing"
        )
    if origin_lps is not None:
        o = _vec(origin_lps)
        if o is None:
            return bad("origin_shape")
        if not np.all(np.isfinite(o)):
            return bad("origin_nonfinite")
        d = float(unit @ o)
    else:
        try:
            raw_offset = float(offset_mm if offset_mm is not None else math.nan)
            d = (raw_offset / big) / scaled_length
        except (OverflowError, TypeError, ValueError):
            return bad("offset_nonfinite")
    if not math.isfinite(d):
        return bad("offset_nonfinite")
    p = float(precision_mm)
    if p < 0 or math.isinf(p):
        return bad("precision_invalid")
    return KeyPlane(
        outcome=SELECTED, normal=_triple(unit), offset_mm=d, precision_mm=p, **base
    )


def unresolved_plane(
    object: str,
    orientation: str,
    outcome: str,
    *,
    reason: str = "",
    provenance: str = "",
    candidates: Iterable[tuple[str, int]] = (),
) -> KeyPlane:
    """A selection with no plane, by its own named outcome. A tie must name at least two candidates."""
    if outcome not in UNRESOLVED_OUTCOMES:
        raise ValueError(f"not an unresolved outcome: {outcome}")
    found = tuple((str(s), int(i)) for s, i in candidates)
    if outcome == TIED and len(set(found)) < 2:
        raise ValueError("a tie names at least two distinct candidates")
    return KeyPlane(
        object=object,
        orientation=orientation,
        outcome=outcome,
        reason=reason,
        provenance=provenance,
        candidates=found,
    )


def invalid_plane(
    object: str,
    orientation: str,
    code: str,
    *,
    series_uid: str = "",
    slice: int = -1,
    reason: str = "",
    provenance: str = "",
) -> KeyPlane:
    """A selection whose named source cannot give a plane (a series or slice that does not exist, a frame the
    header could not give): `invalid:<code>`, kept so the lack is named and never mistaken for an absence."""
    return KeyPlane(
        object=object,
        orientation=orientation,
        outcome=INVALID + code,
        series_uid=series_uid,
        slice=int(slice),
        reason=reason,
        provenance=provenance,
    )


def plane_of_frame(
    object: str,
    orientation: str,
    *,
    series_uid: str,
    slice: int,
    frame: PlaneFrame,
    precision_mm: float = NAN,
    reason: str = "",
    provenance: str = "",
) -> KeyPlane:
    """The key plane that is one slice of an acquisition, from that slice's own frame (its normal and origin)."""
    return key_plane(
        object,
        orientation,
        series_uid=series_uid,
        slice=slice,
        normal=frame.normal(),
        origin_lps=frame.origin_lps,
        precision_mm=precision_mm,
        reason=reason,
        provenance=provenance,
    )


@dataclass(frozen=True)
class Position:
    """One object's reference position from its key planes, or the partial constraints known.

    `point_lps` is None unless `status` is `complete`. `planes` holds the planes as supplied (orientation order);
    `used` those that constrain it. `problems` maps each orientation that gave no usable plane to its code.
    `rank` is the rank of the used normals; `geometry` says "ok", "not_enough_planes", "parallel_planes" or
    a failure code; `line_direction` is the unit direction of the line two independent planes leave.
    `precision_mm` is the per-axis bound from the planes' precisions (None where any is unknown).
    """

    object: str
    status: str
    point_lps: Triple | None
    precision_mm: Triple | None
    condition: float
    rank: int
    geometry: str
    planes: tuple[KeyPlane, ...]
    used: tuple[KeyPlane, ...]
    problems: Mapping[str, str]
    line_direction: Triple | None = None
    frame: str = PATIENT_FRAME

    @property
    def complete(self) -> bool:
        return self.status == COMPLETE

    def sources(self) -> dict:
        return {p.orientation: p.address() for p in self.planes}


def reference_position(object: str, planes: Iterable[KeyPlane]) -> Position:
    """Solve N p = d from the object's selected planes (at most one usable per orientation)."""
    given = tuple(planes)
    if any(p.object != object for p in given):
        return Position(
            object,
            MIXED,
            None,
            None,
            NAN,
            0,
            MIXED,
            given,
            (),
            dict.fromkeys(ORIENTATIONS, MIXED),
        )
    problems: dict[str, str] = {}
    chosen: list[KeyPlane] = []
    ordered: list[KeyPlane] = []
    for orientation in ORIENTATIONS:
        mine = [p for p in given if p.orientation == orientation]
        if not mine:
            problems[orientation] = NOT_SUPPLIED
        elif len(mine) > 1:
            problems[orientation] = REPEATED
        elif mine[0].usable:
            chosen.append(mine[0])
        else:
            problems[orientation] = mine[0].outcome
        ordered += mine
    for p in given:
        if p.orientation not in ORIENTATIONS:
            problems[p.orientation] = INVALID + "unknown_orientation"
            ordered.append(p)
    used = tuple(chosen)
    k = len(used)

    def fail(status: str, geometry: str, rank=0, condition=NAN, direction=None):
        return Position(
            object,
            status,
            None,
            None,
            condition,
            rank,
            geometry,
            tuple(ordered),
            used,
            problems,
            direction,
        )

    if k == 0:
        return fail(PARTIAL, "not_enough_planes")
    n = np.array([p.normal for p in used], dtype=np.float64)
    d = np.array([p.offset_mm for p in used], dtype=np.float64)
    s = np.linalg.svd(n, compute_uv=False)
    rank = int(np.sum(s > float(s[0]) * max(k, 3) * EPS))
    condition = float(s[0] / s[-1]) if s[-1] > 0 else math.inf
    if k < 3:
        if rank < k:
            return fail(PARTIAL, "parallel_planes", rank, condition)
        if k == 2:
            c = np.cross(n[0], n[1])
            return fail(
                PARTIAL,
                "not_enough_planes",
                rank,
                condition,
                _triple(c / np.linalg.norm(c)),
            )
        return fail(PARTIAL, "not_enough_planes", rank, condition)
    if rank < 3:
        return fail(SINGULAR, SINGULAR, rank, condition)
    with np.errstate(all="ignore"):
        point = np.linalg.solve(n, d)
        inverse = np.linalg.inv(n)
    if not np.all(np.isfinite(point)):
        return fail(NONFINITE, NONFINITE, rank, condition)
    precisions = np.array([p.precision_mm for p in used], dtype=np.float64)
    bound = (
        _triple(np.abs(inverse) @ precisions)
        if np.all(np.isfinite(precisions))
        else None
    )
    return Position(
        object,
        COMPLETE,
        _triple(point),
        bound,
        condition,
        rank,
        "ok",
        tuple(ordered),
        used,
        problems,
    )


# ---------------------------------------------------------------- scale, knee, vectors


@dataclass(frozen=True)
class KneeScale:
    """An explicit anatomical scale of one knee in millimetres, with its source; `mm` is None (and `code` says
    why) when none was given or what was given cannot be a scale."""

    mm: float | None
    source: str
    code: str


UNKNOWN_SCALE = KneeScale(None, "", "scale_unknown")


def knee_scale(mm, source: str) -> KneeScale:
    """A scale only if `mm` is a positive finite number; otherwise a named non-scale."""
    try:
        value = float(mm)
    except (TypeError, ValueError):
        return KneeScale(None, source, "scale_not_a_number")
    if not math.isfinite(value):
        return KneeScale(None, source, "scale_nonfinite")
    if value <= 0:
        return KneeScale(None, source, "scale_not_positive")
    return KneeScale(value, source, "given")


def knee_side(knee: str | None) -> str | None:
    """ "R" or "L" from the header's word; None when it names no knee."""
    word = str(knee or "").strip().upper()
    return word if word in ("R", "L") else None


def _medial_sign(side: str | None) -> float | None:
    # patient frame: +x toward the patient's left. A right knee's medial side faces the left leg.
    return {"R": 1.0, "L": -1.0}.get(side or "")


@dataclass(frozen=True)
class PairVector:
    """The 3D vector from `origin` to `target`: patient-frame displacement, magnitude, unit direction, the same
    against the knee scale, and in the anatomical orientation where the knee is named."""

    origin: str
    target: str
    displacement_lps: Triple
    magnitude_mm: float
    direction_lps: Triple | None
    direction_code: str
    precision_mm: Triple | None
    scale: KneeScale
    normalized_displacement: Triple | None
    normalized_distance: float | None
    knee: str | None
    anatomical_mm: Triple | None
    anatomical_direction: Triple | None
    orientation_code: str
    provenance: Mapping[str, Mapping[str, dict]] = field(default_factory=dict)


def _vector(origin, target, disp, precision, scale, knee, provenance) -> PairVector:
    disp = np.asarray(disp, dtype=np.float64)
    mag = float(np.linalg.norm(disp))
    unit = disp / mag if mag > 0 else None
    side = knee_side(knee)
    sign = _medial_sign(side)
    anatomical = None
    anatomical_direction = None
    if sign is not None:
        anatomical = (float(sign * disp[0]), float(disp[1]), float(disp[2]))
        if unit is not None:
            anatomical_direction = (
                float(sign * unit[0]),
                float(unit[1]),
                float(unit[2]),
            )
    return PairVector(
        origin,
        target,
        _triple(disp),
        mag,
        _triple(unit) if unit is not None else None,
        "ok" if unit is not None else "coincident_points",
        precision,
        scale,
        _triple(disp / scale.mm) if scale.mm else None,
        mag / scale.mm if scale.mm else None,
        side,
        anatomical,
        anatomical_direction,
        "ok" if anatomical is not None else "knee_unknown",
        provenance,
    )


def _sum_precision(a: Triple | None, b: Triple | None) -> Triple | None:
    if a is None or b is None:
        return None
    return _triple([x + y for x, y in zip(a, b, strict=True)])


def pair_vector(
    a: Position,
    b: Position,
    scale: KneeScale = UNKNOWN_SCALE,
    knee: str | None = None,
) -> PairVector:
    """The vector a -> b between two complete positions of one study."""
    if not (a.complete and b.complete) or a.point_lps is None or b.point_lps is None:
        raise ValueError("a vector needs two complete positions")
    if a.frame != b.frame:
        raise ValueError("positions are in different frames")
    disp = np.asarray(b.point_lps) - np.asarray(a.point_lps)
    return _vector(
        a.object,
        b.object,
        disp,
        _sum_precision(a.precision_mm, b.precision_mm),
        scale,
        knee,
        {a.object: a.sources(), b.object: b.sources()},
    )


def reversed_vector(v: PairVector) -> PairVector:
    """The vector target -> origin: exactly the negation."""
    return _vector(
        v.target,
        v.origin,
        -np.asarray(v.displacement_lps),
        v.precision_mm,
        v.scale,
        v.knee,
        v.provenance,
    )


def pair_vectors(
    positions: Mapping[str, Position],
    scale: KneeScale = UNKNOWN_SCALE,
    knee: str | None = None,
) -> tuple[dict[tuple[str, str], PairVector], dict[str, str]]:
    """Every ordered pair of the complete positions, and the objects left out with their status."""
    complete = sorted(n for n, p in positions.items() if p.complete)
    skipped = {n: p.status for n, p in positions.items() if not p.complete}
    out: dict[tuple[str, str], PairVector] = {}
    for i, a in enumerate(complete):
        for b in complete[i + 1 :]:
            v = pair_vector(positions[a], positions[b], scale, knee)
            out[(a, b)] = v
            out[(b, a)] = reversed_vector(v)
    return out, skipped


# ---------------------------------------------------------------- ideal, kept apart from the study


@dataclass(frozen=True)
class IdealVector:
    """Anatomy's displacement of `target` from `origin`, (medial, posterior, superior) in millimetres, with the
    anatomical source the caller grounded it in. Never derived from the studies."""

    origin: str
    target: str
    anatomical_mm: Triple
    source: str


@dataclass(frozen=True)
class ExpectedPoint:
    """Where the ideal says `object` should lie given an OBSERVED anchor: an expectation, never a Position."""

    object: str
    status: str
    point_lps: Triple | None
    anchor: str
    ideal_source: str
    kind: str = "expected_from_ideal"


def expected_point(
    anchor: Position, ideal: IdealVector, knee: str | None
) -> ExpectedPoint:
    """The ideal's target place from an observed, complete anchor position; needs the knee named (to turn
    medial into the patient's left or right)."""

    def none(status: str) -> ExpectedPoint:
        return ExpectedPoint(ideal.target, status, None, anchor.object, ideal.source)

    if anchor.object != ideal.origin:
        return none("anchor_is_not_the_ideal_origin")
    if not anchor.complete or anchor.point_lps is None:
        return none("anchor_incomplete")
    v = _vec(ideal.anatomical_mm)
    if v is None or not np.all(np.isfinite(v)):
        return none("ideal_invalid")
    sign = _medial_sign(knee_side(knee))
    if sign is None:
        return none("knee_unknown")
    p = np.asarray(anchor.point_lps) + np.array([sign * v[0], v[1], v[2]])
    return ExpectedPoint(
        ideal.target, "expected", _triple(p), anchor.object, ideal.source
    )


# ---------------------------------------------------------------- translation into an image


@dataclass(frozen=True)
class ImagePlacement:
    """A point in one image: its nearest slice by physical plane distance, the in-plane native (row, column)
    (`rc`, unclipped; `clipped_rc` inside the image) and the signed off-plane distance, with named extent flags."""

    status: str
    slice: int | None = None
    off_plane_mm: float | None = None
    half_step_mm: float | None = None
    rc: tuple[float, float] | None = None
    clipped_rc: tuple[float, float] | None = None
    in_stack: bool | None = None
    in_image: bool | None = None
    tied_slices: tuple[int, ...] = ()
    unusable_frames: int = 0


def locate_in_image(
    point_lps,
    frames: Sequence[PlaneFrame | None],
    shape_rc: tuple[int, int] | None = None,
) -> ImagePlacement:
    """Where `point_lps` lies in one image whose slices have the given frames (stack order, None = unusable).
    Pixel (r, c) spans [r - 0.5, r + 0.5]."""
    p = _vec(point_lps)
    if p is None or not np.all(np.isfinite(p)):
        return ImagePlacement("target_invalid")
    held = {i: f for i, f in enumerate(frames) if f is not None}
    usable = list(held)
    unusable = len(frames) - len(usable)
    if not usable:
        return ImagePlacement("no_usable_frames", unusable_frames=unusable)
    normals = {i: np.asarray(f.normal(), dtype=np.float64) for i, f in held.items()}
    origins = {i: np.asarray(f.origin_lps, dtype=np.float64) for i, f in held.items()}
    signed = {
        i: math.fsum(
            float(normals[i][axis]) * (float(p[axis]) - float(origins[i][axis]))
            for axis in range(3)
        )
        for i in usable
    }
    nearest = min(abs(v) for v in signed.values())
    # Compare distances at their local physical precision. Absolute LPS coordinates
    # include irrelevant in-plane translations and can otherwise turn distinct
    # slice distances into ties.
    nearest_indices = [i for i in usable if abs(signed[i]) == nearest]
    nearest_precision = max(1.0, *(abs(signed[i]) for i in nearest_indices))
    tied = tuple(
        i
        for i in usable
        if abs(signed[i])
        <= nearest + 8 * EPS * max(nearest_precision, 1.0, abs(signed[i]))
    )
    if len(tied) > 1:
        return ImagePlacement("tied_slices", tied_slices=tied, unusable_frames=unusable)
    i = tied[0]
    d = signed[i]
    # inside the stack: a neighbouring plane lies on the point's side, or at an end within half the step
    steps = [
        (
            j,
            math.fsum(
                float(normals[i][axis])
                * (float(origins[j][axis]) - float(origins[i][axis]))
                for axis in range(3)
            ),
        )
        for j in (i - 1, i + 1)
        if j in normals
    ]
    missing_neighbors = [
        j for j in (i - 1, i + 1) if 0 <= j < len(frames) and j not in held
    ]
    on_side = [step for _, step in steps if step != 0 and (step > 0) == (d > 0)]
    half: float | None
    if d == 0 or on_side:
        in_stack: bool | None = True
        half = abs(on_side[0]) / 2 if on_side else None
    elif missing_neighbors:
        # A missing adjacent frame is an unknown endpoint. When a usable neighbor
        # establishes the stack's local index direction, infer which physical side
        # the missing slot would occupy; never call that side outside the stack.
        missing_side_signs = set()
        for missing in missing_neighbors:
            for neighbor, step in steps:
                if step:
                    missing_side_signs.add(
                        1 if step * (missing - i) * (neighbor - i) > 0 else -1
                    )
        if (
            not missing_side_signs
            or (d > 0 and 1 in missing_side_signs)
            or (d < 0 and -1 in missing_side_signs)
        ):
            half, in_stack = None, None
        else:
            half = min((abs(s) for _, s in steps if s), default=0.0) / 2 or None
            in_stack = abs(d) <= half if half is not None else None
    elif steps:
        nonzero_steps = [abs(step) for _, step in steps if step != 0]
        half = min(nonzero_steps) / 2 if nonzero_steps else None
        in_stack = abs(d) <= half if half is not None else None
    else:
        half, in_stack = None, None
    rc = held[i].to_native(p[None, :])[0]
    rc_t = (float(rc[0]), float(rc[1]))
    in_image: bool | None = None
    clipped = None
    if shape_rc is not None:
        rows, cols = shape_rc
        clipped = (
            float(min(max(rc_t[0], -0.5), rows - 0.5)),
            float(min(max(rc_t[1], -0.5), cols - 0.5)),
        )
        in_image = clipped == rc_t
    if in_stack is False and in_image is False:
        status = "outside_stack_and_image"
    elif in_stack is False:
        status = "outside_stack"
    elif in_image is False:
        status = "outside_image"
    elif in_stack is None or in_image is None:
        status = "extent_unknown"
    else:
        status = "ok"
    return ImagePlacement(
        status, i, d, half, rc_t, clipped, in_stack, in_image, (), unusable
    )


def plane_trace_in_frame(plane: KeyPlane, frame: PlaneFrame) -> Triple | None:
    """Where a selected plane cuts one image: the line a*row + b*col = e in native coordinates; None where the
    plane is parallel to the image (to floating precision)."""
    if plane.normal is None:
        raise ValueError("an unresolved plane has no geometry")
    n = np.asarray(plane.normal)
    a, b = (float(v) for v in n @ np.asarray(frame.basis_lps))
    if math.hypot(a, b) <= 8 * EPS * max(frame.spacing_rc):
        return None
    return a, b, float(plane.offset_mm - n @ np.asarray(frame.origin_lps))
