"""Every located object answers its own questions as the object identified in context,
unless an applicable negative case speaks over the region asserted to be it.

Rohan, 2026-10-21: «The operation for finding and naming the bones is already built. Use
its results and their supporting observations. Do not restart bone recognition because a
downstream appearance comparison resembles another bone.» And: «A femur resembling a tibia
is compatible with both being bones.» And: «Diagnosis asks about the state of the
contextually identified object.» And: «Positive and negative cases are expertise, not
decorative annotations... Muscle surrounding a bone is different from muscle occupying the
region asserted to be the bone. A broad mixed window is different from a resolved object.»

So resemblance to another object never keeps a region from its own questions or its
bounded looks. A negative case whose reason holds for the asserted region (it speaks over
the object's own tiles) keeps that region from being read as the object: its questions
stay open, nothing renames it, and its bounded looks are still made. A negative heard only
through the surroundings changes nothing. ``identity_consumption``
(``knee.study-identity-consumption/v2``) records each object's identity context, its
recall outcome and effect, a revisable ``identity_question`` for a genuine contradictory
law observation, and an ``identity_open_question`` naming the existing bounded readings
that could settle an unsettled identity, run by nothing here.

Each meaning is pinned with both signs. ``recall_object`` is a spy (an empty profile gets
the real recall, as production gives an unlocated object); identity recall, configuration
composition and the condition contracts are the real ones.
"""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
from pathlib import Path

import pytest

from knee.diagnosis import squint_locator, squint_pipeline, squint_profiles
from knee.diagnosis.declarations import QUESTIONS
from knee.diagnosis.squint_anatomy_locator import BONES
from knee.diagnosis.squint_contracts import combine_condition
from knee.diagnosis.squint_identity import (
    APPEARANCE_OPPOSED,
    CONDITIONING,
    CONTEXT_SCHEMA,
    IDENTITY_CONSUMPTION_SCHEMA,
    MAP_RELATION,
    PRIOR_ONLY,
    PROPOSED_PLACES,
    RESOLVED_SUPPORT,
    SIGNED_CONFLICT,
    STRUCTURAL_READER,
    SUPPORT_UNRECORDED,
)
from knee.diagnosis.squint_interfaces import TERRITORY_PROCEDURE, territory_bank_name

REAL_RECALL = squint_locator.recall_object
SAG = {"orientation": "sagittal", "fluid_sensitive": "1", "fat_suppression": "1"}
COR = {"orientation": "coronal", "fluid_sensitive": "1", "fat_suppression": "1"}
SAG_TRIPLE = ["sagittal", "1", "1"]
SANITY_SCHEMA = "knee.object-anatomical-sanity/v1"
WINDOW = [0, 1, 0, 2, 0, 2]
#: The structural reader's provenance for its bone, as the anchor territory records it.
PROVENANCE = {
    "producer": "knee.diagnosis.squint_anchors.find_anchors/v1",
    "derivation": "middle_slice_named_by_the_established_rule",
    "rule": "knee.objects.assignments.assign_plane, read with its partner (with_partner)",
    "middle_slice_code": "agreed_with_its_partner",
    "partner": "read_with_series-sag-fat-dark",
    "scale": "native",
    "cross_view_checks": [
        {
            "against_series_uid": "series-cor",
            "against_orientation": "coronal",
            "against_slice": 15,
            "outcome": "no_carried_place_on_this_slice",
        }
    ],
}


def bank(view=SAG, role="object") -> str:
    return territory_bank_name(view, role, "m", "d", 10.0)


def tprofile(subject: str, counts, view=SAG, ring=None) -> dict:
    banks = {bank(view): list(counts)}
    if ring is not None:
        banks[bank(view, "context")] = list(ring)
    return {
        "schema": "knee.squint-profile/v1",
        "subject": subject,
        "banks": banks,
        "source": {"procedure": TERRITORY_PROCEDURE},
    }


def law_check(subject, target, result, *, candidate_subject=None, reference=None):
    """One authored law check, shaped as the locator records it."""
    return {
        "rule_id": f"authored:{subject}:superior_to:{target}",
        "subject": subject,
        "target": target,
        "candidate_role": "subject"
        if candidate_subject in (None, subject)
        else "target",
        "axis": "z",
        "relation": "superior_to",
        "expected_relation": "strictly_after",
        "candidate_interval": [0.0, 10.0],
        "target_interval": [20.0, 30.0],
        "result": result,
        "candidate_subject": candidate_subject or subject,
        "reference_subject": reference or target,
    }


def sanity(*checks) -> dict:
    """A knee.object-anatomical-sanity/v1 record over the one fixture window."""
    results = [check["result"] for check in checks]
    status = (
        "contradicted"
        if any(result.startswith("reversed_") for result in results)
        else "plausible"
        if any(result.startswith("supported_") for result in results)
        else "unknown"
    )
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
                "series_uid": "series-sag",
                "checks": list(checks),
            }
        ],
    }


