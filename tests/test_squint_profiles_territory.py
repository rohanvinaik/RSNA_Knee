from __future__ import annotations

import json
from dataclasses import replace

import numpy as np
import pytest
from pydicom.uid import generate_uid

from knee.diagnosis import squint_interfaces as shapes
from knee.diagnosis import squint_profiles as writer
from tests import squint_upgrade_fixtures as fixture
from tests.test_squint_profiles import _write_dicom, _write_tables


def _bank(role="object", metric="signal_median", direction="overview", scale=10):
    return shapes.territory_bank_name(fixture.VIEW, role, metric, direction, scale)


def _support_at(places):
    territory = fixture.teacher_territory()
    territory["roles"][:] = shapes.ROLE_CONTEXT
    territory["object_share"][:] = np.nan
    for r, c in places:
        territory["roles"][0, r, c] = shapes.ROLE_OBJECT
        territory["object_share"][0, r, c] = 1
    return territory


def test_same_box_different_places_changes_counts_and_box_surrogate_fails():
    series, leg = fixture.series_record(), fixture.expected_leg_map()
    corners = [(2, 2), (2, 5), (5, 2), (5, 5)]
    dark_support = _support_at([*corners, (3, 3)])
    neutral_support = _support_at([*corners, (2, 3)])
    # Both supports have identical extrema, as well as the same read window.
    for territory in (dark_support, neutral_support):
        places = np.argwhere(territory["roles"][0] == shapes.ROLE_OBJECT)
        assert places.min(axis=0).tolist() == [2, 2]
        assert places.max(axis=0).tolist() == [5, 5]
    dark = writer.profile_territory(
        series, dark_support, leg, subject="medial_meniscus"
    )
    neutral = writer.profile_territory(
        series, neutral_support, leg, subject="medial_meniscus"
    )
    assert dark["banks"][_bank()] == [1, 4, 0]
    assert neutral["banks"][_bank()] == [0, 5, 0]
    assert dark["banks"][_bank("context")] == [8, 12, 0]
    assert neutral["banks"][_bank("context")] == [9, 11, 0]
    box = _support_at([(r, c) for r in range(2, 6) for c in range(2, 6)])
    stand_in = writer.profile_territory(series, box, leg, subject="medial_meniscus")
    assert stand_in["banks"][_bank()] == [4, 12, 0]
    assert stand_in["banks"][_bank()] not in (
        dark["banks"][_bank()],
        neutral["banks"][_bank()],
    )


def test_leg_edges_recode_dark_body_without_changing_v1():
    series, leg = fixture.series_record(), fixture.expected_leg_map()
    before = {k: v.copy() for k, v in series["metric_codes"].items()}
    calibration, codes = writer.leg_calibration(series, leg)
    body = (slice(None), *fixture.DARK_BODY)
    assert np.all(series["metric_codes"]["signal_median"][body] == 0)
    assert np.all(codes["signal_median"][body] == -1)
    assert np.all(codes["signal_median"][leg["codes"] == shapes.LEG_OUTSIDE] == -2)
    assert np.all(codes["signal_median"][leg["codes"] == shapes.LEG_MIXED] == -1)
    for metric, record in calibration.items():
        assert record["policy"] == "leg_inside_terciles"
        assert record["available_count"] == record["inside_count"] == 90
        assert record["mixed_count"] == 18
        assert record["writable_count"] == 108
        assert np.array_equal(before[metric], series["metric_codes"][metric])
        assert not codes[metric].flags.writeable
    profile = writer.profile_territory(
        series, fixture.teacher_territory(), leg, subject="medial_meniscus"
    )
    assert profile["banks"][_bank()] == [4, 0, 0]
    assert profile["source"]["procedure"] == shapes.TERRITORY_PROCEDURE


