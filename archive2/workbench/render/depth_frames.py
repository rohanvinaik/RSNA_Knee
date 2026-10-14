"""Draw the funnel's depth collapse: one sheet per series, the four readings over Z with each lens's slice marked, and the chosen slices themselves.

The-funnel task 4.5 (`openspec/changes/the-funnel/tasks.md`). The funnel's operation 4
(`knee.collapse.depth`) reads four cheap readings per slice of a series' squint stack and stands
each lens at the slice where its reading peaks; the writer saves the record whole beside the
stack. This workbench arranges those saved values through `knee.pictures.depth`: ONE SHEET PER
SERIES (one image per series), for the founder's eye-check (task 4.6, E2): on the left, the
four readings as curves over the stack index in one panel, each lens's chosen slice marked on
its own curve and named in the legend with its word and index; to the right, one panel per
distinct chosen slice, the acquired plane at that slice where this run saved one (the study
stage's walk, or the run's selected slice), else the squint stack's own tile medians at that
slice, placed by the stack's saved native bounds, the title saying which and naming the lenses
that chose it. It takes no measurement of its own: every number on the page is a saved value,
and every gap is a named silence, never a zero.

Four silences are kept apart on a view sheet, because each has its own remedy
(`knee.pictures.depth.SHEET_STANDINGS`): this run's writer saved no collapse for the series;
the saved code is a word the stage does not say; the stage stood no lens and says why (its
stack or its first lens was absent); the sheet's slice lies outside the slices the collapse
read. A series whose collapse is `predecessor_absent` draws its silence in words; a series at
which no lens stands draws the curves and says so. A collapse saved without the series' squint
stack, or over another number of slices than the stack's, disagrees with the writer and is
refused rather than drawn.

Nothing here reads a tile, re-reads a share or re-chooses a slice. The grey scale is
Matplotlib's linear display scale over each plane's own stored values.
"""

import argparse
import json
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from itertools import pairwise
from pathlib import Path
from textwrap import fill
from typing import Any

import numpy as np

from knee.collapse.depth import CHOICE_CODES, DEPTH_CODES, LENSES
from knee.pictures import depth as pictures
from workbench.render import squint_stack_frames
from workbench.render._out import PROJECT, ArgumentRefusal
from workbench.render.field_frames import (
    UNREAD_COLOUR,
    native_extent,
    saved_array,
    tile_edges,
)

#: The collapse's arrays by the short names the writer gives them in
#: `record["depth"]["arrays"]`, each with the dtype it must have and its number of axes.
DEPTH_ARRAYS: Mapping[str, tuple[np.dtype, int]] = {
    **{lens: (np.dtype(np.float64), 1) for lens in LENSES},
    "chosen_slices": (np.dtype(np.int64), 1),
}

#: What each silence a view sheet's slice can hold says, in words. The codes are the adapter's
#: (`knee.pictures.depth.SHEET_STANDINGS`); the words are this drawing's.
STANDING_WORDS: Mapping[str, str] = {
    "chosen": "this sheet's slice is one a lens stands at",
    "unchosen": "this sheet's slice is not one a lens stands at",
    "depth_not_saved": "not saved: this run's writer saved no depth collapse for this series",
    "depth_code_unknown": "not drawn: the saved code is one the stage does not say",
    "depth_absent": "not made: the stage stood no lens; its own code and reason are beside",
    "slice_outside_depth": (
        "not drawn: this sheet's slice lies outside the slices the collapse read"
    ),
}

#: What each source of a chosen slice's plane says, in words
#: (`knee.pictures.depth.PLANE_SOURCES`).
SOURCE_WORDS: Mapping[str, str] = {
    "walk": "the acquired plane at this slice, from the study stage's saved walk",
    "selected": "the acquired plane at this slice, the run's selected slice",
    "plane_not_saved": (
        "the squint's tile medians at this slice, placed by the stack's saved bounds: this "
        "run's writer saved no plane here"
    ),
}

