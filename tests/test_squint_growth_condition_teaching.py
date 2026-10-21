"""Two-sign intent of condition teaching and held-out studies in a growth round.

CLASSICAL_AI_BUILD_DESIGN §§5.1, 7 and 8. When a round admits a recognition-
derived object case, its study's official labels are carried onto it through
``carry_condition_calls``: a positive for a condition implicating the object is a
presentation in every view where the admission's identity holds, its normal
labels speak through those views alike, a blank label makes no call, and a
Fracture or Contusion positive stays unlocalized. The calls keep train.csv as
their source, apart from the recognition-derived identity lineage, and labels
never reach a decision. A held-out study is never scored or admitted, its labels
are never read, and every child keeps its parent's held-out studies. Each test
pins one meaning in both signs, through the growth API, the published child and
the production condition consumer: ``prepare_recall``/``recall_object`` as the
squint pipeline calls them, ``memory_view`` and ``combine_condition``.
"""

from __future__ import annotations

import copy
import csv
import json
from pathlib import Path

import pytest

from knee.diagnosis.squint_contracts import combine_condition
from knee.diagnosis.squint_identity import SANITY_SCHEMA, TEACHING_SCHEMA
from knee.diagnosis.squint_identity_growth import (
    CHILD_DIRECTORY,
    CONDITION_TEACHING_SCHEMA,
    DECISIONS_FILE,
    HELD_OUT_SCHEMA,
    LABEL_SOURCE,
    RECOGNITION_KIND,
    IdentityGrowthError,
    grow_identity_memory,
    harvest_candidates,
    held_out_record,
    inherited_held_out,
)
from knee.diagnosis.squint_interfaces import TERRITORY_PROCEDURE, territory_bank_name
from knee.diagnosis.squint_locator import prepare_recall, recall_object
from knee.diagnosis.squint_memory import (
    CONDITION_CARRY_SCHEMA,
    LOCALIZED_PRESENTATION_SCOPE,
    SCHEMA,
    _condition_calls,
    _json_sha256,
    carry_condition_calls,
    load_memory_snapshot,
    save_memory,
)
from knee.diagnosis.squint_memory_view import memory_view
from knee.diagnosis.squint_questions import question_selection
from knee.study.tables import LABELS

SAG = ["Sagittal", "0", "0"]
COR = ["Coronal", "0", "0"]
WINDOW = [0, 1, 0, 2, 0, 2]
REVISION = "inference-memory-r1"


def view_bank(view: list[str]) -> str:
    """A canonical cheap territory bank: identity recall and the condition
    selections of Fracture, ACL and Medial OA all read it for the femur."""
    return territory_bank_name(
        dict(
            zip(
                ("orientation", "fluid_sensitive", "fat_suppression"), view, strict=True
            )
        ),
        "object",
        "signal_median",
        "overview",
        10.0,
    )


SAG_BANK, COR_BANK = view_bank(SAG), view_bank(COR)
QUERY_SAG = {SAG_BANK: (3, 0, 0)}
QUERY_COR = {COR_BANK: (0, 0, 3)}
# The candidate reads in both views; only its sagittal reading resembles a femur
# seed, so recognition admits it on the sagittal view alone.
CANDIDATE_BANKS = {**QUERY_SAG, **QUERY_COR}
# Two labelled normal femurs, one per view, so each view has opposing cases.
NORMAL = {"Fracture": 0, "ACL": 0, "Medial OA": 1}
# The candidate study's row: two positives, one normal, every other label blank.
STUDY_X = {"Fracture": 1, "ACL": 1, "Medial OA": 0}


def profile(subject: str, banks) -> dict:
    return {
        "schema": "knee.squint-profile/v1",
        "subject": subject,
        "banks": {name: list(counts) for name, counts in banks.items()},
        "source": {"procedure": TERRITORY_PROCEDURE},
    }


def label_row(values: dict) -> dict:
    row = dict.fromkeys(LABELS)
    row.update(values)
    return row


def object_case(subject: str, study: str, banks, labels: dict | None = None) -> dict:
    """An object case as the compiler writes one: calls from ``_condition_calls``."""
    case = {
        "case_id": f"squint-case:{study}:{subject}",
        "study_uid": study,
        "subject": subject,
        "condition_calls": {},
        "profile": profile(subject, banks),
        "regions": [],
    }
    if labels is not None:
        calls, scopes = _condition_calls(subject, label_row(labels))
        case.update(condition_calls=calls, presentation_scope=scopes)
    return case


