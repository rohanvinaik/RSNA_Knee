from typing import cast

import numpy as np
from scipy import ndimage as ndi

from knee.collapse.local_native import (
    enclosed_body_at_sources,
    enclosed_components_at_source,
    source_window,
)
from knee.collapse.menisci import meniscus_local_body
from knee.collapse.physical import PlaneFrame
from knee.objects import assignments as A


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


def test_enclosed_components_measure_once_and_keep_every_four_connected_component(
    monkeypatch,
):
    frame = PlaneFrame.from_dicom(
        np.zeros(3), np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0]), (2.0, 0.5)
    )
    raw = np.full((12, 14), 10.0)
    raw[3, 3] = np.nan
    available = np.ones(raw.shape, dtype=bool)
    available[2, 2] = False
    target = np.zeros(raw.shape, dtype=bool)
    target[4, 4] = True
    depth = np.zeros(raw.shape, dtype=np.float64)
    depth[4, 6:8] = 1.0  # one contacted two-pixel component
    depth[5, 4] = 1.0  # exactly on the existing two-mm contact shell
    depth[5, 8] = 1.0  # diagonal only: FOUR-connectivity keeps it separate
    depth[8, 4] = 1.0
    depth[0, 10] = 1.0  # crop-edge component
    calls = []

    def enclosed_once(plane):
        calls.append(plane.copy())
        return depth

    def forbidden_opening(*_args, **_kwargs):
        raise AssertionError("component measurement must not call thick_parts")

    monkeypatch.setattr(A, "enclosed_darkness", enclosed_once)
    monkeypatch.setattr(A, "thick_parts", forbidden_opening)
    result = enclosed_components_at_source(raw, available, target, frame)

    assert result["status"] == "partial_reading"
    assert result["partial_reading"] is True
    assert result["enclosure_status"] == "present"
    assert len(calls) == 1
    assert np.isfinite(calls[0]).all()
    assert calls[0][3, 3] == result["neutral_minimum"]
    assert result["component_count"] == 5
    assert result["contacted_component_count"] == 2
    assert result["contacted_component_sizes_pixels"] == [2, 1]
    assert int(result["contacted_component_mask"].sum()) == 3
    assert result["distance_to_target_mm"][5, 4] == 2.0
    assert result["distance_to_target_mm"][5, 8] == np.sqrt(8.0)
    rows = result["components"]
    assert sorted(row["pixels"] for row in rows) == [1, 1, 1, 1, 2]
    edge_rows = [row for row in rows if row["touches_crop_edge"]]
    assert len(edge_rows) == 1 and edge_rows[0]["crop_edge_pixels"] == 1
    assert result["positive_enclosure"][2, 2] is np.False_
    assert result["labels"].dtype == np.int32


def test_enclosed_component_reductions_match_mask_loop_reference_on_random_inputs(
    monkeypatch,
):
    rng = np.random.default_rng(2041)
    spacings = ((0.25, 2.0), (0.5, 1.5), (1.25, 0.75), (2.5, 0.4))

    for case in range(80):
        shape = (int(rng.integers(2, 14)), int(rng.integers(2, 15)))
        raw = rng.normal(size=shape)
        if case % 3 == 0:
            raw.flat[int(rng.integers(raw.size))] = np.nan
        available = rng.random(shape) > 0.15
        target = np.zeros(shape, dtype=bool)
        target_rc = (int(rng.integers(shape[0])), int(rng.integers(shape[1])))
        target[target_rc] = True
        available[target_rc] = True
        synthetic_depth = (rng.random(shape) > 0.72).astype(np.float64)
        spacing = spacings[case % len(spacings)]
        frame = PlaneFrame.from_dicom(
            np.zeros(3),
            np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0]),
            spacing,
        )
        monkeypatch.setattr(
            A,
            "enclosed_darkness",
            lambda _plane, depth=synthetic_depth: depth.copy(),
        )

        result = enclosed_components_at_source(raw, available, target, frame)
        effective = available & np.isfinite(raw)
        expected_labels, expected_count = ndi.label(
            (synthetic_depth > 0.0) & effective,
            structure=A.FOUR_NEIGHBOURS,
        )
        expected_distance = ndi.distance_transform_edt(
            ~(target & effective), sampling=spacing
        )
        edge = np.zeros(shape, dtype=bool)
        edge[[0, -1], :] = True
        edge[:, [0, -1]] = True
        unknown_boundary = (
            ndi.binary_dilation(~effective, structure=A.FOUR_NEIGHBOURS) & effective
        )

        assert result["component_count"] == expected_count
        assert result["positive_enclosure_pixels"] == int(
            expected_labels.astype(bool).sum()
        )
        np.testing.assert_array_equal(result["labels"], expected_labels)
        np.testing.assert_array_equal(
            result["distance_to_target_mm"], expected_distance
        )
        expected_rows = []
        expected_contacted = []
        for label in range(1, expected_count + 1):
            component = expected_labels == label
            minimum_distance = float(expected_distance[component].min())
            edge_pixels = int(np.count_nonzero(component & edge))
            within_shell = minimum_distance <= A.SHELL_MM
            expected_rows.append(
                {
                    "label": label,
                    "pixels": int(component.sum()),
                    "minimum_target_distance_mm": minimum_distance,
                    "within_existing_contact_shell": bool(within_shell),
                    "crop_edge_pixels": edge_pixels,
                    "touches_crop_edge": bool(edge_pixels),
                    "unknown_boundary_pixels": int(
                        np.count_nonzero(component & unknown_boundary)
                    ),
                    "touches_unavailable_boundary": bool(
                        np.any(component & unknown_boundary)
                    ),
                }
            )
            if within_shell:
                expected_contacted.append(label)
        assert result["components"] == expected_rows
        assert result["contacted_component_ids"] == expected_contacted
        assert result["contacted_component_count"] == len(expected_contacted)
        assert result["crop_edge_pixels"] == int(edge.sum())
        assert result["contacted_component_sizes_pixels"] == [
            row["pixels"] for row in expected_rows if row["label"] in expected_contacted
        ]
        expected_mask = np.isin(expected_labels, expected_contacted)
        np.testing.assert_array_equal(result["contacted_component_mask"], expected_mask)


