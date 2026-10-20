from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from knee.array_archive import write_npz_xz
from knee.encoding import h5_store, operation
from knee.encoding.product import open_product
from knee.receipt import digest


def _fixture(tmp_path: Path):
    run_dir = tmp_path / "run"
    main_run = tmp_path / "main"
    artifact = "study-1/series.npz.xz"
    arrays = {
        "support": np.array([[1, 1], [0, 0]], dtype=np.uint8),
        "intensity": np.array([[10, 20], [30, 40]], dtype=np.int16),
        "available": np.array([[True, False], [True, True]], dtype=np.bool_),
    }
    path = run_dir / artifact
    path.parent.mkdir(parents=True)
    write_npz_xz(path, arrays.items())
    record = {
        "study_uid": "study-1",
        "series_uid": "series-1",
        "view": ["Coronal", "fluid", "fat-suppressed"],
        "slice_index": 4,
        "artifact": artifact,
        "arrays": {name: {"digest": digest(value)} for name, value in arrays.items()},
        "observations": [
            {
                "object": "femur",
                "provenance": "native",
                "kind": "resolved",
                "series_uid": "series-1",
                "view": ["Coronal", "fluid", "fat-suppressed"],
                "slices": [4],
                "code": "identified",
                "count": 2,
                "support": "support",
                "artifact": artifact,
                "row": None,
                "label": 1,
            }
        ],
    }
    result = {
        "study_uid": "study-1",
        "records": [record],
        "main_records": [],
        "objects": {"femur": {"anatomical_relations": {"tibia": "adjacent"}}},
    }
    profile = {
        "object": "femur",
        "provenance": "native",
        "kind": "resolved",
        "support": "support",
        "view": ["Coronal", "fluid", "fat-suppressed"],
        "readings": [
            {
                "bank": "signal",
                "metric": "light",
                "value": "intensity",
                "available": "available",
            }
        ],
        "references": [],
    }
    spec = {
        "version": "retained-metric-test-v1",
        "storage": "h5",
        "retain_object_sources": True,
        "banks": [
            {
                "name": "signal",
                "facet": "measured intensity",
                "metrics": [{"name": "light", "kind": "digit"}],
            }
        ],
        "profiles": [profile, dict(profile)],
    }
    return run_dir, main_run, result, record, arrays, spec


def test_missing_reference_retains_measured_values_and_unavailability_once(
    tmp_path, monkeypatch
):
    run_dir, main_run, result, _record, source_arrays, spec = _fixture(tmp_path)
    opened = []
    reads = {}
    encoder_calls = []
    original_open = operation.open_arrays
    original_encode = operation.encode_observation

    class CountingArchive:
        def __init__(self, archive):
            self.archive = archive

        @property
        def files(self):
            return self.archive.files

        def __contains__(self, name):
            return name in self.archive.files

        def __getitem__(self, name):
            reads[name] = reads.get(name, 0) + 1
            return self.archive[name]

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self.archive.close()

    def counted_open(path):
        opened.append(Path(path))
        return CountingArchive(original_open(path))

    def counted_encode(*args, **kwargs):
        encoder_calls.append(1)
        return original_encode(*args, **kwargs)

    monkeypatch.setattr(operation, "open_arrays", counted_open)
    monkeypatch.setattr(operation, "encode_observation", counted_encode)
    product_path = tmp_path / "encoded.json.xz"
    outcome = operation.encode_study(result, run_dir, main_run, spec, product_path)

    assert len(opened) == 1
    assert reads == {"support": 1, "intensity": 1, "available": 1}
    assert len(encoder_calls) == 2
    assert outcome["object_sources"]["status"] == "complete"

    with open_product(Path(outcome["manifest"])) as product:
        manifest = product.manifest
        assert manifest["retained_metric_inputs"] == {
            "schema": "knee-retained-metric-inputs/v1",
            "status": "complete",
            "array_count": 2,
            "deduplication": "encoding_and_dtype_shape_digest",
        }
        metrics = [p["outcomes"][0]["metrics"][0] for p in manifest["profiles"]]
        assert [m["status"] for m in metrics] == [
            "missing_reference",
            "missing_reference",
        ]
        assert all(m["binding"]["value"] == "intensity" for m in metrics)
        assert all(m["binding"]["available"] == "available" for m in metrics)
        value_refs = [m["retained_source_values"] for m in metrics]
        available_refs = [m["retained_source_available"] for m in metrics]
        assert value_refs[0] == value_refs[1]
        assert available_refs[0] == available_refs[1]
        retained_values = product.arrays[value_refs[0]["array"]]
        retained_available = product.arrays[available_refs[0]["array"]]
        assert retained_values.dtype == source_arrays["intensity"].dtype
        assert retained_values.tolist() == [10, 20]
        assert retained_available.dtype == np.dtype(np.bool_)
        assert retained_available.tolist() == [True, False]
        assert retained_values[1] != 0 and retained_available[1] is np.False_
        assert value_refs[0]["digest"] == digest(retained_values)
        assert available_refs[0]["digest"] == digest(retained_available)
        assert manifest["encoded_arrays"][value_refs[0]["array"]]["digest"] == digest(
            retained_values
        )
        assert manifest["encoded_arrays"][available_refs[0]["array"]][
            "digest"
        ] == digest(retained_available)
        for profile in manifest["profiles"]:
            assert product.arrays[
                profile["outcomes"][0]["metrics"][0]["row_codes"]
            ].tolist() == [-1, -1]


def test_unicode_metric_values_have_lossless_public_array_representation(tmp_path):
    values = np.asarray([["clear", "opaque"], ["partial", "clear"]], dtype="U7")
    arrays = {}
    index = {}
    descriptor = operation._retain_metric_array(values, "word_values", arrays, index)
    assert descriptor["encoding"] == "utf8_json"
    stored = arrays[descriptor["array"]]
    assert stored.dtype == np.dtype(np.uint8)
    decoded = np.asarray(
        json.loads(stored.tobytes().decode("utf-8")), dtype=values.dtype
    )
    assert decoded.shape == values.shape
    assert decoded.tolist() == values.tolist()
    assert descriptor["dtype"] == values.dtype.str
    assert descriptor["shape"] == list(values.shape)
    assert descriptor["digest"] == digest(stored)
    pytest.importorskip("h5py")
    path = tmp_path / "retained-words.h5"
    h5_store.write_h5(
        path,
        {
            "study_uid": "word-fixture",
            "encoded_arrays": {
                name: {
                    "digest": digest(array),
                    "shape": list(array.shape),
                    "dtype": array.dtype.str,
                }
                for name, array in arrays.items()
            },
        },
        arrays,
    )
    with open_product(path) as product:
        public = product.arrays[descriptor["array"]]
        assert public.tobytes() == stored.tobytes()
        decoded_public = np.asarray(
            json.loads(public.tobytes().decode("utf-8")), dtype=values.dtype
        )
        assert decoded_public.tolist() == values.tolist()
