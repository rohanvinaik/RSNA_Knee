"""Per-study bridge from retained observations to an exact typed encoding.

This module consumes declared profiles and existing saved arrays only. It does
not run recognition, choose references, infer missing measurements, or make a
diagnosis.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
from typing import Any

import numpy as np

from knee.array_archive import open_arrays, write_npz_xz
from knee.encoding import h5_store
from knee.encoding.carrier import CarrierError, CarrierOverflow, HadamardCarrier
from knee.encoding.coarse_adapter import (
    CoarseBlockLayout,
    CoarseTargetEvidence,
    encode_coarse_observation,
)
from knee.encoding.composition import (
    StudyComposer,
    _profile_inputs,
    prepare_composition,
)
from knee.encoding.composition_output import serialize_study_composition
from knee.encoding.handoff import AddressedEncoding, encode_observation
from knee.encoding.mri_spec import _base_readings, _profile_unread_bindings
from knee.encoding.packed_adapter import PackedSupportLayout, encode_packed_observation
from knee.encoding.places import (
    BankSpec,
    CompiledLayout,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    NumericReference,
    compile_layout,
)
from knee.encoding.sampled_profile_adapter import encode_sampled_profile_observation
from knee.encoding.scoped import ScopedEncoding
from knee.encoding.slice_profile_adapter import (
    encode_slice_profile_observation,
    slice_profile_layout_problem,
)
from knee.encoding.trace_adapter import TraceEncoding, encode_trace_observation
from knee.json_store import dump_json_atomic, load_json
from knee.objects.assignments import OBJECT_CODES
from knee.receipt import digest

_OBJECT_CONTEXT_FIELDS = (
    "anatomical_relations",
    "definition_decisions",
    "search_refusals",
    "unresolved",
)
_PREPARED_TOKEN = object()
_STORAGES = ("npz_xz", "h5")

_COARSE_FAMILY = "native_coarse_blocks"
_COARSE_TOKEN = "{arrays_prefix}"
_COARSE_REQUIRED = (
    "family",
    "offsets",
    "shapes",
    "slices",
    "windows_rc",
    "block_px",
    "block_mm",
    "packed_arrays",
)
_COARSE_OPTIONAL = ("frame_arrays", "count_meaning", "target_evidence")
_COARSE_FRAME_KEYS = ("origin_lps", "basis_lps", "normal_lps", "thickness_mm")
_COARSE_POLICIES = ("finite_values", "all_stored")


def _is_coarse_profile(profile: Mapping[str, Any]) -> bool:
    layout = profile.get("support_layout")
    return isinstance(layout, Mapping) and layout.get("family") == _COARSE_FAMILY


def _coarse_name_ok(name: object, tokenized: bool) -> bool:
    if not isinstance(name, str) or not name:
        return False
    if tokenized:
        rest = name[len(_COARSE_TOKEN) :]
        return (
            name.startswith(_COARSE_TOKEN + "_")
            and len(rest) > 1
            and "{" not in rest
            and "}" not in rest
        )
    return "{" not in name and "}" not in name


def _coarse_layout_problem(layout: object, profile: dict, readings: list) -> str | None:
    """Name the first problem in an explicit coarse declaration; no I/O."""
    if not isinstance(layout, dict):
        return "layout_not_object"
    keys = set(layout)
    if not set(_COARSE_REQUIRED) <= keys:
        return "missing_fields"
    if keys - set(_COARSE_REQUIRED) - set(_COARSE_OPTIONAL):
        return "unknown_fields"
    tokenized = "target_evidence" in layout
    if tokenized:
        evidence = layout["target_evidence"]
        if (
            not isinstance(evidence, dict)
            or set(evidence) != {"record_field", "orientation"}
            or evidence["record_field"] != "fibula_key_planes"
            or not isinstance(evidence["orientation"], str)
            or not evidence["orientation"]
        ):
            return "invalid_target_evidence"
    for field in ("offsets", "shapes", "slices", "windows_rc", "block_px", "block_mm"):
        if not _coarse_name_ok(layout[field], tokenized):
            return f"invalid_array_name:{field}"
    packed = layout["packed_arrays"]
    if (
        not isinstance(packed, list)
        or not packed
        or any(not _coarse_name_ok(name, tokenized) for name in packed)
        or len(set(packed)) != len(packed)
    ):
        return "invalid_packed_arrays"
    if "frame_arrays" in layout:
        frame = layout["frame_arrays"]
        if (
            not isinstance(frame, dict)
            or not frame
            or any(
                key not in _COARSE_FRAME_KEYS or not _coarse_name_ok(name, tokenized)
                for key, name in frame.items()
            )
        ):
            return "invalid_frame_arrays"
    if "count_meaning" in layout and layout["count_meaning"] != "coarse_blocks":
        return "invalid_count_meaning"
    if profile["provenance"] != "native" or profile["kind"] not in (
        "resolved",
        "reading",
    ):
        return "invalid_observation_kind"
    if not _coarse_name_ok(profile["support"], tokenized):
        return "invalid_support_name"
    if profile["support"] not in packed:
        return "support_not_declared_packed"
    for reading in readings:
        source = reading.get("source", "array")
        if source == "record_context":
            return "record_context_unsupported"
        if source != "array":
            continue
        if "window" in reading:
            return "window_unsupported"
        if reading.get("value") not in packed:
            return "reading_value_not_declared_packed"
        has_available = "available" in reading
        has_policy = "availability_policy" in reading
        if has_available == has_policy:
            return "availability_binding_invalid"
        if has_available and reading["available"] not in packed:
            return "reading_available_not_declared_packed"
        if has_policy and reading["availability_policy"] not in _COARSE_POLICIES:
            return "invalid_availability_policy"
    return None


def _concrete_name(name: str, prefix: str | None) -> str:
    if prefix is not None and name.startswith(_COARSE_TOKEN):
        return prefix + name[len(_COARSE_TOKEN) :]
    return name


def _resolve_coarse_prefix(
    record: Mapping[str, Any], observation: Mapping[str, Any], declaration: Mapping
) -> tuple[str | None, str | None]:
    """The one allowed resolution: this record's summary for this target series."""
    evidence = declaration["target_evidence"]
    planes = record.get(evidence["record_field"])
    uid = observation.get("series_uid")
    summary = (
        planes.get(uid)
        if isinstance(planes, Mapping) and isinstance(uid, str)
        else None
    )
    if not isinstance(summary, Mapping):
        return None, "target_evidence_missing"
    orientation = summary.get("orientation")
    if (
        not isinstance(orientation, str)
        or orientation.lower() != evidence["orientation"].lower()
    ):
        return None, "target_view_mismatch"
    prefix = summary.get("arrays_prefix")
    if not isinstance(prefix, str) or not prefix:
        return None, "arrays_prefix_mismatch"
    row, slices = observation.get("row"), observation.get("slices")
    if type(row) is not int or row < 0:
        return None, "invalid_packed_row"
    if (
        not isinstance(slices, (list, tuple))
        or len(slices) != 1
        or type(slices[0]) is not int
        or slices[0] < 0
    ):
        return None, "plane_address_required"
    read = summary.get("slices_read")
    if (
        not isinstance(read, list)
        or not all(type(v) is int for v in read)
        or row >= len(read)
        or read[row] != slices[0]
    ):
        return None, "target_slice_mismatch"
    return prefix, None


def _coarse_matches(candidates: list[tuple[dict, Path, str]], profile: Mapping):
    """Yield (record, root, root_name, observation, refusal_or_None)."""
    declaration = profile["support_layout"]
    tokenized = declaration.get("target_evidence") is not None
    tail = profile["support"][len(_COARSE_TOKEN) :] if tokenized else None
    for record, root, root_name in candidates:
        for observation in record.get("observations", []):
            if not (
                observation.get("object") == profile["object"]
                and observation.get("provenance") == profile["provenance"]
                and observation.get("kind") == profile["kind"]
                and _view_matches(profile.get("view"), observation.get("view"))
            ):
                continue
            if not tokenized:
                if observation.get("support") == profile["support"]:
                    yield record, root, root_name, observation, None
                continue
            support = observation.get("support")
            if not isinstance(support, str) or not support.endswith(tail):
                continue
            prefix, code = _resolve_coarse_prefix(record, observation, declaration)
            if code is not None:
                yield record, root, root_name, observation, code
                continue
            if not isinstance(prefix, str) or not prefix:
                yield record, root, root_name, observation, "arrays_prefix_mismatch"
                continue
            if not isinstance(tail, str):
                yield record, root, root_name, observation, "arrays_prefix_mismatch"
                continue
            if support == prefix + tail:
                yield record, root, root_name, observation, None
            else:
                yield record, root, root_name, observation, "arrays_prefix_mismatch"


def _coarse_inputs(profile: Mapping, record: Mapping, observation: Mapping):
    """Concrete CoarseBlockLayout and bindings for one retained row, or a named code."""
    declaration = _thaw(profile["support_layout"])
    evidence = declaration.get("target_evidence")
    prefix = None
    target = None
    if evidence is not None:
        prefix, code = _resolve_coarse_prefix(record, observation, declaration)
        if code is not None:
            return None, None, code
        if prefix is None:
            return None, None, "arrays_prefix_mismatch"
        if observation.get("support") != _concrete_name(profile["support"], prefix):
            return None, None, "arrays_prefix_mismatch"
        view = observation.get("view")
        owner_artifact = record.get("artifact")
        owner_series_uid = record.get("series_uid")
        target_series_uid = observation.get("series_uid")
        if (
            not isinstance(owner_artifact, str)
            or not owner_artifact
            or not isinstance(owner_series_uid, str)
            or not owner_series_uid
            or not isinstance(target_series_uid, str)
            or not target_series_uid
            or not isinstance(view, (tuple, list))
            or len(view) != 3
            or any(not isinstance(part, str) or not part for part in view)
        ):
            return None, None, "target_identity_invalid"
        target = CoarseTargetEvidence(
            owner_artifact,
            owner_series_uid,
            target_series_uid,
            tuple(view),
            evidence["record_field"],
            evidence["orientation"],
        )
    frame = declaration.get("frame_arrays")
    layout = CoarseBlockLayout(
        _concrete_name(declaration["offsets"], prefix),
        _concrete_name(declaration["shapes"], prefix),
        _concrete_name(declaration["slices"], prefix),
        _concrete_name(declaration["windows_rc"], prefix),
        _concrete_name(declaration["block_px"], prefix),
        _concrete_name(declaration["block_mm"], prefix),
        tuple(_concrete_name(n, prefix) for n in declaration["packed_arrays"]),
        None
        if frame is None
        else {k: _concrete_name(v, prefix) for k, v in frame.items()},
        declaration.get("count_meaning"),
        target,
    )
    bindings = []
    for reading in _thaw(profile["readings"]):
        item = dict(reading)
        for field in ("value", "available"):
            if isinstance(item.get(field), str):
                item[field] = _concrete_name(item[field], prefix)
        bindings.append(item)
    return layout, bindings, None


