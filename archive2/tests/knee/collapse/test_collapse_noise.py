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
    MAD_TO_SIGMA,
    background_split,
    bright_sigma,
    coil_count,
    coil_count_robust,
    dark_sigma,
    finite_values,
    floor_bias,
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
    quiet = quiet_population(values, 9.5)
    assert quiet.size == 10
    assert quiet.max() == 9.0


def test_the_quiet_population_does_not_depend_on_where_the_values_sit() -> None:
    # Taken by value, never from a designated corner: 181 of 336 series give no spatial guarantee.
    values = np.arange(100.0)
    rng = np.random.default_rng(3)
    shuffled = values.copy()
    rng.shuffle(shuffled)
    assert sorted(quiet_population(values, 19.5)) == sorted(
        quiet_population(shuffled, 19.5)
    )


def test_a_reading_not_made_is_empty_never_a_reading_of_zero() -> None:
    assert quiet_population(np.empty(0), 9.5).size == 0
    assert quiet_population(np.arange(10.0), float("nan")).size == 0


def test_the_split_finds_the_valley_between_two_modes() -> None:
    rng = np.random.default_rng(21)
    background = rng.normal(10.0, 2.0, 40000)
    tissue = rng.normal(100.0, 15.0, 40000)
    split = background_split(np.concatenate([background, tissue]))
    assert 20.0 < split < 70.0, split


