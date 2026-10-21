"""Identity recall governs which located tissue condition reasoning consumes.

The binding (OpenSpec ``complete-signed-bootstrap-loop``, "Identity recall affects the
decisions that consume tissue"; CLASSICAL_AI_BUILD_DESIGN §10 step 5): tissue recognized
as a different object, or spoken against by its own subject's negative cases alone, is
withheld from that subject's condition questions (object and whole-configuration voices
alike) and from bounded reads aimed at it. It reaches ``combine_condition`` exactly as an
unlocated object does: unknown, never normal, never a defeat. It is never reassigned to
the other identity, and its located record stays retained and unmodified. Identified as
itself, conflicted, unresolved, missing or untaught, the structure's placement stands.

Each decision is pinned with both signs. ``recall_object`` is a spy (an empty profile gets
the real recall, as production gives an unlocated object); identity recall, configuration
composition and the condition contracts are the real ones.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from knee.diagnosis import (
    squint_locator,
    squint_pipeline,
    squint_profiles,
    squint_residual,
)
from knee.diagnosis.declarations import QUESTIONS
from knee.diagnosis.squint_contracts import combine_condition
from knee.diagnosis.squint_interfaces import TERRITORY_PROCEDURE, territory_bank_name

REAL_RECALL = squint_locator.recall_object
SAG = {"orientation": "sagittal", "fluid_sensitive": "1", "fat_suppression": "1"}
COR = {"orientation": "coronal", "fluid_sensitive": "1", "fat_suppression": "1"}
SAG_TRIPLE = ["sagittal", "1", "1"]
SANITY_SCHEMA = "knee.object-anatomical-sanity/v1"
WITHHELD_AS_TIBIA = {"reason": "identity_recognized_as_other", "recognized_as": "tibia"}


def bank(view=SAG) -> str:
    return territory_bank_name(view, "object", "m", "d", 10.0)


def tprofile(subject: str, counts, view=SAG) -> dict:
    return {
        "schema": "knee.squint-profile/v1",
        "subject": subject,
        "banks": {bank(view): list(counts)},
        "source": {"procedure": TERRITORY_PROCEDURE},
    }


def located(subject: str, counts, view=SAG, sanity=None) -> dict:
    record = {
        "status": "located",
        "profile": tprofile(subject, counts, view),
        "regions": [],
    }
    if sanity is not None:
        record["sanity"] = {
            "schema": SANITY_SCHEMA,
            "status": sanity,
            "identity_assertion": None,
            "windows": [],
        }
    return record


def seed(case_id: str, subject: str, study_uid: str, counts) -> dict:
    return {
        "case_id": case_id,
        "subject": subject,
        "study_uid": study_uid,
        "profile": tprofile(subject, counts),
    }


def taught_memory(*, femur_negative: bool = False) -> dict:
    """Confirmed femur (3,0,0) and tibia (0,0,3) seeds; optionally a femur reject.

    The reject is a candidate proposed as femur whose sagittal support, (1,2,0), the
    reviewer called not femur: an ordinary negative identity case on its own view.
    """
    memory = {
        "revision": "r1",
        "cases": [
            seed("f1", "femur", "sf", (3, 0, 0)),
            seed("t1", "tibia", "st", (0, 0, 3)),
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
        memory["object_identity_cases"] = {
            "schema": "knee.object-identity-cases/v1",
            "cases": [seed("n1", "femur", "sn", (1, 2, 0))],
        }
        teaching = memory["object_identity_teaching"]
        teaching["negative_case_ids"] = ["n1"]
        teaching["negative_views"] = {"n1": [SAG_TRIPLE]}
        teaching["calls"].append(
            {"candidate_id": "n1", "call": "reject", "views": [SAG_TRIPLE]}
        )
    return memory


def untaught(memory: dict) -> dict:
    """The same cases with no identity teaching declared."""
    return {
        key: value
        for key, value in memory.items()
        if key not in ("object_identity_teaching", "object_identity_cases")
    }


def bones(femur_counts) -> dict:
    """Four located bones; patella and fibula on a view no identity seed speaks on."""
    return {
        "femur": located("femur", femur_counts),
        "tibia": located("tibia", (0, 0, 3)),
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


def femur_fracture_positive(question, subject, banks):
    if subject == "femur" and question == "Fracture":
        return warranted(subject, 1, banks)
    if subject.startswith("diagnosis/"):
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


def without_annotation(record: dict) -> dict:
    return {key: value for key, value in record.items() if key != "identity_withheld"}


# ---------------------------------------------------------------------------
# the pure decision, both signs of every rule
# ---------------------------------------------------------------------------


def reading(outcome, identity=None, speaking=(), opposed=None, **extra):
    record = {
        "outcome": outcome,
        "identity": identity,
        "speaking_identities": list(speaking),
    }
    if opposed is not None:
        record["opposed_identities"] = list(opposed)
    record.update(extra)
    return record


@pytest.mark.parametrize(
    ("item", "expected"),
    [
        # Recognized as a different object: withheld, named, never reassigned.
        (
            reading("identified", "tibia", ["tibia"]),
            {"decision": "withheld", **WITHHELD_AS_TIBIA},
        ),
        # Recognized as itself: kept.
        (
            reading("identified", "femur", ["femur"], opposed=[]),
            {"decision": "kept", "reason": "identified", "recognized_as": "femur"},
        ),
        # Spoken against by its own negative cases alone, whatever else is unresolved.
        *(
            (
                reading(outcome, None, speaking, opposed=["femur"], **extra),
                {
                    "decision": "withheld",
                    "reason": "identity_opposed_by_negative_cases",
                },
            )
            for outcome, speaking, extra in (
                ("unresolved_no_precedent", [], {}),
                ("proposal", [], {}),
                ("blocked_by_sanity", ["tibia"], {"blocked_identity": "tibia"}),
                ("unresolved_conflict", ["patella", "tibia"], {}),
            )
        ),
        # Spoken for and against: a conflict, kept and flagged.
        (
            reading("unresolved_conflict", None, ["femur"], opposed=["femur"]),
            {"decision": "kept", "reason": "unresolved_conflict"},
        ),
        (
            reading("unresolved_conflict", None, ["femur", "tibia"], opposed=[]),
            {"decision": "kept", "reason": "unresolved_conflict"},
        ),
        # Another identity's opposition says nothing against this object.
        (
            reading("unresolved_no_precedent", None, [], opposed=["tibia"]),
            {"decision": "kept", "reason": "unresolved_no_precedent"},
        ),
        # A blocked identity, its own or another's, is not a recognition: kept.
        (
            reading("blocked_by_sanity", None, ["femur"], blocked_identity="femur"),
            {"decision": "kept", "reason": "blocked_by_sanity"},
        ),
        (
            reading("blocked_by_sanity", None, ["tibia"], blocked_identity="tibia"),
            {"decision": "kept", "reason": "blocked_by_sanity"},
        ),
        *(
            (reading(outcome), {"decision": "kept", "reason": outcome})
            for outcome in (
                "proposal",
                "unresolved_no_precedent",
                "unresolved_missing_reading",
                "silent",
                "invalid_input",
                "invalid_preparation",
            )
        ),
    ],
)
def test_one_located_objects_identity_decides_what_its_tissue_answers(item, expected):
    assert squint_pipeline._identity_decision("femur", item, "examined") == expected


@pytest.mark.parametrize(
    "outcome", ["unreviewed_candidate_memory", "invalid_seed_teaching"]
)
def test_a_memory_whose_identity_teaching_was_not_heard_keeps_every_placement(outcome):
    other = reading("identified", "tibia", ["tibia"])
    assert squint_pipeline._identity_decision("femur", other, outcome) == {
        "decision": "kept",
        "reason": outcome,
    }
    consumption = squint_pipeline._identity_consumption(
        {"femur": {}, "tibia": {}}, {"outcome": outcome, "objects": {}}
    )
    assert consumption == {
        "femur": {"decision": "kept", "reason": outcome},
        "tibia": {"decision": "kept", "reason": outcome},
    }


def test_an_examined_study_without_this_objects_reading_keeps_it_by_name():
    consumption = squint_pipeline._identity_consumption(
        {"femur": {}, "tibia": {}},
        {"outcome": "examined", "objects": {"tibia": reading("identified", "femur")}},
    )
    assert consumption == {
        "femur": {"decision": "kept", "reason": "identity_reading_missing"},
        "tibia": {
            "decision": "withheld",
            "reason": "identity_recognized_as_other",
            "recognized_as": "femur",
        },
    }


# ---------------------------------------------------------------------------
# both voices reach combine_condition exactly as for an unlocated object
# ---------------------------------------------------------------------------


def question(question_id):
    return next(q for q in QUESTIONS if q.question_id == question_id)


@pytest.mark.parametrize(
    ("question_id", "subject", "sign", "consumed_outcome"),
    [
        ("MCL", "mcl", -1, "defeated"),
        ("MCL", "mcl", 1, "assigned"),
        ("Fracture", "femur", 1, "assigned"),
    ],
)
def test_withheld_tissue_reaches_the_contract_exactly_as_unlocated_tissue(
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
    assert any(
        object_bank.startswith(f"object/{subject}/")
        for object_bank in configuration_banks(calls)
    )

    calls.clear()
    withheld = squint_pipeline._recall_question(
        declared, objects, memory, "q", False, withheld={subject: WITHHELD_AS_TIBIA}
    )
    absent = {name: value for name, value in objects.items() if name != subject}
    unlocated = squint_pipeline._recall_question(declared, absent, memory, "q", False)

    # The subject's own voice heard no tissue, and no configuration composed it.
    assert all(banks == () for banks in reads_of(calls, subject))
    assert not any(
        object_bank.startswith(f"object/{subject}/")
        for object_bank in configuration_banks(calls)
    )
    # Exactly the unlocated record, with the named reason beside it.
    assert withheld[subject]["identity_withheld"] == WITHHELD_AS_TIBIA
    assert without_annotation(withheld[subject]) == unlocated[subject]
    assert {k: v for k, v in withheld.items() if k != subject} == {
        k: v for k, v in unlocated.items() if k != subject
    }
    finding = combine_condition(question_id, withheld)
    assert finding == combine_condition(question_id, unlocated)
    # Unknown: never a normal reading, never a defeat, never an assignment.
    assert finding["outcome"] == "open"
    assert finding["evidence"]["readings"][subject]["state"] == "unknown"
    assert subject in finding["evidence"]["unresolved_subjects"]
    assert objects == before


def test_a_withheld_alternative_cannot_complete_an_all_normal_defeat(monkeypatch):
    declared = question("Fracture")
    objects = bones((3, 0, 0))
    spy(monkeypatch, all_normal)
    memory = {"revision": "r1", "cases": []}
    consumed = squint_pipeline._recall_question(declared, objects, memory, "q", False)
    assert combine_condition("Fracture", consumed)["outcome"] == "defeated"
    withheld = squint_pipeline._recall_question(
        declared, objects, memory, "q", False, withheld={"femur": WITHHELD_AS_TIBIA}
    )
    finding = combine_condition("Fracture", withheld)
    assert finding["outcome"] == "open"
    assert finding["evidence"]["readings"]["femur"]["state"] == "unknown"
    # The covered normal configuration cannot cover the withheld site either.
    coverage = finding["evidence"]["joint_configuration_coverage"]
    assert coverage["eligible_case_ids"] == {"positive": [], "negative": []}


def test_the_unlocated_path_hears_the_real_recall_of_an_empty_reading(monkeypatch):
    # What "exactly as unlocated" is, in production: the real recall of an empty profile.
    declared = question("Fracture")
    spy(monkeypatch, all_normal)
    record = squint_pipeline._recall_question(
        declared,
        bones((3, 0, 0)),
        {"revision": "r1", "cases": []},
        "q",
        False,
        withheld={"femur": WITHHELD_AS_TIBIA},
    )
    femur = record["femur"]
    assert femur["outcome"] == "proposal"
    assert femur["location_status"] == "unavailable"
    assert femur["regions"] == [] and femur["query_origins"] == []
    assert "decision_scope" not in femur
    reading_ = combine_condition("Fracture", record)["evidence"]["readings"]["femur"]
    assert (reading_["state"], reading_["code"]) == (
        "unknown",
        "proposal_without_sourced_trust",
    )


# ---------------------------------------------------------------------------
# bounded reads aimed at withheld tissue are never made
# ---------------------------------------------------------------------------


def _boom(*args, **kwargs):
    raise AssertionError("no reading may be made for withheld tissue")


def test_no_bounded_read_generic_or_named_is_aimed_at_withheld_tissue(
    monkeypatch, tmp_path
):
    from test_squint_orchestration import _located, _study

    from knee.diagnosis.squint_profiles import profile_window

    _uid, study = _study(tmp_path)
    series = study["series"][0]
    coarse = profile_window(series, (0, 1, 0, 1, 0, 1), subject="femur")
    objects = _located(series, coarse)

    # Kept, the same request earns the paired finer reading.
    kept = copy.deepcopy(objects)
    attempted: set = set()
    measured = squint_pipeline._bounded_observation(
        {"object": "femur"}, study, kept, attempted, None, withheld={}
    )
    assert measured["code"] == "measured" and attempted == {"femur"}

    for module, name in (
        (squint_profiles, "refine_window"),
        (squint_profiles, "refine_territory"),
        (squint_residual, "own_outline"),
        (squint_residual, "run_residual"),
    ):
        monkeypatch.setattr(module, name, _boom)
    before = copy.deepcopy(objects)
    attempted = set()
    for request in (
        {"object": "femur"},
        {"subject": "femur", "kind": "bounded_zoom", "question": "Fracture"},
        {"object": "femur", "lens": "native_bone"},
    ):
        observed = squint_pipeline._bounded_observation(
            request,
            study,
            objects,
            attempted,
            None,
            withheld={"femur": WITHHELD_AS_TIBIA},
        )
        assert observed == {
            "code": "object_region_unavailable",
            "request": request,
            "subject": "femur",
            **WITHHELD_AS_TIBIA,
        }
    assert attempted == set()
    assert objects == before


# ---------------------------------------------------------------------------
# the production operation: infer_study with real identity recall
# ---------------------------------------------------------------------------


def test_a_located_femur_recognized_as_tibia_answers_no_femur_question(monkeypatch):
    objects = bones((0, 0, 3))
    original = copy.deepcopy(objects)
    record, calls = run_study(monkeypatch, taught_memory(), objects)

    femur = record["identity_recall"]["objects"]["femur"]
    assert (femur["outcome"], femur["identity"]) == ("identified", "tibia")
    assert record["identity_consumption"] == {
        "femur": {"decision": "withheld", **WITHHELD_AS_TIBIA},
        "fibula": {"decision": "kept", "reason": "silent"},
        "patella": {"decision": "kept", "reason": "silent"},
        "tibia": {"decision": "kept", "reason": "identified", "recognized_as": "tibia"},
    }
    # Every femur question heard no femur tissue in either voice.
    assert reads_of(calls, "femur") and all(b == () for b in reads_of(calls, "femur"))
    assert not any(b.startswith("object/femur/") for b in configuration_banks(calls))
    for question_id in femur_questions():
        evidence = record["questions"][question_id]["objects"]["femur"]
        assert evidence["identity_withheld"] == WITHHELD_AS_TIBIA
        readings = record["questions"][question_id]["finding"]["evidence"]["readings"]
        assert readings["femur"]["state"] == "unknown"
    # Three normal bones and a withheld femur cannot rule fracture out.
    assert record["questions"]["Fracture"]["finding"]["outcome"] == "open"
    # The tissue is not reassigned: the tibia answers from its own reading alone.
    assert set(reads_of(calls, "tibia")) == {(bank(),)}
    # No read was aimed at it; every request for it names why.
    femur_rows = [
        row for row in record["observations"] if row.get("subject") == "femur"
    ]
    assert femur_rows and all(
        row["code"] == "object_region_unavailable"
        and row["reason"] == "identity_recognized_as_other"
        and row["recognized_as"] == "tibia"
        for row in femur_rows
    )
    assert record["work"]["bounded_zoom_runs"] == 0
    # The located record itself is retained, unmodified.
    assert record["objects"] == original


def test_withheld_tissue_gives_the_findings_of_an_unlocated_object(monkeypatch):
    withheld, _ = run_study(monkeypatch, taught_memory(), bones((0, 0, 3)))
    absent = {k: v for k, v in bones((0, 0, 3)).items() if k != "femur"}
    unlocated, _ = run_study(monkeypatch, taught_memory(), absent)
    assert decided(withheld) == decided(unlocated)
    assert withheld["values"] == unlocated["values"]
    for question_id in femur_questions():
        assert (
            without_annotation(withheld["questions"][question_id]["objects"]["femur"])
            == unlocated["questions"][question_id]["objects"]["femur"]
        )


def test_a_femur_recognized_as_itself_keeps_exactly_its_evidence(monkeypatch):
    taught, calls = run_study(monkeypatch, taught_memory(), bones((3, 0, 0)))
    assert taught["identity_consumption"]["femur"] == {
        "decision": "kept",
        "reason": "identified",
        "recognized_as": "femur",
    }
    assert set(reads_of(calls, "femur")) == {(bank(),)}
    assert taught["questions"]["Fracture"]["finding"]["outcome"] == "defeated"
    plain, _ = run_study(monkeypatch, untaught(taught_memory()), bones((3, 0, 0)))
    assert taught["questions"] == plain["questions"]
    assert taught["values"] == plain["values"]
    assert taught["observations"] == plain["observations"]


def test_a_femur_spoken_against_by_its_negative_cases_alone_is_withheld(monkeypatch):
    record, calls = run_study(
        monkeypatch, taught_memory(femur_negative=True), bones((0, 2, 0))
    )
    femur = record["identity_recall"]["objects"]["femur"]
    assert femur["opposed_identities"] == ["femur"]
    assert femur["speaking_identities"] == [] and femur["identity"] is None
    assert record["identity_consumption"]["femur"] == {
        "decision": "withheld",
        "reason": "identity_opposed_by_negative_cases",
    }
    assert all(b == () for b in reads_of(calls, "femur"))
    assert record["questions"]["Fracture"]["finding"]["outcome"] == "open"
    evidence = record["questions"]["Fracture"]["objects"]["femur"]
    assert evidence["identity_withheld"] == {
        "reason": "identity_opposed_by_negative_cases"
    }


def test_a_femur_spoken_for_and_against_stays_placed_and_flagged(monkeypatch):
    record, calls = run_study(
        monkeypatch, taught_memory(femur_negative=True), bones((1, 2, 0))
    )
    femur = record["identity_recall"]["objects"]["femur"]
    assert (femur["outcome"], femur["reason"]) == (
        "unresolved_conflict",
        "identity_spoken_for_and_against",
    )
    assert record["identity_consumption"]["femur"] == {
        "decision": "kept",
        "reason": "unresolved_conflict",
    }
    # An unresolved identity is no clinical absence: its tissue still answers.
    assert set(reads_of(calls, "femur")) == {(bank(),)}
    assert record["questions"]["Fracture"]["finding"]["outcome"] == "defeated"
    assert (
        "identity_withheld" not in record["questions"]["Fracture"]["objects"]["femur"]
    )


def test_a_sanity_blocked_femur_stays_placed_and_flagged(monkeypatch):
    objects = bones((3, 0, 0))
    objects["femur"] = located("femur", (3, 0, 0), sanity="contradicted")
    record, calls = run_study(monkeypatch, taught_memory(), objects)
    assert (
        record["identity_recall"]["objects"]["femur"]["outcome"] == "blocked_by_sanity"
    )
    assert record["identity_consumption"]["femur"] == {
        "decision": "kept",
        "reason": "blocked_by_sanity",
    }
    assert set(reads_of(calls, "femur")) == {(bank(),)}


# ---------------------------------------------------------------------------
# a memory without identity teaching changes nothing
# ---------------------------------------------------------------------------

#: sha256 of the study record below, computed by the code before identity was wired into
#: the condition consumer (1804e00), with timing, RSS and the new identity_consumption
#: key set aside.
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
    """A femur shaped like the tibia seed, which taught memory would withhold."""
    return {
        **bones((0, 0, 3)),
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
    assert record["identity_consumption"] == {
        name: {"decision": "kept", "reason": "unreviewed_candidate_memory"}
        for name in sorted(objects)
    }
    assert _record_digest(record) == NO_TEACHING_RECORD_SHA256
