"""Scan-local squint profiles and exact count comparisons.

The reader retains the physical squint and its source ``Series`` for the
duration of one study operation. Profiles are small count tables; they do not
contain dense pixel vectors or copied study volumes.
"""

from __future__ import annotations

import hashlib
import json
import math
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

from knee.collapse.physical import PlaneFrame, physical_squint
from knee.collapse.squint_stack import SquintStack, read_squint_stack, tile_centres_lps
from knee.diagnosis.squint_interfaces import (
    LEG_INSIDE,
    LEG_MIXED,
    ROLE_CONTEXT,
    ROLE_NAMES,
    ROLE_OBJECT,
    ROLE_UNQUERIED,
    TERRITORY_PROCEDURE,
    leg_map_code,
    territory_bank_name,
    territory_code,
)
from knee.study.corpus import open_corpus, series_directory
from knee.study.series import Series, read_series

_PROFILE_SCHEMA = "knee.squint-profile/v1"
_PROCEDURE = "knee.squint-profile/scan-tercile-v1"
_UNREAD = -2


def _plain_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "\0" not in value


def _array(value: object, shape: tuple[int, ...] | None = None) -> np.ndarray:
    if not isinstance(value, np.ndarray) or value.dtype.hasobject:
        raise ValueError("squint_array_invalid")
    if shape is not None and value.shape != shape:
        raise ValueError("squint_array_shape_invalid")
    return value


def _plain_nonnegative_int(value: object) -> bool:
    return type(value) is int and value >= 0


def _series_view(series: Series) -> dict[str, str]:
    return {
        "orientation": series.row.anatomical_plane,
        "fluid_sensitive": series.row.fluid_sensitive,
        "fat_suppression": series.row.fat_suppression,
    }


def _frame_at(series: Series, index: int) -> PlaneFrame | ValueError:
    geometry = series.geometry
    if geometry is None:
        return ValueError("series_geometry_unavailable")
    try:
        return PlaneFrame.from_dicom(
            geometry.position[index],
            geometry.orientation[index],
            geometry.spacing[index],
        )
    except (IndexError, ValueError) as error:
        return ValueError(str(error))


def _gradient(values: np.ndarray, axis: int) -> tuple[np.ndarray, np.ndarray]:
    """Return signed neighbor change and availability without bridging missing tiles."""
    result = np.full(values.shape, np.nan, dtype=np.float64)
    available = np.zeros(values.shape, dtype=np.bool_)
    if values.ndim != 3 or axis not in (1, 2) or values.shape[axis] == 0:
        return result, available
    finite = np.isfinite(values)
    length = values.shape[axis]
    for index in range(length):
        center = [slice(None)] * 3
        center[axis] = index
        center_t = tuple(center)
        center_values = values[center_t]
        center_finite = finite[center_t]
        before_values = before_finite = after_values = after_finite = None
        if index > 0:
            before = list(center)
            before[axis] = index - 1
            before_values = values[tuple(before)]
            before_finite = finite[tuple(before)]
        if index + 1 < length:
            after = list(center)
            after[axis] = index + 1
            after_values = values[tuple(after)]
            after_finite = finite[tuple(after)]
        both = np.zeros(center_values.shape, dtype=np.bool_)
        if before_finite is not None and after_finite is not None:
            both = center_finite & before_finite & after_finite
            target = result[center_t]
            target[both] = (after_values[both] - before_values[both]) / 2.0
            result[center_t] = target
        only_after = np.zeros(center_values.shape, dtype=np.bool_)
        if after_finite is not None:
            only_after = center_finite & after_finite & ~both
            target = result[center_t]
            target[only_after] = after_values[only_after] - center_values[only_after]
            result[center_t] = target
        only_before = np.zeros(center_values.shape, dtype=np.bool_)
        if before_finite is not None:
            only_before = center_finite & before_finite & ~both & ~only_after
            target = result[center_t]
            target[only_before] = (
                center_values[only_before] - before_values[only_before]
            )
            result[center_t] = target
        available[center_t] = both | only_after | only_before
    return result, available


def _metrics(stack: SquintStack) -> dict[str, np.ndarray]:
    median = np.asarray(stack.median, dtype=np.float64)
    minimum = np.asarray(stack.minimum, dtype=np.float64)
    maximum = np.asarray(stack.maximum, dtype=np.float64)
    if median.ndim != 3:
        raise ValueError("squint_median_shape_invalid")
    values: dict[str, np.ndarray] = {
        "signal_median": median,
        "signal_minimum": minimum,
        "signal_maximum": maximum,
        "local_range": maximum - minimum,
    }
    for metric in ("signal_median", "signal_minimum", "signal_maximum", "local_range"):
        values[metric].flags.writeable = False
    for axis, name in ((1, "gradient_row"), (2, "gradient_column")):
        gradient, _ = _gradient(median, axis)
        gradient.flags.writeable = False
        values[name] = gradient
    return values


def _metric_availability(
    stack: SquintStack, metric_values: dict[str, np.ndarray]
) -> dict[str, np.ndarray]:
    coverage = np.asarray(stack.coverage)
    if coverage.shape != stack.median.shape:
        raise ValueError("squint_coverage_shape_invalid")
    base = np.isfinite(coverage) & (coverage > 0)
    result: dict[str, np.ndarray] = {}
    for name, values in metric_values.items():
        available = base & np.isfinite(values)
        available.flags.writeable = False
        result[name] = available
    return result


