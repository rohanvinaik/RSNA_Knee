"""Intent tests for relative signal and a ridge split of named suprapatellar fat."""

import numpy as np
import pytest

from knee.objects.assignments import relative_signal, suprapatellar_pads


def _basis_rows_superior():
    return np.array([[0.0, 0.0], [0.0, 1.0], [1.0, 0.0]])


def _paired_scene():
    fs_line = np.array([1.0, 2.0, 12.0, 2.0, 6.0, 2.0, 1.0, 2.0, 1.0])
    other_line = np.array([1.0, 2.0, 12.0, 2.0, 1.0, 2.0, 1.0, 2.0, 1.0])
    fs = np.tile(fs_line, (5, 1))
    other = np.tile(other_line, (5, 1))
    combined = np.ones(fs.shape, dtype=bool)
    back_mm = np.tile(np.arange(fs.shape[1], dtype=float), (fs.shape[0], 1))
    return fs, other, combined, back_mm


def _assert_empty_triplet(result, shape, code):
    anterior, posterior, ridge, actual = result
    assert actual == code
    assert anterior.shape == posterior.shape == ridge.shape == shape
    assert not anterior.any() and not posterior.any() and not ridge.any()


def test_relative_signal_handles_zero_negative_and_nonfinite_samples():
    numerator = np.array([[4.0, 1.0, -1.0, np.nan, np.inf]])
    denominator = np.array([[2.0, 0.0, 1.0, 2.0, 3.0]])

    ratio = relative_signal(numerator, denominator)

    assert ratio[0, 0] == 2.0
    assert np.isnan(ratio[0, 1:]).all()
    with pytest.raises(ValueError):
        relative_signal(numerator, np.ones((1, 4)))
    with pytest.raises(ValueError):
        relative_signal(numerator.ravel(), denominator)


def test_paired_relative_signal_selects_internal_seam_over_raw_bright_edge_and_scales():
    fs, other, combined, back_mm = _paired_scene()
    ratio = relative_signal(fs, other)
    assert np.argmax(fs[0]) == 2
    assert np.nanargmax(ratio[0]) == 4

    masks = suprapatellar_pads(ratio, combined, _basis_rows_superior(), back_mm)
    scaled = suprapatellar_pads(
        relative_signal(7.0 * fs, other), combined, _basis_rows_superior(), back_mm
    )
    anterior, posterior, ridge, code = masks

    assert code == "identified"
    assert ridge[:, 4].all() and ridge.sum() == combined.shape[0]
    assert anterior[:, :4].all() and not anterior[:, 4:].any()
    assert posterior[:, 5:].all() and not posterior[:, :5].any()
    assert np.array_equal(anterior, scaled[0])
    assert np.array_equal(posterior, scaled[1])
    assert np.array_equal(ridge, scaled[2])


def test_empty_uniform_and_unavailable_inputs_abstain_with_empty_masks():
    _, _, combined, back_mm = _paired_scene()
    basis = _basis_rows_superior()
    shape = combined.shape

    _assert_empty_triplet(
        suprapatellar_pads(np.ones(shape), np.zeros(shape, dtype=bool), basis, back_mm),
        shape,
        "abstain_no_suprapatellar_fat",
    )
    _assert_empty_triplet(
        suprapatellar_pads(np.ones(shape), combined, basis, back_mm),
        shape,
        "abstain_no_internal_seam",
    )
    _assert_empty_triplet(
        suprapatellar_pads(np.full(shape, np.nan), combined, basis, back_mm),
        shape,
        "abstain_no_internal_seam",
    )


def test_ridge_accepts_contiguous_ties_and_rejects_separated_equal_maxima():
    _, _, combined, back_mm = _paired_scene()
    basis = _basis_rows_superior()
    contiguous = np.zeros(combined.shape, dtype=float)
    contiguous[:, 3:5] = 8.0

    anterior, posterior, ridge, code = suprapatellar_pads(
        contiguous, combined, basis, back_mm
    )
    assert code == "identified"
    assert ridge[:, 3:5].all() and ridge.sum() == 2 * combined.shape[0]
    assert not anterior[:, 3:5].any() and not posterior[:, 3:5].any()

    separated = np.zeros(combined.shape, dtype=float)
    separated[:, 2] = 8.0
    separated[:, 5] = 8.0
    _assert_empty_triplet(
        suprapatellar_pads(separated, combined, basis, back_mm),
        combined.shape,
        "abstain_no_internal_seam",
    )


def test_superior_axis_transpose_and_reversal_preserve_physical_partition():
    fs, other, combined, back_mm = _paired_scene()
    ratio = relative_signal(fs, other)
    basis = _basis_rows_superior()
    original = suprapatellar_pads(ratio, combined, basis, back_mm)

    transposed_basis = np.column_stack((basis[:, 1], -basis[:, 0]))
    transposed = suprapatellar_pads(ratio.T, combined.T, transposed_basis, back_mm.T)
    assert transposed[3] == "identified"
    for expected, actual in zip(original[:3], transposed[:3], strict=True):
        assert np.array_equal(actual, expected.T)

    reversed_back = suprapatellar_pads(ratio, combined, basis, -back_mm)
    assert reversed_back[3] == "identified"
    assert np.array_equal(reversed_back[2], original[2])
    assert np.array_equal(reversed_back[0], original[1])
    assert np.array_equal(reversed_back[1], original[0])
