"""Native white-body selection beside the known patellar retinacular locations."""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import ndimage as ndi

from knee.objects.assignments import MENISCUS_THICKNESS_MM, thick_parts


def white_components(
    white: np.ndarray, spacing_rc: np.ndarray
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    """Label whole connected white bodies once and retain each existing 2 mm core reading."""
    mask = np.asarray(white)
    spacing = np.asarray(spacing_rc, dtype=float)
    if mask.ndim != 2 or mask.dtype != np.dtype(bool):
        raise ValueError("white must be a two-dimensional boolean mask")
    if spacing.shape != (2,) or not np.isfinite(spacing).all() or np.any(spacing <= 0):
        raise ValueError("spacing_rc must contain two finite positive values")
    labels, count = ndi.label(mask, structure=np.ones((3, 3), dtype=bool))
    components: list[dict[str, Any]] = []
    for component_id in range(1, int(count) + 1):
        rc = np.argwhere(labels == component_id).astype(float)
        core = thick_parts(labels == component_id, spacing, MENISCUS_THICKNESS_MM)
        components.append(
            {
                "component_id": component_id,
                "count": len(rc),
                "core_count": int(np.count_nonzero(core)),
                "core": core,
                "rc": rc,
            }
        )
    return labels.astype(np.int32, copy=False), components


def closest_white_body(
    labels: np.ndarray,
    components: list[dict[str, Any]],
    source_rc: np.ndarray,
    frame: Any,
    outward_mm: np.ndarray,
    *,
    require_inward: bool,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Select the unique nearest whole 2 mm-core white body at native source locations."""
    label_array = np.asarray(labels)
    source = np.asarray(source_rc)
    outward = np.asarray(outward_mm)
    empty = np.zeros(label_array.shape, dtype=bool)
    if label_array.ndim != 2 or source.ndim != 2 or source.shape[1:] != (2,):
        raise ValueError("labels and source_rc must be 2D labels and Nx2 coordinates")
    if outward.shape != label_array.shape:
        raise ValueError("outward_mm must match labels")
    source = np.unique(source.astype(np.int64), axis=0)
    if not len(source):
        return (
            empty,
            empty.copy(),
            {"status": "source_target_unavailable", "components": []},
        )
    if (
        np.any(source[:, 0] < 0)
        or np.any(source[:, 0] >= label_array.shape[0])
        or np.any(source[:, 1] < 0)
        or np.any(source[:, 1] >= label_array.shape[1])
    ):
        return (
            empty,
            empty.copy(),
            {"status": "source_target_outside_frame", "components": []},
        )
    source_lps = np.asarray(frame.to_patient(source.astype(float)), dtype=float)
    if source_lps.shape != (len(source), 3) or not np.isfinite(source_lps).all():
        return (
            empty,
            empty.copy(),
            {"status": "source_projection_unavailable", "components": []},
        )
    source_values = outward[source[:, 0], source[:, 1]]
    if not np.isfinite(source_values).all():
        return (
            empty,
            empty.copy(),
            {"status": "source_position_unavailable", "components": []},
        )
    source_outward = float(np.median(source_values))
    spacing = np.asarray(frame.spacing_rc, dtype=float)
    if spacing.shape != (2,) or not np.isfinite(spacing).all() or np.any(spacing <= 0):
        return (
            empty,
            empty.copy(),
            {"status": "native_spacing_unavailable", "components": []},
        )
    source_target = np.zeros(label_array.shape, dtype=bool)
    source_target[source[:, 0], source[:, 1]] = True
    distance_mm = ndi.distance_transform_edt(~source_target, sampling=spacing)
    candidates: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    for component in components:
        rc = np.asarray(component["rc"], dtype=float)
        if not len(rc) or not np.isfinite(rc).all():
            continue
        rc_integer = rc.astype(int)
        distances = distance_mm[rc_integer[:, 0], rc_integer[:, 1]]
        component_outward = outward[rc_integer[:, 0], rc_integer[:, 1]]
        median_outward = float(np.median(component_outward))
        passes_order = not require_inward or median_outward <= source_outward
        row = {
            "component_id": int(component["component_id"]),
            "count": int(component["count"]),
            "two_mm_core_count": int(component["core_count"]),
            "nearest_source_distance_mm": float(np.min(distances)),
            "median_source_distance_mm": float(np.median(distances)),
            "median_outward_mm": median_outward,
            "source_median_outward_mm": source_outward,
            "passes_inward_order": bool(passes_order),
            "eligible": bool(component["core_count"] and passes_order),
        }
        details.append(row)
        if row["eligible"]:
            candidates.append(row)
    if not candidates:
        status = (
            "no_two_mm_body_in_anatomical_order" if details else "no_native_white_body"
        )
        return empty, empty.copy(), {"status": status, "components": details}
    nearest = min(row["nearest_source_distance_mm"] for row in candidates)
    winners = [
        row for row in candidates if row["nearest_source_distance_mm"] == nearest
    ]
    if len(winners) != 1:
        return (
            empty,
            empty.copy(),
            {
                "status": "tied_nearest_native_white_bodies",
                "components": details,
            },
        )
    winner = winners[0]
    body = label_array == winner["component_id"]
    selected_component = next(
        item for item in components if item["component_id"] == winner["component_id"]
    )
    core = np.asarray(selected_component["core"], dtype=bool)
    return (
        body,
        core,
        {
            "status": "selected_nearest_native_white_body",
            "selected_component_id": int(winner["component_id"]),
            "selected_count": int(winner["count"]),
            "selected_two_mm_core_count": int(winner["two_mm_core_count"]),
            "nearest_source_distance_mm": float(winner["nearest_source_distance_mm"]),
            "components": details,
        },
    )
