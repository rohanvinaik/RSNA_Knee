"""Intent tests for the strip (the-funnel tasks 6.1 to 6.3), both signs, every call direct.

The CONTRACT's proof gate (`knee.objects.strip.CONTRACT`) is the first section: a 2 x 2 block of
tiles in a 4 x 4 grid gives eight boundary segments on the block's native edges with normals that
point away from it; a tile on the picture's frame has no segment on the frame side; an object
with no tile gives no point; no input is written. The second section is the orchestration over
synthetic planes whose dark lines sit where this file puts them, so every band, code, digit and
mask cell below is a number worked out by hand and not read back from the code. The third and
fourth sections are the picture's adapter and the drawer, tested end to end on a record shaped
as the writer will save it.

The plane is 64 x 64 at half a millimetre, the squint's tile is 8 mm (16 px), so the grid is 4 x 4
and the bounds are `physical_squint`'s own. Native coordinates are pixel-centre coordinates: a tile
holds the pixels r0 .. r1 - 1, its edge to the next tile lies at r1 - 0.5.
"""

from __future__ import annotations

import ast
import dataclasses
import json
import shutil
import uuid
from pathlib import Path

import numpy as np
import pytest

from knee.collapse.physical import physical_squint
from knee.lenses.places import DIGIT_VALUES, place_codes_reference
from knee.objects import strip
from knee.objects.conversation import EXCHANGE_CODES
from knee.objects.interiors import TRACE_CODES, dark_bands
from knee.objects.profiles import sample_profiles
from knee.objects.strip import STRIP_CODES, Strip, edge_points, read_strip
from knee.pictures import strip as pictures
from knee.pictures.strip import (
    STRIP_STANDINGS,
    band_centres_rc,
    strip_panel,
    strip_standing,
)
from knee.telemetry import recording
from workbench.render import strip_frames
from workbench.render._out import PROJECT, ArgumentRefusal

SIZE = 64
SPACING = (0.5, 0.5)
TILE_MM = 8.0
STRIP_MM = 6.0
SPLIT = 10.0
PROMINENCE = 3.0
MINIMUM = 8
BRIGHT, DARK = 100.0, 0.0
BRACKETED = TRACE_CODES["bracketed"]
NO_BRACKET = TRACE_CODES["no_dark_bracket"]
MISSING = TRACE_CODES["missing_profile"]
CLIPPED = TRACE_CODES["frame_clipped"]

#: The series and the chosen slice every strip here is read for, and the border it is read under
#: (`knee.objects.tile_dome.BORDER_CODES`), with the other one a series' record may hold no strip
#: of. `read_strip` is handed all three and the strip carries them as given.
SERIES = "series"
SLICE = 15
BORDER, OTHER_BORDER = "dark_on_both", "edge_of_bright_partner"
#: A tile is 16 pixels across (8 mm at half a millimetre a pixel), and a strip holds one point for
#: every native pixel along each boundary segment, so a segment of a tile is `TILE_PX` points.
TILE_PX = 16


def _bounds(plane: np.ndarray) -> np.ndarray:
    """The squint's own half-open native bounds for this plane, 4 x 4 tiles of 16 px."""
    return physical_squint(plane, SPACING, TILE_MM).bounds_rc


def _block(
    rows: tuple[int, int] = (1, 3), columns: tuple[int, int] = (1, 3)
) -> np.ndarray:
    """The label grid of one object, id 1, over a 4 x 4 grid of tiles; 0 elsewhere."""
    labels = np.zeros((4, 4), dtype=np.int32)
    labels[rows[0] : rows[1], columns[0] : columns[1]] = 1
    return labels


def _flat_plane(dtype=np.float64) -> np.ndarray:
    return np.full((SIZE, SIZE), BRIGHT, dtype=dtype)


def _expected_segments(labels: np.ndarray, bounds: np.ndarray, index: int):
    """The docstring's rule applied in plain loops, tile by tile and side by side.

    A segment is the shared edge between a tile of the object and a four-neighbour tile, inside
    the grid, that is not. One point lies at every native pixel along it, in increasing pixel
    order, in pixel-centre coordinates: on the edge's own line (half a pixel before the tile's
    first pixel or past its last) and at the pixel's own row or column along it. Its normal is
    the step from the object's tile into the neighbour's, and the tile beyond is that neighbour.
    Each item is (point, normal, tile beyond).
    """
    found = []
    tiles_down, tiles_across = labels.shape
    for i in range(tiles_down):
        for j in range(tiles_across):
            if labels[i, j] != index:
                continue
            r0, r1, c0, c1 = (int(v) for v in bounds[i, j])
            for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ni, nj = i + di, j + dj
                if not (0 <= ni < tiles_down and 0 <= nj < tiles_across):
                    continue
                if labels[ni, nj] == index:
                    continue
                if di:
                    row = r0 - 0.5 if di < 0 else r1 - 0.5
                    points = [(row, float(pixel)) for pixel in range(c0, c1)]
                else:
                    column = c0 - 0.5 if dj < 0 else c1 - 0.5
                    points = [(float(pixel), column) for pixel in range(r0, r1)]
                found.extend(
                    (point, (float(di), float(dj)), (ni, nj)) for point in points
                )
    return found


# --- edge_points: the proof gate ----------------------------------------------------------------


def test_a_two_by_two_block_gives_eight_segments_on_its_native_edges() -> None:
    plane = _flat_plane()
    bounds = _bounds(plane)
    labels = _block()
    points, normals, beyond = edge_points(labels, bounds, 1)
    # Eight segments, not sixteen: the four edges the block's tiles share with each other are
    # interior. One point lies at every native pixel along each, so `TILE_PX` of them a segment.
    assert points.shape == (8 * TILE_PX, 2) and normals.shape == points.shape
    assert beyond.shape == points.shape
    assert points.dtype == np.float64 and normals.dtype == np.float64
    assert beyond.dtype == np.int64
    # The block holds pixels 16 .. 47, so its native edges lie at 15.5 and 47.5. A segment above
    # or below a tile runs along its pixel columns, one left or right of it along its rows.
    np.testing.assert_array_equal(
        points,
        [
            *[(15.5, float(c)) for c in range(16, 32)],  # tile (1, 1) up
            *[(float(r), 15.5) for r in range(16, 32)],  # tile (1, 1) left
            *[(15.5, float(c)) for c in range(32, 48)],  # tile (1, 2) up
            *[(float(r), 47.5) for r in range(16, 32)],  # tile (1, 2) right
            *[(47.5, float(c)) for c in range(16, 32)],  # tile (2, 1) down
            *[(float(r), 15.5) for r in range(32, 48)],  # tile (2, 1) left
            *[(47.5, float(c)) for c in range(32, 48)],  # tile (2, 2) down
            *[(float(r), 47.5) for r in range(32, 48)],  # tile (2, 2) right
        ],
    )
    # The tile each cast enters is named for every point: the neighbour beyond its segment.
    np.testing.assert_array_equal(
        beyond,
        np.repeat(
            [[0, 1], [1, 0], [0, 2], [1, 3], [3, 1], [2, 0], [3, 2], [2, 3]],
            TILE_PX,
            axis=0,
        ),
    )
    for (row, column), (row_step, column_step) in zip(points, normals, strict=True):
        on_a_horizontal_edge = row in (15.5, 47.5) and 16 <= column <= 47
        on_a_vertical_edge = column in (15.5, 47.5) and 16 <= row <= 47
        assert on_a_horizontal_edge or on_a_vertical_edge
        # Away from the block: the step has a positive component along the offset from its centre.
        assert (row - 31.5) * row_step + (column - 31.5) * column_step > 0
        assert abs(row_step) + abs(column_step) == 1.0


def test_the_points_come_in_scan_order_of_the_tiles_then_up_down_left_right() -> None:
    plane = _flat_plane()
    bounds = _bounds(plane)
    points, normals, beyond = edge_points(_block((1, 2), (1, 2)), bounds, 1)
    # One tile: its four sides, in the order up, down, left, right, each side as one point for
    # every pixel along it in increasing order.
    np.testing.assert_array_equal(
        points,
        [
            *[(15.5, float(c)) for c in range(16, 32)],  # up
            *[(31.5, float(c)) for c in range(16, 32)],  # down
            *[(float(r), 15.5) for r in range(16, 32)],  # left
            *[(float(r), 31.5) for r in range(16, 32)],  # right
        ],
    )
    np.testing.assert_array_equal(
        normals, np.repeat([[-1, 0], [1, 0], [0, -1], [0, 1]], TILE_PX, axis=0)
    )
    np.testing.assert_array_equal(
        beyond, np.repeat([[0, 1], [2, 1], [1, 0], [1, 2]], TILE_PX, axis=0)
    )
    # Two tiles side by side: the left tile's sides first (scan order), then the right tile's.
    points, _, _ = edge_points(_block((1, 2), (1, 3)), bounds, 1)
    np.testing.assert_array_equal(
        points,
        [
            *[(15.5, float(c)) for c in range(16, 32)],  # tile (1, 1) up
            *[(31.5, float(c)) for c in range(16, 32)],  # tile (1, 1) down
            *[(float(r), 15.5) for r in range(16, 32)],  # tile (1, 1) left
            *[(15.5, float(c)) for c in range(32, 48)],  # tile (1, 2) up
            *[(31.5, float(c)) for c in range(32, 48)],  # tile (1, 2) down
            *[(float(r), 47.5) for r in range(16, 32)],  # tile (1, 2) right
        ],
    )


def test_a_tile_on_the_frame_has_no_segment_on_the_frame_side() -> None:
    plane = _flat_plane()
    bounds = _bounds(plane)
    corner, normals, beyond = edge_points(_block((0, 2), (0, 2)), bounds, 1)
    # The block holds the corner: its up and left sides are the picture's frame, which is no
    # segment, so only the two edges toward the rest of the grid remain, one per tile on each.
    np.testing.assert_array_equal(
        corner,
        [
            *[(float(r), 31.5) for r in range(16)],  # tile (0, 1) right
            *[(31.5, float(c)) for c in range(16)],  # tile (1, 0) down
            *[(31.5, float(c)) for c in range(16, 32)],  # tile (1, 1) down
            *[(float(r), 31.5) for r in range(16, 32)],  # tile (1, 1) right
        ],
    )
    np.testing.assert_array_equal(
        normals, np.repeat([[0, 1], [1, 0], [1, 0], [0, 1]], TILE_PX, axis=0)
    )
    np.testing.assert_array_equal(
        beyond, np.repeat([[0, 2], [2, 0], [2, 1], [1, 2]], TILE_PX, axis=0)
    )
    assert (corner >= 0).all(), "a segment was placed on the picture's frame"
    # A whole row of tiles has only its lower side: the three others are frame or interior.
    row_points, row_normals, row_beyond = edge_points(_block((0, 1), (0, 4)), bounds, 1)
    np.testing.assert_array_equal(row_points, [(15.5, float(c)) for c in range(64)])
    np.testing.assert_array_equal(row_normals, [[1, 0]] * (4 * TILE_PX))
    np.testing.assert_array_equal(
        row_beyond, np.repeat([[1, 0], [1, 1], [1, 2], [1, 3]], TILE_PX, axis=0)
    )


