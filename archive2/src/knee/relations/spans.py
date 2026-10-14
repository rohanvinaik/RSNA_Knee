"""Round 3: the spans between the big objects outside every interstice, and the fluid-like envelope around them.

**Why it exists, against the settled record.** Once the objects and the spaces between them are
resolved, "the roles that are still unassigned in the visual field are a lot easier to figure
out, since they're definitionally NOT the things you already DO know how to resolve" (the
founder, 2026-10-11). Two kinds remain that the twelve findings read (the design's glosses: the
ligament on the inner side; the fluid-filled envelope of the joint, its pouch behind the knee):
a span, a dark body on both acquisitions that reaches both big objects outside any interstice;
and the envelope, the connected body of fluid-like tiles (bright on the fat-dark acquisition's
own reading) that touches an interstice, with its posterior pouch and the neck joining them.
Both are named by what they touch and where they lie, never by anatomy.

**The rules, at tile scale, on one chosen slice.** A span is a four-connected body of
`below_below` tiles, none inside any interstice's extent, that is four-adjacent to the
`superior_big` territory and to the `inferior_big` territory; `span_code` names each candidate
body. The envelope is the four-connected component of tiles whose own digit (the recipient's
`TileDigits`) reads `above` and that is four-adjacent to any interstice's extent; its posterior
pouch is its tiles posterior (LPS +y) of both big objects' most posterior tile centres; the neck
is the narrowest row of the envelope, counted in tiles, between the pouch and the rest;
`pouch_code` names it.

This is the funnel's operation 9 (`openspec/changes/the-funnel/design.md` R9, tasks 9.1 to
9.3). The pure decisions are `span_code` and `pouch_code`; `read_spans` and `read_envelope` are
orchestrations.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage

from knee.collapse.first_lens import FOUR_CONNECTED
from knee.compute.contracts import handed_on
from knee.lenses.conjunction import CONJUNCTION_CODES, Conjunction
from knee.lenses.places import CODE_VALUES, DIGIT_VALUES
from knee.lenses.tiles import TileDigits
from knee.objects.selection import ObjectRecord, Selection
from knee.objects.tile_dome import TileDome
from knee.relations.interstice import InterstitialRecord, side_code
from knee.telemetry import ledger

#: What one dark body outside the interstices is to the spans.
SPAN_CODES: tuple[str, ...] = (
    "span",
    "touches_one",
    "touches_none",
    "inside_interstice",
    "invalid_measurement",
)

#: What the envelope's posterior part is.
POUCH_CODES: tuple[str, ...] = ("pouch", "no_pouch", "invalid_measurement")

#: What a slice's spans and its envelope report as wholes.
SPANS_RECORD_CODES: tuple[str, ...] = ("present", "no_candidate", "predecessor_absent")
ENVELOPE_CODES: tuple[str, ...] = ("present", "no_fluid_like", "predecessor_absent")


def span_code(
    touches_first: bool, touches_second: bool, inside_interstice: bool
) -> str:
    """Whether one dark body is a span between the two big objects (pure -- pinned).

    `touches_first`, `touches_second`: the body is four-adjacent to the superior and the inferior
    big territory; `inside_interstice`: any tile of it lies in an interstice's extent. A value
    that is not a bool is "invalid_measurement". Inside an interstice is "inside_interstice",
    whatever it touches (it is that interstice's content, not a span). Touching both is "span";
    one, "touches_one"; neither, "touches_none".

    post: __return__ in SPAN_CODES
    """
    if not all(
        isinstance(v, bool) for v in (touches_first, touches_second, inside_interstice)
    ):
        return "invalid_measurement"
    if inside_interstice:
        return "inside_interstice"
    if touches_first and touches_second:
        return "span"
    if touches_first or touches_second:
        return "touches_one"
    return "touches_none"


def pouch_code(pouch_tiles: int, neck_tiles: int) -> str:
    """Whether the envelope has a posterior pouch (pure -- pinned).

    `pouch_tiles`: how many envelope tiles lie posterior of both big objects' posterior faces;
    `neck_tiles`: the narrowest row joining them to the rest, 0 when they are the whole envelope
    or disconnected. A count that is not a non-negative int is "invalid_measurement". No pouch
    tile is "no_pouch"; else "pouch", with the neck width kept as a reading beside it.

    post: __return__ in POUCH_CODES
    """
    for value in (pouch_tiles, neck_tiles):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return "invalid_measurement"
    return "pouch" if pouch_tiles > 0 else "no_pouch"


@dataclass(frozen=True, slots=True)
class Span:
    """One dark body outside the interstices: its tiles, its code, its side."""

    index: int
    tiles: np.ndarray
    centre_lps: np.ndarray
    code: str
    side_code: str


@dataclass(frozen=True, slots=True)
class Spans:
    """Every candidate dark body of one chosen slice, each named; nothing dropped.

    `code` from `SPANS_RECORD_CODES`: `present` when at least one body was examined,
    `no_candidate` when no `below_below` tile lies outside every interstice, `predecessor_absent`
    when the conjunction, the selection or the interstices were not present (no interstice
    `present` on the slice: without one, a body inside a space cannot be told from a span).
    `border`: the dome's border word (`knee.objects.tile_dome.BORDER_CODES`) the slice's objects
    were read under.
    """

    series_uid: str
    slice_index: int
    code: str
    why: str
    spans: tuple[Span, ...]
    border: str


@dataclass(frozen=True, slots=True)
class Envelope:
    """The fluid-like body touching the interstices, with its posterior pouch and neck.

    `tiles`: bool (TR, TC); `pouch_tiles`: bool (TR, TC), the posterior part; `pouch_count`,
    `neck_tiles`: ints; `pouch_code` from `POUCH_CODES`. `unjoined`: bool (TR, TC), every
    fluid-like component that touches no present interstice's extent, kept beside the envelope
    and never merged into it (task 9.2: a posterior component with no connection is kept as a
    separate record). `code` from `ENVELOPE_CODES`: `present`; `no_fluid_like` when no `above`
    tile touches an interstice; `predecessor_absent` when the tile digits, the selection or the
    interstices were not present. `border`: the dome's border word the slice's objects were read
    under.
    """

    series_uid: str
    slice_index: int
    code: str
    why: str
    tiles: np.ndarray
    pouch_tiles: np.ndarray
    pouch_count: int
    neck_tiles: int
    pouch_code: str
    unjoined: np.ndarray
    border: str


def read_spans(
    conjunction: Conjunction | None,
    selection: Selection,
    interstices: tuple[InterstitialRecord, ...],
    dome: TileDome,
    centres_lps: np.ndarray,
    lateral_sign: str,
) -> Spans:
    """Every dark body outside the interstices, named by what it touches (orchestration).

    Records the consumption of the conjunction (only when handed over), the selection, the
    interstices and the dome at the point of reading. No conjunction, a selection or dome not
    present, or no interstice `present` among those handed over, gives `predecessor_absent` (the
    class docstring's rule: without a space, a body inside one cannot be told from a span). The
    record carries the selection's border. Else the four-connected bodies of `below_below` tiles at
    this slice; for each, `span_code` from its adjacency to the `superior_big` and `inferior_big`
    territories (the dome's labels of the two objects the selection so named; with no such pair
    every body is `touches_none`) and whether any tile of it lies in an interstice's extent;
    `side_code` (`knee.relations.interstice.side_code`) from its centre's left-right offset from
    the pair's centre and `lateral_sign`. Arrays frozen. Then records `spans.produced` (spans: how
    many are `span`). Decides nothing beyond the two decisions.

    What the above leaves open, and how it is read. The bodies are indexed 1.. in the scan order
    of each body's first tile; every body is kept, whatever its code, so nothing is dropped. The
    pair's centre is the midpoint of the two big objects' centres (their `TerritoryFacts`); with
    no such pair there is no centre to take an offset from, and a body's side is the named
    silence `side_abstained`, never a refusal. `no_candidate` is the record's word when no
    `below_below` tile lies outside every interstice's extent, including when there is no
    `below_below` tile at all; the bodies that lie inside are still listed, each
    `inside_interstice`. Only a `present` interstice contributes an extent. Records that cannot
    be one slice's (a conjunction of another series or without this slice, a dome or an
    interstice of another slice or border, a grid that is not the dome's, a big object the
    selection names that the dome has no tile of) are refused by name, `spans_inputs_disagree`,
    after their consumption is recorded and before anything is produced.
    """
    # The consumer records what it read at the point of reading (`specs/route-composition`): a
    # record handed over is named, and the count says whether it held a reading. A conjunction
    # that is None was not produced for this series and is never named.
    if conjunction is not None:
        ledger.record(
            "conjunction.consumed_by.spans",
            conjunction=1 if conjunction.code == "present" else 0,
        )
    ledger.record(
        "selection.consumed_by.spans", selection=1 if selection.code == "present" else 0
    )
    ledger.record(
        "interstice.consumed_by.spans",
        interstices=sum(1 for item in interstices if item.code == "present"),
    )
    ledger.record(
        "tile_dome.consumed_by.spans", dome=1 if dome.code == "present" else 0
    )
    reading = _read_spans(
        conjunction, selection, interstices, dome, centres_lps, lateral_sign
    )
    ledger.record(
        "spans.produced", spans=sum(1 for body in reading.spans if body.code == "span")
    )
    return reading


def read_envelope(
    digits: TileDigits,
    selection: Selection,
    interstices: tuple[InterstitialRecord, ...],
    centres_lps: np.ndarray,
    *,
    dome: TileDome | None = None,
) -> Envelope:
    """The fluid-like body touching the interstices, with its pouch and neck (orchestration).

    Records the consumption of the digits, the selection and the interstices at the point of
    reading. A digit record not present, a selection not present, or no interstice `present`,
    gives `predecessor_absent`. Else the tiles whose own digit at this slice is +1 (`above`),
    their four-connected components, and the union of those components four-adjacent to any
    `present` interstice's extent is the envelope (`no_fluid_like` when none). The pouch is its
    tiles whose centre's LPS y exceeds both big objects' most posterior tile-centre y (with no
    big pair, no pouch); the neck is the smallest number of envelope tiles in any tile row
    between the pouch's most anterior row and the rest's most posterior row, 0 when they do not
    both exist; `pouch_code` names it. Arrays frozen. Then records `envelope.produced` (tiles:
    the envelope's count). Decides nothing beyond `pouch_code`.

    What the above leaves open, and how it is read. The big objects' "most posterior tile-centre
    y" needs their tiles, and neither the selection (a tile count and an anterior face per
    territory) nor the interstices carry them; the keyword `dome`, the slice's `TileDome`, is
    beyond the four arguments for that reason, and its consumption is recorded when it is handed
    over. When the selection names the pair (`superior_big` and `inferior_big`) and no dome
    arrives the pouch cannot be read, and the call is refused by name,
    `envelope_pouch_needs_the_dome`, rather than answered `no_pouch`: a reading not made is
    never a zero. "A tile row" is the line of tiles across whichever grid axis carries the
    centres' LPS y (the sagittal's grid columns, the axial's rows), measured from `centres_lps`
    and never assumed from the plane's name; the lines are ordered by their mean y, and the neck
    counts the whole envelope's tiles on each line from the pouch's most anterior line to the
    rest's most posterior line, both ends included, counting only the envelope's components that
    hold both a pouch tile and a rest tile, so a pouch joined to the rest by no component reads
    0. Adjacency counts overlap: an `above` tile inside an extent touches it. Records that cannot
    be one slice's (another series, slice or border among the digits, the selection, the
    interstices and the dome) are refused by name, `envelope_inputs_disagree`, after their
    consumption is recorded and before anything is produced. Components not four-adjacent to any
    extent are kept beside the envelope as `unjoined`, never merged into it, and counted in
    `why`. The record carries the selection's border.
    """
    ledger.record(
        "tile_digits.consumed_by.envelope", digits=1 if digits.code == "present" else 0
    )
    ledger.record(
        "selection.consumed_by.envelope",
        selection=1 if selection.code == "present" else 0,
    )
    ledger.record(
        "interstice.consumed_by.envelope",
        interstices=sum(1 for item in interstices if item.code == "present"),
    )
    if dome is not None:
        ledger.record(
            "tile_dome.consumed_by.envelope", dome=1 if dome.code == "present" else 0
        )
    reading = _read_envelope(digits, selection, interstices, centres_lps, dome)
    ledger.record("envelope.produced", tiles=int(np.count_nonzero(reading.tiles)))
    return reading


#: The stored index of `below_below` in a conjunction's codes, and the digit the tile digits store
#: for `above`: both read from the vocabularies that own them, never restated as a level.
_BELOW_BELOW: int = CONJUNCTION_CODES.index("below_below")
_ABOVE_DIGIT: int = int(DIGIT_VALUES[CODE_VALUES["above"]])

#: The roles whose territories a span reaches between and a pouch lies behind.
_SUPERIOR_BIG: str = "superior_big"
_INFERIOR_BIG: str = "inferior_big"


def _plural(count: int, one: str, many: str) -> str:
    """A count with its noun in the right number, for the reasons the records carry."""
    return f"{count} {one if count == 1 else many}"


def _disagreement(name: str, problems: list[str]) -> ValueError:
    """A refusal by name whose note says which records contradict one another."""
    error = ValueError(name)
    error.add_note("; ".join(problems))
    return error


def _big_pair(selection: Selection) -> tuple[ObjectRecord, ObjectRecord] | None:
    """The `superior_big` and `inferior_big` object records, or None unless the selection names both."""
    by_role: dict[str, ObjectRecord] = {}
    for record in selection.objects:
        by_role.setdefault(record.role_code, record)
    superior, inferior = by_role.get(_SUPERIOR_BIG), by_role.get(_INFERIOR_BIG)
    if superior is None or inferior is None:
        return None
    return superior, inferior


def _dilated(mask: np.ndarray) -> np.ndarray:
    """The mask and every tile four-adjacent to it (measurement): bool, newly owned.

    A body is four-adjacent to a target when it meets the target's dilation; the dilation keeps
    the target itself, so an overlap touches too.
    """
    return ndimage.binary_dilation(mask, structure=FOUR_CONNECTED)


def _centre(centres: np.ndarray, tiles: np.ndarray) -> np.ndarray:
    """The mean of the centres of a body's tiles that have one (measurement): float64 (3,), NaN where none does."""
    points = centres[tiles]
    points = points[np.isfinite(points).all(axis=1)]
    if not len(points):
        return np.full(3, np.nan, dtype=np.float64)
    return points.mean(axis=0)


