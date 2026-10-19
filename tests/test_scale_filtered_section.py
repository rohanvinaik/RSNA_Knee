"""B0: the scale-filtered coarse section estimate, which the bones' axial key planes read.

`narrowest_breadth_mm` is a body's extent in its thinnest direction (the smallest width of the convex hull of its
blocks' corners); `scale_filtered_section` returns the unfiltered section exactly as `coarse_section` does, and
beside it the estimate: the touched bodies whose narrowest breadth is at least a floor, a lossy scale filter and
neither the cortex-enclosed section nor an identity proof. `axial_bone_planes` reads the estimate for the key
plane, the statuses and the femur's left-right scale, keeps the unfiltered arrays as they were, and packs the
estimate beside them.

The oracles are independent of the code under test: scipy's hull with the height over each edge, a sweep over
many projection angles, and a frozen copy of `coarse_section` as it was before the estimate existed.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import SimpleNamespace
from typing import cast

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra import numpy as hnp
from scipy import ndimage as ndi
from scipy.spatial import ConvexHull

import knee.collapse.coarse_section as section_module
from knee.collapse.coarse_section import (
    EMPTY,
    NO_BONE_SCALE,
    NOT_READ,
    SECTION,
    SEEDS_UNSEEN,
    SHARED,
    STATUS_CODES,
    CoarseSection,
    ScaleEstimate,
    TouchedComponent,
    coarse_section,
    narrowest_breadth_mm,
    pack_estimates,
    pack_sections,
    scale_filtered_section,
)
from knee.collapse.physical import PlaneFrame
from knee.collapse.profile import BlockReading
from knee.collapse.study_map import StudyMap
from scripts import run_interiors as run

BLOCK_MM = (2.0, 2.0)
BLOCK_AREA = 4.0
# The project's `BONE_MM`, given explicitly here: the unit tests of the function do not depend on it, and the
# runner is checked to pass `BONE_MM` itself.
FLOOR = 10.0
SHAPE = (24, 30)
# Blocks (row start, row end, column start, column end): a body 8 x 8 blocks (16 mm each way), and a strip 12
# blocks long and ONE block (2 mm) wide, two blocks away from it.
BODY = (4, 12, 4, 12)
STRIP = (4, 16, 14, 15)


def depth_of(*boxes: tuple[int, int, int, int], shape=SHAPE) -> np.ndarray:
    """A depth grid: 5.0 inside each box (so the cut level is 5.0 and the boxes are the bodies), 0.0 elsewhere."""
    depth = np.zeros(shape)
    for r0, r1, c0, c1 in boxes:
        depth[r0:r1, c0:c1] = 5.0
    return depth


def marks_at(*blocks: tuple[int, int], shape=SHAPE) -> np.ndarray:
    marks = np.zeros(shape, dtype=bool)
    for row, column in blocks:
        marks[row, column] = True
    return marks


def reference_coarse_section(
    depth: np.ndarray,
    seeds: np.ndarray,
    block_area_mm2: float,
    others: Mapping[str, np.ndarray] | None = None,
) -> CoarseSection:
    """`coarse_section` exactly as it was before the estimate existed (frozen: the oracle that the refactor onto
    a shared helper changed no output)."""
    grid = np.asarray(depth, dtype=np.float64)
    marks = np.asarray(seeds, dtype=bool)
    if marks.shape != grid.shape:
        raise ValueError("seeds_must_share_the_block_grid")
    if not marks.any():
        return CoarseSection(NOT_READ, None, float("nan"), float("nan"), marks)
    seen = np.isfinite(grid)
    held = marks & seen
    if not held.any():
        return CoarseSection(SEEDS_UNSEEN, None, float("nan"), float("nan"), marks)
    inside = held & (grid > 0)
    if not inside.any():
        return CoarseSection(EMPTY, None, 0.0, 0.0, marks)
    level = float(np.median(grid[inside]))
    labels, _ = ndi.label(seen & (np.where(seen, grid, 0.0) >= level))
    touched = np.unique(labels[held])
    touched = touched[touched > 0]
    if not len(touched):
        return CoarseSection(EMPTY, None, 0.0, level, marks)
    body = ndi.binary_fill_holes(np.isin(labels, touched)) & seen
    for other in (others or {}).values():
        if np.any(np.asarray(other, dtype=bool) & body):
            return CoarseSection(SHARED, None, float("nan"), level, marks)
    return CoarseSection(
        SECTION, body, float(body.sum()) * float(block_area_mm2), level, marks
    )


def same_section(first: CoarseSection, second: CoarseSection) -> None:
    assert first.status == second.status
    assert (first.body is None) == (second.body is None)
    if first.body is not None and second.body is not None:
        np.testing.assert_array_equal(first.body, second.body)
    np.testing.assert_array_equal(first.seeds, second.seeds)
    np.testing.assert_equal(first.area_mm2, second.area_mm2)
    np.testing.assert_equal(first.level, second.level)


def corners_mm(marks: np.ndarray, pitch) -> np.ndarray:
    rows, columns = np.nonzero(marks)
    return np.unique(
        np.concatenate(
            [
                np.column_stack(
                    ((rows + down) * pitch[0], (columns + across) * pitch[1])
                )
                for down in (0, 1)
                for across in (0, 1)
            ]
        ),
        axis=0,
    )


def hull_height_breadth(marks: np.ndarray, pitch) -> float:
    """An independent breadth: scipy's hull of every block corner, the greatest distance of a hull corner from
    each edge's line, the least of those."""
    points = corners_mm(marks, pitch)
    hull = points[ConvexHull(points).vertices]
    best = np.inf
    for index in range(len(hull)):
        start, end = hull[index], hull[(index + 1) % len(hull)]
        edge = end - start
        height = np.abs(
            edge[0] * (hull[:, 1] - start[1]) - edge[1] * (hull[:, 0] - start[0])
        ) / np.hypot(edge[0], edge[1])
        best = min(best, float(height.max()))
    return best


