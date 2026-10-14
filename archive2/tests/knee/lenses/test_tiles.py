"""Intent tests for the tile digits' measurement and orchestration (knee.lenses.tiles), both
signs, written from the contract and the founder's rulings of 2026-10-13: over a grid holding
every tile code, with finite and NaN medians, the mask marks exactly the not_background and
undecided tiles with a finite median and never a background, empty, NaN-median or unknown-index
tile, and agrees with `tile_population_code` at every tile; over a synthetic stack and first
lens the edges come from the kept tiles only, a cleared tile reads place_unread (stored 2) and
never a digit, the population count equals the kept finite tiles, a population below the bar
gives every tile silent, an absent stack or an absent lens gives predecessor_absent, a shape
mismatch is refused by name, nothing of the caller's is written, and the ledger carries the
two consumptions then the production. The CONTRACT's proof gate."""

from __future__ import annotations

import math
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from knee.collapse.first_lens import TILE_CODES, FirstLens, read_first_lens
from knee.collapse.regime import tercile_edges
from knee.collapse.squint_stack import SquintStack, read_squint_stack
from knee.lenses.digits import DIGIT_CODES, READ_CODES, digit_code
from knee.lenses.places import CODE_VALUES, DIGIT_VALUES, SILENT
from knee.lenses.tiles import (
    POPULATION_CODES,
    TILE_DIGIT_CODES,
    TileDigits,
    population_mask,
    read_tile_digits,
    tile_population_code,
)
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
#: The two stored values and the valley between them; the bar the terciles are read under.
AIR, BRIGHT, SPLIT = 0.0, 100.0, 10.0
BAR = 8

BACKGROUND = TILE_CODES.index("background")
NOT_BACKGROUND = TILE_CODES.index("not_background")
UNDECIDED = TILE_CODES.index("undecided")
TILE_EMPTY = TILE_CODES.index("tile_empty")

BELOW, AT, ABOVE = (CODE_VALUES[name] for name in READ_CODES)
UNREAD = CODE_VALUES["place_unread"]

NOWHERE = Path("/nonexistent/the-funnel/tile-digits")

#: The plane, tile by tile, as the first lens's proof gate has it: B all dark (the air, touching
#: the border), U partly dark beside the air (half its pixels dark), L all bright, D all dark but
#: enclosed (a dark interior), M partly dark away from the air. The lens clears the border ring
#: (B) and keeps the rest; the kept medians are 50 (U, M), 100 (L) and 0 (D).
PATTERN = ("BBBBBB", "BUUUUB", "BULMUB", "BULDUB", "BUUUUB", "BBBBBB")
MEDIAN = {"B": AIR, "U": 50.0, "L": BRIGHT, "D": AIR, "M": 50.0}
CLEARED = "B"


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


def _series(volume: np.ndarray | None, uid: str = "series-tile-digits") -> Series:
    return Series(
        row=SeriesRow("study-tile-digits", uid, "1", "1", "Coronal"),
        directory=NOWHERE / uid,
        slices=(),
        stack=("stackable",),
        volume=volume,
        geometry=_geometry(),
    )


def _volume(empty_tile: tuple[int, int, int] | None = (1, 2, 2)) -> np.ndarray:
    """Three slices of the pattern; by default tile (row 2, column 2) of slice 1 holds no
    finite pixel, so the stack carries one empty tile (an L tile, median 100, in the lens's
    `tile_empty`)."""
    volume = np.stack([_plane() for _ in range(SLICES)])
    if empty_tile is not None:
        z, i, j = empty_tile
        volume[z, i * TILE_PX : (i + 1) * TILE_PX, j * TILE_PX : (j + 1) * TILE_PX] = (
            np.nan
        )
    return volume


def _stack(volume: np.ndarray | None = None, tile_mm: float = TILE_MM) -> SquintStack:
    return read_squint_stack(_series(_volume() if volume is None else volume), tile_mm)


def _lens(stack: SquintStack, split: float = SPLIT) -> FirstLens:
    return read_first_lens(stack, split)


def _kept_medians(volume: np.ndarray | None = None) -> list[float]:
    """The population by hand: every tile the lens keeps (not B) with a finite median, over
    every slice; the empty tile is left out."""
    stack = _stack(volume)
    kept = []
    for z in range(SLICES):
        for i, row in enumerate(PATTERN):
            for j, kind in enumerate(row):
                if kind == CLEARED or not np.isfinite(stack.median[z, i, j]):
                    continue
                assert stack.median[z, i, j] == MEDIAN[kind], (z, i, j, kind)
                kept.append(MEDIAN[kind])
    return kept