def _absent_spans(selection: Selection, why: str) -> Spans:
    """The spans of a slice whose predecessors were not there to read: no body, and why."""
    return Spans(
        series_uid=selection.series_uid,
        slice_index=int(selection.slice_index),
        code="predecessor_absent",
        why=why,
        spans=(),
        border=selection.border,
    )


def _spans_problems(
    conjunction: Conjunction,
    selection: Selection,
    interstices: tuple[InterstitialRecord, ...],
    dome: TileDome,
    centres: np.ndarray,
) -> list[str]:
    """How the records handed to `read_spans` contradict one another, in words; empty when none do."""
    problems: list[str] = []
    slice_index = int(selection.slice_index)
    grid = tuple(int(size) for size in dome.labels.shape)
    codes = np.asarray(conjunction.codes)
    if len(grid) != 2 or 0 in grid:
        problems.append(f"the dome's labels {grid} are not a (TR, TC) tile grid")
    elif codes.ndim != 3 or tuple(codes.shape[1:]) != grid:
        problems.append(
            f"the conjunction's codes {tuple(codes.shape)} are not (Z, {grid[0]}, {grid[1]})"
        )
    elif not 0 <= slice_index < codes.shape[0]:
        problems.append(
            f"slice {slice_index} lies outside the conjunction's {codes.shape[0]} slices"
        )
    if tuple(centres.shape) != (*grid, 3):
        problems.append(f"the centres {tuple(centres.shape)} are not ({grid}, 3)")
    if conjunction.recipient_uid != selection.series_uid:
        problems.append("the conjunction is of another series than the selection")
    if dome.series_uid != selection.series_uid:
        problems.append("the dome is of another series than the selection")
    if dome.slice_index != slice_index:
        problems.append(
            f"the dome is of slice {dome.slice_index}, the selection of slice {slice_index}"
        )
    if dome.border != selection.border:
        problems.append(
            f"the dome is of border {dome.border}, the selection of {selection.border}"
        )
    pair = _big_pair(selection)
    if pair is not None and len(grid) == 2:
        for record in pair:
            if not (np.asarray(dome.labels) == record.index).any():
                problems.append(
                    f"territory {record.index} ({record.role_code}) has no tile in the dome"
                )
    for item in interstices:
        if item.code != "present":
            continue
        if item.series_uid != selection.series_uid:
            problems.append("an interstice is of another series than the selection")
        if item.slice_index != slice_index:
            problems.append(
                f"an interstice is of slice {item.slice_index}, the selection of {slice_index}"
            )
        if item.border != selection.border:
            problems.append(
                f"an interstice is of border {item.border}, the selection of {selection.border}"
            )
        if tuple(np.shape(item.extent)) != grid:
            problems.append(
                f"an interstice's extent {tuple(np.shape(item.extent))} is not the dome's grid {grid}"
            )
    return problems


