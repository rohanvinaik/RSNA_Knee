"""Identity recall in context and the context it is conditioned on, two signs a meaning.

Rohan, 2026-10-21: «Positive and negative cases are expertise, not decorative
annotations... Muscle surrounding a bone is different from muscle occupying the region
asserted to be the bone. A broad mixed window is different from a resolved object.» And:
«They're BOTH BONES... Do not introduce a new tissue-kind classifier, tune bone profiles
apart».

So a located object keeps its identity in context and is never renamed. Its own cases
speak against the identities the context leaves open: for a bone the structural reader
established, every identity but the reader's other bones (found in the study or not),
which it tells apart by their observed arrangement; for a placement by the anatomy map,
the alternatives whose own proposals overlap it; for the prior alone, every other
identity. A negative case applies where its reason holds for the candidate's asserted
region: over the object's own tiles, not only through the surroundings; for the object's
own identity; and, if its call asserts what the region shows instead, only while that
alternative is still open. Each test calls ``recall_identity`` or the pipeline's context
builder directly.
"""

from __future__ import annotations

import copy
from fractions import Fraction

import pytest

from knee.diagnosis import squint_pipeline
from knee.diagnosis.squint_anatomy_locator import BONES
from knee.diagnosis.squint_identity import (
    APPEARANCE_OPPOSED,
    APPEARANCE_SUPPORTS,
    CONDITIONING,
    CONTESTED_AFTER_FINER_READING,
    CONTEXT_SCHEMA,
    ESTABLISHED_BY_STRUCTURE,
    FINER_RECALL_INVALID,
    IDENTITY_CASES_SCHEMA,
    JOINT_SCALE,
    MAP_RELATION,
    NEGATIVE_APPLIES,
    NEGATIVE_NOT_COMPARED,
    PRIOR_ONLY,
    PROPOSED_PLACES,
    RECALL_CONTEXT_SCHEMA,
    RESOLVED_BY_FINER_READING,
    RESOLVED_SUPPORT,
    SIGNED_CONFLICT,
    SQUINT_SCALE,
    STRUCTURAL_READER,
    SUPPORT_UNRECORDED,
    TEACHING_SCHEMA,
    UNRESOLVED_NO_FINER_READING,
    _envelope_over,
    preparation_scale,
    prepare_identity,
    recall_identity,
    squint_contest_resolution,
)
from knee.diagnosis.squint_interfaces import territory_bank_name

SAG = ["Sagittal", "0", "0"]
COR = ["Coronal", "0", "0"]
PROCEDURE = "knee.squint-profile/scan-tercile-v1"
WINDOW = [0, 1, 0, 2, 0, 2]


def bank(view: list[str], role: str = "object") -> str:
    return territory_bank_name(
        dict(
            zip(
                ("orientation", "fluid_sensitive", "fat_suppression"), view, strict=True
            )
        ),
        role,
        "signal",
        "d",
        10.0,
    )


def profile(subject: str, by_view, ring=()) -> dict:
    banks = {bank(view): list(counts) for view, counts in by_view}
    banks.update({bank(view, "context"): list(counts) for view, counts in ring})
    return {
        "schema": "knee.squint-profile/v1",
        "subject": subject,
        "banks": banks,
        "source": {"procedure": PROCEDURE},
    }


def _case(case_id, subject, study_uid, by_view, ring=()) -> dict:
    return {
        "case_id": case_id,
        "study_uid": study_uid,
        "subject": subject,
        "condition_calls": {},
        "profile": profile(subject, by_view, ring),
        "regions": [],
    }


