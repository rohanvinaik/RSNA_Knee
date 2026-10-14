"""Draw the funnel's interstices: one sheet per series, each facing pair's extent over the acquired plane, with its walls, fill and contents.

The-funnel task 8.3 (`openspec/changes/the-funnel/tasks.md`). The funnel's operation 8
(`knee.relations.interstice.read_interstices`) builds, per facing pair of a chosen slice, the
space between the two objects at tile scale: its extent, each object's wall named profile by
profile, what fills it, and the round-2 contents inside it, named by position and side only. The
writer saves the records; this workbench arranges the saved values through
`knee.pictures.interstice`: ONE SHEET PER SERIES (one image per series), so the founder can check
the spaces and what is in them by eye (E5, task 9.4): a text panel with the stage's standing and
the vocabulary, then one panel per saved interstice: the acquired plane at its slice in grey
(or the tiles alone, said in the title, where no saved plane shows that slice), the extent tinted
over it, each content outlined with its index, position and side words, the fill word with the
conjunction words counted over the extent, and each wall's words written at its own object (the
tile the dome grounded it at). Tiles are placed in native pixels by the squint stack's saved
bounds. It takes no measurement of its own: every number on the page is a saved value, and every
gap is a named silence, never a zero.

THE SAVED SHAPE (what the writer saves for a series, `record["interstice"]`; the arrays sit in the
series' artifact beside the others and are named in `record["arrays"]`). One series holds several
chosen slices and several pairs, so the arrays are STACKED and cut back by the saved lengths:

- `code_names`, `wall_code_names`, `fill_code_names`, `position_code_names`, `side_code_names`,
  `conjunction_code_names`: the stage's vocabularies, as lists, checked against the stage's own;
- `tiles_rc`: [tiles_down, tiles_across], the grid every tile array is over;
- `plane_slices` (optional, with `arrays["planes"]`: both or neither): the stack indices of the
  planes saved with the interstices, distinct, in order of first appearance among the
  interstices' `slice_index`;
- `interstices`: one dict per `InterstitialRecord`, in the stage's order, with `slice_index`,
  `first`, `second`, `code`, `why`, `fill_code`, `fill_counts` (word to count), `first_wall_count`,
  `second_wall_count`, `first_at_rc` and `second_at_rc` ([row, column] of the dome's saved peak
  tile for that territory, or None), and `contents`: one dict per content with `index`,
  `position_code`, `side_code` and `centre_lps` ([x, y, z]);
- `arrays`: the short names of the stacked arrays: `extent` bool (M, tiles_down, tiles_across),
  one tile map per interstice (a `predecessor_absent` interstice saves all False);
  `first_wall_codes` and `second_wall_codes` uint8 (sum of the counts,), every interstice's codes
  concatenated in order; `content_tiles` bool (C, tiles_down, tiles_across), every content of
  every interstice in order; `planes` (optional, with `plane_slices`) any numeric dtype
  (K, rows, columns), the acquired plane at each slice of `plane_slices` in that order, row 0 at
  the top, in the plane's own stored units, so the extent is tinted over the plane at ITS slice
  whichever slice the depth collapse chose. A writer that saves neither key saves no planes: that
  is a named silence, not a refusal. Where no plane was saved for a slice, the study's walked
  plane or the series' selected plane is used if it holds that slice, and else the tiles are
  drawn alone and the title says so. Only one of the two keys present is a record that disagrees
  with itself, and is refused.

Four silences are kept apart because each has its own remedy
(`knee.pictures.interstice.ENTRY_STANDINGS`): the pair faces across no tile (`no_extent`); the
stage had a predecessor missing and made none (`predecessor_absent`, its reason beside); the
saved code is a word the stage does not say; and this run's writer saved no interstice for the
series at all. An interstice saved without the series' squint stack, over another grid than the
stack's, or over a plane of another size, disagrees with the writer and is refused rather than
drawn.

Nothing here thresholds, labels, dilates or recomputes a code, an extent or a position. The grey
scale is Matplotlib's linear display scale over each plane's own stored values.
"""

import argparse
import json
import math
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from textwrap import fill as wrapped