def _read_spans(
    conjunction: Conjunction | None,
    selection: Selection,
    interstices: tuple[InterstitialRecord, ...],
    dome: TileDome,
    centres_lps: np.ndarray,
    lateral_sign: str,
) -> Spans:
    """The spans of one chosen slice: the silences first, then one decision per dark body."""
    if conjunction is None:
        return _absent_spans(
            selection,
            "no conjunction was handed over (a solitary series, or the partner of a pair), "
            "so no tile has a two-acquisition reading",
        )
    if conjunction.code != "present":
        return _absent_spans(
            selection, f"the conjunction is {conjunction.code}: {conjunction.why}"
        )
    if selection.code != "present":
        return _absent_spans(
            selection, f"the selection is {selection.code}: {selection.why}"
        )
    if dome.code != "present":
        return _absent_spans(selection, f"the dome is {dome.code}: {dome.why}")
    if not any(item.code == "present" for item in interstices):
        return _absent_spans(
            selection,
            f"no interstice is present among the {len(interstices)} handed over, so a body "
            "inside a space cannot be told from a span",
        )
    centres = np.asarray(centres_lps, dtype=np.float64)
    problems = _spans_problems(conjunction, selection, interstices, dome, centres)
    if problems:
        raise _disagreement("spans_inputs_disagree", problems)
    slice_index = int(selection.slice_index)
    below = np.asarray(conjunction.codes)[slice_index] == _BELOW_BELOW
    present = [item for item in interstices if item.code == "present"]
    inside = np.zeros(below.shape, dtype=bool)
    for item in present:
        inside |= np.asarray(item.extent, dtype=bool)
    pair = _big_pair(selection)
    superior_reach = inferior_reach = None
    pair_x = float("nan")
    if pair is not None:
        superior_reach = _dilated(dome.labels == pair[0].index)
        inferior_reach = _dilated(dome.labels == pair[1].index)
        pair_x = 0.5 * (
            float(pair[0].facts.centre_lps[0]) + float(pair[1].facts.centre_lps[0])
        )
    labelled, found = ndimage.label(below, structure=FOUR_CONNECTED)
    bodies: list[Span] = []
    for index in range(1, int(found) + 1):
        tiles = labelled == index
        centre = _centre(centres, tiles)
        touches_first = superior_reach is not None and bool(
            (tiles & superior_reach).any()
        )
        touches_second = inferior_reach is not None and bool(
            (tiles & inferior_reach).any()
        )
        bodies.append(
            Span(
                index=index,
                tiles=handed_on(tiles),
                centre_lps=handed_on(centre),
                code=span_code(
                    touches_first, touches_second, bool((tiles & inside).any())
                ),
                # With no pair there is no centre to take an offset from: a silence, not a refusal.
                side_code=side_code(float(centre[0]) - pair_x, lateral_sign)
                if pair is not None
                else "side_abstained",
            )
        )
    outside = bool((below & ~inside).any())
    tally = {
        name: sum(1 for body in bodies if body.code == name) for name in SPAN_CODES
    }
    named = ", ".join(f"{n} {name}" for name, n in tally.items() if n) or "none"
    pair_words = (
        "the selection names no superior_big and inferior_big pair, so no body can touch both"
        if pair is None
        else f"superior_big is territory {pair[0].index}, inferior_big territory {pair[1].index}"
    )
    lead = (
        f"{_plural(len(bodies), 'body', 'bodies')} of below_below tiles at slice "
        f"{slice_index}"
        if outside
        else (
            f"no below_below tile lies outside every interstice at slice {slice_index} "
            f"({_plural(int(np.count_nonzero(below)), 'below_below tile', 'below_below tiles')} "
            f"in {_plural(len(bodies), 'body', 'bodies')})"
        )
    )
    return Spans(
        series_uid=selection.series_uid,
        slice_index=slice_index,
        code="present" if outside else "no_candidate",
        why=(
            f"{lead}: {named}; {pair_words}; "
            f"{_plural(len(present), 'present interstice', 'present interstices')}"
        ),
        spans=tuple(bodies),
        border=selection.border,
    )


