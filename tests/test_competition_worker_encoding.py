from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path

import numpy as np
import pytest

from knee import receipt_batch
from knee.encoding import mri_spec, operation
from scripts import run_interiors as runner


def _completion(uid: str, archive: Path, spec_hash: str, object_sources: dict):
    return {
        "schema": "verified_competition_encoding/v1",
        "study_uid": uid,
        "base_spec_sha256": spec_hash,
        "archive": str(archive),
        "manifest": str(archive),
        "status": "complete",
        "work": {
            "opened_artifacts": 1,
            "product_verified_arrays": 2,
            "product_verified_bytes": 32,
            "product_verification_seconds": 0.25,
        },
        "object_sources": object_sources,
    }


def _object_sources(archive: Path):
    return {
        "schema": "knee-object-sources/v1",
        "status": "complete",
        "archive": str(archive),
        "array_count": 0,
        "objects": {},
    }


def _report_args(tmp_path, *, worker=True, spec_hash="spec-hash"):
    archive = tmp_path / "encoding" / "s.h5"
    return Namespace(
        encoding_declaration={"version": "test"},
        encoding_prepared={"spec_sha256": spec_hash},
        encoding_run=tmp_path / "encoding",
        run=tmp_path / "run",
        main_run=tmp_path / "main",
        competition_output=True,
        competition_worker_encoding=worker,
        draw=False,
        out=tmp_path / "out",
        assignments_out=tmp_path / "assignments",
        main_out=tmp_path / "main-out",
        root=tmp_path / "input",
    ), archive


def _result(uid="s"):
    return {
        "study_uid": uid,
        "series_uids": ["series"],
        "records": [],
        "main_records": [],
        "unread": {"unread": "reason"},
        "main_unread": {},
        "telemetry": {"computed_once": {}, "read_by_no_stage": []},
        "named": {},
        "objects": {},
        "study_map": {"uses": 0},
        "main_keys": ["series"],
    }


def test_worker_initializer_prepares_once_and_attaches_metadata_only_completion(
    monkeypatch, tmp_path
):
    source_spec = mri_spec.make_mri_spec()
    source_spec["storage"] = "h5"
    source_spec["retain_object_sources"] = True
    calls = []
    real_validate = operation.validate_spec

    def validate(spec):
        calls.append(spec)
        return real_validate(spec)

    monkeypatch.setattr(operation, "validate_spec", validate)
    runner._initialize_competition_encoder(source_spec, tmp_path / "encoding")
    assert calls == [source_spec]
    assert runner._COMPETITION_ENCODER is not None
    prepared = runner._COMPETITION_ENCODER["prepared"]
    archive = tmp_path / "encoding" / "s.h5"
    sources = _object_sources(archive)
    encoded_calls = []
    verify_calls = []

    monkeypatch.setattr(runner, "measure_study_at", lambda *_args: _result())

    def encode(result, run_dir, main_run, spec, output, *, prepared):
        encoded_calls.append((result, run_dir, main_run, spec, output, prepared))
        assert runner._COMPETITION_ENCODER is not None
        assert prepared is runner._COMPETITION_ENCODER["prepared"]
        assert spec is prepared["spec"]
        return {
            "archive": str(archive),
            "manifest": str(archive),
            "work": {"opened_artifacts": 1},
            "object_sources": sources,
        }

    def verify(value, *, work):
        verify_calls.append(value)
        assert work == {"opened_artifacts": 1}
        work["product_verified_arrays"] = 2
        work["product_verified_bytes"] = 32
        work["product_verification_seconds"] = 0.25
        return sources

    monkeypatch.setattr(operation, "encode_study", encode)
    monkeypatch.setattr(runner, "_verify_competition_product", verify)
    result = runner._measure_and_encode_competition_at(
        tmp_path / "input", "s", tmp_path / "run", tmp_path / "main", False
    )

    assert len(calls) == 1
    assert len(encoded_calls) == len(verify_calls) == 1
    assert encoded_calls[0][4] == tmp_path / "encoding" / "s.json.xz"
    assert result["telemetry"]["encoding"]["product_verified_arrays"] == 2
    completion = result["competition_encoding"]
    assert completion["study_uid"] == "s"
    assert completion["base_spec_sha256"] == prepared["spec_sha256"]
    assert completion["object_sources"] == sources
    assert not any(isinstance(value, np.ndarray) for value in completion.values())


