from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from knee.encoding.places import (
    BankSpec,
    EncodingCode,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    NumericReference,
    compile_layout,
)
from knee.encoding.scoped import ScopedEncoding
from knee.encoding.slice_profile_adapter import encode_slice_profile_observation
from knee.receipt import digest

VALUE = "a3_femur_profile_area_mm2"
STATUS = "a3_femur_profile_status"
SUPPORT = VALUE


def compiled():
    layout = compile_layout(
        LayoutSpec(
            "slice-profile-v1",
            "slice-profile-carrier-v1",
            (BankSpec("bone", "profile", (MetricSpec("area", MetricKind.DIGIT),)),),
        )
    )
    assert layout is not None
    return layout


def payload(
    *,
    slices: tuple[int, ...] = (2, 1),
    values: np.ndarray | None = None,
    statuses: np.ndarray | None = None,
    kind: str = "reading",
) -> tuple[dict[str, Any], dict[str, Any], dict[str, np.ndarray], dict[str, Any]]:
    value_array = (
        np.asarray([0.0, 4.5, 8.0], dtype=np.float64)
        if values is None
        else np.asarray(values)
    )
    status_array = (
        np.asarray([1, 2, 2], dtype=np.int8)
        if statuses is None
        else np.asarray(statuses)
    )
    arrays = {VALUE: value_array, STATUS: status_array}
    record = {
        "study_uid": "study",
        "series_uid": "series",
        "artifact": "series.npz.xz",
        "view": ("sagittal", "T1", "no_fs"),
        "slice_index": 1,
        "arrays": {name: {"digest": digest(array)} for name, array in arrays.items()},
    }
    observation = {
        "object": "femur",
        "provenance": "native",
        "kind": kind,
        "series_uid": "series",
        "view": list(record["view"]),
        "slices": slices,
        "support": SUPPORT,
        "code": "pointer_body",
        "artifact": "series.npz.xz",
    }
    declaration = {
        "family": "native_slice_profile_values",
        "support": SUPPORT,
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
        "unit": "mm2",
        "scope": "native_series_profile",
    }
    return record, observation, arrays, declaration


def numeric_binding() -> dict[str, str]:
    return {
        "bank": "bone",
        "metric": "area",
        "source": "array",
        "value": VALUE,
        "available": STATUS,
    }


def reference(layout, *, low=1.0, high=5.0):
    return NumericReference(
        layout.fingerprint,
        "bone",
        "area",
        "source-profile-reference",
        "explicit test source",
        "mm2",
        low,
        high,
    )


def test_values_remain_at_the_observation_slice_addresses_without_pixel_points():
    layout = compiled()
    record, observation, arrays, declaration = payload()
    result = encode_slice_profile_observation(
        record,
        observation,
        arrays,
        layout,
        [numeric_binding()],
        {("bone", "area"): reference(layout)},
        declaration,
    )
    assert isinstance(result, ScopedEncoding)
    assert result.status == EncodingCode.OK.value
    assert result.address_kind == "series_slice"
    assert result.coordinates.tolist() == [[2], [1]]
    assert result.coordinates.shape == (2, 1)
    assert not result.coordinates.flags.writeable
    metric = result.encoding.metrics[0]
    np.testing.assert_array_equal(metric.source_values, [8.0, 4.5])
    np.testing.assert_array_equal(metric.source_available, [True, True])
    assert metric.row_codes.tolist() == [2, 1]
    assert result.metadata["source_address"]["unit"] == "mm2"
    assert result.metadata["scope_address"] == {
        "series_uid": "series",
        "view": ["sagittal", "T1", "no_fs"],
        "axis": "native_series_slice_index",
        "measurement": VALUE,
    }
    assert (
        result.metadata["meaning"]
        == "per-slice scalar readings; no plane pixels or physical volume"
    )


def test_real_values_without_an_authored_numeric_reference_remain_named_missing_reference():
    layout = compiled()
    record, observation, arrays, declaration = payload()
    result = encode_slice_profile_observation(
        record, observation, arrays, layout, [numeric_binding()], {}, declaration
    )
    assert result.status == EncodingCode.MISSING_REFERENCE.value
    assert result.encoding.bundle is not None
    metric = result.encoding.metrics[0]
    assert metric.status is EncodingCode.MISSING_REFERENCE
    assert metric.row_codes.tolist() == [-1, -1]
    np.testing.assert_array_equal(metric.source_values, [8.0, 4.5])
    assert result.metadata["source_refs"][VALUE]["digest"] == digest(arrays[VALUE])
    assert result.metadata["source_address"]["slice_indices"] == [2, 1]