# --- the measurement: positive --------------------------------------------------------------


def _every_code_grid() -> tuple[np.ndarray, np.ndarray]:
    """One slice of 2 x 4 tiles holding every tile code once with a finite median and once
    with NaN, plus a second slice holding two indices outside the vocabulary."""
    codes = np.array(
        [
            [[BACKGROUND, NOT_BACKGROUND, UNDECIDED, TILE_EMPTY]] * 2,
            [[len(TILE_CODES), 255, NOT_BACKGROUND, UNDECIDED]] * 2,
        ],
        dtype=np.uint8,
    )
    median = np.array(
        [
            [[1.0, 2.0, 3.0, 4.0], [np.nan, np.nan, np.nan, np.nan]],
            [[5.0, 6.0, 7.0, np.nan], [np.nan, np.nan, 8.0, np.nan]],
        ],
        dtype=np.float64,
    )
    return codes, median


def test_the_mask_marks_exactly_the_kept_tiles_with_a_finite_median() -> None:
    codes, median = _every_code_grid()
    mask = population_mask(codes, median)
    assert mask.shape == codes.shape and mask.dtype == np.bool_
    expected = np.zeros(codes.shape, dtype=bool)
    expected[0, 0, 1] = expected[0, 0, 2] = True  # not_background, undecided, finite
    expected[1, 0, 2] = True  # not_background, finite
    expected[1, 1, 2] = True  # not_background, finite
    np.testing.assert_array_equal(mask, expected)


def test_the_mask_never_counts_a_background_empty_nan_median_or_unknown_tile() -> None:
    # MUST NOT: count a cleared tile, an empty tile, a tile with no median, or an index the
    # lens does not store, whatever its median.
    codes, median = _every_code_grid()
    mask = population_mask(codes, median)
    assert not mask[0, 0, 0] and not mask[0, 0, 3]  # background, tile_empty
    assert not mask[0, 1, :].any()  # every code, NaN median
    assert not mask[1, 0, 0] and not mask[1, 0, 1]  # indices 4 and 255
    assert not mask[1, 0, 3] and not mask[1, 1, 3]  # undecided with a NaN median


def test_the_mask_is_the_decision_at_every_tile() -> None:
    # The one statement of the rule is `tile_population_code`; the mask must say what it says
    # at every tile, with a stored index outside the vocabulary handed a word the lens does not
    # say.
    codes, median = _every_code_grid()
    mask = population_mask(codes, median)
    for z in range(codes.shape[0]):
        for i in range(codes.shape[1]):
            for j in range(codes.shape[2]):
                index = int(codes[z, i, j])
                word = (
                    TILE_CODES[index] if index < len(TILE_CODES) else f"index_{index}"
                )
                counted = tile_population_code(word) == "counted"
                assert bool(mask[z, i, j]) == (
                    counted and bool(np.isfinite(median[z, i, j]))
                ), (
                    z,
                    i,
                    j,
                )


def test_the_mask_over_the_synthetic_lens_is_the_uncleared_finite_tiles() -> None:
    stack = _stack()
    lens = _lens(stack)
    mask = population_mask(lens.codes, stack.median)
    assert int(mask.sum()) == len(_kept_medians()) == SLICES * 16 - 1
    for z in range(SLICES):
        for i, row in enumerate(PATTERN):
            for j, kind in enumerate(row):
                expected = kind != CLEARED and bool(np.isfinite(stack.median[z, i, j]))
                assert bool(mask[z, i, j]) == expected, (z, i, j, kind)
    assert not mask[1, 2, 2]  # the empty tile


def test_an_empty_grid_is_an_empty_mask_and_never_an_error() -> None:
    mask = population_mask(
        np.empty((0, 0, 0), dtype=np.uint8), np.empty((0, 0, 0), dtype=np.float64)
    )
    assert mask.shape == (0, 0, 0) and mask.dtype == np.bool_


# --- the measurement: negative --------------------------------------------------------------


