"""Study-level assembly of retained per-place measurements into object profiles.

The composer re-encodes existing row indexes under one declared expanded
layout.  It does not read files, choose references, infer anatomy, resample
coordinates, or turn a sparse profile into a dense carrier vector.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import StrEnum
from types import MappingProxyType
from typing import Any, cast

import numpy as np

from knee.encoding.carrier import CarrierError, HadamardCarrier
from knee.encoding.facets import (
    BankFacetPlan,
    DirectionMPS,
    ExpandedBank,
    FacetExpansion,
    ViewRole,
    expand_facets,
)
from knee.encoding.handoff import AddressedEncoding
from knee.encoding.object_profile import (
    BankFacet,
    FacetCoordinate,
    ObjectAssemblyResult,
    PlaceAddressBatch,
    ProfileLayout,
    RowcodeBatch,
    SourceLink,
    _assemble_prepared_object_profile,
    _bind_profile_layout_reference,
    _validate_prepared_profile_layout,
    assemble_object_profile,
    compile_profile_layout,
    registry_fingerprint,
    registry_problem,
)
from knee.encoding.places import (
    CompiledLayout,
    LayoutSpec,
    MetricEncoding,
    MetricKind,
    MetricRows,
    NumericReference,
    compile_layout,
)
from knee.encoding.scoped import ScopedEncoding
from knee.encoding.spatial import (
    BatchSpatialReading,
    SpatialContext,
    batch_native_lps_readings,
    batch_native_rc_readings,
    prepare_spatial_context,
)
from knee.encoding.trace_adapter import TraceEncoding

__all__ = [
    "AddResult",
    "BatchIndexMap",
    "CompositionCode",
    "CompositionPreparation",
    "ObjectComposition",
    "PreparedComposition",
    "StudyComposer",
    "StudyComposition",
    "prepare_composition",
]


class CompositionCode(StrEnum):
    OK = "ok"
    INVALID_BASE_LAYOUT = "invalid_base_layout"
    INVALID_DECLARATION = "invalid_declaration"
    INVALID_PROFILES = "invalid_profiles"
    CARRIER_ERROR = "carrier_error"
    LAYOUT_ERROR = "layout_error"
    PROFILE_LAYOUT_ERROR = "profile_layout_error"
    REFERENCE_MAPPING_CONFLICT = "reference_mapping_conflict"
    INVALID_PROFILE_INDEX = "invalid_profile_index"
    INVALID_OUTCOME_INDEX = "invalid_outcome_index"
    PROFILE_MISMATCH = "profile_mismatch"
    TARGET_ONLY = "target_only"
    UNSUPPORTED_ADDRESS = "unsupported_address"
    INVALID_OBSERVATION = "invalid_observation"
    UNDECLARED_VIEW = "undeclared_view"
    SOURCE_REFERENCE_MISMATCH = "source_reference_mismatch"
    METRIC_ROW_MISMATCH = "metric_row_mismatch"
    METRIC_ENCODING_MALFORMED = "metric_encoding_malformed"
    SPATIAL_INPUT_MALFORMED = "spatial_input_malformed"
    MEASUREMENT_SOURCE_UNAVAILABLE = "measurement_source_unavailable"
    ALREADY_FINALIZED = "already_finalized"


@dataclass(frozen=True, slots=True)
class _ProfileInput:
    object_name: str
    provenance: str
    kind: str
    support: str
    view: ViewRole | None
    references: Mapping[tuple[str, str], tuple[str, str, str, int | float, int | float]]
    signature: str


@dataclass(frozen=True, slots=True)
class PreparedComposition:
    """Validated study-independent layout, registry, and reference contracts."""

    base_layout: CompiledLayout
    layout: CompiledLayout
    carrier: HadamardCarrier
    expansion: FacetExpansion
    registry: tuple[BankFacet, ...]
    view_roles: tuple[ViewRole, ...]
    profiles: tuple[_ProfileInput, ...]
    profile_layouts: Mapping[str, ProfileLayout]
    object_codes: Mapping[str, CompositionCode]
    object_reference_identities: Mapping[str, str]
    metric_rows: Mapping[tuple[str, str, str], MetricRows]
    facets_by_key: Mapping[tuple[str, ViewRole, DirectionMPS | None], str]
    base_metric_rows: Mapping[tuple[str, str], MetricRows]


@dataclass(frozen=True, slots=True)
class CompositionPreparation:
    code: CompositionCode
    prepared: PreparedComposition | None = None
    detail: str = ""


@dataclass(frozen=True, slots=True, eq=False)
class BatchIndexMap:
    object_name: str
    object_batch_ordinal: int
    profile_index: int
    outcome_index: int
    bank: str
    metric: str
    direction: DirectionMPS | None
    original_place_indices: np.ndarray
    source_link: SourceLink


@dataclass(frozen=True, slots=True)
class AddResult:
    code: CompositionCode
    object_name: str
    profile_index: int
    outcome_index: int
    spatial: BatchSpatialReading | None = None
    batches: tuple[RowcodeBatch, ...] = ()
    batch_index_maps: tuple[BatchIndexMap, ...] = ()
    metadata: Mapping[str, Any] | None = None
    detail: str = ""


@dataclass(frozen=True, slots=True)
class ObjectComposition:
    object_name: str
    code: CompositionCode
    assembly: ObjectAssemblyResult | None
    batch_index_maps: tuple[BatchIndexMap, ...]
    detail: str = ""


@dataclass(frozen=True, slots=True)
class StudyComposition:
    code: CompositionCode
    objects: Mapping[str, ObjectComposition]
    spatial_contexts: Mapping[str, SpatialContext]
    additions: tuple[AddResult, ...]


def _plain_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _frozen(array: np.ndarray) -> np.ndarray:
    """Owned immutable snapshot whose writeable flag cannot be reset."""
    source = np.ascontiguousarray(array)
    return np.frombuffer(source.tobytes(), dtype=source.dtype).reshape(source.shape)


def _finite_number(value: object) -> bool:
    return _plain_int(value) or isinstance(value, float) and math.isfinite(value)


def _jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"unsupported_json_value:{type(value).__name__}")


def _canonical(value: Any) -> str:
    return json.dumps(
        _jsonable(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _base_compiled_layout(value: object) -> CompiledLayout | None:
    if isinstance(value, CompiledLayout):
        checked = compile_layout(
            LayoutSpec(value.version, value.carrier_id, value.banks)
        )
        return checked if checked == value else None
    if isinstance(value, LayoutSpec):
        return compile_layout(value)
    return None


def _view_role(value: object) -> ViewRole | None:
    if (
        isinstance(value, (tuple, list))
        and len(value) == 3
        and all(isinstance(item, str) and item for item in value)
    ):
        return (value[0], value[1], value[2])
    return None


def _profile_inputs(
    profiles: object,
    layout: CompiledLayout,
) -> tuple[tuple[_ProfileInput, ...], str | None]:
    if not isinstance(profiles, (tuple, list)):
        return (), "profiles_must_be_a_sequence"
    metric_kinds = {
        (bank.name, metric.name): metric.kind
        for bank in layout.banks
        for metric in bank.metrics
    }
    output: list[_ProfileInput] = []
    for item in profiles:
        if not isinstance(item, Mapping):
            return (), "profile_must_be_an_object"
        object_name = item.get("object")
        provenance, kind, support = (
            item.get("provenance"),
            item.get("kind"),
            item.get("support"),
        )
        if not all(
            isinstance(v, str) and v for v in (object_name, provenance, kind, support)
        ):
            return (), "profile_identity_fields_required"
        view_raw = item.get("view")
        if view_raw is not None and _view_role(view_raw) is None:
            return (), "invalid_profile_view"
        refs_raw = item.get("references", ())
        if not isinstance(refs_raw, (tuple, list)):
            return (), "profile_references_must_be_a_sequence"
        refs: dict[tuple[str, str], tuple[str, str, str, int | float, int | float]] = {}
        for reference in refs_raw:
            if not isinstance(reference, Mapping):
                return (), "profile_reference_must_be_an_object"
            bank, metric = reference.get("bank"), reference.get("metric")
            key = (bank, metric)
            if (
                not isinstance(bank, str)
                or not isinstance(metric, str)
                or metric_kinds.get(key) is not MetricKind.DIGIT
            ):
                return (), "profile_reference_unknown_or_non_numeric_metric"
            reference_id, source, units = (
                reference.get("reference_id"),
                reference.get("source"),
                reference.get("units"),
            )
            low, high = reference.get("low"), reference.get("high")
            if (
                not all(isinstance(v, str) and v for v in (reference_id, source, units))
                or not _finite_number(low)
                or not _finite_number(high)
                or low > high
                or key in refs
            ):
                return (), "invalid_or_duplicate_profile_reference"
            refs[key] = (reference_id, source, units, low, high)
        try:
            signature = _canonical(item)
        except (TypeError, ValueError) as error:
            return (), f"profile_not_canonical_json:{error}"
        output.append(
            _ProfileInput(
                object_name,
                provenance,
                kind,
                support,
                _view_role(view_raw) if view_raw is not None else None,
                MappingProxyType(refs),
                signature,
            )
        )
    return tuple(output), None


def _reference_identity(
    base: CompiledLayout,
    object_name: str,
    profiles: tuple[_ProfileInput, ...],
    view_roles: tuple[ViewRole, ...],
) -> tuple[str, bool]:
    """Fingerprint known norm meanings by metric and qualified view only."""
    known: dict[tuple[str, str, str], set[str]] = {}
    for profile in profiles:
        if profile.object_name != object_name:
            continue
        scopes = view_roles if profile.view is None else (profile.view,)
        for (bank, metric), ref in profile.references.items():
            reference = {
                "reference_id": ref[0],
                "source": ref[1],
                "units": ref[2],
                "low": {"type": type(ref[3]).__name__, "value": ref[3]},
                "high": {"type": type(ref[4]).__name__, "value": ref[4]},
            }
            for view_role in scopes:
                scope = _canonical(view_role)
                known.setdefault((bank, metric, scope), set()).add(
                    _canonical(reference)
                )
    conflict = any(len(values) > 1 for values in known.values())
    canonical = {
        "schema": "object_reference_meanings/v2",
        "base_layout_fingerprint": base.fingerprint,
        "known_references": [
            {
                "bank": bank,
                "metric": metric,
                "view_scope": scope,
                "reference": reference,
            }
            for (bank, metric, scope), references in sorted(known.items())
            for reference in sorted(references)
        ],
    }
    return hashlib.sha256(_canonical(canonical).encode("utf-8")).hexdigest(), conflict


def _registry_for_profile(
    expansion: FacetExpansion,
) -> tuple[BankFacet, ...]:
    entries = []
    for item in expansion.registry:
        view = _canonical(item.view_role)
        direction = None if item.direction is None else _canonical(item.direction)
        entries.append(
            BankFacet(
                item.bank,
                FacetCoordinate(view, item.lens, item.scale, direction),
            )
        )
    return tuple(entries)


def prepare_composition(
    base_layout: CompiledLayout | LayoutSpec,
    profiles: Sequence[Mapping[str, Any]],
    declaration: Mapping[str, Any],
) -> CompositionPreparation:
    """Compile the shared carrier/facets and per-object reference identities."""
    base = _base_compiled_layout(base_layout)
    if base is None:
        return CompositionPreparation(CompositionCode.INVALID_BASE_LAYOUT)
    if not isinstance(declaration, Mapping):
        return CompositionPreparation(CompositionCode.INVALID_DECLARATION)
    schema_version = declaration.get("version")
    roles_raw, plans_raw = declaration.get("view_roles"), declaration.get("bank_plans")
    if (
        not isinstance(schema_version, str)
        or not schema_version
        or not isinstance(roles_raw, (tuple, list))
        or not isinstance(plans_raw, (tuple, list))
    ):
        return CompositionPreparation(CompositionCode.INVALID_DECLARATION)
    roles: list[ViewRole] = []
    for role in roles_raw:
        normalized = _view_role(role)
        if normalized is None:
            return CompositionPreparation(
                CompositionCode.INVALID_DECLARATION, detail="invalid_view_role"
            )
        roles.append(normalized)
    plans: list[BankFacetPlan] = []
    for plan in plans_raw:
        if isinstance(plan, BankFacetPlan):
            plans.append(plan)
        elif isinstance(plan, Mapping):
            plans.append(
                BankFacetPlan(
                    plan.get("base_bank"), plan.get("lens"), plan.get("scale_scope")
                )
            )
        else:
            return CompositionPreparation(
                CompositionCode.INVALID_DECLARATION, detail="invalid_bank_plan"
            )
    parsed_profiles, profile_error = _profile_inputs(profiles, base)
    if profile_error:
        return CompositionPreparation(
            CompositionCode.INVALID_PROFILES, detail=profile_error
        )

    base_spec = LayoutSpec(base.version, base.carrier_id, base.banks)
    expansion_result = expand_facets(base_spec, tuple(roles), tuple(plans))
    if expansion_result.expansion is None:
        return CompositionPreparation(
            CompositionCode.INVALID_DECLARATION, detail=expansion_result.code.value
        )
    expansion = expansion_result.expansion
    try:
        carrier = HadamardCarrier.from_banks(
            tuple(bank.name for bank in expansion.layout_spec.banks)
        )
    except (CarrierError, TypeError, ValueError) as error:
        return CompositionPreparation(CompositionCode.CARRIER_ERROR, detail=str(error))
    versioned_spec = replace(
        expansion.layout_spec,
        version=f"{base.version}:composition:{schema_version}",
        carrier_id=carrier.identity,
    )
    registry = _registry_for_profile(expansion)
    if registry_problem(registry) is not None:
        return CompositionPreparation(
            CompositionCode.LAYOUT_ERROR, detail="registry_invalid"
        )
    shared_profile_layout = compile_profile_layout(
        versioned_spec, registry, "shared-layout-reference-placeholder"
    )
    if shared_profile_layout is None:
        return CompositionPreparation(CompositionCode.LAYOUT_ERROR)
    shared_layout = shared_profile_layout.compiled

    object_names = tuple(
        dict.fromkeys(profile.object_name for profile in parsed_profiles)
    )
    profile_layouts: dict[str, ProfileLayout] = {}
    object_codes: dict[str, CompositionCode] = {}
    reference_identities: dict[str, str] = {}
    layouts_by_reference: dict[str, ProfileLayout] = {}
    for object_name in object_names:
        reference_identity, conflict = _reference_identity(
            base, object_name, parsed_profiles, tuple(roles)
        )
        reference_identities[object_name] = reference_identity
        if conflict:
            object_codes[object_name] = CompositionCode.REFERENCE_MAPPING_CONFLICT
            continue
        built = layouts_by_reference.get(reference_identity)
        if built is None:
            built = _bind_profile_layout_reference(
                shared_profile_layout, reference_identity
            )
            if built is None:
                object_codes[object_name] = CompositionCode.PROFILE_LAYOUT_ERROR
                continue
            layouts_by_reference[reference_identity] = built
        # Identical immutable reference meanings share preparation as well as
        # the common compiled bank layout; object observations remain separate.
        profile_layouts[object_name] = built
        object_codes[object_name] = CompositionCode.OK

    metric_rows = {
        (row.bank, row.metric, row.facet): row for row in shared_layout.metric_rows
    }
    facets_by_key = {
        (item.base_bank, item.view_role, item.direction): item.bank
        for item in expansion.mapping
    }
    base_rows = {(row.bank, row.metric): row for row in base.metric_rows}
    prepared = PreparedComposition(
        base,
        shared_layout,
        carrier,
        expansion,
        registry,
        tuple(roles),
        parsed_profiles,
        MappingProxyType(profile_layouts),
        MappingProxyType(object_codes),
        MappingProxyType(reference_identities),
        MappingProxyType(metric_rows),
        MappingProxyType(facets_by_key),
        MappingProxyType(base_rows),
    )
    return CompositionPreparation(CompositionCode.OK, prepared)


def _typed_equal(left: object, right: object) -> bool:
    """Compare prepared values without Python's bool/int or int/float aliases."""
    if type(left) is not type(right):
        return False
    if (
        is_dataclass(left)
        and not isinstance(left, type)
        and is_dataclass(right)
        and not isinstance(right, type)
    ):
        return all(
            _typed_equal(getattr(left, item.name), getattr(right, item.name))
            for item in fields(left)
        )
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        if len(left) != len(right):
            return False
        unmatched = list(right.items())
        for key, value in left.items():
            match = next(
                (
                    index
                    for index, (other_key, other_value) in enumerate(unmatched)
                    if _typed_equal(key, other_key) and _typed_equal(value, other_value)
                ),
                None,
            )
            if match is None:
                return False
            unmatched.pop(match)
        return not unmatched
    if isinstance(left, (tuple, list)) and isinstance(right, (tuple, list)):
        return len(left) == len(right) and all(
            _typed_equal(a, b) for a, b in zip(left, right, strict=True)
        )
    if isinstance(left, float) and isinstance(right, float):
        return left.hex() == right.hex()
    return bool(left == right)


