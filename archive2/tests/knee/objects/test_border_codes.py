"""Intent examples for a dark-band reading, not anatomical admission."""

import numpy as np
import pytest

from knee.objects.border_codes import border_code
from knee.objects.interiors import dark_bands
from knee.objects.profiles import sample_profiles


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ((False, -1, 3, 1, True), "invalid_measurement"),
        ((False, 4, 3, 1, True), "invalid_measurement"),
        ((False, 3, 3, -1, True), "invalid_measurement"),
        ((True, 0, 3, 1, True), "frame_clipped"),
        ((False, 0, 0, 0, False), "empty_profile"),
        ((False, 2, 3, 1, True), "missing_profile"),
        ((False, 3, 3, 0, True), "no_dark_bracket"),
        ((False, 3, 3, 1, False), "no_dark_bracket"),
        ((False, 5, 5, 2, True), "multiple_brackets"),
        ((False, 5, 5, 1, True), "bracketed"),
    ],
)
def test_named_border_outcomes(args, expected):
    assert border_code(*args) == expected


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ([8, 8, 0, 0, 8, 8, 8], 1),
        ([8, 0, 8, 0, 8, 8, 8], 3),
        ([0, 0, 8, 8, 8, 8, 8], 2),
        ([8, 8, 8, 8, 8, 8, 8], 2),
        ([8, 8, 0, np.nan, 8, 8, 8], 4),
    ],
)
def test_native_profile_distinguishes_bounded_multiple_missing_and_unbounded(
    values, expected
):
    plane = np.tile(values, (3, 1))
    points, normals = np.array([[1.0, 3.0]]), np.array([[0.0, 1.0]])
    profile = sample_profiles(plane, points, normals, np.arange(-3.0, 4.0), (1.0, 1.0))
    lower, upper, trace, codes = dark_bands(
        profile, 0, np.array([2]), points, normals, np.ones(2)
    )
    assert codes[0] == expected
    if expected == 1:
        assert lower[0] == -1 and upper[0] == 0
        np.testing.assert_array_equal(trace, [[1.0, 2.5]])
    else:
        assert np.isnan(lower[0]) and np.isnan(upper[0]) and np.all(np.isnan(trace))
