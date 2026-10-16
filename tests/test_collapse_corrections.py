"""The corrections to the fibula case, each pinned through the function a run calls.

1. A finer block's median is read over its footprint, which crosses tile boundaries, so the squint's
   tile extrema exclude it only over every tile the footprint can touch (`footprint_reach`); the
   consumer, `fibula_profile`, reads finely where a crossing block can hold the level, and an
   exclusion beside an unseen tile is an unknown and never an absence.
2. The finer readings are kept as ragged native windows, and every plane the profile pointed to keeps
   its lens readings.
3. Raw pointer support, confirmed extent and unresolved candidate ranges are kept apart; a run the
   established rule rejected is never the bone's extent; runs are envelopes over sampled slabs.
4. An observation names the artifact, row or label that holds its places; a transfer or projection
   that could not be made is an unresolved saying, never skipped.
5. The head's walk is made once for one measurement and handed to its callers whole, never aliased
   across another light, series or place.
"""

from __future__ import annotations

import json
from dataclasses import replace
from math import ceil
from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pytest

from knee.collapse.observations import Observation, Unresolved, unresolved_rows
from knee.collapse.physical import PlaneFrame, physical_squint
from knee.collapse.profile import (
    FineReading,
    block_medians,
    block_pixels,
    could_hold_level,
    could_hold_level_in_reach,
    footprint_reach,
    over_reach,
    pack_fine_readings,
    run_slabs_mm,
    slab_gaps_mm,
    support_intervals_mm,
)
from knee.objects import assignments as A
from knee.telemetry import computing, recording
from scripts import run_interiors as run

BODY = A.FIBULA_POINTER_STATUS
LEVEL = A.LIKE_THE_TIBIA


def grid(rows: int, cols: int, tile: int) -> np.ndarray:
    """The squint's own bounds for a plane, tiles `tile` pixels, the last cut by the edge."""
    down, across = ceil(rows / tile), ceil(cols / tile)
    out = np.empty((down, across, 4), dtype=np.int64)
    for r in range(down):
        for c in range(across):
            out[r, c] = (
                r * tile,
                min(rows, (r + 1) * tile),
                c * tile,
                min(cols, (c + 1) * tile),
            )
    return out


# -- 1. the footprint ---------------------------------------------------------------------------


def test_the_reach_of_a_tile_is_the_tiles_a_block_with_a_pixel_in_it_can_touch():
    bounds = grid(14, 14, 7)
    two = footprint_reach(bounds, (2, 2))
    assert two.rows.tolist() == [
        [0, 1],
        [0, 1],
    ]  # a 2 px block starting at pixel 6 reads 7
    one = footprint_reach(bounds, (1, 1))
    assert one.rows.tolist() == [[0, 0], [1, 1]] and one.cols.tolist() == [
        [0, 0],
        [1, 1],
    ]
    # a cut last tile, and three tiles of reach for a block wider than a tile
    cut = footprint_reach(grid(23, 23, 10), (3, 3))
    assert cut.rows.tolist() == [[0, 1], [0, 2], [1, 2]]
    wide = footprint_reach(grid(23, 23, 10), (12, 12))
    assert wide.rows.tolist() == [[0, 2], [0, 2], [0, 2]]


def test_a_malformed_grid_or_block_is_refused_by_name():
    with pytest.raises(ValueError, match="invalid_bounds"):
        footprint_reach(np.zeros((2, 2)), (2, 2))
    with pytest.raises(ValueError, match="invalid_block_px"):
        footprint_reach(grid(14, 14, 7), (0, 2))
    skewed = grid(14, 14, 7)
    skewed[0, 1, 0] = 1  # one tile of a row does not share the row's bounds
    with pytest.raises(ValueError, match="tile_grid_is_not_regular"):
        footprint_reach(skewed, (2, 2))
    reach = footprint_reach(grid(14, 14, 7), (2, 2))
    with pytest.raises(ValueError, match="values_must_be_the_tile_grid"):
        over_reach(np.zeros((3, 3)), reach, np.fmax)


def test_the_baselines_counterexample_two_tiles_miss_the_level_and_a_crossing_block_holds_it():
    """data/readings/collapse-20261016/baseline/profile-contract-counterexample.json, executed."""
    plane = np.array([[0.3, 0.3, 0.7, 0.7], [0.3, 0.3, 0.7, 0.7]])
    squint = physical_squint(plane, (1.0, 1.0), 2.0)
    assert squint.tile_shape_rc == (2, 2)
    own, _ = could_hold_level(squint.minimum, squint.maximum, 0.4, 0.6)
    assert own.tolist() == [[False, False]]  # one tile's own extrema exclude both
    fine = block_medians(plane, np.zeros((2, 4), bool), (1.0, 1.0), 2.0, (0, 2, 1, 3))
    assert fine.median.tolist() == [
        [0.5]
    ]  # the block across their boundary lies in the level
    reach = footprint_reach(squint.bounds_rc, block_pixels((1.0, 1.0), 2.0))
    could, blind = could_hold_level_in_reach(
        squint.minimum, squint.maximum, 0.4, 0.6, reach
    )
    assert could.tolist() == [[True, True]] and not blind.any()
    # a block that cannot cross (one pixel wide) is excluded exactly as before
    reach_one = footprint_reach(squint.bounds_rc, (1, 1))
    could, _ = could_hold_level_in_reach(
        squint.minimum, squint.maximum, 0.4, 0.6, reach_one
    )
    assert could.tolist() == [[False, False]]


