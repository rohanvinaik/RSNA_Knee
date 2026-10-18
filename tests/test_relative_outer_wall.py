"""Direct behavior pins for the anatomy-agnostic outer-wall reading."""

from typing import cast

import numpy as np
import pytest

from knee.objects.assignments import relative_outer_wall


def scene(values: list[float]) -> tuple[np.ndarray, ...]:
    plane = np.asarray([values], dtype=np.float64)
    body = np.zeros(plane.shape, dtype=bool)
    body[0, 1:3] = True
    white = body.copy()
    available = np.ones(plane.shape, dtype=bool)
    outward = np.asarray([[0.0, 1.0, 1.0, 1.5, 2.0, 2.5, 3.0]], dtype=np.float64)
    return plane, body, white, available, outward


def test_relative_outer_wall_accepts_contiguous_darker_minimum() -> None:
    plane, body, white, available, outward = scene([30, 10, 12, 5, 5, 8, 9])

    result = relative_outer_wall(plane, body, white, available, outward, section_axis=0)

    assert result["status"].tolist() == [1]
    assert result["row_minimum"].tolist() == [5.0]
    assert result["adjacent_median"].tolist() == [11.0]
    assert result["body_outer_edge_mm"].tolist() == [1.0]
    assert result["tied_runs"].tolist() == [1]
    assert np.flatnonzero(result["strip"][0]).tolist() == [3, 4, 5, 6]
    assert np.flatnonzero(result["minimum_band"][0]).tolist() == [3, 4]
    assert np.flatnonzero(result["lining_edge"][0]).tolist() == [1, 2]
    assert result["section_axis"].item() == 0


def test_relative_outer_wall_refuses_separated_tied_minima() -> None:
    plane, body, white, available, outward = scene([30, 10, 12, 5, 7, 5, 9])

    result = relative_outer_wall(plane, body, white, available, outward, section_axis=0)

    assert result["status"].tolist() == [2]
    assert result["tied_runs"].tolist() == [2]
    assert result["row_minimum"].tolist() == [5.0]
    assert not result["minimum_band"].any()
    assert not result["lining_edge"].any()


def test_relative_outer_wall_names_nondarker_minimum() -> None:
    plane, body, white, available, outward = scene([30, 10, 12, 12, 13, 14, 15])

    result = relative_outer_wall(plane, body, white, available, outward, section_axis=0)

    assert result["status"].tolist() == [3]
    assert result["row_minimum"].tolist() == [12.0]
    assert result["adjacent_median"].tolist() == [11.0]
    assert not result["minimum_band"].any()


def test_relative_outer_wall_marks_empty_sections_missing() -> None:
    plane, body, white, available, outward = scene([30, 10, 12, 5, 5, 8, 9])
    body[:] = False

    result = relative_outer_wall(plane, body, white, available, outward, section_axis=0)

    assert result["status"].tolist() == [0]
    assert np.isnan(result["body_outer_edge_mm"][0])
    assert np.isnan(result["row_minimum"][0])
    assert not result["strip"].any()


def test_relative_outer_wall_excludes_nonfinite_signal_and_position() -> None:
    plane, body, white, available, outward = scene([30, 10, np.nan, 5, 5, 8, 9])
    outward[0, 5] = np.nan

    result = relative_outer_wall(plane, body, white, available, outward, section_axis=0)

    assert result["status"].tolist() == [1]
    assert result["adjacent_median"].tolist() == [10.0]
    assert np.flatnonzero(result["strip"][0]).tolist() == [3, 4, 6]
    assert np.flatnonzero(result["minimum_band"][0]).tolist() == [3, 4]


