"""Draw the funnel's conjunction: one sheet per recipient, every tile by its code over the acquired plane at the walked slices.

The-funnel task 3c.2 (`openspec/changes/the-funnel/tasks.md`). The funnel's operation 3c
(`knee.lenses.conjunction`) reads the two acquisitions of a paired plane together at every tile
of the fat-dark recipient, through the line-up's partner tiles, as one named code; the writer
saves the record whole on the recipient beside its digits, its line-up and its stack. This
workbench arranges those saved values through `knee.pictures.conjunction`: ONE SHEET PER
RECIPIENT (one image per recipient series), so the founder can check each paired plane by eye
(task 3c.1: on the coronal pair, whether the `above_below` tiles fill the two big bright regions
and the `below_below` tiles trace the dark line between them): the conjunction's standing in
words, then one panel per step of the study stage's own walk through the stack (`Series.walk`,
the slices `knee.study.series.walk_indices` visits, saved by the writer): the acquired plane at
that slice in grey, and over it every tile by its code, placed in native pixels by the squint
stack's saved bounds -- the nine read pairs in nine distinguishable colours, the two silences
and the unmatched tile in three neutral tones, the refusal loud -- with a legend naming every
word present at that slice with its count. It takes no measurement of its own: every number on
the page is a saved value, and every gap is a named silence, never a zero.

Four silences are kept apart, because each has its own remedy
(`knee.pictures.conjunction.CONJUNCTION_STANDINGS`): this run's writer saved no conjunction for
the series; the saved code is a word the stage does not say; the stage named no tile and says
why (its line-up or a digit record was absent); the walked slice lies outside the slices the
conjunction holds. A study with no recipient draws its silence in words: a partner, a solitary
and a surplus series carry no conjunction, and that is the silence it is. A recipient whose
writer saved no walk draws its tiles alone on the tile grid and the title says so. A conjunction
saved without the recipient's squint stack, or one that holds a grid other than the stack's,
disagrees with the writer and is refused rather than drawn. A conjunction the stage did not
make holds no grid at all (the writer saves it with (0, 0, 0) codes beside the recipient's
stack, which may well be present: the ordinary form is a partner whose stack is absent), so it
is handed on as the silence it is and never compared with the stack's grid; one that claims
that silence while holding codes was not written by the stage, and is refused.

Nothing here reads a digit, re-reads the line-up or recomputes a code. The grey scale is
Matplotlib's linear display scale over each plane's own stored values.
"""

import argparse
import json
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from textwrap import fill

import numpy as np

from knee.lenses.conjunction import (
    CONJUNCTION_CODES,
    CONJUNCTION_RECORD_CODES,
    READ_CONJUNCTIONS,
)
from knee.pictures import conjunction as pictures
from workbench.render import squint_stack_frames
from workbench.render._out import PROJECT, ArgumentRefusal
from workbench.render.field_frames import (
    native_extent,
    overlay,
    saved_array,
    tile_edges,
)

#: The conjunction's arrays by the short names the writer gives them in
#: `record["conjunction"]["arrays"]`, each with the dtype it must have and its number of axes.
CONJUNCTION_ARRAYS: Mapping[str, tuple[np.dtype, int]] = {
    "codes": (np.dtype(np.uint8), 3)
}

#: What each silence a walked slice can hold says, in words. The codes are the adapter's
#: (`knee.pictures.conjunction.CONJUNCTION_STANDINGS`); the words are this drawing's.
STANDING_WORDS: Mapping[str, str] = {
    "named": "every tile at this slice by its conjunction code, over the plane",
    "conjunction_not_saved": (
        "not saved: this run's writer saved no conjunction for this series"
    ),
    "conjunction_code_unknown": "not drawn: the saved code is one the stage does not say",
    "conjunction_absent": (
        "not made: the stage named no tile; its own code and reason are beside"
    ),
    "slice_outside_conjunction": (
        "not drawn: the walked slice lies outside the slices the conjunction holds"
    ),
}

