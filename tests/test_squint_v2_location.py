"""S1: comparable territory queries, anatomical placement and named uncertainty."""

from __future__ import annotations

import copy
import inspect
import json

import numpy as np
import pytest

from knee.diagnosis import squint_anatomy_locator as anatomy
from knee.diagnosis import squint_locator as locator
from knee.diagnosis import squint_pipeline
from knee.diagnosis import squint_profiles as writer
from knee.diagnosis.squint_interfaces import (
    ANCHOR_SCHEMA,
    ROLE_CONTEXT,
    ROLE_OBJECT,
    TERRITORY_PROCEDURE,
    anchor_code,
    parse_territory_bank_name,
)
from knee.diagnosis.squint_residual import held_readings
from tests import test_squint_dependent_territories as dependent
from tests.test_squint_profiles_territory import _native_fixture


def _anchor(series, territory):
    return {
        "schema": ANCHOR_SCHEMA,
        "study_uid": territory["study_uid"],
        "subject": territory["subject"],
        "status": "partial",
        "territories": [territory],
        "key_planes": {
            "coronal": {
                "outcome": "selected",
                "series_uid": series["series_uid"],
                "slice": 0,
            }
        },
        "reference_lps": None,
        "breadth_mm": None,
        "producer": "fixture-native-anchor",
        "cost": {"seconds": 0.0},
    }


def _native_bone(tmp_path):
    series, leg, territory = _native_fixture(tmp_path)
    territory.update(subject="femur", origin="anchor_structure")
    territory["key_planes"] = {
        "coronal": {
            "outcome": "selected",
            "series_uid": series["series_uid"],
            "slice": 0,
        }
    }
    return series, leg, territory


def _case(profile, subject, *, name="teacher", call=1, view=None):
    return {
        "case_id": name,
        "study_uid": "different-study-" + name,
        "subject": subject,
        "profile": profile,
        "condition_calls": {"Fracture" if subject == "femur" else "MM": call},
        "regions": []
        if view is None
        else [{"view": view, "extent_source": "retained_object_support"}],
        "teaching_source": {"kind": "independent_call"},
    }


def test_native_anchor_writes_own_places_at_both_scales_and_recall_terms(tmp_path):
    series, leg, territory = _native_bone(tmp_path)
    expected = writer.profile_territory(series, territory, leg, subject="femur")
    memory = {"cases": [_case(expected, "femur")]}
    study = {
        "study_uid": territory["study_uid"],
        "series": [series],
        "leg_maps": {series["series_uid"]: leg},
        "anchors": {"femur": _anchor(series, territory)},
    }
    result = locator.locate_objects(study, memory)
    bone = result["objects"]["femur"]
    assert bone["evidence"]["location_route"] == "structural_anchor"
    assert not bone["evidence"]["resemblance_applied"]
    profile = bone["profile"]
    assert profile["source"]["procedure"] == TERRITORY_PROCEDURE
    fields = [parse_territory_bank_name(name) for name in profile["banks"]]
    assert all(field is not None for field in fields)
    fields = [field for field in fields if field is not None]
    assert {field["scale_mm"] for field in fields} == {10.0, 2.0}
    assert {field["role"] for field in fields} == {"object", "context"}
    assert anatomy._object_coarse_banks(profile) == anatomy._object_coarse_banks(
        expected
    )
    bank = next(
        name
        for name in expected["banks"]
        if "/role=object/metric=signal_median/direction=overview/" in name
    )
    assert profile["banks"][bank] == [4, 0, 0]
    assert sum(profile["banks"][bank]) == np.count_nonzero(
        territory["roles"] == ROLE_OBJECT
    )
    memory["prepared_recall"] = locator.prepare_recall(memory)
    recall = locator.recall_object(profile, memory, "Fracture")
    assert recall.get("reason") != "selection_procedure_mismatch"
    assert recall["case_terms"]
    assert all(term["common_speaking_banks"] for term in recall["case_terms"])
    from knee.diagnosis.squint_location_check import located_rows

    rows, _ = located_rows(result)
    assert rows[0]["territory"]["roles"] == territory["roles"].tolist()
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("refine_finalists", [True, False], ids=["paired", "deferred"])
def test_locator_keeps_one_map_and_one_measured_calibration_for_two_bones(
    tmp_path, monkeypatch, refine_finalists
):
    series, leg, territory = _native_bone(tmp_path)
    other = {**territory, "subject": "tibia"}
    from knee.diagnosis import squint_leg

    map_calls = []
    quantile_calls = []
    quantile = writer.np.quantile

    def maps(study):
        map_calls.append(study["study_uid"])
        return {series["series_uid"]: leg}

    def measure(*args, **kwargs):
        quantile_calls.append(True)
        return quantile(*args, **kwargs)

    monkeypatch.setattr(squint_leg, "leg_maps", maps)
    monkeypatch.setattr(writer.np, "quantile", measure)
    study = {
        "study_uid": territory["study_uid"],
        "series": [series],
        "anchors": {
            "femur": _anchor(series, territory),
            "tibia": _anchor(series, other),
        },
    }
    result = locator.locate_objects(
        study,
        {"objects": ["femur", "tibia"], "procedure": TERRITORY_PROCEDURE},
        refine_finalists=refine_finalists,
    )
    assert map_calls == [territory["study_uid"]]
    assert study["leg_maps"][series["series_uid"]] is leg
    assert study["series"][0] is series
    assert len(quantile_calls) == len(series["metric_values"])
    assert set(result["objects"]) == {"femur", "tibia"}
    assert all(item["profile"] for item in result["objects"].values())
    from knee.diagnosis.squint_residual import _leg_map

    shared, source, _ = _leg_map(study, series)
    assert shared is leg and source == "study_shared"
    assert map_calls == [territory["study_uid"]]


