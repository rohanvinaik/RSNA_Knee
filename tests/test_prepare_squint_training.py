from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import scripts.prepare_squint_training as cli

UID = "1.2.826.0.1.3680043.8.498.1000"
SOURCE_REVISION = "inference-revision"
TEACHING_REVISION = "reviewed-revision"
SOURCE_MEMORY_SHA = "a" * 64
TEACHING_MEMORY_SHA = "b" * 64


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def record(uid: str = UID, revision: str = SOURCE_REVISION) -> dict:
    return {
        "schema": "knee.squint-study/v1",
        "study_uid": uid,
        "memory_revision": revision,
        "study_status": "examined",
        "questions": {},
        "values": {},
        "objects": {},
        "identity_recall": {"resolved_scale": {"contested_at_squint_scale": []}},
        "identity_consumption": {"objects": {}},
        "observations": [
            {
                "subject": "femur",
                "code": "measured",
                "requested_by": "identity_question",
            }
        ],
        "unresolved_observation_requests": [],
        "work": {},
    }


def reviewed_memory(record_sha: str) -> dict:
    candidate_id = f"located:{UID}:femur:{SOURCE_REVISION}"
    return {
        "revision": TEACHING_REVISION,
        "cases": [
            {
                "case_id": candidate_id,
                "identity_growth": {"source": {"record_sha256": record_sha}},
            }
        ],
        "object_identity_teaching": {
            "admission_reviews": [
                {
                    "review_sha256": "r" * 64,
                    "calls": [
                        {
                            "candidate_id": candidate_id,
                            "call": "confirm",
                            "views": [["Coronal", "0", "0"]],
                            "reader": "reviewer",
                        }
                    ],
                }
            ]
        },
    }


def inputs(tmp_path: Path, *, evidence_path: str = "studies/study.json"):
    memory_path = tmp_path / "memory"
    memory_path.mkdir()
    manifest = memory_path / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")

    run = tmp_path / "run"
    run.mkdir()
    study_path = run / evidence_path
    write_json(study_path, record())
    record_sha = sha(study_path)
    receipt = {
        "schema": "knee.squint-run/v1",
        "action": "infer",
        "source_mode": "raw_squint_case_recall",
        "memory_revision": SOURCE_REVISION,
        "memory_manifest_sha256": SOURCE_MEMORY_SHA,
        "work": {"studies": [{"study_uid": UID, "evidence_path": evidence_path}]},
    }
    write_json(run / "receipt.json", receipt)
    labels = tmp_path / "train.csv"
    labels.write_text(
        f"StudyInstanceUID,Report,ACL\n{UID},report,1\n", encoding="utf-8"
    )
    output = tmp_path / "prepared"
    snapshot = SimpleNamespace(
        memory=reviewed_memory(record_sha),
        sha256=TEACHING_MEMORY_SHA,
        path=manifest,
    )
    return memory_path, run, labels, output, snapshot


