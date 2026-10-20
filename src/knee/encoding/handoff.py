"""Read addressed, retained native measurements into the exact place encoder.

This adapter never runs recognition, chooses a healthy norm, or turns a target
into observed tissue. Each binding names its actual value, availability and
optional crop window. Packed traces/unequal planes need their own declared
adapter; they are refused by name rather than guessed to be image masks.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from knee.collapse.observations import address_frame_status
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
class AddressedEncoding:
    status: str
    encoding: EncodingResult | None
    points_rc: np.ndarray | None
    metadata: dict


class _SourceError(ValueError):
    pass


def encode_observation(
    record: dict,
    observation: dict,
    arrays: Mapping[str, np.ndarray],
    layout: CompiledLayout,
    bindings: Sequence[dict],
    references: Mapping[tuple[str, str], NumericReference],
    *,
    verified_arrays: dict[tuple[str, str], np.ndarray] | None = None,
) -> AddressedEncoding:
    """Encode one plane's actual support, with the supplied layout and norms.

    `points_rc[i]` is the native address of every metric's `row_codes[i]`.
    Array bindings are {bank, metric, value, available, window?}; window names
    a retained int array [r0,r1,c0,c1], with exclusive upper bounds. A binding
    without a window reads a full native plane. A record_context binding names
    an explicit path and acquisition or record_plane scope. Digests are checked
    before array use.
    """
    metadata = {"observation": dict(observation), "bindings": list(bindings)}
    context_sources: list[dict] = []
    metadata["context_sources"] = context_sources
    unread_sources: list[dict] = []
    metadata["unread_sources"] = unread_sources

    def refused(code: str, detail: str = "") -> AddressedEncoding:
        return AddressedEncoding(code, None, None, {**metadata, "detail": detail})

    if (
        observation.get("provenance") == "projected"
        or observation.get("kind") == "target"
    ):
        return refused("target_only")
    if observation.get("provenance") not in ("native", "laid"):
        return refused("unsupported_provenance")
    if observation.get("kind") not in ("resolved", "reading"):
        return refused("unsupported_observation_kind")
    if observation.get("artifact") != record.get("artifact"):
        return refused("source_artifact_mismatch")
    if observation.get("series_uid") != record.get("series_uid"):
        return refused("source_series_mismatch")
    slices = observation.get("slices")
    if not isinstance(slices, (list, tuple)) or len(slices) != 1:
        return refused("plane_address_required")
    if not isinstance(slices[0], int) or isinstance(slices[0], bool) or slices[0] < 0:
        return refused("invalid_slice_address")
    explicit_frame = observation.get("address_frame")
    if explicit_frame is not None:
        frame_status = address_frame_status(explicit_frame)
        if frame_status != "frame_valid":
            metadata["plane_frame_source"] = "observation.address_frame_invalid"
            return refused("invalid_observation_address_frame", frame_status)
    for binding in bindings:
        if binding.get("source", "array") != "record_context":
            continue
        if (
            binding.get("scope") == "record_plane"
            and record.get("slice_index") != slices[0]
        ):
            return refused("context_record_plane_slice_mismatch")
        if binding.get("scope") == "acquisition":
            record_view, observation_view = record.get("view"), observation.get("view")
            if (
                not isinstance(record_view, (list, tuple))
                or not isinstance(observation_view, (list, tuple))
                or tuple(record_view) != tuple(observation_view)
            ):
                return refused("context_acquisition_view_mismatch")

    observation_view, record_view = observation.get("view"), record.get("view")
    if (
        not isinstance(observation_view, (list, tuple))
        or not isinstance(record_view, (list, tuple))
        or tuple(observation_view) != tuple(record_view)
    ):
        return refused("source_view_mismatch")

    loaded: dict[str, np.ndarray] = {}
    source_refs: dict[str, dict] = {}
    metadata["source_refs"] = source_refs

    def read(name: object) -> np.ndarray:
        if not isinstance(name, str) or not name:
            raise _SourceError("missing_array_name")
        if name in loaded:
            return loaded[name]
        if name not in arrays:
            raise _SourceError("missing_array:" + name)
        expected = record.get("arrays", {}).get(name, {}).get("digest")
        if not isinstance(expected, str):
            raise _SourceError("missing_digest:" + name)
        cache_key = (name, expected)
        if verified_arrays is not None and cache_key in verified_arrays:
            array = verified_arrays[cache_key]
        else:
            array = arrays[name]
            if digest(array) != expected:
                raise _SourceError("digest_mismatch:" + name)
            if verified_arrays is not None:
                verified_arrays[cache_key] = array
        loaded[name] = array
        source_refs[name] = {
            "artifact": record["artifact"],
            "digest": expected,
            "shape": list(array.shape),
            "dtype": array.dtype.str,
        }
        return array

    try:
        support = read(observation.get("support"))
        row = observation.get("row")
        if row is not None:
            if (
                not isinstance(row, int)
                or isinstance(row, bool)
                or row < 0
                or support.ndim != 3
                or row >= support.shape[0]
            ):
                return refused("support_adapter_required")
            support = support[row]
        elif slices[0] != record.get("slice_index") and explicit_frame is None:
            return refused("plane_address_required")
        if support.ndim != 2:
            return refused("support_adapter_required")
        label = observation.get("label")
        if label is None:
            if support.dtype.kind != "b":
                return refused("support_label_required")
            mask = support
        else:
            if (
                not isinstance(label, int)
                or isinstance(label, bool)
                or support.dtype.kind not in "iu"
            ):
                return refused("invalid_support_label")
            mask = support == label
        count = int(np.count_nonzero(mask))
        declared_count = observation.get("count")
        if declared_count is not None:
            if (
                not isinstance(declared_count, int)
                or isinstance(declared_count, bool)
                or declared_count < 0
            ):
                return refused("invalid_support_count")
            if declared_count != count:
                return refused("support_count_mismatch")
        points = np.column_stack(np.nonzero(mask)).astype(np.int32)
        readings: dict[tuple[str, str], PlaceReading] = {}
        for binding in bindings:
            bank, metric = binding["bank"], binding["metric"]
            key = (bank, metric)
            if key in readings:
                return refused("duplicate_measurement_binding")
            metric_spec = next(
                (
                    metric_spec
                    for bank_spec in layout.banks
                    if bank_spec.name == bank
                    for metric_spec in bank_spec.metrics
                    if metric_spec.name == metric
                ),
                None,
            )
            if metric_spec is None:
                return refused("unknown_measurement_metric")
            if binding.get("source") == "unread":
                reading, unread_metadata = unread_place_reading(
                    binding,
                    metric_spec,
                    count,
                    {
                        "artifact": record.get("artifact"),
                        "series_uid": record.get("series_uid"),
                        "view": observation.get("view"),
                        "slice_index": slices[0],
                        "row": row,
                        "support": observation.get("support"),
                    },
                )
                readings[key] = reading
                unread_sources.append(unread_metadata)
                continue
            if binding.get("source", "array") == "record_context":
                context_address = {
                    "series_uid": record.get("series_uid"),
                    "view": record.get("view"),
                    "slice_index": record.get("slice_index"),
                    "artifact": record.get("artifact"),
                }
                try:
                    reading, context_item = record_context_place_reading(
                        binding, metric_spec, count, record, context_address
                    )
                except ValueError as error:
                    raise _SourceError(str(error).split(":", 1)[0]) from error
                readings[key] = reading
                context_sources.append(context_item)
                continue
            values, available = read(binding["value"]), read(binding["available"])
            if (
                values.ndim != 2
                or values.shape != available.shape
                or available.dtype.kind != "b"
            ):
                return refused("measurement_shape_mismatch")
            if binding.get("window") is None:
                if slices[0] != record.get("slice_index"):
                    return refused("measurement_plane_address_required")
                if values.shape != mask.shape:
                    return refused("measurement_window_required")
                r0, r1, c0, c1 = 0, mask.shape[0], 0, mask.shape[1]
            else:
                window = read(binding["window"])
                if window.shape != (4,) or window.dtype.kind not in "iu":
                    return refused("invalid_measurement_window")
                r0, r1, c0, c1 = (int(n) for n in window)
                if not (
                    0 <= r0 <= r1 <= mask.shape[0] and 0 <= c0 <= c1 <= mask.shape[1]
                ):
                    return refused("invalid_measurement_window")
                if values.shape != (r1 - r0, c1 - c0):
                    return refused("measurement_window_shape_mismatch")
            inside = (
                (points[:, 0] >= r0)
                & (points[:, 0] < r1)
                & (points[:, 1] >= c0)
                & (points[:, 1] < c1)
            )
            # Exterior has no measured value. The false availability mask makes
            # its storage placeholder unwritten; original values stay addressed.
            selected = np.zeros(count, dtype=values.dtype)
            valid = np.zeros(count, dtype=bool)
            local = points[inside] - np.array((r0, c0))
            selected[inside] = values[local[:, 0], local[:, 1]]
            valid[inside] = available[local[:, 0], local[:, 1]]
            readings[key] = PlaceReading(bank, metric, selected, valid)
        encoded = encode_places(layout, readings, references)
    except _SourceError as error:
        return refused(str(error).split(":", 1)[0], str(error))
    except (KeyError, TypeError, ValueError, IndexError) as error:
        return refused("invalid_measurement_binding", str(error))

    # Prefer a frame attached to this observation; a record frame belongs only
    # to that record's own slice and cannot be relabelled for another slice.
    if explicit_frame is not None:
        frame = explicit_frame
        frame_source = "observation.address_frame"
    elif record.get("slice_index") == slices[0]:
        frame = record.get("plane_frame")
        frame_source = "record.plane_frame" if frame is not None else None
    else:
        frame = None
        frame_source = None
    metadata.update(
        source_refs=source_refs,
        native_shape_rc=list(mask.shape),
        plane_frame=frame,
        plane_frame_source=frame_source,
        geometry_status="available"
        if frame is not None
        else "frame_not_retained_for_slice",
        references=[
            {
                "bank": ref.bank,
                "metric": ref.metric,
                "reference_id": ref.reference_id,
                "source": ref.source,
                "units": ref.units,
                "low": ref.low,
                "high": ref.high,
            }
            for ref in references.values()
        ],
        place_count=count,
        meaning="counts of addressed readings; no physical volume or diagnosis",
    )
    points.flags.writeable = False
    return AddressedEncoding(encoded.status.value, encoded, points, metadata)