def test_an_object_with_no_tile_gives_no_point() -> None:
    plane = _flat_plane()
    bounds = _bounds(plane)
    points, normals, beyond = edge_points(_block(), bounds, 7)
    assert points.shape == (0, 2) and normals.shape == (0, 2) and beyond.shape == (0, 2)
    assert points.dtype == np.float64 and normals.dtype == np.float64
    assert beyond.dtype == np.int64
    # An empty grid, and an object that fills every tile (nothing beyond it, the frame is none).
    empty_points, empty_normals, empty_beyond = edge_points(
        np.zeros((4, 4), np.int32), bounds, 1
    )
    assert empty_points.shape == (0, 2) and empty_normals.shape == (0, 2)
    assert empty_beyond.shape == (0, 2)
    full_points, _, _ = edge_points(np.ones((4, 4), np.int32), bounds, 1)
    assert full_points.shape == (0, 2)
    nothing_points, _, _ = edge_points(
        np.empty((0, 0), np.int32), np.empty((0, 0, 4), np.int64), 1
    )
    assert nothing_points.shape == (0, 2)


def test_no_input_is_written_and_the_outputs_are_frozen() -> None:
    plane = _flat_plane()
    bounds = _bounds(plane).copy()
    labels = _block()
    before_labels, before_bounds = labels.copy(), bounds.copy()
    points, normals, beyond = edge_points(labels, bounds, 1)
    np.testing.assert_array_equal(labels, before_labels)
    np.testing.assert_array_equal(bounds, before_bounds)
    assert labels.flags.writeable and bounds.flags.writeable
    assert not points.flags.writeable and not normals.flags.writeable
    assert not beyond.flags.writeable
    assert not np.shares_memory(points, bounds) and not np.shares_memory(
        normals, bounds
    )
    assert not np.shares_memory(beyond, bounds)
    # Frozen inputs are read all the same.
    labels.setflags(write=False)
    bounds.setflags(write=False)
    again, _, _ = edge_points(labels, bounds, 1)
    np.testing.assert_array_equal(again, points)


def test_a_hole_in_the_object_has_its_own_segments_facing_into_the_hole() -> None:
    bounds = physical_squint(np.zeros((80, 80)), SPACING, TILE_MM).bounds_rc
    labels = np.zeros((5, 5), dtype=np.int32)
    labels[1:4, 1:4] = 1
    labels[2, 2] = 0
    points, normals, _ = edge_points(labels, bounds, 1)
    # Twelve segments on the ring's outer edge, four around the hole, `TILE_PX` points each.
    assert len(points) == 16 * TILE_PX
    hole_centre = (2 * 16 + 7.5, 2 * 16 + 7.5)
    inward = [
        (point, normal)
        for point, normal in zip(points, normals, strict=True)
        if abs(point[0] - hole_centre[0]) <= 8 and abs(point[1] - hole_centre[1]) <= 8
    ]
    assert len(inward) == 4 * TILE_PX
    for point, normal in inward:
        # From the ring's tile into the hole: toward the hole's centre.
        assert (hole_centre[0] - point[0]) * normal[0] + (
            hole_centre[1] - point[1]
        ) * normal[1] > 0


def test_a_neighbouring_object_is_a_tile_not_so_labelled() -> None:
    bounds = _bounds(_flat_plane())
    labels = np.zeros((4, 4), dtype=np.int32)
    labels[1, 1], labels[1, 2] = 1, 2
    one, one_normals, _ = edge_points(labels, bounds, 1)
    two, two_normals, _ = edge_points(labels, bounds, 2)
    # Each has four sides, the shared one among them, with opposite normals; the shared side is
    # the line at column 31.5, and `TILE_PX` points lie along it for each object.
    assert len(one) == 4 * TILE_PX and len(two) == 4 * TILE_PX
    shared_one = [n for p, n in zip(one, one_normals, strict=True) if p[1] == 31.5]
    shared_two = [n for p, n in zip(two, two_normals, strict=True) if p[1] == 31.5]
    np.testing.assert_array_equal(shared_one, [[0, 1]] * TILE_PX)
    np.testing.assert_array_equal(shared_two, [[0, -1]] * TILE_PX)


def test_ragged_last_tiles_are_placed_by_their_own_bounds() -> None:
    plane = np.zeros((37, 29))
    bounds = physical_squint(plane, SPACING, 4.0).bounds_rc
    assert bounds.shape == (5, 4, 4)
    assert tuple(bounds[-1, -1]) == (32, 37, 24, 29)
    labels = np.zeros((5, 4), dtype=np.int32)
    labels[4, 3] = 1
    points, normals, beyond = edge_points(labels, bounds, 1)
    # The last tile holds rows 32 .. 36 and columns 24 .. 28: five pixels each way, so five
    # points along each side that has a tile beyond it, and only the up and left sides have.
    np.testing.assert_array_equal(
        points,
        [
            *[(31.5, float(c)) for c in range(24, 29)],  # up
            *[(float(r), 23.5) for r in range(32, 37)],  # left
        ],
    )
    np.testing.assert_array_equal(normals, [[-1, 0]] * 5 + [[0, -1]] * 5)
    np.testing.assert_array_equal(beyond, [[3, 3]] * 5 + [[4, 2]] * 5)


def test_the_vectorised_rule_agrees_with_the_loops_on_random_grids() -> None:
    rng = np.random.default_rng(20261013)
    plane = np.zeros((83, 61))
    bounds = physical_squint(plane, SPACING, 4.0).bounds_rc
    shape = bounds.shape[:2]
    for _ in range(40):
        labels = rng.integers(0, 4, size=shape).astype(np.int32)
        for index in (1, 2, 3):
            points, normals, beyond = edge_points(labels, bounds, index)
            expected = _expected_segments(labels, bounds, index)
            assert len(points) == len(expected)
            if expected:
                np.testing.assert_array_equal(points, [p for p, _, _ in expected])
                np.testing.assert_array_equal(normals, [n for _, n, _ in expected])
                np.testing.assert_array_equal(beyond, [b for _, _, b in expected])


def test_the_tile_a_strip_names_beyond_a_profile_is_the_tile_its_point_and_normal_enter() -> (
    None
):
    # Stepping half a pixel from a point along its normal lands on a pixel of the tile beyond;
    # stepping half a pixel back lands on a pixel of the object's own tile. So the record the
    # interstice reads is checked against the geometry and not against itself.
    rng = np.random.default_rng(20261013)
    plane = np.zeros((83, 61))
    bounds = physical_squint(plane, SPACING, 4.0).bounds_rc
    labels = rng.integers(0, 4, size=bounds.shape[:2]).astype(np.int32)

    def tile_holding(row: float, column: float) -> tuple[int, int]:
        """The one tile whose half-open bounds hold this whole pixel."""
        (found,) = [
            (i, j)
            for i in range(bounds.shape[0])
            for j in range(bounds.shape[1])
            if bounds[i, j, 0] <= row < bounds[i, j, 1]
            and bounds[i, j, 2] <= column < bounds[i, j, 3]
        ]
        return found

    checked = 0
    for index in (1, 2, 3):
        points, normals, beyond = edge_points(labels, bounds, index)
        for point, normal, tile in zip(points, normals, beyond, strict=True):
            outside, inside = point + 0.5 * normal, point - 0.5 * normal
            assert tile_holding(*outside) == tuple(tile), (point, normal)
            assert labels[tuple(tile)] != index
            assert labels[tile_holding(*inside)] == index, (point, normal)
            checked += 1
    assert checked > 100


@pytest.mark.parametrize(
    "index", [0, -1, True, False, 1.0, 2.5, "1", None, np.float64(1.0), (1,)]
)
def test_an_object_index_that_is_not_a_positive_int_is_refused_by_name(index) -> None:
    bounds = _bounds(_flat_plane())
    with pytest.raises(ValueError, match="invalid_object_index"):
        edge_points(_block(), bounds, index)


def test_a_numpy_integer_index_is_an_int() -> None:
    bounds = _bounds(_flat_plane())
    points, _, _ = edge_points(_block(), bounds, np.int64(1))  # ty: ignore[invalid-argument-type]
    assert len(points) == 8 * TILE_PX


def test_shapes_that_disagree_are_refused_by_name() -> None:
    bounds = _bounds(_flat_plane())
    labels = _block()
    for bad_labels, bad_bounds in (
        (labels[None], bounds),  # a stack of grids
        (labels, bounds[..., 0]),  # bounds without their four edges
        (labels, bounds[..., :3]),  # three edges
        (labels[:3], bounds),  # another number of tile rows
        (labels[:, :3], bounds),  # another number of tile columns
        (np.empty((0, 4), np.int32), bounds),
        (None, bounds),
        (labels, None),
        (labels.astype(str), bounds),
        (labels, bounds.astype(str)),
        # The contract reads labels int32 and bounds int64. A float bound could carry a NaN
        # into a point, a bool grid is not a label map, so each is refused up front.
        (labels.astype(np.float64), bounds),
        (labels.astype(bool), bounds),
        (labels, bounds.astype(np.float64)),
    ):
        with pytest.raises(ValueError, match="strip_inputs_disagree"):
            edge_points(bad_labels, bad_bounds, 1)  # ty: ignore[invalid-argument-type]


