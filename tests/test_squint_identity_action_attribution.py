"""An identity look teaches its own result, never a later aggregate decision."""

from __future__ import annotations

import copy

import pytest
from test_train_ready_repairs_intent import BANK, OTHER_UID, experience

from knee.diagnosis import squint_identity, squint_pipeline
from knee.diagnosis.squint_procedure_memory import (
    _row_category,
    build_call_index,
    experience_rows,
    identity_state,
    recall_procedure_experiences,
    retain_procedure_experiences,
)


def action(*, read_as=True):
    return {
        "attribution_scope": "single_procedure",
        "before_state": {"outcome": "signed_conflict", "scale": "10mm"},
        "after_state": {"outcome": "recognized_in_context", "scale": "joint"},
        "after_identity_consumption": {
            "region_read_as_subject": read_as,
            "identity_effect": "answers"
            if read_as is True
            else "appearance_opposed"
            if read_as is False
            else "signed_conflict",
        },
    }


def test_identity_action_uses_its_own_consumption_not_the_final_aggregate():
    observation = action()
    final = {
        "identity_consumption": {
            "objects": {"femur": {"region_read_as_subject": False}}
        }
    }
    state = identity_state(final, "femur", observation)
    assert state["attribution_scope"] == "single_procedure"
    assert state["consumed"]["region_read_as_subject"] is True
    assert state["changed"] is True
    row = experience(direct=True)
    row["state"] = state
    row["independent_outcome"] = {
        "status": "checked",
        "evidence": [{"call": "confirm"}],
    }
    assert _row_category(row, "bounded_zoom")[0] == "confirmed_resolution"
    row["independent_outcome"]["evidence"] = [{"call": "reject"}]
    assert _row_category(row, "bounded_zoom")[0] == "contradicted_outcome"


@pytest.mark.parametrize(
    "missing", ["before_state", "after_state", "after_identity_consumption"]
)
def test_incomplete_snapshots_never_certify_an_identity_action(missing):
    observation = action()
    del observation[missing]
    state = identity_state({}, "femur", observation)
    assert state.get("attribution_scope") != "single_procedure"
    row = experience(direct=True)
    row["state"] = state
    assert _row_category(row, "bounded_zoom")[0] == "outcome_unattributed"


def test_unresolved_identity_action_does_not_borrow_a_later_resolution():
    observation = action(read_as=None)
    observation["after_state"]["outcome"] = "signed_conflict"
    state = identity_state({}, "femur", observation)
    assert state["changed"] is False
    row = experience(direct=True)
    row["state"] = state
    row["independent_outcome"] = {
        "status": "checked",
        "evidence": [{"call": "confirm"}],
    }
    assert _row_category(row, "bounded_zoom")[0] == "obtained_reading_open"


@pytest.mark.parametrize("call", ["confirm", "reject"])
def test_withheld_disputed_support_is_not_a_negative_identity_answer(call):
    observation = action(read_as=False)
    observation["after_identity_consumption"]["identity_effect"] = "signed_conflict"
    state = identity_state({}, "femur", observation)
    row = experience(direct=True)
    row["state"] = state
    row["independent_outcome"] = {"status": "checked", "evidence": [{"call": call}]}
    category, _info, agreement = _row_category(row, "bounded_zoom")
    assert category == "obtained_reading_open"
    assert agreement["status"] == "unresolved_after_action"
    assert agreement["after_answer"] is None


def test_export_keeps_each_identity_looks_own_answer_and_review_scope():
    from test_squint_procedure_memory import SOURCE, look_record, memory_with_calls

    record = look_record()
    first = record["observations"][0]
    first.update(action())
    first["before_cue"] = {"banks": {BANK: [2, 0, 1]}}
    second = copy.deepcopy(first)
    second.update(action(read_as=False))
    record["observations"].append(second)
    rows = experience_rows(
        record, SOURCE, labels={}, call_index=build_call_index(memory_with_calls())
    )
    assert len(rows) == 2
    assert rows[0]["state"]["consumed"]["region_read_as_subject"] is True
    assert rows[1]["state"]["consumed"]["region_read_as_subject"] is False
    assert rows[0]["independent_outcome"]["scope"] == "reviewed_views"
    assert rows[0]["context"]["subject"]["observed_cue"]["provenance"] == (
        "recorded_before_procedure"
    )
    assert _row_category(rows[0], "bounded_zoom")[0] == "confirmed_resolution"
    assert _row_category(rows[1], "bounded_zoom")[0] == "contradicted_outcome"


def test_real_infer_study_handoff_exports_the_identity_action_snapshots(monkeypatch):
    from test_squint_pipeline_identity_consumption_intent import (
        FEMUR_2,
        NOT_FEMUR_10,
        bones,
        femur_left_open,
        finer_look,
        joint_memory,
        placed,
        run_study,
    )

    finer_look(monkeypatch, {"femur": FEMUR_2})
    record, _ = run_study(
        monkeypatch,
        joint_memory(),
        bones(placed("femur", NOT_FEMUR_10)),
        femur_left_open,
    )
    observed = [
        o
        for o in record["observations"]
        if o.get("requested_by") == "identity_question"
    ]
    assert len(observed) == 1
    state = identity_state(record, "femur", observed[0])
    assert state["attribution_scope"] == "single_procedure"
    assert observed[0]["before_cue"]["banks"]
    assert state["before"]["outcome"] is not None
    assert state["after"]["outcome"] is not None