def test_relative_outer_wall_excluded_body_pixels_cannot_move_valid_edge() -> None:
    plane, body, white, available, outward = scene([30, 10, 12, 5, 5, 8, 9])
    white[0, 4] = True
    available[0, 5:7] = False
    baseline = relative_outer_wall(
        plane, body, white, available, outward, section_axis=0
    )

    body[0, 4:7] = True
    white[0, 4] = True
    available[0, 4] = True
    plane[0, 4] = np.nan
    outward[0, 4] = 40.0
    white[0, 5] = True
    available[0, 5] = False
    plane[0, 5] = 1000.0
    outward[0, 5] = 50.0
    white[0, 6] = False
    available[0, 6] = True
    plane[0, 6] = 2000.0
    outward[0, 6] = 60.0

    changed_excluded_values = plane.copy()
    changed_excluded_values[0, 4:7] = [np.inf, -2000.0, -3000.0]
    changed_excluded_positions = outward.copy()
    changed_excluded_positions[0, 4:7] = [400.0, 500.0, 600.0]
    first = relative_outer_wall(plane, body, white, available, outward, section_axis=0)
    second = relative_outer_wall(
        changed_excluded_values,
        body,
        white,
        available,
        changed_excluded_positions,
        section_axis=0,
    )

    assert baseline["body_outer_edge_mm"].tolist() == [1.0]
    assert first["body_outer_edge_mm"].tolist() == [1.0]
    assert second["body_outer_edge_mm"].tolist() == [1.0]
    for key in (
        "strip",
        "minimum_band",
        "lining_edge",
        "status",
        "row_minimum",
        "adjacent_median",
    ):
        np.testing.assert_array_equal(first[key], baseline[key])
        np.testing.assert_array_equal(second[key], baseline[key])


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"plane": np.zeros((2, 2, 2))}, "two-dimensional"),
        ({"body": np.zeros((2, 3), dtype=bool)}, "same shape"),
        ({"white": np.zeros((2, 3), dtype=bool)}, "same shape"),
        ({"available": np.zeros((2, 3), dtype=bool)}, "same shape"),
        ({"outward_mm": np.zeros((2, 3))}, "same shape"),
    ],
)
def test_relative_outer_wall_rejects_malformed_shapes(
    changes: dict[str, np.ndarray], message: str
) -> None:
    plane = np.ones((1, 3), dtype=np.float64)
    body = np.ones((1, 3), dtype=bool)
    white = body.copy()
    available = body.copy()
    outward = np.zeros((1, 3), dtype=np.float64)
    inputs = {
        "plane": plane,
        "body": body,
        "white": white,
        "available": available,
        "outward_mm": outward,
    }
    inputs.update(changes)

    with pytest.raises(ValueError, match=message):
        relative_outer_wall(
            inputs["plane"],
            inputs["body"],
            inputs["white"],
            inputs["available"],
            inputs["outward_mm"],
            section_axis=0,
        )


@pytest.mark.parametrize("mask_name", ["body", "white", "available"])
@pytest.mark.parametrize("mask_value", [np.nan, 1])
def test_relative_outer_wall_rejects_nonboolean_masks(
    mask_name: str, mask_value: float
) -> None:
    plane, body, white, available, outward = scene([30, 10, 12, 5, 5, 8, 9])
    inputs = {
        "body": body,
        "white": white,
        "available": available,
    }
    mask = inputs[mask_name].astype(np.float64)
    mask[0, 0] = mask_value
    inputs[mask_name] = mask

    with pytest.raises(ValueError, match="boolean masks"):
        relative_outer_wall(
            plane,
            inputs["body"],
            inputs["white"],
            inputs["available"],
            outward,
            section_axis=0,
        )


@pytest.mark.parametrize("axis", [-1, 2, True, 0.5, None])
def test_relative_outer_wall_rejects_invalid_section_axis(axis: object) -> None:
    plane, body, white, available, outward = scene([30, 10, 12, 5, 5, 8, 9])

    with pytest.raises(ValueError, match="section_axis"):
        # Intentional malformed boundary value exercises runtime validation.
        relative_outer_wall(
            plane,
            body,
            white,
            available,
            outward,
            section_axis=cast(int, axis),
        )


@pytest.mark.parametrize(
    ("width", "error"),
    [
        (-0.1, ValueError),
        (np.inf, ValueError),
        (np.nan, ValueError),
        (True, TypeError),
        ([1.0], TypeError),
        (1j, TypeError),
        ("1.0", TypeError),
    ],
)
def test_relative_outer_wall_rejects_invalid_width(
    width: object, error: type[Exception]
) -> None:
    plane, body, white, available, outward = scene([30, 10, 12, 5, 5, 8, 9])

    with pytest.raises(error, match="width_mm"):
        relative_outer_wall(
            plane,
            body,
            white,
            available,
            outward,
            section_axis=0,
            # Intentional malformed boundary value exercises runtime validation.
            width_mm=cast(float, width),
        )


def test_relative_outer_wall_axis_and_reflection_preserve_native_masks() -> None:
    plane, body, white, available, outward = scene([30, 10, 12, 5, 5, 8, 9])
    baseline = relative_outer_wall(
        plane, body, white, available, outward, section_axis=0
    )

    transposed = relative_outer_wall(
        plane.T, body.T, white.T, available.T, outward.T, section_axis=1
    )
    reflected = relative_outer_wall(
        plane[:, ::-1],
        body[:, ::-1],
        white[:, ::-1],
        available[:, ::-1],
        outward[:, ::-1],
        section_axis=0,
    )

    for key in ("strip", "minimum_band", "lining_edge"):
        np.testing.assert_array_equal(transposed[key], baseline[key].T)
        np.testing.assert_array_equal(reflected[key], baseline[key][:, ::-1])
    for key in (
        "body_outer_edge_mm",
        "row_minimum",
        "adjacent_median",
        "status",
        "tied_runs",
    ):
        np.testing.assert_array_equal(transposed[key], baseline[key])
        np.testing.assert_array_equal(reflected[key], baseline[key])


def test_relative_outer_wall_zero_width_is_a_location_boundary() -> None:
    plane, body, white, available, outward = scene([30, 10, 12, 5, 5, 8, 9])

    result = relative_outer_wall(
        plane, body, white, available, outward, section_axis=0, width_mm=0.0
    )

    assert result["status"].tolist() == [0]
    assert not result["strip"].any()
