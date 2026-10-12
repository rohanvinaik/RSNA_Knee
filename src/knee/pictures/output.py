"""What THE OUTPUT resolved, drawn: the companion record of the twelve and the projection's standing.

Task 6.9 of `openspec/changes/every-stage-renders`, drawing task 4.2's companion record. The frame is
about **pipeline state**, not study-derived evidence: while the numeric projection is undeclared the
stage writes no submission row, so the table shows the twelve findings joined to the competition's
columns with each finding's own code and reason, and it never shows what a knee holds. A missing
reading is silence, never a negative (`AGENTS.md` law 3).

Per §13.7 this layer only **arranges** the completed reading's values: the stage's code and reason,
the twelve companion rows exactly as the stage returned them, the projection (None until declared)
and the submission rows (None while no row may be written). It joins nothing, evaluates no
predicate, takes no measurement and decides nothing. The index-to-column correspondence is
`knee.output.projection.COLUMN_BY_INDEX`, and this layer reads the column from the row it is handed.

The workbench draws the returned frame; Matplotlib is supplied per run and is never imported here.
"""

from __future__ import annotations

from dataclasses import dataclass

from knee.output.projection import CompanionRow, OutputReading, Projection


@dataclass(frozen=True, slots=True)
class OutputPanels:
    """The output reading's unchanged values, ready for the workbench to draw.

    code, why: the stage's own standing and reason. companion: the rows exactly as the stage returned
    them, in its order. projection: the declared value with its author and date, or None while it is
    undeclared. submission_rows: the (column, value) pairs the stage wrote, or None when it wrote no
    row, which is a refusal and never a row of zeros.
    """

    code: str
    why: str
    companion: tuple[CompanionRow, ...]
    projection: Projection | None
    submission_rows: tuple[tuple[str, float], ...] | None


def panels(reading: OutputReading) -> OutputPanels:
    """Hand on the stage's code, reason, companion rows, projection and submission rows unchanged."""
    return OutputPanels(
        code=reading.code,
        why=reading.why,
        companion=reading.companion,
        projection=reading.projection,
        submission_rows=reading.rows,
    )