def parent_memory() -> dict:
    """Femur and patella identity seeds, and two labelled normal femurs, all confirmed."""
    cases = [
        object_case("femur", "study-s", {SAG_BANK: (3, 0, 0)}),
        object_case("patella", "study-p", {SAG_BANK: (0, 0, 3)}),
        object_case("femur", "study-b", {SAG_BANK: (1, 2, 0)}, NORMAL),
        object_case("femur", "study-c", {COR_BANK: (1, 2, 0)}, NORMAL),
    ]
    return {
        "schema": SCHEMA,
        "revision": "teaching-parent-r1",
        "questions": list(LABELS),
        "cases": cases,
        "object_identity_teaching": {
            "schema": TEACHING_SCHEMA,
            "reader": "fixture reviewer",
            "confirmed_case_ids": [case["case_id"] for case in cases],
            "calls": [
                {
                    "candidate_id": case["case_id"],
                    "call": "confirm",
                    "notes": "n",
                    "reader": "fixture reviewer",
                }
                for case in cases
            ],
        },
    }


def sanity(subject: str, status: str, result: str) -> dict:
    """A knee.object-anatomical-sanity/v1 record shaped as the locator writes it."""
    check = {
        "rule_id": f"authored:{subject}:superior_to:tibia",
        "source": "docs/OBJECTS_AND_CONDITIONS.md §4",
        "subject": subject,
        "target": "tibia",
        "candidate_role": "subject",
        "axis": "z",
        "relation": "superior_to",
        "expected_relation": "strictly_after",
        "candidate_interval": [40.0, 80.0],
        "target_interval": [0.0, 30.0],
        "result": result,
        "candidate_subject": subject,
        "reference_subject": "tibia",
    }
    return {
        "schema": SANITY_SCHEMA,
        "status": status,
        "identity_assertion": None,
        "windows": [
            {
                "index": 0,
                "window": list(WINDOW),
                "address": list(WINDOW),
                "status": status,
                "eligible": True,
                "checks": [check],
                "series_uid": "series-sag",
            }
        ],
    }


def record(uid: str, banks=CANDIDATE_BANKS, *, anatomy: str = "plausible") -> dict:
    """A knee.squint-study/v1 record with one located femur, abridged."""
    result = "supported_strictly_after" if anatomy == "plausible" else "unknown"
    return {
        "schema": "knee.squint-study/v1",
        "study_uid": uid,
        "memory_revision": REVISION,
        "study_status": "examined",
        "objects": {
            "femur": {
                "status": "proposal",
                "profile": profile("femur", banks),
                "regions": [{"series_uid": "series-sag", "window": list(WINDOW)}],
                "sanity": sanity("femur", anatomy, result),
                "evidence": {"source": "fixture"},
            }
        },
        "identity_recall": {"outcome": "examined", "objects": {}},
        "questions": {},
        "values": {},
    }


def located_id(uid: str) -> str:
    return f"located:{uid}:femur:{REVISION}"


X = located_id("study-x")


def write_labels(path: Path, rows: dict) -> Path:
    """A train.csv with the competition's header; each Report holds a comma and
    a line break, as real reports do."""
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["StudyInstanceUID", "Report", *LABELS])
        for uid, values in rows.items():
            writer.writerow(
                [
                    uid,
                    "Findings: joint fluid,\nno other finding.",
                    *(
                        "" if values.get(question) is None else str(values[question])
                        for question in LABELS
                    ),
                ]
            )
    return path


@pytest.fixture
def parent(tmp_path: Path):
    save_memory(parent_memory(), tmp_path / "parent")
    return load_memory_snapshot(tmp_path / "parent")


def grow(tmp_path: Path, name: str, parent, records, **options) -> dict:
    return grow_identity_memory(
        parent, harvest_candidates(records), tmp_path / name, **options
    )


def child_of(tmp_path: Path, name: str) -> dict:
    return load_memory_snapshot(tmp_path / name / CHILD_DIRECTORY).memory


