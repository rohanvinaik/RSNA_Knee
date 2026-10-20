"""Pure JSON/array serialization for one study's composed object profiles.

The caller owns persistence. This module returns ordinary JSON metadata and
named ndarray payloads for the existing common serializer; it never writes a
file or materializes a dense CountBundle.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Any

import numpy as np

from knee.encoding.composition import (
    AddResult,
    BatchIndexMap,
    ObjectComposition,
    PreparedComposition,
    StudyComposition,
)
from knee.encoding.object_profile import (
    BankFacet,
    ConflictRecord,
    FacetCoordinate,
    IssueRecord,
    RowcodeBatch,
    SourceLink,
    registry_fingerprint,
)

__all__ = ["serialize_add_result", "serialize_study_composition"]


class _ArrayStore(dict[str, np.ndarray]):
    """Study-local keyed arrays, interning only repeated object identities."""

    def __init__(self) -> None:
        super().__init__()
        self.by_identity: dict[int, tuple[np.ndarray, dict[str, object]]] = {}


def _prefix(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or any(char in value for char in ("/", "\\", "\0"))
    ):
        raise ValueError("invalid_composition_array_prefix")
    return value


def _array(arrays: dict[str, np.ndarray], key: str, value: object) -> dict[str, object]:
    if not isinstance(value, np.ndarray) or value.dtype.hasobject:
        raise ValueError(f"composition_array_invalid:{key}")
    if isinstance(arrays, _ArrayStore):
        shared = arrays.by_identity.get(id(value))
        if shared is not None and shared[0] is value:
            return shared[1]
    if key in arrays:
        raise ValueError(f"composition_array_key_collision:{key}")
    arrays[key] = value
    descriptor: dict[str, object] = {
        "key": key,
        "dtype": value.dtype.str,
        "shape": list(value.shape),
    }
    if isinstance(arrays, _ArrayStore):
        arrays.by_identity[id(value)] = (value, descriptor)
    return descriptor


def _json_value(value: Any, arrays: dict[str, np.ndarray], prefix: str) -> Any:
    if isinstance(value, np.ndarray):
        return _array(arrays, prefix, value)
    if isinstance(value, np.generic):
        return _json_value(value.item(), arrays, prefix)
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("composition_metadata_key_not_string")
            result[key] = _json_value(item, arrays, f"{prefix}.{key}")
        return result
    if isinstance(value, (tuple, list)):
        return [
            _json_value(item, arrays, f"{prefix}.{index}")
            for index, item in enumerate(value)
        ]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if np.isfinite(value):
            return value
        return {"nonfinite_float": repr(value)}
    raise ValueError(f"composition_metadata_value_unsupported:{type(value).__name__}")


def _source_link(link: object) -> dict[str, str] | None:
    if not isinstance(link, SourceLink):
        return None
    return {
        "observation": link.observation,
        "artifact": link.artifact,
        "array_name": link.array_name,
        "index_lineage": link.index_lineage,
    }


def _facet(value: object) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, FacetCoordinate):
        coordinate = value
    elif isinstance(value, BankFacet):
        coordinate = value.coordinate
    elif isinstance(value, (RowcodeBatch, ConflictRecord)):
        coordinate = value.facet_coordinate
    else:
        return None
    return {
        "view_role": coordinate.view_role,
        "lens": coordinate.lens,
        "scale": coordinate.scale,
        "direction": coordinate.direction,
    }


def _spatial(
    spatial: object, arrays: dict[str, np.ndarray], prefix: str
) -> dict[str, Any] | None:
    if spatial is None:
        return None
    names = (
        "point_lps",
        "relative_lps_mm",
        "relative_mps_mm",
        "normalized_mps",
        "axis_digits",
        "joint_code",
        "coordinate_codes",
        "joint_codes",
    )
    result: dict[str, Any] = {}
    for name in names:
        value = getattr(spatial, name, None)
        if value is not None:
            result[name] = _array(arrays, f"{prefix}.spatial.{name}", value)
    for name in (
        "input_code",
        "coordinate_kind",
        "object_name",
        "map_status",
        "reference_status",
        "precision_status",
        "side",
        "scale_mm",
        "scale_source",
        "keyplanes",
        "coordinate_status_names",
        "joint_status_names",
    ):
        value = getattr(spatial, name, None)
        if value is not None:
            result[name] = _json_value(value, arrays, f"{prefix}.spatial_meta.{name}")
    return result


def serialize_add_result(
    add_result: AddResult, prefix: str
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Serialize one composer addition without converting its places to JSON lists."""
    arrays = _ArrayStore()
    metadata = _serialize_add_into(add_result, prefix, arrays)
    return arrays, metadata