def test_a_bound_that_is_not_a_number_never_reaches_a_point() -> None:
    plane = _flat_plane()
    nan_bounds = _bounds(plane).astype(np.float64)
    nan_bounds[1, 1, 0] = np.nan
    with recording() as run, pytest.raises(ValueError, match="strip_inputs_disagree"):
        read_strip(
            plane,
            SPACING,
            _block(),
            nan_bounds,
            1,
            STRIP_MM,
            SPLIT,
            PROMINENCE,
            MINIMUM,
            None,
            None,
            series_uid=SERIES,
            slice_index=SLICE,
            border=BORDER,
        )
    assert run.events() == ()


# --- read_strip: the orchestration over planes whose dark lines are placed by hand --------------
#
# The 2 x 2 block's eight segments, in `edge_points` order, each as `TILE_PX` casts, one for every
# native pixel along it (segment k holds casts k * TILE_PX .. (k + 1) * TILE_PX - 1):
#   0 up (15.5, 16..31)    1 left (16..31, 15.5)   2 up (15.5, 32..47)    3 right (16..31, 47.5)
#   4 down (47.5, 16..31)  5 left (32..47, 15.5)   6 down (47.5, 32..47)  7 right (32..47, 47.5)
# At half a millimetre a pixel one offset step of 0.5 mm is one pixel, so a cast's sample at
# offset o lies o / 0.5 pixels along its normal from the edge.


def _line_plane(columns: tuple[int, int], dtype=np.float64) -> np.ndarray:
    """A bright plane with one dark band over the given columns (half-open), full height."""
    plane = _flat_plane(dtype)
    plane[:, columns[0] : columns[1]] = DARK
    return plane


