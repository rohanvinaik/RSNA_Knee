from __future__ import annotations

from pathlib import Path

import numpy as np

from knee.array_archive import write_npz_xz
from knee.collapse.posterior import FOLLOWED, START_NAMES
from knee.encoding import binding_sources, handoff, trace_adapter
from knee.encoding.binding_sources import (
    record_context_place_reading,
    unread_place_reading,
)
from knee.encoding.operation import encode_study
from knee.encoding.places import MetricKind, MetricSpec
from knee.receipt import digest

VIEW = ("sagittal", "fluid", "fat-suppressed")
TRACE_SUPPORT = "a3_posterior_trace_test_object_points_lps"
TRACE_PREFIX = TRACE_SUPPORT.removesuffix("_points_lps")
TRACE_LAYOUT = {
    "family": "posterior_trace",
    "identity_sources": {
        "owner_artifact": "observation.artifact",
        "target_series_uid": "target_record.series_uid",
        "target_view": "target_record.view",
        "target_slice": "observation.slices[0]",
        "row": "observation.row",
    },
    "offsets_suffix": "_offsets",
    "slices_suffix": "_slices",
    "starts_suffix": "_starts",
    "stops_suffix": "_stops",
    "coordinates": "patient_lps",
    "availability": "finite_values",
}


