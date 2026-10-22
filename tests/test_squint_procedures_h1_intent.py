from __future__ import annotations

from knee.diagnosis import squint_pipeline as pipeline
from knee.diagnosis import squint_procedures as procedures


def test_named_request_reaches_its_consumer_once_and_never_becomes_zoom(monkeypatch):
    calls = []
    monkeypatch.setitem(
        procedures._CONSUMERS,
        "locate_object_region",
        lambda call: calls.append(call.subject) or {"code": "located"},
    )
    monkeypatch.setattr(
        pipeline,
        "_bounded_observation",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("wrong action")),
    )
    attempted = set()
    request = {"kind": "locate_object_region", "subject": "acl", "question": "ACL"}
    first = procedures.route_observation_request(
        request, {}, {}, attempted, None, memory={}
    )
    second = procedures.route_observation_request(
        request, {}, {}, attempted, None, memory={}
    )
    assert first["code"] == "located"
    assert second["code"] == "procedure_already_answered"
    assert calls == ["acl"]


def test_unknown_kind_is_named_without_running_an_unrelated_reader(monkeypatch):
    monkeypatch.setattr(
        pipeline,
        "_bounded_observation",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("wrong action")),
    )
    result = procedures.route_observation_request(
        {"kind": "not_an_action", "subject": "acl"}, {}, {}, set(), None, memory={}
    )
    assert result["code"] == "request_kind_has_no_consumer"


def test_identity_disagreement_does_not_block_a_requested_observation(monkeypatch):
    seen = []
    monkeypatch.setitem(
        procedures._CONSUMERS,
        "profile_object_window",
        lambda call: seen.append(call.subject) or {"code": "profiled"},
    )
    result = procedures.route_observation_request(
        {"kind": "profile_object_window", "subject": "tibia"},
        {},
        {},
        set(),
        None,
        memory={},
        withheld={"tibia": {"reason": "signed_conflict"}},
    )
    assert result["code"] == "profiled"
    assert seen == ["tibia"]


def test_repeat_recall_returns_to_shared_coordinator_without_comparing_twice(
    monkeypatch,
):
    from knee.diagnosis import squint_locator

    monkeypatch.setattr(
        squint_locator,
        "recall_object",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("duplicate recall")
        ),
    )
    objects = {"acl": {"profile": {"subject": "acl", "banks": {"reading": [1, 0, 0]}}}}
    result = procedures.route_observation_request(
        {"kind": "repeat_object_recall", "subject": "acl", "question": "ACL"},
        {},
        objects,
        set(),
        None,
        memory={},
    )
    assert result["code"] == "recall_ready"


def test_malformed_recall_input_does_not_become_a_success():
    objects = {"acl": {"profile": {"subject": "another_object", "banks": {}}}}
    result = procedures.route_observation_request(
        {"kind": "repeat_object_recall", "subject": "acl", "question": "ACL"},
        {},
        objects,
        set(),
        None,
        memory={},
    )
    assert result["code"] == "current_profile_invalid"
    assert result["reason"] == "profile_names_another_object"


def test_changed_profile_reaches_h1_in_its_structural_context_and_keeps_other_evidence(
    monkeypatch,
):
    before = {"banks": {"old": [1, 0, 0]}}
    after = {"banks": {"new": [0, 0, 1]}}
    other = {"banks": {"other": [0, 1, 0]}}
    objects = {"tibia": {"profile": after}, "femur": {"profile": other}}
    contexts = {
        "tibia": {"basis": "structural_reader"},
        "femur": {"basis": "structural_reader"},
    }
    monkeypatch.setattr(pipeline, "_identity_contexts", lambda rows: dict(contexts))
    calls = []

    def hear(rows, memory, excluded_uid, *, prepared_identity, contexts):
        calls.append((rows, prepared_identity, contexts))
        return {
            "outcome": "examined",
            "objects": {"tibia": {"outcome": "established_by_structure"}},
        }

    monkeypatch.setattr(pipeline, "_identity_readings", hear)
    monkeypatch.setattr(pipeline, "_resolve_identity_contests", lambda *args: {})
    readings = {
        "objects": {"tibia": {"outcome": "old"}, "femur": {"outcome": "old_femur"}},
        "resolved_scale": {
            "objects": {
                "tibia": {"outcome": "stale"},
                "femur": {"outcome": "keep_joint"},
            }
        },
    }
    contests = {"tibia": {"old": True}, "femur": {"keep": True}}
    prepared = {"shared": "squint"}
    joint = {"shared": "joint"}
    returned = pipeline._refresh_identity_after_observations(
        objects,
        {},
        {},
        None,
        {"tibia": before, "femur": other},
        contexts,
        readings,
        contests,
        set(),
        [],
        None,
        prepared,
        joint,
    )
    assert returned is joint
    assert len(calls) == 1 and set(calls[0][0]) == {"tibia"}
    assert calls[0][0]["tibia"]["profile"] is after
    assert calls[0][1] is prepared
    assert calls[0][2]["tibia"]["basis"] == "structural_reader"
    assert readings["objects"]["tibia"]["outcome"] == "established_by_structure"
    assert readings["resolved_scale"]["objects"] == {"femur": {"outcome": "keep_joint"}}
    assert contests == {"femur": {"keep": True}}


