"""SUPERSEDED FRAMING (2026-10-17): the cohort windows below (`PATELLA_FROM_REFERENCE_MM`, the
empty `JOINT_FROM_REFERENCE_MM`, "what the cohort says") are statistics of one link, which Rohan
rejected: «I told you to base this on knee anatomy, NOT on statistics». The mechanism is the relative
position map, `docs/RELATIVE_POSITION_MAP.md` §0: one 3D map of the whole knee, every object against
every other object, the ideal from anatomy and physiology, the studies giving only each pair's range
and standard deviation. The key plane read here (the bone's strongest supported marrow body, named by
the lens) is an instance of the bones' key slice, the map's zero.

The study's anatomical reference: the plane that shows a big bone clearly, and where the other
parts lie relative to it (measurements and geometry only, no names;
`docs/ANCHOR_RELATIVE_SEARCH.md`, `docs/DIMENSIONAL_COLLAPSE_PLAN.md`).

**Why it exists.** Rohan, 2026-10-16: «Knee anatomy is physically linked. Get the one that is
cheapest to resolve with the squint system (I imagine the tibia/femur?), Get its "key slice", use
that as a normalizer, get the statistical slice range and position estimation *relative* to the
obvious elements, to make the hard compute, the expensive process, sanely targeted where they
likely are." The femur and the tibia are named on every study's middle slices (the bootstrap), so
which bone it is is known; what is not known is WHERE ALONG THE STACK IT SHOWS CLEARLY. The cheap
bone profile (`bone_profile`: the marrow body's supported area on every slice, from the squint's
tiles and a finer block reading only where the tiles cannot say) already measures that on every
slice without the lens.

**The key plane**, in plain words: the slice on which the bone's marrow body, inside the
anatomical corridor of the bone already known, is the largest supported body the whole depth
holds, and which the lens's territories then confirm as that bone (`name_territory`, the
established carried-bone rule). One existing measurement, no weighted score. Equal areas are a
tie and every tied slice is kept; a slice not read, or not readable, is not a candidate (unknown,
never empty); a strongest slice the lens does not name the bone on is not the reference, and the
next strongest is asked (`strongest_first`), so only the planes the cheap reading points to are
ever read in detail.

**The coordinate.** A key plane supplies its DEPTH, the place along its own normal where it lies;
the resolved bone's places on it supply the IN-PLANE positions. Neither stands in for the other. The
reference's place along any other series' normal is the mean of its support's places along it
(`reference_position`): for a plane parallel to that series the support lies in the plane, so this
is its depth, and the support spans no depth (`kind` "depth"); for a plane across it the support
spreads along it and the number is the bone's own in-plane landmark (`kind` "in_plane"). Offsets are
signed by physical direction (`offset_sign`: toward the patient's left, or medially where the
sagittal series' header names the knee), so a reversed stack or the other knee gives the same
offset; there is no subtraction of slice indices anywhere.

**What the cohort says** (`PATELLA_FROM_REFERENCE_MM`, from `scripts/reference_offsets.py` over
the 58 labelled studies): where the patella's native-resolved sections lie relative to the
reference, a range. It points where the patella's cheap profile and lens are read first
(`expected_slices`); it never names anything and never changes a definition. Where the reference,
the knee, the view or the geometry is unknown, no window is given and the whole depth is read.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from knee.collapse.profile import positive_runs, run_maxima

# The bones that can be the reference, and the views a reference is looked for in, in order: the
# sagittal first, since its depth axis is the one the patella's own search runs along.
REFERENCE_BONES = ("femur", "tibia")
REFERENCE_VIEWS = ("Sagittal", "Coronal")

# Where the patella's native-resolved sections lie against the reference: the quartiles (the central
# half) of the offsets of each fat-suppressed sagittal series' largest native-resolved patella
# section over the labelled cohort, in millimetres along the target series' normal, positive toward
# the patient's left: 39 series of 35 studies, whose reference is a plane across the stack's axis
# (kind "depth"; `scripts/reference_offsets.py`, `docs/ANCHOR_RELATIVE_SEARCH.md`). Keyed by the
# kind of reference (`reference_position`) and the sign convention (`offset_sign`). The medial
# convention (17 series where the header names the knee) was measured too and is no narrower
# (-16.5 to 11.2 mm), so it is not wired; a reference that is a landmark within the plane (kind
# "in_plane", 5 series) has too few sections to say, so it points nowhere. Measured, not chosen: a
# pointer for where to read first, never a definition. A section outside it is found by the
# broader read that follows (out of sample the central half held the representative in 19 of 39
# series and 19% of the slices lay in it).
PATELLA_FROM_REFERENCE_MM: dict[tuple[str, str], tuple[float, float]] = {
    ("depth", "left"): (-13.1, 5.3),
}


# Where the joint family's cheap quantities point against the reference, keyed (quantity, plane,
# fat suppression "0"/"1", kind of reference, convention): the central half of each series'
# strongest non-middle pointed plane over the labelled cohort, in millimetres along the target
# series' normal in the direction `offset_direction` names. An entry is wired ONLY where its
# leave-one-study-out check holds the pointed plane in the central half clearly more often than the
# share of the slices it covers (a window no better than its own coverage points nowhere), and has at
# least 10 series. Measured over the 58 studies (`scripts/joint_reference_offsets.py`,
# `data/readings/collapse-20261016/search-priors/reference-joint-first/joint-pointer-stats.json`):
# the coronal populations (the only ones of useful size: 11 to 23 series) hold the pointed plane in
# the central half 36 to 44% of the time over a window covering 33 to 57% of the slices read, no
# lift; the sagittal populations hold 3 to 4 series. So nothing is wired and every joint search
# reads the whole established depth, as before, with its reason recorded. An entry added here is a
# measured range of a candidate pointer, never a definition and never a native-resolved position.
JOINT_FROM_REFERENCE_MM: dict[tuple[str, str, str, str, str], tuple[float, float]] = {}


@dataclass(frozen=True)
class Reference:
    """One study's reference: the series and key slice(s) it was read on (`slices`: every slice at
    the strongest supported area that the lens confirmed, ties kept), the bone and its supported
    marrow-body area there, the resolved bone's places in the scanner's millimetres (`support_lps`),
    the plane's own origin, unit normal and thickness (the depth it supplies), the header's word
    for the knee, why it was chosen (`reason`) and every candidate asked on the way, with how each
    came out (`candidates`; the planes the cheap profile did not point to were never read, and say
    so by being absent)."""

    series_uid: str
    view: tuple[str, str, str]
    bone: str
    slices: tuple[int, ...]
    area_mm2: float
    support_lps: np.ndarray
    origin_lps: np.ndarray
    normal: np.ndarray
    thickness_mm: float
    knee: str
    reason: str
    candidates: tuple[dict, ...]


def patient_axis(normal: Sequence[float] | np.ndarray) -> tuple[int, float] | None:
    """The patient axis (0 toward the left, 1 toward the back, 2 toward the head) a normal mainly
    runs along, and the sign (+1 or -1) of its component there; None for a normal that is not a
    finite, nonzero 3-vector."""
    v = np.asarray(normal, dtype=np.float64)
    if v.shape != (3,) or not np.all(np.isfinite(v)) or not np.any(v):
        return None
    axis = int(np.argmax(np.abs(v)))
    return axis, 1.0 if v[axis] > 0 else -1.0


def offset_sign(
    normal: Sequence[float] | np.ndarray, plane: str, knee: str
) -> tuple[float, str] | None:
    """The sign that makes an offset along `normal` positive in a physical direction, and which:
    ("medial", sign) on a sagittal series whose header names the knee (a right knee's medial side
    lies toward the patient's left, a left knee's toward the right), else ("left", sign) for a
    series that runs along the patient's left-right axis; None for any other axis or an unusable
    normal (the offsets of other axes were not measured)."""
    found = patient_axis(normal)
    if found is None or found[0] != 0:
        return None
    side = (
        {"R": 1.0, "L": -1.0}.get(knee.strip().upper()) if plane == "Sagittal" else None
    )
    if side is None:
        return found[1], "left"
    return found[1] * side, "medial"


def offset_direction(
    normal: Sequence[float] | np.ndarray, plane: str, knee: str
) -> tuple[float, str] | None:
    """`offset_sign` plus the front-to-back axis: the sign that makes an offset along `normal`
    positive in a physical direction, and which. Along the patient's left-right axis exactly
    `offset_sign` ("medial" or "left"); along the front-to-back axis ("posterior", sign), positive
    toward the back (the scanner's +y: a coronal series' own depth, the reference's AP landmark);
    None for the head-to-foot axis (no offsets were measured on it) and for an unusable normal. Other
    axes are never guessed and `offset_sign` itself is unchanged."""
    found = offset_sign(normal, plane, knee)
    if found is not None:
        return found
    axis = patient_axis(normal)
    if axis is None or axis[0] != 1:
        return None
    return axis[1], "posterior"


def strongest_first(area_mm2: np.ndarray) -> list[tuple[int, tuple[int, ...]]]:
    """The candidates for a key plane in the order a bone asks them, each as (tier, slices): tier 0
    the planes the cheap profile points to, the maximum of each run of supported marrow body
    (`run_maxima`: a plateau keeps all its slices), strongest first; tier 1, to be asked only where
    no tier-0 plane is named as the bone, every other slice that holds a supported body, strongest
    first, since the lens's territories can refuse a plane its neighbour is named on. Slices of equal
    area are one group and a tie is never broken. A slice whose area is not finite (not read,
    unreadable, cut) or not positive (measured empty) is no candidate: unknown or empty, never
    supported. Tier 0 is what the bones' own reading reads anyway, so asking it first costs nothing
    more; two bones are merged by (tier, area) by the caller."""
    values = np.asarray(area_mm2, dtype=np.float64)
    held = np.flatnonzero(np.isfinite(values) & (values > 0))
    peaks = {int(z) for run in run_maxima(values, positive_runs(values)) for z in run}

    def by_area(slices: list[int], tier: int) -> list[tuple[int, tuple[int, ...]]]:
        return [
            (tier, tuple(z for z in slices if values[z] == level))
            for level in sorted({float(values[z]) for z in slices}, reverse=True)
        ]

    return by_area(sorted(peaks), 0) + by_area(
        [int(z) for z in held if int(z) not in peaks], 1
    )


def reference_position(
    support_lps: np.ndarray, unit: np.ndarray, thickness_mm: float
) -> tuple[float, float, float, str] | None:
    """The reference's place along `unit` (a series' normal, millimetres in the scanner's frame):
    (mean, lowest, highest, kind) over the resolved bone's places. `kind` is "depth" where the
    support spans no more than the key plane's own thickness along `unit` (it lies in a plane across
    that axis: the plane's depth is the coordinate), "in_plane" where it spreads along it (the
    bone's own landmark). None where there is no finite place or the axis is not usable."""
    points = np.asarray(support_lps, dtype=np.float64).reshape(-1, 3)
    points = points[np.isfinite(points).all(axis=1)]
    axis = np.asarray(unit, dtype=np.float64)
    if not len(points) or axis.shape != (3,) or not np.any(axis):
        return None
    axis = axis / np.linalg.norm(axis)
    along = points @ axis
    low, high = float(np.min(along)), float(np.max(along))
    flat = math.isfinite(thickness_mm) and high - low <= thickness_mm
    return float(along.mean()), low, high, "depth" if flat else "in_plane"


def expected_slices(
    positions: np.ndarray,
    reference: float,
    sign: float,
    lo_hi: tuple[float, float],
    always: int,
) -> np.ndarray | None:
    """Which slices lie in the expected neighbourhood: those whose place along the series' normal
    (`positions`, millimetres, any order or spacing) is within `lo_hi` of the `reference`'s, the
    offset taken in the direction `sign` makes positive; slice `always` (the bootstrap's own) is
    always in. None where a place is unknown, so that no window is trusted and the whole depth is
    read."""
    places = np.asarray(positions, dtype=np.float64)
    if (
        not len(places)
        or not np.all(np.isfinite(places))
        or not math.isfinite(reference)
    ):
        return None
    offset = sign * (places - reference)
    inside = (offset >= lo_hi[0]) & (offset <= lo_hi[1])
    inside[always] = True
    return inside
