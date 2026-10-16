"""The cheap continuation of a located tube along the leg: measurements only, no names
(`docs/DIMENSIONAL_COLLAPSE_PLAN.md` Steps 4-5, the posterior family and the vessels and bursa).

**Why it exists.** A tendon, a vessel or a bursa found as a cross-section on an axial slice is a
tube along the leg. Its longitudinal description lies on the sagittal and coronal slices. The
projected place of the cross-section is where to ask (a target, never a boundary); this asks
the one question the established definitions already use for a dark band, whether the tube
stands apart from what lies beside it, and follows the answer along the leg, step by step, in
both directions, on one native slice, with no lens and no fixed footprint extruded.

**The relation** (the iliotibial band's, `iliotibial_band_on_slice`): at each pixel step along the
leg, the object's ridge is the darkest (or, for fluid on a fluid-sensitive slice, the brightest)
place within the object's own measured cross width about the previous step's centre, and it
holds only where it is darker (brighter) than an equally wide strip on EACH side. A monotonic fall
from fat to muscle is not a ridge: it is darker than one side only. There is no signal cutoff,
smoothing or interpolation. The window moves with the ridge, so a tube that runs obliquely is
followed; it moves by at most its own half width per step.

**What it keeps distinct.** A step stops for a named reason: the scan ended
(`clipped_by_the_scan`), no seen pixel was there to read (`stopped_unseen`: an unseen place is
never read as dark), the ridge no longer stands apart from its flanks
(`stopped_not_set_apart_from_the_flanks`), or the extreme was shared by separated places
(`stopped_tied_separated_extremes`; a contiguous tie is kept whole, at its middle). A target
whose own place does not stand apart is a reading, never an absence of the object: the tube
may lie off this slice. The trace is the places where the relation held and the reason each end
stopped, not the object's boundary or full course.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

SUPERIOR = 2  # LPS: z toward the head

CLIPPED = "clipped_by_the_scan"
UNSEEN = "stopped_unseen"
FLANKS = "stopped_not_set_apart_from_the_flanks"
TIED = "stopped_tied_separated_extremes"
FOLLOWED = "followed"
STOPS = (CLIPPED, UNSEEN, FLANKS, TIED)
# the start's own refusals are the same four, named for the place the question was asked
START_REFUSALS = tuple(f"at_the_target_{stop}" for stop in STOPS)
# The names behind the small integers a record keeps (a trace's start, and where each end stopped):
# the number is the index; 0 is "followed" for a start and "no end" where the start was refused.
START_NAMES = (FOLLOWED, *START_REFUSALS)
STOP_NAMES = ("not_followed", *STOPS)


def leg_axis(basis_lps: np.ndarray) -> tuple[int, int] | None:
    """Which axis of a slice (0 rows, 1 columns) runs along the leg, and which way along it is
    toward the head (+1 where the index grows toward the head, -1 where it falls), from the
    slice's own basis (3, 2): the axis whose direction lies within 45 degrees of the patient's
    superior axis. None where neither does (an axial slice, which the leg does not run in) or
    the basis is not finite: an unknown, never a guess."""
    basis = np.asarray(basis_lps, dtype=np.float64)
    if basis.shape != (3, 2) or not np.all(np.isfinite(basis)):
        return None
    lengths = np.linalg.norm(basis, axis=0)
    if np.any(lengths <= 0):
        return None
    up = basis[SUPERIOR] / lengths
    axis = int(np.argmax(np.abs(up)))
    if abs(up[axis]) < np.sqrt(0.5):
        return None
    return axis, 1 if up[axis] > 0 else -1


def cross_extent_mm(
    points_lps: np.ndarray, basis_lps: np.ndarray, axis: int
) -> float | None:
    """The physical width of an object's places (scanner millimetres, (N, 3)) across the leg on a
    slice whose leg axis is `axis`: their range along the other in-plane direction. None where
    no place is finite."""
    points = np.asarray(points_lps, dtype=np.float64).reshape(-1, 3)
    points = points[np.isfinite(points).all(axis=1)]
    if not len(points):
        return None
    across = np.asarray(basis_lps, dtype=np.float64)[:, 1 - axis]
    unit = across / np.linalg.norm(across)
    along = points @ unit
    return float(np.max(along) - np.min(along))


@dataclass(frozen=True, slots=True)
class Trace:
    """What the relation held on, along one slice: `start` is `FOLLOWED` or why the place asked
    did not hold it (`START_REFUSALS`); `points_rc` the traced centres in native (row, column)
    pixels, ordered from the feet toward the head, with the `light` at each (the extreme in its
    window) and the `flank`: the nearer of the two side strips' medians (the tighter test);
    `toward_head` and `toward_feet` why each end stopped (None where the start was refused)."""

    start: str
    points_rc: np.ndarray
    light: np.ndarray
    flank: np.ndarray
    toward_head: str | None
    toward_feet: str | None


def window_step(
    line: np.ndarray, centre: int, half: int, dark: bool
) -> tuple[str, float, float, float]:
    """One pixel step along the leg: the ridge of the line of light `line` (the cross direction at
    one place along the leg) within `half` pixels of `centre`, and whether it stands apart from an
    equally wide strip on each side. Returns (`FOLLOWED` or a stop, the ridge's centre, its light,
    the nearer flank's median); the numbers are NaN with a stop."""
    nothing = float("nan")
    width = 2 * half + 1
    low, high = centre - half, centre + half
    if low - width < 0 or high + width >= len(line):
        return CLIPPED, nothing, nothing, nothing
    window = line[low : high + 1]
    seen = window[np.isfinite(window)]
    left, right = line[low - width : low], line[high + 1 : high + 1 + width]
    left, right = left[np.isfinite(left)], right[np.isfinite(right)]
    if not seen.size or not left.size or not right.size:
        return UNSEEN, nothing, nothing, nothing
    extreme = seen.min() if dark else seen.max()
    where = np.flatnonzero(window == extreme)
    if np.any(np.diff(where) != 1):
        return TIED, nothing, nothing, nothing
    sides = (float(np.median(left)), float(np.median(right)))
    nearer = min(sides) if dark else max(sides)
    apart = extreme < nearer if dark else extreme > nearer
    if not apart:
        return FLANKS, nothing, float(extreme), nearer
    return FOLLOWED, float(low + where.mean()), float(extreme), nearer


def trace_tube(
    plane: np.ndarray,
    axis: int,
    toward_head: int,
    start_rc: tuple[float, float],
    half_width_px: int,
    dark: bool = True,
) -> Trace:
    """Follow the ridge of a tube along the leg on one native slice, from the pixel the located
    cross-section projects to, toward the head and toward the feet. `plane` holds NaN for the
    places no value was seen; `axis` and `toward_head` are `leg_axis`'s; `half_width_px` (at
    least one) is the object's own half width across the leg. Every step is `window_step`."""
    light = np.asarray(plane, dtype=np.float64)
    if light.ndim != 2:
        raise ValueError("a_slice_is_two_dimensional")
    if half_width_px < 1:
        raise ValueError("a_ridge_is_at_least_one_pixel_across")
    # work with the leg along the rows, the places of one row being one line across the leg
    lines = light if axis == 0 else light.T
    along = round(start_rc[axis])
    across = round(start_rc[1 - axis])
    empty = np.empty((0, 2))
    if not 0 <= along < len(lines):
        return Trace(START_REFUSALS[0], empty, empty[:, 0], empty[:, 0], None, None)
    status, centre, value, flank = window_step(
        lines[along], across, half_width_px, dark
    )
    if status != FOLLOWED:
        refusal = START_REFUSALS[STOPS.index(status)]
        return Trace(refusal, empty, empty[:, 0], empty[:, 0], None, None)
    here = [(along, centre, value, flank)]
    stops: dict[int, str] = {}
    for step in (1, -1):
        at, near = along + step, centre
        while True:
            if not 0 <= at < len(lines):
                stops[step] = CLIPPED
                break
            status, now, value, flank = window_step(
                lines[at], round(near), half_width_px, dark
            )
            if status != FOLLOWED:
                stops[step] = status
                break
            here.append((at, now, value, flank))
            at, near = at + step, now
    here.sort(key=lambda item: item[0] * toward_head)
    rows = np.asarray([h[0] for h in here], dtype=np.float64)
    cols = np.asarray([h[1] for h in here], dtype=np.float64)
    points = np.column_stack((rows, cols) if axis == 0 else (cols, rows))
    return Trace(
        FOLLOWED,
        points,
        np.asarray([h[2] for h in here]),
        np.asarray([h[3] for h in here]),
        stops[toward_head],
        stops[-toward_head],
    )
