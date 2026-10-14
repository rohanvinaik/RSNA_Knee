"""Draw the funnel's tile digits: one sheet per view, every tile by its digit over the acquired plane at the walked slices.

The-funnel task 3b.3 (`openspec/changes/the-funnel/tasks.md`). The funnel's operation 3b
(`knee.lenses.tiles`) names every tile of every slice of a series below, at or above the
terciles of the tiles the first lens did not clear, and every other tile silent; the writer
saves the record whole beside the lens and the stack. This workbench arranges those saved
values through `knee.pictures.tiles`: ONE SHEET PER VIEW (one image per series), so the
founder can check each view by eye (task 3b.2: on the fat-bright coronal, whether the `above`
tiles lie inside the two big bright regions): the digits' standing in words, then one panel
per step of the study stage's own walk through the stack (`Series.walk`, the slices
`knee.study.series.walk_indices` visits, saved by the writer): the acquired plane at that slice
in grey, and over it every tile by its digit, placed in native pixels by the squint stack's
saved bounds -- below, at and above in the lens gallery's three colours, and every silence,
whichever word the oracle gave it, in ONE neutral tone named silence in the legend. It takes no
measurement of its own: every number on the page is a saved value, and every gap is a named
silence, never a zero.

Four silences are kept apart, because each has its own remedy
(`knee.pictures.tiles.DIGIT_STANDINGS`): this run's writer saved no tile digits; the saved code
is a word the stage does not say; the stage named no tile and says why (its stack or its lens
was absent); the walked slice lies outside the slices the digits hold. A series whose oracle
gave no pair of edges draws every tile as silence, and the title says which word the oracle
gave. A series whose writer saved no walk draws its tiles alone on the tile grid and the title
says so. Digits saved without their squint stack, or over another grid than the stack's,
disagree with the writer and are refused rather than drawn.

Nothing here thresholds, re-reads an edge or recomputes a digit. The grey scale is Matplotlib's
linear display scale over each plane's own stored values.
"""

import argparse
import json
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from textwrap import fill

import numpy as np

from knee.lenses.digits import DIGIT_CODES, READ_CODES
from knee.lenses.places import CODE_VALUES, DIGIT_VALUES, SILENT
from knee.lenses.tiles import TILE_DIGIT_CODES
from knee.pictures import tiles as pictures
from workbench.render import squint_stack_frames
from workbench.render._out import PROJECT, ArgumentRefusal
from workbench.render.field_frames import (
    native_extent,
    overlay,
    saved_array,
    tile_edges,
)

#: The digits' arrays by the short names the writer gives them in
#: `record["tile_digits"]["arrays"]`, each with the dtype it must have and its number of axes.
DIGIT_ARRAYS: Mapping[str, tuple[np.dtype, int]] = {
    "codes": (np.dtype(np.uint8), 3),
    "digits": (np.dtype(np.int8), 3),
}

#: What each silence a walked slice can hold says, in words. The codes are the adapter's
#: (`knee.pictures.tiles.DIGIT_STANDINGS`); the words are this drawing's.
STANDING_WORDS: Mapping[str, str] = {
    "named": "every tile at this slice by its digit, over the plane; silence as silence",
    "digits_not_saved": "not saved: this run's writer saved no tile digits for this series",
    "digits_code_unknown": "not drawn: the saved code is one the stage does not say",
    "digits_absent": (
        "not made: the stage named no tile; its own code and reason are beside"
    ),
    "slice_outside_digits": (
        "not drawn: the walked slice lies outside the slices the digits hold"
    ),
}

#: The three digits in the lens gallery's own colours (`workbench.render.lens_frames.COLORS`,
#: restated here so this drawer imports no Matplotlib at module level), and ONE neutral tone
#: for every silence, whichever word the oracle gave it: a silence is drawn as silence, never
#: as a digit and never as nothing. No grey is a digit's colour.
DIGIT_COLOURS: Mapping[str, str] = {
    "below": "#2563eb",
    "at": "#22c55e",
    "above": "#f59e0b",
}
SILENCE_COLOUR = "#9ca3af"
DIGIT_ALPHA = 0.45
SILENCE_ALPHA = 0.35

#: The stored value of each digit that is a reading, by its word, and the stored values that
#: are a silence: the stage's own vocabulary, read once here so the drawer names nothing.
READ_VALUES: Mapping[str, int] = {name: CODE_VALUES[name] for name in READ_CODES}
SILENCE_VALUES: tuple[int, ...] = tuple(
    CODE_VALUES[name] for name in DIGIT_CODES if name not in READ_CODES
)

#: One sheet per series: the text panel, then one panel per walked slice.
PANEL_INCHES = 4.2
ROW_INCHES = 5.2
DPI = 120


