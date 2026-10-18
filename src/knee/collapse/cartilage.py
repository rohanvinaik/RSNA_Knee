"""Companion descriptions derived from existing native cartilage readings."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

import numpy as np
from scipy import ndimage as ndi

from knee.collapse.observations import Observation
from knee.objects.assignments import (
    CARTILAGE_BRIGHTER,
    CARTILAGE_MM,
    FLUID_BRIGHTER,
    OBJECT_CODES,
    SHELL_MM,
    unique_largest,
)

SAGITTAL_FS = ("Sagittal", "1", "1")
CARTILAGE_READING = "a3_joint_plane_reading"
CARTILAGE_NOTE = (
    "The same existing bone-facing cartilage rule gives an independent sagittal description; "
    "this is not a projection and does not claim full-surface precision."
)


def femoral_cartilage_on_plane(
    raw: np.ndarray,
    available: np.ndarray,
    femur_core: np.ndarray,
    positive_enclosure: np.ndarray,
    sagittal_target: np.ndarray,
    coronal_target: np.ndarray,
    marrow_median: float,
    spacing_rc: tuple[float, float] | np.ndarray,
    distance: Callable[[np.ndarray, np.ndarray], np.ndarray] | None = None,
) -> dict[str, Any]:
    """Measure a whole femoral surface candidate from one native axial frame.

    The existing coarse femur core selects one whole native positive enclosed-darkness component.
    Its hole-filled complement is a separate enclosure reading. The candidate uses the existing
    cartilage brightness and reach relations, bounded above by the same-core fluid relation, and
    remains whole when it touches both independent source-location targets.
    """
    plane = np.asarray(raw)
    valid = np.asarray(available)
    core = np.asarray(femur_core)
    enclosure = np.asarray(positive_enclosure)
    sagittal = np.asarray(sagittal_target)
    coronal = np.asarray(coronal_target)
    inputs = (valid, core, enclosure, sagittal, coronal)
    empty = (
        np.zeros(plane.shape, dtype=bool)
        if plane.ndim == 2
        else np.zeros((0, 0), dtype=bool)
    )
    if plane.ndim != 2 or plane.size == 0 or plane.dtype.kind not in "iuf":
        return {"status": "native_plane_unavailable", "selected": empty}
    if any(item.shape != plane.shape or item.dtype.kind != "b" for item in inputs):
        return {"status": "native_context_shape_unavailable", "selected": empty}
    try:
        spacing = np.asarray(spacing_rc, dtype=float)
        marrow = float(marrow_median)
    except (TypeError, ValueError, OverflowError):
        return {"status": "native_measurement_unavailable", "selected": empty}
    if (
        spacing.shape != (2,)
        or not np.isfinite(spacing).all()
        or np.any(spacing <= 0)
        or not np.isfinite(marrow)
        or marrow <= 0
    ):
        return {"status": "native_measurement_unavailable", "selected": empty}
    finite_valid = valid & np.isfinite(plane)
    if np.any(valid & ~np.isfinite(plane)):
        return {"status": "native_values_unavailable", "selected": empty}
    if not core.any():
        return {"status": "femur_core_empty", "selected": empty}
    if np.any(core & ~finite_valid):
        return {"status": "femur_core_incomplete", "selected": empty}
    if not sagittal.any() or not coronal.any():
        return {"status": "source_target_unavailable", "selected": empty}

    positive = enclosure & finite_valid
    labels, _ = ndi.label(positive)
    touched = np.unique(labels[core])
    touched = touched[touched > 0]
    sizes = np.bincount(labels.ravel())
    touched_sizes = sizes[touched]
    enclosure_index = unique_largest(touched_sizes)
    base: dict[str, Any] = {
        "positive_enclosure": positive,
        "enclosure_labels": labels.astype(np.int32, copy=False),
        "touched_labels": touched.astype(np.int32, copy=False),
        "touched_sizes": touched_sizes.astype(np.int64, copy=False),
        "selected_enclosure": empty.copy(),
        "filled_enclosure": empty.copy(),
        "fill_difference": empty.copy(),
        "candidate": empty.copy(),
        "candidate_labels": np.zeros(plane.shape, dtype=np.int32),
        "sagittal_contact_distance_mm": np.full(plane.shape, np.inf),
        "coronal_contact_distance_mm": np.full(plane.shape, np.inf),
        "contact_labels": np.empty(0, dtype=np.int32),
        "contact_sizes": np.empty(0, dtype=np.int64),
        "selected": empty.copy(),
    }
    if not len(touched):
        return {**base, "status": "no_positive_enclosure_touched_by_core"}
    if enclosure_index is None:
        return {**base, "status": "tied_largest_touched_enclosures"}
    selected_enclosure = labels == int(touched[enclosure_index])
    filled = ndi.binary_fill_holes(selected_enclosure)
    fill_difference = filled & ~selected_enclosure
    if np.any(ndi.binary_dilation(selected_enclosure) & ~finite_valid) or np.any(
        fill_difference & ~finite_valid
    ):
        return {
            **base,
            "selected_enclosure": selected_enclosure,
            "filled_enclosure": filled,
            "fill_difference": fill_difference,
            "status": "enclosure_neighbors_unavailable",
        }

    def measure_distance(target: np.ndarray) -> np.ndarray:
        if distance is None:
            return ndi.distance_transform_edt(~target, sampling=spacing)
        return np.asarray(distance(target, spacing))

    distance_from_enclosure = measure_distance(filled)
    bright_level = CARTILAGE_BRIGHTER * marrow
    fluid_level = FLUID_BRIGHTER * marrow
    candidate = (
        finite_valid
        & ~filled
        & (distance_from_enclosure <= CARTILAGE_MM)
        & (plane > bright_level)
        & (plane <= fluid_level)
    )
    candidate_labels, _ = ndi.label(candidate)
    sagittal_distance = measure_distance(sagittal)
    coronal_distance = measure_distance(coronal)
    candidate_ids = np.unique(candidate_labels[candidate])
    candidate_ids = candidate_ids[candidate_ids > 0]
    sagittal_contact_min = ndi.minimum(
        sagittal_distance, candidate_labels, index=candidate_ids
    )
    coronal_contact_min = ndi.minimum(
        coronal_distance, candidate_labels, index=candidate_ids
    )
    contact_ids = candidate_ids[
        (sagittal_contact_min <= SHELL_MM) & (coronal_contact_min <= SHELL_MM)
    ].astype(np.int32, copy=False)
    candidate_sizes = np.bincount(candidate_labels.ravel())
    contact_sizes = candidate_sizes[contact_ids]
    selected_index = unique_largest(contact_sizes)
    selected = (
        candidate_labels == int(contact_ids[selected_index])
        if selected_index is not None
        else empty.copy()
    )
    result = {
        **base,
        "positive_enclosure": positive,
        "selected_enclosure": selected_enclosure,
        "filled_enclosure": filled,
        "fill_difference": fill_difference,
        "candidate": candidate,
        "candidate_labels": candidate_labels.astype(np.int32, copy=False),
        "sagittal_contact_distance_mm": sagittal_distance,
        "coronal_contact_distance_mm": coronal_distance,
        "contact_labels": contact_ids,
        "contact_sizes": contact_sizes.astype(np.int64, copy=False),
        "selected": selected,
        "marrow_median": marrow,
        "brightness_level": bright_level,
        "fluid_level": fluid_level,
    }
    if not candidate.any():
        status = "measured_empty_brightness_band"
    elif not len(contact_ids):
        status = "no_candidate_component_contacts_both_sources"
    elif selected_index is None:
        status = "tied_largest_components_contacting_both_sources"
    else:
        status = "selected_native_component"
    return {**result, "status": status}


def sagittal_cartilage_observations(record: dict[str, Any]) -> list[Observation]:
    """Make companions from validated serialized sagittal cartilage candidate rows.

    The saved reading row already contains the native candidate address and count. This transform
    adds no mask, recount, or threshold; incomplete and refused rows remain only their original
    readings in the containing record.
    """
    rows = record.get("observations", [])
    record_uid = record.get("series_uid")
    record_view = record.get("view")
    record_artifact = record.get("artifact")
    if (
        not isinstance(rows, list)
        or not isinstance(record_uid, str)
        or not record_uid
        or not isinstance(record_view, (list, tuple))
        or tuple(record_view) != SAGITTAL_FS
        or not isinstance(record_artifact, str)
        or not record_artifact
    ):
        return []

    companions: list[Observation] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        object_name = item.get("object")
        if object_name not in ("femoral_cartilage", "tibial_cartilage"):
            continue
        view = item.get("view")
        slices = item.get("slices")
        count = item.get("count")
        row = item.get("row")
        off_plane_mm = item.get("off_plane_mm")
        if (
            item.get("provenance") != "native"
            or item.get("kind") != "reading"
            or not isinstance(view, (list, tuple))
            or tuple(view) != SAGITTAL_FS
            or item.get("code") != "cartilage_candidates"
            or item.get("support") != CARTILAGE_READING
            or not isinstance(count, int)
            or isinstance(count, bool)
            or count <= 0
            or item.get("label") != OBJECT_CODES[object_name]
            or not isinstance(row, int)
            or isinstance(row, bool)
            or row < 0
            or not isinstance(slices, (list, tuple))
            or len(slices) != 1
            or not isinstance(slices[0], int)
            or isinstance(slices[0], bool)
            or slices[0] < 0
            or item.get("series_uid") != record_uid
            or item.get("artifact") != record_artifact
            or not isinstance(item.get("note"), str)
            or (
                off_plane_mm is not None
                and (
                    isinstance(off_plane_mm, bool)
                    or not isinstance(off_plane_mm, (int, float))
                    or not math.isfinite(off_plane_mm)
                    or off_plane_mm < 0
                )
            )
        ):
            continue
        companions.append(
            Observation(
                object=object_name,
                provenance="native",
                kind="resolved",
                series_uid=record_uid,
                view=tuple(view),
                slices=tuple(slices),
                code="identified",
                count=count,
                off_plane_mm=off_plane_mm,
                support=CARTILAGE_READING,
                note=CARTILAGE_NOTE,
                artifact=record_artifact,
                row=row,
                label=OBJECT_CODES[object_name],
            )
        )
    return companions
