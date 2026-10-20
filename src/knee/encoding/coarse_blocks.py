"""Pure coarse block-grid row addressing.

The measured grid is preserved as-is: no expansion into native pixels, no
resampling, no synthetic masks/frames and no cortex identity.  Bounds are
reported for addressed blocks only.  Grid indices are ``coarse_grid_rc``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

OK = "ok"
SLICES_INVALID = "slices_invalid"
SHAPES_INVALID = "shapes_invalid"
WINDOW_INVALID = "window_invalid"
BLOCK_PX_INVALID = "block_px_invalid"
BLOCK_MM_INVALID = "block_mm_invalid"
ROW_NOT_INT = "row_not_int"
ROW_OUT_OF_RANGE = "row_out_of_range"
GRID_WINDOW_MISMATCH = "grid_window_mismatch"
COORDINATES_INVALID = "coordinates_invalid"
COORDINATE_OUTSIDE_GRID = "coordinate_outside_grid"
MASK_INVALID = "mask_invalid"

# Keeps every sum below fit in int64.
_LIMIT = 2**61


@dataclass(frozen=True, slots=True)
class CoarseRowGeometry:
    code: str
    row: int | None
    slice_index: int | None = None
    grid_shape: tuple[int, int] | None = None
    window_rc: tuple[int, int, int, int] | None = None
    block_px: tuple[int, int] | None = None
    block_mm: tuple[float, float] | None = None


def _int_array(value: object, ndim: int, tail: tuple[int, ...]) -> bool:
    return (
        isinstance(value, np.ndarray)
        and value.dtype.kind in "iu"  # bool ('b') is rejected here
        and value.ndim == ndim
        and value.shape[1:] == tail
    )


def coarse_row_geometry(
    shapes, slices, windows_rc, block_px, block_mm, row
) -> CoarseRowGeometry:
    """Validate the whole per-row tables, then describe row ``row``."""
    kept = row if type(row) is int else None

    def fail(code: str) -> CoarseRowGeometry:
        return CoarseRowGeometry(code, kept)

    if not _int_array(slices, 1, ()):
        return fail(SLICES_INVALID)
    n = slices.shape[0]
    if slices.dtype.kind == "i" and bool(np.any(slices < 0)):
        return fail(SLICES_INVALID)
    if not _int_array(shapes, 2, (2,)) or shapes.shape[0] != n:
        return fail(SHAPES_INVALID)
    if shapes.dtype.kind == "i" and bool(np.any(shapes < 0)):
        return fail(SHAPES_INVALID)
    if not _int_array(windows_rc, 2, (4,)) or windows_rc.shape[0] != n:
        return fail(WINDOW_INVALID)
    if windows_rc.dtype.kind == "i" and bool(np.any(windows_rc < 0)):
        return fail(WINDOW_INVALID)
    if n and bool(np.any(windows_rc > _LIMIT)):
        return fail(WINDOW_INVALID)
    if bool(np.any(windows_rc[:, 0] > windows_rc[:, 1])) or bool(
        np.any(windows_rc[:, 2] > windows_rc[:, 3])
    ):
        return fail(WINDOW_INVALID)
    if not _int_array(block_px, 2, (2,)) or block_px.shape[0] != n:
        return fail(BLOCK_PX_INVALID)
    if bool(np.any(block_px == 0)) or (
        block_px.dtype.kind == "i" and bool(np.any(block_px < 0))
    ):
        return fail(BLOCK_PX_INVALID)
    if n and bool(np.any(block_px > _LIMIT)):
        return fail(BLOCK_PX_INVALID)
    if (
        not isinstance(block_mm, np.ndarray)
        or block_mm.dtype.kind != "f"
        or block_mm.shape != (n, 2)
        or not bool(np.all(np.isfinite(block_mm)))
        or bool(np.any(block_mm <= 0))
    ):
        return fail(BLOCK_MM_INVALID)
    if type(row) is not int:
        return fail(ROW_NOT_INT)
    if row < 0 or row >= n:
        return fail(ROW_OUT_OF_RANGE)

    r0, r1, c0, c1 = (int(v) for v in windows_rc[row])
    bh, bw = (int(v) for v in block_px[row])
    expected = (-(-(r1 - r0) // bh), -(-(c1 - c0) // bw))
    grid = (int(shapes[row][0]), int(shapes[row][1]))
    if grid != expected:
        return fail(GRID_WINDOW_MISMATCH)
    return CoarseRowGeometry(
        OK,
        row,
        int(slices[row]),
        grid,
        (r0, r1, c0, c1),
        (bh, bw),
        (float(block_mm[row][0]), float(block_mm[row][1])),
    )


def support_block_coordinates(mask) -> tuple[str, np.ndarray | None]:
    """Row-major (row, col) grid indices of true blocks of a 2-D bool grid."""
    if not isinstance(mask, np.ndarray) or mask.dtype.kind != "b" or mask.ndim != 2:
        return MASK_INVALID, None
    coords = np.argwhere(mask).astype(np.int64, copy=False)
    coords.flags.writeable = False
    return OK, coords


def block_native_bounds(
    geometry: CoarseRowGeometry, coordinates
) -> tuple[str, np.ndarray | None]:
    """Clipped native half-open bounds ``[r0, r1, c0, c1]`` of addressed blocks.

    Bounds only: blocks are never expanded to pixels and the far-edge blocks
    are clipped to the row window.
    """
    if geometry.code != OK:
        return geometry.code, None
    if (
        geometry.grid_shape is None
        or geometry.window_rc is None
        or geometry.block_px is None
    ):
        return GRID_WINDOW_MISMATCH, None
    if (
        not isinstance(coordinates, np.ndarray)
        or coordinates.dtype.kind not in "iu"
        or coordinates.ndim != 2
        or coordinates.shape[1] != 2
    ):
        return COORDINATES_INVALID, None
    if (
        coordinates.dtype.kind == "u"
        and coordinates.size
        and int(coordinates.max()) > np.iinfo(np.int64).max
    ):
        return COORDINATES_INVALID, None
    gr, gc = geometry.grid_shape
    if coordinates.shape[0]:
        if coordinates.dtype.kind == "i" and int(coordinates.min()) < 0:
            return COORDINATE_OUTSIDE_GRID, None
        if int(coordinates[:, 0].max()) >= gr or int(coordinates[:, 1].max()) >= gc:
            return COORDINATE_OUTSIDE_GRID, None
    c = coordinates.astype(np.int64)
    r0, r1, c0, c1 = geometry.window_rc
    bh, bw = geometry.block_px
    out = np.empty((c.shape[0], 4), dtype=np.int64)
    lo_r = r0 + c[:, 0] * np.int64(bh)
    lo_c = c0 + c[:, 1] * np.int64(bw)
    out[:, 0] = lo_r
    out[:, 1] = np.minimum(lo_r + bh, r1)
    out[:, 2] = lo_c
    out[:, 3] = np.minimum(lo_c + bw, c1)
    out.flags.writeable = False
    return OK, out
