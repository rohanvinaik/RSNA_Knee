from __future__ import annotations

from typing import cast

import numpy as np
import pytest

from knee.collapse.native_sampling import sample_native_points
from knee.collapse.physical import PlaneFrame

SHAPE = (4, 4)


def frame_at(z: float, *, reverse: bool = False) -> PlaneFrame:
    row_direction = np.array([0.0, -1.0, 0.0])
    column_direction = np.array([1.0, 0.0, 0.0])
    if reverse:
        row_direction = -row_direction
    basis = np.column_stack((row_direction, column_direction))
    return PlaneFrame(np.array([0.0, 0.0, z]), basis, (1.0, 1.0))


def point_at(
    frame: PlaneFrame, row: float, column: float, z: float | None = None
) -> np.ndarray:
    point = frame.to_patient(np.array([[row, column]], dtype=np.float64))[0].copy()
    if z is not None:
        point[2] = z
    return point


def test_samples_nearest_oblique_or_reversed_planes_once_each() -> None:
    first = frame_at(0.0)
    second = frame_at(2.0, reverse=True)
    points = np.stack(
        (
            point_at(first, 1, 2, 0.2),
            point_at(first, 1.4, 2.4, 0.2),
            point_at(second, 2, 1, 2.2),
        )
    )
    calls: list[int] = []

    def read(z: int) -> tuple[np.ndarray, bool]:
        calls.append(z)
        return (np.arange(16, dtype=np.int16).reshape(SHAPE) + 100 * z), False

    result = sample_native_points(points, [first, second], [1.0, 1.0], SHAPE, read)

    assert result.status == ("valid", "valid", "valid")
    assert result.selected_z.tolist() == [0, 0, 1]
    assert result.native_rc.tolist() == [[1, 2], [1, 2], [2, 1]]
    assert result.signed_distance_mm.tolist() == pytest.approx([0.2, 0.2, -0.2])
    assert result.signal.tolist() == [6.0, 6.0, 109.0]
    assert calls == [0, 1]


def test_tied_nearest_planes_and_outside_slab_are_not_sampled() -> None:
    first = frame_at(0.0)
    duplicate = frame_at(0.0, reverse=True)
    distant = frame_at(4.0)
    calls: list[int] = []

    def read(z: int) -> tuple[np.ndarray, bool]:
        calls.append(z)
        return np.ones(SHAPE), False

    tied = sample_native_points(
        point_at(first, 1, 1, 0.0)[None, :],
        [first, duplicate, distant],
        [1.0, 1.0, 1.0],
        SHAPE,
        read,
    )
    outside = sample_native_points(
        point_at(first, 1, 1, 1.6)[None, :], [first, distant], [1.0, 1.0], SHAPE, read
    )

    assert tied.status == ("nearest_plane_tie",)
    assert outside.status == ("outside_slab",)
    assert tied.selected_z.tolist() == [-1]
    assert outside.selected_z.tolist() == [0]
    assert calls == []


def test_nearest_tolerance_uses_global_minimum_and_is_frame_order_invariant() -> None:
    epsilon = np.finfo(np.float64).eps
    origins = [1.0, 1.0 + 9.0 * epsilon, 1.0 + 14.0 * epsilon]
    point = point_at(frame_at(0.0), 1, 1, 0.0)[None, :]
    observed: list[float] = []

    for order in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
        frames = [frame_at(origins[index]) for index in order]
        result = sample_native_points(
            point, frames, [4.0, 4.0, 4.0], SHAPE, lambda _: (np.ones(SHAPE), False)
        )
        selected_origin = origins[order[int(result.selected_z[0])]]
        observed.append(selected_origin)
        assert result.status == ("valid",)
        assert selected_origin == origins[0]

    assert observed == [origins[0]] * 3


