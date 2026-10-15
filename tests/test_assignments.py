"""Intent tests for the named objects: air, skin, femur over tibia, the joint, patella, menisci,
fibula, cartilage, the PCL, the ACL, the MCL, the LCL, the joint's fluid, Hoffa's fat pad, the
suprapatellar fat, the medial gastrocnemius head, the semimembranosus tendon, and the patellar and
quadriceps tendons.

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
    band_joining,
    between_along_the_leg,
    carried_bone,
    dark_bands,
    end_pieces,
    extensor_tendons,
    fat_pad_code,
    fat_under_the_skin,
    fibula_block,
    fibula_code,
    fibula_on_slice,
    fluid_code,
    gastrocnemius_code,
    gastrocnemius_head,
    inner_condyle,
    laid_on,
    lcl_attachment,
    lcl_code,
    lcl_on_slice,
    ligament_on_the_inner_side,
    main_slice,
    margin,
    mcl_code,
    meniscus_side,
    muscle_bodies,
    muscle_code,
    outer_step,
    pair_code,
    patella_code,
    places_on_slice,
    region_holding,
    rest_of_the_patellas_territory,
    semimembranosus_code,
    semimembranosus_on_slice,
    slice_through,
    subcutaneous_code,
    tendon_code,
    tibia_top_slice,
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
    fluid_sensitive: bool = False,
):
    spacing = (pixel_mm, pixel_mm)
    reading = read_interiors(plane, spacing, 5.0, 3.0, OFFSETS, "reference")
    return assign_plane(
        plane, reading, basis * pixel_mm, knee, fat_suppressed, fluid_sensitive
    )


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
    # a band 7 mm thick behind both bones, at a ligament's light
    plane[25:50, 41:48] = 12.0
    plane[30:45, 20:22] = 12.0  # a line 2 mm thin between them: no ligament's thickness
    plane[60:70, 50:58] = 12.0  # as dark, but joined to neither bone
    # the band's darkest places, stored as zero: tissue, not the margin
    plane[34:37, 43:46] = 0.0
    plane[:, 0:3] = 0.0  # the black margin along the frame
    spacing = np.array([1.0, 1.0])
    bands = dark_bands(plane, objects, spacing, margin(plane))
    femur, tibia = (objects == OBJECT_CODES[name] for name in ("femur", "tibia"))
    band = band_joining(bands, femur, tibia, spacing)
    assert band[35, 44]
    assert not band[35, 21]
    assert not band[65, 54]
    assert not band[10, 20]
    assert not band[40, 1]


def test_the_extensor_tendons_are_the_band_from_the_patella_to_the_tibia_split_at_the_patella():
    # one place per millimetre, rows running down and columns back, front to the left: the femur
    # behind, the patella in front of its lower end, the tibia below; one dark band runs down the
    # front from above the patella, along its front, to the tibia's front
    plane = np.full((120, 80), 40.0)
    objects = np.zeros((120, 80), dtype=np.int8)
    for name, rows, cols in (
        ("femur", slice(0, 60), slice(40, 75)),
        ("patella", slice(40, 60), slice(22, 34)),
        ("tibia", slice(75, 120), slice(20, 75)),
    ):
        objects[rows, cols] = OBJECT_CODES[name]
        plane[rows, cols] = 100.0
    plane[10:40, 17:23] = 5.0  # above the patella: the quadriceps tendon
    plane[38:62, 15:22] = 5.0  # along the patella's front
    plane[60:78, 17:23] = 5.0  # below it, down to the tibia: the patellar tendon
    plane[64:70, 19:21] = 0.0  # the patellar tendon's darkest places, stored as zero
    # the fat pad behind it, named first, over the band's back edge
    objects[62:70, 21:23] = OBJECT_CODES["hoffa_fat_pad"]
    plane[90:100, 2:8] = 5.0  # as dark, but joined to neither
    spacing = np.array([1.0, 1.0])
    bands = dark_bands(plane, objects, spacing, margin(plane))
    below, above = extensor_tendons(bands, objects, spacing, SAGITTAL)
    # the patellar tendon, its darkest places and the fat pad's edge too
    assert below[66, 18] and below[66, 20] and below[65, 22]
    assert above[20, 20]  # the quadriceps tendon
    assert not below[50, 18] and not above[50, 18]  # alongside the patella: neither
    assert not below[50, 25] and not above[50, 25]  # the patella
    assert not below[95, 5]
    # without the patella the band has no upper end: neither tendon
    alone = np.where(objects == OBJECT_CODES["patella"], 0, objects)
    nothing = extensor_tendons(bands, alone, spacing, SAGITTAL)
    assert not nothing[0].any() and not nothing[1].any()


def test_tendon_code_names_why():
    assert tendon_code(False, False, True, True) == (
        "abstain_front_to_back_runs_through_the_plane"
    )
    assert tendon_code(True, True, True, True) == (
        "abstain_not_uniformly_dark_with_fat_suppression"
    )
    assert tendon_code(True, False, False, True) == "abstain_no_patella_and_tibia"
    assert tendon_code(True, False, True, False) == (
        "abstain_no_dark_band_below_the_patella"
    )
    assert tendon_code(True, False, True, False, above=True) == (
        "abstain_no_dark_band_above_the_patella"
    )
    assert tendon_code(True, False, True, True) == "identified"


def test_read_alone_a_slice_says_why_it_cannot_name_the_extensor_tendons():
    plain = assigned(sagittal_scene(), SAGITTAL)
    suppressed = assigned(sagittal_scene(), SAGITTAL, fat_suppressed=True)
    coronal = assigned(scene(), CORONAL)
    for name in ("patellar_tendon", "quadriceps_tendon"):
        assert plain.codes[name] == "abstain_no_patella_and_tibia"
        assert suppressed.codes[name] == (
            "abstain_not_uniformly_dark_with_fat_suppression"
        )
        assert coronal.codes[name] == "abstain_front_to_back_runs_through_the_plane"
    # the bands are kept where the PCL is read, and only there
    assert plain.bands is not None
    assert (
        suppressed.bands is None and coronal.bands is None
    )  # the femur's own places are never the band


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


def mcl_scene() -> tuple[np.ndarray, np.ndarray]:
    """A coronal slice at one place per millimetre, columns toward the patient's left: the femur
    above and the tibia below, the joint between them with the medial meniscus at its end toward
    the left and the lateral at the other, and the low-signal lens's marks: a band on each side
    from beside the femur to beside the tibia, a line further out, and a band beside the tibia
    alone."""
    objects = np.zeros((80, 70), dtype=np.int8)
    objects[0:30, 10:46] = OBJECT_CODES["femur"]
    objects[40:80, 10:46] = OBJECT_CODES["tibia"]
    objects[30:40, 14:42] = OBJECT_CODES["joint"]
    objects[30:40, 42:46] = OBJECT_CODES["medial_meniscus"]
    objects[30:40, 10:14] = OBJECT_CODES["lateral_meniscus"]
    dark = np.zeros(objects.shape, dtype=bool)
    dark[22:50, 47:49] = True  # on the medial meniscus's side, across the joint line
    dark[22:50, 7:9] = True  # the same on the other side
    dark[:, 58:60] = True  # further out: near neither bone
    dark[60:75, 47:49] = True  # beside the tibia alone
    return dark, objects


def test_the_mcl_is_the_low_signal_joining_the_bones_on_the_inner_side():
    dark, objects = mcl_scene()
    nowhere = np.zeros(objects.shape, dtype=bool)
    mcl = ligament_on_the_inner_side(dark, objects, CORONAL, nowhere)
    assert mcl[35, 47] and mcl[25, 48] and mcl[45, 47]
    assert not mcl[35, 7]  # it joins both bones too, but on the other side
    assert not mcl[10, 58]
    assert not mcl[70, 47]
    # with no medial meniscus to say which side is inner, nothing is named
    objects[objects == OBJECT_CODES["medial_meniscus"]] = OBJECT_CODES["joint"]
    unsided = ligament_on_the_inner_side(dark, objects, CORONAL, nowhere)
    assert not unsided.any()


def test_the_mcl_one_slice_shows_is_laid_on_the_other_slice_of_the_same_place():
    assignment, labels, laid = partner_scene()
    laid[30:60, 42:44] = OBJECT_CODES["mcl"]
    objects, codes = with_partner(
        assignment,
        labels,
        SAGITTAL_MM,
        np.zeros(labels.shape, dtype=bool),
        laid,
        {**PARTNER_CODES, "mcl": "identified"},
    )
    assert codes["mcl"] == "laid_from_its_partner"
    # where this slice's own femur took in the soft tissue the partner names the MCL, the two
    # disagree on the femur, so the MCL is laid there too
    assert objects[35, 43] == OBJECT_CODES["mcl"]
    assert objects[55, 43] == OBJECT_CODES["mcl"]


def test_the_air_and_skin_one_slice_names_are_laid_on_the_other_slice_of_the_same_place():
    # where the lens draws the air into its territories the slice names none of its own; the
    # partner's air and skin are laid on, last, onto the places nothing else holds
    assignment, labels, laid = partner_scene()
    laid[:, 0:3] = OBJECT_CODES["air"]
    laid[:, 3] = OBJECT_CODES["skin"]
    own_codes = {
        **assignment.codes,
        "air": "abstain_no_field_outside_the_leg",
        "skin": "abstain_no_air",
    }
    alone = PlaneAssignment(assignment.objects, own_codes, assignment.peaks, 1, 2, 0)
    objects, codes = with_partner(
        alone,
        labels,
        SAGITTAL_MM,
        np.zeros(labels.shape, dtype=bool),
        laid,
        {**PARTNER_CODES, "air": "identified", "skin": "identified"},
    )
    assert codes["air"] == codes["skin"] == "laid_from_its_partner"
    assert objects[10, 1] == OBJECT_CODES["air"]
    assert objects[10, 3] == OBJECT_CODES["skin"]


def test_a_part_the_partner_names_is_laid_over_the_rest_of_the_field():
    # without fat suppression a body of fluid is as dark as muscle, so this slice named it muscle
    # by elimination; the fat-suppressed partner names it fluid, and the fluid is laid on there
    assignment, labels, laid = partner_scene()
    own = assignment.objects.copy()
    own[42:48, 20:40] = OBJECT_CODES["muscle"]
    laid[42:48, 20:40] = OBJECT_CODES["joint_fluid"]
    alone = PlaneAssignment(own, dict(assignment.codes), assignment.peaks, 1, 2, 0)
    objects, codes = with_partner(
        alone,
        labels,
        SAGITTAL_MM,
        np.zeros(labels.shape, dtype=bool),
        laid,
        {**PARTNER_CODES, "joint_fluid": "identified"},
    )
    assert codes["joint_fluid"] == "laid_from_its_partner"
    assert objects[45, 30] == OBJECT_CODES["joint_fluid"]


def test_the_fat_under_the_skin_is_the_layer_as_bright_as_marrow_reaching_the_skin():
    # one place per millimetre, the leg's edge to the left: the skin, the fat under it, the
    # fascia's thin dark line, muscle at about half the marrow's light, and the femur; deep fat
    # lies behind the fascia
    plane = np.full((40, 60), 45.0)
    objects = np.zeros((40, 60), dtype=np.int8)
    objects[:, 0] = OBJECT_CODES["skin"]
    plane[:, 1:7] = 90.0  # the fat under the skin
    plane[:, 7] = 10.0  # the fascia
    plane[5:15, 8:14] = 95.0  # the deep fat behind it
    objects[:, 40:60] = OBJECT_CODES["femur"]
    plane[:, 40:60] = 100.0  # its marrow
    plane[20:24, 20:24] = 95.0  # as bright, but far from the skin
    spacing = np.array([1.0, 1.0])
    fat = fat_under_the_skin(plane, objects, spacing)
    assert fat[10, 3] and fat[30, 6]
    assert not fat[10, 10]  # the deep fat
    assert not fat[30, 20]  # muscle
    assert not fat[22, 22]
    assert not fat[10, 50]  # the femur's marrow, already named
    no_skin = np.where(objects == OBJECT_CODES["skin"], 0, objects)
    assert not fat_under_the_skin(plane, no_skin, spacing).any()


def test_subcutaneous_code_names_why():
    assert subcutaneous_code(True, True, True, True) == (
        "abstain_fat_as_dark_as_muscle_with_fat_suppression"
    )
    assert subcutaneous_code(False, False, True, True) == "abstain_no_skin"
    assert subcutaneous_code(False, True, False, True) == "abstain_no_femur"
    assert (
        subcutaneous_code(False, True, True, False) == "abstain_no_fat_under_the_skin"
    )
    assert subcutaneous_code(False, True, True, True) == "identified"


def test_muscle_is_the_legs_bodies_darker_than_fat_a_centimetre_across():
    # one place per millimetre: air at the left, then the leg, its soft tissue as bright as fat;
    # the femur's marrow at the right; a black margin along the bottom of the picture
    plane = np.full((80, 80), 95.0)
    objects = np.zeros((80, 80), dtype=np.int8)
    objects[:, 0:5] = OBJECT_CODES["air"]
    plane[:, 0:5] = 5.0
    objects[0:40, 60:80] = OBJECT_CODES["femur"]
    plane[0:40, 60:80] = 100.0
    plane[10:30, 20:40] = 45.0  # a belly 2 cm across
    plane[40:55, 20:24] = 45.0  # a tendon 4 mm thick
    plane[0:60, 50] = 10.0  # a fascia line, 1 mm
    plane[65:80, :] = 0.0  # the black margin, 15 mm deep
    spacing = np.array([1.0, 1.0])
    muscle = muscle_bodies(plane, objects, spacing, margin(plane))
    assert muscle[20, 30]
    assert not muscle[47, 22]  # the tendon
    assert not muscle[30, 50]  # the fascia line
    assert not muscle[20, 2]  # the air
    assert not muscle[72, 30]  # the black margin
    assert not muscle[20, 70]  # the femur
    no_air = np.where(objects == OBJECT_CODES["air"], 0, objects)
    assert not muscle_bodies(plane, no_air, spacing, margin(plane)).any()


def test_muscle_code_names_why():
    assert muscle_code(True, True, True, True) == (
        "abstain_as_grey_as_fat_with_fat_suppression"
    )
    assert muscle_code(False, False, True, True) == "abstain_no_air"
    assert muscle_code(False, True, False, True) == "abstain_no_femur"
    assert muscle_code(False, True, True, False) == "abstain_no_muscle_body"
    assert muscle_code(False, True, True, True) == "identified"


def test_mcl_code_names_why():
    assert mcl_code(False, True, True) == "abstain_side_to_side_runs_through_the_plane"
    assert mcl_code(True, False, True) == "abstain_no_medial_meniscus"
    assert mcl_code(True, True, False) == (
        "abstain_no_low_signal_joins_the_bones_on_the_inner_side"
    )
    assert mcl_code(True, True, True) == "identified"


def lcl_scene() -> np.ndarray:
    """A coronal slice's regions at one place per millimetre, columns toward the patient's left: the
    femur (1) above; the tibia below, sharing one region (2) with the fibula's head, which lies
    toward the patient's right, as a T1 may draw them; a band (3) on the fibula's side from beside
    the femur down to the fibula's head; the same band (4) on the other side, beside the femur and
    the tibia; and a region (5) in the joint, its middle at the tibia's."""
    labels = np.zeros((80, 70), dtype=np.int32)
    labels[0:31, 20:51] = 1  # the femur
    labels[40:80, 20:51] = 2  # the tibia
    labels[60:80, 5:20] = 2  # the fibula's head, in the tibia's region
    labels[25:60, 10:20] = 3  # the band on the fibula's side
    labels[25:60, 51:59] = 4  # the band on the other side
    labels[31:40, 20:51] = 5  # in the joint
    return labels