import numpy as np

from knee.lenses.conjunction import CONJUNCTION_CODES
from knee.pictures import interstice as pictures
from knee.relations.interstice import (
    FILL_CODES,
    INTERSTICE_CODES,
    POSITION_CODES,
    SIDE_CODES,
    WALL_CODES,
)
from workbench.render import squint_stack_frames
from workbench.render._out import PROJECT, ArgumentRefusal
from workbench.render.field_frames import (
    native_extent,
    overlay,
    saved_array,
    tile_edges,
)

#: The stacked arrays by the short names the writer gives them in
#: `record["interstice"]["arrays"]`, each with the dtype it must have and its number of axes.
INTERSTICE_ARRAYS: Mapping[str, tuple[np.dtype, int]] = {
    "extent": (np.dtype(np.bool_), 3),
    "first_wall_codes": (np.dtype(np.uint8), 1),
    "second_wall_codes": (np.dtype(np.uint8), 1),
    "content_tiles": (np.dtype(np.bool_), 3),
}

#: The stage's vocabularies by the name the record carries them under.
VOCABULARIES: Mapping[str, tuple[str, ...]] = {
    "code_names": INTERSTICE_CODES,
    "wall_code_names": WALL_CODES,
    "fill_code_names": FILL_CODES,
    "position_code_names": POSITION_CODES,
    "side_code_names": SIDE_CODES,
    "conjunction_code_names": CONJUNCTION_CODES,
}

#: What each standing an interstice can hold says, in words. The codes are the adapter's
#: (`knee.pictures.interstice.ENTRY_STANDINGS`); the words are this drawing's.
STANDING_WORDS: Mapping[str, str] = {
    "named": "the extent, walls, fill and contents of this pair",
    "no_extent": "no extent: the pair faces across no tile at all",
    "predecessor_absent": (
        "not made: a predecessor was absent; the stage's own reason is beside"
    ),
    "code_unknown": "not drawn: the saved code is one the stage does not say",
}

#: What each place a plane can come from says, in words.
PLANE_WORDS: Mapping[str, str] = {
    "saved": "over the acquired plane saved with the interstices at this slice",
    "walk": "over the acquired plane at the study's walked slice",
    "selected": "over the series' selected plane",
    "tiles_alone": "tiles alone: no saved plane shows this slice",
}

#: What each content's position is drawn in; the tint of the extent. None of them is a colour a
#: stored value is drawn in. Every word of `POSITION_CODES` has one.
POSITION_COLOURS: Mapping[str, str] = {
    "peripheral": "#f59e0b",
    "central": "#a855f7",
    "invalid_measurement": "#ef4444",
}
EXTENT_COLOUR = "#06b6d4"
EXTENT_ALPHA = 0.38
#: The pale tile grid drawn where no saved plane shows the slice: its face and its edges.
GRID_FACE = "#f3f4f6"
GRID_EDGE = "#d1d5db"

#: One panel for the text, then one per interstice, at most this many panels across.
PANELS_ACROSS = 4
PANEL_INCHES = 4.6
ROW_INCHES = 5.6
DPI = 120


def whole(value: object, where: str, minimum: int = 0) -> int:
    """A saved whole number at least `minimum`; anything else is a record that disagrees."""
    if type(value) is not int or value < minimum:
        raise ValueError(f"saved_interstice_not_a_whole_number:{where}")
    return value


def saved_tile(value: object, where: str, tiles: tuple[int, int]) -> list[int] | None:
    """A saved [row, column] inside the grid, or None where the writer saved none."""
    if value is None:
        return None
    if not (
        isinstance(value, list)
        and len(value) == 2
        and all(type(item) is int for item in value)
        and 0 <= value[0] < tiles[0]
        and 0 <= value[1] < tiles[1]
    ):
        raise ValueError(f"saved_interstice_tile_invalid:{where}")
    return value