def _v2_dependent():
    series = dependent._series()
    femur = dependent._complete_anchor(
        "femur",
        dependent._femur_point(series),
        [dependent._anchor_territory("femur", (2, 3, 6, 10, 13, 20))],
    )
    built = dependent._propose(
        series, "medial_meniscus", {"femur": dependent._geometry(series, femur)}
    )
    profiles = [
        writer.profile_territory(
            series, t, series["leg_map"], subject="medial_meniscus"
        )
        for t in built["territories"]
    ]
    memory = {
        "objects": ["femur", "medial_meniscus"],
        "cases": [_case(profiles[0], "medial_meniscus", view=series["view"])],
    }
    return series, femur, built, profiles, memory


def test_v2_candidates_compare_only_object_coarse_banks_and_preserve_exact_ties(
    monkeypatch,
):
    series, femur, built, profiles, memory = _v2_dependent()
    precedent = anatomy._object_coarse_banks(profiles[0])
    terms = [
        locator._exact_bank_terms(anatomy._object_coarse_banks(p), precedent)
        for p in profiles
    ]
    # The precedent is one current candidate: its exact self-comparison is the maximum.
    expected = []
    for territory, term in zip(built["territories"], terms, strict=True):
        if term["dot"] ** 2 == term["left_norm_sq"] * term["right_norm_sq"]:
            window = anatomy._object_window(territory)
            assert window is not None
            expected.append(window)
    expected.sort()

    def v1_forbidden(*args, **kwargs):
        raise AssertionError("v2 location must never invoke the v1 box writer")

    monkeypatch.setattr(writer, "profile_window", v1_forbidden)
    study = dependent._study(series, knee_side="left", anchors={"femur": femur})
    first = locator.locate_objects(study, memory)["objects"]["medial_meniscus"]
    assert sorted(tuple(r["window"]) for r in first["regions"]) == expected
    assert first["evidence"]["resemblance_banks"] == "object_role_10mm_only"
    for record in first["territories"]:
        assert record["origin"] == "anatomical_relation"
        assert all(
            value is None
            for plane in record["object_share"]
            for row in plane
            for value in row
        )
    changed = copy.deepcopy(memory)
    for profile in [changed["cases"][0]["profile"]]:
        for name in list(profile["banks"]):
            fields = parse_territory_bank_name(name)
            assert fields is not None
            if fields["role"] == "context":
                profile["banks"][name] = [10**30, 0, 10**30]
        name = next(iter(profile["banks"]))
        profile["banks"][name.replace("scale=10mm", "scale=2mm")] = [10**40, 0, 0]
    second = locator.locate_objects(study, changed)["objects"]["medial_meniscus"]
    assert first["regions"] == second["regions"]
    assert first["profile"] == second["profile"]


