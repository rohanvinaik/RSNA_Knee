from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

CANDIDATE = Path(__file__).parents[1]
sys.path.insert(0, str(CANDIDATE / "src"))

from knee.json_store import load_json
from knee.receipt import merged_receipt
from knee.receipt_batch import ReceiptBatch

REQUEST = {"profile": "same"}


class JsonCodec:
    def __init__(self):
        self.loads: list[Path] = []
        self.dumps: list[Path] = []
        self.fail_final = False

    @staticmethod
    def compressed_path(path: Path) -> Path:
        return path.with_name(path.name + ".xz")

    def load_json(self, path: Path):
        self.loads.append(path)
        candidates = (path, path.with_name(path.name + ".xz"))
        for candidate in candidates:
            if candidate.exists():
                return json.loads(candidate.read_text())
        raise FileNotFoundError(path)

    def dump_json_atomic(self, path: Path, value, *, default=None):
        self.dumps.append(path)
        if self.fail_final and path.name == "receipt.json":
            raise OSError("final publish failed")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(json.dumps(value, default=default))
        temporary.replace(path)

    def kwargs(self):
        return {
            "load_json": self.load_json,
            "compressed_path": self.compressed_path,
            "dump_json_atomic": self.dump_json_atomic,
            "merged_receipt": merged_receipt,
        }


def update(study, series, *, telemetry=None, objects=None, tag=None):
    return {
        "study_uid": study,
        "series_uids": [series],
        "records": [{"study_uid": study, "series_uid": series, "tag": tag}],
        "unread": {},
        "telemetry": telemetry,
        "objects": objects,
    }


def batch(path, codec):
    return ReceiptBatch(path, REQUEST, **codec.kwargs())


def test_many_completed_updates_encode_each_update_and_aggregate_once(tmp_path):
    codec = JsonCodec()
    target = tmp_path / "interiors"
    receipt = batch(target, codec)
    updates = [
        update("A", "a1", telemetry={"run": 1}, objects={"parts": [1]}, tag="a1"),
        update("B", "b1", telemetry={"run": 2}, objects={"parts": [2]}, tag="b1"),
        update("A", "a2", telemetry=None, objects=None, tag="a2"),
        update("C", "c1", telemetry={"run": 4}, objects={"parts": [4]}, tag="c1"),
    ]
    expected = None
    for item in updates:
        receipt.add(**item)
        expected = merged_receipt(
            expected,
            REQUEST,
            item["study_uid"],
            item["series_uids"],
            item["records"],
            item["unread"],
            item["telemetry"],
            item["objects"],
        )

    stage_writes = [p for p in codec.dumps if ".receipt-pending" in str(p)]
    aggregate_writes_before_finalize = [
        p for p in codec.dumps if p.name == "receipt.json"
    ]
    assert len(stage_writes) == len(updates)
    assert aggregate_writes_before_finalize == []
    receipt.finalize()

    assert json.loads((target / "receipt.json").read_text()) == expected
    assert len([p for p in codec.dumps if p.name == "receipt.json"]) == 1
    assert not (target / ".receipt-pending").exists()
    assert expected is not None
    assert expected["records"] == [
        updates[1]["records"][0],
        updates[2]["records"][0],
        updates[3]["records"][0],
    ]
    assert expected["telemetry"] == {"B": {"run": 2}, "C": {"run": 4}}
    assert expected["objects"] == {"B": {"parts": [2]}, "C": {"parts": [4]}}


def test_request_mismatch_refuses_update_without_staging(tmp_path):
    codec = JsonCodec()
    target = tmp_path / "run"
    old = merged_receipt(None, REQUEST, "A", ["a"], [{"study_uid": "A"}], {}, None)
    (target / "receipt.json").parent.mkdir(parents=True)
    (target / "receipt.json").write_text(json.dumps(old))
    other = ReceiptBatch(target, {"profile": "other"}, **codec.kwargs())
    with pytest.raises(ValueError, match="receipt_request_differs"):
        other.add("B", ["b"], [{"study_uid": "B"}], {}, None)
    assert not (target / ".receipt-pending").exists()


