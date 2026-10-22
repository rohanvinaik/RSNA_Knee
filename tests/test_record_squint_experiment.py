"""Two-sign recording intent; fixtures are not production transfer evidence."""

import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest
from test_evaluate_squint_capacity import _make_run

from knee.json_store import dump_json_atomic, load_json
from scripts.record_squint_experiment import ExperimentError, record_experiment

LABEL_COUNT = 12


def _labels(values):
    return [[uid, "fixture report", *([truth] * LABEL_COUNT)] for uid, truth in values]


def _teacher(run):
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["action"] = "infer"
    for entry in receipt["work"]["studies"]:
        entry.pop("capacity_exclusion", None)
        path = run / entry["evidence_path"]
        record = load_json(path)
        record.pop("capacity_exclusion", None)
        dump_json_atomic(path, record)
    receipt_path.write_text(json.dumps(receipt))


def test_both_truth_signs_open_and_missing_truth_keep_their_meanings(tmp_path):
    run, labels = _make_run(
        tmp_path,
        _labels(
            [("p", "1"), ("n", "0"), ("open", "1"), ("normal", "0"), ("blank", "")]
        ),
        [
            ("assigned", Fraction(7, 10)),
            ("assigned", Fraction(7, 10)),
            ("open", Fraction(1, 2)),
            ("defeated", Fraction(1, 5)),
            ("open", Fraction(1, 2)),
        ],
    )
    _teacher(run)
    report = record_experiment(
        run, labels, tmp_path / "report", protocol="teacher-readback"
    )
    result = report["per_condition"]["ACL"]
    assert result["positive"]["identified"] == 1
    assert result["positive"]["abstained"] == 1
    assert result["negative"]["identified"] == 1
    assert result["negative"]["wrong"] == 1
    assert result["negative"]["count"] == 2  # Blank is never normal.
    assert sum(result["unavailable_truth"].values()) == 1
    assert result["ordering"]["value"] == {"numerator": "5", "denominator": "8"}
    assert report["protocol"] == "teacher-readback"


def test_csv_ties_survive_finer_internal_rational_difference(tmp_path):
    run, labels = _make_run(
        tmp_path,
        _labels([("p", "1"), ("n", "0")]),
        [("open", Fraction(1, 2) + Fraction(1, 10**20)), ("open", Fraction(1, 2))],
    )
    report = record_experiment(
        run, labels, tmp_path / "report", protocol="whole-study-excluded"
    )
    ordering = report["per_condition"]["ACL"]["ordering"]
    assert ordering["equal"] == 1  # Both submitted values are exactly text "0.5".
    assert ordering["value"] == {"numerator": "1", "denominator": "2"}
    assert report["per_condition"]["ACL"]["positive"]["mean_ranking_value"] == 0.5


def test_protocol_mismatch_and_missing_exclusion_are_refused(tmp_path):
    run, labels = _make_run(tmp_path, _labels([("p", "1")]), [("open", Fraction(1, 2))])
    with pytest.raises(ExperimentError, match="protocol_action_mismatch"):
        record_experiment(run, labels, tmp_path / "wrong", protocol="teacher-readback")
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["work"]["studies"][0].pop("capacity_exclusion")
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="receipt_capacity_exclusion_mismatch"):
        record_experiment(
            run, labels, tmp_path / "missing", protocol="whole-study-excluded"
        )
    assert not (tmp_path / "missing").exists()


def test_comparison_reports_real_transitions_but_never_pairs_different_truth(tmp_path):
    first, labels = _make_run(
        tmp_path / "first",
        _labels([("p", "1"), ("n", "0")]),
        [("open", Fraction(1, 2)), ("assigned", Fraction(4, 5))],
    )
    _teacher(first)
    record_experiment(first, labels, tmp_path / "before", protocol="teacher-readback")
    second, labels2 = _make_run(
        tmp_path / "second",
        _labels([("p", "1"), ("n", "0")]),
        [("assigned", Fraction(4, 5)), ("defeated", Fraction(1, 5))],
    )
    _teacher(second)
    after = record_experiment(
        second,
        labels2,
        tmp_path / "after",
        protocol="teacher-readback",
        compare=tmp_path / "before/report.json",
    )
    change = after["comparison"]["per_condition"]["ACL"]
    assert after["comparison"]["status"] == "paired"
    assert change["assessment_transitions"] == {
        "abstained->identified": 1,
        "wrong->identified": 1,
    }
    assert change["outcome_transitions"] == {
        "open->assigned": 1,
        "assigned->defeated": 1,
    }
    different = labels2.read_text().replace(
        "fixture report", "different truth-source receipt"
    )
    labels2.write_text(different)
    incomparable = record_experiment(
        second,
        labels2,
        tmp_path / "incomparable",
        protocol="teacher-readback",
        compare=tmp_path / "before/report.json",
    )
    assert incomparable["comparison"]["status"] == "incomparable"
    assert "different_truth_source" in incomparable["comparison"]["reasons"]
    assert "per_condition" not in incomparable["comparison"]


@pytest.mark.parametrize("different", ["protocol", "cohort"])
def test_different_protocol_or_cohort_never_produces_paired_gains(tmp_path, different):
    first, labels = _make_run(
        tmp_path / "first", _labels([("p", "1")]), [("open", Fraction(1, 2))]
    )
    protocol = "whole-study-excluded" if different == "protocol" else "teacher-readback"
    if protocol == "teacher-readback":
        _teacher(first)
    record_experiment(first, labels, tmp_path / "before", protocol=protocol)
    uid = "q" if different == "cohort" else "p"
    second, labels2 = _make_run(
        tmp_path / "second", _labels([(uid, "1")]), [("assigned", Fraction(3, 4))]
    )
    _teacher(second)
    report = record_experiment(
        second,
        labels2,
        tmp_path / "after",
        protocol="teacher-readback",
        compare=tmp_path / "before/report.json",
    )
    assert report["comparison"]["status"] == "incomparable"
    assert "different_" + different in report["comparison"]["reasons"]
    assert "per_condition" not in report["comparison"]


