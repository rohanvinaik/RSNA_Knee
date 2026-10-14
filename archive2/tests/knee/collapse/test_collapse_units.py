"""Intent tests for the variance-stabilizing transform (knee.collapse.units), written from the
contract: after it, one unit is one sigma at ANY intensity, the dark end included; the transform is
derived from the measured noise law and fitted to nothing; and it is never built on an abstention.

The analytic facts checked here are derived, never chosen: a Rayleigh magnitude has mean
1.2533 sigma and variance 0.4292 sigma^2; E[M^2] = A^2 + 2 L sigma^2 exactly for a noncentral-chi
magnitude; and the variance rises to sigma^2 far above the noise.
"""

import numpy as np

from knee.collapse.units import magnitude_moments, stabilizer, to_units

SIGMA = 7.0


def _noncentral_chi(signal: float, sigma: float, coils: int, n: int, seed: int = 17):
    """A magnitude over `coils` complex channels: the root of the summed squares."""
    rng = np.random.default_rng(seed)
    total = np.zeros(n)
    for channel in range(coils):
        # the whole signal sits in the first channel's real part, the usual convention
        real = rng.normal(signal if channel == 0 else 0.0, sigma, n)
        imaginary = rng.normal(0.0, sigma, n)
        total += real**2 + imaginary**2
    return np.sqrt(total)


def test_a_rayleigh_magnitude_has_its_known_moments() -> None:
    mean, variance = magnitude_moments(np.array([0.0]), SIGMA, 1.0)
    assert abs(float(mean[0]) - 1.2533 * SIGMA) < 0.01 * SIGMA
    assert abs(float(variance[0]) - 0.4292 * SIGMA**2) < 0.01 * SIGMA**2


def test_the_second_moment_identity_is_exact() -> None:
    # E[M^2] = A^2 + 2 L sigma^2, which is what makes the bias removable rather than clippable.
    for coils in (1.0, 2.0, 4.0):
        signal = np.array([0.0, 3.0, 11.0, 40.0])
        mean, variance = magnitude_moments(signal, SIGMA, coils)
        second = variance + mean**2
        assert np.allclose(second, signal**2 + 2 * coils * SIGMA**2)


def test_the_variance_rises_to_one_sigma_squared_far_above_the_noise() -> None:
    # Computed from the moments, not quoted: a consultant's summary gave 0.86 at two sigma and the
    # identity gives 0.8363. The computed value is the one pinned.
    _, variance = magnitude_moments(
        np.array([0.0, 2 * SIGMA, 3 * SIGMA, 40 * SIGMA]), SIGMA, 1.0
    )
    ratios = variance / SIGMA**2
    assert abs(ratios[0] - 0.4292) < 0.001
    assert abs(ratios[1] - 0.8363) < 0.001
    assert abs(ratios[2] - 0.9348) < 0.001
    assert abs(ratios[3] - 0.9997) < 0.001


def test_the_moments_are_monotone_in_the_signal() -> None:
    # The table is read as variance against expected magnitude, which needs the mean to rise.
    signal = np.linspace(0.0, 30 * SIGMA, 200)
    mean, _ = magnitude_moments(signal, SIGMA, 1.0)
    assert np.all(np.diff(mean) > 0)


def test_the_transform_gives_unit_spread_wherever_there_is_signal() -> None:
    """The contract, as far as it actually holds: at or above one sigma of signal the transform is
    within 7%, and above five sigma within half a percent."""
    table = stabilizer(SIGMA, 1.0)
    assert table is not None
    for signal in (SIGMA, 2 * SIGMA, 3 * SIGMA):
        spread = float(
            np.std(to_units(_noncentral_chi(signal, SIGMA, 1, 200000), table))
        )
        assert abs(spread - 1.0) < 0.07, (signal / SIGMA, spread)
    for signal in (5 * SIGMA, 10 * SIGMA, 25 * SIGMA):
        spread = float(
            np.std(to_units(_noncentral_chi(signal, SIGMA, 1, 200000), table))
        )
        assert abs(spread - 1.0) < 0.005, (signal / SIGMA, spread)