def _mapping_proxy_matches(actual: object, expected: object) -> bool:
    return (
        type(actual) is type(MappingProxyType({}))
        and isinstance(actual, Mapping)
        and isinstance(expected, Mapping)
        and _typed_equal(dict(actual), dict(expected))
    )


def _is_mapping_proxy(value: object) -> bool:
    return type(value) is type(MappingProxyType({}))


def _profile_inputs_match_prepared(
    profiles: object, base: CompiledLayout
) -> tuple[_ProfileInput, ...] | None:
    if type(profiles) is not tuple:
        return None
    checked: list[_ProfileInput] = []
    for profile in profiles:
        if type(profile) is not _ProfileInput or not isinstance(profile.signature, str):
            return None
        try:
            source = json.loads(profile.signature)
        except (TypeError, ValueError):
            return None
        rebuilt, problem = _profile_inputs((source,), base)
        if problem is not None or len(rebuilt) != 1:
            return None
        if not _typed_equal(profile, rebuilt[0]):
            return None
        checked.append(rebuilt[0])
    return tuple(checked)


def _canonical_expansion(
    base: CompiledLayout,
    view_roles: object,
    expansion: object,
) -> FacetExpansion | None:
    if (
        type(view_roles) is not tuple
        or not view_roles
        or any(
            type(role) is not tuple
            or len(role) != 3
            or any(type(part) is not str or not part for part in role)
            for role in view_roles
        )
        or len(set(view_roles)) != len(view_roles)
        or type(expansion) is not FacetExpansion
        or type(expansion.mapping) is not tuple
    ):
        return None

    base_names = tuple(bank.name for bank in base.banks)
    plans_by_base: dict[str, BankFacetPlan] = {}
    seen_keys: set[tuple[str, ViewRole, DirectionMPS | None]] = set()
    for entry in expansion.mapping:
        if (
            type(entry) is not ExpandedBank
            or type(entry.base_bank) is not str
            or entry.base_bank not in base_names
            or type(entry.bank) is not str
            or not entry.bank
            or type(entry.lens) is not str
            or not entry.lens
            or type(entry.scale_scope) is not str
            or not entry.scale_scope
            or type(entry.view_role) is not tuple
            or entry.view_role not in view_roles
        ):
            return None
        direction = entry.direction
        if direction is not None and (
            type(direction) is not tuple
            or len(direction) != 3
            or any(
                type(axis) is not int or axis not in (-1, 0, 1) for axis in direction
            )
        ):
            return None
        key = (entry.base_bank, entry.view_role, direction)
        if key in seen_keys:
            return None
        seen_keys.add(key)
        plan = BankFacetPlan(entry.base_bank, entry.lens, entry.scale_scope)
        prior = plans_by_base.setdefault(entry.base_bank, plan)
        if not _typed_equal(prior, plan):
            return None
    if tuple(plans_by_base) != base_names:
        return None

    result = expand_facets(
        LayoutSpec(base.version, base.carrier_id, base.banks),
        cast(tuple[ViewRole, ...], view_roles),
        tuple(plans_by_base[name] for name in base_names),
    )
    if result.expansion is None or not _typed_equal(expansion, result.expansion):
        return None
    return result.expansion