def test_v2_missing_native_refinement_is_named_and_coarse_reading_retained():
    series, femur, _built, _profiles, memory = _v2_dependent()
    result = locator.locate_objects(
        dependent._study(series, knee_side="left", anchors={"femur": femur}), memory
    )
    bone = result["objects"]["femur"]
    source = bone["profile"]["source"]["lineage"][0]
    assert source["fine_reading"] == {
        "code": "territory_refinement_unavailable",
        "reason": "squint_refine_native_series_unavailable",
    }
    assert anatomy._object_coarse_banks(bone["profile"])


def test_v2_moved_femur_moves_dependent_candidates_by_two_tiles():
    series, femur, _built, _profiles, memory = _v2_dependent()
    first = locator.locate_objects(
        dependent._study(series, knee_side="left", anchors={"femur": femur}), memory
    )["objects"]["medial_meniscus"]
    moved = copy.deepcopy(femur)
    moved["reference_lps"][2] -= 20.0
    moved["key_planes"]["axial"]["offset_mm"] -= 20.0
    second = locator.locate_objects(
        dependent._study(series, knee_side="left", anchors={"femur": moved}), memory
    )["objects"]["medial_meniscus"]
    before = first["evidence"]["candidate_territories"][dependent.CORONAL][
        "candidate_object_windows"
    ]
    after = second["evidence"]["candidate_territories"][dependent.CORONAL][
        "candidate_object_windows"
    ]
    assert before
    assert sorted(after) == sorted(
        [z0, z1, r0 + 2, r1 + 2, c0, c1] for z0, z1, r0, r1, c0, c1 in before
    )


def test_v1_memory_stays_on_v1_writer_and_counts(monkeypatch):
    dependent._no_producer(monkeypatch)
    series = dependent._series()
    memory = dependent._memory(
        series,
        {
            "femur": (2, 3, 6, 10, 13, 20),
            "tibia": (3, 4, 10, 15, 13, 21),
            "medial_meniscus": (4, 5, 11, 12, 10, 15),
        },
    )

    def v2_forbidden(*args, **kwargs):
        raise AssertionError("v1 memory must not calibrate or write a v2 profile")

    monkeypatch.setattr(writer, "leg_calibration", v2_forbidden)
    monkeypatch.setattr(writer, "profile_territory", v2_forbidden)
    result = locator.locate_objects(
        dependent._study(series, knee_side="left", anchors={}), memory
    )
    part = result["objects"]["medial_meniscus"]
    assert part["regions"][0]["window"] == (3, 4, 12, 13, 8, 13)
    assert part["profile"]["source"]["procedure"] == writer._PROCEDURE
    assert all(name.startswith("squint/v1/") for name in part["profile"]["banks"])
    expected = [
        writer.profile_window(series, tuple(r["window"]), subject="medial_meniscus")
        for r in part["regions"]
    ]
    assert part["profile"] == writer.merge_profiles(expected, subject="medial_meniscus")


def _conflicted_anchor():
    base = dependent._complete_anchor("femur", [0, 0, 0])
    base["status"] = "conflict"
    base["conflicts"] = [{"code": "explicit_native_view_contradiction"}]
    territories = []
    uids = ["sag", "cor", "ax"]
    for index, uid in enumerate(uids):
        t = dependent._anchor_territory("femur", (2, 3, 6, 10, 13, 20))
        t["series_uid"] = uid
        base["key_planes"][anatomy._ORIENTATIONS[index]]["series_uid"] = uid
        checks = [
            {
                "against_series_uid": other,
                "outcome": (
                    "consistent"
                    if {uid, other} == {"sag", "cor"}
                    else "the_other_views_section_lies_mostly_in_another_territory"
                ),
            }
            for other in uids
            if other != uid
        ]
        t["provenance"]["cross_view_checks"] = checks
        territories.append(t)
    base["territories"] = territories
    return base


