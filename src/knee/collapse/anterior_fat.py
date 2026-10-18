from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isfinite
from numbers import Real
from typing import Any

import numpy as np
from scipy import ndimage as ndi


@dataclass(frozen=True)
class NativeGradientTerritories:
    gradient_magnitude: np.ndarray
    gradient_u16: np.ndarray
    gradient_valid: np.ndarray
    marker_ids: np.ndarray
    conflicts: np.ndarray
    labels: np.ndarray
    unknown: np.ndarray
    marker_codes: dict[str, int]
    marker_counts: dict[str, int]
    gradient_facts: dict[str, Any]


def _mask(value: object, shape: tuple[int, int], name: str) -> np.ndarray:
    result = np.asarray(value)
    if result.shape != shape or result.dtype.kind != "b":
        raise ValueError(f"{name}_must_be_boolean_with_target_shape")
    return result.astype(bool, copy=False)


def _spacing(value: Sequence[float]) -> tuple[float, float]:
    try:
        items = tuple(value)
    except TypeError as error:
        raise ValueError("spacing_rc_mm_must_contain_two_positive_numbers") from error
    if len(items) != 2:
        raise ValueError("spacing_rc_mm_must_contain_two_positive_numbers")
    converted: list[float] = []
    for item in items:
        if not isinstance(item, Real) or isinstance(item, (bool, np.bool_)):
            raise TypeError("spacing_rc_mm_must_contain_two_positive_numbers")
        number = float(item)
        if not isfinite(number) or number <= 0.0:
            raise ValueError("spacing_rc_mm_must_contain_two_positive_numbers")
        converted.append(number)
    return converted[0], converted[1]


def _axis_derivative(
    values: np.ndarray, valid: np.ndarray, spacing: float, axis: int
) -> tuple[np.ndarray, np.ndarray]:
    length = values.shape[axis]
    derivative = np.zeros(values.shape, dtype=np.float64)
    derivative_valid = np.zeros(values.shape, dtype=bool)
    if length < 2:
        return derivative, derivative_valid

    first = [slice(None), slice(None)]
    second = [slice(None), slice(None)]
    first[axis] = 0
    second[axis] = 1
    first_index, second_index = tuple(first), tuple(second)
    derivative[first_index] = (values[second_index] - values[first_index]) / spacing
    derivative_valid[first_index] = valid[first_index] & valid[second_index]

    first[axis] = length - 2
    second[axis] = length - 1
    first_index, second_index = tuple(first), tuple(second)
    derivative[second_index] = (values[second_index] - values[first_index]) / spacing
    derivative_valid[second_index] = valid[first_index] & valid[second_index]

    if length > 2:
        center = [slice(None), slice(None)]
        before = [slice(None), slice(None)]
        after = [slice(None), slice(None)]
        center[axis] = slice(1, length - 1)
        before[axis] = slice(0, length - 2)
        after[axis] = slice(2, length)
        center_index, before_index, after_index = (
            tuple(center),
            tuple(before),
            tuple(after),
        )
        derivative[center_index] = (values[after_index] - values[before_index]) / (
            2.0 * spacing
        )
        derivative_valid[center_index] = valid[before_index] & valid[after_index]
    return derivative, derivative_valid