def test_the_lcl_is_the_region_joining_the_femur_and_the_fibula_on_the_fibulas_side():
    labels = lcl_scene()
    across = np.indices(labels.shape)[1].astype(float)  # mm toward the patient's left
    femur, fibula = labels == 1, labels == 2
    lcl = lcl_on_slice(labels, femur, fibula, across, 35.0, 12.0, np.ones(2))
    assert lcl[40, 15] and lcl.sum() == 35 * 10
    assert not lcl[40, 55]  # it joins both too, but on the other side
    assert not lcl[35, 35]  # in the joint: on neither side of the tibia's middle
    assert not lcl[10, 30] and not lcl[70, 10]  # the bones are never the LCL
    # with no fibula on the slice, nothing is named
    nowhere = np.zeros(labels.shape, dtype=bool)
    assert not lcl_on_slice(
        labels, femur, nowhere, across, 35.0, 12.0, np.ones(2)
    ).any()


def test_the_lcl_attaches_8_mm_behind_the_front_of_the_fibula():
    # x toward the patient's left, y toward the back, z up
    fibula = np.array(
        [[-50.0, 10.0, -30.0], [-52.0, 40.0, -34.0], [-54.0, 25.0, -32.0]]
    )
    assert np.allclose(lcl_attachment(fibula), [-52.0, 18.2, -32.0])


