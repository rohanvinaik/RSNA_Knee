"""Finite, anatomy-authored candidate windows over current-study squint tiles.

This module proposes addresses only. It does not identify an object, interpret
signal, or create an observation; every proposed window is one acquired slice.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping
from typing import Any

import numpy as np

from knee.collapse.anatomy_map import MAP_OBJECTS, ideal_vector, target_span_mm

_INITIAL_BONES = frozenset(("femur", "tibia", "patella", "fibula"))
_EPS = float(np.finfo(np.float64).eps)


def _side(value: str | None) -> tuple[str | None, tuple[tuple[str, float], ...]]:
    text = value.strip().lower() if isinstance(value, str) else ""
    if text in ("left", "l"):
        return "left", (("left", -1.0),)
    if text in ("right", "r"):
        return "right", (("right", 1.0),)
    return None, (("left_hypothesis", -1.0), ("right_hypothesis", 1.0))


def _mps_to_lps(vector: np.ndarray, medial_sign: float) -> np.ndarray:
    return np.asarray((medial_sign * vector[0], vector[1], vector[2]), dtype=np.float64)


def _leg_bounds(value: Any) -> tuple[np.ndarray | None, str]:
    if value is None:
        return None, "not_supplied"
    try:
        bounds = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError):
        return None, "malformed"
    if bounds.shape != (2, 3) or not np.all(np.isfinite(bounds)):
        return None, "malformed_or_nonfinite"
    if np.any(bounds[0] >= bounds[1]):
        return None, "empty_or_degenerate"
    return bounds, "measured_current_study_extents"


def _stack_arrays(
    series: Any,
) -> tuple[Any | None, np.ndarray | None, np.ndarray | None, str]:
    if not isinstance(series, Mapping):
        return None, None, None, "series_not_mapping"
    stack = series.get("stack")
    if stack is None:
        return None, None, None, "stack_unavailable"
    if getattr(stack, "code", None) != "present":
        return stack, None, None, "stack_" + str(getattr(stack, "code", "code_missing"))
    try:
        centres = np.asarray(stack.centres_lps, dtype=np.float64)
        coverage = np.asarray(stack.coverage, dtype=np.float64)
    except (AttributeError, TypeError, ValueError):
        return stack, None, None, "centres_or_coverage_unavailable"
    if (
        centres.ndim != 4
        or centres.shape[-1] != 3
        or coverage.shape != centres.shape[:3]
    ):
        return stack, None, None, "geometry_shape_invalid"
    if any(size <= 0 for size in centres.shape[:3]):
        return stack, None, None, "geometry_empty"
    try:
        bounds_rc = np.asarray(stack.bounds_rc)
    except (AttributeError, TypeError, ValueError):
        return stack, None, None, "native_bounds_unavailable"
    if bounds_rc.shape != centres.shape[1:3] + (4,) or not np.issubdtype(
        bounds_rc.dtype, np.integer
    ):
        return stack, None, None, "native_bounds_shape_invalid"
    if (
        np.any(bounds_rc[..., 1] <= bounds_rc[..., 0])
        or np.any(bounds_rc[..., 3] <= bounds_rc[..., 2])
        or np.any(~np.isfinite(coverage))
        or np.any((coverage < 0) | (coverage > 1))
    ):
        return stack, None, None, "native_bounds_or_coverage_invalid"
    return stack, centres, coverage, "available"


def _local_axis(
    slice_centres: np.ndarray, row: int, col: int, axis: int
) -> tuple[np.ndarray | None, float | None, str]:
    differences = np.diff(slice_centres, axis=axis)
    lengths = np.linalg.norm(differences, axis=-1)
    usable = (
        np.all(np.isfinite(differences), axis=-1) & np.isfinite(lengths) & (lengths > 0)
    )
    if not np.any(usable):
        return None, None, "axis_has_no_finite_step"
    step = float(np.median(lengths[usable]))
    if axis == 0:
        before = slice_centres[row - 1, col] if row > 0 else None
        after = (
            slice_centres[row + 1, col] if row + 1 < slice_centres.shape[0] else None
        )
    else:
        before = slice_centres[row, col - 1] if col > 0 else None
        after = (
            slice_centres[row, col + 1] if col + 1 < slice_centres.shape[1] else None
        )
    here = slice_centres[row, col]
    candidates = []
    if before is not None and np.all(np.isfinite(before)):
        candidates.append(here - before)
    if after is not None and np.all(np.isfinite(after)):
        candidates.append(after - here)
    if len(candidates) == 2:
        direction = candidates[0] + candidates[1]
    elif candidates:
        direction = candidates[0]
    else:
        return None, step, "local_axis_unavailable"
    norm = float(np.linalg.norm(direction))
    if not math.isfinite(norm) or norm <= 0:
        return None, step, "local_axis_degenerate"
    return direction / norm, step, "available"


def _nearest_centres(
    point: np.ndarray, centres: np.ndarray, valid: np.ndarray
) -> list[tuple[int, int, int]]:
    positions = np.argwhere(valid)
    if not len(positions):
        return []
    distances = np.linalg.norm(centres[valid] - point, axis=1)
    minimum = float(np.min(distances))
    tolerance = 8.0 * _EPS * max(1.0, minimum)
    tied = np.flatnonzero(np.abs(distances - minimum) <= tolerance)
    return [tuple(int(value) for value in positions[index]) for index in tied]


def _window(
    z: int,
    row: int,
    col: int,
    requested_rows: int,
    requested_cols: int,
    shape: tuple[int, int, int],
) -> tuple[tuple[int, int, int, int, int, int], dict[str, Any]]:
    depth, rows, cols = shape
    row_count = min(requested_rows, rows)
    col_count = min(requested_cols, cols)
    row_start = min(max(row - requested_rows // 2, 0), rows - row_count)
    col_start = min(max(col - requested_cols // 2, 0), cols - col_count)
    row_stop = row_start + row_count
    col_stop = col_start + col_count
    z_index = min(max(z, 0), depth - 1)
    address = (z_index, z_index + 1, row_start, row_stop, col_start, col_stop)
    return address, {
        "requested_tile_size": [requested_rows, requested_cols],
        "used_tile_size": [row_count, col_count],
        "clipped_to_grid": requested_rows > rows or requested_cols > cols,
    }


def _native_anchor_hypothesis(
    anchor_name: str,
    record: Any,
    *,
    bounds: np.ndarray | None,
    target: str,
    scale: float | None,
    medial_sign: float,
) -> tuple[np.ndarray | None, dict[str, Any]]:
    """Resolve a complete point or project a weak atlas seed onto selected planes."""
    if not isinstance(record, Mapping):
        return None, {"anchor": anchor_name, "status": "anchor_not_mapping"}
    reference = record.get("reference")
    if not isinstance(reference, Mapping):
        reference = record
    reference_status = reference.get("status")
    if reference_status == "complete":
        try:
            point = np.asarray(reference.get("point_lps"), dtype=np.float64)
        except (TypeError, ValueError):
            point = np.asarray([], dtype=np.float64)
        if point.shape == (3,) and np.all(np.isfinite(point)):
            return point, {
                "anchor": anchor_name,
                "kind": "complete_native_reference",
                "anchor_observation_status": "complete",
                "prior_only": False,
                "reference": dict(reference),
            }
        return None, {
            "anchor": anchor_name,
            "status": "complete_reference_point_invalid",
            "reference": dict(reference),
        }
    if reference_status != "partial":
        return None, {
            "anchor": anchor_name,
            "status": "native_reference_not_complete_or_partial",
            "anchor_observation_status": reference_status,
        }
    if bounds is None:
        return None, {
            "anchor": anchor_name,
            "status": "partial_reference_needs_leg_seed",
            "anchor_observation_status": "partial",
        }
    try:
        seed_vector = ideal_vector("joint", anchor_name, scale)
        target_vector = ideal_vector(anchor_name, target, scale)
    except (KeyError, TypeError, ValueError, OverflowError):
        seed_vector = target_vector = None
    if seed_vector is None or target_vector is None:
        return None, {
            "anchor": anchor_name,
            "status": "partial_reference_authored_vector_unavailable",
            "anchor_observation_status": "partial",
        }
    seed_origin = (bounds[0] + bounds[1]) / 2.0
    seed_mps = np.asarray(seed_vector.anatomical_mm, dtype=np.float64)
    seed = seed_origin + _mps_to_lps(seed_mps, medial_sign)
    planes = record.get("planes")
    selected_normals: list[np.ndarray] = []
    selected_offsets: list[float] = []
    selected_addresses: list[dict[str, Any]] = []
    ignored_planes: list[dict[str, Any]] = []
    if not isinstance(planes, Mapping):
        planes = {}
        ignored_planes.append(
            {"orientation": "*", "outcome": "plane_addresses_missing"}
        )
    for orientation in ("sagittal", "coronal", "axial"):
        address = planes.get(orientation)
        if not isinstance(address, Mapping):
            ignored_planes.append(
                {"orientation": orientation, "outcome": "not_supplied"}
            )
            continue
        outcome = address.get("outcome")
        if outcome != "selected":
            ignored_planes.append(
                {
                    "orientation": orientation,
                    "outcome": outcome
                    if isinstance(outcome, str)
                    else "outcome_missing",
                    "reason": address.get("reason"),
                    "candidates": address.get("candidates"),
                }
            )
            continue
        try:
            normal = np.asarray(address.get("normal"), dtype=np.float64)
            offset = float(address.get("offset_mm"))
        except (TypeError, ValueError):
            ignored_planes.append(
                {"orientation": orientation, "outcome": "selected_geometry_malformed"}
            )
            continue
        norm = float(np.linalg.norm(normal)) if normal.shape == (3,) else math.nan
        if (
            normal.shape != (3,)
            or not np.all(np.isfinite(normal))
            or not math.isfinite(norm)
            or norm <= 0
            or not math.isfinite(offset)
        ):
            ignored_planes.append(
                {"orientation": orientation, "outcome": "selected_geometry_invalid"}
            )
            continue
        selected_normals.append(normal / norm)
        selected_offsets.append(offset / norm)
        selected_addresses.append(dict(address))
    if not selected_normals:
        return None, {
            "anchor": anchor_name,
            "status": "partial_reference_has_no_selected_native_planes",
            "anchor_observation_status": "partial",
            "ignored_planes": ignored_planes,
        }
    matrix = np.asarray(selected_normals, dtype=np.float64)
    offsets = np.asarray(selected_offsets, dtype=np.float64)
    gram = matrix @ matrix.T
    multipliers = np.linalg.lstsq(gram, offsets - matrix @ seed, rcond=None)[0]
    projected = seed + matrix.T @ multipliers
    residual = matrix @ projected - offsets
    return projected, {
        "anchor": anchor_name,
        "kind": "partial_native_planes_guided_prior",
        "anchor_observation_status": "partial",
        "prior_only": True,
        "reference": dict(reference),
        "leg_frame_seed_lps": seed.tolist(),
        "leg_frame_seed_status": "measured_leg_extents_midpoint_plus_authored_joint_to_anchor_prior",
        "joint_to_anchor_ideal_source": seed_vector.source,
        "anchor_to_target_ideal_source": target_vector.source,
        "selected_native_planes": selected_addresses,
        "ignored_planes": ignored_planes,
        "projection_rank": int(np.linalg.matrix_rank(matrix)),
        "projection_residual_mm": residual.tolist(),
        "projected_anchor_prior_lps": projected.tolist(),
    }


def anatomical_windows(
    series: dict,
    subject: str,
    *,
    leg_bounds_lps: tuple[tuple[float, float, float], tuple[float, float, float]]
    | None,
    anchors: dict,
    knee_side: str | None = None,
    knee_scale_mm: float | None = None,
) -> dict:
    """Propose bounded one-slice windows from anatomy and current-study references.

    Supplied leg bounds are measured current-study extents. Their midpoint is
    only an initial origin prior for an unanchored bone search. With no explicit
    positive knee scale, authored millimetres stay unscaled and are named so.
    """
    if not isinstance(subject, str) or subject not in MAP_OBJECTS:
        return {
            "status": "subject_unknown",
            "windows": [],
            "provenance": {"subject": subject},
        }
    if knee_scale_mm is not None and (
        isinstance(knee_scale_mm, bool)
        or not isinstance(knee_scale_mm, (int, float, np.number))
        or not math.isfinite(float(knee_scale_mm))
        or float(knee_scale_mm) <= 0
    ):
        return {
            "status": "scale_invalid",
            "windows": [],
            "provenance": {"subject": subject, "knee_scale_mm": knee_scale_mm},
        }
    scale = None if knee_scale_mm is None else float(knee_scale_mm)
    side_name, side_hypotheses = _side(knee_side)
    bounds, bounds_status = _leg_bounds(leg_bounds_lps)
    if leg_bounds_lps is not None and bounds is None:
        return {
            "status": "leg_bounds_invalid",
            "windows": [],
            "provenance": {"subject": subject, "leg_bounds_status": bounds_status},
        }
    stack, centres, coverage, geometry_status = _stack_arrays(series)
    if (
        geometry_status != "available"
        or stack is None
        or centres is None
        or coverage is None
    ):
        return {
            "status": geometry_status,
            "windows": [],
            "provenance": {
                "subject": subject,
                "stack_code": getattr(stack, "code", None),
                "leg_bounds_status": bounds_status,
            },
        }
    foreground_status = "not_supplied_geometry_only_prior"
    foreground_count = None
    if "foreground" in series:
        foreground = series.get("foreground")
        if (
            not isinstance(foreground, np.ndarray)
            or foreground.dtype != np.dtype(bool)
            or foreground.shape != coverage.shape
        ):
            return {
                "status": "foreground_mask_unavailable",
                "windows": [],
                "provenance": {
                    "subject": subject,
                    "foreground_mask_status": "malformed_or_shape_mismatched",
                    "foreground_mask_shape": getattr(foreground, "shape", None),
                    "coverage_shape": coverage.shape,
                },
            }
        foreground_status = "provided_current_study_mask"
        foreground_count = int(np.count_nonzero(foreground))
    try:
        span = target_span_mm(subject, scale)
    except (KeyError, ValueError, TypeError, OverflowError):
        span = None
    if span is None:
        return {
            "status": "reference_span_unavailable",
            "windows": [],
            "provenance": {"subject": subject},
        }
    span_array = np.asarray(span, dtype=np.float64)
    if (
        span_array.shape != (3,)
        or not np.all(np.isfinite(span_array))
        or np.any(span_array <= 0)
    ):
        return {
            "status": "reference_span_invalid",
            "windows": [],
            "provenance": {"subject": subject, "target_span_mm": list(span)},
        }

    valid = (
        np.all(np.isfinite(centres), axis=-1) & np.isfinite(coverage) & (coverage > 0)
    )
    if foreground_status == "provided_current_study_mask":
        valid &= foreground
    if bounds is not None:
        valid &= np.all(centres >= bounds[0], axis=-1) & np.all(
            centres <= bounds[1], axis=-1
        )
    if not np.any(valid):
        return {
            "status": "no_finite_current_foreground_tiles",
            "windows": [],
            "provenance": {
                "subject": subject,
                "leg_bounds_status": bounds_status,
                "valid_tile_count": 0,
                "foreground_mask_status": foreground_status,
                "foreground_mask_true_count": foreground_count,
            },
        }

    hypotheses: list[dict[str, Any]] = []
    rejected_anchors: list[dict[str, str]] = []
    if not isinstance(anchors, Mapping):
        anchors = {}
        rejected_anchors.append({"anchor": "*", "reason": "anchors_not_mapping"})
    for anchor_name, record in anchors.items():
        if anchor_name == subject:
            continue
        if not isinstance(anchor_name, str) or not isinstance(record, Mapping):
            rejected_anchors.append(
                {"anchor": str(anchor_name), "reason": "anchor_not_mapping"}
            )
            continue
        try:
            vector = ideal_vector(anchor_name, subject, scale)
        except (KeyError, ValueError, TypeError, OverflowError):
            vector = None
        if vector is None:
            rejected_anchors.append(
                {"anchor": anchor_name, "reason": "ideal_vector_unavailable"}
            )
            continue
        ideal_mps = np.asarray(vector.anatomical_mm, dtype=np.float64)
        if ideal_mps.shape != (3,) or not np.all(np.isfinite(ideal_mps)):
            rejected_anchors.append(
                {"anchor": anchor_name, "reason": "ideal_vector_invalid"}
            )
            continue
        for hypothesis_name, medial_sign in side_hypotheses:
            point, anchor_details = _native_anchor_hypothesis(
                anchor_name,
                record,
                bounds=bounds,
                target=subject,
                scale=scale,
                medial_sign=medial_sign,
            )
            if point is None:
                rejected_anchors.append(
                    {
                        "anchor": anchor_name,
                        "reason": anchor_details.get("status", "anchor_unavailable"),
                        "side_hypothesis": hypothesis_name,
                        "details": anchor_details,
                    }
                )
                continue
            reference = record.get("reference")
            if not isinstance(reference, Mapping):
                reference = record
            raw_precision = reference.get("precision_mm")
            precision = None
            precision_status = "not_supplied"
            if raw_precision is not None:
                try:
                    precision_array = np.asarray(raw_precision, dtype=np.float64)
                except (TypeError, ValueError):
                    precision_array = np.asarray([], dtype=np.float64)
                if (
                    precision_array.shape == (3,)
                    and np.all(np.isfinite(precision_array))
                    and np.all(precision_array >= 0)
                ):
                    precision = precision_array.tolist()
                    precision_status = "provided"
                else:
                    precision_status = "invalid_retained_as_unknown"
            hypotheses.append(
                {
                    **anchor_details,
                    "kind": (
                        "partial_native_planes_guided_prior"
                        if anchor_details.get("kind")
                        == "partial_native_planes_guided_prior"
                        else "current_anchor_relative_prior"
                    ),
                    "anchor": anchor_name,
                    "anchor_point_lps": point.tolist(),
                    "anchor_precision_mm": precision,
                    "anchor_precision_status": precision_status,
                    "ideal_vector_mps_mm": ideal_mps.tolist(),
                    "ideal_source": vector.source,
                    "knee_side_hypothesis": hypothesis_name,
                    "medial_sign": medial_sign,
                    "expected_point_lps": (
                        point + _mps_to_lps(ideal_mps, medial_sign)
                    ).tolist(),
                }
            )

    used_leg_frame_prior = False
    if not hypotheses and subject in _INITIAL_BONES:
        if bounds is None:
            return {
                "status": "leg_frame_prior_unavailable",
                "windows": [],
                "provenance": {
                    "subject": subject,
                    "leg_bounds_status": bounds_status,
                    "rejected_anchors": rejected_anchors,
                },
            }
        try:
            vector = ideal_vector("joint", subject, scale)
        except (KeyError, ValueError, TypeError, OverflowError):
            vector = None
        if vector is None:
            return {
                "status": "reference_vector_unavailable",
                "windows": [],
                "provenance": {"subject": subject},
            }
        midpoint = (bounds[0] + bounds[1]) / 2.0
        ideal_mps = np.asarray(vector.anatomical_mm, dtype=np.float64)
        for hypothesis_name, medial_sign in side_hypotheses:
            hypotheses.append(
                {
                    "kind": "leg_frame_prior",
                    "origin_lps": midpoint.tolist(),
                    "origin_status": "measured_leg_extents_midpoint_used_only_as_initial_prior",
                    "anchor": "authored_joint_site",
                    "ideal_vector_mps_mm": ideal_mps.tolist(),
                    "ideal_source": vector.source,
                    "knee_side_hypothesis": hypothesis_name,
                    "medial_sign": medial_sign,
                    "expected_point_lps": (
                        midpoint + _mps_to_lps(ideal_mps, medial_sign)
                    ).tolist(),
                }
            )
        used_leg_frame_prior = True

    if not hypotheses:
        return {
            "status": "relative_reference_unavailable",
            "windows": [],
            "provenance": {
                "subject": subject,
                "leg_bounds_status": bounds_status,
                "rejected_anchors": rejected_anchors,
                "reason": "no_applicable_native_anchor_or_initial_bone_seed",
            },
        }

    windows_to_sources: dict[
        tuple[int, int, int, int, int, int], list[dict[str, Any]]
    ] = defaultdict(list)
    hypothesis_records = []
    placement_failures: dict[str, int] = defaultdict(int)
    for hypothesis_index, hypothesis in enumerate(hypotheses):
        expected = np.asarray(hypothesis["expected_point_lps"], dtype=np.float64)
        hypothesis_windows: set[tuple[int, int, int, int, int, int]] = set()
        samples = [(expected, [0.0, 0.0, 0.0], "centre")]
        for anatomical_axis in range(3):
            for direction in (-1.0, 1.0):
                offset = np.zeros(3, dtype=np.float64)
                offset[anatomical_axis] = direction * span_array[anatomical_axis] / 2.0
                samples.append(
                    (
                        expected + _mps_to_lps(offset, hypothesis["medial_sign"]),
                        offset.tolist(),
                        f"axis_{anatomical_axis}_{'positive' if direction > 0 else 'negative'}_half_span",
                    )
                )
        for predicted, offset_mps, sample_name in samples:
            nearest = _nearest_centres(predicted, centres, valid)
            if not nearest:
                placement_failures["no_nearest_foreground_tile"] += 1
                continue
            for z, row, col in nearest:
                row_direction, row_step, row_status = _local_axis(
                    centres[z], row, col, 0
                )
                col_direction, col_step, col_status = _local_axis(
                    centres[z], row, col, 1
                )
                if (
                    row_direction is None
                    or col_direction is None
                    or row_step is None
                    or col_step is None
                ):
                    placement_failures[
                        row_status if row_direction is None else col_status
                    ] += 1
                    continue
                row_span = float(np.sum(span_array * np.abs(row_direction)))
                col_span = float(np.sum(span_array * np.abs(col_direction)))
                nominal_rows = max(1, math.ceil(row_span / row_step))
                nominal_cols = max(1, math.ceil(col_span / col_step))
                sizes = (
                    (
                        max(1, nominal_rows - 1),
                        max(1, nominal_cols - 1),
                        "smaller_one_tile",
                    ),
                    (nominal_rows, nominal_cols, "nominal"),
                    (nominal_rows + 1, nominal_cols + 1, "larger_one_tile"),
                )
                for rows, cols, size_name in sizes:
                    address, clipping = _window(
                        z, row, col, rows, cols, centres.shape[:3]
                    )
                    hypothesis_windows.add(address)
                    windows_to_sources[address].append(
                        {
                            "hypothesis_index": hypothesis_index,
                            "sample": sample_name,
                            "offset_mps_mm": offset_mps,
                            "predicted_point_lps": predicted.tolist(),
                            "nearest_tile_index": [z, row, col],
                            "nearest_tile_centre_lps": centres[z, row, col].tolist(),
                            "physical_projected_span_mm": [row_span, col_span],
                            "native_tile_step_mm": [row_step, col_step],
                            "size_hypothesis": size_name,
                            **clipping,
                        }
                    )
        hypothesis_records.append(
            {
                **{
                    key: value
                    for key, value in hypothesis.items()
                    if key != "medial_sign"
                },
                "candidate_window_count": len(hypothesis_windows),
                "candidate_windows": [
                    list(window) for window in sorted(hypothesis_windows)
                ],
            }
        )

    windows = sorted(windows_to_sources)
    for sources in windows_to_sources.values():
        sources.sort(
            key=lambda row: (
                row["hypothesis_index"],
                row["sample"],
                row["size_hypothesis"],
            )
        )
    status = "proposed_unknown_side" if side_name is None else "proposed"
    return {
        "status": status if windows else "no_valid_native_windows",
        "windows": windows,
        "provenance": {
            "schema": "knee.squint-anatomical-windows/v1",
            "subject": subject,
            "reference_kind": "anatomical_prior_not_measurement",
            "target_span_mm": span_array.tolist(),
            "knee_scale_mm": scale,
            "knee_scale_status": "explicit_positive"
            if scale is not None
            else "unscaled_authored_millimetres",
            "knee_scale_basis": "femoral_breadth_mm"
            if scale is not None
            else "unknown_no_scale_application",
            "knee_side": side_name,
            "knee_side_status": "named"
            if side_name is not None
            else "unknown_both_mirrored_hypotheses_retained",
            "leg_bounds_lps": bounds.tolist() if bounds is not None else None,
            "leg_bounds_status": bounds_status,
            "leg_frame_prior_used": used_leg_frame_prior,
            "candidate_count": len(windows),
            "hypothesis_count": len(hypothesis_records),
            "valid_current_tile_count": int(np.count_nonzero(valid)),
            "foreground_mask_status": foreground_status,
            "foreground_mask_true_count": foreground_count,
            "rejected_anchors": rejected_anchors,
            "hypotheses": hypothesis_records,
            "window_sources": [
                {"window": list(window), "sources": windows_to_sources[window]}
                for window in windows
            ],
            "placement_failures": dict(sorted(placement_failures.items())),
            "identity_assertion": None,
        },
    }
