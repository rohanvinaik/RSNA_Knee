"""The cheap continuation of a located tube along the leg (`knee.collapse.posterior`)."""

import numpy as np
import pytest

from knee.collapse import posterior as P


def sagittal_basis(rows_toward_head=False):
    """A sagittal slice: rows run along z (toward the feet unless flipped), columns along y."""
    row = np.array([0.0, 0.0, 1.0 if rows_toward_head else -1.0])
    return np.column_stack((row, [0.0, 1.0, 0.0]))


def tube(rows=40, cols=40, line_rows=(5, 30), col=20, level=100.0, dark=100.0):
    plane = np.full((rows, cols), level)
    plane[line_rows[0] : line_rows[1], col] = level - dark
    return plane


def test_the_axis_along_the_leg_and_its_direction_come_from_the_basis():
    assert P.leg_axis(sagittal_basis()) == (0, -1)
    assert P.leg_axis(sagittal_basis(True)) == (0, 1)
    assert P.leg_axis(sagittal_basis()[:, ::-1]) == (1, -1)  # transposed picture
    axial = np.column_stack(([0.0, 1.0, 0.0], [1.0, 0.0, 0.0]))
    assert P.leg_axis(axial) is None  # the leg does not run in an axial slice
    assert P.leg_axis(np.full((3, 2), np.nan)) is None
    assert P.leg_axis(np.zeros((3, 2))) is None
    # an oblique stack keeps the axis that is within 45 degrees of the head
    oblique = np.column_stack(([0.0, 0.5, -1.0], [0.0, 1.0, 0.0]))
    assert P.leg_axis(oblique) == (0, -1)
    steep = np.column_stack(([0.0, 1.0, -0.5], [0.0, 1.0, 0.0]))
    assert P.leg_axis(steep) is None


def test_the_width_is_across_the_leg_not_along_it():
    points = np.array([[0.0, 0.0, 0.0], [0.0, 4.0, 30.0], [1.0, 2.0, 5.0]])
    assert P.cross_extent_mm(points, sagittal_basis(), 0) == pytest.approx(4.0)
    assert P.cross_extent_mm(np.full((2, 3), np.nan), sagittal_basis(), 0) is None


def test_a_dark_tube_is_followed_to_where_it_ends_in_both_directions():
    plane = tube()
    got = P.trace_tube(plane, 0, -1, (15.0, 20.0), 1)
    assert got.start == P.FOLLOWED
    assert got.points_rc[:, 0].tolist() == list(range(29, 4, -1))  # head is row 0
    assert set(got.points_rc[:, 1]) == {20.0}
    assert got.toward_feet == P.FLANKS and got.toward_head == P.FLANKS
    assert np.all(got.light < got.flank)


def test_reversed_stack_direction_gives_the_same_places():
    plane = tube()
    a = P.trace_tube(plane, 0, -1, (15.0, 20.0), 1)
    b = P.trace_tube(plane[::-1], 0, 1, (24.0, 20.0), 1)  # rows now run toward the head
    assert a.points_rc[:, 0].tolist() == [39 - r for r in b.points_rc[:, 0]]
    assert b.points_rc[0, 0] == 10.0  # the feet end is the low row
    assert a.toward_head == b.toward_head and a.toward_feet == b.toward_feet


def test_a_picture_with_the_leg_across_the_columns_is_followed_the_same():
    a = P.trace_tube(tube(), 0, -1, (15.0, 20.0), 1)
    b = P.trace_tube(tube().T, 1, -1, (20.0, 15.0), 1)
    assert np.array_equal(a.points_rc[:, ::-1], b.points_rc)


def test_the_window_moves_with_an_oblique_tube():
    plane = np.full((40, 40), 100.0)
    for r in range(5, 30):
        plane[r, 10 + r // 2] = 0.0
    got = P.trace_tube(plane, 0, -1, (10.0, 15.0), 1)
    assert got.start == P.FOLLOWED
    assert got.points_rc[:, 0].min() == 5.0 and got.points_rc[:, 0].max() == 29.0
    assert got.points_rc[0, 1] > got.points_rc[-1, 1]  # head end is the low row


def test_a_monotonic_fall_is_not_a_ridge_and_a_bright_tube_needs_bright_polarity():
    ramp = np.tile(np.linspace(200.0, 0.0, 40), (40, 1))
    got = P.trace_tube(ramp, 0, -1, (20.0, 20.0), 2)
    assert got.start == P.START_REFUSALS[2] and not len(got.points_rc)
    assert got.toward_head is None and got.toward_feet is None
    bright = tube(level=10.0, dark=-90.0)
    assert P.trace_tube(bright, 0, -1, (15.0, 20.0), 1).start != P.FOLLOWED
    assert P.trace_tube(bright, 0, -1, (15.0, 20.0), 1, dark=False).start == P.FOLLOWED


def test_unseen_places_are_never_dark_and_stop_the_trace_by_name():
    plane = tube()
    plane[10, 15:25] = np.nan  # the reconstruction never filled these places
    got = P.trace_tube(plane, 0, -1, (15.0, 20.0), 1)
    assert got.toward_head == P.UNSEEN  # row 10 is toward the head from row 15
    assert got.points_rc[:, 0].min() == 11.0
    nowhere = np.full((40, 40), np.nan)
    assert P.trace_tube(nowhere, 0, -1, (15.0, 20.0), 1).start == P.START_REFUSALS[1]


def test_the_scan_edge_and_a_start_off_the_picture_are_named():
    plane = tube(line_rows=(0, 30))
    got = P.trace_tube(plane, 0, -1, (15.0, 20.0), 1)
    assert got.toward_head == P.CLIPPED and got.toward_feet == P.FLANKS
    near_edge = P.trace_tube(tube(), 0, -1, (15.0, 1.0), 2)
    assert near_edge.start == P.START_REFUSALS[0]
    assert P.trace_tube(tube(), 0, -1, (99.0, 20.0), 1).start == P.START_REFUSALS[0]


def test_contiguous_ties_are_one_ridge_and_separated_ties_stop():
    plane = tube()
    plane[:, 21] = plane[:, 20]  # two equally dark neighbours: one two pixel ridge
    got = P.trace_tube(plane, 0, -1, (15.0, 20.0), 1)
    assert got.start == P.FOLLOWED and set(got.points_rc[:, 1]) == {20.5}
    split = np.full((40, 40), 100.0)
    split[:, 19] = 0.0
    split[:, 21] = 0.0
    assert P.trace_tube(split, 0, -1, (15.0, 20.0), 1).start == P.START_REFUSALS[3]


def test_a_ridge_is_at_least_a_pixel_and_a_slice_is_two_dimensional():
    with pytest.raises(ValueError, match="at_least_one_pixel"):
        P.trace_tube(tube(), 0, -1, (15.0, 20.0), 0)
    with pytest.raises(ValueError, match="two_dimensional"):
        P.trace_tube(np.zeros(5), 0, -1, (1.0, 1.0), 1)
