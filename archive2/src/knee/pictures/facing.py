"""What the facing pairs resolved, drawn: each pair's gap tiles between its two objects, on the chosen slice.

The funnel's operation 7 (`openspec/changes/the-funnel/design.md` R7, task 7.2):
`knee.relations.facing.read_facing` names, on each chosen slice, every pair of territories that
carry a role, with the direct sites between them, the gap tiles that lie between them (the dark
tiles in the overlap of their widths that form a chain touching both), the saddle height over
those tiles and one named code. Its picture shows which objects the stage took to face one
another, and across what: per chosen slice, the acquired plane in grey (the squint's tile medians
where no plane was stored for the slice), the two objects of each pair in their own colours with
their indices, and the gap tiles between them, with the pair's code and saddle height written at
the gap.

Every value here is one the stage computed and the writer saved. Choosing which stored plane, or
which slice of the stack's medians, to show under a chosen slice, and handing each pair its own row
of the saved gap tiles, is ARRANGING: it selects stored values and alters none of them. A plane is
never borrowed from another slice. Nothing here measures, thresholds, dilates or recomputes a
count, a code or a height; a facing record that was not saved, a code the stage does not say, a
stage that found no pair, a stage whose predecessors were absent and a slice the stack does not
hold are each a named silence in words, never an empty picture. The one decision, `slice_standing`,
is pure and total and names what one saved slice of the picture can be.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from knee.relations.facing import FACING_RECORD_CODES

#: What one saved slice of the picture can be. `pairs_drawn` is a reading drawn: the stage
#: examined at least one pair on that slice and the slice lies inside the stack that places it.
#: The rest are the silences, each with its own remedy: this run's writer saved no facing record
#: for the series; the saved code is a word the stage does not say; the stage's dome or selection
#: was absent (its own reason is beside); the stage found fewer than two objects with a role, so
#: there was no pair to examine; the slice lies outside the slices the stack holds.
SLICE_STANDINGS: tuple[str, ...] = (
    "pairs_drawn",
    "facing_not_saved",
    "facing_code_unknown",
    "facing_absent",
    "no_pair",
    "slice_outside_stack",
)

#: Where the plane under a slice came from. `own` is a plane the facing record names for that
#: slice; `walk` is the study stage's walk, which holds the slice; `acquired` is the objects
#: stage's selected plane, which is the slice; `none` is a slice with no stored plane, drawn over
#: the squint's tile medians at the slice where the stack holds them, else on the tile grid alone.
PLANE_SOURCES: tuple[str, ...] = ("own", "walk", "acquired", "none")


def slice_standing(code: object, index: object, slices: int) -> str:
    """Name what one saved slice of the picture can show, from its saved code, slice and the stack's size.

    `code` is the slice's saved code (`FACING_RECORD_CODES`), or None when the writer saved no
    facing record for the series; `index` the stack index the stage read the slice at; `slices`
    how many slices the stack that places it holds. Total: no saved record is `facing_not_saved`;
    a code the stage does not say, or one that is not text, is `facing_code_unknown`, named and
    never drawn; a stage whose predecessors were absent is `facing_absent`; a stage that examined
    no pair is `no_pair`; an index that is not a whole number inside the stack is
    `slice_outside_stack`; else the slice is `pairs_drawn`. It selects nothing and counts nothing.

    post: __return__ in SLICE_STANDINGS
    """
    if code is None:
        return "facing_not_saved"
    if not isinstance(code, str) or code not in FACING_RECORD_CODES:
        return "facing_code_unknown"
    if code == "predecessor_absent":
        return "facing_absent"
    if code == "no_pair":
        return "no_pair"
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < slices:
        return "slice_outside_stack"
    return "pairs_drawn"


@dataclass(frozen=True, slots=True)
class PairPanel:
    """One pair of objects on one slice, as the stage saved it.

    first, second: the two territories' labels, `first < second`. first_role, second_role: their
    role codes. code: the stage's word for the pair. sites, gap_sites: the counts the stage's
    decision read. saddle_mm: the least dome height over the gap tiles, None where the stage
    saved none (no gap tile). gap_tiles: bool (tile rows, tile columns), the saved gap tiles of
    this pair. Nothing is derived.
    """

    first: int
    second: int
    first_role: str
    second_role: str
    code: str
    sites: int
    gap_sites: int
    saddle_mm: float | None
    gap_tiles: np.ndarray


@dataclass(frozen=True, slots=True)
class SlicePanel:
    """One chosen slice of the picture: its standing, and the saved values at that slice.

    index: the stack index the stage read the slice at (-1 where its dome was absent). standing:
    from `SLICE_STANDINGS`. code, why: the stage's code and reason for the slice, as saved.
    minimum_sites: the bar the stage read under. pairs: one `PairPanel` per pair, in the saved
    order, empty unless `standing` is `pairs_drawn`. labels: int32 (tile rows, tile columns), the
    dome's territories the pairs' labels name, None where the writer saved none. plane: (rows,
    columns) in the dtype it was stored in, None where none was stored for this slice.
    plane_source: from `PLANE_SOURCES`. median: float64 (tile rows, tile columns), the stack's tile
    medians at this slice, None where the stack holds no such slice. An absent value stays absent,
    never a zero. border: the word of `knee.objects.tile_dome.BORDER_CODES` the dome was read
    under, as saved; a slice read under two borders is two panels, each keyed by its border and
    its index together.
    """

    index: int
    standing: str
    code: str
    why: str
    minimum_sites: int
    pairs: tuple[PairPanel, ...]
    labels: np.ndarray | None
    plane: np.ndarray | None
    plane_source: str
    median: np.ndarray | None
    border: str


@dataclass(frozen=True, slots=True)
class FacingPanels:
    """One series' saved facing pairs, AS THE WRITER SAVED THEM, ready for the workbench to draw.

    saved: whether the series' record carries a facing record at all. bounds_rc: (tile rows, tile
    columns, 4) int64, the squint stack's saved half-open native bounds that place the tiles on a
    plane, None where none was handed on. slices: one `SlicePanel` per saved slice, in the saved
    order, empty when nothing was saved.
    """

    saved: bool
    bounds_rc: np.ndarray | None
    slices: tuple[SlicePanel, ...]


def _stored_plane(
    own: np.ndarray | None,
    index: int,
    walk_indices: Sequence[int],
    walk: np.ndarray | None,
    acquired_index: int | None,
    acquired_plane: np.ndarray | None,
) -> tuple[np.ndarray | None, str]:
    """Which stored plane lies under a slice, and where it came from: its own, the walk's, the selected plane, or none."""
    if own is not None:
        return np.asarray(own), "own"
    if walk is not None and index in walk_indices:
        return np.asarray(walk[list(walk_indices).index(index)]), "walk"
    if acquired_plane is not None and acquired_index == index:
        return np.asarray(acquired_plane), "acquired"
    return None, "none"


