"""Intent tests for the boundary census: both signs of Detective's two-sign discipline.

A generated suite characterises what the code does; these state what it is FOR, so a change that
silently reverses a design decision fails here rather than passing a regenerated suite.

EVERY TEST CALLS THE TARGET DIRECTLY. Detective routes tests to a function by STATIC path, so a
local helper wrapping the call makes the test invisible to the tracer (measured on this project
2026-10-11: 9 of 13 tests routed through a helper, and Detective traced 4).
"""

import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from knee.objects.boundaries import (
    PAIR_CODE_VALUES,
    PAIR_CODES,
    boundary_census,
    carries_prominence,
    pair_code,
)

# ---------------------------------------------------------------------------------------------
# THE POSITIVE SIGN: what `pair_code` must DO.
# ---------------------------------------------------------------------------------------------


def test_every_outcome_is_a_named_code() -> None:
    assert len(set(PAIR_CODES)) == len(PAIR_CODES)
    assert pair_code(10, 5.0, 1.0, 1) in PAIR_CODES


def test_a_pair_that_touches_and_stands_above_its_valley_is_read() -> None:
    """The quantity SS9.1 asks for: a centre standing above its valley."""
    assert pair_code(10, 5.0, 1.0, 1) == "read"
    assert carries_prominence("read")


def test_two_territories_that_never_touch_are_silent_not_zero() -> None:
    """A pair with no divide has no relief to report. Silence, never a zero prominence."""
    assert pair_code(0, 5.0, 1.0, 1) == "no_divide"
    assert not carries_prominence(pair_code(0, 5.0, 1.0, 1))


def test_touching_too_little_is_a_different_fact_from_never_touching() -> None:
    """Different remedies, so different codes (law 3): one needs a divide, one needs more of it."""
    assert pair_code(0, 5.0, 1.0, 10) == "no_divide"
    assert pair_code(3, 5.0, 1.0, 10) == "too_few_sites"


def test_a_centre_below_its_own_pass_is_named_and_never_clamped() -> None:
    """A watershed basin cannot do this, so the code names a wiring fault instead of hiding it."""
    assert pair_code(10, 1.0, 5.0, 1) == "peak_below_saddle"
    assert not carries_prominence(pair_code(10, 1.0, 5.0, 1))


def test_a_height_that_was_not_read_is_silence_about_the_relief() -> None:
    assert pair_code(10, math.nan, 1.0, 1) == "unreadable_relief"
    assert pair_code(10, 5.0, math.nan, 1) == "unreadable_relief"
    assert pair_code(10, math.inf, 1.0, 1) == "unreadable_relief"


def test_arguments_that_cannot_be_a_measurement_are_refused() -> None:
    assert pair_code(-1, 5.0, 1.0, 1) == "invalid_measurement"
    assert pair_code(10, 5.0, 1.0, -1) == "invalid_measurement"
    assert pair_code(10, -1.0, 1.0, 1) == "invalid_measurement"
    assert pair_code(10, 5.0, -1.0, 1) == "invalid_measurement"


def test_a_pair_is_read_before_its_heights() -> None:
    """Two territories that never touch have no relief, so the absent divide outranks a bad height."""
    assert pair_code(0, math.nan, math.nan, 1) == "no_divide"


def test_an_invalid_argument_outranks_every_other_outcome() -> None:
    assert pair_code(-1, math.nan, math.nan, 1) == "invalid_measurement"


def test_carries_prominence_names_exactly_the_read_code() -> None:
    for name in PAIR_CODES:
        assert carries_prominence(name) == (name == "read")


# ---------------------------------------------------------------------------------------------
# THE NEGATIVE SIGN: what it must NEVER do.
# ---------------------------------------------------------------------------------------------


def test_a_single_adjacency_must_not_be_refused_when_one_was_asked_for() -> None:
    """MUST-NOT: refuse a legitimate configuration.

    `minimum_sites` is a recorded argument; a caller declaring 1 means one adjacency suffices, and
    a guard that crept to `sites < 2` would silence every thin divide without saying so.
    """
    assert pair_code(1, 5.0, 1.0, 1) == "read"


def test_a_floor_of_zero_must_admit_any_pair_that_touches_at_all() -> None:
    """MUST-NOT: impose a floor the caller did not declare."""
    assert pair_code(1, 5.0, 1.0, 0) == "read"
    assert pair_code(0, 5.0, 1.0, 0) == "no_divide"


def test_a_pass_at_the_floor_must_not_be_refused() -> None:
    """MUST-NOT: treat a legitimate measurement as impossible.

    A divide can run where the distance field is 0 -- two territories meeting at a constraint --
    and a saddle of exactly 0 is a reading, not a fault.
    """
    assert pair_code(10, 5.0, 0.0, 1) == "read"
    assert pair_code(10, 0.0, 0.0, 1) == "read"


def test_a_centre_exactly_at_its_pass_must_read_rather_than_fault() -> None:
    """MUST-NOT: put the boundary on the wrong side.

    Standing level with the pass is prominence zero, which is a reading. Only standing BELOW it is
    the impossible case, so the boundary belongs to `read`.
    """
    assert pair_code(10, 2.5, 2.5, 1) == "read"
    assert pair_code(10, 2.5 - 1e-9, 2.5, 1) == "peak_below_saddle"