def memory(seeds, negatives=()) -> dict:
    """Confirmed seeds, and ordinary negative cases on the views their reject asserted.

    ``seeds`` are (case_id, subject, study_uid, by_view[, ring]); each negative is a dict
    with case_id, subject, study_uid, by_view, views and optionally ring and also_positive.
    """
    cases = [_case(*seed) for seed in seeds]
    calls = [{"candidate_id": case["case_id"], "call": "confirm"} for case in cases]
    teaching = {
        "schema": TEACHING_SCHEMA,
        "confirmed_case_ids": [case["case_id"] for case in cases],
        "calls": calls,
    }
    result = {"revision": "r1", "cases": cases, "object_identity_teaching": teaching}
    if negatives:
        teaching["negative_case_ids"] = [row["case_id"] for row in negatives]
        teaching["negative_views"] = {
            row["case_id"]: [list(view) for view in row["views"]] for row in negatives
        }
        for row in negatives:
            call = {
                "candidate_id": row["case_id"],
                "call": "reject",
                "views": [list(view) for view in row["views"]],
                "notes": "not this object",
            }
            if "also_positive" in row:
                call["also_positive"] = copy.deepcopy(row["also_positive"])
            calls.append(call)
        result["object_identity_cases"] = {
            "schema": IDENTITY_CASES_SCHEMA,
            "cases": [
                _case(
                    row["case_id"],
                    row["subject"],
                    row["study_uid"],
                    row["by_view"],
                    row.get("ring", ()),
                )
                for row in negatives
            ],
        }
    return result


def context(subject: str, basis: str, open_alternatives=(), contradictions=()) -> dict:
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


def recall(query: dict, taught: dict, ctx: dict | None) -> dict:
    return recall_identity(query, taught, context=ctx)


def negative_row(result: dict, case_id: str) -> dict:
    [row] = [row for row in result["negative_cases"] if row["case_id"] == case_id]
    return row


# Femur and patella seeds over their object tiles and surroundings.
RING_SEEDS = (
    ("f1", "femur", "sf", [(SAG, (3, 0, 0))], [(SAG, (3, 0, 0))]),
    ("p1", "patella", "sp", [(SAG, (0, 0, 3))], [(SAG, (0, 0, 3))]),
)
# A "not femur" support: its object tiles (0,3,0), its surroundings (1,2,0).
RING_NEGATIVE = {
    "case_id": "n1",
    "subject": "femur",
    "study_uid": "sn",
    "by_view": [(SAG, (0, 3, 0))],
    "ring": [(SAG, (1, 2, 0))],
    "views": [SAG],
}
PLAIN_SEEDS = (
    ("f1", "femur", "sf", [(SAG, (3, 0, 0))]),
    ("t1", "tibia", "st", [(SAG, (0, 0, 3))]),
)
NOT_FEMUR = {
    "case_id": "n1",
    "subject": "femur",
    "study_uid": "sn",
    "by_view": [(SAG, (1, 2, 0))],
    "views": [SAG],
}


# ----------------------------------------------- where a negative's reason holds


def test_a_negative_applies_over_the_asserted_region_and_not_through_the_surroundings():
    taught = memory(RING_SEEDS, [RING_NEGATIVE])
    placement = context("femur", MAP_RELATION, ["patella"])
    # Occupying: the candidate's own tiles resemble the negative's own tiles.
    occupying = recall(
        profile("femur", [(SAG, (0, 3, 0))], [(SAG, (1, 2, 0))]), taught, placement
    )
    row = negative_row(occupying, "n1")
    assert (row["applies"], row["reason"]) == (True, "speaks_over_the_asserted_region")
    assert row["over_the_asserted_region"]["speaks"] is True
    assert occupying["applicable_negative_case_ids"] == ["n1"]
    assert (occupying["outcome"], occupying["identity"]) == (SIGNED_CONFLICT, "femur")
    assert occupying["identity_state"] == "contested"
    # Surrounding: only the surroundings resemble; the femur's own tiles do not.
    around = recall(
        profile("femur", [(SAG, (3, 0, 0))], [(SAG, (1, 2, 0))]), taught, placement
    )
    row = negative_row(around, "n1")
    assert (row["applies"], row["reason"]) == (False, "surroundings_only")
    assert row["with_the_surroundings"]["speaks"] is True
    assert row["over_the_asserted_region"]["speaks"] is False
    assert around["applicable_negative_case_ids"] == []
    assert around["outcome"] == APPEARANCE_SUPPORTS


