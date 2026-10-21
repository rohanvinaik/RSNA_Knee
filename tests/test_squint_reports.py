"""Direct pins for independent report calls and source-enforced case admission.

Every pure decision helper is pinned on both signs of its intent. The reports
below are invented fixtures; nothing here reads or classifies real report text.
"""

from __future__ import annotations

import copy
import csv
import json
from pathlib import Path

import pytest

from knee.diagnosis.squint_reports import (
    ReportCallError,
    admission_call_code,
    admit_report_cases,
    assertion_digit_code,
    digit_status,
    export_report_batch,
    finding_admission_code,
    group_digits_code,
    import_report_calls,
    memory_question_code,
    profile_status,
    read_batch_reports,
    read_reports,
    repeat_code,
    report_sha256,
    revision_code,
    scope_code,
    sentence_status,
    source_independence_code,
    subject_code,
    validate_report_calls,
)
from knee.study.tables import LABELS, TRAIN_COLUMNS

UID_A = "1.2.826.0001"
UID_B = "1.2.826.0002"
SENT_PRESENT = "Reader fixture sentence one affirms the first condition."
SENT_ABSENT = "Reader fixture sentence two states the second condition is absent."
SENT_UNCERTAIN = "Reader fixture sentence three is equivocal about the third condition."
REPORT_A = (
    f"{SENT_PRESENT} {SENT_ABSENT}\n{SENT_UNCERTAIN}\nA wrapped\nsentence stays whole."
)
REPORT_B = "Another invented report with a single sentence."


def _call(report: str = REPORT_A, **override: object) -> dict:
    record: dict = {
        "study_uid": UID_A,
        "question": "ACL",
        "digit": 1,
        "assertion": "present",
        "sentence": SENT_PRESENT,
        "subject": "acl",
        "scope": "study_condition",
        "source": "report:train.csv",
        "report_sha": report_sha256(report),
        "reader": "claude-reader-1",
    }
    record.update(override)
    return record


def _validate(*records: dict, reports: dict[str, str] | None = None) -> list:
    return validate_report_calls(
        list(records),
        reports if reports is not None else {UID_A: REPORT_A, UID_B: REPORT_B},
    )


def _profile(subject: str = "acl", banks: dict | None = None, **source: object) -> dict:
    return {
        "schema": "knee.squint-profile/v1",
        "subject": subject,
        "banks": banks if banks is not None else {"sag/t2/bright/s1": [2, 0, 3]},
        "source": {"study_uid": UID_A, **source},
    }


def _finding(subject: str = "acl", uid: str = UID_A, **override: object) -> dict:
    finding: dict = {
        "study_uid": uid,
        "subject": subject,
        "status": "located",
        "profile": _profile(subject),
        "regions": {"sag": [1, 2, 3, 4]},
    }
    finding.update(override)
    return finding


def _existing_case() -> dict:
    return {
        "case_id": "case-existing",
        "study_uid": "1.2.826.0099",
        "subject": "acl",
        "condition_calls": {"ACL": 1},
        "profile": _profile("acl", study_uid="1.2.826.0099"),
        "regions": {},
        "full_profile": {"banks": {"x": [1, 1, 1]}},
        "full_source": {"status": "paired"},
        "teaching_source": "labels-sha256:abc",
    }


def _memory(**extra: object) -> dict:
    memory: dict = {
        "schema": "knee.squint-memory/v1",
        "revision": "rev-1",
        "cases": [_existing_case()],
        "arrays": object(),
    }
    memory.update(extra)
    return memory


# --- pure helpers -------------------------------------------------------------


@pytest.mark.parametrize(
    ("digit", "expected"),
    [
        (1, "positive"),
        (-1, "negative"),
        (0, "abstention"),
        (True, "invalid_digit"),
        (1.0, "invalid_digit"),
        (2, "invalid_digit"),
        ("1", "invalid_digit"),
        (None, "invalid_digit"),
    ],
)
def test_digit_status_names_both_signs_and_refuses_non_digits(digit, expected) -> None:
    assert digit_status(digit) == expected


@pytest.mark.parametrize(
    ("assertion", "digit", "has_sentence", "expected"),
    [
        ("present", 1, True, "present_signed"),
        ("present", -1, True, "assertion_digit_mismatch"),
        ("present", 0, True, "assertion_digit_mismatch"),
        ("absent", -1, True, "absent_signed"),
        ("absent", 1, True, "assertion_digit_mismatch"),
        ("uncertain", 0, True, "uncertain_abstention"),
        ("uncertain", 1, True, "assertion_digit_mismatch"),
        ("not_mentioned", 0, False, "not_mentioned_abstention"),
        ("not_mentioned", -1, False, "silence_not_a_sign"),
        ("not_mentioned", 1, False, "silence_not_a_sign"),
        ("not_mentioned", 0, True, "sentence_with_silence"),
        ("present", 1, False, "sentence_required"),
        ("absent", -1, False, "sentence_required"),
        ("uncertain", 0, False, "sentence_required"),
        ("probably", 1, True, "invalid_assertion"),
        ("present", True, True, "invalid_digit"),
        ("present", 1, 1, "invalid_sentence_state"),
    ],
)
def test_assertion_digit_code_pins_negation_uncertainty_and_silence(
    assertion, digit, has_sentence, expected
) -> None:
    assert assertion_digit_code(assertion, digit, has_sentence) == expected


