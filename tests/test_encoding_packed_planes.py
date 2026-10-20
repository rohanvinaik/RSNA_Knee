"""Focused tests for knee.encoding.packed_planes (NumPy + pytest only)."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from knee.encoding import packed_planes as pp
from knee.encoding.packed_planes import PackedPlaneResult, read_packed_plane


def pack(planes, dtype):
    flat = [np.asarray(p, dtype=dtype).ravel() for p in planes]
    values = np.concatenate(flat) if flat else np.zeros(0, dtype=dtype)
    offsets = np.zeros(len(planes) + 1, dtype=np.int64)
    offsets[1:] = np.cumsum([f.size for f in flat])
    shapes = np.array([np.asarray(p).shape for p in planes], dtype=np.int64).reshape(
        -1, 2
    )
    return values, offsets, shapes


def make_planes(dtype):
    return [
        np.arange(6).reshape(2, 3),
        np.arange(100, 104).reshape(4, 1),
        np.arange(200, 215).reshape(3, 5),
    ]


DTYPES = [
    np.bool_,
    np.int8,
    np.uint8,
    np.int16,
    np.int32,
    np.int64,
    np.float32,
    np.float64,
    np.complex64,
]


@pytest.mark.parametrize("dtype", DTYPES)
def test_exact_shape_value_dtype_bytes_every_row(dtype):
    planes = [np.asarray(p, dtype=dtype) for p in make_planes(dtype)]
    values, offsets, shapes = pack(planes, dtype)
    for i, expected in enumerate(planes):
        res = read_packed_plane(values, offsets, shapes, i)
        assert res.code == "ok"
        assert res.row == i
        assert res.plane.shape == expected.shape
        assert res.plane.dtype == expected.dtype
        assert np.array_equal(res.plane, expected)
        assert res.plane.tobytes() == expected.tobytes()


def test_result_is_frozen_named():
    values, offsets, shapes = pack(make_planes(np.int16), np.int16)
    res = read_packed_plane(values, offsets, shapes, 0)
    assert isinstance(res, PackedPlaneResult)
    assert [f.name for f in dataclasses.fields(res)] == ["code", "row", "plane"]
    with pytest.raises(dataclasses.FrozenInstanceError):
        res.code = "x"
    assert isinstance(res.code, str) and res.code in pp.CODES


def test_no_copy_shared_memory_and_write_through():
    values, offsets, shapes = pack(make_planes(np.int32), np.int32)
    res = read_packed_plane(values, offsets, shapes, 2)
    assert np.shares_memory(res.plane, values)
    assert res.plane.base is not None
    res.plane[0, 0] = -7
    assert values[offsets[2]] == -7


def test_read_only_source_preserved():
    values, offsets, shapes = pack(make_planes(np.float32), np.float32)
    values.flags.writeable = False
    res = read_packed_plane(values, offsets, shapes, 1)
    assert res.code == "ok"
    assert not res.plane.flags.writeable
    assert np.shares_memory(res.plane, values)


def test_adjacent_row_separation():
    values, offsets, shapes = pack(make_planes(np.int64), np.int64)
    a = read_packed_plane(values, offsets, shapes, 0).plane
    b = read_packed_plane(values, offsets, shapes, 1).plane
    assert a.size == 6 and b.size == 4
    assert not np.any(np.isin(a, b))
    assert a.max() < b.min()
    # row 0 view ends exactly where row 1 begins
    assert a.ravel()[-1] == values[offsets[1] - 1]
    assert b.ravel()[0] == values[offsets[1]]


@pytest.mark.parametrize("dtype", [np.uint8, np.float64, np.bool_])
def test_empty_planes_valid_preserve_dtype_and_readonly(dtype):
    planes = [
        np.zeros((0, 3), dtype=dtype),
        np.ones((2, 2), dtype=dtype),
        np.zeros((4, 0), dtype=dtype),
    ]
    values, offsets, shapes = pack(planes, dtype)
    values.flags.writeable = False
    for i in (0, 2):
        res = read_packed_plane(values, offsets, shapes, i)
        assert res.code == "ok"
        assert res.plane.shape == planes[i].shape
        assert res.plane.dtype == np.dtype(dtype)
        assert not res.plane.flags.writeable
    mid = read_packed_plane(values, offsets, shapes, 1)
    assert mid.plane.shape == (2, 2)


def test_all_empty_values():
    values = np.zeros(0, dtype=np.int16)
    offsets = np.array([0, 0], dtype=np.int64)
    shapes = np.array([[0, 5]], dtype=np.int64)
    res = read_packed_plane(values, offsets, shapes, 0)
    assert (
        res.code == "ok" and res.plane.shape == (0, 5) and res.plane.dtype == np.int16
    )


def good():
    return pack(make_planes(np.int16), np.int16)


def expect(res, code, row):
    assert res.code == code
    assert res.row == row
    assert res.plane is None


def test_values_failures():
    _, o, s = good()
    expect(read_packed_plane([1, 2], o, s, 0), "values_not_array", 0)
    expect(read_packed_plane(np.zeros((2, 2)), o, s, 0), "values_not_1d", 0)
    expect(
        read_packed_plane(np.array([1, 2], dtype=object), o, s, 0),
        "values_dtype_unsupported",
        0,
    )
    expect(read_packed_plane(np.array(["a"]), o, s, 0), "values_dtype_unsupported", 0)


def test_offsets_failures():
    v, o, s = good()
    expect(read_packed_plane(v, o.tolist(), s, 1), "offsets_not_array", 1)
    expect(read_packed_plane(v, o.astype(bool), s, 1), "offsets_not_integer", 1)
    expect(read_packed_plane(v, o.astype(np.float64), s, 1), "offsets_not_integer", 1)
    expect(
        read_packed_plane(v, np.array([0.5, 1.5, 3.0, 4.0]), s, 1),
        "offsets_not_integer",
        1,
    )
    expect(read_packed_plane(v, o.reshape(2, 2), s, 1), "offsets_not_1d", 1)
    expect(read_packed_plane(v, np.zeros(0, dtype=np.int64), s, 1), "offsets_empty", 1)


def test_shapes_failures():
    v, o, s = good()
    expect(read_packed_plane(v, o, s.tolist(), 0), "shapes_not_array", 0)
    expect(read_packed_plane(v, o, s.astype(bool), 0), "shapes_not_integer", 0)
    expect(read_packed_plane(v, o, s.astype(np.float64), 0), "shapes_not_integer", 0)
    expect(read_packed_plane(v, o, s.ravel(), 0), "shapes_not_n_by_2", 0)
    expect(
        read_packed_plane(v, o, np.zeros((3, 3), dtype=np.int64), 0),
        "shapes_not_n_by_2",
        0,
    )
    expect(read_packed_plane(v, o, s[:, :1], 0), "shapes_not_n_by_2", 0)
    expect(read_packed_plane(v, o, s.reshape(3, 2, 1), 0), "shapes_not_n_by_2", 0)


def test_table_length_mismatch():
    v, o, s = good()
    expect(read_packed_plane(v, o[:-1], s, 0), "table_length_mismatch", 0)
    expect(read_packed_plane(v, o, s[:-1], 0), "table_length_mismatch", 0)


def test_offset_content_failures():
    v, o, s = good()
    bad = o.copy()
    bad[0] = 1
    expect(read_packed_plane(v, bad, s, 0), "offsets_start_nonzero", 0)
    # gap / short coverage: end does not reach len(values)
    bad = o.copy()
    bad[-1] -= 1
    expect(read_packed_plane(v, bad, s, 0), "offsets_end_mismatch", 0)
    # out of bounds beyond len(values)
    bad = o.copy()
    bad[-1] += 3
    expect(read_packed_plane(v, bad, s, 0), "offsets_end_mismatch", 0)
    # nonmonotonic with end still correct
    bad = o.copy()
    bad[1], bad[2] = bad[2], bad[1]
    expect(read_packed_plane(v, bad, s, 0), "offsets_nonmonotonic", 0)
    # intermediate offset past end then back
    bad = o.copy()
    bad[1] = len(v) + 5
    expect(read_packed_plane(v, bad, s, 0), "offsets_nonmonotonic", 0)


def test_values_longer_than_offsets_end_is_gap():
    v, o, s = good()
    longer = np.concatenate([v, np.zeros(2, dtype=v.dtype)])
    expect(read_packed_plane(longer, o, s, 0), "offsets_end_mismatch", 0)


def test_negative_shape():
    v, o, s = good()
    bad = s.copy()
    bad[0] = (-2, -3)  # product matches span 6 but negative dims are illegal
    expect(read_packed_plane(v, o, bad, 2), "shape_negative", 2)
    bad = s.copy()
    bad[1, 0] = -1
    expect(read_packed_plane(v, o, bad, 0), "shape_negative", 0)


def test_shape_size_mismatch_including_unselected_row():
    v, o, s = good()
    bad = s.copy()
    bad[1] = (2, 3)
    expect(read_packed_plane(v, o, bad, 1), "shape_size_mismatch", 1)
    expect(read_packed_plane(v, o, bad, 0), "shape_size_mismatch", 0)


def test_overflow_like_products():
    values = np.zeros(0, dtype=np.int8)
    offsets = np.array([0, 0], dtype=np.int64)
    # 2**40 * 2**40 would wrap in int64 arithmetic; must not alias to 0
    shapes = np.array([[2**40, 2**40]], dtype=np.int64)
    expect(read_packed_plane(values, offsets, shapes, 0), "shape_size_mismatch", 0)
    # 2**32 * 2**32 == 2**64 wraps to 0 in uint64
    shapes = np.array([[2**32, 2**32]], dtype=np.uint64)
    expect(read_packed_plane(values, offsets, shapes, 0), "shape_size_mismatch", 0)
    shapes = np.array([[2**63 - 1, 2**63 - 1]], dtype=np.int64)
    expect(read_packed_plane(values, offsets, shapes, 0), "shape_size_mismatch", 0)
    # a zero dimension with a huge other one is a valid empty plane
    shapes = np.array([[0, 2**62]], dtype=np.int64)
    res = read_packed_plane(values, offsets, shapes, 0)
    assert res.code == "ok" and res.plane.shape == (0, 2**62)


@pytest.mark.parametrize(
    "bad_row", [True, False, 1.0, 1.5, np.int64(1), np.int8(0), "1", None, [1], (1,)]
)
def test_row_not_int(bad_row):
    v, o, s = good()
    expect(read_packed_plane(v, o, s, bad_row), "row_not_int", None)


@pytest.mark.parametrize("bad_row", [-1, 3, 10**30])
def test_row_out_of_range_retains_row(bad_row):
    v, o, s = good()
    expect(read_packed_plane(v, o, s, bad_row), "row_out_of_range", bad_row)


def test_zero_rows_any_row_out_of_range():
    v = np.zeros(0, dtype=np.int8)
    o = np.array([0], dtype=np.int64)
    s = np.zeros((0, 2), dtype=np.int64)
    expect(read_packed_plane(v, o, s, 0), "row_out_of_range", 0)


def test_unsigned_offsets_and_shapes_accepted():
    v, o, s = good()
    res = read_packed_plane(v, o.astype(np.uint32), s.astype(np.uint16), 2)
    assert res.code == "ok" and res.plane.shape == (3, 5)
    assert np.array_equal(res.plane, np.arange(200, 215).reshape(3, 5))


def test_no_input_mutation():
    v, o, s = good()
    before = (v.copy(), o.copy(), s.copy())
    read_packed_plane(v, o, s, 1)
    assert (
        np.array_equal(v, before[0])
        and np.array_equal(o, before[1])
        and np.array_equal(s, before[2])
    )


@pytest.mark.parametrize("shape", [(0, 2**63), (2**63, 0), (0, 2**64 - 1)])
def test_unrepresentable_empty_shape_returns_named_outcome(shape):
    result = read_packed_plane(
        np.zeros(0, dtype=np.uint8),
        np.array([0, 0], dtype=np.uint64),
        np.array([shape], dtype=np.uint64),
        0,
    )
    assert result.code == "shape_not_representable"
    assert result.row == 0 and result.plane is None
