"""Lossless, non-geometric ownership summary for retained encoded supports.

This module describes which saved measurement outputs belong to which source
addresses.  It deliberately does not join coordinates across acquisitions or
interpret support counts as volume.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Any, TypedDict

_COORDINATE_FIELDS = ("points_rc", "points_lps", "scope_coordinates")


class _SupportGroup(TypedDict):
    source_address: dict[str, Any]
    source_address_fingerprint: str
    meaning_fingerprint: str
    meaning: dict[str, Any]
    links: list[dict[str, Any]]


def _canonical(value: Any) -> str:
    """Return stable JSON for JSON-shaped manifest data."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _as_json(value: Any) -> Any:
    """Copy JSON-compatible values without retaining caller-owned containers."""
    if isinstance(value, Mapping):
        return {str(key): _as_json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_as_json(item) for item in value]
    if value is None or isinstance(value, (str, bool, int, float)):
        if isinstance(value, float) and not isfinite(value):
            raise ValueError("non_finite_manifest_value")
        return value
    raise TypeError(f"unsupported_manifest_value:{type(value).__name__}")


def _profile_entries(
    profiles: Sequence[Mapping[str, Any] | tuple[int, Mapping[str, Any]]],
    profile_indices: Sequence[int] | None,
) -> list[tuple[int, Mapping[str, Any]]]:
    if profile_indices is not None and len(profile_indices) != len(profiles):
        raise ValueError("profile_index_count_mismatch")
    result: list[tuple[int, Mapping[str, Any]]] = []
    for position, item in enumerate(profiles):
        if (
            isinstance(item, tuple)
            and len(item) == 2
            and isinstance(item[0], int)
            and not isinstance(item[0], bool)
            and isinstance(item[1], Mapping)
        ):
            index, profile = item
            if profile_indices is not None and profile_indices[position] != index:
                raise ValueError("profile_index_disagreement")
        elif isinstance(item, Mapping):
            profile = item
            if profile_indices is not None:
                index = profile_indices[position]
                declared_index = profile.get("profile_index")
                if declared_index is not None and declared_index != index:
                    raise ValueError("profile_index_disagreement")
            else:
                index = profile.get("profile_index")
                if not isinstance(index, int) or isinstance(index, bool):
                    raise ValueError("global_profile_index_required")
        else:
            raise TypeError("profile_entry_must_be_mapping_or_index_pair")
        if not isinstance(index, int) or isinstance(index, bool) or index < 0:
            raise ValueError("invalid_global_profile_index")
        result.append((index, profile))
    return result


def _role_scope(profile: Mapping[str, Any]) -> dict[str, Any]:
    # These are declared role/scope fields.  Do not infer a role from a path.
    return {
        key: _as_json(profile.get(key))
        for key in (
            "provenance",
            "kind",
            "support",
            "view",
            "retained_address",
            "retained_expansion",
        )
        if key in profile
    }


def _coordinate_member(outcome: Mapping[str, Any]) -> str | None:
    found = [key for key in _COORDINATE_FIELDS if key in outcome]
    if len(found) > 1:
        raise ValueError("multiple_coordinate_members")
    return found[0] if found else None


def _source_address(
    profile: Mapping[str, Any],
    outcome: Mapping[str, Any],
    metadata: Mapping[str, Any],
    study_uid: str | None,
) -> dict[str, Any]:
    observation = metadata.get("observation")
    observation = observation if isinstance(observation, Mapping) else {}
    fields = (
        "study_uid",
        "series_uid",
        "view",
        "slice_index",
        "support",
        "row",
        "label",
        "artifact",
    )
    address: dict[str, Any] = {
        "role_scope": _role_scope(profile),
        "caller_study_uid": _as_json(study_uid),
        "address_kind": _as_json(outcome.get("address_kind")),
        "owner_series_uid": _as_json(outcome.get("owner_series_uid")),
        "record_series_uid": _as_json(outcome.get("record_series_uid")),
        "target_series_uid": _as_json(outcome.get("target_series_uid")),
        "owner_view": _as_json(outcome.get("owner_view")),
        "record_view": _as_json(outcome.get("record_view")),
        "owner_slice_index": _as_json(outcome.get("owner_slice_index")),
        "record_slice_index": _as_json(outcome.get("record_slice_index")),
        "owner_artifact": _as_json(outcome.get("artifact")),
        "record_artifact": _as_json(outcome.get("record_artifact")),
        "target_artifact": _as_json(outcome.get("target_artifact")),
        "target_artifact_root": _as_json(outcome.get("target_artifact_root")),
        "target_artifact_status": _as_json(outcome.get("target_artifact_status")),
        "source_root": _as_json(outcome.get("source_root")),
        "owner_root": _as_json(outcome.get("owner_root")),
    }
    for field in fields:
        if field in observation:
            address[f"observation_{field}"] = _as_json(observation[field])
    for field in (
        "native_shape_rc",
        "plane_frame",
        "plane_frame_source",
        "packed_frame",
        "geometry_status",
        "scope_address",
        "lineage",
        "packed_family",
        "packed_row",
        "packed_slice",
        "declared_count",
        "count_interpreted_as_blocks",
        "support_block_count",
    ):
        if field in metadata:
            address[field] = _as_json(metadata[field])
    for field in ("slices", "address_frame"):
        if field in observation:
            address[f"observation_{field}"] = _as_json(observation[field])
    return address