#: What each conjunction code is drawn in: the nine ordered pairs `<partner>_<own>` in nine
#: distinguishable colours, none of them a grey; the two silences and the unmatched tile in
#: three neutral tones, so a silence is drawn as silence and never as a pair; the refusal in a
#: colour no reading takes. Every code of the stage's vocabulary has an entry, checked before
#: anything is drawn.
CODE_COLOURS: Mapping[str, str] = {
    "below_below": "#1d4ed8",
    "below_at": "#06b6d4",
    "below_above": "#14b8a6",
    "at_below": "#7c3aed",
    "at_at": "#22c55e",
    "at_above": "#84cc16",
    "above_below": "#f59e0b",
    "above_at": "#f97316",
    "above_above": "#ef4444",
    "partner_silent": "#e5e7eb",
    "self_silent": "#9ca3af",
    "unmatched": "#4b5563",
    "invalid_measurement": "#ff00ff",
}
PAIR_ALPHA = 0.45
NEUTRAL_ALPHA = 0.35
REFUSAL_ALPHA = 0.6
CODE_ALPHAS: Mapping[str, float] = {
    **{name: PAIR_ALPHA for name in READ_CONJUNCTIONS},
    "partner_silent": NEUTRAL_ALPHA,
    "self_silent": NEUTRAL_ALPHA,
    "unmatched": NEUTRAL_ALPHA,
    "invalid_measurement": REFUSAL_ALPHA,
}

#: The words that are not a reading of both sides: the silences, the unmatched tile and the
#: refusal, read from the stage's own vocabulary so the drawer names nothing.
NEUTRAL_WORDS: tuple[str, ...] = tuple(
    name for name in CONJUNCTION_CODES if name not in READ_CONJUNCTIONS
)

#: One sheet per recipient: the text panel, then one panel per walked slice.
PANEL_INCHES = 4.2
ROW_INCHES = 5.4
DPI = 120


