"""Both signed identity buckets remain audible after role alternatives disappear.

An absent overlapping role proposal is not an identity observation. Positive
recognition still needs a measured empirical envelope over the asserted support;
the context ring, a fabricated zero, or another bone's name cannot supply it.
"""

from __future__ import annotations

import copy

import pytest
from test_squint_identity_context import COR, SAG, bank, context, memory, profile
from test_squint_identity_growth import candidate, plausible, unknown

from knee.diagnosis.squint_identity import (
    APPEARANCE_OPPOSED,
    APPEARANCE_SUPPORTS,
    JOINT_SCALE,
    MAP_RELATION,
    SIGNED_CONFLICT,
    prepare_identity,
    recall_identity,
)
from knee.diagnosis.squint_identity_growth import admission_decision


def signed_memory(positive=(3, 0, 0), negative=(0, 0, 3), *, ring=()):
    return memory(
        [("positive", "mcl", "positive-study", [(SAG, positive)], ring)],
        [
            {
                "case_id": "negative",
                "subject": "mcl",
                "study_uid": "negative-study",
                "by_view": [(SAG, negative)],
                "ring": ring,
                "views": [SAG],
            }
        ],
    )


def test_empty_role_alternatives_hear_a_positive_against_actual_signed_countercases():
    result = recall_identity(
        profile("mcl", [(SAG, (3, 0, 0))]),
        signed_memory(),
        context=context("mcl", MAP_RELATION),
    )
    assert result["outcome"] == APPEARANCE_SUPPORTS
    assert result["speaking_case_ids"] == ["positive"]
    assert result["applicable_negative_case_ids"] == []
    [row] = result["cases"]
    assert row["common_speaking_banks"] == [bank(SAG)]
    assert row["envelope"]["opponent_case_ids"] == ["negative"]
    assert row["envelope"]["comparison_count"] == 1
    # This zero is an actual measured disjoint countercase, not a default.
    assert row["envelope"]["numerator"] == "0"
    assert row["calibration_basis"] == "signed_identity_countercases_on_object_support"
    assert row["negative_case_sources"][0]["case_id"] == "negative"
    assert row["negative_case_sources"][0]["study_uid"] == "negative-study"


def test_the_same_signed_question_still_hears_its_negative_and_neither_stays_open():
    opposed = recall_identity(
        profile("mcl", [(SAG, (0, 0, 3))]),
        signed_memory(),
        context=context("mcl", MAP_RELATION),
    )
    assert opposed["outcome"] == APPEARANCE_OPPOSED
    assert opposed["speaking_case_ids"] == []
    assert opposed["applicable_negative_case_ids"] == ["negative"]
    neither = recall_identity(
        profile("mcl", [(SAG, (0, 3, 0))]),
        signed_memory(),
        context=context("mcl", MAP_RELATION),
    )
    assert neither["appearance"] == "silent"
    assert neither["speaking_case_ids"] == []
    assert neither["applicable_negative_case_ids"] == []


def test_the_exact_empirical_boundary_does_not_speak_and_both_signs_keep_conflict():
    equal = recall_identity(
        profile("mcl", [(SAG, (1, 1, 0))]),
        signed_memory((1, 0, 0), (1, 1, 0)),
        context=context("mcl", MAP_RELATION),
    )
    [row] = equal["cases"]
    assert row["speaks"] is False
    assert row["squared_cosine"]["numerator"] == "1"
    assert row["squared_cosine"]["denominator"] == "2"
    assert row["envelope"]["numerator"] == "1"
    assert row["envelope"]["denominator"] == "2"
    conflict = recall_identity(
        profile("mcl", [(SAG, (2, 1, 1))]),
        signed_memory((2, 1, 0), (2, 0, 1)),
        context=context("mcl", MAP_RELATION),
    )
    assert conflict["outcome"] == SIGNED_CONFLICT
    assert conflict["speaking_case_ids"] == ["positive"]
    assert conflict["applicable_negative_case_ids"] == ["negative"]


