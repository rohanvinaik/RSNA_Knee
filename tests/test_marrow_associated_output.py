"""Associated marrow readings link only products already retained in each saved record."""

import copy

import numpy as np

from knee.collapse.observations import describe_objects
from knee.receipt import digest, merged_receipt

NAMES = ("femur", "tibia", "patella", "fibula")


def _record(uid, bones, array_names):
    values = {name: np.arange(4, dtype=np.float32) for name in array_names}
    record = {
        "study_uid": "study",
        "series_uid": uid,
        "view": ["Sagittal", "fat-bright", "unsuppressed"],
        "slice_index": 2,
        "artifact": f"study/{uid}-bones.npz",
        "bones": bones,
        "arrays": {name: {"digest": digest(array)} for name, array in values.items()},
        "observations": [],
        "observations_unresolved": [],
        "assignments": {"codes": {}},
        "main_slice": {"object": "femur"},
    }
    return record, values


def _bone(outcome, light):
    return {"outcome": outcome, "marrow_light": light}


def _fixture():
    common = [
        "a1_objects",
        "a3_femur_reference_light",
        "a3_femur_profile_area_mm2",
        "a3_femur_fine_profile_area_mm2",
        "a3_femur_laid_region",
        "a3_tibia_reference_light",
        "a3_tibia_profile_area_mm2",
    ]
    first, first_arrays = _record(
        "s1",
        {
            "codes": {"femur": "identified", "tibia": "ambiguous"},
            "femur": _bone("identified", 812.5),
            "tibia": _bone("ambiguous", 640.0),
        },
        common,
    )
    unresolved, unresolved_arrays = _record(
        "s2",
        {
            "codes": {
                "femur": "unreadable",
                "tibia": "bone_not_named_on_the_middle_slice",
            },
            "femur": _bone("unreadable", None),
        },
        ["a1_objects", "a3_femur_reference_light", "a3_femur_profile_status"],
    )
    no_source, _ = _record("s3", {"codes": {}}, ["a1_objects"])
    laid_only, _ = _record(
        "s4",
        {
            "codes": {
                "femur": "fat_suppressed_not_profiled",
                "tibia": "fat_suppressed_not_profiled",
            }
        },
        ["a3_femur_laid_region", "a3_tibia_laid_region", "a3_femur_plane_region"],
    )
    records = [first, unresolved, no_source, laid_only]
    arrays = {"s1": first_arrays, "s2": unresolved_arrays}
    return records, arrays


def _marrow(described, name):
    return described[name]["associated_fields"]["marrow"]


def _by_series(field):
    return {entry["series_uid"]: entry for entry in field["series"]}


def test_real_describer_and_merged_receipt_keep_old_evidence_and_inputs_unchanged():
    records, _ = _fixture()
    before = copy.deepcopy(records)
    described = describe_objects(records, NAMES)
    assert records == before

    obs = {
        "object": "femur",
        "provenance": "native",
        "kind": "resolved",
        "series_uid": "s1",
        "view": ["Sagittal", "fat-bright", "unsuppressed"],
        "slices": [2],
        "code": "identified",
        "count": 4,
        "off_plane_mm": 0.0,
        "support": "a1_objects",
        "note": "native named bone",
        "artifact": records[0]["artifact"],
        "row": None,
        "label": 3,
    }
    records[0]["observations"] = [obs]
    described = describe_objects(records, NAMES)
    receipt = merged_receipt(
        None, {"version": 1}, "study", ["s1", "s2", "s3"], records, {}, None, described
    )
    assert (
        receipt["objects"]["study"]["femur"]["observations"]["native"]["resolved"][
            "a1_objects"
        ][0]["label"]
        == 3
    )
    assert (
        receipt["objects"]["study"]["femur"]["associated_fields"]
        == described["femur"]["associated_fields"]
    )
    assert described["patella"]["associated_fields"]["marrow"]["availability"] == (
        "native_marrow_measurement_unavailable"
    )
    assert described["fibula"]["associated_fields"]["marrow"]["unavailability_reason"]
    assert described["femur"]["native_series"] == ["s1"]


