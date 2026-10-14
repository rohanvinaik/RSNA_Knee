"""The tile digits: every tile the first lens kept, against the terciles of its own series' kept tiles.

**Why it exists, against the thesis.** The static middle (§7.2): a place reads below, at or above
a pair of edges read from a structurally selected population, never an absolute level. The
founder's ruling of 2026-10-11 on the edges: "the middle is two tercile edges; both edges belong
to the middle row" (`chapters/03-lenses/teachings.md`, carried by `knee.lenses.digits`). The
squint makes the reading cheap (§4.5): "Reduced to the median light of each 16 × 16 square, a
crowded plate still shows where its cells mass and where its ground is dark." The founder,
2026-10-13, asked whether the terciles over the leg tiles, and then over each object's own places,
are the local normalisation he meant: "Yup, that should do." And the same day, on which tiles the
thirds are read over, the lead's restatement he confirmed with "Good.": "They are read over
everything the lens did not clear. A handful of dark corner tiles among ten thousand barely moves
a third's edge, and whatever they do to it is information to look at, not a reason to stall." On
the undecided tiles at the skin: "They stay in play. 'Some buffer is perfectly fine.' Only what was
cleared is never read again."

**The rule.** The population is the median of every tile, of every slice of the series, that the
first lens did not clear (`not_background` and `undecided`; `background` and `tile_empty` are out)
and whose median is finite. The edges are `knee.collapse.regime.tercile_edges(population,
minimum_population)`, the one tercile rule the regime already applies to its own populations
(task 3b.1 makes it public; `read_regime`'s terciles are byte-identical before and after). The
digits are `knee.lenses.places.place_codes_reference` over the medians with every tile outside
the population set to NaN, so a cleared or empty tile reads `place_unread` (silence, stored as 2)
and never a digit; `digits = DIGIT_VALUES[codes]` as the native lenses store theirs. The scalar
oracle is `knee.lenses.digits.digit_code`, pinned, which this module never re-states.

**What it does not do.** No absolute level, no normalisation across series, no tissue word. It
reads one series alone; the two acquisitions of a plane meet only in the conjunction (operation
3c). It never recomputes a median: the squint stack is the one source.

This is the funnel's operation 3b (`openspec/changes/the-funnel/design.md` R3b, tasks 3b.1 to
3b.3). The pure decision is `tile_population_code`; `population_mask` is the measurement and
carries the contract; `read_tile_digits` is orchestration.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from knee.collapse.first_lens import TILE_CODES, FirstLens
from knee.collapse.regime import tercile_edges
from knee.collapse.squint_stack import SquintStack
from knee.compute.contracts import ComputeContract, contracted, handed_on
from knee.lenses.digits import DIGIT_CODES, digit_code
from knee.lenses.places import CODE_VALUES, DIGIT_VALUES, place_codes_reference
from knee.telemetry import ledger

#: Whether one tile of the first lens enters the terciles' population.
POPULATION_CODES: tuple[str, ...] = ("counted", "cleared", "empty", "unknown_code")

#: The codes a series' tile digits report as a whole. `present` when the edges read and every
#: tile is named; `no_edges` and `population_too_small` are the digit oracle's own silences for a
#: population that gave no pair; `invalid_measurement` its refusal; `predecessor_absent` when the
#: stack or the first lens was not there to read.
TILE_DIGIT_CODES: tuple[str, ...] = (
    "present",
    "no_edges",
    "population_too_small",
    "invalid_measurement",
    "predecessor_absent",
)

#: The smallest population the terciles are read over: `RegimeKey.tercile_minimum_population`'s
#: declared default, the bar the regime reads its own terciles under (design §3,
#: `minimum_population`); the founder changes it. The route hands the regime's own value when a
#: regime was read and this when none was.
DEFAULT_MINIMUM_POPULATION: int = 8


def tile_population_code(tile_code: str) -> str:
    """Whether one tile enters the population the terciles are read over (pure -- pinned).

    `tile_code` is the first lens's word for the tile (`knee.collapse.first_lens.TILE_CODES`).
    A tile the lens did not clear is "counted": `not_background`, and `undecided`, which the
    founder keeps in play ("some buffer is perfectly fine"). A `background` tile is "cleared":
    never read again. A `tile_empty` tile is "empty": it has no median to count. Any other word
    is "unknown_code": a record written under a rule this module does not know, named and never
    counted.

    post: __return__ in POPULATION_CODES
    """
    if tile_code == "not_background" or tile_code == "undecided":
        return "counted"
    if tile_code == "background":
        return "cleared"
    if tile_code == "tile_empty":
        return "empty"
    return "unknown_code"


CONTRACT = ComputeContract(
    kind="measurement",
    language="NumPy vectorized membership and finiteness; no twin",
    reads="first-lens codes uint8 (Z, TR, TC) and squint medians float64 (Z, TR, TC)",
    writes="population mask bool (Z, TR, TC)",
    allocation="one bool array of the tile grid's shape",
    work="one membership test and one finiteness test over Z * TR * TC tiles",
    parallel_unit="slice",
    reference="population_mask",
    proof_gate="tests/knee/lenses/test_tiles.py: a grid holding every tile code marks exactly "
    "the not_background and undecided tiles with a finite median, and never a background, empty "
    "or NaN-median tile; the mask equals tile_population_code applied at every tile",
)


@contracted
def population_mask(codes: np.ndarray, median: np.ndarray) -> np.ndarray:
    """Which tiles the terciles are read over: counted by the lens's word, with a finite median.

    `codes` is the first lens's uint8 (Z, TR, TC) indexing `TILE_CODES`; `median` the squint
    stack's float64 (Z, TR, TC). The mask is `tile_population_code(TILE_CODES[code]) == "counted"`
    at every tile AND `isfinite(median)`, vectorised by evaluating the decision on the stored
    index; a stored index outside `TILE_CODES` is `unknown_code` and never counted. Returned
    bool (Z, TR, TC), frozen. Decides nothing beyond applying `tile_population_code`.

    pre: codes.ndim == 3 and median.ndim == 3
    pre: codes.shape == median.shape
    post: __return__.shape == codes.shape
    post: __return__.dtype == np.dtype("bool")
    """
    stored = np.asarray(codes)
    medians = np.asarray(median)
    if stored.ndim != 3 or medians.ndim != 3:
        raise ValueError("invalid_tile_grid")
    if stored.shape != medians.shape:
        raise ValueError("tile_grids_do_not_match")
    if stored.dtype.kind not in "iu":
        raise ValueError("invalid_tile_codes")
    # The decision, evaluated on the stored index: `_COUNTED_BY_INDEX` is
    # `tile_population_code(TILE_CODES[index]) == "counted"` for every index the lens can store,
    # built by calling the pinned scalar, so the mask answers to it by construction. An index
    # outside `TILE_CODES` is a word the module does not know, which the decision names
    # `unknown_code` and never counts; the mask is False there without looking it up.
    counted = np.zeros(stored.shape, dtype=bool)
    known = (stored >= 0) & (stored < len(TILE_CODES))
    counted[known] = _COUNTED_BY_INDEX[stored[known]]
    return handed_on(counted & np.isfinite(medians))


@dataclass(frozen=True, slots=True)
class TileDigits:
    """One series' tile digits: every tile of every slice against its own series' kept-tile edges.

    `low_edge`, `high_edge`: the terciles of the population, in the series' own stored units, NaN
    when none could be read. `population_count`: how many tiles were counted; `minimum_population`:
    the bar they were read under. `codes`: uint8 (Z, TR, TC) indexing `knee.lenses.digits.DIGIT_CODES`
    (`below`, `at`, `above`, or a silence). `digits`: int8 (Z, TR, TC), -1, 0, +1, and 2 for every
    silence, as `knee.lenses.places.DIGIT_VALUES` stores them. `counts`: one integer per
    `DIGIT_CODES` word. `code` from `TILE_DIGIT_CODES`, `why` saying which. A reading not made is
    NaN or a silence, never zero.
    """

    series_uid: str
    code: str
    why: str
    low_edge: float
    high_edge: float
    population_count: int
    minimum_population: int
    codes: np.ndarray
    digits: np.ndarray
    counts: tuple[int, ...]


def read_tile_digits(
    stack: SquintStack, first: FirstLens, minimum_population: int
) -> TileDigits:
    """Name every tile of a series against the terciles of its kept tiles (orchestration).

    `minimum_population` that is a bool, not an int, or negative is refused by name,
    `invalid_minimum_population`, before any ledger event. Records
    `squint_stack.consumed_by.tile_digits` (stack: 1 when present, else 0) and
    `first_lens.consumed_by.tile_digits` (lens: 1 when the lens's code is not
    `predecessor_absent`, else 0) at the point of reading. When `stack.code` is not `present`, or
    `first.code` is `predecessor_absent`, the digits are `predecessor_absent` with (0, 0, 0)
    arrays, NaN edges, zero counts and `why` naming which. A first lens whose `codes` shape is not
    the stack's `median` shape is a contradiction between two records of one series, refused by
    name, `first_lens_does_not_match_stack`. Else: `mask = population_mask(first.codes,
    stack.median)`; `(low, high), count = tercile_edges(stack.median[mask], minimum_population)`
    from `knee.collapse.regime` (NaN edges when the count is 0 or below the bar); `codes =
    place_codes_reference(where(mask, median, NaN), low, high, count, minimum_population)`;
    `digits = DIGIT_VALUES[codes]`; `counts` per `DIGIT_CODES`. `code` mirrors the digit oracle as
    `knee.lenses.places` does: `digit_code(NaN, low, high, count, minimum_population)` read
    `place_unread` means `present`, else its own word (`no_edges`, `population_too_small`,
    `invalid_measurement`). Arrays frozen with `handed_on`. Then records `tile_digits.produced`
    (counted: the population count; read: the tiles whose code is below, at or above). Decides
    nothing itself.
    """
    if (
        isinstance(minimum_population, bool)
        or not isinstance(minimum_population, (int, np.integer))
        or minimum_population < 0
    ):
        raise ValueError("invalid_minimum_population")
    bar = int(minimum_population)
    # The consumer records what it read at the point of reading (`specs/route-composition`):
    # both records are always handed over, and each count says whether it held a reading.
    ledger.record(
        "squint_stack.consumed_by.tile_digits",
        stack=1 if stack.code == "present" else 0,
    )
    ledger.record(
        "first_lens.consumed_by.tile_digits",
        lens=1 if first.code != "predecessor_absent" else 0,
    )
    digits = _read_tile_digits(stack, first, bar)
    ledger.record(
        "tile_digits.produced",
        counted=digits.population_count,
        read=sum(digits.counts[value] for value in _READ_VALUES),
    )
    return digits


#: The stored indices the orchestration and the mask read, so a code is one byte in the record.
_NOT_BACKGROUND: int = TILE_CODES.index("not_background")
_UNDECIDED: int = TILE_CODES.index("undecided")
_READ_VALUES: tuple[int, ...] = (
    CODE_VALUES["below"],
    CODE_VALUES["at"],
    CODE_VALUES["above"],
)

#: Whether each stored tile index is counted, BY CALLING the pinned decision on the lens's own
#: word for it, so the vectorised mask has no second statement of the rule that could drift.
_COUNTED_BY_INDEX: np.ndarray = np.array(
    [tile_population_code(word) == "counted" for word in TILE_CODES], dtype=bool
)


def _absent(series_uid: str, bar: int, why: str) -> TileDigits:
    """The digits of a series whose stack or first lens was not there to read: the named
    silence, (0, 0, 0) arrays, NaN edges and zero counts, every array frozen."""
    return TileDigits(
        series_uid=series_uid,
        code="predecessor_absent",
        why=why,
        low_edge=float("nan"),
        high_edge=float("nan"),
        population_count=0,
        minimum_population=bar,
        codes=handed_on(np.empty((0, 0, 0), dtype=np.uint8)),
        digits=handed_on(np.empty((0, 0, 0), dtype=np.int8)),
        counts=(0,) * len(DIGIT_CODES),
    )


def _read_tile_digits(stack: SquintStack, first: FirstLens, bar: int) -> TileDigits:
    """The digits themselves: the two silences first, the contradiction, then every tile."""
    if stack.code != "present":
        return _absent(
            stack.series_uid,
            bar,
            f"the squint stack is {stack.code}: {stack.why}; no tile was read",
        )
    if first.code == "predecessor_absent":
        return _absent(
            stack.series_uid,
            bar,
            f"the first lens is {first.code}: {first.why}; no tile was read",
        )
    if tuple(first.codes.shape) != tuple(stack.median.shape):
        error = ValueError("first_lens_does_not_match_stack")
        error.add_note(
            f"first lens codes {tuple(first.codes.shape)}, squint stack median "
            f"{tuple(stack.median.shape)}: two records of series {stack.series_uid}"
        )
        raise error
    mask = population_mask(first.codes, stack.median)
    low, high, count = tercile_edges(stack.median[mask], bar)
    # Every tile outside the population is handed NaN, so the oracle names it `place_unread`
    # (silence) and never a digit; the medians themselves are read, never recomputed.
    codes = place_codes_reference(
        np.where(mask, stack.median, np.nan), low, high, count, bar
    )
    digits = handed_on(DIGIT_VALUES[codes])
    counts = tuple(
        int(np.count_nonzero(codes == index)) for index in range(len(DIGIT_CODES))
    )
    probe = digit_code(float("nan"), low, high, count, bar)
    code = "present" if probe == "place_unread" else probe
    slices, tiles_down, tiles_across = (int(size) for size in stack.median.shape)
    population = (
        f"{count} of {slices * tiles_down * tiles_across} tiles counted (not_background "
        f"and undecided with a finite median) over {slices} slices of {tiles_down} x "
        f"{tiles_across}"
    )
    if code == "present":
        why = (
            f"{population}: edges {low:g} and {high:g} under a bar of {bar}; "
            f"{counts[CODE_VALUES['below']]} below, {counts[CODE_VALUES['at']]} at, "
            f"{counts[CODE_VALUES['above']]} above, "
            f"{counts[CODE_VALUES['place_unread']]} silent"
        )
    else:
        why = (
            f"{population}: the digit oracle names {probe} under a bar of {bar}, so no "
            "tile reads a digit and every tile is silent"
        )
    return TileDigits(
        series_uid=stack.series_uid,
        code=code,
        why=why,
        low_edge=low,
        high_edge=high,
        population_count=count,
        minimum_population=bar,
        codes=codes,
        digits=digits,
        counts=counts,
    )


__all__ = [
    "CONTRACT",
    "DEFAULT_MINIMUM_POPULATION",
    "DIGIT_CODES",
    "DIGIT_VALUES",
    "POPULATION_CODES",
    "TILE_DIGIT_CODES",
    "TileDigits",
    "digit_code",
    "population_mask",
    "read_tile_digits",
    "tile_population_code",
]