def test_the_split_cuts_a_WHOLE_background_not_a_truncated_one() -> None:
    """The fault this replaces. A quantile truncates the population from above and its moments stop
    being the noise's; a valley keeps the mode entire."""
    sigma = 7.0
    rng = np.random.default_rng(23)
    background = _rayleigh(sigma, 120000, seed=23)
    tissue = rng.normal(300.0, 40.0, 120000)
    values = np.concatenate([background, tissue])

    whole = quiet_population(values, background_split(values))
    assert abs(coil_count_robust(whole) - 1.0) < 0.1
    assert abs(dark_sigma(whole, 1.0) - sigma) < 0.3

    # the old instrument, for contrast: the lowest fifth BY VALUE, truncated near zero, where the
    # density goes as x and the ratio tends to 4/3, which the identity reads as three channels
    truncated = np.sort(values)[: values.size // 5]
    assert coil_count(moment_ratio(truncated)) > 2.0


def test_the_channel_count_survives_outliers_where_the_moment_ratio_does_not() -> None:
    """The measured failure. Fifteen tissue values among 120,000 background ones sent the
    fourth-to-second moment ratio to 7.19, outside the identity's (1, 2], while the second moment
    still gave sigma to 1.4%. A quartile ratio barely moves."""
    rng = np.random.default_rng(41)
    for channels in (1, 2, 4):
        total = np.zeros(120000)
        for _ in range(channels):
            total += (
                rng.normal(0.0, 7.0, 120000) ** 2 + rng.normal(0.0, 7.0, 120000) ** 2
            )
        clean = np.sqrt(total)
        dirty = np.concatenate([clean, rng.normal(300.0, 40.0, 15)])
        assert abs(coil_count_robust(clean) - channels) < 0.1, channels
        assert abs(coil_count_robust(dirty) - channels) < 0.1, channels
        assert np.isnan(coil_count(moment_ratio(dirty))), channels


def test_the_channel_count_abstains_rather_than_guessing() -> None:
    assert np.isnan(coil_count_robust(np.empty(0)))
    assert np.isnan(coil_count_robust(np.full(100, 5.0)))  # too few, and no spread
    assert np.isnan(coil_count_robust(np.zeros(1000)))  # a masked background


def test_a_split_that_is_not_a_number_reads_nothing() -> None:
    assert np.isnan(background_split(np.empty(0)))
    assert np.isnan(background_split(np.full(100, 5.0)))


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
    # here, and this one still reads the law. The count is of BLOCKS, not residuals.
    rng = np.random.default_rng(7)
    plane = np.zeros((300, 300))
    plane[50:250, 50:250] = rng.normal(800.0, 4.0, (200, 200))
    sigma, blocks = bright_sigma(plane, lag=1, floor=400.0)
    assert blocks > 100
    assert abs(sigma - 4.0) < 0.3


def test_the_bright_estimator_reads_the_noise_FLOOR_through_structure() -> None:
    """The measured failure this replaces. Over 336 real series the old reading -- one spread over
    every bright residual -- ran a median of 5.5x the dark estimator, because a residual in real
    anatomy carries edges and texture as well as noise. Among many small blocks the quiet ones hold
    almost no structure, so the LOW end of their spreads is the noise."""
    rng = np.random.default_rng(31)
    sigma = 5.0
    size = 320
    # Texture must be PERVASIVE to reproduce the real failure: a few hard edges perturb only a few
    # percent of residuals, which a MAD ignores by construction. Real tissue carries curvature at
    # every place, so every residual picks some up. A sum of sinusoids at the lag's own scale does
    # that, and leaves a quiet corner where the noise floor still shows.
    y, x = np.meshgrid(np.arange(size), np.arange(size), indexing="ij")
    texture = 120.0 * (np.sin(x / 2.5) * np.cos(y / 3.0) + np.sin((x + y) / 2.0))
    texture[: size // 2, :] = 0.0  # half the field is quiet tissue
    plane = rng.normal(600.0, sigma, (size, size)) + texture

    floor_read, _ = bright_sigma(plane, lag=1, floor=100.0, block=16, quantile=0.1)
    # what the old instrument did: one spread over every residual, structure included
    every = pseudo_residuals(plane, 1).ravel()
    central = float(np.median(np.abs(every - np.median(every)))) * MAD_TO_SIGMA

    # The floor lands on sigma; the whole-field reading sits above it. The inflation here is only
    # about 1.5x because half this fixture is quiet, which pulls a global median down too. On the
    # real corpus, where texture is pervasive, the same whole-field reading ran 5.5x the dark
    # estimator over 336 series -- that figure belongs to the measurement, not to a fixture built
    # to give the floor something to find.
    assert abs(floor_read - sigma) < 1.0, floor_read
    assert central > 1.4 * floor_read, (central, floor_read)


def test_the_floor_needs_quiet_blocks_to_exist_and_says_so_by_reading_high() -> None:
    """The estimator's own precondition, pinned. The quantile must sit BELOW the share of blocks
    that are quiet. Where texture covers almost everything there is no floor to find, and the
    reading rises toward the structure rather than inventing a noise level."""
    rng = np.random.default_rng(33)
    size, sigma = 320, 5.0
    y, x = np.meshgrid(np.arange(size), np.arange(size), indexing="ij")
    texture = 120.0 * (np.sin(x / 2.5) * np.cos(y / 3.0) + np.sin((x + y) / 2.0))

    half_quiet = texture.copy()
    half_quiet[: size // 2, :] = 0.0
    barely_quiet = texture.copy()
    barely_quiet[: size // 16, :] = 0.0  # about 6% of blocks

    quiet_enough, _ = bright_sigma(
        rng.normal(600.0, sigma, (size, size)) + half_quiet, 1, 100.0, 16, 0.1
    )
    too_textured, _ = bright_sigma(
        rng.normal(600.0, sigma, (size, size)) + barely_quiet, 1, 100.0, 16, 0.1
    )
    assert abs(quiet_enough - sigma) < 1.0
    assert too_textured > 2.0 * quiet_enough, (too_textured, quiet_enough)


def test_the_bright_estimator_abstains_when_nothing_stands_above_the_floor() -> None:
    plane = np.full((50, 50), 10.0)
    sigma, blocks = bright_sigma(plane, lag=1, floor=1000.0)
    assert np.isnan(sigma)
    assert blocks == 0


def test_the_block_and_the_quantile_are_the_callers_bars() -> None:
    rng = np.random.default_rng(9)
    plane = rng.normal(500.0, 6.0, (256, 256))
    assert np.isnan(bright_sigma(plane, lag=1, floor=0.0, block=1)[0])
    assert np.isnan(bright_sigma(plane, lag=1, floor=0.0, quantile=0.0)[0])
    assert np.isnan(bright_sigma(plane, lag=1, floor=0.0, quantile=1.5)[0])


def test_the_floors_own_bias_is_derived_and_corrected() -> None:
    """A low quantile rejects structure but under-reads noise, because the block spreads scatter
    even with nothing but noise. The correction comes from the MAD's asymptotic spread,
    sigma / sqrt(0.74 n), never from fitting."""
    # the shape of the bias: lower quantiles and smaller blocks read further below sigma
    assert floor_bias(64, 0.10) < floor_bias(256, 0.10) < floor_bias(1024, 0.10) < 1.0
    assert floor_bias(256, 0.10) < floor_bias(256, 0.25) < floor_bias(256, 0.50)
    assert abs(floor_bias(256, 0.50) - 1.0) < 1e-9  # the median is unbiased
    assert floor_bias(1, 0.1) == 1.0 and floor_bias(256, 0.0) == 1.0

    # and after it, the reading lands on sigma whatever block or quantile is asked for
    rng = np.random.default_rng(57)
    plane = rng.normal(500.0, 6.0, (512, 512))
    for block in (8, 16, 32):
        for quantile in (0.1, 0.25):
            read, _ = bright_sigma(plane, 1, 0.0, block, quantile)
            assert abs(read / 6.0 - 1.0) < 0.03, (block, quantile, read)


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