# Explicit ordinary image-mask families only. Packed, point, profile-vector,
# and trace families keep their dedicated source adapters.
_RETAINED_ORDINARY_2D_SUPPORTS = frozenset(
    {
        "a2_anterior_synovial_recess",
        "a2_synovium",
        "a2_iliotibial_band",
        "a2_joint_capsule",
        "a2_gastrocnemius_semimembranosus_bursa",
        "a2_popliteal_artery",
        "a2_popliteal_vein",
        "a2_sartorius",
        "a2_prefemoral_fat_pad",
        "a2_quadriceps_fat_pad",
        "a2_biceps_femoris_tendon",
        "a2_popliteus_tendon",
        "a2_medial_patellar_retinaculum",
        "a2_lateral_patellar_retinaculum",
        "a2_retinacula_positive_inner_lining",
        "a2_retinacula_negative_inner_lining",
    }
)
_RETAINED_ORDINARY_ROW_SUPPORTS = frozenset(
    {
        "a3_bone_plane_labels",
        "a3_femur_plane_region",
        "a3_tibia_plane_region",
        "a3_joint_plane_objects",
        "a3_joint_plane_reading",
        "a3_patella_plane_objects",
        "a4_patellofemoral_patellar_cartilage_support",
        "a4_patellofemoral_trochlear_cartilage_support",
        "a3_patella_twin_objects",
        "a3_patella_twin_pad_anterior",
        "a3_patella_twin_pad_posterior",
        "a3_recess_twin_recess",
        "a3_recess_twin_lining",
        "a3_recess_plane_recess",
        "a3_recess_plane_lining",
        "a3_recess_plane_fluid",
        "a3_recess_plane_medial_wall",
        "a3_recess_plane_lateral_wall",
        "a3_recess_plane_medial_lining",
        "a3_recess_plane_lateral_lining",
    }
)


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _finite_number(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        or isinstance(value, float)
        and math.isfinite(value)
    )


