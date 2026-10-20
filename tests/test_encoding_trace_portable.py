from __future__ import annotations

from pathlib import Path

import numpy as np

from knee.array_archive import open_arrays, write_npz_xz
from knee.collapse.posterior import FOLLOWED, START_NAMES
from knee.encoding.operation import encode_study
from knee.encoding.places import (
    BankSpec,
    EncodingCode,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    NumericReference,
    compile_layout,
)
from knee.encoding.trace_adapter import encode_trace_observation
from knee.receipt import digest

VIEW = ["sagittal", "fluid", "fat-suppressed"]
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
    empty_start = next(name for name in START_NAMES if name != FOLLOWED)
    arrays = {
        f"{TRACE_PREFIX}_points_lps": np.array(
            [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float64
        ),
        f"{TRACE_PREFIX}_light": np.array([1.0, 3.0], dtype=np.float32),
        f"{TRACE_PREFIX}_flank": np.array([2.0, 2.0], dtype=np.float32),
        f"{TRACE_PREFIX}_offsets": np.array([0, 2, 2], dtype=np.int64),
        f"{TRACE_PREFIX}_slices": np.array([9, 10], dtype=np.int32),
        f"{TRACE_PREFIX}_starts": np.array(
            [START_NAMES.index(FOLLOWED), START_NAMES.index(empty_start)], dtype=np.int8
        ),
        f"{TRACE_PREFIX}_stops": np.array([[0, 0], [0, 0]], dtype=np.int8),
    }
    write_npz_xz(run_dir / owner_artifact, arrays)
    descriptors = {name: {"digest": digest(value)} for name, value in arrays.items()}
    study_uid = "test-study"
    target_observations = [
        {
            "object": "test_object",
            "provenance": "native",
            "kind": "reading",
            "series_uid": target_uid,
            "view": VIEW,
            "slices": [int(arrays[f"{TRACE_PREFIX}_slices"][row])],
            "code": "tube_followed" if row == 0 else empty_start,
            "count": count,
            "support": TRACE_SUPPORT,
            "artifact": owner_artifact,
            "row": row,
            "label": None,
        }
        for row, count in ((0, 2), (1, 0))
    ]
    target = {
        "study_uid": study_uid,
        "series_uid": target_uid,
        "view": VIEW,
        "slice_index": 8,
        "artifact": target_artifact,
        "arrays": {},
        "observations": target_observations,
    }
    owner = {
        "study_uid": study_uid,
        "series_uid": owner_uid,
        "view": ["axial", "fluid", "fat-suppressed"],
        "slice_index": 12,
        "artifact": owner_artifact,
        "arrays": descriptors,
        "observations": [],
    }
    return run_dir, target, owner, arrays


def _layout_and_references():
    # Layout compilation validates the carrier identity; obtain the matching
    # production carrier through operation's validator instead of inventing one.
    from knee.encoding.carrier import HadamardCarrier

    carrier = HadamardCarrier.from_banks(["trace"])
    layout = compile_layout(
        LayoutSpec(
            "trace-portable-test-v1",
            carrier.identity,
            (
                BankSpec(
                    "trace",
                    "native_trace_measurements",
                    (
                        MetricSpec("light", MetricKind.DIGIT),
                        MetricSpec("flank", MetricKind.DIGIT),
                    ),
                ),
            ),
        )
    )
    assert layout is not None
    references = {
        ("trace", metric): NumericReference(
            layout.fingerprint,
            "trace",
            metric,
            f"explicit-{metric}-reference",
            "portable test input",
            "test units",
            2.0,
            2.0,
        )
        for metric in ("light", "flank")
    }
    return layout, references


def _spec():
    return {
        "version": "trace-portable-test-v1",
        "banks": [
            {
                "name": "trace",
                "facet": "native_trace_measurements",
                "metrics": [
                    {"name": "light", "kind": "digit"},
                    {"name": "flank", "kind": "digit"},
                ],
            }
        ],
        "profiles": [
            {
                "object": "test_object",
                "provenance": "native",
                "kind": "reading",
                "support": TRACE_SUPPORT,
                "view": VIEW,
                "support_layout": TRACE_LAYOUT,
                "readings": [
                    {"bank": "trace", "metric": "light", "value": "light"},
                    {"bank": "trace", "metric": "flank", "value": "flank"},
                ],
                "references": [
                    {
                        "bank": "trace",
                        "metric": metric,
                        "reference_id": f"explicit-{metric}-reference",
                        "source": "portable test input",
                        "units": "test units",
                        "low": 2.0,
                        "high": 2.0,
                    }
                    for metric in ("light", "flank")
                ],
            }
        ],
    }


def _bindings():
    return [
        {"bank": "trace", "metric": metric, "value": f"{TRACE_PREFIX}_{metric}"}
        for metric in ("light", "flank")
    ]


def test_portable_adapter_encodes_nonempty_and_empty_rows_and_counts(tmp_path):
    run_dir, target, owner, arrays = _fixture(tmp_path)
    layout, references = _layout_and_references()
    with open_arrays(run_dir / owner["artifact"]) as loaded:
        first = encode_trace_observation(
            target,
            owner,
            target["observations"][0],
            loaded,
            layout,
            _bindings(),
            references,
        )
        empty = encode_trace_observation(
            target,
            owner,
            target["observations"][1],
            loaded,
            layout,
            _bindings(),
            references,
        )
    assert first.status == EncodingCode.OK.value
    assert empty.status == EncodingCode.SILENT.value
    assert np.array_equal(first.points_lps, arrays[f"{TRACE_PREFIX}_points_lps"])
    assert empty.points_lps is not None and empty.points_lps.shape == (0, 3)
    assert first.metadata["slice_index"] == 9
    assert target["slice_index"] == 8
    bundle = first.encoding.bundle
    assert bundle is not None
    light = bundle.counts[0]
    assert light[0] == 1 and light[2] == 1
    assert light[4] == 2
    assert sum(light) == 4


def test_portable_adapter_names_boolean_address_count_digest_and_owner_faults(tmp_path):
    run_dir, target, owner, _arrays = _fixture(tmp_path)
    layout, references = _layout_and_references()
    observation = dict(target["observations"][0])
    with open_arrays(run_dir / owner["artifact"]) as loaded:
        for field, value, expected in (
            ("row", True, "invalid_trace_row"),
            ("count", True, "trace_count_mismatch"),
            ("count", 3, "trace_count_mismatch"),
        ):
            changed = dict(observation)
            changed[field] = value
            answer = encode_trace_observation(
                target, owner, changed, loaded, layout, _bindings(), references
            )
            assert answer.status == expected
        wrong_target = dict(target, series_uid="another-target")
        answer = encode_trace_observation(
            wrong_target, owner, observation, loaded, layout, _bindings(), references
        )
        assert answer.status == "target_series_mismatch"
        wrong_owner = dict(owner, study_uid="another-study")
        answer = encode_trace_observation(
            target, wrong_owner, observation, loaded, layout, _bindings(), references
        )
        assert answer.status == "source_study_mismatch"
        wrong_owner_uid = dict(owner, series_uid="other-source")
        answer = encode_trace_observation(
            target,
            wrong_owner_uid,
            observation,
            loaded,
            layout,
            _bindings(),
            references,
        )
        assert answer.status == "source_artifact_owner_mismatch"
        wrong_digest_owner = dict(owner, arrays=dict(owner["arrays"]))
        wrong_digest_owner["arrays"][f"{TRACE_PREFIX}_light"] = {"digest": "0" * 64}
        answer = encode_trace_observation(
            target,
            wrong_digest_owner,
            observation,
            loaded,
            layout,
            _bindings(),
            references,
        )
        assert answer.status == "digest_mismatch"
    wrong_owner = dict(owner, artifact="other.npz.xz")
    with open_arrays(run_dir / owner["artifact"]) as loaded:
        answer = encode_trace_observation(
            target, wrong_owner, observation, loaded, layout, _bindings(), references
        )
    assert answer.status == "source_artifact_owner_mismatch"


def test_portable_adapter_preserves_missing_reference_status(tmp_path):
    run_dir, target, owner, _arrays = _fixture(tmp_path)
    layout, _references = _layout_and_references()
    with open_arrays(run_dir / owner["artifact"]) as loaded:
        answer = encode_trace_observation(
            target, owner, target["observations"][0], loaded, layout, _bindings(), {}
        )
    assert answer.status == EncodingCode.MISSING_REFERENCE.value
    assert answer.points_lps is not None and answer.points_lps.shape == (2, 3)


def test_portable_encode_study_uses_owner_and_writes_patient_lps(tmp_path):
    run_dir, target, owner, _arrays = _fixture(tmp_path)
    result = {
        "study_uid": target["study_uid"],
        "records": [target, owner],
        "main_records": [],
        "objects": {"test_object": {}},
    }
    status = encode_study(
        result, run_dir, tmp_path / "main", _spec(), tmp_path / "encoded.json"
    )
    outcomes = status["profiles"][0]["outcomes"]
    assert [outcome["status"] for outcome in outcomes] == ["ok", "silent"]
    assert [outcome["metadata"]["slice_index"] for outcome in outcomes] == [9, 10]
    assert all(outcome["artifact"] == owner["artifact"] for outcome in outcomes)
    assert all(outcome["target_artifact"] == target["artifact"] for outcome in outcomes)
    assert status["work"]["addressed_places"] == 2
    with open_arrays(Path(status["archive"])) as encoded:
        points = encoded[outcomes[0]["points_lps"]]
        empty = encoded[outcomes[1]["points_lps"]]
    assert np.array_equal(points, np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float64))
    assert empty.shape == (0, 3)
    assert np.isfinite(points).all()


