from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from knee.collapse.anatomy_map import ideal_vector

MODULE_PATH = (
    Path(__file__).parents[1] / "src/knee/diagnosis/squint_anatomical_priors.py"
)
_SPEC = importlib.util.spec_from_file_location("squint_anatomical_priors", MODULE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
anatomical_windows = _MODULE.anatomical_windows


def _series(*, shape=(3, 33, 33), origin=(-128.0, -128.0, 96.0), step=8.0):
    z, rows, cols = np.indices(shape, dtype=np.float64)
    centres = np.empty((*shape, 3), dtype=np.float64)
    centres[..., 0] = origin[0] + cols * step
    centres[..., 1] = origin[1] + rows * step
    centres[..., 2] = origin[2] + z * step
    bounds = np.empty((rows.shape[1], cols.shape[2], 4), dtype=np.int64)
    tile_rows, tile_cols = bounds.shape[:2]
    row = np.arange(tile_rows, dtype=np.int64)
    col = np.arange(tile_cols, dtype=np.int64)
    bounds[..., 0] = row[:, None] * 4
    bounds[..., 1] = (row[:, None] + 1) * 4
    bounds[..., 2] = col[None, :] * 4
    bounds[..., 3] = (col[None, :] + 1) * 4
    stack = SimpleNamespace(
        code="present",
        centres_lps=centres,
        coverage=np.ones(shape, dtype=np.float64),
        bounds_rc=bounds,
    )
    low = np.min(centres, axis=(0, 1, 2)) - step
    high = np.max(centres, axis=(0, 1, 2)) + step
    return {"stack": stack}, (tuple(low.tolist()), tuple(high.tolist()))


def _expected(anchor: tuple[float, float, float], side: str, scale=None):
    vector = ideal_vector("femur", "medial_meniscus", scale)
    assert vector is not None
    medial_sign = -1.0 if side == "left" else 1.0
    return np.asarray(anchor) + np.asarray(
        (
            medial_sign * vector.anatomical_mm[0],
            vector.anatomical_mm[1],
            vector.anatomical_mm[2],
        )
    )


def _anchors(point=(0.0, 0.0, 108.0)):
    return {
        "femur": {
            "status": "complete",
            "point_lps": list(point),
            "precision_mm": [0.5, 0.5, 0.5],
        }
    }


def test_current_anchor_translation_preserves_native_windows():
    original_anchor = np.asarray((0.0, 0.0, 108.0))
    expected = _expected(tuple(original_anchor), "left")
    series, bounds = _series(
        origin=(expected[0] - 16 * 8, expected[1] - 16 * 8, expected[2] - 8)
    )
    first = anatomical_windows(
        series,
        "medial_meniscus",
        leg_bounds_lps=bounds,
        anchors=_anchors(tuple(original_anchor)),
        knee_side="left",
    )

    shift = np.asarray((41.0, -27.0, 13.0))
    moved_series, moved_bounds = _series(
        origin=(
            expected[0] + shift[0] - 16 * 8,
            expected[1] + shift[1] - 16 * 8,
            expected[2] + shift[2] - 8,
        )
    )
    moved = anatomical_windows(
        moved_series,
        "medial_meniscus",
        leg_bounds_lps=moved_bounds,
        anchors=_anchors(tuple(original_anchor + shift)),
        knee_side="left",
    )

    assert first["status"] == moved["status"] == "proposed"
    assert first["windows"] == moved["windows"]
    assert (
        first["provenance"]["hypotheses"][0]["kind"] == "current_anchor_relative_prior"
    )
    first_point = first["provenance"]["hypotheses"][0]["expected_point_lps"]
    moved_point = moved["provenance"]["hypotheses"][0]["expected_point_lps"]
    np.testing.assert_allclose(np.asarray(moved_point) - first_point, shift)


def test_left_and_right_keep_mirrored_prior_hypotheses():
    anchor = (0.0, 0.0, 108.0)
    left_expected = _expected(anchor, "left")
    series, bounds = _series(
        shape=(3, 41, 41),
        origin=(min(left_expected[0], -left_expected[0]) - 20 * 8, -160.0, 96.0),
    )
    left = anatomical_windows(
        series,
        "medial_meniscus",
        leg_bounds_lps=bounds,
        anchors=_anchors(anchor),
        knee_side="left",
    )
    right = anatomical_windows(
        series,
        "medial_meniscus",
        leg_bounds_lps=bounds,
        anchors=_anchors(anchor),
        knee_side="right",
    )

    left_point = np.asarray(left["provenance"]["hypotheses"][0]["expected_point_lps"])
    right_point = np.asarray(right["provenance"]["hypotheses"][0]["expected_point_lps"])
    assert left_point[0] == -right_point[0]
    assert left["windows"] != right["windows"]

    unknown = anatomical_windows(
        series,
        "medial_meniscus",
        leg_bounds_lps=bounds,
        anchors=_anchors(anchor),
        knee_side=None,
    )
    assert unknown["status"] == "proposed_unknown_side"
    assert (
        unknown["provenance"]["knee_side_status"]
        == "unknown_both_mirrored_hypotheses_retained"
    )
    assert len(unknown["provenance"]["hypotheses"]) == 2
    assert {
        row["knee_side_hypothesis"] for row in unknown["provenance"]["hypotheses"]
    } == {
        "left_hypothesis",
        "right_hypothesis",
    }


def test_unanchored_bone_uses_named_leg_frame_prior_only():
    series, bounds = _series()
    result = anatomical_windows(
        series,
        "femur",
        leg_bounds_lps=bounds,
        anchors={},
        knee_side="left",
    )
    provenance = result["provenance"]
    assert provenance["leg_frame_prior_used"] is True
    assert provenance["hypotheses"][0]["kind"] == "leg_frame_prior"
    assert (
        provenance["hypotheses"][0]["origin_status"]
        == "measured_leg_extents_midpoint_used_only_as_initial_prior"
    )
    assert provenance["identity_assertion"] is None
    assert all(z1 == z0 + 1 for z0, z1, *_ in result["windows"])


def test_unknown_side_retains_two_initial_bone_hypotheses():
    series, bounds = _series(shape=(3, 41, 41), origin=(-160.0, -160.0, 96.0))
    result = anatomical_windows(
        series,
        "tibia",
        leg_bounds_lps=bounds,
        anchors={},
        knee_side=None,
    )
    assert result["status"] == "proposed_unknown_side"
    assert len(result["provenance"]["hypotheses"]) == 2
    assert result["provenance"]["leg_frame_prior_used"] is True
    assert all(z1 == z0 + 1 for z0, z1, *_ in result["windows"])


def test_partial_native_plane_guides_only_its_measured_axis_and_keeps_reference():
    series, bounds = _series()
    lower, upper = np.asarray(bounds[0]), np.asarray(bounds[1])
    midpoint = (lower + upper) / 2
    selected_offset = float(midpoint[0] + 16.0)
    native_reference = {
        "status": "partial",
        "geometry": "not_enough_planes",
        "point_lps": None,
        "precision_mm": None,
        "rank": 1,
        "problems": {"coronal": "not_supplied", "axial": "tied"},
    }
    planes = {
        "sagittal": {
            "orientation": "sagittal",
            "outcome": "selected",
            "normal": [1.0, 0.0, 0.0],
            "offset_mm": selected_offset,
            "precision_mm": 0.5,
            "series_uid": "current-sagittal",
            "slice": 1,
            "candidates": [],
        },
        "coronal": {
            "orientation": "coronal",
            "outcome": "not_supplied",
            "normal": None,
            "offset_mm": None,
            "precision_mm": None,
            "candidates": [],
        },
        "axial": {
            "orientation": "axial",
            "outcome": "tied",
            "normal": None,
            "offset_mm": None,
            "precision_mm": None,
            "candidates": [["axial-a", 2], ["axial-b", 4]],
        },
    }
    original = {"reference": native_reference.copy(), "planes": planes.copy()}
    result = anatomical_windows(
        series,
        "medial_meniscus",
        leg_bounds_lps=bounds,
        anchors={"femur": original},
        knee_side="left",
    )

    hypothesis = result["provenance"]["hypotheses"][0]
    seed_vector = ideal_vector("joint", "femur")
    target_vector = ideal_vector("femur", "medial_meniscus")
    assert seed_vector is not None and target_vector is not None
    seed = midpoint + np.asarray(
        (
            -seed_vector.anatomical_mm[0],
            seed_vector.anatomical_mm[1],
            seed_vector.anatomical_mm[2],
        )
    )
    projected = seed.copy()
    projected[0] = selected_offset
    expected = projected + np.asarray(
        (
            -target_vector.anatomical_mm[0],
            target_vector.anatomical_mm[1],
            target_vector.anatomical_mm[2],
        )
    )
    np.testing.assert_allclose(hypothesis["projected_anchor_prior_lps"], projected)
    np.testing.assert_allclose(hypothesis["expected_point_lps"], expected)
    assert hypothesis["kind"] == "partial_native_planes_guided_prior"
    assert hypothesis["anchor_observation_status"] == "partial"
    assert hypothesis["prior_only"] is True
    assert hypothesis["projection_rank"] == 1
    assert [row["orientation"] for row in hypothesis["selected_native_planes"]] == [
        "sagittal"
    ]
    ignored = {row["orientation"]: row for row in hypothesis["ignored_planes"]}
    assert ignored["axial"]["outcome"] == "tied"
    assert ignored["axial"]["candidates"] == [["axial-a", 2], ["axial-b", 4]]
    assert original["reference"] == native_reference
    assert original["planes"] == planes
    assert native_reference["point_lps"] is None


def test_partial_native_planes_retain_translation_covariance():
    series, bounds = _series()
    partial = {
        "reference": {
            "status": "partial",
            "geometry": "not_enough_planes",
            "point_lps": None,
            "precision_mm": None,
        },
        "planes": {
            "sagittal": {
                "orientation": "sagittal",
                "outcome": "selected",
                "normal": [1.0, 0.0, 0.0],
                "offset_mm": 4.0,
                "precision_mm": 0.5,
            },
            "coronal": {"orientation": "coronal", "outcome": "not_supplied"},
            "axial": {"orientation": "axial", "outcome": "not_supplied"},
        },
    }
    first = anatomical_windows(
        series,
        "medial_meniscus",
        leg_bounds_lps=bounds,
        anchors={"femur": partial},
        knee_side="left",
    )
    delta = np.asarray((32.0, -24.0, 16.0))
    moved_series, moved_bounds = _series(
        origin=(-128.0 + delta[0], -128.0 + delta[1], 96.0 + delta[2])
    )
    moved_partial = {
        "reference": partial["reference"],
        "planes": {
            **partial["planes"],
            "sagittal": {
                **partial["planes"]["sagittal"],
                "offset_mm": 4.0 + delta[0],
            },
        },
    }
    moved = anatomical_windows(
        moved_series,
        "medial_meniscus",
        leg_bounds_lps=moved_bounds,
        anchors={"femur": moved_partial},
        knee_side="left",
    )
    assert first["windows"] == moved["windows"]
    np.testing.assert_allclose(
        np.asarray(moved["provenance"]["hypotheses"][0]["expected_point_lps"])
        - first["provenance"]["hypotheses"][0]["expected_point_lps"],
        delta,
    )


def test_tied_only_and_nan_selected_plane_are_not_used_as_native_anchor():
    series, bounds = _series()
    planes = {
        "sagittal": {
            "orientation": "sagittal",
            "outcome": "selected",
            "normal": [float("nan"), 0.0, 0.0],
            "offset_mm": 2.0,
        },
        "coronal": {"orientation": "not_supplied", "outcome": "not_supplied"},
        "axial": {
            "orientation": "axial",
            "outcome": "tied",
            "normal": [0.0, 0.0, 1.0],
            "offset_mm": 108.0,
            "candidates": [["a", 0], ["b", 1]],
        },
    }
    result = anatomical_windows(
        series,
        "medial_meniscus",
        leg_bounds_lps=bounds,
        anchors={
            "femur": {
                "reference": {
                    "status": "partial",
                    "geometry": "not_enough_planes",
                    "point_lps": None,
                },
                "planes": planes,
            }
        },
        knee_side="left",
    )
    assert result["status"] == "relative_reference_unavailable"
    assert result["windows"] == []
    detail = result["provenance"]["rejected_anchors"][0]["details"]
    ignored = {row["orientation"]: row for row in detail["ignored_planes"]}
    assert ignored["sagittal"]["outcome"] == "selected_geometry_invalid"
    assert ignored["axial"]["outcome"] == "tied"
    assert ignored["axial"]["candidates"] == [["a", 0], ["b", 1]]


def test_nonbone_without_native_anchor_does_not_search_leg_exhaustively():
    series, bounds = _series()
    result = anatomical_windows(
        series,
        "medial_meniscus",
        leg_bounds_lps=bounds,
        anchors={},
        knee_side="left",
    )
    assert result["status"] == "relative_reference_unavailable"
    assert result["windows"] == []


def test_missing_subject_stack_and_empty_foreground_are_named_silences():
    unknown = anatomical_windows(
        {"stack": None},
        "not_an_object",
        leg_bounds_lps=None,
        anchors={},
    )
    assert unknown["status"] == "subject_unknown"

    absent = anatomical_windows(
        {"stack": SimpleNamespace(code="geometry_unreadable")},
        "femur",
        leg_bounds_lps=None,
        anchors={},
    )
    assert absent["status"] == "stack_geometry_unreadable"

    series, bounds = _series()
    series["stack"].centres_lps[:] = np.nan
    empty = anatomical_windows(
        series,
        "femur",
        leg_bounds_lps=bounds,
        anchors={},
        knee_side="left",
    )
    assert empty["status"] == "no_finite_current_foreground_tiles"
    assert empty["windows"] == []


def test_windows_are_valid_half_open_one_slice_and_respect_foreground_bounds():
    series, bounds = _series()
    result = anatomical_windows(
        series,
        "femur",
        leg_bounds_lps=bounds,
        anchors={},
        knee_side="left",
    )
    z_size, row_size, col_size = series["stack"].centres_lps.shape[:3]
    assert result["windows"]
    for z0, z1, row0, row1, col0, col1 in result["windows"]:
        assert 0 <= z0 < z1 <= z_size
        assert z1 == z0 + 1
        assert 0 <= row0 < row1 <= row_size
        assert 0 <= col0 < col1 <= col_size
    assert result["provenance"]["candidate_count"] == len(result["windows"])
    assert result["provenance"]["identity_assertion"] is None


def test_malformed_stack_bounds_and_degenerate_leg_extents_are_refused():
    series, bounds = _series()
    series["stack"].bounds_rc = np.zeros((1, 1, 4), dtype=np.int64)
    malformed = anatomical_windows(
        series,
        "femur",
        leg_bounds_lps=bounds,
        anchors={},
        knee_side="left",
    )
    assert malformed["status"] == "native_bounds_shape_invalid"

    valid_series, _ = _series()
    degenerate = anatomical_windows(
        valid_series,
        "femur",
        leg_bounds_lps=((0, 0, 0), (0, 1, 1)),
        anchors={},
        knee_side="left",
    )
    assert degenerate["status"] == "leg_bounds_invalid"


def test_candidate_cardinality_depends_on_geometry_not_case_population():
    series, bounds = _series()
    one = anatomical_windows(
        series,
        "femur",
        leg_bounds_lps=bounds,
        anchors={},
        knee_side=None,
    )
    # Stored precedent count is deliberately not an input to this geometric proposal API.
    nominal_stored_case_counts = (1, 58, 10_000)
    results = [
        anatomical_windows(
            series,
            "femur",
            leg_bounds_lps=bounds,
            anchors={},
            knee_side=None,
        )
        for _ in nominal_stored_case_counts
    ]
    assert all(result["windows"] == one["windows"] for result in results)
    assert one["provenance"]["candidate_count"] <= 2 * 7 * 3 * 3


def test_foreground_mask_absence_empty_and_malformed_are_named():
    series, bounds = _series()
    absent = anatomical_windows(
        series,
        "femur",
        leg_bounds_lps=bounds,
        anchors={},
        knee_side="left",
    )
    assert absent["provenance"]["foreground_mask_status"] == (
        "not_supplied_geometry_only_prior"
    )

    series["foreground"] = np.zeros(series["stack"].coverage.shape, dtype=bool)
    empty = anatomical_windows(
        series,
        "femur",
        leg_bounds_lps=bounds,
        anchors={},
        knee_side="left",
    )
    assert empty["status"] == "no_finite_current_foreground_tiles"
    assert empty["windows"] == []
    assert empty["provenance"]["foreground_mask_status"] == (
        "provided_current_study_mask"
    )
    assert empty["provenance"]["foreground_mask_true_count"] == 0

    series["foreground"] = np.ones((1, 1, 1), dtype=bool)
    wrong_shape = anatomical_windows(
        series,
        "femur",
        leg_bounds_lps=bounds,
        anchors={},
        knee_side="left",
    )
    assert wrong_shape["status"] == "foreground_mask_unavailable"
    assert wrong_shape["windows"] == []

    series["foreground"] = np.ones(series["stack"].coverage.shape, dtype=np.uint8)
    wrong_type = anatomical_windows(
        series,
        "femur",
        leg_bounds_lps=bounds,
        anchors={},
        knee_side="left",
    )
    assert wrong_type["status"] == "foreground_mask_unavailable"
    assert wrong_type["windows"] == []


def test_predicted_background_centre_uses_nearest_eligible_foreground_tile():
    series, bounds = _series()
    stack = series["stack"]
    foreground = np.zeros(stack.coverage.shape, dtype=bool)
    foreground_tile = (1, 16, 16)
    foreground[foreground_tile] = True
    series["foreground"] = foreground

    result = anatomical_windows(
        series,
        "femur",
        leg_bounds_lps=bounds,
        anchors={},
        knee_side="left",
    )

    assert result["windows"]
    assert result["provenance"]["foreground_mask_status"] == (
        "provided_current_study_mask"
    )
    assert result["provenance"]["foreground_mask_true_count"] == 1
    sources = [
        source
        for row in result["provenance"]["window_sources"]
        for source in row["sources"]
    ]
    assert sources
    assert {tuple(source["nearest_tile_index"]) for source in sources} == {
        foreground_tile
    }