#: Each lens's curve and marker, none of them a grey, so a reading is never mistaken for the
#: plane beneath it on a view sheet.
LENS_COLOURS: Mapping[str, str] = {
    "kept_share": "#2563eb",
    "dark_share": "#7c3aed",
    "split_quality": "#16a34a",
    "above_below_share": "#f59e0b",
}
LENS_MARKERS: Mapping[str, str] = {
    "kept_share": "o",
    "dark_share": "s",
    "split_quality": "^",
    "above_below_share": "D",
}

#: One sheet per series: the curves panel, then one panel per chosen slice.
PANEL_INCHES = 4.4
ROW_INCHES = 5.2
DPI = 120

#: The type sizes of an axis title and of the sheet's title, in points.
TITLE_POINTS = 8
SUPTITLE_POINTS = 9

#: How wide a line of a title may run, so that no word of it is cut by the picture's edge or
#: runs under the title beside it. A character is taken to be this fraction of the type size
#: wide (digits and capitals set widest in the face Matplotlib draws with, and a title is mostly
#: both), and a line may fill this fraction of the width it is centred in.
POINTS_PER_INCH = 72.0
CHARACTER_EM = 0.65
LINE_FILL = 0.8


def line_columns(inches: float, points: float) -> int:
    """How many characters one line of type of `points` may hold across `inches` of width (pure)."""
    return max(int(inches * POINTS_PER_INCH * LINE_FILL / (points * CHARACTER_EM)), 1)


#: The characters one line of an axis title may hold: one panel wide, at an axis title's size.
TITLE_COLUMNS = line_columns(PANEL_INCHES, TITLE_POINTS)


def wrapped(text: str, columns: int) -> str:
    """`text` filled to `columns` characters a line, a paragraph at a time, no word split (pure).

    A word longer than the line stays whole on a line of its own: a title is wrapped so that no
    word is cut, never so that no line runs long.
    """
    return "\n".join(
        fill(paragraph, width=columns, break_long_words=False, break_on_hyphens=False)
        for paragraph in text.split("\n")
    )