def swept_breadth(marks: np.ndarray, pitch, steps: int = 7200) -> float:
    """The least extent of the corners over many projection directions: never under the true breadth."""
    points = corners_mm(marks, pitch)
    angle = np.linspace(0.0, np.pi, steps, endpoint=False)
    along = points @ np.column_stack((np.cos(angle), np.sin(angle))).T
    return float((along.max(axis=0) - along.min(axis=0)).min())


# -- narrowest_breadth_mm -----------------------------------------------------------------------------------


@pytest.mark.parametrize("pitch", [(2.0, 3.0), (3.0, 2.0), (2.5, 2.5)])
def test_a_single_block_is_as_narrow_as_its_shorter_side(pitch):
    assert narrowest_breadth_mm(np.ones((1, 1), dtype=bool), pitch) == min(pitch)


def test_a_straight_line_of_blocks_has_its_width():
    assert narrowest_breadth_mm(np.ones((1, 7), dtype=bool), (2.0, 2.0)) == 2.0
    assert narrowest_breadth_mm(np.ones((4, 1), dtype=bool), (2.0, 2.0)) == 2.0
    # a line of four blocks 1 mm tall and 3 mm wide: 1 mm across it along the columns, 3 mm the other way
    assert narrowest_breadth_mm(np.ones((1, 4), dtype=bool), (1.0, 3.0)) == 1.0
    assert narrowest_breadth_mm(np.ones((4, 1), dtype=bool), (1.0, 3.0)) == 3.0


def test_an_l_shape_has_the_breadth_of_its_hull_and_not_of_its_arm():
    # three blocks: each arm is one block wide, the outline is two across
    tromino = np.array([[1, 0], [1, 1]], dtype=bool)
    assert narrowest_breadth_mm(tromino, (1.0, 1.0)) == 2.0
    # a long L, arms one block wide: its hull is broad, so this is not read as thin (a stated limit of the filter)
    ell = np.zeros((6, 6), dtype=bool)
    ell[:, 0] = True
    ell[5, :] = True
    got = narrowest_breadth_mm(ell, (2.0, 2.0))
    assert got == pytest.approx(hull_height_breadth(ell, (2.0, 2.0)), rel=1e-12)
    assert got > 2.0 * 2.0


def test_a_body_with_holes_has_the_breadth_of_its_outline():
    ring = np.ones((3, 3), dtype=bool)
    ring[1, 1] = False
    assert narrowest_breadth_mm(ring, (2.0, 2.0)) == 6.0
    lacy = np.ones((8, 8), dtype=bool)
    lacy[2:4, 2:4] = False
    lacy[5, 1] = False
    lacy[6, 6] = False
    lacy[0, 3] = False
    assert narrowest_breadth_mm(lacy, (2.0, 2.0)) == narrowest_breadth_mm(
        np.ones((8, 8), dtype=bool), (2.0, 2.0)
    )


def test_anisotropic_blocks_use_each_axes_own_size():
    assert narrowest_breadth_mm(np.ones((2, 4), dtype=bool), (1.0, 3.0)) == 2.0
    assert narrowest_breadth_mm(np.ones((5, 1), dtype=bool), (1.0, 3.0)) == 3.0


def test_breadth_agrees_with_independent_references_on_seeded_random_bodies():
    rng = np.random.default_rng(20261019)
    for _ in range(200):
        rows, columns = rng.integers(2, 26, size=2)
        grid = rng.random((rows, columns)) < rng.uniform(0.2, 0.95)
        if not grid.any():
            grid[rng.integers(rows), rng.integers(columns)] = True
        pitch = (float(rng.uniform(0.5, 4.0)), float(rng.uniform(0.5, 4.0)))
        got = narrowest_breadth_mm(grid, pitch)
        assert got == pytest.approx(hull_height_breadth(grid, pitch), rel=1e-9)
        sweep = swept_breadth(grid, pitch)
        # the sweep can only be over the true breadth, and a dense sweep is close to it
        assert got <= sweep + 1e-9
        assert sweep - got < 0.05 * max(got, 1.0)


grids = hnp.arrays(
    dtype=np.bool_,
    shape=st.tuples(st.integers(1, 7), st.integers(1, 7)),
).filter(lambda grid: bool(grid.any()))
pitches = st.tuples(st.floats(0.5, 4.0), st.floats(0.5, 4.0))


@settings(max_examples=60, deadline=None)
@given(grid=grids, pitch=pitches, down=st.integers(0, 4), across=st.integers(0, 4))
def test_breadth_does_not_depend_on_where_the_body_lies_or_on_transposing(
    grid, pitch, down, across
):
    moved = np.pad(grid, ((down, 1), (across, 2)))
    base = narrowest_breadth_mm(grid, pitch)
    assert narrowest_breadth_mm(moved, pitch) == pytest.approx(base, rel=1e-9)
    assert narrowest_breadth_mm(grid.T, (pitch[1], pitch[0])) == pytest.approx(
        base, rel=1e-9
    )


