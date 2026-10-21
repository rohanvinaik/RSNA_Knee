"""Production composition intent: current pixels, immutable precedents, official shape."""

import argparse
import csv
import hashlib
import json
import sys
import types
from pathlib import Path

import pytest

from knee.diagnosis.squint_pipeline import (
    SquintRunError,
    _selected_uids,
    infer_study,
    is_squint_memory,
    run_squint_cli,
)
from knee.json_store import load_json
from knee.study.tables import LABELS


def _module(monkeypatch, name, **members):
    module = types.ModuleType(name)
    vars(module).update(members)
    monkeypatch.setitem(sys.modules, name, module)
    return module


def test_new_memory_routes_without_treating_legacy_as_squint(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"schema": "knee.squint-memory/v1"}))
    assert is_squint_memory(tmp_path)
    assert is_squint_memory(manifest)
    manifest.write_text(json.dumps({"schema": "knee.other-memory/v1"}))
    assert not is_squint_memory(tmp_path)
    manifest.write_text("malformed")
    assert not is_squint_memory(manifest)
    manifest.write_text("[]")
    assert not is_squint_memory(manifest)
    manifest.write_text("null")
    assert not is_squint_memory(manifest)
    manifest.write_bytes(b"\xff")
    assert not is_squint_memory(manifest)
    assert not is_squint_memory(tmp_path / "missing.json")
    assert not is_squint_memory(None)


def test_missing_memory_selector_returns_false_not_none():
    assert is_squint_memory(None) is False


def test_selector_rejects_duplicate_or_path_uid():
    for values in (["x", "x"], ["../x"]):
        with pytest.raises(SquintRunError, match="study_uid_invalid_or_duplicate"):
            _selected_uids(argparse.Namespace(study_uid=values))
    assert _selected_uids(argparse.Namespace(study_uid=["x", "y"])) == ("x", "y")


def _wire(monkeypatch):
    calls = []

    def reader(root, uid, *, io_workers):
        calls.append(("read", uid))
        return {"study_uid": uid, "series": [], "work": {"squint_stacks": 1}}

    def locator(study, memory, *, deadline):
        return {"objects": {}}

    def recall(profile, memory, *, question, exclude_study_uid):
        assert not profile["banks"]
        calls.append(("recall", question, exclude_study_uid))
        return {"outcome": "unresolved_missing_reading", "case_terms": []}

    _module(monkeypatch, "knee.diagnosis.squint_profiles", read_study_squints=reader)
    _module(
        monkeypatch,
        "knee.diagnosis.squint_locator",
        locate_objects=locator,
        recall_object=recall,
        prepare_recall=lambda m: {"outcome": "prepared"},
    )
    _module(
        monkeypatch,
        "knee.diagnosis.squint_contracts",
        combine_condition=lambda q, o: {
            "outcome": "open",
            "reason": "missing",
            "observation_requests": [],
        },
        rank_condition=lambda f: {"value": 0.5, "policy_id": "test"},
    )
    return calls


def test_unlocated_objects_remain_open_and_do_not_invoke_reconstruction(
    monkeypatch, tmp_path
):
    calls = _wire(monkeypatch)
    record = infer_study(tmp_path, "query", {"revision": "r1"}, exclude_same_study=True)
    assert record["work"]["full_anatomy_runs"] == 0
    assert record["work"]["bounded_zoom_runs"] == 0
    assert set(record["values"]) == set(LABELS)
    assert all(q["finding"]["outcome"] == "open" for q in record["questions"].values())
    assert calls[0] == ("read", "query")
    assert all(c[2] == "query" for c in calls if c[0] == "recall")