def saved_conjunction(
    run: Path, record: dict
) -> tuple[Path, pictures.ConjunctionPanels]:
    """Reconstitute one recipient's saved conjunction and the study stage's saved walk, without measuring.

    Total over a series whose writer saved no conjunction, or no walk, or a conjunction the
    stage did not make (`predecessor_absent`, with (0, 0, 0) codes): each is handed on as the
    silence it is, the last with no bounds, since it places no tile. A conjunction record that
    is not a mapping, a code the stage does not say, a recipient that is not this series, a
    vocabulary that is not the stage's, counts that are not whole numbers keyed by the stage's
    codes, an array whose dtype, shape or digest disagrees with its descriptor, a slice count or
    a grid that is not the codes', a code value outside the vocabulary, a walk whose saved
    indices do not match its slices, a conjunction saved without the recipient's squint stack,
    a `present` conjunction whose grid or slices are not the stack's, or an absent conjunction
    that holds codes, means the record and this renderer disagree, and is raised rather than
    drawn. The stack is read through the stack drawer's own reader, which validates it against
    the writer's descriptors; its bounds place the tiles of a `present` conjunction.
    """
    artifact = run / record["artifact"]
    descriptors = record["arrays"]
    saved_study = record.get("study") or {}
    walk_name = saved_study.get("walk_array")
    walk_indices = tuple(int(index) for index in saved_study.get("walk_indices", ()))
    saved = record.get("conjunction")
    code = why = recipient = partner = counts = tiles = None
    drawn: dict[str, np.ndarray] = {}
    bounds = None
    if saved is not None:
        if type(saved) is not dict:
            raise ValueError("saved_conjunction_not_a_record")
        for key in ("code", "why", "recipient_uid", "partner_uid"):
            if type(saved.get(key)) is not str:
                raise ValueError(f"saved_conjunction_field_invalid:{key}")
        if saved["code"] not in CONJUNCTION_RECORD_CODES:
            raise ValueError(f"saved_conjunction_code_unknown:{saved['code']}")
        if saved["recipient_uid"] != record.get("series_uid"):
            raise ValueError("saved_conjunction_recipient_mismatch")
        if saved.get("code_names") != list(CONJUNCTION_CODES):
            raise ValueError("saved_conjunction_vocabulary_mismatch")
        code, why = saved["code"], saved["why"]
        recipient, partner = saved["recipient_uid"], saved["partner_uid"]
        saved_counts = saved.get("counts")
        if not (
            isinstance(saved_counts, dict)
            and list(saved_counts) == list(CONJUNCTION_CODES)
            and all(
                type(count) is int and count >= 0 for count in saved_counts.values()
            )
        ):
            raise ValueError("saved_conjunction_counts_invalid")
        counts = tuple(saved_counts[name] for name in CONJUNCTION_CODES)
        names = saved.get("arrays")
        if type(names) is not dict:
            raise ValueError("saved_conjunction_arrays_missing")
        for short in CONJUNCTION_ARRAYS:
            if type(names.get(short)) is not str:
                raise ValueError(f"saved_conjunction_array_unnamed:{short}")
        tiles = saved.get("tiles_rc")
        if not (
            isinstance(tiles, list)
            and len(tiles) == 2
            and all(type(size) is int and size >= 0 for size in tiles)
        ):
            raise ValueError("saved_conjunction_tiles_invalid")
    with np.load(artifact, allow_pickle=False) as arrays:
        walk = (
            saved_array(arrays, descriptors, walk_name, 3)
            if walk_name is not None
            else None
        )
        if saved is not None:
            for short, (dtype, ndim) in CONJUNCTION_ARRAYS.items():
                array = saved_array(arrays, descriptors, saved["arrays"][short], ndim)
                if array.dtype != dtype:
                    raise ValueError(
                        f"saved_conjunction_representation_invalid:{short}"
                    )
                drawn[short] = array
    if walk is not None and walk.shape[0] != len(walk_indices):
        raise ValueError("saved_walk_indices_mismatch")
    if saved is not None and tiles is not None:
        codes = drawn["codes"]
        if saved.get("slices") != codes.shape[0]:
            raise ValueError("saved_conjunction_slices_mismatch")
        if tuple(codes.shape[1:]) != (int(tiles[0]), int(tiles[1])):
            raise ValueError("saved_conjunction_shape_mismatch:codes")
        if codes.size and int(codes.max()) >= len(CONJUNCTION_CODES):
            raise ValueError("saved_conjunction_code_unknown:codes")
        # The conjunction rides on the recipient beside its squint stack, whatever the stage
        # said, so a record that saved the one and not the other disagrees with the writer.
        if "squint_stack" not in record:
            raise ValueError("saved_conjunction_without_a_stack")
        _, stack = squint_stack_frames.saved_stack(run, record)
        if code == "present":
            # A conjunction that holds a grid is read over the recipient's own squint stack
            # grid: the stack's grid and slices must be the conjunction's, because the stack's
            # bounds are what place the tiles on the plane.
            bounds = stack.bounds_rc
            if (
                bounds is None
                or tuple(bounds.shape[:2]) != tuple(codes.shape[1:])
                or stack.slices != int(codes.shape[0])
            ):
                raise ValueError("saved_conjunction_grid_mismatch")
        elif codes.size:
            # The only other word the stage says is `predecessor_absent`, which it writes with
            # (0, 0, 0) codes: it named no tile, so there is no grid to compare with the stack's
            # and no tile to place, and the bounds stay absent. A record that claims that
            # silence while holding codes was not written by the stage.
            raise ValueError("saved_conjunction_absent_with_codes")
    return artifact, pictures.conjunction_panels(
        code,
        why,
        recipient,
        partner,
        counts,
        drawn.get("codes"),
        bounds,
        walk_indices,
        walk,
    )


def code_counts(codes: np.ndarray | None) -> dict[str, int]:
    """How many tiles at one slice carry each conjunction code, from the saved codes; empty when none."""
    if codes is None:
        return {}
    values = np.asarray(codes)
    return {
        name: int(np.count_nonzero(values == value))
        for value, name in enumerate(CONJUNCTION_CODES)
    }


def read_count(counts: Mapping[str, int]) -> int:
    """How many of the counted tiles carry one of the nine pairs, from the saved counts."""
    return sum(count for name, count in counts.items() if name in READ_CONJUNCTIONS)


def image_name(index: int, record: dict) -> str:
    """One sheet per recipient, named as the view sheets are: its order, plane and the two flags."""
    view, fluid, fat = record["view"]
    return f"{index:02d}-{view.lower()}-fs{fluid}-fat{fat}.png"


