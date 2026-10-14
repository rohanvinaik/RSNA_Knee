"""Draw the funnel's facing pairs: one sheet per series, each chosen slice's pairs and the gap between their objects.

The-funnel task 7.2 (`openspec/changes/the-funnel/tasks.md`). The funnel's operation 7
(`knee.relations.facing`) names, on each chosen slice, every pair of the objects the selection
gave a role, with the direct sites between them, the gap tiles that lie between them, the least
dome height over those tiles (the saddle height) and one word; the writer saves the record. This
workbench arranges those saved values through `knee.pictures.facing`: ONE SHEET PER SERIES, a text
panel with the pairs and their numbers in words, then one panel per chosen slice. A panel shows,
under the tiles, the plane stored for that slice in grey (the facing record's own plane for the
slice, else the study stage's walk where it holds the slice, else the objects stage's selected
plane where that is the slice; else the squint's tile medians at the slice, and the title says
so), over it the objects of every pair, each tile of an object in the object's own colour with its
index written on it, and the gap tiles between each pair's two objects in amber where the pair
faces and in grey where the pair has gap tiles but does not face. At the gap are written the
pair's two indices, its code and its saddle height. A pair with no gap tile has nothing to draw
between its objects; it is listed in the text panel. It takes no measurement of its own: every
number on the page is a saved value, and every gap in the record is a named silence, never a zero.

Five silences are kept apart, because each has its own remedy
(`knee.pictures.facing.SLICE_STANDINGS`): this run's writer saved no facing pairs for the series;
the saved code is a word the stage does not say; the stage's dome or selection was absent and says
why; the stage found fewer than two objects with a role and so examined no pair; the slice lies
outside the slices the stack holds. A record saved without the territories draws the gap and the
indices at it, and the title says the territories were not saved. A facing record that disagrees
with the writer's other records is refused rather than drawn: a vocabulary that is not the
stage's, a code or role the stage does not say, a count that disagrees with the saved gap tiles, a
pair whose row is not its place, an array whose dtype, shape or digest disagrees with its
descriptor, a pair that names a territory the saved territories do not hold, a gap tile lying on a
territory, a record saved without the series' squint stack, a grid that is not the stack's, or a
plane that covers another plane than the stack's.

Nothing here thresholds, labels, dilates or recomputes a code. Where a word or a number is written
at the gap, the position is the mean of the centres of the saved gap tiles, placed by the stack's
own native bounds: a place for words, not a reading. The grey scale is Matplotlib's linear display
scale over each plane's own stored values, or over the medians' own.
"""

import argparse
import json
from collections.abc import Mapping, Sequence
from hashlib import sha256
from pathlib import Path
from textwrap import fill
from typing import NamedTuple, TypeGuard

import numpy as np

from knee.objects.selection import ROLE_CODES
from knee.objects.tile_dome import BORDER_CODES
from knee.pictures import facing as pictures
from knee.relations.facing import FACING_CODES, FACING_RECORD_CODES
from workbench.render import squint_stack_frames
from workbench.render._out import PROJECT, ArgumentRefusal
from workbench.render.field_frames import (
    UNREAD_COLOUR,
    native_extent,
    overlay,
    saved_array,
    silence,
    tile_edges,
)

#: What each silence a saved slice can hold says, in words. The codes are the adapter's
#: (`knee.pictures.facing.SLICE_STANDINGS`); the words are this drawing's. `tiles_not_placed` is
#: this drawing's own: pairs saved with no stack bounds to place their tiles. So is
#: `border_not_saved`: a place on the sheet, a slice under a border, where the record holds no
#: entry (the sheet has one row per border and one column per slice).
STANDING_WORDS: Mapping[str, str] = {
    "pairs_drawn": "the objects of every pair and the gap tiles between them, over the plane",
    "facing_not_saved": "not saved: this run's writer saved no facing pairs for this series",
    "facing_code_unknown": "not drawn: the saved code is one the stage does not say",
    "facing_absent": "not made: the stage's tile dome or selection was absent",
    "no_pair": "not drawn: fewer than two objects carried a role, so no pair was examined",
    "slice_outside_stack": "not drawn: the slice lies outside the slices the stack holds",
    "tiles_not_placed": "not drawn: no squint stack bounds were handed on to place the tiles",
    "border_not_saved": "not drawn: this run's writer saved no reading under this border at this slice",
}

