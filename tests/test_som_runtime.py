"""Intent: learned navigation acts without rewriting symbolic measurements or calls."""

import copy
import hashlib
import importlib.util
import json
import math
import os
import sys
import tarfile
from argparse import Namespace
from pathlib import Path

import numpy as np
import pytest

from knee.diagnosis.som_features import fit_feature_schema
from knee.diagnosis.som_navigation import architecture_for, weight_shapes
from knee.diagnosis.som_runtime import (
    NavigationRuntimeError,
    apply_navigation_record,
    load_navigation_runtime,
    order_navigation_requests,
)
from knee.diagnosis.squint_interfaces import territory_bank_name
from knee.study.tables import LABELS


def _record(uid="query"):
    bank = territory_bank_name(
        {"orientation": "Sagittal", "fluid_sensitive": "1", "fat_suppression": "1"},
        "object",
        "signal_median",
        "centre",
        10,
    )
    subjects = [
        "acl",
        "mcl",
        "medial_meniscus",
        "lateral_meniscus",
        "femur",
        "patella",
        "joint_fluid",
        "synovium",
        "gastrocnemius_semimembranosus_bursa",
    ]
    return {
        "schema": "knee.squint-study/v1",
        "study_uid": uid,
        "study_status": "examined",
        "objects": {
            s: {"profile": {"subject": s, "banks": {bank: [1, 2, 3]}}} for s in subjects
        },
        "values": {q: 0.5 for q in LABELS},
        "questions": {
            q: {"finding": {"outcome": "open", "reason": "original"}, "objects": {}}
            for q in LABELS
        },
        "identity_recall": {"signed_cases": ["positive", "negative"]},
        "work": {"full_anatomy_runs": 0, "elapsed_seconds": 0.1},
        "capacity_exclusion": {"exclusion_status": "not_requested"},
    }


def _artifact(tmp_path, *, labels=None):
    folder = tmp_path / "model"
    folder.mkdir()
    schema = fit_feature_schema([_record()])
    if labels is not None:
        schema["labels"] = labels
    architecture = architecture_for(schema, hidden=2, context=1, gate=2)
    weights = {
        name: np.zeros(shape, np.float32)
        for name, shape in weight_shapes(architecture).items()
    }
    for name, values in weights.items():
        if name.endswith("opinion.bias"):
            values[:] = np.float32(np.log(4))
    for index, group in enumerate(architecture["groups"]):
        if group["name"] == "femur":
            weights["gate_head.bias"][
                index * len(LABELS) + list(LABELS).index("Fracture")
            ] = np.float32(np.log(9))
    weights["input_mean"] = np.zeros(architecture["feature_count"], np.float32)
    weights["input_scale"] = np.ones(architecture["feature_count"], np.float32)
    np.savez(folder / "weights.npz", allow_pickle=False, **weights)
    (folder / "schema.json").write_text(json.dumps(schema))
    manifest = {
        "format": "rsna-knee-som-navigation-v1",
        "architecture": architecture,
        "schema_sha256": hashlib.sha256(
            (folder / "schema.json").read_bytes()
        ).hexdigest(),
        "weights_sha256": hashlib.sha256(
            (folder / "weights.npz").read_bytes()
        ).hexdigest(),
        "parameter_count": sum(
            v.size for k, v in weights.items() if not k.startswith("input_")
        ),
        "provenance": {"source_pins": {"input": "test-only-fixed-record"}},
    }
    (folder / "navigation.json").write_text(json.dumps(manifest))
    return folder