def test_nearest_tolerance_boundary_matches_global_reference() -> None:
    frame = frame_at(0.0)
    point = point_at(frame, 1, 1, 0.0)[None, :]
    origin = 1.0
    eight_steps = origin
    for _ in range(8):
        eight_steps = np.nextafter(eight_steps, np.inf)
    frames = [frame_at(origin), frame_at(eight_steps)]
    distances = [abs(float(candidate.origin_lps[2])) for candidate in frames]
    minimum = min(distances)
    tolerance = 8.0 * np.finfo(np.float64).eps * max(1.0, minimum)
    reference_ties = sum(abs(distance - minimum) <= tolerance for distance in distances)

    result = sample_native_points(
        point, frames, [4.0, 4.0], SHAPE, lambda _: (np.ones(SHAPE), False)
    )

    assert reference_ties == 2
    assert result.status == ("nearest_plane_tie",)
    assert result.selected_z.tolist() == [-1]


def test_half_pixel_span_is_lower_inclusive_and_upper_exclusive() -> None:
    frame = frame_at(0.0)
    points = np.stack(
        (
            point_at(frame, -0.5, 1.0),
            point_at(frame, SHAPE[0] - 0.5, 1.0),
        )
    )
    result = sample_native_points(
        points, [frame], [1.0], SHAPE, lambda _: (np.ones(SHAPE), False)
    )

    assert result.status == ("valid", "outside_image")
    assert result.native_rc.tolist() == [[0, 1], [-1, -1]]


def test_outside_slab_gap_and_nearest_tie_between_acquired_planes() -> None:
    first, second = frame_at(0.0), frame_at(4.0)
    points = np.stack(
        (
            point_at(first, 1, 1, 1.0),
            point_at(first, 1, 1, 2.0),
        )
    )
    calls: list[int] = []
    result = sample_native_points(
        points,
        [first, second],
        [1.0, 1.0],
        SHAPE,
        lambda z: (calls.append(z) or np.ones(SHAPE), False),
    )
    assert result.status == ("outside_slab", "nearest_plane_tie")
    assert calls == []


def test_overlapping_half_thickness_slabs_still_use_nearest_plane() -> None:
    first, second = frame_at(0.0), frame_at(1.0)
    result = sample_native_points(
        point_at(first, 1, 1, 0.8)[None, :],
        [first, second],
        [2.0, 2.0],
        SHAPE,
        lambda z: (np.full(SHAPE, 20 + z), False),
    )

    assert result.status == ("valid",)
    assert result.selected_z.tolist() == [1]
    assert result.signed_distance_mm.tolist() == pytest.approx([-0.2])
    assert result.signal.tolist() == [21.0]


@pytest.mark.parametrize(
    ("frames", "thicknesses"),
    [
        ([frame_at(0.0)], []),
        ([PlaneFrame(np.zeros(3), np.zeros((3, 2)), (1.0, 1.0))], [1.0]),
        ([frame_at(0.0)], [float("nan")]),
        ([frame_at(0.0)], [0.0]),
        ([frame_at(0.0)], [None]),
    ],
)
def test_incomplete_or_invalid_geometry_is_named_without_reading(
    frames: list[PlaneFrame], thicknesses: list[float | None]
) -> None:
    calls: list[int] = []
    result = sample_native_points(
        np.array([[1.0, 1.0, 0.0]]),
        frames,
        thicknesses,
        SHAPE,
        lambda z: (calls.append(z) or np.ones(SHAPE), False),
    )
    assert result.status == ("invalid_geometry",)
    assert result.selected_z.tolist() == [-1]
    assert calls == []


def test_nonfinite_points_are_invalid_and_empty_input_does_not_read() -> None:
    calls: list[int] = []
    read = lambda z: (calls.append(z) or np.ones(SHAPE), False)
    frame = frame_at(0.0)
    invalid = sample_native_points(
        np.array([[1.0, np.nan, 0.0]]), [frame], [1.0], SHAPE, read
    )
    empty = sample_native_points(np.empty((0, 3)), [frame], [1.0], SHAPE, read)
    malformed = sample_native_points(
        np.array([[1.0, 2.0]]), [frame], [1.0], SHAPE, read
    )

    assert invalid.status == ("invalid_point",)
    assert empty.status == ()
    assert malformed.status == ("invalid_point",)
    assert calls == []


