"""Intent tests for inclusive pixel-cell supercover of transported bands."""

import numpy as np
import pytest

from knee.collapse.band_raster import raster_bands


def _quad(corners: list[tuple[float, float]]) -> np.ndarray:
    return np.asarray(corners, dtype=np.float64).reshape(1, 4, 2)


def test_axis_aligned_band_marks_every_intersected_pixel_cell() -> None:
    quad = _quad([(1, 1), (1, 4), (3, 4), (3, 1)])
    mask, visited = raster_bands(quad, np.array([True]), (6, 7))

    expected = np.zeros((6, 7), dtype=bool)
    expected[1:4, 1:5] = True
    np.testing.assert_array_equal(mask, expected)
    assert visited == int(expected.sum())


def test_oblique_thin_band_supercovers_diagonal_corner_crossings() -> None:
    # A narrow parallelogram follows the diagonal through the pixel-cell corners.
    quad = _quad([(-0.07, 0.07), (0.07, -0.07), (4.57, 4.43), (4.43, 4.57)])
    mask, _ = raster_bands(quad, np.array([True]), (5, 5))

    # Inclusive ties retain cells on both sides of every corner crossing.
    assert np.all(np.diag(mask))
    for index in range(4):
        assert mask[index, index + 1]
        assert mask[index + 1, index]


def test_pixel_cell_boundary_ties_are_inclusive() -> None:
    quad = _quad([(0.5, 0.5), (0.5, 1.5), (1.5, 1.5), (1.5, 0.5)])
    mask, visited = raster_bands(quad, np.array([True]), (3, 3))

    expected = np.zeros((3, 3), dtype=bool)
    expected[:3, :3] = True
    np.testing.assert_array_equal(mask, expected)
    assert visited == 9


def test_band_is_clipped_to_frame_without_changing_its_source_geometry() -> None:
    quad = _quad([(-2, 1), (-2, 3), (2, 3), (2, 1)])
    before = quad.copy()
    mask, visited = raster_bands(quad, np.array([True]), (4, 5))

    expected = np.zeros((4, 5), dtype=bool)
    expected[:3, 1:4] = True
    np.testing.assert_array_equal(mask, expected)
    assert visited == int(expected.sum())
    np.testing.assert_array_equal(quad, before)


def test_unselected_valid_band_is_inert_and_empty_input_is_well_defined() -> None:
    quad = _quad([(1, 1), (1, 3), (3, 3), (3, 1)])
    mask, visited = raster_bands(quad, np.array([False]), (5, 5))
    assert not np.any(mask)
    assert visited == 0

    empty, empty_visited = raster_bands(
        np.empty((0, 4, 2), dtype=np.float64), np.empty((0,), dtype=bool), (3, 4)
    )
    assert empty.shape == (3, 4)
    assert empty.dtype == np.bool_
    assert not np.any(empty)
    assert empty_visited == 0

    zero_height, zero_height_visited = raster_bands(
        _quad([(0, 0), (0, 1), (1, 1), (1, 0)]),
        np.array([True]),
        (0, 3),
    )
    assert zero_height.shape == (0, 3)
    assert zero_height.dtype == np.bool_
    assert not zero_height.flags.writeable
    assert zero_height_visited == 0


def test_outputs_are_read_only() -> None:
    mask, _ = raster_bands(
        _quad([(1, 1), (1, 3), (3, 3), (3, 1)]), np.array([True]), (5, 5)
    )
    assert not mask.flags.writeable


@pytest.mark.parametrize(
    ("quads", "selected", "shape"),
    [
        (np.zeros((1, 4, 2), dtype=np.float32), np.array([True]), (3, 3)),
        (np.zeros((1, 4, 3), dtype=np.float64), np.array([True]), (3, 3)),
        (np.zeros((1, 4, 2), dtype=np.float64), np.array([], dtype=bool), (3, 3)),
        (np.zeros((1, 4, 2), dtype=np.float64), np.array([True]), (3, -1)),
        (
            np.array([[[0, 0], [0, 2], [2, 0], [2, 2]]], dtype=np.float64),
            np.array([True]),
            (3, 3),
        ),
        (
            np.array([[[0, 0], [0, 2], [np.nan, 2], [2, 0]]], dtype=np.float64),
            np.array([True]),
            (3, 3),
        ),
    ],
)
def test_malformed_raster_inputs_are_refused(quads, selected, shape) -> None:
    with pytest.raises(ValueError):
        raster_bands(quads, selected, shape)


def test_reference_and_jit_return_exact_same_mask_and_visit_count() -> None:
    quads = np.asarray(
        [
            [(0.2, 0.1), (0.1, 1.8), (3.2, 2.1), (3.1, 0.2)],
            [(1.0, 2.0), (2.0, 4.0), (4.0, 3.0), (3.0, 1.0)],
        ],
        dtype=np.float64,
    )
    selected = np.array([True, False])
    reference = raster_bands(quads, selected, (5, 6), backend="reference")
    jit = raster_bands(quads, selected, (5, 6), backend="jit")

    assert reference[0].dtype == jit[0].dtype == np.bool_
    np.testing.assert_array_equal(reference[0], jit[0])
    assert reference[1] == jit[1]


def test_unavailable_or_unknown_backend_is_not_silently_accepted() -> None:
    quad = _quad([(1, 1), (1, 3), (3, 3), (3, 1)])
    with pytest.raises(ValueError, match="invalid_backend"):
        raster_bands(quad, np.array([True]), (5, 5), backend="automatic")
