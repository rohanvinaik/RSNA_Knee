"""The regime key keeps what it computed, both signs (task 7.2 and 7.1a, the field's retained readings).

Written by the lead BEFORE the body. Two things the field already computes and dropped: the
histogram its valley is read from (the `look` probe redrew it by hand), and the moment-ratio
channel count, which the robust reading replaced in production and which is a second member of
the same question, kept beside it because the founder keeps everything the pipeline computes,
conflicts included. And one thing it declared and never read: `QUIET_SHARE`, whose rule the
valley replaced, so the declaration lied about being an argument and goes.
"""

import math
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import norm

from knee.collapse import regime as regime_module
from knee.collapse.noise import (
    background_histogram,
    background_split,
    coil_count,
    histogram_valley,
    moment_ratio,
    quiet_population,
)
from knee.collapse.regime import GAUSSIAN_SPREAD_RATIO, RegimeKey, read_regime
from knee.study.series import Series
from knee.study.tables import SeriesRow

ROW = SeriesRow("study", "series", "1", "1", "Coronal")


def _volume(seed: int = 0, contaminated: float = 0.0) -> np.ndarray:
    """Four slices: the left half a Rayleigh background at sigma 5, the right half tissue near 200
    with its own spread, so the histogram has a background mode, a valley and a tissue mode.

    `contaminated` replaces that fraction of the background's columns with a Rayleigh at five times
    the sigma. Those values stay BELOW the valley, so they enter the quiet population and send its
    fourth moment outside the identity's range while its quartiles barely move. (The earlier
    fixture wrote outliers of 150 into a reshaped copy, which touched nothing, and 150 lies above
    the valley in any case, so the negative test passed for the sampling reason and not for
    contamination; measured 2026-10-12 by the regime builder.)
    """
    rng = np.random.default_rng(seed)
    volume = np.empty((4, 64, 64))
    volume[:, :, :32] = rng.rayleigh(5.0, (4, 64, 32))
    volume[:, :, 32:] = rng.normal(200.0, 20.0, (4, 64, 32)).clip(60.0, None)
    columns = round(32 * contaminated)
    if columns:
        volume[:, :, :columns] = rng.rayleigh(25.0, (4, 64, columns))
    return volume


def _nan_equal(left: float, right: float) -> bool:
    """Equal, with NaN equal to NaN: an abstention seated beside an abstention is the same reading."""
    return (math.isnan(left) and math.isnan(right)) or left == right


def _series(volume: np.ndarray | None) -> Series:
    return Series(
        row=ROW,
        directory=Path("."),
        slices=(),
        stack=("stackable",),
        volume=volume,
        geometry=None,
    )


# ---------------------------------------------------------------- positive


def test_the_histogram_is_split_into_its_two_steps_and_agrees_with_the_one_call() -> (
    None
):
    values = _volume().ravel()
    counts, edges = background_histogram(values)
    assert counts.dtype == np.int64 and edges.dtype == np.float64
    assert counts.shape == (512,) and edges.shape == (513,)
    assert int(counts.sum()) == values.size
    assert histogram_valley(counts, edges) == background_split(values)
    assert np.isfinite(background_split(values))


def test_the_regime_retains_the_histogram_its_valley_was_read_from() -> None:
    """Retained as tuples of plain numbers, so the writer's field enumeration serialises them
    as it does every other reading, and the field frame can draw the valley on them."""
    key = read_regime(_series(_volume()))
    assert isinstance(key, RegimeKey)
    assert isinstance(key.histogram_counts, tuple) and isinstance(
        key.histogram_edges, tuple
    )
    assert all(type(count) is int for count in key.histogram_counts)
    assert all(type(edge) is float for edge in key.histogram_edges)
    assert sum(key.histogram_counts) == _volume().size
    assert len(key.histogram_edges) == len(key.histogram_counts) + 1 == 513
    counts = np.asarray(key.histogram_counts, dtype=np.int64)
    edges = np.asarray(key.histogram_edges, dtype=np.float64)
    assert histogram_valley(counts, edges) == key.background_split


def test_the_moment_channel_count_is_seated_beside_the_robust_one() -> None:
    """Seated means EQUAL to the member's own reading of the same quiet population, NaN included.

    A one-channel sample's moment ratio scatters about exactly 2.0, the identity's upper bound, so
    on about half of all seeds the identity refuses and the member abstains (76 of 200 seeds on
    this fixture, measured 2026-10-12). That abstention IS the reading, seated beside the robust
    member's; the first version of this test compared NaN with NaN and demanded a finite count of
    a sample the identity had rightly refused.
    """
    for seed in range(8):
        key = read_regime(_series(_volume(seed)))
        assert key is not None
        quiet = quiet_population(_volume(seed).ravel(), key.background_split)
        assert _nan_equal(key.coils_moment, coil_count(moment_ratio(quiet))), seed
        # two readings of one question, both carried; the word is still read from the robust one
        assert key.coils_word in ("single", "multi", "implausible_ratio")


def test_a_ratio_the_identity_accepts_reads_one_channel_beside_the_robust_one() -> None:
    """On a seed whose sample ratio falls inside (1, 2], both members read one channel."""
    key = read_regime(_series(_volume(seed=2)))
    assert key is not None
    assert np.isfinite(key.coils_moment)
    assert abs(key.coils_moment - 1.0) < 0.15
    assert abs(key.coils - 1.0) < 0.15


def test_the_gaussian_spread_reference_is_derived_not_chosen() -> None:
    derived = (norm.ppf(0.95) - norm.ppf(0.05)) / (norm.ppf(0.75) - norm.ppf(0.25))
    assert GAUSSIAN_SPREAD_RATIO == pytest.approx(derived, abs=5e-5)


# ---------------------------------------------------------------- negative


def test_a_background_the_identity_refuses_is_nan_never_a_count() -> None:
    """MUST NOT: turn a contaminated fourth moment into a channel count.

    With fifteen percent of the background drawn at five times the sigma, below the valley, the
    quiet population's moment ratio leaves (1, 2] (2.29 measured) while its quartile ratio barely
    moves: the moment member abstains, the robust member still reads one channel, and the
    disagreement is the record, not an error.
    """
    key = read_regime(_series(_volume(contaminated=0.15)))
    assert key is not None
    assert np.isnan(key.coils_moment)
    assert np.isfinite(key.coils)
    assert abs(key.coils - 1.0) < 0.15


def test_an_empty_or_flat_population_has_no_histogram_and_no_valley() -> None:
    counts, edges = background_histogram(np.empty(0))
    assert counts.shape == (0,) and edges.shape == (0,)
    assert np.isnan(histogram_valley(counts, edges))
    counts, edges = background_histogram(np.full(100, 7.0))
    assert counts.shape == (0,) and edges.shape == (0,)
    assert np.isnan(background_split(np.full(100, 7.0)))


def test_a_series_without_a_volume_still_has_no_regime() -> None:
    assert read_regime(_series(None)) is None


def test_no_bar_is_declared_that_nothing_reads() -> None:
    """MUST NOT: carry a constant whose comment calls it an argument when no function takes it.
    `QUIET_SHARE`'s rule was replaced by the valley (`background_split`), and a declared bar
    nothing reads is a bar that lies about what the reading used."""
    assert not hasattr(regime_module, "QUIET_SHARE")
