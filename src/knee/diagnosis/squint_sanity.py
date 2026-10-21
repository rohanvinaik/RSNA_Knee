"""Advisory anatomical plausibility checks for candidate object windows.

This module only categorizes. It never asserts identity, never rejects or
removes a window, and never changes a high-resolution measurement. Unknown
evidence stays unknown and the window stays eligible.

A reference supplies an interval only on an LPS axis its own record determines
(``docs/RELATIVE_POSITION_MAP.md`` §8.8: each key plane is one physical depth
constraint; oblique planes are solved, never read by their orientation label).

* A ``complete`` reference supplies its measured point +/- its recorded
  precision on every axis, exactly as before; its planes are not reread.
* A ``partial`` reference supplies an interval only on an axis that lies in the
  row space of its selected planes' normals. That test is the floating-precision
  rank ``knee.collapse.relative.reference_position`` already uses for singular
  planes, not an anatomical or angular threshold. The interval is the solved
  coordinate ``w . d`` +/- ``sum |w_i| precision_i`` over the planes that
  determine the axis: with three planes this is row ``a`` of ``N^-1`` and
  ``|N^-1| @ precision``, the complete construction itself. A plane whose
  normal is exactly one axis gives that axis its own offset +/- its precision;
  an oblique plane determines no single LPS axis and supplies nothing.
* Every undetermined axis, and every other status, stays unknown.

Each check records which reference status supplied it, how
(``reference_construction``) and from which planes, with their weights
(``reference_planes``). A pass remains a location statement only.
"""

from __future__ import annotations

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


def _partial_interval(record: Mapping, axis: str):
    """(interval, construction code, planes) on one LPS axis of a partial reference.

    The axis is determined only when it lies in the row space of the selected
    planes' normals; then the smallest set of planes whose span holds it gives
    the solved coordinate and its precision bound. Dependent (parallel)
    planes, a malformed selected plane, or an unknown precision on a plane the
    axis needs supply nothing, by name.
    """
    planes = record.get("planes")
    if not isinstance(planes, Mapping):
        return None, "partial_reference_without_selected_planes", []
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
            return None, "partial_reference_plane_malformed", []
        rows.append(row)
    if not rows:
        return None, "partial_reference_without_selected_planes", []
    normals = np.asarray([row["normal"] for row in rows], dtype=np.float64)
    if _rank(normals) < len(rows):
        return None, "partial_reference_planes_dependent", []
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
                return None, "partial_reference_planes_dependent", []
            used = [rows[index] for index in subset]
            if any(row["precision_mm"] is None for row in used):
                return None, "partial_reference_precision_unknown", []
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
                return None, "partial_reference_interval_nonfinite", []
            return (
                interval,
                PARTIAL_CONSTRUCTION,
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
    return None, "partial_reference_axis_not_constrained", []


def _reference_supply(anchors: object, name: str, axis: str) -> dict[str, Any]:
    """The target interval one reference supplies on one axis, and from what.

    ``status`` is the reference record's own status (None without a record);
    ``construction`` names how the interval was made or why none was;
    ``planes`` lists the planes that made it (empty when none was made).
    """
    record = anchors.get(name) if isinstance(anchors, Mapping) else None
    reference = record.get("reference") if isinstance(record, Mapping) else None
    if not isinstance(reference, Mapping):
        return {
            "interval": None,
            "status": None,
            "construction": "no_reference",
            "planes": [],
        }
    status = reference.get("status")
    if status == relative.COMPLETE:
        interval = _complete_interval(reference, axis)
        return {
            "interval": interval,
            "status": status,
            "construction": COMPLETE_CONSTRUCTION
            if interval is not None
            else "complete_reference_point_or_precision_unusable",
            "planes": _selected_names(record) if interval is not None else [],
        }
    if status == relative.PARTIAL:
        interval, construction, planes = _partial_interval(record, axis)
        return {
            "interval": interval,
            "status": status,
            "construction": construction,
            "planes": planes,
        }
    return {
        "interval": None,
        "status": status if isinstance(status, str) else None,
        "construction": "reference_status_supplies_no_interval",
        "planes": [],
    }


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
    series, candidate_subject, window, anchors, knee_side, rules, supplies
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
        # A reference's interval does not depend on the window: made once per call.
        key = (other, axis)
        if key not in supplies:
            supplies[key] = _reference_supply(anchors, other, axis)
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
        checks[-1]["reference_planes"] = [dict(plane) for plane in supply["planes"]]
    return checks


def _status(checks: list[dict]) -> str:
    codes = [check["result"] for check in checks]
    if any(code.startswith("reversed_") for code in codes):
        return "contradicted"
    if any(code.startswith("supported_") for code in codes):
        return "plausible"
    return "unknown"


def window_sanity_checks(series, subject, windows, anchors, knee_side):
    """Advisory per-window checks of candidate windows against authored anatomy.

    Returns one result per input window, in input order, each holding the
    original window, its address, a list of named checks, and an aggregate
    status: contradicted, plausible or unknown. Unknown and overlapping checks
    are neutral; every window stays eligible. A complete reference speaks on
    every axis; a partial one only on the axes its selected planes determine
    (module note), and each check names the reference status, construction
    and planes that supplied its target interval.
    """
    if not isinstance(windows, Sequence) or isinstance(windows, (str, bytes)):
        return []
    rules = _rules()
    supplies: dict[tuple[str, str], dict[str, Any]] = {}
    results = []
    for index, item in enumerate(windows):
        window = _window_tuple(item)
        checks = _window_checks(
            series, subject, window, anchors, knee_side, rules, supplies
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
    "PARTIAL_CONSTRUCTION",
    "interval_relation_code",
    "window_sanity_checks",
]
