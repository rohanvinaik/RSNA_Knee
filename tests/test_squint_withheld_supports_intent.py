"""Withheld source supports must reach recall without acquiring anchor authority.

Intent from the local bootstrap producer/consumer defect: retained evidence is not
consumed evidence, and a disputed hypothesis is not established anatomy.
"""

from __future__ import annotations

import numpy as np
import pytest

from knee.diagnosis import squint_anatomy_locator as locator
from knee.diagnosis import squint_pipeline as pipeline
from knee.diagnosis import squint_profiles as writer
from knee.diagnosis.squint_identity import PRIOR_ONLY, STRUCTURAL_READER
from knee.diagnosis.squint_identity_growth import admission_from_recall
from knee.diagnosis.squint_interfaces import (
    ANCHOR_SCHEMA,
    ROLE_CONTEXT,
    ROLE_OBJECT,
    TERRITORY_PROCEDURE,
)
from tests import squint_upgrade_fixtures as fixture


def supplied_anchor(territory, *, evidence_only=True, status="conflict"):
    return {
        "schema": ANCHOR_SCHEMA,
        "study_uid": fixture.STUDY_UID,
        "subject": "femur",
        "status": status,
        "territories": [] if evidence_only else [territory],
        "evidence_territories": [territory] if evidence_only else [],
        "key_planes": {},
        "reference_lps": None,
        "producer": "source-reader-fixture",
        "cost": {},
    }


def setup(monkeypatch, *, evidence_only=True, status="conflict"):
    series, leg = fixture.series_record(), fixture.expected_leg_map()
    series["leg_map"] = leg
    territory = fixture.teacher_territory("femur")
    territory["origin"] = "anchor_structure"
    territory["provenance"].update(
        standing="withheld",
        evidence="withheld_from_anchoring",
        source_call="source-femur-section",
    )
    profile = writer.profile_territory(series, territory, leg, subject="femur")
    other = {
        **profile,
        "subject": "muscle",
        "banks": {
            key: [counts[2], counts[0], counts[1]]
            for key, counts in profile["banks"].items()
        },
    }
    memory = {
        "objects": ["femur"],
        "procedure": TERRITORY_PROCEDURE,
        "revision": "test-frozen-parent",
        "cases": [
            {
                "case_id": "teacher-femur",
                "study_uid": "other-femur",
                "subject": "femur",
                "profile": profile,
            },
            {
                "case_id": "teacher-muscle",
                "study_uid": "other-muscle",
                "subject": "muscle",
                "profile": other,
            },
        ],
        "object_identity_teaching": {
            "schema": "knee.object-identity-teaching/v1",
            "confirmed_case_ids": ["teacher-femur", "teacher-muscle"],
            "calls": [
                {"candidate_id": "teacher-femur", "call": "confirm"},
                {"candidate_id": "teacher-muscle", "call": "confirm"},
            ],
        },
    }
    study = {
        "study_uid": fixture.STUDY_UID,
        "series": [series],
        "anchors": {
            "femur": supplied_anchor(
                territory, evidence_only=evidence_only, status=status
            )
        },
    }

    def no_map(*args, **kwargs):
        return {
            "proposal": {"windows": [], "status": "not_proposed"},
            "territories": [],
            "origin": None,
            "status": "not_proposed",
            "proposed_window_count": 0,
            "refusals": {},
            "leg_prior": None,
        }

    monkeypatch.setattr(locator, "dependent_territories", no_map)
    return study, memory, series, territory


