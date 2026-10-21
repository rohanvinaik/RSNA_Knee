"""Check each located object against its own study's bootstrap support.

The position agency is taught against full resolutions and measured within
tolerance or not (*What an <Object> Is* §11.1). Here the full resolution is the
bootstrap: each labelled study's own high-resolution object supports, kept in
the memory as its object cases' ``regions``. For every region a squint run
located, this module takes the same study's own case for that object, finds
its region in the same series, and asks four things:

(a) the centre of the located object tiles lies inside the support's tile box
    (the case region's ``source_window``, half-open);
(b) the located slice lies within ``SLICE_TOLERANCE`` slices of the support's
    key slice;
(c) both;
(d) where the run record carries a territory, the share of the support's own
    native pixels that the territory's object tiles cover.

A located region without a territory claims every tile of its window, so its
object tiles are the window's tiles. With a territory only its object-role
tiles are the object: a box is an address, not an object.

The yardstick is the study's own *native support*: a case region whose
``extent_source`` is ``retained_object_support``. A case region that kept
only the object's physical reference point (``retained_physical_location``,
one tile at the point) is not a support. It is judged under its own heading
and never enters a support hit or miss. A located region whose study has no
own case for the object, or whose case has no region in that series, is
unknown and counted apart, never as a miss or a hit.

Labels are never read. From a case this module reads only ``case_id``,
``study_uid``, ``subject``, ``regions`` and the product address in
``full_source``; from a run record only the study identity and each object's
``status`` and ``regions``.
"""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

import numpy as np

from knee.diagnosis.squint_interfaces import ROLE_CODES, ROLE_OBJECT, territory_code

SCHEMA = "knee.squint-location-check/v1"
#: The job's tolerance: the located slice within 2 slices of the key slice.
SLICE_TOLERANCE = 2

NATIVE_SUPPORT = "native_support"
PHYSICAL_LOCATION = "physical_location_only"
REFERENCE_KINDS = (NATIVE_SUPPORT, PHYSICAL_LOCATION)
_EXTENT_KINDS = {
    "retained_object_support": NATIVE_SUPPORT,
    "retained_physical_location": PHYSICAL_LOCATION,
}
_COVERAGE_FIELDS = ("share_on_key_slice", "share_in_plane")


def _window(value: object) -> tuple[int, int, int, int, int, int] | None:
    """A half-open tile window ``z0,z1,r0,r1,c0,c1`` of plain ints, else None."""
    if (
        isinstance(value, (list, tuple))
        and len(value) == 6
        and all(type(item) is int for item in value)
    ):
        z0, z1, r0, r1, c0, c1 = value
        if 0 <= z0 < z1 and 0 <= r0 < r1 and 0 <= c0 < c1:
            return (z0, z1, r0, r1, c0, c1)
    return None


def view_key(view: object) -> str:
    """``orientation/fluid_sensitive/fat_suppression`` of a view, or ``unknown``."""
    if isinstance(view, Mapping):
        parts = [
            part
            for part in (
                view.get(key)
                for key in ("orientation", "fluid_sensitive", "fat_suppression")
            )
            if isinstance(part, str) and part
        ]
        if len(parts) == 3:
            return "/".join(parts)
    return "unknown"


def _reference(region: Mapping[str, Any], case_id: object) -> dict[str, Any]:
    """One own case region as a reference, with a named code when unusable."""
    kind = _EXTENT_KINDS.get(region.get("extent_source"))
    window = _window(region.get("source_window"))
    source_slice = region.get("source_slice")
    code = "valid"
    if kind is None:
        code = "own_region_extent_unrecognized"
    elif window is None:
        code = "own_region_window_invalid"
    elif type(source_slice) is int and source_slice != window[0]:
        code = "own_region_slice_mismatch"
    return {
        "code": code,
        "kind": kind,
        "case_id": case_id,
        "window": None if window is None else list(window),
        "key_slice": None if window is None else window[0],
        "extent_source": region.get("extent_source"),
        "support_code": region.get("support_code"),
        "native_bounds_rc": region.get("native_bounds_rc"),
        "view": region.get("view"),
    }