def saved_content(content: object, where: str) -> None:
    """One saved content: its index, the stage's words and a finite centre, or the disagreement."""
    if type(content) is not dict:
        raise ValueError(f"saved_interstice_content_invalid:{where}")
    whole(content.get("index"), f"{where}.index", 1)
    if content.get("position_code") not in POSITION_CODES:
        raise ValueError(f"saved_interstice_position_unknown:{where}")
    if content.get("side_code") not in SIDE_CODES:
        raise ValueError(f"saved_interstice_side_unknown:{where}")
    centre = content.get("centre_lps")
    if not (
        isinstance(centre, list)
        and len(centre) == 3
        and all(
            isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
            for v in centre
        )
    ):
        raise ValueError(f"saved_interstice_centre_invalid:{where}")


def saved_entry(entry: object, position: int, tiles: tuple[int, int]) -> None:
    """One saved interstice's scalars and words, checked against the stage's vocabularies."""
    where = f"interstices[{position}]"
    if type(entry) is not dict:
        raise ValueError(f"saved_interstice_entry_invalid:{where}")
    whole(entry.get("slice_index"), f"{where}.slice_index", -1)
    whole(entry.get("first"), f"{where}.first")
    whole(entry.get("second"), f"{where}.second")
    if type(entry.get("why")) is not str:
        raise ValueError(f"saved_interstice_field_invalid:{where}.why")
    if entry.get("code") not in INTERSTICE_CODES:
        raise ValueError(f"saved_interstice_code_unknown:{entry.get('code')}")
    if entry.get("fill_code") not in FILL_CODES:
        raise ValueError(f"saved_interstice_fill_unknown:{entry.get('fill_code')}")
    counts = entry.get("fill_counts")
    if not (
        type(counts) is dict
        and all(
            word in CONJUNCTION_CODES and type(count) is int and count >= 0
            for word, count in counts.items()
        )
    ):
        raise ValueError(f"saved_interstice_counts_invalid:{where}")
    whole(entry.get("first_wall_count"), f"{where}.first_wall_count")
    whole(entry.get("second_wall_count"), f"{where}.second_wall_count")
    for key in ("first_at_rc", "second_at_rc"):
        saved_tile(entry.get(key), f"{where}.{key}", tiles)
    contents = entry.get("contents")
    if type(contents) is not list:
        raise ValueError(f"saved_interstice_contents_invalid:{where}")
    for number, content in enumerate(contents):
        saved_content(content, f"{where}.contents[{number}]")


