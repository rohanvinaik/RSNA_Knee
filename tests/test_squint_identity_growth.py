"""Two-sign intent of signed identity growth from one frozen parent.

CLASSICAL_AI_BUILD_DESIGN §§7, 7.1-7.2 and the OpenSpec change
``complete-signed-bootstrap-loop``: answering and admitting are different
decisions; an anatomical pass is a location law check; a round scores against
its frozen parent alone; the child keeps every signed record; a candidate's
whole study leaves its comparison across every record kind.

Rohan, 2026-10-21: «Growth stores the warranted object presentation with that context
and lineage.» A candidate's identity is warranted in its context, what the inference
run's structure established about it, with a high recognition match: a bone its
structural reader established whose own cases rise above every identity but the
reader's other bones (which it tells apart by arrangement, found or not), or an object
the anatomy map placed whose own cases speak against the alternatives that placement
leaves open; never a placement by the prior alone. The reader's recorded arrangement is
its affirmative support. «Positive and negative cases are expertise, not decorative
annotations»: a negative case whose reason holds for the candidate's asserted region
opposes it; one that speaks only with the surroundings, or asserts an alternative
structure removed, is recorded and changes nothing. Resemblance to another object never
blocks. A reversed law check blocks as an ``identity_question``. Each test pins one
meaning in both signs, through direct calls to the growth API, the identity reader and
the CLI.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from knee.diagnosis.squint_anatomy_locator import BONES
from knee.diagnosis.squint_bootstrap import (
    CALLS_SCHEMA,
    build_review,
    publish_seed_memory,
)
from knee.diagnosis.squint_identity import (
    CONDITIONING,
    CONTEXT_SCHEMA,
    IDENTITY_CASES_SCHEMA,
    IDENTITY_CONSUMPTION_SCHEMA,
    JOINT_SCALE,
    MAP_RELATION,
    PRIOR_ONLY,
    PROPOSED_PLACES,
    RECALL_CONTEXT_SCHEMA,
    RESOLVED_SUPPORT,
    SANITY_SCHEMA,
    STRUCTURAL_READER,
    TEACHING_SCHEMA,
    prepare_identity,
    recall_identity,
)
from knee.diagnosis.squint_identity_growth import (
    CHILD_DIRECTORY,
    DECISIONS_FILE,
    DECISIONS_SCHEMA,
    GROWTH_SCHEMA,
    READER,
    RECOGNITION_KIND,
    IdentityGrowthError,
    admission_decision,
    admission_from_recall,
    admission_scope,
    candidates_from_memory,
    exclusion_studies,
    grow_identity_memory,
    harvest_candidates,
    location_support,
    read_inference_records,
    record_sha256,
    represented_objects,
)
from knee.diagnosis.squint_locator import prepare_recall
from knee.diagnosis.squint_memory import (
    SCHEMA,
    _full_profile_from_validated_case,
    _json_sha256,
    full_profile_from_case,
    hydrate_full_profiles,
    load_memory_snapshot,
    save_memory,
)
from knee.diagnosis.squint_memory_view import memory_view
from knee.json_store import dump_json_atomic
from knee.study.tables import LABELS
from tests.test_squint_bootstrap import _product

ROOT = Path(__file__).resolve().parents[1]
SAG = ["Sagittal", "0", "0"]
COR = ["Coronal", "0", "0"]
PROCEDURE = "knee.squint-profile/scan-tercile-v1"
WINDOW = [0, 1, 0, 2, 0, 2]
INFERENCE_REVISION = "inference-memory-r1"
DECISION_KEYS = sorted(
    [
        "candidate_id",
        "study_uid",
        "subject",
        "state",
        "reason",
        "recognized_identity",
        "views",
        "support",
        "regions",
        "source",
        "identity_context",
        "identity_question",
        "identity_scale",
    ]
)
#: The structural reader's own record of how it named a bone, as infer_study copies it
#: from the anchor territory's provenance.
ARRANGEMENT = {
    "establishes": "bone_identity_by_the_readers_observed_arrangement",
    "series_uid": "series-sag",
    "window": list(WINDOW),
    "producer": "knee.diagnosis.squint_anchors",
    "derivation": "middle_slice_named_by_the_established_rule",
    "rule": "knee.objects.assignments.assign_plane, read with its partner (with_partner)",
    "middle_slice_code": "identified",
    "partner": "agree",
    "cross_view_checks": [],
}


def bank(view: list[str], role: str = "object", scale: str = "10mm") -> str:
    return (
        "squint/v2/view="
        + json.dumps(view, separators=(",", ":"))
        + f"/role={role}/metric=signal/direction=d/scale={scale}"
    )


def profile(subject: str, by_view, ring=(), fine=()) -> dict:
    """A profile's object tiles at 10 mm, its ``ring`` and its ``fine`` 2 mm tiles."""
    banks = {bank(view): list(counts) for view, counts in by_view}
    banks.update({bank(view, "context"): list(counts) for view, counts in ring})
    banks.update({bank(view, scale="2mm"): list(counts) for view, counts in fine})
    return {
        "schema": "knee.squint-profile/v1",
        "subject": subject,
        "banks": banks,
        "source": {"procedure": PROCEDURE},
    }


def sanity(subject: str, status: str, *results: str) -> dict:
    """A knee.object-anatomical-sanity/v1 record shaped as the locator writes it."""
    checks = [
        {
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
        for result in results
    ]
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
                "checks": checks,
                "series_uid": "series-sag",
            }
        ],
    }


def plausible(subject: str) -> dict:
    return sanity(subject, "plausible", "supported_strictly_after")


def unknown(subject: str) -> dict:
    return sanity(subject, "unknown", "unknown")


def contradicted(subject: str) -> dict:
    return sanity(subject, "contradicted", "reversed_strictly_after")


def identity_context(
    subject: str,
    basis: str = STRUCTURAL_READER,
    open_alternatives=(),
    contradictions=(),
    *,
    arrangement: bool = True,
) -> dict:
    """What an inference run's structure established about one located object."""
    structural = basis == STRUCTURAL_READER
    observations: dict = {"reason": "fixture", "record": f"objects/{subject}/evidence"}
    if structural and arrangement:
        observations["arrangement"] = [dict(ARRANGEMENT)]
    return {
        "schema": CONTEXT_SCHEMA,
        "subject": subject,
        "basis": basis,
        "conditioning": CONDITIONING[basis],
        "support": RESOLVED_SUPPORT if structural else PROPOSED_PLACES,
        "open_alternatives": sorted(open_alternatives),
        "removed_by_structure": sorted(set(BONES) - {subject}) if structural else [],
        "contradictions": list(contradictions),
        "supporting_observations": observations,
    }


def established(subject: str, **options) -> dict:
    return identity_context(subject, STRUCTURAL_READER, **options)


def placed(subject: str, *alternatives: str) -> dict:
    return identity_context(subject, MAP_RELATION, alternatives)


def located(subject: str, by_view, anatomy, ring=(), fine=()) -> dict:
    return {
        "status": "proposal",
        "profile": profile(subject, by_view, ring, fine),
        "regions": [
            {
                "series_uid": "series-sag",
                "view": {
                    "orientation": "Sagittal",
                    "fluid_sensitive": "0",
                    "fat_suppression": "0",
                },
                "window": list(WINDOW),
            }
        ],
        "sanity": anatomy,
        "evidence": {"source": "fixture"},
    }


def study_record(
    uid: str,
    objects: dict,
    revision: str = INFERENCE_REVISION,
    contexts: dict | None = None,
) -> dict:
    """A knee.squint-study/v1 record as infer_study writes it, abridged.

    ``contexts`` are recorded in its ``identity_consumption``, where infer_study keeps
    each located object's identity context.
    """
    record = {
        "schema": "knee.squint-study/v1",
        "study_uid": uid,
        "memory_revision": revision,
        "study_status": "examined",
        "objects": objects,
        "identity_recall": {"outcome": "examined", "objects": {}},
        "questions": {},
        "values": {},
    }
    if contexts is not None:
        record["identity_consumption"] = {
            "schema": IDENTITY_CONSUMPTION_SCHEMA,
            "not_read_as_subject": [],
            "objects": {
                subject: {
                    "answers_questions_as": subject,
                    "identity_basis": (contexts.get(subject) or {}).get("basis"),
                    "recall_outcome": "fixture",
                    "identity_context": contexts.get(subject),
                    "identity_question": None,
                }
                for subject in objects
            },
        }
    return record


def candidate(
    uid: str, subject: str, by_view, anatomy, context, ring=(), fine=()
) -> dict:
    [item] = harvest_candidates(
        [
            study_record(
                uid,
                {subject: located(subject, by_view, anatomy, ring, fine)},
                contexts={subject: context},
            )
        ]
    )
    return item


def _record(
    case_id: str, subject: str, study_uid: str, by_view, ring=(), fine=()
) -> dict:
    return {
        "case_id": case_id,
        "study_uid": study_uid,
        "subject": subject,
        "condition_calls": {},
        "profile": profile(subject, by_view, ring, fine),
        "regions": [],
    }


