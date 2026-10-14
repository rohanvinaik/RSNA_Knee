"""Intent tests for the conjunction's measurement and orchestration (knee.lenses.conjunction),
both signs, written from the contract and the founder's ruling of 2026-10-13: over a slice
holding every digit on both sides under every match word, the vectorised codes equal
`conjunction_code` applied at every tile; a partner tile index of -1 reads unmatched; a digit
outside the vocabulary reads the refusal the scalar gives it; a partner tile index outside the
partner's grid, a stored match index outside `MATCH_CODES` and a digit grid that is not the
tile digits' own int8 are refused by name; no input is
written and the output is frozen; over synthetic digits and a synthetic line-up the conjunction
agrees with the scalar at every tile, a `beyond_half_tile` tile reads its named partner tile
like a matched one, a partner slice of -1 reads unmatched throughout, mismatched uids are refused
by name, an absent line-up or an absent digit record is predecessor_absent, a shape mismatch is
refused, and the ledger carries the two consumptions then the production. The CONTRACT's proof
gate."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from knee.collapse.first_lens import read_first_lens
from knee.collapse.lineup import MATCH_CODES, LineUp, line_up
from knee.collapse.squint_stack import SquintStack, read_squint_stack
from knee.compute.contracts import handed_on
from knee.lenses.conjunction import (
    CONJUNCTION_CODES,
    CONJUNCTION_RECORD_CODES,
    CONTRACT,
    READ_CONJUNCTIONS,
    Conjunction,
    conjoin,
    conjunction_code,
    read_conjunction,
)
from knee.lenses.places import SILENT
from knee.lenses.tiles import TileDigits, read_tile_digits
from knee.study.series import Series, SeriesGeometry
from knee.study.tables import SeriesRow
from knee.telemetry import recording

#: The digit vocabulary as the tile digits store it, and one int outside it.
DIGITS: tuple[int, ...] = (-1, 0, 1, SILENT)
OUTSIDE = SILENT + 1

MATCHED = MATCH_CODES.index("matched")
BEYOND = MATCH_CODES.index("beyond_half_tile")
UNAVAILABLE = MATCH_CODES.index("partner_unavailable")
INVALID_MATCH = MATCH_CODES.index("invalid_measurement")
UNMATCHED = CONJUNCTION_CODES.index("unmatched")
INVALID = CONJUNCTION_CODES.index("invalid_measurement")
SELF_SILENT = CONJUNCTION_CODES.index("self_silent")
PARTNER_SILENT = CONJUNCTION_CODES.index("partner_silent")

#: An axial-like header at half a millimetre a pixel: a 2 mm tile is 4 px; the plane is 24 px
#: square, a 6 x 6 grid of tiles, three slices one millimetre apart; the partner's origin lies a
#: quarter of a millimetre along the row direction from the recipient's (the "scootch").
AXIAL = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
NORMAL = np.array([0.0, 0.0, 1.0])
SPACING = (0.5, 0.5)
TILE_MM = 2.0
HALF_TILE_MM = TILE_MM / 2.0
HALF_THICKNESS_MM = 0.5
TILE_PX = 4
TILES = 6
SLICES = 3
SCOOTCH_MM = 0.25
AIR, BRIGHT, SPLIT = 0.0, 100.0, 10.0
BAR = 8

NOWHERE = Path("/nonexistent/the-funnel/conjunction")
STUDY = "study-conjunction"
DARK_UID = "series-conjunction-dark"
BRIGHT_UID = "series-conjunction-bright"

#: The two planes, tile by tile, as the tile digits' proof gate has them: B all dark (the air),
#: U partly dark beside the air, L all bright, D all dark but enclosed, M partly dark away from
#: the air. The kept medians are 50 (U, M), 100 (L) and 0 (D), so the terciles of either series
#: are 50 and 50: D reads below, U and M at, L above. The partner swaps where L and D sit, so
#: the two series' digits differ at known tiles.
RECIPIENT = ("BBBBBB", "BUUUUB", "BULMUB", "BULDUB", "BUUUUB", "BBBBBB")
PARTNER = ("BBBBBB", "BUUUUB", "BUDMUB", "BULLUB", "BUUUUB", "BBBBBB")


# --- synthetic records ---------------------------------------------------------------------


def _plane(pattern: tuple[str, ...]) -> np.ndarray:
    plane = np.full((TILES * TILE_PX, TILES * TILE_PX), BRIGHT, dtype=np.float64)
    for i, row in enumerate(pattern):
        for j, kind in enumerate(row):
            r0, c0 = i * TILE_PX, j * TILE_PX
            if kind in "BD":
                plane[r0 : r0 + TILE_PX, c0 : c0 + TILE_PX] = AIR
            elif kind in "UM":
                plane[r0 : r0 + TILE_PX // 2, c0 : c0 + TILE_PX] = AIR
    return plane


def _volume(
    pattern: tuple[str, ...], empty_tile: tuple[int, int, int] | None
) -> np.ndarray:
    volume = np.stack([_plane(pattern) for _ in range(SLICES)])
    if empty_tile is not None:
        z, i, j = empty_tile
        volume[z, i * TILE_PX : (i + 1) * TILE_PX, j * TILE_PX : (j + 1) * TILE_PX] = (
            np.nan
        )
    return volume


def _geometry(origin_x: float) -> SeriesGeometry:
    positions = np.array([[origin_x, 0.0, float(z)] for z in range(SLICES)])
    return SeriesGeometry(
        normal=NORMAL.copy(),
        orientation=np.tile(AXIAL, (SLICES, 1)),
        position=positions,
        spacing=np.tile(np.asarray(SPACING, dtype=np.float64), (SLICES, 1)),
        along_normal=positions @ NORMAL,
        orientation_spread=0.0,
        origin_spread_mm=0.0,
    )


def _series(
    uid: str, flavour: str, volume: np.ndarray | None, origin_x: float = 0.0
) -> Series:
    return Series(
        row=SeriesRow(STUDY, uid, flavour, flavour, "Coronal"),
        directory=NOWHERE / uid,
        slices=(),
        stack=("stackable",),
        volume=volume,
        geometry=_geometry(origin_x),
        slice_thickness_mm=(2.0 * HALF_THICKNESS_MM,) * SLICES,
    )


def _recipient(tile_mm: float = TILE_MM) -> tuple[Series, SquintStack, TileDigits]:
    """The fat-dark series with an empty tile at slice 1, tile (2, 2): a silence of its own."""
    series = _series(DARK_UID, "1", _volume(RECIPIENT, (1, 2, 2)))
    stack = read_squint_stack(series, tile_mm)
    return series, stack, read_tile_digits(stack, read_first_lens(stack, SPLIT), BAR)


def _partner(tile_mm: float = TILE_MM) -> tuple[Series, SquintStack, TileDigits]:
    """The fat-bright partner, scootched a quarter of a millimetre, with an empty tile at slice
    1, tile (3, 2): a silence the recipient does not share."""
    series = _series(BRIGHT_UID, "0", _volume(PARTNER, (1, 3, 2)), origin_x=SCOOTCH_MM)
    stack = read_squint_stack(series, tile_mm)
    return series, stack, read_tile_digits(stack, read_first_lens(stack, SPLIT), BAR)


def _lineup(
    recipient: tuple[Series, SquintStack, TileDigits],
    partner: tuple[Series, SquintStack, TileDigits],
    half_tile_mm: float = HALF_TILE_MM,
    without_recipient_geometry: bool = False,
) -> LineUp:
    """The line-up from the recipient to the partner; without the recipient's geometry no slice
    can be projected, which is the line-up's own silence (every slice -1, every tile
    partner_unavailable)."""
    return line_up(
        recipient[1],
        partner[1],
        None if without_recipient_geometry else recipient[0].geometry,
        partner[0].geometry,
        half_tile_mm,
        HALF_THICKNESS_MM,
    )


def _expected(own: TileDigits, partner: TileDigits, lineup: LineUp) -> np.ndarray:
    """The scalar decision at every tile, by hand: the partner's digit at the named partner tile
    of the named partner slice (silence where none is named), the recipient's own digit, and the
    line-up's word."""
    codes = np.empty(own.codes.shape, dtype=np.uint8)
    for z in range(own.codes.shape[0]):
        nearest = int(lineup.partner_slice[z])
        for i in range(own.codes.shape[1]):
            for j in range(own.codes.shape[2]):
                row, column = (int(v) for v in lineup.partner_tile[z, i, j])
                partner_digit = (
                    SILENT
                    if nearest == -1 or row == -1
                    else int(partner.digits[nearest, row, column])
                )
                word = conjunction_code(
                    partner_digit,
                    int(own.digits[z, i, j]),
                    MATCH_CODES[int(lineup.match_codes[z, i, j])],
                )
                codes[z, i, j] = CONJUNCTION_CODES.index(word)
    return codes


