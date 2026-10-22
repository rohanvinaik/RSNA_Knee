"""Record completed squint runs without running inference or changing memory.

Ordering uses the submitted decimal values, never the internal rational's finer
precision. Teacher readback and whole-study-excluded evaluation stay distinct.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import lzma
import sys
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import evaluate_squint_capacity as capacity

SCHEMA = "knee.squint-experiment/v1"
FIELDS = (
    "study_uid",
    "condition",
    "truth",
    "outcome",
    "predicted_ternary",
    "assessment",
    "ranking_value",
    "reason",
    "record_sha256",
)


class ExperimentError(ValueError):
    """A named refusal to misreport an experiment."""


def _sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _read(path: Path) -> tuple[dict, str]:
    try:
        raw = path.read_bytes()
        value = json.loads(lzma.decompress(raw) if path.suffix == ".xz" else raw)
    except (OSError, ValueError, lzma.LZMAError) as error:
        raise ExperimentError("input_unreadable:" + str(path)) from error
    if not isinstance(value, dict):
        raise ExperimentError("input_not_object:" + str(path))
    return value, hashlib.sha256(raw).hexdigest()


def summarize(rows: list[dict]) -> dict:
    """Count both truth signs, keep unavailable truth out of ordering and means."""
    result = {}
    for question in capacity.LABELS:
        population = [r for r in rows if r["condition"] == question]
        scores, summary = {}, {}
        for truth in ("positive", "negative"):
            members = [r for r in population if r["truth"] == truth]
            counts = Counter(r["assessment"] for r in members)
            values = [Fraction(r["ranking_value"]) for r in members]
            mean = sum(values, Fraction()) / len(values) if values else None
            scores[truth] = values
            summary[truth] = {
                "count": len(members),
                **{key: counts[key] for key in ("identified", "abstained", "wrong")},
                "mean_ranking_value": float(mean) if mean is not None else None,
                "mean_exact": (
                    {
                        "numerator": str(mean.numerator),
                        "denominator": str(mean.denominator),
                    }
                    if mean is not None
                    else None
                ),
            }
        summary["unavailable_truth"] = dict(
            Counter(
                r["truth"]
                for r in population
                if r["truth"] not in ("positive", "negative")
            )
        )
        summary["ordering"] = capacity._auc_summary(
            scores["positive"], scores["negative"]
        )
        result[question] = summary
    return result


def compare_reports(report: dict, rows: list[dict], previous: Path) -> dict:
    """Paired changes require the same protocol, cohort and independent truth."""
    old, old_sha = _read(previous)
    if old.get("schema") != SCHEMA:
        raise ExperimentError("comparison_schema_invalid")
    prior_csv = previous.parent / "rows.csv"
    if _sha(prior_csv) != old.get("artifacts", {}).get("rows.csv", {}).get("sha256"):
        raise ExperimentError("comparison_rows_digest_mismatch")
    with prior_csv.open(newline="", encoding="utf-8") as stream:
        old_rows = list(csv.DictReader(stream))

    def keys(values: list[dict]) -> list[tuple[str, str]]:
        return [(r["study_uid"], r["condition"]) for r in values]

    if len(set(keys(old_rows))) != len(old_rows):
        raise ExperimentError("comparison_duplicate_row")
    reasons = []
    if old.get("protocol") != report["protocol"]:
        reasons.append("different_protocol")
    if set(keys(old_rows)) != set(keys(rows)):
        reasons.append("different_cohort")
    if old.get("labels", {}).get("sha256") != report["labels"]["sha256"]:
        reasons.append("different_truth_source")
    provenance = {"report": str(previous.resolve()), "sha256": old_sha}
    if reasons:
        return {"status": "incomparable", "reasons": reasons, "previous": provenance}
    prior = {(r["study_uid"], r["condition"]): r for r in old_rows}
    changes = {}
    old_summary = summarize(old_rows)
    for question, current in report["per_condition"].items():
        transition = Counter()
        outcome_transitions = Counter()
        for row in rows:
            if row["condition"] == question:
                before = prior[(row["study_uid"], question)]
                if before["truth"] != row["truth"]:
                    raise ExperimentError("comparison_truth_row_mismatch")
                transition[before["assessment"] + "->" + row["assessment"]] += 1
                outcome_transitions[before["outcome"] + "->" + row["outcome"]] += 1
        before = old_summary[question]
        deltas = {}
        for side in ("positive", "negative"):
            deltas[side] = {
                key: current[side][key] - before[side][key]
                for key in ("identified", "abstained", "wrong")
            }
            a, b = (
                current[side]["mean_ranking_value"],
                before[side]["mean_ranking_value"],
            )
            deltas[side]["mean_ranking_value"] = (
                a - b if a is not None and b is not None else None
            )
        before_auc, after_auc = (
            before["ordering"].get("value"),
            current["ordering"].get("value"),
        )
        auc_delta = None
        if before_auc is not None and after_auc is not None:
            difference = Fraction(
                int(after_auc["numerator"]), int(after_auc["denominator"])
            ) - Fraction(int(before_auc["numerator"]), int(before_auc["denominator"]))
            auc_delta = {
                "numerator": str(difference.numerator),
                "denominator": str(difference.denominator),
            }
        changes[question] = {
            "count_deltas": deltas,
            "assessment_transitions": dict(transition),
            "outcome_transitions": dict(outcome_transitions),
            "auc_delta_exact": auc_delta,
            "before_ordering": before["ordering"],
            "after_ordering": current["ordering"],
        }
    return {"status": "paired", "previous": provenance, "per_condition": changes}


def record_experiment(
    run: Path,
    labels_path: Path,
    output: Path,
    *,
    protocol: str,
    memory: Path | None = None,
    compare: Path | None = None,
) -> dict:
    """Write a fresh report; never reinterpret an infer receipt as capacity."""
    if output.exists():
        raise ExperimentError("output_already_exists")
    if protocol == "fresh-transfer":
        raise ExperimentError("fresh_transfer_verified_population_evidence_required")
    expected_action = {
        "teacher-readback": "infer",
        "whole-study-excluded": "capacity",
    }.get(protocol)
    if expected_action is None:
        raise ExperimentError("protocol_invalid")
    run = run.resolve()
    receipt, receipt_sha = _read(run / "receipt.json")
    if receipt.get("action") != expected_action:
        raise ExperimentError("protocol_action_mismatch")
    if receipt.get("source_mode") != "raw_squint_case_recall":
        raise ExperimentError("source_mode_invalid")
    if protocol == "whole-study-excluded":
        # Keep the existing evaluator's complete refusal contract intact. Its
        # internal rational AUC is not substituted for submitted decimal ties.
        capacity.evaluate_capacity(run, labels_path)
    revision, memory_sha = (
        receipt.get("memory_revision"),
        receipt.get("memory_manifest_sha256"),
    )
    if (
        not isinstance(revision, str)
        or not revision
        or not isinstance(memory_sha, str)
        or not memory_sha
    ):
        raise ExperimentError("memory_identity_missing")
    memory_identity = {
        "revision": revision,
        "sha256": memory_sha,
        "verification": "run_receipt_pin_only",
    }
    if memory is not None:
        manifest = memory / "manifest.json" if memory.is_dir() else memory
        if _sha(manifest) != memory_sha:
            raise ExperimentError("memory_manifest_digest_mismatch")
        memory_identity.update(
            path=str(manifest.resolve()), verification="actual_manifest_bytes_verified"
        )
    work = receipt.get("work")
    studies = work.get("studies") if isinstance(work, dict) else None
    if (
        not isinstance(studies, list)
        or not studies
        or type(receipt.get("studies")) is not int
        or receipt.get("studies") != len(studies)
    ):
        raise ExperimentError("study_count_invalid")
    if any(not isinstance(entry, dict) for entry in studies):
        raise ExperimentError("study_entry_invalid")
    uids, submitted, submission = capacity._read_submission(run, receipt)
    if [r.get("study_uid") for r in studies] != uids:
        raise ExperimentError("study_submission_order_mismatch")
    labels, truth_sha = capacity._read_labels(labels_path)
    rows, sources = [], []
    for entry in studies:
        uid = entry["study_uid"]
        if entry.get("study_status") == "not_examined_budget":
            raise ExperimentError("study_not_examined_budget:" + uid)
        path = capacity._safe_evidence_path(run, entry.get("evidence_path"))
        record, digest = _read(path)
        if record.get("study_status") == "not_examined_budget":
            raise ExperimentError("study_not_examined_budget:" + uid)
        if (
            record.get("schema") != "knee.squint-study/v1"
            or record.get("study_uid") != uid
            or record.get("memory_revision") != revision
        ):
            raise ExperimentError("study_identity_mismatch:" + uid)
        study_work = record.get("work")
        if (
            not isinstance(study_work, dict)
            or study_work.get("source_mode") != receipt["source_mode"]
        ):
            raise ExperimentError("study_source_mode_mismatch:" + uid)
        readout_policy = capacity._record_policy(record, receipt, uid)
        exclusion = entry.get("capacity_exclusion")
        if protocol == "whole-study-excluded":
            observed = capacity._capacity_exclusion(record, uid, memory_sha)
            if observed != exclusion:
                raise ExperimentError("receipt_exclusion_mismatch:" + uid)
        else:
            evidence_exclusion = record.get("capacity_exclusion")
            if any(
                isinstance(value, dict) and value.get("exclusion_status") == "applied"
                for value in (exclusion, evidence_exclusion)
            ):
                raise ExperimentError("teacher_readback_has_exclusion:" + uid)
        sources.append(
            {
                "study_uid": uid,
                "path": str(path),
                "sha256": digest,
                "exclusion": exclusion,
                "study_status": record.get("study_status"),
            }
        )
        questions, retained_values = record.get("questions"), record.get("values")
        if not isinstance(questions, dict):
            raise ExperimentError("study_questions_missing:" + uid)
        if not isinstance(retained_values, dict):
            raise ExperimentError("study_values_missing:" + uid)
        for condition in capacity.LABELS:
            question = questions.get(condition)
            if not isinstance(question, dict):
                raise ExperimentError("question_missing:" + uid + ":" + condition)
            ranking, finding = question.get("ranking"), question.get("finding")
            if not isinstance(ranking, dict) or not isinstance(finding, dict):
                raise ExperimentError("question_missing:" + uid + ":" + condition)
            if condition not in retained_values:
                raise ExperimentError("study_value_missing:" + uid + ":" + condition)
            capacity._exact_score(ranking, uid, condition)
            if readout_policy is not None:
                capacity._new_readout_score(
                    record,
                    receipt,
                    ranking,
                    finding,
                    submitted[uid][condition],
                    uid,
                    condition,
                )
                agrees = True
            else:
                try:
                    value = Decimal(submitted[uid][condition])
                    agrees = (
                        value
                        == Decimal(str(ranking["value"]))
                        == Decimal(str(retained_values[condition]))
                    )
                except (InvalidOperation, KeyError) as error:
                    raise ExperimentError("ranking_missing_or_invalid") from error
            outcome = finding.get("outcome")
            if (
                not agrees
                or ranking.get("tier") != outcome
                or outcome not in ("assigned", "defeated", "open")
            ):
                raise ExperimentError(
                    "ranking_outcome_mismatch:" + uid + ":" + condition
                )
            label = labels.get(uid, {}).get(condition, "study_not_in_label_source")
            truth = {"1": "positive", "0": "negative"}.get(label, label)
            assessment = (
                "unavailable"
                if truth not in ("positive", "negative")
                else "abstained"
                if outcome == "open"
                else "identified"
                if (outcome == "assigned") == (truth == "positive")
                else "wrong"
            )
            rows.append(
                dict(
                    zip(
                        FIELDS,
                        (
                            uid,
                            condition,
                            truth,
                            outcome,
                            {"assigned": 1, "open": 0, "defeated": -1}[outcome],
                            assessment,
                            submitted[uid][condition],
                            finding.get("reason", "not_recorded"),
                            digest,
                        ),
                        strict=True,
                    )
                )
            )
    if _sha(run / "receipt.json") != receipt_sha:
        raise ExperimentError("run_receipt_changed_during_read")
    report = {
        "schema": SCHEMA,
        "created_utc": datetime.now(UTC).isoformat(),
        "protocol": protocol,
        "run": {
            "path": str(run),
            "receipt_sha256": receipt_sha,
            "action": expected_action,
            "memory": memory_identity,
            "work": receipt["work"],
            "study_uids": uids,
            "source_records": sources,
            "submission": submission,
            "readout_policy_id": receipt.get("readout_policy_id"),
        },
        "labels": {"path": str(labels_path.resolve()), "sha256": truth_sha},
        "score_semantics": "Actual submission.csv decimal ranking values; not calibrated probabilities.",
        "tie_policy": "Exact Fraction(decimal text); one-half credit for ties.",
        "per_condition": summarize(rows),
        "row_count": len(rows),
        "fresh_transfer": "unavailable_without_verified_teacher_population_evidence",
        "limits": [
            "Observational readback does not establish a causal censor or contrast effect.",
            "Paired deltas describe observed runs; code, policy and readout changes may contribute, so they are not isolated memory-only gains.",
            "No aggregate score, inference, memory mutation or clinical mapping.",
        ],
    }
    if compare is not None:
        report["comparison"] = compare_reports(report, rows, compare)
    output.mkdir(parents=True, exist_ok=False)
    with (output / "rows.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# Squint experiment",
        "",
        f"Protocol: `{protocol}`.",
        "",
        report["score_semantics"],
        "",
        "| Condition | Positive identified / abstained / wrong | Negative identified / abstained / wrong | AUC |",
        "|---|---|---|---|",
    ]
    for condition, result in report["per_condition"].items():
        a, b, ordering = result["positive"], result["negative"], result["ordering"]
        exact = ordering.get("value")
        auc = (
            str(float(Fraction(int(exact["numerator"]), int(exact["denominator"]))))
            if exact
            else ordering["status"]
        )
        lines.append(
            f"| {condition} | {a['identified']} / {a['abstained']} / {a['wrong']} | {b['identified']} / {b['abstained']} / {b['wrong']} | {auc} |"
        )
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    report["artifacts"] = {
        name: {"sha256": _sha(output / name)} for name in ("rows.csv", "report.md")
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--protocol",
        choices=("teacher-readback", "whole-study-excluded", "fresh-transfer"),
        required=True,
    )
    parser.add_argument("--memory", type=Path)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args(argv)
    try:
        result = record_experiment(
            args.run,
            args.labels,
            args.output,
            protocol=args.protocol,
            memory=args.memory,
            compare=args.compare,
        )
    except (ExperimentError, capacity.CapacityReportError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "status": "recorded",
                "protocol": result["protocol"],
                "rows": result["row_count"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
