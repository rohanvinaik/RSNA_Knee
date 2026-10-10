"""The collapse's noise measurements: one law per series, read two independent ways.

The sibling build fits sigma^2 = a + b * brightness, because a photon counter jitters more where it
is brighter (cell_tracking `physics/flicker.py`). MR magnitude is not a photon counter. For
per-channel complex noise sigma_g it is Rician, and in that parameterization b is about zero with a
sub-additive dark end, so an affine fit would read a false positive slope. The structure is kept --
one law per series, measured, with a transform derived from it -- and the family (a, b) is replaced
by (sigma_g, coils).

Every function here is a MEASUREMENT: it returns a number with its scope, and decides nothing. The
decisions are in `codes.py`, and they read these numbers. Nothing here is fitted to a label.

Units: every sigma is in the series' own stored values, never normalized. Arrays are float64.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import chi2, norm

# The spread of a normal sample estimated from its median absolute deviation: MAD * this is sigma.
# Derived, not chosen: the MAD of a normal is sigma * Phi^-1(3/4) = sigma * 0.674489...
MAD_TO_SIGMA = 1.0 / 0.6744897501960817

# A centre minus the mean of four independent neighbours has variance sigma^2 * (1 + 1/4), so the
# residual is scaled by this to read back as one sigma. Derived from the count of neighbours.
FOUR_NEIGHBOUR_SCALE = np.sqrt(4.0 / 5.0)


def finite_values(volume: np.ndarray) -> np.ndarray:
    """Every finite value of `volume`, flat, float64. Non-finite values are not readings."""
    flat = np.asarray(volume, dtype=np.float64).ravel()
    return flat[np.isfinite(flat)]


def background_split(values: np.ndarray, bins: int = 512, smooth: int = 5) -> float:
    """The VALLEY after the background's mode: the first local minimum of the histogram past its
    first peak.

    Two instruments were tried before this one, and each failed in a way worth keeping written
    down.

    A QUANTILE truncates. Taking the lowest fifth by value leaves a sample cut off from above, and
    the identity the channel count rests on holds for a whole distribution, not a lower tail: on a
    Rayleigh truncated near zero the density goes as x, the fourth-to-second moment ratio is exactly
    4/3, and the identity reads three channels where the truth is one. Measured over 336 series,
    that put the median channel count at 1.86 and made the dark estimator abstain on half of them.

    OTSU is a different thing from a valley. It maximizes BETWEEN-CLASS variance, which sits at the
    valley only when the two modes carry comparable mass and spread. Here the background is a narrow
    spike and the tissue is broad, so Otsu lands far above the valley and drags tissue into the
    quiet population -- whose spread is then tissue variation, not noise. Measured over the same 336
    series, that drove the median dark sigma from 4.2 to 87.3, a twentyfold overread.

    A valley is a local minimum, so it is found as one: the histogram is smoothed by a moving
    average, the first peak located, and the first bin after it where the counts stop falling is
    taken. That is parameter-free in the sense that matters -- no level is chosen to separate
    anything -- and `smooth` and `bins` are the caller's, declared.

    NaN when nothing is finite, when every value is equal, or when the histogram falls away from
    its first peak without ever turning back up: a distribution with no valley has no split, and
    saying so is a reading.
    """
    if values.size == 0:
        return float("nan")
    low, high = float(np.min(values)), float(np.max(values))
    if not (np.isfinite(low) and np.isfinite(high)) or high <= low:
        return float("nan")
    counts, edges = np.histogram(values, bins=bins, range=(low, high))
    centres = (edges[:-1] + edges[1:]) / 2.0
    if smooth > 1:
        window = np.ones(smooth) / smooth
        counts = np.convolve(counts.astype(np.float64), window, mode="same")
    peak = int(np.argmax(counts))
    falling = False
    for i in range(peak + 1, counts.size):
        if counts[i] < counts[i - 1]:
            falling = True
        elif falling and counts[i] > counts[i - 1]:
            return float(centres[i - 1])
    return float("nan")


def quiet_population(values: np.ndarray, split: float) -> np.ndarray:
    """The values at or below `split`: the series' background, as a whole population.

    Taken by value and never from a designated corner — measured on this corpus, 181 of 336 series
    carry no laterality tag and 62 are over 20% zeros, so a corner is not reliably air. This is
    `instruments/background.py`'s move in the sibling build, made one reference for the whole
    series rather than a per-window floor.

    Unlike a quantile, this is not truncated by construction: where the background is its own mode,
    everything in that mode is kept and nothing of it is cut off, so its moments are the noise's.

    An empty input, or a split that is not a number, gives an empty array: a reading not made,
    never a reading of zero.
    """
    if values.size == 0 or not np.isfinite(split):
        return np.empty(0, dtype=np.float64)
    return values[values <= split]


def moment_ratio(values: np.ndarray) -> float:
    """E[M^4] / E[M^2]^2 of `values`.

    For a sum-of-squares magnitude over L channels the background obeys this ratio = (L + 1) / L,
    so it measures the channel count without knowing the signal. NaN when nothing was read or the
    second moment is zero: a ratio of zero over zero is not a reading.
    """
    if values.size == 0:
        return float("nan")
    second = float(np.mean(values**2))
    if second <= 0.0:
        return float("nan")
    fourth = float(np.mean(values**4))
    return fourth / (second * second)


def coil_count_robust(quiet: np.ndarray, grid: int = 512) -> float:
    """The channel count read from the background's QUARTILE RATIO, not its moments.

    The fourth moment is not robust and measurement showed it fails here. With 15 tissue values
    leaking into 120,000 background ones, the fourth-to-second moment ratio went to 7.19 -- far
    outside the identity's (1, 2] -- while the second moment still gave sigma to 1.4%. A handful of
    outliers destroys a fourth moment; it barely moves a quartile.

    A magnitude with no signal is sigma times a chi variate on 2L degrees of freedom, so sigma
    cancels in q75/q25 and the ratio depends on L alone. It falls as L rises, so it inverts. The
    curve is derived from the chi distribution, never fitted.

    NaN when the sample is too small to hold quartiles, or when the ratio lies outside what any
    L >= 1 can produce.
    """
    if quiet.size < 64:
        return float("nan")
    q25, q75 = (float(q) for q in np.quantile(quiet, (0.25, 0.75)))
    if not (np.isfinite(q25) and np.isfinite(q75)) or q25 <= 0.0:
        return float("nan")
    observed = q75 / q25
    counts = np.linspace(1.0, 64.0, grid)
    curve = np.sqrt(chi2.ppf(0.75, 2.0 * counts) / chi2.ppf(0.25, 2.0 * counts))
    # One channel is the floor: a magnitude cannot be built from fewer. The ratio at L = 1 is
    # 2.195, and a true one-channel sample scatters to BOTH sides of it, so a reading above it is
    # one channel observed with sampling scatter -- it clamps, it does not refuse. Refusing there
    # would abstain on about half of all genuinely single-channel series.
    if observed >= curve[0]:
        return 1.0
    if observed < curve[-1]:
        return float("nan")
    # the curve falls with L, so flip both for a rising interpolation
    return float(np.interp(-observed, -curve, counts))


def coil_count(ratio: float) -> float:
    """The channel count L implied by a background moment `ratio`, from (L + 1) / L = ratio.

    NaN outside (1, 2], where the identity implies L outside [1, inf): L = 1 (one channel, Rayleigh)
    gives a ratio of exactly 2, and the ratio falls toward 1 as L grows. `codes.coil_code` reads the
    same bound and names it.
    """
    if not np.isfinite(ratio) or ratio <= 1.0 or ratio > 2.0:
        return float("nan")
    return 1.0 / (ratio - 1.0)


def dark_sigma(quiet: np.ndarray, coils: float) -> float:
    """The per-channel sigma_g read from the quiet population, in the series' own values.

    For a noncentral-chi magnitude over L channels with no signal, E[M^2] = 2 * L * sigma_g^2
    exactly, so sigma_g is the root of the second moment over twice the channel count. At L = 1
    this is the Rayleigh maximum-likelihood estimator.

    NaN when nothing was read, when `coils` is not a positive number, or when the second moment is
    zero -- a masked background reads exactly zero, and zero is not a sigma.
    """
    if quiet.size == 0 or not np.isfinite(coils) or coils <= 0.0:
        return float("nan")
    second = float(np.mean(quiet**2))
    if second <= 0.0:
        return float("nan")
    return float(np.sqrt(second / (2.0 * coils)))


def pseudo_residuals(plane: np.ndarray, lag: int) -> np.ndarray:
    """Each interior place of `plane` minus the mean of its four neighbours at `lag`, scaled to one
    sigma.

    The scale is sqrt(4/5), derived from the neighbour count: a centre minus the mean of four
    independent neighbours has variance sigma^2 * (1 + 1/4). The lag must reach beyond the noise's
    correlation length, or the neighbours are not independent and the residual under-reads sigma.
    Zero-filled reconstructions correlate neighbouring places, so the lag is the caller's to set
    from a measured autocorrelation, never assumed to be 1.

    Returns an empty array when `plane` is not two-dimensional, when `lag` is not positive, or when
    the plane is too small to hold one interior place at that lag.
    """
    values = np.asarray(plane, dtype=np.float64)
    if values.ndim != 2 or lag <= 0:
        return np.empty((0, 0), dtype=np.float64)
    rows, columns = values.shape
    if rows <= 2 * lag or columns <= 2 * lag:
        return np.empty((0, 0), dtype=np.float64)
    centre = values[lag:-lag, lag:-lag]
    neighbours = (
        values[: -2 * lag, lag:-lag]
        + values[2 * lag :, lag:-lag]
        + values[lag:-lag, : -2 * lag]
        + values[lag:-lag, 2 * lag :]
    ) / 4.0
    return (centre - neighbours) * FOUR_NEIGHBOUR_SCALE


def bright_sigma(
    plane: np.ndarray,
    lag: int,
    floor: float,
    block: int = 16,
    quantile: float = 0.1,
) -> tuple[float, int]:
    """The noise FLOOR among local blocks of pseudo-residuals, where the tissue stands above `floor`.

    The second, independent estimator. It never reads the background, so it survives a
    vendor-masked one -- which 62 of this corpus's 336 series have.

    It reads a LOW QUANTILE of the blocks' spreads, not the spread of all of them, and that is the
    correction to a measured failure. A pseudo-residual assumes the four neighbours are independent
    samples of one level. In a real knee they are not: they sit on tissue with edges and texture, so
    the residual carries ANATOMY as well as noise, and a single spread over every bright residual is
    dominated by the anatomy. Measured over 336 series, that read a median of 5.5 times the dark
    estimator and up to 64 times.

    Among many small blocks, the quiet ones hold almost no structure, so the low end of their
    spreads is the noise and the high end is the anatomy. Taking the low quantile reads the floor.
    `quantile` and `block` are the caller's bars, never constants inside the reading.

    Returns the sigma and the count of blocks it was read from. (NaN, 0) when no block holds enough
    tissue above the floor.
    """
    values = np.asarray(plane, dtype=np.float64)
    residuals = pseudo_residuals(values, lag)
    if residuals.size == 0 or not np.isfinite(floor) or block <= 1:
        return float("nan"), 0
    if not (0.0 < quantile <= 1.0):
        return float("nan"), 0
    centre = values[lag:-lag, lag:-lag]
    rows, columns = residuals.shape
    spreads: list[float] = []
    for top in range(0, rows - block + 1, block):
        for left in range(0, columns - block + 1, block):
            tile = residuals[top : top + block, left : left + block]
            on_tissue = centre[top : top + block, left : left + block] >= floor
            kept = tile[np.isfinite(tile) & on_tissue]
            # half the block must be tissue, or the reading is of an edge rather than a region
            if kept.size < block * block // 2:
                continue
            deviation = float(np.median(np.abs(kept - np.median(kept))))
            if deviation > 0.0:
                spreads.append(deviation * MAD_TO_SIGMA)
    if not spreads:
        return float("nan"), 0
    read = float(np.quantile(np.array(spreads), quantile))
    return read / floor_bias(block * block, quantile), len(spreads)


def floor_bias(samples: int, quantile: float) -> float:
    """How far below sigma the `quantile`-th of many block spreads sits ON PURE NOISE.

    Taking a LOW quantile rejects structure, but it also under-reads the noise, because the spreads
    scatter even with nothing but noise present. That bias is derived, not fitted. A MAD-based
    sigma over n samples has an asymptotic spread of sigma / sqrt(0.74 n) -- 0.74 being the MAD's
    efficiency against a normal -- so the q-th quantile of many such estimates sits at

        1 + z(q) / sqrt(0.74 n)

    times sigma, with z the standard normal quantile. Measured against simulation at a true sigma
    of 6: predicted 0.814 / 0.907 / 0.953 / 0.977 for blocks of 8 / 16 / 32 / 64, against 0.799 /
    0.899 / 0.945 / 0.971 observed. The formula runs 1-2% high and converges as the block grows,
    because residuals in neighbouring places share neighbours and so are not quite independent.
    That residual is stated rather than tuned away.

    1.0 (no correction) when the sample or the quantile is not usable, so a bad argument never
    scales a reading.
    """
    if samples <= 1 or not (0.0 < quantile < 1.0):
        return 1.0
    factor = 1.0 + float(norm.ppf(quantile)) / np.sqrt(0.74 * samples)
    return float(factor) if factor > 0.1 else 1.0


def signal_squared(values: np.ndarray, sigma: float, coils: float) -> np.ndarray:
    """The underlying signal's square, A^2 = M^2 - 2 * L * sigma_g^2, unbiased.

    A magnitude reading is biased upward by the noise, by up to 1.25 sigma_g at the dark end, so M^2
    is never the signal's square. This identity is exact for a noncentral-chi magnitude. The result
    may be negative where the true signal is near zero, and it is returned as measured: clipping it
    would reintroduce the bias it removes.

    All-NaN when `sigma` or `coils` is not a positive number.
    """
    array = np.asarray(values, dtype=np.float64)
    if not np.isfinite(sigma) or sigma <= 0.0 or not np.isfinite(coils) or coils <= 0.0:
        return np.full(array.shape, float("nan"))
    return array**2 - 2.0 * coils * sigma * sigma