def test_conflict_pair_drops_third_by_name_and_never_keeps_a_complete_reference():
    anchor = _conflicted_anchor()
    before = anatomy._json_safe(anchor)
    resolved = anatomy.resolve_anchor_views(anchor)
    assert resolved["status"] == "partial"
    assert resolved["reference_lps"] is None
    assert set(resolved["key_planes"]) == {"sagittal", "coronal"}
    assert {t["series_uid"] for t in resolved["territories"]} == {"sag", "cor"}
    resolution = resolved["view_resolution"]
    assert resolution["code"] == "partial_anchor_two_agree_third_contradicts_both"
    assert resolution["dropped_views"] == [
        {"series_uid": "ax", "reason": "contradicts_both_members_of_the_agreeing_pair"}
    ]
    assert resolution["original_conflicts"] == anchor["conflicts"]
    assert anatomy._json_safe(anchor) == before
    assert anchor_code(resolved) == "valid"
    series = dependent._series()
    state = anatomy.study_anchors(
        {"study_uid": dependent.STUDY, "anchors": {"femur": anchor}},
        {uid: {**series, "series_uid": uid} for uid in ("sag", "cor", "ax")},
    )
    assert state["usable"]["femur"]["anchor"]["status"] == "partial"
    assert len(state["usable"]["femur"]["territories"]) == 2
    assert (
        state["bones"]["femur"]["view_resolution"]["dropped_views"]
        == resolution["dropped_views"]
    )


@pytest.mark.parametrize(
    "defect",
    ["two_views", "silent_pair", "opposed_pair", "missing_second_contradiction"],
)
def test_conflict_without_explicit_triad_stays_unanchored(defect):
    anchor = _conflicted_anchor()
    if defect == "two_views":
        anchor["territories"] = anchor["territories"][:2]
        for t in anchor["territories"]:
            t["provenance"]["cross_view_checks"] = [
                c
                for c in t["provenance"]["cross_view_checks"]
                if c["against_series_uid"] != "ax"
            ]
    elif defect == "silent_pair":
        for t in anchor["territories"][:2]:
            t["provenance"]["cross_view_checks"][0]["outcome"] = (
                "no_carried_place_on_this_slice"
            )
    elif defect == "opposed_pair":
        anchor["territories"][0]["provenance"]["cross_view_checks"].append(
            {
                "against_series_uid": "cor",
                "outcome": "the_other_views_section_lies_mostly_in_another_territory",
            }
        )
    else:
        for t in anchor["territories"]:
            t["provenance"]["cross_view_checks"] = [
                c
                for c in t["provenance"]["cross_view_checks"]
                if {t["series_uid"], c["against_series_uid"]} != {"cor", "ax"}
            ]
    result = anatomy.resolve_anchor_views(anchor)
    assert result["status"] == "conflict"
    assert result["view_resolution"]["code"] == "conflict_without_unique_agreeing_pair"
    state = anatomy.study_anchors(
        {"study_uid": dependent.STUDY, "anchors": {"femur": anchor}}, {}
    )
    assert "femur" not in state["usable"]


def test_usable_partial_anchor_is_unchanged():
    anchor = _conflicted_anchor()
    anchor["status"] = "partial"
    assert anatomy.resolve_anchor_views(anchor) == anchor


@pytest.mark.parametrize("anchor", [None, {}, {"schema": ANCHOR_SCHEMA}])
def test_invalid_anchor_has_a_named_refusal(anchor):
    result = anatomy.resolve_anchor_views(anchor)
    assert result["status"] == "unavailable"
    assert result["view_resolution"]["code"] != "valid"


def test_missing_leg_map_and_deadline_keep_named_unavailable_states(monkeypatch):
    series, femur, _built, _profiles, memory = _v2_dependent()
    missing = dependent._study(series, knee_side="left", anchors={"femur": femur})
    missing["leg_maps"] = {}
    result = locator.locate_objects(missing, memory)
    assert result["objects"]["femur"]["profile"] is None
    assert result["objects"]["femur"]["evidence"]["reading_refusals"]
    assert result["objects"]["medial_meniscus"]["evidence"]["reading_refusals"]
    late = locator.locate_objects(missing, memory, deadline=0.0)
    assert all(row["profile"] is None for row in late["objects"].values())
    assert all(
        row["evidence"]["reason"] == "deadline_before_search"
        for row in late["objects"].values()
    )