def test_the_lcls_slice_is_the_one_through_where_it_attaches():
    # coronal slices 3.4 mm apart, each 3 mm thick, stepping toward the back
    origins = np.array([[0.0, 3.4 * z, 0.0] for z in range(6)])
    normal = np.array([0.0, 1.0, 0.0])
    thicknesses = [3.0] * 6
    assert slice_through(np.array([9.0, 7.0, -4.0]), origins, normal, thicknesses) == 2
    beyond = np.array([0.0, 30.0, 0.0])  # 13 mm past the last slice
    assert slice_through(beyond, origins, normal, thicknesses) is None


def test_a_slice_holds_the_places_within_half_its_thickness():
    origin = np.array([0.0, 5.0, 0.0])
    near = np.array([[3.0, 5.4, -2.0]])  # 0.4 mm off the plane: row 2, column 3
    off = np.array([[3.0, 9.0, -2.0]])  # 4 mm off it
    held = places_on_slice(near, origin, CORONAL, (6, 6), 3.0)
    assert held[2, 3] and held.sum() == 1
    assert not places_on_slice(off, origin, CORONAL, (6, 6), 3.0).any()


def test_the_region_holding_most_of_the_places_is_the_one_that_holds_them():
    labels = np.array([[1, 1, 2, 2], [0, 0, 2, 2]])
    places = np.array([[False, True, True, True], [True, False, True, False]])
    assert region_holding(labels, places).tolist() == (labels == 2).tolist()
    assert not region_holding(labels, np.zeros(labels.shape, dtype=bool)).any()


