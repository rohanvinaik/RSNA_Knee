"""Native DICOM plane geometry and case-relative search constraints for squint profiles."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from functools import lru_cache
from typing import Any

import numpy as np

from knee.collapse import relative
from knee.collapse.physical import PlaneFrame
from knee.collapse.study_map import StudyMap

_ORIENTATIONS = ("sagittal", "coronal", "axial")
_GEOMETRY_API = "knee.diagnosis.squint_geometry.object_geometry/v1"


def _point(value: object) -> tuple[float, float, float] | None:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or len(value) != 3
    ):
        return None
    try:
        result = tuple(float(item) for item in value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if all(math.isfinite(item) for item in result) else None


def _orientation(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    key = value.strip().lower()
    return key if key in _ORIENTATIONS else None


def _slice_precision(
    geometry: Mapping[str, Any], index: int, normal: np.ndarray
) -> float:
    positions = geometry.get("position")
    if (
        not isinstance(positions, np.ndarray)
        or positions.ndim != 2
        or positions.shape[1:] != (3,)
    ):
        return math.nan
    steps = []
    for neighbor in (index - 1, index + 1):
        if 0 <= neighbor < len(positions):
            delta = positions[neighbor] - positions[index]
            if np.all(np.isfinite(delta)):
                step = abs(float(normal @ delta))
                if math.isfinite(step) and step > 0:
                    steps.append(step)
    return min(steps) / 2.0 if steps else math.nan


def _series_map(series_by_uid: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    result = {}
    for key, record in series_by_uid.items():
        if isinstance(key, str) and isinstance(record, Mapping):
            uid = record.get("series_uid", key)
            if isinstance(uid, str) and uid:
                result[uid] = record
    return result


def object_geometry(subject: str, regions: list, series_by_uid: dict) -> dict:
    """Build one map from native one-slice region addresses; never infer tissue support."""
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("squint_geometry_subject_required")
    if not isinstance(regions, list) or not isinstance(series_by_uid, dict):
        raise TypeError("squint_geometry_regions_and_series_required")
    records = _series_map(series_by_uid)
    study_map = StudyMap(names=(subject,))
    region_sources: list[dict[str, Any]] = []
    for ordinal, region in enumerate(regions):
        if not isinstance(region, Mapping):
            continue
        uid = region.get("series_uid")
        record = records.get(uid) if isinstance(uid, str) else None
        view = region.get("view")
        if not isinstance(view, Mapping) and record is not None:
            view = record.get("view")
        orientation = _orientation(
            view.get("orientation") if isinstance(view, Mapping) else None
        )
        window = region.get("window")
        source = f"{_GEOMETRY_API}:region:{ordinal}"
        if orientation is None:
            continue
        if record is None:
            plane = relative.invalid_plane(
                subject,
                orientation,
                "series_missing",
                series_uid=str(uid or ""),
                provenance=source,
            )
            study_map.offer(subject, plane, support=None, source=source)
            region_sources.append(
                {"series_uid": uid, "window": window, "status": "series_missing"}
            )
            continue
        stack = record.get("stack")
        geometry = record.get("geometry")
        if (
            not isinstance(window, (tuple, list))
            or len(window) != 6
            or any(type(v) is not int for v in window)
        ):
            plane = relative.invalid_plane(
                subject,
                orientation,
                "window_invalid",
                series_uid=str(uid),
                provenance=source,
            )
            study_map.offer(subject, plane, support=None, source=source)
            region_sources.append(
                {"series_uid": uid, "window": None, "status": "window_invalid"}
            )
            continue
        z0, z1, *_ = window
        median = getattr(stack, "median", None)
        bounds = np.asarray(getattr(stack, "bounds_rc", None))
        if (
            not isinstance(median, np.ndarray)
            or median.ndim != 3
            or bounds.ndim != 3
            or bounds.shape[-1] != 4
            or bounds.shape[:2] != median.shape[1:]
            or not (0 <= z0 <= z1 <= median.shape[0])
            or not (0 <= window[2] <= window[3] <= bounds.shape[0])
            or not (0 <= window[4] <= window[5] <= bounds.shape[1])
        ):
            plane = relative.invalid_plane(
                subject,
                orientation,
                "window_out_of_bounds",
                series_uid=str(uid),
                slice=z0,
                provenance=source,
            )
            study_map.offer(subject, plane, support=None, source=source)
            region_sources.append(
                {
                    "series_uid": uid,
                    "window": list(window),
                    "status": "window_out_of_bounds",
                }
            )
            continue
        if z1 - z0 != 1:
            plane = relative.invalid_plane(
                subject,
                orientation,
                "window_not_one_native_slice",
                series_uid=str(uid),
                slice=z0,
                provenance=source,
            )
            study_map.offer(subject, plane, support=None, source=source)
            region_sources.append(
                {
                    "series_uid": uid,
                    "window": list(window),
                    "status": "window_not_one_native_slice",
                }
            )
            continue
        if not isinstance(geometry, Mapping):
            plane = relative.invalid_plane(
                subject,
                orientation,
                "geometry_unavailable",
                series_uid=str(uid),
                slice=z0,
                provenance=source,
            )
            study_map.offer(subject, plane, support=None, source=source)
            region_sources.append(
                {
                    "series_uid": uid,
                    "window": list(window),
                    "status": "geometry_unavailable",
                }
            )
            continue
        try:
            frame = PlaneFrame.from_dicom(
                geometry["position"][z0],
                geometry["orientation"][z0],
                geometry["spacing"][z0],
            )
        except (KeyError, IndexError, TypeError, ValueError):
            plane = relative.invalid_plane(
                subject,
                orientation,
                "frame_unavailable",
                series_uid=str(uid),
                slice=z0,
                provenance=source,
            )
            study_map.offer(subject, plane, support=None, source=source)
            region_sources.append(
                {
                    "series_uid": uid,
                    "window": list(window),
                    "status": "frame_unavailable",
                }
            )
            continue
        precision = _slice_precision(geometry, z0, frame.normal())
        plane = relative.plane_of_frame(
            subject,
            orientation,
            series_uid=str(uid),
            slice=z0,
            frame=frame,
            precision_mm=precision,
            provenance=source,
            reason="one native slice selected by current-study squint region",
        )
        study_map.offer(subject, plane, support=None, source=source)
        region_sources.append(
            {
                "series_uid": uid,
                "window": list(window),
                "status": "selected" if plane.usable else plane.outcome,
                "precision_status": "measured"
                if math.isfinite(precision)
                else "unavailable",
                "source": source,
            }
        )

    selected = {
        orientation: study_map.selected(subject, orientation)
        for orientation in _ORIENTATIONS
    }
    position = study_map.positions()[subject]
    point = None if position.point_lps is None else list(position.point_lps)
    line = None if position.line_direction is None else list(position.line_direction)
    return {
        "schema": "knee.squint-object-geometry/v1",
        "subject": subject,
        "planes": {key: plane.address() for key, plane in selected.items()},
        "reference": {
            "status": position.status,
            "geometry": position.geometry,
            "point_lps": point,
            "line_direction": line,
            "problems": dict(position.problems),
            "precision_mm": None
            if position.precision_mm is None
            else list(position.precision_mm),
            "rank": position.rank,
            "condition": None
            if not math.isfinite(position.condition)
            else position.condition,
            "provenance": {key: value.address() for key, value in selected.items()},
        },
        "support": None,
        "regions": region_sources,
    }


def _regions_for(case: Mapping[str, Any], subject: str) -> list[Mapping[str, Any]]:
    regions = case.get("regions", ())
    if isinstance(regions, Mapping):
        value = regions.get(subject, ())
        if isinstance(value, Mapping):
            return [value]
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return [row for row in value if isinstance(row, Mapping)]
        return []
    if isinstance(regions, Sequence) and not isinstance(regions, (str, bytes)):
        return [
            row
            for row in regions
            if isinstance(row, Mapping)
            and row.get("subject", row.get("object", subject)) == subject
        ]
    return []


def _unique_source_point(
    case: Mapping[str, Any], subject: str
) -> tuple[float, float, float] | None | str:
    points = {
        _point(region.get("source_point_lps")) for region in _regions_for(case, subject)
    }
    points.discard(None)
    if len(points) > 1:
        return "conflicting_source_points"
    return next(iter(points)) if points else None


def _complete_point(
    geometry_by_subject: Mapping[str, Any], subject: str
) -> tuple[float, float, float] | None:
    value = geometry_by_subject.get(subject)
    if not isinstance(value, Mapping):
        return None
    reference = value.get("reference")
    if (
        not isinstance(reference, Mapping)
        or reference.get("status") != relative.COMPLETE
    ):
        return None
    return _point(reference.get("point_lps"))


def _positive_separation(
    points: Mapping[str, tuple[float, float, float] | None],
) -> float | None:
    femur, tibia = points.get("femur"), points.get("tibia")
    if femur is None or tibia is None:
        return None
    distance = float(np.linalg.norm(np.asarray(femur) - np.asarray(tibia)))
    return distance if math.isfinite(distance) and distance > 0 else None


def relative_scope_priors(
    subject: str, anchors: tuple, cases: list, geometry_by_subject: dict
) -> dict:
    """Translate source-case offsets onto current selected anchor planes."""
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("squint_geometry_subject_required")
    if (
        not isinstance(anchors, tuple)
        or not isinstance(cases, list)
        or not isinstance(geometry_by_subject, dict)
    ):
        raise TypeError("squint_relative_prior_inputs_invalid")
    anchor_names = tuple(name for name in anchors if isinstance(name, str) and name)
    current_points = {
        name: _complete_point(geometry_by_subject, name)
        for name in (*anchor_names, "femur", "tibia")
    }
    query_scale = _positive_separation(current_points)
    source_index: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for row in cases:
        if isinstance(row, Mapping):
            uid, name = row.get("study_uid"), row.get("subject")
            if isinstance(uid, str) and isinstance(name, str):
                source_index.setdefault((uid, name), []).append(row)
    source_cases = []
    for case_index, case in enumerate(cases):
        if not isinstance(case, Mapping) or case.get("subject") != subject:
            continue
        uid = case.get("study_uid")
        if not isinstance(uid, str) or not uid:
            continue
        target = _unique_source_point(case, subject)
        if isinstance(target, str):
            source_cases.append(
                {
                    "case_index": case_index,
                    "study_uid": uid,
                    "status": target,
                    "planes": [],
                }
            )
            continue
        if target is None:
            source_cases.append(
                {
                    "case_index": case_index,
                    "study_uid": uid,
                    "status": "target_source_point_unavailable",
                    "planes": [],
                }
            )
            continue
        source_anchor_points = {}
        failure = None
        for anchor in anchor_names:
            matches = source_index.get((uid, anchor), ())
            points = {_unique_source_point(row, anchor) for row in matches}
            points.discard(None)
            if any(isinstance(point, str) for point in points) or len(points) > 1:
                failure = f"anchor_source_point_conflict:{anchor}"
                break
            source_anchor_points[anchor] = next(iter(points)) if points else None
        if failure is not None:
            source_cases.append(
                {
                    "case_index": case_index,
                    "study_uid": uid,
                    "status": failure,
                    "planes": [],
                }
            )
            continue
        source_scale_points = {}
        for anchor in ("femur", "tibia"):
            matches = source_index.get((uid, anchor), ())
            points = {_unique_source_point(row, anchor) for row in matches}
            points.discard(None)
            source_scale_points[anchor] = (
                next(iter(points))
                if len(points) == 1 and all(not isinstance(p, str) for p in points)
                else None
            )
        source_scale = _positive_separation(source_scale_points)
        normalized = query_scale is not None and source_scale is not None
        factor = query_scale / source_scale if normalized else 1.0
        shifted = []
        for anchor in anchor_names:
            source_anchor = source_anchor_points.get(anchor)
            current = geometry_by_subject.get(anchor)
            if source_anchor is None or not isinstance(current, Mapping):
                continue
            planes = current.get("planes", {})
            if not isinstance(planes, Mapping):
                continue
            delta = (np.asarray(target) - np.asarray(source_anchor)) * factor
            for orientation, plane in planes.items():
                if (
                    not isinstance(plane, Mapping)
                    or plane.get("outcome") != relative.SELECTED
                ):
                    continue
                normal = _point(plane.get("normal"))
                offset = plane.get("offset_mm")
                precision = plane.get("precision_mm")
                if (
                    normal is None
                    or not isinstance(offset, (int, float))
                    or not math.isfinite(float(offset))
                ):
                    continue
                normal_array = np.asarray(normal)
                shifted.append(
                    {
                        "anchor": anchor,
                        "orientation": orientation,
                        "normal": list(normal),
                        "offset_mm": float(offset + normal_array @ delta),
                        "precision_mm": precision
                        if isinstance(precision, (int, float))
                        and math.isfinite(float(precision))
                        else None,
                        "source_plane": dict(plane),
                        "displacement_mm": delta.tolist(),
                    }
                )
        source_cases.append(
            {
                "case_index": case_index,
                "case_id": case.get("case_id"),
                "study_uid": uid,
                "status": "available" if shifted else "no_current_anchor_planes",
                "scale_status": "normalized_by_femur_tibia_separation"
                if normalized
                else "unscaled_millimetres",
                "source_separation_mm": source_scale,
                "query_separation_mm": query_scale,
                "planes": shifted,
            }
        )
    return {
        "schema": "knee.squint-relative-scope-priors/v1",
        "subject": subject,
        "anchors": list(anchor_names),
        "cases": source_cases,
    }


def _projected_tile_bounds(
    series: dict[str, Any], normal: np.ndarray
) -> np.ndarray | None:
    """Cache every tile's projected LPS interval for one source series and plane normal."""
    cache = series.setdefault("_squint_geometry_projection_cache", {})
    key = tuple(float(value) for value in normal)
    if key in cache:
        return cache[key]
    stack = series.get("stack")
    geometry = series.get("geometry")
    if stack is None or not isinstance(geometry, Mapping):
        return None
    median = getattr(stack, "median", None)
    bounds = np.asarray(getattr(stack, "bounds_rc", None))
    positions, orientations, spacings = (
        geometry.get("position"),
        geometry.get("orientation"),
        geometry.get("spacing"),
    )
    if (
        not isinstance(median, np.ndarray)
        or median.ndim != 3
        or bounds.ndim != 3
        or bounds.shape[-1] != 4
        or bounds.shape[:2] != median.shape[1:]
        or not all(
            isinstance(value, np.ndarray)
            for value in (positions, orientations, spacings)
        )
        or len(positions) != median.shape[0]
        or len(orientations) != len(positions)
        or len(spacings) != len(positions)
    ):
        return None
    output = np.full((*median.shape, 2), np.nan, dtype=np.float64)
    tile_rows, tile_cols = bounds.shape[:2]
    row0 = bounds[..., 0].astype(np.float64) - 0.5
    row1 = bounds[..., 1].astype(np.float64) - 0.5
    col0 = bounds[..., 2].astype(np.float64) - 0.5
    col1 = bounds[..., 3].astype(np.float64) - 0.5
    corner_rows = np.stack((row0, row0, row1, row1), axis=-1)
    corner_cols = np.stack((col0, col1, col0, col1), axis=-1)
    native_corners = np.stack((corner_rows, corner_cols), axis=-1).reshape(-1, 2)
    for index in range(median.shape[0]):
        try:
            frame = PlaneFrame.from_dicom(
                positions[index], orientations[index], spacings[index]
            )
        except (IndexError, ValueError, TypeError):
            continue
        projected = (frame.to_patient(native_corners) @ normal).reshape(
            tile_rows, tile_cols, 4
        )
        low, high = projected.min(axis=-1), projected.max(axis=-1)
        precision = _slice_precision(geometry, index, frame.normal())
        if math.isfinite(precision):
            reach = precision * abs(float(normal @ frame.normal()))
            low, high = low - reach, high + reach
        output[index, ..., 0] = low
        output[index, ..., 1] = high
    output.flags.writeable = False
    cache[key] = output
    return output


