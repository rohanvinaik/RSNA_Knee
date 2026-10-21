"""Advisory anatomical plausibility checks for candidate object windows.

This module only categorizes. It never asserts identity, never rejects or
removes a window, and never changes a high-resolution measurement. Unknown
evidence stays unknown and the window stays eligible.

A reference supplies an interval only on an LPS axis its own record determines
(``docs/RELATIVE_POSITION_MAP.md`` §8.8: each key plane is one physical depth
constraint; oblique planes are solved, never read by their orientation label;
``docs/CLASSICAL_AI_BUILD_DESIGN.md`` §7.2 for the order below). For a
``complete`` or ``partial`` record, in this order:

1. A complete reference with a usable point and precision supplies its measured
   point +/- its recorded precision, exactly as before; its planes and windows
   are not reread.
2. Otherwise the record's selected planes supply an interval only on an axis
   that lies in the row space of their normals. That test is the floating-
   precision rank ``knee.collapse.relative.reference_position`` already uses
   for singular planes, not an anatomical or angular threshold. The interval is
   the solved coordinate ``w . d`` +/- ``sum |w_i| precision_i`` over the
   planes that determine the axis: with three planes this is row ``a`` of
   ``N^-1`` and ``|N^-1| @ precision``, the complete construction itself. A
   plane whose normal is exactly one axis gives that axis its own offset +/-
   its precision; an oblique plane determines no single LPS axis.
3. Otherwise the anchor's own observed tile windows (its record's ``regions``)
   supply the exact projection of their tiles onto the axis, made by
   ``squint_geometry._candidate_interval``, the same function that projects the
   candidate's window: its windows in the candidate's own series when it has
   any, else the union over its series, which can only add overlap. Every
   chosen window must project, or the axis stays unknown.
4. An anchor with no usable window stays unknown, by name.

Every other status stays unknown. Each check records which reference status
supplied it, how (``reference_construction``), from which planes with their
weights (``reference_planes``) or which series' windows with their projected
intervals (``reference_windows``), and why each earlier step supplied nothing
(``reference_fallbacks``). No tolerance or map distance enters. A pass remains a
location statement only.
"""

from __future__ import annotations

import copy
import itertools
import math
from collections.abc import Mapping, Sequence
from numbers import Real
from typing import Any

import numpy as np

from knee.collapse import relative
from knee.collapse.anatomical_relations import RELATIONSHIPS
from knee.diagnosis import squint_geometry

SOURCE = "docs/OBJECTS_AND_CONDITIONS.md §4"

#: How a check's target interval was obtained (``reference_construction``).
COMPLETE_CONSTRUCTION = "complete_reference_point_and_precision"
PARTIAL_CONSTRUCTION = "partial_reference_selected_planes"
COMPLETE_PLANES_CONSTRUCTION = "complete_reference_selected_planes"
WINDOW_CONSTRUCTION = "anchor_window_projection"

_RELATIONS = ("strictly_before", "strictly_after")
_OPPOSITE = {"strictly_before": "strictly_after", "strictly_after": "strictly_before"}
_AXES = {"x": (1.0, 0.0, 0.0), "y": (0.0, 1.0, 0.0), "z": (0.0, 0.0, 1.0)}
_AXIS_INDEX = {"x": 0, "y": 1, "z": 2}

# predicate -> (LPS axis, fixed expected relation or None, side term or None)
_PREDICATES = {
    "superior_to": ("z", "strictly_after", None),
    "anterior_to": ("y", "strictly_before", None),
    "posterior_to": ("y", "strictly_after", None),
    "lateral_to": ("x", None, "lateral"),
    "medial_to": ("x", None, "medial"),
}

# subject, predicate, target: the specifically supplied rules of §4
_DIRECT_RULES = (
    ("femur", "superior_to", "tibia"),
    ("patella", "anterior_to", "femur"),
    ("medial_gastrocnemius", "posterior_to", "femur"),
    ("lateral_gastrocnemius", "posterior_to", "femur"),
    ("fibula", "lateral_to", "tibia"),
)


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def _valid_interval(value: object) -> tuple[float, float] | None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return None
    if len(value) != 2:
        return None
    low, high = _number(value[0]), _number(value[1])
    if low is None or high is None or low > high:
        return None
    return low, high


