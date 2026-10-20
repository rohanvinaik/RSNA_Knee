from __future__ import annotations

import numpy as np
import pytest

from knee.collapse import patellofemoral as mod

reading = mod.patellofemoral_surface_reading


def scene():
    raw = np.full((13, 17), 12.0)
    available = np.ones(raw.shape, dtype=bool)
    patella = np.zeros(raw.shape, dtype=bool)
    femur = np.zeros(raw.shape, dtype=bool)
    patella[5:8, 2:5] = True
    femur[5:8, 11:14] = True
    return raw, available, patella, femur


def test_bridge_prior_supports_and_crop_coordinates_are_retained():
    raw, available, patella, femur = scene()
    raw[6, 5:11] = 25.0
    result = reading(raw, available, patella, femur, (1.0, 1.0), 10.0)
    arrays = result
    assert result["status"] == "measured"
    assert result["brightness_lower"] == 15.0
    assert result["brightness_upper"] == 40.0
    assert arrays["bridge"].shape == raw.shape
    assert arrays["bridge"][6, 7]
    assert arrays["patella"][6, 3] and arrays["femur"][6, 12]
    assert arrays["patella_filled"].dtype == np.bool_
    assert arrays["femur_filled"].dtype == np.bool_
    assert arrays["patella_support"][6, 5]
    assert arrays["trochlear_support"][6, 10]
    assert result["shape_rc"] == [13, 17]


def test_nonfinite_and_unavailable_pixels_remain_out_of_eligibility():
    raw, available, patella, femur = scene()
    raw[6, 5:11] = 25.0
    raw[6, 7] = np.nan
    available[6, 8] = False
    result = reading(raw, available, patella, femur, (1.0, 1.0), 10.0)
    arrays = result
    assert not arrays["finite"][6, 7]
    assert not arrays["available"][6, 8]
    assert not arrays["eligible"][6, 7]
    assert not arrays["eligible"][6, 8]
    assert not arrays["patella_support"][6, 7:9].any()


def test_exact_brightness_bounds_are_lower_exclusive_and_upper_inclusive():
    raw, available, patella, femur = scene()
    raw[6, 5:11] = (15.0, 15.0001, 39.999, 40.0, 40.0001, 25.0)
    arrays = reading(raw, available, patella, femur, (1.0, 1.0), 10.0)
    assert not arrays["brightness_band"][6, 5]
    assert arrays["brightness_band"][6, 6]
    assert arrays["brightness_band"][6, 7]
    assert arrays["brightness_band"][6, 8]
    assert not arrays["brightness_band"][6, 9]


def test_physical_reach_uses_anisotropic_spacing_and_includes_three_mm():
    raw, available, patella, femur = scene()
    raw[6, 5:11] = 25.0
    result = reading(raw, available, patella, femur, (2.0, 1.0), 10.0)
    arrays = result
    assert arrays["to_patella_mm"][6, 5] == 1.0
    assert arrays["patella_reach"][6, 7]
    assert not arrays["patella_reach"][6, 8]
    assert arrays["femur_reach"][6, 9]


def test_equal_distance_pixels_are_retained_as_ties_not_named_support():
    raw = np.full((9, 15), 25.0)
    available = np.ones(raw.shape, dtype=bool)
    patella = np.zeros(raw.shape, dtype=bool)
    femur = np.zeros(raw.shape, dtype=bool)
    patella[4, 4] = True
    femur[4, 10] = True
    result = reading(raw, available, patella, femur, (1.0, 1.0), 10.0)
    arrays = result
    assert arrays["bridge"][4, 7]
    assert arrays["ties"][4, 7]
    assert not arrays["patella_support"][4, 7]
    assert not arrays["trochlear_support"][4, 7]


def test_overlapping_original_bone_masks_are_retained():
    raw, available, patella, femur = scene()
    femur[6, 4] = True
    result = reading(raw, available, patella, femur, (1.0, 1.0), 10.0)
    assert result["overlap"][6, 4]
    assert result["patella"][6, 4]
    assert result["femur"][6, 4]


def test_original_inputs_are_not_mutated():
    raw, available, patella, femur = scene()
    before = tuple(a.copy() for a in (raw, available, patella, femur))
    reading(raw, available, patella, femur, (0.7, 1.3), 10.0)
    for actual, expected in zip((raw, available, patella, femur), before, strict=True):
        np.testing.assert_array_equal(actual, expected)