def identity_memory(seeds, negatives=(), revision: str = "parent-r1") -> dict:
    """A valid squint memory of confirmed seeds and scoped ordinary negative cases.

    ``seeds`` are (case_id, subject, study_uid, by_view[, ring[, fine]]); ``negatives``
    add the views their reject asserted (and optionally a ring and fine 2 mm tiles).
    """
    cases = [_record(*seed) for seed in seeds]
    calls = [
        {
            "candidate_id": case["case_id"],
            "call": "confirm",
            "notes": "n",
            "reader": "fixture reviewer",
        }
        for case in cases
    ]
    teaching = {
        "schema": TEACHING_SCHEMA,
        "reader": "fixture reviewer",
        "confirmed_case_ids": [case["case_id"] for case in cases],
        "calls": calls,
    }
    memory = {
        "schema": SCHEMA,
        "revision": revision,
        "questions": list(LABELS),
        "cases": cases,
        "object_identity_teaching": teaching,
    }
    if negatives:
        records = []
        teaching["negative_case_ids"] = []
        teaching["negative_views"] = {}
        for case_id, subject, study_uid, by_view, views, *rest in negatives:
            records.append(_record(case_id, subject, study_uid, by_view, *rest))
            teaching["negative_case_ids"].append(case_id)
            teaching["negative_views"][case_id] = [list(view) for view in views]
            calls.append(
                {
                    "candidate_id": case_id,
                    "call": "reject",
                    "notes": "n",
                    "reader": "fixture reviewer",
                    "views": [list(view) for view in views],
                }
            )
        memory["object_identity_cases"] = {
            "schema": IDENTITY_CASES_SCHEMA,
            "cases": records,
        }
    return memory


def saved(tmp_path: Path, name: str, memory: dict):
    save_memory(memory, tmp_path / name)
    return load_memory_snapshot(tmp_path / name)


def decide(item: dict, memory: dict) -> dict:
    return admission_decision(item, memory)["decision"]


# A femur and a tibia seed that resemble each other: each one's envelope is 4/5.
ROUND_SEEDS = (
    ("a1", "femur", "sa", [(SAG, (3, 0, 0))]),
    ("t1", "tibia", "st", [(SAG, (2, 1, 0))]),
)
# A femur and a patella seed that share nothing: both envelopes are 0.
TWO_SEEDS = (
    ("a1", "femur", "sa", [(SAG, (3, 0, 0))]),
    ("b1", "patella", "sb", [(SAG, (0, 0, 3))]),
)
# A muscle seed sharing nothing with the femur seed: the identity a structural bone's
# own cases are calibrated against once the reader's other bones are set aside.
MUSCLE = ("m1", "medial_gastrocnemius", "sm", [(SAG, (0, 3, 0))])
# A reviewer rejected this sagittal support as femur; study "sn" holds nothing else.
NEGATIVE = ("n1", "femur", "sn", [(SAG, (1, 2, 0))], [SAG])
# Seeds and a "not femur" reject read at both scales (finer tiles, so larger 2 mm
# counts). At 10 mm the reject (2,1,0) still mixes bone with the soft tissue it named and
# sits close to the femur seed (3,1,0); at 2 mm it is that soft tissue (0,15,0), and the
# femur seed is bone (15,0,0).
JOINT_SEEDS = (
    ("a1", "femur", "sa", [(SAG, (3, 1, 0))], (), [(SAG, (15, 0, 0))]),
    ("t1", "tibia", "st", [(SAG, (0, 0, 3))], (), [(SAG, (0, 0, 15))]),
)
JOINT_MUSCLE = (
    "m1",
    "medial_gastrocnemius",
    "sm",
    [(SAG, (0, 1, 3))],
    (),
    [(SAG, (0, 0, 15))],
)
JOINT_NEGATIVE = (
    "n1",
    "femur",
    "sn",
    [(SAG, (2, 1, 0))],
    [SAG],
    (),
    [(SAG, (0, 15, 0))],
)
#: A candidate that reads like the reject at 10 mm, and its own 2 mm tiles either way.
LIKE_THE_REJECT = [(SAG, (2, 1, 0))]
BONE_2MM = [(SAG, (15, 0, 0))]
SOFT_TISSUE_2MM = [(SAG, (0, 15, 0))]


# ------------------------------------------------------------- the decision


def test_a_placement_its_own_cases_support_is_admitted_at_the_views_that_spoke():
    memory = identity_memory(ROUND_SEEDS)
    item = candidate(
        "sx", "femur", [(SAG, (4, 0, 1))], plausible("femur"), placed("femur", "tibia")
    )
    scored = admission_decision(item, memory)
    decision = scored["decision"]
    assert sorted(decision) == DECISION_KEYS
    assert (decision["state"], decision["reason"]) == (
        "admitted",
        "appearance_supports_with_location_support",
    )
    # Nothing contested it at the squint scale, so the squint-scale recall decided.
    assert decision["identity_scale"] == "10mm"
    assert scored["resolved_recall"] is None
    assert decision["recognized_identity"] == "femur"
    assert decision["views"] == [SAG]
    assert decision["identity_context"] == placed("femur", "tibia")
    assert decision["identity_question"] is None
    [support] = decision["support"]
    assert support["establishes"] == "location_only"
    assert (support["rule_id"], support["axis"], support["result"]) == (
        "authored:femur:superior_to:tibia",
        "z",
        "supported_strictly_after",
    )
    assert support["candidate_interval"] == [40.0, 80.0]
    assert support["target_interval"] == [0.0, 30.0]
    recall = scored["recall"]
    assert (recall["schema"], recall["outcome"]) == (
        RECALL_CONTEXT_SCHEMA,
        "appearance_supports",
    )
    assert recall["speaking_case_ids"] == ["a1"]
    assert scored["excluded_study_uid"] is None
    # Its own case does not reach past the placement's open alternative: a proposal.
    quiet = candidate(
        "sw", "femur", [(SAG, (4, 0, 2))], plausible("femur"), placed("femur", "tibia")
    )
    decision = decide(quiet, memory)
    assert (decision["state"], decision["reason"]) == ("proposal", "appearance_silent")
    assert decision["recognized_identity"] is None and decision["views"] == []


def test_a_structural_bone_must_rise_above_every_identity_but_the_readers_bones():
    item = candidate(
        "sw",
        "femur",
        [(SAG, (4, 0, 2)), (COR, (1, 1, 1))],
        plausible("femur"),
        established("femur"),
    )
    # The tibia is the reader's own bone: its cases never set the femur's bar, and the
    # muscle's do. The femur's case rises above the muscle's: a high recognition match.
    memory = identity_memory((*ROUND_SEEDS, MUSCLE))
    scored = admission_decision(item, memory)
    recall = scored["recall"]
    assert (recall["outcome"], recall["appearance"]) == (
        "established_by_structure",
        "supports",
    )
    [row] = recall["cases"]
    assert row["envelope"]["opposing_identities"] == ["medial_gastrocnemius"]
    decision = scored["decision"]
    assert (decision["state"], decision["reason"]) == (
        "admitted",
        "established_by_structure_with_the_readers_arrangement",
    )
    assert decision["recognized_identity"] == "femur"
    # Its scope is where the recognition match spoke, the sagittal view.
    assert decision["views"] == [SAG]
    assert decision["support"][0] == ARRANGEMENT
    # Placed by the map with the tibia open, the same case cannot beat the tibia's.
    as_placement = {**item, "identity_context": placed("femur", "tibia")}
    assert decide(as_placement, memory)["reason"] == "appearance_silent"
    # Structure alone never admits: with nothing but the reader's bones to compare
    # against, the recognition match is uncalibrated.
    alone = decide(item, identity_memory(ROUND_SEEDS))
    assert (alone["state"], alone["reason"]) == (
        "proposal",
        "structural_appearance_uncalibrated",
    )


def test_the_readers_arrangement_is_the_support_and_a_placement_needs_a_recorded_pass():
    with_muscle = identity_memory((*ROUND_SEEDS, MUSCLE))
    for anatomy in (unknown("femur"), None):
        # An unavailable law check does not erase the reader's own observation.
        reader = decide(
            candidate("sx", "femur", [(SAG, (4, 0, 1))], anatomy, established("femur")),
            with_muscle,
        )
        assert (reader["state"], reader["support"]) == ("admitted", [ARRANGEMENT])
        # Without a recorded arrangement it has no affirmative support.
        bare = decide(
            candidate(
                "sx",
                "femur",
                [(SAG, (4, 0, 1))],
                anatomy,
                established("femur", arrangement=False),
            ),
            with_muscle,
        )
        assert (bare["state"], bare["reason"]) == ("proposal", "anatomy_unknown")
        assert bare["recognized_identity"] == "femur"
        # A placement's identity is warranted, but unknown-only anatomy keeps it a
        # proposal.
        scored = admission_decision(
            candidate(
                "sx", "femur", [(SAG, (4, 0, 1))], anatomy, placed("femur", "tibia")
            ),
            identity_memory(ROUND_SEEDS),
        )
        assert scored["recall"]["outcome"] == "appearance_supports"
        decision = scored["decision"]
        assert (decision["state"], decision["reason"]) == (
            "proposal",
            "anatomy_unknown",
        )
        assert decision["recognized_identity"] == "femur"
        assert decision["views"] == [] and decision["support"] == []
    # A bare plausible status that records no supporting check establishes nothing.
    bare = candidate(
        "sx",
        "femur",
        [(SAG, (4, 0, 1))],
        sanity("femur", "plausible"),
        placed("femur", "tibia"),
    )
    decision = decide(bare, identity_memory(ROUND_SEEDS))
    assert (decision["state"], decision["reason"]) == (
        "proposal",
        "anatomy_support_unrecorded",
    )


def test_admission_needs_a_plausible_status_as_well_as_a_recorded_pass():
    memory = identity_memory(ROUND_SEEDS)
    passed = sanity("femur", "plausible", "supported_strictly_after")
    decision = decide(
        candidate("sx", "femur", [(SAG, (4, 0, 1))], passed, placed("femur", "tibia")),
        memory,
    )
    assert decision["state"] == "admitted"
    inconsistent = sanity("femur", "unknown", "supported_strictly_after")
    decision = decide(
        candidate(
            "sx", "femur", [(SAG, (4, 0, 1))], inconsistent, placed("femur", "tibia")
        ),
        memory,
    )
    assert (decision["state"], decision["reason"]) == ("proposal", "anatomy_unknown")
    assert [row["result"] for row in decision["support"]] == [
        "supported_strictly_after"
    ]


