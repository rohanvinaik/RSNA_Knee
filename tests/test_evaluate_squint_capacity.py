from __future__ import annotations

import csv
import hashlib
import json
from fractions import Fraction
from pathlib import Path

import pytest

from knee.diagnosis.submission import SUBMISSION_COLUMNS
from knee.json_store import dump_json_atomic
from knee.study.tables import LABELS, TRAIN_COLUMNS
from scripts.evaluate_squint_capacity import (
    CapacityReportError,
    evaluate_capacity,
    main,
)


def _exclusion(uid: str) -> dict:
    fingerprint = hashlib.sha256(("population:" + uid).encode()).hexdigest()
    return {
        "excluded_study_uid": uid,
        "exclusion_status": "applied",
        "original_case_count": 2,
        "filtered_case_count": 1,
        "excluded_case_count": 1,
        "original_censor_count": 0,
        "filtered_censor_count": 0,
        "excluded_censor_count": 0,
        "consumed_case_fingerprint": fingerprint,
        "consumed_fingerprint_scope": "source_cases_calls_profiles_and_censors_v1",
        "preparation_schema": "knee.squint-recall-preparation/v1",
        "preparation_outcome": "prepared",
        "prepared_population_identity": {
            "status": "prepared",
            "source_fingerprint": fingerprint,
            "source": "fixture-memory",
            "memory_manifest_sha256": "memory-sha",
            "case_profile_count": 1,
        },
    }


def _record(uid: str, outcome: str, score: Fraction) -> dict:
    ranking = {
        "value": float(score),
        "tier": outcome,
        "exact": {
            "numerator": str(score.numerator),
            "denominator": str(score.denominator),
        },
    }
    return {
        "schema": "knee.squint-study/v1",
        "study_uid": uid,
        "memory_revision": "memory-r1",
        "capacity_exclusion": _exclusion(uid),
        "work": {"source_mode": "raw_squint_case_recall"},
        "values": {name: float(score) for name in LABELS},
        "questions": {
            name: {"finding": {"outcome": outcome}, "ranking": ranking}
            for name in LABELS
        },
    }