def saved_number(value: object, where: str) -> float | None:
    """A saved edge as a float; None where the writer saved None (a pair the oracle did not read).

    A value that is neither None nor a finite number is a record that disagrees, and is raised.
    """
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not np.isfinite(value)
    ):
        raise ValueError(f"saved_tile_digits_not_a_number:{where}")
    return float(value)


def saved_count(value: object, where: str) -> int:
    """A saved count or bar as an int: a whole number that is not a bool and not negative."""
    if type(value) is not int or value < 0:
        raise ValueError(f"saved_tile_digits_not_a_count:{where}")
    return value


def saved_digits(run: Path, record: dict) -> tuple[Path, pictures.TileDigitPanels]:
    """Reconstitute one series' saved tile digits and the study stage's saved walk, without measuring.

    Total over a series whose writer saved no digits, or no walk: each is handed on as the
    silence it is. A digits record that is not a mapping, a code the stage does not say,
    vocabularies that are not the stage's, a silence value that is not the stage's, an edge that
    is not a number, a count or a bar that is not a whole number, counts that are not whole
    numbers keyed by the stage's digit codes, an array whose dtype, shape or digest disagrees
    with its descriptor, a slice count or a grid that is not the codes', a code value outside the
    vocabulary, digits that are not the codes' own values, a walk whose saved indices do not
    match its slices, digits saved without the series' squint stack, or a stack whose grid or
    slices are not the digits', means the record and this renderer disagree, and is raised
    rather than drawn. The stack is read through the stack drawer's own reader, which validates
    it against the writer's descriptors; its bounds place the tiles.
    """
    artifact = run / record["artifact"]
    descriptors = record["arrays"]
    saved_study = record.get("study") or {}
    walk_name = saved_study.get("walk_array")
    walk_indices = tuple(int(index) for index in saved_study.get("walk_indices", ()))
    saved = record.get("tile_digits")
    code = why = low = high = population = bar = counts = tiles = None
    drawn: dict[str, np.ndarray] = {}
    bounds = None
    if saved is not None:
        if type(saved) is not dict:
            raise ValueError("saved_tile_digits_not_a_record")
        for key in ("code", "why"):
            if type(saved.get(key)) is not str:
                raise ValueError(f"saved_tile_digits_field_invalid:{key}")
        if saved["code"] not in TILE_DIGIT_CODES:
            raise ValueError(f"saved_tile_digits_code_unknown:{saved['code']}")
        if saved.get("code_names") != list(TILE_DIGIT_CODES) or saved.get(
            "digit_code_names"
        ) != list(DIGIT_CODES):
            raise ValueError("saved_tile_digits_vocabulary_mismatch")
        if saved.get("digit_silence") != SILENT:
            raise ValueError("saved_tile_digits_silence_mismatch")
        code, why = saved["code"], saved["why"]
        low = saved_number(saved.get("low_edge"), "low_edge")
        high = saved_number(saved.get("high_edge"), "high_edge")
        population = saved_count(saved.get("population_count"), "population_count")
        bar = saved_count(saved.get("minimum_population"), "minimum_population")
        saved_counts = saved.get("counts")
        if not (
            isinstance(saved_counts, dict)
            and list(saved_counts) == list(DIGIT_CODES)
            and all(
                type(count) is int and count >= 0 for count in saved_counts.values()
            )
        ):
            raise ValueError("saved_tile_digits_counts_invalid")
        counts = tuple(saved_counts[name] for name in DIGIT_CODES)
        names = saved.get("arrays")
        if type(names) is not dict:
            raise ValueError("saved_tile_digits_arrays_missing")
        for short in DIGIT_ARRAYS:
            if type(names.get(short)) is not str:
                raise ValueError(f"saved_tile_digits_array_unnamed:{short}")
        tiles = saved.get("tiles_rc")
        if not (
            isinstance(tiles, list)
            and len(tiles) == 2
            and all(type(size) is int and size >= 0 for size in tiles)
        ):
            raise ValueError("saved_tile_digits_tiles_invalid")
    with np.load(artifact, allow_pickle=False) as arrays:
        walk = (
            saved_array(arrays, descriptors, walk_name, 3)
            if walk_name is not None
            else None
        )
        if saved is not None:
            for short, (dtype, ndim) in DIGIT_ARRAYS.items():
                array = saved_array(arrays, descriptors, saved["arrays"][short], ndim)
                if array.dtype != dtype:
                    raise ValueError(
                        f"saved_tile_digits_representation_invalid:{short}"
                    )
                drawn[short] = array
    if walk is not None and walk.shape[0] != len(walk_indices):
        raise ValueError("saved_walk_indices_mismatch")
    if saved is not None and tiles is not None:
        codes, digits = drawn["codes"], drawn["digits"]
        if saved.get("slices") != codes.shape[0]:
            raise ValueError("saved_tile_digits_slices_mismatch")
        if tuple(codes.shape[1:]) != (int(tiles[0]), int(tiles[1])):
            raise ValueError("saved_tile_digits_shape_mismatch:codes")
        if digits.shape != codes.shape:
            raise ValueError("saved_tile_digits_shape_mismatch:digits")
        if codes.size and int(codes.max()) >= len(DIGIT_CODES):
            raise ValueError("saved_tile_digits_code_unknown:codes")
        # The digits are the codes' own stored values and nothing else; a record whose two
        # arrays disagree was not written by the stage.
        if codes.size and not np.array_equal(digits, DIGIT_VALUES[codes]):
            raise ValueError("saved_tile_digits_disagree_with_codes")
        # The digits are read over the series' own squint stack, so a record that saved the
        # one and not the other disagrees with the writer; the stack's grid and slices must be
        # the digits', because the stack's bounds are what place the tiles on the plane.
        if "squint_stack" not in record:
            raise ValueError("saved_tile_digits_without_a_stack")
        _, stack = squint_stack_frames.saved_stack(run, record)
        bounds = stack.bounds_rc
        if (
            bounds is None
            or tuple(bounds.shape[:2]) != tuple(codes.shape[1:])
            or stack.slices != int(codes.shape[0])
        ):
            raise ValueError("saved_tile_digits_grid_mismatch")
    return artifact, pictures.digit_panels(
        code,
        why,
        low,
        high,
        population,
        bar,
        counts,
        drawn.get("codes"),
        drawn.get("digits"),
        bounds,
        walk_indices,
        walk,
    )


