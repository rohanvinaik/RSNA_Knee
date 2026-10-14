"""Draw the funnel's tile dome: one sheet per view, each chosen slice's territories on the squint medians, and its height.

The-funnel task 5.3 (`openspec/changes/the-funnel/tasks.md`). The funnel's operation 5
(`knee.objects.tile_dome`) reads, at each slice the depth collapse chose, the dome of the tiles
the first lens kept; the writer saves the domes beside the series' record. This workbench
arranges those saved values through `knee.pictures.tile_dome`: ONE SHEET PER VIEW (one image per
series), the stage's standing in words, then for each saved dome two panels in two rows.

The territories panel: the squint's tile medians at the dome's slice, over the acquired plane at
that exact slice when the writer saved one there, each tile placed in native pixels by the squint
stack's saved bounds; over them every territory in its own colour, the tiles the first lens
cleared in red at a low alpha (as the first lens's own sheet draws them), the obstacles it did
not clear in blue, and each peak as a cyan + numbered by the territory it holds. The height panel
beneath it: the height in millimetres on the interior tiles, the same two tints on the
obstacles, and a tile that is neither an obstacle nor an interior (no finite pixel, or a word the
stage does not say) in the colour no value takes.

It takes no measurement of its own: every number on the page is a saved value, and every gap is
a named silence, never a zero. Five silences are kept apart because each has its own remedy
(`knee.pictures.tile_dome.DOME_STANDINGS`): this run's writer saved no tile dome; the saved code
is a word the stage does not say; the stage made no dome and says why; the dome's slice lies
outside the slices the stack holds; and, for a dome that is drawn, the writer saved no acquired
plane at its slice, so the medians are drawn alone and the title says so. A record that
disagrees with the writer -- a vocabulary, a count, an array whose dtype, shape or digest is not
its descriptor's, a stack that is not the dome's grid, a peak or a label outside what the record
holds -- is refused by name rather than drawn.

Nothing here thresholds, labels, dilates or recomputes a height, a peak or a territory. The grey
scale is Matplotlib's linear display scale over each map's own stored values.
"""

import argparse
import json
from collections.abc import Mapping, Sequence
from hashlib import sha256
from pathlib import Path
from textwrap import fill

import numpy as np

from knee.objects.tile_dome import BORDER_CODES, DOME_CODES, DOME_TILE_CODES
from knee.pictures import tile_dome as pictures
from workbench.render import squint_stack_frames
from workbench.render._out import PROJECT, ArgumentRefusal
from workbench.render.field_frames import (
    UNREAD_COLOUR,
    native_extent,
    overlay,
    saved_array,
    tile_edges,
)

#: The tile dome's arrays by the short names the writer gives them in
#: `record["tile_dome"]["arrays"]`, each with the dtype it must have and its number of axes. The
#: grid arrays hold one tile grid per saved dome along their first axis; `peaks` and
#: `peak_height_mm` hold every dome's peaks one after the other.
TILE_DOME_ARRAYS: Mapping[str, tuple[np.dtype, int]] = {
    "obstacle": (np.dtype(np.bool_), 3),
    "cleared": (np.dtype(np.bool_), 3),
    "interior": (np.dtype(np.bool_), 3),
    "height": (np.dtype(np.float64), 3),
    "labels": (np.dtype(np.int32), 3),
    "peaks": (np.dtype(np.int64), 2),
    "peak_height_mm": (np.dtype(np.float64), 1),
}
GRID_ARRAYS: tuple[str, ...] = ("obstacle", "cleared", "interior", "height", "labels")

#: The standing of a column the sheet reserves for a slice's other border where the record holds
#: no dome of that slice under it. It is this drawing's own, not the adapter's: the adapter
#: names the standing of a dome the record holds, and here the record holds none.
BORDER_NOT_SAVED = "border_not_saved"

#: What each silence a saved dome can hold says, in words. The codes are the adapter's
#: (`knee.pictures.tile_dome.DOME_STANDINGS`); the words are this drawing's.
STANDING_WORDS: Mapping[str, str] = {
    "named": "the territories on the squint medians, with the peaks and the obstacles",
    "dome_not_saved": "not saved: this run's writer saved no tile dome for this series",
    "dome_code_unknown": "not drawn: the saved code is one the stage does not say",
    "dome_absent": "not made: the stage read no slice; its own reason is beside",
    "slice_outside_stack": "not drawn: the dome's slice lies outside the slices the stack holds",
    BORDER_NOT_SAVED: "not saved: the record holds no dome of this slice under this border",
}

