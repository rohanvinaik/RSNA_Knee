"""The output stage, both signs: the declared correspondence, the companion, the refused rows."""

from knee.output.projection import (
    CODES,
    COLUMN_BY_INDEX,
    OutputReading,
    Projection,
    output_code,
    read_output,
    submission_rows,
)
from knee.predicates.findings import REQUIREMENTS, read_findings
from knee.study.tables import LABELS
from knee.telemetry import recording


class _Row:
    def __init__(self, ownership_code: str = "present") -> None:
        self.ownership = type("O", (), {"code": ownership_code})()
        self.relations = type(
            "R", (), {"code": "construction_absent", "interstices": ()}
        )()


# ---------------------------------------------------------------- the correspondence


def test_the_index_to_column_table_is_a_bijection_onto_the_competitions_labels():
    indices = [index for index, _ in COLUMN_BY_INDEX]
    columns = [column for _, column in COLUMN_BY_INDEX]
    assert indices == [r[0] for r in REQUIREMENTS]
    assert sorted(columns) == sorted(LABELS)
    assert len(set(columns)) == len(LABELS)


def test_the_two_object_findings_map_to_the_two_bone_columns():
    """The object model's table order puts the single-object findings first; the competition's
    column order puts them last. The declared table carries that join, and this pins it."""
    by_index = dict(COLUMN_BY_INDEX)
    assert by_index[0] == "Fracture"
    assert by_index[1] == "Contusion"
    assert by_index[7] == "ACL"
    assert by_index[11] == "Baker's"


# ---------------------------------------------------------------- output_code


def test_output_code_names_each_case_it_can_reach():
    assert output_code(False, 0, False) == "predecessor_absent"
    assert output_code(True, 0, False) == "predecessor_empty"
    assert output_code(True, -1, True) == "invalid_count"
    assert output_code(True, 12, False) == "projection_undeclared"
    assert output_code(True, 12, True) == "present"


def test_output_code_never_says_present_without_a_declared_projection():
    for returned in (False, True):
        for count in (-1, 0, 12):
            assert output_code(returned, count, False) != "present"


def test_output_code_never_blames_the_projection_for_a_missing_record():
    for count in (-1, 0):
        for declared in (False, True):
            assert output_code(True, count, declared) != "projection_undeclared"
    assert output_code(False, 12, False) != "projection_undeclared"


def test_every_code_the_stage_admits_is_reachable():
    reached = {
        output_code(False, 0, False),
        output_code(True, 0, False),
        output_code(True, -1, False),
        output_code(True, 12, False),
        output_code(True, 12, True),
    }
    assert reached == set(CODES)


# ---------------------------------------------------------------- read_output, positive


def test_an_undeclared_projection_yields_a_complete_companion_and_no_rows():
    reading = read_output(read_findings((_Row(),)))
    assert reading.code == "projection_undeclared"
    assert reading.rows is None
    assert len(reading.companion) == 12
    assert [row.column for row in reading.companion] == [c for _, c in COLUMN_BY_INDEX]
    assert all(row.code != "reading_not_taken" for row in reading.companion)


def test_a_declared_projection_writes_one_value_per_column():
    projection = Projection(0.5, "a test, not the founder", "2026-10-12")
    reading = read_output(read_findings((_Row(),)), projection)
    assert reading.code == "present"
    assert reading.rows is not None
    assert dict(reading.rows) == {column: 0.5 for column in LABELS}


def test_submission_rows_are_in_the_competitions_own_order():
    projection = Projection(0.25, "a test, not the founder", "2026-10-12")
    code, row = submission_rows(
        read_output(read_findings((_Row(),)), projection), "uid"
    )
    assert code == "written"
    assert row == ["uid", *(["0.25"] * len(LABELS))]


def test_nothing_handed_over_is_distinguished_from_an_empty_record():
    assert read_output(None).code == "predecessor_absent"
    empty = type("Empty", (), {"findings": ()})()
    assert read_output(empty).code == "predecessor_empty"
    # A record of the wrong shape -- here an output reading handed in as findings -- holds no
    # findings tuple at all, and that is an argument that cannot be read, never an empty one.
    wrong = OutputReading("x", "y", (), None, None)
    assert read_output(wrong).code == "invalid_count"
    # Each silence explains itself: a code never comes back over an empty sentence.
    for reading in (read_output(None), read_output(empty), read_output(wrong)):
        assert reading.why, reading.code


