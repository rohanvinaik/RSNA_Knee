"""Draw the funnel's first lens: one sheet per view, the tiles by code over the acquired plane at the walked slices.

The-funnel task 2.3 (`openspec/changes/the-funnel/tasks.md`). The funnel's operation 2
(`knee.collapse.first_lens`) names every tile of every slice of a series background,
not_background, undecided or empty under the series' own split, once; the writer saves the
record whole, and
that is the freeze. This workbench arranges those saved values through
`knee.pictures.first_lens`: ONE SHEET PER VIEW (one image per series), so the founder can check
each view by eye (task 2.4, E1): the lens's standing in words, then one panel per step of the
study stage's own walk through the stack (`Series.walk`, the slices
`knee.study.series.walk_indices` visits, saved by the writer): the acquired plane at that slice
in grey, and over it every tile by its code, placed in native pixels by the squint stack's
saved bounds -- background in red at a low alpha (what the lens cleared, so what lies beneath
can be checked), undecided in amber (in play), not_background untouched (the plane shows
through: the lens found no air there and says nothing more), a tile with no finite pixel in
grey. It takes no measurement of its own: every number on the page is a
saved value, and every gap is a named silence, never a zero.

Four silences are kept apart, because each has its own remedy
(`knee.pictures.first_lens.LENS_STANDINGS`): this run's writer saved no first lens; the saved
code is a word the stage does not say; the stage named no tile and says why (its stack was
absent); the walked slice lies outside the slices the lens holds. A series whose writer saved
no walk draws its tiles alone on the tile grid and the title says so. A lens saved without its
squint stack, or over another grid than the stack's, disagrees with the writer and is refused
rather than drawn.

Nothing here thresholds, labels, dilates or recomputes a code. The grey scale is Matplotlib's
linear display scale over each plane's own stored values.
"""

import argparse
import json
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from textwrap import fill

import numpy as np

from knee.collapse.first_lens import LENS_CODES, TILE_CODES
from knee.pictures import first_lens as pictures
from workbench.render import squint_stack_frames
from workbench.render._out import PROJECT, ArgumentRefusal
from workbench.render.field_frames import (
    native_extent,
    overlay,
    saved_array,
    tile_edges,
)

#: The lens's arrays by the short names the writer gives them in
#: `record["first_lens"]["arrays"]`, each with the dtype it must have and its number of axes.
LENS_ARRAYS: Mapping[str, tuple[np.dtype, int]] = {"codes": (np.dtype(np.uint8), 3)}

#: What each silence a walked slice can hold says, in words. The codes are the adapter's
#: (`knee.pictures.first_lens.LENS_STANDINGS`); the words are this drawing's.
STANDING_WORDS: Mapping[str, str] = {
    "named": "every tile at this slice by its code, over the plane",
    "lens_not_saved": "not saved: this run's writer saved no first lens for this series",
    "lens_code_unknown": "not drawn: the saved code is one the stage does not say",
    "lens_absent": "not made: the stage named no tile; its own code and reason are beside",
    "slice_outside_lens": (
        "not drawn: the walked slice lies outside the slices the lens holds"
    ),
}

#: What each tile code is drawn in, and how much of the plane shows through it.
#: `not_background` is None: it is left untouched, so the plane is seen exactly as the lens
#: leaves it in play. Background is a low alpha, so what the lens cleared can be checked against
#: what lies beneath it. Grey is given only to a tile with no finite pixel, which is a silence
#: and never a reading.
CODE_COLOURS: Mapping[str, str | None] = {
    "background": "#ff1414",
    "not_background": None,
    "undecided": "#f59e0b",
    "tile_empty": "#9ca3af",
}
CODE_ALPHAS: Mapping[str, float] = {
    "background": 0.28,
    "not_background": 0.0,
    "undecided": 0.45,
    "tile_empty": 0.6,
}

#: One sheet per series: the text panel, then one panel per walked slice.
PANEL_INCHES = 4.2
ROW_INCHES = 5.2
DPI = 120


def saved_number(value: object, where: str) -> float | None:
    """A saved split as a float; None where the writer saved None (a valley the regime did not read).

    A value that is neither None nor a finite number is a record that disagrees, and is raised.
    """
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not np.isfinite(value)
    ):
        raise ValueError(f"saved_first_lens_not_a_number:{where}")
    return float(value)


