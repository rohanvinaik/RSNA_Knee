import copy
import hashlib
import json
import math

import numpy as np
import pytest

from knee.collapse import relative
from knee.diagnosis import squint_geometry, squint_sanity

W = (0, 1, 0, 1, 0, 1)
X = (1.0, 0.0, 0.0)
Y = (0.0, 1.0, 0.0)
Z = (0.0, 0.0, 1.0)


def _anchor(point, precision=(1.0, 1.0, 1.0), status=relative.COMPLETE):
    return {
        "reference": {
            "status": status,
            "point_lps": list(point),
            "precision_mm": list(precision),
        }
    }


def _run(
    monkeypatch, intervals, subject, anchors, side="left", windows=None, series=None
):
    calls = []

    def fake(series_arg, window, normal):
        key = tuple(float(v) for v in normal)
        calls.append((series_arg, window, key, normal))
        return intervals.get(key)

    monkeypatch.setattr(squint_geometry, "_candidate_interval", fake)
    series = {"name": "s"} if series is None else series
    out = squint_sanity.window_sanity_checks(
        series, subject, [W] if windows is None else windows, anchors, side
    )
    return out, calls


def _by_rule(result, rule_id):
    found = [c for c in result["checks"] if c["rule_id"] == rule_id]
    assert len(found) == 1
    return found[0]


def test_strict_before_after_supported_and_reversed():
    assert (
        squint_sanity.interval_relation_code((0, 1), (2, 3), "strictly_before")
        == "supported_strictly_before"
    )
    assert (
        squint_sanity.interval_relation_code((4, 5), (2, 3), "strictly_after")
        == "supported_strictly_after"
    )
    assert (
        squint_sanity.interval_relation_code((4, 5), (2, 3), "strictly_before")
        == "reversed_strictly_before"
    )
    assert (
        squint_sanity.interval_relation_code((0, 1), (2, 3), "strictly_after")
        == "reversed_strictly_after"
    )


def test_overlap_and_touching_endpoints_are_overlap():
    assert (
        squint_sanity.interval_relation_code((0, 2), (2, 3), "strictly_before")
        == "overlap_or_touching"
    )
    assert (
        squint_sanity.interval_relation_code((3, 4), (2, 3), "strictly_after")
        == "overlap_or_touching"
    )
    assert (
        squint_sanity.interval_relation_code((0, 5), (2, 3), "strictly_after")
        == "overlap_or_touching"
    )
    assert (
        squint_sanity.interval_relation_code((2, 2), (2, 2), "strictly_before")
        == "overlap_or_touching"
    )


def test_malformed_reversed_missing_nonfinite_are_unknown():
    bad = [
        None,
        (1,),
        (1, 2, 3),
        "ab",
        (2, 1),
        (float("nan"), 1),
        (0, float("inf")),
        (True, 2),
        ("a", "b"),
        5,
    ]
    for value in bad:
        assert (
            squint_sanity.interval_relation_code(value, (2, 3), "strictly_before")
            == "unknown"
        )
        assert (
            squint_sanity.interval_relation_code((0, 1), value, "strictly_before")
            == "unknown"
        )


def test_unsupported_relation_is_unknown():
    for relation in ("overlaps", "before", None, "", 3):
        assert (
            squint_sanity.interval_relation_code((0, 1), (2, 3), relation) == "unknown"
        )


def test_exact_zero_precision_has_no_tolerance(monkeypatch):
    anchors = {"tibia": _anchor((0, 0, 10.0), precision=(0, 0, 0))}
    out, _ = _run(monkeypatch, {Z: (10.1, 12.0)}, "femur", {"tibia": anchors["tibia"]})
    check = _by_rule(out[0], "authored:femur:superior_to:tibia")
    assert check["target_interval"] == [10.0, 10.0]
    assert check["result"] == "supported_strictly_after"
    out, _ = _run(monkeypatch, {Z: (10.0, 12.0)}, "femur", anchors)
    assert (
        _by_rule(out[0], "authored:femur:superior_to:tibia")["result"]
        == "overlap_or_touching"
    )


def test_lps_axis_mapping_and_direct_rules(monkeypatch):
    anchors = {"femur": _anchor((0, 0, 0))}
    out, calls = _run(monkeypatch, {Y: (-10.0, -5.0)}, "patella", anchors)
    assert [c[2] for c in calls] == [Y]
    check = _by_rule(out[0], "authored:patella:anterior_to:femur")
    assert check["axis"] == "y"
    assert check["expected_relation"] == "strictly_before"
    assert check["result"] == "supported_strictly_before"

    anchors = {"femur": _anchor((0, 0, 0))}
    for name in ("medial_gastrocnemius", "lateral_gastrocnemius"):
        out, _ = _run(monkeypatch, {Y: (5.0, 6.0)}, name, anchors)
        check = _by_rule(out[0], f"authored:{name}:posterior_to:femur")
        assert check["expected_relation"] == "strictly_after"
        assert check["result"] == "supported_strictly_after"

    out, calls = _run(
        monkeypatch, {Z: (5.0, 6.0)}, "femur", {"tibia": _anchor((0, 0, 0))}
    )
    check = _by_rule(out[0], "authored:femur:superior_to:tibia")
    assert check["axis"] == "z"
    assert check["result"] == "supported_strictly_after"
    # the axis interval is computed once per window even with several rules
    assert sorted(c[2] for c in calls) == sorted([Y, Z])