def _calibrate(
    values: dict[str, np.ndarray], available: dict[str, np.ndarray]
) -> tuple[dict[str, dict[str, Any]], dict[str, np.ndarray]]:
    calibration: dict[str, dict[str, Any]] = {}
    codes: dict[str, np.ndarray] = {}
    for metric, array in values.items():
        mask = available[metric]
        finite_values = np.asarray(array[mask], dtype=np.float64)
        code_array = np.full(array.shape, _UNREAD, dtype=np.int8)
        if finite_values.size == 0:
            calibration[metric] = {
                "status": "unavailable",
                "available_count": 0,
                "quantile_method": "numpy_linear_terciles",
                "low": None,
                "high": None,
            }
        else:
            low, high = (
                float(value) for value in np.quantile(finite_values, (1 / 3, 2 / 3))
            )
            writable = mask & np.isfinite(array)
            code_array[writable & (array < low)] = -1
            code_array[writable & (array >= low) & (array <= high)] = 0
            code_array[writable & (array > high)] = 1
            calibration[metric] = {
                "status": "measured",
                "available_count": int(finite_values.size),
                "quantile_method": "numpy_linear_terciles",
                "low": low,
                "high": high,
            }
        code_array.flags.writeable = False
        codes[metric] = code_array
    return calibration, codes


def _read_one_series(corpus, study_row, row) -> Series:
    return read_series(series_directory(corpus, study_row, row), row)


def read_study_squints(
    root: Path,
    study_uid: str,
    *,
    io_workers: int = 8,
    tile_mm: float = 10.0,
) -> dict[str, Any]:
    """Read a study's series and make one cached physical squint per series.

    Series are read concurrently with a bounded worker pool. The returned
    ``native_series`` references are runtime-only; callers release the study
    dictionary after processing and must not serialize those objects.
    """
    if not isinstance(root, Path):
        raise TypeError("squint_root_path_required")
    if not _plain_text(study_uid):
        raise ValueError("squint_study_uid_required")
    if type(io_workers) is not int or io_workers <= 0:
        raise ValueError("squint_io_workers_positive_integer_required")
    if isinstance(tile_mm, bool) or not isinstance(tile_mm, (int, float)):
        raise TypeError("squint_tile_mm_invalid")
    tile_mm = float(tile_mm)
    if not math.isfinite(tile_mm) or tile_mm <= 0:
        raise ValueError("squint_tile_mm_invalid")

    corpus = open_corpus(root)
    study_row = corpus.tables.studies.get(study_uid)
    if study_row is None:
        raise ValueError("squint_study_uid_missing")
    series_rows = tuple(study_row.series)
    if not series_rows:
        raise ValueError("squint_study_series_missing")
    worker_count = min(io_workers, len(series_rows))
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        native_series = tuple(
            pool.map(lambda row: _read_one_series(corpus, study_row, row), series_rows)
        )

    series_records: list[dict[str, Any]] = []
    slice_count = tile_count = successful_squints = 0
    for series in native_series:
        stack = read_squint_stack(
            series,
            tile_mm,
            lambda z, current=series: _frame_at(current, z),
        )
        values = _metrics(stack) if stack.code == "present" else {}
        availability = _metric_availability(stack, values) if values else {}
        calibration, codes = _calibrate(values, availability) if values else ({}, {})
        geometry = series.geometry
        shape = (
            tuple(int(dim) for dim in series.volume.shape)
            if series.volume is not None
            else (0, 0, 0)
        )
        if stack.code == "present":
            successful_squints += 1
            tile_count += int(stack.median.size)
        slice_count += len(series.slices)
        source = {
            "api": "knee.diagnosis.squint_profiles.read_study_squints/v1",
            "study_uid": study_uid,
            "series_uid": series.row.series_uid,
            "tile_mm": tile_mm,
            "procedure": _PROCEDURE,
            "geometry_status": "available" if geometry is not None else "unavailable",
            "calibration": calibration,
            "native_slice_paths": tuple(
                str(item.path.resolve()) for item in series.slices
            ),
        }
        series_records.append(
            {
                "series_uid": series.row.series_uid,
                "view": _series_view(series),
                "shape": shape,
                "geometry": None
                if geometry is None
                else {
                    "orientation": geometry.orientation,
                    "position": geometry.position,
                    "spacing": geometry.spacing,
                },
                "stack": stack,
                "metric_values": values,
                "metric_available": availability,
                "metric_codes": codes,
                "calibration": calibration,
                "source": source,
                "native_series": series,
            }
        )
    return {
        "schema": "knee.squint-study/v1",
        "study_uid": study_uid,
        "series": series_records,
        "work": {
            "series_count": len(series_records),
            "series_read": len(series_records),
            "slices_read": slice_count,
            "squinted_series": successful_squints,
            "tiles_squinted": tile_count,
            "io_workers": worker_count,
        },
    }