def test_a_negative_over_the_region_applies_even_where_the_whole_window_is_unlike_it():
    seeds = (("f1", "femur", "sf", [(SAG, (3, 0, 0))], [(SAG, (0, 0, 3))]),)
    negative = {**NOT_FEMUR, "ring": [(SAG, (0, 0, 3))]}
    taught = memory(seeds, [negative])
    prepared = prepare_identity(taught)
    object_key = (bank(SAG),)
    [object_envelope] = prepared._negative_object_envelopes
    entry = object_envelope[object_key]
    # Over the object tiles the negative shares 1/5 with the femur's seed ...
    assert Fraction(entry["num"], entry["den"]) == Fraction(1, 5)
    [whole_envelope] = prepared._negative_envelopes
    entry = whole_envelope[tuple(sorted((bank(SAG), bank(SAG, "context"))))]
    # ... and 4/7 over the whole window.
    assert Fraction(entry["num"], entry["den"]) == Fraction(4, 7)
    query = profile("femur", [(SAG, (1, 2, 0))], [(SAG, (3, 0, 0))])
    result = recall_identity(
        query, taught, prepared=prepared, context=context("femur", PRIOR_ONLY)
    )
    row = negative_row(result, "n1")
    assert row["with_the_surroundings"]["speaks"] is False
    assert (row["applies"], row["over_the_asserted_region"]["speaks"]) == (True, True)


def test_an_applicable_negative_with_no_own_case_speaking_opposes_and_never_renames():
    query = profile("femur", [(SAG, (1, 2, 0))])
    reader = context("femur", STRUCTURAL_READER)
    opposed = recall(query, memory(PLAIN_SEEDS, [NOT_FEMUR]), reader)
    assert (opposed["outcome"], opposed["identity"]) == (APPEARANCE_OPPOSED, "femur")
    assert opposed["appearance"] == "uncalibrated"
    assert opposed["reason"] == "applicable_negative_case_speaks_and_no_own_case"
    # Without the negative, the reader's bone is established.
    plain = recall(query, memory(PLAIN_SEEDS), reader)
    assert (plain["outcome"], plain["identity_state"]) == (
        ESTABLISHED_BY_STRUCTURE,
        "established",
    )
    assert plain["negative_cases"] == [] and plain["applicable_negative_case_ids"] == []


@pytest.mark.parametrize(
    ("basis", "alternatives", "removed", "applies"),
    [
        (MAP_RELATION, ["patella"], [], True),
        (MAP_RELATION, [], [], True),
        (MAP_RELATION, [], ["patella"], False),
        (STRUCTURAL_READER, [], [], False),
        (PRIOR_ONLY, [], [], True),
    ],
)
def test_a_negative_asserting_an_alternative_applies_unless_structure_excludes_it(
    basis, alternatives, removed, applies
):
    asserting = {
        **NOT_FEMUR,
        "also_positive": [{"identity": "patella", "views": [SAG]}],
    }
    taught = memory(PLAIN_SEEDS, [asserting])
    observed_context = context("femur", basis, alternatives)
    observed_context["removed_by_structure"].extend(removed)
    result = recall(
        profile("femur", [(SAG, (1, 2, 0))]),
        taught,
        observed_context,
    )
    row = negative_row(result, "n1")
    assert row["asserted_alternatives"] == ["patella"]
    assert row["applies"] is applies
    assert row["reason"] == (
        "speaks_over_the_asserted_region"
        if applies
        else "asserted_alternative_removed_by_structure"
    )
    assert (result["outcome"] in (APPEARANCE_OPPOSED, SIGNED_CONFLICT)) is applies
    # An alternative asserted on another view says nothing about this negative.
    elsewhere = {
        **NOT_FEMUR,
        "also_positive": [{"identity": "patella", "views": [COR]}],
    }
    result = recall(
        profile("femur", [(SAG, (1, 2, 0))]),
        memory(PLAIN_SEEDS, [elsewhere]),
        observed_context,
    )
    row = negative_row(result, "n1")
    assert (row["asserted_alternatives"], row["applies"]) == ([], True)


def test_a_negative_outside_the_querys_views_is_never_met():
    taught = memory(PLAIN_SEEDS, [NOT_FEMUR])
    reader = context("femur", STRUCTURAL_READER)
    coronal = recall(profile("femur", [(COR, (1, 2, 0))]), taught, reader)
    assert (coronal["negative_cases"], coronal["negative_cases_compared"]) == ([], 0)
    assert coronal["outcome"] == ESTABLISHED_BY_STRUCTURE
    sagittal = recall(profile("femur", [(SAG, (1, 2, 0))]), taught, reader)
    assert sagittal["negative_cases_compared"] == 1
    assert negative_row(sagittal, "n1")["applies"] is True