def interval_relation_code(candidate_interval, target_interval, relation):
    """Name how a candidate interval stands to a target for an expected direction.

    Intervals are closed, finite, valid (low, high) bounds with low <= high.
    Strictly before means candidate.high < target.low; strictly after means
    candidate.low > target.high. Equal endpoints and any overlap are
    overlapping. No tolerance or epsilon is applied. ``relation`` is the
    expected direction: ``strictly_before`` or ``strictly_after``.

    Returned codes:
      supported_strictly_before - expected before, candidate is strictly before
      supported_strictly_after  - expected after, candidate is strictly after
      reversed_strictly_before  - expected before, candidate is strictly after
      reversed_strictly_after   - expected after, candidate is strictly before
      overlap_or_touching       - intervals overlap or touch at an endpoint
      unknown                   - malformed, reversed, nonfinite or missing
                                  bounds, or an unsupported relation
    """
    if not isinstance(relation, str) or relation not in _RELATIONS:
        return "unknown"
    candidate = _valid_interval(candidate_interval)
    target = _valid_interval(target_interval)
    if candidate is None or target is None:
        return "unknown"
    if candidate[1] < target[0]:
        actual = "strictly_before"
    elif candidate[0] > target[1]:
        actual = "strictly_after"
    else:
        return "overlap_or_touching"
    if actual == relation:
        return "supported_" + relation
    return "reversed_" + relation


def _side(knee_side: object) -> str | None:
    if not isinstance(knee_side, str):
        return None
    key = knee_side.strip().lower()
    return key if key in ("left", "right") else None


def _expected(predicate: str, knee_side: object) -> tuple[str, str | None]:
    axis, relation, term = _PREDICATES[predicate]
    if term is None:
        return axis, relation
    side = _side(knee_side)
    if side is None:
        return axis, None
    # In LPS, patient-left is +x: a left knee has lateral at larger x.
    lateral_after = side == "left"
    if term == "medial":
        lateral_after = not lateral_after
    return axis, "strictly_after" if lateral_after else "strictly_before"


def _rules() -> list[tuple[str, str, str, str, str]]:
    rules = [
        ("authored", subject, predicate, target, SOURCE)
        for subject, predicate, target in _DIRECT_RULES
    ]
    seen = set(_DIRECT_RULES)
    for subject, predicate, targets, _qualifier, source in RELATIONSHIPS:
        if predicate not in _PREDICATES:
            continue
        for target in targets:
            if (subject, predicate, target) in seen:
                continue
            seen.add((subject, predicate, target))
            rules.append(("relationship", subject, predicate, target, source))
    return rules


def _complete_interval(reference: Mapping, axis: str):
    """Measured point +/- precision on one axis of a complete reference."""
    point = reference.get("point_lps")
    precision = reference.get("precision_mm")
    for value in (point, precision):
        if (
            not isinstance(value, Sequence)
            or isinstance(value, (str, bytes))
            or len(value) != 3
        ):
            return None
    centre = [_number(value) for value in point]
    reach = [_number(value) for value in precision]
    if any(v is None for v in centre) or any(v is None or v < 0 for v in reach):
        return None
    index = _AXIS_INDEX[axis]
    return _valid_interval((centre[index] - reach[index], centre[index] + reach[index]))


def _selected_names(record: Mapping) -> list[dict[str, Any]]:
    """The selected planes a reference record names, by orientation."""
    planes = record.get("planes")
    if not isinstance(planes, Mapping):
        return []
    named = []
    for orientation in relative.ORIENTATIONS:
        address = planes.get(orientation)
        if isinstance(address, Mapping) and address.get("outcome") == relative.SELECTED:
            named.append(
                {
                    "orientation": orientation,
                    "series_uid": address.get("series_uid"),
                    "slice": address.get("slice"),
                }
            )
    return named


def _plane_row(orientation: str, address: Mapping) -> dict[str, Any] | None:
    """One selected plane as unit normal, matching offset and precision.

    ``n . p = d`` holds for the normal as given, so a non-unit normal and its
    offset are rescaled together (as ``relative.key_plane`` does). A normal
    that is not three finite numbers, all zero, or an offset that is not a
    finite number, is malformed (None). A precision that is not a finite
    nonnegative number is unknown.
    """
    raw = address.get("normal")
    if isinstance(raw, np.ndarray):
        raw = raw.tolist()
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)) or len(raw) != 3:
        return None
    values = [_number(value) for value in raw]
    offset = _number(address.get("offset_mm"))
    if any(value is None for value in values) or offset is None:
        return None
    normal = np.asarray(values, dtype=np.float64)
    big = float(np.max(np.abs(normal)))
    # Exact on purpose: only an all-zero normal cannot be scaled by its maximum.
    if big == 0.0:  # NOSONAR(S1244)
        return None
    scaled = normal / big
    length = float(np.linalg.norm(scaled))
    precision = _number(address.get("precision_mm"))
    return {
        "orientation": orientation,
        "series_uid": address.get("series_uid"),
        "slice": address.get("slice"),
        "normal": scaled / length,
        "offset_mm": (offset / big) / length,
        "precision_mm": precision if precision is not None and precision >= 0 else None,
    }