def test_a_slightly_negative_height_must_never_be_accepted() -> None:
    """MUST-NOT: treat an impossible distance as a measurement.

    A distance from a constraint is a magnitude, so a negative one cannot have been measured. Both
    surviving mutants of the first converge crept this guard from `< 0.0` to `< -0.1`, which admits
    a small negative and then reports it as `peak_below_saddle` -- a relief fault -- when the true
    fact is that the argument could not be a measurement at all. Two different remedies, so the
    distinction must hold at the boundary and not merely near it.
    """
    assert pair_code(10, -0.05, 1.0, 1) == "invalid_measurement"
    assert pair_code(10, 1.0, -0.05, 1) == "invalid_measurement"
    assert pair_code(10, -1e-9, 1.0, 1) == "invalid_measurement"
    assert pair_code(10, 1.0, -1e-9, 1) == "invalid_measurement"


def test_a_prominence_is_never_invented_for_a_pair_that_was_not_read() -> None:
    """MUST-NOT: let an unread pair contribute to any total."""
    for code in PAIR_CODES:
        if code != "read":
            assert not carries_prominence(code)


# ---------------------------------------------------------------------------------------------
# The census itself: a measurement that assigns no anatomy.
# ---------------------------------------------------------------------------------------------


def test_two_touching_territories_report_their_pass_and_both_heights() -> None:
    labels = np.array([[1, 1, 2, 2]], dtype=np.int32)
    distance = np.array([[3.0, 1.0, 2.0, 4.0]])
    census = boundary_census(
        labels, distance, np.zeros(0, np.int32), np.zeros(0, np.uint8)
    )
    assert list(census.labels) == [1, 2]
    assert list(census.peak_mm) == [3.0, 4.0]
    assert census.pair_labels.tolist() == [[1, 2]]
    assert census.pair_sites.tolist() == [1]
    # crossing costs the LOWER of the two pixels, so the pass is 1.0, not 2.0
    assert census.pair_saddle_mm.tolist() == [1.0]
    assert census.pair_codes.tolist() == [PAIR_CODE_VALUES["read"]]
    assert census.prominences_mm().tolist() == [[2.0, 3.0]]


def test_territories_that_never_touch_make_no_pair() -> None:
    labels = np.array([[1, 0, 2]], dtype=np.int32)
    distance = np.array([[3.0, 0.0, 4.0]])
    census = boundary_census(
        labels, distance, np.zeros(0, np.int32), np.zeros(0, np.uint8)
    )
    assert len(census.pair_labels) == 0


def test_an_unread_pair_has_a_silent_prominence_and_never_a_zero() -> None:
    labels = np.array([[1, 1, 2, 2]], dtype=np.int32)
    distance = np.array([[3.0, 1.0, 2.0, 4.0]])
    census = boundary_census(
        labels, distance, np.zeros(0, np.int32), np.zeros(0, np.uint8), minimum_sites=5
    )
    assert census.pair_codes.tolist() == [PAIR_CODE_VALUES["too_few_sites"]]
    assert np.isnan(census.prominences_mm()).all()


def test_edges_are_counted_per_territory_by_what_lies_across_them() -> None:
    labels = np.array([[1, 2]], dtype=np.int32)
    distance = np.array([[1.0, 1.0]])
    regions = np.array([1, 1, 2], dtype=np.int32)
    kinds = np.array([1, 2, 4], dtype=np.uint8)  # low_signal, peer_territory, frame
    census = boundary_census(labels, distance, regions, kinds)
    assert census.edges_by_kind[0].tolist() == [1, 1, 0, 0, 0]
    assert census.edges_by_kind[1].tolist() == [0, 0, 0, 1, 0]


def test_a_plane_with_no_territory_measures_nothing_and_refuses_nothing() -> None:
    labels = np.zeros((3, 3), dtype=np.int32)
    distance = np.zeros((3, 3))
    census = boundary_census(
        labels, distance, np.zeros(0, np.int32), np.zeros(0, np.uint8)
    )
    assert len(census.labels) == 0
    assert len(census.pair_labels) == 0


def test_the_census_owns_its_output_and_never_hands_back_writable_arrays() -> None:
    labels = np.array([[1, 2]], dtype=np.int32)
    census = boundary_census(
        labels, np.array([[1.0, 2.0]]), np.zeros(0, np.int32), np.zeros(0, np.uint8)
    )
    for array in (
        census.labels,
        census.peak_mm,
        census.edges_by_kind,
        census.pair_saddle_mm,
    ):
        assert not array.flags.writeable


def test_disagreeing_shapes_are_refused_rather_than_broadcast() -> None:
    with pytest.raises(ValueError):
        boundary_census(
            np.zeros((2, 2), np.int32),
            np.zeros((3, 3)),
            np.zeros(0, np.int32),
            np.zeros(0, np.uint8),
        )


# ---------------------------------------------------------------------------------------------
# A law of the abstraction, as a property (code-verification.md: Hypothesis for a law).
# ---------------------------------------------------------------------------------------------


@settings(max_examples=200, deadline=None)
@given(
    sites=st.integers(min_value=0, max_value=1000),
    peak=st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False),
    saddle=st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False),
    floor=st.integers(min_value=0, max_value=1000),
)
def test_a_read_pair_always_has_a_prominence_at_or_above_zero(
    sites: int, peak: float, saddle: float, floor: int
) -> None:
    """The law: `read` is returned only where the prominence it licenses is not negative."""
    if pair_code(sites, peak, saddle, floor) == "read":
        assert peak - saddle >= 0.0
