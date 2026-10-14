"""The dome, one measurement shared by the squint and the native scale: height, peaks, territories.

The thesis §6.2: "A center's dome is the territory of places it holds ... Nothing is cut on
strength, so a bright nucleus never silences a dim one." The native interiors
(`knee.objects.interiors.read_interiors`) already compute this over the pixels of the selected
plane: the Euclidean distance from the surrounding dark, the peaks by prominence
(`prominent_peaks`), and the watershed from those peaks. This module is that computation as one
function, so the funnel's tile dome (`knee.objects.tile_dome`) and the native interiors run one
rule at two scales (task 5.1: once the integrator makes `read_interiors` call it, its saved run
is byte-identical before and after). It measures; it decides nothing.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from skimage.segmentation import watershed

from knee.compute.contracts import ComputeContract, contracted, handed_on
from knee.objects.interiors import prominent_peaks

CONTRACT = ComputeContract(
    kind="measurement",
    language="SciPy's distance transform and scikit-image's watershed; no twin",
    reads="interior bool (H, W), spacing (row_mm, column_mm), prominence_mm",
    writes="height float64 (H, W) mm, peaks int64 (P, 2), labels int32 (H, W)",
    allocation="one float64 and one int32 array of the grid's shape, plus the peaks",
    work="one distance transform, one peak search and one watershed over H * W places",
    parallel_unit="slice",
    reference="dome",
    proof_gate="tests/knee/objects/test_dome.py: two interiors parted by an obstacle give two "
    "peaks and two territories that never cross the obstacle; one round interior gives one peak "
    "at its centre with height equal to its radius in millimetres; an empty interior gives no "
    "peak and all-zero labels; the height is zero on every obstacle; no input is written",
)


def _number_or_nan(value: object) -> float:
    """The value as a float when it is a number and not a bool, else NaN: no number at all."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        return float("nan")
    try:
        return float(value)
    except OverflowError:
        return float("nan")


def _positive_number(value: object, refusal: str) -> float:
    """A finite positive number as a float, or the named refusal (a bool is not a number)."""
    number = _number_or_nan(value)
    if not np.isfinite(number) or number <= 0.0:
        raise ValueError(refusal)
    return number


def _spacing_pair(spacing: object) -> tuple[float, float]:
    """Two finite positive numbers, (row_mm, column_mm), or the named refusal."""
    if isinstance(spacing, np.ndarray) and spacing.ndim != 1:
        raise ValueError("invalid_spacing")
    if not isinstance(spacing, (tuple, list, np.ndarray)) or len(spacing) != 2:
        raise ValueError("invalid_spacing")
    return (
        _positive_number(spacing[0], "invalid_spacing"),
        _positive_number(spacing[1], "invalid_spacing"),
    )


def _interior_grid(interior: object) -> np.ndarray:
    """The interior as a two-dimensional bool grid (not written, not copied when it already is one).

    A grid of integers is read as non-zero meaning interior; anything that is not a
    two-dimensional array of booleans or integers is the named refusal, because a coerced float
    would turn a missing reading into a place.
    """
    try:
        grid = np.asarray(interior)
    except (TypeError, ValueError):
        raise ValueError("invalid_interior") from None
    if grid.ndim != 2 or grid.dtype.kind not in "biu":
        raise ValueError("invalid_interior")
    return grid.astype(bool, copy=False)


@contracted
def dome(
    interior: np.ndarray, spacing: tuple[float, float], prominence_mm: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Height, peaks and territories of an interior (measurement).

    `interior` bool (H, W): the places an object can hold. `spacing` (row_mm, column_mm): the
    size of one place in millimetres along each axis. `height` is the Euclidean distance in
    millimetres from each interior place to the nearest place that is not interior, or to the
    frame (the picture's edge counts as an obstacle: `distance_transform_edt` over `interior`
    padded by one false place on every side, then unpadded), 0 outside the interior. `peaks`
    int64 (P, 2) are the interior's local maxima of height that stand at least `prominence_mm`
    above their surroundings, by `knee.objects.interiors.prominent_peaks`' own rule, ordered by
    descending height, ties by scan order. `labels` int32 (H, W) is
    `skimage.segmentation.watershed(-height, markers, mask=interior)` with marker k + 1 at peak
    k, so territory k + 1 is peak k's; 0 where unseeded or not interior. A `prominence_mm` that
    is not a finite positive number, a spacing that is not two finite positive numbers, or an
    `interior` that is not two-dimensional is refused by name (`invalid_prominence_mm`,
    `invalid_spacing`, `invalid_interior`). Nothing is cut on strength. Outputs frozen.

    pre: interior.ndim == 2
    post: __return__[0].shape == interior.shape
    post: __return__[2].shape == interior.shape
    post: __return__[1].ndim == 2 and __return__[1].shape[1] == 2
    """
    # The refusals, in the order the docstring names them, before anything is measured.
    bar = _positive_number(prominence_mm, "invalid_prominence_mm")
    pitch = _spacing_pair(spacing)
    grid = _interior_grid(interior)

    # The picture's edge is an obstacle: one false place all round, taken off again after.
    distances = ndi.distance_transform_edt(np.pad(grid, 1), sampling=pitch)
    height = distances[1:-1, 1:-1].copy()

    seeded = grid.any() and height.max() >= bar
    plateaus, count = ndi.label(
        prominent_peaks(height, bar).astype(bool) & grid
        if seeded
        else np.zeros(grid.shape, dtype=bool)
    )
    if not count:
        return (
            handed_on(height),
            handed_on(np.empty((0, 2), dtype=np.int64)),
            handed_on(np.zeros(grid.shape, dtype=np.int32)),
        )

    # A peak is a plateau of equal height (a flat top is one peak, not as many as it has places),
    # so it is seeded whole: a marker on a single place of it hands the places beside the plateau
    # to whichever neighbour floods first, and the territories would no longer be the ones
    # `read_interiors` draws (measured on the saved run: two of five series differ).
    # It is named by its first place in scan order, and ranked tallest first, ties in scan order.
    flat = plateaus.ravel()
    held = np.flatnonzero(flat)
    _, first_held = np.unique(flat[held], return_index=True)
    first = held[first_held]
    rows, cols = np.divmod(first, grid.shape[1])
    order = np.lexsort((first, -height[rows, cols]))
    rank = np.zeros(count + 1, dtype=np.int32)
    rank[order + 1] = np.arange(1, count + 1, dtype=np.int32)

    labels = watershed(-height, rank[plateaus], mask=grid, connectivity=1)
    return (
        handed_on(height),
        handed_on(np.column_stack((rows[order], cols[order])).astype(np.int64)),
        handed_on(labels.astype(np.int32)),
    )


__all__ = ["CONTRACT", "dome"]
