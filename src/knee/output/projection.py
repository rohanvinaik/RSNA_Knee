"""THE OUTPUT: where the twelve named decisions meet the competition's foreign schema.

Task 6.8 of `every-stage-renders` (the first increment of 4.2). Three contracts, each from
`specs/abstaining-findings/spec.md` and `specs/route-composition/spec.md`:

  - **The correspondence from index to column is declared here, once, and checked.** The
    predicates stage keys a finding by its index in the object model's table order and writes no
    anatomical word. The competition's columns ARE anatomical words. The join between the two is
    `COLUMN_BY_INDEX`, the one table in the codebase that carries both, and
    `tests/knee/output/test_projection.py` checks it is a bijection onto `knee.study.tables.LABELS`
    so a finding can never be written under the wrong column.
  - **The companion record is written on every run.** Each finding's index, column, code, reason
    and the subjects it read, so the submission is derivable from the record and never the
    reverse (design.md: "a disconnected predicates stage that always returns twelve abstentions
    produces the same final file").
  - **Submission rows are refused while the numeric projection is undeclared.** The founder,
    2026-10-12: *"I don't know, that should resolve experientially, when actually running and
    seeing it in action."* So `Projection` is a value with its author and the date it was
    declared, and `None` is its honest state today: `read_output` returns `projection_undeclared`,
    `submission_rows` refuses, and no number stands in for silence.

This module reads no bar: the projection, when declared, is an ARGUMENT with its provenance, never
a constant chosen here, and never one chosen by reference to a score, a prevalence or a label.
"""

from __future__ import annotations

from dataclasses import dataclass

from knee.absence import absence_code
from knee.predicates.findings import CODES as FINDING_CODES
from knee.study.tables import LABELS
from knee.telemetry import ledger

#: Every code this stage admits.
CODES: tuple[str, ...] = (
    "present",
    "projection_undeclared",
    "predecessor_absent",
    "predecessor_empty",
    "invalid_count",
)

#: The finding's index in the object model's table order → the competition's column. This is the
#: ONE place both vocabularies meet, and the test checks it is a bijection onto `LABELS`.
COLUMN_BY_INDEX: tuple[tuple[int, str], ...] = (
    (0, "Fracture"),
    (1, "Contusion"),
    (2, "Medial OA"),
    (3, "Lateral OA"),
    (4, "PF OA"),
    (5, "Medial Meniscus"),
    (6, "Lateral Meniscus"),
    (7, "ACL"),
    (8, "MCL"),
    (9, "Effusion"),
    (10, "Synovitis"),
    (11, "Baker's"),
)


@dataclass(frozen=True, slots=True)
class Projection:
    """The value written for an abstaining finding, with who declared it and when.

    It exists only once the founder has inspected the named decisions running; until then no
    instance of it exists in the codebase, and `read_output` is handed None.
    """

    value: float
    author: str
    declared: str


@dataclass(frozen=True, slots=True)
class CompanionRow:
    """One finding as the companion record carries it: its index, its column, and its standing."""

    index: int
    column: str
    code: str
    reason: str
    subjects: tuple[int, int]
    candidates: int


@dataclass(frozen=True, slots=True)
class OutputReading:
    """The companion record of the twelve, and the projection's standing.

    `code` is `present` only when a projection is declared and every finding has a row; it is
    `projection_undeclared` when the record is complete and the number is not, which is this
    build's state. `rows` is None whenever no row may be written.
    """

    code: str
    why: str
    companion: tuple[CompanionRow, ...]
    projection: Projection | None
    rows: tuple[tuple[str, float], ...] | None


def output_code(
    findings_returned: bool, finding_count: int, projection_declared: bool
) -> str:
    """Name the stage's standing from three facts the caller established.

    The order is the order of causes: nothing handed over; a record handed over with no rows, or
    with a count that cannot be read; then the projection. `present` needs ALL of a record, the
    twelve rows and a declared projection.

    post: __return__ in CODES
    post: __return__ != "present" or (findings_returned and finding_count > 0 and projection_declared)
    post: __return__ != "projection_undeclared" or (findings_returned and finding_count > 0)
    """
    standing = absence_code(
        construction_built=True,
        predecessor_returned=findings_returned,
        item_count=finding_count,
        item_read=True,
    )
    if standing != "present":
        return standing
    return "present" if projection_declared else "projection_undeclared"


def _whole(value: object) -> int | None:
    """A whole number as an int; None for a bool, a float, a string or anything else."""
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _pair(value: object) -> tuple[int, int] | None:
    """Two whole subject indices as the record carries them, or None for anything else.

    Until task 7.13 anything that was not two came back as (0, 0): a default standing in for a
    reading not made. Now a row whose subjects cannot be read is not a row.
    """
    if not isinstance(value, tuple) or len(value) != 2:
        return None
    first, second = _whole(value[0]), _whole(value[1])
    if first is None or second is None:
        return None
    return first, second


