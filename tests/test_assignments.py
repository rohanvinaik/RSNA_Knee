"""Intent tests for the named objects: air, skin, femur over tibia, the joint, patella and menisci.

The scene is a small synthetic knee in a coronal frame (rows run inferior, columns run to the left,
one place per millimetre): air around a leg of soft tissue, a black margin along two sides of the
picture, and two bones stacked along the leg with a joint between them. The interiors stage reads
the scene exactly as the run does, and the assignments read that reading.
"""

import numpy as np

from knee.objects.assignments import (
    OBJECT_CODES,
    assign_plane,
    between_along_the_leg,
    end_pieces,
    margin,
    meniscus_side,
    pair_code,
)
from knee.objects.interiors import read_interiors

OFFSETS = np.arange(-3.0, 3.5, 0.5)
CORONAL = np.array([[0.0, 1.0], [0.0, 0.0], [-1.0, 0.0]])  # rows inferior, columns left
AXIAL = np.array([[0.0, 1.0], [1.0, 0.0], [0.0, 0.0]])  # rows posterior, columns left
SAGITTAL = np.array(
    [[0.0, 0.0], [0.0, 1.0], [-1.0, 0.0]]
)  # rows inferior, columns posterior


def rounded_box(shape, r0: int, r1: int, c0: int, c1: int, radius: int) -> np.ndarray:
    """The places inside a box with rounded corners: bones' ends are round, never square."""
    rows, cols = np.indices(shape)
    near_r = np.clip(rows, r0 + radius, r1 - 1 - radius)
    near_c = np.clip(cols, c0 + radius, c1 - 1 - radius)
    return (rows - near_r) ** 2 + (cols - near_c) ** 2 <= radius**2


def scene() -> np.ndarray:
    plane = np.full((140, 120), 2.0)  # air
    plane[:3, :] = 0.0  # the black margin
    plane[:, :3] = 0.0
    plane[10:132, 20:100] = 40.0  # the leg's soft tissue
    for top in (16, 76):  # the femur above, the tibia below
        shell = rounded_box(plane.shape, top, top + 46, 32, 88, 8)
        plane[shell] = 1.0  # the dark shell
        plane[rounded_box(plane.shape, top + 2, top + 44, 34, 86, 6)] = 100.0  # marrow
    plane[62:76, 38:82] = 25.0  # the joint between them
    return plane


FINE_MM = (
    0.5  # the meniscus scene's pixel, near the 0.44 mm of the proof's coronal planes
)


def fine_coronal_scene(menisci: bool = False) -> np.ndarray:
    """A coronal knee at half-millimetre pixels: bones with a 1 mm shell, round at their ends, and
    the joint between them; with `menisci`, a 7 mm wedge at each end of the joint, reaching out
    past the bones' edges as menisci do."""
    plane = np.full((280, 240), 2.0)  # air
    plane[20:264, 40:200] = 40.0  # the leg's soft tissue
    for top in (32, 152):  # the femur above, the tibia below
        plane[rounded_box(plane.shape, top, top + 92, 64, 176, 16)] = 1.0  # the shell
        plane[rounded_box(plane.shape, top + 2, top + 90, 66, 174, 14)] = (
            100.0  # marrow
        )
    plane[124:152, 76:164] = 25.0  # the joint between them
    if menisci:
        plane[124:152, 52:84] = 1.0
        plane[124:152, 156:188] = 1.0
    return plane


def sagittal_scene(fat_pad_reaching_down: bool = False) -> np.ndarray:
    """A sagittal knee at a knee's own proportions, front to the left, one place per millimetre.

    The femur runs off the top and the tibia off the bottom, with the joint between them at rows
    110 to 124. The patella sits in front of the femur's lower end, its middle about 2.5 cm above
    the femur's lowest point; the quadriceps tendon runs down to it through the soft tissue in
    front of the femur's shaft, whose middle lies some 7 cm above that point.
    """
    plane = np.full((200, 160), 2.0)  # air
    plane[:, 28:150] = 40.0  # the leg's soft tissue
    plane[:110, 60:120] = 1.0  # the femur's shell, running off the top
    plane[:108, 62:118] = 100.0  # its marrow
    plane[124:, 60:120] = 1.0  # the tibia's shell, running off the bottom
    plane[126:, 62:118] = 100.0  # its marrow
    plane[:66, 46:48] = 1.0  # the quadriceps tendon, down to the patella
    plane[66:100, 36:58] = 1.0  # the patella's shell
    plane[68:98, 38:56] = 100.0  # its marrow
    if fat_pad_reaching_down:  # its marrow runs on, unbroken, down past the femur
        plane[98:150, 38:56] = 100.0
    return plane