@pytest.mark.parametrize("evidence_only", [True, False])
def test_withheld_source_reaches_actual_writer_and_recall_without_anchor_authority(
    monkeypatch, evidence_only
):
    study, memory, series, territory = setup(monkeypatch, evidence_only=evidence_only)
    state = locator.study_anchors(study, {fixture.SERIES_UID: series})
    assert state["usable"] == {} and state["geometry"] == {}
    assert state["hypotheses"]["femur"][0]["territory"] is territory
    located = locator.locate_anatomy_first(study, memory, refine_finalists=False)
    femur = located["objects"]["femur"]
    assert femur["profile"] is not None
    assert (
        femur["territories"][0]["provenance"]["source_call"] == "source-femur-section"
    )
    assert femur["evidence"]["source"] != "current_study_structural_anchor"
    contexts = pipeline._identity_contexts(located["objects"])
    assert contexts["femur"]["basis"] == PRIOR_ONLY
    assert "arrangement" not in contexts["femur"]["supporting_observations"]
    recalled = pipeline._identity_readings(
        located["objects"], memory, None, contexts=contexts
    )
    reading = recalled["objects"]["femur"]
    assert reading["outcome"] != "unresolved_missing_reading"
    assert reading["identity_basis"] == PRIOR_ONLY
    candidate = {
        "case_id": "query-femur",
        "study_uid": fixture.STUDY_UID,
        "subject": "femur",
        "regions": femur["regions"],
        "sanity": femur["sanity"],
        "source": {"kind": "current-study-observation"},
        "identity_context": contexts["femur"],
    }
    admission = admission_from_recall(candidate, reading)
    assert admission["state"] != "admitted"
    assert not admission["support"]


def test_usable_anchor_keeps_existing_path_once(monkeypatch):
    study, memory, _series, territory = setup(
        monkeypatch, evidence_only=False, status="partial"
    )
    study["anchors"]["femur"]["evidence_territories"] = []
    territory["provenance"].pop("standing")
    result = locator.locate_anatomy_first(study, memory, refine_finalists=False)
    femur = result["objects"]["femur"]
    assert femur["evidence"]["location_route"] == "structural_anchor"
    assert len(femur["regions"]) == 1
    assert (
        pipeline._identity_contexts(result["objects"])["femur"]["basis"]
        == STRUCTURAL_READER
    )


@pytest.mark.parametrize(
    "mutation, expected",
    [
        ("study", "territory_identity_mismatch"),
        ("subject", "territory_identity_mismatch"),
        ("series", "territory_series_not_in_study"),
        ("list", "territory_list_invalid"),
        ("record", "territory_schema_invalid"),
    ],
)
def test_invalid_withheld_scope_is_refused_and_never_read(
    monkeypatch, mutation, expected
):
    study, memory, series, territory = setup(monkeypatch)
    anchor = study["anchors"]["femur"]
    if mutation == "study":
        territory["study_uid"] = "foreign-study"
    elif mutation == "subject":
        territory["subject"] = "tibia"
    elif mutation == "series":
        territory["series_uid"] = "foreign-series"
    elif mutation == "list":
        anchor["evidence_territories"] = None
    else:
        anchor["evidence_territories"] = [None]
    state = locator.study_anchors(study, {fixture.SERIES_UID: series})
    assert not state["hypotheses"].get("femur")
    assert state["bones"]["femur"]["refused_hypothesis_territories"] == {expected: 1}
    result = locator.locate_anatomy_first(study, memory, refine_finalists=False)
    assert result["objects"]["femur"]["profile"] is None


def test_empty_object_support_before_valid_hypothesis_is_named_without_index_shift(
    monkeypatch,
):
    import copy

    study, memory, _series, territory = setup(monkeypatch)
    empty = copy.deepcopy(territory)
    empty["origin"] = "fallback_location"
    empty["roles"][:] = ROLE_CONTEXT
    empty["object_share"][:] = np.nan
    empty["provenance"]["source_call"] = "empty-support"
    study["anchors"]["femur"]["evidence_territories"].insert(0, empty)
    result = locator.locate_anatomy_first(study, memory, refine_finalists=False)
    femur = result["objects"]["femur"]
    assert femur["profile"] is not None
    assert (
        femur["territories"][0]["provenance"]["source_call"] == "source-femur-section"
    )
    assert [row["reason"] for row in femur["evidence"]["reading_refusals"]] == [
        "candidate_territory_without_object_tiles"
    ]