def _meaning(
    profile: Mapping[str, Any], outcome: Mapping[str, Any], metadata: Mapping[str, Any]
) -> dict[str, Any]:
    bindings = metadata.get("bindings", [])
    semantic_bindings = []
    if isinstance(bindings, list):
        for binding in bindings:
            if isinstance(binding, Mapping):
                semantic_bindings.append(
                    {
                        key: _as_json(value)
                        for key, value in binding.items()
                        if key
                        not in {
                            "value",
                            "available",
                            "array",
                            "source_array",
                            "available_array",
                            "row_codes",
                            "source_values",
                        }
                    }
                )
            else:
                semantic_bindings.append(_as_json(binding))
    metrics = outcome.get("metrics", [])
    semantic_metrics = []
    if isinstance(metrics, list):
        for metric in metrics:
            if isinstance(metric, Mapping):
                semantic_metrics.append(
                    {
                        key: _as_json(metric.get(key))
                        for key in (
                            "bank",
                            "metric",
                            "status",
                            "row_names",
                            "nonfinite_available_count",
                        )
                        if key in metric
                    }
                )
            else:
                semantic_metrics.append(_as_json(metric))
    return {
        "role_scope": _role_scope(profile),
        "bindings": semantic_bindings,
        "source_refs": _as_json(metadata.get("source_refs", {})),
        "references": _as_json(metadata.get("references", [])),
        "metrics": semantic_metrics,
        "encoding_status": _as_json(outcome.get("encoding_status")),
        "status": _as_json(outcome.get("status")),
        "place_count": _as_json(outcome.get("place_count")),
    }