def _absent_envelope(
    digits: TileDigits, selection: Selection, centres: np.ndarray, why: str
) -> Envelope:
    """The envelope of a slice whose predecessors were not there to read: no tile, and why."""
    grid = (
        (int(centres.shape[0]), int(centres.shape[1])) if centres.ndim == 3 else (0, 0)
    )
    return Envelope(
        series_uid=digits.series_uid,
        slice_index=int(selection.slice_index),
        code="predecessor_absent",
        why=why,
        tiles=handed_on(np.zeros(grid, dtype=bool)),
        pouch_tiles=handed_on(np.zeros(grid, dtype=bool)),
        pouch_count=0,
        neck_tiles=0,
        pouch_code=pouch_code(0, 0),
        unjoined=handed_on(np.zeros(grid, dtype=bool)),
        border=selection.border,
    )


def _envelope_problems(
    digits: TileDigits,
    selection: Selection,
    present: list[InterstitialRecord],
    centres: np.ndarray,
    pair: tuple[ObjectRecord, ObjectRecord] | None,
    dome: TileDome | None,
) -> list[str]:
    """How the records handed to `read_envelope` contradict one another, in words; empty when none do."""
    if centres.ndim != 3 or centres.shape[2] != 3 or 0 in centres.shape[:2]:
        return [f"the centres {tuple(centres.shape)} are not a (TR, TC, 3) tile grid"]
    problems: list[str] = []
    slice_index = int(selection.slice_index)
    grid = (int(centres.shape[0]), int(centres.shape[1]))
    values = np.asarray(digits.digits)
    if values.ndim != 3 or tuple(values.shape[1:]) != grid:
        problems.append(
            f"the digits {tuple(values.shape)} are not (Z, {grid[0]}, {grid[1]})"
        )
    elif not 0 <= slice_index < values.shape[0]:
        problems.append(
            f"slice {slice_index} lies outside the digits' {values.shape[0]} slices"
        )
    if digits.series_uid != selection.series_uid:
        problems.append("the digits are of another series than the selection")
    for item in present:
        if item.series_uid != selection.series_uid:
            problems.append("an interstice is of another series than the selection")
        if item.slice_index != slice_index:
            problems.append(
                f"an interstice is of slice {item.slice_index}, the selection of {slice_index}"
            )
        if item.border != selection.border:
            problems.append(
                f"an interstice is of border {item.border}, the selection of {selection.border}"
            )
        if tuple(np.shape(item.extent)) != grid:
            problems.append(
                f"an interstice's extent {tuple(np.shape(item.extent))} is not the tile grid {grid}"
            )
    if dome is not None:
        # A dome handed over must be this slice's whether or not a pouch is read from it: the
        # series, the slice and the border are checked first; the grid and the big territories
        # only matter to a pouch, so only a big pair asks for them below.
        if dome.series_uid != selection.series_uid:
            problems.append("the dome is of another series than the selection")
        if dome.slice_index != slice_index:
            problems.append(
                f"the dome is of slice {dome.slice_index}, the selection of slice {slice_index}"
            )
        if dome.border != selection.border:
            problems.append(
                f"the dome is of border {dome.border}, the selection of {selection.border}"
            )
    if pair is None or dome is None:
        return problems
    if dome.code != "present":
        problems.append(
            f"the selection names the big pair but the dome is {dome.code}: {dome.why}"
        )
        return problems
    if tuple(dome.labels.shape) != grid:
        problems.append(
            f"the dome's labels {tuple(dome.labels.shape)} are not the tile grid {grid}"
        )
        return problems
    for record in pair:
        heights = centres[..., 1][dome.labels == record.index]
        if not np.isfinite(heights).any():
            problems.append(
                f"territory {record.index} ({record.role_code}) has no tile with a centre in the dome"
            )
    return problems