def test_fibula_left_right_direction(monkeypatch):
    anchors = {"tibia": _anchor((0, 0, 0))}
    rule = "authored:fibula:lateral_to:tibia"
    out, _ = _run(monkeypatch, {X: (5.0, 6.0)}, "fibula", anchors, side="left")
    assert _by_rule(out[0], rule)["result"] == "supported_strictly_after"
    out, _ = _run(monkeypatch, {X: (5.0, 6.0)}, "fibula", anchors, side="right")
    check = _by_rule(out[0], rule)
    assert check["expected_relation"] == "strictly_before"
    assert check["result"] == "reversed_strictly_before"
    assert out[0]["status"] == "contradicted"
    out, _ = _run(monkeypatch, {X: (-6.0, -5.0)}, "fibula", anchors, side="right")
    assert _by_rule(out[0], rule)["result"] == "supported_strictly_before"
    for side in (None, "", "both", 3):
        out, _ = _run(monkeypatch, {X: (5.0, 6.0)}, "fibula", anchors, side=side)
        check = _by_rule(out[0], rule)
        assert check["expected_relation"] is None
        assert check["result"] == "unknown"
        assert out[0]["status"] == "unknown"


def test_reverse_direction_when_candidate_is_authored_target(monkeypatch):
    anchors = {"femur": _anchor((0, 0, 10.0))}
    rule = "authored:femur:superior_to:tibia"
    out, _ = _run(monkeypatch, {Z: (0.0, 5.0)}, "tibia", anchors)
    check = _by_rule(out[0], rule)
    assert check["candidate_role"] == "target"
    assert check["expected_relation"] == "strictly_before"
    assert check["result"] == "supported_strictly_before"
    assert out[0]["status"] == "plausible"
    out, _ = _run(monkeypatch, {Z: (20.0, 30.0)}, "tibia", anchors)
    assert _by_rule(out[0], rule)["result"] == "reversed_strictly_before"
    assert out[0]["status"] == "contradicted"


def test_unavailable_and_partial_references_are_unknown_and_represented(monkeypatch):
    partial_cases = [
        {},
        {"tibia": None},
        {"tibia": {"reference": None}},
        {"tibia": _anchor((0, 0, 0), status="partial")},
        {"tibia": _anchor((0, 0, float("nan")))},
        {"tibia": _anchor((0, 0, 0), precision=(1.0, 1.0))},
        {"tibia": _anchor((0, 0, 0), precision=(1.0, 1.0, -1.0))},
        {"tibia": _anchor((0, 0, 0), precision=(1.0, 1.0, float("inf")))},
        {
            "tibia": {
                "reference": {
                    "status": relative.COMPLETE,
                    "point_lps": None,
                    "precision_mm": [1, 1, 1],
                }
            }
        },
    ]
    for anchors in partial_cases:
        out, _ = _run(monkeypatch, {Z: (5.0, 6.0)}, "femur", anchors)
        assert len(out) == 1
        assert out[0]["window"] == W
        assert out[0]["eligible"] is True
        assert out[0]["status"] == "unknown"
        check = _by_rule(out[0], "authored:femur:superior_to:tibia")
        assert check["result"] == "unknown"
        assert check["target_interval"] is None
        assert check["candidate_interval"] == [5.0, 6.0]


def test_invalid_window_is_unknown_but_present(monkeypatch):
    bad = [(0, 0), [0, 1, 0, 1, 0, "a"], None, (0.0, 1, 0, 1, 0, 1)]
    out, calls = _run(
        monkeypatch,
        {Z: (5.0, 6.0)},
        "femur",
        {"tibia": _anchor((0, 0, 0))},
        windows=bad,
    )
    assert [r["window"] for r in out] == bad
    assert calls == []
    assert all(r["status"] == "unknown" for r in out)


def test_relationship_rules_use_axis_and_side_mapping(monkeypatch):
    # popliteus_tendon medial_to lcl: left knee medial is toward smaller x.
    anchors = {"lcl": _anchor((0, 0, 0))}
    rule = "relationship:popliteus_tendon:medial_to:lcl"
    out, _ = _run(
        monkeypatch, {X: (-5.0, -3.0)}, "popliteus_tendon", anchors, side="left"
    )
    assert _by_rule(out[0], rule)["result"] == "supported_strictly_before"
    out, _ = _run(
        monkeypatch, {X: (-5.0, -3.0)}, "popliteus_tendon", anchors, side="right"
    )
    assert _by_rule(out[0], rule)["result"] == "reversed_strictly_after"
    # candidate is the target: lcl must be lateral to the popliteus anchor.
    out, _ = _run(
        monkeypatch,
        {X: (5.0, 6.0)},
        "lcl",
        {"popliteus_tendon": _anchor((0, 0, 0))},
        side="left",
    )
    check = _by_rule(out[0], rule)
    assert check["candidate_role"] == "target"
    assert check["result"] == "supported_strictly_after"
    # anterior_to on y
    out, _ = _run(
        monkeypatch,
        {Y: (-5.0, -3.0)},
        "popliteal_artery",
        {"popliteal_vein": _anchor((0, 0, 0))},
    )
    assert (
        _by_rule(out[0], "relationship:popliteal_artery:anterior_to:popliteal_vein")[
            "result"
        ]
        == "supported_strictly_before"
    )


def test_relationship_missing_reference_is_reported_as_unknown(monkeypatch):
    out, calls = _run(monkeypatch, {X: (-5.0, -3.0)}, "popliteus_tendon", {})
    assert (
        _by_rule(out[0], "relationship:popliteus_tendon:medial_to:lcl")["result"]
        == "unknown"
    )
    assert out[0]["status"] == "unknown"
    assert len(calls) == 1
    out, _ = _run(
        monkeypatch,
        {X: (-5.0, -3.0)},
        "popliteus_tendon",
        {"lcl": _anchor((0, 0, 0), status="partial")},
    )
    assert (
        _by_rule(out[0], "relationship:popliteus_tendon:medial_to:lcl")["result"]
        == "unknown"
    )