@pytest.mark.parametrize("pitch", [0.7, 1.0, 1.5, 2.5])
def test_no_readable_block_in_the_level_lies_over_a_tile_the_reach_excluded(pitch):
    """Adversarial, over random planes, windows and levels, with the squint as production makes it
    (non-finite pixels missing): every tile any block in the level touches could hold it."""
    rng = np.random.default_rng(int(pitch * 100))
    spacing = (pitch, pitch * 1.3)
    for _ in range(40):
        plane = rng.choice([50.0, 150.0, 300.0, 650.0], size=(37, 43)) + rng.normal(
            0, 5, (37, 43)
        )
        plane[rng.random(plane.shape) < 0.02] = np.nan
        unseen = rng.random(plane.shape) < 0.02
        squint = physical_squint(plane, spacing, 10.0)
        block = block_pixels(spacing, 2.0)
        r0, c0 = int(rng.integers(0, 10)), int(rng.integers(0, 10))
        window = (r0, int(rng.integers(r0 + 4, 38)), c0, int(rng.integers(c0 + 4, 44)))
        low = float(rng.uniform(100, 400))
        high = low + float(rng.uniform(5, 300))
        reading = block_medians(plane, unseen, spacing, 2.0, window)
        reach = footprint_reach(squint.bounds_rc, block)
        could, _ = could_hold_level_in_reach(
            squint.minimum, squint.maximum, low, high, reach
        )
        rows_in, cols_in = np.nonzero(
            (reading.median >= low) & (reading.median <= high)
        )
        for i, j in zip(rows_in, cols_in, strict=True):
            rows = range(
                window[0] + i * block[0], min(window[0] + (i + 1) * block[0], window[1])
            )
            cols = range(
                window[2] + j * block[1], min(window[2] + (j + 1) * block[1], window[3])
            )
            for tr, tc in {
                (r // squint.tile_shape_rc[0], c // squint.tile_shape_rc[1])
                for r in rows
                for c in cols
            }:
                assert could[tr, tc]


def test_a_tile_beside_an_unseen_tile_is_blind_and_unseen_tiles_give_no_extremum():
    minimum = np.array([[200.0, np.nan]])
    maximum = np.array([[200.0, np.nan]])
    reach = footprint_reach(grid(7, 14, 7), (2, 2))
    could, blind = could_hold_level_in_reach(minimum, maximum, 300.0, 500.0, reach)
    assert not could.any()  # nothing seen can hold it
    assert blind.tolist() == [[True, True]]  # but an unseen tile is in reach of both
    far = footprint_reach(grid(7, 14, 7), (1, 1))
    _, blind = could_hold_level_in_reach(minimum, maximum, 300.0, 500.0, far)
    assert blind.tolist() == [
        [False, True]
    ]  # a block that cannot reach it is not blind


# -- 1. the consumer ------------------------------------------------------------------------------

PITCH = (
    1.5  # tiles of 7 px, blocks of 2 px: a block crosses the tile boundary at pixel 7
)
LIGHT = 400.0


def lens_frame() -> PlaneFrame:
    return PlaneFrame(
        np.zeros(3), np.array([[0.0, 1.5], [1.5, 0.0], [0.0, 0.0]]), (PITCH, PITCH)
    )


class Plain:
    """A series with a volume, for the profile's reads of native slices."""

    def __init__(self, uid: str, planes: list[np.ndarray]):
        self.row = SimpleNamespace(series_uid=uid)
        self.volume = planes
        self.geometry = None
        self.slice_thickness_mm: tuple = ()


def stack_of(planes, corridor_tiles, unseen=()):
    """A squint stack over `planes` made as production makes it, with every tile centre outboard of
    a right knee's tibia middle, behind it and below its top except where `corridor_tiles` says not."""
    squints = [physical_squint(p, (PITCH, PITCH), 10.0) for p in planes]
    tiles = squints[0].bounds_rc.shape[:2]
    centres = np.zeros((len(planes), *tiles, 3))
    centres[..., 0] = -30.0
    centres[..., 1] = 50.0
    centres[..., 2] = 50.0
    for i, j in set(np.ndindex(tiles)) - set(corridor_tiles):
        centres[:, i, j, 1] = -50.0  # in front of the tibia's middle: not the corridor
    minimum = np.stack([s.minimum.copy() for s in squints])
    maximum = np.stack([s.maximum.copy() for s in squints])
    for i, j in unseen:
        minimum[:, i, j] = maximum[:, i, j] = np.nan
    return SimpleNamespace(
        minimum=minimum,
        maximum=maximum,
        median=np.stack([s.median for s in squints]),
        bounds_rc=squints[0].bounds_rc,
        centres_lps=centres,
    )


def times(led, name: str) -> int:
    """How many events the ledger holds under `name`."""
    return sum(1 for event in led.events() if event.name == name)


def planes_of(led, name: str) -> int:
    """The planes the ledger counted under `name`, summed."""
    return sum(e.counts.get("planes", 0) for e in led.events() if e.name == name)


def profile_of(monkeypatch, planes, stack, medians, light=LIGHT):
    """`fibula_profile` over `planes`, the pointer replaced by a recorder so the consumer's own
    branch is what runs: it records the block medians it is handed and says a body is there."""
    frame = lens_frame()
    monkeypatch.setattr(run, "plane_frame", lambda s, z: frame)
    monkeypatch.setattr(
        run,
        "seen_native",
        lambda s, z, stage="x": (
            np.asarray(planes[z], float),
            np.zeros(planes[z].shape, bool),
        ),
    )

    def pointer(median, cell_mm, centres, tibia, middle, *args):
        medians.append(np.array(median))
        body = np.zeros(median.shape, bool)
        return A.FibulaPointer(BODY["body"], 100.0, np.zeros(3), body, body, 1)

    monkeypatch.setattr(run, "fibula_pointer", pointer)
    tibia = np.zeros(planes[0].shape, dtype=bool)
    tibia[0:3, 0:3] = True
    with computing(), recording() as led:
        got = run.fibula_profile(
            cast(Any, Plain("s", planes)),
            cast(Any, stack),
            tibia,
            (1, 1),
            light,
            100.0,
            np.array([0.0, 0.0, 90.0]),
            "R",
        )
    return got, led


def crossing_planes(count=2):
    """Left tile 0.5 of the light, right tile 1.5: both outside [0.75, 1.33] of it, and a 2 px block
    across the boundary (pixels 6 and 7) has median exactly the light."""
    plane = np.full((14, 14), 0.5 * LIGHT)
    plane[:, 7:] = 1.5 * LIGHT
    return [plane.copy() for _ in range(count)]


def test_the_consumer_reads_finely_where_a_crossing_block_can_hold_the_level(
    monkeypatch,
):
    planes = crossing_planes()
    stack = stack_of(planes, corridor_tiles=[(0, 0), (0, 1), (1, 0), (1, 1)])
    # each tile's own extrema exclude the level: the old branch would have said none and skipped
    own, _ = could_hold_level(
        stack.minimum[0], stack.maximum[0], LEVEL[0] * LIGHT, LEVEL[1] * LIGHT
    )
    assert not own.any()
    medians: list[np.ndarray] = []
    got, led = profile_of(monkeypatch, planes, stack, medians)
    assert len(medians) == 2  # the finer reading ran on both slices
    assert (got.status == BODY["body"]).all() and (got.area_mm2 == 100.0).all()
    assert (got.window_rc[:, 0] == 0).all() and got.block_px.tolist() == [
        [2, 2],
        [2, 2],
    ]
    crossing = medians[0][:, 3]  # pixels 6 and 7: the block the tiles cannot see
    assert crossing.tolist() == [LIGHT] * 7
    assert (medians[0][:, 0] == 0.5 * LIGHT).all() and (
        medians[0][:, 5] == 1.5 * LIGHT
    ).all()
    assert planes_of(led, "fibula.cheap_readings") == 2
    assert planes_of(led, "fibula.tile_exclusions") == 0
    # and what was read is kept, at its own small resolution
    assert [f.index for f in got.fine] == [0, 1] and got.fine[0].median.shape == (7, 7)
    assert np.array_equal(got.fine[1].median, medians[1])


def test_a_level_no_block_can_reach_is_still_measured_absent_and_skips_the_finer_reading(
    monkeypatch,
):
    plane = np.full((14, 14), 0.5 * LIGHT)  # nothing near the level anywhere
    stack = stack_of([plane], corridor_tiles=[(0, 0), (0, 1), (1, 0), (1, 1)])
    medians: list[np.ndarray] = []
    got, led = profile_of(monkeypatch, [plane], stack, medians)
    assert not medians and got.status[0] == BODY["none"] and got.area_mm2[0] == 0.0
    assert planes_of(led, "fibula.tile_exclusions") == 1 and not got.fine


def test_an_unseen_corridor_tile_is_unknown_never_absent(monkeypatch):
    plane = np.full((14, 14), 0.5 * LIGHT)
    stack = stack_of([plane], [(0, 0), (0, 1), (1, 0), (1, 1)], unseen=[(0, 1)])
    got, _ = profile_of(monkeypatch, [plane], stack, [])
    assert got.status[0] == BODY["unreadable"] and np.isnan(got.area_mm2[0])


def test_an_unseen_tile_a_block_could_touch_makes_an_exclusion_unknown_not_absent(
    monkeypatch,
):
    """The corridor is the left tiles only; the right tiles are unseen and in reach of a block of the
    left ones (a 2 px block at pixels 6 and 7). Their own extrema excluded the level and the old
    branch said none; what lies there cannot be said."""
    plane = np.full((14, 14), 0.5 * LIGHT)
    stack = stack_of([plane], corridor_tiles=[(0, 0), (1, 0)], unseen=[(0, 1), (1, 1)])
    got, _ = profile_of(monkeypatch, [plane], stack, [])
    assert got.status[0] == BODY["unreadable"] and np.isnan(got.area_mm2[0])
    assert got.corridor[0].tolist() == [
        [True, False],
        [True, False],
    ]  # the corridor is unchanged


def test_a_reversed_stack_reads_every_slice_the_same(monkeypatch):
    planes = crossing_planes(3)
    stack = stack_of(planes, [(0, 0), (0, 1), (1, 0), (1, 1)])
    forward, _ = profile_of(monkeypatch, planes, stack, [])
    again, _ = profile_of(monkeypatch, planes[::-1], stack, [])
    assert np.array_equal(forward.status, again.status[::-1])
    assert np.array_equal(forward.fine[0].median, again.fine[2].median)


# -- 2. the retained readings ---------------------------------------------------------------------


def unpack_fine_reading(packed: dict[str, np.ndarray], i: int) -> FineReading:
    """Test-only inverse of `pack_fine_readings` (nothing in production reads the packed readings)."""
    if not 0 <= i < len(packed["slices"]):
        raise ValueError("invalid_reading_index")
    a, b = int(packed["offsets"][i]), int(packed["offsets"][i + 1])
    shape = (int(packed["shapes"][i][0]), int(packed["shapes"][i][1]))
    window = packed["windows_rc"][i]
    return FineReading(
        int(packed["slices"][i]),
        (int(window[0]), int(window[1]), int(window[2]), int(window[3])),
        (int(packed["block_px"][i][0]), int(packed["block_px"][i][1])),
        (float(packed["block_mm"][i][0]), float(packed["block_mm"][i][1])),
        packed["median"][a:b].reshape(shape),
        packed["pointer_body"][a:b].reshape(shape),
        packed["tibia_reference"][a:b].reshape(shape),
    )


def fine(index, rows, cols, window, value):
    median = np.full((rows, cols), value)
    median[0, 0] = np.nan
    return FineReading(
        index,
        window,
        (2, 3),
        (2.0, 3.0),
        median,
        median > value - 1,
        np.zeros((rows, cols), bool),
    )


def test_ragged_fine_readings_round_trip_with_every_slice_explicit_and_nothing_padded():
    readings = [fine(4, 3, 5, (2, 8, 1, 16), 10.0), fine(9, 6, 2, (0, 12, 4, 10), 20.0)]
    packed = pack_fine_readings(readings)
    assert packed["slices"].tolist() == [4, 9]
    assert packed["shapes"].tolist() == [[3, 5], [6, 2]]
    assert packed["offsets"].tolist() == [0, 15, 27]
    assert (
        packed["median"].size == 27 == packed["pointer_body"].size
    )  # no padding to a common shape
    assert packed["windows_rc"].tolist() == [[2, 8, 1, 16], [0, 12, 4, 10]]
    assert packed["block_px"].tolist() == [[2, 3], [2, 3]]
    for i, original in enumerate(readings):
        back = unpack_fine_reading(packed, i)
        assert back.index == original.index and back.window_rc == original.window_rc
        assert np.array_equal(back.median, original.median, equal_nan=True)
        assert np.array_equal(back.body, original.body)
    with pytest.raises(ValueError, match="invalid_reading_index"):
        unpack_fine_reading(packed, 2)
    empty = pack_fine_readings([])
    assert empty["slices"].size == 0 and empty["offsets"].tolist() == [0]


# -- 3. raw pointer support, confirmed extent and candidate ranges -------------------------------

SAGITTAL = np.array(
    [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]]
)  # rows run back, columns up, slices left
SHAPE = (6, 6)
SPACING = 4.0  # millimetres between slice origins
SLAB = (
    2.0  # each slice's thickness: 2 mm sampled of every 4, so gaps of 2 mm lie between
)


