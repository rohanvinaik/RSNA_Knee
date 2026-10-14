"""Intent tests for the interstice's pure decisions (knee.relations.interstice) and round 3's
(knee.relations.spans), written from the contracts: a wall reads plate, layer, fill from the band
outward; the fill is the read pair that holds most of the space, a mix when tied, unread when none;
a content is central or peripheral by where it lies across the pair's axis; a side is given only
with the laterality sign; a span reaches both big objects outside every interstice; a pouch is the
envelope's posterior part; every refusal is named."""

from knee.relations.interstice import (
    FILL_CODES,
    POSITION_CODES,
    SIDE_CODES,
    WALL_CODES,
    fill_code,
    position_code,
    side_code,
    wall_code,
)
from knee.relations.spans import POUCH_CODES, SPAN_CODES, pouch_code, span_code

# --- the wall -------------------------------------------------------------------------------


def test_a_plate_then_a_layer_then_the_fill_is_plate_layer_fill() -> None:
    assert wall_code((-1, -1, 0, 0, 1, 1)) == "plate_layer_fill"
    assert wall_code((-1, 0, -1)) == "plate_layer_fill"


def test_a_plate_then_the_fill_directly_is_plate_fill() -> None:
    assert wall_code((-1, -1, 1, 1)) == "plate_fill"
    assert wall_code((-1, 1)) == "plate_fill"


def test_a_wall_with_no_plate_first_cannot_be_read() -> None:
    assert wall_code((0, -1, 1)) == "unreadable"
    assert wall_code((1, 1)) == "unreadable"


def test_a_plate_with_nothing_or_silence_after_it_cannot_be_read() -> None:
    assert wall_code((-1, -1)) == "unreadable"
    assert wall_code((-1, 2, 1)) == "unreadable"
    assert wall_code((-1, 0, 0)) == "unreadable"
    assert wall_code((-1, 0, 2)) == "unreadable"


def test_an_empty_or_malformed_sequence_cannot_be_read() -> None:
    assert wall_code(()) == "unreadable"
    assert wall_code((-1, 3)) == "unreadable"
    assert wall_code((-1, True)) == "unreadable"
    assert wall_code("-1 0 1") == "unreadable"  # type: ignore[arg-type]


# --- the fill -------------------------------------------------------------------------------


def test_the_fill_is_the_read_pair_holding_most_tiles() -> None:
    assert (
        fill_code({"above_below": 30, "at_at": 4, "self_silent": 10}) == "above_below"
    )


def test_a_tie_between_read_pairs_is_a_mix() -> None:
    assert fill_code({"above_below": 10, "below_below": 10}) == "fill_mixed"


def test_silences_and_unmatched_tiles_never_fill_the_space() -> None:
    assert fill_code({"self_silent": 40, "unmatched": 3}) == "fill_unread"
    assert fill_code({}) == "fill_unread"
    assert fill_code({"at_at": 0}) == "fill_unread"


def test_the_fill_decision_refuses_what_it_cannot_read() -> None:
    assert fill_code({"fat": 3}) == "invalid_measurement"
    assert fill_code({"at_at": -1}) == "invalid_measurement"
    assert fill_code({"at_at": True}) == "invalid_measurement"
    assert fill_code([("at_at", 3)]) == "invalid_measurement"  # type: ignore[arg-type]


# --- the position ---------------------------------------------------------------------------


def test_a_content_near_the_pairs_axis_is_central_and_one_far_from_it_peripheral() -> (
    None
):
    assert position_code(1.0, 20.0) == "central"
    assert position_code(-15.0, 20.0) == "peripheral"
    assert position_code(10.0, 20.0) == "peripheral"


def test_the_position_decision_refuses_what_it_cannot_read() -> None:
    assert position_code(float("nan"), 20.0) == "invalid_measurement"
    assert position_code(1.0, 0.0) == "invalid_measurement"
    assert position_code(True, 20.0) == "invalid_measurement"


# --- the side -------------------------------------------------------------------------------


def test_the_side_follows_the_sign() -> None:
    assert side_code(12.0, "left") == "lateral"
    assert side_code(-12.0, "left") == "medial"
    assert side_code(12.0, "right") == "medial"
    assert side_code(-12.0, "right") == "lateral"


def test_with_no_sign_the_side_abstains_and_never_guesses() -> None:
    assert side_code(12.0, "side_abstained") == "side_abstained"
    assert side_code(12.0, "invalid_measurement") == "side_abstained"
    assert side_code(0.0, "left") == "side_abstained"


def test_the_side_decision_refuses_what_it_cannot_read() -> None:
    assert side_code(float("inf"), "left") == "invalid_measurement"
    assert side_code(12.0, "lateral") == "invalid_measurement"
    assert side_code(True, "left") == "invalid_measurement"


# --- round 3 --------------------------------------------------------------------------------


def test_a_dark_body_reaching_both_big_objects_outside_the_spaces_is_a_span() -> None:
    assert span_code(True, True, False) == "span"


def test_a_body_inside_an_interstice_is_its_content_not_a_span() -> None:
    assert span_code(True, True, True) == "inside_interstice"


def test_a_body_reaching_one_or_neither_object_is_named_so() -> None:
    assert span_code(True, False, False) == "touches_one"
    assert span_code(False, True, False) == "touches_one"
    assert span_code(False, False, False) == "touches_none"


def test_the_span_decision_refuses_a_non_bool() -> None:
    assert span_code(1, True, False) == "invalid_measurement"  # type: ignore[arg-type]


def test_a_pouch_exists_when_envelope_tiles_lie_behind_the_big_objects() -> None:
    assert pouch_code(14, 3) == "pouch"
    assert pouch_code(0, 0) == "no_pouch"
    assert pouch_code(14, 0) == "pouch"


def test_the_pouch_decision_refuses_a_bad_count() -> None:
    assert pouch_code(-1, 0) == "invalid_measurement"
    assert pouch_code(2, True) == "invalid_measurement"


def test_every_code_is_in_its_vocabulary() -> None:
    assert wall_code((-1, 1)) in WALL_CODES
    assert fill_code({"at_at": 1}) in FILL_CODES
    assert position_code(1.0, 2.0) in POSITION_CODES
    assert side_code(1.0, "left") in SIDE_CODES
    assert span_code(True, True, False) in SPAN_CODES
    assert pouch_code(1, 1) in POUCH_CODES
