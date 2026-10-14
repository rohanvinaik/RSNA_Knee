"""The dome at the squint: each object's interior rising from the obstacles around it, grounded at a peak.

**Why it exists, against the thesis.** "A center's dome is the territory of places it holds ...
Nothing is cut on strength, so a bright nucleus never silences a dim one" (§6.2). The founder, on
the knee (2026-10-11): "The difference between tibia and femur? It's the GIANT fucking gap between
them. Look into the cell tracking project for the way we resolved cells, the "dome" shape, with a
discrete fall-off in signal intensity that marks the border ... Here? We just need to figure out
the difference between two GIANT fucking objects that almost precisely split the picture right in
the middle." And on where the work runs (2026-10-12): "you only spend expensive compute to try and
find the exact boundary of things in the places where they actually look like they might exist."
So the dome is read at the squint, on the chosen slices only, inside what the first lens kept,
and the territories it gives are what the strip later refines at native resolution.

**The rule, at tile scale, and its two borders.** An obstacle is a tile the lens cleared, always.
A kept tile (`not_background` or `undecided`: the founder keeps the buffer at the skin in play,
"some buffer is perfectly fine", so it is eligible for an object's interior like any kept tile)
is an obstacle on a solitary plane when its median lies at or below the series' split. On a paired
plane the border is read one of two ways, named by `BORDER_CODES`, and both are seated:

- `dark_on_both`: a tile whose two acquisitions read `below_below` is an obstacle. This is the
  object model's recorded row, "cortex, tendon, ligament, meniscus: dark on everything"
  (`docs/OBJECT_MODEL.md`, settled with the founder 2026-10-11).
- `edge_of_bright_partner`: a tile whose fat-bright partner digit was read and is not `above` is
  an obstacle (the six read pairs `at_*` and `below_*`); the dome's interior is then the body that
  is bright on the fat-bright, and its border is where that brightness falls off.

Every silence (`partner_silent`, `self_silent`, `unmatched`) and the conjunction's own refusal
leave a kept tile interior under either border: silence settles nothing. Why two: measured on the
one study at 8 mm (`docs/chapters/02-collapse/measurements/the-funnel-dome-border-20261013.md`),
the dark line between the two big bones is narrower than a tile, so `dark_on_both` leaves them one
territory on most middle slices, while `edge_of_bright_partner` parts them on every middle slice
of both paired views. The founder's ruling of 2026-10-12 ("we always keep information we compute
... keep everything, including where things conflict") seats both as two members, and he chooses
by eye; nothing here prefers one.

The interior is every kept tile that is not an obstacle. The height of an interior tile is its
Euclidean distance in millimetres to the nearest obstacle tile or to the picture's frame; the
peaks are the interior's local maxima of height that stand at least `prominence_mm` above their
surroundings (`knee.objects.interiors.prominent_peaks`, the rule the native dome already uses);
the territories are the watershed of the height from the peaks, within the interior, every
unseeded tile 0. The obstacles, the cleared tiles, the height, the peaks and the labels are all
kept; nothing is cut on strength.

This is the funnel's operation 5 (`openspec/changes/the-funnel/design.md` R5, tasks 5.1 to 5.3).
The pure decision is `dome_tile_code`; `knee.objects.dome.dome` is the one measurement, shared
with the native interiors; `read_tile_domes` is orchestration over the depth collapse's chosen
slices, once per border.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from knee.collapse.depth import DepthCollapse
from knee.collapse.first_lens import TILE_CODES, FirstLens
from knee.collapse.squint_stack import SquintStack
from knee.compute.contracts import handed_on
from knee.lenses.conjunction import CONJUNCTION_CODES, READ_CONJUNCTIONS, Conjunction
from knee.objects.dome import dome
from knee.telemetry import ledger

#: What one tile is to the dome: interior (a place an object can hold), obstacle (a place it
#: cannot), empty (no finite pixel), or a word this rule does not know.
DOME_TILE_CODES: tuple[str, ...] = ("interior", "obstacle", "empty", "unknown_code")

#: The codes one slice's dome reports as a whole.
DOME_CODES: tuple[str, ...] = ("present", "no_interior", "predecessor_absent")

#: The two readings of a paired plane's border, both seated (see the module docstring).
BORDER_CODES: tuple[str, ...] = ("dark_on_both", "edge_of_bright_partner")

#: The read pairs whose fat-bright partner digit is not `above`: the obstacles of
#: `edge_of_bright_partner`. Derived from the conjunction's own words, never restated.
_READ_NOT_BRIGHT: tuple[str, ...] = tuple(
    word for word in READ_CONJUNCTIONS if not word.startswith("above_")
)


def dome_tile_code(
    first_code: str,
    conjunction_code: str | None,
    at_or_below_split: bool,
    border: str,
) -> str:
    """What one tile is to the dome under one border (pure -- pinned).

    `first_code` is the first lens's word for the tile; `conjunction_code` its two-acquisition
    word on a paired plane, or None on a solitary plane; `at_or_below_split` whether its median
    lies at or below the series' split (read only on a solitary plane); `border` a word of
    `BORDER_CODES`. A first word outside the first lens's vocabulary is "unknown_code".
    `tile_empty` is "empty". `background` is "obstacle" whatever else is said: the lens cleared
    it. For a kept tile (`not_background` or `undecided` alike), a border outside `BORDER_CODES`
    or a conjunction word outside its vocabulary is "unknown_code", named and never an interior.
    With no paired reading, the tile is "obstacle" when its median lies at or below the split,
    under either border. With a paired reading: under `dark_on_both` it is "obstacle" when the
    word is `below_below`; under `edge_of_bright_partner` it is "obstacle" when the word is a read
    pair whose partner digit is not `above` (`at_*` or `below_*`). Else it is "interior": every
    silence and the conjunction's own refusal leave a kept tile interior.

    post: __return__ in DOME_TILE_CODES
    """
    if first_code not in TILE_CODES:
        return "unknown_code"
    if first_code == "tile_empty":
        return "empty"
    if first_code == "background":
        return "obstacle"
    if border not in BORDER_CODES:
        return "unknown_code"
    if conjunction_code is not None and conjunction_code not in CONJUNCTION_CODES:
        return "unknown_code"
    if conjunction_code is None:
        return "obstacle" if at_or_below_split else "interior"
    if border == "dark_on_both":
        return "obstacle" if conjunction_code == "below_below" else "interior"
    return "obstacle" if conjunction_code in _READ_NOT_BRIGHT else "interior"


@dataclass(frozen=True, slots=True)
class TileDome:
    """One chosen slice's dome over the tile grid, under one border.

    `slice_index`: the stack index the depth collapse chose. `obstacle`, `interior`: bool
    (TR, TC). `cleared`: bool (TR, TC), the tiles the first lens cleared (every cleared tile is
    an obstacle; an obstacle that is not cleared is a kept tile the border names, which is what a
    gap between two objects is made of). `height`: float64 (TR, TC) mm, 0 on obstacles and outside
    the interior. `peaks`: int64 (P, 2) tile rc, in descending height; `peak_height_mm`: float64
    (P,). `labels`: int32 (TR, TC), 1..P the territory of each peak, 0 unseeded or obstacle.
    `prominence_mm`: the bar the peaks were read under. `code` from `DOME_CODES`: `present` when
    the slice holds an interior, `no_interior` when every tile is an obstacle or empty (empty
    peaks, all-zero labels), `predecessor_absent` when the stack, the lens or the depth collapse
    was not there to read (empty arrays of the right rank). A reading not made is never zero.
    `border`: the word of `BORDER_CODES` this dome was read under; every record read from a dome
    carries it on, so two domes of one slice are never confused.
    """

    series_uid: str
    slice_index: int
    code: str
    why: str
    prominence_mm: float
    obstacle: np.ndarray
    cleared: np.ndarray
    interior: np.ndarray
    height: np.ndarray
    peaks: np.ndarray
    peak_height_mm: np.ndarray
    labels: np.ndarray
    border: str


def read_tile_domes(
    stack: SquintStack,
    first: FirstLens,
    conjunction: Conjunction | None,
    depth: DepthCollapse,
    split: float,
    prominence_mm: float,
    border: str,
) -> tuple[TileDome, ...]:
    """The dome of every chosen slice of one series under one border (orchestration).

    `prominence_mm` that is not a finite positive number is refused by name,
    `invalid_prominence_mm`, and a `border` outside `BORDER_CODES` by `invalid_border`, both
    before any ledger event. Records `squint_stack.consumed_by.tile_dome` (stack: 1 when
    present), `first_lens.consumed_by.tile_dome` (lens: 1 when not `predecessor_absent`),
    `depth.consumed_by.tile_dome` (depth: 1 when `present`) and, only when `conjunction` is not
    None, `conjunction.consumed_by.tile_dome` (conjunction: 1 when `present`), each at the point
    of reading. When the stack, the lens or the depth is not present, or a conjunction handed over
    holds no reading, one `predecessor_absent` dome is returned with `slice_index` -1. Else, for
    each index in `depth.chosen_slices` in order: `tile_codes = dome_tile_code` at every tile of
    that slice under `border`, vectorised on the stored indices (the proof gate checks the map
    against the scalar); `obstacle = codes == obstacle`, `cleared = first.codes[slice] ==
    background`, `interior = codes == interior`; `height, peaks, labels =
    knee.objects.dome.dome(interior, (tile_mm, tile_mm), prominence_mm)` with the tile's
    millimetre size as the spacing; `no_interior` when no tile is interior. Every dome carries
    `border`. Arrays frozen with `handed_on`. Then records `tile_dome.produced` (slices: how many
    domes were read, 0 for the absent placeholder; peaks: the peaks over all of them). Decides
    nothing itself beyond applying `dome_tile_code`. The route calls it once per word of
    `BORDER_CODES`.
    """
    bar = _bar(prominence_mm)
    if border not in BORDER_CODES:
        raise ValueError("invalid_border")
    # The consumer records what it read at the point of reading (`specs/route-composition`): each
    # record is always handed over, and the count says whether it held a reading. The conjunction
    # is the one record that may not be handed over at all, and then nothing is recorded for it.
    ledger.record(
        "squint_stack.consumed_by.tile_dome",
        stack=1 if stack.code == "present" else 0,
    )
    ledger.record(
        "first_lens.consumed_by.tile_dome",
        lens=0 if first.code == "predecessor_absent" else 1,
    )
    ledger.record(
        "depth.consumed_by.tile_dome", depth=1 if depth.code == "present" else 0
    )
    if conjunction is not None:
        ledger.record(
            "conjunction.consumed_by.tile_dome",
            conjunction=1 if conjunction.code == "present" else 0,
        )
    domes = _tile_domes(
        stack, first, conjunction, depth, _split_value(split), bar, border
    )
    ledger.record(
        "tile_dome.produced",
        slices=sum(1 for read in domes if read.code != "predecessor_absent"),
        peaks=sum(int(read.peaks.shape[0]) for read in domes),
    )
    return domes


def _number_or_nan(value: object) -> float:
    """The value as a float when it is a number and not a bool, else NaN: no number at all."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        return float("nan")
    try:
        return float(value)
    except OverflowError:
        return float("nan")