def assigned(plane, basis=CORONAL, pixel_mm: float = 1.0, knee: str = ""):
    spacing = (pixel_mm, pixel_mm)
    reading = read_interiors(plane, spacing, 5.0, 3.0, OFFSETS, "reference")
    return assign_plane(plane, reading, basis * pixel_mm, knee)


def test_the_scene_names_air_skin_femur_over_tibia_and_the_joint():
    result = assigned(scene())
    objects = result.objects
    for name in ("air", "skin", "femur", "tibia", "joint"):
        assert result.codes[name] == "identified"
    assert objects[40, 60] == OBJECT_CODES["femur"]
    assert objects[100, 60] == OBJECT_CODES["tibia"]
    assert objects[69, 60] == OBJECT_CODES["joint"]
    assert objects[70, 10] == OBJECT_CODES["air"]
    assert objects[70, 20] == OBJECT_CODES["skin"]


def test_nothing_is_named_in_the_black_margin():
    objects = assigned(scene()).objects
    assert not objects[:3].any() and not objects[:, :3].any()


def test_a_thin_dark_strip_along_the_frame_is_not_air_and_no_skin_is_traced_there():
    plane = np.full((60, 60), 40.0)
    plane[:3, :] = 0.0  # the black margin
    plane[3:6, :] = 2.0  # a 3 mm strip where the picture fades into it
    result = assigned(plane)
    assert result.codes["air"] == "abstain_no_field_outside_the_leg"
    assert result.codes["skin"] == "abstain_no_air"
    assert not result.objects.any()


def test_an_axial_slice_names_air_and_skin_but_no_femur_or_tibia():
    result = assigned(scene(), AXIAL)
    assert result.codes["femur"] == "abstain_leg_runs_through_the_plane"
    assert result.codes["air"] == "identified"
    assert not np.isin(result.objects, [3, 4, 5]).any()


def test_a_plane_with_no_tissue_names_nothing():
    result = assigned(np.full((40, 40), 1.0))
    assert result.codes["air"] == "abstain_no_leg"
    assert result.codes["femur"] == "abstain_fewer_than_two_territories"
    assert not result.objects.any()


def test_two_territories_side_by_side_are_not_femur_and_tibia():
    plane = np.full((80, 140), 2.0)
    plane[10:70, 10:130] = 40.0
    plane[10:70, 69:71] = 1.0  # a dark line splits the leg into left and right
    result = assigned(plane)
    assert result.codes["femur"] == "abstain_nothing_above_or_below_the_deepest"
    assert not np.isin(result.objects, [3, 4, 5]).any()


def test_the_patella_is_the_bone_in_front_of_the_femurs_lower_end():
    result = assigned(sagittal_scene(), SAGITTAL)
    assert result.codes["femur"] == "identified"
    assert result.codes["patella"] == "identified"
    assert result.objects[83, 47] == OBJECT_CODES["patella"]
    assert result.objects[50, 90] == OBJECT_CODES["femur"]
    assert result.objects[160, 90] == OBJECT_CODES["tibia"]


def test_a_region_in_front_that_reaches_down_past_the_femur_is_not_the_patella():
    result = assigned(sagittal_scene(fat_pad_reaching_down=True), SAGITTAL)
    assert result.codes["patella"] == "abstain_nothing_in_front_of_the_femurs_lower_end"
    assert not (result.objects == OBJECT_CODES["patella"]).any()


def test_the_patella_is_not_named_where_front_and_back_run_through_the_plane():
    coronal = assigned(scene(), CORONAL)
    assert coronal.codes["patella"] == "abstain_front_runs_through_the_plane"
    axial = assigned(scene(), AXIAL)
    assert axial.codes["patella"] == "abstain_no_femur"