def _row(finding: object, by_index: dict[int, str]) -> CompanionRow | None:
    """One finding as the companion carries it, or None when it does not read as one.

    A row needs a whole index, a code and a reason that are strings, two whole subject indices
    and a whole candidate count. Anything else is not a row: the reader returns None and the
    stage names the record `invalid_count` (task 7.13) instead of raising, as its contract
    promises. The Codex re-review of 2026-12-12 reproduced both a row without a reason and a
    non-numeric index raising out of this stage.
    """
    index = _whole(getattr(finding, "index", None))
    code = getattr(finding, "code", None)
    reason = getattr(finding, "reason", None)
    subjects = _pair(getattr(finding, "subjects", None))
    candidates = _whole(getattr(finding, "candidates", None))
    if index is None or not isinstance(code, str) or not isinstance(reason, str):
        return None
    if subjects is None or candidates is None:
        return None
    return CompanionRow(
        index=index,
        column=by_index.get(index, "unmapped"),
        code=code,
        reason=reason,
        subjects=subjects,
        candidates=candidates,
    )


def read_output(
    findings: object, projection: Projection | None = None
) -> OutputReading:
    """Join the twelve to the competition's columns; refuse the rows while the number is undeclared.

    Total over `findings`: None, a malformed object and a reading with no rows all return a named
    code over an empty companion, and nothing here raises. A record holding a row that does not
    read as one keeps its readable rows in the companion and is named `invalid_count`: the
    companion is never silently shorter than the twelve.

    post: __return__.code in CODES
    post: __return__.rows is None or __return__.code == "present"
    """
    rows = getattr(findings, "findings", None)
    standings = tuple(rows) if isinstance(rows, tuple) else ()
    by_index = {index: column for index, column in COLUMN_BY_INDEX}
    read = tuple(_row(finding, by_index) for finding in standings)
    companion = tuple(row for row in read if row is not None)
    # Complete means THE TWELVE: every declared index exactly once, each under a mapped column
    # with an admitted code. Twelve rows of one finding once passed this check, and a row that
    # did not read as one made the companion shorter instead of the record unreadable (7.13).
    complete = (
        all(row is not None for row in read)
        and sorted(row.index for row in companion)
        == [index for index, _ in COLUMN_BY_INDEX]
        and all(
            row.column != "unmapped" and row.code in FINDING_CODES for row in companion
        )
    )
    if findings is not None:
        # Consumption is recorded only for a record handed over (`specs/route-composition`,
        # task 7.14): None was not produced, and the code below names that silence.
        ledger.record(
            "predicates.consumed_by.output",
            findings=len(companion),
            complete=1 if complete else 0,
        )
    # The count the decision reads: -1 when what was handed over cannot be read as findings at
    # all (no `findings` tuple, or rows that are not the twelve), 0 when a findings tuple was
    # handed over and held nothing, else the twelve. Those are three silences with three
    # remedies, and `output_code` keeps them apart.
    if not isinstance(rows, tuple):
        count = -1
    elif not rows:
        count = 0
    else:
        count = len(companion) if complete else -1
    code = output_code(
        findings_returned=findings is not None,
        finding_count=count,
        projection_declared=projection is not None,
    )
    projected = None
    if code == "present" and projection is not None:
        projected = tuple((row.column, float(projection.value)) for row in companion)
    ledger.record("output.produced", rows=len(projected) if projected else 0)
    why = {
        "present": "every finding has a column and the projection is declared",
        "projection_undeclared": (
            "the companion record is complete; the numeric projection has not been "
            "declared, so no submission row is written"
        ),
        "predecessor_absent": "no findings reading was handed to this stage",
        "predecessor_empty": "a findings reading was handed over and it held no finding",
        "invalid_count": "the findings handed over do not read as the twelve",
    }[code]
    return OutputReading(
        code=code, why=why, companion=companion, projection=projection, rows=projected
    )


def submission_rows(reading: OutputReading, study_uid: str) -> tuple[str, list[str]]:
    """The one CSV row for a study in `LABELS` order, or the named refusal and no row.

    The first value is the refusal code (`written` when a row is returned). A row is returned only
    from a `present` reading, and its columns are the competition's in the competition's own
    order, read from the reading's rows by column name so a reordered table cannot shift a value.
    A reading whose code is outside this stage's vocabulary, or one that says `present` and
    carries no rows, is refused as `invalid_count`: CrossHair found (2026-10-12) that a reading
    carrying the code `written` with no rows was handed back as `written` with no row, which the
    post-condition below forbids, and the refusal code is now always one of `CODES`.

    post: (__return__[0] == "written") == (len(__return__[1]) == 1 + len(LABELS))
    post: __return__[0] == "written" or __return__[0] in CODES
    """
    if reading.code != "present":
        return (reading.code if reading.code in CODES else "invalid_count"), []
    if reading.rows is None:
        return "invalid_count", []
    values = dict(reading.rows)
    if set(values) != set(LABELS):
        return "invalid_count", []
    return "written", [study_uid, *(repr(values[column]) for column in LABELS)]
