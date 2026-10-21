"""Scan-local squint profiles and exact count comparisons.

The reader retains the physical squint and its source ``Series`` for the
duration of one study operation. Profiles are small count tables; they do not
contain dense pixel vectors or copied study volumes.
"""

from __future__ import annotations

import json
import math
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

from knee.collapse.physical import PlaneFrame, physical_squint
from knee.collapse.squint_stack import SquintStack, read_squint_stack, tile_centres_lps
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


def refine_window(
    series: dict[str, Any],
    window: tuple[int, int, int, int, int, int],
    *,
    subject: str,
    tile_mm: float = 2.0,
) -> dict[str, Any]:
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
        "metric_codes": fine_codes,
        "calibration": coarse_calibration,
        "view": view,
        "source": source,
    }
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
    if source.get("procedure") != _PROCEDURE:
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
            "procedure": _PROCEDURE,
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
    "merge_profiles",
    "profile_window",
    "read_study_squints",
    "refine_window",
]
