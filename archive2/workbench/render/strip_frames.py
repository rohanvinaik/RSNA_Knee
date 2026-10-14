"""Draw the funnel's strips: one sheet per series, one panel per object, the edge read at native resolution.

The-funnel task 6.5 (`openspec/changes/the-funnel/tasks.md`; the taut outline of task 6.4 is a later
unit and is not drawn). The funnel's operation 6 (`knee.objects.strip`) casts a profile across each
midpoint of an object's tile boundary at native resolution, reads each for its dark band, and names
the outcome. This workbench arranges those saved values through `knee.pictures.strip`: ONE SHEET PER
SERIES (one image per series record), so the founder can check by eye (task 6.6, E4) that the lines
are where the bones end: a text panel with the series, then one panel per saved strip, each over the
acquired plane at that strip's own slice, at native resolution. In a panel every edge point is
coloured by its trace code; each bracketed band's midpoint is a cyan point; the strip's footprint,
the pixels the casts read, is tinted faintly, so the silence everywhere else is plain to see; and,
where a partner's bands were carried to the points, a ring marks each point by its exchange code.
It takes no measurement of its own: every number on the page is a saved value, and every gap is a
named silence, never a zero.

Five silences are kept apart, because each has its own remedy
(`knee.pictures.strip.STRIP_STANDINGS`): this run's writer saved no strips for the series; the saved
code is a word the stage does not say; the stage made no strip and says why (a plane, labels or
bounds were absent); the object has no tile boundary; the strip was made and the writer saved no
plane at its slice, so its points are drawn alone. A saved record that disagrees with the writer
(a vocabulary that is not the stage's, an array whose dtype, shape or digest disagrees with its
descriptor, a code value outside the vocabulary, counts that are not the arrays', a plane that is
not the footprint's) is refused rather than drawn. Nothing here thresholds, labels, dilates or
recomputes a code. The grey scale is Matplotlib's linear display scale over each plane's own values.

Each chosen slice is read under two borders (`knee.objects.tile_dome.BORDER_CODES`, both seated on
the founder's ruling of 2026-10-12, "keep everything, including where things conflict"), so a
series' record holds two strips for one slice and object index, one per border, and every entry
names its border. The sheet draws them next to each other so the founder compares them: one row
of cells per (slice, object index), the first border on the left and the second on the right,
every panel titled with its border. The two borders number their territories separately, so a
row pairs two strips by their slice and index alone; that is a place on the sheet and never a
claim that they are one object. A border with no strip at an index is a named silence,
`unpaired`. A record whose entry names a border that is not a word of `BORDER_CODES`, or repeats a
(border, slice, object) already saved, is refused by name.
"""

import argparse
import json
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from textwrap import fill
from typing import Any

import numpy as np

from knee.objects.conversation import EXCHANGE_CODES
from knee.objects.interiors import TRACE_CODES
from knee.objects.strip import STRIP_CODES
from knee.objects.tile_dome import BORDER_CODES
from knee.pictures import strip as pictures
from workbench.render._out import PROJECT, ArgumentRefusal
from workbench.render.field_frames import saved_array

#: The strip's arrays by the short names the writer gives them in each saved strip's `arrays`, each
#: with the dtype it must have and its number of axes. All ten are saved; seven are drawn
#: (`beyond_tiles`, the tile each profile enters, is checked and kept for the interstice).
STRIP_ARRAYS: Mapping[str, tuple[np.dtype, int]] = {
    "edge_points": (np.dtype(np.float64), 2),
    "normals": (np.dtype(np.float64), 2),
    "offsets_mm": (np.dtype(np.float64), 1),
    "profiles": (np.dtype(np.float64), 2),
    "trace_codes": (np.dtype(np.uint8), 1),
    "band_mm": (np.dtype(np.float64), 2),
    "exchange_codes": (np.dtype(np.uint8), 1),
    "native_digits": (np.dtype(np.int8), 2),
    "strip_mask": (np.dtype(np.bool_), 2),
    "beyond_tiles": (np.dtype(np.int64), 2),
}