@settings(max_examples=60, deadline=None)
@given(grid=grids, pitch=pitches, data=st.data())
def test_breadth_never_falls_when_blocks_are_added_and_is_bounded_by_the_box(
    grid, pitch, data
):
    extra = data.draw(hnp.arrays(dtype=np.bool_, shape=grid.shape))
    base = narrowest_breadth_mm(grid, pitch)
    assert narrowest_breadth_mm(grid | extra, pitch) >= base - 1e-9
    rows, columns = np.nonzero(grid)
    box = (
        min(
            (rows.max() - rows.min() + 1) * pitch[0],
            (columns.max() - columns.min() + 1) * pitch[1],
        )
        + 1e-9
    )
    assert 0.0 < base <= box


def test_empty_and_malformed_components_are_refused_by_name():
    with pytest.raises(ValueError, match="empty_component"):
        narrowest_breadth_mm(np.zeros((3, 3), dtype=bool), BLOCK_MM)
    with pytest.raises(ValueError, match="empty_component"):
        narrowest_breadth_mm(np.zeros((0, 0), dtype=bool), BLOCK_MM)
    with pytest.raises(ValueError, match="component_must_be_2d"):
        narrowest_breadth_mm(np.ones(4, dtype=bool), BLOCK_MM)
    for bad in [(0.0, 2.0), (2.0, -1.0), (float("nan"), 2.0), (2.0, float("inf"))]:
        with pytest.raises(ValueError, match="invalid_block_mm"):
            narrowest_breadth_mm(np.ones((2, 2), dtype=bool), bad)
    with pytest.raises(ValueError, match="invalid_block_mm"):
        narrowest_breadth_mm(np.ones((2, 2), dtype=bool), (2.0,))


# -- scale_filtered_section ---------------------------------------------------------------------------------


def test_a_thin_strip_touched_beside_a_body_is_omitted_and_the_body_kept():
    depth = depth_of(BODY, STRIP)
    seeds = marks_at((6, 6), (10, 14))
    got = scale_filtered_section(depth, seeds, BLOCK_AREA, BLOCK_MM, FLOOR)
    # the unfiltered section is both bodies, as `coarse_section` reads it
    same_section(got.unfiltered, coarse_section(depth, seeds, BLOCK_AREA))
    assert got.unfiltered.status == SECTION
    assert got.unfiltered.body is not None and got.unfiltered.body.sum() == 64 + 12
    estimate = got.estimate
    assert estimate.status == SECTION and estimate.body is not None
    np.testing.assert_array_equal(estimate.body, depth_of(BODY) > 0)
    assert estimate.area_mm2 == 64 * BLOCK_AREA
    np.testing.assert_array_equal(estimate.omitted, depth_of(STRIP) > 0)
    assert [(c.blocks, c.kept) for c in estimate.components] == [
        (64, True),
        (12, False),
    ]
    assert estimate.components[0].breadth_mm == pytest.approx(16.0)
    assert estimate.components[1].breadth_mm == pytest.approx(2.0)
    assert estimate.floor_mm == FLOOR


def test_a_perforated_body_of_bone_breadth_is_kept_whole():
    depth = depth_of(BODY)
    depth[6:8, 6:8] = 0.0  # an enclosed hole
    depth[10, 5] = 0.0  # another
    depth[4, 8] = 0.0  # a notch open to the outside: not a hole
    # an unseen block inside: filled as a hole, but never part of a section
    depth[9, 9] = np.nan
    seeds = marks_at((5, 5))
    got = scale_filtered_section(depth, seeds, BLOCK_AREA, BLOCK_MM, FLOOR)
    same_section(got.unfiltered, coarse_section(depth, seeds, BLOCK_AREA))
    estimate = got.estimate
    assert estimate.status == SECTION and estimate.body is not None
    assert got.unfiltered.body is not None
    np.testing.assert_array_equal(estimate.body, got.unfiltered.body)
    assert estimate.body[6:8, 6:8].all() and estimate.body[10, 5]
    assert not estimate.body[4, 8] and not estimate.body[9, 9]
    assert not estimate.omitted.any()
    assert len(estimate.components) == 1 and estimate.components[0].kept
    assert estimate.components[0].breadth_mm == pytest.approx(16.0)


def test_a_body_exactly_at_the_floor_is_kept_and_one_block_under_it_is_omitted():
    # blocks are 2 mm: five across is 10 mm, the floor itself ("at least"); four across is 8 mm
    at_floor = depth_of((4, 9, 4, 9))
    under = depth_of((4, 9, 4, 8))
    kept = scale_filtered_section(
        at_floor, marks_at((5, 5)), BLOCK_AREA, BLOCK_MM, FLOOR
    ).estimate
    left = scale_filtered_section(
        under, marks_at((5, 5)), BLOCK_AREA, BLOCK_MM, FLOOR
    ).estimate
    assert kept.status == SECTION and kept.components[0].breadth_mm == 10.0
    assert kept.components[0].kept
    assert left.status == NO_BONE_SCALE and left.components[0].breadth_mm == 8.0
    assert not left.components[0].kept


def test_an_omitted_body_enclosed_by_a_kept_one_is_both_omitted_and_a_filled_hole():
    # a ring body 12 x 12 blocks with a 2 x 2 island of the same depth inside, separated from it by a gap
    depth = depth_of((4, 16, 4, 16))
    depth[6:14, 6:14] = 0.0
    depth[9:11, 9:11] = 5.0
    seeds = marks_at((5, 5), (9, 9))
    got = scale_filtered_section(depth, seeds, BLOCK_AREA, BLOCK_MM, FLOOR)
    estimate = got.estimate
    assert estimate.status == SECTION and estimate.body is not None
    island = np.zeros(SHAPE, dtype=bool)
    island[9:11, 9:11] = True
    assert [c.kept for c in estimate.components] == [True, False]
    np.testing.assert_array_equal(estimate.omitted, island)
    # the hole filling of the kept ring encloses the omitted island: the estimate's body holds it too
    assert estimate.body[island].all()
    assert got.unfiltered.body is not None
    np.testing.assert_array_equal(estimate.body, got.unfiltered.body)