def saved_lens(run: Path, record: dict) -> tuple[Path, pictures.FirstLensPanels]:
    """Reconstitute one series' saved first lens and the study stage's saved walk, without measuring.

    Total over a series whose writer saved no lens, or no walk: each is handed on as the silence
    it is. A lens record that is not a mapping, a code the stage does not say, vocabularies that
    are not the stage's, a split that is not a number, counts that are not whole numbers keyed by
    the stage's tile codes, an array whose dtype, shape or digest disagrees with its descriptor,
    a slice count or a grid that is not the codes', a code value outside the vocabulary, a walk
    whose saved indices do not match its slices, a lens saved without the series' squint stack,
    or a stack whose grid or slices are not the lens's, means the record and this renderer
    disagree, and is raised rather than drawn. The stack is read through the stack drawer's own
    reader, which validates it against the writer's descriptors; its bounds place the tiles.
    """
    artifact = run / record["artifact"]
    descriptors = record["arrays"]
    saved_study = record.get("study") or {}
    walk_name = saved_study.get("walk_array")
    walk_indices = tuple(int(index) for index in saved_study.get("walk_indices", ()))
    saved = record.get("first_lens")
    code = why = rule = split = counts = tiles = None
    drawn: dict[str, np.ndarray] = {}
    bounds = None
    if saved is not None:
        if type(saved) is not dict:
            raise ValueError("saved_first_lens_not_a_record")
        for key in ("code", "why", "rule_version"):
            if type(saved.get(key)) is not str:
                raise ValueError(f"saved_first_lens_field_invalid:{key}")
        if saved["code"] not in LENS_CODES:
            raise ValueError(f"saved_first_lens_code_unknown:{saved['code']}")
        if saved.get("code_names") != list(LENS_CODES) or saved.get(
            "tile_code_names"
        ) != list(TILE_CODES):
            raise ValueError("saved_first_lens_vocabulary_mismatch")
        code, why, rule = saved["code"], saved["why"], saved["rule_version"]
        split = saved_number(saved.get("split"), "split")
        saved_counts = saved.get("counts")
        if not (
            isinstance(saved_counts, dict)
            and list(saved_counts) == list(TILE_CODES)
            and all(
                type(count) is int and count >= 0 for count in saved_counts.values()
            )
        ):
            raise ValueError("saved_first_lens_counts_invalid")
        counts = tuple(saved_counts[name] for name in TILE_CODES)
        names = saved.get("arrays")
        if type(names) is not dict:
            raise ValueError("saved_first_lens_arrays_missing")
        for short in LENS_ARRAYS:
            if type(names.get(short)) is not str:
                raise ValueError(f"saved_first_lens_array_unnamed:{short}")
        tiles = saved.get("tiles_rc")
        if not (
            isinstance(tiles, list)
            and len(tiles) == 2
            and all(type(size) is int and size >= 0 for size in tiles)
        ):
            raise ValueError("saved_first_lens_tiles_invalid")
    with np.load(artifact, allow_pickle=False) as arrays:
        walk = (
            saved_array(arrays, descriptors, walk_name, 3)
            if walk_name is not None
            else None
        )
        if saved is not None:
            for short, (dtype, ndim) in LENS_ARRAYS.items():
                array = saved_array(arrays, descriptors, saved["arrays"][short], ndim)
                if array.dtype != dtype:
                    raise ValueError(f"saved_first_lens_representation_invalid:{short}")
                drawn[short] = array
    if walk is not None and walk.shape[0] != len(walk_indices):
        raise ValueError("saved_walk_indices_mismatch")
    if saved is not None and tiles is not None:
        codes = drawn["codes"]
        if saved.get("slices") != codes.shape[0]:
            raise ValueError("saved_first_lens_slices_mismatch")
        if tuple(codes.shape[1:]) != (int(tiles[0]), int(tiles[1])):
            raise ValueError("saved_first_lens_shape_mismatch:codes")
        if codes.size and int(codes.max()) >= len(TILE_CODES):
            raise ValueError("saved_first_lens_tile_code_unknown")
        # The lens is made over the series' own squint stack, so a record that saved the one
        # and not the other disagrees with the writer; the stack's grid and slices must be the
        # lens's, because the stack's bounds are what place the lens's tiles on the plane.
        if "squint_stack" not in record:
            raise ValueError("saved_first_lens_without_a_stack")
        _, stack = squint_stack_frames.saved_stack(run, record)
        bounds = stack.bounds_rc
        if (
            bounds is None
            or tuple(bounds.shape[:2]) != tuple(codes.shape[1:])
            or stack.slices != int(codes.shape[0])
        ):
            raise ValueError("saved_first_lens_grid_mismatch")
    return artifact, pictures.lens_panels(
        code,
        why,
        split,
        rule,
        counts,
        drawn.get("codes"),
        bounds,
        walk_indices,
        walk,
    )