def test_sentence_status_exact_whitespace_and_missing() -> None:
    report = "First part. Second\n  part continues."
    assert sentence_status("First part.", report) == "verbatim"
    assert sentence_status("Second part continues.", report) == "verbatim_whitespace"
    assert sentence_status("Third part.", report) == "not_in_report"
    assert sentence_status("first part.", report) == "not_in_report"
    assert sentence_status("", report) == "sentence_empty"
    assert sentence_status("...", report) == "sentence_empty"
    assert sentence_status("First part.", None) == "report_missing"


@pytest.mark.parametrize(
    ("source", "reader", "expected"),
    [
        ("report:train.csv", "claude-reader-1", "independent_report"),
        ("recall:squint-memory", "claude-reader-1", "visual_memory_source"),
        ("report:train.csv", "squint-recall", "visual_memory_source"),
        ("report:predicted-labels", "claude-reader-1", "predicted_label_source"),
        ("report:train.csv", "classifier-7", "predicted_label_source"),
        ("train.csv", "claude-reader-1", "source_not_report"),
        ("report:", "claude-reader-1", "source_not_report"),
        ("", "claude-reader-1", "source_missing"),
        ("report:train.csv", "", "reader_missing"),
        (None, "claude-reader-1", "source_missing"),
    ],
)
def test_source_independence_code_both_sides(source, reader, expected) -> None:
    assert source_independence_code(source, reader) == expected


def test_scope_code_is_study_condition_only() -> None:
    assert scope_code("study_condition") == "study_condition"
    assert scope_code("pixel_region") == "scope_not_study_condition"
    assert scope_code("slice") == "scope_not_study_condition"
    assert scope_code(None) == "scope_not_study_condition"


def test_subject_code_declared_composite_and_not_implicated() -> None:
    assert subject_code("ACL", "acl") == "declared_object"
    assert subject_code("ACL", "diagnosis/ACL") == "question_composite"
    assert subject_code("Effusion", "femur") == "subject_not_implicated"
    assert subject_code("Fracture", "femur") == "declared_object"
    assert subject_code("acl", "acl") == "unknown_question"
    assert subject_code("ACL", "") == "subject_missing"


def test_group_digits_code_both_signs_abstention_and_contradiction() -> None:
    assert group_digits_code([1]) == "positive"
    assert group_digits_code([-1]) == "negative"
    assert group_digits_code([1, 1, 0]) == "positive"
    assert group_digits_code([-1, 0]) == "negative"
    assert group_digits_code([1, -1]) == "contradictory"
    assert group_digits_code([-1, 0, 1]) == "contradictory"
    assert group_digits_code([0, 0]) == "abstention_only"
    assert group_digits_code([]) == "silent"
    assert group_digits_code([1, True]) == "invalid_digit"


def test_repeat_code_same_digit_once_and_changed_digit_conflicts() -> None:
    assert repeat_code(1, 1) == "duplicate"
    assert repeat_code(-1, -1) == "duplicate"
    assert repeat_code(1, -1) == "self_contradiction"
    assert repeat_code(0, 1) == "self_contradiction"
    assert repeat_code(1, 2) == "invalid_digit"


def test_revision_code_new_and_not_new() -> None:
    assert revision_code("rev-2", "rev-1") == "new"
    assert revision_code("rev-2", None) == "new"
    assert revision_code("rev-1", "rev-1") == "revision_not_new"
    assert revision_code("", "rev-1") == "revision_invalid"
    assert revision_code(3, "rev-1") == "revision_invalid"


def test_admission_call_code_signs_teach_and_everything_else_holds() -> None:
    assert admission_call_code("signed", 1) == "teach_positive"
    assert admission_call_code("signed", -1) == "teach_negative"
    assert admission_call_code("signed", 0) == "invalid_digit"
    assert admission_call_code("abstention", 0) == "abstain_no_case"
    assert admission_call_code("abstention", 1) == "abstain_no_case"
    assert admission_call_code("duplicate", 1) == "duplicate_ignored"
    assert admission_call_code("contradictory", -1) == "hold_contradictory"
    assert admission_call_code("needs_review", 1) == "hold_review"
    assert admission_call_code("not_in_report", 1) == "rejected"
    assert admission_call_code(None, 1) == "rejected"


def test_profile_status_actual_speaking_cheap_and_each_refusal() -> None:
    assert profile_status(_profile(), "acl", UID_A) == "speaking"
    assert profile_status(None, "acl", UID_A) == "profile_missing"
    assert profile_status({**_profile(), "schema": "other/v1"}, "acl", UID_A) == (
        "profile_schema_unsupported"
    )
    assert profile_status(_profile("femur"), "acl", UID_A) == "profile_subject_mismatch"
    assert profile_status(_profile(), "acl", "other-study") == "profile_study_mismatch"
    assert profile_status(_profile(mode="full"), "acl", UID_A) == "profile_not_cheap"
    assert profile_status(_profile(mode="cheap"), "acl", UID_A) == "speaking"
    assert (
        profile_status(_profile(banks={"b": [0, 0, 0]}), "acl", UID_A)
        == "profile_silent"
    )
    assert profile_status(_profile(banks={}), "acl", UID_A) == "profile_silent"
    assert profile_status(_profile(banks={"b": [1, 2]}), "acl", UID_A) == (
        "profile_banks_invalid"
    )
    assert profile_status(_profile(banks={"b": [1, -1, 0]}), "acl", UID_A) == (
        "profile_banks_invalid"
    )
    assert profile_status(_profile(banks={"b": [True, 0, 0]}), "acl", UID_A) == (
        "profile_banks_invalid"
    )


