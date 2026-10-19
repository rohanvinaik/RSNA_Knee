import numpy as np
import pytest

from knee.objects.interiors import (
    LensScope,
    interior_regions,
    lens_scope,
    read_interiors,
)


def axis(n, size, extent):
    return np.array([[i * size, min((i + 1) * size, extent)] for i in range(n)])


def grid(fill=0.0, n=5) -> tuple[np.ndarray, np.ndarray]:
    return np.full((n, n), fill), np.ones((n, n))


def make_bounds(axes):
    row_bounds, col_bounds = axes
    out = np.empty((len(row_bounds), len(col_bounds), 4), dtype=np.int64)
    for r, (r0, r1) in enumerate(row_bounds):
        for c, (c0, c1) in enumerate(col_bounds):
            out[r, c] = (r0, r1, c0, c1)
    return out


def square_bounds(n=5, size=10, extent=50):
    return make_bounds((axis(n, size, extent), axis(n, size, extent)))


def one_high_tile(r, c):
    maximum, coverage = grid(0.0)
    maximum[r, c] = 100.0
    return lens_scope(maximum, coverage, square_bounds(), 50.0, (50, 50))


def test_four_connectivity_keeps_diagonal_enclosed_low_in_scope():
    maximum, coverage = grid(100.0)
    maximum[0, 0] = 0.0  # exterior low
    maximum[1, 1] = 0.0  # diagonal-only neighbour: enclosed under 4-connectivity
    scope = lens_scope(maximum, coverage, square_bounds(), 50.0, (50, 50))
    assert not scope.in_scope_tiles[0, 0]
    assert scope.in_scope_tiles[1, 1]
    assert scope.in_scope_tile_count == 24
    # An orthogonal neighbour does join the exterior component.
    maximum[0, 1] = 0.0
    maximum[1, 1] = 0.0
    scope = lens_scope(maximum, coverage, square_bounds(), 50.0, (50, 50))
    assert not scope.in_scope_tiles[1, 1]


def test_unknown_nan_and_partial_tiles_stay_in_scope():
    maximum, coverage = grid(0.0, n=4)
    maximum[0, 0] = np.nan
    coverage[0, 1] = np.nextafter(1.0, 0.0)
    bounds = square_bounds(4, 10, 40)
    scope = lens_scope(maximum, coverage, bounds, 50.0, (40, 40))
    assert scope.in_scope_tiles[0, 0] and scope.in_scope_tiles[0, 1]
    assert scope.in_scope_tile_count == 2
    # tiles (0,0),(0,1) plus one tile of halo: rows 0..20, cols 0..30
    assert scope.window_rc == (0, 20, 0, 30)


def test_nan_coverage_is_unknown_but_infinite_or_out_of_range_is_malformed():
    maximum, coverage = grid(0.0)
    coverage[0, 0] = np.nan
    scope = lens_scope(maximum, coverage, square_bounds(), 50.0, (50, 50))
    assert scope.in_scope_tiles[0, 0]
    assert scope.window_rc == (0, 20, 0, 20)
    for invalid in (-0.1, 1.1, np.inf, -np.inf):
        bad_coverage = np.ones((5, 5))
        bad_coverage[1, 1] = invalid
        with pytest.raises(ValueError):
            lens_scope(maximum, bad_coverage, square_bounds(), 50.0, (50, 50))


def test_gapped_tile_grid_keeps_tile_classification_but_uses_full_frame_window():
    maximum, coverage = grid(0.0)
    maximum[2, 2] = 100.0
    rows = axis(5, 10, 50)
    rows[1:, 0] += 2
    rows[1:, 1] += 2
    bounds = make_bounds((rows, axis(5, 10, 50)))
    scope = lens_scope(maximum, coverage, bounds, 50.0, (52, 50))
    assert scope.in_scope_tiles[2, 2]
    assert scope.in_scope_tile_count == 1
    assert scope.window_rc == (0, 52, 0, 50)
    assert scope.code == "full_frame_tile_bounds_incomplete"


def test_all_low_is_empty_scope_but_no_exterior_low_is_full_frame():
    maximum, coverage = grid(0.0)
    empty = lens_scope(maximum, coverage, square_bounds(), 50.0, (50, 50))
    assert empty.in_scope_tile_count == 0
    assert not empty.in_scope_tiles.any()
    assert empty.window_rc == (0, 0, 0, 0)

    maximum, coverage = grid(100.0)
    full = lens_scope(maximum, coverage, square_bounds(), 50.0, (50, 50))
    assert full.window_rc == (0, 50, 0, 50)
    assert full.in_scope_tiles.all()
    # A non-finite split yields no eligible low tile at all.
    nan_split = lens_scope(*grid(0.0), square_bounds(), np.nan, (50, 50))
    assert nan_split.window_rc == (0, 50, 0, 50) and nan_split.in_scope_tiles.all()


