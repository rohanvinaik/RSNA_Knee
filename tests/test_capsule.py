"""The capsule wall is dark tissue outward of eligible femoral side recesses."""

import numpy as np
import pytest

from knee.objects.assignments import (
    OBJECT_CODES,
    capsule_at_side_recesses,
    capsule_code,
)

CORONAL = np.array([[0.0, 1.0], [0.0, 0.0], [-1.0, 0.0]])
SPACING = np.ones(2)


def capsule_scene():
    """A femur, two menisci, and separate fluid bodies at one pixel per millimetre."""
    objects = np.zeros((40, 50), dtype=np.int8)
    objects[2:25, 16:34] = OBJECT_CODES["femur"]
    objects[25:28, 14:19] = OBJECT_CODES["lateral_meniscus"]
    objects[25:28, 31:36] = OBJECT_CODES["medial_meniscus"]
    white = np.zeros(objects.shape, dtype=bool)
    white[7:18, 13:16] = True
    white[7:18, 34:37] = True
    dark = np.zeros(objects.shape, dtype=bool)
    expected = np.zeros(objects.shape, dtype=bool)
    expected[7:18, 11:13] = True
    expected[7:18, 37:39] = True
    dark |= expected
    dark[7:18, 16] = True  # inner cortex beside the left recess
    dark[7:18, 33] = True  # inner cortex beside the right recess
    dark[7:18, 22] = True  # central/notch tissue
    white[7:18, 23:27] = True  # central bright body, not a side recess
    dark[6, 11:13] = True  # just above the left recess's height
    dark[18, 37:39] = True  # just below the right recess's height
    return dark, white, objects, expected


def test_only_the_dark_outer_walls_of_both_side_recesses_are_selected():
    dark, white, objects, expected = capsule_scene()
    found = capsule_at_side_recesses(dark, white, objects, CORONAL, SPACING)
    assert np.array_equal(found["capsule"], expected)
    expected_lining = np.zeros(objects.shape, dtype=bool)
    expected_lining[7:18, 13] = True
    expected_lining[7:18, 36] = True
    assert np.array_equal(found["lining"], expected_lining)
    expected_negative_wall = np.zeros(objects.shape, dtype=bool)
    expected_negative_wall[7:18, 11:13] = True
    expected_positive_wall = np.zeros(objects.shape, dtype=bool)
    expected_positive_wall[7:18, 37:39] = True
    assert np.array_equal(found["negative_wall"], expected_negative_wall)
    assert np.array_equal(found["positive_wall"], expected_positive_wall)
    assert int(found["section_axis"]) == 0
    assert np.all(found["negative_section_status"][7:18] == "selected")
    assert np.all(found["positive_section_status"][7:18] == "selected")
    assert not found["capsule"][:, 16].any() and not found["capsule"][:, 33].any()
    assert not found["capsule"][:, 22].any()
    assert not found["capsule"][6, 11] and not found["capsule"][18, 37]


def test_each_side_uses_its_largest_eligible_white_body():
    dark, white, objects, expected = capsule_scene()
    white[20:23, 13:16] = True  # a smaller but eligible left recess
    white[20:23, 34:37] = True  # a smaller but eligible right recess
    dark[20:23, 11:13] = True
    dark[20:23, 37:39] = True
    found = capsule_at_side_recesses(dark, white, objects, CORONAL, SPACING)
    assert np.array_equal(found["capsule"], expected)
    assert not found["capsule"][20:23].any()


def test_one_wall_straddling_the_fluid_edge_is_ambiguous_without_losing_other_rows():
    dark, white, objects, _ = capsule_scene()
    dark[10, 36] = (
        True  # wall reaches the positive-side fluid's outermost position on one row
    )
    found = capsule_at_side_recesses(dark, white, objects, CORONAL, SPACING)
    assert found["positive_section_status"][10] == "ambiguous_wall"
    assert np.all(found["positive_section_status"][7:10] == "selected")
    assert np.all(found["positive_section_status"][11:18] == "selected")
    assert not found["positive_lining"][10].any()
    expected_negative_edge = np.zeros((11, 50), dtype=bool)
    expected_negative_edge[:, 13] = True
    assert np.array_equal(found["negative_lining"][7:18], expected_negative_edge)
    assert np.array_equal(
        found["capsule"], found["negative_wall"] | found["positive_wall"]
    )


def test_both_selected_fluid_bodies_are_retained_when_both_walls_are_absent():
    dark, white, objects, _ = capsule_scene()
    dark[:] = False
    found = capsule_at_side_recesses(dark, white, objects, CORONAL, SPACING)
    assert found["negative_recess"].sum() == 33
    assert found["positive_recess"].sum() == 33
    assert not found["capsule"].any()
    assert not found["lining"].any()
    assert np.all(found["negative_section_status"][7:18] == "no_wall")
    assert np.all(found["positive_section_status"][7:18] == "no_wall")


def test_larger_bodies_below_the_joint_or_far_from_the_femur_are_excluded():
    dark, white, objects, expected = capsule_scene()
    # Extend the femur so the lower body reaches it: height must exclude this body.
    objects[28:38, 16:34] = OBJECT_CODES["femur"]
    white[29:38, 11:16] = True
    dark[29:38, 9:11] = True
    # A separate body is above the joint and outboard, but too far from the femur.
    white[2:24, 4:9] = True
    dark[2:24, 2:4] = True
    found = capsule_at_side_recesses(dark, white, objects, CORONAL, SPACING)
    assert np.array_equal(found["capsule"], expected)
    assert not found["capsule"][29:].any() and not found["capsule"][:, :4].any()