def back_of_knee_scene() -> tuple[np.ndarray, tuple[Peak, ...]]:
    """An axial slice's regions at one place per millimetre, rows toward the back, columns toward
    the patient's left, the notch at column 40: the front of the knee (1); the femur's two condyles,
    toward the patient's right (2) and left (3); and behind them the two heads of the calf's muscle
    (4, 5). Their peaks, the deepest first, as the lens finds them on the proof: the front, the
    condyles, then the muscles."""
    labels = np.zeros((60, 80), dtype=np.int32)
    labels[0:15, 10:70] = 1  # the front
    labels[15:35, 10:38] = 2  # the condyle toward the right
    labels[15:35, 42:70] = 3  # the condyle toward the left
    labels[38:58, 10:38] = 4  # the head behind the right-hand condyle
    labels[38:58, 42:70] = 5  # the head behind the left-hand condyle
    peaks = (
        Peak(1, 17.0, (8, 40), 0.0),
        Peak(3, 16.0, (25, 56), 0.0),
        Peak(2, 15.0, (25, 24), 0.0),
        Peak(4, 12.0, (48, 24), 0.0),
        Peak(5, 10.0, (48, 56), 0.0),
    )
    return labels, peaks


def test_the_medial_gastrocnemius_head_is_the_body_behind_the_inner_condyle():
    labels, peaks = back_of_knee_scene()
    rows, cols = np.indices(labels.shape)
    back, toward_left = rows.astype(float), cols - 40.0
    bone = np.zeros(labels.shape, dtype=bool)
    # the femur carried from a coronal slice, across both condyles
    bone[25, 12:68] = True
    # a right knee: the inner side is toward the patient's left
    condyle = inner_condyle(peaks, labels, bone, toward_left)
    assert condyle is not None and condyle.territory == 3
    head = gastrocnemius_head(peaks, labels, bone, condyle, back, toward_left)
    assert head[48, 56] and head.sum() == 20 * 28
    # a left knee: the inner side is toward the patient's right
    condyle = inner_condyle(peaks, labels, bone, -toward_left)
    assert condyle is not None and condyle.territory == 2
    assert gastrocnemius_head(peaks, labels, bone, condyle, back, -toward_left)[48, 24]
    # where no carried bone lies on the inner side, there is no inner condyle to stand behind
    outer_only = np.zeros(labels.shape, dtype=bool)
    outer_only[25, 12:38] = True
    assert inner_condyle(peaks, labels, outer_only, toward_left) is None


