"""Draw the study stage's saved values: the selected plane, and the stage's own walk through the stack.

Task 6.9 of `openspec/changes/every-stage-renders`. The study stage's picture is a walk through the
stacked volume with a named code per slice (`knee.pictures.study`). Since 2026-10-12 the stage
RETAINS that walk (`Series.walk`, the slices `knee.study.series.walk_indices` visits) and its
per-slice codes, the route carries them, and the writer saves them beside the plane the objects
stage selected. This workbench arranges exactly those saved values through
`knee.pictures.study.recorded_panels`. A run whose writer saved no walk still draws its plane and
says the walk is absent; the manifest's `scope` states what was drawn.

Nothing here decodes, windows, rescales or measures. The grey scale is Matplotlib's linear display
scale over the stored values, so each series is shown on its own scale and two are never put on one.
Each value is labelled with the stage that produced it: the pixels, the stack codes, the per-slice
codes and the walk are the study stage's; which plane was selected, its file, its pixel spacing and
its thickness are what the objects stage recorded when it read the header; the view comes from the
series table.

The superior end is the field stage's reading of the selected plane's header, its structural
reading's axis and superior codes, named by `knee.pictures.study.superior_end`. An in-plane axis
names an image edge, marked on every plane drawn; the stack normal names an end of the stack, and
the walked slices at the stack's two ends say which is which. A run whose writer saved no
structural reading says the superior end is not saved, and a code the stage does not say is named
and never drawn.
"""

import argparse
import json
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from textwrap import fill

import numpy as np

from knee.pictures import study
from knee.pictures.study import SUPERIOR_ENDS
from workbench.render._out import PROJECT, ArgumentRefusal

#: Stated in the manifest: what this frame draws, and what it draws only when the writer saved it.
SCOPE = (
    "the selected stored plane, and the study stage's retained walk through the stack "
    "with its per-slice codes where the run's writer saved them, and the superior end "
    "named from the field stage's saved header codes where the writer saved them"
)

#: What each named superior end says, in words, for a series' heading. The codes are the adapter's
#: (`knee.pictures.study.SUPERIOR_ENDS`); the words are this drawing's.
SUPERIOR_END_WORDS: Mapping[str, str] = {
    "top_edge": "the top edge of every plane",
    "bottom_edge": "the bottom edge of every plane",
    "left_edge": "the left edge of every plane",
    "right_edge": "the right edge of every plane",
    "first_slice": "the first slice of the stack (stack index 0)",
    "last_slice": "the last slice of the stack (the highest stack index)",
    "not_saved": "not saved: this run's writer saved no structural reading for this series",
    "axis_ambiguous": "not read: the header's three z cosines tie for the largest, so it names no axis",
    "axis_unreadable": "not read: the header did not read as finite direction cosines",
    "direction_unreadable": "not read: the header's axis has no direction (its z cosine is zero)",
    "axis_code_unknown": "not drawn: the saved axis code is one the field stage does not say",
    "superior_code_unknown": "not drawn: the saved superior code is one the field stage does not say",
}

#: The ends that are an image edge, with the strip that marks each along the edge, as fractions of
#: an axes (x, y, width, height), and where its letter sits (x, y, horizontal and vertical alignment).
EDGE_MARKS: Mapping[
    str, tuple[tuple[float, float, float, float], tuple[float, float, str, str]]
] = {
    "top_edge": ((0.0, 0.985, 1.0, 0.015), (0.5, 0.97, "center", "top")),
    "bottom_edge": ((0.0, 0.0, 1.0, 0.015), (0.5, 0.03, "center", "bottom")),
    "left_edge": ((0.0, 0.0, 0.015, 1.0), (0.03, 0.5, "left", "center")),
    "right_edge": ((0.985, 0.0, 0.015, 1.0), (0.97, 0.5, "right", "center")),
}

#: The colour of the superior-end mark: one no stored value is drawn in.
SUPERIOR_COLOUR = "#22d3ee"


