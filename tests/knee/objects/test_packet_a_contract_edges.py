"""Packet A contract edges: metric geometry, supported storage layouts and requests."""

from __future__ import annotations

import builtins

import numpy as np
import pytest

from knee.objects.analysis import AnalysisRequest
from knee.objects.profiles import jit_profile_kernel, sample_profiles


def _metric_case():
    basis = np.array(
        [[0.0, 0.999999], [0.999999, 0.0], [0.0, 0.000001]], dtype=np.float64
    )
    metric = basis.T @ basis
    diagonal = np.array([1.0, 1.0])
    normal = diagonal / np.sqrt(diagonal @ metric @ diagonal)
    return metric, normal


def _compare_readings(reference, twin) -> None:
    for name in ("samples", "valid", "slopes", "distances_mm"):
        left, right = getattr(reference, name), getattr(twin, name)
        assert left.shape == right.shape
        assert left.dtype == right.dtype
        if left.dtype.kind == "f":
            np.testing.assert_array_equal(np.isnan(left), np.isnan(right))
            finite = ~np.isnan(left)
            np.testing.assert_array_equal(
                np.signbit(left[finite]), np.signbit(right[finite])
            )
            np.testing.assert_array_equal(left, right)
        else:
            np.testing.assert_array_equal(left, right)


def test_rounded_dicom_metric_gives_analytic_profile_step_and_same_twin() -> None:
    metric, normal = _metric_case()
    rows, columns = np.indices((11, 11), dtype=np.float64)
    plane = rows + 2.0 * columns
    spacing = (1.5, 0.75)
    offsets = np.array([-1.0, 0.0, 1.0])
    points = np.array([[5.0, 5.0]])
    normals = normal.reshape(1, 2)

    reference = sample_profiles(
        plane, points, normals, offsets, spacing, backend="reference", metric_rc=metric
    )
    jit = sample_profiles(
        plane, points, normals, offsets, spacing, backend="jit", metric_rc=metric
    )

    expected_slope = normal[0] / spacing[0] + 2.0 * normal[1] / spacing[1]
    np.testing.assert_allclose(
        np.diff(reference.samples, axis=1)[0], expected_slope, atol=1e-12
    )
    np.testing.assert_allclose(
        reference.slopes, [[expected_slope, expected_slope]], atol=1e-12
    )
    np.testing.assert_allclose(np.sqrt(normal @ metric @ normal), 1.0, atol=1e-12)
    _compare_readings(reference, jit)


@pytest.mark.parametrize(
    "metric",
    [
        np.eye(3),
        np.array([[1.0, 0.0], [0.0, np.nan]]),
        np.array([[1.0, 0.5], [0.0, 1.0]]),
        np.array([[1.0, 2.0], [2.0, 1.0]]),
        np.array([[1.0, 0.0], [0.0, 0.0]]),
    ],
)
def test_malformed_profile_metric_is_rejected(metric: np.ndarray) -> None:
    with pytest.raises(ValueError):
        sample_profiles(
            np.ones((3, 3)),
            np.array([[1.0, 1.0]]),
            np.array([[1.0, 0.0]]),
            np.array([0.0]),
            (1.0, 1.0),
            metric_rc=metric,
        )


@pytest.mark.parametrize(
    "dtype", [np.int16, np.uint16, np.uint64, np.float32, np.float64]
)
@pytest.mark.parametrize("layout", ["c", "f", "strided"])
def test_supported_plane_dtypes_and_strides_match_between_reference_and_jit(
    dtype, layout: str
) -> None:
    base = (np.arange(81, dtype=np.float64).reshape(9, 9) * 0.25).astype(dtype)
    if layout == "f":
        plane = np.asfortranarray(base)
    elif layout == "strided":
        storage = np.zeros((18, 18), dtype=dtype)
        storage[::2, ::2] = base
        plane = storage[::2, ::2]
    else:
        plane = np.ascontiguousarray(base)
    before = plane.copy()
    points = np.array([[4.0, 4.0], [3.0, 5.0]])
    normals = np.array([[1.0, 0.0], [0.0, 1.0]])
    offsets = np.array([-0.5, 0.0, 0.5])
    reference = sample_profiles(plane, points, normals, offsets, (1.0, 1.0))
    jit = sample_profiles(plane, points, normals, offsets, (1.0, 1.0), backend="jit")

    assert plane.dtype == np.dtype(dtype)
    np.testing.assert_array_equal(plane, before)
    _compare_readings(reference, jit)


