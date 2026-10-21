"""Intent at the existing teaching and identity boundaries, in both signs.

These are recognition tests, not evidence that automated growth is complete.
In particular, an unknown anatomical check may leave identity recall neutral;
that does not authorize the growth publisher to admit the observation.
"""

from __future__ import annotations

import copy

import pytest

from knee.diagnosis.squint_bootstrap import (
    CALLS_SCHEMA,
    REVIEW_SCHEMA,
    SquintBootstrapError,
    validate_calls,
)
from knee.diagnosis.squint_identity import recall_identity

SAGITTAL = ["Sagittal", "0", "0"]
CORONAL = ["Coronal", "0", "0"]
SAGITTAL_BANK = (
    'squint/v2/view=["Sagittal","0","0"]/role=object/'
    "metric=signal/direction=whole/scale=10mm"
)
CORONAL_BANK = (
    'squint/v2/view=["Coronal","0","0"]/role=object/'
    "metric=signal/direction=whole/scale=10mm"
)
REVIEW_PIN = "a" * 64


def _profile(counts, *, subject="femur", banks=None):
    return {
        "subject": subject,
        "banks": {CORONAL_BANK: list(counts)} if banks is None else banks,
        "source": {"procedure": "intent-fixture-procedure-v1"},
    }


def _case(case_id, subject, study_uid, counts, *, banks=None):
    return {
        "case_id": case_id,
        "subject": subject,
        "study_uid": study_uid,
        "profile": _profile(counts, subject=subject, banks=banks),
    }


@pytest.fixture
def identity_memory():
    return {
        "cases": [
            _case("femur-teacher", "femur", "teacher-f", (4, 0, 0)),
            _case("tibia-teacher", "tibia", "teacher-t", (0, 4, 0)),
        ],
        "object_identity_teaching": {
            "schema": "knee.object-identity-teaching/v1",
            "confirmed_case_ids": ["femur-teacher", "tibia-teacher"],
            "calls": [
                {"candidate_id": "femur-teacher", "call": "confirm"},
                {"candidate_id": "tibia-teacher", "call": "confirm"},
            ],
        },
    }


@pytest.fixture
def review_and_calls():
    review = {
        "schema": REVIEW_SCHEMA,
        "source_manifest_sha256": "b" * 64,
        "candidates": [
            {
                "candidate_id": "candidate-f",
                "case_id": "candidate-f",
                "study_uid": "query-study",
                "subject": "femur",
                "profile_sha256": "c" * 64,
                "source_product_sha256": "d" * 64,
                "full_profile": {
                    "payload_ref": "payload-f",
                    "context_ref": "context-f",
                    "product_record_sha256": "e" * 64,
                },
                "profile_views": [SAGITTAL, CORONAL],
                "evidence": {
                    "panels": [
                        {
                            "view": {
                                "orientation": view[0],
                                "fluid_sensitive": view[1],
                                "fat_suppression": view[2],
                            },
                            "image_state": "read",
                            "support_state": "drawn",
                        }
                        for view in (SAGITTAL, CORONAL)
                    ]
                },
            }
        ],
    }
    calls = {
        "schema": CALLS_SCHEMA,
        "review_sha256": REVIEW_PIN,
        "reader": "independent-picture-reader",
        "calls": [
            {
                "candidate_id": "candidate-f",
                "call": "confirm",
                "notes": "The coronal picture establishes femur identity.",
                "views": [CORONAL],
            }
        ],
    }
    return review, calls


def test_unknown_anatomy_does_not_turn_recognized_identity_into_a_negative(
    identity_memory,
):
    result = recall_identity(
        _profile((4, 0, 0)),
        identity_memory,
        sanity={
            "schema": "knee.object-anatomical-sanity/v1",
            "status": "unknown",
            "identity_assertion": None,
        },
    )

    assert result["outcome"] == "identified"
    assert result["identity"] == "femur"
    assert result["sanity"] == {"status": "unknown"}
    assert result["speaking_identities"] == ["femur"]
    # The unknown-admission policy belongs to the publisher, not this assertion.


def test_unknown_anatomy_cannot_supply_missing_identity_evidence(identity_memory):
    result = recall_identity(
        _profile((0, 0, 4)),
        identity_memory,
        sanity={
            "schema": "knee.object-anatomical-sanity/v1",
            "status": "unknown",
            "identity_assertion": None,
        },
    )

    assert result["outcome"] == "unresolved_no_precedent"
    assert result["identity"] is None
    assert result["admitted"] is False
    assert result["speaking_identities"] == []
    assert {case["identity"] for case in result["cases"]} == {"femur", "tibia"}


