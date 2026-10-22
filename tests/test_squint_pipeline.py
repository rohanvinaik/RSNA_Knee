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
    _budget_unexamined_study,
    _selected_uids,
    _study_budget_deadline,
    infer_study,
    is_squint_memory,
    run_squint_cli,
)
from knee.json_store import dump_json_atomic, load_json
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
    from knee.diagnosis.squint_contracts import serialize_condition_value

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
        serialize_condition_value=serialize_condition_value,
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


def test_production_location_defers_the_fine_reading_where_the_locator_declares_it(
    monkeypatch, tmp_path
):
    _wire(monkeypatch)
    seen = []

    def locator(study, memory, deadline=None, *, refine_finalists=True):
        seen.append((deadline, refine_finalists))
        return {"objects": {}}

    monkeypatch.setattr(
        sys.modules["knee.diagnosis.squint_locator"], "locate_objects", locator
    )
    infer_study(tmp_path, "query", {"revision": "r1"}, deadline=None)
    assert seen == [(None, False)]


@pytest.mark.parametrize("shape", ["teacher_control", "variadic_keywords"])
def test_a_locator_that_does_not_declare_the_keyword_is_called_as_before(
    monkeypatch, tmp_path, shape
):
    # The teacher control substitutes a locator that reads its own pairs upfront; its
    # signature is (study, memory, deadline=None) and must never be handed the keyword.
    _wire(monkeypatch)
    seen = []

    def teacher(study, memory, deadline=None):
        seen.append(deadline)
        return {"objects": {}}

    def variadic(study, memory, deadline=None, **options):
        seen.append(options)
        return {"objects": {}}

    monkeypatch.setattr(
        sys.modules["knee.diagnosis.squint_locator"],
        "locate_objects",
        teacher if shape == "teacher_control" else variadic,
    )
    record = infer_study(tmp_path, "query", {"revision": "r1"}, deadline=None)
    assert seen == ([None] if shape == "teacher_control" else [{}])
    assert record["work"]["location_fine_readings"] == 0


def test_the_deferral_is_named_only_for_a_locator_that_declares_it():
    from knee.diagnosis import squint_locator
    from knee.diagnosis.squint_pipeline import _squint_first_location

    assert _squint_first_location(squint_locator.locate_objects) == {
        "refine_finalists": False
    }
    assert _squint_first_location(lambda study, memory, deadline=None: None) == {}
    assert _squint_first_location(lambda study, memory, **options: None) == {}
    assert _squint_first_location(object()) == {}


def test_expired_study_deadline_returns_neutral_unexamined_record(
    monkeypatch, tmp_path
):
    calls = _wire(monkeypatch)
    record = infer_study(
        tmp_path,
        "late",
        {"revision": "r1"},
        deadline=0.0,
    )
    assert record["study_status"] == "not_examined_budget"
    assert record["not_examined_reason"] == "study_time_budget_exhausted_before_read"
    assert record["objects"] == {}
    assert record["observations"] == []
    assert record["work"]["image_reads"] == 0
    assert set(record["values"]) == set(LABELS)
    assert all(
        question["finding"]["outcome"] == "open"
        for question in record["questions"].values()
    )
    assert all(value == 0.5 for value in record["values"].values())
    assert calls == []


def test_budget_unexamined_record_uses_real_open_neutral_condition_contracts():
    from knee.diagnosis.declarations import QUESTIONS

    record = _budget_unexamined_study(
        "late",
        {"revision": "r4"},
        reason="study_time_budget_exhausted_before_read",
    )
    assert set(record["questions"]) == {question.question_id for question in QUESTIONS}
    for question in record["questions"].values():
        assert question["finding"]["outcome"] == "open"
        assert question["finding"]["recall_evidence"] == {}
        assert question["ranking"]["value"] == 0.5
        assert question["ranking"]["reason"] == "no_eligible_signed_support_neutral"


def test_real_coordinator_writes_template_order_and_loads_memory_once(
    monkeypatch, tmp_path
):
    calls = _wire(monkeypatch)
    from knee import json_store

    compression_calls = []
    original_dump = json_store.dump_json_atomic

    def record_compression(path, value, default=None, *, compression_preset=6):
        compression_calls.append((Path(path).name, compression_preset))
        return original_dump(
            path, value, default, compression_preset=compression_preset
        )

    monkeypatch.setattr(json_store, "dump_json_atomic", record_compression)
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
    assert compression_calls.count(("recall-preparation.json", 6)) == 1
    assert compression_calls.count(("a.json", 0)) == 1
    assert compression_calls.count(("b.json", 0)) == 1
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
        assert retained["capacity_exclusion"] == {
            "exclusion_status": "not_requested",
            "excluded_study_uid": None,
        }


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