# --- the measurement: positive ---------------------------------------------------------------


def _every_combination_slice() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """One 8 x 8 recipient slice holding every (partner digit, own digit, match word): four
    4 x 4 blocks, one match word each; within a block the rows cycle the own digits and the
    columns the partner's, through a 4 x 4 partner slice whose column is its digit. The block
    whose word is partner_unavailable names no partner tile."""
    own = np.empty((8, 8), dtype=np.int8)
    partner = np.empty((4, 4), dtype=np.int8)
    tiles = np.empty((8, 8, 2), dtype=np.int64)
    matches = np.empty((8, 8), dtype=np.uint8)
    for column in range(4):
        partner[:, column] = DIGITS[column]
    for i in range(8):
        for j in range(8):
            own[i, j] = DIGITS[i % 4]
            matches[i, j] = (i // 4) * 2 + (j // 4)
            if MATCH_CODES[matches[i, j]] == "partner_unavailable":
                tiles[i, j] = (-1, -1)
            else:
                tiles[i, j] = (i % 4, j % 4)
    return own, partner, tiles, matches


def test_the_vectorised_codes_are_the_scalar_decision_at_every_tile() -> None:
    own, partner, tiles, matches = _every_combination_slice()
    codes = conjoin(own, partner, tiles, matches)
    assert codes.shape == own.shape and codes.dtype == np.uint8
    seen = set()
    for i in range(8):
        for j in range(8):
            row, column = (int(v) for v in tiles[i, j])
            partner_digit = SILENT if row == -1 else int(partner[row, column])
            expected = conjunction_code(
                partner_digit, int(own[i, j]), MATCH_CODES[int(matches[i, j])]
            )
            assert CONJUNCTION_CODES[codes[i, j]] == expected, (i, j)
            seen.add(expected)
    # Every one of the twelve words over the readings is met somewhere on this slice, and the
    # refusal nowhere: the slice holds nothing outside the domain.
    assert seen == set(CONJUNCTION_CODES) - {"invalid_measurement"}


def test_a_matched_tile_reads_the_ordered_pair_partner_first() -> None:
    own = np.array([[-1]], dtype=np.int8)
    partner = np.array([[1]], dtype=np.int8)
    tiles = np.array([[[0, 0]]], dtype=np.int64)
    codes = conjoin(own, partner, tiles, np.array([[MATCHED]], dtype=np.uint8))
    assert CONJUNCTION_CODES[codes[0, 0]] == "above_below"
    # The pair is ordered: swapped digits give the other name.
    swapped = conjoin(partner, own, tiles, np.array([[MATCHED]], dtype=np.uint8))
    assert CONJUNCTION_CODES[swapped[0, 0]] == "below_above"


def test_a_tile_beyond_half_a_tile_reads_its_named_partner_tile_like_a_matched_one() -> (
    None
):
    # The founder, 2026-10-13: "The distance is a reading to keep; refusing the overlap on it
    # was never your rule."
    own, partner, tiles, _ = _every_combination_slice()
    matched = conjoin(own, partner, tiles, np.full(own.shape, MATCHED, dtype=np.uint8))
    beyond = conjoin(own, partner, tiles, np.full(own.shape, BEYOND, dtype=np.uint8))
    np.testing.assert_array_equal(matched, beyond)
    assert UNMATCHED not in beyond and INVALID not in beyond


def test_a_partner_tile_index_of_minus_one_reads_unmatched() -> None:
    own = np.array([[-1, 0], [1, SILENT]], dtype=np.int8)
    partner = np.array([[1, 1], [1, 1]], dtype=np.int8)
    none = np.full((2, 2, 2), -1, dtype=np.int64)
    codes = conjoin(own, partner, none, np.full((2, 2), UNAVAILABLE, dtype=np.uint8))
    assert set(codes.ravel().tolist()) == {UNMATCHED}
    # The line-up's own refusal names no partner tile either, and reads the same.
    refused = conjoin(
        own, partner, none, np.full((2, 2), INVALID_MATCH, dtype=np.uint8)
    )
    assert set(refused.ravel().tolist()) == {UNMATCHED}


def test_the_recipients_own_silence_is_named_before_the_partners() -> None:
    own = np.array([[SILENT, SILENT, 0]], dtype=np.int8)
    partner = np.array([[SILENT, 1, SILENT]], dtype=np.int8)
    tiles = np.array([[[0, 0], [0, 1], [0, 2]]], dtype=np.int64)
    codes = conjoin(own, partner, tiles, np.full((1, 3), MATCHED, dtype=np.uint8))
    assert [CONJUNCTION_CODES[c] for c in codes[0]] == [
        "self_silent",
        "self_silent",
        "partner_silent",
    ]


def test_an_empty_slice_is_an_empty_map_and_never_an_error() -> None:
    codes = conjoin(
        np.empty((0, 0), dtype=np.int8),
        np.empty((0, 0), dtype=np.int8),
        np.empty((0, 0, 2), dtype=np.int64),
        np.empty((0, 0), dtype=np.uint8),
    )
    assert codes.shape == (0, 0) and codes.dtype == np.uint8


def test_the_measurement_carries_the_modules_contract() -> None:
    assert conjoin.__dict__["__contract__"] is CONTRACT
    assert CONTRACT.reference == "conjoin"
    assert "test_conjunction.py" in CONTRACT.proof_gate


# --- the measurement: negative ---------------------------------------------------------------


def test_a_digit_outside_the_vocabulary_reads_the_refusal_the_scalar_gives_it() -> None:
    # MUST NOT: read a pair, or a silence, from a digit the vocabulary does not hold; the
    # scalar names it invalid_measurement, and so does the map, whatever the match word.
    own = np.array([[OUTSIDE, 0, -5]], dtype=np.int8)
    partner = np.array([[0, OUTSIDE, 0]], dtype=np.int8)
    tiles = np.array([[[0, 0], [0, 1], [0, 2]]], dtype=np.int64)
    for word in MATCH_CODES:
        codes = conjoin(
            own,
            partner,
            tiles,
            np.full((1, 3), MATCH_CODES.index(word), dtype=np.uint8),
        )
        assert set(codes.ravel().tolist()) == {INVALID}, word
        for j in range(3):
            assert conjunction_code(int(partner[0, j]), int(own[0, j]), word) == (
                "invalid_measurement"
            )


def test_a_partner_tile_outside_the_partners_grid_is_refused_by_name() -> None:
    own = np.zeros((2, 2), dtype=np.int8)
    partner = np.zeros((2, 2), dtype=np.int8)
    matches = np.full((2, 2), MATCHED, dtype=np.uint8)
    for bad in ((2, 0), (0, 2), (-1, 0), (0, -1), (-2, -2), (5, 5)):
        tiles = np.zeros((2, 2, 2), dtype=np.int64)
        tiles[1, 1] = bad
        with pytest.raises(ValueError, match="partner_tile_outside_grid"):
            conjoin(own, partner, tiles, matches)
    # An empty partner grid holds no tile to name: a named index is outside it.
    with pytest.raises(ValueError, match="partner_tile_outside_grid"):
        conjoin(
            own,
            np.empty((0, 0), dtype=np.int8),
            np.zeros((2, 2, 2), dtype=np.int64),
            matches,
        )


def test_a_stored_match_index_outside_the_vocabulary_is_refused_by_name() -> None:
    own = np.zeros((1, 2), dtype=np.int8)
    partner = np.zeros((1, 2), dtype=np.int8)
    tiles = np.array([[[0, 0], [0, 1]]], dtype=np.int64)
    with pytest.raises(ValueError, match="match_code_unknown"):
        conjoin(own, partner, tiles, np.array([[0, len(MATCH_CODES)]], dtype=np.uint8))
    with pytest.raises(ValueError, match="match_code_unknown"):
        conjoin(own, partner, tiles, np.array([[0, -1]], dtype=np.int64))


def test_a_digit_grid_that_is_not_the_tile_digits_int8_is_refused_by_name() -> None:
    # MUST NOT: gather a wider or an unsigned grid into the contract's int8 scratch, where 256
    # wraps to 0 and 255 to -1 and the map would name a pair the pinned scalar refuses. The
    # dtype the tile digits store is the one this operation reads; any other is named.
    own = np.zeros((1, 4), dtype=np.int8)
    tiles = np.array([[[0, 0], [0, 1], [0, 2], [0, 3]]], dtype=np.int64)
    matches = np.full((1, 4), MATCHED, dtype=np.uint8)
    wide = np.array([[255, 256, 257, 258]], dtype=np.int64)
    with pytest.raises(ValueError, match="conjunction_digits_not_int8"):
        conjoin(own, wide, tiles, matches)
    unsigned = np.array([[255, 0, 1, 2]], dtype=np.uint8)
    with pytest.raises(ValueError, match="conjunction_digits_not_int8"):
        conjoin(own, unsigned, tiles, matches)
    with pytest.raises(ValueError, match="conjunction_digits_not_int8"):
        conjoin(own.astype(np.int16), np.zeros((1, 4), dtype=np.int8), tiles, matches)
    for value in (255, 256, 257, 258):
        assert conjunction_code(value, 0, "matched") == "invalid_measurement"
    # The tile digits' own int8 reads as before: the positive sign of the same bar.
    codes = conjoin(own, np.array([[-1, 0, 1, SILENT]], dtype=np.int8), tiles, matches)
    assert [CONJUNCTION_CODES[c] for c in codes[0]] == [
        "below_at",
        "at_at",
        "above_at",
        "partner_silent",
    ]


@pytest.mark.parametrize(
    ("own", "partner", "tiles", "matches", "named"),
    [
        (
            np.zeros((2,), dtype=np.int8),
            np.zeros((2, 2), dtype=np.int8),
            np.zeros((2, 2), dtype=np.int64),
            np.zeros((2,), dtype=np.uint8),
            "invalid_digit_grid",
        ),
        (
            np.zeros((2, 2), dtype=np.int8),
            np.zeros((1, 2, 2), dtype=np.int8),
            np.zeros((2, 2, 2), dtype=np.int64),
            np.zeros((2, 2), dtype=np.uint8),
            "invalid_digit_grid",
        ),
        (
            np.zeros((2, 2), dtype=np.int8),
            np.zeros((2, 2), dtype=np.int8),
            np.zeros((2, 3, 2), dtype=np.int64),
            np.zeros((2, 2), dtype=np.uint8),
            "conjunction_grids_do_not_match",
        ),
        (
            np.zeros((2, 2), dtype=np.int8),
            np.zeros((2, 2), dtype=np.int8),
            np.zeros((2, 2, 2), dtype=np.int64),
            np.zeros((2, 3), dtype=np.uint8),
            "conjunction_grids_do_not_match",
        ),
        (
            np.zeros((2, 2), dtype=np.float64),
            np.zeros((2, 2), dtype=np.int8),
            np.zeros((2, 2, 2), dtype=np.int64),
            np.zeros((2, 2), dtype=np.uint8),
            "conjunction_values_not_whole_numbers",
        ),
    ],
)
def test_grids_that_are_not_one_slice_pairs_tiles_are_refused_by_name(
    own: np.ndarray,
    partner: np.ndarray,
    tiles: np.ndarray,
    matches: np.ndarray,
    named: str,
) -> None:
    with pytest.raises(ValueError, match=named):
        conjoin(own, partner, tiles, matches)


def test_the_measurement_writes_nothing_of_the_callers_and_freezes_its_own() -> None:
    own, partner, tiles, matches = _every_combination_slice()
    before = (own.copy(), partner.copy(), tiles.copy(), matches.copy())
    codes = conjoin(own, partner, tiles, matches)
    np.testing.assert_array_equal(own, before[0])
    np.testing.assert_array_equal(partner, before[1])
    np.testing.assert_array_equal(tiles, before[2])
    np.testing.assert_array_equal(matches, before[3])
    assert own.flags.writeable and partner.flags.writeable
    assert tiles.flags.writeable and matches.flags.writeable
    assert not codes.flags.writeable


# --- the orchestration: positive -------------------------------------------------------------


def test_the_conjunction_is_the_scalar_decision_at_every_tile_of_the_recipient() -> (
    None
):
    recipient, partner = _recipient(), _partner()
    lineup = _lineup(recipient, partner)
    assert lineup.code == "present"
    assert set(lineup.match_codes.ravel().tolist()) == {MATCHED}
    reading = read_conjunction(recipient[2], partner[2], lineup)
    assert isinstance(reading, Conjunction)
    assert reading.code == "present"
    assert reading.recipient_uid == DARK_UID and reading.partner_uid == BRIGHT_UID
    assert reading.codes.shape == (SLICES, TILES, TILES)
    assert reading.codes.dtype == np.uint8
    np.testing.assert_array_equal(
        reading.codes, _expected(recipient[2], partner[2], lineup)
    )
    # The known tiles: the swapped bright and dark tiles read the ordered pair, partner first.
    words = [[CONJUNCTION_CODES[c] for c in row] for row in reading.codes[0]]
    assert words[2][2] == "below_above"  # partner D (below), recipient L (above)
    assert words[3][3] == "above_below"  # partner L (above), recipient D (below)
    assert words[2][3] == "at_at"  # both M
    assert words[3][2] == "above_above"  # both L
    assert (
        words[1][1] == "at_at"
    )  # both U: undecided tiles stay in play (his ruling, 2026-10-13)
    assert words[0][0] == "self_silent"  # both cleared: the recipient's silence first
    # The recipient's empty tile is its own silence; the partner's is the partner's.
    assert CONJUNCTION_CODES[reading.codes[1, 2, 2]] == "self_silent"
    assert CONJUNCTION_CODES[reading.codes[1, 3, 2]] == "partner_silent"
    assert len(reading.counts) == len(CONJUNCTION_CODES)
    assert sum(reading.counts) == reading.codes.size
    for index, count in enumerate(reading.counts):
        assert count == int(np.count_nonzero(reading.codes == index))
    assert str(sum(reading.counts[: len(READ_CONJUNCTIONS)])) in reading.why
    assert "unmatched" in reading.why and "self_silent" in reading.why


def test_a_tile_beyond_half_a_tile_is_read_like_a_matched_one_over_the_pair() -> None:
    recipient, partner = _recipient(), _partner()
    matched = _lineup(recipient, partner)
    beyond = _lineup(recipient, partner, half_tile_mm=0.1)
    assert set(beyond.match_codes.ravel().tolist()) == {BEYOND}
    np.testing.assert_array_equal(
        read_conjunction(recipient[2], partner[2], beyond).codes,
        read_conjunction(recipient[2], partner[2], matched).codes,
    )


def test_a_partner_slice_of_minus_one_reads_unmatched_throughout() -> None:
    recipient, partner = _recipient(), _partner()
    # Without the recipient's geometry no slice is projected: the line-up is present, names no
    # partner slice, and every tile is partner_unavailable.
    silent = _lineup(recipient, partner, without_recipient_geometry=True)
    assert silent.code == "present"
    assert set(silent.partner_slice.tolist()) == {-1}
    reading = read_conjunction(recipient[2], partner[2], silent)
    assert reading.code == "present"
    assert set(reading.codes.ravel().tolist()) == {UNMATCHED}
    assert reading.counts[UNMATCHED] == reading.codes.size
    # One slice unnamed among named ones: that slice alone reads unmatched.
    lineup = _lineup(recipient, partner)
    mixed = replace(
        lineup,
        partner_slice=handed_on(np.array([0, -1, 2], dtype=np.int64)),
        partner_tile=handed_on(
            np.where(
                np.arange(SLICES)[:, None, None, None] == 1, -1, lineup.partner_tile
            ).astype(np.int64)
        ),
        match_codes=handed_on(
            np.where(
                np.arange(SLICES)[:, None, None] == 1, UNAVAILABLE, lineup.match_codes
            ).astype(np.uint8)
        ),
    )
    reading = read_conjunction(recipient[2], partner[2], mixed)
    assert set(reading.codes[1].ravel().tolist()) == {UNMATCHED}
    np.testing.assert_array_equal(
        reading.codes[0], _expected(recipient[2], partner[2], lineup)[0]
    )
    np.testing.assert_array_equal(
        reading.codes[2], _expected(recipient[2], partner[2], lineup)[2]
    )


def test_the_ledger_carries_the_two_consumptions_then_the_production() -> None:
    recipient, partner = _recipient(), _partner()
    lineup = _lineup(recipient, partner)
    with recording() as run_ledger:
        reading = read_conjunction(recipient[2], partner[2], lineup)
    events = run_ledger.events()
    assert [event.name for event in events] == [
        "tile_digits.consumed_by.conjunction",
        "lineup.consumed_by.conjunction",
        "conjunction.produced",
    ]
    assert dict(events[0].counts) == {"own": 1, "partner": 1}
    assert dict(events[1].counts) == {"lineup": 1}
    assert dict(events[2].counts) == {
        "read": sum(reading.counts[: len(READ_CONJUNCTIONS)])
    }
    assert dict(events[2].counts)["read"] > 0


# --- the orchestration: negative -------------------------------------------------------------


def test_mismatched_uids_are_refused_by_name_before_any_event() -> None:
    # MUST NOT: read two records as one pair's when the line-up names other series.
    recipient, partner = _recipient(), _partner()
    lineup = _lineup(recipient, partner)
    with (
        recording() as run_ledger,
        pytest.raises(ValueError, match="conjunction_series_mismatch"),
    ):
        read_conjunction(partner[2], recipient[2], lineup)
    assert run_ledger.events() == ()
    with pytest.raises(ValueError, match="conjunction_series_mismatch"):
        read_conjunction(recipient[2], recipient[2], lineup)


def test_an_absent_line_up_is_the_named_absence_with_empty_codes() -> None:
    recipient, partner = _recipient(), _partner()
    gone = _series(BRIGHT_UID, "0", None, origin_x=SCOOTCH_MM)
    absent_stack = read_squint_stack(gone, TILE_MM)
    assert absent_stack.code == "no_stacked_volume"
    lineup = line_up(
        recipient[1],
        absent_stack,
        recipient[0].geometry,
        gone.geometry,
        HALF_TILE_MM,
        HALF_THICKNESS_MM,
    )
    assert lineup.code == "no_stacked_volume"
    with recording() as run_ledger:
        reading = read_conjunction(recipient[2], partner[2], lineup)
    assert reading.code == "predecessor_absent"
    assert reading.code in CONJUNCTION_RECORD_CODES
    assert "line-up is no_stacked_volume" in reading.why
    assert reading.recipient_uid == DARK_UID and reading.partner_uid == BRIGHT_UID
    assert reading.codes.shape == (0, 0, 0) and reading.codes.dtype == np.uint8
    assert reading.counts == (0,) * len(CONJUNCTION_CODES)
    assert not reading.codes.flags.writeable
    events = run_ledger.events()
    assert dict(events[0].counts) == {"own": 1, "partner": 1}
    assert dict(events[1].counts) == {"lineup": 0}
    assert dict(events[2].counts) == {"read": 0}


def test_an_absent_digit_record_is_the_named_absence_whatever_the_line_up_holds() -> (
    None
):
    # MUST NOT: read a conjunction from digits that named no tile, on either side.
    recipient, partner = _recipient(), _partner()
    lineup = _lineup(recipient, partner)
    gone = read_squint_stack(_series(DARK_UID, "1", None), TILE_MM)
    absent_own = read_tile_digits(gone, read_first_lens(gone, SPLIT), BAR)
    assert absent_own.code == "predecessor_absent"
    with recording() as run_ledger:
        reading = read_conjunction(absent_own, partner[2], lineup)
    assert reading.code == "predecessor_absent"
    assert "recipient's tile digits are predecessor_absent" in reading.why
    assert reading.codes.shape == (0, 0, 0)
    assert dict(run_ledger.events()[0].counts) == {"own": 0, "partner": 1}
    assert dict(run_ledger.events()[1].counts) == {"lineup": 1}
    gone_partner = read_squint_stack(
        _series(BRIGHT_UID, "0", None, origin_x=SCOOTCH_MM), TILE_MM
    )
    absent_partner = read_tile_digits(
        gone_partner, read_first_lens(gone_partner, SPLIT), BAR
    )
    with recording() as run_ledger:
        reading = read_conjunction(recipient[2], absent_partner, lineup)
    assert reading.code == "predecessor_absent"
    assert "partner's tile digits are predecessor_absent" in reading.why
    assert dict(run_ledger.events()[0].counts) == {"own": 1, "partner": 0}


def test_digits_over_another_grid_than_the_line_up_are_refused_by_name() -> None:
    # MUST NOT: read a 3 x 3 digit record against a 6 x 6 line-up as if they were one series'.
    recipient, partner = _recipient(), _partner()
    lineup = _lineup(recipient, partner)
    coarse = _recipient(tile_mm=4.0)[2]
    assert coarse.codes.shape != lineup.match_codes.shape
    with pytest.raises(ValueError, match="digits_do_not_match_lineup"):
        read_conjunction(coarse, partner[2], lineup)


def test_a_partner_slice_the_partners_digits_do_not_hold_is_refused_by_name() -> None:
    recipient, partner = _recipient(), _partner()
    lineup = _lineup(recipient, partner)
    outside = replace(
        lineup, partner_slice=handed_on(np.array([0, SLICES, 2], dtype=np.int64))
    )
    with pytest.raises(ValueError, match="partner_slice_outside_digits"):
        read_conjunction(recipient[2], partner[2], outside)


def test_nothing_of_the_callers_is_written_and_the_output_is_frozen() -> None:
    recipient, partner = _recipient(), _partner()
    lineup = _lineup(recipient, partner)
    before = (
        recipient[2].digits.copy(),
        partner[2].digits.copy(),
        lineup.partner_tile.copy(),
        lineup.match_codes.copy(),
    )
    reading = read_conjunction(recipient[2], partner[2], lineup)
    np.testing.assert_array_equal(recipient[2].digits, before[0])
    np.testing.assert_array_equal(partner[2].digits, before[1])
    np.testing.assert_array_equal(lineup.partner_tile, before[2])
    np.testing.assert_array_equal(lineup.match_codes, before[3])
    assert not reading.codes.flags.writeable


def test_every_code_is_in_its_vocabulary_and_none_carries_a_tissue_word() -> None:
    recipient, partner = _recipient(), _partner()
    present = read_conjunction(recipient[2], partner[2], _lineup(recipient, partner))
    silent = read_conjunction(
        recipient[2],
        partner[2],
        _lineup(recipient, partner, without_recipient_geometry=True),
    )
    for reading in (present, silent):
        assert reading.code in CONJUNCTION_RECORD_CODES
        assert set(reading.codes.ravel().tolist()) <= set(range(len(CONJUNCTION_CODES)))
        assert len(reading.counts) == len(CONJUNCTION_CODES)
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