def facing_panels(
    entries: Sequence[Mapping[str, Any]] | None,
    gap_tiles: np.ndarray | None,
    labels: np.ndarray | None,
    own_planes: Sequence[np.ndarray | None],
    bounds_rc: np.ndarray | None,
    median: np.ndarray | None,
    walk_indices: Sequence[int],
    walk: np.ndarray | None,
    acquired_index: int | None,
    acquired_plane: np.ndarray | None,
) -> FacingPanels:
    """Hand on one series' saved facing pairs, slice by slice, reading nothing of the study.

    Every argument is a value a stage computed and the writer saved. `entries` is the saved slice
    records in saved order (each with `slice_index`, `code`, `why`, `minimum_sites` and `pairs`,
    each pair carrying the `row` of its gap tiles), or None when the writer saved no facing
    record; `gap_tiles` the saved gap tiles bool (pairs over every slice, tile rows, tile
    columns); `labels` the saved territories int32 (slices, tile rows, tile columns), one grid per
    entry in saved order, None where the writer saved none; `own_planes` the plane the record
    names for each entry, None where it names none; `bounds_rc` and `median` the squint stack's
    saved bounds and tile medians (slices, tile rows, tile columns); `walk_indices` and `walk` the
    study stage's walk with its planes, and `acquired_index` and `acquired_plane` the objects
    stage's selected plane, each of which stands under a slice only when no plane is named for it
    and the slice is its own. For an entry `slice_standing` names what the slice can show; only
    where it is `pairs_drawn` are the pairs handed on, each with its own row of the saved gap
    tiles. The arrays are handed on in their saved dtypes; nothing is measured, resampled or
    derived, and an absent value stays absent. Each entry also carries the `border` its dome was
    read under, handed on as it is on its panel; the panels stay in the saved order, one per
    entry, and the pairs, territories and plane of an entry are its own whatever the border of
    another entry at the same slice.
    """
    bounds = None if bounds_rc is None else np.asarray(bounds_rc, dtype=np.int64)
    if entries is None:
        return FacingPanels(saved=False, bounds_rc=bounds, slices=())
    medians = None if median is None else np.asarray(median, dtype=np.float64)
    stack_slices = 0 if medians is None else int(medians.shape[0])
    panels = []
    for number, entry in enumerate(entries):
        code = entry["code"]
        index = int(entry["slice_index"])
        standing = slice_standing(code, index, stack_slices)
        pairs: tuple[PairPanel, ...] = ()
        if standing == "pairs_drawn" and gap_tiles is not None:
            pairs = tuple(
                PairPanel(
                    first=int(pair["first"]),
                    second=int(pair["second"]),
                    first_role=str(pair["first_role"]),
                    second_role=str(pair["second_role"]),
                    code=str(pair["code"]),
                    sites=int(pair["sites"]),
                    gap_sites=int(pair["gap_sites"]),
                    saddle_mm=None
                    if pair["saddle_mm"] is None
                    else float(pair["saddle_mm"]),
                    gap_tiles=np.asarray(gap_tiles[int(pair["row"])], dtype=bool),
                )
                for pair in entry["pairs"]
            )
        plane, source = _stored_plane(
            own_planes[number],
            index,
            walk_indices,
            walk,
            acquired_index,
            acquired_plane,
        )
        panels.append(
            SlicePanel(
                index=index,
                standing=standing,
                code=str(code),
                why=str(entry["why"]),
                minimum_sites=int(entry["minimum_sites"]),
                pairs=pairs,
                labels=None
                if labels is None
                else np.asarray(labels[number], dtype=np.int32),
                plane=plane,
                plane_source=source,
                median=medians[index]
                if medians is not None and 0 <= index < stack_slices
                else None,
                border=str(entry["border"]),
            )
        )
    return FacingPanels(saved=True, bounds_rc=bounds, slices=tuple(panels))
