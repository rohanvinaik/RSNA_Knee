"""Intent and property tests for deterministic candidate interiors."""

from typing import Any

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from knee.collapse.interiors import read_interiors


def _read(plane: np.ndarray, **overrides):
    arguments: dict[str, Any] = {
        "spacing_rc": (1.0, 1.0),
        "split": 0.0,
        "prominence_mm": 2.0,
        "offsets_mm": np.linspace(-5.0, 5.0, 21),
        "backend": "reference",
    }
    arguments.update(overrides)
    return read_interiors(plane, **arguments)


def _two_rectangles_with_dark_slit() -> np.ndarray:
    plane = np.zeros((24, 30), dtype=np.float64)
    plane[3:21, 2:13] = 8.0
    plane[3:21, 15:28] = 8.0
    return plane


def test_two_solid_regions_separated_by_dark_slit_propose_two_interiors() -> None:
    reading = _read(_two_rectangles_with_dark_slit())

    assert reading.code == "measured"
    labels = reading.labels
    assert labels.dtype == np.int32
    assert set(np.unique(labels)) == {0, 1, 2}
    assert np.all(labels[reading.dark] == 0)
    assert np.all(labels[~reading.available] == 0)
    assert np.all(labels[3:21, 2:13] > 0)
    assert np.all(labels[3:21, 15:28] > 0)
    assert labels[10, 8] != labels[10, 20]
    assert np.all(labels[:, 13:15] == 0)


def test_returned_arrays_are_read_only() -> None:
    reading = _read(_two_rectangles_with_dark_slit())

    arrays = (
        reading.dark,
        reading.available,
        reading.distance_mm,
        reading.markers,
        reading.labels,
        reading.edge_points_rc,
        reading.edge_normals_rc,
        reading.edge_regions,
        reading.edge_kinds,
        reading.band_low_mm,
        reading.band_high_mm,
        reading.trace_points_rc,
        reading.trace_codes,
    )
    assert all(not array.flags.writeable for array in arrays)
    assert reading.profiles is not None
    assert not reading.profiles.samples.flags.writeable
    assert not reading.profiles.valid.flags.writeable


def test_source_plane_is_preserved() -> None:
    plane = _two_rectangles_with_dark_slit()
    plane[0, 0] = np.nan
    original = plane.copy()

    _read(plane)

    np.testing.assert_array_equal(plane, original)


def test_dark_and_unavailable_pixels_are_never_assigned_to_interiors() -> None:
    plane = _two_rectangles_with_dark_slit()
    plane[7:10, 7:10] = 0.0
    plane[9, 8] = np.nan
    reading = _read(plane)

    assert reading.code == "measured"
    assert reading.dark[8, 8]
    assert not reading.available[9, 8]
    assert np.all(reading.labels[reading.dark] == 0)
    assert np.all(reading.labels[~reading.available] == 0)


def test_unavailable_split_is_not_treated_as_negative_evidence() -> None:
    plane = np.array([[1.0, 2.0, np.nan], [3.0, 4.0, 5.0]])
    reading = _read(plane, split=float("nan"))

    assert reading.code == "split_unavailable"
    np.testing.assert_array_equal(reading.available, np.isfinite(plane))
    assert np.all(reading.labels == 0)


def test_empty_nonfinite_and_all_dark_planes_have_distinct_codes() -> None:
    empty = _read(np.empty((0, 5), dtype=np.float64))
    nonfinite = _read(np.full((4, 5), np.nan))
    dark = _read(np.zeros((4, 5), dtype=np.float64))

    assert empty.code == "empty_plane"
    assert nonfinite.code == "no_finite_support"
    assert dark.code == "no_interior_seeds"
    assert empty.labels.size == 0
    assert np.all(nonfinite.labels == 0)
    assert np.all(dark.labels == 0)