def located(subject: str, counts, view=SAG) -> dict:
    """An object the locator holds a reading of, with no structural placement recorded."""
    return {
        "status": "located",
        "profile": tprofile(subject, counts, view),
        "regions": [],
    }


def anchored(subject: str, counts, ring=None) -> dict:
    """A bone located by its own structural anchor, as ``_anchored_object`` records it.

    Its sanity is the reader's own: an anchor whose law checks reversed is set aside
    before it can anchor (``_check_anchor_sanity``), so none appear here.
    """
    return {
        "status": "proposal",
        "profile": tprofile(subject, counts, ring=ring),
        "regions": [{"series_uid": "series-sag", "view": SAG, "window": list(WINDOW)}],
        "territories": [
            {
                "origin": "anchor_structure",
                "subject": subject,
                "provenance": copy.deepcopy(PROVENANCE),
            }
        ],
        "sanity": sanity(),
        "evidence": {
            "source": "current_study_structural_anchor",
            "location_route": "structural_anchor",
            "anchor": {
                "status": "partial",
                "code": "valid",
                "producer": "fixture-anchor",
                "key_planes": {
                    "sagittal": {
                        "outcome": "selected",
                        "series_uid": "series-sag",
                        "slice": 0,
                    }
                },
            },
            "reading_territories": "territories_on_selected_key_planes",
        },
    }


def set_aside(subject: str, reference: str) -> dict:
    """A structural anchor ``_check_anchor_sanity`` set aside for a reversed relation."""
    return {
        "status": "conflict",
        "code": "anatomical_relation_conflict",
        "anatomical_sanity": sanity(
            law_check(
                reference,
                subject,
                "reversed_strictly_after",
                candidate_subject=subject,
                reference=reference,
            )
        ),
    }


def placed(subject: str, counts, *, unanchored=None) -> dict:
    """An object the anatomy map placed from the established structural anchors."""
    evidence = {
        "source": "current_study_anatomy_first_finite_windows",
        "location_route": "anatomical_relation_from_structural_anchors",
    }
    if unanchored is not None:
        evidence["unanchored_bone"] = unanchored
    return {
        "status": "proposal",
        "profile": tprofile(subject, counts),
        "regions": [{"series_uid": "series-sag", "view": SAG, "window": list(WINDOW)}],
        "territories": [
            {
                "origin": "anatomical_relation",
                "subject": subject,
                "relation": {"kind": "authored_relation"},
                "anchors": [{"anchor": "femur", "kind": "structural_anchor"}],
            }
        ],
        "sanity": sanity(),
        "evidence": evidence,
    }


def seed(case_id: str, subject: str, study_uid: str, counts, ring=None) -> dict:
    return {
        "case_id": case_id,
        "subject": subject,
        "study_uid": study_uid,
        "profile": tprofile(subject, counts, ring=ring),
    }


def taught_memory(*, femur_negative: bool = False, ring: bool = False) -> dict:
    """Confirmed femur (3,0,0) and tibia (0,0,3) seeds; optionally a femur reject.

    The reject is a candidate proposed as femur whose sagittal support the reviewer
    called not femur: an ordinary negative identity case on its own view, with object
    tiles (1,2,0). With ``ring`` every case also carries context tiles, and the reject's
    object tiles are (0,3,0) while its context tiles are (1,2,0).
    """
    memory = {
        "revision": "r1",
        "cases": [
            seed("f1", "femur", "sf", (3, 0, 0), (3, 0, 0) if ring else None),
            seed("t1", "tibia", "st", (0, 0, 3), (0, 0, 3) if ring else None),
        ],
        "object_identity_teaching": {
            "schema": "knee.object-identity-teaching/v1",
            "confirmed_case_ids": ["f1", "t1"],
            "calls": [
                {"candidate_id": "f1", "call": "confirm"},
                {"candidate_id": "t1", "call": "confirm"},
            ],
        },
    }
    if femur_negative:
        negative = (
            seed("n1", "femur", "sn", (0, 3, 0), (1, 2, 0))
            if ring
            else seed("n1", "femur", "sn", (1, 2, 0))
        )
        memory["object_identity_cases"] = {
            "schema": "knee.object-identity-cases/v1",
            "cases": [negative],
        }
        teaching = memory["object_identity_teaching"]
        teaching["negative_case_ids"] = ["n1"]
        teaching["negative_views"] = {"n1": [SAG_TRIPLE]}
        teaching["calls"].append(
            {
                "candidate_id": "n1",
                "call": "reject",
                "views": [SAG_TRIPLE],
                "notes": "posterior soft tissue, not femur",
            }
        )
    return memory


def untaught(memory: dict) -> dict:
    """The same cases with no identity teaching declared."""
    return {
        key: value
        for key, value in memory.items()
        if key not in ("object_identity_teaching", "object_identity_cases")
    }


def bones(femur, tibia=None) -> dict:
    """Four located bones; patella and fibula on a view no identity seed speaks on."""
    return {
        "femur": femur,
        "tibia": tibia if tibia is not None else located("tibia", (0, 0, 3)),
        "patella": located("patella", (1, 1, 1), COR),
        "fibula": located("fibula", (1, 1, 1), COR),
    }


