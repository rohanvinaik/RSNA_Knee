"""Intent tests for the first lens's measurement and orchestration (knee.collapse.first_lens),
both signs, written from the contract: a dark ring enclosing a dark centre marks the ring
air-connected only where it touches the border and never the enclosed centre; a border tile is
beside air whether or not any tile is dark; over a synthetic stack a dark tile enclosed by
kept tiles is not_background (the dark interior, never air), a mixed tile beside the air is
undecided and a mixed tile away from it is not_background, a NaN split gives
`split_unavailable` with nothing cleared, every background tile is adjacent only to background
or undecided tiles or lies on a straight all-dark boundary (its not_background neighbour holds
no dark pixel), the vectorised map is the scalar
decision at every tile, nothing of the caller's is written, and the ledger carries the
consumption then the production. The CONTRACT's proof gate."""

from __future__ import annotations

import math
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from knee.collapse.first_lens import (
    LENS_CODES,
    RULE_VERSION,
    TILE_CODES,
    FirstLens,
    air_connectivity,
    read_first_lens,
    tile_code,
)
from knee.collapse.squint_stack import SquintStack, read_squint_stack
from knee.study.series import Series, SeriesGeometry
from knee.study.tables import SeriesRow
from knee.telemetry import recording

#: An axial-like header at half a millimetre a pixel: a 2 mm tile is 4 px; the plane is 24 px
#: square, a 6 x 6 grid of tiles, three slices one millimetre apart.
AXIAL = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
NORMAL = np.array([0.0, 0.0, 1.0])
SPACING = (0.5, 0.5)
TILE_MM = 2.0
TILE_PX = 4
TILES = 6
SLICES = 3
#: The two stored values and the valley between them.
AIR, BRIGHT, SPLIT = 0.0, 100.0, 10.0

BACKGROUND = TILE_CODES.index("background")
NOT_BACKGROUND = TILE_CODES.index("not_background")
UNDECIDED = TILE_CODES.index("undecided")
TILE_EMPTY = TILE_CODES.index("tile_empty")

NOWHERE = Path("/nonexistent/the-funnel/first-lens")

#: The plane, tile by tile: B all dark (the air, touching the border), U partly dark beside the
#: air (half its pixels dark), L all bright, D all dark but enclosed (a dark interior), M partly
#: dark away from the air. The border row and column are air; the ring inside it straddles.
PATTERN = ("BBBBBB", "BUUUUB", "BULMUB", "BULDUB", "BUUUUB", "BBBBBB")
EXPECTED = {
    "B": BACKGROUND,
    "U": UNDECIDED,
    "L": NOT_BACKGROUND,
    "D": NOT_BACKGROUND,
    "M": NOT_BACKGROUND,
}


