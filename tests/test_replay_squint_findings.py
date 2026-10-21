"""Intent tests for replaying saved squint evidence through the current contracts.

What the tool owes (Rohan's rules for this build, 2026-10-21): it is an honest
lightweight replay. It reruns the *current* ``combine_condition`` and
``rank_condition`` over exactly the evidence a run saved, so a change to the
contracts can be read on retained records; it decodes no image, locates and
recalls nothing, and never reads a label as a feature. Unknown stays unknown,
a partial dataset is never passed off as a complete one, and a malformed or
missing study is named, never dropped.

Every fixture is a synthetic saved study in the real ``knee.squint-study/v1``
shape, written through the project's own ``dump_json_atomic``. Each test chooses
its saved outcomes explicitly and builds evidence whose current outcome is
fixed by the single-tissue and alternative-branch contracts, so none of them
depends on how a later contract fix resolves a configuration conflict. Both signs
of every decision are pinned, and no number here is tuned to a metric.
"""

from __future__ import annotations

import csv
import hashlib
import json
import lzma
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

import scripts.replay_squint_findings as replay
from knee.diagnosis import squint_contracts
from knee.diagnosis.squint_contracts import (
    FINDING_SCHEMA,
    ContractError,
    combine_condition,
    rank_condition,
)
from knee.json_store import dump_json_atomic
from knee.study.tables import LABELS, TRAIN_COLUMNS

REPO = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# builders: saved evidence, saved findings, a run directory, a label table
# ---------------------------------------------------------------------------


def _row(case_id: str, call: int, *, k: int = 1, m: int = 2) -> dict:
    """A sourced-trust case row whose squared cosine is exactly (k/m)**2."""
    return {
        "case_id": case_id,
        "call": call,
        "terms": {"dot": k, "left_norm_sq": m, "right_norm_sq": m},
        "common_speaking_banks": ["bank"],
        "trust": {"numerator": 1, "denominator": 2, "source": "sourced-envelope"},
        "reaches_trust": True,
    }


def _voice(outcome: str, *rows: dict, **extra: object) -> dict:
    return {"outcome": outcome, "case_terms": list(rows), "vetoed_answers": [], **extra}


def _acl(state: str, *, k: int = 1, m: int = 2) -> dict[str, dict]:
    """ACL object evidence: its own tissue present, absent, or never read."""
    if state == "present":
        return {"ACL": {"acl": _voice("present", _row("acl-pos", 1, k=k, m=m))}}
    if state == "absent":
        return {"ACL": {"acl": _voice("absent", _row("acl-neg", -1, k=k, m=m))}}
    return {}


def _stub(question: str, outcome: str, reason: str = "saved:stub") -> dict:
    """A saved finding with a chosen outcome, serialized by the contract's own rank."""
    ranking = rank_condition({"outcome": outcome, "recall_evidence": []})
    return {
        "schema": FINDING_SCHEMA,
        "question": question,
        "contract_id": "saved-contract",
        "policy_id": "saved-policy",
        "outcome": outcome,
        "reason": reason,
        "evidence": {
            "decided_by": [],
            "unresolved_subjects": [],
            "unsupported_positive_subjects": [],
            "joint_configuration_coverage": {
                "status": "not_present",
                "eligible_case_ids": {"positive": [], "negative": []},
            },
        },
        "observation_requests": [],
        "recall_evidence": {},
        "rank": ranking,
        "probability": ranking["value"],
    }


def _study(
    uid: str,
    evidence: dict[str, dict] | None = None,
    saved: dict[str, dict] | None = None,
    *,
    status: str | None = "examined",
) -> dict:
    """A saved study. A condition not given a saved finding keeps the current one."""
    evidence = evidence or {}
    saved = saved or {}
    questions = {}
    for question in LABELS:
        objects = evidence.get(question, {})
        finding = saved.get(question) or combine_condition(question, objects)
        questions[question] = {
            "finding": finding,
            "ranking": finding["rank"],
            "objects": objects,
        }
    record = {
        "schema": "knee.squint-study/v1",
        "study_uid": uid,
        "memory_revision": "memory-r1",
        "questions": questions,
        "values": {q: item["ranking"]["value"] for q, item in questions.items()},
        "objects": {},
        "observations": [],
        "work": {"source_mode": "raw_squint_case_recall"},
        "unresolved_observation_requests": [],
    }
    if status is not None:
        record["study_status"] = status
    return record


def _run(
    tmp_path: Path,
    studies: dict[str, dict],
    *,
    receipt: bool = True,
    raw: dict[str, bytes] | None = None,
    absent: tuple[str, ...] = (),
) -> Path:
    """A run directory as ``run_squint_cli`` leaves it: studies/ and a receipt."""
    run = tmp_path / "run"
    (run / "studies").mkdir(parents=True)
    listed = []
    for uid, record in studies.items():
        path = dump_json_atomic(run / "studies" / f"{uid}.json", record)
        listed.append({"study_uid": uid, "evidence_path": str(path.relative_to(run))})
    for uid, data in (raw or {}).items():
        path = run / "studies" / f"{uid}.json.xz"
        path.write_bytes(data)
        listed.append({"study_uid": uid, "evidence_path": f"studies/{path.name}"})
    for uid in absent:
        listed.append({"study_uid": uid, "evidence_path": f"studies/{uid}.json.xz"})
    if receipt:
        document = {
            "schema": "knee.squint-run/v1",
            "action": "capacity",
            "source_mode": "raw_squint_case_recall",
            "studies": len(listed),
            "memory_revision": "memory-r1",
            "memory_manifest_sha256": "memory-sha",
            "work": {"studies": listed},
        }
        (run / "receipt.json").write_text(json.dumps(document), encoding="utf-8")
    return run


def _labels(
    tmp_path: Path, rows: dict[str, dict[str, str]], *, default: str = "0"
) -> Path:
    path = tmp_path / "train.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(TRAIN_COLUMNS)
        for uid, values in rows.items():
            writer.writerow(
                [uid, "fixture report"] + [values.get(q, default) for q in LABELS]
            )
    return path


def _xz(data: bytes) -> bytes:
    return lzma.compress(data, format=lzma.FORMAT_XZ)


def _codes(report: dict, **where: object) -> list[str]:
    return [
        issue["code"]
        for issue in report["issues"]
        if all(issue[key] == value for key, value in where.items())
    ]


def _row_for(report: dict, uid: str, question: str) -> dict:
    (row,) = [
        item
        for item in report["rows"]
        if item["study_uid"] == uid and item["question"] == question
    ]
    return row


def _canonical_sha(value: object) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("ascii")).hexdigest()


# ---------------------------------------------------------------------------
# the replay reruns the current contracts over the saved evidence
# ---------------------------------------------------------------------------


