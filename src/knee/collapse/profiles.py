"""Native signal profiles with a plain reference and strict, required JIT twin."""

from dataclasses import dataclass
from functools import lru_cache
from math import floor, isfinite

import numpy as np

from knee.collapse.contracts import ComputeContract, contracted, handed_on
from knee.collapse.physical import numeric_plane, spacing_pair
from knee.collapse.profile_codes import profile_support_code


@contracted(
    ComputeContract(
        kind="measurement",
        language="Python reference / Numba strict twin",
        reads="plane: original dtype (R,C); points,normals: float64(P,2); offsets: float64(S); spacing mm",
        writes="samples float64(P,S), valid bool(P,S)",
        allocation="9*P*S bytes output; constant scalar scratch",
        work="P*S coordinate evaluations, at most 4*P*S positive-weight source reads",
        parallel_unit="independent profile; serial ordered reference/twin initially",
        reference="profile_samples_reference",
        proof_gate="exact SAME including support, signed zero, NaN, dtype, shape",
    )
)
def profile_samples_reference(plane, points, normals, offsets, spacing):
    samples = np.full((len(points), len(offsets)), np.nan, dtype=np.float64)
    valid = np.zeros(samples.shape, dtype=np.bool_)
    for p in range(len(points)):
        for s in range(len(offsets)):
            row = points[p, 0] + offsets[s] * normals[p, 0] / spacing[0]
            col = points[p, 1] + offsets[s] * normals[p, 1] / spacing[1]
            if (
                row < 0
                or col < 0
                or row > plane.shape[0] - 1
                or col > plane.shape[1] - 1
            ):
                continue
            r0, c0 = floor(row), floor(col)
            dr, dc = row - r0, col - c0
            total = 0.0
            supported = True
            for ri in range(2):
                for ci in range(2):
                    weight = (dr if ri else 1.0 - dr) * (dc if ci else 1.0 - dc)
                    if weight > 0:
                        value = float(plane[r0 + ri, c0 + ci])
                        if not isfinite(value):
                            supported = False
                        total += weight * value
            if supported:
                samples[p, s] = total
                valid[p, s] = True
    return samples, valid


@lru_cache(maxsize=1)
def jit_profile_kernel():
    try:
        from numba import njit
    except ImportError as error:
        raise RuntimeError("required_backend_unavailable:jit") from error
    return njit(cache=True, nogil=True, fastmath=False)(profile_samples_reference)


@dataclass(frozen=True, slots=True)
class ProfileReading:
    """Samples in stored intensity units; slopes intensity/mm. Missing entries retain NaN.

    Shapes: samples,valid (P,S), slopes (P,max(0,S-1)), distances_mm (S,).
    Per-profile counts/support codes are retained, alongside overall support.
    """

    samples: np.ndarray
    valid: np.ndarray
    slopes: np.ndarray
    distances_mm: np.ndarray
    support_code: str
    support_codes: tuple[str, ...]
    requested_backend: str
    effective_backend: str


def sample_profiles(
    plane: np.ndarray,
    points_rc: np.ndarray,
    normals_rc: np.ndarray,
    offsets_mm: np.ndarray,
    spacing_rc: tuple[float, float],
    backend: str = "reference",
    *,
    metric_rc: np.ndarray | None = None,
) -> ProfileReading:
    """Sample unit physical steps: n.T metric_rc n = 1.

    Default metric is identity. A retained DICOM direction basis A uses A.T @ A.
    Source strides are retained. JIT admits native-endian integers up to 64 bits
    and float32/float64; other numeric dtypes remain reference-only.
    """
    numeric_plane(plane)
    spacing = spacing_pair(spacing_rc)
    points = np.asarray(points_rc, dtype=np.float64)
    normals = np.asarray(normals_rc, dtype=np.float64)
    offsets = np.asarray(offsets_mm, dtype=np.float64)
    metric = np.eye(2) if metric_rc is None else np.asarray(metric_rc, dtype=np.float64)
    if (
        metric.shape != (2, 2)
        or not np.all(np.isfinite(metric))
        or not np.array_equal(metric, metric.T)
        or np.any(np.linalg.eigvalsh(metric) <= 0)
    ):
        raise ValueError("invalid_profile_metric")
    if points.ndim != 2 or points.shape[1] != 2 or not np.all(np.isfinite(points)):
        raise ValueError("invalid_profile_points")
    if normals.shape != points.shape or not np.all(np.isfinite(normals)):
        raise ValueError("invalid_profile_normals")
    lengths_squared = np.sum((normals @ metric) * normals, axis=1)
    if not np.allclose(lengths_squared, 1.0, rtol=0, atol=1e-12):
        raise ValueError("invalid_profile_normals")
    if (
        offsets.ndim != 1
        or not np.all(np.isfinite(offsets))
        or np.any(np.diff(offsets) <= 0)
    ):
        raise ValueError("invalid_profile_offsets")
    if backend not in ("reference", "jit"):
        raise ValueError("invalid_backend")
    if backend == "jit" and (
        not plane.dtype.isnative
        or (plane.dtype.kind == "f" and plane.dtype.itemsize not in (4, 8))
        or plane.dtype.itemsize > 8
    ):
        raise ValueError("unsupported_backend_dtype:jit")
    kernel = (
        profile_samples_reference if backend == "reference" else jit_profile_kernel()
    )
    samples, valid = kernel(plane, points, normals, offsets, spacing)
    slopes = np.full((len(points), max(0, len(offsets) - 1)), np.nan)
    if len(offsets) > 1:
        both = valid[:, 1:] & valid[:, :-1]
        np.divide(np.diff(samples, axis=1), np.diff(offsets), out=slopes, where=both)
    return ProfileReading(
        handed_on(samples),
        handed_on(valid),
        handed_on(slopes),
        handed_on(offsets.copy()),
        profile_support_code(int(valid.size), int(valid.sum())),
        tuple(profile_support_code(len(offsets), int(row.sum())) for row in valid),
        backend,
        backend,
    )
