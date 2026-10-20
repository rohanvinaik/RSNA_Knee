from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

import pytest

from knee import receipt_batch as receipt_module
from scripts import run_interiors as runner


def _load_runner():
    return runner


def _load_receipt_batch():
    return receipt_module


def test_duplicate_explicit_uids_fail_before_open_or_output_validation(
    monkeypatch, tmp_path
):
    runner = _load_runner()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_interiors.py",
            "--study-uid",
            "same",
            "same",
            "--competition-output",
            "--run",
            str(tmp_path / "run"),
            "--main-run",
            str(tmp_path / "main"),
            "--encoding-run",
            str(tmp_path / "encoding"),
        ],
    )
    monkeypatch.setattr(
        runner,
        "_validate_competition_output_roots",
        lambda _args: pytest.fail("duplicate UIDs must fail before output validation"),
    )
    monkeypatch.setattr(
        runner,
        "opened",
        lambda _root: pytest.fail("duplicate UIDs must fail before opening"),
    )
    with pytest.raises(ValueError, match="duplicate_study_uid"):
        runner.main()
    assert not (tmp_path / "run").exists()
    assert not (tmp_path / "main").exists()
    assert not (tmp_path / "encoding").exists()


def test_unique_explicit_uid_still_reaches_study_open(monkeypatch, tmp_path):
    runner = _load_runner()
    opened = []
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_interiors.py", "--study-uid", "one", "--draw", "--root", str(tmp_path)],
    )
    monkeypatch.setattr(runner, "opened", lambda root: opened.append(root) or object())
    monkeypatch.setattr(
        runner, "measure_study", lambda _corpus, uid, *_args: {"study_uid": uid}
    )
    monkeypatch.setattr(runner, "report", lambda *_args: None)
    runner.main()
    assert opened == [tmp_path]


def test_worker_study_uid_mismatch_stops_before_encoding(monkeypatch, tmp_path):
    runner = _load_runner()
    from knee.encoding import operation

    monkeypatch.setattr(
        runner,
        "_COMPETITION_ENCODER",
        {"prepared": {"spec": {}}, "encoding_run": tmp_path},
    )
    monkeypatch.setattr(
        runner,
        "measure_study_at",
        lambda *_args: {"study_uid": "different", "telemetry": {}},
    )
    monkeypatch.setattr(
        operation,
        "encode_study",
        lambda *_args, **_kwargs: pytest.fail(
            "encoding must not run for a mismatched UID"
        ),
    )
    with pytest.raises(ValueError, match="competition_worker_study_uid_mismatch"):
        runner._measure_and_encode_competition_at(
            tmp_path, "submitted", tmp_path / "run", tmp_path / "main", False
        )


def _completion(tmp_path: Path, array_count: object, *, verified_arrays=1):
    archive = tmp_path / "study.h5"
    archive.write_bytes(b"already-published-product")
    sources = {
        "schema": "knee-object-sources/v1",
        "status": "complete",
        "archive": str(archive.resolve()),
        "array_count": array_count,
        "objects": {},
    }
    completion = {
        "schema": "verified_competition_encoding/v1",
        "study_uid": "study",
        "base_spec_sha256": "spec-sha",
        "archive": str(archive.resolve()),
        "manifest": str(archive.resolve()),
        "status": "complete",
        "work": {
            "product_verified_arrays": verified_arrays,
            "product_verified_bytes": 0,
            "product_verification_seconds": 0.0,
        },
        "object_sources": sources,
    }
    return archive, completion


def _report_args(tmp_path: Path, *, batch):
    return Namespace(
        competition_output=True,
        competition_worker_encoding=True,
        encoding_declaration={},
        encoding_prepared={"spec_sha256": "spec-sha"},
        encoding_run=tmp_path,
        run=tmp_path / "run",
        main_run=tmp_path / "main",
        draw=False,
        out=tmp_path / "out",
        assignments_out=tmp_path / "assignments",
        main_out=tmp_path / "main-out",
        root=tmp_path,
        _batch=batch,
    )


def _report_result(completion):
    return {
        "study_uid": "study",
        "series_uids": [],
        "competition_encoding": completion,
        "named": {},
        "unread": {},
        "main_unread": {},
        "telemetry": {"encoding": {}, "read_by_no_stage": [], "computed_once": {}},
        "objects": {},
        "study_map": {"uses": 0},
    }


@pytest.mark.parametrize("array_count", [2, True, -1, "1", None])
def test_impossible_object_array_count_refuses_before_receipt_stage_or_cleanup(
    monkeypatch, tmp_path, array_count
):
    runner = _load_runner()
    _archive, completion = _completion(tmp_path, array_count, verified_arrays=1)
    staged = []
    deleted = []
    batch = SimpleNamespace(add=lambda *args: staged.append(args))
    args = _report_args(tmp_path, batch=batch)
    monkeypatch.setattr(
        runner, "_delete_competition_intermediates", lambda *args: deleted.append(args)
    )
    with pytest.raises(
        ValueError, match="competition_worker_object_array_count_invalid"
    ):
        runner.report(_report_result(completion), args, batch)
    assert staged == []
    assert deleted == []