def test_replay_matches_a_saved_finding_the_current_contracts_would_make(tmp_path):
    run = _run(
        tmp_path,
        {
            "s1": _study("s1", _acl("present")),
            "s2": _study("s2", _acl("absent")),
            "s3": _study("s3"),
        },
    )
    report = replay.replay_run(run)

    assert report["dataset"]["status"] == "complete"
    assert report["dataset"]["studies"] == {
        "listed": 3,
        "complete": 3,
        "partial": 0,
        "not_replayed": 0,
    }
    assert len(report["rows"]) == 3 * len(LABELS)
    for row in report["rows"]:
        assert row["disposition"] == "replayed"
        assert row["identical_finding"] is True
        assert row["changed"] == []
        assert row["rank_delta"] == {"numerator": "0", "denominator": "1"}
        assert row["rank_embedded_equals_standalone"] is True
    summary = report["bins"]["complete_studies"]
    assert summary["identical_to_saved"] == summary["replayed"] == 3 * len(LABELS)
    assert summary["outcome_changed"] == summary["any_field_changed"] == 0
    acl = summary["per_condition"]["ACL"]["transitions"]
    assert acl["assigned"]["assigned"] == 1
    assert acl["defeated"]["defeated"] == 1
    assert acl["open"]["open"] == 1


def test_the_saved_finding_is_compared_never_copied(tmp_path):
    """Sign one: a saved open that the evidence now assigns is a changed finding.
    Sign two: the saved assigned that the evidence still assigns is not."""
    run = _run(
        tmp_path,
        {
            "was_open": _study(
                "was_open", _acl("present"), {"ACL": _stub("ACL", "open")}
            ),
            "was_assigned": _study(
                "was_assigned", _acl("present"), {"ACL": _stub("ACL", "assigned")}
            ),
        },
    )
    report = replay.replay_run(run)

    moved = _row_for(report, "was_open", "ACL")
    assert moved["saved"]["outcome"] == "open"
    assert moved["current"]["outcome"] == "assigned"
    assert moved["identical_finding"] is False
    assert "outcome" in moved["changed"]
    # the exact value is the contract's own serialization of the saved evidence:
    # assigned tier, best positive squared cosine (1/2)**2 and no negative support
    grade = (1 + Fraction(1, 4)) / 2
    expected = (Fraction(7) + grade) / 9
    assert moved["current"]["rank"]["exact"] == {
        "numerator": str(expected.numerator),
        "denominator": str(expected.denominator),
    }
    delta = Fraction(
        int(moved["rank_delta"]["numerator"]), int(moved["rank_delta"]["denominator"])
    )
    assert delta == expected - Fraction(1, 2)  # the saved stub is the neutral open
    held = _row_for(report, "was_assigned", "ACL")
    assert held["current"]["outcome"] == held["saved"]["outcome"] == "assigned"
    assert "outcome" not in held["changed"]


def test_the_current_function_is_the_one_that_replays(tmp_path, monkeypatch):
    """The outcome in the report follows whichever ``combine_condition`` is current."""
    run = _run(tmp_path, {"s1": _study("s1", _acl("present"))})
    real = replay.combine_condition
    seen = []

    def current(question, objects):
        seen.append(question)
        finding = real(question, objects)
        if question == "ACL":
            return {
                **finding,
                "outcome": "open",
                "rank": rank_condition({"outcome": "open"}),
            }
        return finding

    before = replay.replay_run(run)
    monkeypatch.setattr(replay, "combine_condition", current)
    after = replay.replay_run(run)

    assert _row_for(before, "s1", "ACL")["current"]["outcome"] == "assigned"
    assert _row_for(after, "s1", "ACL")["current"]["outcome"] == "open"
    assert _row_for(after, "s1", "ACL")["saved"]["outcome"] == "assigned"
    assert seen == list(LABELS)  # one call per condition, in the official order


def test_saved_terms_reach_the_contracts_exactly_as_saved(tmp_path, monkeypatch):
    evidence = _acl("present", k=3, m=7)
    run = _run(tmp_path, {"s1": _study("s1", evidence)})
    received = {}
    real = replay.combine_condition

    def spy(question, objects):
        received[question] = json.loads(json.dumps(objects))
        return real(question, objects)

    monkeypatch.setattr(replay, "combine_condition", spy)
    report = replay.replay_run(run)

    assert received["ACL"] == evidence["ACL"]  # every term, as saved
    assert received["MCL"] == {}  # nothing is added for an unread condition
    row = _row_for(report, "s1", "ACL")
    assert row["input_sha256"] == _canonical_sha(evidence["ACL"])
    assert row["input"]["acl"] == {
        "outcome": "present",
        "case_terms": 1,
        "decision_scope": None,
    }
    # sign two: one different term is a different input
    other = _acl("present", k=3, m=8)
    assert _canonical_sha(other["ACL"]) != row["input_sha256"]


def test_case_and_query_terms_are_retained_in_the_comparison(tmp_path):
    evidence = {
        "ACL": {
            "acl": _voice(
                "present", _row("pos-a", 1, k=1, m=2), _row("neg-a", -1, k=1, m=3)
            )
        }
    }
    run = _run(tmp_path, {"s1": _study("s1", evidence)})
    current = _row_for(replay.replay_run(run), "s1", "ACL")["current"]["rank"]

    assert current["positive_case_ids"] == ["pos-a"]
    assert current["negative_case_ids"] == ["neg-a"]
    assert current["s_plus"] == {
        "exact": {"numerator": "1", "denominator": "4"},
        "available": True,
    }
    assert current["s_minus"] == {
        "exact": {"numerator": "1", "denominator": "9"},
        "available": True,
    }
    assert current["eligible_term_count"] == 2
    assert current["rejected_term_count"] == 0


def test_configuration_coverage_retains_counterevidence_and_competing_sites():
    coverage = {
        "status": "covered_warranted_cases",
        "state": "positive",
        "eligible_case_ids": {"positive": ["config-a"], "negative": []},
        "counterevidence_case_ids": ["normal-b"],
        "competing_partial_counterevidence": {"normal-b": ["femur", "tibia"]},
    }
    finding = {
        "outcome": "open",
        "reason": "configuration_partial_presentations_compete",
        "evidence": {"joint_configuration_coverage": coverage},
    }
    ranking = rank_condition({"outcome": "open", "recall_evidence": []})

    projected = replay._projection(finding, ranking)

    assert projected["configuration"] == coverage


def test_configuration_coverage_retains_competing_anatomical_counterevidence():
    """Sign one: the sites where a covered positive case and a normal anatomical
    reading compete are kept as the contract wrote them. Sign two: a coverage saved
    before the field existed is projected without it, never given an empty one."""
    coverage = {
        "status": "covered_warranted_cases",
        "state": "positive",
        "eligible_case_ids": {"positive": ["config-a"], "negative": []},
        "competing_anatomical_counterevidence": ["femur", "tibia"],
    }
    finding = {
        "outcome": "open",
        "evidence": {"joint_configuration_coverage": coverage},
    }
    ranking = rank_condition({"outcome": "open", "recall_evidence": []})

    assert replay._projection(finding, ranking)["configuration"] == coverage

    older = {
        key: value
        for key, value in coverage.items()
        if key != "competing_anatomical_counterevidence"
    }
    finding["evidence"]["joint_configuration_coverage"] = older
    assert replay._projection(finding, ranking)["configuration"] == older


