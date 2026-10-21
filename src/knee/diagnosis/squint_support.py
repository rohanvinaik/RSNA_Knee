"""Resolve saved teacher supports and map their own places to squint tiles.

``support_mask`` follows the compiler's existing ordered address resolution.
Its mask is a two-dimensional, full native-frame boolean mask; its half-open
``bbox`` is only an address. ``teacher_territory`` keeps the actual mask crop
and offset, and reports native occupancy separately from each tile's role.
No scan, label, anatomical detector or calibration is recomputed here.
"""

from __future__ import annotations

import io
import lzma
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from knee.diagnosis.squint_interfaces import (
    LEG_OUTSIDE,
    ROLE_CONTEXT,
    ROLE_OBJECT,
    ROLE_OUTSIDE_LEG,
    TERRITORY_SCHEMA,
    leg_map_code,
    territory_code,
)


def _resolved(
    mask: np.ndarray, address: dict[str, Any], **provenance: Any
) -> dict[str, Any]:
    rows, cols = np.nonzero(mask)
    return {
        "code": "resolved",
        "mask": mask,
        "bbox": (
            int(rows.min()),
            int(rows.max()) + 1,
            int(cols.min()),
            int(cols.max()) + 1,
        ),
        "source_address": address,
        "provenance": provenance,
    }


def _coordinate_support(
    subject: str,
    series_uid: str,
    slice_index: int,
    entry: dict[str, Any],
    address: dict[str, Any],
    verified_arrays: Mapping[str, np.ndarray] | None,
) -> dict[str, Any] | None:
    # Keep the existing public-coordinate validation and named exceptions.
    # The bounding-box-only API cannot expose the selected member, so locate
    # that same first matching link after it has validated the whole entry.
    from knee.diagnosis.squint_memory import _coordinate_bbox

    bbox = _coordinate_bbox(
        subject, series_uid, slice_index, entry, address, verified_arrays
    )
    if bbox is None:
        return None
    assert verified_arrays is not None
    for link in entry["links"]:
        if not isinstance(link, dict) or link.get("coordinate_field") != "points_rc":
            continue
        member = link.get("coordinate_member")
        if not isinstance(member, str) or not member or member not in verified_arrays:
            continue
        metadata = link["metadata"]
        observation = metadata["observation"]
        if (
            link.get("profile_object") != subject
            or observation.get("series_uid") != series_uid
            or observation.get("slices") != [slice_index]
            or observation.get("support") != address.get("observation_support")
            or observation.get("view") != address.get("observation_view")
        ):
            continue
        shape = address.get("native_shape_rc")
        if shape is None:
            shape = metadata["native_shape_rc"]
        points = np.asarray(verified_arrays[member])
        mask = np.zeros(tuple(shape), dtype=np.bool_)
        mask[points[:, 0], points[:, 1]] = True
        return _resolved(
            mask,
            address,
            resolver="verified_public_coordinates",
            coordinate_member=member,
            place_count=link["place_count"],
        )
    return None


