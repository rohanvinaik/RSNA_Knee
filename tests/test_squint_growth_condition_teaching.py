"""Two-sign intent of condition teaching and held-out studies in a growth round.

CLASSICAL_AI_BUILD_DESIGN §§5.1, 7 and 8. When a round admits a recognition-
derived object case, its study's official labels are carried onto it through
``carry_condition_calls``: a positive for a condition implicating the object is a
presentation in every view where the admission's identity holds, its normal
labels speak through those views alike, a blank label makes no call, and a
Fracture or Contusion positive stays unlocalized. The calls keep train.csv as
their source, apart from the recognition-derived identity lineage, and labels
never reach a decision. A held-out study is never scored or admitted, its labels
are never read, and every child keeps its parent's held-out studies.

The same carried row also teaches the study's whole-condition configuration
cases, made by the seed's own scoped builder from the cases admitted that round,
each role on its admission's views. The call is the official label alone, at
study scope; the identity basis stays recognition-derived; a blank label, an
unlabelled round, a proposal or a held-out candidate teaches none; and no parent
record is rebuilt, a held configuration or ledger row being refused by name.

Each test pins one meaning in both signs, through the growth API, the published
child and the production condition consumer: ``prepare_recall``/``recall_object``
as the squint pipeline calls them (``_recall_question``), ``memory_view`` and
``combine_condition``.
"""

from __future__ import annotations

import copy
import csv
import json
from pathlib import Path

import pytest