def _anatomy_against_configuration(*, femur_reads_normal: bool) -> dict[str, dict]:
    """Medial OA evidence: a covered configuration case, and perhaps a normal femur.

    The whole-question case speaks over the femur and tibia banks, so it is covered
    on the femur; a femur the anatomy reads as normal competes with it there.
    """
    banks = ["object/femur/bank", "object/tibia/bank"]
    case = {**_row("config-pos", 1), "common_speaking_banks": banks}
    objects = {"diagnosis/Medial OA": _voice("present", case)}
    if femur_reads_normal:
        objects["femur"] = _voice("absent", _row("femur-neg", -1))
    return {"Medial OA": objects}


def test_competing_anatomical_counterevidence_is_compared_on_both_sides(tmp_path):
    """Sign one: a covered configuration case and a normal femur compete, so the
    finding stays open on it and the saved and the replayed projection both name the
    femur. Sign two: with no normal femur nothing competes and both name nothing. A
    saved finding that disagreed on it is a changed configuration, however alike the
    rest of it is."""
    competing = _anatomy_against_configuration(femur_reads_normal=True)
    quiet = _anatomy_against_configuration(femur_reads_normal=False)
    disagreeing = combine_condition("Medial OA", competing["Medial OA"])
    coverage = disagreeing["evidence"]["joint_configuration_coverage"]
    coverage["competing_anatomical_counterevidence"] = []
    run = _run(
        tmp_path,
        {
            "competing": _study("competing", competing),
            "quiet": _study("quiet", quiet),
            "disagreeing": _study("disagreeing", competing, {"Medial OA": disagreeing}),
        },
    )
    report = replay.replay_run(run)

    key = "competing_anatomical_counterevidence"
    held = _row_for(report, "competing", "Medial OA")
    assert held["current"]["outcome"] == "open"
    assert held["current"]["reason"] == "configuration_anatomy_counterevidence"
    assert held["saved"]["configuration"][key] == ["femur"]
    assert held["current"]["configuration"][key] == ["femur"]
    assert held["changed"] == []
    nothing = _row_for(report, "quiet", "Medial OA")
    assert nothing["current"]["outcome"] == "assigned"
    assert nothing["saved"]["configuration"][key] == []
    assert nothing["current"]["configuration"][key] == []
    assert nothing["changed"] == []
    moved = _row_for(report, "disagreeing", "Medial OA")
    assert moved["saved"]["configuration"][key] == []
    assert moved["current"]["configuration"][key] == ["femur"]
    assert moved["changed"] == ["configuration"]  # the only field that moved
    assert moved["identical_finding"] is False


def test_saved_decision_scope_marks_are_replayed_and_counted_not_assumed(tmp_path):
    """A small part read only over its expected area grades and never decides; a
    record saved before the mark existed carries none, and the report says so."""
    marked = {
        "Medial Meniscus": {
            "medial_meniscus": _voice(
                "present", _row("mm", 1), decision_scope="grade_only"
            )
        }
    }
    plain = {"Medial Meniscus": {"medial_meniscus": _voice("present", _row("mm", 1))}}
    run = _run(
        tmp_path, {"marked": _study("marked", marked), "plain": _study("plain", plain)}
    )
    report = replay.replay_run(run)

    assert _row_for(report, "marked", "Medial Meniscus")["current"]["outcome"] == "open"
    assert (
        _row_for(report, "plain", "Medial Meniscus")["current"]["outcome"] == "assigned"
    )
    marks = report["saved_epoch"]["marks_in_saved_evidence"]["decision_scope"]
    assert marks == {"absent": 1, "grade_only": 1}


# ---------------------------------------------------------------------------
# labels are read only after the replay, and never reach it
# ---------------------------------------------------------------------------


def test_labels_are_opened_only_after_every_study_is_replayed(tmp_path, monkeypatch):
    run = _run(tmp_path, {"s1": _study("s1", _acl("present")), "s2": _study("s2")})
    labels = _labels(tmp_path, {"s1": {"ACL": "1"}, "s2": {"ACL": "0"}})
    events = []
    real_combine, real_read = replay.combine_condition, replay.read_labels

    def combine(question, objects):
        events.append("combine")
        return real_combine(question, objects)

    def read(path):
        events.append("labels")
        return real_read(path)

    monkeypatch.setattr(replay, "combine_condition", combine)
    monkeypatch.setattr(replay, "read_labels", read)
    replay.build_report(run, labels_path=labels)

    assert events.count("labels") == 1
    assert events.count("combine") == 2 * len(LABELS)
    assert events.index("labels") == len(events) - 1  # after the last combination


def test_flipping_every_label_changes_the_evaluation_and_nothing_replayed(tmp_path):
    run = _run(
        tmp_path,
        {"s1": _study("s1", _acl("present")), "s2": _study("s2", _acl("absent"))},
    )
    ones = _labels(tmp_path, {"s1": {}, "s2": {}}, default="1")
    zeros = tmp_path / "zeros.csv"
    zeros.write_bytes(ones.read_bytes().replace(b",1", b",0"))
    by_ones = replay.build_report(run, labels_path=ones)
    by_zeros = replay.build_report(run, labels_path=zeros)

    for part in ("rows", "bins", "epoch", "studies", "issues", "dataset"):
        assert by_ones[part] == by_zeros[part], part
    assert by_ones["inputs"]["evidence"] == by_zeros["inputs"]["evidence"]
    acl_ones = by_ones["evaluation"]["bins"]["complete_studies"]["per_condition"]["ACL"]
    acl_zeros = by_zeros["evaluation"]["bins"]["complete_studies"]["per_condition"][
        "ACL"
    ]
    # sign one: all positive truth: the assigned study is identified, the defeated is wrong
    assert acl_ones["replayed"]["positive"] == {
        "identified": 1,
        "abstained": 0,
        "wrong": 1,
        "unavailable": 0,
        "count": 2,
    }
    # sign two: all negative truth: the same findings are scored the other way round
    assert acl_zeros["replayed"]["negative"] == {
        "identified": 1,
        "abstained": 0,
        "wrong": 1,
        "unavailable": 0,
        "count": 2,
    }
    assert acl_zeros["replayed"]["positive"]["count"] == 0