#: Where the plane under a slice came from, in words for the title. `none` says that no plane is
#: stored for the slice; the title then adds what lies under the tiles instead. Each phrase is
#: short enough to stand on one line of a panel's title beside its neighbour's.
SOURCE_WORDS: Mapping[str, str] = {
    "own": "over the plane stored for this slice",
    "walk": "over the study walk's plane at this slice",
    "acquired": "over the objects stage's selected plane",
    "none": "no plane stored",
}

#: What an object is drawn in, by order of its label among the labels the pairs name, and what a
#: gap is drawn in. A pair that faces has an amber gap; a pair that has gap tiles and does not face
#: has a grey one. The colours are the drawing's, never a reading.
OBJECT_COLOURS: tuple[str, ...] = ("#2563eb", "#16a34a", "#9333ea", "#0891b2")
OBJECT_ALPHA = 0.38
FACING_GAP_COLOUR = "#f59e0b"
OTHER_GAP_COLOUR = "#94a3b8"
GAP_ALPHA = 0.85

#: One sheet per series: the text panel, then one panel per chosen slice.
PANEL_INCHES = 4.6
ROW_INCHES = 5.6
DPI = 120


def whole(value: object, floor: int = 0) -> TypeGuard[int]:
    """Whether a saved value is a whole number (never a bool) at or above `floor`."""
    return type(value) is int and value >= floor


def saved_pair(pair: object) -> None:
    """Refuse one saved pair that is not what the writer saves: its labels, roles, code, counts, saddle or row."""
    if type(pair) is not dict:
        raise ValueError("saved_facing_pair_not_a_record")
    first, second = pair.get("first"), pair.get("second")
    if not (whole(first) and whole(second) and first < second):
        raise ValueError("saved_facing_pair_labels_invalid")
    for key in ("first_role", "second_role"):
        role = pair.get(key)
        if type(role) is not str or role not in ROLE_CODES or role == "unselected":
            raise ValueError(f"saved_facing_role_unknown:{role}")
    code = pair.get("code")
    if type(code) is not str or code not in FACING_CODES:
        raise ValueError(f"saved_facing_pair_code_unknown:{code}")
    for key in ("sites", "gap_sites", "row"):
        if not whole(pair.get(key)):
            raise ValueError(f"saved_facing_count_invalid:{key}")
    saddle = pair.get("saddle_mm")
    if saddle is not None and (
        isinstance(saddle, bool)
        or not isinstance(saddle, (int, float))
        or not np.isfinite(saddle)
    ):
        raise ValueError("saved_facing_saddle_invalid")


def saved_entry(entry: object) -> dict:
    """Refuse one saved slice that is not what the writer saves; hand it on as it is."""
    if type(entry) is not dict:
        raise ValueError("saved_facing_slice_not_a_record")
    if not whole(entry.get("slice_index"), -1):
        raise ValueError("saved_facing_field_invalid:slice_index")
    border = entry.get("border")
    if type(border) is not str:
        raise ValueError("saved_facing_field_invalid:border")
    if border not in BORDER_CODES:
        raise ValueError(f"saved_facing_border_unknown:{border}")
    code, why = entry.get("code"), entry.get("why")
    if type(code) is not str:
        raise ValueError("saved_facing_field_invalid:code")
    if type(why) is not str:
        raise ValueError("saved_facing_field_invalid:why")
    if code not in FACING_RECORD_CODES:
        raise ValueError(f"saved_facing_code_unknown:{code}")
    if not whole(entry.get("minimum_sites")):
        raise ValueError("saved_facing_field_invalid:minimum_sites")
    pairs = entry.get("pairs")
    if type(pairs) is not list:
        raise ValueError("saved_facing_pairs_invalid")
    for pair in pairs:
        saved_pair(pair)
    # `present` means at least one pair was examined; the two silences examined none.
    if (code == "present") != bool(pairs):
        raise ValueError("saved_facing_pairs_disagree_with_the_code")
    plane = entry.get("plane")
    if plane is not None and type(plane) is not str:
        raise ValueError("saved_facing_array_unnamed:plane")
    return entry


