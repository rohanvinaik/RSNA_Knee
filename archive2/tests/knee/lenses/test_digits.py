"""Two-sign intent: a digit reads supplied edges; silence never becomes a middle.

Founder ruling in chapters/03-lenses/teachings.md and OpenSpec task 2.1 replace
the retired witness-band tests. Every test calls the decision directly for Detective.
"""

import math

import pytest

from knee.lenses.digits import DIGIT_CODES, digit_code, is_read


@pytest.mark.parametrize("value", [2.0, 3.0, 4.0])
def test_both_edges_and_the_interval_are_measured_middle(value) -> None:
    assert digit_code(value, 2.0, 4.0, 3, 3) == "at"


def test_outside_each_edge_has_its_own_direction() -> None:
    assert digit_code(1.0, 2.0, 4.0, 3, 3) == "below"
    assert digit_code(5.0, 2.0, 4.0, 3, 3) == "above"


def test_edges_move_the_reading_without_changing_the_place() -> None:
    assert digit_code(5.0, 2.0, 4.0, 3, 3) == "above"
    assert digit_code(5.0, 4.0, 6.0, 3, 3) == "at"
    assert digit_code(5.0, 6.0, 8.0, 3, 3) == "below"


def test_equal_edges_are_not_refused_or_widened() -> None:
    assert digit_code(2.0, 2.0, 2.0, 3, 3) == "at"
    assert digit_code(1.0, 2.0, 2.0, 3, 3) == "below"
    assert digit_code(3.0, 2.0, 2.0, 3, 3) == "above"


@pytest.mark.parametrize("unread", [None, math.nan, math.inf, -math.inf])
def test_unread_places_are_not_middle_or_negative(unread) -> None:
    assert digit_code(unread, 2.0, 4.0, 3, 3) == "place_unread"
    assert digit_code(unread, 2.0, 4.0, 3, 3) not in ("at", "below", "above")


@pytest.mark.parametrize("unread", [None, math.nan, math.inf, -math.inf])
def test_each_edge_is_required_before_any_digit_is_written(unread) -> None:
    assert digit_code(3.0, unread, 4.0, 3, 3) == "no_edges"
    assert digit_code(3.0, 2.0, unread, 3, 3) == "no_edges"
    assert digit_code(None, unread, 4.0, 3, 3) == "no_edges"


def test_empty_small_and_unread_population_cases_stay_distinct() -> None:
    assert digit_code(3.0, 2.0, 4.0, 0, 3) == "no_edges"
    assert digit_code(3.0, 2.0, 4.0, 2, 3) == "population_too_small"
    assert digit_code(None, 2.0, 4.0, 2, 3) == "population_too_small"
    assert digit_code(3.0, 2.0, 4.0, 3, 3) == "at"


def test_invalid_counts_and_reversed_edges_never_become_readings() -> None:
    assert digit_code(3.0, 2.0, 4.0, -1, 3) == "invalid_measurement"
    assert digit_code(3.0, 2.0, 4.0, 3, -1) == "invalid_measurement"
    assert digit_code(3.0, 4.0, 2.0, 3, 3) == "invalid_measurement"
    assert digit_code(None, 4.0, 2.0, 0, 3) == "invalid_measurement"
    assert digit_code(None, None, None, -1, 3) == "invalid_measurement"


def test_population_bar_is_an_argument_never_a_hidden_constant() -> None:
    assert digit_code(3.0, 2.0, 4.0, 2, 2) == "at"
    assert digit_code(3.0, 2.0, 4.0, 2, 3) == "population_too_small"
    assert digit_code(3.0, 2.0, 4.0, 1, 0) == "at"
    assert digit_code(3.0, 2.0, 4.0, 0, 0) == "no_edges"


def test_adjacent_floats_outside_edges_must_not_be_absorbed_by_a_band() -> None:
    assert digit_code(math.nextafter(2.0, -math.inf), 2.0, 4.0, 3, 3) == "below"
    assert digit_code(math.nextafter(4.0, math.inf), 2.0, 4.0, 3, 3) == "above"
    assert digit_code(0.05, 0.05, 0.05, 1, 1) == "at"


def test_is_read_includes_middle_and_excludes_every_silence() -> None:
    assert len(set(DIGIT_CODES)) == len(DIGIT_CODES)
    for code in (*DIGIT_CODES, "unknown"):
        assert is_read(code) == (code in ("below", "at", "above"))