def _verified_shared_compiled_layout(
    prepared: PreparedComposition,
) -> CompiledLayout | None:
    """Validate all prepared derivatives before any study-level consumer uses them."""
    if type(prepared) is not PreparedComposition:
        return None
    base = prepared.base_layout
    if type(base) is not CompiledLayout:
        return None
    profiles = _profile_inputs_match_prepared(prepared.profiles, base)
    expansion = _canonical_expansion(base, prepared.view_roles, prepared.expansion)
    if profiles is None or expansion is None:
        return None
    expected_registry = _registry_for_profile(expansion)
    expected_layout_registry = tuple(
        sorted(expected_registry, key=lambda item: item.bank)
    )
    if (
        not _typed_equal(prepared.registry, expected_registry)
        or registry_problem(expected_registry) is not None
        or type(prepared.carrier) is not HadamardCarrier
    ):
        return None
    expected_bank_names = tuple(bank.name for bank in expansion.layout_spec.banks)
    canonical_carrier = HadamardCarrier.from_banks(expected_bank_names)
    if (
        type(prepared.carrier.banks) is not tuple
        or any(type(name) is not str or not name for name in prepared.carrier.banks)
        or prepared.carrier.banks != expected_bank_names
        or prepared.carrier.identity != canonical_carrier.identity
    ):
        return None
    names = tuple(dict.fromkeys(profile.object_name for profile in profiles))
    if not _is_mapping_proxy(prepared.object_codes) or not _is_mapping_proxy(
        prepared.object_reference_identities
    ):
        return None
    if set(prepared.object_codes) != set(names) or set(
        prepared.object_reference_identities
    ) != set(names):
        return None

    facet_map = {
        (entry.base_bank, entry.view_role, entry.direction): entry.bank
        for entry in expansion.mapping
    }
    if not _mapping_proxy_matches(prepared.facets_by_key, facet_map):
        return None

    canonical_declared_version: str | None = None
    if not _is_mapping_proxy(prepared.profile_layouts):
        return None
    if prepared.profile_layouts:
        first_layout = next(iter(prepared.profile_layouts.values()))
        if type(first_layout) is not ProfileLayout:
            return None
        canonical_declared_version = first_layout.declared_version
    else:
        fingerprint = registry_fingerprint(expected_registry)
        if fingerprint is None or type(prepared.layout) is not CompiledLayout:
            return None
        suffix = f":facet-registry:{fingerprint}"
        if not prepared.layout.version.endswith(suffix):
            return None
        canonical_declared_version = prepared.layout.version[: -len(suffix)]
    version_prefix = f"{base.version}:composition:"
    if (
        type(canonical_declared_version) is not str
        or not canonical_declared_version.startswith(version_prefix)
        or not canonical_declared_version[len(version_prefix) :]
    ):
        return None
    canonical_profile = compile_profile_layout(
        replace(
            expansion.layout_spec,
            version=canonical_declared_version,
            carrier_id=canonical_carrier.identity,
        ),
        expected_registry,
        "shared-layout-reference-placeholder",
    )
    if canonical_profile is None:
        return None
    canonical_shared = canonical_profile.compiled
    if type(prepared.layout) is not CompiledLayout or not _typed_equal(
        prepared.layout, canonical_shared
    ):
        return None
    shared = prepared.layout

    expected_metric_rows = {
        (row.bank, row.metric, row.facet): row for row in shared.metric_rows
    }
    expected_base_rows = {(row.bank, row.metric): row for row in base.metric_rows}
    if not _mapping_proxy_matches(prepared.metric_rows, expected_metric_rows) or not (
        _mapping_proxy_matches(prepared.base_metric_rows, expected_base_rows)
    ):
        return None

    expected_codes: dict[str, CompositionCode] = {}
    expected_identities: dict[str, str] = {}
    expected_layout_names: set[str] = set()
    for object_name in names:
        identity, conflict = _reference_identity(
            base, object_name, profiles, prepared.view_roles
        )
        expected_identities[object_name] = identity
        expected_code = (
            CompositionCode.REFERENCE_MAPPING_CONFLICT
            if conflict
            else CompositionCode.OK
        )
        expected_codes[object_name] = expected_code
        if conflict:
            continue
        layout = prepared.profile_layouts.get(object_name)
        if (
            type(layout) is not ProfileLayout
            or not _validate_prepared_profile_layout(layout, shared)
            or layout.reference_set_identity != identity
            or not _typed_equal(layout.registry, expected_layout_registry)
            or layout.declared_version != canonical_declared_version
        ):
            return None
        expected_layout_names.add(object_name)
    if (
        not _mapping_proxy_matches(prepared.object_codes, expected_codes)
        or not _mapping_proxy_matches(
            prepared.object_reference_identities, expected_identities
        )
        or set(prepared.profile_layouts) != expected_layout_names
        or not _mapping_proxy_matches(
            prepared.profile_layouts,
            {name: prepared.profile_layouts[name] for name in expected_layout_names},
        )
    ):
        return None
    return shared


