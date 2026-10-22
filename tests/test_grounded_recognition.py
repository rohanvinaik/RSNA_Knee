"""Explicit teaching enters recall without changing scopes or erasing expertise."""

import copy

import pytest

from knee.diagnosis.squint_configurations import (
    ConfigurationProfileError,
    configuration_role_cases,
)
from knee.study.tables import LABELS
from scripts.grounded_recognition import extend_references, outcome_against_call


def inputs():
    reference = {
        "case_id": "reference",
        "study_uid": "study-x",
        "subject": "acl",
        "profile": {"schema": "knee.squint-profile/v1", "banks": {}},
        "regions": [],
        "condition_calls": {"ACL": -1},
        "teaching_source": {"official_row": {"ACL": "0"}},
        "source": {},
        "identity_call": {
            "candidate_id": "reference",
            "call": "confirm",
            "reader": "reviewer",
            "views": [["Sagittal", "1", "1"]],
        },
    }
    workset = {
        "schema": "knee.grounded-reference-workset/v1",
        "spec_sha256": "b" * 64,
        "spec": {"source_memory_sha256": "a" * 64},
        "cases": [reference],
    }
    old = copy.deepcopy(reference)
    old["case_id"] = "old-object"
    old["condition_calls"] = {}
    parent = {
        "schema": "knee.squint-memory/v1",
        "revision": "parent",
        "questions": list(LABELS),
        "cases": [old],
        "object_identity_teaching": {
            "schema": "knee.object-identity-teaching/v1",
            "confirmed_case_ids": ["old-object"],
            "calls": [{**reference["identity_call"], "candidate_id": "old-object"}],
        },
        "object_identity_cases": {
            "schema": "preserved",
            "cases": [{"negative": "keep me"}],
        },
    }
    return parent, workset


def test_unknown_and_missing_answers_never_become_normal():
    assert outcome_against_call("open", 0) == "unresolved"
    assert outcome_against_call("unresolved_conflict", 1) == "unresolved"
    assert outcome_against_call("absent", None) == "unlabeled"


def test_actual_positive_and_negative_answers_are_checked_both_ways():
    assert outcome_against_call("assigned", 1) == "identified"
    assert outcome_against_call("assigned", 0) == "wrong"
    assert outcome_against_call("defeated", 0) == "identified"
    assert outcome_against_call("defeated", 1) == "wrong"


def test_reference_is_not_a_second_canonical_object():
    parent, workset = inputs()
    before = copy.deepcopy(parent)
    child = extend_references(parent, workset, workset["spec"]["source_memory_sha256"])
    assert parent == before
    assert child["cases"][0] == before["cases"][0]
    assert child["object_identity_cases"] == before["object_identity_cases"]
    assert configuration_role_cases(child["cases"]) == parent["cases"]
    assert child["cases"][1]["condition_calls"] == {"ACL": -1}
    assert (
        child["object_identity_teaching"]["calls"][-1]["views"]
        == workset["cases"][0]["identity_call"]["views"]
    )


def test_stale_parent_does_not_receive_reference_cases():
    parent, workset = inputs()
    with pytest.raises(ValueError, match="reference_parent_pin_stale"):
        extend_references(parent, workset, "0" * 64)


def test_no_reference_call_is_created_without_scoped_visual_confirmation():
    parent, workset = inputs()
    workset["cases"][0]["identity_call"]["views"] = []
    with pytest.raises(ValueError, match="scoped_visual_confirmation_required"):
        extend_references(parent, workset, workset["spec"]["source_memory_sha256"])


def test_reference_cannot_change_its_independent_source_label():
    parent, workset = inputs()
    workset["cases"][0]["condition_calls"]["ACL"] = 1
    with pytest.raises(ValueError, match="reference_official_call_mismatch"):
        extend_references(parent, workset, workset["spec"]["source_memory_sha256"])


def test_a_question_reference_never_disappears_as_an_unmarked_duplicate():
    a = {"case_id": "a", "subject": "acl"}
    b = {"case_id": "b", "subject": "acl"}
    assert configuration_role_cases([a, b]) == [a, b]


def test_malformed_reference_marker_is_refused_not_ignored():
    with pytest.raises(ConfigurationProfileError):
        configuration_role_cases(
            [{"question_reference": {}, "condition_calls": {"ACL": -1}}]
        )


def test_question_reference_preserves_canonical_role_in_actual_condition_reader():
    from knee.diagnosis.squint_configurations import (
        rebuild_study_configurations,
        with_configuration_cases,
    )
    from knee.diagnosis.squint_identity import identity_condition_views
    from knee.diagnosis.squint_interfaces import (
        TERRITORY_PROCEDURE,
        territory_bank_name,
    )
    from knee.diagnosis.squint_locator import _scoped_cases, recall_source_fingerprint

    parent, workset = inputs()
    name = territory_bank_name(
        {"orientation": "Sagittal", "fluid_sensitive": "1", "fat_suppression": "1"},
        "object",
        "signal_median",
        "overview",
        10.0,
    )
    for case in [parent["cases"][0], workset["cases"][0]]:
        case["profile"].update(
            subject="acl",
            source={"procedure": TERRITORY_PROCEDURE},
            banks={name: [1, 2, 3]},
        )
    parent["label_ledger"] = {"study-x": {"ACL": 0}}
    parent = with_configuration_cases(parent, procedure=TERRITORY_PROCEDURE)
    child = extend_references(parent, workset, workset["spec"]["source_memory_sha256"])
    scoped = _scoped_cases(child["cases"], identity_condition_views(child))
    configuration = next(c for c in scoped if c["subject"] == "diagnosis/ACL")
    assert configuration["profile"]["banks"]
    assert scoped[-1]["profile"]["banks"] == {name: [1, 2, 3]}
    rebuilt = rebuild_study_configurations(
        child, ["study-x"], built_by={"kind": "fixture"}
    )
    assert (
        rebuilt["cases"][0]["configuration_teaching"]["roles"]["acl"]["case_id"]
        == "old-object"
    )
    unmarked = copy.deepcopy(child)
    del unmarked["cases"][-1]["question_reference"]
    assert recall_source_fingerprint(unmarked) != recall_source_fingerprint(child)
    unmarked_scope = _scoped_cases(
        unmarked["cases"], identity_condition_views(unmarked)
    )
    assert (
        next(c for c in unmarked_scope if c["subject"] == "diagnosis/ACL")["profile"][
            "banks"
        ]
        == {}
    )


def test_actual_recall_aliases_preserve_both_signs():
    assert outcome_against_call("present", 1) == "identified"
    assert outcome_against_call("present", 0) == "wrong"
    assert outcome_against_call("absent", 0) == "identified"
    assert outcome_against_call("absent", 1) == "wrong"
