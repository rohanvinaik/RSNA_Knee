from __future__ import annotations

from argparse import Namespace
from contextlib import contextmanager

import numpy as np
import pytest

from knee.encoding import operation, product
from scripts import run_interiors as runner


def _args(tmp_path, **overrides):
    values = {
        "root": tmp_path / "input",
        "run": tmp_path / "run",
        "main_run": tmp_path / "main",
        "encoding_run": tmp_path / "encoding",
    }
    values.update(overrides)
    return Namespace(**values)


def test_competition_output_roots_accept_missing_or_empty(tmp_path):
    args = _args(tmp_path)
    runner._validate_competition_output_roots(args)
    for path in (args.run, args.main_run, args.encoding_run):
        path.mkdir()
    runner._validate_competition_output_roots(args)


def test_competition_output_roots_reject_nonempty_before_work(tmp_path):
    args = _args(tmp_path)
    args.run.mkdir()
    (args.run / "receipt.json.xz").write_bytes(b"old")
    with pytest.raises(ValueError, match="competition_output_root_not_fresh:run"):
        runner._validate_competition_output_roots(args)


def test_competition_output_roots_reject_overlaps(tmp_path):
    args = _args(tmp_path, main_run=tmp_path / "run" / "main")
    with pytest.raises(
        ValueError, match="competition_output_paths_overlap:run:main_run"
    ):
        runner._validate_competition_output_roots(args)
    args = _args(tmp_path, encoding_run=tmp_path / "input" / "encoding")
    with pytest.raises(
        ValueError, match="competition_output_overlaps_input:encoding_run"
    ):
        runner._validate_competition_output_roots(args)


