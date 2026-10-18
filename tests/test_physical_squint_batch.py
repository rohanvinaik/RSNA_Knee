from math import ceil

import numpy as np
import pytest

from knee.collapse.physical import physical_squint


def literal_reference(plane, spacing, tile_mm, finite=None):
    if finite is None:
        finite = np.isfinite(plane)
    tile = tuple(max(1, ceil(tile_mm / step)) for step in spacing)
    out_shape = tuple(
        ceil(size / step) for size, step in zip(plane.shape, tile, strict=True)
    )
    median, minimum, maximum = (np.full(out_shape, np.nan) for _ in range(3))
    coverage = np.zeros(out_shape, dtype=np.float64)
    bounds = np.empty((*out_shape, 4), dtype=np.int64)
    for r in range(out_shape[0]):
        for c in range(out_shape[1]):
            r0, c0 = r * tile[0], c * tile[1]
            r1 = min(r0 + tile[0], plane.shape[0])
            c1 = min(c0 + tile[1], plane.shape[1])
            block = plane[r0:r1, c0:c1]
            values = block[finite[r0:r1, c0:c1]]
            bounds[r, c] = r0, r1, c0, c1
            coverage[r, c] = values.size / block.size
            if values.size:
                median[r, c] = np.median(values)
                minimum[r, c] = np.min(values)
                maximum[r, c] = np.max(values)
    return median, minimum, maximum, coverage, bounds


def assert_matches_reference(plane, spacing, tile_mm, finite=None):
    got = physical_squint(plane, spacing, tile_mm, finite)
    expected = literal_reference(plane, spacing, tile_mm, finite)
    for field, values in zip(
        ("median", "minimum", "maximum", "coverage", "bounds_rc"),
        expected,
        strict=True,
    ):
        actual = getattr(got, field)
        np.testing.assert_array_equal(actual, values)
        assert not actual.flags.writeable
    return got


def test_anisotropic_ragged_windows_match_literal_and_keep_native_bounds():
    plane = np.arange(7 * 11, dtype=np.uint16).reshape(7, 11)
    finite = np.ones(plane.shape, dtype=bool)
    finite[1, 2] = False
    finite[6, 10] = False
    got = assert_matches_reference(plane, (1.3, 0.7), 2.4, finite)
    assert got.tile_shape_rc == (2, 4)
    assert got.bounds_rc[-1, -1].tolist() == [6, 7, 8, 11]
    assert got.coverage[-1, -1] == pytest.approx(2 / 3)


def test_transpose_noncontiguous_and_readonly_arrays_match_reference():
    base = np.arange(15 * 19, dtype=np.int32).reshape(15, 19)
    mask = np.ones(base.shape, dtype=bool)
    mask[::4, ::3] = False
    plane = base[::-2, 1::2].T
    finite = mask[::-2, 1::2].T
    plane.setflags(write=False)
    finite.setflags(write=False)
    assert_matches_reference(plane, (0.6, 1.4), 2.1, finite)


def test_positive_affine_preserves_bounds_coverage_and_transforms_extrema():
    plane = np.arange(63, dtype=np.int16).reshape(7, 9)
    base = physical_squint(plane, (1.0, 1.5), 2.5)
    moved = physical_squint(plane * 3 + 7, (1.0, 1.5), 2.5)
    np.testing.assert_array_equal(base.bounds_rc, moved.bounds_rc)
    np.testing.assert_array_equal(base.coverage, moved.coverage)
    for name in ("median", "minimum", "maximum"):
        np.testing.assert_array_equal(getattr(moved, name), getattr(base, name) * 3 + 7)


def test_empty_huge_tile_and_nonfinite_default_mask():
    empty = np.empty((0, 5), dtype=np.float32)
    assert_matches_reference(empty, (0.7, 2.0), 1000.0)
    plane = np.array([[1.0, np.nan, 3.0], [np.inf, -np.inf, 6.0]])
    got = assert_matches_reference(plane, (1.0, 1.0), 1000.0)
    assert got.coverage.tolist() == [[3 / 6]]
    assert got.minimum[0, 0] == 1.0 and got.maximum[0, 0] == 6.0


@pytest.mark.parametrize(
    "plane,spacing,tile,message",
    [
        (np.zeros((2, 2), dtype=bool), (1.0, 1.0), 1.0, "invalid_plane"),
        (np.zeros((2, 2)), (0.0, 1.0), 1.0, "invalid_spacing"),
        (np.zeros((2, 2)), (1.0, 1.0), 0.0, "invalid_tile_mm"),
    ],
)
def test_named_input_errors(plane, spacing, tile, message):
    with pytest.raises(ValueError, match=message):
        physical_squint(plane, spacing, tile)