def saved_interstices(
    run: Path, record: dict
) -> tuple[Path, pictures.InterstitialPanels]:
    """Reconstitute one series' saved interstices and the planes they lie over, without measuring.

    Total over a series whose writer saved no interstice: that is handed on as the silence it is.
    A record that is not a mapping, vocabularies that are not the stage's, a tile grid that is not
    two whole numbers, an interstice with a code, fill, position or side the stage does not say,
    an array whose dtype, shape or digest disagrees with its descriptor or whose length is not the
    sum of the saved counts, a wall code outside the vocabulary, an interstice saved without the
    series' squint stack, over another grid than the stack's, or over a plane of another size,
    a walk whose saved indices do not match its slices, means the record and this renderer
    disagree, and is raised rather than drawn.
    """
    artifact = run / record["artifact"]
    descriptors = record["arrays"]
    saved_study = record.get("study") or {}
    walk_name = saved_study.get("walk_array")
    walk_indices = tuple(int(index) for index in saved_study.get("walk_indices", ()))
    selected = record.get("slice_index")
    selected_index = selected if type(selected) is int else None
    saved = record.get("interstice")
    if saved is None:
        return artifact, pictures.interstice_panels(
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            (),
            None,
            walk_indices,
            None,
            None,
            None,
        )
    if type(saved) is not dict:
        raise ValueError("saved_interstice_not_a_record")
    for key, vocabulary in VOCABULARIES.items():
        if saved.get(key) != list(vocabulary):
            raise ValueError("saved_interstice_vocabulary_mismatch")
    shape = saved.get("tiles_rc")
    if not (
        isinstance(shape, list)
        and len(shape) == 2
        and all(type(size) is int and size >= 1 for size in shape)
    ):
        raise ValueError("saved_interstice_tiles_invalid")
    tiles = (int(shape[0]), int(shape[1]))
    entries = saved.get("interstices")
    if type(entries) is not list:
        raise ValueError("saved_interstice_entries_invalid")
    for position, entry in enumerate(entries):
        saved_entry(entry, position, tiles)
    names = saved.get("arrays")
    if type(names) is not dict:
        raise ValueError("saved_interstice_arrays_missing")
    for short in INTERSTICE_ARRAYS:
        if type(names.get(short)) is not str:
            raise ValueError(f"saved_interstice_array_unnamed:{short}")
    # The planes saved with the interstices are an optional pair: both keys, or neither. Neither
    # is a writer that saved no planes, which is a silence the picture names (it falls back to the
    # walked plane, the selected plane, or the tiles alone); one without the other disagrees.
    plane_slices = saved.get("plane_slices")
    plane_name = names.get("planes")
    if (plane_slices is None) != (plane_name is None):
        raise ValueError("saved_interstice_planes_incomplete")
    if plane_slices is not None and not (
        isinstance(plane_slices, list)
        and all(type(index) is int and index >= 0 for index in plane_slices)
        and len(set(plane_slices)) == len(plane_slices)
    ):
        raise ValueError("saved_interstice_plane_slices_invalid")
    if plane_name is not None and type(plane_name) is not str:
        raise ValueError("saved_interstice_array_unnamed:planes")
    drawn: dict[str, np.ndarray] = {}
    walk = selected_plane = planes = None
    with np.load(artifact, allow_pickle=False) as arrays:
        for short, (dtype, ndim) in INTERSTICE_ARRAYS.items():
            array = saved_array(arrays, descriptors, names[short], ndim)
            if array.dtype != dtype:
                raise ValueError(f"saved_interstice_representation_invalid:{short}")
            drawn[short] = array
        if plane_name is not None:
            planes = saved_array(arrays, descriptors, plane_name, 3)
            if planes.dtype.kind not in "iuf":
                raise ValueError("saved_interstice_representation_invalid:planes")
        if walk_name is not None:
            walk = saved_array(arrays, descriptors, walk_name, 3)
        if "acquired_plane" in descriptors:
            selected_plane = saved_array(arrays, descriptors, "acquired_plane", 2)
    if walk is not None and walk.shape[0] != len(walk_indices):
        raise ValueError("saved_walk_indices_mismatch")
    contents = sum(len(entry["contents"]) for entry in entries)
    expected = {
        "extent": (len(entries), *tiles),
        "first_wall_codes": (sum(entry["first_wall_count"] for entry in entries),),
        "second_wall_codes": (sum(entry["second_wall_count"] for entry in entries),),
        "content_tiles": (contents, *tiles),
    }
    for short, wanted in expected.items():
        if drawn[short].shape != wanted:
            raise ValueError(f"saved_interstice_shape_mismatch:{short}")
    for short in ("first_wall_codes", "second_wall_codes"):
        if drawn[short].size and int(drawn[short].max()) >= len(WALL_CODES):
            raise ValueError("saved_interstice_wall_code_unknown")
    # The interstices are made over the series' own squint stack; its saved bounds are what place
    # the tiles on the plane, so a record that saved the one and not the other disagrees.
    if "squint_stack" not in record:
        raise ValueError("saved_interstice_without_a_stack")
    _, stack = squint_stack_frames.saved_stack(run, record)
    bounds = stack.bounds_rc
    if bounds is None or tuple(bounds.shape[:2]) != tiles:
        raise ValueError("saved_interstice_grid_mismatch")
    plane_size = (int(bounds[-1, -1, 1]), int(bounds[-1, -1, 3]))
    if planes is not None and planes.shape[0] != len(plane_slices or ()):
        raise ValueError("saved_interstice_planes_mismatch")
    saved_planes = planes if planes is not None else ()
    for plane in (selected_plane, *saved_planes, *(walk if walk is not None else ())):
        if plane is not None and tuple(plane.shape) != plane_size:
            raise ValueError("saved_interstice_covers_another_plane")
    return artifact, pictures.interstice_panels(
        entries,
        drawn["extent"],
        drawn["first_wall_codes"],
        drawn["second_wall_codes"],
        drawn["content_tiles"],
        tiles,
        bounds,
        tuple(plane_slices or ()),
        planes,
        walk_indices,
        walk,
        selected_index,
        selected_plane,
    )