@pytest.mark.parametrize(
    "missing", ["absent", "view", "procedure", "excluded", "context_only"]
)
def test_missing_or_incompatible_signed_calibration_never_becomes_a_zero_floor(missing):
    taught = signed_memory()
    kwargs = {}
    if missing == "absent":
        taught = memory([("positive", "mcl", "positive-study", [(SAG, (3, 0, 0))])])
    elif missing == "view":
        negative = taught["object_identity_cases"]["cases"][0]
        negative["profile"] = profile("mcl", [(COR, (0, 0, 3))])
        taught["object_identity_teaching"]["calls"][-1]["views"] = [COR]
        taught["object_identity_teaching"]["negative_views"]["negative"] = [COR]
    elif missing == "procedure":
        taught["object_identity_cases"]["cases"][0]["profile"]["source"][
            "procedure"
        ] = "incompatible"
    elif missing == "excluded":
        kwargs["exclude_study_uid"] = "negative-study"
    else:
        taught["object_identity_cases"]["cases"][0]["profile"] = profile(
            "mcl", [], [(SAG, (0, 0, 3))]
        )
    result = recall_identity(
        profile("mcl", [(SAG, (3, 0, 0))]),
        taught,
        context=context("mcl", MAP_RELATION),
        **kwargs,
    )
    assert result["outcome"] == "placement_only"
    assert result["appearance"] == "uncalibrated"
    [row] = result["cases"]
    assert row["speaks"] is False and row["envelope"] is None
    assert row["calibration_status"] == "no_compatible_identity_negative_case"


def test_context_ring_neither_manufactures_nor_erases_positive_support():
    taught = signed_memory(ring=[(SAG, (0, 0, 300))])
    correct = recall_identity(
        profile("mcl", [(SAG, (3, 0, 0))], [(SAG, (300, 0, 0))]),
        taught,
        context=context("mcl", MAP_RELATION),
    )
    wrong = recall_identity(
        profile("mcl", [(SAG, (0, 0, 3))], [(SAG, (0, 0, 300))]),
        taught,
        context=context("mcl", MAP_RELATION),
    )
    assert correct["outcome"] == APPEARANCE_SUPPORTS
    assert wrong["outcome"] == APPEARANCE_OPPOSED
    for result in (correct, wrong):
        assert result["cases"][0]["common_speaking_banks"] == [bank(SAG)]
    ring_only = recall_identity(
        profile("mcl", [], [(SAG, (0, 0, 300))]),
        taught,
        context=context("mcl", MAP_RELATION),
    )
    assert ring_only["speaking_case_ids"] == []
    assert ring_only["outcome"] != APPEARANCE_SUPPORTS


@pytest.mark.parametrize(
    "exclusion_field", ["removed_by_structure", "law_excluded_alternatives"]
)
def test_a_countercase_whose_asserted_alternative_was_removed_cannot_calibrate(
    exclusion_field,
):
    taught = signed_memory()
    taught["object_identity_teaching"]["calls"][-1]["also_positive"] = [
        {"identity": "femur", "views": [SAG]}
    ]
    observed_context = context("mcl", MAP_RELATION)
    observed_context[exclusion_field] = ["femur"]
    result = recall_identity(
        profile("mcl", [(SAG, (3, 0, 0))]),
        taught,
        context=observed_context,
    )
    assert result["outcome"] == "placement_only"
    assert result["cases"][0]["envelope"] is None


def test_an_unproposed_alternative_is_not_exclusion_for_either_signed_bucket():
    taught = signed_memory()
    taught["object_identity_teaching"]["calls"][-1]["also_positive"] = [
        {"identity": "femur", "views": [SAG]}
    ]
    unknown_alternative = context("mcl", MAP_RELATION)
    assert unknown_alternative["open_alternatives"] == []
    assert unknown_alternative["removed_by_structure"] == []
    positive = recall_identity(
        profile("mcl", [(SAG, (3, 0, 0))]), taught, context=unknown_alternative
    )
    negative = recall_identity(
        profile("mcl", [(SAG, (0, 0, 3))]), taught, context=unknown_alternative
    )
    assert positive["outcome"] == APPEARANCE_SUPPORTS
    assert positive["cases"][0]["envelope"]["opponent_case_ids"] == ["negative"]
    assert negative["outcome"] == APPEARANCE_OPPOSED
    assert negative["applicable_negative_case_ids"] == ["negative"]


