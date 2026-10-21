#!/usr/bin/env python3
"""Report held-out capacity results from a completed squint production run."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import sys
from collections import Counter
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path
from typing import Any

from knee.diagnosis.submission import SUBMISSION_COLUMNS
from knee.json_store import load_json
from knee.study.codes import label_code
from knee.study.tables import LABELS, TRAIN_COLUMNS


class CapacityReportError(ValueError):
    """A named refusal to report an incomplete or mismatched capacity run."""


def _object(value: Any, code: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CapacityReportError(code)
    return value


def _read_labels(path: Path) -> tuple[dict[str, dict[str, str]], str]:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise CapacityReportError("labels_unreadable") from error
    try:
        text = raw.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text, newline=""), strict=True))
    except (UnicodeDecodeError, csv.Error) as error:
        raise CapacityReportError("labels_csv_malformed") from error
    if not rows:
        raise CapacityReportError("labels_empty")
    header, *body = rows
    if tuple(header) != TRAIN_COLUMNS:
        raise CapacityReportError("labels_columns_invalid")
    if not body:
        raise CapacityReportError("labels_empty")
    labels: dict[str, dict[str, str]] = {}
    for number, cells in enumerate(body, start=2):
        if len(cells) != len(TRAIN_COLUMNS):
            raise CapacityReportError(f"labels_row_width_invalid:{number}")
        row = dict(zip(TRAIN_COLUMNS, cells, strict=True))
        uid = row["StudyInstanceUID"]
        if not isinstance(uid, str) or not uid.strip():
            raise CapacityReportError("labels_study_uid_invalid")
        if uid in labels:
            raise CapacityReportError("labels_study_uid_duplicate:" + uid)
        labels[uid] = {name: label_code(row[name]) for name in LABELS}
    return labels, hashlib.sha256(raw).hexdigest()


def _exact_score(ranking: dict[str, Any], uid: str, condition: str) -> Fraction:
    exact = ranking.get("exact")
    if not isinstance(exact, dict):
        raise CapacityReportError(f"ranking_exact_missing:{uid}:{condition}")
    numerator = exact.get("numerator")
    denominator = exact.get("denominator")
    if type(numerator) is not str or type(denominator) is not str:
        raise CapacityReportError(f"ranking_exact_invalid:{uid}:{condition}")
    try:
        score = Fraction(int(numerator), int(denominator))
    except (ValueError, ZeroDivisionError) as error:
        raise CapacityReportError(f"ranking_exact_invalid:{uid}:{condition}") from error
    if score <= 0 or score >= 1:
        raise CapacityReportError(f"ranking_exact_out_of_range:{uid}:{condition}")
    value = ranking.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CapacityReportError(f"ranking_value_invalid:{uid}:{condition}")
    if not math.isfinite(value) or not 0.0 < value < 1.0:
        raise CapacityReportError(f"ranking_value_invalid:{uid}:{condition}")
    if float(score) != value:
        raise CapacityReportError(f"ranking_exact_value_mismatch:{uid}:{condition}")
    return score


def _safe_evidence_path(run: Path, relative: Any) -> Path:
    if type(relative) is not str or not relative:
        raise CapacityReportError("evidence_path_invalid")
    path = (run / relative).resolve()
    try:
        path.relative_to(run.resolve())
    except ValueError as error:
        raise CapacityReportError("evidence_path_outside_run") from error
    return path


def _capacity_exclusion(
    record: dict[str, Any], uid: str, memory_sha: str
) -> dict[str, Any]:
    exclusion = record.get("capacity_exclusion")
    if not isinstance(exclusion, dict):
        raise CapacityReportError("capacity_exclusion_missing:" + uid)
    if exclusion.get("excluded_study_uid") != uid:
        raise CapacityReportError("capacity_excluded_uid_mismatch:" + uid)
    if exclusion.get("exclusion_status") != "applied":
        raise CapacityReportError("capacity_exclusion_not_applied:" + uid)
    counts = (
        "original_case_count",
        "filtered_case_count",
        "excluded_case_count",
        "original_censor_count",
        "filtered_censor_count",
        "excluded_censor_count",
    )
    if any(type(exclusion.get(key)) is not int or exclusion[key] < 0 for key in counts):
        raise CapacityReportError("capacity_exclusion_counts_invalid:" + uid)
    if (
        exclusion["original_case_count"]
        != exclusion["filtered_case_count"] + exclusion["excluded_case_count"]
        or exclusion["original_censor_count"]
        != exclusion["filtered_censor_count"] + exclusion["excluded_censor_count"]
        or exclusion["excluded_case_count"] == 0
    ):
        raise CapacityReportError("capacity_exclusion_counts_inconsistent:" + uid)
    fingerprint = exclusion.get("consumed_case_fingerprint")
    if type(fingerprint) is not str or not fingerprint:
        raise CapacityReportError("capacity_exclusion_fingerprint_missing:" + uid)
    if exclusion.get("preparation_schema") != "knee.squint-recall-preparation/v1":
        raise CapacityReportError("capacity_preparation_schema_invalid:" + uid)
    if exclusion.get("preparation_outcome") != "prepared":
        raise CapacityReportError("capacity_preparation_outcome_invalid:" + uid)
    if (
        exclusion.get("consumed_fingerprint_scope")
        != "source_cases_calls_profiles_and_censors_v1"
    ):
        raise CapacityReportError("capacity_fingerprint_scope_invalid:" + uid)
    identity = exclusion.get("prepared_population_identity")
    if not isinstance(identity, dict):
        raise CapacityReportError("capacity_population_identity_missing:" + uid)
    if identity.get("status") != "prepared":
        raise CapacityReportError("capacity_population_status_invalid:" + uid)
    if identity.get("source_fingerprint") != fingerprint:
        raise CapacityReportError("capacity_population_fingerprint_mismatch:" + uid)
    if identity.get("memory_manifest_sha256") != memory_sha:
        raise CapacityReportError("capacity_population_memory_mismatch:" + uid)
    if "source" not in identity or type(identity["source"]) not in (str, dict):
        raise CapacityReportError("capacity_population_source_missing:" + uid)
    if (
        type(identity.get("case_profile_count")) is not int
        or identity["case_profile_count"] < 0
        or identity["case_profile_count"] > exclusion["filtered_case_count"]
    ):
        raise CapacityReportError("capacity_population_count_mismatch:" + uid)
    return exclusion


def _read_submission(
    run: Path, receipt: dict[str, Any]
) -> tuple[list[str], dict[str, dict[str, str]], dict[str, Any]]:
    metadata = receipt.get("submission")
    if not isinstance(metadata, dict):
        raise CapacityReportError("submission_metadata_missing")
    raw_path = metadata.get("submission_path")
    if type(raw_path) is not str or not raw_path:
        raise CapacityReportError("submission_path_missing")
    path = Path(raw_path).resolve()
    if path != (run / "submission.csv").resolve():
        raise CapacityReportError("submission_path_mismatch")
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise CapacityReportError("submission_unreadable") from error
    digest = hashlib.sha256(raw).hexdigest()
    if metadata.get("submission_sha256") != digest:
        raise CapacityReportError("submission_sha256_mismatch")
    if metadata.get("columns") != list(SUBMISSION_COLUMNS):
        raise CapacityReportError("submission_receipt_columns_mismatch")
    if metadata.get("source_provenance") != {
        "source_mode": receipt.get("source_mode"),
        "memory_revision": receipt.get("memory_revision"),
        "memory_manifest_sha256": receipt.get("memory_manifest_sha256"),
    }:
        raise CapacityReportError("submission_source_provenance_mismatch")
    try:
        rows = list(
            csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
        )
    except (UnicodeDecodeError, csv.Error) as error:
        raise CapacityReportError("submission_csv_malformed") from error
    if not rows or tuple(rows[0]) != SUBMISSION_COLUMNS:
        raise CapacityReportError("submission_columns_invalid")
    uids: list[str] = []
    values: dict[str, dict[str, str]] = {}
    for row in rows[1:]:
        if len(row) != len(SUBMISSION_COLUMNS):
            raise CapacityReportError("submission_row_width_invalid")
        uid = row[0]
        if not uid or uid in values:
            raise CapacityReportError("submission_uid_empty_or_duplicate")
        uids.append(uid)
        values[uid] = dict(zip(LABELS, row[1:], strict=True))
    if metadata.get("study_count") != len(uids):
        raise CapacityReportError("submission_receipt_study_count_mismatch")
    template_raw_path = metadata.get("template_path")
    if type(template_raw_path) is not str or not template_raw_path:
        raise CapacityReportError("submission_template_path_missing")
    template_path = Path(template_raw_path).resolve()
    try:
        template_raw = template_path.read_bytes()
    except OSError as error:
        raise CapacityReportError("submission_template_unreadable") from error
    template_sha = hashlib.sha256(template_raw).hexdigest()
    if (
        metadata.get("template_sha256") != template_sha
        or metadata.get("template_sha256_before_write") != template_sha
    ):
        raise CapacityReportError("submission_template_sha256_mismatch")
    try:
        template_rows = list(
            csv.reader(
                io.StringIO(template_raw.decode("utf-8-sig"), newline=""), strict=True
            )
        )
    except (UnicodeDecodeError, csv.Error) as error:
        raise CapacityReportError("submission_template_csv_malformed") from error
    if not template_rows or tuple(template_rows[0]) != SUBMISSION_COLUMNS:
        raise CapacityReportError("submission_template_columns_invalid")
    template_uids: list[str] = []
    for row in template_rows[1:]:
        if len(row) != len(SUBMISSION_COLUMNS) or not row[0] or row[0] in template_uids:
            raise CapacityReportError("submission_template_uid_invalid")
        template_uids.append(row[0])
    if template_uids != uids:
        raise CapacityReportError("submission_template_uid_order_mismatch")
    return (
        uids,
        values,
        {
            "path": "submission.csv",
            "sha256": digest,
            "bytes": len(raw),
            "template_path": str(template_path),
            "template_sha256": template_sha,
        },
    )


def _auc_summary(positive: list[Fraction], negative: list[Fraction]) -> dict[str, Any]:
    if not positive:
        return {"status": "undefined_no_positive_truth", "value": None}
    if not negative:
        return {"status": "undefined_no_negative_truth", "value": None}
    wins = ties = losses = 0
    for pos in positive:
        for neg in negative:
            if pos > neg:
                wins += 1
            elif pos == neg:
                ties += 1
            else:
                losses += 1
    numerator = 2 * wins + ties
    denominator = 2 * len(positive) * len(negative)
    exact = Fraction(numerator, denominator)
    return {
        "status": "defined",
        "value": {
            "numerator": str(exact.numerator),
            "denominator": str(exact.denominator),
        },
        "positive_greater": wins,
        "equal": ties,
        "negative_greater": losses,
        "positive_count": len(positive),
        "negative_count": len(negative),
    }


def evaluate_capacity(run_dir: Path, labels_path: Path) -> dict[str, Any]:
    """Read and reconcile a complete capacity run against independent official labels."""
    run = run_dir.resolve()
    if not run.is_dir():
        raise CapacityReportError("run_directory_missing")
    receipt_path = run / "receipt.json"
    if not receipt_path.is_file():
        raise CapacityReportError("run_receipt_missing")
    try:
        receipt = _object(load_json(receipt_path), "run_receipt_invalid")
    except (OSError, ValueError) as error:
        raise CapacityReportError("run_receipt_invalid") from error
    if receipt.get("action") != "capacity":
        raise CapacityReportError("run_action_not_capacity")
    if receipt.get("source_mode") != "raw_squint_case_recall":
        raise CapacityReportError("run_source_mode_invalid")
    revision = receipt.get("memory_revision")
    memory_sha = receipt.get("memory_manifest_sha256")
    if (
        type(revision) is not str
        or not revision
        or type(memory_sha) is not str
        or not memory_sha
    ):
        raise CapacityReportError("run_memory_identity_missing")
    studies = (
        receipt.get("work", {}).get("studies")
        if isinstance(receipt.get("work"), dict)
        else None
    )
    if not isinstance(studies, list) or not studies:
        raise CapacityReportError("run_studies_missing")
    if type(receipt.get("studies")) is not int or receipt["studies"] != len(studies):
        raise CapacityReportError("run_study_count_mismatch")
    preparation = receipt.get("recall_preparation")
    if not isinstance(preparation, dict):
        raise CapacityReportError("run_recall_preparation_missing")
    per_study_preparation = (
        preparation.get("path") is None
        and preparation.get("sha256") is None
        and type(preparation.get("bytes")) is int
        and preparation["bytes"] == 0
        and preparation.get("cache_status") == "study_excluded_per_study"
    )
    if not per_study_preparation:
        preparation_path = _safe_evidence_path(run, preparation.get("path"))
        if preparation_path.name not in (
            "recall-preparation.json",
            "recall-preparation.json.xz",
        ):
            raise CapacityReportError("run_recall_preparation_path_invalid")
        try:
            preparation_raw = preparation_path.read_bytes()
        except OSError as error:
            raise CapacityReportError("run_recall_preparation_unreadable") from error
        if hashlib.sha256(preparation_raw).hexdigest() != preparation.get("sha256"):
            raise CapacityReportError("run_recall_preparation_sha256_mismatch")
        try:
            preparation_record = _object(
                load_json(preparation_path), "run_recall_preparation_invalid"
            )
        except (OSError, ValueError) as error:
            raise CapacityReportError("run_recall_preparation_invalid") from error
        if (
            preparation_record.get("memory_manifest_sha256") != memory_sha
            or preparation_record.get("memory_revision") != revision
        ):
            raise CapacityReportError("run_recall_preparation_source_mismatch")
    receipt_uids: list[str] = []
    records: dict[str, dict[str, Any]] = {}
    exclusions: dict[str, dict[str, Any]] = {}
    for item in studies:
        if not isinstance(item, dict):
            raise CapacityReportError("run_study_row_invalid")
        uid = item.get("study_uid")
        if type(uid) is not str or not uid or uid in records:
            raise CapacityReportError("run_study_uid_invalid_or_duplicate")
        if item.get("study_status") == "not_examined_budget":
            raise CapacityReportError("study_not_examined_budget:" + uid)
        evidence_path = _safe_evidence_path(run, item.get("evidence_path"))
        try:
            record = _object(load_json(evidence_path), "study_evidence_invalid:" + uid)
        except (OSError, ValueError) as error:
            raise CapacityReportError("study_evidence_unreadable:" + uid) from error
        if (
            record.get("schema") != "knee.squint-study/v1"
            or record.get("study_uid") != uid
        ):
            raise CapacityReportError("study_evidence_identity_mismatch:" + uid)
        if record.get("study_status") == "not_examined_budget":
            raise CapacityReportError("study_not_examined_budget:" + uid)
        if record.get("memory_revision") != revision:
            raise CapacityReportError("study_memory_revision_mismatch:" + uid)
        if (
            not isinstance(record.get("work"), dict)
            or record["work"].get("source_mode") != receipt["source_mode"]
        ):
            raise CapacityReportError("study_source_mode_mismatch:" + uid)
        exclusion = _capacity_exclusion(record, uid, memory_sha)
        records[uid] = record
        if item.get("capacity_exclusion") != exclusion:
            raise CapacityReportError("receipt_capacity_exclusion_mismatch:" + uid)
        exclusions[uid] = exclusion
        receipt_uids.append(uid)

    submission_uids, submitted, submission_meta = _read_submission(run, receipt)
    if submission_uids != receipt_uids:
        raise CapacityReportError("submission_uid_order_mismatch")
    labels, labels_sha = _read_labels(labels_path)
    validated: dict[str, dict[str, tuple[Fraction, str]]] = {}
    for uid in receipt_uids:
        record = records[uid]
        questions = record.get("questions")
        if not isinstance(questions, dict):
            raise CapacityReportError("study_questions_missing:" + uid)
        validated[uid] = {}
        for condition in LABELS:
            evidence = questions.get(condition)
            if not isinstance(evidence, dict):
                raise CapacityReportError(f"study_question_missing:{uid}:{condition}")
            finding = evidence.get("finding")
            ranking = evidence.get("ranking")
            if not isinstance(finding, dict) or not isinstance(ranking, dict):
                raise CapacityReportError(f"study_ranking_missing:{uid}:{condition}")
            score = _exact_score(ranking, uid, condition)
            retained_values = record.get("values")
            if (
                not isinstance(retained_values, dict)
                or condition not in retained_values
            ):
                raise CapacityReportError(f"study_value_missing:{uid}:{condition}")
            try:
                agrees = Decimal(submitted[uid][condition]) == Decimal(
                    str(ranking["value"])
                )
                value_agrees = Decimal(str(retained_values[condition])) == Decimal(
                    str(ranking["value"])
                )
            except InvalidOperation:
                agrees = False
                value_agrees = False
            if not agrees or not value_agrees:
                raise CapacityReportError(
                    f"submission_ranking_mismatch:{uid}:{condition}"
                )
            outcome = finding.get("outcome")
            if ranking.get("tier") != outcome:
                raise CapacityReportError(
                    f"finding_ranking_tier_mismatch:{uid}:{condition}"
                )
            if outcome not in ("open", "assigned", "defeated"):
                raise CapacityReportError(f"finding_outcome_invalid:{uid}:{condition}")
            validated[uid][condition] = (score, outcome)

    by_condition: dict[str, dict[str, Any]] = {}
    for condition in LABELS:
        summary: dict[str, Any] = {
            truth: {"identified": 0, "abstained": 0, "wrong": 0, "count": 0}
            for truth in ("positive", "negative")
        }
        unavailable = Counter()
        positive_scores: list[Fraction] = []
        negative_scores: list[Fraction] = []
        for uid in receipt_uids:
            if uid not in labels:
                unavailable["study_not_in_label_source"] += 1
                continue
            label = labels[uid][condition]
            if label not in ("1", "0"):
                unavailable[label] += 1
                continue
            truth = "positive" if label == "1" else "negative"
            summary[truth]["count"] += 1
            score, outcome = validated[uid][condition]
            if outcome == "open":
                summary[truth]["abstained"] += 1
            elif outcome in ("assigned", "defeated"):
                predicted = "positive" if outcome == "assigned" else "negative"
                summary[truth]["identified" if predicted == truth else "wrong"] += 1
            else:
                raise CapacityReportError(f"finding_outcome_invalid:{uid}:{condition}")
            if truth == "positive":
                positive_scores.append(score)
            else:
                negative_scores.append(score)
        by_condition[condition] = {
            **summary,
            "unavailable_truth": dict(sorted(unavailable.items())),
            "ordering": _auc_summary(positive_scores, negative_scores),
        }
    return {
        "schema": "knee.squint-capacity-evaluation/v1",
        "action": "capacity",
        "run": {
            "path": str(run),
            "receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
            "memory_revision": revision,
            "memory_manifest_sha256": memory_sha,
            "source_mode": receipt["source_mode"],
            "study_count": len(receipt_uids),
            "study_uids": receipt_uids,
            "submission": submission_meta,
        },
        "labels": {
            "path": str(labels_path.resolve()),
            "sha256": labels_sha,
            "study_count": len(labels),
        },
        "capacity_exclusions": {uid: exclusions[uid] for uid in receipt_uids},
        "per_condition": by_condition,
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Squint held-out capacity report",
        "",
        f"Run: `{report['run']['path']}`  ",
        f"Run receipt SHA-256: `{report['run']['receipt_sha256']}`  ",
        f"Memory revision: `{report['run']['memory_revision']}`  ",
        f"Memory manifest SHA-256: `{report['run']['memory_manifest_sha256']}`  ",
        f"Label source SHA-256: `{report['labels']['sha256']}`  ",
        f"Studies: {report['run']['study_count']}",
        "",
        "Counts below use only literal official labels `1` and `0`; blank or unrecognized labels are unavailable, not negative.",
        "Identified means decisive and correct; wrong means decisive and incorrect; abstained means open.",
        "The ordering statistic compares exact retained ranking fractions. It is a descriptive ordering measure, not a calibrated risk estimate.",
        "",
        "| Condition | Positive: identified / abstained / wrong | Negative: identified / abstained / wrong | Unavailable labels | AUC / ordering |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, result in report["per_condition"].items():
        pos, neg = result["positive"], result["negative"]
        ordering = result["ordering"]
        auc = (
            f"{ordering['value']['numerator']}/{ordering['value']['denominator']}"
            if ordering["status"] == "defined"
            else ordering["status"]
        )
        unavailable = sum(result["unavailable_truth"].values())
        lines.append(
            f"| {name} | {pos['identified']} / {pos['abstained']} / {pos['wrong']} | "
            f"{neg['identified']} / {neg['abstained']} / {neg['wrong']} | {unavailable} | {auc} |"
        )
    lines.extend(("", "No combined or macro score is reported.", ""))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run",
        type=Path,
        required=True,
        help="completed production diagnostics directory",
    )
    parser.add_argument(
        "--labels", type=Path, required=True, help="independent official train.csv"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="new JSON report path"
    )
    parser.add_argument(
        "--markdown", type=Path, help="optional new Markdown report path"
    )
    args = parser.parse_args(argv)
    try:
        report = evaluate_capacity(args.run, args.labels)
        if (
            args.markdown is not None
            and args.markdown.resolve() == args.output.resolve()
        ):
            raise CapacityReportError("output_paths_must_be_distinct")
        for output in (args.output, args.markdown):
            if output is not None and output.exists():
                raise CapacityReportError("output_already_exists:" + str(output))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(report, sort_keys=True, indent=2) + "\n")
        if args.markdown is not None:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            with args.markdown.open("x", encoding="utf-8") as stream:
                stream.write(_markdown(report))
    except (CapacityReportError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(f"wrote {args.output}")
    if args.markdown is not None:
        print(f"wrote {args.markdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