def saved_array(
    arrays: Mapping[str, np.ndarray], descriptors: dict, name: str, ndim: int
) -> np.ndarray:
    """Validate one saved array against the writer's descriptor: dtype, shape and content digest.

    The digest is the writer's own: sha256 over the dtype string, the shape and the bytes.
    """
    if name not in arrays or name not in descriptors:
        raise ValueError(f"missing_saved_array:{name}")
    array = arrays[name]
    descriptor = descriptors[name]
    if array.dtype.str != descriptor["dtype"]:
        raise ValueError(f"saved_array_dtype_mismatch:{name}")
    if array.shape != tuple(descriptor["shape"]):
        raise ValueError(f"saved_array_shape_mismatch:{name}")
    digest = sha256(
        array.dtype.str.encode() + str(array.shape).encode() + array.tobytes()
    ).hexdigest()
    if digest != descriptor["digest"]:
        raise ValueError(f"saved_array_digest_mismatch:{name}")
    if array.ndim != ndim:
        raise ValueError(f"saved_array_representation_invalid:{name}")
    return array


def saved_header_codes(record: dict) -> tuple[str | None, str | None]:
    """The field stage's two header codes for the selected plane as saved, or (None, None).

    A record that saved no structural reading saved no codes, and its superior end is drawn as not
    saved. A structural reading whose axis or superior is not text disagrees with the writer, and
    is raised. A code the field stage does not say is not judged here: the adapter names it.
    """
    saved = record.get("structure")
    if saved is None:
        return None, None
    if type(saved) is not dict:
        raise ValueError("saved_structure_not_a_record")
    axis, superior = saved.get("axis"), saved.get("superior")
    if type(axis) is not str or type(superior) is not str:
        raise ValueError("saved_structure_header_codes_not_text")
    return axis, superior


def saved_recorded(run: Path, record: dict) -> tuple[Path, study.RecordedPanels]:
    """Reconstitute one series' saved plane and stated geometry, without measuring.

    Total over a series with no saved plane: that is drawn as the silence it is. An array whose
    dtype, shape or digest disagrees with its descriptor, a stored plane that is not numeric, or a
    spacing that is not a pair, means the record and this renderer disagree, and is raised.
    """
    artifact = run / record["artifact"]
    descriptors = record["arrays"]
    plane = None
    walk = None
    saved_study = record.get("study") or {}
    walk_name = saved_study.get("walk_array")
    with np.load(artifact, allow_pickle=False) as arrays:
        if "acquired_plane" in descriptors:
            plane = saved_array(arrays, descriptors, "acquired_plane", 2)
            if plane.dtype.kind not in "iuf":
                raise ValueError("saved_array_representation_invalid:acquired_plane")
        if walk_name is not None:
            walk = saved_array(arrays, descriptors, walk_name, 3)
            if walk.shape[0] != len(saved_study.get("walk_indices", ())):
                raise ValueError("saved_walk_indices_mismatch")
    spacing = record.get("spacing_rc_mm")
    if spacing is not None and len(spacing) != 2:
        raise ValueError("saved_spacing_mismatch")
    # Each code is labelled with the stage that produced it: the study stage's stack codes where
    # the writer saved them (it did not before 2026-10-12), then the objects stage's.
    codes = []
    if record.get("stack") is not None:
        codes.append("study stage stack codes: " + ", ".join(record["stack"]))
    codes.append(f"objects stage code: {record['code']}")
    if record.get("validation_code") is not None:
        codes.append(f"objects stage validation code: {record['validation_code']}")
    axis_code, superior_code = saved_header_codes(record)
    return artifact, study.recorded_panels(
        plane,
        spacing,
        record.get("slice_thickness_mm"),
        record.get("slice_index"),
        tuple(codes),
        walk=walk,
        walk_indices=tuple(saved_study.get("walk_indices", ())),
        slice_codes=tuple(saved_study.get("slice_codes", ())),
        axis_code=axis_code,
        superior_code=superior_code,
    )


