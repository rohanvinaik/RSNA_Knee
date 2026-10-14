"""Intent tests for the depth collapse's pure decision (knee.collapse.depth.chosen_slice), written
from the contract: a lens stands at the slice where its cheap reading is largest; an exact tie
takes the middle of the tied slices; silence is never a slice; too few readings is a named
abstention, never a guess; a refusal outranks every silence; the thesis's "not every slice"."""

import math

from knee.collapse.depth import CHOICE_CODES, chosen_slice

NAN = math.nan


def test_a_single_peak_is_chosen() -> None:
    assert chosen_slice((0.1, 0.4, 0.9, 0.3), 1) == (2, "chosen")


def test_the_peak_is_the_largest_reading_not_the_last_or_the_first() -> None:
    assert chosen_slice((0.9, 0.1, 0.2), 1) == (0, "chosen")
    assert chosen_slice((0.1, 0.2, 0.9), 1) == (2, "chosen")


def test_an_exact_tie_takes_the_middle_of_the_tied_run_and_says_so() -> None:
    assert chosen_slice((0.2, 0.5, 0.5, 0.5, 0.1), 1) == (2, "tie_middle")


def test_an_even_tie_takes_the_lower_of_the_two_middles() -> None:
    assert chosen_slice((0.5, 0.5, 0.5, 0.5), 1) == (1, "tie_middle")
    assert chosen_slice((0.5, 0.5), 1) == (0, "tie_middle")


def test_tied_slices_need_not_be_contiguous_and_the_middle_is_still_the_middle() -> (
    None
):
    assert chosen_slice((0.5, 0.1, 0.5, 0.1, 0.5), 1) == (2, "tie_middle")


def test_a_near_tie_is_not_a_tie() -> None:
    assert chosen_slice((0.5, 0.5000001), 1) == (1, "chosen")


def test_a_silent_slice_is_never_chosen_even_when_the_rest_are_lower() -> None:
    assert chosen_slice((NAN, 0.1, 0.2), 1) == (2, "chosen")
    assert chosen_slice((0.3, NAN, NAN), 1) == (0, "chosen")


def test_all_silent_is_an_abstention_not_a_slice() -> None:
    assert chosen_slice((NAN, NAN, NAN), 1) == (None, "all_silent")
    assert chosen_slice((), 0) == (None, "all_silent")


def test_too_few_readings_abstains_by_name_never_guesses() -> None:
    assert chosen_slice((0.1, NAN, 0.9, NAN), 3) == (None, "too_few_valid")


def test_the_bar_counts_finite_readings_not_slices() -> None:
    assert chosen_slice((0.1, 0.9, 0.2), 3) == (1, "chosen")
    assert chosen_slice((0.1, 0.9, NAN), 3) == (None, "too_few_valid")


def test_a_bar_of_zero_or_one_lets_a_lone_reading_stand() -> None:
    assert chosen_slice((NAN, 0.7, NAN), 0) == (1, "chosen")
    assert chosen_slice((NAN, 0.7, NAN), 1) == (1, "chosen")


def test_a_bar_that_is_not_a_count_is_refused() -> None:
    assert chosen_slice((0.1, 0.9), -1) == (None, "invalid_measurement")
    assert chosen_slice((0.1, 0.9), True) == (None, "invalid_measurement")
    assert chosen_slice((0.1, 0.9), 2.0) == (None, "invalid_measurement")  # type: ignore[arg-type]


def test_a_reading_that_is_not_a_number_is_refused() -> None:
    assert chosen_slice((0.1, "0.9"), 1) == (None, "invalid_measurement")  # type: ignore[arg-type]
    assert chosen_slice((0.1, True), 1) == (None, "invalid_measurement")
    assert chosen_slice("0.9", 1) == (None, "invalid_measurement")  # type: ignore[arg-type]
    assert chosen_slice(None, 1) == (None, "invalid_measurement")  # type: ignore[arg-type]


def test_the_refusal_outranks_the_silences() -> None:
    assert chosen_slice((NAN, NAN), -1) == (None, "invalid_measurement")


def test_an_index_rides_only_with_chosen_or_tie_middle() -> None:
    for readings, bar in (
        ((0.1, 0.9), 1),
        ((0.5, 0.5), 1),
        ((NAN, NAN), 1),
        ((0.1, NAN), 2),
        ((0.1, 0.9), -1),
    ):
        index, code = chosen_slice(readings, bar)
        assert code in CHOICE_CODES
        assert (index is None) == (code not in ("chosen", "tie_middle"))
        if index is not None:
            assert 0 <= index < len(readings)