#: What each tint is, and how much of what lies beneath it shows through. The cleared tiles are
#: drawn as the first lens's own sheet draws them. The obstacles the lens did not clear are the
#: dark tiles (a gap between two objects is made of them). Territories take the colours in turn.
CLEARED_COLOUR, CLEARED_ALPHA = "#ff1414", 0.28
DARK_COLOUR, DARK_ALPHA = "#2563eb", 0.5
TERRITORY_COLOURS: tuple[str, ...] = (
    "#16a34a",
    "#f59e0b",
    "#a855f7",
    "#ec4899",
    "#84cc16",
    "#eab308",
    "#b45309",
    "#6366f1",
)
TERRITORY_ALPHA = 0.5
PEAK_COLOUR = "#00e5ff"
MEDIAN_ALPHA = 0.62
NOT_READ_ALPHA = 0.85

#: One sheet per series: two rows, the text then the territories above, the key then the heights
#: beneath; one column per saved dome after the first.
PANEL_INCHES = 4.2
ROW_INCHES = 4.7
DPI = 120
#: How many characters of the nine-point title fit in an inch of sheet, with room to spare.
TITLE_CHARACTERS_PER_INCH = 11


def saved_number(value: object, where: str) -> float | None:
    """A saved bar as a float; None where the writer saved None (no dome was made to read it from).

    A value that is neither None nor a finite positive number is a record that disagrees.
    """
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not np.isfinite(value)
        or value <= 0
    ):
        raise ValueError(f"saved_tile_dome_not_a_number:{where}")
    return float(value)


def saved_dome_entries(
    saved: dict,
) -> tuple[list[object], list[str], list[str], list[str], list[int]]:
    """The saved domes' slice, border, word, reason and peak count, each checked against the stage's own.

    The slice is handed on AS SAVED, never coerced: one that is not a whole number inside the
    stack is the adapter's silence, `slice_outside_stack`, in words on the page. A dome is
    identified by its (border, slice): an entry whose border is missing or not text is refused
    by name (`saved_tile_dome_dome_invalid:<position>:border`), so is one whose border is not a
    word of the stage's (`saved_tile_dome_border_unknown`), and so are two entries of one border
    and one slice (`saved_tile_dome_entry_duplicated`), because a sheet that drew either would
    draw one reading twice or let one stand for the other. The order of the entries is not
    load-bearing: nothing here is keyed by position but the arrays, which follow the entries.
    """
    count = saved.get("slices")
    entries = saved.get("domes")
    if type(count) is not int or count < 0:
        raise ValueError("saved_tile_dome_slices_invalid")
    if type(entries) is not list or len(entries) != count:
        raise ValueError("saved_tile_dome_slices_mismatch")
    indices, borders, codes, whys, peak_counts = [], [], [], [], []
    seen: set[tuple[str, str]] = set()
    for position, entry in enumerate(entries):
        if not isinstance(entry, dict) or "slice_index" not in entry:
            raise ValueError(f"saved_tile_dome_dome_invalid:{position}")
        code, why, peaks = entry.get("code"), entry.get("why"), entry.get("peaks")
        if type(code) is not str:
            raise ValueError(f"saved_tile_dome_dome_invalid:{position}:code")
        if type(why) is not str:
            raise ValueError(f"saved_tile_dome_dome_invalid:{position}:why")
        if code not in DOME_CODES:
            raise ValueError(f"saved_tile_dome_code_unknown:{code}")
        if type(peaks) is not int or peaks < 0:
            raise ValueError(f"saved_tile_dome_dome_invalid:{position}:peaks")
        border = entry.get("border")
        if type(border) is not str:
            raise ValueError(f"saved_tile_dome_dome_invalid:{position}:border")
        if border not in BORDER_CODES:
            raise ValueError(f"saved_tile_dome_border_unknown:{border}")
        # The slice is whatever was saved, so it is keyed by its repr and never by its value: a
        # `1`, a `1.0` and a `True` are three different things on a record.
        key = (border, repr(entry["slice_index"]))
        if key in seen:
            raise ValueError(
                f"saved_tile_dome_entry_duplicated:{border}:{entry['slice_index']}"
            )
        seen.add(key)
        indices.append(entry["slice_index"])
        borders.append(border)
        codes.append(code)
        whys.append(why)
        peak_counts.append(peaks)
    return indices, borders, codes, whys, peak_counts


