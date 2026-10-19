"""Small native-space measurements shared by anatomically targeted readers."""

from __future__ import annotations

from itertools import product
from typing import Any

import numpy as np
from scipy import ndimage as ndi

from knee.collapse.physical import PlaneFrame
from knee.objects import assignments


def _empty_window(status: str) -> dict[str, Any]:
    return {
        "status": status,
        "window_rc_exclusive": None,
        "projected_half_span_pixels_rc": None,
        "target_bbox_rc_exclusive": None,
        "source_out_of_bounds_pixels": 0,
        "window_clipped_to_image": None,
    }


def source_window(
    source_rc: np.ndarray,
    span_lps_mm: tuple[float, float, float],
    frame: PlaneFrame,
    shape: tuple[int, int],
) -> dict[str, Any]:
    """Bound rounded source pixels plus symmetric padding from a physical search-box size.

    The full span is projected as centered padding around the source-pixel centroid; it does
    not assert that this centroid is the object's physical center. A source at an object's
    corner needs twice the point-to-point object extent as the full span.
    """
    if (
        not isinstance(source_rc, np.ndarray)
        or source_rc.ndim != 2
        or source_rc.shape[1:] != (2,)
    ):
        return _empty_window("malformed_source_shape")
    if source_rc.dtype.kind not in "iuf":
        return _empty_window("malformed_source_dtype")
    if not np.isfinite(source_rc).all():
        return _empty_window("nonfinite_source")
    if source_rc.shape[0] == 0:
        return _empty_window("empty_source")
    if not isinstance(shape, tuple) or len(shape) != 2:
        return _empty_window("malformed_image_shape")
    if any(
        isinstance(size, (bool, np.bool_)) or not isinstance(size, (int, np.integer))
        for size in shape
    ):
        return _empty_window("malformed_image_shape")
    if any(size <= 0 for size in shape):
        return _empty_window("empty_image_shape")
    try:
        span = np.asarray(span_lps_mm, dtype=np.float64)
    except (TypeError, ValueError):
        return _empty_window("malformed_span")
    if span.shape != (3,):
        return _empty_window("malformed_span")
    if not np.isfinite(span).all():
        return _empty_window("nonfinite_span")
    if np.any(span <= 0):
        return _empty_window("nonpositive_span")

    outside = (
        (source_rc[:, 0] < 0)
        | (source_rc[:, 0] > shape[0] - 1)
        | (source_rc[:, 1] < 0)
        | (source_rc[:, 1] > shape[1] - 1)
    )
    if outside.any():
        result = _empty_window("source_out_of_bounds")
        result["source_out_of_bounds_pixels"] = int(outside.sum())
        return result
    rounded = np.rint(source_rc).astype(np.int64)
    origin = np.asarray(frame.origin_lps, dtype=np.float64)
    basis = np.asarray(frame.basis_lps, dtype=np.float64)
    if origin.shape != (3,):
        return _empty_window("invalid_frame_origin")
    if basis.shape != (3, 2):
        return _empty_window("invalid_frame_basis")
    if not np.isfinite(origin).all() or not np.isfinite(basis).all():
        return _empty_window("nonfinite_frame_geometry")
    if np.linalg.matrix_rank(basis) != 2:
        return _empty_window("degenerate_frame_basis")
    try:
        center_rc = rounded.astype(np.float64).mean(axis=0, keepdims=True)
        center_lps = np.asarray(frame.to_patient(center_rc), dtype=np.float64)
        half = span / 2.0
        offsets = np.asarray(list(product(*[(-v, v) for v in half])), dtype=np.float64)
        corners_lps = center_lps + offsets
        projected = np.asarray(frame.to_native(corners_lps), dtype=np.float64)
        projected_center = np.asarray(frame.to_native(center_lps), dtype=np.float64)
    except (AttributeError, TypeError, ValueError, np.linalg.LinAlgError):
        return _empty_window("invalid_frame")
    if (
        center_lps.shape != (1, 3)
        or projected.shape != (8, 2)
        or projected_center.shape != (1, 2)
        or not np.isfinite(center_lps).all()
        or not np.isfinite(projected).all()
        or not np.isfinite(projected_center).all()
    ):
        return _empty_window("invalid_frame_geometry")

    radius_rc = np.max(np.abs(projected - projected_center[0]), axis=0)
    if not np.isfinite(radius_rc).all():
        return _empty_window("invalid_projected_span")
    r0_target, c0_target = rounded.min(axis=0)
    r1_target, c1_target = rounded.max(axis=0) + 1
    padding = np.ceil(radius_rc).astype(np.int64)
    r0 = max(0, int(r0_target) - int(padding[0]))
    r1 = min(shape[0], int(r1_target) + int(padding[0]))
    c0 = max(0, int(c0_target) - int(padding[1]))
    c1 = min(shape[1], int(c1_target) + int(padding[1]))
    clipped = r0 == 0 or c0 == 0 or r1 == shape[0] or c1 == shape[1]
    return {
        "status": "window_clipped_to_image" if clipped else "present",
        "window_rc_exclusive": [r0, r1, c0, c1],
        "projected_half_span_pixels_rc": [float(v) for v in radius_rc],
        "target_bbox_rc_exclusive": [
            int(r0_target),
            int(r1_target),
            int(c0_target),
            int(c1_target),
        ],
        "source_out_of_bounds_pixels": 0,
        "window_clipped_to_image": bool(clipped),
    }