def test_no_distance_rule_for_attach_cover_between(monkeypatch):
    anchors = {
        name: _anchor((0, 0, 0)) for name in ("femur", "tibia", "patella", "fibula")
    }
    for subject in (
        "acl",
        "pcl",
        "mcl",
        "lcl",
        "meniscus",
        "medial_meniscus",
        "femoral_cartilage",
        "joint",
        "synovium",
        "joint_capsule",
        "iliotibial_band",
        "quadriceps_tendon",
    ):
        out, _calls = _run(
            monkeypatch, {Z: (5.0, 6.0), Y: (5.0, 6.0), X: (5.0, 6.0)}, subject, anchors
        )
        rules = {c["relation"] for c in out[0]["checks"]}
        assert not rules & {
            "attaches_to",
            "covers",
            "between",
            "lines",
            "bounds",
            "encloses",
            "deep_to",
        }


def test_aggregate_contradicted_plausible_unknown(monkeypatch):
    anchors = {"tibia": _anchor((0, 0, 0)), "patella": _anchor((0, 0, 0))}
    # z supports; femur strictly before the patella on y contradicts.
    out, _ = _run(monkeypatch, {Z: (5.0, 6.0), Y: (-10.0, -5.0)}, "femur", anchors)
    assert out[0]["status"] == "contradicted"
    # support plus unknown/overlap only is plausible.
    out, _ = _run(monkeypatch, {Z: (5.0, 6.0), Y: (-0.5, 0.5)}, "femur", anchors)
    assert out[0]["status"] == "plausible"
    out, _ = _run(monkeypatch, {Z: (5.0, 6.0)}, "femur", {"tibia": anchors["tibia"]})
    assert out[0]["status"] == "plausible"
    # overlap and unknown only is unknown and still eligible.
    out, _ = _run(monkeypatch, {Z: (-0.5, 0.5)}, "femur", {"tibia": anchors["tibia"]})
    assert out[0]["status"] == "unknown"
    assert out[0]["eligible"] is True
    # no anchors at all
    out, _ = _run(monkeypatch, {}, "femur", {})
    assert out[0]["status"] == "unknown"


def test_preserves_order_and_does_not_mutate_inputs(monkeypatch):
    anchors = {"tibia": _anchor((0, 0, 0)), "patella": _anchor((0, 0, 0))}
    windows = [(0, 1, 0, 1, 0, 1), (1, 2, 0, 1, 0, 1), (2, 3, 0, 1, 0, 1)]
    before_anchors = copy.deepcopy(anchors)
    before_windows = copy.deepcopy(windows)
    series = {"name": "s"}
    before_series = copy.deepcopy(series)
    calls = []

    def fake(series_arg, window, normal):
        calls.append(window)
        return (window[0] * 10.0 + 5.0, window[0] * 10.0 + 6.0)

    monkeypatch.setattr(squint_geometry, "_candidate_interval", fake)
    out = squint_sanity.window_sanity_checks(series, "femur", windows, anchors, "left")
    assert [r["window"] for r in out] == windows
    assert [r["address"] for r in out] == windows
    assert [r["index"] for r in out] == [0, 1, 2]
    assert anchors == before_anchors
    assert windows == before_windows
    assert series == before_series


def test_mapping_windows_keep_original_and_address(monkeypatch):
    item = {"window": W, "address": {"series_uid": "a"}}
    out, calls = _run(
        monkeypatch,
        {Z: (5.0, 6.0)},
        "femur",
        {"tibia": _anchor((0, 0, 0))},
        windows=[item],
    )
    assert out[0]["window"] is item
    assert out[0]["address"] == {"series_uid": "a"}
    assert calls[0][1] == W


def test_candidate_intervals_come_from_candidate_interval_with_unit_axis(monkeypatch):
    series = {"name": "series"}
    out, calls = _run(
        monkeypatch,
        {Z: (7.0, 8.0), Y: (7.0, 8.0)},
        "femur",
        {"tibia": _anchor((0, 0, 0))},
        series=series,
    )
    assert calls
    for series_arg, window, key, normal in calls:
        assert series_arg is series
        assert window == W
        assert isinstance(normal, np.ndarray)
        assert normal.dtype == np.float64
        assert key in (Y, Z)
        assert float(np.linalg.norm(normal)) == 1.0
    check = _by_rule(out[0], "authored:femur:superior_to:tibia")
    assert check["candidate_interval"] == [7.0, 8.0]
    assert check["target_interval"] == [-1.0, 1.0]


def test_malformed_candidate_interval_from_projection_is_unknown(monkeypatch):
    for value in (None, (9.0, 1.0), (float("nan"), 1.0)):
        out, _ = _run(monkeypatch, {Z: value}, "femur", {"tibia": _anchor((0, 0, 0))})
        check = _by_rule(out[0], "authored:femur:superior_to:tibia")
        assert check["candidate_interval"] is None
        assert check["result"] == "unknown"


# ---------------------------------------------------------------- complete references, pinned

#: The keys every check carried before partial references could supply an interval.
ORIGINAL_CHECK_KEYS = (
    "rule_id",
    "source",
    "subject",
    "target",
    "candidate_role",
    "axis",
    "relation",
    "expected_relation",
    "candidate_interval",
    "target_interval",
    "result",
    "candidate_subject",
    "reference_subject",
)