def test_known_anatomical_contradiction_blocks_identity_without_erasing_recall(
    identity_memory,
):
    result = recall_identity(
        _profile((4, 0, 0)),
        identity_memory,
        sanity={
            "schema": "knee.object-anatomical-sanity/v1",
            "status": "contradicted",
            "identity_assertion": None,
        },
    )

    assert result["outcome"] == "blocked_by_sanity"
    assert result["reason"] == "sanity_contradicted"
    assert result["blocked_identity"] == "femur"
    assert result["identity"] is None
    assert result["admitted"] is False
    assert result["speaking_identities"] == ["femur"]
    assert any(case["case_id"] == "femur-teacher" for case in result["cases"])


def test_confirmed_visual_call_keeps_only_the_called_views(review_and_calls):
    review, calls = review_and_calls
    before = copy.deepcopy((review, calls))

    result = validate_calls(review, calls, REVIEW_PIN)

    assert result["outcome"] == "valid"
    assert result["confirmed_case_ids"] == ["candidate-f"]
    assert result["calls"][0]["views"] == [CORONAL]
    assert SAGITTAL not in result["calls"][0]["views"]
    assert (review, calls) == before


def test_rejected_visual_call_does_not_reject_an_uncalled_view(review_and_calls):
    review, calls = review_and_calls
    calls["calls"][0].update(call="reject", views=[SAGITTAL])

    result = validate_calls(review, calls, REVIEW_PIN)

    assert result["outcome"] == "valid"
    assert result["confirmed_case_ids"] == []
    assert result["calls"][0]["call"] == "reject"
    assert result["calls"][0]["views"] == [SAGITTAL]
    assert CORONAL not in result["calls"][0]["views"]


def test_invalid_view_scope_is_refused_instead_of_becoming_a_whole_case_call(
    review_and_calls,
):
    review, calls = review_and_calls
    calls["calls"][0]["views"] = []

    with pytest.raises(SquintBootstrapError) as error:
        validate_calls(review, calls, REVIEW_PIN)

    assert error.value.code == "call_views_invalid"
    assert calls["calls"][0]["views"] == []


def test_uncalled_seed_view_cannot_speak_for_identity(identity_memory):
    identity_memory["cases"][0]["profile"]["banks"][SAGITTAL_BANK] = [4, 0, 0]
    identity_memory["cases"][1]["profile"]["banks"][SAGITTAL_BANK] = [0, 4, 0]
    identity_memory["object_identity_teaching"]["calls"][0]["views"] = [CORONAL]

    result = recall_identity(
        _profile((4, 0, 0), banks={SAGITTAL_BANK: [4, 0, 0]}),
        identity_memory,
    )

    assert result["identity"] is None
    assert result["admitted"] is False
    assert [case["case_id"] for case in result["cases"]] == ["tibia-teacher"]
    assert all(
        case["common_speaking_banks"] == [SAGITTAL_BANK] for case in result["cases"]
    )


def test_a_study_cannot_teach_its_own_identity_comparison(identity_memory):
    result = recall_identity(
        _profile((4, 0, 0)), identity_memory, exclude_study_uid="teacher-f"
    )

    assert result["outcome"] == "proposal"
    assert result["reason"] == "no_compatible_opposing_case"
    assert result["identity"] is None
    assert result["admitted"] is False
    assert [case["case_id"] for case in result["cases"]] == ["tibia-teacher"]
    assert result["cases"][0]["envelope"] is None


def test_clinical_labels_do_not_change_an_identity_answer(identity_memory):
    identity_memory["cases"][0]["condition_calls"] = {"ACL": 1}
    identity_memory["cases"][0]["presentation_scope"] = {
        "ACL": "positive_condition_presentation"
    }
    negative_label_memory = copy.deepcopy(identity_memory)
    negative_label_memory["cases"][0]["condition_calls"] = {"ACL": 0}
    negative_label_memory["cases"][0]["presentation_scope"] = {
        "ACL": "negative_condition_presentation"
    }

    positive_label_result = recall_identity(_profile((4, 0, 0)), identity_memory)
    negative_label_result = recall_identity(_profile((4, 0, 0)), negative_label_memory)

    assert positive_label_result == negative_label_result
    assert positive_label_result["outcome"] == "identified"
    assert positive_label_result["identity"] == "femur"
    assert "condition_calls" not in positive_label_result
    assert "diagnosis" not in positive_label_result


def test_visual_identity_call_cannot_smuggle_in_a_clinical_verdict(review_and_calls):
    review, calls = review_and_calls
    calls["calls"][0]["condition_calls"] = {"ACL": 1}

    with pytest.raises(SquintBootstrapError) as error:
        validate_calls(review, calls, REVIEW_PIN)

    assert error.value.code == "calls_malformed"