def test_cli_writes_pinned_experience_with_separate_memory_identities(
    tmp_path, monkeypatch
):
    memory_path, run, labels, output, snapshot = inputs(tmp_path)
    monkeypatch.setattr(cli, "load_memory_snapshot", lambda _path: snapshot)

    receipt = cli.prepare(
        memory_path=memory_path,
        expected_memory_sha256=TEACHING_MEMORY_SHA,
        run_paths=[run],
        labels_path=labels,
        output_path=output,
    )

    rows = [
        json.loads(line)
        for line in (output / "procedure-experiences.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert len(rows) == 1
    row = rows[0]
    assert row["independent_outcome"]["status"] == "checked"
    assert row["source"]["memory_revision"] == SOURCE_REVISION
    assert row["source"]["memory_sha256"] == SOURCE_MEMORY_SHA
    saved = json.loads((output / "receipt.json").read_text(encoding="utf-8"))
    assert saved["inputs"]["teaching_memory"]["revision"] == TEACHING_REVISION
    assert saved["inputs"]["teaching_memory"]["manifest_sha256"] == TEACHING_MEMORY_SHA
    assert saved["outputs"]["checked"] == 1
    assert saved["outputs"]["unchecked"] == 0
    assert saved["outputs"]["question_attribution"] == {"recorded": 1}
    assert receipt["outputs"]["rows"] == 1


def test_evidence_path_outside_run_is_refused_without_partial_output(
    tmp_path, monkeypatch
):
    memory_path, run, labels, output, snapshot = inputs(
        tmp_path, evidence_path="../outside.json"
    )
    monkeypatch.setattr(cli, "load_memory_snapshot", lambda _path: snapshot)
    with pytest.raises(cli.PrepareError, match="study_evidence_outside_run"):
        cli.prepare(
            memory_path=memory_path,
            expected_memory_sha256=TEACHING_MEMORY_SHA,
            run_paths=[run],
            labels_path=labels,
            output_path=output,
        )
    assert not output.exists()


def test_record_from_another_inference_memory_is_refused(tmp_path, monkeypatch):
    memory_path, run, labels, output, snapshot = inputs(tmp_path)
    write_json(run / "studies/study.json", record(revision="stale-revision"))
    monkeypatch.setattr(cli, "load_memory_snapshot", lambda _path: snapshot)
    with pytest.raises(cli.PrepareError, match="study_record_memory_revision_mismatch"):
        cli.prepare(
            memory_path=memory_path,
            expected_memory_sha256=TEACHING_MEMORY_SHA,
            run_paths=[run],
            labels_path=labels,
            output_path=output,
        )
    assert not output.exists()


def test_empty_run_and_missing_inputs_have_named_refusals(tmp_path, monkeypatch):
    memory_path, run, labels, output, snapshot = inputs(tmp_path)
    write_json(
        run / "receipt.json",
        {
            "schema": "knee.squint-run/v1",
            "action": "infer",
            "source_mode": "raw_squint_case_recall",
            "memory_revision": SOURCE_REVISION,
            "memory_manifest_sha256": SOURCE_MEMORY_SHA,
            "work": {"studies": []},
        },
    )
    monkeypatch.setattr(cli, "load_memory_snapshot", lambda _path: snapshot)
    with pytest.raises(cli.PrepareError, match="run_studies_empty"):
        cli.prepare(
            memory_path=memory_path,
            expected_memory_sha256=TEACHING_MEMORY_SHA,
            run_paths=[run],
            labels_path=labels,
            output_path=output,
        )
    with pytest.raises(cli.PrepareError, match="run_inputs_missing"):
        cli.prepare(
            memory_path=memory_path,
            expected_memory_sha256=TEACHING_MEMORY_SHA,
            run_paths=[],
            labels_path=labels,
            output_path=output,
        )
    with pytest.raises(cli.PrepareError, match="labels_missing"):
        cli.prepare(
            memory_path=memory_path,
            expected_memory_sha256=TEACHING_MEMORY_SHA,
            run_paths=[run],
            labels_path=tmp_path / "missing.csv",
            output_path=output,
        )
    assert not output.exists()


def test_memory_digest_mismatch_is_refused(tmp_path, monkeypatch):
    memory_path, run, labels, output, snapshot = inputs(tmp_path)
    monkeypatch.setattr(cli, "load_memory_snapshot", lambda _path: snapshot)
    with pytest.raises(cli.PrepareError, match="teaching_memory_sha256_mismatch"):
        cli.prepare(
            memory_path=memory_path,
            expected_memory_sha256="c" * 64,
            run_paths=[run],
            labels_path=labels,
            output_path=output,
        )
    assert not output.exists()


def test_empty_labels_table_is_refused(tmp_path, monkeypatch):
    memory_path, run, labels, output, snapshot = inputs(tmp_path)
    labels.write_text("StudyInstanceUID,Report,ACL\n", encoding="utf-8")
    monkeypatch.setattr(cli, "load_memory_snapshot", lambda _path: snapshot)
    with pytest.raises(cli.PrepareError, match="labels_empty"):
        cli.prepare(
            memory_path=memory_path,
            expected_memory_sha256=TEACHING_MEMORY_SHA,
            run_paths=[run],
            labels_path=labels,
            output_path=output,
        )
    assert not output.exists()