def test_a_reversed_check_is_an_identity_question_that_blocks_and_a_supported_one_admits():
    """Reachable as inference records it: a bone whose own anchor the locator set aside
    for a reversed relation, placed from the other anchors, carries that contradiction
    in its context. A caller-supplied sanity (a memory candidate's) can carry one on the
    candidate's own window; the locator's own windows exclude contradicted ones."""
    memory = identity_memory(ROUND_SEEDS)
    admitted = decide(
        candidate(
            "sx",
            "femur",
            [(SAG, (4, 0, 1))],
            plausible("femur"),
            placed("femur", "tibia"),
        ),
        memory,
    )
    assert admitted["state"] == "admitted"
    assert admitted["identity_question"] is None
    blocked = decide(
        candidate(
            "sx",
            "femur",
            [(SAG, (4, 0, 1))],
            contradicted("femur"),
            placed("femur", "tibia"),
        ),
        memory,
    )
    assert (blocked["state"], blocked["reason"]) == ("blocked", "identity_question")
    question = blocked["identity_question"]
    assert (question["status"], question["revisable"]) == ("open", True)
    [check] = question["location_checks"]
    assert (check["rule_id"], check["result"]) == (
        "authored:femur:superior_to:tibia",
        "reversed_strictly_after",
    )
    assert (check["candidate_interval"], check["target_interval"]) == (
        [40.0, 80.0],
        [0.0, 30.0],
    )
    # One reversed check is enough, and the pass beside it stays location support.
    mixed = sanity(
        "femur", "plausible", "supported_strictly_after", "reversed_strictly_after"
    )
    decision = decide(
        candidate("sx", "femur", [(SAG, (4, 0, 1))], mixed, placed("femur", "tibia")),
        memory,
    )
    assert (decision["state"], decision["reason"]) == ("blocked", "identity_question")
    assert [row["result"] for row in decision["support"]] == [
        "supported_strictly_after"
    ]
    # The contradiction a set-aside anchor leaves in the context blocks as well.
    set_aside = identity_context(
        "femur",
        MAP_RELATION,
        ["tibia"],
        contradictions=[
            {
                "scope": "set_aside_structural_anchor",
                "result": "reversed_strictly_after",
            }
        ],
    )
    decision = decide(
        candidate("sx", "femur", [(SAG, (4, 0, 1))], plausible("femur"), set_aside),
        memory,
    )
    assert (decision["state"], decision["reason"]) == ("blocked", "identity_question")
    assert (
        decision["identity_question"]["context_contradictions"]
        == (set_aside["contradictions"])
    )


def test_a_pass_is_location_support_for_its_own_subject_only():
    tibia_pass = plausible("tibia")
    assert location_support(tibia_pass, "femur")["support"] == []
    assert len(location_support(tibia_pass, "tibia")["support"]) == 1
    asserted = {**plausible("femur"), "identity_assertion": "femur"}
    assert location_support(asserted, "femur")["status"] is None
    decision = decide(
        candidate(
            "sx", "femur", [(SAG, (4, 0, 1))], tibia_pass, placed("femur", "tibia")
        ),
        identity_memory(ROUND_SEEDS),
    )
    assert (decision["state"], decision["reason"]) == (
        "proposal",
        "anatomy_support_unrecorded",
    )


def test_a_prior_only_placement_never_auto_admits_and_a_missing_context_never_does():
    memory = identity_memory(TWO_SEEDS)
    femur_like = [(SAG, (3, 0, 0))]
    # Unconditioned, the same presentation is recognized as femur above its envelope.
    assert recall_identity(profile("femur", femur_like), memory)["identity"] == "femur"
    prior = decide(
        candidate(
            "sx",
            "femur",
            femur_like,
            plausible("femur"),
            identity_context("femur", PRIOR_ONLY),
        ),
        memory,
    )
    assert (prior["state"], prior["reason"]) == (
        "proposal",
        "identity_basis_prior_only",
    )
    assert prior["recognized_identity"] is None
    [bare] = harvest_candidates(
        [
            study_record(
                "sx", {"femur": located("femur", femur_like, plausible("femur"))}
            )
        ]
    )
    assert bare["identity_context"] is None
    missing = decide(bare, memory)
    assert (missing["state"], missing["reason"]) == (
        "proposal",
        "identity_context_unavailable",
    )
    warranted = decide(
        candidate(
            "sx", "femur", femur_like, plausible("femur"), placed("femur", "patella")
        ),
        memory,
    )
    assert warranted["state"] == "admitted"


def test_resembling_another_identity_never_renames_or_blocks_the_candidate():
    memory = identity_memory((*TWO_SEEDS, MUSCLE))
    both = [(SAG, (3, 0, 3))]
    # Unconditioned, this reading resembles the femur and the patella seeds alike: the
    # withdrawn authority read that as a conflict between two bones.
    assert recall_identity(profile("femur", both), memory)["outcome"] == (
        "unresolved_conflict"
    )
    scored = admission_decision(
        candidate("sp", "femur", both, plausible("femur"), established("femur")), memory
    )
    assert [row["identity"] for row in scored["recall"]["also_resembles"]][:1] == [
        "patella"
    ]
    decision = scored["decision"]
    assert (decision["state"], decision["recognized_identity"]) == ("admitted", "femur")
    # A reading recognized as the patella, unconditioned, is never renamed and never a
    # conflict: the femur's own cases do not speak, so it stays a proposal.
    patella_like = [(SAG, (0, 0, 3))]
    assert recall_identity(profile("femur", patella_like), memory)["identity"] == (
        "patella"
    )
    scored = admission_decision(
        candidate(
            "sp", "femur", patella_like, plausible("femur"), established("femur")
        ),
        memory,
    )
    assert scored["recall"]["identity"] == "femur"
    decision = scored["decision"]
    assert (decision["state"], decision["reason"]) == (
        "proposal",
        "structural_appearance_silent",
    )
    own = decide(
        candidate(
            "sp",
            "patella",
            patella_like,
            plausible("patella"),
            established("patella"),
        ),
        memory,
    )
    assert (own["state"], own["recognized_identity"]) == ("admitted", "patella")


def test_a_squint_scale_negative_opens_the_question_and_the_finer_look_decides():
    item = candidate(
        "sr",
        "femur",
        [(SAG, (1, 2, 0))],
        plausible("femur"),
        placed("femur", "patella"),
    )
    without = admission_decision(item, identity_memory(TWO_SEEDS))
    assert (without["decision"]["state"], without["decision"]["views"]) == (
        "admitted",
        [SAG],
    )
    # The reviewer's "not femur" support, over the same asserted region: its reason
    # holds at 10 mm. That opens the identity question; it decides nothing.
    scored = admission_decision(item, identity_memory(TWO_SEEDS, [NEGATIVE]))
    [negative] = scored["recall"]["negative_cases"]
    assert (negative["case_id"], negative["applies"], negative["reason"]) == (
        "n1",
        True,
        "speaks_over_the_asserted_region",
    )
    assert scored["recall"]["outcome"] == "signed_conflict"
    assert scored["recall"]["identity"] == "femur"
    assert scored["resolved_recall"] is None
    decision = scored["decision"]
    assert (decision["state"], decision["reason"], decision["identity_scale"]) == (
        "proposal",
        "squint_contest_unresolved_no_finer_reading",
        "10mm",
    )
    assert decision["recognized_identity"] is None and decision["views"] == []
    # Read at both scales: placed with nothing left open, so its own cases are
    # uncalibrated and the reject opposes it at 10 mm.
    memory = identity_memory(JOINT_SEEDS, [JOINT_NEGATIVE])
    alone = placed("femur")
    opposed = decide(
        candidate(
            "sq",
            "femur",
            LIKE_THE_REJECT,
            plausible("femur"),
            alone,
            fine=SOFT_TISSUE_2MM,
        ),
        memory,
    )
    # Still the soft tissue with its 2 mm tiles: opposed, never renamed.
    assert (opposed["state"], opposed["reason"], opposed["identity_scale"]) == (
        "opposed",
        "applicable_negative_case_speaks",
        JOINT_SCALE,
    )
    assert opposed["recognized_identity"] is None
    # Bone with its 2 mm tiles: the reject was squint-scale resemblance only, and
    # with nothing open to calibrate against, the placement alone stays a proposal.
    settled = decide(
        candidate(
            "sq", "femur", LIKE_THE_REJECT, plausible("femur"), alone, fine=BONE_2MM
        ),
        memory,
    )
    assert (settled["state"], settled["reason"], settled["identity_scale"]) == (
        "proposal",
        "placement_only",
        JOINT_SCALE,
    )


