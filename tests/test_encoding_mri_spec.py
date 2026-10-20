from __future__ import annotations

import numpy as np
import pytest

from knee.encoding.handoff import encode_observation
from knee.encoding.mri_spec import BASE_SLICE_VIEWS, make_mri_spec
from knee.encoding.operation import digest, encode_study, validate_spec
from knee.objects.assignments import OBJECT_CODES


def test_factory_covers_all_canonical_nonzero_objects_and_both_provenances() -> None:
    spec = make_mri_spec()
    expected = {name for name, code in OBJECT_CODES.items() if code != 0}
    profiles = [item for item in spec["profiles"] if item["support"] == "a1_objects"]
    assert len(profiles) == len(expected) * 2 * len(BASE_SLICE_VIEWS)
    assert {profile["object"] for profile in profiles} == expected
    assert {profile["provenance"] for profile in profiles} == {"native", "laid"}
    assert {profile["kind"] for profile in profiles} == {"resolved"}
    assert {profile["support"] for profile in profiles} == {"a1_objects"}
    assert {tuple(profile["view"]) for profile in profiles} == set(BASE_SLICE_VIEWS)
    assert len({tuple(profile["readings"][0].items()) for profile in profiles}) == 1


def test_factory_is_accepted_and_uses_one_shared_composition_layout() -> None:
    spec = make_mri_spec()
    prepared = validate_spec(spec)
    composition = prepared["composition"]
    assert composition is not None
    assert len(composition.view_roles) == len(BASE_SLICE_VIEWS)
    assert set(composition.profile_layouts) == {
        name for name, code in OBJECT_CODES.items() if code != 0
    }
    fingerprints = {
        layout.compiled.fingerprint for layout in composition.profile_layouts.values()
    }
    assert fingerprints == {composition.layout.fingerprint}
    assert len(composition.expansion.mapping) == len(spec["banks"]) * 5 * 28


def test_measurement_reference_sets_are_empty_and_binding_meanings_stay_explicit() -> (
    None
):
    spec = make_mri_spec()
    assert all(profile["references"] == [] for profile in spec["profiles"])
    assert all(
        not any(
            "low" in reference or "high" in reference
            for reference in profile["references"]
        )
        for profile in spec["profiles"]
    )
    sample = spec["profiles"][0]
    bindings = {(item["bank"], item["metric"]): item for item in sample["readings"]}
    assert bindings[("lens_boolean", "low_signal")]["value"] == "b1_dark"
    assert bindings[("lens_boolean", "low_signal")]["available"] == "b1_available"
    assert bindings[("lens_raw_signal", "raw_signal")]["value"] == "acquired_plane"
    assert bindings[("lens_distance", "distance_mm")]["value"] == "b1_distance_mm"
    assert bindings[("acquisition_context", "view_orientation")]["path"] == ["view", 0]
    assert bindings[("acquisition_context", "fluid_sensitivity")]["path"] == ["view", 1]
    assert bindings[("acquisition_context", "fat_suppression")]["path"] == ["view", 2]
    plan_by_bank = {
        item["base_bank"]: item for item in spec["object_composition"]["bank_plans"]
    }
    assert {
        plan_by_bank[name]["scale_scope"]
        for name in ("lens_boolean", "lens_raw_signal", "lens_distance")
    } == {"retained_place"}
    assert plan_by_bank["acquisition_context"]["scale_scope"] == "acquisition_record"


def test_false_is_measured_word_while_unavailable_place_remains_unread() -> None:
    spec = make_mri_spec(view=BASE_SLICE_VIEWS[0])
    prepared = validate_spec(spec)
    profile = next(
        item
        for item in spec["profiles"]
        if item["object"] == "femur" and item["provenance"] == "native"
    )
    arrays = {
        "a1_objects": np.asarray([[3, 3]], dtype=np.uint8),
        "b1_dark": np.asarray([[False, True]], dtype=np.bool_),
        "b1_available": np.asarray([[True, False]], dtype=np.bool_),
        "acquired_plane": np.asarray([[12.0, 99.0]], dtype=np.float32),
        "b1_distance_mm": np.asarray([[0.25, 8.0]], dtype=np.float32),
    }
    record = {
        "artifact": "study/series.npz.xz",
        "series_uid": "series",
        "study_uid": "study",
        "view": list(BASE_SLICE_VIEWS[0]),
        "slice_index": 4,
        "arrays": {name: {"digest": digest(array)} for name, array in arrays.items()},
    }
    observation = {
        "artifact": record["artifact"],
        "series_uid": record["series_uid"],
        "object": "femur",
        "provenance": "native",
        "kind": "resolved",
        "support": "a1_objects",
        "view": list(BASE_SLICE_VIEWS[0]),
        "slices": [4],
        "label": 3,
        "count": 2,
    }
    addressed = encode_observation(
        record,
        observation,
        arrays,
        prepared["layout"],
        profile["readings"],
        {},
    )
    assert addressed.status == "missing_reference"
    assert addressed.encoding is not None
    metric = next(
        item
        for item in addressed.encoding.metrics
        if (item.bank, item.metric) == ("lens_boolean", "low_signal")
    )
    false_index = metric.row_names.index("False")
    assert metric.row_codes.tolist() == [false_index, -1]
    assert metric.source_available.tolist() == [True, False]
    assert addressed.encoding.bundle is not None
    assert metric.source_values.tolist() == [False, True]


