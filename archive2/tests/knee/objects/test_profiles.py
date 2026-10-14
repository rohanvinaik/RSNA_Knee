"""Intent tests for native bilinear profiles, support and their reference/JIT twin."""

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from knee.objects.profiles import profile_support_code, sample_profiles


@pytest.mark.parametrize(
    ("requested", "supported", "expected"),
    [
        (-1, 0, "invalid_counts"),
        (3, -1, "invalid_counts"),
        (3, 4, "invalid_counts"),
        (0, 0, "empty_request"),
        (5, 0, "no_support"),
        (5, 2, "partial_support"),
        (5, 5, "complete_support"),
    ],
)
def test_support_is_a_total_named_reading_of_the_counts(
    requested, supported, expected
) -> None:
    assert profile_support_code(requested, supported) == expected


def test_linear_ramp_is_sampled_in_physical_normal_coordinates() -> None:
    spacing = (2.0, 0.5)
    rows, columns = np.indices((9, 9), dtype=np.float64)
    plane = 7.0 + 4.0 * rows + 3.0 * columns
    normals = np.array([[1.0, 0.0], [0.0, 1.0], [np.sqrt(0.5), np.sqrt(0.5)]])
    offsets = np.array([-2.0, 0.0, 2.0])
    points = np.array([[4.0, 4.0]] * len(normals))

    result = sample_profiles(
        plane, points, normals, offsets, spacing, backend="reference"
    )

    expected = np.array(
        [
            [31.0, 35.0, 39.0],
            [23.0, 35.0, 47.0],
            [35.0 - 8.0 * np.sqrt(2.0), 35.0, 35.0 + 8.0 * np.sqrt(2.0)],
        ]
    )
    np.testing.assert_allclose(result.samples, expected, atol=1e-12)
    np.testing.assert_array_equal(result.valid, np.ones((3, 3), dtype=bool))
    np.testing.assert_allclose(result.distances_mm, offsets)
    np.testing.assert_allclose(
        result.slopes,
        [[2.0, 2.0], [6.0, 6.0], [4.0 * np.sqrt(2.0), 4.0 * np.sqrt(2.0)]],
        atol=1e-12,
    )
    assert result.support_code == "complete_support"
    assert result.requested_backend == "reference"
    assert result.effective_backend == "reference"


def test_exact_image_edges_are_sampled_and_outside_points_are_missing() -> None:
    plane = np.arange(9.0).reshape(3, 3)
    points = np.array([[0.0, 0.0], [2.0, 2.0], [-0.01, 1.0]])
    normals = np.array([[1.0, 0.0]] * 3)
    result = sample_profiles(plane, points, normals, np.array([0.0]), (1.0, 1.0))

    np.testing.assert_array_equal(result.valid[:, 0], [True, True, False])
    np.testing.assert_allclose(result.samples[:2, 0], [0.0, 8.0])
    assert np.isnan(result.samples[2, 0])
    assert result.support_code == "partial_support"


def test_zero_weight_nan_corner_does_not_invalidate_an_exact_pixel_sample() -> None:
    plane = np.array([[5.0, np.nan], [np.inf, -np.inf]])
    result = sample_profiles(
        plane,
        np.array([[0.0, 0.0]]),
        np.array([[1.0, 0.0]]),
        np.array([0.0]),
        (1.0, 1.0),
    )
    assert result.valid[0, 0]
    assert result.samples[0, 0] == 5.0


def test_a_positive_weight_nonfinite_corner_makes_that_sample_missing() -> None:
    plane = np.array([[5.0, np.nan], [6.0, 7.0]])
    result = sample_profiles(
        plane,
        np.array([[0.0, 0.5]]),
        np.array([[0.0, 1.0]]),
        np.array([0.0]),
        (1.0, 1.0),
    )
    assert not result.valid[0, 0]
    assert np.isnan(result.samples[0, 0])
    assert result.support_code == "no_support"


def test_empty_profiles_and_one_offset_are_well_defined() -> None:
    empty = sample_profiles(
        np.ones((2, 2)), np.empty((0, 2)), np.empty((0, 2)), np.array([0.0]), (1.0, 1.0)
    )
    assert empty.samples.shape == (0, 1)
    assert empty.support_code == "empty_request"
    assert empty.slopes.shape[0] == 0

    no_offsets = sample_profiles(
        np.ones((2, 2)),
        np.array([[1.0, 1.0]]),
        np.array([[1.0, 0.0]]),
        np.array([]),
        (1.0, 1.0),
    )
    assert no_offsets.samples.shape == (1, 0)
    assert no_offsets.support_code == "empty_request"

    one = sample_profiles(
        np.ones((2, 2)),
        np.array([[1.0, 1.0]]),
        np.array([[1.0, 0.0]]),
        np.array([0.0]),
        (1.0, 1.0),
    )
    assert one.samples.shape == (1, 1)
    assert one.slopes.shape[1] == 0