def _fixture(tmp_path: Path):
    run_dir = tmp_path / "interiors"
    run_dir.mkdir()
    owner_uid = "source-series-axial"
    target_uid = "target-series-sagittal"
    owner_artifact = f"{owner_uid}.npz.xz"
    target_artifact = f"{target_uid}.npz.xz"
    arrays = {
        f"{TRACE_PREFIX}_points_lps": np.array(
            [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float64
        ),
        f"{TRACE_PREFIX}_light": np.array([1.0, 3.0], dtype=np.float32),
        f"{TRACE_PREFIX}_flank": np.array([2.0, 2.0], dtype=np.float32),
        f"{TRACE_PREFIX}_offsets": np.array([0, 2], dtype=np.int64),
        f"{TRACE_PREFIX}_slices": np.array([9], dtype=np.int32),
        f"{TRACE_PREFIX}_starts": np.array(
            [START_NAMES.index(FOLLOWED)], dtype=np.int8
        ),
        f"{TRACE_PREFIX}_stops": np.array([[0, 0]], dtype=np.int8),
    }
    write_npz_xz(run_dir / owner_artifact, arrays)
    descriptors = {name: {"digest": digest(value)} for name, value in arrays.items()}
    observation = {
        "object": "test_object",
        "provenance": "native",
        "kind": "reading",
        "series_uid": target_uid,
        "view": list(VIEW),
        "slices": [9],
        "code": "tube_followed",
        "count": 2,
        "support": TRACE_SUPPORT,
        "artifact": owner_artifact,
        "row": 0,
        "label": None,
    }
    target = {
        "study_uid": "test-study",
        "series_uid": target_uid,
        "view": VIEW,
        # Bootstrap middle differs from the trace's addressed slice.
        "slice_index": 8,
        "artifact": target_artifact,
        "arrays": {},
        "observations": [observation],
    }
    owner = {
        "study_uid": "test-study",
        "series_uid": owner_uid,
        "view": ("axial", "fluid", "fat-suppressed"),
        "slice_index": 12,
        "artifact": owner_artifact,
        "arrays": descriptors,
        "observations": [],
    }
    result = {
        "study_uid": target["study_uid"],
        "records": [target, owner],
        "main_records": [],
        "objects": {"test_object": {}},
    }
    return run_dir, result, target, owner, observation


def _spec(scope: str):
    return {
        "version": "trace-record-context-candidate-v1",
        "banks": [
            {
                "name": "trace_context",
                "facet": "retained acquisition descriptor",
                "metrics": [
                    {
                        "name": "view_orientation",
                        "kind": "words",
                        "words": ["sagittal", "coronal", "axial"],
                    }
                ],
            }
        ],
        "profiles": [
            {
                "object": "test_object",
                "provenance": "native",
                "kind": "reading",
                "support": TRACE_SUPPORT,
                "view": list(VIEW),
                "support_layout": TRACE_LAYOUT,
                "readings": [
                    {
                        "bank": "trace_context",
                        "metric": "view_orientation",
                        "source": "record_context",
                        "path": ["view", 0],
                        "scope": scope,
                    }
                ],
                "references": [],
            }
        ],
    }


def test_encode_study_reads_context_from_target_not_owner_or_middle(tmp_path):
    run_dir, result, target, owner, _observation = _fixture(tmp_path)
    status = encode_study(
        result,
        run_dir,
        tmp_path / "main",
        _spec("acquisition"),
        tmp_path / "encoded.json",
    )
    outcome = status["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "ok"
    assert outcome["address_kind"] == "patient_lps_points"
    assert outcome["place_count"] == 2
    assert outcome["counts"][0][:3] == [2, 0, 0]
    assert outcome["metrics"][0]["status"] == "ok"
    assert outcome["metadata"]["target_series_uid"] == target["series_uid"]
    assert outcome["metadata"]["owner_series_uid"] == owner["series_uid"]
    context = outcome["metadata"]["context_sources"][0]
    assert context["status"] == "available"
    assert context["value"] == "sagittal"
    assert context["source_address"]["series_uid"] == target["series_uid"]
    assert context["source_address"]["artifact"] == target["artifact"]
    assert context["source_address"]["owner_series_uid"] == owner["series_uid"]
    assert context["source_address"]["trace_slice_index"] == 9


def test_record_plane_scope_refuses_target_middle_mismatch(tmp_path):
    run_dir, result, _target, _owner, _observation = _fixture(tmp_path)
    status = encode_study(
        result,
        run_dir,
        tmp_path / "main",
        _spec("record_plane"),
        tmp_path / "encoded.json",
    )
    outcome = status["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "context_record_plane_slice_mismatch"
    assert outcome["metadata"]["observation"]["slices"] == [9]
    assert outcome["metadata"]["bindings"][0]["scope"] == "record_plane"
    assert outcome.get("points_lps") is None


def test_ordinary_and_trace_adapters_share_the_context_reader():
    assert handoff.record_context_place_reading is record_context_place_reading
    assert trace_adapter.record_context_place_reading is record_context_place_reading
    assert binding_sources.record_context_place_reading is record_context_place_reading


def test_context_unavailable_and_unread_are_distinct_zero_stride_readings():
    metric = MetricSpec("orientation", MetricKind.WORDS, ("sagittal",))
    context_binding = {
        "bank": "context",
        "metric": "orientation",
        "source": "record_context",
        "path": ["missing"],
        "scope": "acquisition",
    }
    reading, metadata = record_context_place_reading(
        context_binding,
        metric,
        7,
        {"view": ("sagittal", "fluid", "fat-suppressed")},
        {"series_uid": "target", "owner_series_uid": "owner"},
    )
    assert metadata["status"] == "unavailable"
    assert metadata["reason"] == "context_path_unavailable"
    assert reading.values.shape == reading.available.shape == (7,)
    assert reading.values.strides == reading.available.strides == (0,)
    assert not reading.available.any()

    unread, unread_metadata = unread_place_reading(
        {"bank": "context", "metric": "orientation", "reason": "not applicable"},
        metric,
        7,
        {"series_uid": "target"},
    )
    assert unread_metadata["status"] == "unread"
    assert unread_metadata["source"] == "unread"
    assert unread.values.strides == unread.available.strides == (0,)
    assert not unread.available.any()
    assert metadata["source"] == "record_context"


def test_context_null_and_nonfinite_keep_named_reason_and_scalar_type():
    metric = MetricSpec("light", MetricKind.DIGIT)
    for record, reason, scalar_type in (
        ({"metadata": {"value": None}}, "context_value_null", None),
        ({"metadata": {"value": float("nan")}}, "context_value_nonfinite", "float"),
    ):
        reading, metadata = record_context_place_reading(
            {
                "bank": "context",
                "metric": "light",
                "path": ["metadata", "value"],
                "scope": "record_plane",
            },
            metric,
            3,
            record,
            {"slice_index": 12},
        )
        assert metadata["status"] == "unavailable"
        assert metadata["reason"] == reason
        assert metadata["scalar_type"] == scalar_type
        assert reading.values.shape == reading.available.shape == (3,)
        assert reading.values.strides == reading.available.strides == (0,)