def case_of(memory: dict, case_id: str) -> dict:
    [case] = [case for case in memory["cases"] if case["case_id"] == case_id]
    return case


def call_of(memory: dict, case_id: str) -> dict:
    calls = memory["object_identity_teaching"]["calls"]
    [call] = [row for row in calls if row["candidate_id"] == case_id]
    return call


def decisions_of(tmp_path: Path, name: str) -> dict:
    return json.loads((tmp_path / name / DECISIONS_FILE).read_text())


def taught(tmp_path: Path, parent, name: str = "grown", rows: dict | None = None):
    """One round admitting study-x's femur with study-x's labels."""
    labels = write_labels(
        tmp_path / f"{name}-train.csv", {"study-x": STUDY_X} if rows is None else rows
    )
    receipt = grow(tmp_path, name, parent, [record("study-x")], labels=labels)
    return receipt, child_of(tmp_path, name), labels


def condition_recall(memory: dict, banks, question: str) -> dict:
    """``recall_object`` as the squint pipeline calls it: a prepared memory and the
    question's own selection."""
    if "prepared_recall" not in memory:
        memory = {**memory, "prepared_recall": prepare_recall(memory)}
    selected = {**memory, "recall_selection": question_selection(question)}
    return recall_object(profile("femur", banks), selected, question=question)


def term_of(result: dict, case_id: str) -> dict:
    [row] = [row for row in result["case_terms"] if row["case_id"] == case_id]
    return row


# ------------------------------------------------------- the carry on admission


def test_an_admission_carries_its_studys_labels_through_its_admission_views(
    tmp_path: Path, parent
):
    receipt, child, labels = taught(tmp_path, parent)
    [decision] = decisions_of(tmp_path, "grown")["decisions"]
    assert (decision["state"], decision["views"]) == ("admitted", [SAG])
    case = case_of(child, X)
    row = label_row(STUDY_X)
    # Exactly the existing carry, on the admission's own confirm call.
    carry = carry_condition_calls(case, call_of(child, X), row)
    assert carry["schema"] == CONDITION_CARRY_SCHEMA
    assert case["condition_teaching"] == {
        "schema": CONDITION_TEACHING_SCHEMA,
        "status": "carried",
        "labels": {
            "source": LABEL_SOURCE,
            "source_path": str(labels.resolve()),
            "source_sha256": receipt["condition_teaching"]["labels"]["source_sha256"],
            "study_uid": "study-x",
        },
        "carry": carry,
    }
    assert case["condition_calls"] == {"Fracture": 1, "ACL": 1, "Medial OA": -1}
    assert case["condition_calls"] == _condition_calls("femur", row)[0]
    assert case["presentation_scope"] == {
        "Fracture": "positive_condition_presentation",
        "ACL": "positive_condition_presentation",
        "Medial OA": "condition_negative_with_other_positive_presentation",
    }
    # The candidate also reads coronally; its calls speak only where its identity holds.
    assert set(case["profile"]["banks"]) == {SAG_BANK, COR_BANK}
    assert (carry["identity_scope"], carry["identity_views"]) == (
        "confirmed_views",
        [SAG],
    )
    assert carry["speaks_through"] == {
        "Fracture": [SAG],
        "ACL": [SAG],
        "Medial OA": [SAG],
    }
    # Each call keeps train.csv as its source; identity lineage stays recognition.
    for question in case["condition_calls"]:
        assert case["label_attribution"][question] == {
            **case["condition_teaching"]["labels"],
            "condition": question,
            "column": question,
        }
    assert case["teaching_source"]["kind"] == RECOGNITION_KIND
    assert "condition_calls" not in case["teaching_source"]
    lineage = case["identity_growth"]
    assert lineage["independent_confirmation"] is False
    assert "labels" not in lineage and "condition_teaching" not in lineage
    [entry] = child["object_identity_growth"]["rounds"]
    assert entry["condition_teaching"] == receipt["condition_teaching"]
    assert entry["condition_teaching"]["read_study_uids"] == ["study-x"]
    assert entry["condition_teaching"]["cases"] == {
        X: {"status": "carried", "condition_calls": case["condition_calls"]}
    }