def test_outside_padding_changes_neither_leg_edges_nor_role_counts():
    series, leg, territory = (
        fixture.series_record(),
        fixture.expected_leg_map(),
        fixture.teacher_territory(),
    )
    original = writer.profile_territory(
        series, territory, leg, subject="medial_meniscus"
    )
    original_cal, _ = writer.leg_calibration(series, leg)
    pad = ((0, 0), (2, 2), (2, 2))
    padded = dict(series)
    # Reuse the readings already measured at the original places. Added tiles
    # have arbitrary extreme readings and cannot contribute to the reference.
    padded["metric_values"] = {
        k: np.pad(v, pad, constant_values=1e9)
        for k, v in series["metric_values"].items()
    }
    padded["metric_available"] = {
        k: np.pad(v, pad, constant_values=True)
        for k, v in series["metric_available"].items()
    }
    centres = np.pad(
        series["stack"].centres_lps, (*pad, (0, 0)), constant_values=np.nan
    )
    bounds = np.zeros((12, 12, 4), dtype=np.int64)
    for r, c in np.ndindex(12, 12):
        bounds[r, c] = [r * 20, (r + 1) * 20, c * 20, (c + 1) * 20]
    padded["stack"] = replace(
        series["stack"],
        median=padded["metric_values"]["signal_median"],
        centres_lps=centres,
        bounds_rc=bounds,
    )
    padded_leg = {
        **leg,
        "codes": np.pad(leg["codes"], pad, constant_values=shapes.LEG_OUTSIDE),
        "leg_share": np.pad(leg["leg_share"], pad),
    }
    roles = np.full((1, 10, 10), shapes.ROLE_OUTSIDE_LEG, dtype=np.int8)
    roles[:, 2:8, 2:8] = territory["roles"]
    shares = np.full(roles.shape, np.nan)
    shares[:, 2:8, 2:8] = territory["object_share"]
    padded_territory = {
        **territory,
        "tile_window": [1, 2, 0, 10, 0, 10],
        "roles": roles,
        "object_share": shares,
    }
    current_cal, _ = writer.leg_calibration(padded, padded_leg)
    current = writer.profile_territory(
        padded, padded_territory, padded_leg, subject="medial_meniscus"
    )
    for metric in original_cal:
        assert current_cal[metric]["low"] == original_cal[metric]["low"]
        assert current_cal[metric]["high"] == original_cal[metric]["high"]
    assert current["banks"] == original["banks"]
    assert (
        current["source"]["direction_origin"] == original["source"]["direction_origin"]
    )


def test_measured_middle_is_written_but_unknown_unqueried_and_unavailable_are_silent():
    series, leg = fixture.series_record(), fixture.expected_leg_map()
    territory = _support_at([(2, 2)])
    territory["roles"][territory["roles"] == shapes.ROLE_CONTEXT] = (
        shapes.ROLE_UNQUERIED
    )
    measured = writer.profile_territory(
        series, territory, leg, subject="medial_meniscus"
    )
    assert measured["banks"][_bank()] == [0, 1, 0]
    assert not any("role=context/" in name for name in measured["banks"])
    assert measured["source"]["direction_origin"]["lps"] == [25.0, 3.0, -25.0]
    leg["codes"][1, 2, 2] = shapes.LEG_UNKNOWN
    leg["leg_share"][1, 2, 2] = np.nan
    unknown = writer.profile_territory(
        series, territory, leg, subject="medial_meniscus"
    )
    assert unknown["banks"] == {}
    assert unknown["source"]["status"] == "silent"
    assert (
        unknown["source"]["direction_origin"]["status"] == "object_geometry_unavailable"
    )
    assert writer.cosine_evidence(measured, unknown)["code"] == "silent"
    series["metric_available"]["signal_median"] = np.zeros_like(
        leg["codes"], dtype=bool
    )
    unavailable = writer.profile_territory(
        series, fixture.teacher_territory(), leg, subject="medial_meniscus"
    )
    assert not any("metric=signal_median/" in name for name in unavailable["banks"])


