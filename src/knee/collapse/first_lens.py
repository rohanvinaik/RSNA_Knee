"""The first lens: background versus leg, per tile, per view, frozen once it is right.

**Why it exists, against the thesis.** Stage 1, the black, "removes from each lens's picture what
is knowably not signal ... where it fires it is right, and there it decides alone" (§5.2); "A
narrow lens speaks rarely, and is knowably correct where it speaks, so there it settles. Its
silence settles nothing" (§1.11); "Stage 1 deletes nothing" (§5.2); "Where a lens's stage 1/2
clears a place, that lens spends no full analysis there" (§7.3). The founder, 2026-10-12: "On
image 2, already, we can CLEANLY see most of the noise cleanly subtracted out ... We need to
actually fix this lens to work on all five images, but once it's good like this for all of them,
we should NEVER spend a SECOND of compute on this ever again." On its authority: "The thing that
grants the first lens the "authority" to declare background is "being correct" ... when it works
and only finds things that aren't bones or other anatomical features, then it works and we use
it." And 2026-10-13, on a tile that straddles the skin line: "a lil bit of extra compute
requirement, some buffer, is perfectly fine."

**The rule, at tile scale.** A tile is background when every pixel in it lies at or below the
series' own split (the first valley past the air's spike in the whole volume's histogram,
`RegimeKey.background_split`) AND it connects to the picture's border through such tiles within
its slice: air touches the frame, a dark interior does not. A tile that is only partly dark and
sits beside the air, or on the border, is undecided: it stays in play. Every other tile is
not_background, a dark interior included: the lens found no air there and says nothing more.
The decision is per tile; the measurement before it is the connectivity.

**The third word.** It was "leg" until 2026-10-13. The founder agreed that day that the word said
more than the lens measured ("The word 'leg' is mine and says more than the lens measured; what
the lens leaves is simply 'not background', and that is what everything after it works on":
"Good."), under his law that a category's name never outruns its warrant. The stored index did not
change, so a record made under `first-lens-v1` reads the same.

**What it does not do.** It does not clear a tile it is unsure of; later operations receive every
tile not declared background (the Codex correction of 2026-10-13: an abstention is not a clearing).
It reads one series alone. Its correctness is checked by the founder's eye on each of the five
views (task 2.4, E1); a view that fails gets its own rule, declared before it is written.

This is the funnel's operation 2 (`openspec/changes/the-funnel/design.md` R2, task 2.1). The pure
decision is `tile_code`; `read_first_lens` is orchestration over the connectivity measurement.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage

from knee.collapse.squint_stack import SquintStack
from knee.compute.contracts import ComputeContract, contracted, handed_on
from knee.telemetry import ledger

#: Every code a tile takes. The order is the uint8 value stored in `FirstLens.codes`.
TILE_CODES: tuple[str, ...] = (
    "background",
    "not_background",
    "undecided",
    "tile_empty",
)

#: The codes a series' first lens reports as a whole.
LENS_CODES: tuple[str, ...] = ("present", "split_unavailable", "predecessor_absent")

#: The rule's version, kept in the record so a frozen reading says which rule made it.
RULE_VERSION: str = "first-lens-v1"


def tile_code(
    finite: bool,
    all_dark: bool,
    any_dark: bool,
    air_connected: bool,
    beside_air: bool,
) -> str:
    """What one tile is to the first lens, as a named code (pure -- pinned).

    `finite`: the tile holds at least one finite pixel. `all_dark`: every finite pixel lies at or
    below the split. `any_dark`: at least one does. `air_connected`: the tile is all dark and
    reaches the picture's border through all-dark tiles (the measurement establishes this; a tile
    that is not all dark is never air-connected). `beside_air`: the tile is four-adjacent to an
    air-connected tile, or lies on the picture's border.

    A tile with no finite pixel is "tile_empty". An all-dark tile connected to the border is
    "background": air, which the lens clears, and where it fires it is right. A partly dark tile
    beside the air is "undecided": it may hold a sliver of skin, so it stays in play. Everything
    else is "not_background": a fully bright tile, a partly dark tile away from the air, and an
    all-dark tile that does not reach the border, which is a dark interior and not air. The lens
    found no air there; what the tile holds is for later readings to say.

    post: __return__ in TILE_CODES
    """
    if not finite:
        return "tile_empty"
    if all_dark and air_connected:
        return "background"
    if any_dark and not all_dark and beside_air:
        return "undecided"
    return "not_background"


CONTRACT = ComputeContract(
    kind="measurement",
    language="NumPy with SciPy's label for the connectivity; no twin",
    reads="all_dark bool (Z, TR, TC)",
    writes="air_connected bool (Z, TR, TC) and beside_air bool (Z, TR, TC)",
    allocation="two bool arrays of the tile grid's shape",
    work="one four-connected labelling per slice over TR * TC tiles, plus one dilation",
    parallel_unit="slice",
    reference="air_connectivity",
    proof_gate="tests/knee/collapse/test_first_lens.py: a dark ring enclosing a dark centre marks "
    "the ring air-connected only where it touches the border and never the enclosed centre; a "
    "border tile is beside air whether or not any tile is dark",
)


@contracted
def air_connectivity(all_dark: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Which all-dark tiles reach the picture's border, and which tiles lie beside them (measurement).

    Per slice, four-connected components of `all_dark`; a component touching any of the four
    borders of the tile grid is air-connected. `beside_air` is true for a tile four-adjacent to an
    air-connected tile, and for every tile on the grid's border. Both returned as bool (Z, TR, TC).

    pre: all_dark.ndim == 3
    post: __return__[0].shape == all_dark.shape and __return__[1].shape == all_dark.shape
    """
    dark = np.asarray(all_dark, dtype=bool)
    if dark.ndim != 3:
        raise ValueError("invalid_all_dark")
    slices, tiles_down, tiles_across = (int(size) for size in dark.shape)
    air = np.zeros(dark.shape, dtype=bool)
    beside = np.zeros(dark.shape, dtype=bool)
    if tiles_down and tiles_across:
        # The grid's border: the first and last tile rows and columns. A component that holds
        # any of these tiles reaches the picture's edge, which is where the air comes in.
        border = np.zeros((tiles_down, tiles_across), dtype=bool)
        border[0, :] = border[-1, :] = True
        border[:, 0] = border[:, -1] = True
        for z in range(slices):
            labels, count = ndimage.label(dark[z], structure=FOUR_CONNECTED)
            if count:
                touching = np.unique(labels[border])
                air[z] = np.isin(labels, touching[touching > 0])
            # One four-neighbour dilation reaches every tile that shares an edge with an
            # air-connected tile; the border is beside the air whether or not any tile is dark.
            beside[z] = (
                ndimage.binary_dilation(air[z], structure=FOUR_CONNECTED) | border
            )
    return handed_on(air), handed_on(beside)


