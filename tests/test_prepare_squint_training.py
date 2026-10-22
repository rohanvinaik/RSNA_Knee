from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import scripts.prepare_squint_training as cli
from knee.study.tables import LABELS

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
                "study_uid": UID,
                "subject": "femur",
                "condition_calls": {},
                "profile": {
                    "schema": "knee.squint-profile/v1",
                    "subject": "femur",
                    "banks": {
                        'squint/v2/view=["Coronal","0","0"]/role=object/metric=signal/direction=d/scale=10mm': [
                            2,
                            0,
                            1,
                        ]
                    },
                },
                "identity_growth": {"source": {"record_sha256": record_sha}},
            }
        ],
        "object_identity_teaching": {
            "schema": "knee.object-identity-teaching/v1",
            "confirmed_case_ids": [candidate_id],
            "calls": [
                {
                    "candidate_id": candidate_id,
                    "call": "confirm",
                    "views": [["Coronal", "0", "0"]],
                    "identity_growth": {"source": {"record_sha256": record_sha}},
                }
            ],
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
            ],
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
    corpus = json.loads((output / "object-buckets.json").read_text())
    assert corpus["scoped_records"][0]["state"]["status"] == "condition_presentation"
    assert corpus["scoped_records"][0]["state"]["unknown_questions"]
    assert corpus["teaching_memory"]["manifest_sha256"] == TEACHING_MEMORY_SHA


def test_official_unrelated_positive_keeps_reviewed_femur_in_normal_bucket(
    tmp_path, monkeypatch
):
    memory_path, run, labels, output, snapshot = inputs(tmp_path)
    with labels.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["StudyInstanceUID", *LABELS])
        writer.writeheader()
        writer.writerow(
            {"StudyInstanceUID": UID, **dict.fromkeys(LABELS, 0), "Synovitis": 1}
        )
    monkeypatch.setattr(cli, "load_memory_snapshot", lambda _path: snapshot)

    receipt = cli.prepare(
        memory_path=memory_path,
        expected_memory_sha256=TEACHING_MEMORY_SHA,
        run_paths=[run],
        labels_path=labels,
        output_path=output,
    )

    corpus = json.loads((output / "object-buckets.json").read_text())
    case_id = snapshot.memory["cases"][0]["case_id"]
    assert corpus["buckets"] == {"femur": {"normal": [case_id]}}
    assert corpus["condition_buckets"] == {}
    [scoped] = corpus["scoped_records"]
    assert scoped["identity_views"] == [["Coronal", "0", "0"]]
    assert scoped["case"]["profile"]["banks"]
    assert scoped["case"]["condition_calls"] == {}
    assert receipt["outputs"]["object_states"] == {"normal": 1}


def test_official_fracture_retains_condition_presentation_without_localizing_it(
    tmp_path, monkeypatch
):
    memory_path, run, labels, output, snapshot = inputs(tmp_path)
    with labels.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["StudyInstanceUID", *LABELS])
        writer.writeheader()
        writer.writerow(
            {"StudyInstanceUID": UID, **dict.fromkeys(LABELS, 0), "Fracture": 1}
        )
    monkeypatch.setattr(cli, "load_memory_snapshot", lambda _path: snapshot)

    cli.prepare(
        memory_path=memory_path,
        expected_memory_sha256=TEACHING_MEMORY_SHA,
        run_paths=[run],
        labels_path=labels,
        output_path=output,
    )

    corpus = json.loads((output / "object-buckets.json").read_text())
    case_id = snapshot.memory["cases"][0]["case_id"]
    assert corpus["buckets"] == {"femur": {"condition_presentation": [case_id]}}
    assert corpus["condition_buckets"] == {"femur": {"Fracture": [case_id]}}
    [scoped] = corpus["scoped_records"]
    assert scoped["case"]["condition_calls"] == {}
    assert scoped["state"]["implicated_positive"] == ["Fracture"]


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