def test_mixed_only_grid_cannot_invent_calibration_or_negative_readings():
    series, leg = fixture.series_record(), fixture.expected_leg_map()
    leg["codes"][:] = shapes.LEG_MIXED
    leg["leg_share"][:] = 0.5
    calibration, codes = writer.leg_calibration(series, leg)
    assert all(record["status"] == "unavailable" for record in calibration.values())
    assert all(np.all(array == -2) for array in codes.values())
    result = writer.profile_territory(
        series, fixture.teacher_territory(), leg, subject="medial_meniscus"
    )
    assert result["banks"] == {}


def test_immutable_metrics_share_one_leg_calibration_and_changed_leg_invalidates_it(
    monkeypatch,
):
    series, leg = fixture.series_record(), fixture.expected_leg_map()
    calls = []
    original = writer.np.quantile

    def observe(*args, **kwargs):
        calls.append(True)
        return original(*args, **kwargs)

    monkeypatch.setattr(writer.np, "quantile", observe)
    first = writer.leg_calibration(series, leg)
    second = writer.leg_calibration(series, leg)
    assert first is second
    assert len(calls) == 6
    leg["codes"][0, 2, 2] = shapes.LEG_UNKNOWN
    leg["leg_share"][0, 2, 2] = np.nan
    third = writer.leg_calibration(series, leg)
    assert third is not first
    assert len(calls) == 12
    assert third[1]["signal_median"][0, 2, 2] == -2


def test_malformed_calibration_and_leg_inputs_are_named():
    series, leg, territory = (
        fixture.series_record(),
        fixture.expected_leg_map(),
        fixture.teacher_territory(),
    )
    calibration, codes = writer.leg_calibration(series, leg)
    bad = {
        **calibration,
        "signal_median": {**calibration["signal_median"], "low": float("nan")},
    }
    with pytest.raises(ValueError, match="squint_leg_calibration_edges_invalid"):
        writer.profile_territory(
            series, territory, leg, subject="medial_meniscus", calibration=bad
        )
    bad_codes = {
        **codes,
        "signal_median": np.full(leg["codes"].shape, -3, dtype=np.int8),
    }
    with pytest.raises(ValueError, match="squint_leg_codes_invalid"):
        writer.profile_territory(
            series,
            territory,
            leg,
            subject="medial_meniscus",
            calibration=(calibration, bad_codes),
        )
    with pytest.raises(ValueError, match="leg_map_schema_invalid"):
        writer.leg_calibration(series, None)
    with pytest.raises(ValueError, match="squint_leg_series_mismatch"):
        writer.leg_calibration(series, {**leg, "series_uid": "other"})
    with pytest.raises(ValueError, match="squint_leg_scale_mismatch"):
        writer.leg_calibration(series, {**leg, "tile_mm": 2.0})


def test_depth_thirds_keep_each_role_and_missing_geometry_does_not_invent_directions():
    series, leg, territory = (
        fixture.series_record(),
        fixture.expected_leg_map(),
        fixture.teacher_territory(),
    )
    territory["tile_window"] = [0, 3, 0, 6, 0, 6]
    territory["roles"] = np.repeat(territory["roles"], 3, axis=0)
    territory["object_share"] = np.repeat(territory["object_share"], 3, axis=0)
    profile = writer.profile_territory(
        series, territory, leg, subject="medial_meniscus"
    )
    assert profile["banks"][_bank()] == [12, 0, 0]
    for direction in ("stack_depth_first", "stack_depth_middle", "stack_depth_last"):
        assert profile["banks"][_bank(direction=direction)] == [4, 0, 0]
        assert sum(profile["banks"][_bank("context", direction=direction)]) == 21
    missing = {
        **series,
        "stack": replace(
            series["stack"],
            centres_lps=np.full_like(series["stack"].centres_lps, np.nan),
        ),
    }
    no_geometry = writer.profile_territory(
        missing, territory, leg, subject="medial_meniscus"
    )
    assert no_geometry["banks"][_bank()] == [12, 0, 0]
    assert not any("patient_lps_" in name for name in no_geometry["banks"])
    assert no_geometry["source"]["direction_origin"]["lps"] is None