def check_domes_against_arrays(
    drawn: dict[str, np.ndarray],
    tiles: tuple[int, int],
    count: int,
    peak_counts: list[int],
) -> None:
    """The saved arrays against the record's own counts: shapes, then each dome's peaks and labels.

    Raised by name when they disagree: an array whose shape is not (domes, tiles down, tiles
    across), peaks that are not the sum of the counts, a peak outside the grid, a label that no
    peak of its dome holds.
    """
    grid = (count, tiles[0], tiles[1])
    for short in GRID_ARRAYS:
        if drawn[short].shape != grid:
            raise ValueError(f"saved_tile_dome_shape_mismatch:{short}")
    total = sum(peak_counts)
    if drawn["peaks"].shape != (total, 2):
        raise ValueError("saved_tile_dome_shape_mismatch:peaks")
    if drawn["peak_height_mm"].shape != (total,):
        raise ValueError("saved_tile_dome_shape_mismatch:peak_height_mm")
    starts = np.concatenate(([0], np.cumsum(np.asarray(peak_counts, dtype=np.int64))))
    for position in range(count):
        mine = drawn["peaks"][starts[position] : starts[position + 1]]
        if mine.size and (
            int(mine.min()) < 0
            or int(mine[:, 0].max()) >= tiles[0]
            or int(mine[:, 1].max()) >= tiles[1]
        ):
            raise ValueError(f"saved_tile_dome_peak_outside_grid:{position}")
        labels = drawn["labels"][position]
        if labels.size and (int(labels.min()) < 0 or int(labels.max()) > len(mine)):
            raise ValueError(f"saved_tile_dome_label_outside_peaks:{position}")