def test_a_declared_value_is_written_as_a_decimal_whatever_number_declared_it():
    # The competition's columns carry decimals. A projection declared as a whole number is still
    # written as one, so no row reads "1" where every other reads "0.25".
    whole = Projection(1, "a test, not the founder", "2026-10-12")
    reading = read_output(read_findings((_Row(),)), whole)
    assert reading.rows is not None
    assert all(type(value) is float for _, value in reading.rows)
    assert submission_rows(reading, "uid")[1][1:] == ["1.0"] * len(LABELS)


def test_the_ledger_records_a_consumption_only_for_a_record_handed_over():
    """Tasks 6.5 and 7.14: `predicates.consumed_by.output` is recorded only when a findings record
    was handed over, with the rows read and whether they were the twelve, and `output.produced`
    on every path with the rows written. None was not produced, so nothing is consumed; a record
    of the wrong type (the twelve in a list) is read as nothing. The Detective survivors of
    2026-10-12 that moved the guard, dropped or renamed a record, or altered a count were
    killable only with the ledger recording, which refuses a count that is not a whole number."""
    good = read_findings((_Row(),))
    projection = Projection(0.5, "a test, not the founder", "2026-10-12")

    class NoReason:
        index, code, subjects, candidates = 0, "form_not_given", (0, 0), 0

    short = type("F", (), {"findings": (NoReason(), *good.findings[1:])})()
    listed = type("F", (), {"findings": list(good.findings)})()
    with recording() as run:
        read_output(None)
        read_output(good)
        read_output(good, projection)
        read_output(short)
        read_output(listed)
    assert [(event.name, dict(event.counts)) for event in run.events()] == [
        ("output.produced", {"rows": 0}),
        ("predicates.consumed_by.output", {"findings": 12, "complete": 1}),
        ("output.produced", {"rows": 0}),
        ("predicates.consumed_by.output", {"findings": 12, "complete": 1}),
        ("output.produced", {"rows": 12}),
        ("predicates.consumed_by.output", {"findings": 11, "complete": 0}),
        ("output.produced", {"rows": 0}),
        ("predicates.consumed_by.output", {"findings": 0, "complete": 0}),
        ("output.produced", {"rows": 0}),
    ]


# ---------------------------------------------------------------- read_output, negative


def test_no_row_is_ever_written_while_the_projection_is_undeclared():
    # MUST NOT: a number in that column cannot carry silence, so none is written without the
    # founder's declared value -- "that should resolve experientially".
    for handed in (None, read_findings((_Row(),)), read_findings(None)):
        reading = read_output(handed)
        assert reading.rows is None
        assert submission_rows(reading, "uid") == (reading.code, [])


def test_a_submission_without_its_companion_is_refused():
    # MUST NOT: a present reading whose rows do not cover the competition's columns is refused
    # by name rather than written short.
    partial = OutputReading("present", "w", (), None, (("ACL", 0.5),))
    assert submission_rows(partial, "uid") == ("invalid_count", [])


def test_a_refusal_is_always_a_named_code_of_this_stage():
    # MUST NOT: hand back a word outside the stage's vocabulary as the refusal, least of all
    # `written` with no row. CrossHair's counterexample, 2026-10-12: a reading carrying the code
    # `written` and no rows came back as ("written", []), which the post-condition forbids.
    for odd in (
        OutputReading("written", "", (), Projection(0.0, "", ""), None),
        OutputReading("anything", "", (), None, None),
        OutputReading("present", "w", (), None, None),
    ):
        code, row = submission_rows(odd, "uid")
        assert code == "invalid_count", odd.code
        assert row == []
    for silence in ("projection_undeclared", "predecessor_absent", "predecessor_empty"):
        assert submission_rows(OutputReading(silence, "", (), None, None), "uid") == (
            silence,
            [],
        )


def test_a_malformed_findings_record_is_named_not_projected():
    class Odd:
        findings = ("not", "findings")

    # MUST NOT: rows that are not the twelve are never projected, whatever projection is
    # declared; they are named as unreadable.
    reading = read_output(Odd(), Projection(0.5, "test", "2026-10-12"))
    assert reading.code == "invalid_count"
    assert reading.rows is None


