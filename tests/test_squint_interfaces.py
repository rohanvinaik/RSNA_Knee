from __future__ import annotations

import numpy as np

import tests.squint_upgrade_fixtures as fixture
from knee.diagnosis import squint_interfaces as shapes


def test_fixture_leg_map_and_territory_are_valid():
    grid = fixture.series_record()["stack"].median.shape
    assert shapes.leg_map_code(fixture.expected_leg_map(), grid_shape=grid) == "valid"
    assert (
        shapes.territory_code(fixture.teacher_territory(), grid_shape=grid) == "valid"
    )


def test_v1_cutoffs_spend_the_dark_digit_on_air_in_the_fixture():
    """The defect the territory writer must remove, reproduced on the fixture.

    v1 takes its cutoffs over air and leg together. Air fills the lowest third,
    so every tile coded dark is air and the enclosed dark body, which is leg, reads
    middle. Cutoffs taken over the leg alone must let it read dark.
    """
    record = fixture.series_record()
    codes = record["metric_codes"]["signal_median"]
    leg = fixture.expected_leg_map()["codes"]
    dark_body = np.zeros(leg.shape, dtype=np.bool_)
    dark_body[:, 3:5, 3:5] = True
    dark = codes == -1
    assert dark.any()
    assert np.all(leg[dark] == shapes.LEG_OUTSIDE)
    assert np.all(codes[dark_body] == 0)


def test_leg_map_rejects_outside_tile_with_leg_share_and_unknown_codes():
    value = fixture.expected_leg_map()
    value["leg_share"] = value["leg_share"].copy()
    value["leg_share"][0, 0, 0] = 0.5
    assert shapes.leg_map_code(value) == "leg_map_share_contradicts_code"
    value = fixture.expected_leg_map()
    value["codes"] = value["codes"].copy()
    value["codes"][0, 0, 0] = 7
    assert shapes.leg_map_code(value) == "leg_map_code_unknown"
    assert shapes.leg_map_code(fixture.expected_leg_map(), grid_shape=(1, 2, 3)) == (
        "leg_map_shape_mismatch"
    )


def test_measured_territory_needs_support_on_every_object_tile():
    value = fixture.teacher_territory()
    value["object_share"] = value["object_share"].copy()
    value["object_share"][0, 3, 3] = np.nan
    assert shapes.territory_code(value) == "territory_measured_share_missing"
    value["object_share"][0, 3, 3] = 0.0
    assert shapes.territory_code(value) == "territory_object_tile_without_support"
    expected = fixture.teacher_territory()
    expected["origin"] = "anatomical_relation"
    expected["object_share"] = np.full_like(expected["object_share"], np.nan)
    # An anatomical expectation has roles but no measured share.
    assert shapes.territory_code(expected) == "valid"


def test_territory_window_must_fit_the_grid_and_match_the_roles():
    value = fixture.teacher_territory()
    assert (
        shapes.territory_code(value, grid_shape=(1, 8, 8))
        == "territory_window_outside_grid"
    )
    value["tile_window"] = [1, 2, 0, 5, 0, 6]
    assert shapes.territory_code(value) == "territory_roles_invalid"


def test_bank_names_round_trip_and_reject_v1_names():
    name = shapes.territory_bank_name(
        fixture.VIEW, "object", "signal_median", "overview", 10.0
    )
    parsed = shapes.parse_territory_bank_name(name)
    assert parsed is not None
    assert parsed["role"] == "object"
    assert parsed["metric"] == "signal_median"
    assert parsed["scale_mm"] == 10.0
    assert parsed["view"] == ["Coronal", "1", "1"]
    v1 = 'squint/v1/view=["Coronal","1","1"]/metric=signal_median/direction=overview/scale=10mm'
    assert shapes.parse_territory_bank_name(v1) is None


def test_residual_result_measured_needs_its_own_native_territory():
    territory = fixture.teacher_territory()
    territory["origin"] = "residual_native_support"
    result = {
        "schema": shapes.RESIDUAL_RESULT_SCHEMA,
        "code": "measured",
        "subject": "medial_meniscus",
        "lens": "existing_meniscus_rule",
        "territory": territory,
        "profile": {"banks": {}},
        "cost": {"seconds": 0.1},
    }
    assert shapes.residual_result_code(result) == "valid"
    result["territory"] = fixture.teacher_territory()
    assert (
        shapes.residual_result_code(result)
        == "residual_result_territory_origin_invalid"
    )
    unavailable = {
        "schema": shapes.RESIDUAL_RESULT_SCHEMA,
        "code": "procedure_unavailable",
        "subject": "acl",
        "lens": "none_named",
        "cost": {},
    }
    assert shapes.residual_result_code(unavailable) == "valid"


def test_teaching_round_child_must_be_a_new_revision():
    manifest = {
        "schema": shapes.TEACHING_ROUND_SCHEMA,
        "status": "published",
        "parent": {"revision": "r6", "manifest_sha256": "a" * 64},
        "calls": [{"source": "labels:train.csv", "sha256": "b" * 64}],
        "admission": {"admitted": 1},
        "child": {"revision": "r6", "manifest_sha256": "c" * 64},
    }
    assert shapes.teaching_round_code(manifest) == "teaching_round_child_invalid"
    manifest["child"]["revision"] = "r7"
    assert shapes.teaching_round_code(manifest) == "valid"