def tile_counts(codes: np.ndarray | None) -> dict[str, int]:
    """How many tiles at one slice carry each code, from the saved codes; empty when none."""
    if codes is None:
        return {}
    values = np.asarray(codes)
    return {
        name: int(np.count_nonzero(values == value))
        for value, name in enumerate(TILE_CODES)
    }


def number(value: float | None) -> str:
    """A saved split as text; None is how a valley the regime could not read comes back."""
    return "not read" if value is None else f"{value:g}"


def image_name(index: int, record: dict) -> str:
    """One sheet per view, named as the view sheets are: its order, plane and the two flags."""
    view, fluid, fat = record["view"]
    return f"{index:02d}-{view.lower()}-fs{fluid}-fat{fat}.png"


def lens_lines(record: dict, frame: pictures.FirstLensPanels) -> list[str]:
    """The text panel: the series, its view, and the lens's standing with its split, rule and counts."""
    view, fluid, fat = record["view"]
    lines = [
        fill(record["series_uid"], width=40),
        f"{view} · fluid-sensitive={fluid}, fat-suppressed={fat}",
        "",
    ]
    if frame.code is None:
        lines.append("first lens (collapse): not saved")
        lines.append(fill(STANDING_WORDS["lens_not_saved"], width=40))
        return lines
    lines += [
        f"first lens (collapse): {frame.code}",
        fill(f"why: {frame.why}", width=40),
        "",
        f"split         {number(frame.split)}",
        f"rule          {frame.rule_version}",
        f"slices        {frame.slices}",
    ]
    if frame.codes is not None and frame.codes.ndim == 3:
        lines.append(
            f"grid          {frame.codes.shape[1]} x {frame.codes.shape[2]} tiles"
        )
    if frame.counts is not None:
        lines += ["", "tiles over the stack"]
        lines += [
            f"  {name:<12}{count}"
            for name, count in zip(TILE_CODES, frame.counts, strict=True)
        ]
    lines.append("")
    lines.append("walked        " + ", ".join(str(step.index) for step in frame.walked))
    return lines