def frame_at(z: int) -> PlaneFrame:
    return PlaneFrame(np.array([SPACING * z, 0.0, 0.0]), SAGITTAL, (1.0, 1.0))


class Stack:
    """A series stub with real geometry: nine slices one 4 mm step apart, normal along x."""

    def __init__(self, uid="sg", depth=9, thickness=SLAB, reverse=False):
        self.row = SimpleNamespace(
            series_uid=uid,
            fat_suppression="0",
            fluid_sensitive="0",
            anatomical_plane="Sagittal",
        )
        order = range(depth)[::-1] if reverse else range(depth)
        self.geometry = SimpleNamespace(
            position=[np.array([SPACING * z, 0.0, 0.0]) for z in order]
        )
        self.slice_thickness_mm = tuple([thickness] * depth)
        self.volume = [np.ones(SHAPE) for _ in range(depth)]


def profile_for(status, area, fine_readings=()):
    depth = len(status)
    return run.FibulaProfile(
        np.asarray(status, dtype=np.int8),
        np.asarray(area, dtype=float),
        np.full((depth, 3), np.nan),
        np.zeros(depth, dtype=np.int32),
        np.zeros((depth, 2, 2), bool),
        np.zeros((depth, 2, 2), bool),
        np.full((depth, 4), -1, dtype=np.int32),
        np.full((depth, 2), np.nan),
        np.full((depth, 2), -1, dtype=np.int32),
        tuple(fine_readings),
        LIGHT,
        100.0,
        np.array([0.0, 0.0, 90.0]),
    )


NOT_READ, NONE_, BODY_, UNREADABLE = 0, 1, 2, 3
# slices:                  0       1      2      3      4      5      6      7      8
STATUS = [NOT_READ, NONE_, BODY_, BODY_, NONE_, NONE_, BODY_, BODY_, NOT_READ]
AREA = [np.nan, 0.0, 30.0, 30.0, 0.0, 0.0, 10.0, 20.0, np.nan]
HEAD_AREAS = {
    3: 120.0,
    2: 100.0,
    1: 10.0,
}  # the walk from slice 3: a disc, a disc, then not