def saved_number(value: object, where: str) -> int:
    """A saved count or bar as an int: a whole non-negative number that is not a bool."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"saved_depth_not_a_count:{where}")
    return int(value)


def saved_depth(run: Path, record: dict) -> tuple[Path, pictures.DepthPanels]:
    """Reconstitute one series' saved depth collapse and the planes it can be shown on, without measuring.

    Total over a series whose writer saved no collapse: it is handed on as the silence it is. A
    collapse record that is not a mapping, a code the stage does not say, a vocabulary that is
    not the stage's, a bar or a count that is not a whole number, choices that are not one
    index and one word per lens, a word outside `CHOICE_CODES`, an array whose dtype, shape or
    digest disagrees with its descriptor, a reading whose length is not the saved slice count,
    chosen slices that are not the ascending distinct indices inside the readings, choices that
    do not agree with the chosen slices or with their own words, a collapse saved without the
    series' squint stack, or a stack holding another number of slices, means the record and
    this renderer disagree, and is raised rather than drawn. The stack is read through the
    stack drawer's own reader, which validates it against the writer's descriptors and hands on
    the study stage's walk; its medians and bounds show a chosen slice no plane was saved at.
    """
    artifact = run / record["artifact"]
    descriptors = record["arrays"]
    _, stack = squint_stack_frames.saved_stack(run, record)
    walk_indices = tuple(
        step.index for step in stack.walked if isinstance(step.index, int)
    )
    walk = (
        np.stack([step.plane for step in stack.walked])
        if stack.walked and all(step.plane is not None for step in stack.walked)
        else None
    )
    saved = record.get("depth")
    with np.load(artifact, allow_pickle=False) as arrays:
        plane = (
            saved_array(arrays, descriptors, "acquired_plane", 2)
            if "acquired_plane" in descriptors
            else None
        )
        if saved is None:
            drawn: dict[str, np.ndarray] = {}
        else:
            if type(saved) is not dict:
                raise ValueError("saved_depth_not_a_record")
            for key in ("code", "why"):
                if type(saved.get(key)) is not str:
                    raise ValueError(f"saved_depth_field_invalid:{key}")
            if saved["code"] not in DEPTH_CODES:
                raise ValueError(f"saved_depth_code_unknown:{saved['code']}")
            if (
                saved.get("code_names") != list(DEPTH_CODES)
                or saved.get("choice_code_names") != list(CHOICE_CODES)
                or saved.get("lenses") != list(LENSES)
            ):
                raise ValueError("saved_depth_vocabulary_mismatch")
            names = saved.get("arrays")
            if type(names) is not dict:
                raise ValueError("saved_depth_arrays_missing")
            for short in DEPTH_ARRAYS:
                if type(names.get(short)) is not str:
                    raise ValueError(f"saved_depth_array_unnamed:{short}")
            drawn = {}
            for short, (dtype, ndim) in DEPTH_ARRAYS.items():
                array = saved_array(arrays, descriptors, names[short], ndim)
                if array.dtype != dtype:
                    raise ValueError(f"saved_depth_representation_invalid:{short}")
                drawn[short] = array
    if saved is None:
        return artifact, pictures.depth_panels(
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            stack.median,
            stack.bounds_rc,
            walk_indices,
            walk,
            record.get("slice_index"),
            plane,
        )
    bar = saved_number(saved.get("minimum_valid"), "minimum_valid")
    slices = saved_number(saved.get("slices"), "slices")
    chosen_count = saved_number(saved.get("chosen"), "chosen")
    for lens in LENSES:
        if drawn[lens].shape != (slices,):
            raise ValueError(f"saved_depth_slices_mismatch:{lens}")
    chosen = [int(index) for index in drawn["chosen_slices"]]
    if len(chosen) != chosen_count:
        raise ValueError("saved_depth_chosen_mismatch")
    if any(not 0 <= index < slices for index in chosen) or any(
        later <= earlier for earlier, later in pairwise(chosen)
    ):
        raise ValueError("saved_depth_chosen_slices_invalid")
    indices, words = saved.get("chosen_index"), saved.get("choice_codes")
    if not (
        type(indices) is list
        and len(indices) == len(LENSES)
        and all(type(index) is int for index in indices)
        and all(index == -1 or 0 <= index < slices for index in indices)
    ):
        raise ValueError("saved_depth_choices_invalid")
    if not (
        type(words) is list
        and len(words) == len(LENSES)
        and all(type(word) is str and word in CHOICE_CODES for word in words)
    ):
        raise ValueError("saved_depth_choice_code_unknown")
    standing = {index for index in indices if index >= 0}
    if standing != set(chosen) or any(
        (index == -1) != (word not in ("chosen", "tie_middle"))
        for index, word in zip(indices, words, strict=True)
    ):
        raise ValueError("saved_depth_choices_mismatch")
    if "squint_stack" not in record:
        raise ValueError("saved_depth_without_a_stack")
    if stack.slices != slices:
        raise ValueError("saved_depth_stack_mismatch")
    return artifact, pictures.depth_panels(
        saved["code"],
        saved["why"],
        bar,
        drawn["kept_share"],
        drawn["dark_share"],
        drawn["split_quality"],
        drawn["above_below_share"],
        tuple(indices),
        tuple(words),
        tuple(chosen),
        stack.median,
        stack.bounds_rc,
        walk_indices,
        walk,
        record.get("slice_index"),
        plane,
    )


def standing_words(standing: pictures.LensStanding) -> str:
    """One lens's standing as the legend and the titles word it: its slice and word, or nowhere."""
    if standing.index >= 0:
        return f"{standing.lens}: slice {standing.index} ({standing.code})"
    return f"{standing.lens}: nowhere ({standing.code})"


def image_name(index: int, record: dict) -> str:
    """One sheet per series, named as the view sheets are: its order, plane and the two flags."""
    view, fluid, fat = record["view"]
    return f"{index:02d}-{view.lower()}-fs{fluid}-fat{fat}.png"