def _outcome_link(
    profile_index: int,
    outcome_index: int,
    profile: Mapping[str, Any],
    outcome: Mapping[str, Any],
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    coordinate = _coordinate_member(outcome)
    metrics = outcome.get("metrics", [])
    metric_links: list[dict[str, Any]] = []
    if isinstance(metrics, list):
        for metric in metrics:
            if isinstance(metric, Mapping):
                metric_links.append(
                    {
                        "bank": _as_json(metric.get("bank")),
                        "metric": _as_json(metric.get("metric")),
                        "status": _as_json(metric.get("status")),
                        "row_names": _as_json(metric.get("row_names")),
                        "row_codes_member": _as_json(metric.get("row_codes")),
                        "nonfinite_available_count": _as_json(
                            metric.get("nonfinite_available_count")
                        ),
                    }
                )
    refs = metadata.get("source_refs", {})
    if not isinstance(refs, Mapping):
        refs = {"malformed_source_refs": _as_json(refs)}
    status = outcome.get("status", "status_missing")
    count = outcome.get("place_count")
    coordinate_member = outcome.get(coordinate) if coordinate else None
    addressed = (
        coordinate is not None
        and isinstance(coordinate_member, str)
        and coordinate_member != ""
        and isinstance(outcome.get("address_kind"), str)
        and outcome.get("address_kind") != ""
        and isinstance(count, int)
        and not isinstance(count, bool)
        and count >= 0
    )
    link = {
        "profile_index": profile_index,
        "profile_object": _as_json(profile.get("object")),
        "provenance": _as_json(profile.get("provenance")),
        "kind": _as_json(profile.get("kind")),
        "support": _as_json(profile.get("support")),
        "profile_view": _as_json(profile.get("view")),
        "outcome_index": outcome_index,
        "status": _as_json(status),
        "encoding_status": _as_json(outcome.get("encoding_status")),
        "address_kind": _as_json(outcome.get("address_kind")),
        "coordinate_field": coordinate,
        "coordinate_member": _as_json(coordinate_member),
        "place_count": _as_json(count),
        "metrics": metric_links,
        "source_refs": _as_json(refs),
        "metadata": _as_json(metadata),
    }
    return {"addressed": addressed, "link": link}


def summarize_support_ownership(
    object_name: str,
    profiles: Sequence[Mapping[str, Any] | tuple[int, Mapping[str, Any]]],
    *,
    profile_indices: Sequence[int] | None = None,
    study_uid: str | None = None,
) -> dict[str, Any]:
    """Describe retained support ownership without reading or joining arrays.

    ``profiles`` may be the full profile list (each with its global
    ``profile_index``), a filtered list plus matching ``profile_indices``, or
    explicit ``(global_index, profile)`` pairs.  Filtered lists are never
    silently renumbered.
    """
    if not isinstance(object_name, str) or not object_name:
        raise ValueError("object_name_required")
    if not isinstance(profiles, Sequence) or isinstance(profiles, (str, bytes)):
        raise TypeError("profiles_must_be_sequence")

    if study_uid is not None and (not isinstance(study_uid, str) or not study_uid):
        raise ValueError("invalid_study_uid")
    indexed_profiles = _profile_entries(profiles, profile_indices)
    sources: list[_SupportGroup] = []
    non_place: list[dict[str, Any]] = []
    groups: dict[tuple[str, str], _SupportGroup] = {}
    conflicts: list[dict[str, Any]] = []

    for profile_index, profile in indexed_profiles:
        if profile.get("object") != object_name:
            raise ValueError("profile_object_mismatch")
        if (
            "profile_index" in profile
            and profile["profile_index"] is not None
            and profile["profile_index"] != profile_index
        ):
            raise ValueError("profile_index_disagreement")
        outcomes = profile.get("outcomes", [])
        if not isinstance(outcomes, list):
            raise TypeError("profile_outcomes_malformed")
        for outcome_index, outcome in enumerate(outcomes):
            if not isinstance(outcome, Mapping):
                raise TypeError("outcome_malformed")
            metadata = outcome.get("metadata", {})
            if not isinstance(metadata, Mapping):
                metadata = {"malformed_metadata": _as_json(metadata)}
            resolved = _outcome_link(
                profile_index, outcome_index, profile, outcome, metadata
            )
            if not resolved["addressed"]:
                non_place.append(resolved["link"])
                continue

            address = _source_address(profile, outcome, metadata, study_uid)
            meaning = _meaning(profile, outcome, metadata)
            address_key = _digest(address)
            meaning_key = _digest(meaning)
            group_key = (address_key, _digest(address["role_scope"]))
            group = groups.get(group_key)
            if group is None:
                group = _SupportGroup(
                    source_address=address,
                    source_address_fingerprint=address_key,
                    meaning_fingerprint=meaning_key,
                    meaning=meaning,
                    links=[],
                )
                groups[group_key] = group
            elif group["meaning_fingerprint"] != meaning_key:
                conflicts.append(
                    {
                        "code": "source_address_meaning_conflict",
                        "source_address_fingerprint": address_key,
                        "existing_meaning_fingerprint": group["meaning_fingerprint"],
                        "conflicting_meaning_fingerprint": meaning_key,
                        "links": [group["links"][0], resolved["link"]],
                    }
                )
            group["links"].append(resolved["link"])

    sources = sorted(
        groups.values(), key=lambda item: item["source_address_fingerprint"]
    )
    acquisition_keys: set[str] = set()
    acquisition_incomplete = False
    for source in sources:
        address = source["source_address"]
        identity = {
            "study_uid": address.get("caller_study_uid")
            or address.get("observation_study_uid"),
            "series_uid": address.get("target_series_uid"),
            "view": address.get("record_view") or address.get("observation_view"),
            "slice": address.get("record_slice_index")
            if address.get("record_slice_index") is not None
            else address.get("observation_slice_index"),
            "artifact": address.get("target_artifact"),
        }
        if any(value is None for value in identity.values()):
            acquisition_incomplete = True
        else:
            acquisition_keys.add(_digest(identity))

    if len(acquisition_keys) > 1 or acquisition_incomplete:
        overlap = "unresolved"
    elif acquisition_keys:
        overlap = "single_acquisition_only"
    else:
        overlap = "unresolved"

    frame_count = sum(
        1
        for source in sources
        if source["source_address"].get("plane_frame") is not None
        or source["source_address"].get("packed_frame") is not None
    )
    if sources and frame_count == len(sources):
        geometry = "frame_retained_for_each_addressed_support"
    elif frame_count:
        geometry = "partial_frame_retention"
    else:
        geometry = "no_frame_retained_or_unknown"

    return {
        "schema": "support_ownership.v1",
        "object": object_name,
        "addressed_supports": sources,
        "non_place_outcomes": non_place,
        "conflicts": conflicts,
        "physical_volume": "not_measured",
        "cross_acquisition_overlap": overlap,
        "geometry_retention": geometry,
        "summary_limits": [
            "supports retain their own address and role scope",
            "no cross-acquisition voxel union was computed",
            "support counts are not interpreted as physical volume",
            "missing acquisition or geometry identity remains unresolved",
        ],
    }