def test_a_replay_alone_never_touches_a_labels_file(tmp_path, monkeypatch):
    run = _run(tmp_path, {"s1": _study("s1")})

    def forbidden(path):
        raise AssertionError("labels were read without being asked for")

    monkeypatch.setattr(replay, "read_labels", forbidden)
    report = replay.build_report(run)

    assert report["scope"]["labels_read"] is False
    assert report["evaluation"] == {"status": "not_requested", "labels_read": False}
    assert "labels" not in report["inputs"]


def test_a_malformed_label_table_is_refused_by_name_after_the_replay(tmp_path):
    run = _run(tmp_path, {"s1": _study("s1")})
    bad = tmp_path / "bad.csv"
    bad.write_text("StudyInstanceUID,wrong\ns1,1\n", encoding="utf-8")
    with pytest.raises(replay.ReplayError, match="labels_columns_invalid"):
        replay.build_report(run, labels_path=bad)
    twice = _labels(tmp_path, {"s1": {}})
    twice.write_text(twice.read_text() + twice.read_text().splitlines()[1] + "\n")
    with pytest.raises(replay.ReplayError, match="labels_study_uid_duplicate:s1"):
        replay.build_report(run, labels_path=twice)
    with pytest.raises(replay.ReplayError, match="labels_unreadable"):
        replay.build_report(run, labels_path=tmp_path / "absent.csv")


# ---------------------------------------------------------------------------
# identified / abstained / wrong, and the transitions from the saved outcomes
# ---------------------------------------------------------------------------


def _six_acl_studies(tmp_path: Path, saved: str | None) -> tuple[Path, Path]:
    states = {
        "p_assigned": "present",
        "p_open": "none",
        "p_defeated": "absent",
        "n_defeated": "absent",
        "n_open": "none",
        "n_assigned": "present",
    }
    studies = {
        uid: _study(
            uid, _acl(state), None if saved is None else {"ACL": _stub("ACL", saved)}
        )
        for uid, state in states.items()
    }
    truth = {uid: {"ACL": "1" if uid.startswith("p_") else "0"} for uid in states}
    return _run(tmp_path, studies), _labels(tmp_path, truth)


def test_identified_abstained_and_wrong_are_counted_by_truth_sign(tmp_path):
    run, labels = _six_acl_studies(tmp_path, saved="open")
    report = replay.build_report(run, labels_path=labels)
    acl = report["evaluation"]["bins"]["complete_studies"]["per_condition"]["ACL"]

    # the replayed side: decisive and correct / open / decisive and incorrect
    for sign in ("positive", "negative"):
        assert acl["replayed"][sign] == {
            "identified": 1,
            "abstained": 1,
            "wrong": 1,
            "unavailable": 0,
            "count": 3,
        }
    # the saved side was open everywhere: all abstained, none identified or wrong
    for sign in ("positive", "negative"):
        assert acl["saved"][sign] == {
            "identified": 0,
            "abstained": 3,
            "wrong": 0,
            "unavailable": 0,
            "count": 3,
        }
    # and the transitions by truth say where the movement happened
    positive = acl["transitions_by_truth"]["positive"]
    assert positive["open"] == {
        "assigned": 1,
        "defeated": 1,
        "open": 1,
        "unavailable": 0,
    }
    assert positive["assigned"] == dict.fromkeys(positive, 0)
    assert report["evaluation"]["labels_read_after_replay"] is True


def test_blank_unrecognized_and_absent_labels_are_unavailable_never_negative(tmp_path):
    run = _run(
        tmp_path,
        {name: _study(name, _acl("absent")) for name in ("blank", "odd", "gone", "ok")},
    )
    labels = _labels(
        tmp_path,
        {
            "blank": {"ACL": ""},
            "odd": {"ACL": "maybe"},
            "ok": {"ACL": "0"},
        },
    )
    report = replay.build_report(run, labels_path=labels)
    acl = report["evaluation"]["bins"]["complete_studies"]["per_condition"]["ACL"]

    assert acl["unavailable_truth"] == {
        "not_given": 1,
        "study_not_in_label_source": 1,
        "unrecognized": 1,
    }
    assert acl["replayed"]["negative"]["count"] == 1  # only the literal 0
    assert acl["replayed"]["negative"]["identified"] == 1
    assert acl["replayed"]["positive"]["count"] == 0
    completeness = report["evaluation"]["label_completeness"]
    assert completeness == {"complete": 1, "partial": 2, "study_not_in_label_source": 1}


def test_transitions_from_the_saved_outcomes_are_a_matrix_per_condition(tmp_path):
    run = _run(
        tmp_path,
        {
            "open_to_assigned": _study(
                "open_to_assigned", _acl("present"), {"ACL": _stub("ACL", "open")}
            ),
            "assigned_stays": _study(
                "assigned_stays", _acl("present"), {"ACL": _stub("ACL", "assigned")}
            ),
            "defeated_to_open": _study(
                "defeated_to_open", None, {"ACL": _stub("ACL", "defeated")}
            ),
        },
    )
    bin_ = replay.replay_run(run)["bins"]["complete_studies"]
    acl = bin_["per_condition"]["ACL"]["transitions"]

    expected = {
        saved: dict.fromkeys(("assigned", "defeated", "open", "unavailable"), 0)
        for saved in ("assigned", "defeated", "open", "unavailable")
    }
    expected["open"]["assigned"] = 1
    expected["assigned"]["assigned"] = 1
    expected["defeated"]["open"] = 1
    assert acl == expected
    # the other eleven conditions were saved by the current contracts: unchanged
    for question in LABELS[1:]:
        matrix = bin_["per_condition"][question]["transitions"]
        assert matrix["open"]["open"] == 3
        assert sum(sum(row.values()) for row in matrix.values()) == 3
    assert bin_["outcome_changed"] == 2
    # Full finding equality also sees the unchanged ACL assignment's reason
    # change from the synthetic saved stub to the current contract reason.
    assert bin_["identical_to_saved"] == 3 * len(LABELS) - 3
    unchanged_outcome = _row_for(replay.replay_run(run), "assigned_stays", "ACL")
    assert (
        unchanged_outcome["saved"]["outcome"] == unchanged_outcome["current"]["outcome"]
    )
    assert "outcome" not in unchanged_outcome["changed"]
    assert "reason" in unchanged_outcome["changed"]


def test_the_transition_matrix_names_what_could_not_be_compared(tmp_path):
    record = _study("s1", _acl("present"))
    del record["questions"]["ACL"]["finding"]
    run = _run(tmp_path, {"s1": record})
    report = replay.replay_run(run)

    acl = report["bins"]["partial_studies"]["per_condition"]["ACL"]["transitions"]
    assert acl["unavailable"]["assigned"] == 1  # nothing saved, assigned now
    assert _codes(report, study_uid="s1", question="ACL") == ["saved_finding_missing"]
    row = _row_for(report, "s1", "ACL")
    assert row["changed"] is None and row["identical_finding"] is None
    assert row["rank_delta"] is None
    assert row["current"]["outcome"] == "assigned"