def test_zero_object_array_count_is_valid_and_can_stage_and_cleanup(
    monkeypatch, tmp_path
):
    runner = _load_runner()
    _archive, completion = _completion(tmp_path, 0, verified_arrays=1)
    staged = []
    deleted = []
    batch = SimpleNamespace(add=lambda *args: staged.append(args))
    args = _report_args(tmp_path, batch=batch)
    monkeypatch.setattr(
        runner, "_delete_competition_intermediates", lambda *args: deleted.append(args)
    )
    runner.report(_report_result(completion), args, batch)
    assert len(staged) == 1
    assert len(deleted) == 1


def _batch_options(tmp_path: Path, *, dump):
    def load(path):
        raise FileNotFoundError(path)

    def compressed(path):
        return path.with_suffix(path.suffix + ".xz")

    def merge(receipt, request, uid, series_uids, records, unread, telemetry, objects):
        current = {} if receipt is None else dict(receipt)
        current[uid] = {
            "request": dict(request),
            "series_uids": list(series_uids),
            "records": list(records),
            "unread": dict(unread),
            "telemetry": telemetry,
            "objects": objects,
        }
        return current

    return {
        "load_json": load,
        "compressed_path": compressed,
        "dump_json_atomic": dump,
        "merged_receipt": merge,
    }


def test_receipt_batch_failure_finalizer_publishes_prior_durable_stage(
    tmp_path,
):
    ReceiptBatch = _load_receipt_batch().ReceiptBatch

    def dump(path, value, **_kwargs):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        return path

    batch = ReceiptBatch(tmp_path, {}, **_batch_options(tmp_path, dump=dump))
    batch.add("study-1", [], [], {}, None, {})
    original = RuntimeError("later worker failed")
    batch.finalize_after_failure(original)
    assert (tmp_path / "receipt.json").is_file()
    assert not (tmp_path / ".receipt-pending").exists()
    saved = json.loads((tmp_path / "receipt.json").read_text())
    assert list(saved) == ["study-1"]
    assert original.args == ("later worker failed",)


def test_competition_main_finalizes_receiptbatch_after_later_study_failure(
    monkeypatch, tmp_path
):
    runner = _load_runner()
    receipt_module = _load_receipt_batch()
    from knee.encoding import mri_spec, operation

    monkeypatch.setitem(sys.modules, "knee.receipt_batch", receipt_module)
    monkeypatch.setattr(
        runner, "_validate_competition_output_roots", lambda _args: None
    )
    monkeypatch.setattr(runner, "opened", lambda _root: object())
    monkeypatch.setattr(
        runner,
        "measure_study",
        lambda _corpus, uid, *_args: {"study_uid": uid},
    )
    monkeypatch.setattr(
        mri_spec,
        "make_mri_spec",
        lambda **_kwargs: {"version": "test"},
    )
    monkeypatch.setattr(
        operation,
        "validate_spec",
        lambda spec: {
            "storage": "h5",
            "retain_object_sources": True,
            "spec": spec,
            "spec_sha256": "spec-sha",
        },
    )
    calls = []

    def report(result, _args, batch):
        calls.append(result["study_uid"])
        if result["study_uid"] == "first":
            batch.add("first", [], [], {}, {}, {})
        else:
            raise RuntimeError("later study failed")

    monkeypatch.setattr(runner, "report", report)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_interiors.py",
            "--study-uid",
            "first",
            "second",
            "--competition-output",
            "--workers",
            "1",
            "--root",
            str(tmp_path / "data"),
            "--run",
            str(tmp_path / "run"),
            "--main-run",
            str(tmp_path / "main"),
            "--encoding-run",
            str(tmp_path / "encoding"),
        ],
    )

    with pytest.raises(RuntimeError, match="later study failed"):
        runner.main()
    assert calls == ["first", "second"]
    from knee.json_store import load_json

    receipt = load_json(tmp_path / "encoding" / "receipt.json")
    assert "first" in receipt["objects"]


def test_receipt_batch_finalization_failure_notes_original_and_keeps_pending(
    tmp_path,
):
    ReceiptBatch = _load_receipt_batch().ReceiptBatch

    def dump(path, value, **_kwargs):
        if path.name == "receipt.json":
            raise OSError("final write failed")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        return path

    batch = ReceiptBatch(tmp_path, {}, **_batch_options(tmp_path, dump=dump))
    batch.add("study-1", [], [], {}, None, {})
    pending = tuple((tmp_path / ".receipt-pending").iterdir())
    original = RuntimeError("later worker failed")
    batch.finalize_after_failure(original)
    assert original.args == ("later worker failed",)
    assert any("final write failed" in note for note in original.__notes__)
    assert pending and all(path.is_file() for path in pending)