def test_persisted_recall_cache_is_copied_as_exact_checked_bytes(monkeypatch, tmp_path):
    _wire(monkeypatch)
    locator = sys.modules["knee.diagnosis.squint_locator"]
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "manifest.json").write_text(
        json.dumps({"schema": "knee.squint-memory/v1"})
    )
    preparation = {
        "outcome": "prepared",
        "schema": "knee.squint-recall-preparation/v1",
        "source_fingerprint": "f" * 64,
        "memory_source": {"source": "bootstrap"},
        "envelopes": {"femur": {"ACL": {"banks": ["bank/a"]}}},
        "case_indices": {"femur": {"ACL": [0, 1]}},
        "censor_indices": {"ACL": []},
        "runtime_indexes_rebuilt": True,
        "case_profile_banks": {"femur": {}},
        "subject_profile_matrices": {"femur": {}},
    }
    cache = {
        "schema": "knee.squint-recall-cache/v1",
        "source_fingerprint": preparation["source_fingerprint"],
        "censor_count": 0,
        "memory_manifest_sha256": "a" * 64,
        "memory_revision": "r1",
        "preparation": {
            key: value
            for key, value in preparation.items()
            if key
            not in {
                "runtime_indexes_rebuilt",
                "case_profile_banks",
                "subject_profile_matrices",
            }
        },
    }
    source_path = dump_json_atomic(memory_dir / "recall-preparation.json", cache)
    source_bytes = source_path.read_bytes()

    def prepare(memory, *, cached=None):
        assert memory == {"revision": "r1"}
        assert cached == cache
        return preparation

    locator.prepare_recall = prepare
    memory_manifest = memory_dir / "manifest.json"

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
        load_memory_snapshot=lambda path: MemorySnapshot(
            memory_manifest,
            "a" * 64,
            "squint",
            "knee.squint-memory/v1",
            {"revision": "r1"},
        ),
        compile_bootstrap=lambda *a, **k: None,
    )

    from knee import json_store

    original_dump = json_store.dump_json_atomic

    def reject_reencoding(path, value, default=None, *, compression_preset=6):
        if Path(path).name == "recall-preparation.json":
            raise AssertionError("persisted cache should be copied without re-encoding")
        return original_dump(
            path, value, default, compression_preset=compression_preset
        )

    monkeypatch.setattr(json_store, "dump_json_atomic", reject_reencoding)
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

    output_path = tmp_path / "out" / "recall-preparation.json.xz"
    receipt = result["recall_preparation"]
    assert output_path.read_bytes() == source_bytes
    assert receipt["sha256"] == hashlib.sha256(source_bytes).hexdigest()
    assert receipt["bytes"] == len(source_bytes)
    assert receipt["schema"] == "knee.squint-recall-cache/v1"
    assert receipt["preparation_schema"] == "knee.squint-recall-preparation/v1"
    assert receipt["artifact_source"] == "persisted_cache_sidecar_bytes"
    assert receipt["identity"] == {
        "source_fingerprint": preparation["source_fingerprint"],
        "memory_manifest_sha256": "a" * 64,
        "memory_revision": "r1",
    }
    assert load_json(output_path) == cache


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


