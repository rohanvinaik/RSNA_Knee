"""Intent tests for the ternary digit: the POSITIVE sign of Detective's two-sign discipline.

A generated suite characterises what the function does; these state what it is FOR, so a change that
silently reverses a design decision fails here rather than passing a regenerated suite. The negative
sign -- what the function must NOT do -- is recorded as a FENCE against a surviving mutant, which
blocks COMPLETE until the suite enforces it.

EVERY TEST CALLS `digit_code` DIRECTLY. Detective routes tests to a function by STATIC path, so a
local helper that wraps the call makes the test invisible to the tracer: measured 2026-10-11, 9 of 13
tests here were routed through a `code()` helper and Detective traced only the 4 that called the
function by name, reporting two covered lines as uncovered.
"""

import math

import pytest

from knee.lenses.digits import DIGIT_CODES, band_width, digit_code, is_read

# One flicker is one sigma by construction of the variance-stabilising transform.
FLICKER = 1.0


def test_every_outcome_is_a_named_code() -> None:
    assert len(set(DIGIT_CODES)) == len(DIGIT_CODES)
    assert digit_code(5.0, 0.0, FLICKER, 0.0, 1.0, 100, 10) in DIGIT_CODES


def test_a_reading_at_the_middle_is_a_reading_and_not_silence() -> None:
    """SS1.12: `at` is a reading at its middle. It must never be confused with nothing said."""
    assert digit_code(0.0, 0.0, FLICKER, 0.0, 1.0, 100, 10) == "at"
    assert is_read("at")


def test_an_unread_place_is_silence_and_never_a_negative() -> None:
    """The founder: "'Silence' is meaningful, not a default negative score"."""
    assert digit_code(math.nan, 0.0, FLICKER, 0.0, 1.0, 100, 10) == "place_unread"
    assert not is_read("place_unread")
    assert digit_code(math.nan, 0.0, FLICKER, 0.0, 1.0, 100, 10) != "at"
    assert digit_code(math.nan, 0.0, FLICKER, 0.0, 1.0, 100, 10) != "below"


def test_an_absent_witness_is_distinct_from_a_witness_too_small() -> None:
    """Different facts with different remedies, so they get different codes (law 3)."""
    assert digit_code(1.0, math.nan, FLICKER, 0.0, 1.0, 100, 10) == "no_witness"
    assert digit_code(1.0, 0.0, FLICKER, 0.0, 1.0, 0, 10) == "no_witness"
    assert digit_code(1.0, 0.0, FLICKER, 0.0, 1.0, 3, 10) == "witness_too_small"


def test_an_absent_witness_outranks_an_unread_place() -> None:
    """A place cannot be placed against a standard that is not there, so the witness is read first."""
    assert digit_code(math.nan, math.nan, FLICKER, 0.0, 1.0, 100, 10) == "no_witness"
    assert digit_code(math.nan, 0.0, FLICKER, 0.0, 1.0, 0, 10) == "no_witness"


def test_no_reading_is_returned_without_an_admissible_witness() -> None:
    """The post-condition in prose: a digit is only ever stated against a witness that qualifies."""
    for count in range(10):
        assert not is_read(digit_code(5.0, 0.0, FLICKER, 0.0, 1.0, count, 10))
    assert is_read(digit_code(5.0, 0.0, FLICKER, 0.0, 1.0, 10, 10))


def test_above_the_witness_reads_above() -> None:
    assert digit_code(5.0, 0.0, FLICKER, 0.0, 1.0, 100, 10) == "above"


def test_below_the_witness_reads_below() -> None:
    assert digit_code(-5.0, 0.0, FLICKER, 0.0, 1.0, 100, 10) == "below"


def test_the_witnesss_location_moves_the_verdict() -> None:
    """Naming the witness is the whole point: the same value reads differently against another."""
    assert digit_code(5.0, 0.0, FLICKER, 0.0, 1.0, 100, 10) == "above"
    assert digit_code(5.0, 10.0, FLICKER, 0.0, 1.0, 100, 10) == "below"


def test_the_band_carries_the_witnesss_spread_not_only_voxel_noise() -> None:
    """The correction both second readers reached on 2026-10-11.

    A place three flickers out is ABOVE a tight witness and AT a broad one. A band taking only the
    place's own noise would read a heterogeneous witness as if it were exact.
    """
    assert digit_code(3.0, 0.0, FLICKER, 0.0, 1.0, 100, 10) == "above"
    assert digit_code(3.0, 0.0, FLICKER, 10.0, 1.0, 100, 10) == "at"


def test_a_band_from_voxel_noise_alone_would_be_degenerate() -> None:
    """Why the correction mattered: at real SNR, `at` would be nearly empty."""
    assert band_width(FLICKER, 0.0, 1.0) == pytest.approx(1.0)
    assert band_width(FLICKER, 6.0, 1.0) > 6.0
    assert digit_code(2.0, 0.0, FLICKER, 0.0, 1.0, 100, 10) == "above"
    assert digit_code(2.0, 0.0, FLICKER, 6.0, 1.0, 100, 10) == "at"


def test_the_band_is_symmetric_and_k_scales_it() -> None:
    assert digit_code(4.0, 0.0, FLICKER, 0.0, 1.0, 100, 10) == "above"
    assert digit_code(-4.0, 0.0, FLICKER, 0.0, 1.0, 100, 10) == "below"
    assert digit_code(4.0, 0.0, FLICKER, 0.0, 5.0, 100, 10) == "at"
    assert digit_code(-4.0, 0.0, FLICKER, 0.0, 5.0, 100, 10) == "at"