def test_run_round_publishes_immutable_child_memory_and_resumes_pinned_checkpoints(
    tmp_path,
):
    from knee.diagnosis.squint_memory import load_memory_snapshot, save_memory

    uid_a = UID
    uid_b = "1.2.826.0.1.3680043.8.498.2000"
    from squint_training_fixture import make_training_raw_fixture

    make_training_raw_fixture(tmp_path / "raw", [uid_a, uid_b])
    parent_dir = tmp_path / "parent-memory"
    parent_memory = reviewed_memory("r" * 64)
    parent_memory["schema"] = "knee.squint-memory/v1"
    parent_memory["procedure"] = "knee.squint-ternary/v1"
    parent_memory["questions"] = list(LABELS)
    parent_memory["cases"][0]["regions"] = []
    parent_memory["cases"][0]["profile"]["source"] = {
        "procedure": "knee.squint-profile/scan-tercile-v1"
    }
    parent_memory["cases"][0]["source"] = {"kind": "seed"}
    save_memory(parent_memory, parent_dir)
    parent_snapshot = load_memory_snapshot(parent_dir)
    assert parent_snapshot.sha256 is not None

    labels = tmp_path / "train.csv"
    with labels.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["StudyInstanceUID", "Report", *LABELS]
        )
        writer.writeheader()
        writer.writerow(
            {
                "StudyInstanceUID": uid_a,
                "Report": "report",
                **dict.fromkeys(LABELS, 0),
                "ACL": 1,
            }
        )
        writer.writerow(
            {"StudyInstanceUID": uid_b, "Report": "report", **dict.fromkeys(LABELS, 0)}
        )

    executed_calls: list[str] = []
    fail_on_b = True

    def fake_infer(_root: Path, uid: str, memory, **_kwargs):
        if uid == uid_b and fail_on_b:
            raise RuntimeError("interrupted_before_uid_b")
        executed_calls.append(uid)
        rec = record(uid=uid, revision=str(memory["revision"]))
        rec["observations"] = [
            {
                "subject": "acl",
                "code": "measured",
                "question": "ACL",
                "request_id": "ACL/acl/bounded_zoom",
                "request_kind": "bounded_zoom",
                "request_reason": "proposal_without_sourced_trust",
                "before_cue": {
                    "schema": "knee.squint-profile/v1",
                    "subject": "acl",
                    "procedure": "territory-v2",
                    "banks": {
                        'squint/v2/view=["Sagittal","0","0"]/role=object/metric=signal/direction=si/scale=10mm': [
                            2,
                            0,
                            1,
                        ]
                    },
                },
                "before_state": {"outcome": "open", "reason": "before"},
                "after_state": {
                    "outcome": "assigned" if uid == uid_a else "defeated",
                    "reason": "after",
                    "subject_reading": {
                        "state": (
                            "condition_presentation" if uid == uid_a else "normal"
                        ),
                        "code": "sourced",
                    },
                    "attribution_scope": "single_procedure",
                },
            }
        ]
        rec["questions"] = {
            "ACL": {
                "finding": {
                    "outcome": "assigned" if uid == uid_a else "defeated",
                    "reason": "after",
                    "evidence": {
                        "readings": {"acl": {"role": "necessary", "state": "normal"}},
                        "necessary": ["acl"],
                        "alternatives": [],
                        "supporting": [],
                    },
                    "observation_requests": [],
                    "rank": {"tier": "assigned"},
                },
                "ranking": {},
                "objects": {},
            }
        }
        return rec

    round_dir = tmp_path / "round-1"
    with pytest.raises(RuntimeError, match="interrupted_before_uid_b"):
        cli.run_round(
            memory_path=parent_dir,
            expected_memory_sha256=parent_snapshot.sha256,
            root_path=tmp_path / "raw",
            study_uids=[uid_a, uid_b],
            labels_path=labels,
            output_path=round_dir,
            child_revision="round-1-child",
            infer_fn=fake_infer,
        )
    assert executed_calls == [uid_a]
    assert (round_dir / "inference" / "studies" / f"{uid_a}.pin.json").exists()
    assert not (round_dir / "memory").exists()

    # Mismatched round inputs on resume are refused by name
    with pytest.raises(cli.PrepareError, match="round_inputs_mismatch"):
        cli.run_round(
            memory_path=parent_dir,
            expected_memory_sha256=parent_snapshot.sha256,
            root_path=tmp_path / "raw",
            study_uids=[uid_a],
            labels_path=labels,
            output_path=round_dir,
            child_revision="round-1-child",
            infer_fn=fake_infer,
        )

    # Resume interrupted round with identical pinned inputs: uid_a is reused, only uid_b executes
    fail_on_b = False
    completed = cli.run_round(
        memory_path=parent_dir,
        expected_memory_sha256=parent_snapshot.sha256,
        root_path=tmp_path / "raw",
        study_uids=[uid_a, uid_b],
        labels_path=labels,
        output_path=round_dir,
        child_revision="round-1-child",
        infer_fn=fake_infer,
    )
    assert executed_calls == [uid_a, uid_b]
    assert completed["studies"] == {
        "requested": [uid_a, uid_b],
        "executed": [uid_b],
        "resumed": [uid_a],
    }
    assert completed["child_memory"]["retained_procedure_experiences"] == 2
    child_manifest = round_dir / "memory" / "manifest.json"
    child_inode_before = child_manifest.stat().st_ino

    # Calling run_round again on the completed round reuses the verified child without deleting it
    resumed_completed = cli.run_round(
        memory_path=parent_dir,
        expected_memory_sha256=parent_snapshot.sha256,
        root_path=tmp_path / "raw",
        study_uids=[uid_a, uid_b],
        labels_path=labels,
        output_path=round_dir,
        child_revision="round-1-child",
        infer_fn=fake_infer,
    )
    assert executed_calls == [uid_a, uid_b]
    assert resumed_completed["studies"] == {
        "requested": [uid_a, uid_b],
        "executed": [],
        "resumed": [uid_a, uid_b],
    }
    assert child_manifest.stat().st_ino == child_inode_before

    # Next round consumes the published child memory
    round2_dir = tmp_path / "round-2"
    round2 = cli.run_round(
        memory_path=round_dir / "memory",
        expected_memory_sha256=completed["child_memory"]["manifest_sha256"],
        root_path=tmp_path / "raw",
        study_uids=[uid_b],
        labels_path=labels,
        output_path=round2_dir,
        child_revision="round-2-child",
        infer_fn=fake_infer,
    )
    assert (
        round2["parent_memory"]["manifest_sha256"]
        == completed["child_memory"]["manifest_sha256"]
    )
    assert round2["child_memory"]["retained_procedure_experiences"] >= 2