def test_native_profile_and_calibration_refs_resolve_to_exact_saved_keys_and_digests():
    records, arrays = _fixture()
    by_uid = {record["series_uid"]: record for record in records}
    described = describe_objects(records, NAMES)
    field = _marrow(described, "femur")
    assert field["availability"] == "native_calibration_and_profile_reading"
    s1 = _by_series(field)["s1"]
    assert s1["calibration"]["marrow_light"] == 812.5
    assert "whole-bone support" in s1["calibration"]["support"]["meaning"]
    assert s1["calibration"]["support"]["label"] == 3
    refs = [s1["calibration"]["reference"], s1["calibration"]["support"]["reference"]]
    refs.extend(s1["profile_references"])
    assert {ref["name"] for ref in refs} == {
        "a3_femur_reference_light",
        "a1_objects",
        "a3_femur_profile_area_mm2",
        "a3_femur_fine_profile_area_mm2",
    }
    for ref in refs:
        record = by_uid[s1["series_uid"]]
        assert ref["artifact"] == record["artifact"]
        assert ref["digest"] == record["arrays"][ref["name"]]["digest"]
        assert ref["digest"] == digest(arrays[s1["series_uid"]][ref["name"]])
        assert ref["dtype_shape"] == "not_retained_in_receipt"
        assert "laid" not in ref["name"]


def test_refusal_unreadable_and_missing_native_products_remain_distinct():
    records, _ = _fixture()
    described = describe_objects(records, NAMES)
    f = _by_series(_marrow(described, "femur"))
    assert f["s2"]["reader_outcome"] == "unreadable"
    assert f["s2"]["availability"] == "native_reader_unresolved"
    assert f["s2"]["calibration"]["marrow_light"] is None
    assert f["s2"]["calibration"]["reference"] is not None
    assert [ref["name"] for ref in f["s2"]["profile_references"]] == [
        "a3_femur_profile_status"
    ]
    tibia = _by_series(_marrow(described, "tibia"))
    assert tibia["s1"]["availability"] == "native_calibration_and_profile_reading"
    assert tibia["s2"]["reader_outcome"] == "bone_not_named_on_the_middle_slice"
    assert tibia["s2"]["basis_refusal_code"] == "bone_not_named_on_the_middle_slice"
    assert tibia["s2"]["availability"] == "native_marrow_measurement_unavailable"
    assert f["s4"]["reader_outcome"] == "fat_suppressed_not_profiled"
    assert f["s4"]["basis_refusal_code"] == "fat_suppressed_not_profiled"
    assert f["s4"]["availability"] == "native_marrow_measurement_unavailable"
    assert f["s4"]["profile_references"] == []
    assert f["s3"]["reader_outcome"] is None
    assert f["s3"]["basis_refusal_code"] is None
    assert f["s3"]["availability"] == "native_marrow_measurement_unavailable"
    assert f["s3"]["calibration"]["support"]["reference"] is None
    assert _marrow(described, "patella")["measurement"] is None
    assert _marrow(described, "fibula")["measurement"] is None


def test_missing_artifact_never_creates_a_resolvable_native_reference():
    records, _ = _fixture()
    records[0].pop("artifact")
    entry = _by_series(_marrow(describe_objects(records, NAMES), "femur"))["s1"]
    assert entry["availability"] == "native_marrow_measurement_unavailable"
    assert entry["calibration"]["reference"] is None
    assert entry["calibration"]["support"]["reference"] is None
    assert entry["profile_references"] == []


def test_invalid_measured_calibration_stays_unresolved_not_missing_basis():
    records, _ = _fixture()
    records[0]["bones"]["femur"]["marrow_light"] = None
    entry = _by_series(_marrow(describe_objects(records, NAMES), "femur"))["s1"]
    assert entry["availability"] == "native_reader_unresolved"
    assert entry["reader_outcome"] == "identified"
    assert entry["basis_refusal_code"] is None
    assert entry["calibration"]["reference"] is not None


def test_no_native_reader_source_is_named_unavailable():
    described = describe_objects([], NAMES)
    assert _marrow(described, "femur")["availability"] == (
        "native_marrow_measurement_unavailable"
    )
    assert _marrow(described, "tibia")["availability"] == (
        "native_marrow_measurement_unavailable"
    )