def test_shared_calibration_teacher_query_identity_directions_and_provenance():
    series, leg = fixture.series_record(), fixture.expected_leg_map()
    teacher = fixture.teacher_territory()
    query = {**teacher, "origin": "anatomical_relation", "provenance": {"query": True}}
    calibration = writer.leg_calibration(series, leg)
    trained = writer.profile_territory(
        series, teacher, leg, subject="medial_meniscus", calibration=calibration
    )
    recalled = writer.profile_territory(
        series, query, leg, subject="medial_meniscus", calibration=calibration[0]
    )
    assert trained["banks"] == recalled["banks"]
    source = trained["source"]
    assert source["direction_origin"]["lps"] == [40.0, 3.0, -40.0]
    assert source["territory"]["tile_window"] == teacher["tile_window"]
    assert source["territory"]["origin"] == "teacher_support"
    assert source["territory"]["provenance"] == {"fixture": True}
    assert source["territory"]["object_share"][0][3][3] == 0.25
    assert trained["banks"][_bank(direction="patient_lps_left")] == [2, 0, 0]
    assert trained["banks"][_bank(direction="stack_depth_first")] == [4, 0, 0]
    assert _bank(metric="gradient_row", direction="row") in trained["banks"]
    assert _bank(metric="gradient_column", direction="column") in trained["banks"]
    assert source["role_tile_counts"] == {"object": 4, "context": 21}
    json.dumps(trained, allow_nan=False)
    doubled = writer.merge_profiles([trained, recalled], subject="medial_meniscus")
    assert doubled["source"]["procedure"] == shapes.TERRITORY_PROCEDURE
    assert doubled["banks"][_bank()] == [8, 0, 0]
    reverse = writer.merge_profiles([recalled, trained], subject="medial_meniscus")
    assert reverse == doubled
    evidence = writer.cosine_evidence(trained, recalled)
    assert evidence["code"] == "ok"
    assert evidence["dot"] == evidence["left_norm_sq"] == evidence["right_norm_sq"]
    v1 = writer.profile_window(
        series, tuple(teacher["tile_window"]), subject="medial_meniscus"
    )
    assert writer.cosine_evidence(v1, trained) == {
        "code": "identity_mismatch",
        "reason": "procedure_mismatch",
    }
    with pytest.raises(ValueError, match="squint_profile_procedure_mismatch"):
        writer.merge_profiles([v1, trained], subject="medial_meniscus")
    with pytest.raises(ValueError, match="squint_leg_calibration_identity_mismatch"):
        writer.profile_territory(
            series,
            teacher,
            leg,
            subject="medial_meniscus",
            calibration=series["calibration"],
        )


@pytest.mark.parametrize(
    "defect,code",
    [
        ("null", "territory_schema_invalid"),
        ("empty", "territory_window_empty"),
        ("outside", "territory_window_outside_grid"),
        ("roles", "territory_roles_invalid"),
        ("subject", "squint_territory_subject_mismatch"),
        ("series", "squint_territory_series_mismatch"),
    ],
)
def test_malformed_territories_have_named_refusals(defect, code):
    series, leg, territory = (
        fixture.series_record(),
        fixture.expected_leg_map(),
        fixture.teacher_territory(),
    )
    if defect == "null":
        territory = None
    elif defect == "empty":
        territory["tile_window"][1] = 1
    elif defect == "outside":
        territory["tile_window"][1] = 4
    elif defect == "roles":
        territory["roles"] = territory["roles"].astype(float)
    elif defect == "subject":
        territory["subject"] = "femur"
    elif defect == "series":
        territory["series_uid"] = "other"
    with pytest.raises(ValueError, match=code):
        writer.profile_territory(series, territory, leg, subject="medial_meniscus")


