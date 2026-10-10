"""The variance-stabilizing transform: after it, one unit is one sigma at any intensity.

The sibling build reads a difference in "flicker units" (cell_tracking
`instruments/support.py::flicker_units`), the closed-form integral of dv/sigma(v) for a photon
counter's sigma^2 = a + b*v. The structure is kept and the family is replaced: MR magnitude is
noncentral chi over the coil channels, Rician at one channel, so its spread is nearly flat in the
bright regime and SUB-additive at the dark end rather than growing with brightness.

There is no elementary closed form for the MR case, so the integral is taken once per series by
quadrature and kept as a table, which is what makes it cheap to apply. The transform is derived
from the measured noise law; nothing in it is fitted to a label.

HOW EXACT IT IS, measured rather than claimed. The integral stabilizes to first order (the delta
method), so it is exact only in the limit where the spread is small against the curvature of the
mean-variance curve. At one channel, measured on 400,000 draws at each level:

    signal      0      0.5sigma   1sigma   2sigma   3sigma   5sigma   10sigma   25sigma
    spread      0.886  0.922      0.995    1.063    1.031    1.002    1.001     0.999

So: within half a percent above 5 sigma, within about 7% through the transition band, and
**11% LOW at pure noise**, where the Rayleigh distribution is broad and skewed against its own
mean and the linearization is poorest. The deviation is systematic and bounded, never random.

What that means downstream: a difference read in the bright and middle regimes is on the scale it
claims. A null computed in air is NOT -- air reads about 0.886 of a unit, so an excursion rate
taken there must use the measured dark-end spread rather than assume one. That correction is the
air null's to carry, and it is recorded here rather than assumed away.

Every function here is a MEASUREMENT. Units: magnitudes are in the series' own stored values;
the transform's output is in sigmas. Arrays are float64.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.special import gammaln, hyp1f1

# How far above the noise the table is built, in units of the per-channel sigma. The transform is
# linear far above the floor, so beyond this the extension is exact rather than approximate.
TABLE_REACH_SIGMAS = 60.0

# Entries in a series' table. Enough that linear interpolation between neighbours is far below the
# quantization of the stored values it reads.
TABLE_ENTRIES = 4096


@dataclass(frozen=True, slots=True)
class Stabilizer:
    """One series' transform, tabulated.

    magnitude: (n,) float64, ascending, the expected magnitudes the table is built on, starting at
    the no-signal mean. units: (n,) float64, each magnitude in sigmas. floor_slope: the derivative
    at the no-signal end, which continues the transform linearly below the table. sigma, coils: the
    noise law the table was built from.
    """

    magnitude: np.ndarray
    units: np.ndarray
    floor_slope: float
    sigma: float
    coils: float


def magnitude_moments(
    signal: np.ndarray, sigma: float, coils: float
) -> tuple[np.ndarray, np.ndarray]:
    """The mean and variance of a noncentral-chi magnitude over `coils` channels.

    The second moment is exact: E[M^2] = A^2 + 2 * L * sigma^2. The first is
    E[M] = sigma * sqrt(2) * Gamma(L + 1/2) / Gamma(L) * 1F1(-1/2; L; -A^2 / (2 sigma^2)),
    and the variance is their difference.

    At one channel and no signal this gives the Rayleigh values: a mean of 1.2533 sigma and a
    variance of 0.4292 sigma^2. Far above the noise the variance approaches sigma^2, so the whole
    swing is about 2.3x -- much gentler than a photon counter's, and the reason the dark end is
    where the transform does its work.
    """
    amplitude = np.asarray(signal, dtype=np.float64)
    second = amplitude**2 + 2.0 * coils * sigma * sigma
    scale = np.sqrt(2.0) * np.exp(gammaln(coils + 0.5) - gammaln(coils))
    mean = sigma * scale * hyp1f1(-0.5, coils, -(amplitude**2) / (2.0 * sigma * sigma))
    return mean, second - mean**2


def stabilizer(sigma: float, coils: float) -> Stabilizer | None:
    """One series' variance-stabilizing table, from its measured noise law.

    The table is parameterized by the underlying signal, giving a curve of (expected magnitude,
    variance); the expected magnitude rises with the signal, so the variance is read as a function
    of it and integrated:

        f(m) = integral from the no-signal mean to m of dt / sqrt(variance at t)

    After it, a difference of one unit is one standard deviation at whatever intensity it was read.
    The table begins at the no-signal mean rather than at zero, because a magnitude with no signal
    still reads 1.2533 sigma on average at one channel; below that the transform continues
    linearly at the dark end's own slope, which is `flicker_units`' below-floor branch.

    None when the noise law is not a reading: a sigma or a channel count that is not finite or not
    positive. A table is never built on an abstention.
    """
    if not np.isfinite(sigma) or sigma <= 0.0:
        return None
    if not np.isfinite(coils) or coils < 1.0:
        return None
    amplitude = np.linspace(0.0, TABLE_REACH_SIGMAS * sigma, TABLE_ENTRIES)
    mean, variance = magnitude_moments(amplitude, sigma, coils)
    if not np.all(np.isfinite(variance)) or np.any(variance <= 0.0):
        return None
    slope = 1.0 / np.sqrt(variance)
    units = cumulative_trapezoid(slope, mean, initial=0.0)
    return Stabilizer(
        magnitude=mean,
        units=units,
        floor_slope=float(slope[0]),
        sigma=float(sigma),
        coils=float(coils),
    )


def to_units(values: np.ndarray, table: Stabilizer) -> np.ndarray:
    """`values`, in the series' own stored values, read in sigmas through `table`.

    Below the table's first magnitude the transform continues linearly at the dark end's slope, so
    a reading with no signal at all is still on the same scale -- which the air null needs. Above
    the table's reach it continues linearly at the bright end's slope, where the transform is
    already linear, so the extension is exact. Non-finite values stay non-finite: a reading that
    was never made is not transformed into one.
    """
    array = np.asarray(values, dtype=np.float64)
    low, high = table.magnitude[0], table.magnitude[-1]
    out = np.interp(array, table.magnitude, table.units)
    below = array < low
    if np.any(below):
        out = np.where(below, (array - low) * table.floor_slope, out)
    above = array > high
    if np.any(above):
        top_slope = (table.units[-1] - table.units[-2]) / (
            table.magnitude[-1] - table.magnitude[-2]
        )
        out = np.where(above, table.units[-1] + (array - high) * top_slope, out)
    return np.where(np.isfinite(array), out, np.nan)