def heads(monkeypatch, areas=None):
    """`fibula_head` stood in for: a body in the corner of each slice and its area by slice."""
    areas = HEAD_AREAS if areas is None else areas
    calls: list[tuple[str, int, float]] = []

    def head(series, z, places, light):
        calls.append((series.row.series_uid, int(z), float(light)))
        body = np.zeros(SHAPE, bool)
        body[z % 6, :2] = True
        target = np.zeros(SHAPE, bool)
        target[0, 0] = True
        return body, target, "identified", float(areas.get(z, np.nan))

    monkeypatch.setattr(run, "fibula_head", head)
    return calls


def places_on(z: int) -> np.ndarray:
    return frame_at(z).to_patient(np.array([[2.0, 2.0], [3.0, 3.0]]))


def support_for(
    monkeypatch, accepted, status=STATUS, area=AREA, stack=None, planes=None
):
    stack = Stack() if stack is None else stack
    monkeypatch.setattr(run, "plane_frame", lambda s, z: frame_at(z))
    calls = heads(monkeypatch)
    profile = profile_for(status, area)
    runs = run.positive_runs(profile.area_mm2)
    maxima = run.run_maxima(profile.area_mm2, runs)
    pointed = sorted({int(z) for peaks in maxima for z in peaks})
    planes = pointed if planes is None else planes
    with computing(), recording() as led:
        got = run.fibula_support(
            cast(Any, stack),
            frame_at(4),
            frame_at(3),
            3,
            profile,
            (runs, maxima, []),
            planes,
            tuple(accepted),
            places_on(3),
            LIGHT,
            "R",
        )
    return got, calls, led


def test_a_rejected_pointer_run_is_a_candidate_never_confirmed_extent(monkeypatch):
    (support, arrays, ambiguities), _, _ = support_for(monkeypatch, accepted=(2, 3))
    raw = support["pointer_runs"]
    assert [r["slices"] for r in raw] == [
        [2, 3],
        [6, 7],
    ]  # the raw pointer support is whole
    assert [r["native_rule"] for r in raw] == [
        "confirmed_by_the_native_rule",
        "rejected_by_the_native_rule",
    ]
    assert [r["slices"] for r in support["confirmed_extent"]] == [[2, 3]]
    candidate = support["unresolved_candidate_ranges"]
    assert [c["slices"] for c in candidate] == [[6, 7]]
    assert candidate[0]["why"] == "rejected_by_the_native_rule"
    assert candidate[0]["pointer_area_mm2_greatest"] == 20.0
    status = arrays["a3_fibula_support_status"]
    assert status[6] == status[7] == run.UNCONFIRMED_CANDIDATE
    assert status[6] not in (BODY["body"], BODY["none"])
    assert (
        "a_pointer_run_the_native_rule_rejected_is_not_confirmed_extent" in ambiguities
    )
    assert arrays["a3_fibula_pointer_run_confirmation"].tolist() == [1, 2]
    assert arrays["a3_fibula_native_resolved_slices"].tolist() == [2, 3]


def test_not_read_is_never_measured_empty_and_an_unconfirmed_run_end_is_named(
    monkeypatch,
):
    (support, arrays, _), _, _ = support_for(monkeypatch, accepted=(2, 3))
    status = arrays["a3_fibula_support_status"]
    assert (
        status[0] == BODY["not_read"] and status[8] == BODY["not_read"]
    )  # not measured empty
    assert status[4] == status[5] == BODY["none"]  # measured empty, as read
    (extent,) = support["confirmed_extent"]
    # beyond slice 3 the profile measured empty; below slice 2 the head's walk measured a head
    # that is no longer a disc
    assert extent["ends"] == ["observed_end", "observed_end"]
    candidate = support["unresolved_candidate_ranges"][0]
    assert candidate["ends"] == [
        "observed_end",
        "beyond_the_corridor",
    ]  # slice 8 was never read


def test_a_run_read_natively_nowhere_is_named_not_read_and_a_confirmed_run_has_no_candidate(
    monkeypatch,
):
    # the second run's plane was never read (its frame could not be made)
    (support, arrays, ambiguities), _, _ = support_for(
        monkeypatch, accepted=(2, 3), planes=[2, 3]
    )
    assert support["unresolved_candidate_ranges"][0]["why"] == "not_read_natively"
    assert "a_pointer_run_not_read_natively_is_not_confirmed_extent" in ambiguities
    assert arrays["a3_fibula_pointer_run_confirmation"].tolist() == [1, 3]
    (support, _, _), _, _ = support_for(monkeypatch, accepted=(2, 3, 7))
    assert support["unresolved_candidate_ranges"] == []
    assert [r["slices"] for r in support["confirmed_extent"]] == [[2, 3], [6, 7]]


def test_a_natively_identified_plane_is_support_even_where_the_pointer_saw_a_cut(
    monkeypatch,
):
    status = list(STATUS)
    status[6] = status[7] = 4  # the window cut the body: unknown by the pointer
    area = list(AREA)
    area[6] = area[7] = np.nan
    (support, arrays, _), _, _ = support_for(
        monkeypatch, accepted=(2, 3), status=status, area=area
    )
    assert [r["slices"] for r in support["pointer_runs"]] == [[2, 3]]
    assert (
        arrays["a3_fibula_support_status"][6] == 4
    )  # unknown stays unknown, never absence
    assert support["unknown_slices"] == [6, 7]


def test_runs_are_envelopes_over_sampled_slabs_with_their_gaps_never_dense_occupancy(
    monkeypatch,
):
    (support, arrays, _), _, _ = support_for(monkeypatch, accepted=(2, 3))
    first, second = support["pointer_runs"]
    # slices 2 and 3: slabs [7, 9] and [11, 13] about the main slice's origin at 12 -> offsets -4, 0
    assert first["sampled_slices"] == [2, 3]
    assert first["slabs_mm"] == [[-5.0, -3.0], [-1.0, 1.0]]
    assert first["gaps_mm"] == [2.0]  # 2 mm between the planes was never sampled
    assert first["envelope_mm"] == [-5.0, 1.0]  # the envelope spans the gap unmeasured
    assert first["occupancy"] == "envelope_over_the_sampled_slabs_never_dense"
    assert second["envelope_mm"] == [11.0, 17.0] and second["gaps_mm"] == [2.0]
    assert arrays["a3_fibula_slab_mm"].shape == (9, 2)
    assert arrays["a3_fibula_pointer_run_envelope_mm"].tolist() == [
        [-5.0, 1.0],
        [11.0, 17.0],
    ]