def test_empty_bridge_is_a_measured_empty_result():
    raw = np.ones((5, 5), dtype=float)
    available = np.ones(raw.shape, dtype=bool)
    patella = np.zeros(raw.shape, dtype=bool)
    femur = np.zeros(raw.shape, dtype=bool)
    patella[2, 2] = femur[2, 2] = True
    result = reading(raw, available, patella, femur, (1.0, 1.0), 10.0)
    assert result["status"] == "measured_empty"
    assert result["reason"] == "no_eligible_bridge_pixels"
    assert not result["bridge"].any()


@pytest.mark.parametrize(
    "raw,available,patella,femur,spacing,light,reason",
    [
        (
            np.ones((2, 2, 2)),
            np.ones((2, 2), bool),
            np.ones((2, 2), bool),
            np.ones((2, 2), bool),
            (1, 1),
            1,
            "invalid_raw_plane",
        ),
        (
            np.ones((4, 4)),
            np.ones((3, 4), bool),
            np.ones((4, 4), bool),
            np.ones((4, 4), bool),
            (1, 1),
            1,
            "invalid_available_mask",
        ),
        (
            np.ones((4, 4)),
            np.ones((4, 4), bool),
            np.ones((4, 4), dtype=float),
            np.ones((4, 4), bool),
            (1, 1),
            1,
            "invalid_patella_support",
        ),
        (
            np.ones((4, 4)),
            np.ones((4, 4), bool),
            np.ones((4, 4), bool),
            np.ones((3, 4), bool),
            (1, 1),
            1,
            "invalid_femur_support",
        ),
        (
            np.ones((4, 4)),
            np.ones((4, 4), bool),
            np.ones((4, 4), bool),
            np.ones((4, 4), bool),
            (1, 0),
            1,
            "invalid_spacing",
        ),
        (
            np.ones((4, 4)),
            np.ones((4, 4), bool),
            np.ones((4, 4), bool),
            np.ones((4, 4), bool),
            (1, 1),
            np.nan,
            "invalid_reference_light",
        ),
    ],
)
def test_malformed_prerequisites_return_named_unmeasured_status(
    raw, available, patella, femur, spacing, light, reason
):
    result = reading(raw, available, patella, femur, spacing, light)
    assert result["status"] == "unmeasured"
    assert result["reason"] == reason


def test_missing_native_support_is_not_treated_as_absent():
    raw, available, _patella, femur = scene()
    result = reading(raw, available, None, femur, (1.0, 1.0), 10.0)
    assert result["status"] == "unmeasured"
    assert result["reason"] == "missing_patella_support"
    assert not result["patella_support"].any()


def test_empty_availability_is_unmeasured_not_measured_empty():
    raw, available, patella, femur = scene()
    available[:] = False
    result = reading(raw, available, patella, femur, (1.0, 1.0), 10.0)
    assert result["status"] == "unmeasured"
    assert result["reason"] == "no_available_finite_pixels"
    assert result["reference_light"] == 10.0


def test_all_missing_inputs_return_named_unmeasured_result():
    result = reading(None, None, None, None, (1.0, 1.0), 1.0)
    assert result["status"] == "unmeasured"
    assert result["reason"] == "invalid_raw_plane"
    assert result["shape_rc"] == [0, 0]
    assert result["bridge"].shape == (0, 0)
    assert result["bridge"].dtype == np.bool_


def test_distance_adapter_is_used_and_malformed_output_is_named():
    raw, available, patella, femur = scene()
    calls = []

    def adapter(target, spacing):
        calls.append((target.copy(), tuple(spacing)))
        return mod.ndi.distance_transform_edt(~target, sampling=spacing)

    result = reading(raw, available, patella, femur, (0.8, 1.4), 10.0, distance=adapter)
    assert result["status"] == "measured_empty"
    assert len(calls) == 2
    assert calls[0][1] == calls[1][1] == (0.8, 1.4)

    bad = reading(
        raw,
        available,
        patella,
        femur,
        (1.0, 1.0),
        10.0,
        distance=lambda _mask, _spacing: np.zeros((1, 1)),
    )
    assert bad["status"] == "unmeasured"
    assert bad["reason"] == "native_distance_unavailable"


def test_degenerate_segment_hull_keeps_pixel_center_bridge():
    raw = np.full((7, 9), 25.0)
    available = np.ones(raw.shape, dtype=bool)
    patella = np.zeros(raw.shape, dtype=bool)
    femur = np.zeros(raw.shape, dtype=bool)
    patella[3, 1] = True
    femur[3, 7] = True
    result = reading(raw, available, patella, femur, (1.0, 1.0), 10.0)
    arrays = result
    assert arrays["bridge"][3, 4]
    assert arrays["ties"][3, 4]