def _candidate_interval(
    series: dict[str, Any], window: tuple, normal: np.ndarray
) -> tuple[float, float] | None:
    stack = series.get("stack")
    if stack is None:
        return None
    z0, z1, r0, r1, c0, c1 = window
    median = getattr(stack, "median", None)
    bounds = np.asarray(getattr(stack, "bounds_rc", None))
    if (
        not isinstance(median, np.ndarray)
        or median.ndim != 3
        or bounds.ndim != 3
        or bounds.shape[-1] != 4
        or bounds.shape[:2] != median.shape[1:]
        or not (0 <= z0 < z1 <= median.shape[0])
        or not (0 <= r0 < r1 <= bounds.shape[0])
        or not (0 <= c0 < c1 <= bounds.shape[1])
    ):
        return None
    projected = _projected_tile_bounds(series, normal)
    if projected is None:
        return None
    selected = projected[z0:z1, r0:r1, c0:c1]
    if not selected.size or not np.isfinite(selected).all():
        return None
    return float(np.min(selected[..., 0])), float(np.max(selected[..., 1]))


@lru_cache(maxsize=32)
def _compile_scope_cases(canonical_cases: str) -> tuple:
    """Compile JSON-safe constraints; the content key makes mutable caller input safe."""
    raw_cases = json.loads(canonical_cases)
    compiled = []
    for case in raw_cases:
        if not isinstance(case, Mapping) or case.get("status") != "available":
            continue
        rows = case.get("planes")
        if not isinstance(rows, list) or not rows:
            compiled.append(((), True))
            continue
        planes = []
        unknown = False
        for plane in rows:
            if not isinstance(plane, Mapping):
                continue
            normal = _point(plane.get("normal"))
            offset, precision = plane.get("offset_mm"), plane.get("precision_mm")
            if (
                normal is None
                or not isinstance(offset, (int, float))
                or not math.isfinite(float(offset))
            ):
                unknown = True
                planes.append((None, None, None))
                continue
            norm = math.sqrt(sum(value * value for value in normal))
            if not math.isfinite(norm) or not math.isclose(
                norm, 1.0, rel_tol=1e-7, abs_tol=1e-7
            ):
                unknown = True
                planes.append((None, None, None))
                continue
            usable_precision = (
                float(precision)
                if isinstance(precision, (int, float))
                and math.isfinite(float(precision))
                else None
            )
            if usable_precision is None:
                unknown = True
            planes.append((normal, float(offset), usable_precision))
        compiled.append((tuple(planes), unknown))
    return tuple(compiled)


