"""Unobserved values cannot enter the local-contrast measurement."""

import numpy as np

from knee.objects.assignments import local_lightness


def test_an_excluded_pixels_stored_value_cannot_change_any_reading():
    plane = np.arange(81, dtype=float).reshape(9, 9) + 10.0
    excluded = np.zeros(plane.shape, dtype=bool)
    excluded[4, 4] = True
    first = plane.copy()
    second = plane.copy()
    first[4, 4] = 0.0
    second[4, 4] = 1000.0
    low_readings = local_lightness(first, excluded, np.ones(2))
    high_readings = local_lightness(second, excluded, np.ones(2))
    for low, high in zip(low_readings, high_readings, strict=True):
        assert np.allclose(low, high, equal_nan=True)


def test_a_nonfinite_acquired_pixel_has_no_smoothed_light_or_ratio():
    plane = np.full((9, 9), 10.0)
    plane[4, 4] = np.nan
    lightness, smooth, _ = local_lightness(
        plane, np.zeros(plane.shape, bool), np.ones(2)
    )
    assert np.isnan(smooth[4, 4])
    assert np.isnan(lightness[4, 4])
