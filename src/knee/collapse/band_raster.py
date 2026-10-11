"""Convex sample-band supercover; plain specification and strict JIT twin."""

from functools import lru_cache
from math import ceil, floor

import numpy as np

from knee.collapse.contracts import ComputeContract, contracted, handed_on


@contracted(
    ComputeContract(
        kind="convex_band_supercover",
        language="Python reference / Numba strict twin",
        reads="float64(P,4,2) native rc convex quads; bool(P); integer R,C",
        writes="bool(R,C) constraint mask, exact integer visited cell count",
        allocation="N bytes output; constant scalar scratch per pixel cell",
        work="clipped bounding cells per selected band; <=P*N visits; four SAT axes",
        parallel_unit="recipient (serial); JIT releases GIL",
        reference="raster_bands_reference",
        proof_gate="exact reference/JIT mask and visits, inclusive ties and clipping",
    )
)
def raster_bands_reference(quads, selected, rows, cols):
    out = np.zeros((rows, cols), dtype=np.bool_)
    visits = 0
    for p in range(len(quads)):
        if not selected[p]:
            continue
        q = quads[p]
        top = max(0, ceil(np.min(q[:, 0]) - 0.5))
        bottom = min(rows - 1, floor(np.max(q[:, 0]) + 0.5))
        left = max(0, ceil(np.min(q[:, 1]) - 0.5))
        right = min(cols - 1, floor(np.max(q[:, 1]) + 0.5))
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                visits += 1
                intersects = True
                for edge in range(4):
                    following = (edge + 1) % 4
                    nr = -(q[following, 1] - q[edge, 1])
                    nc = q[following, 0] - q[edge, 0]
                    low = float("inf")
                    high = -float("inf")
                    for corner in range(4):
                        v = nr * q[corner, 0] + nc * q[corner, 1]
                        low = min(low, v)
                        high = max(high, v)
                    center = nr * r + nc * c
                    radius = 0.5 * (abs(nr) + abs(nc))
                    if center + radius < low or center - radius > high:
                        intersects = False
                        break
                if intersects:
                    out[r, c] = True
    return out, visits


@lru_cache(maxsize=1)
def jit_band_kernel():
    try:
        from numba import njit
    except ImportError as error:
        raise RuntimeError("required_backend_unavailable:jit") from error
    return njit(cache=True, nogil=True, fastmath=False)(raster_bands_reference)


def raster_bands(quads, selected, shape, backend="reference"):
    """Mark intersecting pixel cells, including ties; do not extrapolate bands."""
    q = np.asarray(quads)
    if q.dtype != np.float64:
        raise ValueError("invalid_band_dtype")
    take = np.asarray(selected)
    if (
        len(shape) != 2
        or any(type(n) is not int or n < 0 for n in shape)
        or shape[0] * shape[1] > np.iinfo(np.int32).max
    ):
        raise ValueError("invalid_raster_shape")
    if q.ndim != 3 or q.shape[1:] != (4, 2) or not np.all(np.isfinite(q)):
        raise ValueError("invalid_band_quads")
    if take.shape != (len(q),) or take.dtype != np.bool_:
        raise ValueError("invalid_band_selection")
    edges = np.roll(q, -1, axis=1) - q
    following = np.roll(edges, -1, axis=1)
    cross = edges[:, :, 0] * following[:, :, 1] - edges[:, :, 1] * following[:, :, 0]
    if np.any(np.any(cross > 0, axis=1) & np.any(cross < 0, axis=1)):
        raise ValueError("nonconvex_band_quad")
    if len(q) * shape[0] * shape[1] > np.iinfo(np.int64).max:
        raise ValueError("raster_count_overflow")
    if backend not in ("reference", "jit"):
        raise ValueError("invalid_backend")
    kernel = raster_bands_reference if backend == "reference" else jit_band_kernel()
    mask, visits = kernel(q, take, shape[0], shape[1])
    return handed_on(mask), int(visits)
