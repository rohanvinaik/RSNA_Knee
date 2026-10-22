"""Export reviewed object buckets and pinned procedure experiences for training."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from knee.diagnosis import squint_corpus, squint_procedure_memory
from knee.diagnosis.squint_memory import (
    SquintMemoryError,
    load_memory_snapshot,
)
from knee.json_store import load_json, resolve_json_path

RECEIPT_SCHEMA = "knee.squint-procedure-experiences/v1"
RUN_SCHEMA = "knee.squint-run/v1"
STUDY_SCHEMA = "knee.squint-study/v1"


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


def _load_labels_and_corpus(
    memory: Mapping[str, Any],
    teaching_identity: Mapping[str, Any],
    labels_path: Path,
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


def _code_identity() -> dict[str, dict[str, str]]:
    code_files = {
        "script": Path(__file__).resolve(),
        "procedure_memory_module": Path(squint_procedure_memory.__file__).resolve(),
        "object_corpus_module": Path(squint_corpus.__file__).resolve(),
    }
    return {
        name: {
            "path": str(path),
            "sha256": _sha256_file(path, "code_unreadable:" + name),
        }
        for name, path in code_files.items()
    }


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
        memory, teaching_identity, labels_path
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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--memory", type=Path, required=True)
    parser.add_argument("--memory-sha256", required=True)
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        receipt = prepare(
            memory_path=args.memory,
            expected_memory_sha256=args.memory_sha256,
            run_paths=args.run,
            labels_path=args.labels,
            output_path=args.output,
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
