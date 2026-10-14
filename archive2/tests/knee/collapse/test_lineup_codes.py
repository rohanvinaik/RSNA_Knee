"""Intent tests for the line-up's pure decisions (knee.collapse.lineup.match_code, slab_code),
written from the contract: a partner tile centre within half a tile reads the same millimetres of
knee; farther is kept and named but not the same patch; no partner is a silence; a bar or a
measurement that is not a number is a refusal, never a match; a slice thickness the header did not
give is not a slab of zero."""

import math

from knee.collapse.lineup import MATCH_CODES, SLAB_CODES, match_code, slab_code


def test_a_centre_within_half_a_tile_is_the_same_patch() -> None:
    assert (
        match_code(distance_mm=1.5, half_tile_mm=4.0, partner_exists=True) == "matched"
    )
    assert (
        match_code(distance_mm=4.0, half_tile_mm=4.0, partner_exists=True) == "matched"
    )


def test_a_centre_beyond_half_a_tile_is_named_not_matched() -> None:
    assert (
        match_code(distance_mm=4.01, half_tile_mm=4.0, partner_exists=True)
        == "beyond_half_tile"
    )


def test_no_partner_is_a_silence_whatever_the_distance() -> None:
    assert (
        match_code(distance_mm=0.0, half_tile_mm=4.0, partner_exists=False)
        == "partner_unavailable"
    )
    assert (
        match_code(distance_mm=math.nan, half_tile_mm=4.0, partner_exists=False)
        == "partner_unavailable"
    )


def test_a_distance_or_bar_that_cannot_be_read_is_a_refusal() -> None:
    assert (
        match_code(distance_mm=math.nan, half_tile_mm=4.0, partner_exists=True)
        == "invalid_measurement"
    )
    assert (
        match_code(distance_mm=-1.0, half_tile_mm=4.0, partner_exists=True)
        == "invalid_measurement"
    )
    assert (
        match_code(distance_mm=1.0, half_tile_mm=0.0, partner_exists=True)
        == "invalid_measurement"
    )
    assert (
        match_code(distance_mm=1.0, half_tile_mm=math.inf, partner_exists=True)
        == "invalid_measurement"
    )


def test_the_half_tile_is_the_callers_bar() -> None:
    assert (
        match_code(distance_mm=3.0, half_tile_mm=2.0, partner_exists=True) != "matched"
    )
    assert (
        match_code(distance_mm=3.0, half_tile_mm=5.0, partner_exists=True) == "matched"
    )


def test_a_partner_slice_within_half_the_thickness_cuts_the_same_slab() -> None:
    assert (
        slab_code(offset_mm=1.0, half_thickness_mm=1.5, partner_exists=True)
        == "in_slab"
    )
    assert (
        slab_code(offset_mm=1.5, half_thickness_mm=1.5, partner_exists=True)
        == "in_slab"
    )


def test_a_farther_partner_slice_is_still_named_as_nearest() -> None:
    assert (
        slab_code(offset_mm=2.0, half_thickness_mm=1.5, partner_exists=True)
        == "nearest_only"
    )


def test_no_partner_slice_is_a_silence() -> None:
    assert (
        slab_code(offset_mm=0.0, half_thickness_mm=1.5, partner_exists=False)
        == "no_partner"
    )


def test_a_thickness_the_header_did_not_give_is_not_a_slab_of_zero() -> None:
    assert (
        slab_code(offset_mm=0.0, half_thickness_mm=math.nan, partner_exists=True)
        == "invalid_measurement"
    )
    assert (
        slab_code(offset_mm=0.0, half_thickness_mm=0.0, partner_exists=True)
        == "invalid_measurement"
    )
    assert (
        slab_code(offset_mm=-0.5, half_thickness_mm=1.5, partner_exists=True)
        == "invalid_measurement"
    )


def test_every_code_is_in_its_vocabulary() -> None:
    for distance in (0.0, 1.0, 10.0, -1.0, math.nan, math.inf):
        for bar in (0.0, 4.0, math.nan):
            for exists in (True, False):
                assert match_code(distance, bar, exists) in MATCH_CODES
                assert slab_code(distance, bar, exists) in SLAB_CODES
