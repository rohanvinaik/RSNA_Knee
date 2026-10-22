"""Versioned readout compatibility, preserving strict legacy reconciliation."""

from __future__ import annotations

import csv
import hashlib
import json
from fractions import Fraction

import pytest
from test_evaluate_squint_capacity import _make_run
from test_record_squint_experiment import _teacher

from knee.diagnosis.som_runtime import ARTIFACT_FILES, SCHEMA, SCOPE
from knee.diagnosis.squint_contracts import READOUT_POLICY_ID, serialize_condition_value
from knee.json_store import dump_json_atomic, load_json
from knee.study.tables import LABELS
from scripts.evaluate_squint_capacity import CapacityReportError, evaluate_capacity
from scripts.record_squint_experiment import record_experiment


def upgraded_run(run, *, navigation=False, grades=None):
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["readout_policy_id"] = READOUT_POLICY_ID
    source = receipt["submission"]["source_provenance"]
    source["readout_policy_id"] = READOUT_POLICY_ID
    pins = {name: hashlib.sha256(name.encode()).hexdigest() for name in ARTIFACT_FILES}
    if navigation:
        receipt["navigation"] = {
            "schema": SCHEMA,
            "scope": SCOPE,
            "labels": list(LABELS),
            "readout_policy_id": READOUT_POLICY_ID,
            "artifact_pins": pins,
        }
        source["navigation"] = {"scope": SCOPE, "artifact_pins": pins}
    rows = []
    for entry in receipt["work"]["studies"]:
        path = run / entry["evidence_path"]
        record = load_json(path)
        uid = record["study_uid"]
        record["readout_policy_id"] = READOUT_POLICY_ID
        values = {}
        raw = {
            q: grades[uid]
            if grades is not None
            else record["questions"][q]["ranking"]["value"]
            for q in LABELS
        }
        for question in LABELS:
            values[question] = serialize_condition_value(
                record["questions"][question]["finding"], raw[question]
            )
        if navigation:
            record["navigation"] = {
                "schema": SCHEMA,
                "scope": SCOPE,
                "artifact_pins": pins,
                "readout_policy_id": READOUT_POLICY_ID,
                "outcome": "applied",
                "numerical_values": raw,
                "readout_values": values.copy(),
            }
        record["values"] = values
        dump_json_atomic(path, record)
        rows.append([uid, *[str(values[q]) for q in LABELS]])
    with (run / "submission.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(receipt["submission"]["columns"])
        writer.writerows(rows)
    receipt["submission"]["submission_sha256"] = hashlib.sha256(
        (run / "submission.csv").read_bytes()
    ).hexdigest()
    receipt_path.write_text(json.dumps(receipt))
    return receipt


def labelled(uids):
    return [
        [uid, "fixture independently supplied report", *([truth] * 12)]
        for uid, truth in uids
    ]


def test_new_capacity_uses_actual_endpoints_without_rewriting_internal_ranks(tmp_path):
    run, labels = _make_run(
        tmp_path,
        labelled([("p", "1"), ("n", "0")]),
        [("assigned", Fraction(1, 10)), ("defeated", Fraction(9, 10))],
    )
    upgraded_run(run)
    result = evaluate_capacity(run, labels)
    assert result["per_condition"]["ACL"]["ordering"]["value"] == {
        "numerator": "1",
        "denominator": "1",
    }
    assert result["per_condition"]["ACL"]["positive"]["identified"] == 1
    assert result["run"]["readout_policy_id"] == READOUT_POLICY_ID
    assert (
        load_json(run / "studies/p.json.xz")["questions"]["ACL"]["ranking"]["value"]
        == 0.1
    )


def test_new_navigation_grade_changes_ordering_but_not_symbolic_open(tmp_path):
    run, labels = _make_run(
        tmp_path,
        labelled([("p", "1"), ("n", "0")]),
        [("open", Fraction(7, 10)), ("open", Fraction(3, 10))],
    )
    upgraded_run(run, navigation=True, grades={"p": 0.2, "n": 0.9})
    result = evaluate_capacity(run, labels)
    acl = result["per_condition"]["ACL"]
    assert acl["ordering"]["value"] == {"numerator": "0", "denominator": "1"}
    assert acl["positive"]["abstained"] == 1
    assert acl["negative"]["abstained"] == 1


def test_new_recorder_reads_author_endpoints_and_navigation_grades(tmp_path):
    run, labels = _make_run(
        tmp_path,
        labelled([("p", "1"), ("n", "0")]),
        [("assigned", Fraction(1, 10)), ("defeated", Fraction(9, 10))],
    )
    _teacher(run)
    upgraded_run(run, navigation=True, grades={"p": 0.01, "n": 0.99})
    report = record_experiment(
        run, labels, tmp_path / "report", protocol="teacher-readback"
    )
    assert report["per_condition"]["ACL"]["ordering"]["value"] == {
        "numerator": "1",
        "denominator": "1",
    }
    assert report["per_condition"]["ACL"]["positive"]["mean_ranking_value"] == 1
    assert report["per_condition"]["ACL"]["negative"]["mean_ranking_value"] == 0
    assert report["run"]["readout_policy_id"] == READOUT_POLICY_ID


@pytest.mark.parametrize("where", ["record", "submission_source", "navigation"])
def test_new_policy_must_agree_at_all_sources(tmp_path, where):
    run, labels = _make_run(
        tmp_path, labelled([("p", "1")]), [("open", Fraction(1, 2))]
    )
    receipt = upgraded_run(run, navigation=True, grades={"p": 0.7})
    if where == "submission_source":
        receipt["submission"]["source_provenance"]["readout_policy_id"] = "wrong"
        (run / "receipt.json").write_text(json.dumps(receipt))
    else:
        path = run / "studies/p.json.xz"
        record = load_json(path)
        target = record if where == "record" else record["navigation"]
        target["readout_policy_id"] = "wrong"
        dump_json_atomic(path, record)
    with pytest.raises(CapacityReportError, match="provenance|readout_policy"):
        evaluate_capacity(run, labels)


def test_unrecognized_future_policy_is_not_silently_legacy(tmp_path):
    run, labels = _make_run(
        tmp_path, labelled([("p", "1")]), [("open", Fraction(1, 2))]
    )
    receipt = upgraded_run(run)
    receipt["readout_policy_id"] = "unimplemented/v99"
    (run / "receipt.json").write_text(json.dumps(receipt))
    with pytest.raises(CapacityReportError, match="readout_policy_unknown"):
        evaluate_capacity(run, labels)


def test_new_readout_does_not_accept_a_changed_csv_even_with_rehashed_metadata(
    tmp_path,
):
    run, labels = _make_run(
        tmp_path, labelled([("p", "1")]), [("assigned", Fraction(3, 4))]
    )
    receipt = upgraded_run(run)
    with (run / "submission.csv").open(newline="") as stream:
        rows = list(csv.reader(stream))
    rows[1][1] = "0.8"
    with (run / "submission.csv").open("w", newline="") as stream:
        csv.writer(stream, lineterminator="\n").writerows(rows)
    receipt["submission"]["submission_sha256"] = hashlib.sha256(
        (run / "submission.csv").read_bytes()
    ).hexdigest()
    (run / "receipt.json").write_text(json.dumps(receipt))
    with pytest.raises(CapacityReportError, match="submission_readout_mismatch:p:ACL"):
        evaluate_capacity(run, labels)


def test_new_navigation_pins_are_exact_and_unknown_fields_are_not_allowed(tmp_path):
    run, labels = _make_run(
        tmp_path, labelled([("p", "1")]), [("open", Fraction(1, 2))]
    )
    receipt = upgraded_run(run, navigation=True, grades={"p": 0.7})
    receipt["submission"]["source_provenance"]["navigation"]["unverified_override"] = (
        True
    )
    (run / "receipt.json").write_text(json.dumps(receipt))
    with pytest.raises(
        CapacityReportError, match="submission_source_provenance_mismatch"
    ):
        evaluate_capacity(run, labels)


def test_new_policy_still_refuses_corrupt_internal_rational_rank(tmp_path):
    run, labels = _make_run(
        tmp_path, labelled([("p", "1")]), [("assigned", Fraction(3, 4))]
    )
    upgraded_run(run)
    path = run / "studies/p.json.xz"
    record = load_json(path)
    record["questions"]["ACL"]["ranking"]["exact"]["numerator"] = "1"
    dump_json_atomic(path, record)
    with pytest.raises(CapacityReportError, match="ranking_exact_value_mismatch"):
        evaluate_capacity(run, labels)