def _bar(value: object) -> float:
    """The prominence bar as a float, or the named refusal (a bool is not a number)."""
    bar = _number_or_nan(value)
    if not np.isfinite(bar) or bar <= 0.0:
        raise ValueError("invalid_prominence_mm")
    return bar


def _split_value(split: object) -> float:
    """The split as a float: a finite number that is not a bool, else NaN, which is no valley.

    The first lens reads an infinite split as no valley too, so the two agree on what a split is.
    """
    value = _number_or_nan(split)
    return value if np.isfinite(value) else float("nan")


def _absent_reasons(
    stack: SquintStack,
    first: FirstLens,
    depth: DepthCollapse,
    conjunction: Conjunction | None,
) -> list[str]:
    """Why each predecessor was not there to read, in words; empty when all were.

    A conjunction that was handed over and made no reading is named here too: the plane is a
    paired one, so reading it by the rule a solitary plane has would be a different answer to a
    different question. Not handed over at all is a solitary plane, and no reason.
    """
    reasons: list[str] = []
    if stack.code != "present":
        reasons.append(f"the squint stack is {stack.code} ({stack.why})")
    if first.code == "predecessor_absent":
        reasons.append(f"the first lens is {first.code} ({first.why})")
    if depth.code != "present":
        reasons.append(f"the depth collapse is {depth.code} ({depth.why})")
    if conjunction is not None and conjunction.code != "present":
        reasons.append(f"the conjunction is {conjunction.code} ({conjunction.why})")
    return reasons