def test_admission_waits_for_the_identity_settled_after_the_finer_look(tmp_path: Path):
    memory = identity_memory(JOINT_SEEDS, [JOINT_NEGATIVE])
    placement = placed("femur", "tibia")

    def scored(fine=(), context=placement):
        return admission_decision(
            candidate(
                "sx", "femur", LIKE_THE_REJECT, plausible("femur"), context, fine=fine
            ),
            memory,
        )

    # At 10 mm the femur's own case and the reject both speak: an open question.
    squint_only = scored()
    assert squint_only["recall"]["outcome"] == "signed_conflict"
    assert squint_only["recall"]["applicable_negative_case_ids"] == ["n1"]
    decision = squint_only["decision"]
    assert (decision["state"], decision["reason"]) == (
        "proposal",
        "squint_contest_unresolved_no_finer_reading",
    )
    # Its own 2 mm tiles are bone: one comparison over both scales settles it, and the
    # identity is admitted on that comparison, its scope that comparison's.
    settled = scored(BONE_2MM)
    joint = settled["resolved_recall"]
    assert (joint["scale"], joint["squint_scale_negatives"]) == (
        JOINT_SCALE,
        {"n1": "compared_not_applying"},
    )
    [own] = [row for row in joint["cases"] if row["case_id"] == "a1"]
    assert sorted(own["common_speaking_banks"]) == sorted(
        [bank(SAG), bank(SAG, scale="2mm")]
    )
    decision = settled["decision"]
    assert (decision["state"], decision["reason"], decision["identity_scale"]) == (
        "admitted",
        "appearance_supports_with_location_support",
        JOINT_SCALE,
    )
    assert decision["views"] == [SAG]
    # Its own 2 mm tiles are the soft tissue the reviewer named: still contested.
    decision = scored(SOFT_TISSUE_2MM)["decision"]
    assert (decision["state"], decision["identity_scale"]) == ("conflict", JOINT_SCALE)
    # A finer reading of another view cannot include the sagittal reject: unsettled.
    decision = scored([(COR, (15, 0, 0))])["decision"]
    assert (decision["state"], decision["reason"]) == (
        "proposal",
        "squint_contest_unresolved_not_compared_with_finer_reading",
    )
    # A bone the reader established whose disagreement stands after the look: the
    # structure's word carries diagnosis, but admission needs it settled.
    muscled = identity_memory((*JOINT_SEEDS, JOINT_MUSCLE), [JOINT_NEGATIVE])
    decision = admission_decision(
        candidate(
            "sx",
            "femur",
            LIKE_THE_REJECT,
            plausible("femur"),
            established("femur"),
            fine=SOFT_TISSUE_2MM,
        ),
        muscled,
    )["decision"]
    assert (decision["state"], decision["identity_scale"]) == ("conflict", JOINT_SCALE)
    # A round admits on the joint comparison and its lineage says so.
    parent = saved(tmp_path, "parent", memory)
    item = candidate(
        "sx", "femur", LIKE_THE_REJECT, plausible("femur"), placement, fine=BONE_2MM
    )
    receipt = grow_identity_memory(parent, [item], tmp_path / "grown")
    assert receipt["admitted_case_ids"] == [item["case_id"]]
    child = load_memory_snapshot(tmp_path / "grown" / CHILD_DIRECTORY).memory
    [case] = [case for case in child["cases"] if case["case_id"] == item["case_id"]]
    lineage = case["identity_growth"]
    assert lineage["decision"]["identity_scale"] == JOINT_SCALE
    assert lineage["speaking_case_ids"] == ["a1"]
    assert (
        lineage["preparation_source_pin"]
        == (prepare_identity(parent.memory, scale=JOINT_SCALE)["source_pin"])
    )


def test_a_negative_case_heard_only_through_the_surroundings_changes_nothing():
    # A "not femur" support whose ring resembles this candidate's ring, while its own
    # asserted region does not resemble the candidate's: surroundings, not occupancy.
    seeds = (
        ("a1", "femur", "sa", [(SAG, (3, 0, 0))], [(SAG, (3, 0, 0))]),
        ("b1", "patella", "sb", [(SAG, (0, 0, 3))], [(SAG, (0, 0, 3))]),
    )
    surroundings = ("n2", "femur", "sn", [(SAG, (0, 3, 0))], [SAG], [(SAG, (1, 2, 0))])
    memory = identity_memory(seeds, [surroundings])
    item = candidate(
        "sr",
        "femur",
        [(SAG, (3, 0, 0))],
        plausible("femur"),
        placed("femur", "patella"),
        ring=[(SAG, (1, 2, 0))],
    )
    scored = admission_decision(item, memory)
    [negative] = scored["recall"]["negative_cases"]
    assert (negative["applies"], negative["reason"]) == (False, "surroundings_only")
    assert negative["with_the_surroundings"]["speaks"] is True
    assert negative["over_the_asserted_region"]["speaks"] is False
    assert scored["decision"]["state"] == "admitted"
    # The same negative over the candidate's own asserted region applies: at 10 mm that
    # opens the identity question, and with no finer reading it stays a proposal.
    occupying = candidate(
        "sr",
        "femur",
        [(SAG, (0, 3, 0))],
        plausible("femur"),
        placed("femur", "patella"),
        ring=[(SAG, (1, 2, 0))],
    )
    scored = admission_decision(occupying, memory)
    assert scored["recall"]["applicable_negative_case_ids"] == ["n2"]
    assert (scored["decision"]["state"], scored["decision"]["reason"]) == (
        "proposal",
        "squint_contest_unresolved_no_finer_reading",
    )


def test_a_study_known_only_through_a_negative_record_is_excluded():
    memory = identity_memory(TWO_SEEDS, [NEGATIVE])
    # Reading studies from ``cases`` alone, as the prototype did, misses "sn".
    assert {case["study_uid"] for case in memory["cases"]} == {"sa", "sb"}
    assert exclusion_studies(memory) == {"sa", "sb", "sn"}
    item = candidate(
        "sn", "tibia", [(SAG, (1, 2, 0))], plausible("tibia"), established("tibia")
    )
    scored = admission_decision(item, memory)
    assert scored["excluded_study_uid"] == "sn"
    assert scored["recall"]["negative_cases_compared"] == 0
    assert scored["recall"]["negative_cases"] == []
    assert prepare_identity(memory, exclude_study_uid="sn")["negative_case_count"] == 0
    # Unexcluded, the study's own negative would be heard in its candidate's
    # comparison: a femur negative, so of another identity than this tibia's.
    leaked = recall_identity(
        item["profile"], memory, sanity=item["sanity"], context=established("tibia")
    )
    [row] = leaked["negative_cases"]
    assert (row["case_id"], row["applies"], row["reason"]) == (
        "n1",
        False,
        "concerns_another_identity",
    )


def test_an_object_the_parent_already_holds_in_either_sign_is_a_duplicate():
    memory = identity_memory(TWO_SEEDS, [NEGATIVE])
    assert represented_objects(memory)["objects"] == {
        ("sa", "femur"),
        ("sb", "patella"),
        ("sn", "femur"),
    }
    for uid in ("sa", "sn"):
        decision = decide(
            candidate(
                uid,
                "femur",
                [(SAG, (3, 0, 0))],
                plausible("femur"),
                established("femur"),
            ),
            memory,
        )
        assert (decision["state"], decision["reason"]) == (
            "duplicate",
            "object_already_in_parent",
        )
        assert decision["identity_context"] == established("femur")
    other = decide(
        candidate(
            "sa", "tibia", [(SAG, (0, 0, 3))], plausible("tibia"), established("tibia")
        ),
        memory,
    )
    assert other["state"] != "duplicate"
    same_id = {
        **candidate(
            "sz", "tibia", [(SAG, (0, 0, 3))], plausible("tibia"), established("tibia")
        ),
        "case_id": "a1",
    }
    decision = decide(same_id, memory)
    assert (decision["state"], decision["reason"]) == (
        "duplicate",
        "case_id_already_in_parent",
    )


def _row(identity: str, speaks: bool, *views: list[str]) -> dict:
    return {
        "identity": identity,
        "speaks": speaks,
        "common_speaking_banks": [bank(view) for view in views],
    }


def _in_context(identity: str, basis: str, outcome: str, **fields) -> dict:
    return {
        "schema": RECALL_CONTEXT_SCHEMA,
        "identity": identity,
        "identity_basis": basis,
        "outcome": outcome,
        **fields,
    }


def test_scope_is_the_views_the_recognition_match_spoke_through_and_no_negative_subtracts():
    axial = ["Axial", "0", "0"]
    rows = [
        _row("femur", True, SAG, COR),
        _row("patella", True, axial),
        _row("femur", False, axial),
    ]
    not_applying = [{**_row("femur", True, SAG), "applies": False}]
    for basis, outcome in (
        (MAP_RELATION, "appearance_supports"),
        (STRUCTURAL_READER, "established_by_structure"),
    ):
        warranted = _in_context(
            "femur",
            basis,
            outcome,
            appearance="supports",
            cases=rows,
            negative_cases=not_applying,
        )
        assert admission_scope(warranted, "femur") == {"views": [COR, SAG]}
    # A bone the reader established whose own cases do not speak warrants no scope.
    unsupported = _in_context(
        "femur",
        STRUCTURAL_READER,
        "established_by_structure",
        appearance="silent",
        cases=rows,
    )
    assert admission_scope(unsupported, "femur")["detail"] == (
        "identity_not_warranted_in_context"
    )
    # A recall made without context warrants no scope, whatever spoke in it.
    legacy = {"cases": rows, "negative_cases": []}
    assert admission_scope(legacy, "femur") == {
        "refusal": "admission_scope_unresolved",
        "detail": "recall_not_in_context",
    }


