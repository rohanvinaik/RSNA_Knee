"""Draw the output stage's companion record: the twelve joined to the competition's columns.

Task 6.9 of `openspec/changes/every-stage-renders`, drawing task 4.2's companion record from one saved
production study entry. The frame is about **pipeline state**. While the numeric projection is
undeclared the stage writes no submission row, so the table shows each finding's own code and reason
beside its competition column, and never what a knee holds. A missing reading is silence, never a
negative.

This workbench arranges values through `knee.pictures.output`. It joins nothing, evaluates no
predicate, selects no subject and writes no number against any finding. A value appears in the
table only when the stage itself saved a submission row for it.
"""

import argparse
import json
from hashlib import sha256
from pathlib import Path
from textwrap import fill

from knee.output.projection import (
    CODES as OUTPUT_CODES,
)
from knee.output.projection import (
    COLUMN_BY_INDEX,
    CompanionRow,
    OutputReading,
    Projection,
)
from knee.pictures import output as pictures
from knee.predicates.findings import CODES as FINDING_CODES
from workbench.render._out import PROJECT, ArgumentRefusal


def saved_reading(study: dict) -> OutputReading:
    """Reconstitute the stage's returned reading from one saved study entry, without deciding.

    Every saved field is checked against the vocabulary the stage owns rather than trusted: an
    output code outside its `CODES`, a companion that is not the twelve rows in the declared
    order, a column that is not the one `COLUMN_BY_INDEX` joins to that index, a finding code
    outside the predicates stage's `CODES`, a projection that is not a value with its author and
    date, or submission rows without a `present` standing, all mean the record and this renderer
    disagree, and that is reported rather than drawn.
    """
    if "output" not in study:
        raise ValueError("missing_saved_output")
    saved = study["output"]
    if saved["code"] not in OUTPUT_CODES:
        raise ValueError(f"saved_output_code_unknown:{saved['code']}")
    rows = saved["companion"]
    if len(rows) != len(COLUMN_BY_INDEX):
        raise ValueError("saved_companion_count_mismatch")
    if [row["index"] for row in rows] != [index for index, _ in COLUMN_BY_INDEX]:
        raise ValueError("saved_companion_index_mismatch")
    for row, (index, column) in zip(rows, COLUMN_BY_INDEX, strict=True):
        if row["column"] != column:
            raise ValueError(f"saved_companion_column_mismatch:{index}")
        if row["code"] not in FINDING_CODES:
            raise ValueError(f"saved_companion_code_unknown:{row['code']}")
        if len(row["subjects"]) != 2:
            raise ValueError(f"saved_companion_subjects_mismatch:{index}")
    projection = None
    if saved["projection"] is not None:
        if set(saved["projection"]) != {"value", "author", "declared"}:
            raise ValueError("saved_projection_mismatch")
        projection = Projection(
            value=float(saved["projection"]["value"]),
            author=saved["projection"]["author"],
            declared=saved["projection"]["declared"],
        )
    submitted = None
    if saved["submission_rows"] is not None:
        if saved["code"] != "present":
            raise ValueError("saved_submission_rows_without_present")
        if [column for column, _ in saved["submission_rows"]] != [
            column for _, column in COLUMN_BY_INDEX
        ]:
            raise ValueError("saved_submission_columns_mismatch")
        submitted = tuple(
            (column, float(value)) for column, value in saved["submission_rows"]
        )
    return OutputReading(
        code=saved["code"],
        why=saved["why"],
        companion=tuple(
            CompanionRow(
                index=row["index"],
                column=row["column"],
                code=row["code"],
                reason=row["reason"],
                subjects=(int(row["subjects"][0]), int(row["subjects"][1])),
                candidates=int(row["candidates"]),
            )
            for row in rows
        ),
        projection=projection,
        rows=submitted,
    )