def check_entries_unique(entries: list[dict]) -> None:
    """Refuse two saved slices read under one border at one stack index: an entry is keyed by both.

    The route reads each chosen slice once under each border, so a slice is one entry per border
    and never one entry per slice: the same index under the two borders is two entries, and the
    same border and index twice is a record whose writer disagrees with the route. The order the
    entries were saved in is not read.
    """
    seen: set[tuple[str, int]] = set()
    for entry in entries:
        key = (entry["border"], entry["slice_index"])
        if key in seen:
            raise ValueError(f"saved_facing_entry_repeated:{key[0]}:{key[1]}")
        seen.add(key)


def saved_optional(
    arrays: Mapping[str, np.ndarray],
    descriptors: dict,
    name: str | None,
    ndim: int,
    dtype: np.dtype | None,
    short: str,
) -> np.ndarray | None:
    """One array a record may name: None where it names none, else validated against its descriptor."""
    if name is None:
        return None
    array = saved_array(arrays, descriptors, name, ndim)
    if dtype is not None and array.dtype != dtype:
        raise ValueError(f"saved_facing_representation_invalid:{short}")
    return array


def check_pairs_against_arrays(
    entries: list[dict], gap: np.ndarray, labels: np.ndarray | None
) -> None:
    """The saved pairs against the saved gap tiles and territories: rows, counts, labels and gaps.

    Each pair's row must be its place among all the pairs, slice by slice; its saved gap count
    must be the count of its row. Where territories were saved, each pair's two labels must be
    held by its own slice's territories, and no gap tile may lie on a territory.
    """
    row = 0
    for number, entry in enumerate(entries):
        for pair in entry["pairs"]:
            if pair["row"] != row:
                raise ValueError("saved_facing_row_mismatch")
            if pair["gap_sites"] != int(np.count_nonzero(gap[row])):
                raise ValueError("saved_facing_gap_sites_mismatch")
            if labels is not None:
                held = labels[number]
                for label in (pair["first"], pair["second"]):
                    if not (held == label).any():
                        raise ValueError(f"saved_facing_label_missing:{label}")
                if held[gap[row]].any():
                    raise ValueError("saved_facing_gap_on_a_territory")
            row += 1