def _quantize_gradient(
    raw: np.ndarray, available: np.ndarray, spacing: tuple[float, float]
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    finite_signal = np.isfinite(raw)
    signal_valid = available & finite_signal
    safe = np.where(signal_valid, raw, 0.0).astype(np.float64, copy=False)
    row_derivative, row_valid = _axis_derivative(safe, signal_valid, spacing[0], 0)
    col_derivative, col_valid = _axis_derivative(safe, signal_valid, spacing[1], 1)
    gradient_valid = signal_valid & row_valid & col_valid
    magnitude = np.zeros(raw.shape, dtype=np.float64)
    magnitude[gradient_valid] = np.hypot(
        row_derivative[gradient_valid], col_derivative[gradient_valid]
    )
    gradient_u16 = np.zeros(raw.shape, dtype=np.uint16)
    if gradient_valid.any():
        low = float(magnitude[gradient_valid].min())
        high = float(magnitude[gradient_valid].max())
        if high > low:
            # Reserve uint16's maximum as a barrier for disconnected components.
            scaled = (magnitude[gradient_valid] - low) * (65534.0 / (high - low))
            gradient_u16[gradient_valid] = (
                np.rint(scaled).clip(0, 65535).astype(np.uint16)
            )
    else:
        low = high = None
    digest = hashlib.sha256(np.ascontiguousarray(gradient_u16).tobytes()).hexdigest()
    facts = {
        "definition": "Euclidean magnitude of row and column finite differences on acquired valid neighbors, divided by actual row and column spacing in mm",
        "spacing_rc_mm": [spacing[0], spacing[1]],
        "valid_pixel_count": int(gradient_valid.sum()),
        "magnitude_min": low,
        "magnitude_max": high,
        "quantization": "linear per-frame valid-gradient min/max to uint16 values 0..65534, round-to-nearest; 65535 is reserved as the disconnected-domain barrier; invalid gradient pixels are stored as 0 and excluded from min/max",
        "gradient_u16_sha256": digest,
    }
    return magnitude, gradient_u16, gradient_valid, facts


def _native_watershed(
    gradient: np.ndarray,
    valid: np.ndarray,
    markers: np.ndarray,
    conflicts: np.ndarray,
) -> tuple[np.ndarray, int, int]:
    """Apply SciPy IFT independently to seeded 4-connected valid components."""
    domain = valid & ~conflicts
    components, component_count = ndi.label(
        domain, structure=ndi.generate_binary_structure(2, 1)
    )
    labels = np.zeros(gradient.shape, dtype=np.int32)
    component_slices = ndi.find_objects(components, max_label=component_count)
    seeded_components = 0
    unseeded_components = 0
    barrier = np.iinfo(np.uint16).max

    for component_id, bounds in enumerate(component_slices, start=1):
        if bounds is None:
            continue
        region = components[bounds] == component_id
        local_markers = np.where(region, markers[bounds], 0).astype(np.int32)
        if not np.any(local_markers):
            unseeded_components += 1
            continue

        local_gradient = np.where(region, gradient[bounds], barrier).astype(np.uint16)
        local_labels = ndi.watershed_ift(
            local_gradient,
            local_markers,
            structure=ndi.generate_binary_structure(2, 1),
        )
        output = labels[bounds]
        output[region] = local_labels[region]
        labels[bounds] = output
        seeded_components += 1
    return labels, seeded_components, unseeded_components


def native_gradient_territories(
    raw: np.ndarray,
    available: np.ndarray,
    spacing_rc_mm: Sequence[float],
    marker_groups: Mapping[str, np.ndarray],
) -> NativeGradientTerritories:
    """Measure physical gradients and apply SciPy native watershed basins.

    Marker masks are independent groups. Overlapping claims are withheld as
    conflicts. Equal priorities follow SciPy's native marker queue order; this
    function does not claim to detect tied pixels. Invalid neighborhoods and
    conflicts are excluded from the flood domain, and unseeded components remain
    unknown.
    """
    signal = np.asarray(raw)
    if signal.ndim != 2 or signal.dtype.kind not in "iuf":
        raise ValueError("raw_must_be_a_two_dimensional_numeric_array")
    shape = (int(signal.shape[0]), int(signal.shape[1]))
    if min(shape) < 2:
        raise ValueError("raw_dimensions_must_each_be_at_least_two")
    signal_available = _mask(available, shape, "available")
    spacing = _spacing(spacing_rc_mm)
    if not isinstance(marker_groups, Mapping):
        raise TypeError("marker_groups_must_be_a_mapping")

    names = list(marker_groups)
    if any(not isinstance(name, str) or not name for name in names):
        raise ValueError("marker_group_names_must_be_nonempty_strings")
    marker_codes = {name: index + 1 for index, name in enumerate(names)}
    marker_claims = np.zeros(shape, dtype=np.uint32)
    marker_ids = np.zeros(shape, dtype=np.int32)
    conflicts = np.zeros(shape, dtype=bool)
    marker_counts: dict[str, int] = {}
    for name in names:
        group_mask = _mask(marker_groups[name], shape, f"marker_{name}")
        first_claim = group_mask & (marker_claims == 0)
        marker_ids[first_claim] = marker_codes[name]
        conflicts |= group_mask & (marker_claims > 0)
        marker_claims += group_mask.astype(np.uint32)
        marker_counts[name] = int(group_mask.sum())
    marker_ids[conflicts] = 0

    magnitude, gradient_u16, gradient_valid, facts = _quantize_gradient(
        signal, signal_available, spacing
    )
    labels, seeded_components, unseeded_components = _native_watershed(
        gradient_u16, gradient_valid, marker_ids, conflicts
    )
    unknown = ~gradient_valid | conflicts | (labels == 0)
    facts["watershed"] = {
        "primitive": "scipy.ndimage.watershed_ift",
        "connectivity": 4,
        "marker_code_assignment": "1-based codes follow marker_groups mapping insertion order",
        "equal_priority_policy": "native SciPy watershed_ift marker queue order; no tied-pixel detection or added priority rule",
        "valid_connected_components": int(seeded_components + unseeded_components),
        "seeded_components": int(seeded_components),
        "unseeded_components_left_unknown": int(unseeded_components),
    }
    return NativeGradientTerritories(
        gradient_magnitude=magnitude,
        gradient_u16=gradient_u16,
        gradient_valid=gradient_valid,
        marker_ids=marker_ids,
        conflicts=conflicts,
        labels=labels,
        unknown=unknown,
        marker_codes=marker_codes,
        marker_counts=marker_counts,
        gradient_facts=facts,
    )


def fat_compatibility_sets(
    compatible_fields: Sequence[np.ndarray], available_fields: Sequence[np.ndarray]
) -> dict[str, np.ndarray]:
    """Combine per-field fat-compatible classes without hiding disagreement."""
    if len(compatible_fields) != len(available_fields) or not compatible_fields:
        raise ValueError("compatible_and_available_fields_must_be_nonempty_and_paired")
    first = np.asarray(compatible_fields[0])
    if first.ndim != 2 or first.dtype.kind != "b":
        raise ValueError("compatible_fields_must_be_boolean_two_dimensional_arrays")
    shape = (int(first.shape[0]), int(first.shape[1]))
    any_positive = np.zeros(shape, dtype=bool)
    any_negative = np.zeros(shape, dtype=bool)
    any_available = np.zeros(shape, dtype=bool)
    for index, (compatible_value, available_value) in enumerate(
        zip(compatible_fields, available_fields, strict=True)
    ):
        compatible = _mask(compatible_value, shape, f"compatible_{index}")
        available = _mask(available_value, shape, f"available_{index}")
        any_available |= available
        any_positive |= available & compatible
        any_negative |= available & ~compatible
    disagreement = any_positive & any_negative
    unknown = ~any_available
    return {
        "positive": any_positive,
        "negative": any_negative,
        "unknown": unknown,
        "disagreement": disagreement,
        "positive_without_known_negative": any_positive & ~any_negative,
        "negative_without_known_positive": any_negative & ~any_positive,
        "known": any_available,
    }
