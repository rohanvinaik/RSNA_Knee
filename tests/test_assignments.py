"""Intent tests for the assignments: what each question names, and where it must abstain.

The scene is a small synthetic knee in a coronal frame (rows run inferior, columns run to the left,
one place per millimetre): air around a leg of soft tissue, a margin of stored zeros along two sides
of the frame, and two bones (marrow inside a 2 mm cortex) stacked along the leg with a joint space
between them, closed at its sides by two dark wedges. The interiors stage reads the scene exactly as
the run does, and the assignments read that reading.
"""

import numpy as np
import pytest

from knee.objects.assignments import (
    OBJECT_CODES,
    air_code,
    assign_plane,
    between_along_superior,
    bone_code,
    fat_sign,
    held_body,
    joint_code,
    marrow_sign,
    noise_sign,
    pair_code,
    signal_third,
    unrecorded,
    wall_sign,
)
from knee.objects.interiors import read_interiors

OFFSETS = np.arange(-3.0, 3.5, 0.5)
SPLIT = 5.0
THIRDS = (30.0, 70.0)
REACH = 3.0
CORONAL = np.array([[0.0, 1.0], [0.0, 0.0], [-1.0, 0.0]])  # rows inferior, columns left
AXIAL = np.array([[0.0, 1.0], [1.0, 0.0], [0.0, 0.0]])  # rows posterior, columns left
T1W, FAT_SUPPRESSED = ("0", "0"), ("1", "1")


def scene(marrow: float, joint: float) -> np.ndarray:
    plane = np.full((140, 120), 2.0)  # air: low signal, recorded
    plane[:3, :] = 0.0  # a margin the reconstruction never filled
    plane[:, :3] = 0.0
    plane[10:132, 20:100] = 40.0  # the leg's soft tissue
    for top in (16, 76):  # the femur above, the tibia below
        plane[top : top + 46, 32:88] = 1.0  # cortex, very low
        plane[top + 2 : top + 44, 34:86] = marrow
    plane[62:76, 32:38] = 1.0  # the dark wedges at the joint's two sides
    plane[62:76, 82:88] = 1.0
    plane[62:76, 38:82] = joint
    return plane


NOISE_VOUCHES = (
    1.0,
    2.0,
)  # the places below the split read no louder than the tissue's noise


def assigned(
    plane, basis=CORONAL, tags=T1W, thirds=THIRDS, split=SPLIT, sigmas=NOISE_VOUCHES
):
    reading = read_interiors(plane, (1.0, 1.0), split, 3.0, OFFSETS, "reference")
    return assign_plane(plane, reading, (1.0, 1.0), basis, thirds, tags, REACH, sigmas)


def test_t1w_scene_names_air_skin_femur_over_tibia_and_the_joint():
    result = assigned(scene(marrow=100.0, joint=25.0))
    objects = result.objects
    assert result.codes == {
        "air": "identified",
        "skin": "identified",
        "pair": "femur_tibia",
        "femur": "identified",
        "tibia": "identified",
        "joint": "identified",
    }
    assert objects[40, 60] == OBJECT_CODES["femur"]
    assert objects[100, 60] == OBJECT_CODES["tibia"]
    assert objects[69, 60] == OBJECT_CODES["joint"]
    assert objects[70, 10] == OBJECT_CODES["air"]
    assert objects[70, 20] == OBJECT_CODES["skin"]
    # the joint is only what lies between the two bones: never the cortex, the wedges or the leg
    joint_rows = np.flatnonzero((objects == OBJECT_CODES["joint"]).any(axis=1))
    assert int(joint_rows[0]) >= 62 and int(joint_rows[-1]) <= 75  # sorted indices
    assert objects[61, 60] == objects[69, 34] == OBJECT_CODES["unassigned"]
    # every territory was asked; only the two marrows answered bone on both signs
    concurred = [r.territory for r in result.readings if r.bone == "bone_concurred"]
    assert sorted(concurred) == sorted([result.femur, result.tibia])


def test_the_margin_and_the_record_edge_are_never_air():
    result = assigned(scene(marrow=100.0, joint=25.0))
    air = result.objects == OBJECT_CODES["air"]
    assert result.margin[:3].all() and result.margin[:, :3].all()
    assert not (air & result.margin).any()
    assert not (air & result.record_edge).any()
    assert result.record_edge[3:6, 60].all()  # within the 3 mm reach of the margin