def draw(run: Path, study_uid: str, out: Path) -> dict:
    """Draw this stage from the saved run and return its manifest.

    The one entry a caller uses, so the single command can draw every stage without knowing each
    renderer's argument spelling. `main()` is a thin wrapper over it, so the hand-typed command
    and the joined run draw the same thing from the same code.

    Matplotlib is supplied PER RUN and is never a production dependency, so it is imported after
    every refusal this function can make: `saved_reading` above is then importable and testable in
    the ordinary environment, which is where its must-nots are pinned.
    """
    target = out.resolve()
    if not target.is_relative_to((PROJECT / "data").resolve()):
        raise ArgumentRefusal("out must be under the project's private data directory")
    receipt_path = run / "receipt.json"
    receipt_bytes = receipt_path.read_bytes()
    receipt = json.loads(receipt_bytes)
    studies = [s for s in receipt["studies"] if s["study_uid"] == study_uid]
    if not studies:
        raise ArgumentRefusal("no saved study entry for this study")
    frame = pictures.panels(saved_reading(studies[0]))
    if pictures.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:output")

    import matplotlib.pyplot as plt

    target.mkdir(parents=True, exist_ok=True)
    values = dict(frame.submission_rows or ())
    columns = ["#", "competition column", "code", "reason"]
    widths = [0.05, 0.17, 0.20, 0.58]
    if frame.submission_rows is not None:
        columns.append("submitted value")
        widths = [0.05, 0.15, 0.18, 0.50, 0.12]
    cells = []
    for row in frame.companion:
        cell = [str(row.index), row.column, row.code, fill(row.reason, width=52)]
        if frame.submission_rows is not None:
            cell.append(repr(values[row.column]))
        cells.append(cell)
    if frame.projection is None:
        projection_line = "projection: undeclared"
    else:
        projection_line = (
            f"projection: {frame.projection.value!r}, declared by "
            f"{frame.projection.author} on {frame.projection.declared}"
        )
    if frame.submission_rows is None:
        submission_line = "no submission row was written (submission_rows is None)"
    else:
        submission_line = f"{len(frame.submission_rows)} submission values written"

    figure, axis = plt.subplots(figsize=(13, 7), layout="constrained")
    axis.set_axis_off()
    axis.set_title(
        "THE OUTPUT, as the output stage returned it "
        "— the companion record of the twelve, a frame about pipeline state, never about a knee\n"
        f"stage: {frame.code} — {frame.why}\n"
        f"{projection_line} · {submission_line}",
        fontsize=10,
    )
    # The renderer only ARRANGES. Every cell below is a saved value; none is computed here.
    table = axis.table(
        cellText=cells,
        colLabels=columns,
        colWidths=widths,
        cellLoc="left",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7.5)
    table.scale(1, 1.6)
    figure.savefig(target / "companion.png", dpi=160)
    plt.close(figure)

    manifest = {
        "schema": "output-frames-v1",
        "receipt_sha256": sha256(receipt_bytes).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": {
            "output": sha256(Path(pictures.__file__).read_bytes()).hexdigest()
        },
        "study_uid": study_uid,
        "image": "companion.png",
        "frame_kind": "pipeline",
        "stage_code": frame.code,
        "stage_why": frame.why,
        "projection": None
        if frame.projection is None
        else {
            "value": frame.projection.value,
            "author": frame.projection.author,
            "declared": frame.projection.declared,
        },
        "submission_rows": None
        if frame.submission_rows is None
        else [[column, value] for column, value in frame.submission_rows],
        "rows": [
            {
                "index": row.index,
                "column": row.column,
                "code": row.code,
                "subjects": list(row.subjects),
                "candidates": row.candidates,
            }
            for row in frame.companion
        ],
        "note": (
            "A row carries a number only when the stage saved a submission row for it. An "
            "abstention is never a negative, and no value here is chosen by this renderer."
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
    # ONLY the argument refusals. A saved record that disagrees with the stage's vocabulary is a
    # corruption signal and must propagate, never be dressed as a mistyped flag.
    try:
        draw(args.run, args.study_uid, args.out)
    except ArgumentRefusal as refusal:
        parser.error(str(refusal))
    target = args.out.resolve()
    print(
        json.dumps(
            {
                "image": str(target / "companion.png"),
                "manifest": str(target / "manifest.json"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
