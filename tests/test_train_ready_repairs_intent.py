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
            "attribution_scope": "single_procedure"
            if direct
            else "question_final_finding",
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
    ambiguous_failure = experience(direct=False, call=-1)
    ambiguous_failure["row_id"] = "unattributed-final-failure"
    memory = retain_procedure_experiences(
        {"revision": "parent", "cases": []}, [row, ambiguous_failure]
    )
    request = row["request"]
    neutral = {**request, "reason": "different_question_context"}
    objects = {"acl": {"profile": {"banks": {BANK: [2, 0, 1]}}}}
    selected = select_observation_requests(
        [neutral, request],
        memory,
        objects=objects,
        study_uid=OTHER_UID,
        exclude_same_study=True,
    )
    assert selected[0]["reason"] == request["reason"]
    assert (
        selected[0]["recalled_procedure"]["status"] == "recalled_confirmed_resolution"
    )
    assert (
        selected[1].get("recalled_procedure", {}).get("status")
        != "recalled_confirmed_resolution"
    )


def test_final_object_profile_is_not_silently_used_as_a_pre_action_cue():
    row = experience(direct=True)
    cue = row["context"]["subject"]["observed_cue"]
    assert _row_cue_banks(row, None, UID, "acl") == {BANK: [2, 0, 1]}
    cue["provenance"] = "coarse_banks_from_record"
    assert _row_cue_banks(row, None, UID, "acl") == {}
    row["pre_action_cue"] = {"banks": {BANK: [1, 0, 2]}}
    assert _row_cue_banks(row, None, UID, "acl") == {BANK: [1, 0, 2]}


def test_procedure_opposition_requires_compatible_context_and_contrary_outcome():
    import copy

    # Baseline: a successful attributed experience
    succ = experience(direct=True)
    base_memory = retain_procedure_experiences(
        {"revision": "parent", "cases": []}, [succ]
    )
    recalled_base = recall_procedure_experiences(
        base_memory,
        question="ACL",
        subject="acl",
        kind="bounded_zoom",
        query_profile={"banks": {BANK: [2, 0, 1]}},
        query_context={"request_reason": "proposal_without_sourced_trust"},
        study_uid=OTHER_UID,
        exclude_same_study=True,
    )
    assert recalled_base["status"] == "recalled_confirmed_resolution"

    # Sign 1A: An otherwise identical attributed experience ending open does NOT oppose usefulness
    open_exp = copy.deepcopy(succ)
    open_exp["row_id"] = "open-action"
    open_exp["state"]["after"] = {"outcome": "open"}
    open_exp["study_uid"] = "1.2.826.0.1.3680043.8.498.9999"
    memory_with_open = retain_procedure_experiences(
        {"revision": "parent", "cases": []}, [succ, open_exp]
    )
    recalled_open = recall_procedure_experiences(
        memory_with_open,
        question="ACL",
        subject="acl",
        kind="bounded_zoom",
        query_profile={"banks": {BANK: [2, 0, 1]}},
        query_context={"request_reason": "proposal_without_sourced_trust"},
        study_uid=OTHER_UID,
        exclude_same_study=True,
    )
    assert recalled_open["status"] == "recalled_confirmed_resolution"

    # Sign 1B: An otherwise identical failed experience with a different request reason
    # cannot define this precedent's opposition floor
    fail_diff_reason = copy.deepcopy(succ)
    fail_diff_reason["row_id"] = "fail-diff-reason"
    fail_diff_reason["state"]["after"] = {"outcome": "assigned"}
    fail_diff_reason["independent_outcome"] = {"status": "checked", "call": -1}
    fail_diff_reason["request"]["reason"] = "different_reason"
    fail_diff_reason["study_uid"] = "1.2.826.0.1.3680043.8.498.8888"
    memory_with_inapplicable_failure = retain_procedure_experiences(
        {"revision": "parent", "cases": []}, [succ, fail_diff_reason]
    )
    recalled_diff_reason = recall_procedure_experiences(
        memory_with_inapplicable_failure,
        question="ACL",
        subject="acl",
        kind="bounded_zoom",
        query_profile={"banks": {BANK: [2, 0, 1]}},
        query_context={"request_reason": "proposal_without_sourced_trust"},
        study_uid=OTHER_UID,
        exclude_same_study=True,
    )
    assert recalled_diff_reason["status"] == "recalled_confirmed_resolution"

    # Sign 2A: An otherwise identical failed experience WITH compatible request reason
    # DOES oppose and prevent promotion (neither strictly dominates, so neither reaches envelope)
    fail_same_reason = copy.deepcopy(succ)
    fail_same_reason["row_id"] = "fail-same-reason"
    fail_same_reason["state"]["after"] = {"outcome": "assigned"}
    fail_same_reason["independent_outcome"] = {"status": "checked", "call": -1}
    fail_same_reason["study_uid"] = "1.2.826.0.1.3680043.8.498.7777"
    memory_with_applicable_failure = retain_procedure_experiences(
        {"revision": "parent", "cases": []}, [succ, fail_same_reason]
    )
    recalled_same_reason = recall_procedure_experiences(
        memory_with_applicable_failure,
        question="ACL",
        subject="acl",
        kind="bounded_zoom",
        query_profile={"banks": {BANK: [2, 0, 1]}},
        query_context={"request_reason": "proposal_without_sourced_trust"},
        study_uid=OTHER_UID,
        exclude_same_study=True,
    )
    assert recalled_same_reason["status"] == "no_context_compatible_experience"
    assert recalled_same_reason["confirmed_resolution_row_ids"] == []
    assert "synthetic-action" in recalled_same_reason["incompatible_cue_row_ids"]
    assert "fail-same-reason" in recalled_same_reason["incompatible_cue_row_ids"]

    # Sign 2B: When query is closer to the applicable failure than to the success,
    # the failure's envelope is reached and outcome is contradicted
    fail_closer = copy.deepcopy(succ)
    fail_closer["row_id"] = "fail-closer"
    fail_closer["state"]["after"] = {"outcome": "assigned"}
    fail_closer["independent_outcome"] = {"status": "checked", "call": -1}
    fail_closer["study_uid"] = "1.2.826.0.1.3680043.8.498.7778"
    fail_closer["context"]["subject"]["observed_cue"]["banks"][BANK] = [3, 0, 1]
    memory_with_closer_failure = retain_procedure_experiences(
        {"revision": "parent", "cases": []}, [succ, fail_closer]
    )
    recalled_closer = recall_procedure_experiences(
        memory_with_closer_failure,
        question="ACL",
        subject="acl",
        kind="bounded_zoom",
        query_profile={"banks": {BANK: [4, 0, 1]}},
        query_context={"request_reason": "proposal_without_sourced_trust"},
        study_uid=OTHER_UID,
        exclude_same_study=True,
    )
    assert recalled_closer["status"] == "recalled_outcome_contradicted"
    assert recalled_closer["confirmed_resolution_row_ids"] == []
    assert "fail-closer" in recalled_closer["contradicted_outcome_row_ids"]


