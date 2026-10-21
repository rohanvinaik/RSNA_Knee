"""Finite anatomy-first candidate selection for the production locator entrypoint.

Bones found by their structure locate themselves, and every other object is
placed from them (SQUINT_TRAINING_BUILD §4 L2/L0, §9 W10).

* The anchors are the caller's ``study["anchors"]``, or what
  ``knee.diagnosis.squint_anchors.find_anchors`` (lane W9) finds in the study.
  Each is checked by ``squint_interfaces.anchor_code``, against its study and
  bone, and each of its territories against the grid of the series it names.
* A bone whose anchor is ``complete`` or ``partial`` is located by its own
  territories and key planes, never by the best-resembling atlas window. Its
  cheap profile is read over the object tiles of its territories on its
  selected key planes.
* The memory chooses the writer: territory-v2 queries use object/context roles
  and the shared leg calibration at 10 mm and 2 mm. Candidate resemblance reads
  only object-role 10 mm banks, case by case. A v1 memory retains the v1 writer
  and comparison path.
* The 2 mm reading is written beside the 10 mm one while locating
  (``refine_finalists``, the default) or left to the named question that asks for
  it (False, the production caller; ``squint_pipeline._bounded_observation``
  reads it then, once, over the same territory). Deferred, the located profile is
  exactly the 10 mm reading held, for a bone with a native mask as for any other
  territory. The JSON record holds that mask as an address and digest alone, so a
  deferring location keeps the original territory it read by reference on the runtime
  study (``NATIVE_SUPPORT_RETAINED``). ``retained_native_territory`` gives it back for
  the question that asks, when its own serialization is the record asked about, and
  the later reading is made over that very mask. The located objects and their JSON
  never hold it, and it goes with the runtime study. A mask the study does not hold,
  or holds as another territory, is named and never read in its place.
* Every other object is proposed from the usable anchors only, through the
  authored anatomy map in physical millimetres (``anatomical_windows``, which
  reads each anchor's complete reference, or its selected planes when partial).
  Each finite window becomes a ``squint_interfaces`` territory: origin
  ``anatomical_relation`` (``fallback_location`` where only the leg-frame seed
  placed it), its expected places in the object role, one tile of context round
  them, ``object_share`` NaN (an expectation, not a measured share), and the
  anchors and the relation that placed it. A place the leg prior calls outside
  the leg is neither object nor context; a window with no place in the leg is
  refused by name. Resemblance to stored cases is then applied only to these
  candidates, to choose among them (thesis §11.1: resemblance chooses where to
  try; it does not settle what is there). The case-relative scope check, the
  per-study deadline and the explicit coarse and exact ties are unchanged.
* A conflict with an explicit agreeing pair and a third view contradicting both
  becomes a partial anchor of that pair, with the dropped view named. Any
  remaining ``conflict`` or ``unavailable`` bone is located like any
  other object, from the usable anchors, and anchors nothing. With no usable
  anchor at all the study keeps the existing finite route unchanged, named by
  why (``anchor_producer_unavailable``, ``no_usable_structural_anchor``, ...).
  No position is invented, and a missing plane stays missing.

On the structural route each located object keeps ``regions`` (one address per
reading) and the aligned ``territories`` as JSON-safe records
(``territory_record``; ``territory_from_record`` rebuilds the interface shape).
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from knee.diagnosis import squint_locator as shared
from knee.diagnosis.squint_geometry import (
    object_geometry,
)
from knee.diagnosis.squint_interfaces import (
    LEG_OUTSIDE,
    ROLE_CONTEXT,
    ROLE_OBJECT,
    ROLE_OUTSIDE_LEG,
    TERRITORY_PROCEDURE,
    TERRITORY_SCHEMA,
    anchor_code,
    leg_map_code,
    parse_territory_bank_name,
    territory_code,
)
from knee.diagnosis.squint_sanity import window_sanity_checks

BONES = ("femur", "tibia", "patella", "fibula")
USABLE_ANCHOR_STATUSES = ("complete", "partial")
#: Context round a relation territory's expected places, as the teacher's (W4).
CONTEXT_RING_TILES = 1
ANCHOR_GEOMETRY_SCHEMA = "knee.squint-anchor-geometry/v1"
TERRITORY_RECORD_SERIALIZATION = "knee.squint-territory-record/v1"
STRUCTURAL_ROUTE = "structural_anchors"
EXISTING_ROUTE = "existing_finite_route"
#: What the evidence names when the 2 mm reading is left to a question (module note).
FINE_READING_DEFERRED = "deferred_to_a_named_question"
#: Where a deferring location keeps, on the runtime study alone, the original territories
#: whose native masks their JSON records hold as an address (module note).
NATIVE_SUPPORT_RETAINED = "native_support_territories"
_DEPENDENT_API = "knee.diagnosis.squint_anatomy_locator.dependent_territories/v1"
_ORIENTATIONS = ("sagittal", "coronal", "axial")


def resolve_anchor_views(anchor: object) -> dict[str, Any]:
    """Use an explicit agreeing pair only when a third view contradicts both.

    Views are acquisitions (series UIDs), not votes or window centres. W9's
    directed native-section checks supply the pair relations. A silent check
    is no agreement; opposed checks on the same pair cannot resolve it. This
    pure adapter never changes the supplied anchor or manufactures a third
    plane. All original evidence stays in the resolution record.
    """
    code = anchor_code(anchor)
    if code != "valid":
        return {"status": "unavailable", "view_resolution": {"code": code}}
    assert isinstance(anchor, Mapping)
    if anchor.get("status") != "conflict":
        return dict(anchor)
    territories = anchor.get("territories", ())
    observed = {territory["series_uid"] for territory in territories}
    pairs: dict[tuple[str, str], set[str]] = {}
    for territory in territories:
        uid = territory["series_uid"]
        for check in territory.get("provenance", {}).get("cross_view_checks", ()):
            other = check.get("against_series_uid")
            if not isinstance(other, str) or other == uid or other not in observed:
                continue
            outcome = check.get("outcome")
            relation = (
                "agree"
                if outcome == "consistent"
                else "conflict"
                if outcome == "the_other_views_section_lies_mostly_in_another_territory"
                else None
            )
            if relation is not None:
                pairs.setdefault(tuple(sorted((uid, other))), set()).add(relation)
    views = sorted({uid for pair in pairs for uid in pair})
    choices = []
    for a, b in itertools.combinations(views, 2):
        if pairs.get((a, b)) != {"agree"}:
            continue
        for dropped in set(views) - {a, b}:
            if all(
                pairs.get(tuple(sorted((uid, dropped)))) == {"conflict"}
                for uid in (a, b)
            ) and set(views) == {a, b, dropped}:
                choices.append((a, b, dropped))
    resolution = {
        "code": "conflict_without_unique_agreeing_pair",
        "original_status": "conflict",
        "original_key_planes": anchor.get("key_planes", {}),
        "original_reference": anchor.get("reference"),
        "original_reference_lps": anchor.get("reference_lps"),
        "original_conflicts": anchor.get("conflicts", []),
        "pair_relations": [
            {"series_uids": list(pair), "relations": sorted(relations)}
            for pair, relations in sorted(pairs.items())
        ],
        "dropped_views": [],
    }
    result = {**anchor, "view_resolution": resolution}
    if len(choices) != 1:
        return result
    a, b, dropped = choices[0]
    resolution.update(
        code="partial_anchor_two_agree_third_contradicts_both",
        agreeing_views=[a, b],
        dropped_views=[
            {
                "series_uid": dropped,
                "reason": "contradicts_both_members_of_the_agreeing_pair",
            }
        ],
        unused_territories=[
            territory_record(t) for t in territories if t["series_uid"] not in (a, b)
        ],
    )
    result.update(
        status="partial",
        territories=[t for t in territories if t["series_uid"] in (a, b)],
        key_planes={
            orientation: plane
            for orientation, plane in anchor.get("key_planes", {}).items()
            if plane.get("series_uid") in (a, b)
        },
        reference_lps=None,
        reference={"status": "partial", "point_lps": None, "precision_mm": None},
        conflicts=[],
    )
    return result


def _object_coarse_banks(profile: object) -> dict[str, list[int]]:
    """Only v2 object-role 10 mm readings may place a v2 candidate."""
    if shared._source(profile).get("procedure") != TERRITORY_PROCEDURE:
        return {}
    result = {}
    for name, counts in (shared._banks(profile) or {}).items():
        fields = parse_territory_bank_name(name)
        if (
            fields
            and fields["role"] == "object"
            # Bank scale is an exact typed address; near scales must remain ineligible.
            and fields["scale_mm"] == 10.0  # NOSONAR(S1244)
        ):
            result[name] = list(counts)
    return result


def _territory_profile(
    series: dict,
    territory: dict,
    calibration: tuple[dict, dict],
    *,
    coarse: dict | None = None,
    refine: bool = False,
    deadline: float | None = None,
) -> dict:
    """One addressed coarse reading, optionally paired with its native 2 mm reading."""
    from knee.diagnosis.squint_profiles import (
        merge_profiles,
        profile_territory,
        refine_territory,
    )

    subject = territory["subject"]
    if coarse is None:
        coarse = profile_territory(
            series,
            territory,
            series["leg_map"],
            subject=subject,
            calibration=calibration,
        )
    if not refine:
        return coarse
    if deadline is not None and time.monotonic() >= deadline:
        return {
            **coarse,
            "source": {
                **coarse["source"],
                "fine_reading": {
                    "code": "deadline_before_territory_refinement",
                },
            },
        }
    try:
        fine = refine_territory(series, territory, series["leg_map"], subject=subject)
    except (TypeError, ValueError) as error:
        return {
            **coarse,
            "source": {
                **coarse["source"],
                "fine_reading": {
                    "code": "territory_refinement_unavailable",
                    "reason": str(error),
                },
            },
        }
    return merge_profiles([coarse, fine], subject=subject)


def _json_safe(value: Any) -> Any:
    """Plain JSON values: arrays become lists, NaN and infinities become None."""
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if value is None or isinstance(value, (bool, int, str)):
        return value
    return str(value)


def _object_window(
    territory: Mapping[str, Any],
) -> tuple[int, int, int, int, int, int] | None:
    """The half-open tile box of a territory's object places: an address only."""
    roles = territory.get("roles")
    window = territory.get("tile_window")
    if (
        not isinstance(roles, np.ndarray)
        or roles.ndim != 3
        or not isinstance(window, (list, tuple))
        or len(window) != 6
    ):
        return None
    places = np.argwhere(roles == ROLE_OBJECT)
    if not len(places):
        return None
    z0, _z1, r0, _r1, c0, _c1 = (int(value) for value in window)
    low = places.min(axis=0)
    high = places.max(axis=0) + 1
    return (
        z0 + int(low[0]),
        z0 + int(high[0]),
        r0 + int(low[1]),
        r0 + int(high[1]),
        c0 + int(low[2]),
        c0 + int(high[2]),
    )