# ---------------------------------------------------------------------------
# a complete dataset and a partial one are never pooled
# ---------------------------------------------------------------------------


def test_partial_studies_are_tallied_apart_from_complete_ones(tmp_path):
    no_mcl = _study("short", _acl("present"))
    del no_mcl["questions"]["MCL"]
    run = _run(
        tmp_path,
        {
            "whole": _study("whole", _acl("present")),
            "budget": _study("budget", status="not_examined_budget"),
            "short": no_mcl,
        },
        absent=("lost",),
    )
    labels = _labels(
        tmp_path,
        {name: {"ACL": "1"} for name in ("whole", "budget", "short", "lost")},
    )
    report = replay.build_report(run, labels_path=labels)

    assert report["dataset"]["status"] == "partial"
    assert report["dataset"]["studies"] == {
        "listed": 4,
        "complete": 1,
        "partial": 2,
        "not_replayed": 1,
    }
    assert report["dataset"]["partial_because"] == {
        "evidence_file_missing": 1,
        "question_missing": 1,
        "study_not_examined_budget": 1,
    }
    assert report["bins"]["complete_studies"]["study_count"] == 1
    assert report["bins"]["partial_studies"]["study_count"] == 2
    bins = report["evaluation"]["bins"]
    assert set(bins) == {"complete_studies", "partial_studies"}  # never a pooled bin
    whole = bins["complete_studies"]["per_condition"]["ACL"]["replayed"]["positive"]
    mixed = bins["partial_studies"]["per_condition"]["ACL"]["replayed"]["positive"]
    assert whole == {
        "identified": 1,
        "abstained": 0,
        "wrong": 0,
        "unavailable": 0,
        "count": 1,
    }
    assert mixed == {  # the budget study is open, the short study still assigned ACL
        "identified": 1,
        "abstained": 1,
        "wrong": 0,
        "unavailable": 0,
        "count": 2,
    }
    # the study whose file is gone is named, and appears in no bin
    assert _codes(report, study_uid="lost") == ["evidence_file_missing"]
    assert [s["disposition"] for s in report["studies"]] == [
        "complete",
        "partial",
        "partial",
        "not_replayed",
    ]


def test_when_every_study_is_whole_the_dataset_is_complete_and_nothing_is_partial(
    tmp_path,
):
    run = _run(tmp_path, {name: _study(name) for name in ("a", "b")})
    labels = _labels(tmp_path, {"a": {}, "b": {}})
    report = replay.build_report(run, labels_path=labels)

    assert report["dataset"]["status"] == "complete"
    assert report["dataset"]["partial_because"] == {}
    assert report["bins"]["partial_studies"]["study_count"] == 0
    assert report["evaluation"]["bins"]["partial_studies"]["study_count"] == 0
    assert report["dataset"]["expected"] == {
        "source": "receipt",
        "verifiable": True,
        "count": 2,
    }


def test_a_study_that_was_not_examined_is_open_everywhere_and_partial(tmp_path):
    run = _run(tmp_path, {"idle": _study("idle", status="not_examined_budget")})
    report = replay.replay_run(run)

    assert _codes(report, study_uid="idle") == ["study_not_examined_budget"]
    assert {row["current"]["outcome"] for row in report["rows"]} == {"open"}
    assert report["studies"][0]["disposition"] == "partial"
    assert report["studies"][0]["study_status"] == "not_examined_budget"


def test_a_run_without_a_receipt_cannot_be_called_complete(tmp_path):
    run = _run(tmp_path, {"a": _study("a"), "b": _study("b")}, receipt=False)
    report = replay.replay_run(run)

    assert report["run"]["study_index"] == "directory_listing"
    assert report["dataset"]["status"] == "partial"
    assert report["dataset"]["expected"] == {
        "source": "directory_listing",
        "verifiable": False,
        "count": None,
    }
    assert report["dataset"]["partial_because"] == {"receipt_missing": 1}
    # the studies are still replayed, each complete in itself
    assert [s["disposition"] for s in report["studies"]] == ["complete", "complete"]


def test_supplied_expected_uids_establish_the_universe_without_a_receipt(tmp_path):
    run = _run(tmp_path, {"a": _study("a"), "b": _study("b")}, receipt=False)
    expected = tmp_path / "expected.txt"
    expected.write_text("b\n\na\n", encoding="utf-8")
    report = replay.build_report(run, expected_uids_path=expected)

    assert report["dataset"]["status"] == "complete"
    assert report["dataset"]["expected"]["source"] == "expected_uids"
    assert [s["study_uid"] for s in report["studies"]] == ["b", "a"]  # their order
    assert (
        report["inputs"]["expected_uids"]["sha256"]
        == hashlib.sha256(expected.read_bytes()).hexdigest()
    )
    # one study the run never produced, one it produced that nobody expected
    expected.write_text("a\nc\n", encoding="utf-8")
    report = replay.build_report(run, expected_uids_path=expected)
    assert report["dataset"]["status"] == "partial"
    assert sorted(_codes(report)) == sorted(
        [
            "receipt_missing",
            "study_not_in_expected",
            "expected_study_not_in_run",
            "evidence_file_missing",
        ]
    )
    assert _codes(report, study_uid="c") == ["evidence_file_missing"]


@pytest.mark.parametrize(
    ("content", "code"),
    [
        ("", "expected_uids_empty"),
        ("a\nb\na\n", "expected_uids_duplicate:a"),
    ],
)
def test_a_malformed_expected_uid_list_is_refused_by_name(tmp_path, content, code):
    path = tmp_path / "expected.txt"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(replay.ReplayError, match=code):
        replay.read_expected_uids(path)
    with pytest.raises(replay.ReplayError, match="expected_uids_unreadable"):
        replay.read_expected_uids(tmp_path / "nope.txt")


# ---------------------------------------------------------------------------
# a malformed or missing study, question or file is named, never dropped
# ---------------------------------------------------------------------------


def _without(record: dict, *path: str) -> dict:
    node = record
    for key in path[:-1]:
        node = node[key]
    del node[path[-1]]
    return record


def _with(record: dict, value: object, *path: str) -> dict:
    node = record
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    return record