def _rank(rows: np.ndarray) -> int:
    """Rank at floating precision: the tolerance of ``relative.reference_position``."""
    singular = np.linalg.svd(rows, compute_uv=False)
    if not singular.size or not float(singular[0]) > 0:
        return 0
    return int(np.sum(singular > float(singular[0]) * max(rows.shape) * relative.EPS))


def _planes_interval(record: Mapping, axis: str, prefix: str):
    """(interval, construction code, planes) on one LPS axis from selected planes.

    The axis is determined only when it lies in the row space of the selected
    planes' normals; then the smallest set of planes whose span holds it gives
    the solved coordinate and its precision bound. Dependent (parallel)
    planes, a malformed selected plane, or an unknown precision on a plane the
    axis needs supply nothing, by name. Codes carry the record's status as
    ``prefix`` (``partial_reference_`` or ``complete_reference_``).
    """
    planes = record.get("planes")
    if not isinstance(planes, Mapping):
        return None, prefix + "without_selected_planes", []
    rows = []
    for orientation in relative.ORIENTATIONS:
        address = planes.get(orientation)
        if (
            not isinstance(address, Mapping)
            or address.get("outcome") != relative.SELECTED
        ):
            continue
        row = _plane_row(orientation, address)
        if row is None:
            return None, prefix + "plane_malformed", []
        rows.append(row)
    if not rows:
        return None, prefix + "without_selected_planes", []
    normals = np.asarray([row["normal"] for row in rows], dtype=np.float64)
    if _rank(normals) < len(rows):
        return None, prefix + "planes_dependent", []
    unit = np.zeros(3, dtype=np.float64)
    unit[_AXIS_INDEX[axis]] = 1.0
    for size in range(1, len(rows) + 1):
        for subset in itertools.combinations(range(len(rows)), size):
            chosen = normals[list(subset)]
            if _rank(np.vstack((chosen, unit))) != size:
                continue
            try:
                weights = np.linalg.solve(chosen @ chosen.T, chosen @ unit)
            except np.linalg.LinAlgError:
                return None, prefix + "planes_dependent", []
            used = [rows[index] for index in subset]
            if any(row["precision_mm"] is None for row in used):
                return None, prefix + "precision_unknown", []
            value = math.fsum(
                float(weight) * row["offset_mm"]
                for weight, row in zip(weights, used, strict=True)
            )
            reach = math.fsum(
                abs(float(weight)) * row["precision_mm"]
                for weight, row in zip(weights, used, strict=True)
            )
            interval = _valid_interval((value - reach, value + reach))
            if interval is None:
                return None, prefix + "interval_nonfinite", []
            return (
                interval,
                prefix + "selected_planes",
                [
                    {
                        "orientation": row["orientation"],
                        "series_uid": row["series_uid"],
                        "slice": row["slice"],
                        "normal": [float(value) for value in row["normal"]],
                        "offset_mm": float(row["offset_mm"]),
                        "precision_mm": float(row["precision_mm"]),
                        "weight": float(weight),
                    }
                    for weight, row in zip(weights, used, strict=True)
                ],
            )
    return None, prefix + "axis_not_constrained", []


def _observed_windows(record: Mapping) -> list[tuple[str, tuple]]:
    """The anchor's own observed tile windows, ``(series_uid, window)``, once each.

    They are the ``regions`` its record carries: a structural anchor's checked
    territories' object-tile boxes, or the windows a located object was found
    in. An entry without a series or a six-integer window is not a window.
    """
    regions = record.get("regions")
    if not isinstance(regions, Sequence) or isinstance(regions, (str, bytes)):
        return []
    found: list[tuple[str, tuple]] = []
    for region in regions:
        if not isinstance(region, Mapping):
            continue
        uid = region.get("series_uid")
        window = _window_tuple(region)
        usable = isinstance(uid, str) and uid and window is not None
        if usable and (uid, window) not in found:
            found.append((uid, window))
    return found