def territory_record(territory: Mapping[str, Any]) -> dict[str, Any]:
    """The JSON-safe record of one frozen-interface territory.

    Roles and shares become nested lists; an unmeasured share is None, never
    zero. The runtime-only native support mask is replaced by its address and
    digest. ``territory_from_record`` rebuilds the interface shape.
    """
    code = territory_code(territory)
    if code != "valid":
        raise ValueError(code)
    record = {
        key: _json_safe(value)
        for key, value in territory.items()
        if key not in ("roles", "object_share", "native_support")
    }
    record["serialization"] = TERRITORY_RECORD_SERIALIZATION
    record["roles"] = territory["roles"].astype(np.int64).tolist()
    share = np.asarray(territory["object_share"], dtype=np.float64)
    record["object_share"] = [
        [
            [float(value) if math.isfinite(value) else None for value in row]
            for row in plane
        ]
        for plane in share
    ]
    support = territory.get("native_support")
    record["native_support"] = None
    if support is not None:
        mask = np.ascontiguousarray(support["mask"])
        record["native_support_address"] = {
            "slices": [int(value) for value in support["slices"]],
            "offset_rc": [int(value) for value in support["offset_rc"]],
            "shape": [int(value) for value in mask.shape],
            "support_count": int(np.count_nonzero(mask)),
            "mask_sha256": hashlib.sha256(mask.tobytes()).hexdigest(),
            "retention": "runtime_only_mask_not_serialized",
        }
    return record


def territory_from_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """The frozen-interface territory of a record (its native mask is not kept)."""
    if (
        not isinstance(record, Mapping)
        or record.get("serialization") != TERRITORY_RECORD_SERIALIZATION
    ):
        raise ValueError("territory_record_invalid")
    try:
        roles = np.asarray(record["roles"], dtype=np.int8)
        share = np.asarray(
            [
                [
                    [math.nan if value is None else float(value) for value in row]
                    for row in plane
                ]
                for plane in record["object_share"]
            ],
            dtype=np.float64,
        )
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        raise ValueError("territory_record_invalid") from error
    territory = {
        key: value
        for key, value in record.items()
        if key not in ("roles", "object_share", "native_support", "serialization")
    }
    territory["roles"] = roles
    territory["object_share"] = share
    territory["native_support"] = None
    code = territory_code(territory)
    if code != "valid":
        raise ValueError(code)
    return territory


def retained_native_territory(
    study: object, record: Mapping[str, Any]
) -> tuple[Mapping[str, Any] | None, str]:
    """The retained original of a record that holds its native mask as an address alone.

    ``territory_record`` replaces the runtime-only mask by its address and digest, and a
    territory rebuilt from the record has none: read over its coarse object tiles, it
    would be other pixels than its 10 mm reading. A deferring location keeps the original
    territories it read by reference on the runtime study (``locate_anatomy_first``). One
    is returned only when its own ``territory_record`` is this record: the same study,
    subject, series, tile window, roles, shares and mask address and digest, never a
    bounding box or a subject alone. Otherwise the reason is named:
    ``native_support_mask_not_retained`` (the study holds no territory at the record's
    address) or ``native_support_mask_mismatch`` (it holds some there, none of them this).
    """

    def address(value: Mapping[str, Any]) -> list[Any]:
        return [
            value.get("study_uid"),
            value.get("subject"),
            value.get("series_uid"),
            _json_safe(value.get("tile_window")),
        ]

    retained = (
        study.get(NATIVE_SUPPORT_RETAINED) if isinstance(study, Mapping) else None
    )
    wanted = address(record)
    here = [
        territory
        for territory in (retained if isinstance(retained, list) else ())
        if isinstance(territory, Mapping) and address(territory) == wanted
    ]
    if not here:
        return None, "native_support_mask_not_retained"
    for territory in here:
        try:
            if territory_record(territory) == dict(record):
                return territory, "retained"
        except (AttributeError, KeyError, TypeError, ValueError):
            continue
    return None, "native_support_mask_mismatch"


def _plane_has_geometry(address: Mapping[str, Any]) -> bool:
    try:
        normal = np.asarray(address.get("normal"), dtype=np.float64)
        offset = float(address["offset_mm"])
    except (KeyError, TypeError, ValueError):
        return False
    return (
        normal.shape == (3,)
        and bool(np.all(np.isfinite(normal)))
        and float(np.linalg.norm(normal)) > 0
        and math.isfinite(offset)
    )


def _anchor_geometry(
    subject: str, anchor: Mapping[str, Any], series_by_uid: Mapping[str, Any]
) -> dict[str, Any]:
    """One usable anchor's planes and reference, in the shape the priors read.

    A selected plane given only as its series and slice takes its physical
    plane from that slice's own acquisition frame (``object_geometry``). A plane
    the anchor does not supply is not made, and its unresolved outcomes stay.
    """
    planes: dict[str, Any] = {}
    derive: list[tuple[str, Mapping[str, Any]]] = []
    raw_planes = anchor.get("key_planes", {})
    for orientation in _ORIENTATIONS:
        address = raw_planes.get(orientation)
        if address is None:
            continue
        if not isinstance(address, Mapping):
            planes[orientation] = {
                "orientation": orientation,
                "outcome": "invalid:anchor_plane_not_mapping",
            }
            continue
        if address.get("outcome") == "selected" and not _plane_has_geometry(address):
            if (
                isinstance(address.get("series_uid"), str)
                and type(address.get("slice")) is int
            ):
                derive.append((orientation, address))
            else:
                planes[orientation] = {
                    **_json_safe(dict(address)),
                    "outcome": "invalid:anchor_plane_address_incomplete",
                    "anchor_outcome": "selected",
                }
            continue
        planes[orientation] = _json_safe(dict(address))
    if derive:
        derived = object_geometry(
            subject,
            [
                {
                    "series_uid": address["series_uid"],
                    "window": [address["slice"], address["slice"] + 1, 0, 1, 0, 1],
                }
                for _orientation, address in derive
            ],
            dict(series_by_uid),
        )
        derived_planes = derived.get("planes", {})
        for orientation, address in derive:
            plane = derived_planes.get(orientation)
            if (
                isinstance(plane, Mapping)
                and plane.get("outcome") == "selected"
                and plane.get("series_uid") == address["series_uid"]
                and plane.get("slice") == address["slice"]
            ):
                planes[orientation] = {
                    **_json_safe(dict(plane)),
                    "geometry_source": "acquisition_frame_at_anchor_slice",
                }
            else:
                planes[orientation] = {
                    **_json_safe(dict(address)),
                    "outcome": "invalid:anchor_plane_frame_unavailable",
                    "anchor_outcome": "selected",
                    "derived_outcome": plane.get("outcome")
                    if isinstance(plane, Mapping)
                    else None,
                }
    reference = anchor.get("reference")
    reference = reference if isinstance(reference, Mapping) else {}
    precision = None
    raw_precision = reference.get("precision_mm")
    if isinstance(raw_precision, (list, tuple)) and len(raw_precision) == 3:
        try:
            values = [float(value) for value in raw_precision]
        except (TypeError, ValueError):
            values = []
        if len(values) == 3 and all(math.isfinite(v) and v >= 0 for v in values):
            precision = values
    point = anchor.get("reference_lps")
    return {
        "schema": ANCHOR_GEOMETRY_SCHEMA,
        "subject": subject,
        "source": "structural_anchor",
        "producer": _json_safe(anchor.get("producer")),
        "planes": planes,
        "reference": {
            "status": anchor["status"],
            "point_lps": None if point is None else [float(value) for value in point],
            "precision_mm": precision,
            "position_status": _json_safe(reference.get("status")),
            "construction": "the anchor's own key planes; no centroid stands in "
            "for a missing plane",
        },
    }