def test_finding_admission_code_requires_located_actual_cheap_speaking() -> None:
    assert finding_admission_code(_finding()) == "admissible"
    assert finding_admission_code(_finding(status="partial")) == "not_located"
    assert finding_admission_code(_finding(status="open")) == "not_located"
    assert finding_admission_code(
        _finding(status="partial"), ("located", "partial")
    ) == ("admissible")
    assert finding_admission_code(_finding(mode="full")) == "profile_not_cheap"
    assert finding_admission_code(_finding(profile=None)) == "profile_missing"
    assert finding_admission_code(
        _finding(profile=_profile(banks={"b": [0, 0, 0]}))
    ) == ("profile_silent")
    assert finding_admission_code(_finding(uid="")) == "study_uid_missing"
    assert finding_admission_code([]) == "finding_not_mapping"


def test_memory_question_code_applicable_and_not() -> None:
    table = {"ACL": frozenset({"acl", "femur"}), "MCL": None}
    assert memory_question_code(None, "ACL", "acl") == "no_memory_table"
    assert memory_question_code(table, "ACL", "acl") == "applicable"
    assert memory_question_code(table, "ACL", "diagnosis/ACL") == "applicable"
    assert memory_question_code(table, "ACL", "pcl") == "subject_not_in_memory_question"
    assert memory_question_code(table, "MCL", "anything") == "applicable"
    assert memory_question_code(table, "Fracture", "femur") == "question_not_in_memory"


# --- validate_report_calls ----------------------------------------------------


def test_validate_signed_positive_and_negative_calls_are_countable() -> None:
    positive = _call()
    negative = _call(
        question="MCL",
        digit=-1,
        assertion="absent",
        sentence=SENT_ABSENT,
        subject="mcl",
    )
    results = _validate(positive, negative)
    assert [r["status"] for r in results] == ["signed", "signed"]
    assert [r["digit"] for r in results] == [1, -1]
    assert results[0]["sentence_match"] == "verbatim"
    assert results[0]["sentence"] == SENT_PRESENT
    assert results[0]["call_id"] != results[1]["call_id"]
    assert [r["index"] for r in results] == [0, 1]


def test_validate_uncertain_and_not_mentioned_are_abstentions_with_no_negative() -> (
    None
):
    uncertain = _call(
        question="Effusion",
        digit=0,
        assertion="uncertain",
        sentence=SENT_UNCERTAIN,
        subject="joint_fluid",
    )
    silent = _call(
        question="Fracture",
        digit=0,
        assertion="not_mentioned",
        sentence="",
        subject="femur",
    )
    silence_as_negative = _call(
        question="Fracture",
        digit=-1,
        assertion="not_mentioned",
        sentence="",
        subject="femur",
    )
    results = _validate(uncertain, silent, silence_as_negative)
    assert [r["status"] for r in results] == [
        "abstention",
        "abstention",
        "silence_not_a_sign",
    ]
    assert results[1]["sentence_match"] == "none"
    assert results[1]["sentence_sha256"] is None
    assert results[2]["record"]["digit"] == -1


def test_validate_sentence_must_be_in_the_report() -> None:
    wrapped = _call(
        question="Lateral OA",
        sentence="A wrapped sentence stays whole.",
        subject="femur",
    )
    invented = _call(sentence="Complete tear of the invented ligament.")
    results = _validate(wrapped, invented)
    assert results[0]["status"] == "signed"
    assert results[0]["sentence_match"] == "verbatim_whitespace"
    assert results[1]["status"] == "not_in_report"


def test_validate_binds_report_sha_and_report_presence() -> None:
    wrong_sha = _call(report_sha=report_sha256("a different report"))
    no_report = _call(study_uid="unknown-study", report_sha=report_sha256(REPORT_A))
    other_study = _call(study_uid=UID_B, report_sha=report_sha256(REPORT_B))
    results = _validate(wrong_sha, no_report, other_study)
    assert results[0]["status"] == "report_sha_mismatch"
    assert results[1]["status"] == "report_missing"
    # The sentence belongs to report A, not B: a correct sha cannot rescue it.
    assert results[2]["status"] == "not_in_report"


def test_validate_refuses_visual_memory_and_predicted_teachers() -> None:
    recalled = _call(source="recall:squint-memory")
    predicted_field = _call()
    predicted_field["prediction"] = 1
    outcome_field = _call()
    outcome_field["recall_outcome"] = {"outcome": "positive"}
    results = _validate(recalled, predicted_field, outcome_field)
    assert results[0]["status"] == "visual_memory_source"
    assert results[1]["status"] == "predicted_label_teacher"
    assert results[2]["status"] == "predicted_label_teacher"
    # A refused record retains the original for review.
    assert results[1]["record"]["prediction"] == 1


def test_validate_exact_twelve_questions_digits_scope_and_fields() -> None:
    results = _validate(
        _call(question="acl"),
        _call(question="Bakers"),
        _call(digit=True),
        _call(digit=2),
        _call(digit=1.0),
        _call(scope="pixel_region"),
        _call(subject="patella"),
        _call(reader=""),
        _call(extra_field="x"),
    )
    assert [r["status"] for r in results] == [
        "unknown_question",
        "unknown_question",
        "invalid_digit",
        "invalid_digit",
        "invalid_digit",
        "scope_not_study_condition",
        "subject_not_implicated",
        "field_invalid",
        "unknown_field",
    ]
    missing = _call()
    del missing["reader"]
    assert _validate(missing)[0]["status"] == "missing_field"
    assert _validate("not a record")[0]["status"] == "record_not_mapping"