def _direction_tuple(joint_code: int) -> DirectionMPS:
    return (joint_code // 9 - 1, (joint_code // 3) % 3 - 1, joint_code % 3 - 1)


def _reference_contract(reference: NumericReference | None) -> tuple | None:
    if reference is None:
        return None
    return (
        reference.bank,
        reference.metric,
        reference.reference_id,
        reference.source,
        reference.units,
        type(reference.low).__name__,
        reference.low,
        type(reference.high).__name__,
        reference.high,
    )


def _source_identity(
    metadata: Mapping[str, Any], metric: MetricEncoding
) -> tuple[str | None, str, str]:
    try:
        return _source_identity_unchecked(metadata, metric)
    except (TypeError, ValueError, RecursionError):
        return None, "", "measurement_source_unavailable"


def _source_identity_unchecked(
    metadata: Mapping[str, Any], metric: MetricEncoding
) -> tuple[str | None, str, str]:
    bindings = metadata.get("bindings")
    if not isinstance(bindings, Sequence) or isinstance(bindings, (str, bytes)):
        return None, "", "measurement_binding_unavailable"
    matches = [
        binding
        for binding in bindings
        if isinstance(binding, Mapping)
        and binding.get("bank") == metric.bank
        and binding.get("metric") == metric.metric
    ]
    if len(matches) != 1:
        return None, "", "measurement_binding_unavailable"
    binding = matches[0]
    source = binding.get("source", "array")
    refs = metadata.get("source_refs")
    refs = refs if isinstance(refs, Mapping) else {}
    identity: dict[str, Any] = {
        "bank": metric.bank,
        "metric": metric.metric,
        "source": source,
    }
    if source == "unread":
        identity["reason"] = binding.get("reason")
        array_name = f"unread:{binding.get('reason', '')}"
    elif source == "record_context":
        context = metadata.get("context_sources", ())
        items = (
            [
                item
                for item in context
                if isinstance(item, Mapping)
                and item.get("bank") == metric.bank
                and item.get("metric") == metric.metric
            ]
            if isinstance(context, Sequence)
            else []
        )
        identity["binding"] = _jsonable(binding)
        identity["context"] = _jsonable(items)
        path = binding.get("path")
        array_name = "context:" + _canonical(path)
    elif source == "status_words":
        status_source = metadata.get("status_word_source")
        observation = metadata.get("observation")
        if not isinstance(status_source, Mapping):
            return None, "", "measurement_source_unavailable"
        name = status_source.get("array")
        descriptor = status_source.get("source_ref")
        stored_descriptor = refs.get(name) if isinstance(name, str) else None
        if (
            not isinstance(name, str)
            or not name
            or not isinstance(descriptor, Mapping)
            or not isinstance(stored_descriptor, Mapping)
        ):
            return None, "", "measurement_source_unavailable"
        descriptor_fields = ("artifact", "dtype", "shape", "digest")
        if any(
            descriptor.get(field) != stored_descriptor.get(field)
            for field in descriptor_fields
        ):
            return None, "", "measurement_source_unavailable"
        expected_artifact = metadata.get("source_artifact") or metadata.get(
            "owner_artifact"
        )
        if not isinstance(expected_artifact, str) and isinstance(observation, Mapping):
            expected_artifact = observation.get("artifact")
        artifact = descriptor.get("artifact")
        digest = descriptor.get("digest")
        dtype = descriptor.get("dtype")
        shape = descriptor.get("shape")
        if (
            not isinstance(expected_artifact, str)
            or artifact != expected_artifact
            or not isinstance(digest, str)
            or not digest
            or not isinstance(dtype, str)
            or not dtype
            or not isinstance(shape, (tuple, list))
            or any(
                not isinstance(dim, int) or isinstance(dim, bool) or dim < 0
                for dim in shape
            )
        ):
            return None, "", "measurement_source_unavailable"
        codes = status_source.get("codes")
        measured_names = status_source.get("measured_status_names")
        if (
            not isinstance(codes, Mapping)
            or not codes
            or not isinstance(measured_names, (tuple, list))
            or not measured_names
            or any(not isinstance(item, str) or not item for item in measured_names)
        ):
            return None, "", "measurement_source_unavailable"
        identity["status_array"] = {
            "name": name,
            **{field: _jsonable(descriptor[field]) for field in descriptor_fields},
        }
        identity["status_codes"] = _jsonable(codes)
        identity["measured_status_names"] = _jsonable(measured_names)
        identity["producer_scope"] = _jsonable(status_source.get("scope"))
        identity["unit"] = _jsonable(status_source.get("unit"))
        array_name = name
    elif source == "array":
        names = [binding.get("value")]
        if isinstance(binding.get("available"), str):
            names.append(binding["available"])
        if isinstance(binding.get("window"), str):
            names.append(binding["window"])
        observation = metadata.get("observation")
        expected_artifact = metadata.get("source_artifact") or metadata.get(
            "owner_artifact"
        )
        if not isinstance(expected_artifact, str) and isinstance(observation, Mapping):
            expected_artifact = observation.get("artifact")
        descriptors = []
        for name in names:
            if not isinstance(name, str):
                return None, "", "measurement_source_unavailable"
            descriptor = refs.get(name)
            if (
                not isinstance(descriptor, Mapping)
                or (
                    descriptor.get("artifact") is not None
                    and (
                        not isinstance(expected_artifact, str)
                        or descriptor.get("artifact") != expected_artifact
                    )
                )
                or not isinstance(descriptor.get("digest"), str)
                or not descriptor.get("digest")
                or not isinstance(descriptor.get("dtype"), str)
                or not descriptor.get("dtype")
            ):
                return None, "", "measurement_source_unavailable"
            shape = descriptor.get("shape")
            if not isinstance(shape, (tuple, list)) or any(
                not isinstance(dim, int) or isinstance(dim, bool) or dim < 0
                for dim in shape
            ):
                return None, "", "measurement_source_unavailable"
            descriptors.append({"name": name, **_jsonable(descriptor)})
        identity["arrays"] = descriptors
        identity["window"] = binding.get("window")
        array_name = str(binding.get("value"))
    else:
        return None, "", "measurement_binding_unavailable"
    try:
        canonical = _canonical(identity)
    except (TypeError, ValueError):
        return None, "", "measurement_source_unavailable"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest(), array_name, "ok"


def _profile_matches(profile: Mapping[str, Any], expected: _ProfileInput) -> bool:
    try:
        return _canonical(profile) == expected.signature
    except (TypeError, ValueError):
        return False


class StudyComposer:
    """One study's spatial cache and rowcode batches under a prepared layout."""

    def __init__(
        self, prepared: PreparedComposition, study_map_record: Mapping[str, Any]
    ):
        if not isinstance(prepared, PreparedComposition):
            raise TypeError("prepared_composition_required")
        self.prepared = prepared
        self.study_map_record = study_map_record
        self._shared_compiled_layout = _verified_shared_compiled_layout(prepared)
        self._prepared_invalid = self._shared_compiled_layout is None
        if self._prepared_invalid:
            names = (
                tuple(
                    dict.fromkeys(
                        profile.object_name
                        for profile in prepared.profiles
                        if type(profile) is _ProfileInput
                        and type(profile.object_name) is str
                        and profile.object_name
                    )
                )
                if type(prepared.profiles) is tuple
                else ()
            )
            self._object_codes = MappingProxyType(
                {name: CompositionCode.PROFILE_LAYOUT_ERROR for name in names}
            )
        else:
            self._object_codes = prepared.object_codes
        self._contexts: dict[str, SpatialContext] = {}
        self._batches: dict[str, list[RowcodeBatch]] = {
            name: [] for name in self._object_codes
        }
        self._index_maps: dict[str, list[BatchIndexMap]] = {
            name: [] for name in self._object_codes
        }
        self._additions: list[AddResult] = []
        self._finalized: StudyComposition | None = None

    def _context(self, object_name: str) -> SpatialContext:
        if object_name not in self._contexts:
            self._contexts[object_name] = prepare_spatial_context(
                self.study_map_record, object_name
            )
        return self._contexts[object_name]

    def add(
        self,
        object_name: str,
        profile_index: int,
        outcome_index: int,
        addressed: AddressedEncoding | TraceEncoding | ScopedEncoding,
        profile: Mapping[str, Any],
        source_metadata: Mapping[str, Any] | None = None,
    ) -> AddResult:
        """Retain one encoded observation as overview and known-direction batches."""
        if self._finalized is not None:
            return AddResult(
                CompositionCode.ALREADY_FINALIZED,
                object_name,
                profile_index,
                outcome_index,
            )
        if self._prepared_invalid:
            result = AddResult(
                CompositionCode.PROFILE_LAYOUT_ERROR,
                object_name if type(object_name) is str else str(object_name),
                profile_index if _plain_int(profile_index) else -1,
                outcome_index if _plain_int(outcome_index) else -1,
                detail="prepared_composition_derivatives_invalid",
            )
            self._additions.append(result)
            return result
        if not _plain_int(profile_index) or not 0 <= profile_index < len(
            self.prepared.profiles
        ):
            return AddResult(
                CompositionCode.INVALID_PROFILE_INDEX,
                str(object_name),
                -1,
                outcome_index,
            )
        if not _plain_int(outcome_index) or outcome_index < 0:
            return AddResult(
                CompositionCode.INVALID_OUTCOME_INDEX,
                str(object_name),
                profile_index,
                -1,
            )
        expected = self.prepared.profiles[profile_index]
        if (
            object_name != expected.object_name
            or not isinstance(profile, Mapping)
            or not _profile_matches(profile, expected)
        ):
            result = AddResult(
                CompositionCode.PROFILE_MISMATCH,
                str(object_name),
                profile_index,
                outcome_index,
                detail="profile_declaration_or_object_differs_from_prepared_input",
            )
            self._additions.append(result)
            return result
        object_code = self.prepared.object_codes.get(
            object_name, CompositionCode.PROFILE_LAYOUT_ERROR
        )
        if object_code is not CompositionCode.OK:
            result = AddResult(
                object_code,
                object_name,
                profile_index,
                outcome_index,
                detail="object_reference_or_layout_not_composable",
            )
            self._additions.append(result)
            return result
        if not isinstance(
            addressed, (AddressedEncoding, TraceEncoding, ScopedEncoding)
        ):
            result = AddResult(
                CompositionCode.UNSUPPORTED_ADDRESS,
                object_name,
                profile_index,
                outcome_index,
            )
            self._additions.append(result)
            return result

        metadata = addressed.metadata
        if source_metadata is not None:
            if not isinstance(source_metadata, Mapping):
                result = AddResult(
                    CompositionCode.INVALID_OBSERVATION,
                    object_name,
                    profile_index,
                    outcome_index,
                    detail="source_metadata_must_be_a_mapping",
                )
                self._additions.append(result)
                return result
            # Source-specific fields are additive; addressed adapter fields stay
            # authoritative where both layers name the same fact.
            metadata = {**dict(source_metadata), **dict(metadata)}
        observation = metadata.get("observation")
        if not isinstance(observation, Mapping):
            result = AddResult(
                CompositionCode.INVALID_OBSERVATION,
                object_name,
                profile_index,
                outcome_index,
                metadata=MappingProxyType(dict(metadata)),
            )
            self._additions.append(result)
            return result
        if any(
            observation.get(field) != profile.get(field)
            for field in ("object", "provenance", "kind", "support")
        ):
            result = AddResult(
                CompositionCode.INVALID_OBSERVATION,
                object_name,
                profile_index,
                outcome_index,
                metadata=MappingProxyType(dict(metadata)),
                detail="observation_does_not_match_profile_declaration",
            )
            self._additions.append(result)
            return result
        observation_view = _view_role(observation.get("view"))
        if observation_view is None or observation_view not in self.prepared.view_roles:
            result = AddResult(
                CompositionCode.UNDECLARED_VIEW,
                object_name,
                profile_index,
                outcome_index,
                metadata=MappingProxyType(dict(metadata)),
            )
            self._additions.append(result)
            return result
        if expected.view is not None and expected.view != observation_view:
            result = AddResult(
                CompositionCode.INVALID_OBSERVATION,
                object_name,
                profile_index,
                outcome_index,
                metadata=MappingProxyType(dict(metadata)),
                detail="observation_view_differs_from_profile_view",
            )
            self._additions.append(result)
            return result
        if addressed.encoding is None:
            code = (
                CompositionCode.TARGET_ONLY
                if addressed.status == "target_only"
                else CompositionCode.UNSUPPORTED_ADDRESS
            )
            result = AddResult(
                code,
                object_name,
                profile_index,
                outcome_index,
                metadata=MappingProxyType(dict(metadata)),
                detail=addressed.status,
            )
            self._additions.append(result)
            return result
        points: np.ndarray | None
        if isinstance(addressed, ScopedEncoding):
            points = addressed.coordinates
            address_kind = addressed.address_kind
            width = {"coarse_grid_rc": 2, "series_slice": 1}.get(address_kind)
            if (
                width is None
                or not isinstance(points, np.ndarray)
                or points.ndim != 2
                or points.shape[1:] != (width,)
                or points.dtype.kind not in "iu"
                or points.size
                and int(points.min()) < 0
                or points.size
                and points.dtype.kind == "u"
                and points.dtype.itemsize >= 8
                and int(points.max()) > np.iinfo(np.int64).max
            ):
                result = AddResult(
                    CompositionCode.SPATIAL_INPUT_MALFORMED,
                    object_name,
                    profile_index,
                    outcome_index,
                    metadata=MappingProxyType(dict(metadata)),
                    detail="scoped_coordinates_must_have_declared_nonnegative_integer_shape",
                )
                self._additions.append(result)
                return result
            scope_address = metadata.get("scope_address")
            if not isinstance(scope_address, Mapping) or not scope_address:
                result = AddResult(
                    CompositionCode.SPATIAL_INPUT_MALFORMED,
                    object_name,
                    profile_index,
                    outcome_index,
                    metadata=MappingProxyType(dict(metadata)),
                    detail="scoped_address_metadata_required",
                )
                self._additions.append(result)
                return result
            # These are measured scopes, not patient-space points. Preserve
            # their typed addresses; do not allocate fictional point arrays.
            spatial = None
            metadata = {
                **dict(metadata),
                "geometry_status": "scope_has_no_point_address",
            }
            try:
                frame_identity = _canonical(
                    {
                        "coordinate_frame": address_kind,
                        "series_uid": observation.get("series_uid"),
                        "view": observation_view,
                        "scope": scope_address,
                    }
                )
            except (TypeError, ValueError):
                result = AddResult(
                    CompositionCode.SPATIAL_INPUT_MALFORMED,
                    object_name,
                    profile_index,
                    outcome_index,
                    metadata=MappingProxyType(dict(metadata)),
                    detail="scoped_address_metadata_must_be_finite_json",
                )
                self._additions.append(result)
                return result
        elif isinstance(addressed, TraceEncoding):
            points = addressed.points_lps
            address_kind = "patient_lps"
            if (
                not isinstance(points, np.ndarray)
                or points.ndim != 2
                or points.shape[1:] != (3,)
                or points.dtype != np.dtype(np.float64)
                or not np.isfinite(points).all()
            ):
                result = AddResult(
                    CompositionCode.SPATIAL_INPUT_MALFORMED,
                    object_name,
                    profile_index,
                    outcome_index,
                    metadata=MappingProxyType(dict(metadata)),
                    detail="trace_points_must_be_finite_float64_lps",
                )
                self._additions.append(result)
                return result
            trace_slices = observation.get("slices")
            if (
                not isinstance(trace_slices, (tuple, list))
                or len(trace_slices) != 1
                or not _plain_int(trace_slices[0])
                or trace_slices[0] < 0
            ):
                result = AddResult(
                    CompositionCode.SPATIAL_INPUT_MALFORMED,
                    object_name,
                    profile_index,
                    outcome_index,
                    metadata=MappingProxyType(dict(metadata)),
                    detail="trace_slices_must_be_exactly_one_nonnegative_integer",
                )
                self._additions.append(result)
                return result
            try:
                frame_identity = _canonical(
                    {
                        "coordinate_frame": "patient_lps",
                        "owner_series_uid": metadata.get("owner_series_uid"),
                        "owner_artifact": metadata.get("owner_artifact"),
                        "target_series_uid": metadata.get("target_series_uid"),
                        "view": observation_view,
                        "slice_index": trace_slices[0],
                    }
                )
            except (TypeError, ValueError, RecursionError):
                result = AddResult(
                    CompositionCode.SPATIAL_INPUT_MALFORMED,
                    object_name,
                    profile_index,
                    outcome_index,
                    metadata=MappingProxyType(dict(metadata)),
                    detail="trace_frame_metadata_must_be_finite_json",
                )
                self._additions.append(result)
                return result
            context = self._context(object_name)
            spatial = batch_native_lps_readings(context, points)
        else:
            points = addressed.points_rc
            address_kind = "native_rc"
            if (
                not isinstance(points, np.ndarray)
                or points.ndim != 2
                or points.shape[1:] != (2,)
                or points.dtype.kind not in "iu"
                or points.dtype.kind == "b"
            ):
                result = AddResult(
                    CompositionCode.SPATIAL_INPUT_MALFORMED,
                    object_name,
                    profile_index,
                    outcome_index,
                    metadata=MappingProxyType(dict(metadata)),
                    detail="native_points_must_be_integer_n_by_2",
                )
                self._additions.append(result)
                return result
            if points.size and points.dtype.kind == "i" and int(points.min()) < 0:
                result = AddResult(
                    CompositionCode.SPATIAL_INPUT_MALFORMED,
                    object_name,
                    profile_index,
                    outcome_index,
                    metadata=MappingProxyType(dict(metadata)),
                    detail="native_points_negative",
                )
                self._additions.append(result)
                return result
            frame = metadata.get("packed_frame") or metadata.get("plane_frame")
            context = self._context(object_name)
            spatial = batch_native_rc_readings(context, points, frame=frame)
            slices = observation.get("slices")
            slice_index = (
                slices[0]
                if isinstance(slices, (tuple, list)) and len(slices) == 1
                else None
            )
            try:
                frame_identity = _canonical(
                    {
                        "coordinate_frame": "native_rc",
                        "series_uid": observation.get("series_uid"),
                        "view": observation_view,
                        "slice_index": slice_index,
                    }
                )
            except (TypeError, ValueError, RecursionError):
                result = AddResult(
                    CompositionCode.SPATIAL_INPUT_MALFORMED,
                    object_name,
                    profile_index,
                    outcome_index,
                    metadata=MappingProxyType(dict(metadata)),
                    detail="native_frame_metadata_must_be_finite_json",
                )
                self._additions.append(result)
                return result

        if spatial is not None and spatial.joint_code.shape != (points.shape[0],):
            result = AddResult(
                CompositionCode.SPATIAL_INPUT_MALFORMED,
                object_name,
                profile_index,
                outcome_index,
                metadata=MappingProxyType(dict(metadata)),
                detail="spatial_output_place_count_mismatch",
            )
            self._additions.append(result)
            return result
        known_joint_codes = (
            np.unique(spatial.joint_code[spatial.joint_code >= 0])
            if spatial is not None
            else ()
        )
        directions = tuple(
            (int(code), _direction_tuple(int(code))) for code in known_joint_codes
        )
        profile_layout = self.prepared.profile_layouts[object_name]
        source_link_base = (
            metadata.get("owner_artifact")
            if isinstance(addressed, TraceEncoding)
            else observation.get("artifact")
        )
        if not isinstance(source_link_base, str) or not source_link_base:
            source_link_base = observation.get("artifact")
        if not isinstance(source_link_base, str) or not source_link_base:
            source_link_base = "artifact_unavailable"

        metric_by_key: dict[tuple[str, str], MetricEncoding] = {}
        for metric_encoding in addressed.encoding.metrics:
            if not isinstance(metric_encoding, MetricEncoding):
                result = AddResult(
                    CompositionCode.METRIC_ENCODING_MALFORMED,
                    object_name,
                    profile_index,
                    outcome_index,
                    spatial,
                    metadata=MappingProxyType(dict(metadata)),
                )
                self._additions.append(result)
                return result
            key = (metric_encoding.bank, metric_encoding.metric)
            if key in metric_by_key:
                result = AddResult(
                    CompositionCode.METRIC_ENCODING_MALFORMED,
                    object_name,
                    profile_index,
                    outcome_index,
                    spatial,
                    metadata=MappingProxyType(dict(metadata)),
                    detail="duplicate_metric_encoding",
                )
                self._additions.append(result)
                return result
            metric_by_key[key] = metric_encoding

        expected_metric_keys = {
            (bank.name, metric.name)
            for bank in self.prepared.base_layout.banks
            for metric in bank.metrics
        }
        if set(metric_by_key) != expected_metric_keys:
            result = AddResult(
                CompositionCode.METRIC_ENCODING_MALFORMED,
                object_name,
                profile_index,
                outcome_index,
                spatial,
                metadata=MappingProxyType(dict(metadata)),
                detail="metric_encoding_set_differs_from_base_layout",
            )
            self._additions.append(result)
            return result

        pending_batches: list[RowcodeBatch] = []
        pending_maps: list[BatchIndexMap] = []
        outcome_indices: list[tuple[DirectionMPS | None, np.ndarray]] = [
            (None, np.arange(points.shape[0], dtype=np.int64))
        ]
        if spatial is not None:
            outcome_indices.extend(
                (
                    direction,
                    np.flatnonzero(spatial.joint_code == joint_code).astype(np.int64),
                )
                for joint_code, direction in directions
            )
        # Each direction selects the same native places for all its lenses.
        outcome_indices = [(d, _frozen(i)) for d, i in outcome_indices]
        coordinate_snapshot = _frozen(points)
        coordinate_groups = {}
        for direction, indices in outcome_indices:
            coordinates = (
                coordinate_snapshot
                if direction is None
                else _frozen(coordinate_snapshot[indices])
            )
            coordinate_groups[direction] = PlaceAddressBatch(
                address_kind, frame_identity, coordinates
            )
        registry_by_bank = {
            item.bank: item.coordinate for item in self.prepared.registry
        }
        for base_bank in self.prepared.base_layout.banks:
            for metric_spec in base_bank.metrics:
                metric_key = (base_bank.name, metric_spec.name)
                metric_encoding = metric_by_key.get(metric_key)
                if metric_encoding is None:
                    continue
                base_rows = self.prepared.base_metric_rows.get(metric_key)
                if (
                    base_rows is None
                    or metric_encoding.row_names != base_rows.names
                    or not isinstance(metric_encoding.row_codes, np.ndarray)
                    or metric_encoding.row_codes.dtype != np.dtype(np.int16)
                    or metric_encoding.row_codes.shape != (points.shape[0],)
                    or not isinstance(metric_encoding.source_values, np.ndarray)
                    or metric_encoding.source_values.shape != (points.shape[0],)
                    or not isinstance(metric_encoding.source_available, np.ndarray)
                    or metric_encoding.source_available.dtype.kind != "b"
                    or metric_encoding.source_available.shape != (points.shape[0],)
                ):
                    result = AddResult(
                        CompositionCode.METRIC_ROW_MISMATCH,
                        object_name,
                        profile_index,
                        outcome_index,
                        spatial,
                        metadata=MappingProxyType(dict(metadata)),
                        detail=f"metric_shape_or_rows_mismatch:{base_bank.name}:{metric_spec.name}",
                    )
                    self._additions.append(result)
                    return result
                expected_ref = expected.references.get(metric_key)
                actual_ref = _reference_contract(metric_encoding.reference)
                if (expected_ref is None) != (actual_ref is None):
                    result = AddResult(
                        CompositionCode.SOURCE_REFERENCE_MISMATCH,
                        object_name,
                        profile_index,
                        outcome_index,
                        spatial,
                        metadata=MappingProxyType(dict(metadata)),
                        detail=f"reference_presence_mismatch:{base_bank.name}:{metric_spec.name}",
                    )
                    self._additions.append(result)
                    return result
                if expected_ref is not None and actual_ref != (
                    metric_key[0],
                    metric_key[1],
                    expected_ref[0],
                    expected_ref[1],
                    expected_ref[2],
                    type(expected_ref[3]).__name__,
                    expected_ref[3],
                    type(expected_ref[4]).__name__,
                    expected_ref[4],
                ):
                    result = AddResult(
                        CompositionCode.SOURCE_REFERENCE_MISMATCH,
                        object_name,
                        profile_index,
                        outcome_index,
                        spatial,
                        metadata=MappingProxyType(dict(metadata)),
                        detail=f"reference_contract_mismatch:{base_bank.name}:{metric_spec.name}",
                    )
                    self._additions.append(result)
                    return result
                if metric_encoding.reference is not None and (
                    metric_encoding.reference.layout_fingerprint
                    != self.prepared.base_layout.fingerprint
                ):
                    result = AddResult(
                        CompositionCode.SOURCE_REFERENCE_MISMATCH,
                        object_name,
                        profile_index,
                        outcome_index,
                        spatial,
                        metadata=MappingProxyType(dict(metadata)),
                        detail=f"base_layout_reference_mismatch:{base_bank.name}:{metric_spec.name}",
                    )
                    self._additions.append(result)
                    return result
                source_identity, array_name, source_code = _source_identity(
                    metadata, metric_encoding
                )
                if source_identity is None:
                    result = AddResult(
                        CompositionCode.MEASUREMENT_SOURCE_UNAVAILABLE,
                        object_name,
                        profile_index,
                        outcome_index,
                        spatial,
                        metadata=MappingProxyType(dict(metadata)),
                        detail=source_code,
                    )
                    self._additions.append(result)
                    return result
                input_codes = metric_encoding.row_codes
                if input_codes.size and int(np.min(input_codes)) < -1:
                    result = AddResult(
                        CompositionCode.METRIC_ROW_MISMATCH,
                        object_name,
                        profile_index,
                        outcome_index,
                        spatial,
                        metadata=MappingProxyType(dict(metadata)),
                        detail=f"rowcode_below_no_measurement:{base_bank.name}:{metric_spec.name}",
                    )
                    self._additions.append(result)
                    return result
                observed = input_codes >= 0
                if observed.any() and (
                    int(np.min(input_codes[observed], axis=0)) < base_rows.start
                    or int(np.max(input_codes[observed], axis=0))
                    >= base_rows.start + len(base_rows.names)
                ):
                    result = AddResult(
                        CompositionCode.METRIC_ROW_MISMATCH,
                        object_name,
                        profile_index,
                        outcome_index,
                        spatial,
                        metadata=MappingProxyType(dict(metadata)),
                        detail=f"rowcode_outside_base_metric:{base_bank.name}:{metric_spec.name}",
                    )
                    self._additions.append(result)
                    return result

                row_batches = outcome_indices if observed.any() else outcome_indices[:1]
                for direction, indices in row_batches:
                    new_bank = self.prepared.facets_by_key.get(
                        (base_bank.name, observation_view, direction)
                    )
                    target_rows = (
                        None
                        if new_bank is None
                        else self.prepared.metric_rows.get(
                            (new_bank, metric_spec.name, base_bank.facet)
                        )
                    )
                    if target_rows is None or target_rows.names != base_rows.names:
                        result = AddResult(
                            CompositionCode.METRIC_ROW_MISMATCH,
                            object_name,
                            profile_index,
                            outcome_index,
                            spatial,
                            metadata=MappingProxyType(dict(metadata)),
                            detail=f"expanded_metric_rows_missing:{base_bank.name}:{metric_spec.name}",
                        )
                        self._additions.append(result)
                        return result
                    remapped = np.full(indices.shape, -1, dtype=np.int16)
                    source_codes = input_codes[indices]
                    written = source_codes >= 0
                    if written.any():
                        ordinal = (
                            source_codes[written].astype(np.int32) - base_rows.start
                        )
                        remapped[written] = (ordinal + target_rows.start).astype(
                            np.int16
                        )
                    remapped = _frozen(remapped)
                    source_link = SourceLink(
                        f"p{profile_index}/o{outcome_index}",
                        source_link_base,
                        array_name,
                        f"profile:{profile_index}/outcome:{outcome_index}/{base_bank.name}/{metric_spec.name}/place-index",
                    )
                    assert new_bank is not None
                    registry_coord = registry_by_bank[new_bank]
                    batch = RowcodeBatch(
                        new_bank,
                        metric_spec.name,
                        registry_coord,
                        source_identity,
                        profile_layout.compiled.fingerprint,
                        profile_layout.count_layout,
                        profile_layout.reference_set_identity,
                        remapped,
                        coordinate_groups[direction],
                        source_link,
                    )
                    ordinal = len(self._batches[object_name]) + len(pending_batches)
                    index_map = indices
                    pending_batches.append(batch)
                    pending_maps.append(
                        BatchIndexMap(
                            object_name,
                            ordinal,
                            profile_index,
                            outcome_index,
                            new_bank,
                            metric_spec.name,
                            direction,
                            index_map,
                            source_link,
                        )
                    )

        self._batches[object_name].extend(pending_batches)
        self._index_maps[object_name].extend(pending_maps)
        result = AddResult(
            CompositionCode.OK,
            object_name,
            profile_index,
            outcome_index,
            spatial,
            tuple(pending_batches),
            tuple(pending_maps),
            MappingProxyType(dict(metadata)),
        )
        self._additions.append(result)
        return result

    def finalize(self) -> StudyComposition:
        """Assemble each object's batches once and return sparse exact profiles."""
        if self._finalized is not None:
            return self._finalized
        objects: dict[str, ObjectComposition] = {}
        for object_name, object_code in self._object_codes.items():
            if object_code is not CompositionCode.OK:
                objects[object_name] = ObjectComposition(
                    object_name,
                    object_code,
                    None,
                    tuple(self._index_maps[object_name]),
                    "object_reference_or_layout_not_composable",
                )
                continue
            if self._shared_compiled_layout is None:
                assembled = assemble_object_profile(
                    object_name,
                    self.prepared.profile_layouts[object_name],
                    self._batches[object_name],
                )
            else:
                assembled = _assemble_prepared_object_profile(
                    object_name,
                    self.prepared.profile_layouts[object_name],
                    self._batches[object_name],
                    self._shared_compiled_layout,
                )
            objects[object_name] = ObjectComposition(
                object_name,
                CompositionCode.OK,
                assembled,
                tuple(self._index_maps[object_name]),
            )
        result = StudyComposition(
            (
                CompositionCode.PROFILE_LAYOUT_ERROR
                if self._prepared_invalid
                else CompositionCode.OK
            ),
            MappingProxyType(objects),
            MappingProxyType(dict(self._contexts)),
            tuple(self._additions),
        )
        self._finalized = result
        return result
