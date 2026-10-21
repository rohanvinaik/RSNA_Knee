"""W1 intent checks, using the frozen shared anatomy and real split producer."""

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest
from squint_upgrade_fixtures import (
    DARK_BODY,
    SERIES_UID,
    expected_leg_map,
    series_record,
)

from knee.collapse.noise import background_split, finite_values
from knee.diagnosis.squint_interfaces import (
    LEG_INSIDE,
    LEG_MIXED,
    LEG_OUTSIDE,
    LEG_UNKNOWN,
    leg_map_code,
)
from knee.diagnosis.squint_leg import leg_maps


def _record(uid=SERIES_UID, *, fat="1", split=30.0):
    record = series_record()
    record["series_uid"] = uid
    record["stack"] = replace(record["stack"], series_uid=uid)
    record["view"]["fat_suppression"] = fat
    record["background_split"] = split
    return record


def _study(*records):
    return {"study_uid": "fixture.study", "series": list(records)}


def _geometry(record, *, shift=(0.0, 0.0, 0.0)):
    depth = record["stack"].median.shape[0]
    position = np.array([(0.25, z * 3.0, -0.25) for z in range(depth)])
    position += shift
    record["geometry"] = {
        "position": position,
        "orientation": np.tile((1.0, 0, 0, 0, 0, -1.0), (depth, 1)),
        "spacing": np.tile((0.5, 0.5), (depth, 1)),
    }
    record["stack"] = replace(
        record["stack"], centres_lps=record["stack"].centres_lps + shift
    )
    return record


def test_frozen_fixture_codes_reproduced_without_inventing_mixed_share():
    record = _record()
    result = leg_maps(_study(record))[SERIES_UID]
    expected = expected_leg_map()
    assert leg_map_code(result, grid_shape=(3, 8, 8)) == "valid"
    np.testing.assert_array_equal(result["codes"], expected["codes"])
    assert result["counts"] == expected["counts"]
    np.testing.assert_array_equal(result["leg_share"][result["codes"] == LEG_INSIDE], 1)
    np.testing.assert_array_equal(
        result["leg_share"][result["codes"] == LEG_OUTSIDE], 0
    )
    assert np.isnan(result["leg_share"][result["codes"] == LEG_MIXED]).all()
    assert result["provenance"]["background_split"]["value"] == 30.0
    assert "leg_map" not in record
    assert not result["codes"].flags.writeable


def test_enclosed_dark_body_stays_inside_even_on_end_slices():
    result = leg_maps(_study(_record()))[SERIES_UID]
    assert (result["codes"][(slice(None), *DARK_BODY)] == LEG_INSIDE).all()
    assert result["counts"]["outside"] == 3 * 28


@pytest.mark.parametrize("background", [2.0, 30.0])
def test_dark_median_noisy_air_floods_but_enclosed_body_in_other_slices_stays_inside(
    background,
):
    record = _record()
    stack = record["stack"]
    minimum, median, maximum = (
        a.copy() for a in (stack.minimum, stack.median, stack.maximum)
    )
    # One bright pixel cannot keep a mostly dark air tile inside. The same
    # summaries form a four-connected path from the border to the dark body.
    pixels = np.full((20, 20), background)
    pixels[0, 0] = 1000.0
    minimum[1, 3, :4] = pixels.min()
    median[1, 3, :4] = np.median(pixels)
    maximum[1, 3, :4] = pixels.max()
    record["stack"] = replace(stack, minimum=minimum, median=median, maximum=maximum)
    result = leg_maps(_study(record))[SERIES_UID]
    assert (result["codes"][1, 3, :4] == LEG_OUTSIDE).all()
    assert (result["codes"][1][DARK_BODY] == LEG_OUTSIDE).all()
    assert (result["codes"][0][DARK_BODY] == LEG_INSIDE).all()
    assert (result["codes"][2][DARK_BODY] == LEG_INSIDE).all()


def test_border_tile_with_bright_median_and_dark_minimum_remains_mixed():
    record = _record()
    stack = record["stack"]
    median, maximum = stack.median.copy(), stack.maximum.copy()
    median[1, 0, 3] = 31.0
    maximum[1, 0, 3] = 1000.0
    record["stack"] = replace(stack, median=median, maximum=maximum)
    result = leg_maps(_study(record))[SERIES_UID]
    assert result["codes"][1, 0, 3] == LEG_MIXED
    assert np.isnan(result["leg_share"][1, 0, 3])


