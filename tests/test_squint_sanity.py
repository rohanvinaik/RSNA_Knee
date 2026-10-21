import copy

import numpy as np

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