def draw_curves(axis, record: dict, frame: pictures.DepthPanels) -> str:
    """The four readings over the stack index, each lens's chosen slice marked on its own curve.

    Returns `drawn`, or the silence the panel holds when the collapse was not saved or not made.
    """
    view, fluid, fat = record["view"]
    identity = (
        f"{record['series_uid'][-16:]} · {view} · fluid-sensitive={fluid}, "
        f"fat-suppressed={fat}"
    )
    if frame.code is None:
        axis.set_axis_off()
        axis.set_title(
            wrapped(f"{identity}\nthe depth collapse: not saved", TITLE_COLUMNS),
            fontsize=TITLE_POINTS,
        )
        axis.text(
            0.03,
            0.95,
            fill(STANDING_WORDS["depth_not_saved"], width=48),
            transform=axis.transAxes,
            va="top",
        )
        return "depth_not_saved"
    if frame.code != "present" or not frame.readings:
        axis.set_axis_off()
        axis.set_title(
            wrapped(f"{identity}\nthe depth collapse: {frame.code}", TITLE_COLUMNS),
            fontsize=TITLE_POINTS,
        )
        axis.text(
            0.03,
            0.95,
            fill(f"{STANDING_WORDS['depth_absent']}: {frame.why}", width=48),
            transform=axis.transAxes,
            va="top",
        )
        return "depth_absent"
    steps = np.arange(frame.slices)
    for lens, reading in frame.readings:
        axis.plot(
            steps,
            reading,
            color=LENS_COLOURS[lens],
            linewidth=1.2,
            marker=".",
            markersize=3,
        )
    for standing in frame.standings:
        if standing.index >= 0 and np.isfinite(standing.reading):
            axis.plot(
                [standing.index],
                [standing.reading],
                marker=LENS_MARKERS[standing.lens],
                markersize=9,
                markerfacecolor="none",
                markeredgewidth=1.6,
                color=LENS_COLOURS[standing.lens],
                linestyle="none",
            )
            axis.axvline(
                standing.index,
                color=LENS_COLOURS[standing.lens],
                linewidth=0.6,
                linestyle=":",
            )
    axis.set_xlim(-0.5, max(frame.slices - 0.5, 0.5))
    axis.set_ylim(-0.02, 1.02)
    axis.set_xlabel("stack index", fontsize=7)
    axis.set_ylabel("reading (a share, 0 to 1)", fontsize=7)
    axis.tick_params(labelsize=6)
    axis.grid(True, linewidth=0.3, alpha=0.5)
    from matplotlib.lines import Line2D

    axis.legend(
        handles=[
            Line2D(
                [0],
                [0],
                color=LENS_COLOURS[standing.lens],
                marker=LENS_MARKERS[standing.lens],
                markerfacecolor="none",
                label=standing_words(standing),
            )
            for standing in frame.standings
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.14),
        ncol=1,
        fontsize=6.5,
        frameon=False,
    )
    chosen = ", ".join(str(index) for index in frame.chosen_slices) or "none"
    axis.set_title(
        wrapped(
            f"{identity}\nthe four readings over {frame.slices} slices, each lens at its "
            f"peak (bar {frame.minimum_valid}): chosen slices {chosen}; a gap is a silent "
            "slice",
            TITLE_COLUMNS,
        ),
        fontsize=TITLE_POINTS,
    )
    return "drawn"