def test_shared_is_judged_on_the_estimates_own_body():
    depth = depth_of(BODY, STRIP)
    seeds = marks_at((6, 6), (10, 14))
    in_the_strip = {"other": marks_at((10, 14))}
    got = scale_filtered_section(
        depth, seeds, BLOCK_AREA, BLOCK_MM, FLOOR, in_the_strip
    )
    # the other object's seed lies in the strip: the unfiltered union is shared, the estimate (strip omitted) is not
    assert got.unfiltered.status == SHARED and got.unfiltered.body is None
    same_section(got.unfiltered, coarse_section(depth, seeds, BLOCK_AREA, in_the_strip))
    assert got.estimate.status == SECTION and got.estimate.body is not None
    assert got.estimate.body.sum() == 64
    # the other object's seed lies in the body: both are shared, and the estimate keeps what it read
    in_the_body = {"other": marks_at((8, 8))}
    both = scale_filtered_section(
        depth, seeds, BLOCK_AREA, BLOCK_MM, FLOOR, in_the_body
    )
    assert both.unfiltered.status == SHARED
    assert both.estimate.status == SHARED and both.estimate.body is None
    assert np.isnan(both.estimate.area_mm2)
    np.testing.assert_array_equal(both.estimate.omitted, depth_of(STRIP) > 0)
    assert [c.kept for c in both.estimate.components] == [True, False]


def test_every_touched_body_under_the_floor_is_a_measured_abstention_of_its_own():
    small = (16, 20, 20, 24)  # 4 x 4 blocks: 8 mm each way, under the floor
    depth = depth_of(STRIP, small)
    seeds = marks_at((10, 14), (17, 21))
    got = scale_filtered_section(depth, seeds, BLOCK_AREA, BLOCK_MM, FLOOR)
    assert got.unfiltered.status == SECTION
    assert got.unfiltered.body is not None and got.unfiltered.body.sum() == 12 + 16
    estimate = got.estimate
    assert estimate.status == NO_BONE_SCALE and STATUS_CODES[NO_BONE_SCALE] == 5
    assert estimate.body is None and estimate.area_mm2 == 0.0
    np.testing.assert_array_equal(estimate.omitted, depth > 0)
    assert [c.kept for c in estimate.components] == [False, False]
    assert sorted(round(c.breadth_mm, 6) for c in estimate.components) == [2.0, 8.0]


def test_an_unread_unseen_or_empty_reading_is_carried_over_unchanged():
    depth = depth_of(BODY)
    nothing = scale_filtered_section(depth, marks_at(), BLOCK_AREA, BLOCK_MM, FLOOR)
    assert nothing.unfiltered.status == nothing.estimate.status == NOT_READ
    assert nothing.estimate.body is None and np.isnan(nothing.estimate.area_mm2)
    assert (
        nothing.estimate.omitted.shape == SHAPE and not nothing.estimate.omitted.any()
    )
    assert nothing.estimate.components == ()
    unseen = depth.copy()
    unseen[3, 3] = np.nan
    got = scale_filtered_section(unseen, marks_at((3, 3)), BLOCK_AREA, BLOCK_MM, FLOOR)
    assert got.unfiltered.status == got.estimate.status == SEEDS_UNSEEN
    assert np.isnan(got.estimate.area_mm2) and got.estimate.components == ()
    flat = scale_filtered_section(
        depth, marks_at((20, 20)), BLOCK_AREA, BLOCK_MM, FLOOR
    )
    assert flat.unfiltered.status == flat.estimate.status == EMPTY
    assert flat.estimate.area_mm2 == 0.0 and flat.estimate.components == ()
    same_section(flat.unfiltered, coarse_section(depth, marks_at((20, 20)), BLOCK_AREA))


def test_the_level_and_the_labelling_are_made_once_for_both_readings(monkeypatch):
    calls: list[int] = []
    real = section_module.ndi.label

    def counted(*args, **kwargs):
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(section_module.ndi, "label", counted)
    scale_filtered_section(
        depth_of(BODY, STRIP), marks_at((6, 6), (10, 14)), BLOCK_AREA, BLOCK_MM, FLOOR
    )
    assert calls == [1]


def test_malformed_inputs_are_refused_by_name():
    depth = depth_of(BODY)
    seeds = marks_at((6, 6))
    with pytest.raises(ValueError, match="seeds_must_share_the_block_grid"):
        scale_filtered_section(
            depth, np.ones((3, 3), dtype=bool), BLOCK_AREA, BLOCK_MM, FLOOR
        )
    for bad in [(0.0, 2.0), (2.0,), (float("nan"), 2.0)]:
        with pytest.raises(ValueError, match="invalid_block_mm"):
            scale_filtered_section(depth, seeds, BLOCK_AREA, bad, FLOOR)
    for bad_floor in (float("nan"), -1.0, float("inf")):
        with pytest.raises(ValueError, match="invalid_floor_mm"):
            scale_filtered_section(depth, seeds, BLOCK_AREA, BLOCK_MM, bad_floor)


def random_case(rng: np.random.Generator):
    rows, columns = rng.integers(6, 28, size=2)
    depth = ndi.gaussian_filter(
        rng.normal(size=(rows, columns)), sigma=float(rng.uniform(0.0, 2.0))
    )
    depth = np.where(rng.random(depth.shape) < 0.05, np.nan, depth * 4.0)
    seeds = rng.random(depth.shape) < rng.uniform(0.01, 0.2)
    others = {"other": rng.random(depth.shape) < rng.uniform(0.0, 0.05)}
    return depth, seeds, others