def _absent_dome(
    stack: SquintStack, bar: float, reasons: list[str], border: str
) -> TileDome:
    """The dome of a series with a predecessor missing: its named silence and empty arrays of rank."""
    return TileDome(
        series_uid=stack.series_uid,
        slice_index=-1,
        code="predecessor_absent",
        why="; ".join(reasons) + "; no slice was read",
        prominence_mm=bar,
        obstacle=handed_on(np.empty((0, 0), dtype=np.bool_)),
        cleared=handed_on(np.empty((0, 0), dtype=np.bool_)),
        interior=handed_on(np.empty((0, 0), dtype=np.bool_)),
        height=handed_on(np.empty((0, 0), dtype=np.float64)),
        peaks=handed_on(np.empty((0, 2), dtype=np.int64)),
        peak_height_mm=handed_on(np.empty((0,), dtype=np.float64)),
        labels=handed_on(np.empty((0, 0), dtype=np.int32)),
        border=border,
    )


def _tile_domes(
    stack: SquintStack,
    first: FirstLens,
    conjunction: Conjunction | None,
    depth: DepthCollapse,
    split: float,
    bar: float,
    border: str,
) -> tuple[TileDome, ...]:
    """The domes themselves: the silences first, the records' agreement next, then each slice."""
    reasons = _absent_reasons(stack, first, depth, conjunction)
    if reasons:
        return (_absent_dome(stack, bar, reasons, border),)
    shape = stack.median.shape
    if first.codes.shape != shape:
        raise ValueError("first_lens_does_not_match_stack")
    if conjunction is not None and conjunction.codes.shape != shape:
        raise ValueError("conjunction_does_not_match_stack")
    chosen = [int(index) for index in depth.chosen_slices]
    if any(not 0 <= index < shape[0] for index in chosen):
        raise ValueError("chosen_slice_outside_stack")
    return tuple(
        _dome_at(stack, first, conjunction, split, bar, index, border)
        for index in chosen
    )


