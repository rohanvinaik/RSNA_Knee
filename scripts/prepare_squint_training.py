"""Export reviewed object buckets and pinned procedure experiences for training."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import tempfile
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from knee.diagnosis import (
    squint_configurations,
    squint_corpus,
    squint_procedure_memory,
    squint_visual_teaching,
)
from knee.diagnosis.squint_identity import (
    identity_condition_views,
    prepare_identity,
)
from knee.diagnosis.squint_locator import prepare_recall
from knee.diagnosis.squint_memory import (
    MemorySnapshot,
    SquintMemoryError,
    carry_condition_calls,
    load_memory_snapshot,
    save_memory,
)
from knee.diagnosis.squint_memory_view import memory_view
from knee.diagnosis.squint_pipeline import infer_study
from knee.diagnosis.squint_reports import (
    ReportCallError,
    import_report_calls,
    read_reports,
)
from knee.diagnosis.squint_training_pins import (
    archive_study_inventory,
    checkpoint_identity_code,
    training_source_identity,
    verified_study_input,
)
from knee.json_store import dump_json_atomic, load_json, resolve_json_path
from knee.study.tables import LABELS

try:
    from scripts.squint_round_composition import stage_identity_growth
except ModuleNotFoundError as error:
    if error.name != "scripts":
        raise
    from squint_round_composition import stage_identity_growth

RECEIPT_SCHEMA = "knee.squint-procedure-experiences/v1"
ROUND_RECEIPT_SCHEMA = "knee.squint-training-round/v1"
ROUND_INPUTS_SCHEMA = "knee.squint-training-round-inputs/v1"
STUDY_PIN_SCHEMA = "knee.squint-study-checkpoint-pin/v1"
RUN_SCHEMA = "knee.squint-run/v1"
STUDY_SCHEMA = "knee.squint-study/v1"
_RUNTIME_MEMORY_KEYS = {
    "full_profile_retention",
    "view",
    "prepared_recall",
    "memory_manifest_sha256",
}


class PrepareError(ValueError):
    """A named refusal to retain procedure experience from invalid inputs."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path, code: str) -> str:
    try:
        return _sha256_bytes(path.read_bytes())
    except OSError as error:
        raise PrepareError(code) from error


def _stable_json(path: Path, code: str) -> tuple[Any, Path, str]:
    actual = resolve_json_path(path).resolve()
    try:
        before = _sha256_file(actual, code + "_unreadable")
        value = load_json(path)
        after = _sha256_file(actual, code + "_unreadable")
    except (OSError, UnicodeError, ValueError, EOFError) as error:
        if isinstance(error, PrepareError):
            raise
        raise PrepareError(code + "_malformed") from error
    if before != after:
        raise PrepareError(code + "_changed_during_read")
    return value, actual, before


