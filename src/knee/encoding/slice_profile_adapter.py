from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from knee.encoding.binding_sources import (
    record_context_place_reading,
    unread_place_reading,
)
from knee.encoding.places import (
    CompiledLayout,
    MetricKind,
    NumericReference,
    PlaceReading,
    encode_places,
)
from knee.encoding.scoped import ScopedEncoding
from knee.receipt import digest


def _status_word_values(
    status_codes: Mapping[str, Any],
    measured_status_names: Sequence[str],
    statuses: np.ndarray,
) -> tuple[str, list[str | None], np.ndarray | None]:
    """Decode retained integer statuses without turning unmeasured into absence."""
    if (
        statuses.ndim != 1
        or statuses.dtype.kind not in "iu"
        or not isinstance(status_codes, Mapping)
        or not isinstance(measured_status_names, (list, tuple))
    ):
        return "status_payload_invalid", [], None
    if any(
        not isinstance(name, str)
        or not name
        or not isinstance(code, int)
        or isinstance(code, bool)
        for name, code in status_codes.items()
    ) or len(set(status_codes.values())) != len(status_codes):
        return "status_contract_invalid", [], None
    if any(name not in status_codes for name in measured_status_names):
        return "status_contract_invalid", [], None
    names_by_code = {code: name for name, code in status_codes.items()}
    selected_names = [names_by_code.get(int(code)) for code in statuses]
    if any(name is None for name in selected_names):
        return "status_code_unrecognized", selected_names, None
    available = np.isin(
        statuses, [status_codes[name] for name in measured_status_names]
    )
    return "ok", selected_names, available


def slice_profile_layout_problem(declaration: object) -> str | None:
    """Validate the explicit source contract before the study opens arrays."""
    fields = {
        "family",
        "support",
        "values",
        "status",
        "status_codes",
        "measured_status_names",
        "unit",
        "scope",
    }
    if not isinstance(declaration, Mapping) or set(declaration) != fields:
        return "slice_profile_declaration_invalid"
    if declaration["family"] != "native_slice_profile_values":
        return "unsupported_slice_profile_family"
    if any(
        not isinstance(declaration[name], str) or not declaration[name].strip()
        for name in ("support", "values", "status", "unit", "scope")
    ):
        return "slice_profile_declaration_invalid"
    codes = declaration["status_codes"]
    measured = declaration["measured_status_names"]
    if (
        not isinstance(codes, Mapping)
        or not codes
        or any(
            not isinstance(name, str)
            or not name
            or not isinstance(value, int)
            or isinstance(value, bool)
            for name, value in codes.items()
        )
        or len(set(codes.values())) != len(codes)
        or not isinstance(measured, (list, tuple))
        or not measured
        or any(not isinstance(name, str) or name not in codes for name in measured)
        or len(set(measured)) != len(measured)
    ):
        return "slice_profile_declaration_invalid"
    return None