def test_the_unfiltered_reading_is_the_frozen_original_on_fixtures_and_random_grids():
    unseen = depth_of(BODY)
    unseen[3, 3] = np.nan
    fixtures = [
        (depth_of(BODY, STRIP), marks_at((6, 6), (10, 14)), None),
        (depth_of(BODY, STRIP), marks_at((6, 6), (10, 14)), {"o": marks_at((10, 14))}),
        (depth_of(BODY, STRIP), marks_at((6, 6)), {"o": marks_at((8, 8))}),
        (depth_of(BODY), marks_at(), None),
        (depth_of(BODY), marks_at((20, 20)), None),
        (unseen, marks_at((3, 3)), None),
    ]
    rng = np.random.default_rng(1019)
    cases = fixtures + [random_case(rng) for _ in range(150)]
    statuses = set()
    for depth, seeds, others in cases:
        original = reference_coarse_section(depth, seeds, BLOCK_AREA, others)
        same_section(coarse_section(depth, seeds, BLOCK_AREA, others), original)
        both = scale_filtered_section(depth, seeds, BLOCK_AREA, BLOCK_MM, FLOOR, others)
        same_section(both.unfiltered, original)
        statuses.add(original.status)
    # the random grids reach every status the original can give
    assert {NOT_READ, SEEDS_UNSEEN, EMPTY, SECTION, SHARED} <= statuses


def test_the_estimate_obeys_its_invariants_on_seeded_random_grids():
    rng = np.random.default_rng(20261020)
    seen_estimates = set()
    shared_only_in_the_union: list[int] = []
    for _ in range(200):
        depth, seeds, others = random_case(rng)
        both = scale_filtered_section(depth, seeds, BLOCK_AREA, BLOCK_MM, FLOOR, others)
        whole, estimate = both.unfiltered, both.estimate
        seen_estimates.add(estimate.status)
        assert estimate.floor_mm == FLOOR and estimate.omitted.shape == depth.shape
        for part in estimate.components:
            assert part.kept == (part.breadth_mm >= FLOOR)
            assert part.blocks >= 1 and part.breadth_mm > 0.0
        assert int(estimate.omitted.sum()) == sum(
            part.blocks for part in estimate.components if not part.kept
        )
        if estimate.status == SECTION:
            assert estimate.body is not None
            assert estimate.area_mm2 == float(estimate.body.sum()) * BLOCK_AREA
            assert any(part.kept for part in estimate.components)
            # the unfiltered union may be shared where the estimate is not (shared is judged on the
            # estimate's own body); where it is a section the estimate lies within it (hole filling is monotone)
            assert whole.status in (SECTION, SHARED)
            if whole.body is not None:
                assert not (estimate.body & ~whole.body).any()
            else:
                shared_only_in_the_union.append(1)
        if estimate.status == SHARED:
            assert whole.status == SHARED
        if estimate.status == NO_BONE_SCALE:
            assert whole.status in (SECTION, SHARED)
            assert not any(part.kept for part in estimate.components)
            assert estimate.area_mm2 == 0.0 and estimate.body is None
        if estimate.status in (NOT_READ, SEEDS_UNSEEN, EMPTY):
            assert whole.status == estimate.status and estimate.components == ()
        # no floor: nothing is left out, and the estimate is the unfiltered section
        free = scale_filtered_section(depth, seeds, BLOCK_AREA, BLOCK_MM, 0.0, others)
        same_section(
            CoarseSection(
                free.estimate.status,
                free.estimate.body,
                free.estimate.area_mm2,
                whole.level,
                whole.seeds,
            ),
            whole,
        )
        # a floor no body reaches: every touched body is under it
        huge = scale_filtered_section(depth, seeds, BLOCK_AREA, BLOCK_MM, 1e9, others)
        if whole.status in (SECTION, SHARED):
            assert huge.estimate.status == NO_BONE_SCALE
        # raising the floor never adds a block to the estimate
        if estimate.body is not None and free.estimate.body is not None:
            assert not (estimate.body & ~free.estimate.body).any()
    assert {SECTION, NO_BONE_SCALE} <= seen_estimates
    # the grids reach the case where the unfiltered union is shared and the estimate is a section
    assert shared_only_in_the_union


# -- pack_estimates -----------------------------------------------------------------------------------------


def reading(shape) -> BlockReading:
    return BlockReading(
        np.ones(shape), (2, 2), (2.0, 2.0), (0, 2 * shape[0], 0, 2 * shape[1])
    )