def _posterior_face_mm(
    dome: TileDome, pair: tuple[ObjectRecord, ObjectRecord], centres: np.ndarray
) -> float:
    """The most posterior tile-centre LPS y of the two big objects together (measurement), in millimetres.

    The larger of the two objects' own maxima, over the tiles of their territories that have a
    centre; the caller has checked that each has one.
    """
    heights = centres[..., 1]
    faces = []
    for record in pair:
        own = heights[dome.labels == record.index]
        faces.append(float(own[np.isfinite(own)].max()))
    return max(faces)


def _posterior_axis(heights: np.ndarray) -> int | None:
    """The grid axis along which the tile centres' LPS y changes most (measurement).

    0 when it changes most from row to row, 1 from column to column; None when it changes
    nowhere that two neighbouring tiles both have a centre. Measured from the centres and never
    assumed from the plane's name: on the real sagittal grid y runs along the columns (about 7.9
    mm a tile, against about 1 mm along the rows), on the axial along the rows.
    """
    steps = []
    for axis in (0, 1):
        near, far = (
            (heights[1:], heights[:-1])
            if axis == 0
            else (heights[:, 1:], heights[:, :-1])
        )
        both = np.isfinite(near) & np.isfinite(far)
        gaps = np.abs(np.where(both, near, 0.0) - np.where(both, far, 0.0))
        steps.append(float(gaps[both].mean()) if both.any() else 0.0)
    if max(steps) <= 0.0:
        return None
    return 0 if steps[0] >= steps[1] else 1