def _anchor_territories(
    bone: str,
    anchor: Mapping[str, Any],
    study_uid: object,
    series_by_uid: Mapping[str, Any],
) -> tuple[list[Mapping[str, Any]], dict[str, int]]:
    kept: list[Mapping[str, Any]] = []
    refused: Counter = Counter()
    for territory in anchor.get("territories", ()):
        record = series_by_uid.get(territory.get("series_uid"))
        stack = record.get("stack") if isinstance(record, Mapping) else None
        grid = getattr(getattr(stack, "median", None), "shape", None)
        if record is None:
            code = "territory_series_not_in_study"
        elif grid is None or len(grid) != 3:
            code = "territory_series_without_squint"
        else:
            code = territory_code(territory, grid_shape=tuple(grid))
            if code == "valid" and (
                territory.get("study_uid") != study_uid
                or territory.get("subject") != bone
            ):
                code = "territory_identity_mismatch"
        if code == "valid":
            kept.append(territory)
        else:
            refused[code] += 1
    return kept, dict(sorted(refused.items()))


def _anchor_summary(
    anchor: object,
    code: str,
    territories: Sequence[Mapping[str, Any]],
    refused: Mapping[str, int],
) -> dict[str, Any]:
    if not isinstance(anchor, Mapping):
        return {"status": "unavailable", "code": code}
    planes = anchor.get("key_planes")
    planes = planes if isinstance(planes, Mapping) else {}
    declared = anchor.get("status")
    return _json_safe(
        {
            "status": declared if code == "valid" else "unavailable",
            "declared_status": declared,
            "code": code,
            "producer": anchor.get("producer"),
            "cost": anchor.get("cost"),
            "key_planes": {
                str(orientation): {
                    "outcome": address.get("outcome"),
                    "series_uid": address.get("series_uid"),
                    "slice": address.get("slice"),
                }
                for orientation, address in planes.items()
                if isinstance(address, Mapping)
            },
            "reference_lps": anchor.get("reference_lps"),
            "breadth_mm": anchor.get("breadth_mm"),
            "breadth_source": anchor.get("breadth_source"),
            "breadth_use": "recorded_not_applied_as_knee_scale",
            "knee": anchor.get("knee"),
            "conflicts": anchor.get("conflicts", []),
            "view_resolution": anchor.get("view_resolution"),
            "territory_count": len(territories),
            "refused_territories": dict(refused),
        }
    )


def study_anchors(
    study: Mapping[str, Any],
    series_by_uid: Mapping[str, Any],
    *,
    deadline: float | None = None,
) -> dict[str, Any]:
    """The study's structural bone anchors, each checked, with how they came.

    ``route`` is ``structural_anchors`` when at least one bone has a usable
    (complete or partial) anchor, else ``existing_finite_route``. ``usable``
    holds each usable bone's checked anchor and territories; ``geometry`` its
    planes and reference for the relation priors; ``bones`` a JSON-safe summary
    of every bone, usable or not, with its named code; ``source`` how the
    anchors were obtained, or why none were.
    """
    state: dict[str, Any] = {
        "route": EXISTING_ROUTE,
        "source": {},
        "bones": {},
        "usable": {},
        "geometry": {},
    }
    study_uid = study.get("study_uid") if isinstance(study, Mapping) else None
    supplied = study.get("anchors") if isinstance(study, Mapping) else None
    if supplied is not None:
        raw = supplied
        state["source"] = {"status": "supplied_with_study"}
    else:
        try:
            from knee.diagnosis.squint_anchors import find_anchors
        except ImportError:
            state["source"] = {"status": "anchor_producer_unavailable"}
            return state
        if deadline is not None and time.monotonic() >= deadline:
            state["source"] = {"status": "deadline_before_anchor_search"}
            return state
        started = time.perf_counter()
        try:
            raw = find_anchors(study)
        except (IndexError, KeyError, TypeError, ValueError) as error:
            state["source"] = {
                "status": f"anchor_producer_failed:{type(error).__name__}",
                "seconds": time.perf_counter() - started,
            }
            return state
        state["source"] = {
            "status": "produced",
            "api": "knee.diagnosis.squint_anchors.find_anchors",
            "seconds": time.perf_counter() - started,
        }
    if not isinstance(raw, Mapping):
        state["source"]["status"] = "anchor_result_invalid"
        return state
    for name in sorted(raw, key=str):
        anchor = raw[name]
        if name not in BONES:
            state["bones"][str(name)] = {
                "status": "unavailable",
                "code": "anchor_subject_not_a_bone",
            }
            continue
        code = anchor_code(anchor)
        if code == "valid" and (
            anchor.get("subject") != name or anchor.get("study_uid") != study_uid
        ):
            code = "anchor_identity_mismatch"
        if code == "valid":
            anchor = resolve_anchor_views(anchor)
        territories, refused = (
            _anchor_territories(name, anchor, study_uid, series_by_uid)
            if code == "valid"
            else ([], {})
        )
        state["bones"][name] = _anchor_summary(anchor, code, territories, refused)
        if code == "valid" and anchor["status"] in USABLE_ANCHOR_STATUSES:
            state["usable"][name] = {"anchor": anchor, "territories": territories}
            state["geometry"][name] = _anchor_geometry(name, anchor, series_by_uid)
    for name in BONES:
        state["bones"].setdefault(
            name, {"status": "unavailable", "code": "anchor_not_returned"}
        )
    if state["usable"]:
        state["route"] = STRUCTURAL_ROUTE
    else:
        state["source"]["route_reason"] = "no_usable_structural_anchor"
    return state


def _outside_leg(
    series_record: Mapping[str, Any], foreground: np.ndarray | None
) -> tuple[np.ndarray, dict[str, Any]]:
    """Tiles the leg prior calls outside the leg; unread tiles are never outside.

    A valid W1 leg map on the series record names them (``LEG_OUTSIDE``).
    Otherwise the locator's own foreground does (``squint_locator._leg_bounds``):
    a measured tile that foreground leaves out.
    """
    stack = series_record["stack"]
    shape = tuple(stack.median.shape)
    leg_map = series_record.get("leg_map")
    refused = None
    if leg_map is not None:
        code = leg_map_code(leg_map, grid_shape=shape)
        if code == "valid" and leg_map.get("series_uid") != series_record.get(
            "series_uid"
        ):
            code = "leg_map_series_mismatch"
        if code == "valid":
            outside = np.asarray(leg_map["codes"]) == LEG_OUTSIDE
            return outside, {
                "source": "leg_map",
                "rule": _json_safe(leg_map.get("rule")),
                "outside_tiles": int(np.count_nonzero(outside)),
            }
        refused = code
    if not isinstance(foreground, np.ndarray) or foreground.shape != shape:
        return np.zeros(shape, dtype=np.bool_), {
            "source": "leg_prior_unavailable",
            "outside_tiles": 0,
            "leg_map_refused": refused,
        }
    coverage = np.asarray(stack.coverage, dtype=np.float64)
    measured = np.isfinite(coverage) & (coverage > 0)
    maximum = getattr(stack, "maximum", None)
    if isinstance(maximum, np.ndarray) and maximum.shape == shape:
        measured &= np.isfinite(maximum)
    outside = measured & ~np.asarray(foreground, dtype=np.bool_)
    return outside, {
        "source": "squint_foreground_proxy",
        "rule": "measured tiles the locator's foreground (squint_locator._leg_bounds) "
        "leaves out; unread tiles are not outside",
        "outside_tiles": int(np.count_nonzero(outside)),
        "leg_map_refused": refused,
    }


def _authored_relations(subject: str) -> list[dict[str, Any]]:
    try:
        from knee.collapse.anatomical_relations import RELATIONSHIPS
    except ImportError:
        return []
    return [
        {
            "predicate": predicate,
            "targets": list(targets),
            "qualifier": qualifier,
            "source": source,
        }
        for name, predicate, targets, qualifier, source in RELATIONSHIPS
        if name == subject
    ]


_HYPOTHESIS_FIELDS = (
    "anchor",
    "kind",
    "anchor_observation_status",
    "prior_only",
    "anchor_point_lps",
    "anchor_precision_status",
    "expected_point_lps",
    "ideal_vector_mps_mm",
    "ideal_source",
    "knee_side_hypothesis",
    "origin_lps",
    "origin_status",
    "projected_anchor_prior_lps",
)