def saved_tile_dome(run: Path, record: dict) -> tuple[Path, pictures.TileDomePanels]:
    """Reconstitute one series' saved tile domes and the stack that places them, without measuring.

    Total over a series whose writer saved no tile dome: that is handed on as the silence it is.
    A record that is not a mapping, a code the stage does not say, vocabularies that are not the
    stage's, a bar that is not a number, domes that are not the record's count, a dome without a
    border word of the stage's, two domes of one border and one slice, an array whose
    dtype, shape or digest disagrees with its descriptor or with the record's own counts, a peak
    outside the grid, a label no peak holds, a dome saved without the squint stack that places
    it, a stack whose grid is not the dome's, or an acquired plane that is not the stack's plane,
    means the record and this renderer disagree, and is raised rather than drawn. The stack is
    read through the stack drawer's own reader, which validates it against the writer's
    descriptors; its bounds place the tiles, its medians lie under them, and its walk and the
    selected plane give the acquired planes, each only at the stack index it was saved at.
    """
    artifact = run / record["artifact"]
    descriptors = record["arrays"]
    saved = record.get("tile_dome")
    if saved is None:
        return artifact, pictures.dome_panels(
            code=None,
            why=None,
            prominence_mm=None,
            tile_mm=None,
            median=None,
            bounds_rc=None,
            indices=(),
            borders=(),
            codes=(),
            whys=(),
            peak_counts=(),
            obstacle=None,
            cleared=None,
            interior=None,
            height=None,
            labels=None,
            peaks=None,
            peak_height_mm=None,
            planes={},
        )
    if type(saved) is not dict:
        raise ValueError("saved_tile_dome_not_a_record")
    for key in ("code", "why"):
        if type(saved.get(key)) is not str:
            raise ValueError(f"saved_tile_dome_field_invalid:{key}")
    if saved["code"] not in DOME_CODES:
        raise ValueError(f"saved_tile_dome_code_unknown:{saved['code']}")
    if saved.get("code_names") != list(DOME_CODES) or saved.get(
        "tile_code_names"
    ) != list(DOME_TILE_CODES):
        raise ValueError("saved_tile_dome_vocabulary_mismatch")
    prominence = saved_number(saved.get("prominence_mm"), "prominence_mm")
    tiles = saved.get("tiles_rc")
    if not (
        isinstance(tiles, list)
        and len(tiles) == 2
        and all(type(size) is int and size >= 0 for size in tiles)
    ):
        raise ValueError("saved_tile_dome_tiles_invalid")
    indices, borders, codes, whys, peak_counts = saved_dome_entries(saved)
    names = saved.get("arrays")
    if type(names) is not dict:
        raise ValueError("saved_tile_dome_arrays_missing")
    for short in TILE_DOME_ARRAYS:
        if type(names.get(short)) is not str:
            raise ValueError(f"saved_tile_dome_array_unnamed:{short}")
    drawn: dict[str, np.ndarray] = {}
    plane = None
    with np.load(artifact, allow_pickle=False) as arrays:
        for short, (dtype, ndim) in TILE_DOME_ARRAYS.items():
            array = saved_array(arrays, descriptors, names[short], ndim)
            if array.dtype != dtype:
                raise ValueError(f"saved_tile_dome_representation_invalid:{short}")
            drawn[short] = array
        if "acquired_plane" in descriptors:
            plane = saved_array(arrays, descriptors, "acquired_plane", 2)
            if plane.dtype.kind not in "iuf":
                raise ValueError("saved_array_representation_invalid:acquired_plane")
    check_domes_against_arrays(
        drawn, (int(tiles[0]), int(tiles[1])), len(indices), peak_counts
    )

    median = bounds = tile_mm = None
    planes: dict[int, np.ndarray] = {}
    if any(code != "predecessor_absent" for code in codes):
        # The domes are placed by the series' own squint stack, so a record that saved the one
        # and not the other disagrees with the writer; the stack's grid must be the domes'.
        if "squint_stack" not in record:
            raise ValueError("saved_tile_dome_without_a_stack")
        _, stack = squint_stack_frames.saved_stack(run, record)
        if (
            stack.code != "present"
            or stack.bounds_rc is None
            or stack.median is None
            or tuple(stack.bounds_rc.shape[:2]) != (int(tiles[0]), int(tiles[1]))
        ):
            raise ValueError("saved_tile_dome_grid_mismatch")
        median, bounds, tile_mm = stack.median, stack.bounds_rc, stack.tile_mm
        extent = (int(bounds[-1, -1, 1]), int(bounds[-1, -1, 3]))
        for step in stack.walked:
            if step.plane is not None and type(step.index) is int:
                planes[step.index] = step.plane
        selected = record.get("slice_index")
        if plane is not None and type(selected) is int:
            planes.setdefault(selected, plane)
        if any(held.shape != extent for held in planes.values()):
            raise ValueError("saved_tile_dome_covers_another_plane")
    return artifact, pictures.dome_panels(
        saved["code"],
        saved["why"],
        prominence,
        tile_mm,
        median,
        bounds,
        indices,
        borders,
        codes,
        whys,
        peak_counts,
        drawn["obstacle"],
        drawn["cleared"],
        drawn["interior"],
        drawn["height"],
        drawn["labels"],
        drawn["peaks"],
        drawn["peak_height_mm"],
        planes,
    )


def millimetres(value: float | None) -> str:
    """A saved bar in millimetres as text; None is how a bar no dome could read comes back."""
    return "not read" if value is None else f"{value:g} mm"


def counted(count: int, one: str, many: str) -> str:
    """A count with its noun in the right number: 1 territory, 0 territories, 2 territories."""
    return f"{count} {one if count == 1 else many}"


def image_name(index: int, record: dict) -> str:
    """One sheet per view, named as the view sheets are: its order, plane and the two flags."""
    view, fluid, fat = record["view"]
    return f"{index:02d}-{view.lower()}-fs{fluid}-fat{fat}.png"


def dome_counts(panel: pictures.DomePanel) -> dict[str, int]:
    """How many tiles of one saved dome are interior, obstacle and cleared, counted from the saved masks."""
    if panel.interior is None or panel.obstacle is None or panel.cleared is None:
        return {}
    return {
        "interior": int(np.count_nonzero(panel.interior)),
        "obstacle": int(np.count_nonzero(panel.obstacle)),
        "cleared": int(np.count_nonzero(panel.cleared)),
        "peaks": 0 if panel.peaks is None else int(panel.peaks.shape[0]),
    }