def test_competition_cli_selects_builtin_h5_and_object_retention(monkeypatch, tmp_path):
    captured = []
    monkeypatch.setattr(runner, "opened", lambda _root: object())
    monkeypatch.setattr(runner, "measure_study", lambda *_args: {"study_uid": "s"})
    monkeypatch.setattr(
        runner, "report", lambda _result, args, _batches: captured.append(args)
    )
    monkeypatch.setattr(
        __import__("sys"),
        "argv",
        [
            "run_interiors.py",
            "--study-uid",
            "s",
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
    original_validate = operation.validate_spec
    received = []

    def validate(spec):
        received.append(dict(spec))
        return original_validate(spec)

    monkeypatch.setattr(operation, "validate_spec", validate)
    runner.main()

    assert len(captured) == 1
    assert captured[0].competition_output is True
    assert captured[0].draw is False
    assert received[0]["storage"] == "h5"
    assert received[0]["retain_object_sources"] is True
    assert captured[0].encoding_prepared["retain_object_sources"] is True


def test_competition_cli_rejects_draw_and_custom_spec_before_opened(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        runner,
        "opened",
        lambda _root: pytest.fail("must reject before reading input"),
    )
    base = [
        "run_interiors.py",
        "--study-uid",
        "s",
        "--competition-output",
        "--root",
        str(tmp_path / "input"),
        "--run",
        str(tmp_path / "run"),
        "--main-run",
        str(tmp_path / "main"),
        "--encoding-run",
        str(tmp_path / "encoding"),
    ]
    import sys

    monkeypatch.setattr(sys, "argv", [*base, "--draw"])
    with pytest.raises(ValueError, match="competition_output_disallows_draw"):
        runner.main()
    monkeypatch.setattr(
        sys, "argv", [*base, "--encoding-spec", str(tmp_path / "spec.json")]
    )
    with pytest.raises(
        ValueError, match="competition_output_requires_builtin_encoding"
    ):
        runner.main()


def test_competition_report_verifies_stages_receipt_then_cleans(monkeypatch, tmp_path):
    events = []
    object_sources = {
        "schema": "knee-object-sources/v1",
        "status": "complete",
        "archive": str(tmp_path / "encoding" / "s.h5"),
        "objects": {},
    }

    def encode(*_args, **_kwargs):
        events.append("encode")
        return {
            "archive": object_sources["archive"],
            "object_sources": object_sources,
            "work": {"opened_artifacts": 2},
        }

    def verify(value, *, work):
        events.append("verify")
        assert value["object_sources"] is object_sources
        work["product_verified_arrays"] = 4
        return object_sources

    class Batch:
        def add(self, study_uid, series_uids, records, unread, telemetry, objects):
            events.append("stage")
            assert study_uid == "s"
            assert series_uids == ["series"]
            assert records == []
            assert unread == {"u": "missing", "u:part": "missing_part"}
            assert objects is object_sources

    def cleanup(*_args):
        events.append("cleanup")

    monkeypatch.setattr(operation, "encode_study", encode)
    monkeypatch.setattr(runner, "_verify_competition_product", verify)
    monkeypatch.setattr(runner, "_delete_competition_intermediates", cleanup)
    result = {
        "study_uid": "s",
        "series_uids": ["series"],
        "records": [],
        "main_records": [],
        "unread": {"u": "missing"},
        "main_unread": {"u:part": "missing_part"},
        "telemetry": {"computed_once": {}, "read_by_no_stage": []},
        "named": {},
        "objects": {},
        "study_map": {"uses": 0},
        "main_keys": ["series"],
    }
    args = Namespace(
        encoding_declaration={"retained_object_sources": True},
        encoding_prepared={"prepared": True},
        run=tmp_path / "run",
        main_run=tmp_path / "main",
        encoding_run=tmp_path / "encoding",
        competition_output=True,
        draw=False,
        out=tmp_path / "out",
        assignments_out=tmp_path / "assignments",
        main_out=tmp_path / "main-out",
        root=tmp_path / "input",
    )

    runner.report(result, args, Batch())

    assert events == ["encode", "verify", "stage", "cleanup"]
    assert result["telemetry"]["encoding"] == {
        "opened_artifacts": 2,
        "product_verified_arrays": 4,
    }


def test_competition_report_keeps_sources_when_product_verification_fails(
    monkeypatch, tmp_path
):
    events = []
    monkeypatch.setattr(
        operation,
        "encode_study",
        lambda *_args, **_kwargs: (
            events.append("encode")
            or {"archive": "study.h5", "object_sources": {}, "work": {}}
        ),
    )

    def verify(_value, **_kwargs):
        events.append("verify")
        raise ValueError("product verification failed")

    monkeypatch.setattr(runner, "_verify_competition_product", verify)
    monkeypatch.setattr(
        runner,
        "_delete_competition_intermediates",
        lambda *_args: events.append("cleanup"),
    )
    result = {
        "study_uid": "s",
        "series_uids": [],
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
    args = Namespace(
        encoding_declaration={},
        encoding_prepared={},
        run=tmp_path / "run",
        main_run=tmp_path / "main",
        encoding_run=tmp_path / "encoding",
        competition_output=True,
        draw=False,
        out=tmp_path / "out",
        assignments_out=tmp_path / "assignments",
        main_out=tmp_path / "main-out",
        root=tmp_path / "input",
    )

    with pytest.raises(ValueError, match="product verification failed"):
        runner.report(result, args, object())
    assert events == ["encode", "verify"]


def test_owned_intermediate_paths_are_exact_and_refuse_escape(tmp_path):
    run = tmp_path / "run"
    main = tmp_path / "main"
    own = run / "s" / "series.npz.xz"
    map_path = run / "s" / "study-map.json.xz"
    part = main / "s" / "main.npz.xz"
    unrelated = run / "old" / "old.npz.xz"
    result = {
        "records": [
            {
                "artifact": "s/series.npz.xz",
                "study_map": {"file": "s/study-map.json.xz"},
            }
        ],
        "main_records": [{"artifact": "s/main.npz.xz"}],
    }
    assert set(runner._competition_owned_intermediates(result, run, main)) == {
        own.resolve(),
        map_path.resolve(),
        part.resolve(),
    }
    result["records"][0]["artifact"] = "../outside.npz.xz"
    with pytest.raises(ValueError, match="competition_intermediate_path_unsafe"):
        runner._competition_owned_intermediates(result, run, main)
    assert not unrelated.exists()


def test_competition_product_verifier_checks_nested_support_and_companion_arrays(
    monkeypatch, tmp_path
):
    archive = tmp_path / "study.h5"
    archive.write_bytes(b"h5")
    descriptor = {
        "archive": str(archive),
        "name": "object_support_0",
        "digest": "sha256:one",
        "dtype": "|u1",
        "shape": [2],
    }
    companion = {
        "archive": str(archive),
        "name": "companion_0",
        "digest": "sha256:two",
        "dtype": "<f4",
        "shape": [1],
    }
    metadata = {
        "schema": "knee-object-sources/v1",
        "status": "complete",
        "archive": str(archive),
        "array_count": 2,
        "objects": {
            "femur": {
                "status": "reading",
                "observations": [
                    {
                        "observation": {"support": "a1_objects"},
                        "source_address": {"root_name": "run"},
                        "support": {
                            "role": "support",
                            "source": {},
                            "active": descriptor,
                        },
                        "companions": [
                            {"role": "light", "source": {}, "active": companion}
                        ],
                    }
                ],
                "associated_field_references": [
                    {"path": "marrow", "active": companion}
                ],
                "unresolved": [],
            }
        },
    }
    verified = []
    manifest = {
        "object_sources": metadata,
        "encoded_arrays": {
            name: {key: desc[key] for key in ("digest", "dtype", "shape")}
            for name, desc in (
                (descriptor["name"], descriptor),
                (companion["name"], companion),
                (
                    "unlinked_encoding_array",
                    {
                        "digest": "sha256:three",
                        "dtype": "|u1",
                        "shape": [1],
                    },
                ),
            )
        },
    }

    class FakeProduct:
        storage = "h5"

        def __init__(self):
            self.manifest = manifest
            self.arrays = self

        def __getitem__(self, name):
            verified.append(name)
            return {
                "object_support_0": np.zeros((2,), dtype=np.uint8),
                "companion_0": np.zeros((1,), dtype=np.float32),
                "unlinked_encoding_array": np.zeros((1,), dtype=np.uint8),
            }[name]

    @contextmanager
    def open_fake(_path):
        yield FakeProduct()

    monkeypatch.setattr(product, "open_product", open_fake)
    encoded = {"archive": str(archive), "object_sources": metadata}
    work = {}
    assert runner._verify_competition_product(encoded, work=work) == metadata
    assert verified == [
        "object_support_0",
        "companion_0",
        "unlinked_encoding_array",
    ]
    assert work["product_verified_arrays"] == 3
    assert work["product_verified_bytes"] == 7
    assert work["product_verification_seconds"] >= 0

    broken = {**companion, "name": "associated_0", "digest": "sha256:wrong"}
    metadata["objects"]["femur"]["associated_field_references"] = [
        {"path": "marrow", "active": broken}
    ]
    metadata["array_count"] = 3
    with pytest.raises(
        ValueError, match="competition_object_array_manifest_mismatch:associated_0"
    ):
        runner._verify_competition_product(encoded)

    metadata["objects"]["femur"]["observations"][0]["support"] = {
        "role": "support",
        "source": {},
    }
    with pytest.raises(
        ValueError, match="competition_object_support_active_missing:femur"
    ):
        runner._verify_competition_product(encoded)


def test_competition_product_verifier_rejects_unreferenced_emitted_arrays(
    monkeypatch, tmp_path
):
    archive = tmp_path / "study.h5"
    archive.write_bytes(b"h5")
    metadata = {
        "schema": "knee-object-sources/v1",
        "status": "complete",
        "archive": str(archive),
        "array_count": 1,
        "objects": {},
    }
    monkeypatch.setattr(
        product,
        "open_product",
        lambda _path: pytest.fail("array-count mismatch must fail before open"),
    )
    with pytest.raises(ValueError, match="competition_object_array_count_mismatch"):
        runner._verify_competition_product(
            {"archive": str(archive), "object_sources": metadata}
        )


def test_competition_cleanup_validates_all_files_before_unlink(tmp_path):
    run = tmp_path / "run"
    main = tmp_path / "main"
    first = run / "study" / "first.npz.xz"
    later = main / "study" / "directory.npz.xz"
    first.parent.mkdir(parents=True)
    first.write_bytes(b"source")
    later.mkdir(parents=True)
    result = {
        "records": [{"artifact": "study/first.npz.xz"}],
        "main_records": [{"artifact": "study/directory.npz.xz"}],
    }
    with pytest.raises(ValueError, match="competition_intermediate_not_file"):
        runner._delete_competition_intermediates(result, run, main)
    assert first.read_bytes() == b"source"


def test_object_source_retention_spec_is_explicit_and_h5_only():
    def small_spec():
        return {
            "version": "retention-test-v1",
            "banks": [
                {
                    "name": "signal",
                    "facet": "test signal",
                    "metrics": [{"name": "value", "kind": "digit"}],
                }
            ],
            "profiles": [
                {
                    "object": "femur",
                    "provenance": "native",
                    "kind": "resolved",
                    "support": "a1_objects",
                    "readings": [
                        {
                            "bank": "signal",
                            "metric": "value",
                            "value": "support",
                            "available": "available",
                        }
                    ],
                }
            ],
        }

    ordinary = operation.validate_spec(small_spec())
    assert ordinary["retain_object_sources"] is False
    retained = small_spec()
    retained["storage"] = "h5"
    retained["retain_object_sources"] = True
    prepared = operation.validate_spec(retained)
    assert prepared["retain_object_sources"] is True
    assert prepared["spec"]["retain_object_sources"] is True
    malformed = small_spec()
    malformed["retain_object_sources"] = 1
    with pytest.raises(TypeError, match="retain_object_sources_must_be_bool"):
        operation.validate_spec(malformed)
    npz = small_spec()
    npz["retain_object_sources"] = True
    with pytest.raises(ValueError, match="object_sources_require_h5_storage"):
        operation.validate_spec(npz)
