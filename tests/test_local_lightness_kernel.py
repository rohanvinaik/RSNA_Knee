"""The compiled local-lightness kernel preserves the independent SciPy measurement."""

import numpy as np
import pytest
from scipy import ndimage as ndi

from knee.objects.assignments import local_lightness
from knee.objects.local_lightness import local_lightness_jit

SAMPLING_PIXELS = 3
LOCAL_CONTRAST_MM = 20.0


def median_of_seen(window: np.ndarray) -> float:
    seen = window[np.isfinite(window)]
    return float(np.median(seen)) if seen.size else float("nan")


def window_pixels(spacing_rc: np.ndarray, length_mm: float) -> tuple[int, int]:
    steps = np.asarray(spacing_rc, dtype=np.float64)
    if steps.shape != (2,) or not np.all(np.isfinite(steps)) or np.any(steps <= 0):
        raise ValueError("invalid_spacing")
    counts = np.rint(length_mm / steps).astype(int)
    rows, cols = (int(n + 1 if n % 2 == 0 else n) for n in counts)
    return rows, cols


def scipy_reference(
    plane: np.ndarray, excluded: np.ndarray, spacing_rc: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    values = np.asarray(plane, dtype=np.float64)
    gone = np.asarray(excluded, dtype=bool) | ~np.isfinite(values)
    if values.ndim != 2 or gone.shape != values.shape:
        raise ValueError("lightness_inputs_must_share_a_2d_shape")
    with np.errstate(over="ignore", invalid="ignore"):
        smooth = ndi.generic_filter(
            np.where(gone, np.nan, values),
            median_of_seen,
            size=SAMPLING_PIXELS,
            mode="constant",
            cval=np.nan,
        )
    smooth[gone] = np.nan
    with np.errstate(over="ignore", invalid="ignore"):
        surround = ndi.generic_filter(
            smooth,
            median_of_seen,
            size=window_pixels(spacing_rc, LOCAL_CONTRAST_MM),
            mode="constant",
            cval=np.nan,
        )
    lightness = np.full(values.shape, np.nan)
    with np.errstate(invalid="ignore"):
        np.divide(smooth, surround, out=lightness, where=surround > 0)
    return lightness, smooth, surround


def assert_same_float_arrays(actual, expected) -> None:
    assert actual.dtype == expected.dtype == np.dtype(np.float64)
    assert actual.shape == expected.shape
    assert np.array_equal(actual.view(np.uint64), expected.view(np.uint64))


def compare(
    plane: np.ndarray, excluded: np.ndarray, spacing_rc: tuple[float, float]
) -> None:
    before_plane = plane.copy()
    before_excluded = excluded.copy()
    spacing = np.asarray(spacing_rc, dtype=np.float64)
    expected = scipy_reference(plane, excluded, spacing)
    actual = local_lightness_jit(
        plane, excluded, window_pixels(spacing, LOCAL_CONTRAST_MM)
    )
    production = local_lightness(plane, excluded, spacing)
    for readings in (actual, production):
        for got, want in zip(readings, expected, strict=True):
            assert_same_float_arrays(got, want)
    assert np.array_equal(plane, before_plane, equal_nan=True)
    assert np.array_equal(excluded, before_excluded)


@pytest.mark.parametrize("spacing_rc", [(20.0, 20.0), (10.0, 5.0), (5.0, 2.5)])
def test_compiled_kernel_matches_scipy_for_deterministic_random_planes(
    spacing_rc,
) -> None:
    rng = np.random.default_rng(140716)
    plane = rng.normal(loc=20.0, scale=35.0, size=(17, 19))
    plane[rng.random(plane.shape) < 0.12] = np.nan
    plane[rng.random(plane.shape) < 0.04] = np.inf
    excluded = rng.random(plane.shape) < 0.18
    compare(plane, excluded, spacing_rc)


def test_compiled_kernel_matches_at_edges_and_with_even_sample_counts() -> None:
    plane = np.array(
        [
            [0.0, 2.0, 8.0, -4.0],
            [6.0, 10.0, np.nan, 14.0],
            [18.0, 22.0, 26.0, 30.0],
        ],
        dtype=np.float64,
    )
    excluded = np.zeros(plane.shape, dtype=bool)
    excluded[1, 1] = True
    compare(plane, excluded, (20.0, 20.0))


def test_even_boundary_median_half_value_and_nonpositive_surrounds() -> None:
    plane = np.array([[-4.0, -2.0], [0.0, 2.0]], dtype=np.float64)
    excluded = np.zeros(plane.shape, dtype=bool)
    actual = local_lightness_jit(plane, excluded, (1, 1))
    expected = scipy_reference(plane, excluded, np.asarray((20.0, 20.0)))
    for got, want in zip(actual, expected, strict=True):
        assert_same_float_arrays(got, want)
    assert actual[1][0, 0] == -1.0
    assert np.isnan(actual[0][0, 0])


def test_even_finite_median_overflow_keeps_positive_infinite_surround_ratio() -> None:
    plane = np.full((3, 3), 1.1e308, dtype=np.float64)
    excluded = np.zeros(plane.shape, dtype=bool)
    excluded[0, 0] = True
    spacing = np.asarray((20.0 / 3.0, 20.0 / 3.0))
    expected = scipy_reference(plane, excluded, spacing)
    actual = local_lightness_jit(plane, excluded, window_pixels(spacing, 20.0))
    for got, want in zip(actual, expected, strict=True):
        assert_same_float_arrays(got, want)
    assert np.isfinite(actual[1][0, 1]) and actual[1][0, 1] > 0.0
    assert np.isposinf(actual[2][0, 1])
    assert actual[0][0, 1] == 0.0


def test_signed_zero_odd_and_even_medians_match_scipy_bits() -> None:
    plane = np.array([[-0.0, 4.0, -0.0], [2.0, -0.0, 6.0], [-0.0, 8.0, -0.0]])
    excluded = np.zeros(plane.shape, dtype=bool)
    compare(plane, excluded, (20.0, 20.0))


def test_noncanonical_input_nan_payload_does_not_escape_measurement() -> None:
    plane = np.arange(25, dtype=np.float64).reshape(5, 5)
    plane.view(np.uint64)[2, 2] = np.uint64(0x7FF8000000000001)
    excluded = np.zeros(plane.shape, dtype=bool)
    compare(plane, excluded, (20.0, 20.0))


@pytest.mark.parametrize(
    "plane,excluded",
    [
        (np.zeros((5, 7), dtype=np.float32), np.zeros((5, 7), dtype=bool)),
        (np.full((6, 8), np.nan), np.zeros((6, 8), dtype=bool)),
        (np.arange(48, dtype=np.int16).reshape(6, 8), np.ones((6, 8), dtype=bool)),
    ],
)
def test_compiled_kernel_matches_empty_zero_and_integer_inputs(plane, excluded) -> None:
    compare(plane, excluded, (10.0, 10.0))


def test_excluded_pixel_perturbations_do_not_change_readings() -> None:
    rng = np.random.default_rng(160716)
    plane = rng.uniform(1.0, 90.0, size=(13, 15))
    excluded = np.zeros(plane.shape, dtype=bool)
    excluded[3:8, 4:10] = True
    baseline = local_lightness_jit(plane, excluded, (5, 7))
    perturbed = plane.copy()
    perturbed[excluded] = np.inf
    changed = local_lightness_jit(perturbed, excluded, (5, 7))
    for got, want in zip(changed, baseline, strict=True):
        assert_same_float_arrays(got, want)


def test_window_shape_validation_is_named() -> None:
    plane = np.ones((3, 3), dtype=np.float64)
    excluded = np.zeros((3, 3), dtype=bool)
    with pytest.raises(ValueError, match="^invalid_window_shape$"):
        local_lightness_jit(plane, excluded, (2, 3))
