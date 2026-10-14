"""Intent tests for the tile dome's pure decision (knee.objects.tile_dome.dome_tile_code), written
from the contract: an object can hold any tile the first lens kept, the buffer at the skin included
(the founder keeps it in play); the cleared air is an obstacle whatever else is said; on a solitary
plane the series' own split says which kept tiles are dark; on a paired plane the border is read
two ways and both are seated (his ruling of 2026-10-12, keep everything): `dark_on_both`, the
object model's recorded row, and `edge_of_bright_partner`, where the body bright on the fat-bright
ends; silence settles nothing under either; nothing is cut on strength."""

from knee.collapse.first_lens import TILE_CODES
from knee.lenses.conjunction import CONJUNCTION_CODES
from knee.objects.tile_dome import BORDER_CODES, DOME_TILE_CODES, dome_tile_code

DARK = "dark_on_both"
EDGE = "edge_of_bright_partner"
SILENCES = ("partner_silent", "self_silent", "unmatched", "invalid_measurement")


def test_the_two_borders_are_named() -> None:
    assert BORDER_CODES == (DARK, EDGE)


def test_dark_on_both_makes_only_the_tile_dark_on_both_an_obstacle() -> None:
    assert dome_tile_code("not_background", "below_below", False, DARK) == "obstacle"
    for word in ("above_below", "at_at", "below_above", "above_above", "at_below"):
        assert dome_tile_code("not_background", word, True, DARK) == "interior"


def test_the_edge_of_the_bright_partner_keeps_only_the_partners_bright_tiles() -> None:
    # Interior: the fat-bright partner read the tile and it is bright there.
    for word in ("above_below", "above_at", "above_above"):
        assert dome_tile_code("not_background", word, True, EDGE) == "interior"
    # Obstacle: the partner read the tile and it is not bright there, whatever the own digit.
    for word in (
        "at_below",
        "at_at",
        "at_above",
        "below_below",
        "below_at",
        "below_above",
    ):
        assert dome_tile_code("not_background", word, False, EDGE) == "obstacle"


def test_the_two_borders_disagree_where_the_line_between_the_bodies_is_not_dark_on_both() -> (
    None
):
    # Measured on the one study at 8 mm: the line between the two bodies reads at_below.
    assert dome_tile_code("not_background", "at_below", False, DARK) == "interior"
    assert dome_tile_code("not_background", "at_below", False, EDGE) == "obstacle"
    # And the two agree on the tile dark on both and on the bright body.
    for border in BORDER_CODES:
        assert dome_tile_code("not_background", "below_below", False, border) == (
            "obstacle"
        )
        assert dome_tile_code("not_background", "above_at", False, border) == "interior"


def test_a_silent_or_unmatched_pair_reading_leaves_the_kept_tile_interior_under_both() -> (
    None
):
    # Silence settles nothing: a tile the pair could not read is not thereby an obstacle.
    for border in BORDER_CODES:
        for word in SILENCES:
            assert dome_tile_code("not_background", word, True, border) == "interior"
            assert dome_tile_code("undecided", word, True, border) == "interior"


def test_the_split_decides_only_on_a_solitary_plane_under_both_borders() -> None:
    for border in BORDER_CODES:
        assert dome_tile_code("not_background", None, True, border) == "obstacle"
        assert dome_tile_code("not_background", None, False, border) == "interior"
    # With a pair reading present the split is not consulted.
    assert dome_tile_code("not_background", "at_at", True, DARK) == "interior"
    assert dome_tile_code("not_background", "above_at", True, EDGE) == "interior"


def test_the_buffer_at_the_skin_stays_in_play_and_follows_the_kept_tiles_rule() -> None:
    # The founder, 2026-10-13: "some buffer is perfectly fine"; the Codex check the same day:
    # keeping its data does not keep it eligible unless the dome lets it in. It does.
    assert dome_tile_code("undecided", "above_below", True, DARK) == "interior"
    assert dome_tile_code("undecided", "above_below", True, EDGE) == "interior"
    assert dome_tile_code("undecided", None, False, EDGE) == "interior"
    assert dome_tile_code("undecided", "below_below", False, DARK) == "obstacle"
    assert dome_tile_code("undecided", "at_at", False, EDGE) == "obstacle"
    assert dome_tile_code("undecided", None, True, DARK) == "obstacle"


def test_the_cleared_air_is_an_obstacle_whatever_else_is_said() -> None:
    for pair in (None, "above_below", "below_below", "self_silent", "fat", ""):
        for dark in (True, False):
            for border in (*BORDER_CODES, "neither", ""):
                assert dome_tile_code("background", pair, dark, border) == "obstacle"


def test_an_empty_tile_is_empty_before_anything_else() -> None:
    assert dome_tile_code("tile_empty", "below_below", True, DARK) == "empty"
    assert dome_tile_code("tile_empty", None, False, EDGE) == "empty"
    assert dome_tile_code("tile_empty", "fat", False, "neither") == "empty"


def test_a_word_outside_any_vocabulary_is_named_and_never_interior() -> None:
    assert dome_tile_code("leg", None, False, DARK) == "unknown_code"
    assert dome_tile_code("", "", False, EDGE) == "unknown_code"
    assert dome_tile_code("not_background", "fat", False, DARK) == "unknown_code"
    assert dome_tile_code("not_background", "above_at", False, "neither") == (
        "unknown_code"
    )
    assert dome_tile_code("undecided", None, False, "") == "unknown_code"


def test_every_code_is_in_the_vocabulary() -> None:
    for first in (*TILE_CODES, "leg", ""):
        for pair in (None, *CONJUNCTION_CODES, "fat"):
            for dark in (True, False):
                for border in (*BORDER_CODES, "neither"):
                    assert dome_tile_code(first, pair, dark, border) in DOME_TILE_CODES
