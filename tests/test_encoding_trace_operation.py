from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from knee.array_archive import open_arrays
from knee.encoding.operation import encode_study

BASE = Path(
    "data/readings/"
    "collapse-20261017/full-build/targeted-compute-20261018/"
    "b9b10-integrated-20261019/cohort/labeled-workers4-no-draw/interiors"
)

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


def _retained_case():
    if not (BASE / "receipt.json").is_file():
        pytest.skip("saved proof trace receipt is not available")
    receipt = json.loads((BASE / "receipt.json").read_text())
    records = receipt["records"]
    owners = {record.get("artifact"): record for record in records}
    for target in records:
        for observation in target.get("observations", []):
            if (
                observation.get("support")
                == "a3_posterior_trace_popliteal_artery_points_lps"
                and observation.get("count") == 161
            ):
                owner = owners.get(observation.get("artifact"))
                if owner is not None:
                    return target, owner, observation
    raise AssertionError("retained_popliteal_artery_trace_not_found")


def _spec(observation):
    return {
        "version": "trace-operation-test-v1",
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
                "object": observation["object"],
                "provenance": "native",
                "kind": "reading",
                "support": observation["support"],
                "view": observation["view"],
                "support_layout": TRACE_LAYOUT,
                "readings": [
                    {"bank": "trace", "metric": "light", "value": "light"},
                    {"bank": "trace", "metric": "flank", "value": "flank"},
                ],
                "references": [
                    {
                        "bank": "trace",
                        "metric": "light",
                        "reference_id": "test-light-reference",
                        "source": "explicit-test-input",
                        "units": "test-units",
                        "low": 250.0,
                        "high": 350.0,
                    },
                    {
                        "bank": "trace",
                        "metric": "flank",
                        "reference_id": "test-flank-reference",
                        "source": "explicit-test-input",
                        "units": "test-units",
                        "low": 250.0,
                        "high": 350.0,
                    },
                ],
            }
        ],
    }


def test_encode_study_reads_owner_artifact_and_serializes_lps_points(tmp_path):
    target, owner, observation = _retained_case()
    result = {
        "study_uid": target["study_uid"],
        "records": [target, owner],
        "main_records": [],
        "objects": {observation["object"]: {}},
    }
    output = tmp_path / "trace-encoding.json"
    status = encode_study(result, BASE, BASE, _spec(observation), output)
    outcome = status["profiles"][0]["outcomes"][0]

    assert outcome["status"] == "ok"
    assert outcome["artifact"] == owner["artifact"]
    assert outcome["target_artifact"] == target["artifact"]
    assert outcome["metadata"]["owner_series_uid"] == owner["series_uid"]
    assert outcome["metadata"]["target_series_uid"] == target["series_uid"]
    assert outcome["address_kind"] == "patient_lps_points"
    assert outcome["place_count"] == observation["count"]
    assert status["work"]["opened_artifacts"] == 1
    assert status["work"]["addressed_places"] == observation["count"]

    with open_arrays(Path(status["archive"])) as encoded:
        points = encoded[outcome["points_lps"]]
        assert points.shape == (observation["count"], 3)
        assert points.dtype.kind == "f"
        assert not any("points_rc" in name for name in encoded.files)
        assert np.isfinite(points).all()


def test_encode_study_retains_named_refusal_when_owner_record_is_missing(tmp_path):
    target, _owner, observation = _retained_case()
    result = {
        "study_uid": target["study_uid"],
        "records": [target],
        "main_records": [],
        "objects": {observation["object"]: {}},
    }
    output = tmp_path / "trace-owner-missing.json"
    status = encode_study(result, BASE, BASE, _spec(observation), output)
    outcome = status["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "trace_owner_record_missing"
    assert outcome["artifact"] == observation["artifact"]
    assert status["work"]["opened_artifacts"] == 0