def test_unresolved_or_malformed_scope_is_a_named_refusal_never_a_whole_case_call():
    unparsed = [
        {"identity": "femur", "speaks": True, "common_speaking_banks": ["not-a-bank"]}
    ]
    for recall, detail in (
        (
            _in_context("femur", MAP_RELATION, "appearance_supports", cases=unparsed),
            "speaking_banks_malformed",
        ),
        (
            _in_context(
                "femur",
                MAP_RELATION,
                "appearance_supports",
                cases=[_row("femur", False, SAG)],
            ),
            "no_usable_view",
        ),
        (
            _in_context("femur", MAP_RELATION, "appearance_supports", cases="rows"),
            "recall_rows_missing",
        ),
        (
            _in_context("femur", MAP_RELATION, "appearance_silent", cases=[]),
            "identity_not_warranted_in_context",
        ),
        (
            _in_context("femur", MAP_RELATION, "signed_conflict", cases=[]),
            "identity_not_warranted_in_context",
        ),
        (
            _in_context(
                "tibia",
                STRUCTURAL_READER,
                "established_by_structure",
                appearance="supports",
                cases=[_row("tibia", True, SAG)],
            ),
            "recall_identity_mismatch",
        ),
        ({}, "recall_not_in_context"),
    ):
        assert admission_scope(recall, "femur") == {
            "refusal": "admission_scope_unresolved",
            "detail": detail,
        }
    item = candidate(
        "sx", "femur", [(SAG, (4, 0, 1))], plausible("femur"), placed("femur", "tibia")
    )
    decision = admission_from_recall(
        item,
        _in_context("femur", MAP_RELATION, "appearance_supports", cases=unparsed),
    )
    assert (decision["state"], decision["reason"]) == (
        "refused",
        "admission_scope_unresolved",
    )
    assert decision["views"] == []
    scoped = admission_from_recall(
        item,
        _in_context(
            "femur",
            MAP_RELATION,
            "appearance_supports",
            cases=[_row("femur", True, SAG)],
        ),
    )
    assert (scoped["state"], scoped["views"]) == ("admitted", [SAG])
    # A recall made for another basis than the candidate's context is refused by name.
    mismatched = admission_from_recall(
        item,
        _in_context(
            "femur",
            STRUCTURAL_READER,
            "established_by_structure",
            appearance="supports",
            cases=[_row("femur", True, SAG)],
        ),
    )
    assert (mismatched["state"], mismatched["reason"]) == (
        "refused",
        "recall_not_in_this_context",
    )


def test_a_malformed_context_is_refused_by_name_and_never_recalled_as_valid():
    memory = identity_memory(ROUND_SEEDS)
    item = candidate(
        "sx", "femur", [(SAG, (4, 0, 1))], plausible("femur"), established("femur")
    )
    for broken, code in (
        (
            {**placed("femur"), "subject": "tibia"},
            "identity_context_subject_mismatch",
        ),
        (
            # Valid for no subject: the reader removes the context's own bone.
            {**established("femur"), "subject": "tibia"},
            "identity_context_removed_invalid",
        ),
        (
            {**established("femur"), "basis": "resemblance"},
            "identity_context_basis_invalid",
        ),
        (
            {**established("femur"), "open_alternatives": ["muscle"]},
            "identity_context_alternatives_invalid",
        ),
        (
            {**placed("femur"), "conditioning": "unconditioned"},
            "identity_context_conditioning_invalid",
        ),
        (
            {**established("femur"), "removed_by_structure": ["femur"]},
            "identity_context_removed_invalid",
        ),
        (
            {**established("femur"), "support": "established_tissue"},
            "identity_context_support_invalid",
        ),
    ):
        decision = decide({**item, "identity_context": broken}, memory)
        assert (decision["state"], decision["reason"]) == ("refused", code)


# ------------------------------------------------------------- candidates


def test_harvest_takes_each_located_profile_with_its_recorded_sanity_and_source():
    anatomy = plausible("femur")
    record = study_record(
        "s1",
        {
            "femur": located("femur", [(SAG, (4, 0, 1))], anatomy),
            "tibia": {"status": "unresolved_missing_reading", "profile": None},
        },
    )
    record["work"] = {"elapsed_seconds": math.nan}  # records are written allowing NaN
    [item] = harvest_candidates([record])
    assert item["case_id"] == f"located:s1:femur:{INFERENCE_REVISION}"
    assert (item["study_uid"], item["subject"]) == ("s1", "femur")
    assert item["profile"] == record["objects"]["femur"]["profile"]
    assert item["sanity"] == anatomy
    assert item["regions"] == [{"series_uid": "series-sag", "window": WINDOW}]
    assert item["source"] == {
        "kind": "squint-inference",
        "record_sha256": record_sha256(record),
        "record_sha256_scope": "decoded_json",
        "memory_revision": INFERENCE_REVISION,
    }
    assert "full_profile" not in item
    [pinned] = harvest_candidates([record], record_sha256s=["c" * 64])
    assert pinned["source"]["record_sha256"] == "c" * 64
    assert pinned["source"]["record_sha256_scope"] == "file_bytes"


def test_harvest_carries_the_identity_context_the_run_recorded_and_no_other():
    objects = {"femur": located("femur", [(SAG, (4, 0, 1))], plausible("femur"))}
    [item] = harvest_candidates(
        [study_record("s1", objects, contexts={"femur": placed("femur", "tibia")})]
    )
    assert item["identity_context"] == placed("femur", "tibia")
    # A record without the versioned consumption record carries none.
    [bare] = harvest_candidates([study_record("s1", objects)])
    assert bare["identity_context"] is None
    older = study_record("s1", objects)
    older["identity_consumption"] = {
        "femur": {"decision": "kept", "reason": "identified"}
    }
    [old] = harvest_candidates([older])
    assert old["identity_context"] is None


def test_harvest_refuses_a_repeated_study_and_malformed_records_by_name():
    record = study_record("s1", {"femur": located("femur", [(SAG, (4, 0, 1))], None)})
    bad_window = copy.deepcopy(record)
    bad_window["objects"]["femur"]["regions"][0]["window"] = [0, 0, 0, 2, 0, 2]
    no_regions = copy.deepcopy(record)
    no_regions["objects"]["femur"]["regions"] = []
    for records, code in (
        ([record, copy.deepcopy(record)], "duplicate_study_record"),
        ([bad_window], "study_record_region_invalid"),
        ([no_regions], "study_record_regions_missing"),
        ([{**record, "schema": "other"}], "study_record_invalid"),
        ([{**record, "memory_revision": ""}], "study_record_invalid"),
    ):
        with pytest.raises(IdentityGrowthError) as info:
            list(harvest_candidates(records))
        assert info.value.code == code
    for digests in (["c" * 63], [], ["c" * 64, "d" * 64]):
        with pytest.raises(IdentityGrowthError) as info:
            list(harvest_candidates([record], record_sha256s=digests))
        assert info.value.code == "record_sha256s_invalid"


# ---------------------------------------------------------- rounds and children


def _placed_record(uid: str, subject: str, by_view, alternative: str) -> dict:
    return study_record(
        uid,
        {subject: located(subject, by_view, plausible(subject))},
        contexts={subject: placed(subject, alternative)},
    )


def test_a_round_consumes_one_shot_streams_in_arrival_order(tmp_path: Path):
    parent = saved(tmp_path, "parent", identity_memory(ROUND_SEEDS))
    records = [
        _placed_record("sx", "femur", [(SAG, (4, 0, 1))], "tibia"),
        # A study the parent holds: scored on its own held-out preparation.
        _placed_record("sa", "tibia", [(SAG, (2, 1, 0))], "femur"),
        _placed_record("sw", "femur", [(SAG, (4, 0, 2))], "tibia"),
    ]
    read: list[str] = []

    def stream():
        for record in records:
            read.append(record["study_uid"])
            yield record

    candidates = harvest_candidates(stream())
    assert read == []  # nothing is read before the round asks for it
    receipt = grow_identity_memory(parent, candidates, tmp_path / "streamed")
    assert read == ["sx", "sa", "sw"]
    expected = [decide(item, parent.memory) for item in harvest_candidates(records)]
    document = json.loads((tmp_path / "streamed" / DECISIONS_FILE).read_text())
    assert document["decisions"] == expected
    assert receipt["admitted_case_ids"] == [f"located:sx:femur:{INFERENCE_REVISION}"]
    [held] = harvest_candidates(records[1:2])
    scored = admission_decision(held, parent.memory)
    assert scored["excluded_study_uid"] == "sa"
    # Its study's femur case is held out: no femur case is left to calibrate against.
    assert (scored["decision"]["state"], scored["decision"]["reason"]) == (
        "proposal",
        "placement_only",
    )
    # A refusal met mid-stream leaves nothing written.
    with pytest.raises(IdentityGrowthError) as info:
        grow_identity_memory(
            parent,
            harvest_candidates(iter([records[0], records[0]])),
            tmp_path / "broken",
        )
    assert info.value.code == "duplicate_study_record"
    assert not (tmp_path / "broken").exists()


def test_admissions_never_speak_in_their_own_round_and_the_next_round_hears_them(
    tmp_path: Path,
):
    parent = saved(tmp_path, "parent", identity_memory(ROUND_SEEDS))
    x = candidate(
        "sx", "femur", [(SAG, (4, 0, 1))], plausible("femur"), placed("femur", "tibia")
    )
    w = candidate(
        "sw", "femur", [(SAG, (4, 0, 2))], plausible("femur"), placed("femur", "tibia")
    )
    receipt = grow_identity_memory(parent, [x, w], tmp_path / "round-1")
    assert receipt["outcome"] == "published"
    assert receipt["admitted_case_ids"] == [x["case_id"]]
    document = json.loads((tmp_path / "round-1" / DECISIONS_FILE).read_text())
    by_id = {row["candidate_id"]: row for row in document["decisions"]}
    # Each candidate was scored against the frozen parent alone.
    for item in (x, w):
        assert (
            by_id[item["case_id"]]
            == admission_decision(item, parent.memory)["decision"]
        )
    assert (by_id[w["case_id"]]["state"], by_id[w["case_id"]]["reason"]) == (
        "proposal",
        "appearance_silent",
    )
    child = load_memory_snapshot(tmp_path / "round-1" / CHILD_DIRECTORY)
    assert prepare_identity(child.memory)["seed_count"] == 3
    heard = recall_identity(
        w["profile"], child.memory, sanity=w["sanity"], context=w["identity_context"]
    )
    assert heard["outcome"] == "appearance_supports"
    [row] = [row for row in heard["cases"] if row["case_id"] == x["case_id"]]
    assert row["speaks"] is True
    assert row["lineage"]["call"]["reader"] == READER
    second = grow_identity_memory(child, [w], tmp_path / "round-2")
    assert second["admitted_case_ids"] == [w["case_id"]]
    grandchild = load_memory_snapshot(tmp_path / "round-2" / CHILD_DIRECTORY).memory
    [admitted] = [c for c in grandchild["cases"] if c["case_id"] == w["case_id"]]
    assert admitted["identity_growth"]["speaking_case_ids"] == [x["case_id"]]
    assert admitted["identity_growth"]["parent_manifest_sha256"] == child.sha256
    rounds = grandchild["object_identity_growth"]["rounds"]
    assert [entry["parent_manifest_sha256"] for entry in rounds] == [
        parent.sha256,
        child.sha256,
    ]