@pytest.mark.parametrize("selected_held", [False, True])
def test_only_a_selected_hypothesis_withholds_fallback_geometry(
    monkeypatch, selected_held
):
    import copy

    study, memory, _series, territory = setup(monkeypatch)
    ordinary = copy.deepcopy(territory)
    ordinary["origin"] = "fallback_location"
    ordinary["provenance"] = {"source_call": "ordinary-map-proposal"}
    # The ordinary map support matches the seed exactly; the held rival is different.
    if not selected_held:
        territory["roles"][:] = ROLE_CONTEXT
        territory["object_share"][:] = np.nan
        territory["roles"][0, 2, 2] = ROLE_OBJECT
        territory["object_share"][0, 2, 2] = 1
    other = copy.deepcopy(memory["cases"][0])
    other.update(case_id="teacher-tibia", subject="tibia", study_uid="other-tibia")
    other["profile"]["subject"] = "tibia"
    memory["cases"].append(other)
    memory["object_identity_teaching"]["confirmed_case_ids"].append("teacher-tibia")
    memory["object_identity_teaching"]["calls"].append(
        {"candidate_id": "teacher-tibia", "call": "confirm"}
    )
    calls = []

    def proposal(_series, subject, **kwargs):
        calls.append((subject, dict(kwargs["anchors"])))
        made = [ordinary] if subject == "femur" and not selected_held else []
        return {
            "proposal": {"windows": [], "status": "proposed"},
            "territories": made,
            "origin": "fallback_location",
            "status": "proposed",
            "proposed_window_count": len(made),
            "refusals": {},
            "leg_prior": None,
        }

    monkeypatch.setattr(locator, "dependent_territories", proposal)
    monkeypatch.setattr(
        locator,
        "object_geometry",
        lambda *args: {"reference": {"status": "partial", "point_lps": None}},
    )
    result = locator.locate_anatomy_first(study, memory, refine_finalists=False)
    femur = result["objects"]["femur"]
    selected = femur["evidence"]["selected_withheld_support_hypotheses"]
    assert bool(selected) is selected_held
    tibia_anchors = next(anchors for subject, anchors in calls if subject == "tibia")
    assert ("femur" in tibia_anchors) is (not selected_held)
    if not selected_held:
        assert (
            femur["territories"][0]["provenance"]["source_call"]
            == "ordinary-map-proposal"
        )


def test_real_signed_negative_speaks_on_hypothesis_without_admitting_it(monkeypatch):
    import copy

    study, memory, _series, _territory = setup(monkeypatch)
    negative = copy.deepcopy(memory["cases"][0])
    negative.update(case_id="not-femur", study_uid="reviewed-negative-study")
    # A different positive presentation leaves a nontrivial trust radius for this
    # confirmed negative. The query matches the negative's measured support exactly.
    positive = memory["cases"][0]["profile"]
    positive["banks"] = {
        key: [counts[0] + 1, counts[1] + 1, counts[2] + 1]
        for key, counts in positive["banks"].items()
    }
    teaching = memory["object_identity_teaching"]
    teaching["negative_case_ids"] = ["not-femur"]
    teaching["negative_views"] = {
        "not-femur": [[fixture.VIEW["orientation"], "1", "1"]]
    }
    teaching["calls"].append(
        {
            "candidate_id": "not-femur",
            "call": "reject",
            "views": [[fixture.VIEW["orientation"], "1", "1"]],
        }
    )
    memory["object_identity_cases"] = {
        "schema": "knee.object-identity-cases/v1",
        "cases": [negative],
    }
    result = locator.locate_anatomy_first(study, memory, refine_finalists=False)
    contexts = pipeline._identity_contexts(result["objects"])
    reading = pipeline._identity_readings(
        result["objects"], memory, None, contexts=contexts
    )["objects"]["femur"]
    assert reading["applicable_negative_case_ids"] == ["not-femur"], reading
    [negative_reading] = reading["negative_cases"]
    assert negative_reading["applies"] is True
    assert negative_reading["over_the_asserted_region"]["speaks"] is True
    assert reading["identity_basis"] == PRIOR_ONLY
    femur = result["objects"]["femur"]
    admission = admission_from_recall(
        {
            "case_id": "query-femur",
            "study_uid": fixture.STUDY_UID,
            "subject": "femur",
            "regions": femur["regions"],
            "sanity": femur["sanity"],
            "source": {"kind": "current-study-observation"},
            "identity_context": contexts["femur"],
        },
        reading,
    )
    assert admission["state"] != "admitted"
    assert not admission["support"]
