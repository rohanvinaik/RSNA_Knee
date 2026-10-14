"""What the interstices resolved, drawn: each facing pair's extent over the acquired plane, with its walls, fill and contents.

The funnel's operation 8 (`openspec/changes/the-funnel/design.md` R8, task 8.3):
`knee.relations.interstice.read_interstices` builds, for each facing pair of a chosen slice, the
space between the two objects at tile scale: its extent, each object's wall named profile by
profile, what fills it, and the round-2 contents inside it, named by position and side only. Its
picture is the one the founder checks by eye (E5, task 9.4): per facing pair, the extent tinted
over the acquired plane at that slice, each content outlined with its position and side words,
the fill word and its counts, and each wall's words written at its own object; one sheet per
series, each tile placed in native pixels by the squint stack's saved bounds.

Every value here is one the stage computed and the writer saved. Choosing which saved plane lies
under an extent, slicing the stacked saved arrays back into the records they came from, and
tallying the saved wall codes by their words is ARRANGING: it picks stored values and alters none
of them (as `knee.pictures.first_lens.lens_panels` does with the first lens). Nothing here
measures, thresholds, dilates or recomputes a code, an extent or a position; a record the writer
did not save, a record the stage could not make, and a slice no saved plane shows are named
silences in words, never an empty picture. The two decisions, `entry_standing` and
`plane_standing`, are pure and total.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from knee.relations.interstice import INTERSTICE_CODES, WALL_CODES

#: What one saved interstice can be to the picture. `named` is a reading drawn: its extent, walls,
#: fill and contents. The rest are the silences, each with its own remedy: the pair faces across
#: no tile at all (the stage's `no_extent`); the stage had a predecessor missing and made none
#: (`predecessor_absent`, its own reason beside); the saved code is a word the stage does not say.
ENTRY_STANDINGS: tuple[str, ...] = (
    "named",
    "no_extent",
    "predecessor_absent",
    "code_unknown",
)

#: Which saved plane lies under an extent: the plane the writer saved with the interstices at
#: that very slice (`saved`), one of the study stage's walked slices (`walk`), the series'
#: selected plane when the interstice's slice is the selected one (`selected`), or none, in which
#: case the tiles are drawn alone on the tile grid and the sheet says so.
PLANE_STANDINGS: tuple[str, ...] = ("saved", "walk", "selected", "tiles_alone")


def entry_standing(code: object) -> str:
    """Name what one saved interstice can show, from its saved code (pure -- total).

    `present` is `named`; `no_extent` and `predecessor_absent` are the stage's own silences,
    named apart because their remedies differ; a code that is not text, or is not a word of
    `INTERSTICE_CODES`, is `code_unknown`, named and never drawn as a reading. It selects nothing.

    post: __return__ in ENTRY_STANDINGS
    """
    if not isinstance(code, str) or code not in INTERSTICE_CODES:
        return "code_unknown"
    if code == "present":
        return "named"
    return code


def plane_standing(
    slice_index: object,
    saved_indices: Sequence[int],
    walk_indices: Sequence[int],
    selected_index: object,
    has_selected_plane: bool,
) -> str:
    """Name which saved plane an interstice at `slice_index` is drawn over (pure -- total).

    `saved_indices` are the slices whose planes the writer saved with the interstices (empty when
    none were); `walk_indices` the stack indices of the study stage's saved walk (empty when none
    was saved); `selected_index` the series' selected slice and `has_selected_plane` whether its
    plane was saved. An index that is not a whole number is `tiles_alone`, as is an index no saved
    plane shows. The plane saved for this very slice wins, then a walked slice, then the selected
    one: where two hold the same slice they are the same plane. It reads nothing from the planes.

    post: __return__ in PLANE_STANDINGS
    """
    if isinstance(slice_index, bool) or not isinstance(slice_index, int):
        return "tiles_alone"
    if slice_index in tuple(saved_indices):
        return "saved"
    if slice_index in tuple(walk_indices):
        return "walk"
    if (
        has_selected_plane
        and not isinstance(selected_index, bool)
        and isinstance(selected_index, int)
        and selected_index == slice_index
    ):
        return "selected"
    return "tiles_alone"


def wall_tally(codes: np.ndarray | None) -> tuple[tuple[str, int], ...]:
    """How many saved wall codes carry each word, in the stage's `WALL_CODES` order.

    Counting stored values by their words arranges them and decides nothing. None, or no code at
    all, is an empty tally: no profile entered the extent, or no strip was read, and the sheet
    says which in words rather than drawing a row of zeros.
    """
    if codes is None or np.size(codes) == 0:
        return ()
    return tuple(
        (word, int(np.count_nonzero(codes == value)))
        for value, word in enumerate(WALL_CODES)
    )


@dataclass(frozen=True, slots=True)
class ContentPanel:
    """One saved content of an interstice, as saved.

    index: 1.. within its interstice. tiles: (tiles_down, tiles_across) bool. centre_lps: the
    saved centre in LPS mm. position_code, side_code: the stage's words, as saved.
    """

    index: int
    tiles: np.ndarray
    centre_lps: tuple[float, float, float]
    position_code: str
    side_code: str


@dataclass(frozen=True, slots=True)
class InterstitialPanel:
    """One saved interstice, AS THE WRITER SAVED IT, ready for the workbench to draw.

    slice_index, first, second: the chosen slice and the pair's two territory labels. code, why:
    the stage's standing and reason; standing: `entry_standing(code)`. extent: (tiles_down,
    tiles_across) bool. fill_code and fill_counts: the stage's fill word and the conjunction words
    counted over the extent. first_walls, second_walls: the saved wall codes tallied by word
    (empty when no profile entered the extent). first_at_rc, second_at_rc: where the stage's dome
    grounded each object (its saved peak tile), None where the writer saved none. contents: the
    round-2 objects. plane: the saved plane under the extent, None for tiles alone: (rows,
    columns) in the dtype it was saved in, row 0 at the top, the plane's own stored units, in
    native pixels; plane_standing: which saved plane it is. An absent value stays absent, never a
    zero.
    """

    slice_index: int
    first: int
    second: int
    code: str
    why: str
    standing: str
    extent: np.ndarray
    fill_code: str
    fill_counts: tuple[tuple[str, int], ...]
    first_walls: tuple[tuple[str, int], ...]
    second_walls: tuple[tuple[str, int], ...]
    first_at_rc: tuple[int, int] | None
    second_at_rc: tuple[int, int] | None
    contents: tuple[ContentPanel, ...]
    plane: np.ndarray | None
    plane_standing: str


@dataclass(frozen=True, slots=True)
class InterstitialPanels:
    """One series' saved interstices, AS THE WRITER SAVED THEM.

    saved: whether the writer saved an interstice record for this series at all. tiles_rc: the
    tile grid the records are over, None when none was saved. bounds_rc: (tiles_down,
    tiles_across, 4) int64, the squint stack's saved half-open native bounds that place the tiles,
    None when none was handed on. panels: one per saved interstice, in the stage's order.
    """

    saved: bool
    tiles_rc: tuple[int, int] | None
    bounds_rc: np.ndarray | None
    panels: tuple[InterstitialPanel, ...]


def _at(value: Any) -> tuple[int, int] | None:
    """A saved tile coordinate as a pair of ints; None where the writer saved none."""
    if value is None:
        return None
    row, column = value
    return int(row), int(column)


def interstice_panels(
    entries: Sequence[Mapping[str, Any]] | None,
    extent: np.ndarray | None,
    first_walls: np.ndarray | None,
    second_walls: np.ndarray | None,
    content_tiles: np.ndarray | None,
    tiles_rc: tuple[int, int] | None,
    bounds_rc: np.ndarray | None,
    plane_slices: Sequence[int],
    planes: np.ndarray | None,
    walk_indices: Sequence[int],
    walk: np.ndarray | None,
    selected_index: int | None,
    selected_plane: np.ndarray | None,
) -> InterstitialPanels:
    """Hand on one series' saved interstices beside the planes they lie over, reading none of them.

    Every argument is a value a stage computed and the writer saved: the per-interstice
    `entries` (scalars and words), the stacked `extent` (one tile map per entry), the wall codes
    of every entry concatenated in entry order with each entry's length in its record, and the
    contents' `content_tiles` stacked in entry then content order; with the squint stack's
    `bounds_rc`, the planes the writer saved with the interstices (`planes`, one per slice of
    `plane_slices`), the study stage's `walk_indices` with the `walk` of planes at them, and the
    series' selected slice with its plane. The stacked arrays are cut back into their records by
    the saved lengths. Shapes: `extent` bool (M, tiles_down, tiles_across); `first_walls` and
    `second_walls` uint8 (N,); `content_tiles` bool (C, tiles_down, tiles_across); `bounds_rc`
    int64 (tiles_down, tiles_across, 4), the half-open native bounds (r0, r1, c0, c1) of each
    tile; `planes` (K, rows, columns), `walk` (W, rows, columns) and `selected_plane` (rows,
    columns), each in the dtype it was saved in, row 0 at the top, in the plane's own stored
    units and native pixels. Only planes that were actually saved count as available: slice
    indices whose planes are not there name no plane. Nothing is measured, resampled or derived;
    no entries at all is a series the writer saved nothing for.
    """
    if entries is None or extent is None:
        return InterstitialPanels(False, tiles_rc, bounds_rc, ())
    panels = []
    first_start = second_start = content_start = 0
    for position, entry in enumerate(entries):
        first_count = int(entry["first_wall_count"])
        second_count = int(entry["second_wall_count"])
        saved_contents = entry["contents"]
        contents = []
        for offset, content in enumerate(saved_contents):
            if content_tiles is None:
                break
            x, y, z = (float(v) for v in content["centre_lps"])
            contents.append(
                ContentPanel(
                    index=int(content["index"]),
                    tiles=content_tiles[content_start + offset],
                    centre_lps=(x, y, z),
                    position_code=str(content["position_code"]),
                    side_code=str(content["side_code"]),
                )
            )
        slice_index = int(entry["slice_index"])
        saved_slices = tuple(plane_slices) if planes is not None else ()
        walked_slices = tuple(walk_indices) if walk is not None else ()
        standing = plane_standing(
            slice_index,
            saved_slices,
            walked_slices,
            selected_index,
            selected_plane is not None,
        )
        plane = None
        if standing == "saved" and planes is not None:
            plane = np.asarray(planes[saved_slices.index(slice_index)])
        elif standing == "walk" and walk is not None:
            plane = np.asarray(walk[walked_slices.index(slice_index)])
        elif standing == "selected" and selected_plane is not None:
            plane = np.asarray(selected_plane)
        counts = entry["fill_counts"]
        panels.append(
            InterstitialPanel(
                slice_index=slice_index,
                first=int(entry["first"]),
                second=int(entry["second"]),
                code=str(entry["code"]),
                why=str(entry["why"]),
                standing=entry_standing(entry["code"]),
                extent=extent[position],
                fill_code=str(entry["fill_code"]),
                fill_counts=tuple((str(w), int(n)) for w, n in counts.items()),
                first_walls=wall_tally(
                    None
                    if first_walls is None
                    else first_walls[first_start : first_start + first_count]
                ),
                second_walls=wall_tally(
                    None
                    if second_walls is None
                    else second_walls[second_start : second_start + second_count]
                ),
                first_at_rc=_at(entry.get("first_at_rc")),
                second_at_rc=_at(entry.get("second_at_rc")),
                contents=tuple(contents),
                plane=plane,
                plane_standing=standing,
            )
        )
        first_start += first_count
        second_start += second_count
        content_start += len(saved_contents)
    return InterstitialPanels(True, tiles_rc, bounds_rc, tuple(panels))
