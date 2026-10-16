"""The cheap profile's measurements: what a tile median hides, what is unknown and never zero, the
runs, plateaus and ends of a profile, and the physical depth of its support."""

from typing import Any

import numpy as np
import pytest

from knee.collapse.profile import (
    CLIPPED_BY_THE_SCAN,
    block_centres_rc,
    block_holds,
    block_medians,
    confirmations,
    could_hold_level,
    depth_offsets_mm,
    positive_runs,
    run_maxima,
    run_neighbours,
    support_intervals_mm,
)

NONE_UNSEEN = np.zeros((40, 40), dtype=bool)


def test_a_thin_bright_cord_a_tile_median_hides_is_read_by_the_finer_blocks():
    plane = np.full((40, 40), 10.0)
    plane[:, 18:22] = 500.0  # 4 px wide: under half of a 10 px tile
    tile = block_medians(plane, NONE_UNSEEN, (1.0, 1.0), 10.0)
    fine = block_medians(plane, NONE_UNSEEN, (1.0, 1.0), 2.0)
    assert tile.median.max() == 10.0  # the squint's median says nothing is there
    assert fine.median.max() == 500.0  # the finer reading sees it


def test_a_block_with_any_unseen_pixel_is_unknown_never_a_dark_median():
    plane = np.full((40, 40), 400.0)
    unseen = NONE_UNSEEN.copy()
    unseen[0, 0] = True
    plane[5, 5] = np.nan  # not finite is unseen too
    read = block_medians(plane, unseen, (1.0, 1.0), 4.0)
    assert np.isnan(read.median[0, 0]) and np.isnan(read.median[1, 1])
    assert read.median[2, 2] == 400.0
    assert np.isnan(read.median).sum() == 2  # nothing else lost, nothing made 0


def test_blocks_tile_the_window_from_its_corner_and_the_cut_block_is_unknown():
    plane = np.arange(1600.0).reshape(40, 40)
    read = block_medians(plane, NONE_UNSEEN, (1.0, 1.0), 4.0, (2, 11, 3, 40))
    assert read.window_rc == (2, 11, 3, 40) and read.block_px == (4, 4)
    assert read.median.shape == (3, 10)
    assert read.median[0, 0] == np.median(plane[2:6, 3:7])
    assert np.isnan(read.median[2]).all()  # rows 10 only: a block cut by the window
    assert np.isnan(read.median[:, 9]).all()  # columns 39 only
    centres = block_centres_rc(read)
    assert np.allclose(centres[0, 0], (2 + 1.5, 3 + 1.5))


def test_the_block_size_follows_the_pixel_pitch_per_axis():
    read = block_medians(np.ones((40, 40)), NONE_UNSEEN, (0.5, 2.0), 2.0)
    assert read.block_px == (4, 1) and read.block_mm == (2.0, 2.0)


def test_places_are_carried_onto_blocks_by_any_place_held():
    read = block_medians(
        np.ones((40, 40)), NONE_UNSEEN, (1.0, 1.0), 4.0, (0, 20, 0, 20)
    )
    mask = np.zeros((40, 40), dtype=bool)
    mask[5, 9] = True
    mask[30, 30] = True  # outside the window: not a place of it
    held = block_holds(mask, read)
    assert held.sum() == 1 and held[1, 2]


@pytest.mark.parametrize(
    ("args", "name"),
    [
        ({"plane": np.ones(5)}, "invalid_plane"),
        ({"plane": np.ones((4, 4), dtype=bool)}, "invalid_plane"),
        ({"unseen": np.zeros((3, 3), dtype=bool)}, "invalid_unseen"),
        ({"unseen": np.zeros((4, 4), dtype=int)}, "invalid_unseen"),
        ({"spacing": (0.0, 1.0)}, "invalid_spacing"),
        ({"block": float("nan")}, "invalid_block_mm"),
        ({"block": -1.0}, "invalid_block_mm"),
        ({"window": (0, 0, 0, 4)}, "invalid_window"),
        ({"window": (0, 5, 0, 4)}, "invalid_window"),
    ],
)
def test_empty_nonfinite_and_malformed_input_is_refused_by_name(args, name):
    call: dict[str, Any] = {
        "plane": np.ones((4, 4)),
        "unseen": np.zeros((4, 4), dtype=bool),
        "spacing": (1.0, 1.0),
        "block": 2.0,
        "window": None,
    }
    call.update(args)
    with pytest.raises(ValueError, match=name):
        block_medians(
            call["plane"],
            call["unseen"],
            call["spacing"],
            call["block"],
            call["window"],
        )