#: What each standing says, in words. The codes are the adapter's
#: (`knee.pictures.strip.STRIP_STANDINGS`); the words are this drawing's.
STANDING_WORDS: Mapping[str, str] = {
    "named": "every edge point by its trace code, over the plane at this slice",
    "strip_not_saved": "not saved: this run's writer saved no strip for this series",
    "strip_code_unknown": "not drawn: the saved code is one the stage does not say",
    "strip_absent": "not made: the stage cast nothing; its own reason is beside",
    "strip_has_no_boundary": (
        "not drawn: the object has no tile boundary, so nothing was cast"
    ),
    "plane_not_saved": (
        "points alone: the writer saved no plane at this slice, so the points are "
        "drawn on a blank field of the footprint's size"
    ),
}

#: The standings with nothing to draw but words.
SILENT_STANDINGS: tuple[str, ...] = (
    "strip_not_saved",
    "strip_code_unknown",
    "strip_absent",
    "strip_has_no_boundary",
)

#: What each trace code is drawn in. No colour is one a stored value is drawn in.
TRACE_COLOURS: Mapping[str, str] = {
    "bracketed": "#16a34a",
    "no_dark_bracket": "#9ca3af",
    "multiple_brackets": "#f59e0b",
    "missing_profile": "#a855f7",
    "frame_clipped": "#ef4444",
    "empty_profile": "#92400e",
    "invalid_measurement": "#111827",
}

#: What each exchange code is drawn in, as a ring about the point. 0, a point no partner band was
#: carried to, is never drawn.
EXCHANGE_COLOURS: Mapping[str, str] = {
    "concurrent": "#2563eb",
    "peer_only": "#0891b2",
    "disagreement": "#dc2626",
    "native_missing": "#7c3aed",
    "native_open": "#ea580c",
    "native_multiple": "#ca8a04",
    "outside_slab": "#4b5563",
    "slab_support_unknown": "#6b7280",
    "normal_unavailable": "#9ca3af",
    "empty_profile": "#92400e",
    "invalid_measurement": "#000000",
}

#: Each bracketed band's midpoint, and the strip's footprint.
BAND_COLOUR = "#06b6d4"
MASK_COLOUR = "#3b82f6"
MASK_ALPHA = 0.28

#: A sheet: the text column this many inches wide, then the pairs of strips (one cell per border
#: in each) this many pairs to a row, each panel this many inches across and each row this many
#: inches tall.
PAIRS_PER_ROW = 2
TEXT_INCHES = 4.6
PANEL_INCHES = 4.6
ROW_INCHES = 5.4
DPI = 120

#: The name of an exchange code of 0 in the manifest and the legend.
NOT_CARRIED = "not_carried"

#: What a cell of a pair holds when its border saved no strip at that slice and object index, and
#: what the cell says. It is not a standing of a strip (there is none), so it is not in
#: `knee.pictures.strip.STRIP_STANDINGS`.
UNPAIRED = "unpaired"
UNPAIRED_WORDS = (
    "no strip is saved under this border for this object index at this slice. The two borders "
    "number their territories separately, so an index one border has may not exist in the other"
)


def saved_number(value: object, where: str) -> float | None:
    """A saved reading as a float; None where the writer saved None (a reading the stage did not make).

    A value that is neither None nor a finite number is a record that disagrees, and is raised.
    """
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not np.isfinite(value)
    ):
        raise ValueError(f"saved_strip_not_a_number:{where}")
    return float(value)


def saved_whole(value: object, where: str, minimum: int) -> int:
    """A saved whole number at or above `minimum`; anything else is a record that disagrees."""
    if type(value) is not int or value < minimum:
        raise ValueError(f"saved_strip_not_a_whole_number:{where}")
    return value


def saved_spacing(value: object) -> tuple[float, float] | None:
    """The plane's saved spacing (rows, columns) in millimetres, None where the writer saved none."""
    if value is None:
        return None
    if (
        not isinstance(value, list)
        or len(value) != 2
        or not all(
            not isinstance(item, bool)
            and isinstance(item, (int, float))
            and np.isfinite(item)
            and item > 0
            for item in value
        )
    ):
        raise ValueError("saved_strip_spacing_invalid")
    return float(value[0]), float(value[1])


