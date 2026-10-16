"""The iliotibial band: the dark fascial line on the deep surface of the outer subcutaneous fat,
from the thigh to the tibia (Chien et al. 2020), read on native cross-sections across the leg."""

import numpy as np
import pytest

from knee.objects.assignments import (
    OBJECT_CODES,
    Measures,
    distance_from,
    iliotibial_band,
    iliotibial_band_on_slice,
    itb_code,
    positions_along,
)

# rows run down the leg (1 mm each), columns toward the patient's left (1 mm each): a right knee's
# outer side is the low columns, as on a coronal slice
CORONAL = np.asarray([[0.0, 1.0], [0.0, 0.0], [-1.0, 0.0]])
SIDE = 60


def scene(tibia_left: int = 15, femur_rows: tuple[int, int] = (0, 30)) -> tuple:
    """Air, skin, a bright outer fat band, one dark line on its deep surface, muscle, and the bones:
    the femur above, the tibia below with its outer edge `tibia_left` (the line is at column 13)."""
    plane = np.full((SIDE, SIDE), 300.0)
    objects = np.zeros((SIDE, SIDE), dtype=np.int8)
    plane[:, 0:3] = 0.0
    objects[:, 0:3] = OBJECT_CODES["air"]
    plane[:, 3:5] = 20.0
    objects[:, 3:5] = OBJECT_CODES["skin"]
    plane[:, 5:13] = 600.0
    objects[:, 5:13] = OBJECT_CODES["subcutaneous_fat"]
    plane[:, 13] = 20.0  # the fascia's dark line
    top, bottom = femur_rows
    plane[top:bottom, 40:] = 700.0
    objects[top:bottom, 40:] = OBJECT_CODES["femur"]
    plane[bottom:, 40:] = 700.0
    objects[bottom:, 40:] = OBJECT_CODES["tibia"]
    plane[bottom + 10 :, tibia_left:] = 700.0
    objects[bottom + 10 :, tibia_left:] = OBJECT_CODES["tibia"]
    return plane, objects, np.ones((SIDE, SIDE), dtype=bool)


def expected_line(last_row: int = 40) -> np.ndarray:
    line = np.zeros((SIDE, SIDE), dtype=bool)
    line[: last_row + 1, 13] = True
    return line


def run(plane, objects, available, basis=CORONAL, knee="R", suppressed=False, **kw):
    return iliotibial_band_on_slice(
        plane, objects, available, basis, knee, suppressed, **kw
    )


def test_names_the_dark_line_on_the_fats_deep_surface_down_to_the_tibia() -> None:
    plane, objects, available = scene()
    mask, readings, code = run(plane, objects, available)
    assert code == "identified"
    # kept down to the most superior section where the line comes within 2 mm of the tibia (row 40)
    assert np.array_equal(mask, expected_line(40))
    # the line below the insertion is measured and kept as a reading, not named
    assert readings["candidate_lines"][:, 13].all()
    assert not mask[41:].any()
    # the retained selector: the layer is the fat outboard of the bones, the strip lies deeper than it
    fat = objects == OBJECT_CODES["subcutaneous_fat"]
    assert np.array_equal(readings["fat_layer"], fat)
    assert readings["strip"][:, 13:15].all() and not (readings["strip"] & fat).any()
    assert (readings["section_status"][:60] == 1).all()
    assert readings["section_axis"] == 0
    assert float(readings["distal_stop_up_mm"]) == -40.0
    assert float(readings["section_line_light"][5]) == 20.0
    assert float(readings["section_fat_light"][5]) == 600.0


def test_the_band_is_only_ever_the_dark_line_not_the_fat_bone_or_muscle() -> None:
    plane, objects, available = scene()
    mask, _, _ = run(plane, objects, available)
    assert not (mask & (objects != 0)).any()
    assert (plane[mask] < 300.0).all()


