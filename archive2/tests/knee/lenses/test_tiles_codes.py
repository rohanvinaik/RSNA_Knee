"""Intent tests for the tile digits' pure decision (knee.lenses.tiles.tile_population_code),
written from the contract and the founder's rulings of 2026-10-13: the terciles are read over
everything the first lens did not clear; the undecided tiles at the skin stay in play; a cleared
tile is never read again; an empty tile has nothing to count; a word the module does not know is
named, never counted."""

from knee.collapse.first_lens import TILE_CODES
from knee.lenses.tiles import POPULATION_CODES, tile_population_code


def test_a_tile_the_lens_did_not_clear_is_counted() -> None:
    assert tile_population_code("not_background") == "counted"


def test_an_undecided_tile_at_the_skin_stays_in_play_and_is_counted() -> None:
    # The founder, 2026-10-13: "They stay in play. 'Some buffer is perfectly fine.'"
    assert tile_population_code("undecided") == "counted"


def test_a_cleared_tile_is_never_read_again() -> None:
    # "Only what was cleared is never read again."
    assert tile_population_code("background") == "cleared"


def test_an_empty_tile_has_nothing_to_count() -> None:
    assert tile_population_code("tile_empty") == "empty"


def test_a_word_the_module_does_not_know_is_named_and_never_counted() -> None:
    for word in ("leg", "air", "", "BACKGROUND", "not background"):
        assert tile_population_code(word) == "unknown_code"


def test_only_the_lens_own_words_are_ever_counted() -> None:
    counted = [word for word in TILE_CODES if tile_population_code(word) == "counted"]
    assert counted == ["not_background", "undecided"]


def test_every_code_is_in_the_vocabulary() -> None:
    for word in (*TILE_CODES, "leg", "", "anything"):
        assert tile_population_code(word) in POPULATION_CODES