@pytest.mark.parametrize(
    ("codes", "median"),
    [
        (np.zeros((4, 4), dtype=np.uint8), np.zeros((4, 4))),
        (np.zeros((1, 2, 4, 4), dtype=np.uint8), np.zeros((1, 2, 4, 4))),
        (np.zeros((1, 4, 4), dtype=np.uint8), np.zeros((4, 4))),
    ],
)
def test_a_grid_that_is_not_slices_of_tiles_is_refused_by_name(
    codes: np.ndarray, median: np.ndarray
) -> None:
    with pytest.raises(ValueError, match="invalid_tile_grid"):
        population_mask(codes, median)


def test_grids_of_two_shapes_are_refused_by_name() -> None:
    with pytest.raises(ValueError, match="tile_grids_do_not_match"):
        population_mask(np.zeros((1, 4, 4), dtype=np.uint8), np.zeros((1, 4, 5)))


def test_codes_that_are_not_whole_numbers_are_refused_by_name() -> None:
    with pytest.raises(ValueError, match="invalid_tile_codes"):
        population_mask(np.zeros((1, 2, 2), dtype=np.float64), np.zeros((1, 2, 2)))


def test_the_measurement_writes_nothing_of_the_callers_and_freezes_its_own() -> None:
    codes, median = _every_code_grid()
    before = (codes.copy(), median.copy())
    mask = population_mask(codes, median)
    np.testing.assert_array_equal(codes, before[0])
    np.testing.assert_array_equal(median, before[1])
    assert codes.flags.writeable and median.flags.writeable
    assert not mask.flags.writeable


# --- the orchestration: positive ------------------------------------------------------------


def test_the_edges_come_from_the_kept_tiles_only() -> None:
    stack = _stack()
    digits = read_tile_digits(stack, _lens(stack), BAR)
    assert isinstance(digits, TileDigits)
    assert digits.code == "present"
    assert digits.series_uid == "series-tile-digits"
    kept = _kept_medians()
    low, high = (float(q) for q in np.quantile(np.array(kept), (1 / 3, 2 / 3)))
    assert (digits.low_edge, digits.high_edge) == (low, high)
    assert (
        digits.low_edge,
        digits.high_edge,
        digits.population_count,
    ) == tercile_edges(np.array(kept), BAR)
    # The cleared tiles are air at 0: had they entered the population, the lower third would
    # have moved down to 0 (60 air tiles against 47 kept).
    with_air = np.quantile(np.array(kept + [AIR] * (SLICES * 20)), 1 / 3)
    assert digits.low_edge != with_air
    assert digits.minimum_population == BAR


def test_the_population_count_equals_the_kept_tiles_with_a_finite_median() -> None:
    stack = _stack()
    digits = read_tile_digits(stack, _lens(stack), BAR)
    assert digits.population_count == len(_kept_medians()) == SLICES * 16 - 1
    assert digits.population_count == int(
        population_mask(_lens(stack).codes, stack.median).sum()
    )


def test_a_cleared_tile_reads_place_unread_stored_as_silence_and_never_a_digit() -> (
    None
):
    stack = _stack()
    lens = _lens(stack)
    digits = read_tile_digits(stack, lens, BAR)
    cleared = lens.codes == BACKGROUND
    assert cleared.any()
    assert set(digits.codes[cleared].tolist()) == {UNREAD}
    assert set(digits.digits[cleared].tolist()) == {SILENT}
    assert SILENT == 2 and SILENT != 0
    # The empty tile reads the same silence.
    assert lens.codes[1, 2, 2] == TILE_EMPTY
    assert digits.codes[1, 2, 2] == UNREAD and digits.digits[1, 2, 2] == SILENT


def test_every_kept_tile_reads_a_digit_and_the_map_is_the_scalar_oracle_at_every_tile() -> (
    None
):
    stack = _stack()
    lens = _lens(stack)
    digits = read_tile_digits(stack, lens, BAR)
    mask = population_mask(lens.codes, stack.median)
    assert set(digits.codes[mask].tolist()) <= {BELOW, AT, ABOVE}
    for z in range(SLICES):
        for i in range(TILES):
            for j in range(TILES):
                value = float(stack.median[z, i, j]) if mask[z, i, j] else float("nan")
                expected = digit_code(
                    value,
                    digits.low_edge,
                    digits.high_edge,
                    digits.population_count,
                    digits.minimum_population,
                )
                assert DIGIT_CODES[digits.codes[z, i, j]] == expected, (z, i, j)
    np.testing.assert_array_equal(digits.digits, DIGIT_VALUES[digits.codes])
    assert digits.codes.dtype == np.uint8 and digits.digits.dtype == np.int8
    assert digits.codes.shape == (SLICES, TILES, TILES)


