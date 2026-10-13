"""Intent tests for the predicates stage, both signs, every call direct by name.

Positive: what each unit must do. Negative: what it must NEVER do. Detective routes tests to a
function by STATIC path, so every call below names the function literally -- a call behind a local
helper is invisible to the tracer and is not a pin (measured on this project: 9 of 13 invisible).

Revised 2026-10-12 with task 6.4: `finding_code` takes the COUNT of constructions of the required
kind in place of a boolean, and `read_findings` reads those constructions from each series'
relations record. Every earlier intent is kept; the calls carry the new argument.
"""

from knee.predicates.findings import (
    CODES,
    EXPLANATIONS,
    REQUIREMENTS,
    SATISFACTIONS,
    Finding,
    FindingsReading,
    finding_code,
    finding_reason,
    read_findings,
)
from knee.relations.shell import KINDS, Interstice
from knee.telemetry import recording

#: Words no stage record, code or picture may carry (`stage-totality`). "interstice" is NOT here:
#: it is the thesis's structural tier, defined by the founder as a RELATIVE role.
ANATOMICAL = (
    "femur",
    "tibia",
    "patella",
    "fibula",
    "bone",
    "cartilage",
    "meniscus",
    "ligament",
    "capsule",
    "synovi",
    "effusion",
    "fracture",
    "contusion",
    "osteoarthritis",
    "marrow",
    "cruciate",
    "bursa",
    "medial",
    "lateral",
)


class _Row:
    """A stand-in for one SeriesRun, carrying only the fields this stage reads."""

    def __init__(
        self,
        ownership_code: str = "",
        relations_code: str = "",
        interstices: tuple = (),
    ) -> None:
        self.ownership = type("O", (), {"code": ownership_code})()
        self.relations = type(
            "R", (), {"code": relations_code, "interstices": interstices}
        )()


def _facing(first: int, second: int, uid: str = "s") -> Interstice:
    return Interstice("facing_pair", first, second, uid, "test")


# ---------------------------------------------------------------- finding_code, positive


def test_a_label_offered_is_refused():
    assert (
        finding_code("population", 1, 0, 0, 0, 5, True, True, True)
        == "prior_outcome_refused"
    )


def test_an_unconstructed_relation_names_the_construction():
    assert (
        finding_code("construction", 2, 0, 0, 0, 5, False, False, False)
        == "subject_unconstructed"
    )


def test_several_constructions_name_the_undeclared_dispatch():
    assert (
        finding_code("construction", 2, 0, 0, 2, 5, False, False, False)
        == "dispatch_undeclared"
    )


def test_a_population_requirement_with_no_extents_names_the_population():
    assert (
        finding_code("population", 1, 0, 0, 0, 0, False, False, False)
        == "subject_population_empty"
    )


def test_a_population_requirement_with_extents_reaches_the_form():
    assert (
        finding_code("population", 1, 0, 0, 0, 3, False, False, False)
        == "form_not_given"
    )


def test_a_constructed_relation_with_one_side_missing_is_unresolved():
    assert (
        finding_code("construction", 2, 7, 0, 1, 3, False, False, False)
        == "subject_unresolved"
    )


def test_two_identical_indices_are_not_a_relation():
    assert (
        finding_code("construction", 2, 7, 7, 1, 3, False, False, False)
        == "subjects_not_distinct"
    )


def test_two_distinct_constructed_subjects_reach_the_form():
    assert (
        finding_code("construction", 2, 3, 7, 1, 3, False, False, False)
        == "form_not_given"
    )


def test_a_given_form_without_a_correspondence_says_so():
    assert (
        finding_code("construction", 2, 3, 7, 1, 3, True, False, False)
        == "correspondence_undeclared"
    )


def test_everything_present_still_takes_no_reading():
    assert (
        finding_code("construction", 2, 3, 7, 1, 3, True, True, False)
        == "reading_not_taken"
    )


def test_an_unreadable_satisfaction_is_an_invalid_request():
    assert (
        finding_code("whatever", 2, 3, 7, 1, 3, True, True, False) == "invalid_request"
    )


def test_a_negative_index_is_an_invalid_request():
    assert (
        finding_code("construction", 2, -1, 7, 1, 3, True, True, False)
        == "invalid_request"
    )


