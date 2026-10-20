from __future__ import annotations

import pytest

from knee.diagnosis.coverage import (
    CoverageError,
    _association_decision,
    coverage_for_snapshot,
)
from knee.diagnosis.models import Call, Case, Profile, Question, Snapshot
from knee.encoding.counts import BankLayout, CountBundle, CountLayout
from knee.objects.assignments import OBJECT_CODES


def _nested_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value).union(
            key for child in value.values() for key in _nested_keys(child)
        )
    if isinstance(value, list):
        return set().union(*(_nested_keys(child) for child in value))
    return set()


def _canonical_catalogue() -> tuple[str, ...]:
    return tuple(name for name, code in OBJECT_CODES.items() if code != 0)


def _profile(subject: str, *, scope: str = "question:fixture") -> Profile:
    layout = CountLayout(
        "coverage-test-layout/v1",
        "coverage-test-carrier/v1",
        (BankLayout("content", 2),),
    )
    return Profile(
        subject,
        CountBundle(layout, ((1, 0),)),
        "cheap/coverage-test-v1",
        scope,
        f"source:{subject}",
    )


def _case(
    case_id: str,
    profile: Profile,
    calls: tuple[Call, ...] = (),
    *,
    study_uid: str = "study-1",
) -> Case:
    return Case(case_id, study_uid, profile, calls, "teaching-r1")


def _questions() -> tuple[Question, ...]:
    return (
        Question(
            "ACL",
            "diagnosis/ACL",
            ("acl", "femur", "tibia"),
        ),
        Question(
            "Fracture",
            "diagnosis/Fracture",
            ("femur", "tibia", "patella", "fibula"),
        ),
    )


def test_composite_negative_is_role_reference_not_universal_object_normal() -> None:
    composite_negative = _case(
        "acl-negative",
        _profile("diagnosis/ACL", scope="question:ACL"),
        (Call("ACL", -1, "independent-label"),),
    )
    composite_positive = _case(
        "acl-positive",
        _profile("diagnosis/ACL", scope="question:ACL"),
        (Call("ACL", 1, "independent-label"),),
        study_uid="study-1",
    )
    composite_silent = _case(
        "acl-no-call",
        _profile("diagnosis/ACL", scope="question:ACL"),
        study_uid="study-3",
    )
    composite_zero = _case(
        "acl-explicit-silence",
        _profile("diagnosis/ACL", scope="question:ACL"),
        (Call("ACL", 0, "teacher-abstained"),),
        study_uid="study-4",
    )
    direct_femur = _case(
        "femur-direct-positive",
        _profile("femur", scope="object:femur"),
        (Call("ACL", 1, "independent-object-call"),),
        study_uid="study-5",
    )
    unassociated_object = _case(
        "tibia-no-question-call",
        _profile("tibia", scope="object:tibia"),
        study_uid="study-6",
    )
    snapshot = Snapshot(
        "memory-r1",
        (
            composite_negative,
            composite_positive,
            composite_silent,
            composite_zero,
            direct_femur,
            unassociated_object,
        ),
    )

    result = coverage_for_snapshot(
        snapshot,
        _questions(),
        _canonical_catalogue(),
    )

    assert result["schema"] == "knee.diagnostic-coverage/v1"
    assert result["memory_revision"] == "memory-r1"
    acl_composite = next(
        item
        for item in result["question_subjects"]
        if item["question_id"] == "ACL" and item["profile_subject"] == "diagnosis/ACL"
    )
    assert acl_composite["positive_case_ids"] == ["acl-positive"]
    assert acl_composite["negative_case_ids"] == ["acl-negative"]
    assert acl_composite["silent_case_ids"] == [
        "acl-explicit-silence",
        "acl-no-call",
    ]
    assert acl_composite["study_uids"] == [
        "study-1",
        "study-3",
        "study-4",
    ]
    assert {item["profile_scope"] for item in acl_composite["source_scopes"]} == {
        "question:ACL"
    }

    objects = {item["object"]: item for item in result["objects"]}
    femur = objects["femur"]
    assert femur["coverage_state"] == "direct_calls_present"
    assert femur["direct_question_calls"] == [
        {
            "question_id": "ACL",
            "positive_case_ids": ["femur-direct-positive"],
            "negative_case_ids": [],
            "silent_case_ids": [],
            "study_uids": ["study-5"],
            "source_scopes": [
                {
                    "case_id": "femur-direct-positive",
                    "study_uid": "study-5",
                    "profile_scope": "object:femur",
                    "profile_source_id": "source:femur",
                    "call_source": "independent-object-call",
                }
            ],
        }
    ]
    assert femur["declared_role_case_ids"] == [
        "acl-explicit-silence",
        "acl-negative",
        "acl-no-call",
        "acl-positive",
        "femur-direct-positive",
    ]
    assert objects["acl"]["coverage_state"] == "declared_role_only"
    assert objects["acl"]["direct_question_calls"] == []
    assert objects["patella"]["coverage_state"] == "no_precedent"
    assert objects["patella"]["declared_role_case_ids"] == []
    assert result["unassociated_case_ids"] == ["tibia-no-question-call"]
    assert not {"counts", "bundle", "profiles"}.intersection(_nested_keys(result))


