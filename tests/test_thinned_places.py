"""`thinned` puts a bone's carried places on a lattice, one place per cell. It sorts one integer per cell
instead of byte-sorting rows (`np.unique(axis=0)`); the cells and their order must be exactly the same."""

import numpy as np

from scripts import run_interiors as run

STEP = run.BONE_PLACES_STEP_MM


def by_rows(points):
    """The first form of `thinned`: the answer the integer form must equal."""
    points = np.asarray(points, dtype=np.float64).reshape(-1, 3)
    points = points[np.isfinite(points).all(axis=1)]
    if not len(points):
        return points
    return np.unique(np.rint(points / STEP).astype(np.int64), axis=0) * STEP


def test_the_cells_and_their_order_are_those_of_the_row_sort():
    rng = np.random.default_rng(3)
    for scale, offset in ((5.0, 0.0), (120.0, -60.0), (300.0, -400.0), (0.3, 7.0)):
        points = rng.normal(size=(5000, 3)) * scale + offset
        points = np.vstack([points, points[:700]])  # duplicates, and places in one cell
        assert np.array_equal(run.thinned(points), by_rows(points))


def test_negative_coordinates_unequal_columns_and_a_flat_lattice():
    rng = np.random.default_rng(5)
    flat = rng.integers(-40, 40, size=(2000, 3)).astype(float) * STEP
    flat[:, 2] = 12.5  # one plane: a span of one cell in a column
    assert np.array_equal(run.thinned(flat), by_rows(flat))
    long = np.column_stack(
        (
            rng.uniform(-1, 1, 3000),
            rng.uniform(-500, 500, 3000),
            rng.uniform(0, 3, 3000),
        )
    )
    assert np.array_equal(run.thinned(long), by_rows(long))


def test_places_that_are_not_finite_are_not_places_and_nothing_is_nothing():
    points = np.array(
        [[1.0, 2.0, 3.0], [np.nan, 0.0, 0.0], [np.inf, 1.0, 1.0], [1.1, 2.1, 3.1]]
    )
    assert np.array_equal(run.thinned(points), by_rows(points))
    assert run.thinned(points).shape == (1, 3)  # the two finite places share a cell
    assert run.thinned(np.empty((0, 3))).shape == (0, 3)
    assert run.thinned(np.full((3, 3), np.nan)).shape == (0, 3)
    single = np.array([[4.0, -9.0, 2.0]])
    assert np.array_equal(run.thinned(single), by_rows(single))


def test_a_lattice_too_wide_for_one_integer_per_cell_falls_back_to_the_rows():
    wide = np.array([[0.0, 0.0, 0.0], [STEP * 2**21, STEP * 2**21, STEP * 2**21]])
    assert np.array_equal(run.thinned(wide), by_rows(wide))
    assert len(run.thinned(wide)) == 2


def test_a_signed_span_that_would_wrap_int64_still_takes_the_row_fallback():
    # cells at about -4.7e18 and +4.7e18: their difference exceeds int64, and so would a span made in int64
    big = 4.7e18 * STEP
    extreme = np.array([[-big, -big, -big], [big, big, big], [0.0, 0.0, 0.0]])
    got = run.thinned(extreme)
    assert np.array_equal(got, by_rows(extreme))
    assert len(got) == 3
    one_column = np.array([[-big, 1.0, 2.0], [big, 1.0, 2.0], [big, 1.0, 2.0]])
    assert np.array_equal(run.thinned(one_column), by_rows(one_column))
    assert len(run.thinned(one_column)) == 2
