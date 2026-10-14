"""Intent tests for the tile dome's orchestration (knee.objects.tile_dome.read_tile_domes), both
signs, over hand-drawn tile grids, with the picture adapter and the drawer that arrange it.

The rule under test, from the module's docstring: an obstacle is a tile the first lens cleared, a
tile dark on both acquisitions (paired plane, under the `dark_on_both` border), or a tile whose median is at or below the split
(solitary plane); the buffer the lens left undecided is kept and eligible like any kept tile; the
height is the distance in millimetres (`stack.tile_mm` a tile) to the nearest obstacle or the
frame; the peaks and territories are the shared `dome` measurement's; only the chosen slices are
read; a missing predecessor is one named `predecessor_absent` dome; the ledger names each record
read and the dome produced. The vectorised map is checked against the scalar `dome_tile_code`
tile by tile.
"""

from __future__ import annotations

import importlib
import json
import shutil
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from knee.collapse.depth import DepthCollapse
from knee.collapse.first_lens import RULE_VERSION, TILE_CODES, FirstLens
from knee.collapse.squint_stack import SquintStack
from knee.lenses.conjunction import CONJUNCTION_CODES, Conjunction
from knee.objects.tile_dome import (
    DOME_CODES,
    DOME_TILE_CODES,
    TileDome,
    dome_tile_code,
    read_tile_domes,
)
from knee.pictures import tile_dome as pictures
from knee.pictures.tile_dome import DOME_STANDINGS, dome_panels, dome_standing
from knee.telemetry import recording
from workbench.measure.object_analysis import array_table, squint_stack_record
from workbench.render import tile_dome_frames
from workbench.render._out import PROJECT, ArgumentRefusal

UID = "series-tile-dome"
TILE_PX = 4
TILE_MM = 2.0
SPLIT = 10.0
DARK, BRIGHT = 0.0, 100.0
BAR = 4.0
#: The two readings of a paired plane's border (`knee.objects.tile_dome.BORDER_CODES`). Every dome
#: here is read under the first, which is the rule the module docstring above states; the second is
#: the border a record may hold no dome of.
BORDER, OTHER_BORDER = "dark_on_both", "edge_of_bright_partner"

TILE = {name: TILE_CODES.index(name) for name in TILE_CODES}
PAIR = {name: CONJUNCTION_CODES.index(name) for name in CONJUNCTION_CODES}

#: One letter a tile: (the first lens's word, the conjunction's word, the median). The wall is
#: dark on both acquisitions AND dark by its median, so both planes see it. The D tile is dark by
#: its median only (the pair does not read it dark on both): a solitary plane's obstacle and a
#: paired plane's interior. The B tile's pair word is not consulted: cleared air is an obstacle.
LEGEND: dict[str, tuple[str, str, float]] = {
    "B": ("background", "above_below", BRIGHT),
    "U": ("undecided", "at_at", BRIGHT),
    "N": ("not_background", "above_below", BRIGHT),
    "W": ("not_background", "below_below", DARK),
    "D": ("not_background", "at_at", DARK),
    "E": ("tile_empty", "unmatched", float("nan")),
}

#: Two blocks of kept tiles, each five tiles square, parted by one wall column, inside a ring of
#: cleared air; the block's outer column is the undecided buffer. Each block's centre is three
#: tiles from the nearest obstacle, so six millimetres at a two millimetre tile.
PATTERN = (
    "BBBBBBBBBBBBB",
    "BUNNNNWNNNNUB",
    "BUNNNNWNNNNUB",
    "BUNNNNWNNNNUB",
    "BUNNNNWNNNNUB",
    "BUNNNNWNNNNUB",
    "BBBBBBBBBBBBB",
)
WITH_A_DARK_TILE = tuple(
    row[:2] + "D" + row[3:] if i == 3 else row for i, row in enumerate(PATTERN)
)
WITH_AN_EMPTY_TILE = tuple(
    row[:9] + "E" + row[10:] if i == 2 else row for i, row in enumerate(PATTERN)
)
NOTHING_KEPT = tuple("B" * 13 for _ in range(7))


# --- the inputs, built by hand; nothing here calls the function under test ------------------------


