from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from knee.diagnosis.squint_geometry import (
    object_geometry,
    relative_scope_priors,
    window_scope_code,
    window_scope_codes,
)


def _series(uid: str, orientation: str, axis: int, offset: float, *, step: float = 4.0):
    orientations = {
        "sagittal": np.asarray([[0, 1, 0, 0, 0, 1]] * 3, dtype=float),
        "coronal": np.asarray([[1, 0, 0, 0, 0, 1]] * 3, dtype=float),
        "axial": np.asarray([[1, 0, 0, 0, 1, 0]] * 3, dtype=float),
    }
    normal = np.eye(3)[axis]
    positions = np.asarray([normal * (offset + (z - 1) * step) for z in range(3)])
    bounds = np.zeros((1, 1, 4), dtype=np.int64)
    bounds[0, 0] = (0, 4, 0, 5)
    stack = SimpleNamespace(bounds_rc=bounds, median=np.zeros((3, 1, 1)))
    return {
        "series_uid": uid,
        "view": {"orientation": orientation},
        "stack": stack,
        "geometry": {
            "position": positions,
            "orientation": orientations[orientation],
            "spacing": np.asarray([[1.0, 1.0]] * 3),
        },
    }


def _region(uid: str, view: str = "axial"):
    return {
        "series_uid": uid,
        "view": {"orientation": view},
        "window": (1, 2, 0, 1, 0, 1),
    }


def test_three_native_planes_solve_one_shared_reference():
    series = {
        "s": _series("s", "sagittal", 0, 3),
        "c": _series("c", "coronal", 1, 5),
        "a": _series("a", "axial", 2, 7),
    }
    geometry = object_geometry(
        "meniscus",
        [_region("s", "sagittal"), _region("c", "coronal"), _region("a")],
        series,
    )
    assert geometry["reference"]["status"] == "complete"
    assert np.allclose(geometry["reference"]["point_lps"], [3, 5, 7])
    assert geometry["support"] is None
    assert all(row["precision_mm"] == 2.0 for row in geometry["planes"].values())


def test_two_planes_remain_partial_and_constrain_their_own_axes():
    series = {"s": _series("s", "sagittal", 0, 3), "c": _series("c", "coronal", 1, 5)}
    geometry = object_geometry(
        "femur", [_region("s", "sagittal"), _region("c", "coronal")], series
    )
    assert geometry["reference"]["status"] == "partial"
    assert geometry["reference"]["point_lps"] is None
    assert geometry["reference"]["line_direction"] is not None
    assert geometry["planes"]["sagittal"]["outcome"] == "selected"
    assert geometry["planes"]["coronal"]["outcome"] == "selected"
    assert geometry["planes"]["axial"]["outcome"] == "not_supplied"


def test_single_slice_without_neighbor_keeps_plane_and_names_precision_unknown():
    series = _series("a", "axial", 2, 7)
    series["geometry"]["position"] = series["geometry"]["position"][1:2]
    series["geometry"]["orientation"] = series["geometry"]["orientation"][1:2]
    series["geometry"]["spacing"] = series["geometry"]["spacing"][1:2]
    series["stack"].median = np.zeros((1, 1, 1))
    region = _region("a")
    region["window"] = (0, 1, 0, 1, 0, 1)
    geometry = object_geometry("ACL", [region], {"a": series})
    assert geometry["planes"]["axial"]["outcome"] == "selected"
    assert geometry["planes"]["axial"]["precision_mm"] is None
    assert geometry["regions"][0]["precision_status"] == "unavailable"


def test_repeated_same_view_does_not_erase_plane_but_distinct_tie_is_preserved():
    first = _series("a", "axial", 2, 7)
    duplicate = _series("b", "axial", 2, 7)
    same = object_geometry(
        "tibia", [_region("a"), _region("b")], {"a": first, "b": duplicate}
    )
    assert same["planes"]["axial"]["outcome"] == "selected"
    distinct = _series("c", "axial", 2, 19)
    tied = object_geometry(
        "tibia", [_region("a"), _region("c")], {"a": first, "c": distinct}
    )
    assert tied["planes"]["axial"]["outcome"] == "tied"
    assert tied["reference"]["status"] == "partial"


