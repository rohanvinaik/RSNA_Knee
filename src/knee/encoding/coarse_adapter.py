"""Packed coarse-block adapter returning a ``coarse_grid_rc`` ScopedEncoding."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, TypeGuard

import numpy as np

from knee.encoding.coarse_blocks import (
    OK,
    block_native_bounds,
    coarse_row_geometry,
    support_block_coordinates,
)

# Names bound in handoff's namespace by the existing adapters.
from knee.encoding.handoff import digest, unread_place_reading
from knee.encoding.packed_planes import read_packed_plane
from knee.encoding.places import (
    CompiledLayout,
    NumericReference,
    PlaceReading,
    encode_places,
)
from knee.encoding.scoped import ScopedEncoding

ADDRESS_KIND = "coarse_grid_rc"
COARSE_BLOCKS_COUNT = "coarse_blocks"
_FRAME_TAILS = {
    "origin_lps": (3,),
    "basis_lps": (3, 2),
    "normal_lps": (3,),
    "thickness_mm": (),
}


@dataclass(frozen=True, slots=True)
class CoarseTargetEvidence:
    """Explicit declaration for a holder whose target is another acquisition."""

    owner_artifact: str
    owner_series_uid: str
    target_series_uid: str
    target_view: tuple[str, str, str]
    record_field: str = "fibula_key_planes"
    orientation: str = "axial"


@dataclass(frozen=True, slots=True)
class CoarseBlockLayout:
    offsets: str
    shapes: str
    slices: str
    windows_rc: str
    block_px: str
    block_mm: str
    packed_arrays: tuple[str, ...]
    frame_arrays: Mapping[str, str] | None = None
    count_meaning: str | None = None
    target_evidence: CoarseTargetEvidence | None = None


class _SourceError(Exception):
    pass


def _name(value: object) -> TypeGuard[str]:
    return isinstance(value, str) and bool(value)


def _plain_int(value: object) -> TypeGuard[int]:
    return type(value) is int


def _layout_names(c: CoarseBlockLayout) -> list[str]:
    names = [c.offsets, c.shapes, c.slices, c.windows_rc, c.block_px, c.block_mm]
    names += list(c.packed_arrays)
    if c.frame_arrays:
        names += list(c.frame_arrays.values())
    return names


def _same_view(a: object, b: object) -> bool:
    return (
        isinstance(a, (list, tuple))
        and isinstance(b, (list, tuple))
        and tuple(a) == tuple(b)
    )


def encode_coarse_observation(
    record: Mapping[str, Any],
    observation: Mapping[str, Any],
    arrays: Mapping[str, np.ndarray],
    layout: CompiledLayout,
    bindings: Sequence[Mapping[str, Any]],
    references: Mapping[tuple[str, str], NumericReference],
    coarse: CoarseBlockLayout,
    *,
    verified_arrays: dict[tuple[str, str], np.ndarray] | None = None,
) -> ScopedEncoding:
    metadata: dict[str, Any] = {
        "observation": dict(observation) if isinstance(observation, Mapping) else None,
        "address_kind": ADDRESS_KIND,
    }

    def refused(code: str, detail: str = "") -> ScopedEncoding:
        return ScopedEncoding(
            code, None, None, ADDRESS_KIND, {**metadata, "detail": detail}
        )

    # ---- layout ----
    if not isinstance(coarse, CoarseBlockLayout):
        return refused("invalid_coarse_layout")
    if (
        not all(
            _name(n)
            for n in (
                coarse.offsets,
                coarse.shapes,
                coarse.slices,
                coarse.windows_rc,
                coarse.block_px,
                coarse.block_mm,
            )
        )
        or not isinstance(coarse.packed_arrays, tuple)
        or not coarse.packed_arrays
        or not all(_name(n) for n in coarse.packed_arrays)
        or len(set(coarse.packed_arrays)) != len(coarse.packed_arrays)
    ):
        return refused("invalid_coarse_array_layout")
    if coarse.frame_arrays is not None and (
        not isinstance(coarse.frame_arrays, Mapping)
        or any(
            k not in _FRAME_TAILS or not _name(v)
            for k, v in coarse.frame_arrays.items()
        )
    ):
        return refused("invalid_coarse_frame_layout")
    if coarse.count_meaning is not None and not _name(coarse.count_meaning):
        return refused("invalid_count_meaning")
    # ---- observation ----
    if observation.get("provenance") != "native" or observation.get("kind") not in (
        "reading",
        "resolved",
    ):
        return refused("unsupported_observation_kind")
    row = observation.get("row")
    if not _plain_int(row) or row < 0:
        return refused("invalid_packed_row")
    obs_slices = observation.get("slices")
    if (
        not isinstance(obs_slices, (list, tuple))
        or len(obs_slices) != 1
        or not _plain_int(obs_slices[0])
        or obs_slices[0] < 0
    ):
        return refused("plane_address_required")
    slice_index = obs_slices[0]
    support_name = observation.get("support")
    if not _name(support_name) or support_name not in coarse.packed_arrays:
        return refused("support_not_declared_packed")
    owner_uid = record.get("series_uid")
    owner_artifact = record.get("artifact")
    if not _name(owner_uid) or not _name(owner_artifact):
        return refused("invalid_owner_identity")

    # ---- identity ----
    ev = coarse.target_evidence
    evidence_entry = None
    if ev is None:
        if observation.get("artifact") != owner_artifact:
            return refused("source_artifact_mismatch")
        if observation.get("series_uid") != owner_uid:
            return refused("source_series_mismatch")
        if not _same_view(observation.get("view"), record.get("view")):
            return refused("source_view_mismatch")
        target_uid = owner_uid
        target_view = tuple(observation["view"])
    else:
        if (
            not isinstance(ev, CoarseTargetEvidence)
            or not all(
                _name(x)
                for x in (
                    ev.owner_artifact,
                    ev.owner_series_uid,
                    ev.target_series_uid,
                    ev.record_field,
                    ev.orientation,
                )
            )
            or not isinstance(ev.target_view, tuple)
            or len(ev.target_view) != 3
            or not all(isinstance(p, str) for p in ev.target_view)
        ):
            return refused("invalid_target_evidence")
        if (
            owner_artifact != ev.owner_artifact
            or observation.get("artifact") != ev.owner_artifact
        ):
            return refused("owner_artifact_mismatch")
        if owner_uid != ev.owner_series_uid:
            return refused("invalid_owner_identity")
        if observation.get("series_uid") != ev.target_series_uid:
            return refused("target_series_mismatch")
        if not _same_view(observation.get("view"), ev.target_view):
            return refused("target_view_mismatch")
        if str(ev.target_view[0]).lower() != ev.orientation.lower():
            return refused("target_view_mismatch")
        planes = record.get(ev.record_field)
        evidence_entry = (
            planes.get(ev.target_series_uid) if isinstance(planes, Mapping) else None
        )
        if not isinstance(evidence_entry, Mapping):
            return refused("target_evidence_missing")
        if str(evidence_entry.get("orientation", "")).lower() != ev.orientation.lower():
            return refused("target_view_mismatch")
        prefix = evidence_entry.get("arrays_prefix")
        if not _name(prefix) or not all(
            n.startswith(prefix + "_") for n in _layout_names(coarse)
        ):
            return refused("arrays_prefix_mismatch")
        read_slices = evidence_entry.get("slices_read")
        if (
            not isinstance(read_slices, list)
            or not all(_plain_int(v) for v in read_slices)
            or row >= len(read_slices)
            or read_slices[row] != slice_index
        ):
            return refused("target_slice_mismatch")
        target_uid = ev.target_series_uid
        target_view = ev.target_view

    # ---- sources ----
    loaded: dict[str, np.ndarray] = {}
    source_refs: dict[str, dict[str, Any]] = {}
    metadata["source_refs"] = source_refs

    def read(name: object) -> np.ndarray:
        if not _name(name):
            raise _SourceError("missing_array_name")
        if name in loaded:
            return loaded[name]
        if name not in arrays:
            raise _SourceError("missing_array:" + name)
        descriptors = record.get("arrays")
        if not isinstance(descriptors, Mapping):
            raise _SourceError("array_descriptors_invalid")
        entry = descriptors.get(name, {})
        expected = entry.get("digest") if isinstance(entry, Mapping) else None
        if not isinstance(expected, str):
            raise _SourceError("missing_digest:" + name)
        key = (name, expected)
        if verified_arrays is not None and key in verified_arrays:
            array = verified_arrays[key]
        else:
            array = arrays[name]
            if digest(array) != expected:
                raise _SourceError("digest_mismatch:" + name)
            if verified_arrays is not None:
                verified_arrays[key] = array
        loaded[name] = array
        source_refs[name] = {
            "artifact": owner_artifact,
            "owner_series_uid": owner_uid,
            "digest": expected,
            "shape": list(array.shape),
            "dtype": array.dtype.str,
        }
        return array

    try:
        offsets = read(coarse.offsets)
        shapes = read(coarse.shapes)
        row_slices = read(coarse.slices)
        windows = read(coarse.windows_rc)
        px = read(coarse.block_px)
        mm = read(coarse.block_mm)
        geom = coarse_row_geometry(shapes, row_slices, windows, px, mm, row)
        if geom.code != OK:
            return refused(geom.code)
        if (
            geom.slice_index is None
            or geom.window_rc is None
            or geom.block_px is None
            or geom.block_mm is None
            or geom.grid_shape is None
        ):
            return refused("coarse_geometry_incomplete")
        if geom.slice_index != slice_index:
            return refused("packed_slice_mismatch")

        row_arrays: dict[str, np.ndarray] = {}
        for name in coarse.packed_arrays:
            result = read_packed_plane(read(name), offsets, shapes, row)
            if result.code != "ok" or result.plane is None:
                return refused("packed_plane_unavailable", str(result.code))
            row_arrays[name] = result.plane

        # support
        support = row_arrays[support_name]
        label = observation.get("label")
        if label is None:
            if support.dtype.kind != "b":
                return refused("support_label_required")
            mask = support
        else:
            if not _plain_int(label) or support.dtype.kind not in "iu":
                return refused("invalid_support_label")
            mask = support == label
        code, coordinates = support_block_coordinates(mask)
        if code != OK or coordinates is None:
            return refused(code)
        count = int(coordinates.shape[0])
        code, bounds = block_native_bounds(geom, coordinates)
        if code != OK or bounds is None:
            return refused(code)

        # count: interpreted only under the exact declared meaning
        declared_count = observation.get("count")
        count_checked = False
        if coarse.count_meaning == COARSE_BLOCKS_COUNT and declared_count is not None:
            if not _plain_int(declared_count) or declared_count < 0:
                return refused("invalid_support_count")
            if declared_count != count:
                return refused("support_count_mismatch")
            count_checked = True

        # optional frame: validated row-wise, retained, never used for coordinates
        frame: dict[str, list | float] = {}
        frame_status = "frame_not_declared"
        if coarse.frame_arrays:
            n_rows = len(row_slices)
            problems = []
            for key, name in coarse.frame_arrays.items():
                try:
                    arr = read(name)
                except _SourceError as error:
                    if str(error).startswith("digest_mismatch"):
                        raise
                    problems.append(key)
                    continue
                if (
                    arr.shape != (n_rows, *_FRAME_TAILS[key])
                    or arr.dtype.kind not in "iuf"
                    or not bool(np.all(np.isfinite(arr[row])))
                ):
                    problems.append(key)
                    continue
                frame[key] = arr[row].tolist()
            complete = not problems and {"origin_lps", "basis_lps"} <= set(
                coarse.frame_arrays
            )
            frame_status = "frame_available" if complete else "frame_incomplete"
            metadata["frame_problems"] = problems

        # bindings -> place readings on the true support blocks
        scope_address = {
            "target_series_uid": target_uid,
            "target_view": list(target_view),
            "slice_index": slice_index,
            "window_rc": list(geom.window_rc),
            "block_px": list(geom.block_px),
            "block_mm": list(geom.block_mm),
            "grid_shape": list(geom.grid_shape),
        }
        readings: dict[tuple[str, str], PlaceReading] = {}
        unread_sources: list[dict] = []
        for binding in bindings:
            if not isinstance(binding, Mapping):
                return refused("invalid_measurement_binding")
            bank, metric = binding.get("bank"), binding.get("metric")
            if not _name(bank) or not _name(metric):
                return refused("invalid_measurement_binding")
            key = (bank, metric)
            if key in readings:
                return refused("duplicate_measurement_binding")
            spec = next(
                (
                    m
                    for b in layout.banks
                    if b.name == bank
                    for m in b.metrics
                    if m.name == metric
                ),
                None,
            )
            if spec is None:
                return refused("unknown_measurement_metric")
            source = binding.get("source", "array")
            if source == "unread":
                if any(
                    f in binding
                    for f in (
                        "value",
                        "available",
                        "availability_policy",
                        "window",
                        "path",
                        "scope",
                    )
                ):
                    return refused("invalid_unread_binding")
                reading, unread_meta = unread_place_reading(
                    binding,
                    spec,
                    count,
                    {
                        "artifact": owner_artifact,
                        "series_uid": target_uid,
                        "view": list(target_view),
                        "slice_index": slice_index,
                        "row": row,
                        "support": support_name,
                    },
                )
                readings[key] = reading
                unread_sources.append(unread_meta)
                continue
            if source == "record_context":
                return refused("coarse_record_context_unsupported")
            if source != "array":
                return refused("unsupported_binding_source")
            if binding.get("window") is not None:
                return refused("coarse_window_binding_unsupported")
            value_name = binding.get("value")
            if value_name not in row_arrays:
                return refused("binding_array_not_declared_packed", str(value_name))
            selected = row_arrays[value_name][mask]
            policy = binding.get("availability_policy")
            avail_name = binding.get("available")
            if (policy is None) == (avail_name is None):
                return refused("availability_binding_invalid")
            if avail_name is not None:
                if avail_name not in row_arrays:
                    return refused("binding_array_not_declared_packed", str(avail_name))
                plane = row_arrays[avail_name]
                if plane.dtype.kind != "b":
                    return refused("availability_array_dtype_mismatch")
                available = plane[mask]
            elif policy == "finite_values":
                if selected.dtype.kind not in "iuf":
                    return refused("availability_policy_dtype_mismatch", str(policy))
                available = np.isfinite(selected)
            elif policy == "all_stored":
                if selected.dtype.kind not in "biu":
                    return refused("availability_policy_dtype_mismatch", str(policy))
                available = np.ones(count, dtype=bool)
            else:
                return refused("invalid_availability_policy", str(policy))
            readings[key] = PlaceReading(bank, metric, selected, available)

        encoded = encode_places(layout, readings, references)
    except _SourceError as error:
        return refused(str(error).split(":", 1)[0], str(error))
    except (KeyError, TypeError, ValueError, IndexError, OverflowError) as error:
        return refused("invalid_measurement_binding", str(error))

    metadata.update(
        observation=dict(observation),
        scope_address=scope_address,
        lineage={
            "owner_artifact": owner_artifact,
            "owner_series_uid": owner_uid,
            "packed_row": row,
            "support_array": support_name,
        },
        native_bounds_rc=bounds,
        native_bounds_meaning="clipped half-open native pixel bounds [r0, r1, c0, c1] of each addressed block; bounds only",
        geometry_status=frame_status,
        packed_frame=frame if frame else None,
        declared_count=declared_count,
        declared_count_meaning=coarse.count_meaning,
        count_interpreted_as_blocks=count_checked,
        support_block_count=count,
        unread_sources=unread_sources,
        references=[
            {
                "bank": r.bank,
                "metric": r.metric,
                "reference_id": r.reference_id,
                "source": r.source,
                "units": r.units,
                "low": r.low,
                "high": r.high,
            }
            for r in references.values()
        ],
        meaning="counts of addressed coarse-block readings on the measured grid; indices are coarse_grid_rc, not native_rc or LPS",
    )
    return ScopedEncoding(
        encoded.status.value, encoded, coordinates, ADDRESS_KIND, metadata
    )