def test_direct_calls_stay_scoped_to_their_actual_profile_subject() -> None:
    q_acl = Question("ACL", "diagnosis/ACL", ("acl", "femur"))
    q_fracture = Question("Fracture", "diagnosis/Fracture", ("femur", "tibia"))
    cases = (
        _case(
            "composite-fracture-positive",
            _profile("diagnosis/Fracture", scope="question:Fracture"),
            (Call("Fracture", 1, "label-source"),),
        ),
        _case(
            "direct-femur-negative",
            _profile("femur", scope="object:femur"),
            (Call("ACL", -1, "object-source"),),
            study_uid="study-2",
        ),
    )

    result = coverage_for_snapshot(
        Snapshot("r2", cases), (q_acl, q_fracture), _canonical_catalogue()
    )
    subjects = {
        (row["question_id"], row["profile_subject"]): row
        for row in result["question_subjects"]
    }

    assert subjects[("Fracture", "diagnosis/Fracture")]["positive_case_ids"] == [
        "composite-fracture-positive"
    ]
    assert ("Fracture", "femur") not in subjects
    assert subjects[("ACL", "femur")]["negative_case_ids"] == ["direct-femur-negative"]
    objects = {item["object"]: item for item in result["objects"]}
    assert objects["femur"]["direct_question_calls"][0]["question_id"] == "ACL"


@pytest.mark.parametrize(
    ("snapshot", "questions", "catalogue", "error"),
    [
        (None, (), (), "snapshot_required"),
        (Snapshot("r", ()), None, (), "questions_sequence_required"),
        (Snapshot("r", ()), (), None, "object_catalogue_sequence_required"),
        (
            Snapshot(
                "r",
                (
                    _case("duplicate", _profile("diagnosis/ACL")),
                    _case("duplicate", _profile("diagnosis/ACL")),
                ),
            ),
            _questions(),
            _canonical_catalogue(),
            "duplicate_case_id",
        ),
        (
            Snapshot(
                "r",
                (
                    _case(
                        "unknown-q",
                        _profile("diagnosis/ACL"),
                        (Call("Mystery", 1, "source"),),
                    ),
                ),
            ),
            _questions(),
            _canonical_catalogue(),
            "unknown_question",
        ),
        (
            Snapshot("r", ()),
            (_questions()[0], _questions()[0]),
            ("acl",),
            "duplicate_question_id",
        ),
        (
            Snapshot("r", ()),
            _questions(),
            ("acl", "acl"),
            "duplicate_object_name",
        ),
        (
            Snapshot("r", ()),
            _questions(),
            ("acl", 7),
            "invalid_object_name",
        ),
    ],
)
def test_invalid_or_duplicate_inputs_have_named_errors(
    snapshot: object,
    questions: object,
    catalogue: object,
    error: str,
) -> None:
    with pytest.raises(CoverageError, match=error):
        coverage_for_snapshot(snapshot, questions, catalogue)


