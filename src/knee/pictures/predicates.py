"""Arrange the twelve findings' existing standings as the rows of one table.

Task 4.3 of `openspec/changes/every-stage-renders`: *"the twelve-row table per study, each row
showing its abstention and reason."*

The frame is about **pipeline state**, not study-derived evidence, and task 0.4 requires that to be
said rather than left to be inferred: in this build every row is an abstention, so the table shows
what the pipeline could not reach and never what a knee holds. A row reading
`subject_unconstructed` does not assert that a study has no such relation -- a missing reading is
silence, never a negative (`AGENTS.md` law 3).

Per §13.7 this layer only **arranges** the completed reading's values: each finding's index, its
structural requirement, its named code and its reason, plus the stage's own code and the two
counts it computed. It evaluates no predicate, selects no subject, takes no measurement and makes
no decision. **No row carries a number**, because a confidence is `knee.output`'s lossy projection
of this record and never this stage's output; and no row carries an anatomical name, because the
record it arranges carries none.

The workbench draws the returned frame; Matplotlib is supplied per run and is never imported here.
"""

from __future__ import annotations

from dataclasses import dataclass

from knee.predicates.findings import FindingsReading


@dataclass(frozen=True, slots=True)
class FindingRow:
    """One row of the table: the finding's index, what it required, its code and its reason."""

    index: int
    requirement: str
    code: str
    reason: str


@dataclass(frozen=True, slots=True)
class PredicatesPanels:
    """The findings reading's unchanged values, ready for the workbench to draw.

    `rows` always holds TWELVE entries, in the reading's own order, because the stage always
    returns twelve. A missing row would let a viewer read silence as a negative.
    """

    code: str
    why: str
    rows: tuple[FindingRow, ...]
    series_with_population: int
    series_with_construction: int


def panels(reading: FindingsReading) -> PredicatesPanels:
    """Hand on the twelve standings and the stage's own code, without interpreting any of them.

    **The postcondition is relative to the reading, not an absolute twelve, and CrossHair is why.**
    The first version claimed `len(__return__.rows) == 12`, and the symbolic check refused it with
    a counterexample: `panels(FindingsReading('\\x00', '\\x00\\x00', (), 0, 0))` returns no rows at
    all. This adapter is total over any reading it is handed, so "always twelve" is a promise it
    cannot keep. That promise belongs to `read_findings`, which does hold it
    (`post: len(__return__.findings) == 12`), and to the saved-record reader in
    `workbench.render.predicate_frames`, which refuses a stored record that is not the twelve.
    What the adapter guarantees is the only thing an arranger can: it passes through exactly the
    rows it was given, in their order, unchanged.

    post: len(__return__.rows) == len(reading.findings)
    post: [r.index for r in __return__.rows] == [f.index for f in reading.findings]
    """
    return PredicatesPanels(
        code=reading.code,
        why=reading.why,
        rows=tuple(
            FindingRow(
                index=finding.index,
                requirement=finding.requirement,
                code=finding.code,
                reason=finding.reason,
            )
            for finding in reading.findings
        ),
        series_with_population=reading.series_with_population,
        series_with_construction=reading.series_with_construction,
    )