def test_the_estimates_are_packed_on_the_same_planes_as_the_sections():
    depth = depth_of(BODY, STRIP)
    seeds = marks_at((6, 6), (10, 14))
    got = scale_filtered_section(depth, seeds, BLOCK_AREA, BLOCK_MM, FLOOR)
    readings = [reading(SHAPE), reading((10, 12))]
    packed = pack_estimates(
        readings, {"femur": [got.estimate, None], "tibia": [None, None]}
    )
    unread = CoarseSection(
        NOT_READ, None, float("nan"), float("nan"), np.zeros((10, 12), dtype=bool)
    )
    sections = pack_sections(
        [3, 7],
        readings,
        [depth, np.zeros((10, 12))],
        {"femur": [got.unfiltered, unread]},
    )
    offsets = sections["offsets"]
    assert offsets.tolist() == [0, 720, 840]
    assert packed["femur_estimate_made"].tolist() == [True, False]
    assert packed["femur_estimate_status"].tolist() == [
        STATUS_CODES[SECTION],
        STATUS_CODES[NOT_READ],
    ]
    np.testing.assert_array_equal(
        packed["femur_estimate_area_mm2"], [64 * BLOCK_AREA, np.nan]
    )
    body = packed["femur_estimate_body"]
    omitted = packed["femur_omitted"]
    assert body.dtype == bool and len(body) == len(omitted) == 840
    np.testing.assert_array_equal(
        body[offsets[0] : offsets[1]], (depth_of(BODY) > 0).ravel()
    )
    np.testing.assert_array_equal(
        omitted[offsets[0] : offsets[1]], (depth_of(STRIP) > 0).ravel()
    )
    assert not body[offsets[1] : offsets[2]].any()
    assert not omitted[offsets[1] : offsets[2]].any()
    # the unfiltered body packed beside it is both bodies
    assert sections["femur_body"][offsets[0] : offsets[1]].sum() == 64 + 12
    assert packed["femur_component_offsets"].tolist() == [0, 2, 2]
    assert packed["femur_component_blocks"].tolist() == [64, 12]
    np.testing.assert_allclose(packed["femur_component_breadth_mm"], [16.0, 2.0])
    assert packed["femur_component_kept"].tolist() == [True, False]
    # a body with no estimate on any slice: nothing made, nothing invented
    assert not packed["tibia_estimate_made"].any()
    assert packed["tibia_component_offsets"].tolist() == [0, 0, 0]
    assert packed["tibia_component_blocks"].shape == (0,)
    assert packed["tibia_component_blocks"].dtype == np.int32


def test_an_estimate_with_no_body_is_packed_as_its_status_and_its_omitted_blocks():
    estimate = ScaleEstimate(
        NO_BONE_SCALE,
        None,
        0.0,
        depth_of(STRIP) > 0,
        (TouchedComponent(12, 2.0, False),),
        FLOOR,
    )
    packed = pack_estimates([reading(SHAPE)], {"femur": [estimate]})
    assert packed["femur_estimate_status"].tolist() == [5]
    assert packed["femur_estimate_made"].tolist() == [True]
    assert packed["femur_estimate_area_mm2"].tolist() == [0.0]
    assert not packed["femur_estimate_body"].any()
    assert packed["femur_omitted"].sum() == 12
    assert packed["femur_component_kept"].tolist() == [False]


def test_no_readings_pack_to_empty_arrays_and_a_mismatch_is_refused():
    packed = pack_estimates([], {"femur": []})
    assert packed["femur_estimate_made"].shape == (0,)
    assert packed["femur_estimate_body"].shape == (0,)
    assert packed["femur_component_offsets"].tolist() == [0]
    with pytest.raises(ValueError, match="estimates_must_match_the_readings"):
        pack_estimates([reading(SHAPE)], {"femur": []})


def test_the_status_codes_keep_their_numbers_and_the_new_one_is_last():
    assert STATUS_CODES == {
        NOT_READ: 0,
        SEEDS_UNSEEN: 1,
        EMPTY: 2,
        SECTION: 3,
        SHARED: 4,
        NO_BONE_SCALE: 5,
    }
    assert coarse_section(depth_of(BODY), marks_at((6, 6)), BLOCK_AREA).status != (
        NO_BONE_SCALE
    )


# -- axial_bone_planes reads the estimate ---------------------------------------------------------------------

# At 1 mm, the real 2 mm block reading gives 2 x 2 pixel blocks: a 20 x 30 grid of blocks.
NATIVE = (40, 60)
GRID = (20, 30)
# Rows toward y, columns toward x (the patient's left-right axis).
BASIS = np.array([[0.0, 1.0], [1.0, 0.0], [0.0, 0.0]])


def grid_depth(*boxes: tuple[int, int, int, int]) -> np.ndarray:
    return depth_of(*boxes, shape=GRID)


def native_seeds(*blocks: tuple[int, int]) -> np.ndarray:
    """One native pixel inside each named 2 x 2 block."""
    mask = np.zeros(NATIVE, dtype=bool)
    for row, column in blocks:
        mask[2 * row, 2 * column] = True
    return mask


def plane_image() -> np.ndarray:
    image = np.full(NATIVE, 100.0)
    rr, cc = np.mgrid[: NATIVE[0], : NATIVE[1]]
    image[np.hypot(rr - 20, cc - 30) <= 8] = 30.0
    return image


def read_axial(
    monkeypatch,
    tag: str,
    depths: list[np.ndarray],
    femur: list[tuple[tuple[int, int], ...]],
    tibia: list[tuple[tuple[int, int], ...]] | None = None,
    femur_low: float | None = None,
):
    """`axial_bone_planes` through its real code on a stack of planes whose coarse depth grids are the given ones
    (the enclosure reading is not what is under test: the consumer is). The seeds are the blocks named per slice;
    a carried femur at `femur_low` (z, millimetres) makes a tibia slice above it an overlap."""
    count = len(depths)
    tibia = tibia if tibia is not None else [()] * count
    frames = [
        PlaneFrame(np.array([0.0, 0.0, 10.0 * z]), BASIS, (1.0, 1.0))
        for z in range(count)
    ]
    monkeypatch.setattr(run, "plane_frame", lambda series, z: frames[z])
    monkeypatch.setattr(
        run,
        "leg_on",
        lambda leg, series, z, frame, shape, thick: (
            native_seeds(*femur[z]),
            native_seeds(*tibia[z]),
        ),
    )
    supplied = iter(depths)
    monkeypatch.setattr(run, "coarse_depth", lambda median, dark: next(supplied).copy())
    volume = np.stack([plane_image() for _ in range(count)])
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid=tag, fat_suppression="1"),
        volume=volume,
        slice_thickness_mm=[3.0] * count,
    )
    own = SimpleNamespace(
        series=series,
        arrays={"acquired_plane": volume[0]},
        record={"view": ["Axial", "1", "1"]},
    )
    places = (
        np.zeros((0, 3)) if femur_low is None else np.array([[0.0, 0.0, femur_low]])
    )
    leg = SimpleNamespace(femur_lps=places, tibia_lps=np.zeros((0, 3)))
    smap = StudyMap(knee="R")
    said = run.axial_bone_planes(smap, cast(run.Measured, own), cast(run.Leg, leg))
    return smap, own, said