def support_mask(
    subject: str,
    series_uid: str,
    slice_index: int,
    support_ownership: dict[str, Any],
    source_roots: dict[str, Any],
    artifact_arrays: dict[Path, dict[str, np.ndarray]],
    verified_arrays: Mapping[str, np.ndarray] | None = None,
) -> dict[str, Any]:
    """Resolve the same first support as ``squint_memory._support_bbox``.

    Return ``code=resolved``, native ``mask``, half-open ``bbox``, original
    ``source_address`` and resolution provenance. If nothing resolves, return
    ``code=support_unavailable`` with no guessed mask/bounds. Invalid verified
    coordinates retain the compiler's existing named SquintMemoryError.
    ``artifact_arrays`` is the caller-owned per-study cache, as before.
    """
    owner = (
        support_ownership.get(subject) if isinstance(support_ownership, dict) else None
    )
    entries = owner.get("addressed_supports", []) if isinstance(owner, dict) else []
    candidates: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        address = entry.get("source_address")
        if not isinstance(address, dict):
            continue
        if address.get("target_series_uid") != series_uid:
            continue
        slices = address.get("observation_slices")
        if not isinstance(slices, list) or slice_index not in slices:
            continue
        if address.get("address_kind") != "native_rc":
            continue
        if address.get("geometry_status") != "available":
            continue
        candidates.append((entry, address))
    for entry, address in candidates:
        coordinates = _coordinate_support(
            subject, series_uid, slice_index, entry, address, verified_arrays
        )
        if coordinates is not None:
            return coordinates
        public_member_available = verified_arrays is not None and any(
            isinstance(link, dict)
            and link.get("coordinate_field") == "points_rc"
            and isinstance(link.get("coordinate_member"), str)
            and link.get("coordinate_member") in verified_arrays
            for link in entry.get("links", [])
        )
        if public_member_available:
            continue
        root_name = address.get("source_root")
        artifact = address.get("observation_artifact")
        if not isinstance(root_name, str) or not isinstance(artifact, str):
            continue
        source_root = source_roots.get(root_name)
        if not isinstance(source_root, str) or not source_root:
            continue
        root_path = Path(source_root).resolve()
        artifact_path = (root_path / artifact).resolve()
        try:
            artifact_path.relative_to(root_path)
        except ValueError:
            continue
        if not artifact_path.is_file():
            continue
        arrays = artifact_arrays.get(artifact_path)
        if arrays is None:
            try:
                raw = (
                    lzma.decompress(artifact_path.read_bytes())
                    if artifact_path.suffix == ".xz"
                    else artifact_path.read_bytes()
                )
                with np.load(io.BytesIO(raw), allow_pickle=False) as archive:
                    lineage = address.get("lineage")
                    support_array = (
                        lineage.get("support_array")
                        if isinstance(lineage, dict)
                        else None
                    )
                    support_name = address.get("observation_support")
                    desired = [
                        name
                        for name in (support_array, support_name, "a1_objects")
                        if isinstance(name, str) and name
                    ]
                    names = set(desired)
                    for name in desired:
                        names.add(f"{name}_slices")
                    names.update(
                        (
                            "a3_bone_plane_labels",
                            "a3_bone_plane_slices",
                            "a3_femur_plane_region",
                            "a3_femur_plane_slices",
                            "a3_tibia_plane_region",
                            "a3_tibia_plane_slices",
                        )
                    )
                    arrays = {
                        name: archive[name] for name in archive.files if name in names
                    }
            except (OSError, EOFError, lzma.LZMAError, ValueError):
                continue
            artifact_arrays[artifact_path] = arrays
        support_name = address.get("observation_support")
        lineage = address.get("lineage")
        support_array = (
            lineage.get("support_array") if isinstance(lineage, dict) else None
        )
        candidates_names: list[str] = []
        for name in (support_array, support_name, "a1_objects"):
            if (
                isinstance(name, str)
                and name in arrays
                and name not in candidates_names
            ):
                candidates_names.append(name)
        label = address.get("observation_label")
        for array_name in candidates_names:
            array = np.asarray(arrays[array_name])
            native_shape = address.get("native_shape_rc")
            if (
                not isinstance(native_shape, list)
                or len(native_shape) != 2
                or any(type(value) is not int or value <= 0 for value in native_shape)
            ):
                continue
            row = None
            if array.ndim == 3:
                slice_key = {
                    "a3_bone_plane_labels": "a3_bone_plane_slices",
                    "a3_femur_plane_region": "a3_femur_plane_slices",
                    "a3_tibia_plane_region": "a3_tibia_plane_slices",
                }.get(array_name, f"{array_name.removesuffix('_labels')}_slices")
                row = address.get("observation_row")
                if slice_key in arrays:
                    source_slices = np.asarray(arrays[slice_key]).reshape(-1)
                    choices = np.flatnonzero(source_slices == slice_index)
                    if (
                        choices.size != 1
                        or type(row) is not int
                        or row != int(choices[0])
                        or not 0 <= row < array.shape[0]
                    ):
                        continue
                elif type(row) is not int or not 0 <= row < array.shape[0]:
                    continue
                array = array[row]
            if array.ndim != 2 or array.shape != tuple(native_shape):
                continue
            mask = array == label if type(label) is int else array != 0
            if np.any(mask):
                return _resolved(
                    mask,
                    address,
                    resolver="native_artifact_array",
                    artifact_path=str(artifact_path),
                    support_array=array_name,
                    observation_row=row,
                    observation_label=label,
                )
    return {
        "code": "support_unavailable",
        "mask": None,
        "bbox": None,
        "source_address": None,
        "provenance": {
            "subject": subject,
            "series_uid": series_uid,
            "slice": slice_index,
        },
    }