def _plane(orientation, normal, offset, precision=1.0, outcome="selected"):
    return {
        "orientation": orientation,
        "outcome": outcome,
        "series_uid": f"series-{orientation}",
        "slice": 3,
        "normal": list(normal),
        "offset_mm": offset,
        "precision_mm": precision,
    }


def _complete(point, precision, planes=None):
    record = {
        "reference": {
            "status": relative.COMPLETE,
            "point_lps": point,
            "precision_mm": precision,
        }
    }
    if planes is not None:
        record["planes"] = planes
    return record


def _complete_matrix():
    """Complete-reference inputs whose outputs were captured before partial support."""
    one = [1.0, 1.0, 1.0]
    axial_far = {"axial": _plane("axial", Z, 50.0, 3.0)}
    axial_near = {"axial": _plane("axial", Z, 10.0, 2.0)}
    return [
        (
            "femur",
            {
                "tibia": _complete([0.0, 0.0, 10.0], [1.0, 1.0, 2.0]),
                "patella": _complete([0.0, -40.0, 0.0], [0.5, 0.5, 0.5]),
                "medial_gastrocnemius": _complete([0.0, 50.0, 0.0], one),
            },
            "left",
            {Z: (13.0, 20.0), Y: (-30.0, -20.0)},
        ),
        (
            "femur",
            {
                "tibia": _complete([0.0, 0.0, 10.0], [1.0, 1.0, 2.0]),
                "patella": _complete([0.0, -40.0, 0.0], [0.5, 0.5, 0.5]),
            },
            "left",
            {Z: (0.0, 7.0), Y: (-45.0, -41.0)},
        ),
        (
            "tibia",
            {
                "femur": _complete([0.0, 0.0, 10.0], [0.0, 0.0, 0.0]),
                "fibula": _complete([30.0, 0.0, 0.0], one),
            },
            "left",
            {Z: (0.0, 9.99), X: (0.0, 10.0)},
        ),
        (
            "tibia",
            {
                "femur": _complete([0.0, 0.0, 10.0], [0.0, 0.0, 0.0]),
                "fibula": _complete([30.0, 0.0, 0.0], one),
            },
            "left",
            {Z: (9.0, 11.0), X: (29.5, 40.0)},
        ),
        (
            "fibula",
            {"tibia": _complete([0.0, 0.0, 0.0], one)},
            "right",
            {X: (5.0, 6.0)},
        ),
        ("fibula", {"tibia": _complete([0.0, 0.0, 0.0], one)}, None, {X: (5.0, 6.0)}),
        (
            "popliteus_tendon",
            {"lcl": _complete([0.0, 0.0, 0.0], one)},
            "left",
            {X: (-5.0, -3.0)},
        ),
        (
            "lateral_gastrocnemius",
            {"femur": _complete([0.0, 0.0, 0.0], [2.0, 2.0, 2.0])},
            "left",
            {Y: (5.0, 6.0)},
        ),
        (
            "lateral_gastrocnemius",
            {"femur": _complete([0.0, 0.0, 0.0], [2.0, 2.0, 2.0])},
            "left",
            {Y: (-6.0, -5.0)},
        ),
        (
            "popliteal_artery",
            {"popliteal_vein": _complete([0.0, 10.0, 0.0], one)},
            "left",
            {Y: (0.0, 5.0)},
        ),
        # A complete reference reads its point and precision, never its planes.
        (
            "femur",
            {"tibia": _complete([0.0, 0.0, 10.0], one, axial_far)},
            "left",
            {Z: (13.0, 20.0)},
        ),
        # A complete reference without a usable point or precision stays unknown,
        # even when its record holds selected planes.
        (
            "femur",
            {"tibia": _complete([0.0, 0.0, 10.0], None, axial_near)},
            "left",
            {Z: (13.0, 20.0)},
        ),
        (
            "femur",
            {"tibia": _complete([0.0, 0.0, float("nan")], one, axial_near)},
            "left",
            {Z: (13.0, 20.0)},
        ),
        (
            "femur",
            {"tibia": _complete([0.0, 0.0, 10.0], [1.0, 1.0, -1.0], axial_near)},
            "left",
            {Z: (13.0, 20.0)},
        ),
        (
            "femur",
            {"tibia": _complete(["a", "b", "c"], one, axial_near)},
            "left",
            {Z: (13.0, 20.0)},
        ),
        (
            "femur",
            {"tibia": _complete([0.0, 0.0, 10.0], [0.0, 0.0, 0.0])},
            "left",
            {Z: (10.0, 12.0)},
        ),
    ]


def _original_projection(rows):
    return [
        {
            "index": row["index"],
            "window": list(row["window"]),
            "address": list(row["address"]),
            "status": row["status"],
            "eligible": row["eligible"],
            "checks": [
                {key: check[key] for key in ORIGINAL_CHECK_KEYS}
                for check in row["checks"]
            ],
        }
        for row in rows
    ]


def _complete_matrix_outputs(monkeypatch):
    outputs = []
    for subject, anchors, side, intervals in _complete_matrix():
        rows, _ = _run(monkeypatch, intervals, subject, anchors, side=side)
        outputs.append(_original_projection(rows))
    return outputs