def test_slabs_follow_physical_order_in_a_reversed_unequal_and_unthick_stack():
    offsets = np.array([6.0, 2.0, 1.0, np.nan])
    thickness = np.array([2.0, 2.0, 4.0, 2.0])
    (slabs,) = run_slabs_mm(offsets, thickness, [(0, 3)])
    assert slabs.tolist() == [[-1.0, 3.0], [1.0, 3.0], [5.0, 7.0]]  # sorted by position
    assert slab_gaps_mm(slabs).tolist() == [
        -2.0,
        2.0,
    ]  # an overlap is negative, a gap positive
    assert support_intervals_mm(offsets, thickness, [(0, 3)]).tolist() == [[-1.0, 7.0]]
    (unknown,) = run_slabs_mm(offsets, np.array([2.0, 2.0, 4.0, np.nan]), [(2, 4)])
    assert np.isnan(unknown[-1]).all() and np.isnan(slab_gaps_mm(unknown)).all()
    with pytest.raises(ValueError, match="thickness_must_match"):
        run_slabs_mm(offsets, thickness[:2], [(0, 1)])
    with pytest.raises(ValueError, match="slabs_are_low_high_pairs"):
        slab_gaps_mm(np.zeros(3))


def test_a_reversed_stack_gives_the_same_envelopes_in_physical_millimetres(monkeypatch):
    forward, _, _ = support_for(monkeypatch, accepted=(2, 3))
    # the same physical stack stored in the other order: slice z of the stub is physical slice 8 - z
    flipped_status, flipped_area = STATUS[::-1], AREA[::-1]
    stack = Stack(reverse=True)
    monkeypatch.setattr(run, "plane_frame", lambda s, z: frame_at(8 - z))
    calls = heads(monkeypatch, {8 - z: a for z, a in HEAD_AREAS.items()})
    profile = profile_for(flipped_status, flipped_area)
    runs = run.positive_runs(profile.area_mm2)
    maxima = run.run_maxima(profile.area_mm2, runs)
    with computing():
        (support, _, _) = run.fibula_support(
            cast(Any, stack),
            frame_at(4),
            frame_at(5),
            5,
            profile,
            (runs, maxima, []),
            sorted({int(z) for p in maxima for z in p}),
            (5, 6),
            places_on(3),
            LIGHT,
            "R",
        )
    assert calls  # the walk read heads
    envelopes = sorted(tuple(r["envelope_mm"]) for r in support["pointer_runs"])
    assert envelopes == sorted(
        tuple(r["envelope_mm"]) for r in forward[0]["pointer_runs"]
    )


# -- 5. the head's walk, once --------------------------------------------------------------------


def biceps_world(monkeypatch, uid="sg", knee="R"):
    series = Stack(uid)
    own = SimpleNamespace(
        series=series,
        record={
            "series_uid": uid,
            "slice_index": 4,
            "assignments": {"knee": knee, "codes": {}},
            "background_split": 1.0,
        },
        frame=frame_at(4),
    )
    twin = SimpleNamespace(
        series=SimpleNamespace(
            row=SimpleNamespace(series_uid="fs", fat_suppression="1")
        ),
        record={"series_uid": "fs"},
    )
    monkeypatch.setattr(run, "plane_frame", lambda s, z: frame_at(z))
    monkeypatch.setattr(run, "biceps_twin", lambda *a: (np.ones(SHAPE), 5))
    monkeypatch.setattr(
        run,
        "read_part_slice",
        lambda *a: (
            {"assignments": {"codes": {}}, "series_uid": uid},
            {"acquired_plane": np.ones(SHAPE)},
            None,
        ),
    )
    monkeypatch.setattr(
        run,
        "seen_native",
        lambda s, z, stage="x": (np.ones(SHAPE), np.zeros(SHAPE, bool)),
    )
    monkeypatch.setattr(run, "measures_of", lambda *a: None)
    monkeypatch.setattr(
        run,
        "proximal_biceps_on_slice",
        lambda *a: (np.zeros(SHAPE, bool), {"contrast": np.zeros(2)}, "identified"),
    )
    return own, twin


def shared_fibula(own, twin_uid="fs", light=LIGHT):
    places = places_on(3)
    arrays: dict[str, np.ndarray] = {}
    record = {"series_uid": own.record["series_uid"], "slice_index": 3}
    return run.FibulaFound(
        record,
        arrays,
        frame_at(3),
        places,
        places,
        light,
        own.record["series_uid"],
        3,
        (),
        twin_uid,
        5,
        light,
    )


def test_the_walk_is_made_once_for_the_fibula_and_the_biceps_and_the_bodies_are_kept(
    monkeypatch,
):
    own, twin = biceps_world(monkeypatch)
    walks = []
    real = run.lateral_to_the_head
    monkeypatch.setattr(
        run, "lateral_to_the_head", lambda *a: walks.append(1) or real(*a)
    )
    calls = heads(monkeypatch)
    found = shared_fibula(own)
    profile = profile_for(STATUS, AREA)
    runs = run.positive_runs(profile.area_mm2)
    maxima = run.run_maxima(profile.area_mm2, runs)
    with computing(), recording() as led:
        support, arrays, _ = run.fibula_support(
            cast(Any, own.series),
            frame_at(4),
            frame_at(3),
            3,
            profile,
            (runs, maxima, []),
            [2, 3, 7],
            (2, 3),
            found.places,
            LIGHT,
            "R",
        )
        got = run.biceps_native(cast(Any, own), cast(Any, twin), found.places, found)
    assert not isinstance(got, str)
    assert len(walks) == 1  # one walk for both callers
    assert [c[1] for c in calls] == [3, 2, 1]  # one head per slice the walk reached
    assert times(led, "head_walk.made") == 1 and times(led, "head_walk.handed_on") == 1
    # both callers hold the same heads: the biceps's record is the fibula's walk
    biceps = got[1]
    assert biceps["a2_biceps_head_slices"].tolist() == [3, 2, 1]
    assert arrays["a3_fibula_head_walked_slices"].tolist() == [3, 2, 1]
    assert np.array_equal(
        biceps["a2_biceps_head_bodies"], arrays["a3_fibula_head_bodies"]
    )
    assert np.array_equal(
        biceps["a2_biceps_head_targets"], arrays["a3_fibula_head_targets"]
    )
    assert support["head"]["walked"] == [3, 2, 1]
    assert support["head"]["face_slice"] == 1 and support["head"]["slices"] == [2, 3]


def test_the_heads_are_kept_in_the_fibulas_record_even_when_the_biceps_abstains(
    monkeypatch,
):
    own, _ = biceps_world(monkeypatch)
    heads(monkeypatch)
    found = shared_fibula(own)
    profile = profile_for(STATUS, AREA)
    runs = run.positive_runs(profile.area_mm2)
    maxima = run.run_maxima(profile.area_mm2, runs)
    with computing():
        _, arrays, _ = run.fibula_support(
            cast(Any, own.series),
            frame_at(4),
            frame_at(3),
            3,
            profile,
            (runs, maxima, []),
            [2, 3, 7],
            (2, 3),
            found.places,
            LIGHT,
            "R",
        )
        assert (
            run.biceps_native(cast(Any, own), None, found.places, found)
            == "abstain_no_fat_suppressed_twin"
        )
    assert arrays["a3_fibula_head_bodies"].shape == (3, *SHAPE)
    assert arrays["a3_fibula_head_targets"].shape == (3, *SHAPE)
    assert arrays["a3_fibula_head_walked_slices"].tolist() == [3, 2, 1]