@pytest.mark.parametrize(
    "missing", ["femur", "medial_meniscus", "lateral_meniscus", "white", "dark", "all"]
)
def test_missing_anatomy_or_measured_signal_returns_an_empty_mask(missing):
    dark, white, objects, _ = capsule_scene()
    if missing == "all":
        dark[:] = white[:] = False
        objects[:] = 0
    elif missing == "white":
        white[:] = False
    elif missing == "dark":
        dark[:] = False
    else:
        objects[objects == OBJECT_CODES[missing]] = 0
    found = capsule_at_side_recesses(dark, white, objects, CORONAL, SPACING)
    assert found["capsule"].shape == objects.shape
    assert found["capsule"].dtype == np.dtype(bool)
    assert not found["capsule"].any()
    assert not found["lining"].any()
    if missing == "dark":
        assert np.all(
            np.isin(found["negative_section_status"], ["no_fluid", "no_wall"])
        )
        assert np.all(
            np.isin(found["positive_section_status"], ["no_fluid", "no_wall"])
        )
        assert np.any(found["negative_section_status"] == "no_wall")
        assert np.any(found["positive_section_status"] == "no_wall")
    else:
        assert np.all(found["negative_section_status"] == "no_fluid")
        assert np.all(found["positive_section_status"] == "no_fluid")


@pytest.mark.parametrize("axes", [(0,), (1,), (0, 1)])
def test_axis_reversals_preserve_the_same_patient_space_wall(axes):
    dark, white, objects, expected = capsule_scene()
    basis = CORONAL.copy()
    for axis in axes:
        basis[:, axis] *= -1
    found = capsule_at_side_recesses(
        np.flip(dark, axis=axes),
        np.flip(white, axis=axes),
        np.flip(objects, axis=axes),
        basis,
        SPACING,
    )
    assert np.array_equal(found["capsule"], np.flip(expected, axis=axes))
    expected_edge = np.zeros(objects.shape, dtype=bool)
    expected_edge[7:18, 13] = True
    expected_edge[7:18, 36] = True
    assert np.array_equal(found["lining"], np.flip(expected_edge, axis=axes))


def test_transposing_rows_and_columns_preserves_the_patient_space_wall():
    dark, white, objects, expected = capsule_scene()
    found = capsule_at_side_recesses(
        dark.T, white.T, objects.T, CORONAL[:, ::-1], SPACING[::-1]
    )
    assert np.array_equal(found["capsule"], expected.T)
    expected_edge = np.zeros(objects.shape, dtype=bool)
    expected_edge[7:18, 13] = True
    expected_edge[7:18, 36] = True
    assert int(found["section_axis"]) == 1
    assert np.array_equal(found["lining"], expected_edge.T)


def test_contact_allowance_is_in_millimetres_for_the_outer_wall():
    dark, white, objects, _ = capsule_scene()
    basis = CORONAL.copy()
    basis[:, 1] *= 1.5
    found = capsule_at_side_recesses(dark, white, objects, basis, np.array([1.0, 1.5]))
    expected = np.zeros(objects.shape, dtype=bool)
    expected[7:18, 12] = True
    expected[7:18, 37] = True
    assert np.array_equal(found["capsule"], expected)


def test_a_recess_beyond_the_physical_femur_contact_allowance_is_excluded():
    dark, white, objects, _ = capsule_scene()
    basis = CORONAL.copy()
    basis[:, 1] *= 2.5
    found = capsule_at_side_recesses(dark, white, objects, basis, np.array([1.0, 2.5]))
    assert not found["capsule"].any()


def test_readonly_input_arrays_are_unchanged():
    dark, white, objects, _ = capsule_scene()
    basis, spacing = CORONAL.copy(), SPACING.copy()
    inputs = (dark, white, objects, basis, spacing)
    originals = [value.copy() for value in inputs]
    for value in inputs:
        value.flags.writeable = False
    capsule_at_side_recesses(*inputs)
    for actual, original in zip(inputs, originals, strict=True):
        assert np.array_equal(actual, original)


@pytest.mark.parametrize(
    "conditions, expected",
    [
        ((False, True, True, True, True), "abstain_not_a_coronal_slice"),
        ((True, False, True, True, True), "abstain_fluid_not_bright_on_this_sequence"),
        ((True, True, False, True, True), "abstain_no_femur"),
        (
            (True, True, True, False, True),
            "abstain_no_two_menisci_to_locate_the_side_recesses",
        ),
        ((True, True, True, True, False), "abstain_no_dark_outer_wall_at_the_recesses"),
        ((True, True, True, True, True), "identified"),
        ((False, False, False, False, False), "abstain_not_a_coronal_slice"),
        (
            (True, False, False, False, False),
            "abstain_fluid_not_bright_on_this_sequence",
        ),
        ((True, True, False, False, False), "abstain_no_femur"),
        (
            (True, True, True, False, False),
            "abstain_no_two_menisci_to_locate_the_side_recesses",
        ),
    ],
)
def test_capsule_decisions_name_each_requirement_and_its_precedence(
    conditions, expected
):
    assert capsule_code(*conditions) == expected
