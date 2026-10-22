"""Growth must retain measured location evidence without promoting it to identity."""

from __future__ import annotations

import copy
import json
from types import SimpleNamespace

import numpy as np
import pytest

from knee.collapse.physical import physical_squint
from knee.diagnosis.squint_identity_growth import (
    _decisions_bytes,
    admission_from_recall,
    location_support,
)
from knee.diagnosis.squint_sanity import window_sanity_checks


@pytest.fixture
def measured_between():
    normal = np.asarray([0.0, 0.6, 0.8])
    grid = physical_squint(np.zeros((2, 2)), (1.0, 1.0), 1.0)
    series = {
        "series_uid": "query-series",
        "stack": SimpleNamespace(median=np.zeros((3, 2, 2)), bounds_rc=grid.bounds_rc),
        "geometry": {
            "position": np.asarray([-2 * normal, 0 * normal, 2 * normal]),
            "orientation": np.asarray([[1, 0, 0, 0, 0.8, -0.6]] * 3),
            "spacing": np.ones((3, 2)),
        },
    }
    anchors = {
        name: {
            "source": "structural_anchor",
            "reference": {"status": "partial", "point_lps": None},
            "planes": {
                "axial": {
                    "outcome": "selected",
                    "series_uid": name + "-series",
                    "slice": 4,
                    "normal": normal.tolist(),
                    "offset_mm": offset,
                    "precision_mm": 1.0,
                }
            },
        }
        for name, offset in (("femur", -5), ("tibia", 5))
    }
    window = [1, 2, 0, 2, 0, 2]
    rows = window_sanity_checks(series, "medial_meniscus", [window], anchors, None)
    rows[0]["series_uid"] = series["series_uid"]
    return {
        "schema": "knee.object-anatomical-sanity/v1",
        "status": rows[0]["status"],
        "identity_assertion": None,
        "windows": rows,
    }


def test_measured_provenance_survives_the_growth_decision_and_strict_json(
    measured_between,
):
    support = location_support(measured_between, "medial_meniscus")
    original = measured_between["windows"][0]["checks"][0]
    retained = support["support"][0]
    for key in (
        "axis_lps",
        "target",
        "anchor_bands",
        "reference_planes",
        "gap_interval",
        "qualifier",
        "source",
        "reference_construction",
        "relation",
    ):
        assert retained[key] == original[key]
    assert [row["subject"] for row in retained["reference_planes"]] == [
        "femur",
        "tibia",
    ]
    assert set(retained["reference_planes"][0]) >= {
        "normal",
        "offset_mm",
        "precision_mm",
        "weight",
        "series_uid",
        "slice",
    }
    candidate = {
        "case_id": "measured-proposal",
        "study_uid": "new-study",
        "subject": "medial_meniscus",
        "regions": [{"series_uid": "query-series", "window": [1, 2, 0, 2, 0, 2]}],
        "source": {"kind": "squint-inference"},
        "sanity": measured_between,
    }
    decision = admission_from_recall(candidate, {"outcome": "placement_only"})
    assert decision["state"] == "proposal"
    assert decision["reason"] == "identity_context_unavailable"
    assert decision["recognized_identity"] is None
    assert decision["support"] == support["support"]
    persisted = json.loads(_decisions_bytes({"decisions": [decision]}))
    assert persisted["decisions"][0]["support"] == decision["support"]
    assert persisted["decisions"][0]["support"][0]["establishes"] == "location_only"


def test_retained_provenance_does_not_share_mutable_input(measured_between):
    original = copy.deepcopy(measured_between)
    result = location_support(measured_between, "medial_meniscus")
    retained = result["support"][0]
    retained["axis_lps"][0] = 100
    retained["anchor_bands"]["femur"][0] = 100
    retained["reference_planes"][1]["normal"][0] = 100
    retained["target"].append("another-object")
    assert measured_between == original


@pytest.mark.parametrize(
    "code",
    [
        "unknown_between_shared_planes_unavailable",
        "unknown_between_candidate_outside_or_touching",
    ],
)
def test_unknown_between_evidence_is_neither_support_nor_contradiction(
    measured_between, code
):
    measured_between["status"] = "unknown"
    measured_between["windows"][0]["status"] = "unknown"
    measured_between["windows"][0]["checks"][0]["result"] = code
    result = location_support(measured_between, "medial_meniscus")
    assert result == {
        "status": "unknown",
        "support": [],
        "reversed": [],
        "contradicted": False,
    }


def test_between_support_does_not_speak_for_another_subject(measured_between):
    result = location_support(measured_between, "lateral_meniscus")
    assert result["support"] == []
    assert result["reversed"] == []
    assert result["contradicted"] is False


def test_existing_axis_interval_checks_retain_their_original_record_shape():
    check = {
        "rule_id": "authored:femur:superior_to:tibia",
        "axis": "z",
        "result": "supported_strictly_after",
        "candidate_interval": [5, 6],
        "target_interval": [1, 2],
    }
    sanity = {
        "schema": "knee.object-anatomical-sanity/v1",
        "status": "plausible",
        "identity_assertion": None,
        "windows": [
            {"series_uid": "s", "window": [1, 2, 0, 2, 0, 2], "checks": [check]}
        ],
    }
    result = location_support(sanity, "femur")
    assert result["support"] == [
        {
            "establishes": "location_only",
            **check,
            "series_uid": "s",
            "window": [1, 2, 0, 2, 0, 2],
        }
    ]
