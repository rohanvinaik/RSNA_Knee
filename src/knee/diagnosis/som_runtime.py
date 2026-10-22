"""Optional learned navigation over fixed HDC readings, retaining symbolic evidence.

Navigation values and priorities are study-condition model opinions. They never
rewrite an anatomical identity, a lens measurement, or a signed symbolic finding.
"""

from __future__ import annotations

import copy
import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from knee.diagnosis import som_features
from knee.diagnosis.som_features import SCHEMA as FEATURE_SCHEMA
from knee.diagnosis.som_features import features_for_record
from knee.diagnosis.som_navigation import (
    NavigationModel,
    load_navigation,
    predict_navigation,
    predict_navigation_details,
)
from knee.diagnosis.squint_contracts import (
    READOUT_POLICY_ID,
    serialize_condition_value,
)
from knee.study.tables import LABELS

SCHEMA = "knee.som-navigation-runtime/v1"
SCOPE = "study_condition_model_opinion_not_localized_tissue"
ARTIFACT_FILES = ("navigation.json", "schema.json", "weights.npz")


class NavigationRuntimeError(ValueError):
    """A named runtime contract refusal."""


@dataclass(frozen=True)
class NavigationRuntime:
    """One content-pinned model shared by the study workers."""

    model: NavigationModel
    path: Path
    artifact_pins: Mapping[str, str]
    feature_writer_sha256: str


def _pins(folder: Path) -> dict[str, str]:
    return {
        name: hashlib.sha256((folder / name).read_bytes()).hexdigest()
        for name in ARTIFACT_FILES
    }


def load_navigation_runtime(path: Path | str) -> NavigationRuntime:
    """Load once, verify schema/label order and pin every numerical artifact."""
    folder = Path(path)
    if folder.is_file():
        folder = folder.parent
    folder = folder.resolve()
    pins = _pins(folder)
    model = load_navigation(folder)
    if _pins(folder) != pins:
        raise NavigationRuntimeError("navigation_artifact_changed_during_load")
    if model.schema.get("schema") != FEATURE_SCHEMA:
        raise NavigationRuntimeError("navigation_feature_schema_invalid")
    if model.architecture.get("labels") != list(LABELS):
        raise NavigationRuntimeError("navigation_label_order_mismatch")
    if model.schema.get("labels") != list(LABELS):
        raise NavigationRuntimeError("navigation_schema_label_order_mismatch")
    writer_sha256 = hashlib.sha256(Path(som_features.__file__).read_bytes()).hexdigest()
    source_pins = model.schema.get("source_pins", {})
    if not isinstance(source_pins, Mapping):
        raise NavigationRuntimeError("navigation_source_pins_invalid")
    expected_writer = source_pins.get("feature_writer_sha256")
    if expected_writer is not None and expected_writer != writer_sha256:
        raise NavigationRuntimeError("navigation_feature_writer_pin_mismatch")
    if len(model.schema.get("feature_names", ())) != model.architecture.get(
        "feature_count"
    ):
        raise NavigationRuntimeError("navigation_feature_count_mismatch")
    return NavigationRuntime(model, folder, pins, writer_sha256)


def navigation_provenance(runtime: NavigationRuntime) -> dict[str, Any]:
    """Serializable run-level identity, including declared training provenance."""
    return {
        "schema": SCHEMA,
        "scope": SCOPE,
        "readout_policy_id": READOUT_POLICY_ID,
        "artifact": str(runtime.path),
        "artifact_pins": dict(runtime.artifact_pins),
        "labels": list(LABELS),
        "specialists": [
            group["name"] for group in runtime.model.architecture["groups"]
        ],
        "feature_count": runtime.model.architecture["feature_count"],
        "feature_writer_sha256": runtime.feature_writer_sha256,
        "parameter_count": runtime.model.manifest.get("parameter_count"),
        "training_provenance": copy.deepcopy(
            runtime.model.manifest.get("provenance", {})
        ),
    }


def _features(runtime: NavigationRuntime, record: Mapping[str, Any]) -> np.ndarray:
    features = features_for_record(runtime.model.schema, record)
    if (
        not isinstance(features, np.ndarray)
        or features.dtype != np.float32
        or features.shape != (runtime.model.architecture["feature_count"],)
        or not np.isfinite(features).all()
    ):
        raise NavigationRuntimeError("navigation_features_invalid")
    return features


def _probabilities(value: object) -> np.ndarray:
    array = np.asarray(value)
    if (
        array.shape != (1, len(LABELS))
        or not np.issubdtype(array.dtype, np.number)
        or not np.isfinite(array).all()
        or np.any(array < 0)
        or np.any(array > 1)
    ):
        raise NavigationRuntimeError("navigation_prediction_invalid")
    return array