def saved_facing(run: Path, record: dict) -> tuple[Path, pictures.FacingPanels]:
    """Reconstitute one series' saved facing pairs and the planes that may lie under them, without measuring.

    Total over a series whose writer saved no facing record: it is handed on as the silence it is.
    A facing record that is not a mapping, vocabularies that are not the stage's, a grid, array
    name, slice, pair, code, role, count, row or saddle the stage does not say, a pair count that
    disagrees with the code, an array whose dtype, shape or digest disagrees with its descriptor,
    gap tiles that are not one row per pair on the record's grid, a count that is not its row's,
    territories that are not one grid per slice or are off the grid or do not hold a pair's labels
    or lie under a gap tile, a record saved without the series' squint stack, a stack whose grid is
    not the record's, a plane that does not cover the stack's plane, a walk whose saved indices do
    not match its planes, or a walk index list that is not whole numbers, means the record and
    this renderer disagree, and is raised rather than drawn. So is a slice whose border is
    missing, is not text or is not a word of `BORDER_CODES`, and so are two slices read under the
    same border at the same stack index. The stack is read through the stack
    drawer's own reader, which validates it against the writer's descriptors; its bounds place the
    tiles and its medians lie under them.
    """
    artifact = run / record["artifact"]
    descriptors = record["arrays"]
    saved = record.get("facing")
    saved_study = record.get("study") or {}
    walk_name = saved_study.get("walk_array")
    walk_indices = saved_study.get("walk_indices", [])
    if type(walk_indices) is not list or not all(whole(i) for i in walk_indices):
        raise ValueError("saved_walk_indices_invalid")
    entries: list[dict] | None = None
    tiles: tuple[int, int] = (0, 0)
    names: dict = {}
    if saved is not None:
        if type(saved) is not dict:
            raise ValueError("saved_facing_not_a_record")
        if saved.get("record_code_names") != list(FACING_RECORD_CODES) or saved.get(
            "pair_code_names"
        ) != list(FACING_CODES):
            raise ValueError("saved_facing_vocabulary_mismatch")
        slices = saved.get("slices")
        if type(slices) is not list:
            raise ValueError("saved_facing_slices_invalid")
        grid = saved.get("tiles_rc")
        if not (
            isinstance(grid, list)
            and len(grid) == 2
            and all(whole(size) for size in grid)
        ):
            raise ValueError("saved_facing_tiles_invalid")
        tiles = (int(grid[0]), int(grid[1]))
        named = saved.get("arrays")
        if type(named) is not dict:
            raise ValueError("saved_facing_arrays_missing")
        if type(named.get("gap_tiles")) is not str:
            raise ValueError("saved_facing_array_unnamed:gap_tiles")
        if named.get("labels") is not None and type(named["labels"]) is not str:
            raise ValueError("saved_facing_array_unnamed:labels")
        names = named
        entries = [saved_entry(entry) for entry in slices]
        check_entries_unique(entries)
    gap = labels = walk = acquired = None
    planes: list[np.ndarray | None] = []
    with np.load(artifact, allow_pickle=False) as arrays:
        if entries is not None:
            gap = saved_optional(
                arrays,
                descriptors,
                names["gap_tiles"],
                3,
                np.dtype(np.bool_),
                "gap_tiles",
            )
            labels = saved_optional(
                arrays,
                descriptors,
                names.get("labels"),
                3,
                np.dtype(np.int32),
                "labels",
            )
            for entry in entries:
                own = saved_optional(
                    arrays, descriptors, entry.get("plane"), 2, None, "plane"
                )
                if own is not None and own.dtype.kind not in "iuf":
                    raise ValueError(
                        f"saved_array_representation_invalid:{entry['plane']}"
                    )
                planes.append(own)
            if entries:
                if walk_name is not None:
                    walk = saved_array(arrays, descriptors, walk_name, 3)
                if "acquired_plane" in descriptors:
                    acquired = saved_array(arrays, descriptors, "acquired_plane", 2)
    if walk is not None and walk.shape[0] != len(walk_indices):
        raise ValueError("saved_walk_indices_mismatch")
    if entries is not None and gap is not None:
        total = sum(len(entry["pairs"]) for entry in entries)
        if gap.shape[0] != total:
            raise ValueError("saved_facing_rows_mismatch")
        if tuple(gap.shape[1:]) != tiles:
            raise ValueError("saved_facing_shape_mismatch:gap_tiles")
        if labels is not None and tuple(labels.shape) != (len(entries), *tiles):
            raise ValueError("saved_facing_shape_mismatch:labels")
        if labels is not None and labels.size and int(labels.min()) < 0:
            raise ValueError("saved_facing_labels_invalid")
        check_pairs_against_arrays(entries, gap, labels)
    bounds = median = None
    if tiles != (0, 0):
        # The facing pairs are read over the series' squint grid, so a record that saved the one
        # and not the other disagrees with the writer; the stack's bounds are what place the tiles.
        if "squint_stack" not in record:
            raise ValueError("saved_facing_without_a_stack")
        _, stack = squint_stack_frames.saved_stack(run, record)
        bounds, median = stack.bounds_rc, stack.median
        if bounds is None or median is None or tuple(bounds.shape[:2]) != tiles:
            raise ValueError("saved_facing_grid_mismatch")
    frame = pictures.facing_panels(
        entries,
        gap,
        labels,
        planes,
        bounds,
        median,
        tuple(walk_indices),
        walk,
        record.get("slice_index") if type(record.get("slice_index")) is int else None,
        acquired,
    )
    if bounds is not None:
        covered = (int(bounds[-1, -1, 1]), int(bounds[-1, -1, 3]))
        for panel in frame.slices:
            if panel.plane is not None and tuple(panel.plane.shape) != covered:
                raise ValueError("saved_facing_covers_another_plane")
    return artifact, frame


def number(value: float | None) -> str:
    """A saved saddle height as text; None is how a height the stage did not read comes back."""
    return "none (no gap tile)" if value is None else f"{value:g} mm"


def tile_centre(
    edges: tuple[np.ndarray, np.ndarray], mask: np.ndarray
) -> tuple[float, float] | None:
    """The mean of the native centres of the tiles of a saved map: where to write words, not a reading.

    `edges` are the stack's native (column edges, row edges); the centre of a tile is the midpoint
    of its two edges on each axis. None for a map with no tile.
    """
    rows, columns = np.nonzero(mask)
    if not rows.size:
        return None
    column_edges, row_edges = edges
    x = (column_edges[columns] + column_edges[columns + 1]) / 2.0
    y = (row_edges[rows] + row_edges[rows + 1]) / 2.0
    return float(x.mean()), float(y.mean())