def enclosed_components_at_source(
    raw: np.ndarray,
    available: np.ndarray,
    target: np.ndarray,
    frame: PlaneFrame,
) -> dict[str, Any]:
    """Measure positive enclosed-dark components and their native target distances.

    This keeps the existing enclosed-darkness measurement and reports every FOUR-connected
    positive component. It does not open, select, or assign anatomy to any component.
    """
    arrays: dict[str, Any] = {
        "availability_input": None,
        "target_input": None,
        "effective_availability": None,
        "depth_input": None,
        "enclosed_depth": None,
        "positive_enclosure": None,
        "labels": None,
        "distance_to_target_mm": None,
        "contacted_component_mask": None,
        "unavailable_boundary": None,
    }
    stats: dict[str, Any] = {
        "neutral_minimum": None,
        "available_pixels": None,
        "unavailable_pixels": None,
        "target_pixels": None,
        "available_target_pixels": None,
        "positive_enclosure_pixels": None,
        "component_count": None,
        "contacted_component_count": None,
        "contacted_component_ids": [],
        "contacted_component_sizes_pixels": [],
        "components": [],
        "crop_edge_pixels": None,
        "partial_reading": None,
        "enclosure_status": "unmeasured",
    }

    def outcome(status: str, **values: Any) -> dict[str, Any]:
        return {"status": status, **arrays, **stats, **values}

    if not isinstance(raw, np.ndarray) or raw.ndim != 2:
        return outcome("malformed_raw_shape")
    if raw.dtype.kind not in "iuf":
        return outcome("malformed_raw_dtype")
    if raw.size == 0:
        return outcome("empty_raw")
    if not isinstance(available, np.ndarray) or available.shape != raw.shape:
        return outcome("malformed_availability_shape")
    if available.dtype.kind != "b":
        return outcome("malformed_availability_dtype")
    if not isinstance(target, np.ndarray) or target.shape != raw.shape:
        return outcome("malformed_target_shape")
    if target.dtype.kind != "b":
        return outcome("malformed_target_dtype")
    if not isinstance(frame, PlaneFrame):
        return outcome("invalid_frame")
    try:
        spacing = np.asarray(frame.spacing_rc, dtype=np.float64)
    except (TypeError, ValueError):
        return outcome("invalid_spacing")
    if spacing.shape != (2,) or not np.isfinite(spacing).all() or np.any(spacing <= 0):
        return outcome("invalid_spacing")

    arrays["availability_input"] = available
    arrays["target_input"] = target
    effective = available & np.isfinite(raw)
    target_pixels = int(target.sum())
    available_pixels = int(effective.sum())
    available_target = target & effective
    available_target_pixels = int(available_target.sum())
    partial = not bool(effective.all())
    arrays["effective_availability"] = effective
    stats.update(
        available_pixels=available_pixels,
        unavailable_pixels=int(raw.size - available_pixels),
        target_pixels=target_pixels,
        available_target_pixels=available_target_pixels,
        partial_reading=partial,
    )
    if target_pixels == 0:
        return outcome("target_missing")
    if available_pixels == 0:
        return outcome("no_available_pixels")
    if available_target_pixels == 0:
        return outcome("target_unavailable")

    neutral = float(np.min(raw[effective]))
    depth_input = np.where(effective, raw, neutral).astype(np.float64)
    enclosed_depth = np.asarray(
        assignments.enclosed_darkness(depth_input), dtype=np.float64
    )
    positive = (enclosed_depth > 0.0) & effective
    labels, component_count = ndi.label(positive, structure=assignments.FOUR_NEIGHBOURS)
    distance_to_target = ndi.distance_transform_edt(~available_target, sampling=spacing)
    component_ids = np.arange(1, int(component_count) + 1, dtype=np.int32)
    component_sizes = np.bincount(labels.ravel(), minlength=int(component_count) + 1)
    crop_edge = np.zeros(raw.shape, dtype=bool)
    crop_edge[[0, -1], :] = True
    crop_edge[:, [0, -1]] = True
    unknown_boundary = (
        ndi.binary_dilation(~effective, structure=assignments.FOUR_NEIGHBOURS)
        & effective
    )
    if len(component_ids):
        minimum_distances = np.asarray(
            ndi.minimum(distance_to_target, labels, index=component_ids),
            dtype=np.float64,
        )
        edge_counts = np.asarray(
            ndi.sum(crop_edge, labels, index=component_ids), dtype=np.int64
        )
        unknown_boundary_counts = np.asarray(
            ndi.sum(unknown_boundary, labels, index=component_ids), dtype=np.int64
        )
    else:
        minimum_distances = np.empty(0, dtype=np.float64)
        edge_counts = np.empty(0, dtype=np.int64)
        unknown_boundary_counts = np.empty(0, dtype=np.int64)
    contacted_components = minimum_distances <= assignments.SHELL_MM
    contacted_ids = component_ids[contacted_components].astype(int).tolist()
    rows = [
        {
            "label": int(label),
            "pixels": int(component_sizes[label]),
            "minimum_target_distance_mm": float(minimum_distance),
            "within_existing_contact_shell": bool(contacted),
            "crop_edge_pixels": int(edge_pixels),
            "touches_crop_edge": bool(edge_pixels),
            "unknown_boundary_pixels": int(unknown_pixels),
            "touches_unavailable_boundary": bool(unknown_pixels),
        }
        for label, minimum_distance, edge_pixels, unknown_pixels, contacted in zip(
            component_ids,
            minimum_distances,
            edge_counts,
            unknown_boundary_counts,
            contacted_components,
            strict=True,
        )
    ]
    contacted_mask = np.isin(labels, contacted_ids)
    arrays.update(
        depth_input=depth_input,
        enclosed_depth=enclosed_depth,
        positive_enclosure=positive,
        labels=labels.astype(np.int32, copy=False),
        distance_to_target_mm=distance_to_target,
        contacted_component_mask=contacted_mask,
        unavailable_boundary=unknown_boundary,
    )
    stats.update(
        neutral_minimum=neutral,
        positive_enclosure_pixels=int(positive.sum()),
        component_count=int(component_count),
        contacted_component_count=len(contacted_ids),
        contacted_component_ids=contacted_ids,
        contacted_component_sizes_pixels=[
            int(component_sizes[label]) for label in contacted_ids
        ],
        components=rows,
        crop_edge_pixels=int(crop_edge.sum()),
        enclosure_status="empty" if component_count == 0 else "present",
    )
    return outcome("partial_reading" if partial else "complete")