def test_failed_final_publish_preserves_published_receipt_and_pending_for_recovery(
    tmp_path,
):
    codec = JsonCodec()
    target = tmp_path / "run"
    old = merged_receipt(
        None, REQUEST, "A", ["a"], [{"study_uid": "A", "v": 0}], {}, None
    )
    target.mkdir()
    published = target / "receipt.json"
    original = json.dumps(old)
    published.write_text(original)
    pending = batch(target, codec)
    item = update("B", "b", telemetry={"ok": True}, objects={"x": 1}, tag="new")
    pending.add(**item)

    codec.fail_final = True
    with pytest.raises(OSError, match="final publish failed"):
        pending.finalize()
    assert published.read_text() == original
    pending_files = list((target / ".receipt-pending").glob("*.json.xz"))
    assert len(pending_files) == 1

    codec.fail_final = False
    recovered = batch(target, codec)
    later = update("C", "c", telemetry=None, objects=None, tag="after-restart")
    recovered.add(**later)
    recovered.finalize()
    expected = merged_receipt(
        old,
        REQUEST,
        item["study_uid"],
        item["series_uids"],
        item["records"],
        item["unread"],
        item["telemetry"],
        item["objects"],
    )
    expected = merged_receipt(
        expected,
        REQUEST,
        later["study_uid"],
        later["series_uids"],
        later["records"],
        later["unread"],
        later["telemetry"],
        later["objects"],
    )
    assert json.loads(published.read_text()) == expected
    assert not (target / ".receipt-pending").exists()


def test_completed_updates_finalize_when_a_later_study_raises(tmp_path):
    codec = JsonCodec()
    target = tmp_path / "run"
    from knee.receipt_batch import ReceiptBatches

    batches = ReceiptBatches(
        target,
        tmp_path / "main",
        REQUEST,
        **codec.kwargs(),
    )
    first = update("A", "a", telemetry={"done": True}, objects=None, tag="complete")
    batches.interiors.add(**first)
    original = RuntimeError("later study failed")

    batches.finalize_after_failure(original)

    assert (
        json.loads((target / "receipt.json").read_text())["records"] == first["records"]
    )
    assert not (target / ".receipt-pending").exists()
    assert str(original) == "later study failed"


def test_two_receipts_stage_complete_study_metadata_separately(tmp_path):
    from knee.receipt_batch import ReceiptBatches

    codec = JsonCodec()
    batches = ReceiptBatches(
        tmp_path / "interiors",
        tmp_path / "main",
        REQUEST,
        **codec.kwargs(),
    )
    result = {
        "study_uid": "A",
        "series_uids": ["a1", "a2"],
        "records": [{"study_uid": "A", "series_uid": "a1"}],
        "unread": {"a2": "unread"},
        "telemetry": {"computed_once": {"x": 1}},
        "objects": {"part": {"native_series": ["a1"]}},
        "main_keys": ["a1"],
        "main_records": [{"study_uid": "A", "series_uid": "a1", "main": True}],
        "main_unread": {},
    }
    batches.add_study(result)
    batches.finalize()

    interior = json.loads((tmp_path / "interiors" / "receipt.json").read_text())
    main = json.loads((tmp_path / "main" / "receipt.json").read_text())
    assert interior["records"] == result["records"]
    assert interior["unread"] == result["unread"]
    assert interior["telemetry"] == {"A": result["telemetry"]}
    assert interior["objects"] == {"A": result["objects"]}
    assert main["records"] == result["main_records"]
    assert main["telemetry"] == {}
    assert "objects" not in main
    assert len([p for p in codec.dumps if p.name == "receipt.json"]) == 2


def test_corrupt_or_incompatible_pending_is_preserved_and_refused(tmp_path):
    codec = JsonCodec()
    target = tmp_path / "run"
    pending_dir = target / ".receipt-pending"
    pending_dir.mkdir(parents=True)
    corrupted = pending_dir / "00000000000000000000.json.xz"
    corrupted.write_text(json.dumps({"schema": "wrong"}))
    with pytest.raises(ValueError, match="receipt_pending_incompatible"):
        batch(target, codec)
    assert corrupted.exists()