#: Captured from squint_sanity at 1804e00, before partial references could supply
#: an interval: SHA-256 of the canonical JSON (sorted keys, compact separators) of
#: every matrix case's original-key projection (18234 bytes).
COMPLETE_MATRIX_SHA256 = "7583bb6ea6922138532c88119e9f200dd6fffbd686ea592086ea0c87311ca910"  # pragma: allowlist secret
FEMUR_RULES = (
    "authored:femur:superior_to:tibia",
    "authored:patella:anterior_to:femur",
    "authored:medial_gastrocnemius:posterior_to:femur",
    "authored:lateral_gastrocnemius:posterior_to:femur",
)
_ALL_UNKNOWN = ("unknown", [(rule, None, "unknown") for rule in FEMUR_RULES])
#: The same capture, readable: each case's status and (rule, target interval, result).
COMPLETE_MATRIX_COMPACT = [
    (
        "plausible",
        [
            (FEMUR_RULES[0], [8.0, 12.0], "supported_strictly_after"),
            (FEMUR_RULES[1], [-40.5, -39.5], "supported_strictly_after"),
            (FEMUR_RULES[2], [49.0, 51.0], "supported_strictly_before"),
            (FEMUR_RULES[3], None, "unknown"),
        ],
    ),
    (
        "contradicted",
        [
            (FEMUR_RULES[0], [8.0, 12.0], "reversed_strictly_after"),
            (FEMUR_RULES[1], [-40.5, -39.5], "reversed_strictly_after"),
            (FEMUR_RULES[2], None, "unknown"),
            (FEMUR_RULES[3], None, "unknown"),
        ],
    ),
    (
        "plausible",
        [
            (FEMUR_RULES[0], [10.0, 10.0], "supported_strictly_before"),
            (
                "authored:fibula:lateral_to:tibia",
                [29.0, 31.0],
                "supported_strictly_before",
            ),
        ],
    ),
    (
        "unknown",
        [
            (FEMUR_RULES[0], [10.0, 10.0], "overlap_or_touching"),
            ("authored:fibula:lateral_to:tibia", [29.0, 31.0], "overlap_or_touching"),
        ],
    ),
    (
        "contradicted",
        [("authored:fibula:lateral_to:tibia", [-1.0, 1.0], "reversed_strictly_before")],
    ),
    ("unknown", [("authored:fibula:lateral_to:tibia", [-1.0, 1.0], "unknown")]),
    (
        "plausible",
        [
            (
                "relationship:popliteus_tendon:medial_to:lcl",
                [-1.0, 1.0],
                "supported_strictly_before",
            )
        ],
    ),
    ("plausible", [(FEMUR_RULES[3], [-2.0, 2.0], "supported_strictly_after")]),
    ("contradicted", [(FEMUR_RULES[3], [-2.0, 2.0], "reversed_strictly_after")]),
    (
        "plausible",
        [
            (
                "relationship:popliteal_artery:anterior_to:popliteal_vein",
                [9.0, 11.0],
                "supported_strictly_before",
            )
        ],
    ),
    (
        "plausible",
        [
            (FEMUR_RULES[0], [9.0, 11.0], "supported_strictly_after"),
            (FEMUR_RULES[1], None, "unknown"),
            (FEMUR_RULES[2], None, "unknown"),
            (FEMUR_RULES[3], None, "unknown"),
        ],
    ),
    _ALL_UNKNOWN,
    _ALL_UNKNOWN,
    _ALL_UNKNOWN,
    _ALL_UNKNOWN,
    (
        "unknown",
        [
            (FEMUR_RULES[0], [10.0, 10.0], "overlap_or_touching"),
            (FEMUR_RULES[1], None, "unknown"),
            (FEMUR_RULES[2], None, "unknown"),
            (FEMUR_RULES[3], None, "unknown"),
        ],
    ),
]


def test_complete_references_give_byte_identical_checks(monkeypatch):
    outputs = _complete_matrix_outputs(monkeypatch)
    text = json.dumps(outputs, sort_keys=True, separators=(",", ":"), allow_nan=False)
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == COMPLETE_MATRIX_SHA256
    compact = [
        (
            case[0]["status"],
            [
                (check["rule_id"], check["target_interval"], check["result"])
                for check in case[0]["checks"]
            ],
        )
        for case in outputs
    ]
    assert compact == COMPLETE_MATRIX_COMPACT


def test_complete_reference_names_its_planes_and_never_rereads_them(monkeypatch):
    planes = {"axial": _plane("axial", Z, 50.0, 3.0)}
    out, _ = _run(
        monkeypatch,
        {Z: (13.0, 20.0)},
        "femur",
        {"tibia": _complete([0.0, 0.0, 10.0], [1.0, 1.0, 1.0], planes)},
    )
    check = _by_rule(out[0], FEMUR_RULES[0])
    # The point +/- precision, not the plane's 50 +/- 3.
    assert check["target_interval"] == [9.0, 11.0]
    assert check["reference_status"] == "complete"
    assert check["reference_construction"] == squint_sanity.COMPLETE_CONSTRUCTION
    assert check["reference_planes"] == [
        {"orientation": "axial", "series_uid": "series-axial", "slice": 3}
    ]
    # Without a usable precision it stays unknown: no fallback to the planes.
    out, _ = _run(
        monkeypatch,
        {Z: (13.0, 20.0)},
        "femur",
        {"tibia": _complete([0.0, 0.0, 10.0], None, planes)},
    )
    check = _by_rule(out[0], FEMUR_RULES[0])
    assert check["target_interval"] is None
    assert check["result"] == "unknown"
    assert check["reference_status"] == "complete"
    assert check["reference_construction"] == (
        "complete_reference_point_or_precision_unusable"
    )
    assert check["reference_planes"] == []


# ---------------------------------------------------------------- partial references