def test_the_menisci_are_the_dark_wedges_at_the_two_ends_of_the_joint():
    result = assigned(fine_coronal_scene(menisci=True), pixel_mm=FINE_MM)
    assert result.codes["meniscus"] == "identified"
    assert result.menisci == 2
    assert result.objects[138, 66] == OBJECT_CODES["meniscus"]
    assert result.objects[138, 172] == OBJECT_CODES["meniscus"]
    assert result.objects[138, 120] == OBJECT_CODES["joint"]
    # the bones' thin shells along the joint are not menisci
    assert result.objects[123, 120] != OBJECT_CODES["meniscus"]
    # with no knee named in the header, they are not sided
    assert result.codes["meniscus_side"] == "abstain_header_names_no_knee"


def test_on_a_right_knee_the_medial_meniscus_is_the_one_toward_the_patients_left():
    result = assigned(fine_coronal_scene(menisci=True), pixel_mm=FINE_MM, knee="R")
    assert result.codes["meniscus_side"] == "from_the_header"
    # the scene's columns run toward the patient's left
    assert result.objects[138, 172] == OBJECT_CODES["medial_meniscus"]
    assert result.objects[138, 66] == OBJECT_CODES["lateral_meniscus"]


def test_on_a_left_knee_the_sides_swap():
    result = assigned(fine_coronal_scene(menisci=True), pixel_mm=FINE_MM, knee="L")
    assert result.objects[138, 172] == OBJECT_CODES["lateral_meniscus"]
    assert result.objects[138, 66] == OBJECT_CODES["medial_meniscus"]


def test_the_slices_own_frame_decides_the_side_not_the_pictures_left_and_right():
    columns_to_the_right = np.array([[0.0, -1.0], [0.0, 0.0], [-1.0, 0.0]])
    plane = fine_coronal_scene(menisci=True)
    result = assigned(plane, columns_to_the_right, FINE_MM, "R")
    assert result.objects[138, 172] == OBJECT_CODES["lateral_meniscus"]
    assert result.objects[138, 66] == OBJECT_CODES["medial_meniscus"]


def test_each_end_takes_a_piece_from_its_own_side_of_the_middle():
    # piece 2 sits exactly at the middle: it is still the only piece toward the left
    pieces = np.array([[1, 0, 2]])
    across = np.array([[0.0, 5.0, 5.0]])
    assert end_pieces(pieces, 2, across, 5.0) == [(1, False), (2, True)]


def test_a_knee_the_header_does_not_name_leaves_the_menisci_unsided():
    for word in ("", "B", "U", "r"):
        assert meniscus_side(word, True) == "meniscus"
    assert meniscus_side("R", True) == "medial"
    assert meniscus_side("L", True) == "lateral"


def test_no_menisci_without_thick_low_signal_or_on_a_sagittal_slice():
    plain = assigned(fine_coronal_scene(), pixel_mm=FINE_MM, knee="R")
    assert plain.codes["joint"] == "identified"
    assert plain.codes["meniscus"] == "abstain_no_thick_low_signal_in_the_joint"
    assert plain.codes["meniscus_side"] == "abstain_no_meniscus"
    sagittal = assigned(sagittal_scene(), SAGITTAL)
    assert sagittal.codes["meniscus"] == "abstain_side_to_side_runs_through_the_plane"
    assert assigned(scene(), AXIAL).codes["meniscus"] == "abstain_no_joint"


def test_pair_code_names_why():
    assert pair_code(False, 5, True) == "abstain_leg_runs_through_the_plane"
    assert pair_code(True, 1, False) == "abstain_fewer_than_two_territories"
    assert pair_code(True, 3, False) == "abstain_nothing_above_or_below_the_deepest"
    assert pair_code(True, 3, True) == "identified"


def test_margin_is_only_zeros_joined_to_the_frame():
    plane = np.ones((6, 6))
    plane[0, :] = 0.0
    plane[3, 3] = 0.0
    assert margin(plane).sum() == 6
    assert not margin(np.ones((4, 4))).any()


def test_between_follows_the_leg_whichever_way_the_rows_run():
    upper, lower = np.zeros((7, 1), dtype=bool), np.zeros((7, 1), dtype=bool)
    upper[1, 0], lower[5, 0] = True, True
    rows_inferior = np.array([[0.0, 1.0], [0.0, 0.0], [-1.0, 0.0]])
    rows_superior = np.array([[0.0, 1.0], [0.0, 0.0], [1.0, 0.0]])
    found = between_along_the_leg(upper, lower, rows_inferior)
    assert np.flatnonzero(found).tolist() == [2, 3, 4]
    assert not between_along_the_leg(upper, lower, rows_superior).any()