def test_navigation_changes_only_numerical_output_and_retains_signed_symbolic_evidence(
    tmp_path,
):
    runtime = load_navigation_runtime(_artifact(tmp_path))
    record = _record()
    before = copy.deepcopy(record)
    result = apply_navigation_record(runtime, record)
    assert record == before
    assert result["questions"] == before["questions"]
    assert result["identity_recall"] == before["identity_recall"]
    assert result["objects"] == before["objects"]
    assert result["navigation"]["original_values"] == before["values"]
    assert list(result["values"]) == list(LABELS)
    assert all(v == pytest.approx(0.8) for v in result["values"].values())
    assert result["navigation"]["outcome"] == "applied"
    assert (
        result["navigation"]["scope"]
        == "study_condition_model_opinion_not_localized_tissue"
    )
    assert result["readout_policy_id"] == "knee.warranted-endpoints-open-grade/v1"
    assert result["navigation"]["readout_policy_id"] == result["readout_policy_id"]
    assert (
        result["navigation"]["artifact_pins"]["navigation.json"]
        == hashlib.sha256((tmp_path / "model/navigation.json").read_bytes()).hexdigest()
    )


@pytest.mark.parametrize(
    ("outcome", "opinion", "expected"),
    [
        ("assigned", 0.01, 1.0),
        ("defeated", 0.99, 0.0),
        ("open", 0.99, 0.99),
        ("open", 0.01, 0.01),
        ("open", 0.0, math.nextafter(0.0, 1.0)),
        ("open", 1.0, math.nextafter(1.0, 0.0)),
        ("open", math.nextafter(0.0, 1.0), math.nextafter(0.0, 1.0)),
        ("open", math.nextafter(1.0, 0.0), math.nextafter(1.0, 0.0)),
    ],
)
def test_symbolic_warrant_owns_endpoints_and_only_open_gets_navigation_grade(
    tmp_path, monkeypatch, outcome, opinion, expected
):
    runtime = load_navigation_runtime(_artifact(tmp_path))
    record = _record()
    record["questions"]["ACL"]["finding"]["outcome"] = outcome
    before = copy.deepcopy(record)
    monkeypatch.setattr(
        "knee.diagnosis.som_runtime.predict_navigation",
        lambda *args: np.full((1, len(LABELS)), opinion, np.float64),
    )
    result = apply_navigation_record(runtime, record)
    assert result["values"]["ACL"] == expected
    assert result["navigation"]["numerical_values"]["ACL"] == opinion
    assert result["navigation"]["readout_values"]["ACL"] == expected
    assert result["questions"] == before["questions"]
    assert record == before


@pytest.mark.parametrize("outcome", [None, "conflict", "unknown", "assigned-by-model"])
def test_unknown_or_malformed_categorical_state_never_becomes_certainty(
    tmp_path, outcome
):
    from knee.diagnosis.squint_contracts import ContractError

    runtime = load_navigation_runtime(_artifact(tmp_path))
    record = _record()
    record["questions"]["ACL"]["finding"]["outcome"] = outcome
    with pytest.raises(ContractError, match="finding_outcome_invalid"):
        apply_navigation_record(runtime, record)


def test_no_navigation_is_exact_noop_and_budget_empty_never_gets_model_diagnosis(
    tmp_path, monkeypatch
):
    record = _record()
    assert apply_navigation_record(None, record) is record
    runtime = load_navigation_runtime(_artifact(tmp_path))
    record["study_status"] = "not_examined_budget"
    record["objects"] = {}
    monkeypatch.setattr(
        "knee.diagnosis.som_runtime.predict_navigation",
        lambda *a: pytest.fail("budget-empty prediction"),
    )
    result = apply_navigation_record(runtime, record)
    assert result["values"] == record["values"]
    assert result["questions"] == record["questions"]
    assert result["navigation"]["outcome"] == "skipped_unexamined_budget"


def test_runtime_refuses_reordered_condition_labels_and_tampered_artifact(tmp_path):
    folder = _artifact(tmp_path, labels=list(reversed(LABELS)))
    with pytest.raises(NavigationRuntimeError, match="label_order"):
        load_navigation_runtime(folder)
    (folder / "schema.json").write_text("{}")
    with pytest.raises((NavigationRuntimeError, ValueError), match="pin mismatch"):
        load_navigation_runtime(folder)