def dome_lines(record: dict, frame: pictures.TileDomePanels) -> list[str]:
    """The text panel: the series, its view, the stage's standing, and one line per saved dome."""
    view, fluid, fat = record["view"]
    lines = [
        fill(record["series_uid"], width=40),
        f"{view} · fluid-sensitive={fluid}, fat-suppressed={fat}",
        "",
    ]
    if frame.code is None:
        lines.append("tile dome (objects): not saved")
        lines.append(fill(STANDING_WORDS["dome_not_saved"], width=40))
        return lines
    lines += [
        f"tile dome (objects): {frame.code}",
        fill(f"why: {frame.why}", width=40),
        "",
        f"prominence    {millimetres(frame.prominence_mm)}",
        f"tile          {millimetres(frame.tile_mm)}",
    ]
    if frame.bounds_rc is not None:
        lines.append(
            f"grid          {frame.bounds_rc.shape[0]} x {frame.bounds_rc.shape[1]} tiles"
        )
    lines += ["", "saved domes"]
    if not frame.domes:
        lines.append("  none: the depth collapse chose no slice")
    for panel in frame.domes:
        counts = dome_counts(panel)
        lines.append(
            f"  no slice read · {panel.border}: {panel.code}"
            if panel.standing == "dome_absent"
            else f"  slice {panel.index} · {panel.border}: {panel.code}"
        )
        if counts:
            lines.append(
                f"    {counted(counts['peaks'], 'peak', 'peaks')} · "
                f"interior {counts['interior']} · "
                f"obstacle {counts['obstacle']} · cleared {counts['cleared']}"
            )
    return lines


def tile_centre(edges: tuple[np.ndarray, np.ndarray], row: int, column: int):
    """A tile's centre in native pixel coordinates, read straight from the tile edges."""
    columns, rows = edges
    return (columns[column] + columns[column + 1]) / 2, (rows[row] + rows[row + 1]) / 2


def mark_peaks(axis, edges, panel: pictures.DomePanel) -> None:
    """Each peak as a cyan + at its tile's centre, numbered by the territory it holds."""
    if panel.peaks is None:
        return
    for territory, (row, column) in enumerate(panel.peaks.tolist(), start=1):
        x, y = tile_centre(edges, int(row), int(column))
        axis.plot(x, y, "+", color=PEAK_COLOUR, markersize=11, markeredgewidth=2.0)
        axis.text(
            x,
            y,
            f" {territory}",
            color=PEAK_COLOUR,
            fontsize=8,
            fontweight="bold",
            va="bottom",
            ha="left",
            bbox={"facecolor": "black", "alpha": 0.45, "pad": 0.6, "edgecolor": "none"},
        )


def silent_axis(axis, panel: pictures.DomePanel, what: str) -> str:
    """An axis that holds a dome's named silence in words, so it is never read as an empty picture."""
    axis.set_axis_off()
    axis.set_title(
        f"{panel.border} · no slice read"
        if panel.standing == "dome_absent"
        else f"{panel.border} · stack index {panel.index}",
        fontsize=8,
    )
    words = STANDING_WORDS[panel.standing]
    if panel.standing == "dome_absent" and panel.why:
        words = f"{words}: {panel.why}"
    axis.text(
        0.03,
        0.95,
        fill(f"{what}: {words}", width=38),
        transform=axis.transAxes,
        va="top",
    )
    return panel.standing


def missing_axis(axis, index: object, border: str, what: str) -> str:
    """An axis for a slice's other border where the record holds no dome of it, in words.

    The sheet reserves a column for each border of each slice so the founder can compare them;
    where the record holds one and not the other, the empty column says so rather than standing
    blank. Returns `BORDER_NOT_SAVED`.
    """
    axis.set_axis_off()
    axis.set_title(f"{border} · stack index {index}", fontsize=8)
    axis.text(
        0.03,
        0.95,
        fill(f"{what}: {STANDING_WORDS[BORDER_NOT_SAVED]}", width=38),
        transform=axis.transAxes,
        va="top",
    )
    return BORDER_NOT_SAVED