# ---------------------------------------------------------------------------
# squint first: the 2 mm reading waits for the question that names it
# ---------------------------------------------------------------------------


def _watch_fine_readings(monkeypatch) -> list[str]:
    """Each call to the territory writer's 2 mm reader, by the subject it was made for."""
    calls: list[str] = []
    real = writer.refine_territory

    def watched(series, territory, leg_map, **kwargs):
        calls.append(territory["subject"])
        return real(series, territory, leg_map, **kwargs)

    monkeypatch.setattr(writer, "refine_territory", watched)
    return calls


def _bone_study(tmp_path, *, native_mask: bool = False):
    """A femur given by its anchor, with the native pixels a 2 mm reading needs."""
    series, leg, territory = _native_bone(tmp_path)
    if native_mask:
        support = np.zeros((1, 16, 16), dtype=bool)
        support[0, 0, 0] = support[0, -1, -1] = True
        support[0, 4:8, 4:8] = True
        territory["native_support"] = {
            "mask": support,
            "offset_rc": [60, 60],
            "slices": [0],
        }
    coarse = writer.profile_territory(series, territory, leg, subject="femur")
    study = {
        "study_uid": territory["study_uid"],
        "series": [series],
        "leg_maps": {series["series_uid"]: leg},
        "anchors": {"femur": _anchor(series, territory)},
    }
    return study, {"cases": [_case(coarse, "femur")]}, coarse


def _scales(profile) -> set[float]:
    fields = [parse_territory_bank_name(name) for name in profile["banks"]]
    assert all(field is not None for field in fields)
    return {field["scale_mm"] for field in fields if field is not None}


#: What a located object's evidence says of its profile's payload, not of where it is.
_PROFILE_EVIDENCE = (
    "profile_reading",
    "fine_reading",
    "candidate_costs_by_view",
    "candidate_profile_catalog",
    "candidate_bank_catalog",
    "candidate_series_context_catalog",
)


def _without_profile_refs(value):
    """A content id names a payload; a payload that differs has a different one."""
    if isinstance(value, dict):
        return {
            key: _without_profile_refs(item)
            for key, item in value.items()
            if key != "profile_ref"
        }
    if isinstance(value, list):
        return [_without_profile_refs(item) for item in value]
    return value


def _placement(located: dict) -> dict:
    """Everything that places an object and nothing that is a reading's payload."""
    return {
        "status": located["status"],
        "regions": located["regions"],
        "territories": located["territories"],
        "evidence": {
            key: _without_profile_refs(value)
            for key, value in located["evidence"].items()
            if key not in _PROFILE_EVIDENCE
        },
        "candidates": [
            {key: item.get(key) for key in ("series_uid", "window", "territory_origin")}
            for item in located["candidate_profiles"]
        ],
    }


def test_the_deferral_keyword_is_off_for_direct_and_reference_callers():
    for function in (
        locator.locate_objects,
        anatomy.locate_anatomy_first,
        anatomy._anchored_object,
    ):
        parameter = inspect.signature(function).parameters["refine_finalists"]
        assert parameter.default is True
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY


def test_deferred_location_places_a_bone_alike_and_holds_only_its_coarse_reading(
    tmp_path, monkeypatch
):
    study, memory, coarse = _bone_study(tmp_path)
    calls = _watch_fine_readings(monkeypatch)
    reference = locator.locate_objects(study, memory)
    assert calls == ["femur"]
    deferred = locator.locate_objects(study, memory, refine_finalists=False)
    assert calls == ["femur"]  # the deferred location read no 2 mm
    paired, bone = reference["objects"]["femur"], deferred["objects"]["femur"]
    # Where the bone is, and the addresses its readings carry, are not touched.
    assert _placement(bone) == _placement(paired)
    assert bone["regions"][0]["territory"]["origin"] == "anchor_structure"
    # The profile is exactly the coarse reading held: no fine bank, no refusal marker.
    assert _scales(paired["profile"]) == {10.0, 2.0}
    assert _scales(bone["profile"]) == {10.0}
    assert bone["profile"] == writer.merge_profiles([coarse], subject="femur")
    assert anatomy._object_coarse_banks(bone["profile"]) == (
        anatomy._object_coarse_banks(paired["profile"])
    )
    # The evidence says what each location read, and nothing it did not.
    assert paired["evidence"]["profile_reading"] == (
        "leg_tercile_territory_v2_10mm_and_2mm"
    )
    assert "fine_reading" not in paired["evidence"]
    assert "fine_reading" not in reference["evidence"]
    assert bone["evidence"]["profile_reading"] == "leg_tercile_territory_v2_10mm"
    assert bone["evidence"]["fine_reading"] == {
        "policy": anatomy.FINE_READING_DEFERRED,
        "requested_at_location": 0,
        "deferred": 1,
    }
    assert deferred["evidence"]["fine_reading"] == anatomy.FINE_READING_DEFERRED
    json.dumps(deferred, allow_nan=False)
    # The question that names the bone then reads the same pair once: the profile is
    # the one the paired location wrote, and the fine counts are added a single time.
    objects = {"femur": bone}
    observed = squint_pipeline._bounded_observation(
        {"object": "femur", "question": "Fracture"}, study, objects, set(), None
    )
    assert observed["code"] == "measured"
    assert calls == ["femur", "femur"]
    assert objects["femur"]["profile"]["banks"] == paired["profile"]["banks"]
    assert held_readings(objects["femur"]["profile"]) == held_readings(
        paired["profile"]
    )


def test_a_bone_over_two_territories_ends_with_the_same_pairs_and_counts_nothing_twice(
    tmp_path, monkeypatch
):
    series, leg, first = _native_bone(tmp_path)
    second = copy.deepcopy(first)
    second["roles"][0, 3:5, 3:5] = ROLE_CONTEXT
    second["roles"][0, 2:4, 1:3] = ROLE_OBJECT
    second["object_share"][:] = np.nan
    second["object_share"][0, 2:4, 1:3] = 0.5
    anchor = _anchor(series, first)
    anchor["territories"] = [first, second]
    held = [
        writer.profile_territory(series, item, leg, subject="femur")
        for item in (first, second)
    ]
    study = {
        "study_uid": first["study_uid"],
        "series": [series],
        "leg_maps": {series["series_uid"]: leg},
        "anchors": {"femur": anchor},
    }
    memory = {"cases": [_case(writer.merge_profiles(held, subject="femur"), "femur")]}
    calls = _watch_fine_readings(monkeypatch)
    paired = locator.locate_objects(study, memory)["objects"]["femur"]
    assert len(paired["regions"]) == 2
    assert calls == ["femur", "femur"]
    bone = locator.locate_objects(study, memory, refine_finalists=False)["objects"][
        "femur"
    ]
    assert calls == ["femur", "femur"]
    assert _placement(bone) == _placement(paired)
    assert _scales(bone["profile"]) == {10.0}
    assert bone["profile"] == writer.merge_profiles(held, subject="femur")
    assert bone["evidence"]["fine_reading"]["deferred"] == 2
    # One question reads both territories' pairs; the next reads nothing more.
    objects, attempted = {"femur": bone}, set()
    observed = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, objects, attempted, None
    )
    assert observed["code"] == "measured"
    assert len(observed["regions"]) == 2
    assert calls == ["femur"] * 4
    assert objects["femur"]["profile"]["banks"] == paired["profile"]["banks"]
    assert held_readings(objects["femur"]["profile"]) == held_readings(
        paired["profile"]
    )
    again = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, objects, attempted, None
    )
    assert again["code"] == "shared_observation_already_available"
    assert calls == ["femur"] * 4
    assert objects["femur"]["profile"]["banks"] == paired["profile"]["banks"]


