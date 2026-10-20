"""Expand declared base metric banks into shared view/scale/direction facets.

This module is a declaration compiler only. Callers retain and supply all
measurement values, continuous coordinates, availability, and rowcodes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from typing import TypeAlias

from knee.encoding.places import BankSpec, LayoutSpec, MetricSpec

ViewRole: TypeAlias = tuple[str, str, str]
DirectionMPS: TypeAlias = tuple[int, int, int]

# Axis order is explicitly medial, posterior, superior. Zero is a known
# centered ternary coordinate; None is the unconditioned overview facet.
MPS_DIRECTIONS: tuple[DirectionMPS, ...] = tuple(
    (m, p, s) for m in (-1, 0, 1) for p in (-1, 0, 1) for s in (-1, 0, 1)
)
OVERVIEW_DIRECTION: None = None


@dataclass(frozen=True, slots=True)
class BankFacetPlan:
    """Caller declaration for the view-independent base bank meaning."""

    base_bank: str
    lens: str
    scale_scope: str


@dataclass(frozen=True, slots=True)
class FacetRegistryEntry:
    """Metadata shaped for conversion to the registry binder's BankFacet."""

    bank: str
    view_role: ViewRole
    lens: str
    scale: str
    direction: DirectionMPS | None

    def as_record(self) -> dict[str, object]:
        """Return lossless registry fields; direction is a named M/P/S triple."""
        return {
            "bank": self.bank,
            "coordinate": {
                "view_role": self.view_role,
                "lens": self.lens,
                "scale": self.scale,
                "direction": self.direction,
            },
        }


@dataclass(frozen=True, slots=True)
class ExpandedBank:
    """One stable expansion key and its generated bank name."""

    base_bank: str
    view_role: ViewRole
    direction: DirectionMPS | None
    bank: str
    lens: str
    scale_scope: str

    @property
    def registry_entry(self) -> FacetRegistryEntry:
        return FacetRegistryEntry(
            self.bank,
            self.view_role,
            self.lens,
            self.scale_scope,
            self.direction,
        )


class FacetExpansionCode(StrEnum):
    OK = "ok"
    INVALID_BASE_LAYOUT = "invalid_base_layout"
    INVALID_VIEW_ROLES = "invalid_view_roles"
    INVALID_VIEW_ROLE = "invalid_view_role"
    DUPLICATE_VIEW_ROLE = "duplicate_view_role"
    INVALID_BASE_BANKS = "invalid_base_banks"
    DUPLICATE_BASE_BANK = "duplicate_base_bank"
    INVALID_BANK_PLANS = "invalid_bank_plans"
    INVALID_BANK_PLAN = "invalid_bank_plan"
    DUPLICATE_BANK_PLAN = "duplicate_bank_plan"
    UNKNOWN_BASE_BANK = "unknown_base_bank"
    INCOMPLETE_BANK_PLANS = "incomplete_bank_plans"
    INVALID_METRICS = "invalid_metrics"
    GENERATED_BANK_COLLISION = "generated_bank_collision"


@dataclass(frozen=True, slots=True)
class FacetExpansion:
    """Unbound expanded layout plus complete stable facet metadata."""

    layout_spec: LayoutSpec
    registry: tuple[FacetRegistryEntry, ...]
    mapping: tuple[ExpandedBank, ...]
    base_version: str

    def bank_for(
        self,
        base_bank: str,
        view_role: ViewRole,
        direction: DirectionMPS | None,
    ) -> str | None:
        """Resolve one declared (base bank, complete view, direction) key."""
        if not _valid_view_role(view_role):
            return None
        if direction is not None and not _valid_direction(direction):
            return None
        for entry in self.mapping:
            if (
                entry.base_bank == base_bank
                and entry.view_role == view_role
                and entry.direction == direction
            ):
                return entry.bank
        return None

    def banks_for_reading(
        self,
        base_bank: str,
        view_role: ViewRole,
        measured_direction: DirectionMPS | None,
    ) -> tuple[str, ...] | None:
        """Overview always; additionally the conditioned bank for known direction.

        `None` means the direction measurement is unknown, so only the
        unconditioned overview receives the available reading. It is not the
        known center tuple `(0, 0, 0)`. Availability is decided by the caller.
        """
        overview = self.bank_for(base_bank, view_role, None)
        if overview is None:
            return None
        if measured_direction is None:
            return (overview,)
        if not _valid_direction(measured_direction):
            return None
        conditioned = self.bank_for(base_bank, view_role, measured_direction)
        if conditioned is None:
            return None
        return (overview, conditioned)


@dataclass(frozen=True, slots=True)
class FacetExpansionResult:
    code: FacetExpansionCode
    expansion: FacetExpansion | None = None


def _valid_view_role(value: object) -> bool:
    return (
        isinstance(value, tuple)
        and len(value) == 3
        and all(isinstance(part, str) and bool(part) for part in value)
    )


def _valid_direction(value: object) -> bool:
    return (
        isinstance(value, tuple)
        and len(value) == 3
        and all(type(part) is int and part in (-1, 0, 1) for part in value)
    )


