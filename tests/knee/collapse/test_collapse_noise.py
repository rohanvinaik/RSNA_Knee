"""Intent tests for the collapse's noise measurements (knee.collapse.noise), written from the
contract: one law per series in the series' own values, read two independent ways, each function a
measurement that decides nothing, and a reading not made returned as NaN rather than as zero.

The analytic facts these check are derived, never chosen: a Rayleigh background has a fourth-to-
second moment ratio of exactly 2; E[M^2] = 2 * L * sigma_g^2 for a noncentral-chi magnitude; the MAD
of a normal sample is sigma * 0.6745; and a centre minus the mean of four independent neighbours has
variance sigma^2 * 5/4.
"""

import numpy as np

from knee.collapse.noise import (
    bright_sigma,
    coil_count,
    dark_sigma,
    finite_values,
    moment_ratio,
    pseudo_residuals,
    quiet_population,
    signal_squared,
)


def _rayleigh(sigma: float, n: int, seed: int = 11) -> np.ndarray:
    """A single-channel magnitude background: the modulus of two independent normals."""
    rng = np.random.default_rng(seed)
    real = rng.normal(0.0, sigma, n)
    imaginary = rng.normal(0.0, sigma, n)
    return np.sqrt(real**2 + imaginary**2)


def test_only_finite_values_are_readings() -> None:
    volume = np.array([[1.0, np.nan], [np.inf, 4.0]])
    assert sorted(finite_values(volume).tolist()) == [1.0, 4.0]


def test_the_quiet_population_is_the_lowest_share_wherever_it_lies() -> None:
    values = np.arange(100.0)
    quiet = quiet_population(values, 0.1)
    assert quiet.size == 10
    assert quiet.max() == 9.0


def test_the_quiet_population_does_not_depend_on_where_the_values_sit() -> None:
    # Taken by value, never from a designated corner: 181 of 336 series give no spatial guarantee.
    values = np.arange(100.0)
    rng = np.random.default_rng(3)
    shuffled = values.copy()
    rng.shuffle(shuffled)
    assert np.array_equal(
        quiet_population(values, 0.2), quiet_population(shuffled, 0.2)
    )


def test_a_reading_not_made_is_empty_never_a_reading_of_zero() -> None:
    assert quiet_population(np.empty(0), 0.1).size == 0
    assert quiet_population(np.arange(10.0), 0.0).size == 0
    assert quiet_population(np.arange(10.0), 1.5).size == 0


def test_a_rayleigh_background_reads_a_moment_ratio_of_two() -> None:
    ratio = moment_ratio(_rayleigh(7.0, 200000))
    assert abs(ratio - 2.0) < 0.02


def test_the_moment_ratio_recovers_one_channel() -> None:
    assert abs(coil_count(moment_ratio(_rayleigh(7.0, 200000))) - 1.0) < 0.05


def test_the_channel_count_inverts_the_identity_exactly() -> None:
    assert coil_count(2.0) == 1.0
    assert coil_count(1.5) == 2.0
    assert coil_count(1.25) == 4.0


def test_a_ratio_the_identity_cannot_hold_is_not_a_channel_count() -> None:
    for ratio in (1.0, 0.5, 2.5, float("nan"), float("inf")):
        assert np.isnan(coil_count(ratio)), ratio


def test_the_dark_estimator_recovers_the_sigma_it_was_built_from() -> None:
    sigma = 7.0
    values = _rayleigh(sigma, 200000)
    assert abs(dark_sigma(values, coils=1.0) - sigma) < 0.05


def test_a_masked_background_abstains_rather_than_reading_zero() -> None:
    # Every quiet value exactly zero is a vendor-masked background, not a sigma of zero.
    assert np.isnan(dark_sigma(np.zeros(500), coils=1.0))
    assert np.isnan(dark_sigma(np.empty(0), coils=1.0))


def test_the_dark_estimator_abstains_without_a_channel_count() -> None:
    values = _rayleigh(7.0, 1000)
    assert np.isnan(dark_sigma(values, coils=float("nan")))
    assert np.isnan(dark_sigma(values, coils=0.0))


def test_a_flat_plane_holds_no_residual() -> None:
    assert np.allclose(pseudo_residuals(np.full((20, 20), 5.0), lag=1), 0.0)


def test_a_residual_reads_back_as_one_sigma() -> None:
    # The sqrt(4/5) scale is derived from the neighbour count, so the residual's spread is sigma.
    rng = np.random.default_rng(5)
    plane = rng.normal(0.0, 3.0, (400, 400))
    assert abs(float(np.std(pseudo_residuals(plane, lag=1))) - 3.0) < 0.05


def test_a_plane_too_small_for_its_lag_holds_no_interior_place() -> None:
    assert pseudo_residuals(np.ones((4, 4)), lag=2).size == 0
    assert pseudo_residuals(np.ones((20, 20)), lag=0).size == 0
    assert pseudo_residuals(np.ones(20), lag=1).size == 0


def test_the_bright_estimator_recovers_sigma_without_reading_the_background() -> None:
    # A bright field with a masked (exactly zero) border: the dark estimator would read nothing
    # here, and this one still reads the law.
    rng = np.random.default_rng(7)
    plane = np.zeros((300, 300))
    plane[50:250, 50:250] = rng.normal(800.0, 4.0, (200, 200))
    sigma, count = bright_sigma(plane, lag=1, floor=400.0)
    assert count > 10000
    assert abs(sigma - 4.0) < 0.2


def test_the_bright_estimator_abstains_when_nothing_stands_above_the_floor() -> None:
    plane = np.full((50, 50), 10.0)
    sigma, count = bright_sigma(plane, lag=1, floor=1000.0)
    assert np.isnan(sigma)
    assert count == 0


def test_the_floor_is_the_callers_so_the_two_estimators_stay_independent() -> None:
    rng = np.random.default_rng(9)
    plane = rng.normal(500.0, 6.0, (200, 200))
    high, _ = bright_sigma(plane, lag=1, floor=400.0)
    low, _ = bright_sigma(plane, lag=1, floor=0.0)
    assert abs(high - low) < 0.5


def test_the_magnitude_bias_is_removed_exactly_not_clipped() -> None:
    # E[M^2] = A^2 + 2 L sigma^2, so the identity recovers A^2 on average. At A = 0 the estimate
    # scatters around zero and the negative half is kept: clipping would restore the bias.
    sigma = 5.0
    values = _rayleigh(sigma, 200000)
    estimate = signal_squared(values, sigma=sigma, coils=1.0)
    assert abs(float(np.mean(estimate))) < 2.0
    assert float(np.min(estimate)) < 0.0


def test_the_signal_square_abstains_without_a_law() -> None:
    values = np.array([1.0, 2.0, 3.0])
    assert np.all(np.isnan(signal_squared(values, sigma=float("nan"), coils=1.0)))
    assert np.all(np.isnan(signal_squared(values, sigma=5.0, coils=0.0)))