def _grids(pattern: tuple[str, ...]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    median = np.array(
        [[LEGEND[tile][2] for tile in row] for row in pattern], dtype=np.float64
    )
    first = np.array(
        [[TILE[LEGEND[tile][0]] for tile in row] for row in pattern], dtype=np.uint8
    )
    pair = np.array(
        [[PAIR[LEGEND[tile][1]] for tile in row] for row in pattern], dtype=np.uint8
    )
    return median, first, pair


def _where(pattern: tuple[str, ...], letters: str) -> np.ndarray:
    return np.array([[tile in letters for tile in row] for row in pattern], dtype=bool)


def _bounds(down: int, across: int) -> np.ndarray:
    """The native half-open bounds of a grid of four-pixel tiles: r0, r1, c0, c1, int64."""
    r0 = np.repeat(np.arange(down)[:, None] * TILE_PX, across, axis=1)
    c0 = np.repeat(np.arange(across)[None, :] * TILE_PX, down, axis=0)
    return np.stack([r0, r0 + TILE_PX, c0, c0 + TILE_PX], axis=-1).astype(np.int64)


def _stack(median: np.ndarray, tile_mm: float = TILE_MM) -> SquintStack:
    slices, down, across = median.shape
    return SquintStack(
        series_uid=UID,
        code="present",
        why="synthetic",
        tile_mm=tile_mm,
        tile_shape_rc=(TILE_PX, TILE_PX),
        bounds_rc=_bounds(down, across),
        median=median,
        minimum=median,
        maximum=median,
        coverage=np.where(np.isfinite(median), 1.0, 0.0),
        centres_lps=np.zeros((slices, down, across, 3)),
    )


def _absent_stack(code: str = "no_stacked_volume") -> SquintStack:
    return SquintStack(
        series_uid=UID,
        code=code,
        why="synthetic silence",
        tile_mm=TILE_MM,
        tile_shape_rc=(0, 0),
        bounds_rc=np.empty((0, 0, 4), dtype=np.int64),
        median=np.empty((0, 0, 0)),
        minimum=np.empty((0, 0, 0)),
        maximum=np.empty((0, 0, 0)),
        coverage=np.empty((0, 0, 0)),
        centres_lps=np.empty((0, 0, 0, 3)),
    )


def _lens(codes: np.ndarray, code: str = "present") -> FirstLens:
    background, kept, undecided, empty = (
        int(np.count_nonzero(codes == i)) for i in range(len(TILE_CODES))
    )
    counts = (background, kept, undecided, empty)
    return FirstLens(UID, code, "synthetic", SPLIT, RULE_VERSION, codes, counts)


def _absent_lens() -> FirstLens:
    return _lens(np.empty((0, 0, 0), dtype=np.uint8), "predecessor_absent")


def _pair(codes: np.ndarray, code: str = "present") -> Conjunction:
    counts = tuple(
        int(np.count_nonzero(codes == i)) for i in range(len(CONJUNCTION_CODES))
    )
    return Conjunction(UID, "partner", code, "synthetic", codes, counts)


def _depth(chosen: list[int], code: str = "present") -> DepthCollapse:
    nothing = np.empty(0)
    return DepthCollapse(
        series_uid=UID,
        code=code,
        why="synthetic",
        minimum_valid=8,
        kept_share=nothing,
        dark_share=nothing,
        split_quality=nothing,
        above_below_share=nothing,
        chosen_index=(-1, -1, -1, -1),
        choice_codes=("all_silent", "all_silent", "all_silent", "all_silent"),
        chosen_slices=np.asarray(chosen, dtype=np.int64),
    )


def _records(pattern: tuple[str, ...], slices: int = 3):
    """The stack, first lens and conjunction of a series whose every slice is `pattern`."""
    median, first, pair = _grids(pattern)
    return (
        _stack(np.stack([median] * slices)),
        _lens(np.stack([first] * slices)),
        _pair(np.stack([pair] * slices)),
    )


# --- the orchestration: positive -------------------------------------------------------------------


def test_a_paired_slice_is_cleared_air_and_a_wall_around_two_interiors_with_two_peaks() -> (
    None
):
    stack, lens, pair = _records(PATTERN)
    (dome,) = read_tile_domes(stack, lens, pair, _depth([1]), SPLIT, BAR, BORDER)
    assert isinstance(dome, TileDome)
    assert dome.code == "present" and dome.series_uid == UID
    assert dome.slice_index == 1 and dome.prominence_mm == BAR
    np.testing.assert_array_equal(dome.cleared, _where(PATTERN, "B"))
    np.testing.assert_array_equal(dome.obstacle, _where(PATTERN, "BW"))
    np.testing.assert_array_equal(dome.interior, _where(PATTERN, "UN"))
    # Each block's centre is three tiles from its nearest obstacle, two millimetres a tile.
    assert dome.peaks.tolist() == [[3, 3], [3, 9]]
    np.testing.assert_allclose(dome.peak_height_mm, [6.0, 6.0])
    assert dome.height[3, 3] == pytest.approx(6.0)
    assert dome.height[3, 9] == pytest.approx(6.0)
    # Two territories, one each side of the wall; nothing of the wall or the air is labelled.
    assert np.unique(dome.labels).tolist() == [0, 1, 2]
    assert np.all(dome.labels[1:6, 1:6] == 1) and np.all(dome.labels[1:6, 7:12] == 2)
    assert not dome.labels[~dome.interior].any()
    assert np.all(dome.height[~dome.interior] == 0.0)


def test_the_buffer_the_lens_left_undecided_is_interior_and_holds_a_territory() -> None:
    # The founder keeps the buffer in play: it is eligible like any kept tile.
    stack, lens, pair = _records(PATTERN)
    buffer = _where(PATTERN, "U")
    assert np.all(lens.codes[0][buffer] == TILE["undecided"])
    (dome,) = read_tile_domes(stack, lens, pair, _depth([0]), SPLIT, BAR, BORDER)
    assert np.all(dome.interior[buffer])
    assert not dome.obstacle[buffer].any()
    assert np.all(dome.labels[1:6, 1] == 1) and np.all(dome.labels[1:6, 11] == 2)


def test_a_solitary_slice_takes_its_obstacles_from_the_split() -> None:
    stack, lens, _ = _records(PATTERN)
    (dome,) = read_tile_domes(stack, lens, None, _depth([2]), SPLIT, BAR, BORDER)
    # The wall is dark by its median as well, so a solitary plane sees the same wall.
    np.testing.assert_array_equal(dome.obstacle, _where(PATTERN, "BW"))
    assert dome.peaks.tolist() == [[3, 3], [3, 9]]
    assert dome.code == "present"


def test_the_split_is_consulted_only_on_a_solitary_plane() -> None:
    stack, lens, pair = _records(WITH_A_DARK_TILE)
    (paired,) = read_tile_domes(stack, lens, pair, _depth([1]), SPLIT, BAR, BORDER)
    (alone,) = read_tile_domes(stack, lens, None, _depth([1]), SPLIT, BAR, BORDER)
    # Dark by median, but not dark on both: a paired plane's interior, a solitary plane's obstacle.
    assert paired.interior[3, 2] and not paired.obstacle[3, 2]
    assert paired.labels[3, 2] != 0
    assert alone.obstacle[3, 2] and not alone.interior[3, 2]
    assert alone.labels[3, 2] == 0
    assert not np.array_equal(paired.height, alone.height)


def test_only_the_chosen_slices_are_read_and_in_the_order_the_depth_names_them() -> (
    None
):
    median, first, pair = _grids(PATTERN)
    kept_median, kept_first, kept_pair = _grids(NOTHING_KEPT)
    stack = _stack(np.stack([kept_median, median, kept_median, median, kept_median]))
    lens = _lens(np.stack([kept_first, first, kept_first, first, kept_first]))
    conj = _pair(np.stack([kept_pair, pair, kept_pair, pair, kept_pair]))
    domes = read_tile_domes(stack, lens, conj, _depth([3, 1]), SPLIT, BAR, BORDER)
    assert [dome.slice_index for dome in domes] == [3, 1]
    assert [dome.code for dome in domes] == ["present", "present"]
    assert all(len(dome.peaks) == 2 for dome in domes)
    # Slice 0, 2 and 4 hold nothing but air: had one been read it would be `no_interior`.
    only_air = read_tile_domes(stack, lens, conj, _depth([0]), SPLIT, BAR, BORDER)
    assert [dome.code for dome in only_air] == ["no_interior"]


def test_a_slice_with_nothing_kept_is_no_interior_with_no_peak_and_zero_labels() -> (
    None
):
    stack, lens, pair = _records(NOTHING_KEPT)
    (dome,) = read_tile_domes(stack, lens, pair, _depth([0]), SPLIT, BAR, BORDER)
    assert dome.code == "no_interior"
    assert dome.peaks.shape == (0, 2) and dome.peak_height_mm.shape == (0,)
    assert dome.labels.shape == (7, 13) and not dome.labels.any()
    assert not dome.interior.any() and not dome.height.any()
    assert dome.obstacle.all() and dome.cleared.all()


def test_a_bar_above_every_height_seeds_nothing_yet_the_slice_still_holds_an_interior() -> (
    None
):
    # `present` says the slice holds an interior; it does not say a peak stands in it.
    stack, lens, pair = _records(PATTERN)
    (dome,) = read_tile_domes(stack, lens, pair, _depth([1]), SPLIT, 7.0, BORDER)
    assert dome.code == "present" and dome.interior.any()
    assert dome.peaks.shape == (0, 2) and not dome.labels.any()
    assert dome.height.max() == pytest.approx(6.0)


def test_the_height_is_in_millimetres_at_the_tile_size_the_stack_was_made_with() -> (
    None
):
    median, first, pair = _grids(PATTERN)
    for tile_mm in (2.0, 4.0, 0.5):
        stack = _stack(median[None], tile_mm)
        (dome,) = read_tile_domes(
            stack,
            _lens(first[None]),
            _pair(pair[None]),
            _depth([0]),
            SPLIT,
            0.25,
            BORDER,
        )
        assert dome.height[3, 3] == pytest.approx(3 * tile_mm)
        assert dome.peak_height_mm.tolist() == pytest.approx([3 * tile_mm] * 2)


def test_the_picture_edge_is_an_obstacle_to_the_tile_dome_too() -> None:
    everything = tuple("N" * 7 for _ in range(7))
    stack, lens, pair = _records(everything, slices=1)
    (dome,) = read_tile_domes(stack, lens, pair, _depth([0]), SPLIT, BAR, BORDER)
    assert dome.peaks.tolist() == [[3, 3]]
    assert dome.height[3, 3] == pytest.approx(4 * TILE_MM)
    assert dome.height[0, 0] == pytest.approx(TILE_MM)
    assert not dome.obstacle.any() and not dome.cleared.any()
    assert np.all(dome.labels == 1)


def test_an_empty_tile_is_neither_an_obstacle_nor_an_interior_yet_the_dome_rises_from_it() -> (
    None
):
    stack, lens, pair = _records(WITH_AN_EMPTY_TILE)
    (dome,) = read_tile_domes(stack, lens, pair, _depth([0]), SPLIT, BAR, BORDER)
    assert not dome.obstacle[2, 9] and not dome.interior[2, 9]
    assert dome.height[2, 9] == 0.0 and dome.labels[2, 9] == 0
    # The tile beside it has nothing to hold it up on that side: one tile, two millimetres.
    assert dome.height[2, 10] == pytest.approx(TILE_MM)


def test_every_array_has_the_stated_shape_dtype_and_is_frozen() -> None:
    stack, lens, pair = _records(PATTERN)
    (dome,) = read_tile_domes(stack, lens, pair, _depth([1]), SPLIT, BAR, BORDER)
    expected = {
        "obstacle": (np.bool_, (7, 13)),
        "cleared": (np.bool_, (7, 13)),
        "interior": (np.bool_, (7, 13)),
        "height": (np.float64, (7, 13)),
        "peaks": (np.int64, (2, 2)),
        "peak_height_mm": (np.float64, (2,)),
        "labels": (np.int32, (7, 13)),
    }
    for name, (dtype, shape) in expected.items():
        array = getattr(dome, name)
        assert array.dtype == dtype and array.shape == shape, name
        assert not array.flags.writeable, name
    assert dome.code in DOME_CODES and dome.why


def test_every_cleared_tile_is_an_obstacle_and_every_territory_tile_an_interior_one() -> (
    None
):
    stack, lens, pair = _records(WITH_A_DARK_TILE)
    for conj in (pair, None):
        (dome,) = read_tile_domes(stack, lens, conj, _depth([1]), SPLIT, BAR, BORDER)
        assert np.all(dome.obstacle[dome.cleared])
        assert not (dome.obstacle & dome.interior).any()
        assert np.all(dome.interior[dome.labels > 0])
        assert dome.labels.max() == len(dome.peaks)
        for k, (row, column) in enumerate(dome.peaks.tolist()):
            assert dome.labels[row, column] == k + 1


def test_the_vectorised_map_is_the_scalar_decision_at_every_tile() -> None:
    # Rows: every first-lens word at each of dark and bright; columns: every conjunction word.
    rows = len(TILE_CODES) * 2
    columns = len(CONJUNCTION_CODES)
    first = np.zeros((1, rows, columns), dtype=np.uint8)
    median = np.full((1, rows, columns), BRIGHT)
    pair = np.zeros((1, rows, columns), dtype=np.uint8)
    for row in range(rows):
        first[0, row, :] = row // 2
        median[0, row, :] = DARK if row % 2 else BRIGHT
        pair[0, row, :] = np.arange(columns)
    stack, lens, conj = _stack(median), _lens(first), _pair(pair)
    paired = read_tile_domes(stack, lens, conj, _depth([0]), SPLIT, 0.25, BORDER)[0]
    alone = read_tile_domes(stack, lens, None, _depth([0]), SPLIT, 0.25, BORDER)[0]
    for row in range(rows):
        for column in range(columns):
            for dome, word in (
                (paired, CONJUNCTION_CODES[column]),
                (alone, None),
            ):
                expected = dome_tile_code(
                    TILE_CODES[row // 2], word, bool(row % 2), BORDER
                )
                assert dome.obstacle[row, column] == (expected == "obstacle"), (
                    row,
                    column,
                    expected,
                )
                assert dome.interior[row, column] == (expected == "interior"), (
                    row,
                    column,
                    expected,
                )
    assert set(DOME_TILE_CODES) >= {"interior", "obstacle", "empty"}


def test_the_ledger_names_each_record_read_then_the_dome_produced() -> None:
    stack, lens, pair = _records(PATTERN)
    with recording() as run_ledger:
        read_tile_domes(stack, lens, pair, _depth([1, 2]), SPLIT, BAR, BORDER)
    events = run_ledger.events()
    assert [event.name for event in events] == [
        "squint_stack.consumed_by.tile_dome",
        "first_lens.consumed_by.tile_dome",
        "depth.consumed_by.tile_dome",
        "conjunction.consumed_by.tile_dome",
        "tile_dome.produced",
    ]
    assert [dict(event.counts) for event in events] == [
        {"stack": 1},
        {"lens": 1},
        {"depth": 1},
        {"conjunction": 1},
        {"slices": 2, "peaks": 4},
    ]


def test_with_no_conjunction_handed_over_nothing_is_recorded_for_it() -> None:
    # Never for a None predecessor.
    stack, lens, _ = _records(PATTERN)
    with recording() as run_ledger:
        read_tile_domes(stack, lens, None, _depth([1]), SPLIT, BAR, BORDER)
    names = [event.name for event in run_ledger.events()]
    assert names == [
        "squint_stack.consumed_by.tile_dome",
        "first_lens.consumed_by.tile_dome",
        "depth.consumed_by.tile_dome",
        "tile_dome.produced",
    ]


def test_a_lens_that_read_no_valley_is_still_a_lens_to_read() -> None:
    # `split_unavailable` cleared nothing but named every kept tile: it is not an absent record.
    stack, lens, pair = _records(PATTERN)
    unavailable = _lens(lens.codes, "split_unavailable")
    with recording() as run_ledger:
        (dome,) = read_tile_domes(
            stack, unavailable, pair, _depth([1]), SPLIT, BAR, BORDER
        )
    assert dome.code == "present"
    assert dict(run_ledger.events()[1].counts) == {"lens": 1}


# --- the orchestration: negative -------------------------------------------------------------------


@pytest.mark.parametrize(
    "bar", [0, 0.0, -1.0, float("nan"), float("inf"), True, None, "8", 1j]
)
def test_a_bar_that_is_not_a_finite_positive_number_is_refused_before_any_ledger_event(
    bar: Any,
) -> None:
    stack, lens, pair = _records(PATTERN)
    with (
        recording() as run_ledger,
        pytest.raises(ValueError, match="invalid_prominence_mm"),
    ):
        read_tile_domes(stack, lens, pair, _depth([1]), SPLIT, bar, BORDER)
    assert run_ledger.events() == ()


def test_a_missing_predecessor_is_one_named_absent_dome_with_empty_arrays_of_rank() -> (
    None
):
    stack, lens, pair = _records(PATTERN)
    cases = (
        (_absent_stack(), lens, _depth([1]), "the squint stack is no_stacked_volume"),
        (stack, _absent_lens(), _depth([1]), "the first lens is predecessor_absent"),
        (
            stack,
            lens,
            _depth([], "predecessor_absent"),
            "the depth collapse is predecessor_absent",
        ),
    )
    for absent_stack, absent_lens, absent_depth, reason in cases:
        domes = read_tile_domes(
            absent_stack, absent_lens, pair, absent_depth, SPLIT, BAR, BORDER
        )
        assert len(domes) == 1
        (dome,) = domes
        assert dome.code == "predecessor_absent" and dome.slice_index == -1
        assert reason in dome.why and dome.series_uid == UID
        assert dome.prominence_mm == BAR
        # Empty arrays of the right rank, never zeros of a size the stage did not read.
        assert dome.obstacle.shape == dome.cleared.shape == (0, 0)
        assert dome.interior.shape == dome.height.shape == dome.labels.shape == (0, 0)
        assert dome.peaks.shape == (0, 2) and dome.peak_height_mm.shape == (0,)
        assert dome.labels.dtype == np.int32 and dome.peaks.dtype == np.int64
        assert not dome.labels.flags.writeable and not dome.peaks.flags.writeable


def test_every_missing_predecessor_is_named_in_the_one_dome_and_the_ledger_counts_it_unread() -> (
    None
):
    # The produced event's `slices` is 0 here: it counts the domes MADE, and the one placeholder
    # dome returned for a missing predecessor was not read from any slice (the stage's docstring:
    # "how many domes were read, 0 for the absent placeholder"). It was once pinned as 1, the
    # placeholder counted, while that was an open question for the lead.
    _, _, pair = _records(PATTERN)
    with recording() as run_ledger:
        (dome,) = read_tile_domes(
            _absent_stack(),
            _absent_lens(),
            pair,
            _depth([], "predecessor_absent"),
            SPLIT,
            BAR,
            BORDER,
        )
    for reason in ("squint stack", "first lens", "depth collapse"):
        assert reason in dome.why
    assert [dict(event.counts) for event in run_ledger.events()] == [
        {"stack": 0},
        {"lens": 0},
        {"depth": 0},
        {"conjunction": 1},
        {"slices": 0, "peaks": 0},
    ]


def test_a_depth_that_chose_no_slice_reads_no_slice() -> None:
    stack, lens, pair = _records(PATTERN)
    with recording() as run_ledger:
        domes = read_tile_domes(stack, lens, pair, _depth([]), SPLIT, BAR, BORDER)
    assert domes == ()
    assert dict(run_ledger.events()[-1].counts) == {"slices": 0, "peaks": 0}


def test_records_that_are_not_one_series_grid_are_refused_by_name() -> None:
    stack, lens, pair = _records(PATTERN)
    narrower = _lens(lens.codes[:, :, :-1])
    with pytest.raises(ValueError, match="first_lens_does_not_match_stack"):
        read_tile_domes(stack, narrower, pair, _depth([1]), SPLIT, BAR, BORDER)
    taller = _pair(np.concatenate([pair.codes, pair.codes[:, :1]], axis=1))
    with pytest.raises(ValueError, match="conjunction_does_not_match_stack"):
        read_tile_domes(stack, lens, taller, _depth([1]), SPLIT, BAR, BORDER)
    shorter = _lens(lens.codes[:-1])
    with pytest.raises(ValueError, match="first_lens_does_not_match_stack"):
        read_tile_domes(stack, shorter, pair, _depth([1]), SPLIT, BAR, BORDER)


@pytest.mark.parametrize("chosen", [[-1], [3], [1, 99]])
def test_a_chosen_slice_outside_the_stack_is_refused_by_name_before_any_is_read(
    chosen: list[int],
) -> None:
    stack, lens, pair = _records(PATTERN, slices=3)
    with (
        recording() as run_ledger,
        pytest.raises(ValueError, match="chosen_slice_outside_stack"),
    ):
        read_tile_domes(stack, lens, pair, _depth(chosen), SPLIT, BAR, BORDER)
    # Nothing was produced: the refusal came before the first dome was made.
    assert "tile_dome.produced" not in [event.name for event in run_ledger.events()]


def test_a_conjunction_handed_over_that_made_no_reading_is_a_silence_not_a_solitary_plane() -> (
    None
):
    # MUST NOT: read a paired plane by the rule a solitary plane has. The plane is paired, the
    # pair reading is what failed, and a dome read by the split would be a different answer to a
    # different question. The silence is named, with the conjunction's own reason.
    stack, lens, _ = _records(WITH_A_DARK_TILE)
    silent = _pair(np.empty((0, 0, 0), dtype=np.uint8), "predecessor_absent")
    with recording() as run_ledger:
        domes = read_tile_domes(stack, lens, silent, _depth([1]), SPLIT, BAR, BORDER)
    assert [dome.code for dome in domes] == ["predecessor_absent"]
    assert (
        domes[0].slice_index == -1
        and "the conjunction is predecessor_absent" in domes[0].why
    )
    assert domes[0].labels.shape == (0, 0)
    assert dict(run_ledger.events()[3].counts) == {"conjunction": 0}
    # Not handed over at all IS a solitary plane, and is read by the split.
    (alone,) = read_tile_domes(stack, lens, None, _depth([1]), SPLIT, BAR, BORDER)
    assert alone.code == "present" and alone.obstacle[3, 2]


@pytest.mark.parametrize(
    "split", [float("nan"), None, True, "ten", float("inf"), -float("inf")]
)
def test_a_split_that_is_not_a_finite_number_makes_no_tile_an_obstacle_by_darkness(
    split: Any,
) -> None:
    # Silence settles nothing: with no valley to read, a dark tile is not thereby an obstacle.
    # The first lens reads an infinite split as no valley as well.
    stack, lens, _ = _records(WITH_A_DARK_TILE)
    (dome,) = read_tile_domes(stack, lens, None, _depth([1]), split, BAR, BORDER)
    np.testing.assert_array_equal(dome.obstacle, _where(WITH_A_DARK_TILE, "B"))
    assert dome.interior[3, 2] and dome.interior[1:6, 6].all()
    assert "a split that was not read" in dome.why


def test_a_stored_word_no_vocabulary_says_is_named_unknown_and_never_an_interior() -> (
    None
):
    median, first, pair = _grids(PATTERN)
    first = first.copy()
    pair = pair.copy()
    first[2, 2] = 9  # a first-lens index no word stands for
    pair[3, 3] = 99  # a conjunction index no word stands for
    first[4, 4] = 255
    stack = _stack(median[None])
    with recording() as run_ledger:
        (dome,) = read_tile_domes(
            stack,
            _lens(first[None]),
            _pair(pair[None]),
            _depth([0]),
            SPLIT,
            BAR,
            BORDER,
        )
    for row, column in ((2, 2), (3, 3), (4, 4)):
        assert not dome.interior[row, column] and not dome.obstacle[row, column]
        assert dome.labels[row, column] == 0 and dome.height[row, column] == 0.0
    assert "3 unnamed" in dome.why
    assert not dome.cleared[2, 2]
    assert dict(run_ledger.events()[0].counts) == {"stack": 1}


def test_a_stored_negative_code_is_unknown_and_never_read_as_a_word_by_wrapping() -> (
    None
):
    median, first, pair = _grids(PATTERN)
    signed_first = first.astype(np.int16)
    signed_pair = pair.astype(np.int16)
    signed_first[2, 2] = -1
    signed_pair[3, 3] = -1
    (dome,) = read_tile_domes(
        _stack(median[None]),
        _lens(signed_first[None]),
        _pair(signed_pair[None]),
        _depth([0]),
        SPLIT,
        BAR,
        BORDER,
    )
    for row, column in ((2, 2), (3, 3)):
        assert not dome.interior[row, column] and not dome.obstacle[row, column]


def test_nothing_of_the_callers_records_is_written() -> None:
    stack, lens, pair = _records(WITH_A_DARK_TILE)
    depth = _depth([1, 2])
    arrays = (stack.median, lens.codes, pair.codes, depth.chosen_slices)
    before = [array.copy() for array in arrays]
    for array in arrays:
        array.setflags(write=False)  # a write to any of them would raise
    for conj in (pair, None):
        read_tile_domes(stack, lens, conj, depth, SPLIT, BAR, BORDER)
    for array, kept in zip(arrays, before, strict=True):
        np.testing.assert_array_equal(array, kept)


def test_the_three_codes_the_stage_says_are_each_reached() -> None:
    stack, lens, pair = _records(PATTERN)
    empty_stack, empty_lens, empty_pair = _records(NOTHING_KEPT)
    seen = set()
    for domes in (
        read_tile_domes(stack, lens, pair, _depth([1]), SPLIT, BAR, BORDER),
        read_tile_domes(
            empty_stack, empty_lens, empty_pair, _depth([0]), SPLIT, BAR, BORDER
        ),
        read_tile_domes(_absent_stack(), lens, pair, _depth([1]), SPLIT, BAR, BORDER),
    ):
        seen.update(dome.code for dome in domes)
    assert seen == set(DOME_CODES)


# --- the picture adapter: it arranges the saved domes and alters nothing -------------------------

TILE_DOME_ARRAYS = (
    "obstacle",
    "cleared",
    "interior",
    "height",
    "labels",
    "peaks",
    "peak_height_mm",
)
PLANE_SHAPE = (7 * TILE_PX, 13 * TILE_PX)


def _plane(offset: int = 0) -> np.ndarray:
    size = PLANE_SHAPE[0] * PLANE_SHAPE[1]
    return ((np.arange(size).reshape(PLANE_SHAPE) + offset) % 200).astype(np.uint16)


def _two_domes() -> tuple[SquintStack, tuple[TileDome, ...]]:
    stack, lens, pair = _records(PATTERN, slices=4)
    return stack, read_tile_domes(stack, lens, pair, _depth([1, 2]), SPLIT, BAR, BORDER)


def _tile_dome_record(
    domes: tuple[TileDome, ...],
) -> tuple[dict, dict[str, np.ndarray]]:
    """The record the writer must save for a series' tile domes, and its arrays.

    This is the SHAPE the drawer reads (and the writer_note of this unit hands the integrator):
    a series-level word and reason from the stage's own vocabulary, the two vocabularies, the bar,
    how many domes, the tile grid, one entry per dome (its slice, word, reason, number of peaks),
    and one array per field saved as `tile_dome_<field>`: the grids stacked with one grid per
    dome along the first axis, and every dome's peaks one after the other. Each dome's entry also
    names the border it was read under: a dome is identified by its (border, slice).
    """
    if not domes or any(dome.code == "predecessor_absent" for dome in domes):
        code = "predecessor_absent"
        why = (
            domes[0].why
            if domes
            else "the depth collapse chose no slice; no dome was read"
        )
    else:
        code = "present" if any(d.code == "present" for d in domes) else "no_interior"
        why = "; ".join(f"slice {d.slice_index}: {d.code}" for d in domes)
    grid = domes[0].labels.shape if domes else (0, 0)
    record = {
        "code": code,
        "why": why,
        "code_names": list(DOME_CODES),
        "tile_code_names": list(DOME_TILE_CODES),
        "prominence_mm": float(domes[0].prominence_mm) if domes else None,
        "slices": len(domes),
        "tiles_rc": [int(grid[0]), int(grid[1])],
        "domes": [
            {
                "slice_index": int(d.slice_index),
                "border": d.border,
                "code": d.code,
                "why": d.why,
                "peaks": int(d.peaks.shape[0]),
            }
            for d in domes
        ],
        "axes": (
            "obstacle, cleared, interior, height, labels (K, TR, TC): one tile grid per saved "
            "dome, in saved order; peaks (sum of peaks, 2) tile rc and peak_height_mm (sum of "
            "peaks,) mm, every dome's peaks one after the other, tallest first within a dome"
        ),
        "arrays": {name: f"tile_dome_{name}" for name in TILE_DOME_ARRAYS},
    }
    empty_grid = (0, 0, 0)

    def stacked(field: str, dtype: type) -> np.ndarray:
        if not domes:
            return np.empty(empty_grid, dtype=dtype)
        return np.stack([getattr(dome, field) for dome in domes])

    arrays = {
        "tile_dome_obstacle": stacked("obstacle", np.bool_),
        "tile_dome_cleared": stacked("cleared", np.bool_),
        "tile_dome_interior": stacked("interior", np.bool_),
        "tile_dome_height": stacked("height", np.float64),
        "tile_dome_labels": stacked("labels", np.int32),
        "tile_dome_peaks": np.concatenate([d.peaks for d in domes])
        if domes
        else np.empty((0, 2), dtype=np.int64),
        "tile_dome_peak_height_mm": np.concatenate([d.peak_height_mm for d in domes])
        if domes
        else np.empty((0,), dtype=np.float64),
    }
    return record, arrays


def _saved_record(
    tmp_path: Path,
    domes: tuple[TileDome, ...],
    stack: SquintStack | None,
    *,
    name: str = "series",
    with_dome: bool = True,
    plane: np.ndarray | None = None,
    selected: int = 1,
    walk: dict[int, np.ndarray] | None = None,
) -> dict:
    """One series record shaped as the writer saves it, with its arrays on disk."""
    saved: dict[str, np.ndarray] = {}
    entry: dict = {
        "study_uid": "study",
        "series_uid": name,
        "view": ["Coronal", "1", "1"],
        "code": "measured",
        "slice_index": selected,
        "source_plane": f"slice-{selected}.dcm",
        "artifact": f"{name}.npz",
    }
    if stack is not None:
        stack_record, stack_arrays = squint_stack_record(stack)
        saved.update(stack_arrays)
        entry["squint_stack"] = stack_record
    if with_dome:
        dome_record, dome_arrays = _tile_dome_record(domes)
        saved.update(dome_arrays)
        entry["tile_dome"] = dome_record
    if plane is not None:
        saved["acquired_plane"] = plane
    if walk:
        saved["study_walk"] = np.stack([walk[index] for index in sorted(walk)])
        entry["study"] = {
            "slice_codes": ["decoded"] * 4,
            "walk_indices": sorted(walk),
            "walk_array": "study_walk",
        }
    np.savez_compressed(tmp_path / f"{name}.npz", allow_pickle=False, **saved)
    entry["arrays"] = json.loads(json.dumps(array_table(saved), allow_nan=False))
    return json.loads(json.dumps(entry, allow_nan=False))


def _panel_arguments(
    stack: SquintStack,
    record: dict,
    arrays: dict[str, np.ndarray],
    planes: dict[int, np.ndarray],
    **overrides: Any,
) -> dict[str, Any]:
    """The arguments the reader hands the adapter: the record's words and the saved arrays.

    It only builds them. Every test calls `dome_panels` itself, directly, so the call is one
    Detective can route by its static path.
    """
    saved = record.get("tile_dome", record)
    arguments = {
        "code": saved["code"],
        "why": saved["why"],
        "prominence_mm": saved["prominence_mm"],
        "tile_mm": stack.tile_mm,
        "median": stack.median,
        "bounds_rc": stack.bounds_rc,
        "indices": [d["slice_index"] for d in saved["domes"]],
        "borders": [d["border"] for d in saved["domes"]],
        "codes": [d["code"] for d in saved["domes"]],
        "whys": [d["why"] for d in saved["domes"]],
        "peak_counts": [d["peaks"] for d in saved["domes"]],
        "obstacle": arrays["tile_dome_obstacle"],
        "cleared": arrays["tile_dome_cleared"],
        "interior": arrays["tile_dome_interior"],
        "height": arrays["tile_dome_height"],
        "labels": arrays["tile_dome_labels"],
        "peaks": arrays["tile_dome_peaks"],
        "peak_height_mm": arrays["tile_dome_peak_height_mm"],
        "planes": planes,
    }
    arguments.update(overrides)
    return arguments


def test_the_standing_names_a_named_dome_and_every_silence_apart() -> None:
    assert dome_standing("present", 0, 3) == "named"
    assert dome_standing("no_interior", 2, 3) == "named"
    assert dome_standing(None, 0, 3) == "dome_not_saved"
    assert dome_standing("predecessor_absent", -1, 0) == "dome_absent"
    assert dome_standing("present", 3, 3) == "slice_outside_stack"
    assert dome_standing("present", -1, 3) == "slice_outside_stack"
    assert dome_standing("present", 0, 0) == "slice_outside_stack"
    assert dome_standing("lesion", 0, 3) == "dome_code_unknown"
    assert dome_standing(7, 0, 3) == "dome_code_unknown"


def test_the_standing_is_total_and_never_named_without_a_held_slice() -> None:
    # MUST NOT: draw a dome whose word the stage does not say, whose stage made none, or whose
    # slice is not a whole number inside the stack; and every answer is a declared standing.
    for code in (*DOME_CODES, None, "", 1, "lesion"):
        for index in (0, 1, 2, 3, -1, True, 1.0, None, "1"):
            standing = dome_standing(code, index, 3)
            assert standing in DOME_STANDINGS, (code, index)
            if standing == "named":
                assert code in ("present", "no_interior")
                assert type(index) is int and 0 <= index < 3


def test_the_adapter_selects_each_domes_own_tiles_peaks_medians_and_plane_and_alters_nothing() -> (
    None
):
    stack, domes = _two_domes()
    record, arrays = _tile_dome_record(domes)
    planes = {2: _plane(2)}
    before = {name: array.copy() for name, array in arrays.items()}
    frame = dome_panels(**_panel_arguments(stack, record, arrays, planes))
    assert frame.code == "present" and frame.prominence_mm == BAR
    assert frame.tile_mm == TILE_MM and frame.slices == 4
    assert frame.bounds_rc is not None and frame.bounds_rc.dtype == np.int64
    assert [panel.index for panel in frame.domes] == [1, 2]
    for panel, dome in zip(frame.domes, domes, strict=True):
        assert panel.standing == "named" and panel.code == "present"
        for field in ("obstacle", "cleared", "interior", "height", "labels", "peaks"):
            np.testing.assert_array_equal(getattr(panel, field), getattr(dome, field))
        np.testing.assert_array_equal(panel.peak_height_mm, dome.peak_height_mm)
        np.testing.assert_array_equal(panel.median, stack.median[dome.slice_index])
    # Handed on, not copied or derived: a view of the saved array.
    assert np.shares_memory(frame.domes[0].height, arrays["tile_dome_height"])
    # The plane is the one saved at EXACTLY the dome's own stack index and never another's.
    assert frame.domes[1].plane is planes[2]
    assert frame.domes[0].plane is None
    for name, array in arrays.items():
        np.testing.assert_array_equal(array, before[name])


def test_the_adapter_splits_the_peaks_by_the_saved_counts() -> None:
    stack, domes = _two_domes()
    record, arrays = _tile_dome_record(domes)
    moved = replace(
        domes[0], peaks=domes[0].peaks[:1], peak_height_mm=domes[0].peak_height_mm[:1]
    )
    record, arrays = _tile_dome_record((moved, domes[1]))
    frame = dome_panels(**_panel_arguments(stack, record, arrays, {}))
    counts = [0 if p.peaks is None else p.peaks.shape[0] for p in frame.domes]
    assert counts == [1, 2]
    np.testing.assert_array_equal(frame.domes[1].peaks, domes[1].peaks)


def test_the_adapter_keeps_every_absence_absent() -> None:
    nothing = dome_panels(
        None,
        None,
        None,
        None,
        None,
        None,
        (),
        (),
        (),
        (),
        (),
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        {},
    )
    assert nothing.code is None and nothing.domes == () and nothing.slices == 0
    assert nothing.prominence_mm is None and nothing.tile_mm is None
    assert nothing.bounds_rc is None


def test_the_adapter_names_each_silence_and_draws_none_of_them() -> None:
    stack, domes = _two_domes()
    record, arrays = _tile_dome_record(domes * 2)
    frame = dome_panels(
        **_panel_arguments(
            stack,
            record,
            arrays,
            {},
            indices=[1, 1, -1, 9],
            codes=["present", "lesion", "predecessor_absent", "present"],
            whys=["w", "w", "w", "w"],
        )
    )
    assert [panel.standing for panel in frame.domes] == [
        "named",
        "dome_code_unknown",
        "dome_absent",
        "slice_outside_stack",
    ]
    for panel in frame.domes[1:]:
        for field in ("plane", "median", "obstacle", "height", "labels", "peaks"):
            assert getattr(panel, field) is None, (panel.standing, field)
        assert panel.code is not None and panel.why == "w"
    # A slice that is not a whole number is named and never rounded into a slice.
    odd = dome_panels(
        **_panel_arguments(stack, record, arrays, {}, indices=[2.7, "two"])
    )
    assert [panel.standing for panel in odd.domes] == ["slice_outside_stack"] * 2
    assert [panel.index for panel in odd.domes] == [2.7, "two"]


# --- the drawer's reader -------------------------------------------------------------------------


def test_the_reader_reconstitutes_a_writer_shaped_record(tmp_path: Path) -> None:
    stack, domes = _two_domes()
    record = _saved_record(
        tmp_path,
        domes,
        stack,
        plane=_plane(1),
        selected=1,
        walk={0: _plane(0), 2: _plane(2)},
    )
    artifact, frame = tile_dome_frames.saved_tile_dome(tmp_path, record)
    assert artifact == tmp_path / "series.npz"
    assert frame.code == "present" and frame.prominence_mm == BAR
    assert frame.tile_mm == TILE_MM and frame.slices == 4
    assert frame.bounds_rc is not None and frame.bounds_rc.shape == (7, 13, 4)
    assert [panel.index for panel in frame.domes] == [1, 2]
    for panel, dome in zip(frame.domes, domes, strict=True):
        assert panel.standing == "named"
        for field in ("obstacle", "cleared", "interior", "height", "labels", "peaks"):
            np.testing.assert_array_equal(getattr(panel, field), getattr(dome, field))
        np.testing.assert_array_equal(panel.median, stack.median[dome.slice_index])
    # Slice 1 is the selected plane, slice 2 the walk's; each only at its own index.
    np.testing.assert_array_equal(frame.domes[0].plane, _plane(1))
    np.testing.assert_array_equal(frame.domes[1].plane, _plane(2))


def test_the_reader_says_when_no_plane_was_saved_at_a_domes_slice(
    tmp_path: Path,
) -> None:
    stack, domes = _two_domes()
    record = _saved_record(
        tmp_path, domes, stack, plane=_plane(3), selected=3, walk={0: _plane(0)}
    )
    _, frame = tile_dome_frames.saved_tile_dome(tmp_path, record)
    assert [panel.plane for panel in frame.domes] == [None, None]
    assert [panel.standing for panel in frame.domes] == ["named", "named"]


def test_the_reader_says_when_no_dome_was_saved(tmp_path: Path) -> None:
    stack, domes = _two_domes()
    record = _saved_record(tmp_path, domes, stack, with_dome=False)
    _, frame = tile_dome_frames.saved_tile_dome(tmp_path, record)
    assert frame.code is None and frame.domes == () and frame.slices == 0
    assert frame.bounds_rc is None and frame.prominence_mm is None


def test_the_reader_needs_no_stack_for_a_dome_the_stage_did_not_make(
    tmp_path: Path,
) -> None:
    _, lens, pair = _records(PATTERN)
    absent = read_tile_domes(
        _absent_stack(), lens, pair, _depth([1]), SPLIT, BAR, BORDER
    )
    record = _saved_record(tmp_path, absent, None)
    _, frame = tile_dome_frames.saved_tile_dome(tmp_path, record)
    assert frame.code == "predecessor_absent" and frame.bounds_rc is None
    assert [panel.standing for panel in frame.domes] == ["dome_absent"]
    assert frame.domes[0].index == -1 and frame.domes[0].median is None
    nothing = _saved_record(tmp_path, (), None, name="chosen-nothing")
    _, empty = tile_dome_frames.saved_tile_dome(tmp_path, nothing)
    assert empty.code == "predecessor_absent" and empty.domes == ()
    assert empty.prominence_mm is None


#: Each way a saved record can disagree with the writer, as the change that makes it so and the
#: name the reader refuses it by.
DISAGREEMENTS = [
    pytest.param(
        lambda r: r["arrays"]["tile_dome_height"].__setitem__("digest", "changed"),
        "saved_array_digest_mismatch",
        id="a tampered array",
    ),
    pytest.param(
        lambda r: r.__setitem__("tile_dome", "yes"),
        "saved_tile_dome_not_a_record",
        id="a record that is not a mapping",
    ),
    pytest.param(
        lambda r: r["tile_dome"].__setitem__("why", 5),
        "saved_tile_dome_field_invalid:why",
        id="a reason that is not text",
    ),
    pytest.param(
        lambda r: r["tile_dome"].__setitem__("code", "lesion"),
        "saved_tile_dome_code_unknown:lesion",
        id="a series word the stage does not say",
    ),
    pytest.param(
        lambda r: r["tile_dome"]["domes"][0].__setitem__("code", "lesion"),
        "saved_tile_dome_code_unknown:lesion",
        id="a dome word the stage does not say",
    ),
    pytest.param(
        lambda r: r["tile_dome"].__setitem__("code_names", ["present"]),
        "saved_tile_dome_vocabulary_mismatch",
        id="a code vocabulary that is not the stage's",
    ),
    pytest.param(
        lambda r: r["tile_dome"].__setitem__("tile_code_names", []),
        "saved_tile_dome_vocabulary_mismatch",
        id="a tile vocabulary that is not the stage's",
    ),
    pytest.param(
        lambda r: r["tile_dome"].__setitem__("prominence_mm", "eight"),
        "saved_tile_dome_not_a_number:prominence_mm",
        id="a bar that is text",
    ),
    pytest.param(
        lambda r: r["tile_dome"].__setitem__("prominence_mm", 0.0),
        "saved_tile_dome_not_a_number:prominence_mm",
        id="a bar that is not positive",
    ),
    pytest.param(
        lambda r: r["tile_dome"].__setitem__("slices", 5),
        "saved_tile_dome_slices_mismatch",
        id="a count that is not the domes'",
    ),
    pytest.param(
        lambda r: r["tile_dome"].__setitem__("tiles_rc", [7]),
        "saved_tile_dome_tiles_invalid",
        id="a grid that is not two sizes",
    ),
    pytest.param(
        lambda r: r["tile_dome"]["domes"][0].__setitem__("peaks", -1),
        "saved_tile_dome_dome_invalid:0:peaks",
        id="a number of peaks below zero",
    ),
    pytest.param(
        lambda r: r["tile_dome"]["arrays"].pop("labels"),
        "saved_tile_dome_array_unnamed:labels",
        id="an array the record does not name",
    ),
    pytest.param(
        lambda r: r["tile_dome"].__setitem__("tiles_rc", [7, 12]),
        "saved_tile_dome_shape_mismatch",
        id="a grid that is not the arrays'",
    ),
    pytest.param(
        lambda r: r["tile_dome"]["domes"][0].__setitem__("peaks", 1),
        "saved_tile_dome_shape_mismatch:peaks",
        id="peaks that are not the sum of the counts",
    ),
    pytest.param(
        lambda r: r["arrays"]["tile_dome_labels"].__setitem__("dtype", "<i8"),
        "saved_array_dtype_mismatch:tile_dome_labels",
        id="a descriptor that is not its array's dtype",
    ),
]


@pytest.mark.parametrize(("mutate", "match"), DISAGREEMENTS)
def test_the_reader_refuses_a_saved_record_that_disagrees_with_the_writer(
    tmp_path: Path, mutate: Any, match: str
) -> None:
    # MUST NOT: draw a tampered array, a word the stage does not say, a vocabulary that is not
    # the stage's, a bar that is not a number, a count that is not the domes', an array whose
    # shape is not the record's; each is named. (A peak or label the record cannot hold, a dome
    # without its stack, a stack that is not its grid and a plane that is not the stack's are
    # the tests below.)
    stack, domes = _two_domes()
    record = _saved_record(tmp_path, domes, stack)
    mutate(record)
    with pytest.raises(ValueError, match=match):
        tile_dome_frames.saved_tile_dome(tmp_path, record)


def test_the_reader_refuses_an_array_saved_in_a_representation_the_stage_does_not_make(
    tmp_path: Path,
) -> None:
    # The array and its descriptor AGREE, so the writer's own check passes; what is refused is
    # that the stage's labels are int32 and these are not.
    stack, domes = _two_domes()
    record = _saved_record(tmp_path, domes, stack)
    with np.load(tmp_path / "series.npz", allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    arrays["tile_dome_labels"] = arrays["tile_dome_labels"].astype(np.int64)
    np.savez_compressed(tmp_path / "series.npz", allow_pickle=False, **arrays)
    record["arrays"] = json.loads(json.dumps(array_table(arrays), allow_nan=False))
    with pytest.raises(
        ValueError, match="saved_tile_dome_representation_invalid:labels"
    ):
        tile_dome_frames.saved_tile_dome(tmp_path, record)


def test_the_reader_refuses_a_peak_or_label_the_record_cannot_hold(
    tmp_path: Path,
) -> None:
    stack, domes = _two_domes()
    outside = replace(
        domes[0],
        peaks=np.array([[99, 0], [3, 9]], dtype=np.int64),
    )
    record = _saved_record(tmp_path, (outside, domes[1]), stack)
    with pytest.raises(ValueError, match="saved_tile_dome_peak_outside_grid:0"):
        tile_dome_frames.saved_tile_dome(tmp_path, record)
    fewer = replace(
        domes[1], peaks=domes[1].peaks[:1], peak_height_mm=domes[1].peak_height_mm[:1]
    )
    record = _saved_record(tmp_path, (domes[0], fewer), stack)
    with pytest.raises(ValueError, match="saved_tile_dome_label_outside_peaks:1"):
        tile_dome_frames.saved_tile_dome(tmp_path, record)


def test_the_reader_refuses_a_dome_without_the_stack_that_places_it(
    tmp_path: Path,
) -> None:
    _, domes = _two_domes()
    alone = _saved_record(tmp_path, domes, None)
    with pytest.raises(ValueError, match="saved_tile_dome_without_a_stack"):
        tile_dome_frames.saved_tile_dome(tmp_path, alone)
    taller = _stack(np.zeros((4, 8, 13)))
    other_grid = _saved_record(tmp_path, domes, taller)
    with pytest.raises(ValueError, match="saved_tile_dome_grid_mismatch"):
        tile_dome_frames.saved_tile_dome(tmp_path, other_grid)
    absent_stack = _saved_record(tmp_path, domes, _absent_stack())
    with pytest.raises(ValueError, match="saved_tile_dome_grid_mismatch"):
        tile_dome_frames.saved_tile_dome(tmp_path, absent_stack)


def test_the_reader_refuses_an_acquired_plane_that_is_not_the_stacks_plane(
    tmp_path: Path,
) -> None:
    stack, domes = _two_domes()
    wrong = np.zeros((5, 5), dtype=np.uint16)
    record = _saved_record(tmp_path, domes, stack, plane=wrong, selected=1)
    with pytest.raises(ValueError, match="saved_tile_dome_covers_another_plane"):
        tile_dome_frames.saved_tile_dome(tmp_path, record)


# --- the drawer ----------------------------------------------------------------------------------


def test_an_out_directory_outside_data_is_an_argument_refusal(tmp_path: Path) -> None:
    stack, domes = _two_domes()
    record = _saved_record(tmp_path, domes, stack)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    with pytest.raises(ArgumentRefusal, match="private data directory"):
        tile_dome_frames.draw(tmp_path, "study", tmp_path / "out")
    with pytest.raises(ArgumentRefusal, match="no saved records"):
        tile_dome_frames.draw(
            tmp_path, "another-study", PROJECT / "data" / "pictures" / "_pytest" / "x"
        )


def test_the_drawer_writes_one_sheet_per_view_with_its_manifest(tmp_path: Path) -> None:
    """The impure edge, end to end: one image per series under data/, bound to the receipt.

    Four series in one receipt, each a different silence or reading: two domes with a plane at
    one slice only; a dome the stage did not make; a record that holds no dome; a series whose
    writer saved no tile dome at all.
    """
    stack, domes = _two_domes()
    _, lens, pair = _records(PATTERN)
    absent = read_tile_domes(
        _absent_stack(), lens, pair, _depth([1]), SPLIT, BAR, BORDER
    )
    records = [
        _saved_record(tmp_path, domes, stack, name="read", plane=_plane(1), selected=1),
        _saved_record(tmp_path, absent, None, name="absent"),
        _saved_record(tmp_path, (), None, name="chosen-nothing"),
        _saved_record(tmp_path, domes, stack, name="unsaved", with_dome=False),
    ]
    (tmp_path / "receipt.json").write_text(json.dumps({"records": records}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = tile_dome_frames.draw(tmp_path, "study", out)
        assert manifest["schema"] == "tile-dome-frames-v2"
        assert manifest["images"] == [
            "01-coronal-fs1-fat1.png",
            "02-coronal-fs1-fat1.png",
            "03-coronal-fs1-fat1.png",
            "04-coronal-fs1-fat1.png",
        ]
        assert manifest["image"] == manifest["images"][0]
        assert manifest["standings"] == list(DOME_STANDINGS)
        for name in manifest["images"]:
            assert (out / name).stat().st_size > 0
        assert (out / "manifest.json").exists()
        assert manifest["legend"]["peak"] == tile_dome_frames.PEAK_COLOUR
        read, absent_sheet, nothing, unsaved = manifest["series"]
        assert read["tile_dome"]["code"] == "present"
        assert read["tile_dome"]["prominence_mm"] == BAR
        assert read["tile_dome"]["tiles_rc"] == [7, 13]
        # One column for each border of each slice, in the order of `BORDER_CODES`. The record
        # holds the domes under one border only, so the other border's column of each slice is a
        # named silence in words and never a blank.
        assert [(d["index"], d["border"]) for d in read["domes"]] == [
            (1, BORDER),
            (1, OTHER_BORDER),
            (2, BORDER),
            (2, OTHER_BORDER),
        ]
        not_saved = [d for d in read["domes"] if d["border"] == OTHER_BORDER]
        assert [d["standing"] for d in not_saved] == [
            tile_dome_frames.BORDER_NOT_SAVED
        ] * 2
        assert [d["drawn"] for d in not_saved] == [
            {
                "territories": tile_dome_frames.BORDER_NOT_SAVED,
                "height": tile_dome_frames.BORDER_NOT_SAVED,
            }
        ] * 2
        # Slice 1 has the selected plane under it; slice 2 has none saved, so its medians are
        # drawn alone and the manifest says so. The heights are drawn from the saved values.
        saved = [d for d in read["domes"] if d["border"] == BORDER]
        assert [d["drawn"] for d in saved] == [
            {"territories": "named", "height": "named"},
            {"territories": "medians_alone", "height": "named"},
        ]
        assert [d["counts"]["peaks"] for d in saved] == [2, 2]
        assert absent_sheet["domes"][0]["drawn"] == {
            "territories": "dome_absent",
            "height": "dome_absent",
        }
        assert (
            nothing["domes"] == []
            and nothing["tile_dome"]["code"] == "predecessor_absent"
        )
        assert unsaved["tile_dome"] is None and unsaved["domes"] == []
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_every_standing_the_adapter_names_has_words_on_the_sheet() -> None:
    assert set(DOME_STANDINGS) <= set(tile_dome_frames.STANDING_WORDS)
    assert len(tile_dome_frames.TERRITORY_COLOURS) == len(
        set(tile_dome_frames.TERRITORY_COLOURS)
    )


def test_the_picture_module_is_the_adapter_the_drawer_reads() -> None:
    assert tile_dome_frames.pictures is pictures
    module = importlib.import_module("workbench.render.tile_dome_frames")
    assert module.draw is tile_dome_frames.draw