def _window_interval(record: Mapping, axis: str, series, series_by_uid):
    """(interval, construction code, windows) from the anchor's own observed windows.

    Each window is projected onto the axis by ``squint_geometry._candidate_interval``,
    the function that projects the candidate's window: every tile corner through
    its slice's own frame, widened by that slice's precision along the axis. The
    anchor's windows in the candidate's own series are used when it has any;
    otherwise all of its windows over its series. The interval is their union,
    which can only add overlap. A union missing a window could be narrower than
    what was observed, so every chosen window must project: a series that is not
    available, or a window that does not project, leaves the axis unknown, by name.
    """
    windows = _observed_windows(record)
    if not windows:
        return None, "anchor_without_window", []
    own_uid = series.get("series_uid") if isinstance(series, Mapping) else None
    own = [item for item in windows if isinstance(own_uid, str) and item[0] == own_uid]
    scope = "candidate_series" if own else "anchor_series_union"
    unit = np.asarray(_AXES[axis], dtype=np.float64)
    used = []
    for uid, window in own or windows:
        if uid == own_uid:
            source = series
        elif isinstance(series_by_uid, Mapping):
            source = series_by_uid.get(uid)
        else:
            source = None
        if not isinstance(source, dict):
            return None, "anchor_window_series_unavailable", []
        try:
            interval = _valid_interval(
                squint_geometry._candidate_interval(source, window, unit)
            )
        except (TypeError, ValueError, IndexError):
            interval = None
        if interval is None:
            return None, "anchor_window_projection_unavailable", []
        used.append(
            {
                "series_uid": uid,
                "window": list(window),
                "interval": list(interval),
                "scope": scope,
            }
        )
    low = min(item["interval"][0] for item in used)
    high = max(item["interval"][1] for item in used)
    return (low, high), WINDOW_CONSTRUCTION, used


def _supply(interval, status, construction, *, planes=(), windows=(), fallbacks=()):
    return {
        "interval": interval,
        "status": status,
        "construction": construction,
        "planes": list(planes),
        "windows": list(windows),
        "fallbacks": list(fallbacks),
    }


def _reference_supply(
    anchors: object, name: str, axis: str, series=None, series_by_uid=None
) -> dict[str, Any]:
    """The target interval one reference supplies on one axis, and from what.

    ``status`` is the reference record's own status (None without a record);
    ``construction`` names how the interval was made, or why none was;
    ``planes`` and ``windows`` hold what made it (empty when none was made);
    ``fallbacks`` names, in order, why each earlier step supplied nothing.
    """
    record = anchors.get(name) if isinstance(anchors, Mapping) else None
    reference = record.get("reference") if isinstance(record, Mapping) else None
    if not isinstance(reference, Mapping):
        return _supply(None, None, "no_reference")
    status = reference.get("status")
    if status not in (relative.COMPLETE, relative.PARTIAL):
        return _supply(
            None,
            status if isinstance(status, str) else None,
            "reference_status_supplies_no_interval",
        )
    fallbacks = []
    if status == relative.COMPLETE:
        interval = _complete_interval(reference, axis)
        if interval is not None:
            return _supply(
                interval, status, COMPLETE_CONSTRUCTION, planes=_selected_names(record)
            )
        fallbacks.append("complete_reference_point_or_precision_unusable")
    interval, construction, planes = _planes_interval(
        record, axis, f"{status}_reference_"
    )
    if interval is not None:
        return _supply(
            interval, status, construction, planes=planes, fallbacks=fallbacks
        )
    fallbacks.append(construction)
    interval, construction, windows = _window_interval(
        record, axis, series, series_by_uid
    )
    return _supply(interval, status, construction, windows=windows, fallbacks=fallbacks)


def _window_tuple(item: object) -> tuple | None:
    window = item.get("window") if isinstance(item, Mapping) else item
    if (
        isinstance(window, (tuple, list))
        and len(window) == 6
        and all(type(value) is int for value in window)
    ):
        return tuple(window)
    return None