def saved_panel(
    arrays: Mapping[str, np.ndarray],
    descriptors: dict,
    item: Any,
    spacing: tuple[float, float] | None,
    position: int,
) -> pictures.StripPanel:
    """Reconstitute one saved strip and hand it to the adapter, without measuring.

    The strip's arrays are found through its own `arrays` map (never by rebuilding a key) and
    checked against the top-level descriptor table by dtype, shape and digest; its codes against
    the stage's vocabularies; its counts against the arrays'. The entry names its border, which
    must be a word of `BORDER_CODES`. Anything that disagrees means the record and this renderer
    disagree, and is raised rather than drawn.
    """
    if type(item) is not dict:
        raise ValueError(f"saved_strip_not_a_record:{position}")
    for key in ("series_uid", "border", "code", "why"):
        if type(item.get(key)) is not str:
            raise ValueError(f"saved_strip_field_invalid:{key}")
    if item["border"] not in BORDER_CODES:
        raise ValueError(f"saved_strip_border_unknown:{item['border']}")
    if item["code"] not in STRIP_CODES:
        raise ValueError(f"saved_strip_code_unknown:{item['code']}")
    object_index = saved_whole(item.get("object_index"), "object_index", 1)
    # The stage is told its slice and refuses a negative one, so a saved slice is a stack index.
    slice_index = saved_whole(item.get("slice_index"), "slice_index", 0)
    count = saved_whole(item.get("population_count"), "population_count", 0)
    points_saved = saved_whole(item.get("points"), "points", 0)
    offsets_saved = saved_whole(item.get("offsets"), "offsets", 0)
    names = item.get("arrays")
    if type(names) is not dict:
        raise ValueError("saved_strip_arrays_missing")
    drawn: dict[str, np.ndarray] = {}
    for short, (dtype, ndim) in STRIP_ARRAYS.items():
        key = names.get(short)
        if type(key) is not str:
            raise ValueError(f"saved_strip_array_unnamed:{short}")
        array = saved_array(arrays, descriptors, key, ndim)
        if array.dtype != dtype:
            raise ValueError(f"saved_strip_representation_invalid:{short}")
        drawn[short] = array
    points = drawn["edge_points"].shape[0]
    width = drawn["offsets_mm"].shape[0]
    expected = {
        "edge_points": (points, 2),
        "normals": (points, 2),
        "trace_codes": (points,),
        "band_mm": (points, 2),
        "profiles": (points, width),
        "native_digits": (points, width),
        "beyond_tiles": (points, 2),
    }
    for short, shape in expected.items():
        if drawn[short].shape != shape:
            raise ValueError(f"saved_strip_shape_mismatch:{short}")
    # With a partner handed over there is one code per point; with none, none at all.
    if drawn["exchange_codes"].shape not in ((points,), (0,)):
        raise ValueError("saved_strip_shape_mismatch:exchange_codes")
    if points_saved != points or offsets_saved != width:
        raise ValueError("saved_strip_counts_mismatch")
    if not np.isin(drawn["trace_codes"], list(TRACE_CODES.values())).all():
        raise ValueError("saved_strip_trace_code_unknown")
    if not np.isin(drawn["exchange_codes"], [0, *EXCHANGE_CODES.values()]).all():
        raise ValueError("saved_strip_exchange_code_unknown")
    plane = None
    plane_name = item.get("plane_array")
    if plane_name is not None:
        if type(plane_name) is not str:
            raise ValueError("saved_strip_field_invalid:plane_array")
        plane = saved_array(arrays, descriptors, plane_name, 2)
        if plane.dtype.kind not in "iuf":
            raise ValueError("saved_strip_representation_invalid:plane")
        if drawn["strip_mask"].size and plane.shape != drawn["strip_mask"].shape:
            raise ValueError("saved_strip_plane_mismatch")
    return pictures.strip_panel(
        item["series_uid"],
        slice_index,
        object_index,
        item["code"],
        item["why"],
        saved_number(item.get("strip_mm"), "strip_mm"),
        saved_number(item.get("low_edge"), "low_edge"),
        saved_number(item.get("high_edge"), "high_edge"),
        count,
        spacing,
        plane,
        drawn["edge_points"],
        drawn["normals"],
        drawn["trace_codes"],
        drawn["band_mm"],
        drawn["exchange_codes"],
        drawn["strip_mask"],
        item["border"],
    )


