"""Intent checks for the transfer reporter, not substitutes for real study runs."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from scripts import check_squint_learning_transfer as transfer
from scripts.check_squint_learning_transfer import transfer_assessment


def action(*, code="measured", row_id="new-teacher", cue="actual-study-cue"):
    return {
        "question": "Baker's",
        "subject": "bursa",
        "kind": "bounded_zoom",
        "code": code,
        "before_cue_sha256": cue,
        "recalled_procedure": {
            "status": "recalled_confirmed_resolution",
            "confirmed_resolution_row_ids": [row_id],
        },
    }


def test_actual_new_recall_and_changed_action_are_both_required():
    result = transfer_assessment([action()], [], ["new-teacher"])
    assert result["status"] == "new_experience_changed_real_action_sequence"
    assert result["heard_new_experiences"] == [action()]


def test_recall_annotation_does_not_prove_an_action_changed():
    result = transfer_assessment([action()], [action()], ["new-teacher"])
    assert result["status"] == "recall_consumed_without_demonstrated_action_change"


def test_preexisting_experience_does_not_prove_new_learning():
    result = transfer_assessment([action(row_id="old")], [], ["new-teacher"])
    assert result["status"] == "no_new_confirmed_experience_consumed"


def test_absent_pre_action_observation_cannot_claim_real_transfer():
    result = transfer_assessment([action(cue=None)], [], ["new-teacher"])
    assert result["status"] == "no_new_confirmed_experience_consumed"


def test_empty_context_is_not_a_measured_query():
    row = transfer._action({"before_cue": {"status": "located", "banks": {}}})
    assert row["before_cue_sha256"] is None


def test_unknown_or_negative_recall_cannot_claim_confirmed_recruitment():
    row = action()
    row["recalled_procedure"]["status"] = "no_context_compatible_experience"
    result = transfer_assessment([row], [], ["new-teacher"])
    assert result["status"] == "no_new_confirmed_experience_consumed"


def test_real_action_order_change_is_observable():
    first = action()
    second = {**action(row_id="old"), "subject": "another_actual_request"}
    result = transfer_assessment([first, second], [second, first], ["new-teacher"])
    assert result["status"] == "new_experience_changed_real_action_sequence"


def test_study_files_are_content_pinned(tmp_path):
    study = tmp_path / "train_series" / "study" / "series"
    study.mkdir(parents=True)
    image = study / "1.dcm"
    image.write_bytes(b"first actual bytes")
    before = transfer._study_identity(tmp_path, "study")
    image.write_bytes(b"different bytes")
    assert transfer._study_identity(tmp_path, "study") != before


@pytest.mark.parametrize("uid", ["", "../elsewhere", "not-present"])
def test_missing_or_invalid_study_is_not_an_empty_success(tmp_path, uid):
    with pytest.raises(ValueError):
        transfer._study_identity(tmp_path, uid)


def test_one_study_cannot_be_repeated_as_its_own_control(tmp_path):
    with pytest.raises(ValueError, match="distinct_real_studies"):
        transfer.run_check(
            tmp_path, tmp_path, tmp_path, ["same", "same"], tmp_path / "out"
        )


def test_action_cue_comes_from_its_own_before_record():
    observed = {"subject": "bursa", "banks": {"real-bank": [1, 2, 3]}}
    recorded = transfer._action(
        {"before_cue": observed, "profile": {"banks": {"later": [9, 9, 9]}}}
    )
    assert recorded["before_cue_sha256"] == transfer._digest(observed)


def test_real_capacity_entrypoint_and_exclusion_are_used(tmp_path, monkeypatch):
    snapshot = SimpleNamespace(path=tmp_path / "manifest.json", sha256="manifest-sha")

    def capacity(args, *, prepared_memory_snapshot):
        assert args.diagnostic_mode == "capacity"
        assert args.study_uid == ["query-study"]
        assert prepared_memory_snapshot is snapshot
        args.diagnostic_output.mkdir()
        record_path = args.diagnostic_output / "record.json"
        record_path.write_text(
            json.dumps(
                {
                    "study_uid": "query-study",
                    "study_status": "examined",
                    "capacity_exclusion": {"excluded_study_uid": "query-study"},
                    "observations": [],
                    "questions": {},
                }
            )
        )
        return {
            "memory_manifest_sha256": snapshot.sha256,
            "work": {"studies": [{"evidence_path": "record.json"}]},
        }

    monkeypatch.setattr(transfer, "run_squint_cli", capacity)
    result = transfer._run_capacity(
        snapshot, tmp_path, ["query-study"], tmp_path / "actual-entry", 30
    )
    assert (
        result["records"]["query-study"]["capacity_exclusion"]["excluded_study_uid"]
        == "query-study"
    )
    assert result["records"]["query-study"]["record_sha256"]


def test_entrypoint_cannot_silently_consume_another_memory(tmp_path, monkeypatch):
    snapshot = SimpleNamespace(path=tmp_path / "manifest.json", sha256="wanted")
    monkeypatch.setattr(
        transfer, "run_squint_cli", lambda *a, **k: {"memory_manifest_sha256": "other"}
    )
    with pytest.raises(ValueError, match="memory_identity_mismatch"):
        transfer._run_capacity(snapshot, tmp_path, ["query"], tmp_path / "out", 30)


def test_report_does_not_copy_large_comparison_tables():
    summary = transfer._finding_summary(
        {
            "outcome": "open",
            "reason": "unresolved",
            "evidence": {"decided_by": [], "readings": {"bursa": {"state": "unknown"}}},
            "recall_evidence": {
                "large": "complete tables stay in the pinned source record"
            },
        }
    )
    assert summary["outcome"] == "open"
    assert summary["readings"]["bursa"]["state"] == "unknown"
    assert "recall_evidence" not in summary


def test_action_state_is_addressed_and_hashed_without_copying_full_profiles():
    state = {
        "outcome": "open",
        "reason": "identity contested",
        "profile": {"large": [1, 2, 3]},
    }
    rows = transfer._actions({"observations": [{"before_state": state}]})
    assert rows[0]["observation_index"] == 0
    assert rows[0]["before_state"]["state_sha256"] == transfer._digest(state)
    assert "profile" not in rows[0]["before_state"]
