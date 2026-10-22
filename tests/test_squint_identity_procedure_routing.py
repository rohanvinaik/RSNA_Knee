"""Resolver/selector integration with fixture experiences, not a patient-transfer claim."""

from __future__ import annotations

import pytest

from knee.diagnosis import squint_identity as identity
from knee.diagnosis import squint_pipeline as pipeline
from knee.diagnosis.squint_interfaces import territory_bank_name
from knee.diagnosis.squint_pipeline import _resolve_identity_contests
from knee.diagnosis.squint_procedure_memory import SCHEMA, retain_procedure_experiences

TEACHER = "fixture-teacher"
QUERY = "fixture-query"
VIEW = {
    "orientation": "sagittal",
    "fluid_sensitive": "false",
    "fat_suppression": "false",
}
COARSE = territory_bank_name(VIEW, "object", "signal_median", "overview", 10.0)
FINE = territory_bank_name(VIEW, "object", "signal_median", "overview", 2.0)


def retained_experience(*, reason=None, result="confirmed"):
    read_as = {"confirmed": True, "contradicted": False, "open": None}[result]
    row = {
        "schema": SCHEMA,
        "row_id": "fixture-identity-look",
        "source": {
            "run": "fixture-run",
            "record_file": "fixture-record.json",
            "record_sha256": "a" * 64,
            "memory_sha256": "b" * 64,
            "memory_revision": "fixture-parent",
            "study_uid": TEACHER,
        },
        "request": {
            "question": "identity",
            "subject": "femur",
            "kind": "bounded_zoom",
            "reason": reason or identity.CONTESTED_AT_SQUINT_SCALE,
        },
        "execution": {
            "status": "ran_new_reading",
            "new_reading": True,
            "reading_available": True,
        },
        "context": {
            "subject": {
                "location_status": "located",
                "observed_cue": {
                    "banks": {COARSE: [2, 0, 1]},
                    "provenance": "recorded_before_procedure",
                },
            }
        },
        "state": {
            "scope": "identity",
            "attribution_scope": "single_procedure",
            "before": {"outcome": "appearance_opposed"},
            "after": {"outcome": "appearance_supported"},
            "consumed": {
                "identity_effect": "answers",
                "region_read_as_subject": read_as,
            },
        },
        "independent_outcome": {"status": "checked", "evidence": [{"call": "confirm"}]},
    }
    return retain_procedure_experiences(
        {"revision": "fixture-parent", "cases": []}, [row]
    )


@pytest.fixture
def world(monkeypatch):
    order = []
    objects = {
        name: {
            "status": "located",
            "profile": {"subject": name, "banks": {COARSE: [2, 0, 1]}},
        }
        for name in ("acl", "femur")
    }
    readings = {
        "outcome": "examined",
        "objects": {
            name: {
                "schema": identity.RECALL_CONTEXT_SCHEMA,
                "scale": identity.SQUINT_SCALE,
                "identity": name,
                "identity_basis": identity.STRUCTURAL_READER,
                "outcome": "appearance_opposed",
                "applicable_negative_case_ids": ["fixture-negative"],
            }
            for name in objects
        },
    }

    def finer(request, study, located, attempted, deadline):
        name = request["object"]
        order.append(name)
        located[name]["profile"]["banks"][FINE] = [2, 0, 1]
        return {"subject": name, "code": "measured", "regions": []}

    def compare(profile, memory, **kwargs):
        return {
            "schema": identity.RECALL_CONTEXT_SCHEMA,
            "scale": identity.JOINT_SCALE,
            "identity": profile["subject"],
            "identity_basis": identity.STRUCTURAL_READER,
            "outcome": "appearance_supported",
            "applicable_negative_case_ids": [],
            "squint_scale_negatives": {
                "fixture-negative": identity.NEGATIVE_COMPARED_NOT_APPLYING
            },
        }

    monkeypatch.setattr(pipeline, "_bounded_observation", finer)
    monkeypatch.setattr(identity, "recall_identity", compare)
    monkeypatch.setattr(
        pipeline,
        "_object_consumption",
        lambda *a, **k: {"identity_effect": "answers", "region_read_as_subject": True},
    )
    return {
        "objects": objects,
        "study": {"study_uid": QUERY},
        "identity_readings": readings,
        "contexts": {},
        "attempted": set(),
        "observations": [],
        "deadline": None,
        "prepared_resolved": {},
    }, order


def test_learned_identity_look_is_promoted_and_all_required_looks_still_run(world):
    arguments, order = world
    memory = retained_experience()
    states = _resolve_identity_contests(memory=memory, excluded_uid=QUERY, **arguments)
    assert order == ["femur", "acl"]
    assert set(states) == {"femur", "acl"}
    assert all(
        state["resolved"]["outcome"] == "appearance_supported"
        for state in states.values()
    )
    assert all(
        state["resolution"]["status"] == identity.RESOLVED_BY_FINER_READING
        for state in states.values()
    )
    observations = arguments["observations"]
    assert (
        observations[0]["recalled_procedure"]["status"]
        == "recalled_confirmed_resolution"
    )
    assert observations[0]["recalled_procedure"]["confirmed_resolution_row_ids"] == [
        "fixture-identity-look"
    ]
    assert all(row["attribution_scope"] == "single_procedure" for row in observations)
    assert all(
        row["before_cue"]["banks"] == {COARSE: [2, 0, 1]} for row in observations
    )


@pytest.mark.parametrize("control", ["different_context", "same_study"])
def test_inapplicable_or_self_study_experience_does_not_reorder_required_looks(
    world, control
):
    arguments, order = world
    memory = retained_experience(
        reason="different_context" if control == "different_context" else None
    )
    excluded_uid = TEACHER if control == "same_study" else QUERY
    arguments["study"]["study_uid"] = excluded_uid
    states = _resolve_identity_contests(
        memory=memory, excluded_uid=excluded_uid, **arguments
    )
    assert order == ["acl", "femur"]
    assert set(states) == {"acl", "femur"}
    assert all(
        row.get("recalled_procedure", {}).get("status")
        != "recalled_confirmed_resolution"
        for row in arguments["observations"]
    )


@pytest.mark.parametrize("result", ["contradicted", "open"])
def test_negative_or_open_experience_cannot_cancel_a_required_identity_look(
    world, result
):
    arguments, order = world
    memory = retained_experience(result=result)
    states = _resolve_identity_contests(memory=memory, excluded_uid=QUERY, **arguments)
    assert order == ["acl", "femur"]
    assert set(states) == {"acl", "femur"}
    assert all(row["code"] == "measured" for row in arguments["observations"])
    expected = (
        "recalled_outcome_contradicted"
        if result == "contradicted"
        else "recalled_reading_obtained_open"
    )
    assert arguments["observations"][1]["recalled_procedure"]["status"] == expected