def _serialize_add_into(
    add_result: AddResult, prefix: str, arrays: _ArrayStore
) -> dict[str, Any]:
    prefix = _prefix(prefix)
    if not isinstance(add_result, AddResult):
        raise TypeError("composition_add_result_required")
    batches: list[dict[str, Any]] = []
    if len(add_result.batches) != len(add_result.batch_index_maps):
        raise ValueError("composition_batch_index_map_count_mismatch")
    for local_ordinal, (batch, index_map) in enumerate(
        zip(add_result.batches, add_result.batch_index_maps, strict=True)
    ):
        if not isinstance(batch, RowcodeBatch) or not isinstance(
            index_map, BatchIndexMap
        ):
            raise TypeError("composition_batch_payload_malformed")
        if index_map.source_link != batch.source_link:
            raise ValueError("composition_batch_source_link_mismatch")
        key = f"{prefix}.batch.{local_ordinal}"
        address = batch.addresses
        batches.append(
            {
                "object_batch_ordinal": index_map.object_batch_ordinal,
                "bank": batch.bank,
                "metric": batch.metric,
                "facet_coordinate": _facet(batch),
                "measurement_source_identity": batch.measurement_source_identity,
                "layout_fingerprint": batch.layout_fingerprint,
                "count_layout_id": batch.count_layout.layout_id,
                "reference_set_identity": batch.reference_set_identity,
                "rowcodes": _array(arrays, f"{key}.rowcodes", batch.rowcodes),
                "address": {
                    "kind": address.kind,
                    "frame_identity": address.frame_identity,
                    "coordinates": _array(
                        arrays, f"{key}.coordinates", address.coordinates
                    ),
                },
                "original_place_indices": _array(
                    arrays,
                    f"{key}.original_place_indices",
                    index_map.original_place_indices,
                ),
                "profile_index": index_map.profile_index,
                "outcome_index": index_map.outcome_index,
                "direction": _json_value(
                    index_map.direction, arrays, f"{key}.direction"
                ),
                "source_link": _source_link(batch.source_link),
            }
        )
    metadata = {
        "code": add_result.code.value,
        "object_name": add_result.object_name,
        "profile_index": add_result.profile_index,
        "outcome_index": add_result.outcome_index,
        "detail": add_result.detail,
        "spatial": _spatial(add_result.spatial, arrays, prefix),
        "batches": batches,
        "metadata": _json_value(
            add_result.metadata or {}, arrays, f"{prefix}.source_metadata"
        ),
    }
    return metadata


def _issue(issue: IssueRecord) -> dict[str, Any]:
    return {
        "batch_ordinal": issue.batch_ordinal,
        "code": issue.code.value,
        "fields": list(issue.fields),
        "detail": issue.detail,
        "source_link": _source_link(issue.source_link),
    }


def _conflict(
    conflict: ConflictRecord, arrays: dict[str, np.ndarray], prefix: str
) -> dict[str, Any]:
    return {
        "bank": conflict.bank,
        "metric": conflict.metric,
        "facet_coordinate": _facet(conflict),
        "measurement_source_identity": conflict.measurement_source_identity,
        "address_kind": conflict.address_kind,
        "frame_identity": conflict.frame_identity,
        "event_count": conflict.event_count,
        "link_batch": _array(arrays, f"{prefix}.link_batch", conflict.link_batch),
        "link_place": _array(arrays, f"{prefix}.link_place", conflict.link_place),
        "link_event": _array(arrays, f"{prefix}.link_event", conflict.link_event),
        "link_rowcode": _array(arrays, f"{prefix}.link_rowcode", conflict.link_rowcode),
    }


