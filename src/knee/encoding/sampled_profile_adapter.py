"""Adapter for retained sparse native-plane sample profiles.

This preserves the producer's sampled coordinates and values. It does not
turn samples into a plane mask or infer measurements outside those samples.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np

from knee.encoding.binding_sources import (
    record_context_place_reading,
    unread_place_reading,
)
from knee.encoding.handoff import AddressedEncoding
from knee.encoding.places import (
    CompiledLayout,
    NumericReference,
    PlaceReading,
    encode_places,
)
from knee.receipt import digest


def encode_sampled_profile_observation(
    record: dict,
    observation: dict,
    arrays: Mapping[str, np.ndarray],
    layout: CompiledLayout,
    bindings: Sequence[dict],
    references: Mapping[tuple[str, str], NumericReference],
    declaration: Mapping[str, object],
    *,
    verified_arrays: dict[tuple[str, str], np.ndarray] | None = None,
) -> AddressedEncoding:
    """Encode a row of native sampled values at its exact saved ``(r,c)`` points."""
    metadata: dict = {
        "observation": dict(observation),
        "bindings": list(bindings),
        "address_kind": "native_rc_sample_points",
        "meaning": "sampled native readings only; not a plane mask or boundary",
    }
    context_sources: list[dict] = []
    unread_sources: list[dict] = []
    metadata["context_sources"] = context_sources
    metadata["unread_sources"] = unread_sources

    def refused(code: str, detail: str = "") -> AddressedEncoding:
        return AddressedEncoding(code, None, None, {**metadata, "detail": detail})

    if declaration.get("family") != "joint_axial_profile_samples":
        return refused("unsupported_sample_profile_family")
    if (
        observation.get("object") != "joint"
        or observation.get("provenance") != "native"
        or observation.get("kind") != "reading"
        or observation.get("support") != "a4_joint_axial_profile_white"
    ):
        return refused("unsupported_sample_profile_observation")
    if (
        not isinstance(record.get("study_uid"), str)
        or observation.get("artifact") != record.get("artifact")
        or observation.get("series_uid") != record.get("series_uid")
    ):
        return refused("sample_profile_owner_mismatch")
    view = observation.get("view")
    owner_view = record.get("view")
    if (
        not isinstance(view, (list, tuple))
        or not isinstance(owner_view, (list, tuple))
        or tuple(view) != tuple(owner_view)
        or len(view) != 3
        or str(view[0]).casefold() != "axial"
    ):
        return refused("sample_profile_view_mismatch")
    slices = observation.get("slices")
    row = observation.get("row")
    if (
        not isinstance(slices, (list, tuple))
        or len(slices) != 1
        or not isinstance(slices[0], int)
        or isinstance(slices[0], bool)
        or slices[0] < 0
        or not isinstance(row, int)
        or isinstance(row, bool)
        or row < 0
    ):
        return refused("sample_profile_row_address_invalid")

    names = {
        "offsets": declaration.get("offsets"),
        "slices": declaration.get("slices"),
        "coordinates": declaration.get("coordinates"),
        "valid": declaration.get("valid"),
        "light": declaration.get("light"),
    }
    support_name = declaration.get("white", observation.get("support"))
    names["white"] = support_name
    source_refs: dict[str, dict] = {}
    loaded: dict[str, np.ndarray] = {}

    def read(name: object) -> np.ndarray:
        if not isinstance(name, str) or not name or name not in arrays:
            raise ValueError("sample_profile_array_missing")
        if name in loaded:
            return loaded[name]
        descriptors = record.get("arrays")
        if not isinstance(descriptors, Mapping):
            raise TypeError("sample_profile_array_descriptors_invalid")
        descriptor = descriptors.get(name)
        if not isinstance(descriptor, Mapping):
            raise TypeError("sample_profile_digest_missing")
        expected = descriptor.get("digest")
        if not isinstance(expected, str):
            raise TypeError("sample_profile_digest_missing")
        cache_key = (name, expected)
        if verified_arrays is not None and cache_key in verified_arrays:
            value = verified_arrays[cache_key]
        else:
            value = arrays[name]
            if digest(value) != expected:
                raise ValueError("sample_profile_digest_mismatch")
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

    try:
        offsets = read(names["offsets"])
        row_slices = read(names["slices"])
        coordinates = read(names["coordinates"])
        valid_all = read(names["valid"])
        white_all = read(names["white"])
    except (KeyError, TypeError, ValueError) as error:
        return refused("sample_profile_source_unavailable", str(error))

    if (
        offsets.ndim != 1
        or offsets.dtype.kind not in "iu"
        or row_slices.ndim != 1
        or row_slices.dtype.kind not in "iu"
        or offsets.size != row_slices.size + 1
        or row >= row_slices.size
        or offsets.size == 0
        or int(offsets[0]) != 0
        or np.any(offsets[1:] < offsets[:-1])
    ):
        return refused("sample_profile_offset_shape_invalid")
    stop = int(offsets[-1])
    if (
        coordinates.ndim != 2
        or coordinates.shape[1:] != (2,)
        or coordinates.dtype.kind not in "iu"
        or valid_all.ndim != 1
        or white_all.ndim != 1
        or stop != len(coordinates)
        or stop != len(valid_all)
        or stop != len(white_all)
        or valid_all.dtype.kind != "b"
        or white_all.dtype.kind != "b"
    ):
        return refused("sample_profile_payload_shape_invalid")
    if int(row_slices[row]) != slices[0]:
        return refused("sample_profile_slice_mismatch")
    detail_record = record.get("axial_joint_compartment")
    if not isinstance(detail_record, Mapping):
        return refused("sample_profile_record_row_evidence_mismatch")
    details = detail_record.get("pointed_planes")
    if not isinstance(details, (list, tuple)):
        return refused("sample_profile_record_row_evidence_mismatch")
    matching_details = [
        item
        for item in details
        if isinstance(item, dict)
        and item.get("slice") == slices[0]
        and item.get("row") == row
        and item.get("support") == observation.get("support")
        and item.get("code") == observation.get("code")
        and item.get("count") == observation.get("count")
    ]
    if len(matching_details) != 1:
        return refused("sample_profile_record_row_evidence_mismatch")
    start, stop = int(offsets[row]), int(offsets[row + 1])
    points = coordinates[start:stop]
    values = white_all[start:stop]
    available = valid_all[start:stop]
    if points.size and (points.min() < 0 or points.max() > np.iinfo(np.int32).max):
        return refused("sample_profile_coordinate_invalid")
    if points.ndim != 2 or points.shape[1:] != (2,):
        return refused("sample_profile_coordinate_invalid")
    if not len(points):
        return refused("sample_profile_empty_point_row")
    if np.any(values & ~available):
        return refused("sample_profile_white_without_valid_sample")
    claimed = observation.get("count")
    measured_white_count = int(np.count_nonzero(values & available))
    if (
        not isinstance(claimed, int)
        or isinstance(claimed, bool)
        or claimed < 0
        or claimed != measured_white_count
    ):
        return refused("sample_profile_white_count_mismatch")

    readings: dict[tuple[str, str], PlaceReading] = {}
    source_address = {
        "study_uid": record.get("study_uid"),
        "series_uid": record.get("series_uid"),
        "view": record.get("view"),
        "record_slice_index": record.get("slice_index"),
        "sample_slice_index": slices[0],
        "artifact": record.get("artifact"),
        "support": observation.get("support"),
        "row": row,
    }
    for binding in bindings:
        if not isinstance(binding, Mapping):
            return refused("sample_profile_binding_invalid")
        bank, metric = binding.get("bank"), binding.get("metric")
        if not isinstance(bank, str) or not isinstance(metric, str):
            return refused("sample_profile_binding_invalid")
        key = (bank, metric)
        if key in readings:
            return refused("duplicate_measurement_binding")
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
            return refused("unknown_sample_profile_metric")
        source = binding.get("source", "array")
        if source == "unread":
            try:
                reading, unread_item = unread_place_reading(
                    binding, metric_spec, len(points), source_address
                )
            except ValueError as error:
                return refused(str(error).split(":", 1)[0], str(error))
            readings[key] = reading
            unread_sources.append(unread_item)
            continue
        if source == "record_context":
            scope = binding.get("scope")
            if scope == "record_plane" and record.get("slice_index") != slices[0]:
                return refused("context_record_plane_slice_mismatch")
            if scope == "acquisition" and tuple(owner_view) != tuple(view):
                return refused("context_acquisition_view_mismatch")
            try:
                reading, context_item = record_context_place_reading(
                    binding, metric_spec, len(points), record, source_address
                )
            except ValueError as error:
                return refused(str(error).split(":", 1)[0], str(error))
            readings[key] = reading
            context_sources.append(context_item)
            continue
        if source != "array":
            return refused("sample_profile_binding_invalid")
        value_name = binding.get("value")
        available_name = binding.get("available")
        if not isinstance(value_name, str) or not isinstance(available_name, str):
            return refused("sample_profile_binding_invalid")
        if (
            value_name not in (names["white"], names["light"])
            or available_name != names["valid"]
        ):
            return refused("sample_profile_binding_array_not_declared")
        try:
            values_all = white_all if value_name == names["white"] else read(value_name)
            available_values = (
                valid_all if available_name == names["valid"] else read(available_name)
            )
        except (
            KeyError,
            TypeError,
            ValueError,
            IndexError,
            OSError,
            OverflowError,
        ) as error:
            return refused("sample_profile_source_unavailable", str(error))
        if (
            values_all.ndim != 1
            or values_all.shape != valid_all.shape
            or available_values.ndim != 1
            or available_values.shape != valid_all.shape
        ):
            return refused("sample_profile_binding_shape_mismatch")
        metric_values = values_all[start:stop]
        metric_available = available_values[start:stop]
        if metric_available.dtype.kind != "b":
            return refused("sample_profile_availability_dtype_mismatch")
        readings[key] = PlaceReading(bank, metric, metric_values, metric_available)

    encoded = encode_places(layout, readings, references)
    points_rc = np.asarray(points, dtype=np.int32).copy()
    points_rc.flags.writeable = False
    metadata.update(
        source_refs=source_refs,
        packed_row=row,
        target_slice=slices[0],
        point_count=len(points_rc),
        declared_count=claimed,
        declared_count_meaning="white_sample_count",
        measured_white_count=measured_white_count,
        target_frame_status="per_slice_lps_basis_not_retained",
        sample_scope="projected_native_source_locations_only",
    )
    # Store this row's exact sampled light under the same verified source address in metadata;
    # no conversion or threshold is performed by the adapter.
    metadata["sampled_light_array"] = names["light"]
    return AddressedEncoding(encoded.status.value, encoded, points_rc, metadata)