def draw_territories(axis, panel: pictures.DomePanel, frame: pictures.TileDomePanels):
    """One saved dome's territories on the squint medians over the plane, or its silence in words.

    Returns the dome's standing, or `medians_alone` when it is drawn with no plane beneath.
    """
    from matplotlib import colormaps
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    if (
        panel.standing != "named"
        or panel.median is None
        or panel.labels is None
        or panel.obstacle is None
        or panel.cleared is None
        or frame.bounds_rc is None
    ):
        return silent_axis(axis, panel, "territories")
    axis.set_axis_off()
    edges = tile_edges(frame.bounds_rc)
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
    if panel.plane is not None:
        axis.imshow(
            panel.plane,
            cmap="gray",
            interpolation="nearest",
            extent=native_extent(panel.plane.shape),
        )
        standing, where = "named", "over the acquired plane"
    else:
        standing, where = "medians_alone", "medians alone: no plane saved at this slice"
    axis.pcolormesh(
        columns_edges,
        rows_edges,
        panel.median,
        cmap=colormaps["gray"].with_extremes(bad=UNREAD_COLOUR),
        alpha=MEDIAN_ALPHA if panel.plane is not None else 1.0,
        **limits,
    )
    peaks = 0 if panel.peaks is None else int(panel.peaks.shape[0])
    for k in range(peaks):
        overlay(
            axis,
            edges,
            panel.labels == k + 1,
            TERRITORY_COLOURS[k % len(TERRITORY_COLOURS)],
            alpha=TERRITORY_ALPHA,
        )
    overlay(axis, edges, panel.cleared, CLEARED_COLOUR, alpha=CLEARED_ALPHA)
    overlay(axis, edges, panel.obstacle & ~panel.cleared, DARK_COLOUR, alpha=DARK_ALPHA)
    mark_peaks(axis, edges, panel)
    axis.set_xlim(0, float(columns_edges[-1]))
    axis.set_ylim(float(rows_edges[-1]), 0)
    axis.set_aspect("equal")
    axis.legend(
        handles=[
            Patch(
                facecolor=CLEARED_COLOUR, alpha=0.5, label="cleared by the first lens"
            ),
            Patch(facecolor=DARK_COLOUR, alpha=0.6, label="obstacle, not cleared"),
            Line2D(
                [],
                [],
                marker="+",
                color=PEAK_COLOUR,
                linestyle="",
                markersize=9,
                markeredgewidth=2.0,
                label="peak, numbered by its territory",
            ),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.0),
        ncol=1,
        fontsize=5.5,
        frameon=False,
    )
    axis.set_title(
        f"{panel.border} · stack index {panel.index} · {panel.code}\n"
        f"{counted(peaks, 'territory', 'territories')} on the squint medians\n{where}",
        fontsize=8,
    )
    return standing


def draw_height(axis, panel: pictures.DomePanel, frame: pictures.TileDomePanels) -> str:
    """One saved dome's height on its interior tiles with the obstacles tinted, or its silence in words."""
    if (
        panel.standing != "named"
        or panel.height is None
        or panel.interior is None
        or panel.obstacle is None
        or panel.cleared is None
        or frame.bounds_rc is None
    ):
        return silent_axis(axis, panel, "height")
    axis.set_axis_off()
    edges = tile_edges(frame.bounds_rc)
    columns_edges, rows_edges = edges
    has_interior = bool(panel.interior.any())
    if has_interior:
        mesh = axis.pcolormesh(
            columns_edges,
            rows_edges,
            np.ma.masked_where(~panel.interior, panel.height),
            cmap="viridis",
            vmin=0.0,
            vmax=float(panel.height[panel.interior].max()),
        )
        axis.figure.colorbar(mesh, ax=axis, shrink=0.7, label="height (mm)")
    overlay(axis, edges, panel.cleared, CLEARED_COLOUR, alpha=0.5)
    overlay(axis, edges, panel.obstacle & ~panel.cleared, DARK_COLOUR, alpha=0.7)
    overlay(
        axis,
        edges,
        ~(panel.obstacle | panel.interior),
        UNREAD_COLOUR,
        alpha=NOT_READ_ALPHA,
    )
    mark_peaks(axis, edges, panel)
    axis.set_xlim(0, float(columns_edges[-1]))
    axis.set_ylim(float(rows_edges[-1]), 0)
    axis.set_aspect("equal")
    axis.set_title(
        f"{panel.border} · stack index {panel.index}\n"
        "height above the nearest obstacle or the frame, mm"
        + ("" if has_interior else " · no interior tile"),
        fontsize=8,
    )
    return "named" if has_interior else "no_interior"


#: The sheet's key, in words: the label of each colour, as the panels draw it.
KEY_WORDS: Mapping[str, str] = {
    "cleared": "red: cleared by the first lens",
    "obstacle": (
        "blue: an obstacle the lens did not clear,\n"
        "by the panel's border: dark on both\n"
        "acquisitions (dark_on_both) or not bright on\n"
        "the partner acquisition (edge_of_bright_partner);\n"
        "on a solitary plane, at or below the split"
    ),
    "not_read": (
        "fuchsia: neither obstacle nor interior\n"
        "(no finite pixel in the tile, or a word\nthe stage does not say)"
    ),
    "territory": "green, amber, purple ...: a territory,\none colour for each peak in turn",
    "peak": "cyan +: a peak, numbered by the\nterritory it holds (tallest first)",
}


