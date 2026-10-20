from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from knee.array_archive import open_arrays, write_npz_xz
from knee.collapse.posterior import FOLLOWED, START_NAMES
from knee.encoding.operation import encode_study
from knee.json_store import load_json
from knee.receipt import digest

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


def _mixed_source_case(tmp_path: Path):
    run_dir = tmp_path / "interiors"
    main_run = tmp_path / "main"
    study_uid = "study-1"

    native_artifact = f"{study_uid}/native.npz.xz"
    native_arrays = {
        "a1_objects": np.asarray([[1, 0], [0, 1]], dtype=np.uint8),
    }
    native_path = run_dir / native_artifact
    native_path.parent.mkdir(parents=True, exist_ok=True)
    write_npz_xz(native_path, native_arrays.items())
    native_record = {
        "study_uid": study_uid,
        "series_uid": "native-series",
        "view": ["coronal", "fluid", "fat-suppressed"],
        "slice_index": 0,
        "artifact": native_artifact,
        "arrays": {
            name: {"digest": digest(array)} for name, array in native_arrays.items()
        },
        "observations": [
            {
                "object": "femur",
                "provenance": "native",
                "kind": "resolved",
                "series_uid": "native-series",
                "view": ["coronal", "fluid", "fat-suppressed"],
                "slices": [0],
                "code": "identified",
                "count": 2,
                "support": "a1_objects",
                "row": None,
                "label": 1,
                "artifact": native_artifact,
            }
        ],
    }

    owner_artifact = f"{study_uid}/trace-owner.npz.xz"
    prefix = "a3_posterior_trace_femur"
    trace_arrays = {
        f"{prefix}_points_lps": np.asarray(
            [[1.0, 2.0, 3.0], [1.5, 2.5, 3.5]], dtype=np.float64
        ),
        f"{prefix}_offsets": np.asarray([0, 2], dtype=np.int64),
        f"{prefix}_slices": np.asarray([2], dtype=np.int32),
        f"{prefix}_starts": np.asarray([0], dtype=np.int32),
        f"{prefix}_stops": np.asarray([[0, 1]], dtype=np.int32),
        f"{prefix}_light": np.asarray([5.0, 8.0], dtype=np.float32),
    }
    owner_path = run_dir / owner_artifact
    write_npz_xz(owner_path, trace_arrays.items())
    owner_record = {
        "study_uid": study_uid,
        "series_uid": "trace-owner",
        "view": ["sagittal", "owner", "owner"],
        "slice_index": 0,
        "artifact": owner_artifact,
        "arrays": {
            name: {"digest": digest(array)} for name, array in trace_arrays.items()
        },
    }
    trace_view = ["axial", "fluid", "fat-suppressed"]
    trace_record = {
        "study_uid": study_uid,
        "series_uid": "trace-target",
        "view": trace_view,
        "slice_index": 2,
        "artifact": f"{study_uid}/trace-target.npz.xz",
        "observations": [
            {
                "object": "femur",
                "provenance": "native",
                "kind": "reading",
                "series_uid": "trace-target",
                "view": trace_view,
                "slices": [2],
                "code": (
                    "tube_followed" if START_NAMES[0] == FOLLOWED else START_NAMES[0]
                ),
                "count": 2,
                "support": f"{prefix}_points_lps",
                "row": 0,
                "label": None,
                "artifact": owner_artifact,
            }
        ],
    }
    result = {
        "study_uid": study_uid,
        "records": [native_record, trace_record, owner_record],
        "main_records": [],
        "objects": {"femur": {}},
    }
    spec = {
        "version": "mixed-source-v1",
        "banks": [
            {
                "name": "context",
                "facet": "declared word context",
                "metrics": [{"name": "view_part", "kind": "words", "words": ["fluid"]}],
            },
            {
                "name": "signal",
                "facet": "numeric trace measurement",
                "metrics": [{"name": "light", "kind": "digit"}],
            },
        ],
        "profiles": [
            {
                "object": "femur",
                "provenance": "native",
                "kind": "resolved",
                "support": "a1_objects",
                "view": ["coronal", "fluid", "fat-suppressed"],
                "readings": [
                    {
                        "bank": "context",
                        "metric": "view_part",
                        "source": "record_context",
                        "path": ["view", 1],
                        "scope": "acquisition",
                    },
                    {
                        "bank": "signal",
                        "metric": "light",
                        "source": "unread",
                        "reason": "no numeric light measure is declared for this profile",
                    },
                ],
                "references": [
                    {
                        "bank": "signal",
                        "metric": "light",
                        "reference_id": "explicit-test-reference",
                        "source": "test fixture only",
                        "units": "fixture units",
                        "low": 4,
                        "high": 6,
                    }
                ],
            },
            {
                "object": "femur",
                "provenance": "native",
                "kind": "reading",
                "support": f"{prefix}_points_lps",
                "view": trace_view,
                "support_layout": TRACE_LAYOUT,
                "readings": [
                    {
                        "bank": "context",
                        "metric": "view_part",
                        "source": "unread",
                        "reason": "no per-point context word is retained on this trace",
                    },
                    {"bank": "signal", "metric": "light", "value": "light"},
                ],
                "references": [
                    {
                        "bank": "signal",
                        "metric": "light",
                        "reference_id": "explicit-test-reference",
                        "source": "test fixture only",
                        "units": "fixture units",
                        "low": 4,
                        "high": 6,
                    }
                ],
            },
        ],
    }
    return run_dir, main_run, result, spec, native_artifact, owner_artifact