#: The four-neighbourhood within a slice: a tile touches the four tiles it shares an edge with,
#: never a corner. The same structure labels the all-dark tiles and dilates the air by one tile.
FOUR_CONNECTED: np.ndarray = np.array(
    [[False, True, False], [True, True, True], [False, True, False]], dtype=bool
)


@dataclass(frozen=True, slots=True)
class FirstLens:
    """One series' first lens: every tile of every slice named, under one split and one rule.

    `codes`: uint8 (Z, TR, TC) indexing `TILE_CODES`. `counts`: the number of tiles under each code,
    in `TILE_CODES` order. `split`: the series' own valley the rule read, NaN when none.
    `rule_version`: `RULE_VERSION`. `code` is from `LENS_CODES`: `present` when the lens read the
    stack; `split_unavailable` when the regime gave no finite split, in which case every tile is
    `not_background` and nothing is cleared; `predecessor_absent` when the stack was not present.
    `why` says which. The record is frozen once made: every later operation reads it from the
    saved run.
    """

    series_uid: str
    code: str
    why: str
    split: float
    rule_version: str
    codes: np.ndarray
    counts: tuple[int, int, int, int]


def read_first_lens(stack: SquintStack, split: float) -> FirstLens:
    """Name every tile of a series background, leg or undecided under its own split (orchestration).

    When `stack.code` is not `present` the lens is `predecessor_absent` with empty codes. When
    `split` is not finite the lens is `split_unavailable`: every tile with a finite pixel is
    `not_background`, empty tiles `tile_empty`, and nothing is cleared, because a lens with no
    valley to read has no authority to declare air. Else: `finite = isfinite(stack.coverage) &
    (coverage > 0)`; `all_dark = stack.maximum <= split` (false where not finite); `any_dark =
    stack.minimum <= split`; `air_connected, beside_air = air_connectivity(all_dark)`;
    `codes[z, i, j] = TILE_CODES.index(tile_code(finite, all_dark, any_dark, air_connected,
    beside_air))`, which is vectorised by evaluating the decision on the four bool grids. Counts
    are taken over every slice. Arrays frozen with `handed_on`. Records
    `squint_stack.consumed_by.first_lens` and `first_lens.produced` (background, not_background,
    undecided counts) on the ledger. Decides nothing itself beyond applying `tile_code` at every
    tile.
    """
    # The consumer records what it read at the point of reading (`specs/route-composition`):
    # the stack is always handed over, and the count says whether it held a reading.
    ledger.record(
        "squint_stack.consumed_by.first_lens",
        stack=1 if stack.code == "present" else 0,
    )
    lens = _read_first_lens(stack, _split_value(split))
    ledger.record(
        "first_lens.produced",
        background=lens.counts[_BACKGROUND],
        not_background=lens.counts[_NOT_BACKGROUND],
        undecided=lens.counts[_UNDECIDED],
    )
    return lens