def test_opening_dark_path_changes_body_to_outside_but_not_other_enclosed_body():
    record = _record()
    stack = record["stack"]
    minimum, median, maximum = (
        a.copy() for a in (stack.minimum, stack.median, stack.maximum)
    )
    # Slice 1: a four-connected dark path from the left frame to the body.
    minimum[1, 3, :4] = 0
    median[1, 3, :4] = 2
    maximum[1, 3, :4] = 30
    record["stack"] = replace(stack, minimum=minimum, median=median, maximum=maximum)
    result = leg_maps(_study(record))[SERIES_UID]
    assert (result["codes"][1][DARK_BODY] == LEG_OUTSIDE).all()
    assert (result["codes"][0][DARK_BODY] == LEG_INSIDE).all()
    assert (result["codes"][2][DARK_BODY] == LEG_INSIDE).all()


def test_diagonal_dark_contact_does_not_make_a_path():
    record = _record()
    stack = record["stack"]
    minimum, median, maximum = (
        a.copy() for a in (stack.minimum, stack.median, stack.maximum)
    )
    minimum[:, 2, 2] = 0
    median[:, 2, 2] = 2
    maximum[:, 2, 2] = 30
    record["stack"] = replace(stack, minimum=minimum, median=median, maximum=maximum)
    result = leg_maps(_study(record))[SERIES_UID]
    assert (result["codes"][:, 2, 2] == LEG_INSIDE).all()
    assert (result["codes"][(slice(None), *DARK_BODY)] == LEG_INSIDE).all()


@pytest.mark.parametrize("coverage", [0.0, np.nan, -1.0, 2.0])
def test_unread_or_invalid_coverage_never_outside(coverage):
    record = _record()
    stack = record["stack"]
    values = stack.coverage.copy()
    values[:, 0, 0] = coverage
    record["stack"] = replace(stack, coverage=values)
    result = leg_maps(_study(record))[SERIES_UID]
    assert (result["codes"][:, 0, 0] == LEG_UNKNOWN).all()
    assert np.isnan(result["leg_share"][:, 0, 0]).all()


@pytest.mark.parametrize("field", ["minimum", "median", "maximum"])
def test_nonfinite_tile_measurements_never_outside(field):
    record = _record()
    values = getattr(record["stack"], field).copy()
    values[:, 0, 0] = np.nan
    record["stack"] = replace(record["stack"], **{field: values})
    result = leg_maps(_study(record))[SERIES_UID]
    assert (result["codes"][:, 0, 0] == LEG_UNKNOWN).all()


@pytest.mark.parametrize("split", [None, np.nan, np.inf, -np.inf])
def test_missing_split_is_all_unknown_with_named_code(split):
    result = leg_maps(_study(_record(split=split)))[SERIES_UID]
    assert (result["codes"] == LEG_UNKNOWN).all()
    assert np.isnan(result["leg_share"]).all()
    assert result["code"] == "no_background_split"
    assert leg_map_code(result) == "valid"


def test_missing_native_volume_does_not_estimate_a_split_from_tiles():
    record = series_record()
    result = leg_maps(_study(record))[SERIES_UID]
    assert result["code"] == "native_volume_unavailable"
    assert (result["codes"] == LEG_UNKNOWN).all()


def test_constant_native_volume_has_no_split_and_remains_unknown():
    record = series_record()
    record["native_series"] = SimpleNamespace(volume=np.ones((3, 160, 160)))
    result = leg_maps(_study(record))[SERIES_UID]
    assert result["code"] == "no_background_split"
    assert (result["codes"] == LEG_UNKNOWN).all()


def test_native_finite_values_use_the_existing_background_measurement():
    record = series_record()
    volume = np.r_[np.zeros(10000), np.arange(100, 200), np.nan, np.inf]
    record["native_series"] = SimpleNamespace(volume=volume)
    expected = background_split(finite_values(volume))
    assert np.isfinite(expected)
    result = leg_maps(_study(record))[SERIES_UID]
    reading = result["provenance"]["background_split"]
    assert reading["value"] == expected
    assert reading["finite_count"] == 10100
    assert reading["source"] == "knee.collapse.noise.background_split"


def test_all_dark_tiles_are_outside_including_boundary_equality():
    record = _record(split=30)
    stack = record["stack"]
    record["stack"] = replace(
        stack,
        minimum=np.zeros((3, 8, 8)),
        median=np.full((3, 8, 8), 30.0),
        maximum=np.full((3, 8, 8), 30.0),
    )
    result = leg_maps(_study(record))[SERIES_UID]
    assert (result["codes"] == LEG_OUTSIDE).all()