def _neck_tiles(tiles: np.ndarray, pouch: np.ndarray, heights: np.ndarray) -> int:
    """The fewest envelope tiles on any line between the pouch and the rest (measurement).

    Only the envelope's four-connected components that hold both a pouch tile and a rest tile
    are counted: a pouch that no component joins to the rest reads 0 (the checker of
    2026-10-13 caught a disconnected pouch reading a neck). A line is the tiles across the grid
    axis that carries y (`_posterior_axis`); the lines are ordered by their mean y. From the
    pouch's most anterior line to the rest's most posterior line, both ends included, each line
    counts the joining components' tiles on it, and the fewest is the neck. 0 as well when the
    pouch or the rest is empty, or y changes nowhere.
    """
    rest = tiles & ~pouch
    axis = _posterior_axis(heights)
    if axis is None or not pouch.any() or not rest.any():
        return 0
    components, _ = ndimage.label(tiles, structure=FOUR_CONNECTED)
    joining = np.intersect1d(components[pouch], components[rest])
    joining = joining[joining > 0]
    if not joining.size:
        return 0
    joined = np.isin(components, joining)
    tiles, pouch, rest = tiles & joined, pouch & joined, rest & joined
    across = 1 - axis
    known = np.isfinite(heights)
    on_line = known.sum(axis=across)
    line_y = np.where(
        on_line > 0,
        np.where(known, heights, 0.0).sum(axis=across) / np.maximum(on_line, 1),
        np.nan,
    )
    pouch_lines = np.flatnonzero(pouch.any(axis=across))
    rest_lines = np.flatnonzero(rest.any(axis=across))
    rest_lines = rest_lines[np.isfinite(line_y[rest_lines])]
    if not rest_lines.size:
        return 0
    anterior_pouch = int(pouch_lines[np.argmin(line_y[pouch_lines])])
    posterior_rest = int(rest_lines[np.argmax(line_y[rest_lines])])
    low, high = sorted((anterior_pouch, posterior_rest))
    return int(tiles.sum(axis=across)[low : high + 1].min())