def _make_run(
    tmp_path: Path, labels: list[list[str]], outcomes_scores: list[tuple[str, Fraction]]
) -> tuple[Path, Path]:
    run = tmp_path / "run"
    studies_dir = run / "studies"
    studies_dir.mkdir(parents=True)
    labels_path = tmp_path / "train.csv"
    with labels_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(TRAIN_COLUMNS)
        writer.writerows(labels)

    uids = [row[0] for row in labels]
    rows = []
    study_receipts = []
    csv_rows = []
    for uid, (outcome, score) in zip(uids, outcomes_scores, strict=True):
        record = _record(uid, outcome, score)
        evidence_path = dump_json_atomic(studies_dir / f"{uid}.json", record)
        exclusion = record["capacity_exclusion"]
        study_receipts.append(
            {
                "study_uid": uid,
                "evidence_path": str(evidence_path.relative_to(run)),
                "capacity_exclusion": exclusion,
            }
        )
        rows.append((uid, record))
        csv_rows.append((uid, *[str(float(score)) for _ in LABELS]))

    preparation = {
        "schema": "knee.squint-recall-preparation/v1",
        "memory_manifest_sha256": "memory-sha",
        "memory_revision": "memory-r1",
    }
    prep_path = dump_json_atomic(run / "recall-preparation.json", preparation)
    prep_sha = hashlib.sha256(prep_path.read_bytes()).hexdigest()
    submission_path = run / "submission.csv"
    with submission_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(SUBMISSION_COLUMNS)
        writer.writerows(csv_rows)
    submission_raw = submission_path.read_bytes()
    template_path = tmp_path / "held-out-template.csv"
    with template_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(SUBMISSION_COLUMNS)
        writer.writerows((uid, *("" for _ in LABELS)) for uid in uids)
    template_sha = hashlib.sha256(template_path.read_bytes()).hexdigest()
    receipt = {
        "schema": "knee.squint-run/v1",
        "action": "capacity",
        "source_mode": "raw_squint_case_recall",
        "studies": len(rows),
        "memory_revision": "memory-r1",
        "memory_manifest_sha256": "memory-sha",
        "recall_preparation": {
            "path": str(prep_path.relative_to(run)),
            "sha256": prep_sha,
            "bytes": prep_path.stat().st_size,
        },
        "submission": {
            "submission_path": str(submission_path.resolve()),
            "submission_sha256": hashlib.sha256(submission_raw).hexdigest(),
            "columns": list(SUBMISSION_COLUMNS),
            "study_count": len(rows),
            "template_path": str(template_path.resolve()),
            "template_sha256": template_sha,
            "template_sha256_before_write": template_sha,
            "source_provenance": {
                "source_mode": "raw_squint_case_recall",
                "memory_revision": "memory-r1",
                "memory_manifest_sha256": "memory-sha",
            },
        },
        "work": {"studies": study_receipts},
    }
    (run / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    return run, labels_path


def _labels(uids: list[str]) -> list[list[str]]:
    return [[uid, "fixture report", *("1" for _ in LABELS)] for uid in uids]


def test_reports_decisive_correct_wrong_and_abstained_by_truth_sign(
    tmp_path: Path,
) -> None:
    rows = _labels(["p_correct", "p_open", "p_wrong", "n_correct", "n_open", "n_wrong"])
    rows[3] = [rows[3][0], rows[3][1], *("0" for _ in LABELS)]
    rows[4] = [rows[4][0], rows[4][1], *("0" for _ in LABELS)]
    rows[5] = [rows[5][0], rows[5][1], *("0" for _ in LABELS)]
    outcomes = [
        ("assigned", Fraction(3, 4)),
        ("open", Fraction(1, 2)),
        ("defeated", Fraction(1, 4)),
        ("defeated", Fraction(1, 4)),
        ("open", Fraction(1, 2)),
        ("assigned", Fraction(3, 4)),
    ]
    run, labels_path = _make_run(tmp_path, rows, outcomes)
    report = evaluate_capacity(run, labels_path)
    acl = report["per_condition"]["ACL"]
    assert acl["positive"] == {"identified": 1, "abstained": 1, "wrong": 1, "count": 3}
    assert acl["negative"] == {"identified": 1, "abstained": 1, "wrong": 1, "count": 3}
    assert acl["ordering"]["value"] == {"numerator": "1", "denominator": "2"}
    assert (
        acl["ordering"]["positive_greater"],
        acl["ordering"]["equal"],
        acl["ordering"]["negative_greater"],
    ) == (3, 3, 3)


def test_missing_and_unrecognized_labels_are_unavailable_not_negative(
    tmp_path: Path,
) -> None:
    rows = _labels(["one", "two"])
    rows[0][2] = ""
    rows[1][2] = "maybe"
    run, labels_path = _make_run(
        tmp_path, rows, [("assigned", Fraction(2, 3)), ("defeated", Fraction(1, 3))]
    )
    acl = evaluate_capacity(run, labels_path)["per_condition"]["ACL"]
    assert acl["positive"]["count"] == 0
    assert acl["negative"]["count"] == 0
    assert acl["unavailable_truth"] == {"not_given": 1, "unrecognized": 1}
    assert acl["ordering"] == {"status": "undefined_no_positive_truth", "value": None}


def test_study_missing_from_label_source_is_separate_from_blank_cell(
    tmp_path: Path,
) -> None:
    run, labels_path = _make_run(tmp_path, _labels(["one"]), [("open", Fraction(1, 2))])
    with labels_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(TRAIN_COLUMNS)
        writer.writerow(_labels(["different-study"])[0])
    acl = evaluate_capacity(run, labels_path)["per_condition"]["ACL"]
    assert acl["unavailable_truth"] == {"study_not_in_label_source": 1}


def test_auc_is_named_undefined_when_either_truth_sign_is_absent(
    tmp_path: Path,
) -> None:
    rows = _labels(["one", "two"])
    run, labels_path = _make_run(
        tmp_path, rows, [("assigned", Fraction(2, 3)), ("open", Fraction(1, 3))]
    )
    assert (
        evaluate_capacity(run, labels_path)["per_condition"]["ACL"]["ordering"][
            "status"
        ]
        == "undefined_no_negative_truth"
    )


@pytest.mark.parametrize(
    "bad_rows,code",
    [
        ([], "labels_empty"),
        ([["StudyInstanceUID", "wrong"]], "labels_columns_invalid"),
    ],
)
def test_malformed_label_table_is_refused(
    tmp_path: Path, bad_rows: list[list[str]], code: str
) -> None:
    run, labels_path = _make_run(tmp_path, _labels(["one"]), [("open", Fraction(1, 2))])
    with labels_path.open("w", newline="", encoding="utf-8") as stream:
        csv.writer(stream).writerows(bad_rows)
    with pytest.raises(CapacityReportError, match=code):
        evaluate_capacity(run, labels_path)


def test_duplicate_label_uid_is_refused(tmp_path: Path) -> None:
    run, labels_path = _make_run(tmp_path, _labels(["one"]), [("open", Fraction(1, 2))])
    with labels_path.open("a", newline="", encoding="utf-8") as stream:
        csv.writer(stream).writerow(_labels(["one"])[0])
    with pytest.raises(CapacityReportError, match="labels_study_uid_duplicate"):
        evaluate_capacity(run, labels_path)


@pytest.mark.parametrize(
    "mutation,code",
    [
        (lambda receipt: receipt.update(action="infer"), "run_action_not_capacity"),
        (
            lambda receipt: receipt["work"]["studies"][0].update(
                capacity_exclusion=None
            ),
            "receipt_capacity_exclusion_mismatch",
        ),
    ],
)
def test_noncapacity_or_missing_exclusion_is_refused(
    tmp_path: Path, mutation, code: str
) -> None:
    run, labels_path = _make_run(tmp_path, _labels(["one"]), [("open", Fraction(1, 2))])
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    mutation(receipt)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(CapacityReportError, match=code):
        evaluate_capacity(run, labels_path)


def test_wrong_excluded_uid_is_refused(tmp_path: Path) -> None:
    run, labels_path = _make_run(tmp_path, _labels(["one"]), [("open", Fraction(1, 2))])
    evidence_path = run / "studies" / "one.json.xz"
    record = __import__("knee.json_store", fromlist=["load_json"]).load_json(
        evidence_path
    )
    record["capacity_exclusion"]["excluded_study_uid"] = "someone_else"
    dump_json_atomic(evidence_path, record)
    with pytest.raises(CapacityReportError, match="capacity_excluded_uid_mismatch"):
        evaluate_capacity(run, labels_path)


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("status", "not_prepared", "capacity_population_status_invalid"),
        (
            "memory_manifest_sha256",
            "another-memory",
            "capacity_population_memory_mismatch",
        ),
    ],
)
def test_prepared_population_identity_must_match_run_memory(
    tmp_path: Path, field: str, value: str, code: str
) -> None:
    run, labels_path = _make_run(tmp_path, _labels(["one"]), [("open", Fraction(1, 2))])
    evidence_path = run / "studies" / "one.json.xz"
    from knee.json_store import load_json

    record = load_json(evidence_path)
    record["capacity_exclusion"]["prepared_population_identity"][field] = value
    dump_json_atomic(evidence_path, record)
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["work"]["studies"][0]["capacity_exclusion"] = record["capacity_exclusion"]
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(CapacityReportError, match=code):
        evaluate_capacity(run, labels_path)