MALFORMED_STUDIES = {
    "wrong_schema": (
        lambda r: _with(r, "knee.other/v9", "schema"),
        "evidence_schema_mismatch",
        "not_replayed",
    ),
    "wrong_uid": (
        lambda r: _with(r, "someone-else", "study_uid"),
        "study_uid_mismatch",
        "not_replayed",
    ),
    "no_questions": (
        lambda r: _without(r, "questions"),
        "questions_missing",
        "not_replayed",
    ),
    "questions_list": (
        lambda r: _with(r, [], "questions"),
        "questions_missing",
        "not_replayed",
    ),
    "no_status": (
        lambda r: _without(r, "study_status"),
        "study_status_missing",
        "partial",
    ),
    "odd_status": (
        lambda r: _with(r, "finished", "study_status"),
        "study_status_invalid",
        "partial",
    ),
    "missing_question": (
        lambda r: _without(r, "questions", "MCL"),
        "question_missing",
        "partial",
    ),
    "question_not_object": (
        lambda r: _with(r, "text", "questions", "MCL"),
        "question_entry_not_object",
        "partial",
    ),
    "no_objects": (
        lambda r: _without(r, "questions", "MCL", "objects"),
        "question_objects_missing",
        "partial",
    ),
    "objects_list": (
        lambda r: _with(r, [], "questions", "MCL", "objects"),
        "question_objects_invalid",
        "partial",
    ),
    "no_saved_finding": (
        lambda r: _without(r, "questions", "MCL", "finding"),
        "saved_finding_missing",
        "partial",
    ),
    "finding_text": (
        lambda r: _with(r, "open", "questions", "MCL", "finding"),
        "saved_finding_not_object",
        "partial",
    ),
    "saved_outcome_odd": (
        lambda r: _with(r, "maybe", "questions", "MCL", "finding", "outcome"),
        "saved_outcome_invalid",
        "partial",
    ),
    "saved_exact_huge": (
        lambda r: _with(
            r,
            {"numerator": "9" * 5000, "denominator": "1"},
            "questions",
            "MCL",
            "ranking",
            "exact",
        ),
        "saved_rank_invalid",
        "partial",
    ),
}


@pytest.mark.parametrize("name", sorted(MALFORMED_STUDIES))
def test_a_malformed_study_is_named_and_the_good_one_is_still_replayed(tmp_path, name):
    mutate, code, disposition = MALFORMED_STUDIES[name]
    run = _run(
        tmp_path,
        {"good": _study("good", _acl("present")), "bad": mutate(_study("bad"))},
    )
    report = replay.replay_run(run)

    assert code in _codes(report, study_uid="bad")
    by_uid = {s["study_uid"]: s for s in report["studies"]}
    assert by_uid["bad"]["disposition"] == disposition
    assert by_uid["bad"]["issue_codes"], "a malformed study is never silent"
    assert by_uid["good"]["disposition"] == "complete"
    assert _row_for(report, "good", "ACL")["current"]["outcome"] == "assigned"
    assert report["dataset"]["status"] == "partial"
    assert disposition == "not_replayed" or any(
        row["study_uid"] == "bad" for row in report["rows"]
    )


def _write_file(tmp_path: Path, data: bytes) -> Path:
    return _run(tmp_path, {"good": _study("good")}, raw={"bad": data})


@pytest.mark.parametrize(
    ("data", "code"),
    [
        (b"plain text, not compressed", "evidence_not_xz"),
        (_xz(b"\xff\xfe\x00"), "evidence_not_utf8"),
        (_xz(b'{"broken": '), "evidence_not_json"),
        (_xz(b"[1, 2, 3]"), "evidence_not_object"),
        (_xz(b'"a string"'), "evidence_not_object"),
        (_xz(b"null"), "evidence_not_object"),
    ],
    ids=["not_xz", "not_utf8", "not_json", "list", "string", "null"],
)
def test_an_undecodable_record_is_named_by_how_it_failed(tmp_path, data, code):
    report = replay.replay_run(_write_file(tmp_path, data))

    assert _codes(report, study_uid="bad") == [code]
    assert report["studies"][1]["disposition"] == "not_replayed"
    assert report["rows"] and {r["study_uid"] for r in report["rows"]} == {"good"}
    evidence = {item["study_uid"]: item for item in report["inputs"]["evidence"]}
    assert evidence["bad"]["sha256"] == hashlib.sha256(data).hexdigest()


def test_an_unreadable_record_and_an_escaping_path_are_named_and_not_followed(tmp_path):
    run = _run(tmp_path, {"good": _study("good")})
    (run / "studies" / "dir.json.xz").mkdir()
    outside = tmp_path / "outside.json.xz"
    outside.write_bytes(_xz(json.dumps(_study("elsewhere")).encode()))
    receipt = json.loads((run / "receipt.json").read_text())
    receipt["work"]["studies"] += [
        {"study_uid": "dir", "evidence_path": "studies/dir.json.xz"},
        {"study_uid": "elsewhere", "evidence_path": "../outside.json.xz"},
        {"study_uid": "none"},
    ]
    receipt["studies"] = len(receipt["work"]["studies"])
    (run / "receipt.json").write_text(json.dumps(receipt))
    report = replay.replay_run(run)

    assert _codes(report, study_uid="dir") == ["evidence_unreadable"]
    assert "receipt_evidence_path_outside_run" in _codes(report)
    assert "receipt_evidence_path_invalid" in _codes(report)
    # the file outside the run is never opened, so it is never replayed
    assert all(row["study_uid"] != "elsewhere" for row in report["rows"])
    assert [i["study_uid"] for i in report["inputs"]["evidence"]] == ["good", "dir"]


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (
            lambda r: r["work"]["studies"].append(
                {"study_uid": "good", "evidence_path": "x"}
            ),
            "receipt_study_uid_duplicate",
        ),
        (
            lambda r: r["work"]["studies"].append("not a row"),
            "receipt_study_row_invalid",
        ),
        (lambda r: r.update(studies=99), "receipt_study_count_mismatch"),
        (lambda r: r.update(work={}), "receipt_studies_missing"),
    ],
    ids=["duplicate_uid", "bad_row", "count", "no_studies"],
)
def test_a_receipt_that_does_not_account_for_its_studies_is_named(
    tmp_path, mutate, code
):
    run = _run(tmp_path, {"good": _study("good")})
    receipt = json.loads((run / "receipt.json").read_text())
    mutate(receipt)
    (run / "receipt.json").write_text(json.dumps(receipt))
    report = replay.replay_run(run)

    assert code in _codes(report)
    assert report["dataset"]["status"] == "partial"
    assert code in report["dataset"]["partial_because"]


@pytest.mark.parametrize(
    ("text", "code"),
    [("{not json", "receipt_not_json"), ("[1]", "receipt_not_object")],
)
def test_an_unusable_receipt_falls_back_to_the_directory_and_says_so(
    tmp_path, text, code
):
    run = _run(tmp_path, {"good": _study("good")})
    (run / "receipt.json").write_text(text)
    report = replay.replay_run(run)

    assert code in _codes(report)
    assert report["run"]["study_index"] == "directory_listing"
    assert report["dataset"]["status"] == "partial"
    assert [s["disposition"] for s in report["studies"]] == ["complete"]


def test_an_unknown_condition_is_named_without_making_a_complete_study_partial(
    tmp_path,
):
    record = _study("s1")
    record["questions"]["Knee Rumour"] = {"objects": {}}
    report = replay.replay_run(_run(tmp_path, {"s1": record}))

    assert _codes(report, study_uid="s1") == ["question_unknown"]
    assert report["studies"][0]["disposition"] == "complete"
    assert report["dataset"]["status"] == "complete"
    assert len(report["rows"]) == len(LABELS)  # the unknown one is not replayed