def test_a_negative_candidate_count_is_an_invalid_request():
    assert (
        finding_code("construction", 2, 3, 7, -1, 3, True, True, False)
        == "invalid_request"
    )


def test_an_unsupported_arity_is_an_invalid_request():
    assert (
        finding_code("construction", 3, 3, 7, 1, 3, True, True, False)
        == "invalid_request"
    )


def test_every_code_the_unit_admits_is_reachable():
    reached = {
        finding_code("population", 1, 0, 0, 0, 5, True, True, True),
        finding_code("nonsense", 1, 0, 0, 0, 5, True, True, False),
        finding_code("population", 1, 0, 0, 0, 0, False, False, False),
        finding_code("construction", 2, 0, 0, 0, 5, False, False, False),
        finding_code("construction", 2, 0, 0, 3, 5, False, False, False),
        finding_code("construction", 2, 7, 0, 1, 5, False, False, False),
        finding_code("construction", 2, 7, 7, 1, 5, False, False, False),
        finding_code("construction", 2, 3, 7, 1, 5, False, False, False),
        finding_code("construction", 2, 3, 7, 1, 5, True, False, False),
        finding_code("construction", 2, 3, 7, 1, 5, True, True, False),
    }
    assert reached == set(CODES)


# ---------------------------------------------------------------- finding_code, negative


def test_a_label_is_never_read_whatever_else_is_wrong():
    # MUST NOT: an input that could only move a decision toward a known answer is refused BEFORE
    # anything else is inspected, so no path exists on which it is read and then acted upon.
    for satisfaction in ("population", "construction", "nonsense"):
        for required in (-5, 1, 2, 9):
            assert (
                finding_code(satisfaction, required, -3, -9, -2, -4, True, True, True)
                == "prior_outcome_refused"
            )


def test_a_population_requirement_never_blames_a_construction():
    # MUST NOT: the two have opposite remedies -- "resolve an extent" against "build the relation".
    for population in (0, 1, 50):
        for candidates in (0, 1, 4):
            assert finding_code(
                "population", 1, 0, 0, candidates, population, False, False, False
            ) not in ("subject_unconstructed", "dispatch_undeclared")


def test_a_construction_requirement_never_blames_the_population():
    # MUST NOT: a construction's absence is never reported as an empty population.
    for population in (0, 1, 50):
        assert (
            finding_code("construction", 2, 0, 0, 0, population, False, False, False)
            != "subject_population_empty"
        )


def test_dispatch_is_never_undeclared_with_one_or_no_candidate():
    # MUST NOT: `dispatch_undeclared` names a choice among SEVERAL; with one there is nothing to
    # choose and with none there is nothing to select from.
    for candidates in (0, 1):
        for first, second in ((0, 0), (3, 7), (3, 3)):
            assert (
                finding_code(
                    "construction", 2, first, second, candidates, 5, True, True, False
                )
                != "dispatch_undeclared"
            )


def test_several_candidates_never_name_a_subject():
    # MUST NOT: with several candidates no subject check may run, because reading any one of
    # them would be guessing the rule the founder has not given.
    for first, second in ((0, 0), (3, 7), (3, 3), (7, 0)):
        assert (
            finding_code("construction", 2, first, second, 2, 5, True, True, False)
            == "dispatch_undeclared"
        )


def test_no_reading_is_ever_claimed_without_a_declared_correspondence():
    # MUST NOT: `reading_not_taken` is the only terminal code, and it must never be reached while
    # the form or the correspondence is missing -- that would assert a comparison nobody declared.
    for form in (False, True):
        for declared in (False, True):
            code = finding_code("construction", 2, 3, 7, 1, 3, form, declared, False)
            if not (form and declared):
                assert code != "reading_not_taken"


def test_a_negative_second_index_is_never_admitted():
    # MUST NOT: the second subject slot must be validated exactly like the first.
    assert (
        finding_code("construction", 2, 0, -1, 1, 5, False, False, False)
        == "invalid_request"
    )
    assert (
        finding_code("construction", 2, 4, -1, 1, 5, False, False, False)
        == "invalid_request"
    )


