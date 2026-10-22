from __future__ import annotations

import copy
import json

from knee.diagnosis.squint_corpus import (
    object_state_from_labels,
    reviewed_object_buckets,
)
from knee.diagnosis.squint_memory import IMPLICATED_OBJECTS
from knee.study.tables import LABELS

SAG = ["Sagittal", "1", "1"]
COR = ["Coronal", "1", "1"]


def complete_labels(**changes):
    result = {question: 0 for question in LABELS}
    result.update(changes)
    return result


def bank(view, scale="10mm"):
    return (
        "squint/v2/view="
        + json.dumps(view, separators=(",", ":"))
        + f"/role=object/metric=signal/direction=d/scale={scale}"
    )


def identity_case(
    case_id="case-joint",
    uid="study-joint",
    subject="joint",
    views=(SAG,),
    banks=None,
):
    if banks is None:
        banks = {bank(SAG): [2, 0, 1]}
    return {
        "case_id": case_id,
        "study_uid": uid,
        "subject": subject,
        "condition_calls": {"Synovitis": -1},
        "presentation_scope": {"Synovitis": "normal_for_this_condition_only"},
        "question_reference": {
            "schema": "knee.question-reference/v1",
            "question": "Synovitis",
            "scope": "addressed site",
        },
        "profile": {
            "schema": "knee.squint-profile/v1",
            "subject": subject,
            "banks": banks,
            "source": {"procedure": "knee.squint-profile/scan-tercile-v1"},
        },
        "regions": [],
        "source": {"kind": "visual-review-fixture"},
        "full_profile": {"payload_ref": "retained-full-payload"},
        "full_profile_refs": {
            subject: {"payload_ref": "role-full-payload", "context_ref": "context-1"}
        },
    }


def memory(case=None, *, confirmed=True, call="confirm", views=(SAG,)):
    case = case or identity_case(views=views)
    cid = case["case_id"]
    return {
        "revision": "reviewed-r1",
        "cases": [case],
        "object_identity_teaching": {
            "schema": "knee.object-identity-teaching/v1",
            "reader": "reviewer",
            "confirmed_case_ids": [cid] if confirmed else [],
            "calls": [
                {
                    "candidate_id": cid,
                    "call": call,
                    "notes": "visually reviewed",
                    "views": [list(view) for view in views]
                    if views is not None
                    else None,
                }
            ],
            "negative_case_ids": ["signed-negative-1"],
            "negative_views": {"signed-negative-1": [SAG]},
        },
        "object_identity_cases": {
            "schema": "knee.object-identity-cases/v1",
            "cases": [{"case_id": "signed-negative-1", "call": "reject"}],
        },
    }


def test_unrelated_positive_condition_still_makes_unimplicated_object_normal():
    state = object_state_from_labels("joint", complete_labels(ACL=1))

    assert state["status"] == "normal"
    assert state["positive_questions"] == ["ACL"]
    assert state["implicated_positive"] == []
    assert state["implicated_unknown"] == []


def test_relevant_positive_is_a_condition_presentation_at_existing_scope():
    state = object_state_from_labels("femur", complete_labels(Contusion=1))

    assert state["status"] == "condition_presentation"
    assert state["implicated_positive"] == ["Contusion"]
    assert state["implicated_unknown"] == []


def test_all_negative_labels_make_the_object_normal():
    state = object_state_from_labels("femur", complete_labels())

    assert state["status"] == "normal"
    assert state["implicated_positive"] == []
    assert state["unknown_questions"] == []


def test_missing_row_or_required_label_never_becomes_normal():
    unlabelled = object_state_from_labels("femur", None)
    partial = complete_labels()
    del partial["ACL"]
    incomplete = object_state_from_labels("femur", partial)

    assert unlabelled["status"] == "unlabelled"
    assert "ACL" in unlabelled["implicated_unknown"]
    assert incomplete["status"] == "incomplete"
    assert incomplete["unknown_questions"] == ["ACL"]
    assert incomplete["implicated_unknown"] == ["ACL"]


def test_rejected_identity_is_not_added_to_any_object_bucket():
    rejected = memory(confirmed=False, call="reject")

    result = reviewed_object_buckets(
        rejected,
        {"study-joint": complete_labels()},
        {"kind": "official_labels", "sha256": "a" * 64},
    )

    assert result["outcome"] == "classified"
    assert result["buckets"] == {}
    assert result["scoped_records"] == []
    assert result["object_identity_cases"] is rejected["object_identity_cases"]


def test_missing_study_row_preserves_confirmed_identity_as_unlabelled():
    source = memory()

    result = reviewed_object_buckets(source, {}, "official-label-source")

    assert result["buckets"] == {"joint": {"unlabelled": ["case-joint"]}}
    [record] = result["scoped_records"]
    assert record["source_case_id"] == "case-joint"
    assert record["state"]["status"] == "unlabelled"
    assert record["identity_views"] == [SAG]
    assert record["case"]["profile"]["banks"] == source["cases"][0]["profile"]["banks"]


def test_confirmed_views_scope_all_exported_banks_and_preserve_original_records():
    original = identity_case(
        banks={
            bank(SAG): [2, 0, 1],
            bank(SAG, "2mm"): [3, 0, 2],
            bank(COR): [0, 4, 1],
        }
    )
    source = memory(original, views=(SAG,))
    before = copy.deepcopy(source)
    labels = complete_labels(ACL=1)

    result = reviewed_object_buckets(
        source,
        {"study-joint": labels},
        {"kind": "official_labels", "sha256": "b" * 64},
    )

    [record] = result["scoped_records"]
    scoped_case = record["case"]
    assert result["buckets"] == {"joint": {"normal": ["case-joint"]}}
    assert record["identity_views"] == [SAG]
    assert record["identity_call"]["views"] == [SAG]
    assert set(scoped_case["profile"]["banks"]) == {bank(SAG), bank(SAG, "2mm")}
    assert scoped_case["condition_calls"] == original["condition_calls"]
    assert scoped_case["presentation_scope"] == original["presentation_scope"]
    assert scoped_case["question_reference"] == original["question_reference"]
    assert scoped_case["full_profile"] == original["full_profile"]
    assert scoped_case["full_profile_refs"] == original["full_profile_refs"]
    assert result["object_identity_cases"] is source["object_identity_cases"]
    assert result["object_identity_teaching"] is source["object_identity_teaching"]
    assert source == before


def test_generic_meniscus_uses_medial_and_lateral_condition_sets():
    for question in sorted(
        set(IMPLICATED_OBJECTS["medial_meniscus"])
        | set(IMPLICATED_OBJECTS["lateral_meniscus"])
    ):
        state = object_state_from_labels("meniscus", complete_labels(**{question: 1}))

        assert state["status"] == "condition_presentation"
        assert state["implicated_positive"] == [question]