def test_validate_all_twelve_questions_are_accepted() -> None:
    records = [
        _call(
            question=q,
            digit=0,
            assertion="not_mentioned",
            sentence="",
            subject=f"diagnosis/{q}",
        )
        for q in LABELS
    ]
    results = _validate(*records)
    assert len(results) == 12
    assert {r["status"] for r in results} == {"abstention"}


def test_validate_duplicate_source_scope_call_counts_once() -> None:
    first = _call()
    repeat = _call(reader="claude-reader-2")
    results = _validate(first, repeat)
    assert [r["status"] for r in results] == ["signed", "duplicate"]
    assert results[1]["duplicate_of"] == results[0]["call_id"]
    assert results[0]["duplicate_of"] is None


def test_validate_contradictory_calls_are_all_retained_not_resolved() -> None:
    positive = _call()
    negative = _call(
        source="report:addendum.txt",
        digit=-1,
        assertion="absent",
        sentence=SENT_ABSENT,
    )
    results = _validate(positive, negative)
    assert [r["status"] for r in results] == ["contradictory", "contradictory"]
    assert [r["digit"] for r in results] == [1, -1]


def test_validate_one_source_changing_its_own_call_is_contradictory() -> None:
    first = _call()
    changed = _call(digit=-1, assertion="absent", sentence=SENT_ABSENT)
    results = _validate(first, changed)
    assert [r["status"] for r in results] == ["contradictory", "contradictory"]


def test_validate_agreeing_independent_sources_and_abstentions_do_not_conflict() -> (
    None
):
    first = _call()
    second = _call(source="report:addendum.txt")
    abstain = _call(
        source="report:other.txt",
        digit=0,
        assertion="uncertain",
        sentence=SENT_UNCERTAIN,
    )
    results = _validate(first, second, abstain)
    assert [r["status"] for r in results] == ["signed", "signed", "abstention"]


def test_validate_needs_review_is_retained_and_teaches_nothing() -> None:
    flagged = _call(needs_review=True, note="ambiguous laterality")
    results = _validate(flagged)
    assert results[0]["status"] == "needs_review"
    assert results[0]["note"] == "ambiguous laterality"
    assert results[0]["needs_review"] is True


def test_validate_does_not_mutate_inputs_and_seals_records() -> None:
    records = [
        _call(),
        _call(
            question="MCL",
            digit=-1,
            assertion="absent",
            sentence=SENT_ABSENT,
            subject="mcl",
        ),
    ]
    reports = {UID_A: REPORT_A}
    before = copy.deepcopy((records, reports))
    results = validate_report_calls(records, reports)
    assert (records, reports) == before
    assert all(len(r["record_sha256"]) == 64 for r in results)
    again = validate_report_calls(records, reports)
    assert [r["record_sha256"] for r in results] == [r["record_sha256"] for r in again]


def test_validate_argument_errors_are_named() -> None:
    with pytest.raises(ReportCallError) as error:
        validate_report_calls("records", {})
    assert error.value.reason == "report_call_records_list_required"
    with pytest.raises(ReportCallError) as error:
        validate_report_calls([], [])
    assert error.value.reason == "reports_mapping_required"


# --- admit_report_cases -------------------------------------------------------


def _admit(
    memory: dict, findings: list, *records: dict, revision: str = "rev-2"
) -> dict:
    return admit_report_cases(
        memory,
        findings,
        _validate(*records),
        revision,
        reports={UID_A: REPORT_A, UID_B: REPORT_B},
    )


def test_admit_positive_call_creates_cheap_case_and_next_revision() -> None:
    memory = _memory()
    findings = [_finding()]
    before = copy.deepcopy((memory["cases"], memory["revision"], findings))
    result = _admit(memory, findings, _call())
    assert result is not memory
    assert (memory["cases"], memory["revision"], findings) == before
    assert memory["revision"] == "rev-1" and len(memory["cases"]) == 1
    assert result["revision"] == "rev-2"
    assert result["parent_revision"] == "rev-1"
    assert result["arrays"] is memory["arrays"]
    assert result["cases"][0] is memory["cases"][0]
    assert len(result["cases"]) == 2
    case = result["cases"][-1]
    assert case["condition_calls"] == {"ACL": 1}
    assert case["condition_scopes"] == {"ACL": "study_condition"}
    assert case["study_uid"] == UID_A and case["subject"] == "acl"
    assert case["profile"] == _profile()
    assert case["profile"] is not findings[0]["profile"]
    assert case["regions"] == {"sag": [1, 2, 3, 4]}
    assert case["case_id"].startswith("case-sha256:")
    assert case["full_profile"] is None
    assert case["full_source"]["status"] == "unavailable"
    assert case["teaching"]["pixel_localization_confirmed"] is False
    assert case["teaching"]["source_scope"] == "study_condition"
    assert case["teaching"]["calls"][0]["sentence"] == SENT_PRESENT
    assert case["teaching_source"].startswith("report-calls-sha256:")
    receipt = result["report_admissions"][-1]
    assert receipt["added_case_count"] == 1
    assert receipt["trust_added"] == 0 and receipt["censors_added"] == 0
    assert receipt["pixel_localization_confirmed"] is False
    assert receipt["source_identities"] == [
        {
            "source": "report:train.csv",
            "reader": "claude-reader-1",
            "report_sha": report_sha256(REPORT_A),
        }
    ]