def _bank_name(
    base_bank: str,
    view_role: ViewRole,
    lens: str,
    scale_scope: str,
    direction: DirectionMPS | None,
) -> str:
    # JSON is an injective, deterministic name for these typed scalar fields;
    # unlike a study UID, every input is a layout declaration.
    payload = json.dumps(
        [base_bank, list(view_role), lens, scale_scope, direction],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return f"facet:{payload}"


def expand_facets(
    base: LayoutSpec,
    view_roles: tuple[ViewRole, ...],
    bank_plans: tuple[BankFacetPlan, ...],
) -> FacetExpansionResult:
    """Expand base banks over declared views and overview+27 MPS directions.

    The returned `LayoutSpec` is intentionally unbound: its declared version
    and carrier identity are preserved, and the caller passes `registry` to
    the shared registry binder before calling `compile_layout`. The binder
    fingerprints the complete registry into the actual compiled version.
    """
    if not isinstance(base, LayoutSpec):
        return FacetExpansionResult(FacetExpansionCode.INVALID_BASE_LAYOUT)
    if (
        not isinstance(base.version, str)
        or not base.version
        or not isinstance(base.carrier_id, str)
        or not base.carrier_id
        or not isinstance(base.banks, tuple)
        or not base.banks
    ):
        return FacetExpansionResult(FacetExpansionCode.INVALID_BASE_LAYOUT)
    if not isinstance(view_roles, tuple) or not view_roles:
        return FacetExpansionResult(FacetExpansionCode.INVALID_VIEW_ROLES)
    if any(not _valid_view_role(view) for view in view_roles):
        return FacetExpansionResult(FacetExpansionCode.INVALID_VIEW_ROLE)
    if len(set(view_roles)) != len(view_roles):
        return FacetExpansionResult(FacetExpansionCode.DUPLICATE_VIEW_ROLE)
    if not isinstance(bank_plans, tuple):
        return FacetExpansionResult(FacetExpansionCode.INVALID_BANK_PLANS)

    base_names: list[str] = []
    for bank in base.banks:
        if (
            not isinstance(bank, BankSpec)
            or not isinstance(bank.name, str)
            or not bank.name
        ):
            return FacetExpansionResult(FacetExpansionCode.INVALID_BASE_BANKS)
        if bank.name in base_names:
            return FacetExpansionResult(FacetExpansionCode.DUPLICATE_BASE_BANK)
        base_names.append(bank.name)
    if any(not isinstance(plan, BankFacetPlan) for plan in bank_plans):
        return FacetExpansionResult(FacetExpansionCode.INVALID_BANK_PLAN)
    plan_by_name: dict[str, BankFacetPlan] = {}
    for plan in bank_plans:
        if (
            not isinstance(plan.base_bank, str)
            or not plan.base_bank
            or not isinstance(plan.lens, str)
            or not plan.lens
            or not isinstance(plan.scale_scope, str)
            or not plan.scale_scope
        ):
            return FacetExpansionResult(FacetExpansionCode.INVALID_BANK_PLAN)
        if plan.base_bank in plan_by_name:
            return FacetExpansionResult(FacetExpansionCode.DUPLICATE_BANK_PLAN)
        if plan.base_bank not in base_names:
            return FacetExpansionResult(FacetExpansionCode.UNKNOWN_BASE_BANK)
        plan_by_name[plan.base_bank] = plan
    if set(plan_by_name) != set(base_names):
        return FacetExpansionResult(FacetExpansionCode.INCOMPLETE_BANK_PLANS)

    expanded_banks: list[BankSpec] = []
    mapping: list[ExpandedBank] = []
    registry: list[FacetRegistryEntry] = []
    directions: tuple[DirectionMPS | None, ...] = (None, *MPS_DIRECTIONS)
    for base_bank in base.banks:
        plan = plan_by_name[base_bank.name]
        if not isinstance(base_bank.metrics, tuple) or not base_bank.metrics:
            return FacetExpansionResult(FacetExpansionCode.INVALID_METRICS)
        if any(not isinstance(metric, MetricSpec) for metric in base_bank.metrics):
            return FacetExpansionResult(FacetExpansionCode.INVALID_METRICS)
        for view_role in view_roles:
            for direction in directions:
                name = _bank_name(
                    base_bank.name,
                    view_role,
                    plan.lens,
                    plan.scale_scope,
                    direction,
                )
                expanded_banks.append(
                    BankSpec(name, base_bank.facet, base_bank.metrics)
                )
                entry = ExpandedBank(
                    base_bank.name,
                    view_role,
                    direction,
                    name,
                    plan.lens,
                    plan.scale_scope,
                )
                mapping.append(entry)
                registry.append(entry.registry_entry)

    if len({bank.name for bank in expanded_banks}) != len(expanded_banks):
        return FacetExpansionResult(FacetExpansionCode.GENERATED_BANK_COLLISION)
    layout_spec = LayoutSpec(base.version, base.carrier_id, tuple(expanded_banks))
    expansion = FacetExpansion(
        layout_spec,
        tuple(registry),
        tuple(mapping),
        base.version,
    )
    return FacetExpansionResult(FacetExpansionCode.OK, expansion)