def _native_fixture(tmp_path):
    uid, series_uid = generate_uid(), generate_uid()
    directory = tmp_path / "train_series" / uid / series_uid
    directory.mkdir(parents=True)
    coarse_pixels = fixture.series_record()["stack"].median[1].astype(np.uint16)
    pixels = np.repeat(np.repeat(coarse_pixels, 20, axis=0), 20, axis=1)
    pixels[68:72, 68:72] = 1000
    _write_dicom(directory / "one.dcm", uid, series_uid, pixels, spacing_rc=(0.5, 0.5))
    _write_tables(tmp_path, uid, series_uid)
    series = writer.read_study_squints(tmp_path, uid, io_workers=1)["series"][0]
    # Keep the same acquisition name used by the frozen fixture's bank helper.
    series["view"] = dict(fixture.VIEW)
    leg = fixture.expected_leg_map()
    leg.update(
        study_uid=uid,
        series_uid=series_uid,
        codes=leg["codes"][1:2],
        leg_share=leg["leg_share"][1:2],
    )
    territory = fixture.teacher_territory()
    territory.update(
        study_uid=uid, series_uid=series_uid, tile_window=[0, 1, 0, 6, 0, 6]
    )
    return series, leg, territory


def test_fine_native_support_distinguishes_same_box_and_keeps_context_and_coarse_edges(
    tmp_path,
):
    series, leg, territory = _native_fixture(tmp_path)
    masks = []
    for block in (slice(4, 8), slice(8, 12)):
        mask = np.zeros((1, 16, 16), dtype=bool)
        mask[0, 0, 0] = mask[0, -1, -1] = True
        mask[0, block, block] = True
        masks.append(mask)
    dark_territory = {
        **territory,
        "native_support": {"mask": masks[0], "offset_rc": [60, 60], "slices": [0]},
    }
    bright_territory = {
        **territory,
        "native_support": {"mask": masks[1], "offset_rc": [60, 60], "slices": [0]},
    }
    dark = writer.refine_territory(
        series, dark_territory, leg, subject="medial_meniscus"
    )
    bright = writer.refine_territory(
        series, bright_territory, leg, subject="medial_meniscus"
    )
    box = writer.refine_territory(series, territory, leg, subject="medial_meniscus")
    assert dark["banks"][_bank(scale=2)] == [3, 0, 0]
    assert bright["banks"][_bank(scale=2)] == [2, 0, 1]
    assert sum(box["banks"][_bank(scale=2)]) == 100
    assert sum(dark["banks"][_bank("context", scale=2)]) == 622
    assert sum(bright["banks"][_bank("context", scale=2)]) == 622
    source = dark["source"]
    coarse_calibration, _ = writer.leg_calibration(series, leg)
    assert source["calibration"] == coarse_calibration
    assert source["calibration_policy"] == "coarse_leg_inside_terciles_reused"
    assert source["native_crop_rc"] == [0, 120, 0, 120]
    assert source["native_slice_range"] == [0, 1]
    assert source["coarse_window"] == territory["tile_window"]
    assert source["fine_support_policy"] == "native_support_overlap"
    assert source["fine_object_share"][0][15][15] == 1 / 16
    assert source["territory"]["native_support_address"]["offset_rc"] == [60, 60]
    assert "native_support" not in source["territory"]
    assert all("scale=2mm" in name for name in dark["banks"])
    json.dumps(dark, allow_nan=False)
    coarse = writer.profile_territory(series, territory, leg, subject="medial_meniscus")
    combined = writer.merge_profiles([coarse, dark], subject="medial_meniscus")
    assert combined["banks"][_bank(scale=2)] == dark["banks"][_bank(scale=2)]
    assert combined["banks"][_bank()] == coarse["banks"][_bank()]


