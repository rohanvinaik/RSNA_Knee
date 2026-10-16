"""The popliteus cross-section occupies an LCL-region concavity in the femoral envelope."""

import numpy as np
import pytest

from knee.objects.assignments import convex_envelope, popliteus_in_notch


def test_convex_envelope_rasterizes_the_pixel_centre_hull():
    femur = np.zeros((9, 11), dtype=bool)
    femur[2:7, 3:8] = True

    envelope, vertices, equations, code = convex_envelope(femur)

    expected = np.zeros_like(femur)
    expected[2:7, 3:8] = True
    assert code == "measured"
    assert np.array_equal(envelope, expected)
    assert len(vertices) == 4
    assert equations.shape == (4, 3)


@pytest.mark.parametrize(
    "points, expected_code",
    [
        ((), "abstain_fewer_than_three_points"),
        (((2, 2),), "abstain_fewer_than_three_points"),
        (((2, 2), (2, 4)), "abstain_fewer_than_three_points"),
        (((2, 2), (2, 4), (2, 6)), "abstain_no_area"),
    ],
)
def test_convex_envelope_abstains_on_empty_or_degenerate_masks(points, expected_code):
    mask = np.zeros((8, 9), dtype=bool)
    for row, col in points:
        mask[row, col] = True

    envelope, vertices, equations, code = convex_envelope(mask)

    assert code == expected_code
    assert not envelope.any()
    assert vertices.shape == (0, 2)
    assert equations.shape == (0, 3)


def test_convex_envelope_rejects_non_2d_input():
    with pytest.raises(ValueError, match="2-D"):
        convex_envelope(np.zeros((2, 3, 4), dtype=bool))


def test_missing_femur_or_lcl_returns_named_empty_masks():
    femur = np.zeros((10, 12), dtype=bool)
    lcl = np.zeros_like(femur)
    output, readings, code = popliteus_in_notch(femur, lcl)
    assert code == "abstain_no_femoral_region"
    assert output.dtype == np.dtype(bool) and not output.any()
    assert not readings["envelope"].any()

    femur[2:8, 2:8] = True
    output, readings, code = popliteus_in_notch(femur, lcl)
    assert code == "abstain_no_lcl_region"
    assert output.shape == femur.shape and not output.any()


def test_convex_femur_has_no_lcl_component_in_its_envelope_exterior():
    femur = np.zeros((12, 14), dtype=bool)
    femur[2:10, 3:11] = True
    lcl = np.zeros_like(femur)
    lcl[4:7, 11:13] = True

    output, readings, code = popliteus_in_notch(femur, lcl)

    assert code == "abstain_no_lateral_femoral_notch"
    assert not output.any()
    assert readings["convex_envelope_code"] == "measured"
    assert not readings["candidate"].any()


def concave_scene():
    femur = np.zeros((12, 14), dtype=bool)
    femur[2:10, 2:12] = True
    femur[2:8, 5:9] = False
    lcl = np.zeros_like(femur)
    lcl[2:4, 5:8] = True
    lcl[5, 5] = True
    lcl[0:2, 5:8] = True  # outside the convex envelope
    return femur, lcl


def test_largest_lcl_component_in_the_femoral_concavity_is_selected():
    femur, lcl = concave_scene()
    expected = np.zeros_like(femur)
    expected[2:4, 5:8] = True

    output, readings, code = popliteus_in_notch(femur, lcl)

    assert code == "identified"
    assert np.array_equal(output, expected)
    assert readings["candidate"].sum() == 7
    assert readings["candidate_labels"].max() == 2
    assert np.array_equal(readings["selected_component"], expected)
    assert readings["vertices"].shape[1] == 2
    assert readings["equations"].shape[1] == 3
    assert all(isinstance(value, np.ndarray) for value in readings.values())
    assert all(value.dtype != np.dtype(object) for value in readings.values())


@pytest.mark.parametrize("axes", [(0,), (1,), (0, 1)])
def test_reflection_preserves_the_selected_patient_space_component(axes):
    femur, lcl = concave_scene()
    expected, _, _ = popliteus_in_notch(femur, lcl)

    output, _, code = popliteus_in_notch(
        np.flip(femur, axis=axes), np.flip(lcl, axis=axes)
    )

    assert code == "identified"
    assert np.array_equal(output, np.flip(expected, axis=axes))


def test_transpose_preserves_the_selected_component():
    femur, lcl = concave_scene()
    expected, _, _ = popliteus_in_notch(femur, lcl)

    output, _, code = popliteus_in_notch(femur.T, lcl.T)

    assert code == "identified"
    assert np.array_equal(output, expected.T)


def test_mask_shapes_must_match():
    with pytest.raises(ValueError, match="same shape"):
        popliteus_in_notch(np.zeros((3, 4)), np.zeros((4, 3)))