def test_unapplied_or_unattributed_exclusion_is_not_heldout(tmp_path: Path) -> None:
    run, labels_path = _make_run(tmp_path, _labels(["one"]), [("open", Fraction(1, 2))])
    evidence_path = run / "studies" / "one.json.xz"
    from knee.json_store import load_json

    record = load_json(evidence_path)
    record["capacity_exclusion"]["exclusion_status"] = "no_matching_attribution"
    dump_json_atomic(evidence_path, record)
    with pytest.raises(CapacityReportError, match="capacity_exclusion_not_applied"):
        evaluate_capacity(run, labels_path)


def test_per_study_prepared_capacity_route_needs_no_global_preparation_file(
    tmp_path: Path,
) -> None:
    run, labels_path = _make_run(tmp_path, _labels(["one"]), [("open", Fraction(1, 2))])
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    preparation_path = run / receipt["recall_preparation"]["path"]
    preparation_path.unlink()
    receipt["recall_preparation"] = {
        "path": None,
        "sha256": None,
        "bytes": 0,
        "cache_status": "study_excluded_per_study",
    }
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    report = evaluate_capacity(run, labels_path)

    assert report["run"]["study_count"] == 1
    assert (
        report["capacity_exclusions"]["one"]["prepared_population_identity"][
            "source_fingerprint"
        ]
        == report["capacity_exclusions"]["one"]["consumed_case_fingerprint"]
    )