@pytest.mark.parametrize(
    "bad", [np.full((1, 12), np.nan), np.full((1, 12), -0.1), np.ones((1, 11))]
)
def test_runtime_never_clips_or_accepts_invalid_predictions(tmp_path, monkeypatch, bad):
    runtime = load_navigation_runtime(_artifact(tmp_path))
    monkeypatch.setattr("knee.diagnosis.som_runtime.predict_navigation", lambda *a: bad)
    with pytest.raises(NavigationRuntimeError, match="prediction"):
        apply_navigation_record(runtime, _record())


def test_learned_priority_keeps_every_request_and_mandatory_first(
    tmp_path, monkeypatch
):
    runtime = load_navigation_runtime(_artifact(tmp_path))
    groups = runtime.model.architecture["groups"]
    weights = np.zeros((1, 12, len(groups)), np.float32)
    for i, group in enumerate(groups):
        if group["name"] == "femur":
            weights[:, :, i] = 0.9
        if group["name"] == "patella":
            weights[:, :, i] = 0.1
    monkeypatch.setattr(
        "knee.diagnosis.som_runtime.predict_navigation_details",
        lambda *a: {
            "probabilities": np.full((1, 12), 0.8, np.float32),
            "trust_weights": weights,
        },
    )
    requests = [
        {"object": "patella", "request_id": "optional-low"},
        {"object": "femur", "request_id": "optional-high"},
        {"object": "patella", "request_id": "mandatory", "discretionary": False},
        {"object": "unknown", "request_id": "unmapped"},
    ]
    before = copy.deepcopy(requests)
    ordered, receipt = order_navigation_requests(
        runtime, _record(), "Fracture", requests
    )
    assert requests == before
    assert [r["request_id"] for r in ordered] == [
        "mandatory",
        "optional-high",
        "optional-low",
        "unmapped",
    ]
    assert sorted(r["request_id"] for r in ordered) == sorted(
        r["request_id"] for r in requests
    )
    assert receipt["outcome"] == "ordered"
    assert len(receipt["before"]) == len(receipt["after"]) == 4
    assert receipt["artifact_pins"] == runtime.artifact_pins


def test_declared_feature_writer_pin_is_checked_before_any_prediction(tmp_path):
    from knee.diagnosis import som_features

    folder = _artifact(tmp_path)
    schema_path = folder / "schema.json"
    manifest_path = folder / "navigation.json"
    schema = json.loads(schema_path.read_text())
    schema["source_pins"] = {
        "feature_writer_sha256": hashlib.sha256(
            Path(som_features.__file__).read_bytes()
        ).hexdigest()
    }
    schema_path.write_text(json.dumps(schema))
    manifest = json.loads(manifest_path.read_text())
    manifest["schema_sha256"] = hashlib.sha256(schema_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    runtime = load_navigation_runtime(folder)
    assert (
        runtime.feature_writer_sha256 == schema["source_pins"]["feature_writer_sha256"]
    )
    schema["source_pins"]["feature_writer_sha256"] = "0" * 64
    schema_path.write_text(json.dumps(schema))
    manifest["schema_sha256"] = hashlib.sha256(schema_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(NavigationRuntimeError, match="feature_writer_pin_mismatch"):
        load_navigation_runtime(folder)


def test_numerical_failure_keeps_original_symbolic_values_and_request_order(
    tmp_path, monkeypatch
):
    runtime = load_navigation_runtime(_artifact(tmp_path))
    record = _record()

    def failed(*args):
        raise FloatingPointError("finite OOD conditioning")

    monkeypatch.setattr("knee.diagnosis.som_runtime.predict_navigation", failed)
    monkeypatch.setattr("knee.diagnosis.som_runtime.predict_navigation_details", failed)
    result = apply_navigation_record(runtime, record)
    assert result["values"] == record["values"]
    assert result["questions"] == record["questions"]
    assert result["navigation"]["outcome"] == "navigation_numerical_failure"
    requests = [
        {"object": "femur", "request_id": "first"},
        {"object": "patella", "request_id": "second"},
    ]
    ordered, receipt = order_navigation_requests(runtime, record, "Fracture", requests)
    assert ordered == requests
    assert receipt["outcome"] == "navigation_numerical_failure"
    assert receipt["before"] == receipt["after"]


def _coordinator(monkeypatch, tmp_path, outcomes=None):
    from knee.diagnosis import squint_locator, squint_pipeline

    memory = tmp_path / "memory"
    memory.mkdir()
    (memory / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "knee.squint-memory/v1",
                "revision": "r1",
                "questions": list(LABELS),
                "cases": [],
            }
        )
    )
    monkeypatch.setattr(
        squint_locator,
        "prepare_recall",
        lambda *args, **kwargs: {"outcome": "prepared"},
    )
    seen = []

    def infer(root, uid, memory, **kwargs):
        seen.append(kwargs.get("navigation_runtime"))
        record = _record(uid)
        for question, outcome in (outcomes or {}).items():
            record["questions"][question]["finding"]["outcome"] = outcome
        return record

    monkeypatch.setattr(squint_pipeline, "infer_study", infer)
    template = tmp_path / "template.csv"
    template.write_text(
        "StudyInstanceUID,"
        + ",".join(LABELS)
        + "\na,"
        + ",".join(["0.5"] * 12)
        + "\nb,"
        + ",".join(["0.5"] * 12)
        + "\n"
    )
    return memory, template, seen