def test_capacity_excludes_study_before_preparation_locator_and_recall(
    monkeypatch, tmp_path
):
    calls = _wire(monkeypatch)
    locator_module = sys.modules["knee.diagnosis.squint_locator"]
    seen = {}

    def prepare(memory, *, cached=None, exclude_study_uid=""):
        assert exclude_study_uid == "held-out"
        assert cached is not None
        assert cached["cache_marker"] == "same-manifest"
        filtered = {
            **memory,
            "cases": [
                case for case in memory["cases"] if case["study_uid"] != "held-out"
            ],
            "censors": [
                censor
                for censor in memory["censors"]
                if censor.get("study_uid") != "held-out"
            ],
        }
        seen["prepared_memory"] = filtered
        return {
            "outcome": "prepared",
            "schema": "knee.squint-recall-preparation/v1",
            "source_fingerprint": "filtered-source-fingerprint",
            "memory_source": "filtered-memory-source",
            "case_profile_banks": {"peer-case": {"femur": [1, 0, 0]}},
            "runtime_indexes_rebuilt": True,
        }

    def locate(study, memory, *, deadline):
        seen["located_memory"] = memory
        assert all(case["study_uid"] != "held-out" for case in memory["cases"])
        assert "prepared_recall" in memory
        return {"objects": {}}

    monkeypatch.setattr(locator_module, "prepare_recall", prepare)
    monkeypatch.setattr(locator_module, "locate_objects", locate)

    def recall(profile, memory, *, question, exclude_study_uid):
        assert all(case["study_uid"] != "held-out" for case in memory["cases"])
        assert "prepared_recall" in memory
        assert exclude_study_uid == "held-out"
        calls.append(("capacity-recall", question, exclude_study_uid))
        return {"outcome": "unresolved_missing_reading", "case_terms": []}

    monkeypatch.setattr(locator_module, "recall_object", recall)

    class MemorySnapshot:
        def __init__(self, path, sha256, status, declared_schema, memory):
            self.path = path.resolve()
            self.sha256 = sha256
            self.status = status
            self.declared_schema = declared_schema
            self.memory = memory
            self.error_code = None

    memory = {
        "revision": "r2",
        "cases": [
            {"case_id": "held-case", "study_uid": "held-out"},
            {"case_id": "peer-case", "study_uid": "peer"},
        ],
        "censors": [
            {"study_uid": "held-out", "question": "ACL"},
            {"source": {"study_uid": "peer"}, "question": "MCL"},
        ],
    }

    def load(path):
        return MemorySnapshot(
            path / "manifest.json", "b" * 64, "squint", "knee.squint-memory/v1", memory
        )

    _module(
        monkeypatch,
        "knee.diagnosis.squint_memory",
        MemorySnapshot=MemorySnapshot,
        load_memory_snapshot=load,
        compile_bootstrap=lambda *a, **k: None,
    )
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "manifest.json").write_text("{}")
    dump_json_atomic(
        memory_dir / "recall-preparation.json",
        {
            "memory_manifest_sha256": "b" * 64,
            "memory_revision": "r2",
            "cache_marker": "same-manifest",
        },
    )
    result = run_squint_cli(
        argparse.Namespace(
            diagnostic_mode="capacity",
            diagnostic_memory=memory_dir,
            diagnostic_output=tmp_path / "capacity-out",
            root=tmp_path,
            study_uid=["held-out"],
            workers=1,
            squint_time_limit=60.0,
        )
    )
    prepared_memory = seen["prepared_memory"]
    assert prepared_memory["cases"] == [{"case_id": "peer-case", "study_uid": "peer"}]
    assert prepared_memory["censors"] == [
        {"source": {"study_uid": "peer"}, "question": "MCL"}
    ]
    assert seen["located_memory"]["prepared_recall"]["source_fingerprint"] == (
        "filtered-source-fingerprint"
    )
    assert any(c[0] == "capacity-recall" for c in calls)
    capacity = result["work"]["studies"][0]["capacity_exclusion"]
    assert capacity == {
        "excluded_study_uid": "held-out",
        "exclusion_status": "applied",
        "original_case_count": 2,
        "filtered_case_count": 1,
        "excluded_case_count": 1,
        "original_censor_count": 2,
        "filtered_censor_count": 1,
        "excluded_censor_count": 1,
        "consumed_case_fingerprint": "filtered-source-fingerprint",
        "consumed_fingerprint_scope": "source_cases_calls_profiles_and_censors_v1",
        "preparation_schema": "knee.squint-recall-preparation/v1",
        "preparation_outcome": "prepared",
        "prepared_population_identity": {
            "status": "prepared",
            "source_fingerprint": "filtered-source-fingerprint",
            "source": "filtered-memory-source",
            "memory_manifest_sha256": "b" * 64,
            "case_profile_count": 1,
        },
    }
    assert result["work"]["studies"][0]["capacity_exclusion"] == capacity
    assert result["work"]["studies"][0]["recall_preparation_source"] == (
        "study_excluded_projected"
    )