def test_enclosed_components_shift_invariant_under_finite_intensity_translation():
    frame = PlaneFrame.from_dicom(
        np.zeros(3), np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0]), (0.75, 1.5)
    )
    raw = np.full((18, 20), 40.0)
    raw[5:13, 6:15] = 23.0
    available = np.ones(raw.shape, dtype=bool)
    target = np.zeros(raw.shape, dtype=bool)
    target[9, 5] = True
    first = enclosed_components_at_source(raw, available, target, frame)
    shifted = enclosed_components_at_source(raw + 17.25, available, target, frame)
    assert first["status"] == shifted["status"] == "complete"
    np.testing.assert_allclose(first["enclosed_depth"], shifted["enclosed_depth"])
    np.testing.assert_array_equal(
        first["positive_enclosure"], shifted["positive_enclosure"]
    )
    np.testing.assert_array_equal(first["labels"], shifted["labels"])
    np.testing.assert_allclose(
        first["distance_to_target_mm"], shifted["distance_to_target_mm"]
    )
    assert first["components"] == shifted["components"]


def test_enclosed_components_names_malformed_empty_and_unavailable_inputs():
    raw = np.ones((4, 5), dtype=np.float64)
    available = np.ones(raw.shape, dtype=bool)
    target = np.zeros(raw.shape, dtype=bool)
    frame = PlaneFrame.from_dicom(
        np.zeros(3), np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0]), (1.0, 1.0)
    )

    assert (
        enclosed_components_at_source(np.ones(3), available, target, frame)["status"]
        == "malformed_raw_shape"
    )
    assert (
        enclosed_components_at_source(
            np.empty((0, 5)), available[:0], target[:0], frame
        )["status"]
        == "empty_raw"
    )
    assert (
        enclosed_components_at_source(raw.astype(object), available, target, frame)[
            "status"
        ]
        == "malformed_raw_dtype"
    )
    assert (
        enclosed_components_at_source(raw, available[:, :2], target, frame)["status"]
        == "malformed_availability_shape"
    )
    assert (
        enclosed_components_at_source(raw, available.astype(np.uint8), target, frame)[
            "status"
        ]
        == "malformed_availability_dtype"
    )
    assert (
        enclosed_components_at_source(raw, available, target[:, :2], frame)["status"]
        == "malformed_target_shape"
    )
    assert (
        enclosed_components_at_source(raw, available, target.astype(np.uint8), frame)[
            "status"
        ]
        == "malformed_target_dtype"
    )
    assert (
        enclosed_components_at_source(raw, available, target, cast(PlaneFrame, None))[
            "status"
        ]
        == "invalid_frame"
    )
    invalid_spacing = PlaneFrame(frame.origin_lps, frame.basis_lps, (np.nan, 1.0))
    assert (
        enclosed_components_at_source(raw, available, target, invalid_spacing)["status"]
        == "invalid_spacing"
    )

    assert (
        enclosed_components_at_source(raw, available, target, frame)["status"]
        == "target_missing"
    )
    target[1, 1] = True
    unavailable = np.zeros(raw.shape, dtype=bool)
    assert (
        enclosed_components_at_source(raw, unavailable, target, frame)["status"]
        == "no_available_pixels"
    )
    partial_target = target.copy()
    partial_availability = available.copy()
    partial_availability[target] = False
    result = enclosed_components_at_source(
        raw, partial_availability, partial_target, frame
    )
    assert result["status"] == "target_unavailable"
    assert result["available_pixels"] == raw.size - 1
    assert result["effective_availability"] is not None

    complete_empty = enclosed_components_at_source(raw, available, target, frame)
    assert complete_empty["status"] == "complete"
    assert complete_empty["enclosure_status"] == "empty"
    assert complete_empty["component_count"] == 0