def test_parent_accepts_only_matching_worker_identity_and_expected_archive(tmp_path):
    args, archive = _report_args(tmp_path)
    archive.parent.mkdir(parents=True)
    archive.write_bytes(b"verified-by-worker")
    sources = _object_sources(archive)
    result = _result()
    completion = _completion("s", archive, "spec-hash", sources)
    accepted = runner._accept_competition_worker_result(result, args, completion)
    assert accepted["archive"] == str(archive.resolve())
    assert accepted["object_sources"] == sources
    assert accepted["work"]["product_verified_arrays"] == 2

    for broken, error in (
        ({**completion, "study_uid": "other"}, "competition_worker_study_uid_mismatch"),
        (
            {**completion, "base_spec_sha256": "stale"},
            "competition_worker_spec_mismatch",
        ),
        (
            {**completion, "archive": str(tmp_path / "elsewhere.h5")},
            "competition_worker_archive_mismatch",
        ),
        ({**completion, "status": "partial"}, "competition_worker_encoding_incomplete"),
    ):
        with pytest.raises(ValueError, match=error):
            runner._accept_competition_worker_result(result, args, broken)

    archive.unlink()
    with pytest.raises(FileNotFoundError, match="competition_worker_archive_missing"):
        runner._accept_competition_worker_result(result, args, completion)


def test_parallel_competition_report_stages_verified_worker_result_without_reencoding(
    monkeypatch, tmp_path
):
    events = []
    args, archive = _report_args(tmp_path)
    archive.parent.mkdir(parents=True)
    archive.write_bytes(b"verified-by-worker")
    sources = _object_sources(archive)
    result = _result()
    result["competition_encoding"] = _completion("s", archive, "spec-hash", sources)

    monkeypatch.setattr(
        operation,
        "encode_study",
        lambda *_args, **_kwargs: pytest.fail("parent must not encode again"),
    )
    monkeypatch.setattr(
        runner,
        "_verify_competition_product",
        lambda *_args, **_kwargs: pytest.fail("parent must not reread H5"),
    )

    class Batch:
        def add(self, study_uid, series_uids, records, unread, telemetry, objects):
            events.append("stage")
            assert study_uid == "s"
            assert series_uids == ["series"]
            assert records == []
            assert unread == {"unread": "reason"}
            assert telemetry["encoding"]["product_verified_arrays"] == 2
            assert objects == sources

    def cleanup(value, run_dir, main_run):
        events.append("cleanup")
        assert value is result
        assert run_dir == args.run
        assert main_run == args.main_run

    monkeypatch.setattr(runner, "_delete_competition_intermediates", cleanup)
    runner.report(result, args, Batch())
    assert events == ["stage", "cleanup"]


def test_stale_worker_result_fails_before_receipt_staging_or_cleanup(
    monkeypatch, tmp_path
):
    args, archive = _report_args(tmp_path)
    archive.parent.mkdir(parents=True)
    archive.write_bytes(b"verified-by-worker")
    result = _result()
    result["competition_encoding"] = _completion(
        "wrong", archive, "spec-hash", _object_sources(archive)
    )
    events = []

    class Batch:
        def add(self, *_args):
            events.append("stage")

    monkeypatch.setattr(
        runner,
        "_delete_competition_intermediates",
        lambda *_args: events.append("cleanup"),
    )
    with pytest.raises(ValueError, match="competition_worker_study_uid_mismatch"):
        runner.report(result, args, Batch())
    assert events == []


