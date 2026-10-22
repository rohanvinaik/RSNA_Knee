"""Shared shapes for the squint-to-training upgrade (SQUINT_TRAINING_BUILD §3, §3a).

Frozen in wave 0 so independent workers build compatible parts. Each shape is a
plain dict of numpy arrays and JSON values, like the rest of ``knee.diagnosis``.
The validators read a value and return a named code; they never repair one.
They state meanings, not implementations: each docstring names the lane that
produces the shape and the consumers that read it.

Leg map (lane W1). One series' 10 mm tile grid sorted into the leg and what is
not the leg. Rohan, 2026-10-18: what is not in the leg is never a target for
compute. A useful prior, not a skin boundary: enclosed dark tissue (cortex,
tendons, menisci) is leg; a tile straddling the edge is mixed; unavailable
tiles are unknown, never outside.

Territory (lanes W4, W9, W10, W12). The tiles one object is read over in one
series, each with a role: the object's own places, its surroundings (context),
outside the leg, or not queried. ``tile_window`` is only an address; the roles
inside it are the territory. ``object_share`` is the measured share of each
tile's native pixels that the object's support covers, NaN where no support
was measured (an anatomical expectation has roles but no measured share).
``native_support`` optionally carries the support mask itself for the finer
reading; it is runtime-only and never serialized.

Profile written over a territory (lane W2). Same dict shape as
``knee.squint-profile/v1``. Its procedure is ``TERRITORY_PROCEDURE`` and every
bank name carries the territory role, so a v2 profile never meets a v1 one in
a comparison (``cosine_evidence`` refuses differing procedures).

Anchor (lane W9). One bone found by structure in the current study, with its
territories by series, the key planes that constrain it and named partial or
conflicting outcomes. Breadth is a measurement of attributed bone, or None.

Question selection (lane W6). The banks one question reads, chosen before any
score from the existing declarations and condition contracts. An empty
selection is named; nothing falls back to every bank.

Memory view (lane W8). One immutable memory revision with a stated set of
studies left out of every consumer: location, recall, censors, configurations
and prepared comparisons alike.

Residual request and result (lane W12). An open question asks one named,
existing anatomical producer to resolve its object inside a bounded region;
the result carries the native support it found, the profile written over it
and the cost, or a named reason it could not.

Teaching round (lane W14). Parent revision, independent call sources,
admission outcomes, the published child revision and its evaluation.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

LEG_MAP_SCHEMA = "knee.squint-leg-map/v1"
TERRITORY_SCHEMA = "knee.squint-territory/v1"
ANCHOR_SCHEMA = "knee.squint-anchor/v1"
SELECTION_SCHEMA = "knee.squint-question-selection/v1"
MEMORY_VIEW_SCHEMA = "knee.squint-memory-view/v1"
RESIDUAL_REQUEST_SCHEMA = "knee.squint-residual-request/v1"
RESIDUAL_RESULT_SCHEMA = "knee.squint-residual-result/v1"
TEACHING_ROUND_SCHEMA = "knee.squint-teaching-round/v1"

#: Procedure of profiles counted over a territory, against leg-only cutoffs.
TERRITORY_PROCEDURE = "knee.squint-profile/leg-tercile-territory-v2"

# Leg codes, one int8 per 10 mm tile.
LEG_UNKNOWN = -1
LEG_OUTSIDE = 0
LEG_INSIDE = 1
LEG_MIXED = 2
LEG_CODES = (LEG_UNKNOWN, LEG_OUTSIDE, LEG_INSIDE, LEG_MIXED)

# Territory roles, one int8 per tile of the territory's window.
ROLE_UNQUERIED = -1
ROLE_OUTSIDE_LEG = 0
ROLE_OBJECT = 1
ROLE_CONTEXT = 2
ROLE_CODES = (ROLE_UNQUERIED, ROLE_OUTSIDE_LEG, ROLE_OBJECT, ROLE_CONTEXT)
#: Roles that write banks. Outside-leg and unqueried tiles write nothing.
ROLE_NAMES = {ROLE_OBJECT: "object", ROLE_CONTEXT: "context"}

TERRITORY_ORIGINS = (
    "teacher_support",
    "anchor_structure",
    "anatomical_relation",
    "residual_native_support",
    "fallback_location",
)
#: Origins whose object tiles must carry a measured share.
MEASURED_ORIGINS = ("teacher_support", "residual_native_support")
ANCHOR_STATUSES = ("complete", "partial", "conflict", "unavailable")
SUBJECT_ROLES = ("defining", "alternative", "supporting")
RESIDUAL_CODES = (
    "measured",
    "procedure_unavailable",
    "object_region_unavailable",
    "deadline_before_residual",
    "already_measured",
    "no_compatible_reading",
)
TEACHING_STATUSES = ("published", "evaluated", "refused", "incomplete")

_ORIENTATIONS = ("sagittal", "coronal", "axial")


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "\0" not in value


def _ints(value: object, length: int) -> tuple[int, ...] | None:
    """The value as a tuple of exactly ``length`` plain ints, else None."""
    if (
        isinstance(value, (list, tuple))
        and len(value) == length
        and all(type(item) is int for item in value)
    ):
        return tuple(value)
    return None


def _window_shape(window: Sequence[int]) -> tuple[int, int, int] | None:
    z0, z1, r0, r1, c0, c1 = window
    if not (0 <= z0 < z1 and 0 <= r0 < r1 and 0 <= c0 < c1):
        return None
    return (z1 - z0, r1 - r0, c1 - c0)


def territory_bank_name(
    view: Mapping[str, str], role: str, metric: str, direction: str, tile_mm: float
) -> str:
    """Name one v2 bank: the v1 fields plus the territory role it was read over."""
    if role not in ROLE_NAMES.values():
        raise ValueError("territory_role_invalid")
    view_key = json.dumps(
        [view["orientation"], view["fluid_sensitive"], view["fat_suppression"]],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return (
        f"squint/v2/view={view_key}/role={role}/metric={metric}/"
        f"direction={direction}/scale={tile_mm:g}mm"
    )


def parse_territory_bank_name(name: object) -> dict[str, Any] | None:
    """Split a v2 bank name into its fields; None for anything else."""
    if not isinstance(name, str) or not name.startswith("squint/v2/view="):
        return None
    rest = name[len("squint/v2/view=") :]
    marker = "]/role="
    end = rest.find(marker)
    if end < 0:
        return None
    try:
        view = json.loads(rest[: end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(view, list) or len(view) != 3:
        return None
    fields: dict[str, Any] = {"view": view}
    for part in rest[end + 2 :].split("/"):
        key, sep, value = part.partition("=")
        if not sep or key in fields:
            return None
        fields[key] = value
    if set(fields) != {"view", "role", "metric", "direction", "scale"}:
        return None
    if fields["role"] not in ROLE_NAMES.values() or not fields["scale"].endswith("mm"):
        return None
    try:
        fields["scale_mm"] = float(fields["scale"][:-2])
    except ValueError:
        return None
    return fields


def leg_map_code(value: object, *, grid_shape: tuple[int, ...] | None = None) -> str:
    """``valid`` or the first named defect of a leg map."""
    import numpy as np

    if not isinstance(value, Mapping) or value.get("schema") != LEG_MAP_SCHEMA:
        return "leg_map_schema_invalid"
    if not _text(value.get("series_uid")) or not _text(value.get("rule")):
        return "leg_map_identity_invalid"
    tile_mm = value.get("tile_mm")
    if isinstance(tile_mm, bool) or not isinstance(tile_mm, (int, float)):
        return "leg_map_tile_mm_invalid"
    codes = value.get("codes")
    if not isinstance(codes, np.ndarray) or codes.dtype != np.int8 or codes.ndim != 3:
        return "leg_map_codes_invalid"
    if grid_shape is not None and codes.shape != tuple(grid_shape):
        return "leg_map_shape_mismatch"
    if not np.isin(codes, LEG_CODES).all():
        return "leg_map_code_unknown"
    share = value.get("leg_share")
    if not isinstance(share, np.ndarray) or share.shape != codes.shape:
        return "leg_map_share_invalid"
    finite = np.isfinite(share)
    if np.any((share[finite] < 0) | (share[finite] > 1)):
        return "leg_map_share_out_of_range"
    if np.any(finite & (codes == LEG_INSIDE) & (share < 1)) or np.any(
        finite & (codes == LEG_OUTSIDE) & (share > 0)
    ):
        return "leg_map_share_contradicts_code"
    if not isinstance(value.get("provenance"), Mapping):
        return "leg_map_provenance_missing"
    return "valid"


def territory_code(value: object, *, grid_shape: tuple[int, ...] | None = None) -> str:
    """``valid`` or the first named defect of a territory."""
    import numpy as np

    if not isinstance(value, Mapping) or value.get("schema") != TERRITORY_SCHEMA:
        return "territory_schema_invalid"
    for key in ("study_uid", "series_uid", "subject"):
        if not _text(value.get(key)):
            return "territory_identity_invalid"
    origin = value.get("origin")
    if origin not in TERRITORY_ORIGINS:
        return "territory_origin_invalid"
    window = _ints(value.get("tile_window"), 6)
    if window is None:
        return "territory_window_invalid"
    shape = _window_shape(window)
    if shape is None:
        return "territory_window_empty"
    if grid_shape is not None:
        depth, rows, cols = grid_shape
        _, z1, _, r1, _, c1 = window
        if z1 > depth or r1 > rows or c1 > cols:
            return "territory_window_outside_grid"
    roles = value.get("roles")
    if (
        not isinstance(roles, np.ndarray)
        or roles.dtype != np.int8
        or roles.shape != shape
    ):
        return "territory_roles_invalid"
    if not np.isin(roles, ROLE_CODES).all():
        return "territory_role_unknown"
    share = value.get("object_share")
    if not isinstance(share, np.ndarray) or share.shape != shape:
        return "territory_share_invalid"
    finite = np.isfinite(share)
    if np.any((share[finite] < 0) | (share[finite] > 1)):
        return "territory_share_out_of_range"
    if origin in MEASURED_ORIGINS:
        if not np.any(roles == ROLE_OBJECT):
            return "territory_measured_without_object_tiles"
        if not np.all(finite[roles == ROLE_OBJECT]):
            return "territory_measured_share_missing"
        if np.any(share[roles == ROLE_OBJECT] <= 0):
            return "territory_object_tile_without_support"
    support = value.get("native_support")
    if support is not None:
        if not isinstance(support, Mapping):
            return "territory_native_support_invalid"
        mask = support.get("mask")
        slices = support.get("slices")
        offset = support.get("offset_rc")
        if (
            not isinstance(mask, np.ndarray)
            or mask.dtype != np.bool_
            or mask.ndim != 3
            or not isinstance(slices, (list, tuple))
            or len(slices) != mask.shape[0]
            or any(type(item) is not int for item in slices)
            or _ints(offset, 2) is None
        ):
            return "territory_native_support_invalid"
    if not isinstance(value.get("provenance"), Mapping):
        return "territory_provenance_missing"
    return "valid"


def anchor_code(value: object) -> str:
    """``valid`` or the first named defect of an anchor."""
    if not isinstance(value, Mapping) or value.get("schema") != ANCHOR_SCHEMA:
        return "anchor_schema_invalid"
    if not _text(value.get("study_uid")) or not _text(value.get("subject")):
        return "anchor_identity_invalid"
    status = value.get("status")
    if status not in ANCHOR_STATUSES:
        return "anchor_status_invalid"
    territories = value.get("territories")
    if not isinstance(territories, list):
        return "anchor_territories_invalid"
    for territory in territories:
        if territory_code(territory) != "valid":
            return "anchor_territory_invalid"
    planes = value.get("key_planes")
    if not isinstance(planes, Mapping) or set(planes) - set(_ORIENTATIONS):
        return "anchor_key_planes_invalid"
    point = value.get("reference_lps")
    if point is not None and not (
        isinstance(point, (list, tuple))
        and len(point) == 3
        and all(isinstance(x, (int, float)) and math.isfinite(x) for x in point)
    ):
        return "anchor_reference_invalid"
    if status == "complete" and point is None:
        return "anchor_complete_without_reference"
    breadth = value.get("breadth_mm")
    if breadth is not None and (
        isinstance(breadth, bool)
        or not isinstance(breadth, (int, float))
        or not math.isfinite(breadth)
        or breadth <= 0
        or not _text(value.get("breadth_source"))
    ):
        return "anchor_breadth_invalid"
    if not _text(value.get("producer")) or not isinstance(value.get("cost"), Mapping):
        return "anchor_producer_or_cost_missing"
    return "valid"


def selection_code(value: object) -> str:
    """``valid`` or the first named defect of a question selection."""
    if not isinstance(value, Mapping) or value.get("schema") != SELECTION_SCHEMA:
        return "selection_schema_invalid"
    if not _text(value.get("question_id")) or not _text(value.get("version")):
        return "selection_identity_invalid"
    subjects = value.get("subjects")
    if (
        not isinstance(subjects, Mapping)
        or not subjects
        or any(not _text(name) for name in subjects)
        or any(role not in SUBJECT_ROLES for role in subjects.values())
    ):
        return "selection_subjects_invalid"
    cheap = value.get("cheap")
    if not isinstance(cheap, list):
        return "selection_cheap_invalid"
    for descriptor in cheap:
        if (
            not isinstance(descriptor, Mapping)
            or descriptor.get("subject") not in subjects
            or descriptor.get("role") not in ROLE_NAMES.values()
            or not isinstance(descriptor.get("metrics"), list)
            or not isinstance(descriptor.get("scales_mm"), list)
        ):
            return "selection_descriptor_invalid"
    if not isinstance(value.get("full_prefixes"), list):
        return "selection_full_prefixes_invalid"
    if not isinstance(value.get("unavailable"), list):
        return "selection_unavailable_invalid"
    return "valid"


def residual_request_code(value: object) -> str:
    """``valid`` or the first named defect of a residual request."""
    if not isinstance(value, Mapping) or value.get("schema") != RESIDUAL_REQUEST_SCHEMA:
        return "residual_request_schema_invalid"
    for key in ("question_id", "subject", "series_uid", "reason", "lens"):
        if not _text(value.get(key)):
            return "residual_request_field_invalid"
    window = _ints(value.get("tile_window"), 6)
    if window is None or _window_shape(window) is None:
        return "residual_request_window_invalid"
    return "valid"


def residual_result_code(value: object) -> str:
    """``valid`` or the first named defect of a residual result."""
    if not isinstance(value, Mapping) or value.get("schema") != RESIDUAL_RESULT_SCHEMA:
        return "residual_result_schema_invalid"
    code = value.get("code")
    if code not in RESIDUAL_CODES:
        return "residual_result_code_invalid"
    if not _text(value.get("subject")) or not _text(value.get("lens")):
        return "residual_result_identity_invalid"
    if not isinstance(value.get("cost"), Mapping):
        return "residual_result_cost_missing"
    if code == "measured":
        territory = value.get("territory")
        if not isinstance(territory, Mapping) or territory_code(territory) != "valid":
            return "residual_result_territory_invalid"
        if territory.get("origin") != "residual_native_support":
            return "residual_result_territory_origin_invalid"
        profile = value.get("profile")
        if not isinstance(profile, Mapping) or not isinstance(
            profile.get("banks"), Mapping
        ):
            return "residual_result_profile_invalid"
    return "valid"


def teaching_round_code(value: object) -> str:
    """``valid`` or the first named defect of a teaching-round manifest."""
    if not isinstance(value, Mapping) or value.get("schema") != TEACHING_ROUND_SCHEMA:
        return "teaching_round_schema_invalid"
    if value.get("status") not in TEACHING_STATUSES:
        return "teaching_round_status_invalid"
    parent = value.get("parent")
    if not isinstance(parent, Mapping) or not all(
        _text(parent.get(key)) for key in ("revision", "manifest_sha256")
    ):
        return "teaching_round_parent_invalid"
    calls = value.get("calls")
    if not isinstance(calls, list) or any(
        not isinstance(row, Mapping)
        or not _text(row.get("source"))
        or not _text(row.get("sha256"))
        for row in calls
    ):
        return "teaching_round_calls_invalid"
    if not isinstance(value.get("admission"), Mapping):
        return "teaching_round_admission_missing"
    child = value.get("child")
    if value["status"] in ("published", "evaluated") and not (
        isinstance(child, Mapping)
        and all(_text(child.get(key)) for key in ("revision", "manifest_sha256"))
        and child.get("revision") != parent.get("revision")
    ):
        return "teaching_round_child_invalid"
    return "valid"


__all__ = [
    "ANCHOR_SCHEMA",
    "ANCHOR_STATUSES",
    "LEG_CODES",
    "LEG_INSIDE",
    "LEG_MAP_SCHEMA",
    "LEG_MIXED",
    "LEG_OUTSIDE",
    "LEG_UNKNOWN",
    "MEASURED_ORIGINS",
    "MEMORY_VIEW_SCHEMA",
    "RESIDUAL_CODES",
    "RESIDUAL_REQUEST_SCHEMA",
    "RESIDUAL_RESULT_SCHEMA",
    "ROLE_CODES",
    "ROLE_CONTEXT",
    "ROLE_NAMES",
    "ROLE_OBJECT",
    "ROLE_OUTSIDE_LEG",
    "ROLE_UNQUERIED",
    "SELECTION_SCHEMA",
    "SUBJECT_ROLES",
    "TEACHING_ROUND_SCHEMA",
    "TEACHING_STATUSES",
    "TERRITORY_ORIGINS",
    "TERRITORY_PROCEDURE",
    "TERRITORY_SCHEMA",
    "anchor_code",
    "leg_map_code",
    "parse_territory_bank_name",
    "residual_request_code",
    "residual_result_code",
    "selection_code",
    "teaching_round_code",
    "territory_bank_name",
    "territory_code",
]