def image_name(index: int, record: dict) -> str:
    """One sheet per series, named as the view sheets are: its order, plane and the two flags."""
    view, fluid, fat = record["view"]
    return f"{index:02d}-{view.lower()}-fs{fluid}-fat{fat}.png"


def underlay(panel: pictures.SlicePanel) -> str:
    """What lies under the tiles of a slice: its stored `plane`, the stack's `medians` at it, or `none`."""
    if panel.plane is not None:
        return "plane"
    return "medians" if panel.median is not None else "none"


class SheetPlan(NamedTuple):
    """Where each saved slice's panel stands on the sheet, and which slice heads each column.

    cells: one (row, column) per panel, in the panels' own order. A row is the position of the
    panel's border in `BORDER_CODES`; a column is 1 plus the position of its stack index among the
    distinct indices in the order they first appear, column 0 being the text panel. indices: the
    stack index each slice column holds, in column order. rows: how many rows the sheet has, one
    per border where anything is saved, else one.
    """

    cells: tuple[tuple[int, int], ...]
    indices: tuple[int, ...]
    rows: int


def sheet_cells(panels: Sequence[pictures.SlicePanel]) -> SheetPlan:
    """Place each saved slice on the sheet so one slice's readings under the borders stand together.

    Arranging only: the panels are taken in the order given and none is reordered, measured or
    dropped. The columns follow the order the slices first appear in, whatever order the writer
    saved the borders in, so the readings of one slice under the two borders stand one above the
    other, in the order of `BORDER_CODES`, and a slice read under one border only leaves the other
    border's place empty for `unfilled_cells` to name. A border that is not a word of
    `BORDER_CODES`, and two panels of one border and one stack index, are refused by name.
    """
    indices: list[int] = []
    cells: list[tuple[int, int]] = []
    taken: set[tuple[int, int]] = set()
    for panel in panels:
        if panel.border not in BORDER_CODES:
            raise ValueError(f"saved_facing_border_unknown:{panel.border}")
        if panel.index not in indices:
            indices.append(panel.index)
        cell = (BORDER_CODES.index(panel.border), 1 + indices.index(panel.index))
        if cell in taken:
            raise ValueError(
                f"saved_facing_entry_repeated:{panel.border}:{panel.index}"
            )
        taken.add(cell)
        cells.append(cell)
    return SheetPlan(
        cells=tuple(cells),
        indices=tuple(indices),
        rows=len(BORDER_CODES) if panels else 1,
    )


def unfilled_cells(plan: SheetPlan) -> tuple[tuple[int, int], ...]:
    """The (row, column) places of a sheet's slice columns that no saved slice holds, column by column."""
    held = set(plan.cells)
    return tuple(
        (row, 1 + position)
        for position in range(len(plan.indices))
        for row in range(plan.rows)
        if (row, 1 + position) not in held
    )


def pair_lines(pair: pictures.PairPanel) -> list[str]:
    """One pair in words: its two objects and roles, then its code, sites, gap tiles and saddle."""
    return [
        f"  objects {pair.first} and {pair.second}: {pair.first_role} / {pair.second_role}",
        f"    {pair.code}; direct sites {pair.sites}; gap tiles {pair.gap_sites}",
        f"    saddle height {number(pair.saddle_mm)}",
    ]


def facing_lines(record: dict, frame: pictures.FacingPanels) -> list[str]:
    """The text panel: the series, its view, and each saved slice's standing, bar and pairs."""
    view, fluid, fat = record["view"]
    lines = [
        fill(record["series_uid"], width=40),
        f"{view} · fluid-sensitive={fluid}, fat-suppressed={fat}",
        "",
    ]
    if not frame.saved:
        lines.append("facing pairs (relations): not saved")
        lines.append(fill(STANDING_WORDS["facing_not_saved"], width=40))
        return lines
    if not frame.slices:
        lines.append("facing pairs (relations): saved, with no chosen slice")
        return lines
    lines.append("facing pairs (relations), per chosen slice and border")
    # The sheet's own order: by slice, in the order the slices first appear, a slice's borders
    # together in the order of `BORDER_CODES`.
    plan = sheet_cells(frame.slices)
    for number in sorted(
        range(len(frame.slices)),
        key=lambda n: (plan.cells[n][1], plan.cells[n][0]),
    ):
        panel = frame.slices[number]
        lines += [
            "",
            f"{panel.border} · stack index {panel.index}: {panel.code}",
            fill(f"why: {panel.why}", width=40),
        ]
        if panel.standing == "pairs_drawn":
            lines.append(f"  bar: {panel.minimum_sites} gap tiles")
            for pair in panel.pairs:
                lines += pair_lines(pair)
        elif panel.standing == "slice_outside_stack":
            lines.append(fill(STANDING_WORDS[panel.standing], width=40))
    return lines