def test_unchanged_observations_do_not_repeat_identity_computation(monkeypatch):
    profile = {"banks": {"observed": [1, 0, 0]}}
    objects = {"tibia": {"profile": profile}}
    contexts = {"tibia": {"basis": "structural_reader"}}
    monkeypatch.setattr(pipeline, "_identity_contexts", lambda rows: dict(contexts))
    monkeypatch.setattr(
        pipeline,
        "_identity_readings",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("duplicate identity")
        ),
    )
    joint = {"shared": "joint"}
    returned = pipeline._refresh_identity_after_observations(
        objects,
        {},
        {},
        None,
        {"tibia": profile},
        contexts,
        {"objects": {}},
        {},
        set(),
        [],
        None,
        {},
        joint,
    )
    assert returned is joint


def test_infer_study_locates_the_requested_object_and_its_new_reading_reaches_diagnosis(
    monkeypatch,
):
    import time

    from knee.diagnosis import (
        squint_anatomy_locator,
        squint_contracts,
        squint_locator,
        squint_profiles,
    )
    from tests import test_squint_dependent_territories as dependent
    from tests.test_squint_v2_location import _v2_dependent

    series, femur, _built, _profiles, memory = _v2_dependent()
    study = dependent._study(series, knee_side="left", anchors={"femur": femur})
    clock = {"now": 0.0}
    real_anchor = squint_anatomy_locator._anchored_object

    def anchor_then_late(*args, **kwargs):
        result = real_anchor(*args, **kwargs)
        clock["now"] = 20.0
        return result

    with monkeypatch.context() as patch:
        patch.setattr(squint_anatomy_locator, "_anchored_object", anchor_then_late)
        patch.setattr(time, "monotonic", lambda: clock["now"])
        location = squint_locator.locate_objects(
            study, memory, 10.0, refine_finalists=False
        )
    assert (
        location["objects"]["medial_meniscus"]["evidence"]["reason"]
        == "deadline_before_search"
    )
    monkeypatch.setattr(
        squint_profiles, "read_study_squints", lambda *args, **kwargs: study
    )
    monkeypatch.setattr(
        squint_locator, "locate_objects", lambda *args, **kwargs: location
    )
    monkeypatch.setattr(
        pipeline,
        "_bounded_observation",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("location is not zoom")
        ),
    )
    seen = []

    def recall(profile, memory, *, question, exclude_study_uid):
        if question == "Medial Meniscus" and profile["subject"] == "medial_meniscus":
            seen.append(bool(profile["banks"]))
        return {
            "outcome": "proposal",
            "subject": profile["subject"],
            "case_terms": [],
            "censor_terms": [],
            "speaking_calls": [],
            "vetoed_answers": [],
        }

    def combine(question, evidence):
        return (
            {
                "outcome": "open",
                "observation_requests": [
                    {
                        "kind": "locate_object_region",
                        "subject": "medial_meniscus",
                        "question": question,
                        "reason": "not_observed",
                    }
                ],
            }
            if question == "Medial Meniscus"
            else {"outcome": "defeated", "observation_requests": []}
        )

    monkeypatch.setattr(squint_locator, "recall_object", recall)
    monkeypatch.setattr(squint_contracts, "combine_condition", combine)
    result = pipeline.infer_study(None, study["study_uid"], memory)
    assert seen == [False, True]
    assert [row["code"] for row in result["observations"]] == ["located"]
    assert result["identity_consumption"]["objects"]["medial_meniscus"][
        "region_read_as_subject"
    ]
    assert result["work"]["bounded_zoom_runs"] == 0