def encode_slice_profile_observation(
    record: Mapping[str, Any],
    observation: Mapping[str, Any],
    arrays: Mapping[str, np.ndarray],
    layout: CompiledLayout,
    bindings: Sequence[Mapping[str, Any]],
    references: Mapping[tuple[str, str], NumericReference],
    declaration: Mapping[str, Any],
    *,
    verified_arrays: dict[tuple[str, str], np.ndarray] | None = None,
) -> ScopedEncoding:
    """Encode one native profile observation at its listed, actual slice indices.

    The declaration supplies a full-depth numeric vector, a parallel integer status
    vector with named status meanings, the measured status names, a physical unit
    and the producer's scope. The observation's ``slices`` are the only places encoded.
    This function deliberately supplies no RC/LPS point: a plane profile is addressed
    by slice, not by a fabricated representative pixel or object centroid.
    """
    initial_view = record.get("view")
    metadata: dict[str, Any] = {
        "observation": dict(observation),
        "bindings": [dict(binding) for binding in bindings],
        "address_kind": "series_slice",
        "declaration": dict(declaration),
        "source_refs": {},
        "context_sources": [],
        "unread_sources": [],
        "scope_address": {
            "series_uid": record.get("series_uid"),
            "view": list(initial_view)
            if isinstance(initial_view, (list, tuple))
            else None,
            "axis": "native_series_slice_index",
            "measurement": declaration.get("values"),
        },
    }

    def refused(code: str, detail: str = "") -> ScopedEncoding:
        metadata["detail"] = detail
        return ScopedEncoding(code, None, None, "series_slice", metadata)

    problem = slice_profile_layout_problem(declaration)
    if problem is not None:
        return refused(problem)
    support_name = declaration.get("support")
    value_name = declaration.get("values")
    status_name = declaration.get("status")
    unit = declaration.get("unit")
    scope = declaration.get("scope")
    status_codes = declaration["status_codes"]
    measured_names = declaration["measured_status_names"]
    if (
        observation.get("object") is None
        or observation.get("provenance") != "native"
        or observation.get("kind") not in ("resolved", "reading")
        or observation.get("support") != support_name
    ):
        return refused("unsupported_slice_profile_observation")
    if (
        not isinstance(record.get("study_uid"), str)
        or observation.get("artifact") != record.get("artifact")
        or observation.get("series_uid") != record.get("series_uid")
    ):
        return refused("slice_profile_owner_mismatch")
    observation_view, record_view = observation.get("view"), record.get("view")
    if (
        not isinstance(observation_view, (list, tuple))
        or not isinstance(record_view, (list, tuple))
        or tuple(observation_view) != tuple(record_view)
    ):
        return refused("slice_profile_view_mismatch")
    raw_slices = observation.get("slices")
    if (
        not isinstance(raw_slices, (list, tuple))
        or not raw_slices
        or any(
            not isinstance(index, int) or isinstance(index, bool) or index < 0
            for index in raw_slices
        )
        or len(set(raw_slices)) != len(raw_slices)
    ):
        return refused("slice_profile_address_invalid")
    try:
        slice_indices = np.asarray(raw_slices, dtype=np.int64)
    except (OverflowError, ValueError):
        return refused("slice_profile_address_out_of_range")
    scope_address = {
        "series_uid": record.get("series_uid"),
        "view": list(record_view),
        "axis": "native_series_slice_index",
        "measurement": value_name,
    }
    metadata["scope_address"] = scope_address

    loaded: dict[str, np.ndarray] = {}
    source_refs: dict[str, dict[str, Any]] = metadata["source_refs"]

    def read(name: object) -> np.ndarray:
        if not isinstance(name, str) or not name:
            raise ValueError("slice_profile_array_name_invalid")
        if name in loaded:
            return loaded[name]
        if name not in arrays:
            raise ValueError("slice_profile_array_missing:" + name)
        descriptors = record.get("arrays")
        if not isinstance(descriptors, Mapping):
            raise TypeError("slice_profile_array_descriptors_invalid")
        descriptor = descriptors.get(name)
        if not isinstance(descriptor, Mapping):
            raise TypeError("slice_profile_digest_missing:" + name)
        expected = descriptor.get("digest")
        if not isinstance(expected, str):
            raise TypeError("slice_profile_digest_missing:" + name)
        cache_key = (name, expected)
        if verified_arrays is not None and cache_key in verified_arrays:
            value = verified_arrays[cache_key]
        else:
            value = arrays[name]
            if digest(value) != expected:
                raise ValueError("slice_profile_digest_mismatch:" + name)
            if verified_arrays is not None:
                verified_arrays[cache_key] = value
        loaded[name] = value
        source_refs[name] = {
            "artifact": record.get("artifact"),
            "digest": expected,
            "shape": list(value.shape),
            "dtype": value.dtype.str,
        }
        return value

    value_vector: np.ndarray | None = None
    status_vector: np.ndarray | None = None
    selected_status_names: list[str | None] | None = None
    readings: dict[tuple[str, str], PlaceReading] = {}
    for binding in bindings:
        if not isinstance(binding, Mapping):
            return refused("slice_profile_binding_invalid")
        bank, metric_name = binding.get("bank"), binding.get("metric")
        if (
            not isinstance(bank, str)
            or not bank
            or not isinstance(metric_name, str)
            or not metric_name
        ):
            return refused("slice_profile_binding_invalid")
        key = (bank, metric_name)
        if key in readings:
            return refused("duplicate_measurement_binding")
        metric_spec = next(
            (
                metric
                for bank_spec in layout.banks
                if bank_spec.name == bank
                for metric in bank_spec.metrics
                if metric.name == metric_name
            ),
            None,
        )
        if metric_spec is None:
            return refused("unknown_slice_profile_metric")
        source = binding.get("source", "array")
        source_address = {
            "study_uid": record.get("study_uid"),
            "series_uid": record.get("series_uid"),
            "view": list(record_view),
            "artifact": record.get("artifact"),
            "support": support_name,
            "slice_indices": [int(index) for index in raw_slices],
            "unit": unit,
            "scope": scope,
        }
        if source == "unread":
            try:
                reading, unread_item = unread_place_reading(
                    binding, metric_spec, len(slice_indices), source_address
                )
            except ValueError as error:
                return refused(str(error).split(":", 1)[0], str(error))
            readings[key] = reading
            metadata["unread_sources"].append(unread_item)
            continue
        if source == "record_context":
            context_scope = binding.get("scope")
            if context_scope == "record_plane" and (
                len(slice_indices) != 1
                or record.get("slice_index") != int(slice_indices[0])
            ):
                return refused("context_record_plane_slice_mismatch")
            if context_scope == "acquisition" and tuple(record_view) != tuple(
                observation_view
            ):
                return refused("context_acquisition_view_mismatch")
            try:
                reading, context_item = record_context_place_reading(
                    binding, metric_spec, len(slice_indices), record, source_address
                )
            except ValueError as error:
                return refused(str(error).split(":", 1)[0], str(error))
            readings[key] = reading
            metadata["context_sources"].append(context_item)
            continue
        if source == "status_words":
            if metric_spec.kind is not MetricKind.WORDS:
                return refused("slice_profile_status_words_metric_must_be_words")
            try:
                if status_vector is None:
                    status_vector = read(status_name)
            except (
                KeyError,
                TypeError,
                ValueError,
                IndexError,
                OSError,
                OverflowError,
            ) as error:
                return refused("slice_profile_source_unavailable", str(error))
            if (
                status_vector.ndim != 1
                or status_vector.dtype.kind not in "iu"
                or (
                    slice_indices.size
                    and int(slice_indices.max()) >= status_vector.size
                )
            ):
                return refused("slice_profile_payload_shape_invalid")
            statuses = status_vector[slice_indices]
            status_code, selected_status_names, available = _status_word_values(
                status_codes, measured_names, statuses
            )
            if status_code == "status_code_unrecognized":
                return refused("slice_profile_status_code_unrecognized")
            if status_code != "ok" or available is None:
                return refused("slice_profile_declaration_invalid")
            status_words = np.asarray(selected_status_names, dtype=np.str_)
            readings[key] = PlaceReading(bank, metric_name, status_words, available)
            metadata["status_word_source"] = {
                "array": status_name,
                "source_ref": source_refs.get(status_name),
                "codes": dict(status_codes),
                "measured_status_names": list(measured_names),
                "selected_status_names": list(selected_status_names),
                "unit": unit,
                "scope": scope,
            }
            continue
        if source != "array":
            return refused("slice_profile_binding_invalid")
        if metric_spec.kind is not MetricKind.DIGIT:
            return refused("slice_profile_array_metric_must_be_numeric")
        if (
            binding.get("value") != value_name
            or binding.get("available") != status_name
        ):
            return refused("slice_profile_binding_array_not_declared")
        try:
            if value_vector is None:
                value_vector = read(value_name)
            if status_vector is None:
                status_vector = read(status_name)
        except (
            KeyError,
            TypeError,
            ValueError,
            IndexError,
            OSError,
            OverflowError,
        ) as error:
            return refused("slice_profile_source_unavailable", str(error))
        if (
            value_vector.ndim != 1
            or value_vector.dtype.kind not in "iuf"
            or status_vector.ndim != 1
            or status_vector.dtype.kind not in "iu"
            or value_vector.shape != status_vector.shape
            or (slice_indices.size and int(slice_indices.max()) >= value_vector.size)
        ):
            return refused("slice_profile_payload_shape_invalid")
        statuses = status_vector[slice_indices]
        status_code, selected_status_names, available = _status_word_values(
            status_codes, measured_names, statuses
        )
        if status_code == "status_code_unrecognized":
            return refused("slice_profile_status_code_unrecognized")
        if status_code != "ok" or available is None:
            return refused("slice_profile_declaration_invalid")
        if not bool(np.all(available)):
            return refused("slice_profile_address_includes_unmeasured_sample")
        values = np.asarray(value_vector[slice_indices]).copy()
        available = np.asarray(available, dtype=np.bool_)
        readings[key] = PlaceReading(bank, metric_name, values, available)

    if set(readings) != {
        (bank.name, metric.name) for bank in layout.banks for metric in bank.metrics
    }:
        return refused("slice_profile_bindings_incomplete")
    encoded = encode_places(layout, readings, references)
    metadata.update(
        source_address={
            "study_uid": record.get("study_uid"),
            "series_uid": record.get("series_uid"),
            "view": list(record_view),
            "artifact": record.get("artifact"),
            "support": support_name,
            "slice_indices": [int(index) for index in raw_slices],
            "unit": unit,
            "scope": scope,
        },
        place_count=len(slice_indices),
        slice_indices=slice_indices.tolist(),
        value_array=value_name if value_vector is not None else None,
        status_array=status_name if status_vector is not None else None,
        status_codes=dict(status_codes),
        measured_status_names=list(measured_names),
        selected_status_names=selected_status_names,
        meaning="per-slice scalar readings; no plane pixels or physical volume",
    )
    coordinates = slice_indices.reshape((-1, 1)).copy()
    coordinates.flags.writeable = False
    return ScopedEncoding(
        encoded.status.value, encoded, coordinates, "series_slice", metadata
    )
