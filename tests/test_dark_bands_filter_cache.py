from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from knee.objects import assignments
from knee.objects.assignments import OBJECT_CODES, Measures, dark_bands
from knee.telemetry import computing


def _legacy_uniform(plane: np.ndarray, size: tuple[int, ...]) -> np.ndarray:
    return ndi.median_filter(np.asarray(plane, dtype=np.float64), size=size)


def test_uniform_filter_is_shared_for_same_slice_inputs_and_frozen(monkeypatch) -> None:
    plane = np.arange(81, dtype=np.float32).reshape(9, 9)
    first = Measures(("series", 4), plane, np.eye(3))
    second = Measures(("series", 4), plane.copy(), np.eye(3))
    calls = 0
    original = assignments.ndi.median_filter

    def counted(values, *args, **kwargs):
        nonlocal calls
        calls += 1
        return original(values, *args, **kwargs)

    monkeypatch.setattr(assignments.ndi, "median_filter", counted)
    with computing():
        one = first.median_filter(plane, (3, 3))
        two = second.median_filter(plane.copy(), (3, 3))
    assert calls == 1
    assert one is two
    assert not one.flags.writeable
    np.testing.assert_array_equal(one, _legacy_uniform(plane, (3, 3)))


def test_explicit_plane_size_shape_and_dtype_are_part_of_filter_key(
    monkeypatch,
) -> None:
    owner = np.arange(100, dtype=np.float32).reshape(10, 10)
    other = np.flipud(owner).copy()
    measures = Measures(("series", 2), owner, np.eye(3))
    calls = 0
    original = assignments.ndi.median_filter

    def counted(values, *args, **kwargs):
        nonlocal calls
        calls += 1
        return original(values, *args, **kwargs)

    monkeypatch.setattr(assignments.ndi, "median_filter", counted)
    with computing():
        a = measures.median_filter(other, (3, 3))
        b = measures.median_filter(other, (5, 3))
        c = measures.median_filter(other.reshape(5, 20), (3, 3))
        d = measures.median_filter(other.astype(np.float64), (3, 3))
        again = measures.median_filter(other, (3, 3))
    assert calls == 4
    assert a is again
    np.testing.assert_array_equal(a, _legacy_uniform(other, (3, 3)))
    np.testing.assert_array_equal(b, _legacy_uniform(other, (5, 3)))
    np.testing.assert_array_equal(c, _legacy_uniform(other.reshape(5, 20), (3, 3)))
    np.testing.assert_array_equal(d, _legacy_uniform(other.astype(np.float64), (3, 3)))


def test_without_study_key_filter_is_computed_for_each_request(monkeypatch) -> None:
    plane = np.arange(49, dtype=np.float64).reshape(7, 7)
    measures = Measures(None, plane, np.eye(3))
    calls = 0
    original = assignments.ndi.median_filter

    def counted(values, *args, **kwargs):
        nonlocal calls
        calls += 1
        return original(values, *args, **kwargs)

    monkeypatch.setattr(assignments.ndi, "median_filter", counted)
    first = measures.median_filter(plane, (3, 3))
    second = measures.median_filter(plane, (3, 3))
    assert calls == 2
    assert first is not second
    assert not first.flags.writeable
    assert not second.flags.writeable


def test_dark_bands_keeps_exact_labels_and_uses_explicit_plane() -> None:
    plane = np.full((31, 31), 20.0, dtype=np.float32)
    plane[15, :] = 0.0
    objects = np.zeros(plane.shape, dtype=np.int16)
    objects[5:11, 5:11] = OBJECT_CODES["femur"]
    objects[20:25, 20:25] = OBJECT_CODES["tibia"]
    outside = np.zeros(plane.shape, dtype=bool)
    spacing = np.array([1.0, 1.0])
    wrong_measures_plane = np.full(plane.shape, 900.0)
    measures = Measures(("series", 0), wrong_measures_plane, np.eye(3))
    # The pre-existing Measures.light semantics use its owned plane; only the shared
    # uniform filter must honor dark_bands' explicit plane argument.
    expected_light = np.median(wrong_measures_plane[objects == OBJECT_CODES["femur"]])
    size = tuple(
        int(2 * round(assignments.LIGAMENT_SMOOTH_MM / step) + 1) for step in spacing
    )
    uniform = _legacy_uniform(plane, size)
    dark = (
        (uniform < assignments.LIGAMENT_DARKER * expected_light)
        & ~outside
        & (objects != OBJECT_CODES["femur"])
        & (objects != OBJECT_CODES["tibia"])
    )
    expected, _ = ndi.label(
        assignments.thick_parts(dark, spacing, assignments.LIGAMENT_THICK_MM)
    )
    expected = np.asarray(expected, dtype=np.int32)
    with computing():
        actual = dark_bands(plane, objects, spacing, outside, measures)
    np.testing.assert_array_equal(actual, expected)
    assert actual.dtype == np.int32


def test_dark_bands_standalone_path_matches_old_filter_for_nonfinite_border_and_empty() -> (
    None
):
    plane = np.arange(81, dtype=np.float64).reshape(9, 9)
    plane[0, 0] = np.nan
    objects = np.zeros(plane.shape, dtype=np.int16)
    objects[2:4, 2:4] = OBJECT_CODES["femur"]
    objects[5:7, 5:7] = OBJECT_CODES["tibia"]
    outside = np.zeros(plane.shape, dtype=bool)
    spacing = np.array([1.0, 1.0])
    size = tuple(
        int(2 * round(assignments.LIGAMENT_SMOOTH_MM / step) + 1) for step in spacing
    )
    light = assignments.marrow_light(plane, objects == OBJECT_CODES["femur"])
    uniform = _legacy_uniform(plane, size)
    dark = (
        (uniform < assignments.LIGAMENT_DARKER * light)
        & ~outside
        & (objects != OBJECT_CODES["femur"])
        & (objects != OBJECT_CODES["tibia"])
    )
    expected, _ = ndi.label(
        assignments.thick_parts(dark, spacing, assignments.LIGAMENT_THICK_MM)
    )
    np.testing.assert_array_equal(
        dark_bands(plane, objects, spacing, outside),
        np.asarray(expected, dtype=np.int32),
    )
    empty = np.zeros_like(objects)
    assert not dark_bands(plane, empty, spacing, outside).any()