def saved_strips(
    run: Path, record: dict
) -> tuple[Path, tuple[pictures.StripPanel, ...] | None]:
    """Reconstitute one series' saved strips, without measuring.

    None where the writer saved no strips for the series, which is drawn as the silence it is; an
    empty tuple where it saved the record and no object had a strip. A strips record that is not a
    mapping, vocabularies that are not the stage's, items that are not a list, a spacing that is
    not two positive numbers, or any strip that disagrees (see `saved_panel`) means the record and
    this renderer disagree, and is raised rather than drawn. So is a record that saves two strips
    under one (border, slice, object index), `saved_strips_entry_repeated`: the strips are keyed
    by all three and never by the slice alone, and a repeated key would hide one of the two.
    """
    artifact = run / record["artifact"]
    saved = record.get("strips")
    if saved is None:
        return artifact, None
    if type(saved) is not dict:
        raise ValueError("saved_strips_not_a_record")
    if (
        saved.get("code_names") != list(STRIP_CODES)
        or saved.get("trace_code_values") != dict(TRACE_CODES)
        or saved.get("exchange_code_values") != dict(EXCHANGE_CODES)
    ):
        raise ValueError("saved_strips_vocabulary_mismatch")
    items = saved.get("items")
    if type(items) is not list:
        raise ValueError("saved_strips_items_invalid")
    spacing = saved_spacing(record.get("spacing_rc_mm"))
    descriptors = record["arrays"]
    with np.load(artifact, allow_pickle=False) as arrays:
        panels = tuple(
            saved_panel(arrays, descriptors, item, spacing, position)
            for position, item in enumerate(items)
        )
    seen: set[tuple[str | None, int | None, int | None]] = set()
    for panel in panels:
        key = (panel.border, panel.slice_index, panel.object_index)
        if key in seen:
            raise ValueError(f"saved_strips_entry_repeated:{key[0]}:{key[1]}:{key[2]}")
        seen.add(key)
    return artifact, panels


def trace_counts(panel: pictures.StripPanel) -> dict[str, int]:
    """How many points carry each trace code, from the saved codes; empty when none were saved."""
    if panel.trace_codes is None:
        return {}
    return {
        name: int(np.count_nonzero(panel.trace_codes == value))
        for name, value in TRACE_CODES.items()
    }


def exchange_counts(panel: pictures.StripPanel) -> dict[str, int]:
    """How many points carry each exchange code, 0 as `not_carried`; empty with no partner."""
    if panel.exchange_codes is None or not panel.exchange_codes.size:
        return {}
    counts = {NOT_CARRIED: int(np.count_nonzero(panel.exchange_codes == 0))}
    counts.update(
        {
            name: int(np.count_nonzero(panel.exchange_codes == value))
            for name, value in EXCHANGE_CODES.items()
        }
    )
    return counts


def bracketed_centres(panel: pictures.StripPanel) -> int:
    """How many band midpoints the panel places: the saved centres that are numbers."""
    if panel.band_centres_rc is None:
        return 0
    return int(np.count_nonzero(np.isfinite(panel.band_centres_rc).all(axis=1)))


def number(value: float | None) -> str:
    """A saved reading as text; None is how a reading the stage did not make comes back."""
    return "not read" if value is None else f"{value:g}"


def image_name(index: int, record: dict) -> str:
    """One sheet per series, named as the view sheets are: its order, plane and the two flags."""
    view, fluid, fat = record["view"]
    return f"{index:02d}-{view.lower()}-fs{fluid}-fat{fat}.png"


def cell_title(
    border: str | None, slice_index: int | None, object_index: int | None
) -> str:
    """A cell's title: the border it was read under first, then the object and the slice, as saved."""
    return f"{border} · object {object_index} · slice {slice_index}"


def heading(panel: pictures.StripPanel) -> str:
    """A panel's title: whose strip it is, as saved, with the border it was read under."""
    return cell_title(panel.border, panel.slice_index, panel.object_index)


def paired_cells(
    panels: tuple[pictures.StripPanel, ...],
) -> tuple[tuple[int, int, tuple[pictures.StripPanel | None, ...]], ...]:
    """The saved strips arranged for the sheet: one row per (slice, object index), one cell per border.

    Each row is (slice_index, object_index, cells): the rows in increasing order of slice and then
    object index, the cells in the order of `BORDER_CODES`, a cell None where that border saved no
    strip at that slice and index. It only places the saved panels; it measures, counts and decides
    nothing. The two borders number their territories separately, so a row pairs two strips by their
    slice and index alone: a place on the sheet, never a claim that they are one object. A panel that
    cannot be placed (no slice, no object index, or a border outside `BORDER_CODES`) is refused,
    `strip_panel_unplaceable`, and so are two panels under one (border, slice, object index),
    `strip_panel_repeated`: placing the second over the first would hide a saved strip.
    """
    placed: dict[tuple[int, int, str], pictures.StripPanel] = {}
    for panel in panels:
        if (
            type(panel.slice_index) is not int
            or type(panel.object_index) is not int
            or panel.border not in BORDER_CODES
        ):
            raise ValueError("strip_panel_unplaceable")
        key = (panel.slice_index, panel.object_index, panel.border)
        if key in placed:
            raise ValueError("strip_panel_repeated")
        placed[key] = panel
    rows = sorted({(slice_index, index) for slice_index, index, _ in placed})
    return tuple(
        (
            slice_index,
            index,
            tuple(placed.get((slice_index, index, border)) for border in BORDER_CODES),
        )
        for slice_index, index in rows
    )