def conjunction_lines(record: dict, frame: pictures.ConjunctionPanels) -> list[str]:
    """The text panel: the recipient, its view, the partner, and the conjunction's standing with its counts."""
    view, fluid, fat = record["view"]
    lines = [
        fill(record["series_uid"], width=40),
        f"{view} · fluid-sensitive={fluid}, fat-suppressed={fat}",
        "",
    ]
    if frame.code is None:
        lines.append("conjunction (lenses): not saved")
        lines.append(fill(STANDING_WORDS["conjunction_not_saved"], width=40))
        return lines
    lines += [
        f"conjunction (lenses): {frame.code}",
        fill(f"why: {frame.why}", width=40),
        "",
        "partner (fat-bright, same plane)",
        fill(str(frame.partner_uid), width=40),
        "",
    ]
    if frame.code != "present":
        # The stage named no tile: its silence holds no slice, no grid and no count, and a
        # zero here would read as a reading. Its own code and reason stand above.
        lines.append(
            fill(STANDING_WORDS["conjunction_absent"] + "; no slice, grid or count", 40)
        )
        lines.append("")
        lines.append(
            "walked        " + ", ".join(str(step.index) for step in frame.walked)
        )
        return lines
    lines.append(f"slices        {frame.slices}")
    if frame.codes is not None and frame.codes.ndim == 3:
        lines.append(
            f"grid          {frame.codes.shape[1]} x {frame.codes.shape[2]} tiles"
        )
    if frame.counts is not None:
        lines += ["", "tiles over the stack, <partner>_<own>"]
        lines += [
            f"  {name:<21}{count}"
            for name, count in zip(CONJUNCTION_CODES, frame.counts, strict=True)
        ]
    lines.append("")
    lines.append("walked        " + ", ".join(str(step.index) for step in frame.walked))
    return lines


def draw_walked(
    axis, step: pictures.WalkedConjunction, frame: pictures.ConjunctionPanels
):
    """One walked slice: the plane in grey with every tile by its code over it, or the silence in words.

    Returns the step's standing, or `tiles_alone` when the codes are drawn with no plane beneath.
    """
    from matplotlib.patches import Patch

    axis.set_axis_off()
    if step.standing != "named" or step.codes is None or frame.bounds_rc is None:
        axis.set_title(f"stack index {step.index}", fontsize=8)
        words = STANDING_WORDS[step.standing]
        if step.standing == "conjunction_absent" and frame.code is not None:
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
    for value, name in enumerate(CONJUNCTION_CODES):
        mask = step.codes == value
        if not mask.any():
            continue
        overlay(axis, edges, mask, CODE_COLOURS[name], alpha=CODE_ALPHAS[name])
        present.append((f"{name} ({int(mask.sum())})", CODE_COLOURS[name]))
    counts = code_counts(step.codes)
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
        f"stack index {step.index}\ntiles by conjunction code, {where}; "
        f"{read_count(counts)} read on both sides ({frame.code})",
        fontsize=8,
    )
    return standing