def test_admit_negative_call_creates_negative_case_not_inferred_from_silence() -> None:
    result = _admit(
        _memory(),
        [_finding("mcl"), _finding("femur")],
        _call(
            question="MCL",
            digit=-1,
            assertion="absent",
            sentence=SENT_ABSENT,
            subject="mcl",
        ),
    )
    assert len(result["cases"]) == 2
    assert result["cases"][-1]["subject"] == "mcl"
    assert result["cases"][-1]["condition_calls"] == {"MCL": -1}
    receipt = result["report_admissions"][-1]
    # The femur has no report call: no case, and no negative derived from silence.
    assert receipt["findings_without_calls"] == 1
    assert [c["subject"] for c in receipt["admitted"]] == ["mcl"]


def test_admit_abstention_adds_no_signed_case_trust_or_censor() -> None:
    result = _admit(
        _memory(),
        [_finding()],
        _call(digit=0, assertion="uncertain", sentence=SENT_UNCERTAIN),
        _call(
            digit=0, assertion="not_mentioned", sentence="", source="report:other.txt"
        ),
    )
    assert len(result["cases"]) == 1
    receipt = result["report_admissions"][-1]
    assert receipt["added_case_count"] == 0
    assert len(receipt["retained_calls"]["abstentions"]) == 2
    assert receipt["skipped_findings"] == [
        {"study_uid": UID_A, "subject": "acl", "code": "no_signed_call"}
    ]
    assert receipt["trust_added"] == 0 and receipt["censors_added"] == 0


def test_admit_abstained_question_is_not_added_beside_signed_question() -> None:
    result = _admit(
        _memory(),
        [_finding("femur")],
        _call(
            question="Fracture",
            digit=-1,
            assertion="absent",
            sentence=SENT_ABSENT,
            subject="femur",
        ),
        _call(
            question="Contusion",
            digit=0,
            assertion="uncertain",
            sentence=SENT_UNCERTAIN,
            subject="femur",
        ),
    )
    assert result["cases"][-1]["condition_calls"] == {"Fracture": -1}


def test_admit_contradictory_calls_are_retained_and_teach_nothing() -> None:
    result = _admit(
        _memory(),
        [_finding()],
        _call(),
        _call(
            source="report:addendum.txt",
            digit=-1,
            assertion="absent",
            sentence=SENT_ABSENT,
        ),
    )
    assert len(result["cases"]) == 1
    receipt = result["report_admissions"][-1]
    assert [c["digit"] for c in receipt["retained_calls"]["contradictory"]] == [1, -1]
    assert receipt["skipped_findings"] == [
        {"study_uid": UID_A, "subject": "acl", "code": "calls_contradictory"}
    ]


def test_admit_regroups_contradictions_across_separately_validated_batches() -> None:
    batch_one = _validate(_call())
    batch_two = _validate(
        _call(
            source="report:addendum.txt",
            digit=-1,
            assertion="absent",
            sentence=SENT_ABSENT,
        )
    )
    assert batch_one[0]["status"] == "signed" and batch_two[0]["status"] == "signed"
    result = admit_report_cases(
        _memory(),
        [_finding()],
        batch_one + batch_two,
        "rev-2",
        reports={UID_A: REPORT_A},
    )
    assert len(result["cases"]) == 1
    receipt = result["report_admissions"][-1]
    assert len(receipt["retained_calls"]["contradictory"]) == 2


def test_admit_regroups_duplicates_across_batches_once() -> None:
    batch_one = _validate(_call())
    batch_two = _validate(_call(reader="claude-reader-2"))
    result = admit_report_cases(
        _memory(),
        [_finding()],
        batch_one + batch_two,
        "rev-2",
        reports={UID_A: REPORT_A},
    )
    receipt = result["report_admissions"][-1]
    assert receipt["added_case_count"] == 1
    assert len(receipt["retained_calls"]["duplicates"]) == 1
    assert len(result["cases"][-1]["teaching"]["calls"]) == 1


def test_admit_needs_review_call_teaches_nothing_but_is_visible() -> None:
    result = _admit(_memory(), [_finding()], _call(needs_review=True))
    receipt = result["report_admissions"][-1]
    assert len(result["cases"]) == 1
    assert len(receipt["retained_calls"]["needs_review"]) == 1
    assert receipt["skipped_findings"][0]["code"] == "call_needs_review"


def test_admit_refuses_silent_unlocated_and_non_cheap_profiles() -> None:
    silent = _finding(profile=_profile(banks={"b": [0, 0, 0]}))
    partial = _finding("mcl", status="partial")
    full = _finding("femur", mode="full")
    result = _admit(
        _memory(),
        [silent, partial, full],
        _call(),
        _call(question="MCL", subject="mcl"),
        _call(question="Fracture", subject="femur"),
    )
    assert len(result["cases"]) == 1
    receipt = result["report_admissions"][-1]
    codes = {(s["subject"], s["code"]) for s in receipt["skipped_findings"]}
    assert codes == {
        ("acl", "profile_silent"),
        ("mcl", "not_located"),
        ("femur", "profile_not_cheap"),
    }
    assert {u["code"] for u in receipt["unmatched_calls"]} == {
        "profile_silent",
        "not_located",
        "profile_not_cheap",
    }


def test_admit_call_without_located_finding_is_unmatched_not_invented() -> None:
    result = _admit(_memory(), [_finding("mcl")], _call())
    receipt = result["report_admissions"][-1]
    assert len(result["cases"]) == 1
    assert [u["code"] for u in receipt["unmatched_calls"]] == ["no_located_finding"]