def test_status_codes_are_explicit_and_unmeasured_observation_address_refuses():
    layout = compiled()
    record, observation, arrays, declaration = payload(
        statuses=np.asarray([2, 0, 2], dtype=np.int8)
    )
    observation["slices"] = [0, 1]
    result = encode_slice_profile_observation(
        record,
        observation,
        arrays,
        layout,
        [numeric_binding()],
        {("bone", "area"): reference(layout)},
        declaration,
    )
    assert result.status == "slice_profile_address_includes_unmeasured_sample"
    assert result.encoding is None
    assert result.coordinates is None


def test_unread_metric_keeps_slice_addresses_without_reading_profile_arrays():
    layout = compiled()
    record, observation, arrays, declaration = payload()
    record["arrays"] = {}
    binding = {
        "bank": "bone",
        "metric": "area",
        "source": "unread",
        "reason": "not in this view",
    }
    result = encode_slice_profile_observation(
        record, observation, arrays, layout, [binding], {}, declaration
    )
    assert result.status == EncodingCode.SILENT.value
    assert result.coordinates.tolist() == [[2], [1]]
    assert result.metadata["source_refs"] == {}
    assert result.metadata["unread_sources"][0]["reason"] == "not in this view"


def test_numeric_acquisition_context_is_broadcast_once_to_each_slice():
    layout = compiled()
    record, observation, arrays, declaration = payload()
    binding = {
        "bank": "bone",
        "metric": "area",
        "source": "record_context",
        "scope": "acquisition",
        "path": ["acquisition", "reference_light"],
    }
    record["acquisition"] = {"reference_light": 3.0}
    result = encode_slice_profile_observation(
        record,
        observation,
        arrays,
        layout,
        [binding],
        {("bone", "area"): reference(layout)},
        declaration,
    )
    assert result.status == EncodingCode.OK.value
    metric = result.encoding.metrics[0]
    np.testing.assert_array_equal(metric.source_values, [3.0, 3.0])
    np.testing.assert_array_equal(metric.source_available, [True, True])
    assert result.metadata["context_sources"][0]["path"] == [
        "acquisition",
        "reference_light",
    ]


def test_owner_view_and_slice_indices_are_not_fabricated_or_relabelled():
    layout = compiled()
    record, observation, arrays, declaration = payload()
    observation["view"] = ["coronal", "T1", "no_fs"]
    mismatch = encode_slice_profile_observation(
        record,
        observation,
        arrays,
        layout,
        [numeric_binding()],
        {("bone", "area"): reference(layout)},
        declaration,
    )
    assert mismatch.status == "slice_profile_view_mismatch"

    record, observation, arrays, declaration = payload(slices=(3,))
    out_of_range = encode_slice_profile_observation(
        record,
        observation,
        arrays,
        layout,
        [numeric_binding()],
        {("bone", "area"): reference(layout)},
        declaration,
    )
    assert out_of_range.status == "slice_profile_payload_shape_invalid"


@pytest.mark.parametrize("bad", [(), (-1,), (True,), (1, 1)])
def test_malformed_slice_addresses_have_named_refusal(bad):
    layout = compiled()
    record, observation, arrays, declaration = payload()
    observation["slices"] = bad
    result = encode_slice_profile_observation(
        record,
        observation,
        arrays,
        layout,
        [numeric_binding()],
        {("bone", "area"): reference(layout)},
        declaration,
    )
    assert result.status == "slice_profile_address_invalid"


def test_slice_address_outside_int64_has_named_refusal():
    layout = compiled()
    record, observation, arrays, declaration = payload()
    observation["slices"] = [2**80]
    result = encode_slice_profile_observation(
        record,
        observation,
        arrays,
        layout,
        [numeric_binding()],
        {("bone", "area"): reference(layout)},
        declaration,
    )
    assert result.status == "slice_profile_address_out_of_range"
    assert result.encoding is None
    assert result.coordinates is None