def own_references(
    cases: Iterable[Mapping[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    """Index every case's own regions by ``(study_uid, subject)`` and series.

    Only cases that kept regions contribute; configuration cases keep none.
    Label-bearing fields (condition calls, attribution, scope) are not read.
    """
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for case in cases:
        regions = case.get("regions")
        study_uid = case.get("study_uid")
        subject = case.get("subject")
        if not isinstance(regions, list) or not regions:
            continue
        if not isinstance(study_uid, str) or not isinstance(subject, str):
            continue
        case_id = case.get("case_id")
        entry = index.setdefault(
            (study_uid, subject), {"case_ids": [], "series": {}, "full_sources": {}}
        )
        entry["case_ids"].append(case_id)
        source = case.get("full_source")
        if isinstance(source, Mapping):
            entry["full_sources"][str(case_id)] = {
                key: source.get(key) for key in ("product_path", "product_sha256")
            }
        for region in regions:
            if not isinstance(region, Mapping):
                continue
            series_uid = region.get("series_uid")
            if isinstance(series_uid, str) and series_uid:
                entry["series"].setdefault(series_uid, []).append(
                    _reference(region, case_id)
                )
    return index


def located_rows(record: Mapping[str, Any]) -> tuple[list[dict[str, Any]], Counter]:
    """One row per located region of one study record, and the unlocated statuses.

    The located address follows the production rule
    ``region.get("window", region.get("source_window"))``; a region carrying a
    territory may give its address as the territory's ``tile_window``.
    """
    study_uid = record.get("study_uid")
    objects = record.get("objects")
    rows: list[dict[str, Any]] = []
    unlocated: Counter = Counter()
    if not isinstance(objects, Mapping):
        return rows, unlocated
    for subject in sorted(objects):
        entry = objects[subject]
        if not isinstance(entry, Mapping):
            unlocated[(subject, "object_record_invalid")] += 1
            continue
        status = entry.get("status")
        regions = entry.get("regions")
        if not isinstance(regions, list) or not regions:
            unlocated[(subject, str(status))] += 1
            continue
        in_series = Counter(
            region.get("series_uid")
            for region in regions
            if isinstance(region, Mapping)
        )
        for index, region in enumerate(regions):
            row: dict[str, Any] = {
                "study_uid": study_uid,
                "subject": subject,
                "status": status,
                "region_index": index,
            }
            if not isinstance(region, Mapping):
                row.update(
                    {
                        "series_uid": None,
                        "view": "unknown",
                        "located_code": "located_region_invalid",
                    }
                )
                rows.append(row)
                continue
            territory = region.get("territory")
            if "window" in region:
                address, address_key = region.get("window"), "window"
            elif "source_window" in region:
                address, address_key = region.get("source_window"), "source_window"
            elif isinstance(territory, Mapping):
                address, address_key = (
                    territory.get("tile_window"),
                    "territory.tile_window",
                )
            else:
                address, address_key = None, None
            row.update(
                {
                    "series_uid": region.get("series_uid"),
                    "view": view_key(region.get("view")),
                    "located_window": address,
                    "located_window_key": address_key,
                    "regions_in_series": in_series[region.get("series_uid")],
                    "territory": territory,
                }
            )
            rows.append(row)
    return rows, unlocated


def territory_runtime(value: object) -> tuple[dict[str, Any] | None, str]:
    """A recorded territory in the frozen runtime shape, or its named defect.

    A record is JSON: roles and shares arrive as nested lists, an unmeasured
    share as null, and the runtime-only native support at most as a summary.
    Only that representation changes here; the frozen validator then reads it.
    """
    if not isinstance(value, Mapping):
        return None, "territory_not_mapping"
    try:
        roles = np.asarray(value.get("roles"))
        share = np.asarray(value.get("object_share"), dtype=np.float64)
    except (TypeError, ValueError):
        return None, "territory_arrays_invalid"
    if roles.dtype.kind not in "iu" or roles.ndim != 3:
        return None, "territory_roles_invalid"
    if not np.isin(roles, ROLE_CODES).all():
        return None, "territory_role_unknown"
    runtime = dict(value)
    runtime["roles"] = roles.astype(np.int8)
    runtime["object_share"] = share
    native = value.get("native_support")
    if isinstance(native, Mapping) and not isinstance(native.get("mask"), np.ndarray):
        runtime["native_support"] = None
    code = territory_code(runtime)
    return (runtime if code == "valid" else None), code


def located_object_tiles(row: Mapping[str, Any]) -> dict[str, Any]:
    """The located object's tiles, centre and slice, or a named defect."""
    territory = row.get("territory")
    if territory is None:
        window = _window(row.get("located_window"))
        if row.get("located_window") is None:
            return {"code": "located_window_missing"}
        if window is None:
            return {"code": "located_window_invalid"}
        z0, z1, r0, r1, c0, c1 = window
        return {
            "code": "ok",
            "source": "window_without_territory",
            "centre_rc": [(r0 + r1) / 2, (c0 + c1) / 2],
            "slice": z0 if z1 - z0 == 1 else (z0 + z1 - 1) / 2,
            "box_rc": [r0, r1, c0, c1],
            "tile_count": (z1 - z0) * (r1 - r0) * (c1 - c0),
            "tiles": None,
        }
    runtime, code = territory_runtime(territory)
    if runtime is None:
        return {"code": f"territory_invalid:{code}"}
    if (
        runtime.get("study_uid") != row.get("study_uid")
        or runtime.get("series_uid") != row.get("series_uid")
        or runtime.get("subject") != row.get("subject")
    ):
        return {"code": "territory_identity_mismatch"}
    z0, _z1, r0, _r1, c0, _c1 = runtime["tile_window"]
    local = np.argwhere(runtime["roles"] == ROLE_OBJECT)
    if local.size == 0:
        return {"code": "territory_without_object_tiles"}
    tiles = local + np.asarray([z0, r0, c0], dtype=np.int64)
    slices = sorted({int(z) for z in tiles[:, 0]})
    return {
        "code": "ok",
        "source": "territory_object_role",
        "origin": runtime.get("origin"),
        "centre_rc": [float(tiles[:, 1].mean() + 0.5), float(tiles[:, 2].mean() + 0.5)],
        "slice": slices[0] if len(slices) == 1 else float(tiles[:, 0].mean()),
        "box_rc": [
            int(tiles[:, 1].min()),
            int(tiles[:, 1].max()) + 1,
            int(tiles[:, 2].min()),
            int(tiles[:, 2].max()) + 1,
        ],
        "tile_count": int(tiles.shape[0]),
        "tiles": tiles,
        "window_matches_territory": row.get("located_window")
        == list(runtime["tile_window"]),
    }


def judge(tiles: Mapping[str, Any], reference: Mapping[str, Any]) -> dict[str, Any]:
    """(a), (b) and (c) for one located object against one own reference."""
    _z0, _z1, r0, r1, c0, c1 = reference["window"]
    centre_r, centre_c = tiles["centre_rc"]
    inside = bool(r0 <= centre_r < r1 and c0 <= centre_c < c1)
    offset = abs(tiles["slice"] - reference["key_slice"])
    within = bool(offset <= SLICE_TOLERANCE)
    lr0, lr1, lc0, lc1 = tiles["box_rc"]
    rows = max(0, min(lr1, r1) - max(lr0, r0))
    cols = max(0, min(lc1, c1) - max(lc0, c0))
    intersection = rows * cols
    union = (lr1 - lr0) * (lc1 - lc0) + (r1 - r0) * (c1 - c0) - intersection
    return {
        "centre_inside_support_box": inside,
        "slice_offset": offset,
        "within_slice_tolerance": within,
        "on_target": inside and within,
        "in_plane_overlap": intersection > 0,
        "in_plane_iou": intersection / union,
    }


def support_coverage(
    tiles: np.ndarray,
    key_slice: int,
    support_mask: np.ndarray,
    bounds_rc: np.ndarray,
) -> dict[str, Any]:
    """(d): the share of the support's own native pixels the object tiles cover.

    ``tiles`` holds absolute ``(z, r, c)`` object tiles, ``support_mask`` the
    support's full native frame on its key slice and ``bounds_rc`` the series'
    half-open native bounds of every 10 mm tile. On the key slice only tiles of
    that slice cover; in plane every object tile covers whatever its slice.
    """
    mask = np.asarray(support_mask)
    bounds = np.asarray(bounds_rc)
    if mask.dtype != np.bool_ or mask.ndim != 2:
        return {"code": "support_mask_invalid"}
    if bounds.ndim != 3 or bounds.shape[2] != 4 or bounds.dtype.kind not in "iu":
        return {"code": "tile_bounds_invalid"}
    tiles = np.asarray(tiles)
    if tiles.ndim != 2 or tiles.shape[1] != 3 or tiles.dtype.kind not in "iu":
        return {"code": "object_tiles_invalid"}
    if (
        np.any(tiles[:, 1:] < 0)
        or np.any(tiles[:, 1] >= bounds.shape[0])
        or np.any(tiles[:, 2] >= bounds.shape[1])
    ):
        return {"code": "object_tiles_outside_grid"}
    if bounds.size and (
        bounds[..., 1].max() > mask.shape[0] or bounds[..., 3].max() > mask.shape[1]
    ):
        return {"code": "support_frame_mismatch"}
    total = int(np.count_nonzero(mask))
    if total == 0:
        return {"code": "support_empty"}
    on_key = np.zeros(mask.shape, dtype=np.bool_)
    in_plane = np.zeros(mask.shape, dtype=np.bool_)
    for z, r, c in tiles:
        r0, r1, c0, c1 = (int(value) for value in bounds[r, c])
        in_plane[r0:r1, c0:c1] = True
        if int(z) == key_slice:
            on_key[r0:r1, c0:c1] = True
    covered_key = int(np.count_nonzero(mask & on_key))
    covered_plane = int(np.count_nonzero(mask & in_plane))
    return {
        "code": "measured",
        "support_pixels": total,
        "covered_on_key_slice": covered_key,
        "share_on_key_slice": covered_key / total,
        "covered_in_plane": covered_plane,
        "share_in_plane": covered_plane / total,
    }


#: (d) supplier: ``coverage(row, reference, tiles) -> support_coverage result``.
Coverage = Callable[[Mapping[str, Any], Mapping[str, Any], np.ndarray], dict[str, Any]]


def check_row(
    row: Mapping[str, Any],
    references: Mapping[tuple[str, str], Mapping[str, Any]],
    coverage: Coverage | None = None,
) -> dict[str, Any]:
    """One located row with its located tiles and every judged own reference.

    ``coverage`` measures (d) for a territory against a native support; without
    it, such a pair records ``coverage_not_requested`` rather than a share.
    """
    result: dict[str, Any] = {
        key: row.get(key)
        for key in (
            "study_uid",
            "subject",
            "status",
            "region_index",
            "series_uid",
            "view",
            "located_window",
            "located_window_key",
            "regions_in_series",
        )
    }
    if row.get("located_code") is not None:
        result.update({"located_code": row["located_code"], "pairs": []})
        return result
    tiles = located_object_tiles(row)
    result["located_code"] = tiles["code"]
    result["located"] = {key: value for key, value in tiles.items() if key != "tiles"}
    result["pairs"] = []
    if tiles["code"] != "ok":
        return result
    own = references.get((row.get("study_uid"), row.get("subject")))
    if own is None:
        result["reference_code"] = "no_own_case"
        return result
    candidates = own["series"].get(row.get("series_uid"), [])
    usable = [reference for reference in candidates if reference["code"] == "valid"]
    if not usable:
        result["reference_code"] = (
            candidates[0]["code"] if candidates else "no_own_region_in_series"
        )
        return result
    result["reference_code"] = "judged"
    for reference in usable:
        pair = {
            "reference": {
                key: reference[key]
                for key in (
                    "kind",
                    "case_id",
                    "window",
                    "key_slice",
                    "support_code",
                    "native_bounds_rc",
                )
            },
            "judgment": judge(tiles, reference),
        }
        if tiles["tiles"] is not None and reference["kind"] == NATIVE_SUPPORT:
            pair["coverage"] = (
                {"code": "coverage_not_requested"}
                if coverage is None
                else coverage(row, reference, tiles["tiles"])
            )
        result["pairs"].append(pair)
    return result


def unlocated_supports(
    study_uid: str,
    checked: Sequence[Mapping[str, Any]],
    unlocated: Counter,
    references: Mapping[tuple[str, str], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Own native supports of one study in series where nothing was located."""
    located_series = {
        (row.get("subject"), row.get("series_uid"))
        for row in checked
        if row.get("located_code") == "ok"
    }
    located_subjects = {subject for subject, _series in located_series}
    subjects_with_regions = {row.get("subject") for row in checked}
    statuses = {subject: status for subject, status in unlocated}
    missing: list[dict[str, Any]] = []
    for (case_study, subject), own in sorted(references.items()):
        if case_study != study_uid:
            continue
        for series_uid, candidates in sorted(own["series"].items()):
            for reference in candidates:
                if reference["code"] != "valid" or reference["kind"] != NATIVE_SUPPORT:
                    continue
                if (subject, series_uid) in located_series:
                    continue
                missing.append(
                    {
                        "study_uid": study_uid,
                        "subject": subject,
                        "series_uid": series_uid,
                        "view": view_key(reference.get("view")),
                        "object_state": "located_in_other_series"
                        if subject in located_subjects
                        else "located_regions_unusable"
                        if subject in subjects_with_regions
                        else f"not_located:{statuses.get(subject, 'absent_from_record')}",
                    }
                )
    return missing


def _median(values: Sequence[float]) -> float | None:
    return statistics.median(values) if values else None


def _kind_summary(pairs: Sequence[Mapping[str, Any]], kind: str) -> dict[str, Any]:
    judged = [pair for pair in pairs if pair["reference"]["kind"] == kind]
    judgments = [pair["judgment"] for pair in judged]
    summary: dict[str, Any] = {
        "pairs": len(judgments),
        "centre_inside_support_box": sum(
            j["centre_inside_support_box"] for j in judgments
        ),
        "within_slice_tolerance": sum(j["within_slice_tolerance"] for j in judgments),
        "on_target": sum(j["on_target"] for j in judgments),
        "in_plane_overlap": sum(j["in_plane_overlap"] for j in judgments),
        "median_in_plane_iou": _median([j["in_plane_iou"] for j in judgments]),
        "median_slice_offset": _median([j["slice_offset"] for j in judgments]),
    }
    if kind == NATIVE_SUPPORT:
        codes: Counter = Counter()
        shares: dict[str, list[float]] = {field: [] for field in _COVERAGE_FIELDS}
        for pair in judged:
            coverage = pair.get("coverage")
            if coverage is None:
                codes["no_territory"] += 1
                continue
            codes[coverage["code"]] += 1
            if coverage["code"] == "measured":
                for field in _COVERAGE_FIELDS:
                    shares[field].append(coverage[field])
        summary["territory_coverage"] = {
            "codes": dict(sorted(codes.items())),
            "measured": len(shares["share_on_key_slice"]),
            **{f"median_{field}": _median(shares[field]) for field in _COVERAGE_FIELDS},
        }
    return summary


def _group_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    located_defects: Counter = Counter()
    unknown: Counter = Counter()
    pairs: list[Mapping[str, Any]] = []
    for row in rows:
        if row.get("located_code") != "ok":
            located_defects[str(row.get("located_code"))] += 1
            continue
        if row.get("reference_code") != "judged":
            unknown[str(row.get("reference_code"))] += 1
            continue
        pairs.extend(row["pairs"])
    return {
        "located_regions": len(rows),
        "located_defects": dict(sorted(located_defects.items())),
        "unknown_reference": dict(sorted(unknown.items())),
        **{kind: _kind_summary(pairs, kind) for kind in REFERENCE_KINDS},
    }


def summarize(checked: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Per object, all views together and each view on its own."""
    by_subject: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in checked:
        by_subject[str(row.get("subject"))].append(row)
    result: dict[str, Any] = {}
    for subject in sorted(by_subject):
        rows = by_subject[subject]
        by_view: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for row in rows:
            by_view[str(row.get("view"))].append(row)
        result[subject] = {
            "all_views": _group_summary(rows),
            "views": {view: _group_summary(by_view[view]) for view in sorted(by_view)},
        }
    return result


def pooled_reference_table(checked: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """The lead's r3 convention: native supports and physical locations pooled.

    Every (located region, own region in the same series) pair counts, fractions
    rounded to two places and medians taken by ``statistics.median``, as the
    lead's ``locator-truth-check`` table reports them. Kept to reproduce that
    table, not as the yardstick: it mixes physical locations with supports.
    """
    by_subject: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in checked:
        if row.get("located_code") == "ok" and row.get("reference_code") == "judged":
            by_subject[str(row["subject"])].extend(
                pair["judgment"] for pair in row["pairs"]
            )
    table: dict[str, Any] = {}
    for subject in sorted(by_subject):
        judgments = by_subject[subject]
        count = len(judgments)
        table[subject] = {
            "pairs": count,
            "in_plane_overlap": round(
                sum(j["in_plane_overlap"] for j in judgments) / count, 2
            ),
            "centre_inside_support_box": round(
                sum(j["centre_inside_support_box"] for j in judgments) / count, 2
            ),
            "within_2_slices_of_key": round(
                sum(j["within_slice_tolerance"] for j in judgments) / count, 2
            ),
            "centre_inside_and_within_2_slices": round(
                sum(j["on_target"] for j in judgments) / count, 2
            ),
            "median_iou": round(
                statistics.median(j["in_plane_iou"] for j in judgments), 2
            ),
            "median_slice_offset": statistics.median(
                j["slice_offset"] for j in judgments
            ),
        }
    return table


__all__ = [
    "NATIVE_SUPPORT",
    "PHYSICAL_LOCATION",
    "REFERENCE_KINDS",
    "SCHEMA",
    "SLICE_TOLERANCE",
    "check_row",
    "judge",
    "located_object_tiles",
    "located_rows",
    "own_references",
    "pooled_reference_table",
    "summarize",
    "support_coverage",
    "territory_runtime",
    "unlocated_supports",
    "view_key",
]