def test_main_initializes_competition_encoder_only_in_parallel_competition_mode(
    monkeypatch, tmp_path
):
    calls = []
    fake_workers = []

    class FakeBatch:
        def __init__(self, *_args, **_kwargs):
            pass

        def finalize(self):
            pass

        def finalize_after_failure(self, _error):
            pass

    class FakeFuture:
        def __init__(self, value):
            self.value = value

        def result(self):
            return self.value

        def cancel(self):
            return True

    class FakePool:
        def __init__(self, max_workers=None, *, initializer=None, initargs=()):
            self.max_workers = max_workers
            self.initializer = initializer
            self.initargs = initargs
            fake_workers.append(self)
            if initializer is not None:
                initializer(*initargs)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def submit(self, function, *args):
            calls.append(function.__name__)
            return FakeFuture(function(*args))

    monkeypatch.setattr(runner, "ProcessPoolExecutor", FakePool)
    monkeypatch.setattr(runner, "opened", lambda _root: object())
    monkeypatch.setattr(
        runner,
        "measure_study_at",
        lambda _root, uid, *_args: {
            "study_uid": uid,
            "telemetry": {"computed_once": {}, "read_by_no_stage": []},
            "objects": {},
        },
    )
    monkeypatch.setattr(runner, "report", lambda *_args: None)
    monkeypatch.setattr(receipt_batch, "ReceiptBatch", FakeBatch)

    real_validate = operation.validate_spec
    validations = []

    def validate(spec):
        validations.append(spec)
        return real_validate(spec)

    monkeypatch.setattr(operation, "validate_spec", validate)
    monkeypatch.setattr(
        operation,
        "encode_study",
        lambda result, _run, _main, _spec, output, **_kwargs: {
            "archive": str(output.with_name(result["study_uid"] + ".h5")),
            "manifest": str(output.with_name(result["study_uid"] + ".h5")),
            "work": {},
            "object_sources": _object_sources(
                output.with_name(result["study_uid"] + ".h5")
            ),
        },
    )

    def verify(encoded, *, work):
        work.update(
            product_verified_arrays=0,
            product_verified_bytes=0,
            product_verification_seconds=0.0,
        )
        return encoded["object_sources"]

    monkeypatch.setattr(runner, "_verify_competition_product", verify)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_interiors.py",
            "--study-uid",
            "s0",
            "s1",
            "--workers",
            "2",
            "--competition-output",
            "--root",
            str(tmp_path / "input"),
            "--run",
            str(tmp_path / "run"),
            "--main-run",
            str(tmp_path / "main"),
            "--encoding-run",
            str(tmp_path / "encoding"),
        ],
    )

    try:
        runner.main()
    finally:
        runner._COMPETITION_ENCODER = None

    assert len(fake_workers) == 1
    pool = fake_workers[0]
    assert pool.max_workers == 2
    assert pool.initializer is runner._initialize_competition_encoder
    assert isinstance(pool.initargs[0], dict)
    assert pool.initargs[1] == tmp_path / "encoding"
    assert calls == ["_measure_and_encode_competition_at"] * 2
    # Parent preflight plus one process initializer; per-study operations did not prepare.
    assert len(validations) == 2


def test_default_parallel_pool_does_not_get_encoding_initializer(monkeypatch, tmp_path):
    made = []

    class FakeFuture:
        def __init__(self, value):
            self.value = value

        def result(self):
            return self.value

        def cancel(self):
            return True

    class FakePool:
        def __init__(self, max_workers=None):
            made.append(max_workers)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def submit(self, function, *args):
            return FakeFuture(function(*args))

    monkeypatch.setattr(runner, "ProcessPoolExecutor", FakePool)
    monkeypatch.setattr(runner, "opened", lambda _root: object())
    monkeypatch.setattr(
        runner,
        "measure_study_at",
        lambda _root, uid, *_args: {"study_uid": uid},
    )
    monkeypatch.setattr(runner, "report", lambda *_args: None)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_interiors.py",
            "--study-uid",
            "s0",
            "s1",
            "--workers",
            "2",
            "--root",
            str(tmp_path / "input"),
            "--run",
            str(tmp_path / "run"),
            "--main-run",
            str(tmp_path / "main"),
        ],
    )
    runner.main()
    assert made == [2]