def test_actual_cli_loads_navigation_once_and_csv_uses_graded_values(
    tmp_path, monkeypatch
):
    import csv

    from knee.diagnosis.squint_pipeline import run_squint_cli
    from knee.json_store import load_json

    memory, template, seen = _coordinator(monkeypatch, tmp_path)
    artifact = _artifact(tmp_path)
    loaded = []
    original = load_navigation_runtime

    def loader(path):
        loaded.append(path)
        return original(path)

    monkeypatch.setattr("knee.diagnosis.som_runtime.load_navigation_runtime", loader)
    result = run_squint_cli(
        Namespace(
            diagnostic_mode="infer",
            diagnostic_memory=memory,
            diagnostic_navigation=artifact,
            diagnostic_output=tmp_path / "out",
            root=tmp_path,
            study_uid=["a", "b"],
            workers=2,
            diagnostic_submission_template=template,
        )
    )
    assert loaded == [artifact]
    assert len(seen) == 2 and seen[0] is seen[1]
    with (tmp_path / "out/submission.csv").open() as stream:
        rows = list(csv.reader(stream))
    assert all(float(v) == pytest.approx(0.8) for row in rows[1:] for v in row[1:])
    assert result["navigation"]["study_outcomes"] == {"applied": 2}
    assert result["readout_policy_id"] == "knee.warranted-endpoints-open-grade/v1"
    assert (
        result["submission"]["source_provenance"]["readout_policy_id"]
        == result["readout_policy_id"]
    )
    for item in result["work"]["studies"]:
        stored = load_json(tmp_path / "out" / item["evidence_path"])
        assert stored["questions"] == _record()["questions"]
        assert stored["navigation"]["original_values"] == _record()["values"]


def test_actual_cli_without_flag_never_loads_navigation_or_changes_record_values(
    tmp_path, monkeypatch
):
    from knee.diagnosis.squint_pipeline import run_squint_cli
    from knee.json_store import load_json

    memory, template, seen = _coordinator(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "knee.diagnosis.som_runtime.load_navigation_runtime",
        lambda *a: pytest.fail("default navigation load"),
    )
    result = run_squint_cli(
        Namespace(
            diagnostic_mode="infer",
            diagnostic_memory=memory,
            diagnostic_output=tmp_path / "out",
            root=tmp_path,
            study_uid=["a", "b"],
            workers=2,
            diagnostic_submission_template=template,
        )
    )
    assert seen == [None, None]
    assert "navigation" not in result
    for item in result["work"]["studies"]:
        stored = load_json(tmp_path / "out" / item["evidence_path"])
        assert stored["values"] == _record()["values"]
        assert "navigation" not in stored