def test_another_identitys_negative_is_recorded_and_never_applies():
    not_tibia = {**NOT_FEMUR, "case_id": "n2", "subject": "tibia"}
    taught = memory(PLAIN_SEEDS, [not_tibia])
    query = profile("femur", [(SAG, (1, 2, 0))])
    femur = recall(query, taught, context("femur", MAP_RELATION, ["tibia"]))
    row = negative_row(femur, "n2")
    assert (row["identity"], row["applies"], row["reason"]) == (
        "tibia",
        False,
        "concerns_another_identity",
    )
    assert femur["applicable_negative_case_ids"] == []
    untouched = recall(
        query, memory(PLAIN_SEEDS), context("femur", MAP_RELATION, ["tibia"])
    )
    assert femur["outcome"] == untouched["outcome"]
    # The same negative is the tibia's own: for a tibia it applies.
    tibia = recall(
        profile("tibia", [(SAG, (1, 2, 0))]),
        taught,
        context("tibia", MAP_RELATION, ["femur"]),
    )
    assert negative_row(tibia, "n2")["applies"] is True


# ------------------------------------------------- what sets an own case's bar


def test_a_structural_bone_is_held_back_by_another_tissue_never_by_the_readers_bones():
    query = profile("femur", [(SAG, (3, 1, 0))])
    reader = context("femur", STRUCTURAL_READER)
    patella = ("p1", "patella", "sp", [(SAG, (3, 1, 0))])
    muscle = ("m1", "medial_gastrocnemius", "sm", [(SAG, (0, 0, 3))])
    close_muscle = ("m2", "medial_gastrocnemius", "sm2", [(SAG, (6, 1, 0))])
    femur = ("f1", "femur", "sf", [(SAG, (3, 0, 0))])
    # Unconditioned, the patella's case wins: it resembles this reading most.
    taught = memory((femur, patella, muscle))
    assert recall(query, taught, None)["identity"] == "patella"
    # The reader established the femur, in a study with no patella found: the patella's
    # case never sets the femur's bar, and the femur's own case speaks above the muscle.
    result = recall(query, taught, reader)
    assert (result["outcome"], result["appearance"]) == (
        ESTABLISHED_BY_STRUCTURE,
        "supports",
    )
    [row] = result["cases"]
    assert row["envelope"]["opposing_identities"] == ["medial_gastrocnemius"]
    assert result["also_resembles"][0]["identity"] == "patella"
    # A muscle case close to the femur's own raises its bar: the appearance is silent.
    held = recall(query, memory((femur, patella, muscle, close_muscle)), reader)
    assert (held["outcome"], held["appearance"]) == (ESTABLISHED_BY_STRUCTURE, "silent")
    # Placed by the map with the patella open, the patella's case does set the bar.
    placed = recall(query, taught, context("femur", MAP_RELATION, ["patella"]))
    assert (placed["outcome"], placed["appearance"]) == ("appearance_silent", "silent")


def test_per_identity_maxima_reproduce_the_overall_envelope():
    seeds = (
        ("f1", "femur", "s1", [(SAG, (3, 0, 0)), (COR, (1, 1, 1))]),
        ("f2", "femur", "s2", [(SAG, (2, 1, 0))]),
        ("t1", "tibia", "s3", [(SAG, (1, 1, 1)), (COR, (0, 2, 1))]),
        ("t2", "tibia", "s4", [(COR, (2, 0, 1))]),
        ("m1", "medial_gastrocnemius", "s5", [(SAG, (2, 2, 0)), (COR, (2, 0, 1))]),
        ("m2", "medial_gastrocnemius", "s6", [(SAG, (3, 0, 1))]),
    )
    prepared = prepare_identity(memory(seeds))
    compared = 0
    for overall, table in zip(prepared._envelopes, prepared._opposition, strict=True):
        assert set(overall) == set(table)
        for key, entry in overall.items():
            rebuilt = _envelope_over(table[key], frozenset(table[key]))
            assert Fraction(rebuilt["num"], rebuilt["den"]) == Fraction(
                entry["num"], entry["den"]
            )
            assert sorted(rebuilt["opponents"]) == sorted(entry["opponents"])
            assert rebuilt["count"] == entry["count"]
            compared += 1
    assert compared >= len(seeds)