def test_admit_ignores_prediction_fields_carried_by_a_finding() -> None:
    finding = _finding(condition_calls={"ACL": 1}, outcome="positive")
    result = _admit(
        _memory(),
        [finding],
        _call(digit=-1, assertion="absent", sentence=SENT_ABSENT),
    )
    case = result["cases"][-1]
    assert case["condition_calls"] == {"ACL": -1}
    receipt = result["report_admissions"][-1]
    assert receipt["admitted"][0]["finding_calls_ignored"] == [
        "condition_calls",
        "outcome",
    ]


def test_admit_study_already_in_memory_is_not_double_counted() -> None:
    memory = _memory()
    memory["cases"][0]["study_uid"] = UID_A
    result = _admit(memory, [_finding()], _call())
    assert len(result["cases"]) == 1
    assert result["report_admissions"][-1]["skipped_findings"] == [
        {"study_uid": UID_A, "subject": "acl", "code": "already_in_memory_question"}
    ]


def test_admit_ambiguous_duplicate_findings_are_not_guessed_between() -> None:
    other = _finding(profile=_profile(banks={"b": [5, 0, 0]}))
    result = _admit(_memory(), [_finding(), other], _call())
    assert len(result["cases"]) == 1
    assert (
        result["report_admissions"][-1]["skipped_findings"][0]["code"]
        == "finding_ambiguous"
    )


def test_admit_preserves_full_pairing_when_the_finding_has_it() -> None:
    full = {
        "schema": "knee.squint-profile/v1",
        "subject": "acl",
        "banks": {"f": [1, 0, 2]},
    }
    finding = _finding(
        full_profile=full, full_source={"status": "paired", "mode": "full"}
    )
    result = _admit(_memory(), [finding], _call())
    case = result["cases"][-1]
    assert case["full_profile"] == full
    assert case["full_profile"] is not full
    assert case["full_source"] == {"status": "paired", "mode": "full"}
    assert case["profile_mode"] == "cheap"
    assert (
        result["report_admissions"][-1]["admitted"][0]["full_profile_available"] is True
    )


def test_admit_accepts_locator_result_with_objects_mapping() -> None:
    located = {
        "study_uid": UID_A,
        "objects": {
            "acl": {"status": "located", "profile": _profile("acl"), "regions": {}},
            "femur": {"status": "absent"},
        },
    }
    result = _admit(_memory(), [located], _call())
    assert result["cases"][-1]["subject"] == "acl"
    assert result["cases"][-1]["study_uid"] == UID_A


def test_admit_respects_the_memorys_own_question_declarations() -> None:
    memory = _memory(questions={"ACL": {"objects": ["acl"]}})
    result = _admit(
        memory,
        [_finding("mcl"), _finding("acl")],
        _call(question="MCL", subject="mcl"),
        _call(),
    )
    receipt = result["report_admissions"][-1]
    assert [c["subject"] for c in receipt["admitted"]] == ["acl"]
    assert receipt["held_calls"][0]["code"] == "question_not_in_memory"
    assert receipt["skipped_findings"] == [
        {"study_uid": UID_A, "subject": "mcl", "code": "no_applicable_signed_call"}
    ]


def test_admit_tampered_records_fail_integrity_and_teach_nothing() -> None:
    sealed = _validate(_call())[0]
    flipped_digit = {**sealed, "digit": -1}
    forged_status = {**_validate(_call(needs_review=True))[0], "status": "signed"}
    not_a_call = {"status": "signed", "digit": 1}
    result = admit_report_cases(
        _memory(),
        [_finding()],
        [flipped_digit, forged_status, not_a_call],
        "rev-2",
        reports={UID_A: REPORT_A},
    )
    assert len(result["cases"]) == 1
    rejected = result["report_admissions"][-1]["retained_calls"]["rejected"]
    assert [r["status"] for r in rejected] == ["record_integrity_failed"] * 3


def test_admit_keeps_rejected_calls_for_review_and_never_teaches_from_them() -> None:
    invented = _call(sentence="Complete tear of the invented ligament.")
    result = _admit(_memory(), [_finding()], invented)
    assert len(result["cases"]) == 1
    rejected = result["report_admissions"][-1]["retained_calls"]["rejected"]
    assert rejected[0]["status"] == "not_in_report"


def test_admit_requires_a_new_revision_and_valid_arguments() -> None:
    with pytest.raises(ReportCallError) as error:
        admit_report_cases(_memory(), [], [], "rev-1", reports={})
    assert error.value.reason == "revision_not_new"
    with pytest.raises(ReportCallError) as error:
        admit_report_cases(_memory(), [], [], "", reports={})
    assert error.value.reason == "revision_invalid"
    with pytest.raises(ReportCallError) as error:
        admit_report_cases(
            _memory(schema="knee.squint-memory/v2"), [], [], "rev-2", reports={}
        )
    assert error.value.reason == "memory_schema_unsupported"
    with pytest.raises(ReportCallError) as error:
        admit_report_cases(
            {"schema": "knee.squint-memory/v1"}, [], [], "rev-2", reports={}
        )
    assert error.value.reason == "memory_cases_required"
    with pytest.raises(ReportCallError) as error:
        admit_report_cases(_memory(), "findings", [], "rev-2", reports={})
    assert error.value.reason == "findings_list_required"


