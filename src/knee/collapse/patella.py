"""Where the patella can lie, as a relation to the femur: measurements only, no names
(`docs/DIMENSIONAL_COLLAPSE_PLAN.md` Step 5, the patella and the extensor mechanism).

**Why it exists.** The patella is one bone that rides in front of the femur's lower end. Its
existing definition (`knee.objects.assignments.patella_peak`) says where, in the slice's own
axes: in front of the femur, no higher than `PATELLA_ABOVE_MM` above the femur's lowest place.
The collapse asks the same relation of the whole stack cheaply, before any lens is read: which
native pixels of each slice lie in front of every place the femur was carried to, and no higher
than that above its lowest. That is the corridor the cheap marrow-body profile is read in; the
established rule then runs only on the planes the profile points to.

The relation is read in the scanner's millimetres (LPS: y toward the back, z toward the head),
so it holds on any series, whatever its plane, its order or its spacing. It is an UPPER BOUND on
where the patella can lie, never its section: the femur's carried places are the union over the
planes they were named on, so a lateral slice's own femur may stand further back than they do.
Nothing here decides identity; a nonfinite place is not a place.
"""

from __future__ import annotations

import numpy as np

from knee.objects.assignments import PATELLA_ABOVE_MM


def femur_landmarks(femur_lps: np.ndarray) -> tuple[float, float] | None:
    """The femur's front (its least y, the most anterior place) and its lowest place (its least z)
    over the carried `femur_lps` (N, 3), in millimetres; None when no place is finite. The two
    numbers `patella_peak` reads from the femur on a slice, read from every carried place."""
    points = np.asarray(femur_lps, dtype=np.float64).reshape(-1, 3)
    points = points[np.isfinite(points).all(axis=1)]
    if not len(points):
        return None
    return float(np.min(points[:, 1])), float(np.min(points[:, 2]))


def in_front_of_the_femur(
    points_lps: np.ndarray,
    front: float,
    lowest: float,
    margin_mm: float = 0.0,
    above_mm: float = PATELLA_ABOVE_MM,
) -> np.ndarray:
    """Which places (`points_lps`, (..., 3)) lie in front of the femur (y < `front`) and between
    its lowest place and `above_mm` above it, as `patella_peak` asks. `margin_mm` widens each
    bound, for a place that stands for a patch that big (a squint tile's centre, half a tile).
    A nonfinite place is not in front of anything."""
    points = np.asarray(points_lps, dtype=np.float64)
    if points.shape[-1] != 3:
        raise ValueError("places_are_three_dimensional")
    y, z = points[..., 1], points[..., 2]
    with np.errstate(invalid="ignore"):
        return (
            np.isfinite(points).all(axis=-1)
            & (y < front + margin_mm)
            & (z >= lowest - margin_mm)
            & (z <= lowest + above_mm + margin_mm)
        )