def test_portable_encode_study_keeps_named_owner_refusal(tmp_path):
    run_dir, target, _owner, _arrays = _fixture(tmp_path)
    result = {
        "study_uid": target["study_uid"],
        "records": [target],
        "main_records": [],
        "objects": {"test_object": {}},
    }
    status = encode_study(
        result, run_dir, tmp_path / "main", _spec(), tmp_path / "encoded.json"
    )
    outcomes = status["profiles"][0]["outcomes"]
    assert [outcome["status"] for outcome in outcomes] == [
        "trace_owner_record_missing",
        "trace_owner_record_missing",
    ]
    assert status["work"]["opened_artifacts"] == 0


def test_spec_keeps_trace_family_typed_and_preserves_missing_references():
    spec = _spec()
    spec["profiles"][0]["references"] = []
    from knee.encoding.operation import validate_spec

    # Missing references are a runtime named state, not invalid declaration.
    validated = validate_spec(spec)
    assert validated["profiles"][0]["support_layout"]["family"] == "posterior_trace"


def test_portable_encode_study_refuses_ambiguous_owner_record(tmp_path):
    run_dir, target, owner, _arrays = _fixture(tmp_path)
    duplicate = dict(owner, series_uid="duplicate-source-series")
    result = {
        "study_uid": target["study_uid"],
        "records": [target, owner, duplicate],
        "main_records": [],
        "objects": {"test_object": {}},
    }
    status = encode_study(
        result, run_dir, tmp_path / "main", _spec(), tmp_path / "encoded.json"
    )
    outcomes = status["profiles"][0]["outcomes"]
    assert [outcome["status"] for outcome in outcomes] == [
        "trace_owner_record_ambiguous",
        "trace_owner_record_ambiguous",
    ]
    assert status["work"]["opened_artifacts"] == 0