def digit_counts(codes: np.ndarray | None) -> dict[str, int]:
    """How many tiles at one slice carry each digit code, from the saved codes; empty when none."""
    if codes is None:
        return {}
    values = np.asarray(codes)
    return {
        name: int(np.count_nonzero(values == value))
        for value, name in enumerate(DIGIT_CODES)
    }


def silence_mask(codes: np.ndarray) -> np.ndarray:
    """Which tiles of one slice carry a silence, whichever of the oracle's words it is."""
    return np.isin(np.asarray(codes), SILENCE_VALUES)


def silent_count(counts: Mapping[str, int]) -> int:
    """How many of the counted tiles are a silence, from the saved counts."""
    return sum(count for name, count in counts.items() if name not in READ_CODES)


def number(value: float | None) -> str:
    """A saved edge as text; None is how a pair the oracle could not read comes back."""
    return "not read" if value is None else f"{value:g}"


def image_name(index: int, record: dict) -> str:
    """One sheet per view, named as the view sheets are: its order, plane and the two flags."""
    view, fluid, fat = record["view"]
    return f"{index:02d}-{view.lower()}-fs{fluid}-fat{fat}.png"


def digit_lines(record: dict, frame: pictures.TileDigitPanels) -> list[str]:
    """The text panel: the series, its view, and the digits' standing with its edges, bar and counts."""
    view, fluid, fat = record["view"]
    lines = [
        fill(record["series_uid"], width=40),
        f"{view} · fluid-sensitive={fluid}, fat-suppressed={fat}",
        "",
    ]
    if frame.code is None:
        lines.append("tile digits (lenses): not saved")
        lines.append(fill(STANDING_WORDS["digits_not_saved"], width=40))
        return lines
    lines += [
        f"tile digits (lenses): {frame.code}",
        fill(f"why: {frame.why}", width=40),
        "",
        f"low edge      {number(frame.low_edge)}",
        f"high edge     {number(frame.high_edge)}",
        f"counted       {frame.population_count}",
        f"bar           {frame.minimum_population}",
        f"slices        {frame.slices}",
    ]
    if frame.codes is not None and frame.codes.ndim == 3:
        lines.append(
            f"grid          {frame.codes.shape[1]} x {frame.codes.shape[2]} tiles"
        )
    if frame.counts is not None:
        lines += ["", "tiles over the stack"]
        lines += [
            f"  {name:<21}{count}"
            for name, count in zip(DIGIT_CODES, frame.counts, strict=True)
        ]
    lines.append("")
    lines.append("walked        " + ", ".join(str(step.index) for step in frame.walked))
    return lines


