"""Signed report teaching checks saved procedures without becoming image evidence."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
from pathlib import Path

import pytest

import scripts.prepare_squint_training as cli
from knee.diagnosis.squint_memory_view import memory_view
from knee.diagnosis.squint_procedure_memory import (
    condition_outcome,
    experience_rows,
    retain_procedure_experiences,
)
from knee.diagnosis.squint_reports import report_sha256, validate_report_calls
from knee.study.tables import LABELS
from test_prepare_squint_training import (
    SOURCE_MEMORY_SHA,
    TEACHING_MEMORY_SHA,
    UID,
    inputs,
)

REPORT = "ACL is torn. MCL is intact. The ACL tear is uncertain."


def report_call(question="ACL", digit=1, **changes):
    sentence = "ACL is torn." if question == "ACL" else "MCL is intact."
    record = {
        "study_uid": UID,
        "question": question,
        "digit": digit,
        "assertion": "present" if digit == 1 else "absent",
        "sentence": sentence,
        "subject": f"diagnosis/{question}",
        "scope": "study_condition",
        "source": "report:official-train.csv",
        "report_sha": report_sha256(REPORT),
        "reader": "independent report reader",
    }
    return {**record, **changes}


def labels_with(*raw_calls, numeric=None):
    checked = validate_report_calls(list(raw_calls), {UID: REPORT})
    grouped = {}
    for entry in checked:
        grouped.setdefault(entry["question"], []).append(entry)
    return {
        "table_uids": {UID},
        "calls": {UID: numeric or {}},
        "report_calls": {UID: grouped},
        "source": {"path": "train.csv", "sha256": "a" * 64},
    }


def condition_record(record):
    record = copy.deepcopy(record)
    record["observations"] = [
        {
            "subject": "acl",
            "question": "ACL",
            "code": "measured",
            "request_id": "ACL/acl/zoom",
            "request_kind": "bounded_zoom",
            "request_reason": "open",
            "before_state": {"outcome": "open"},
            "after_state": {"outcome": "assigned", "reason": "observed"},
            "before_cue": {
                "schema": "knee.squint-profile/v1",
                "subject": "acl",
                "banks": {
                    'squint/v2/view=["Sagittal","FS","0"]/role=object/metric=signal/direction=si/scale=10mm': [
                        1, 0, 1
                    ]
                },
            },
        }
    ]
    return record


def call_file(path: Path, *calls):
    path.write_text(
        json.dumps({"schema": "knee.squint-report-calls/v1", "calls": calls}),
        encoding="utf-8",
    )
    return path


def export_inputs(tmp_path, monkeypatch):
    memory, run, labels, output, snapshot = inputs(tmp_path)
    study = run / "studies/study.json"
    study.write_text(json.dumps(condition_record(json.loads(study.read_text()))))
    with labels.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["StudyInstanceUID", "Report", *LABELS])
        writer.writeheader()
        writer.writerow({"StudyInstanceUID": UID, "Report": REPORT, "ACL": ""})
    monkeypatch.setattr(cli, "load_memory_snapshot", lambda _path: snapshot)
    return memory, run, labels, output


@pytest.mark.parametrize("question,digit", [("ACL", 1), ("MCL", -1)])
def test_signed_report_checks_its_question_with_exact_quote(question, digit):
    labels = labels_with(report_call(question, digit))
    result = condition_outcome(labels, UID, question, "measured")
    assert result["status"] == "checked"
    assert result["source"] == "independent_report"
    assert result["call"] == digit
    assert result["scope"] == "study_condition"
    assert result["report_calls"][0]["sentence"] == labels["report_calls"][UID][question][0]["sentence"]
    assert result["report_calls"][0]["report_sha"] == report_sha256(REPORT)


def test_opposing_report_and_numeric_label_remain_unchecked():
    result = condition_outcome(
        labels_with(report_call(), numeric={"ACL": -1}), UID, "ACL", "measured"
    )
    assert result["status"] == "unchecked"
    assert result["reason"] == "independent_call_conflict"
    assert result["official_label_call"] == -1
    assert result["report_calls"][0]["digit"] == 1


def test_matching_report_and_numeric_label_keep_both_sources():
    result = condition_outcome(
        labels_with(report_call(), numeric={"ACL": 1}), UID, "ACL", "measured"
    )
    assert result["status"] == "checked"
    assert result["source"] == "official_label_and_report"
    assert result["call"] == 1
    assert result["label_source"] and result["report_calls"]


@pytest.mark.parametrize(
    "changes",
    [
        {"digit": 0, "assertion": "not_mentioned", "sentence": ""},
        {"digit": 0, "assertion": "uncertain", "sentence": "The ACL tear is uncertain."},
        {"needs_review": True},
    ],
)
def test_unknown_or_held_report_never_erases_a_numeric_call(changes):
    result = condition_outcome(
        labels_with(report_call(**changes), numeric={"ACL": -1}),
        UID, "ACL", "measured",
    )
    assert result["status"] == "checked"
    assert result["source"] == "official_label"
    assert result["call"] == -1


@pytest.mark.parametrize(
    "changes",
    [
        {"digit": 0, "assertion": "not_mentioned", "sentence": ""},
        {"digit": 0, "assertion": "uncertain", "sentence": "The ACL tear is uncertain."},
        {"needs_review": True},
    ],
)
def test_unknown_or_held_report_cannot_check_a_blank_label(changes):
    result = condition_outcome(
        labels_with(report_call(**changes)), UID, "ACL", "measured"
    )
    assert result["status"] == "unchecked"
    assert result["reason"] == "label_blank_no_call"


def test_report_call_never_checks_an_unrun_or_other_question():
    labels = labels_with(report_call())
    result = condition_outcome(labels, UID, "ACL", "not_run")
    other = condition_outcome(labels, UID, "MCL", "measured")
    assert result["reason"] == "request_did_not_run"
    assert other["reason"] == "label_blank_no_call"


def test_opposing_report_calls_stay_a_disagreement():
    labels = labels_with(report_call(), report_call(digit=-1))
    result = condition_outcome(labels, UID, "ACL", "measured")
    assert result["status"] == "unchecked"
    assert result["reason"] == "independent_call_conflict"
    assert {entry["digit"] for entry in result["report_calls"]} == {-1, 1}


def test_real_export_reads_saved_record_and_pins_report_calls(tmp_path, monkeypatch):
    memory, run, labels, output = export_inputs(tmp_path, monkeypatch)
    report_path = call_file(tmp_path / "calls.json", report_call())
    monkeypatch.setattr(cli, "infer_study", lambda *_a, **_k: pytest.fail("new inference"))
    receipt = cli.prepare(
        memory_path=memory, expected_memory_sha256=TEACHING_MEMORY_SHA,
        run_paths=[run], labels_path=labels, output_path=output,
        report_call_paths=[report_path],
    )
    rows = [json.loads(line) for line in (output / "procedure-experiences.jsonl").read_text().splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert row["independent_outcome"]["source"] == "independent_report"
    assert row["independent_agreement"]["status"] == "matches_independent_call"
    assert row["state"]["attribution_scope"] == "single_procedure"
    assert row["source"]["memory_sha256"] == SOURCE_MEMORY_SHA
    pin = receipt["inputs"]["labels"]["report_calls"][0]
    assert pin == {"path": str(report_path.resolve()), "sha256": hashlib.sha256(report_path.read_bytes()).hexdigest()}
    assert row["independent_outcome"]["report_calls"][0]["call_document"] == pin
    assert receipt["outputs"]["checked"] == 1


def test_changed_report_document_refuses_export_resume(tmp_path, monkeypatch):
    memory, run, labels, output = export_inputs(tmp_path, monkeypatch)
    report_path = call_file(tmp_path / "calls.json", report_call())
    cli.prepare(
        memory_path=memory, expected_memory_sha256=TEACHING_MEMORY_SHA,
        run_paths=[run], labels_path=labels, output_path=output,
        report_call_paths=[report_path],
    )
    call_file(report_path, report_call(needs_review=True))
    with pytest.raises(cli.PrepareError, match="training_checkpoint_mismatch"):
        cli._training_export(
            memory_path=memory, expected_memory_sha256=TEACHING_MEMORY_SHA,
            inference_dir=run, labels_path=labels, output_path=output,
            report_call_paths=[report_path],
        )


def test_invalid_quote_cannot_enter_export(tmp_path, monkeypatch):
    memory, run, labels, output = export_inputs(tmp_path, monkeypatch)
    report_path = call_file(tmp_path / "calls.json", report_call(sentence="Invented finding."))
    with pytest.raises(cli.PrepareError, match="report_call_refused:"):
        cli.prepare(
            memory_path=memory, expected_memory_sha256=TEACHING_MEMORY_SHA,
            run_paths=[run], labels_path=labels, output_path=output,
            report_call_paths=[report_path],
        )
    assert not output.exists()


def test_call_document_changed_during_validation_is_refused(tmp_path, monkeypatch):
    memory, run, labels, output = export_inputs(tmp_path, monkeypatch)
    report_path = call_file(tmp_path / "calls.json", report_call())
    importer = cli.import_report_calls

    def changing_import(path, reports):
        results = importer(path, reports)
        call_file(path, report_call(needs_review=True))
        return results

    monkeypatch.setattr(cli, "import_report_calls", changing_import)
    with pytest.raises(cli.PrepareError, match="report_calls_changed_during_read"):
        cli.prepare(
            memory_path=memory, expected_memory_sha256=TEACHING_MEMORY_SHA,
            run_paths=[run], labels_path=labels, output_path=output,
            report_call_paths=[report_path],
        )
    assert not output.exists()


def test_report_checked_experience_keeps_whole_study_exclusion():
    from test_prepare_squint_training import record

    source = {
        "run": "saved-run", "record_file": "study.json", "record_sha256": "a" * 64,
        "memory_sha256": "b" * 64, "memory_revision": "parent",
    }
    rows = experience_rows(
        condition_record(record()), source,
        labels=labels_with(report_call()), call_index={},
    )
    child = retain_procedure_experiences({"revision": "parent", "cases": []}, rows)
    assert child["procedure_experiences"]["rows"][0]["source"]["study_uid"] == UID
    view = memory_view(child, exclude_study_uids=[UID])
    assert view["procedure_experiences"]["rows"] == []


def test_cli_repeated_report_inputs_reach_real_export(tmp_path, monkeypatch):
    memory, run, labels, output = export_inputs(tmp_path, monkeypatch)
    first = call_file(tmp_path / "acl.json", report_call())
    second = call_file(tmp_path / "mcl.json", report_call("MCL", -1))
    status = cli.main([
        "--memory", str(memory), "--memory-sha256", TEACHING_MEMORY_SHA,
        "--run", str(run), "--labels", str(labels), "--output", str(output),
        "--report-calls", str(first), "--report-calls", str(second),
    ])
    assert status == 0
    receipt = json.loads((output / "receipt.json").read_text())
    assert [row["path"] for row in receipt["inputs"]["labels"]["report_calls"]] == [str(first), str(second)]