def test_identity_producer_records_before_cue_and_its_single_finer_result(monkeypatch):
    coarse = {
        "schema": squint_identity.RECALL_CONTEXT_SCHEMA,
        "identity": "femur",
        "identity_basis": "prior_only",
        "outcome": squint_identity.SIGNED_CONFLICT,
        "applicable_negative_case_ids": ["negative"],
        "case_comparisons": {"large_profile": "retained in the main recall only"},
    }
    resolved = {
        **coarse,
        "scale": squint_identity.JOINT_SCALE,
        "outcome": "recognized_in_context",
        "applicable_negative_case_ids": [],
        "squint_scale_negatives": {
            "negative": squint_identity.NEGATIVE_COMPARED_NOT_APPLYING
        },
    }
    objects = {"femur": {"status": "located", "profile": {"banks": {BANK: [2, 0, 1]}}}}
    observations = []

    def look(_request, _study, current, _attempted, _deadline):
        current["femur"]["profile"]["banks"][BANK][0] = 99
        current["femur"]["profile"]["has_fine"] = True
        return {"code": "measured", "subject": "femur"}

    monkeypatch.setattr(squint_pipeline, "_bounded_observation", look)
    monkeypatch.setattr(
        squint_pipeline, "holds_scale", lambda p, _scale: bool(p.get("has_fine"))
    )
    monkeypatch.setattr(
        squint_identity, "recall_identity", lambda *_args, **_kwargs: resolved
    )
    monkeypatch.setattr(
        squint_pipeline,
        "_object_consumption",
        lambda *_args, **_kwargs: {"region_read_as_subject": True},
    )
    squint_pipeline._resolve_identity_contests(
        objects,
        {},
        {},
        None,
        {"outcome": "examined", "objects": {"femur": coarse}},
        {},
        set(),
        observations,
        None,
        {"prepared": True},
    )
    assert len(observations) == 1
    obs = observations[0]
    assert obs["before_cue"]["banks"][BANK] == [2, 0, 1]
    assert obs["before_state"]["outcome"] == squint_identity.SIGNED_CONFLICT
    assert obs["after_state"]["outcome"] == "recognized_in_context"
    assert "case_comparisons" not in obs["before_state"]
    assert "case_comparisons" not in obs["after_state"]
    resolved["outcome"] = "later_changed"
    assert obs["after_state"]["outcome"] == "recognized_in_context"
    assert identity_state({}, "femur", obs)["attribution_scope"] == "single_procedure"


@pytest.mark.parametrize("field", ["reason", "location_status"])
def test_query_inapplicable_failure_cannot_suppress_partial_context_success(field):
    success = experience(direct=True)
    success["request"].pop("reason")
    failure = copy.deepcopy(success)
    failure["row_id"] = "inapplicable-failure"
    failure["independent_outcome"]["call"] = -1
    query = {}
    if field == "reason":
        failure["request"]["reason"] = "different-reason"
        query["request_reason"] = "current-reason"
    else:
        failure["context"]["subject"]["location_status"] = "not_located"
        query["location_status"] = "located"
    memory = retain_procedure_experiences(
        {"revision": "parent", "cases": []}, [success, failure]
    )
    recalled = recall_procedure_experiences(
        memory,
        question="ACL",
        subject="acl",
        kind="bounded_zoom",
        query_profile={"banks": {BANK: [2, 0, 1]}},
        query_context=query,
        study_uid=OTHER_UID,
        exclude_same_study=True,
    )
    assert recalled["status"] == "recalled_confirmed_resolution"
    assert recalled["confirmed_resolution_row_ids"] == [success["row_id"]]
    assert recalled["context_mismatch_row_ids"] == [failure["row_id"]]


def test_applicable_failure_still_opposes_a_partial_context_success():
    success = experience(direct=True)
    success["request"].pop("reason")
    failure = copy.deepcopy(success)
    failure["row_id"] = "applicable-failure"
    failure["request"]["reason"] = "current-reason"
    failure["independent_outcome"]["call"] = -1
    memory = retain_procedure_experiences(
        {"revision": "parent", "cases": []}, [success, failure]
    )
    recalled = recall_procedure_experiences(
        memory,
        question="ACL",
        subject="acl",
        kind="bounded_zoom",
        query_profile={"banks": {BANK: [2, 0, 1]}},
        query_context={"request_reason": "current-reason"},
        study_uid=OTHER_UID,
        exclude_same_study=True,
    )
    assert recalled["status"] != "recalled_confirmed_resolution"
    assert recalled["confirmed_resolution_row_ids"] == []