def draw_walked(axis, step: pictures.WalkedDigits, frame: pictures.TileDigitPanels):
    """One walked slice: the plane in grey with every tile by its digit over it, or the silence in words.

    Returns the step's standing, or `tiles_alone` when the digits are drawn with no plane beneath.
    """
    from matplotlib.patches import Patch

    axis.set_axis_off()
    if step.standing != "named" or step.codes is None or frame.bounds_rc is None:
        axis.set_title(f"stack index {step.index}", fontsize=8)
        words = STANDING_WORDS[step.standing]
        if step.standing == "digits_absent" and frame.code is not None:
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
    for name, value in READ_VALUES.items():
        mask = step.codes == value
        if not mask.any():
            continue
        overlay(axis, edges, mask, DIGIT_COLOURS[name], alpha=DIGIT_ALPHA)
        present.append((f"{name} ({int(mask.sum())})", DIGIT_COLOURS[name]))
    silence = silence_mask(step.codes)
    if silence.any():
        overlay(axis, edges, silence, SILENCE_COLOUR, alpha=SILENCE_ALPHA)
        present.append((f"silence ({int(silence.sum())})", SILENCE_COLOUR))
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
        f"stack index {step.index}\ntiles by digit, {where}; "
        f"silence {int(silence.sum())} ({frame.code})",
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
    loaded = [saved_digits(run, record) for record in records]
    if pictures.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:tiles")
    # Every standing the adapter can name has words here, and every digit that is a reading a
    # colour, checked before anything is drawn.
    unworded = [name for name in pictures.DIGIT_STANDINGS if name not in STANDING_WORDS]
    if unworded:
        raise RuntimeError(f"digit_standing_unworded:{','.join(unworded)}")
    uncoloured = [name for name in READ_CODES if name not in DIGIT_COLOURS]
    if uncoloured:
        raise RuntimeError(f"tile_digits_vocabulary_uncoloured:{','.join(uncoloured)}")

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
        text.set_title("the tile digits", fontsize=8)
        text.text(
            0.0,
            1.0,
            "\n".join(digit_lines(record, frame)),
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
                "no walk saved for this series: no slice to draw the digits at",
                transform=axes[0, 1].transAxes,
                va="center",
            )
        for column, step in enumerate(frame.walked, start=1):
            standings.append(
                {
                    "index": step.index,
                    "standing": step.standing,
                    "drawn": draw_walked(axes[0, column], step, frame),
                    "counts": digit_counts(step.codes),
                }
            )
        view, fluid, fat = record["view"]
        sheet.suptitle(
            f"The funnel's tile digits · {view} · fluid-sensitive={fluid}, "
            f"fat-suppressed={fat} · series {record['series_uid']}\n"
            "the digits' standing, then every tile by its digit against this series' own "
            "kept-tile edges at the study stage's walked slices, each over the acquired "
            "plane at that slice and placed by the squint stack's own native bounds\n"
            "blue: below · green: at · amber: above · grey: silence, a tile the first lens "
            "cleared, an empty tile, or a series whose oracle gave no edges",
            fontsize=9,
        )
        name = image_name(index, record)
        sheet.savefig(target / name, dpi=DPI)
        plt.close(sheet)
        saved = record.get("tile_digits")
        series.append(
            {
                "image": name,
                "image_sha256": sha256((target / name).read_bytes()).hexdigest(),
                "series_uid": record["series_uid"],
                "artifact": record["artifact"],
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "view": record["view"],
                "tile_digits": None
                if saved is None
                else {
                    "code": frame.code,
                    "why": frame.why,
                    "low_edge": frame.low_edge,
                    "high_edge": frame.high_edge,
                    "population_count": frame.population_count,
                    "minimum_population": frame.minimum_population,
                    "counts": None
                    if frame.counts is None
                    else dict(zip(DIGIT_CODES, frame.counts, strict=True)),
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
        "schema": "tile-digit-frames-v1",
        "receipt_sha256": sha256(receipt_bytes).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": {
            "tiles": sha256(Path(pictures.__file__).read_bytes()).hexdigest()
        },
        "study_uid": study_uid,
        "image": series[0]["image"],
        "images": [entry["image"] for entry in series],
        "frame_kind": "study",
        "standings": list(pictures.DIGIT_STANDINGS),
        "legend": {
            "digits": dict(DIGIT_COLOURS),
            "silence": SILENCE_COLOUR,
            "alphas": {"digit": DIGIT_ALPHA, "silence": SILENCE_ALPHA},
            "silence_words": [name for name in DIGIT_CODES if name not in READ_CODES],
        },
        "series": series,
        "note": (
            "Every value is a saved one. A walked slice the digits do not hold, digits the "
            "stage did not make and digits this run's writer did not save are three silences, "
            "each named; none is a zero. A silent tile is drawn in one neutral tone, never as "
            "a digit. One sheet per view, for the founder's eye."
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
