"""Intent at the real production command boundary, before integration."""

from __future__ import annotations

import sys

import pytest

from knee.diagnosis import pipeline
from scripts import run_interiors as runner


@pytest.mark.parametrize(
    "mode,products,inputs,memory,labels,expected",
    [
        (None, False, False, False, False, "disabled"),
        ("teach", True, False, True, True, "teach"),
        ("infer", False, True, True, False, "infer"),
        ("capacity", True, False, True, True, "capacity"),
        ("invented", True, False, True, True, "invalid_mode"),
        ("infer", True, True, True, False, "ambiguous_source"),
        ("infer", False, False, True, False, "missing_source"),
        ("infer", True, False, False, False, "missing_memory"),
        ("teach", True, False, True, False, "missing_labels"),
        ("capacity", True, False, True, False, "missing_labels"),
    ],
)
def test_operation_has_distinct_named_remedies(
    mode, products, inputs, memory, labels, expected
):
    assert (
        pipeline.diagnostic_action(mode, products, inputs, memory, labels) == expected
    )


@pytest.mark.parametrize("source", ["--diagnostic-products", "--diagnostic-inputs"])
def test_diagnostic_command_never_opens_or_measures_full_study(
    monkeypatch, tmp_path, capsys, source
):
    calls = []
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_interiors.py",
            source,
            str(tmp_path / "source"),
            "--diagnostic-mode",
            "infer",
            "--diagnostic-memory",
            str(tmp_path / "memory"),
            "--diagnostic-output",
            str(tmp_path / "out"),
        ],
    )
    monkeypatch.setattr(runner, "opened", lambda *_: pytest.fail("no full-study load"))
    monkeypatch.setattr(
        runner, "measure_study", lambda *_: pytest.fail("no full measurement")
    )

    def dispatch(args, *, study_source, source_mode, probability_readout):
        assert study_source is None
        assert source_mode is None
        assert probability_readout is None
        calls.append(args)
        return {"action": "infer"}

    monkeypatch.setattr(pipeline, "run_diagnostic_cli", dispatch)
    runner.main()
    assert len(calls) == 1
    assert '"action": "infer"' in capsys.readouterr().out


def test_diagnostic_source_is_exclusive_with_anatomy_selection(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_interiors.py",
            "--study-uid",
            "study",
            "--diagnostic-products",
            "products",
        ],
    )
    monkeypatch.setattr(
        runner, "opened", lambda *_: pytest.fail("no source on invalid args")
    )
    with pytest.raises(SystemExit) as error:
        runner.main()
    assert error.value.code == 2


@pytest.mark.parametrize(
    "flags", [["--draw"], ["--encode-objects"], ["--competition-output"]]
)
def test_diagnostic_mode_refuses_accidental_anatomical_work(monkeypatch, flags):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_interiors.py",
            "--diagnostic-products",
            "products",
            "--diagnostic-mode",
            "infer",
            *flags,
        ],
    )
    monkeypatch.setattr(runner, "opened", lambda *_: pytest.fail("no full-study load"))
    monkeypatch.setattr(
        pipeline, "run_diagnostic_cli", lambda *_: pytest.fail("reject first")
    )
    with pytest.raises(ValueError, match="diagnostic_conflicting_anatomy_options"):
        runner.main()


@pytest.mark.parametrize("uid", ["../escape", "a/b", "a\\b", ".", "..", "", "a\0b"])
def test_source_identity_cannot_escape_output_directory(uid):
    with pytest.raises(
        pipeline.DiagnosticRunError, match="diagnostic_invalid_study_uid"
    ):
        pipeline._safe_uid(uid)


def test_explicit_question_banks_are_configuration_not_label_fitting(tmp_path):
    import json

    path = tmp_path / "questions.json"
    path.write_text(
        json.dumps(
            {
                "schema": "knee.diagnostic-questions/v1",
                "questions": [
                    {
                        "question_id": "ACL",
                        "objects": ["acl"],
                        "banks": ["object/acl/raw"],
                        "context_keys": ["acquisition"],
                    }
                ],
            }
        )
    )
    questions = pipeline._questions(path)
    assert len(questions) == 12
    acl = next(q for q in questions if q.question_id == "ACL")
    assert acl.subject == "diagnosis/ACL"
    assert acl.objects == ("acl",)
    assert acl.banks == ("object/acl/raw",)
    assert acl.bank_prefixes == ()


def test_question_declaration_cannot_introduce_an_unknown_diagnosis(tmp_path):
    import json

    path = tmp_path / "questions.json"
    path.write_text(
        json.dumps(
            {
                "schema": "knee.diagnostic-questions/v1",
                "questions": [
                    {
                        "question_id": "made up",
                        "objects": ["acl"],
                        "banks": ["object/acl/raw"],
                    }
                ],
            }
        )
    )
    with pytest.raises(
        pipeline.DiagnosticRunError, match="diagnostic_question_unknown"
    ):
        pipeline._questions(path)
