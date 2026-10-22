"""Intent: one changed shared object invalidates only its actual condition consumers.

Image and precedent producers are controlled fixtures; infer_study, identity
refresh, role contracts, signed condition combination, and readout are real.
"""

import copy
from collections import Counter

import pytest

from knee.diagnosis import (
    declarations,
    squint_locator,
    squint_pipeline,
    squint_procedures,
    squint_profiles,
)


def _signed(subject, sign, *, scope="controlled_localized_fixture"):
    return {
        "outcome": "present" if sign == 1 else "absent",
        "subject": subject,
        "speaking_calls": [sign],
        "speaking_case_ids": [f"fixture-{subject}{sign}"],
        "case_terms": [
            {
                "case_id": f"fixture-{subject}{sign}",
                "call": sign,
                "call_scope": scope,
                "terms": {"dot": 1, "left_norm_sq": 1, "right_norm_sq": 1},
                "reaches_trust": True,
                "trust": {"source": "controlled independent fixture"},
            }
        ],
    }


def _run(monkeypatch, tmp_path, mode):
    profile = {"subject": "femur", "banks": {}, "epoch": "coarse"}
    objects = {
        "femur": {"profile": profile, "context_epoch": "coarse", "withheld": False}
    }
    calls = []
    identity_calls = []
    routed = []
    questions = tuple(
        declarations.question_for(q) for q in ("Contusion", "Effusion", "Fracture")
    )
    monkeypatch.setattr(declarations, "QUESTIONS", questions)
    monkeypatch.setattr(
        squint_profiles, "read_study_squints", lambda *a, **k: {"work": {}}
    )
    monkeypatch.setattr(
        squint_locator, "locate_objects", lambda *a, **k: {"objects": objects}
    )
    monkeypatch.setattr(
        squint_pipeline,
        "_identity_contexts",
        lambda objects: {
            "femur": {"epoch": objects["femur"]["context_epoch"]},
        },
    )

    def identity(selected, *args, **kwargs):
        identity_calls.append(tuple(selected))
        return {
            "objects": {s: {"outcome": "controlled_fixture_identity"} for s in selected}
        }

    def consumption(objects, *args):
        withheld = objects["femur"]["withheld"]
        return {
            "objects": {
                "femur": {
                    "region_read_as_subject": not withheld,
                    "identity_effect": "applicable_negative_after_finer_look"
                    if withheld
                    else "controlled_identity_support",
                    "applicable_negative_case_ids": ["controlled-negative"]
                    if withheld
                    else [],
                }
            }
        }

    monkeypatch.setattr(squint_pipeline, "_identity_readings", identity)
    monkeypatch.setattr(
        squint_pipeline, "_resolve_identity_contests", lambda *a, **k: {}
    )
    monkeypatch.setattr(squint_pipeline, "_identity_consumption", consumption)
    monkeypatch.setattr(squint_pipeline, "_subject_cue_snapshot", lambda *a: None)

    def recall(question, objects, memory, uid, excluded, *, not_read_as):
        q = question.question_id
        fine = objects["femur"]["profile"]["epoch"] == "finer"
        calls.append((q, fine, "femur" in not_read_as))
        evidence = {}
        for subject in question.objects:
            if subject != "femur" or q == "Effusion":
                evidence[subject] = _signed(subject, -1)
            elif subject in not_read_as:
                evidence[subject] = {
                    "outcome": "unresolved_missing_reading",
                    "subject": subject,
                    "case_terms": [],
                    "region_not_read_as_subject": copy.deepcopy(not_read_as[subject]),
                }
            elif q == "Fracture":
                evidence[subject] = (
                    _signed(subject, -1)
                    if fine
                    else {
                        "outcome": "unresolved_missing_reading",
                        "subject": subject,
                        "case_terms": [],
                    }
                )
            elif fine and mode == "opposition":
                positive = _signed(subject, 1)
                negative = _signed(subject, -1)
                evidence[subject] = {
                    "outcome": "unresolved_conflict",
                    "subject": subject,
                    "speaking_calls": [1, -1],
                    "case_terms": positive["case_terms"] + negative["case_terms"],
                }
            elif fine:
                evidence[subject] = _signed(subject, -1 if mode == "negative" else 1)
            elif mode in {"negative", "positive", "opposition"}:
                evidence[subject] = _signed(
                    subject, 1, scope="positive_condition_presentation"
                )
            else:
                evidence[subject] = _signed(subject, 1)
        return evidence

    monkeypatch.setattr(squint_pipeline, "_recall_question", recall)

    def observe(request, study, objects, attempted, deadline, **kwargs):
        assert request.get("object", request.get("subject")) == "femur"
        routed.append(request["question"])
        if mode in {"noop", "repeat"}:
            code = "recall_ready" if mode == "repeat" else "reading_unchanged"
        elif mode == "copy":
            objects["femur"]["profile"] = copy.deepcopy(objects["femur"]["profile"])
            code = "reading_unchanged"
        elif mode == "context":
            objects["femur"]["context_epoch"] = "changed"
            objects["femur"]["withheld"] = True
            code = "measured"
        elif mode == "eligibility":
            objects["femur"]["withheld"] = True
            code = "measured"
        else:
            objects["femur"]["profile"] = {
                "subject": "femur",
                "banks": {},
                "epoch": "finer",
            }
            objects["femur"]["withheld"] = mode == "withhold"
            code = "measured"
        return {"code": code, "subject": "femur", "lens": "controlled_fixture"}

    monkeypatch.setattr(squint_procedures, "route_observation_request", observe)
    record = squint_pipeline.infer_study(tmp_path, "controlled-study", {})
    return record, calls, identity_calls, routed


