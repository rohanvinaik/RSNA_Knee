"""Intent tests for the squint over the stack (knee.collapse.squint_stack), both signs, written
from the contract: a tile's centre is the midpoint of the pixels it holds, placed in the scanner's
millimetres by the slice's own frame; the corner tile's centre is the slice origin (the first
pixel's centre) offset by half a tile of pixel centres along both in-plane directions; a centre
maps back to native within half a pixel; every slice is squinted and the chosen slice's medians
are byte-identical to `physical_squint` on that plane; a series without a stacked volume or a
geometry is a named absence with empty arrays of the right rank; nothing of the caller's is
written; the ledger carries the consumption then the production. The CONTRACT's proof gate."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from knee.collapse.physical import PlaneFrame, physical_squint
from knee.collapse.squint_stack import (
    STACK_CODES,
    SquintStack,
    read_squint_stack,
    tile_centres_lps,
)
from knee.study.series import Series, SeriesGeometry, read_series, selected_slice
from knee.study.tables import SeriesRow
from knee.telemetry import recording

#: A coronal-like header: the row direction (the first triplet) is the scanner's +x and the
#: column direction (the second) its -z, so the slice normal is +y and the stack steps along it.
ORIENTATION = np.array([1.0, 0.0, 0.0, 0.0, 0.0, -1.0])
NORMAL = np.array([0.0, 1.0, 0.0])
ORIGIN = np.array([10.0, 20.0, 30.0])
SPACING = (0.5, 0.5)
STEP_MM = 2.0
SLICES, ROWS, COLUMNS = 3, 8, 8
#: Two millimetres is four pixels at half a millimetre: a 2 x 2 grid of 4 x 4 px tiles.
TILE_MM = 2.0
TILE_PX = 4

#: A directory no series has: `read_series` then returns a Series with no slices, no volume and
#: no geometry, as the study stage itself returns one.
NOWHERE = Path("/nonexistent/the-funnel/squint")


def _row(uid: str = "series-squint") -> SeriesRow:
    return SeriesRow(
        study_uid="study-squint",
        series_uid=uid,
        fluid_sensitive="0",
        fat_suppression="0",
        anatomical_plane="Coronal",
    )


def _geometry(
    slices: int = SLICES,
    orientation: np.ndarray = ORIENTATION,
    spacing: np.ndarray | None = None,
) -> SeriesGeometry:
    positions = np.array([ORIGIN + z * STEP_MM * NORMAL for z in range(slices)])
    return SeriesGeometry(
        normal=NORMAL.copy(),
        orientation=np.tile(np.asarray(orientation, dtype=np.float64), (slices, 1)),
        position=positions,
        spacing=np.tile(np.asarray(SPACING, dtype=np.float64), (slices, 1))
        if spacing is None
        else np.asarray(spacing, dtype=np.float64),
        along_normal=positions @ NORMAL,
        orientation_spread=0.0,
        origin_spread_mm=0.0,
    )


def _volume() -> np.ndarray:
    rows, columns = np.indices((ROWS, COLUMNS))
    return np.stack(
        [
            (100 + 7 * rows + 3 * columns + 50 * z).astype(np.uint16)
            for z in range(SLICES)
        ]
    )


def _series(
    volume: np.ndarray | None,
    geometry: SeriesGeometry | None,
    uid: str = "series-squint",
) -> Series:
    return Series(
        row=_row(uid),
        directory=NOWHERE / uid,
        slices=(),
        stack=("stackable",),
        volume=volume,
        geometry=geometry,
    )


def _frame(z: int = 0) -> PlaneFrame:
    return PlaneFrame.from_dicom(ORIGIN + z * STEP_MM * NORMAL, ORIENTATION, SPACING)


def _half_tile_of_pixel_centres(frame: PlaneFrame) -> np.ndarray:
    """Half a tile measured between pixel centres, in mm, along the row then the column direction.

    The origin is the first pixel's CENTRE, and a tile of n pixels has its centre (n - 1) / 2
    pixels from it along each direction; the frame's basis carries the spacing.
    """
    return frame.basis_lps @ np.array([(TILE_PX - 1) / 2, (TILE_PX - 1) / 2])


# --- the measurement: positive --------------------------------------------------------------


def test_the_corner_tiles_centre_is_the_origin_offset_by_half_a_tile_along_both_directions() -> (
    None
):
    frame = _frame()
    squint = physical_squint(_volume()[0], SPACING, TILE_MM)
    assert squint.tile_shape_rc == (TILE_PX, TILE_PX)
    centres = tile_centres_lps(frame, squint.bounds_rc)
    assert centres.shape == (2, 2, 3) and centres.dtype == np.float64
    expected = ORIGIN + _half_tile_of_pixel_centres(frame)
    np.testing.assert_allclose(centres[0, 0], expected, rtol=0.0, atol=1e-12)
    # Concretely, with this header: 1.5 px x 0.5 mm along +x and along -z.
    np.testing.assert_allclose(centres[0, 0], [10.75, 20.0, 29.25], atol=1e-12)
    # The other tiles step by one whole tile along the row direction, then the column direction.
    row_step = frame.basis_lps @ np.array([TILE_PX, 0.0])
    column_step = frame.basis_lps @ np.array([0.0, TILE_PX])
    np.testing.assert_allclose(centres[1, 0], expected + row_step, atol=1e-12)
    np.testing.assert_allclose(centres[0, 1], expected + column_step, atol=1e-12)
    np.testing.assert_allclose(
        centres[1, 1], expected + row_step + column_step, atol=1e-12
    )


def test_a_centre_maps_back_to_native_within_half_a_pixel() -> None:
    frame = _frame()
    squint = physical_squint(_volume()[0], SPACING, TILE_MM)
    centres = tile_centres_lps(frame, squint.bounds_rc)
    bounds = squint.bounds_rc.reshape(-1, 4).astype(np.float64)
    midpoints = np.column_stack(
        ((bounds[:, 0] + bounds[:, 1] - 1) / 2, (bounds[:, 2] + bounds[:, 3] - 1) / 2)
    )
    back = frame.to_native(centres.reshape(-1, 3))
    assert np.all(np.abs(back - midpoints) < 0.5)
    np.testing.assert_allclose(back, midpoints, atol=1e-9)


def test_a_remainder_tile_is_centred_on_the_pixels_it_holds() -> None:
    # A 5-column plane under 4 px tiles: the second tile holds one column, so its centre is it.
    frame = _frame()
    plane = np.arange(8 * 5, dtype=np.float64).reshape(8, 5)
    squint = physical_squint(plane, SPACING, TILE_MM)
    assert tuple(squint.bounds_rc[0, 1]) == (0, 4, 4, 5)
    centres = tile_centres_lps(frame, squint.bounds_rc)
    back = frame.to_native(centres[0, 1][None, :])
    np.testing.assert_allclose(back, [[1.5, 4.0]], atol=1e-9)


# --- the measurement: negative --------------------------------------------------------------


def test_a_tile_with_no_pixels_is_nan_and_is_never_handed_to_the_frame() -> None:
    # MUST NOT: place a tile that holds nothing, or feed the frame a point it would refuse.
    bounds = np.array([[[0, 4, 0, 4], [0, 4, 4, 4]], [[4, 8, 0, 4], [4, 4, 4, 8]]])
    centres = tile_centres_lps(_frame(), bounds)
    assert np.isfinite(centres[0, 0]).all()
    assert np.isnan(centres[0, 1]).all()
    assert np.isnan(centres[1, 1]).all()
    assert np.isfinite(centres[1, 0]).all()


@pytest.mark.parametrize(
    "bad",
    [
        np.zeros((2, 4), dtype=np.int64),
        np.zeros((2, 2, 3), dtype=np.int64),
        np.zeros((2, 2, 4, 1), dtype=np.int64),
    ],
)
def test_bounds_that_are_not_a_tile_grid_are_refused_by_name(bad: np.ndarray) -> None:
    with pytest.raises(ValueError, match="invalid_bounds"):
        tile_centres_lps(_frame(), bad)


def test_the_measurement_writes_nothing_of_the_callers_and_freezes_its_own() -> None:
    squint = physical_squint(_volume()[0], SPACING, TILE_MM)
    before = squint.bounds_rc.copy()
    centres = tile_centres_lps(_frame(), squint.bounds_rc)
    np.testing.assert_array_equal(squint.bounds_rc, before)
    assert not centres.flags.writeable


# --- the orchestration: positive ------------------------------------------------------------


def test_every_slice_is_squinted_and_the_chosen_slices_medians_are_byte_identical() -> (
    None
):
    volume = _volume()
    stack = read_squint_stack(_series(volume, _geometry()), TILE_MM)
    assert isinstance(stack, SquintStack)
    assert stack.code == "present"
    assert stack.series_uid == "series-squint"
    assert stack.tile_mm == TILE_MM
    assert stack.tile_shape_rc == (TILE_PX, TILE_PX)
    assert stack.median.shape == (SLICES, 2, 2)
    assert stack.centres_lps.shape == (SLICES, 2, 2, 3)
    assert stack.bounds_rc.shape == (2, 2, 4)
    chosen = selected_slice(SLICES, None)
    assert chosen is not None
    plane = physical_squint(volume[chosen], SPACING, TILE_MM)
    assert stack.median[chosen].tobytes() == plane.median.tobytes()
    assert stack.minimum[chosen].tobytes() == plane.minimum.tobytes()
    assert stack.maximum[chosen].tobytes() == plane.maximum.tobytes()
    assert stack.coverage[chosen].tobytes() == plane.coverage.tobytes()
    np.testing.assert_array_equal(stack.bounds_rc, plane.bounds_rc)
    # Every other slice too: the stack is one squint per slice, nothing shared but the grid.
    for z in range(SLICES):
        each = physical_squint(volume[z], SPACING, TILE_MM)
        assert stack.median[z].tobytes() == each.median.tobytes()
        np.testing.assert_array_equal(each.bounds_rc, stack.bounds_rc)


def test_each_slices_centres_come_from_that_slices_own_frame() -> None:
    stack = read_squint_stack(_series(_volume(), _geometry()), TILE_MM)
    for z in range(SLICES):
        frame = _frame(z)
        np.testing.assert_array_equal(
            stack.centres_lps[z], tile_centres_lps(frame, stack.bounds_rc)
        )
        np.testing.assert_allclose(
            stack.centres_lps[z, 0, 0],
            ORIGIN + z * STEP_MM * NORMAL + _half_tile_of_pixel_centres(frame),
            atol=1e-12,
        )


def test_a_tile_with_no_finite_pixel_is_nan_in_the_maps_but_its_centre_is_still_placed() -> (
    None
):
    volume = _volume().astype(np.float64)
    volume[1, 0:4, 0:4] = np.nan
    stack = read_squint_stack(_series(volume, _geometry()), TILE_MM)
    assert stack.code == "present"
    assert np.isnan(stack.median[1, 0, 0])
    assert stack.coverage[1, 0, 0] == 0.0
    assert np.isfinite(stack.centres_lps[1, 0, 0]).all()
    assert np.isfinite(stack.median[1, 1, 1])


def test_the_ledger_carries_the_consumption_then_the_production_with_its_counts() -> (
    None
):
    with recording() as run_ledger:
        read_squint_stack(_series(_volume(), _geometry()), TILE_MM)
    events = run_ledger.events()
    assert [event.name for event in events] == [
        "study.consumed_by.squint_stack",
        "squint_stack.produced",
    ]
    assert dict(events[0].counts) == {"volume": 1, "geometry": 1}
    assert dict(events[1].counts) == {"slices": SLICES, "tiles": SLICES * 2 * 2}


# --- the orchestration: negative ------------------------------------------------------------


def _assert_absent(stack: SquintStack, code: str) -> None:
    assert stack.code == code
    assert stack.tile_shape_rc == (0, 0)
    assert stack.median.shape == (0, 0, 0)
    assert stack.minimum.shape == (0, 0, 0)
    assert stack.maximum.shape == (0, 0, 0)
    assert stack.coverage.shape == (0, 0, 0)
    assert stack.centres_lps.shape == (0, 0, 0, 3)
    assert stack.bounds_rc.shape == (0, 0, 4)
    assert stack.bounds_rc.dtype == np.int64
    assert stack.median.dtype == np.float64
    assert stack.why


def test_a_series_without_a_stacked_volume_is_the_named_absence() -> None:
    series = read_series(NOWHERE / "series-none", _row("series-none"))
    assert series.volume is None
    with recording() as run_ledger:
        stack = read_squint_stack(series, TILE_MM)
    _assert_absent(stack, "no_stacked_volume")
    assert stack.series_uid == "series-none"
    assert stack.tile_mm == TILE_MM
    events = run_ledger.events()
    assert dict(events[0].counts) == {"volume": 0, "geometry": 0}
    assert dict(events[1].counts) == {"slices": 0, "tiles": 0}


def test_a_series_without_a_geometry_is_geometry_unreadable() -> None:
    _assert_absent(
        read_squint_stack(_series(_volume(), None), TILE_MM), "geometry_unreadable"
    )


def test_a_header_that_does_not_read_as_a_plane_frame_is_geometry_unreadable() -> None:
    # Parallel direction cosines: the frame refuses it by name, and the stack names that.
    stack = read_squint_stack(
        _series(_volume(), _geometry(orientation=np.array([1, 0, 0, 1, 0, 0]))),
        TILE_MM,
    )
    _assert_absent(stack, "geometry_unreadable")
    assert "degenerate_orientation" in stack.why


def test_a_spacing_that_changes_the_grid_through_the_stack_is_named_and_never_stacked() -> (
    None
):
    # MUST NOT: stack two grids as one. A slice at twice the spacing makes a 1 x 1 grid.
    spacing = np.tile(np.asarray(SPACING), (SLICES, 1))
    spacing[2] = (1.0, 1.0)
    stack = read_squint_stack(_series(_volume(), _geometry(spacing=spacing)), TILE_MM)
    _assert_absent(stack, "geometry_unreadable")
    assert "slice 2" in stack.why


def test_nothing_of_the_callers_volume_is_written_and_every_array_is_frozen() -> None:
    volume = _volume()
    before = volume.copy()
    stack = read_squint_stack(_series(volume, _geometry()), TILE_MM)
    np.testing.assert_array_equal(volume, before)
    assert volume.flags.writeable
    for array in (
        stack.median,
        stack.minimum,
        stack.maximum,
        stack.coverage,
        stack.centres_lps,
        stack.bounds_rc,
    ):
        assert not array.flags.writeable


@pytest.mark.parametrize("tile", [0.0, -1.0, float("nan"), float("inf")])
def test_a_tile_bar_that_cannot_be_read_is_refused_before_anything_is_recorded(
    tile: float,
) -> None:
    with (
        recording() as run_ledger,
        pytest.raises(ValueError, match="invalid_tile_mm"),
    ):
        read_squint_stack(_series(_volume(), _geometry()), tile)
    assert run_ledger.events() == ()


def test_every_code_is_in_the_vocabulary() -> None:
    present = read_squint_stack(_series(_volume(), _geometry()), TILE_MM)
    no_volume = read_squint_stack(_series(None, _geometry()), TILE_MM)
    no_geometry = read_squint_stack(_series(_volume(), None), TILE_MM)
    assert {present.code, no_volume.code, no_geometry.code} <= set(STACK_CODES)
    assert present.code == "present"
    assert no_volume.code != "present" and no_geometry.code != "present"