def test_a_slope_from_fat_to_muscle_is_not_a_band() -> None:
    plane, objects, available = scene(tibia_left=30)  # no bright bone beside the line
    plane[:, 13] = (
        300.0  # no dip: the first muscle pixel is lower than the fat, not than the muscle
    )
    mask, readings, code = run(plane, objects, available)
    assert code == "abstain_no_dark_line_deep_to_the_fat"
    assert not mask.any() and not readings["candidate_lines"].any()
    assert (readings["section_status"][:60] == 3).all()


def test_two_separated_equal_minima_name_nothing_on_that_section() -> None:
    plane, objects, available = scene(tibia_left=30)
    scale = 0.5  # half-millimetre pixels: the 2 mm strip now holds four pixels
    plane[:, 13:17] = [20.0, 100.0, 20.0, 100.0]
    left = np.indices(plane.shape)[1] * scale
    mask, readings, code = iliotibial_band(
        plane,
        objects == OBJECT_CODES["subcutaneous_fat"],
        objects == OBJECT_CODES["femur"],
        objects == OBJECT_CODES["tibia"],
        np.isin(objects, (OBJECT_CODES["air"], OBJECT_CODES["skin"])),
        available,
        -left,
        -np.indices(plane.shape)[0] * scale,
        distance_from(objects == OBJECT_CODES["tibia"], np.asarray([scale, scale])),
        0,
    )
    assert code == "abstain_no_dark_line_deep_to_the_fat"
    assert not mask.any()
    assert (readings["section_status"][:60] == 2).all()


def test_a_line_that_never_reaches_the_tibia_is_not_the_band() -> None:
    plane, objects, available = scene(tibia_left=30)
    mask, readings, code = run(plane, objects, available)
    assert code == "abstain_band_does_not_reach_the_tibia"
    assert not mask.any()
    # the line was measured, and is kept as a reading
    assert readings["candidate_lines"].any()


def test_the_band_must_pass_a_section_holding_the_femur() -> None:
    # the bones swapped along the leg: the tibia above, where the line reaches it, the femur far below
    plane, objects, available = scene()
    objects = np.where(objects == OBJECT_CODES["femur"], OBJECT_CODES["tibia"], objects)
    objects[40:, 40:] = OBJECT_CODES["femur"]
    plane[:30, 15:40] = 700.0
    objects[:30, 15:40] = OBJECT_CODES["tibia"]
    mask, _, code = run(plane, objects, available)
    assert code == "abstain_band_not_beside_the_femur"
    assert not mask.any()


@pytest.mark.parametrize(
    "drop, code",
    [
        ("subcutaneous_fat", "abstain_no_subcutaneous_fat"),
        ("femur", "abstain_no_femur_and_tibia"),
        ("tibia", "abstain_no_femur_and_tibia"),
    ],
)
def test_missing_landmarks_name_nothing(drop: str, code: str) -> None:
    plane, objects, available = scene()
    objects = np.where(objects == OBJECT_CODES[drop], 0, objects)
    mask, readings, reading = run(plane, objects, available)
    assert reading == code
    assert not mask.any() and mask.dtype == np.dtype(bool)
    assert not readings["candidate_lines"].any()


def test_an_empty_slice_names_nothing() -> None:
    mask, _, code = run(
        np.zeros((SIDE, SIDE)),
        np.zeros((SIDE, SIDE), dtype=np.int8),
        np.ones((SIDE, SIDE), bool),
    )
    assert code == "abstain_no_subcutaneous_fat" and not mask.any()


def test_fat_inboard_of_the_bones_is_not_the_outer_layer() -> None:
    plane, objects, available = scene()
    objects[objects == OBJECT_CODES["subcutaneous_fat"]] = 0
    objects[:, 50:55] = OBJECT_CODES["subcutaneous_fat"]  # beside the bones' inner side
    _, _, code = run(plane, objects, available)
    assert code == "abstain_no_fat_outside_the_bones"