def test_neither_a_bones_region_nor_one_in_front_is_the_medial_gastrocnemius_head():
    labels, peaks = back_of_knee_scene()
    rows, cols = np.indices(labels.shape)
    back, toward_left = rows.astype(float), cols - 40.0
    bone = np.zeros(labels.shape, dtype=bool)
    bone[25, 12:68] = True
    condyle = inner_condyle(peaks, labels, bone, toward_left)
    assert condyle is not None
    # the front lies on the inner side of a notch at column 30, but in front of the condyle
    moved = cols - 30.0
    assert gastrocnemius_head(peaks, labels, bone, condyle, back, moved)[48, 56]
    assert not gastrocnemius_head(peaks, labels, bone, condyle, back, moved)[8, 40]
    # a region holding a carried bone place is the bone's, never the muscle
    bone[50, 60] = True
    assert not gastrocnemius_head(peaks, labels, bone, condyle, back, toward_left).any()


def test_gastrocnemius_code_names_why():
    assert gastrocnemius_code(False, "R", True, True, True, True, True) == (
        "abstain_leg_runs_in_the_plane"
    )
    assert gastrocnemius_code(True, "", True, True, True, True, True) == (
        "abstain_header_names_no_knee"
    )
    # without fat suppression the fat between the muscles is bright and draws no border
    assert gastrocnemius_code(True, "R", False, True, True, True, True) == (
        "abstain_not_parted_from_the_fat_without_fat_suppression"
    )
    assert gastrocnemius_code(True, "L", True, False, True, True, True) == (
        "abstain_no_bone_carried"
    )
    assert gastrocnemius_code(True, "R", True, True, False, True, True) == (
        "abstain_no_middle_sagittal_slice"
    )
    assert gastrocnemius_code(True, "R", True, True, True, False, True) == (
        "abstain_no_inner_condyle"
    )
    assert gastrocnemius_code(True, "R", True, True, True, True, False) == (
        "abstain_no_body_behind_the_inner_condyle"
    )
    assert gastrocnemius_code(True, "R", True, True, True, True, True) == "identified"


