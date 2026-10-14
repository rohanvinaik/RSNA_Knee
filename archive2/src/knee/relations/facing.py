"""The facing pairs: which selected objects face each other across gap tiles.

**Why it exists, against the thesis and the settled record.** "An interstice is constructed, not
detected: it exists the moment its two bounding objects do" (`docs/OBJECT_MODEL.md`). The
founder, 2026-10-11: "Interstitial space...is the space between the two bones we resolve as
objects! That's LITERALLY what the term means." The first plan had no producer for the pairs an
interstice is built between; the Codex consult of 2026-10-13 proved the gap, and this is the
producer. Two objects face when there are gap tiles, obstacle tiles of the dome, touching both,
with no third object between them along those tiles; two objects that touch with no gap tile
between them are named so, and not faced.

**The rule, at tile scale.** For each pair of territories that carry a role other than
`unselected` on one chosen slice: the sites are the four-adjacent tile crossings between the two
territories (`knee.objects.boundaries.boundary_census` and `knee.objects.interiors.boundary_edges`
on the tile labels, read whole); the gap tiles are the DARK obstacle tiles (an obstacle of the
dome that the first lens did not clear: `dome.obstacle & ~dome.cleared`, never the air around
the leg) that lie between the two objects, in the region whose projection on the line joining
the two centres falls between the two territories' nearest faces and whose projection across
that line falls within the overlap of the two territories' widths, and that belong to a
four-connected component of such tiles touching both territories, so a space two or three tiles
wide still counts and the cleared air never does (the Codex check of 2026-10-13 caught the
contract's first wording, a single tile touching both); `saddle_mm` is the smallest dome height
along the gap tiles; the decision names the pair.

This is the funnel's operation 7 (`openspec/changes/the-funnel/design.md` R7, tasks 7.1 and
7.2). The pure decision is `facing_code`; `read_facing` is orchestration.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import combinations

import numpy as np
from scipy import ndimage

from knee.compute.contracts import handed_on
from knee.objects.boundaries import boundary_census
from knee.objects.interiors import boundary_edges
from knee.objects.selection import Selection
from knee.objects.tile_dome import TileDome
from knee.telemetry import ledger

#: What one pair of objects is to the relations stage.
FACING_CODES: tuple[str, ...] = (
    "facing",
    "touching_no_gap",
    "not_selected",
    "too_few_sites",
    "invalid_measurement",
)

#: What one slice's facing pairs report as a whole.
FACING_RECORD_CODES: tuple[str, ...] = ("present", "no_pair", "predecessor_absent")


def facing_code(
    sites: int, gap_sites: int, minimum_sites: int, both_selected: bool
) -> str:
    """Whether two objects face across a gap (pure -- pinned).

    `sites` is how many tile crossings join the two territories directly (they touch there);
    `gap_sites` how many gap tiles lie between them (every tile of the dark chains the module
    docstring keeps, each chain touching both; a space two or three tiles wide counts every tile
    of it); `minimum_sites` the bar on `gap_sites` (an argument; the founder changes it);
    `both_selected` whether both carry a role. A count that is
    not a non-negative int, a bar that is not one, or a `both_selected` that is not a bool, is
    "invalid_measurement". Not both selected is "not_selected": an unselected territory is never
    in a facing pair. Gap sites at or above the bar is "facing", whatever the direct sites.
    Below the bar, direct sites above zero is "touching_no_gap"; none of either is
    "too_few_sites".

    post: __return__ in FACING_CODES
    """
    if (
        isinstance(sites, bool)
        or isinstance(gap_sites, bool)
        or isinstance(minimum_sites, bool)
        or not isinstance(sites, int)
        or not isinstance(gap_sites, int)
        or not isinstance(minimum_sites, int)
        or sites < 0
        or gap_sites < 0
        or minimum_sites < 0
        or not isinstance(both_selected, bool)
    ):
        return "invalid_measurement"
    if not both_selected:
        return "not_selected"
    if gap_sites >= minimum_sites and gap_sites > 0:
        return "facing"
    if sites > 0:
        return "touching_no_gap"
    return "too_few_sites"


@dataclass(frozen=True, slots=True)
class FacingPair:
    """One pair of objects on one chosen slice: their indices, the code, and the gap between them.

    `first`, `second`: the two territories' labels, `first < second`. `first_role`,
    `second_role`: their role codes. `sites`, `gap_sites`: the counts the decision read.
    `gap_tiles`: bool (TR, TC), the dark tiles between the two objects as the module docstring
    defines them. `saddle_mm`: the least dome height over the gap tiles, NaN when none.
    """

    first: int
    second: int
    first_role: str
    second_role: str
    code: str
    sites: int
    gap_sites: int
    gap_tiles: np.ndarray
    saddle_mm: float


@dataclass(frozen=True, slots=True)
class FacingPairs:
    """Every pair of selected objects on one chosen slice, each with its code; nothing dropped.

    `code` from `FACING_RECORD_CODES`: `present` when at least one pair was examined, `no_pair`
    when fewer than two objects carry a role, `predecessor_absent` when the dome or the selection
    was not present. `border`: the dome's border word (`knee.objects.tile_dome.BORDER_CODES`)
    the pairs were read under.
    """

    series_uid: str
    slice_index: int
    code: str
    why: str
    minimum_sites: int
    pairs: tuple[FacingPair, ...]
    border: str


def read_facing(
    dome: TileDome, selection: Selection, minimum_sites: int
) -> FacingPairs:
    """Every pair of selected objects on one slice, faced or named otherwise (orchestration).

    `minimum_sites` that is not a non-negative int is refused by name before any ledger event,
    and so is a dome and a selection that are not of one series, one slice and one border
    (`facing_inputs_disagree`). The record carries the dome's border. Records
    `tile_dome.consumed_by.facing` (dome: 1 when `present`) and
    `selection.consumed_by.facing` (selection: 1 when `present`) at the point of reading. Either
    not present gives `predecessor_absent`; fewer than two roled objects gives `no_pair`. Else
    for every pair of territories with a role other than `unselected`, in ascending label order:
    the direct sites by `boundary_census`/`boundary_edges` over the dome's labels (read both
    whole; the same crossings the native census counts, over tiles), the gap tiles as the module
    docstring defines them (the between-region from the two territories' tile centres in the
    grid, the dark obstacles `dome.obstacle & ~dome.cleared`, the four-connected components of
    those within the region, those touching both territories), `gap_sites` their count,
    `saddle_mm` the least `dome.height` over them, and `facing_code`.
    Arrays frozen. Then records `facing.produced` (pairs: how many are `facing`). Decides nothing
    beyond applying `facing_code`.
    """
    # The refusal comes first, before any ledger event. `type(...) is not int` refuses a bool,
    # which is an int in Python, and a NumPy integer, as `boundary_census` refuses its own bar.
    if type(minimum_sites) is not int or minimum_sites < 0:
        raise ValueError("invalid_minimum_sites")
    # A selection is read from one dome: another series, slice or border is a wiring error.
    if (
        selection.series_uid != dome.series_uid
        or selection.slice_index != dome.slice_index
        or selection.border != dome.border
    ):
        raise ValueError("facing_inputs_disagree")
    # The consumer records what it read at the point of reading: both records are always handed
    # over, and the count says whether each held a reading.
    ledger.record(
        "tile_dome.consumed_by.facing", dome=1 if dome.code == "present" else 0
    )
    ledger.record(
        "selection.consumed_by.facing",
        selection=1 if selection.code == "present" else 0,
    )
    facing = _read_facing(dome, selection, minimum_sites)
    ledger.record(
        "facing.produced",
        pairs=sum(1 for pair in facing.pairs if pair.code == "facing"),
    )
    return facing


#: The four-neighbourhood within the tile grid: a tile touches the four tiles it shares an edge
#: with, never a corner. The same structure labels the candidate gap tiles into components.
_FOUR_CONNECTED: np.ndarray = ndimage.generate_binary_structure(2, 1)


def _read_facing(
    dome: TileDome, selection: Selection, minimum_sites: int
) -> FacingPairs:
    """The record itself: the two silences first, then every pair of roled territories.

    A dome or a selection whose code is not `present` is `predecessor_absent`, naming which; the
    record then takes the dome's series and slice, since a selection is made from a dome and the
    dome is the one that locates the slice. Fewer than two territories with a role is `no_pair`.
    """
    absent = [
        f"the {name} is {record.code}"
        for name, record in (("tile dome", dome), ("selection", selection))
        if record.code != "present"
    ]
    if absent:
        return FacingPairs(
            series_uid=dome.series_uid,
            slice_index=dome.slice_index,
            code="predecessor_absent",
            why="; ".join(absent) + "; no pair was examined",
            minimum_sites=minimum_sites,
            pairs=(),
            border=dome.border,
        )
    roles = {int(record.index): record.role_code for record in selection.objects}
    roled = sorted(label for label, role in roles.items() if role != "unselected")
    if len(roled) < 2:
        return FacingPairs(
            series_uid=dome.series_uid,
            slice_index=dome.slice_index,
            code="no_pair",
            why=(
                f"{len(roled)} of {len(roles)} territories carry a role; a pair needs "
                "two, so no pair was examined"
            ),
            minimum_sites=minimum_sites,
            pairs=(),
            border=dome.border,
        )
    pairs = _read_pairs(dome, roles, roled, minimum_sites)
    counts = {
        code: sum(1 for pair in pairs if pair.code == code) for code in FACING_CODES
    }
    return FacingPairs(
        series_uid=dome.series_uid,
        slice_index=dome.slice_index,
        code="present",
        why=(
            f"pairs examined: {len(pairs)}, among {len(roled)} roled territories, under "
            f"a bar of {minimum_sites} gap tiles; "
            + ", ".join(f"{count} {code}" for code, count in counts.items() if count)
        ),
        minimum_sites=minimum_sites,
        pairs=pairs,
        border=dome.border,
    )


def _read_pairs(
    dome: TileDome, roles: dict[int, str], roled: list[int], minimum_sites: int
) -> tuple[FacingPair, ...]:
    """Every pair of roled territories, in ascending label order, each named by `facing_code`.

    The direct sites are the census's own count of four-adjacent tile crossings between the two
    territories, read from `boundary_edges` and `boundary_census` over the dome's labels: at tile
    scale an obstacle is the measured dark across an edge and a tile that is neither an obstacle
    nor an interior is the missing acquisition, the metric is the identity (the grid is square in
    millimetres). The gap tiles are `_gap_tiles` for the pair; `saddle_mm` is the least
    `dome.height` over them, NaN when there are none. Every count is a plain int and every height
    a plain float, because `facing_code` refuses a NumPy scalar.
    """
    labels = np.asarray(dome.labels)
    obstacle = np.asarray(dome.obstacle, dtype=bool)
    interior = np.asarray(dome.interior, dtype=bool)
    dark = obstacle & ~np.asarray(dome.cleared, dtype=bool)
    _, _, regions, kinds = boundary_edges(
        labels, obstacle, obstacle | interior, np.eye(2)
    )
    census = boundary_census(labels, dome.height, regions, kinds, minimum_sites)
    sites = {
        (int(low), int(high)): int(count)
        for (low, high), count in zip(
            census.pair_labels, census.pair_sites, strict=True
        )
    }
    held = {label: labels == label for label in roled}
    beside = {label: _beside(mask) for label, mask in held.items()}
    pairs = []
    for first, second in combinations(roled, 2):
        gap = _gap_tiles(dark, held[first], held[second], beside[first], beside[second])
        gap_sites = int(np.count_nonzero(gap))
        both_selected = roles[first] != "unselected" and roles[second] != "unselected"
        direct = sites.get((first, second), 0)
        pairs.append(
            FacingPair(
                first=first,
                second=second,
                first_role=roles[first],
                second_role=roles[second],
                code=facing_code(direct, gap_sites, minimum_sites, both_selected),
                sites=direct,
                gap_sites=gap_sites,
                gap_tiles=handed_on(gap),
                saddle_mm=float(np.min(dome.height[gap])) if gap_sites else math.nan,
            )
        )
    return tuple(pairs)


def _beside(mask: np.ndarray) -> np.ndarray:
    """The tiles four-adjacent to a tile of `mask` (measurement).

    `mask` bool (TR, TC), tile rows then tile columns on the squint stack's grid; returns a newly
    owned bool (TR, TC) on the same grid. A tile on the frame has no neighbour beyond it: the
    grid does not wrap. A tile of `mask` is itself marked only when another tile of `mask` is
    four-adjacent to it.
    """
    beside = np.zeros(mask.shape, dtype=bool)
    beside[1:, :] |= mask[:-1, :]
    beside[:-1, :] |= mask[1:, :]
    beside[:, 1:] |= mask[:, :-1]
    beside[:, :-1] |= mask[:, 1:]
    return beside


def between_region(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    """The tiles between two territories along the line joining their centres (measurement).

    Public because the interstice's extent is built by the same rule
    (`knee.relations.interstice`), so the facing gap and the extent cannot drift apart.

    `first`, `second` bool (TR, TC): the two territories' tiles on one grid, tile rows then tile
    columns, with tile (row, column) as the tile's position in grid units. The line is the one
    from the first territory's centre (the mean of its tile positions) to the second's. A tile is
    between when its projection on that line lies strictly between the first territory's most
    advanced tile and the second's least advanced one (their nearest faces), and its projection
    across the line lies within the overlap of the two territories' extents across it, ends
    included. Exact: the line is held as the integer vector between the centres scaled by the
    product of the two tile counts, so every projection is a whole number and no tolerance is
    needed. Returns a newly owned bool (TR, TC), all False when either territory holds no tile,
    when the two centres coincide, when the faces do not leave room between them, or when the
    extents across the line do not overlap.
    """
    rows_first, columns_first = np.nonzero(first)
    rows_second, columns_second = np.nonzero(second)
    count_first, count_second = len(rows_first), len(rows_second)
    nowhere = np.zeros(first.shape, dtype=bool)
    if not count_first or not count_second:
        return nowhere
    axis_row = (
        int(rows_second.sum()) * count_first - int(rows_first.sum()) * count_second
    )
    axis_column = (
        int(columns_second.sum()) * count_first
        - int(columns_first.sum()) * count_second
    )
    if axis_row == 0 and axis_column == 0:
        return nowhere
    row, column = np.indices(first.shape, dtype=np.int64)
    along = row * axis_row + column * axis_column
    across = column * axis_row - row * axis_column
    low = max(across[first].min(), across[second].min())
    high = min(across[first].max(), across[second].max())
    return (
        (along > along[first].max())
        & (along < along[second].min())
        & (across >= low)
        & (across <= high)
    )


def _gap_tiles(
    dark: np.ndarray,
    first: np.ndarray,
    second: np.ndarray,
    first_beside: np.ndarray,
    second_beside: np.ndarray,
) -> np.ndarray:
    """The gap between two territories: the dark chains between them that touch both (measurement).

    `dark` bool (TR, TC): the obstacle tiles the first lens did not clear. `first`, `second`: the
    two territories' tiles. `first_beside`, `second_beside`: the tiles four-adjacent to each
    (`_beside`). The candidates are the dark tiles in `between_region` of the two territories;
    they are labelled into four-connected components, and a component is kept when it holds a
    tile beside each territory, so a space two or three tiles wide counts, a cleared tile never
    does, and a third territory standing between the two cuts the chain. Returns a newly owned
    bool (TR, TC).
    """
    candidates = dark & between_region(first, second)
    components, _ = ndimage.label(candidates, structure=_FOUR_CONNECTED)
    keep = np.intersect1d(
        components[first_beside & candidates], components[second_beside & candidates]
    )
    return np.isin(components, keep) & candidates


__all__ = [
    "FACING_CODES",
    "FACING_RECORD_CODES",
    "FacingPair",
    "FacingPairs",
    "between_region",
    "facing_code",
    "read_facing",
]
