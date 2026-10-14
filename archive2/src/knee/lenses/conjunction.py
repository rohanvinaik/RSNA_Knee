"""The conjunction: the two acquisitions of one plane, read together at each tile, as one named code.

**Why it exists, against the thesis.** "Two lenses at about one depth read one plane two ways, and
each corrects the other's borders" (§5.4); the meaning is in the conjunction, not in either lens
alone (§1.3: I(X; Y1, Y2) = I(X; Y1) + I(X; Y2 | Y1)); "truth is assigned by concurrence" (§5.4).
The founder, 2026-10-12: "fat-dark vs fat-bright? These aren't independent views. These two are
basically "lenses" that are given to us for free, by the competition itself." And 2026-10-13, on
how the two pictures meet: "the squint is how you make it cheap, you just kinda...line it up.
That's all ... It's the same fucking image, just sorta scootch it a bit, and you're good." The
settled record (`docs/OBJECT_MODEL.md`): a tissue class is a conjunction of digits across
acquisitions, never a threshold on one image; the digits stay separate and a question reads the
conjunction. The design's glosses (which ordered pair is fat, which is fluid-like, which is the
dark line) live in the design and in `OBJECT_MODEL.md`, never here: the nine codes are named by
their digits and carry no tissue word.

**The rule.** The line-up (`knee.collapse.lineup`) names, for each tile of the recipient (the
fat-dark series), the partner (fat-bright) tile at the same place on the knee and the partner
slice. The code at a tile is the ordered pair (the partner tile's digit, the recipient tile's own
digit), each from `knee.lenses.tiles`, as `<partner word>_<own word>` over below, at and above:
`above_below` is a tile bright on the fat-bright and dark on the fat-dark. A silence on either
side is named as such, the recipient's own first. Where the line-up named no partner tile there is
nothing to read together: `unmatched`.

**The distance is a reading, not a refusal.** The founder, 2026-10-13, confirming with "Good."
the lead's restatement: "The two coronal pictures are of one knee; where the narrower picture ends
there is no second reading, and where its tiles overlap the other's they are the same place. The
half-a-tile bar is my invention. The distance is a reading to keep; refusing the overlap on it was
never your rule." So a tile whose line-up word is `matched` OR `beyond_half_tile` reads the named
partner tile; only `partner_unavailable` (no partner tile named) is `unmatched`. The line-up's
distance and word stay on its own record for anyone to consult.

This is the funnel's operation 3c (`openspec/changes/the-funnel/design.md` R3c, tasks 3c.1 and
3c.2). The pure decision is `conjunction_code`; `read_conjunction` is orchestration over the
line-up's indices and the two digit records, and `conjoin` is the vectorised measurement that
carries the contract.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from knee.collapse.lineup import MATCH_CODES, LineUp
from knee.compute.contracts import ComputeContract, contracted, handed_on
from knee.lenses.places import SILENT
from knee.lenses.tiles import TileDigits
from knee.telemetry import ledger

#: Every code a tile's conjunction takes, in the order stored as uint8. The first nine are the
#: ordered pairs `<partner>_<own>`; then the two silences; then the tile with no partner tile;
#: then the refusal. None carries a tissue word.
CONJUNCTION_CODES: tuple[str, ...] = (
    "below_below",
    "below_at",
    "below_above",
    "at_below",
    "at_at",
    "at_above",
    "above_below",
    "above_at",
    "above_above",
    "partner_silent",
    "self_silent",
    "unmatched",
    "invalid_measurement",
)

#: The nine codes that carry a reading on both sides.
READ_CONJUNCTIONS: tuple[str, ...] = CONJUNCTION_CODES[:9]

#: The codes a pair's conjunction reports as a whole.
CONJUNCTION_RECORD_CODES: tuple[str, ...] = ("present", "predecessor_absent")

#: A digit's word, by the stored value `knee.lenses.places.DIGIT_VALUES` gives it.
DIGIT_WORDS: dict[int, str] = {-1: "below", 0: "at", 1: "above"}

#: The line-up words under which a partner tile was named and can be read together with the
#: recipient's: the founder's ruling of 2026-10-13 keeps the distance as a reading only.
READABLE_MATCHES: tuple[str, ...] = ("matched", "beyond_half_tile")


def conjunction_code(partner_digit: int, own_digit: int, match: str) -> str:
    """The two acquisitions' digits at one tile, read together, as one code (pure -- pinned).

    `partner_digit` is the fat-bright partner tile's digit and `own_digit` the fat-dark recipient
    tile's, each -1, 0 or +1 for below, at or above, and 2 for a silence, as the tile digits store
    them; `match` is the line-up's word for the tile (`knee.collapse.lineup.MATCH_CODES`).

    A digit that is a bool, not an int, or outside {-1, 0, 1, 2}, or a `match` that is not a
    line-up word, is "invalid_measurement": a refusal, which outranks every silence. A `match`
    under which no partner tile was named (`partner_unavailable`, or the line-up's own
    `invalid_measurement`) is "unmatched": there is nothing to read together. Then the
    recipient's own silence is named first, "self_silent"; then the partner's, "partner_silent";
    else the ordered pair `<partner word>_<own word>`. Both `matched` and `beyond_half_tile`
    read: the distance is a reading kept on the line-up, never a refusal here.

    post: __return__ in CONJUNCTION_CODES
    """
    if (
        isinstance(partner_digit, bool)
        or isinstance(own_digit, bool)
        or not isinstance(partner_digit, int)
        or not isinstance(own_digit, int)
        or partner_digit not in (-1, 0, 1, SILENT)
        or own_digit not in (-1, 0, 1, SILENT)
        or not isinstance(match, str)
        or match not in MATCH_CODES
    ):
        return "invalid_measurement"
    if match not in READABLE_MATCHES:
        return "unmatched"
    if own_digit == SILENT:
        return "self_silent"
    if partner_digit == SILENT:
        return "partner_silent"
    return f"{DIGIT_WORDS[partner_digit]}_{DIGIT_WORDS[own_digit]}"


CONTRACT = ComputeContract(
    kind="measurement",
    language="NumPy fancy indexing and a table lookup; no twin",
    reads="own digits int8 (TR, TC), partner digits int8 (TR', TC'), partner_tile int64 "
    "(TR, TC, 2), match codes uint8 (TR, TC) of one slice pair",
    writes="conjunction codes uint8 (TR, TC)",
    allocation="one (TR, TC) int8 scratch for the gathered partner digits and one uint8 output",
    work="one gather over TR * TC tiles and one 4 x 4 x 4 table lookup per tile",
    parallel_unit="slice",
    reference="conjoin",
    proof_gate="tests/knee/lenses/test_conjunction.py: over a slice holding every digit on both "
    "sides and every match word, the vectorised codes equal conjunction_code applied at every "
    "tile; a partner tile index of -1 reads as unmatched; no own or partner digit is written",
)


@contracted
def conjoin(
    own_digits: np.ndarray,
    partner_digits: np.ndarray,
    partner_tile: np.ndarray,
    match_codes: np.ndarray,
) -> np.ndarray:
    """`conjunction_code` at every tile of one recipient slice at once (measurement).

    `own_digits` int8 (TR, TC): the recipient slice's digits. `partner_digits` int8 (TR', TC'):
    the partner slice's digits, the slice the line-up named. `partner_tile` int64 (TR, TC, 2):
    the partner tile's rc per recipient tile, -1 where none. `match_codes` uint8 (TR, TC) indexing
    `MATCH_CODES`. The partner digit gathered at a named tile, and `SILENT` where the index is -1
    (such a tile's match word is never a readable one, so the gather there is never read). The
    codes are the decision's own truth table, built BY CALLING `conjunction_code` over the 4 x 4
    x len(MATCH_CODES) combinations, so the vectorised map answers to the pinned scalar by
    construction. A partner tile index outside `partner_digits`' grid, or a stored match index
    outside `MATCH_CODES`, is a contradiction between records, refused by name
    (`partner_tile_outside_grid`, `match_code_unknown`). A digit grid that is not the tile
    digits' own int8 is refused by name too (`conjunction_digits_not_int8`): the partner's
    digit is gathered into an int8 scratch, as the contract allocates, and a wider or an
    unsigned grid could wrap a value the scalar refuses into one it reads. Returned uint8
    (TR, TC), frozen.

    pre: own_digits.ndim == 2 and partner_digits.ndim == 2
    pre: partner_tile.shape == own_digits.shape + (2,)
    pre: match_codes.shape == own_digits.shape
    post: __return__.shape == own_digits.shape
    post: __return__.dtype == np.dtype("uint8")
    """
    own = np.asarray(own_digits)
    partner = np.asarray(partner_digits)
    tiles = np.asarray(partner_tile)
    matches = np.asarray(match_codes)
    if own.ndim != 2 or partner.ndim != 2:
        raise ValueError("invalid_digit_grid")
    if tiles.shape != own.shape + (2,) or matches.shape != own.shape:
        raise ValueError("conjunction_grids_do_not_match")
    if any(array.dtype.kind not in "iu" for array in (own, partner, tiles, matches)):
        raise ValueError("conjunction_values_not_whole_numbers")
    # The digits are read as the tile digits store them, int8, because the gather below lands
    # in an int8 scratch: a wider or an unsigned grid is not that record, and gathering it
    # would wrap 256 to 0 and 255 to -1, a pair where the scalar refuses. Named, never read.
    if own.dtype != np.dtype(np.int8) or partner.dtype != np.dtype(np.int8):
        raise ValueError("conjunction_digits_not_int8")
    rows, columns = tiles[..., 0], tiles[..., 1]
    # A partner tile is named when both of its indices lie inside the partner's grid, and
    # unnamed when both are -1. Anything else is a contradiction between the line-up and the
    # partner's digits, refused by name rather than gathered from the wrong tile.
    unnamed = (rows == -1) & (columns == -1)
    named = (
        (rows >= 0)
        & (columns >= 0)
        & (rows < partner.shape[0])
        & (columns < partner.shape[1])
    )
    if not np.all(unnamed | named):
        raise ValueError("partner_tile_outside_grid")
    if matches.size and (
        int(matches.min()) < 0 or int(matches.max()) >= len(MATCH_CODES)
    ):
        raise ValueError("match_code_unknown")
    gathered = np.full(own.shape, SILENT, dtype=np.int8)
    gathered[named] = partner[rows[named], columns[named]]
    codes = _TRUTH_TABLE[
        _digit_index(gathered), _digit_index(own), matches.astype(np.intp)
    ]
    return handed_on(np.ascontiguousarray(codes, dtype=np.uint8))


@dataclass(frozen=True, slots=True)
class Conjunction:
    """One pair's conjunction, on the recipient's tile grid, every slice.

    `codes`: uint8 (Z, TR, TC) indexing `CONJUNCTION_CODES`, in the recipient's stack order and
    tile grid. `counts`: one integer per `CONJUNCTION_CODES` word. `code` from
    `CONJUNCTION_RECORD_CODES`: `present` when the line-up and both digit records were there to
    read, whatever they said; `predecessor_absent` when any of the three was not, with (0, 0, 0)
    codes, zero counts and `why` naming which. A solitary series has no conjunction record at all:
    the route makes one only for a recipient the line-up named.
    """

    recipient_uid: str
    partner_uid: str
    code: str
    why: str
    codes: np.ndarray
    counts: tuple[int, ...]


def read_conjunction(
    own: TileDigits, partner: TileDigits, lineup: LineUp
) -> Conjunction:
    """Read the two acquisitions together at every tile of the recipient (orchestration).

    `own` is the recipient's (fat-dark) tile digits, `partner` the fat-bright partner's, `lineup`
    the line-up from the recipient to the partner. The uids must agree (`own.series_uid ==
    lineup.recipient_uid`, `partner.series_uid == lineup.partner_uid`), else the records are
    not one pair's, refused by name, `conjunction_series_mismatch`. Records
    `tile_digits.consumed_by.conjunction` (own: 1 when `own.code` is not `predecessor_absent`,
    else 0; partner: likewise) and `lineup.consumed_by.conjunction` (lineup: 1 when
    `lineup.code` is `present`, else 0) at the point of reading. When `lineup.code` is not
    `present`, or either digit record is `predecessor_absent`, the conjunction is
    `predecessor_absent`. Else `own.codes.shape` must equal `lineup.match_codes.shape`
    (`digits_do_not_match_lineup` otherwise); per recipient slice z, `partner_slice =
    lineup.partner_slice[z]` (-1 when none: then every tile's match word is
    `partner_unavailable` and the slice reads `unmatched` throughout, with the partner digits
    taken as all silent), and `codes[z] = conjoin(own.digits[z], partner.digits[partner_slice],
    lineup.partner_tile[z], lineup.match_codes[z])`. `counts` per `CONJUNCTION_CODES`. Arrays
    frozen with `handed_on`. Then records `conjunction.produced` (read: the tiles whose code is
    one of the nine pairs). Decides nothing itself beyond applying `conjoin`.
    """
    if (
        own.series_uid != lineup.recipient_uid
        or partner.series_uid != lineup.partner_uid
    ):
        error = ValueError("conjunction_series_mismatch")
        error.add_note(
            f"digits of {own.series_uid} and {partner.series_uid} against a line-up from "
            f"{lineup.recipient_uid} to {lineup.partner_uid}: not one pair's records"
        )
        raise error
    # The consumer records what it read at the point of reading (`specs/route-composition`):
    # every record is always handed over, and each count says whether it held a reading.
    ledger.record(
        "tile_digits.consumed_by.conjunction",
        own=1 if own.code != "predecessor_absent" else 0,
        partner=1 if partner.code != "predecessor_absent" else 0,
    )
    ledger.record(
        "lineup.consumed_by.conjunction",
        lineup=1 if lineup.code == "present" else 0,
    )
    conjunction = _read_conjunction(own, partner, lineup)
    ledger.record(
        "conjunction.produced",
        read=sum(conjunction.counts[index] for index in range(len(READ_CONJUNCTIONS))),
    )
    return conjunction


#: An int outside the digit vocabulary, so the table's fifth row and column hold what the
#: decision says of a digit it does not know: the refusal. The first four are the vocabulary.
_OUTSIDE_DIGIT: int = SILENT + 1
_TABLE_DIGITS: tuple[int, ...] = (-1, 0, 1, SILENT, _OUTSIDE_DIGIT)

#: The decision's truth table, built BY CALLING `conjunction_code` over every (partner digit,
#: own digit, match word) the table indexes: the 4 x 4 x len(MATCH_CODES) combinations of the
#: vocabulary, bordered by the row and column of a digit outside it. So the vectorised map has no
#: second statement of the rule that could drift from the pinned scalar.
_TRUTH_TABLE: np.ndarray = np.array(
    [
        [
            [
                CONJUNCTION_CODES.index(conjunction_code(partner, own, match))
                for match in MATCH_CODES
            ]
            for own in _TABLE_DIGITS
        ]
        for partner in _TABLE_DIGITS
    ],
    dtype=np.uint8,
)

#: The stored index of each silence and of the refusal, for the counts a reader asks about.
_INVALID: int = CONJUNCTION_CODES.index("invalid_measurement")


def _digit_index(digits: np.ndarray) -> np.ndarray:
    """Where each stored digit sits in the truth table: -1, 0, 1 and the silence in the first
    four rows, in that order, and any other value in the fifth, which the decision refuses."""
    values = np.asarray(digits).astype(np.int64) + 1
    return np.where((values < 0) | (values > len(_TABLE_DIGITS) - 2), 4, values)


def _absent(own: TileDigits, partner: TileDigits, why: str) -> Conjunction:
    """The conjunction of a pair one of whose records was not there to read: the named silence,
    (0, 0, 0) codes and zero counts, the array frozen."""
    return Conjunction(
        recipient_uid=own.series_uid,
        partner_uid=partner.series_uid,
        code="predecessor_absent",
        why=why,
        codes=handed_on(np.empty((0, 0, 0), dtype=np.uint8)),
        counts=(0,) * len(CONJUNCTION_CODES),
    )


def _read_conjunction(
    own: TileDigits, partner: TileDigits, lineup: LineUp
) -> Conjunction:
    """The conjunction itself: the three silences first, the contradiction, then every slice."""
    if lineup.code != "present":
        return _absent(
            own,
            partner,
            f"the line-up is {lineup.code}: {lineup.why}; no tile was read together",
        )
    if own.code == "predecessor_absent":
        return _absent(
            own,
            partner,
            f"the recipient's tile digits are {own.code}: {own.why}; no tile was read "
            "together",
        )
    if partner.code == "predecessor_absent":
        return _absent(
            own,
            partner,
            f"the partner's tile digits are {partner.code}: {partner.why}; no tile was "
            "read together",
        )
    if tuple(own.codes.shape) != tuple(lineup.match_codes.shape):
        error = ValueError("digits_do_not_match_lineup")
        error.add_note(
            f"tile digits {tuple(own.codes.shape)}, line-up match codes "
            f"{tuple(lineup.match_codes.shape)}: two records of series {own.series_uid}"
        )
        raise error
    slices, tiles_down, tiles_across = (int(size) for size in own.codes.shape)
    partner_slices = int(partner.digits.shape[0])
    codes = np.empty((slices, tiles_down, tiles_across), dtype=np.uint8)
    for z in range(slices):
        nearest = int(lineup.partner_slice[z])
        if nearest == -1:
            # No partner slice named: every tile's match word is partner_unavailable, so the
            # slice reads unmatched throughout; the partner digits are taken as all silent.
            partner_digits = np.full((tiles_down, tiles_across), SILENT, dtype=np.int8)
        elif 0 <= nearest < partner_slices:
            partner_digits = partner.digits[nearest]
        else:
            error = ValueError("partner_slice_outside_digits")
            error.add_note(
                f"recipient slice {z} names partner slice {nearest}, and the partner's "
                f"digits hold {partner_slices} slices: two records of series "
                f"{partner.series_uid}"
            )
            raise error
        codes[z] = conjoin(
            own.digits[z], partner_digits, lineup.partner_tile[z], lineup.match_codes[z]
        )
    counts = tuple(
        int(np.count_nonzero(codes == index)) for index in range(len(CONJUNCTION_CODES))
    )
    read = sum(counts[index] for index in range(len(READ_CONJUNCTIONS)))
    by_word = {word: counts[index] for index, word in enumerate(CONJUNCTION_CODES)}
    return Conjunction(
        recipient_uid=own.series_uid,
        partner_uid=partner.series_uid,
        code="present",
        why=(
            f"{slices} recipient slices of {tiles_down} x {tiles_across} tiles read together "
            f"with the partner's digits at the line-up's partner tiles: {read} tiles carry one "
            f"of the nine pairs, {by_word['self_silent']} self_silent, "
            f"{by_word['partner_silent']} partner_silent, {by_word['unmatched']} unmatched, "
            f"{counts[_INVALID]} invalid_measurement"
        ),
        codes=handed_on(codes),
        counts=counts,
    )


__all__ = [
    "CONJUNCTION_CODES",
    "CONJUNCTION_RECORD_CODES",
    "CONTRACT",
    "DIGIT_WORDS",
    "READABLE_MATCHES",
    "READ_CONJUNCTIONS",
    "Conjunction",
    "conjoin",
    "conjunction_code",
    "read_conjunction",
]
