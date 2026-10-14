"""The shared absence vocabulary, both signs.

Every test calls `absence_code` and `is_silence` DIRECTLY by name. Detective routes tests to a
function by static path, so a call hidden behind a local helper is not a pin -- measured on this
project, where 9 of 13 intent tests went through a `code()` helper and Detective traced 4.

The negative sign is the half that is usually skipped: what the decision must NEVER do. Each of
those is a must-not the project would otherwise discover from a picture that looked plausible.
"""

from knee.absence import CODES, SILENCES, absence_code, is_silence

# --------------------------------------------------------------------------------------------
# Positive: what it must do.
# --------------------------------------------------------------------------------------------


def test_a_missing_construction_is_named_before_anything_about_the_input() -> None:
    """A stage whose unit is unbuilt reports that, with every input fact perfectly good."""
    assert absence_code(False, True, 7, True) == "construction_absent"


def test_a_predecessor_that_returned_nothing_is_named() -> None:
    assert absence_code(True, False, 0, False) == "predecessor_absent"


def test_a_record_that_was_read_and_held_nothing_is_named() -> None:
    assert absence_code(True, True, 0, False) == "predecessor_empty"


def test_a_record_with_items_whose_item_was_not_read_is_named() -> None:
    assert absence_code(True, True, 3, False) == "item_unread"


def test_a_reading_that_was_actually_made_is_present() -> None:
    assert absence_code(True, True, 3, True) == "present"


def test_a_count_below_zero_is_an_unreadable_argument() -> None:
    assert absence_code(True, True, -1, True) == "invalid_count"


def test_is_silence_answers_for_the_vocabulary_it_owns() -> None:
    for code in SILENCES:
        assert is_silence(code)
    assert not is_silence("present")
    assert not is_silence("invalid_count")


# --------------------------------------------------------------------------------------------
# Negative: what it must NEVER do.
# --------------------------------------------------------------------------------------------


def test_it_never_returns_a_code_outside_the_declared_vocabulary() -> None:
    """The whole point is one vocabulary; a code outside it composes with nothing."""
    for built in (True, False):
        for returned in (True, False):
            for count in (-2, -1, 0, 1, 5):
                for read in (True, False):
                    assert absence_code(built, returned, count, read) in CODES


def test_it_never_reports_present_when_any_silence_holds() -> None:
    """`present` asserts a reading was made. Saying it over a silence invents the reading."""
    assert absence_code(False, True, 3, True) != "present"
    assert absence_code(True, False, 3, True) != "present"
    assert absence_code(True, True, 0, True) != "present"
    assert absence_code(True, True, 3, False) != "present"


def test_it_never_blames_the_study_for_a_gap_in_the_build() -> None:
    """A missing construction must not surface as a missing predecessor: opposite remedies.

    One says "build the unit", the other says "this study has no such reading". If the ordering
    ever reverses, a stage nobody wrote would read as a corpus finding.
    """
    assert absence_code(False, False, 0, False) == "construction_absent"


def test_it_never_collapses_an_unreadable_count_into_an_empty_record() -> None:
    """Zero was read and held nothing; below zero could not be read. A caller's bug is not a finding."""
    assert absence_code(True, True, -1, False) != "predecessor_empty"
    assert absence_code(True, True, 0, False) != "invalid_count"


def test_it_never_collapses_an_empty_record_into_an_unread_item() -> None:
    """Nothing to read, versus something there that this pass did not read."""
    assert absence_code(True, True, 0, False) != "item_unread"
    assert absence_code(True, True, 2, False) != "predecessor_empty"


def test_is_silence_never_calls_a_reading_or_an_unreadable_argument_a_silence() -> None:
    """A stage routing on silence must not route `present` into the absence path."""
    assert not is_silence("present")
    assert not is_silence("invalid_count")
    assert not is_silence("")
    assert not is_silence("predecessor_absent_typo")
