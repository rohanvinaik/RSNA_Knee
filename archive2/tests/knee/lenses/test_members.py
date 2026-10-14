"""Two members read one place: what they said is kept, and nothing here resolves it."""

import pytest

from knee.lenses.digits import DIGIT_CODES, READ_CODES
from knee.lenses.members import READ_STANDINGS, STANDING_CODES, standing_code

SILENCES = tuple(code for code in DIGIT_CODES if code not in READ_CODES)


# --- positive: what it must do -------------------------------------------------------------


@pytest.mark.parametrize("reading", READ_CODES)
def test_two_members_reading_the_same_thing_concur(reading) -> None:
    assert standing_code(reading, reading) == "concur"


@pytest.mark.parametrize("first", READ_CODES)
@pytest.mark.parametrize("second", READ_CODES)
def test_two_members_reading_different_things_dissent(first, second) -> None:
    expected = "concur" if first == second else "dissent"
    assert standing_code(first, second) == expected


@pytest.mark.parametrize("silence", SILENCES)
@pytest.mark.parametrize("reading", READ_CODES)
def test_one_member_reading_is_named_by_which_member_read(silence, reading) -> None:
    assert standing_code(reading, silence) == "first_only"
    assert standing_code(silence, reading) == "second_only"


@pytest.mark.parametrize("first", SILENCES)
@pytest.mark.parametrize("second", SILENCES)
def test_two_silent_members_are_neither_read_whatever_their_silences(
    first, second
) -> None:
    assert standing_code(first, second) == "neither_read"


def test_a_code_outside_the_digit_vocabulary_is_an_unreadable_argument() -> None:
    assert standing_code("resolved", "at") == "invalid_measurement"
    assert standing_code("at", "") == "invalid_measurement"
    assert standing_code("ABOVE", "above") == "invalid_measurement"


def test_a_dissent_counts_as_a_reading_just_as_a_concurrence_does() -> None:
    """Disagreement is information, so it is never filed with the silences."""
    assert set(READ_STANDINGS) == {"concur", "dissent", "first_only", "second_only"}


# --- negative: what it must NEVER do -------------------------------------------------------


def test_the_vocabulary_offers_no_way_to_say_a_disagreement_was_settled() -> None:
    """Resolution is the founder's. A code meaning it would let a stage take that from him."""
    for forbidden in ("resolved", "preferred", "corrected", "combined", "agreed_value"):
        assert forbidden not in STANDING_CODES


@pytest.mark.parametrize("first", READ_CODES)
@pytest.mark.parametrize("second", READ_CODES)
def test_differing_readings_are_never_reported_as_concurrence(first, second) -> None:
    if first != second:
        assert standing_code(first, second) != "concur"


@pytest.mark.parametrize("silence", SILENCES)
@pytest.mark.parametrize("reading", READ_CODES)
def test_a_silent_member_is_never_filled_from_the_member_that_read(
    silence, reading
) -> None:
    """The forbidden move is a DEFAULT: project law 3, and the reason this is two members."""
    assert standing_code(reading, silence) not in ("concur", "dissent")
    assert standing_code(silence, reading) not in ("concur", "dissent")


@pytest.mark.parametrize("first", SILENCES)
@pytest.mark.parametrize("second", SILENCES)
def test_two_silences_never_become_a_reading(first, second) -> None:
    assert standing_code(first, second) not in READ_STANDINGS


def test_an_unreadable_argument_is_never_named_as_a_silence_about_the_knee() -> None:
    assert standing_code("resolved", "resolved") != "neither_read"
    assert standing_code("resolved", "resolved") not in READ_STANDINGS
