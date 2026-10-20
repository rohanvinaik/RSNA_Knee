"""One object's retained reference geometry and native point coordinates.

Native row/column coordinates are transformed with their own frame only. Trace
points already in patient LPS remain in that frame. This module carries point
measurements and relative coordinates; it does not resample or create volume.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np

SCHEMA = "study_map/v1"
AXES = ("medial", "posterior", "superior")
COORDINATE_STATUS_NAMES = (
    "ok",
    "invalid_coordinate",
    "nonfinite_coordinate",
    "unsupported_coordinate_kind",
    "invalid_lps_shape",
    "invalid_rc_shape",
    "boolean_coordinate",
    "invalid_coordinate_shape",
    "invalid_coordinate_dtype",
    "invalid_coordinates",
    "frame_unavailable",
    "malformed_frame",
)
JOINT_STATUS_NAMES = (
    "ok",
    "reference_unavailable",
    "side_unavailable",
    "precision_unavailable",
    "direction_unknown",
    *COORDINATE_STATUS_NAMES[1:],
)
_COORDINATE_STATUS = {name: i for i, name in enumerate(COORDINATE_STATUS_NAMES)}
_JOINT_STATUS = {name: i for i, name in enumerate(JOINT_STATUS_NAMES)}


@dataclass(frozen=True, slots=True)
class SpatialContext:
    """Reference data for one named object, copied from one study map record."""

    object_name: str
    map_status: str
    point_lps: tuple[float, float, float] | None
    precision_mm: tuple[float, float, float] | None
    keyplanes: Mapping[str, Any]
    side: str | None
    scale_mm: float | None
    scale_source: str | None
    scale_record_code: str | None
    code: str


@dataclass(frozen=True, slots=True)
class SpatialReading:
    """One addressed point with its original coordinate and derived facets."""

    object_name: str
    view: str
    slice_index: int | None
    row: int | None
    address: Mapping[str, Any]
    coordinate_kind: str
    coordinate: tuple[float, ...] | None
    provenance: Mapping[str, Any]
    coordinate_code: str
    point_lps: tuple[float, float, float] | None
    relative_lps_mm: tuple[float, float, float] | None
    relative_mps_mm: tuple[float | None, float | None, float | None] | None
    normalized_mps: tuple[float | None, float | None, float | None] | None
    axis_codes: tuple[str, str, str]
    joint_code: int | None
    joint_code_status: str


@dataclass(frozen=True, slots=True)
class BatchSpatialReading:
    """Array result for many points sharing one object reference context."""

    input_code: str
    coordinate_kind: str
    point_lps: np.ndarray
    relative_lps_mm: np.ndarray
    relative_mps_mm: np.ndarray
    normalized_mps: np.ndarray
    axis_digits: np.ndarray
    joint_code: np.ndarray
    coordinate_codes: np.ndarray
    joint_codes: np.ndarray
    object_name: str
    map_status: str
    reference_status: str
    precision_status: str
    side: str | None
    scale_mm: float | None
    scale_source: str | None
    keyplanes: Mapping[str, Any]
    coordinate_status_names: tuple[str, ...]
    joint_status_names: tuple[str, ...]


def coordinate_status_name(code: int) -> str:
    """Decode one compact batch coordinate status code."""
    if not isinstance(code, (int, np.integer)) or isinstance(code, (bool, np.bool_)):
        return "invalid_status_code"
    return (
        COORDINATE_STATUS_NAMES[code]
        if 0 <= code < len(COORDINATE_STATUS_NAMES)
        else "invalid_status_code"
    )


def joint_status_name(code: int) -> str:
    """Decode one compact batch joint status code."""
    if not isinstance(code, (int, np.integer)) or isinstance(code, (bool, np.bool_)):
        return "invalid_status_code"
    return (
        JOINT_STATUS_NAMES[code]
        if 0 <= code < len(JOINT_STATUS_NAMES)
        else "invalid_status_code"
    )


def _triple(value: Any) -> tuple[float, float, float] | None:
    if _has_boolean(value):
        return None
    try:
        arr = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError):
        return None
    if arr.shape != (3,) or not np.isfinite(arr).all():
        return None
    return (float(arr[0]), float(arr[1]), float(arr[2]))


def _positive_triple(value: Any) -> tuple[float, float, float] | None:
    result = _triple(value)
    if result is None or any(v <= 0 for v in result):
        return None
    return result


def _has_boolean(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return True
    if isinstance(value, np.ndarray):
        if value.dtype.kind == "b":
            return True
        if value.dtype.kind == "O":
            return any(isinstance(item, (bool, np.bool_)) for item in value.flat)
        return False
    if isinstance(value, (list, tuple)):
        return any(_has_boolean(item) for item in value)
    return False


def _scale(record: Mapping[str, Any]) -> tuple[float | None, str | None, str | None]:
    scale = record.get("scale")
    if not isinstance(scale, Mapping):
        return None, None, None
    source = scale.get("source")
    source = source if isinstance(source, str) else None
    record_code = scale.get("code")
    record_code = record_code if isinstance(record_code, str) else None
    mm = scale.get("mm")
    if isinstance(mm, (bool, np.bool_)):
        return None, source, record_code
    try:
        number = float(mm)
    except (TypeError, ValueError, OverflowError):
        return None, source, record_code
    if not math.isfinite(number) or number <= 0:
        return None, source, record_code
    return number, source, record_code


def prepare_spatial_context(
    record: Mapping[str, Any], object_name: str
) -> SpatialContext:
    """Read one object's reference position, precision, side and scale.

    Missing or unresolved fields remain independently unavailable; they do not
    remove the object or substitute a fabricated point or scale.
    """
    if not isinstance(record, Mapping) or record.get("schema") != SCHEMA:
        return SpatialContext(
            object_name,
            "unavailable",
            None,
            None,
            {},
            None,
            None,
            None,
            None,
            "invalid_map",
        )
    objects = record.get("objects")
    if not isinstance(objects, Mapping) or object_name not in objects:
        return SpatialContext(
            object_name,
            "unavailable",
            None,
            None,
            {},
            None,
            None,
            None,
            None,
            "object_not_in_map",
        )
    obj = objects[object_name]
    if not isinstance(obj, Mapping):
        return SpatialContext(
            object_name,
            "unavailable",
            None,
            None,
            {},
            None,
            None,
            None,
            None,
            "malformed_object_record",
        )
    status = obj.get("status")
    status = status if isinstance(status, str) else "unknown_status"
    point = _triple(obj.get("point_lps"))
    precision = _positive_triple(obj.get("precision_mm"))
    keyplanes = obj.get("key_planes")
    keyplanes = keyplanes if isinstance(keyplanes, Mapping) else {}
    side = record.get("knee")
    side = side if side in ("R", "L") else None
    scale_mm, scale_source, scale_record_code = _scale(record)
    if status != "complete" or point is None:
        code = "reference_unavailable"
    else:
        code = "ok"
    return SpatialContext(
        object_name,
        status,
        point,
        precision,
        dict(keyplanes),
        side,
        scale_mm,
        scale_source,
        scale_record_code,
        code,
    )


def _point_lps(
    coordinate: Any, kind: str, frame: Any
) -> tuple[tuple[float, float, float] | None, str]:
    if _has_boolean(coordinate):
        return None, "boolean_coordinate"
    try:
        point = np.asarray(coordinate, dtype=np.float64)
    except (TypeError, ValueError):
        return None, "invalid_coordinate"
    if not np.isfinite(point).all():
        return None, "nonfinite_coordinate"
    if kind == "native_lps":
        if point.shape != (3,):
            return None, "invalid_lps_shape"
        return (float(point[0]), float(point[1]), float(point[2])), "ok"
    if kind != "native_rc":
        return None, "unsupported_coordinate_kind"
    if point.shape != (2,):
        return None, "invalid_rc_shape"
    if not isinstance(frame, Mapping):
        return None, "frame_unavailable"
    origin = _triple(frame.get("origin_lps"))
    try:
        basis = np.asarray(frame.get("basis_lps"), dtype=np.float64)
    except (TypeError, ValueError):
        return None, "malformed_frame"
    if (
        origin is None
        or basis.shape != (3, 2)
        or not np.isfinite(basis).all()
        or np.linalg.matrix_rank(basis) < 2
    ):
        return None, "malformed_frame"
    result = np.asarray(origin) + basis @ point
    if not np.isfinite(result).all():
        return None, "malformed_frame"
    return (float(result[0]), float(result[1]), float(result[2])), "ok"


def _joint_code(codes: tuple[str, str, str]) -> tuple[int | None, str]:
    if any(code not in ("below", "within", "above") for code in codes):
        return None, "direction_unknown"
    digits = {"below": 0, "within": 1, "above": 2}
    return digits[codes[0]] * 9 + digits[codes[1]] * 3 + digits[codes[2]], "ok"


def _reading(
    context: SpatialContext,
    *,
    view: str,
    coordinate: Any,
    coordinate_kind: str,
    frame: Mapping[str, Any] | None,
    slice_index: int | None,
    row: int | None,
    address: Mapping[str, Any] | None,
    provenance: Mapping[str, Any] | None,
) -> SpatialReading:
    try:
        raw_arr = np.asarray(coordinate, dtype=np.float64)
        raw = (
            tuple(float(v) for v in raw_arr.reshape(-1))
            if np.isfinite(raw_arr).all()
            else None
        )
    except (TypeError, ValueError):
        raw = None
    point, point_code = _point_lps(coordinate, coordinate_kind, frame)
    delta_lps = None
    delta_mps: tuple[float | None, float | None, float | None] | None = None
    normalized: tuple[float | None, float | None, float | None] | None = None
    axis_codes = ["reference_unavailable"] * 3
    if (
        point is not None
        and context.point_lps is not None
        and context.map_status == "complete"
    ):
        delta_lps = (
            point[0] - context.point_lps[0],
            point[1] - context.point_lps[1],
            point[2] - context.point_lps[2],
        )
        sign = 1.0 if context.side == "R" else -1.0 if context.side == "L" else None
        axis_values = (
            None if sign is None else sign * delta_lps[0],
            delta_lps[1],
            delta_lps[2],
        )
        delta_mps = axis_values
        normalized_values: list[float | None] = [None, None, None]
        for i, value in enumerate(axis_values):
            if value is None:
                axis_codes[i] = "side_unavailable" if i == 0 else "ok"
                continue
            if context.precision_mm is None:
                axis_codes[i] = "precision_unavailable"
            else:
                tolerance = context.precision_mm[i]
                axis_codes[i] = (
                    "below"
                    if value < -tolerance
                    else "above"
                    if value > tolerance
                    else "within"
                )
            if context.scale_mm is not None:
                normalized_values[i] = value / context.scale_mm
        normalized = (
            normalized_values[0],
            normalized_values[1],
            normalized_values[2],
        )
        if context.scale_mm is None:
            scale_code = "scale_unavailable"
        else:
            scale_code = "ok"
    else:
        scale_code = "reference_unavailable"
    axis_code_tuple = (axis_codes[0], axis_codes[1], axis_codes[2])
    jcode, jstatus = _joint_code(axis_code_tuple)
    if (
        jcode is None
        and context.precision_mm is None
        and context.map_status == "complete"
    ):
        jstatus = "precision_unavailable"
    elif jcode is None and context.side is None and point is not None:
        jstatus = "side_unavailable"
    elif jcode is not None:
        jstatus = "ok"
    if point_code != "ok":
        jcode, jstatus = None, point_code
        delta_lps = None
        delta_mps = None
        normalized = None
    elif context.code != "ok":
        jcode, jstatus = None, context.code
    # Keep axis-level states and scale status independently visible in provenance.
    prov = dict(provenance or {})
    prov.setdefault("spatial_context_code", context.code)
    prov.setdefault("scale_code", scale_code)
    prov.setdefault("scale_source", context.scale_source)
    prov.setdefault("scale_record_code", context.scale_record_code)
    prov.setdefault("keyplanes", dict(context.keyplanes))
    return SpatialReading(
        context.object_name,
        view,
        slice_index,
        row,
        dict(address or {}),
        coordinate_kind,
        raw,
        prov,
        point_code,
        point,
        delta_lps,
        delta_mps,
        normalized,
        axis_code_tuple,
        jcode,
        jstatus,
    )


def native_rc_reading(
    context: SpatialContext,
    coordinate_rc: Any,
    *,
    frame: Mapping[str, Any] | None,
    view: str,
    slice_index: int | None = None,
    row: int | None = None,
    address: Mapping[str, Any] | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> SpatialReading:
    """Encode a native row/column point using its retained per-plane LPS frame."""
    return _reading(
        context,
        view=view,
        coordinate=coordinate_rc,
        coordinate_kind="native_rc",
        frame=frame,
        slice_index=slice_index,
        row=row,
        address=address,
        provenance=provenance,
    )


def native_lps_reading(
    context: SpatialContext,
    coordinate_lps: Any,
    *,
    view: str,
    slice_index: int | None = None,
    row: int | None = None,
    address: Mapping[str, Any] | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> SpatialReading:
    """Encode an already-patient-frame point, such as a retained physical trace."""
    return _reading(
        context,
        view=view,
        coordinate=coordinate_lps,
        coordinate_kind="native_lps",
        frame=None,
        slice_index=slice_index,
        row=row,
        address=address,
        provenance=provenance,
    )


def _empty_batch(
    count: int,
    *,
    input_code: str,
    coordinate_kind: str,
    context: SpatialContext,
) -> BatchSpatialReading:
    point = np.full((count, 3), np.nan, dtype=np.float64)
    relative_lps = np.full((count, 3), np.nan, dtype=np.float64)
    relative_mps = np.full((count, 3), np.nan, dtype=np.float64)
    normalized = np.full((count, 3), np.nan, dtype=np.float64)
    digits = np.full((count, 3), -1, dtype=np.int8)
    joint = np.full(count, -1, dtype=np.int16)
    coordinate_code = _COORDINATE_STATUS.get(
        input_code, _COORDINATE_STATUS["invalid_coordinates"]
    )
    joint_code = _JOINT_STATUS["reference_unavailable"]
    coordinate_codes = np.full(count, coordinate_code, dtype=np.uint8)
    joint_codes = np.full(count, joint_code, dtype=np.uint8)
    return BatchSpatialReading(
        input_code,
        coordinate_kind,
        point,
        relative_lps,
        relative_mps,
        normalized,
        digits,
        joint,
        coordinate_codes,
        joint_codes,
        context.object_name,
        context.map_status,
        context.code,
        "ok" if context.precision_mm is not None else "precision_unavailable",
        context.side,
        context.scale_mm,
        context.scale_source,
        dict(context.keyplanes),
        COORDINATE_STATUS_NAMES,
        JOINT_STATUS_NAMES,
    )


def _seal_batch(result: BatchSpatialReading) -> BatchSpatialReading:
    for name in (
        "point_lps",
        "relative_lps_mm",
        "relative_mps_mm",
        "normalized_mps",
        "axis_digits",
        "joint_code",
        "coordinate_codes",
        "joint_codes",
    ):
        getattr(result, name).flags.writeable = False
    return result


def _numeric_points(value: Any, width: int) -> tuple[np.ndarray | None, str]:
    if _has_boolean(value):
        return None, "invalid_coordinate_dtype"
    try:
        raw = np.asarray(value)
    except (TypeError, ValueError):
        return None, "invalid_coordinates"
    if raw.ndim != 2 or raw.shape[1] != width:
        return None, "invalid_coordinate_shape"
    if raw.dtype.kind not in "iuf":
        return None, "invalid_coordinate_dtype"
    try:
        points = raw.astype(np.float64, copy=False)
    except (TypeError, ValueError, OverflowError):
        return None, "invalid_coordinates"
    return points, "ok"


def _finish_batch(
    context: SpatialContext,
    points_lps: np.ndarray,
    coordinate_codes: np.ndarray,
    *,
    coordinate_kind: str,
    input_code: str = "ok",
) -> BatchSpatialReading:
    count = points_lps.shape[0]
    result = _empty_batch(
        count, input_code=input_code, coordinate_kind=coordinate_kind, context=context
    )
    result.point_lps[:] = points_lps
    result.coordinate_codes[:] = coordinate_codes
    valid = coordinate_codes == _COORDINATE_STATUS["ok"]
    for name, code in _COORDINATE_STATUS.items():
        if name != "ok":
            result.joint_codes[coordinate_codes == code] = _JOINT_STATUS[name]
    if (
        context.code != "ok"
        or context.point_lps is None
        or context.map_status != "complete"
    ):
        result.joint_codes[valid] = _JOINT_STATUS["reference_unavailable"]
        return _seal_batch(result)

    reference = np.asarray(context.point_lps, dtype=np.float64)
    result.relative_lps_mm[valid] = points_lps[valid] - reference

    # MPS medial direction depends on knee side; posterior/superior do not.
    if context.side == "R":
        result.relative_mps_mm[valid, 0] = result.relative_lps_mm[valid, 0]
    elif context.side == "L":
        result.relative_mps_mm[valid, 0] = -result.relative_lps_mm[valid, 0]
    result.relative_mps_mm[valid, 1:] = result.relative_lps_mm[valid, 1:]

    if context.scale_mm is not None:
        result.normalized_mps[:] = result.relative_mps_mm / context.scale_mm

    if context.precision_mm is not None:
        bounds = np.asarray(context.precision_mm, dtype=np.float64)
        values = result.relative_mps_mm
        measurable = valid[:, None] & np.isfinite(values)
        result.axis_digits[measurable] = 1
        below = measurable & (values < -bounds)
        above = measurable & (values > bounds)
        result.axis_digits[below] = 0
        result.axis_digits[above] = 2

    complete = np.all(result.axis_digits >= 0, axis=1)
    if np.any(complete):
        digits = result.axis_digits[complete].astype(np.int16)
        result.joint_code[complete] = digits[:, 0] * 9 + digits[:, 1] * 3 + digits[:, 2]
        result.joint_codes[complete] = _JOINT_STATUS["ok"]
    result.joint_codes[valid & ~complete] = _JOINT_STATUS["direction_unknown"]
    if context.precision_mm is None:
        result.joint_codes[valid & ~complete] = _JOINT_STATUS["precision_unavailable"]
    elif context.side is None:
        result.joint_codes[valid & ~complete] = _JOINT_STATUS["side_unavailable"]
    return _seal_batch(result)


def batch_native_lps_readings(
    context: SpatialContext,
    coordinates_lps: Any,
) -> BatchSpatialReading:
    """Transform N already-patient-frame LPS points using one object context."""
    points, code = _numeric_points(coordinates_lps, 3)
    if points is None:
        return _seal_batch(
            _empty_batch(
                0, input_code=code, coordinate_kind="native_lps", context=context
            )
        )
    finite = np.isfinite(points).all(axis=1)
    output = np.full((len(points), 3), np.nan, dtype=np.float64)
    output[finite] = points[finite]
    codes = np.full(len(points), _COORDINATE_STATUS["ok"], dtype=np.uint8)
    codes[~finite] = _COORDINATE_STATUS["nonfinite_coordinate"]
    return _finish_batch(context, output, codes, coordinate_kind="native_lps")


def batch_native_rc_readings(
    context: SpatialContext,
    coordinates_rc: Any,
    *,
    frame: Mapping[str, Any] | None = None,
    origins_lps: Any = None,
    bases_lps: Any = None,
) -> BatchSpatialReading:
    """Transform N native points using one frame or explicit per-row frames.

    Per-row frames are supplied as arrays shaped ``(N, 3)`` and ``(N, 3, 2)``.
    Bad frame rows receive a named coordinate code while other points proceed.
    """
    points, code = _numeric_points(coordinates_rc, 2)
    if points is None:
        return _seal_batch(
            _empty_batch(
                0, input_code=code, coordinate_kind="native_rc", context=context
            )
        )
    count = len(points)
    finite_points = np.isfinite(points).all(axis=1)
    output = np.full((count, 3), np.nan, dtype=np.float64)
    codes = np.full(count, _COORDINATE_STATUS["ok"], dtype=np.uint8)
    codes[~finite_points] = _COORDINATE_STATUS["nonfinite_coordinate"]

    if (origins_lps is None) != (bases_lps is None):
        codes[finite_points] = _COORDINATE_STATUS["malformed_frame"]
    elif origins_lps is not None:
        if _has_boolean(origins_lps) or _has_boolean(bases_lps):
            codes[finite_points] = _COORDINATE_STATUS["malformed_frame"]
            return _finish_batch(context, output, codes, coordinate_kind="native_rc")
        try:
            origins = np.asarray(origins_lps, dtype=np.float64)
            bases = np.asarray(bases_lps, dtype=np.float64)
        except (TypeError, ValueError):
            origins = np.empty((0, 3))
            bases = np.empty((0, 3, 2))
        if origins.shape != (count, 3) or bases.shape != (count, 3, 2):
            codes[finite_points] = _COORDINATE_STATUS["malformed_frame"]
        else:
            frame_ok = np.isfinite(origins).all(axis=1) & np.isfinite(bases).all(
                axis=(1, 2)
            )
            safe_bases = np.where(frame_ok[:, None, None], bases, 0.0)
            singular_values = np.linalg.svd(safe_bases, compute_uv=False)
            frame_ok &= singular_values[:, 1] > (
                np.finfo(np.float64).eps * 3 * singular_values[:, 0]
            )
            codes[finite_points & ~frame_ok] = _COORDINATE_STATUS["malformed_frame"]
            valid = finite_points & frame_ok
            if np.any(valid):
                output[valid] = origins[valid] + np.einsum(
                    "nij,nj->ni", bases[valid], points[valid]
                )
    elif frame is None:
        codes[finite_points] = _COORDINATE_STATUS["frame_unavailable"]
    else:
        if _has_boolean(frame):
            codes[finite_points] = _COORDINATE_STATUS["malformed_frame"]
            return _finish_batch(context, output, codes, coordinate_kind="native_rc")
        origin_raw = frame.get("origin_lps") if isinstance(frame, Mapping) else None
        basis_raw = frame.get("basis_lps") if isinstance(frame, Mapping) else None
        if _has_boolean(origin_raw) or _has_boolean(basis_raw):
            codes[finite_points] = _COORDINATE_STATUS["malformed_frame"]
            return _finish_batch(context, output, codes, coordinate_kind="native_rc")
        origin = _triple(origin_raw) if isinstance(frame, Mapping) else None
        try:
            basis = (
                np.asarray(basis_raw, dtype=np.float64)
                if isinstance(frame, Mapping)
                else np.empty((0, 0))
            )
        except (TypeError, ValueError):
            basis = np.empty((0, 0))
        valid_frame = (
            origin is not None
            and basis.shape == (3, 2)
            and np.isfinite(basis).all()
            and np.linalg.matrix_rank(basis) == 2
        )
        if not valid_frame:
            codes[finite_points] = _COORDINATE_STATUS["malformed_frame"]
        else:
            valid = finite_points
            output[valid] = np.asarray(origin) + points[valid] @ basis.T

    overflowed = (
        finite_points
        & ~np.isfinite(output).all(axis=1)
        & (codes == _COORDINATE_STATUS["ok"])
    )
    codes[overflowed] = _COORDINATE_STATUS["malformed_frame"]
    return _finish_batch(context, output, codes, coordinate_kind="native_rc")
