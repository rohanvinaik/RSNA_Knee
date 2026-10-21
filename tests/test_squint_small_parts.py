"""Small parts decide only after being read over their own outline.

Rohan, 2026-10-21, agreeing to the lead's proposal: «Agreed, let's try it, see
how AI folds in to efficiency with it built in» (SQUINT_TRAINING_BUILD §10).
Stored cases are read over each part's saved outline. A new scan's small part
read over its expected area is mostly neighbouring tissue, so comparing the two
is not like with like: until the part is read over its own outline, its recall
grades within "open" and never assigns or defeats. Large parts are unaffected.
"""

from __future__ import annotations

import pytest

from knee.diagnosis.squint_contracts import combine_condition
from knee.diagnosis.squint_pipeline import (
    SMALL_PARTS,
    _decision_scope,
    _profile_origins,
)


def _record(outcome: str, **extra) -> dict:
    return {"outcome": outcome, "case_terms": [], "vetoed_answers": [], **extra}


def _profile(*origins: str, merged: bool = False) -> dict:
    sources = [{"territory": {"origin": origin}} for origin in origins]
    if merged:
        return {"source": {"lineage": sources}}
    return {"source": sources[0] if sources else {}}


@pytest.mark.parametrize("outcome", ["present", "absent"])
def test_a_small_part_not_read_over_its_outline_grades_but_never_decides(outcome):
    decided = combine_condition(
        "Medial Meniscus", {"medial_meniscus": _record(outcome)}
    )
    graded = combine_condition(
        "Medial Meniscus",
        {"medial_meniscus": _record(outcome, decision_scope="grade_only")},
    )
    assert decided["outcome"] in ("assigned", "defeated")
    assert graded["outcome"] == "open"
    # The open question asks for the bounded look that reads the part's outline.
    assert [
        (r["subject"], r["kind"], r["reason"]) for r in graded["observation_requests"]
    ] == [("medial_meniscus", "bounded_zoom", "small_part_not_read_over_own_outline")]


def test_the_same_record_still_decides_when_read_over_its_own_outline():
    finding = combine_condition(
        "Medial Meniscus",
        {"medial_meniscus": _record("present", decision_scope="decide")},
    )
    assert finding["outcome"] == "assigned"


@pytest.mark.parametrize(
    ("profile", "expected"),
    [
        (_profile("anatomical_relation"), "grade_only"),
        (_profile("anchor_structure"), "grade_only"),
        (_profile("fallback_location"), "grade_only"),
        (_profile(), "grade_only"),
        (None, "grade_only"),
        (_profile("teacher_support"), "decide"),
        (_profile("residual_native_support"), "decide"),
        (_profile("residual_native_support", merged=True), "decide"),
        # An own-outline reading merged with an expected-area one is still mixed.
        (
            _profile("anatomical_relation", "residual_native_support", merged=True),
            "grade_only",
        ),
    ],
)
def test_small_part_scope_follows_every_origin_it_was_read_from(profile, expected):
    assert _decision_scope("medial_meniscus", profile) == expected


@pytest.mark.parametrize(
    "subject", ["femur", "tibia", "patella", "joint", "prefemoral_fat_pad"]
)
def test_large_parts_are_compared_at_squint_scale(subject):
    assert subject not in SMALL_PARTS
    assert _decision_scope(subject, _profile("anatomical_relation")) == "decide"


def test_the_small_parts_are_the_ones_rohan_agreed():
    assert SMALL_PARTS == {
        "medial_meniscus",
        "lateral_meniscus",
        "acl",
        "pcl",
        "mcl",
        "femoral_cartilage",
        "tibial_cartilage",
        "patellar_cartilage",
        "trochlear_cartilage",
        "synovium",
        "joint_fluid",
    }


def test_origins_are_read_through_merge_lineage():
    nested = {
        "source": {
            "lineage": [
                {"territory": {"origin": "teacher_support"}},
                {"lineage": [{"territory": {"origin": "residual_native_support"}}]},
            ]
        }
    }
    assert _profile_origins(nested) == {"teacher_support", "residual_native_support"}
