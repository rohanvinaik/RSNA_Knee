"""Intent tests for the predicates stage, both signs, every call direct by name.

Positive: what each unit must do. Negative: what it must NEVER do. Detective routes tests to a
function by STATIC path, so every call below names the function literally -- a call behind a local
helper is invisible to the tracer and is not a pin (measured on this project: 9 of 13 invisible).
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
    """A stand-in for one SeriesRun, carrying only the two fields this stage reads."""

    def __init__(self, ownership_code: str = "", relations_code: str = "") -> None:
        self.ownership = type("O", (), {"code": ownership_code})()
        self.relations = type("R", (), {"code": relations_code})()


# ---------------------------------------------------------------- finding_code, positive


def test_a_label_offered_is_refused():
    assert (
        finding_code("population", 1, 0, 0, False, 5, True, True, True)
        == "prior_outcome_refused"
    )


def test_an_unconstructed_relation_names_the_construction():
    assert (
        finding_code("construction", 2, 0, 0, False, 5, False, False, False)
        == "subject_unconstructed"
    )


def test_a_population_requirement_with_no_extents_names_the_population():
    assert (
        finding_code("population", 1, 0, 0, False, 0, False, False, False)
        == "subject_population_empty"
    )


def test_a_population_requirement_with_extents_reaches_the_form():
    assert (
        finding_code("population", 1, 0, 0, False, 3, False, False, False)
        == "form_not_given"
    )


def test_a_constructed_relation_with_one_side_missing_is_unresolved():
    assert (
        finding_code("construction", 2, 7, 0, True, 3, False, False, False)
        == "subject_unresolved"
    )


def test_two_identical_indices_are_not_a_relation():
    assert (
        finding_code("construction", 2, 7, 7, True, 3, False, False, False)
        == "subjects_not_distinct"
    )


def test_two_distinct_constructed_subjects_reach_the_form():
    assert (
        finding_code("construction", 2, 3, 7, True, 3, False, False, False)
        == "form_not_given"
    )


def test_a_given_form_without_a_correspondence_says_so():
    assert (
        finding_code("construction", 2, 3, 7, True, 3, True, False, False)
        == "correspondence_undeclared"
    )


def test_everything_present_still_takes_no_reading():
    assert (
        finding_code("construction", 2, 3, 7, True, 3, True, True, False)
        == "reading_not_taken"
    )


def test_an_unreadable_satisfaction_is_an_invalid_request():
    assert (
        finding_code("whatever", 2, 3, 7, True, 3, True, True, False)
        == "invalid_request"
    )


def test_a_negative_index_is_an_invalid_request():
    assert (
        finding_code("construction", 2, -1, 7, True, 3, True, True, False)
        == "invalid_request"
    )


def test_an_unsupported_arity_is_an_invalid_request():
    assert (
        finding_code("construction", 3, 3, 7, True, 3, True, True, False)
        == "invalid_request"
    )


def test_every_code_the_unit_admits_is_reachable():
    reached = {
        finding_code("population", 1, 0, 0, False, 5, True, True, True),
        finding_code("nonsense", 1, 0, 0, False, 5, True, True, False),
        finding_code("population", 1, 0, 0, False, 0, False, False, False),
        finding_code("construction", 2, 0, 0, False, 5, False, False, False),
        finding_code("construction", 2, 7, 0, True, 5, False, False, False),
        finding_code("construction", 2, 7, 7, True, 5, False, False, False),
        finding_code("construction", 2, 3, 7, True, 5, False, False, False),
        finding_code("construction", 2, 3, 7, True, 5, True, False, False),
        finding_code("construction", 2, 3, 7, True, 5, True, True, False),
    }
    assert reached == set(CODES)


# ---------------------------------------------------------------- finding_code, negative


def test_a_label_is_never_read_whatever_else_is_wrong():
    # MUST NOT: an input that could only move a decision toward a known answer is refused BEFORE
    # anything else is inspected, so no path exists on which it is read and then acted upon.
    for satisfaction in ("population", "construction", "nonsense"):
        for required in (-5, 1, 2, 9):
            assert (
                finding_code(satisfaction, required, -3, -9, True, -4, True, True, True)
                == "prior_outcome_refused"
            )


def test_a_population_requirement_never_blames_a_construction():
    # MUST NOT: the two have opposite remedies -- "resolve an extent" against "build the relation".
    for population in (0, 1, 50):
        assert (
            finding_code("population", 1, 0, 0, False, population, False, False, False)
            != "subject_unconstructed"
        )


def test_a_construction_requirement_never_blames_the_population():
    # MUST NOT: a construction's absence is never reported as an empty population.
    for population in (0, 1, 50):
        assert (
            finding_code(
                "construction", 2, 0, 0, False, population, False, False, False
            )
            != "subject_population_empty"
        )


def test_no_reading_is_ever_claimed_without_a_declared_correspondence():
    # MUST NOT: `reading_not_taken` is the only terminal code, and it must never be reached while
    # the form or the correspondence is missing -- that would assert a comparison nobody declared.
    for form in (False, True):
        for declared in (False, True):
            code = finding_code("construction", 2, 3, 7, True, 3, form, declared, False)
            if not (form and declared):
                assert code != "reading_not_taken"


def test_a_negative_second_index_is_never_admitted():
    # MUST NOT: the second subject slot must be validated exactly like the first. Letting it
    # through would reach the relation checks with an index that is not an index.
    assert (
        finding_code("construction", 2, 0, -1, True, 5, False, False, False)
        == "invalid_request"
    )
    assert (
        finding_code("construction", 2, 4, -1, True, 5, False, False, False)
        == "invalid_request"
    )


def test_a_negative_population_is_never_admitted():
    # MUST NOT: a count below zero is an argument that cannot be read, and must never be treated
    # as "some extents were resolved" merely because it is not equal to zero.
    assert (
        finding_code("population", 1, 0, 0, False, -1, False, False, False)
        == "invalid_request"
    )


def test_an_unresolved_first_subject_is_never_passed_over():
    # MUST NOT: a relation needs BOTH sides. An unresolved first subject must be reported even
    # when the second one is resolved -- the asymmetry is a bug, not a convention.
    assert (
        finding_code("construction", 2, 0, 7, True, 5, False, False, False)
        == "subject_unresolved"
    )


def test_a_resolved_first_subject_is_never_mistaken_for_an_unresolved_one():
    # MUST NOT: index 1 is a resolved extent like any other. Only 0 means "none".
    assert (
        finding_code("construction", 2, 1, 7, True, 5, False, False, False)
        == "form_not_given"
    )


def test_a_one_subject_requirement_never_demands_a_second():
    # MUST NOT: a requirement naming one subject must never be refused for the absence of a
    # second. Findings 0-1 name one subject, and this is what keeps arity meaningful.
    assert (
        finding_code("construction", 1, 7, 0, True, 5, False, False, False)
        == "form_not_given"
    )


def test_a_one_subject_requirement_is_never_a_degenerate_pair():
    # MUST NOT: distinctness is only a question where two subjects are required. One subject
    # repeated in both slots is not a relation between one extent and itself.
    assert (
        finding_code("construction", 1, 5, 5, True, 5, False, False, False)
        == "form_not_given"
    )


def test_no_code_is_ever_a_number_or_a_probability():
    # MUST NOT: a finding's answer is a named code. A confidence is `knee.output`'s lossy
    # projection of this record, never this unit's output.
    code = finding_code("construction", 2, 3, 7, True, 3, True, True, False)
    assert isinstance(code, str)
    assert code in CODES
    assert not code.replace(".", "").isdigit()


def test_the_decision_reads_the_relation_and_not_one_subject():
    # MUST NOT: no property of either subject alone can distinguish these three. The subjects are
    # identical in the first two calls and the answers differ on the RELATION; the third differs
    # only in that the two indices are the same extent.
    unconstructed = finding_code("construction", 2, 3, 7, False, 3, False, False, False)
    constructed = finding_code("construction", 2, 3, 7, True, 3, False, False, False)
    degenerate = finding_code("construction", 2, 3, 3, True, 3, False, False, False)
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


def test_the_two_bone_findings_abstain_differently_from_the_other_ten():
    reading = read_findings((_Row("present"),))
    by_index = {f.index: f for f in reading.findings}
    assert by_index[0].code == "form_not_given"
    assert by_index[1].code == "form_not_given"
    for index in range(2, 12):
        assert by_index[index].code == "subject_unconstructed"


def test_a_study_resolving_nothing_names_the_empty_population():
    reading = read_findings((_Row("predecessor_empty"),))
    by_index = {f.index: f for f in reading.findings}
    assert by_index[0].code == "subject_population_empty"
    assert by_index[2].code == "subject_unconstructed"


def test_every_finding_carries_its_requirement_in_its_reason():
    for finding in read_findings((_Row("present"),)).findings:
        assert finding.requirement in finding.reason


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
        + list(EXPLANATIONS.values())
        + list(CODES)
        + list(SATISFACTIONS)
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
    # envelope. Until relations supplies a PER-FINDING construction fact, no finding may come
    # back claiming a subject it was never given: `subject_unresolved` would be the wrong
    # reason, and the 0,0 behind it would be a substituted zero standing in for a reading
    # nobody took, which `stage-totality` forbids. Obligation recorded on task 1.3a.
    for relations_code in ("construction_absent", "present", "built_something"):
        reading = read_findings(
            (_Row("present", relations_code), _Row("present", relations_code))
        )
        by_index = {f.index: f for f in reading.findings}
        for finding in reading.findings:
            assert finding.code not in ("subject_unresolved", "subjects_not_distinct")
        for index in range(2, 12):
            assert by_index[index].code == "subject_unconstructed"


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


def test_the_requirement_table_is_the_competitions_twelve_in_order():
    assert len(REQUIREMENTS) == 12
    assert [r[0] for r in REQUIREMENTS] == list(range(12))
    for _index, _requirement, satisfied_by, subjects_required in REQUIREMENTS:
        assert satisfied_by in SATISFACTIONS
        assert subjects_required in (1, 2)