@pytest.mark.parametrize(
    "tile, window",
    [
        ((0, 2), (0, 20, 10, 40)),
        ((4, 2), (30, 50, 10, 40)),
        ((2, 0), (10, 40, 0, 20)),
        ((2, 4), (10, 40, 30, 50)),
    ],
)
def test_halo_is_clamped_at_every_frame_edge(tile, window):
    assert one_high_tile(*tile).window_rc == window


def test_non_square_ragged_tiles_use_adjacent_tile_extent():
    maximum, coverage = grid(0.0)
    maximum[2, 4] = 100.0  # last, ragged column tile (5 px wide)
    bounds = make_bounds((axis(5, 8, 40), axis(5, 10, 45)))
    scope = lens_scope(maximum, coverage, bounds, 50.0, (40, 45))
    assert scope.window_rc == (8, 32, 30, 45)
    maximum[2, 4], maximum[2, 3] = 0.0, 100.0  # halo reaches into the ragged tile
    scope = lens_scope(maximum, coverage, bounds, 50.0, (40, 45))
    assert scope.window_rc == (8, 32, 20, 45)


def test_scoped_regions_only_window_pixels_get_expensive_outputs():
    scope = one_high_tile(2, 2)
    assert scope.window_rc == (10, 40, 10, 40)
    plane = np.zeros((50, 50))
    plane[20:30, 20:30] = 100.0
    plane[2:8, 2:8] = 100.0  # high pixels outside the window must be ignored
    plane[45, 45] = np.nan
    out = interior_regions(plane, (1.0, 1.0), 50.0, 1.0, scope=scope)

    window = np.zeros(plane.shape, dtype=bool)
    window[10:40, 10:40] = True
    assert out.code == "measured"
    # dark/available are whole-frame
    expected_available = np.isfinite(plane)
    np.testing.assert_array_equal(out.available, expected_available)
    np.testing.assert_array_equal(out.dark, expected_available & (plane <= 50.0))
    assert not out.dark[45, 45] and not out.available[45, 45]
    assert out.dark[0, 0] and not out.dark[3, 3]
    # expensive outputs are zero outside the window
    for field in (out.distance_mm, out.markers, out.labels):
        assert not field[~window].any()
    assert out.distance_mm[20:30, 20:30].max() == pytest.approx(5.0)
    assert out.markers[window].any()
    assert np.count_nonzero(out.labels) == 100
    assert np.all(out.labels[20:30, 20:30] == 1)
    for field in (out.dark, out.available, out.distance_mm, out.markers, out.labels):
        assert not field.flags.writeable


def test_draw_and_undrawn_entrypoints_share_scoped_regions():
    scope = one_high_tile(2, 2)
    plane = np.zeros((50, 50))
    plane[20:30, 20:30] = 100.0
    plain = interior_regions(plane, (1.0, 1.0), 50.0, 1.0, scope=scope)
    drawn = read_interiors(
        plane,
        (1.0, 1.0),
        50.0,
        1.0,
        np.array([-1.0, 0.0, 1.0]),
        scope=scope,
    )
    for name in ("code", "dark", "available", "distance_mm", "markers", "labels"):
        left, right = getattr(plain, name), getattr(drawn, name)
        if isinstance(left, np.ndarray):
            np.testing.assert_array_equal(left, right)
        else:
            assert left == right


def test_empty_scope_on_nonempty_plane_is_no_interior_seeds():
    scope = lens_scope(*grid(0.0), square_bounds(), 50.0, (50, 50))
    plane = np.random.default_rng(0).uniform(0, 100, (50, 50))
    out = interior_regions(plane, (1.0, 1.0), 50.0, 1.0, scope=scope)
    assert out.code == "no_interior_seeds"
    np.testing.assert_array_equal(out.dark, plane <= 50.0)
    assert out.available.all()
    assert not (out.distance_mm.any() or out.markers.any() or out.labels.any())


