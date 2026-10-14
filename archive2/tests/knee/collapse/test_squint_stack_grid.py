"""The stack's grid guard (knee.collapse.squint_stack.read_squint_stack), both signs: a series is
one grid only when every slice's tile count, tile size in native pixels and half-open bounds are
the first slice's, because the record keeps ONE bounds grid and ONE tile shape for every slice. A
slice whose spacing changes the tile size while keeping the tile count (the case the 2026-10-13
verifier reproduced: 0.5 mm against 0.45 mm under a 2 mm tile) is named `geometry_unreadable`
with the slice and the difference, never stacked; one that changes the tile count is named with
the grids; a spacing change that keeps the tile size is one grid, each slice's centres from its
own frame. The three words of `_grid_mismatch` are pinned directly, because the third (bounds
that differ at one tile count and one tile size) cannot arise from a stackable volume, whose
slices share one pixel shape, and is kept as the belt beside the braces."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from knee.collapse.physical import PlaneFrame, Squint, physical_squint
from knee.collapse.squint_stack import (
    SquintStack,
    _grid_mismatch,
    read_squint_stack,
    tile_centres_lps,
)
from knee.study.series import Series, SeriesGeometry
from knee.study.tables import SeriesRow

#: A coronal-like header: the row direction is the scanner's +x, the column direction its -z,
#: so the slice normal is +y and the stack steps along it.
ORIENTATION = np.array([1.0, 0.0, 0.0, 0.0, 0.0, -1.0])
NORMAL = np.array([0.0, 1.0, 0.0])
ORIGIN = np.array([10.0, 20.0, 30.0])
SPACING = (0.5, 0.5)
STEP_MM = 2.0
SLICES, ROWS, COLUMNS = 3, 8, 8
#: Two millimetres is four pixels at half a millimetre: a 2 x 2 grid of 4 x 4 px tiles.
TILE_MM = 2.0
TILE_PX = 4


def _geometry(spacing: np.ndarray) -> SeriesGeometry:
    positions = np.array([ORIGIN + z * STEP_MM * NORMAL for z in range(SLICES)])
    return SeriesGeometry(
        normal=NORMAL.copy(),
        orientation=np.tile(ORIENTATION, (SLICES, 1)),
        position=positions,
        spacing=np.asarray(spacing, dtype=np.float64),
        along_normal=positions @ NORMAL,
        orientation_spread=0.0,
        origin_spread_mm=0.0,
    )


def _spacing(**per_slice: tuple[float, float]) -> np.ndarray:
    """Half a millimetre on every slice, except the slices named `z<index>=(row, column)`."""
    spacing = np.tile(np.asarray(SPACING), (SLICES, 1))
    for name, value in per_slice.items():
        spacing[int(name[1:])] = value
    return spacing


def _volume() -> np.ndarray:
    rows, columns = np.indices((ROWS, COLUMNS))
    return np.stack(
        [
            (100 + 7 * rows + 3 * columns + 50 * z).astype(np.uint16)
            for z in range(SLICES)
        ]
    )


def _series(spacing: np.ndarray) -> Series:
    return Series(
        row=SeriesRow(
            study_uid="study-grid",
            series_uid="series-grid",
            fluid_sensitive="0",
            fat_suppression="0",
            anatomical_plane="Coronal",
        ),
        directory=Path("/nonexistent/the-funnel/squint-grid"),
        slices=(),
        stack=("stackable",),
        volume=_volume(),
        geometry=_geometry(spacing),
    )


def _assert_absent(stack: SquintStack, code: str) -> None:
    assert stack.code == code
    assert stack.tile_shape_rc == (0, 0)
    assert stack.median.shape == (0, 0, 0)
    assert stack.centres_lps.shape == (0, 0, 0, 3)
    assert stack.bounds_rc.shape == (0, 0, 4)


# --- negative: a grid that is not the first slice's is named, never stacked --------------------


def test_a_spacing_that_keeps_the_tile_count_but_changes_the_tile_size_is_named_and_never_stacked() -> (
    None
):
    # MUST NOT: stack a slice whose tiles are 5 px under the first slice's 4 px bounds. At
    # 0.45 mm a 2 mm tile is 5 px and an 8 px plane is still 2 x 2 tiles, so the tile COUNT is
    # the first slice's while every bound differs: the case a shape-only guard let through.
    volume = _volume()
    own = physical_squint(volume[2], (0.45, 0.45), TILE_MM)
    first = physical_squint(volume[0], SPACING, TILE_MM)
    assert own.bounds_rc.shape == first.bounds_rc.shape == (2, 2, 4)
    assert own.tile_shape_rc == (5, 5) and first.tile_shape_rc == (TILE_PX, TILE_PX)
    assert tuple(own.bounds_rc[0, 0]) == (0, 5, 0, 5)
    stack = read_squint_stack(_series(_spacing(z2=(0.45, 0.45))), TILE_MM)
    _assert_absent(stack, "geometry_unreadable")
    assert "slice 2" in stack.why
    assert "5 x 5 px" in stack.why and "4 x 4 px" in stack.why
    assert "tile count (2, 2) does not" in stack.why


def test_a_spacing_that_changes_the_tile_count_is_named_with_both_grids() -> None:
    # MUST NOT: stack two grids as one. At 1 mm a 2 mm tile is 2 px and the plane is 4 x 4 tiles.
    stack = read_squint_stack(_series(_spacing(z1=(1.0, 1.0))), TILE_MM)
    _assert_absent(stack, "geometry_unreadable")
    assert "slice 1" in stack.why
    assert "tile grid (4, 4) is not the first slice's (2, 2)" in stack.why


def test_the_three_mismatches_are_told_apart_in_words_and_one_grid_is_none() -> None:
    # The words themselves, directly: the tile count, the tile size, then the bounds; and None
    # for a grid that is the first slice's in all three. The bounds case is built by hand: a
    # stackable volume cannot make it, since its slices share one pixel shape.
    first = physical_squint(_volume()[0], SPACING, TILE_MM)
    same = physical_squint(_volume()[1], SPACING, TILE_MM)
    assert _grid_mismatch(1, same, first.bounds_rc, first.tile_shape_rc) is None
    counted = physical_squint(_volume()[1], (1.0, 1.0), TILE_MM)
    words = _grid_mismatch(1, counted, first.bounds_rc, first.tile_shape_rc)
    assert words is not None and words.startswith("slice 1: its tile grid (4, 4)")
    sized = physical_squint(_volume()[1], (0.45, 0.45), TILE_MM)
    words = _grid_mismatch(2, sized, first.bounds_rc, first.tile_shape_rc)
    assert words is not None and words.startswith("slice 2: its tiles are 5 x 5 px")
    moved = np.array(first.bounds_rc)
    moved[0, 0] = (0, 4, 0, 3)
    shifted = Squint(
        first.median,
        first.minimum,
        first.maximum,
        first.coverage,
        moved,
        first.tile_shape_rc,
    )
    words = _grid_mismatch(2, shifted, first.bounds_rc, first.tile_shape_rc)
    assert words is not None
    assert words.startswith("slice 2: its tile bounds are not the first slice's")


# --- positive: one grid, each slice's centres from its own frame -----------------------------


def test_a_spacing_change_that_keeps_the_tile_size_is_one_grid_with_each_slices_own_frame() -> (
    None
):
    # At 0.51 mm a 2 mm tile is still 4 px (ceil(2 / 0.51) = 4), so the grid is the first
    # slice's; the stack is present and that slice's centres come from its own frame, so they
    # are not the first slice's offset by the step.
    spacing = _spacing(z2=(0.51, 0.51))
    stack = read_squint_stack(_series(spacing), TILE_MM)
    assert stack.code == "present"
    assert stack.tile_shape_rc == (TILE_PX, TILE_PX)
    assert stack.median.shape == (SLICES, 2, 2)
    for z in range(SLICES):
        own = physical_squint(_volume()[z], tuple(spacing[z]), TILE_MM)
        np.testing.assert_array_equal(own.bounds_rc, stack.bounds_rc)
        assert stack.median[z].tobytes() == own.median.tobytes()
        frame = PlaneFrame.from_dicom(
            ORIGIN + z * STEP_MM * NORMAL, ORIENTATION, tuple(spacing[z])
        )
        np.testing.assert_array_equal(
            stack.centres_lps[z], tile_centres_lps(frame, stack.bounds_rc)
        )
    wide = PlaneFrame.from_dicom(
        ORIGIN + 2 * STEP_MM * NORMAL, ORIENTATION, (0.51, 0.51)
    )
    np.testing.assert_allclose(
        stack.centres_lps[2, 0, 0],
        ORIGIN + 2 * STEP_MM * NORMAL + wide.basis_lps @ np.array([1.5, 1.5]),
        atol=1e-12,
    )
    assert not np.allclose(
        stack.centres_lps[2, 0, 0] - 2 * STEP_MM * NORMAL, stack.centres_lps[0, 0, 0]
    )