@pytest.mark.parametrize("mode", ["capacity", "teach"])
def test_navigation_refuses_modes_without_matching_model_study_exclusion(
    tmp_path, mode
):
    from knee.diagnosis.squint_pipeline import SquintRunError, run_squint_cli

    with pytest.raises(SquintRunError, match="navigation_requires_infer"):
        run_squint_cli(
            Namespace(diagnostic_mode=mode, diagnostic_navigation=tmp_path / "model")
        )


def test_real_infer_study_uses_learned_gate_before_actual_request_consumer(
    tmp_path, monkeypatch
):
    from knee.diagnosis import (
        squint_contracts,
        squint_locator,
        squint_pipeline,
        squint_profiles,
    )

    runtime = load_navigation_runtime(_artifact(tmp_path))
    monkeypatch.setattr(
        squint_profiles, "read_study_squints", lambda *a, **k: {"work": {}}
    )
    monkeypatch.setattr(
        squint_locator,
        "locate_objects",
        lambda *a, **k: {"objects": _record()["objects"]},
    )
    monkeypatch.setattr(
        squint_pipeline, "_identity_readings", lambda *a, **k: {"objects": {}}
    )
    monkeypatch.setattr(
        squint_pipeline, "_resolve_identity_contests", lambda *a, **k: {}
    )
    monkeypatch.setattr(
        squint_pipeline, "_identity_consumption", lambda *a, **k: {"objects": {}}
    )
    monkeypatch.setattr(squint_pipeline, "_recall_question", lambda *a, **k: {})
    monkeypatch.setattr(
        squint_pipeline, "_refresh_identity_after_observations", lambda *a, **k: None
    )
    monkeypatch.setattr(squint_pipeline, "_subject_cue_snapshot", lambda *a: None)
    monkeypatch.setattr(
        squint_pipeline, "_condition_state_snapshot", lambda *a: {"outcome": "open"}
    )
    requests = [
        {"object": "patella", "request_id": "low"},
        {"object": "femur", "request_id": "high"},
        {"object": "patella", "request_id": "mandatory", "discretionary": False},
    ]

    def combine(question, evidence):
        return {
            "outcome": "open",
            "reason": "test",
            "rank": {"value": 0.5},
            "observation_requests": copy.deepcopy(requests)
            if question == "Fracture"
            else [],
        }

    monkeypatch.setattr(squint_contracts, "combine_condition", combine)
    consumed = []

    def route(request, *args, **kwargs):
        consumed.append(request["request_id"])
        return {"code": "no_reading", "subject": request["object"]}

    monkeypatch.setattr(
        "knee.diagnosis.squint_procedures.route_observation_request", route
    )
    result = squint_pipeline.infer_study(
        tmp_path, "query", {}, navigation_runtime=runtime
    )
    assert consumed == ["mandatory", "high", "low"]
    assert result["values"] == {q: 0.5 for q in LABELS}
    ordering = result["navigation_request_orderings"][0]
    assert ordering["question"] == "Fracture"
    assert [x["request_id"] for x in ordering["before"]] == ["low", "high", "mandatory"]
    assert [x["request_id"] for x in ordering["after"]] == consumed
    assert ordering["after"][1]["gate_weight"] > ordering["after"][2]["gate_weight"]


def _script_module(path, name, monkeypatch):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    return module


