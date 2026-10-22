"""Synthetic two-sign checks for attributed learning and durable child publication.

These establish wiring/durability, not diagnostic transfer on another patient.
"""

from __future__ import annotations

import csv
import json

import pytest

import scripts.prepare_squint_training as cli
from knee.diagnosis.squint_memory import load_memory_snapshot, save_memory
from knee.diagnosis.squint_procedure_memory import (
    SCHEMA,
    _row_category,
    _row_cue_banks,
    recall_procedure_experiences,
    retain_procedure_experiences,
    select_observation_requests,
)
from knee.study.tables import LABELS

UID = "1.2.826.0.1.3680043.8.498.1000"
OTHER_UID = "1.2.826.0.1.3680043.8.498.2000"
VIEW = ["Coronal", "0", "0"]
BANK = 'squint/v2/view=["Coronal","0","0"]/role=object/metric=signal/direction=d/scale=10mm'


def experience(*, direct: bool, call: int = 1) -> dict:
    return {
        "schema": SCHEMA,
        "row_id": "synthetic-action",
        "study_uid": UID,
        "source": {
            "run": "synthetic-run",
            "record_file": "synthetic-record.json",
            "record_sha256": "a" * 64,
            "memory_sha256": "b" * 64,
            "memory_revision": "parent",
        },
        "request": {
            "question": "ACL",
            "subject": "acl",
            "kind": "bounded_zoom",
            "reason": "proposal_without_sourced_trust",
        },
        "execution": {
            "status": "measured",
            "new_reading": True,
            "reading_available": True,
        },
        "context": {
            "subject": {
                "observed_cue": {
                    "banks": {BANK: [2, 0, 1]},
                    "provenance": "recorded_before_procedure",
                }
            }
        },
        "state": {
            "scope": "condition",
            "attribution_scope": "single_procedure" if direct else "question_final_finding",
            "before": {"outcome": "open"},
            "after": {"outcome": "assigned"},
        },
        "independent_outcome": {"status": "checked", "call": call},
    }


@pytest.mark.parametrize("call", [-1, 1])
def test_final_answer_does_not_teach_success_or_failure_of_an_individual_action(call):
    row = experience(direct=False, call=call)
    category, info, agreement = _row_category(row, "bounded_zoom")
    assert category == "outcome_unattributed"
    assert info["status"] == "new_reading_obtained"
    assert agreement["independent_call"] == call
    memory = retain_procedure_experiences({"revision": "parent", "cases": []}, [row])
    assert memory["procedure_experiences"]["rows"][0] == row
    recalled = recall_procedure_experiences(
        memory,
        question="ACL",
        subject="acl",
        kind="bounded_zoom",
        query_profile={"banks": {BANK: [2, 0, 1]}},
        study_uid=OTHER_UID,
        exclude_same_study=True,
    )
    assert recalled["confirmed_resolution_row_ids"] == []
    assert recalled["contradicted_outcome_row_ids"] == []
    assert recalled["no_reading_available_row_ids"] == []
    assert recalled["unattributed_outcome_row_ids"] == [row["row_id"]]


def test_direct_action_outcome_changes_selection_but_different_context_does_not():
    row = experience(direct=True)
    category, _info, _agreement = _row_category(row, "bounded_zoom")
    assert category == "confirmed_resolution"
    memory = retain_procedure_experiences({"revision": "parent", "cases": []}, [row])
    request = row["request"]
    neutral = {**request, "reason": "different_question_context"}
    objects = {"acl": {"profile": {"banks": {BANK: [2, 0, 1]}}}}
    selected = select_observation_requests(
        [neutral, request], memory, objects=objects, study_uid=OTHER_UID, exclude_same_study=True
    )
    assert selected[0]["reason"] == request["reason"]
    assert selected[0]["recalled_procedure"]["status"] == "recalled_confirmed_resolution"
    assert selected[1].get("recalled_procedure", {}).get("status") != "recalled_confirmed_resolution"


def test_final_object_profile_is_not_silently_used_as_a_pre_action_cue():
    row = experience(direct=True)
    cue = row["context"]["subject"]["observed_cue"]
    assert _row_cue_banks(row, None, UID, "acl") == {BANK: [2, 0, 1]}
    cue["provenance"] = "coarse_banks_from_record"
    assert _row_cue_banks(row, None, UID, "acl") == {}
    row["pre_action_cue"] = {"banks": {BANK: [1, 0, 2]}}
    assert _row_cue_banks(row, None, UID, "acl") == {BANK: [1, 0, 2]}


def object_case(uid: str, case_id: str) -> dict:
    return {
        "case_id": case_id,
        "study_uid": uid,
        "subject": "acl",
        "condition_calls": {},
        "profile": {
            "schema": "knee.squint-profile/v1",
            "subject": "acl",
            "source": {"procedure": "knee.squint-profile/scan-tercile-v1"},
            "banks": {BANK: [2, 0, 1]},
        },
        "regions": [],
        "source": {"kind": "synthetic_visual_fixture"},
    }


