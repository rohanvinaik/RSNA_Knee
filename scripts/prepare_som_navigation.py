#!/usr/bin/env python3
"""Export measured study signals and independently reviewed diagnostic targets."""

from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import io
import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from knee.diagnosis.som_features import (
    NavigationFeatureError,
    counts_for_record,
    features_for_record,
    fit_feature_schema,
    population_study_uids,
    validate_feature_population,
)
from knee.diagnosis.squint_memory import load_memory_snapshot
from knee.diagnosis.squint_reports import import_report_calls, read_reports
from knee.json_store import load_json
from knee.study.tables import LABELS, TRAIN_COLUMNS


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _truth(labels_path: Path, report_paths: Sequence[Path]) -> tuple[dict, dict]:
    raw = labels_path.read_bytes()
    rows = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    if tuple(rows.fieldnames or ()) != TRAIN_COLUMNS:
        raise NavigationFeatureError("labels_columns_invalid")
    votes: dict[tuple[str, str], set[int]] = {}
    seen = set()
    for row in rows:
        uid = row["StudyInstanceUID"]
        if not uid or uid in seen:
            raise NavigationFeatureError("labels_uid_invalid_or_duplicate")
        seen.add(uid)
        for question in LABELS:
            cell = row[question].strip()
            if cell not in ("", "0", "1"):
                raise NavigationFeatureError("label_value_invalid")
            if cell:
                votes.setdefault((uid, question), set()).add(int(cell))
    pins = {
        "numeric_labels": {
            "path": str(labels_path.resolve()),
            "sha256": hashlib.sha256(raw).hexdigest(),
        },
        "report_calls": [],
    }
    reports = read_reports(labels_path) if report_paths else {}
    for path in report_paths:
        digest = _sha(path)
        calls = import_report_calls(path, reports)
        for call in calls:
            status = call["status"]
            if status not in ("signed", "abstention", "duplicate", "contradictory"):
                raise NavigationFeatureError(
                    "report_call_not_reviewed_or_invalid:" + status
                )
            if call["digit"] in (-1, 1):
                votes.setdefault((call["study_uid"], call["question"]), set()).add(
                    int(call["digit"] == 1)
                )
        if _sha(path) != digest:
            raise NavigationFeatureError("report_calls_changed_during_read")
        pins["report_calls"].append({"path": str(path.resolve()), "sha256": digest})
    return votes, pins


def _population_proofs(paths: Sequence[Path]) -> dict:
    proofs = {}
    for path in paths:
        snapshot = load_memory_snapshot(path)
        if snapshot.memory is None or snapshot.sha256 is None:
            raise NavigationFeatureError("population_memory_invalid")
        proofs[snapshot.sha256] = {
            "uids": population_study_uids(snapshot.memory),
            "path": str(snapshot.path),
            "sha256": snapshot.sha256,
            "stores": [
                "cases",
                "object_identity_cases",
                "censors",
                "procedure_experiences",
            ],
        }
        del snapshot
        gc.collect()
    return proofs