def test_later_withheld_support_retracts_earlier_established_call(
    monkeypatch, tmp_path
):
    record, calls, _, routed = _run(monkeypatch, tmp_path, "withhold")
    early = record["questions"]["Contusion"]
    assert early["finding"]["outcome"] == "open"
    assert 0 < record["values"]["Contusion"] < 1
    assert (
        record["identity_consumption"]["objects"]["femur"]["region_read_as_subject"]
        is False
    )
    assert early["objects"]["femur"]["outcome"] == "unresolved_missing_reading"
    assert early["objects"]["femur"]["region_not_read_as_subject"][
        "applicable_negative_case_ids"
    ] == ["controlled-negative"]
    assert "fixture-femur1" not in early["ranking"]["positive_case_ids"]
    assert routed == ["Fracture"]  # no new image pass for the earlier question
    assert Counter(q for q, _, _ in calls) == {
        "Contusion": 2,
        "Effusion": 1,
        "Fracture": 2,
    }
    event = record["condition_propagation"]["updates"][0]
    assert event["changed_subjects"]["femur"] == [
        "profile_changed",
        "condition_eligibility_changed",
    ]
    assert event["refreshed_questions"][0]["previous_outcome"] == "assigned"
    assert event["refreshed_questions"][0]["current_outcome"] == "open"
    assert early["shared_state_revision"] == event["revision"] == 1
    assert {r["question"] for r in record["unresolved_observation_requests"]} == {
        "Contusion",
        "Fracture",
    }
    assert record["observations"][0]["before_state"]["outcome"] == "open"
    assert record["observations"][0]["after_state"]["outcome"] == "open"


@pytest.mark.parametrize(
    ("mode", "outcome", "value"),
    [("negative", "defeated", 0.0), ("positive", "assigned", 1.0)],
)
def test_later_measurement_resolves_earlier_open_question(
    monkeypatch, tmp_path, mode, outcome, value
):
    record, calls, _, routed = _run(monkeypatch, tmp_path, mode)
    assert record["questions"]["Contusion"]["finding"]["outcome"] == outcome
    assert record["values"]["Contusion"] == value
    event = record["condition_propagation"]["updates"][0]
    assert event["refreshed_questions"][0]["previous_outcome"] == "open"
    assert event["refreshed_questions"][0]["current_outcome"] == outcome
    assert Counter(q for q, _, _ in calls)["Effusion"] == 1
    assert routed == ["Fracture"]
    assert record["unresolved_observation_requests"] == []
    assert record["observations"][0]["after_state"]["outcome"] == "defeated"


@pytest.mark.parametrize("mode", ["noop", "copy"])
def test_no_new_shared_information_reuses_all_cached_condition_recalls(
    monkeypatch, tmp_path, mode
):
    record, calls, _, _ = _run(monkeypatch, tmp_path, mode)
    assert Counter(q for q, _, _ in calls) == {
        "Contusion": 1,
        "Effusion": 1,
        "Fracture": 1,
    }
    assert record["condition_propagation"]["revision"] == 0
    assert record["condition_propagation"]["updates"] == []
    assert record["work"]["condition_recall_calls"] == 3


@pytest.mark.parametrize("mode", ["context", "eligibility"])
def test_context_or_eligibility_changes_invalidate_without_new_profile(
    monkeypatch, tmp_path, mode
):
    record, calls, _, _ = _run(monkeypatch, tmp_path, mode)
    assert record["objects"]["femur"]["profile"]["epoch"] == "coarse"
    assert record["questions"]["Contusion"]["finding"]["outcome"] == "open"
    reasons = record["condition_propagation"]["updates"][0]["changed_subjects"]["femur"]
    assert "profile_changed" not in reasons
    assert "condition_eligibility_changed" in reasons
    assert ("identity_context_changed" in reasons) is (mode == "context")
    assert Counter(q for q, _, _ in calls)["Effusion"] == 1


def test_refreshed_question_preserves_both_signed_opposing_cases(monkeypatch, tmp_path):
    record, _, _, _ = _run(monkeypatch, tmp_path, "opposition")
    finding = record["questions"]["Contusion"]["finding"]
    assert finding["outcome"] == "open"
    assert {
        row["call"] for row in finding["recall_evidence"]["femur"][0]["case_terms"]
    } == {-1, 1}
    assert "fixture-femur1" in finding["rank"]["positive_case_ids"]
    assert "fixture-femur-1" in finding["rank"]["negative_case_ids"]


def test_explicit_repeat_recall_still_runs_its_named_consumer(monkeypatch, tmp_path):
    record, calls, _, _ = _run(monkeypatch, tmp_path, "repeat")
    assert Counter(q for q, _, _ in calls) == {
        "Contusion": 1,
        "Effusion": 1,
        "Fracture": 2,
    }
    assert record["condition_propagation"]["revision"] == 0