#: The words each border's paired-plane obstacles are named by, for the record's `why`.
_BORDER_WORDS: dict[str, str] = {
    "dark_on_both": "dark on both acquisitions",
    "edge_of_bright_partner": "read on the fat-bright partner and not bright there",
}


def _dome_at(
    stack: SquintStack,
    first: FirstLens,
    pair: Conjunction | None,
    split: float,
    bar: float,
    index: int,
    border: str,
) -> TileDome:
    """One chosen slice: every tile named by `dome_tile_code`, then the one shared dome measurement."""
    words = _TILE_WORDS[
        _stored(first.codes[index], len(TILE_CODES)),
        _NO_PAIR
        if pair is None
        else _stored(pair.codes[index], len(CONJUNCTION_CODES)),
        (stack.median[index] <= split).astype(np.intp),
        BORDER_CODES.index(border),
    ]
    obstacle = words == _OBSTACLE
    cleared = first.codes[index] == _BACKGROUND
    interior = words == _INTERIOR
    height, peaks, labels = dome(interior, (stack.tile_mm, stack.tile_mm), bar)
    rule = (
        _BORDER_WORDS[border]
        if pair is not None
        else (
            f"median at or below the split {split:g}"
            if np.isfinite(split)
            else "median at or below a split that was not read, so none"
        )
    )
    interior_tiles = int(np.count_nonzero(interior))
    return TileDome(
        series_uid=stack.series_uid,
        slice_index=index,
        code="present" if interior_tiles else "no_interior",
        why=(
            f"slice {index}, border {border}: {interior_tiles} interior tiles, "
            f"{int(np.count_nonzero(obstacle))} obstacle tiles "
            f"({int(np.count_nonzero(cleared))} cleared by the first lens, the rest {rule}), "
            f"{int(np.count_nonzero(words == _EMPTY))} empty and "
            f"{int(np.count_nonzero(words == _UNKNOWN))} unnamed, of {words.shape[0]} x "
            f"{words.shape[1]}; {len(peaks)} peaks at least {bar:g} mm above their "
            f"surroundings seed {len(peaks)} territories"
        ),
        prominence_mm=bar,
        obstacle=handed_on(obstacle),
        cleared=handed_on(cleared),
        interior=handed_on(interior),
        height=height,
        peaks=peaks,
        peak_height_mm=handed_on(height[peaks[:, 0], peaks[:, 1]]),
        labels=labels,
        border=border,
    )


