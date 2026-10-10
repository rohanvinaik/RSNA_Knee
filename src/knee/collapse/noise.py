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


def quiet_population(values: np.ndarray, share: float) -> np.ndarray:
    """The lowest `share` of `values`, the series' quiet population.

    Taken wherever it lies, never from a designated corner: measured on this corpus, 181 of 336
    series carry no laterality tag and 62 are over 20% zeros, so a corner is not reliably air. This
    is `instruments/background.py`'s move in the sibling build, where the noise is read as the
    spread of the below-level voxels, made one reference for the whole series rather than a
    per-window floor.

    `share` in (0, 1]. An empty input, or a share outside that range, gives an empty array: a
    reading not made, never a reading of zero.
    """
    if values.size == 0 or not (0.0 < share <= 1.0):
        return np.empty(0, dtype=np.float64)
    count = max(1, int(values.size * share))
    return np.sort(values)[:count]


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
        return np.empty(0, dtype=np.float64)
    rows, columns = values.shape
    if rows <= 2 * lag or columns <= 2 * lag:
        return np.empty(0, dtype=np.float64)
    centre = values[lag:-lag, lag:-lag]
    neighbours = (
        values[: -2 * lag, lag:-lag]
        + values[2 * lag :, lag:-lag]
        + values[lag:-lag, : -2 * lag]
        + values[lag:-lag, 2 * lag :]
    ) / 4.0
    return ((centre - neighbours) * FOUR_NEIGHBOUR_SCALE).ravel()


def bright_sigma(plane: np.ndarray, lag: int, floor: float) -> tuple[float, int]:
    """The sigma read from pseudo-residuals where the centre stands at or above `floor`.

    This is the second, independent estimator. It never reads the background, so it survives a
    vendor-masked one -- which 62 of this corpus's 336 series have. `floor` is supplied by the
    caller from the dark reading, so this function stays pure and the two estimators stay
    independent of each other's assumptions.

    Returns the sigma and the count of residuals it was read from, so the caller can weigh its
    sampling error. (NaN, 0) when no interior place stands at or above the floor.
    """
    values = np.asarray(plane, dtype=np.float64)
    residuals = pseudo_residuals(values, lag)
    if residuals.size == 0 or not np.isfinite(floor):
        return float("nan"), 0
    centre = values[lag:-lag, lag:-lag].ravel()
    kept = residuals[np.isfinite(centre) & (centre >= floor) & np.isfinite(residuals)]
    if kept.size == 0:
        return float("nan"), 0
    deviation = float(np.median(np.abs(kept - np.median(kept))))
    if deviation <= 0.0:
        return float("nan"), int(kept.size)
    return deviation * MAD_TO_SIGMA, int(kept.size)


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