def test_a_negative_population_is_never_admitted():
    # MUST NOT: a count below zero is an argument that cannot be read, and must never be treated
    # as "some extents were resolved" merely because it is not equal to zero.
    assert (
        finding_code("population", 1, 0, 0, 0, -1, False, False, False)
        == "invalid_request"
    )


def test_an_unresolved_first_subject_is_never_passed_over():
    # MUST NOT: a relation needs BOTH sides. An unresolved first subject must be reported even
    # when the second one is resolved -- the asymmetry is a bug, not a convention.
    assert (
        finding_code("construction", 2, 0, 7, 1, 5, False, False, False)
        == "subject_unresolved"
    )


def test_a_resolved_first_subject_is_never_mistaken_for_an_unresolved_one():
    # MUST NOT: index 1 is a resolved extent like any other. Only 0 means "none".
    assert (
        finding_code("construction", 2, 1, 7, 1, 5, False, False, False)
        == "form_not_given"
    )


def test_a_one_subject_requirement_never_demands_a_second():
    # MUST NOT: a requirement naming one subject must never be refused for the absence of a
    # second. Findings 0-1 name one subject, and this is what keeps arity meaningful.
    assert (
        finding_code("construction", 1, 7, 0, 1, 5, False, False, False)
        == "form_not_given"
    )


def test_a_one_subject_requirement_is_never_a_degenerate_pair():
    # MUST NOT: distinctness is only a question where two subjects are required.
    assert (
        finding_code("construction", 1, 5, 5, 1, 5, False, False, False)
        == "form_not_given"
    )


def test_no_code_is_ever_a_number_or_a_probability():
    # MUST NOT: a finding's answer is a named code. A confidence is `knee.output`'s lossy
    # projection of this record, never this unit's output.
    code = finding_code("construction", 2, 3, 7, 1, 3, True, True, False)
    assert isinstance(code, str)
    assert code in CODES
    assert not code.replace(".", "").isdigit()


def test_the_decision_reads_the_relation_and_not_one_subject():
    # MUST NOT: no property of either subject alone can distinguish these three. The subjects are
    # identical in the first two calls and the answers differ on the RELATION; the third differs
    # only in that the two indices are the same extent.
    unconstructed = finding_code("construction", 2, 3, 7, 0, 3, False, False, False)
    constructed = finding_code("construction", 2, 3, 7, 1, 3, False, False, False)
    degenerate = finding_code("construction", 2, 3, 3, 1, 3, False, False, False)
    assert unconstructed == "subject_unconstructed"
    assert constructed == "form_not_given"
    assert degenerate == "subjects_not_distinct"
    assert len({unconstructed, constructed, degenerate}) == 3


# ---------------------------------------------------------------- finding_reason


def test_a_reason_names_the_requirement_and_the_explanation():
    reason = finding_reason("an envelope", "subject_unconstructed")
    assert "an envelope" in reason
    assert EXPLANATIONS["subject_unconstructed"] in reason


def test_an_unknown_code_is_named_as_unknown_not_given_another_codes_words():
    # MUST NOT: a code outside the vocabulary must never silently borrow a real code's sentence.
    reason = finding_reason("an object", "not_a_code")
    assert "an object" in reason
    for explanation in EXPLANATIONS.values():
        assert explanation not in reason


# ---------------------------------------------------------------- read_findings, positive


def test_twelve_findings_whatever_was_handed_over():
    for handed in (None, (), (_Row(),), [_Row("present"), _Row("present")], 17):
        assert len(read_findings(handed).findings) == 12


def test_nothing_handed_over_is_distinguished_from_an_empty_record():
    assert read_findings(None).code == "predecessor_absent"
    assert read_findings(()).code == "predecessor_empty"


def test_series_that_resolved_a_partition_are_counted():
    reading = read_findings(
        (_Row("present"), _Row("predecessor_empty"), _Row("present"))
    )
    assert reading.code == "present"
    assert reading.series_with_population == 2
    assert reading.series_with_construction == 0
    # The record explains itself in the counts it read, in one sentence that never drifts from them.
    assert reading.why == (
        "2 of 3 series resolved a partition; 0 resolved a construction (0 in all); "
        "0 wrote profiles (0 in all)"
    )