def test_the_dark_end_falls_short_by_a_known_bounded_amount() -> None:
    """The delta method's limit, pinned rather than hidden. At pure noise the Rayleigh is broad and
    skewed against its own mean, so the linearization under-reads by about 11%. A null computed in
    air must use this, never assume one."""
    table = stabilizer(SIGMA, 1.0)
    assert table is not None
    spread = float(np.std(to_units(_noncentral_chi(0.0, SIGMA, 1, 400000), table)))
    assert 0.86 < spread < 0.91, spread


def test_the_transform_stabilizes_a_multi_channel_magnitude_too() -> None:
    table = stabilizer(SIGMA, 4.0)
    assert table is not None
    for signal in (3 * SIGMA, 12 * SIGMA):
        spread = float(
            np.std(to_units(_noncentral_chi(signal, SIGMA, 4, 200000), table))
        )
        assert abs(spread - 1.0) < 0.05, (signal / SIGMA, spread)
    # More channels make the dark end less skewed, so it falls short by less than one channel's 11%.
    dark = float(np.std(to_units(_noncentral_chi(0.0, SIGMA, 4, 200000), table)))
    assert 0.90 < dark < 0.98, dark


def test_without_the_transform_the_spread_is_not_constant() -> None:
    """What the transform is for: raw magnitudes read in sigmas do NOT have unit spread at the
    dark end, which is where a difference field would otherwise misread its own noise."""
    dark = np.std(_noncentral_chi(0.0, SIGMA, 1, 200000)) / SIGMA
    bright = np.std(_noncentral_chi(25 * SIGMA, SIGMA, 1, 200000)) / SIGMA
    assert abs(dark - 0.655) < 0.02  # sqrt(0.429)
    assert abs(bright - 1.0) < 0.02
    assert bright / dark > 1.4


def test_the_dark_end_is_stretched_relative_to_the_bright_end() -> None:
    # f' = 1 / sqrt(variance), and the dark end's variance is 0.429 sigma^2, so its slope is
    # 1/sqrt(0.429) = 1.53 times the bright end's.
    table = stabilizer(SIGMA, 1.0)
    assert table is not None
    bright_slope = (table.units[-1] - table.units[-2]) / (
        table.magnitude[-1] - table.magnitude[-2]
    )
    assert abs(table.floor_slope / bright_slope - 1.527) < 0.02


def test_far_above_the_noise_the_transform_is_one_sigma_per_sigma() -> None:
    table = stabilizer(SIGMA, 1.0)
    assert table is not None
    far = np.array([30 * SIGMA, 31 * SIGMA])
    step = float(np.diff(to_units(far, table))[0])
    assert abs(step - 1.0) < 0.01


def test_a_reading_below_the_no_signal_mean_stays_on_the_scale() -> None:
    # A magnitude can read below its own expected value; the air null needs those on one scale.
    table = stabilizer(SIGMA, 1.0)
    assert table is not None
    got = to_units(np.array([0.0, 0.5 * SIGMA, table.magnitude[0]]), table)
    assert np.all(np.isfinite(got))
    assert np.all(np.diff(got) > 0)
    assert got[-1] == 0.0


def test_the_table_is_never_built_on_an_abstention() -> None:
    for sigma, coils in (
        (float("nan"), 1.0),
        (0.0, 1.0),
        (-1.0, 1.0),
        (SIGMA, float("nan")),
        (SIGMA, 0.0),
        (SIGMA, 0.5),
    ):
        assert stabilizer(sigma, coils) is None, (sigma, coils)


def test_a_reading_never_made_is_not_transformed_into_one() -> None:
    table = stabilizer(SIGMA, 1.0)
    assert table is not None
    got = to_units(np.array([np.nan, np.inf, -np.inf, 10.0]), table)
    assert np.isnan(got[0]) and np.isnan(got[1]) and np.isnan(got[2])
    assert np.isfinite(got[3])