def test_real_coordinator_writes_template_order_and_loads_memory_once(
    monkeypatch, tmp_path
):
    calls = _wire(monkeypatch)
    envelope = {
        "population_case_ids": ["independent-positive", "independent-negative"],
        "maximum_squared_cosine": {"numerator": "2", "denominator": "3"},
        "comparisons": [{"case_ids": ["independent-positive", "independent-negative"]}],
    }
    monkeypatch.setattr(
        sys.modules["knee.diagnosis.squint_locator"],
        "prepare_recall",
        lambda m: {
            "outcome": "prepared",
            "schema": "knee.squint-recall-preparation/v1",
            "envelopes": {"femur": envelope},
            "subject_profile_matrices": {"private_acceleration_cache": object()},
        },
    )
    memory = tmp_path / "memory"
    memory.mkdir()
    (memory / "manifest.json").write_text(
        json.dumps({"schema": "knee.squint-memory/v1"})
    )
    loaded = []

    def load(path):
        loaded.append(path)
        manifest = path / "manifest.json" if path.is_dir() else path
        return MemorySnapshot(
            manifest,
            "a" * 64,
            "squint",
            "knee.squint-memory/v1",
            {"revision": "r1"},
        )

    class MemorySnapshot:
        def __init__(self, path, sha256, status, declared_schema, memory):
            self.path = path.resolve()
            self.sha256 = sha256
            self.status = status
            self.declared_schema = declared_schema
            self.memory = memory
            self.error_code = None

    _module(
        monkeypatch,
        "knee.diagnosis.squint_memory",
        MemorySnapshot=MemorySnapshot,
        load_memory_snapshot=load,
        compile_bootstrap=lambda *a, **k: None,
    )
    template = tmp_path / "template.csv"
    with template.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("StudyInstanceUID", *LABELS))
        writer.writerows([(uid, *([0] * 12)) for uid in ("b", "a")])
    args = argparse.Namespace(
        diagnostic_mode="infer",
        diagnostic_memory=memory,
        diagnostic_output=tmp_path / "out",
        root=tmp_path,
        study_uid=["a", "b"],
        workers=2,
        diagnostic_submission_template=template,
    )
    result = run_squint_cli(args)
    assert loaded == [memory]
    assert sorted(c[1] for c in calls if c[0] == "read") == ["a", "b"]
    assert result["work"]["full_anatomy_runs"] == 0
    assert result["studies"] == 2
    with (tmp_path / "out/submission.csv").open() as stream:
        rows = list(csv.reader(stream))
    assert rows[0] == ["StudyInstanceUID", *LABELS]
    assert [r[0] for r in rows[1:]] == ["b", "a"]
    assert all(0 < float(v) < 1 for row in rows[1:] for v in row[1:])
    preparation = load_json(tmp_path / "out" / result["recall_preparation"]["path"])
    assert preparation["envelopes"] == {"femur": envelope}
    assert "subject_profile_matrices" not in preparation
    for study in result["work"]["studies"]:
        path = tmp_path / "out" / study["evidence_path"]
        assert path.name.endswith(".json.xz")
        assert path.stat().st_size == study["evidence_bytes"]
        retained = load_json(path)
        assert retained["study_uid"] == study["study_uid"]
        assert set(retained["values"]) == set(LABELS)


def test_direct_squint_cli_reads_and_parses_one_memory_snapshot(monkeypatch, tmp_path):
    _wire(monkeypatch)
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    manifest = memory_dir / "manifest.json"
    raw = json.dumps(
        {
            "schema": "knee.squint-memory/v1",
            "revision": "r1",
            "questions": list(LABELS),
            "cases": [],
        }
    ).encode()
    manifest.write_bytes(raw)

    reads = []
    original_read_bytes = Path.read_bytes

    def count_reads(path):
        if path.resolve() == manifest.resolve():
            reads.append(path)
        return original_read_bytes(path)

    parses = []
    original_loads = json.loads

    def count_parses(value, *args, **kwargs):
        if isinstance(value, bytes) and value == raw:
            parses.append(value)
        return original_loads(value, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", count_reads)
    monkeypatch.setattr(json, "loads", count_parses)
    result = run_squint_cli(
        argparse.Namespace(
            diagnostic_mode="infer",
            diagnostic_memory=memory_dir,
            diagnostic_output=tmp_path / "out",
            root=tmp_path,
            study_uid=["query"],
            workers=1,
        )
    )
    assert len(reads) == 1
    assert len(parses) == 1
    assert result["memory_manifest_sha256"] == hashlib.sha256(raw).hexdigest()
    assert result["memory_revision"] == "r1"
    assert result["work"]["full_anatomy_runs"] == 0


def test_inference_refuses_training_label_source(monkeypatch, tmp_path):
    _wire(monkeypatch)
    _module(
        monkeypatch,
        "knee.diagnosis.squint_memory",
        MemorySnapshot=type("MemorySnapshot", (), {}),
        load_memory_snapshot=lambda p: None,
        compile_bootstrap=lambda *a, **k: None,
    )
    args = argparse.Namespace(
        diagnostic_mode="infer",
        diagnostic_memory=tmp_path / "m",
        diagnostic_output=tmp_path / "o",
        diagnostic_labels=tmp_path / "train.csv",
    )
    with pytest.raises(SquintRunError, match="does_not_read_label_source"):
        run_squint_cli(args)