def _read_envelope(
    digits: TileDigits,
    selection: Selection,
    interstices: tuple[InterstitialRecord, ...],
    centres_lps: np.ndarray,
    dome: TileDome | None,
) -> Envelope:
    """The envelope of one chosen slice: the silences first, then the components that touch an interstice."""
    centres = np.asarray(centres_lps, dtype=np.float64)
    if digits.code != "present":
        return _absent_envelope(
            digits,
            selection,
            centres,
            f"the tile digits are {digits.code}: {digits.why}",
        )
    if selection.code != "present":
        return _absent_envelope(
            digits,
            selection,
            centres,
            f"the selection is {selection.code}: {selection.why}",
        )
    present = [item for item in interstices if item.code == "present"]
    if not present:
        return _absent_envelope(
            digits,
            selection,
            centres,
            f"no interstice is present among the {len(interstices)} handed over, so the "
            "envelope has nothing to touch",
        )
    pair = _big_pair(selection)
    if pair is not None and dome is None:
        error = ValueError("envelope_pouch_needs_the_dome")
        error.add_note(
            "the selection names superior_big and inferior_big, whose most posterior "
            "tile-centre y needs their tiles, and no dome was handed over"
        )
        raise error
    problems = _envelope_problems(digits, selection, present, centres, pair, dome)
    if problems:
        raise _disagreement("envelope_inputs_disagree", problems)
    slice_index = int(selection.slice_index)
    above = np.asarray(digits.digits)[slice_index] == _ABOVE_DIGIT
    components, found = ndimage.label(above, structure=FOUR_CONNECTED)
    extent = np.zeros(above.shape, dtype=bool)
    for item in present:
        extent |= np.asarray(item.extent, dtype=bool)
    joined = np.unique(components[_dilated(extent) & above])
    tiles = np.isin(components, joined) & above
    components_words = (
        f"{_plural(int(np.count_nonzero(above)), 'above tile', 'above tiles')} in "
        f"{_plural(int(found), 'component', 'components')}, {int(joined.size)} "
        "four-adjacent to or inside a present interstice's extent"
    )
    if not joined.size:
        return Envelope(
            series_uid=digits.series_uid,
            slice_index=slice_index,
            code="no_fluid_like",
            why=f"no above tile touches an interstice at slice {slice_index}: {components_words}",
            tiles=handed_on(tiles),
            pouch_tiles=handed_on(np.zeros(above.shape, dtype=bool)),
            pouch_count=0,
            neck_tiles=0,
            pouch_code=pouch_code(0, 0),
            unjoined=handed_on(above & ~tiles),
            border=selection.border,
        )
    pouch = np.zeros(above.shape, dtype=bool)
    face = None
    if pair is not None and dome is not None:
        face = _posterior_face_mm(dome, pair, centres)
        heights = centres[..., 1]
        known = np.isfinite(heights)
        pouch = tiles & known & (np.where(known, heights, -np.inf) > face)
    neck = _neck_tiles(tiles, pouch, centres[..., 1])
    count = int(np.count_nonzero(pouch))
    if face is None:
        pouch_words = "the selection names no superior_big and inferior_big pair, so no pouch is read"
    else:
        pouch_words = (
            f"the big objects' most posterior tile centre is at y {face:.1f} mm; "
            f"behind it, {_plural(count, 'tile', 'tiles')} of the envelope; "
            f"neck, {_plural(neck, 'tile', 'tiles')}"
        )
        if selection.plane_kind == "Coronal":
            pouch_words += (
                "; this is a Coronal slice, posterior runs through its plane, so tile-centre "
                "y here follows only the plane's tilt"
            )
    return Envelope(
        series_uid=digits.series_uid,
        slice_index=slice_index,
        code="present",
        why=(
            f"envelope of {_plural(int(np.count_nonzero(tiles)), 'tile', 'tiles')} at slice "
            f"{slice_index}: {components_words}; kept beside the envelope as unjoined: "
            f"{_plural(int(found) - int(joined.size), 'component', 'components')}; "
            f"{pouch_words}"
        ),
        tiles=handed_on(tiles),
        pouch_tiles=handed_on(pouch),
        pouch_count=count,
        neck_tiles=neck,
        pouch_code=pouch_code(count, neck),
        unjoined=handed_on(above & ~tiles),
        border=selection.border,
    )


__all__ = [
    "ENVELOPE_CODES",
    "POUCH_CODES",
    "SPANS_RECORD_CODES",
    "SPAN_CODES",
    "Envelope",
    "Span",
    "Spans",
    "pouch_code",
    "read_envelope",
    "read_spans",
    "span_code",
]