def test_another_identitys_reject_is_not_this_questions_calibration():
    taught = signed_memory()
    taught["object_identity_cases"]["cases"][0]["subject"] = "acl"
    taught["object_identity_cases"]["cases"][0]["profile"]["subject"] = "acl"
    result = recall_identity(
        profile("mcl", [(SAG, (3, 0, 0))]),
        taught,
        context=context("mcl", MAP_RELATION),
    )
    assert result["outcome"] == "placement_only"
    assert result["cases"][0]["envelope"] is None


def test_identical_other_bone_appearance_does_not_raise_the_signed_identity_bar():
    taught = memory(
        [
            ("positive", "femur", "positive-study", [(SAG, (3, 0, 0))]),
            ("other-bone", "tibia", "other-study", [(SAG, (3, 0, 0))]),
        ],
        [
            {
                "case_id": "negative",
                "subject": "femur",
                "study_uid": "negative-study",
                "by_view": [(SAG, (0, 0, 3))],
                "views": [SAG],
            }
        ],
    )
    result = recall_identity(
        profile("femur", [(SAG, (3, 0, 0))]),
        taught,
        context=context("femur", MAP_RELATION),
    )
    assert result["identity"] == "femur"
    assert result["outcome"] == APPEARANCE_SUPPORTS
    assert result["cases"][0]["envelope"]["opponent_case_ids"] == ["negative"]


def test_nonempty_role_competition_remains_the_existing_path():
    taught = signed_memory()
    taught["cases"].append(
        {
            **copy.deepcopy(taught["cases"][0]),
            "case_id": "other",
            "subject": "acl",
            "study_uid": "other-study",
        }
    )
    taught["cases"][-1]["profile"]["subject"] = "acl"
    taught["object_identity_teaching"]["confirmed_case_ids"].append("other")
    taught["object_identity_teaching"]["calls"].append(
        {"candidate_id": "other", "call": "confirm"}
    )
    result = recall_identity(
        profile("mcl", [(SAG, (3, 0, 0))]),
        taught,
        context=context("mcl", MAP_RELATION, ["acl"]),
    )
    assert result["appearance"] == "silent"
    assert "calibration_basis" not in result["cases"][0]


def test_joint_scale_uses_one_signed_comparison_over_both_object_scale_banks():
    taught = signed_memory((3, 0, 0), (3, 0, 0))
    fine = bank(SAG).replace("scale=10mm", "scale=2mm")
    taught["cases"][0]["profile"]["banks"][fine] = [0, 3, 0]
    taught["object_identity_cases"]["cases"][0]["profile"]["banks"][fine] = [0, 0, 3]
    query = profile("mcl", [(SAG, (3, 0, 0))])
    query["banks"][fine] = [0, 3, 0]
    coarse = recall_identity(query, taught, context=context("mcl", MAP_RELATION))
    assert coarse["speaking_case_ids"] == []
    result = recall_identity(
        query, taught, scale=JOINT_SCALE, context=context("mcl", MAP_RELATION)
    )
    assert result["outcome"] == APPEARANCE_SUPPORTS
    assert set(result["cases"][0]["common_speaking_banks"]) == {bank(SAG), fine}
    assert result["cases"][0]["envelope"]["numerator"] == "81"
    assert result["cases"][0]["envelope"]["denominator"] == "324"


def test_signed_positive_recognition_still_needs_affirmative_anatomy_for_growth():
    taught = signed_memory()
    for anatomy, expected in [
        (unknown("mcl"), "proposal"),
        (plausible("mcl"), "admitted"),
    ]:
        item = candidate(
            "new-study",
            "mcl",
            [(SAG, (3, 0, 0))],
            anatomy,
            context("mcl", MAP_RELATION),
        )
        scored = admission_decision(item, taught)
        assert scored["recall"]["outcome"] == APPEARANCE_SUPPORTS
        assert scored["decision"]["state"] == expected
    assert prepare_identity(taught)["outcome"] == "prepared"
