"""A measured projection supports location, never identity or exclusion."""

from __future__ import annotations

import copy
from types import SimpleNamespace

import numpy as np
import pytest

from knee.collapse.physical import physical_squint
from knee.diagnosis.squint_sanity import (
    between_interval_code,
    window_sanity_checks,
)


def _series():
    # The measured normal is oblique to every LPS body axis it constrains.
    normal = np.asarray([0.0, 0.6, 0.8])
    grid = physical_squint(np.zeros((2, 2)), (1.0, 1.0), 1.0)
    return {
        "series_uid": "query-series",
        "stack": SimpleNamespace(median=np.zeros((3, 2, 2)), bounds_rc=grid.bounds_rc),
        "geometry": {
            "position": np.asarray([-2 * normal, 0 * normal, 2 * normal]),
            "orientation": np.asarray([[1, 0, 0, 0, 0.8, -0.6]] * 3),
            "spacing": np.ones((3, 2)),
        },
    }


def _anchor(subject, offset, *, reverse=False):
    sign = -1.0 if reverse else 1.0
    return {
        "source": "structural_anchor",
        "reference": {"status": "partial", "point_lps": None},
        "planes": {
            "axial": {
                "outcome": "selected",
                "series_uid": subject + "-series",
                "slice": 4,
                "normal": [0.0, sign * 0.6, sign * 0.8],
                "offset_mm": sign * offset,
                "precision_mm": 1.0,
            }
        },
    }


@pytest.mark.parametrize("reverse", [False, True])
def test_oblique_partial_planes_support_only_the_authored_subject(reverse):
    series = _series()
    anchors = {
        "femur": _anchor("femur", -5),
        "tibia": _anchor("tibia", 5, reverse=reverse),
    }
    rows = window_sanity_checks(
        series, "medial_meniscus", [(1, 2, 0, 2, 0, 2)], anchors, None
    )
    check = rows[0]["checks"][0]
    assert rows[0]["status"] == "plausible"
    assert rows[0]["eligible"] is True
    assert check["result"] == "supported_between"
    assert check["establishes"] == "location_only"
    assert check["candidate_role"] == "subject"
    assert check["target"] == ["femur", "tibia"]
    assert check["qualifier"] == "medial compartment"
    assert check["axis_lps"] == pytest.approx([0.0, 0.6, 0.8])
    assert check["candidate_interval"] == pytest.approx([-1.0, 1.0])
    assert check["anchor_bands"]["femur"] == pytest.approx([-6.0, -4.0])
    assert check["anchor_bands"]["tibia"] == pytest.approx([4.0, 6.0])
    assert check["gap_interval"] == pytest.approx([-4.0, 4.0])
    assert [p["series_uid"] for p in check["reference_planes"]] == [
        "femur-series",
        "tibia-series",
    ]
    assert check["reference_planes"][1]["weight"] == pytest.approx(
        -1.0 if reverse else 1.0
    )


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        ("missing_anchor", "unknown_between_shared_planes_unavailable"),
        ("unresolved_anchor", "unknown_between_shared_planes_unavailable"),
        ("unselected_plane", "unknown_between_shared_planes_unavailable"),
        ("malformed_plane", "unknown_between_shared_planes_unavailable"),
        ("nonparallel_planes", "unknown_between_shared_planes_unavailable"),
        ("missing_precision", "unknown_between_plane_precision"),
        ("overflow_band", "unknown_between_anchor_interval"),
        ("overlapping_bands", "unknown_between_anchor_overlap"),
        ("outside", "unknown_between_candidate_outside_or_touching"),
        ("touching", "unknown_between_candidate_outside_or_touching"),
        ("invalid_window", "unknown_between_candidate_interval"),
    ],
)
def test_unestablished_or_ambiguous_projection_never_excludes(change, expected):
    anchors = {"femur": _anchor("femur", -5), "tibia": _anchor("tibia", 5)}
    window = (1, 2, 0, 2, 0, 2)
    if change == "missing_anchor":
        del anchors["tibia"]
    elif change == "unresolved_anchor":
        anchors["tibia"]["reference"]["status"] = "conflict"
    elif change == "unselected_plane":
        anchors["tibia"]["planes"]["axial"]["outcome"] = "tied"
    elif change == "malformed_plane":
        anchors["tibia"]["planes"]["axial"]["normal"] = [0, 0, 0]
    elif change == "nonparallel_planes":
        anchors["tibia"]["planes"]["axial"]["normal"] = [1, 0, 0]
    elif change == "missing_precision":
        anchors["tibia"]["planes"]["axial"]["precision_mm"] = None
    elif change == "overflow_band":
        anchors["tibia"]["planes"]["axial"].update(offset_mm=1e308, precision_mm=1e308)
    elif change == "overlapping_bands":
        anchors["tibia"]["planes"]["axial"]["offset_mm"] = -4
    elif change in ("outside", "touching"):
        anchors["tibia"]["planes"]["axial"]["offset_mm"] = (
            -2 if change == "outside" else 2
        )
    elif change == "invalid_window":
        window = (1, 1, 0, 2, 0, 2)
    rows = window_sanity_checks(_series(), "medial_meniscus", [window], anchors, None)
    assert rows[0]["status"] == "unknown"
    assert rows[0]["eligible"] is True
    assert rows[0]["checks"][0]["result"] == expected
    assert not any(c["result"].startswith("reversed_") for c in rows[0]["checks"])


