"""Exact Numba twin for the SciPy local-lightness measurement."""

from functools import lru_cache

import numpy as np


def _local_lightness_kernel(values, gone, window_rows, window_cols):
    rows, cols = values.shape
    smooth = np.full((rows, cols), np.nan, dtype=np.float64)
    surround = np.full((rows, cols), np.nan, dtype=np.float64)

    for row in range(rows):
        for col in range(cols):
            if gone[row, col]:
                continue
            samples = np.empty(9, dtype=np.float64)
            count = 0
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    rr, cc = row + dr, col + dc
                    if (
                        rr >= 0
                        and rr < rows
                        and cc >= 0
                        and cc < cols
                        and not gone[rr, cc]
                    ):
                        samples[count] = values[rr, cc]
                        count += 1
            if count:
                upper = count // 2
                partitioned = np.partition(samples[:count], upper)
                total = 0.0
                if count % 2:
                    total += partitioned[upper]
                else:
                    total += np.max(partitioned[:upper])
                    total += partitioned[upper]
                smooth[row, col] = total / (2.0 if count % 2 == 0 else 1.0)

    half_rows, half_cols = window_rows // 2, window_cols // 2
    max_samples = window_rows * window_cols
    for row in range(rows):
        for col in range(cols):
            samples = np.empty(max_samples, dtype=np.float64)
            count = 0
            row_start = max(0, row - half_rows)
            row_stop = min(rows, row + half_rows + 1)
            col_start = max(0, col - half_cols)
            col_stop = min(cols, col + half_cols + 1)
            for rr in range(row_start, row_stop):
                for cc in range(col_start, col_stop):
                    value = smooth[rr, cc]
                    if np.isfinite(value):
                        samples[count] = value
                        count += 1
            if count:
                upper = count // 2
                partitioned = np.partition(samples[:count], upper)
                total = 0.0
                if count % 2:
                    total += partitioned[upper]
                else:
                    total += np.max(partitioned[:upper])
                    total += partitioned[upper]
                surround[row, col] = total / (2.0 if count % 2 == 0 else 1.0)

    lightness = np.full((rows, cols), np.nan, dtype=np.float64)
    for row in range(rows):
        for col in range(cols):
            denominator = surround[row, col]
            if denominator > 0.0:
                lightness[row, col] = smooth[row, col] / denominator
    return lightness, smooth, surround


@lru_cache(maxsize=1)
def jit_local_lightness_kernel():
    """Return the exact, lazily compiled twin; Numba is required for this backend."""
    try:
        from numba import njit
    except ImportError as error:
        raise RuntimeError("required_backend_unavailable:jit") from error
    return njit(cache=True, nogil=True, fastmath=False)(_local_lightness_kernel)


def local_lightness_jit(
    plane: np.ndarray,
    excluded: np.ndarray,
    window_shape: tuple[int, int],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Measure local lightness using float64 values and the requested odd physical window.

    The caller supplies the window already computed from the existing physical-spacing rule.
    Input validation and the meaning of the excluded mask stay with that caller.
    """
    values = np.asarray(plane, dtype=np.float64)
    gone = np.asarray(excluded, dtype=bool) | ~np.isfinite(values)
    if values.ndim != 2 or gone.shape != values.shape:
        raise ValueError("lightness_inputs_must_share_a_2d_shape")
    window_rows, window_cols = (int(value) for value in window_shape)
    if (
        window_rows < 1
        or window_cols < 1
        or window_rows % 2 == 0
        or window_cols % 2 == 0
    ):
        raise ValueError("invalid_window_shape")
    return jit_local_lightness_kernel()(values, gone, window_rows, window_cols)