def window_scope_code(series: dict, window: tuple, priors: dict) -> str:
    """Test projected physical intervals against one alternative's conjunctive plane slabs."""
    if not isinstance(series, dict) or not isinstance(priors, dict):
        return "geometry_unavailable"
    if (
        not isinstance(window, tuple)
        or len(window) != 6
        or any(type(value) is not int for value in window)
    ):
        return "geometry_unavailable"
    cases = priors.get("cases")
    if not isinstance(cases, list):
        return "geometry_unavailable"
    try:
        canonical_cases = json.dumps(
            cases,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        compiled_cases = _compile_scope_cases(canonical_cases)
    except (TypeError, ValueError):
        compiled_cases = None
    if compiled_cases is None:
        return "geometry_unavailable"
    intervals = {}
    tested_constraint = False
    uncertain_alternative = False
    for planes, case_unknown in compiled_cases:
        if not planes:
            uncertain_alternative = uncertain_alternative or case_unknown
            continue
        case_constraints = []
        for normal, offset, precision in planes:
            if normal is None or offset is None:
                case_unknown = True
                continue
            unit = np.asarray(normal, dtype=np.float64)
            interval = intervals.get(tuple(unit.tolist()))
            if interval is None:
                interval = _candidate_interval(series, window, unit)
                if interval is not None:
                    intervals[tuple(unit.tolist())] = interval
            if interval is None or precision is None:
                case_unknown = True
                continue
            tested_constraint = True
            if interval[1] < offset - precision or interval[0] > offset + precision:
                case_constraints.append(False)
            else:
                case_constraints.append(True)
        if case_constraints and all(case_constraints) and not case_unknown:
            return "eligible"
        if case_unknown and not any(value is False for value in case_constraints):
            uncertain_alternative = True
    if uncertain_alternative or not tested_constraint:
        return "geometry_unavailable"
    return "outside_anatomical_prior"


def _prepared_scope_cases(priors: dict) -> tuple | None:
    cases = priors.get("cases")
    if not isinstance(cases, list):
        return None
    try:
        canonical_cases = json.dumps(
            cases,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        return _compile_scope_cases(canonical_cases)
    except (TypeError, ValueError):
        return None


def _flatten_scope_cases(compiled_cases: tuple) -> tuple:
    normal_indices: dict[tuple[float, float, float], int] = {}
    normals = []
    max_planes = max((len(planes) for planes, _ in compiled_cases), default=0)
    case_indices = np.full((len(compiled_cases), max_planes), -1, dtype=np.int64)
    offsets = np.full((len(compiled_cases), max_planes), np.nan, dtype=np.float64)
    precisions = np.full((len(compiled_cases), max_planes), np.nan, dtype=np.float64)
    present = np.zeros((len(compiled_cases), max_planes), dtype=np.bool_)
    static_unknown = np.zeros(len(compiled_cases), dtype=np.bool_)
    for case_index, (planes, unknown) in enumerate(compiled_cases):
        static_unknown[case_index] = unknown
        for plane_index, (normal, offset, precision) in enumerate(planes):
            present[case_index, plane_index] = True
            if normal is None or offset is None:
                continue
            normal_index = normal_indices.get(normal)
            if normal_index is None:
                normal_index = len(normals)
                normal_indices[normal] = normal_index
                normals.append(normal)
            case_indices[case_index, plane_index] = normal_index
            offsets[case_index, plane_index] = float(offset)
            precisions[case_index, plane_index] = (
                math.nan if precision is None else float(precision)
            )
    return tuple(normals), case_indices, offsets, precisions, present, static_unknown


def _window_codes_from_intervals(
    intervals: np.ndarray,
    case_indices: np.ndarray,
    offsets: np.ndarray,
    precisions: np.ndarray,
    present: np.ndarray,
    static_unknown: np.ndarray,
) -> list[str]:
    window_count = len(intervals)
    case_count, plane_count = case_indices.shape
    if case_count == 0 or plane_count == 0:
        return ["geometry_unavailable"] * window_count
    safe_indices = np.maximum(case_indices, 0)
    projected = intervals[:, safe_indices, :]
    known = (
        present[None, :, :]
        & (case_indices[None, :, :] >= 0)
        & np.isfinite(precisions[None, :, :])
        & np.isfinite(projected).all(axis=-1)
    )
    misses = known & (
        (projected[..., 1] < offsets[None, :, :] - precisions[None, :, :])
        | (projected[..., 0] > offsets[None, :, :] + precisions[None, :, :])
    )
    unknown = static_unknown[None, :] | np.any(present[None, :, :] & ~known, axis=2)
    case_failed = np.any(misses, axis=2)
    case_success = np.any(present, axis=1)[None, :] & ~unknown & ~case_failed
    case_uncertain = unknown & ~case_failed
    tested_constraint = np.any(known, axis=(1, 2))
    uncertain_alternative = np.any(case_uncertain, axis=1)
    result = []
    for index in range(window_count):
        if np.any(case_success[index]):
            result.append("eligible")
        elif uncertain_alternative[index] or not tested_constraint[index]:
            result.append("geometry_unavailable")
        else:
            result.append("outside_anatomical_prior")
    return result


def window_scope_codes(
    series: dict, windows: Sequence[tuple], priors: dict
) -> list[str]:
    """Evaluate a bounded batch of windows against one compiled, fixed prior set."""
    if not isinstance(series, dict) or not isinstance(priors, dict):
        return (
            ["geometry_unavailable"] * len(windows)
            if isinstance(windows, Sequence)
            else []
        )
    if not isinstance(windows, Sequence) or isinstance(windows, (str, bytes)):
        raise TypeError("squint_windows_sequence_required")
    compiled = _prepared_scope_cases(priors)
    if compiled is None:
        return ["geometry_unavailable"] * len(windows)
    normals, case_indices, offsets, precisions, present, static_unknown = (
        _flatten_scope_cases(compiled)
    )
    if not normals:
        return ["geometry_unavailable"] * len(windows)
    results = []
    for start in range(0, len(windows), 128):
        batch = windows[start : start + 128]
        batch_intervals = np.full(
            (len(batch), len(normals), 2), np.nan, dtype=np.float64
        )
        for row_index, window in enumerate(batch):
            if (
                not isinstance(window, tuple)
                or len(window) != 6
                or any(type(value) is not int for value in window)
            ):
                continue
            for normal_index, normal in enumerate(normals):
                interval = _candidate_interval(
                    series, window, np.asarray(normal, dtype=np.float64)
                )
                if interval is not None:
                    batch_intervals[row_index, normal_index] = interval
        results.extend(
            _window_codes_from_intervals(
                batch_intervals,
                case_indices,
                offsets,
                precisions,
                present,
                static_unknown,
            )
        )
    return results


__all__ = [
    "object_geometry",
    "relative_scope_priors",
    "window_scope_code",
    "window_scope_codes",
]