def draw_key(axis) -> None:
    """The colour key of the whole sheet, in words, in the first column of the second row."""
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    axis.set_axis_off()
    axis.set_title("the key", fontsize=8)
    axis.legend(
        handles=[
            Patch(facecolor=CLEARED_COLOUR, alpha=0.5, label=KEY_WORDS["cleared"]),
            Patch(facecolor=DARK_COLOUR, alpha=0.7, label=KEY_WORDS["obstacle"]),
            Patch(
                facecolor=UNREAD_COLOUR,
                alpha=NOT_READ_ALPHA,
                label=KEY_WORDS["not_read"],
            ),
            Patch(
                facecolor=TERRITORY_COLOURS[0],
                alpha=0.6,
                label=KEY_WORDS["territory"],
            ),
            Line2D(
                [],
                [],
                marker="+",
                color=PEAK_COLOUR,
                linestyle="",
                markersize=9,
                markeredgewidth=2.0,
                label=KEY_WORDS["peak"],
            ),
        ],
        loc="upper left",
        fontsize=6.5,
        frameon=False,
    )


def sheet_title(record: dict, width: int) -> str:
    """The sheet's title, each line wrapped to the sheet's own width so a sheet of one dome is never clipped."""
    view, fluid, fat = record["view"]
    lines = (
        (
            f"The funnel's tile dome · {view} · fluid-sensitive={fluid}, "
            f"fat-suppressed={fat} · series {record['series_uid']}"
        ),
        (
            "the stage's standing, then for each chosen slice the dome under each of its "
            "two borders side by side: the territories on the squint medians (over the "
            "acquired plane where the writer saved one at that slice), placed by the "
            "squint stack's own native bounds, and the height beneath"
        ),
        (
            "red: cleared by the first lens · blue: an obstacle it did not clear · "
            "cyan +: a peak, numbered by its territory · fuchsia: neither obstacle "
            "nor interior"
        ),
    )
    return "\n".join(fill(line, width=width) for line in lines)


def same_slice(first: object, second: object) -> bool:
    """Whether two saved slice indices are one slice: the same type and the same value.

    A saved index is handed on as it was saved, so `1`, `1.0` and `True` are three different
    things on a record and never one slice.
    """
    return type(first) is type(second) and first == second


def slice_columns(
    domes: Sequence[pictures.DomePanel],
) -> list[tuple[object, str, pictures.DomePanel | None]]:
    """The sheet's columns: each slice's readings under the stage's borders, next to each other.

    Pure arrangement of finished panels, which it neither alters nor re-pairs with arrays: a
    panel already carries its own dome's grids. Slices come in the order they first appear among
    the saved domes, so a record saved border by border and one saved slice by slice give one
    sheet; each slice then takes one column for each word of `BORDER_CODES`, in that order,
    holding the panel saved under that (slice, border), or None where the record holds none (the
    sheet then says so in words in that column, and never leaves it blank). A panel whose border
    is not a word of the stage's is refused by name, `tile_dome_border_unknown`: the reader
    refuses it first, so this meets one only from a caller that did not go through the reader.
    """
    for panel in domes:
        if panel.border not in BORDER_CODES:
            raise ValueError(f"tile_dome_border_unknown:{panel.border}")
    slices: list[object] = []
    for panel in domes:
        if not any(same_slice(panel.index, seen) for seen in slices):
            slices.append(panel.index)
    return [
        (
            index,
            border,
            next(
                (
                    panel
                    for panel in domes
                    if panel.border == border and same_slice(panel.index, index)
                ),
                None,
            ),
        )
        for index in slices
        for border in BORDER_CODES
    ]


