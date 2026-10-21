"""Two-sign pins for the teaching round (scripts/squint_training_round.py).

Everything here is an invented fixture: small memories, one squint run with a
few located objects, and reader calls bound to invented report text. The
round's own admission is the existing ``admit_report_cases``; these tests pin
how the round joins it to observations, publication, readback and evaluation.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pytest

from knee.diagnosis.squint_configurations import configuration_profile
from knee.diagnosis.squint_interfaces import (
    TEACHING_ROUND_SCHEMA,
    TERRITORY_PROCEDURE,
    teaching_round_code,
)
from knee.diagnosis.squint_locator import prepare_recall, recall_source_fingerprint
from knee.diagnosis.squint_memory import SCHEMA, load_memory, save_memory
from knee.diagnosis.squint_pipeline import _study_excluded_memory
from knee.diagnosis.squint_reports import CALL_SCHEMA, CALLS_DOCUMENT_SCHEMA
from knee.diagnosis.submission import write_submission
from knee.json_store import dump_json_atomic, load_json
from knee.study.tables import LABELS, TRAIN_COLUMNS
from scripts.squint_training_round import (
    LOCATED_STATUSES,
    composite_finding,
    object_finding,
    parse_options,
    run_round,
)

PROCEDURE = "knee.squint-profile/scan-tercile-v1"
UID_A = "1.2.826.0.1.round.a"
UID_B = "1.2.826.0.1.round.b"
UID_OTHER = "1.2.826.0.1.round.other"
SENT_TEAR = "There is a full thickness ACL tear."
SENT_INTACT = "The ACL is intact."
SENT_FRACTURE = "A nondisplaced fracture of the lateral femoral condyle."
SENT_NO_FRACTURE = "No fracture is seen."
SENT_EQUIVOCAL = "The tibial spine may be irregular."
REPORTS = {
    UID_A: f"{SENT_TEAR} {SENT_FRACTURE} {SENT_NO_FRACTURE} {SENT_EQUIVOCAL}",
    UID_B: f"{SENT_TEAR}",
    UID_OTHER: f"{SENT_INTACT}",
}
BANK = 'squint/v1/view=["Sagittal","1","1"]/metric=signal_median/direction=overview/scale=10mm'


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree(path: Path) -> dict[str, str]:
    return {
        str(item.relative_to(path)): _sha(item)
        for item in sorted(path.rglob("*"))
        if item.is_file()
    }


def _profile(uid: str, subject: str, counts: list[int]) -> dict:
    return {
        "schema": "knee.squint-profile/v1",
        "subject": subject,
        "banks": {BANK: list(counts)},
        "source": {"study_uid": uid, "procedure": PROCEDURE},
    }


def _case(uid: str, subject: str, calls: dict, counts: list[int]) -> dict:
    return {
        "case_id": f"squint-case:{uid}:{subject}",
        "study_uid": uid,
        "subject": subject,
        "condition_calls": calls,
        "profile": _profile(uid, subject, counts),
        "regions": [],
        "full_profile": None,
        "full_source": {"status": "unavailable"},
        "teaching_source": {"kind": "official_train_csv_label"},
    }


def _parent(path: Path) -> Path:
    memory = {
        "schema": SCHEMA,
        "revision": "parent-r0",
        "questions": list(LABELS),
        "label_ledger": {UID_OTHER: {"ACL": 0}},
        "cases": [
            _case(UID_OTHER, "acl", {"ACL": -1}, [0, 3, 4]),
            _case(UID_B, "diagnosis/ACL", {"ACL": -1}, [1, 1, 1]),
        ],
    }
    save_memory(memory, path, prepared_recall=prepare_recall(memory))
    return path


def _train_csv(path: Path) -> Path:
    # The labels deliberately disagree with the reader's calls: a round never
    # reads them, so they can never become a case's call.
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(TRAIN_COLUMNS)
        for uid, report in REPORTS.items():
            writer.writerow((uid, report, *("0" for _ in LABELS)))
    return path


def _objects(uid: str, *, status: str = "proposal") -> dict[str, dict[str, Any]]:
    objects: dict[str, dict[str, Any]] = {
        subject: {
            "status": status,
            "profile": _profile(uid, subject, counts),
            "regions": [{"series_uid": f"{uid}.series", "window": [0, 1, 2, 4, 2, 4]}],
            "evidence": {"case_best_candidates": ["memory routed this"]},
        }
        for subject, counts in (
            ("acl", [4, 1, 0]),
            ("femur", [0, 2, 5]),
            ("tibia", [1, 4, 1]),
            ("pcl", [3, 0, 1]),
        )
    }
    objects["mcl"] = {"status": "unresolved_missing_reading", "profile": None}
    return objects


def _record(uid: str) -> dict:
    # Verdicts the memory itself reached; nothing here may teach.
    ranking = {"value": 0.9, "tier": "assigned"}
    return {
        "schema": "knee.squint-study/v1",
        "study_uid": uid,
        "memory_revision": "parent-r0",
        "study_status": "examined",
        "objects": _objects(uid),
        "questions": {
            question: {
                "finding": {"outcome": "assigned", "condition_calls": {question: 1}},
                "ranking": ranking,
                "objects": {},
            }
            for question in LABELS
        },
        "values": {question: 0.9 for question in LABELS},
        "capacity_exclusion": {"exclusion_status": "applied"},
    }


def _run(path: Path, parent_sha: str) -> Path:
    studies = []
    for uid in (UID_A, UID_B):
        evidence = dump_json_atomic(path / "studies" / f"{uid}.json", _record(uid))
        studies.append(
            {"study_uid": uid, "evidence_path": str(evidence.relative_to(path))}
        )
    receipt = {
        "schema": "knee.squint-run/v1",
        "action": "capacity",
        "source_mode": "raw_squint_case_recall",
        "memory_revision": "parent-r0",
        "memory_manifest_sha256": parent_sha,
        "work": {"studies": studies},
    }
    (path / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    return path


def _call(**override: object) -> dict:
    record: dict = {
        "schema": CALL_SCHEMA,
        "study_uid": UID_A,
        "question": "ACL",
        "digit": 1,
        "assertion": "present",
        "sentence": SENT_TEAR,
        "subject": "acl",
        "scope": "study_condition",
        "source": "report:train.csv",
        "report_sha": hashlib.sha256(REPORTS[UID_A].encode("utf-8")).hexdigest(),
        "reader": "independent-reader-1",
        "needs_review": False,
        "note": "",
    }
    record.update(override)
    if record["study_uid"] in REPORTS and "report_sha" not in override:
        report = REPORTS[record["study_uid"]]
        record["report_sha"] = hashlib.sha256(report.encode("utf-8")).hexdigest()
    return record


def _calls_file(path: Path, *calls: dict) -> Path:
    document = {"schema": CALLS_DOCUMENT_SCHEMA, "calls": list(calls)}
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


@pytest.fixture
def world(tmp_path: Path) -> dict:
    parent = _parent(tmp_path / "parent" / "memory")
    parent_sha = _sha(parent / "manifest.json")
    return {
        "tmp": tmp_path,
        "parent": parent,
        "parent_sha": parent_sha,
        "train": _train_csv(tmp_path / "train.csv"),
        "run": _run(tmp_path / "run", parent_sha),
    }


def _argv(world: dict, calls: Path, out: Path, *extra: str) -> list[str]:
    return [
        "--parent-memory",
        str(world["parent"]),
        "--expect-parent-sha256",
        world["parent_sha"],
        "--observations",
        str(world["run"]),
        "--reports",
        str(world["train"]),
        "--calls",
        str(calls),
        "--revision",
        "child-r1",
        "--out",
        str(out),
        *extra,
    ]


def _round(world: dict, calls: Path, out: Path, *extra: str, runner=None) -> dict:
    return run_round(
        parse_options(_argv(world, calls, out, *extra)), capacity_runner=runner
    )


def _on_disk(out: Path) -> dict:
    return json.loads((out / "round.json").read_text(encoding="utf-8"))


# --- teaching changes the child only through an independent call ---------------


def test_an_independent_call_teaches_the_child_and_the_parent_stays_intact(
    world: dict,
) -> None:
    calls = _calls_file(
        world["tmp"] / "calls.json",
        _call(),
        _call(
            question="Fracture",
            subject="femur",
            digit=-1,
            assertion="absent",
            sentence=SENT_NO_FRACTURE,
        ),
    )
    parent_before = _tree(world["parent"].parent)
    inputs_before = {name: _sha(world[name]) for name in ("train",)} | {
        "calls": _sha(calls),
        **_tree(world["run"]),
    }
    out = world["tmp"] / "round"

    manifest = _round(world, calls, out)

    assert manifest["status"] == "published"
    assert manifest["schema"] == TEACHING_ROUND_SCHEMA
    assert teaching_round_code(manifest) == "valid"
    assert _on_disk(out) == manifest
    assert manifest["parent"]["manifest_sha256"] == world["parent_sha"]
    assert manifest["calls"][0]["sha256"] == _sha(calls)
    assert manifest["admission"]["added_case_count"] == 2
    child = load_memory(out / "memory")
    parent = load_memory(world["parent"])
    assert child["revision"] == "child-r1" != parent["revision"]
    assert child["parent_revision"] == "parent-r0"
    new = {
        case["subject"]: case for case in child["cases"] if case["study_uid"] == UID_A
    }
    assert len(child["cases"]) == len(parent["cases"]) + 2
    assert set(new) == {"acl", "femur"}
    # Independent +1 and -1 calls teach; train.csv's labels never do.
    assert new["acl"]["condition_calls"] == {"ACL": 1}
    assert new["femur"]["condition_calls"] == {"Fracture": -1}
    assert all(
        case["teaching"]["kind"] == "independent_report_calls" for case in new.values()
    )
    assert child["label_ledger"] == parent["label_ledger"]
    assert child["teaching_rounds"][-1]["use"] == "teaching"
    assert child["teaching_rounds"][-1]["parent_manifest_sha256"] == world["parent_sha"]
    # The parent and every consumed input are byte for byte as they were.
    assert _tree(world["parent"].parent) == parent_before
    assert {name: _sha(world[name]) for name in ("train",)} | {
        "calls": _sha(calls),
        **_tree(world["run"]),
    } == inputs_before
    # The next run reads the child and its preparation through the normal route.
    cache = load_json(out / "memory" / "recall-preparation.json")
    assert cache["memory_manifest_sha256"] == manifest["child"]["manifest_sha256"]
    assert prepare_recall(child, cached=cache)["runtime_indexes_rebuilt"] is True
    assert manifest["child"]["recall_preparation_source"] == "computed"


def test_inference_verdicts_alone_never_change_the_child(world: dict) -> None:
    # The record says "assigned" with call-shaped fields everywhere. The located
    # acl is offered to admission under an independent abstention, and the only
    # signed "call" is the memory's own answer under a recall source.
    routed = _call(source="recall:held-out-memory", reader="squint-recall")
    abstention = _call(digit=0, assertion="uncertain", sentence=SENT_EQUIVOCAL)
    calls = _calls_file(world["tmp"] / "calls.json", routed, abstention)
    out = world["tmp"] / "round"

    manifest = _round(world, calls, out)

    assert manifest["status"] == "published"
    assert manifest["admission"]["findings_offered"] == 1
    assert manifest["admission"]["added_case_count"] == 0
    assert manifest["admission"]["rejected_by_reason"] == {"visual_memory_source": 1}
    assert manifest["admission"]["skipped_findings_by_code"] == {"no_signed_call": 1}
    child = load_memory(out / "memory")
    parent = load_memory(world["parent"])
    assert [case["case_id"] for case in child["cases"]] == [
        case["case_id"] for case in parent["cases"]
    ]
    # Unchanged recall inputs reuse the parent's exact preparation.
    assert manifest["child"]["recall_preparation_source"] == "parent_preparation_reused"


def test_no_calls_teach_nothing_however_confident_the_record(world: dict) -> None:
    calls = world["tmp"] / "calls.json"
    calls.write_text("[]", encoding="utf-8")
    manifest = _round(world, calls, world["tmp"] / "round")
    assert manifest["status"] == "published"
    assert manifest["admission"]["added_case_count"] == 0
    assert manifest["admission"]["findings_offered"] == 0


# --- existing admission outcomes are kept by name ------------------------------


def test_duplicate_conflicting_malformed_and_unsupported_calls_keep_their_outcomes(
    world: dict,
) -> None:
    malformed = _call(question="MCL", subject="mcl", digit="1")
    missing = _call(question="Fracture", subject="femur")
    del missing["reader"]
    with_prediction = _call(question="Fracture", subject="tibia")
    with_prediction["prediction"] = 1
    calls = _calls_file(
        world["tmp"] / "calls.json",
        _call(),
        _call(),
        _call(question="Fracture", subject="femur", sentence=SENT_FRACTURE),
        _call(
            question="Fracture",
            subject="femur",
            digit=-1,
            assertion="absent",
            sentence=SENT_NO_FRACTURE,
        ),
        _call(question="ACL", subject="tibia", needs_review=True),
        _call(
            question="ACL",
            subject="pcl",
            digit=0,
            assertion="uncertain",
            sentence=SENT_EQUIVOCAL,
        ),
        malformed,
        missing,
        with_prediction,
        _call(question="ACL", subject="tibia", scope="lesion"),
        _call(question="ACL", subject="medial_meniscus"),
    )
    out = world["tmp"] / "round"

    manifest = _round(world, calls, out)

    admission = manifest["admission"]
    assert manifest["status"] == "published"
    assert admission["added_case_count"] == 1
    assert [row["subject"] for row in admission["admitted"]] == ["acl"]
    assert admission["duplicates"] == 1
    assert admission["contradictory"] == 2
    assert admission["needs_review"] == 1
    assert admission["abstentions"] == 1
    assert admission["rejected_by_reason"] == {
        "invalid_digit": 1,
        "missing_field": 1,
        "predicted_label_teacher": 1,
        "scope_not_study_condition": 1,
        "subject_not_implicated": 1,
    }
    assert admission["skipped_findings_by_code"]["calls_contradictory"] == 1


def test_official_labels_are_not_calls_for_the_existing_admission(world: dict) -> None:
    """Why the round does not teach train.csv labels.

    The existing admission binds a call to its report: a report source and a
    sentence quoted from that report. A label is a cell of train.csv, with no
    sentence; both honest ways of writing it as a call are refused by name.
    """
    as_label = _call(source="label:train.csv", sentence="", reader="train-csv")
    as_report = _call(source="report:train.csv", sentence="", reader="train-csv")
    calls = _calls_file(world["tmp"] / "calls.json", as_label, as_report)

    manifest = _round(world, calls, world["tmp"] / "round")

    assert manifest["admission"]["added_case_count"] == 0
    assert manifest["admission"]["rejected_by_reason"] == {
        "sentence_required": 1,
        "source_not_report": 1,
    }


# --- publication failure, resume and parents -----------------------------------


def test_a_publication_failure_leaves_parent_and_inputs_intact_then_resumes(
    world: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    import knee.diagnosis.squint_locator as locator

    calls = _calls_file(world["tmp"] / "calls.json", _call())
    out = world["tmp"] / "round"
    parent_before = _tree(world["parent"].parent)
    inputs_before = (_sha(calls), _sha(world["train"]), _tree(world["run"]))

    def fail(*_args: object, **_kwargs: object) -> dict:
        raise ValueError("injected_publication_failure")

    monkeypatch.setattr(locator, "persisted_recall_cache", fail)
    failed = _round(world, calls, out)

    assert failed["status"] == "incomplete"
    assert failed["failure"] == {"code": "child_publication_failed:ValueError"}
    assert teaching_round_code(failed) == "valid"
    assert _on_disk(out)["status"] == "incomplete"
    assert not (out / "memory").exists()
    assert sorted(item.name for item in out.iterdir()) == [
        "round-inputs.json",
        "round.json",
    ]
    assert _tree(world["parent"].parent) == parent_before
    assert (_sha(calls), _sha(world["train"]), _tree(world["run"])) == inputs_before

    monkeypatch.undo()
    resumed = _round(world, calls, out)

    assert resumed["status"] == "published"
    assert resumed["resumed"] is True
    assert resumed["child"]["publication"] == "published_now"
    assert load_memory(out / "memory")["revision"] == "child-r1"
    assert _tree(world["parent"].parent) == parent_before


def test_a_resumed_round_reuses_its_child_and_refuses_changed_inputs(
    world: dict,
) -> None:
    calls = _calls_file(world["tmp"] / "calls.json", _call())
    out = world["tmp"] / "round"
    first = _round(world, calls, out)
    child_bytes = _sha(out / "memory" / "manifest.json")

    again = _round(world, calls, out)

    assert again["status"] == "published" and again["resumed"] is True
    assert again["child"]["publication"] == "resumed_existing"
    assert again["child"]["manifest_sha256"] == first["child"]["manifest_sha256"]
    assert _sha(out / "memory" / "manifest.json") == child_bytes
    kept = (out / "round.json").read_bytes()

    _calls_file(calls, _call(), _call(question="Fracture", subject="femur"))
    changed = _round(world, calls, out)

    assert changed["status"] == "refused"
    assert changed["failure"] == {"code": "round_root_inputs_mismatch"}
    assert (out / "round.json").read_bytes() == kept
    assert _sha(out / "memory" / "manifest.json") == child_bytes


def test_a_parent_from_an_unfinished_or_test_round_is_refused(world: dict) -> None:
    calls = _calls_file(world["tmp"] / "calls.json", _call())
    taught = world["tmp"] / "taught"
    assert _round(world, calls, taught)["status"] == "published"

    # A completed teaching round's child is a parent; the next run reads it and
    # reuses its preparation when nothing new is admitted.
    none = world["tmp"] / "none.json"
    none.write_text("[]", encoding="utf-8")
    argv = _argv(world, none, world["tmp"] / "second")
    argv[argv.index("--parent-memory") + 1] = str(taught / "memory")
    argv[argv.index("--expect-parent-sha256") + 1] = _sha(
        taught / "memory" / "manifest.json"
    )
    argv[argv.index("--revision") + 1] = "child-r2"
    second = run_round(parse_options(argv))
    assert second["status"] == "published"
    assert second["parent"]["round"]["status"] == "round_child"
    assert second["child"]["recall_preparation_source"] == "parent_preparation_reused"

    test_round = world["tmp"] / "loop"
    assert (
        _round(world, calls, test_round, "--use", "mechanical_loop_test")["status"]
        == "published"
    )
    argv[argv.index("--parent-memory") + 1] = str(test_round / "memory")
    argv[argv.index("--expect-parent-sha256") + 1] = _sha(
        test_round / "memory" / "manifest.json"
    )
    argv[argv.index("--out") + 1] = str(world["tmp"] / "after-loop")
    refused = run_round(parse_options(argv))
    assert refused["failure"] == {"code": "parent_marked_not_for_use"}
    assert not (world["tmp"] / "after-loop").exists()

    unfinished = _on_disk(taught)
    unfinished["status"] = "incomplete"
    (taught / "round.json").write_text(json.dumps(unfinished), encoding="utf-8")
    argv[argv.index("--parent-memory") + 1] = str(taught / "memory")
    argv[argv.index("--expect-parent-sha256") + 1] = _sha(
        taught / "memory" / "manifest.json"
    )
    assert run_round(parse_options(argv))["failure"] == {
        "code": "parent_publication_incomplete"
    }


def test_a_changed_parent_is_refused_before_anything_is_written(world: dict) -> None:
    calls = _calls_file(world["tmp"] / "calls.json", _call())
    argv = _argv(world, calls, world["tmp"] / "round")
    argv[argv.index("--expect-parent-sha256") + 1] = "0" * 64
    refused = run_round(parse_options(argv))
    assert refused["status"] == "refused"
    assert refused["failure"] == {"code": "parent_manifest_sha256_mismatch"}
    assert teaching_round_code(refused) == "valid"
    assert not (world["tmp"] / "round").exists()


def test_a_child_that_is_not_this_rounds_publication_stops_the_round(
    world: dict,
) -> None:
    calls = _calls_file(world["tmp"] / "calls.json", _call())
    out = world["tmp"] / "round"
    assert _round(world, calls, out)["status"] == "published"
    # Replace the published child with another valid memory: the parent itself.
    for name in ("manifest.json", "recall-preparation.json.xz"):
        (out / "memory" / name).write_bytes((world["parent"] / name).read_bytes())
    seen: list = []

    stopped = _round(
        world, calls, out, *_evaluation_args(world), runner=_capacity(seen)
    )

    assert stopped["status"] == "incomplete"
    assert stopped["failure"] == {"code": "child_publication_mismatch:revision"}
    assert _on_disk(out)["status"] == "incomplete"
    assert seen == []


@pytest.mark.parametrize("where", ["holding_parent", "inside_parent"])
def test_a_round_root_overlapping_the_parent_is_refused(world: dict, where) -> None:
    calls = _calls_file(world["tmp"] / "calls.json", _call())
    before = _tree(world["parent"].parent)
    out = world["parent"].parent if where == "holding_parent" else world["parent"] / "x"
    refused = _round(world, calls, out)
    assert refused["failure"] == {"code": "round_root_overlaps_parent"}
    assert _tree(world["parent"].parent) == before


# --- question composites --------------------------------------------------------


def test_a_composite_call_teaches_the_configuration_the_inference_recalled(
    world: dict,
) -> None:
    composite = _call(subject="diagnosis/ACL")
    taught_before = _call(subject="diagnosis/ACL", study_uid=UID_B)
    calls = _calls_file(world["tmp"] / "calls.json", composite, taught_before)
    out = world["tmp"] / "round"

    manifest = _round(world, calls, out)

    child = load_memory(out / "memory")
    new = [case for case in child["cases"] if case["study_uid"] == UID_A]
    objects = _objects(UID_A)
    expected = configuration_profile(
        {name: objects[name]["profile"] for name in ("acl", "femur", "tibia", "pcl")},
        "ACL",
    )
    assert len(new) == 1 and new[0]["subject"] == "diagnosis/ACL"
    assert new[0]["profile"] == expected
    assert new[0]["condition_calls"] == {"ACL": 1}
    assert {region["subject"] for region in new[0]["regions"]} == {
        "acl",
        "femur",
        "tibia",
        "pcl",
    }
    # Study B already holds a diagnosis/ACL case for ACL: the existing guard holds it.
    assert manifest["admission"]["held_calls_by_code"] == {
        "already_in_memory_question": 1
    }
    assert not [case for case in child["cases"][2:] if case["study_uid"] == UID_B]


def test_findings_are_read_only_from_located_objects() -> None:
    objects = _objects(UID_A)
    finding, code = composite_finding(objects, UID_A, "diagnosis/ACL", LOCATED_STATUSES)
    assert code == "composite_finding" and finding is not None
    assert finding["status"] == "proposal"

    located = _objects(UID_A, status="located")
    located_finding, code = composite_finding(
        located, UID_A, "diagnosis/ACL", LOCATED_STATUSES
    )
    assert code == "composite_finding" and located_finding is not None
    assert located_finding["status"] == "located"

    unlocated = _objects(UID_A)
    unlocated["pcl"]["status"] = "unresolved_candidate_tie"
    assert composite_finding(unlocated, UID_A, "diagnosis/ACL", LOCATED_STATUSES) == (
        None,
        "composite_role_not_located",
    )
    assert composite_finding({}, UID_A, "diagnosis/ACL", LOCATED_STATUSES) == (
        None,
        "composite_silent",
    )
    assert composite_finding(objects, UID_A, "diagnosis/Nope", LOCATED_STATUSES) == (
        None,
        "composite_question_unknown",
    )

    # One configuration reads one writer, as the inference composes it.
    territory = _objects(UID_A)
    for item in territory.values():
        if item["profile"] is not None:
            item["profile"]["source"]["procedure"] = TERRITORY_PROCEDURE
    composed, code = composite_finding(
        territory, UID_A, "diagnosis/ACL", LOCATED_STATUSES
    )
    assert code == "composite_finding" and composed is not None
    assert composed["profile"]["source"]["procedure"] == TERRITORY_PROCEDURE
    territory["pcl"]["profile"]["source"]["procedure"] = PROCEDURE
    assert composite_finding(territory, UID_A, "diagnosis/ACL", LOCATED_STATUSES) == (
        None,
        "composite_mixed_procedures",
    )

    assert (
        object_finding(objects, UID_A, "acl", LOCATED_STATUSES)[1] == "object_finding"
    )
    assert object_finding(objects, UID_A, "mcl", LOCATED_STATUSES) == (
        None,
        "object_not_located",
    )
    objects["acl"]["profile"]["source"]["calibration"] = math.nan
    assert object_finding(objects, UID_A, "acl", LOCATED_STATUSES) == (
        None,
        "object_reading_not_finite_json",
    )


# --- held-out evaluation --------------------------------------------------------


def _capacity(seen: list, *, fingerprint: str | None = None):
    """A stand-in for the production capacity route, with its own population."""

    def runner(namespace, *, prepared_memory_snapshot):
        seen.append(namespace)
        snapshot = prepared_memory_snapshot
        memory = snapshot.memory
        run = Path(namespace.diagnostic_output)
        run.mkdir(parents=True)
        studies, rows = [], []
        for uid in namespace.study_uid:
            view, excluded = _study_excluded_memory(memory, uid)
            consumed = fingerprint or recall_source_fingerprint(view)
            exclusion = {
                **excluded,
                "exclusion_status": "applied",
                "consumed_case_fingerprint": consumed,
                "consumed_fingerprint_scope": "source_cases_calls_profiles_and_censors_v1",
                "preparation_schema": "knee.squint-recall-preparation/v1",
                "preparation_outcome": "prepared",
                "prepared_population_identity": {
                    "status": "prepared",
                    "source_fingerprint": consumed,
                    "source": {},
                    "memory_manifest_sha256": snapshot.sha256,
                    "case_profile_count": len(view["cases"]),
                },
            }
            ranking = {
                "value": 0.5,
                "tier": "open",
                "exact": {"numerator": "1", "denominator": "2"},
            }
            record = {
                "schema": "knee.squint-study/v1",
                "study_uid": uid,
                "memory_revision": memory["revision"],
                "study_status": "examined",
                "capacity_exclusion": exclusion,
                "work": {"source_mode": "raw_squint_case_recall"},
                "values": {question: 0.5 for question in LABELS},
                "questions": {
                    question: {"finding": {"outcome": "open"}, "ranking": ranking}
                    for question in LABELS
                },
                "objects": {},
            }
            evidence = dump_json_atomic(run / "studies" / f"{uid}.json", record)
            studies.append(
                {
                    "study_uid": uid,
                    "evidence_path": str(evidence.relative_to(run)),
                    "capacity_exclusion": exclusion,
                }
            )
            rows.append((uid, record["values"]))
        submission = write_submission(
            Path(namespace.diagnostic_submission_template),
            run / "submission.csv",
            rows,
            source_provenance={
                "source_mode": "raw_squint_case_recall",
                "memory_revision": memory["revision"],
                "memory_manifest_sha256": snapshot.sha256,
            },
        )
        receipt = {
            "schema": "knee.squint-run/v1",
            "action": "capacity",
            "source_mode": "raw_squint_case_recall",
            "studies": len(studies),
            "memory_revision": memory["revision"],
            "memory_manifest_sha256": snapshot.sha256,
            "recall_preparation": {
                "path": None,
                "sha256": None,
                "bytes": 0,
                "cache_status": "study_excluded_per_study",
            },
            "submission": submission,
            "work": {"studies": studies},
        }
        (run / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
        return receipt

    return runner


def _evaluation_args(world: dict) -> tuple[str, ...]:
    return (
        "--evaluate",
        "--root",
        str(world["tmp"] / "raw"),
        "--labels",
        str(world["train"]),
        "--evaluate-study-uid",
        UID_A,
        "--evaluate-study-uid",
        UID_OTHER,
        "--workers",
        "1",
    )


def test_evaluation_checks_each_study_against_the_one_memory_view(
    world: dict,
) -> None:
    calls = _calls_file(
        world["tmp"] / "calls.json",
        _call(),
        _call(
            question="Fracture",
            subject="femur",
            digit=-1,
            assertion="absent",
            sentence=SENT_NO_FRACTURE,
        ),
    )
    out = world["tmp"] / "round"
    seen: list = []

    manifest = _round(
        world, calls, out, *_evaluation_args(world), runner=_capacity(seen)
    )

    evaluation = manifest["evaluation"]
    assert (
        manifest["status"] == "evaluated" and teaching_round_code(manifest) == "valid"
    )
    assert evaluation["status"] == "evaluated"
    assert evaluation["exclusion"]["agree"] is True
    rows = evaluation["exclusion"]["studies"]
    assert rows[UID_A]["excluded_case_count"] == 2
    assert rows[UID_A]["excluded_cases_reachable"] == 0
    assert evaluation["per_condition"]["ACL"]["negative"]["abstained"] == 2
    assert evaluation["trajectory"]["previous"]["status"] == "unavailable"
    assert len(evaluation["trajectory"]["points"]) == 1
    assert len(seen) == 1 and seen[0].diagnostic_mode == "capacity"
    assert Path(seen[0].diagnostic_memory) == (out / "memory").resolve()

    # A completed evaluation is kept and reused, never rerun.
    again = _round(world, calls, out, *_evaluation_args(world), runner=_capacity(seen))
    assert again["status"] == "evaluated" and again["evaluation"]["resumed"] is True
    assert len(seen) == 1


def test_an_evaluation_whose_population_differs_from_the_view_is_not_accepted(
    world: dict,
) -> None:
    calls = _calls_file(world["tmp"] / "calls.json", _call())
    out = world["tmp"] / "round"
    runner = _capacity([], fingerprint="f" * 64)

    manifest = _round(world, calls, out, *_evaluation_args(world), runner=runner)

    assert manifest["evaluation"]["status"] == "exclusion_mismatch"
    assert manifest["evaluation"]["exclusion"]["agree"] is False
    assert manifest["status"] == "published"
    assert teaching_round_code(manifest) == "valid"