def test_the_ledger_records_what_the_stage_read_only_when_series_were_handed_over():
    """Tasks 6.5 and 7.14: the three consumptions are recorded, with the series read and the facts
    counted from them, only when at least one series record was handed over; `predicates.produced`
    on every path. None and an empty tuple hand over no ownership, relations or bundles record to
    consume. The Detective survivors of 2026-10-12 that moved the guard, dropped or renamed a
    record, or altered a count were killable only with the ledger recording."""
    with recording() as run:
        read_findings(None)
        read_findings(())
        read_findings((_Row("present"),))
        read_findings(
            (_Row("present", "present", (_facing(3, 7),)), _Row("predecessor_empty"))
        )
    assert [(event.name, dict(event.counts)) for event in run.events()] == [
        ("predicates.produced", {"findings": 12}),
        ("predicates.produced", {"findings": 12}),
        ("ownership.consumed_by.predicates", {"series": 1, "with_population": 1}),
        ("relations.consumed_by.predicates", {"series": 1, "constructions": 0}),
        ("vectors.consumed_by.predicates", {"series": 1, "profiles": 0}),
        ("predicates.produced", {"findings": 12}),
        ("ownership.consumed_by.predicates", {"series": 2, "with_population": 1}),
        ("relations.consumed_by.predicates", {"series": 2, "constructions": 1}),
        ("vectors.consumed_by.predicates", {"series": 2, "profiles": 0}),
        ("predicates.produced", {"findings": 12}),
    ]


def test_the_two_bone_findings_abstain_differently_from_the_other_ten():
    reading = read_findings((_Row("present"),))
    by_index = {f.index: f for f in reading.findings}
    assert by_index[0].code == "form_not_given"
    assert by_index[1].code == "form_not_given"
    for index in range(2, 12):
        assert by_index[index].code == "subject_unconstructed"
        assert by_index[index].candidates == 0
        assert by_index[index].subjects == (0, 0)


def test_a_study_resolving_nothing_names_the_empty_population():
    reading = read_findings((_Row("predecessor_empty"),))
    by_index = {f.index: f for f in reading.findings}
    assert by_index[0].code == "subject_population_empty"
    assert by_index[2].code == "subject_unconstructed"


def test_one_construction_of_a_kind_supplies_that_kinds_subjects():
    # The construction is READ from the relations record: one facing-pair interstice between
    # extents 3 and 7 reaches findings 2-4 as their subjects and reaches no other finding.
    reading = read_findings(
        (_Row("present", "present", (_facing(3, 7),)), _Row("present"))
    )
    by_index = {f.index: f for f in reading.findings}
    assert reading.series_with_construction == 1
    for index in (2, 3, 4):
        assert by_index[index].code == "form_not_given"
        assert by_index[index].subjects == (3, 7)
        assert by_index[index].candidates == 1
    for index in (5, 6, 7, 8, 9, 10, 11):
        assert by_index[index].code == "subject_unconstructed"
        assert by_index[index].candidates == 0


def test_several_constructions_of_a_kind_abstain_on_dispatch():
    reading = read_findings(
        (
            _Row("present", "present", (_facing(3, 7, "a"),)),
            _Row("present", "present", (_facing(2, 5, "b"),)),
        )
    )
    by_index = {f.index: f for f in reading.findings}
    for index in (2, 3, 4):
        assert by_index[index].code == "dispatch_undeclared"
        assert by_index[index].candidates == 2
        assert by_index[index].subjects == (0, 0)


def test_every_finding_carries_its_requirement_in_its_reason():
    for finding in read_findings((_Row("present"),)).findings:
        assert finding.requirement in finding.reason


def test_every_construction_kind_a_requirement_names_is_one_relations_declares():
    for _index, _requirement, satisfied_by, _subjects, kind in REQUIREMENTS:
        if satisfied_by == "construction":
            assert kind in KINDS
        else:
            assert kind == "object"


# ---------------------------------------------------------------- read_findings, negative


def test_the_stage_never_omits_a_row_for_a_finding_it_could_not_evaluate():
    # MUST NOT: an absent row would let a consumer read silence as a negative (law 3).
    indices = [f.index for f in read_findings(None).findings]
    assert indices == list(range(12))