def test_exhausted_overall_budget_skips_capacity_preparation_and_records_abstention(
    monkeypatch, tmp_path
):
    _wire(monkeypatch)
    import knee.diagnosis.squint_pipeline as pipeline

    locator_module = sys.modules["knee.diagnosis.squint_locator"]
    preparation_calls = []

    def prepare(*args, **kwargs):
        preparation_calls.append((args, kwargs))
        raise AssertionError("capacity preparation started after deadline")

    monkeypatch.setattr(locator_module, "prepare_recall", prepare)

    class MemorySnapshot:
        def __init__(self, path, sha256, status, declared_schema, memory):
            self.path = path.resolve()
            self.sha256 = sha256
            self.status = status
            self.declared_schema = declared_schema
            self.memory = memory
            self.error_code = None

    memory = {
        "revision": "r3",
        "source": {"source_id": "budget-memory"},
        "cases": [{"case_id": "held", "study_uid": "held-out"}],
        "censors": [{"question": "ACL", "study_uid": "held-out"}],
    }
    _module(
        monkeypatch,
        "knee.diagnosis.squint_memory",
        MemorySnapshot=MemorySnapshot,
        load_memory_snapshot=lambda path: MemorySnapshot(
            path / "manifest.json",
            "c" * 64,
            "squint",
            "knee.squint-memory/v1",
            memory,
        ),
        compile_bootstrap=lambda *a, **k: None,
    )
    memory_dir = tmp_path / "budget-memory"
    memory_dir.mkdir()
    (memory_dir / "manifest.json").write_text("{}")
    moments = iter((0.0, 2.0, 2.0))
    monkeypatch.setattr(pipeline.time, "monotonic", lambda: next(moments))
    result = run_squint_cli(
        argparse.Namespace(
            diagnostic_mode="capacity",
            diagnostic_memory=memory_dir,
            diagnostic_output=tmp_path / "budget-out",
            root=tmp_path,
            study_uid=["held-out"],
            workers=1,
            squint_time_limit=1.0,
        )
    )
    assert preparation_calls == []
    assert result["per_question"]["ACL"] == {"not_examined_budget": 1}
    summary = result["work"]["studies"][0]
    retained = load_json(tmp_path / "budget-out" / summary["evidence_path"])
    assert retained["study_status"] == "not_examined_budget"
    assert retained["not_examined_reason"] == (
        "study_time_budget_exhausted_before_preparation"
    )
    assert retained["work"]["image_reads"] == 0
    assert retained["objects"] == {}
    assert all(value == 0.5 for value in retained["values"].values())
    assert retained["capacity_exclusion"]["exclusion_status"] == "applied"
    assert retained["capacity_exclusion"]["preparation_outcome"] == (
        "not_run_budget_exhausted"
    )
    assert retained["capacity_exclusion"]["consumed_case_fingerprint"] is None
    assert summary["capacity_exclusion"] == retained["capacity_exclusion"]


def test_each_study_receives_only_its_remaining_time_share():
    deadline, budget = _study_budget_deadline(100.0, 4, 2, now=20.0)
    assert budget == 40.0
    assert deadline == 60.0
    assert _study_budget_deadline(100.0, 3, 3, now=20.0) == (100.0, 80.0)
    assert _study_budget_deadline(100.0, 12, 4, now=10.0) == (40.0, 30.0)
    assert _study_budget_deadline(100.0, 1, 4, now=20.0) == (100.0, 80.0)
    exhausted, zero_budget = _study_budget_deadline(100.0, 3, 2, now=100.0)
    assert exhausted == 100.0
    assert zero_budget == 0.0
    with pytest.raises(SquintRunError, match="remaining_studies_invalid"):
        _study_budget_deadline(100.0, 0, 1, now=20.0)


def _identity_run_snapshot(monkeypatch, tmp_path, memory):
    class MemorySnapshot:
        def __init__(self, path, sha256, status, declared_schema, payload):
            self.path = path.resolve()
            self.sha256 = sha256
            self.status = status
            self.declared_schema = declared_schema
            self.memory = payload
            self.error_code = None

    _module(
        monkeypatch,
        "knee.diagnosis.squint_memory",
        MemorySnapshot=MemorySnapshot,
        load_memory_snapshot=lambda path: MemorySnapshot(
            path / "manifest.json", "c" * 64, "squint", "knee.squint-memory/v1", memory
        ),
        compile_bootstrap=lambda *a, **k: None,
    )
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "manifest.json").write_text("{}")
    return memory_dir