TIED = {"orientation": "coronal", "outcome": "tied", "candidates": [["a", 1], ["b", 2]]}
FIBULA_RULE = "authored:fibula:lateral_to:tibia"


def _partial(planes, **reference):
    record = {
        "reference": {
            "status": relative.PARTIAL,
            "point_lps": None,
            "precision_mm": None,
            **reference,
        }
    }
    if planes is not None:
        record["planes"] = planes
    return record


def test_partial_axial_plane_supports_and_reverses_femur_superior_to_tibia(
    monkeypatch,
):
    tibia = _partial({"axial": _plane("axial", Z, 10.0, 2.0), "coronal": TIED})
    out, _ = _run(monkeypatch, {Z: (13.0, 20.0)}, "femur", {"tibia": tibia})
    check = _by_rule(out[0], FEMUR_RULES[0])
    assert check["axis"] == "z"
    assert check["target_interval"] == [8.0, 12.0]
    assert check["result"] == "supported_strictly_after"
    assert out[0]["status"] == "plausible"
    assert check["reference_status"] == "partial"
    assert check["reference_construction"] == squint_sanity.PARTIAL_CONSTRUCTION
    assert check["reference_planes"] == [
        {
            "orientation": "axial",
            "series_uid": "series-axial",
            "slice": 3,
            "normal": [0.0, 0.0, 1.0],
            "offset_mm": 10.0,
            "precision_mm": 2.0,
            "weight": 1.0,
        }
    ]
    # The opposite sign: a candidate wholly below the tibia's plane reverses it.
    out, _ = _run(monkeypatch, {Z: (0.0, 7.0)}, "femur", {"tibia": tibia})
    assert _by_rule(out[0], FEMUR_RULES[0])["result"] == "reversed_strictly_after"
    assert out[0]["status"] == "contradicted"
    assert out[0]["eligible"] is True
    # Touching the slab's edge is overlap, which stays neutral.
    out, _ = _run(monkeypatch, {Z: (12.0, 20.0)}, "femur", {"tibia": tibia})
    assert _by_rule(out[0], FEMUR_RULES[0])["result"] == "overlap_or_touching"
    assert out[0]["status"] == "unknown"


def test_partial_axial_plane_speaks_for_the_candidate_as_target(monkeypatch):
    femur = _partial({"axial": _plane("axial", Z, 10.0, 2.0)})
    out, _ = _run(monkeypatch, {Z: (0.0, 5.0)}, "tibia", {"femur": femur})
    check = _by_rule(out[0], FEMUR_RULES[0])
    assert check["candidate_role"] == "target"
    assert check["expected_relation"] == "strictly_before"
    assert check["result"] == "supported_strictly_before"
    out, _ = _run(monkeypatch, {Z: (20.0, 30.0)}, "tibia", {"femur": femur})
    assert _by_rule(out[0], FEMUR_RULES[0])["result"] == "reversed_strictly_before"
    assert out[0]["status"] == "contradicted"


def test_partial_axial_plane_leaves_y_rules_unknown(monkeypatch):
    femur = _partial({"axial": _plane("axial", Z, 10.0, 2.0)})
    for subject, rule in (
        ("patella", FEMUR_RULES[1]),
        ("medial_gastrocnemius", FEMUR_RULES[2]),
        ("lateral_gastrocnemius", FEMUR_RULES[3]),
    ):
        # Far from the plane on y: still unknown, since the plane says nothing of y.
        for interval in ((-300.0, -200.0), (200.0, 300.0)):
            out, _ = _run(monkeypatch, {Y: interval}, subject, {"femur": femur})
            check = _by_rule(out[0], rule)
            assert check["axis"] == "y"
            assert check["target_interval"] is None
            assert check["result"] == "unknown"
            assert check["reference_status"] == "partial"
            assert check["reference_construction"] == (
                "partial_reference_axis_not_constrained"
            )
            assert check["reference_planes"] == []
            assert out[0]["status"] == "unknown"


def test_partial_sagittal_plane_speaks_on_x_only(monkeypatch):
    tibia = _partial({"sagittal": _plane("sagittal", X, 0.0, 1.0), "coronal": TIED})
    out, _ = _run(monkeypatch, {Z: (13.0, 20.0)}, "femur", {"tibia": tibia})
    check = _by_rule(out[0], FEMUR_RULES[0])
    assert check["result"] == "unknown"
    assert check["reference_construction"] == "partial_reference_axis_not_constrained"
    out, _ = _run(monkeypatch, {X: (5.0, 6.0)}, "fibula", {"tibia": tibia}, side="left")
    check = _by_rule(out[0], FIBULA_RULE)
    assert check["target_interval"] == [-1.0, 1.0]
    assert check["result"] == "supported_strictly_after"
    out, _ = _run(
        monkeypatch, {X: (5.0, 6.0)}, "fibula", {"tibia": tibia}, side="right"
    )
    assert _by_rule(out[0], FIBULA_RULE)["result"] == "reversed_strictly_before"
    assert out[0]["status"] == "contradicted"
    # Without a named knee the expected direction is unknown, interval or not.
    out, _ = _run(monkeypatch, {X: (5.0, 6.0)}, "fibula", {"tibia": tibia}, side=None)
    check = _by_rule(out[0], FIBULA_RULE)
    assert check["target_interval"] == [-1.0, 1.0]
    assert check["result"] == "unknown"


