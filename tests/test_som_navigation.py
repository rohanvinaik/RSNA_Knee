"""Two-sign intent for pure offline navigation and its fixed-schema artifact."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from knee.diagnosis.som_navigation import (
    FORMAT,
    architecture_for,
    file_sha256,
    load_navigation,
    predict_navigation,
    predict_navigation_details,
    schema_parts,
    weight_shapes,
)


def schema() -> dict:
    return {
        "feature_names": [f"hdc_{i}" for i in range(5)],
        "labels": [f"condition_{i}" for i in range(12)],
        "specialist_groups": [
            {
                "name": "bone",
                "feature_indices": [0, 1],
                "condition_indices": list(range(12)),
            },
            {
                "name": "fluid",
                "feature_indices": [2, 3],
                "condition_indices": list(range(12)),
            },
        ],
    }


def artifact(folder: Path, source_schema: dict | None = None) -> Path:
    source_schema = source_schema or schema()
    architecture = architecture_for(source_schema, 4, 2, 3)
    weights = {
        k: np.zeros(shape, dtype=np.float32)
        for k, shape in weight_shapes(architecture).items()
    }
    weights["specialists.0.opinion.bias"][:] = 2
    weights["specialists.1.opinion.bias"][:] = -2
    folder.mkdir()
    (folder / "schema.json").write_text(json.dumps(source_schema))
    np.savez_compressed(
        folder / "weights.npz",
        allow_pickle=False,
        **weights,
        input_mean=np.zeros(5, np.float32),
        input_scale=np.ones(5, np.float32),
    )
    manifest = {
        "format": FORMAT,
        "architecture": architecture,
        "schema_sha256": file_sha256(folder / "schema.json"),
        "weights_sha256": file_sha256(folder / "weights.npz"),
        "parameter_count": sum(v.size for v in weights.values()),
    }
    (folder / "navigation.json").write_text(json.dumps(manifest))
    return folder


def test_balanced_opinions_return_half_and_equal_gate(tmp_path):
    model = load_navigation(artifact(tmp_path / "model"))
    actual = predict_navigation(model, np.zeros((3, 5), dtype=np.float32))
    details = predict_navigation_details(model, np.zeros((3, 5), dtype=np.float32))
    np.testing.assert_array_equal(actual, np.full((3, 12), 0.5, np.float32))
    np.testing.assert_array_equal(
        details["trust_weights"], np.full((3, 12, 2), 0.5, np.float32)
    )


def test_inapplicable_specialist_never_routes_a_question(tmp_path):
    source_schema = schema()
    source_schema["specialist_groups"][1]["condition_indices"] = [1]
    model = load_navigation(artifact(tmp_path / "model", source_schema))
    details = predict_navigation_details(model, np.zeros((1, 5), dtype=np.float32))
    assert details["trust_weights"][0, 0, 1] == 0
    assert details["trust_weights"][0, 0, 0] == 1
    assert details["probabilities"][0, 0] > 0.8
    assert details["probabilities"][0, 1] == 0.5
    np.testing.assert_allclose(details["trust_weights"].sum(axis=2), 1)


def test_empty_batch_has_named_shapes(tmp_path):
    model = load_navigation(artifact(tmp_path / "model"))
    assert predict_navigation(model, np.empty((0, 5), np.float32)).shape == (0, 12)
    assert predict_navigation_details(model, np.empty((0, 5), np.float32))[
        "trust_weights"
    ].shape == (0, 12, 2)


@pytest.mark.parametrize(
    "values", [np.zeros((1, 4)), np.zeros(5), np.full((1, 5), np.nan)]
)
def test_wrong_shape_or_nonfinite_features_are_not_scored(tmp_path, values):
    model = load_navigation(artifact(tmp_path / "model"))
    with pytest.raises(ValueError, match="finite"):
        predict_navigation(model, values)


def test_modified_schema_cannot_silently_change_feature_meaning(tmp_path):
    folder = artifact(tmp_path / "model")
    (folder / "schema.json").write_text("{}")
    with pytest.raises(ValueError, match="pin mismatch"):
        load_navigation(folder)


def test_missing_applicability_is_not_invented():
    source_schema = schema()
    del source_schema["specialist_groups"][0]["condition_indices"]
    with pytest.raises(ValueError, match="condition_indices"):
        schema_parts(source_schema)


def test_runtime_module_never_imports_torch():
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}
    code = 'import sys; import knee.diagnosis.som_navigation; assert "torch" not in sys.modules'
    result = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