def test_a_directory_with_both_formats_keeps_the_compressed_one_and_says_so(tmp_path):
    run = _run(tmp_path, {"s1": _study("s1")}, receipt=False)
    (run / "studies" / "s1.json").write_text("{}", encoding="utf-8")
    report = replay.replay_run(run)

    assert "evidence_duplicate_format" in _codes(report)
    assert report["studies"][0]["disposition"] == "complete"
    assert report["inputs"]["evidence"][0]["path"] == "studies/s1.json.xz"


def test_evidence_the_receipt_does_not_list_is_reported_not_replayed(tmp_path):
    run = _run(tmp_path, {"listed": _study("listed")})
    dump_json_atomic(run / "studies" / "stray.json", _study("stray"))
    report = replay.replay_run(run)

    assert _codes(report) == ["unlisted_evidence_file"]
    assert [s["study_uid"] for s in report["studies"]] == ["listed"]
    assert report["dataset"]["status"] == "complete"  # the receipt defines the run


def test_a_run_with_nothing_to_replay_is_not_complete(tmp_path):
    run = _run(tmp_path, {})
    report = replay.replay_run(run)

    assert report["dataset"]["status"] == "partial"
    assert report["dataset"]["partial_because"] == {"no_studies_listed": 1}
    with pytest.raises(replay.ReplayError, match="run_studies_directory_missing"):
        replay.replay_run(tmp_path / "elsewhere")


def test_the_run_is_found_by_its_diagnostics_directory_too(tmp_path):
    run = _run(tmp_path, {"s1": _study("s1")})
    parent = tmp_path / "parent"
    parent.mkdir()
    run.rename(parent / "diagnostics")
    report = replay.replay_run(parent)

    assert report["run"]["path"] == str((parent / "diagnostics").resolve())
    assert report["dataset"]["status"] == "complete"


# ---------------------------------------------------------------------------
# a failure of the contracts is a named result, not a crash and not a silence
# ---------------------------------------------------------------------------


def test_a_contract_failure_is_named_per_condition_and_the_rest_replays(
    tmp_path, monkeypatch
):
    run = _run(tmp_path, {"s1": _study("s1", _acl("present"))})
    real = replay.combine_condition

    def failing(question, objects):
        if question == "MCL":
            raise ContractError("question_unknown", "forced")
        if question == "Synovitis":
            raise KeyError("boom")
        finding = real(question, objects)
        if question == "Fracture":
            finding["rank"] = {**finding["rank"], "value": float("nan")}
        return finding

    monkeypatch.setattr(replay, "combine_condition", failing)
    report = replay.replay_run(run)

    assert _codes(report, study_uid="s1") == [
        "combine_condition_refused:question_unknown",
        "combine_condition_raised:KeyError",
        "current_rank_invalid",
    ]
    states = {row["question"]: row["disposition"] for row in report["rows"]}
    assert states["MCL"] == states["Synovitis"] == states["Fracture"] == "not_replayed"
    assert sum(state == "replayed" for state in states.values()) == len(LABELS) - 3
    assert report["studies"][0]["disposition"] == "partial"
    # a failed replay is its own cell in the matrix, never a made-up outcome
    mcl = report["bins"]["partial_studies"]["per_condition"]["MCL"]["transitions"]
    assert mcl["open"]["unavailable"] == 1
    assert _row_for(report, "s1", "ACL")["current"]["outcome"] == "assigned"
    json.dumps(report, allow_nan=False)


# ---------------------------------------------------------------------------
# exact fractions, input hashes and the epoch
# ---------------------------------------------------------------------------


def test_fractions_stay_exact_far_beyond_float_range_and_json_safe(tmp_path):
    big = 10**400
    run = _run(tmp_path, {"s1": _study("s1", _acl("present", k=big, m=2 * big))})
    report = replay.replay_run(run)
    rank = _row_for(report, "s1", "ACL")["current"]["rank"]

    expected = (Fraction(7) + (1 + Fraction(1, 4)) / 2) / 9  # assigned tier, s+ = 1/4
    assert rank["exact"] == {
        "numerator": str(expected.numerator),
        "denominator": str(expected.denominator),
    }
    assert rank["s_plus"]["exact"] == {"numerator": "1", "denominator": "4"}
    assert type(rank["exact"]["numerator"]) is str
    assert 0.0 < rank["value"] < 1.0 and rank["value"] == float(expected)
    text = json.dumps(report, allow_nan=False, sort_keys=True)
    assert json.loads(text)["rows"][0]["question"] == "ACL"


def test_input_hashes_name_the_exact_bytes_read_and_nothing_is_modified(tmp_path):
    run = _run(tmp_path, {"s1": _study("s1"), "s2": _study("s2", _acl("present"))})
    files = sorted((run / "studies").iterdir()) + [run / "receipt.json"]
    before = {path: path.read_bytes() for path in files}
    report = replay.replay_run(run)

    evidence = {item["study_uid"]: item for item in report["inputs"]["evidence"]}
    for uid in ("s1", "s2"):
        data = before[run / "studies" / f"{uid}.json.xz"]
        assert evidence[uid]["sha256"] == hashlib.sha256(data).hexdigest()
        assert evidence[uid]["bytes"] == len(data)
        assert evidence[uid]["path"] == f"studies/{uid}.json.xz"
    receipt = report["inputs"]["receipt"]
    assert receipt["sha256"] == hashlib.sha256(before[run / "receipt.json"]).hexdigest()
    assert receipt["memory_manifest_sha256"] == "memory-sha"
    assert receipt["memory_revision"] == "memory-r1"
    assert report["saved_epoch"]["memory_revisions"] == {"memory-r1": 2}
    assert all(path.read_bytes() == data for path, data in before.items())
    # sign two: a different record is a different hash, and replaying is deterministic
    dump_json_atomic(run / "studies" / "s1.json", _study("s1", _acl("absent")))
    changed = replay.replay_run(run)
    assert changed["inputs"]["evidence"][0]["sha256"] != evidence["s1"]["sha256"]
    assert changed["inputs"]["evidence"][1] == report["inputs"]["evidence"][1]
    assert replay.replay_run(run) == changed