def test_a_bone_whose_native_mask_cannot_be_rebuilt_keeps_its_pair_when_deferred(
    tmp_path, monkeypatch
):
    study, memory, _coarse = _bone_study(tmp_path, native_mask=True)
    calls = _watch_fine_readings(monkeypatch)
    paired = locator.locate_objects(study, memory)["objects"]["femur"]
    bone = locator.locate_objects(study, memory, refine_finalists=False)["objects"][
        "femur"
    ]
    # The located record has only the address and digest. The original territory stays
    # on the runtime study, while the located profile holds only the coarse reading.
    assert calls == ["femur"]
    assert _scales(paired["profile"]) == {10.0, 2.0}
    assert _scales(bone["profile"]) == {10.0}
    assert bone["territories"][0]["native_support"] is None
    assert bone["territories"][0]["native_support_address"]["support_count"] > 0
    assert bone["evidence"]["fine_reading"] == {
        "policy": anatomy.FINE_READING_DEFERRED,
        "requested_at_location": 0,
        "deferred": 1,
    }
    assert bone["evidence"]["profile_reading"] == "leg_tercile_territory_v2_10mm"
    # A named question can refine from the original retained mask, once.
    objects = {"femur": bone}
    observed = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, objects, set(), None
    )
    assert observed["code"] == "measured"
    assert observed["unavailable_regions"] == []
    assert calls == ["femur", "femur"]
    assert _scales(objects["femur"]["profile"]) == {10.0, 2.0}


def test_deferred_location_leaves_dependent_finalists_at_their_coarse_reading(
    monkeypatch,
):
    series, femur, built, profiles, memory = _v2_dependent()
    study = dependent._study(series, knee_side="left", anchors={"femur": femur})
    calls = _watch_fine_readings(monkeypatch)
    reference = locator.locate_objects(study, memory)
    assert calls == ["femur", "medial_meniscus"]
    calls.clear()
    deferred = locator.locate_objects(study, memory, refine_finalists=False)
    # The femur's and dependent's readings both wait for their named questions.
    assert calls == []
    paired = reference["objects"]["medial_meniscus"]
    part = deferred["objects"]["medial_meniscus"]
    assert _placement(part) == _placement(paired)
    assert part["profile"] is not None
    windows = [anatomy._object_window(t) for t in built["territories"]]
    held = [profiles[windows.index(tuple(r["window"]))] for r in part["regions"]]
    assert part["profile"] == writer.merge_profiles(held, subject="medial_meniscus")
    # This fixture holds no native pixels: the paired location carries the reader's
    # named refusal, and the deferred one never asked.
    marker = paired["profile"]["source"]["lineage"][0]["fine_reading"]
    assert marker["code"] == "territory_refinement_unavailable"
    assert "fine_reading" not in part["profile"]["source"]["lineage"][0]
    assert part["evidence"]["fine_reading"] == {
        "policy": anatomy.FINE_READING_DEFERRED,
        "requested_at_location": 0,
        "deferred": 1,
    }
    assert "fine_reading" not in paired["evidence"]
    paired_cost = next(iter(paired["evidence"]["candidate_costs_by_view"].values()))
    cost = next(iter(part["evidence"]["candidate_costs_by_view"].values()))
    assert (paired_cost["full_profiles_materialized"], cost) == (
        1,
        {**paired_cost, "full_profiles_materialized": 0},
    )
    assert deferred["evidence"]["fine_reading"] == anatomy.FINE_READING_DEFERRED
    assert "fine_reading" not in reference["evidence"]
    json.dumps(deferred, allow_nan=False)


def test_deferred_location_changes_nothing_on_a_v1_memory(monkeypatch):
    dependent._no_producer(monkeypatch)
    series = dependent._series()
    memory = dependent._memory(
        series,
        {
            "femur": (2, 3, 6, 10, 13, 20),
            "tibia": (3, 4, 10, 15, 13, 21),
            "medial_meniscus": (4, 5, 11, 12, 10, 15),
        },
    )

    def v2_forbidden(*args, **kwargs):
        raise AssertionError("v1 memory must not calibrate or write a v2 profile")

    monkeypatch.setattr(writer, "leg_calibration", v2_forbidden)
    monkeypatch.setattr(writer, "profile_territory", v2_forbidden)
    monkeypatch.setattr(writer, "refine_territory", v2_forbidden)
    study = dependent._study(series, knee_side="left", anchors={})
    reference = locator.locate_objects(study, memory)
    deferred = locator.locate_objects(study, memory, refine_finalists=False)
    assert json.dumps(deferred, sort_keys=True, default=str) == json.dumps(
        reference, sort_keys=True, default=str
    )
    assert "fine_reading" not in deferred["evidence"]
