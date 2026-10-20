"""Bounded native patellofemoral cartilage surface reading."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import ConvexHull

from knee.objects.assignments import CARTILAGE_BRIGHTER, CARTILAGE_MM, FLUID_BRIGHTER

Distance = Callable[[np.ndarray, tuple[float, float] | np.ndarray], np.ndarray]


def _blank_arrays(
    shape: tuple[int, int],
    available: np.ndarray | None,
    finite: np.ndarray | None,
    patella: np.ndarray | None,
    femur: np.ndarray | None,
) -> dict[str, np.ndarray]:
    zeros = np.zeros(shape, dtype=bool)
    distances = np.full(shape, np.inf, dtype=np.float64)
    return {
        "bridge": zeros.copy(),
        "bridge_hull": zeros.copy(),
        "patella": zeros.copy()
        if patella is None or patella.shape != shape
        else patella.copy(),
        "femur": zeros.copy()
        if femur is None or femur.shape != shape
        else femur.copy(),
        "overlap": zeros.copy(),
        "patella_filled": zeros.copy(),
        "femur_filled": zeros.copy(),
        "brightness_band": zeros.copy(),
        "to_patella_mm": distances.copy(),
        "to_femur_mm": distances.copy(),
        "patella_reach": zeros.copy(),
        "femur_reach": zeros.copy(),
        "eligible": zeros.copy(),
        "patella_support": zeros.copy(),
        "trochlear_support": zeros.copy(),
        "ties": zeros.copy(),
        "available": zeros.copy()
        if available is None or available.shape != shape
        else available.copy(),
        "finite": zeros.copy()
        if finite is None or finite.shape != shape
        else finite.copy(),
    }


def _convex_hull_mask(points_rc: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    """Rasterize the convex hull at pixel centers, including point and segment hulls."""
    points = np.unique(np.asarray(points_rc, dtype=np.float64).reshape(-1, 2), axis=0)
    hull = np.zeros(shape, dtype=bool)
    if not len(points):
        return hull
    if len(points) == 1:
        row, col = points[0].astype(np.int64)
        hull[row, col] = True
        return hull
    centered = points - points[0]
    if np.linalg.matrix_rank(centered) < 2:
        direction = points[-1] - points[0]
        norm_sq = float(np.dot(direction, direction))
        # Exact zero denotes a point segment; short nonzero segments retain their extent.
        if norm_sq == 0.0:  # NOSONAR(S1244)
            row, col = points[0].astype(np.int64)
            hull[row, col] = True
            return hull
        r0 = max(0, int(np.floor(points[:, 0].min())))
        r1 = min(shape[0], int(np.ceil(points[:, 0].max())) + 1)
        c0 = max(0, int(np.floor(points[:, 1].min())))
        c1 = min(shape[1], int(np.ceil(points[:, 1].max())) + 1)
        rr, cc = np.mgrid[r0:r1, c0:c1]
        candidates = np.column_stack((rr.ravel(), cc.ravel())).astype(np.float64)
        relative = candidates - points[0]
        cross = relative[:, 0] * direction[1] - relative[:, 1] * direction[0]
        along = relative @ direction
        on_segment = (
            (np.abs(cross) <= 1e-9) & (along >= -1e-9) & (along <= norm_sq + 1e-9)
        )
        hull[rr.ravel()[on_segment], cc.ravel()[on_segment]] = True
        return hull

    geometry = ConvexHull(points)
    r0 = max(0, int(np.floor(points[:, 0].min())))
    r1 = min(shape[0], int(np.ceil(points[:, 0].max())) + 1)
    c0 = max(0, int(np.floor(points[:, 1].min())))
    c1 = min(shape[1], int(np.ceil(points[:, 1].max())) + 1)
    rr, cc = np.mgrid[r0:r1, c0:c1]
    candidates = np.column_stack((rr.ravel(), cc.ravel())).astype(np.float64)
    inside = np.all(
        candidates @ geometry.equations[:, :2].T + geometry.equations[:, 2] <= 1e-9,
        axis=1,
    )
    hull[rr.ravel()[inside], cc.ravel()[inside]] = True
    return hull


def patellofemoral_surface_reading(
    raw: np.ndarray,
    available: np.ndarray,
    patella: np.ndarray,
    femur: np.ndarray,
    spacing_rc: tuple[float, float] | np.ndarray,
    reference_light: float,
    *,
    distance: Distance | None = None,
) -> dict[str, Any]:
    """Measure a bounded native surface reading between supplied patella and femur supports.

    The convex bridge is a broad geometric prior: it includes recesses, tendon-insertion regions,
    and any femoral concavity inside the input crop. It is not a cartilage or capsule boundary.
    The brightness and reach relations are the existing cartilage measurements; the 4x upper bound
    comes from `femoral_cartilage_on_plane`, while `cartilage_on` supplies the tibiofemoral lower
    brightness and reach comparison. The reference light is supplied by the caller from original
    native bone support and is never recomputed from hole-filled masks. Returned masks stay in the
    input crop's coordinates; the caller owns the crop address.

    `patella_support` and `trochlear_support` are native readings only. A 3 mm reach truncates
    some patellar cartilage and nearest-bone attribution splits the contact layer approximately.
    Equal-distance eligible pixels remain in `ties` rather than being assigned to either support.
    """
    try:
        plane = np.asarray(raw)
    except (TypeError, ValueError):
        plane = np.empty((0, 0), dtype=np.float64)
    shape = tuple(plane.shape) if plane.ndim == 2 else (0, 0)
    finite = (
        np.isfinite(plane) if plane.ndim == 2 and plane.dtype.kind in "iuf" else None
    )
    valid_input = np.asarray(available) if available is not None else None
    patella_input = np.asarray(patella) if patella is not None else None
    femur_input = np.asarray(femur) if femur is not None else None
    result_arrays = _blank_arrays(
        shape, valid_input, finite, patella_input, femur_input
    )
    result: dict[str, Any] = {
        "status": "unmeasured",
        "reason": None,
        "reference_light": None,
        "brightness_lower": None,
        "brightness_upper": None,
        "reach_mm": float(CARTILAGE_MM),
        "threshold_provenance": "FLUID_BRIGHTER upper bound in femoral_cartilage_on_plane",
        "shape_rc": list(shape),
    }
    result.update(result_arrays)

    if plane.ndim != 2 or plane.size == 0 or plane.dtype.kind not in "iuf":
        result["reason"] = "invalid_raw_plane"
        return result
    if (
        valid_input is None
        or valid_input.shape != shape
        or valid_input.dtype.kind != "b"
    ):
        result["reason"] = "invalid_available_mask"
        return result
    if patella_input is None:
        result["reason"] = "missing_patella_support"
        return result
    if patella_input.shape != shape or patella_input.dtype.kind != "b":
        result["reason"] = "invalid_patella_support"
        return result
    if femur_input is None:
        result["reason"] = "missing_femur_support"
        return result
    if femur_input.shape != shape or femur_input.dtype.kind != "b":
        result["reason"] = "invalid_femur_support"
        return result
    if not patella_input.any():
        result["reason"] = "missing_patella_support"
        return result
    if not femur_input.any():
        result["reason"] = "missing_femur_support"
        return result
    try:
        raw_spacing = np.asarray(spacing_rc)
        if raw_spacing.dtype.kind == "b":
            raise ValueError("boolean_spacing")
        spacing = np.asarray(raw_spacing, dtype=np.float64)
    except (TypeError, ValueError, OverflowError):
        result["reason"] = "invalid_spacing"
        return result
    if (
        spacing.shape != (2,)
        or not np.isfinite(spacing).all()
        or np.any(spacing <= 0.0)
    ):
        result["reason"] = "invalid_spacing"
        return result
    try:
        if isinstance(reference_light, (bool, np.bool_)):
            raise TypeError("boolean_reference_light")
        light = float(reference_light)
    except (TypeError, ValueError, OverflowError):
        result["reason"] = "invalid_reference_light"
        return result
    if not np.isfinite(light) or light <= 0.0:
        result["reason"] = "invalid_reference_light"
        return result

    arrays = result
    arrays["available"] = valid_input.copy()
    arrays["finite"] = finite.copy()
    arrays["patella"] = patella_input.copy()
    arrays["femur"] = femur_input.copy()
    arrays["overlap"] = patella_input & femur_input
    arrays["patella_filled"] = ndi.binary_fill_holes(patella_input)
    arrays["femur_filled"] = ndi.binary_fill_holes(femur_input)
    arrays["bridge_hull"] = _convex_hull_mask(
        np.argwhere(patella_input | femur_input), shape
    )
    arrays["bridge"] = arrays["bridge_hull"] & ~(
        arrays["patella_filled"] | arrays["femur_filled"]
    )
    usable = valid_input & finite
    arrays["brightness_band"] = (
        finite
        & (plane > CARTILAGE_BRIGHTER * light)
        & (plane <= FLUID_BRIGHTER * light)
    )
    if not usable.any():
        result.update(status="unmeasured", reason="no_available_finite_pixels")
        result["reference_light"] = light
        result["brightness_lower"] = float(CARTILAGE_BRIGHTER * light)
        result["brightness_upper"] = float(FLUID_BRIGHTER * light)
        return result

    def read_distance(target: np.ndarray) -> np.ndarray | None:
        try:
            values = (
                ndi.distance_transform_edt(~target, sampling=spacing)
                if distance is None
                else np.asarray(distance(target, spacing))
            )
        except (TypeError, ValueError, OverflowError, FloatingPointError):
            return None
        if values.shape != shape or values.dtype.kind not in "iuf":
            return None
        values = np.asarray(values, dtype=np.float64)
        if not np.isfinite(values).all() or np.any(values < 0.0):
            return None
        return values

    to_patella = read_distance(patella_input)
    to_femur = read_distance(femur_input)
    if to_patella is None or to_femur is None:
        result.update(status="unmeasured", reason="native_distance_unavailable")
        result["reference_light"] = light
        result["brightness_lower"] = float(CARTILAGE_BRIGHTER * light)
        result["brightness_upper"] = float(FLUID_BRIGHTER * light)
        if to_patella is not None:
            arrays["to_patella_mm"] = to_patella
        if to_femur is not None:
            arrays["to_femur_mm"] = to_femur
        return result

    arrays["to_patella_mm"] = to_patella
    arrays["to_femur_mm"] = to_femur
    arrays["patella_reach"] = to_patella <= CARTILAGE_MM
    arrays["femur_reach"] = to_femur <= CARTILAGE_MM
    arrays["eligible"] = (
        arrays["bridge"]
        & usable
        & arrays["brightness_band"]
        & (arrays["patella_reach"] | arrays["femur_reach"])
    )
    arrays["ties"] = arrays["eligible"] & (to_patella == to_femur)
    arrays["patella_support"] = (
        arrays["eligible"] & arrays["patella_reach"] & (to_patella < to_femur)
    )
    arrays["trochlear_support"] = (
        arrays["eligible"] & arrays["femur_reach"] & (to_femur < to_patella)
    )
    result.update(
        status="measured" if arrays["eligible"].any() else "measured_empty",
        reason=None if arrays["eligible"].any() else "no_eligible_bridge_pixels",
        reference_light=light,
        brightness_lower=float(CARTILAGE_BRIGHTER * light),
        brightness_upper=float(FLUID_BRIGHTER * light),
        spacing_rc=spacing.tolist(),
    )
    return result