def test_admit_preserves_the_cases_container_kind_without_mutating_it() -> None:
    as_tuple = _memory(cases=(_existing_case(),))
    result = _admit(as_tuple, [_finding()], _call())
    assert isinstance(result["cases"], tuple) and len(as_tuple["cases"]) == 1
    existing = _existing_case()
    as_mapping = _memory(cases={existing["case_id"]: existing})
    result = _admit(as_mapping, [_finding()], _call())
    assert isinstance(result["cases"], dict)
    assert len(as_mapping["cases"]) == 1 and len(result["cases"]) == 2
    new_case = next(c for c in result["cases"].values() if c["study_uid"] == UID_A)
    assert result["cases"][new_case["case_id"]] is new_case


def test_admit_chains_revisions_and_keeps_every_receipt() -> None:
    first = _admit(_memory(), [_finding()], _call())
    second = admit_report_cases(
        first,
        [
            _finding(
                "mcl",
                uid=UID_B,
                profile={**_profile("mcl"), "source": {"study_uid": UID_B}},
            )
        ],
        _validate(
            _call(
                REPORT_B,
                study_uid=UID_B,
                question="MCL",
                subject="mcl",
                sentence=REPORT_B,
            )
        ),
        "rev-3",
        reports={UID_A: REPORT_A, UID_B: REPORT_B},
    )
    assert second["parent_revision"] == "rev-2"
    assert len(second["cases"]) == 3
    assert len(first["cases"]) == 2
    assert [r["revision"] for r in second["report_admissions"]] == ["rev-2", "rev-3"]
    assert len(first["report_admissions"]) == 1
    assert (
        second["report_admissions"][1]["parent_cases_sha256"]
        == first["report_admissions"][0]["cases_sha256"]
    )


def test_admit_case_identity_is_deterministic() -> None:
    one = _admit(_memory(), [_finding()], _call())["cases"][-1]["case_id"]
    two = _admit(_memory(), [_finding()], _call())["cases"][-1]["case_id"]
    other = _admit(_memory(), [_finding()], _call(), revision="rev-9")["cases"][-1][
        "case_id"
    ]
    assert one == two
    assert one != other


# --- exchange files -----------------------------------------------------------


def _train_csv(path: Path) -> Path:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(TRAIN_COLUMNS)
        writer.writerow([UID_A, REPORT_A, *["1"] * len(LABELS)])
        writer.writerow([UID_B, REPORT_B, *["0"] * len(LABELS)])
        writer.writerow(["1.2.826.0003", "  ", *[""] * len(LABELS)])
    return path


def test_read_reports_returns_report_text_only(tmp_path: Path) -> None:
    reports = read_reports(_train_csv(tmp_path / "train.csv"))
    assert reports == {UID_A: REPORT_A, UID_B: REPORT_B, "1.2.826.0003": "  "}


def test_export_writes_full_reports_without_labels(tmp_path: Path) -> None:
    train = _train_csv(tmp_path / "train.csv")
    out = tmp_path / "batches" / "batch.json"
    summary = export_report_batch(train, out)
    assert summary["study_count"] == 2
    assert summary["study_uids"] == [UID_A, UID_B]
    assert summary["skipped"] == {"1.2.826.0003": "report_blank"}
    document = json.loads(out.read_text(encoding="utf-8"))
    assert document["questions"] == list(LABELS)
    assert [set(s) for s in document["studies"]] == [
        {"study_uid", "report_sha256", "report"}
    ] * 2
    assert document["studies"][0]["report"] == REPORT_A
    assert document["studies"][0]["report_sha256"] == report_sha256(REPORT_A)
    assert "labels" not in document
    assert document["subjects_by_question"]["ACL"][0] == "diagnosis/ACL"
    assert document["call_record_template"]["scope"] == "study_condition"
    assert not list(out.parent.glob("*.tmp"))
    assert read_batch_reports(out) == {UID_A: REPORT_A, UID_B: REPORT_B}


def test_export_selected_study_uids_keep_requested_order(tmp_path: Path) -> None:
    train = _train_csv(tmp_path / "train.csv")
    summary = export_report_batch(train, tmp_path / "b.json", [UID_B, UID_A])
    assert summary["study_uids"] == [UID_B, UID_A]


def test_export_refuses_unknown_duplicate_and_bare_string_uids(tmp_path: Path) -> None:
    train = _train_csv(tmp_path / "train.csv")
    for uids, reason in (
        (["nope"], "study_uid_not_in_train_csv"),
        ([UID_A, UID_A], "duplicate_study_uid_requested"),
        (UID_A, "study_uids_list_required"),
        ([1], "study_uid_invalid"),
    ):
        with pytest.raises(ReportCallError) as error:
            export_report_batch(train, tmp_path / "b.json", uids)
        assert error.value.reason == reason
    assert not (tmp_path / "b.json").exists()


def test_read_batch_reports_refuses_a_tampered_report(tmp_path: Path) -> None:
    out = tmp_path / "batch.json"
    export_report_batch(_train_csv(tmp_path / "train.csv"), out)
    document = json.loads(out.read_text(encoding="utf-8"))
    document["studies"][0]["report"] += " edited"
    out.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ReportCallError) as error:
        read_batch_reports(out)
    assert error.value.reason == "report_batch_study_invalid"


def test_import_report_calls_reads_list_document_and_jsonl(tmp_path: Path) -> None:
    reports = {UID_A: REPORT_A}
    record = _call()
    as_list = tmp_path / "calls.json"
    as_list.write_text(json.dumps([record]), encoding="utf-8")
    as_document = tmp_path / "document.json"
    as_document.write_text(
        json.dumps({"schema": "knee.squint-report-calls/v1", "calls": [record]}),
        encoding="utf-8",
    )
    as_lines = tmp_path / "calls.jsonl"
    as_lines.write_text(
        json.dumps(record)
        + "\n\n"
        + json.dumps(_call(digit=0, assertion="uncertain", sentence=SENT_UNCERTAIN))
        + "\n",
        encoding="utf-8",
    )
    assert [r["status"] for r in import_report_calls(as_list, reports)] == ["signed"]
    assert [r["status"] for r in import_report_calls(as_document, reports)] == [
        "signed"
    ]
    assert [r["status"] for r in import_report_calls(as_lines, reports)] == [
        "contradictory",
        "contradictory",
    ]