def test_no_record_field_carries_an_anatomical_name():
    # MUST NOT: `stage-totality` -- "A record schema SHALL NOT contain a field whose values are
    # anatomical names." Checked over the whole returned record and over the declared tables.
    reading = read_findings((_Row("present"),))
    text = " ".join(
        [reading.code, reading.why]
        + [f"{f.requirement} {f.code} {f.reason}" for f in reading.findings]
        + [r[1] for r in REQUIREMENTS]
        + [r[4] for r in REQUIREMENTS]
        + list(EXPLANATIONS.values())
        + list(CODES)
        + list(SATISFACTIONS)
        + list(KINDS)
    ).lower()
    for word in ANATOMICAL:
        assert word not in text


def test_the_stage_never_decides_anything_about_a_knee():
    # MUST NOT: no finding may come back decided while no correspondence is declared.
    for handed in (None, (), (_Row("present"), _Row("present"))):
        for finding in read_findings(handed).findings:
            assert finding.code != "reading_not_taken"


def test_a_declared_correspondence_alone_does_not_decide():
    # MUST NOT: declaring `e` must not by itself produce a decision -- the predicate's FORM is
    # still the founder's to teach, and author/date metadata is not the correspondence itself.
    for finding in read_findings(
        (_Row("present"),), correspondence_declared=True
    ).findings:
        assert finding.code in ("form_not_given", "subject_unconstructed")


def test_a_global_construction_count_never_supplies_a_subject():
    # MUST NOT: a per-study count of series that constructed SOMETHING cannot tell one
    # requirement's construction from another's -- an interstice of a facing pair is not an
    # envelope. A relations code alone, whatever it says, supplies no subject: only an
    # `Interstice` record of the finding's own kind does.
    for relations_code in ("construction_absent", "present", "built_something"):
        reading = read_findings(
            (_Row("present", relations_code), _Row("present", relations_code))
        )
        by_index = {f.index: f for f in reading.findings}
        for finding in reading.findings:
            assert finding.code not in ("subject_unresolved", "subjects_not_distinct")
        for index in range(2, 12):
            assert by_index[index].code == "subject_unconstructed"


def test_a_construction_of_one_kind_never_reaches_a_finding_of_another():
    # MUST NOT: an envelope is not an interstice of a facing pair. One construction of kind
    # `envelope` must leave every facing-pair and content finding unconstructed.
    envelope = Interstice("envelope", 4, 9, "s", "test")
    reading = read_findings((_Row("present", "present", (envelope,)),))
    by_index = {f.index: f for f in reading.findings}
    for index in (2, 3, 4, 5, 6, 7, 8, 10):
        assert by_index[index].code == "subject_unconstructed"
    for index in (9, 11):
        assert by_index[index].code == "form_not_given"
        assert by_index[index].subjects == (4, 9)


def test_a_malformed_construction_is_never_read_as_one():
    # MUST NOT: something in the interstices tuple that is not an `Interstice` record supplies
    # no subject and raises nothing.
    reading = read_findings((_Row("present", "present", ("not a record", 7, None)),))
    for index in range(2, 12):
        assert reading.findings[index].code == "subject_unconstructed"
    assert reading.series_with_construction == 0


def test_the_record_is_frozen():
    # MUST NOT: a consumer must not be able to edit a finding's standing after the fact.
    reading = read_findings((_Row("present"),))
    assert isinstance(reading, FindingsReading)
    assert isinstance(reading.findings[0], Finding)
    for target, field in ((reading, "code"), (reading.findings[0], "code")):
        try:
            setattr(target, field, "tampered")
        except (AttributeError, TypeError):
            continue
        raise AssertionError("a finding's standing must not be mutable")


def test_the_requirement_table_is_the_object_models_twelve_in_order():
    assert len(REQUIREMENTS) == 12
    assert [r[0] for r in REQUIREMENTS] == list(range(12))
    for _index, _requirement, satisfied_by, subjects_required, _kind in REQUIREMENTS:
        assert satisfied_by in SATISFACTIONS
        assert subjects_required in (1, 2)