def warranted(subject: str, call: int, banks) -> dict:
    """A recall record whose one trusted case speaks ``call`` over ``banks``."""
    return {
        "outcome": "present" if call == 1 else "absent",
        "subject": subject,
        "case_terms": [
            {
                "case_id": f"{subject}-{'diagnosed' if call == 1 else 'normal'}",
                "call": call,
                "terms": {"dot": 1, "left_norm_sq": 1, "right_norm_sq": 1},
                "reaches_trust": True,
                "trust": {"source": "test-envelope"},
                "common_speaking_banks": list(banks),
            }
        ],
        "speaking_calls": [call],
        "vetoed_answers": [],
    }


def spy(monkeypatch, script) -> list:
    """Banked queries answer by ``script``; an empty profile gets the real recall."""
    calls: list = []

    def recall(profile, memory, *, question, exclude_study_uid):
        banks = tuple(sorted(profile["banks"]))
        calls.append((question, profile["subject"], banks))
        if not banks:
            return REAL_RECALL(
                profile, memory, question=question, exclude_study_uid=exclude_study_uid
            )
        return script(question, profile["subject"], banks)

    monkeypatch.setattr(squint_locator, "recall_object", recall)
    return calls


def all_normal(question, subject, banks):
    return warranted(subject, -1, banks)


def femur_left_open(question, subject, banks):
    """Every other object is normal; the femur's voice and every configuration stay
    untrusted proposals, so each femur question is left open and asks for a look."""
    if subject == "femur" or subject.startswith("diagnosis/"):
        return {"outcome": "proposal", "subject": subject, "case_terms": []}
    return warranted(subject, -1, banks)


def run_study(monkeypatch, memory, objects, script=all_normal):
    calls = spy(monkeypatch, script)
    monkeypatch.setattr(
        squint_profiles,
        "read_study_squints",
        lambda root, uid, io_workers=8: {
            "study_uid": uid,
            "series": [],
            "work": {"raw_read_mocked": True},
            "leg_map_status": "available",
            "leg_maps": {},
        },
    )
    monkeypatch.setattr(
        squint_locator,
        "locate_objects",
        lambda study, memory, **kwargs: {"objects": objects},
    )
    return squint_pipeline.infer_study(Path("."), "query", memory), calls


def reads_of(calls, subject):
    return [banks for _question, named, banks in calls if named == subject]


def configuration_banks(calls):
    return [
        bank
        for _q, named, banks in calls
        if named.startswith("diagnosis/")
        for bank in banks
    ]


def femur_questions():
    return [q.question_id for q in QUESTIONS if "femur" in q.objects]


def decided(record):
    return {
        q: (item["finding"], item["ranking"]) for q, item in record["questions"].items()
    }


def question(question_id):
    return next(q for q in QUESTIONS if q.question_id == question_id)


def femur_rows(record):
    return [row for row in record["observations"] if row.get("subject") == "femur"]


# ---------------------------------------------------------------------------
# the consumption record: resemblance answers, an applicable negative does not
# ---------------------------------------------------------------------------


def context(
    subject: str,
    basis: str = PRIOR_ONLY,
    contradictions=(),
    open_alternatives=(),
) -> dict:
    structural = basis == STRUCTURAL_READER
    return {
        "schema": CONTEXT_SCHEMA,
        "subject": subject,
        "basis": basis,
        "conditioning": CONDITIONING[basis],
        "support": RESOLVED_SUPPORT if structural else PROPOSED_PLACES,
        "open_alternatives": sorted(open_alternatives),
        "removed_by_structure": sorted(set(BONES) - {subject}) if structural else [],
        "contradictions": list(contradictions),
        "supporting_observations": {"reason": "fixture"},
    }


def reading(outcome: str, basis: str, appearance: str, *negatives: str) -> dict:
    return {
        "outcome": outcome,
        "identity": "femur",
        "identity_basis": basis,
        "identity_state": "fixture",
        "appearance": appearance,
        "applicable_negative_case_ids": list(negatives),
    }


@pytest.mark.parametrize(
    ("heard", "basis"),
    [
        (
            reading("established_by_structure", STRUCTURAL_READER, "silent"),
            STRUCTURAL_READER,
        ),
        (reading("appearance_supports", MAP_RELATION, "supports"), MAP_RELATION),
        (reading("appearance_silent", MAP_RELATION, "silent"), MAP_RELATION),
        (reading("placement_only", PRIOR_ONLY, "uncalibrated"), PRIOR_ONLY),
    ],
)
def test_whatever_its_recall_resembles_an_uncontested_object_answers_as_itself(
    heard, basis
):
    record = squint_pipeline._identity_consumption(
        {"femur": {}},
        {"outcome": "examined", "objects": {"femur": heard}},
        {"femur": context("femur", basis)},
    )
    assert record["schema"] == IDENTITY_CONSUMPTION_SCHEMA
    assert record["not_read_as_subject"] == []
    entry = record["objects"]["femur"]
    assert (entry["answers_questions_as"], entry["region_read_as_subject"]) == (
        "femur",
        True,
    )
    assert entry["identity_effect"] == "answers"
    assert entry["recall_outcome"] == heard["outcome"]
    assert entry["identity_basis"] == basis
    assert entry["identity_context"] == context("femur", basis)
    assert entry["identity_question"] is None
    assert entry["applicable_negative_case_ids"] == []
    assert squint_pipeline._regions_not_read(record) == {}


