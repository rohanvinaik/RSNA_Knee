"""Draw the funnel's squint over the stack: per series, the tile medians at the walked slices over the acquired planes.

The-funnel task 1.2 (`openspec/changes/the-funnel/tasks.md`). The funnel's operation 1
(`knee.collapse.squint_stack`) squints every slice of a series in millimetres; the writer saves
the whole stack beside the series' record. This workbench arranges those saved values through
`knee.pictures.squint_stack`: one row per series, the stack's standing in words, then one panel
per step of the study stage's own walk through the stack (`Series.walk`, the slices
`knee.study.series.walk_indices` visits, saved by the writer): the acquired plane at that slice in
grey, and over it the stack's tile medians at the same slice, each tile placed in native pixels
by the bounds the stage saved. It takes no measurement of its own: every number on the page is a
saved value, and every gap is a named silence, never a zero.

Four silences are kept apart, because each has its own remedy (`knee.pictures.squint_stack.
WALK_STANDINGS`): this run's writer saved no stack; the stage made none and says why; the walked
slice lies outside the stack; the saved code is a word the stage does not say. A series whose
writer saved no walk draws its tiles alone on the tile grid and the title says so.

Nothing here squints, thresholds, resamples or recomputes a centre. The grey scale is
Matplotlib's linear display scale over each plane's own stored values; the medians are drawn in
the series' own stored units, with a tile that holds no finite pixel in a colour no value takes.
"""

import argparse
import json
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from textwrap import fill

import numpy as np

from knee.collapse.squint_stack import STACK_CODES
from knee.pictures import squint_stack as pictures
from workbench.render._out import PROJECT, ArgumentRefusal
from workbench.render.field_frames import (
    UNREAD_COLOUR,
    native_extent,
    saved_array,
    tile_edges,
)

#: The stack's arrays by the short names the writer gives them in
#: `record["squint_stack"]["arrays"]`, each with the dtype it must have and its number of axes.
STACK_ARRAYS: Mapping[str, tuple[np.dtype, int]] = {
    "median": (np.dtype(np.float64), 3),
    "minimum": (np.dtype(np.float64), 3),
    "maximum": (np.dtype(np.float64), 3),
    "coverage": (np.dtype(np.float64), 3),
    "centres_lps": (np.dtype(np.float64), 4),
    "bounds_rc": (np.dtype(np.int64), 3),
}

#: What each silence a walked slice can hold says, in words. The codes are the adapter's
#: (`knee.pictures.squint_stack.WALK_STANDINGS`); the words are this drawing's.
STANDING_WORDS: Mapping[str, str] = {
    "squinted": "the stack's tile medians at this slice, over the plane",
    "stack_not_saved": "not saved: this run's writer saved no squint stack for this series",
    "stack_absent": "not made: the stage squinted no slice; its own code and reason are beside",
    "slice_outside_stack": "not drawn: the walked slice lies outside the slices the stack holds",
    "stack_code_unknown": "not drawn: the saved code is one the stage does not say",
}

#: How much of the plane shows through the medians laid over it.
MEDIAN_ALPHA = 0.62

#: One row per series: the text panel, then one panel per walked slice.
PANEL_INCHES = 4.2
ROW_INCHES = 5.0
DPI = 120


def saved_number(value: object, where: str) -> float:
    """A saved bar as a float. A value that is not a finite number is a record that disagrees."""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not np.isfinite(value)
    ):
        raise ValueError(f"saved_squint_stack_not_a_number:{where}")
    return float(value)