def test_the_tibias_top_is_the_highest_slice_below_the_femur_that_holds_the_tibia():
    # slices stored from the foot up: the femur on the top two, the tibia on all but the top
    femur, tibia = [False, False, False, True, True], [True, True, True, True, False]
    assert tibia_top_slice(femur, tibia, [0.0, 4.0, 8.0, 12.0, 16.0]) == 2
    # stored from the head down, the same leg: its order is read from the positions
    assert tibia_top_slice(femur[::-1], tibia[::-1], [16.0, 12.0, 8.0, 4.0, 0.0]) == 2
    # with no femur carried at all, the tibia's highest slice; with no tibia, none
    assert tibia_top_slice([False] * 3, [True] * 3, [0.0, 4.0, 8.0]) == 2
    assert tibia_top_slice([True, True], [False, False], [0.0, 4.0]) is None


def test_the_semimembranosus_is_the_front_tendon_at_the_condyles_back_inner_corner():
    # an axial slice at one place per millimetre, rows toward the back, columns toward the
    # patient's left, the notch at column 30: the tibia's inner condyle, its peak at (25, 50),
    # with its back corner reaching back on the inner side
    region = np.zeros((70, 90), dtype=bool)
    region[10:40, 10:70] = True
    region[40:51, 64:71] = True
    condyle = Peak(1, 15.0, (25, 50), 0.0)
    rows, cols = np.indices(region.shape)
    back, inner = rows.astype(float), cols - 30.0
    dark = np.zeros(region.shape, dtype=bool)
    dark[41:46, 55:60] = True  # the tendon, against the condyle's back, inside its peak
    dark[42, 56:59] = False  # the scanner's grain: a crack one pixel wide across it
    # a second body behind it, against the corner, 3 mm of fat between them
    dark[49:54, 59:64] = True
    # the PCL's end: inside the notch, outside the condyle's peak
    dark[41:46, 38:43] = True
    dark[43, 10:75] = True  # a fascia line, 1 mm thick
    free = np.ones(region.shape, dtype=bool)
    tendon = semimembranosus_on_slice(
        dark, free, region, condyle, back, inner, np.ones(2)
    )
    # the tendon whole, its crack too; not the body behind it, the PCL's end or the fascia line
    assert tendon[43, 57] and tendon[42, 57]
    assert not tendon[51, 61] and not tendon[43, 40] and not tendon[43, 30]
    # where nothing lies behind the condyle's peak, there is none
    behind_all = Peak(1, 15.0, (60, 50), 0.0)
    assert not semimembranosus_on_slice(
        dark, free, region, behind_all, back, inner, np.ones(2)
    ).any()