def test_tile_extrema_exclude_exactly_what_they_can_and_say_nothing_of_unseen_tiles():
    low, high = np.array([[0.0, 600.0, np.nan]]), np.array([[100.0, 900.0, np.nan]])
    could, unseen = could_hold_level(low, high, 300.0, 500.0)
    assert could.tolist() == [[False, False, False]]  # max under the level; min over it
    assert unseen.tolist() == [[False, False, True]]  # unseen excludes nothing: apart
    could, _ = could_hold_level(np.array([[100.0]]), np.array([[900.0]]), 300.0, 500.0)
    assert could.tolist() == [[True]]  # a tile spanning the level may hold it


def test_a_run_ends_at_nan_and_at_zero_and_a_plateau_keeps_every_slice():
    area = np.array([np.nan, 5.0, 9.0, 9.0, 0.0, 4.0, np.nan, 7.0])
    runs = positive_runs(area)
    assert runs == [
        (1, 4),
        (5, 6),
        (7, 8),
    ]  # not read and measured empty both end a run
    peaks = run_maxima(area, runs)
    assert [p.tolist() for p in peaks] == [[2, 3], [5], [7]]  # tie kept; runs apart
    assert positive_runs(np.array([])) == [] and positive_runs(np.full(3, np.nan)) == []


def test_what_a_run_touches_at_each_end_is_the_scans_edge_or_the_neighbours_status():
    status = np.array([2, 2, 1, 2, 3, 0])
    runs = positive_runs(np.where(status == 2, 1.0, 0.0))
    ends = run_neighbours(runs, status)
    assert ends.tolist() == [[CLIPPED_BY_THE_SCAN, 1], [1, 3]]


def test_only_a_maximum_at_a_run_end_beside_an_unresolved_slice_is_pointed_to():
    status = np.array([4, 2, 2, 2, 3, 1, 2, 2, 1])
    area = np.where(status == 2, [0, 5, 9, 5, 0, 0, 3, 3, 0], np.nan).astype(float)
    area[5] = 0.0
    runs = positive_runs(area)
    maxima = run_maxima(area, runs)
    assert confirmations(runs, maxima, status, (3, 4)) == []  # maximum inside the run
    area[3] = 11.0
    maxima = run_maxima(area, runs)
    assert confirmations(runs, maxima, status, (3, 4)) == [4]
    area[1] = (
        20.0  # the run's first maximum now beside the first slice, which is unresolved (4)
    )
    assert confirmations(runs, run_maxima(area, runs), status, (3, 4)) == [0]
    # measured-empty neighbours and a plateau beside a measured-empty slice point nowhere
    assert confirmations(runs, run_maxima(area, runs), status, (3,)) == []


def test_depth_is_physical_whatever_the_stack_order_and_spacing():
    normal = np.array([1.0, 0.0, 0.0])
    ascending = np.array([[0.0, 0, 0], [2.0, 5, 5], [3.0, 0, 0], [7.0, 0, 0]])
    forward = depth_offsets_mm(ascending, normal, 1)
    backward = depth_offsets_mm(ascending[::-1], normal, 2)
    assert forward.tolist() == [-2.0, 0.0, 1.0, 5.0]
    assert backward.tolist() == forward[::-1].tolist()
    # a normal that is not unit length still measures millimetres
    assert depth_offsets_mm(ascending, normal * 4, 1).tolist() == forward.tolist()


def test_support_runs_are_given_by_the_planes_own_thickness_and_nothing_between():
    offsets = np.array([-2.0, 0.0, 1.0, 5.0])
    thickness = np.array([2.0, 2.0, 4.0, np.nan])
    found = support_intervals_mm(offsets, thickness, [(0, 3), (3, 4)])
    assert found[0].tolist() == [
        -3.0,
        3.0,
    ]  # a gap between planes stays inside, uninterpolated
    assert np.isnan(found[1]).all()  # a face cannot be placed without a thickness
    with pytest.raises(ValueError, match="thickness_must_match"):
        support_intervals_mm(offsets, thickness[:2], [(0, 1)])


@pytest.mark.parametrize(
    ("origins", "normal", "at", "name"),
    [
        (np.zeros(3), np.ones(3), 0, "invalid_slice_origins"),
        (np.array([[np.nan, 0, 0]]), np.ones(3), 0, "invalid_slice_origins"),
        (np.zeros((2, 3)), np.zeros(3), 0, "invalid_series_normal"),
        (np.zeros((2, 3)), np.ones(3), 5, "invalid_slice_index"),
    ],
)
def test_depth_refuses_what_it_cannot_place(origins, normal, at, name):
    with pytest.raises(ValueError, match=name):
        depth_offsets_mm(origins, normal, at)