def validate_spec(spec: dict) -> dict:
    """Validate a JSON-shaped declaration and compile its explicit layout.

    The returned value contains the original declaration, carrier and compiled
    layout. No files are opened and no anatomical defaults are supplied.
    """
    if not isinstance(spec, dict):
        raise TypeError("encoding_spec_must_be_an_object")
    spec = deepcopy(spec)
    storage = spec.get("storage", "npz_xz")
    compact_h5 = spec.get("h5_compact", False)
    if not isinstance(compact_h5, bool):
        raise TypeError("h5_compact_must_be_bool")
    if not isinstance(storage, str) or storage not in _STORAGES:
        raise ValueError(f"invalid_encoding_storage:{storage!r}")
    retain_object_sources = spec.get("retain_object_sources", False)
    if not isinstance(retain_object_sources, bool):
        raise TypeError("retain_object_sources_must_be_bool")
    if retain_object_sources and storage != "h5":
        raise ValueError("object_sources_require_h5_storage")
    h5_encoding = spec.get("h5_encoding", "compact" if compact_h5 else "legacy")
    if not isinstance(h5_encoding, str) or h5_encoding not in (
        "legacy",
        "compact",
        "byte_xor",
        "modular_hybrid",
    ):
        raise ValueError(f"invalid_h5_encoding:{h5_encoding!r}")
    if compact_h5 and h5_encoding != "compact":
        raise ValueError("conflicting_h5_encoding")
    if storage == "h5":
        try:
            h5_store._h5py()
        except h5_store.OptionalDependencyError as error:
            raise h5_store.OptionalDependencyError(
                "h5_storage_unavailable: optional dependency 'h5py' is not installed"
            ) from error
    if "retained_ordinary_profiles" in spec and not isinstance(
        spec["retained_ordinary_profiles"], bool
    ):
        raise TypeError("retained_ordinary_profiles_must_be_bool")
    definition_enabled = spec.get("authored_definition_context", False)
    if not isinstance(definition_enabled, bool):
        raise TypeError("authored_definition_context_must_be_bool")
    definition_prepared = None
    if definition_enabled:
        from knee.encoding.mri_definition_context import prepare_definition_context

        definition_prepared = prepare_definition_context()
    version = spec.get("version")
    banks_raw = spec.get("banks")
    profiles_raw = spec.get("profiles")
    if not isinstance(version, str) or not version:
        raise ValueError("encoding_spec_version_required")
    if not isinstance(banks_raw, list) or not banks_raw:
        raise ValueError("encoding_spec_banks_required")
    if not isinstance(profiles_raw, list):
        raise TypeError("encoding_spec_profiles_required")

    bank_names: list[str] = []
    banks: list[BankSpec] = []
    metrics_by_bank: dict[str, set[str]] = {}
    metric_kinds: dict[tuple[str, str], MetricKind] = {}
    for bank in banks_raw:
        if not isinstance(bank, dict):
            raise TypeError("invalid_bank_declaration")
        name, facet, metrics_raw = (
            bank.get("name"),
            bank.get("facet"),
            bank.get("metrics"),
        )
        if (
            not isinstance(name, str)
            or not name
            or not isinstance(facet, str)
            or not facet
        ):
            raise ValueError("bank_name_and_facet_required")
        if not isinstance(metrics_raw, list) or not metrics_raw:
            raise ValueError(f"bank_metrics_required:{name}")
        metrics: list[MetricSpec] = []
        for metric in metrics_raw:
            if not isinstance(metric, dict):
                raise TypeError(f"invalid_metric_declaration:{name}")
            metric_name, kind = metric.get("name"), metric.get("kind")
            words = metric.get("words", [])
            if not isinstance(metric_name, str) or not metric_name:
                raise ValueError(f"metric_name_required:{name}")
            if not isinstance(kind, str):
                raise TypeError(f"metric_kind_required:{name}:{metric_name}")
            if not isinstance(words, list) or any(
                not isinstance(word, str) for word in words
            ):
                raise TypeError(f"invalid_metric_words:{name}:{metric_name}")
            try:
                metric_kind = MetricKind(kind)
            except ValueError as error:
                raise ValueError(f"unknown_metric_kind:{kind}") from error
            metrics.append(MetricSpec(metric_name, metric_kind, tuple(words)))
        bank_names.append(name)
        metrics_by_bank[name] = {metric.name for metric in metrics}
        metric_kinds.update({(name, metric.name): metric.kind for metric in metrics})
        banks.append(BankSpec(name, facet, tuple(metrics)))
    if len(set(bank_names)) != len(bank_names):
        raise ValueError("duplicate_bank_name")

    carrier = HadamardCarrier.from_banks(bank_names)
    compiled = compile_layout(LayoutSpec(version, carrier.identity, tuple(banks)))
    if compiled is None:
        raise ValueError("invalid_encoding_layout")

    profiles: list[dict] = []
    for profile_index, profile in enumerate(profiles_raw):
        if not isinstance(profile, dict):
            raise TypeError(f"invalid_profile:{profile_index}")
        for field in ("object", "provenance", "kind", "support"):
            if not isinstance(profile.get(field), str) or not profile[field]:
                raise ValueError(f"profile_{field}_required:{profile_index}")
        if profile["provenance"] not in ("native", "laid", "projected"):
            raise ValueError(f"invalid_profile_provenance:{profile_index}")
        if profile["kind"] not in ("resolved", "reading", "target"):
            raise ValueError(f"invalid_profile_kind:{profile_index}")
        if (profile["provenance"] == "projected") != (profile["kind"] == "target"):
            raise ValueError(f"profile_target_provenance_mismatch:{profile_index}")
        view = profile.get("view")
        if view is not None and (
            not isinstance(view, list)
            or len(view) != 3
            or any(not isinstance(part, str) for part in view)
        ):
            raise ValueError(f"invalid_profile_view:{profile_index}")
        readings = profile.get("readings")
        if not isinstance(readings, list):
            raise TypeError(f"profile_readings_required:{profile_index}")
        support_layout = profile.get("support_layout")
        trace_family = (
            isinstance(support_layout, dict)
            and support_layout.get("family") == "posterior_trace"
        )
        sampled_profile_family = (
            isinstance(support_layout, dict)
            and support_layout.get("family") == "joint_axial_profile_samples"
        )
        slice_profile_family = (
            isinstance(support_layout, dict)
            and support_layout.get("family") == "native_slice_profile_values"
        )
        coarse_family = (
            isinstance(support_layout, dict)
            and support_layout.get("family") == _COARSE_FAMILY
        )
        reading_keys: list[tuple[str, str]] = []
        for reading in readings:
            if not isinstance(reading, dict):
                raise TypeError(f"invalid_profile_reading:{profile_index}")
            key = (reading.get("bank"), reading.get("metric"))
            source = reading.get("source", "array")
            if source == "unread":
                source_valid = (
                    isinstance(reading.get("reason"), str)
                    and bool(reading["reason"].strip())
                    and not any(
                        field in reading
                        for field in (
                            "value",
                            "available",
                            "window",
                            "path",
                            "scope",
                        )
                    )
                )
            elif source == "record_context":
                path = reading.get("path")
                scope = reading.get("scope")
                source_valid = (
                    isinstance(path, list)
                    and bool(path)
                    and all(
                        isinstance(part, str)
                        and bool(part)
                        and "*" not in part
                        or isinstance(part, int)
                        and not isinstance(part, bool)
                        and part >= 0
                        for part in path
                    )
                    and scope in ("acquisition", "record_plane")
                    and not any(
                        field in reading for field in ("value", "available", "window")
                    )
                )
            elif source == "status_words":
                source_valid = not any(
                    field in reading
                    for field in ("value", "available", "window", "path", "scope")
                )
            else:
                source_valid = source == "array" and (
                    "path" not in reading and "scope" not in reading
                )
            binding_valid = (
                source_valid
                and isinstance(key[0], str)
                and isinstance(key[1], str)
                and key[0] in metrics_by_bank
                and key[1] in metrics_by_bank[key[0]]
            )
            if source in ("record_context", "unread"):
                binding_valid = binding_valid and isinstance(reading.get("source"), str)
            elif source == "status_words":
                binding_valid = (
                    binding_valid
                    and slice_profile_family
                    and isinstance(reading.get("source"), str)
                    and metric_kinds.get(key) is MetricKind.WORDS
                )
            elif source == "array":
                binding_valid = binding_valid and (
                    isinstance(reading.get("value"), str)
                    and bool(reading["value"])
                    and (
                        trace_family
                        or coarse_family
                        or (
                            isinstance(reading.get("available"), str)
                            and bool(reading["available"])
                        )
                    )
                    and (
                        "window" not in reading
                        or isinstance(reading["window"], str)
                        and bool(reading["window"])
                    )
                )
            if not binding_valid:
                raise ValueError(f"invalid_profile_reading_binding:{profile_index}")
            reading_keys.append(key)
        if len(set(reading_keys)) != len(reading_keys):
            raise ValueError(f"duplicate_profile_reading:{profile_index}")
        expected_keys = {
            (bank.name, metric.name) for bank in banks for metric in bank.metrics
        }
        if set(reading_keys) != expected_keys:
            raise ValueError(f"profile_metric_bindings_incomplete:{profile_index}")

        if support_layout is not None:
            if trace_family:
                expected_trace_layout = {
                    "family": "posterior_trace",
                    "identity_sources": {
                        "owner_artifact": "observation.artifact",
                        "target_series_uid": "target_record.series_uid",
                        "target_view": "target_record.view",
                        "target_slice": "observation.slices[0]",
                        "row": "observation.row",
                    },
                    "offsets_suffix": "_offsets",
                    "slices_suffix": "_slices",
                    "starts_suffix": "_starts",
                    "stops_suffix": "_stops",
                    "coordinates": "patient_lps",
                    "availability": "finite_values",
                }
                if (
                    support_layout != expected_trace_layout
                    or profile["provenance"] != "native"
                    or profile["kind"] != "reading"
                    or profile["support"]
                    != f"a3_posterior_trace_{profile['object']}_points_lps"
                ):
                    raise ValueError(f"invalid_trace_support_family:{profile_index}")
                if any(
                    (
                        reading.get("source") == "unread"
                        and (
                            "value" in reading
                            or "available" in reading
                            or "window" in reading
                            or "path" in reading
                            or "scope" in reading
                            or not isinstance(reading.get("reason"), str)
                            or not reading["reason"].strip()
                        )
                    )
                    or (
                        reading.get("source", "array") == "array"
                        and (
                            reading.get("value") not in ("light", "flank")
                            or "available" in reading
                            or "window" in reading
                            or metric_kinds.get((reading["bank"], reading["metric"]))
                            is not MetricKind.DIGIT
                        )
                    )
                    or reading.get("source", "array")
                    not in (
                        "array",
                        "unread",
                        "record_context",
                    )
                    for reading in readings
                ):
                    raise ValueError(f"invalid_trace_reading_binding:{profile_index}")
            elif slice_profile_family:
                problem = slice_profile_layout_problem(support_layout)
                if (
                    problem is not None
                    or profile["support"] != support_layout["support"]
                    or profile["provenance"] != "native"
                    or profile["kind"] not in ("resolved", "reading")
                    or any(
                        reading.get("source", "array") == "array"
                        and (
                            reading.get("value") != support_layout["values"]
                            or reading.get("available") != support_layout["status"]
                            or "window" in reading
                            or metric_kinds.get((reading["bank"], reading["metric"]))
                            is not MetricKind.DIGIT
                        )
                        or reading.get("source") == "status_words"
                        and metric_kinds.get(
                            (reading.get("bank"), reading.get("metric"))
                        )
                        is not MetricKind.WORDS
                        for reading in readings
                    )
                ):
                    raise ValueError(
                        f"invalid_slice_profile_layout:{profile_index}:{problem}"
                    )
            elif sampled_profile_family:
                expected_sample_layout = {
                    "family": "joint_axial_profile_samples",
                    "offsets": "a4_joint_axial_profile_offsets",
                    "slices": "a4_joint_axial_profile_slices",
                    "coordinates": "a4_joint_axial_profile_rc",
                    "white": "a4_joint_axial_profile_white",
                    "valid": "a4_joint_axial_profile_valid",
                    "light": "a4_joint_axial_profile_light",
                }
                if (
                    support_layout != expected_sample_layout
                    or profile["object"] != "joint"
                    or profile["provenance"] != "native"
                    or profile["kind"] != "reading"
                    or profile["support"] != "a4_joint_axial_profile_white"
                ):
                    raise ValueError(f"invalid_sample_profile_family:{profile_index}")
                if any(
                    reading.get("source", "array")
                    not in ("array", "unread", "record_context")
                    or reading.get("source", "array") == "array"
                    and (
                        reading.get("value")
                        not in (
                            "a4_joint_axial_profile_white",
                            "a4_joint_axial_profile_light",
                        )
                        or reading.get("available") != "a4_joint_axial_profile_valid"
                        or "window" in reading
                    )
                    for reading in readings
                ):
                    raise ValueError(f"invalid_sample_profile_binding:{profile_index}")
            elif coarse_family:
                problem = _coarse_layout_problem(support_layout, profile, readings)
                if problem is not None:
                    raise ValueError(f"invalid_coarse_layout:{profile_index}:{problem}")
            elif (
                not isinstance(support_layout, dict)
                or set(support_layout)
                != {
                    "family",
                    "identity_sources",
                    "offsets",
                    "shapes",
                    "slices",
                    "packed_arrays",
                    "target_pixels_array",
                    "frame_arrays",
                    "count_meaning",
                }
                or support_layout.get("family") != "fibula_axial"
                or profile["object"] != "fibula"
                or profile["provenance"] != "native"
                or profile["kind"] != "reading"
                or profile["support"] != "a3_fibula_axial_region"
            ):
                raise ValueError(f"invalid_packed_support_family:{profile_index}")
            if (
                not trace_family
                and not sampled_profile_family
                and not slice_profile_family
                and not coarse_family
            ):
                identity_sources = support_layout.get("identity_sources")
                if identity_sources != {
                    "owner_series_uid": "record.series_uid",
                    "artifact": "record.artifact",
                    "target_series_uid": "axial_evidence.series_uid",
                    "target_view": "axial_evidence.view",
                    "target_slice": "axial_evidence.slice",
                    "row": "observation.row_to_axial_evidence.row",
                }:
                    raise ValueError(f"invalid_packed_identity_sources:{profile_index}")
                for field, expected_name in (
                    ("offsets", "a3_fibula_axial_offsets"),
                    ("shapes", "a3_fibula_axial_shapes"),
                    ("slices", "a3_fibula_axial_slices"),
                    ("target_pixels_array", "a3_fibula_axial_target"),
                    ("count_meaning", "fibula_axial_target_pixels"),
                ):
                    if support_layout.get(field) != expected_name:
                        raise ValueError(
                            f"invalid_packed_layout_field:{profile_index}:{field}"
                        )
                packed_arrays = support_layout.get("packed_arrays")
                if (
                    not isinstance(packed_arrays, list)
                    or any(
                        not isinstance(name, str) or not name for name in packed_arrays
                    )
                    or len(set(packed_arrays)) != len(packed_arrays)
                    or not {
                        "a3_fibula_axial_region",
                        "a3_fibula_axial_target",
                        "a3_fibula_axial_available",
                    }.issubset(packed_arrays)
                ):
                    raise ValueError(f"invalid_packed_arrays:{profile_index}")
                frame_arrays = support_layout.get("frame_arrays")
                if frame_arrays != {
                    "origin_lps": "a3_fibula_axial_origin_lps",
                    "basis_lps": "a3_fibula_axial_basis_lps",
                    "normal_lps": "a3_fibula_axial_normal_lps",
                    "thickness_mm": "a3_fibula_axial_thickness_mm",
                }:
                    raise ValueError(f"invalid_packed_frame_arrays:{profile_index}")
                if profile["support"] not in packed_arrays:
                    raise ValueError(f"packed_support_not_declared:{profile_index}")
                if any(
                    reading.get("source") == "record_context" for reading in readings
                ):
                    raise ValueError(
                        f"packed_record_context_unsupported:{profile_index}"
                    )
                if any(
                    reading.get("source", "array") == "array"
                    and any(
                        reading[field] not in packed_arrays
                        for field in ("value", "available")
                    )
                    for reading in readings
                ) or any(
                    reading.get("source", "array") == "array" and "window" in reading
                    for reading in readings
                ):
                    raise ValueError(f"invalid_packed_reading_binding:{profile_index}")

        references = profile.get("references", [])
        if not isinstance(references, list):
            raise TypeError(f"invalid_profile_references:{profile_index}")
        reference_keys: list[tuple[str, str]] = []
        for reference in references:
            if not isinstance(reference, dict):
                raise TypeError(f"invalid_profile_reference:{profile_index}")
            key = (reference.get("bank"), reference.get("metric"))
            if (
                key not in expected_keys
                or any(
                    not isinstance(reference.get(field), str) or not reference[field]
                    for field in ("reference_id", "source", "units")
                )
                or any(
                    not _finite_number(reference.get(field))
                    for field in ("low", "high")
                )
                or metric_kinds.get(key) is not MetricKind.DIGIT
                or reference["low"] > reference["high"]
            ):
                raise ValueError(f"invalid_profile_reference_fields:{profile_index}")
            reference_keys.append(key)
        if len(set(reference_keys)) != len(reference_keys):
            raise ValueError(f"duplicate_profile_reference:{profile_index}")
        profiles.append(profile)

    composition = None
    if "object_composition" in spec:
        preparation = prepare_composition(
            compiled, profiles, spec["object_composition"]
        )
        if preparation.prepared is None:
            raise ValueError(
                f"invalid_object_composition:{preparation.code.value}:{preparation.detail}"
            )
        composition = preparation.prepared
    spec_bytes = json.dumps(
        spec, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return {
        "_prepared_token": _PREPARED_TOKEN,
        "spec": _freeze(spec),
        "spec_sha256": hashlib.sha256(spec_bytes).hexdigest(),
        "carrier": carrier,
        "layout": compiled,
        "profiles": tuple(_freeze(profile) for profile in profiles),
        "storage": storage,
        "retain_object_sources": retain_object_sources,
        "h5_compact": compact_h5,
        "h5_encoding": h5_encoding,
        "definition_context": definition_prepared,
        "composition": composition,
    }


def _view_matches(expected: list[str] | tuple[str, ...] | None, actual: object) -> bool:
    if expected is None:
        return True
    return isinstance(actual, (tuple, list)) and tuple(actual) == tuple(expected)


def _matching_observations(candidates: list[tuple[dict, Path, str]], profile: dict):
    for record, root, root_name in candidates:
        for observation_index, observation in enumerate(record.get("observations", [])):
            if (
                observation.get("object") == profile["object"]
                and observation.get("provenance") == profile["provenance"]
                and observation.get("kind") == profile["kind"]
                and observation.get("support") == profile["support"]
                and _view_matches(profile.get("view"), observation.get("view"))
                and _retained_address_matches(
                    profile.get("retained_address"),
                    record,
                    observation,
                    observation_index,
                    root_name,
                )
            ):
                yield record, root, root_name, observation


def _retained_address_matches(
    selector: object,
    record: dict,
    observation: dict,
    observation_index: int,
    root_name: str,
) -> bool:
    if selector is None:
        return True
    if not isinstance(selector, Mapping):
        return False
    expected_index = selector.get("observation_index")
    if (
        not isinstance(expected_index, int)
        or isinstance(expected_index, bool)
        or expected_index != observation_index
        or selector.get("owner_collection") != root_name
        or selector.get("artifact") != record.get("artifact")
        or selector.get("series_uid") != record.get("series_uid")
        or selector.get("record_slice_index") != record.get("slice_index")
    ):
        return False
    for key in (
        "object",
        "provenance",
        "kind",
        "support",
        "support_address_kind",
        "view",
        "slices",
        "row",
        "label",
        "count",
        "address_frame",
    ):
        actual, expected = observation.get(key), selector.get(key)
        if key in ("view", "slices"):
            if not isinstance(actual, (tuple, list)) or tuple(actual) != tuple(
                expected or ()
            ):
                return False
        elif key == "address_frame":
            if _thaw(actual) != _thaw(expected):
                return False
        elif actual != expected:
            return False
    return True


def _dynamic_native_plane_support(support: object) -> tuple[str, str, int] | None:
    """Return the producer-owned object, orientation and slice in a native plane key.

    These keys identify one full native boolean plane directly; unlike packed families, they
    carry no row index. The caller still checks the observation's object/view/slice and frame.
    """
    if not isinstance(support, str) or not support.endswith("_support"):
        return None
    families = (
        *(
            (f"a4_{name}_z", name, "sagittal")
            for name in ("medial_meniscus", "lateral_meniscus")
        ),
        *(
            (f"a4_axial_{name}_z", name, "axial")
            for name in ("medial_meniscus", "lateral_meniscus")
        ),
        *(
            (f"a4_{orientation}_{name}_z", name, orientation)
            for orientation, names in (("axial", ("pcl", "mcl")), ("coronal", ("pcl",)))
            for name in names
        ),
    )
    for prefix, object_name, orientation in families:
        if not support.startswith(prefix):
            continue
        slice_text = support[len(prefix) : -len("_support")]
        if not slice_text.isdecimal():
            return None
        try:
            slice_index = int(slice_text)
        except (ValueError, OverflowError):
            return None
        if str(slice_index) != slice_text:
            return None
        return object_name, orientation, slice_index
    return None


def _retained_ordinary_profiles(
    records: list, main_records: list, banks: list | None = None
) -> list[dict]:
    """Describe only known ordinary image-mask observations by exact address."""
    profiles: list[dict] = []
    candidates = [
        *((record, "run") for record in records),
        *((record, "main") for record in main_records),
    ]
    for record, owner_collection in candidates:
        if not isinstance(record, dict) or not isinstance(
            record.get("observations"), list
        ):
            continue
        for observation_index, observation in enumerate(record["observations"]):
            if not isinstance(observation, dict):
                continue
            object_name = observation.get("object")
            if (
                not isinstance(object_name, str)
                or OBJECT_CODES.get(object_name, 0) == 0
            ):
                continue
            support, row = observation.get("support"), observation.get("row")
            provenance, kind = observation.get("provenance"), observation.get("kind")
            dynamic_support = _dynamic_native_plane_support(support)
            stamped_native_rc = (
                observation.get("support_address_kind") == "native_rc"
                and provenance == "native"
            )
            if isinstance(support, str) and support in _RETAINED_ORDINARY_2D_SUPPORTS:
                if row is not None:
                    continue
            elif (
                isinstance(support, str) and support in _RETAINED_ORDINARY_ROW_SUPPORTS
            ):
                if not isinstance(row, int) or isinstance(row, bool) or row < 0:
                    continue
            elif dynamic_support is not None:
                if row is not None:
                    continue
            elif stamped_native_rc:
                if (
                    not isinstance(support, str)
                    or not support
                    or (
                        row is not None
                        and (
                            not isinstance(row, int) or isinstance(row, bool) or row < 0
                        )
                    )
                ):
                    continue
            else:
                continue
            if provenance not in ("native", "laid") or kind not in (
                "resolved",
                "reading",
            ):
                continue
            if observation.get("artifact") != record.get("artifact") or observation.get(
                "series_uid"
            ) != record.get("series_uid"):
                continue
            view = observation.get("view")
            if (
                not isinstance(view, (tuple, list))
                or len(view) != 3
                or any(not isinstance(part, str) or not part for part in view)
            ):
                continue
            slices = observation.get("slices")
            if (
                not isinstance(slices, (tuple, list))
                or len(slices) != 1
                or not isinstance(slices[0], int)
                or isinstance(slices[0], bool)
                or slices[0] < 0
            ):
                continue
            if dynamic_support is not None and (
                dynamic_support[0] != object_name
                or dynamic_support[1] != view[0].casefold()
                or dynamic_support[2] != slices[0]
                or not isinstance(observation.get("address_frame"), dict)
            ):
                continue
            same_slice = slices[0] == record.get("slice_index")
            if not same_slice and observation.get("address_frame") is None:
                continue
            readings = [*_base_readings(), *_profile_unread_bindings()]
            declared_banks: list[dict[str, Any]]
            if banks is None:
                declared_banks = [
                    {
                        "name": "native_profile_area",
                        "metrics": [{"name": "area_mm2"}],
                    },
                    {
                        "name": "native_profile_status",
                        "metrics": [{"name": "status"}],
                    },
                ]
            else:
                declared_banks = []
                for bank in banks:
                    if (
                        not isinstance(bank, dict)
                        or not isinstance(bank.get("name"), str)
                        or not isinstance(bank.get("metrics"), list)
                    ):
                        raise TypeError("ordinary_expansion_bank_declaration_invalid")
                    metrics = bank["metrics"]
                    if any(
                        not isinstance(metric, dict)
                        or not isinstance(metric.get("name"), str)
                        for metric in metrics
                    ):
                        raise TypeError("ordinary_expansion_bank_declaration_invalid")
                    declared_banks.append(bank)
            bound = {(item.get("bank"), item.get("metric")) for item in readings}
            for bank in declared_banks:
                bank_name = bank["name"]
                for metric in bank["metrics"]:
                    metric_name = metric["name"]
                    if (bank_name, metric_name) not in bound:
                        readings.append(
                            {
                                "bank": bank_name,
                                "metric": metric_name,
                                "source": "unread",
                                "reason": "this retained ordinary observation has no value for this declared facet",
                            }
                        )
            if not same_slice:
                readings = [
                    {
                        "bank": item["bank"],
                        "metric": item["metric"],
                        "source": "unread",
                        "reason": "measurement_not_retained_for_observation_slice",
                    }
                    if item["bank"] not in ("acquisition_context",)
                    else item
                    for item in readings
                ]
            profiles.append(
                {
                    "object": observation.get("object"),
                    "provenance": provenance,
                    "kind": kind,
                    "support": support,
                    "view": list(view),
                    "readings": readings,
                    "references": [],
                    "retained_address": {
                        "owner_collection": owner_collection,
                        "artifact": record.get("artifact"),
                        "series_uid": record.get("series_uid"),
                        "record_slice_index": record.get("slice_index"),
                        "observation_index": observation_index,
                        "object": observation.get("object"),
                        "provenance": provenance,
                        "kind": kind,
                        "support": support,
                        "support_address_kind": observation.get("support_address_kind"),
                        "view": list(view),
                        "slices": list(slices),
                        "row": row,
                        "label": observation.get("label"),
                        "count": observation.get("count"),
                        "address_frame": observation.get("address_frame"),
                    },
                    "retained_expansion": "ordinary_known_plane_family_v1",
                }
            )
    return profiles


def _retained_ordinary_dispositions(
    records: list,
    main_records: list,
    base_profiles: tuple,
    generated_profiles: list[dict],
) -> list[dict]:
    """Record named non-expansion reasons for each retained observation."""
    generated = {
        (
            item["retained_address"]["owner_collection"],
            item["retained_address"]["artifact"],
            item["retained_address"]["observation_index"],
        )
        for item in generated_profiles
    }
    exact_base_profiles = {
        (
            item.get("object"),
            item.get("provenance"),
            item.get("kind"),
            item.get("support"),
            tuple(item["view"]),
        )
        for item in base_profiles
        if isinstance(item.get("view"), (tuple, list))
    }
    any_view_base_profiles = {
        (
            item.get("object"),
            item.get("provenance"),
            item.get("kind"),
            item.get("support"),
        )
        for item in base_profiles
        if item.get("view") is None
    }
    dispositions: list[dict] = []
    candidates = [
        *((record, "run") for record in records),
        *((record, "main") for record in main_records),
    ]
    for record, owner_collection in candidates:
        if not isinstance(record, dict) or not isinstance(
            record.get("observations"), list
        ):
            continue
        for index, observation in enumerate(record["observations"]):
            if not isinstance(observation, dict):
                dispositions.append(
                    {
                        "owner_collection": owner_collection,
                        "artifact": record.get("artifact"),
                        "observation_index": index,
                        "disposition": "invalid_observation_record",
                    }
                )
                continue
            if (owner_collection, record.get("artifact"), index) in generated:
                continue
            identity = (
                observation.get("object"),
                observation.get("provenance"),
                observation.get("kind"),
                observation.get("support"),
            )
            view = observation.get("view")
            if identity in any_view_base_profiles or (
                isinstance(view, (tuple, list))
                and (*identity, tuple(view)) in exact_base_profiles
            ):
                continue
            provenance, kind = observation.get("provenance"), observation.get("kind")
            support = observation.get("support")
            if provenance == "projected" or kind == "target":
                reason = "projected_target_not_observation"
            elif (
                not isinstance(observation.get("object"), str)
                or observation.get("object") not in OBJECT_CODES
                or OBJECT_CODES.get(observation.get("object"), 0) == 0
            ):
                reason = "unsupported_object_identity_metadata"
            elif (
                (
                    isinstance(support, str)
                    and support
                    in (
                        _RETAINED_ORDINARY_2D_SUPPORTS | _RETAINED_ORDINARY_ROW_SUPPORTS
                    )
                )
                or _dynamic_native_plane_support(support) is not None
                or (
                    observation.get("support_address_kind") == "native_rc"
                    and provenance == "native"
                )
            ):
                dynamic_support = _dynamic_native_plane_support(support)
                if provenance not in ("native", "laid") or kind not in (
                    "resolved",
                    "reading",
                ):
                    reason = "unsupported_provenance_or_kind"
                elif observation.get("artifact") != record.get(
                    "artifact"
                ) or observation.get("series_uid") != record.get("series_uid"):
                    reason = "different_owner_artifact"
                elif not _valid_observation_view(observation.get("view")):
                    reason = "invalid_observation_view"
                elif not _valid_single_slice(observation.get("slices")):
                    reason = "invalid_observation_slice_address"
                elif dynamic_support is not None and (
                    dynamic_support[0] != observation.get("object")
                ):
                    reason = "dynamic_native_support_object_mismatch"
                elif dynamic_support is not None and (
                    dynamic_support[1]
                    != str(observation.get("view", [""])[0]).casefold()
                ):
                    reason = "dynamic_native_support_view_mismatch"
                elif dynamic_support is not None and (
                    dynamic_support[2] != observation["slices"][0]
                ):
                    reason = "dynamic_native_support_slice_mismatch"
                elif (
                    (
                        support in _RETAINED_ORDINARY_ROW_SUPPORTS
                        or observation.get("support_address_kind") == "native_rc"
                    )
                    and observation.get("row") is not None
                    and (
                        not isinstance(observation.get("row"), int)
                        or isinstance(observation.get("row"), bool)
                        or observation["row"] < 0
                    )
                ):
                    reason = "invalid_observation_row_address"
                elif (
                    observation["slices"][0] != record.get("slice_index")
                    and observation.get("address_frame") is None
                ):
                    reason = "missing_observation_address_frame"
                elif dynamic_support is not None and (
                    observation.get("row") is not None
                    or not isinstance(observation.get("address_frame"), dict)
                ):
                    reason = "dynamic_native_support_address_malformed"
                else:
                    reason = "ordinary_address_not_expanded"
            else:
                reason = "unsupported_family"
            dispositions.append(
                {
                    "owner_collection": owner_collection,
                    "artifact": record.get("artifact"),
                    "series_uid": record.get("series_uid"),
                    "record_slice_index": record.get("slice_index"),
                    "observation_index": index,
                    "object": observation.get("object"),
                    "provenance": provenance,
                    "kind": kind,
                    "support": support,
                    "support_address_kind": observation.get("support_address_kind"),
                    "view": observation.get("view"),
                    "slices": observation.get("slices"),
                    "row": observation.get("row"),
                    "label": observation.get("label"),
                    "disposition": reason,
                }
            )
    return dispositions


def _valid_observation_view(value: object) -> bool:
    return (
        isinstance(value, (tuple, list))
        and len(value) == 3
        and all(isinstance(part, str) and part for part in value)
    )


def _valid_single_slice(value: object) -> bool:
    return (
        isinstance(value, (tuple, list))
        and len(value) == 1
        and isinstance(value[0], int)
        and not isinstance(value[0], bool)
        and value[0] >= 0
    )


def _expand_retained_profiles(
    validated: dict, records: list, main_records: list
) -> dict:
    if not validated["spec"].get("retained_ordinary_profiles", False):
        return validated
    expanded = _thaw(validated["spec"])
    additions = _retained_ordinary_profiles(
        records, main_records, _thaw(validated["spec"]["banks"])
    )
    dispositions = _retained_ordinary_dispositions(
        records, main_records, validated["profiles"], additions
    )
    expanded["profiles"].extend(additions)
    expansion_state = {
        "version": "retained-ordinary-expansion-state-v1",
        "expanded_observation_count": len(additions),
        "not_expanded": dispositions,
    }
    expanded["retained_ordinary_expansion_state"] = expansion_state
    spec_bytes = json.dumps(
        expanded,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    profiles = [*validated["profiles"], *(_freeze(item) for item in additions)]
    composition = validated["composition"]
    if composition is not None:
        parsed_additions, problem = _profile_inputs(additions, composition.base_layout)
        if problem is not None:
            raise ValueError(f"invalid_generated_composition_profiles:{problem}")
        if any(
            item.object_name not in composition.profile_layouts
            or item.references
            or item.view is not None
            and item.view not in composition.view_roles
            for item in parsed_additions
        ):
            raise ValueError("generated_profile_changes_prepared_composition_contract")
        composition = replace(
            composition,
            profiles=(*composition.profiles, *parsed_additions),
        )
    return {
        **validated,
        "spec": _freeze(expanded),
        "spec_sha256": hashlib.sha256(spec_bytes).hexdigest(),
        "profiles": tuple(profiles),
        "composition": composition,
    }


def _artifact_path(root: Path, artifact: object) -> Path | None:
    if not isinstance(artifact, str) or not artifact:
        return None
    base = root.resolve()
    candidate = Path(artifact)
    resolved = (
        candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    )
    try:
        resolved.relative_to(base)
    except ValueError:
        return None
    return resolved


def _composition_study_map(result: dict, run_dir: Path) -> tuple[dict, dict]:
    """Reuse the already-produced study map; never reconstruct its geometry."""
    summary = result.get("study_map")
    if not isinstance(summary, Mapping) or (
        summary.get("schema") != "study_map/v1" and not summary.get("file")
    ):
        # The real study entry point returns map counts at result.study_map;
        # finish_map publishes the file pointer on its first source record.
        summaries = [
            record["study_map"]
            for record in result.get("records", ())
            if isinstance(record, Mapping)
            and record.get("study_uid") == result.get("study_uid")
            and isinstance(record.get("study_map"), Mapping)
            and record["study_map"].get("file")
        ]
        if len(summaries) != 1:
            return {}, {
                "status": (
                    "study_map_not_retained"
                    if not summaries
                    else "study_map_source_ambiguous"
                )
            }
        summary = summaries[0]
    source = "in_memory"
    if summary.get("schema") == "study_map/v1":
        record = _thaw(summary)
    else:
        path = _artifact_path(run_dir, summary.get("file"))
        if path is None:
            return {}, {"status": "invalid_study_map_path"}
        study_uid = result.get("study_uid")
        if (
            not isinstance(study_uid, str)
            or path.parent != (run_dir / study_uid).resolve()
        ):
            return {}, {"status": "study_map_study_mismatch", "file": str(path)}
        try:
            record = load_json(path)
        except (OSError, ValueError) as error:
            return {}, {
                "status": "study_map_unreadable",
                "file": str(path),
                "detail": str(error),
            }
        source = str(path)
    if not isinstance(record, dict) or record.get("schema") != "study_map/v1":
        return {}, {"status": "invalid_study_map_schema", "source": source}
    try:
        canonical = json.dumps(
            record, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError):
        return {}, {"status": "invalid_study_map_values", "source": source}
    return record, {
        "status": "ok",
        "source": source,
        "study_uid": result.get("study_uid"),
        "record_sha256": hashlib.sha256(canonical).hexdigest(),
        "digest_meaning": "canonical complete study_map/v1 JSON value",
    }


def _packed_layout_for_observation(
    declaration: Mapping[str, Any], record: dict, observation: dict
) -> PackedSupportLayout:
    """Bind the declared fibula packed-address fields to this retained row."""
    view = observation.get("view")
    return PackedSupportLayout(
        family=declaration["family"],
        owner_series_uid=record.get("series_uid", ""),
        target_series_uid=observation.get("series_uid", ""),
        target_view=tuple(view) if isinstance(view, (list, tuple)) else (),
        offsets=declaration["offsets"],
        shapes=declaration["shapes"],
        slices=declaration["slices"],
        packed_arrays=tuple(declaration["packed_arrays"]),
        target_pixels_array=declaration["target_pixels_array"],
        frame_arrays=declaration["frame_arrays"],
        count_meaning=declaration["count_meaning"],
    )


def _references(
    profile: dict, layout: CompiledLayout
) -> dict[tuple[str, str], NumericReference]:
    return {
        (item["bank"], item["metric"]): NumericReference(
            layout.fingerprint,
            item["bank"],
            item["metric"],
            item["reference_id"],
            item["source"],
            item["units"],
            item["low"],
            item["high"],
        )
        for item in profile.get("references", [])
    }


def _trace_bindings_for_observation(profile: Mapping[str, Any], support: str):
    prefix = support[: -len("_points_lps")]
    bindings = []
    for reading in profile["readings"]:
        source = reading.get("source", "array")
        if source == "unread":
            bindings.append(dict(reading))
        elif source == "record_context":
            bindings.append(_thaw(reading))
        elif source == "array":
            bindings.append(
                {
                    "bank": reading["bank"],
                    "metric": reading["metric"],
                    "value": f"{prefix}_{reading['value']}",
                }
            )
        else:
            bindings.append(dict(reading))
    return bindings


def _encoding_arrays(
    addressed: AddressedEncoding | TraceEncoding | ScopedEncoding,
    carrier: HadamardCarrier,
    layout: CompiledLayout,
    prefix: str,
    *,
    retain_metric_values: bool = False,
    retained_metric_arrays: dict[tuple[str, str, tuple[int, ...], str, str], str]
    | None = None,
    metric_bindings: Mapping[tuple[str, str], Mapping[str, Any]] | None = None,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    arrays: dict[str, np.ndarray] = {}
    item: dict[str, Any] = {
        "status": addressed.status,
        "metadata": addressed.metadata,
        "encoding_status": None,
        "metrics": [],
    }
    if isinstance(addressed, ScopedEncoding):
        points = addressed.coordinates
        address_name = "scope_coordinates"
        item["address_kind"] = addressed.address_kind
    elif isinstance(addressed, TraceEncoding):
        points = addressed.points_lps
        address_name = "points_lps"
        item["address_kind"] = "patient_lps_points"
    else:
        points = addressed.points_rc
        address_name = "points_rc"
        item["address_kind"] = addressed.metadata.get("address_kind", "native_rc")
    if points is None or addressed.encoding is None:
        return arrays, item
    points_key = f"{prefix}_{address_name}"
    arrays[points_key] = points
    item[address_name] = points_key
    item["place_count"] = int(points.shape[0])
    encoding = addressed.encoding
    item["encoding_status"] = encoding.status.value
    for metric_index, metric in enumerate(encoding.metrics):
        row_key = f"{prefix}_metric_{metric_index}_row_codes"
        arrays[row_key] = metric.row_codes
        metric_item = {
            "bank": metric.bank,
            "metric": metric.metric,
            "status": metric.status.value,
            "row_names": list(metric.row_names),
            "row_codes": row_key,
            "nonfinite_available_count": metric.nonfinite_available_count,
        }
        if metric_bindings is not None:
            binding = metric_bindings.get((metric.bank, metric.metric))
            if binding is not None:
                metric_item["binding"] = dict(binding)
        if retain_metric_values:
            if retained_metric_arrays is None:
                raise ValueError("retained_metric_array_index_required")
            metric_item["retained_source_values"] = _retain_metric_array(
                metric.source_values,
                f"{prefix}_metric_{metric_index}_source_values",
                arrays,
                retained_metric_arrays,
            )
            metric_item["retained_source_available"] = _retain_metric_array(
                metric.source_available,
                f"{prefix}_metric_{metric_index}_source_available",
                arrays,
                retained_metric_arrays,
            )
        item["metrics"].append(metric_item)
    bundle = encoding.bundle
    if bundle is not None:
        item["counts"] = [list(bank_counts) for bank_counts in bundle.counts]
        item["bundle_layout"] = {
            "layout_id": bundle.layout.layout_id,
            "carrier_id": bundle.layout.carrier_id,
            "banks": [
                {"name": bank.name, "row_count": bank.row_count}
                for bank in bundle.layout.banks
            ],
        }
        item["reference_set_fingerprint"] = getattr(
            encoding, "reference_set_fingerprint", None
        )
        item["carrier_identity"] = carrier.identity
        item["layout_fingerprint"] = layout.fingerprint
        table = np.zeros((len(bundle.layout.banks), 512), dtype=object)
        for bank_index, bank_counts in enumerate(bundle.counts):
            table[bank_index, : len(bank_counts)] = bank_counts
        if (
            bundle.layout.carrier_id != carrier.identity
            or tuple(bank.name for bank in bundle.layout.banks) != carrier.banks
        ):
            item["carrier_status"] = "identity_mismatch"
        else:
            try:
                vector = carrier.encode(table)
            except CarrierOverflow as error:
                item["carrier_status"] = "int32_overflow"
                item["carrier_detail"] = str(error)
            except CarrierError as error:
                item["carrier_status"] = "invalid_count_table"
                item["carrier_detail"] = str(error)
            else:
                vector_key = f"{prefix}_carrier_vector"
                arrays[vector_key] = vector
                item["carrier_status"] = "encoded"
                item["carrier_vector"] = vector_key
    else:
        item["carrier_status"] = "count_bundle_unavailable"
    return arrays, item


def _retain_metric_array(
    value: np.ndarray,
    preferred_key: str,
    arrays: dict[str, np.ndarray],
    retained_metric_arrays: dict[tuple[str, str, tuple[int, ...], str, str], str],
) -> dict[str, Any]:
    """Retain one exact consumed array, deduplicated by dtype, shape, and digest."""
    if not isinstance(value, np.ndarray) or value.dtype.hasobject:
        raise ValueError("retained_metric_array_malformed")
    if value.dtype.kind == "U":
        payload = json.dumps(
            value.tolist(), ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        stored = np.frombuffer(payload, dtype=np.uint8)
        encoding = "utf8_json"
    elif value.dtype.kind in "biufc":
        stored = value
        encoding = "native"
    else:
        raise ValueError(f"retained_metric_array_dtype_unsupported:{value.dtype.str}")
    payload_digest = digest(stored)
    identity = (
        encoding,
        value.dtype.str,
        tuple(value.shape),
        payload_digest,
        stored.dtype.str,
    )
    key = retained_metric_arrays.get(identity)
    if key is None:
        key = preferred_key
        if key in arrays:
            raise ValueError(f"retained_metric_array_key_collision:{key}")
        arrays[key] = stored
        retained_metric_arrays[identity] = key
    return {
        "array": key,
        "encoding": encoding,
        "dtype": value.dtype.str,
        "shape": list(value.shape),
        "digest": payload_digest,
        "stored_dtype": stored.dtype.str,
        "stored_shape": list(stored.shape),
    }


def _manifest_path(output: Path) -> Path:
    if output.name.endswith(".json.xz") or output.name.endswith(".json"):
        return output
    raise ValueError("encoding_output_must_end_with_json_or_json_xz")


def _archive_path(manifest: Path) -> Path:
    name = manifest.name
    stem = (
        name[: -len(".json.xz")] if name.endswith(".json.xz") else name[: -len(".json")]
    )
    return manifest.with_name(stem + ".npz.xz")


def _h5_path(manifest: Path) -> Path:
    name = manifest.name
    stem = (
        name[: -len(".json.xz")] if name.endswith(".json.xz") else name[: -len(".json")]
    )
    return manifest.with_name(stem + ".h5")


def _json_pure(manifest: dict) -> dict:
    """Same normalization a JSON round trip gives the legacy manifest."""
    return json.loads(json.dumps(manifest))


def _artifact_owners(
    candidates: list[tuple[dict, Path, str]], study_uid: object, artifact: object
) -> list[tuple[dict, Path, str]]:
    """Return same-study records that own the exact declared artifact."""
    if not isinstance(artifact, str) or not artifact:
        return []
    return [
        (candidate, candidate_root, candidate_root_name)
        for candidate, candidate_root, candidate_root_name in candidates
        if candidate.get("study_uid") == study_uid
        and candidate.get("artifact") == artifact
    ]


def _outcome_provenance(
    record: dict,
    owner_record: dict,
    observation: dict,
    record_root: str,
    owner_root: str,
) -> dict[str, Any]:
    """Keep the carrying record, array owner and observed acquisition distinct.

    A target artifact identifies a provided record in the observed acquisition;
    it does not assert that record's main plane is the observation's native plane.
    """
    target_uid = observation.get("series_uid")
    target_artifact = None
    target_artifact_root = None
    if not isinstance(target_uid, str) or not target_uid:
        target_uid = None
        target_status = "target_identity_unavailable"
    else:
        target_status = "target_record_artifact_unavailable"
        for candidate_record, candidate_root in (
            (owner_record, owner_root),
            (record, record_root),
        ):
            candidate = candidate_record.get("artifact")
            if (
                candidate_record.get("series_uid") == target_uid
                and isinstance(candidate, str)
                and candidate
            ):
                target_artifact = candidate
                target_artifact_root = candidate_root
                target_status = "retained_target_record_artifact"
                break
    return {
        "artifact": owner_record.get("artifact"),
        "record_series_uid": record.get("series_uid"),
        "record_artifact": record.get("artifact"),
        "record_view": record.get("view"),
        "record_slice_index": record.get("slice_index"),
        "target_series_uid": target_uid,
        "target_artifact": target_artifact,
        "target_artifact_root": target_artifact_root,
        "target_artifact_status": target_status,
        "owner_series_uid": owner_record.get("series_uid"),
        "owner_view": owner_record.get("view"),
        "owner_slice_index": owner_record.get("slice_index"),
        "source_root": record_root,
        "owner_root": owner_root,
    }


def encode_study(
    result: dict,
    run_dir: Path,
    main_run: Path,
    spec: dict,
    output: Path,
    *,
    prepared: dict | None = None,
) -> dict:
    """Encode declared profiles against the study's already-retained records."""
    if not isinstance(result, dict):
        raise TypeError("study_result_must_be_an_object")
    if prepared is None:
        validated = validate_spec(spec)
        spec = validated["spec"]
    else:
        if (
            not isinstance(prepared, dict)
            or prepared.get("_prepared_token") is not _PREPARED_TOKEN
            or spec is not prepared.get("spec")
        ):
            raise ValueError("prepared_spec_identity_mismatch")
        validated = prepared
    layout: CompiledLayout = validated["layout"]
    carrier: HadamardCarrier = validated["carrier"]
    manifest_path = _manifest_path(Path(output).resolve())
    storage = validated["storage"]
    archive_path = (
        _h5_path(manifest_path) if storage == "h5" else _archive_path(manifest_path)
    )
    records = result.get("records")
    main_records = result.get("main_records")
    objects = result.get("objects")
    if (
        not isinstance(records, list)
        or not isinstance(main_records, list)
        or not isinstance(objects, dict)
    ):
        raise TypeError("study_result_records_main_records_objects_required")

    validated = _expand_retained_profiles(validated, records, main_records)
    spec_sha256 = validated["spec_sha256"]

    composer = None
    composition_source = None
    composition_prepared = validated.get("composition")
    if composition_prepared is not None:
        map_record, composition_source = _composition_study_map(result, Path(run_dir))
        composer = StudyComposer(composition_prepared, map_record)

    candidates = [(record, Path(run_dir), "run") for record in records]
    candidates.extend((record, Path(main_run), "main") for record in main_records)
    object_source_plan = None
    object_source_error_type: type[Exception] | None = None
    object_source_artifacts: frozenset[Path] = frozenset()
    if validated["retain_object_sources"]:
        from knee.encoding.object_sources import (
            ObjectSourceError,
            prepare_object_sources,
        )

        object_source_error_type = ObjectSourceError
        object_source_plan = prepare_object_sources(result, candidates, archive_path)
        object_source_artifacts = frozenset(
            Path(path).resolve() for path in object_source_plan.artifacts
        )
    emitted_arrays: dict[str, np.ndarray] = {}
    retained_metric_arrays: dict[tuple[str, str, tuple[int, ...], str, str], str] = {}
    profile_outcomes: list[list[dict[str, Any] | None]] = [
        [] for _ in validated["profiles"]
    ]
    object_contexts: dict[str, dict[str, Any]] = {}
    artifact_groups: dict[Path, list[tuple[int, int, dict, dict, dict, str, str]]] = {}
    work = {
        "opened_artifacts": 0,
        "verified_source_arrays": 0,
        "source_bytes_verified": 0,
        "emitted_array_bytes": 0,
        "addressed_places": 0,
        "metric_row_arrays": 0,
        "bundle_count": 0,
    }

    for profile_index, profile in enumerate(validated["profiles"]):
        object_entry = objects.get(profile["object"], {})
        object_contexts.setdefault(
            profile["object"],
            {
                field: object_entry[field]
                for field in _OBJECT_CONTEXT_FIELDS
                if field in object_entry
            },
        )
        coarse_profile = _is_coarse_profile(profile)
        if coarse_profile:
            matched = list(_coarse_matches(candidates, profile))
        else:
            matched = [
                (*item, None) for item in _matching_observations(candidates, profile)
            ]
        if not matched:
            profile_outcomes[profile_index].append({"status": "missing_observation"})
            continue
        for record, record_root, root_name, observation, coarse_refusal in matched:
            if record.get("study_uid") != result.get("study_uid"):
                profile_outcomes[profile_index].append(
                    {"status": "source_study_mismatch", "observation": observation}
                )
                continue
            if coarse_refusal is not None:
                profile_outcomes[profile_index].append(
                    {"status": coarse_refusal, "observation": observation}
                )
                continue
            if profile["provenance"] == "projected" or profile["kind"] == "target":
                # The handoff exits on target semantics before touching arrays.
                addressed = encode_observation(
                    record,
                    observation,
                    {},
                    layout,
                    _thaw(profile["readings"]),
                    _references(profile, layout),
                )
                retain_metric_values = validated["retain_object_sources"]
                metric_bindings = {
                    (binding["bank"], binding["metric"]): binding
                    for binding in _thaw(profile["readings"])
                }
                target_arrays, outcome = _encoding_arrays(
                    addressed,
                    carrier,
                    layout,
                    f"p{profile_index}_target",
                    retain_metric_values=retain_metric_values,
                    retained_metric_arrays=(
                        retained_metric_arrays if retain_metric_values else None
                    ),
                    metric_bindings=(metric_bindings if retain_metric_values else None),
                )
                if retain_metric_values:
                    emitted_arrays.update(target_arrays)
                outcome.update(
                    _outcome_provenance(
                        record, record, observation, root_name, root_name
                    )
                )
                if composer is not None:
                    contribution = composer.add(
                        profile["object"],
                        profile_index,
                        len(profile_outcomes[profile_index]),
                        addressed,
                        _thaw(profile),
                    )
                    outcome["object_contribution"] = contribution.code.value
                profile_outcomes[profile_index].append(outcome)
                continue
            support_layout = profile.get("support_layout")
            is_trace = (
                isinstance(support_layout, Mapping)
                and support_layout.get("family") == "posterior_trace"
            )
            owner_record = record
            owner_root = record_root
            owner_root_name = root_name
            artifact_name = record.get("artifact")
            observation_artifact = observation.get("artifact")
            if is_trace or observation_artifact != record.get("artifact"):
                artifact_name = observation_artifact
                owners = _artifact_owners(
                    candidates, result.get("study_uid"), artifact_name
                )
                if len(owners) != 1:
                    profile_outcomes[profile_index].append(
                        {
                            "status": (
                                "trace_owner_record_missing"
                                if is_trace and not owners
                                else "trace_owner_record_ambiguous"
                                if is_trace
                                else "ordinary_source_owner_record_missing"
                                if not owners
                                else "ordinary_source_owner_record_ambiguous"
                            ),
                            "artifact": artifact_name,
                            "observation": observation,
                            "target_root": root_name,
                        }
                    )
                    continue
                owner_record, owner_root, owner_root_name = owners[0]
            artifact = _artifact_path(owner_root, artifact_name)
            if artifact is None:
                profile_outcomes[profile_index].append(
                    {"status": "invalid_artifact_path", "observation": observation}
                )
                continue
            if not artifact.is_file():
                profile_outcomes[profile_index].append(
                    {
                        "status": "artifact_missing",
                        "observation": observation,
                        **_outcome_provenance(
                            record,
                            owner_record,
                            observation,
                            root_name,
                            owner_root_name,
                        ),
                    }
                )
                continue
            slot = len(profile_outcomes[profile_index])
            profile_outcomes[profile_index].append(None)
            artifact_groups.setdefault(artifact, []).append(
                (
                    profile_index,
                    slot,
                    record,
                    owner_record,
                    observation,
                    root_name,
                    owner_root_name,
                )
            )

    if object_source_plan is not None:
        for source_artifact in object_source_artifacts:
            artifact_groups.setdefault(source_artifact, [])

    for artifact, entries in artifact_groups.items():
        try:
            archive = open_arrays(artifact)
        except (OSError, ValueError) as error:
            if object_source_plan is not None and artifact in object_source_artifacts:
                assert object_source_error_type is not None
                raise object_source_error_type(
                    "object_source_archive_unreadable"
                ) from error
            for (
                profile_index,
                slot,
                record,
                owner_record,
                observation,
                root_name,
                owner_root_name,
            ) in entries:
                profile_outcomes[profile_index][slot] = {
                    "status": "artifact_unreadable",
                    "detail": str(error),
                    "observation": observation,
                    **_outcome_provenance(
                        record, owner_record, observation, root_name, owner_root_name
                    ),
                }
            continue
        work["opened_artifacts"] += 1
        verified_arrays: dict[tuple[str, str], np.ndarray] = {}
        with archive:
            for (
                profile_index,
                slot,
                record,
                owner_record,
                observation,
                root_name,
                owner_root_name,
            ) in entries:
                profile = validated["profiles"][profile_index]
                support_layout = profile.get("support_layout")
                is_trace = (
                    isinstance(support_layout, Mapping)
                    and support_layout.get("family") == "posterior_trace"
                )
                if _is_coarse_profile(profile):
                    coarse_layout, coarse_bindings, problem = _coarse_inputs(
                        profile, record, observation
                    )
                    if problem is not None:
                        addressed = ScopedEncoding(
                            problem,
                            None,
                            None,
                            "coarse_grid_rc",
                            {"observation": dict(observation), "detail": problem},
                        )
                    else:
                        addressed = encode_coarse_observation(
                            record,
                            observation,
                            archive,
                            layout,
                            coarse_bindings,
                            _references(profile, layout),
                            coarse_layout,
                            verified_arrays=verified_arrays,
                        )
                elif is_trace:
                    addressed = encode_trace_observation(
                        record,
                        owner_record,
                        observation,
                        archive,
                        layout,
                        _trace_bindings_for_observation(
                            profile, observation["support"]
                        ),
                        _references(profile, layout),
                        verified_arrays=verified_arrays,
                    )
                elif (
                    isinstance(support_layout, Mapping)
                    and support_layout.get("family") == "joint_axial_profile_samples"
                ):
                    addressed = encode_sampled_profile_observation(
                        owner_record,
                        observation,
                        archive,
                        layout,
                        _thaw(profile["readings"]),
                        _references(profile, layout),
                        _thaw(support_layout),
                        verified_arrays=verified_arrays,
                    )
                elif (
                    isinstance(support_layout, Mapping)
                    and support_layout.get("family") == "native_slice_profile_values"
                ):
                    addressed = encode_slice_profile_observation(
                        owner_record,
                        observation,
                        archive,
                        layout,
                        _thaw(profile["readings"]),
                        _references(profile, layout),
                        _thaw(support_layout),
                        verified_arrays=verified_arrays,
                    )
                elif support_layout is None:
                    addressed = encode_observation(
                        owner_record,
                        observation,
                        archive,
                        layout,
                        _thaw(profile["readings"]),
                        _references(profile, layout),
                        verified_arrays=verified_arrays,
                    )
                else:
                    addressed = encode_packed_observation(
                        record,
                        observation,
                        archive,
                        layout,
                        _thaw(profile["readings"]),
                        _references(profile, layout),
                        _packed_layout_for_observation(
                            _thaw(support_layout), record, observation
                        ),
                        verified_arrays=verified_arrays,
                    )
                prefix = f"p{profile_index}_o{slot:04d}"
                retain_metric_values = validated["retain_object_sources"]
                metric_bindings = {
                    (binding["bank"], binding["metric"]): binding
                    for binding in _thaw(profile["readings"])
                }
                arrays, outcome = _encoding_arrays(
                    addressed,
                    carrier,
                    layout,
                    prefix,
                    retain_metric_values=retain_metric_values,
                    retained_metric_arrays=(
                        retained_metric_arrays if retain_metric_values else None
                    ),
                    metric_bindings=(metric_bindings if retain_metric_values else None),
                )
                emitted_arrays.update(arrays)
                bounds = addressed.metadata.get("native_bounds_rc")
                if isinstance(bounds, np.ndarray):
                    bounds_key = f"{prefix}_native_bounds_rc"
                    emitted_arrays[bounds_key] = bounds
                    metadata = dict(outcome["metadata"])
                    metadata["native_bounds_rc"] = bounds_key
                    outcome["metadata"] = metadata
                encoding_result = addressed.encoding
                addressed_points = (
                    addressed.coordinates
                    if isinstance(addressed, ScopedEncoding)
                    else addressed.points_lps
                    if isinstance(addressed, TraceEncoding)
                    else addressed.points_rc
                )
                if addressed_points is not None:
                    work["addressed_places"] += int(addressed_points.shape[0])
                if encoding_result is not None:
                    work["metric_row_arrays"] += len(encoding_result.metrics)
                    if encoding_result.bundle is not None:
                        work["bundle_count"] += 1
                outcome.update(
                    _outcome_provenance(
                        record, owner_record, observation, root_name, owner_root_name
                    )
                )
                if composer is not None:
                    contribution = composer.add(
                        profile["object"],
                        profile_index,
                        slot,
                        addressed,
                        _thaw(profile),
                        {
                            "owner_artifact": owner_record.get("artifact"),
                            "owner_series_uid": owner_record.get("series_uid"),
                            "target_series_uid": observation.get("series_uid"),
                        },
                    )
                    outcome["object_contribution"] = contribution.code.value
                profile_outcomes[profile_index][slot] = outcome
            if object_source_plan is not None and artifact in object_source_artifacts:
                object_source_plan.retain_artifact(
                    artifact, archive, verified_arrays, emitted_arrays
                )
        work["verified_source_arrays"] += len(verified_arrays)
        work["source_bytes_verified"] += sum(
            array.nbytes for array in verified_arrays.values()
        )

    manifest_profiles: list[dict[str, Any]] = []
    for profile_index, profile in enumerate(validated["profiles"]):
        outcomes = profile_outcomes[profile_index]
        if any(outcome is None for outcome in outcomes):
            raise RuntimeError("encoding_outcome_not_materialized")
        manifest_profiles.append(
            {
                "profile_index": profile_index,
                "object": profile["object"],
                "provenance": profile["provenance"],
                "kind": profile["kind"],
                "support": profile["support"],
                "view": profile.get("view"),
                "retained_address": _thaw(profile.get("retained_address")),
                "retained_expansion": profile.get("retained_expansion"),
                "outcomes": outcomes,
            }
        )

    composition_metadata = None
    if composer is not None:
        assert composition_prepared is not None
        composition_arrays, composition_metadata = serialize_study_composition(
            composer.finalize(),
            composition_prepared,
        )
        composition_metadata["study_map_source"] = composition_source
        emitted_arrays.update(composition_arrays)
        work["object_profiles"] = len(composition_metadata["objects"])
        work["composition_batches"] = sum(
            len(item["batches"]) for item in composition_metadata["additions"]
        )
        work["composition_array_bytes"] = sum(
            value.nbytes for value in composition_arrays.values()
        )

    from knee.encoding.support_ownership import summarize_support_ownership

    by_object: dict[str, list[dict[str, Any]]] = {}
    for profile in manifest_profiles:
        by_object.setdefault(profile["object"], []).append(profile)
    ownership = {
        name: summarize_support_ownership(
            name, profiles, study_uid=result.get("study_uid")
        )
        for name, profiles in by_object.items()
    }
    object_source_metadata = (
        object_source_plan.finish() if object_source_plan is not None else None
    )
    definition_metadata = None
    definition_prepared = validated.get("definition_context")
    if definition_prepared is not None:
        from knee.encoding.mri_definition_context import serialize_definition_contexts

        definition_arrays, definition_metadata = serialize_definition_contexts(
            definition_prepared, object_contexts
        )
        emitted_arrays.update(definition_arrays)
        work["definition_context_objects"] = len(definition_metadata["objects"])
    if composition_metadata is not None:
        for name, item in composition_metadata["objects"].items():
            item["support_ownership"] = {
                "object": name,
                "schema": "support_ownership.v1",
            }
            if definition_metadata is not None:
                item["definition_context"] = {
                    "object": name,
                    "role": "anatomical_definition",
                    "status": definition_metadata["objects"]
                    .get(name, {})
                    .get("status"),
                }

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    work["emitted_array_bytes"] = sum(array.nbytes for array in emitted_arrays.values())
    if storage == "npz_xz":
        write_npz_xz(archive_path, emitted_arrays.items())
    manifest = {
        "version": 1,
        "study_uid": result.get("study_uid"),
        "spec": _thaw(validated["spec"]),
        "spec_sha256": spec_sha256,
        "carrier_identity": carrier.identity,
        "layout_fingerprint": layout.fingerprint,
        "archive": str(archive_path),
        "source_roots": {
            "run": str(Path(run_dir).resolve()),
            "main": str(Path(main_run).resolve()),
        },
        "encoded_arrays": {
            name: {
                "digest": digest(array),
                "shape": list(array.shape),
                "dtype": array.dtype.str,
            }
            for name, array in emitted_arrays.items()
        },
        "work": dict(work),
        "profiles": manifest_profiles,
        "retained_ordinary_expansion_state": _thaw(
            validated["spec"].get("retained_ordinary_expansion_state")
        ),
        "object_contexts": object_contexts,
        "support_ownership": ownership,
        "meaning": "addressed count encoding only; no cross-view alias or volume",
    }
    expansion_state = validated["spec"].get("retained_ordinary_expansion_state")
    if expansion_state is not None:
        manifest["retained_ordinary_expansion_state"] = _thaw(expansion_state)
    if definition_metadata is not None:
        manifest["definition_context"] = definition_metadata
    if object_source_metadata is not None:
        manifest["object_sources"] = object_source_metadata
        manifest["retained_metric_inputs"] = {
            "schema": "knee-retained-metric-inputs/v1",
            "status": "complete",
            "array_count": len(retained_metric_arrays),
            "deduplication": "encoding_and_dtype_shape_digest",
        }
    if composition_metadata is not None:
        manifest["object_composition"] = composition_metadata
        manifest["meaning"] = (
            "unified object profiles from addressed view/lens/scale/direction readings; "
            "no physical volume or diagnosis"
        )
    if storage == "h5":
        writer = {
            "legacy": h5_store.write_h5,
            "compact": h5_store.write_h5_compact,
            "byte_xor": h5_store.write_h5_byte_xor,
            "modular_hybrid": h5_store.write_h5_modular,
        }[validated["h5_encoding"]]
        actual_manifest = writer(archive_path, _json_pure(manifest), emitted_arrays)
    else:
        actual_manifest = dump_json_atomic(manifest_path, manifest)
    statuses: dict[str, Any] = {
        "manifest": str(actual_manifest),
        "archive": str(archive_path),
        "profiles": manifest_profiles,
        "work": dict(work),
    }
    if expansion_state is not None:
        statuses["retained_ordinary_expansion_state"] = _thaw(expansion_state)
    if object_source_metadata is not None:
        statuses["object_sources"] = object_source_metadata
    for profile in manifest_profiles:
        link = {
            "manifest": str(actual_manifest),
            "archive": str(archive_path),
            "profile_index": profile["profile_index"],
            "status": (
                profile["outcomes"][0]["status"]
                if len(profile["outcomes"]) == 1
                else "multiple_observation_outcomes"
            ),
        }
        objects.setdefault(profile["object"], {}).setdefault("encoding", []).append(
            link
        )
    if composition_metadata is not None:
        statuses["object_composition"] = {
            "manifest": str(actual_manifest),
            "objects": list(composition_metadata["objects"]),
            "layout_fingerprint": composition_metadata["layout_fingerprint"],
        }
        for object_name, object_profile in composition_metadata["objects"].items():
            objects.setdefault(object_name, {})["encoding_object"] = {
                "manifest": str(actual_manifest),
                "archive": str(archive_path),
                "object": object_name,
                "status": object_profile["status"],
                "count_layout_id": object_profile["count_layout_id"],
            }
    if definition_metadata is not None:
        for name, item in definition_metadata["objects"].items():
            objects.setdefault(name, {})["encoding_definition_context"] = {
                "manifest": str(actual_manifest),
                "object": name,
                "role": "anatomical_definition",
                "status": item["status"],
                "count_layout_id": item["count_layout_id"],
            }
    return statuses