def _inside(path: Path, root: Path, code: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise PrepareError(code) from error
    return resolved


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "\0" not in value


def _sha256_text(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _validate_run_receipt(receipt: object) -> tuple[list[Any], str, str]:
    if not isinstance(receipt, Mapping):
        raise PrepareError("run_receipt_not_object")
    work = receipt.get("work")
    entries = work.get("studies") if isinstance(work, Mapping) else None
    if (
        receipt.get("schema") != RUN_SCHEMA
        or receipt.get("action") not in ("infer", "capacity")
        or receipt.get("source_mode") != "raw_squint_case_recall"
    ):
        raise PrepareError("run_receipt_not_completed_inference")
    if not isinstance(entries, list):
        raise PrepareError("run_receipt_studies_invalid")
    if not entries:
        raise PrepareError("run_studies_empty")
    revision = receipt.get("memory_revision")
    memory_sha = receipt.get("memory_manifest_sha256")
    if not _text(revision) or not _sha256_text(memory_sha):
        raise PrepareError("run_memory_identity_invalid")
    return entries, str(revision), str(memory_sha)


def _index_run_entry(
    item: object,
    run: Path,
    seen: set[str],
) -> dict[str, str]:
    if not isinstance(item, Mapping):
        raise PrepareError("run_study_entry_invalid")
    uid = item.get("study_uid")
    evidence = item.get("evidence_path")
    if not _text(uid) or Path(uid).name != uid or not _text(evidence):
        raise PrepareError("run_study_entry_invalid")
    if uid in seen:
        raise PrepareError("run_study_uid_duplicate:" + uid)
    seen.add(uid)
    logical = _inside(run / evidence, run, "study_evidence_outside_run:" + uid)
    actual = _inside(
        resolve_json_path(logical), run, "study_evidence_outside_run:" + uid
    )
    return {
        "study_uid": str(uid),
        "evidence_path": str(actual.relative_to(run)),
        "actual_path": str(actual),
    }


def _run_index(
    run_path: Path,
) -> tuple[dict[str, Any], Path, str, list[dict[str, str]]]:
    run = run_path.resolve()
    if not run.is_dir():
        raise PrepareError("run_directory_missing")
    receipt_path = _inside(run / "receipt.json", run, "run_receipt_outside_run")
    receipt, actual_receipt, receipt_sha = _stable_json(receipt_path, "run_receipt")
    entries, revision, memory_sha = _validate_run_receipt(receipt)
    seen: set[str] = set()
    indexed = [_index_run_entry(item, run, seen) for item in entries]
    identity = {
        "path": str(run),
        "receipt_path": str(actual_receipt),
        "receipt_sha256": receipt_sha,
        "action": receipt["action"],
        "source_mode": receipt["source_mode"],
        "memory_revision": revision,
        "memory_manifest_sha256": memory_sha,
        "study_count": len(indexed),
    }
    return identity, run, revision, indexed


def _source_record(
    run: Mapping[str, Any], entry: Mapping[str, str], record_sha: str
) -> dict[str, str]:
    return {
        "run": str(run["path"]),
        "record_file": str(entry["evidence_path"]),
        "record_sha256": record_sha,
        # These two identify the memory that produced this inference record, not
        # the reviewed memory whose calls are consulted as independent evidence.
        "memory_sha256": str(run["memory_manifest_sha256"]),
        "memory_revision": str(run["memory_revision"]),
    }


def _write_json(path: Path, value: object) -> None:
    try:
        text = json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (TypeError, ValueError, OverflowError) as error:
        raise PrepareError("output_not_finite_json") from error
    path.write_text(text + "\n", encoding="utf-8")


def _load_verified_teaching_memory(
    memory_path: Path,
    expected_memory_sha256: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        snapshot = load_memory_snapshot(memory_path)
    except SquintMemoryError as error:
        raise PrepareError("teaching_memory_" + error.code) from error
    memory = snapshot.memory
    if memory is None or snapshot.sha256 is None:
        raise PrepareError("teaching_memory_unavailable")
    if snapshot.sha256 != expected_memory_sha256:
        raise PrepareError("teaching_memory_sha256_mismatch")
    teaching_identity = {
        "path": str(snapshot.path.parent),
        "revision": memory["revision"],
        "manifest_sha256": snapshot.sha256,
    }
    return memory, teaching_identity


def _report_call_pins(paths: Sequence[Path]) -> list[dict[str, Any]]:
    """Pin the exact optional clinical call documents, without interpreting them."""
    resolved = [path.resolve() for path in paths]
    if len(set(resolved)) != len(resolved):
        raise PrepareError("report_call_source_repeated")
    return [
        {
            "path": str(path),
            "sha256": _sha256_file(path, "report_calls_unreadable"),
        }
        for path in resolved
    ]


def _verified_report_calls(
    labels_file: Path, pins: Sequence[Mapping[str, Any]]
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Keep verified signed/conflicting calls at their actual study/question scope."""
    if not pins:
        return {}
    try:
        reports = read_reports(labels_file)
        calls: dict[str, dict[str, list[dict[str, Any]]]] = {}
        seen: set[str] = set()
        for pin in pins:
            path = Path(str(pin["path"]))
            entries = import_report_calls(path, reports)
            if _sha256_file(path, "report_calls_unreadable") != pin["sha256"]:
                raise PrepareError("report_calls_changed_during_read")
            for entry in entries:
                status = entry["status"]
                if status not in (
                    "signed",
                    "contradictory",
                    "duplicate",
                    "abstention",
                    "needs_review",
                ):
                    raise PrepareError("report_call_refused:" + str(status))
                if status not in ("signed", "contradictory"):
                    continue
                call_id = entry["call_id"]
                if call_id in seen:
                    continue
                seen.add(call_id)
                calls.setdefault(entry["study_uid"], {}).setdefault(
                    entry["question"], []
                ).append({**entry, "call_document": dict(pin)})
        return calls
    except ReportCallError as error:
        raise PrepareError("report_calls_" + error.reason) from error


def _load_labels_and_corpus(
    memory: Mapping[str, Any],
    teaching_identity: Mapping[str, Any],
    labels_path: Path,
    report_call_paths: Sequence[Path] = (),
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    labels_file = labels_path.resolve()
    try:
        labels_bytes = labels_file.read_bytes()
        labels_text = labels_bytes.decode("utf-8-sig")
    except FileNotFoundError as error:
        raise PrepareError("labels_missing") from error
    except (OSError, UnicodeDecodeError) as error:
        raise PrepareError("labels_unreadable") from error
    labels = squint_procedure_memory.read_label_table(labels_text)
    if not labels["table_uids"]:
        raise PrepareError("labels_empty")
    labels_identity = {
        "path": str(labels_file),
        "sha256": _sha256_bytes(labels_bytes),
        "bytes": len(labels_bytes),
        "study_count": len(labels["table_uids"]),
    }
    report_pins = _report_call_pins(report_call_paths)
    if report_pins:
        labels_identity["report_calls"] = report_pins
        labels["report_calls"] = _verified_report_calls(labels_file, report_pins)
    labels["source"] = labels_identity
    labels_by_uid = {
        uid: {question: int(value == 1) for question, value in row.items()}
        for uid, row in labels["calls"].items()
    }
    corpus = squint_corpus.reviewed_object_buckets(
        memory, labels_by_uid, labels_identity
    )
    if corpus.get("outcome") != "classified":
        raise PrepareError("object_buckets_" + str(corpus.get("reason", "unavailable")))
    corpus["teaching_memory"] = dict(teaching_identity)
    return labels, labels_identity, corpus


def _index_all_runs(
    run_paths: Sequence[Path],
) -> tuple[
    list[dict[str, Any]],
    list[tuple[dict[str, Any], Path, str, list[dict[str, str]]]],
]:
    run_identities: list[dict[str, Any]] = []
    seen_runs: set[str] = set()
    indexed_runs: list[tuple[dict[str, Any], Path, str, list[dict[str, str]]]] = []
    for run_path in run_paths:
        identity, run, revision, entries = _run_index(run_path)
        if identity["path"] in seen_runs:
            raise PrepareError("run_repeated")
        seen_runs.add(identity["path"])
        indexed_runs.append((identity, run, revision, entries))
        run_identities.append(identity)
    return run_identities, indexed_runs


def _code_identity() -> dict[str, Any]:
    return training_source_identity(Path(__file__).resolve().parents[1])


def _load_study_record(
    run: Mapping[str, Any],
    revision: str,
    entry: Mapping[str, str],
) -> tuple[Mapping[str, Any], Path, str]:
    uid = entry["study_uid"]
    run_root = Path(run["path"])
    record_path = _inside(
        Path(entry["actual_path"]),
        run_root,
        "study_evidence_outside_run:" + uid,
    )
    record, actual, record_sha = _stable_json(record_path, "study_record:" + uid)
    actual = _inside(actual, run_root, "study_evidence_outside_run:" + uid)
    if not isinstance(record, Mapping) or record.get("schema") != STUDY_SCHEMA:
        raise PrepareError("study_record_schema_invalid:" + uid)
    if record.get("study_uid") != uid:
        raise PrepareError("study_record_uid_mismatch:" + uid)
    if record.get("memory_revision") != revision:
        raise PrepareError("study_record_memory_revision_mismatch:" + uid)
    return record, actual, record_sha


def _write_experience_rows(
    rows_path: Path,
    indexed_runs: Sequence[tuple[dict[str, Any], Path, str, list[dict[str, str]]]],
    *,
    labels: Mapping[str, Any],
    call_index: Mapping[str, Any],
) -> tuple[Counter[str], Counter[str], Counter[str]]:
    counts: Counter[str] = Counter()
    outcome_counts: Counter[str] = Counter()
    attribution_counts: Counter[str] = Counter()
    with rows_path.open("x", encoding="utf-8") as stream:
        for run, _root, revision, entries in indexed_runs:
            for entry in entries:
                record, actual, record_sha = _load_study_record(run, revision, entry)
                rows = squint_procedure_memory.experience_rows(
                    record,
                    _source_record(run, entry, record_sha),
                    labels=labels,
                    call_index=call_index,
                )
                counts["studies"] += 1
                counts["records"] += 1
                for row in rows:
                    try:
                        encoded = json.dumps(
                            row,
                            sort_keys=True,
                            ensure_ascii=False,
                            allow_nan=False,
                            separators=(",", ":"),
                        )
                    except (TypeError, ValueError, OverflowError) as error:
                        raise PrepareError(
                            "experience_row_not_finite_json:" + entry["study_uid"]
                        ) from error
                    stream.write(encoded + "\n")
                    counts["rows"] += 1
                    outcome_counts[str(row["independent_outcome"]["status"])] += 1
                    attribution_counts[str(row["question_attribution"]["status"])] += 1
                run.setdefault("records", []).append(
                    {
                        "study_uid": entry["study_uid"],
                        "evidence_path": entry["evidence_path"],
                        "actual_path": str(actual),
                        "sha256": record_sha,
                        "rows": len(rows),
                        "study_status": record.get("study_status"),
                    }
                )
    return counts, outcome_counts, attribution_counts


def prepare(
    *,
    memory_path: Path,
    expected_memory_sha256: str,
    run_paths: Sequence[Path],
    labels_path: Path,
    output_path: Path,
    report_call_paths: Sequence[Path] = (),
) -> dict[str, Any]:
    """Write reviewed buckets, experience rows, and pins into a fresh directory."""
    if output_path.exists() or output_path.is_symlink():
        raise PrepareError("output_already_exists")
    output = output_path.resolve()
    if not output.parent.is_dir():
        raise PrepareError("output_parent_missing")
    if not run_paths:
        raise PrepareError("run_inputs_missing")
    if not _sha256_text(expected_memory_sha256):
        raise PrepareError("memory_sha256_invalid")

    memory, teaching_identity = _load_verified_teaching_memory(
        memory_path, expected_memory_sha256
    )
    labels, labels_identity, corpus = _load_labels_and_corpus(
        memory, teaching_identity, labels_path, report_call_paths
    )
    call_index = squint_procedure_memory.build_call_index(memory)
    run_identities, indexed_runs = _index_all_runs(run_paths)
    code_identity = _code_identity()

    staging = Path(tempfile.mkdtemp(prefix=".squint-training-", dir=output.parent))
    try:
        _write_json(staging / "object-buckets.json", corpus)
        counts, outcome_counts, attribution_counts = _write_experience_rows(
            staging / "procedure-experiences.jsonl",
            indexed_runs,
            labels=labels,
            call_index=call_index,
        )
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "inputs": {
                "teaching_memory": teaching_identity,
                "labels": labels_identity,
                "runs": run_identities,
            },
            "code": code_identity,
            "output_sha256": {
                name: _sha256_file(staging / name, "training_output_unreadable")
                for name in ("object-buckets.json", "procedure-experiences.jsonl")
            },
            "outputs": {
                "object_buckets_file": "object-buckets.json",
                "object_cases": len(corpus["scoped_records"]),
                "object_states": dict(
                    sorted(
                        Counter(
                            row["state"]["status"] for row in corpus["scoped_records"]
                        ).items()
                    )
                ),
                "experience_file": "procedure-experiences.jsonl",
                **dict(sorted(counts.items())),
                "checked": outcome_counts["checked"],
                "unchecked": outcome_counts["unchecked"],
                "independent_outcomes": dict(sorted(outcome_counts.items())),
                "question_attribution": dict(sorted(attribution_counts.items())),
            },
            "scope": {
                "labels_supply_independent_object_states_and_outcomes": True,
                "labels_are_not_image_features": True,
                "images_read": False,
                "procedure_proposal_or_learning": False,
                "inference_memory_pins_are_distinct_from_teaching_memory": True,
            },
        }
        _write_json(staging / "receipt.json", receipt)
        if output.exists() or output.is_symlink():
            raise PrepareError("output_already_exists")
        os.rename(staging, output)
        return receipt
    except BaseException:
        if staging.exists():
            for path in staging.iterdir():
                path.unlink(missing_ok=True)
            staging.rmdir()
        raise


def _training_export(
    *,
    memory_path: Path,
    expected_memory_sha256: str,
    inference_dir: Path,
    labels_path: Path,
    output_path: Path,
    report_call_paths: Sequence[Path] = (),
) -> dict[str, Any]:
    """Reuse only a complete export with identical inputs, code and output bytes."""
    if not output_path.exists() and not output_path.is_symlink():
        return prepare(
            memory_path=memory_path,
            expected_memory_sha256=expected_memory_sha256,
            run_paths=[inference_dir],
            labels_path=labels_path,
            output_path=output_path,
            report_call_paths=report_call_paths,
        )
    if output_path.is_symlink() or not (output_path / "receipt.json").is_file():
        raise PrepareError("training_checkpoint_invalid")
    receipt, _actual, _sha = _stable_json(
        output_path / "receipt.json", "training_receipt"
    )
    runs, indexed = _index_all_runs([inference_dir])
    saved_runs = _mapping_get(receipt, "inputs", "runs")
    run_headers = (
        [
            {key: value for key, value in run.items() if key != "records"}
            for run in saved_runs
        ]
        if isinstance(saved_runs, list)
        and all(isinstance(run, Mapping) for run in saved_runs)
        else None
    )
    if (
        not isinstance(receipt, Mapping)
        or receipt.get("schema") != RECEIPT_SCHEMA
        or _mapping_get(receipt, "inputs", "teaching_memory", "manifest_sha256")
        != expected_memory_sha256
        or _mapping_get(receipt, "inputs", "labels", "sha256")
        != _sha256_file(labels_path.resolve(), "labels_unreadable")
        or (_mapping_get(receipt, "inputs", "labels", "report_calls") or [])
        != _report_call_pins(report_call_paths)
        or run_headers != runs
        or receipt.get("code") != _code_identity()
    ):
        raise PrepareError("training_checkpoint_mismatch")
    for saved_run, (_identity, root, _revision, entries) in zip(
        saved_runs, indexed, strict=True
    ):
        records = saved_run.get("records")
        if not isinstance(records, list) or len(records) != len(entries):
            raise PrepareError("training_checkpoint_mismatch")
        for record, entry in zip(records, entries, strict=True):
            if (
                not isinstance(record, Mapping)
                or record.get("study_uid") != entry["study_uid"]
                or record.get("evidence_path") != entry["evidence_path"]
                or record.get("sha256")
                != _sha256_file(
                    _inside(
                        root / entry["evidence_path"],
                        root,
                        "study_evidence_outside_run",
                    ),
                    "study_record_unreadable",
                )
            ):
                raise PrepareError("training_checkpoint_mismatch")
    for name in ("object-buckets.json", "procedure-experiences.jsonl"):
        if _mapping_get(receipt, "output_sha256", name) != _sha256_file(
            output_path / name, "training_checkpoint_output_missing"
        ):
            raise PrepareError("training_checkpoint_output_mismatch")
    return dict(receipt)


def _memory_content_sha256(memory: Mapping[str, Any]) -> str:
    """Exact semantic child content; publication-derived/runtime metadata is excluded."""
    content = {
        key: value for key, value in memory.items() if key not in _RUNTIME_MEMORY_KEYS
    }
    return _sha256_bytes(
        json.dumps(
            content, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    )


def _study_pin_payload(
    *,
    uid: str,
    memory_manifest_sha256: str,
    memory_revision: str,
    code_identity: Mapping[str, Any],
    study_input: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema": STUDY_PIN_SCHEMA,
        "study_uid": uid,
        "memory_manifest_sha256": memory_manifest_sha256,
        "memory_revision": memory_revision,
        "exclude_same_study": True,
        "code": dict(code_identity),
        "study_input": dict(study_input),
    }


def _try_resume_study_record(
    studies_dir: Path,
    inference_dir: Path,
    uid: str,
    expected_pin: Mapping[str, Any],
) -> dict[str, str] | None:
    candidate = resolve_json_path(studies_dir / f"{uid}.json.xz")
    pin_path = studies_dir / f"{uid}.pin.json"
    if not candidate.exists() and not pin_path.exists():
        return None
    if not candidate.exists() or not pin_path.exists():
        raise PrepareError("study_checkpoint_pin_mismatch:" + uid)
    record, actual, record_sha = _stable_json(candidate, "study_record:" + uid)
    pin_doc, _actual_pin, _pin_sha = _stable_json(pin_path, "study_pin:" + uid)
    if (
        not isinstance(record, Mapping)
        or record.get("schema") != STUDY_SCHEMA
        or record.get("study_uid") != uid
        or record.get("memory_revision") != expected_pin["memory_revision"]
        or not isinstance(pin_doc, Mapping)
    ):
        raise PrepareError("study_checkpoint_pin_mismatch:" + uid)
    expected_with_record = {
        **expected_pin,
        "record_file": str(actual.relative_to(inference_dir)),
        "record_sha256": record_sha,
    }
    disposition = checkpoint_identity_code(expected_with_record, dict(pin_doc))
    if disposition != "checkpoint_pin_identical":
        raise PrepareError(disposition + ":" + uid)
    return {
        "study_uid": uid,
        "evidence_path": str(actual.relative_to(inference_dir)),
    }


def _pin_round_inputs(output: Path, round_inputs: Mapping[str, Any]) -> None:
    inputs_path = output / "round-inputs.json"
    if inputs_path.exists():
        existing, _actual, _sha = _stable_json(inputs_path, "round_inputs")
        if isinstance(existing, Mapping):
            if existing.get("study_uids") != round_inputs.get("study_uids"):
                raise PrepareError("round_inputs_mismatch")
            if existing.get("code") != round_inputs.get("code"):
                raise PrepareError("round_source_changed_use_fresh_output")
            if existing.get("study_inputs") != round_inputs.get("study_inputs"):
                raise PrepareError("round_study_input_changed")
        if not isinstance(existing, Mapping) or dict(existing) != dict(round_inputs):
            raise PrepareError("round_inputs_mismatch")
        return
    if output.exists() and any(output.iterdir()):
        raise PrepareError("round_root_not_fresh")
    output.mkdir(parents=True, exist_ok=True)
    _write_json(inputs_path, dict(round_inputs))


def _compose_round_teaching(
    parent_memory: Mapping[str, Any],
    parent_sha256: str,
    *,
    labels: Mapping[str, Any],
    labels_identity: Mapping[str, Any],
    visual_additions_path: Path | None,
    round_name: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Incorporate visual object additions, carry clinical meanings, and rebuild configurations."""
    working: dict[str, Any] = {
        key: copy.deepcopy(value)
        for key, value in parent_memory.items()
        if key not in _RUNTIME_MEMORY_KEYS
    }
    added_visual_case_ids: list[str] = []
    carried_condition_case_ids: list[str] = []
    rebuilt_configuration_case_ids: list[str] = []
    touched_studies: set[str] = set()

    if visual_additions_path is not None:
        addition_file = visual_additions_path.resolve()
        try:
            addition_bytes = addition_file.read_bytes()
            additions = json.loads(addition_bytes.decode("utf-8"))
        except (OSError, UnicodeDecodeError, ValueError) as error:
            raise PrepareError("visual_additions_unreadable") from error
        try:
            new_cases, new_calls = squint_visual_teaching.validate_additions(
                working, additions
            )
        except squint_visual_teaching.VisualTeachingError as error:
            raise PrepareError(f"visual_additions_{error.code}") from error
        digest = _sha256_bytes(addition_bytes)
        provenance = {
            "schema": squint_visual_teaching.SCHEMA,
            "kind": "independent_direct_visual_teaching",
            "reader": additions["reader"],
            "parent_manifest_sha256": parent_sha256,
            "additions_sha256": digest,
            "additions_source": str(addition_file),
            "case_ids": [case["case_id"] for case in new_cases],
            "calls": new_calls,
            "configuration_extension": "rebuilt_in_round",
        }
        working = squint_visual_teaching.apply_validated_additions(
            working, new_cases, new_calls, provenance
        )
        for case, call in zip(new_cases, new_calls, strict=True):
            added_visual_case_ids.append(str(case["case_id"]))
            if call["call"] == "confirm":
                touched_studies.add(str(case["study_uid"]))
        if prepare_identity(working).get("outcome") != "prepared":
            raise PrepareError("visual_additions_identity_preparation_failed")

    teaching_block = working.get("object_identity_teaching")
    if isinstance(teaching_block, Mapping):
        scope = identity_condition_views(working)
        if scope.get("outcome") == "scoped":
            label_calls_by_uid = labels.get("calls", {})
            complete_rows_by_uid: dict[str, dict[str, int | None]] = {}
            for uid, row in label_calls_by_uid.items():
                if isinstance(row, Mapping) and all(
                    row.get(q) in (-1, 1) for q in LABELS
                ):
                    complete_rows_by_uid[str(uid)] = {
                        q: int(row[q] == 1) for q in LABELS
                    }
            label_ref = {
                "source": "train.csv",
                "source_path": str(labels_identity["path"]),
                "source_sha256": str(labels_identity["sha256"]),
            }
            identity_sources = scope.get("identity_sources", {})
            for case in working.get("cases", []):
                if not isinstance(case, dict):
                    continue
                subject = str(case.get("subject", ""))
                if (
                    subject.startswith("diagnosis/")
                    or case.get("question_reference") is not None
                ):
                    continue
                cid = str(case.get("case_id", ""))
                uid = str(case.get("study_uid", ""))
                if cid not in scope["views"] or uid not in complete_rows_by_uid:
                    continue
                source_id = identity_sources.get(cid, cid)
                call_rows = scope["calls"].get(source_id, ())
                if not call_rows:
                    continue
                try:
                    carried = carry_condition_calls(
                        case, call_rows[0], complete_rows_by_uid[uid]
                    )
                except SquintMemoryError as error:
                    raise PrepareError(f"condition_carry_{error.code}") from error
                calls_map = dict(carried["condition_calls"])
                existing_calls = dict(case.get("condition_calls") or {})
                new_calls = {
                    q: v for q, v in calls_map.items() if q not in existing_calls
                }
                if new_calls:
                    case["condition_calls"] = {**existing_calls, **new_calls}
                    scopes = dict(case.get("presentation_scope") or {})
                    scopes.update(
                        {q: carried["presentation_scope"][q] for q in new_calls}
                    )
                    case["presentation_scope"] = scopes
                    case.setdefault("label_attribution", {})
                    case["label_attribution"].update(
                        {
                            question: {
                                **label_ref,
                                "study_uid": uid,
                                "condition": question,
                                "column": question,
                            }
                            for question in new_calls
                        }
                    )
                    carried_condition_case_ids.append(cid)
                    touched_studies.add(uid)

            rebuild_uids = sorted(
                uid for uid in touched_studies if uid in complete_rows_by_uid
            )
            if rebuild_uids:
                built_by = {
                    "kind": "training_round_teaching",
                    "round": round_name,
                    "parent_manifest_sha256": parent_sha256,
                }
                try:
                    rebuilt = squint_configurations.rebuild_study_configurations(
                        working,
                        rebuild_uids,
                        built_by=built_by,
                        labels={uid: complete_rows_by_uid[uid] for uid in rebuild_uids},
                        label_source=label_ref,
                    )
                    working = squint_configurations.apply_rebuilt_configurations(
                        working, rebuilt
                    )
                except squint_configurations.ConfigurationProfileError as error:
                    raise PrepareError(f"configuration_rebuild_{error.code}") from error
                rebuilt_configuration_case_ids = [
                    str(c["case_id"]) for c in rebuilt["cases"]
                ]

    summary = {
        "added_visual_case_ids": added_visual_case_ids,
        "carried_condition_case_ids": carried_condition_case_ids,
        "rebuilt_configuration_case_ids": rebuilt_configuration_case_ids,
        "rebuilt_study_uids": sorted(touched_studies),
    }
    return working, summary


def run_round(
    *,
    memory_path: Path,
    expected_memory_sha256: str,
    root_path: Path,
    study_uids: Sequence[str],
    labels_path: Path,
    output_path: Path,
    child_revision: str | None = None,
    visual_additions_path: Path | None = None,
    reviewed_growth_memory_path: Path | None = None,
    growth_review_mode: str = "first-round",
    infer_fn: Callable[..., Mapping[str, Any]] | None = None,
    source_archive_path: Path | None = None,
    study_inventories: Mapping[str, Mapping[str, Mapping[str, Any]]] | None = None,
    report_call_paths: Sequence[Path] = (),
) -> dict[str, Any]:
    """Run one resumable local round: checkpoint studies, export experiences, and publish child memory."""
    if growth_review_mode not in ("first-round", "spot-check"):
        raise PrepareError("growth_review_mode_invalid")
    if output_path.is_symlink():
        raise PrepareError("output_symlink_refused")
    output = output_path.resolve()
    if not output.parent.is_dir():
        raise PrepareError("output_parent_missing")
    if not study_uids:
        raise PrepareError("study_uids_missing")
    if not _sha256_text(expected_memory_sha256):
        raise PrepareError("memory_sha256_invalid")

    ordered_uids: list[str] = []
    seen_uids: set[str] = set()
    for uid in study_uids:
        if not _text(uid) or Path(uid).name != uid:
            raise PrepareError("study_uid_invalid")
        if uid not in seen_uids:
            seen_uids.add(uid)
            ordered_uids.append(str(uid))

    # A directory's current subset cannot certify extraction completeness.
    # The ZIP central directory supplies expected files without reading its images.
    if study_inventories is None:
        source_archive = source_archive_path or root_path.with_suffix(".zip")
        if not source_archive.is_file():
            raise PrepareError("study_readiness_unknown_supply_source_archive")
        study_inventories = archive_study_inventory(source_archive, ordered_uids)
    cache_directory = output.parent / ".squint-study-input-digests"
    study_inputs = {}
    for uid in ordered_uids:
        measured_input = verified_study_input(
            root_path,
            uid,
            expected_files=study_inventories.get(uid),
            cache_directory=cache_directory,
        )
        study_inputs[uid] = {
            key: measured_input[key]
            for key in ("schema", "study_uid", "split", "sha256")
        }

    memory, teaching_identity = _load_verified_teaching_memory(
        memory_path, expected_memory_sha256
    )
    labels, labels_identity, _initial_corpus = _load_labels_and_corpus(
        memory, teaching_identity, labels_path, report_call_paths
    )
    code_identity = _code_identity()
    next_revision = child_revision or f"{memory['revision']}-round-{output.name}"
    visual_pin = None
    if visual_additions_path is not None:
        resolved_visual = visual_additions_path.resolve()
        visual_pin = {
            "path": str(resolved_visual),
            "sha256": _sha256_file(resolved_visual, "visual_additions_unreadable"),
        }
    round_inputs = {
        "schema": ROUND_INPUTS_SCHEMA,
        "parent_memory": teaching_identity,
        "root_path": str(root_path.resolve()),
        "study_uids": ordered_uids,
        "study_inputs": study_inputs,
        "labels": labels_identity,
        "visual_additions": visual_pin,
        "child_revision": next_revision,
        "growth_review_mode": growth_review_mode,
        "exclude_same_study": True,
        "code": code_identity,
    }
    _pin_round_inputs(output, round_inputs)

    inference_dir = output / "inference"
    studies_dir = inference_dir / "studies"
    training_dir = output / "training"
    child_dir = output / "memory"
    child_training_dir = output / "child-training"
    round_receipt_path = output / "round-receipt.json"

    if round_receipt_path.exists():
        saved_round, _actual_rr, _rr_sha = _stable_json(
            round_receipt_path, "round_receipt"
        )
        if (
            not isinstance(saved_round, Mapping)
            or saved_round.get("schema") != ROUND_RECEIPT_SCHEMA
        ):
            raise PrepareError("round_receipt_invalid")
        saved_composition = saved_round.get("composition_parent")
        if not isinstance(saved_composition, Mapping):
            raise PrepareError("composition_parent_checkpoint_missing")
        composition_path = saved_composition.get("path")
        if not isinstance(composition_path, str):
            raise PrepareError("composition_parent_checkpoint_invalid")
        expected_composition_sha = saved_composition.get("manifest_sha256")
        if (
            _sha256_file(
                Path(composition_path) / "manifest.json",
                "composition_parent_unreadable",
            )
            != expected_composition_sha
        ):
            raise PrepareError("composition_parent_changed_on_resume")
        if reviewed_growth_memory_path is not None:
            requested_review = reviewed_growth_memory_path.resolve()
            requested_manifest = (
                requested_review / "manifest.json"
                if requested_review.is_dir()
                else requested_review
            )
            if (
                _sha256_file(requested_manifest, "reviewed_growth_memory_unreadable")
                != expected_composition_sha
            ):
                raise PrepareError("reviewed_growth_memory_changed_on_resume")
        for uid in ordered_uids:
            expected_pin = _study_pin_payload(
                uid=uid,
                memory_manifest_sha256=str(teaching_identity["manifest_sha256"]),
                memory_revision=str(memory["revision"]),
                code_identity=code_identity,
                study_input=study_inputs[uid],
            )
            if (
                _try_resume_study_record(studies_dir, inference_dir, uid, expected_pin)
                is None
            ):
                raise PrepareError("study_checkpoint_missing_on_completed_round:" + uid)
        if not child_dir.is_dir():
            raise PrepareError("child_memory_missing_on_completed_round")
        child_snapshot = load_memory_snapshot(child_dir)
        expected_child_sha = _mapping_get(
            saved_round, "child_memory", "manifest_sha256"
        )
        if (
            child_snapshot.memory is None
            or child_snapshot.sha256 is None
            or child_snapshot.sha256 != expected_child_sha
        ):
            raise PrepareError("child_memory_sha256_mismatch_on_resume")
        _training_export(
            memory_path=child_dir,
            expected_memory_sha256=child_snapshot.sha256,
            inference_dir=inference_dir,
            labels_path=labels_path,
            output_path=child_training_dir,
            report_call_paths=report_call_paths,
        )
        if _mapping_get(
            saved_round, "child_training", "receipt_sha256"
        ) != _sha256_file(
            child_training_dir / "receipt.json", "child_training_receipt_missing"
        ):
            raise PrepareError("child_training_receipt_mismatch")
        resumed_receipt = dict(saved_round)
        resumed_receipt["studies"] = {
            "requested": ordered_uids,
            "executed": [],
            "resumed": list(ordered_uids),
        }
        return resumed_receipt

    memory["memory_manifest_sha256"] = str(teaching_identity["manifest_sha256"])
    if "prepared_recall" not in memory:
        memory["prepared_recall"] = prepare_recall(memory)
    actual_infer = infer_fn or infer_study

    studies_dir.mkdir(parents=True, exist_ok=True)

    study_entries: list[dict[str, str]] = []
    executed_study_uids: list[str] = []
    resumed_study_uids: list[str] = []

    for uid in ordered_uids:
        expected_pin = _study_pin_payload(
            uid=uid,
            memory_manifest_sha256=str(teaching_identity["manifest_sha256"]),
            memory_revision=str(memory["revision"]),
            code_identity=code_identity,
            study_input=study_inputs[uid],
        )
        resumed = _try_resume_study_record(
            studies_dir,
            inference_dir,
            uid,
            expected_pin,
        )
        if resumed is not None:
            resumed_study_uids.append(uid)
            study_entries.append(resumed)
            continue
        study_memory = memory_view(memory, exclude_study_uids=(uid,))
        record = actual_infer(
            root_path,
            uid,
            study_memory,
            exclude_same_study=True,
        )
        after_input = verified_study_input(
            root_path,
            uid,
            expected_files=study_inventories.get(uid),
            cache_directory=cache_directory,
        )
        if after_input["sha256"] != study_inputs[uid]["sha256"]:
            raise PrepareError("study_changed_during_inference:" + uid)
        if _code_identity() != code_identity:
            raise PrepareError("round_source_changed_during_inference")
        written = dump_json_atomic(studies_dir / f"{uid}.json.xz", dict(record))
        written_sha = _sha256_file(written, "study_record_unreadable:" + uid)
        pin_doc = {
            **expected_pin,
            "record_file": str(written.relative_to(inference_dir)),
            "record_sha256": written_sha,
        }
        _write_json(studies_dir / f"{uid}.pin.json", pin_doc)
        executed_study_uids.append(uid)
        study_entries.append(
            {
                "study_uid": uid,
                "evidence_path": str(written.relative_to(inference_dir)),
            }
        )

    run_receipt = {
        "schema": RUN_SCHEMA,
        "action": "infer",
        "source_mode": "raw_squint_case_recall",
        "memory_revision": str(memory["revision"]),
        "memory_manifest_sha256": str(teaching_identity["manifest_sha256"]),
        "work": {
            "studies": study_entries,
            "executed_study_uids": executed_study_uids,
            "resumed_study_uids": resumed_study_uids,
        },
    }
    inference_receipt_path = inference_dir / "receipt.json"
    if inference_receipt_path.exists():
        saved_inference, _actual, _sha = _stable_json(
            inference_receipt_path, "run_receipt"
        )
        if (
            not isinstance(saved_inference, Mapping)
            or any(
                saved_inference.get(key) != run_receipt[key]
                for key in (
                    "schema",
                    "action",
                    "source_mode",
                    "memory_revision",
                    "memory_manifest_sha256",
                )
            )
            or _mapping_get(saved_inference, "work", "studies") != study_entries
        ):
            raise PrepareError("inference_checkpoint_mismatch")
    else:
        _write_json(inference_receipt_path, run_receipt)

    training_receipt = _training_export(
        memory_path=memory_path,
        expected_memory_sha256=expected_memory_sha256,
        inference_dir=inference_dir,
        labels_path=labels_path,
        output_path=training_dir,
        report_call_paths=report_call_paths,
    )

    exported_rows = [
        json.loads(line)
        for line in (training_dir / "procedure-experiences.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    frozen_parent = MemorySnapshot(
        path=Path(teaching_identity["path"]) / "manifest.json",
        sha256=expected_memory_sha256,
        status="squint",
        declared_schema=str(memory["schema"]),
        memory=memory,
    )
    growth_stage = stage_identity_growth(
        frozen_parent,
        [inference_dir],
        output / "growth",
        reviewed_memory=reviewed_growth_memory_path,
        require_admission_review=growth_review_mode == "first-round",
    )
    if growth_stage.status != "ready_to_compose":
        raise PrepareError(
            "identity_growth_admission_review_required:" + str(output / "growth")
        )
    composition_parent = growth_stage.snapshot
    assert composition_parent is not None
    assert composition_parent.memory is not None
    assert composition_parent.sha256 is not None
    taught_memory, teaching_summary = _compose_round_teaching(
        composition_parent.memory,
        composition_parent.sha256,
        labels=labels,
        labels_identity=labels_identity,
        visual_additions_path=visual_additions_path,
        round_name=output.name,
    )
    child_memory = squint_procedure_memory.retain_procedure_experiences(
        taught_memory,
        exported_rows,
        revision=next_revision,
    )
    child_memory["parent_revision"] = composition_parent.memory["revision"]
    child_memory["parent_manifest_sha256"] = composition_parent.sha256

    if child_dir.exists() or child_dir.is_symlink():
        if child_dir.is_symlink() or not child_dir.is_dir():
            raise PrepareError("child_memory_checkpoint_invalid")
        child_snapshot = load_memory_snapshot(child_dir)
        if (
            child_snapshot.memory is None
            or child_snapshot.sha256 is None
            or child_snapshot.memory.get("revision") != next_revision
        ):
            raise PrepareError("child_memory_checkpoint_mismatch")
        if _memory_content_sha256(child_snapshot.memory) != _memory_content_sha256(
            child_memory
        ):
            raise PrepareError("child_memory_checkpoint_content_mismatch")
    else:
        child_prepared = prepare_recall(child_memory)
        save_memory(child_memory, child_dir, prepared_recall=child_prepared)
        child_snapshot = load_memory_snapshot(child_dir)
        if child_snapshot.memory is None or child_snapshot.sha256 is None:
            raise PrepareError("child_memory_unavailable")

    child_training_receipt = _training_export(
        memory_path=child_dir,
        expected_memory_sha256=child_snapshot.sha256,
        inference_dir=inference_dir,
        labels_path=labels_path,
        output_path=child_training_dir,
        report_call_paths=report_call_paths,
    )
    retained_rows = (
        child_snapshot.memory.get("procedure_experiences", {}).get("rows", [])
        if isinstance(child_snapshot.memory.get("procedure_experiences"), Mapping)
        else []
    )
    round_receipt = {
        "schema": ROUND_RECEIPT_SCHEMA,
        "parent_memory": teaching_identity,
        "growth_review_mode": growth_review_mode,
        "child_memory": {
            "path": str(child_dir),
            "revision": str(child_snapshot.memory["revision"]),
            "manifest_sha256": str(child_snapshot.sha256),
            "case_count": len(child_snapshot.memory.get("cases", [])),
            "retained_procedure_experiences": len(retained_rows),
        },
        "teaching": teaching_summary,
        "identity_growth": dict(growth_stage.receipt),
        "composition_parent": {
            "path": str(composition_parent.path.parent),
            "revision": composition_parent.memory["revision"],
            "manifest_sha256": composition_parent.sha256,
        },
        "child_training": {
            "path": str(child_training_dir),
            "teaching_memory": child_training_receipt["inputs"]["teaching_memory"],
            "receipt_sha256": _sha256_file(
                child_training_dir / "receipt.json", "child_training_receipt_missing"
            ),
            "outputs": child_training_receipt["outputs"],
        },
        "studies": {
            "requested": ordered_uids,
            "executed": executed_study_uids,
            "resumed": resumed_study_uids,
        },
        "scope": {
            "resumable_study_checkpoints": True,
            "immutable_child_publication": True,
            "procedure_learning_retained_in_child_memory": True,
            "single_memory_chain": True,
        },
        "outputs": training_receipt["outputs"],
    }
    _write_json(round_receipt_path, round_receipt)
    return round_receipt


def _mapping_get(mapping: object, *keys: str) -> Any:
    current: object = mapping
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--memory", type=Path, required=True)
    parser.add_argument("--memory-sha256", required=True)
    parser.add_argument("--run", type=Path, action="append")
    parser.add_argument("--run-round", action="store_true")
    parser.add_argument("--root", type=Path)
    parser.add_argument(
        "--source-archive",
        type=Path,
        help="Trusted competition ZIP expected inventory; defaults to <root>.zip.",
    )
    parser.add_argument("--study-uid", action="append", default=[])
    parser.add_argument("--study-uids-file", type=Path)
    parser.add_argument("--visual-additions", type=Path)
    parser.add_argument("--reviewed-growth-memory", type=Path)
    parser.add_argument(
        "--growth-review-mode",
        choices=("first-round", "spot-check"),
        default="first-round",
        help="Use spot-check only after the first fully inspected round.",
    )
    parser.add_argument("--child-revision")
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument(
        "--report-calls",
        type=Path,
        action="append",
        default=[],
        help="reviewed report-call document; repeat for additional independent sources",
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser


def _collect_study_uids(args: argparse.Namespace) -> list[str]:
    uids = list(args.study_uid or [])
    if args.study_uids_file is not None:
        text = args.study_uids_file.read_text(encoding="utf-8")
        uids.extend(line.strip() for line in text.splitlines() if line.strip())
    return uids


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.run_round:
            if args.root is None:
                raise PrepareError("root_missing")
            round_receipt = run_round(
                memory_path=args.memory,
                expected_memory_sha256=args.memory_sha256,
                root_path=args.root,
                source_archive_path=args.source_archive,
                study_uids=_collect_study_uids(args),
                labels_path=args.labels,
                output_path=args.output,
                child_revision=args.child_revision,
                visual_additions_path=args.visual_additions,
                reviewed_growth_memory_path=args.reviewed_growth_memory,
                growth_review_mode=args.growth_review_mode,
                report_call_paths=args.report_calls,
            )
            print(
                json.dumps(
                    {
                        "output": str(args.output),
                        "child_memory": round_receipt["child_memory"],
                        "child_training": round_receipt["child_training"],
                        "studies": round_receipt["studies"],
                        "counts": round_receipt["outputs"],
                    },
                    sort_keys=True,
                )
            )
            return 0
        receipt = prepare(
            memory_path=args.memory,
            expected_memory_sha256=args.memory_sha256,
            run_paths=args.run or [],
            labels_path=args.labels,
            output_path=args.output,
            report_call_paths=args.report_calls,
        )
    except (PrepareError, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(
        json.dumps(
            {"output": str(args.output), "counts": receipt["outputs"]}, sort_keys=True
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