def test_reversed_or_rescaled_plane_gives_the_same_interval(monkeypatch):
    readings = []
    for normal, offset, weight in (
        (Z, 10.0, 1.0),
        ((0.0, 0.0, -1.0), -10.0, -1.0),
        ((0.0, 0.0, 4.0), 40.0, 1.0),
    ):
        tibia = _partial({"axial": _plane("axial", normal, offset, 2.0)})
        out, _ = _run(monkeypatch, {Z: (13.0, 20.0)}, "femur", {"tibia": tibia})
        check = _by_rule(out[0], FEMUR_RULES[0])
        readings.append((check["target_interval"], check["result"]))
        assert [plane["weight"] for plane in check["reference_planes"]] == [weight]
    assert readings == [([8.0, 12.0], "supported_strictly_after")] * 3


def test_oblique_partial_plane_determines_no_lps_axis(monkeypatch):
    for tilt in (math.radians(7.0), 1e-9):
        normal = (0.0, math.sin(tilt), math.cos(tilt))
        tibia = _partial({"axial": _plane("axial", normal, 10.0, 2.0)})
        for interval in ((13.0, 20.0), (0.0, 7.0), (500.0, 600.0)):
            out, _ = _run(monkeypatch, {Z: interval}, "femur", {"tibia": tibia})
            check = _by_rule(out[0], FEMUR_RULES[0])
            assert check["target_interval"] is None
            assert check["result"] == "unknown"
            assert check["reference_construction"] == (
                "partial_reference_axis_not_constrained"
            )
            assert out[0]["status"] == "unknown"
    # Floating noise in an axial normal is not obliquity (relative.py's rank precision).
    noisy = _partial({"axial": _plane("axial", (1e-17, 0.0, 1.0), 10.0, 2.0)})
    out, _ = _run(monkeypatch, {Z: (13.0, 20.0)}, "femur", {"tibia": noisy})
    check = _by_rule(out[0], FEMUR_RULES[0])
    assert check["target_interval"] == [8.0, 12.0]
    assert check["result"] == "supported_strictly_after"


def test_two_oblique_planes_that_span_an_axis_determine_it(monkeypatch):
    # Neither plane is axial, and their labels do not decide anything: their
    # normals' span holds z and y exactly, never x.
    pair = _partial(
        {
            "sagittal": _plane("sagittal", (0.0, 0.6, 0.8), 8.0, 1.0),
            "coronal": _plane("coronal", (0.0, -0.6, 0.8), 8.0, 1.0),
        }
    )
    out, _ = _run(monkeypatch, {Z: (12.0, 13.0)}, "femur", {"tibia": pair})
    check = _by_rule(out[0], FEMUR_RULES[0])
    # z = (d1 + d2) / 1.6 = 10, bound (e1 + e2) / 1.6 = 1.25
    assert check["target_interval"] == pytest.approx([8.75, 11.25])
    assert check["result"] == "supported_strictly_after"
    assert [plane["orientation"] for plane in check["reference_planes"]] == [
        "sagittal",
        "coronal",
    ]
    assert [plane["weight"] for plane in check["reference_planes"]] == pytest.approx(
        [0.625, 0.625]
    )
    out, _ = _run(monkeypatch, {Z: (5.0, 8.0)}, "femur", {"tibia": pair})
    assert _by_rule(out[0], FEMUR_RULES[0])["result"] == "reversed_strictly_after"
    out, _ = _run(
        monkeypatch, {X: (40.0, 50.0)}, "fibula", {"tibia": pair}, side="left"
    )
    check = _by_rule(out[0], FIBULA_RULE)
    assert check["result"] == "unknown"
    assert check["reference_construction"] == "partial_reference_axis_not_constrained"


def test_partial_precision_must_be_known_on_the_planes_an_axis_needs(monkeypatch):
    sagittal = _plane("sagittal", X, 0.0, 1.0)
    for precision in (None, float("nan"), float("inf"), -1.0, True, "2"):
        tibia = _partial(
            {"sagittal": sagittal, "axial": _plane("axial", Z, 10.0, precision)}
        )
        out, _ = _run(monkeypatch, {Z: (13.0, 20.0)}, "femur", {"tibia": tibia})
        check = _by_rule(out[0], FEMUR_RULES[0])
        assert check["target_interval"] is None
        assert check["result"] == "unknown"
        assert check["reference_construction"] == "partial_reference_precision_unknown"
        # The sagittal plane's own axis does not need the axial precision.
        out, _ = _run(
            monkeypatch, {X: (5.0, 6.0)}, "fibula", {"tibia": tibia}, side="left"
        )
        assert _by_rule(out[0], FIBULA_RULE)["result"] == "supported_strictly_after"


