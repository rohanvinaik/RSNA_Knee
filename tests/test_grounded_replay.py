"""Saved evidence may be reused; changed identity expertise cannot be hidden."""

import copy

import pytest

from scripts.grounded_replay import identity_reuse_code, teaching_inputs


def test_condition_configurations_can_change_without_relabeling_identity():
    old = {"cases": [{"subject": "femur", "profile": {"banks": {}}}]}
    new = {**old, "cases": [*old["cases"], {"subject": "diagnosis/Fracture"}]}
    assert identity_reuse_code(old, new) == "identity_inputs_unchanged"


def test_changed_signed_negative_refuses_identity_reuse():
    old = {"cases": [], "object_identity_cases": {"cases": [{"digit": -1}]}}
    new = {**old, "object_identity_cases": {"cases": []}}
    assert identity_reuse_code(old, new) == "identity_teaching_changed"


def test_changed_measured_object_refuses_identity_reuse():
    old = {"cases": [{"subject": "femur", "profile": {"banks": {}}}]}
    new = {"cases": [{"subject": "femur", "profile": {"banks": {"new": [1, 0, 0]}}}]}
    assert identity_reuse_code(old, new) == "identity_cases_changed"


def test_teaching_input_does_not_promote_an_unconfirmed_object():
    m = {
        "cases": [
            {
                "case_id": "a",
                "subject": "acl",
                "study_uid": "s",
                "profile": {"banks": {}},
                "regions": [],
            }
        ],
        "object_identity_teaching": {
            "schema": "knee.object-identity-teaching/v1",
            "confirmed_case_ids": [],
            "calls": [],
        },
    }
    own, refs = teaching_inputs(m)
    assert own == {}
    assert refs == {}


def test_teaching_views_are_not_widened_by_held_region_addresses():
    m = {
        "cases": [
            {
                "case_id": "a",
                "subject": "acl",
                "study_uid": "s",
                "profile": {"banks": {}},
                "regions": [
                    {
                        "view": {
                            "orientation": "Sagittal",
                            "fluid_sensitive": "1",
                            "fat_suppression": "1",
                        }
                    },
                    {
                        "view": {
                            "orientation": "Coronal",
                            "fluid_sensitive": "1",
                            "fat_suppression": "1",
                        }
                    },
                ],
            }
        ],
        "object_identity_teaching": {
            "schema": "knee.object-identity-teaching/v1",
            "confirmed_case_ids": ["a"],
            "calls": [
                {
                    "candidate_id": "a",
                    "call": "confirm",
                    "views": [["Sagittal", "1", "1"]],
                }
            ],
        },
    }
    own, _ = teaching_inputs(m)
    assert len(own["s"]["acl"]["regions"]) == 1
    assert own["s"]["acl"]["regions"][0]["view"]["orientation"] == "Sagittal"
    duplicate = copy.deepcopy(m["cases"][0])
    duplicate["case_id"] = "b"
    m["cases"].append(duplicate)
    m["object_identity_teaching"]["confirmed_case_ids"].append("b")
    m["object_identity_teaching"]["calls"].append(
        {"candidate_id": "b", "call": "confirm"}
    )
    with pytest.raises(ValueError, match="canonical_teaching_object_ambiguous"):
        teaching_inputs(m)