def test_the_counts_are_one_per_digit_code_and_sum_to_every_tile() -> None:
    stack = _stack()
    digits = read_tile_digits(stack, _lens(stack), BAR)
    assert len(digits.counts) == len(DIGIT_CODES)
    assert sum(digits.counts) == digits.codes.size == SLICES * TILES * TILES
    for index, count in enumerate(digits.counts):
        assert count == int(np.count_nonzero(digits.codes == index))
    # The dark interior (D, median 0) is below both edges; the bright tiles (L, 100) above.
    assert digits.codes[0, 3, 3] == BELOW and digits.codes[0, 2, 2] == ABOVE
    assert digits.counts[UNREAD] == SLICES * 20 + 1
    assert "present" not in digits.why and str(digits.population_count) in digits.why


def test_a_lens_that_cleared_nothing_counts_every_finite_tile() -> None:
    stack = _stack()
    unavailable = _lens(stack, float("nan"))
    assert unavailable.code == "split_unavailable"
    digits = read_tile_digits(stack, unavailable, BAR)
    assert digits.code == "present"
    assert digits.population_count == SLICES * TILES * TILES - 1
    assert digits.counts[UNREAD] == 1


def test_the_ledger_carries_the_two_consumptions_then_the_production() -> None:
    # The stack and the lens are made BEFORE the block, so the ledger holds the digits' own
    # three events only.
    stack = _stack()
    lens = _lens(stack)
    with recording() as run_ledger:
        digits = read_tile_digits(stack, lens, BAR)
    events = run_ledger.events()
    assert [event.name for event in events] == [
        "squint_stack.consumed_by.tile_digits",
        "first_lens.consumed_by.tile_digits",
        "tile_digits.produced",
    ]
    assert dict(events[0].counts) == {"stack": 1}
    assert dict(events[1].counts) == {"lens": 1}
    assert dict(events[2].counts) == {
        "counted": digits.population_count,
        "read": sum(digits.counts[value] for value in (BELOW, AT, ABOVE)),
    }
    assert dict(events[2].counts)["read"] == digits.population_count


# --- the orchestration: negative ------------------------------------------------------------


def test_a_population_below_the_bar_leaves_every_tile_silent() -> None:
    # MUST NOT: read a digit against edges from fewer tiles than the bar. The edges are NaN
    # under the bar (`tercile_edges`), so the oracle names the series `no_edges` -- in
    # `digit_code` an absent pair outranks the count, so `population_too_small` is not what
    # this chain yields -- and every tile is silent, never 0.
    stack = _stack()
    lens = _lens(stack)
    with recording() as run_ledger:
        digits = read_tile_digits(stack, lens, SLICES * TILES * TILES + 1)
    assert digits.code == "no_edges"
    assert math.isnan(digits.low_edge) and math.isnan(digits.high_edge)
    assert digits.population_count == len(_kept_medians())
    assert digits.minimum_population == SLICES * TILES * TILES + 1
    assert set(digits.digits.ravel().tolist()) == {SILENT}
    assert set(digits.codes.ravel().tolist()) == {CODE_VALUES["no_edges"]}
    assert sum(digits.counts[value] for value in (BELOW, AT, ABOVE)) == 0
    assert "no_edges" in digits.why
    assert dict(run_ledger.events()[2].counts)["read"] == 0


def test_an_empty_population_gives_no_edges_and_every_tile_silent() -> None:
    # Every tile cleared: an all-dark stack is all background, so nothing is counted.
    stack = _stack(np.full((SLICES, 8, 8), AIR))
    lens = _lens(stack)
    assert set(lens.codes.ravel().tolist()) == {BACKGROUND}
    digits = read_tile_digits(stack, lens, BAR)
    assert digits.code == "no_edges"
    assert digits.population_count == 0
    assert set(digits.digits.ravel().tolist()) == {SILENT}


