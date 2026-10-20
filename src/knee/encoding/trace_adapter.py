"""Strict encoder adapter for retained posterior-trace points.

Trace coordinates are kept as their original LPS points. They are not rasterized
or interpreted as a mask. Numeric trace readings require explicit references.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeGuard

import numpy as np

from knee.encoding.binding_sources import (
    record_context_place_reading,
    unread_place_reading,
)
from knee.encoding.places import (
    CompiledLayout,
    EncodingResult,
    NumericReference,
    PlaceReading,
    encode_places,
)
from knee.receipt import digest


@dataclass(frozen=True, slots=True)
class TraceEncoding:
    status: str
    encoding: EncodingResult | None
    points_lps: np.ndarray | None
    metadata: dict[str, Any]


class _SourceError(ValueError):
    pass


def _plain_index(value: object) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


def _artifact_matches_owner(owner: dict, artifact: object) -> bool:
    if not isinstance(owner, Mapping):
        return False
    if not isinstance(artifact, str) or owner.get("artifact") != artifact:
        return False
    uid = owner.get("series_uid")
    if not isinstance(uid, str) or not uid:
        return False
    main_slice = owner.get("main_slice")
    if main_slice is not None and not isinstance(main_slice, Mapping):
        return False
    part = None if main_slice is None else main_slice.get("object")
    stem = uid if part is None else f"{uid}-{part}"
    return Path(artifact).name in (f"{stem}.npz", f"{stem}.npz.xz")


def encode_trace_observation(
    target_record: dict,
    owner_record: dict,
    observation: dict,
    arrays: Mapping[str, np.ndarray],
    layout: CompiledLayout,
    bindings: Sequence[dict],
    references: Mapping[tuple[str, str], NumericReference],
    *,
    verified_arrays: dict[tuple[str, str], np.ndarray] | None = None,
) -> TraceEncoding:
    """Encode numeric measurements at one retained trace's exact patient-LPS points.

    `target_record` owns the Observation row; `owner_record` owns the artifact
    named by that Observation. Array bindings are `{bank, metric, value}` and
    the value must be the row-aligned retained `light` or `flank` vector. A
    point is available exactly when its retained reading is finite. Explicit
    unread bindings create unavailable rows without loading an array.
    """
    metadata: dict[str, Any] = {}

    def refused(code: str, detail: str = "") -> TraceEncoding:
        return TraceEncoding(code, None, None, {**metadata, "detail": detail})

    if not isinstance(observation, Mapping):
        return refused("invalid_trace_observation")
    if not isinstance(bindings, Sequence) or isinstance(bindings, (str, bytes)):
        return refused("invalid_trace_bindings")
    metadata.update(observation=dict(observation), bindings=list(bindings))
    if not isinstance(target_record, Mapping) or not isinstance(owner_record, Mapping):
        return refused("invalid_trace_records")
    if (
        observation.get("provenance") != "native"
        or observation.get("kind") != "reading"
        or observation.get("label") is not None
    ):
        return refused("unsupported_trace_observation")
    if observation.get("series_uid") != target_record.get("series_uid"):
        return refused("target_series_mismatch")
    observation_view = observation.get("view")
    target_view = target_record.get("view")
    if (
        not isinstance(observation_view, (tuple, list))
        or len(observation_view) != 3
        or any(not isinstance(item, str) for item in observation_view)
        or not isinstance(target_view, (tuple, list))
        or len(target_view) != 3
        or any(not isinstance(item, str) for item in target_view)
        or tuple(observation_view) != tuple(target_view)
    ):
        return refused("target_view_mismatch")
    if target_record.get("study_uid") != owner_record.get("study_uid"):
        return refused("source_study_mismatch")
    if not _artifact_matches_owner(owner_record, observation.get("artifact")):
        return refused("source_artifact_owner_mismatch")
    support = observation.get("support")
    if (
        not isinstance(support, str)
        or not support.startswith("a3_posterior_trace_")
        or not support.endswith("_points_lps")
    ):
        return refused("unsupported_trace_support")
    prefix = support[: -len("_points_lps")]
    if observation.get("object") != prefix.removeprefix("a3_posterior_trace_"):
        return refused("trace_support_object_mismatch")
    slices = observation.get("slices")
    if (
        not isinstance(slices, (list, tuple))
        or len(slices) != 1
        or not _plain_index(slices[0])
        or slices[0] < 0
    ):
        return refused("invalid_target_slice_address")
    row = observation.get("row")
    if not _plain_index(row) or row < 0:
        return refused("invalid_trace_row")

    loaded: dict[str, np.ndarray] = {}
    source_refs: dict[str, dict[str, Any]] = {}
    unread_sources: list[dict[str, Any]] = []
    context_sources: list[dict[str, Any]] = []

    def read(name: object) -> np.ndarray:
        if not isinstance(name, str) or not name:
            raise _SourceError("missing_array_name")
        if name in loaded:
            return loaded[name]
        if name not in arrays:
            raise _SourceError("missing_array:" + name)
        descriptors = owner_record.get("arrays")
        if not isinstance(descriptors, Mapping):
            raise _SourceError("missing_array_descriptors")
        descriptor = descriptors.get(name)
        if not isinstance(descriptor, Mapping):
            raise _SourceError("missing_digest:" + name)
        expected = descriptor.get("digest")
        if not isinstance(expected, str):
            raise _SourceError("missing_digest:" + name)
        cache_key = (name, expected)
        if verified_arrays is not None and cache_key in verified_arrays:
            value = verified_arrays[cache_key]
        else:
            value = arrays[name]
            if digest(value) != expected:
                raise _SourceError("digest_mismatch:" + name)
            if verified_arrays is not None:
                verified_arrays[cache_key] = value
        loaded[name] = value
        source_refs[name] = {
            "artifact": owner_record["artifact"],
            "digest": expected,
            "shape": list(value.shape),
            "dtype": value.dtype.str,
        }
        return value

    try:
        points_all = read(support)
        offsets = read(f"{prefix}_offsets")
        slices_all = read(f"{prefix}_slices")
        starts = read(f"{prefix}_starts")
        stops = read(f"{prefix}_stops")
        if (
            points_all.ndim != 2
            or points_all.shape[1:] != (3,)
            or points_all.dtype.kind not in "fi"
            or offsets.ndim != 1
            or offsets.dtype.kind not in "iu"
            or slices_all.ndim != 1
            or slices_all.dtype.kind not in "iu"
            or starts.ndim != 1
            or starts.dtype.kind not in "iu"
            or stops.ndim != 2
            or stops.shape[1:] != (2,)
            or stops.dtype.kind not in "iu"
        ):
            return refused("invalid_trace_arrays")
        trace_count = len(slices_all)
        if (
            len(offsets) != trace_count + 1
            or len(starts) != trace_count
            or len(stops) != trace_count
            or int(offsets[0]) != 0
            or int(offsets[-1]) != len(points_all)
            or np.any(offsets[1:] < offsets[:-1])
        ):
            return refused("invalid_trace_offsets")
        if row >= trace_count:
            return refused("trace_row_out_of_range")
        if int(slices_all[row]) != slices[0]:
            return refused("trace_slice_mismatch")
        begin, end = int(offsets[row]), int(offsets[row + 1])
        points = points_all[begin:end]
        count = end - begin
        declared_count = observation.get("count")
        if (
            not _plain_index(declared_count)
            or declared_count < 0
            or declared_count != count
        ):
            return refused("trace_count_mismatch")
        if not np.all(np.isfinite(points)):
            return refused("nonfinite_trace_point")

        from knee.collapse.posterior import FOLLOWED, START_NAMES, STOP_NAMES

        start_code = int(starts[row])
        if not 0 <= start_code < len(START_NAMES):
            return refused("invalid_trace_start_code")
        expected_code = (
            "tube_followed"
            if START_NAMES[start_code] == FOLLOWED
            else START_NAMES[start_code]
        )
        if observation.get("code") != expected_code:
            return refused("trace_start_code_mismatch")
        if np.any(stops[row] < 0) or np.any(stops[row] >= len(STOP_NAMES)):
            return refused("invalid_trace_stop_codes")

        readings: dict[tuple[str, str], PlaceReading] = {}
        for binding in bindings:
            if not isinstance(binding, Mapping):
                return refused("invalid_trace_measurement_binding")
            bank, metric = binding.get("bank"), binding.get("metric")
            if (
                not isinstance(bank, str)
                or not bank
                or not isinstance(metric, str)
                or not metric
            ):
                return refused("invalid_trace_measurement_binding")
            key = (bank, metric)
            if key in readings:
                return refused("invalid_trace_measurement_binding")
            if binding.get("source") == "unread":
                metric_spec = next(
                    (
                        item
                        for bank_spec in layout.banks
                        if bank_spec.name == bank
                        for item in bank_spec.metrics
                        if item.name == metric
                    ),
                    None,
                )
                if metric_spec is None:
                    return refused("unknown_trace_metric")
                if any(
                    field in binding
                    for field in ("value", "available", "window", "path", "scope")
                ):
                    return refused("invalid_unread_binding")
                reading, unread_metadata = unread_place_reading(
                    binding,
                    metric_spec,
                    count,
                    {
                        "owner_artifact": owner_record.get("artifact"),
                        "owner_series_uid": owner_record.get("series_uid"),
                        "target_series_uid": target_record.get("series_uid"),
                        "target_view": list(observation_view),
                        "support": support,
                        "row": row,
                        "slice_index": slices[0],
                    },
                )
                readings[key] = reading
                unread_sources.append(unread_metadata)
                continue
            if binding.get("source") == "record_context":
                metric_spec = next(
                    (
                        item
                        for bank_spec in layout.banks
                        if bank_spec.name == bank
                        for item in bank_spec.metrics
                        if item.name == metric
                    ),
                    None,
                )
                if metric_spec is None:
                    return refused("unknown_trace_metric")
                path = binding.get("path")
                scope = binding.get("scope")
                if (
                    not isinstance(path, list)
                    or not path
                    or any(
                        not isinstance(part, str)
                        and not (
                            isinstance(part, int)
                            and not isinstance(part, bool)
                            and part >= 0
                        )
                        for part in path
                    )
                ):
                    return refused("invalid_trace_context_path")
                if scope == "record_plane":
                    if target_record.get("slice_index") != slices[0]:
                        return refused("context_record_plane_slice_mismatch")
                elif scope == "acquisition":
                    if tuple(target_record.get("view", ())) != tuple(observation_view):
                        return refused("context_acquisition_view_mismatch")
                else:
                    return refused("invalid_trace_context_scope")
                source_address = {
                    "series_uid": target_record.get("series_uid"),
                    "view": target_record.get("view"),
                    "slice_index": target_record.get("slice_index"),
                    "trace_slice_index": slices[0],
                    "artifact": target_record.get("artifact"),
                    "owner_series_uid": owner_record.get("series_uid"),
                    "owner_artifact": owner_record.get("artifact"),
                }
                try:
                    reading, context_item = record_context_place_reading(
                        binding, metric_spec, count, target_record, source_address
                    )
                except ValueError as error:
                    return refused(str(error).split(":", 1)[0], str(error))
                readings[key] = reading
                context_sources.append(context_item)
                continue
            value_name = binding.get("value")
            if (
                binding.get("source", "array") != "array"
                or not isinstance(value_name, str)
                or not value_name
                or value_name not in (f"{prefix}_light", f"{prefix}_flank")
            ):
                return refused("invalid_trace_measurement_binding")
            values = read(value_name)
            if (
                values.ndim != 1
                or values.shape != (len(points_all),)
                or values.dtype.kind not in "iuf"
            ):
                return refused("invalid_trace_measurement_values")
            local = values[begin:end]
            available = np.isfinite(local)
            readings[key] = PlaceReading(bank, metric, local, available)
        encoded = encode_places(layout, readings, references)
    except _SourceError as error:
        return refused(str(error).split(":", 1)[0], str(error))
    except (KeyError, TypeError, ValueError, IndexError) as error:
        return refused("invalid_trace_data", str(error))

    points.flags.writeable = False
    metadata.update(
        source_refs=source_refs,
        unread_sources=unread_sources,
        context_sources=context_sources,
        owner_series_uid=owner_record.get("series_uid"),
        target_series_uid=target_record.get("series_uid"),
        row=row,
        slice_index=slices[0],
        point_count=count,
        target_count=declared_count,
        start_name=START_NAMES[start_code],
        stop_codes=list(map(int, stops[row])),
        stop_names=[STOP_NAMES[int(code)] for code in stops[row]],
        addresses="patient_lps_points",
        meaning="per-point trace readings at retained coordinates; no mask or volume",
    )
    return TraceEncoding(encoded.status.value, encoded, points, metadata)