# Slice 0: a body 100 blocks (20 x 20 mm) with a thin lateral strip beside it (12 blocks, 2 mm wide); slice 1: the
# same body with six more blocks and no strip. The unfiltered areas are 448 and 424 mm2 (slice 0 is the larger
# and widest: 38 mm left to right), the estimate's 400 and 424 (slice 1 is the larger: 20 mm).
BODY_BOX = (4, 14, 4, 14)
LATERAL_STRIP = (6, 18, 22, 23)
EXTRA_ROW = (14, 15, 4, 10)


def test_the_axial_key_plane_and_the_knees_scale_read_the_estimate_not_the_thin_strip(
    monkeypatch,
):
    smap, own, said = read_axial(
        monkeypatch,
        "b0-scale-femur",
        [grid_depth(BODY_BOX, LATERAL_STRIP), grid_depth(BODY_BOX, EXTRA_ROW)],
        femur=[((8, 8), (10, 22)), ((8, 8),)],
    )
    arrays = own.arrays
    # the estimate chooses the key plane: slice 1 (424 against 400); the unfiltered areas would pick slice 0
    np.testing.assert_array_equal(
        arrays["a4_axial_coarse_femur_area_mm2"], [4.0 * 112, 4.0 * 106]
    )
    np.testing.assert_array_equal(
        arrays["a4_axial_femur_section_area_mm2"], [4.0 * 100, 4.0 * 106]
    )
    assert said["femur"]["key_slices"] == [1]
    assert smap.selected("femur", "axial").slice == 1
    # and the knee's scale is the estimate's left-right extent there (20 mm), not the strip's (38 mm)
    assert smap.scale.mm == pytest.approx(20.0)
    assert smap.scale.code == "measured_femur_ml_breadth"
    assert "scale-filtered" in smap.scale.source
    # the provenance names the estimate and no longer claims the cortex-enclosed section
    reason = smap.selected("femur", "axial").reason
    assert "scale-filtered" in reason and "enclosed by its cortex" not in reason
    assert smap.selected("femur", "axial").provenance == "scale_filtered_section"
    assert "scale-filtered" in said["femur"]["rule"]
    assert "enclosed by its cortex" not in said["femur"]["rule"]
    assert said["femur"]["scale_floor_mm"] == run.BONE_MM
    # the statuses read the estimate; the unfiltered statuses are kept beside them
    assert said["femur"]["statuses"] == {SECTION: 2}
    assert said["femur"]["unfiltered_statuses"] == {SECTION: 2}


def test_the_knees_scale_is_the_estimates_breadth_where_the_strip_lies_on_the_key_plane(
    monkeypatch,
):
    # the key plane is slice 0 either way (400 mm2 of estimate against 360, 448 unfiltered against 360), and the
    # lateral strip lies on it: the scale is the estimate's 20 mm, and not the strip's 38 mm
    smaller = (4, 13, 4, 14)
    smap, own, said = read_axial(
        monkeypatch,
        "b0-scale-on-key-plane",
        [grid_depth(BODY_BOX, LATERAL_STRIP), grid_depth(smaller)],
        femur=[((8, 8), (10, 22)), ((8, 8),)],
    )
    assert said["femur"]["key_slices"] == [0]
    assert smap.scale.mm == pytest.approx(20.0)
    assert "0:400mm2" in smap.scale.source
    assert smap.selected("femur", "axial").slice == 0
    # the unfiltered section of that slice is the wider one, kept beside it
    assert own.arrays["a4_axial_coarse_femur_area_mm2"].tolist() == [448.0, 360.0]
    assert own.arrays["a4_axial_femur_section_area_mm2"].tolist() == [400.0, 360.0]