def test_actual_json_store_reads_xz_receipts_and_atomically_publishes_xz(tmp_path):
    from knee.json_store import compressed_path, dump_json_atomic, load_json

    target = tmp_path / "run"
    target.mkdir()
    initial = merged_receipt(None, REQUEST, "A", ["a"], [{"study_uid": "A"}], {}, None)
    legacy = target / "receipt.json"
    legacy.write_text(json.dumps(initial))
    candidate = ReceiptBatch(
        target,
        REQUEST,
        load_json=load_json,
        compressed_path=compressed_path,
        dump_json_atomic=dump_json_atomic,
        merged_receipt=merged_receipt,
    )
    candidate.add("B", ["b"], [{"study_uid": "B"}], {}, None)
    candidate.finalize()

    compressed = target / "receipt.json.xz"
    assert compressed.exists()
    assert not legacy.exists()
    assert load_json(legacy)["records"] == [
        {"study_uid": "A"},
        {"study_uid": "B"},
    ]
    assert not (target / ".receipt-pending").exists()


def test_empty_batch_does_not_rewrite_published_receipt(tmp_path):
    codec = JsonCodec()
    target = tmp_path / "run"
    target.mkdir()
    published = target / "receipt.json"
    published.write_text('{"kept":true}')
    (target / ".receipt-pending").mkdir()
    candidate = batch(target, codec)
    candidate.finalize()
    assert published.read_text() == '{"kept":true}'
    assert not (target / ".receipt-pending").exists()
    assert codec.dumps == []