#: The stored index of each tile code, so a tile's code is one byte in the record.
_BACKGROUND: int = TILE_CODES.index("background")
_NOT_BACKGROUND: int = TILE_CODES.index("not_background")
_UNDECIDED: int = TILE_CODES.index("undecided")
_TILE_EMPTY: int = TILE_CODES.index("tile_empty")


def _split_value(split: object) -> float:
    """The split as a float: a number that is not a bool, else NaN, which is no valley at all."""
    if isinstance(split, bool) or not isinstance(split, (int, float, np.number)):
        return float("nan")
    return float(split)


def _counts(codes: np.ndarray) -> tuple[int, int, int, int]:
    """How many tiles, over every slice, carry each code, in `TILE_CODES` order."""
    return (
        int(np.count_nonzero(codes == _BACKGROUND)),
        int(np.count_nonzero(codes == _NOT_BACKGROUND)),
        int(np.count_nonzero(codes == _UNDECIDED)),
        int(np.count_nonzero(codes == _TILE_EMPTY)),
    )


def _finite_tiles(stack: SquintStack) -> np.ndarray:
    """Which tiles hold at least one finite pixel: a finite coverage above zero, bool (Z, TR, TC)."""
    coverage = np.asarray(stack.coverage, dtype=np.float64)
    return np.isfinite(coverage) & (coverage > 0.0)


def _tile_codes(stack: SquintStack, split: float) -> np.ndarray:
    """`tile_code` at every tile at once: the same truth table over the four bool grids.

    `finite`, `all_dark`, `any_dark`, `air_connected` and `beside_air` are the grids; the
    assignments below are the decision's clauses in its own order, so the vectorised map and the
    scalar rule say one thing (the proof gate checks them against each other tile by tile).
    """
    finite = _finite_tiles(stack)
    maximum = np.asarray(stack.maximum, dtype=np.float64)
    minimum = np.asarray(stack.minimum, dtype=np.float64)
    all_dark = finite & (maximum <= split)
    any_dark = finite & (minimum <= split)
    air_connected, beside_air = air_connectivity(all_dark)
    codes = np.full(finite.shape, _NOT_BACKGROUND, dtype=np.uint8)
    codes[~finite] = _TILE_EMPTY
    codes[finite & all_dark & air_connected] = _BACKGROUND
    codes[finite & any_dark & ~all_dark & beside_air] = _UNDECIDED
    return codes


def _read_first_lens(stack: SquintStack, split: float) -> FirstLens:
    """The lens itself: the two silences first, then the decision at every tile."""
    if stack.code != "present":
        return FirstLens(
            series_uid=stack.series_uid,
            code="predecessor_absent",
            why=f"the squint stack is {stack.code}: {stack.why}; no tile was named",
            split=split,
            rule_version=RULE_VERSION,
            codes=handed_on(np.empty((0, 0, 0), dtype=np.uint8)),
            counts=(0, 0, 0, 0),
        )
    slices, tiles_down, tiles_across = (int(size) for size in stack.median.shape)
    if not np.isfinite(split):
        # No valley to read: the lens has no authority to declare air, so every tile with a
        # finite pixel stays in play as not_background and nothing is cleared. No connectivity
        # is read.
        finite = _finite_tiles(stack)
        codes = np.where(finite, _NOT_BACKGROUND, _TILE_EMPTY).astype(np.uint8)
        counts = _counts(codes)
        return FirstLens(
            series_uid=stack.series_uid,
            code="split_unavailable",
            why=(
                "the regime gave no finite split, so the lens has no valley to read and "
                "clears nothing: every tile with a finite pixel is not_background "
                f"({counts[_NOT_BACKGROUND]} of {slices} x {tiles_down} x {tiles_across})"
            ),
            split=split,
            rule_version=RULE_VERSION,
            codes=handed_on(codes),
            counts=counts,
        )
    codes = _tile_codes(stack, split)
    counts = _counts(codes)
    return FirstLens(
        series_uid=stack.series_uid,
        code="present",
        why=(
            f"{slices} slices of {tiles_down} x {tiles_across} tiles named under split "
            f"{split:g} by {RULE_VERSION}: {counts[_BACKGROUND]} background, "
            f"{counts[_NOT_BACKGROUND]} not_background, {counts[_UNDECIDED]} undecided, "
            f"{counts[_TILE_EMPTY]} empty"
        ),
        split=split,
        rule_version=RULE_VERSION,
        codes=handed_on(codes),
        counts=counts,
    )
