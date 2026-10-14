"""Intent tests for the facing pairs' pure decision (knee.relations.facing.facing_code), written
from the contract: two selected objects face when gap tiles touch both; touching without a gap is
named, not faced; an unselected territory is never in a facing pair; a refusal is named."""

from knee.relations.facing import FACING_CODES, facing_code


def test_two_selected_objects_with_gap_tiles_between_them_face() -> None:
    assert facing_code(0, 12, 1, True) == "facing"
    assert facing_code(3, 12, 1, True) == "facing"


def test_the_bar_on_gap_tiles_is_an_argument() -> None:
    assert facing_code(0, 2, 3, True) == "too_few_sites"
    assert facing_code(0, 3, 3, True) == "facing"


def test_a_bar_of_zero_still_needs_one_gap_tile() -> None:
    assert facing_code(0, 0, 0, True) == "too_few_sites"
    assert facing_code(0, 1, 0, True) == "facing"


def test_objects_that_touch_with_no_gap_are_named_and_not_faced() -> None:
    assert facing_code(5, 0, 1, True) == "touching_no_gap"


def test_an_unselected_territory_is_never_in_a_facing_pair() -> None:
    assert facing_code(5, 12, 1, False) == "not_selected"


def test_a_count_or_bar_that_cannot_be_read_is_refused() -> None:
    assert facing_code(-1, 12, 1, True) == "invalid_measurement"
    assert facing_code(0, True, 1, True) == "invalid_measurement"
    assert facing_code(0, 12, -1, True) == "invalid_measurement"
    assert facing_code(0, 12, 1, 1) == "invalid_measurement"  # type: ignore[arg-type]


def test_every_code_is_in_the_vocabulary() -> None:
    for sites in (0, 1, 5):
        for gap in (0, 1, 12):
            for bar in (0, 1, 3):
                for both in (True, False):
                    assert facing_code(sites, gap, bar, both) in FACING_CODES