@pytest.fixture
def round_inputs(tmp_path):
    case = object_case(UID, "teacher-acl")
    parent = {
        "schema": "knee.squint-memory/v1",
        "procedure": "knee.squint-ternary/v1",
        "revision": "synthetic-parent",
        "questions": list(LABELS),
        "cases": [case],
        "object_identity_teaching": {
            "schema": "knee.object-identity-teaching/v1",
            "confirmed_case_ids": [case["case_id"]],
            "calls": [{"candidate_id": case["case_id"], "call": "confirm", "views": [VIEW]}],
        },
    }
    parent_dir = tmp_path / "parent"
    save_memory(parent, parent_dir)
    snapshot = load_memory_snapshot(parent_dir)
    labels = tmp_path / "labels.csv"
    with labels.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["StudyInstanceUID", *LABELS])
        writer.writeheader()
        writer.writerow({"StudyInstanceUID": UID, **dict.fromkeys(LABELS, 0), "ACL": 1})
        writer.writerow({"StudyInstanceUID": OTHER_UID, **dict.fromkeys(LABELS, 0)})
    executions = []

    def infer(_root, uid, memory, **_kwargs):
        executions.append(uid)
        return {
            "schema": "knee.squint-study/v1",
            "study_uid": uid,
            "memory_revision": memory["revision"],
            "study_status": "examined",
            "questions": {},
            "values": {},
            "objects": {},
            "identity_recall": {},
            "identity_consumption": {"objects": {}},
            "observations": [],
            "work": {},
        }

    return {
        "memory_path": parent_dir,
        "expected_memory_sha256": snapshot.sha256,
        "root_path": tmp_path / "raw",
        "study_uids": [UID],
        "labels_path": labels,
        "output_path": tmp_path / "round",
        "child_revision": "synthetic-child",
        "infer_fn": infer,
    }, executions


def test_resume_after_child_publication_preserves_lineage_and_completed_work(round_inputs, monkeypatch):
    inputs, executions = round_inputs
    original_write = cli._write_json

    def interrupt_final_receipt(path, payload):
        if path.name == "round-receipt.json":
            raise RuntimeError("interrupted_after_publication")
        return original_write(path, payload)

    monkeypatch.setattr(cli, "_write_json", interrupt_final_receipt)
    with pytest.raises(RuntimeError, match="interrupted_after_publication"):
        cli.run_round(**inputs)
    child_path = inputs["output_path"] / "memory"
    published = load_memory_snapshot(child_path)
    assert published.memory is not None
    assert published.memory["parent_revision"] == "synthetic-parent"
    assert published.memory["parent_manifest_sha256"] == inputs["expected_memory_sha256"]
    original_inode = (child_path / "manifest.json").stat().st_ino
    monkeypatch.setattr(cli, "_write_json", original_write)
    result = cli.run_round(**inputs)
    assert executions == [UID]
    assert result["studies"]["resumed"] == [UID]
    assert result["child_memory"]["manifest_sha256"] == published.sha256
    assert (child_path / "manifest.json").stat().st_ino == original_inode


def test_partial_resume_rejects_different_signed_content_even_with_the_same_case_ids(round_inputs):
    inputs, _executions = round_inputs
    cli.run_round(**inputs)
    output = inputs["output_path"]
    (output / "round-receipt.json").unlink()
    manifest_path = output / "memory" / "manifest.json"
    changed = json.loads(manifest_path.read_text())
    changed["cases"][0]["condition_calls"]["ACL"] = -1
    manifest_path.write_text(json.dumps(changed))
    with pytest.raises(cli.PrepareError, match="child_memory_checkpoint_content_mismatch"):
        cli.run_round(**inputs)


def test_child_export_contains_new_visual_teaching_and_its_own_pin(round_inputs):
    inputs, executions = round_inputs
    new_case = object_case(OTHER_UID, "added-acl")
    additions = {
        "schema": cli.squint_visual_teaching.SCHEMA,
        "reader": "synthetic-test-reviewer",
        "cases": [new_case],
        "calls": [{
            "candidate_id": new_case["case_id"], "call": "confirm", "views": [VIEW],
            "notes": "Synthetic independently called support for publication test.",
        }],
    }
    additions_path = inputs["output_path"].parent / "additions.json"
    additions_path.write_text(json.dumps(additions))
    result = cli.run_round(**inputs, visual_additions_path=additions_path)
    parent_corpus = json.loads((inputs["output_path"] / "training" / "object-buckets.json").read_text())
    child_corpus = json.loads((inputs["output_path"] / "child-training" / "object-buckets.json").read_text())
    assert len(parent_corpus["scoped_records"]) == 1
    assert len(child_corpus["scoped_records"]) == 2
    assert child_corpus["teaching_memory"]["manifest_sha256"] == result["child_memory"]["manifest_sha256"]
    added = next(r for r in child_corpus["scoped_records"] if r["case_id"] == "added-acl")
    assert added["state"]["status"] == "normal"
    assert result["child_training"]["outputs"]["object_cases"] == 2
    cli.run_round(**inputs, visual_additions_path=additions_path)
    assert executions == [UID]


def test_completed_round_refuses_tampered_child_export(round_inputs):
    inputs, _executions = round_inputs
    cli.run_round(**inputs)
    corpus_path = inputs["output_path"] / "child-training" / "object-buckets.json"
    changed = json.loads(corpus_path.read_text())
    changed["scoped_records"] = []
    corpus_path.write_text(json.dumps(changed))
    with pytest.raises(cli.PrepareError, match="training_checkpoint_output_mismatch"):
        cli.run_round(**inputs)


def test_real_cli_resume_reports_the_child_material_without_reexecuting_studies(round_inputs, capsys):
    inputs, executions = round_inputs
    expected = cli.run_round(**inputs)
    assert cli.main([
        "--run-round", "--memory", str(inputs["memory_path"]),
        "--memory-sha256", inputs["expected_memory_sha256"],
        "--root", str(inputs["root_path"]), "--study-uid", UID,
        "--labels", str(inputs["labels_path"]),
        "--child-revision", inputs["child_revision"],
        "--output", str(inputs["output_path"]),
    ]) == 0
    returned = json.loads(capsys.readouterr().out)
    assert returned["child_training"]["teaching_memory"]["manifest_sha256"] == expected["child_memory"]["manifest_sha256"]
    assert returned["studies"] == {"requested": [UID], "executed": [], "resumed": [UID]}
    assert executions == [UID]