def test_attributed_identity_look_with_independent_review_and_agreement():
    from knee.diagnosis.squint_procedure_memory import (
        experience_rows,
    )

    source = {
        "run": "synthetic-run",
        "record_file": "synthetic-record.json",
        "record_sha256": "a" * 64,
        "memory_sha256": "b" * 64,
        "memory_revision": "parent",
    }
    study_record = {
        "schema": "knee.squint-study/v1",
        "study_uid": UID,
        "memory_revision": "parent",
        "study_status": "examined",
        "questions": {},
        "values": {},
        "objects": {
            "femur": {
                "status": "located",
                "profile": {"banks": {BANK: [2, 0, 1]}},
                "evidence": {"location_route": "structural_anchor"},
            }
        },
        "identity_recall": {
            "objects": {
                "femur": {
                    "scale": "10mm",
                    "outcome": "appearance_opposed",
                    "applicable_negative_case_ids": ["neg-1"],
                }
            },
            "resolved_scale": {
                "contested_at_squint_scale": ["femur"],
                "objects": {
                    "femur": {
                        "scale": "joint",
                        "outcome": "appearance_supported",
                        "applicable_negative_case_ids": [],
                    }
                },
            },
        },
        "identity_consumption": {
            "objects": {
                "femur": {
                    "region_read_as_subject": True,
                    "identity_effect": "answers",
                    "squint_scale_contest": {
                        "status": "resolved_by_finer_reading",
                        "finer_look": {"code": "measured"},
                    },
                }
            }
        },
        "observations": [
            {
                "requested_by": "identity_question",
                "question": "identity",
                "subject": "femur",
                "code": "measured",
                "request_id": "identity:femur:contested_at_squint_scale",
                "request_kind": "bounded_zoom",
                "request_reason": "contested_at_squint_scale",
                "request_scope": "object_window",
                "attribution_scope": "single_procedure",
                "before_cue": {
                    "subject": "femur",
                    "banks": {BANK: [2, 0, 1]},
                    "procedure": "paired_finer_reading",
                },
                "before_state": {
                    "scale": "10mm",
                    "outcome": "appearance_opposed",
                    "applicable_negative_cases": 1,
                },
                "after_state": {
                    "scale": "joint",
                    "outcome": "appearance_supported",
                    "applicable_negative_cases": 0,
                },
                "after_identity_consumption": {
                    "region_read_as_subject": True,
                    "identity_effect": "answers",
                },
            }
        ],
        "work": {},
    }

    def make_call_index(call_str: str) -> dict:
        return {
            "reviewer_calls": {
                (UID, "femur"): [
                    {
                        "call": call_str,
                        "concerns": "located_candidate",
                        "record_sha256": source["record_sha256"],
                        "candidate_revision": source["memory_revision"],
                        "views": [VIEW],
                        "reader": "reviewer",
                        "notes": "reviewer note",
                        "candidate_id": f"located:{UID}:femur:rev",
                    }
                ]
            }
        }

    # Case 1: Attributed identity look with matching reviewer confirm -> confirmed_resolution
    rows = experience_rows(
        study_record,
        source,
        labels={"calls": {}, "table_uids": {UID}},
        call_index=make_call_index("confirm"),
    )
    assert len(rows) == 1
    row = rows[0]
    assert row["question_attribution"]["status"] == "recorded"
    assert row["question_attribution"]["basis"] == "recorded_on_observation_row"
    assert row["request"]["reason"] == "contested_at_squint_scale"
    assert row["request"]["provenance"]["reason"] == "recorded"
    assert row["state"]["attribution_scope"] == "single_procedure"
    assert row["state"]["before"]["outcome"] == "appearance_opposed"
    assert row["state"]["after"]["outcome"] == "appearance_supported"
    assert row["state"]["changed"] is True
    assert row["independent_agreement"]["status"] == "matches_independent_call"
    cat, info, agree = _row_category(row, "bounded_zoom")
    assert cat == "confirmed_resolution"
    assert info["status"] == "new_reading_obtained"
    assert agree["status"] == "matches_independent_call"

    # Retain into memory and recall from another study
    memory = retain_procedure_experiences({"revision": "parent", "cases": []}, [row])
    recalled = recall_procedure_experiences(
        memory,
        question="identity",
        subject="femur",
        kind="bounded_zoom",
        query_profile={"banks": {BANK: [2, 0, 1]}},
        query_context={"request_reason": "contested_at_squint_scale"},
        study_uid=OTHER_UID,
        exclude_same_study=True,
    )
    assert recalled["status"] == "recalled_confirmed_resolution"
    assert recalled["confirmed_resolution_row_ids"] == [row["row_id"]]

    # Same-study exclusion works
    recalled_same = recall_procedure_experiences(
        memory,
        question="identity",
        subject="femur",
        kind="bounded_zoom",
        query_profile={"banks": {BANK: [2, 0, 1]}},
        query_context={"request_reason": "contested_at_squint_scale"},
        study_uid=UID,
        exclude_same_study=True,
    )
    assert recalled_same["status"] == "no_precedent"
    assert recalled_same["confirmed_resolution_row_ids"] == []

    # Case 2: Reviewer rejected the candidate -> contradicts_independent_call
    rows_reject = experience_rows(
        study_record,
        source,
        labels={"calls": {}, "table_uids": {UID}},
        call_index=make_call_index("reject"),
    )
    cat_reject, _, agree_reject = _row_category(rows_reject[0], "bounded_zoom")
    assert agree_reject["status"] == "contradicts_independent_call"
    assert cat_reject == "contradicted_outcome"

    # Case 3: Identity remains unresolved after action -> obtained_reading_open
    study_unresolved = json.loads(json.dumps(study_record))
    study_unresolved["observations"][0]["after_identity_consumption"][
        "region_read_as_subject"
    ] = None
    study_unresolved["identity_consumption"]["objects"]["femur"][
        "region_read_as_subject"
    ] = None
    rows_open = experience_rows(
        study_unresolved,
        source,
        labels={"calls": {}, "table_uids": {UID}},
        call_index=make_call_index("confirm"),
    )
    cat_open, _, agree_open = _row_category(rows_open[0], "bounded_zoom")
    assert agree_open["status"] == "unresolved_after_action"
    assert cat_open == "obtained_reading_open"

    # Case 4: Unattributed identity look (lacks single_procedure attribution) -> outcome_unattributed
    study_unattributed = json.loads(json.dumps(study_record))
    study_unattributed["observations"][0]["attribution_scope"] = (
        "question_final_finding"
    )
    del study_unattributed["observations"][0]["before_state"]
    del study_unattributed["observations"][0]["after_state"]
    del study_unattributed["observations"][0]["request_id"]
    rows_unattr = experience_rows(
        study_unattributed,
        source,
        labels={"calls": {}, "table_uids": {UID}},
        call_index=make_call_index("confirm"),
    )
    cat_unattr, _, _ = _row_category(rows_unattr[0], "bounded_zoom")
    assert cat_unattr == "outcome_unattributed"


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
    from squint_training_fixture import make_training_raw_fixture

    make_training_raw_fixture(tmp_path / "raw", [UID, OTHER_UID])
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
            "calls": [
                {"candidate_id": case["case_id"], "call": "confirm", "views": [VIEW]}
            ],
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