def test_the_epoch_names_the_current_source_that_replayed(tmp_path):
    epoch = replay.current_epoch()
    code = epoch["replayed_code"]

    path = Path(code["path"])
    assert path == Path(squint_contracts.__file__).resolve()
    assert code["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert code["policy_id"] == squint_contracts.POLICY_ID
    assert code["finding_schema"] == FINDING_SCHEMA
    assert code["contract_ids"]["ACL"] == "knee.squint-contract/acl/v1"
    assert code["entry_points"] == ["combine_condition", "rank_condition"]
    assert {"combine_condition", "rank_condition"} <= set(code["functions"])
    assert (
        epoch["script"]["sha256"]
        == hashlib.sha256(Path(replay.__file__).read_bytes()).hexdigest()
    )
    assert "decision_scope assignment" in epoch["not_rerun"]


def test_the_epoch_tells_which_function_changed(tmp_path, monkeypatch):
    """Sign one: a changed function body changes that function's digest and the file's.
    Sign two: the functions it did not touch keep theirs."""
    first = tmp_path / "contracts_a.py"
    second = tmp_path / "contracts_b.py"
    first.write_text("def stable():\n    return 1\n\n\ndef moved():\n    return 2\n")
    second.write_text("def stable():\n    return 1\n\n\ndef moved():\n    return 3\n")
    monkeypatch.setattr(squint_contracts, "__file__", str(first))
    before = replay.current_epoch()["replayed_code"]
    monkeypatch.setattr(squint_contracts, "__file__", str(second))
    after = replay.current_epoch()["replayed_code"]

    assert before["sha256"] != after["sha256"]
    assert before["functions"]["moved"] != after["functions"]["moved"]
    assert before["functions"]["stable"] == after["functions"]["stable"]
    assert set(before["functions"]) == {"stable", "moved"}
    monkeypatch.setattr(squint_contracts, "__file__", str(tmp_path / "gone.py"))
    gone = replay.current_epoch()["replayed_code"]
    assert gone["status"] == "source_unavailable" and gone["sha256"] is None


def test_no_score_threshold_or_readout_is_added_to_the_report(tmp_path):
    run, labels = _six_acl_studies(tmp_path, saved="open")
    report = replay.build_report(run, labels_path=labels)

    def keys(value):
        if isinstance(value, dict):
            for key, item in value.items():
                yield str(key)
                yield from keys(item)
        elif isinstance(value, list):
            for item in value:
                yield from keys(item)

    invented = {"auc", "threshold", "cutoff", "weight", "weights", "accuracy", "score"}
    assert not invented & {key.lower() for key in keys(report)}
    # every replayed value is the contract's own serialization, nothing else
    for row in report["rows"]:
        objects = _study(row["study_uid"], _acl("none"))["questions"][row["question"]]
        assert row["current"]["rank"]["value"] == float(
            Fraction(
                int(row["current"]["rank"]["exact"]["numerator"]),
                int(row["current"]["rank"]["exact"]["denominator"]),
            )
        )
        del objects


def test_the_replay_never_loads_the_recognition_stack():
    """No decode, location, recall or memory: those modules are not even imported."""
    code = (
        "import json, sys\n"
        "import scripts.replay_squint_findings\n"
        "print(json.dumps(sorted(sys.modules)))"
    )
    done = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO,
        env={**os.environ},
        capture_output=True,
        text=True,
        check=True,
    )
    loaded = set(json.loads(done.stdout))
    forbidden = (
        "numpy",
        "scipy",
        "skimage",
        "pydicom",
        "gdcm",
        "h5py",
        "knee.collapse",
        "knee.encoding",
        "knee.objects",
        "knee.compute",
        "knee.diagnosis.squint_locator",
        "knee.diagnosis.squint_pipeline",
        "knee.diagnosis.squint_memory",
        "knee.diagnosis.squint_profiles",
        "knee.diagnosis.squint_residual",
        "knee.diagnosis.squint_anchors",
        "knee.diagnosis.squint_anatomy_locator",
        "knee.study.series",
        "knee.study.slices",
        "knee.study.decoders",
        "knee.study.corpus",
    )
    assert {name for name in loaded if name.startswith(forbidden)} == set()
    assert "knee.diagnosis.squint_contracts" in loaded


# ---------------------------------------------------------------------------
# the command
# ---------------------------------------------------------------------------


def test_the_command_writes_a_fresh_json_and_markdown_report(tmp_path, capsys):
    run, labels = _six_acl_studies(tmp_path, saved="open")
    output = tmp_path / "out" / "replay.json"
    markdown = tmp_path / "out" / "replay.md"
    code = replay.main(
        [
            "--run",
            str(run),
            "--output",
            str(output),
            "--markdown",
            str(markdown),
            "--labels",
            str(labels),
        ]
    )

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        f"wrote {output}",
        f"wrote {markdown}",
    ]
    report = json.loads(output.read_text())
    assert report["schema"] == "knee.squint-replay/v1"
    assert report["evaluation"]["status"] == "evaluated"
    assert (
        report["inputs"]["labels"]["sha256"]
        == hashlib.sha256(labels.read_bytes()).hexdigest()
    )
    text = markdown.read_text()
    assert "Dataset: **complete**" in text
    # The six fixture studies contain two current assignments, two defeats and
    # two open outcomes; all six were saved as open.
    assert "open→assigned 2" in text and "open→defeated 2" in text
    assert "No combined score is reported." in text
    # an existing report is never overwritten, and a refusal is named on stderr
    assert replay.main(["--run", str(run), "--output", str(output)]) == 2
    assert "output_already_exists" in capsys.readouterr().err
    assert (
        replay.main(
            ["--run", str(run), "--output", str(output), "--markdown", str(output)]
        )
        == 2
    )
    assert "output_paths_must_be_distinct" in capsys.readouterr().err


def test_the_command_refuses_unusable_inputs_without_writing_a_report(tmp_path, capsys):
    run = _run(tmp_path, {"s1": _study("s1")})
    output = tmp_path / "replay.json"
    broken = tmp_path / "bad.csv"
    broken.write_text("nothing useful", encoding="utf-8")

    assert (
        replay.main(
            ["--run", str(run), "--output", str(output), "--labels", str(broken)]
        )
        == 2
    )
    assert "labels_columns_invalid" in capsys.readouterr().err
    assert not output.exists()
    missing = tmp_path / "no-run"
    assert replay.main(["--run", str(missing), "--output", str(output)]) == 2
    assert "run_studies_directory_missing" in capsys.readouterr().err
    assert not output.exists()


def test_require_complete_exits_nonzero_after_writing_a_partial_report(
    tmp_path, capsys
):
    partial = _run(tmp_path, {"s1": _study("s1")}, absent=("lost",))
    output = tmp_path / "replay.json"

    code = replay.main(
        ["--run", str(partial), "--output", str(output), "--require-complete"]
    )

    assert code == 1
    assert json.loads(output.read_text())["dataset"]["status"] == "partial"
    assert "dataset is partial" in capsys.readouterr().err
    whole = tmp_path / "whole"
    whole.mkdir()
    run = _run(whole, {"s1": _study("s1")})
    second = tmp_path / "second.json"
    assert (
        replay.main(["--run", str(run), "--output", str(second), "--require-complete"])
        == 0
    )