def strip_lines(
    record: dict, panels: tuple[pictures.StripPanel, ...] | None
) -> list[str]:
    """The text panel: the series, its view, and each saved strip's standing, counts and terciles."""
    view, fluid, fat = record["view"]
    lines = [
        fill(record["series_uid"], width=40),
        f"{view} · fluid-sensitive={fluid}, fat-suppressed={fat}",
        "",
    ]
    if panels is None:
        lines.append("strips (objects): not saved")
        lines.append(fill(STANDING_WORDS["strip_not_saved"], width=40))
        return lines
    spacing = record.get("spacing_rc_mm")
    rows = paired_cells(panels)
    lines += [
        f"strips saved   {len(panels)}",
        "spacing (mm)   "
        + ("not saved" if spacing is None else " x ".join(f"{s:g}" for s in spacing)),
        fill(
            f"{len(rows)} rows, each a slice and an object index with a cell for "
            f"each border: {', '.join(BORDER_CODES)}",
            width=40,
        ),
    ]
    if not panels:
        lines += ["", fill("no object had a strip made for this series", width=40)]
    for panel in (cell for _, _, held in rows for cell in held if cell is not None):
        lines += ["", f"{heading(panel)}: {panel.code}"]
        # A strip the stage did not cast says why in its own words. A cast strip's reason is in
        # the receipt, and repeating it here would run the column past the sheet.
        if panel.code != "present":
            lines.append(fill(f"why: {panel.why}", width=40))
        else:
            points = 0 if panel.edge_points is None else len(panel.edge_points)
            lines.append(f"  points {points}, bands placed {bracketed_centres(panel)}")
            lines += [
                f"  {name:<20}{count}"
                for name, count in trace_counts(panel).items()
                if count
            ]
        shown = exchange_counts(panel)
        if shown:
            lines.append(
                "  partner handed over: "
                + ", ".join(f"{k} {v}" for k, v in shown.items() if v)
            )
            if not any(count for name, count in shown.items() if name != NOT_CARRIED):
                lines.append("  no partner band was carried to the points")
        if panel.code in ("present", "no_boundary"):
            lines.append(
                f"  terciles ({number(panel.low_edge)}, {number(panel.high_edge)}) "
                f"of {panel.population_count} own pixels"
            )
    return lines


def centre_extent(shape: tuple[int, ...]) -> tuple[float, float, float, float]:
    """An image's extent so that pixel (r, c) is centred on the native coordinate (r, c)."""
    return -0.5, float(shape[1]) - 0.5, float(shape[0]) - 0.5, -0.5


def draw_unpaired(axis, border: str, slice_index: int, object_index: int) -> str:
    """The cell of a border that saved no strip at this slice and object index: the silence, in words."""
    axis.set_axis_off()
    axis.set_title(cell_title(border, slice_index, object_index), fontsize=8)
    axis.text(
        0.03, 0.95, fill(UNPAIRED_WORDS, width=38), transform=axis.transAxes, va="top"
    )
    return UNPAIRED