def serialize_study_composition(
    study_composition: StudyComposition,
    prepared: PreparedComposition,
    prefix: str = "object",
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Return one shared layout/registry and sparse per-object profiles for persistence."""
    prefix = _prefix(prefix)
    if not isinstance(study_composition, StudyComposition):
        raise TypeError("study_composition_required")
    if not isinstance(prepared, PreparedComposition):
        raise TypeError("prepared_composition_required")
    arrays = _ArrayStore()
    additions: list[dict[str, Any]] = []
    batch_rows: dict[str, dict[int, dict[str, Any]]] = {
        name: {} for name in study_composition.objects
    }
    for add_index, addition in enumerate(study_composition.additions):
        add_metadata = _serialize_add_into(
            addition, f"{prefix}.addition.{add_index}", arrays
        )
        additions.append(add_metadata)
        for batch in add_metadata["batches"]:
            object_name = add_metadata["object_name"]
            ordinal = batch["object_batch_ordinal"]
            if object_name in batch_rows:
                if ordinal in batch_rows[object_name]:
                    raise ValueError("composition_duplicate_object_batch_ordinal")
                batch_rows[object_name][ordinal] = batch

    objects: dict[str, Any] = {}
    for object_index, (object_name, composition) in enumerate(
        study_composition.objects.items()
    ):
        if not isinstance(composition, ObjectComposition):
            raise TypeError("composition_object_payload_malformed")
        object_prefix = f"{prefix}.object.{object_index}"
        profile_layout = prepared.profile_layouts.get(object_name)
        reference_identity = prepared.object_reference_identities.get(object_name)
        assembly = composition.assembly
        batches: list[dict[str, Any]] = []
        sparse_counts: list[list[Any]] = []
        conflicts: list[dict[str, Any]] = []
        mismatches: list[dict[str, Any]] = []
        malformed: list[dict[str, Any]] = []
        if assembly is not None:
            sparse_counts = [
                [bank, int(row), int(count)]
                for bank, row, count in assembly.profile.entries
            ]
            for record in assembly.batches:
                record_prefix = f"{object_prefix}.batch.{record.ordinal}"
                batch = batch_rows.get(object_name, {}).get(record.ordinal)
                batches.append(
                    {
                        "ordinal": record.ordinal,
                        "status": record.status.value,
                        "detail": record.detail,
                        "bank": record.bank,
                        "metric": record.metric,
                        "facet_coordinate": _json_value(
                            _facet(record.facet_coordinate),
                            arrays,
                            f"{record_prefix}.facet_coordinate",
                        ),
                        "measurement_source_identity": record.measurement_source_identity,
                        "source_link": _source_link(record.source_link),
                        "place_count": record.place_count,
                        "counted": record.counted,
                        "duplicate": record.duplicate,
                        "conflict": record.conflict,
                        "no_measurement": record.no_measurement,
                        "row_status": _array(
                            arrays, f"{record_prefix}.row_status", record.row_status
                        ),
                        "batch_payload": batch,
                    }
                )
            conflicts = [
                _conflict(conflict, arrays, f"{object_prefix}.conflict.{index}")
                for index, conflict in enumerate(assembly.conflicts)
            ]
            mismatches = [_issue(issue) for issue in assembly.mismatches]
            malformed = [_issue(issue) for issue in assembly.malformed]
        context = study_composition.spatial_contexts.get(object_name)
        context_metadata = None
        if context is not None:
            context_metadata = {
                name: _json_value(
                    getattr(context, name), arrays, f"{object_prefix}.context.{name}"
                )
                for name in (
                    "object_name",
                    "map_status",
                    "point_lps",
                    "precision_mm",
                    "keyplanes",
                    "side",
                    "scale_mm",
                    "scale_source",
                    "scale_record_code",
                    "code",
                )
            }
        objects[object_name] = {
            "status": (
                composition.code.value if assembly is None else assembly.code.value
            ),
            "preparation_status": composition.code.value,
            "detail": composition.detail,
            "reference_set_identity": reference_identity,
            "count_layout_id": (
                None
                if profile_layout is None
                else profile_layout.count_layout.layout_id
            ),
            "sparse_counts": sparse_counts,
            "assembly": None
            if assembly is None
            else {
                "code": assembly.code.value,
                "outcomes": [code.value for code in assembly.outcomes],
                "batches": batches,
                "conflicts": conflicts,
                "mismatches": mismatches,
                "malformed": malformed,
            },
            "batch_index_maps": [
                {
                    "object_batch_ordinal": item.object_batch_ordinal,
                    "profile_index": item.profile_index,
                    "outcome_index": item.outcome_index,
                    "bank": item.bank,
                    "metric": item.metric,
                    "direction": _json_value(
                        item.direction,
                        arrays,
                        f"{object_prefix}.index_map.{item.object_batch_ordinal}.direction",
                    ),
                    "original_place_indices": batch_rows.get(object_name, {})
                    .get(item.object_batch_ordinal, {})
                    .get("original_place_indices"),
                    "source_link": _source_link(item.source_link),
                }
                for item in composition.batch_index_maps
            ],
            "spatial_context": context_metadata,
        }

    registry = [
        {
            "bank": item.bank,
            "coordinate": {
                "view_role": item.coordinate.view_role,
                "lens": item.coordinate.lens,
                "scale": item.coordinate.scale,
                "direction": item.coordinate.direction,
            },
        }
        for item in prepared.registry
    ]
    metadata = {
        "schema": "knee_object_profiles/v1",
        "study_code": study_composition.code.value,
        "carrier_identity": prepared.carrier.identity,
        "layout_fingerprint": prepared.layout.fingerprint,
        "registry_fingerprint": registry_fingerprint(prepared.registry),
        "layout": {
            "version": prepared.layout.version,
            "carrier_id": prepared.layout.carrier_id,
            "fingerprint": prepared.layout.fingerprint,
            "banks": [
                {
                    "name": bank.name,
                    "facet": bank.facet,
                    "metrics": [
                        {
                            "name": metric.name,
                            "kind": metric.kind.value,
                            "words": list(metric.words),
                        }
                        for metric in bank.metrics
                    ],
                }
                for bank in prepared.layout.banks
            ],
        },
        "registry": registry,
        "objects": objects,
        "additions": additions,
    }
    return arrays, metadata