def test_the_prior_leaves_every_identity_open_and_records_the_unconditioned_one():
    taught = memory(PLAIN_SEEDS)
    prior = context("femur", PRIOR_ONLY)
    like_tibia = recall(profile("femur", [(SAG, (0, 0, 3))]), taught, prior)
    assert (like_tibia["identity"], like_tibia["outcome"]) == (
        "femur",
        "appearance_silent",
    )
    assert like_tibia["identity_state"] == "unconditioned"
    assert like_tibia["unconditioned_identity"] == "tibia"
    assert like_tibia["unconditioned_speaking_identities"] == ["tibia"]
    like_femur = recall(profile("femur", [(SAG, (3, 0, 0))]), taught, prior)
    assert like_femur["outcome"] == APPEARANCE_SUPPORTS
    assert like_femur["unconditioned_identity"] == "femur"
    assert like_femur["schema"] == RECALL_CONTEXT_SCHEMA


def test_a_placement_with_nothing_left_open_is_placement_only():
    taught = memory(PLAIN_SEEDS)
    result = recall(
        profile("femur", [(SAG, (3, 0, 0))]), taught, context("femur", MAP_RELATION)
    )
    assert (result["outcome"], result["appearance"], result["reason"]) == (
        "placement_only",
        "uncalibrated",
        "no_open_alternative",
    )
    [row] = result["cases"]
    assert row["envelope_status"] == "no_open_alternative"
    opened = recall(
        profile("femur", [(SAG, (3, 0, 0))]),
        taught,
        context("femur", MAP_RELATION, ["tibia"]),
    )
    assert opened["outcome"] == APPEARANCE_SUPPORTS


# ---------------------------------------------------- the context builder


def _anchored(subject: str) -> dict:
    return {
        "status": "proposal",
        "profile": {"banks": {"b": [1, 0, 0]}},
        "regions": [{"series_uid": "s-sag", "window": list(WINDOW)}],
        "territories": [
            {
                "origin": "anchor_structure",
                "subject": subject,
                "provenance": {
                    "producer": "knee.diagnosis.squint_anchors.find_anchors/v1",
                    "derivation": "middle_slice_named_by_the_established_rule",
                    "rule": "knee.objects.assignments.assign_plane",
                    "middle_slice_code": "identified",
                    "partner": "none_of_the_other_sequence",
                    "scale": "native",
                },
            }
        ],
        "evidence": {
            "source": "current_study_structural_anchor",
            "location_route": "structural_anchor",
            "anchor": {"status": "partial", "code": "valid"},
        },
    }


def _placed(subject: str, *origins: str, route=None, window=WINDOW, **evidence) -> dict:
    origins = origins or ("anatomical_relation",)
    return {
        "status": "proposal",
        "profile": {"banks": {"b": [1, 0, 0]}},
        "regions": [{"series_uid": "s-sag", "window": list(window)} for _ in origins],
        "territories": [{"origin": origin, "subject": subject} for origin in origins],
        "evidence": {
            "location_route": route or "anatomical_relation_from_structural_anchors",
            **evidence,
        },
    }


def _candidates(*windows, uid="s-sag", contradicted=()) -> dict:
    return {
        "candidate_territories": {
            uid: {"candidate_object_windows": [list(window) for window in windows]}
        },
        "anatomical_sanity_checks": [
            {"series_uid": uid, "window": list(window), "status": "contradicted"}
            for window in contradicted
        ],
    }


