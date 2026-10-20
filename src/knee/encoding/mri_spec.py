"""Installed base-slice MRI declaration for the retained measurement path.

This is a first measurement declaration, not a complete MRI normative
catalogue. It preserves measured values and explicit unread bindings; it does
not assign healthy ranges or diagnoses.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from knee.encoding.mri_secondary_spec import append_secondary_declarations
from knee.objects.assignments import OBJECT_CODES

BASE_SLICE_VIEWS: tuple[tuple[str, str, str], ...] = (
    ("Sagittal", "0", "0"),
    ("Sagittal", "1", "1"),
    ("Coronal", "0", "0"),
    ("Coronal", "1", "1"),
    ("Axial", "1", "1"),
)

_BANKS: tuple[dict[str, Any], ...] = (
    {
        "name": "lens_boolean",
        "facet": "measured low-signal boolean",
        "metrics": [
            {"name": "low_signal", "kind": "words", "words": ["False", "True"]}
        ],
    },
    {
        "name": "lens_raw_signal",
        "facet": "acquired raw signal; no supplied norm",
        "metrics": [{"name": "raw_signal", "kind": "digit"}],
    },
    {
        "name": "lens_distance",
        "facet": "measured distance; no supplied norm",
        "metrics": [{"name": "distance_mm", "kind": "digit"}],
    },
    {
        "name": "acquisition_context",
        "facet": "retained acquisition descriptor",
        "metrics": [
            {
                "name": "view_orientation",
                "kind": "words",
                "words": ["Sagittal", "Coronal", "Axial"],
            },
            {"name": "fluid_sensitivity", "kind": "words", "words": ["0", "1"]},
            {"name": "fat_suppression", "kind": "words", "words": ["0", "1"]},
        ],
    },
    {
        "name": "native_profile_area",
        "facet": "retained per-slice support area; no supplied norm",
        "metrics": [{"name": "area_mm2", "kind": "digit"}],
    },
    {
        "name": "native_profile_status",
        "facet": "measured native producer status word",
        "metrics": [
            {
                "name": "status",
                "kind": "words",
                "words": [
                    "not_read",
                    "none",
                    "body",
                    "unreadable",
                    "cut",
                    "unread",
                    "head_still_a_disc",
                    "head_no_longer_a_disc",
                    "head_unreadable",
                ],
            }
        ],
    },
)

_PROFILE_STATUS_CODES = {
    "not_read": 0,
    "none": 1,
    "body": 2,
    "unreadable": 3,
    "cut": 4,
}
_HEAD_STATUS_CODES = {
    "unread": 0,
    "head_still_a_disc": 1,
    "head_no_longer_a_disc": 2,
    "head_unreadable": 3,
}

_NATIVE_SLICE_PROFILES: tuple[dict[str, Any], ...] = (
    {
        "object": "femur",
        "support": "a3_femur_profile_area_mm2",
        "values": "a3_femur_profile_area_mm2",
        "status": "a3_femur_profile_status",
        "status_codes": _PROFILE_STATUS_CODES,
        "measured_status_names": ["body"],
        "unit": "mm^2",
        "scope": "cheap marrow-like per-slice support area; not whole-bone extent",
    },
    {
        "object": "tibia",
        "support": "a3_tibia_profile_area_mm2",
        "values": "a3_tibia_profile_area_mm2",
        "status": "a3_tibia_profile_status",
        "status_codes": _PROFILE_STATUS_CODES,
        "measured_status_names": ["body"],
        "unit": "mm^2",
        "scope": "cheap marrow-like per-slice support area; not whole-bone extent",
    },
    {
        "object": "joint_fluid",
        "support": "a3_recess_profile_area_mm2",
        "values": "a3_recess_profile_area_mm2",
        "status": "a3_recess_profile_status",
        "status_codes": _PROFILE_STATUS_CODES,
        "measured_status_names": ["body"],
        "unit": "mm^2",
        "scope": "2 mm-block fluid-level support area in the earlier-located compartment; not a boundary or name",
    },
    {
        "object": "fibula",
        "support": "a3_fibula_profile_area_mm2",
        "values": "a3_fibula_profile_area_mm2",
        "status": "a3_fibula_profile_status",
        "status_codes": _PROFILE_STATUS_CODES,
        "measured_status_names": ["body"],
        "unit": "mm^2",
        "scope": "marrow-like pointer profile support area; not whole-bone extent",
    },
    {
        "object": "fibula",
        "support": "a3_fibula_head_area_mm2",
        "values": "a3_fibula_head_area_mm2",
        "status": "a3_fibula_head_status",
        "status_codes": _HEAD_STATUS_CODES,
        "measured_status_names": ["head_still_a_disc"],
        "unit": "mm^2",
        "scope": "native fibular-head continuation area; not whole-bone extent",
    },
)


def _base_readings() -> list[dict[str, Any]]:
    return [
        {
            "bank": "lens_boolean",
            "metric": "low_signal",
            "value": "b1_dark",
            "available": "b1_available",
        },
        {
            "bank": "lens_raw_signal",
            "metric": "raw_signal",
            "value": "acquired_plane",
            "available": "b1_available",
        },
        {
            "bank": "lens_distance",
            "metric": "distance_mm",
            "value": "b1_distance_mm",
            "available": "b1_available",
        },
        {
            "bank": "acquisition_context",
            "metric": "view_orientation",
            "source": "record_context",
            "path": ["view", 0],
            "scope": "acquisition",
        },
        {
            "bank": "acquisition_context",
            "metric": "fluid_sensitivity",
            "source": "record_context",
            "path": ["view", 1],
            "scope": "acquisition",
        },
        {
            "bank": "acquisition_context",
            "metric": "fat_suppression",
            "source": "record_context",
            "path": ["view", 2],
            "scope": "acquisition",
        },
    ]


def _profile_unread_bindings() -> list[dict[str, Any]]:
    return [
        {
            "bank": "native_profile_area",
            "metric": "area_mm2",
            "source": "unread",
            "reason": "this base-slice observation has no native depth-profile area measurement",
        },
        {
            "bank": "native_profile_status",
            "metric": "status",
            "source": "unread",
            "reason": "this base-slice observation has no native depth-profile status word",
        },
    ]


def _native_profile_readings() -> list[dict[str, Any]]:
    return [
        {
            "bank": "lens_boolean",
            "metric": "low_signal",
            "source": "unread",
            "reason": "a slice-profile value is not a plane low-signal mask",
        },
        {
            "bank": "lens_raw_signal",
            "metric": "raw_signal",
            "source": "unread",
            "reason": "a slice-profile value is not acquired plane pixels",
        },
        {
            "bank": "lens_distance",
            "metric": "distance_mm",
            "source": "unread",
            "reason": "a slice-profile value is not a per-pixel distance field",
        },
        {
            "bank": "acquisition_context",
            "metric": "view_orientation",
            "source": "record_context",
            "path": ["view", 0],
            "scope": "acquisition",
        },
        {
            "bank": "acquisition_context",
            "metric": "fluid_sensitivity",
            "source": "record_context",
            "path": ["view", 1],
            "scope": "acquisition",
        },
        {
            "bank": "acquisition_context",
            "metric": "fat_suppression",
            "source": "record_context",
            "path": ["view", 2],
            "scope": "acquisition",
        },
    ]


def _normalize_views(view: Sequence[str] | None) -> tuple[tuple[str, str, str], ...]:
    if view is None:
        return BASE_SLICE_VIEWS
    if (
        isinstance(view, (str, bytes))
        or len(view) != 3
        or any(not isinstance(part, str) or not part for part in view)
    ):
        raise ValueError("view_must_be_one_explicit_base_slice_view")
    normalized = (view[0], view[1], view[2])
    if normalized not in BASE_SLICE_VIEWS:
        raise ValueError("view_not_in_base_slice_views")
    return (normalized,)


def make_mri_spec(
    object_codes: Mapping[str, int] = OBJECT_CODES,
    *,
    view: Sequence[str] | None = None,
    retained_ordinary_profiles: bool = False,
    include_coarse: bool = False,
) -> dict[str, Any]:
    """Build the shared-layout base-slice declaration.

    ``view=None`` explicitly expands the five supported acquisition views.
    A concrete view narrows the declaration to that member of the same set.
    Every nonzero canonical object is represented in both native and laid
    resolved profile families. Numeric readings intentionally have no refs.
    """
    if not isinstance(object_codes, Mapping):
        raise TypeError("object_codes_must_be_mapping")
    if dict(object_codes) != OBJECT_CODES:
        raise ValueError("canonical_object_codes_required")
    names = [name for name, code in OBJECT_CODES.items() if code != 0]

    selected_views = _normalize_views(view)
    profiles: list[dict[str, Any]] = []
    for name in names:
        for provenance in ("native", "laid"):
            for selected_view in selected_views:
                profiles.append(
                    {
                        "object": name,
                        "provenance": provenance,
                        "kind": "resolved",
                        "support": "a1_objects",
                        "view": list(selected_view),
                        "readings": _base_readings() + _profile_unread_bindings(),
                        "references": [],
                    }
                )

    for item in _NATIVE_SLICE_PROFILES:
        support_layout = {
            "family": "native_slice_profile_values",
            "support": item["support"],
            "values": item["values"],
            "status": item["status"],
            "status_codes": dict(item["status_codes"]),
            "measured_status_names": list(item["measured_status_names"]),
            "unit": item["unit"],
            "scope": item["scope"],
        }
        profiles.append(
            {
                "object": item["object"],
                "provenance": "native",
                "kind": "reading",
                "support": item["support"],
                "view": None,
                "support_layout": support_layout,
                "readings": [
                    *_native_profile_readings(),
                    {
                        "bank": "native_profile_area",
                        "metric": "area_mm2",
                        "value": item["values"],
                        "available": item["status"],
                    },
                    {
                        "bank": "native_profile_status",
                        "metric": "status",
                        "source": "status_words",
                    },
                ],
                "references": [],
            }
        )

    if not isinstance(retained_ordinary_profiles, bool):
        raise TypeError("retained_ordinary_profiles_must_be_bool")

    declaration = {
        "version": "retained-base-slice-measurements-v1",
        "storage": "h5",
        "h5_encoding": "modular_hybrid",
        "authored_definition_context": True,
        "banks": deepcopy(list(_BANKS)),
        "profiles": profiles,
        "retained_ordinary_profiles": retained_ordinary_profiles,
        "object_composition": {
            "version": "knee-mps-object-v1",
            "view_roles": [list(item) for item in BASE_SLICE_VIEWS],
            "bank_plans": [
                {
                    "base_bank": "lens_boolean",
                    "lens": "b1",
                    "scale_scope": "retained_place",
                },
                {
                    "base_bank": "lens_raw_signal",
                    "lens": "b1",
                    "scale_scope": "retained_place",
                },
                {
                    "base_bank": "lens_distance",
                    "lens": "b1",
                    "scale_scope": "retained_place",
                },
                {
                    "base_bank": "acquisition_context",
                    "lens": "record_context",
                    "scale_scope": "acquisition_record",
                },
                {
                    "base_bank": "native_profile_area",
                    "lens": "native_slice_profile",
                    "scale_scope": "retained_mm2",
                },
                {
                    "base_bank": "native_profile_status",
                    "lens": "native_slice_profile",
                    "scale_scope": "retained_slice",
                },
            ],
        },
        "declaration_scope": "base_slice_family_only_not_full_mri_normative_catalogue",
    }
    if not isinstance(include_coarse, bool):
        raise TypeError("include_coarse_must_be_bool")
    if include_coarse:
        from knee.encoding.mri_coarse_spec import append_coarse_spec

        declaration = append_coarse_spec(declaration)
    return append_secondary_declarations(declaration)