@pytest.mark.parametrize("outcome", [APPEARANCE_OPPOSED, SIGNED_CONFLICT])
@pytest.mark.parametrize("basis", [STRUCTURAL_READER, MAP_RELATION, PRIOR_ONLY])
def test_an_applicable_negative_keeps_the_region_from_being_read_as_its_object(
    outcome, basis
):
    record = squint_pipeline._identity_consumption(
        {"femur": {}, "tibia": {}},
        {
            "outcome": "examined",
            "objects": {
                "femur": reading(outcome, basis, "supports", "n1"),
                "tibia": reading("appearance_silent", basis, "silent"),
            },
        },
        {"femur": context("femur", basis), "tibia": context("tibia", basis)},
    )
    entry = record["objects"]["femur"]
    # Never renamed: the region is simply not read as the femur.
    assert (entry["answers_questions_as"], entry["region_read_as_subject"]) == (
        None,
        False,
    )
    assert entry["identity_effect"] == outcome
    assert entry["applicable_negative_case_ids"] == ["n1"]
    assert record["not_read_as_subject"] == ["femur"]
    assert record["objects"]["tibia"]["region_read_as_subject"] is True
    assert squint_pipeline._regions_not_read(record) == {
        "femur": {"reason": outcome, "applicable_negative_case_ids": ["n1"]}
    }
    # The contested identity names the bounded readings that could settle it.
    question_ = entry["identity_open_question"]
    assert (question_["status"], question_["why"]) == ("open", "contested")
    assert question_["run"] == "left_to_the_consumer_within_budget"
    assert [row["procedure"] for row in question_["next_observations"]] == [
        "paired_finer_reading"
    ]


def test_a_contradiction_is_a_revisable_question_and_a_plain_context_asks_none():
    reversed_check = {
        "scope": "set_aside_structural_anchor",
        "result": "reversed_strictly_after",
    }
    asked = squint_pipeline._identity_consumption(
        {"tibia": {}},
        {
            "outcome": "examined",
            "objects": {
                "tibia": reading("placement_only", MAP_RELATION, "uncalibrated")
            },
        },
        {"tibia": context("tibia", MAP_RELATION, contradictions=[reversed_check])},
    )["objects"]["tibia"]
    assert asked["identity_question"] == {
        "status": "open",
        "kind": "reversed_anatomical_relation",
        "revisable": True,
        "evidence": [reversed_check],
    }
    # A contradiction asks; it keeps nothing from the object's own questions.
    assert asked["answers_questions_as"] == "tibia"
    assert asked["region_read_as_subject"] is True
    plain = squint_pipeline._identity_consumption(
        {"tibia": {}},
        {
            "outcome": "examined",
            "objects": {
                "tibia": reading("placement_only", MAP_RELATION, "uncalibrated")
            },
        },
        {"tibia": context("tibia", MAP_RELATION)},
    )["objects"]["tibia"]
    assert plain["identity_question"] is None


@pytest.mark.parametrize(
    ("subject", "basis", "appearance", "asks"),
    [
        ("femur", STRUCTURAL_READER, "silent", False),
        ("femur", STRUCTURAL_READER, "uncalibrated", False),
        ("femur", MAP_RELATION, "supports", False),
        ("femur", MAP_RELATION, "silent", True),
        ("femur", PRIOR_ONLY, "uncalibrated", True),
        ("mcl", MAP_RELATION, "silent", True),
    ],
)
def test_an_unconfirmed_identity_names_its_next_observation_and_runs_nothing(
    subject, basis, appearance, asks
):
    from knee.diagnosis.squint_residual import producer_for

    outcome = (
        "established_by_structure"
        if basis == STRUCTURAL_READER
        else {
            "supports": "appearance_supports",
            "silent": "appearance_silent",
            "uncalibrated": "placement_only",
        }[appearance]
    )
    heard = {**reading(outcome, basis, appearance), "identity": subject}
    entry = squint_pipeline._identity_consumption(
        {subject: {}},
        {"outcome": "examined", "objects": {subject: heard}},
        {subject: context(subject, basis)},
    )["objects"][subject]
    question_ = entry["identity_open_question"]
    if not asks:
        assert question_ is None
        return
    assert (question_["why"], question_["support"]) == (
        "appearance_unconfirmed",
        PROPOSED_PLACES,
    )
    procedures = [row["procedure"] for row in question_["next_observations"]]
    if producer_for(subject) is None:
        assert procedures == ["paired_finer_reading"]
    else:
        # A part with its own native producer names that existing procedure too.
        assert procedures == ["paired_finer_reading", "residual_native_support"]
        assert question_["next_observations"][1]["request"]["lens"] == (
            producer_for(subject).lens
        )
    assert all(
        row["request"] == {**row["request"], "object": subject, "question": "identity"}
        for row in question_["next_observations"]
    )
    # Unconfirmed is not contested: the region is still read as the object.
    assert entry["region_read_as_subject"] is True