def superior_line(frame: study.RecordedPanels) -> str:
    """Where the superior end lies, in words, with the codes it was named from.

    The codes are the field stage's reading of the selected plane's header, so the line says whose
    reading it is; a record that saved none says that instead.
    """
    end = study.superior_end(frame.axis_code, frame.superior_code)
    source = (
        ""
        if frame.axis_code is None
        else f" (field stage, selected plane's header: axis {frame.axis_code}, "
        f"superior {frame.superior_code})"
    )
    return f"superior end{source}: {SUPERIOR_END_WORDS.get(end, end)}"


def stack_end_tag(end: str, index: int, stack_count: int) -> str:
    """Which end of the stack a walked slice is, when the superior end is an end of the stack.

    The stack is ordered ascending along its normal, so stack index 0 is its first end and
    `stack_count - 1` its last. `stack_count` is the number of per-slice codes the record saved,
    0 when it saved none, and then only the first end can be told. Empty for any other slice.
    """
    if end not in ("first_slice", "last_slice"):
        return ""
    if index == 0 and stack_count != 1:
        return f"{'superior' if end == 'first_slice' else 'inferior'} end of the stack"
    if stack_count > 1 and index == stack_count - 1:
        return f"{'superior' if end == 'last_slice' else 'inferior'} end of the stack"
    return ""


def panel_title(record: dict, frame: study.RecordedPanels) -> str:
    """The panel's labels: identity, the series table's view, and each recorded value by stage."""
    view, fluid, fat = record["view"]
    index = "not recorded" if frame.slice_index is None else str(frame.slice_index)
    source = record.get("source_plane") or "not recorded"
    if frame.spacing_mm is None:
        spacing = "not recorded"
    else:
        spacing = f"{frame.spacing_mm[0]:.4g} × {frame.spacing_mm[1]:.4g} mm"
    thickness = (
        "not recorded" if frame.thickness_mm is None else f"{frame.thickness_mm:.4g} mm"
    )
    # The series identifier and the file name are single tokens: wrapping them mid-token would
    # leave a fragment on a line of its own, so each takes a whole line.
    lines = [
        record["series_uid"],
        f"series table: {view} · fluid-sensitive={fluid}, fat-suppressed={fat}",
        f"plane selected by the objects stage: stack index {index}",
        f"its file: {source}",
        "header geometry as the objects stage recorded it:",
        f"pixel spacing (rows × columns) {spacing} · slice thickness {thickness}",
        *(fill(code, width=84) for code in frame.codes),
        fill(superior_line(frame), width=84),
    ]
    return "\n".join(lines)


def mark_superior_edge(axis, end: str) -> None:
    """Mark the image edge the superior end names, along the edge and with a letter.

    Drawn in axes fractions, so it sits on the edge of the plane as drawn and moves no limit.
    """
    from matplotlib.patches import Rectangle

    strip, (x, y, horizontal, vertical) = EDGE_MARKS[end]
    axis.add_patch(
        Rectangle(
            strip[:2],
            strip[2],
            strip[3],
            transform=axis.transAxes,
            facecolor=SUPERIOR_COLOUR,
            edgecolor="none",
            clip_on=False,
        )
    )
    axis.text(
        x,
        y,
        "S",
        transform=axis.transAxes,
        color="black",
        fontsize=9,
        fontweight="bold",
        ha=horizontal,
        va=vertical,
        bbox={"facecolor": SUPERIOR_COLOUR, "edgecolor": "none", "pad": 1.5},
    )