def test_non_fs_map_restores_suppressed_leg_by_physical_place():
    source = _geometry(_record("nonfs", fat="0"))
    target = _geometry(_record("fs", split=10000.0))
    # All local FS maxima fall below its own split; source supplies the leg.
    result = leg_maps(_study(source, target))["fs"]
    np.testing.assert_array_equal(result["codes"], expected_leg_map()["codes"])
    assert (result["local_codes"] == LEG_OUTSIDE).all()
    assert result["provenance"]["carried_tiles"] == 192
    assert result["provenance"]["projection_sources"][0]["series_uid"] == "nonfs"


def test_physical_translation_uses_different_tile_addresses_and_no_extrapolation():
    source = _geometry(_record("nonfs", fat="0"))
    target = _geometry(_record("fs", split=10000.0), shift=(10, 0, 0))
    result = leg_maps(_study(source, target))["fs"]
    expected = expected_leg_map()["codes"]
    np.testing.assert_array_equal(result["codes"][:, :, :-1], expected[:, :, 1:])
    assert (result["codes"][:, :, -1] == LEG_OUTSIDE).all()  # local fallback
    assert result["provenance"]["local_fallback_tiles"] == 24


def test_cross_plane_carry_uses_patient_place_instead_of_matching_array_indices():
    source = _geometry(_record("nonfs", fat="0"))
    target = _record("axial", split=10000.0)
    target["view"]["orientation"] = "Axial"
    centres = np.empty((3, 8, 8, 3))
    for z, r, c in np.ndindex(3, 8, 8):
        centres[z, r, c] = (10 * c + 5, 3 * r, -(10 * z + 5))
    target["stack"] = replace(target["stack"], centres_lps=centres)
    result = leg_maps(_study(source, target))["axial"]
    expected = expected_leg_map()["codes"]
    for z, r, c in np.ndindex(3, 3, 8):
        assert result["codes"][z, r, c] == expected[r, z, c]
    assert (result["codes"][:, 3:, :] == LEG_OUTSIDE).all()  # local fallback
    assert result["provenance"]["projection_sources"][0]["same_plane"] is False


@pytest.mark.parametrize("split", [True, np.bool_(False), "30", 1j, [30]])
def test_supplied_split_rejects_nonreal_or_malformed_values_by_name(split):
    with pytest.raises(ValueError, match="leg_background_split_invalid"):
        leg_maps(_study(_record(split=split)))


def test_source_maps_disagree_without_majority_vote():
    source = _geometry(_record("source1", fat="0"))
    other = _geometry(_record("source2", fat="0", split=10000.0))
    third = _geometry(_record("source3", fat="0"))
    target = _geometry(_record("fs", split=10000.0))
    result = leg_maps(_study(source, other, third, target))["fs"]
    assert (result["codes"][(slice(None), *DARK_BODY)] == LEG_UNKNOWN).all()
    assert result["provenance"]["conflict_code"] == "source_maps_disagree"


def test_projection_cannot_turn_missing_target_coverage_or_split_into_outside():
    source = _geometry(_record("source", fat="0"))
    target = _geometry(_record("fs"))
    coverage = target["stack"].coverage.copy()
    coverage[:, 0, :] = 0
    target["stack"] = replace(target["stack"], coverage=coverage)
    no_split = _geometry(_record("no_split", split=None))
    result = leg_maps(_study(source, target, no_split))
    assert (result["fs"]["codes"][:, 0, :] == LEG_UNKNOWN).all()
    assert (result["no_split"]["codes"] == LEG_UNKNOWN).all()


def test_missing_geometry_keeps_local_map_and_names_why_carry_unavailable():
    source = _record("source", fat="0")
    target = _record("fs")
    result = leg_maps(_study(source, target))["fs"]
    np.testing.assert_array_equal(result["codes"], expected_leg_map()["codes"])
    assert result["provenance"]["carried_tiles"] == 0
    assert (
        result["provenance"]["projection_sources"][0]["code"]
        == "source_depth_or_geometry_unavailable"
    )


def test_empty_study_is_empty_and_malformed_inputs_have_named_refusals():
    assert leg_maps(_study()) == {}
    with pytest.raises(TypeError, match="leg_study_invalid"):
        leg_maps(None)
    with pytest.raises(ValueError, match="leg_series_identity_invalid"):
        leg_maps(_study({}))
    with pytest.raises(ValueError, match="leg_series_identity_repeated"):
        leg_maps(_study(_record(), _record()))
