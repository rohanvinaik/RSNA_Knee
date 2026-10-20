"""Source-only helpers shared by addressed measurement adapters."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from knee.encoding.places import MetricKind, MetricSpec, PlaceReading


def unread_place_reading(
    binding: Mapping[str, Any],
    metric: MetricSpec,
    count: int,
    source_address: Mapping[str, Any],
) -> tuple[PlaceReading, dict[str, Any]]:
    """Return an explicitly unavailable row vector without reading source data."""
    bank, metric_name = binding.get("bank"), binding.get("metric")
    reason = binding.get("reason")
    if (
        not isinstance(bank, str)
        or not bank
        or not isinstance(metric_name, str)
        or not metric_name
        or not isinstance(reason, str)
        or not reason.strip()
        or not isinstance(count, int)
        or isinstance(count, bool)
        or count < 0
    ):
        raise ValueError("invalid_unread_binding")

    placeholder = (
        np.asarray(0.0, dtype=np.float64)
        if metric.kind is MetricKind.DIGIT
        else np.asarray("", dtype="U1")
    )
    values = np.broadcast_to(placeholder, (count,))
    available = np.broadcast_to(np.asarray(False), (count,))
    reading = PlaceReading(bank, metric_name, values, available)
    metadata = {
        "bank": bank,
        "metric": metric_name,
        "source": "unread",
        "reason": reason,
        "status": "unread",
        "source_address": dict(source_address),
    }
    return reading, metadata


def record_context_place_reading(
    binding: Mapping[str, Any],
    metric: MetricSpec,
    count: int,
    record: Mapping[str, Any],
    source_address: Mapping[str, Any],
) -> tuple[PlaceReading, dict[str, Any]]:
    """Read one declared scalar record path and broadcast it across places.

    Adapters validate identity and scope before calling this function. This
    helper only traverses the explicit path, checks scalar compatibility, and
    creates zero-stride value/availability views; it never reads an array.
    """
    bank, metric_name = binding.get("bank"), binding.get("metric")
    path = binding.get("path")
    scope = binding.get("scope")
    if (
        not isinstance(bank, str)
        or not bank
        or not isinstance(metric_name, str)
        or not metric_name
        or not isinstance(path, list)
        or not path
        or any(
            not isinstance(part, str)
            and not (isinstance(part, int) and not isinstance(part, bool) and part >= 0)
            for part in path
        )
        or scope not in ("acquisition", "record_plane")
        or not isinstance(metric, MetricSpec)
        or not isinstance(record, Mapping)
        or not isinstance(source_address, Mapping)
        or not isinstance(count, int)
        or isinstance(count, bool)
        or count < 0
    ):
        raise ValueError("invalid_context_path")

    current: object = record
    found = True
    for part in path:
        if isinstance(current, Mapping) and isinstance(part, str):
            if part not in current:
                found, current = False, None
                break
            current = current[part]
        elif (
            isinstance(current, (list, tuple))
            and isinstance(part, int)
            and not isinstance(part, bool)
            and 0 <= part < len(current)
        ):
            current = current[part]
        else:
            found, current = False, None
            break

    reason: str | None = None
    if not found:
        reason = "context_path_unavailable"
    elif current is None:
        reason = "context_value_null"
    elif not isinstance(current, (str, bool, int, float)):
        raise ValueError("context_value_not_scalar")
    elif isinstance(current, float) and not np.isfinite(current):
        reason = "context_value_nonfinite"

    if reason is None:
        if metric.kind is MetricKind.DIGIT:
            if isinstance(current, bool) or not isinstance(current, (int, float)):
                raise ValueError("context_scalar_metric_type_mismatch")
            try:
                scalar = np.asarray(
                    current, dtype=np.int64 if isinstance(current, int) else np.float64
                )
            except OverflowError as error:
                raise ValueError("context_numeric_out_of_range") from error
        elif isinstance(current, bool):
            scalar = np.asarray(current, dtype=np.bool_)
        elif isinstance(current, str):
            scalar = np.asarray(current)
        else:
            raise ValueError("context_scalar_metric_type_mismatch")
        values = np.broadcast_to(scalar, (count,))
        available = np.broadcast_to(np.asarray(True), (count,))
        metadata = {
            "bank": bank,
            "metric": metric_name,
            "source": "record_context",
            "path": list(path),
            "scope": scope,
            "source_address": dict(source_address),
            "status": "available",
            "value": current,
            "scalar_type": type(current).__name__,
        }
    else:
        placeholder = (
            np.asarray(0.0, dtype=np.float64)
            if metric.kind is MetricKind.DIGIT
            else np.asarray(False, dtype=np.bool_)
        )
        values = np.broadcast_to(placeholder, (count,))
        available = np.broadcast_to(np.asarray(False), (count,))
        metadata = {
            "bank": bank,
            "metric": metric_name,
            "source": "record_context",
            "path": list(path),
            "scope": scope,
            "source_address": dict(source_address),
            "status": "unavailable",
            "reason": reason,
            "value": None,
            "scalar_type": type(current).__name__ if current is not None else None,
        }
    return PlaceReading(bank, metric_name, values, available), metadata