from knee.diagnosis.declarations import QUESTIONS, question_for
from knee.diagnosis.squint_bootstrap import _rebuilt_configurations
from knee.diagnosis.squint_configurations import (
    CONFIGURATION_TEACHING_SCHEMA,
    SEED_CALL_KIND,
    SUPERSEDED_CONFIGURATIONS_KEY,
    SUPERSEDED_CONFIGURATIONS_SCHEMA,
    ConfigurationProfileError,
    apply_rebuilt_configurations,
    rebuild_study_configurations,
    with_configuration_cases,
)
from knee.diagnosis.squint_contracts import combine_condition
from knee.diagnosis.squint_identity import (
    CONDITIONING,
    CONTEXT_SCHEMA,
    IDENTITY_CONSUMPTION_SCHEMA,
    MAP_RELATION,
    PROPOSED_PLACES,
    SANITY_SCHEMA,
    TEACHING_SCHEMA,
    prepare_identity,
)
from knee.diagnosis.squint_identity_growth import (
    CHILD_DIRECTORY,
    CONDITION_TEACHING_SCHEMA,
    DECISIONS_FILE,
    GROWTH_ROUND_KIND,
    GROWTH_SCHEMA,
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
from knee.diagnosis.squint_pipeline import _recall_question
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


def placed_femur() -> dict:
    """The identity context infer_study records for a femur the anatomy map placed
    with the patella still open beside it."""
    return {
        "schema": CONTEXT_SCHEMA,
        "subject": "femur",
        "basis": MAP_RELATION,
        "conditioning": CONDITIONING[MAP_RELATION],
        "support": PROPOSED_PLACES,
        "open_alternatives": ["patella"],
        "removed_by_structure": [],
        "contradictions": [],
        "supporting_observations": {"reason": "fixture"},
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
        "identity_consumption": {
            "schema": IDENTITY_CONSUMPTION_SCHEMA,
            "not_read_as_subject": [],
            "objects": {"femur": {"identity_context": placed_femur()}},
        },
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
    # Unlabelled, the child holds no configuration case and no ledger row.
    assert "label_ledger" not in children["plain"]
    assert not [case for case in children["plain"]["cases"] if is_configuration(case)]
    for name, value in (("ones", 1), ("zeros", 0)):
        child = children[name]
        # Apart from the carried calls, the configuration cases and the row they
        # were read from, and what records them, the children agree.
        for key in set(child) | set(children["plain"]):
            if key not in (
                "cases",
                "revision",
                "object_identity_growth",
                "label_ledger",
            ):
                assert child[key] == children["plain"][key], key
        assert child["label_ledger"] == {"study-x": dict.fromkeys(LABELS, value)}
        objects = [case for case in child["cases"] if not is_configuration(case)]
        for mine, theirs in zip(objects, children["plain"]["cases"], strict=True):
            if mine["case_id"] != X:
                assert mine == theirs
        # Every labelled question gets its configuration case, after the objects.
        assert [case["case_id"] for case in child["cases"][len(objects) :]] == [
            configuration_id("study-x", question) for question in QUESTION_ORDER
        ]
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
        taught_keys = ("condition_teaching", "configuration_teaching")
        assert {k: v for k, v in mine.items() if k not in taught_keys} == theirs
    assert set(case_of(children["ones"], X)["condition_calls"].values()) == {1}
    assert set(case_of(children["zeros"], X)["condition_calls"].values()) == {-1}
    # The labels are each configuration's call and never its composition.
    grown = {
        name: [case for case in children[name]["cases"] if is_configuration(case)]
        for name in ("ones", "zeros")
    }
    assert [case["profile"] for case in grown["ones"]] == [
        case["profile"] for case in grown["zeros"]
    ]
    assert {d for c in grown["ones"] for d in c["condition_calls"].values()} == {1}
    assert {d for c in grown["zeros"] for d in c["condition_calls"].values()} == {-1}
    # A child carrying labels never shares a revision with another child.
    assert len({child["revision"] for child in children.values()}) == 3
    for key in ("condition_teaching", "configuration_teaching"):
        assert key not in children["plain"]["object_identity_growth"]["rounds"][0]


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


def test_a_held_out_study_that_already_teaches_the_parent_is_refused(
    tmp_path: Path, parent
):
    # study-s is a femur seed of the parent. Holding it out would only skip its
    # candidates: the child would keep the seed and it would speak for study-x.
    with pytest.raises(IdentityGrowthError) as info:
        grow(tmp_path, "tainted", parent, [record("study-x")], held_out=["study-s"])
    assert (info.value.code, info.value.detail) == (
        "held_out_study_teaches_parent",
        "study-s",
    )
    assert not (tmp_path / "tainted").exists()
    # Every teaching study named is listed; an untaught one beside them is not.
    with pytest.raises(IdentityGrowthError) as info:
        grow(
            tmp_path,
            "tainted-2",
            parent,
            [record("study-x")],
            held_out=["study-p", "study-k", "study-b"],
        )
    assert (info.value.code, info.value.detail) == (
        "held_out_study_teaches_parent",
        "study-b,study-p",
    )
    assert not (tmp_path / "tainted-2").exists()
    # A study the parent never learned from is held out and the round goes on; the
    # admission's speaking cases are all from studies the parent learned from.
    clean = grow(
        tmp_path,
        "round-1",
        parent,
        [record("study-k"), record("study-x")],
        held_out=["study-k"],
    )
    assert clean["state_counts"] == {"admitted": 1, "held_out": 1}
    child = child_of(tmp_path, "round-1")
    studies = {case["case_id"]: case["study_uid"] for case in child["cases"]}
    speaking = case_of(child, X)["identity_growth"]["speaking_case_ids"]
    assert speaking and all(studies[case_id] != "study-k" for case_id in speaking)
    # A study admitted in an earlier round now teaches: it cannot be held out next.
    grown = load_memory_snapshot(tmp_path / "round-1" / CHILD_DIRECTORY)
    with pytest.raises(IdentityGrowthError) as info:
        grow(tmp_path, "round-2", grown, [record("study-w")], held_out=["study-x"])
    assert (info.value.code, info.value.detail) == (
        "held_out_study_teaches_parent",
        "study-x",
    )
    assert not (tmp_path / "round-2").exists()
    # An inherited held-out record naming a teaching study is refused the same way.
    inherited = copy.deepcopy(child)
    uids = ["study-k", "study-s"]
    inherited["object_identity_growth"]["held_out"] = held_out_record(uids)
    save_memory(inherited, tmp_path / "inherited")
    with pytest.raises(IdentityGrowthError) as info:
        grow(
            tmp_path,
            "round-3",
            load_memory_snapshot(tmp_path / "inherited"),
            [record("study-w")],
        )
    assert (info.value.code, info.value.detail) == (
        "held_out_study_teaches_parent",
        "study-s",
    )
    assert not (tmp_path / "round-3").exists()


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


# -------------------------------------- whole-condition configurations of a round

QUESTION_ORDER = tuple(question.question_id for question in QUESTIONS)
# The configured parent's labelled normal femurs, so every question the rounds
# below teach has an opposing configuration case.
SEED_ROW = {**NORMAL, "Contusion": 0}
FEMUR_SAG, FEMUR_COR = "object/femur/" + SAG_BANK, "object/femur/" + COR_BANK
PATELLA_SAG = "object/patella/" + SAG_BANK


def is_configuration(case: dict) -> bool:
    return case["subject"].startswith("diagnosis/")


def configuration_id(study: str, question: str) -> str:
    return f"squint-configuration:{study}:{question}"


def configurations_of(memory: dict, study: str) -> list[dict]:
    return [
        case
        for case in memory["cases"]
        if is_configuration(case) and case["study_uid"] == study
    ]


def located_of(uid: str, subject: str) -> str:
    return f"located:{uid}:{subject}:{REVISION}"


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def configured_parent_memory(rows: dict | None = None) -> dict:
    """The parent as a seed publishes it: its two labelled studies' configuration
    cases, built by the seed's own scoped builder, with their ledger rows."""
    if rows is None:
        rows = {"study-b": SEED_ROW, "study-c": SEED_ROW}
    memory = parent_memory()
    for case in memory["cases"]:
        if case["study_uid"] in rows:
            calls, scopes = _condition_calls(
                "femur", label_row(rows[case["study_uid"]])
            )
            case.update(condition_calls=calls, presentation_scope=scopes)
    ledger = {study: label_row(row) for study, row in rows.items()}
    built, kept, revision = _rebuilt_configurations({"label_ledger": ledger}, memory)
    memory.update(cases=[*memory["cases"], *built], label_ledger=kept)
    memory["revision"] = revision
    return memory


@pytest.fixture
def configured(tmp_path: Path):
    save_memory(configured_parent_memory(), tmp_path / "configured-parent")
    return load_memory_snapshot(tmp_path / "configured-parent")


def with_patella(base: dict, anatomy: str = "plausible") -> dict:
    """The record with a located patella beside its femur; only the patella
    seed's sagittal reading resembles it."""
    result = copy.deepcopy(base)
    located = copy.deepcopy(result["objects"]["femur"])
    outcome = "supported_strictly_after" if anatomy == "plausible" else "unknown"
    located.update(
        profile=profile("patella", {SAG_BANK: (0, 0, 3)}),
        sanity=sanity("patella", anatomy, outcome),
    )
    result["objects"]["patella"] = located
    return result


def next_round(memory: dict, question: str, banks=QUERY_SAG) -> tuple[dict, dict]:
    """One question of a later study read on a published memory, as ``infer_study``
    reads it: ``_recall_question`` on a located femur, then ``combine_condition``."""
    attached = {**memory, "prepared_recall": prepare_recall(memory)}
    located = {
        "femur": {
            "status": "located",
            "profile": profile("femur", banks),
            "regions": [{"series_uid": "series-sag", "window": list(WINDOW)}],
        }
    }
    evidence = _recall_question(
        question_for(question), located, attached, "study-q", False
    )
    return evidence, combine_condition(question, evidence)


def lineage_link(case: dict) -> dict:
    lineage = case["identity_growth"]
    return {
        "kind": RECOGNITION_KIND,
        "independent_confirmation": False,
        "parent_manifest_sha256": lineage["parent_manifest_sha256"],
        "lineage_sha256": _json_sha256(lineage),
    }


def test_a_labelled_admission_teaches_its_studys_configurations_on_its_views(
    tmp_path: Path, configured
):
    rows = {"study-x": {**STUDY_X, "Effusion": 1}}
    receipt, child, _labels = taught(tmp_path, configured, rows=rows)
    [decision] = decisions_of(tmp_path, "grown")["decisions"]
    assert (decision["state"], decision["views"]) == ("admitted", [SAG])
    femur = case_of(child, X)
    assert set(femur["profile"]["banks"]) == {SAG_BANK, COR_BANK}
    row = label_row(rows["study-x"])
    grown = configurations_of(child, "study-x")
    # One case per labelled question; a blank label writes none.
    assert [case["case_id"] for case in grown] == [
        configuration_id("study-x", question)
        for question in QUESTION_ORDER
        if row[question] is not None
    ]
    record_ = receipt["configuration_teaching"]
    for case in grown:
        question = case["subject"].removeprefix("diagnosis/")
        objects = question_for(question).objects
        present = [subject for subject in objects if subject == "femur"]
        source = case["profile"]["source"]
        # The role holds only its admission's view: the coronal reading stays out.
        assert case["profile"]["banks"] == ({FEMUR_SAG: [3, 0, 0]} if present else {})
        assert sorted(source["roles"]) == present
        assert source["missing_roles"] == [
            {"subject": subject, "status": "missing_object_case"}
            for subject in objects
            if subject not in present
        ]
        # The call is the official label alone, as the seed's builder writes it.
        assert case["condition_calls"] == {question: 1 if row[question] else -1}
        assert case["presentation_scope"] == {question: "study_condition_configuration"}
        assert case["label_attribution"] == {
            question: {
                "source": "label_ledger",
                "study_uid": "study-x",
                "condition": question,
            }
        }
        assert case["teaching_source"] == {
            "kind": "official_train_csv_label_ledger",
            "scope": "study_condition_configuration",
        }
        # The role names its admitted case; its identity stays recognition-derived.
        assert case["configuration_teaching"] == {
            "schema": CONFIGURATION_TEACHING_SCHEMA,
            "labels": {**record_["labels"], "study_uid": "study-x"},
            "built_by": record_["built_by"],
            "roles": {
                "femur": {
                    "case_id": X,
                    "identity_views": [SAG],
                    "identity": lineage_link(femur),
                }
            }
            if present
            else {},
            "supersedes": None,
        }
    # Exactly the builder's cases for the admitted case read on its view alone.
    scoped = {**femur, "profile": {**femur["profile"], "banks": {SAG_BANK: [3, 0, 0]}}}
    staged = {
        "schema": SCHEMA,
        "revision": "builder",
        "cases": [scoped],
        "label_ledger": {"study-x": row},
    }
    expected = with_configuration_cases(staged, procedure=TERRITORY_PROCEDURE)
    assert [
        {key: value for key, value in case.items() if key != "configuration_teaching"}
        for case in grown
    ] == expected["cases"][1:]
    # Control: were its identity held coronally too, the same builder hears both.
    widened = copy.deepcopy(child)
    call_of(widened, X)["views"] = [COR, SAG]
    rebuilt, _rows, _revision = _rebuilt_configurations(
        {"label_ledger": {"study-x": row}}, {**widened, "cases": [case_of(widened, X)]}
    )
    assert set(rebuilt[-1]["profile"]["banks"]) == {FEMUR_SAG, FEMUR_COR}
    # The round's record, the ledger row it adds, and the revision binding both.
    [entry] = child["object_identity_growth"]["rounds"]
    assert entry["configuration_teaching"] == record_
    assert record_ == {
        "schema": CONFIGURATION_TEACHING_SCHEMA,
        "labels": receipt["condition_teaching"]["labels"],
        "built_by": {
            "kind": GROWTH_ROUND_KIND,
            "ordinal": 1,
            "parent_manifest_sha256": configured.sha256,
            "decisions_sha256": receipt["decisions_sha256"],
        },
        "study_uids": ["study-x"],
        "case_ids": [case["case_id"] for case in grown],
        "superseded": {},
        "cases_sha256": _json_sha256(grown),
        "label_ledger_added": ["study-x"],
    }
    assert child["label_ledger"] == {
        **configured.memory["label_ledger"],
        "study-x": row,
    }
    parts = [
        configured.sha256,
        receipt["decisions_sha256"],
        GROWTH_SCHEMA,
        _json_sha256(entry["condition_teaching"]),
    ]
    bound = _json_sha256([*parts, _json_sha256(record_)])[:16]
    assert (
        child["revision"] == f"{configured.memory['revision']}+identity-growth-{bound}"
    )
    assert bound != _json_sha256(parts)[:16]


def test_no_label_row_or_label_file_teaches_no_configuration(
    tmp_path: Path, configured
):
    parent_ids = [case["case_id"] for case in configured.memory["cases"]]
    plain = grow(tmp_path, "plain", configured, [record("study-x")])
    child = child_of(tmp_path, "plain")
    assert plain["configuration_teaching"] is None
    assert "configuration_teaching" not in child["object_identity_growth"]["rounds"][0]
    assert [case["case_id"] for case in child["cases"]] == [*parent_ids, X]
    assert child["label_ledger"] == configured.memory["label_ledger"]
    # A study with no row teaches none; neither does a row blank for every label.
    for name, rows, read in (
        ("test-study", {"study-other": STUDY_X}, []),
        ("blank-row", {"study-x": {}}, ["study-x"]),
    ):
        receipt, child, _labels = taught(tmp_path, configured, name, rows=rows)
        assert [case["case_id"] for case in child["cases"]] == [*parent_ids, X]
        teaching = receipt["configuration_teaching"]
        assert (teaching["study_uids"], teaching["case_ids"]) == (read, [])
    assert child["label_ledger"]["study-x"] == dict.fromkeys(LABELS)
    # The same admission with its row teaches exactly its labelled questions.
    receipt, child, _labels = taught(tmp_path, configured, "labelled")
    assert receipt["configuration_teaching"]["case_ids"] == [
        configuration_id("study-x", question)
        for question in QUESTION_ORDER
        if question in STUDY_X
    ]


def test_parent_configurations_stay_byte_identical_where_nothing_was_admitted(
    tmp_path: Path, configured
):
    manifest = configured.path.read_bytes()
    before = canonical(configured.memory)
    taught(tmp_path, configured, "round-1")
    # The parent, in memory and on disk, is never changed.
    assert canonical(configured.memory) == before
    assert configured.path.read_bytes() == manifest
    child = child_of(tmp_path, "round-1")
    held = {case["case_id"]: case for case in child["cases"]}
    for case in configured.memory["cases"]:
        assert canonical(held[case["case_id"]]) == canonical(case)
    # Round two admits in study-y alone: every case of round one, the teaching
    # set's and study-x's configurations included, stays byte for byte.
    first = load_memory_snapshot(tmp_path / "round-1" / CHILD_DIRECTORY)
    first_bytes = first.path.read_bytes()
    labels = write_labels(tmp_path / "round-2.csv", {"study-y": STUDY_X})
    second = grow(tmp_path, "round-2", first, [record("study-y")], labels=labels)
    assert first.path.read_bytes() == first_bytes
    grandchild = child_of(tmp_path, "round-2")
    later = {case["case_id"]: case for case in grandchild["cases"]}
    for case in child["cases"]:
        assert canonical(later[case["case_id"]]) == canonical(case)
    assert second["configuration_teaching"]["superseded"] == {}
    # Nothing was replaced, so neither child keeps a superseded record.
    assert SUPERSEDED_CONFIGURATIONS_KEY not in child
    assert SUPERSEDED_CONFIGURATIONS_KEY not in grandchild
    assert second["configuration_teaching"]["case_ids"] == [
        configuration_id("study-y", question)
        for question in QUESTION_ORDER
        if question in STUDY_X
    ]


def test_a_later_admission_rebuilds_its_studys_configurations_with_every_role(
    tmp_path: Path, configured
):
    taught(tmp_path, configured, "round-1")
    first = load_memory_snapshot(tmp_path / "round-1" / CHILD_DIRECTORY)
    child = first.memory
    versions = {case["case_id"]: case for case in configurations_of(child, "study-x")}
    labels = write_labels(tmp_path / "round-2.csv", {"study-x": STUDY_X})
    again = [with_patella(record("study-x"))]
    second = grow(tmp_path, "round-2", first, again, labels=labels)
    states = {
        row["subject"]: row["state"]
        for row in decisions_of(tmp_path, "round-2")["decisions"]
    }
    assert states == {"femur": "duplicate", "patella": "admitted"}
    grandchild = child_of(tmp_path, "round-2")
    # The same ids, in the parent versions' places: one live case per condition.
    ids = [case["case_id"] for case in grandchild["cases"]]
    assert len(ids) == len(set(ids))
    assert ids[: len(child["cases"])] == [case["case_id"] for case in child["cases"]]
    assert [case["case_id"] for case in configurations_of(grandchild, "study-x")] == [
        *versions
    ]
    # Both rounds' admissions are roles, each on its own admission's view.
    patella = case_of(grandchild, located_of("study-x", "patella"))
    fracture = case_of(grandchild, configuration_id("study-x", "Fracture"))
    assert fracture["profile"]["banks"] == {
        FEMUR_SAG: [3, 0, 0],
        PATELLA_SAG: [0, 0, 3],
    }
    assert fracture["configuration_teaching"]["roles"] == {
        "femur": {
            "case_id": X,
            "identity_views": [SAG],
            "identity": lineage_link(case_of(grandchild, X)),
        },
        "patella": {
            "case_id": patella["case_id"],
            "identity_views": [SAG],
            "identity": lineage_link(patella),
        },
    }
    # Round two's admission was recognized against round one's child.
    assert patella["identity_growth"]["parent_manifest_sha256"] == first.sha256
    # The version it replaces is recorded with its round, and the parent keeps it.
    prior = versions[configuration_id("study-x", "Fracture")]
    assert fracture["configuration_teaching"]["supersedes"] == {
        "case_sha256": _json_sha256(prior),
        "built_by": prior["configuration_teaching"]["built_by"],
    }
    assert prior["configuration_teaching"]["built_by"]["ordinal"] == 1
    assert fracture["configuration_teaching"]["built_by"]["ordinal"] == 2
    assert second["configuration_teaching"]["superseded"] == {
        case_id: _json_sha256(case) for case_id, case in versions.items()
    }
    on_disk = load_memory_snapshot(first.path)
    assert on_disk.sha256 == first.sha256
    assert canonical(case_of(on_disk.memory, prior["case_id"])) == canonical(prior)
    # In the child each replaced version stops speaking and stays as a record.
    records = grandchild[SUPERSEDED_CONFIGURATIONS_KEY]["cases"]
    assert [canonical(r["case"]) for r in records] == [
        canonical(case) for case in versions.values()
    ]
    built = fracture["configuration_teaching"]["built_by"]
    assert all(record["superseded_by"] == built for record in records)
    assert all(record["case"] not in grandchild["cases"] for record in records)
    # A condition the patella has no role in keeps round one's composition.
    acl = case_of(grandchild, configuration_id("study-x", "ACL"))
    assert acl["profile"] == versions[configuration_id("study-x", "ACL")]["profile"]
    # Without a label file the admission still rebuilds them, from the ledger row.
    plain = grow(tmp_path, "round-2-plain", first, again)
    unlabelled = child_of(tmp_path, "round-2-plain")
    fracture = case_of(unlabelled, configuration_id("study-x", "Fracture"))
    assert set(fracture["profile"]["banks"]) == {FEMUR_SAG, PATELLA_SAG}
    assert fracture["condition_calls"] == {"Fracture": 1}
    assert fracture["configuration_teaching"]["labels"] == {
        "source": "label_ledger",
        "study_uid": "study-x",
    }
    assert fracture["configuration_teaching"]["built_by"]["parent_manifest_sha256"] == (
        first.sha256
    )
    assert plain["configuration_teaching"]["labels"] is None
    assert (
        case_of(unlabelled, located_of("study-x", "patella"))["condition_calls"] == {}
    )


def test_a_teaching_study_is_rebuilt_only_when_an_object_of_it_is_admitted(
    tmp_path: Path, configured
):
    teaching = configured.memory["object_identity_teaching"]
    seed_id = "squint-case:study-b:femur"
    [seed_call] = [row for row in teaching["calls"] if row["candidate_id"] == seed_id]
    versions = {
        case["case_id"]: case
        for case in configurations_of(configured.memory, "study-b")
    }
    labels = write_labels(tmp_path / "train.csv", {"study-b": SEED_ROW})
    grow(
        tmp_path, "grown", configured, [with_patella(record("study-b"))], labels=labels
    )
    child = child_of(tmp_path, "grown")
    patella = case_of(child, located_of("study-b", "patella"))
    assert [case["case_id"] for case in configurations_of(child, "study-b")] == [
        *versions
    ]
    fracture = case_of(child, configuration_id("study-b", "Fracture"))
    assert fracture["profile"]["banks"] == {
        FEMUR_SAG: [1, 2, 0],
        PATELLA_SAG: [0, 0, 3],
    }
    # Each role keeps its own provenance: the seed's visual call, the admission's
    # recognition-derived lineage.
    assert fracture["configuration_teaching"]["roles"] == {
        "femur": {
            "case_id": seed_id,
            "identity_views": None,
            "identity": {
                "kind": SEED_CALL_KIND,
                "reader": "fixture reviewer",
                "call_sha256": _json_sha256(seed_call),
            },
        },
        "patella": {
            "case_id": patella["case_id"],
            "identity_views": [SAG],
            "identity": lineage_link(patella),
        },
    }
    prior = versions[configuration_id("study-b", "Fracture")]
    assert fracture["configuration_teaching"]["supersedes"] == {
        "case_sha256": _json_sha256(prior),
        "built_by": None,
    }
    # The teaching set's versions are kept whole as records, study-b's alone; the
    # other teaching study, nothing of it admitted, keeps its cases speaking.
    records = child[SUPERSEDED_CONFIGURATIONS_KEY]["cases"]
    assert [canonical(r["case"]) for r in records] == [
        canonical(case) for case in versions.values()
    ]
    for case in configurations_of(configured.memory, "study-c"):
        assert canonical(case_of(child, case["case_id"])) == canonical(case)
    # A round admitting nothing of study-b leaves its cases byte for byte too.
    taught(tmp_path, configured, "elsewhere")
    elsewhere = child_of(tmp_path, "elsewhere")
    for case in versions.values():
        assert canonical(case_of(elsewhere, case["case_id"])) == canonical(case)


def test_a_proposal_or_held_out_candidate_contributes_no_role(
    tmp_path: Path, configured
):
    rows = {"study-x": STUDY_X, "study-h": {"Fracture": "x"}}
    labels = write_labels(tmp_path / "train.csv", rows)
    records = [with_patella(record("study-x"), "unknown"), record("study-h")]
    receipt = grow(
        tmp_path, "grown", configured, records, labels=labels, held_out=["study-h"]
    )
    decided = {
        (row["study_uid"], row["subject"]): (row["state"], row["reason"])
        for row in decisions_of(tmp_path, "grown")["decisions"]
    }
    assert decided == {
        ("study-x", "femur"): ("admitted", "identified_with_location_support"),
        ("study-x", "patella"): ("proposal", "anatomy_unknown"),
        ("study-h", "femur"): ("held_out", "study_held_out"),
    }
    child = child_of(tmp_path, "grown")
    fracture = case_of(child, configuration_id("study-x", "Fracture"))
    assert fracture["profile"]["banks"] == {FEMUR_SAG: [3, 0, 0]}
    assert sorted(fracture["profile"]["source"]["roles"]) == ["femur"]
    assert {"subject": "patella", "status": "missing_object_case"} in fracture[
        "profile"
    ]["source"]["missing_roles"]
    assert configurations_of(child, "study-h") == []
    assert receipt["configuration_teaching"]["study_uids"] == ["study-x"]
    assert "study-h" not in child["label_ledger"]
    # Admitted, the same patella is a role on its admission's view.
    both = write_labels(tmp_path / "both.csv", {"study-x": STUDY_X})
    grow(tmp_path, "both", configured, [with_patella(record("study-x"))], labels=both)
    fracture = case_of(
        child_of(tmp_path, "both"), configuration_id("study-x", "Fracture")
    )
    assert fracture["profile"]["banks"] == {
        FEMUR_SAG: [3, 0, 0],
        PATELLA_SAG: [0, 0, 3],
    }


def test_the_next_rounds_consumer_decides_only_through_defining_tissue(
    tmp_path: Path, configured
):
    _receipt, child, _labels = taught(tmp_path, configured)
    grow(tmp_path, "plain", configured, [record("study-x")])
    plain = child_of(tmp_path, "plain")
    # Fracture: the femur is a defining site, so the grown configuration decides.
    grown = configuration_id("study-x", "Fracture")
    evidence, finding = next_round(child, "Fracture")
    joint = evidence["diagnosis/Fracture"]
    assert (joint["outcome"], joint["speaking_case_ids"]) == ("present", [grown])
    [term] = [row for row in joint["case_terms"] if row["case_id"] == grown]
    assert term["reaches_trust"] is True
    assert term["common_speaking_banks"] == [FEMUR_SAG]
    assert term["call_scope"] == "study_condition_configuration"
    assert (finding["outcome"], finding["reason"]) == (
        "assigned",
        "warranted_condition_configuration",
    )
    assert finding["evidence"]["decided_by"] == ["diagnosis/Fracture"]
    # Without that case (an unlabelled round) nothing decides.
    _evidence, unlabelled = next_round(plain, "Fracture")
    assert unlabelled["outcome"] == "open"
    # ACL: the femur is only its context. The same voice grades and never decides.
    acl = configuration_id("study-x", "ACL")
    evidence, finding = next_round(child, "ACL")
    assert evidence["diagnosis/ACL"]["speaking_case_ids"] == [acl]
    assert (finding["outcome"], finding["reason"]) == (
        "open",
        "configuration_defining_tissue_coverage_missing",
    )
    coverage = finding["evidence"]["joint_configuration_coverage"]
    excluded = {row["case_id"]: row["reason"] for row in coverage["excluded_cases"]}
    assert excluded[acl] == "defining_tissue_coverage_incomplete"
    unheard = {key: value for key, value in evidence.items() if key != "diagnosis/ACL"}
    ungraded = combine_condition("ACL", unheard)
    assert ungraded["outcome"] == "open"
    assert 4 / 9 < ungraded["probability"] < finding["probability"] < 5 / 9


def test_a_bone_positive_configuration_stays_at_study_scope(tmp_path: Path, configured):
    rows = {"study-x": {**STUDY_X, "Contusion": 1}}
    _receipt, child, _labels = taught(tmp_path, configured, rows=rows)
    femur = case_of(child, X)
    carry = femur["condition_teaching"]["carry"]
    assert (femur["condition_calls"], femur["presentation_scope"]) == (
        carry["condition_calls"],
        carry["presentation_scope"],
    )
    for question in ("Fracture", "Contusion"):
        configuration = case_of(child, configuration_id("study-x", question))
        assert configuration["condition_calls"] == {question: 1}
        assert configuration["presentation_scope"] == {
            question: "study_condition_configuration"
        }
        # The femur keeps the study's unlocalized presentation, as carried.
        assert femur["presentation_scope"][question] == (
            "positive_condition_presentation"
        )
        _evidence, finding = next_round(child, question)
        reading = finding["evidence"]["readings"]["femur"]
        assert (reading["state"], reading["code"]) == (
            "unknown",
            "study_positive_presentation_not_localized",
        )
        assert finding["outcome"] == "assigned"
        assert finding["evidence"]["decided_by"] == [f"diagnosis/{question}"]
    scopes = {
        scope
        for case in child["cases"]
        for scope in (case.get("presentation_scope") or {}).values()
    }
    assert LOCALIZED_PRESENTATION_SCOPE not in scopes
    # Were the femur's positive localized, the femur itself would decide.
    localized = copy.deepcopy(child)
    case_of(localized, X)["presentation_scope"]["Fracture"] = (
        LOCALIZED_PRESENTATION_SCOPE
    )
    _evidence, finding = next_round(localized, "Fracture")
    assert finding["evidence"]["readings"]["femur"]["state"] == "positive"
    assert finding["evidence"]["decided_by"] == ["femur"]


def test_a_label_row_or_configuration_the_parent_holds_otherwise_is_refused(
    tmp_path: Path, configured
):
    again = [with_patella(record("study-b"))]
    # A carried row differing from the parent's ledger row.
    changed = write_labels(
        tmp_path / "changed.csv", {"study-b": {**SEED_ROW, "ACL": 1}}
    )
    with pytest.raises(IdentityGrowthError) as info:
        grow(tmp_path, "changed", configured, again, labels=changed)
    assert (info.value.code, info.value.detail) == (
        "label_ledger_row_conflict",
        "study-b",
    )
    assert not (tmp_path / "changed").exists()
    # The same row as the parent's is kept, never added again.
    same = write_labels(tmp_path / "same.csv", {"study-b": SEED_ROW})
    receipt = grow(tmp_path, "same", configured, again, labels=same)
    assert receipt["configuration_teaching"]["label_ledger_added"] == []
    ledger = child_of(tmp_path, "same")["label_ledger"]
    assert ledger == configured.memory["label_ledger"]
    # A configured study whose ledger row is missing cannot be rebuilt, and a
    # parent case its row no longer writes would stay live beside the rebuild.
    rowless = configured_parent_memory()
    del rowless["label_ledger"]["study-b"]
    stale = configured_parent_memory()
    stale["label_ledger"]["study-b"]["ACL"] = None
    refusals = (
        (rowless, ("configuration_label_row_missing", "study-b")),
        (
            stale,
            ("configuration_rebuild_incomplete", configuration_id("study-b", "ACL")),
        ),
    )
    for index, (memory, expected) in enumerate(refusals):
        save_memory(memory, tmp_path / f"refusing-{index}")
        parent_ = load_memory_snapshot(tmp_path / f"refusing-{index}")
        with pytest.raises(IdentityGrowthError) as info:
            grow(tmp_path, f"refused-{index}", parent_, again)
        assert (info.value.code, info.value.detail) == expected
        assert not (tmp_path / f"refused-{index}").exists()
    # A new case's id the parent holds under another study is never overwritten.
    misfiled = configured_parent_memory()
    acl = configuration_id("study-x", "ACL")
    [held] = [
        case
        for case in misfiled["cases"]
        if case["case_id"] == configuration_id("study-c", "ACL")
    ]
    held["case_id"] = acl
    save_memory(misfiled, tmp_path / "misfiled")
    with pytest.raises(IdentityGrowthError) as info:
        taught(tmp_path, load_memory_snapshot(tmp_path / "misfiled"), "misfiled-round")
    assert (info.value.code, info.value.detail) == ("configuration_case_conflict", acl)
    assert not (tmp_path / "misfiled-round").exists()


# ------------------------------------- the same rebuild for any publication

DIRECT_VISUAL_KIND = "independent_direct_visual_teaching"
VISUAL_READER = "fixture visual reviewer"
PUBLISHED = {"kind": "direct_visual_teaching", "additions_sha256": "1" * 64}
ACL_SAG = "object/acl/" + SAG_BANK
BURSA = "gastrocnemius_semimembranosus_bursa"


def visual_id(study: str, subject: str) -> str:
    return f"direct-visual:{study}:{subject}:native-r1"


def with_direct_visual_cases(memory: dict, study: str, additions) -> dict:
    """``memory`` plus direct visual teaching cases of ``(subject, views)``, added as
    the visual publisher adds them: each case with its publication's provenance and
    an explicit confirm call, and no full profile."""
    calls = [
        {
            "candidate_id": visual_id(study, subject),
            "call": "confirm",
            "reader": VISUAL_READER,
            "views": views,
            "notes": "pictured on its native image",
        }
        for subject, views in additions
    ]
    provenance = {
        "schema": "knee.direct-visual-teaching/v1",
        "kind": DIRECT_VISUAL_KIND,
        "reader": VISUAL_READER,
        "additions_sha256": "1" * 64,
        "case_ids": [call["candidate_id"] for call in calls],
        "calls": calls,
        "configuration_extension": "pending_C2",
    }
    child = copy.deepcopy(memory)
    for (subject, _views), call in zip(additions, calls, strict=True):
        child["cases"].append(
            {
                "case_id": call["candidate_id"],
                "study_uid": study,
                "subject": subject,
                "condition_calls": {},
                "profile": profile(subject, {SAG_BANK: (0, 0, 3), COR_BANK: (0, 3, 0)}),
                "regions": [],
                "teaching_source": {
                    "kind": DIRECT_VISUAL_KIND,
                    "reader": VISUAL_READER,
                },
                "direct_visual_teaching": {**provenance, "call": call},
            }
        )
        teaching = child["object_identity_teaching"]
        teaching["confirmed_case_ids"].append(call["candidate_id"])
        teaching["calls"].append(call)
    return child


def test_a_direct_visual_case_gives_its_studys_acl_configuration_an_acl_role():
    memory = configured_parent_memory(
        {"study-b": {**SEED_ROW, "ACL": 1}, "study-c": SEED_ROW}
    )
    acl_id = configuration_id("study-b", "ACL")
    before = case_of(memory, acl_id)
    # The teaching set's ACL configuration of study-b hears its femur alone.
    assert before["condition_calls"] == {"ACL": 1}
    assert sorted(before["profile"]["source"]["roles"]) == ["femur"]
    visual = with_direct_visual_cases(memory, "study-b", [("acl", [SAG])])
    untouched = canonical(visual)
    case_id = visual_id("study-b", "acl")
    [call] = [
        row
        for row in visual["object_identity_teaching"]["calls"]
        if row["candidate_id"] == case_id
    ]
    published = PUBLISHED
    rebuilt = rebuild_study_configurations(visual, ["study-b"], built_by=published)
    acl = rebuilt["replaces"][acl_id]
    # The ACL is a role, on its identity view alone, beside the seed's femur.
    assert acl["profile"]["banks"] == {ACL_SAG: [0, 0, 3], FEMUR_SAG: [1, 2, 0]}
    roles = acl["configuration_teaching"]["roles"]
    assert roles["acl"] == {
        "case_id": case_id,
        "identity_views": [SAG],
        "identity": {
            "kind": DIRECT_VISUAL_KIND,
            "reader": VISUAL_READER,
            "call_sha256": _json_sha256(call),
            "provenance_sha256": _json_sha256(
                case_of(visual, case_id)["direct_visual_teaching"]
            ),
        },
    }
    assert roles["femur"]["identity"]["kind"] == SEED_CALL_KIND
    # The call stays the official study label; the teaching set's version is recorded.
    assert acl["condition_calls"] == {"ACL": 1}
    assert acl["presentation_scope"] == {"ACL": "study_condition_configuration"}
    assert acl["configuration_teaching"]["labels"] == {
        "source": "label_ledger",
        "study_uid": "study-b",
    }
    assert acl["configuration_teaching"]["built_by"] == published
    assert acl["configuration_teaching"]["supersedes"] == {
        "case_sha256": _json_sha256(before),
        "built_by": None,
    }
    assert sorted(rebuilt["replaces"]) == sorted(
        case["case_id"] for case in configurations_of(memory, "study-b")
    )
    assert (rebuilt["new"], rebuilt["label_ledger"]) == ([], {})
    # Placed, each replaces its version in place; study-c's stay byte for byte.
    child = apply_rebuilt_configurations(visual, rebuilt)
    ids = [case["case_id"] for case in child["cases"]]
    assert ids == [case["case_id"] for case in visual["cases"]]
    for case in configurations_of(visual, "study-c"):
        assert canonical(case_of(child, case["case_id"])) == canonical(case)
    assert canonical(visual) == untouched
    # Each replaced version left the speaking cases and stays, whole, as a record.
    assert child[SUPERSEDED_CONFIGURATIONS_KEY] == {
        "schema": SUPERSEDED_CONFIGURATIONS_SCHEMA,
        "cases": [
            {
                "case_sha256": _json_sha256(case),
                "superseded_by": published,
                "case": case,
            }
            for case in configurations_of(visual, "study-b")
        ],
    }
    # A rebuild is never applied twice, nor onto a memory it was not made from.
    for target in (child, memory):
        with pytest.raises(ConfigurationProfileError) as info:
            apply_rebuilt_configurations(target, rebuilt)
        assert info.value.code == "rebuilt_configurations_stale"
    # The production preparation now hears the ACL role for ACL; before, only
    # the femur.
    index = ids.index(acl_id)
    for memory_, heard in ((child, {ACL_SAG, FEMUR_SAG}), (visual, {FEMUR_SAG})):
        prepared = prepare_recall(memory_)
        assert set(prepared["question_case_profile_banks"]["ACL"][index]) == heard
    # A study with no configuration yet gets new cases from the row supplied.
    fresh = with_direct_visual_cases(memory, "study-v", [("acl", [SAG])])
    source = {"source": "train.csv", "source_sha256": "2" * 64}
    rebuilt = rebuild_study_configurations(
        fresh,
        ["study-v"],
        built_by=published,
        labels={"study-v": label_row({"ACL": 1})},
        label_source=source,
    )
    [new] = rebuilt["new"]
    assert new["case_id"] == configuration_id("study-v", "ACL")
    assert new["profile"]["banks"] == {ACL_SAG: [0, 0, 3]}
    assert new["configuration_teaching"]["labels"] == {**source, "study_uid": "study-v"}
    assert rebuilt["label_ledger"] == {"study-v": label_row({"ACL": 1})}
    assert apply_rebuilt_configurations(fresh, rebuilt)["cases"][-1] == new
    # Supplied labels need their source named, and the builder a kind.
    for options, code in (
        (
            {"labels": {"study-v": label_row({"ACL": 1})}},
            "labels_or_label_source_invalid",
        ),
        ({"built_by": {"additions_sha256": "1" * 64}}, "built_by_invalid"),
    ):
        with pytest.raises(ConfigurationProfileError) as info:
            rebuild_study_configurations(
                fresh, ["study-v"], **{"built_by": published, **options}
            )
        assert info.value.code == code


def test_a_direct_visual_child_extends_its_studys_configurations_dropping_none(
    tmp_path: Path,
):
    """The shape of the five-case visual child: in one taught study an ACL and an
    MCL with positive labels, a bursa normal for Baker's, and two identity-only
    objects, all direct visual cases with no full profile."""
    row = {**SEED_ROW, "ACL": 1, "MCL": 1, "Baker's": 0}
    memory = configured_parent_memory({"study-b": row, "study-c": SEED_ROW})
    additions = [
        ("acl", [SAG]),
        ("mcl", [COR]),
        (BURSA, [SAG]),
        ("iliotibial_band", [COR]),
        ("lcl", [COR]),
    ]
    visual = with_direct_visual_cases(memory, "study-b", additions)
    for subject, _views in additions:
        case = case_of(visual, visual_id("study-b", subject))
        assert "direct_visual_teaching" in case and "full_profile" not in case
    held = configurations_of(visual, "study-b")
    others = {
        case["case_id"]: canonical(case)
        for case in visual["cases"]
        if case["study_uid"] != "study-b"
    }
    rebuilt = rebuild_study_configurations(visual, ["study-b"], built_by=PUBLISHED)
    save_memory(apply_rebuilt_configurations(visual, rebuilt), tmp_path / "visual")
    child = load_memory_snapshot(tmp_path / "visual").memory
    ids = [case["case_id"] for case in child["cases"]]
    live = {case["case_id"]: case for case in configurations_of(child, "study-b")}
    # Every configuration of the study is rebuilt under its own id: none dropped,
    # none speaking twice, every replaced version kept whole as a record.
    assert len(ids) == len(set(ids))
    assert list(live) == [case["case_id"] for case in held]
    records = child[SUPERSEDED_CONFIGURATIONS_KEY]["cases"]
    assert [record["case"] for record in records] == held
    assert all(record["case"] != live[record["case"]["case_id"]] for record in records)
    # The new roles, each on its own identity view with its visual provenance.
    banks = {
        question: live[configuration_id("study-b", question)]["profile"]["banks"]
        for question in ("ACL", "MCL", "Baker's")
    }
    assert banks == {
        "ACL": {ACL_SAG: [0, 0, 3], FEMUR_SAG: [1, 2, 0]},
        "MCL": {"object/mcl/" + COR_BANK: [0, 3, 0], FEMUR_SAG: [1, 2, 0]},
        "Baker's": {f"object/{BURSA}/" + SAG_BANK: [0, 0, 3]},
    }
    for question, subject in (("ACL", "acl"), ("MCL", "mcl"), ("Baker's", BURSA)):
        case = live[configuration_id("study-b", question)]
        role = case["configuration_teaching"]["roles"][subject]
        assert (role["case_id"], role["identity"]["kind"]) == (
            visual_id("study-b", subject),
            DIRECT_VISUAL_KIND,
        )
        assert case["condition_calls"] == {question: 1 if row[question] else -1}
    # Identity-only objects are no condition's role.
    for case in live.values():
        assert not {"iliotibial_band", "lcl"} & set(case["profile"]["source"]["roles"])
    # Conditions whose objects gained nothing keep round one's composition.
    for question in ("Medial OA", "Contusion", "Fracture"):
        case_id = configuration_id("study-b", question)
        [prior] = [r["case"] for r in records if r["case"]["case_id"] == case_id]
        assert live[case_id]["profile"] == prior["profile"]
    # Every other study's cases stay byte for byte.
    for case in child["cases"]:
        if case["study_uid"] != "study-b":
            assert canonical(case) == others[case["case_id"]]
    # The production consumers read the published child.
    assert prepare_identity(child)["outcome"] == "prepared"
    prepared = prepare_recall(child)
    index = ids.index(configuration_id("study-b", "Baker's"))
    assert set(prepared["question_case_profile_banks"]["Baker's"][index]) == {
        f"object/{BURSA}/" + SAG_BANK
    }