def draw_walked(axis, step: pictures.WalkedLens, frame: pictures.FirstLensPanels):
    """One walked slice: the plane in grey with every tile by its code over it, or the silence in words.

    Returns the step's standing, or `tiles_alone` when the lens is drawn with no plane beneath.
    """
    from matplotlib.patches import Patch

    axis.set_axis_off()
    if step.standing != "named" or step.codes is None or frame.bounds_rc is None:
        axis.set_title(f"stack index {step.index}", fontsize=8)
        words = STANDING_WORDS[step.standing]
        if step.standing == "lens_absent" and frame.code is not None:
            words = f"{words}: {frame.code}"
        axis.text(0.03, 0.95, fill(words, width=38), transform=axis.transAxes, va="top")
        return step.standing
    edges = tile_edges(frame.bounds_rc)
    columns_edges, rows_edges = edges
    if step.plane is not None:
        axis.imshow(
            step.plane,
            cmap="gray",
            interpolation="nearest",
            extent=native_extent(step.plane.shape),
        )
        standing, where = "named", "over the acquired plane"
    else:
        standing, where = "tiles_alone", "tiles alone: no walk saved for this series"
    present = []
    for value, name in enumerate(TILE_CODES):
        colour = CODE_COLOURS[name]
        mask = step.codes == value
        if colour is None or not mask.any():
            continue
        overlay(axis, edges, mask, colour, alpha=CODE_ALPHAS[name])
        present.append((f"{name} ({int(mask.sum())})", colour))
    counts = tile_counts(step.codes)
    axis.set_xlim(0, float(columns_edges[-1]))
    axis.set_ylim(float(rows_edges[-1]), 0)
    axis.set_aspect("equal")
    if present:
        axis.legend(
            handles=[Patch(facecolor=colour, label=label) for label, colour in present],
            loc="upper center",
            bbox_to_anchor=(0.5, 0.0),
            ncol=2,
            fontsize=5.5,
            frameon=False,
        )
    axis.set_title(
        f"stack index {step.index}\ntiles by code, {where}; "
        f"not background untouched ({counts['not_background']})",
        fontsize=8,
    )
    return standing


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
    loaded = [saved_lens(run, record) for record in records]
    if pictures.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:first_lens")
    # Every standing the adapter can name has words here, and every tile code a colour entry
    # (None for the one left untouched), checked before anything is drawn.
    unworded = [name for name in pictures.LENS_STANDINGS if name not in STANDING_WORDS]
    if unworded:
        raise RuntimeError(f"lens_standing_unworded:{','.join(unworded)}")
    uncoloured = [
        name
        for name in TILE_CODES
        if name not in CODE_COLOURS or name not in CODE_ALPHAS
    ]
    if uncoloured:
        raise RuntimeError(f"first_lens_vocabulary_uncoloured:{','.join(uncoloured)}")

    import matplotlib.pyplot as plt

    target.mkdir(parents=True, exist_ok=True)
    series = []
    for index, (record, (artifact, frame)) in enumerate(
        zip(records, loaded, strict=True), start=1
    ):
        across = 1 + max(len(frame.walked), 1)
        sheet, axes = plt.subplots(
            1,
            across,
            figsize=(PANEL_INCHES * across, ROW_INCHES),
            layout="constrained",
            squeeze=False,
        )
        for axis in axes.flat:
            axis.set_axis_off()
        text = axes[0, 0]
        text.set_title("the first lens", fontsize=8)
        text.text(
            0.0,
            1.0,
            "\n".join(lens_lines(record, frame)),
            transform=text.transAxes,
            va="top",
            family="monospace",
            fontsize=6.5,
        )
        standings = []
        if not frame.walked:
            axes[0, 1].text(
                0.03,
                0.5,
                "no walk saved for this series: no slice to draw the lens at",
                transform=axes[0, 1].transAxes,
                va="center",
            )
        for column, step in enumerate(frame.walked, start=1):
            standings.append(
                {
                    "index": step.index,
                    "standing": step.standing,
                    "drawn": draw_walked(axes[0, column], step, frame),
                    "counts": tile_counts(step.codes),
                }
            )
        view, fluid, fat = record["view"]
        sheet.suptitle(
            f"The funnel's first lens · {view} · fluid-sensitive={fluid}, "
            f"fat-suppressed={fat} · series {record['series_uid']}\n"
            "the lens's standing, then every tile by its code at the study stage's walked "
            "slices, each over the acquired plane at that slice and placed by the squint "
            "stack's own native bounds\n"
            "red: background, cleared by the lens (low alpha, so what lies beneath can be "
            "checked) · amber: undecided, in play · untouched: not background, the lens found "
            "no air there · grey: no finite pixel in the tile",
            fontsize=9,
        )
        name = image_name(index, record)
        sheet.savefig(target / name, dpi=DPI)
        plt.close(sheet)
        saved = record.get("first_lens")
        series.append(
            {
                "image": name,
                "image_sha256": sha256((target / name).read_bytes()).hexdigest(),
                "series_uid": record["series_uid"],
                "artifact": record["artifact"],
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "view": record["view"],
                "first_lens": None
                if saved is None
                else {
                    "code": frame.code,
                    "why": frame.why,
                    "split": frame.split,
                    "rule_version": frame.rule_version,
                    "counts": None
                    if frame.counts is None
                    else dict(zip(TILE_CODES, frame.counts, strict=True)),
                    "slices": frame.slices,
                    "tiles_rc": []
                    if frame.codes is None
                    else [int(size) for size in frame.codes.shape[1:]],
                    "arrays": {
                        short: record["arrays"][key]
                        for short, key in saved["arrays"].items()
                    },
                },
                "walked": standings,
                "frame_kind": "study",
            }
        )
    manifest = {
        "schema": "first-lens-frames-v1",
        "receipt_sha256": sha256(receipt_bytes).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": {
            "first_lens": sha256(Path(pictures.__file__).read_bytes()).hexdigest()
        },
        "study_uid": study_uid,
        "image": series[0]["image"],
        "images": [entry["image"] for entry in series],
        "frame_kind": "study",
        "standings": list(pictures.LENS_STANDINGS),
        "legend": {
            "tile_codes": dict(CODE_COLOURS),
            "alphas": dict(CODE_ALPHAS),
            "not_background": "untouched: the plane shows through",
        },
        "series": series,
        "note": (
            "Every value is a saved one. A walked slice the lens does not hold, a lens the "
            "stage did not make and a lens this run's writer did not save are three silences, "
            "each named; none is a zero. One sheet per view, for the founder's eye-check."
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