def draw_chosen(axis, chosen: pictures.ChosenPlane, frame: pictures.DepthPanels) -> str:
    """One chosen slice: the acquired plane where the run saved it, else the squint's medians, titled with its lenses.

    Returns the plane's source, or `nothing_saved` when neither a plane nor the medians exist.
    """
    from matplotlib import colormaps

    axis.set_axis_off()
    lenses = ", ".join(chosen.lenses) or "no lens"
    if chosen.plane is not None:
        axis.imshow(
            chosen.plane,
            cmap="gray",
            interpolation="nearest",
            extent=native_extent(chosen.plane.shape),
        )
        axis.set_xlim(0, float(chosen.plane.shape[1]))
        axis.set_ylim(float(chosen.plane.shape[0]), 0)
        axis.set_aspect("equal")
        axis.set_title(
            wrapped(
                f"stack index {chosen.index} · chosen by {lenses}\n"
                f"{SOURCE_WORDS[chosen.source]}",
                TITLE_COLUMNS,
            ),
            fontsize=TITLE_POINTS,
        )
        return chosen.source
    if chosen.median is not None and frame.bounds_rc is not None:
        columns_edges, rows_edges = tile_edges(frame.bounds_rc)
        colours = colormaps["gray"].with_extremes(bad=UNREAD_COLOUR)
        finite = np.isfinite(chosen.median)
        limits = (
            {
                "vmin": float(chosen.median[finite].min()),
                "vmax": float(chosen.median[finite].max()),
            }
            if finite.any()
            else {}
        )
        axis.pcolormesh(
            columns_edges, rows_edges, chosen.median, cmap=colours, **limits
        )
        axis.set_xlim(0, float(columns_edges[-1]))
        axis.set_ylim(float(rows_edges[-1]), 0)
        axis.set_aspect("equal")
        axis.set_title(
            wrapped(
                f"stack index {chosen.index} · chosen by {lenses}\n"
                f"{SOURCE_WORDS['plane_not_saved']}",
                TITLE_COLUMNS,
            ),
            fontsize=TITLE_POINTS,
        )
        return "plane_not_saved"
    axis.set_title(
        wrapped(f"stack index {chosen.index} · chosen by {lenses}", TITLE_COLUMNS),
        fontsize=TITLE_POINTS,
    )
    axis.text(
        0.03,
        0.95,
        fill(
            "nothing saved to show this slice: neither a plane nor the squint's medians",
            width=40,
        ),
        transform=axis.transAxes,
        va="top",
    )
    return "nothing_saved"


@dataclass(frozen=True, slots=True)
class Sheet:
    """One series' sheet, built and not yet saved.

    figure: the Matplotlib figure, one axis for the curves and one for each chosen slice (one
    for the words, when none is chosen). suptitle: the figure's title, as the Text it is.
    curves: the curves panel's status word. panels: one record per chosen slice, as the manifest
    carries them. Nothing here is a measurement.
    """

    figure: Any
    suptitle: Any
    curves: str
    panels: list[dict]


