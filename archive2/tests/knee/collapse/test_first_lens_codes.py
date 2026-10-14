"""Intent tests for the first lens's pure decision (knee.collapse.first_lens.tile_code), written
from the contract: the lens clears air only where every pixel is dark and the tile reaches the
border; a dark interior is not air, and the lens says nothing more of it; a tile that straddles the
skin line beside the air is undecided and stays in play; an empty tile is its own code; the lens
never clears what it is unsure of. The third word is "not_background" (the founder, 2026-10-13:
the word "leg" said more than the lens measured)."""

from knee.collapse.first_lens import TILE_CODES, tile_code


def test_an_all_dark_tile_reaching_the_border_is_background() -> None:
    assert (
        tile_code(
            finite=True,
            all_dark=True,
            any_dark=True,
            air_connected=True,
            beside_air=True,
        )
        == "background"
    )


def test_a_dark_interior_is_not_air_and_the_lens_says_nothing_more() -> None:
    # The marrow on a fat-dark series is dark and enclosed: it never reaches the border.
    assert (
        tile_code(
            finite=True,
            all_dark=True,
            any_dark=True,
            air_connected=False,
            beside_air=False,
        )
        == "not_background"
    )


def test_a_straddling_tile_beside_the_air_is_undecided_and_stays_in_play() -> None:
    assert (
        tile_code(
            finite=True,
            all_dark=False,
            any_dark=True,
            air_connected=False,
            beside_air=True,
        )
        == "undecided"
    )


def test_a_partly_dark_tile_away_from_the_air_is_not_background() -> None:
    assert (
        tile_code(
            finite=True,
            all_dark=False,
            any_dark=True,
            air_connected=False,
            beside_air=False,
        )
        == "not_background"
    )


def test_a_fully_bright_tile_is_not_background_wherever_it_lies() -> None:
    for beside in (True, False):
        assert (
            tile_code(
                finite=True,
                all_dark=False,
                any_dark=False,
                air_connected=False,
                beside_air=beside,
            )
            == "not_background"
        )


def test_an_empty_tile_is_its_own_code_before_anything_else() -> None:
    assert (
        tile_code(
            finite=False,
            all_dark=True,
            any_dark=True,
            air_connected=True,
            beside_air=True,
        )
        == "tile_empty"
    )


def test_the_lens_never_clears_a_tile_it_is_unsure_of() -> None:
    # Only the all-dark, border-connected tile is ever background.
    for all_dark in (True, False):
        for any_dark in (True, False):
            for connected in (True, False):
                for beside in (True, False):
                    code = tile_code(True, all_dark, any_dark, connected, beside)
                    if code == "background":
                        assert all_dark and connected


def test_the_third_word_never_claims_what_the_lens_did_not_measure() -> None:
    # No code of the lens names anatomy: it clears, it hesitates beside the air, or it says
    # only that it found no air here.
    for word in TILE_CODES:
        assert word in ("background", "not_background", "undecided", "tile_empty")


def test_every_code_is_in_the_vocabulary() -> None:
    for finite in (True, False):
        for all_dark in (True, False):
            for any_dark in (True, False):
                for connected in (True, False):
                    for beside in (True, False):
                        assert (
                            tile_code(finite, all_dark, any_dark, connected, beside)
                            in TILE_CODES
                        )
