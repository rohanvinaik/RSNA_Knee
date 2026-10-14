"""Intent and property tests for the shared dome measurement (knee.objects.dome.dome), both signs.

The CONTRACT's proof gate: two interiors parted by an obstacle give two peaks and two territories
that never cross the obstacle; one round interior gives one peak at its centre with height equal
to its radius in millimetres; an empty interior gives no peak and all-zero labels; the height is
zero on every obstacle; no input is written. Beside it, the rules the docstring states: the
picture's edge is an obstacle, the spacing is (row_mm, column_mm), the peaks are ordered tallest
first with ties in scan order, territory k + 1 is peak k's, prominence and never strength decides
what is a peak, a flat top is ONE peak seeded whole (so the territories are the ones
`read_interiors` draws -- measured on the saved run, where seeding a single place of a flat top
changes two of five series), and a refusal is a name.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from scipy import ndimage as ndi
from skimage.segmentation import watershed

from knee.objects.dome import CONTRACT, dome
from knee.objects.interiors import read_interiors

UNIT = (1.0, 1.0)


def _two_squares() -> np.ndarray:
    """Two 7 x 7 squares, columns 1-7 and 11-17, parted by a wall of obstacle three places wide."""
    interior = np.zeros((9, 19), dtype=bool)
    interior[1:8, 1:8] = True
    interior[1:8, 11:18] = True
    return interior


def _disc(radius: int = 4, size: int = 13) -> np.ndarray:
    """A digital disc whose nearest outside place is exactly `radius` places from its centre."""
    rows, cols = np.mgrid[0:size, 0:size]
    centre = size // 2
    return (rows - centre) ** 2 + (cols - centre) ** 2 < radius**2


def _dumbbell() -> np.ndarray:
    """A 9 x 9 square (height 5), a one-place corridor (height 1), a 3 x 3 square (height 2)."""
    interior = np.zeros((13, 20), dtype=bool)
    interior[2:11, 1:10] = True
    interior[5:8, 14:17] = True
    interior[6, 10:14] = True
    return interior


def _unequal_squares() -> np.ndarray:
    """A 3 x 3 square (height 2) at the top left and a 9 x 9 square (height 5) lower right."""
    interior = np.zeros((14, 20), dtype=bool)
    interior[1:4, 1:4] = True
    interior[3:12, 8:17] = True
    return interior


#: The smallest interior found where seeding a single place of a flat top and seeding the whole
#: flat top disagree: two flat tops of equal height (1.414 mm), one of three places and one of
#: two, and the place at row 3, column 3 between them, which only the whole-plateau seeding
#: gives to the right-hand one (what `read_interiors` does, and the saved run shows).
PLATEAU_CASE = np.array(
    [
        [0, 0, 0, 0, 0, 0],
        [1, 1, 1, 0, 1, 0],
        [0, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1],
        [0, 1, 1, 0, 1, 0],
    ],
    dtype=bool,
)


# --- the proof gate: positive ------------------------------------------------------------------


def test_two_interiors_parted_by_an_obstacle_give_two_peaks_and_two_territories() -> (
    None
):
    interior = _two_squares()
    _, peaks, labels = dome(interior, UNIT, 2.0)
    assert peaks.shape == (2, 2)
    assert peaks.tolist() == [[4, 4], [4, 14]]
    assert np.unique(labels).tolist() == [0, 1, 2]
    # Every interior place is in the territory of the peak on its own side of the wall.
    assert np.all(labels[:, :8][interior[:, :8]] == 1)
    assert np.all(labels[:, 11:][interior[:, 11:]] == 2)


def test_no_territory_crosses_the_obstacle_that_parts_the_interiors() -> None:
    # MUST NOT: carry one peak's territory over the wall, or label the wall itself.
    interior = _two_squares()
    _, _, labels = dome(interior, UNIT, 2.0)
    assert not labels[:, 8:11].any()
    assert not np.isin(labels[:, :8], [2]).any()
    assert not np.isin(labels[:, 11:], [1]).any()
    assert not labels[~interior].any()


def test_a_round_interior_gives_one_peak_at_its_centre_with_its_radius_in_millimetres() -> (
    None
):
    interior = _disc(radius=4)
    height, peaks, labels = dome(interior, (0.5, 0.5), 1.0)
    assert peaks.tolist() == [[6, 6]]
    # The nearest outside place is four places away, at half a millimetre a place.
    assert height[6, 6] == pytest.approx(4 * 0.5)
    assert np.array_equal(labels > 0, interior)
    assert set(np.unique(labels).tolist()) == {0, 1}


def test_an_empty_interior_gives_no_peak_and_all_zero_labels() -> None:
    interior = np.zeros((6, 7), dtype=bool)
    height, peaks, labels = dome(interior, UNIT, 1.0)
    assert peaks.shape == (0, 2) and peaks.dtype == np.int64
    assert labels.shape == (6, 7) and not labels.any()
    assert height.shape == (6, 7) and not height.any()


def test_a_grid_with_no_places_at_all_is_empty_and_never_an_error() -> None:
    for shape in ((0, 5), (5, 0), (0, 0)):
        height, peaks, labels = dome(np.zeros(shape, dtype=bool), UNIT, 1.0)
        assert height.shape == shape and labels.shape == shape
        assert peaks.shape == (0, 2)


def test_the_height_is_zero_on_every_obstacle_and_positive_on_every_interior_place() -> (
    None
):
    interior = _two_squares()
    height, _, _ = dome(interior, UNIT, 2.0)
    assert np.all(height[~interior] == 0.0)
    assert np.all(height[interior] > 0.0)


def test_no_input_is_written_and_every_output_is_frozen() -> None:
    interior = _two_squares()
    interior.setflags(write=False)  # a write to it would raise
    before = interior.copy()
    spacing: Any = np.array([1.0, 1.0])  # an array of two numbers is a spacing too
    spacing.setflags(write=False)
    height, peaks, labels = dome(interior, spacing, 2.0)
    assert np.array_equal(interior, before)
    assert not interior.flags.writeable
    for output in (height, peaks, labels):
        assert not output.flags.writeable
    assert (height.dtype, peaks.dtype, labels.dtype) == (
        np.float64,
        np.int64,
        np.int32,
    )
    # The outputs are the measurement's own storage, never a view of the caller's grid.
    assert not np.shares_memory(height, interior)
    assert not np.shares_memory(labels, interior)


@pytest.mark.parametrize(
    ("interior", "bar"),
    [
        (np.zeros((6, 7), dtype=bool), 1.0),
        (np.zeros((0, 0), dtype=bool), 1.0),
        (_two_squares(), 99.0),
    ],
    ids=[
        "an interior with no place in it",
        "a grid with no places",
        "a bar above every height",
    ],
)
def test_the_no_peak_path_freezes_every_output_too_and_freezes_nothing_of_the_callers(
    interior: np.ndarray, bar: float
) -> None:
    # The early return that seeds nothing is a path of its own (the peak path is checked above):
    # it hands on the measurement's own storage, frozen, of the stated dtype and shape.
    before = interior.copy()
    height, peaks, labels = dome(interior, UNIT, bar)
    assert peaks.shape == (0, 2)
    for output in (height, peaks, labels):
        assert not output.flags.writeable
    assert (height.dtype, peaks.dtype, labels.dtype) == (
        np.float64,
        np.int64,
        np.int32,
    )
    assert height.shape == labels.shape == interior.shape
    assert not labels.any()
    assert not np.shares_memory(height, interior)
    assert not np.shares_memory(labels, interior)
    # The negative sign: reading the caller's grid neither writes nor freezes it.
    assert interior.flags.writeable
    assert np.array_equal(interior, before)


def test_the_same_interior_gives_the_same_answer_twice() -> None:
    first = dome(_two_squares(), UNIT, 2.0)
    second = dome(_two_squares(), UNIT, 2.0)
    for one, other in zip(first, second, strict=True):
        assert np.array_equal(one, other)


# --- the docstring's rules ----------------------------------------------------------------------


def test_the_pictures_edge_is_an_obstacle() -> None:
    # An interior that fills the whole picture is bounded by the frame: the height rises from the
    # edge, one place at the border and three at the centre of a 5 x 5.
    height, peaks, labels = dome(np.ones((5, 5), dtype=bool), UNIT, 1.0)
    assert height[0, 0] == 1.0 and height[0, 2] == 1.0 and height[2, 0] == 1.0
    assert height[2, 2] == 3.0
    assert peaks.tolist() == [[2, 2]]
    assert np.all(labels == 1)


def test_the_spacing_is_row_millimetres_then_column_millimetres() -> None:
    strip = np.ones((1, 7), dtype=bool)
    tall_rows, _, _ = dome(strip, (3.0, 1.0), 0.5)
    # One row high: the row above and below are 3 mm away, the columns' ends 1 mm per place.
    assert tall_rows[0].tolist() == [1.0, 2.0, 3.0, 3.0, 3.0, 2.0, 1.0]
    tall_columns, _, _ = dome(strip, (1.0, 3.0), 0.5)
    assert tall_columns[0].tolist() == [1.0] * 7


def test_a_flat_top_is_one_peak_and_one_territory() -> None:
    # The three places of equal height are a single dome's flat top, not three domes.
    strip = np.ones((1, 7), dtype=bool)
    height, peaks, labels = dome(strip, (3.0, 1.0), 0.5)
    assert peaks.tolist() == [[0, 2]]  # named by its first place in scan order
    assert height[0, 2] == height[0, 3] == height[0, 4] == 3.0
    assert np.all(labels == 1)


def test_a_flat_top_is_seeded_whole_so_the_territories_are_the_ones_read_interiors_draws() -> (
    None
):
    # MUST NOT: seed a flat top at a single place. Two flat tops of equal height with a place
    # between them: seeded whole, that place goes to the right-hand dome (as read_interiors has
    # it); seeded at the left one's first place alone it would go to the left.
    height, peaks, labels = dome(PLATEAU_CASE, UNIT, 1.0)
    assert peaks.tolist() == [[2, 2], [2, 4]]
    assert height[2, 2] == pytest.approx(np.sqrt(2.0))
    assert height[2, 4] == pytest.approx(np.sqrt(2.0))
    assert labels[3, 3] == labels[3, 4] == 2
    assert labels[3, 3] != labels[3, 2]
    assert labels.tolist() == [
        [0, 0, 0, 0, 0, 0],
        [1, 1, 1, 0, 2, 0],
        [0, 1, 1, 1, 2, 2],
        [1, 1, 1, 2, 2, 2],
        [0, 1, 1, 0, 2, 0],
    ]


def test_the_peaks_are_ordered_tallest_first_whatever_their_place_in_the_scan() -> None:
    height, peaks, labels = dome(_unequal_squares(), UNIT, 1.0)
    assert peaks.tolist() == [[7, 12], [2, 2]]
    assert height[7, 12] == 5.0 and height[2, 2] == 2.0
    assert labels[7, 12] == 1 and labels[2, 2] == 2


def test_peaks_of_equal_height_are_ordered_by_scan_order() -> None:
    across = np.zeros((9, 19), dtype=bool)
    across[1:8, 1:8] = True
    across[1:8, 11:18] = True
    _, peaks, _ = dome(across, UNIT, 2.0)
    assert peaks.tolist() == [
        [4, 4],
        [4, 14],
    ]  # the left one first: same row, lower column
    down = across.T.copy()  # the same two squares, one above the other
    _, peaks, _ = dome(down, UNIT, 2.0)
    assert peaks.tolist() == [[4, 4], [14, 4]]  # the upper one first


def test_territory_k_plus_one_belongs_to_peak_k_and_holds_it() -> None:
    interior = _dumbbell()
    _, peaks, labels = dome(interior, UNIT, 0.5)
    assert len(peaks) == 2
    for k, (row, column) in enumerate(peaks.tolist()):
        assert labels[row, column] == k + 1
    assert labels.max() == len(peaks)


def test_prominence_and_not_strength_decides_what_is_a_peak() -> None:
    interior = _dumbbell()
    # The small lobe stands one millimetre above the corridor that joins it to the big one.
    height, peaks, labels = dome(interior, UNIT, 0.5)
    assert peaks.tolist() == [[6, 5], [6, 15]]
    assert height[6, 5] == 5.0 and height[6, 15] == 2.0
    assert set(np.unique(labels[5:8, 14:17]).tolist()) == {2}
    # Under a bar higher than that, the lobe is no peak of its own.
    _, peaks, labels = dome(interior, UNIT, 1.5)
    assert peaks.tolist() == [[6, 5]]


def test_a_dim_dome_is_never_cut_away_only_not_seeded() -> None:
    # MUST NOT: drop the small lobe's places because it is weaker. Nothing is cut on strength: it
    # is flooded by the territory it hangs from, and every interior place stays labelled.
    interior = _dumbbell()
    _, _, labels = dome(interior, UNIT, 1.5)
    assert np.all(labels[interior] == 1)
    assert not labels[~interior].any()


def test_a_bar_above_every_height_seeds_nothing_and_keeps_the_height() -> None:
    interior = _dumbbell()
    height, peaks, labels = dome(interior, UNIT, 5.5)
    assert peaks.shape == (0, 2) and not labels.any()
    assert height.max() == 5.0


def test_an_interior_place_no_peak_reaches_stays_zero() -> None:
    interior = np.zeros((10, 12), dtype=bool)
    interior[1:9, 1:6] = True
    interior[4, 9] = True  # one place, apart, 1 mm high against a 2 mm bar
    height, peaks, labels = dome(interior, UNIT, 2.0)
    assert peaks.tolist() == [[3, 3]]
    assert height[4, 9] == 1.0
    assert labels[4, 9] == 0
    assert np.all(labels[1:9, 1:6] == 1)


def test_an_interior_given_as_integers_is_read_as_non_zero_meaning_interior() -> None:
    as_bool = dome(_two_squares(), UNIT, 2.0)
    as_uint8 = dome(_two_squares().astype(np.uint8), UNIT, 2.0)
    as_int = dome((_two_squares() * 5).astype(np.int64), UNIT, 2.0)
    for other in (as_uint8, as_int):
        for one, two in zip(as_bool, other, strict=True):
            assert np.array_equal(one, two)


def test_numbers_of_any_numeric_type_are_accepted_for_the_bar_and_the_spacing() -> None:
    reference = dome(_two_squares(), (1.0, 1.0), 2.0)
    spacing: Any = (np.float32(1.0), 1)
    bar: Any = np.int64(2)
    other = dome(_two_squares(), spacing, bar)
    for one, two in zip(reference, other, strict=True):
        assert np.array_equal(one, two)


# --- the refusals, each a name -----------------------------------------------------------------


@pytest.mark.parametrize(
    "bar",
    [0, 0.0, -1.0, float("nan"), float("inf"), -float("inf"), True, None, "2", 1j],
)
def test_a_bar_that_is_not_a_finite_positive_number_is_refused_by_name(
    bar: Any,
) -> None:
    with pytest.raises(ValueError, match="invalid_prominence_mm"):
        dome(_two_squares(), UNIT, bar)


@pytest.mark.parametrize(
    "spacing",
    [
        (0.0, 1.0),
        (1.0, -1.0),
        (1.0, float("nan")),
        (float("inf"), 1.0),
        (1.0,),
        (1.0, 1.0, 1.0),
        (True, 1.0),
        ("a", "b"),
        None,
        1.0,
        np.array([[1.0, 1.0]]),
        np.array(1.0),
        {1.0: 1.0, 2.0: 2.0},
    ],
)
def test_a_spacing_that_is_not_two_finite_positive_numbers_is_refused_by_name(
    spacing: Any,
) -> None:
    with pytest.raises(ValueError, match="invalid_spacing"):
        dome(_two_squares(), spacing, 2.0)


@pytest.mark.parametrize(
    "interior",
    [
        np.ones(5, dtype=bool),
        np.ones((2, 3, 4), dtype=bool),
        np.ones((3, 3), dtype=np.float64),
        np.full((3, 3), np.nan),
        np.array(True),
        None,
        [[True, False], [True]],
        "ab",
    ],
)
def test_an_interior_that_is_not_a_two_dimensional_grid_of_booleans_is_refused_by_name(
    interior: Any,
) -> None:
    # A coerced float would turn a missing reading into a place; a vector or a volume is no grid.
    with pytest.raises(ValueError, match="invalid_interior"):
        dome(interior, UNIT, 2.0)


def test_a_refusal_comes_before_any_measurement_and_writes_nothing() -> None:
    interior = _two_squares()
    interior.setflags(write=False)
    with pytest.raises(ValueError, match="invalid_prominence_mm"):
        dome(interior, (0.0, 1.0), float("nan"))  # both wrong: the bar is named first
    assert not interior.flags.writeable


# --- one rule at two scales: the dome answers to read_interiors ---------------------------------


def _read_interiors_of(interior: np.ndarray, spacing: tuple[float, float], bar: float):
    """What the native interiors make of the same interior: a plane that is bright exactly there."""
    plane = np.where(interior, 8.0, 0.0)
    return read_interiors(plane, spacing, 0.0, bar, np.array([-1.0, 0.0, 1.0]))


def _same_territories_under_a_renumbering(
    peaks: np.ndarray, labels: np.ndarray, reading
) -> bool:
    """The dome numbers its territories by height rank, the native reading by scan order of the
    flat top's first place; they are the same partition iff each peak lies in its own marker and
    the renumbering carries one onto the other."""
    markers = reading.markers
    seeded = markers[peaks[:, 0], peaks[:, 1]] if len(peaks) else np.zeros(0, dtype=int)
    if len(peaks) != int(markers.max(initial=0)) or (seeded <= 0).any():
        return False
    if len(set(seeded.tolist())) != len(peaks):
        return False
    to_native = np.zeros(len(peaks) + 1, dtype=np.int64)
    to_native[1:] = seeded
    return bool(np.array_equal(to_native[labels], reading.labels))


@pytest.mark.parametrize(
    ("interior", "spacing", "bar"),
    [
        (_two_squares(), (1.0, 1.0), 2.0),
        (_dumbbell(), (0.5, 0.5), 0.5),
        (_dumbbell(), (0.5, 1.5), 1.0),
        (PLATEAU_CASE, (1.0, 1.0), 1.0),
        (np.ones((6, 9), dtype=bool), (1.0, 2.0), 1.0),
    ],
)
def test_the_dome_is_the_native_interiors_height_and_territories(
    interior: np.ndarray, spacing: tuple[float, float], bar: float
) -> None:
    reading = _read_interiors_of(interior, spacing, bar)
    height, peaks, labels = dome(interior, spacing, bar)
    assert np.array_equal(height, reading.distance_mm)
    assert _same_territories_under_a_renumbering(peaks, labels, reading)


def test_seeding_each_peak_at_one_place_would_not_be_the_native_reading() -> None:
    # The negative sign of the claim above, and the reason the flat top is seeded whole: with the
    # same peaks seeded at their one named place each, the place between the two flat tops goes
    # to the left-hand dome, and that is NOT what read_interiors draws.
    reading = _read_interiors_of(PLATEAU_CASE, UNIT, 1.0)
    height, peaks, labels = dome(PLATEAU_CASE, UNIT, 1.0)
    one_place = np.zeros(PLATEAU_CASE.shape, dtype=np.int32)
    for k, (row, column) in enumerate(peaks.tolist()):
        one_place[row, column] = k + 1
    seeded_at_one_place = watershed(
        -height, one_place, mask=PLATEAU_CASE, connectivity=1
    )
    assert seeded_at_one_place[3, 3] != labels[3, 3]
    assert reading.labels[3, 3] == reading.labels[3, 4]
    assert labels[3, 3] == labels[3, 4]


def _as_the_native_reading_numbers_them(
    height: np.ndarray, peaks: np.ndarray, labels: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """The native reading's labels and markers, rebuilt from the dome's own outputs alone.

    Each peak is named by the first place of its flat top in scan order, which is also how scipy's
    `label` numbers its components, so ranking the peaks by (row, column) renumbers the dome's
    territories as `read_interiors` numbers them; and a flat top is the places of equal height,
    four-connected to its peak, inside its own territory. This is the recipe task 5.1's
    byte-identical check needs (verified on the five series of the saved run).
    """
    order = np.lexsort((peaks[:, 1], peaks[:, 0]))
    to_scan = np.zeros(len(peaks) + 1, dtype=np.int32)
    to_scan[order + 1] = np.arange(1, len(peaks) + 1, dtype=np.int32)
    markers = np.zeros(labels.shape, dtype=np.int32)
    for k, (row, column) in enumerate(peaks.tolist()):
        top, _ = ndi.label((labels == k + 1) & (height == height[row, column]))
        markers[top == top[row, column]] = to_scan[k + 1]
    return to_scan[labels], markers


@pytest.mark.parametrize(
    ("interior", "spacing", "bar"),
    [
        (_two_squares(), (1.0, 1.0), 2.0),
        (_unequal_squares(), (1.0, 1.0), 1.0),
        (_dumbbell(), (0.5, 0.5), 0.5),
        (PLATEAU_CASE, (1.0, 1.0), 1.0),
        (np.ones((6, 9), dtype=bool), (1.0, 2.0), 1.0),
    ],
)
def test_the_native_labels_and_markers_are_the_dome_renumbered_by_the_scan_order_of_its_peaks(
    interior: np.ndarray, spacing: tuple[float, float], bar: float
) -> None:
    reading = _read_interiors_of(interior, spacing, bar)
    height, peaks, labels = dome(interior, spacing, bar)
    rebuilt_labels, rebuilt_markers = _as_the_native_reading_numbers_them(
        height, peaks, labels
    )
    np.testing.assert_array_equal(rebuilt_labels, reading.labels)
    np.testing.assert_array_equal(rebuilt_markers, reading.markers)


def test_the_dome_numbers_by_height_so_the_native_labels_are_a_renumbering_of_it() -> (
    None
):
    # The negative sign: with the taller dome later in the scan, the dome's numbers and the native
    # reading's are NOT the same numbers over the same territories -- the byte-identical check of
    # task 5.1 holds only through the renumbering above, never by handing the labels on as they are.
    interior = _unequal_squares()
    reading = _read_interiors_of(interior, UNIT, 1.0)
    _, peaks, labels = dome(interior, UNIT, 1.0)
    assert peaks.tolist() == [[7, 12], [2, 2]]
    assert not np.array_equal(labels, reading.labels)
    assert reading.labels[2, 2] == 1 and labels[2, 2] == 2
    assert _same_territories_under_a_renumbering(peaks, labels, reading)


# --- properties, over unions of rectangles -------------------------------------------------------


@st.composite
def _interiors(draw) -> np.ndarray:
    rows = draw(st.integers(3, 12))
    columns = draw(st.integers(3, 12))
    grid = np.zeros((rows, columns), dtype=bool)
    for _ in range(draw(st.integers(0, 4))):
        r0 = draw(st.integers(0, rows - 1))
        c0 = draw(st.integers(0, columns - 1))
        r1 = draw(st.integers(r0 + 1, rows))
        c1 = draw(st.integers(c0 + 1, columns))
        grid[r0:r1, c0:c1] = True
    return grid


_spacings = st.tuples(
    st.sampled_from([0.5, 1.0, 2.0]), st.sampled_from([0.5, 1.0, 2.0])
)
_bars = st.sampled_from([0.5, 1.0, 1.5, 2.0, 3.0])


@settings(max_examples=120, deadline=None)
@given(interior=_interiors(), spacing=_spacings, bar=_bars)
def test_the_dome_keeps_its_stated_invariants_over_any_interior(
    interior: np.ndarray, spacing: tuple[float, float], bar: float
) -> None:
    before = interior.copy()
    height, peaks, labels = dome(interior, spacing, bar)
    assert np.array_equal(interior, before)
    assert height.shape == labels.shape == interior.shape
    assert peaks.ndim == 2 and peaks.shape[1] == 2
    # Height: zero off the interior, positive on it; labels live only on the interior.
    assert np.all(height[~interior] == 0.0) and np.all(height[interior] > 0.0)
    assert not labels[~interior].any()
    assert labels.min() >= 0 and labels.max() <= len(peaks)
    # Each peak is an interior place that carries its own territory number, none repeated, and
    # they run tallest first.
    assert len({tuple(peak) for peak in peaks.tolist()}) == len(peaks)
    for k, (row, column) in enumerate(peaks.tolist()):
        assert interior[row, column]
        assert labels[row, column] == k + 1
    standing = height[peaks[:, 0], peaks[:, 1]]
    assert np.all(np.diff(standing) <= 0.0)
    # A peak stands at least the bar above its surroundings, and no height is negative, so every
    # peak is at least the bar high.
    assert np.all(standing >= bar)


@settings(max_examples=60, deadline=None)
@given(interior=_interiors(), spacing=_spacings, bar=_bars)
def test_the_dome_is_the_native_reading_over_any_interior(
    interior: np.ndarray, spacing: tuple[float, float], bar: float
) -> None:
    reading = _read_interiors_of(interior, spacing, bar)
    height, peaks, labels = dome(interior, spacing, bar)
    assert np.array_equal(height, reading.distance_mm)
    assert _same_territories_under_a_renumbering(peaks, labels, reading)


@settings(max_examples=60, deadline=None)
@given(interior=_interiors(), spacing=_spacings, bar=_bars)
def test_the_native_numbering_is_the_dome_renumbered_over_any_interior(
    interior: np.ndarray, spacing: tuple[float, float], bar: float
) -> None:
    reading = _read_interiors_of(interior, spacing, bar)
    height, peaks, labels = dome(interior, spacing, bar)
    rebuilt_labels, rebuilt_markers = _as_the_native_reading_numbers_them(
        height, peaks, labels
    )
    assert np.array_equal(rebuilt_labels, reading.labels)
    assert np.array_equal(rebuilt_markers, reading.markers)


def test_the_contract_names_this_file_as_its_proof_gate() -> None:
    assert "tests/knee/objects/test_dome.py" in CONTRACT.proof_gate
    assert CONTRACT.reference == "dome"