def build_sheet(record: dict, frame: pictures.DepthPanels) -> Sheet:
    """Build one series' sheet from its saved collapse: the curves, then one panel per chosen slice.

    ARRANGING only. The figure is returned open; the caller saves it and closes it. The sheet's
    title is wrapped to the sheet's own width and each panel's title to the panel's, so no word
    of any title is cut by the edge of the picture or runs under its neighbour's. Matplotlib is
    imported here and not at the top, so the validators above stay importable where it is not
    installed.
    """
    import matplotlib.pyplot as plt

    across = 1 + max(len(frame.chosen), 1)
    figure, axes = plt.subplots(
        1,
        across,
        figsize=(PANEL_INCHES * across, ROW_INCHES + 1.2),
        layout="constrained",
        squeeze=False,
    )
    curves = draw_curves(axes[0, 0], record, frame)
    panels = []
    if not frame.chosen:
        axes[0, 1].set_axis_off()
        axes[0, 1].set_title("the chosen slices", fontsize=TITLE_POINTS)
        axes[0, 1].text(
            0.03,
            0.95,
            fill(
                "no lens stands anywhere, so no slice is chosen"
                + (
                    f": {frame.code}: {frame.why}"
                    if frame.code is not None and frame.code != "present"
                    else "; each lens's word is in the legend"
                ),
                width=44,
            ),
            transform=axes[0, 1].transAxes,
            va="top",
        )
    for column, chosen in enumerate(frame.chosen, start=1):
        panels.append(
            {
                "index": chosen.index,
                "lenses": list(chosen.lenses),
                "source": chosen.source,
                "drawn": draw_chosen(axes[0, column], chosen, frame),
            }
        )
    view, fluid, fat = record["view"]
    suptitle = figure.suptitle(
        wrapped(
            f"The funnel's depth collapse · {view} · fluid-sensitive={fluid}, "
            f"fat-suppressed={fat} · series {record['series_uid']}\n"
            "left: the four cheap readings per slice over the stack, each lens's chosen "
            "slice marked on its own curve (open marker, dotted line) and named in the "
            "legend; right: the chosen slices themselves, the acquired plane where this run "
            "saved it, else the squint's tile medians, each titled with the lenses that "
            "chose it",
            line_columns(PANEL_INCHES * across, SUPTITLE_POINTS),
        ),
        fontsize=SUPTITLE_POINTS,
    )
    return Sheet(figure, suptitle, curves, panels)


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
    loaded = [saved_depth(run, record) for record in records]
    if pictures.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:depth")
    # Every standing and every source the adapter can name has words here, and every lens a
    # colour and a marker, checked before anything is drawn.
    unworded = [
        *(name for name in pictures.SHEET_STANDINGS if name not in STANDING_WORDS),
        *(name for name in pictures.PLANE_SOURCES if name not in SOURCE_WORDS),
    ]
    if unworded:
        raise RuntimeError(f"depth_standing_unworded:{','.join(unworded)}")
    uncoloured = [
        lens for lens in LENSES if lens not in LENS_COLOURS or lens not in LENS_MARKERS
    ]
    if uncoloured:
        raise RuntimeError(f"depth_lens_uncoloured:{','.join(uncoloured)}")

    import matplotlib.pyplot as plt

    target.mkdir(parents=True, exist_ok=True)
    images: list[str] = []
    series = []
    for (index, record), (artifact, frame) in zip(
        enumerate(records, start=1), loaded, strict=True
    ):
        built = build_sheet(record, frame)
        name = image_name(index, record)
        built.figure.savefig(target / name, dpi=DPI)
        plt.close(built.figure)
        images.append(name)
        saved = record.get("depth")
        series.append(
            {
                "image": name,
                "image_sha256": sha256((target / name).read_bytes()).hexdigest(),
                "series_uid": record["series_uid"],
                "artifact": record["artifact"],
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "view": record["view"],
                "depth": None
                if saved is None
                else {
                    "code": frame.code,
                    "why": frame.why,
                    "minimum_valid": frame.minimum_valid,
                    "slices": frame.slices,
                    "lenses": [
                        {
                            "lens": standing.lens,
                            "index": standing.index,
                            "code": standing.code,
                        }
                        for standing in frame.standings
                    ],
                    "chosen_slices": list(frame.chosen_slices),
                    "arrays": {
                        short: record["arrays"][key]
                        for short, key in saved["arrays"].items()
                    },
                },
                "curves": built.curves,
                "chosen": built.panels,
                "frame_kind": "study",
            }
        )
    manifest = {
        "schema": "depth-frames-v1",
        "receipt_sha256": sha256(receipt_bytes).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": {
            "depth": sha256(Path(pictures.__file__).read_bytes()).hexdigest()
        },
        "study_uid": study_uid,
        "image": images[0],
        "images": images,
        "frame_kind": "study",
        "standings": list(pictures.SHEET_STANDINGS),
        "sources": list(pictures.PLANE_SOURCES),
        "legend": {
            "lenses": {lens: LENS_COLOURS[lens] for lens in LENSES},
            "markers": {lens: LENS_MARKERS[lens] for lens in LENSES},
            "not_read_tile": UNREAD_COLOUR,
        },
        "series": series,
        "note": (
            "Every value is a saved one. A silent slice is a gap in its curve, never a zero; "
            "a lens standing nowhere says its word in the legend and marks no slice; a chosen "
            "slice no plane was saved at shows the squint's own medians and says so. One sheet "
            "per series, for the founder's eye (E2)."
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