def test_real_main_stages_and_publishes_only_after_serial_no_draw_loop(
    tmp_path, monkeypatch, capsys
):
    script = CANDIDATE / "scripts" / "run_interiors.py"
    spec = importlib.util.spec_from_file_location("candidate_main_batch", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    class RuntimeCodec(JsonCodec):
        pass

    codec = RuntimeCodec()
    json_store = SimpleNamespace(
        load_json=codec.load_json,
        compressed_path=codec.compressed_path,
        dump_json_atomic=codec.dump_json_atomic,
    )
    monkeypatch.setitem(sys.modules, "knee.json_store", json_store)
    args = SimpleNamespace(
        study_uid=["A"],
        labeled=False,
        split=None,
        encode_objects=False,
        encoding_spec=None,
        competition_output=False,
        workers=1,
        draw=False,
        root=tmp_path,
        run=tmp_path / "interiors",
        main_run=tmp_path / "main",
        out=tmp_path / "pictures",
        assignments_out=tmp_path / "assignment-pictures",
        main_out=tmp_path / "main-pictures",
        diagnostic_scratch=None,
        diagnostic_readout=None,
    )
    monkeypatch.setattr(
        module.argparse.ArgumentParser, "parse_args", lambda _self: args
    )
    monkeypatch.setattr(module, "opened", lambda _root: object())
    result = {
        "study_uid": "A",
        "series_uids": ["a"],
        "records": [{"study_uid": "A", "series_uid": "a"}],
        "unread": {},
        "telemetry": {"read_by_no_stage": [], "computed_once": {}},
        "objects": {},
        "main_keys": ["a"],
        "main_records": [{"study_uid": "A", "series_uid": "a", "main": True}],
        "main_unread": {},
        "named": {},
        "study_map": {"uses": 0},
    }
    monkeypatch.setattr(module, "measure_study", lambda *args: result)

    module.main()

    assert (
        json.loads((args.run / "receipt.json").read_text())["records"]
        == result["records"]
    )
    assert (
        json.loads((args.main_run / "receipt.json").read_text())["records"]
        == result["main_records"]
    )
    assert not (args.run / ".receipt-pending").exists()
    assert not (args.main_run / ".receipt-pending").exists()
    assert len([p for p in codec.dumps if p.name == "receipt.json"]) == 2
    capsys.readouterr()


def test_real_main_publishes_completed_studies_before_propagating_later_failure(
    tmp_path, monkeypatch, capsys
):
    script = CANDIDATE / "scripts" / "run_interiors.py"
    spec = importlib.util.spec_from_file_location("candidate_main_failure", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    codec = JsonCodec()
    monkeypatch.setitem(
        sys.modules,
        "knee.json_store",
        SimpleNamespace(
            load_json=codec.load_json,
            compressed_path=codec.compressed_path,
            dump_json_atomic=codec.dump_json_atomic,
        ),
    )
    args = SimpleNamespace(
        study_uid=["A", "B"],
        labeled=False,
        split=None,
        encode_objects=False,
        encoding_spec=None,
        competition_output=False,
        workers=1,
        draw=False,
        root=tmp_path,
        run=tmp_path / "interiors",
        main_run=tmp_path / "main",
        out=tmp_path / "pictures",
        assignments_out=tmp_path / "assignment-pictures",
        main_out=tmp_path / "main-pictures",
        diagnostic_scratch=None,
        diagnostic_readout=None,
    )
    monkeypatch.setattr(
        module.argparse.ArgumentParser, "parse_args", lambda _self: args
    )
    monkeypatch.setattr(module, "opened", lambda _root: object())
    completed = {
        "study_uid": "A",
        "series_uids": ["a"],
        "records": [{"study_uid": "A", "series_uid": "a"}],
        "unread": {},
        "telemetry": {"read_by_no_stage": [], "computed_once": {}},
        "objects": {},
        "main_keys": ["a"],
        "main_records": [{"study_uid": "A", "series_uid": "a", "main": True}],
        "main_unread": {},
        "named": {},
        "study_map": {"uses": 0},
    }

    def measure(_corpus, uid, *_args):
        if uid == "B":
            raise RuntimeError("second study failed")
        return completed

    monkeypatch.setattr(module, "measure_study", measure)
    with pytest.raises(RuntimeError, match="second study failed"):
        module.main()

    assert (
        json.loads((args.run / "receipt.json").read_text())["records"]
        == completed["records"]
    )
    assert (
        json.loads((args.main_run / "receipt.json").read_text())["records"]
        == completed["main_records"]
    )
    assert not (args.run / ".receipt-pending").exists()
    assert not (args.main_run / ".receipt-pending").exists()
    capsys.readouterr()


def test_real_report_keeps_draw_immediate_and_stages_no_draw(
    tmp_path, monkeypatch, capsys
):
    script = CANDIDATE / "scripts" / "run_interiors.py"
    spec = importlib.util.spec_from_file_location("candidate_run_interiors", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    result = {
        "study_uid": "A",
        "series_uids": ["a"],
        "records": [],
        "unread": {},
        "telemetry": {"read_by_no_stage": [], "computed_once": {}},
        "objects": {},
        "main_keys": [],
        "main_records": [],
        "main_unread": {},
        "named": {},
        "study_map": {"uses": 0},
    }
    args = SimpleNamespace(
        run=tmp_path / "run",
        main_run=tmp_path / "main",
        draw=False,
        out=tmp_path / "out",
        assignments_out=tmp_path / "assignments",
        main_out=tmp_path / "mainout",
        root=tmp_path,
    )
    events = []
    monkeypatch.setattr(module, "draw_study", lambda *args: [])
    batches = SimpleNamespace(
        add_study=lambda value: events.append(("staged", value["study_uid"]))
    )
    module.report(result, args, batches)
    assert events == [("staged", "A")]
    assert not (args.run / "receipt.json").exists()

    args.run.mkdir(parents=True, exist_ok=True)
    args.main_run.mkdir(parents=True, exist_ok=True)
    args.draw = True
    module.report(result, args, batches)
    assert events == [("staged", "A")]
    assert load_json(args.run / "receipt.json")["records"] == []
    assert load_json(args.main_run / "receipt.json")["records"] == []
    capsys.readouterr()