def test_each_admission_is_recognition_derived_with_lineage_and_no_clinical_call(
    tmp_path: Path,
):
    parent = saved(tmp_path, "parent", identity_memory(ROUND_SEEDS))
    x = candidate(
        "sx", "femur", [(SAG, (4, 0, 1))], plausible("femur"), placed("femur", "tibia")
    )
    receipt = grow_identity_memory(parent, [x], tmp_path / "grown")
    data = (tmp_path / "grown" / DECISIONS_FILE).read_bytes()
    assert receipt["decisions_sha256"] == hashlib.sha256(data).hexdigest()
    child = load_memory_snapshot(tmp_path / "grown" / CHILD_DIRECTORY).memory
    [case] = [case for case in child["cases"] if case["case_id"] == x["case_id"]]
    assert case["condition_calls"] == {}
    assert "full_profile" not in case and "presentation_scope" not in case
    assert (case["profile"], case["regions"]) == (x["profile"], x["regions"])
    assert case["teaching_source"] == {
        "kind": RECOGNITION_KIND,
        "parent_manifest_sha256": parent.sha256,
    }
    lineage = case["identity_growth"]
    assert lineage["independent_confirmation"] is False
    assert lineage["parent_manifest_sha256"] == parent.sha256
    assert lineage["speaking_case_ids"] == ["a1"]
    assert lineage["source"] == x["source"]
    assert lineage["decision"]["views"] == [SAG]
    assert lineage["decision"]["support"][0]["establishes"] == "location_only"
    # The admitted presentation keeps the context its identity was warranted in.
    assert lineage["identity_context"] == placed("femur", "tibia")
    teaching = child["object_identity_teaching"]
    [call] = [row for row in teaching["calls"] if row["candidate_id"] == x["case_id"]]
    assert (call["call"], call["views"], call["reader"]) == ("confirm", [SAG], READER)
    assert teaching["confirmed_case_ids"] == ["a1", "t1", x["case_id"]]
    assert child["object_identity_growth"]["schema"] == GROWTH_SCHEMA
    [entry] = child["object_identity_growth"]["rounds"]
    assert entry["decisions_sha256"] == receipt["decisions_sha256"]
    assert entry["admitted_case_ids"] == [x["case_id"]]
    assert child["revision"].startswith(parent.memory["revision"] + "+identity-growth-")
    # Condition recall and every population view still read the child.
    assert prepare_recall(child)["outcome"] == "prepared"
    view = memory_view(child, exclude_study_uids=("sx",))
    assert x["case_id"] not in [row["case_id"] for row in view["cases"]]


def test_a_round_without_admissions_writes_decisions_and_publishes_no_child(
    tmp_path: Path,
):
    parent = saved(tmp_path, "parent", identity_memory(ROUND_SEEDS))
    w = candidate(
        "sw", "femur", [(SAG, (4, 0, 2))], plausible("femur"), placed("femur", "tibia")
    )
    receipt = grow_identity_memory(parent, [w], tmp_path / "quiet")
    assert (receipt["outcome"], receipt["child"]) == ("no_admissions", None)
    assert [path.name for path in (tmp_path / "quiet").iterdir()] == [DECISIONS_FILE]
    only = grow_identity_memory(
        parent,
        [
            candidate(
                "sx",
                "femur",
                [(SAG, (4, 0, 1))],
                plausible("femur"),
                placed("femur", "tibia"),
            )
        ],
        tmp_path / "decisions",
        decisions_only=True,
    )
    assert only["outcome"] == "decisions_only" and only["admitted_case_ids"]
    assert [path.name for path in (tmp_path / "decisions").iterdir()] == [
        DECISIONS_FILE
    ]


def test_a_round_refuses_by_name_and_writes_nothing(tmp_path: Path):
    parent = saved(tmp_path, "parent", identity_memory(ROUND_SEEDS))
    x = candidate(
        "sx", "femur", [(SAG, (4, 0, 1))], plausible("femur"), placed("femur", "tibia")
    )
    (tmp_path / "taken").mkdir()
    plain = identity_memory(ROUND_SEEDS)
    del plain["object_identity_teaching"]
    for arguments, code in (
        ((parent, [x, copy.deepcopy(x)], tmp_path / "twice"), "duplicate_candidate_id"),
        ((parent, [x], tmp_path / "taken"), "output_exists"),
        ((parent, [x], tmp_path / "parent" / "inside"), "output_path_unsafe"),
        ((parent.memory, [x], tmp_path / "raw"), "invalid_parent_snapshot"),
        (
            (saved(tmp_path, "plain", plain), [x], tmp_path / "untaught"),
            "parent_identity_teaching_missing",
        ),
    ):
        with pytest.raises(IdentityGrowthError) as info:
            grow_identity_memory(*arguments)
        assert info.value.code == code
        assert not arguments[2].exists() or arguments[2] == tmp_path / "taken"


# -------------------------------------- a signed parent with full payloads

SIGNED = (
    ("study-a", "femur", ((SAG, (3, 0, 0)), (COR, (3, 0, 0)))),
    ("study-b", "patella", ((SAG, (0, 0, 3)), (COR, (0, 0, 3)))),
    ("study-c", "femur", ((SAG, (1, 2, 0)), (COR, (3, 0, 0)))),
    ("study-d", "patella", ((SAG, (3, 0, 0)), (COR, (0, 0, 3)))),
    ("study-e", "femur", ((SAG, (3, 0, 0)), (COR, (3, 0, 0)))),
)
FA, PB, FC, PD, FE = (f"squint-case:{uid}:{subject}" for uid, subject, _ in SIGNED)
CONDITION = {"femur": "ACL", "patella": "PF OA"}


@pytest.fixture
def signed(tmp_path: Path) -> SimpleNamespace:
    """A five-study catalogue and its signed parent; every H5 product is deleted.

    The parent confirms FA and PB, rejects FC on the sagittal view (a femur
    negative), and rejects PD sagittally while calling that facet femur (an
    alternative positive). FE stays uncalled.
    """
    products = tmp_path / "products"
    products.mkdir()
    cases, sources = [], {}
    for uid, subject, by_view in SIGNED:
        product = products / f"{uid}.h5"
        manifest, record = _product(product, uid, (subject,))
        composition = manifest["object_composition"]
        digest = hashlib.sha256(product.read_bytes()).hexdigest()
        sources[uid] = {
            "product_path": str(product.resolve()),
            "product_sha256": digest,
            "layout_fingerprint": composition["layout_fingerprint"],
            "carrier_identity": composition["carrier_identity"],
            "source_roots": {},
            "full_profile_subjects": [subject],
        }
        banks = {f"coarse/{subject}/signal": [5, 0, 3]}
        banks.update({bank(view): list(counts) for view, counts in by_view})
        cases.append(
            {
                "case_id": f"squint-case:{uid}:{subject}",
                "study_uid": uid,
                "subject": subject,
                "condition_calls": {CONDITION[subject]: 1},
                "presentation_scope": {
                    CONDITION[subject]: "positive_condition_presentation"
                },
                "question_roles": {CONDITION[subject]: "implicated"},
                "label_attribution": {},
                "profile": {
                    "schema": "knee.squint-profile/v1",
                    "subject": subject,
                    "banks": banks,
                    "source": {"procedure": PROCEDURE},
                },
                "regions": [],
                "full_profile": {
                    "subject": subject,
                    "mode": "full",
                    "scope": f"object:{subject}",
                    "count_layout_id": record["count_layout_id"],
                    "reference_set_identity": record["reference_set_identity"],
                    "carrier_identity": composition["carrier_identity"],
                    "layout_fingerprint": composition["layout_fingerprint"],
                    "product_record_sha256": _json_sha256(record),
                },
                "full_source": {
                    "product_path": str(product.resolve()),
                    "product_sha256": digest,
                    "study_uid": uid,
                    "source_roots": {},
                },
                "teaching_source": {"kind": "official_train_csv_label"},
            }
        )
    catalogue = {
        "schema": SCHEMA,
        "revision": "growth-fixture-catalogue",
        "questions": list(LABELS),
        "procedure": {"id": "knee.squint-ternary/v1"},
        "source_identities": sources,
        "cases": cases,
    }
    save_memory(hydrate_full_profiles(catalogue, products), tmp_path / "catalogue")
    snapshot = load_memory_snapshot(tmp_path / "catalogue")
    review = build_review(snapshot.memory, snapshot.sha256, [FA, PB, FC, PD])
    for item in review["candidates"]:
        if item["candidate_id"] in (FC, PD):
            item["evidence"] = {
                "panels": [
                    {
                        "view": dict(
                            zip(
                                ("orientation", "fluid_sensitive", "fat_suppression"),
                                view,
                                strict=True,
                            )
                        ),
                        "image_state": "read",
                        "support_state": "drawn",
                    }
                    for view in (SAG, COR)
                ]
            }
    pin = hashlib.sha256(json.dumps(review, sort_keys=True).encode("utf-8")).hexdigest()
    calls = {
        "schema": CALLS_SCHEMA,
        "review_sha256": pin,
        "reader": "reader-one",
        "calls": [
            {"candidate_id": FA, "call": "confirm", "notes": "n"},
            {"candidate_id": PB, "call": "confirm", "notes": "n"},
            {"candidate_id": FC, "call": "reject", "notes": "n", "views": [SAG]},
            {
                "candidate_id": PD,
                "call": "reject",
                "notes": "n",
                "views": [SAG],
                "also_positive": [{"identity": "femur", "views": [SAG]}],
            },
        ],
    }
    publish_seed_memory(snapshot, review, calls, pin, tmp_path / "parent")
    parent = load_memory_snapshot(tmp_path / "parent")
    for product in products.glob("*.h5"):
        product.unlink()
    return SimpleNamespace(catalogue=snapshot, parent=parent, root=tmp_path)