def test_view_none_expands_five_roles_and_concrete_view_is_restricted() -> None:
    all_views = make_mri_spec(view=None)
    one_view = make_mri_spec(view=BASE_SLICE_VIEWS[2])
    all_base = [p for p in all_views["profiles"] if p["support"] == "a1_objects"]
    one_base = [p for p in one_view["profiles"] if p["support"] == "a1_objects"]
    assert len(all_base) == len(one_base) * 5
    assert {tuple(profile["view"]) for profile in one_base} == {BASE_SLICE_VIEWS[2]}
    assert len(validate_spec(one_view)["composition"].view_roles) == 5
    with pytest.raises(ValueError, match="view_not_in_base_slice_views"):
        make_mri_spec(view=("Axial", "0", "0"))


def test_absent_observations_remain_missing_observations_not_absent_objects(
    tmp_path,
) -> None:
    spec = make_mri_spec(view=BASE_SLICE_VIEWS[0])
    spec["storage"] = "npz_xz"
    prepared = validate_spec(spec)
    objects = {name: {} for name, code in OBJECT_CODES.items() if code != 0}
    result = {
        "study_uid": "study",
        "records": [],
        "main_records": [],
        "objects": objects,
    }
    statuses = encode_study(
        result,
        tmp_path,
        tmp_path,
        prepared["spec"],
        tmp_path / "encoded.json.xz",
        prepared=prepared,
    )
    assert statuses["profiles"]
    assert all(
        outcome["status"] == "missing_observation"
        for profile in statuses["profiles"]
        for outcome in profile["outcomes"]
    )
    assert all(
        "absent" not in outcome["status"]
        for profile in statuses["profiles"]
        for outcome in profile["outcomes"]
    )


def test_factory_encodes_acquisition_context_from_the_matching_record() -> None:
    selected_view = BASE_SLICE_VIEWS[4]
    spec = make_mri_spec(view=selected_view)
    prepared = validate_spec(spec)
    profile = next(
        item
        for item in spec["profiles"]
        if item["object"] == "femur"
        and item["provenance"] == "native"
        and item["support"] == "a1_objects"
    )
    arrays = {
        "a1_objects": np.asarray([[3, 3]], dtype=np.uint8),
        "b1_dark": np.asarray([[False, True]], dtype=np.bool_),
        "b1_available": np.asarray([[True, True]], dtype=np.bool_),
        "acquired_plane": np.asarray([[12.0, 14.0]], dtype=np.float32),
        "b1_distance_mm": np.asarray([[0.25, 0.5]], dtype=np.float32),
    }
    record = {
        "artifact": "study/series.npz.xz",
        "series_uid": "series",
        "study_uid": "study",
        "view": list(selected_view),
        "slice_index": 4,
        "arrays": {name: {"digest": digest(array)} for name, array in arrays.items()},
    }
    observation = {
        "artifact": record["artifact"],
        "series_uid": record["series_uid"],
        "object": "femur",
        "provenance": "native",
        "kind": "resolved",
        "support": "a1_objects",
        "view": list(selected_view),
        "slices": [4],
        "label": 3,
        "count": 2,
    }

    addressed = encode_observation(
        record,
        observation,
        arrays,
        prepared["layout"],
        profile["readings"],
        {},
    )

    assert addressed.encoding is not None
    assert addressed.status == "missing_reference"
    metrics = {(item.bank, item.metric): item for item in addressed.encoding.metrics}
    expected_context = {
        ("acquisition_context", "view_orientation"): "Axial",
        ("acquisition_context", "fluid_sensitivity"): "1",
        ("acquisition_context", "fat_suppression"): "1",
    }
    for key, value in expected_context.items():
        metric = metrics[key]
        rows = next(
            item
            for item in prepared["layout"].metric_rows
            if (item.bank, item.metric) == key
        )
        assert metric.status.value == "ok"
        assert metric.source_values.tolist() == [value, value]
        expected_row = rows.start + rows.names.index(value)
        assert metric.row_codes.tolist() == [expected_row] * 2