def test_fresh_transfer_and_existing_output_are_not_relabelled(tmp_path):
    run, labels = _make_run(tmp_path, _labels([("p", "1")]), [("open", Fraction(1, 2))])
    with pytest.raises(
        ExperimentError, match="fresh_transfer_verified_population_evidence_required"
    ):
        record_experiment(run, labels, tmp_path / "fresh", protocol="fresh-transfer")
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("immutable")
    with pytest.raises(ExperimentError, match="output_already_exists"):
        record_experiment(run, labels, output, protocol="whole-study-excluded")
    assert sentinel.read_text() == "immutable"


def test_actual_cli_writes_three_readable_artifacts(tmp_path):
    run, labels = _make_run(tmp_path, _labels([("p", "1")]), [("open", Fraction(1, 2))])
    _teacher(run)
    script = Path(__file__).resolve().parents[1] / "scripts/record_squint_experiment.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--run",
            str(run),
            "--labels",
            str(labels),
            "--output",
            str(tmp_path / "cli"),
            "--protocol",
            "teacher-readback",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "recorded"
    assert {p.name for p in (tmp_path / "cli").iterdir()} == {
        "report.json",
        "rows.csv",
        "report.md",
    }


@pytest.mark.parametrize("where", ["entry", "record"])
@pytest.mark.parametrize("protocol", ["teacher-readback", "whole-study-excluded"])
def test_unexamined_study_never_becomes_recorded_abstention(tmp_path, where, protocol):
    run, labels = _make_run(tmp_path, _labels([("p", "1")]), [("open", Fraction(1, 2))])
    if protocol == "teacher-readback":
        _teacher(run)
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    entry = receipt["work"]["studies"][0]
    if where == "entry":
        entry["study_status"] = "not_examined_budget"
        receipt_path.write_text(json.dumps(receipt))
    else:
        path = run / entry["evidence_path"]
        record = load_json(path)
        record["study_status"] = "not_examined_budget"
        dump_json_atomic(path, record)
    with pytest.raises(ValueError, match="study_not_examined_budget:p"):
        record_experiment(run, labels, tmp_path / "report", protocol=protocol)
    assert not (tmp_path / "report").exists()


def test_examined_open_is_valid_uncertainty_and_boolean_is_not_a_count(tmp_path):
    run, labels = _make_run(tmp_path, _labels([("p", "1")]), [("open", Fraction(1, 2))])
    _teacher(run)
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["work"]["studies"][0]["study_status"] = "examined"
    path = run / receipt["work"]["studies"][0]["evidence_path"]
    record = load_json(path)
    record["study_status"] = "examined"
    dump_json_atomic(path, record)
    receipt_path.write_text(json.dumps(receipt))
    report = record_experiment(
        run, labels, tmp_path / "valid", protocol="teacher-readback"
    )
    assert report["per_condition"]["ACL"]["positive"]["abstained"] == 1
    assert report["per_condition"]["ACL"]["positive"]["wrong"] == 0
    receipt["studies"] = True
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(ExperimentError, match="study_count_invalid"):
        record_experiment(
            run, labels, tmp_path / "bool-count", protocol="teacher-readback"
        )


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("questions", None, "study_questions_missing:p"),
        ("questions", [], "study_questions_missing:p"),
        ("questions", {}, "question_missing:p:ACL"),
        ("values", None, "study_values_missing:p"),
        ("values", [], "study_values_missing:p"),
        ("values", {}, "study_value_missing:p:ACL"),
    ],
)
def test_malformed_teacher_mappings_have_named_direct_and_cli_refusals(
    tmp_path, field, value, reason
):
    run, labels = _make_run(tmp_path, _labels([("p", "")]), [("open", Fraction(1, 2))])
    _teacher(run)
    receipt = json.loads((run / "receipt.json").read_text())
    path = run / receipt["work"]["studies"][0]["evidence_path"]
    record = load_json(path)
    record[field] = value
    dump_json_atomic(path, record)
    with pytest.raises(ExperimentError, match=reason):
        record_experiment(run, labels, tmp_path / "direct", protocol="teacher-readback")
    script = Path(__file__).resolve().parents[1] / "scripts/record_squint_experiment.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--run",
            str(run),
            "--labels",
            str(labels),
            "--output",
            str(tmp_path / "cli"),
            "--protocol",
            "teacher-readback",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert result.stderr.strip() == reason
    assert not result.stdout
    assert not (tmp_path / "direct").exists()
    assert not (tmp_path / "cli").exists()


@pytest.mark.parametrize("question", [None, [], {}])
def test_malformed_question_is_named_instead_of_dereferenced(tmp_path, question):
    run, labels = _make_run(tmp_path, _labels([("p", "1")]), [("open", Fraction(1, 2))])
    _teacher(run)
    receipt = json.loads((run / "receipt.json").read_text())
    path = run / receipt["work"]["studies"][0]["evidence_path"]
    record = load_json(path)
    record["questions"]["ACL"] = question
    dump_json_atomic(path, record)
    with pytest.raises(ExperimentError, match="question_missing:p:ACL"):
        record_experiment(run, labels, tmp_path / "report", protocol="teacher-readback")
    assert not (tmp_path / "report").exists()
