from __future__ import annotations

from typing import Any

import numpy as np

from knee.encoding.mri_spec import make_mri_spec
from knee.encoding.operation import validate_spec
from knee.encoding.places import (
    BankSpec,
    EncodingCode,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    compile_layout,
)
from knee.encoding.slice_profile_adapter import encode_slice_profile_observation
from knee.receipt import digest

VALUE = "a3_femur_profile_area_mm2"
STATUS = "a3_femur_profile_status"


def _layout():
    result = compile_layout(
        LayoutSpec(
            "native-profile-test-v1",
            "native-profile-test-carrier-v1",
            (
                BankSpec(
                    "profile_area",
                    "retained per-slice area",
                    (MetricSpec("area_mm2", MetricKind.DIGIT),),
                ),
                BankSpec(
                    "profile_status",
                    "measured producer status",
                    (
                        MetricSpec(
                            "status",
                            MetricKind.WORDS,
                            ("not_read", "none", "body", "unreadable", "cut"),
                        ),
                    ),
                ),
            ),
        )
    )
    assert result is not None
    return result


def _profile_input(
    statuses: np.ndarray | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, np.ndarray], dict[str, Any]]:
    arrays = {
        VALUE: np.asarray([0.0, 2.75, 5.0], dtype=np.float64),
        STATUS: np.asarray([2, 2, 2] if statuses is None else statuses, dtype=np.int8),
    }
    record = {
        "study_uid": "study",
        "series_uid": "series",
        "artifact": "series.npz.xz",
        "view": ["Sagittal", "0", "0"],
        "slice_index": 1,
        "arrays": {name: {"digest": digest(array)} for name, array in arrays.items()},
    }
    observation = {
        "object": "femur",
        "provenance": "native",
        "kind": "reading",
        "series_uid": "series",
        "view": ["Sagittal", "0", "0"],
        "slices": [1, 2],
        "support": VALUE,
        "code": "pointer_body",
        "artifact": "series.npz.xz",
    }
    declaration = {
        "family": "native_slice_profile_values",
        "support": VALUE,
        "values": VALUE,
        "status": STATUS,
        "status_codes": {
            "not_read": 0,
            "none": 1,
            "body": 2,
            "unreadable": 3,
            "cut": 4,
        },
        "measured_status_names": ["body"],
        "unit": "mm^2",
        "scope": "cheap marrow-like per-slice support area; not whole-bone extent",
    }
    return record, observation, arrays, declaration


def _bindings():
    return [
        {
            "bank": "profile_area",
            "metric": "area_mm2",
            "value": VALUE,
            "available": STATUS,
        },
        {
            "bank": "profile_status",
            "metric": "status",
            "source": "status_words",
        },
    ]


def test_mri_spec_installs_exact_profile_sources_without_numeric_norms():
    spec = make_mri_spec()
    validate_spec(spec)
    profile_rows = [
        row
        for row in spec["profiles"]
        if row.get("support_layout", {}).get("family") == "native_slice_profile_values"
    ]
    assert len(profile_rows) == 5
    assert {
        (row["object"], row["support"], row["support_layout"]["values"])
        for row in profile_rows
    } == {
        ("femur", "a3_femur_profile_area_mm2", "a3_femur_profile_area_mm2"),
        ("tibia", "a3_tibia_profile_area_mm2", "a3_tibia_profile_area_mm2"),
        ("joint_fluid", "a3_recess_profile_area_mm2", "a3_recess_profile_area_mm2"),
        ("fibula", "a3_fibula_profile_area_mm2", "a3_fibula_profile_area_mm2"),
        ("fibula", "a3_fibula_head_area_mm2", "a3_fibula_head_area_mm2"),
    }
    assert all(tuple(row.get("references", ())) == () for row in profile_rows)
    assert all(row["support_layout"]["unit"] == "mm^2" for row in profile_rows)
    assert all(row["support_layout"]["scope"] for row in profile_rows)
    head = next(
        row for row in profile_rows if row["support"] == "a3_fibula_head_area_mm2"
    )
    assert head["support_layout"]["measured_status_names"] == ["head_still_a_disc"]
    assert head["support_layout"]["status_codes"]["unread"] == 0


def test_measured_status_is_a_word_while_area_keeps_missing_reference():
    record, observation, arrays, declaration = _profile_input()
    result = encode_slice_profile_observation(
        record, observation, arrays, _layout(), _bindings(), {}, declaration
    )
    assert result.status == EncodingCode.MISSING_REFERENCE.value
    assert result.encoding is not None
    area, status = result.encoding.metrics
    assert area.status is EncodingCode.MISSING_REFERENCE
    np.testing.assert_array_equal(area.source_values, [2.75, 5.0])
    assert area.row_codes.tolist() == [-1, -1]
    assert status.status is EncodingCode.OK
    assert status.source_values.tolist() == ["body", "body"]
    assert status.row_codes.tolist() == [2, 2]
    assert result.metadata["status_word_source"]["array"] == STATUS
    assert result.metadata["status_word_source"]["source_ref"]["digest"] == digest(
        arrays[STATUS]
    )


def test_unread_selected_status_stays_a_named_unknown_not_a_zero_measurement():
    record, observation, arrays, declaration = _profile_input(
        np.asarray([2, 0, 2], dtype=np.int8)
    )
    observation["slices"] = [0, 1]
    result = encode_slice_profile_observation(
        record, observation, arrays, _layout(), _bindings(), {}, declaration
    )
    assert result.status == "slice_profile_address_includes_unmeasured_sample"
    assert result.encoding is None
    assert result.coordinates is None


def test_unrecognized_status_code_has_a_distinct_refusal():
    record, observation, arrays, declaration = _profile_input(
        np.asarray([2, 2, 99], dtype=np.int16)
    )
    observation["slices"] = [1, 2]
    result = encode_slice_profile_observation(
        record, observation, arrays, _layout(), _bindings(), {}, declaration
    )
    assert result.status == "slice_profile_status_code_unrecognized"
    assert result.encoding is None


def test_status_words_source_is_restricted_to_slice_profile_family():
    spec = make_mri_spec(view=("Sagittal", "0", "0"))
    profile = spec["profiles"][0]
    profile["readings"][0] = {
        "bank": "lens_boolean",
        "metric": "low_signal",
        "source": "status_words",
    }
    try:
        validate_spec(spec)
    except ValueError as error:
        assert "invalid_profile_reading_binding" in str(error)
    else:
        raise AssertionError("status_words must not enable ordinary profiles")