def test_named_outcome_precedence_with_scope():
    empty_window = lens_scope(*grid(0.0), square_bounds(), 50.0, (50, 50))
    zero = np.zeros((0, 5))
    manual = LensScope(np.zeros((1, 1), dtype=bool), (0, 0, 0, 0), 0)
    out = interior_regions(zero, (1.0, 1.0), 50.0, 1.0, scope=manual)
    assert out.code == "empty_plane" and out.labels.shape == (0, 5)
    # a zero-size plane is empty_plane even under a nonempty window
    full = lens_scope(*grid(100.0), square_bounds(), 50.0, (50, 50))
    assert (
        interior_regions(zero, (1.0, 1.0), 50.0, 1.0, scope=full).code == "empty_plane"
    )

    nans = np.full((50, 50), np.nan)
    assert interior_regions(nans, (1.0, 1.0), 50.0, 1.0, scope=empty_window).code == (
        "no_finite_support"
    )
    plane = np.ones((50, 50))
    assert interior_regions(
        plane, (1.0, 1.0), np.nan, 1.0, scope=empty_window
    ).code == ("split_unavailable")
    with pytest.raises(ValueError):
        interior_regions(plane, (1.0, 1.0), np.inf, 1.0, scope=empty_window)


def test_inputs_are_not_mutated_and_scope_is_read_only():
    maximum, coverage = grid(0.0)
    maximum[2, 2] = np.nan
    bounds = square_bounds()
    copies = [a.copy() for a in (maximum, coverage, *bounds)]
    scope = lens_scope(maximum, coverage, bounds, 50.0, (50, 50))
    for before, after in zip(copies, (maximum, coverage, *bounds), strict=True):
        np.testing.assert_array_equal(before, after)
    assert not scope.in_scope_tiles.flags.writeable

    plane = np.random.default_rng(1).uniform(0, 100, (50, 50))
    avail = np.isfinite(plane)
    plane_copy, avail_copy = plane.copy(), avail.copy()
    full = lens_scope(*grid(100.0), square_bounds(), 50.0, (50, 50))
    interior_regions(plane, (1.0, 1.0), 50.0, 1.0, available=avail, scope=full)
    np.testing.assert_array_equal(plane, plane_copy)
    np.testing.assert_array_equal(avail, avail_copy)
    assert avail.flags.writeable


@pytest.mark.parametrize(
    "kwargs",
    [
        {"coverage": np.ones((4, 5))},  # shape mismatch
        {"coverage": np.full((5, 5), 1.5)},
        {"maximum": np.zeros(5)},
        {"plane_shape": (0, 50)},
        {"plane_shape": (50,)},
        {"plane_shape": (50.5, 50)},
        {"bounds_rc": np.zeros((4, 5, 4), dtype=int)},  # wrong tile count
        {"bounds_rc": np.full((5, 5, 4), 100)},  # beyond plane
        {"bounds_rc": np.full((5, 5, 4), 0.5)},  # non-integer
        {"bounds_rc": np.full((5, 5, 4), 10)},
        {"bounds_rc": np.zeros((5, 5, 3))},
        {"split": "abc"},
    ],
)
def test_lens_scope_rejects_malformed_inputs(kwargs):
    args = {
        "maximum": np.zeros((5, 5)),
        "coverage": np.ones((5, 5)),
        "bounds_rc": square_bounds(),
        "split": 50.0,
        "plane_shape": (50, 50),
    }
    args.update(kwargs)
    with pytest.raises(ValueError):
        lens_scope(**args)


@pytest.mark.parametrize(
    "scope",
    [
        LensScope(np.ones((2, 2), dtype=bool), (0, 60, 0, 10), 4),  # outside plane
        LensScope(np.ones((2, 2), dtype=bool), (10, 5, 0, 10), 4),  # inverted
        LensScope(np.ones((2, 2), dtype=bool), (0, 10, 0, 10), 3),  # count mismatch
        LensScope(np.ones((2, 2)), (0, 10, 0, 10), 4),  # not bool
        LensScope(np.ones(4, dtype=bool), (0, 10, 0, 10), 4),  # not 2-D
    ],
)
def test_scoped_regions_rejects_malformed_scope(scope):
    with pytest.raises(ValueError):
        interior_regions(np.ones((50, 50)), (1.0, 1.0), 50.0, 1.0, scope=scope)


def test_scoped_regions_rejects_mismatched_available():
    scope = lens_scope(*grid(100.0), square_bounds(), 50.0, (50, 50))
    with pytest.raises(ValueError):
        interior_regions(
            np.ones((50, 50)),
            (1.0, 1.0),
            50.0,
            1.0,
            available=np.ones((5, 5), bool),
            scope=scope,
        )