def test_malformed_partial_records_are_unknown_not_errors(monkeypatch):
    good = _plane("axial", Z, 10.0, 2.0)
    without = "partial_reference_without_selected_planes"
    malformed = "partial_reference_plane_malformed"
    cases = [
        ({"reference": {"status": relative.PARTIAL}}, without),
        (_partial(None), without),
        (_partial([good]), without),
        (_partial({}), without),
        (_partial({"axial": None}), without),
        (_partial({"axial": {**good, "outcome": "tied"}}), without),
        (
            _partial({"axial": {**good, "outcome": "invalid:frame_unavailable"}}),
            without,
        ),
        (_partial({"oblique": good}), without),
        # A partial record's point and precision are never read.
        (
            _partial(None, point_lps=[0.0, 0.0, 10.0], precision_mm=[1.0, 1.0, 1.0]),
            without,
        ),
        (_partial({"axial": {**good, "normal": None}}), malformed),
        (_partial({"axial": {**good, "normal": [0.0, 1.0]}}), malformed),
        (_partial({"axial": {**good, "normal": [0.0, 0.0, float("nan")]}}), malformed),
        (_partial({"axial": {**good, "normal": [0.0, 0.0, 0.0]}}), malformed),
        (_partial({"axial": {**good, "normal": "001"}}), malformed),
        (_partial({"axial": {**good, "normal": [0.0, 0.0, True]}}), malformed),
        (_partial({"axial": {**good, "offset_mm": None}}), malformed),
        (_partial({"axial": {**good, "offset_mm": float("inf")}}), malformed),
        (_partial({"axial": {**good, "offset_mm": "10"}}), malformed),
        # One malformed selected plane withholds the reference's other planes too.
        (_partial({"sagittal": {**good, "normal": "bad"}, "axial": good}), malformed),
        # Two parallel planes are not one reading of the axis.
        (
            _partial({"sagittal": _plane("sagittal", Z, 0.0, 1.0), "axial": good}),
            "partial_reference_planes_dependent",
        ),
    ]
    for record, construction in cases:
        out, _ = _run(monkeypatch, {Z: (13.0, 20.0)}, "femur", {"tibia": record})
        assert out[0]["status"] == "unknown"
        assert out[0]["eligible"] is True
        check = _by_rule(out[0], FEMUR_RULES[0])
        assert check["candidate_interval"] == [13.0, 20.0]
        assert check["target_interval"] is None
        assert check["result"] == "unknown"
        assert check["reference_status"] == "partial"
        assert check["reference_construction"] == construction
        assert check["reference_planes"] == []


def test_other_reference_statuses_supply_no_interval(monkeypatch):
    planes = {"axial": _plane("axial", Z, 10.0, 2.0)}
    for status in ("singular_planes", "nonfinite_solution", "conflict", "", None, 3):
        record = {
            "reference": {
                "status": status,
                "point_lps": [0.0, 0.0, 10.0],
                "precision_mm": [1.0, 1.0, 1.0],
            },
            "planes": planes,
        }
        out, _ = _run(monkeypatch, {Z: (13.0, 20.0)}, "femur", {"tibia": record})
        check = _by_rule(out[0], FEMUR_RULES[0])
        assert check["result"] == "unknown"
        assert check["reference_status"] == (
            status if isinstance(status, str) else None
        )
        assert (
            check["reference_construction"] == "reference_status_supplies_no_interval"
        )
    out, _ = _run(monkeypatch, {Z: (13.0, 20.0)}, "femur", {})
    check = _by_rule(out[0], FEMUR_RULES[0])
    assert check["reference_status"] is None
    assert check["reference_construction"] == "no_reference"


def test_reference_planes_are_not_shared_between_windows(monkeypatch):
    tibia = _partial({"axial": _plane("axial", Z, 10.0, 2.0)})
    windows = [(0, 1, 0, 1, 0, 1), (1, 2, 0, 1, 0, 1)]
    out, _ = _run(
        monkeypatch, {Z: (13.0, 20.0)}, "femur", {"tibia": tibia}, windows=windows
    )
    first = _by_rule(out[0], FEMUR_RULES[0])
    second = _by_rule(out[1], FEMUR_RULES[0])
    assert first["reference_planes"] == second["reference_planes"]
    assert first["reference_planes"][0] is not second["reference_planes"][0]
    first["reference_planes"][0]["weight"] = 99.0
    assert second["reference_planes"][0]["weight"] == 1.0
    assert tibia["planes"]["axial"]["normal"] == list(Z)


def _axial_series(z_positions):
    """One tile per slice of an exactly axial acquisition at the given heights."""
    count = len(z_positions)
    stack = type(
        "Stack",
        (),
        {
            "median": np.ones((count, 1, 1)),
            "bounds_rc": np.asarray([[[0, 2, 0, 2]]], dtype=np.int64),
        },
    )()
    return {
        "series_uid": "axial-series",
        "view": {
            "orientation": "axial",
            "fluid_sensitive": "yes",
            "fat_suppression": "no",
        },
        "stack": stack,
        "geometry": {
            "position": np.asarray([[0.0, 0.0, z] for z in z_positions]),
            "orientation": np.asarray([[1, 0, 0, 0, 1, 0]] * count, dtype=float),
            "spacing": np.asarray([[1.0, 1.0]] * count),
        },
    }


def test_object_geometry_partial_reference_reaches_the_check_end_to_end():
    """A resemblance-located tibia's real one-plane record, real candidate geometry."""
    series = _axial_series([0.0, 60.0, 100.0])
    by_uid = {"axial-series": series}
    for tibia_slice, femur_slice, result, status in (
        (0, 2, "supported_strictly_after", "plausible"),
        (2, 0, "reversed_strictly_after", "contradicted"),
    ):
        tibia = squint_geometry.object_geometry(
            "tibia",
            [
                {
                    "series_uid": "axial-series",
                    "window": [tibia_slice, tibia_slice + 1, 0, 1, 0, 1],
                }
            ],
            by_uid,
        )
        assert tibia["reference"]["status"] == relative.PARTIAL
        assert tibia["reference"]["point_lps"] is None
        window = (femur_slice, femur_slice + 1, 0, 1, 0, 1)
        out = squint_sanity.window_sanity_checks(
            series, "femur", [window], {"tibia": tibia}, "left"
        )
        check = _by_rule(out[0], FEMUR_RULES[0])
        assert check["result"] == result
        assert out[0]["status"] == status
        assert check["reference_status"] == "partial"
        (plane,) = check["reference_planes"]
        assert plane["orientation"] == "axial"
        assert plane["slice"] == tibia_slice
        assert plane["series_uid"] == "axial-series"