def test_unknown_question_subject_and_malformed_case_calls_are_named() -> None:
    catalogue = _canonical_catalogue()
    malformed = (
        (
            _case("unknown-subject", _profile("diagnosis/Mystery")),
            "unknown_question_subject",
        ),
        (
            Case(
                "bad-calls",
                "study-1",
                _profile("diagnosis/ACL"),
                [],
                "teaching-r1",
            ),
            "invalid_case_calls",
        ),
        (
            _case(
                "duplicate-call",
                _profile("diagnosis/ACL"),
                (
                    Call("ACL", 1, "source-a"),
                    Call("ACL", -1, "source-b"),
                ),
            ),
            "duplicate_case_question_call",
        ),
        (
            _case(
                "bad-digit",
                _profile("diagnosis/ACL"),
                (Call("ACL", True, "source"),),
            ),
            "invalid_call_digit",
        ),
    )
    for case, error in malformed:
        with pytest.raises(CoverageError, match=error):
            coverage_for_snapshot(Snapshot("r", (case,)), _questions(), catalogue)


def test_association_decision_keeps_positive_and_negative_signs_distinct() -> None:
    question_subjects = {"ACL": "diagnosis/ACL"}
    positive = _association_decision(
        "diagnosis/ACL",
        [{"question_id": "ACL", "digit": 1, "source": "teacher"}],
        question_subjects,
    )
    negative = _association_decision(
        "diagnosis/ACL",
        [{"question_id": "ACL", "digit": -1, "source": "teacher"}],
        question_subjects,
    )

    assert positive == {
        "code": "associated",
        "associations": [{"question_id": "ACL", "digit": 1, "call_source": "teacher"}],
    }
    assert negative == {
        "code": "associated",
        "associations": [{"question_id": "ACL", "digit": -1, "call_source": "teacher"}],
    }


def test_association_decision_keeps_silence_separate_from_negative() -> None:
    question_subjects = {"ACL": "diagnosis/ACL"}

    explicit_silence = _association_decision(
        "diagnosis/ACL",
        [{"question_id": "ACL", "digit": 0, "source": "abstaining-teacher"}],
        question_subjects,
    )
    no_call_with_known_subject = _association_decision(
        "diagnosis/ACL", [], question_subjects
    )
    unassociated_object_without_call = _association_decision(
        "femur", [], question_subjects
    )

    assert explicit_silence["associations"][0]["digit"] == 0
    assert no_call_with_known_subject == {
        "code": "associated",
        "associations": [{"question_id": "ACL", "digit": 0, "call_source": None}],
    }
    assert unassociated_object_without_call == {
        "code": "unassociated",
        "associations": [],
    }
    assert unassociated_object_without_call != no_call_with_known_subject


def test_association_decision_refuses_unknown_and_duplicate_question_calls() -> None:
    question_subjects = {"ACL": "diagnosis/ACL"}

    assert (
        _association_decision(
            "diagnosis/ACL",
            [{"question_id": "Mystery", "digit": 1, "source": "teacher"}],
            question_subjects,
        )["code"]
        == "unknown_question"
    )
    assert (
        _association_decision(
            "diagnosis/ACL",
            [
                {"question_id": "ACL", "digit": 1, "source": "teacher"},
                {"question_id": "ACL", "digit": -1, "source": "second-teacher"},
            ],
            question_subjects,
        )["code"]
        == "duplicate_case_question_call"
    )


def test_association_decision_names_invalid_call_shapes_and_sources() -> None:
    question_subjects = {"ACL": "diagnosis/ACL"}

    assert _association_decision("diagnosis/ACL", None, question_subjects) == {
        "code": "invalid_case_calls",
        "associations": [],
    }
    assert _association_decision(
        "diagnosis/ACL", ["not-a-call"], question_subjects
    ) == {
        "code": "invalid_case_call",
        "associations": [],
    }
    for source in (None, "", " ", 0):
        assert _association_decision(
            "diagnosis/ACL",
            [{"question_id": "ACL", "digit": 1, "source": source}],
            question_subjects,
        ) == {
            "code": "invalid_call_source",
            "question_id": "ACL",
            "associations": [],
        }