def draw(run: Path, study_uid: str, out: Path) -> dict:
    """Draw this stage from the saved run and return its manifest.

    The one entry a caller uses, so the single command can draw every stage without knowing each
    renderer's argument spelling. `main()` is a thin wrapper over it, so the hand-typed command
    and the joined run draw the same thing from the same code.

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
    loaded = [saved_recorded(run, record) for record in records]
    if study.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:study")
    # The words this drawing gives each end are checked against the adapter's vocabulary before
    # anything is drawn: an end the adapter can name that this table cannot word would be drawn
    # as its bare code, a word from nowhere on the picture.
    unworded = [end for end in SUPERIOR_ENDS if end not in SUPERIOR_END_WORDS]
    if unworded:
        raise RuntimeError(f"superior_end_unworded:{','.join(unworded)}")

    import matplotlib.pyplot as plt

    target.mkdir(parents=True, exist_ok=True)
    # One row per series: the selected plane, then the stage's own walk through the stack, each
    # walked slice titled with its stack index and the stage's code for it.
    walked = max((len(frame.walk_indices) for _, frame in loaded), default=0)
    across = 1 + walked
    down = len(records)
    gallery, axes = plt.subplots(
        down,
        across,
        figsize=(4.2 * across, 5.4 * down),
        layout="constrained",
        squeeze=False,
    )
    for axis in axes.flat:
        axis.set_axis_off()
    series = []
    for row, (record, (artifact, frame)) in enumerate(
        zip(records, loaded, strict=True)
    ):
        end = study.superior_end(frame.axis_code, frame.superior_code)
        axis = axes[row, 0]
        axis.set_title(panel_title(record, frame), fontsize=6.5, loc="left")
        if frame.plane is None:
            axis.text(
                0.03,
                0.5,
                "no plane saved for this series",
                transform=axis.transAxes,
                va="center",
            )
        else:
            image = axis.imshow(frame.plane, cmap="gray", interpolation="nearest")
            axis.figure.colorbar(image, ax=axis, shrink=0.7, label="stored values")
            if end in EDGE_MARKS:
                mark_superior_edge(axis, end)
        for column in range(1, across):
            step = axes[row, column]
            if frame.walk is None or column - 1 >= len(frame.walk_indices):
                if column == 1 and frame.walk is None:
                    step.text(
                        0.03,
                        0.5,
                        "no walk saved for this series",
                        transform=step.transAxes,
                        va="center",
                    )
                continue
            index = frame.walk_indices[column - 1]
            code = (
                frame.slice_codes[index]
                if index < len(frame.slice_codes)
                else "code not saved"
            )
            tag = stack_end_tag(end, index, len(frame.slice_codes))
            step.set_title(
                f"stack index {index}\nstudy stage: {code}"
                + (f"\n{tag}" if tag else ""),
                fontsize=7,
            )
            step.imshow(frame.walk[column - 1], cmap="gray", interpolation="nearest")
            if end in EDGE_MARKS:
                mark_superior_edge(step, end)
        series.append(
            {
                "series_uid": record["series_uid"],
                "artifact": record["artifact"],
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "view": record["view"],
                "slice_index": record.get("slice_index"),
                "source_plane": record.get("source_plane"),
                "spacing_rc_mm": record.get("spacing_rc_mm"),
                "slice_thickness_mm": record.get("slice_thickness_mm"),
                "codes": list(frame.codes),
                "superior_end": {
                    "code": end,
                    "axis_code": frame.axis_code,
                    "superior_code": frame.superior_code,
                },
                "plane": record["arrays"].get("acquired_plane"),
                "walk": None
                if frame.walk is None
                else {
                    "array": record["arrays"].get(
                        (record.get("study") or {}).get("walk_array")
                    ),
                    "indices": list(frame.walk_indices),
                    "slice_codes": list(frame.slice_codes),
                },
                "source_files_hashed": len(record["sources"])
                if "sources" in record
                else None,
                "frame_kind": "study",
            }
        )
    gallery.suptitle(
        "The study stage, one row per series: the selected stored plane, then the stage's own "
        "walk through the stack with its code for every walked slice",
        fontsize=11,
    )
    gallery.savefig(target / "series.png", dpi=130)
    plt.close(gallery)
    manifest = {
        "schema": "study-frames-v1",
        "receipt_sha256": sha256(receipt_bytes).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": {
            "study": sha256(Path(study.__file__).read_bytes()).hexdigest()
        },
        "study_uid": study_uid,
        "image": "series.png",
        "frame_kind": "study",
        "scope": SCOPE,
        "series": series,
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
