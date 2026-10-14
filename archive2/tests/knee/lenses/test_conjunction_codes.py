"""Intent tests for the conjunction's pure decision (knee.lenses.conjunction.conjunction_code),
written from the contract: the two digits of one tile read together as an ordered pair named by
their words; a silence on either side is named, the recipient's own first; a tile with no partner
tile named has nothing to read together; the line-up's distance is a reading, never a refusal here
(the founder, 2026-10-13); a refusal outranks every silence; no code carries a tissue word."""

from knee.collapse.lineup import MATCH_CODES
from knee.lenses.conjunction import (
    CONJUNCTION_CODES,
    READ_CONJUNCTIONS,
    conjunction_code,
)

DIGITS = (-1, 0, 1, 2)


def test_bright_on_the_partner_and_dark_on_the_recipient_is_above_below() -> None:
    assert conjunction_code(1, -1, "matched") == "above_below"


def test_the_pair_is_ordered_partner_first_then_own() -> None:
    assert conjunction_code(-1, 1, "matched") == "below_above"
    assert conjunction_code(1, -1, "matched") != conjunction_code(-1, 1, "matched")


def test_every_ordered_pair_of_readings_has_its_own_name() -> None:
    names = {
        conjunction_code(partner, own, "matched")
        for partner in (-1, 0, 1)
        for own in (-1, 0, 1)
    }
    assert names == set(READ_CONJUNCTIONS)
    assert len(names) == 9


def test_a_tile_beyond_half_a_tile_still_reads_its_named_partner_tile() -> None:
    # The founder, 2026-10-13: "The distance is a reading to keep; refusing the overlap on it was
    # never your rule."
    assert conjunction_code(1, -1, "beyond_half_tile") == "above_below"
    assert conjunction_code(0, 0, "beyond_half_tile") == "at_at"


def test_a_tile_with_no_partner_tile_named_has_nothing_to_read_together() -> None:
    for partner in DIGITS:
        for own in DIGITS:
            assert conjunction_code(partner, own, "partner_unavailable") == "unmatched"
            assert conjunction_code(partner, own, "invalid_measurement") == "unmatched"


def test_the_recipients_own_silence_is_named_first() -> None:
    assert conjunction_code(2, 2, "matched") == "self_silent"
    assert conjunction_code(1, 2, "matched") == "self_silent"


def test_the_partners_silence_is_named_when_the_recipient_read() -> None:
    for own in (-1, 0, 1):
        assert conjunction_code(2, own, "matched") == "partner_silent"


def test_a_digit_outside_the_vocabulary_or_a_bool_is_refused() -> None:
    assert conjunction_code(3, 0, "matched") == "invalid_measurement"
    assert conjunction_code(0, -2, "matched") == "invalid_measurement"
    assert conjunction_code(True, 0, "matched") == "invalid_measurement"
    assert conjunction_code(0, False, "matched") == "invalid_measurement"


def test_a_match_word_the_line_up_does_not_say_is_refused() -> None:
    assert conjunction_code(0, 0, "near") == "invalid_measurement"
    assert conjunction_code(0, 0, "") == "invalid_measurement"


def test_the_refusal_outranks_the_silences_and_the_unmatched_tile() -> None:
    assert conjunction_code(3, 2, "partner_unavailable") == "invalid_measurement"
    assert conjunction_code(2, 2, "nonsense") == "invalid_measurement"


def test_no_code_carries_a_tissue_word() -> None:
    for word in CONJUNCTION_CODES:
        for tissue in (
            "fat",
            "fluid",
            "cortex",
            "bone",
            "marrow",
            "tendon",
            "meniscus",
        ):
            assert tissue not in word


def test_the_twelve_codes_cover_every_valid_input_and_the_refusal_the_rest() -> None:
    seen = set()
    for partner in DIGITS:
        for own in DIGITS:
            for match in MATCH_CODES:
                code = conjunction_code(partner, own, match)
                assert code in CONJUNCTION_CODES
                assert code != "invalid_measurement"
                seen.add(code)
    assert seen == set(CONJUNCTION_CODES) - {"invalid_measurement"}