@pytest.mark.parametrize(
    ("candidate", "first", "second", "expected"),
    [
        ([0, 1], [-3, -2], [2, 3], "supported_between"),
        ([0, 0], [2, 3], [-3, -2], "supported_between"),
        ([-2, 1], [-3, -2], [2, 3], "unknown_between_candidate_outside_or_touching"),
        ([0, 2], [-3, -2], [2, 3], "unknown_between_candidate_outside_or_touching"),
        ([3, 4], [-3, -2], [2, 3], "unknown_between_candidate_outside_or_touching"),
        ([0, 1], [-3, 2], [2, 3], "unknown_between_anchor_overlap"),
        (None, [-3, -2], [2, 3], "unknown_between_candidate_interval"),
        ([1, 0], [-3, -2], [2, 3], "unknown_between_candidate_interval"),
        ([0, 1], None, [2, 3], "unknown_between_anchor_interval"),
        ([0, 1], [-3, -2], [float("inf"), 3], "unknown_between_anchor_interval"),
        ([0, 1], [False, 0], [2, 3], "unknown_between_anchor_interval"),
    ],
)
def test_between_decision_has_both_signs(candidate, first, second, expected):
    assert between_interval_code(candidate, first, second) == expected


def test_between_never_inverts_to_name_or_exclude_a_target():
    anchors = {"femur": _anchor("femur", -5), "tibia": _anchor("tibia", 5)}
    rows = window_sanity_checks(_series(), "femur", [(1, 2, 0, 2, 0, 2)], anchors, None)
    assert not any(check["relation"] == "between" for check in rows[0]["checks"])


def test_each_window_owns_its_scoped_projection_provenance():
    anchors = {"femur": _anchor("femur", -5), "tibia": _anchor("tibia", 5)}
    original = copy.deepcopy(anchors)
    window = (1, 2, 0, 2, 0, 2)
    rows = window_sanity_checks(
        _series(), "medial_meniscus", [window, window], anchors, None
    )
    rows[0]["checks"][0]["anchor_bands"]["femur"][0] = -100
    rows[0]["checks"][0]["reference_planes"][0]["normal"][0] = 100
    assert rows[1]["checks"][0]["anchor_bands"]["femur"] == [-6, -4]
    assert rows[1]["checks"][0]["reference_planes"][0]["normal"][0] == 0
    assert anchors == original


def test_recess_keeps_its_authored_face_scope_without_missing_femur_support():
    anchors = {"femur": _anchor("femur", -5), "tibia": _anchor("tibia", 5)}
    rows = window_sanity_checks(
        _series(), "anterior_synovial_recess", [(1, 2, 0, 2, 0, 2)], anchors, None
    )
    assert rows[0]["checks"][0]["qualifier"] == (
        "posterior patellar face; anterior femoral face"
    )
    assert rows[0]["status"] == "unknown"  # patella was not established