def test_fat_suppressed_scene_takes_out_only_the_fluid_that_runs_out_of_a_bone():
    plane = scene(marrow=20.0, joint=150.0)
    plane[30:34, 50:54] = 150.0  # a bright reading the femur's marrow holds alone
    plane[56:62, 58:61] = 150.0  # bright fluid running out through a gap in the cortex
    result = assigned(plane, tags=FAT_SUPPRESSED)
    assert result.codes["pair"] == "femur_tibia"
    assert result.codes["joint"] == "identified"
    assert result.objects[31, 51] == OBJECT_CODES["femur"]
    assert result.objects[57, 59] != OBJECT_CODES["femur"]
    assert result.counts["femur_refused_by_signal"] > 0
    assert result.objects[40, 60] == OBJECT_CODES["femur"]
    assert result.objects[69, 50] == OBJECT_CODES["joint"]


def test_a_bone_is_the_one_connected_piece_that_holds_its_deepest_place():
    mask = np.zeros((5, 9), dtype=bool)
    mask[1:4, 1:4] = True
    mask[1:4, 6:8] = True
    body = held_body(mask, (2, 2))
    assert body[1:4, 1:4].all() and not body[:, 5:].any()
    assert not held_body(mask, (0, 0)).any()


def test_bright_marrow_under_fat_suppression_is_refused_as_bone():
    result = assigned(scene(marrow=100.0, joint=25.0), tags=FAT_SUPPRESSED)
    deep = sorted(result.readings, key=lambda r: r.depth_mm, reverse=True)[:2]
    assert {r.bone for r in deep} == {"abstain_signs_disagree"}
    assert result.codes["pair"] == "abstain_fewer_than_two_bones"
    assert not np.isin(result.objects, [3, 4, 5]).any()


def test_a_plane_without_the_leg_axis_names_no_femur_or_tibia():
    result = assigned(scene(marrow=100.0, joint=25.0), basis=AXIAL)
    assert result.superior_in_plane == 0.0
    for name in ("pair", "femur", "tibia", "joint"):
        assert result.codes[name] == "abstain_superior_through_plane"
    assert not np.isin(result.objects, [3, 4, 5]).any()
    assert result.codes["air"] == "identified"


def test_no_split_and_no_tissue_abstain_without_naming_anything():
    for plane, split in (
        (scene(marrow=100.0, joint=25.0), float("nan")),
        (np.full((40, 40), 1.0), SPLIT),
    ):
        result = assigned(plane, split=split)
        assert result.codes["air"] == "abstain_no_body"
        assert result.codes["skin"] == "abstain_no_air"
        assert result.codes["pair"] == "abstain_fewer_than_two_bones"
        assert not result.objects.any()


def test_unread_thirds_leave_every_bone_question_open():
    result = assigned(scene(marrow=100.0, joint=25.0), thirds=(np.nan, np.nan))
    assert all(r.signal_third is None for r in result.readings)
    assert all(r.bone != "bone_concurred" for r in result.readings)


@pytest.mark.parametrize(
    ("wall", "marrow", "code"),
    [
        (1, 1, "bone_concurred"),
        (1, 0, "abstain_signal_silent"),
        (1, -1, "abstain_signs_disagree"),
        (-1, 1, "abstain_signs_disagree"),
        (-1, 0, "not_bone"),
        (-1, -1, "not_bone"),
        (0, 1, "abstain_wall_unread"),
        (0, 0, "abstain_wall_unread"),
        (0, -1, "abstain_wall_unread"),
    ],
)
def test_bone_needs_its_two_signs_to_concur(wall, marrow, code):
    assert bone_code(wall, marrow) == code


@pytest.mark.parametrize(
    ("tags", "signs"),
    [
        (T1W, (0, 0, 1)),
        (FAT_SUPPRESSED, (1, 0, -1)),
        (("1", "0"), (0, 0, 0)),
        (("0", "1"), (0, 0, 0)),
    ],
)
def test_marrow_sign_follows_the_tissue_table(tags, signs):
    assert tuple(marrow_sign(third, *tags) for third in (-1, 0, 1)) == signs
    assert marrow_sign(None, *tags) == 0


@pytest.mark.parametrize(
    ("tags", "signs"),
    [(T1W, (-1, 0, 1)), (FAT_SUPPRESSED, (0, 0, -1)), (("1", "0"), (0, 0, 0))],
)
def test_fat_sign_follows_the_tissue_table(tags, signs):
    assert tuple(fat_sign(third, *tags) for third in (-1, 0, 1)) == signs
    assert fat_sign(None, *tags) == 0


def test_wall_sign_is_a_majority_and_silent_without_a_readable_border():
    assert wall_sign(0, 0) == 0
    assert wall_sign(5, 10) == 1
    assert wall_sign(4, 10) == -1
    assert wall_sign(0, 1) == -1