def _stored(codes: np.ndarray, size: int) -> np.ndarray:
    """Stored codes as table rows: a value no word stands for is the row after the last word."""
    return np.where((codes >= 0) & (codes < size), codes, size).astype(np.intp)


def _tile_word_table() -> np.ndarray:
    """`dome_tile_code` at every stored combination, as indices into `DOME_TILE_CODES`.

    The axes are the first lens's stored index (the four words, then one no word stands for), the
    conjunction's (the thirteen words, then one no word stands for, then none handed over),
    whether the median is at or below the split, and the border (the words of `BORDER_CODES`).
    Every entry is the pure decision's own answer, so the vectorised map answers to the scalar
    rule by construction.
    """
    first_words = (*TILE_CODES, "")
    pair_words: tuple[str | None, ...] = (*CONJUNCTION_CODES, "", None)
    table = np.empty(
        (len(first_words), len(pair_words), 2, len(BORDER_CODES)), dtype=np.uint8
    )
    for i, first_word in enumerate(first_words):
        for j, pair_word in enumerate(pair_words):
            for k, dark in enumerate((False, True)):
                for b, border in enumerate(BORDER_CODES):
                    table[i, j, k, b] = DOME_TILE_CODES.index(
                        dome_tile_code(first_word, pair_word, dark, border)
                    )
    return handed_on(table)


#: The stored indices the orchestration reads, so a tile's word is one byte in the record.
_INTERIOR: int = DOME_TILE_CODES.index("interior")
_OBSTACLE: int = DOME_TILE_CODES.index("obstacle")
_EMPTY: int = DOME_TILE_CODES.index("empty")
_UNKNOWN: int = DOME_TILE_CODES.index("unknown_code")
_BACKGROUND: int = TILE_CODES.index("background")
#: The conjunction axis's last row: no conjunction was handed over (a solitary plane).
_NO_PAIR: int = len(CONJUNCTION_CODES) + 1
_TILE_WORDS: np.ndarray = _tile_word_table()


__all__ = [
    "BORDER_CODES",
    "DOME_CODES",
    "DOME_TILE_CODES",
    "TileDome",
    "dome_tile_code",
    "read_tile_domes",
]