def draw_underlay(axis, panel: pictures.SlicePanel, edges) -> str:
    """Draw what lies under a slice's tiles: its stored plane, else the stack's tile medians, else nothing.

    Returns the underlay drawn: `plane`, `medians` or `none`.
    """
    from matplotlib import colormaps

    kind = underlay(panel)
    if kind == "plane" and panel.plane is not None:
        axis.imshow(
            panel.plane,
            cmap="gray",
            interpolation="nearest",
            extent=native_extent(panel.plane.shape),
        )
    elif kind == "medians" and panel.median is not None:
        columns_edges, rows_edges = edges
        finite = np.isfinite(panel.median)
        limits = (
            {
                "vmin": float(panel.median[finite].min()),
                "vmax": float(panel.median[finite].max()),
            }
            if finite.any()
            else {}
        )
        axis.pcolormesh(
            columns_edges,
            rows_edges,
            panel.median,
            cmap=colormaps["gray"].with_extremes(bad=UNREAD_COLOUR),
            **limits,
        )
    return kind


def draw_slice(axis, panel: pictures.SlicePanel, frame: pictures.FacingPanels) -> str:
    """One chosen slice: what lies under it, the objects of each pair, and the gap tiles with their words.

    Returns `drawn` when the pairs are drawn over a stored plane, `medians` when they are drawn
    over the stack's tile medians, `tiles_alone` when they are drawn on the tile grid with nothing
    beneath, or the slice's standing when it is a silence.
    """
    if panel.standing != "pairs_drawn" or frame.bounds_rc is None:
        word = panel.standing if panel.standing != "pairs_drawn" else "tiles_not_placed"
        words = STANDING_WORDS[word]
        if word in ("facing_absent", "no_pair") and panel.why:
            words = f"{words}. The stage says: {panel.why}"
        silence(axis, f"{panel.border} · stack index {panel.index}", words)
        return word
    axis.set_axis_off()
    edges = tile_edges(frame.bounds_rc)
    columns_edges, rows_edges = edges
    kind = draw_underlay(axis, panel, edges)
    named = sorted(
        {pair.first for pair in panel.pairs} | {pair.second for pair in panel.pairs}
    )
    roles = {}
    for pair in panel.pairs:
        roles[pair.first] = pair.first_role
        roles[pair.second] = pair.second_role
    if panel.labels is not None:
        for position, label in enumerate(named):
            mask = panel.labels == label
            overlay(
                axis,
                edges,
                mask,
                OBJECT_COLOURS[position % len(OBJECT_COLOURS)],
                alpha=OBJECT_ALPHA,
            )
            centre = tile_centre(edges, mask)
            if centre is not None:
                axis.text(
                    *centre,
                    f"{label}\n{roles[label]}",
                    ha="center",
                    va="center",
                    fontsize=6,
                    color="white",
                    fontweight="bold",
                )
    for pair in panel.pairs:
        centre = tile_centre(edges, pair.gap_tiles)
        if centre is None:
            continue
        overlay(
            axis,
            edges,
            pair.gap_tiles,
            FACING_GAP_COLOUR if pair.code == "facing" else OTHER_GAP_COLOUR,
            alpha=GAP_ALPHA,
        )
        axis.text(
            *centre,
            f"{pair.first}-{pair.second}\n{pair.code}\nsaddle {number(pair.saddle_mm)}",
            ha="center",
            va="center",
            fontsize=5.5,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.75, "pad": 1},
        )
    axis.set_xlim(0, float(columns_edges[-1]))
    axis.set_ylim(float(rows_edges[-1]), 0)
    axis.set_aspect("equal")
    if kind == "plane":
        under = SOURCE_WORDS[panel.plane_source]
    elif kind == "medians":
        under = f"{SOURCE_WORDS['none']}; the squint's tile medians"
    else:
        under = f"{SOURCE_WORDS['none']}; tiles alone"
    territories = (
        "objects coloured and indexed"
        if panel.labels is not None
        else "territories not saved: indices at the gap only"
    )
    # One fact to a line, each short enough to sit beside the next panel's title.
    axis.set_title(
        f"{panel.border} · stack index {panel.index}: {panel.code}\n{under}\n{territories}",
        fontsize=7,
    )
    return {"plane": "drawn", "medians": "medians", "none": "tiles_alone"}[kind]