@pytest.mark.parametrize(
    ("points", "normals", "offsets", "spacing"),
    [
        (np.ones((2,)), np.ones((1, 2)), np.array([0.0]), (1.0, 1.0)),
        (np.ones((1, 2)), np.ones((2, 2)), np.array([0.0]), (1.0, 1.0)),
        (np.ones((1, 2)), np.array([[2.0, 0.0]]), np.array([0.0]), (1.0, 1.0)),
        (np.ones((1, 2)), np.array([[np.nan, 0.0]]), np.array([0.0]), (1.0, 1.0)),
        (np.ones((1, 2)), np.ones((1, 2)), np.array([0.0, 0.0]), (1.0, 1.0)),
        (np.ones((1, 2)), np.ones((1, 2)), np.array([0.0, np.inf]), (1.0, 1.0)),
        (np.ones((1, 2)), np.ones((1, 2)), np.array([0.0]), (1.0, 0.0)),
    ],
)
def test_malformed_profile_geometry_is_rejected(
    points, normals, offsets, spacing
) -> None:
    with pytest.raises(ValueError):
        sample_profiles(np.ones((3, 3)), points, normals, offsets, spacing)


@given(
    a=st.floats(min_value=-5, max_value=5, allow_nan=False, allow_infinity=False),
    b=st.floats(min_value=-5, max_value=5, allow_nan=False, allow_infinity=False),
    c=st.floats(min_value=-5, max_value=5, allow_nan=False, allow_infinity=False),
    row_spacing=st.floats(
        min_value=0.5, max_value=3, allow_nan=False, allow_infinity=False
    ),
    column_spacing=st.floats(
        min_value=0.5, max_value=3, allow_nan=False, allow_infinity=False
    ),
    offset=st.floats(min_value=0.1, max_value=1, allow_nan=False, allow_infinity=False),
)
def test_bilinear_sampling_and_slope_follow_an_analytic_linear_field(
    a: float,
    b: float,
    c: float,
    row_spacing: float,
    column_spacing: float,
    offset: float,
) -> None:
    rows, columns = np.indices((7, 7), dtype=np.float64)
    plane = a + b * rows + c * columns
    norm = np.array([[np.sqrt(0.5), np.sqrt(0.5)]])
    result = sample_profiles(
        plane,
        np.array([[3.0, 3.0]]),
        norm,
        np.array([-offset, offset]),
        (row_spacing, column_spacing),
    )
    physical_slope = (b / row_spacing + c / column_spacing) / np.sqrt(2.0)
    assert np.all(result.valid)
    np.testing.assert_allclose(
        np.diff(result.samples, axis=1)[0] / np.diff(result.distances_mm),
        physical_slope,
        atol=1e-10,
    )


def test_profile_readings_are_read_only() -> None:
    result = sample_profiles(
        np.arange(9.0).reshape(3, 3),
        np.array([[1.0, 1.0]]),
        np.array([[1.0, 0.0]]),
        np.array([-1.0, 1.0]),
        (1.0, 1.0),
    )
    for value in (result.samples, result.valid, result.slopes, result.distances_mm):
        assert not value.flags.writeable


def test_reference_and_jit_agree_on_values_masks_and_nan_standing() -> None:
    rows, columns = np.indices((8, 9), dtype=np.float64)
    plane = rows * 0.25 - columns * 0.75
    plane[2, 3] = np.nan
    points = np.array([[2.0, 2.0], [3.0, 4.0], [0.0, 0.0]])
    normals = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]])
    offsets = np.array([-1.0, 0.0, 1.0])
    reference = sample_profiles(
        plane, points, normals, offsets, (1.0, 1.0), backend="reference"
    )
    jit = sample_profiles(plane, points, normals, offsets, (1.0, 1.0), backend="jit")

    assert jit.requested_backend == "jit"
    assert jit.effective_backend == "jit"
    for name in ("samples", "valid", "slopes", "distances_mm"):
        expected, actual = getattr(reference, name), getattr(jit, name)
        assert expected.shape == actual.shape
        assert expected.dtype == actual.dtype
        if expected.dtype.kind == "f":
            np.testing.assert_array_equal(np.isnan(actual), np.isnan(expected))
            np.testing.assert_array_equal(
                np.signbit(actual[~np.isnan(actual)]),
                np.signbit(expected[~np.isnan(expected)]),
            )
            np.testing.assert_allclose(
                actual, expected, rtol=0.0, atol=0.0, equal_nan=True
            )
        else:
            np.testing.assert_array_equal(actual, expected)