def test_ragged_point_input_is_named_invalid_without_reader_call() -> None:
    calls: list[int] = []
    result = sample_native_points(
        cast(np.ndarray, [[0.0, 1.0, 2.0], [3.0, 4.0]]),
        [frame_at(0.0)],
        [1.0],
        SHAPE,
        lambda z: (calls.append(z) or np.ones(SHAPE), False),
    )

    assert result.status == ("invalid_point",)
    assert calls == []


@pytest.mark.parametrize("error_type", [TypeError, AttributeError])
def test_projection_type_or_attribute_failure_is_named_invalid_geometry(
    monkeypatch: pytest.MonkeyPatch, error_type: type[Exception]
) -> None:
    frame = frame_at(0.0)
    calls: list[int] = []

    def broken_projection(self: PlaneFrame, points: np.ndarray) -> np.ndarray:
        raise error_type("invalid projection operation")

    monkeypatch.setattr(PlaneFrame, "to_native", broken_projection)
    result = sample_native_points(
        point_at(frame, 1, 1)[None, :],
        [frame],
        [1.0],
        SHAPE,
        lambda z: (calls.append(z) or np.ones(SHAPE), False),
    )

    assert result.status == ("invalid_geometry",)
    assert result.selected_z.tolist() == [-1]
    assert calls == []


def test_oblique_plane_uses_its_physical_normal_and_local_rc() -> None:
    angle = 0.4
    row_direction = np.array([0.0, -1.0, 0.0])
    column_direction = np.array([np.cos(angle), 0.0, np.sin(angle)])
    basis = np.column_stack((row_direction, column_direction))
    normal = np.cross(basis[:, 0], basis[:, 1])
    normal /= np.linalg.norm(normal)
    oblique = PlaneFrame(2.0 * normal, basis, (1.0, 1.0))
    point = oblique.to_patient(np.array([[1.0, 2.0]]))[0].copy() + 0.1 * normal
    calls: list[int] = []

    result = sample_native_points(
        point[None, :],
        [frame_at(0.0), oblique],
        [1.0, 1.0],
        SHAPE,
        lambda z: (calls.append(z) or np.full(SHAPE, z + 4.0), False),
    )

    assert result.status == ("valid",)
    assert result.selected_z.tolist() == [1]
    assert result.native_rc.tolist() == [[1, 2]]
    assert result.signed_distance_mm.tolist() == pytest.approx([0.1])
    assert calls == [1]


def test_unavailable_margin_and_nonfinite_pixels_remain_unknown() -> None:
    frame = frame_at(0.0)
    points = np.stack(
        (
            point_at(frame, 1, 0),
            point_at(frame, 1, 1),
            point_at(frame, 1, 2),
        )
    )
    raw = np.ones(SHAPE, dtype=np.float32)
    raw[1, 1] = np.nan
    unavailable = np.zeros(SHAPE, dtype=bool)
    unavailable[1, 0] = True

    result = sample_native_points(
        points, [frame], [1.0], SHAPE, lambda _: (raw, unavailable)
    )

    assert result.status == ("unavailable_sample", "unavailable_sample", "valid")
    assert np.isnan(result.signal[:2]).all()
    assert result.signal[2] == 1.0