def slice_manifest(
    panel: pictures.SlicePanel,
    entry: dict,
    record: dict,
    drawn: str,
    cell: tuple[int, int],
) -> dict:
    """What one slice drew, from the saved values: the standing, the pairs and what lay under it.

    `cell` is the (row, column) it stood in on the sheet (`sheet_cells`), written beside its
    border so the two readings of one slice can be found next to each other.
    """
    return {
        "index": panel.index,
        "border": panel.border,
        "row": cell[0],
        "column": cell[1],
        "standing": panel.standing,
        "drawn": drawn,
        "code": panel.code,
        "why": panel.why,
        "minimum_sites": panel.minimum_sites,
        "plane_source": panel.plane_source,
        "underlay": underlay(panel),
        "territories": panel.labels is not None,
        "own_plane": None
        if entry.get("plane") is None
        else record["arrays"][entry["plane"]],
        "pairs": [
            {
                "first": pair.first,
                "second": pair.second,
                "first_role": pair.first_role,
                "second_role": pair.second_role,
                "code": pair.code,
                "sites": pair.sites,
                "gap_sites": pair.gap_sites,
                "saddle_mm": pair.saddle_mm,
            }
            for pair in panel.pairs
        ],
    }


def draw(run: Path, study_uid: str, out: Path) -> dict:
    """Draw this stage from the saved run, one sheet per series, and return its manifest.

    The one entry a caller uses, so the single command can draw every stage without knowing each
    renderer's argument spelling. `main()` is a thin wrapper over it.

    Matplotlib is supplied PER RUN and is never a production dependency, so it is imported after
    every refusal this function can make: the validators above are then importable and testable in
    the ordinary environment.
    """
    target = out.resolve()
    if not target.is_relative_to((PROJECT / "data").resolve()):
        raise ArgumentRefusal("out must be under the project's private data directory")
    receipt_path = run / "receipt.json"
    receipt_bytes = receipt_path.read_bytes()
    receipt = json.loads(receipt_bytes)
    records = [r for r in receipt["records"] if r["study_uid"] == study_uid]
    if not records:
        raise ArgumentRefusal("no saved records for this study")
    loaded = [saved_facing(run, record) for record in records]
    if pictures.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:facing")
    # Every standing the adapter can name has words here, checked before anything is drawn.
    unworded = [name for name in pictures.SLICE_STANDINGS if name not in STANDING_WORDS]
    if unworded:
        raise RuntimeError(f"slice_standing_unworded:{','.join(unworded)}")
    unsourced = [name for name in pictures.PLANE_SOURCES if name not in SOURCE_WORDS]
    if unsourced:
        raise RuntimeError(f"plane_source_unworded:{','.join(unsourced)}")

    import matplotlib.pyplot as plt

    target.mkdir(parents=True, exist_ok=True)
    series = []
    for index, (record, (artifact, frame)) in enumerate(
        zip(records, loaded, strict=True), start=1
    ):
        # One column per chosen slice and one row per border, the text panel across every row:
        # a slice's readings under the two borders stand one above the other, so they compare.
        plan = sheet_cells(frame.slices)
        across = 1 + max(len(plan.indices), 1)
        sheet = plt.figure(
            figsize=(PANEL_INCHES * across, ROW_INCHES * plan.rows),
            layout="constrained",
        )
        grid = sheet.add_gridspec(plan.rows, across)
        text = sheet.add_subplot(grid[:, 0])
        axes = {
            (row, column): sheet.add_subplot(grid[row, column])
            for row in range(plan.rows)
            for column in range(1, across)
        }
        for axis in (text, *axes.values()):
            axis.set_axis_off()
        text.set_title("the facing pairs", fontsize=8)
        text.text(
            0.0,
            1.0,
            "\n".join(facing_lines(record, frame)),
            transform=text.transAxes,
            va="top",
            family="monospace",
            fontsize=6.5,
        )
        saved = record.get("facing")
        entries = [] if saved is None else saved["slices"]
        standings = []
        if not frame.slices:
            axes[0, 1].text(
                0.03,
                0.5,
                fill(
                    STANDING_WORDS["facing_not_saved"]
                    if not frame.saved
                    else "no chosen slice was saved for this series",
                    width=38,
                ),
                transform=axes[0, 1].transAxes,
                va="center",
            )
        for panel, entry, cell in zip(frame.slices, entries, plan.cells, strict=True):
            drawn = draw_slice(axes[cell], panel, frame)
            standings.append(slice_manifest(panel, entry, record, drawn, cell))
        # A place on the sheet that no saved slice holds is a silence in words, never a blank.
        unsaved = []
        for row, column in unfilled_cells(plan):
            border, stack_index = BORDER_CODES[row], plan.indices[column - 1]
            silence(
                axes[row, column],
                f"{border} · stack index {stack_index}",
                STANDING_WORDS["border_not_saved"],
            )
            unsaved.append(
                {"border": border, "index": stack_index, "row": row, "column": column}
            )
        view, fluid, fat = record["view"]
        sheet.suptitle(
            f"The funnel's facing pairs · {view} · fluid-sensitive={fluid}, "
            f"fat-suppressed={fat} · series {record['series_uid']}\n"
            "one column per chosen slice; one row per border of the dome, top to bottom "
            f"{', '.join(BORDER_CODES)}, so the two readings of a slice stand one above the "
            "other\n"
            "in each: the objects the selection named, each tile of an object in its "
            "own colour with its index, and the gap tiles between the two objects of each pair; "
            "written at the gap: the two indices, the pair's code and the saddle height, the "
            "least height over the gap tiles\n"
            "amber: the pair faces across these gap tiles · grey: the pair has gap tiles but "
            "does not face · a pair with no gap tile is listed in the text panel",
            fontsize=9,
        )
        name = image_name(index, record)
        sheet.savefig(target / name, dpi=DPI)
        plt.close(sheet)
        series.append(
            {
                "image": name,
                "image_sha256": sha256((target / name).read_bytes()).hexdigest(),
                "series_uid": record["series_uid"],
                "artifact": record["artifact"],
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "view": record["view"],
                "facing": None
                if saved is None
                else {
                    "record_code_names": saved["record_code_names"],
                    "pair_code_names": saved["pair_code_names"],
                    "tiles_rc": saved["tiles_rc"],
                    "arrays": {
                        short: None if name is None else record["arrays"][name]
                        for short, name in saved["arrays"].items()
                    },
                },
                "slices": standings,
                "sheet": {
                    "rows": plan.rows,
                    "columns": across,
                    "slice_indices": list(plan.indices),
                    "unsaved": unsaved,
                },
                "frame_kind": "study",
            }
        )
    manifest = {
        "schema": "facing-frames-v1",
        "receipt_sha256": sha256(receipt_bytes).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": {
            "facing": sha256(Path(pictures.__file__).read_bytes()).hexdigest()
        },
        "study_uid": study_uid,
        "image": series[0]["image"],
        "images": [entry["image"] for entry in series],
        "frame_kind": "study",
        "standings": list(pictures.SLICE_STANDINGS),
        "borders": list(BORDER_CODES),
        "legend": {
            "objects": list(OBJECT_COLOURS),
            "object_alpha": OBJECT_ALPHA,
            "gap_when_the_pair_faces": FACING_GAP_COLOUR,
            "gap_when_it_does_not": OTHER_GAP_COLOUR,
            "gap_alpha": GAP_ALPHA,
            "tile_with_no_finite_pixel": UNREAD_COLOUR,
        },
        "series": series,
        "note": (
            "Every value is a saved one. A chosen slice with no pair, a stage whose "
            "predecessors were absent and a run whose writer did not save the facing pairs "
            "are three silences, each named; none is a zero. One sheet per series."
        ),
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--study-uid", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    # ONLY the argument refusals. A saved-array digest mismatch or a malformed receipt is a
    # corruption signal and must propagate, never be dressed as a mistyped flag.
    try:
        manifest = draw(args.run, args.study_uid, args.out)
    except ArgumentRefusal as refusal:
        parser.error(str(refusal))
    target = args.out.resolve()
    print(
        json.dumps(
            {
                "images": [str(target / name) for name in manifest["images"]],
                "manifest": str(target / "manifest.json"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