def test_growth_keeps_every_signed_record_and_the_next_reader_hears_the_negatives(
    signed,
):
    parent = signed.parent
    before = copy.deepcopy(parent.memory)
    x = candidate(
        "study-x",
        "femur",
        [(SAG, (3, 0, 0)), (COR, (3, 0, 0))],
        plausible("femur"),
        placed("femur", "patella"),
    )
    # Placed by the prior alone, it leaves every identity open: the parent's sagittal
    # "not femur" support is heard in this very round, beside the femur's own case. At
    # 10 mm that opens its identity question, and with no finer reading it stays open.
    y = candidate(
        "study-y",
        "femur",
        [(SAG, (1, 2, 0)), (COR, (3, 0, 0))],
        plausible("femur"),
        identity_context("femur", PRIOR_ONLY),
    )
    receipt = grow_identity_memory(parent, [x, y], signed.root / "grown")
    assert receipt["state_counts"] == {"admitted": 1, "proposal": 1}
    document = json.loads((signed.root / "grown" / DECISIONS_FILE).read_text())
    by_id = {row["candidate_id"]: row for row in document["decisions"]}
    assert by_id[x["case_id"]]["views"] == [COR, SAG]
    assert (by_id[y["case_id"]]["state"], by_id[y["case_id"]]["reason"]) == (
        "proposal",
        "squint_contest_unresolved_no_finer_reading",
    )
    assert by_id[y["case_id"]]["recognized_identity"] is None
    child = load_memory_snapshot(signed.root / "grown" / CHILD_DIRECTORY).memory
    # The frozen parent is untouched, in memory and on disk.
    assert parent.memory == before
    assert load_memory_snapshot(parent.path).sha256 == parent.sha256
    assert child["cases"][: len(before["cases"])] == before["cases"]
    assert child["object_identity_cases"] == before["object_identity_cases"]
    teaching, parent_teaching = (
        child["object_identity_teaching"],
        before["object_identity_teaching"],
    )
    for key in (
        "negative_case_ids",
        "negative_views",
        "negatives_not_written",
        "alternative_positives",
        "reader",
        "review_sha256",
        "reviewed_candidate_ids",
    ):
        assert teaching[key] == parent_teaching[key]
    assert (
        teaching["calls"][: len(parent_teaching["calls"])] == parent_teaching["calls"]
    )
    for table, key in (
        ("full_profile_payloads", "payloads"),
        ("full_profile_contexts", "contexts"),
    ):
        assert child[table][key] == before[table][key]
    assert child["source_identities"] == before["source_identities"]
    [case] = [case for case in child["cases"] if case["case_id"] == x["case_id"]]
    assert case["identity_growth"]["speaking_case_ids"] == sorted(
        [FA, f"{PD}::also_positive::femur"]
    )
    # Offline: no product is left, and every signed record still reads in full.
    for record in child["object_identity_cases"]["cases"]:
        full = _full_profile_from_validated_case(
            child, record, record["full_profile"], record["subject"]
        )
        assert full.source_id == record["study_uid"]
    prepared = prepare_identity(child)
    assert (
        prepared["seed_count"],
        prepared["negative_case_count"],
        prepared["alternative_positive_count"],
    ) == (4, 2, 1)
    # The next round's reader still meets the parent's -1 on its own view.
    heard = recall_identity(y["profile"], child, prepared=prepared)
    assert heard["outcome"] == "unresolved_conflict"
    assert FC in [row["case_id"] for row in heard["negative_cases"] if row["speaks"]]
    # In context it applies over the region it asserted.
    in_context = recall_identity(
        y["profile"], child, prepared=prepared, context=placed("femur", "patella")
    )
    applying = [
        row["case_id"] for row in in_context["negative_cases"] if row["applies"]
    ]
    assert applying == [FC]
    held_out = memory_view(child, exclude_study_uids=("study-c",))
    assert FC not in [
        row["case_id"] for row in held_out["object_identity_cases"]["cases"]
    ]
    assert (
        prepare_identity(child, exclude_study_uid="study-c")["negative_case_count"] == 1
    )
    assert prepare_recall(child)["outcome"] == "prepared"


def _memory_items(snapshot, candidate_ids, contexts, sanity_by_case_id=None):
    """Memory candidates with the contexts a caller supplies, as candidates_from_memory
    carries none of its own."""
    for item in candidates_from_memory(
        snapshot, candidate_ids=candidate_ids, sanity_by_case_id=sanity_by_case_id
    ):
        if item["case_id"] in contexts:
            item = {**item, "identity_context": contexts[item["case_id"]]}
        yield item


def test_a_candidate_memory_case_enters_as_its_source_holds_it(signed):
    items = _memory_items(
        signed.catalogue,
        [FE, FA, FC],
        {FE: placed("femur", "patella")},
        sanity_by_case_id={FE: plausible("femur")},
    )
    receipt = grow_identity_memory(signed.parent, items, signed.root / "from-memory")
    document = json.loads((signed.root / "from-memory" / DECISIONS_FILE).read_text())
    states = {
        row["candidate_id"]: (row["state"], row["reason"])
        for row in document["decisions"]
    }
    assert states == {
        FE: ("admitted", "appearance_supports_with_location_support"),
        FA: ("duplicate", "case_id_already_in_parent"),
        # A rejected support never returns as a positive of its own case.
        FC: ("duplicate", "case_id_already_in_parent"),
    }
    assert receipt["admitted_case_ids"] == [FE]
    child = load_memory_snapshot(signed.root / "from-memory" / CHILD_DIRECTORY).memory
    [case] = [case for case in child["cases"] if case["case_id"] == FE]
    original = next(c for c in signed.catalogue.memory["cases"] if c["case_id"] == FE)
    assert {key: value for key, value in case.items() if key != "identity_growth"} == (
        original
    )
    assert case["identity_growth"]["source"]["kind"] == "candidate-memory"
    assert (
        case["identity_growth"]["source"]["manifest_sha256"] == signed.catalogue.sha256
    )
    # Its paired full profile travelled with it and reads offline.
    assert full_profile_from_case(child, case).source_id == "study-e"
    assert (
        child["source_identities"]["study-e"]
        == (signed.catalogue.memory["source_identities"]["study-e"])
    )
    # The selection is checked at once, before any candidate is made.
    with pytest.raises(IdentityGrowthError) as info:
        candidates_from_memory(signed.catalogue, candidate_ids=["unknown-case"])
    assert info.value.code == "unknown_candidate"
    # A memory case carries no inference context: it stays a proposal, named.
    [plain] = candidates_from_memory(signed.catalogue, candidate_ids=[FE])
    assert admission_decision(plain, signed.parent.memory)["decision"]["reason"] == (
        "memory_candidate_without_identity_context"
    )


# --------------------------------------------------------------------- CLI


