"""NumPy-only execution of learned navigation over fixed, named HDC features.

The artifact carries its feature schema, specialist applicability and frozen training-only
conditioning. Specialists express study-condition opinions, not findings localized to a bone.
No encoder, memory case, anatomical identity or signed clinical call is changed here.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

FORMAT = "rsna-knee-som-navigation-v1"
N_CONDITIONS = 12


def file_sha256(path: Path) -> str:
    """Return the content pin of a saved input or artifact."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def schema_parts(
    schema: Mapping[str, Any],
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    """Validate explicit features, question order and specialist role applicability."""
    names = schema.get("feature_names")
    labels = schema.get("labels", schema.get("LABELS"))
    groups = schema.get("specialist_groups")
    if (
        not isinstance(names, list)
        or not names
        or not all(isinstance(n, str) and n for n in names)
    ):
        raise ValueError("feature_names must be nonempty named features")
    if len(set(names)) != len(names):
        raise ValueError("feature_names must be unique")
    if not isinstance(labels, list) or len(labels) != N_CONDITIONS:
        raise ValueError("schema must give the exact twelve-condition label order")
    if not all(isinstance(n, str) and n for n in labels) or len(set(labels)) != len(
        labels
    ):
        raise ValueError("condition labels must be unique nonempty names")
    if not isinstance(groups, list) or not groups:
        raise ValueError("explicit specialist_groups are required")
    seen: set[str] = set()
    covered: set[int] = set()
    clean = []
    for group in groups:
        if not isinstance(group, dict) or not isinstance(group.get("name"), str):
            raise ValueError("each specialist needs a name")  # noqa: TRY004 -- Serialized artifact refusals retain ValueError.
        name = group["name"]
        if not name or name in seen:
            raise ValueError("specialist names must be unique and nonempty")
        seen.add(name)
        row = {"name": name}
        for key, limit in (
            ("feature_indices", len(names)),
            ("condition_indices", N_CONDITIONS),
        ):
            indices = group.get(key)
            if not isinstance(indices, list) or not indices:
                raise ValueError(f"{name}: explicit nonempty {key} required")
            if any(type(i) is not int or not 0 <= i < limit for i in indices):
                raise ValueError(f"{name}: invalid {key}")
            if len(set(indices)) != len(indices):
                raise ValueError(f"{name}: duplicate {key}")
            row[key] = list(indices)
        covered.update(row["condition_indices"])
        clean.append(row)
    if covered != set(range(N_CONDITIONS)):
        raise ValueError(
            "every condition must have an explicitly applicable specialist"
        )
    return list(names), list(labels), clean


def architecture_for(
    schema: Mapping[str, Any], hidden: int = 32, context: int = 8, gate: int = 16
) -> dict[str, Any]:
    """Name the small dual paths and per-question softmax gate."""
    names, labels, groups = schema_parts(schema)
    if any(type(v) is not int or v < 1 for v in (hidden, context, gate)):
        raise ValueError("network widths must be positive integers")
    if context >= hidden:
        raise ValueError("the full-context path must be smaller than the domain path")
    return {
        "feature_count": len(names),
        "labels": labels,
        "groups": groups,
        "hidden": hidden,
        "context": context,
        "gate": gate,
        "activation": "gelu_tanh",
        "combination": "per_condition_softmax_weighted_logits",
    }


def weight_shapes(architecture: Mapping[str, Any]) -> dict[str, tuple[int, ...]]:
    """Return every required parameter shape, preventing silent partial artifact loads."""
    d, h, c, g = (
        int(architecture[k]) for k in ("feature_count", "hidden", "context", "gate")
    )
    groups = architecture["groups"]
    shapes: dict[str, tuple[int, ...]] = {}
    for i, group in enumerate(groups):
        prefix = f"specialists.{i}."
        for name, shape in {
            "domain1.weight": (h, len(group["feature_indices"])),
            "domain1.bias": (h,),
            "domain2.weight": (h, h),
            "domain2.bias": (h,),
            "context.weight": (c, d),
            "context.bias": (c,),
            "opinion.weight": (N_CONDITIONS, h + c),
            "opinion.bias": (N_CONDITIONS,),
        }.items():
            shapes[prefix + name] = shape
    shapes.update(
        {
            "gate_context.weight": (g, d),
            "gate_context.bias": (g,),
            "gate_head.weight": (
                len(groups) * N_CONDITIONS,
                g + len(groups) * N_CONDITIONS,
            ),
            "gate_head.bias": (len(groups) * N_CONDITIONS,),
        }
    )
    return shapes


@dataclass(frozen=True)
class NavigationModel:
    """Validated fixed-schema navigation artifact; all arrays are read-only."""

    schema: Mapping[str, Any]
    architecture: Mapping[str, Any]
    weights: Mapping[str, np.ndarray]
    mean: np.ndarray
    scale: np.ndarray
    manifest: Mapping[str, Any]


