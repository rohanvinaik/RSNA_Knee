"""The teaching tool must preserve meanings before any scoring is attempted."""

import copy
import json
from pathlib import Path

import pytest

from knee.diagnosis.squint_interfaces import TERRITORY_PROCEDURE
from scripts.grounded_teaching import compare_references, validate_categories

PROFILE = {
    "schema": "knee.squint-profile/v1",
    "source": {"procedure": TERRITORY_PROCEDURE},
}


def test_named_difference_is_retained_without_diagnostic_labels():
    left = {
        **PROFILE,
        "subject": "femur",
        "banks": {"marrow": [3, 0, 0]},
    }
    right = {
        **PROFILE,
        "subject": "femur",
        "banks": {"marrow": [0, 0, 3]},
    }
    result = compare_references(left, right)
    assert result["outcome"] == "distinct_measured_profiles"
    assert result["named_differences"] == [
        {"bank": "marrow", "normal": [3, 0, 0], "diagnosed": [0, 0, 3]}
    ]
    assert "condition_calls" not in left


def test_size_multiplier_cannot_masquerade_as_a_directional_difference():
    left = {
        **PROFILE,
        "subject": "fluid",
        "banks": {"reading": [2, 3, 4]},
    }
    right = {
        **PROFILE,
        "subject": "fluid",
        "banks": {"reading": [4, 6, 8]},
    }
    result = compare_references(left, right)
    assert result["outcome"] == "parallel_profiles"
    assert result["named_differences"] == []


def test_unread_bank_does_not_teach_normality():
    left = {**PROFILE, "subject": "acl", "banks": {}}
    right = {
        **PROFILE,
        "subject": "acl",
        "banks": {"reading": [0, 0, 3]},
    }
    assert compare_references(left, right)["outcome"] == "silent"


def teaching_inputs():
    spec = json.loads(Path("docs/teaching/seed_categories.json").read_text())
    rows = {}
    for category in spec["categories"]:
        for side, sign in (("normal", "0"), ("diagnosed", "1")):
            uid = category[side]["study_uid"]
            rows.setdefault(uid, {})[category["question"]] = sign
    return spec, rows


def test_explicit_opposing_source_calls_are_accepted():
    spec, rows = teaching_inputs()
    validate_categories(spec, rows)


def test_blank_official_label_cannot_teach_a_normal_case():
    spec, rows = teaching_inputs()
    uid = spec["categories"][0]["normal"]["study_uid"]
    rows[uid]["ACL"] = ""
    with pytest.raises(ValueError, match="independent_condition_call_mismatch"):
        validate_categories(spec, rows)


def test_reversed_source_call_cannot_teach_the_desired_category():
    spec, rows = teaching_inputs()
    uid = spec["categories"][0]["diagnosed"]["study_uid"]
    rows[uid]["ACL"] = "0"
    with pytest.raises(ValueError, match="independent_condition_call_mismatch"):
        validate_categories(spec, rows)


def test_duplicate_question_cannot_fill_a_missing_category():
    spec, rows = teaching_inputs()
    spec["categories"][-1] = copy.deepcopy(spec["categories"][0])
    with pytest.raises(ValueError, match="twelve_unique_questions_required"):
        validate_categories(spec, rows)


def test_uninspected_support_cannot_be_promoted_by_a_label():
    spec, rows = teaching_inputs()
    spec["categories"][0]["diagnosed"]["visual_reading"] = ""
    with pytest.raises(ValueError, match="visual_observation_required"):
        validate_categories(spec, rows)


def test_nonfinite_teaching_polygon_is_refused():
    spec, rows = teaching_inputs()
    spec["categories"][0]["normal"]["polygon_xy"][0][0] = float("nan")
    with pytest.raises(ValueError, match="visual_observation_required"):
        validate_categories(spec, rows)


def test_null_specification_is_refused_with_a_named_code():
    with pytest.raises(ValueError, match="teaching_schema_invalid"):
        validate_categories(None, {})


def test_incremental_batch_accepts_a_named_subset_without_all_twelve_pairs():
    spec, rows = teaching_inputs()
    spec["categories"] = spec["categories"][:1]
    spec["case_namespace"] = "reviewed-cohort-batch"
    validate_categories(spec, rows, require_all_questions=False)
    with pytest.raises(ValueError, match="twelve_unique_questions_required"):
        validate_categories(spec, rows)


def test_incremental_batch_still_requires_independent_opposing_calls():
    spec, rows = teaching_inputs()
    spec["categories"] = spec["categories"][:1]
    spec["case_namespace"] = "reviewed-cohort-batch"
    rows[spec["categories"][0]["diagnosed"]["study_uid"]]["ACL"] = "0"
    with pytest.raises(ValueError, match="independent_condition_call_mismatch"):
        validate_categories(spec, rows, require_all_questions=False)


def test_incremental_batch_cannot_collide_with_initial_reference_names():
    spec, rows = teaching_inputs()
    spec["categories"] = spec["categories"][:1]
    with pytest.raises(ValueError, match="incremental_case_namespace_required"):
        validate_categories(spec, rows, require_all_questions=False)


def test_incremental_batch_cannot_be_empty_or_redefine_an_unknown_question():
    spec, rows = teaching_inputs()
    spec["case_namespace"] = "reviewed-cohort-batch"
    spec["categories"] = []
    with pytest.raises(ValueError, match="unique_known_questions_required"):
        validate_categories(spec, rows, require_all_questions=False)
    spec, rows = teaching_inputs()
    spec["case_namespace"] = "reviewed-cohort-batch"
    spec["categories"][0]["question"] = "Invented condition"
    with pytest.raises(ValueError, match="unique_known_questions_required"):
        validate_categories(spec, rows, require_all_questions=False)
