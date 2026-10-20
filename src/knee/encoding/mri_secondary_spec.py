"""Declarations for the already-retained packed, trace and sampled MRI families.

These entries expose existing source measurements to the common layout. They
do not supply a numeric reference or turn sampled points into a plane mask.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, TypedDict

# Mirrors scripts/run_interiors.py::READING_NAMES, the complete set passed to
# posterior_sayings/posterior_readings_from_sources by the retained producer.
TRACE_OBJECTS: tuple[str, ...] = (
    "semimembranosus",
    "semitendinosus",
    "gracilis",
    "popliteal_artery",
    "popliteal_vein",
)

_SECONDARY_BANKS: tuple[dict[str, Any], ...] = (
    {
        "name": "fibula_packed_target",
        "facet": "packed axial target membership at retained RC places",
        "metrics": [
            {
                "name": "target_membership",
                "kind": "words",
                "words": ["False", "True"],
            }
        ],
    },
    {
        "name": "posterior_trace_values",
        "facet": "per-point posterior trace readings at retained patient-LPS points",
        "metrics": [
            {"name": "trace_light", "kind": "digit"},
            {"name": "trace_flank", "kind": "digit"},
        ],
    },
    {
        "name": "axial_joint_samples",
        "facet": "native axial readings at retained sampled RC places",
        "metrics": [
            {
                "name": "sample_white",
                "kind": "words",
                "words": ["False", "True"],
            },
            {"name": "sample_light", "kind": "digit"},
        ],
    },
)

_SCALE_PLANS = (
    {
        "base_bank": "fibula_packed_target",
        "lens": "fibula_axial_target_membership",
        "scale_scope": "retained_place",
    },
    {
        "base_bank": "posterior_trace_values",
        "lens": "posterior_trace_light_and_flank",
        "scale_scope": "retained_place",
    },
    {
        "base_bank": "axial_joint_samples",
        "lens": "axial_joint_native_samples",
        "scale_scope": "retained_place",
    },
)


class _ProfileDeclaration(TypedDict):
    object: str
    provenance: str
    kind: str
    support: str
    view: list[str] | None
    support_layout: dict[str, Any]
    selected: dict[tuple[str, str], dict[str, Any]]
    unread_reason: str


def _unread(
    bank: dict[str, Any], metric: dict[str, Any], reason: str
) -> dict[str, str]:
    return {
        "bank": bank["name"],
        "metric": metric["name"],
        "source": "unread",
        "reason": reason,
    }


def _complete_readings(
    banks: list[dict[str, Any]],
    selected: dict[tuple[str, str], dict[str, Any]],
    *,
    reason: str,
) -> list[dict[str, Any]]:
    readings: list[dict[str, Any]] = []
    for bank in banks:
        for metric in bank["metrics"]:
            binding = selected.get((bank["name"], metric["name"]))
            readings.append(
                deepcopy(binding)
                if binding is not None
                else _unread(bank, metric, reason)
            )
    return readings


def append_secondary_declarations(spec: dict[str, Any]) -> dict[str, Any]:
    """Append the existing fibula, posterior-trace and axial-joint sample profiles.

    Existing profiles receive explicit unread bindings for these three new
    banks. New profiles receive one binding for every metric in the current
    declaration, leaving all unrelated measurements explicitly unread.
    """
    result = deepcopy(spec)
    banks = result.get("banks")
    profiles = result.get("profiles")
    if not isinstance(banks, list) or not isinstance(profiles, list):
        raise TypeError("secondary_declaration_requires_banks_and_profiles")
    existing_names = {bank.get("name") for bank in banks if isinstance(bank, dict)}
    if any(bank["name"] in existing_names for bank in _SECONDARY_BANKS):
        raise ValueError("secondary_bank_already_declared")

    for profile in profiles:
        profile["readings"].extend(
            _unread(
                bank,
                metric,
                "this source family has no binding for the profile's retained address",
            )
            for bank in _SECONDARY_BANKS
            for metric in bank["metrics"]
        )
    banks.extend(deepcopy(list(_SECONDARY_BANKS)))

    if not isinstance(result.get("object_composition"), dict):
        raise TypeError("secondary_declaration_requires_object_composition")
    plans = result["object_composition"].get("bank_plans")
    if not isinstance(plans, list):
        raise TypeError("secondary_declaration_requires_bank_plans")
    plans.extend(deepcopy(list(_SCALE_PLANS)))

    base_readings = {
        ("acquisition_context", "view_orientation"): {
            "bank": "acquisition_context",
            "metric": "view_orientation",
            "source": "record_context",
            "path": ["view", 0],
            "scope": "acquisition",
        },
        ("acquisition_context", "fluid_sensitivity"): {
            "bank": "acquisition_context",
            "metric": "fluid_sensitivity",
            "source": "record_context",
            "path": ["view", 1],
            "scope": "acquisition",
        },
        ("acquisition_context", "fat_suppression"): {
            "bank": "acquisition_context",
            "metric": "fat_suppression",
            "source": "record_context",
            "path": ["view", 2],
            "scope": "acquisition",
        },
    }

    fibula_layout = {
        "family": "fibula_axial",
        "identity_sources": {
            "owner_series_uid": "record.series_uid",
            "artifact": "record.artifact",
            "target_series_uid": "axial_evidence.series_uid",
            "target_view": "axial_evidence.view",
            "target_slice": "axial_evidence.slice",
            "row": "observation.row_to_axial_evidence.row",
        },
        "offsets": "a3_fibula_axial_offsets",
        "shapes": "a3_fibula_axial_shapes",
        "slices": "a3_fibula_axial_slices",
        "packed_arrays": [
            "a3_fibula_axial_region",
            "a3_fibula_axial_target",
            "a3_fibula_axial_available",
        ],
        "target_pixels_array": "a3_fibula_axial_target",
        "frame_arrays": {
            "origin_lps": "a3_fibula_axial_origin_lps",
            "basis_lps": "a3_fibula_axial_basis_lps",
            "normal_lps": "a3_fibula_axial_normal_lps",
            "thickness_mm": "a3_fibula_axial_thickness_mm",
        },
        "count_meaning": "fibula_axial_target_pixels",
    }
    trace_layout = {
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
    sample_layout = {
        "family": "joint_axial_profile_samples",
        "offsets": "a4_joint_axial_profile_offsets",
        "slices": "a4_joint_axial_profile_slices",
        "coordinates": "a4_joint_axial_profile_rc",
        "white": "a4_joint_axial_profile_white",
        "valid": "a4_joint_axial_profile_valid",
        "light": "a4_joint_axial_profile_light",
    }

    declarations: tuple[_ProfileDeclaration, ...] = (
        {
            "object": "fibula",
            "provenance": "native",
            "kind": "reading",
            "support": "a3_fibula_axial_region",
            "view": None,
            "support_layout": fibula_layout,
            "selected": {
                ("fibula_packed_target", "target_membership"): {
                    "bank": "fibula_packed_target",
                    "metric": "target_membership",
                    "value": "a3_fibula_axial_target",
                    "available": "a3_fibula_axial_available",
                }
            },
            "unread_reason": "fibula packed-target family does not bind this measurement",
        },
        {
            "object": "joint",
            "provenance": "native",
            "kind": "reading",
            "support": "a4_joint_axial_profile_white",
            "view": None,
            "support_layout": sample_layout,
            "selected": {
                **base_readings,
                ("axial_joint_samples", "sample_white"): {
                    "bank": "axial_joint_samples",
                    "metric": "sample_white",
                    "value": "a4_joint_axial_profile_white",
                    "available": "a4_joint_axial_profile_valid",
                },
                ("axial_joint_samples", "sample_light"): {
                    "bank": "axial_joint_samples",
                    "metric": "sample_light",
                    "value": "a4_joint_axial_profile_light",
                    "available": "a4_joint_axial_profile_valid",
                },
            },
            "unread_reason": "axial joint sample family does not bind this measurement",
        },
    )
    for item in declarations:
        profiles.append(
            {
                "object": item["object"],
                "provenance": item["provenance"],
                "kind": item["kind"],
                "support": item["support"],
                "view": item["view"],
                "support_layout": deepcopy(item["support_layout"]),
                "readings": _complete_readings(
                    banks, item["selected"], reason=item["unread_reason"]
                ),
                "references": [],
            }
        )
    for object_name in TRACE_OBJECTS:
        support = f"a3_posterior_trace_{object_name}_points_lps"
        selected = {
            **base_readings,
            ("posterior_trace_values", "trace_light"): {
                "bank": "posterior_trace_values",
                "metric": "trace_light",
                "value": "light",
            },
            ("posterior_trace_values", "trace_flank"): {
                "bank": "posterior_trace_values",
                "metric": "trace_flank",
                "value": "flank",
            },
        }
        profiles.append(
            {
                "object": object_name,
                "provenance": "native",
                "kind": "reading",
                "support": support,
                "view": None,
                "support_layout": deepcopy(trace_layout),
                "readings": _complete_readings(
                    banks,
                    selected,
                    reason="posterior trace family does not bind this measurement",
                ),
                "references": [],
            }
        )
    return result