def image_name(index: int, record: dict) -> str:
    """One sheet per series, named as the view sheets are: its order, plane and the two flags."""
    view, fluid, fat = record["view"]
    return f"{index:02d}-{view.lower()}-fs{fluid}-fat{fat}.png"


def words(pairs: tuple[tuple[str, int], ...], silence: str) -> str:
    """Saved (word, count) pairs as text; the silence in words where there are none."""
    if not pairs:
        return silence
    return " · ".join(f"{word} {count}" for word, count in pairs)


def sheet_lines(record: dict, frame: pictures.InterstitialPanels) -> list[str]:
    """The text panel: the series, its view, how many interstices are saved and what each says."""
    view, fluid, fat = record["view"]
    lines = [
        wrapped(record["series_uid"], width=40),
        f"{view} · fluid-sensitive={fluid}, fat-suppressed={fat}",
        "",
    ]
    if not frame.saved:
        lines.append("interstices (relations): not saved")
        lines.append(
            wrapped("this run's writer saved no interstice for this series", width=40)
        )
        return lines
    lines += [
        f"interstices (relations): {len(frame.panels)} saved",
        f"grid          {frame.tiles_rc[0]} x {frame.tiles_rc[1]} tiles"
        if frame.tiles_rc is not None
        else "grid          not saved",
        "",
    ]
    for number, panel in enumerate(frame.panels, start=1):
        lines.append(
            f"{number}. slice {panel.slice_index} · objects {panel.first}, {panel.second}"
        )
        lines.append(f"   {panel.code}")
        lines.append(wrapped(f"   why: {panel.why}", width=40, subsequent_indent="   "))
    return lines


def outline_segments(mask: np.ndarray, edges) -> list[tuple]:
    """The tile edges that face outside a tile mask: where its outline runs, in native pixels.

    A drawing's geometry over a saved mask and the saved tile edges, nothing measured: a side of
    a masked tile is drawn when the tile beyond it is outside the grid or not in the mask.
    """
    columns, rows = edges
    tiles_down, tiles_across = mask.shape
    segments = []
    for row, column in zip(*np.nonzero(mask), strict=True):
        left, right = columns[column], columns[column + 1]
        top, bottom = rows[row], rows[row + 1]
        sides = (
            (-1, 0, ((left, top), (right, top))),
            (1, 0, ((left, bottom), (right, bottom))),
            (0, -1, ((left, top), (left, bottom))),
            (0, 1, ((right, top), (right, bottom))),
        )
        for step_row, step_column, segment in sides:
            beyond_row, beyond_column = row + step_row, column + step_column
            inside = 0 <= beyond_row < tiles_down and 0 <= beyond_column < tiles_across
            if not inside or not mask[beyond_row, beyond_column]:
                segments.append(segment)
    return segments


def place(edges, tile) -> tuple[float, float]:
    """A tile's centre in native pixels, from the saved edges: (x across, y down)."""
    columns, rows = edges
    row, column = tile
    return (columns[column] + columns[column + 1]) / 2, (rows[row] + rows[row + 1]) / 2


def wall_text(label: str, tally: tuple[tuple[str, int], ...]) -> str:
    """One wall's words as a small block: its object, then each word with its count."""
    if not tally:
        return f"{label}\nno profile read"
    return label + "\n" + "\n".join(f"{word} {count}" for word, count in tally)


