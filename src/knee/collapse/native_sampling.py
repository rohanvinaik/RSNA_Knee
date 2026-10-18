"""Sample source light at LPS points using the actual acquired pixel planes."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from math import isfinite
from numbers import Real

import numpy as np

from knee.collapse.physical import PlaneFrame


@dataclass(frozen=True, slots=True)
class NativePointSamples:
    """Per-point samples and the actual native-plane mappings used to obtain them."""

    points_lps: np.ndarray
    signal: np.ndarray
    selected_z: np.ndarray
    native_rc: np.ndarray
    signed_distance_mm: np.ndarray
    status: tuple[str, ...]


Reader = Callable[[int], tuple[np.ndarray, bool | np.bool_ | np.ndarray]]


def _positive_float(value: object) -> float | None:
    if not isinstance(value, Real) or isinstance(value, (bool, np.bool_)):
        return None
    numeric = float(value)
    return numeric if isfinite(numeric) and numeric > 0.0 else None


def _frame_geometry(
    frame: PlaneFrame,
) -> tuple[np.ndarray, np.ndarray] | None:
    try:
        origin = np.asarray(frame.origin_lps)
        basis = np.asarray(frame.basis_lps)
        spacing = frame.spacing_rc
    except (AttributeError, TypeError, ValueError):
        return None
    try:
        spacing_values = tuple(_positive_float(step) for step in spacing)
        valid_spacing = len(spacing_values) == 2 and all(
            step is not None for step in spacing_values
        )
    except TypeError:
        valid_spacing = False
    if (
        origin.shape != (3,)
        or basis.shape != (3, 2)
        or origin.dtype.kind not in "iuf"
        or basis.dtype.kind not in "iuf"
        or not np.all(np.isfinite(origin))
        or not np.all(np.isfinite(basis))
        or not valid_spacing
    ):
        return None
    normal = np.cross(basis[:, 0], basis[:, 1]).astype(np.float64, copy=False)
    length = float(np.linalg.norm(normal))
    if not np.isfinite(length) or length <= 0.0:
        return None
    return origin.astype(np.float64, copy=False), normal / length


def _invalid_result(points: np.ndarray, status: str) -> NativePointSamples:
    count = len(points)
    return NativePointSamples(
        points_lps=points.copy(),
        signal=np.full(count, np.nan, dtype=np.float64),
        selected_z=np.full(count, -1, dtype=np.int32),
        native_rc=np.full((count, 2), -1, dtype=np.int32),
        signed_distance_mm=np.full(count, np.nan, dtype=np.float64),
        status=(status,) * count,
    )


def sample_native_points(
    points_lps: np.ndarray,
    frames: Sequence[PlaneFrame],
    slice_thickness_mm: Sequence[float | None],
    source_shape_rc: tuple[int, int],
    read_plane: Reader,
) -> NativePointSamples:
    """Read finite source light at nearest acquired pixel centers for LPS points.

    Every source frame and thickness must be usable to establish the nearest plane.
    The callback's unavailable result may be a whole-plane boolean or a per-pixel
    boolean mask supplied by the existing reader. It is consumed here, never
    recomputed. Pixel-center coordinates are rounded with ``np.rint`` only after
    enforcing the physical pixel span ``[-0.5, size - 0.5)``.
    """
    try:
        raw_points = np.asarray(points_lps)
    except (TypeError, ValueError):
        return _invalid_result(np.empty((1, 3), dtype=np.float64), "invalid_point")
    if raw_points.ndim == 1:
        raw_points = raw_points[None, :]
    if raw_points.ndim != 2:
        return _invalid_result(np.empty((1, 3), dtype=np.float64), "invalid_point")
    count = raw_points.shape[0]
    if count == 0:
        return _invalid_result(np.empty((0, 3), dtype=np.float64), "invalid_point")
    if raw_points.shape[1] != 3 or raw_points.dtype.kind not in "iuf":
        return _invalid_result(np.full((count, 3), np.nan), "invalid_point")
    points = raw_points.astype(np.float64, copy=True)
    point_valid = np.all(np.isfinite(points), axis=1)
    statuses = np.full(count, "invalid_point", dtype=object)
    signal = np.full(count, np.nan, dtype=np.float64)
    selected_z = np.full(count, -1, dtype=np.int32)
    native_rc = np.full((count, 2), -1, dtype=np.int32)
    signed_distance = np.full(count, np.nan, dtype=np.float64)
    if not point_valid.any():
        return NativePointSamples(
            points, signal, selected_z, native_rc, signed_distance, tuple(statuses)
        )

    try:
        frame_count = len(frames)
        thickness_count = len(slice_thickness_mm)
        rows, columns = source_shape_rc
    except (TypeError, ValueError):
        statuses[point_valid] = "invalid_geometry"
        return NativePointSamples(
            points, signal, selected_z, native_rc, signed_distance, tuple(statuses)
        )
    if (
        frame_count == 0
        or thickness_count != frame_count
        or isinstance(rows, bool)
        or isinstance(columns, bool)
        or not isinstance(rows, (int, np.integer))
        or not isinstance(columns, (int, np.integer))
        or rows <= 0
        or columns <= 0
    ):
        statuses[point_valid] = "invalid_geometry"
        return NativePointSamples(
            points, signal, selected_z, native_rc, signed_distance, tuple(statuses)
        )

    geometries: list[tuple[np.ndarray, np.ndarray]] = []
    thicknesses: list[float] = []
    for frame, thickness in zip(frames, slice_thickness_mm, strict=True):
        geometry = _frame_geometry(frame)
        thickness_value = _positive_float(thickness)
        if geometry is None or thickness_value is None:
            statuses[point_valid] = "invalid_geometry"
            return NativePointSamples(
                points, signal, selected_z, native_rc, signed_distance, tuple(statuses)
            )
        geometries.append(geometry)
        thicknesses.append(thickness_value)

    valid_indices = np.flatnonzero(point_valid)
    nearest_abs = np.full(count, np.inf, dtype=np.float64)
    nearest_signed = np.full(count, np.nan, dtype=np.float64)
    nearest_z = np.full(count, -1, dtype=np.int32)
    bad_distance = np.zeros(count, dtype=bool)
    tie_tolerance = 8.0 * np.finfo(np.float64).eps
    for z, (origin, normal) in enumerate(geometries):
        with np.errstate(over="ignore", invalid="ignore"):
            distances = (points[valid_indices] - origin) @ normal
        finite = np.isfinite(distances)
        bad_distance[valid_indices[~finite]] = True
        candidates = valid_indices[finite]
        absolute = np.abs(distances[finite])
        replace = absolute < nearest_abs[candidates]
        nearest_abs[candidates] = np.where(replace, absolute, nearest_abs[candidates])
        nearest_signed[candidates] = np.where(
            replace, distances[finite], nearest_signed[candidates]
        )
        nearest_z[candidates] = np.where(replace, z, nearest_z[candidates])

    tied_count = np.zeros(count, dtype=np.int32)
    for origin, normal in geometries:
        with np.errstate(over="ignore", invalid="ignore"):
            distances = (points[valid_indices] - origin) @ normal
        finite = np.isfinite(distances)
        candidates = valid_indices[finite & ~bad_distance[valid_indices]]
        absolute = np.abs(distances[finite & ~bad_distance[valid_indices]])
        minimum = nearest_abs[candidates]
        tolerance = tie_tolerance * np.maximum(1.0, np.maximum(minimum, absolute))
        tied_count[candidates] += np.abs(absolute - minimum) <= tolerance

    statuses[bad_distance] = "invalid_geometry"
    tie_indices = valid_indices[
        (tied_count[valid_indices] != 1) & ~bad_distance[valid_indices]
    ]
    statuses[tie_indices] = "nearest_plane_tie"
    sampleable = valid_indices[
        (nearest_z[valid_indices] >= 0)
        & (tied_count[valid_indices] == 1)
        & ~bad_distance[valid_indices]
    ]
    selected_z[sampleable] = nearest_z[sampleable]
    signed_distance[sampleable] = nearest_signed[sampleable]
    in_slab = (
        np.abs(signed_distance[sampleable])
        <= np.asarray([thicknesses[z] for z in nearest_z[sampleable]], dtype=np.float64)
        / 2.0
    )
    statuses[sampleable[~in_slab]] = "outside_slab"
    candidates_by_z = sampleable[in_slab]

    for z in np.unique(nearest_z[candidates_by_z]):
        indices = candidates_by_z[nearest_z[candidates_by_z] == z]
        z_index = int(z)
        try:
            rc_float = np.asarray(
                frames[z_index].to_native(points[indices]), dtype=np.float64
            )
        except (
            AttributeError,
            FloatingPointError,
            OverflowError,
            TypeError,
            ValueError,
            np.linalg.LinAlgError,
        ):
            statuses[indices] = "invalid_geometry"
            selected_z[indices] = -1
            signed_distance[indices] = np.nan
            continue
        if rc_float.shape != (len(indices), 2):
            statuses[indices] = "invalid_geometry"
            selected_z[indices] = -1
            signed_distance[indices] = np.nan
            continue
        finite_rc = np.all(np.isfinite(rc_float), axis=1)
        statuses[indices[~finite_rc]] = "invalid_geometry"
        selected_z[indices[~finite_rc]] = -1
        signed_distance[indices[~finite_rc]] = np.nan
        projected_indices = indices[finite_rc]
        projected_rc = rc_float[finite_rc]
        inside = (
            (projected_rc[:, 0] >= -0.5)
            & (projected_rc[:, 0] < rows - 0.5)
            & (projected_rc[:, 1] >= -0.5)
            & (projected_rc[:, 1] < columns - 0.5)
        )
        statuses[projected_indices[~inside]] = "outside_image"
        pixel_indices = projected_indices[inside]
        pixel_rc = np.rint(projected_rc[inside]).astype(np.int64)
        rounded_inside = (
            (pixel_rc[:, 0] >= 0)
            & (pixel_rc[:, 0] < rows)
            & (pixel_rc[:, 1] >= 0)
            & (pixel_rc[:, 1] < columns)
        )
        statuses[pixel_indices[~rounded_inside]] = "outside_image"
        pixel_indices = pixel_indices[rounded_inside]
        pixel_rc = pixel_rc[rounded_inside]
        if len(pixel_indices) == 0:
            continue
        native_rc[pixel_indices] = pixel_rc.astype(np.int32)
        statuses[pixel_indices] = "unavailable_sample"

        try:
            raw, unavailable = read_plane(z_index)
        except (
            ArithmeticError,
            AssertionError,
            EOFError,
            IndexError,
            KeyError,
            OSError,
            RuntimeError,
            TypeError,
            ValueError,
        ):
            statuses[pixel_indices] = "source_plane_unreadable"
            continue
        try:
            plane = np.asarray(raw)
        except (TypeError, ValueError):
            statuses[pixel_indices] = "invalid_source_plane"
            continue
        if plane.shape != (rows, columns) or plane.dtype.kind not in "iuf":
            statuses[pixel_indices] = "invalid_source_plane"
            continue
        unavailable_map: np.ndarray | None
        if isinstance(unavailable, (bool, np.bool_)):
            if unavailable:
                continue
            unavailable_map = None
        else:
            try:
                unavailable_map = np.asarray(unavailable)
            except (TypeError, ValueError):
                statuses[pixel_indices] = "invalid_unavailable_mask"
                continue
            if (
                unavailable_map.shape != (rows, columns)
                or unavailable_map.dtype.kind != "b"
            ):
                statuses[pixel_indices] = "invalid_unavailable_mask"
                continue
        pixel_values = plane[pixel_rc[:, 0], pixel_rc[:, 1]]
        available = np.isfinite(pixel_values)
        if unavailable_map is not None:
            available &= ~unavailable_map[pixel_rc[:, 0], pixel_rc[:, 1]]
        accepted_indices = pixel_indices[available]
        signal[accepted_indices] = pixel_values[available].astype(np.float64)
        statuses[accepted_indices] = "valid"

    return NativePointSamples(
        points, signal, selected_z, native_rc, signed_distance, tuple(statuses)
    )