def _minimal_bundle(tmp_path, monkeypatch, navigation):
    root = Path(__file__).resolve().parents[1]
    packager = _script_module(
        root / "scripts/package_squint_kaggle.py", "som_packager_test", monkeypatch
    )
    repo = tmp_path / "repo"
    for name in (
        "__init__",
        "diagnosis/__init__",
        "diagnosis/squint_profiles",
        "diagnosis/squint_memory",
        "diagnosis/squint_locator",
        "diagnosis/squint_pipeline",
    ):
        path = repo / "src/knee" / (name + ".py")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")
    entry = repo / "scripts/run_interiors.py"
    entry.parent.mkdir()
    entry.write_text("print('entry')\n")
    memory = tmp_path / "memory"
    memory.mkdir()
    memory_bytes = json.dumps(
        {
            "schema": "knee.squint-memory/v1",
            "cases": [],
            "object_identity_cases": [{"signed": -1}],
        }
    ).encode()
    (memory / "manifest.json").write_bytes(memory_bytes)
    output = tmp_path / "bundle-output"
    packager.build_staging(memory, output, repo, navigation=navigation)
    manifest = json.loads((output / packager.MANIFEST_NAME).read_text())
    return packager, repo, memory, memory_bytes, output, manifest


def test_navigation_package_is_exact_numeric_artifact_and_keeps_memory(
    tmp_path, monkeypatch
):
    artifact = _artifact(tmp_path)
    (artifact / "training-secret.txt").write_text("must not be shipped")
    packager, repo, memory, original, output, manifest = _minimal_bundle(
        tmp_path, monkeypatch, artifact
    )
    assert [
        row["path"] for row in manifest["files"] if row["role"] == "navigation"
    ] == [
        "navigation/navigation.json",
        "navigation/schema.json",
        "navigation/weights.npz",
    ]
    with tarfile.open(output / packager.TAR_NAME) as archive:
        extracted = archive.extractfile("memory/manifest.json")
        assert extracted is not None
        assert extracted.read() == original
        assert not any(
            name.endswith("training-secret.txt") for name in archive.getnames()
        )
    assert (memory / "manifest.json").read_bytes() == original
    assert packager.verify_staging(
        output, memory=memory, root=repo, navigation=artifact
    )["compared_with_sources"] == ["memory", "navigation", "runtime_script", "source"]
    (artifact / "weights.npz").write_bytes(b"not numeric weights")
    with pytest.raises(packager.PackagingError, match="invalid navigation"):
        packager.plan_navigation(artifact)


def test_default_package_has_no_navigation_and_new_artifact_changes_bundle(
    tmp_path, monkeypatch
):
    _, _, _, _, _, manifest = _minimal_bundle(tmp_path, monkeypatch, None)
    assert "navigation" not in manifest
    assert not any(row["path"].startswith("navigation/") for row in manifest["files"])


def test_wrapper_checks_artifact_in_numpy_only_runtime_and_rejects_wrong_scope(
    tmp_path, monkeypatch
):
    root = Path(__file__).resolve().parents[1]
    artifact = _artifact(tmp_path)
    packager, _, _, _, _, manifest = _minimal_bundle(tmp_path, monkeypatch, artifact)
    wrapper = _script_module(
        root / "kaggle/squint-production/run_squint.py", "som_wrapper_test", monkeypatch
    )
    bundle = tmp_path / "extracted"
    (bundle / "navigation").mkdir(parents=True)
    for name in packager.NAVIGATION_FILES:
        (bundle / "navigation" / name).write_bytes((artifact / name).read_bytes())
    monkeypatch.setattr(wrapper, "LOCAL", tmp_path / "local")
    (wrapper.LOCAL / "cwd").mkdir(parents=True)
    monkeypatch.setattr(wrapper, "append_setup_log", lambda *args: None)
    env = {**os.environ, "PYTHONPATH": str(root / "src")}
    template = {"header": ["StudyInstanceUID", *LABELS]}
    assert (
        wrapper.validate_navigation(bundle, manifest, env, sys.executable, template)
        == bundle / "navigation"
    )
    assert (
        wrapper.REPORT["navigation"]["specialists"]
        == manifest["navigation"]["specialists"]
    )
    assert "--diagnostic-navigation" in wrapper.ALLOWED_FLAGS
    assert (
        wrapper.validate_navigation(
            bundle, {"files": []}, env, sys.executable, template
        )
        is None
    )
    bad = copy.deepcopy(manifest)
    bad["navigation"]["specialists"][0] = "invented-specialist"
    with pytest.raises(wrapper.SetupError, match="disagrees"):
        wrapper.validate_navigation(bundle, bad, env, sys.executable, template)
    bad = copy.deepcopy(manifest)
    del bad["navigation"]
    with pytest.raises(wrapper.SetupError, match="metadata"):
        wrapper.navigation_metadata(bad)
    (bundle / "navigation/weights.npz").write_bytes(b"changed")
    with pytest.raises(wrapper.SetupError, match="file changed"):
        wrapper.validate_navigation(bundle, manifest, env, sys.executable, template)