def apply_navigation_record(
    runtime: NavigationRuntime | None, record: dict[str, Any]
) -> dict[str, Any]:
    """Produce numerical values without mutating the original symbolic record."""
    if runtime is None:
        return record
    original_values = copy.deepcopy(record.get("values"))
    provenance = {
        "schema": SCHEMA,
        "scope": SCOPE,
        "readout_policy_id": READOUT_POLICY_ID,
        "artifact_pins": dict(runtime.artifact_pins),
        "original_values": original_values,
        "symbolic_questions": "retained_unchanged",
    }
    if record.get("study_status") == "not_examined_budget":
        return {
            **record,
            "navigation": {**provenance, "outcome": "skipped_unexamined_budget"},
        }
    features = _features(runtime, record)
    try:
        predicted = predict_navigation(runtime.model, features[None, :])
    except (FloatingPointError, OverflowError) as error:
        return {
            **record,
            "navigation": {
                **provenance,
                "outcome": "navigation_numerical_failure",
                "error_type": type(error).__name__,
                "original_symbolic_values_retained": True,
            },
        }
    values = _probabilities(predicted)
    predictions = {label: float(values[0, index]) for index, label in enumerate(LABELS)}
    questions = record.get("questions")
    if not isinstance(questions, Mapping):
        raise NavigationRuntimeError("navigation_symbolic_questions_invalid")
    readout = {}
    readout_sources = {}
    for label in LABELS:
        question = questions.get(label)
        if not isinstance(question, Mapping) or not isinstance(
            question.get("finding"), Mapping
        ):
            raise NavigationRuntimeError("navigation_symbolic_finding_invalid:" + label)
        finding = question["finding"]
        readout[label] = serialize_condition_value(finding, predictions[label])
        readout_sources[label] = (
            "graded_navigation_for_open"
            if finding["outcome"] == "open"
            else "warranted_symbolic_" + finding["outcome"]
        )
    return {
        **record,
        "readout_policy_id": READOUT_POLICY_ID,
        "values": readout,
        "navigation": {
            **provenance,
            "outcome": "applied",
            "feature_count": len(features),
            "feature_sha256": hashlib.sha256(features.tobytes()).hexdigest(),
            "numerical_values": predictions.copy(),
            "readout_values": readout.copy(),
            "readout_sources": readout_sources,
        },
    }


def order_navigation_requests(
    runtime: NavigationRuntime,
    record: Mapping[str, Any],
    question: str,
    requests: Sequence[Mapping[str, Any]],
) -> tuple[list[Mapping[str, Any]], dict[str, Any]]:
    """Gate-sort each existing priority group, keeping every mandatory look first.

    Missing future measurements stay unavailable in the ordinary feature adapter.
    No request is added, suppressed or made optional by this operation.
    """
    if question not in LABELS:
        raise NavigationRuntimeError("navigation_request_question_invalid")
    features = _features(runtime, record)
    try:
        details = predict_navigation_details(runtime.model, features[None, :])
    except (FloatingPointError, OverflowError) as error:
        unchanged = [
            {
                "original_index": index,
                "request_id": request.get("request_id"),
                "kind": request.get("kind", "bounded_zoom"),
                "subject": request.get("object", request.get("subject")),
                "question": question,
                "mandatory": request.get("discretionary", True) is False,
            }
            for index, request in enumerate(requests)
        ]
        return list(requests), {
            "schema": SCHEMA,
            "outcome": "navigation_numerical_failure",
            "scope": "existing_observation_request_order_only",
            "question": question,
            "artifact_pins": dict(runtime.artifact_pins),
            "error_type": type(error).__name__,
            "before": unchanged,
            "after": copy.deepcopy(unchanged),
            "requests_retained": len(requests),
            "new_skipping_policy": False,
        }
    _probabilities(details.get("probabilities"))
    groups = runtime.model.architecture["groups"]
    weights = np.asarray(details.get("trust_weights"))
    if (
        weights.shape != (1, len(LABELS), len(groups))
        or not np.issubdtype(weights.dtype, np.number)
        or not np.isfinite(weights).all()
        or np.any(weights < 0)
        or np.any(weights > 1)
    ):
        raise NavigationRuntimeError("navigation_request_weights_invalid")
    subject_indices = {group["name"]: index for index, group in enumerate(groups)}
    condition_index = list(LABELS).index(question)
    scored = []
    before = []
    for index, request in enumerate(requests):
        if not isinstance(request, Mapping):
            raise NavigationRuntimeError("navigation_request_invalid")
        subject = request.get("object", request.get("subject"))
        group_index = subject_indices.get(subject) if isinstance(subject, str) else None
        priority = (
            float(weights[0, condition_index, group_index])
            if group_index is not None
            else 0.0
        )
        mandatory = request.get("discretionary", True) is False
        signature = {
            "original_index": index,
            "request_id": request.get("request_id"),
            "kind": request.get("kind", "bounded_zoom"),
            "subject": subject,
            "question": question,
            "mandatory": mandatory,
            "gate_weight": priority,
            "specialist": subject if group_index is not None else None,
            "applicability": "matched_specialist"
            if group_index is not None
            else "no_named_specialist",
        }
        before.append(signature)
        scored.append((not mandatory, -priority, index, request, signature))
    scored.sort(key=lambda row: row[:3])
    return [row[3] for row in scored], {
        "schema": SCHEMA,
        "outcome": "ordered",
        "scope": "existing_observation_request_order_only",
        "question": question,
        "artifact_pins": dict(runtime.artifact_pins),
        "feature_sha256": hashlib.sha256(features.tobytes()).hexdigest(),
        "before": before,
        "after": [row[4] for row in scored],
        "requests_retained": len(scored),
        "new_skipping_policy": False,
    }