def draw(run: Path, study_uid: str, out: Path) -> dict:
    """Draw this stage from the saved run, one sheet per view, and return its manifest.

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
    loaded = [saved_tile_dome(run, record) for record in records]
    if pictures.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:tile_dome")
    # Every standing the adapter can name has words here, checked before anything is drawn.
    unworded = [name for name in pictures.DOME_STANDINGS if name not in STANDING_WORDS]
    if unworded:
        raise RuntimeError(f"dome_standing_unworded:{','.join(unworded)}")

    import matplotlib.pyplot as plt

    target.mkdir(parents=True, exist_ok=True)
    series = []
    for index, (record, (artifact, frame)) in enumerate(
        zip(records, loaded, strict=True), start=1
    ):
        columns = slice_columns(frame.domes)
        across = 1 + max(len(columns), 1)
        sheet, axes = plt.subplots(
            2,
            across,
            figsize=(PANEL_INCHES * across, ROW_INCHES * 2),
            layout="constrained",
            squeeze=False,
        )
        for axis in axes.flat:
            axis.set_axis_off()
        text = axes[0, 0]
        text.set_title("the tile dome", fontsize=8)
        text.text(
            0.0,
            1.0,
            "\n".join(dome_lines(record, frame)),
            transform=text.transAxes,
            va="top",
            family="monospace",
            fontsize=6.5,
        )
        draw_key(axes[1, 0])
        drawn = []
        if not columns:
            axes[0, 1].text(
                0.03,
                0.5,
                "no tile dome saved for this series: no slice to draw"
                if frame.code is None
                else "the record holds no dome: no slice was read",
                transform=axes[0, 1].transAxes,
                va="center",
            )
        for column, (index, border, panel) in enumerate(columns, start=1):
            if panel is None:
                drawn.append(
                    {
                        "index": index,
                        "border": border,
                        "standing": BORDER_NOT_SAVED,
                        "code": None,
                        "drawn": {
                            "territories": missing_axis(
                                axes[0, column], index, border, "territories"
                            ),
                            "height": missing_axis(
                                axes[1, column], index, border, "height"
                            ),
                        },
                        "counts": {},
                    }
                )
                continue
            drawn.append(
                {
                    "index": panel.index,
                    "border": panel.border,
                    "standing": panel.standing,
                    "code": panel.code,
                    "drawn": {
                        "territories": draw_territories(axes[0, column], panel, frame),
                        "height": draw_height(axes[1, column], panel, frame),
                    },
                    "counts": dome_counts(panel),
                }
            )
        sheet.suptitle(
            sheet_title(record, int(PANEL_INCHES * across * TITLE_CHARACTERS_PER_INCH)),
            fontsize=9,
        )
        name = image_name(index, record)
        sheet.savefig(target / name, dpi=DPI)
        plt.close(sheet)
        saved = record.get("tile_dome")
        series.append(
            {
                "image": name,
                "image_sha256": sha256((target / name).read_bytes()).hexdigest(),
                "series_uid": record["series_uid"],
                "artifact": record["artifact"],
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "view": record["view"],
                "tile_dome": None
                if saved is None
                else {
                    "code": frame.code,
                    "why": frame.why,
                    "prominence_mm": frame.prominence_mm,
                    "tile_mm": frame.tile_mm,
                    "slices": len(frame.domes),
                    "tiles_rc": list(saved["tiles_rc"]),
                    "arrays": {
                        short: record["arrays"][key]
                        for short, key in saved["arrays"].items()
                    },
                },
                "domes": drawn,
                "frame_kind": "study",
            }
        )
    manifest = {
        "schema": "tile-dome-frames-v2",
        "receipt_sha256": sha256(receipt_bytes).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": {
            "tile_dome": sha256(Path(pictures.__file__).read_bytes()).hexdigest()
        },
        "study_uid": study_uid,
        "image": series[0]["image"],
        "images": [entry["image"] for entry in series],
        "frame_kind": "study",
        "standings": list(pictures.DOME_STANDINGS),
        "borders": list(BORDER_CODES),
        "column_standing": BORDER_NOT_SAVED,
        "legend": {
            "cleared": [CLEARED_COLOUR, CLEARED_ALPHA],
            "obstacle_not_cleared": [DARK_COLOUR, DARK_ALPHA],
            "territories": list(TERRITORY_COLOURS),
            "peak": PEAK_COLOUR,
            "not_read_tile": UNREAD_COLOUR,
        },
        "series": series,
        "note": (
            "Every value is a saved one. A dome the writer did not save, a dome the stage did "
            "not make, a slice the stack does not hold, a plane not saved at a dome's slice "
            "and a slice's other border the record holds no dome of are five silences, each "
            "named; none is a zero. One sheet per view, each slice's two borders side by "
            "side, for the founder's eye-check."
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