def saved_stack(run: Path, record: dict) -> tuple[Path, pictures.SquintStackPanels]:
    """Reconstitute one series' saved squint stack and the study stage's saved walk, without measuring.

    Total over a series whose writer saved no stack, or no walk: each is handed on as the silence
    it is. A stack record that is not a mapping, a code the stage does not say, a bar or a grid
    that is not what the writer saves, an array whose dtype, shape or digest disagrees with its
    descriptor, maps that do not share one shape, centres or bounds that do not fit the maps, a
    slice count that is not the maps', a walk whose saved indices are not a list, or a walk
    whose saved indices do not match its slices, means the record and this renderer disagree,
    and is raised rather than drawn. Each saved walk index is handed to the adapter AS SAVED,
    never coerced: an index that is not a whole number inside the stack is the adapter's own
    silence, `slice_outside_stack`, in words on the page, and never a rounded slice.
    """
    artifact = run / record["artifact"]
    descriptors = record["arrays"]
    saved_study = record.get("study") or {}
    walk_name = saved_study.get("walk_array")
    saved_walk = saved_study.get("walk_indices", [])
    if type(saved_walk) is not list:
        raise ValueError("saved_walk_indices_not_a_list")
    walk_indices = tuple(saved_walk)
    saved = record.get("squint_stack")
    code = why = tile_mm = tile_shape = None
    drawn: dict[str, np.ndarray] = {}
    if saved is not None:
        if type(saved) is not dict:
            raise ValueError("saved_squint_stack_not_a_record")
        for key in ("code", "why"):
            if type(saved.get(key)) is not str:
                raise ValueError(f"saved_squint_stack_field_invalid:{key}")
        if saved["code"] not in STACK_CODES:
            raise ValueError(f"saved_squint_stack_code_unknown:{saved['code']}")
        code, why = saved["code"], saved["why"]
        tile_mm = saved_number(saved.get("tile_mm"), "tile_mm")
        shape = saved.get("tile_shape_rc")
        if not (
            isinstance(shape, list)
            and len(shape) == 2
            and all(type(size) is int and size >= 0 for size in shape)
        ):
            raise ValueError("saved_squint_stack_tile_shape_invalid")
        tile_shape = (int(shape[0]), int(shape[1]))
        names = saved.get("arrays")
        if type(names) is not dict:
            raise ValueError("saved_squint_stack_arrays_missing")
        for short in STACK_ARRAYS:
            if type(names.get(short)) is not str:
                raise ValueError(f"saved_squint_stack_array_unnamed:{short}")
    with np.load(artifact, allow_pickle=False) as arrays:
        walk = (
            saved_array(arrays, descriptors, walk_name, 3)
            if walk_name is not None
            else None
        )
        if saved is not None:
            for short, (dtype, ndim) in STACK_ARRAYS.items():
                array = saved_array(arrays, descriptors, saved["arrays"][short], ndim)
                if array.dtype != dtype:
                    raise ValueError(
                        f"saved_squint_stack_representation_invalid:{short}"
                    )
                drawn[short] = array
    if walk is not None and walk.shape[0] != len(walk_indices):
        raise ValueError("saved_walk_indices_mismatch")
    if saved is not None:
        maps = drawn["median"].shape
        for short in ("minimum", "maximum", "coverage"):
            if drawn[short].shape != maps:
                raise ValueError(f"saved_squint_stack_shape_mismatch:{short}")
        if drawn["centres_lps"].shape != (*maps, 3):
            raise ValueError("saved_squint_stack_shape_mismatch:centres_lps")
        if drawn["bounds_rc"].shape != (*maps[1:], 4):
            raise ValueError("saved_squint_stack_shape_mismatch:bounds_rc")
        if saved.get("slices") != maps[0]:
            raise ValueError("saved_squint_stack_slices_mismatch")
    return artifact, pictures.stack_panels(
        code,
        why,
        tile_mm,
        tile_shape,
        drawn.get("median"),
        drawn.get("coverage"),
        drawn.get("bounds_rc"),
        walk_indices,
        walk,
    )


def stack_lines(record: dict, frame: pictures.SquintStackPanels) -> list[str]:
    """The text panel: the series, its view, and the stack's standing with its bar and grid."""
    view, fluid, fat = record["view"]
    lines = [
        fill(record["series_uid"], width=40),
        f"{view} · fluid-sensitive={fluid}, fat-suppressed={fat}",
        "",
    ]
    if frame.code is None:
        lines.append("squint stack (collapse): not saved")
        lines.append(
            fill("this run's writer saved no squint stack for this series", width=40)
        )
        return lines
    lines += [
        f"squint stack (collapse): {frame.code}",
        fill(f"why: {frame.why}", width=40),
        "",
        f"tile          {frame.tile_mm:g} mm",
    ]
    if frame.tile_shape_rc is not None:
        lines.append(
            f"tile pixels   {frame.tile_shape_rc[0]} x {frame.tile_shape_rc[1]}"
        )
    if frame.median is not None:
        lines.append(
            f"grid          {frame.median.shape[1]} x {frame.median.shape[2]} tiles"
        )
    lines.append(f"slices        {frame.slices}")
    lines.append("walked        " + ", ".join(str(step.index) for step in frame.walked))
    return lines


def draw_walked(axis, step: pictures.WalkedSquint, frame: pictures.SquintStackPanels):
    """One walked slice: the plane in grey with the medians over it, or the silence in words.

    Returns the step's standing, or `tiles_alone` when the stack is drawn with no plane beneath.
    """
    from matplotlib import colormaps

    axis.set_axis_off()
    if step.standing != "squinted" or step.median is None or frame.bounds_rc is None:
        axis.set_title(f"stack index {step.index}", fontsize=8)
        words = STANDING_WORDS[step.standing]
        if step.standing == "stack_absent" and frame.why is not None:
            words = f"{words}: {frame.code}"
        axis.text(0.03, 0.95, fill(words, width=38), transform=axis.transAxes, va="top")
        return step.standing
    columns_edges, rows_edges = tile_edges(frame.bounds_rc)
    colours = colormaps["gray"].with_extremes(bad=UNREAD_COLOUR)
    finite = np.isfinite(step.median)
    limits = (
        {
            "vmin": float(step.median[finite].min()),
            "vmax": float(step.median[finite].max()),
        }
        if finite.any()
        else {}
    )
    if step.plane is not None:
        axis.imshow(
            step.plane,
            cmap="gray",
            interpolation="nearest",
            extent=native_extent(step.plane.shape),
        )
        standing, where = "squinted", "over the acquired plane"
    else:
        standing, where = "tiles_alone", "tiles alone: no walk saved for this series"
    mesh = axis.pcolormesh(
        columns_edges,
        rows_edges,
        step.median,
        cmap=colours,
        alpha=MEDIAN_ALPHA if step.plane is not None else 1.0,
        **limits,
    )
    axis.set_xlim(0, float(columns_edges[-1]))
    axis.set_ylim(float(rows_edges[-1]), 0)
    axis.set_aspect("equal")
    axis.figure.colorbar(mesh, ax=axis, shrink=0.7)
    axis.set_title(
        f"stack index {step.index}\nsquint median (stored units), {where}", fontsize=8
    )
    return standing