def test_transposed_native_axes_give_the_transposed_band() -> None:
    plane, objects, available = scene()
    transposed_basis = np.asarray([[1.0, 0.0], [0.0, 0.0], [0.0, -1.0]])
    mask, readings, code = run(plane.T, objects.T, available.T, transposed_basis)
    assert code == "identified"
    assert np.array_equal(mask, expected_line(40).T)
    assert readings["section_axis"] == 1


def test_the_headers_knee_says_which_side_is_outer() -> None:
    plane, objects, available = scene()
    flipped = (plane[:, ::-1], objects[:, ::-1], available[:, ::-1])
    # a left knee's outer side is the patient's left, the high columns
    mask, _, code = run(*flipped, knee="L")
    assert code == "identified"
    assert np.array_equal(mask, expected_line(40)[:, ::-1])
    # the same picture read as a right knee has its fat on the knee's inner side: no outer layer
    mask, _, code = run(*flipped, knee="R")
    assert code == "abstain_no_fat_outside_the_bones" and not mask.any()


def test_the_slice_measures_give_the_same_reading() -> None:
    plane, objects, available = scene()
    alone, _, code = run(plane, objects, available)
    kept, _, kept_code = run(
        plane, objects, available, measures=Measures(None, plane, CORONAL)
    )
    assert code == kept_code == "identified" and np.array_equal(alone, kept)


def test_inputs_are_left_as_they_were() -> None:
    plane, objects, available = scene()
    before = (plane.copy(), objects.copy(), available.copy())
    run(plane, objects, available)
    assert all(
        np.array_equal(a, b)
        for a, b in zip(before, (plane, objects, available), strict=True)
    )


def test_the_pure_function_refuses_unlike_shapes_and_axes() -> None:
    plane, objects, available = scene()
    ones = np.ones_like(plane)
    fat = objects == OBJECT_CODES["subcutaneous_fat"]
    with pytest.raises(ValueError, match="same-shaped"):
        iliotibial_band(plane, fat[:-1], fat, fat, fat, available, ones, ones, ones, 0)
    with pytest.raises(ValueError, match="same-shaped"):
        iliotibial_band(plane, fat, fat, fat, fat, available, ones, ones, ones, 2)


def test_each_prerequisite_has_its_own_named_refusal() -> None:
    plane, objects, available = scene()
    # the leg runs through an axial plane, side to side through a sagittal one
    axial = np.asarray([[0.0, 1.0], [1.0, 0.0], [0.0, 0.0]])
    sagittal = np.asarray([[0.0, 0.0], [0.0, 1.0], [-1.0, 0.0]])
    assert (
        run(plane, objects, available, axial)[2] == "abstain_leg_runs_through_the_plane"
    )
    assert (
        run(plane, objects, available, sagittal)[2]
        == "abstain_side_to_side_runs_through_the_plane"
    )
    assert run(plane, objects, available, knee="")[2] == "abstain_header_names_no_knee"
    assert run(plane, objects, available, suppressed=True)[2] == (
        "abstain_not_parted_from_the_fat_with_fat_suppression"
    )


def test_the_codes_come_in_the_order_of_the_descriptions() -> None:
    assert (
        itb_code(False, False, "", True, "x")
        == "abstain_side_to_side_runs_through_the_plane"
    )
    assert itb_code(True, False, "", True, "x") == "abstain_leg_runs_through_the_plane"
    assert itb_code(True, True, "", True, "x") == "abstain_header_names_no_knee"
    assert itb_code(True, True, "L", True, "x") == (
        "abstain_not_parted_from_the_fat_with_fat_suppression"
    )
    assert itb_code(True, True, "L", False, "x") == "x"


def test_positions_follow_the_basis_so_a_tilted_slice_still_finds_the_outer_side() -> (
    None
):
    plane, objects, available = scene()
    # a few hundredths of a millimetre toward the left per row
    tilt = np.asarray([[0.02, 1.0], [0.0, 0.0], [-1.0, 0.0]])
    assert positions_along(plane.shape, tilt, 0)[59, 0] == pytest.approx(1.18)
    mask, _, code = run(plane, objects, available, tilt)
    assert code == "identified" and mask[:, 13].any()
