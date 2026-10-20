"""Intent: explicit slice-profile declarations must be valid or refused by name.

Positive requirements preserve a valid producer contract, including an explicitly
declared zero status code. Negative requirements prohibit silently accepting
unknown fields, ambiguous status identities, or unmeasured status names. These
tests assert the source contract, independently of generated characterization.
"""

import pytest

from knee.encoding.slice_profile_adapter import slice_profile_layout_problem


def declaration():
    return {
        "family": "native_slice_profile_values",
        "support": "a3_femur_profile_area_mm2",
        "values": "a3_femur_profile_area_mm2",
        "status": "a3_femur_profile_status",
        "status_codes": {"body": 2},
        "measured_status_names": ["body"],
        "unit": "mm2",
        "scope": "native_series_profile",
    }


def test_explicit_valid_producer_contract_must_be_accepted():
    assert slice_profile_layout_problem(declaration()) is None


def test_explicit_zero_status_code_must_not_be_confused_with_unavailable():
    source = declaration()
    source["status_codes"] = {"measured": 0}
    source["measured_status_names"] = ["measured"]
    assert slice_profile_layout_problem(source) is None


def test_wrong_family_must_remain_a_distinct_named_refusal():
    source = declaration()
    source["family"] = "plane_mask"
    assert slice_profile_layout_problem(source) == "unsupported_slice_profile_family"


@pytest.mark.parametrize("field", ["support", "values", "status", "unit", "scope"])
@pytest.mark.parametrize("bad", ["", "  ", 1, False, None])
def test_required_source_meanings_must_not_be_blank_or_other_types(field, bad):
    source = declaration()
    source[field] = bad
    assert slice_profile_layout_problem(source) == "slice_profile_declaration_invalid"


def test_an_extra_undeclared_field_must_not_silently_change_the_contract():
    source = {**declaration(), "invented_selector": "body"}
    assert slice_profile_layout_problem(source) == "slice_profile_declaration_invalid"


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        {"body": False},
        {"body": 2.0},
        {"body": 2, "other": 2},
        {"body": 2, "": 3},
        {"body": 2, 3: 4},
        {"body": 2, "other": None},
    ],
)
def test_status_identities_must_be_named_integers_and_one_to_one(bad):
    source = declaration()
    source["status_codes"] = bad
    assert slice_profile_layout_problem(source) == "slice_profile_declaration_invalid"


@pytest.mark.parametrize(
    "bad",
    [
        None,
        "body",
        [],
        ["body", "body"],
        ["body", "unknown"],
        ["body", 2],
        ["body", []],
    ],
)
def test_measurement_eligibility_must_only_name_unique_declared_statuses(bad):
    source = declaration()
    source["measured_status_names"] = bad
    assert slice_profile_layout_problem(source) == "slice_profile_declaration_invalid"


@pytest.mark.parametrize("bad", [None, 1, "source", [], {}])
def test_a_noncontract_must_never_mean_valid(bad):
    assert slice_profile_layout_problem(bad) == "slice_profile_declaration_invalid"