def test_semimembranosus_code_names_why():
    assert semimembranosus_code(False, "R", True, True, True, True, True) == (
        "abstain_leg_runs_in_the_plane"
    )
    assert semimembranosus_code(True, "", True, True, True, True, True) == (
        "abstain_header_names_no_knee"
    )
    assert semimembranosus_code(True, "L", False, True, True, True, True) == (
        "abstain_no_bone_carried"
    )
    assert semimembranosus_code(True, "R", True, False, True, True, True) == (
        "abstain_no_middle_sagittal_slice"
    )
    assert semimembranosus_code(True, "R", True, True, False, True, True) == (
        "abstain_no_tibia_below_the_femur"
    )
    assert semimembranosus_code(True, "R", True, True, True, False, True) == (
        "abstain_no_inner_condyle"
    )
    assert semimembranosus_code(True, "R", True, True, True, True, False) == (
        "abstain_no_tendon_at_the_back_inner_corner"
    )
    assert semimembranosus_code(True, "R", True, True, True, True, True) == "identified"


def test_lcl_code_names_why():
    assert lcl_code(False, True, True, True, False, True, True) == (
        "abstain_side_to_side_runs_through_the_plane"
    )
    assert lcl_code(True, False, True, True, False, True, True) == "abstain_no_fibula"
    assert lcl_code(True, True, False, True, False, True, True) == (
        "abstain_no_femur_and_tibia_to_carry"
    )
    assert lcl_code(True, True, True, False, False, True, True) == (
        "abstain_attachment_off_the_slices"
    )
    # with fat suppression the band and the fat under the skin fall in one region
    assert lcl_code(True, True, True, True, True, True, True) == (
        "abstain_not_parted_from_the_fat_with_fat_suppression"
    )
    assert lcl_code(True, True, True, True, False, False, True) == (
        "abstain_no_fibula_on_the_slice"
    )
    assert lcl_code(True, True, True, True, False, True, False) == (
        "abstain_no_region_joins_the_femur_and_the_fibula"
    )
    assert lcl_code(True, True, True, True, False, True, True) == "identified"


def fluid_scene() -> np.ndarray:
    """The fine coronal knee with fluid white, as with fat suppression on a fluid-sensitive
    sequence: a white pocket in the gutter against the femur's side, and a white vessel in the soft
    tissue, 8 mm from the tibia."""
    plane = fine_coronal_scene()
    plane[80:100, 58:64] = 500.0  # against the femur's shell, at column 64
    plane[200:206, 44:48] = 500.0  # a vessel, away from the bones and the joint
    return plane


def test_the_joint_fluid_is_the_white_in_the_joints_recesses():
    result = assigned(
        fluid_scene(), pixel_mm=FINE_MM, fat_suppressed=True, fluid_sensitive=True
    )
    assert result.codes["joint_fluid"] == "identified"
    assert result.objects[90, 60] == OBJECT_CODES["joint_fluid"]
    assert result.objects[203, 46] != OBJECT_CODES["joint_fluid"]  # the vessel