def test_one_layout_encodes_native_and_trace_profiles_with_explicit_unread_facets(
    tmp_path,
):
    run_dir, main_run, result, spec, native_artifact, owner_artifact = (
        _mixed_source_case(tmp_path)
    )
    output = tmp_path / "mixed.json"
    links = encode_study(result, run_dir, main_run, spec, output)
    manifest = load_json(links["manifest"])
    native, trace = [profile["outcomes"][0] for profile in manifest["profiles"]]

    assert native["status"] == "ok"
    assert trace["status"] == "ok"
    assert native["place_count"] == 2
    assert trace["place_count"] == 2
    assert manifest["work"]["addressed_places"] == 4
    assert links["work"]["metric_row_arrays"] == 4
    assert set(native["metadata"]["source_refs"]) == {"a1_objects"}
    assert set(trace["metadata"]["source_refs"]) == {
        "a3_posterior_trace_femur_points_lps",
        "a3_posterior_trace_femur_offsets",
        "a3_posterior_trace_femur_slices",
        "a3_posterior_trace_femur_starts",
        "a3_posterior_trace_femur_stops",
        "a3_posterior_trace_femur_light",
    }

    native_unread = native["metadata"]["unread_sources"][0]
    assert native_unread["reason"] == spec["profiles"][0]["readings"][1]["reason"]
    assert native_unread["source_address"]["artifact"] == native_artifact
    trace_unread = trace["metadata"]["unread_sources"][0]
    assert trace_unread["reason"] == spec["profiles"][1]["readings"][0]["reason"]
    assert trace_unread["source_address"] == {
        "owner_artifact": owner_artifact,
        "owner_series_uid": "trace-owner",
        "target_series_uid": "trace-target",
        "target_view": ["axial", "fluid", "fat-suppressed"],
        "support": "a3_posterior_trace_femur_points_lps",
        "row": 0,
        "slice_index": 2,
    }

    with open_arrays(links["archive"]) as archive:
        native_codes = {
            (item["bank"], item["metric"]): archive[item["row_codes"]]
            for item in native["metrics"]
        }
        trace_codes = {
            (item["bank"], item["metric"]): archive[item["row_codes"]]
            for item in trace["metrics"]
        }
        trace_points = archive[trace["points_lps"]]

    assert native_codes["context", "view_part"].tolist() == [0, 0]
    assert native_codes["signal", "light"].tolist() == [-1, -1]
    assert native["metrics"][1]["status"] == "silent"
    assert trace_codes["context", "view_part"].tolist() == [-1, -1]
    assert trace_codes["signal", "light"].tolist() == [1, 2]
    assert trace_points.tolist() == [[1.0, 2.0, 3.0], [1.5, 2.5, 3.5]]
    assert manifest["work"]["opened_artifacts"] == 2
    assert native["reference_set_fingerprint"] == trace["reference_set_fingerprint"]


def test_unread_declarations_are_explicit_and_do_not_accept_array_fields(tmp_path):
    from copy import deepcopy

    from knee.encoding.operation import validate_spec

    run_dir, main_run, result, spec, _native_artifact, _owner_artifact = (
        _mixed_source_case(tmp_path)
    )
    del run_dir, main_run, result
    for field, value in (
        ("reason", " "),
        ("value", "invented"),
        ("available", "mask"),
        ("path", ["view"]),
        ("window", "window"),
    ):
        invalid = deepcopy(spec)
        binding = invalid["profiles"][0]["readings"][1]
        if field == "reason":
            binding[field] = value
        else:
            binding[field] = value
        with pytest.raises(ValueError, match="invalid_profile_reading_binding"):
            validate_spec(invalid)


@pytest.mark.parametrize("kind", ["digit", "words"])
@pytest.mark.parametrize("count", [0, 1, 100_000])
def test_unread_placeholders_are_shared_readonly_scalar_views(kind, count):
    from knee.encoding.binding_sources import unread_place_reading
    from knee.encoding.places import MetricKind, MetricSpec

    metric = MetricSpec(
        "measurement", MetricKind(kind), ("word",) if kind == "words" else ()
    )
    reading, metadata = unread_place_reading(
        {"bank": "bank", "metric": "measurement", "reason": "not measured"},
        metric,
        count,
        {"artifact": "source"},
    )
    assert reading.values.shape == reading.available.shape == (count,)
    assert reading.values.strides == reading.available.strides == (0,)
    assert not reading.values.flags.writeable
    assert not reading.available.flags.writeable
    assert not reading.available.any()
    assert reading.values.base.nbytes <= 8
    assert reading.available.base.nbytes == 1
    assert metadata["status"] == "unread"