@pytest.mark.parametrize(
    "outcome", ["unreviewed_candidate_memory", "invalid_seed_teaching"]
)
def test_a_memory_whose_identity_teaching_was_not_heard_is_named(outcome):
    record = squint_pipeline._identity_consumption(
        {"femur": {}, "tibia": {}}, {"outcome": outcome, "objects": {}}
    )
    assert {
        name: entry["recall_outcome"] for name, entry in record["objects"].items()
    } == {
        "femur": outcome,
        "tibia": outcome,
    }
    assert all(
        entry["identity_context"] is None
        and entry["identity_question"] is None
        and entry["region_read_as_subject"] is True
        for entry in record["objects"].values()
    )


def test_an_examined_study_without_this_objects_reading_names_it():
    record = squint_pipeline._identity_consumption(
        {"femur": {}, "tibia": {}},
        {"outcome": "examined", "objects": {"tibia": {"outcome": "identified"}}},
    )
    assert record["objects"]["femur"]["recall_outcome"] == "identity_reading_missing"
    assert record["objects"]["tibia"]["recall_outcome"] == "identified"
    assert record["not_read_as_subject"] == []


# ---------------------------------------------------------------------------
# the consumers: reading takes only the regions not read; looks take no identity
# ---------------------------------------------------------------------------