def test_float16_is_supported_by_the_reference_path() -> None:
    plane = np.arange(9, dtype=np.float16).reshape(3, 3)
    result = sample_profiles(
        plane,
        np.array([[1.0, 1.0]]),
        np.array([[1.0, 0.0]]),
        np.array([0.0]),
        (1.0, 1.0),
        backend="reference",
    )
    assert result.valid[0, 0]
    assert result.samples[0, 0] == 4.0


@pytest.mark.parametrize(
    "plane",
    [
        np.ones((3, 3), dtype=np.float16),
        np.ones((3, 3), dtype=np.dtype(">f8")),
    ],
)
def test_jit_rejects_unsupported_float_storage_with_a_named_code(
    plane: np.ndarray,
) -> None:
    with pytest.raises(ValueError, match="^unsupported_backend_dtype:jit$"):
        sample_profiles(
            plane,
            np.array([[1.0, 1.0]]),
            np.array([[1.0, 0.0]]),
            np.array([0.0]),
            (1.0, 1.0),
            backend="jit",
        )


def test_jit_rejects_extended_float_when_the_platform_provides_one() -> None:
    if np.dtype(np.longdouble).itemsize <= np.dtype(np.float64).itemsize:
        pytest.skip("platform longdouble has no extended float representation")
    plane = np.ones((3, 3), dtype=np.longdouble)
    with pytest.raises(ValueError, match="^unsupported_backend_dtype:jit$"):
        sample_profiles(
            plane,
            np.array([[1.0, 1.0]]),
            np.array([[1.0, 0.0]]),
            np.array([0.0]),
            (1.0, 1.0),
            backend="jit",
        )


@pytest.mark.parametrize("backend", ["reference", "jit"])
def test_one_ulp_outside_points_are_missing_but_exact_edges_ignore_zero_weight_nan(
    backend: str,
) -> None:
    plane = np.array([[5.0, np.nan, 1.0], [np.inf, 2.0, 3.0], [4.0, 5.0, 6.0]])
    points = np.array(
        [
            [0.0, 0.0],
            [2.0, 2.0],
            [np.nextafter(0.0, -np.inf), 1.0],
            [np.nextafter(2.0, np.inf), 1.0],
        ]
    )
    result = sample_profiles(
        plane,
        points,
        np.array([[1.0, 0.0]] * 4),
        np.array([0.0]),
        (1.0, 1.0),
        backend=backend,
    )

    np.testing.assert_array_equal(result.valid[:, 0], [True, True, False, False])
    np.testing.assert_allclose(result.samples[:2, 0], [5.0, 6.0])
    assert np.isnan(result.samples[2:, 0]).all()


def test_jit_missing_dependency_is_reported_and_cache_is_restored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jit_profile_kernel.cache_clear()
    original_import = builtins.__import__

    def without_numba(name, *args, **kwargs):
        if name == "numba":
            raise ImportError("simulated missing numba")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_numba)
    try:
        with pytest.raises(RuntimeError, match="^required_backend_unavailable:jit$"):
            sample_profiles(
                np.ones((3, 3)),
                np.array([[1.0, 1.0]]),
                np.array([[1.0, 0.0]]),
                np.array([0.0]),
                (1.0, 1.0),
                backend="jit",
            )
    finally:
        jit_profile_kernel.cache_clear()


def test_analysis_request_validates_explicit_measurement_settings() -> None:
    valid = AnalysisRequest(2.0, (), (0.0, 0.0, 1.0), "reference")
    assert valid.offsets_mm == ()
    assert valid.slice_index is None
    assert AnalysisRequest(2.0, (0.0, 1.0), (0.0, 0.0, 1.0), "jit", 0).slice_index == 0


@pytest.mark.parametrize(
    "arguments",
    [
        (0.0, (0.0,), (0.0, 0.0, 1.0), "reference", None),
        (float("inf"), (0.0,), (0.0, 0.0, 1.0), "reference", None),
        (2.0, (1.0, 0.0), (0.0, 0.0, 1.0), "reference", None),
        (2.0, (0.0, float("nan")), (0.0, 0.0, 1.0), "reference", None),
        (2.0, (0.0,), (0.0, 0.0, 0.0), "reference", None),
        (2.0, (0.0,), (0.0, 0.0, float("nan")), "reference", None),
        (2.0, (0.0,), (0.0, 0.0, 2.0), "reference", None),
        (2.0, (0.0,), (0.0, 0.0, 1.0), "unknown", None),
        (2.0, (0.0,), (0.0, 0.0, 1.0), "reference", -1),
        (2.0, (0.0,), (0.0, 0.0, 1.0), "reference", 1.5),
    ],
)
def test_malformed_analysis_requests_are_rejected(arguments) -> None:
    with pytest.raises(ValueError):
        AnalysisRequest(*arguments)