def test_pair_code_abstains_in_the_order_its_signs_are_read():
    assert pair_code(0.1, 2, 0, True, True) == "abstain_superior_through_plane"
    assert pair_code(float("nan"), 2, 0, True, True) == "abstain_superior_through_plane"
    assert pair_code(1.0, 1, 0, True, True) == "abstain_fewer_than_two_bones"
    assert pair_code(1.0, 2, 1, True, True) == "abstain_candidates_not_the_two_deepest"
    assert pair_code(1.0, 2, 0, False, True) == "abstain_two_deepest_bones_not_stacked"
    assert pair_code(1.0, 2, 0, True, False) == "abstain_no_low_signal_between"
    assert pair_code(1.0, 2, 0, True, True) == "femur_tibia"


def test_joint_code_keeps_fat_out_of_the_joint():
    assert joint_code(-1) == "joint"
    assert joint_code(1) == "abstain_fat_signal"
    assert joint_code(0) == "abstain_signal_silent"


def test_air_code_names_the_first_sign_that_kept_nothing():
    assert air_code(1, 1, 1, 1, 1, 1, 1) == "identified"
    assert air_code(0, 0, 1, 1, 1, 1, 0) == "abstain_no_body"
    assert air_code(1, 0, 1, 1, 1, 1, 0) == "abstain_body_not_at_field_centre"
    assert air_code(1, 1, 0, 1, 1, 1, 0) == "abstain_noise_law_unread"
    assert air_code(1, 1, -1, 1, 1, 1, 0) == "abstain_low_signal_holds_more_than_noise"
    assert air_code(1, 1, 1, 0, 0, 0, 0) == "abstain_no_outside_field"
    assert air_code(1, 1, 1, 1, 0, 0, 0) == "abstain_outside_not_low_signal"
    assert air_code(1, 1, 1, 1, 1, 0, 0) == "abstain_low_signal_only_at_record_edge"
    assert air_code(1, 1, 1, 1, 1, 1, 0) == "abstain_no_low_signal_wider_than_a_border"


def test_noise_sign_vouches_only_when_below_the_split_is_noise_alone():
    assert noise_sign(1.0, 2.0) == noise_sign(2.0, 2.0) == 1
    assert noise_sign(3.0, 2.0) == -1
    assert noise_sign(float("nan"), 2.0) == noise_sign(1.0, 0.0) == 0


def test_low_signal_that_holds_more_than_noise_names_no_air():
    result = assigned(scene(marrow=100.0, joint=25.0), sigmas=(3.0, 2.0))
    assert result.codes["air"] == "abstain_low_signal_holds_more_than_noise"
    assert not (result.objects == OBJECT_CODES["air"]).any()
    assert result.codes["pair"] == "femur_tibia"  # the bones do not read the noise law


def test_tissue_that_misses_the_field_centre_names_no_air_or_skin():
    plane = np.full((120, 120), 2.0)
    plane[5:41, 5:41] = 40.0  # tissue in a corner, while the centre is low signal
    result = assigned(plane)
    assert result.codes["air"] == "abstain_body_not_at_field_centre"
    assert result.codes["skin"] == "abstain_no_air"
    assert not np.isin(result.objects, [1, 2]).any()


def test_signal_third_edges_and_unread_values():
    assert signal_third(30.0, THIRDS) == 0
    assert signal_third(70.0, THIRDS) == 0
    assert signal_third(29.9, THIRDS) == -1
    assert signal_third(70.1, THIRDS) == 1
    assert signal_third(float("nan"), THIRDS) is None
    assert signal_third(50.0, (float("nan"), 70.0)) is None


def test_unrecorded_is_only_zeros_joined_to_the_frame():
    plane = np.ones((6, 6))
    plane[0, :] = 0.0  # a margin
    plane[3, 3] = 0.0  # a zero inside the record
    margin = unrecorded(plane)
    assert margin[0].all()
    assert not margin[3, 3]
    assert margin.sum() == 6
    assert not unrecorded(np.ones((4, 4))).any()


def test_between_follows_the_superior_axis_whichever_way_the_rows_run():
    upper, lower = np.zeros((7, 1), dtype=bool), np.zeros((7, 1), dtype=bool)
    upper[1, 0], lower[5, 0] = True, True
    rows_inferior = np.array([[0.0, 1.0], [0.0, 0.0], [-1.0, 0.0]])
    assert np.flatnonzero(
        between_along_superior(upper, lower, rows_inferior)
    ).tolist() == [2, 3, 4]
    rows_superior = np.array([[0.0, 1.0], [0.0, 0.0], [1.0, 0.0]])
    # rows now run superior, so the upper object must lie at the larger index to be "above"
    assert not between_along_superior(upper, lower, rows_superior).any()
    assert np.flatnonzero(
        between_along_superior(lower, upper, rows_superior)
    ).tolist() == [2, 3, 4]
