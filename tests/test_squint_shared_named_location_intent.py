from __future__ import annotations

import copy

from knee.diagnosis import squint_anatomy_locator as locator
from knee.diagnosis import squint_pipeline as pipeline
from knee.diagnosis import squint_profiles as writer
from knee.diagnosis.squint_identity import PRIOR_ONLY
from tests.test_squint_withheld_supports_intent import setup


def test_named_location_reuses_the_same_locator_and_keeps_withheld_authority(
    monkeypatch,
):
    study, memory, _series, _territory = setup(monkeypatch)
    first = locator.locate_anatomy_first(study, memory, refine_finalists=False)
    expected = first["objects"]["femur"]

    def forbidden(*args, **kwargs):
        raise AssertionError("already computed study work repeated")

    monkeypatch.setattr(locator, "study_anchors", forbidden)
    monkeypatch.setattr(locator, "_check_anchor_sanity", forbidden)
    monkeypatch.setattr(writer, "leg_calibration", forbidden)
    again = locator.locate_anatomy_first(
        study, memory, refine_finalists=False, subjects=("femur",)
    )
    actual = again["objects"]["femur"]
    assert actual["profile"] == expected["profile"]
    assert actual["territories"] == expected["territories"]
    assert actual["evidence"]["selected_withheld_support_hypotheses"]
    assert pipeline._identity_contexts(again["objects"])["femur"]["basis"] == PRIOR_ONLY
    assert (
        again["evidence"]["anchors"]["bones"] == first["evidence"]["anchors"]["bones"]
    )


def test_named_location_does_not_run_unrequested_subjects(monkeypatch):
    study, memory, _series, _territory = setup(monkeypatch)
    muscle = copy.deepcopy(memory["cases"][1])
    muscle.update(case_id="tibia-teacher", subject="tibia")
    muscle["profile"]["subject"] = "tibia"
    memory["cases"].append(muscle)
    locator.locate_anatomy_first(study, memory, refine_finalists=False)
    seen = []
    previous = locator.dependent_territories

    def observed(series, subject, **kwargs):
        seen.append(subject)
        return previous(series, subject, **kwargs)

    monkeypatch.setattr(locator, "dependent_territories", observed)
    result = locator.locate_anatomy_first(
        study, memory, refine_finalists=False, subjects=("femur",)
    )
    assert set(result["objects"]) == {"femur"}
    assert seen == ["femur"]


def test_named_location_preserves_already_retained_native_supports(monkeypatch):
    study, memory, _series, _territory = setup(monkeypatch)
    locator.locate_anatomy_first(study, memory, refine_finalists=False)
    retained = study[locator.LOCATION_RUNTIME_CONTEXT]["retained_support"]
    sentinel = {"native_support": object()}
    retained.append(sentinel)
    study[locator.NATIVE_SUPPORT_RETAINED] = retained
    locator.locate_anatomy_first(
        study, memory, refine_finalists=False, subjects=("femur",)
    )
    assert study[locator.NATIVE_SUPPORT_RETAINED] is retained
    assert study[locator.NATIVE_SUPPORT_RETAINED][0] is sentinel


def test_missing_runtime_does_not_restart_the_anchor_search(monkeypatch):
    study, memory, _series, _territory = setup(monkeypatch)
    monkeypatch.setattr(
        locator,
        "study_anchors",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("anchor search")),
    )
    result = locator.locate_anatomy_first(
        study, memory, refine_finalists=False, subjects=("femur",)
    )
    assert result["reason"] == "location_runtime_unavailable"
    assert result["objects"] == {}


def test_another_memory_or_changed_series_cannot_reuse_the_runtime(monkeypatch):
    study, memory, _series, _territory = setup(monkeypatch)
    locator.locate_anatomy_first(study, memory, refine_finalists=False)
    other = locator.locate_anatomy_first(
        study, dict(memory), refine_finalists=False, subjects=("femur",)
    )
    assert other["reason"] == "location_runtime_identity_mismatch"
    study["series"] = [dict(study["series"][0])]
    changed = locator.locate_anatomy_first(
        study, memory, refine_finalists=False, subjects=("femur",)
    )
    assert changed["reason"] == "location_runtime_series_changed"