def _cli():
    path = ROOT / "scripts" / "squint_object_bootstrap.py"
    spec = importlib.util.spec_from_file_location("squint_object_bootstrap_grow", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MOD = _cli()


def _inference(tmp_path: Path, name: str, records: list[dict]) -> Path:
    for record in records:
        dump_json_atomic(
            tmp_path / name / "studies" / (record["study_uid"] + ".json"),
            record,
            compression_preset=0,
        )
    return tmp_path / name


def test_cli_decisions_only_writes_the_frozen_schema_and_publishes_nothing(
    tmp_path: Path, capsys
):
    parent = saved(tmp_path, "parent", identity_memory(ROUND_SEEDS))
    record = study_record(
        "sx",
        {
            "femur": located("femur", [(SAG, (4, 0, 1))], plausible("femur")),
            "tibia": located("tibia", [(SAG, (0, 0, 3))], unknown("tibia")),
        },
        contexts={"femur": placed("femur", "tibia"), "tibia": placed("tibia", "femur")},
    )
    record["work"] = {"elapsed_seconds": math.nan}
    directory = _inference(tmp_path, "inference", [record])
    [(read_back, digest)] = read_inference_records(directory)
    assert read_back["study_uid"] == "sx"
    output = tmp_path / "decisions"
    result = MOD.main(
        [
            "grow",
            "--parent",
            str(tmp_path / "parent"),
            "--inference",
            str(directory),
            "--output",
            str(output),
            "--decisions-only",
        ]
    )
    assert (result["action"], result["outcome"], result["child"]) == (
        "grow",
        "decisions_only",
        None,
    )
    assert [path.name for path in output.iterdir()] == [DECISIONS_FILE]
    data = (output / DECISIONS_FILE).read_bytes()
    document = json.loads(data)
    assert sorted(document) == ["decisions", "parent", "schema"]
    assert document["schema"] == DECISIONS_SCHEMA
    assert document["parent"] == {
        "manifest_sha256": parent.sha256,
        "revision": parent.memory["revision"],
    }
    assert all(sorted(row) == DECISION_KEYS for row in document["decisions"])
    by_subject = {row["subject"]: row for row in document["decisions"]}
    assert by_subject["femur"]["state"] == "admitted"
    assert by_subject["femur"]["identity_context"] == placed("femur", "tibia")
    assert (by_subject["tibia"]["state"], by_subject["tibia"]["reason"]) == (
        "proposal",
        "appearance_silent",
    )
    file_sha256 = hashlib.sha256(
        (directory / "studies" / "sx.json.xz").read_bytes()
    ).hexdigest()
    assert digest == file_sha256
    assert by_subject["femur"]["source"] == {
        "kind": "squint-inference",
        "record_sha256": file_sha256,
        "record_sha256_scope": "file_bytes",
        "memory_revision": INFERENCE_REVISION,
    }
    assert by_subject["femur"]["regions"] == [
        {"series_uid": "series-sag", "window": WINDOW}
    ]
    printed = json.loads(capsys.readouterr().out)
    assert printed["decisions_sha256"] == hashlib.sha256(data).hexdigest()


def test_cli_publishes_the_child_beside_its_decisions_and_refuses_overwrite(
    tmp_path: Path,
):
    saved(tmp_path, "parent", identity_memory(ROUND_SEEDS))
    record = _placed_record("sx", "femur", [(SAG, (4, 0, 1))], "tibia")
    directory = _inference(tmp_path, "inference", [record])
    output = tmp_path / "grown"
    arguments = [
        "grow",
        "--parent",
        str(tmp_path / "parent"),
        "--inference",
        str(directory),
        "--output",
        str(output),
    ]
    result = MOD.main(arguments)
    assert result["outcome"] == "published"
    assert sorted(path.name for path in output.iterdir()) == [
        DECISIONS_FILE,
        CHILD_DIRECTORY,
    ]
    child = load_memory_snapshot(output / CHILD_DIRECTORY)
    assert child.sha256 == result["child"]["sha256"]
    assert result["child"]["identity_preparation"]["seed_count"] == 3
    with pytest.raises(SystemExit) as info:
        MOD.main(arguments)
    assert str(info.value) == "output_exists"
    assert load_memory_snapshot(output / CHILD_DIRECTORY).sha256 == child.sha256


def test_cli_refuses_a_parent_without_identity_teaching(tmp_path: Path):
    plain = identity_memory(ROUND_SEEDS)
    del plain["object_identity_teaching"]
    save_memory(plain, tmp_path / "plain")
    record = _placed_record("sx", "femur", [(SAG, (4, 0, 1))], "tibia")
    directory = _inference(tmp_path, "inference", [record])
    with pytest.raises(SystemExit) as info:
        MOD.main(
            [
                "grow",
                "--parent",
                str(tmp_path / "plain"),
                "--inference",
                str(directory),
                "--output",
                str(tmp_path / "out"),
            ]
        )
    assert str(info.value) == "parent_identity_teaching_missing"
    assert not (tmp_path / "out").exists()


# ------------------------------------- condition teaching and held-out studies
#
# The full two-sign record is tests/test_squint_growth_condition_teaching.py; these
# pin the memory-candidate path and the CLI flags.


def _labels_csv(path: Path, rows: dict) -> Path:
    """A train.csv with the competition's header; no cell here needs quoting."""
    lines = [",".join(["StudyInstanceUID", "Report", *LABELS])]
    for uid, values in rows.items():
        cells = ["" if values.get(q) is None else str(values[q]) for q in LABELS]
        lines.append(",".join([uid, "report", *cells]))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_a_memory_candidate_keeps_its_source_calls_and_its_row_is_not_read(signed):
    # study-e's row is malformed: reading it would refuse the round.
    labels = _labels_csv(signed.root / "train.csv", {"study-e": {"ACL": "x"}})
    items = _memory_items(
        signed.catalogue,
        [FE],
        {FE: placed("femur", "patella")},
        sanity_by_case_id={FE: plausible("femur")},
    )
    receipt = grow_identity_memory(
        signed.parent, items, signed.root / "labelled", labels=labels
    )
    assert receipt["admitted_case_ids"] == [FE]
    teaching = receipt["condition_teaching"]
    assert teaching["read_study_uids"] == []
    assert teaching["cases"] == {FE: {"status": "source_case_retained"}}
    child = load_memory_snapshot(signed.root / "labelled" / CHILD_DIRECTORY).memory
    [case] = [case for case in child["cases"] if case["case_id"] == FE]
    original = next(c for c in signed.catalogue.memory["cases"] if c["case_id"] == FE)
    assert {key: value for key, value in case.items() if key != "identity_growth"} == (
        original
    )
    assert case["condition_calls"] == {"ACL": 1}
    assert "condition_teaching" not in case
    assert child["object_identity_growth"]["rounds"][0]["condition_teaching"] == (
        teaching
    )


def test_cli_carries_labels_and_holds_out_studies_without_changing_decisions(
    tmp_path: Path,
):
    saved(tmp_path, "parent", identity_memory(ROUND_SEEDS))
    records = [
        _placed_record(uid, "femur", [(SAG, (4, 0, 1))], "tibia")
        for uid in ("sh", "sx")
    ]
    directory = _inference(tmp_path, "inference", records)
    held = tmp_path / "held-out.txt"
    held.write_text("sh\n\n", encoding="utf-8")
    # sh's row is malformed: it is held out, so it is never read.
    labels = _labels_csv(
        tmp_path / "train.csv", {"sh": {"ACL": "x"}, "sx": {"ACL": 1, "Fracture": 0}}
    )
    base = ["grow", "--parent", str(tmp_path / "parent"), "--inference", str(directory)]
    result = MOD.main(
        [
            *base,
            "--output",
            str(tmp_path / "with-labels"),
            "--labels",
            str(labels),
            "--held-out",
            str(held),
        ]
    )
    plain = MOD.main(
        [*base, "--output", str(tmp_path / "without-labels"), "--held-out", str(held)]
    )
    assert result["held_out_file"] == {
        "path": str(held.resolve()),
        "sha256": hashlib.sha256(held.read_bytes()).hexdigest(),
        "study_uid_count": 1,
    }
    data = (tmp_path / "with-labels" / DECISIONS_FILE).read_bytes()
    assert data == (tmp_path / "without-labels" / DECISIONS_FILE).read_bytes()
    document = json.loads(data)
    assert document["held_out"] == {
        "schema": "knee.identity-growth-held-out/v1",
        "study_uids": ["sh"],
        "sha256": _json_sha256(["sh"]),
    }
    states = {row["study_uid"]: row["state"] for row in document["decisions"]}
    assert states == {"sh": "held_out", "sx": "admitted"}
    case_id = f"located:sx:femur:{INFERENCE_REVISION}"
    child = load_memory_snapshot(tmp_path / "with-labels" / CHILD_DIRECTORY).memory
    [case] = [case for case in child["cases"] if case["case_id"] == case_id]
    assert case["condition_calls"] == {"ACL": 1, "Fracture": -1}
    assert case["condition_teaching"]["status"] == "carried"
    assert case["condition_teaching"]["carry"]["speaks_through"] == {
        "ACL": [SAG],
        "Fracture": [SAG],
    }
    assert case["label_attribution"]["ACL"]["source_path"] == str(labels.resolve())
    assert child["object_identity_growth"]["held_out"] == document["held_out"]
    assert result["condition_teaching"]["read_study_uids"] == ["sx"]
    unlabelled = load_memory_snapshot(
        tmp_path / "without-labels" / CHILD_DIRECTORY
    ).memory
    [same] = [case for case in unlabelled["cases"] if case["case_id"] == case_id]
    assert same["condition_calls"] == {} and "condition_teaching" not in same
    assert plain["condition_teaching"] is None
    assert child["revision"] != unlabelled["revision"]


def test_cli_refuses_a_malformed_held_out_file_or_labels_without_a_child(
    tmp_path: Path,
):
    saved(tmp_path, "parent", identity_memory(ROUND_SEEDS))
    record = study_record(
        "sx", {"femur": located("femur", [(SAG, (4, 0, 1))], plausible("femur"))}
    )
    directory = _inference(tmp_path, "inference", [record])
    base = ["grow", "--parent", str(tmp_path / "parent"), "--inference", str(directory)]
    files = {
        "empty": "\n \n",
        "twice": "sx\nsy\nsx\n",
        "spaced": "s x\n",
    }
    expected = {
        "empty": "held_out_file_empty: " + str(tmp_path / "empty.txt"),
        "twice": "held_out_file_duplicate: sx",
        "spaced": "held_out_file_line_invalid: s x",
    }
    for name, text in files.items():
        (tmp_path / f"{name}.txt").write_text(text, encoding="utf-8")
        with pytest.raises(SystemExit) as info:
            MOD.main(
                [
                    *base,
                    "--output",
                    str(tmp_path / "out"),
                    "--held-out",
                    str(tmp_path / f"{name}.txt"),
                ]
            )
        assert str(info.value) == expected[name]
        assert not (tmp_path / "out").exists()
    labels = _labels_csv(tmp_path / "train.csv", {"sx": {"ACL": 1}})
    with pytest.raises(SystemExit) as info:
        MOD.main(
            [
                *base,
                "--output",
                str(tmp_path / "out"),
                "--labels",
                str(labels),
                "--decisions-only",
            ]
        )
    assert str(info.value) == "labels_with_decisions_only"
    assert not (tmp_path / "out").exists()
