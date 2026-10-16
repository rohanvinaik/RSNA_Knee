"""Where the synovial recesses and their walls can lie, as relations between parts already located:
measurements only, no names (`docs/DIMENSIONAL_COLLAPSE_PLAN.md` Step 5, the recesses, fluid, synovial
lining, capsule and patellar retinacula).

**Why it exists.** Fluid is the white at least `FLUID_BRIGHTER` times the bones' marrow. A squint
tile's MAXIMUM at that level only says a bright pixel may be in the tile: it points, it never names a
pocket, and on a fat-suppressed fluid-sensitive series it is positive on nearly every slice (vessels,
skin, noise). So the pointer is read only inside the compartment the earlier families located, by the
same relations the existing definitions state (`anterior_synovial_recess`, `capsule_at_side_recesses`,
`retinacular_walls`), in the scanner's millimetres (LPS: x toward the patient's left, y toward the
back, z toward the head), so they hold on any series whatever its plane, order or spacing:

- the anterior recess lies behind the patella's middle, in front of the femur's middle and no lower than
  the patella's lowest place (`anterior_pocket`);
- a side recess lies outboard of its meniscus, at or above the menisci's lower end, beside the femur
  (`gutter_landmarks`, `side_gutters`);
- the retinacula's recesses lie in the interval from the patella's posterior position to the femur's
  middle, in front of the femoral condyles (`patellofemoral_interval`).

Each is an UPPER BOUND read on the carried places (a union over the planes the parts were named on),
never a section; the existing definition decides, on the pointed planes only. A neighbour's band bounds
a search for a thin wall; it does not establish the wall throughout the band. Nothing nonfinite is a
place.
"""

from __future__ import annotations

import numpy as np


def _places(points_lps: np.ndarray) -> np.ndarray:
    points = np.asarray(points_lps, dtype=np.float64)
    if points.shape[-1] != 3:
        raise ValueError("places_are_three_dimensional")
    return points


def anterior_pocket(
    points_lps: np.ndarray,
    patella_back_mm: float,
    femur_back_mm: float,
    patella_lowest_mm: float,
) -> np.ndarray:
    """The places behind the patella (y beyond `patella_back_mm`), in front of the femur (y short of
    `femur_back_mm`) and no lower than the patella's lowest place: the relation
    `anterior_synovial_recess` states, in the scanner's millimetres. A nonfinite place, or a nonfinite
    landmark, is not in it."""
    points = _places(points_lps)
    none = np.zeros(points.shape[:-1], dtype=bool)
    if not np.all(np.isfinite([patella_back_mm, femur_back_mm, patella_lowest_mm])):
        return none
    y, z = points[..., 1], points[..., 2]
    with np.errstate(invalid="ignore"):
        return (
            np.isfinite(points).all(axis=-1)
            & (y > patella_back_mm)
            & (y < femur_back_mm)
            & (z >= patella_lowest_mm)
        )


def gutter_landmarks(
    first_left_mm: np.ndarray,
    second_left_mm: np.ndarray,
    first_up_mm: np.ndarray,
    second_up_mm: np.ndarray,
) -> tuple[tuple[float, float], float] | None:
    """The side recesses' landmarks from the two menisci's places: the medians of their positions
    toward the left, in order (`capsule_at_side_recesses` sorts them), and the menisci's lower end
    (the lowest height of either). None where either meniscus has no finite place."""
    lefts = [np.asarray(v, dtype=np.float64) for v in (first_left_mm, second_left_mm)]
    ups = [np.asarray(v, dtype=np.float64) for v in (first_up_mm, second_up_mm)]
    lefts = [v[np.isfinite(v)] for v in lefts]
    ups = [v[np.isfinite(v)] for v in ups]
    if not all(v.size for v in (*lefts, *ups)):
        return None
    ends = sorted(float(np.median(v)) for v in lefts)
    return (ends[0], ends[1]), float(min(v.min() for v in ups))


def side_gutters(
    points_lps: np.ndarray,
    ends_mm: tuple[float, float],
    bottom_mm: float,
    femur_left_range_mm: tuple[float, float],
) -> np.ndarray:
    """The places outboard of the two menisci (toward the left of the leftmost end or toward the
    right of the other), at or above their lower end, within the femur's own side-to-side extent:
    where a side recess beside the femur can lie, the relation `capsule_at_side_recesses` states. A
    recess that reaches the femur has a place in the femur's extent, so none is cut off; the part of
    it beyond is not asked here. Nonfinite places and landmarks are not in it."""
    points = _places(points_lps)
    low, high = femur_left_range_mm
    if not np.all(np.isfinite([*ends_mm, bottom_mm, low, high])):
        return np.zeros(points.shape[:-1], dtype=bool)
    x, z = points[..., 0], points[..., 2]
    with np.errstate(invalid="ignore"):
        outboard = (x < ends_mm[0]) | (x > ends_mm[1])
        return (
            np.isfinite(points).all(axis=-1)
            & outboard
            & (z >= bottom_mm)
            & (x >= low)
            & (x <= high)
        )


def patellofemoral_interval(
    points_lps: np.ndarray,
    patella_back_mm: float,
    femur_back_mm: float,
    femur_left_range_mm: tuple[float, float],
) -> np.ndarray:
    """The places from the patella's posterior position to the femur's middle, within the femur's
    side-to-side extent: where the retinacula's bright recesses beside the patella can lie, the
    interval `retinacular_walls` states (it runs to the femur's strongest peak, read here as an
    upper bound by the femur's middle). Empty when the interval is empty or a landmark is
    nonfinite."""
    points = _places(points_lps)
    none = np.zeros(points.shape[:-1], dtype=bool)
    low, high = femur_left_range_mm
    if not np.all(np.isfinite([patella_back_mm, femur_back_mm, low, high])):
        return none
    if femur_back_mm <= patella_back_mm:
        return none
    x, y = points[..., 0], points[..., 1]
    with np.errstate(invalid="ignore"):
        return (
            np.isfinite(points).all(axis=-1)
            & (y >= patella_back_mm)
            & (y <= femur_back_mm)
            & (x >= low)
            & (x <= high)
        )