def test_resume_after_child_publication_preserves_lineage_and_completed_work(
    round_inputs, monkeypatch
):
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
    assert (
        published.memory["parent_manifest_sha256"] == inputs["expected_memory_sha256"]
    )
    original_inode = (child_path / "manifest.json").stat().st_ino
    monkeypatch.setattr(cli, "_write_json", original_write)
    result = cli.run_round(**inputs)
    assert executions == [UID]
    assert result["studies"]["resumed"] == [UID]
    assert result["child_memory"]["manifest_sha256"] == published.sha256
    assert (child_path / "manifest.json").stat().st_ino == original_inode


def test_partial_resume_rejects_different_signed_content_even_with_the_same_case_ids(
    round_inputs,
):
    inputs, _executions = round_inputs
    cli.run_round(**inputs)
    output = inputs["output_path"]
    (output / "round-receipt.json").unlink()
    manifest_path = output / "memory" / "manifest.json"
    changed = json.loads(manifest_path.read_text())
    changed["cases"][0]["condition_calls"]["ACL"] = -1
    manifest_path.write_text(json.dumps(changed))
    with pytest.raises(
        cli.PrepareError, match="child_memory_checkpoint_content_mismatch"
    ):
        cli.run_round(**inputs)


def test_child_export_contains_new_visual_teaching_and_its_own_pin(round_inputs):
    inputs, executions = round_inputs
    new_case = object_case(OTHER_UID, "added-acl")
    additions = {
        "schema": cli.squint_visual_teaching.SCHEMA,
        "reader": "synthetic-test-reviewer",
        "cases": [new_case],
        "calls": [
            {
                "candidate_id": new_case["case_id"],
                "call": "confirm",
                "views": [VIEW],
                "notes": "Synthetic independently called support for publication test.",
            }
        ],
    }
    additions_path = inputs["output_path"].parent / "additions.json"
    additions_path.write_text(json.dumps(additions))
    result = cli.run_round(**inputs, visual_additions_path=additions_path)
    parent_corpus = json.loads(
        (inputs["output_path"] / "training" / "object-buckets.json").read_text()
    )
    child_corpus = json.loads(
        (inputs["output_path"] / "child-training" / "object-buckets.json").read_text()
    )
    assert len(parent_corpus["scoped_records"]) == 1
    assert len(child_corpus["scoped_records"]) == 2
    assert (
        child_corpus["teaching_memory"]["manifest_sha256"]
        == result["child_memory"]["manifest_sha256"]
    )
    added = next(
        r for r in child_corpus["scoped_records"] if r["case_id"] == "added-acl"
    )
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


def test_real_cli_resume_reports_the_child_material_without_reexecuting_studies(
    round_inputs, capsys
):
    inputs, executions = round_inputs
    expected = cli.run_round(**inputs)
    assert (
        cli.main(
            [
                "--run-round",
                "--memory",
                str(inputs["memory_path"]),
                "--memory-sha256",
                inputs["expected_memory_sha256"],
                "--root",
                str(inputs["root_path"]),
                "--study-uid",
                UID,
                "--labels",
                str(inputs["labels_path"]),
                "--child-revision",
                inputs["child_revision"],
                "--output",
                str(inputs["output_path"]),
            ]
        )
        == 0
    )
    returned = json.loads(capsys.readouterr().out)
    assert (
        returned["child_training"]["teaching_memory"]["manifest_sha256"]
        == expected["child_memory"]["manifest_sha256"]
    )
    assert returned["studies"] == {"requested": [UID], "executed": [], "resumed": [UID]}
    assert executions == [UID]