def draw_entry(axis, panel: pictures.InterstitialPanel, frame) -> str:
    """One interstice: the extent over the plane, its contents outlined, its fill and walls in words.

    Returns `drawn` for a named reading, else the standing the panel holds in words. The extent
    is a saved tile map tinted over the plane; nothing is derived from it.
    """
    from matplotlib.collections import LineCollection
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch

    axis.set_axis_off()
    title = f"slice {panel.slice_index} · objects {panel.first}, {panel.second} · {panel.code}"
    if panel.standing not in ("named", "no_extent"):
        axis.set_title(title, fontsize=8)
        message = STANDING_WORDS[panel.standing]
        if panel.standing == "predecessor_absent":
            message = f"{message}: {panel.why}"
        axis.text(
            0.03,
            0.95,
            wrapped(message, width=44),
            transform=axis.transAxes,
            va="top",
            fontsize=7,
        )
        return panel.standing
    edges = tile_edges(frame.bounds_rc)
    columns_edges, rows_edges = edges
    if panel.plane is not None:
        axis.imshow(
            panel.plane,
            cmap="gray",
            interpolation="nearest",
            extent=native_extent(panel.plane.shape),
        )
    else:
        # No saved plane shows this slice: the tile grid itself is drawn, pale, so the extent and
        # the contents have somewhere to be seen. It is the saved edges and nothing more.
        axis.pcolormesh(
            columns_edges,
            rows_edges,
            np.zeros(panel.extent.shape),
            cmap=ListedColormap([GRID_FACE]),
            edgecolors=GRID_EDGE,
            linewidth=0.3,
            vmin=0.0,
            vmax=1.0,
        )
    handles = []
    if panel.extent.any():
        overlay(axis, edges, panel.extent, EXTENT_COLOUR, alpha=EXTENT_ALPHA)
        handles.append(
            Patch(
                facecolor=EXTENT_COLOUR,
                alpha=EXTENT_ALPHA,
                label=f"extent ({int(panel.extent.sum())} tiles)",
            )
        )
    for content in panel.contents:
        colour = POSITION_COLOURS[content.position_code]
        axis.add_collection(
            LineCollection(
                outline_segments(content.tiles, edges), colors=colour, linewidths=1.8
            )
        )
        first_tile = tuple(int(v) for v in np.argwhere(content.tiles)[0])
        x, y = place(edges, first_tile)
        # Labels alternate above and below their tile, so neighbouring contents do not overprint.
        axis.text(
            x,
            y,
            f"{content.index}: {content.position_code}, {content.side_code}",
            fontsize=5,
            color=colour,
            ha="center",
            va="bottom" if content.index % 2 else "top",
            bbox={"facecolor": "black", "edgecolor": "none", "alpha": 0.6, "pad": 0.6},
        )
    axis.set_xlim(0, float(columns_edges[-1]))
    axis.set_ylim(float(rows_edges[-1]), 0)
    axis.set_aspect("equal")
    caption = []
    for label, at, tally in (
        (f"object {panel.first}", panel.first_at_rc, panel.first_walls),
        (f"object {panel.second}", panel.second_at_rc, panel.second_walls),
    ):
        text = wall_text(f"{label}'s wall", tally)
        if at is None:
            caption.append(text.replace("\n", ": ", 1).replace("\n", " · "))
            continue
        x, y = place(edges, at)
        axis.text(
            x,
            y,
            text,
            fontsize=5,
            color="white",
            ha="center",
            va="center",
            bbox={
                "facecolor": "#111827",
                "edgecolor": "none",
                "alpha": 0.7,
                "pad": 1.0,
            },
        )
    counts = words(panel.fill_counts, "no conjunction word counted")
    caption.append(f"fill {panel.fill_code}: {counts}")
    axis.text(
        0.5,
        -0.01,
        wrapped("\n".join(caption), width=64),
        transform=axis.transAxes,
        ha="center",
        va="top",
        fontsize=5.5,
    )
    if handles:
        axis.legend(handles=handles, loc="upper right", fontsize=5.5, frameon=False)
    words_here = (
        f"{STANDING_WORDS[panel.standing]}, {PLANE_WORDS[panel.plane_standing]}"
    )
    axis.set_title(f"{title}\n{wrapped(words_here, width=52)}", fontsize=7.5)
    return "drawn"


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
    loaded = [saved_interstices(run, record) for record in records]
    if pictures.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:interstice")
    # Every standing the adapter can name has words here, and every position word a colour,
    # checked before anything is drawn.
    unworded = [
        name
        for name in (*pictures.ENTRY_STANDINGS, *pictures.PLANE_STANDINGS)
        if name not in STANDING_WORDS and name not in PLANE_WORDS
    ]
    if unworded:
        raise RuntimeError(f"interstice_standing_unworded:{','.join(unworded)}")
    uncoloured = [name for name in POSITION_CODES if name not in POSITION_COLOURS]
    if uncoloured:
        raise RuntimeError(f"interstice_vocabulary_uncoloured:{','.join(uncoloured)}")

    import matplotlib.pyplot as plt

    target.mkdir(parents=True, exist_ok=True)
    series = []
    for index, (record, (artifact, frame)) in enumerate(
        zip(records, loaded, strict=True), start=1
    ):
        count = 1 + max(len(frame.panels), 0)
        across = min(count, PANELS_ACROSS)
        down = math.ceil(count / across)
        sheet, axes = plt.subplots(
            down,
            across,
            figsize=(PANEL_INCHES * across, ROW_INCHES * down),
            layout="constrained",
            squeeze=False,
        )
        for axis in axes.flat:
            axis.set_axis_off()
        text = axes[0, 0]
        text.set_title("the interstices", fontsize=8)
        text.text(
            0.0,
            1.0,
            "\n".join(sheet_lines(record, frame)),
            transform=text.transAxes,
            va="top",
            family="monospace",
            fontsize=6.5,
        )
        panels = []
        for number, panel in enumerate(frame.panels, start=1):
            axis = axes[number // across, number % across]
            panels.append(
                {
                    "slice_index": panel.slice_index,
                    "first": panel.first,
                    "second": panel.second,
                    "code": panel.code,
                    "standing": panel.standing,
                    "plane_standing": panel.plane_standing,
                    "extent_tiles": int(panel.extent.sum()),
                    "fill_code": panel.fill_code,
                    "walls": {
                        "first": dict(panel.first_walls),
                        "second": dict(panel.second_walls),
                    },
                    "contents": [
                        {
                            "index": content.index,
                            "position_code": content.position_code,
                            "side_code": content.side_code,
                        }
                        for content in panel.contents
                    ],
                    "drawn": draw_entry(axis, panel, frame),
                }
            )
        view, fluid, fat = record["view"]
        sheet.suptitle(
            f"The funnel's interstices · {view} · fluid-sensitive={fluid}, "
            f"fat-suppressed={fat} · series {record['series_uid']}\n"
            "per facing pair: the extent (cyan) over the acquired plane at the pair's slice, "
            "each content outlined with its index, position and side, the fill word with the "
            "conjunction words counted over the extent, and each wall's words at its object\n"
            "outline: amber peripheral · purple central · red a refused position",
            fontsize=9,
        )
        name = image_name(index, record)
        sheet.savefig(target / name, dpi=DPI)
        plt.close(sheet)
        saved = record.get("interstice")
        series.append(
            {
                "image": name,
                "image_sha256": sha256((target / name).read_bytes()).hexdigest(),
                "series_uid": record["series_uid"],
                "artifact": record["artifact"],
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "view": record["view"],
                "interstice": None
                if saved is None
                else {
                    "tiles_rc": list(frame.tiles_rc or ()),
                    "arrays": {
                        short: record["arrays"][key]
                        for short, key in saved["arrays"].items()
                    },
                },
                "panels": panels,
                "frame_kind": "study",
            }
        )
    manifest = {
        "schema": "interstice-frames-v1",
        "receipt_sha256": sha256(receipt_bytes).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": {
            "interstice": sha256(Path(pictures.__file__).read_bytes()).hexdigest()
        },
        "study_uid": study_uid,
        "image": series[0]["image"],
        "images": [entry["image"] for entry in series],
        "frame_kind": "study",
        "standings": list(pictures.ENTRY_STANDINGS),
        "plane_standings": list(pictures.PLANE_STANDINGS),
        "legend": {
            "extent": EXTENT_COLOUR,
            "extent_alpha": EXTENT_ALPHA,
            "content_outline_by_position": dict(POSITION_COLOURS),
        },
        "series": series,
        "note": (
            "Every value is a saved one. A pair that faces across no tile, a pair the stage "
            "could not make and a series this run's writer saved nothing for are three "
            "silences, each named; none is a zero. One sheet per series, for the founder's "
            "eye-check."
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