def test_a_carried_positive_speaks_through_its_admission_view_and_not_outside_it(
    tmp_path: Path, parent
):
    _receipt, child, _labels = taught(tmp_path, parent)
    prepared = prepare_recall(child)
    assert prepared["outcome"] == "prepared"
    attached = {**child, "prepared_recall": prepared}
    # The capacity path's population: an unrelated study left out.
    view = memory_view(attached, exclude_study_uids=("study-s",))
    for question in ("Fracture", "ACL"):
        for memory in (attached, view):
            sagittal = condition_recall(memory, QUERY_SAG, question)
            assert sagittal["outcome"] == "present"
            assert sagittal["speaking_case_ids"] == [X]
            term = term_of(sagittal, X)
            assert (term["call"], term["common_speaking_banks"]) == (1, [SAG_BANK])
            assert term["call_scope"] == "positive_condition_presentation"
            # Coronally the admission's identity was never established: silent.
            coronal = condition_recall(memory, QUERY_COR, question)
            assert X in coronal["silent_case_ids"]
            assert X not in coronal["speaking_case_ids"]
            assert coronal["outcome"] != "present"
        # Its own study held out, it does not speak about that study at all.
        own = memory_view(attached, exclude_study_uids=("study-x",))
        held = condition_recall(own, QUERY_SAG, question)
        assert X not in [row["case_id"] for row in held["case_terms"]]
        assert held["outcome"] != "present"
    # Control: were its identity held coronally too, the same case would speak
    # there. The coronal silence is the identity scope, not a missing envelope.
    widened = copy.deepcopy(child)
    call_of(widened, X)["views"] = [COR, SAG]
    for question in ("Fracture", "ACL"):
        coronal = condition_recall(widened, QUERY_COR, question)
        assert coronal["outcome"] == "present"
        assert coronal["speaking_case_ids"] == [X]
        assert term_of(coronal, X)["common_speaking_banks"] == [COR_BANK]


def test_a_normal_label_speaks_only_through_the_admission_view(tmp_path: Path, parent):
    _receipt, child, _labels = taught(tmp_path, parent)
    sagittal = condition_recall(child, QUERY_SAG, "Medial OA")
    assert sagittal["outcome"] == "absent"
    assert sagittal["speaking_case_ids"] == [X]
    term = term_of(sagittal, X)
    assert (term["call"], term["common_speaking_banks"]) == (-1, [SAG_BANK])
    coronal = condition_recall(child, QUERY_COR, "Medial OA")
    assert X in coronal["silent_case_ids"]
    assert coronal["outcome"] != "absent"
    widened = copy.deepcopy(child)
    call_of(widened, X)["views"] = [COR, SAG]
    coronal = condition_recall(widened, QUERY_COR, "Medial OA")
    assert (coronal["outcome"], coronal["speaking_case_ids"]) == ("absent", [X])


def test_a_blank_label_makes_no_call(tmp_path: Path, parent):
    _receipt, child, _labels = taught(tmp_path, parent)
    case = case_of(child, X)
    # Femur conditions left blank on study-x's row carry nothing.
    for question in ("Lateral OA", "PF OA", "Contusion", "MCL"):
        assert question not in case["condition_calls"]
        assert question not in case["label_attribution"]
        assert question not in case["condition_teaching"]["carry"]["speaks_through"]
    assert prepare_recall(child)["case_indices"]["femur"].get("Contusion") is None
    # A row blank for every condition is read and carries no call at all.
    _receipt, blank, _labels = taught(
        tmp_path, parent, "blank-row", rows={"study-x": {}}
    )
    case = case_of(blank, X)
    assert case["condition_teaching"]["status"] == "carried"
    assert (
        case["condition_calls"],
        case["presentation_scope"],
        case["label_attribution"],
    ) == ({}, {}, {})