def test_import_report_calls_named_failures(tmp_path: Path) -> None:
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{not json", encoding="utf-8")
    wrong_schema = tmp_path / "wrong.json"
    wrong_schema.write_text(
        json.dumps({"schema": "other", "calls": []}), encoding="utf-8"
    )
    scalar = tmp_path / "scalar.json"
    scalar.write_text("3", encoding="utf-8")
    for path, reason in (
        (bad_json, "report_calls_json_invalid"),
        (wrong_schema, "report_calls_schema_unsupported"),
        (scalar, "report_calls_document_invalid"),
        (tmp_path / "missing.json", "report_calls_unreadable"),
    ):
        with pytest.raises(ReportCallError) as error:
            import_report_calls(path, {})
        assert error.value.reason == reason


def test_end_to_end_export_import_and_admit(tmp_path: Path) -> None:
    train = _train_csv(tmp_path / "train.csv")
    batch = tmp_path / "batch.json"
    export_report_batch(train, batch, [UID_A])
    reports = read_batch_reports(batch)
    calls = tmp_path / "calls.json"
    calls.write_text(
        json.dumps(
            [
                _call(),
                _call(
                    question="MCL",
                    digit=-1,
                    assertion="absent",
                    sentence=SENT_ABSENT,
                    subject="mcl",
                ),
                _call(
                    question="Fracture",
                    digit=0,
                    assertion="not_mentioned",
                    sentence="",
                    subject="femur",
                ),
            ]
        ),
        encoding="utf-8",
    )
    validated = import_report_calls(calls, reports)
    assert [r["status"] for r in validated] == ["signed", "signed", "abstention"]
    memory = _memory()
    result = admit_report_cases(
        memory,
        [_finding("acl"), _finding("mcl"), _finding("femur")],
        validated,
        "rev-2",
        reports=reports,
    )
    taught = {c["subject"]: c["condition_calls"] for c in result["cases"][1:]}
    assert taught == {"acl": {"ACL": 1}, "mcl": {"MCL": -1}}
    assert len(memory["cases"]) == 1
    receipt = result["report_admissions"][-1]
    assert [c["code"] for c in receipt["skipped_findings"]] == ["no_signed_call"]
    json.dumps(receipt)


def test_admit_requires_real_reports_even_when_call_digest_is_sealed() -> None:
    with pytest.raises(ReportCallError) as error:
        admit_report_cases(_memory(), [_finding()], _validate(_call()), "rev-2")
    assert error.value.reason == "needs_reports"


def test_admit_revalidates_forged_digest_against_report_text() -> None:
    call = _call()
    call["sentence"] = "Invented positive sentence."
    # A public digest does not make an invented sentence an attributed report call.
    forged = _validate(_call())[0]
    forged["sentence"] = call["sentence"]
    forged["sentence_sha256"] = report_sha256(call["sentence"])
    from knee.diagnosis.squint_reports import _seal

    forged["record_sha256"] = _seal(forged)
    result = admit_report_cases(
        _memory(), [_finding()], [forged], "rev-2", reports={UID_A: REPORT_A}
    )
    assert len(result["cases"]) == 1
    assert (
        result["report_admissions"][-1]["retained_calls"]["rejected"][0]["status"]
        == "not_in_report"
    )


def test_profile_nested_lineage_must_bind_every_source_uid() -> None:
    profile = _profile()
    profile["source"] = {
        "mode": "cheap",
        "series_context": {"study_uid": UID_A},
        "lineage": [{"study_uid": "another-study"}],
    }
    assert profile_status(profile, "acl", UID_A) == "profile_study_mismatch"
    assert finding_admission_code(_finding(profile=profile)) == "profile_study_mismatch"


def test_new_question_can_teach_existing_object_and_prior_opposition_is_receipted() -> (
    None
):
    first = _admit(_memory(), [_finding()], _call())
    prior_case = first["cases"][-1]
    prior_snapshot = copy.deepcopy(prior_case)
    opposing = _call(
        digit=-1, assertion="absent", sentence=SENT_ABSENT, source="report:addendum.txt"
    )
    result = admit_report_cases(
        first, [_finding()], _validate(opposing), "rev-3", reports={UID_A: REPORT_A}
    )
    assert first["cases"][-1] == prior_snapshot
    assert (
        result["report_admissions"][-1]["prior_opposition"][0]["prior_case_id"]
        == prior_case["case_id"]
    )
    assert (
        result["report_admissions"][-1]["retained_calls"]["contradictory"][0]["status"]
        == "contradictory"
    )

    new_question = _call(
        question="Fracture",
        digit=-1,
        assertion="absent",
        sentence=SENT_ABSENT,
        subject="femur",
    )
    with_new = admit_report_cases(
        first,
        [_finding(), _finding("femur")],
        _validate(new_question),
        "rev-4",
        reports={UID_A: REPORT_A},
    )
    assert with_new["report_admissions"][-1]["added_case_count"] == 1
    assert with_new["cases"][-1]["condition_calls"] == {"Fracture": -1}
