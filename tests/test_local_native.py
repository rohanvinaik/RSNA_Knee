from typing import cast

import numpy as np

from knee.collapse.local_native import enclosed_body_at_sources, source_window
from knee.collapse.menisci import meniscus_local_body
from knee.collapse.physical import PlaneFrame


def _oblique_frame() -> PlaneFrame:
    angle = np.pi / 4.0
    row_direction = np.array([np.cos(angle), np.sin(angle), 0.0])
    column_direction = np.array([-np.sin(angle), np.cos(angle), 0.0])
    orientation = np.concatenate((row_direction, column_direction))
    return PlaneFrame.from_dicom(np.array([30.0, -12.0, 4.0]), orientation, (2.0, 0.5))


def test_source_window_projects_oblique_physical_span_through_anisotropic_pixels():
    frame = _oblique_frame()
    result = source_window(
        np.array([[20.2, 30.1], [21.0, 31.0]]), (10.0, 6.0, 4.0), frame, (100, 100)
    )
    assert result["status"] == "present"
    np.testing.assert_allclose(
        result["projected_half_span_pixels_rc"],
        [8.0 / np.sqrt(2) / 2.0, 8.0 / np.sqrt(2) / 0.5],
    )
    assert result["target_bbox_rc_exclusive"] == [20, 22, 30, 32]
    assert result["window_rc_exclusive"] == [17, 25, 18, 44]


def test_source_window_full_extent_padding_reaches_opposite_object_corner():
    frame = _oblique_frame()
    source = np.array([[40.0, 60.0]])
    source_lps = frame.to_patient(source)
    point_to_point_extent = np.array([10.0, 6.0, 4.0])
    opposite_corner_rc = frame.to_native(source_lps + point_to_point_extent)[0]
    window = source_window(
        source,
        tuple(2.0 * point_to_point_extent),
        frame,
        (100, 120),
    )
    assert window["status"] == "present"
    r0, r1, c0, c1 = window["window_rc_exclusive"]
    opposite_row, opposite_column = np.rint(opposite_corner_rc).astype(int)
    assert r0 <= opposite_row < r1
    assert c0 <= opposite_column < c1


def test_source_window_handles_reflected_frame_and_clips_explicitly():
    frame = PlaneFrame.from_dicom(
        np.zeros(3), np.array([0.0, 1.0, 0.0, 1.0, 0.0, 0.0]), (1.0, 1.0)
    )
    result = source_window(np.array([[0.0, 0.0]]), (4.0, 2.0, 2.0), frame, (8, 8))
    assert result["status"] == "window_clipped_to_image"
    assert result["window_clipped_to_image"] is True
    assert result["window_rc_exclusive"] == [0, 3, 0, 2]


def test_source_window_rejects_degenerate_and_nonfinite_plane_frame_geometry():
    source = np.array([[2.0, 3.0]])
    span = (2.0, 2.0, 2.0)
    degenerate = PlaneFrame(np.zeros(3), np.zeros((3, 2)), (1.0, 1.0))
    assert (
        source_window(source, span, degenerate, (8, 8))["status"]
        == "degenerate_frame_basis"
    )

    nonfinite_origin = PlaneFrame(
        np.array([np.nan, 0.0, 0.0]), np.eye(3)[:, :2], (1.0, 1.0)
    )
    assert (
        source_window(source, span, nonfinite_origin, (8, 8))["status"]
        == "nonfinite_frame_geometry"
    )


def test_source_window_rejects_bad_spans_shapes_and_out_of_bounds_points_by_name():
    frame = _oblique_frame()
    assert (
        source_window(np.empty((0, 2)), (1.0, 1.0, 1.0), frame, (8, 8))["status"]
        == "empty_source"
    )
    assert (
        source_window(np.array([[1.0, 1.0]]), (-1.0, 1.0, 1.0), frame, (8, 8))["status"]
        == "nonpositive_span"
    )
    assert (
        source_window(np.array([[np.inf, 1.0]]), (1.0, 1.0, 1.0), frame, (8, 8))[
            "status"
        ]
        == "nonfinite_source"
    )
    outside = source_window(np.array([[-0.6, 1.0]]), (1.0, 1.0, 1.0), frame, (8, 8))
    assert outside["status"] == "source_out_of_bounds"
    assert outside["source_out_of_bounds_pixels"] == 1
    assert (
        source_window(np.array([1.0, 1.0]), (1.0, 1.0, 1.0), frame, (8, 8))["status"]
        == "malformed_source_shape"
    )


def test_shared_body_thickness_is_physical_and_two_mm_wrapper_is_unchanged():
    frame = PlaneFrame.from_dicom(
        np.zeros(3), np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0]), (0.5, 0.5)
    )
    raw = np.full((32, 40), 10.0)
    raw[10:22, 14:19] = 2.0
    available = np.ones(raw.shape, dtype=bool)
    target = np.zeros(raw.shape, dtype=bool)
    target[16, 12] = True

    old_thickness = enclosed_body_at_sources(
        raw, available, target, frame, thickness_mm=2.0
    )
    three_mm = enclosed_body_at_sources(raw, available, target, frame, thickness_mm=3.0)
    wrapper = meniscus_local_body(raw, available, target, frame)

    assert old_thickness.keys() == wrapper.keys()
    for key, value in old_thickness.items():
        if isinstance(value, np.ndarray):
            np.testing.assert_array_equal(value, wrapper[key])
        else:
            assert value == wrapper[key]
    assert old_thickness["opened_pixels"] > 0
    assert three_mm["opened_pixels"] == 0
    assert old_thickness["status"] == "identified"
    assert three_mm["status"] == "measured_empty"


def test_shared_body_rejects_nonpositive_or_nonfinite_thickness_by_name():
    raw = np.full((12, 14), 8.0)
    available = np.ones(raw.shape, dtype=bool)
    target = np.zeros(raw.shape, dtype=bool)
    target[6, 7] = True
    frame = _oblique_frame()

    for thickness in (0.0, -1.0, np.nan, np.inf, True, None, "bad"):
        result = enclosed_body_at_sources(
            raw, available, target, frame, thickness_mm=cast(float, thickness)
        )
        assert result["status"] == "invalid_thickness"
        assert result["selection_status"] == "unmeasured"
        assert result["opened"] is None