def test_actual_cli_csv_keeps_exact_symbolic_endpoints_with_navigation(
    tmp_path, monkeypatch
):
    import csv

    from knee.diagnosis.squint_pipeline import run_squint_cli
    from knee.json_store import load_json

    memory, template, _ = _coordinator(
        monkeypatch, tmp_path, {"ACL": "assigned", "MCL": "defeated"}
    )
    artifact = _artifact(tmp_path)
    result = run_squint_cli(
        Namespace(
            diagnostic_mode="infer",
            diagnostic_memory=memory,
            diagnostic_navigation=artifact,
            diagnostic_output=tmp_path / "out",
            root=tmp_path,
            study_uid=["a", "b"],
            workers=2,
            diagnostic_submission_template=template,
        )
    )
    with (tmp_path / "out/submission.csv").open() as stream:
        rows = list(csv.reader(stream))
    for row in rows[1:]:
        assert [float(value) for value in row[1:3]] == [1.0, 0.0]
        assert all(float(v) == pytest.approx(0.8) for v in row[3:])
    stored = load_json(tmp_path / "out" / result["work"]["studies"][0]["evidence_path"])
    assert stored["navigation"]["numerical_values"]["MCL"] == pytest.approx(0.8)
    assert stored["values"]["MCL"] == 0.0


@pytest.mark.parametrize(
    "outcome, grade, expected",
    [
        ("assigned", 0.01, 1.0),
        ("defeated", 0.99, 0.0),
        ("open", 0.2, 0.2),
    ],
)
def test_real_default_infer_study_serializes_warrant_without_navigation(
    tmp_path, monkeypatch, outcome, grade, expected
):
    from knee.diagnosis import (
        squint_contracts,
        squint_locator,
        squint_pipeline,
        squint_profiles,
    )

    monkeypatch.setattr(
        squint_profiles, "read_study_squints", lambda *a, **k: {"work": {}}
    )
    monkeypatch.setattr(
        squint_locator, "locate_objects", lambda *a, **k: {"objects": {}}
    )
    monkeypatch.setattr(
        squint_pipeline, "_identity_readings", lambda *a, **k: {"objects": {}}
    )
    monkeypatch.setattr(
        squint_pipeline, "_resolve_identity_contests", lambda *a, **k: {}
    )
    monkeypatch.setattr(
        squint_pipeline, "_identity_consumption", lambda *a, **k: {"objects": {}}
    )
    monkeypatch.setattr(squint_pipeline, "_recall_question", lambda *a, **k: {})
    monkeypatch.setattr(
        squint_contracts,
        "combine_condition",
        lambda *a, **k: {
            "outcome": outcome,
            "rank": {"value": grade},
            "observation_requests": [],
        },
    )
    record = squint_pipeline.infer_study(tmp_path, "query", {})
    assert record["values"] == {q: expected for q in LABELS}
    assert all(row["ranking"]["value"] == grade for row in record["questions"].values())
    assert "navigation" not in record