def test_without_fat_suppression_and_fluid_sensitivity_the_fluid_is_left_to_the_partner():
    for fat, fluid in ((False, True), (True, False), (False, False)):
        result = assigned(
            fluid_scene(), pixel_mm=FINE_MM, fat_suppressed=fat, fluid_sensitive=fluid
        )
        assert (
            result.codes["joint_fluid"] == "abstain_fluid_not_bright_on_this_sequence"
        )
        assert not (result.objects == OBJECT_CODES["joint_fluid"]).any()


def patella_territory_scene() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """A sagittal slice at one place per millimetre, rows running down: the patella's territory (3)
    holds fat above the patella (rows 0-9), the patella (rows 10-18) and fat below it (rows
    19-29), with the joint's fluid already named in the fat below; another territory (4) lies
    beside it all along."""
    labels = np.zeros((30, 20), dtype=np.int32)
    labels[0:30, 0:10] = 3
    labels[0:30, 10:20] = 4
    patella = np.zeros(labels.shape, dtype=bool)
    patella[10:19, 0:10] = True
    objects = np.zeros(labels.shape, dtype=np.int8)
    objects[patella] = OBJECT_CODES["patella"]
    objects[25:30, 0:3] = OBJECT_CODES["joint_fluid"]  # a part already named
    return labels, patella, objects


def test_hoffas_fat_pad_is_the_rest_of_the_patellas_territory_below_it():
    labels, patella, objects = patella_territory_scene()
    pad = rest_of_the_patellas_territory(labels, 3, patella, objects, SAGITTAL_MM)
    assert pad[22, 5] and pad[29, 9]
    assert not pad[14, 5]  # the patella
    assert not pad[5, 5]  # above it
    assert not pad[27, 1]  # the fluid already named
    assert not pad[25, 15]  # another territory
    assert not rest_of_the_patellas_territory(
        labels, 3, np.zeros_like(patella), objects, SAGITTAL_MM
    ).any()


def test_the_suprapatellar_fat_is_the_rest_of_the_patellas_territory_above_it():
    labels, patella, objects = patella_territory_scene()
    fat = rest_of_the_patellas_territory(
        labels, 3, patella, objects, SAGITTAL_MM, upward=True
    )
    assert fat[0, 0] and fat[9, 9]
    assert not fat[14, 5]  # the patella
    assert not fat[22, 5]  # below it
    assert not fat[5, 15]  # another territory


def test_the_fat_beside_the_patella_is_named_only_with_fat_suppression_on_a_sagittal_slice():
    plain = assigned(sagittal_scene(), SAGITTAL)
    coronal = assigned(scene(), CORONAL, fat_suppressed=True)
    for name in ("hoffa_fat_pad", "suprapatellar_fat"):
        assert plain.codes[name] == "abstain_fat_as_bright_as_marrow"
        assert coronal.codes[name] == "abstain_front_to_back_runs_through_the_plane"
        for result in (plain, coronal):
            assert not (result.objects == OBJECT_CODES[name]).any()


def test_fat_pad_code_names_why():
    assert fat_pad_code(False, True, True, True) == (
        "abstain_front_to_back_runs_through_the_plane"
    )
    assert fat_pad_code(True, False, True, True) == "abstain_fat_as_bright_as_marrow"
    assert fat_pad_code(True, True, False, True) == "abstain_no_patella"
    assert fat_pad_code(True, True, True, False) == "abstain_nothing_below_the_patella"
    assert fat_pad_code(True, True, True, False, above=True) == (
        "abstain_nothing_above_the_patella"
    )
    assert fat_pad_code(True, True, True, True) == "identified"
    assert fat_pad_code(True, True, True, True, above=True) == "identified"


def test_fluid_code_names_why():
    assert fluid_code(False, True, True) == "abstain_fluid_not_bright_on_this_sequence"
    assert fluid_code(True, False, True) == "abstain_no_femur_and_tibia"
    assert fluid_code(True, True, False) == "abstain_no_bright_fluid_in_the_recesses"
    assert fluid_code(True, True, True) == "identified"


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