def test_fine_input_skips_outside_unknown_and_unqueried_native_pixels(
    tmp_path, monkeypatch
):
    series, leg, territory = _native_fixture(tmp_path)
    leg["codes"][0, 2, 2] = shapes.LEG_UNKNOWN
    leg["leg_share"][0, 2, 2] = np.nan
    territory["roles"][0, 2, 3] = shapes.ROLE_UNQUERIED
    observed = []
    original = writer.physical_squint

    def observe(plane, *args, **kwargs):
        observed.append(plane.copy())
        return original(plane, *args, **kwargs)

    monkeypatch.setattr(writer, "physical_squint", observe)
    fine = writer.refine_territory(series, territory, leg, subject="medial_meniscus")
    assert len(observed) == 1
    assert np.isnan(observed[0][:20]).all()
    assert np.isnan(observed[0][:, :20]).all()
    assert np.isnan(observed[0][40:60, 40:80]).all()
    assert sum(fine["banks"][_bank(scale=2)]) == 100
    assert sum(fine["banks"][_bank("context", scale=2)]) == 475


def test_fine_nonzero_crop_preserves_absolute_support_address(tmp_path):
    series, leg, territory = _native_fixture(tmp_path)
    mask = np.zeros((1, 16, 16), dtype=bool)
    mask[0, 0, 0] = mask[0, -1, -1] = True
    mask[0, 4:8, 4:8] = True
    territory["native_support"] = {"mask": mask, "offset_rc": [60, 60], "slices": [0]}
    full = writer.refine_territory(series, territory, leg, subject="medial_meniscus")
    cropped = {
        **territory,
        "tile_window": [0, 1, 2, 6, 2, 6],
        "roles": territory["roles"][:, 2:6, 2:6],
        "object_share": territory["object_share"][:, 2:6, 2:6],
    }
    fine = writer.refine_territory(series, cropped, leg, subject="medial_meniscus")
    assert fine["source"]["native_crop_rc"] == [40, 120, 40, 120]
    assert fine["source"]["native_bounds_rc"] == [40, 120, 40, 120]
    assert fine["source"]["territory"]["native_support_address"]["offset_rc"] == [
        60,
        60,
    ]
    assert fine["banks"][_bank(scale=2)] == full["banks"][_bank(scale=2)] == [3, 0, 0]
    assert fine["source"]["direction_origin"] == full["source"]["direction_origin"]


@pytest.mark.parametrize(
    "defect,code",
    [
        ("empty", "squint_native_support_empty"),
        ("offset", "squint_native_support_address_invalid"),
        ("outside_window", "squint_native_support_outside_territory"),
        ("slice", "squint_native_support_address_invalid"),
    ],
)
def test_fine_support_empty_and_malformed_addresses_are_named(tmp_path, defect, code):
    series, leg, territory = _native_fixture(tmp_path)
    support = {
        "mask": np.ones((1, 4, 4), dtype=bool),
        "offset_rc": [60, 60],
        "slices": [0],
    }
    if defect == "empty":
        support["mask"][:] = False
    elif defect == "offset":
        support["offset_rc"] = [-1, 60]
    elif defect == "outside_window":
        support["offset_rc"] = [140, 140]
    else:
        support["slices"] = [1]
    territory["native_support"] = support
    with pytest.raises(ValueError, match=code):
        writer.refine_territory(series, territory, leg, subject="medial_meniscus")


def test_fine_unavailable_native_series_and_invalid_scale_are_named(tmp_path):
    with pytest.raises(ValueError, match="squint_refine_native_series_unavailable"):
        writer.refine_territory(
            fixture.series_record(),
            fixture.teacher_territory(),
            fixture.expected_leg_map(),
            subject="medial_meniscus",
        )
    series, leg, territory = _native_fixture(tmp_path)
    for scale in (0.0, 10.0, float("nan")):
        with pytest.raises(ValueError, match="squint_refine_tile_mm_must_be_finer"):
            writer.refine_territory(
                series, territory, leg, subject="medial_meniscus", tile_mm=scale
            )