def test_another_light_series_or_place_is_another_walk_never_an_alias(monkeypatch):
    series = Stack("sg")
    calls = heads(monkeypatch)
    origins = np.array([np.asarray(p, float) for p in series.geometry.position])
    normal = frame_at(0).normal()
    thick = list(series.slice_thickness_mm)
    places = places_on(3)
    with computing(), recording() as led:
        first = run.head_walk(
            cast(Any, series), places, "R", origins, normal, thick, lambda: LIGHT
        )
        same = run.head_walk(
            cast(Any, series), places, "R", origins, normal, thick, lambda: LIGHT
        )
        light = run.head_walk(
            cast(Any, series), places, "R", origins, normal, thick, lambda: 399.0
        )
        again = run.head_walk(
            cast(Any, series), places, "R", origins, normal, thick, lambda: 399.0
        )
        other = run.head_walk(
            cast(Any, Stack("other")),
            places,
            "R",
            origins,
            normal,
            thick,
            lambda: LIGHT,
        )
        moved = run.head_walk(
            cast(Any, series), places_on(2), "R", origins, normal, thick, lambda: LIGHT
        )
        thin = run.head_walk(
            cast(Any, series),
            places,
            "R",
            origins,
            normal,
            [None, *thick[1:]],
            lambda: LIGHT,
        )
    assert same is first and again is light
    assert light is not first and other is not first and moved is not first
    assert first.light == LIGHT and light.light == 399.0
    assert (
        len(calls) == 3 + 3 + 3 + 2
    )  # each distinct measurement walked once; none for `thin`
    assert times(led, "head_walk.made") == 5 and times(led, "head_walk.handed_on") == 2
    assert thin.code != "identified"  # unknown thickness is not the same measurement


def test_a_walk_that_abstains_before_any_head_asks_for_no_light(monkeypatch):
    series = Stack("sg")
    heads(monkeypatch)
    origins = np.array([np.asarray(p, float) for p in series.geometry.position])
    normal = frame_at(0).normal()

    def never() -> float:
        raise AssertionError("the light was asked of for a walk that read no head")

    with computing():
        got = run.head_walk(
            cast(Any, series),
            places_on(3),
            "",
            origins,
            normal,
            list(series.slice_thickness_mm),
            never,
        )
    assert (
        got.code == "abstain_header_names_no_knee"
        and got.walked == ()
        and got.light is None
    )


# -- 2 and 3. through find_fibula -----------------------------------------------------------------

TIBIA = 1
LABELS_OF = {
    2: (3, 400.0),
    3: (4, 500.0),
}  # slice: (territory the rule names, its area)


def fibula_scene(monkeypatch):
    """`find_fibula` through its own code, the lens, the field and the established rule stood in for
    by what each plane's labels say: the pointer pointed to slices 2, 3 and 7; the rule named the
    fibula on 2 and 3 and not on 7."""
    series = Stack("sg", depth=9)
    record = {
        "series_uid": "sg",
        "slice_index": 4,
        "background_split": 1.0,
        "view": ["Sagittal", "0", "0"],
        "assignments": {
            "knee": "R",
            "tibia": TIBIA,
            "peaks": [{"territory": TIBIA, "peak_rc": [2, 2]}],
            "codes": {},
        },
    }
    objects = np.zeros(SHAPE, dtype=np.int8)
    objects[:3, :3] = A.OBJECT_CODES["tibia"]
    arrays = {"a1_objects": objects, "acquired_plane": np.full(SHAPE, LIGHT)}
    planes_read: list[int] = []

    def read_part_slice(series_, z, plane, frame, split, knee, reader):
        planes_read.append(int(z))
        labels = np.full(SHAPE, z + 1, dtype=np.int32)
        return (
            {
                "series_uid": "sg",
                "view": ["Sagittal", "0", "0"],
                "slice_index": z,
                "interiors": {"code": "ok", "territories": z + 1},
                "assignments": {
                    "knee": "R",
                    "codes": {"tibia": "x", "fibula": "y"},
                    "peaks": [{"territory": z + 1, "peak_rc": [1, 1]}],
                },
            },
            {
                "acquired_plane": np.full(SHAPE, float(z)),
                "b1_labels": labels,
                "b1_distance_mm": np.full(SHAPE, z / 10.0),
                "b1_dark": np.zeros(SHAPE, bool),
                "b1_markers": labels.copy(),
                "b1_available": np.ones(SHAPE, bool),
                "a1_objects": np.zeros(SHAPE, dtype=np.int8),
            },
            SimpleNamespace(in_plane=(False, True, True)),
        )

    monkeypatch.setattr(run, "plane_frame", lambda s, z: frame_at(z))
    monkeypatch.setattr(run, "read_part_slice", read_part_slice)
    monkeypatch.setattr(
        run,
        "fibula_on_slice",
        lambda labels, *a: LABELS_OF.get(int(labels[0, 0]) - 1, (None, 0.0)),
    )
    monkeypatch.setattr(
        run,
        "seen_native",
        lambda s, z, stage="x": (np.ones(SHAPE), np.zeros(SHAPE, bool)),
    )
    monkeypatch.setattr(
        run, "measures_of", lambda *a: SimpleNamespace(light=lambda mask: LIGHT)
    )
    profile = profile_for(STATUS, AREA)
    monkeypatch.setattr(run, "fibula_profile", lambda *a: profile)
    heads(monkeypatch)
    # the plane the walk starts from is slice 3 once the rule names it on the largest region
    stack = SimpleNamespace(code="present")
    return series, record, arrays, stack, planes_read


@pytest.mark.parametrize("anchor", [float("nan"), float("inf"), 0.0, -400.0])
def test_a_marrow_anchor_that_is_not_positive_and_finite_leaves_the_corridor_unreadable(
    monkeypatch, anchor
):
    """Every comparison with such a light is false, so the tiles would all read as excluding it;
    the exclusion is the consumer's own branch and must not say absent, nor read finely."""
    plane = np.full((14, 14), 0.5 * LIGHT)
    stack = stack_of([plane], [(0, 0), (0, 1), (1, 0), (1, 1)])
    medians: list[np.ndarray] = []
    got, led = profile_of(monkeypatch, [plane], stack, medians, light=anchor)
    assert got.status[0] == BODY["unreadable"] and np.isnan(got.area_mm2[0])
    assert (
        not medians and not got.fine and planes_of(led, "fibula.tile_exclusions") == 0
    )