def test_bounded_looks_take_no_identity_input_and_reading_takes_only_not_read_as():
    assert (
        "not_read_as"
        not in inspect.signature(squint_pipeline._bounded_observation).parameters
    )
    parameters = inspect.signature(squint_pipeline._recall_question).parameters
    assert parameters["not_read_as"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["not_read_as"].default is None
    for name in ("_identity_decision", "_withheld_objects"):
        assert not hasattr(squint_pipeline, name)
    for consumer in (
        squint_pipeline._recall_question,
        squint_pipeline._bounded_observation,
    ):
        assert "withheld" not in inspect.signature(consumer).parameters


def test_a_region_not_read_as_its_object_reaches_both_voices_as_unlocated(monkeypatch):
    declared = question("Fracture")
    objects = bones(located("femur", (3, 0, 0)))
    memory = {"revision": "r1", "cases": []}
    calls = spy(monkeypatch, all_normal)
    read = squint_pipeline._recall_question(declared, objects, memory, "q", False)
    # Read as the femur, its normal reading completes the all-normal defeat.
    assert combine_condition("Fracture", read)["outcome"] == "defeated"
    assert any(banks for banks in reads_of(calls, "femur"))
    assert any(b.startswith("object/femur/") for b in configuration_banks(calls))
    assert "region_not_read_as_subject" not in read["femur"]
    assert (
        squint_pipeline._recall_question(
            declared, objects, memory, "q", False, not_read_as={}
        )
        == read
    )

    calls.clear()
    reason = {"reason": APPEARANCE_OPPOSED, "applicable_negative_case_ids": ["n1"]}
    before = copy.deepcopy(objects)
    kept = squint_pipeline._recall_question(
        declared, objects, memory, "q", False, not_read_as={"femur": reason}
    )
    # Not read as the femur: both voices hear it as unlocated, so it stays open.
    assert all(banks == () for banks in reads_of(calls, "femur"))
    assert not any(b.startswith("object/femur/") for b in configuration_banks(calls))
    assert kept["femur"]["region_not_read_as_subject"] == reason
    assert kept["femur"]["location_status"] == "unavailable"
    finding = combine_condition("Fracture", kept)
    assert finding["outcome"] == "open"
    assert finding["evidence"]["readings"]["femur"]["state"] == "unknown"
    unlocated = squint_pipeline._recall_question(
        declared,
        {k: v for k, v in objects.items() if k != "femur"},
        memory,
        "q",
        False,
    )
    assert {
        k: v for k, v in kept["femur"].items() if k != "region_not_read_as_subject"
    } == (unlocated["femur"])
    assert objects == before


@pytest.mark.parametrize(
    ("question_id", "subject", "sign", "consumed_outcome"),
    [
        ("MCL", "mcl", -1, "defeated"),
        ("MCL", "mcl", 1, "assigned"),
        ("Fracture", "femur", 1, "assigned"),
    ],
)
def test_located_tissue_reaches_the_contract_and_unlocated_tissue_stays_unknown(
    monkeypatch, question_id, subject, sign, consumed_outcome
):
    declared = question(question_id)
    objects = {name: located(name, (1, 0, 1), COR) for name in declared.objects}

    def script(_question_id, named, banks):
        # The subject and its configuration speak ``sign``; every other object stays
        # normal, so the subject's own tissue alone decides the consumed question.
        if named.startswith("diagnosis/") or named == subject:
            return warranted(named, sign, banks)
        return warranted(named, -1, banks)

    calls = spy(monkeypatch, script)
    memory = {"revision": "r1", "cases": []}
    before = copy.deepcopy(objects)

    consumed = squint_pipeline._recall_question(declared, objects, memory, "q", False)
    assert combine_condition(question_id, consumed)["outcome"] == consumed_outcome
    assert any(banks for banks in reads_of(calls, subject))
    assert any(
        object_bank.startswith(f"object/{subject}/")
        for object_bank in configuration_banks(calls)
    )

    calls.clear()
    absent = {name: value for name, value in objects.items() if name != subject}
    unlocated = squint_pipeline._recall_question(declared, absent, memory, "q", False)
    assert all(banks == () for banks in reads_of(calls, subject))
    finding = combine_condition(question_id, unlocated)
    assert finding["outcome"] == "open"
    assert finding["evidence"]["readings"][subject]["state"] == "unknown"
    assert objects == before


def test_the_unlocated_path_hears_the_real_recall_of_an_empty_reading(monkeypatch):
    declared = question("Fracture")
    spy(monkeypatch, all_normal)
    objects = {
        k: v for k, v in bones(located("femur", (3, 0, 0))).items() if k != "femur"
    }
    record = squint_pipeline._recall_question(
        declared, objects, {"revision": "r1", "cases": []}, "q", False
    )
    femur = record["femur"]
    assert femur["outcome"] == "proposal"
    assert femur["location_status"] == "unavailable"
    assert femur["regions"] == [] and femur["query_origins"] == []
    assert "decision_scope" not in femur


# ---------------------------------------------------------------------------
# the production operation: infer_study with real identity recall in context
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("placement", [STRUCTURAL_READER, PRIOR_ONLY])
def test_a_femur_resembling_tibia_keeps_every_question_and_bounded_look(
    monkeypatch, placement
):
    femur = (
        anchored("femur", (0, 0, 3))
        if placement == STRUCTURAL_READER
        else located("femur", (0, 0, 3))
    )
    objects = bones(femur)
    original = copy.deepcopy(objects)
    record, calls = run_study(monkeypatch, taught_memory(), objects, femur_left_open)

    recall = record["identity_recall"]["objects"]["femur"]
    entry = record["identity_consumption"]["objects"]["femur"]
    assert (entry["answers_questions_as"], entry["region_read_as_subject"]) == (
        "femur",
        True,
    )
    assert entry["identity_basis"] == placement
    assert recall["identity"] == "femur"
    assert recall["also_resembles"][0]["identity"] == "tibia"
    if placement == STRUCTURAL_READER:
        # The reader established the bone; resembling the tibia renames nothing, and
        # the reader's other bones never set its own cases' bar.
        assert recall["outcome"] == "established_by_structure"
        assert recall["removed_by_structure"] == ["fibula", "patella", "tibia"]
        assert recall["established_views"] == [SAG_TRIPLE]
        assert entry["identity_open_question"] is None
    else:
        # Nothing known: the unconditioned recall names the tibia, and decides nothing.
        assert recall["outcome"] == "appearance_silent"
        assert recall["unconditioned_identity"] == "tibia"
        assert entry["identity_open_question"]["why"] == "appearance_unconfirmed"
    assert entry["recall_outcome"] == recall["outcome"]
    assert record["identity_consumption"]["not_read_as_subject"] == []
    # Every femur question heard the femur's own reading, in both voices.
    assert set(reads_of(calls, "femur")) == {(bank(),)}
    assert any(b.startswith("object/femur/") for b in configuration_banks(calls))
    for question_id in femur_questions():
        evidence = record["questions"][question_id]["objects"]["femur"]
        assert "region_not_read_as_subject" not in evidence
    # Each open femur question asked for a bounded look, and none was refused for
    # identity: this fixture's region lies in no series of the mocked study.
    assert femur_rows(record)
    assert all(row["code"] != "object_region_unavailable" for row in femur_rows(record))
    # The identity's open question is named, never run.
    assert all(
        (row.get("request") or {}).get("question") != "identity"
        for row in record["observations"]
    )
    assert record["objects"] == original


def test_a_located_femur_gives_its_own_findings_not_an_unlocated_ones(monkeypatch):
    present, _ = run_study(
        monkeypatch, taught_memory(), bones(anchored("femur", (0, 0, 3)))
    )
    absent = {
        k: v for k, v in bones(anchored("femur", (0, 0, 3))).items() if k != "femur"
    }
    missing, _ = run_study(monkeypatch, taught_memory(), absent)
    # Answering as itself, the normal femur completes the all-normal defeat.
    assert present["questions"]["Fracture"]["finding"]["outcome"] == "defeated"
    assert missing["questions"]["Fracture"]["finding"]["outcome"] == "open"
    assert decided(present) != decided(missing)


def test_an_applicable_negative_keeps_the_femur_open_and_its_looks_are_still_made(
    monkeypatch,
):
    record, calls = run_study(
        monkeypatch,
        taught_memory(femur_negative=True),
        bones(anchored("femur", (1, 2, 0))),
    )
    recall = record["identity_recall"]["objects"]["femur"]
    assert (recall["outcome"], recall["identity"]) == (APPEARANCE_OPPOSED, "femur")
    [negative] = recall["negative_cases"]
    assert (negative["case_id"], negative["applies"], negative["reason"]) == (
        "n1",
        True,
        "speaks_over_the_asserted_region",
    )
    assert negative["call_notes"] == "posterior soft tissue, not femur"
    assert negative["views"] == [SAG_TRIPLE]
    consumption = record["identity_consumption"]
    entry = consumption["objects"]["femur"]
    assert (entry["answers_questions_as"], entry["region_read_as_subject"]) == (
        None,
        False,
    )
    assert entry["applicable_negative_case_ids"] == ["n1"]
    assert consumption["not_read_as_subject"] == ["femur"]
    assert entry["identity_open_question"]["why"] == "contested"
    # The region the negative speaks over never reached the femur's questions.
    assert reads_of(calls, "femur") and all(b == () for b in reads_of(calls, "femur"))
    assert not any(b.startswith("object/femur/") for b in configuration_banks(calls))
    for question_id in femur_questions():
        evidence = record["questions"][question_id]["objects"]["femur"]
        assert evidence["region_not_read_as_subject"] == {
            "reason": APPEARANCE_OPPOSED,
            "applicable_negative_case_ids": ["n1"],
        }
    # Not a normal femur, so never the all-normal defeat: the question stays open.
    assert record["questions"]["Fracture"]["finding"]["outcome"] == "open"
    # Its bounded looks are still made: identity never refuses one.
    assert femur_rows(record)
    assert all(row["code"] != "object_region_unavailable" for row in femur_rows(record))
    # The same memory, a femur its negative does not speak over: read, and defeated.
    clean, _ = run_study(
        monkeypatch,
        taught_memory(femur_negative=True),
        bones(anchored("femur", (3, 0, 0))),
    )
    assert clean["identity_consumption"]["not_read_as_subject"] == []
    assert clean["questions"]["Fracture"]["finding"]["outcome"] == "defeated"


def test_a_negative_heard_only_through_the_surroundings_changes_nothing(monkeypatch):
    # The reject's context tiles resemble this femur's surroundings; its own object
    # tiles do not resemble the femur's: muscle around a bone, not occupying it.
    memory = taught_memory(femur_negative=True, ring=True)
    around = bones(anchored("femur", (3, 0, 0), ring=(1, 2, 0)))
    record, _ = run_study(monkeypatch, memory, copy.deepcopy(around))
    [negative] = record["identity_recall"]["objects"]["femur"]["negative_cases"]
    assert (negative["applies"], negative["reason"]) == (False, "surroundings_only")
    assert negative["with_the_surroundings"]["speaks"] is True
    assert negative["over_the_asserted_region"]["speaks"] is False
    assert record["identity_consumption"]["not_read_as_subject"] == []
    plain, _ = run_study(monkeypatch, untaught(memory), copy.deepcopy(around))
    assert record["questions"] == plain["questions"]
    assert record["observations"] == plain["observations"]
    # The same negative over the femur's own tiles applies.
    occupying = bones(anchored("femur", (0, 3, 0), ring=(1, 2, 0)))
    opposed, _ = run_study(monkeypatch, memory, occupying)
    assert opposed["identity_consumption"]["not_read_as_subject"] == ["femur"]


@pytest.mark.parametrize(
    ("femur_counts", "changes"),
    [((0, 0, 3), False), ((3, 0, 0), False), ((1, 2, 0), True)],
)
def test_identity_teaching_changes_condition_reading_only_where_a_negative_applies(
    monkeypatch, femur_counts, changes
):
    objects = bones(anchored("femur", femur_counts))
    taught, _ = run_study(
        monkeypatch, taught_memory(femur_negative=True), copy.deepcopy(objects)
    )
    plain, _ = run_study(monkeypatch, untaught(taught_memory()), copy.deepcopy(objects))
    if not changes:
        assert taught["questions"] == plain["questions"]
        assert taught["values"] == plain["values"]
        assert taught["observations"] == plain["observations"]
        return
    assert taught["questions"] != plain["questions"]
    for question_id in femur_questions():
        assert (
            "region_not_read_as_subject"
            in (taught["questions"][question_id]["objects"]["femur"])
        )
        assert (
            "region_not_read_as_subject"
            not in (plain["questions"][question_id]["objects"]["femur"])
        )
    # Questions that do not ask about the femur are untouched.
    for question_id, item in taught["questions"].items():
        if question_id not in femur_questions():
            assert item == plain["questions"][question_id]


def test_a_set_aside_anchor_asks_an_identity_question_and_still_answers(monkeypatch):
    """Reachable as the locator records it: a bone whose own structural anchor
    ``_check_anchor_sanity`` set aside for a reversed relation, placed by the map from
    the anchors that remain."""
    tibia = placed("tibia", (0, 0, 3), unanchored=set_aside("tibia", "femur"))
    record, calls = run_study(
        monkeypatch, taught_memory(), bones(anchored("femur", (3, 0, 0)), tibia)
    )
    entry = record["identity_consumption"]["objects"]["tibia"]
    assert entry["identity_basis"] == MAP_RELATION
    assert entry["identity_context"]["removed_by_structure"] == ["femur"]
    question_ = entry["identity_question"]
    assert (question_["status"], question_["revisable"]) == ("open", True)
    [evidence] = question_["evidence"]
    assert (evidence["scope"], evidence["result"], evidence["rule_id"]) == (
        "set_aside_structural_anchor",
        "reversed_strictly_after",
        "authored:femur:superior_to:tibia",
    )
    recall = record["identity_recall"]["objects"]["tibia"]
    assert recall["contradictions"] == question_["evidence"]
    # A contradiction asks; it keeps nothing from the tibia's own questions.
    assert (entry["answers_questions_as"], entry["region_read_as_subject"]) == (
        "tibia",
        True,
    )
    assert set(reads_of(calls, "tibia")) == {(bank(),)}
    kept = placed("tibia", (0, 0, 3))
    record, _ = run_study(
        monkeypatch, taught_memory(), bones(anchored("femur", (3, 0, 0)), kept)
    )
    assert (
        record["identity_consumption"]["objects"]["tibia"]["identity_question"] is None
    )


def test_a_bone_the_reader_names_carries_its_arrangement_and_support():
    contexts = squint_pipeline._identity_contexts(
        bones(anchored("femur", (3, 0, 0)), placed("tibia", (0, 0, 3)))
    )
    femur = contexts["femur"]
    assert (femur["basis"], femur["support"]) == (STRUCTURAL_READER, RESOLVED_SUPPORT)
    [arrangement] = femur["supporting_observations"]["arrangement"]
    assert arrangement["establishes"] == (
        "bone_identity_by_the_readers_observed_arrangement"
    )
    for key in (
        "producer",
        "derivation",
        "rule",
        "middle_slice_code",
        "partner",
        "scale",
    ):
        assert arrangement[key] == PROVENANCE[key]
    assert arrangement["cross_view_checks"] == [
        {
            "against_series_uid": "series-cor",
            "against_slice": 15,
            "outcome": ("no_carried_place_on_this_slice"),
        }
    ]
    tibia = contexts["tibia"]
    assert (tibia["basis"], tibia["support"]) == (MAP_RELATION, PROPOSED_PLACES)
    assert "arrangement" not in tibia["supporting_observations"]
    # The prior-only patella was read over no recorded territory.
    assert contexts["patella"]["support"] == SUPPORT_UNRECORDED


# ---------------------------------------------------------------------------
# a memory without identity teaching changes nothing
# ---------------------------------------------------------------------------

#: sha256 of the study record below, computed by the code before identity was wired into
#: the condition consumer (1804e00), with timing, RSS and the identity_consumption key set
#: aside.
NO_TEACHING_RECORD_SHA256 = "12b717097f7466528a178452ec81ac867b4b2dc8d4be8e46887a352043d24222"  # pragma: allowlist secret


def _record_digest(record: dict) -> str:
    kept = {k: v for k, v in record.items() if k != "identity_consumption"}
    kept["work"] = {
        k: v
        for k, v in record["work"].items()
        if k not in ("elapsed_seconds", "process_peak_rss_bytes_at_study_end")
    }
    text = json.dumps(kept, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _mixed(question_id, subject, banks):
    if subject.startswith("diagnosis/"):
        return warranted(subject, -1, banks)
    if subject == "acl" or (subject == "femur" and question_id == "Fracture"):
        return warranted(subject, 1, banks)
    return warranted(subject, -1, banks)


def no_teaching_objects() -> dict:
    """A femur shaped like the tibia seed, beside other located parts."""
    return {
        **bones(located("femur", (0, 0, 3))),
        "mcl": located("mcl", (1, 0, 1), COR),
        "acl": located("acl", (0, 1, 1), COR),
        "medial_meniscus": located("medial_meniscus", (1, 1, 0), COR),
    }


def test_a_memory_without_identity_teaching_gives_todays_study_record(monkeypatch):
    objects = no_teaching_objects()
    record, _ = run_study(monkeypatch, untaught(taught_memory()), objects, _mixed)
    assert record["identity_recall"] == {
        "outcome": "unreviewed_candidate_memory",
        "objects": {},
    }
    consumption = record["identity_consumption"]
    assert consumption["schema"] == IDENTITY_CONSUMPTION_SCHEMA
    assert consumption["not_read_as_subject"] == []
    assert sorted(consumption["objects"]) == sorted(objects)
    for name, entry in consumption["objects"].items():
        assert entry["answers_questions_as"] == name
        assert entry["recall_outcome"] == "unreviewed_candidate_memory"
        # The context is the locator's own record, read whether or not the memory is
        # taught.
        assert entry["identity_context"]["basis"] == PRIOR_ONLY
    assert _record_digest(record) == NO_TEACHING_RECORD_SHA256