def load_navigation(path: str | Path) -> NavigationModel:
    """Load an exact artifact, refusing missing, modified or malformed components."""
    folder = Path(path)
    if folder.is_file():
        folder = folder.parent
    manifest = json.loads((folder / "navigation.json").read_text())
    if manifest.get("format") != FORMAT:
        raise ValueError("unsupported navigation artifact format")
    for filename, key in (
        ("schema.json", "schema_sha256"),
        ("weights.npz", "weights_sha256"),
    ):
        if file_sha256(folder / filename) != manifest.get(key):
            raise ValueError(f"navigation {filename} content pin mismatch")
    schema = json.loads((folder / "schema.json").read_text())
    actual = manifest["architecture"]
    expected = architecture_for(
        schema, actual["hidden"], actual["context"], actual["gate"]
    )
    if actual != expected:
        raise ValueError("navigation architecture disagrees with its feature schema")
    shapes = weight_shapes(actual)
    with np.load(folder / "weights.npz", allow_pickle=False) as saved:
        if set(saved.files) != {*shapes, "input_mean", "input_scale"}:
            raise ValueError("navigation weights have missing or extra arrays")
        weights = {name: np.asarray(saved[name]).copy() for name in shapes}
        mean, scale = (
            np.asarray(saved[name]).copy() for name in ("input_mean", "input_scale")
        )
    for name, array in weights.items():
        if (
            array.shape != shapes[name]
            or array.dtype != np.float32
            or not np.isfinite(array).all()
        ):
            raise ValueError(f"invalid navigation parameter {name}")
        array.setflags(write=False)
    d = actual["feature_count"]
    for name, array in (("mean", mean), ("scale", scale)):
        if (
            array.shape != (d,)
            or array.dtype != np.float32
            or not np.isfinite(array).all()
        ):
            raise ValueError(f"invalid input {name}")
        array.setflags(write=False)
    if np.any(scale <= 0):
        raise ValueError("input scales must be positive")
    count = sum(a.size for a in weights.values())
    if count != manifest.get("parameter_count"):
        raise ValueError("navigation parameter count mismatch")
    return NavigationModel(schema, actual, weights, mean, scale, manifest)


def _gelu(value: np.ndarray) -> np.ndarray:
    return (
        np.float32(0.5)
        * value
        * (
            np.float32(1)
            + np.tanh(
                np.float32(np.sqrt(2 / np.pi))
                * (value + np.float32(0.044715) * value * value * value)
            )
        )
    )


def predict_navigation_details(
    model: NavigationModel, X: np.ndarray
) -> dict[str, np.ndarray]:
    """Return probabilities and [N,question,specialist] learned routing weights."""
    values = np.asarray(X, dtype=np.float32)
    d = model.architecture["feature_count"]
    if values.ndim != 2 or values.shape[1] != d or not np.isfinite(values).all():
        raise ValueError(f"navigation inputs must be finite [N,{d}] features")
    if not len(values):
        return {
            "probabilities": np.empty((0, N_CONDITIONS), dtype=np.float32),
            "trust_weights": np.empty(
                (0, N_CONDITIONS, len(model.architecture["groups"])), dtype=np.float32
            ),
        }
    values = (values - model.mean) / model.scale
    if not np.isfinite(values).all():
        raise ValueError("input conditioning produced nonfinite values")
    w = model.weights

    def linear(x: np.ndarray, name: str) -> np.ndarray:
        return x @ w[name + ".weight"].T + w[name + ".bias"]

    opinions = []
    groups = model.architecture["groups"]
    applicability = np.zeros((len(groups), N_CONDITIONS), dtype=bool)
    with np.errstate(over="raise", invalid="raise"):
        for i, group in enumerate(groups):
            prefix = f"specialists.{i}."
            own = _gelu(linear(values[:, group["feature_indices"]], prefix + "domain1"))
            own = _gelu(linear(own, prefix + "domain2"))
            context = _gelu(linear(values, prefix + "context"))
            opinions.append(
                linear(np.concatenate((own, context), axis=1), prefix + "opinion")
            )
            applicability[i, group["condition_indices"]] = True
        stacked = np.stack(opinions, axis=1)
        context = _gelu(linear(values, "gate_context"))
        gate_opinions = np.where(applicability[None], stacked, np.float32(0))
        gate_input = np.concatenate(
            (context, gate_opinions.reshape(len(values), -1)), axis=1
        )
        trust = linear(gate_input, "gate_head").reshape(
            len(values), len(groups), N_CONDITIONS
        )
        trust = np.where(applicability[None], trust, np.float32(-1e9))
        trust = np.exp(trust - trust.max(axis=1, keepdims=True))
        trust /= trust.sum(axis=1, keepdims=True)
        logits = np.sum(stacked * trust, axis=1)
        result = np.float32(1) / (np.float32(1) + np.exp(-np.clip(logits, -80, 80)))
    if not np.isfinite(result).all():
        raise ValueError("navigation produced nonfinite output")
    return {
        "probabilities": result.astype(np.float32, copy=False),
        "trust_weights": trust.transpose(0, 2, 1).astype(np.float32, copy=False),
    }


def predict_navigation(model: NavigationModel, X: np.ndarray) -> np.ndarray:
    """Return twelve study-condition probabilities from the fixed numerical feature order."""
    return predict_navigation_details(model, X)["probabilities"]