def test_the_casts_are_made_only_at_the_edge_points_and_there_are_points_times_offsets_samples(
    monkeypatch,
) -> None:
    plane = _line_plane((52, 54))
    bounds = _bounds(plane)
    labels = _block()
    calls = []
    real = strip.sample_profiles

    def spy(plane_, points, normals, offsets, spacing, *rest, **named):
        calls.append((points.copy(), normals.copy(), offsets.copy()))
        return real(plane_, points, normals, offsets, spacing, *rest, **named)

    monkeypatch.setattr(strip, "sample_profiles", spy)
    result = read_strip(
        plane,
        SPACING,
        labels,
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    points, normals, beyond = edge_points(labels, bounds, 1)
    # One call, at exactly the edge points and nowhere else.
    assert len(calls) == 1
    np.testing.assert_array_equal(calls[0][0], points)
    np.testing.assert_array_equal(calls[0][1], normals)
    np.testing.assert_array_equal(result.edge_points, points)
    np.testing.assert_array_equal(result.normals, normals)
    np.testing.assert_array_equal(result.beyond_tiles, beyond)
    # Points x offsets samples, and they are the sampler's own, not a second reckoning of them.
    assert result.profiles.shape == (8 * TILE_PX, 25)
    assert result.profiles.size == len(points) * result.offsets_mm.size
    again = sample_profiles(plane, points, normals, result.offsets_mm, SPACING)
    np.testing.assert_array_equal(result.profiles, again.samples)
    assert result.code == "present" and result.code in STRIP_CODES
    assert isinstance(result, Strip)
    assert result.object_index == 1 and result.strip_mm == STRIP_MM


@pytest.mark.parametrize(
    ("spacing", "strip_mm", "pitch", "count"),
    [
        ((0.5, 0.5), 6.0, 0.5, 25),
        ((0.5, 0.5), 6.2, 0.5, 25),  # the last whole pitch inside 6.2 is 6.0
        (
            (0.5, 0.5),
            0.3,
            0.5,
            1,
        ),  # a strip thinner than one pitch is the boundary alone
        ((0.5, 0.4), 6.0, 0.4, 31),  # the finer axis sets the pitch
        ((0.390625, 0.390625), 6.0, 0.390625, 31),  # 15.36 pitches: 15 a side
    ],
)
def test_the_offsets_are_symmetric_hold_zero_and_stay_inside_the_strip(
    spacing, strip_mm, pitch, count
) -> None:
    plane = _flat_plane()
    bounds = physical_squint(plane, spacing, TILE_MM).bounds_rc
    labels = np.zeros(bounds.shape[:2], dtype=np.int32)
    labels[1:3, 1:3] = 1
    result = read_strip(
        plane,
        spacing,
        labels,
        bounds,
        1,
        strip_mm,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    offsets = result.offsets_mm
    assert len(offsets) == count and offsets.dtype == np.float64
    assert 0.0 in offsets, "the boundary itself is not cast"
    np.testing.assert_array_equal(offsets, -offsets[::-1])
    assert offsets.max() <= strip_mm, "a cast reaches farther than the strip"
    if count > 1:
        np.testing.assert_allclose(np.diff(offsets), pitch, rtol=0, atol=1e-12)
    assert result.profiles.shape == (len(result.edge_points), count)
    assert result.native_digits.shape == result.profiles.shape


@pytest.mark.parametrize(
    ("columns", "normal_column", "offset"),
    [
        ((52, 54), 1.0, 2.5),  # beyond the right edge (47.5): sample at column 52.5
        ((56, 58), 1.0, 4.5),
        ((50, 52), 1.0, 1.5),
        ((8, 10), -1.0, 3.5),  # beyond the left edge (15.5): sample at column 8.5
    ],
)
def test_a_bracketed_band_lies_on_the_dark_line_and_nowhere_else(
    columns, normal_column, offset
) -> None:
    plane = _line_plane(columns)
    bounds = _bounds(plane)
    result = read_strip(
        plane,
        SPACING,
        _block(),
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    sees_the_line = result.normals[:, 1] == normal_column
    # Two segments face the line, and every one of their casts meets it.
    assert sees_the_line.sum() == 2 * TILE_PX
    assert (result.trace_codes[sees_the_line] == BRACKETED).all()
    np.testing.assert_array_equal(
        result.band_mm[sees_the_line], [[offset, offset]] * (2 * TILE_PX)
    )
    # The casts of the six other segments never meet the line: no dark run, no band, and no zero
    # in its place.
    assert (result.trace_codes[~sees_the_line] == NO_BRACKET).all()
    assert np.isnan(result.band_mm[~sees_the_line]).all()
    assert result.trace_codes.dtype == np.uint8
    assert result.band_mm.shape == (8 * TILE_PX, 2)


def test_each_axis_is_cast_in_its_own_millimetres() -> None:
    # 0.5 mm down a row, 1.0 mm along a column: a tile is 16 x 8 px, the grid 4 x 8.
    spacing = (0.5, 1.0)
    plane = _flat_plane()
    plane[:, 50] = (
        DARK  # one pixel wide: sample at column 50.0, 2.5 mm past the edge 47.5
    )
    plane[52:54, :] = DARK  # two rows: sample at row 52.5, 2.5 mm past the edge 47.5
    bounds = physical_squint(plane, spacing, TILE_MM).bounds_rc
    assert bounds.shape[:2] == (4, 8)
    labels = np.zeros((4, 8), dtype=np.int32)
    labels[1:3, 2:6] = 1
    result = read_strip(
        plane,
        spacing,
        labels,
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    # Twelve boundary segments, a point for every native pixel along each: the eight above and
    # below the block run along a tile's 8 pixel columns, the four beside it along its 16 rows.
    assert len(result.edge_points) == 8 * 8 + 4 * 16
    pitch_check = np.diff(result.offsets_mm)
    np.testing.assert_allclose(pitch_check, 0.5, rtol=0, atol=1e-12)
    down = result.normals[:, 0] == 1
    right = result.normals[:, 1] == 1
    for cast in (down, right):
        assert (result.trace_codes[cast] == BRACKETED).all()
        np.testing.assert_array_equal(result.band_mm[cast], [[2.5, 2.5]] * cast.sum())
    # Read with one spacing for both axes the column line would sit at 1.25 or 5.0 mm instead.
    rest = ~(down | right)
    assert (result.trace_codes[rest] == NO_BRACKET).all()


def test_a_cast_that_leaves_the_plane_is_frame_clipped_and_a_nan_pixel_is_not() -> None:
    plane = _flat_plane()
    bounds = _bounds(plane)
    # One tile, a strip of 10 mm (20 px): the up and left casts start 15.5 px in and reach -4.5.
    clipped = read_strip(
        plane,
        SPACING,
        _block((1, 2), (1, 2)),
        bounds,
        1,
        10.0,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    # Four segments of `TILE_PX` casts each, in the order up, down, left, right: the up and left
    # casts leave the plane, the down and right casts do not.
    np.testing.assert_array_equal(
        clipped.trace_codes,
        np.repeat([CLIPPED, NO_BRACKET, CLIPPED, NO_BRACKET], TILE_PX),
    )
    up, down, left = (slice(k * TILE_PX, (k + 1) * TILE_PX) for k in range(3))
    assert np.isnan(clipped.band_mm[up]).all() and np.isnan(clipped.band_mm[left]).all()
    # Five offsets of every up cast (8.0 .. 10.0 mm) fall at rows -0.5 .. -4.5: off the plane,
    # NaN in the profile, and silence 2 (never the middle 0) in the digits.
    assert (np.isnan(clipped.profiles[up]).sum(axis=1) == 5).all()
    assert np.isnan(clipped.profiles[up][:, -5:]).all()
    assert (clipped.native_digits[up][:, -5:] == 2).all()
    assert (clipped.native_digits[up][:, :-5] == 0).all()
    assert not np.isnan(clipped.profiles[down]).any()
    # MUST NOT: call a pixel that is not a number "off the plane". Same plane, one NaN pixel
    # that one right cast of tile (1, 2) reads, and every cast stays on the plane.
    holed = _flat_plane()
    holed[23, 50] = np.nan
    unread = read_strip(
        holed,
        SPACING,
        _block(),
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    # The cast that starts at row 23.0 on the right edge reads pixel (23, 50) twice, at 49.5 and
    # 50.5; a cast starts at a whole row, so no other cast reads a pixel of row 23.
    (missing,) = np.flatnonzero(unread.trace_codes == MISSING)
    assert tuple(unread.edge_points[missing]) == (23.0, 47.5)
    assert (unread.trace_codes[unread.trace_codes != MISSING] == NO_BRACKET).all()
    assert CLIPPED not in unread.trace_codes
    assert (
        unread.native_digits[missing][np.isnan(unread.profiles[missing])] == 2
    ).all()
    assert np.isnan(unread.profiles[missing]).sum() == 2


def test_an_object_without_a_boundary_is_no_boundary_with_empty_arrays_of_the_right_rank() -> (
    None
):
    plane = _flat_plane()
    bounds = _bounds(plane)
    for labels, index, population in (
        (_block(), 7, 0),  # an object that has no tile
        (np.ones((4, 4), dtype=np.int32), 1, SIZE * SIZE),  # one that fills every tile
    ):
        with recording() as run:
            result = read_strip(
                plane,
                SPACING,
                labels,
                bounds,
                index,
                STRIP_MM,
                SPLIT,
                PROMINENCE,
                MINIMUM,
                None,
                None,
                series_uid=SERIES,
                slice_index=SLICE,
                border=BORDER,
            )
        assert result.code == "no_boundary"
        assert result.edge_points.shape == (0, 2) and result.normals.shape == (0, 2)
        assert result.offsets_mm.shape == (25,)
        assert result.profiles.shape == (0, 25) and result.native_digits.shape == (
            0,
            25,
        )
        assert result.native_digits.dtype == np.int8
        assert result.trace_codes.shape == (0,) and result.trace_codes.dtype == np.uint8
        assert result.band_mm.shape == (0, 2) and result.exchange_codes.shape == (0,)
        assert result.strip_mask.shape == plane.shape and not result.strip_mask.any()
        # The object's own pixels are still counted: an object with no tile has none.
        assert result.population_count == population
        assert (population == 0) == np.isnan(result.low_edge)
        assert [event.name for event in run.events()][-1] == "strip.produced"
        assert dict(run.events()[-1].counts) == {"points": 0, "bracketed": 0}


@pytest.mark.parametrize("missing", ["plane", "labels", "bounds", "empty_plane"])
def test_a_plane_labels_or_bounds_that_were_not_there_is_predecessor_absent(
    missing,
) -> None:
    plane = _flat_plane()
    labels, bounds = _block(), _bounds(plane)
    handed = {"plane": plane, "labels": labels, "bounds": bounds}
    if missing == "empty_plane":
        handed["plane"] = np.empty((0, 0))
    else:
        handed[missing] = None
    with recording() as run:
        result = read_strip(
            handed["plane"],
            SPACING,
            handed["labels"],
            handed["bounds"],
            1,
            STRIP_MM,
            SPLIT,
            PROMINENCE,
            MINIMUM,
            None,
            None,
            series_uid=SERIES,
            slice_index=SLICE,
            border=BORDER,
        )
    assert result.code == "predecessor_absent"
    assert missing.split("_")[-1] in result.why
    assert result.edge_points.shape == (0, 2) and result.normals.shape == (0, 2)
    assert result.offsets_mm.shape == (0,) and result.profiles.shape == (0, 0)
    assert result.trace_codes.shape == (0,) and result.band_mm.shape == (0, 2)
    assert result.exchange_codes.shape == (0,) and result.native_digits.shape == (0, 0)
    assert result.strip_mask.shape == (0, 0)
    assert np.isnan(result.low_edge) and np.isnan(result.high_edge)
    assert result.population_count == 0
    # A consumer records only a record that was handed over, never a None or an empty one.
    names = [event.name for event in run.events()]
    assert ("tile_dome.consumed_by.strip" in names) == (missing != "labels")
    assert ("study.consumed_by.strip" in names) == (
        missing not in ("plane", "empty_plane")
    )
    assert names[-1] == "strip.produced"
    assert dict(run.events()[-1].counts) == {"points": 0, "bracketed": 0}


def test_the_ledger_records_what_was_read_then_what_was_made() -> None:
    plane = _line_plane((52, 54))
    bounds = _bounds(plane)
    with recording() as run:
        read_strip(
            plane,
            SPACING,
            _block(),
            bounds,
            1,
            STRIP_MM,
            SPLIT,
            PROMINENCE,
            MINIMUM,
            None,
            None,
            series_uid=SERIES,
            slice_index=SLICE,
            border=BORDER,
        )
    assert [(e.name, dict(e.counts)) for e in run.events()] == [
        ("tile_dome.consumed_by.strip", {"labels": 1}),
        ("study.consumed_by.strip", {"plane": 1}),
        ("strip.produced", {"points": 8 * TILE_PX, "bracketed": 2 * TILE_PX}),
    ]


@pytest.mark.parametrize(
    "bar", [0, -1.0, float("nan"), float("inf"), True, "6", None, [6.0]]
)
def test_a_bar_that_is_not_a_finite_positive_number_is_refused_before_any_event(
    bar,
) -> None:
    plane = _flat_plane()
    bounds = _bounds(plane)
    labels = _block()
    with recording() as run:
        with pytest.raises(ValueError, match="invalid_strip_mm"):
            read_strip(
                plane,
                SPACING,
                labels,
                bounds,
                1,
                bar,
                SPLIT,
                PROMINENCE,
                MINIMUM,
                None,
                None,
                series_uid=SERIES,
                slice_index=SLICE,
                border=BORDER,
            )
        with pytest.raises(ValueError, match="invalid_prominence_native_mm"):
            read_strip(
                plane,
                SPACING,
                labels,
                bounds,
                1,
                STRIP_MM,
                SPLIT,
                bar,
                MINIMUM,
                None,
                None,
                series_uid=SERIES,
                slice_index=SLICE,
                border=BORDER,
            )
    assert run.events() == ()


@pytest.mark.parametrize("bar", [-1, 1.5, True, "8", None, 8.0])
def test_a_minimum_population_that_is_not_a_non_negative_int_is_refused_before_any_event(
    bar,
) -> None:
    plane = _flat_plane()
    with (
        recording() as run,
        pytest.raises(ValueError, match="invalid_minimum_population"),
    ):
        read_strip(
            plane,
            SPACING,
            _block(),
            _bounds(plane),
            1,
            STRIP_MM,
            SPLIT,
            PROMINENCE,
            bar,
            None,
            None,
            series_uid=SERIES,
            slice_index=SLICE,
            border=BORDER,
        )
    assert run.events() == ()


def test_a_zero_minimum_population_is_a_bar_and_a_large_integer_type_is_an_int() -> (
    None
):
    plane = _flat_plane()
    bounds = _bounds(plane)
    zero = read_strip(
        plane,
        SPACING,
        _block(),
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        0,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    assert zero.code == "present" and zero.population_count == 1024
    numpy_bar = read_strip(
        plane,
        SPACING,
        _block(),
        bounds,
        np.int64(1),  # ty: ignore[invalid-argument-type]
        np.float64(STRIP_MM),
        SPLIT,
        np.float32(3.0),  # ty: ignore[invalid-argument-type]
        np.int64(8),  # ty: ignore[invalid-argument-type]
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    assert numpy_bar.code == "present" and numpy_bar.object_index == 1


def test_an_object_index_the_plane_the_spacing_and_the_grids_are_refused_before_any_event() -> (
    None
):
    plane = _flat_plane()
    bounds = _bounds(plane)
    with recording() as run:
        with pytest.raises(ValueError, match="invalid_object_index"):
            read_strip(
                plane,
                SPACING,
                _block(),
                bounds,
                0,
                STRIP_MM,
                SPLIT,
                PROMINENCE,
                MINIMUM,
                None,
                None,
                series_uid=SERIES,
                slice_index=SLICE,
                border=BORDER,
            )
        with pytest.raises(ValueError, match="strip_inputs_disagree"):
            read_strip(
                plane,
                SPACING,
                _block()[:3],
                bounds,
                1,
                STRIP_MM,
                SPLIT,
                PROMINENCE,
                MINIMUM,
                None,
                None,
                series_uid=SERIES,
                slice_index=SLICE,
                border=BORDER,
            )
        with pytest.raises(ValueError, match="invalid_spacing"):
            read_strip(
                plane,
                (0.5, 0.0),
                _block(),
                bounds,
                1,
                STRIP_MM,
                SPLIT,
                PROMINENCE,
                MINIMUM,
                None,
                None,
                series_uid=SERIES,
                slice_index=SLICE,
                border=BORDER,
            )
        with pytest.raises(ValueError, match="invalid_plane"):
            read_strip(
                plane.astype(str),
                SPACING,
                _block(),
                bounds,
                1,
                STRIP_MM,
                SPLIT,
                PROMINENCE,
                MINIMUM,
                None,
                None,
                series_uid=SERIES,
                slice_index=SLICE,
                border=BORDER,
            )
    assert run.events() == ()
    # An absent plane needs no spacing: the strip says it was not there and refuses nothing.
    absent = read_strip(
        None,  # ty: ignore[invalid-argument-type]
        (0.0, 0.0),
        _block(),
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    assert absent.code == "predecessor_absent"


def test_the_terciles_are_those_of_the_objects_own_pixels_and_nothing_outside() -> None:
    plane = np.full((SIZE, SIZE), 500.0)
    plane[16:48, 16:48] = np.arange(16, 48, dtype=np.float64)[None, :]
    bounds = _bounds(plane)
    own = plane[16:48, 16:48]
    expected_low, expected_high = (float(q) for q in np.quantile(own, (1 / 3, 2 / 3)))
    result = read_strip(
        plane,
        SPACING,
        _block(),
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    assert (result.low_edge, result.high_edge) == (expected_low, expected_high)
    assert (result.low_edge, result.high_edge) == (26.0, 37.0)
    assert result.population_count == own.size == 1024
    # MUST NOT read outside the object: ruin every pixel beyond its tiles and nothing moves.
    ruined = plane.copy()
    ruined[:16], ruined[48:], ruined[:, :16], ruined[:, 48:] = 1e6, -1e6, 7e5, -7e5
    outside = read_strip(
        ruined,
        SPACING,
        _block(),
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    assert (outside.low_edge, outside.high_edge) == (expected_low, expected_high)
    assert outside.population_count == 1024
    # And it MUST read inside: one object pixel changed moves the count when it is not a number.
    holed = plane.copy()
    holed[20, 20:30] = np.nan
    inside = read_strip(
        holed,
        SPACING,
        _block(),
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    assert inside.population_count == 1024 - 10
    # A larger object (the whole block plus one more tile column) has its own population.
    wider = read_strip(
        plane,
        SPACING,
        _block((1, 3), (1, 4)),
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    assert wider.population_count == 1536


def test_each_sample_is_placed_against_the_terciles_and_silence_is_two_never_zero() -> (
    None
):
    plane = np.full((SIZE, SIZE), 500.0)
    plane[16:48, 16:48] = np.arange(16, 48, dtype=np.float64)[None, :]
    plane[23, 56:60] = (
        np.nan
    )  # beyond the right edge: the right cast of tile (1, 2) reads it
    bounds = _bounds(plane)
    result = read_strip(
        plane,
        SPACING,
        _block(),
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    low, high = result.low_edge, result.high_edge
    samples = result.profiles
    expected = np.where(
        np.isnan(samples),
        2,
        np.where(samples < low, -1, np.where(samples > high, 1, 0)),
    )
    np.testing.assert_array_equal(result.native_digits, expected)
    assert result.native_digits.dtype == np.int8
    for digit in (-1, 0, 1, 2):
        assert (result.native_digits == digit).any(), digit
    # The two stages' own vocabularies agree on what a digit is.
    np.testing.assert_array_equal(
        result.native_digits,
        DIGIT_VALUES[place_codes_reference(samples, low, high, 1024, MINIMUM)],
    )
    # Never the middle for a sample that was not read.
    assert (result.native_digits[np.isnan(samples)] == 2).all()


def test_a_population_below_the_bar_places_nothing_and_says_so_without_losing_the_count() -> (
    None
):
    plane = _flat_plane()
    bounds = _bounds(plane)
    result = read_strip(
        plane,
        SPACING,
        _block(),
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        2000,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    assert result.population_count == 1024
    assert np.isnan(result.low_edge) and np.isnan(result.high_edge)
    assert (result.native_digits == 2).all()
    # The same strip under a bar the population meets places every sample in the middle.
    met = read_strip(
        plane,
        SPACING,
        _block(),
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        1024,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    assert (met.low_edge, met.high_edge) == (BRIGHT, BRIGHT)
    assert (met.native_digits == 0).all()


def test_the_strip_mask_is_exactly_the_pixels_the_casts_read() -> None:
    rng = np.random.default_rng(7)
    plane = rng.uniform(1.0, 200.0, size=(SIZE, SIZE))
    bounds = _bounds(plane)
    result = read_strip(
        plane,
        SPACING,
        _block(),
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    mask = result.strip_mask
    assert mask.shape == plane.shape and mask.dtype == np.bool_
    assert 0 < mask.sum() < plane.size
    assert not np.isnan(result.profiles).any()
    _assert_the_mask_is_the_read_set(plane, result, SPACING)


def test_a_split_that_is_not_a_finite_number_is_refused_before_any_event() -> None:
    # The split is the valley the bands are read under: with none there is no band to read, and
    # the stage says so by refusing (`invalid_split`) and not by naming a trace code for it.
    plane = _line_plane((52, 54))
    bounds = _bounds(plane)
    for split in (float("nan"), float("inf"), -float("inf"), None, "10", True):
        with recording() as run, pytest.raises(ValueError, match="invalid_split"):
            read_strip(
                plane,
                SPACING,
                _block(),
                bounds,
                1,
                STRIP_MM,
                split,  # ty: ignore[invalid-argument-type]
                PROMINENCE,
                MINIMUM,
                None,
                None,
                series_uid=SERIES,
                slice_index=SLICE,
                border=BORDER,
            )
        assert run.events() == (), split
    read = read_strip(
        plane,
        SPACING,
        _block(),
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    assert (read.trace_codes == BRACKETED).sum() == 2 * TILE_PX


def _assert_the_mask_is_the_read_set(
    plane: np.ndarray, result: Strip, spacing: tuple[float, float]
) -> None:
    """The mask is every pixel a sample reads and no other, checked pixel by pixel.

    MUST NOT: a pixel outside it is destroyed and not one sample moves. MUST: each pixel inside
    it is destroyed and some sample notices. Both are read through the sampler itself. A strip
    holds a cast for every native pixel along its boundary, so the second check samples again
    only the casts that start within reach of the pixel: no cast reads farther from its start
    than its farthest offset, plus one pixel for the bilinear read. That is a bound from the
    geometry and not from the footprint rule under test, and a cast beyond it cannot read the
    pixel at all, so no pixel the check would have caught is skipped.
    """
    mask = result.strip_mask
    ruined = plane.astype(np.float64)
    ruined[~mask] = np.nan
    unmoved = sample_profiles(
        ruined, result.edge_points, result.normals, result.offsets_mm, spacing
    )
    np.testing.assert_array_equal(unmoved.samples, result.profiles)
    reach = float(np.abs(result.offsets_mm).max()) / min(spacing) + 1.0
    for row, column in zip(*np.nonzero(mask), strict=True):
        near = (np.abs(result.edge_points[:, 0] - row) <= reach) & (
            np.abs(result.edge_points[:, 1] - column) <= reach
        )
        broken = plane.astype(np.float64)
        broken[row, column] = np.nan
        noticed = sample_profiles(
            broken,
            result.edge_points[near],
            result.normals[near],
            result.offsets_mm,
            spacing,
        )
        assert np.isnan(noticed.samples).any(), f"pixel ({row}, {column}) is not read"


def test_a_sample_on_a_whole_pixel_reads_that_pixel_alone() -> None:
    # A 7.5 mm tile is 15 px, and a strip holds a point at every pixel along an edge, so each
    # cast starts at a whole pixel along it: the sample there has weight 0 on the pixel beside
    # it, which the sampler does not read.
    plane = np.random.default_rng(3).uniform(1.0, 200.0, size=(60, 60))
    bounds = physical_squint(plane, SPACING, 7.5).bounds_rc
    assert tuple(bounds[1, 1]) == (15, 30, 15, 30)
    labels = np.zeros((4, 4), dtype=np.int32)
    labels[1:3, 1:3] = 1
    result = read_strip(
        plane,
        SPACING,
        labels,
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    np.testing.assert_array_equal(result.edge_points[0], [14.5, 15.0])
    _assert_the_mask_is_the_read_set(plane, result, SPACING)
    # The up casts of the block run down columns 15 .. 44, one column each, rows 2.5 .. 26.5 and
    # so pixels 2 .. 27. Above row 14, where no left or right cast crosses them, no pixel beside
    # that run of columns is read: columns 14 and 45 are untouched.
    assert result.strip_mask[2:14, 15:45].all()
    assert not result.strip_mask[2:14, 14].any()
    assert not result.strip_mask[2:14, 45].any()


def test_the_mask_and_the_clipping_follow_each_axis_spacing() -> None:
    spacing = (0.5, 1.0)
    plane = np.random.default_rng(5).uniform(1.0, 200.0, size=(SIZE, SIZE))
    bounds = physical_squint(plane, spacing, TILE_MM).bounds_rc
    labels = np.zeros(bounds.shape[:2], dtype=np.int32)
    labels[1:3, 2:6] = 1
    result = read_strip(
        plane,
        spacing,
        labels,
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    _assert_the_mask_is_the_read_set(plane, result, spacing)
    # Six millimetres is twelve rows a side but only six columns: a right cast, which starts at
    # column 47.5 on a whole row such as 31, reads columns 41.5 .. 53.5, so pixels 41 .. 54 of
    # that row. Row 31 lies between the reach of the up casts (rows 3 .. 28 of their columns)
    # and of the down casts (rows 35 .. 60), so only the right casts read it out there.
    assert result.strip_mask[31, 41:55].all()
    assert not result.strip_mask[31, 40] and not result.strip_mask[31, 55]


def test_a_cast_that_ends_on_the_last_pixel_is_on_the_plane_and_one_beyond_it_is_not() -> (
    None
):
    # Rows 1 mm apart, columns half a millimetre: a 15.5 mm strip is 15.5 rows a side, so the
    # up cast ends on row 0.0 and the down cast on row 63.0 exactly, both pixels of the plane.
    spacing = (1.0, 0.5)
    plane = _flat_plane()
    bounds = physical_squint(plane, spacing, TILE_MM).bounds_rc
    assert bounds.shape[:2] == (8, 4)
    labels = np.zeros((8, 4), dtype=np.int32)
    labels[2:6, 1:3] = 1
    on = read_strip(
        plane,
        spacing,
        labels,
        bounds,
        1,
        15.5,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    up, down = on.normals[:, 0] == -1, on.normals[:, 0] == 1
    assert up.sum() == 2 * TILE_PX and down.sum() == 2 * TILE_PX
    assert (on.trace_codes[up | down] == NO_BRACKET).all()
    assert not np.isnan(on.profiles[up | down]).any()
    # The columns, 31 pixels a side from 15.5 and 47.5, leave the plane at both ends.
    assert (on.trace_codes[~(up | down)] == CLIPPED).all()
    # A strip of 16 mm puts the last sample half a row beyond the plane at both ends.
    beyond = read_strip(
        plane,
        spacing,
        labels,
        bounds,
        1,
        16.0,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    assert (beyond.trace_codes == CLIPPED).all()
    # Only the far end of each up and down cast (offset +16 mm, row -0.5 or 63.5) is off the
    # plane; the near end (-16 mm) lands back inside at row 31.5.
    assert np.isnan(beyond.profiles[up | down][:, -1]).all()
    assert not np.isnan(beyond.profiles[up | down][:, 0]).any()


@pytest.mark.parametrize("dtype", [np.float64, np.float32, np.uint16, np.int32])
def test_the_plane_may_be_stored_in_any_numeric_type_and_reads_the_same(dtype) -> None:
    reference_plane = _line_plane((52, 54))
    bounds = _bounds(reference_plane)
    reference = read_strip(
        reference_plane,
        SPACING,
        _block(),
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    plane = _line_plane((52, 54), dtype)
    result = read_strip(
        plane,
        SPACING,
        _block(),
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    np.testing.assert_array_equal(result.profiles, reference.profiles)
    np.testing.assert_array_equal(result.trace_codes, reference.trace_codes)
    np.testing.assert_array_equal(result.band_mm, reference.band_mm)
    np.testing.assert_array_equal(result.native_digits, reference.native_digits)
    assert (result.low_edge, result.high_edge) == (
        reference.low_edge,
        reference.high_edge,
    )
    assert plane.dtype == dtype, "the plane was converted in place"


def test_every_array_is_frozen_and_no_input_is_written() -> None:
    plane = _line_plane((52, 54))
    bounds = _bounds(plane).copy()
    labels = _block()
    before = plane.copy(), bounds.copy(), labels.copy()
    result = read_strip(
        plane,
        SPACING,
        labels,
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    for field in dataclasses.fields(result):
        value = getattr(result, field.name)
        if isinstance(value, np.ndarray):
            assert not value.flags.writeable, field.name
    np.testing.assert_array_equal(plane, before[0])
    np.testing.assert_array_equal(bounds, before[1])
    np.testing.assert_array_equal(labels, before[2])
    assert plane.flags.writeable and bounds.flags.writeable and labels.flags.writeable
    for field in ("profiles", "strip_mask", "edge_points"):
        assert not np.shares_memory(getattr(result, field), plane)


def test_a_partner_handed_over_is_refused_by_name_because_its_bands_are_not_carried_yet() -> (
    None
):
    plane = _line_plane((52, 54))
    bounds = _bounds(plane)
    # The partner's bands carried to the points (task 6.2) are not built: a partner plane or a
    # partner spacing handed over is refused by name, before any event, and nothing pretends to
    # carry it.
    for partner_plane, partner_spacing in (
        (np.full((80, 80), 50.0), (0.390625, 0.390625)),
        (np.full((80, 80), 50.0), None),
        (None, (0.390625, 0.390625)),
    ):
        with (
            recording() as run,
            pytest.raises(ValueError, match="partner_exchange_not_built"),
        ):
            read_strip(
                plane,
                SPACING,
                _block(),
                bounds,
                1,
                STRIP_MM,
                SPLIT,
                PROMINENCE,
                MINIMUM,
                partner_plane,
                partner_spacing,
                series_uid=SERIES,
                slice_index=SLICE,
                border=BORDER,
            )
        assert run.events() == ()
    # No partner: the record's exchange codes are empty, and its reason says no band is carried.
    alone = read_strip(
        plane,
        SPACING,
        _block(),
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    assert alone.exchange_codes.shape == (0,) and alone.exchange_codes.dtype == np.uint8
    assert 0 not in EXCHANGE_CODES.values()
    assert "no partner band is carried" in alone.why


def test_the_strip_carries_the_series_the_slice_and_the_border_it_was_handed() -> None:
    plane = _flat_plane()
    bounds = _bounds(plane)

    def handed(plane_=plane, **changed: object) -> Strip:
        kept: dict[str, object] = {
            "series_uid": "1.2.3",
            "slice_index": 17,
            "border": OTHER_BORDER,
            **changed,
        }
        return read_strip(
            plane_,
            SPACING,
            _block(),
            bounds,
            1,
            STRIP_MM,
            SPLIT,
            PROMINENCE,
            MINIMUM,
            None,
            None,
            **kept,
        )

    # Not placeholders for a caller to stamp afterwards: the strip is made for a series, a slice
    # and a border, and carries exactly what it was handed, an absent one too.
    result = handed()
    assert (result.series_uid, result.slice_index, result.border) == (
        "1.2.3",
        17,
        OTHER_BORDER,
    )
    absent = handed(None)
    assert absent.code == "predecessor_absent"
    assert (absent.series_uid, absent.slice_index, absent.border) == (
        "1.2.3",
        17,
        OTHER_BORDER,
    )
    # What it is not handed it refuses, by name, before any event.
    for message, changed in (
        ("invalid_series_uid", {"series_uid": 5}),
        ("invalid_series_uid", {"series_uid": None}),
        ("invalid_slice_index", {"slice_index": -1}),
        ("invalid_slice_index", {"slice_index": True}),
        ("invalid_slice_index", {"slice_index": 1.5}),
        ("invalid_border", {"border": "bright"}),
        ("invalid_border", {"border": None}),
    ):
        with recording() as run, pytest.raises(ValueError, match=message):
            handed(**changed)
        assert run.events() == (), changed
    stamped = dataclasses.replace(result, object_index=2)
    assert stamped.edge_points is result.edge_points
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.object_index = 2  # ty: ignore[invalid-assignment]


# --- the picture's adapter: knee.pictures.strip ----------------------------------------------


def _scene_for_the_picture() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The dark-line plane, its squint bounds and the 2 x 2 block: the inputs of a strip."""
    plane = _line_plane((52, 54))
    labels = _block()
    return plane, _bounds(plane), labels


def _anisotropic_scene() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Half a millimetre down a row, one along a column; a dark column and a dark pair of rows."""
    plane = _flat_plane()
    plane[:, 50] = DARK
    plane[52:54, :] = DARK
    bounds = physical_squint(plane, (0.5, 1.0), TILE_MM).bounds_rc
    labels = np.zeros(bounds.shape[:2], dtype=np.int32)
    labels[1:3, 2:6] = 1
    return plane, bounds, labels


def test_the_standing_names_a_strip_that_can_be_drawn_and_every_silence_apart() -> None:
    assert strip_standing("present", True) == "named"
    assert strip_standing("present", False) == "plane_not_saved"
    assert strip_standing(None, True) == "strip_not_saved"
    assert strip_standing("no_boundary", True) == "strip_has_no_boundary"
    assert strip_standing("predecessor_absent", True) == "strip_absent"
    assert strip_standing("lesion", True) == "strip_code_unknown"
    assert strip_standing(3, True) == "strip_code_unknown"


def test_the_standing_is_total_and_names_a_strip_only_when_its_plane_was_saved() -> (
    None
):
    # MUST NOT: draw a strip over a plane nobody saved, or a code the stage does not say; and
    # every answer, for any code and any plane flag, is one of the declared standings.
    for code in (*STRIP_CODES, None, "", "lesion", 1, b"present", ("present",)):
        for plane_held in (True, False, None, 1, 0, "yes", 1.0):
            standing = strip_standing(code, plane_held)
            assert standing in STRIP_STANDINGS, (code, plane_held)
            if standing == "named":
                assert code == "present" and plane_held is True


def test_the_band_midpoints_are_the_stages_own_trace_placed_on_the_plane() -> None:
    for spacing, (plane, bounds, labels) in (
        (SPACING, _scene_for_the_picture()),
        ((0.5, 1.0), _anisotropic_scene()),
    ):
        result = read_strip(
            plane,
            spacing,
            labels,
            bounds,
            1,
            STRIP_MM,
            SPLIT,
            PROMINENCE,
            MINIMUM,
            None,
            None,
            series_uid=SERIES,
            slice_index=SLICE,
            border=BORDER,
        )
        placed = band_centres_rc(
            result.edge_points, result.normals, result.band_mm, spacing
        )
        # The stage's own number: `dark_bands` made the same sum for its `trace` at the time.
        profiles = sample_profiles(
            plane, result.edge_points, result.normals, result.offsets_mm, spacing
        )
        _, _, trace, _ = dark_bands(
            profiles,
            SPLIT,
            np.zeros(len(result.edge_points), dtype=np.uint8),
            result.edge_points,
            result.normals,
            np.asarray(spacing),
        )
        bracketed = result.trace_codes == BRACKETED
        np.testing.assert_array_equal(placed[bracketed], trace[bracketed])
        assert bracketed.any()
        # MUST NOT: put a point at the edge for a band that was not bracketed.
        assert np.isnan(placed[~bracketed]).all()
        assert not placed.flags.writeable
    # By hand: the right cast of tile (1, 2) that starts at row 23.0, edge column 47.5, band 2.5
    # mm out at half a millimetre a pixel, is the point (23.0, 52.5); on a 1 mm column pitch it
    # is (23.0, 50.0).
    plane, bounds, labels = _scene_for_the_picture()
    result = read_strip(
        plane,
        SPACING,
        labels,
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    (cast,) = np.flatnonzero((result.edge_points == [23.0, 47.5]).all(axis=1))
    np.testing.assert_array_equal(
        band_centres_rc(result.edge_points, result.normals, result.band_mm, SPACING)[
            cast
        ],
        [23.0, 52.5],
    )
    np.testing.assert_array_equal(
        band_centres_rc(result.edge_points, result.normals, result.band_mm, (0.5, 1.0))[
            cast
        ],
        [23.0, 50.0],
    )


def test_the_adapter_hands_on_the_saved_values_and_alters_nothing() -> None:
    plane, bounds, labels = _scene_for_the_picture()
    alone = read_strip(
        plane,
        SPACING,
        labels,
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    # By hand, as a partner's exchange would have left them (a strip carries none yet): one
    # code for every point, none of them carried.
    result = dataclasses.replace(
        alone, exchange_codes=np.zeros(len(alone.edge_points), dtype=np.uint8)
    )
    before = {
        name: getattr(result, name).copy()
        for name in (
            "edge_points",
            "normals",
            "band_mm",
            "trace_codes",
            "exchange_codes",
        )
    }
    panel = strip_panel(
        "1.2.3",
        15,
        1,
        result.code,
        result.why,
        result.strip_mm,
        result.low_edge,
        result.high_edge,
        result.population_count,
        SPACING,
        plane,
        result.edge_points,
        result.normals,
        result.trace_codes,
        result.band_mm,
        result.exchange_codes,
        result.strip_mask,
        BORDER,
    )
    assert panel.standing == "named"
    assert (panel.series_uid, panel.slice_index, panel.object_index) == ("1.2.3", 15, 1)
    assert panel.border == BORDER
    assert panel.plane is not None and panel.plane.dtype == plane.dtype
    np.testing.assert_array_equal(panel.plane, plane)
    np.testing.assert_array_equal(panel.edge_points, result.edge_points)
    assert panel.trace_codes is not None and panel.trace_codes.dtype == np.uint8
    np.testing.assert_array_equal(panel.trace_codes, result.trace_codes)
    assert panel.exchange_codes is not None
    assert panel.exchange_codes.shape == (8 * TILE_PX,)
    np.testing.assert_array_equal(panel.strip_mask, result.strip_mask)
    assert panel.band_centres_rc is not None
    assert panel.band_centres_rc.shape == (8 * TILE_PX, 2)
    assert (panel.low_edge, panel.high_edge) == (result.low_edge, result.high_edge)
    assert panel.population_count == 1024 and panel.spacing_rc == SPACING
    for name, value in before.items():
        np.testing.assert_array_equal(getattr(result, name), value)
    assert not hasattr(panel, "normals") and not hasattr(panel, "band_mm")


def test_the_adapter_keeps_every_absence_absent() -> None:
    nothing = strip_panel(*([None] * 18))
    assert nothing.standing == "strip_not_saved" and nothing.code is None
    for name in (
        "border",
        "series_uid",
        "slice_index",
        "object_index",
        "why",
        "strip_mm",
        "low_edge",
        "high_edge",
        "population_count",
        "spacing_rc",
        "plane",
        "edge_points",
        "trace_codes",
        "band_centres_rc",
        "exchange_codes",
        "strip_mask",
    ):
        assert getattr(nothing, name) is None, name
    # Points without a spacing: drawn as points, with no band midpoints placed. A midpoint
    # placed without the spacing would be a guess; the picture says it has none.
    plane, bounds, labels = _scene_for_the_picture()
    result = read_strip(
        plane,
        SPACING,
        labels,
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    unplaced = strip_panel(
        "s",
        15,
        1,
        "present",
        "why",
        6.0,
        1.0,
        2.0,
        3,
        None,
        None,
        result.edge_points,
        result.normals,
        result.trace_codes,
        result.band_mm,
        result.exchange_codes,
        result.strip_mask,
        BORDER,
    )
    assert unplaced.band_centres_rc is None
    assert unplaced.standing == "plane_not_saved" and unplaced.plane is None
    assert unplaced.edge_points is not None
    assert len(unplaced.edge_points) == 8 * TILE_PX


def test_the_stage_does_not_import_the_drawing_layer_and_the_layer_imports_no_plotting() -> (
    None
):
    assert not [
        key
        for key, value in vars(strip).items()
        if getattr(value, "__module__", "").startswith("knee.pictures")
    ]
    tree = ast.parse(Path(pictures.__file__).read_text())
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert imported <= {"__future__", "dataclasses", "numpy", "knee"}, imported


# --- the drawer: workbench.render.strip_frames, end to end on a record shaped as the writer saves -
#
# The record is the one the writer is asked to save for a series (the unit's report spells it):
# `record["strips"]` holds the three vocabularies and one item per strip, each item naming its
# own ten arrays; the arrays are saved beside the series' others as `strip_s<slice>_o<object>_<field>`
# and the plane of each slice once as `strip_s<slice>_plane`; `record["arrays"]` is the writer's
# descriptor table. The field names are written out here, not read back from the drawer, so the
# test states the contract the writer and the drawer share.

FIELDS = (
    "edge_points",
    "normals",
    "offsets_mm",
    "profiles",
    "trace_codes",
    "band_mm",
    "exchange_codes",
    "native_digits",
    "strip_mask",
    "beyond_tiles",
)


def _made_strips() -> tuple[list[Strip], np.ndarray]:
    """Four strips of one series at slice 15 under one border, and the plane read."""
    plane, bounds, labels = _scene_for_the_picture()
    alone = read_strip(
        plane,
        SPACING,
        labels,
        bounds,
        1,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    boundaryless = read_strip(
        plane,
        SPACING,
        labels,
        bounds,
        7,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    absent = read_strip(
        None,  # ty: ignore[invalid-argument-type]
        SPACING,
        labels,
        bounds,
        9,
        STRIP_MM,
        SPLIT,
        PROMINENCE,
        MINIMUM,
        None,
        None,
        series_uid=SERIES,
        slice_index=SLICE,
        border=BORDER,
    )
    # By hand, as a partner's exchange would have left them (a strip carries none yet): the casts
    # of the right segment of tile (1, 2), the fourth, concurrent (1), those of the right segment
    # of tile (2, 2), the eighth, peer-only (2), the rest not carried (0).
    codes = np.zeros(len(alone.edge_points), dtype=np.uint8)
    codes[3 * TILE_PX : 4 * TILE_PX] = 1
    codes[7 * TILE_PX : 8 * TILE_PX] = 2
    codes.setflags(write=False)
    carried = dataclasses.replace(alone, object_index=2, exchange_codes=codes)
    return [alone, carried, boundaryless, absent], plane


def _json_number(value: float) -> float | None:
    return None if np.isnan(value) else float(value)


def _strips_record(
    strips: list[Strip], planes: dict[int, np.ndarray]
) -> tuple[dict, dict[str, np.ndarray]]:
    """The `strips` record and the arrays the writer saves for them."""
    items, arrays = [], {}
    for item in strips:
        tag = f"strip_s{item.slice_index}_o{item.object_index}"
        names = {field: f"{tag}_{field}" for field in FIELDS}
        for field, key in names.items():
            arrays[key] = getattr(item, field)
        plane_key = None
        if item.slice_index in planes:
            plane_key = f"strip_s{item.slice_index}_plane"
            arrays[plane_key] = planes[item.slice_index]
        items.append(
            {
                "series_uid": item.series_uid,
                "border": item.border,
                "slice_index": item.slice_index,
                "object_index": item.object_index,
                "code": item.code,
                "why": item.why,
                "strip_mm": item.strip_mm,
                "low_edge": _json_number(item.low_edge),
                "high_edge": _json_number(item.high_edge),
                "population_count": item.population_count,
                "points": len(item.edge_points),
                "offsets": len(item.offsets_mm),
                "plane_array": plane_key,
                "arrays": names,
            }
        )
    record = {
        "code_names": list(STRIP_CODES),
        "trace_code_values": dict(TRACE_CODES),
        "exchange_code_values": dict(EXCHANGE_CODES),
        "items": items,
    }
    return record, arrays


def _saved_record(
    directory: Path,
    strips: list[Strip],
    planes: dict[int, np.ndarray],
    *,
    name: str = "series",
    view: tuple[str, str, str] = ("Coronal", "1", "1"),
    spacing: object = None,
    edit=None,
) -> dict:
    """One series record shaped as the writer saves it, with its arrays on disk.

    `edit(record, arrays)` may disagree with the writer before the descriptors are made, so a
    tampered array still carries a descriptor that matches it and only the drawer's own checks
    can refuse it.
    """
    from workbench.measure.object_analysis import array_table

    record, arrays = _strips_record(strips, planes)
    if edit is not None:
        edit(record, arrays)
    np.savez_compressed(directory / f"{name}.npz", allow_pickle=False, **arrays)
    entry = {
        "study_uid": "study",
        "series_uid": name,
        "view": list(view),
        "artifact": f"{name}.npz",
        "spacing_rc_mm": [0.5, 0.5] if spacing is None else spacing,
        "strips": record,
        "arrays": array_table(arrays),
    }
    return json.loads(json.dumps(entry, allow_nan=False))


def _key(field: str, slice_index: int = 15, object_index: int = 1) -> str:
    return f"strip_s{slice_index}_o{object_index}_{field}"


def test_the_reader_reconstitutes_a_writer_shaped_record(tmp_path: Path) -> None:
    strips, plane = _made_strips()
    record = _saved_record(tmp_path, strips, {15: plane})
    artifact, panels = strip_frames.saved_strips(tmp_path, record)
    assert artifact == tmp_path / "series.npz"
    assert panels is not None and len(panels) == 4
    assert [p.standing for p in panels] == [
        "named",
        "named",
        "strip_has_no_boundary",
        "strip_absent",
    ]
    assert [(p.series_uid, p.slice_index) for p in panels] == [("series", 15)] * 4
    assert [p.border for p in panels] == [BORDER] * 4
    assert [p.object_index for p in panels] == [1, 2, 7, 9]
    alone, carried, boundaryless, absent = panels
    assert alone.plane is not None
    np.testing.assert_array_equal(alone.plane, plane)
    assert alone.exchange_codes is not None and alone.exchange_codes.shape == (0,)
    assert carried.exchange_codes is not None
    np.testing.assert_array_equal(
        carried.exchange_codes, np.repeat([0, 0, 0, 1, 0, 0, 0, 2], TILE_PX)
    )
    # The spacing came from the series record, and the midpoint was placed by it.
    assert alone.spacing_rc == (0.5, 0.5)
    assert alone.band_centres_rc is not None
    assert alone.edge_points is not None
    (cast,) = np.flatnonzero((alone.edge_points == [23.0, 47.5]).all(axis=1))
    np.testing.assert_array_equal(alone.band_centres_rc[cast], [23.0, 52.5])
    assert strip_frames.bracketed_centres(alone) == 2 * TILE_PX
    assert strip_frames.trace_counts(alone) == {
        "bracketed": 2 * TILE_PX,
        "no_dark_bracket": 6 * TILE_PX,
        "multiple_brackets": 0,
        "missing_profile": 0,
        "frame_clipped": 0,
        "empty_profile": 0,
        "invalid_measurement": 0,
    }
    assert strip_frames.exchange_counts(alone) == {}
    shown = strip_frames.exchange_counts(carried)
    assert (shown["not_carried"], shown["concurrent"], shown["peer_only"]) == (
        6 * TILE_PX,
        TILE_PX,
        TILE_PX,
    )
    assert boundaryless.edge_points is not None and len(boundaryless.edge_points) == 0
    assert absent.plane is not None, (
        "the plane at the slice is saved once for every strip"
    )


def test_the_reader_says_when_no_strips_were_saved_and_when_none_was_made(
    tmp_path: Path,
) -> None:
    strips, plane = _made_strips()
    record = _saved_record(tmp_path, strips, {15: plane})
    del record["strips"]
    _, panels = strip_frames.saved_strips(tmp_path, record)
    assert panels is None
    record = _saved_record(tmp_path, [], {})
    _, panels = strip_frames.saved_strips(tmp_path, record)
    assert panels == ()
    # No plane saved at the slice: the strip is drawn as points alone, and says so.
    record = _saved_record(tmp_path, strips[:1], {})
    _, panels = strip_frames.saved_strips(tmp_path, record)
    assert panels is not None and panels[0].standing == "plane_not_saved"
    assert panels[0].plane is None and panels[0].edge_points is not None
    # No spacing saved: the points are there and no midpoint is placed.
    record = _saved_record(tmp_path, strips[:1], {15: plane})
    del record["spacing_rc_mm"]
    _, panels = strip_frames.saved_strips(tmp_path, record)
    assert panels is not None
    assert panels[0].spacing_rc is None and panels[0].band_centres_rc is None
    assert panels[0].standing == "named"


def _vocabulary(name, change):
    def edit(record, arrays):
        record[name] = change(record[name])

    return edit


def _item(change):
    def edit(record, arrays):
        change(record["items"][0], arrays)

    return edit


def _array(field, change, **where):
    def edit(record, arrays):
        key = _key(field, **where)
        arrays[key] = change(arrays[key])

    return edit


DISAGREEMENTS = {
    "a trace value that is not the stage's": (
        _vocabulary("trace_code_values", lambda v: {**v, "bracketed": 9}),
        "saved_strips_vocabulary_mismatch",
    ),
    "an exchange vocabulary that is not the stage's": (
        _vocabulary("exchange_code_values", lambda v: {}),
        "saved_strips_vocabulary_mismatch",
    ),
    "strip codes that are not the stage's": (
        _vocabulary("code_names", lambda v: v[:1]),
        "saved_strips_vocabulary_mismatch",
    ),
    "items that are not a list": (
        _vocabulary("items", lambda v: "no"),
        "saved_strips_items_invalid",
    ),
    "a code the stage does not say": (
        _item(lambda item, arrays: item.update(code="lesion")),
        "saved_strip_code_unknown",
    ),
    "an item that is not a record": (
        lambda record, arrays: record["items"].__setitem__(0, "x"),
        "saved_strip_not_a_record",
    ),
    "a series identifier that is not text": (
        _item(lambda item, arrays: item.update(series_uid=5)),
        "saved_strip_field_invalid",
    ),
    "an object index of zero": (
        _item(lambda item, arrays: item.update(object_index=0)),
        "saved_strip_not_a_whole_number",
    ),
    "an object index that is a bool": (
        _item(lambda item, arrays: item.update(object_index=True)),
        "saved_strip_not_a_whole_number",
    ),
    "a point count that is not the array's": (
        _item(lambda item, arrays: item.update(points=3)),
        "saved_strip_counts_mismatch",
    ),
    "an offset count that is not the array's": (
        _item(lambda item, arrays: item.update(offsets=3)),
        "saved_strip_counts_mismatch",
    ),
    "an array left unnamed": (
        _item(lambda item, arrays: item["arrays"].pop("band_mm")),
        "saved_strip_array_unnamed",
    ),
    "an array map that is not a map": (
        _item(lambda item, arrays: item.update(arrays=[])),
        "saved_strip_arrays_missing",
    ),
    "an array in the wrong type": (
        _array("edge_points", lambda a: a.astype(np.float32)),
        "saved_strip_representation_invalid",
    ),
    "an array of the wrong size": (
        _array("normals", lambda a: a[:-1]),
        "saved_strip_shape_mismatch",
    ),
    "exchange codes that are neither one a point nor none": (
        _array("exchange_codes", lambda a: np.zeros(3, dtype=np.uint8)),
        "saved_strip_shape_mismatch:exchange_codes",
    ),
    "a trace code the stage does not say": (
        _array("trace_codes", lambda a: np.full_like(a, 99)),
        "saved_strip_trace_code_unknown",
    ),
    "an exchange code the stage does not say": (
        _array("exchange_codes", lambda a: np.full(8 * TILE_PX, 99, dtype=np.uint8)),
        "saved_strip_exchange_code_unknown",
    ),
    "a border that is not text": (
        _item(lambda item, arrays: item.update(border=5)),
        "saved_strip_field_invalid:border",
    ),
    "a border the stage does not say": (
        _item(lambda item, arrays: item.update(border="bright")),
        "saved_strip_border_unknown:bright",
    ),
    "two strips of one border, slice and object": (
        lambda record, arrays: record["items"].append(dict(record["items"][0])),
        "saved_strips_entry_repeated",
    ),
    "a plane that is not the footprint's": (
        lambda record, arrays: arrays.__setitem__(
            "strip_s15_plane", arrays["strip_s15_plane"][:10, :10]
        ),
        "saved_strip_plane_mismatch",
    ),
    "a plane that is not numbers": (
        lambda record, arrays: arrays.__setitem__(
            "strip_s15_plane", arrays["strip_s15_plane"].astype(str)
        ),
        "saved_strip_representation_invalid:plane",
    ),
    "a plane named by a number": (
        _item(lambda item, arrays: item.update(plane_array=5)),
        "saved_strip_field_invalid:plane_array",
    ),
    "a plane named and not saved": (
        _item(lambda item, arrays: item.update(plane_array="nowhere")),
        "missing_saved_array:nowhere",
    ),
    "a half-width that is not a number": (
        _item(lambda item, arrays: item.update(strip_mm="six")),
        "saved_strip_not_a_number:strip_mm",
    ),
}


@pytest.mark.parametrize(
    ("edit", "message"), list(DISAGREEMENTS.values()), ids=list(DISAGREEMENTS)
)
def test_the_reader_refuses_a_saved_record_that_disagrees_with_the_writer(
    tmp_path: Path, edit, message
) -> None:
    # MUST NOT: draw a vocabulary that is not the stage's, an array whose type or size is not
    # the record's, a code outside the vocabulary, or a plane that is not the footprint's; each
    # is named and raised.
    strips, plane = _made_strips()
    record = _saved_record(tmp_path, strips, {15: plane}, edit=edit)
    with pytest.raises(ValueError, match=message):
        strip_frames.saved_strips(tmp_path, record)


def test_a_tampered_array_a_bad_spacing_and_a_record_that_is_not_a_record_are_refused(
    tmp_path: Path,
) -> None:
    strips, plane = _made_strips()
    tampered = _saved_record(tmp_path, strips, {15: plane})
    tampered["arrays"][_key("trace_codes")]["digest"] = "changed"
    with pytest.raises(ValueError, match="saved_array_digest_mismatch"):
        strip_frames.saved_strips(tmp_path, tampered)
    for spacing in ([0.5], [0.5, 0.0], [0.5, -1.0], "0.5", [0.5, True], [0.5, "x"]):
        record = _saved_record(tmp_path, strips[:1], {15: plane}, spacing=spacing)
        with pytest.raises(ValueError, match="saved_strip_spacing_invalid"):
            strip_frames.saved_strips(tmp_path, record)
    record = _saved_record(tmp_path, strips[:1], {15: plane})
    record["strips"] = "yes"
    with pytest.raises(ValueError, match="saved_strips_not_a_record"):
        strip_frames.saved_strips(tmp_path, record)


def test_an_out_directory_outside_data_and_a_study_with_no_records_are_argument_refusals(
    tmp_path: Path,
) -> None:
    strips, plane = _made_strips()
    record = _saved_record(tmp_path, strips, {15: plane})
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    with pytest.raises(ArgumentRefusal, match="private data directory"):
        strip_frames.draw(tmp_path, "study", tmp_path / "out")
    inside = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    with pytest.raises(ArgumentRefusal, match="no saved records for this study"):
        strip_frames.draw(tmp_path, "another study", inside)
    assert not inside.exists(), "a refused call made its directory"


def test_a_record_that_disagrees_is_raised_before_any_sheet_is_drawn(
    tmp_path: Path,
) -> None:
    strips, plane = _made_strips()
    record = _saved_record(
        tmp_path,
        strips,
        {15: plane},
        edit=_array("trace_codes", lambda a: np.full_like(a, 99)),
    )
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    with pytest.raises(ValueError, match="saved_strip_trace_code_unknown"):
        strip_frames.draw(tmp_path, "study", out)
    assert not out.exists()


def test_the_drawer_writes_one_sheet_per_series_with_its_manifest(
    tmp_path: Path,
) -> None:
    """The impure edge, end to end: one image per series under data/, bound to the receipt."""
    strips, plane = _made_strips()
    drawn = _saved_record(tmp_path, strips, {15: plane})
    silent = _saved_record(tmp_path, [], {}, name="plain", view=("Sagittal", "0", "0"))
    del silent["strips"]
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [drawn, silent]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = strip_frames.draw(tmp_path, "study", out)
        assert manifest["images"] == [
            "01-coronal-fs1-fat1.png",
            "02-sagittal-fs0-fat0.png",
        ]
        assert manifest["image"] == "01-coronal-fs1-fat1.png"
        for name in manifest["images"]:
            assert (out / name).stat().st_size > 0
        assert (out / "manifest.json").exists()
        assert manifest["standings"] == list(STRIP_STANDINGS)
        assert manifest["schema"] == "strip-frames-v2"
        assert manifest["borders"] == [BORDER, OTHER_BORDER]
        assert set(manifest["legend"]["trace_codes"]) == set(TRACE_CODES)
        assert set(manifest["legend"]["exchange_codes"]) == set(EXCHANGE_CODES)
        first, second = manifest["series"]
        assert first["strips"] is not None and second["strips"] is None
        assert [s["drawn"] for s in first["strips"]] == [
            "named",
            "named",
            "strip_has_no_boundary",
            "strip_absent",
        ]
        assert [s["object_index"] for s in first["strips"]] == [1, 2, 7, 9]
        assert [s["points"] for s in first["strips"]] == [
            8 * TILE_PX,
            8 * TILE_PX,
            0,
            0,
        ]
        assert [s["band_midpoints"] for s in first["strips"]] == [
            2 * TILE_PX,
            2 * TILE_PX,
            0,
            0,
        ]
        assert first["strips"][0]["trace_counts"]["bracketed"] == 2 * TILE_PX
        assert first["strips"][1]["exchange_counts"]["concurrent"] == TILE_PX
        assert first["strips"][0]["exchange_counts"] == {}
        # One row for each (slice, object index) with a cell for each border. The record holds
        # the strips under one border, so the other border's cell of every row is `unpaired`.
        assert all(s["border"] == BORDER for s in first["strips"])
        assert [(p["slice_index"], p["object_index"]) for p in first["pairs"]] == [
            (15, 1),
            (15, 2),
            (15, 7),
            (15, 9),
        ]
        assert [p["cells"][OTHER_BORDER] for p in first["pairs"]] == ["unpaired"] * 4
        assert second["pairs"] is None
        assert len(first["image_sha256"]) == 64 and len(first["artifact_sha256"]) == 64
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_the_drawer_draws_the_points_alone_when_the_plane_at_the_slice_was_not_saved(
    tmp_path: Path,
) -> None:
    strips, _ = _made_strips()
    record = _saved_record(tmp_path, strips[:1], {})
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = strip_frames.draw(tmp_path, "study", out)
        (series,) = manifest["series"]
        (only,) = series["strips"]
        assert only["standing"] == "plane_not_saved"
        assert only["drawn"] == "points_alone"
        assert only["points"] == 8 * TILE_PX
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_the_picture_module_is_the_adapter_the_drawer_reads() -> None:
    assert strip_frames.pictures is pictures
    assert strip_frames.STRIP_CODES == STRIP_CODES
    assert set(strip_frames.STANDING_WORDS) == set(STRIP_STANDINGS)
    assert set(strip_frames.TRACE_COLOURS) == set(TRACE_CODES)
    assert set(strip_frames.EXCHANGE_COLOURS) == set(EXCHANGE_CODES)
