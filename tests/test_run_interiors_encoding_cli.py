from __future__ import annotations

import json
import sys
from types import SimpleNamespace

import pytest

from knee.encoding import mri_spec, operation
from scripts import run_interiors as runner


def _stub_study(monkeypatch, captured):
    monkeypatch.setattr(runner, "opened", lambda _root: object())
    monkeypatch.setattr(runner, "measure_study", lambda *_args: {"study_uid": "study"})
    monkeypatch.setattr(
        runner,
        "report",
        lambda _result, args, _batches: captured.append(args),
    )


def test_encoding_mode_has_named_cli_states_including_invalid_flags():
    assert runner._encoding_mode(False, False) == "disabled"
    assert runner._encoding_mode(True, False) == "built_in"
    assert runner._encoding_mode(False, True) == "explicit"
    assert runner._encoding_mode(True, True) == "conflict"
    assert runner._encoding_mode("yes", False) == "invalid_mode_flags"


def test_default_cli_does_not_prepare_encoding(monkeypatch, tmp_path):
    captured = []
    _stub_study(monkeypatch, captured)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_interiors.py",
            "--study-uid",
            "study",
            "--draw",
            "--encoding-run",
            str(tmp_path),
        ],
    )
    monkeypatch.setattr(
        operation,
        "validate_spec",
        lambda _spec: pytest.fail("encoding must remain opt-in"),
    )
    monkeypatch.setattr(
        mri_spec,
        "make_mri_spec",
        lambda: pytest.fail("factory must remain opt-in"),
    )

    runner.main()

    assert len(captured) == 1
    assert captured[0].encode_objects is False
    assert captured[0].encoding_spec is None
    assert not hasattr(captured[0], "encoding_prepared")
    assert not hasattr(captured[0], "encoding_declaration")


def test_factory_option_prepares_once_and_sets_shared_report_inputs(
    monkeypatch,
):
    captured = []
    _stub_study(monkeypatch, captured)
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_interiors.py", "--study-uid", "study", "--draw", "--encode-objects"],
    )
    factory_calls = []
    prepare_calls = []
    factory = mri_spec.make_mri_spec
    validator = operation.validate_spec

    def make_spec(**options):
        factory_calls.append(options)
        return factory(**options)

    def validate(spec):
        prepare_calls.append(spec)
        return validator(spec)

    monkeypatch.setattr(mri_spec, "make_mri_spec", make_spec)
    monkeypatch.setattr(operation, "validate_spec", validate)

    runner.main()

    assert len(factory_calls) == 1
    assert factory_calls == [
        {"retained_ordinary_profiles": True, "include_coarse": True}
    ]
    assert len(prepare_calls) == 1
    assert len(captured) == 1
    args = captured[0]
    assert args.encoding_prepared["storage"] == "h5"
    assert len(args.encoding_prepared["layout"].banks) == 11
    assert any(
        profile.get("support_layout", {}).get("family") == "native_coarse_blocks"
        for profile in args.encoding_prepared["profiles"]
    )
    assert args.encoding_declaration is args.encoding_prepared["spec"]


def test_explicit_spec_remains_compatible_and_uses_same_preparation_path(
    monkeypatch, tmp_path
):
    captured = []
    _stub_study(monkeypatch, captured)
    spec = mri_spec.make_mri_spec(view=mri_spec.BASE_SLICE_VIEWS[0])
    path = tmp_path / "explicit.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_interiors.py",
            "--study-uid",
            "study",
            "--draw",
            "--encoding-spec",
            str(path),
        ],
    )
    prepare_calls = []
    validator = operation.validate_spec

    def validate(value):
        prepare_calls.append(value)
        return validator(value)

    monkeypatch.setattr(operation, "validate_spec", validate)
    monkeypatch.setattr(
        mri_spec,
        "make_mri_spec",
        lambda: pytest.fail("explicit declaration must not select the factory"),
    )

    runner.main()

    assert len(prepare_calls) == 1
    assert len(captured) == 1
    assert captured[0].encoding_prepared["spec"]["version"] == spec["version"]
    assert captured[0].encoding_declaration is captured[0].encoding_prepared["spec"]


def test_encoding_options_are_mutually_exclusive_before_study_open(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_interiors.py",
            "--study-uid",
            "study",
            "--encoding-spec",
            "spec.json",
            "--encode-objects",
        ],
    )
    monkeypatch.setattr(
        runner,
        "opened",
        lambda _root: pytest.fail("argument conflict must exit before opening studies"),
    )

    with pytest.raises(SystemExit) as error:
        runner.main()

    assert error.value.code == 2


def test_report_forwards_the_prepared_factory_value_to_existing_consumer(
    monkeypatch, tmp_path
):
    prepared = {"prepared": True}
    declaration = {"declaration": True}
    called = []
    monkeypatch.setattr(
        operation,
        "encode_study",
        lambda *args, **kwargs: called.append((args, kwargs)) or {"work": {"made": 1}},
    )
    monkeypatch.setattr(runner, "keep", lambda *_args: None)
    result = {
        "study_uid": "study",
        "named": {},
        "telemetry": {"read_by_no_stage": [], "computed_once": {}},
        "objects": {},
        "study_map": {"uses": 0},
    }
    args = SimpleNamespace(
        encoding_declaration=declaration,
        encoding_prepared=prepared,
        run=tmp_path / "run",
        main_run=tmp_path / "main",
        encoding_run=tmp_path / "encoding",
        draw=False,
        out=tmp_path / "out",
        assignments_out=tmp_path / "assignments",
        main_out=tmp_path / "main-out",
        root=tmp_path,
    )

    runner.report(result, args)

    assert len(called) == 1
    assert called[0][0][3] is declaration
    assert called[0][1]["prepared"] is prepared


def test_report_encodes_retained_addresses_before_receipt_publication(
    monkeypatch, tmp_path
):
    events = []
    retained = {
        "artifact": "source.npz.xz",
        "support": "native_mask",
        "row_codes": "encoding/object/metric",
    }

    def encode(result, *_args, **_kwargs):
        events.append("encode")
        assert result["objects"]["object"]["retained"] is retained
        result["objects"]["object"]["encoding"] = {
            "manifest": "study.h5",
            "object_profile": "object-profile-1",
        }
        return {"work": {"source_arrays_verified": 1}}

    def publish(result, *_args):
        events.append("publish")
        assert result["telemetry"]["encoding"]["source_arrays_verified"] == 1
        assert result["objects"]["object"]["encoding"]["manifest"] == "study.h5"
        assert result["objects"]["object"]["retained"] is retained

    monkeypatch.setattr(operation, "encode_study", encode)
    monkeypatch.setattr(runner, "keep", publish)
    result = {
        "study_uid": "study",
        "named": {},
        "telemetry": {"read_by_no_stage": [], "computed_once": {}},
        "objects": {
            "object": {
                "retained": retained,
                "native_series": [],
                "observations": {},
            }
        },
        "study_map": {"uses": 0},
    }
    args = SimpleNamespace(
        encoding_declaration={"spec": "prepared"},
        encoding_prepared={"layout": "shared"},
        run=tmp_path / "run",
        main_run=tmp_path / "main",
        encoding_run=tmp_path / "encoding",
        draw=False,
        out=tmp_path / "out",
        assignments_out=tmp_path / "assignments",
        main_out=tmp_path / "main-out",
        root=tmp_path,
    )

    runner.report(result, args)

    assert events == ["encode", "publish"]