def test_empty_mapping_is_a_valid_prepared_population_source_record(
    tmp_path: Path,
) -> None:
    run, labels_path = _make_run(tmp_path, _labels(["one"]), [("open", Fraction(1, 2))])
    evidence_path = run / "studies" / "one.json.xz"
    from knee.json_store import load_json

    record = load_json(evidence_path)
    record["capacity_exclusion"]["prepared_population_identity"]["source"] = {}
    dump_json_atomic(evidence_path, record)
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["work"]["studies"][0]["capacity_exclusion"] = record["capacity_exclusion"]
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    report = evaluate_capacity(run, labels_path)

    assert (
        report["capacity_exclusions"]["one"]["prepared_population_identity"]["source"]
        == {}
    )


def test_budget_skipped_study_is_refused_on_prepared_capacity_route(
    tmp_path: Path,
) -> None:
    run, labels_path = _make_run(tmp_path, _labels(["one"]), [("open", Fraction(1, 2))])
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["recall_preparation"] = {
        "path": None,
        "sha256": None,
        "bytes": 0,
        "cache_status": "study_excluded_per_study",
    }
    receipt["work"]["studies"][0]["study_status"] = "not_examined_budget"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(CapacityReportError, match="study_not_examined_budget:one"):
        evaluate_capacity(run, labels_path)


def test_exact_ranking_fraction_must_match_serialized_float(tmp_path: Path) -> None:
    run, labels_path = _make_run(tmp_path, _labels(["one"]), [("open", Fraction(1, 2))])
    evidence_path = run / "studies" / "one.json.xz"
    from knee.json_store import load_json

    record = load_json(evidence_path)
    record["questions"]["ACL"]["ranking"]["exact"] = {
        "numerator": "2",
        "denominator": "3",
    }
    dump_json_atomic(evidence_path, record)

    with pytest.raises(
        CapacityReportError, match="ranking_exact_value_mismatch:one:ACL"
    ):
        evaluate_capacity(run, labels_path)


def test_submission_must_match_retained_ranking(tmp_path: Path) -> None:
    run, labels_path = _make_run(tmp_path, _labels(["one"]), [("open", Fraction(1, 2))])
    submission = run / "submission.csv"
    with submission.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(SUBMISSION_COLUMNS)
        writer.writerow(("one", *["0.6" for _ in LABELS]))
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["submission"]["submission_sha256"] = hashlib.sha256(
        submission.read_bytes()
    ).hexdigest()
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(CapacityReportError, match="submission_ranking_mismatch"):
        evaluate_capacity(run, labels_path)


def test_incomplete_run_or_untrusted_evidence_path_is_refused(tmp_path: Path) -> None:
    run, labels_path = _make_run(tmp_path, _labels(["one"]), [("open", Fraction(1, 2))])
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["work"]["studies"][0]["evidence_path"] = "../elsewhere.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(CapacityReportError, match="evidence_path_outside_run"):
        evaluate_capacity(run, labels_path)


def test_cli_writes_fresh_json_and_markdown(tmp_path: Path) -> None:
    run, labels_path = _make_run(tmp_path, _labels(["one"]), [("open", Fraction(1, 2))])
    json_output = tmp_path / "report.json"
    markdown_output = tmp_path / "report.md"
    assert (
        main(
            [
                "--run",
                str(run),
                "--labels",
                str(labels_path),
                "--output",
                str(json_output),
                "--markdown",
                str(markdown_output),
            ]
        )
        == 0
    )
    report = json.loads(json_output.read_text(encoding="utf-8"))
    assert len(report["per_condition"]) == len(LABELS)
    assert "No combined or macro score" in markdown_output.read_text(encoding="utf-8")
    assert (
        main(
            [
                "--run",
                str(run),
                "--labels",
                str(labels_path),
                "--output",
                str(json_output),
            ]
        )
        == 2
    )
