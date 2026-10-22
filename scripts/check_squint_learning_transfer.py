"""Measure procedure transfer through real study inference; never borrow a teacher cue.

Runs the existing capacity entry point on identical raw studies under the parent,
child, and a labelled runtime ablation of the child's newly learned procedures.
The ablation changes no persistent memory and leaves every child case intact.
An absent transfer is a valid measured result, not a reason to manufacture one.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from knee.diagnosis.squint_memory import load_memory_snapshot
from knee.diagnosis.squint_memory_view import memory_view
from knee.diagnosis.squint_pipeline import run_squint_cli
from knee.json_store import load_json


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _source_identity() -> dict[str, str]:
    project = Path(__file__).resolve().parents[1]
    paths = sorted((project / "src" / "knee").rglob("*.py"))
    paths.extend(
        [Path(__file__).resolve(), project / "uv.lock", project / "pyproject.toml"]
    )
    return {str(path.relative_to(project)): _sha(path) for path in paths}


def _study_identity(root: Path, uid: str) -> dict[str, str]:
    if not uid or Path(uid).name != uid:
        raise ValueError("transfer_study_uid_invalid")
    candidates = [root / split / uid for split in ("train_series", "test_series")]
    directories = [path for path in candidates if path.is_dir()]
    if len(directories) != 1:
        raise ValueError("transfer_study_directory_missing_or_ambiguous:" + uid)
    files = sorted(path for path in directories[0].rglob("*") if path.is_file())
    if not files:
        raise ValueError("transfer_study_directory_empty:" + uid)
    files.extend(
        path
        for path in (root / "train_series.csv", root / "test_series.csv")
        if path.is_file()
    )
    return {str(path.relative_to(root)): _sha(path) for path in files}


def _experience_rows(memory: Mapping[str, Any]) -> list[dict]:
    return list(memory.get("procedure_experiences", {}).get("rows", ()))


def _state_summary(state: object) -> dict[str, Any] | None:
    if not isinstance(state, Mapping):
        return None
    fields = ("outcome", "reason", "value", "tier", "state", "code", "subject", "scope")
    result = {key: state[key] for key in fields if key in state}
    result["state_sha256"] = _digest(state)
    return result


def _action(row: Mapping[str, Any]) -> dict[str, Any]:
    cue = row.get("before_cue")
    recalled = row.get("recalled_procedure", {})
    return {
        "question": row.get("question"),
        "subject": row.get("subject"),
        "kind": row.get("request_kind", row.get("kind", "bounded_zoom")),
        "request_id": row.get("request_id"),
        "reason": row.get("request_reason", row.get("reason")),
        "code": row.get("code"),
        "before_cue_sha256": _digest(cue)
        if isinstance(cue, Mapping) and cue.get("banks")
        else None,
        "before_state": _state_summary(row.get("before_state")),
        "after_state": _state_summary(row.get("after_state")),
        "recalled_procedure": recalled,
    }


def _actions(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {"observation_index": index, **_action(row)}
        for index, row in enumerate(record.get("observations", ()))
        if isinstance(row, Mapping)
    ]


def _finding_summary(finding: Mapping[str, Any]) -> dict[str, Any]:
    evidence = finding.get("evidence", {})
    return {
        "outcome": finding.get("outcome"),
        "reason": finding.get("reason"),
        "decided_by": evidence.get("decided_by", []),
        "unresolved_subjects": evidence.get("unresolved_subjects", []),
        "readings": evidence.get("readings", {}),
    }


def transfer_assessment(
    child_actions: list[dict], ablated_actions: list[dict], new_row_ids: list[str]
) -> dict[str, Any]:
    """Describe actual recall/action evidence without equating annotation with effect."""
    new_ids = set(new_row_ids)
    heard = [
        row
        for row in child_actions
        if row.get("before_cue_sha256")
        and row.get("recalled_procedure", {}).get("status")
        == "recalled_confirmed_resolution"
        and new_ids.intersection(
            row.get("recalled_procedure", {}).get("confirmed_resolution_row_ids", ())
        )
    ]

    def signature(rows):
        return [
            (row.get("question"), row.get("subject"), row.get("kind"), row.get("code"))
            for row in rows
        ]

    if not heard:
        status = "no_new_confirmed_experience_consumed"
    elif signature(child_actions) == signature(ablated_actions):
        status = "recall_consumed_without_demonstrated_action_change"
    else:
        status = "new_experience_changed_real_action_sequence"
    return {"status": status, "heard_new_experiences": heard}


def _run_capacity(
    snapshot, root: Path, uids: list[str], output: Path, limit: float
) -> dict:
    args = SimpleNamespace(
        diagnostic_mode="capacity",
        diagnostic_memory=snapshot.path,
        diagnostic_output=output,
        root=root,
        study_uid=uids,
        workers=1,
        squint_time_limit=limit,
        draw=False,
    )
    receipt = run_squint_cli(args, prepared_memory_snapshot=snapshot)
    if receipt.get("memory_manifest_sha256") != snapshot.sha256:
        raise ValueError("transfer_entrypoint_memory_identity_mismatch")
    records = {}
    for item in receipt["work"]["studies"]:
        record_path = output / item["evidence_path"]
        record = load_json(record_path)
        uid = record.get("study_uid")
        excluded_uid = record.get("capacity_exclusion", {}).get("excluded_study_uid")
        if uid not in uids or excluded_uid != uid:
            raise ValueError("transfer_entrypoint_study_exclusion_mismatch")
        records[record["study_uid"]] = {
            "record_file": str(record_path.resolve()),
            "record_sha256": _sha(record_path),
            "study_status": record.get("study_status"),
            "capacity_exclusion": record.get("capacity_exclusion"),
            "actions": _actions(record),
            "findings": {
                q: _finding_summary(item["finding"])
                for q, item in record["questions"].items()
            },
        }
    return {"receipt": receipt, "records": records}


def run_check(
    parent: Path,
    child: Path,
    root: Path,
    uids: list[str],
    output: Path,
    *,
    limit: float = 900.0,
) -> dict:
    """Execute pinned parent/child inference and isolate the new procedure contribution."""
    if not uids or len(set(uids)) != len(uids):
        raise ValueError("transfer_requires_distinct_real_studies")
    output.mkdir(parents=True, exist_ok=False)
    sources = _source_identity()
    inputs = {uid: _study_identity(root, uid) for uid in uids}
    parent_snapshot = load_memory_snapshot(parent)
    if parent_snapshot.memory is None:
        raise ValueError("transfer_parent_memory_unavailable")
    parent_sha = parent_snapshot.sha256
    parent_manifest = parent_snapshot.path
    parent_ids = {row["row_id"] for row in _experience_rows(parent_snapshot.memory)}
    parent_run = _run_capacity(parent_snapshot, root, uids, output / "parent", limit)
    del parent_snapshot
    gc.collect()
    child_snapshot = load_memory_snapshot(child)
    child_memory = child_snapshot.memory
    if child_memory is None:
        raise ValueError("transfer_child_memory_unavailable")
    if child_memory.get("parent_manifest_sha256") != parent_sha:
        raise ValueError("transfer_child_does_not_extend_named_parent")
    rows = _experience_rows(child_memory)
    new_rows = [row for row in rows if row["row_id"] not in parent_ids]
    teacher_uids = sorted(
        {row.get("source", {}).get("study_uid") for row in new_rows} - {None}
    )
    if set(uids).intersection(teacher_uids):
        raise ValueError("transfer_query_is_new_experience_teaching_study")
    exclusions = {}
    for teacher in teacher_uids:
        excluded = memory_view(child_memory, exclude_study_uids=(teacher,))
        surviving = {row["row_id"] for row in _experience_rows(excluded)}
        removed = [
            row["row_id"]
            for row in new_rows
            if row.get("source", {}).get("study_uid") == teacher
        ]
        exclusions[teacher] = {
            "excluded_study_uids": excluded["view"]["excluded_study_uids"],
            "teacher_row_ids": removed,
            "surviving_teacher_row_ids": sorted(surviving.intersection(removed)),
        }
        del excluded
    child_run = _run_capacity(child_snapshot, root, uids, output / "child", limit)
    table = child_memory.get("procedure_experiences", {})
    ablated_memory = {
        **child_memory,
        "procedure_experiences": {
            **table,
            "rows": [row for row in rows if row["row_id"] in parent_ids],
        },
    }
    ablated_run = _run_capacity(
        replace(child_snapshot, memory=ablated_memory),
        root,
        uids,
        output / "child-without-new-procedure-experiences",
        limit,
    )
    ablated_run["runtime_override"] = {
        "scope": "new_procedure_experience_rows_only",
        "base_manifest_sha256": child_snapshot.sha256,
        "removed_row_ids": [row["row_id"] for row in new_rows],
        "persistent_memory_modified": False,
    }
    assessments = {
        uid: transfer_assessment(
            child_run["records"][uid]["actions"],
            ablated_run["records"][uid]["actions"],
            [row["row_id"] for row in new_rows],
        )
        for uid in uids
    }
    stable = (
        sources == _source_identity()
        and inputs == {uid: _study_identity(root, uid) for uid in uids}
        and _sha(parent_manifest) == parent_sha
        and _sha(child_snapshot.path) == child_snapshot.sha256
    )
    changed = [
        uid
        for uid, result in assessments.items()
        if result["status"] == "new_experience_changed_real_action_sequence"
    ]
    heard_keys = {
        (row["question"], row["subject"], row["kind"])
        for uid in changed
        for row in assessments[uid]["heard_new_experiences"]
    }
    controls = [
        uid
        for uid, result in assessments.items()
        if result["status"] == "no_new_confirmed_experience_consumed"
        and any(
            row.get("before_cue_sha256")
            and (row["question"], row["subject"], row["kind"]) in heard_keys
            for row in child_run["records"][uid]["actions"]
        )
    ]
    exclusion_failed = any(
        value["surviving_teacher_row_ids"] for value in exclusions.values()
    )
    status = (
        "stale_input"
        if not stable
        else "same_study_exclusion_failed"
        if exclusion_failed
        else "demonstrated_transfer_with_real_noninheriting_control"
        if changed and controls
        else "real_transfer_without_noninheriting_control"
        if changed
        else "no_demonstrated_transfer"
    )
    result = {
        "schema": "knee.real-learning-transfer/v1",
        "status": status,
        "source_files_sha256": sources,
        "study_files_sha256": inputs,
        "parent_manifest_sha256": parent_sha,
        "child_manifest_sha256": child_snapshot.sha256,
        "new_teacher_rows": [
            {
                "row_id": row["row_id"],
                "source": row.get("source"),
                "request": row.get("request"),
            }
            for row in new_rows
        ],
        "same_study_exclusion": exclusions,
        "parent": parent_run,
        "child": child_run,
        "child_runtime_ablation": ablated_run,
        "assessments": assessments,
        "changed_studies": changed,
        "noninheriting_context_control_studies": controls,
        "limits": [
            "A noninheriting study is an observed control, not a proof that every incompatible context is refused.",
            "The runtime ablation preserves child clinical cases and removes only newly learned procedure rows.",
            "Action-sequence change establishes use; clinical benefit still needs its appropriate independent outcome.",
        ],
    }
    (output / "transfer.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--child", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--study-uid", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--time-limit", type=float, default=900.0)
    args = parser.parse_args()
    result = run_check(
        args.parent,
        args.child,
        args.root,
        args.study_uid,
        args.output,
        limit=args.time_limit,
    )
    print(result["status"])
    print(args.output / "transfer.json")
    return (
        0
        if result["status"] == "demonstrated_transfer_with_real_noninheriting_control"
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
