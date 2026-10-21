from __future__ import annotations

import csv
import hashlib
import json
import runpy
from pathlib import Path

from knee.diagnosis.squint_memory import SCHEMA, load_memory, save_memory
from knee.diagnosis.squint_reports import BATCH_SCHEMA, CALL_SCHEMA
from knee.study.tables import LABELS, TRAIN_COLUMNS

SCRIPT = Path(__file__).parents[1] / "scripts" / "squint_report_teaching.py"
main = runpy.run_path(str(SCRIPT), run_name="squint_report_teaching_test")["main"]


def _train_csv(path: Path, uid: str, report: str) -> Path:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(TRAIN_COLUMNS)
        writer.writerow((uid, report, *(["0"] * len(LABELS))))
    return path


def _memory(path: Path) -> Path:
    memory = {
        "schema": SCHEMA,
        "revision": "revision-0",
        "questions": list(LABELS),
        "cases": [],
    }
    save_memory(memory, path)
    return path


def _call(uid: str, report: str, *, source: str = "report:train.csv") -> dict:
    sentence = "There is a full thickness ACL tear."
    return {
        "schema": CALL_SCHEMA,
        "study_uid": uid,
        "question": "ACL",
        "digit": 1,
        "assertion": "present",
        "sentence": sentence,
        "subject": "acl",
        "scope": "study_condition",
        "source": source,
        "report_sha": hashlib.sha256(report.encode("utf-8")).hexdigest(),
        "reader": "independent-reader",
    }


def _inference_record(uid: str) -> dict:
    return {
        "schema": "knee.squint-study/v1",
        "study_uid": uid,
        "objects": {
            "acl": {
                "status": "proposal",
                "profile": {
                    "schema": "knee.squint-profile/v1",
                    "subject": "acl",
                    "banks": {"squint/acl/sagittal/overview/10mm": [2, 1, 0]},
                    "source": {"study_uid": uid, "mode": "cheap"},
                },
                "regions": [{"series_uid": "series-1", "window": [0, 1, 0, 1, 0, 1]}],
            },
            "mcl": {"status": "unresolved_missing_reading", "profile": None},
        },
    }


def test_export_cli_writes_report_batch_without_label_values(tmp_path, capsys):
    uid = "1.2.826.0.1"
    report = "There is a full thickness ACL tear."
    train = _train_csv(tmp_path / "train.csv", uid, report)
    output = tmp_path / "reader-batch.json"

    result = main(
        [
            "export",
            "--train-csv",
            str(train),
            "--output",
            str(output),
            "--study-uid",
            uid,
        ]
    )

    document = json.loads(output.read_text(encoding="utf-8"))
    assert result["schema"] == BATCH_SCHEMA
    assert document["studies"] == [
        {
            "study_uid": uid,
            "report_sha256": hashlib.sha256(report.encode("utf-8")).hexdigest(),
            "report": report,
        }
    ]
    assert "labels" in document["purpose"]
    assert not any(label in document for label in LABELS)
    assert json.loads(capsys.readouterr().out)["study_count"] == 1


def test_admit_cli_publishes_new_revision_from_verified_located_profile(
    tmp_path, capsys
):
    uid = "1.2.826.0.2"
    report = "There is a full thickness ACL tear."
    train = _train_csv(tmp_path / "train.csv", uid, report)
    calls_path = tmp_path / "calls.json"
    calls_path.write_text(json.dumps([_call(uid, report)]), encoding="utf-8")
    findings_dir = tmp_path / "inference"
    studies = findings_dir / "studies"
    studies.mkdir(parents=True)
    (studies / f"{uid}.json").write_text(
        json.dumps(_inference_record(uid)), encoding="utf-8"
    )
    memory_path = _memory(tmp_path / "memory-r0")
    output_memory = tmp_path / "memory-r1"

    result = main(
        [
            "admit",
            "--train-csv",
            str(train),
            "--calls",
            str(calls_path),
            "--findings-dir",
            str(findings_dir),
            "--memory",
            str(memory_path),
            "--revision",
            "revision-1",
            "--output-memory",
            str(output_memory),
        ]
    )

    original = load_memory(memory_path)
    revised = load_memory(output_memory)
    assert original["revision"] == "revision-0" and original["cases"] == []
    assert revised["revision"] == "revision-1"
    assert len(revised["cases"]) == 1
    assert revised["cases"][0]["condition_calls"] == {"ACL": 1}
    assert revised["cases"][0]["study_uid"] == uid
    assert revised["cases"][0]["profile"]["source"]["study_uid"] == uid
    assert result["added_case_count"] == 1
    assert json.loads(capsys.readouterr().out)["revision"] == "revision-1"


def test_forged_report_source_is_retained_without_teaching(tmp_path):
    uid = "1.2.826.0.3"
    report = "There is a full thickness ACL tear."
    train = _train_csv(tmp_path / "train.csv", uid, report)
    calls_path = tmp_path / "calls.json"
    calls_path.write_text(
        json.dumps([_call(uid, report, source="recall:held-out-memory")]),
        encoding="utf-8",
    )
    findings_dir = tmp_path / "inference"
    studies = findings_dir / "studies"
    studies.mkdir(parents=True)
    (studies / f"{uid}.json").write_text(
        json.dumps(_inference_record(uid)), encoding="utf-8"
    )
    memory_path = _memory(tmp_path / "memory-r0")
    output_memory = tmp_path / "memory-r1"

    result = main(
        [
            "admit",
            "--train-csv",
            str(train),
            "--calls",
            str(calls_path),
            "--findings-dir",
            str(findings_dir),
            "--memory",
            str(memory_path),
            "--revision",
            "revision-1",
            "--output-memory",
            str(output_memory),
        ]
    )

    revised = load_memory(output_memory)
    assert revised["cases"] == []
    assert result["added_case_count"] == 0
    assert (
        revised["report_admissions"][-1]["retained_calls"]["rejected"][0]["status"]
        == "visual_memory_source"
    )
    assert load_memory(memory_path)["revision"] == "revision-0"