def enclosed_body_at_sources(
    raw: np.ndarray,
    available: np.ndarray,
    target: np.ndarray,
    frame: PlaneFrame,
    *,
    thickness_mm: float,
    other_target: np.ndarray | None = None,
) -> dict[str, Any]:
    """Measure whole opened components reaching one or both native source regions."""
    arrays = {
        "availability": None,
        "depth_input": None,
        "enclosed_depth": None,
        "positive_enclosure": None,
        "opened": None,
        "labels": None,
        "distance_to_target": None,
        "contacted_components": None,
        "selected": None,
        "distance_to_other_target": None,
        "other_contacted_components": None,
        "both_contacted_components": None,
    }
    counts = {
        "neutral_minimum": None,
        "available_pixels": None,
        "unavailable_pixels": None,
        "target_pixels": None,
        "available_target_pixels": None,
        "positive_enclosure_pixels": None,
        "opened_pixels": None,
        "component_count": None,
        "contacted_component_count": None,
        "contacted_components_pixels": [],
        "largest_component_labels": [],
        "largest_contacted_pixels": 0,
        "selected_pixels": 0,
        "crop_edge_pixels": None,
        "selected_crop_edge_pixels": 0,
        "selected_touches_crop_edge": False,
        "other_target_pixels": None,
        "available_other_target_pixels": None,
        "other_contacted_component_count": None,
        "target_contacted_component_count": None,
        "both_contacted_component_count": None,
        "target_contacted_component_labels": None,
        "other_target_contacted_component_labels": None,
        "both_contacted_component_labels": None,
    }
    if not isinstance(raw, np.ndarray) or raw.ndim != 2:
        return {
            "status": "malformed_raw_shape",
            "selection_status": "unmeasured",
            **arrays,
            **counts,
        }
    if raw.dtype.kind not in "iuf":
        return {
            "status": "malformed_raw_dtype",
            "selection_status": "unmeasured",
            **arrays,
            **counts,
        }
    if raw.size == 0:
        return {
            "status": "empty_raw",
            "selection_status": "unmeasured",
            **arrays,
            **counts,
        }
    if (
        not isinstance(available, np.ndarray)
        or available.shape != raw.shape
        or available.ndim != 2
    ):
        return {
            "status": "malformed_availability_shape",
            "selection_status": "unmeasured",
            **arrays,
            **counts,
        }
    if available.dtype.kind != "b":
        return {
            "status": "malformed_availability_dtype",
            "selection_status": "unmeasured",
            **arrays,
            **counts,
        }
    if (
        not isinstance(target, np.ndarray)
        or target.shape != raw.shape
        or target.ndim != 2
    ):
        return {
            "status": "malformed_target_shape",
            "selection_status": "unmeasured",
            **arrays,
            **counts,
        }
    if target.dtype.kind != "b":
        return {
            "status": "malformed_target_dtype",
            "selection_status": "unmeasured",
            **arrays,
            **counts,
        }
    if other_target is not None:
        if (
            not isinstance(other_target, np.ndarray)
            or other_target.shape != raw.shape
            or other_target.ndim != 2
        ):
            return {
                "status": "malformed_other_target_shape",
                "selection_status": "unmeasured",
                **arrays,
                **counts,
            }
        if other_target.dtype.kind != "b":
            return {
                "status": "malformed_other_target_dtype",
                "selection_status": "unmeasured",
                **arrays,
                **counts,
            }
    if not isinstance(frame, PlaneFrame):
        return {
            "status": "invalid_frame",
            "selection_status": "unmeasured",
            **arrays,
            **counts,
        }
    try:
        spacing = np.asarray(frame.spacing_rc, dtype=np.float64)
    except (TypeError, ValueError):
        return {
            "status": "invalid_spacing",
            "selection_status": "unmeasured",
            **arrays,
            **counts,
        }
    if spacing.shape != (2,) or not np.isfinite(spacing).all() or np.any(spacing <= 0):
        return {
            "status": "invalid_spacing",
            "selection_status": "unmeasured",
            **arrays,
            **counts,
        }

    if isinstance(thickness_mm, (bool, np.bool_)):
        return {
            "status": "invalid_thickness",
            "selection_status": "unmeasured",
            **arrays,
            **counts,
        }
    try:
        thickness = float(thickness_mm)
    except (TypeError, ValueError, OverflowError):
        return {
            "status": "invalid_thickness",
            "selection_status": "unmeasured",
            **arrays,
            **counts,
        }
    if not np.isfinite(thickness) or thickness <= 0:
        return {
            "status": "invalid_thickness",
            "selection_status": "unmeasured",
            **arrays,
            **counts,
        }

    target_pixels = int(target.sum())
    if target_pixels == 0:
        return {
            "status": "target_missing",
            "selection_status": "unmeasured",
            **arrays,
            **counts,
        }
    effective = available & np.isfinite(raw)
    available_pixels = int(effective.sum())
    if available_pixels == 0:
        return {
            "status": "no_available_pixels",
            "selection_status": "unmeasured",
            **arrays,
            **counts,
        }
    available_target = target & effective
    available_target_pixels = int(available_target.sum())
    if available_target_pixels == 0:
        return {
            "status": "target_unavailable",
            "selection_status": "unmeasured",
            **arrays,
            **counts,
            "available_pixels": available_pixels,
            "unavailable_pixels": int(raw.size - available_pixels),
            "target_pixels": target_pixels,
            "available_target_pixels": 0,
        }
    if other_target is not None:
        other_target_pixels = int(other_target.sum())
        if other_target_pixels == 0:
            return {
                "status": "other_target_missing",
                "selection_status": "unmeasured",
                **arrays,
                **counts,
                "available_pixels": available_pixels,
                "unavailable_pixels": int(raw.size - available_pixels),
                "target_pixels": target_pixels,
                "available_target_pixels": available_target_pixels,
                "other_target_pixels": 0,
                "available_other_target_pixels": 0,
            }
        available_other_target = other_target & effective
        available_other_target_pixels = int(available_other_target.sum())
        if available_other_target_pixels == 0:
            return {
                "status": "other_target_unavailable",
                "selection_status": "unmeasured",
                **arrays,
                **counts,
                "available_pixels": available_pixels,
                "unavailable_pixels": int(raw.size - available_pixels),
                "target_pixels": target_pixels,
                "available_target_pixels": available_target_pixels,
                "other_target_pixels": other_target_pixels,
                "available_other_target_pixels": 0,
            }
    else:
        other_target_pixels = None
        available_other_target = None
        available_other_target_pixels = None

    neutral = float(np.min(raw[effective]))
    depth_input = np.where(effective, raw, neutral).astype(np.float64)
    enclosed_depth = np.asarray(
        assignments.enclosed_darkness(depth_input), dtype=np.float64
    )
    positive = (enclosed_depth > 0.0) & effective
    opened = assignments.thick_parts(
        positive,
        spacing,
        thickness,
    )
    labels, component_count = ndi.label(opened, structure=assignments.FOUR_NEIGHBOURS)
    distance_to_target = ndi.distance_transform_edt(~available_target, sampling=spacing)
    target_contacted_ids = np.unique(
        labels[(distance_to_target <= assignments.SHELL_MM) & effective]
    )
    target_contacted_ids = target_contacted_ids[target_contacted_ids > 0]
    other_distance = None
    other_contacted_ids = None
    both_contacted_ids = None
    if available_other_target is None:
        contacted_ids = target_contacted_ids
    else:
        other_distance = ndi.distance_transform_edt(
            ~available_other_target, sampling=spacing
        )
        other_contacted_ids = np.unique(
            labels[(other_distance <= assignments.SHELL_MM) & effective]
        )
        other_contacted_ids = other_contacted_ids[other_contacted_ids > 0]
        both_contacted_ids = np.intersect1d(
            target_contacted_ids, other_contacted_ids, assume_unique=True
        )
        contacted_ids = both_contacted_ids
    component_sizes = np.bincount(labels.ravel(), minlength=int(component_count) + 1)
    contacted_sizes = {
        int(label): int(component_sizes[label]) for label in contacted_ids
    }
    largest = max(contacted_sizes.values(), default=0)
    winners = sorted(
        label
        for label, size in contacted_sizes.items()
        if size == largest and largest > 0
    )
    contacted = np.isin(labels, contacted_ids)
    other_contacted = (
        None if other_contacted_ids is None else np.isin(labels, other_contacted_ids)
    )
    both_contacted = None if both_contacted_ids is None else contacted
    selected = (
        labels == winners[0] if len(winners) == 1 else np.zeros(raw.shape, dtype=bool)
    )
    partial = not bool(effective.all())
    selection_status = (
        "identified"
        if len(winners) == 1
        else "tied_largest_components"
        if len(winners) > 1
        else "measured_empty"
    )
    status = "partial_reading" if partial else selection_status
    crop_edge = np.zeros(raw.shape, dtype=bool)
    crop_edge[[0, -1], :] = True
    crop_edge[:, [0, -1]] = True
    edge_pixels = int(crop_edge.sum())
    selected_edge_pixels = int(np.count_nonzero(selected & crop_edge))
    return {
        "status": status,
        "selection_status": selection_status,
        "availability": effective,
        "depth_input": depth_input,
        "enclosed_depth": enclosed_depth,
        "positive_enclosure": positive,
        "opened": opened,
        "labels": labels.astype(np.int32, copy=False),
        "distance_to_target": distance_to_target,
        "contacted_components": contacted,
        "selected": selected,
        "distance_to_other_target": other_distance,
        "other_contacted_components": other_contacted,
        "both_contacted_components": both_contacted,
        "neutral_minimum": neutral,
        "available_pixels": available_pixels,
        "unavailable_pixels": int(raw.size - available_pixels),
        "target_pixels": target_pixels,
        "available_target_pixels": available_target_pixels,
        "positive_enclosure_pixels": int(positive.sum()),
        "opened_pixels": int(opened.sum()),
        "component_count": int(component_count),
        "contacted_component_count": len(contacted_ids),
        "contacted_components_pixels": [
            {"label": label, "pixels": size}
            for label, size in sorted(contacted_sizes.items())
        ],
        "largest_component_labels": winners,
        "largest_contacted_pixels": largest,
        "selected_pixels": int(selected.sum()),
        "crop_edge_pixels": edge_pixels,
        "selected_crop_edge_pixels": selected_edge_pixels,
        "selected_touches_crop_edge": bool(selected_edge_pixels),
        "other_target_pixels": other_target_pixels,
        "available_other_target_pixels": available_other_target_pixels,
        "other_contacted_component_count": (
            None if other_contacted_ids is None else len(other_contacted_ids)
        ),
        "target_contacted_component_count": (
            None if other_contacted_ids is None else len(target_contacted_ids)
        ),
        "both_contacted_component_count": (
            None if both_contacted_ids is None else len(both_contacted_ids)
        ),
        "target_contacted_component_labels": (
            None
            if other_contacted_ids is None
            else target_contacted_ids.astype(int).tolist()
        ),
        "other_target_contacted_component_labels": (
            None
            if other_contacted_ids is None
            else other_contacted_ids.astype(int).tolist()
        ),
        "both_contacted_component_labels": (
            None
            if both_contacted_ids is None
            else both_contacted_ids.astype(int).tolist()
        ),
    }