def test_a_failed_fibula_keeps_its_profile_and_pointed_readings_in_the_middle_record(
    monkeypatch,
):
    series, record, arrays, stack, planes_read = fibula_scene(monkeypatch)
    monkeypatch.setattr(run, "fibula_on_slice", lambda labels, *a: (None, 0.0))
    with computing():
        found = run.find_fibula(cast(Any, series), record, arrays, cast(Any, stack))
    assert isinstance(found, str)
    kept = record["fibula_profile_retained"]
    assert kept["outcome"] == found and kept["lens_read_slices"] == planes_read
    assert kept["pointed_slices"] == planes_read
    assert arrays["a3_fibula_other_plane_slices"].tolist() == planes_read
    assert arrays["a3_fibula_other_plane_labels"].shape == (len(planes_read), *SHAPE)
    assert arrays["a3_fibula_profile_status"].shape == (9,)
    assert "a3_fibula_fine_slices" in arrays  # the finer readings are not thrown away


def test_every_pointed_plane_keeps_its_readings_and_the_rule_decides_what_is_extent(
    monkeypatch, tmp_path
):
    series, record, arrays, stack, planes_read = fibula_scene(monkeypatch)
    with computing():
        found = run.find_fibula(cast(Any, series), record, arrays, cast(Any, stack))
    assert not isinstance(found, str)
    assert planes_read == [2, 3, 7]  # each pointed plane read once, no others
    assert found.slice_index == 3  # the rule's largest region
    kept = found.arrays
    assert kept["a3_fibula_detailed_slices"].tolist() == [2, 3, 7]
    assert kept["a3_fibula_detailed_territories"].tolist() == [3, 4, -1]
    assert kept["a3_fibula_other_plane_slices"].tolist() == [2, 7]
    for name in run.OTHER_PLANE_READINGS:
        stacked = kept[f"a3_fibula_other_plane_{name}"]
        assert stacked.shape == (2, *SHAPE)
    # the very arrays the lens made, not another reading of them
    assert np.array_equal(kept["a3_fibula_other_plane_labels"][0], np.full(SHAPE, 3))
    assert np.array_equal(
        kept["a3_fibula_other_plane_distance_mm"][1], np.full(SHAPE, 0.7)
    )
    # the selected plane's readings are the record's own arrays
    assert np.array_equal(kept["b1_labels"], np.full(SHAPE, 4))
    table = found.record["main_slice"]["pointed_planes"]
    assert [(p["slice"], p["identified"], p["selected"]) for p in table] == [
        (2, True, False),
        (3, True, True),
        (7, False, False),
    ]
    assert table[0]["readings"]["row"] == 0 and table[2]["readings"]["row"] == 1
    assert table[1]["readings"]["row"] is None
    assert table[2]["readings"]["arrays"][0] == "a3_fibula_other_plane_labels"
    assert table[2]["peaks"] == [{"territory": 8, "peak_rc": [1, 1]}]
    # the rule rejected the run at 6-7: a candidate, and the identified plane 2 is confirmed support
    support = found.record["main_slice"]["support"]
    assert [c["slices"] for c in support["unresolved_candidate_ranges"]] == [[6, 7]]
    assert support["native_resolved_slices"] == [2, 3]
    assert kept["a3_fibula_support_status"][6] == run.UNCONFIRMED_CANDIDATE
    assert found.record["main_slice"]["status_codes"]["unconfirmed_candidate"] == (
        run.UNCONFIRMED_CANDIDATE
    )
    # the whole record saves and is plain JSON
    (tmp_path / "study").mkdir()
    saved = run.save(tmp_path, "study", found.record, found.arrays)
    json.dumps(saved, default=run.plain)
    assert saved["artifact"] == "study/sg-fibula.npz"
    with np.load(tmp_path / saved["artifact"]) as stored:
        assert stored["a3_fibula_other_plane_labels"].shape == (2, *SHAPE)


def test_the_observations_name_where_every_place_is_kept_and_what_could_not_be_said(
    monkeypatch,
):
    series, record, arrays, stack, _ = fibula_scene(monkeypatch)
    with computing():
        found = run.find_fibula(cast(Any, series), record, arrays, cast(Any, stack))
    assert not isinstance(found, str)
    found.record["artifact"] = "study/sg-fibula.npz"
    missing = SimpleNamespace(
        series=SimpleNamespace(
            row=SimpleNamespace(series_uid="nogeom"),
            volume=[np.ones(SHAPE)],
            geometry=None,
        ),
        record={"series_uid": "nogeom", "view": ["Coronal", "1", "1"]},
        frame=frame_at(0),
    )
    thickless = SimpleNamespace(
        series=SimpleNamespace(
            row=SimpleNamespace(series_uid="nothick"),
            volume=[np.ones(SHAPE)],
            geometry=SimpleNamespace(position=[np.zeros(3)]),
            slice_thickness_mm=(None,),
        ),
        record={"series_uid": "nothick", "view": ["Axial", "1", "1"]},
        frame=frame_at(0),
    )
    novolume = SimpleNamespace(
        series=SimpleNamespace(
            row=SimpleNamespace(series_uid="novol"),
            volume=None,
            geometry=SimpleNamespace(position=[np.zeros(3)]),
            slice_thickness_mm=(2.0,),
        ),
        record={"series_uid": "novol", "view": ["Axial", "0", "0"]},
        frame=frame_at(0),
    )
    own = SimpleNamespace(
        series=series,
        record={"series_uid": "sg", "view": ["Sagittal", "0", "0"]},
        frame=frame_at(3),
    )
    seen, unresolved = run.fibula_observations(
        cast(Any, own),
        found,
        None,
        None,
        [cast(Any, m) for m in (own, missing, thickless, novolume)],
    )
    by = {(o.provenance, o.kind, o.code, o.slices): o for o in seen}
    main = by[("native", "resolved", "identified", (3,))]
    assert (main.support, main.row, main.label) == (
        "a1_objects",
        None,
        A.OBJECT_CODES["fibula"],
    )
    assert main.artifact == "study/sg-fibula.npz"
    other = by[("native", "resolved", "identified", (2,))]
    assert (other.support, other.row, other.label) == (
        "a3_fibula_detailed_regions",
        0,
        None,
    )
    rejected = by[
        ("native", "reading", "pointed_plane_rejected_by_the_native_rule", (7,))
    ]
    assert (rejected.support, rejected.row) == ("a3_fibula_other_plane_labels", 1)
    confirmed = by[("native", "reading", "pointer_body", (2, 3))]
    unconfirmed = by[("native", "reading", "pointer_body_unconfirmed", (6, 7))]
    assert confirmed.artifact == unconfirmed.artifact == "study/sg-fibula.npz"
    assert {o.provenance for o in seen} == {
        "native"
    }  # no other sequence and no projectable series
    # the row selects what the receipt can follow: the support array and the row both exist
    kept = found.arrays
    assert kept[other.support].shape[0] == 3 and kept[rejected.support].shape[0] == 2
    assert [(u.provenance, u.series_uid, u.code) for u in unresolved] == [
        ("laid", None, "none_of_the_other_sequence"),
        ("projected", "nogeom", "geometry_unreadable"),
        # the two axial series are asked natively too, and say why they cannot be
        ("native", "nothick", "no_slice_thickness"),
        ("projected", "nothick", "no_slice_thickness"),
        ("native", "novol", "no_stacked_volume"),
        ("projected", "novol", "no_stacked_volume"),
    ]
    assert unresolved_rows(unresolved)[1]["view"] == ("Coronal", "1", "1")