def test_each_basis_is_read_from_the_locators_own_record():
    contexts = squint_pipeline._identity_contexts(
        {
            "femur": _anchored("femur"),
            "tibia": _placed("tibia"),
            "joint": _placed("joint", "anatomical_relation", "fallback_location"),
            "patella": _placed("patella", "fallback_location"),
            "fibula": _placed("fibula", route="existing_finite_route"),
            "mcl": {"status": "located", "profile": {"banks": {"b": [1, 0, 0]}}},
            "acl": {
                "status": "unresolved_missing_reading",
                "profile": None,
                "regions": [],
            },
        }
    )
    assert "acl" not in contexts  # an object the locator did not locate has none
    found = {
        subject: (item["basis"], item["supporting_observations"]["reason"])
        for subject, item in contexts.items()
    }
    assert found == {
        "femur": (STRUCTURAL_READER, "located_by_its_structural_anchor"),
        "tibia": (MAP_RELATION, "placed_from_established_structural_anchors"),
        # One region placed by the map makes the object a placement.
        "joint": (MAP_RELATION, "placed_from_established_structural_anchors"),
        "patella": (PRIOR_ONLY, "leg_frame_prior_only"),
        "fibula": (PRIOR_ONLY, "no_usable_structural_anchor"),
        "mcl": (PRIOR_ONLY, "no_structural_placement_recorded"),
    }
    assert {subject: item["support"] for subject, item in contexts.items()} == {
        "femur": RESOLVED_SUPPORT,
        "tibia": PROPOSED_PLACES,
        "joint": PROPOSED_PLACES,
        "patella": PROPOSED_PLACES,
        "fibula": PROPOSED_PLACES,
        "mcl": SUPPORT_UNRECORDED,
    }
    for item in contexts.values():
        assert item["schema"] == CONTEXT_SCHEMA
        assert item["conditioning"] == CONDITIONING[item["basis"]]


def test_the_reader_removes_its_other_bones_found_or_not_and_a_placement_the_found_ones():
    contexts = squint_pipeline._identity_contexts(
        {"femur": _anchored("femur"), "tibia": _placed("tibia")}
    )
    # No patella or fibula was located here: the reader still tells them apart.
    assert contexts["femur"]["removed_by_structure"] == ["fibula", "patella", "tibia"]
    assert contexts["tibia"]["removed_by_structure"] == ["femur"]
    alone = squint_pipeline._identity_contexts({"tibia": _placed("tibia")})
    assert alone["tibia"]["removed_by_structure"] == []
    prior = squint_pipeline._identity_contexts(
        {"mcl": _placed("mcl", "fallback_location")}
    )
    assert prior["mcl"]["removed_by_structure"] == []


def test_open_alternatives_are_the_overlapping_proposals_structure_has_not_ruled_out():
    beside = [0, 1, 4, 6, 4, 6]
    objects = {
        "femur": {
            **_anchored("femur"),
            "evidence": {**_anchored("femur")["evidence"], **_candidates(WINDOW)},
        },
        "tibia": _placed("tibia"),
        "medial_meniscus": _placed(
            "medial_meniscus", window=beside, **_candidates(WINDOW)
        ),
        "mcl": _placed("mcl", window=beside, **_candidates(beside)),
        "pcl": _placed("pcl", window=beside, **_candidates(WINDOW, uid="s-cor")),
        "acl": _placed(
            "acl", window=beside, **_candidates(WINDOW, contradicted=[WINDOW])
        ),
    }
    tibia = squint_pipeline._identity_contexts(objects)["tibia"]
    # The meniscus's own window overlaps the tibia's; the established femur is no
    # alternative name; the MCL's lies beside it; the PCL's is in another series; the
    # ACL's own law checks contradicted its overlapping window.
    assert tibia["open_alternatives"] == ["medial_meniscus"]
    assert tibia["alternative_overlaps"] == [
        {
            "subject": "medial_meniscus",
            "series_uid": "s-sag",
            "region_window": list(WINDOW),
            "overlapping_candidate_windows": 1,
        }
    ]
    assert tibia["law_excluded_alternatives"] == ["acl"]
    assert tibia["law_excluded_overlaps"][0]["law_contradicted_candidate_windows"] == 1
    # Only a placement is conditioned on alternatives.
    femur = squint_pipeline._identity_contexts(objects)["femur"]
    assert femur["open_alternatives"] == [] and "alternative_overlaps" not in femur


