"""A bursal fluid body is located between a tendon and a broad posterior field."""

import numpy as np
import pytest

from knee.objects.assignments import bursa_code, bursa_on_slice


def bursa_scene():
    """Rows run posterior and columns inward, with one pixel per millimetre."""
    shape = (60, 70)
    rows, cols = np.indices(shape)
    back, inner = rows.astype(float), cols.astype(float) - 30.0
    tendon = np.zeros(shape, dtype=bool)
    tendon[10:13, 38:41] = True
    field = np.zeros(shape, dtype=bool)
    field[30:48, 33:49] = True
    white = np.zeros(shape, dtype=bool)
    white[20:29, 38:44] = True
    white[20:22, 44:53] = True  # retain the connected body's side extension too
    return white, tendon, field, back, inner, np.ones(2)


def test_bursal_body_is_kept_whole_without_a_white_neck_reaching_the_tendon():
    white, tendon, field, back, inner, spacing = bursa_scene()
    found = bursa_on_slice(white, tendon, field, back, inner, spacing)
    assert np.array_equal(found, white)
    assert found[20, 52]  # the whole connected extension is retained
    assert not (found & tendon).any()
    assert not found[13:20].any()  # the narrow neck need not be white
    assert not (found & field).any()  # the broad field is a reach target


@pytest.mark.parametrize("where", ["anterior", "posterior", "outer", "away_field"])
def test_a_larger_body_outside_the_bursal_place_does_not_replace_the_bursa(where):
    white, tendon, field, back, inner, spacing = bursa_scene()
    expected = white.copy()
    distractor = np.zeros(white.shape, dtype=bool)
    if where == "anterior":
        distractor[1:9, 35:46] = True
        field[:31, 33:35] = True  # this distractor reaches the broad target
    elif where == "posterior":
        distractor[49:59, 35:46] = True  # reaches the back of the broad target
    elif where == "outer":
        distractor[20:29, 10:22] = True
        field[30:48, 10:33] = True  # in reach, but not on the inner side
    else:
        distractor[18:29, 56:69] = True  # correct axes, beyond the reach allowance
    assert distractor.sum() > expected.sum()
    white |= distractor
    found = bursa_on_slice(white, tendon, field, back, inner, spacing)
    assert np.array_equal(found, expected)


def test_the_largest_of_two_eligible_white_bodies_is_selected():
    white, tendon, field, back, inner, spacing = bursa_scene()
    expected = white.copy()
    white[18:21, 33:36] = True
    field[20:31, 32:34] = True  # the smaller component also reaches the field
    found = bursa_on_slice(white, tendon, field, back, inner, spacing)
    assert np.array_equal(found, expected)
    assert not found[18, 34]


@pytest.mark.parametrize("missing", ["tendon", "field", "white", "all"])
def test_missing_anatomical_target_or_white_returns_an_empty_mask(missing):
    white, tendon, field, back, inner, spacing = bursa_scene()
    if missing in ("white", "all"):
        white[:] = False
    if missing in ("tendon", "all"):
        tendon[:] = False
    if missing in ("field", "all"):
        field[:] = False
    found = bursa_on_slice(white, tendon, field, back, inner, spacing)
    assert found.shape == white.shape and found.dtype == np.dtype(bool)
    assert not found.any()


@pytest.mark.parametrize("boundary", ["tendon_middle", "field_middle", "inner_zero"])
def test_equality_at_an_anatomical_boundary_is_excluded(boundary):
    white, tendon, field, back, inner, spacing = bursa_scene()
    white[:] = False
    if boundary == "tendon_middle":
        white[11, 36:41] = True  # exactly the tendon's posterior median
        field[11:31, 35] = True  # eligible reach does not override the strict boundary
        assert np.median(back[white]) == np.median(back[tendon])
    elif boundary == "field_middle":
        field[:] = False
        field[30:47, 33:49] = True
        white[38, 31:33] = True  # exactly the posterior field's median
        assert np.median(back[white]) == np.median(back[field])
    else:
        white[22:29, 30] = True
        field[30:48, 31:49] = True
        assert np.median(inner[white]) == 0.0
    found = bursa_on_slice(white, tendon, field, back, inner, spacing)
    assert not found.any()


def test_physical_spacing_controls_reach_to_the_broad_posterior_field():
    white, tendon, field, back, inner, _ = bursa_scene()
    # The body's last row is two pixel steps from the field's first row.
    assert np.array_equal(
        bursa_on_slice(white, tendon, field, back, inner, np.array([1.0, 1.0])),
        white,
    )
    assert not bursa_on_slice(
        white, tendon, field, back, inner, np.array([1.1, 1.0])
    ).any()


@pytest.mark.parametrize("axes", [(0,), (1,), (0, 1)])
def test_reversed_image_axes_preserve_the_same_patient_geometry(axes):
    white, tendon, field, back, inner, spacing = bursa_scene()
    found = bursa_on_slice(
        np.flip(white, axis=axes),
        np.flip(tendon, axis=axes),
        np.flip(field, axis=axes),
        np.flip(back, axis=axes),
        np.flip(inner, axis=axes),
        spacing,
    )
    assert np.array_equal(found, np.flip(white, axis=axes))


def test_transposed_image_axes_preserve_the_same_patient_geometry():
    white, tendon, field, back, inner, spacing = bursa_scene()
    found = bursa_on_slice(white.T, tendon.T, field.T, back.T, inner.T, spacing[::-1])
    assert np.array_equal(found, white.T)


def test_readonly_inputs_are_unchanged():
    inputs = bursa_scene()
    originals = [value.copy() for value in inputs]
    for value in inputs:
        value.flags.writeable = False
    bursa_on_slice(*inputs)
    for actual, original in zip(inputs, originals, strict=True):
        assert np.array_equal(actual, original)


@pytest.mark.parametrize(
    "conditions, expected",
    [
        ((False, True, True, True), "abstain_fluid_not_bright_on_this_sequence"),
        ((True, False, True, True), "abstain_no_semimembranosus_tendon"),
        ((True, True, False, True), "abstain_no_region_behind_the_inner_condyle"),
        ((True, True, True, False), "abstain_no_fluid_body_in_the_bursal_place"),
        ((True, True, True, True), "identified"),
        ((False, False, False, False), "abstain_fluid_not_bright_on_this_sequence"),
        ((True, False, False, False), "abstain_no_semimembranosus_tendon"),
        ((True, True, False, False), "abstain_no_region_behind_the_inner_condyle"),
    ],
)
def test_bursa_codes_name_each_missing_requirement_and_its_precedence(
    conditions, expected
):
    assert bursa_code(*conditions) == expected
