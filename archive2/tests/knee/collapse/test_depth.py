"""Intent tests for the depth collapse's measurements and orchestration (knee.collapse.depth),
both signs, written from the contract and the module docstring: Otsu's share is exact over the
sorted values (two well-separated clusters read above 0.9, a flat set and a lone value read NaN,
a small case agrees with the arithmetic by hand); the four readings per slice come from the tile
grids alone, NaN for every silence and never zero; over a synthetic stack, a first lens and a
hand-built conjunction, each lens stands where its reading peaks, the chosen slices are deduped
ascending, `above_below_share` is NaN without a conjunction, an absent stack or lens is
predecessor_absent, the conjunction is recorded as consumed only when handed over, the bar is
exactly a Python int (a bool or a NumPy integer is refused by name before any ledger event), and
the ledger carries the consumptions then the production. The CONTRACT's proof gate."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from knee.collapse.depth import (
    CHOICE_CODES,
    CONTRACT,
    DEPTH_CODES,
    LENSES,
    DepthCollapse,
    otsu_share,
    read_depth,
    slice_readings,
)
from knee.collapse.first_lens import TILE_CODES, FirstLens, read_first_lens
from knee.collapse.squint_stack import SquintStack, read_squint_stack
from knee.compute.contracts import handed_on
from knee.lenses.conjunction import CONJUNCTION_CODES, Conjunction
from knee.study.series import Series, SeriesGeometry
from knee.study.tables import SeriesRow
from knee.telemetry import recording

NAN = math.nan

#: An axial-like header at half a millimetre a pixel: a 2 mm tile is 4 px; the plane is 24 px
#: square, a 6 x 6 grid of tiles, six slices one millimetre apart.
AXIAL = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
NORMAL = np.array([0.0, 0.0, 1.0])
SPACING = (0.5, 0.5)
TILE_MM = 2.0
TILE_PX = 4
TILES = 6
AIR, BRIGHT, SPLIT = 0.0, 100.0, 10.0

NOWHERE = Path("/nonexistent/the-funnel/depth")
STUDY = "study-depth"
UID = "series-depth"
PARTNER_UID = "series-depth-partner"

#: One slice per pattern, tile by tile: B all dark (the air), L all bright, D all dark but
#: enclosed by bright tiles (a dark interior, kept), M half dark and half bright (a median of
#: 50). Each reading peaks at its own slice, by arithmetic:
#:   kept_share     peaks at slice 1 (only the four corners are air: 32 of 36 kept);
#:   dark_share     peaks at slice 2 (2 of 16 kept tiles at or below the split);
#:   split_quality  peaks at slices 3 and 5 alike (two-valued medians cut exactly: 1.0), an
#:                  exact tie whose middle is the lower, 3; slice 2's three-valued medians cut
#:                  at 0.571, slices 0, 1 and 4 are flat (NaN).
RING = ("BBBBBB", "BLLLLB", "BLLLLB", "BLLLLB", "BLLLLB", "BBBBBB")
CORNERS = ("BLLLLB", "LLLLLL", "LLLLLL", "LLLLLL", "LLLLLL", "BLLLLB")
MIXED = ("BBBBBB", "BMMMMB", "BMDLMB", "BMLDMB", "BMMMMB", "BBBBBB")
ONE_DARK = ("BBBBBB", "BLLLLB", "BLLDLB", "BLLLLB", "BLLLLB", "BBBBBB")
PATTERNS = (RING, CORNERS, MIXED, ONE_DARK, RING, ONE_DARK)
SLICES = len(PATTERNS)

#: The readings those patterns give, by hand (the split quality is worked below, where it is
#: asserted).
KEPT = (16 / 36, 32 / 36, 16 / 36, 16 / 36, 16 / 36, 16 / 36)
DARK = (0.0, 0.0, 2 / 16, 1 / 16, 0.0, 1 / 16)

READ = CONJUNCTION_CODES.index("at_at")
ABOVE_BELOW = CONJUNCTION_CODES.index("above_below")
UNMATCHED = CONJUNCTION_CODES.index("unmatched")
#: The hand-built conjunction: eight read tiles per slice, of which this many are above_below,
#: so `above_below_share` peaks at slice 2; slice 4 reads no pair at all (NaN).
ABOVE_BELOW_OF_EIGHT = (2, 4, 6, 1, None, 0)


# --- synthetic records ---------------------------------------------------------------------


def _plane(pattern: tuple[str, ...]) -> np.ndarray:
    plane = np.full((TILES * TILE_PX, TILES * TILE_PX), BRIGHT, dtype=np.float64)
    for i, row in enumerate(pattern):
        for j, kind in enumerate(row):
            r0, c0 = i * TILE_PX, j * TILE_PX
            if kind in "BD":
                plane[r0 : r0 + TILE_PX, c0 : c0 + TILE_PX] = AIR
            elif kind == "M":
                plane[r0 : r0 + TILE_PX // 2, c0 : c0 + TILE_PX] = AIR
    return plane


def _geometry(slices: int) -> SeriesGeometry:
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


def _series(volume: np.ndarray | None, uid: str = UID) -> Series:
    slices = SLICES if volume is None else int(volume.shape[0])
    return Series(
        row=SeriesRow(STUDY, uid, "1", "1", "Coronal"),
        directory=NOWHERE / uid,
        slices=(),
        stack=("stackable",) if volume is not None else ("no_stacked_volume",),
        volume=volume,
        geometry=_geometry(slices),
        slice_thickness_mm=(1.0,) * slices,
    )


def _stack(tile_mm: float = TILE_MM) -> SquintStack:
    return read_squint_stack(_series(np.stack([_plane(p) for p in PATTERNS])), tile_mm)


def _lens(stack: SquintStack, split: float = SPLIT) -> FirstLens:
    return read_first_lens(stack, split)


def _conjunction(stack: SquintStack, code: str = "present") -> Conjunction:
    """A conjunction on the stack's grid, built by hand: every tile `unmatched` but eight tiles
    of each slice (flat tile indices 6 to 13), which read `at_at` or `above_below` as
    `ABOVE_BELOW_OF_EIGHT` says; slice 4 reads no pair."""
    if code != "present":
        return Conjunction(
            UID,
            PARTNER_UID,
            code,
            "a predecessor of the conjunction was absent",
            handed_on(np.empty((0, 0, 0), dtype=np.uint8)),
            (0,) * len(CONJUNCTION_CODES),
        )
    codes = np.full(stack.median.shape, UNMATCHED, dtype=np.uint8)
    for z, marked in enumerate(ABOVE_BELOW_OF_EIGHT):
        if marked is None:
            continue
        row = np.full(8, READ, dtype=np.uint8)
        row[:marked] = ABOVE_BELOW
        codes[z].reshape(-1)[6:14] = row
    counts = tuple(
        int(np.count_nonzero(codes == index)) for index in range(len(CONJUNCTION_CODES))
    )
    return Conjunction(
        UID, PARTNER_UID, "present", "built by hand", handed_on(codes), counts
    )


def _above_below_expected() -> list[float]:
    return [NAN if marked is None else marked / 8 for marked in ABOVE_BELOW_OF_EIGHT]


def _grids(
    slices: int = 2, down: int = 2, across: int = 3
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    median = np.full((slices, down, across), 100.0)
    finite = np.ones((slices, down, across), dtype=bool)
    kept = np.ones((slices, down, across), dtype=bool)
    return median, finite, kept


# --- otsu_share: positive ------------------------------------------------------------------


def test_two_well_separated_clusters_read_above_nine_tenths() -> None:
    values = np.array([0.0, 1.0, 2.0, 1.0, 100.0, 101.0, 99.0, 100.0])
    share = otsu_share(values)
    assert share > 0.9
    assert 0.0 <= share <= 1.0


def test_a_two_valued_set_cuts_exactly_and_reads_one() -> None:
    # Each class constant: the between-class variance is the whole variance. [0, 0, 10, 10]:
    # mean 5, variance 25; the cut after the two zeros weighs 1/2 by 1/2 times 100 = 25.
    assert otsu_share(np.array([0.0, 0.0, 10.0, 10.0])) == 1.0
    assert otsu_share(np.array([10.0, 0.0, 10.0, 0.0])) == 1.0


def test_the_share_agrees_with_the_arithmetic_by_hand() -> None:
    # [1, 2, 4]: mean 7/3, population variance 14/9. Cut after one value: weights 1/3 and 2/3,
    # means 1 and 3, between 8/9. Cut after two: weights 2/3 and 1/3, means 3/2 and 4,
    # between (2/9) * 25/4 = 25/18. The share is (25/18) / (14/9) = 25/28.
    assert otsu_share(np.array([1.0, 2.0, 4.0])) == pytest.approx(25 / 28, abs=1e-12)
    # Order is immaterial: the values are sorted first.
    assert otsu_share(np.array([4.0, 1.0, 2.0])) == pytest.approx(25 / 28, abs=1e-12)


def test_the_share_is_read_over_the_finite_values_only() -> None:
    with_nan = np.array([1.0, NAN, 2.0, np.inf, 4.0, -np.inf])
    assert otsu_share(with_nan) == pytest.approx(25 / 28, abs=1e-12)


def test_the_share_reads_a_grid_as_its_values() -> None:
    assert otsu_share(np.array([[1.0, 2.0], [4.0, NAN]])) == pytest.approx(
        25 / 28, abs=1e-12
    )


# --- otsu_share: negative ------------------------------------------------------------------


def test_a_flat_set_a_lone_value_and_nothing_read_nan_never_zero() -> None:
    # MUST NOT: read a share of zero where there is no split to read.
    assert math.isnan(otsu_share(np.array([5.0, 5.0, 5.0, 5.0])))
    assert math.isnan(otsu_share(np.array([7.0])))
    assert math.isnan(otsu_share(np.array([])))
    assert math.isnan(otsu_share(np.array([NAN, NAN])))
    assert math.isnan(otsu_share(np.array([3.0, NAN])))


def test_the_share_writes_nothing_of_the_callers_values() -> None:
    values = np.array([9.0, 1.0, 5.0, 1.0])
    before = values.copy()
    otsu_share(values)
    np.testing.assert_array_equal(values, before)
    assert values.flags.writeable


# --- slice_readings: positive --------------------------------------------------------------


def test_kept_tiles_all_above_the_split_read_dark_share_zero_and_all_at_or_below_one() -> (
    None
):
    median, finite, kept = _grids(slices=2)
    median[1] = SPLIT  # at the split counts as dark
    readings = slice_readings(median, finite, kept, SPLIT, None, None)
    kept_share, dark_share, split_quality, above_below_share = readings
    np.testing.assert_array_equal(kept_share, [1.0, 1.0])
    np.testing.assert_array_equal(dark_share, [0.0, 1.0])
    assert all(math.isnan(value) for value in split_quality)
    assert all(math.isnan(value) for value in above_below_share)


def test_two_well_separated_clusters_read_a_split_quality_above_nine_tenths() -> None:
    median, finite, kept = _grids(slices=2, down=2, across=4)
    median[0, 0] = (0.0, 1.0, 2.0, 1.0)
    median[0, 1] = (100.0, 101.0, 99.0, 100.0)
    readings = slice_readings(median, finite, kept, SPLIT, None, None)
    assert readings[2][0] > 0.9
    # One flat value over the kept tiles is no split: NaN.
    assert math.isnan(readings[2][1])


def test_the_kept_share_is_kept_over_finite_and_the_dark_share_over_kept() -> None:
    median, finite, kept = _grids(slices=1, down=2, across=3)
    kept[0, 0] = (True, True, False)
    kept[0, 1] = (True, False, False)
    median[0, 0] = (0.0, 5.0, 100.0)
    median[0, 1] = (100.0, 0.0, 0.0)
    readings = slice_readings(median, finite, kept, SPLIT, None, None)
    assert readings[0][0] == pytest.approx(3 / 6)
    assert readings[1][0] == pytest.approx(2 / 3)
    # The cleared tiles' medians never enter the cut: the kept ones are {0, 5, 100}.
    assert readings[2][0] == pytest.approx(
        otsu_share(np.array([0.0, 5.0, 100.0])), abs=1e-12
    )


def test_the_above_below_share_is_the_above_below_tiles_over_the_read_pairs() -> None:
    median, finite, kept = _grids(slices=2, down=2, across=4)
    readable = np.zeros(median.shape, dtype=bool)
    above_below = np.zeros(median.shape, dtype=bool)
    readable[0, 0] = True  # four read tiles
    above_below[0, 0, :3] = True  # three of them above_below
    readings = slice_readings(median, finite, kept, SPLIT, readable, above_below)
    assert readings[3][0] == pytest.approx(0.75)
    # A slice where no tile read a pair is NaN, never zero.
    assert math.isnan(readings[3][1])


def test_every_reading_is_frozen_float64_of_one_value_per_slice() -> None:
    median, finite, kept = _grids(slices=3)
    for reading in slice_readings(median, finite, kept, SPLIT, None, None):
        assert reading.shape == (3,) and reading.dtype == np.float64
        assert not reading.flags.writeable


def test_the_measurement_carries_the_modules_contract() -> None:
    assert slice_readings.__dict__["__contract__"] is CONTRACT
    assert CONTRACT.reference == "slice_readings"
    assert "test_depth.py" in CONTRACT.proof_gate


# --- slice_readings: negative --------------------------------------------------------------


def test_a_slice_with_no_finite_tile_reads_nan_in_every_reading() -> None:
    # MUST NOT: read any share of a slice that holds no finite pixel.
    median, finite, kept = _grids(slices=2)
    median[1] = NAN
    finite[1] = False
    kept[1] = False
    readable = np.zeros(median.shape, dtype=bool)
    readings = slice_readings(median, finite, kept, SPLIT, readable, readable)
    for reading in readings:
        assert math.isnan(reading[1])
    # And the other slice still reads.
    assert readings[0][0] == 1.0


def test_an_empty_stack_reads_empty_readings_and_never_an_error() -> None:
    empty = np.empty((0, 0, 0))
    readings = slice_readings(
        empty, empty.astype(bool), empty.astype(bool), SPLIT, None, None
    )
    assert all(reading.shape == (0,) for reading in readings)


def test_a_split_that_is_not_a_number_silences_the_dark_share_only() -> None:
    # MUST NOT: read a dark share against no valley, nor turn that silence into zero.
    median, finite, kept = _grids(slices=2)
    median[0, 0, 0] = 0.0
    for split in (NAN, np.inf, None, "10", True):
        readings = slice_readings(median, finite, kept, split, None, None)  # type: ignore[arg-type]
        assert all(math.isnan(value) for value in readings[1])
        np.testing.assert_array_equal(readings[0], [1.0, 1.0])


def test_grids_that_do_not_agree_are_refused_by_name() -> None:
    median, finite, kept = _grids(slices=2)
    with pytest.raises(ValueError, match="invalid_readings_input"):
        slice_readings(median[0], finite[0], kept[0], SPLIT, None, None)
    with pytest.raises(ValueError, match="invalid_readings_input"):
        slice_readings(median, finite[:1], kept, SPLIT, None, None)
    with pytest.raises(ValueError, match="invalid_readings_input"):
        slice_readings(median, finite, kept[:, :1], SPLIT, None, None)
    readable = np.zeros(median.shape, dtype=bool)
    with pytest.raises(ValueError, match="invalid_readings_input"):
        slice_readings(median, finite, kept, SPLIT, readable[:1], readable)
    with pytest.raises(ValueError, match="invalid_readings_input"):
        slice_readings(median, finite, kept, SPLIT, readable, readable[:, :, :1])
    # One of the pair handed over without the other is no conjunction at all: refused.
    with pytest.raises(ValueError, match="invalid_readings_input"):
        slice_readings(median, finite, kept, SPLIT, readable, None)
    with pytest.raises(ValueError, match="invalid_readings_input"):
        slice_readings(median, finite, kept, SPLIT, None, readable)


def test_the_measurement_writes_nothing_of_the_callers_grids() -> None:
    median, finite, kept = _grids(slices=2)
    median[0, 0, 0] = 0.0
    readable = np.ones(median.shape, dtype=bool)
    above_below = np.zeros(median.shape, dtype=bool)
    before = (
        median.copy(),
        finite.copy(),
        kept.copy(),
        readable.copy(),
        above_below.copy(),
    )
    slice_readings(median, finite, kept, SPLIT, readable, above_below)
    for array, kept_copy in zip(
        (median, finite, kept, readable, above_below), before, strict=True
    ):
        np.testing.assert_array_equal(array, kept_copy)
        assert array.flags.writeable


# --- read_depth: positive ------------------------------------------------------------------


def test_each_lens_stands_where_its_reading_peaks_and_the_slices_are_deduped() -> None:
    stack = _stack()
    collapse = read_depth(stack, _lens(stack), _conjunction(stack), SPLIT, 2)
    assert isinstance(collapse, DepthCollapse)
    assert collapse.series_uid == UID
    assert collapse.code == "present" and collapse.minimum_valid == 2
    np.testing.assert_allclose(collapse.kept_share, KEPT)
    np.testing.assert_allclose(collapse.dark_share, DARK)
    # The three-valued slice, by hand: medians {50 x 12, 0 x 2, 100 x 2}, mean 50, variance
    # 625; the best cut sets the two zeros apart, weights 1/8 and 7/8, means 0 and 400/7,
    # between (7/64) * (400/7)^2 = 2500/7; share (2500/7) / 625 = 4/7.
    expected_quality = [NAN, NAN, 4 / 7, 1.0, NAN, 1.0]
    np.testing.assert_allclose(collapse.split_quality, expected_quality)
    np.testing.assert_allclose(collapse.above_below_share, _above_below_expected())
    assert collapse.chosen_index == (1, 2, 3, 2)
    assert collapse.choice_codes == ("chosen", "chosen", "tie_middle", "chosen")
    np.testing.assert_array_equal(collapse.chosen_slices, [1, 2, 3])
    assert collapse.chosen_slices.dtype == np.int64
    assert "kept_share at 1 (chosen)" in collapse.why
    assert "split_quality at 3 (tie_middle)" in collapse.why
    assert "3 distinct slices chosen" in collapse.why


def test_without_a_conjunction_the_above_below_share_is_silent_and_the_lens_stands_nowhere() -> (
    None
):
    stack = _stack()
    lens = _lens(stack)
    with recording() as run_ledger:
        collapse = read_depth(stack, lens, None, SPLIT, 2)
    assert all(math.isnan(value) for value in collapse.above_below_share)
    assert collapse.chosen_index == (1, 2, 3, -1)
    assert collapse.choice_codes == ("chosen", "chosen", "tie_middle", "all_silent")
    np.testing.assert_array_equal(collapse.chosen_slices, [1, 2, 3])
    assert "no conjunction read" in collapse.why
    # MUST NOT: record a read of a conjunction that was never handed over.
    names = [event.name for event in run_ledger.events()]
    assert names == [
        "squint_stack.consumed_by.depth",
        "first_lens.consumed_by.depth",
        "depth.produced",
    ]


def test_the_ledger_carries_the_consumptions_then_the_production() -> None:
    stack = _stack()
    lens, conjunction = _lens(stack), _conjunction(stack)
    with recording() as run_ledger:
        collapse = read_depth(stack, lens, conjunction, SPLIT, 2)
    events = run_ledger.events()
    assert [event.name for event in events] == [
        "squint_stack.consumed_by.depth",
        "first_lens.consumed_by.depth",
        "conjunction.consumed_by.depth",
        "depth.produced",
    ]
    assert dict(events[0].counts) == {"stack": 1}
    assert dict(events[1].counts) == {"lens": 1}
    assert dict(events[2].counts) == {"conjunction": 1}
    assert dict(events[3].counts) == {"chosen": 3, "standing": 4}
    assert dict(events[3].counts)["chosen"] == int(collapse.chosen_slices.shape[0])


def test_a_bar_counts_finite_readings_and_abstains_by_name() -> None:
    stack = _stack()
    collapse = read_depth(stack, _lens(stack), _conjunction(stack), SPLIT, 3)
    # split_quality holds three finite readings and stands; under a bar of four it may not.
    assert collapse.choice_codes[2] == "tie_middle"
    higher = read_depth(stack, _lens(stack), _conjunction(stack), SPLIT, 4)
    assert higher.chosen_index[2] == -1 and higher.choice_codes[2] == "too_few_valid"
    assert higher.chosen_index[:2] == (1, 2)
    np.testing.assert_array_equal(higher.chosen_slices, [1, 2])
    assert higher.minimum_valid == 4


def test_a_conjunction_handed_over_but_not_made_is_consumed_and_reads_nothing() -> None:
    stack = _stack()
    lens, unmade = _lens(stack), _conjunction(stack, "predecessor_absent")
    with recording() as run_ledger:
        collapse = read_depth(stack, lens, unmade, SPLIT, 2)
    assert collapse.code == "present"
    assert all(math.isnan(value) for value in collapse.above_below_share)
    assert collapse.choice_codes[3] == "all_silent"
    events = run_ledger.events()
    assert events[2].name == "conjunction.consumed_by.depth"
    assert dict(events[2].counts) == {"conjunction": 0}


def test_every_array_is_frozen_and_nothing_of_the_callers_is_written() -> None:
    stack = _stack()
    lens = _lens(stack)
    conjunction = _conjunction(stack)
    before = (stack.median.copy(), stack.coverage.copy(), lens.codes.copy())
    collapse = read_depth(stack, lens, conjunction, SPLIT, 2)
    np.testing.assert_array_equal(stack.median, before[0])
    np.testing.assert_array_equal(stack.coverage, before[1])
    np.testing.assert_array_equal(lens.codes, before[2])
    for name in (*LENSES, "chosen_slices"):
        assert not getattr(collapse, name).flags.writeable


def test_every_code_is_in_its_vocabulary() -> None:
    stack = _stack()
    for conjunction in (None, _conjunction(stack)):
        collapse = read_depth(stack, _lens(stack), conjunction, SPLIT, 2)
        assert collapse.code in DEPTH_CODES
        assert all(code in CHOICE_CODES for code in collapse.choice_codes)
        assert len(collapse.chosen_index) == len(LENSES) == 4
        for index, code in zip(
            collapse.chosen_index, collapse.choice_codes, strict=True
        ):
            assert (index == -1) == (code not in ("chosen", "tie_middle"))


# --- read_depth: negative ------------------------------------------------------------------


def test_an_absent_stack_is_the_named_absence_with_empty_readings() -> None:
    gone = read_squint_stack(_series(None), TILE_MM)
    assert gone.code == "no_stacked_volume"
    lens = read_first_lens(gone, SPLIT)
    with recording() as run_ledger:
        collapse = read_depth(gone, lens, None, SPLIT, 2)
    assert collapse.code == "predecessor_absent"
    assert "squint stack is no_stacked_volume" in collapse.why
    for name in LENSES:
        reading = getattr(collapse, name)
        assert reading.shape == (0,) and reading.dtype == np.float64
        assert not reading.flags.writeable
    assert collapse.chosen_index == (-1, -1, -1, -1)
    assert collapse.choice_codes == ("all_silent",) * 4
    assert collapse.chosen_slices.shape == (0,)
    assert collapse.chosen_slices.dtype == np.int64
    assert collapse.minimum_valid == 2
    events = run_ledger.events()
    assert dict(events[0].counts) == {"stack": 0}
    assert dict(events[1].counts) == {"lens": 0}
    assert dict(events[2].counts) == {"chosen": 0, "standing": 0}


def test_an_absent_lens_is_the_named_absence_whatever_the_stack_holds() -> None:
    stack = _stack()
    gone = read_first_lens(read_squint_stack(_series(None), TILE_MM), SPLIT)
    assert gone.code == "predecessor_absent"
    with recording() as run_ledger:
        collapse = read_depth(stack, gone, _conjunction(stack), SPLIT, 2)
    assert collapse.code == "predecessor_absent"
    assert "first lens is predecessor_absent" in collapse.why
    assert collapse.kept_share.shape == (0,) and collapse.chosen_slices.shape == (0,)
    events = run_ledger.events()
    assert dict(events[0].counts) == {"stack": 1}
    assert dict(events[1].counts) == {"lens": 0}
    assert dict(events[2].counts) == {"conjunction": 1}


def test_a_lens_that_could_not_read_its_split_still_reads_and_clears_nothing() -> None:
    # `split_unavailable` is a lens that named every tile not_background: not an absence.
    stack = _stack()
    lens = read_first_lens(stack, NAN)
    assert lens.code == "split_unavailable"
    collapse = read_depth(stack, lens, None, NAN, 2)
    assert collapse.code == "present"
    np.testing.assert_allclose(collapse.kept_share, [1.0] * SLICES)
    # No valley: the dark share is silent, never zero, and its lens stands nowhere.
    assert all(math.isnan(value) for value in collapse.dark_share)
    assert collapse.choice_codes[1] == "all_silent"


def test_a_bar_that_is_not_a_count_is_refused_before_any_event() -> None:
    stack = _stack()
    lens = _lens(stack)
    # A NumPy whole number is not a bar either: the bar is exactly a Python int.
    for bar in (-1, True, 2.0, None, "2", np.int64(2)):
        with (
            recording() as run_ledger,
            pytest.raises(ValueError, match="invalid_minimum_valid"),
        ):
            read_depth(stack, lens, None, SPLIT, bar)  # type: ignore[arg-type]
        assert run_ledger.events() == ()


def test_a_split_that_is_not_a_number_is_no_valley() -> None:
    stack = _stack()
    lens = _lens(stack)
    for split in (None, "10", True):
        collapse = read_depth(stack, lens, None, split, 2)  # type: ignore[arg-type]
        assert all(math.isnan(value) for value in collapse.dark_share)
        assert collapse.choice_codes[1] == "all_silent"
        np.testing.assert_allclose(collapse.kept_share, KEPT)


def test_records_over_another_grid_than_the_stack_are_refused_by_name() -> None:
    stack = _stack()
    coarse = _stack(tile_mm=4.0)
    assert coarse.median.shape != stack.median.shape
    with pytest.raises(ValueError, match="first_lens_does_not_match_stack"):
        read_depth(stack, _lens(coarse), None, SPLIT, 2)
    over_coarse = Conjunction(
        UID,
        PARTNER_UID,
        "present",
        "over the coarse grid",
        handed_on(np.full(coarse.median.shape, UNMATCHED, dtype=np.uint8)),
        (0,) * len(CONJUNCTION_CODES),
    )
    with pytest.raises(ValueError, match="conjunction_does_not_match_stack"):
        read_depth(stack, _lens(stack), over_coarse, SPLIT, 2)


def test_the_kept_tiles_are_the_lens_words_and_never_the_cleared_ones() -> None:
    # The kept share counts not_background and undecided only: a stack whose lens cleared
    # every tile but one reads the one.
    stack = _stack()
    lens = _lens(stack)
    cleared = np.full(lens.codes.shape, TILE_CODES.index("background"), dtype=np.uint8)
    cleared[:, 2, 2] = TILE_CODES.index("undecided")
    one_kept = FirstLens(
        UID, "present", "by hand", SPLIT, "first-lens-v1", cleared, (0, 0, 0, 0)
    )
    collapse = read_depth(stack, one_kept, None, SPLIT, 1)
    np.testing.assert_allclose(collapse.kept_share, [1 / 36] * SLICES)
    # One kept median is no split to read: silent, never zero.
    assert all(math.isnan(value) for value in collapse.split_quality)
    assert collapse.choice_codes[2] == "all_silent"
