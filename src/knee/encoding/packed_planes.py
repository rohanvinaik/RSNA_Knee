"""Pure packed-plane row adapter (candidate).

Unpacks one stored row of a packed set of unequal 2D planes. It only reshapes
the selected flattened span. It does not fabricate slice/frame/window addresses
and does not declare the plane to be a mask or tissue. The requested row index
is retained in the result as lineage whenever it is a valid Python int.

Imports: numpy plus the standard library only.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "CODES",
    "OK",
    "PackedPlaneResult",
    "read_packed_plane",
]

OK = "ok"
VALUES_NOT_ARRAY = "values_not_array"
VALUES_NOT_1D = "values_not_1d"
VALUES_DTYPE_UNSUPPORTED = "values_dtype_unsupported"
OFFSETS_NOT_ARRAY = "offsets_not_array"
OFFSETS_NOT_INTEGER = "offsets_not_integer"
OFFSETS_NOT_1D = "offsets_not_1d"
OFFSETS_EMPTY = "offsets_empty"
SHAPES_NOT_ARRAY = "shapes_not_array"
SHAPES_NOT_INTEGER = "shapes_not_integer"
SHAPES_NOT_N_BY_2 = "shapes_not_n_by_2"
TABLE_LENGTH_MISMATCH = "table_length_mismatch"
OFFSETS_START_NONZERO = "offsets_start_nonzero"
OFFSETS_NONMONOTONIC = "offsets_nonmonotonic"
OFFSETS_END_MISMATCH = "offsets_end_mismatch"
SHAPE_NEGATIVE = "shape_negative"
SHAPE_SIZE_MISMATCH = "shape_size_mismatch"
SHAPE_NOT_REPRESENTABLE = "shape_not_representable"
ROW_NOT_INT = "row_not_int"
ROW_OUT_OF_RANGE = "row_out_of_range"

CODES = frozenset(
    {
        OK,
        VALUES_NOT_ARRAY,
        VALUES_NOT_1D,
        VALUES_DTYPE_UNSUPPORTED,
        OFFSETS_NOT_ARRAY,
        OFFSETS_NOT_INTEGER,
        OFFSETS_NOT_1D,
        OFFSETS_EMPTY,
        SHAPES_NOT_ARRAY,
        SHAPES_NOT_INTEGER,
        SHAPES_NOT_N_BY_2,
        TABLE_LENGTH_MISMATCH,
        OFFSETS_START_NONZERO,
        OFFSETS_NONMONOTONIC,
        OFFSETS_END_MISMATCH,
        SHAPE_NEGATIVE,
        SHAPE_SIZE_MISMATCH,
        SHAPE_NOT_REPRESENTABLE,
        ROW_NOT_INT,
        ROW_OUT_OF_RANGE,
    }
)


@dataclass(frozen=True, slots=True, eq=False)
class PackedPlaneResult:
    """Named outcome. `plane` is non-None only when `code == "ok"`.

    `row` is the requested row when it was a valid Python int (even if the
    table was malformed or the row out of range), else None.
    """

    code: str
    row: int | None
    plane: np.ndarray | None


def read_packed_plane(values, offsets, shapes, row) -> PackedPlaneResult:
    """Return the `row`-th stored plane as a reshaped view of `values`.

    values  : 1D ndarray (bool/int/uint/float/complex dtype; no object).
    offsets : 1D integer ndarray, length N+1, starting 0, monotone, ending len(values).
    shapes  : integer ndarray of shape (N, 2), nonnegative; prod(shape[i]) equals
              offsets[i+1] - offsets[i] for every row.
    row     : plain Python int (not bool, not numpy integer) with 0 <= row < N.

    Checks run in this order: values, offsets, shapes, table lengths, offsets
    contents, shapes contents (whole table), row type, row range. Inputs are
    never coerced.
    """
    kept_row = row if (type(row) is int) else None

    def fail(code: str) -> PackedPlaneResult:
        return PackedPlaneResult(code, kept_row, None)

    # values
    if not isinstance(values, np.ndarray):
        return fail(VALUES_NOT_ARRAY)
    if values.ndim != 1:
        return fail(VALUES_NOT_1D)
    if values.dtype.kind not in "biufc":
        return fail(VALUES_DTYPE_UNSUPPORTED)

    # offsets
    if not isinstance(offsets, np.ndarray):
        return fail(OFFSETS_NOT_ARRAY)
    if offsets.dtype.kind not in "iu":
        return fail(OFFSETS_NOT_INTEGER)
    if offsets.ndim != 1:
        return fail(OFFSETS_NOT_1D)
    if offsets.shape[0] == 0:
        return fail(OFFSETS_EMPTY)

    # shapes
    if not isinstance(shapes, np.ndarray):
        return fail(SHAPES_NOT_ARRAY)
    if shapes.dtype.kind not in "iu":
        return fail(SHAPES_NOT_INTEGER)
    if shapes.ndim != 2 or shapes.shape[1] != 2:
        return fail(SHAPES_NOT_N_BY_2)

    n_rows = shapes.shape[0]
    if offsets.shape[0] != n_rows + 1:
        return fail(TABLE_LENGTH_MISMATCH)

    # offsets contents (comparisons only, so no integer overflow in diff)
    if int(offsets[0]) != 0:
        return fail(OFFSETS_START_NONZERO)
    if offsets.shape[0] > 1 and bool(np.any(offsets[1:] < offsets[:-1])):
        return fail(OFFSETS_NONMONOTONIC)
    if int(offsets[-1]) != values.shape[0]:
        return fail(OFFSETS_END_MISMATCH)

    # shapes contents, whole table, exact Python-int products (no overflow)
    if shapes.dtype.kind == "i" and bool(np.any(shapes < 0)):
        return fail(SHAPE_NEGATIVE)
    offs = [int(x) for x in offsets]
    dims = [(int(a), int(b)) for a, b in shapes]
    for i, (a, b) in enumerate(dims):
        if a * b != offs[i + 1] - offs[i]:
            return fail(SHAPE_SIZE_MISMATCH)

    # row
    if type(row) is not int:
        return fail(ROW_NOT_INT)
    if row < 0 or row >= n_rows:
        return fail(ROW_OUT_OF_RANGE)

    try:
        plane = values[offs[row] : offs[row + 1]].reshape(dims[row])
    except (ValueError, OverflowError):
        # Even an empty plane may carry dimensions beyond NumPy's address space.
        return fail(SHAPE_NOT_REPRESENTABLE)
    return PackedPlaneResult(OK, row, plane)