def _hypothesis_rows(
    sources: Sequence[Any], hypotheses: Sequence[Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """The hypotheses that placed one window: current anchors, and leg-frame seeds."""
    grouped: dict[int, dict[str, set[str]]] = {}
    for source in sources:
        if not isinstance(source, Mapping):
            continue
        index = source.get("hypothesis_index")
        if type(index) is not int or not 0 <= index < len(hypotheses):
            continue
        entry = grouped.setdefault(index, {"samples": set(), "sizes": set()})
        entry["samples"].add(str(source.get("sample")))
        entry["sizes"].add(str(source.get("size_hypothesis")))
    anchors: list[dict[str, Any]] = []
    seeds: list[dict[str, Any]] = []
    for index in sorted(grouped):
        hypothesis = hypotheses[index]
        if not isinstance(hypothesis, Mapping):
            continue
        row = {
            key: _json_safe(hypothesis[key])
            for key in _HYPOTHESIS_FIELDS
            if key in hypothesis
        }
        row["hypothesis_index"] = index
        row["samples"] = sorted(grouped[index]["samples"])
        row["size_hypotheses"] = sorted(grouped[index]["sizes"])
        (seeds if hypothesis.get("kind") == "leg_frame_prior" else anchors).append(row)
    return anchors, seeds


def _relation_territory(
    study_uid: object,
    series_record: Mapping[str, Any],
    subject: str,
    window: tuple[int, ...],
    *,
    outside: np.ndarray,
    origin: str,
    relation: Mapping[str, Any],
    sources: Sequence[Any],
    hypotheses: Sequence[Any],
    leg_prior: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, str]:
    stack = series_record["stack"]
    _depth, rows, cols = stack.median.shape
    z0, z1, r0, r1, c0, c1 = window
    if z1 - z0 != 1:
        return None, "relation_window_not_one_slice"
    expected = np.zeros((rows, cols), dtype=np.bool_)
    expected[r0:r1, c0:c1] = True
    places = expected & ~outside[z0]
    if not places.any():
        return None, "relation_window_outside_leg"
    place_rows, place_cols = np.nonzero(places)
    b0, b1 = int(place_rows.min()), int(place_rows.max()) + 1
    d0, d1 = int(place_cols.min()), int(place_cols.max()) + 1
    t0, t1 = max(0, b0 - CONTEXT_RING_TILES), min(rows, b1 + CONTEXT_RING_TILES)
    u0, u1 = max(0, d0 - CONTEXT_RING_TILES), min(cols, d1 + CONTEXT_RING_TILES)
    roles = np.full((1, t1 - t0, u1 - u0), ROLE_CONTEXT, dtype=np.int8)
    roles[0][places[t0:t1, u0:u1]] = ROLE_OBJECT
    roles[0][outside[z0, t0:t1, u0:u1]] = ROLE_OUTSIDE_LEG
    anchors, seeds = _hypothesis_rows(sources, hypotheses)
    view = series_record.get("view")
    orientation = view.get("orientation") if isinstance(view, Mapping) else None
    territory = {
        "schema": TERRITORY_SCHEMA,
        "study_uid": study_uid,
        "series_uid": series_record.get("series_uid"),
        "subject": subject,
        "origin": origin,
        "tile_window": [z0, z0 + 1, t0, t1, u0, u1],
        "roles": roles,
        "object_share": np.full(roles.shape, np.nan, dtype=np.float64),
        "native_support": None,
        "anchors": anchors,
        "relation": dict(relation),
        "key_planes": {},
        "provenance": {
            "api": _DEPENDENT_API,
            "proposal_windows": [list(window)],
            "candidate_slice": {
                "series_uid": series_record.get("series_uid"),
                "slice": z0,
                "orientation": orientation.lower()
                if isinstance(orientation, str)
                else None,
            },
            "object_tile_count": int(np.count_nonzero(places)),
            "outside_leg_tiles_in_object_box": int(
                np.count_nonzero(outside[z0, b0:b1, d0:d1])
            ),
            "leg_prior": dict(leg_prior),
            "leg_frame_seeds": seeds,
            "object_share_status": "expected_places_not_measured",
            "identity_assertion": None,
        },
    }
    code = territory_code(territory, grid_shape=stack.median.shape)
    return (territory, "valid") if code == "valid" else (None, code)


def _merge_duplicate(previous: dict[str, Any], duplicate: Mapping[str, Any]) -> None:
    """Two windows with the same places in the leg are one candidate."""
    previous["provenance"]["proposal_windows"].extend(
        duplicate["provenance"]["proposal_windows"]
    )
    known = {row["hypothesis_index"]: row for row in previous["anchors"]}
    for row in duplicate["anchors"]:
        mine = known.get(row["hypothesis_index"])
        if mine is None:
            previous["anchors"].append(row)
            known[row["hypothesis_index"]] = row
            continue
        mine["samples"] = sorted(set(mine["samples"]) | set(row["samples"]))
        mine["size_hypotheses"] = sorted(
            set(mine["size_hypotheses"]) | set(row["size_hypotheses"])
        )
    previous["anchors"].sort(key=lambda row: row["hypothesis_index"])
    seeds = previous["provenance"]["leg_frame_seeds"]
    seen = {row["hypothesis_index"] for row in seeds}
    seeds.extend(
        row
        for row in duplicate["provenance"]["leg_frame_seeds"]
        if row["hypothesis_index"] not in seen
    )


def dependent_territories(
    series_record: Mapping[str, Any],
    subject: str,
    *,
    study_uid: object,
    anchors: Mapping[str, Any],
    leg_bounds_lps: tuple[tuple[float, ...], tuple[float, ...]] | None,
    foreground: np.ndarray | None = None,
    knee_side: str | None = None,
    knee_scale_mm: float | None = None,
) -> dict[str, Any]:
    """Propose one object's candidate territories in one series from the anchors.

    The authored anatomy helper places finite one-slice windows from each
    anchor's reference or selected planes (``anatomical_windows``). Each window
    becomes one territory (module note); windows with the same places in the
    leg are one candidate, and their placements are merged. ``foreground`` is the
    locator's leg eligibility for the series, which the locator always passes;
    omitted, the unmapped ``_leg_bounds`` foreground is used, and a leg map on
    the series record still decides which places are outside the leg.
    """
    stack = series_record.get("stack") if isinstance(series_record, Mapping) else None
    median = getattr(stack, "median", None)
    if (
        getattr(stack, "code", None) != "present"
        or not isinstance(median, np.ndarray)
        or median.ndim != 3
    ):
        return {
            "status": "geometry_unavailable",
            "reason": "series_squint_unavailable",
            "origin": None,
            "territories": [],
            "refusals": {},
            "proposed_window_count": 0,
            "leg_prior": None,
            "proposal": {
                "status": "geometry_unavailable",
                "windows": [],
                "reason": "series_squint_unavailable",
            },
        }
    if foreground is None:
        foreground = shared._leg_bounds(stack)[2]
    proposal = shared._anatomical_window_proposal(
        series_record,
        subject,
        leg_bounds_lps=leg_bounds_lps,
        foreground=foreground,
        anchors=anchors,
        knee_side=knee_side,
        knee_scale_mm=knee_scale_mm,
    )
    provenance = proposal.get("provenance")
    provenance = provenance if isinstance(provenance, Mapping) else {}
    hypotheses = provenance.get("hypotheses")
    hypotheses = hypotheses if isinstance(hypotheses, list) else []
    sources_by_window: dict[tuple[int, ...], Sequence[Any]] = {}
    window_sources = provenance.get("window_sources")
    for row in window_sources if isinstance(window_sources, list) else ():
        if isinstance(row, Mapping) and isinstance(row.get("window"), list):
            sources = row.get("sources")
            sources_by_window[tuple(row["window"])] = (
                sources if isinstance(sources, list) else []
            )
    seeded = provenance.get("leg_frame_prior_used") is True
    origin = "fallback_location" if seeded else "anatomical_relation"
    relation = {
        "kind": "leg_frame_prior_without_anchor"
        if seeded
        else "authored_anatomy_map_from_current_study_anchors",
        "subject": subject,
        "relation_source": "knee.collapse.anatomy_map.ideal_vector; "
        "knee.collapse.anatomical_relations.RELATIONSHIPS",
        "authored_relations": _authored_relations(subject),
        "target_span_mm": _json_safe(provenance.get("target_span_mm")),
        "knee_scale_mm": _json_safe(provenance.get("knee_scale_mm")),
        "knee_scale_status": _json_safe(provenance.get("knee_scale_status")),
        "knee_side": _json_safe(provenance.get("knee_side")),
        "knee_side_status": _json_safe(provenance.get("knee_side_status")),
        "context_ring_tiles": CONTEXT_RING_TILES,
        "proposal_schema": _json_safe(provenance.get("schema")),
        "reference_kind": _json_safe(provenance.get("reference_kind")),
    }
    outside, leg_prior = _outside_leg(series_record, foreground)
    found: dict[tuple[int, ...], dict[str, Any]] = {}
    refusals: Counter = Counter()
    windows = proposal.get("windows", ())
    for window in windows:
        territory, code = _relation_territory(
            study_uid,
            series_record,
            subject,
            tuple(window),
            outside=outside,
            origin=origin,
            relation=relation,
            sources=sources_by_window.get(tuple(window), ()),
            hypotheses=hypotheses,
            leg_prior=leg_prior,
        )
        if territory is None:
            refusals[code] += 1
            continue
        key = _object_window(territory)
        assert key is not None  # _relation_territory requires at least one object tile.
        if key in found:
            _merge_duplicate(found[key], territory)
            continue
        found[key] = territory
    return {
        "status": proposal.get("status"),
        "reason": proposal.get("reason"),
        "origin": origin,
        "territories": list(found.values()),
        "refusals": dict(sorted(refusals.items())),
        "proposed_window_count": len(windows),
        "leg_prior": leg_prior,
        "proposal": proposal,
    }


def _on_selected_key_plane(territory: Mapping[str, Any]) -> bool:
    planes = territory.get("key_planes")
    window = territory.get("tile_window")
    if not isinstance(planes, Mapping) or not isinstance(window, (list, tuple)):
        return False
    z0, z1 = int(window[0]), int(window[1])
    return any(
        isinstance(address, Mapping)
        and address.get("outcome") == "selected"
        and address.get("series_uid") == territory.get("series_uid")
        and type(address.get("slice")) is int
        and z0 <= address["slice"] < z1
        for address in planes.values()
    )


def _anchored_object(
    subject: str,
    entry: Mapping[str, Any],
    summary: Mapping[str, Any],
    geometry: Mapping[str, Any],
    series_by_uid: Mapping[str, Any],
    calibrations: Mapping[str, Any] | None = None,
    deadline: float | None = None,
    *,
    refine_finalists: bool = True,
    retained_support: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """A bone located by its own anchor: its territories, read, never searched.

    A territory-v2 reading is paired with its 2 mm one unless ``refine_finalists`` is
    False, which leaves it to the question that asks, whether or not the territory
    carries a native mask. A given ``retained_support`` collects, by reference, each
    territory read that does: its record holds the mask as an address alone, and the
    question that asks needs the original (``retained_native_territory``).
    """
    from knee.diagnosis.squint_profiles import merge_profiles, profile_window

    territories = list(entry["territories"])
    reading = [item for item in territories if _on_selected_key_plane(item)]
    reading_policy = "territories_on_selected_key_planes"
    if not reading:
        reading = territories
        reading_policy = "all_anchor_territories_none_on_a_selected_key_plane"
    profiles = []
    regions = []
    records = []
    candidate_profiles = []
    read: list[Mapping[str, Any]] = []
    #: for each held territory-v2 reading, whether its 2 mm one was made while locating
    paired: list[bool] = []
    seen: set[tuple[Any, ...]] = set()
    duplicates = 0
    refusals = []
    for territory in reading:
        if deadline is not None and time.monotonic() >= deadline:
            refusals.append({"reason": "deadline_before_anchor_reading"})
            break
        window = _object_window(territory)
        series_record = series_by_uid.get(territory["series_uid"])
        if window is None or series_record is None:
            continue
        identity = (territory["series_uid"], window)
        if calibrations is not None:
            # Equal boxes need not hold equal places. Only an identical reading
            # is shared; distinct native supports retain their own profiles.
            record = territory_record(territory)
            identity += (
                tuple(territory["tile_window"]),
                territory["roles"].tobytes(),
                json.dumps(record.get("native_support_address"), sort_keys=True),
            )
        if identity in seen:
            # The same places read twice would count the same tiles twice.
            duplicates += 1
            continue
        seen.add(identity)
        if calibrations is not None:
            calibration = calibrations.get(territory["series_uid"])
            if not isinstance(calibration, tuple):
                refusals.append(
                    {
                        "series_uid": territory["series_uid"],
                        "reason": calibration or "leg_calibration_unavailable",
                    }
                )
                continue
            profile = _territory_profile(
                series_record,
                territory,
                calibration,
                refine=refine_finalists,
                deadline=deadline,
            )
            if not _object_coarse_banks(profile):
                refusals.append(
                    {
                        "series_uid": territory["series_uid"],
                        "reason": "anchor_object_reading_silent",
                    }
                )
                continue
            paired.append(refine_finalists)
        else:
            profile = profile_window(dict(series_record), window, subject=subject)
        read.append(territory)
        profiles.append(profile)
        regions.append(
            {
                "series_uid": territory["series_uid"],
                "view": series_record.get("view"),
                "window": window,
            }
        )
        records.append(territory_record(territory))
        if calibrations is not None:
            # W11 reads each region's own territory. Keep the aligned object
            # list as well, for W10's public readback adapter.
            regions[-1]["territory"] = records[-1]
            if (
                retained_support is not None
                and territory.get("native_support") is not None
            ):
                # The record holds this territory's native mask as an address alone.
                retained_support.append(territory)
        candidate_profiles.append(
            {
                "profile": profile,
                "series_uid": territory["series_uid"],
                "view": series_record.get("view"),
                "window": window,
                "territory_origin": territory["origin"],
            }
        )
    merged = None
    if profiles:
        try:
            merged = merge_profiles(profiles, subject=subject)
        except ValueError:
            if len(profiles) == 1:
                merged = profiles[0]
    catalog = shared._intern_candidate_profiles(candidate_profiles, [])
    other = [
        territory_record(item)
        for item in territories
        if not any(item is used for used in read)
    ]
    deferred = paired.count(False)
    if calibrations is None:
        profile_reading = "scan_tercile_v1_over_object_tile_box"
    elif not deferred:
        profile_reading = "leg_tercile_territory_v2_10mm_and_2mm"
    else:
        profile_reading = "leg_tercile_territory_v2_10mm"
    evidence: dict[str, Any] = {
        "source": "current_study_structural_anchor",
        "location_route": "structural_anchor",
        "anchor": dict(summary),
        "resemblance_applied": False,
        "candidate_profiles_compared": 0,
        "reading_territories": reading_policy,
        "duplicate_reading_territories": duplicates,
        "profile_reading": profile_reading,
        "reading_refusals": refusals,
        "other_anchor_territories": other,
        "spatial_constraints": dict(geometry),
        "candidate_profile_catalog": catalog["profiles"],
        "candidate_bank_catalog": catalog["banks"],
        "candidate_series_context_catalog": catalog["series_contexts"],
        "patient_coordinates_carried": False,
    }
    if calibrations is not None and not refine_finalists:
        evidence["fine_reading"] = {
            "policy": FINE_READING_DEFERRED,
            "requested_at_location": paired.count(True),
            "deferred": deferred,
        }
    if not regions:
        evidence["reason"] = "structural_anchor_without_readable_territory"
    return {
        "status": "proposal" if regions else "unresolved_missing_reading",
        "profile": merged,
        "candidate_profiles": candidate_profiles,
        "regions": regions,
        "territories": records,
        "evidence": evidence,
    }


def _sanity_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Keep the scope of a plausibility check distinct from an identity claim."""
    statuses = {row.get("status") for row in rows}
    return {
        "schema": "knee.object-anatomical-sanity/v1",
        "status": "contradicted"
        if "contradicted" in statuses
        else "plausible"
        if "plausible" in statuses
        else "unknown",
        "identity_assertion": None,
        "windows": list(rows),
    }


def _check_anchor_sanity(
    state: dict[str, Any], series_by_uid: Mapping[str, Any], knee_side: str | None
) -> None:
    """A contradicted pair cannot silently anchor dependent objects.

    Preserve both observations and name the conflict; these checks do not choose
    which of two conflicting bone names was mistaken. A partial reference speaks
    only on the LPS axes its selected planes determine (``squint_sanity``); its
    other axes, and missing references, remain neutral and do not prevent their
    existing useful guide contribution.
    """
    checked: dict[str, Any] = {}
    conflicts: set[str] = set()
    for name, entry in state["usable"].items():
        rows = []
        for territory in entry["territories"]:
            window = _object_window(territory)
            series = series_by_uid.get(territory["series_uid"])
            if window is None or series is None:
                continue
            for row in window_sanity_checks(
                series, name, [window], state["geometry"], knee_side
            ):
                row["series_uid"] = territory["series_uid"]
                rows.append(row)
                for check in row["checks"]:
                    if check["result"].startswith("reversed_"):
                        conflicts.add(name)
                        reference = check.get("reference_subject")
                        if reference in state["usable"]:
                            conflicts.add(reference)
        checked[name] = _sanity_summary(rows)
    state["sanity"] = checked
    for name in sorted(conflicts):
        state["bones"][name] = {
            **state["bones"][name],
            "status": "conflict",
            "code": "anatomical_relation_conflict",
            "anatomical_sanity": checked[name],
        }
        state["usable"].pop(name, None)
        state["geometry"].pop(name, None)
    if not state["usable"]:
        state["route"] = EXISTING_ROUTE
        if conflicts:
            state["source"]["route_reason"] = "anatomical_anchor_conflict"


def locate_anatomy_first(
    study: dict,
    memory: dict,
    deadline: float | None = None,
    *,
    refine_finalists: bool = True,
) -> dict:
    """Locate bones by their structural anchors and place the rest from them.

    Only finite candidates are scored, and only to choose among them; a bounded
    exact tie set is refined. Without a usable structural anchor the existing
    finite route runs unchanged, named (module note).

    ``refine_finalists`` False defers every territory-v2 object's 2 mm reading to the
    question that asks for it, a bone's territory with a native mask included. The
    original of each such territory read is kept by reference on the runtime ``study``
    (``NATIVE_SUPPORT_RETAINED``; never in the result) for that question. Nothing that
    places an object changes: candidates, ties, territories, key planes and source
    addresses are the same either way.
    """
    # A new location owns only the mask-bearing territories it reads and leaves
    # to its questions. Clear a previous invocation before any early return.
    study.pop(NATIVE_SUPPORT_RETAINED, None)
    cases = memory.get("cases", ())
    case_rows = (
        list(cases)
        if isinstance(cases, Sequence) and not isinstance(cases, (str, bytes))
        else []
    )
    territory_v2 = memory.get("procedure") == TERRITORY_PROCEDURE or any(
        isinstance(row, Mapping)
        and shared._source(row.get("profile")).get("procedure") == TERRITORY_PROCEDURE
        for row in case_rows
    )
    procedure = (
        TERRITORY_PROCEDURE if territory_v2 else "knee.squint-profile/scan-tercile-v1"
    )
    known = sorted(
        {
            row.get("subject")
            for row in case_rows
            if isinstance(row, Mapping)
            and isinstance(row.get("subject"), str)
            and not row["subject"].startswith("diagnosis/")
        }
    )
    declared = memory.get("objects", ())
    if isinstance(declared, Sequence) and not isinstance(declared, (str, bytes)):
        known.extend(
            name
            for name in declared
            if isinstance(name, str)
            and not name.startswith("diagnosis/")
            and name not in known
        )
    objects: dict[str, dict[str, Any]] = {
        name: {
            "status": "unresolved_missing_reading",
            "profile": None,
            "candidate_profiles": [],
            "regions": [],
            "evidence": {"reason": "no_anatomical_windows_available"},
        }
        for name in known
    }
    series, series_uids = shared._profile_candidates(study)
    series = [row if isinstance(row, dict) else dict(row) for row in series]
    if not series:
        return {
            "outcome": "unresolved_missing_reading",
            "study_uid": study.get("study_uid"),
            "objects": objects,
            "evidence": {"series_uids": series_uids, "candidate_profiles_compared": 0},
        }
    bounds_by_series: dict[int, tuple[Any, Any, np.ndarray]] = {}
    foreground_by_series: dict[int, np.ndarray] = {}
    leg_bounds_lps = None
    foreground_prepared = False
    from knee.diagnosis.squint_profiles import profile_window

    raw_side = study.get("knee_side")
    knee_side = raw_side if raw_side in {"left", "right"} else None
    priorities = memory.get("object_order", ())
    priorities = (
        priorities
        if isinstance(priorities, Sequence) and not isinstance(priorities, (str, bytes))
        else ()
    )
    ordered = shared._object_order(
        known, priorities, {"femur", "tibia", "fibula", "patella"}
    )
    series_by_uid: dict[str, dict[str, Any]] = {
        row["series_uid"]: row
        for row in series
        if isinstance(row.get("series_uid"), str)
    }
    coarse_indexes = (
        {} if territory_v2 else {id(row): shared._coarse_index(row) for row in series}
    )
    calibrations: dict[str, Any] = {}
    if territory_v2:
        from knee.diagnosis.squint_profiles import leg_calibration

        for uid, row in series_by_uid.items():
            if deadline is not None and time.monotonic() >= deadline:
                calibrations[uid] = "deadline_before_leg_calibration"
                continue
            leg = row.get("leg_map")
            if not isinstance(leg, dict):
                calibrations[uid] = "leg_calibration_unavailable:leg_map_schema_invalid"
                continue
            try:
                calibrations[uid] = leg_calibration(row, leg)
            except (TypeError, ValueError) as error:
                calibrations[uid] = f"leg_calibration_unavailable:{error}"
    geometry_by_subject: dict[str, dict[str, Any]] = {}
    exact_refinements = 0
    # What the runtime study keeps is what this location reads and leaves to a question
    # (module note): nothing from an earlier location, and nothing when it pairs now.
    retained_support: list[Mapping[str, Any]] | None = None if refine_finalists else []
    anchor_state = study_anchors(study, series_by_uid, deadline=deadline)
    _check_anchor_sanity(anchor_state, series_by_uid, knee_side)
    structural = anchor_state["route"] == STRUCTURAL_ROUTE
    structural_geometry: dict[str, dict[str, Any]] = anchor_state["geometry"]
    if structural:
        route_evidence: dict[str, Any] = {
            "location_route": "anatomical_relation_from_structural_anchors",
            "structural_anchors": {
                name: anchor_state["bones"][name]["status"]
                for name in sorted(structural_geometry)
            },
        }
    else:
        route_evidence = {
            "location_route": EXISTING_ROUTE,
            "anchor_source": _json_safe(anchor_state["source"]),
        }

    for subject in ordered:
        subject_refinement_start = exact_refinements
        if deadline is not None and time.monotonic() >= deadline:
            objects[subject]["evidence"] = {
                "reason": "deadline_before_search",
                "deadline_reached": True,
                **route_evidence,
            }
            if structural:
                objects[subject]["territories"] = []
            continue
        if structural and subject in anchor_state["usable"]:
            objects[subject] = _anchored_object(
                subject,
                anchor_state["usable"][subject],
                anchor_state["bones"][subject],
                structural_geometry[subject],
                series_by_uid,
                calibrations if territory_v2 else None,
                deadline,
                refine_finalists=refine_finalists,
                retained_support=retained_support,
            )
            objects[subject]["sanity"] = anchor_state["sanity"].get(
                subject, _sanity_summary([])
            )
            geometry_by_subject[subject] = structural_geometry[subject]
            continue
        if structural:
            # Only structural anchors place another object; a bone located by
            # resemblance anchors nothing (thesis §11.1).
            anchors = {
                name: item
                for name, item in structural_geometry.items()
                if name != subject
            }
        else:
            anchors = {
                name: item
                for name, item in geometry_by_subject.items()
                if name in {"femur", "tibia", "patella", "fibula"}
                and isinstance(item, Mapping)
                and isinstance(item.get("reference"), Mapping)
                and item["reference"].get("status") in {"complete", "partial"}
            }
        # The atlas scale is femoral breadth. A femur–tibia reference
        # separation is not that measurement, so authored spans remain
        # unscaled until a real breadth measurement is available.
        knee_scale_mm = None
        # The old exemplar-offset slabs could inherit wrongly named teaching
        # locations. The authored map generates the finite windows; observed
        # anatomy checks their plausibility before any resemblance is computed.
        relative_priors = {
            "status": "not_used_for_eligibility",
            "reason": "authored_map_and_observed_anatomical_relations",
            "cases": [],
        }
        sanity_by_region: dict[tuple[Any, ...], dict[str, Any]] = {}
        scope_evidence = []
        proposal_evidence = []
        scope_code_counts: dict[str, int] = {}
        view_costs: dict[str, dict[str, Any]] = {}
        coarse_by_view: dict[tuple[str, str, str] | None, list[dict[str, Any]]] = {}
        has_compatible_precedent = False
        candidate_territories: dict[str, dict[str, Any]] = {}
        territory_by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
        coarse_readings: list[dict[str, Any]] = []
        reading_refusals: list[dict[str, Any]] = []
        finalists_paired = finalists_deferred = 0

        for series_record in series:
            stack = series_record.get("stack")
            median = getattr(stack, "median", None)
            if (
                not isinstance(median, np.ndarray)
                or getattr(stack, "code", None) != "present"
            ):
                continue
            view = shared._view_key(series_record.get("view"))
            scoped, _examples, scope_name = shared._location_scope(
                case_rows, subject, view
            )
            scope_evidence.append(
                {
                    "view": None if view is None else list(view),
                    "source": scope_name,
                    "case_ids": [
                        row.get("case_id")
                        for row in scoped
                        if isinstance(row.get("case_id"), str)
                    ],
                }
            )
            compatible = [
                row
                for row in scoped
                if shared._source(row.get("profile")).get("procedure") == procedure
            ]
            if not compatible:
                continue
            has_compatible_precedent = True
            if territory_v2 and not isinstance(
                calibrations.get(series_record.get("series_uid")), tuple
            ):
                reading_refusals.append(
                    {
                        "series_uid": series_record.get("series_uid"),
                        "reason": calibrations.get(series_record.get("series_uid")),
                    }
                )
                continue
            if not foreground_prepared:
                bounds_by_series = {
                    id(row): shared._leg_bounds(row.get("stack"), row.get("leg_map"))
                    for row in series
                    if getattr(row.get("stack"), "code", None) == "present"
                    and isinstance(
                        getattr(row.get("stack"), "median", None), np.ndarray
                    )
                }
                foreground_by_series = {
                    key: value[2] for key, value in bounds_by_series.items()
                }
                leg_bounds_lps = shared._current_leg_frame_prior(
                    series, foreground_by_series
                )
                foreground_prepared = True
            foreground = foreground_by_series[id(series_record)]
            if structural or territory_v2:
                built = dependent_territories(
                    series_record,
                    subject,
                    study_uid=study.get("study_uid"),
                    anchors=anchors,
                    leg_bounds_lps=leg_bounds_lps,
                    foreground=foreground,
                    knee_side=knee_side,
                    knee_scale_mm=knee_scale_mm,
                )
                proposal = built["proposal"]
                windows = []
                for territory in built["territories"]:
                    window = _object_window(territory)
                    assert window is not None
                    territory_by_key[(series_record.get("series_uid"), window)] = (
                        territory
                    )
                    windows.append(window)
                candidate_territories[str(series_record.get("series_uid"))] = {
                    "origin": built["origin"],
                    "proposal_status": _json_safe(built["status"]),
                    "proposed_windows": built["proposed_window_count"],
                    "territories": len(windows),
                    "candidate_object_windows": [list(window) for window in windows],
                    "refusals": built["refusals"],
                    "leg_prior": built["leg_prior"],
                }
            else:
                proposal = shared._anatomical_window_proposal(
                    series_record,
                    subject,
                    leg_bounds_lps=leg_bounds_lps,
                    foreground=foreground,
                    anchors=anchors,
                    knee_side=knee_side,
                    knee_scale_mm=knee_scale_mm,
                )
                windows = proposal.get("windows", ())
            proposal_evidence.append(
                {
                    "series_uid": series_record.get("series_uid"),
                    "status": proposal.get("status"),
                    "reason": proposal.get("reason"),
                    "relative_scope_check": "direct_finite_candidate_scope_check",
                    "provenance": proposal.get("provenance", {}),
                    "window_count": len(proposal.get("windows", ())),
                }
            )
            view_id = json.dumps(view, separators=(",", ":"))
            cost = view_costs.setdefault(
                view_id,
                {
                    "view": None if view is None else list(view),
                    "windows_proposed": 0,
                    "windows_scored": 0,
                    "full_profiles_materialized": 0,
                    "relative_scope_check": "direct_finite_candidate_scope_check",
                    "anatomical_proposal_status": proposal.get("status", "unavailable"),
                },
            )
            cost.setdefault("proposal_sources", []).append(
                {
                    "series_uid": series_record.get("series_uid"),
                    "status": proposal.get("status", "unavailable"),
                    "relative_scope_check": "direct_finite_candidate_scope_check",
                }
            )
            cost["windows_proposed"] += len(windows)
            if not windows:
                continue
            sanity_rows = window_sanity_checks(
                series_record, subject, windows, anchors, knee_side
            )
            for row in sanity_rows:
                row["series_uid"] = series_record.get("series_uid")
                sanity_by_region[(row["series_uid"], tuple(row["window"]))] = row
            scope_codes = [row["status"] for row in sanity_rows]
            for code in scope_codes:
                scope_code_counts[code] = scope_code_counts.get(code, 0) + 1
            eligible = [
                window
                for window, code in zip(windows, scope_codes, strict=True)
                if code != "contradicted"
                and foreground[
                    window[0] : window[1], window[2] : window[3], window[4] : window[5]
                ].any()
            ]
            if not eligible:
                continue
            cost["windows_scored"] += len(eligible)
            profiles_by_window = {}
            terms_by_window = {}
            if territory_v2:
                precedent_banks = [
                    _object_coarse_banks(row.get("profile")) for row in compatible
                ]
                matrix = shared._case_matrix(precedent_banks)
                scores = []
                for window in eligible:
                    if deadline is not None and time.monotonic() >= deadline:
                        break
                    territory = territory_by_key[(series_record["series_uid"], window)]
                    profile = _territory_profile(
                        series_record,
                        territory,
                        calibrations[series_record["series_uid"]],
                    )
                    profiles_by_window[window] = profile
                    coarse_readings.append(
                        {
                            "series_uid": series_record["series_uid"],
                            "window": list(window),
                            "profile": profile,
                        }
                    )
                    terms = shared._batch_terms(
                        _object_coarse_banks(profile),
                        precedent_banks,
                        matrix_cache=matrix,
                    )
                    terms_by_window[window] = terms
                    scores.append(
                        [
                            term["cosine_squared"]
                            if term and term["code"] == "ok"
                            else None
                            for term in terms
                        ]
                    )
                eligible = eligible[: len(scores)]
            else:
                names, integrals = coarse_indexes[id(series_record)]
                if not names:
                    continue
                precedent_banks = [
                    shared._banks(row.get("profile")) for row in compatible
                ]
                case_vectors, case_masks = shared._case_coarse_matrix(
                    compatible, names, precedent_banks
                )
                query_vectors, query_masks = shared._window_coarse_batch(
                    names, integrals, eligible
                )
                scores = shared._coarse_case_scores_batch(
                    query_vectors, query_masks, case_vectors, case_masks
                )
            rows = coarse_by_view.setdefault(view, [])
            for window, row_scores in zip(eligible, scores, strict=True):
                scored = [
                    (index, score)
                    for index, score in enumerate(row_scores)
                    if score is not None
                ]
                if not scored:
                    continue
                best = scored[0][1]
                for _index, score in scored[1:]:
                    if score[0] * best[1] > best[0] * score[1]:
                        best = score
                case_ids = sorted(
                    {
                        compatible[index]["case_id"]
                        for index, score in scored
                        if score[0] * best[1] == best[0] * score[1]
                        and isinstance(compatible[index].get("case_id"), str)
                    }
                )
                rows.append(
                    {
                        "window": tuple(window),
                        "series": series_record,
                        "coarse_score": best,
                        "case_ids": case_ids,
                        "centre_lps": shared._window_centre_lps(series_record, window),
                        **(
                            {
                                "coarse_profile": profiles_by_window[window],
                                "location_cases": compatible,
                                "location_terms": terms_by_window[window],
                            }
                            if territory_v2
                            else {}
                        ),
                    }
                )

        exact_by_view: dict[tuple[str, str, str] | None, dict[str, Any]] = {}
        unresolved_coarse: dict[str, Any] = {}
        coarse_finalists: dict[str, Any] = {}
        case_best: dict[str, dict[str, Any]] = {}
        for view, candidates in coarse_by_view.items():
            if not candidates:
                continue
            best = candidates[0]["coarse_score"]
            for candidate in candidates[1:]:
                score = candidate["coarse_score"]
                if score[0] * best[1] > best[0] * score[1]:
                    best = score
            tied = [
                candidate
                for candidate in candidates
                if candidate["coarse_score"][0] * best[1]
                == best[0] * candidate["coarse_score"][1]
            ]
            view_id = json.dumps(view, separators=(",", ":"))
            coarse_finalists[view_id] = {
                "view": None if view is None else list(view),
                "candidate_count": len(tied),
                "coarse_best_squared_similarity": {
                    "numerator": str(best[0]),
                    "denominator": str(best[1]),
                },
                "candidates": [
                    {
                        "series_uid": item["series"].get("series_uid"),
                        "window": list(item["window"]),
                        "case_ids": item["case_ids"],
                        "centre_lps": item["centre_lps"],
                    }
                    for item in tied
                ],
            }
            if len(tied) > shared._MAX_EXACT_REFINEMENTS_PER_VIEW:
                unresolved_coarse[view_id] = {
                    "status": "unresolved_refinement_budget_exceeded",
                    "candidate_count": len(tied),
                    "max_exact_refinements": shared._MAX_EXACT_REFINEMENTS_PER_VIEW,
                    "coarse_best_squared_similarity": {
                        "numerator": str(best[0]),
                        "denominator": str(best[1]),
                    },
                    "candidates": coarse_finalists[view_id]["candidates"],
                }
                continue
            refined = []
            for candidate in tied:
                if deadline is not None and time.monotonic() >= deadline:
                    break
                series_record = candidate["series"]
                full = True  # a v1 candidate is always written in full
                if territory_v2:
                    territory = territory_by_key[
                        (series_record["series_uid"], candidate["window"])
                    ]
                    full = refine_finalists
                    profile = _territory_profile(
                        series_record,
                        territory,
                        calibrations[series_record["series_uid"]],
                        coarse=candidate["coarse_profile"],
                        refine=full,
                        deadline=deadline,
                    )
                    if full:
                        finalists_paired += 1
                    else:
                        finalists_deferred += 1
                    query = _object_coarse_banks(profile)
                else:
                    profile = profile_window(
                        dict(series_record), candidate["window"], subject=subject
                    )
                    query = shared._banks(profile)
                if query is None:
                    continue
                view_id = json.dumps(view, separators=(",", ":"))
                if view_id in view_costs and full:
                    view_costs[view_id]["full_profiles_materialized"] += 1
                if territory_v2:
                    # Fine banks do not enter location resemblance. These exact
                    # object/10 mm terms were already computed for this candidate.
                    exact_cases = candidate["location_cases"]
                    evidence = candidate["location_terms"]
                else:
                    scoped, _examples, _scope_name = shared._location_scope(
                        case_rows, subject, view
                    )
                    exact_cases = [
                        row
                        for row in scoped
                        if shared._source(row.get("profile")).get("procedure")
                        == shared._source(profile).get("procedure")
                    ]
                    banks = [shared._banks(row.get("profile")) for row in exact_cases]
                    evidence = shared._batch_terms(
                        query, banks, compatible=[True] * len(exact_cases)
                    )
                usable = [
                    (row, item)
                    for row, item in zip(exact_cases, evidence, strict=True)
                    if item is not None and item.get("code") == "ok"
                ]
                if not usable:
                    continue
                exact_best = usable[0][1]["cosine_squared"]
                for _row, item in usable[1:]:
                    score = item["cosine_squared"]
                    if score[0] * exact_best[1] > exact_best[0] * score[1]:
                        exact_best = score
                for source_case, item in usable:
                    case_id = source_case.get("case_id")
                    if not isinstance(case_id, str):
                        continue
                    score = item["cosine_squared"]
                    record = {
                        "profile": profile,
                        "series_uid": series_record.get("series_uid"),
                        "view": series_record.get("view"),
                        "window": candidate["window"],
                        "centre_lps": candidate["centre_lps"],
                    }
                    previous = case_best.get(case_id)
                    if (
                        previous is None
                        or score[0] * previous["score"][1]
                        > previous["score"][0] * score[1]
                    ):
                        case_best[case_id] = {"score": score, "items": [record]}
                    elif (
                        score[0] * previous["score"][1]
                        == previous["score"][0] * score[1]
                    ):
                        previous["items"].append(record)
                refined.append(
                    (
                        {
                            "subject": subject,
                            "window": candidate["window"],
                            "centre_lps": candidate["centre_lps"],
                            "profile": profile,
                        },
                        series_record,
                        exact_best,
                    )
                )
                exact_refinements += 1
            if not refined:
                continue
            exact_best = refined[0][2]
            for _candidate, _series_record, score in refined[1:]:
                if score[0] * exact_best[1] > exact_best[0] * score[1]:
                    exact_best = score
            exact_ties = [
                (item, row)
                for item, row, score in refined
                if score[0] * exact_best[1] == exact_best[0] * score[1]
            ]
            exact_by_view[view] = {"score": exact_best, "items": exact_ties}

        structural_evidence: dict[str, Any] = (
            {"candidate_territories": candidate_territories}
            if structural or territory_v2
            else {}
        )
        structural_evidence["anatomical_sanity_checks"] = list(
            sanity_by_region.values()
        )
        structural_evidence["eligibility_source"] = "authored_anatomical_relations"
        if territory_v2:
            coarse_catalog = shared._intern_candidate_profiles(coarse_readings, [])
            structural_evidence.update(
                profile_procedure=procedure,
                resemblance_banks="object_role_10mm_only",
                reading_refusals=reading_refusals,
                coarse_readings=coarse_readings,
                coarse_reading_catalog=coarse_catalog,
            )
            if not refine_finalists:
                structural_evidence["fine_reading"] = {
                    "policy": FINE_READING_DEFERRED,
                    "requested_at_location": finalists_paired,
                    "deferred": finalists_deferred,
                }
        if territory_v2 and subject in BONES and subject not in anchor_state["usable"]:
            structural_evidence["unanchored_bone"] = anchor_state["bones"].get(
                subject,
                {"status": "unavailable", "code": anchor_state["source"]["status"]},
            )
        if not exact_by_view:
            objects[subject] = {
                "status": "unresolved_candidate_tie"
                if unresolved_coarse
                else "unresolved_missing_reading",
                "profile": None,
                "candidate_profiles": [],
                "regions": [],
                "evidence": {
                    "reason": "coarse_ties_exceed_refinement_budget"
                    if unresolved_coarse
                    else "no_compatible_anatomical_candidates"
                    if has_compatible_precedent
                    else "no_compatible_current_study_candidates",
                    "coarse_ties": unresolved_coarse,
                    "coarse_finalists": coarse_finalists,
                    "proposal_sources": proposal_evidence,
                    "location_precedent_scopes": scope_evidence,
                    "location_scope_codes": dict(sorted(scope_code_counts.items())),
                    "relative_scope_priors": relative_priors,
                    "candidate_costs_by_view": view_costs,
                    "leg_frame_prior": leg_bounds_lps is not None,
                    **route_evidence,
                    **structural_evidence,
                },
            }
            if structural or territory_v2:
                objects[subject]["territories"] = []
            continue
        candidate_profiles = []
        geometry_regions = []
        chosen_profiles = []
        for group in exact_by_view.values():
            for candidate, series_record in group["items"]:
                candidate_profiles.append(
                    {
                        "profile": candidate["profile"],
                        "series_uid": series_record.get("series_uid"),
                        "view": series_record.get("view"),
                        "window": candidate.get("window"),
                        "squared_similarity": {
                            "numerator": str(group["score"][0]),
                            "denominator": str(group["score"][1]),
                        },
                    }
                )
                geometry_regions.append(
                    {
                        "series_uid": series_record.get("series_uid"),
                        "view": series_record.get("view"),
                        "window": candidate.get("window"),
                    }
                )
            if len(group["items"]) == 1:
                chosen_profiles.append(group["items"][0][0]["profile"])
        spatial = object_geometry(subject, geometry_regions, series_by_uid)
        geometry_by_subject[subject] = spatial
        merged = None
        if chosen_profiles:
            try:
                from knee.diagnosis.squint_profiles import merge_profiles

                merged = merge_profiles(chosen_profiles, subject=subject)
            except (ImportError, ValueError):
                if len(chosen_profiles) == 1:
                    merged = chosen_profiles[0]
        best_candidates = [
            {
                "case_id": case_id,
                "squared_similarity": {
                    "numerator": str(row["score"][0]),
                    "denominator": str(row["score"][1]),
                },
                "candidates": row["items"],
            }
            for case_id, row in sorted(case_best.items())
        ]
        catalog = shared._intern_candidate_profiles(candidate_profiles, best_candidates)
        objects[subject] = {
            "status": "proposal",
            "sanity": _sanity_summary(
                [
                    sanity_by_region[(region["series_uid"], tuple(region["window"]))]
                    for region in geometry_regions
                ]
            ),
            "profile": merged,
            "candidate_profiles": candidate_profiles,
            "regions": geometry_regions,
            "evidence": {
                "source": "current_study_anatomy_first_finite_windows",
                "candidate_view_count": len(exact_by_view),
                "selected_view_regions": len(chosen_profiles),
                "candidate_profiles_compared": exact_refinements
                - subject_refinement_start,
                "supporting_case_count": sum(
                    row.get("subject") == subject
                    for row in case_rows
                    if isinstance(row, Mapping)
                ),
                "location_scope_codes": dict(sorted(scope_code_counts.items())),
                "location_precedent_scopes": scope_evidence,
                "proposal_sources": proposal_evidence,
                "coarse_ties": unresolved_coarse,
                "coarse_finalists": coarse_finalists,
                "spatial_constraints": spatial,
                "relative_scope_priors": relative_priors,
                "anchor_reference_scope": "structural_anchor_references_only"
                if structural
                else "resolved_native_bone_references_only",
                "candidate_costs_by_view": view_costs,
                "case_best_candidates": best_candidates,
                "candidate_profile_catalog": catalog["profiles"],
                "candidate_bank_catalog": catalog["banks"],
                "candidate_series_context_catalog": catalog["series_contexts"],
                "patient_coordinates_carried": False,
                "leg_frame_prior": "measured_current_foreground_bounds_used_only_as_initial_reference_origin"
                if leg_bounds_lps is not None
                else "unavailable",
                **route_evidence,
                **structural_evidence,
            },
        }
        if structural or territory_v2:
            # One territory per region, in the same order: what was read where.
            objects[subject]["territories"] = [
                territory_record(
                    territory_by_key[(region["series_uid"], tuple(region["window"]))]
                )
                for region in geometry_regions
            ]
            if territory_v2:
                for region, record in zip(
                    geometry_regions, objects[subject]["territories"], strict=True
                ):
                    region["territory"] = record
    if retained_support:
        study[NATIVE_SUPPORT_RETAINED] = retained_support
    study_evidence = {
        "series_uids": series_uids,
        "candidate_profiles_compared": exact_refinements,
        "candidate_generation": "finite_anatomy_first",
        "anchors": _json_safe(
            {
                "route": anchor_state["route"],
                "source": anchor_state["source"],
                "bones": anchor_state["bones"],
                "anatomical_sanity": anchor_state.get("sanity", {}),
            }
        ),
    }
    if territory_v2 and not refine_finalists:
        study_evidence["fine_reading"] = FINE_READING_DEFERRED
    return {
        "outcome": "located_with_proposals",
        "study_uid": study.get("study_uid"),
        "objects": objects,
        "evidence": study_evidence,
    }


__all__ = [
    "BONES",
    "CONTEXT_RING_TILES",
    "EXISTING_ROUTE",
    "FINE_READING_DEFERRED",
    "NATIVE_SUPPORT_RETAINED",
    "STRUCTURAL_ROUTE",
    "TERRITORY_RECORD_SERIALIZATION",
    "USABLE_ANCHOR_STATUSES",
    "dependent_territories",
    "locate_anatomy_first",
    "resolve_anchor_views",
    "retained_native_territory",
    "study_anchors",
    "territory_from_record",
    "territory_record",
]