def test_production_studies_reuse_one_identity_preparation_for_shared_view(
    monkeypatch, tmp_path
):
    _wire(monkeypatch)
    preparations = []

    def prepare(memory, *, exclude_study_uid=None, scale="10mm"):
        prepared = {
            "outcome": "prepared",
            "source_pin": f"shared-unexcluded-view-{scale}",
            "exclude_study_uid": exclude_study_uid,
        }
        preparations.append((memory, exclude_study_uid, scale, prepared))
        return prepared

    _module(
        monkeypatch,
        "knee.diagnosis.squint_identity",
        prepare_identity=prepare,
        recall_identity=lambda *a, **k: {"outcome": "test"},
    )
    memory = {
        "revision": "r1",
        "object_identity_teaching": {"schema": "knee.object-identity-teaching/v1"},
    }
    memory_dir = _identity_run_snapshot(monkeypatch, tmp_path, memory)
    from knee.diagnosis.squint_pipeline import run_squint_cli
    from knee.json_store import load_json

    result = run_squint_cli(
        argparse.Namespace(
            diagnostic_mode="infer",
            diagnostic_memory=memory_dir,
            diagnostic_output=tmp_path / "out",
            root=tmp_path,
            study_uid=["query-a", "query-b"],
            workers=2,
        )
    )
    # Once per bank set, for the whole run, from the one memory object.
    assert [(item[1], item[2]) for item in preparations] == [
        (None, "10mm"),
        (None, "10mm+2mm"),
    ]
    assert preparations[0][0] is preparations[1][0]
    assert result["work"]["identity_preparations_shared"] == 1
    assert result["work"]["identity_resolved_preparations_shared"] == 1
    assert result["work"]["identity_preparation_seconds"] >= 0
    for study in result["work"]["studies"]:
        assert study["identity_preparation_source"] == "shared_once"
        record = load_json(tmp_path / "out" / study["evidence_path"])
        assert record["identity_recall"]["preparation"]["source_pin"] == (
            "shared-unexcluded-view-10mm"
        )


def test_capacity_studies_prepare_distinct_held_out_identity_views(
    monkeypatch, tmp_path
):
    _wire(monkeypatch)
    from knee.diagnosis import squint_pipeline

    diagnosis_module = sys.modules["knee.diagnosis.squint_locator"]
    diagnosis_module.prepare_recall = (
        lambda memory, *, cached=None, exclude_study_uid=None: {
            "outcome": "prepared",
            "runtime_indexes_rebuilt": True,
        }
    )
    monkeypatch.setattr(
        squint_pipeline, "recall_source_fingerprint", lambda memory: "fp"
    )
    excluded_views = []

    def exclude(memory, uid):
        filtered = {
            **memory,
            "cases": [case for case in memory["cases"] if case["study_uid"] != uid],
            "view": {
                "schema": squint_pipeline.MEMORY_VIEW_SCHEMA,
                "excluded_study_uids": [uid],
                "source_fingerprint": "fp",
            },
        }
        return filtered, {"excluded_study_uid": uid}

    monkeypatch.setattr(squint_pipeline, "_study_excluded_memory", exclude)
    monkeypatch.setattr(
        squint_pipeline,
        "_capacity_exclusion_evidence",
        lambda excluded, prepared, **kwargs: {
            "excluded_study_uid": excluded["excluded_study_uid"],
            "exclusion_status": "applied",
        },
    )

    def prepare_identity(memory, *, exclude_study_uid=None):
        case_studies = {case["study_uid"] for case in memory["cases"]}
        prepared = {
            "outcome": "prepared",
            "exclude_study_uid": exclude_study_uid,
            "case_studies": sorted(case_studies),
            "source_pin": "for-" + str(exclude_study_uid),
        }
        excluded_views.append(prepared)
        return prepared

    _module(
        monkeypatch,
        "knee.diagnosis.squint_identity",
        prepare_identity=prepare_identity,
        recall_identity=lambda *a, **k: {"outcome": "test"},
    )
    memory = {
        "revision": "r2",
        "cases": [
            {"case_id": "a-case", "study_uid": "held-a"},
            {"case_id": "b-case", "study_uid": "held-b"},
        ],
        "censors": [],
        "object_identity_teaching": {"schema": "knee.object-identity-teaching/v1"},
    }
    memory_dir = _identity_run_snapshot(monkeypatch, tmp_path, memory)
    from knee.diagnosis.squint_pipeline import run_squint_cli
    from knee.json_store import load_json

    result = run_squint_cli(
        argparse.Namespace(
            diagnostic_mode="capacity",
            diagnostic_memory=memory_dir,
            diagnostic_output=tmp_path / "capacity-out",
            root=tmp_path,
            study_uid=["held-a", "held-b"],
            workers=2,
            squint_time_limit=60.0,
        )
    )
    assert {row["exclude_study_uid"] for row in excluded_views} == {"held-a", "held-b"}
    assert result["work"]["identity_preparations_shared"] == 0
    assert {tuple(row["case_studies"]) for row in excluded_views} == {
        ("held-b",),
        ("held-a",),
    }
    for study in result["work"]["studies"]:
        assert study["identity_preparation_source"] == "study_excluded"
        record = load_json(tmp_path / "capacity-out" / study["evidence_path"])
        preparation = record["identity_recall"]["preparation"]
        assert preparation["exclude_study_uid"] == study["study_uid"]
        assert study["study_uid"] not in preparation["case_studies"]
