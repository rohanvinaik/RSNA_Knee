"""Advisory anatomical plausibility checks for candidate object windows.

This module only categorizes. It never asserts identity, never rejects or
removes a window, and never changes a high-resolution measurement. Unknown
evidence stays unknown and the window stays eligible.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from numbers import Real
from typing import Any

import numpy as np

from knee.collapse import relative
from knee.collapse.anatomical_relations import RELATIONSHIPS
from knee.diagnosis import squint_geometry

SOURCE = "docs/OBJECTS_AND_CONDITIONS.md §4"

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


def _reference_interval(anchors: object, name: str, axis: str):
    """Measured point +/- precision on one axis from a complete reference only."""
    if not isinstance(anchors, Mapping):
        return None
    anchor = anchors.get(name)
    if not isinstance(anchor, Mapping):
        return None
    reference = anchor.get("reference")
    if not isinstance(reference, Mapping):
        return None
    if reference.get("status") != relative.COMPLETE:
        return None
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


def _window_checks(series, candidate_subject, window, anchors, knee_side, rules):
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
        reference = _reference_interval(anchors, other, axis)
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
    are neutral; every window stays eligible.
    """
    if not isinstance(windows, Sequence) or isinstance(windows, (str, bytes)):
        return []
    rules = _rules()
    results = []
    for index, item in enumerate(windows):
        window = _window_tuple(item)
        checks = _window_checks(series, subject, window, anchors, knee_side, rules)
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


__all__ = ["interval_relation_code", "window_sanity_checks"]
