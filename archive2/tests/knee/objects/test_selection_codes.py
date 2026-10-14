"""Intent tests for the selection's pure decisions (knee.objects.selection) and the laterality
sign (knee.objects.laterality), written from the contracts: the two largest territories are the
big pair, the more superior first; a tie is said; the small object in front of the superior big
one, the small ringed one beside the inferior big one, and the axial's own two are selected by
facts alone; a missing witness abstains the sign; every refusal is named."""

import math

from knee.objects.laterality import SIGN_CODES, lateral_sign_code
from knee.objects.selection import (
    ANTERIOR_CODES,
    PAIR_CODES,
    WITNESS_CODES,
    anterior_small_code,
    axial_code,
    big_pair_code,
    lateral_witness_code,
)

# --- the big pair -------------------------------------------------------------------------


def test_the_two_largest_are_the_pair_and_the_more_superior_is_first() -> None:
    assert big_pair_code((120, 100, 5), (10.0, -40.0, 0.0), 8) == (0, 1, "selected")
    # The pair is returned superior first, whichever of the two is larger.
    assert big_pair_code((100, 120, 5), (-40.0, 10.0, 0.0), 8) == (1, 0, "selected")
    assert big_pair_code((100, 120, 5), (10.0, -40.0, 0.0), 8) == (0, 1, "selected")


def test_a_tie_in_count_is_broken_by_superior_position_and_said() -> None:
    assert big_pair_code((100, 100, 100), (10.0, -40.0, 5.0), 8) == (0, 2, "tie")


def test_a_tie_in_superior_position_is_said_and_takes_the_lower_index_first() -> None:
    assert big_pair_code((120, 100), (3.0, 3.0), 8) == (0, 1, "tie")


def test_one_candidate_only_is_named_and_the_pair_is_not_selected() -> None:
    assert big_pair_code((120, 2), (10.0, -40.0), 8) == (0, None, "one_big_only")


def test_no_candidate_is_none() -> None:
    assert big_pair_code((2, 3), (10.0, -40.0), 8) == (None, None, "none")
    assert big_pair_code((), (), 8) == (None, None, "none")


def test_the_pair_decision_refuses_what_it_cannot_read() -> None:
    assert big_pair_code((120, 100), (10.0,), 8)[2] == "invalid_measurement"
    assert big_pair_code((120, -1), (10.0, 0.0), 8)[2] == "invalid_measurement"
    assert big_pair_code((120, 100), (math.nan, 0.0), 8)[2] == "invalid_measurement"
    assert big_pair_code((120, 100), (10.0, 0.0), True)[2] == "invalid_measurement"
    assert big_pair_code((120, 100), (10.0, 0.0), -1)[2] == "invalid_measurement"


# --- the small object in front ----------------------------------------------------------------


def test_a_small_territory_in_front_of_the_superior_big_one_near_its_end_is_anterior_small() -> (
    None
):
    assert (
        anterior_small_code(12, 120, 30.0, 10.0, -5.0, -20.0, 20.0) == "anterior_small"
    )


def test_the_anterior_decision_names_each_way_a_candidate_fails() -> None:
    assert anterior_small_code(120, 120, 30.0, 10.0, -5.0, -20.0, 20.0) == "not_small"
    assert anterior_small_code(12, 120, 5.0, 10.0, -5.0, -20.0, 20.0) == "not_anterior"
    assert (
        anterior_small_code(12, 120, 30.0, 10.0, 50.0, -20.0, 20.0)
        == "not_near_the_end"
    )
    assert (
        anterior_small_code(12, 120, 30.0, 10.0, -20.0, -20.0, 20.0)
        == "not_near_the_end"
    )


def test_the_anterior_decision_refuses_a_non_number() -> None:
    assert (
        anterior_small_code(12, 120, math.nan, 10.0, -5.0, -20.0, 20.0)
        == "invalid_measurement"
    )
    assert (
        anterior_small_code(True, 120, 30.0, 10.0, -5.0, -20.0, 20.0)
        == "invalid_measurement"
    )


# --- the witness ----------------------------------------------------------------------------


def test_a_small_ringed_territory_below_and_beside_the_inferior_big_one_is_the_witness() -> (
    None
):
    assert (
        lateral_witness_code(9, 110, True, -30.0, -10.0, 25.0) == "lateral_small_ringed"
    )
    assert (
        lateral_witness_code(9, 110, True, -30.0, -10.0, -25.0)
        == "lateral_small_ringed"
    )


def test_the_witness_decision_names_each_way_a_candidate_fails() -> None:
    assert lateral_witness_code(110, 110, True, -30.0, -10.0, 25.0) == "not_small"
    assert lateral_witness_code(9, 110, False, -30.0, -10.0, 25.0) == "not_ringed"
    assert lateral_witness_code(9, 110, True, 0.0, -10.0, 25.0) == "not_below_the_face"
    assert lateral_witness_code(9, 110, True, -30.0, -10.0, 0.0) == "not_beside"


def test_the_witness_decision_refuses_what_it_cannot_read() -> None:
    assert lateral_witness_code(9, 110, 1, -30.0, -10.0, 25.0) == "invalid_measurement"  # type: ignore[arg-type]
    assert (
        lateral_witness_code(9, 110, True, math.inf, -10.0, 25.0)
        == "invalid_measurement"
    )


# --- the axial's own rule ---------------------------------------------------------------------


def test_the_axial_takes_the_largest_and_the_largest_one_in_front_of_it() -> None:
    assert axial_code((200, 30, 20), (0.0, 15.0, 12.0), 8) == (0, 1, "selected")


def test_the_axial_never_takes_a_territory_behind_the_central_one() -> None:
    assert axial_code((200, 30), (0.0, -15.0), 8) == (0, None, "one_big_only")


def test_the_axial_says_a_tie_for_the_central_object() -> None:
    assert axial_code((200, 200, 20), (0.0, 1.0, 12.0), 8)[2] == "tie"


def test_the_axial_decision_abstains_and_refuses_by_name() -> None:
    assert axial_code((2, 3), (0.0, 1.0), 8) == (None, None, "none")
    assert axial_code((200,), (0.0, 1.0), 8)[2] == "invalid_measurement"


# --- the sign -------------------------------------------------------------------------------


def test_the_witness_on_the_patients_left_gives_left_and_on_the_right_gives_right() -> (
    None
):
    assert lateral_sign_code(25.0) == "left"
    assert lateral_sign_code(-25.0) == "right"


def test_no_witness_abstains_the_sign_and_never_guesses() -> None:
    assert lateral_sign_code(None) == "side_abstained"
    assert lateral_sign_code(0.0) == "side_abstained"


def test_the_sign_refuses_a_non_number() -> None:
    assert lateral_sign_code(math.nan) == "invalid_measurement"
    assert lateral_sign_code(True) == "invalid_measurement"
    assert lateral_sign_code("left") == "invalid_measurement"  # type: ignore[arg-type]


def test_every_code_is_in_its_vocabulary() -> None:
    assert big_pair_code((120, 100), (10.0, -40.0), 8)[2] in PAIR_CODES
    assert axial_code((120, 100), (10.0, 40.0), 8)[2] in PAIR_CODES
    assert anterior_small_code(12, 120, 30.0, 10.0, -5.0, -20.0, 20.0) in ANTERIOR_CODES
    assert lateral_witness_code(9, 110, True, -30.0, -10.0, 25.0) in WITNESS_CODES
    for offset in (None, 0.0, 1.0, -1.0, math.nan):
        assert lateral_sign_code(offset) in SIGN_CODES
