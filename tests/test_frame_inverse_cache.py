"""EP2: a frame's basis pseudoinverse is made once per study scope for the exact basis contents."""

import numpy as np
import pytest

from knee.collapse.physical import PlaneFrame
from knee.telemetry.once import computing

_REAL_PINV = np.linalg.pinv

OBLIQUE = np.array([[0.5, 0.8], [1.2, -0.3], [0.7, 0.4]])
ANISOTROPIC = np.array([[0.0, 2.5], [0.7, 0.0], [0.0, 0.1]])
ORIGIN = np.array([10.0, -4.0, 2.5])
POINTS_A = np.array([[1.0, 2.0, 3.0], [-4.0, 5.5, 0.25], [9.0, -2.0, 7.0]])
POINTS_B = np.array([[3.0, 3.0, 3.0], [0.5, -1.5, 8.0]])


def reference(points, origin, basis):
    return (points - origin) @ _REAL_PINV(basis).T


def frame(basis=OBLIQUE, origin=ORIGIN):
    return PlaneFrame(origin.copy(), basis.copy(), (1.0, 1.0))


@pytest.fixture
def calls(monkeypatch):
    made = []

    def counting(*args, **kwargs):
        result = _REAL_PINV(*args, **kwargs)
        made.append(result)
        return result

    monkeypatch.setattr(np.linalg, "pinv", counting)
    return made


def test_same_basis_computes_once_in_scope(calls):
    with computing():
        first, second = frame(), frame()
        first.to_native(POINTS_A)
        first.to_native(POINTS_B)
        second.to_native(POINTS_A)
    assert len(calls) == 1


def test_different_basis_computes_again(calls):
    with computing():
        frame(OBLIQUE).to_native(POINTS_A)
        frame(ANISOTROPIC).to_native(POINTS_A)
    assert len(calls) == 2


def test_new_scope_computes_again(calls):
    with computing():
        frame().to_native(POINTS_A)
    with computing():
        frame().to_native(POINTS_A)
    assert len(calls) == 2


def test_outside_scope_each_call_computes(calls):
    f = frame()
    f.to_native(POINTS_A)
    f.to_native(POINTS_A)
    assert len(calls) == 2


def test_basis_mutation_forms_new_key(calls):
    f = frame()
    with computing():
        f.to_native(POINTS_A)
        f.basis_lps[0, 0] += 0.5
        out = f.to_native(POINTS_A)
    assert len(calls) == 2
    assert np.array_equal(out, reference(POINTS_A, f.origin_lps, f.basis_lps))
    assert f.basis_lps.flags.writeable


def test_origin_mutation_changes_output_without_recompute(calls):
    f = frame()
    with computing():
        before = f.to_native(POINTS_A)
        f.origin_lps[...] += 3.0
        after = f.to_native(POINTS_A)
    assert len(calls) == 1
    assert not np.array_equal(before, after)
    assert np.array_equal(after, reference(POINTS_A, f.origin_lps, f.basis_lps))
    assert f.origin_lps.flags.writeable and f.basis_lps.flags.writeable


@pytest.mark.parametrize("basis", [OBLIQUE, ANISOTROPIC])
def test_matches_reference_with_distinct_point_batches(calls, basis):
    f = frame(basis)
    with computing():
        out_a = f.to_native(POINTS_A)
        out_b = f.to_native(POINTS_B)
    assert np.array_equal(out_a, reference(POINTS_A, ORIGIN, basis))
    assert np.array_equal(out_b, reference(POINTS_B, ORIGIN, basis))
    assert out_a.shape != out_b.shape


@pytest.mark.parametrize(
    "bad",
    [
        np.zeros(3),
        np.zeros((2, 2)),
        np.array([[0.0, np.nan, 1.0]]),
        np.array([[0.0, np.inf, 1.0]]),
    ],
)
def test_invalid_points_rejected_before_pinv(calls, bad):
    with computing(), pytest.raises(ValueError, match="invalid_patient_points"):
        frame().to_native(bad)
    assert calls == []


def test_stored_inverse_is_handed_on_readonly(calls):
    with computing():
        frame().to_native(POINTS_A)
    assert len(calls) == 1
    assert not calls[0].flags.writeable


def test_from_dicom_arrays_stay_readonly_and_output_unchanged(calls):
    f = PlaneFrame.from_dicom(
        [1.0, 2.0, 3.0], [1.0, 0.0, 0.0, 0.0, 1.0, 0.0], (0.5, 2.0)
    )
    with computing():
        out = f.to_native(POINTS_A)
    assert not f.origin_lps.flags.writeable
    assert not f.basis_lps.flags.writeable
    assert np.array_equal(out, reference(POINTS_A, f.origin_lps, f.basis_lps))
    assert not out.flags.writeable
