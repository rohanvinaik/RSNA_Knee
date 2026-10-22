"""Reviewed identity scope is shared by both object-location consumers."""

from __future__ import annotations

import copy

import pytest
import test_squint_anatomy_locator as anatomy_fixture

import knee.diagnosis.squint_locator as locator

VIEW = anatomy_fixture.VIEW
BANK = 'squint/v2/view=["axial","yes","no"]/role=object/metric=signal_median/direction=overview/scale=10mm'
PROCEDURE = anatomy_fixture.PROCEDURE
VIEW_KEY = ("axial", "yes", "no")

CORONAL = {"orientation": "coronal", "fluid_sensitive": "yes", "fat_suppression": "no"}
TEACHING_SCHEMA = "knee.object-identity-teaching/v1"


def _native_case(case_id: str, *, view=VIEW, extent_source=None, support=True):
    profile = {
        "schema": "knee.squint-profile/v1",
        "subject": "femur",
        "banks": {BANK: [1, 0, 0]},
        "source": {"procedure": PROCEDURE, "view": VIEW},
    }
    region = {"view": view}
    if extent_source is not None:
        region["extent_source"] = extent_source
    if support:
        region["territory"] = {
            "native_support": {
                "pixel_count": 4,
                "mask_sha256": "a" * 64,
                "slices": [2, 4],
                "offset_rc": [1, 3],
                "shape": [2, 2, 2],
            }
        }
    return {
        "case_id": case_id,
        "study_uid": f"study-{case_id}",
        "subject": "femur",
        "condition_calls": {"cartilage": 1},
        "profile": profile,
        "question_reference": {
            "schema": "knee.question-reference/v1",
            "question": "cartilage",
        },
        "regions": [region],
    }


def _teach(memory, *confirmed):
    memory["object_identity_teaching"] = {
        "schema": TEACHING_SCHEMA,
        "confirmed_case_ids": list(confirmed),
        "calls": [
            {
                "candidate_id": case_id,
                "call": "confirm",
                "views": [tuple(VIEW.values())],
                "negative_views": [tuple(CORONAL.values())],
                "also_positive": [],
            }
            for case_id in confirmed
        ],
    }


def test_native_support_address_without_outer_extent_is_native_search_scope():
    old = _native_case("old", extent_source="retained_object_support")
    reviewed = _native_case("reviewed")
    marker = _native_case("marker", extent_source="retained_physical_location")
    explicit_unknown = _native_case("unknown", extent_source="future_extent")
    cases = [old, reviewed, marker, explicit_unknown]

    scoped, examples, source = locator._location_scope(cases, "femur", VIEW_KEY)

    assert source == "native_object_support"
    assert {case["case_id"] for case in scoped} == {"old", "reviewed"}
    assert examples[1][1]["territory"]["native_support"]["pixel_count"] == 4


def test_reviewed_location_cases_filter_identity_and_region_views_without_mutation():
    old = _native_case("old")
    reviewed = _native_case("reviewed")
    wrong_view = _native_case("wrong-view", view=CORONAL)
    unreviewed = _native_case("unreviewed")
    memory = {
        "objects": ["femur", "unseen-object"],
        "cases": [old, reviewed, wrong_view, unreviewed],
        "negative_cases": [{"subject": "femur", "call": "reject"}],
        "alternative_cases": [{"subject": "tibia", "call": "alternative"}],
    }
    _teach(memory, "old", "reviewed", "wrong-view")
    before = copy.deepcopy(memory)

    cases = locator._location_cases(memory)
    scoped, _, source = locator._location_scope(cases, "femur", VIEW_KEY)

    assert source == "native_object_support"
    assert {case["case_id"] for case in scoped} == {"old", "reviewed"}
    assert "wrong-view" not in {row["case_id"] for row in cases}
    assert (
        next(row for row in cases if row["case_id"] == "reviewed")["question_reference"]
        == reviewed["question_reference"]
    )
    assert memory == before
    assert memory["negative_cases"] == before["negative_cases"]
    assert memory["alternative_cases"] == before["alternative_cases"]


def test_withheld_only_address_does_not_return_as_a_legacy_precedent():
    case = _native_case("withheld-only", view=CORONAL)
    memory = {"cases": [case]}
    _teach(memory, "withheld-only")

    cases = locator._location_cases(memory)
    scoped, examples, _source = locator._location_scope(cases, "femur", VIEW_KEY)

    assert cases == []
    assert scoped == []
    assert examples == []


@pytest.mark.parametrize("route", ["raw", "cached"])
def test_public_locator_uses_only_confirmed_location_teachers(route, monkeypatch):
    first = (0, 1, 0, 1, 0, 1)
    monkeypatch.setattr(anatomy_fixture, "BANK", BANK)
    series, _base, _helper_calls = anatomy_fixture._fixture([first], monkeypatch)
    old = _native_case("old", extent_source="retained_object_support")
    reviewed = _native_case("reviewed")
    unreviewed = _native_case("unreviewed")
    memory = {
        "objects": ["femur", "unseen-object"],
        "cases": [old, reviewed, unreviewed],
    }
    _teach(memory, "old", "reviewed")
    exact_calls = []
    anatomy_fixture._patch_exact(monkeypatch, exact_calls)

    if route == "raw":
        study = {"study_uid": "current", "series": [series]}
    else:
        study = {
            "study_uid": "current",
            "series": [
                {
                    "series_uid": "cached",
                    "view": VIEW,
                    "candidate_profiles": [
                        {"subject": "femur", "profile": old["profile"]}
                    ],
                }
            ],
        }

    result = locator.locate_objects(study, memory)

    if route == "cached":
        assert result["objects"]["femur"]["status"] == "proposal"
        assert (
            result["objects"]["unseen-object"]["status"] == "unresolved_missing_reading"
        )
    evidence = result["objects"]["femur"]["evidence"]
    scopes = evidence["location_precedent_scopes"]
    axial_scope = next(row for row in scopes if row["view"] == list(VIEW.values()))
    assert axial_scope["source"] == "native_object_support"
    assert set(axial_scope["case_ids"]) == {"old", "reviewed"}


def test_memory_without_identity_teaching_keeps_legacy_location_behavior():
    legacy = _native_case("legacy", support=False)
    memory = {"objects": ["femur"], "cases": [legacy]}

    cases = locator._location_cases(memory)
    scoped, _, source = locator._location_scope(cases, "femur", VIEW_KEY)

    assert [case["case_id"] for case in scoped] == ["legacy"]
    assert source == "legacy_unspecified_scope"