def _plane() -> np.ndarray:
    plane = np.full((TILES * TILE_PX, TILES * TILE_PX), BRIGHT, dtype=np.float64)
    for i, row in enumerate(PATTERN):
        for j, kind in enumerate(row):
            r0, c0 = i * TILE_PX, j * TILE_PX
            if kind in "BD":
                plane[r0 : r0 + TILE_PX, c0 : c0 + TILE_PX] = AIR
            elif kind in "UM":
                plane[r0 : r0 + TILE_PX // 2, c0 : c0 + TILE_PX] = AIR
    return plane


def _expected_codes() -> np.ndarray:
    return np.array(
        [[EXPECTED[kind] for kind in row] for row in PATTERN], dtype=np.uint8
    )


def _geometry(slices: int = SLICES) -> SeriesGeometry:
    positions = np.array([[0.0, 0.0, float(z)] for z in range(slices)])
    return SeriesGeometry(
        normal=NORMAL.copy(),
        orientation=np.tile(AXIAL, (slices, 1)),
        position=positions,
        spacing=np.tile(np.asarray(SPACING, dtype=np.float64), (slices, 1)),
        along_normal=positions @ NORMAL,
        orientation_spread=0.0,
        origin_spread_mm=0.0,
    )


def _series(volume: np.ndarray | None, uid: str = "series-first-lens") -> Series:
    return Series(
        row=SeriesRow("study-first-lens", uid, "1", "1", "Coronal"),
        directory=NOWHERE / uid,
        slices=(),
        stack=("stackable",),
        volume=volume,
        geometry=_geometry(),
    )


def _volume(plane: np.ndarray | None = None) -> np.ndarray:
    return np.stack([_plane() if plane is None else plane for _ in range(SLICES)])


def _stack(volume: np.ndarray | None = None) -> SquintStack:
    return read_squint_stack(_series(_volume() if volume is None else volume), TILE_MM)


def _ring(touching_border: bool) -> np.ndarray:
    """One slice of a 7 x 7 grid: a dark square ring at rows and columns 1 and 5 enclosing a
    dark centre at (3, 3), the two parted by bright tiles; with `touching_border` the ring also
    reaches the top row through tile (0, 3)."""
    dark = np.zeros((1, 7, 7), dtype=bool)
    dark[0, 1, 1:6] = dark[0, 5, 1:6] = True
    dark[0, 1:6, 1] = dark[0, 1:6, 5] = True
    dark[0, 3, 3] = True
    if touching_border:
        dark[0, 0, 3] = True
    return dark


# --- the measurement: positive --------------------------------------------------------------


def test_a_dark_ring_that_touches_the_border_is_air_connected_and_its_enclosed_centre_never() -> (
    None
):
    dark = _ring(touching_border=True)
    air, beside = air_connectivity(dark)
    assert air.shape == dark.shape and air.dtype == np.bool_
    assert beside.shape == dark.shape and beside.dtype == np.bool_
    # The whole ring, and the tile that joins it to the border, are air-connected.
    ring = _ring(touching_border=True)
    ring[0, 3, 3] = False
    np.testing.assert_array_equal(air[0], ring[0])
    assert not air[0, 3, 3]
    # Beside the air: every four-neighbour of an air-connected tile, and the border.
    assert beside[0, 2, 2] and beside[0, 2, 3] and beside[0, 4, 4]
    assert beside[0, 0, 0] and beside[0, 6, 6] and beside[0, 0, 6]
    # The enclosed centre's neighbours are bright tiles beside no air: (3, 3) itself is not
    # beside the air, since nothing four-adjacent to it reaches the border.
    assert not beside[0, 3, 3]


def test_a_dark_ring_that_does_not_touch_the_border_is_air_connected_nowhere() -> None:
    # MUST NOT: call a dark interior air because it is dark; air comes in at the frame.
    dark = _ring(touching_border=False)
    air, beside = air_connectivity(dark)
    assert not air.any()
    border = np.zeros((7, 7), dtype=bool)
    border[0, :] = border[-1, :] = border[:, 0] = border[:, -1] = True
    np.testing.assert_array_equal(beside[0], border)


def test_a_border_tile_is_beside_air_whether_or_not_any_tile_is_dark() -> None:
    nothing_dark = np.zeros((2, 5, 4), dtype=bool)
    air, beside = air_connectivity(nothing_dark)
    assert not air.any()
    border = np.zeros((5, 4), dtype=bool)
    border[0, :] = border[-1, :] = border[:, 0] = border[:, -1] = True
    for z in range(2):
        np.testing.assert_array_equal(beside[z], border)
    all_dark = np.ones((2, 5, 4), dtype=bool)
    air, beside = air_connectivity(all_dark)
    assert air.all() and beside.all()


def test_connectivity_is_four_connected_within_a_slice_and_never_across_slices() -> (
    None
):
    # A dark tile that touches the border only at a corner is not connected to it (four-
    # connected, never eight); and a dark tile under an air tile of another slice is not air.
    dark = np.zeros((2, 4, 4), dtype=bool)
    dark[0, 0, 0] = True
    dark[0, 1, 1] = True
    dark[1, 1, 1] = True
    air, _ = air_connectivity(dark)
    assert air[0, 0, 0]
    assert not air[0, 1, 1]
    assert not air[1, 1, 1]
    # Four-adjacent to the border's tile, it IS connected.
    dark[0, 0, 1] = True
    air, _ = air_connectivity(dark)
    assert air[0, 0, 1] and air[0, 1, 1]
    assert not air[1, 1, 1]


# --- the measurement: negative --------------------------------------------------------------


@pytest.mark.parametrize(
    "bad", [np.zeros((4, 4), dtype=bool), np.zeros((1, 2, 4, 4), dtype=bool)]
)
def test_a_grid_that_is_not_slices_of_tiles_is_refused_by_name(bad: np.ndarray) -> None:
    with pytest.raises(ValueError, match="invalid_all_dark"):
        air_connectivity(bad)


def test_an_empty_grid_is_empty_and_never_an_error() -> None:
    air, beside = air_connectivity(np.zeros((0, 0, 0), dtype=bool))
    assert air.shape == (0, 0, 0) and beside.shape == (0, 0, 0)


def test_the_measurement_writes_nothing_of_the_callers_and_freezes_its_own() -> None:
    dark = _ring(touching_border=True)
    before = dark.copy()
    air, beside = air_connectivity(dark)
    np.testing.assert_array_equal(dark, before)
    assert dark.flags.writeable
    assert not air.flags.writeable and not beside.flags.writeable


# --- the orchestration: positive ------------------------------------------------------------


def test_every_tile_of_the_synthetic_stack_is_named_as_the_rule_says() -> None:
    lens = read_first_lens(_stack(), SPLIT)
    assert isinstance(lens, FirstLens)
    assert lens.code == "present"
    assert lens.series_uid == "series-first-lens"
    assert lens.split == SPLIT
    assert lens.rule_version == RULE_VERSION
    assert lens.codes.shape == (SLICES, TILES, TILES)
    assert lens.codes.dtype == np.uint8
    for z in range(SLICES):
        np.testing.assert_array_equal(lens.codes[z], _expected_codes())
    # The border is air; the ring inside it straddles the skin line; the dark interior and
    # the mixed tile away from the air are not_background, with the two bright tiles.
    assert lens.counts == (SLICES * 20, SLICES * 4, SLICES * 12, 0)
    assert "present" not in lens.why and str(SLICES) in lens.why


def test_a_dark_tile_enclosed_by_not_background_is_not_background_never_air() -> None:
    lens = read_first_lens(_stack(), SPLIT)
    assert PATTERN[3][3] == "D"
    assert lens.codes[0, 3, 3] == NOT_BACKGROUND
    # It is all dark: the tile's maximum lies at or below the split.
    stack = _stack()
    assert stack.maximum[0, 3, 3] <= SPLIT


def test_a_mixed_tile_beside_the_air_is_undecided_and_one_away_from_it_is_not_background() -> (
    None
):
    lens = read_first_lens(_stack(), SPLIT)
    assert PATTERN[1][2] == "U" and lens.codes[0, 1, 2] == UNDECIDED
    assert PATTERN[2][3] == "M" and lens.codes[0, 2, 3] == NOT_BACKGROUND


def test_no_background_tile_touches_a_not_background_tile_except_on_a_straight_all_dark_boundary() -> (
    None
):
    # Every four-neighbour of a background tile is background, undecided or empty -- or a
    # not_background tile that holds no dark pixel at all, so the air ends exactly on the
    # tile's edge.
    stack = _stack()
    lens = read_first_lens(stack, SPLIT)
    for z in range(SLICES):
        codes = lens.codes[z]
        for i, j in zip(*np.nonzero(codes == BACKGROUND), strict=True):
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ni, nj = i + di, j + dj
                if not (0 <= ni < TILES and 0 <= nj < TILES):
                    continue
                neighbour = codes[ni, nj]
                if neighbour == NOT_BACKGROUND:
                    assert stack.minimum[z, ni, nj] > SPLIT, (z, ni, nj)
                else:
                    assert neighbour in (BACKGROUND, UNDECIDED, TILE_EMPTY)


def test_a_fully_bright_tile_beside_the_air_is_not_background_on_a_straight_boundary() -> (
    None
):
    # The positive case of the invariant above: air meets bright exactly on a tile edge.
    plane = np.full((TILES * TILE_PX, TILES * TILE_PX), BRIGHT, dtype=np.float64)
    plane[: 2 * TILE_PX, :] = AIR
    lens = read_first_lens(_stack(_volume(plane)), SPLIT)
    assert set(lens.codes[0, :2, :].ravel().tolist()) == {BACKGROUND}
    assert set(lens.codes[0, 2:, :].ravel().tolist()) == {NOT_BACKGROUND}


def test_the_vectorised_map_is_the_scalar_decision_at_every_tile() -> None:
    # The one statement of the rule is `tile_code`; the map must say what it says, tile by
    # tile, over a stack that holds every kind of tile including an empty one.
    volume = _volume()
    volume[1, 2 * TILE_PX : 3 * TILE_PX, 2 * TILE_PX : 3 * TILE_PX] = np.nan
    stack = _stack(volume)
    lens = read_first_lens(stack, SPLIT)
    finite = np.isfinite(stack.coverage) & (stack.coverage > 0)
    all_dark = finite & (stack.maximum <= SPLIT)
    any_dark = finite & (stack.minimum <= SPLIT)
    air, beside = air_connectivity(all_dark)
    for z in range(SLICES):
        for i in range(TILES):
            for j in range(TILES):
                expected = tile_code(
                    bool(finite[z, i, j]),
                    bool(all_dark[z, i, j]),
                    bool(any_dark[z, i, j]),
                    bool(air[z, i, j]),
                    bool(beside[z, i, j]),
                )
                assert TILE_CODES[lens.codes[z, i, j]] == expected, (z, i, j)
    assert lens.codes[1, 2, 2] == TILE_EMPTY
    assert lens.counts[TILE_EMPTY] == 1


def test_the_ledger_carries_the_consumption_then_the_production_with_its_counts() -> (
    None
):
    # The stack is made BEFORE the block, so the ledger holds the lens's own two events only.
    stack = _stack()
    with recording() as run_ledger:
        read_first_lens(stack, SPLIT)
    events = run_ledger.events()
    assert [event.name for event in events] == [
        "squint_stack.consumed_by.first_lens",
        "first_lens.produced",
    ]
    assert dict(events[0].counts) == {"stack": 1}
    assert dict(events[1].counts) == {
        "background": SLICES * 20,
        "not_background": SLICES * 4,
        "undecided": SLICES * 12,
    }


def test_an_all_dark_stack_is_all_background_and_an_all_bright_one_all_not_background() -> (
    None
):
    dark = read_first_lens(_stack(np.full((SLICES, 8, 8), AIR)), SPLIT)
    assert set(dark.codes.ravel().tolist()) == {BACKGROUND}
    bright = read_first_lens(_stack(np.full((SLICES, 8, 8), BRIGHT)), SPLIT)
    assert set(bright.codes.ravel().tolist()) == {NOT_BACKGROUND}


# --- the orchestration: negative ------------------------------------------------------------


def test_a_nan_split_abstains_on_the_series_and_clears_nothing() -> None:
    # MUST NOT: declare air without a valley to read. Every tile with a finite pixel stays in
    # play as not_background; an empty tile is empty; the counts and the ledger say no tile
    # was cleared.
    volume = _volume()
    volume[0, :TILE_PX, :TILE_PX] = np.nan
    stack = _stack(volume)
    with recording() as run_ledger:
        lens = read_first_lens(stack, float("nan"))
    assert lens.code == "split_unavailable"
    assert math.isnan(lens.split)
    assert lens.rule_version == RULE_VERSION
    assert lens.codes.shape == (SLICES, TILES, TILES)
    assert lens.codes[0, 0, 0] == TILE_EMPTY
    assert set(lens.codes.ravel().tolist()) == {NOT_BACKGROUND, TILE_EMPTY}
    assert lens.counts == (0, SLICES * TILES * TILES - 1, 0, 1)
    assert "clears nothing" in lens.why
    assert dict(run_ledger.events()[1].counts) == {
        "background": 0,
        "not_background": SLICES * TILES * TILES - 1,
        "undecided": 0,
    }


@pytest.mark.parametrize("split", [None, True, "ten", float("inf")])
def test_a_split_that_is_not_a_finite_number_is_no_valley(split: object) -> None:
    # Total over what it is handed: a value that is not a finite number is no valley at all.
    lens = read_first_lens(_stack(), split)  # type: ignore[arg-type]
    assert lens.code == "split_unavailable"
    assert set(lens.codes.ravel().tolist()) == {NOT_BACKGROUND}


def test_a_stack_that_is_not_present_is_the_named_absence_with_empty_codes() -> None:
    absent = read_squint_stack(_series(None, "series-none"), TILE_MM)
    assert absent.code == "no_stacked_volume"
    with recording() as run_ledger:
        lens = read_first_lens(absent, SPLIT)
    assert lens.code == "predecessor_absent"
    assert lens.series_uid == "series-none"
    assert "no_stacked_volume" in lens.why
    assert lens.codes.shape == (0, 0, 0) and lens.codes.dtype == np.uint8
    assert lens.counts == (0, 0, 0, 0)
    # The split it was handed is kept as the bar it was given, never a zero.
    assert lens.split == SPLIT
    events = run_ledger.events()
    assert dict(events[0].counts) == {"stack": 0}
    assert dict(events[1].counts) == {
        "background": 0,
        "not_background": 0,
        "undecided": 0,
    }
    gone = read_squint_stack(replace(_series(_volume()), geometry=None), TILE_MM)
    assert read_first_lens(gone, SPLIT).code == "predecessor_absent"


def test_the_lens_never_clears_a_tile_it_is_unsure_of() -> None:
    # MUST NOT: a tile that is background is all dark and reaches the border; a dark interior
    # and a straddling tile are never background, whatever lies around them.
    stack = _stack()
    lens = read_first_lens(stack, SPLIT)
    cleared = lens.codes == BACKGROUND
    assert cleared.any()
    assert np.all(stack.maximum[cleared] <= SPLIT)
    assert not cleared[0, 3, 3]
    assert not cleared[0, 1:5, 1:5].any()


def test_an_empty_tile_is_its_own_code_and_never_background() -> None:
    volume = _volume()
    # An empty tile on the border, in the air: still empty, never cleared as air.
    volume[2, :TILE_PX, :TILE_PX] = np.nan
    lens = read_first_lens(_stack(volume), SPLIT)
    assert lens.codes[2, 0, 0] == TILE_EMPTY
    assert lens.codes[2, 0, 1] == BACKGROUND
    assert lens.counts[TILE_EMPTY] == 1


def test_nothing_of_the_callers_stack_is_written_and_the_codes_are_frozen() -> None:
    stack = _stack()
    before = (stack.maximum.copy(), stack.minimum.copy(), stack.coverage.copy())
    lens = read_first_lens(stack, SPLIT)
    np.testing.assert_array_equal(stack.maximum, before[0])
    np.testing.assert_array_equal(stack.minimum, before[1])
    np.testing.assert_array_equal(stack.coverage, before[2])
    assert not lens.codes.flags.writeable
    assert not read_first_lens(stack, float("nan")).codes.flags.writeable


def test_every_code_is_in_its_vocabulary() -> None:
    present = read_first_lens(_stack(), SPLIT)
    unavailable = read_first_lens(_stack(), float("nan"))
    absent = read_first_lens(read_squint_stack(_series(None), TILE_MM), SPLIT)
    assert {present.code, unavailable.code, absent.code} == set(LENS_CODES)
    for lens in (present, unavailable, absent):
        assert set(lens.codes.ravel().tolist()) <= set(range(len(TILE_CODES)))
        assert len(lens.counts) == len(TILE_CODES)
        assert sum(lens.counts) == lens.codes.size
