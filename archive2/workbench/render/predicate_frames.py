"""Draw the twelve-row predicate table from one saved production study record.

Task 4.3 of `openspec/changes/every-stage-renders`: *"the twelve-row table per study, each row
showing its abstention and reason."*

The frame is about **pipeline state**. In this build every row is an abstention, so the table
shows what the pipeline could not reach and never what a knee holds: a row reading
`subject_unconstructed` does not assert that a study has no such relation. A missing reading is
silence, never a negative.

This workbench arranges values through `knee.pictures.predicates`. It evaluates no predicate,
selects no subject, takes no measurement and writes no number against any finding -- a confidence
is `knee.output`'s lossy projection of this record, and that projection has not been declared.
"""

import argparse
import json
from hashlib import sha256
from pathlib import Path
from textwrap import fill

from knee.pictures import predicates
from knee.predicates.findings import CODES, REQUIREMENTS, Finding, FindingsReading


def saved_reading(study: dict) -> FindingsReading:
    """Reconstitute the stage's returned reading from one saved study entry, without deciding.

    Every saved field is checked against the vocabulary the stage owns rather than trusted: a
    code outside `CODES`, a row count that is not twelve, or an index set that is not 0..11 means
    the record and this renderer disagree, and that is reported rather than drawn.
    """
    if "findings" not in study:
        raise ValueError("missing_saved_findings")
    saved = study["findings"]
    rows = saved["findings"]
    if len(rows) != len(REQUIREMENTS):
        raise ValueError("saved_findings_count_mismatch")
    if [row["index"] for row in rows] != [r[0] for r in REQUIREMENTS]:
        raise ValueError("saved_findings_index_mismatch")
    for row in rows:
        if row["code"] not in CODES:
            raise ValueError(f"saved_finding_code_unknown:{row['code']}")
        if row["requirement"] not in row["reason"]:
            raise ValueError(f"saved_finding_reason_mismatch:{row['index']}")
    return FindingsReading(
        code=saved["code"],
        why=saved["why"],
        findings=tuple(
            Finding(
                index=row["index"],
                requirement=row["requirement"],
                code=row["code"],
                reason=row["reason"],
            )
            for row in rows
        ),
        series_with_population=saved["series_with_population"],
        series_with_construction=saved["series_with_construction"],
    )


def draw(run: Path, study_uid: str, out: Path) -> dict:
    """Draw this stage from the saved run and return its manifest.

    The one entry a caller uses, so the single command can draw every stage without knowing each
    renderer's argument spelling. `main()` is a thin wrapper over it, so the hand-typed command
    and the joined run draw the same thing from the same code.

    Matplotlib is supplied PER RUN and is never a production dependency, so it is imported here
    rather than at module scope: `saved_reading` above is then importable and testable in the
    ordinary environment, which is where its must-nots are pinned.
    """
    import matplotlib.pyplot as plt

    data_root = Path(__file__).resolve().parents[2] / "data"
    output = out.resolve()
    if not output.is_relative_to(data_root.resolve()):
        raise ValueError("out must be under the project's private data directory")
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    studies = [s for s in receipt["studies"] if s["study_uid"] == study_uid]
    if not studies:
        raise ValueError("no saved study entry for this study")
    frame = predicates.panels(saved_reading(studies[0]))
    output.mkdir(parents=True, exist_ok=True)

    figure, axis = plt.subplots(figsize=(13, 6.5), layout="constrained")
    axis.set_axis_off()
    axis.set_title(
        "THE TWELVE, as the predicates stage returned them "
        "— a frame about pipeline state, never about a knee\n"
        f"stage: {frame.code} — {frame.why}",
        fontsize=10,
    )
    # The renderer only ARRANGES. Every cell below is a saved value; none is computed here.
    table = axis.table(
        cellText=[
            [
                str(row.index),
                fill(row.requirement, width=30),
                row.code,
                fill(row.reason, width=56),
            ]
            for row in frame.rows
        ],
        colLabels=["#", "requirement its subject must satisfy", "code", "reason"],
        colWidths=[0.05, 0.25, 0.20, 0.50],
        cellLoc="left",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7.5)
    table.scale(1, 1.6)
    figure.savefig(output / "findings.png", dpi=160)
    plt.close(figure)

    if predicates.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:predicates")
    manifest = {
        "schema": "predicate-frames-v1",
        "receipt_sha256": sha256(receipt_path.read_bytes()).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": {
            "predicates": sha256(Path(predicates.__file__).read_bytes()).hexdigest()
        },
        "study_uid": study_uid,
        "image": "findings.png",
        "frame_kind": "pipeline",
        "stage_code": frame.code,
        "series_with_population": frame.series_with_population,
        "series_with_construction": frame.series_with_construction,
        "rows": [
            {"index": r.index, "requirement": r.requirement, "code": r.code}
            for r in frame.rows
        ],
        "note": (
            "Every row is an abstention. No row carries a number: the submission's numeric "
            "projection has not been declared, and an abstention is never a negative."
        ),
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--study-uid", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        draw(args.run, args.study_uid, args.out)
    except ValueError as refusal:
        parser.error(str(refusal))
    output = args.out.resolve()
    print(
        json.dumps(
            {
                "image": str(output / "findings.png"),
                "manifest": str(output / "manifest.json"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
