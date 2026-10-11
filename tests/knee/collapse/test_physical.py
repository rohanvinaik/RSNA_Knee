"""Intent tests for physical measurements in knee.collapse.physical.

The frame is the DICOM patient frame with native row/column spacing, while a squint
retains finite coverage and remainder tiles without altering its source plane.
"""

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from knee.collapse.physical import PlaneFrame, physical_squint


def test_dicom_frame_maps_row_and_column_steps_using_their_own_spacing() -> None:
    frame = PlaneFrame.from_dicom(
        position=(10.0, 20.0, 30.0),
        orientation=(0.0, 1.0, 0.0, 1.0, 0.0, 0.0),
        spacing_rc=(2.5, 0.75),
    )
    points = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [2.0, 3.0]])
    expected = np.array(
        [
            [10.0, 20.0, 30.0],
            [12.5, 20.0, 30.0],
            [10.0, 20.75, 30.0],
            [15.0, 22.25, 30.0],
        ]
    )
    np.testing.assert_allclose(frame.to_patient(points), expected, rtol=0.0, atol=1e-12)
    np.testing.assert_allclose(frame.to_native(expected), points, rtol=0.0, atol=1e-12)


@given(
    row=st.floats(min_value=-20, max_value=20, allow_nan=False, allow_infinity=False),
    column=st.floats(
        min_value=-20, max_value=20, allow_nan=False, allow_infinity=False
    ),
)
def test_orthonormal_patient_plane_round_trips_native_coordinates(
    row: float, column: float
) -> None:
    frame = PlaneFrame.from_dicom(
        position=(13.0, -8.0, 4.0),
        orientation=(0.0, 1.0, 0.0, 0.0, 0.0, 1.0),
        spacing_rc=(1.7, 0.6),
    )
    point = np.array([[row, column]])
    np.testing.assert_allclose(
        frame.to_native(frame.to_patient(point)), point, atol=1e-10
    )


@pytest.mark.parametrize(
    ("position", "orientation", "spacing"),
    [
        (None, (1, 0, 0, 0, 1, 0), (1, 1)),
        ((0, 0), (1, 0, 0, 0, 1, 0), (1, 1)),
        ((0, 0, 0), (1, 0, 0, 1, 0, 0), (1, 1)),  # parallel direction cosines
        ((0, 0, 0), (1, 0, 0, 0, 1), (1, 1)),
        ((0, 0, 0), (1, 0, 0, 0, 1, 0), (0, 1)),
        ((0, 0, 0), (1, 0, 0, 0, 1, 0), (1, float("inf"))),
        ((0, 0, float("nan")), (1, 0, 0, 0, 1, 0), (1, 1)),
    ],
)
def test_unreadable_dicom_geometry_is_rejected(position, orientation, spacing) -> None:
    with pytest.raises(ValueError):
        PlaneFrame.from_dicom(position, orientation, spacing)


def test_patient_inverse_projects_off_plane_points_onto_the_declared_plane() -> None:
    frame = PlaneFrame.from_dicom(
        position=(0.0, 0.0, 0.0),
        orientation=(1.0, 0.0, 0.0, 0.0, 1.0, 0.0),
        spacing_rc=(2.0, 3.0),
    )
    np.testing.assert_allclose(
        frame.to_native(np.array([[3.0, 2.0, 9.0]])), [[1.0, 1.0]]
    )


def test_squint_keeps_remainder_tiles_and_reports_finite_coverage() -> None:
    plane = np.arange(15, dtype=np.float64).reshape(3, 5)
    plane[0, 1] = np.nan
    original = plane.copy()
    result = physical_squint(plane, spacing_rc=(1.0, 1.0), tile_mm=2.0)

    assert result.bounds_rc.shape == (2, 3, 4)
    assert result.tile_shape_rc == (2, 2)
    assert result.coverage.shape == (2, 3)
    assert result.coverage[0, 0] == pytest.approx(0.75)
    assert result.coverage[-1, -1] == pytest.approx(1.0)
    assert result.minimum[-1, -1] == 14.0
    assert result.maximum[-1, -1] == 14.0
    np.testing.assert_array_equal(plane, original)


@pytest.mark.parametrize(
    "bad", [np.array([]), np.array([1.0, 2.0]), np.ones((2, 2, 2))]
)
def test_squint_requires_a_rectangular_two_dimensional_plane(bad: np.ndarray) -> None:
    with pytest.raises(ValueError):
        physical_squint(bad, spacing_rc=(1.0, 1.0), tile_mm=1.0)


def test_squint_accepts_an_empty_two_dimensional_plane() -> None:
    result = physical_squint(np.empty((0, 3)), spacing_rc=(1.0, 1.0), tile_mm=2.0)
    assert result.median.size == 0
    assert result.bounds_rc.shape == (0, 2, 4)


@pytest.mark.parametrize(
    ("spacing", "tile"),
    [((0.0, 1.0), 1.0), ((1.0, float("nan")), 1.0), ((1.0, 1.0), 0.0)],
)
def test_squint_rejects_nonphysical_spacing_or_tile_size(spacing, tile) -> None:
    with pytest.raises(ValueError):
        physical_squint(np.ones((2, 2)), spacing_rc=spacing, tile_mm=tile)


def test_squint_records_are_read_only() -> None:
    result = physical_squint(np.arange(4.0).reshape(2, 2), (1.0, 1.0), 1.0)
    for value in (
        result.median,
        result.minimum,
        result.maximum,
        result.coverage,
        result.bounds_rc,
    ):
        assert not value.flags.writeable
