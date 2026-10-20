from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import numpy as np

from knee.encoding import mri_spec, operation
from scripts import run_interiors as runner


def _object_sources(archive: Path) -> dict:
    return {
        "schema": "knee-object-sources/v1",
        "status": "complete",
        "archive": str(archive),
        "array_count": 0,
        "objects": {},
    }


def _study_result(uid: str) -> dict:
    return {
        "study_uid": uid,
        "series_uids": [f"series-{uid}"],
        "records": [],
        "main_records": [],
        "unread": {},
        "main_unread": {},
        "telemetry": {"computed_once": {}, "read_by_no_stage": []},
        "named": {},
        "objects": {},
        "study_map": {"uses": 0},
        "main_keys": [],
    }


def _contains_array(value: object) -> bool:
    if isinstance(value, np.ndarray):
        return True
    if isinstance(value, dict):
        return any(
            _contains_array(key) or _contains_array(item) for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_array(item) for item in value)
    return False


def test_two_studies_share_worker_preparation_and_parent_does_no_duplicate_work(
    monkeypatch, tmp_path
):
    encoding_dir = tmp_path / "encoding"
    encoding_dir.mkdir()
    source_spec = mri_spec.make_mri_spec()
    source_spec["storage"] = "h5"
    source_spec["retain_object_sources"] = True

    validations = []
    real_validate = operation.validate_spec

    def validate(spec):
        validations.append(spec)
        return real_validate(spec)

    monkeypatch.setattr(operation, "validate_spec", validate)
    runner._initialize_competition_encoder(source_spec, encoding_dir)
    assert runner._COMPETITION_ENCODER is not None
    prepared = runner._COMPETITION_ENCODER["prepared"]

    measured = []
    encoded = []
    verified = []

    def measure(_root, uid, *_args):
        measured.append(uid)
        return _study_result(uid)

    def encode(result, run_dir, main_run, spec, output, *, prepared=None):
        uid = result["study_uid"]
        encoded.append(uid)
        assert runner._COMPETITION_ENCODER is not None
        assert prepared is runner._COMPETITION_ENCODER["prepared"]
        assert spec is prepared["spec"]
        assert run_dir == tmp_path / "run"
        assert main_run == tmp_path / "main"
        assert output == encoding_dir / f"{uid}.json.xz"
        archive = encoding_dir / f"{uid}.h5"
        archive.write_bytes(f"product-{uid}".encode())
        sources = _object_sources(archive)
        return {
            "archive": str(archive),
            "manifest": str(archive),
            "work": {"opened_artifacts": 1},
            "object_sources": sources,
        }

    def verify(value, *, work):
        uid = Path(value["archive"]).stem
        verified.append(uid)
        work.update(
            product_verified_arrays=1,
            product_verified_bytes=9,
            product_verification_seconds=0.125,
        )
        return value["object_sources"]

    monkeypatch.setattr(runner, "measure_study_at", measure)
    monkeypatch.setattr(operation, "encode_study", encode)
    monkeypatch.setattr(runner, "_verify_competition_product", verify)

    worker_results = [
        runner._measure_and_encode_competition_at(
            tmp_path / "input", uid, tmp_path / "run", tmp_path / "main", False
        )
        for uid in ("study-a", "study-b")
    ]

    assert validations == [source_spec]
    assert measured == encoded == verified == ["study-a", "study-b"]
    assert all(not _contains_array(result) for result in worker_results)

    args = Namespace(
        encoding_declaration={"version": "test"},
        encoding_prepared=prepared,
        encoding_run=encoding_dir,
        competition_output=True,
        competition_worker_encoding=True,
        draw=False,
        run=tmp_path / "run",
        main_run=tmp_path / "main",
    )
    events = []

    class Batch:
        def add(self, uid, series_uids, records, unread, telemetry, objects):
            events.append(("stage", uid))
            assert series_uids == [f"series-{uid}"]
            assert records == []
            assert telemetry["encoding"]["product_verified_arrays"] == 1
            assert objects["status"] == "complete"

    def cleanup(result, run_dir, main_run):
        events.append(("cleanup", result["study_uid"]))
        assert run_dir == args.run
        assert main_run == args.main_run

    monkeypatch.setattr(runner, "_delete_competition_intermediates", cleanup)
    for result in worker_results:
        runner.report(result, args, Batch())

    assert events == [
        ("stage", "study-a"),
        ("cleanup", "study-a"),
        ("stage", "study-b"),
        ("cleanup", "study-b"),
    ]
    # Parent report consumed the verified envelopes and did not repeat worker work.
    assert encoded == verified == ["study-a", "study-b"]


def test_invalid_worker_completion_preserves_archive_before_parent_actions(
    monkeypatch, tmp_path
):
    archive = tmp_path / "encoding" / "study.h5"
    archive.parent.mkdir(parents=True)
    archive.write_bytes(b"retained-until-valid-handoff")
    result = _study_result("study")
    result["competition_encoding"] = {
        "schema": "verified_competition_encoding/v1",
        "study_uid": "study",
        "base_spec_sha256": "spec-hash",
        "archive": str(archive),
        "manifest": str(archive),
        "status": "complete",
        "work": {
            "product_verified_arrays": 0,
            "product_verified_bytes": 0,
            "product_verification_seconds": 0.0,
        },
        "object_sources": {
            "schema": "knee-object-sources/v1",
            "status": "partial",
            "archive": str(archive),
        },
    }
    args = Namespace(
        encoding_declaration={"version": "test"},
        encoding_prepared={"spec_sha256": "spec-hash"},
        encoding_run=archive.parent,
        competition_output=True,
        competition_worker_encoding=True,
        draw=False,
        run=tmp_path / "run",
        main_run=tmp_path / "main",
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

    try:
        runner.report(result, args, Batch())
    except ValueError as error:
        assert str(error) == "competition_worker_object_sources_incomplete"
    else:
        raise AssertionError("partial object-source closure must be refused")

    assert events == []
    assert archive.read_bytes() == b"retained-until-valid-handoff"
