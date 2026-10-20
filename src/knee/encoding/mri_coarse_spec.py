"""Built-in profiles for retained coarse native MRI readings.

The separate banks preserve the producer's unfiltered and scale-filtered
coarse-grid scopes. Their stored bool membership and numeric grid values are
readings; producer status remains in the observation code and record maps.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from knee.encoding.mri_spec import BASE_SLICE_VIEWS, make_mri_spec

_ALL_VIEW_ROLES: tuple[tuple[str, str, str], ...] = tuple(
    dict.fromkeys(
        [
            *BASE_SLICE_VIEWS,
            *(
                (orientation, fluid, fat)
                for orientation in ("Sagittal", "Coronal", "Axial")
                for fluid in ("0", "1")
                for fat in ("0", "1")
            ),
        ]
    )
)

COARSE_BANKS: tuple[dict[str, Any], ...] = (
    {
        "name": "coarse_unfiltered",
        "facet": "unfiltered coarse-grid body or seed membership and readings",
        "metrics": [
            {"name": "membership", "kind": "words", "words": ["False", "True"]},
            {"name": "median", "kind": "digit"},
            {"name": "depth", "kind": "digit"},
        ],
    },
    {
        "name": "coarse_scale_filtered",
        "facet": "scale-filtered coarse-grid estimate membership and readings",
        "metrics": [
            {"name": "membership", "kind": "words", "words": ["False", "True"]},
            {"name": "median", "kind": "digit"},
            {"name": "depth", "kind": "digit"},
        ],
    },
)


def _native_layout(prefix: str, packed: tuple[str, ...]) -> dict[str, Any]:
    return {
        "family": "native_coarse_blocks",
        "offsets": f"{prefix}offsets",
        "shapes": f"{prefix}shapes",
        "slices": f"{prefix}slices",
        "windows_rc": f"{prefix}windows_rc",
        "block_px": f"{prefix}block_px",
        "block_mm": f"{prefix}block_mm",
        "packed_arrays": list(packed),
        "count_meaning": "coarse_blocks",
    }


def _fibula_layout(support_suffixes: tuple[str, ...]) -> dict[str, Any]:
    prefix = "{arrays_prefix}_"
    return {
        "family": "native_coarse_blocks",
        "target_evidence": {
            "record_field": "fibula_key_planes",
            "orientation": "axial",
        },
        "offsets": prefix + "offsets",
        "shapes": prefix + "shapes",
        "slices": prefix + "slices",
        "windows_rc": prefix + "windows_rc",
        "block_px": prefix + "block_px",
        "block_mm": prefix + "block_mm",
        "packed_arrays": [
            prefix + suffix for suffix in ("median", "depth", *support_suffixes)
        ],
        "count_meaning": "coarse_blocks",
    }


def _readings(
    scope_bank: str,
    support: str,
    median: str,
    depth: str,
    banks: list[dict[str, Any]],
) -> list[dict]:
    other_bank = (
        "coarse_scale_filtered"
        if scope_bank == "coarse_unfiltered"
        else "coarse_unfiltered"
    )
    selected = {
        (scope_bank, "membership"): {
            "bank": scope_bank,
            "metric": "membership",
            "value": support,
            "availability_policy": "all_stored",
        },
        (scope_bank, "median"): {
            "bank": scope_bank,
            "metric": "median",
            "value": median,
            "availability_policy": "finite_values",
        },
        (scope_bank, "depth"): {
            "bank": scope_bank,
            "metric": "depth",
            "value": depth,
            "availability_policy": "finite_values",
        },
    }
    readings: list[dict[str, Any]] = []
    for bank in banks:
        for metric in bank["metrics"]:
            key = (bank["name"], metric["name"])
            binding = selected.get(key)
            if binding is not None:
                readings.append(deepcopy(binding))
                continue
            if bank["name"] == other_bank:
                reason = "the other retained coarse product has a separate scope bank"
            else:
                reason = "this coarse row has no binding for the measurement"
            readings.append(
                {
                    "bank": bank["name"],
                    "metric": metric["name"],
                    "source": "unread",
                    "reason": reason,
                }
            )
    return readings


def _profile(
    object_name: str,
    support: str,
    scope_bank: str,
    layout: dict[str, Any],
    median: str,
    depth: str,
    banks: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "object": object_name,
        "provenance": "native",
        "kind": "reading",
        "support": support,
        "view": None,
        "readings": _readings(scope_bank, support, median, depth, banks),
        "references": [],
        "support_layout": deepcopy(layout),
    }


def _coarse_profiles(banks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    for bone in ("femur", "tibia"):
        prefix = "a4_axial_coarse_"
        grid_values = (
            f"{prefix}median",
            f"{prefix}depth",
            f"{prefix}{bone}_body",
            f"{prefix}{bone}_seeds",
        )
        layout = _native_layout(prefix, grid_values)
        for support in (f"{prefix}{bone}_body", f"{prefix}{bone}_seeds"):
            profiles.append(
                _profile(
                    bone,
                    support,
                    "coarse_unfiltered",
                    layout,
                    f"{prefix}median",
                    f"{prefix}depth",
                    banks,
                )
            )
        filtered_values = (
            f"{prefix}median",
            f"{prefix}depth",
            f"{prefix}{bone}_estimate_body",
        )
        filtered_layout = _native_layout(prefix, filtered_values)
        profiles.append(
            _profile(
                bone,
                f"{prefix}{bone}_estimate_body",
                "coarse_scale_filtered",
                filtered_layout,
                f"{prefix}median",
                f"{prefix}depth",
                banks,
            )
        )

    patella_prefix = "a4_patella_coarse_"
    patella_values = (
        f"{patella_prefix}median",
        f"{patella_prefix}depth",
        f"{patella_prefix}patella_body",
        f"{patella_prefix}patella_seeds",
    )
    patella_layout = _native_layout(patella_prefix, patella_values)
    for support in (f"{patella_prefix}patella_body", f"{patella_prefix}patella_seeds"):
        profiles.append(
            _profile(
                "patella",
                support,
                "coarse_unfiltered",
                patella_layout,
                f"{patella_prefix}median",
                f"{patella_prefix}depth",
                banks,
            )
        )

    fibula_prefix = "{arrays_prefix}_"
    fibula_layout = _fibula_layout(("fibula_body", "fibula_seeds"))
    for suffix in ("fibula_body", "fibula_seeds"):
        profiles.append(
            _profile(
                "fibula",
                fibula_prefix + suffix,
                "coarse_unfiltered",
                fibula_layout,
                fibula_prefix + "median",
                fibula_prefix + "depth",
                banks,
            )
        )
    return profiles


def append_coarse_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Append the retained coarse-grid families once to an existing MRI spec."""
    if not isinstance(spec, dict) or not isinstance(spec.get("banks"), list):
        raise TypeError("mri_spec_required")
    if any(
        bank.get("name") in {item["name"] for item in COARSE_BANKS}
        for bank in spec["banks"]
    ):
        raise ValueError("coarse_banks_already_declared")
    spec = deepcopy(spec)
    spec["version"] = "retained-mri-base-and-coarse-readings-v1"
    spec["banks"].extend(deepcopy(list(COARSE_BANKS)))
    for profile in spec["profiles"]:
        profile["readings"].extend(
            [
                {
                    "bank": bank["name"],
                    "metric": metric["name"],
                    "source": "unread",
                    "reason": "this profile has no coarse-grid observation",
                }
                for bank in COARSE_BANKS
                for metric in bank["metrics"]
            ]
        )
    composition = spec["object_composition"]
    composition["view_roles"] = [list(view) for view in _ALL_VIEW_ROLES]
    composition["bank_plans"].extend(
        [
            {
                "base_bank": "coarse_unfiltered",
                "lens": "axial_coarse_unfiltered",
                "scale_scope": "producer_unfiltered_coarse_grid",
            },
            {
                "base_bank": "coarse_scale_filtered",
                "lens": "axial_coarse_scale_filtered",
                "scale_scope": "producer_scale_filtered_coarse_grid",
            },
        ]
    )
    spec["profiles"].extend(_coarse_profiles(spec["banks"]))
    return spec


def make_mri_coarse_spec() -> dict[str, Any]:
    """Build the standard MRI declaration with its retained coarse-grid readings."""
    return make_mri_spec(include_coarse=True)