def draw(run: Path, study_uid: str, out: Path) -> dict:
    """Draw this stage from the saved run and return its manifest.

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
    loaded = [saved_stack(run, record) for record in records]
    if pictures.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:squint_stack")
    # Every standing the adapter can name has words here, checked before anything is drawn.
    unworded = [name for name in pictures.WALK_STANDINGS if name not in STANDING_WORDS]
    if unworded:
        raise RuntimeError(f"walk_standing_unworded:{','.join(unworded)}")

    import matplotlib.pyplot as plt

    target.mkdir(parents=True, exist_ok=True)
    walked = max((len(frame.walked) for _, frame in loaded), default=0)
    across = 1 + max(walked, 1)
    gallery, axes = plt.subplots(
        len(records),
        across,
        figsize=(PANEL_INCHES * across, ROW_INCHES * len(records)),
        layout="constrained",
        squeeze=False,
    )
    for axis in axes.flat:
        axis.set_axis_off()
    series = []
    for row, (record, (artifact, frame)) in enumerate(
        zip(records, loaded, strict=True)
    ):
        text = axes[row, 0]
        text.set_title("the squint over the stack", fontsize=8)
        text.text(
            0.0,
            1.0,
            "\n".join(stack_lines(record, frame)),
            transform=text.transAxes,
            va="top",
            family="monospace",
            fontsize=6.5,
        )
        standings = []
        if not frame.walked:
            axes[row, 1].text(
                0.03,
                0.5,
                "no walk saved for this series: no slice to draw the stack at",
                transform=axes[row, 1].transAxes,
                va="center",
            )
        for column, step in enumerate(frame.walked, start=1):
            standings.append(
                {
                    "index": step.index,
                    "standing": step.standing,
                    "drawn": draw_walked(axes[row, column], step, frame),
                }
            )
        saved = record.get("squint_stack")
        series.append(
            {
                "series_uid": record["series_uid"],
                "artifact": record["artifact"],
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "view": record["view"],
                "squint_stack": None
                if saved is None
                else {
                    "code": frame.code,
                    "why": frame.why,
                    "tile_mm": frame.tile_mm,
                    "tile_shape_rc": list(frame.tile_shape_rc or ()),
                    "slices": frame.slices,
                    "tiles_rc": []
                    if frame.median is None
                    else [int(size) for size in frame.median.shape[1:]],
                    "arrays": {
                        short: record["arrays"][key]
                        for short, key in saved["arrays"].items()
                    },
                },
                "walked": standings,
                "frame_kind": "study",
            }
        )
    gallery.suptitle(
        "The funnel's squint over the stack, one row per series: the stack's standing, then "
        "its tile medians at the study stage's walked slices, each over the acquired plane "
        "at that slice and placed by the stack's own native bounds\n"
        "fuchsia tiles are not read: no finite pixel in the tile",
        fontsize=11,
    )
    gallery.savefig(target / "series.png", dpi=DPI)
    plt.close(gallery)
    manifest = {
        "schema": "squint-stack-frames-v1",
        "receipt_sha256": sha256(receipt_bytes).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": {
            "squint_stack": sha256(Path(pictures.__file__).read_bytes()).hexdigest()
        },
        "study_uid": study_uid,
        "image": "series.png",
        "frame_kind": "study",
        "standings": list(pictures.WALK_STANDINGS),
        "legend": {"not_read_tile": UNREAD_COLOUR},
        "series": series,
        "note": (
            "Every value is a saved one. A walked slice the stack does not hold, a stack the "
            "stage did not make and a stack this run's writer did not save are three silences, "
            "each named; none is a zero."
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
        draw(args.run, args.study_uid, args.out)
    except ArgumentRefusal as refusal:
        parser.error(str(refusal))
    target = args.out.resolve()
    print(
        json.dumps(
            {
                "series": str(target / "series.png"),
                "manifest": str(target / "manifest.json"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