def test_a_bone_positive_stays_unlocalized_at_the_condition_combiner(
    tmp_path: Path, parent
):
    _receipt, child, _labels = taught(tmp_path, parent)
    case = case_of(child, X)
    assert case["presentation_scope"]["Fracture"] == "positive_condition_presentation"
    assert case["presentation_scope"]["Fracture"] != LOCALIZED_PRESENTATION_SCOPE
    carry = case["condition_teaching"]["carry"]
    assert (carry["localized_calls"], carry["unapplied_localized_calls"]) == ({}, [])
    # The study says some bone is affected, not which: the real combiner keeps
    # the femur's speaking positive for ranking, never as a localized finding.
    sagittal = condition_recall(child, QUERY_SAG, "Fracture")
    assert sagittal["outcome"] == "present"
    reading = combine_condition("Fracture", {"femur": sagittal})["evidence"][
        "readings"
    ]["femur"]
    assert reading["state"] == "unknown"
    assert reading["code"] == "study_positive_presentation_not_localized"
    # Were the same positive localized to this femur, it would read positive.
    localized = copy.deepcopy(child)
    case_of(localized, X)["presentation_scope"]["Fracture"] = (
        LOCALIZED_PRESENTATION_SCOPE
    )
    sagittal = condition_recall(localized, QUERY_SAG, "Fracture")
    reading = combine_condition("Fracture", {"femur": sagittal})["evidence"][
        "readings"
    ]["femur"]
    assert reading["state"] == "positive"


def test_a_study_with_no_label_row_gets_no_condition_calls_by_name(
    tmp_path: Path, parent
):
    receipt, child, labels = taught(
        tmp_path, parent, "test-study", rows={"study-other": STUDY_X}
    )
    case = case_of(child, X)
    assert case["condition_calls"] == {}
    assert "presentation_scope" not in case and "label_attribution" not in case
    assert case["condition_teaching"] == {
        "schema": CONDITION_TEACHING_SCHEMA,
        "status": "no_label_row",
        "labels": {
            "source": LABEL_SOURCE,
            "source_path": str(labels.resolve()),
            "source_sha256": receipt["condition_teaching"]["labels"]["source_sha256"],
            "study_uid": "study-x",
        },
    }
    teaching = child["object_identity_growth"]["rounds"][0]["condition_teaching"]
    assert teaching["read_study_uids"] == []
    assert teaching["cases"] == {X: {"status": "no_label_row"}}
    # With a row, the same admission carries its calls.
    _receipt, carried, _labels = taught(tmp_path, parent, "train-study")
    assert case_of(carried, X)["condition_calls"]


# ---------------------------------------------------- labels never decide


def test_labels_never_change_a_decision(tmp_path: Path, parent):
    plain = grow(tmp_path, "plain", parent, [record("study-x")])
    receipts = {"plain": plain}
    for name, value in (("ones", 1), ("zeros", 0)):
        labels = write_labels(
            tmp_path / f"{name}.csv",
            {"study-x": dict.fromkeys(LABELS, value)},
        )
        receipts[name] = grow(
            tmp_path, name, parent, [record("study-x")], labels=labels
        )
    data = {name: (tmp_path / name / DECISIONS_FILE).read_bytes() for name in receipts}
    assert data["plain"] == data["ones"] == data["zeros"]
    assert len({receipt["decisions_sha256"] for receipt in receipts.values()}) == 1
    children = {name: child_of(tmp_path, name) for name in receipts}
    carried = ("condition_calls", "presentation_scope", "label_attribution")
    for name in ("ones", "zeros"):
        child = children[name]
        # Apart from the carried calls and what records them, the children agree.
        for key in set(child) | set(children["plain"]):
            if key not in ("cases", "revision", "object_identity_growth"):
                assert child[key] == children["plain"][key], key
        for mine, theirs in zip(
            child["cases"], children["plain"]["cases"], strict=True
        ):
            if mine["case_id"] != X:
                assert mine == theirs
        case, plain_case = case_of(child, X), case_of(children["plain"], X)
        assert {
            key: value
            for key, value in case.items()
            if key not in (*carried, "condition_teaching")
        } == {
            key: value for key, value in plain_case.items() if key != "condition_calls"
        }
        assert plain_case["condition_calls"] == {}
        assert case["condition_calls"]
        [mine], [theirs] = (
            child["object_identity_growth"]["rounds"],
            children["plain"]["object_identity_growth"]["rounds"],
        )
        assert {k: v for k, v in mine.items() if k != "condition_teaching"} == theirs
    assert set(case_of(children["ones"], X)["condition_calls"].values()) == {1}
    assert set(case_of(children["zeros"], X)["condition_calls"].values()) == {-1}
    # A child carrying labels never shares a revision with another child.
    assert len({child["revision"] for child in children.values()}) == 3
    assert (
        "condition_teaching"
        not in children["plain"]["object_identity_growth"]["rounds"][0]
    )