def test_the_companion_carries_the_subjects_the_predicates_read():
    reading = read_output(read_findings((_Row(),)))
    for row in reading.companion:
        assert row.subjects == (0, 0)
        assert row.candidates == 0


def test_it_never_raises_however_malformed_the_argument():
    for argument in (object(), 0, "", [], {"findings": 3}):
        assert read_output(argument).code in CODES


def test_twelve_rows_of_one_finding_are_not_the_twelve():
    # MUST NOT: completeness is every declared index exactly once -- never twelve rows of one
    # finding under one column, never eleven, never thirteen. Codex re-review 2026-10-12 found
    # twelve copies of finding zero accepted as a complete companion (task 7.13).
    twelve = read_findings((_Row(),)).findings
    projection = Projection(0.5, "a test, not the founder", "2026-10-12")
    for rows in (tuple(twelve[0] for _ in twelve), twelve[:11], (*twelve, twelve[3])):
        reading = read_output(type("F", (), {"findings": rows})(), projection)
        assert reading.code == "invalid_count", len(rows)
        assert reading.rows is None
    assert (
        read_output(type("F", (), {"findings": twelve})(), projection).code == "present"
    )


def test_a_row_that_does_not_read_as_one_is_named_never_raised():
    # MUST NOT: raise on a row without a reason, with a non-numeric or bool index, or with
    # subjects that are not two whole numbers. The contract says nothing here raises; the
    # readable rows are kept and the record is named unreadable, never shortened (task 7.13).
    good = read_findings((_Row(),)).findings
    projection = Projection(0.5, "a test, not the founder", "2026-10-12")

    class NoReason:
        index, code, subjects, candidates = 0, "form_not_given", (0, 0), 0

    class TextIndex:
        index, code, reason = "zero", "form_not_given", "a reason"
        subjects, candidates = (0, 0), 0

    class BoolIndex:
        index, code, reason = True, "form_not_given", "a reason"
        subjects, candidates = (0, 0), 0

    class OddSubjects:
        index, code, reason = 0, "form_not_given", "a reason"
        subjects, candidates = ("left", "right"), 0

    for odd in (NoReason(), TextIndex(), BoolIndex(), OddSubjects()):
        handed = type("F", (), {"findings": (odd, *good[1:])})()
        reading = read_output(handed, projection)
        assert reading.code == "invalid_count", type(odd).__name__
        assert reading.rows is None
        assert len(reading.companion) == 11


def test_an_unreadable_row_beside_the_twelve_never_makes_the_record_complete():
    # MUST NOT: the twelve readable rows plus one that does not read as one is not the twelve.
    # The companion keeps the twelve and the record is named unreadable (task 7.13); a reader
    # that only counted the readable rows would call this complete and project it.
    twelve = read_findings((_Row(),)).findings
    projection = Projection(0.5, "a test, not the founder", "2026-10-12")

    class NoReason:
        index, code, subjects, candidates = 0, "form_not_given", (0, 0), 0

    reading = read_output(
        type("F", (), {"findings": (*twelve, NoReason())})(), projection
    )
    assert reading.code == "invalid_count"
    assert reading.rows is None
    assert len(reading.companion) == 12


def test_a_code_outside_the_predicates_vocabulary_is_never_written_under_a_column():
    # MUST NOT: a row whose code is not one the predicates stage admits -- a verdict from nowhere
    # -- reads as a row, is kept in the companion under its index, and is never one of the
    # twelve: the record is named unreadable and nothing is projected, whatever is declared.
    twelve = read_findings((_Row(),)).findings
    projection = Projection(0.5, "a test, not the founder", "2026-10-12")

    class Decided:
        index, code, reason = 0, "positive", "a verdict from nowhere"
        subjects, candidates = (0, 0), 0

    reading = read_output(
        type("F", (), {"findings": (Decided(), *twelve[1:])})(), projection
    )
    assert reading.code == "invalid_count"
    assert reading.rows is None
    assert len(reading.companion) == 12
    assert reading.companion[0].code == "positive"