def _bank_name(
    view: dict[str, str], metric: str, direction: str, tile_mm: float
) -> str:
    view_key = json.dumps(
        [view["orientation"], view["fluid_sensitive"], view["fat_suppression"]],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return (
        f"squint/v1/view={view_key}/metric={metric}/direction={direction}/"
        f"scale={tile_mm:g}mm"
    )


def _window(window: object, shape: tuple[int, int, int]) -> tuple[int, ...]:
    if (
        not isinstance(window, tuple)
        or len(window) != 6
        or any(type(value) is not int for value in window)
    ):
        raise ValueError("squint_window_six_integer_bounds_required")
    z0, z1, r0, r1, c0, c1 = window
    depth, rows, cols = shape
    if not (0 <= z0 <= z1 <= depth and 0 <= r0 <= r1 <= rows and 0 <= c0 <= c1 <= cols):
        raise ValueError("squint_window_out_of_bounds")
    return window


def _ternary_counts(codes: np.ndarray) -> list[int] | None:
    selected = np.asarray(codes).reshape(-1)
    measured = selected != _UNREAD
    if not np.any(measured):
        return None
    return [int(np.count_nonzero(selected[measured] == digit)) for digit in (-1, 0, 1)]


def _spatial_masks(
    centres: np.ndarray, window: tuple[int, ...]
) -> dict[str, np.ndarray]:
    """Partition a tile window around its LPS center when geometry is available."""
    z0, z1, r0, r1, c0, c1 = window
    selected = np.asarray(centres)[z0:z1, r0:r1, c0:c1]
    if selected.ndim != 4 or selected.shape[-1] != 3 or not selected.size:
        return {}
    finite = np.all(np.isfinite(selected), axis=-1)
    if not np.any(finite):
        return {}
    origin = np.median(selected[finite], axis=0)
    delta = selected - origin
    masks: dict[str, np.ndarray] = {}
    # DICOM patient coordinates: +x is left, +y posterior, +z superior.
    for positive_name, negative_name, axis in (
        ("left", "right", 0),
        ("posterior", "anterior", 1),
        ("superior", "inferior", 2),
    ):
        positive = finite & (delta[..., axis] > 0)
        negative = finite & (delta[..., axis] < 0)
        if np.any(positive):
            masks[f"patient_lps_{positive_name}"] = positive
        if np.any(negative):
            masks[f"patient_lps_{negative_name}"] = negative
    return masks


def _depth_masks(window: tuple[int, ...]) -> dict[str, np.ndarray]:
    z0, z1, r0, r1, c0, c1 = window
    depth = z1 - z0
    if depth <= 0:
        return {}
    masks: dict[str, np.ndarray] = {}
    labels = ("stack_depth_first", "stack_depth_middle", "stack_depth_last")
    for label, indices in zip(
        labels, np.array_split(np.arange(depth), min(depth, 3)), strict=False
    ):
        if indices.size:
            mask = np.zeros((depth, r1 - r0, c1 - c0), dtype=np.bool_)
            mask[indices] = True
            masks[label] = mask
    return masks


def profile_window(
    series: dict[str, Any],
    window: tuple[int, int, int, int, int, int],
    *,
    subject: str,
) -> dict[str, Any]:
    """Count one half-open tile-grid window against the series' frozen calibration."""
    if not isinstance(series, dict) or not _plain_text(subject):
        raise ValueError("squint_series_and_subject_required")
    stack = series.get("stack")
    if not isinstance(stack, SquintStack):
        raise TypeError("squint_stack_required")
    metric_codes = series.get("metric_codes")
    calibration = series.get("calibration")
    view = series.get("view")
    source = series.get("source")
    if not isinstance(metric_codes, dict) or not isinstance(calibration, dict):
        raise TypeError("squint_metric_codes_required")
    if (
        not isinstance(view, dict)
        or set(view) != {"orientation", "fluid_sensitive", "fat_suppression"}
        or any(not isinstance(value, str) for value in view.values())
    ):
        raise ValueError("squint_view_invalid")
    if not isinstance(source, dict) or source.get("procedure") != _PROCEDURE:
        raise ValueError("squint_source_identity_invalid")
    shape = tuple(int(value) for value in stack.median.shape)
    window = _window(window, shape)
    if stack.code != "present":
        return {
            "schema": _PROFILE_SCHEMA,
            "subject": subject,
            "banks": {},
            "source": {
                "procedure": _PROCEDURE,
                "series_context": source,
                "window": list(window) if isinstance(window, tuple) else None,
                "status": stack.code,
                "why": stack.why,
            },
        }
    z0, z1, r0, r1, c0, c1 = window
    banks: dict[str, list[int]] = {}
    centres = np.asarray(stack.centres_lps)
    spatial_masks = _spatial_masks(centres, window)
    depth_masks = _depth_masks(window)
    for metric in (
        "signal_median",
        "signal_minimum",
        "signal_maximum",
        "local_range",
        "gradient_row",
        "gradient_column",
    ):
        code_array = metric_codes.get(metric)
        record = calibration.get(metric)
        if not isinstance(code_array, np.ndarray) or not isinstance(record, dict):
            continue
        if record.get("status") != "measured":
            continue
        selected = code_array[z0:z1, r0:r1, c0:c1]
        overview = _ternary_counts(selected)
        direction = {"gradient_row": "row", "gradient_column": "column"}.get(metric)
        if overview is not None and direction is None:
            banks[_bank_name(view, metric, "overview", float(stack.tile_mm))] = overview
        for scope, mask in spatial_masks.items():
            counts = _ternary_counts(np.where(mask, selected, _UNREAD))
            if counts is not None:
                banks[_bank_name(view, metric, scope, float(stack.tile_mm))] = counts
        for scope, mask in depth_masks.items():
            counts = _ternary_counts(np.where(mask, selected, _UNREAD))
            if counts is not None:
                banks[_bank_name(view, metric, scope, float(stack.tile_mm))] = counts
        if direction is not None and overview is not None:
            banks[_bank_name(view, metric, direction, float(stack.tile_mm))] = overview
    native_bounds = None
    if r1 > r0 and c1 > c0:
        bounds = np.asarray(stack.bounds_rc)[r0:r1, c0:c1]
        if bounds.size:
            native_bounds = [
                int(np.min(bounds[..., 0])),
                int(np.max(bounds[..., 1])),
                int(np.min(bounds[..., 2])),
                int(np.max(bounds[..., 3])),
            ]
    return {
        "schema": _PROFILE_SCHEMA,
        "subject": subject,
        "banks": banks,
        "source": {
            "procedure": _PROCEDURE,
            "series_context": source,
            "window": list(window),
            "native_bounds_rc": native_bounds,
            "status": "measured" if banks else "silent",
            "view": dict(view),
        },
    }


def _refined_series(
    series: dict[str, Any],
    window: tuple[int, int, int, int, int, int],
    *,
    tile_mm: float = 2.0,
    native_eligible: np.ndarray | None = None,
) -> tuple[dict[str, Any], list[int]]:
    """Make a finer physical squint only inside one coarse window's native support.

    The coarse scan's calibration is reused. The crop is translated back through each original
    DICOM frame, and the returned profile retains both tile-grid and native-pixel addresses.
    """
    coarse = series.get("stack") if isinstance(series, dict) else None
    native = series.get("native_series") if isinstance(series, dict) else None
    source = series.get("source") if isinstance(series, dict) else None
    view = series.get("view") if isinstance(series, dict) else None
    coarse_calibration = series.get("calibration") if isinstance(series, dict) else None
    if not isinstance(coarse, SquintStack) or coarse.code != "present":
        raise ValueError("squint_refine_coarse_stack_unavailable")
    if (
        not isinstance(native, Series)
        or native.volume is None
        or native.geometry is None
    ):
        raise ValueError("squint_refine_native_series_unavailable")
    if not isinstance(source, dict) or source.get("procedure") != _PROCEDURE:
        raise ValueError("squint_source_identity_invalid")
    if not isinstance(coarse_calibration, dict) or not isinstance(view, dict):
        raise TypeError("squint_refine_calibration_or_view_missing")
    if isinstance(tile_mm, bool) or not isinstance(tile_mm, (int, float)):
        raise TypeError("squint_tile_mm_invalid")
    tile_mm = float(tile_mm)
    if not math.isfinite(tile_mm) or tile_mm <= 0 or tile_mm >= coarse.tile_mm:
        raise ValueError("squint_refine_tile_mm_must_be_finer")
    window = _window(window, tuple(int(value) for value in coarse.median.shape))
    z0, z1, tr0, tr1, tc0, tc1 = window
    if z0 == z1 or tr0 == tr1 or tc0 == tc1:
        raise ValueError("squint_refine_empty_window")
    selected_bounds = np.asarray(coarse.bounds_rc)[tr0:tr1, tc0:tc1]
    if not selected_bounds.size:
        raise ValueError("squint_refine_empty_native_support")
    row0, row1 = (
        int(np.min(selected_bounds[..., 0])),
        int(np.max(selected_bounds[..., 1])),
    )
    col0, col1 = (
        int(np.min(selected_bounds[..., 2])),
        int(np.max(selected_bounds[..., 3])),
    )
    cropped = native.volume[z0:z1, row0:row1, col0:col1]
    if cropped.size == 0 or row1 <= row0 or col1 <= col0:
        raise ValueError("squint_refine_empty_native_support")
    if native_eligible is not None:
        if native_eligible.shape != cropped.shape:
            raise ValueError("squint_refine_eligibility_shape_invalid")
        # A bounded input: outside and unqueried pixels receive no reading.
        cropped = np.where(native_eligible, cropped, np.nan)

    fine_medians: list[np.ndarray] = []
    fine_minima: list[np.ndarray] = []
    fine_maxima: list[np.ndarray] = []
    fine_coverages: list[np.ndarray] = []
    fine_centres: list[np.ndarray] = []
    fine_bounds: np.ndarray | None = None
    fine_tile_shape: tuple[int, int] | None = None
    for local_z, absolute_z in enumerate(range(z0, z1)):
        geometry = native.geometry
        frame = PlaneFrame.from_dicom(
            geometry.position[absolute_z],
            geometry.orientation[absolute_z],
            geometry.spacing[absolute_z],
        )
        shifted_origin = frame.to_patient(np.asarray([[row0, col0]], dtype=np.float64))[
            0
        ]
        cropped_frame = PlaneFrame.from_dicom(
            shifted_origin,
            geometry.orientation[absolute_z],
            geometry.spacing[absolute_z],
        )
        squint = physical_squint(cropped[local_z], cropped_frame.spacing_rc, tile_mm)
        if fine_bounds is None:
            fine_bounds = squint.bounds_rc
            fine_tile_shape = squint.tile_shape_rc
        elif (
            squint.bounds_rc.shape != fine_bounds.shape
            or squint.tile_shape_rc != fine_tile_shape
            or not np.array_equal(squint.bounds_rc, fine_bounds)
        ):
            raise ValueError("squint_refine_geometry_grid_mismatch")
        shifted_bounds = np.array(squint.bounds_rc, copy=True)
        shifted_bounds[..., 0:2] += row0
        shifted_bounds[..., 2:4] += col0
        fine_medians.append(squint.median)
        fine_minima.append(squint.minimum)
        fine_maxima.append(squint.maximum)
        fine_coverages.append(squint.coverage)
        fine_centres.append(tile_centres_lps(cropped_frame, squint.bounds_rc))
    assert fine_bounds is not None and fine_tile_shape is not None
    fine_stack = SquintStack(
        series_uid=native.row.series_uid,
        code="present",
        why=f"native crop squinted at {tile_mm:g} mm",
        tile_mm=tile_mm,
        tile_shape_rc=tuple(int(value) for value in fine_tile_shape),
        bounds_rc=fine_bounds,
        median=np.stack(fine_medians),
        minimum=np.stack(fine_minima),
        maximum=np.stack(fine_maxima),
        coverage=np.stack(fine_coverages),
        centres_lps=np.stack(fine_centres),
    )
    fine_values = _metrics(fine_stack)
    fine_available = _metric_availability(fine_stack, fine_values)
    fine_codes: dict[str, np.ndarray] = {}
    for metric, values in fine_values.items():
        record = coarse_calibration.get(metric)
        codes = np.full(values.shape, _UNREAD, dtype=np.int8)
        if isinstance(record, dict) and record.get("status") == "measured":
            available = fine_available[metric] & np.isfinite(values)
            low, high = float(record["low"]), float(record["high"])
            codes[available & (values < low)] = -1
            codes[available & (values >= low) & (values <= high)] = 0
            codes[available & (values > high)] = 1
        codes.flags.writeable = False
        fine_codes[metric] = codes
    fine_record = {
        "stack": fine_stack,
        "metric_values": fine_values,
        "metric_available": fine_available,
        "metric_codes": fine_codes,
        "calibration": coarse_calibration,
        "view": view,
        "source": source,
    }
    return fine_record, [row0, row1, col0, col1]


def refine_window(
    series: dict[str, Any],
    window: tuple[int, int, int, int, int, int],
    *,
    subject: str,
    tile_mm: float = 2.0,
) -> dict[str, Any]:
    """Read a finer native crop using the unchanged v1 coarse scan reference."""
    fine_record, crop = _refined_series(series, window, tile_mm=tile_mm)
    fine_stack = fine_record["stack"]
    tile_mm = float(fine_stack.tile_mm)
    z0, z1, *_ = window
    row0, row1, col0, col1 = crop
    profile = profile_window(
        fine_record,
        (0, z1 - z0, 0, fine_stack.median.shape[1], 0, fine_stack.median.shape[2]),
        subject=subject,
    )
    profile["source"].update(
        {
            "refinement": True,
            "coarse_window": list(window),
            "fine_tile_mm": tile_mm,
            "native_crop_rc": [row0, row1, col0, col1],
            "native_slice_range": [z0, z1],
            "native_bounds_rc": [row0, row1, col0, col1],
        }
    )
    return profile


def _leg_inputs(series: dict, leg_map: dict) -> tuple[SquintStack, np.ndarray]:
    """Check the addressed leg grid before using it as a reading prior."""
    stack = series.get("stack") if isinstance(series, dict) else None
    if not isinstance(stack, SquintStack):
        raise TypeError("squint_stack_required")
    code = leg_map_code(leg_map, grid_shape=stack.median.shape)
    if code != "valid":
        raise ValueError(code)
    if leg_map["series_uid"] != series.get("series_uid"):
        raise ValueError("squint_leg_series_mismatch")
    if leg_map["tile_mm"] != stack.tile_mm:
        raise ValueError("squint_leg_scale_mismatch")
    source = series.get("source")
    if not isinstance(source, dict) or source.get("procedure") != _PROCEDURE:
        raise ValueError("squint_source_identity_invalid")
    if leg_map.get("study_uid", source.get("study_uid")) != source.get("study_uid"):
        raise ValueError("squint_leg_study_mismatch")
    return stack, leg_map["codes"]


def _leg_fingerprint(leg_map: dict) -> str:
    return hashlib.sha256(np.ascontiguousarray(leg_map["codes"]).tobytes()).hexdigest()


def _codes_against(
    values: dict, available: dict, calibration: dict, eligible: np.ndarray
) -> dict[str, np.ndarray]:
    """Write only available eligible readings against already measured edges."""
    result = {}
    for metric, array in values.items():
        record = calibration.get(metric, {})
        codes = np.full(array.shape, _UNREAD, dtype=np.int8)
        if record.get("status") == "measured":
            low, high = record["low"], record["high"]
            writable = available[metric] & eligible & np.isfinite(array)
            codes[writable & (array < low)] = -1
            codes[writable & (array >= low) & (array <= high)] = 0
            codes[writable & (array > high)] = 1
        codes.flags.writeable = False
        result[metric] = codes
    return result


def leg_calibration(series: dict, leg_map: dict) -> tuple[dict, dict]:
    """Return ``(calibration, codes)`` like ``_calibrate``, using inside tiles only.

    Mixed tiles can be coded, but never set the edges. Unknown and outside tiles
    remain unread. The raw six metrics and their availability are reused unchanged.
    Pass this pair to ``profile_territory`` to share it across a series' objects.
    """
    stack, leg = _leg_inputs(series, leg_map)
    values = series.get("metric_values")
    available = series.get("metric_available")
    if not isinstance(values, dict) or not isinstance(available, dict):
        raise TypeError("squint_metric_values_required")
    inside = leg == LEG_INSIDE
    eligible = inside | (leg == LEG_MIXED)
    calibration = {}
    fingerprint = _leg_fingerprint(leg_map)
    signature = (
        series["series_uid"],
        stack.tile_mm,
        fingerprint,
        tuple(
            (metric, id(array), id(available.get(metric)))
            for metric, array in values.items()
        ),
    )
    immutable = all(
        isinstance(array, np.ndarray)
        and not array.flags.writeable
        and isinstance(available.get(metric), np.ndarray)
        and not available[metric].flags.writeable
        for metric, array in values.items()
    )
    cached = series.get("_territory_leg_calibration")
    if immutable and cached is not None and cached[0] == signature:
        return cached[1]
    for metric, array in values.items():
        _array(array, stack.median.shape)
        mask = _array(available.get(metric), stack.median.shape)
        if mask.dtype != np.bool_:
            raise ValueError("squint_metric_availability_invalid")
        selected = np.asarray(
            array[inside & mask & np.isfinite(array)], dtype=np.float64
        )
        low, high = (None, None)
        if selected.size:
            low, high = (float(x) for x in np.quantile(selected, (1 / 3, 2 / 3)))
        calibration[metric] = {
            "status": "measured" if selected.size else "unavailable",
            "policy": "leg_inside_terciles",
            "available_count": int(selected.size),
            "inside_count": int(np.count_nonzero(inside)),
            "mixed_count": int(np.count_nonzero(leg == LEG_MIXED)),
            "writable_count": int(
                np.count_nonzero(eligible & mask & np.isfinite(array))
            )
            if selected.size
            else 0,
            "quantile_method": "numpy_linear_terciles",
            "low": low,
            "high": high,
            "series_uid": series["series_uid"],
            "tile_mm": float(stack.tile_mm),
            "leg_map_sha256": fingerprint,
        }
    result = calibration, _codes_against(values, available, calibration, eligible)
    if immutable:
        # Runtime-only, just like the cached raw metrics. Refinement consumes
        # this same coarse reference rather than calibrating each object again.
        series["_territory_leg_calibration"] = (signature, result)
    return result


def _territory_inputs(series: dict, territory: dict, leg_map: dict, subject: str):
    stack, leg = _leg_inputs(series, leg_map)
    code = territory_code(territory, grid_shape=stack.median.shape)
    if code != "valid":
        raise ValueError(code)
    if not _plain_text(subject) or territory["subject"] != subject:
        raise ValueError("squint_territory_subject_mismatch")
    if territory["series_uid"] != series["series_uid"]:
        raise ValueError("squint_territory_series_mismatch")
    if territory["study_uid"] != series["source"].get("study_uid"):
        raise ValueError("squint_territory_study_mismatch")
    view = series.get("view")
    if (
        not isinstance(view, dict)
        or set(view) != {"orientation", "fluid_sensitive", "fat_suppression"}
        or any(not isinstance(value, str) for value in view.values())
    ):
        raise ValueError("squint_view_invalid")
    return stack, leg


def _territory_source(territory: dict) -> dict:
    """Retain the address/roles/shares, excluding the runtime-only native mask."""
    source = {
        k: v
        for k, v in territory.items()
        if k not in {"roles", "object_share", "native_support"}
    }
    source["roles"] = territory["roles"].tolist()
    share = territory["object_share"]
    source["object_share"] = np.where(np.isfinite(share), share, None).tolist()
    support = territory.get("native_support")
    if support is not None:
        source["native_support_address"] = {
            "slices": list(support["slices"]),
            "offset_rc": list(support["offset_rc"]),
            "shape": list(support["mask"].shape),
            "support_count": int(np.count_nonzero(support["mask"])),
            "mask_sha256": hashlib.sha256(support["mask"].tobytes()).hexdigest(),
        }
    return source


def _count_territory(series, window, roles, eligible, calibration, codes, *, subject):
    """Count role facets using one object-centred origin and v1 depth partitions."""
    stack = series["stack"]
    z0, z1, r0, r1, c0, c1 = window
    selection = (slice(z0, z1), slice(r0, r1), slice(c0, c1))
    centres = np.asarray(stack.centres_lps)[selection]
    finite = np.all(np.isfinite(centres), axis=-1)
    object_places = (roles == ROLE_OBJECT) & eligible
    origin_places = object_places & finite
    origin = np.median(centres[origin_places], axis=0) if origin_places.any() else None
    directions = _depth_masks(window)
    if origin is not None:
        delta = centres - origin
        for positive, negative, axis in (
            ("left", "right", 0),
            ("posterior", "anterior", 1),
            ("superior", "inferior", 2),
        ):
            directions[f"patient_lps_{positive}"] = finite & (delta[..., axis] > 0)
            directions[f"patient_lps_{negative}"] = finite & (delta[..., axis] < 0)
    banks = {}
    for role, name in ROLE_NAMES.items():
        role_mask = (roles == role) & eligible
        for metric, code_array in codes.items():
            if calibration.get(metric, {}).get("status") != "measured":
                continue
            selected = code_array[selection]
            main_direction = {"gradient_row": "row", "gradient_column": "column"}.get(
                metric, "overview"
            )
            for direction, mask in {
                main_direction: role_mask,
                **{key: value & role_mask for key, value in directions.items()},
            }.items():
                counts = _ternary_counts(selected[mask])
                if counts is not None:
                    banks[
                        territory_bank_name(
                            series["view"],
                            name,
                            metric,
                            direction,
                            float(stack.tile_mm),
                        )
                    ] = counts
    bounds = stack.bounds_rc[r0:r1, c0:c1]
    return {
        "schema": _PROFILE_SCHEMA,
        "subject": subject,
        "banks": banks,
        "source": {
            "procedure": TERRITORY_PROCEDURE,
            "series_context": series["source"],
            "calibration": calibration,
            "calibration_policy": "leg_inside_terciles",
            "window": list(window),
            "native_bounds_rc": [
                int(bounds[..., 0].min()),
                int(bounds[..., 1].max()),
                int(bounds[..., 2].min()),
                int(bounds[..., 3].max()),
            ],
            "status": "measured" if banks else "silent",
            "view": dict(series["view"]),
            "direction_origin": {
                "policy": "median_object_tile_centres_lps",
                "lps": origin.tolist() if origin is not None else None,
                "tile_count": int(np.count_nonzero(origin_places)),
                "status": "measured"
                if origin is not None
                else "object_geometry_unavailable",
            },
            "depth_policy": "window_stack_depth_thirds_intersect_role",
            "role_tile_counts": {
                name: int(np.count_nonzero((roles == role) & eligible))
                for role, name in ROLE_NAMES.items()
            },
        },
    }


def profile_territory(series, territory, leg_map, *, subject, calibration=None) -> dict:
    """Read object and context places separately; no box-only object surrogate.

    ``calibration`` may be the pair returned by ``leg_calibration`` (reuses
    codes), or its edge dictionary (codes the cached metrics against those edges).
    """
    _, leg = _territory_inputs(series, territory, leg_map, subject)
    if calibration is None:
        calibration = leg_calibration(series, leg_map)
    if isinstance(calibration, tuple) and len(calibration) == 2:
        records, codes = calibration
    else:
        records, codes = calibration, None
    if not isinstance(records, dict):
        raise TypeError("squint_leg_calibration_invalid")
    fingerprint = _leg_fingerprint(leg_map)
    for metric in series["metric_values"]:
        record = records.get(metric)
        if (
            not isinstance(record, dict)
            or record.get("policy") != "leg_inside_terciles"
            or record.get("series_uid") != series["series_uid"]
            or record.get("leg_map_sha256") != fingerprint
        ):
            raise ValueError("squint_leg_calibration_identity_mismatch")
        if record.get("status") not in ("measured", "unavailable"):
            raise ValueError("squint_leg_calibration_status_invalid")
        if record["status"] == "measured":
            low, high = record.get("low"), record.get("high")
            if (
                not isinstance(low, (int, float))
                or not isinstance(high, (int, float))
                or not math.isfinite(low)
                or not math.isfinite(high)
                or low > high
            ):
                raise ValueError("squint_leg_calibration_edges_invalid")
    eligible = (leg == LEG_INSIDE) | (leg == LEG_MIXED)
    if codes is None:
        codes = _codes_against(
            series["metric_values"], series["metric_available"], records, eligible
        )
    if not isinstance(codes, dict):
        raise TypeError("squint_leg_codes_invalid")
    for metric in series["metric_values"]:
        array = _array(codes.get(metric), leg.shape)
        if array.dtype != np.int8 or not np.isin(array, (_UNREAD, -1, 0, 1)).all():
            raise ValueError("squint_leg_codes_invalid")
    window = tuple(territory["tile_window"])
    z0, z1, r0, r1, c0, c1 = window
    profile = _count_territory(
        series,
        window,
        territory["roles"],
        eligible[z0:z1, r0:r1, c0:c1],
        records,
        codes,
        subject=subject,
    )
    profile["source"].update(
        {
            "territory": _territory_source(territory),
            "leg_map": {
                "rule": leg_map["rule"],
                "provenance": leg_map["provenance"],
                "codes_sha256": fingerprint,
            },
        }
    )
    return profile


def refine_territory(series, territory, leg_map, *, subject, tile_mm=2.0) -> dict:
    """Read a finer addressed territory against its coarse leg-only reference.

    Any overlap with a measured native support makes a fine object-associated
    tile; other queried leg tiles are context. Without native support, the
    coarse object tiles supply the support. Partial occupancy is retained.
    """
    coarse, leg = _territory_inputs(series, territory, leg_map, subject)
    calibration, _ = leg_calibration(series, leg_map)
    window = tuple(territory["tile_window"])
    z0, z1, tr0, tr1, tc0, tc1 = window
    bounds = coarse.bounds_rc[tr0:tr1, tc0:tc1]
    row0, row1 = int(bounds[..., 0].min()), int(bounds[..., 1].max())
    col0, col1 = int(bounds[..., 2].min()), int(bounds[..., 3].max())
    shape = (z1 - z0, row1 - row0, col1 - col0)
    eligible = np.zeros(shape, dtype=np.bool_)
    object_pixels = np.zeros(shape, dtype=np.bool_)
    roles = territory["roles"]
    for r, c in np.ndindex(bounds.shape[:2]):
        r0, r1, c0, c1 = (int(x) for x in bounds[r, c])
        for z in range(z1 - z0):
            role = roles[z, r, c]
            if role not in ROLE_NAMES or leg[z0 + z, tr0 + r, tc0 + c] not in (
                LEG_INSIDE,
                LEG_MIXED,
            ):
                continue
            address = (z, slice(r0 - row0, r1 - row0), slice(c0 - col0, c1 - col0))
            eligible[address] = True
            object_pixels[address] = role == ROLE_OBJECT
    support = territory.get("native_support")
    if support is not None:
        object_pixels[:] = False
        mask = support["mask"]
        sr, sc = support["offset_rc"]
        if not mask.any():
            raise ValueError("squint_native_support_empty")
        depth, rows, cols = series["shape"]
        if (
            sr < 0
            or sc < 0
            or sr + mask.shape[1] > rows
            or sc + mask.shape[2] > cols
            or any(z < 0 or z >= depth for z in support["slices"])
            or len(set(support["slices"])) != len(support["slices"])
        ):
            raise ValueError("squint_native_support_address_invalid")
        ir0, ir1 = max(sr, row0), min(sr + mask.shape[1], row1)
        ic0, ic1 = max(sc, col0), min(sc + mask.shape[2], col1)
        if ir0 < ir1 and ic0 < ic1:
            for index, z in enumerate(support["slices"]):
                if z0 <= z < z1:
                    object_pixels[
                        z - z0, ir0 - row0 : ir1 - row0, ic0 - col0 : ic1 - col0
                    ] = mask[index, ir0 - sr : ir1 - sr, ic0 - sc : ic1 - sc]
        if not object_pixels.any():
            raise ValueError("squint_native_support_outside_territory")
        object_pixels &= eligible
    # Share the exact native crop/geometry producer with v1; only the input
    # domain and coding reference differ. Do not measure outside the queried leg.
    fine_series, crop = _refined_series(
        {**series, "calibration": calibration},
        window,
        tile_mm=tile_mm,
        native_eligible=eligible,
    )
    fine = fine_series["stack"]
    fine_roles = np.full(fine.median.shape, ROLE_UNQUERIED, dtype=np.int8)
    object_share = np.full(fine.median.shape, np.nan, dtype=np.float64)
    eligible_share = np.zeros(fine.median.shape, dtype=np.float64)
    for r, c in np.ndindex(fine.bounds_rc.shape[:2]):
        r0, r1, c0, c1 = (int(x) for x in fine.bounds_rc[r, c])
        for z in range(z1 - z0):
            address = (z, slice(r0, r1), slice(c0, c1))
            region = eligible[address]
            if not region.any():
                continue
            count = int(np.count_nonzero(object_pixels[address]))
            fine_roles[z, r, c] = ROLE_OBJECT if count else ROLE_CONTEXT
            object_share[z, r, c] = count / region.size
            eligible_share[z, r, c] = np.count_nonzero(region) / region.size
    fine_window = (
        0,
        fine.median.shape[0],
        0,
        fine.median.shape[1],
        0,
        fine.median.shape[2],
    )
    profile = _count_territory(
        fine_series,
        fine_window,
        fine_roles,
        eligible_share > 0,
        calibration,
        fine_series["metric_codes"],
        subject=subject,
    )
    profile["source"].update(
        {
            "territory": _territory_source(territory),
            "leg_map": {
                "rule": leg_map["rule"],
                "provenance": leg_map["provenance"],
                "codes_sha256": _leg_fingerprint(leg_map),
            },
            "refinement": True,
            "calibration_policy": "coarse_leg_inside_terciles_reused",
            "coarse_window": list(window),
            "fine_tile_mm": float(tile_mm),
            "native_crop_rc": crop,
            "native_bounds_rc": crop,
            "native_slice_range": [z0, z1],
            "fine_roles": fine_roles.tolist(),
            "fine_object_share": np.where(
                np.isfinite(object_share), object_share, None
            ).tolist(),
            "fine_eligible_share": eligible_share.tolist(),
            "fine_support_policy": "native_support_overlap"
            if support is not None
            else "coarse_object_tile_overlap",
        }
    )
    return profile


def _profile(profile: object) -> tuple[str, dict[str, list[int]], dict[str, Any]]:
    if not isinstance(profile, dict) or profile.get("schema") != _PROFILE_SCHEMA:
        raise ValueError("squint_profile_schema_invalid")
    subject = profile.get("subject")
    banks = profile.get("banks")
    source = profile.get("source")
    if (
        not _plain_text(subject)
        or not isinstance(banks, dict)
        or not isinstance(source, dict)
    ):
        raise ValueError("squint_profile_shape_invalid")
    for name, counts in banks.items():
        if (
            not _plain_text(name)
            or not isinstance(counts, (list, tuple))
            or len(counts) != 3
        ):
            raise ValueError("squint_profile_bank_invalid")
        if any(not _plain_nonnegative_int(value) for value in counts):
            raise ValueError("squint_profile_count_invalid")
    if source.get("procedure") not in (_PROCEDURE, TERRITORY_PROCEDURE):
        raise ValueError("squint_profile_procedure_mismatch")
    return subject, banks, source


def merge_profiles(profiles, *, subject: str) -> dict[str, Any]:
    """Add same-bank ternary counts while preserving all source/calibration records."""
    if not _plain_text(subject):
        raise ValueError("squint_subject_required")
    try:
        items = tuple(profiles)
    except TypeError as error:
        raise ValueError("squint_profiles_iterable_required") from error
    if not items:
        raise ValueError("squint_profiles_nonempty_required")
    parsed = [_profile(item) for item in items]
    procedures = {source["procedure"] for _, _, source in parsed}
    if len(procedures) != 1:
        raise ValueError("squint_profile_procedure_mismatch")
    if any(profile_subject != subject for profile_subject, _, _ in parsed):
        raise ValueError("squint_profile_subject_mismatch")
    bank_names = sorted({name for _, banks, _ in parsed for name in banks})
    merged: dict[str, list[int]] = {}
    for name in bank_names:
        total = [0, 0, 0]
        for _, banks, _ in parsed:
            counts = banks.get(name)
            if counts is not None:
                for index, value in enumerate(counts):
                    total[index] += value
        merged[name] = total
    lineage = [source for _, _, source in parsed]
    lineage.sort(
        key=lambda item: json.dumps(
            item, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str
        )
    )
    return {
        "schema": _PROFILE_SCHEMA,
        "subject": subject,
        "banks": merged,
        "source": {
            "api": "knee.diagnosis.squint_profiles.merge_profiles/v1",
            "procedure": parsed[0][2]["procedure"],
            "lineage": lineage,
            "status": "measured" if merged else "silent",
        },
    }


def cosine_evidence(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Return exact count-space cosine terms over jointly speaking named banks."""
    left_subject, left_banks, left_source = _profile(left)
    right_subject, right_banks, right_source = _profile(right)
    if left_source.get("procedure") != right_source.get("procedure"):
        return {"code": "identity_mismatch", "reason": "procedure_mismatch"}
    common = tuple(
        name
        for name in sorted(left_banks.keys() & right_banks.keys())
        if any(left_banks[name]) and any(right_banks[name])
    )
    if not common:
        return {
            "code": "silent",
            "dot": 0,
            "left_norm_sq": 0,
            "right_norm_sq": 0,
            "common_banks": [],
            "left_subject": left_subject,
            "right_subject": right_subject,
        }
    dot = left_norm_sq = right_norm_sq = 0
    for name in common:
        for a, b in zip(left_banks[name], right_banks[name], strict=True):
            dot += a * b
            left_norm_sq += a * a
            right_norm_sq += b * b
    return {
        "code": "ok",
        "dot": dot,
        "left_norm_sq": left_norm_sq,
        "right_norm_sq": right_norm_sq,
        "common_banks": list(common),
        "left_subject": left_subject,
        "right_subject": right_subject,
    }


__all__ = [
    "cosine_evidence",
    "leg_calibration",
    "merge_profiles",
    "profile_territory",
    "profile_window",
    "read_study_squints",
    "refine_territory",
    "refine_window",
]