def test_a_set_aside_anchors_reversed_relation_is_a_contradiction_and_a_reader_conflict_is_not():
    reversed_sanity = {
        "schema": "knee.object-anatomical-sanity/v1",
        "status": "contradicted",
        "windows": [
            {
                "window": list(WINDOW),
                "series_uid": "s-sag",
                "checks": [
                    {
                        "rule_id": "authored:femur:superior_to:tibia",
                        "relation": "superior_to",
                        "axis": "z",
                        "result": "reversed_strictly_before",
                        "candidate_subject": "tibia",
                        "reference_subject": "femur",
                    }
                ],
            }
        ],
    }
    set_aside = _placed(
        "tibia",
        unanchored_bone={
            "status": "conflict",
            "code": "anatomical_relation_conflict",
            "anatomical_sanity": reversed_sanity,
        },
    )
    [row] = squint_pipeline._identity_contexts({"tibia": set_aside})["tibia"][
        "contradictions"
    ]
    assert (row["scope"], row["result"], row["reference_subject"]) == (
        "set_aside_structural_anchor",
        "reversed_strictly_before",
        "femur",
    )
    # The reader's own cross-view disagreement is not a law observation.
    reader_conflict = _placed(
        "tibia",
        unanchored_bone={
            "status": "conflict",
            "code": "valid",
            "conflicts": [
                {"code": "the_other_views_section_lies_mostly_in_another_territory"}
            ],
        },
    )
    assert (
        squint_pipeline._identity_contexts({"tibia": reader_conflict})["tibia"][
            "contradictions"
        ]
        == []
    )


# ------------------------------------------- one comparison over every scale


def fine_bank(view: list[str], role: str = "object") -> str:
    return territory_bank_name(
        dict(
            zip(
                ("orientation", "fluid_sensitive", "fat_suppression"), view, strict=True
            )
        ),
        role,
        "signal",
        "d",
        2.0,
    )


def with_fine(taught: dict, fine: dict) -> dict:
    """The same memory with each named case's object tiles also read at 2 mm."""
    result = copy.deepcopy(taught)
    records = [
        *result["cases"],
        *(result.get("object_identity_cases") or {}).get("cases", ()),
    ]
    for case in records:
        for view, counts in fine.get(case["case_id"], ()):
            case["profile"]["banks"][fine_bank(view)] = list(counts)
    return result


def joint_query(subject: str, coarse, finer, view=SAG) -> dict:
    query = profile(subject, [(SAG, coarse)])
    query["banks"][fine_bank(view)] = list(finer)
    return query


# Femur and tibia seeds and a sagittal "not femur" reject, at both scales: at 10 mm the
# reject (2,1,0) still mixes bone with the soft tissue it named; at 2 mm it is that soft
# tissue (0,15,0), and the femur seed is bone (15,0,0).
JOINT = with_fine(
    memory(
        (
            ("f1", "femur", "sf", [(SAG, (3, 1, 0))]),
            ("t1", "tibia", "st", [(SAG, (0, 0, 3))]),
        ),
        [{**NOT_FEMUR, "by_view": [(SAG, (2, 1, 0))]}],
    ),
    {
        "f1": [(SAG, (15, 0, 0))],
        "t1": [(SAG, (0, 0, 15))],
        "n1": [(SAG, (0, 15, 0))],
    },
)


def test_the_squint_view_is_unchanged_and_the_joint_view_names_its_bank_set():
    squint = prepare_identity(JOINT)
    joint = prepare_identity(JOINT, scale=JOINT_SCALE)
    assert "scale" not in squint and joint["scale"] == JOINT_SCALE
    assert squint["source_pin"] != joint["source_pin"]
    assert (preparation_scale(squint), preparation_scale(joint)) == (
        SQUINT_SCALE,
        JOINT_SCALE,
    )
    # The squint scale reads exactly the banks it read before scales.
    assert (
        squint["source_pin"]
        == prepare_identity(JOINT, scale=SQUINT_SCALE)["source_pin"]
    )
    # A finer scale alone is no identity bank set; a view is used only at its own set.
    assert prepare_identity(JOINT, scale="2mm") == {
        "outcome": "invalid_input",
        "reason": "identity_scale_invalid",
    }
    query = joint_query("femur", (2, 1, 0), (15, 0, 0))
    assert recall_identity(
        query,
        JOINT,
        prepared=squint,
        context=context("femur", PRIOR_ONLY),
        scale=JOINT_SCALE,
    ) == {"outcome": "invalid_preparation", "reason": "scale_mismatch"}