def test_labels_are_checked_before_the_round_and_refused_with_decisions_only(
    tmp_path: Path, parent
):
    consumed: list[str] = []

    def stream():
        consumed.append("study-x")
        yield record("study-x")

    wrong = tmp_path / "wrong.csv"
    wrong.write_text("StudyInstanceUID,Report,Fracture\n", encoding="utf-8")
    for labels, code in (
        (wrong, "labels_columns_invalid"),
        (tmp_path / "missing.csv", "labels_unreadable"),
        (str(wrong), "labels_path_invalid"),
    ):
        with pytest.raises(IdentityGrowthError) as info:
            grow_identity_memory(
                parent, harvest_candidates(stream()), tmp_path / "out", labels=labels
            )
        assert info.value.code == code
    assert consumed == [] and not (tmp_path / "out").exists()
    good = write_labels(tmp_path / "train.csv", {"study-x": STUDY_X})
    with pytest.raises(IdentityGrowthError) as info:
        grow(
            tmp_path,
            "only",
            parent,
            [record("study-x")],
            labels=good,
            decisions_only=True,
        )
    assert info.value.code == "labels_with_decisions_only"
    assert not (tmp_path / "only").exists()
    only = grow(tmp_path, "only", parent, [record("study-x")], decisions_only=True)
    assert only["outcome"] == "decisions_only" and only["admitted_case_ids"] == [X]
    # A round that admits nothing reads no label row.
    quiet = grow(
        tmp_path, "quiet", parent, [record("study-x", anatomy="unknown")], labels=good
    )
    assert quiet["outcome"] == "no_admissions"
    assert quiet["condition_teaching"]["read_study_uids"] == []


# -------------------------------------------------------- held-out studies


def test_a_held_out_candidate_is_never_scored_and_is_admitted_otherwise(
    tmp_path: Path, parent
):
    held = grow(tmp_path, "held", parent, [record("study-x")], held_out=["study-x"])
    assert (held["outcome"], held["child"]) == ("no_admissions", None)
    assert held["state_counts"] == {"held_out": 1}
    document = decisions_of(tmp_path, "held")
    [decision] = document["decisions"]
    assert (decision["state"], decision["reason"]) == ("held_out", "study_held_out")
    assert decision["recognized_identity"] is None
    assert decision["views"] == [] and decision["support"] == []
    record_ = held_out_record(["study-x"])
    assert record_ == {
        "schema": HELD_OUT_SCHEMA,
        "study_uids": ["study-x"],
        "sha256": _json_sha256(["study-x"]),
    }
    assert document["held_out"] == record_ == held["held_out"]
    # The same candidate, not held out, is admitted; no held-out record is written.
    free = grow(tmp_path, "free", parent, [record("study-x")])
    assert free["admitted_case_ids"] == [X]
    assert free["held_out"] is None
    assert "held_out" not in decisions_of(tmp_path, "free")
    assert "held_out" not in child_of(tmp_path, "free")["object_identity_growth"]


def test_label_rows_are_read_only_for_admitted_studies(tmp_path: Path, parent):
    rows = {
        "study-x": {**STUDY_X, "Fracture": "x"},  # held out
        "study-z": {"Fracture": "x"},  # a proposal: not admitted
        "study-y": STUDY_X,
    }
    labels = write_labels(tmp_path / "train.csv", rows)
    records = [
        record("study-x"),
        record("study-y"),
        record("study-z", anatomy="unknown"),
    ]
    receipt = grow(
        tmp_path, "grown", parent, records, labels=labels, held_out=["study-x"]
    )
    assert receipt["state_counts"] == {"admitted": 1, "held_out": 1, "proposal": 1}
    assert receipt["condition_teaching"]["read_study_uids"] == ["study-y"]
    child = child_of(tmp_path, "grown")
    assert case_of(child, located_id("study-y"))["condition_calls"] == {
        "Fracture": 1,
        "ACL": 1,
        "Medial OA": -1,
    }
    block = child["object_identity_growth"]
    assert block["held_out"] == held_out_record(["study-x"])
    assert block["rounds"][0]["held_out"] == block["held_out"]
    # Not held out, study-x is admitted and its malformed row is read: refused.
    with pytest.raises(IdentityGrowthError) as info:
        grow(tmp_path, "leaked", parent, records, labels=labels)
    assert (info.value.code, info.value.detail) == (
        "labels_value_invalid",
        "study-x:Fracture",
    )
    assert not (tmp_path / "leaked").exists()
    # A repeated row of an admitted study is refused by name too.
    twice = tmp_path / "twice.csv"
    write_labels(twice, {"study-y": STUDY_X})
    with twice.open("a", newline="", encoding="utf-8") as stream:
        csv.writer(stream).writerow(["study-y", "again", *[""] * len(LABELS)])
    with pytest.raises(IdentityGrowthError) as info:
        grow(tmp_path, "twice", parent, [record("study-y")], labels=twice)
    assert info.value.code == "labels_study_uid_duplicate"