def test_vectorized_projection_reads_only_groups_with_in_image_points(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = frame_at(0.0)
    points = np.stack(
        (
            point_at(frame, 1, 1),
            point_at(frame, SHAPE[0] - 0.5, 1),
            point_at(frame, 1, 2),
        )
    )
    original = PlaneFrame.to_native
    projected_groups: list[int] = []

    def counted_to_native(self: PlaneFrame, values: np.ndarray) -> np.ndarray:
        projected_groups.append(len(values))
        return original(self, values)

    monkeypatch.setattr(PlaneFrame, "to_native", counted_to_native)
    read_groups: list[int] = []

    def read(z: int) -> tuple[np.ndarray, bool]:
        read_groups.append(z)
        return np.ones(SHAPE), False

    result = sample_native_points(points, [frame], [1.0], SHAPE, read)

    assert result.status == ("valid", "outside_image", "valid")
    assert projected_groups == [3]
    assert read_groups == [0]


def test_projection_and_reader_calls_scale_by_plane_not_point(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frames = [frame_at(0.0), frame_at(2.0), frame_at(4.0)]
    points = np.concatenate(
        [
            np.stack(
                [
                    point_at(frame, 1, 1, float(frame.origin_lps[2]) + 0.1)
                    for _ in range(1000)
                ]
            )
            for frame in frames
        ],
        axis=0,
    )
    original = PlaneFrame.to_native
    projected_groups: list[int] = []

    def counted_to_native(self: PlaneFrame, values: np.ndarray) -> np.ndarray:
        projected_groups.append(len(values))
        return original(self, values)

    monkeypatch.setattr(PlaneFrame, "to_native", counted_to_native)
    read_groups: list[int] = []

    def read(z: int) -> tuple[np.ndarray, bool]:
        read_groups.append(z)
        return np.full(SHAPE, z + 1, dtype=np.uint8), False

    result = sample_native_points(points, frames, [1.0] * 3, SHAPE, read)

    assert result.status == ("valid",) * len(points)
    assert projected_groups == [1000, 1000, 1000]
    assert read_groups == [0, 1, 2]


def test_source_plane_and_unavailable_mask_failures_have_distinct_statuses() -> None:
    frame = frame_at(0.0)
    point = point_at(frame, 1, 1)[None, :]
    malformed_plane_shape = sample_native_points(
        point, [frame], [1.0], SHAPE, lambda _: (np.ones((2, 2)), False)
    )
    malformed_plane_dtype = sample_native_points(
        point, [frame], [1.0], SHAPE, lambda _: (np.full(SHAPE, "light"), False)
    )
    malformed_mask_shape = sample_native_points(
        point, [frame], [1.0], SHAPE, lambda _: (np.ones(SHAPE), np.zeros((2, 2), bool))
    )
    malformed_mask_dtype = sample_native_points(
        point,
        [frame],
        [1.0],
        SHAPE,
        lambda _: (np.ones(SHAPE), np.zeros(SHAPE, np.uint8)),
    )

    def unreadable(_: int) -> tuple[np.ndarray, bool]:
        raise OSError("source plane read failed")

    callback_failure = sample_native_points(point, [frame], [1.0], SHAPE, unreadable)
    actually_unavailable = sample_native_points(
        point, [frame], [1.0], SHAPE, lambda _: (np.ones(SHAPE), True)
    )

    assert malformed_plane_shape.status == ("invalid_source_plane",)
    assert malformed_plane_dtype.status == ("invalid_source_plane",)
    assert malformed_mask_shape.status == ("invalid_unavailable_mask",)
    assert malformed_mask_dtype.status == ("invalid_unavailable_mask",)
    assert callback_failure.status == ("source_plane_unreadable",)
    assert actually_unavailable.status == ("unavailable_sample",)
    assert np.isnan(malformed_plane_shape.signal[0])
    assert np.isnan(callback_failure.signal[0])


def test_source_shape_round_trip_reads_the_addressed_source_pixel() -> None:
    source_shape = (3, 5)
    frame = frame_at(0.0)
    source_pixel = np.array([[2.0, 4.0]])
    point = frame.to_patient(source_pixel)
    raw = np.zeros(source_shape, dtype=np.float32)
    raw[2, 4] = 37.5

    result = sample_native_points(
        point, [frame], [1.0], source_shape, lambda _: (raw, False)
    )

    assert result.status == ("valid",)
    assert result.native_rc.tolist() == [[2, 4]]
    assert result.signal.tolist() == [37.5]


def test_reader_shape_or_plane_unavailability_does_not_become_zero() -> None:
    frame = frame_at(0.0)
    point = point_at(frame, 1, 1)[None, :]
    whole_plane = sample_native_points(
        point, [frame], [1.0], SHAPE, lambda _: (np.ones(SHAPE), True)
    )
    wrong_shape = sample_native_points(
        point, [frame], [1.0], SHAPE, lambda _: (np.ones((2, 2)), False)
    )

    assert whole_plane.status == ("unavailable_sample",)
    assert wrong_shape.status == ("invalid_source_plane",)
    assert np.isnan(whole_plane.signal[0])
    assert np.isnan(wrong_shape.signal[0])