def test_an_absent_stack_is_the_named_absence_with_empty_arrays() -> None:
    absent = read_squint_stack(_series(None, "series-none"), TILE_MM)
    assert absent.code == "no_stacked_volume"
    lens = read_first_lens(absent, SPLIT)
    with recording() as run_ledger:
        digits = read_tile_digits(absent, lens, BAR)
    assert digits.code == "predecessor_absent"
    assert digits.series_uid == "series-none"
    assert "no_stacked_volume" in digits.why
    assert digits.codes.shape == (0, 0, 0) and digits.codes.dtype == np.uint8
    assert digits.digits.shape == (0, 0, 0) and digits.digits.dtype == np.int8
    assert math.isnan(digits.low_edge) and math.isnan(digits.high_edge)
    assert digits.population_count == 0 and digits.minimum_population == BAR
    assert digits.counts == (0,) * len(DIGIT_CODES)
    events = run_ledger.events()
    assert dict(events[0].counts) == {"stack": 0}
    assert dict(events[1].counts) == {"lens": 0}
    assert dict(events[2].counts) == {"counted": 0, "read": 0}


def test_an_absent_lens_is_the_named_absence_whatever_the_stack_holds() -> None:
    # MUST NOT: read a digit from a lens that named no tile, even over a present stack.
    stack = _stack()
    gone = read_squint_stack(replace(_series(_volume()), geometry=None), TILE_MM)
    lens = read_first_lens(gone, SPLIT)
    assert lens.code == "predecessor_absent"
    with recording() as run_ledger:
        digits = read_tile_digits(stack, lens, BAR)
    assert digits.code == "predecessor_absent"
    assert "first lens is predecessor_absent" in digits.why
    assert digits.codes.shape == (0, 0, 0)
    assert dict(run_ledger.events()[0].counts) == {"stack": 1}
    assert dict(run_ledger.events()[1].counts) == {"lens": 0}


def test_a_lens_over_another_grid_than_the_stack_is_refused_by_name() -> None:
    # MUST NOT: read a 3 x 3 lens over a 6 x 6 stack as if they were one series' records.
    stack = _stack()
    other = _lens(_stack(tile_mm=4.0))
    assert other.codes.shape != stack.median.shape
    with pytest.raises(ValueError, match="first_lens_does_not_match_stack"):
        read_tile_digits(stack, other, BAR)


@pytest.mark.parametrize("bar", [True, -1, 2.5, "eight", None])
def test_a_bar_that_is_not_a_whole_non_negative_number_is_refused_before_any_event(
    bar: object,
) -> None:
    stack = _stack()
    lens = _lens(stack)
    with (
        recording() as run_ledger,
        pytest.raises(ValueError, match="invalid_minimum_population"),
    ):
        read_tile_digits(stack, lens, bar)  # type: ignore[arg-type]
    assert run_ledger.events() == ()


def test_a_bar_of_zero_is_a_bar_and_reads() -> None:
    stack = _stack()
    digits = read_tile_digits(stack, _lens(stack), 0)
    assert digits.code == "present" and digits.minimum_population == 0


def test_nothing_of_the_callers_is_written_and_the_outputs_are_frozen() -> None:
    stack = _stack()
    lens = _lens(stack)
    before = (stack.median.copy(), lens.codes.copy())
    digits = read_tile_digits(stack, lens, BAR)
    np.testing.assert_array_equal(stack.median, before[0])
    np.testing.assert_array_equal(lens.codes, before[1])
    assert not digits.codes.flags.writeable and not digits.digits.flags.writeable
    silent = read_tile_digits(stack, lens, SLICES * TILES * TILES + 1)
    assert not silent.codes.flags.writeable and not silent.digits.flags.writeable


def test_every_code_is_in_its_vocabulary() -> None:
    stack = _stack()
    lens = _lens(stack)
    present = read_tile_digits(stack, lens, BAR)
    silent = read_tile_digits(stack, lens, SLICES * TILES * TILES + 1)
    absent = read_tile_digits(read_squint_stack(_series(None), TILE_MM), lens, BAR)
    for digits in (present, silent, absent):
        assert digits.code in TILE_DIGIT_CODES
        assert set(digits.codes.ravel().tolist()) <= set(range(len(DIGIT_CODES)))
        assert set(digits.digits.ravel().tolist()) <= {-1, 0, 1, SILENT}
        assert len(digits.counts) == len(DIGIT_CODES)
        assert sum(digits.counts) == digits.codes.size
    assert all(tile_population_code(word) in POPULATION_CODES for word in TILE_CODES)