@pytest.mark.parametrize(
    ("spacing", "prominence", "offsets", "split"),
    [
        ((0.0, 1.0), 2.0, np.array([-1.0, 0.0, 1.0]), 0.0),
        ((1.0, float("inf")), 2.0, np.array([-1.0, 0.0, 1.0]), 0.0),
        ((1.0,), 2.0, np.array([-1.0, 0.0, 1.0]), 0.0),
        ((1.0, 1.0), 0.0, np.array([-1.0, 0.0, 1.0]), 0.0),
        ((1.0, 1.0), float("nan"), np.array([-1.0, 0.0, 1.0]), 0.0),
        ((1.0, 1.0), float("inf"), np.array([-1.0, 0.0, 1.0]), 0.0),
        ((1.0, 1.0), 2.0, np.array([-1.0, 1.0]), 0.0),
        ((1.0, 1.0), 2.0, np.array([-1.0, 0.0, 0.0, 1.0]), 0.0),
        ((1.0, 1.0), 2.0, np.array([0.0, -1.0, 1.0]), 0.0),
        ((1.0, 1.0), 2.0, np.array([-1.0, np.nan, 1.0]), 0.0),
        ((1.0, 1.0), 2.0, np.empty((0,), dtype=np.float64), 0.0),
        ((1.0, 1.0), 2.0, np.array([-1.0, 0.0, 1.0]), float("inf")),
    ],
)
def test_invalid_spacing_scale_offsets_or_split_are_rejected(
    spacing, prominence, offsets, split
) -> None:
    with pytest.raises(ValueError):
        _read(
            np.ones((5, 5), dtype=np.float64),
            spacing_rc=spacing,
            prominence_mm=prominence,
            offsets_mm=offsets,
            split=split,
        )


def test_frame_clipped_interior_is_retained_and_trace_is_named() -> None:
    plane = np.zeros((20, 24), dtype=np.float64)
    plane[0:15, 5:19] = 8.0
    reading = _read(plane)

    assert reading.code == "measured"
    assert np.any(reading.labels > 0)
    frame = reading.edge_kinds == 4
    assert np.any(frame)
    assert np.all(reading.trace_codes[frame] == 5)


def test_missing_acquisition_edge_is_distinct_and_profile_abstains() -> None:
    plane = _two_rectangles_with_dark_slit()
    plane[3:21, 13] = np.nan
    reading = _read(plane)

    assert reading.code == "measured"
    missing = reading.edge_kinds == 3
    assert np.any(missing)
    assert np.all(reading.trace_codes[missing] == 4)


def test_seedless_small_component_remains_unclaimed() -> None:
    plane = np.zeros((15, 15), dtype=np.float64)
    plane[6:8, 6:8] = 8.0
    reading = _read(plane, prominence_mm=2.0)

    assert reading.code == "no_interior_seeds"
    assert np.all(reading.labels == 0)
    assert np.all(reading.markers == 0)


def test_bracketed_trace_lies_within_its_declared_profile_band() -> None:
    reading = _read(_two_rectangles_with_dark_slit())
    bracketed = reading.trace_codes == 1

    assert np.any(bracketed)
    assert np.all(np.isfinite(reading.band_low_mm[bracketed]))
    assert np.all(np.isfinite(reading.band_high_mm[bracketed]))
    assert np.all(reading.band_low_mm[bracketed] <= reading.band_high_mm[bracketed])
    assert np.all(np.isfinite(reading.trace_points_rc[bracketed]))

    spacing = np.array([1.0, 1.0])
    delta_mm = (
        reading.trace_points_rc[bracketed] - reading.edge_points_rc[bracketed]
    ) * spacing
    signed_distance = np.einsum(
        "ij,ij->i", delta_mm, reading.edge_normals_rc[bracketed]
    )
    assert np.all(signed_distance >= reading.band_low_mm[bracketed] - 1e-12)
    assert np.all(signed_distance <= reading.band_high_mm[bracketed] + 1e-12)


@given(
    scale=st.floats(
        min_value=0.25, max_value=4.0, allow_nan=False, allow_infinity=False
    ),
    shift=st.floats(
        min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False
    ),
)
def test_positive_affine_intensity_change_preserves_topology(
    scale: float, shift: float
) -> None:
    plane = _two_rectangles_with_dark_slit()
    plane[0, 0] = np.nan
    original = _read(plane, split=0.0)

    transformed_plane = plane * scale + shift
    transformed = _read(transformed_plane, split=shift)

    assert transformed.code == original.code
    for name in (
        "dark",
        "available",
        "markers",
        "labels",
        "edge_points_rc",
        "edge_normals_rc",
        "edge_regions",
        "edge_kinds",
        "trace_codes",
    ):
        np.testing.assert_array_equal(
            getattr(transformed, name), getattr(original, name)
        )