def test_a_failed_transfer_and_a_projection_that_can_be_made_are_both_kept(monkeypatch):
    series, record, arrays, stack, _ = fibula_scene(monkeypatch)
    with computing():
        found = run.find_fibula(cast(Any, series), record, arrays, cast(Any, stack))
    assert not isinstance(found, str)
    found.record["artifact"] = "study/sg-fibula.npz"
    own = SimpleNamespace(
        series=series,
        record={"series_uid": "sg", "view": ["Sagittal", "0", "0"]},
        frame=frame_at(3),
    )
    partner = SimpleNamespace(
        series=SimpleNamespace(
            row=SimpleNamespace(series_uid="fs"),
            volume=[np.ones(SHAPE)] * 2,
            geometry=SimpleNamespace(
                position=[np.array([0.0, 0, 0]), np.array([100.0, 0, 0])]
            ),
            slice_thickness_mm=(2.0, 2.0),
        ),
        record={"series_uid": "fs", "view": ["Sagittal", "1", "1"]},
        frame=frame_at(0),
    )
    seen, unresolved = run.fibula_observations(
        cast(Any, own),
        found,
        cast(Any, partner),
        "abstain_twin_has_no_slice_at_this_place",
        [cast(Any, own), cast(Any, partner)],
    )
    assert [(u.provenance, u.series_uid, u.code) for u in unresolved] == [
        ("laid", "fs", "abstain_twin_has_no_slice_at_this_place"),
        ("native", None, "no_axial_series"),
    ]
    (target,) = [o for o in seen if o.provenance == "projected"]
    assert target.kind == "target" and target.series_uid == "fs"
    assert (
        target.artifact == "study/sg-fibula.npz"
        and target.support == "a3_fibula_places_lps"
    )
    assert target.code in ("on_the_slice", "between_slices", "beyond_the_scan")
    assert target.off_plane_mm is not None and target.off_plane_mm >= 0


def test_the_laid_observation_names_the_twins_own_artifact(monkeypatch):
    series, record, arrays, stack, _ = fibula_scene(monkeypatch)
    with computing():
        found = run.find_fibula(cast(Any, series), record, arrays, cast(Any, stack))
    assert not isinstance(found, str)
    found.record["artifact"] = "study/sg-fibula.npz"
    partner = SimpleNamespace(
        series=SimpleNamespace(
            row=SimpleNamespace(series_uid="fs"),
            volume=[np.ones(SHAPE)] * 2,
            geometry=SimpleNamespace(position=[np.zeros(3), np.array([100.0, 0, 0])]),
            slice_thickness_mm=(2.0, 2.0),
        ),
        record={"series_uid": "fs", "view": ["Sagittal", "1", "1"]},
        frame=frame_at(0),
    )
    own = SimpleNamespace(
        series=series,
        record={"series_uid": "sg", "view": ["Sagittal", "0", "0"]},
        frame=frame_at(3),
    )
    laid_objects = np.zeros(SHAPE, dtype=np.int8)
    laid_objects[1:3, 1:3] = A.OBJECT_CODES["fibula"]
    twin = (
        {
            "assignments": {"codes": {"fibula": "laid_from_its_partner"}},
            "artifact": "study/fs-fibula.npz",
        },
        {"a1_objects": laid_objects},
        0,
        1.0,
        5,
    )
    monkeypatch.setattr(run, "plane_frame", lambda s, z: frame_at(0))
    seen, unresolved = run.fibula_observations(
        cast(Any, own),
        found,
        cast(Any, partner),
        twin,
        [cast(Any, own), cast(Any, partner)],
    )
    (laid,) = [o for o in seen if o.provenance == "laid"]
    assert (
        laid.artifact == "study/fs-fibula.npz"
        and laid.label == A.OBJECT_CODES["fibula"]
    )
    assert laid.series_uid == "fs" and laid.count == 4 and laid.kind == "resolved"
    # no axial series in this study: named, not silent (the transfer itself succeeded)
    assert [(u.provenance, u.series_uid, u.code) for u in unresolved] == [
        ("native", None, "no_axial_series")
    ]
    assert laid.artifact != next(o for o in seen if o.provenance == "native").artifact


# -- 4. the observation schema --------------------------------------------------------------------


def watch(**kwargs):
    base: dict[str, Any] = {
        "object": "fibula",
        "provenance": "native",
        "kind": "resolved",
        "series_uid": "u",
        "view": ("S", "0", "0"),
        "slices": (3,),
        "code": "c",
        "count": 1,
        "off_plane_mm": 0.0,
        "support": "a",
        "note": "n",
    }
    base.update(kwargs)
    return Observation(**base)


def test_an_observation_addresses_its_array_by_artifact_row_or_label_and_refuses_the_rest():
    stacked = watch(artifact="study/u-fibula.npz", row=2)
    labelled = watch(artifact="study/u-fibula.npz", label=7)
    assert (stacked.row, labelled.label, watch().artifact) == (2, 7, None)
    with pytest.raises(ValueError, match="a_row_is_in_an_artifact"):
        watch(row=0)
    with pytest.raises(ValueError, match="a_label_selects_in_an_artifact"):
        watch(label=1)
    with pytest.raises(ValueError, match="a_row_is_an_index"):
        watch(artifact="a.npz", row=-1)
    # a target is still only projected, whatever it addresses
    with pytest.raises(ValueError, match="a_target_is_projected"):
        watch(kind="target", artifact="a.npz")


def test_an_unresolved_saying_is_a_transfer_or_a_projection_and_names_why():
    assert (
        Unresolved(
            "fibula", "laid", None, None, "none_of_the_other_sequence"
        ).series_uid
        is None
    )
    # a native reading asked of an axial series can be unresolved too; no other provenance is
    assert Unresolved("fibula", "native", "u", None, "x").provenance == "native"
    with pytest.raises(ValueError, match="only_a_transfer_or_a_projection"):
        Unresolved("fibula", "seen", "u", None, "x")
    with pytest.raises(ValueError, match="names_why"):
        Unresolved("fibula", "projected", "u", None, "")


def test_the_receipts_view_of_a_found_fibula_is_replaced_not_duplicated():
    # `replace` keeps the shared value whole: the twin's facts are added, the record is the same one
    found = shared_fibula(SimpleNamespace(record={"series_uid": "sg"}))
    again = replace(found, twin_uid="fs", twin_index=5)
    assert again.record is found.record and again.arrays is found.arrays