def test_the_boundary_belongs_to_at_on_both_sides() -> None:
    """Exactly one band out is still indistinguishable from the witness, so it reads `at`."""
    band = band_width(FLICKER, 3.0, 2.0)
    assert digit_code(band, 0.0, FLICKER, 3.0, 2.0, 100, 10) == "at"
    assert digit_code(-band, 0.0, FLICKER, 3.0, 2.0, 100, 10) == "at"
    assert digit_code(band * 1.0001, 0.0, FLICKER, 3.0, 2.0, 100, 10) == "above"
    assert digit_code(-band * 1.0001, 0.0, FLICKER, 3.0, 2.0, 100, 10) == "below"


def test_arguments_that_cannot_be_a_measurement_are_refused() -> None:
    assert digit_code(1.0, 0.0, FLICKER, 0.0, 0.0, 100, 10) == "invalid_measurement"
    assert digit_code(1.0, 0.0, FLICKER, 0.0, -1.0, 100, 10) == "invalid_measurement"
    assert digit_code(1.0, 0.0, 0.0, 0.0, 1.0, 100, 10) == "invalid_measurement"
    assert digit_code(1.0, 0.0, -1.0, 0.0, 1.0, 100, 10) == "invalid_measurement"
    assert digit_code(1.0, 0.0, FLICKER, -1.0, 1.0, 100, 10) == "invalid_measurement"
    assert digit_code(1.0, 0.0, FLICKER, 0.0, 1.0, -1, 10) == "invalid_measurement"
    assert digit_code(1.0, 0.0, FLICKER, 0.0, 1.0, 100, -1) == "invalid_measurement"
    assert digit_code(1.0, 0.0, math.nan, 0.0, 1.0, 100, 10) == "invalid_measurement"
    assert (
        digit_code(1.0, 0.0, FLICKER, math.inf, 1.0, 100, 10) == "invalid_measurement"
    )
    assert (
        digit_code(1.0, 0.0, FLICKER, 0.0, math.nan, 100, 10) == "invalid_measurement"
    )


def test_an_invalid_argument_outranks_every_other_outcome() -> None:
    """A measurement that could not have been made is not a silence about the place or witness."""
    assert (
        digit_code(math.nan, 0.0, FLICKER, 0.0, -1.0, 100, 10) == "invalid_measurement"
    )
    assert digit_code(1.0, math.nan, FLICKER, 0.0, -1.0, 0, 10) == "invalid_measurement"


# ---------------------------------------------------------------------------------------------
# THE NEGATIVE SIGN: what the function must NEVER do.
#
# Each of these was a surviving mutant after the first converge -- a behaviour the suite permitted
# to change without failing. Detective offers two verdicts on a survivor: equivalent, or a FENCE,
# "an authored MUST-NOT ... the suite does not yet enforce". Where the must-not can be enforced
# outright, a test is strictly better than a fence, so these three enforce it.
# ---------------------------------------------------------------------------------------------


def test_a_small_but_positive_band_k_must_not_be_refused() -> None:
    """MUST-NOT: refuse a legitimate configuration.

    `band_k` is a recorded argument and any positive value is a legitimate choice -- a strict
    reading simply decides more often. A guard at `band_k <= 0.1` would silently refuse it.
    """
    assert digit_code(0.0, 0.0, FLICKER, 0.0, 0.05, 100, 10) == "at"
    assert digit_code(0.0, 0.0, FLICKER, 0.0, 1e-6, 100, 10) != "invalid_measurement"


def test_a_small_but_positive_place_sigma_must_not_be_refused() -> None:
    """MUST-NOT: refuse a real instrument.

    One flicker is one sigma by construction, but a caller may supply a place's own noise in other
    units, and a small positive sigma is a sharp instrument rather than an invalid one.
    """
    assert digit_code(0.0, 0.0, 0.05, 0.0, 1.0, 100, 10) != "invalid_measurement"
    assert digit_code(0.0, 0.0, 1e-6, 0.0, 1.0, 100, 10) != "invalid_measurement"


def test_a_negative_witness_spread_must_never_be_accepted() -> None:
    """MUST-NOT: treat an impossible spread as a measurement.

    A spread is a magnitude. A negative one cannot have been measured, and accepting it would feed
    `sqrt` a shrunken band and decide where it should refuse. A guard at `witness_spread < -0.1`
    would let small negatives through.
    """
    assert digit_code(1.0, 0.0, FLICKER, -0.05, 1.0, 100, 10) == "invalid_measurement"
    assert digit_code(1.0, 0.0, FLICKER, -1e-9, 1.0, 100, 10) == "invalid_measurement"


def test_is_read_names_exactly_the_three_readings() -> None:
    for name in DIGIT_CODES:
        assert is_read(name) == (name in ("below", "at", "above"))


def test_band_width_is_never_negative_and_grows_with_either_spread() -> None:
    assert band_width(FLICKER, 0.0, 1.0) >= 0.0
    assert band_width(2.0, 0.0, 1.0) > band_width(1.0, 0.0, 1.0)
    assert band_width(1.0, 2.0, 1.0) > band_width(1.0, 1.0, 1.0)
    assert band_width(1.0, 1.0, 2.0) > band_width(1.0, 1.0, 1.0)