def test_one_comparison_over_both_scales_never_a_cosine_per_scale():
    placement = context("femur", MAP_RELATION, ["tibia"])
    query = joint_query("femur", (2, 1, 0), (15, 0, 0))
    joint = recall_identity(
        query,
        JOINT,
        prepared=prepare_identity(JOINT, scale=JOINT_SCALE),
        context=placement,
        scale=JOINT_SCALE,
    )
    [own] = joint["cases"]
    # One dot product and one pair of norms over every bank both sides speak in.
    assert (own["dot"], own["left_norm_sq"], own["right_norm_sq"]) == (
        7 + 225,
        5 + 225,
        10 + 225,
    )
    assert Fraction(
        int(own["squared_cosine"]["numerator"]),
        int(own["squared_cosine"]["denominator"]),
    ) == Fraction(232**2, 230 * 235)
    assert sorted(own["common_speaking_banks"]) == sorted([bank(SAG), fine_bank(SAG)])
    # Before the look the query's 2 mm banks are silent: the comparison is the 10 mm one,
    # against the squint view's own trust radii.
    coarse = profile("femur", [(SAG, (2, 1, 0))])
    squint = recall_identity(coarse, JOINT, context=placement)
    [own] = squint["cases"]
    assert (own["dot"], own["left_norm_sq"], own["right_norm_sq"]) == (7, 5, 10)
    assert own["envelope"] is not None
    # The joint view has no trust radius for a bank set it was not prepared over.
    unread = recall_identity(
        coarse,
        JOINT,
        prepared=prepare_identity(JOINT, scale=JOINT_SCALE),
        context=placement,
        scale=JOINT_SCALE,
    )
    [own] = unread["cases"]
    assert own["envelope"] is None


def test_a_contest_is_settled_by_what_applies_never_by_a_margin():
    placement = context("femur", MAP_RELATION, ["tibia"])
    coarse = profile("femur", [(SAG, (2, 1, 0))])
    squint = recall_identity(coarse, JOINT, context=placement)
    assert (squint["outcome"], squint["applicable_negative_case_ids"]) == (
        SIGNED_CONFLICT,
        ["n1"],
    )
    # No finer reading: unsettled, every squint-scale negative not compared.
    assert squint_contest_resolution(squint, None)["status"] == (
        UNRESOLVED_NO_FINER_READING
    )
    assert squint_contest_resolution(squint, None)["negatives"] == {
        "n1": NEGATIVE_NOT_COMPARED
    }
    view = prepare_identity(JOINT, scale=JOINT_SCALE)

    def after(finer):
        return recall_identity(
            joint_query("femur", (2, 1, 0), finer),
            JOINT,
            prepared=view,
            context=placement,
            scale=JOINT_SCALE,
            resolve_negatives=squint["applicable_negative_case_ids"],
        )

    bone = squint_contest_resolution(squint, after((15, 0, 0)))
    assert (bone["status"], bone["squint_scale_resemblance_only"]) == (
        RESOLVED_BY_FINER_READING,
        ["n1"],
    )
    soft = squint_contest_resolution(squint, after((0, 15, 0)))
    assert (soft["status"], soft["resolved_outcome"], soft["negatives"]) == (
        CONTESTED_AFTER_FINER_READING,
        SIGNED_CONFLICT,
        {"n1": NEGATIVE_APPLIES},
    )
    # A squint-scale recall handed over as the finer one is refused, by name.
    refused = squint_contest_resolution(squint, squint)
    assert refused["status"] == FINER_RECALL_INVALID
    # A recall that is no contest asks no resolution.
    plain = recall_identity(
        profile("femur", [(SAG, (3, 1, 0))]), JOINT, context=placement
    )
    assert plain["outcome"] == APPEARANCE_SUPPORTS
    assert squint_contest_resolution(plain, None) == {"status": None}