def test_the_unfiltered_arrays_keep_their_meaning_and_the_estimate_is_packed_beside_them(
    monkeypatch,
):
    depths = [grid_depth(BODY_BOX, LATERAL_STRIP), grid_depth(BODY_BOX, EXTRA_ROW)]
    _, own, _ = read_axial(
        monkeypatch,
        "b0-scale-arrays",
        depths,
        femur=[((8, 8), (10, 22)), ((8, 8),)],
    )
    arrays = own.arrays
    sizes = GRID[0] * GRID[1]
    for at, depth in enumerate(depths):
        seeds = np.zeros(GRID, dtype=bool)
        seeds[8, 8] = True
        if at == 0:
            seeds[10, 22] = True
        original = reference_coarse_section(depth, seeds, 4.0)
        window = slice(at * sizes, (at + 1) * sizes)
        assert original.body is not None
        np.testing.assert_array_equal(
            arrays["a4_axial_coarse_femur_body"][window], original.body.ravel()
        )
        np.testing.assert_array_equal(
            arrays["a4_axial_coarse_femur_seeds"][window], seeds.ravel()
        )
        assert arrays["a4_axial_coarse_femur_status"][at] == STATUS_CODES[SECTION]
        assert arrays["a4_axial_coarse_femur_area_mm2"][at] == original.area_mm2
        assert arrays["a4_axial_coarse_femur_level"][at] == original.level
    # the estimate beside them: slice 0 has the strip omitted, slice 1 is whole
    body = arrays["a4_axial_coarse_femur_estimate_body"]
    omitted = arrays["a4_axial_coarse_femur_omitted"]
    assert body[:sizes].sum() == 100 and omitted[:sizes].sum() == 12
    assert body[sizes:].sum() == 106 and not omitted[sizes:].any()
    assert arrays["a4_axial_coarse_femur_estimate_made"].tolist() == [True, True]
    assert arrays["a4_axial_coarse_femur_estimate_status"].tolist() == [3, 3]
    assert arrays["a4_axial_coarse_femur_component_offsets"].tolist() == [0, 2, 3]
    assert arrays["a4_axial_coarse_femur_component_blocks"].tolist() == [100, 12, 106]
    assert arrays["a4_axial_coarse_femur_component_kept"].tolist() == [
        True,
        False,
        True,
    ]
    # the tibia is seeded nowhere: it keeps its call (not read) and makes no estimate
    assert not arrays["a4_axial_coarse_tibia_estimate_made"].any()
    assert arrays["a4_axial_coarse_tibia_status"].tolist() == [0, 0]
    assert arrays["a4_axial_coarse_tibia_estimate_status"].tolist() == [0, 0]
    assert "a4_axial_tibia_section_area_mm2" in arrays


def test_a_slice_whose_touched_bodies_are_all_under_the_floor_is_no_key_plane(
    monkeypatch,
):
    # slice 0: only a long thin strip is touched (2 blocks, 4 mm wide, 30 long: 240 mm2, which unfiltered is the
    # largest section); slice 1: a body 6 x 6 blocks (12 mm each way, 144 mm2)
    long_strip = (4, 6, 0, 30)
    body = (6, 12, 6, 12)
    smap, own, said = read_axial(
        monkeypatch,
        "b0-scale-no-scale",
        [grid_depth(long_strip), grid_depth(body)],
        femur=[((4, 10),), ((8, 8),)],
    )
    assert said["femur"]["statuses"] == {NO_BONE_SCALE: 1, SECTION: 1}
    assert said["femur"]["unfiltered_statuses"] == {SECTION: 2}
    assert said["femur"]["key_slices"] == [1]
    assert smap.selected("femur", "axial").slice == 1
    areas = own.arrays["a4_axial_femur_section_area_mm2"]
    assert np.isnan(areas[0]) and areas[1] == 144.0
    assert own.arrays["a4_axial_coarse_femur_estimate_status"].tolist() == [5, 3]
    assert own.arrays["a4_axial_coarse_femur_area_mm2"].tolist() == [240.0, 144.0]
    # slice 0's estimate holds no body: the omitted strip and its breadth are kept
    omitted = own.arrays["a4_axial_coarse_femur_omitted"]
    assert (
        omitted[: GRID[0] * GRID[1]].sum() == 60
        and not omitted[GRID[0] * GRID[1] :].any()
    )
    assert own.arrays["a4_axial_coarse_femur_component_kept"].tolist() == [False, True]


def test_the_tibia_reads_its_estimate_too_and_an_excluded_slice_keeps_its_old_call(
    monkeypatch,
):
    # the carried femur's lowest place is at z = 5: the tibia is attributed on slice 0 (z 0) and, being
    # above that place, named an overlap on slice 1 (z 10), where only the femur is attributed. The two bones
    # lie in separate bodies (the tibia's at columns 4 to 13, the femur's at columns 16 to 21).
    femur_box = (4, 14, 16, 22)
    smap, own, said = read_axial(
        monkeypatch,
        "b0-scale-tibia",
        [
            grid_depth(BODY_BOX, LATERAL_STRIP),
            grid_depth(BODY_BOX, EXTRA_ROW, femur_box),
        ],
        femur=[(), ((8, 18),)],
        tibia=[((8, 8), (10, 22)), ((8, 8),)],
        femur_low=5.0,
    )
    arrays = own.arrays
    assert arrays["a4_axial_tibia_identity_excluded"].tolist() == [False, True]
    assert said["tibia"]["statuses"] == {SECTION: 1, run.AXIAL_OVERLAP: 1}
    assert said["tibia"]["unfiltered_statuses"] == {SECTION: 1, run.AXIAL_OVERLAP: 1}
    # attributed on slice 0 only: the estimate leaves the strip out, so its area is 400 and not 448
    np.testing.assert_array_equal(
        arrays["a4_axial_tibia_section_area_mm2"], [4.0 * 100, np.nan]
    )
    assert said["tibia"]["key_slices"] == [0]
    assert smap.selected("tibia", "axial").slice == 0
    assert arrays["a4_axial_coarse_tibia_estimate_made"].tolist() == [True, False]
    assert arrays["a4_axial_coarse_tibia_estimate_status"].tolist() == [3, 0]
    # the excluded slice keeps the call it always had (a section, never attributed)
    assert arrays["a4_axial_coarse_tibia_status"].tolist() == [3, 3]
    assert arrays["a4_axial_coarse_tibia_area_mm2"].tolist() == [448.0, 424.0]
    # the femur is attributed on slice 1 only, and sets the knee's scale from its own estimate (12 mm)
    assert said["femur"]["key_slices"] == [1]
    assert arrays["a4_axial_coarse_femur_estimate_made"].tolist() == [False, True]
    assert smap.scale.mm == pytest.approx(12.0)