def test_every_child_keeps_its_parents_held_out_studies(tmp_path: Path, parent):
    first = grow(
        tmp_path,
        "round-1",
        parent,
        [record("study-h"), record("study-x")],
        held_out=["study-h"],
    )
    assert first["admitted_case_ids"] == [X]
    child = load_memory_snapshot(tmp_path / "round-1" / CHILD_DIRECTORY)
    assert inherited_held_out(child.memory) == {"study-h"}
    # Round two names only study-k; the parent's study-h stays held out.
    second = grow(
        tmp_path,
        "round-2",
        child,
        [record("study-h"), record("study-k"), record("study-w")],
        held_out=["study-k"],
    )
    states = {
        row["study_uid"]: row["state"]
        for row in decisions_of(tmp_path, "round-2")["decisions"]
    }
    assert states == {
        "study-h": "held_out",
        "study-k": "held_out",
        "study-w": "admitted",
    }
    union = held_out_record(["study-h", "study-k"])
    assert decisions_of(tmp_path, "round-2")["held_out"] == union
    grandchild = child_of(tmp_path, "round-2")
    assert grandchild["object_identity_growth"]["held_out"] == union
    assert [
        entry.get("held_out")
        for entry in grandchild["object_identity_growth"]["rounds"]
    ] == [held_out_record(["study-h"]), union]
    assert second["held_out"] == union
    # From a parent that records nothing held out, the same study-h is scored.
    open_round = grow(tmp_path, "open", parent, [record("study-h")])
    assert open_round["admitted_case_ids"] == [located_id("study-h")]


def test_a_malformed_held_out_record_or_list_is_refused_by_name(tmp_path: Path, parent):
    grow(
        tmp_path,
        "round-1",
        parent,
        [record("study-h"), record("study-x")],
        held_out=["study-h"],
    )
    grown = child_of(tmp_path, "round-1")
    for mutate in (
        lambda block: block["held_out"].update(sha256="0" * 64),
        lambda block: block["held_out"].update(study_uids=["study-z", "study-h"]),
        lambda block: block["held_out"].update(study_uids=[]),
        lambda block: block["held_out"].update(extra=True),
        lambda block: block.update(held_out=["study-h"]),
    ):
        broken = copy.deepcopy(grown)
        mutate(broken["object_identity_growth"])
        with pytest.raises(IdentityGrowthError) as info:
            inherited_held_out(broken)
        assert (info.value.code, info.value.detail) == (
            "parent_growth_metadata_invalid",
            "held_out",
        )
    broken = copy.deepcopy(grown)
    broken["object_identity_growth"]["held_out"]["sha256"] = "0" * 64
    save_memory(broken, tmp_path / "broken")
    with pytest.raises(IdentityGrowthError) as info:
        grow(
            tmp_path,
            "refused",
            load_memory_snapshot(tmp_path / "broken"),
            [record("study-w")],
        )
    assert info.value.code == "parent_growth_metadata_invalid"
    assert not (tmp_path / "refused").exists()
    for held_out, code in (
        (["study-x", "study-x"], "held_out_duplicate"),
        (["study x"], "held_out_invalid"),
        ([""], "held_out_invalid"),
        ("study-x", "held_out_invalid"),
        ([None], "held_out_invalid"),
    ):
        with pytest.raises(IdentityGrowthError) as info:
            grow(tmp_path, "bad", parent, [record("study-x")], held_out=held_out)
        assert info.value.code == code
        assert not (tmp_path / "bad").exists()