def test_relative_prior_uses_source_case_delta_on_current_anchor_plane():
    current_anchor = object_geometry(
        "femur", [_region("f", "sagittal")], {"f": _series("f", "sagittal", 0, 100)}
    )
    query = {"femur": current_anchor}
    cases = [
        {
            "case_id": "target",
            "study_uid": "old",
            "subject": "ACL",
            "regions": [{"source_point_lps": [15, 2, 0]}],
        },
        {
            "study_uid": "old",
            "subject": "femur",
            "regions": [{"source_point_lps": [10, 2, 0]}],
        },
    ]
    priors = relative_scope_priors("ACL", ("femur",), cases, query)
    constraint = priors["cases"][0]["planes"][0]
    assert constraint["offset_mm"] == -105.0
    assert constraint["displacement_mm"] == [5.0, 0.0, 0.0]
    assert priors["cases"][0]["scale_status"] == "unscaled_millimetres"


def test_missing_geometry_is_neutral_and_bbox_is_not_reported_as_support():
    geometry = object_geometry("ACL", [_region("missing")], {})
    assert geometry["support"] is None
    assert geometry["planes"]["axial"]["outcome"] == "refused"
    assert "invalid:series_missing" in geometry["planes"]["axial"]["reason"]
    assert (
        window_scope_code({}, (0, 1, 0, 1, 0, 1), {"cases": []})
        == "geometry_unavailable"
    )


def test_window_constraint_uses_projected_plane_interval():
    candidate = _series("q", "sagittal", 0, 4)
    prior = {
        "cases": [
            {
                "status": "available",
                "planes": [
                    {
                        "normal": [1, 0, 0],
                        "offset_mm": 4.0,
                        "precision_mm": 2.0,
                    }
                ],
            }
        ]
    }
    assert window_scope_code(candidate, (1, 2, 0, 1, 0, 1), prior) == "eligible"
    prior["cases"][0]["planes"][0]["offset_mm"] = 50.0
    assert (
        window_scope_code(candidate, (1, 2, 0, 1, 0, 1), prior)
        == "outside_anatomical_prior"
    )


def test_malformed_tile_bounds_grid_is_named_unavailable():
    candidate = _series("q", "sagittal", 0, 4)
    candidate["stack"].bounds_rc = np.zeros((1, 2, 4), dtype=np.int64)
    prior = {
        "cases": [
            {
                "status": "available",
                "planes": [
                    {"normal": [1, 0, 0], "offset_mm": 4.0, "precision_mm": 2.0}
                ],
            }
        ]
    }
    assert (
        window_scope_code(candidate, (1, 2, 0, 1, 0, 1), prior)
        == "geometry_unavailable"
    )


def test_mutated_prior_changes_cached_evaluation_without_stale_result():
    candidate = _series("q", "sagittal", 0, 4)
    prior = {
        "cases": [
            {
                "status": "available",
                "planes": [
                    {"normal": [1, 0, 0], "offset_mm": 4.0, "precision_mm": 2.0}
                ],
            }
        ]
    }
    window = (1, 2, 0, 1, 0, 1)
    assert window_scope_code(candidate, window, prior) == "eligible"
    prior["cases"][0]["planes"][0]["precision_mm"] = None
    assert window_scope_code(candidate, window, prior) == "geometry_unavailable"


def test_batch_matches_scalar_for_all_codes_and_malformed_windows():
    candidate = _series("q", "sagittal", 0, 4)
    priors = {
        "cases": [
            {
                "status": "available",
                "planes": [
                    {"normal": [1, 0, 0], "offset_mm": 4.0, "precision_mm": 2.0}
                ],
            }
        ]
    }
    windows = [
        (1, 2, 0, 1, 0, 1),
        (1, 2, 0, 1, 0, 1),
        (1, 2, 0, 1, 0, 1),
        [1, 2, 0, 1, 0, 1],
    ]
    priors["cases"][0]["planes"][0]["offset_mm"] = 4.0
    answers = window_scope_codes(candidate, windows, priors)
    assert answers == [
        window_scope_code(candidate, window, priors) for window in windows
    ]
    assert answers[0] == "eligible"
    assert answers[-1] == "geometry_unavailable"
    priors["cases"][0]["planes"][0]["offset_mm"] = 50.0
    assert (
        window_scope_codes(candidate, windows[:3], priors)
        == ["outside_anatomical_prior"] * 3
    )


def test_batch_unknown_precision_is_neutral_and_mutable_priors_are_recompiled():
    candidate = _series("q", "sagittal", 0, 4)
    window = (1, 2, 0, 1, 0, 1)
    prior = {
        "cases": [
            {
                "status": "available",
                "planes": [
                    {"normal": [1, 0, 0], "offset_mm": 4.0, "precision_mm": 2.0}
                ],
            }
        ]
    }
    assert window_scope_codes(candidate, [window], prior) == ["eligible"]
    prior["cases"][0]["planes"][0]["precision_mm"] = None
    assert window_scope_codes(candidate, [window], prior) == ["geometry_unavailable"]