def teacher_territory(
    study_uid: str,
    series: dict[str, Any],
    subject: str,
    mask_info: dict[str, Any],
    slice_index: int,
    leg_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map one native support to object tiles and a clipped spatial context ring.

    Success is a frozen-interface territory with ``code=resolved``. Refusals
    carry a specific ``code`` and the original mask_info in ``support``; they
    are not territories. Unknown/mixed leg tiles retain their measured roles.
    Only explicitly outside-leg tiles are suppressed, with occupancy retained.
    """

    def unavailable(code: str) -> dict[str, Any]:
        return {"code": code, "support": mask_info}

    if not isinstance(mask_info, dict) or mask_info.get("code") != "resolved":
        return unavailable("support_unavailable")
    if (
        not isinstance(study_uid, str)
        or not study_uid.strip()
        or not isinstance(subject, str)
        or not subject.strip()
        or not isinstance(series, dict)
        or not isinstance(series.get("series_uid"), str)
        or not series["series_uid"].strip()
    ):
        return unavailable("territory_identity_invalid")
    stack = series.get("stack")
    values = getattr(stack, "median", None)
    bounds = getattr(stack, "bounds_rc", None)
    shape = series.get("shape")
    if (
        not isinstance(values, np.ndarray)
        or values.ndim != 3
        or not isinstance(shape, (tuple, list))
        or len(shape) != 3
        or any(type(value) is not int or value <= 0 for value in shape)
        or values.shape[0] != shape[0]
        or not isinstance(bounds, np.ndarray)
        or bounds.shape != (*values.shape[1:], 4)
        or bounds.dtype.kind not in "iu"
    ):
        return unavailable("support_grid_unavailable")
    if type(slice_index) is not int or not 0 <= slice_index < shape[0]:
        return unavailable("support_slice_outside_series")
    mask = mask_info.get("mask")
    bbox = mask_info.get("bbox")
    address = mask_info.get("source_address")
    if (
        not isinstance(mask, np.ndarray)
        or mask.dtype != np.bool_
        or mask.ndim != 2
        or mask.shape != tuple(shape[1:])
        or not isinstance(bbox, (tuple, list))
        or len(bbox) != 4
        or any(type(value) is not int for value in bbox)
    ):
        return unavailable("support_mask_invalid")
    if (
        not isinstance(address, dict)
        or address.get("target_series_uid") != series["series_uid"]
        or not isinstance(address.get("observation_slices"), list)
        or slice_index not in address["observation_slices"]
    ):
        return unavailable("support_address_mismatch")
    if not np.any(mask):
        return unavailable("support_empty")
    r0, r1, c0, c1 = bbox
    if not (0 <= r0 < r1 <= shape[1] and 0 <= c0 < c1 <= shape[2]):
        return unavailable("support_bounds_invalid")
    rows, cols = np.nonzero(mask)
    if tuple(bbox) != (
        int(rows.min()),
        int(rows.max()) + 1,
        int(cols.min()),
        int(cols.max()) + 1,
    ):
        # A padded or stale box cannot certify support outside its claimed crop.
        return unavailable("support_bounds_mismatch")
    tr0, tr1, tc0, tc1 = np.moveaxis(bounds, -1, 0)
    if (
        np.any(tr0 < 0)
        or np.any(tc0 < 0)
        or np.any(tr1 > shape[1])
        or np.any(tc1 > shape[2])
        or np.any(tr0 >= tr1)
        or np.any(tc0 >= tc1)
    ):
        return unavailable("support_tile_bounds_invalid")
    overlaps = (tr0 < r1) & (r0 < tr1) & (tc0 < c1) & (c0 < tc1)
    tile_rows, tile_cols = np.nonzero(overlaps)
    if not tile_rows.size:
        return unavailable("support_outside_grid")
    wr0 = max(0, int(tile_rows.min()) - 1)
    wr1 = min(values.shape[1], int(tile_rows.max()) + 2)
    wc0 = max(0, int(tile_cols.min()) - 1)
    wc1 = min(values.shape[2], int(tile_cols.max()) + 2)
    window = [slice_index, slice_index + 1, wr0, wr1, wc0, wc1]
    roles = np.full((1, wr1 - wr0, wc1 - wc0), ROLE_CONTEXT, dtype=np.int8)
    share = np.zeros(roles.shape, dtype=np.float64)
    for rr in range(wr0, wr1):
        for cc in range(wc0, wc1):
            a, b, c, d = (int(value) for value in bounds[rr, cc])
            covered = int(np.count_nonzero(mask[a:b, c:d]))
            share[0, rr - wr0, cc - wc0] = covered / ((b - a) * (d - c))
            if covered:
                roles[0, rr - wr0, cc - wc0] = ROLE_OBJECT
    if leg_map is not None:
        code = leg_map_code(leg_map, grid_shape=values.shape)
        if code != "valid":
            return unavailable(code)
        if (
            leg_map["series_uid"] != series["series_uid"]
            or leg_map.get("study_uid", study_uid) != study_uid
            or leg_map["tile_mm"] != getattr(stack, "tile_mm", None)
        ):
            return unavailable("support_leg_map_identity_mismatch")
        outside = (
            leg_map["codes"][slice_index : slice_index + 1, wr0:wr1, wc0:wc1]
            == LEG_OUTSIDE
        )
        roles[outside] = ROLE_OUTSIDE_LEG
    if not np.any(roles == ROLE_OBJECT):
        return unavailable("support_outside_leg")
    orientation = series.get("view", {}).get("orientation", "unknown").lower()
    result = {
        "schema": TERRITORY_SCHEMA,
        "code": "resolved",
        "study_uid": study_uid,
        "series_uid": series["series_uid"],
        "subject": subject,
        "origin": "teacher_support",
        "tile_window": window,
        "roles": roles,
        "object_share": share,
        "native_support": {
            "mask": mask[np.newaxis, r0:r1, c0:c1],
            "slices": [slice_index],
            "offset_rc": [r0, c0],
        },
        "anchors": [],
        "relation": None,
        "key_planes": {
            orientation: {
                "series_uid": series["series_uid"],
                "slice": slice_index,
                "outcome": "selected",
            }
        },
        "provenance": {
            "source_address": address,
            "support_resolution": mask_info.get("provenance", {}),
            "native_bounds_rc": list(bbox),
            "context_ring_tiles": 1,
            "leg_map_rule": leg_map["rule"] if leg_map is not None else None,
        },
    }
    code = territory_code(result, grid_shape=values.shape)
    return result if code == "valid" else unavailable(code)
