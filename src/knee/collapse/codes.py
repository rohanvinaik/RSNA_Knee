"""The collapse's decisions: pure, total over their arguments, returning named codes.

Every bar a decision reads is an argument, never a constant inside it: under Law 4 a level is
written down before the run it judges, and it is the founder's to set.
"""

from __future__ import annotations

import math


def quiet_code(n_finite: int, n_zero: int, spread: float, min_count: int) -> str:
    """Whether the quiet population can carry a noise reading, as a named code (pure — pinned).

    The quiet population is the lowest share of a series' finite values, taken wherever it lies and
    never from a designated corner. Four different zeros, kept apart: "no_values" when nothing is
    finite; "too_few" when fewer than `min_count` are; "background_masked" when every one of them is
    exactly zero, which is a vendor-masked background and not a dark reading; "no_spread" when they
    are not all zero yet hold no spread at all. Otherwise "readable".

    A non-finite or negative `spread` is "no_spread": a spread that is not a number is not a
    reading.
    """
    if n_finite <= 0:
        return "no_values"
    if n_finite < min_count:
        return "too_few"
    if n_zero >= n_finite:
        return "background_masked"
    if not math.isfinite(spread) or spread <= 0.0:
        return "no_spread"
    return "readable"


def coil_code(moment_ratio: float, single_tolerance: float) -> str:
    """How many coil channels the background's fourth and second moments imply (pure — pinned).

    For a sum-of-squares magnitude over L channels the background obeys
    E[M^4] / E[M^2]^2 = (L + 1) / L, so L = 1 / (ratio - 1). L = 1 (Rayleigh, one channel) gives a
    ratio of exactly 2, and the ratio falls toward 1 as L grows. A ratio at or below 1, or above 2,
    implies L outside [1, inf) and is "implausible_ratio": a reading the identity cannot hold.

    "single" when L is within `single_tolerance` of 1, else "multi". A non-finite ratio is
    "unmeasurable".
    """
    if not math.isfinite(moment_ratio):
        return "unmeasurable"
    if moment_ratio <= 1.0 or moment_ratio > 2.0:
        return "implausible_ratio"
    coils = 1.0 / (moment_ratio - 1.0)
    if abs(coils - 1.0) <= single_tolerance:
        return "single"
    return "multi"


def concurrence_code(
    dark_sigma: float,
    bright_sigma: float,
    dark_n: int,
    bright_n: int,
    tolerance_errors: float,
) -> str:
    """Whether the two noise estimators concur, as a named code (pure — pinned).

    The dark estimator reads the quiet population; the bright one reads pseudo-residuals where the
    signal is strong. Their agreement within sampling error is the measurement that ONE stationary
    noise law holds over the series. Disagreement is a finding, never a reason to refit.

    The standard error of a spread estimated from n samples is sigma / sqrt(2n), and the two are
    independent, so the difference's standard error is the root of the sum of their squares.
    "concur" when the gap is within `tolerance_errors` of those, else "disagree".

    An estimator that did not read is an abstention, kept apart from a disagreement: a sigma that is
    not finite or not positive, or a count that is not positive, abstains. Hence "both_abstained",
    "dark_abstained" and "bright_abstained".
    """
    dark_ok = math.isfinite(dark_sigma) and dark_sigma > 0.0 and dark_n > 0
    bright_ok = math.isfinite(bright_sigma) and bright_sigma > 0.0 and bright_n > 0
    if not dark_ok and not bright_ok:
        return "both_abstained"
    if not dark_ok:
        return "dark_abstained"
    if not bright_ok:
        return "bright_abstained"
    dark_error = dark_sigma / math.sqrt(2.0 * dark_n)
    bright_error = bright_sigma / math.sqrt(2.0 * bright_n)
    combined = math.sqrt(dark_error * dark_error + bright_error * bright_error)
    if abs(dark_sigma - bright_sigma) <= tolerance_errors * combined:
        return "concur"
    return "disagree"


def storage_code(pixel_representation: int, n_negative: int) -> str:
    """How a series stores its values, as a named code (pure — pinned).

    DICOM's Pixel Representation is 0 for unsigned and 1 for signed two's complement. Measured on
    this corpus: 103 of 336 series declare signed storage while only 5 hold a negative value, so
    what is declared and what is held are two readings and both are kept. "unsigned_negative" is a
    file contradicting itself, carried rather than coerced. Any other declaration is
    "unknown_representation".
    """
    if pixel_representation == 0:
        return "unsigned_negative" if n_negative > 0 else "unsigned"
    if pixel_representation == 1:
        return "signed_negative" if n_negative > 0 else "signed_nonnegative"
    return "unknown_representation"


def normalization_code(image_type: tuple[str, ...]) -> str:
    """Whether the vendor flagged a normalization field on this series (pure — pinned).

    A vendor intensity normalization multiplies signal and noise together by a smooth field, so the
    noise law stops being one number for the series and becomes a field. DICOM's Image Type carries
    "NORM" where that was applied. Its absence is "not_flagged", never "plain": a header that does
    not say is not a header that denies. An empty Image Type is "unknown".
    """
    if not image_type:
        return "unknown"
    if "NORM" in image_type:
        return "normalized"
    return "not_flagged"