def draw(run: Path, study_uid: str, out: Path) -> dict:
    """Draw this stage from the saved run, one sheet per recipient, and return its manifest.

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
    # One sheet per RECIPIENT, numbered as the view sheets number the series, so a recipient's
    # sheet carries the same name as its view sheet.
    recipients = [
        (index, record)
        for index, record in enumerate(records, start=1)
        if "conjunction" in record
    ]
    loaded = [saved_conjunction(run, record) for _, record in recipients]
    if pictures.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:conjunction")
    # Every standing the adapter can name has words here, and every code a colour and an
    # alpha, checked before anything is drawn.
    unworded = [
        name for name in pictures.CONJUNCTION_STANDINGS if name not in STANDING_WORDS
    ]
    if unworded:
        raise RuntimeError(f"conjunction_standing_unworded:{','.join(unworded)}")
    uncoloured = [
        name
        for name in CONJUNCTION_CODES
        if name not in CODE_COLOURS or name not in CODE_ALPHAS
    ]
    if uncoloured:
        raise RuntimeError(f"conjunction_vocabulary_uncoloured:{','.join(uncoloured)}")

    import matplotlib.pyplot as plt

    target.mkdir(parents=True, exist_ok=True)
    silence = None
    images: list[str] = []
    series = []
    if not recipients:
        silence = (
            "no series of this study carries a conjunction: no plane is paired, or this "
            "run's writer saved none. A partner, a solitary and a surplus series carry no "
            "conjunction; it rides on the fat-dark recipient of a paired plane."
        )
        sheet, axis = plt.subplots(1, 1, figsize=(PANEL_INCHES * 2, ROW_INCHES))
        axis.set_axis_off()
        axis.set_title("the conjunction", fontsize=8)
        axis.text(0.0, 1.0, fill(silence, width=70), transform=axis.transAxes, va="top")
        sheet.suptitle(
            f"The funnel's conjunction · study {study_uid}\nno recipient in this run",
            fontsize=9,
        )
        name = "series.png"
        sheet.savefig(target / name, dpi=DPI)
        plt.close(sheet)
        images.append(name)
    for (index, record), (artifact, frame) in zip(recipients, loaded, strict=True):
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
        text.set_title("the conjunction, on the recipient", fontsize=8)
        text.text(
            0.0,
            1.0,
            "\n".join(conjunction_lines(record, frame)),
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
                "no walk saved for this series: no slice to draw the conjunction at",
                transform=axes[0, 1].transAxes,
                va="center",
            )
        for column, step in enumerate(frame.walked, start=1):
            standings.append(
                {
                    "index": step.index,
                    "standing": step.standing,
                    "drawn": draw_walked(axes[0, column], step, frame),
                    "counts": code_counts(step.codes),
                }
            )
        view, fluid, fat = record["view"]
        sheet.suptitle(
            f"The funnel's conjunction · {view} · fluid-sensitive={fluid}, "
            f"fat-suppressed={fat} · recipient {record['series_uid']}\n"
            "the conjunction's standing, then every tile by its code, the partner's digit "
            "and this series' own read together as <partner>_<own> at the study stage's "
            "walked slices, each over the acquired plane at that slice and placed by the "
            "squint stack's own native bounds\n"
            "nine colours for the nine ordered pairs · light grey: partner silent · grey: "
            "self silent · dark grey: unmatched, no partner tile named · magenta: the refusal",
            fontsize=9,
        )
        name = image_name(index, record)
        sheet.savefig(target / name, dpi=DPI)
        plt.close(sheet)
        images.append(name)
        saved = record["conjunction"]
        series.append(
            {
                "image": name,
                "image_sha256": sha256((target / name).read_bytes()).hexdigest(),
                "series_uid": record["series_uid"],
                "partner_uid": frame.partner_uid,
                "artifact": record["artifact"],
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "view": record["view"],
                "conjunction": {
                    "code": frame.code,
                    "why": frame.why,
                    "recipient_uid": frame.recipient_uid,
                    "partner_uid": frame.partner_uid,
                    "counts": None
                    if frame.counts is None
                    else dict(zip(CONJUNCTION_CODES, frame.counts, strict=True)),
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
        "schema": "conjunction-frames-v1",
        "receipt_sha256": sha256(receipt_bytes).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": {
            "conjunction": sha256(Path(pictures.__file__).read_bytes()).hexdigest()
        },
        "study_uid": study_uid,
        "image": images[0],
        "images": images,
        "frame_kind": "study",
        "standings": list(pictures.CONJUNCTION_STANDINGS),
        "legend": {
            "pairs": {name: CODE_COLOURS[name] for name in READ_CONJUNCTIONS},
            "neutral": {name: CODE_COLOURS[name] for name in NEUTRAL_WORDS},
            "alphas": {
                "pair": PAIR_ALPHA,
                "neutral": NEUTRAL_ALPHA,
                "refusal": REFUSAL_ALPHA,
            },
            "order": "<partner>_<own>: the fat-bright partner's digit first, then this series' own",
        },
        "silence": silence,
        "series": series,
        "note": (
            "Every value is a saved one. A walked slice the conjunction does not hold, a "
            "conjunction the stage did not make and a conjunction this run's writer did not "
            "save are three silences, each named; none is a zero. A silent or unmatched tile "
            "is drawn in a neutral tone, never as a pair. One sheet per recipient, for the "
            "founder's eye."
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