def _candidate_axis_interval(series, window, axis, cache):
    if axis in cache:
        return cache[axis]
    interval = None
    if window is not None and isinstance(series, dict):
        unit = np.asarray(_AXES[axis], dtype=np.float64)
        try:
            interval = squint_geometry._candidate_interval(series, window, unit)
        except (TypeError, ValueError, IndexError):
            interval = None
    cache[axis] = _valid_interval(interval)
    return cache[axis]


def _check(
    origin,
    subject,
    predicate,
    target,
    source,
    role,
    axis,
    expected,
    candidate,
    reference,
    code,
):
    return {
        "rule_id": f"{origin}:{subject}:{predicate}:{target}",
        "source": source,
        "subject": subject,
        "target": target,
        "candidate_role": role,
        "axis": axis,
        "relation": predicate,
        "expected_relation": expected,
        "candidate_interval": None if candidate is None else list(candidate),
        "target_interval": None if reference is None else list(reference),
        "result": code,
    }


def _window_checks(
    series,
    candidate_subject,
    window,
    anchors,
    knee_side,
    rules,
    supplies,
    series_by_uid,
):
    cache: dict[str, Any] = {}
    checks = []
    for origin, subject, predicate, target, source in rules:
        if subject == candidate_subject:
            role, other = "subject", target
        elif target == candidate_subject:
            role, other = "target", subject
        else:
            continue
        axis, relation = _expected(predicate, knee_side)
        # A reference's interval does not depend on the candidate window (only on
        # the candidate's series, fixed for the call): made once per call.
        key = (other, axis)
        if key not in supplies:
            supplies[key] = _reference_supply(
                anchors, other, axis, series, series_by_uid
            )
        supply = supplies[key]
        reference = supply["interval"]
        if relation is not None and role == "target":
            relation = _OPPOSITE[relation]
        candidate = _candidate_axis_interval(series, window, axis, cache)
        code = interval_relation_code(candidate, reference, relation)
        checks.append(
            _check(
                origin,
                subject,
                predicate,
                target,
                source,
                role,
                axis,
                relation,
                candidate,
                reference,
                code,
            )
        )
        checks[-1]["candidate_subject"] = candidate_subject
        checks[-1]["reference_subject"] = other
        checks[-1]["reference_status"] = supply["status"]
        checks[-1]["reference_construction"] = supply["construction"]
        # Each check owns its provenance: nothing is shared between checks.
        checks[-1]["reference_planes"] = copy.deepcopy(supply["planes"])
        checks[-1]["reference_windows"] = copy.deepcopy(supply["windows"])
        checks[-1]["reference_fallbacks"] = list(supply["fallbacks"])
    return checks


def _status(checks: list[dict]) -> str:
    codes = [check["result"] for check in checks]
    if any(code.startswith("reversed_") for code in codes):
        return "contradicted"
    if any(code.startswith("supported_") for code in codes):
        return "plausible"
    return "unknown"


def window_sanity_checks(
    series, subject, windows, anchors, knee_side, *, series_by_uid=None
):
    """Advisory per-window checks of candidate windows against authored anatomy.

    Returns one result per input window, in input order, each holding the
    original window, its address, a list of named checks, and an aggregate
    status: contradicted, plausible or unknown. Unknown and overlapping checks
    are neutral; every window stays eligible. Each reference's interval comes
    from the module note's order (complete point, exact planes, the anchor's
    own observed windows), and each check names what supplied it.
    ``series_by_uid`` holds the study's series records, so an anchor's windows
    in other series than the candidate's can be projected; without it only
    the candidate's own series is available.
    """
    if not isinstance(windows, Sequence) or isinstance(windows, (str, bytes)):
        return []
    rules = _rules()
    supplies: dict[tuple[str, str], dict[str, Any]] = {}
    results = []
    for index, item in enumerate(windows):
        window = _window_tuple(item)
        checks = _window_checks(
            series,
            subject,
            window,
            anchors,
            knee_side,
            rules,
            supplies,
            series_by_uid,
        )
        address = (
            item.get("address", item.get("window"))
            if isinstance(item, Mapping)
            else item
        )
        results.append(
            {
                "index": index,
                "window": item,
                "address": address,
                "status": _status(checks),
                "eligible": True,
                "checks": checks,
            }
        )
    return results


__all__ = [
    "COMPLETE_CONSTRUCTION",
    "COMPLETE_PLANES_CONSTRUCTION",
    "PARTIAL_CONSTRUCTION",
    "WINDOW_CONSTRUCTION",
    "interval_relation_code",
    "window_sanity_checks",
]
