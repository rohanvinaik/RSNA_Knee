"""A useful leg prior on the existing squint grid, without reading anatomy again.

The series' own background split and tile medians locate border-connected air.
Flooding is four-connected within each slice: a dark body enclosed by tissue
stays leg even on the first/last acquired slice. Straddling tiles on that
exterior are mixed; tile summaries do not measure their native occupancy.

Fat suppression can hide subcutaneous fat. Where available, non-FS leg maps
are carried by patient-space tile centres, within the source's measured field
and half-spacing end slabs. Same-plane sources are used first; other planes
cover their missing field. Speaking sources must concur, never vote. These
are location priors, not registered skin contours. The original local codes,
split, source identities and projection outcomes remain in each result.

Consumers call ``leg_maps`` once per loaded study and share the returned maps.
An already measured split may be supplied as ``series['background_split']``
(finite float, or NaN/None for no split); otherwise the retained native volume
feeds the existing ``background_split(finite_values(volume))`` unchanged.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
from scipy import ndimage

from knee.collapse.noise import background_split, finite_values
from knee.collapse.physical import PlaneFrame
from knee.collapse.squint_stack import SquintStack
from knee.diagnosis.squint_interfaces import (
    LEG_INSIDE,
    LEG_MAP_SCHEMA,
    LEG_MIXED,
    LEG_OUTSIDE,
    LEG_UNKNOWN,
)

_LOCAL_RULE = "series_background_split_border_flood_4_connected/v2"
_CARRY_RULE = "non_fat_suppressed_physical_tile_centres/v1"
_COUNTS = {
    "inside": LEG_INSIDE,
    "outside": LEG_OUTSIDE,
    "mixed": LEG_MIXED,
    "unknown": LEG_UNKNOWN,
}


def _counts(codes: np.ndarray) -> dict[str, int]:
    return {
        name: int(np.count_nonzero(codes == code)) for name, code in _COUNTS.items()
    }


def _split(series: Mapping) -> tuple[float, dict]:
    if "background_split" in series:
        value = series["background_split"]
        if value is None:
            value = float("nan")
        if isinstance(value, (bool, np.bool_)) or not isinstance(
            value, (int, float, np.integer, np.floating)
        ):
            raise ValueError("leg_background_split_invalid")
        split = float(value)
        return split, {
            "code": "measured" if np.isfinite(split) else "no_background_split",
            "source": "supplied_series_background_split",
            "value": split if np.isfinite(split) else None,
        }
    native = series.get("native_series")
    volume = getattr(native, "volume", None)
    if volume is None:
        return float("nan"), {
            "code": "native_volume_unavailable",
            "source": "native_series.volume",
            "value": None,
        }
    values = finite_values(volume)
    split = background_split(values)
    return split, {
        "code": "measured" if np.isfinite(split) else "no_background_split",
        "source": "knee.collapse.noise.background_split",
        "value": split if np.isfinite(split) else None,
        "finite_count": int(values.size),
        "bins": 512,
        "smooth": 5,
    }


def _available(stack: SquintStack) -> np.ndarray:
    arrays = (stack.minimum, stack.median, stack.maximum, stack.coverage)
    if any(
        not isinstance(a, np.ndarray) or a.shape != stack.median.shape for a in arrays
    ):
        raise ValueError("leg_tile_array_shape_invalid")
    return (
        np.isfinite(stack.coverage)
        & (stack.coverage > 0)
        & (stack.coverage <= 1)
        & np.isfinite(stack.minimum)
        & np.isfinite(stack.median)
        & np.isfinite(stack.maximum)
        & (stack.minimum <= stack.median)
        & (stack.median <= stack.maximum)
    )


def _local_map(study_uid: str, series: Mapping) -> dict:
    stack = series.get("stack")
    if not isinstance(stack, SquintStack) or stack.median.ndim != 3:
        raise ValueError("leg_squint_stack_required")
    codes = np.full(stack.median.shape, LEG_UNKNOWN, dtype=np.int8)
    provenance = {"series_source": dict(series.get("source", {}))}
    code = stack.code
    if code == "present" and codes.size:
        available = _available(stack)
        split, measurement = _split(series)
        provenance["background_split"] = measurement
        code = measurement["code"]
        if np.isfinite(split):
            dark = available & (stack.median <= split)
            border = np.zeros(codes.shape, dtype=bool)
            border[:, 0, :] = border[:, -1, :] = True
            border[:, :, 0] = border[:, :, -1] = True
            # No z-neighbours: every acquired slice has its own exterior.
            structure = np.zeros((3, 3, 3), dtype=bool)
            structure[1] = ndimage.generate_binary_structure(2, 1)
            outside = ndimage.binary_propagation(
                border & dark, structure=structure, mask=dark
            )
            edge = border | ndimage.binary_dilation(outside, structure=structure)
            mixed = available & ~outside & (stack.minimum <= split) & edge
            codes[available] = LEG_INSIDE
            codes[outside] = LEG_OUTSIDE
            codes[mixed] = LEG_MIXED
            code = "measured"
    elif code == "present":
        code = "no_tiles"
    provenance.update(
        {
            "code": code,
            "construction": "series_own_split",
            "connectivity": "four_connected_per_slice",
            "dark_rule": "median_at_or_below_background_split",
            "mixed_rule": "not_outside_minimum_at_or_below_split_and_touches_border_or_outside_tile",
            "leg_share_policy": "categorical_only_mixed_and_unknown_nan",
            "local_counts": _counts(codes),
        }
    )
    return {
        "schema": LEG_MAP_SCHEMA,
        "study_uid": study_uid,
        "series_uid": series["series_uid"],
        "tile_mm": float(stack.tile_mm),
        "code": code,
        "codes": codes,
        "rule": _LOCAL_RULE,
        "provenance": provenance,
    }


def _source_geometry(
    series: Mapping,
) -> tuple[list[PlaneFrame], np.ndarray, np.ndarray, str]:
    """Source slice cells bounded by inter-plane midpoints, no extrapolated field."""
    geometry = series.get("geometry")
    depth = series["stack"].median.shape[0]
    nothing = ([], np.empty(0), np.empty(0, dtype=int))
    if not isinstance(geometry, Mapping) or depth < 2:
        return *nothing, "source_depth_or_geometry_unavailable"
    try:
        frames = [
            PlaneFrame.from_dicom(
                geometry["position"][z],
                geometry["orientation"][z],
                geometry["spacing"][z],
            )
            for z in range(depth)
        ]
    except (KeyError, IndexError, TypeError, ValueError):
        return *nothing, "source_geometry_invalid"
    normal = frames[0].normal()
    if any(not np.allclose(f.normal(), normal, rtol=0, atol=1e-4) for f in frames):
        return *nothing, "source_planes_not_parallel"
    positions = np.array([f.origin_lps @ normal for f in frames])
    order = np.argsort(positions, kind="stable")
    positions = positions[order]
    steps = np.diff(positions)
    if np.any(steps <= 0):
        return *nothing, "source_slice_positions_repeated"
    edges = np.concatenate(
        (
            [positions[0] - steps[0] / 2],
            (positions[:-1] + positions[1:]) / 2,
            [positions[-1] + steps[-1] / 2],
        )
    )
    return frames, edges, order, "available"


def _project(
    target: Mapping, source: Mapping, source_map: dict, geometry: tuple
) -> tuple:
    """Read the source cell containing each target centre, within its actual field."""
    target_stack, source_stack = target["stack"], source["stack"]
    shape = target_stack.median.shape
    result = np.full(shape, LEG_UNKNOWN, dtype=np.int8)
    covered = np.zeros(shape, dtype=bool)
    frames, edges, order, status = geometry
    centres = target_stack.centres_lps
    if status != "available":
        return result, covered, status
    if not isinstance(centres, np.ndarray) or centres.shape != (*shape, 3):
        return result, covered, "target_centres_unavailable"
    flat = centres.reshape(-1, 3)
    finite = np.isfinite(flat).all(axis=1)
    candidates = np.flatnonzero(finite)
    depths = flat[finite] @ frames[0].normal()
    in_depth = (depths >= edges[0]) & (depths < edges[-1])
    candidates, depths = candidates[in_depth], depths[in_depth]
    slice_indices = order[np.searchsorted(edges[1:-1], depths, side="right")]
    bounds = source_stack.bounds_rc
    for z in np.unique(slice_indices):
        indices = candidates[slice_indices == z]
        rc = frames[z].to_native(flat[indices])
        # Pixel centres occupy cells [-.5, n-.5); tile cells inherit those edges.
        row = np.searchsorted(bounds[:, 0, 1] - 0.5, rc[:, 0], side="right")
        col = np.searchsorted(bounds[0, :, 3] - 0.5, rc[:, 1], side="right")
        held = (
            (rc[:, 0] >= bounds[0, 0, 0] - 0.5)
            & (rc[:, 1] >= bounds[0, 0, 2] - 0.5)
            & (row < bounds.shape[0])
            & (col < bounds.shape[1])
        )
        indices = indices[held]
        result.flat[indices] = source_map["codes"][z, row[held], col[held]]
        covered.flat[indices] = True
    return result, covered, "projected"


def _carry(target: Mapping, result: dict, sources: list, geometries: dict) -> None:
    own = result["codes"]
    combined = own.copy()
    unfilled = _available(target["stack"])
    target_plane = target.get("view", {}).get("orientation")
    projections = []
    conflicts = 0
    carried = np.zeros(own.shape, dtype=bool)
    for same_plane in (True, False):
        inside = np.zeros(own.shape, dtype=bool)
        outside = np.zeros(own.shape, dtype=bool)
        mixed = np.zeros(own.shape, dtype=bool)
        covered_any = np.zeros(own.shape, dtype=bool)
        for source, source_map in sources:
            if (
                source.get("view", {}).get("orientation") == target_plane
            ) != same_plane:
                continue
            projected, covered, code = _project(
                target, source, source_map, geometries[source["series_uid"]]
            )
            covered &= unfilled
            projections.append(
                {
                    "series_uid": source["series_uid"],
                    "code": code,
                    "same_plane": same_plane,
                    "covered_tiles": int(covered.sum()),
                    "counts": _counts(projected[covered]),
                }
            )
            covered_any |= covered
            inside |= covered & (projected == LEG_INSIDE)
            outside |= covered & (projected == LEG_OUTSIDE)
            mixed |= covered & (projected == LEG_MIXED)
        combined[covered_any] = LEG_UNKNOWN
        conflict = inside & outside
        combined[inside & ~outside & ~mixed] = LEG_INSIDE
        combined[outside & ~inside & ~mixed] = LEG_OUTSIDE
        combined[mixed & ~conflict] = LEG_MIXED
        conflicts += int(conflict.sum())
        carried |= covered_any
        unfilled &= ~covered_any
    result["local_codes"] = own
    result["codes"] = combined
    if carried.any():
        result["rule"] = _CARRY_RULE
        result["provenance"]["construction"] = (
            "non_fs_physical_carry_with_local_fallback"
        )
    result["provenance"].update(
        {
            "carry_reason": "fat_suppression_can_hide_subcutaneous_fat",
            "projection_rule": "target_centre_in_source_tile_and_half_spacing_slice_cell",
            "projection_sources": projections,
            "carried_tiles": int(carried.sum()),
            "local_fallback_tiles": int(unfilled.sum()),
            "conflicting_source_tiles": conflicts,
            "conflict_code": "source_maps_disagree"
            if conflicts
            else "no_source_conflict",
            "source_preference": "same_plane_then_other_planes_in_uncovered_field",
        }
    )


def leg_maps(study: object) -> dict[str, dict]:
    """One frozen, interface-valid leg map for each series of a loaded study.

    No coverage and no split are unknown, never outside. A series without a
    split remains entirely unknown even if another series could be projected.
    The input study and its measurements are not modified.
    """
    if not isinstance(study, dict) or not isinstance(
        study.get("series"), (list, tuple)
    ):
        raise TypeError("leg_study_invalid")
    records = study["series"]
    maps = {}
    for record in records:
        if (
            not isinstance(record, Mapping)
            or not isinstance(record.get("series_uid"), str)
            or not record["series_uid"]
        ):
            raise ValueError("leg_series_identity_invalid")
        uid = record["series_uid"]
        if uid in maps:
            raise ValueError("leg_series_identity_repeated")
        maps[uid] = _local_map(study.get("study_uid", ""), record)
    sources = [
        (r, maps[r["series_uid"]])
        for r in records
        if r.get("view", {}).get("fat_suppression") == "0"
        and maps[r["series_uid"]]["code"] == "measured"
    ]
    geometries = {r["series_uid"]: _source_geometry(r) for r, _ in sources}
    for record in records:
        result = maps[record["series_uid"]]
        if (
            record.get("view", {}).get("fat_suppression") == "1"
            and result["code"] == "measured"
            and sources
        ):
            _carry(record, result, sources, geometries)
        codes = result["codes"]
        share = np.full(codes.shape, np.nan, dtype=np.float32)
        share[codes == LEG_INSIDE] = 1
        share[codes == LEG_OUTSIDE] = 0
        result["leg_share"] = share
        result["counts"] = _counts(codes)
        for name in ("codes", "local_codes", "leg_share"):
            if name in result:
                result[name].flags.writeable = False
    return maps


__all__ = ["leg_maps"]
