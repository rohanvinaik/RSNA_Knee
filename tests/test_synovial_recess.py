"""The anterior recess is located by named anatomy; its lining is a cavity-side surface."""

import numpy as np
import pytest

from knee.objects.assignments import (
    OBJECT_CODES,
    anterior_synovial_recess,
    synovium_code,
)

SAGITTAL = np.array([[0.0, 0.0], [0.0, 1.0], [-1.0, 0.0]])


def recess_scene():
    """Rows run inferior, columns posterior, at one place per millimetre."""
    objects = np.zeros((30, 36), dtype=np.int8)
    objects[12:18, 5:9] = OBJECT_CODES["patella"]
    objects[:24, 24:30] = OBJECT_CODES["femur"]
    recess = np.zeros(objects.shape, dtype=bool)
    recess[3:14, 13:19] = True
    # The whole connected body is retained, including its end below the pocket.
    recess[14:23, 17:19] = True
    white = recess.copy()
    white[3:7, 10:12] = True  # a smaller body in the anterior pocket
    white[:25, 31:] = True  # a larger bright body behind the femur
    white[25:29, 12:20] = True  # below the patella's lower end
    return white, objects, recess


def test_largest_body_intersecting_the_anterior_pocket_is_retained_whole():
    white, objects, expected = recess_scene()
    recess, lining = anterior_synovial_recess(white, objects, SAGITTAL)
    assert np.array_equal(recess, expected)
    assert recess[22, 18]  # below the pocket, still part of the same fluid body
    assert not recess[4, 10]  # the smaller eligible body
    assert not recess[4, 33]  # the larger posterior distractor
    assert not recess[27, 15]  # a separate body below the anatomical pocket
    assert lining.any()


def test_lining_is_the_anterior_cavity_boundary_and_has_no_membrane_thickness():
    white, objects, _ = recess_scene()
    recess, lining = anterior_synovial_recess(white, objects, SAGITTAL)
    assert np.all(~lining | recess)
    assert lining[7, 13]  # the anterior boundary, sampled inside the cavity
    assert not lining[7, 12]  # adjacent tissue outside the cavity
    assert not lining[7, 14]  # interior fluid, rather than its boundary
    assert not lining[7, 18]  # the posterior boundary
    _, cols = np.indices(recess.shape)
    assert np.all(cols[lining] < np.median(cols[recess]))


@pytest.mark.parametrize("missing", ["all", "patella", "femur", "white"])
def test_absent_anatomy_or_white_returns_two_empty_masks(missing):
    white, objects, _ = recess_scene()
    if missing == "all":
        objects[:] = 0
        white[:] = False
    elif missing == "white":
        white[:] = False
    else:
        objects[objects == OBJECT_CODES[missing]] = 0
    recess, lining = anterior_synovial_recess(white, objects, SAGITTAL)
    assert recess.shape == lining.shape == objects.shape
    assert recess.dtype == lining.dtype == np.dtype(bool)
    assert not recess.any() and not lining.any()


@pytest.mark.parametrize("name", ["femur", "tibia", "patella", "pcl", "acl"])
def test_white_intersecting_only_an_excluded_named_part_is_not_a_recess(name):
    _, objects, _ = recess_scene()
    white = np.zeros(objects.shape, dtype=bool)
    white[8, 15] = True
    objects[8, 15] = OBJECT_CODES[name]
    recess, lining = anterior_synovial_recess(white, objects, SAGITTAL)
    assert not recess.any() and not lining.any()


def test_diagonally_connected_white_is_one_whole_body():
    _, objects, _ = recess_scene()
    white = np.zeros(objects.shape, dtype=bool)
    white[7:10, 14:17] = True
    white[10:13, 17:20] = True  # joins the first block only at a corner
    recess, _ = anterior_synovial_recess(white, objects, SAGITTAL)
    assert np.array_equal(recess, white)


def test_white_outside_every_anterior_pocket_intersection_returns_empty():
    _, objects, _ = recess_scene()
    white = np.zeros(objects.shape, dtype=bool)
    white[:25, 31:] = True
    white[25:29, 12:20] = True
    white[1:8, :3] = True  # in front of the patella
    recess, lining = anterior_synovial_recess(white, objects, SAGITTAL)
    assert not recess.any() and not lining.any()


@pytest.mark.parametrize("axes", [(0,), (1,), (0, 1)])
def test_reversing_array_axes_preserves_the_same_patient_space_result(axes):
    white, objects, _ = recess_scene()
    recess, lining = anterior_synovial_recess(white, objects, SAGITTAL)
    basis = SAGITTAL.copy()
    for axis in axes:
        basis[:, axis] *= -1
    reversed_recess, reversed_lining = anterior_synovial_recess(
        np.flip(white, axis=axes), np.flip(objects, axis=axes), basis
    )
    assert np.array_equal(reversed_recess, np.flip(recess, axis=axes))
    assert np.array_equal(reversed_lining, np.flip(lining, axis=axes))


def test_exchanging_rows_and_columns_preserves_the_patient_space_result():
    white, objects, _ = recess_scene()
    recess, lining = anterior_synovial_recess(white, objects, SAGITTAL)
    transposed_recess, transposed_lining = anterior_synovial_recess(
        white.T, objects.T, SAGITTAL[:, ::-1]
    )
    assert np.array_equal(transposed_recess, recess.T)
    assert np.array_equal(transposed_lining, lining.T)


def test_inputs_are_unchanged():
    white, objects, _ = recess_scene()
    basis = SAGITTAL.copy()
    originals = [value.copy() for value in (white, objects, basis)]
    white.flags.writeable = objects.flags.writeable = basis.flags.writeable = False
    anterior_synovial_recess(white, objects, basis)
    for actual, original in zip((white, objects, basis), originals, strict=True):
        assert np.array_equal(actual, original)


@pytest.mark.parametrize(
    "conditions, expected",
    [
        ((False, True, True, True, True), "abstain_not_a_sagittal_slice"),
        ((True, False, True, True, True), "abstain_fluid_not_bright_on_this_sequence"),
        ((True, True, False, True, True), "abstain_no_patella"),
        ((True, True, True, False, True), "abstain_no_femur"),
        ((True, True, True, True, False), "abstain_no_fluid_in_the_anterior_recess"),
        ((True, True, True, True, True), "identified"),
        ((False, False, False, False, False), "abstain_not_a_sagittal_slice"),
        (
            (True, False, False, False, False),
            "abstain_fluid_not_bright_on_this_sequence",
        ),
        ((True, True, False, False, False), "abstain_no_patella"),
        ((True, True, True, False, False), "abstain_no_femur"),
    ],
)
def test_synovium_decisions_name_each_missing_requirement_and_its_precedence(
    conditions, expected
):
    assert synovium_code(*conditions) == expected