def draw_panel(axis, panel: pictures.StripPanel) -> str:
    """One strip: the plane in grey, the footprint tinted, the points by code, or the silence in words.

    Returns `named` when the points are drawn over their plane, `points_alone` when the writer
    saved no plane at the slice, and the standing itself for a silence.
    """
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch

    axis.set_axis_off()
    if panel.standing in SILENT_STANDINGS:
        axis.set_title(heading(panel), fontsize=8)
        words = STANDING_WORDS[panel.standing]
        if panel.standing == "strip_absent" and panel.why:
            words = f"{words}: {panel.why}"
        axis.text(0.03, 0.95, fill(words, width=38), transform=axis.transAxes, va="top")
        return panel.standing
    mask = panel.strip_mask
    shape = (
        panel.plane.shape
        if panel.plane is not None
        else (mask.shape if mask is not None else (0, 0))
    )
    if panel.plane is not None:
        axis.imshow(
            panel.plane,
            cmap="gray",
            interpolation="nearest",
            extent=centre_extent(shape),
        )
    handles = []
    if mask is not None and mask.any():
        axis.imshow(
            np.ma.masked_where(~mask, np.ones(mask.shape)),
            cmap=ListedColormap([MASK_COLOUR]),
            vmin=0.0,
            vmax=1.0,
            alpha=MASK_ALPHA,
            interpolation="nearest",
            extent=centre_extent(mask.shape),
        )
        handles.append(
            Patch(
                facecolor=MASK_COLOUR,
                alpha=MASK_ALPHA,
                label=f"the strip's footprint ({int(mask.sum())} px)",
            )
        )
    points, codes = panel.edge_points, panel.trace_codes
    if points is not None and codes is not None:
        for name, value in TRACE_CODES.items():
            chosen = codes == value
            if not chosen.any():
                continue
            handles.append(
                axis.scatter(
                    points[chosen, 1],
                    points[chosen, 0],
                    s=18,
                    c=TRACE_COLOURS[name],
                    linewidths=0,
                    label=f"{name} ({int(chosen.sum())})",
                )
            )
        centres = panel.band_centres_rc
        if centres is not None:
            placed = np.isfinite(centres).all(axis=1)
            if placed.any():
                handles.append(
                    axis.scatter(
                        centres[placed, 1],
                        centres[placed, 0],
                        s=26,
                        c=BAND_COLOUR,
                        edgecolors="black",
                        linewidths=0.4,
                        label=f"band midpoints ({int(placed.sum())})",
                    )
                )
        carried = panel.exchange_codes
        if carried is not None and carried.size:
            for name, value in EXCHANGE_CODES.items():
                chosen = carried == value
                if not chosen.any():
                    continue
                handles.append(
                    axis.scatter(
                        points[chosen, 1],
                        points[chosen, 0],
                        s=90,
                        facecolors="none",
                        edgecolors=EXCHANGE_COLOURS[name],
                        linewidths=1.2,
                        label=f"partner: {name} ({int(chosen.sum())})",
                    )
                )
    axis.set_xlim(-0.5, float(shape[1]) - 0.5)
    axis.set_ylim(float(shape[0]) - 0.5, -0.5)
    axis.set_aspect("equal")
    if handles:
        axis.legend(
            handles=handles,
            loc="upper center",
            bbox_to_anchor=(0.5, 0.0),
            ncol=2,
            fontsize=5.5,
            frameon=False,
        )
    where = (
        "over the acquired plane at native resolution"
        if panel.plane is not None
        else "points alone: no plane saved"
    )
    axis.set_title(f"{heading(panel)}\n{where}", fontsize=8)
    return "named" if panel.plane is not None else "points_alone"


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
    loaded = [saved_strips(run, record) for record in records]
    if pictures.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:strip")
    # Every standing the adapter can name has words here, and every code of either vocabulary a
    # colour, checked before anything is drawn.
    unworded = [name for name in pictures.STRIP_STANDINGS if name not in STANDING_WORDS]
    if unworded:
        raise RuntimeError(f"strip_standing_unworded:{','.join(unworded)}")
    uncoloured = [name for name in TRACE_CODES if name not in TRACE_COLOURS] + [
        name for name in EXCHANGE_CODES if name not in EXCHANGE_COLOURS
    ]
    if uncoloured:
        raise RuntimeError(f"strip_vocabulary_uncoloured:{','.join(uncoloured)}")

    import matplotlib.pyplot as plt

    target.mkdir(parents=True, exist_ok=True)
    series = []
    for index, (record, (artifact, panels)) in enumerate(
        zip(records, loaded, strict=True), start=1
    ):
        # One row per (slice, object index) and a cell for each border in it: a pair is drawn
        # side by side, so the founder compares the two borders' readings at a glance.
        rows = paired_cells(panels or ())
        shown = max(len(rows), 1)
        pairs_across = min(shown, PAIRS_PER_ROW)
        across = pairs_across * len(BORDER_CODES) if rows else 1
        down = -(-shown // pairs_across)
        # The text is its own tall column, so a long record never runs into a panel beside it.
        sheet = plt.figure(
            figsize=(TEXT_INCHES + PANEL_INCHES * across, ROW_INCHES * down),
            layout="constrained",
        )
        grid = sheet.add_gridspec(
            down,
            1 + across,
            width_ratios=[TEXT_INCHES / PANEL_INCHES] + [1.0] * across,
        )
        text = sheet.add_subplot(grid[:, 0])
        cells = [
            sheet.add_subplot(grid[row, 1 + column])
            for row in range(down)
            for column in range(across)
        ]
        for axis in (text, *cells):
            axis.set_axis_off()
        text.set_title("the strips", fontsize=8)
        text.text(
            0.0,
            1.0,
            "\n".join(strip_lines(record, panels)),
            transform=text.transAxes,
            va="top",
            family="monospace",
            fontsize=6.5,
        )
        drawn, pairs = [], []
        if not panels:
            words = (
                STANDING_WORDS["strip_not_saved"]
                if panels is None
                else "saved, and no object had a strip made for this series"
            )
            cells[0].text(
                0.03,
                0.5,
                fill(words, width=38),
                transform=cells[0].transAxes,
                va="center",
            )
        for position, (slice_index, object_index, held) in enumerate(rows):
            row, column = divmod(position, pairs_across)
            first = row * across + column * len(BORDER_CODES)
            standings = {}
            for offset, (border, panel) in enumerate(
                zip(BORDER_CODES, held, strict=True)
            ):
                axis = cells[first + offset]
                if panel is None:
                    standings[border] = draw_unpaired(
                        axis, border, slice_index, object_index
                    )
                    continue
                standings[border] = draw_panel(axis, panel)
                drawn.append(
                    {
                        "border": panel.border,
                        "object_index": panel.object_index,
                        "slice_index": panel.slice_index,
                        "code": panel.code,
                        "standing": panel.standing,
                        "drawn": standings[border],
                        "points": 0
                        if panel.edge_points is None
                        else len(panel.edge_points),
                        "band_midpoints": bracketed_centres(panel),
                        "trace_counts": trace_counts(panel),
                        "exchange_counts": exchange_counts(panel),
                    }
                )
            pairs.append(
                {
                    "slice_index": slice_index,
                    "object_index": object_index,
                    "cells": standings,
                }
            )
        view, fluid, fat = record["view"]
        sheet.suptitle(
            f"The funnel's strips · {view} · fluid-sensitive={fluid}, fat-suppressed={fat} · "
            f"series {record['series_uid']}\n"
            "each object's edge read at native resolution along its tile boundary, over the "
            "acquired plane at its own slice\n"
            f"each pair, one slice and object index under both borders: {BORDER_CODES[0]} on "
            f"the left, {BORDER_CODES[1]} on the right (the borders number their territories "
            "separately)\n"
            "points by trace code (green: a dark band bracketed) · cyan: the band's midpoint · "
            "blue tint: the pixels the casts read, silence elsewhere · rings: the partner's "
            "exchange code",
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
                "strips": None if panels is None else drawn,
                "pairs": None if panels is None else pairs,
                "frame_kind": "study",
            }
        )
    manifest = {
        "schema": "strip-frames-v2",
        "receipt_sha256": sha256(receipt_bytes).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": {
            "strip": sha256(Path(pictures.__file__).read_bytes()).hexdigest()
        },
        "study_uid": study_uid,
        "image": series[0]["image"],
        "images": [entry["image"] for entry in series],
        "frame_kind": "study",
        "standings": list(pictures.STRIP_STANDINGS),
        "borders": list(BORDER_CODES),
        "legend": {
            "trace_codes": dict(TRACE_COLOURS),
            "exchange_codes": dict(EXCHANGE_COLOURS),
            "band_midpoints": BAND_COLOUR,
            "strip_footprint": MASK_COLOUR,
        },
        "series": series,
        "note": (
            "Every value is a saved one. A series whose writer saved no strips, a strip the "
            "stage did not make, an object with no boundary, a plane not saved at the "
            "strip's slice and a border with no strip at a slice and object index "
            "(unpaired) are five silences, each named; none is a zero. One sheet per "
            "series, for the founder's eye-check (task 6.6), the two borders' strips of "
            "one slice and object index side by side."
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