def prepare_navigation(
    *,
    runs: Sequence[Path],
    labels: Path,
    report_calls: Sequence[Path],
    train_uids: Sequence[str],
    validation_uids: Sequence[str],
    output: Path,
    population_memories: Sequence[Path] = (),
    allow_teacher_readback: bool = False,
) -> dict:
    """Write a fresh pinned dataset; never fit vocabulary on validation studies."""
    if output.exists() or output.is_symlink():
        raise NavigationFeatureError("output_already_exists")
    train, validation = set(train_uids), set(validation_uids)
    if (
        not train
        or not validation
        or any(not isinstance(u, str) or not u for u in train | validation)
    ):
        raise NavigationFeatureError("explicit_train_and_validation_uids_required")
    if train & validation:
        raise NavigationFeatureError("study_split_overlap")
    votes, truth_pins = _truth(labels, report_calls)
    populations = _population_proofs(population_memories)
    wanted = train | validation
    records, source_rows, run_pins = {}, {}, []
    for run_path in runs:
        run = run_path.resolve()
        receipt_path = run / "receipt.json"
        receipt_sha = _sha(receipt_path)
        receipt = load_json(receipt_path)
        if (
            not isinstance(receipt, dict)
            or receipt.get("source_mode") != "raw_squint_case_recall"
        ):
            raise NavigationFeatureError("run_source_invalid")
        if receipt.get("action") not in ("infer", "capacity"):
            raise NavigationFeatureError("run_action_invalid")
        entries = receipt.get("work", {}).get("studies")
        memory_sha, revision = (
            receipt.get("memory_manifest_sha256"),
            receipt.get("memory_revision"),
        )
        if not isinstance(entries, list) or not memory_sha or not revision:
            raise NavigationFeatureError("run_identity_or_studies_missing")
        if "studies" in receipt and (
            type(receipt["studies"]) is not int or receipt["studies"] != len(entries)
        ):
            raise NavigationFeatureError("run_study_count_invalid")
        run_pins.append(
            {
                "path": str(run),
                "receipt_sha256": receipt_sha,
                "memory_manifest_sha256": memory_sha,
                "memory_revision": revision,
                "action": receipt["action"],
            }
        )
        for entry in entries:
            uid = entry.get("study_uid")
            if uid not in wanted:
                continue
            if uid in records:
                raise NavigationFeatureError("duplicate_study_source:" + uid)
            relative = entry.get("evidence_path")
            if not isinstance(relative, str):
                raise NavigationFeatureError("evidence_path_invalid")
            path = (run / relative).resolve()
            if not path.is_relative_to(run):
                raise NavigationFeatureError("evidence_path_outside_run")
            digest = _sha(path)
            record = load_json(path)
            if (
                not isinstance(record, dict)
                or record.get("schema") != "knee.squint-study/v1"
                or record.get("study_uid") != uid
                or record.get("memory_revision") != revision
            ):
                raise NavigationFeatureError("study_identity_mismatch")
            if (
                entry.get("study_status") == "not_examined_budget"
                or record.get("study_status") == "not_examined_budget"
            ):
                raise NavigationFeatureError("study_not_examined_budget")
            proof = populations.get(memory_sha)
            kind = validate_feature_population(
                record,
                memory_sha,
                population_uids=proof["uids"] if proof else None,
                training=uid in train,
                allow_teacher_readback=allow_teacher_readback,
            )
            if kind == "whole_study_excluded" and entry.get(
                "capacity_exclusion"
            ) != record.get("capacity_exclusion"):
                raise NavigationFeatureError("receipt_record_exclusion_mismatch")
            if _sha(path) != digest:
                raise NavigationFeatureError("study_record_changed_during_read")
            records[uid] = record
            source_rows[uid] = {
                "path": str(path),
                "sha256": digest,
                "run_receipt_sha256": receipt_sha,
                "generating_memory_sha256": memory_sha,
                "population_status": kind,
                "exclusion": record.get("capacity_exclusion"),
                "population_memory": {k: v for k, v in proof.items() if k != "uids"}
                if proof
                else None,
            }
        if _sha(receipt_path) != receipt_sha:
            raise NavigationFeatureError("run_receipt_changed_during_read")
    if set(records) != wanted:
        raise NavigationFeatureError(
            "requested_studies_missing:" + ",".join(sorted(wanted - set(records)))
        )
    schema = fit_feature_schema([records[uid] for uid in sorted(train)])
    uids = sorted(wanted)
    x = np.stack([features_for_record(schema, records[uid]) for uid in uids])
    raw_counts = np.stack([counts_for_record(schema, records[uid]) for uid in uids])
    y = np.zeros((len(uids), len(LABELS)), dtype=np.float32)
    mask = np.zeros_like(y, dtype=bool)
    conflicts = []
    for i, uid in enumerate(uids):
        for j, question in enumerate(LABELS):
            signs = votes.get((uid, question), set())
            if len(signs) == 1:
                y[i, j], mask[i, j] = next(iter(signs)), True
            elif len(signs) > 1:
                conflicts.append(
                    {
                        "study_uid": uid,
                        "question": question,
                        "status": "independent_sources_disagree_masked",
                    }
                )
    writer_path = (
        Path(__file__).resolve().parents[1] / "src/knee/diagnosis/som_features.py"
    )
    schema.update(
        {
            "train_uids": sorted(train),
            "validation_uids": sorted(validation),
            "vocabulary_fit": "train_studies_only",
            "inputs": {
                "runs": run_pins,
                "labels": truth_pins,
                "records": [source_rows[uid] for uid in uids],
            },
            "truth_conflicts": conflicts,
            "source_pins": {
                "feature_writer_sha256": _sha(writer_path),
                "exporter_sha256": _sha(Path(__file__)),
            },
        }
    )
    output.mkdir(parents=True, exist_ok=False)
    np.savez_compressed(
        output / "dataset.npz",
        X=x,
        y=y,
        label_mask=mask,
        study_uids=np.asarray(uids),
        train_mask=np.asarray([u in train for u in uids]),
        validation_mask=np.asarray([u in validation for u in uids]),
        raw_counts=raw_counts,
    )
    (output / "schema.json").write_text(
        json.dumps(schema, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )
    receipt = {
        "schema": "knee.som-navigation-dataset/v1",
        "rows": len(uids),
        "features": x.shape[1],
        "training_studies": len(train),
        "validation_studies": len(validation),
        "per_condition": {
            q: {
                "train_positive": int(
                    (
                        (y[:, j] == 1)
                        & mask[:, j]
                        & np.asarray([u in train for u in uids])
                    ).sum()
                ),
                "train_negative": int(
                    (
                        (y[:, j] == 0)
                        & mask[:, j]
                        & np.asarray([u in train for u in uids])
                    ).sum()
                ),
                "validation_known": int(
                    (mask[:, j] & np.asarray([u in validation for u in uids])).sum()
                ),
            }
            for j, q in enumerate(LABELS)
        },
        "dataset_sha256": _sha(output / "dataset.npz"),
        "schema_sha256": _sha(output / "schema.json"),
        "source_sha256": {
            str(Path(__file__).resolve()): _sha(Path(__file__)),
            "src/knee/diagnosis/som_features.py": _sha(
                Path(__file__).resolve().parents[1]
                / "src/knee/diagnosis/som_features.py"
            ),
        },
        "population_statuses": {
            uid: source_rows[uid]["population_status"] for uid in uids
        },
        "limits": [
            "Study-condition targets are not localized lesion labels.",
            "Unknown or contradictory independent targets are masked.",
            "No raw images, report text, UID or teacher label is an input feature.",
        ],
    }
    (output / "receipt.json").write_text(
        json.dumps(receipt, indent=2, allow_nan=False) + "\n"
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--report-calls", type=Path, action="append", default=[])
    parser.add_argument("--population-memory", type=Path, action="append", default=[])
    parser.add_argument("--train-study-uids-file", type=Path, required=True)
    parser.add_argument("--validation-study-uids-file", type=Path, required=True)
    parser.add_argument("--allow-teacher-readback", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = prepare_navigation(
            runs=args.run,
            labels=args.labels,
            report_calls=args.report_calls,
            train_uids=args.train_study_uids_file.read_text().splitlines(),
            validation_uids=args.validation_study_uids_file.read_text().splitlines(),
            population_memories=args.population_memory,
            allow_teacher_readback=args.allow_teacher_readback,
            output=args.output,
        )
    except (NavigationFeatureError, OSError, ValueError) as error:
        print(json.dumps({"status": "refused", "reason": str(error)}))
        return 1
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
