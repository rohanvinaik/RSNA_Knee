"""Intent tests for the named objects: air, skin, femur over tibia, the joint, patella, menisci,
fibula, cartilage, the PCL and the ACL.

The scene is a small synthetic knee in a coronal frame (rows run inferior, columns run to the left,
one place per millimetre): air around a leg of soft tissue, a black margin along two sides of the
picture, and two bones stacked along the leg with a joint between them. The interiors stage reads
the scene exactly as the run does, and the assignments read that reading.
"""

import numpy as np

from knee.objects.assignments import (
    OBJECT_CODES,
    UNSEEN,
    Peak,
    PlaneAssignment,
    acl_code,
    acl_on_slice,
    assign_plane,
    between_along_the_leg,
    carried_bone,
    end_pieces,
    fibula_block,
    fibula_code,
    fibula_on_slice,
    laid_on,
    ligament_joining,
    main_slice,
    margin,
    meniscus_side,
    outer_step,
    pair_code,
    patella_code,
    with_partner,
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


def fine_coronal_scene(menisci: bool = False, cartilage: bool = False) -> np.ndarray:
    """A coronal knee at half-millimetre pixels: bones with a 1 mm shell, round at their ends, and
    the joint between them; with `menisci`, a 7 mm wedge at each end of the joint, reaching out
    past the bones' edges as menisci do; with `cartilage`, a 2 mm layer twice as bright as the
    marrow on each bone's joint surface, as it is with fat suppression."""
    plane = np.full((280, 240), 2.0)  # air
    plane[20:264, 40:200] = 40.0  # the leg's soft tissue
    for top in (32, 152):  # the femur above, the tibia below
        plane[rounded_box(plane.shape, top, top + 92, 64, 176, 16)] = 1.0  # the shell
        plane[rounded_box(plane.shape, top + 2, top + 90, 66, 174, 14)] = (
            100.0  # marrow
        )
    plane[124:152, 76:164] = 25.0  # the joint between them
    if cartilage:
        plane[124:128, 76:164] = 200.0  # on the femur
        plane[148:152, 76:164] = 200.0  # on the tibia
    if menisci:
        plane[124:152, 52:84] = 1.0
        plane[124:152, 156:188] = 1.0
    return plane


def sagittal_scene() -> np.ndarray:
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
    return plane


def assigned(
    plane,
    basis=CORONAL,
    pixel_mm: float = 1.0,
    knee: str = "",
    fat_suppressed: bool = False,
):
    spacing = (pixel_mm, pixel_mm)
    reading = read_interiors(plane, spacing, 5.0, 3.0, OFFSETS, "reference")
    return assign_plane(plane, reading, basis * pixel_mm, knee, fat_suppressed)


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


def test_with_fat_suppression_the_patella_is_the_bone_like_the_femur_at_its_lower_end():
    result = assigned(sagittal_scene(), SAGITTAL, fat_suppressed=True)
    patella = result.objects == OBJECT_CODES["patella"]
    assert result.codes["patella"] == "identified"
    assert patella[83, 47]  # its marrow
    assert patella.sum() == 30 * 18  # all of its marrow, and nothing else
    assert result.patella is not None
    # the soft tissue in front of the femur's shaft, by the tendon, is not the patella
    assert not patella[:66].any()
    assert result.objects[50, 90] == OBJECT_CODES["femur"]
    assert result.objects[160, 90] == OBJECT_CODES["tibia"]


def test_without_fat_suppression_the_patella_is_left_to_its_partner():
    # the fat pad is as bright as marrow there, so light cannot part them
    result = assigned(sagittal_scene(), SAGITTAL)
    assert result.codes["patella"] == "abstain_fat_as_bright_as_marrow"
    assert not (result.objects == OBJECT_CODES["patella"]).any()


def test_the_patella_is_not_looked_for_across_a_coronal_or_axial_slice():
    coronal = assigned(scene(), CORONAL, fat_suppressed=True)
    assert coronal.codes["patella"] == "abstain_front_to_back_runs_through_the_plane"
    axial = assigned(scene(), AXIAL, fat_suppressed=True)
    assert axial.codes["patella"] == "abstain_no_femur"
    for result in (coronal, axial):
        assert not (result.objects == OBJECT_CODES["patella"]).any()


def test_patella_code_names_why():
    assert patella_code(False, True, True, True, True) == (
        "abstain_front_to_back_runs_through_the_plane"
    )
    assert patella_code(True, False, True, True, True) == "abstain_no_femur"
    assert patella_code(True, True, False, True, True) == (
        "abstain_fat_as_bright_as_marrow"
    )
    assert patella_code(True, True, True, False, True) == (
        "abstain_no_peak_in_front_of_the_femur"
    )
    assert patella_code(True, True, True, True, False) == (
        "abstain_nothing_like_the_femur_at_its_peak"
    )
    assert patella_code(True, True, True, True, True) == "identified"


SAGITTAL_MM = SAGITTAL.astype(float)  # one place per millimetre


def test_a_slice_lays_its_names_on_the_same_place_at_another_pixel_size():
    origin = np.zeros(3)
    coarse = np.zeros((20, 20), dtype=np.int8)
    coarse[4:8, 6:10] = OBJECT_CODES["femur"]  # rows 2-4 mm down, columns 3-5 mm back
    seen = np.ones(coarse.shape, dtype=bool)
    seen[19, :] = False  # its last row is margin
    laid = laid_on(
        coarse,
        seen,
        origin,
        SAGITTAL_MM * 0.5,
        origin,
        SAGITTAL_MM * 0.4,
        (30, 30),
        2.0,
    )
    assert laid is not None
    assert laid[5, 8] == OBJECT_CODES["femur"]  # 2.0 mm down, 3.2 mm back
    assert laid[0, 0] == 0  # seen and named nothing
    assert laid[24, 0] == UNSEEN  # 9.6 mm down: the other slice's margin row
    assert laid[29, 29] == UNSEEN  # 11.6 mm: past the other slice's edge
    beside = origin + np.array([5.0, 0.0, 0.0])  # a slice 5 mm to the side
    assert (
        laid_on(
            coarse,
            seen,
            origin,
            SAGITTAL_MM * 0.5,
            beside,
            SAGITTAL_MM * 0.4,
            (30, 30),
            2.0,
        )
        is None
    )


def partner_scene() -> tuple[PlaneAssignment, np.ndarray, np.ndarray]:
    """A sagittal slice, front to the left, and what its partner laid on it: the femur at rows
    0-40, the tibia at rows 50-80, columns 20-40; this slice's femur also took in a block of soft
    tissue behind it (columns 40-50), which the partner's does not. The partner names a patella in
    front of the femur's lower end; this slice abstains on it but has its own peak there."""
    femur, tibia, patella = (
        OBJECT_CODES["femur"],
        OBJECT_CODES["tibia"],
        OBJECT_CODES["patella"],
    )
    own = np.zeros((90, 60), dtype=np.int8)
    own[0:40, 20:50] = femur
    own[50:80, 20:40] = tibia
    laid = np.zeros((90, 60), dtype=np.int8)
    laid[0:40, 20:40] = femur
    laid[50:80, 20:40] = tibia
    laid[25:36, 5:16] = patella
    labels = np.ones((90, 60), dtype=np.int32)
    peaks = (Peak(7, 5.0, (30, 10), -30.0),)
    codes = {
        "femur": "identified",
        "tibia": "identified",
        "joint": "identified",
        "patella": "abstain_fat_as_bright_as_marrow",
        "meniscus": "abstain_side_to_side_runs_through_the_plane",
    }
    return PlaneAssignment(own, codes, peaks, 1, 2, 0), labels, laid


PARTNER_CODES = {
    "femur": "identified",
    "tibia": "identified",
    "patella": "identified",
    "meniscus": "abstain_side_to_side_runs_through_the_plane",
}


def test_two_slices_name_a_bone_where_they_agree_and_lay_on_what_only_one_sees():
    assignment, labels, laid = partner_scene()
    nowhere = np.zeros(labels.shape, dtype=bool)
    objects, codes = with_partner(
        assignment, labels, SAGITTAL_MM, nowhere, laid, PARTNER_CODES
    )
    assert codes["femur"] == codes["tibia"] == "agreed_with_its_partner"
    assert objects[10, 30] == OBJECT_CODES["femur"]
    assert objects[10, 45] == 0  # the soft tissue only this slice's femur took in
    assert codes["patella"] == "laid_from_its_partner"
    assert objects[30, 10] == OBJECT_CODES["patella"]
    assert codes["joint"] == "identified"
    assert objects[45, 30] == OBJECT_CODES["joint"]
    # where the partner's picture does not reach, it has no say: this slice keeps its own
    unseen = laid.copy()
    unseen[:, 40:] = UNSEEN
    objects, _ = with_partner(
        assignment, labels, SAGITTAL_MM, nowhere, unseen, PARTNER_CODES
    )
    assert objects[10, 45] == OBJECT_CODES["femur"]


def test_two_slices_that_disagree_on_where_the_patella_is_name_none():
    assignment, labels, laid = partner_scene()
    laid[laid == OBJECT_CODES["patella"]] = 0
    laid[60:70, 5:16] = OBJECT_CODES["patella"]  # not at this slice's own peak
    objects, codes = with_partner(
        assignment,
        labels,
        SAGITTAL_MM,
        np.zeros(labels.shape, dtype=bool),
        laid,
        PARTNER_CODES,
    )
    assert codes["patella"] == "abstain_the_two_slices_disagree"
    assert not (objects == OBJECT_CODES["patella"]).any()


def test_the_cartilage_one_slice_shows_is_laid_on_the_other_slice_of_the_same_place():
    # one leg, so the same cartilage (Rohan: «It's literally the same leg»)
    assignment, labels, laid = partner_scene()
    laid[40:42, 20:40] = OBJECT_CODES["femoral_cartilage"]
    laid[48:50, 20:40] = OBJECT_CODES["tibial_cartilage"]
    objects, codes = with_partner(
        assignment,
        labels,
        SAGITTAL_MM,
        np.zeros(labels.shape, dtype=bool),
        laid,
        {**PARTNER_CODES, "cartilage": "identified"},
    )
    assert codes["cartilage"] == "laid_from_its_partner"
    assert objects[40, 30] == OBJECT_CODES["femoral_cartilage"]
    assert objects[49, 30] == OBJECT_CODES["tibial_cartilage"]
    assert objects[45, 30] == OBJECT_CODES["joint"]


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


def test_with_fat_suppression_the_cartilage_is_the_bright_layer_on_each_bone():
    plane = fine_coronal_scene(cartilage=True)
    result = assigned(plane, pixel_mm=FINE_MM, fat_suppressed=True)
    assert result.codes["cartilage"] == "identified"
    assert result.objects[126, 120] == OBJECT_CODES["femoral_cartilage"]
    assert result.objects[150, 120] == OBJECT_CODES["tibial_cartilage"]
    assert (
        result.objects[138, 120] == OBJECT_CODES["joint"]
    )  # the joint between the layers
    assert result.objects[100, 120] == OBJECT_CODES["femur"]


def test_without_fat_suppression_or_across_a_sagittal_slice_no_cartilage_is_named():
    plain = assigned(fine_coronal_scene(cartilage=True), pixel_mm=FINE_MM)
    assert plain.codes["cartilage"] == (
        "abstain_not_brighter_than_marrow_without_fat_suppression"
    )
    sagittal = assigned(sagittal_scene(), SAGITTAL, fat_suppressed=True)
    assert sagittal.codes["cartilage"] == "abstain_side_to_side_runs_through_the_plane"
    for result in (plain, sagittal):
        assert not np.isin(
            result.objects,
            [OBJECT_CODES["femoral_cartilage"], OBJECT_CODES["tibial_cartilage"]],
        ).any()


def test_the_pcl_is_the_thick_uniformly_dark_band_joining_the_femur_and_the_tibia():
    # one place per millimetre: the femur above, the tibia below, soft tissue between
    plane = np.full((80, 60), 40.0)
    objects = np.zeros((80, 60), dtype=np.int8)
    for name, rows in (("femur", slice(0, 30)), ("tibia", slice(45, 80))):
        objects[rows, 10:40] = OBJECT_CODES[name]
        plane[rows, 10:40] = 100.0
    plane[25:50, 41:48] = (
        12.0  # a band 7 mm thick behind both bones, at a ligament's light
    )
    plane[30:45, 20:22] = 12.0  # a line 2 mm thin between them: no ligament's thickness
    plane[60:70, 50:58] = 12.0  # as dark, but joined to neither bone
    band = ligament_joining(plane, objects, np.array([1.0, 1.0]))
    assert band[35, 44]
    assert not band[35, 21]
    assert not band[65, 54]
    assert not band[10, 20]  # the femur's own places are never the band


def test_with_fat_suppression_or_across_a_coronal_slice_no_pcl_is_named():
    suppressed = assigned(sagittal_scene(), SAGITTAL, fat_suppressed=True)
    assert suppressed.codes["pcl"] == (
        "abstain_marrow_as_dark_as_a_ligament_with_fat_suppression"
    )
    coronal = assigned(scene(), CORONAL)
    assert coronal.codes["pcl"] == "abstain_front_to_back_runs_through_the_plane"
    plain = assigned(sagittal_scene(), SAGITTAL)
    assert plain.codes["pcl"] == "abstain_no_dark_band_joins_the_bones"
    for result in (suppressed, coronal, plain):
        assert not (result.objects == OBJECT_CODES["pcl"]).any()


def test_the_acl_is_the_region_whose_peak_lies_in_the_joint_between_the_bones():
    # one place per millimetre, front to the left: the femur above, the tibia below, a body in the
    # notch between them, and a body in front of the bones, beside the joint but not in it
    labels = np.zeros((80, 60), dtype=np.int32)
    labels[0:30, 10:50] = 1  # the femur
    labels[45:80, 10:50] = 2  # the tibia
    labels[30:45, 20:40] = 3  # in the notch, between them
    labels[30:45, 0:8] = 4  # in front of them
    femur, tibia = labels == 1, labels == 2
    peaks = (
        Peak(1, 15.0, (15, 30), 0.0),
        Peak(2, 14.0, (60, 30), 0.0),
        Peak(4, 4.0, (37, 4), 0.0),
        Peak(3, 3.0, (37, 30), 0.0),
    )
    nowhere = np.zeros(labels.shape, dtype=bool)
    acl = acl_on_slice(labels, peaks, femur, tibia, SAGITTAL_MM, nowhere)
    assert acl[37, 30] and acl.sum() == 15 * 20
    assert not acl[37, 4]  # beside the joint, not in it
    # with nothing between the bones whose peak lies there, nothing is named
    alone = acl_on_slice(labels, peaks[:3], femur, tibia, SAGITTAL_MM, nowhere)
    assert not alone.any()


def test_a_bone_is_carried_to_the_next_slice_as_the_regions_that_were_it():
    before = np.zeros((40, 20), dtype=bool)
    before[0:30, :] = True  # the bone on the middle slice
    labels = np.zeros((40, 20), dtype=np.int32)
    labels[0:20, :] = 1  # inside it
    labels[20:28, :] = 2  # inside it too: the lens split the bone here
    labels[28:40, :] = 3  # two rows of twelve inside it: not the bone
    carried = carried_bone(labels, before)
    assert carried[10, 5] and carried[24, 5]
    assert not carried[35, 5]
    assert not carried_bone(labels, np.zeros(before.shape, dtype=bool)).any()


def test_the_acls_slice_is_the_middles_neighbour_on_the_knees_outer_side():
    # the outer side is the patient's right for a right knee and the left for a left one; where
    # the next slice lies toward the patient's left, a right knee's outer neighbour is the one before
    assert outer_step("R", 3.0) == -1
    assert outer_step("R", -3.0) == 1
    assert outer_step("L", 3.0) == 1
    assert outer_step("L", -3.0) == -1


def test_acl_code_names_why():
    assert acl_code(False, "R", True, True, True) == (
        "abstain_front_to_back_runs_through_the_plane"
    )
    assert acl_code(True, "", True, True, True) == "abstain_header_names_no_knee"
    assert acl_code(True, "R", False, True, True) == (
        "abstain_no_femur_and_tibia_to_carry"
    )
    # without fat suppression the fat and the ligament fall in one region
    assert acl_code(True, "R", True, False, True) == (
        "abstain_not_walled_off_without_fat_suppression"
    )
    assert acl_code(True, "L", True, True, False) == "abstain_no_region_in_the_joint"
    assert acl_code(True, "L", True, True, True) == "identified"


def test_a_joint_with_nothing_bright_against_the_bones_names_no_cartilage():
    result = assigned(fine_coronal_scene(), pixel_mm=FINE_MM, fat_suppressed=True)
    assert result.codes["cartilage"] == "abstain_nothing_bright_against_the_bones"


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


def disc(shape, centre_rc, radius_px) -> np.ndarray:
    rows, cols = np.indices(shape)
    return (rows - centre_rc[0]) ** 2 + (cols - centre_rc[1]) ** 2 <= radius_px**2


TIBIA = (
    0,
    58,
    12,
    98,
    6,
)  # the tibia's marrow, rows and columns, running off the block's top


def fibula_scene(fibula_col: int | None = 120, high: bool = False) -> np.ndarray:
    """A sagittal block at half-millimetre pixels, front to the left and the top at row 0: soft
    tissue, the tibia running off the top down to 3 cm, and the fibular head, a bone 2 cm across
    with the tibia's marrow, its middle 6.5 cm below the tibia's top. With `high`, a region as
    bright as the tibia's marrow 2 cm below its top, behind it."""
    plane = np.full((200, 160), 40.0)  # soft tissue, darker than marrow
    plane[rounded_box(plane.shape, 0, 60, 10, 100, 8)] = 1.0  # the tibia's shell
    plane[rounded_box(plane.shape, *TIBIA)] = 100.0  # its marrow
    if fibula_col is not None:
        plane[disc(plane.shape, (130, fibula_col), 22)] = 1.0
        plane[disc(plane.shape, (130, fibula_col), 20)] = 100.0
    if high:
        plane[disc(plane.shape, (40, 140), 14)] = 1.0
        plane[disc(plane.shape, (40, 140), 12)] = 100.0
    return plane


def places(shape) -> np.ndarray:
    """A sagittal block's places in the scanner's millimetres: rows run down, columns to the back."""
    rows, cols = np.indices(shape)
    return np.stack((np.zeros(shape), cols * FINE_MM, -rows * FINE_MM), axis=-1)


TIBIA_MIDDLE = np.array([0.0, 27.5, -14.5])  # column 55, row 29


def fibula_in(plane, tibia_before=None, cut=None):
    reading = read_interiors(plane, (FINE_MM, FINE_MM), 5.0, 3.0, OFFSETS, "reference")
    if tibia_before is None:
        tibia_before = rounded_box(plane.shape, *TIBIA)
    if cut is None:
        cut = np.zeros(plane.shape, dtype=bool)  # the block is the whole picture
    found = fibula_on_slice(
        reading.labels,
        plane,
        FINE_MM**2,
        places(plane.shape),
        tibia_before,
        TIBIA_MIDDLE,
        cut,
    )
    return reading, found


def test_the_fibula_is_the_bone_like_the_tibia_well_below_its_top_and_behind_it():
    reading, (territory, area) = fibula_in(fibula_scene())
    assert territory == reading.labels[130, 120]
    assert 280 < area < 350  # a disc 2 cm across holds 314 mm²


def test_a_bright_region_near_the_tibias_top_is_not_the_fibula():
    assert fibula_in(fibula_scene(fibula_col=None, high=True))[1] == (None, 0.0)


def test_soft_tissue_is_not_the_fibula():
    assert fibula_in(fibula_scene(fibula_col=None))[1] == (None, 0.0)


def test_a_bone_in_front_of_the_tibias_middle_is_not_the_fibula():
    assert fibula_in(fibula_scene(fibula_col=30))[1] == (None, 0.0)


def test_where_the_tibia_is_not_on_the_slice_no_fibula_is_named():
    plane = fibula_scene()
    nowhere = np.zeros(plane.shape, dtype=bool)
    assert fibula_in(plane, nowhere)[1] == (None, 0.0)


def test_a_bone_the_blocks_edge_cuts_through_is_not_the_fibula():
    plane = fibula_scene()[
        :, :130
    ]  # the block's edge runs through the bone at column 129
    cut = np.zeros(plane.shape, dtype=bool)
    cut[:, -1] = True  # that edge is the block's, not the picture's
    assert fibula_in(plane, cut=cut)[1] == (None, 0.0)
    whole_picture = fibula_in(plane)[
        1
    ]  # the same edge as the picture's own: it may run off
    assert whole_picture[0] is not None


def test_the_fibula_block_is_below_the_tibias_top_on_the_outer_side():
    # x toward the patient's left, y toward the back, z up; the tibia's middle at the origin, its
    # top at z = 20
    centres = np.array(
        [
            [
                [-10.0, 10.0, -10.0],
                [10.0, 10.0, -10.0],
                [-10.0, -10.0, -10.0],
                [-10.0, 10.0, 30.0],
            ]
        ]
    )
    middle = np.zeros(3)
    assert fibula_block(centres, 20.0, middle, "R").tolist() == [
        [True, False, True, False]
    ]
    assert fibula_block(centres, 20.0, middle, "L").tolist() == [
        [False, True, False, False]
    ]
    assert not fibula_block(centres, 20.0, middle, "").any()


def test_the_main_slice_is_where_the_region_is_largest():
    assert main_slice([0.0, 120.0, 452.0, 300.0]) == 2
    assert main_slice([0.0, 0.0]) is None


def test_fibula_code_names_why():
    assert fibula_code("", True, False, True) == "abstain_header_names_no_knee"
    assert fibula_code("R", False, False, True) == "abstain_no_tibia"
    # fat suppression darkens marrow to the light of muscle
    assert (
        fibula_code("R", True, True, True) == "abstain_marrow_suppressed_with_the_fat"
    )
    assert (
        fibula_code("R", True, False, False)
        == "abstain_no_bone_like_the_tibia_below_it"
    )
    assert fibula_code("L", True, False, True) == "identified"


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
