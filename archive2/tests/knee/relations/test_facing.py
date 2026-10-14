"""The facing pairs of one chosen slice, their picture's arrangement and their drawer (the-funnel
tasks 7.1 and 7.2), both signs.

Four parts, in this order. The orchestration `read_facing` over hand-built records of the
stage's predecessors: two objects face across a chain of dark tiles that touches both, wider than
one tile too, inside the overlap of their widths, and never through cleared air; objects that
touch with no dark tile between them are named so; an unselected territory is never in a pair;
every silence and every refusal is named; every count is a plain number the decision accepts; the
ledger rows and the frozen arrays are as the contract says. The arrangement of the saved record
for the picture (`knee.pictures.facing`). The drawer's reader, which refuses a saved record that
disagrees with the writer, by name. The drawer end to end on a hand-built record written to a
temporary directory.

A tile picture reads: a digit is a territory, `.` a dark obstacle, `#` an obstacle the first lens
cleared, `+` an interior tile no territory holds, `_` a tile with no reading. Every input array is
frozen, so any write to an input fails loudly. Every call to a function under test is in the body
of the test that makes it.
"""

from __future__ import annotations

import copy
import functools
import json
import shutil
import uuid
from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from knee.collapse.squint_stack import read_squint_stack
from knee.compute.contracts import handed_on
from knee.objects.selection import ObjectRecord, Selection, TerritoryFacts
from knee.objects.tile_dome import TileDome
from knee.pictures import facing as pictures
from knee.pictures.facing import (
    PLANE_SOURCES,
    SLICE_STANDINGS,
    facing_panels,
    slice_standing,
)
from knee.relations.facing import (
    FACING_CODES,
    FACING_RECORD_CODES,
    FacingPairs,
    _beside,
    between_region,
    read_facing,
)
from knee.study.series import Series, SeriesGeometry, walk_indices
from knee.study.tables import SeriesRow
from knee.telemetry import recording
from workbench.measure.object_analysis import array_table, squint_stack_record
from workbench.render import facing_frames
from workbench.render._out import PROJECT, ArgumentRefusal

# --- the hand-built records ---------------------------------------------------------------------

#: The border every hand-built record is read under (`knee.objects.tile_dome.BORDER_CODES`): the
#: dome and the selection of a pair must agree on it, and the pairs carry it on.
BORDER = "dark_on_both"

#: The two big objects a coronal-like slice would name; a third carries no role.
ROLES = {1: "superior_big", 2: "inferior_big"}

#: Two territories parted by one dark row: the plain case of two objects facing.
PARTED = ("111111", "111111", "......", "222222", "222222")


def _dome(
    picture: tuple[str, ...],
    *,
    height: np.ndarray | None = None,
    slice_index: int = 3,
) -> TileDome:
    """A present dome read off a tile picture, every array frozen.

    The height defaults to what the dome measures: zero on every obstacle and a positive distance
    on the interior. A test that needs another height or another slice passes it.
    """
    rows, columns = len(picture), len(picture[0])
    assert all(len(line) == columns for line in picture)
    labels = np.zeros((rows, columns), dtype=np.int32)
    obstacle = np.zeros((rows, columns), dtype=bool)
    cleared = np.zeros((rows, columns), dtype=bool)
    interior = np.zeros((rows, columns), dtype=bool)
    for row, line in enumerate(picture):
        for column, mark in enumerate(line):
            if mark.isdigit():
                labels[row, column] = int(mark)
                interior[row, column] = True
            elif mark == ".":
                obstacle[row, column] = True
            elif mark == "#":
                obstacle[row, column] = cleared[row, column] = True
            elif mark == "+":
                interior[row, column] = True
            else:
                assert mark == "_", mark
    if height is None:
        height = np.where(interior, 8.0, 0.0)
    return TileDome(
        series_uid="series",
        slice_index=slice_index,
        code="present",
        why="built by hand",
        prominence_mm=8.0,
        obstacle=handed_on(obstacle),
        cleared=handed_on(cleared),
        interior=handed_on(interior),
        height=handed_on(np.asarray(height, dtype=np.float64)),
        peaks=handed_on(np.zeros((0, 2), dtype=np.int64)),
        peak_height_mm=handed_on(np.zeros(0)),
        labels=handed_on(labels),
        border=BORDER,
    )


def _absent_dome(code: str) -> TileDome:
    """A dome that holds no reading: empty arrays of the right rank, the slice -1."""
    nothing = np.zeros((0, 0), dtype=bool)
    return TileDome(
        series_uid="series",
        slice_index=-1,
        code=code,
        why="built by hand, absent",
        prominence_mm=8.0,
        obstacle=nothing,
        cleared=nothing,
        interior=nothing,
        height=np.zeros((0, 0)),
        peaks=np.zeros((0, 2), dtype=np.int64),
        peak_height_mm=np.zeros(0),
        labels=np.zeros((0, 0), dtype=np.int32),
        border=BORDER,
    )


def _facts(index: int) -> TerritoryFacts:
    return TerritoryFacts(
        index=index,
        tiles=4,
        centre_lps=np.zeros(3),
        superior_mm=0.0,
        anterior_mm=0.0,
        left_right_mm=0.0,
        superior_extent_mm=(0.0, 0.0),
        anterior_face_mm=0.0,
        touches_leg_border=False,
        ringed=False,
    )


def _selection(
    roles: dict[int, str], *, code: str = "present", slice_index: int = 3
) -> Selection:
    """A selection naming each territory's role, in label order."""
    return Selection(
        series_uid="series",
        slice_index=slice_index,
        plane_kind="Coronal",
        code=code,
        why="built by hand",
        pair_code="selected",
        objects=tuple(
            ObjectRecord(index=index, role_code=role, facts=_facts(index), tiles=4)
            for index, role in sorted(roles.items())
        ),
        candidate_codes=(),
        border=BORDER,
    )


def _tiles(shape: tuple[int, int], *cells: tuple[int, int]) -> np.ndarray:
    """A bool tile map with exactly the listed (row, column) tiles set."""
    mask = np.zeros(shape, dtype=bool)
    for row, column in cells:
        mask[row, column] = True
    return mask


def _picture_of(grid: np.ndarray) -> tuple[str, ...]:
    """A grid of one-character cells as a tile picture."""
    return tuple("".join(row) for row in grid)


def _crossings(labels: np.ndarray, first: int, second: int) -> int:
    """The four-adjacent tile pairs holding exactly these two labels, counted by plain loops."""
    count = 0
    rows, columns = labels.shape
    for row in range(rows):
        for column in range(columns):
            for down, across in ((0, 1), (1, 0)):
                other_row, other_column = row + down, column + across
                if other_row < rows and other_column < columns:
                    pair = {
                        int(labels[row, column]),
                        int(labels[other_row, other_column]),
                    }
                    if pair == {first, second}:
                        count += 1
    return count


# --- the orchestration: two objects face across dark tiles that touch both -----------------------


def test_two_objects_parted_by_one_dark_row_face_across_it() -> None:
    dome = _dome(PARTED)
    result = read_facing(dome, _selection(ROLES), 1)
    assert result.code == "present"
    assert (result.series_uid, result.slice_index, result.minimum_sites) == (
        "series",
        3,
        1,
    )
    (pair,) = result.pairs
    assert (pair.first, pair.second) == (1, 2)
    assert (pair.first_role, pair.second_role) == ("superior_big", "inferior_big")
    assert pair.code == "facing"
    assert (pair.sites, pair.gap_sites) == (0, 6)
    np.testing.assert_array_equal(
        pair.gap_tiles, _tiles((5, 6), *[(2, column) for column in range(6)])
    )
    # The dome's height is zero on every obstacle, and the gap is made of obstacles.
    assert pair.saddle_mm == 0.0


@pytest.mark.parametrize("width", [2, 3])
def test_a_dark_space_two_or_three_tiles_wide_still_faces(width: int) -> None:
    # The Codex check of 2026-10-13: two objects face across a gap wider than one tile, and a
    # chain of dark tiles that touches both is the gap. One tile touching both was the first
    # wording of the contract.
    picture = ("111111", "111111", *("......",) * width, "222222", "222222")
    result = read_facing(_dome(picture), _selection(ROLES), 1)
    (pair,) = result.pairs
    assert pair.code == "facing"
    assert pair.gap_sites == 6 * width
    cells = [(row, column) for row in range(2, 2 + width) for column in range(6)]
    np.testing.assert_array_equal(pair.gap_tiles, _tiles((4 + width, 6), *cells))


def test_cleared_air_between_two_objects_is_never_a_gap() -> None:
    result = read_facing(
        _dome(("111111", "111111", "######", "222222", "222222")), _selection(ROLES), 1
    )
    (pair,) = result.pairs
    assert pair.code == "too_few_sites"
    assert (pair.sites, pair.gap_sites) == (0, 0)
    assert not pair.gap_tiles.any()
    assert np.isnan(pair.saddle_mm)


def test_cleared_air_cuts_a_chain_of_dark_tiles_so_neither_part_touches_both() -> None:
    # Dark, then air, then dark: each dark row touches one object only. A chain that touches
    # both is the gap; two chains that touch one each are not.
    result = read_facing(
        _dome(("111111", "......", "######", "......", "222222")), _selection(ROLES), 1
    )
    (pair,) = result.pairs
    assert pair.code == "too_few_sites"
    assert pair.gap_sites == 0


def test_a_dark_column_beside_both_objects_is_outside_the_overlap_of_their_widths() -> (
    None
):
    # The dark column touches the top object and the bottom object and is one connected chain,
    # but it lies beside them, outside the columns both occupy, so it is not between them.
    result = read_facing(
        _dome(("111.", "111.", "###.", "222.", "222.")), _selection(ROLES), 1
    )
    (pair,) = result.pairs
    assert pair.code == "too_few_sites"
    assert pair.gap_sites == 0


def test_the_gap_of_a_sideways_offset_pair_lies_only_where_the_two_face_each_other() -> (
    None
):
    # The dark row runs the whole width, but the top object spans columns 0 to 3 and the
    # bottom one columns 2 to 5: the gap is the two columns they share.
    result = read_facing(
        _dome(("1111..", "1111..", "......", "..2222", "..2222")), _selection(ROLES), 1
    )
    (pair,) = result.pairs
    assert pair.code == "facing"
    np.testing.assert_array_equal(pair.gap_tiles, _tiles((5, 6), (2, 2), (2, 3)))


def test_a_wide_object_over_a_narrow_one_has_a_gap_only_where_the_narrow_one_faces_it() -> (
    None
):
    # The dark row runs under the whole of the wide object and touches it everywhere, and it is
    # one connected chain that touches the narrow one at its two columns. Only those two columns
    # lie in the overlap of the widths: the rest of the row is beside the narrow object.
    result = read_facing(
        _dome(("111111", "111111", "......", "..22..", "..22..")), _selection(ROLES), 1
    )
    (pair,) = result.pairs
    assert pair.code == "facing"
    np.testing.assert_array_equal(pair.gap_tiles, _tiles((5, 6), (2, 2), (2, 3)))


def test_a_chain_of_dark_tiles_that_meets_only_at_corners_is_not_a_chain() -> None:
    # The dark tile under the top object and the dark tile above the bottom one touch only at a
    # corner. Each touches one object: two parts, neither touching both, so there is no gap.
    result = read_facing(_dome(("#22", "#.#", ".#.", "#11")), _selection(ROLES), 1)
    (pair,) = result.pairs
    assert pair.code == "too_few_sites"
    assert pair.gap_sites == 0


def test_the_gap_does_not_depend_on_how_the_grid_is_turned_or_which_territory_is_first() -> (
    None
):
    # A gap is a fact about the two territories and the dark tiles, not about the grid's
    # orientation or the order the labels came in. Over random layouts of two rectangles in dark
    # and cleared tiles, flipping or turning the grid turns the gap the same way, and swapping the
    # two labels leaves it where it was. A centre taken from one tile instead of the mean of all
    # of them fails this, because the first tile in scan order is not turned with the grid.
    rng = np.random.default_rng(2026)
    swap = str.maketrans("12", "21")
    turns = (np.fliplr, np.flipud, np.rot90, np.transpose)
    with_a_gap = 0
    for _ in range(400):
        rows, columns = (int(size) for size in rng.integers(4, 8, size=2))
        cells = np.where(rng.random((rows, columns)) < 0.25, "#", ".")
        for label in "12":
            for _try in range(20):
                low_row, high_row = sorted(
                    int(n) for n in rng.integers(0, rows + 1, size=2)
                )
                low_col, high_col = sorted(
                    int(n) for n in rng.integers(0, columns + 1, size=2)
                )
                block = cells[low_row:high_row, low_col:high_col]
                if block.size and not np.isin(block, ["1", "2"]).any():
                    cells[low_row:high_row, low_col:high_col] = label
                    break
        if not (cells == "1").any() or not (cells == "2").any():
            continue
        selection = _selection(ROLES)
        base = read_facing(_dome(_picture_of(cells)), selection, 1).pairs[0].gap_tiles
        with_a_gap += bool(base.any())
        for turn in turns:
            turned = read_facing(_dome(_picture_of(turn(cells))), selection, 1)
            np.testing.assert_array_equal(turned.pairs[0].gap_tiles, turn(base))
        relabelled = np.array([list("".join(row).translate(swap)) for row in cells])
        swapped = read_facing(_dome(_picture_of(relabelled)), selection, 1)
        np.testing.assert_array_equal(swapped.pairs[0].gap_tiles, base)
    # The property is exercised on layouts that have a gap, not only on empty ones.
    assert with_a_gap >= 40


def test_objects_that_touch_with_no_dark_tile_between_them_are_named_not_faced() -> (
    None
):
    picture = ("111111", "111111", "222222", "222222")
    dome = _dome(picture)
    result = read_facing(dome, _selection(ROLES), 1)
    (pair,) = result.pairs
    assert pair.code == "touching_no_gap"
    assert (pair.sites, pair.gap_sites) == (6, 0)
    assert pair.sites == _crossings(np.asarray(dome.labels), 1, 2)
    assert np.isnan(pair.saddle_mm)


def test_the_direct_sites_are_four_adjacent_crossings_and_never_a_corner() -> None:
    # Two blocks that meet at a corner share no edge: no site. The two dark tiles beside the
    # corner each touch both blocks, so the pair faces across them.
    dome = _dome(("11..", "11..", "..22", "..22"))
    result = read_facing(dome, _selection(ROLES), 1)
    (pair,) = result.pairs
    assert pair.sites == 0 == _crossings(np.asarray(dome.labels), 1, 2)
    assert pair.code == "facing"
    np.testing.assert_array_equal(pair.gap_tiles, _tiles((4, 4), (1, 2), (2, 1)))
    # A side-by-side pair shares an edge along three rows.
    side = _dome(("1122", "1122", "1122"))
    (touching,) = read_facing(side, _selection(ROLES), 1).pairs
    assert touching.sites == 3 == _crossings(np.asarray(side.labels), 1, 2)
    assert touching.code == "touching_no_gap"


def test_facing_outranks_touching_when_the_gap_meets_the_bar() -> None:
    # One crossing and one dark tile at the inner corner of the L: facing at a bar of one,
    # only touching at a bar of two. The bar is an argument.
    dome = _dome(("...1", "...1", "2221"))
    selection = _selection(ROLES)
    (faced,) = read_facing(dome, selection, 1).pairs
    assert (faced.sites, faced.gap_sites, faced.code) == (1, 1, "facing")
    (touched,) = read_facing(dome, selection, 2).pairs
    assert (touched.sites, touched.gap_sites, touched.code) == (1, 1, "touching_no_gap")


def test_the_bar_on_gap_tiles_is_an_argument_and_zero_still_needs_one_tile() -> None:
    dome = _dome(("11", "11", "..", "22", "22"))
    selection = _selection(ROLES)
    codes = {
        bar: read_facing(dome, selection, bar).pairs[0].code for bar in (0, 1, 2, 3)
    }
    assert codes == {0: "facing", 1: "facing", 2: "facing", 3: "too_few_sites"}
    # With no gap tile at all a bar of zero is not met.
    (parted_by_air,) = read_facing(
        _dome(("11", "11", "##", "22", "22")), selection, 0
    ).pairs
    assert parted_by_air.code == "too_few_sites"


def test_a_third_territory_between_two_cuts_the_chain_between_them() -> None:
    picture = ("111111", "......", "333333", "......", "222222")
    dome = _dome(picture)
    # The middle territory is unselected: the pair of the outer two does not face.
    (pair,) = read_facing(dome, _selection({**ROLES, 3: "unselected"}), 1).pairs
    assert (pair.first, pair.second) == (1, 2)
    assert pair.code == "too_few_sites"
    # With a role it is a third object, and each outer object faces it.
    pairs = read_facing(dome, _selection({1: "a", 2: "b", 3: "c"}), 1).pairs
    assert [(p.first, p.second, p.code) for p in pairs] == [
        (1, 2, "too_few_sites"),
        (1, 3, "facing"),
        (2, 3, "facing"),
    ]


def test_an_unselected_territory_is_never_in_a_pair_even_when_it_faces_an_object() -> (
    None
):
    # Territory 3 faces territory 1 across a dark row; it carries no role.
    dome = _dome(("111", "...", "333", "...", "222"))
    result = read_facing(dome, _selection({1: "a", 2: "b", 3: "unselected"}), 1)
    assert [(p.first, p.second) for p in result.pairs] == [(1, 2)]
    assert all(3 not in (p.first, p.second) for p in result.pairs)
    assert all(p.code != "not_selected" for p in result.pairs)


def test_every_pair_of_roled_territories_is_kept_in_ascending_label_order() -> None:
    dome = _dome(("111", "...", "222", "...", "444", "...", "333"))
    roles = {4: "d", 1: "a", 3: "c", 2: "b"}
    result = read_facing(dome, _selection(roles), 1)
    pairs = [(p.first, p.second) for p in result.pairs]
    assert pairs == [(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)]
    assert all(p.first < p.second for p in result.pairs)
    assert (result.pairs[0].first_role, result.pairs[0].second_role) == ("a", "b")
    # Nothing is dropped: a pair that does not face stays, with its own code.
    by_pair = {(p.first, p.second): p.code for p in result.pairs}
    assert by_pair[(1, 3)] == "too_few_sites"
    assert set(by_pair.values()) <= set(FACING_CODES)


def test_a_roled_object_with_no_tile_on_the_grid_is_a_pair_with_nothingbetween_region() -> (
    None
):
    # The selection names a territory the grid holds no tile of: it has nothing to touch and no
    # centre to draw a line from, so each of its pairs is named, kept and empty.
    result = read_facing(
        _dome(PARTED), _selection({1: "superior_big", 2: "inferior_big", 9: "c"}), 1
    )
    by_pair = {(p.first, p.second): p for p in result.pairs}
    assert set(by_pair) == {(1, 2), (1, 9), (2, 9)}
    assert by_pair[(1, 2)].code == "facing"
    for ghost in ((1, 9), (2, 9)):
        pair = by_pair[ghost]
        assert pair.code == "too_few_sites"
        assert (pair.sites, pair.gap_sites) == (0, 0)
        assert not pair.gap_tiles.any() and pair.gap_tiles.shape == (5, 6)
        assert np.isnan(pair.saddle_mm)


def test_the_saddle_is_the_least_height_over_the_gap_tiles_and_nowhere_else() -> None:
    height = np.full((5, 6), 50.0)
    height[2] = [9.0, 7.5, 4.0, 6.0, 8.0, 5.0]
    # A shallower tile elsewhere on the slice is not on the gap, so it does not enter either.
    height[0, 0] = 0.5
    result = read_facing(_dome(PARTED, height=height), _selection(ROLES), 1)
    (pair,) = result.pairs
    assert pair.saddle_mm == 4.0
    # A pair with no gap tile has no saddle: NaN, never zero.
    (touching,) = read_facing(
        _dome(("111", "222"), height=np.full((2, 3), 3.0)), _selection(ROLES), 1
    ).pairs
    assert np.isnan(touching.saddle_mm)


def test_the_record_holds_plain_numbers_so_the_decision_never_refuses_them() -> None:
    # `facing_code` refuses a NumPy integer as `invalid_measurement`. The counts come out of
    # NumPy arrays; each must be converted before the decision reads it.
    (pair,) = read_facing(_dome(PARTED), _selection(ROLES), 1).pairs
    assert pair.code == "facing"
    assert pair.code != "invalid_measurement"
    assert type(pair.sites) is int
    assert type(pair.gap_sites) is int
    assert type(pair.first) is int and type(pair.second) is int
    assert type(pair.saddle_mm) is float


# --- the silences ---------------------------------------------------------------------------------


def test_fewer_than_two_roled_objects_is_no_pair_and_names_how_many_had_a_role() -> (
    None
):
    dome = _dome(PARTED)
    one = read_facing(dome, _selection({1: "superior_big", 2: "unselected"}), 1)
    assert (one.code, one.pairs) == ("no_pair", ())
    assert "1 of 2 territories carry a role" in one.why
    none = read_facing(dome, _selection({1: "unselected", 2: "unselected"}), 1)
    assert (none.code, none.pairs) == ("no_pair", ())
    empty = read_facing(dome, _selection({}), 1)
    assert (empty.code, empty.pairs) == ("no_pair", ())
    assert (one.series_uid, one.slice_index, one.minimum_sites) == ("series", 3, 1)


@pytest.mark.parametrize("dome_code", ["no_interior", "predecessor_absent"])
@pytest.mark.parametrize("selection_code", ["no_territory", "predecessor_absent"])
def test_a_dome_or_a_selection_that_is_not_present_is_predecessor_absent(
    dome_code: str, selection_code: str
) -> None:
    # A selection is made from a dome, so it stands at the dome's slice, here -1: `read_facing`
    # refuses records that are not of one series, one slice and one border.
    absent = read_facing(
        _absent_dome(dome_code),
        _selection({}, code=selection_code, slice_index=-1),
        1,
    )
    assert absent.code == "predecessor_absent"
    assert absent.pairs == ()
    assert f"the tile dome is {dome_code}" in absent.why
    assert f"the selection is {selection_code}" in absent.why
    # The dome locates the slice: its series and its slice index, here -1, are the record's.
    assert (absent.series_uid, absent.slice_index) == ("series", -1)
    # Either one alone is enough, and the why names only the one that is absent.
    only_dome = read_facing(
        _absent_dome(dome_code), _selection(ROLES, slice_index=-1), 1
    )
    assert only_dome.code == "predecessor_absent"
    assert f"the tile dome is {dome_code}" in only_dome.why
    assert "the selection" not in only_dome.why
    only_selection = read_facing(_dome(PARTED), _selection({}, code=selection_code), 1)
    assert only_selection.code == "predecessor_absent"
    assert f"the selection is {selection_code}" in only_selection.why
    assert "the tile dome" not in only_selection.why


# --- the refusal and the ledger ----------------------------------------------------------------


@pytest.mark.parametrize(
    "bar", [-1, True, False, 1.5, "1", None, np.int64(1), (1,), float("nan")]
)
def test_a_bar_that_is_not_a_non_negative_int_is_refused_before_any_ledger_event(
    bar: Any,
) -> None:
    with (
        recording() as run_ledger,
        pytest.raises(ValueError, match="invalid_minimum_sites"),
    ):
        read_facing(_dome(PARTED), _selection(ROLES), bar)
    assert run_ledger.events() == ()


def test_the_consumer_records_each_read_and_the_producer_its_count() -> None:
    with recording() as run_ledger:
        read_facing(_dome(PARTED), _selection(ROLES), 1)
    events = [(event.name, dict(event.counts)) for event in run_ledger.events()]
    assert events[0] == ("tile_dome.consumed_by.facing", {"dome": 1})
    assert events[1] == ("selection.consumed_by.facing", {"selection": 1})
    assert events[-1] == ("facing.produced", {"pairs": 1})
    # The sites are the census's own count, so the census recorded its work between them.
    assert [name for name, _ in events if name.startswith("objects.")] == [
        "objects.boundary_census"
    ]
    # A pair that does not face is produced and kept but not counted as facing.
    with recording() as touching_ledger:
        read_facing(_dome(("111", "222")), _selection(ROLES), 1)
    assert [(e.name, dict(e.counts)) for e in touching_ledger.events()][-1] == (
        "facing.produced",
        {"pairs": 0},
    )


def test_a_silence_records_the_reads_with_their_counts_and_produces_nothing() -> None:
    with recording() as run_ledger:
        read_facing(
            _absent_dome("predecessor_absent"), _selection(ROLES, slice_index=-1), 1
        )
    assert [(e.name, dict(e.counts)) for e in run_ledger.events()] == [
        ("tile_dome.consumed_by.facing", {"dome": 0}),
        ("selection.consumed_by.facing", {"selection": 1}),
        ("facing.produced", {"pairs": 0}),
    ]
    with recording() as no_pair_ledger:
        read_facing(_dome(PARTED), _selection({1: "superior_big", 2: "unselected"}), 1)
    assert [(e.name, dict(e.counts)) for e in no_pair_ledger.events()] == [
        ("tile_dome.consumed_by.facing", {"dome": 1}),
        ("selection.consumed_by.facing", {"selection": 1}),
        ("facing.produced", {"pairs": 0}),
    ]


# --- the arrays ----------------------------------------------------------------------------------


def test_the_gap_tiles_are_frozen_and_no_input_is_written() -> None:
    dome = _dome(PARTED)
    selection = _selection(ROLES)
    before = {
        name: np.asarray(getattr(dome, name)).copy()
        for name in ("obstacle", "cleared", "interior", "height", "labels")
    }
    result = read_facing(dome, selection, 1)
    for pair in result.pairs:
        assert pair.gap_tiles.dtype == np.bool_
        assert pair.gap_tiles.shape == (5, 6)
        assert not pair.gap_tiles.flags.writeable
        with pytest.raises(ValueError, match="read-only"):
            pair.gap_tiles[0, 0] = True
    # The inputs were frozen to begin with, so a write would have raised; they are also equal.
    for name, array in before.items():
        np.testing.assert_array_equal(getattr(dome, name), array)
    # A pair with no gap carries a frozen all-False map of the same grid, never None.
    (touching,) = read_facing(_dome(("111", "222")), selection, 1).pairs
    assert touching.gap_tiles.shape == (2, 3)
    assert not touching.gap_tiles.any()
    assert not touching.gap_tiles.flags.writeable


def test_every_code_the_record_and_its_pairs_carry_is_in_the_vocabulary() -> None:
    dome = _dome(("111", "...", "222", "...", "333"))
    for roles in (
        {1: "a", 2: "b", 3: "c"},
        {1: "a", 2: "b", 3: "unselected"},
        {1: "a"},
        {},
    ):
        result = read_facing(dome, _selection(roles), 1)
        assert result.code in FACING_RECORD_CODES
        assert all(pair.code in FACING_CODES for pair in result.pairs)
    absent = read_facing(
        _absent_dome("predecessor_absent"), _selection({}, slice_index=-1), 1
    )
    assert absent.code in FACING_RECORD_CODES


# --- the geometry: the tiles between two territories -------------------------------------------


def test_a_tile_on_the_frame_has_no_neighbour_beyond_it_and_a_corner_is_no_neighbour() -> (
    None
):
    mask = _tiles((3, 3), (2, 0))
    np.testing.assert_array_equal(_beside(mask), _tiles((3, 3), (1, 0), (2, 1)))
    # The input is not written and the result is a new array.
    assert _beside(mask) is not mask
    # Two tiles of the mask touching each other mark each other.
    pair = _tiles((1, 4), (0, 1), (0, 2))
    np.testing.assert_array_equal(
        _beside(pair), _tiles((1, 4), (0, 0), (0, 1), (0, 2), (0, 3))
    )


def test_the_between_region_is_strictly_between_the_two_faces() -> None:
    top = _tiles((5, 3), *[(0, c) for c in range(3)])
    bottom = _tiles((5, 3), *[(4, c) for c in range(3)])
    np.testing.assert_array_equal(
        between_region(top, bottom),
        _tiles((5, 3), *[(r, c) for r in (1, 2, 3) for c in range(3)]),
    )
    # Faces one row apart leave no room between them.
    near = _tiles((5, 3), *[(1, c) for c in range(3)])
    assert not between_region(top, near).any()
    # Faces that overlap along the line leave no room either.
    assert not between_region(top, top).any()


def test_the_between_region_is_the_overlap_of_the_two_widths_ends_included() -> None:
    # Columns 0 to 3 above, columns 2 to 5 below: the overlap is columns 2 and 3 on the row
    # between, and the line between the centres is tilted, so nothing else is between them.
    top = _tiles((5, 6), *[(r, c) for r in (0, 1) for c in range(4)])
    bottom = _tiles((5, 6), *[(r, c) for r in (3, 4) for c in range(2, 6)])
    region = between_region(top, bottom)
    assert region[2, 2] and region[2, 3]
    assert not region[2, 0] and not region[2, 1]
    assert not region[2, 4] and not region[2, 5]


def test_no_region_when_a_territory_is_empty_or_the_two_centres_coincide() -> None:
    ring = np.ones((3, 3), dtype=bool)
    ring[1, 1] = False
    centre = _tiles((3, 3), (1, 1))
    # A ring and the tile it holds share a centre: there is no line, so no between.
    assert not between_region(ring, centre).any()
    nothing = np.zeros((3, 3), dtype=bool)
    assert not between_region(nothing, centre).any()
    assert not between_region(centre, nothing).any()


# --- the arrangement of the saved record --------------------------------------------------------


def _entry(index: int, code: str = "present", pairs: list[dict] | None = None) -> dict:
    """One saved slice as the writer saves it, without its arrays."""
    return {
        "slice_index": index,
        "border": BORDER,
        "code": code,
        "why": "by hand",
        "minimum_sites": 1,
        "pairs": pairs or [],
    }


def _saved_pair(
    first: int,
    second: int,
    code: str = "facing",
    gap_sites: int = 2,
    saddle: float | None = 0.0,
    row: int = 0,
) -> dict:
    return {
        "first": first,
        "second": second,
        "first_role": "superior_big",
        "second_role": "inferior_big",
        "code": code,
        "sites": 0,
        "gap_sites": gap_sites,
        "saddle_mm": saddle,
        "row": row,
    }


def test_the_standing_names_a_drawn_slice_and_every_silence_apart() -> None:
    assert slice_standing("present", 1, 3) == "pairs_drawn"
    assert slice_standing(None, 0, 3) == "facing_not_saved"
    assert slice_standing("predecessor_absent", -1, 0) == "facing_absent"
    assert slice_standing("no_pair", 1, 3) == "no_pair"
    assert slice_standing("present", 3, 3) == "slice_outside_stack"
    assert slice_standing("present", -1, 3) == "slice_outside_stack"
    assert slice_standing("present", 0, 0) == "slice_outside_stack"
    assert slice_standing("lesion", 0, 3) == "facing_code_unknown"


def test_the_standing_is_total_and_drawn_only_for_a_pair_inside_the_stack() -> None:
    # MUST NOT: draw a slice from a code the stage does not say, from either silence, or from
    # an index that is not a whole number inside the stack.
    for code in (*FACING_RECORD_CODES, None, "", 1, True, b"present", ("present",)):
        for index in (0, 1, 2, 3, -1, True, 1.0, None, "1"):
            standing = slice_standing(code, index, 3)
            assert standing in SLICE_STANDINGS, (code, index)
            if standing == "pairs_drawn":
                assert code == "present"
                assert type(index) is int and 0 <= index < 3
    reached = {
        slice_standing(code, index, 3)
        for code in (*FACING_RECORD_CODES, None, "x")
        for index in (0, 3)
    }
    assert reached == set(SLICE_STANDINGS)


def test_the_adapter_hands_each_pair_its_own_row_of_the_saved_gap_tiles() -> None:
    # Every input is frozen: a write by the adapter would raise.
    first = _tiles((3, 3), (1, 0), (1, 1))
    second = _tiles((3, 3), (1, 2))
    third = _tiles((3, 3), (0, 0))
    gap = handed_on(np.stack([first, second, third]))
    grid = np.arange(9, dtype=np.int32).reshape(3, 3)
    labels = handed_on(np.stack([grid, grid + 1]))
    medians = handed_on(np.arange(5 * 9, dtype=np.float64).reshape(5, 3, 3))
    bounds = handed_on(np.zeros((3, 3, 4), dtype=np.int64))
    entries = [
        _entry(
            4,
            pairs=[
                _saved_pair(1, 2, gap_sites=2, row=0),
                _saved_pair(1, 3, "touching_no_gap", 1, None, row=1),
            ],
        ),
        _entry(1, pairs=[_saved_pair(1, 2, gap_sites=1, row=2)]),
    ]
    frame = facing_panels(
        entries, gap, labels, [None, None], bounds, medians, (), None, None, None
    )
    assert frame.saved
    assert frame.bounds_rc is not None and frame.bounds_rc.dtype == np.int64
    one, other = frame.slices
    assert (one.index, one.standing, one.code) == (4, "pairs_drawn", "present")
    assert (other.index, other.standing) == (1, "pairs_drawn")
    assert one.minimum_sites == 1
    assert [
        (p.first, p.second, p.code, p.gap_sites, p.saddle_mm) for p in one.pairs
    ] == [(1, 2, "facing", 2, 0.0), (1, 3, "touching_no_gap", 1, None)]
    # Each pair got the row its record names, over every slice's pairs in order.
    np.testing.assert_array_equal(one.pairs[0].gap_tiles, first)
    np.testing.assert_array_equal(one.pairs[1].gap_tiles, second)
    np.testing.assert_array_equal(other.pairs[0].gap_tiles, third)
    assert all(p.gap_tiles.dtype == np.bool_ for p in (*one.pairs, *other.pairs))
    # Each slice got its own grid of territories and its own slice of the medians.
    assert one.labels is not None and one.labels.dtype == np.int32
    np.testing.assert_array_equal(one.labels, grid)
    np.testing.assert_array_equal(other.labels, grid + 1)
    np.testing.assert_array_equal(one.median, medians[4])
    np.testing.assert_array_equal(other.median, medians[1])
    assert one.plane is None and one.plane_source == "none"


def test_the_adapter_names_a_slice_the_stack_does_not_hold_and_hands_on_no_pair() -> (
    None
):
    gap = handed_on(np.zeros((1, 3, 3), dtype=bool))
    medians = handed_on(np.zeros((5, 3, 3)))
    entries = [
        _entry(9, pairs=[_saved_pair(1, 2, gap_sites=0, saddle=None)]),
        _entry(-1, pairs=[_saved_pair(1, 2, gap_sites=0, saddle=None)]),
    ]
    frame = facing_panels(
        entries, gap, None, [None, None], None, medians, (), None, None, None
    )
    assert [p.standing for p in frame.slices] == ["slice_outside_stack"] * 2
    assert all(p.pairs == () for p in frame.slices)
    # A slice outside the stack has no medians to lie under it, and none is borrowed.
    assert all(p.median is None for p in frame.slices)


def test_the_adapter_keeps_every_absence_absent() -> None:
    nothing = facing_panels(None, None, None, [], None, None, (), None, None, None)
    assert (nothing.saved, nothing.bounds_rc, nothing.slices) == (False, None, ())
    # A slice with no saved territories and no plane keeps both absent, never an empty array.
    gap = handed_on(np.zeros((1, 3, 3), dtype=bool))
    medians = handed_on(np.zeros((3, 3, 3)))
    entry = _entry(2, pairs=[_saved_pair(1, 2, gap_sites=0, saddle=None)])
    kept = facing_panels(
        [entry], gap, None, [None], None, medians, (), None, None, None
    )
    (panel,) = kept.slices
    assert panel.labels is None and panel.plane is None
    assert panel.pairs[0].saddle_mm is None
    assert kept.bounds_rc is None


def test_a_silence_is_handed_on_with_no_pairs_even_if_the_record_lists_some() -> None:
    gap = handed_on(np.zeros((1, 3, 3), dtype=bool))
    medians = handed_on(np.zeros((3, 3, 3)))
    entries = [
        _entry(0, "no_pair", pairs=[_saved_pair(1, 2)]),
        _entry(1, "predecessor_absent"),
        _entry(2, "lesion"),
    ]
    frame = facing_panels(
        entries, gap, None, [None] * 3, None, medians, (), None, None, None
    )
    assert [p.standing for p in frame.slices] == [
        "no_pair",
        "facing_absent",
        "facing_code_unknown",
    ]
    assert all(p.pairs == () for p in frame.slices)


def test_the_plane_under_a_slice_is_its_own_then_the_walks_then_the_selected_one() -> (
    None
):
    own, selected = (
        handed_on(np.full((8, 8), value, dtype=np.uint16)) for value in (1, 3)
    )
    walk = handed_on(
        np.stack([np.full((8, 8), value, dtype=np.uint16) for value in (20, 21)])
    )
    none = handed_on(np.zeros((0, 3, 3), dtype=bool))
    entries = [_entry(index, "no_pair") for index in (1, 4, 5, 7)]
    # The walk visits slices 1 and 4, in that order: slice 4 is its second plane, not its fifth.
    frame = facing_panels(
        entries,
        none,
        None,
        [own, None, None, None],
        None,
        None,
        (1, 4),
        walk,
        5,
        selected,
    )
    assert [p.plane_source for p in frame.slices] == ["own", "walk", "acquired", "none"]
    planes = [None if p.plane is None else int(p.plane[0, 0]) for p in frame.slices]
    # Slice 1 is in the walk too, but the plane named for it outranks the walk's.
    assert planes == [1, 21, 3, None]
    assert {p.plane_source for p in frame.slices} <= set(PLANE_SOURCES)
    # A slice that is both walked and the selected one is told by the walk.
    both = facing_panels(
        [_entry(4, "no_pair")],
        none,
        None,
        [None],
        None,
        None,
        (1, 4),
        walk,
        4,
        selected,
    )
    assert both.slices[0].plane_source == "walk"
    assert both.slices[0].plane is not None and int(both.slices[0].plane[0, 0]) == 21


# --- the drawer's reader and the drawer ----------------------------------------------------------

#: The synthetic series in memory: 24 x 24 planes at half a millimetre, a 2 mm tile is 4 px, a
#: 6 x 6 grid; three slices, all walked. Each plane holds its slice's number, so which plane lies
#: under which slice can be told.
TILE_MM = 2.0
TILE_PX = 4
TILES = 6
SLICES = 3
AXIAL = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])

#: Two pictures on that grid: two objects parted by one dark row, and three in a column.
PARTED_SIX = ("111111", "111111", "......", "222222", "222222", "######")
THREE_SIX = ("111111", "......", "333333", "......", "222222", "######")
THREE_ROLES = {1: "superior_big", 2: "inferior_big", 3: "anterior_small"}


def _synthetic_series() -> Series:
    side = TILES * TILE_PX
    volume = np.stack(
        [np.full((side, side), 50 + z, dtype=np.uint16) for z in range(SLICES)]
    )
    positions = np.array([[0.0, 0.0, float(z)] for z in range(SLICES)])
    geometry = SeriesGeometry(
        normal=np.array([0.0, 0.0, 1.0]),
        orientation=np.tile(AXIAL, (SLICES, 1)),
        position=positions,
        spacing=np.full((SLICES, 2), 0.5),
        along_normal=positions[:, 2],
        orientation_spread=0.0,
        origin_spread_mm=0.0,
    )
    indices = walk_indices(SLICES)
    return Series(
        row=SeriesRow("study", "series", "1", "1", "Coronal"),
        directory=Path("/nonexistent/the-funnel/facing"),
        slices=(),
        stack=("stackable",),
        volume=volume,
        geometry=geometry,
        slice_codes=("decoded",) * SLICES,
        walk_indices=indices,
        walk=volume[list(indices)],
    )


@functools.cache
def _stack_parts(tile_mm: float) -> tuple[dict, dict[str, np.ndarray]]:
    """The squint stack as the writer saves it, from the real stage over the synthetic series."""
    return squint_stack_record(read_squint_stack(_synthetic_series(), tile_mm))


def _chosen(
    picture: tuple[str, ...], roles: dict[int, str], index: int
) -> tuple[FacingPairs, TileDome]:
    dome = _dome(picture, slice_index=index)
    return read_facing(dome, _selection(roles, slice_index=index), 1), dome


def _default_chosen() -> tuple[tuple[FacingPairs, ...], tuple[TileDome, ...]]:
    """Three chosen slices as the stage reads them: one pair, three pairs, and no pair at all."""
    parted, parted_dome = _chosen(PARTED_SIX, ROLES, 1)
    three, three_dome = _chosen(THREE_SIX, THREE_ROLES, 2)
    quiet, quiet_dome = _chosen(PARTED_SIX, {1: "superior_big", 2: "unselected"}, 0)
    return (parted, three, quiet), (parted_dome, three_dome, quiet_dome)


def _facing_record(
    facings: tuple[FacingPairs, ...],
    domes: tuple[TileDome, ...],
    planes: tuple[np.ndarray | None, ...],
    *,
    territories: bool = True,
) -> tuple[dict, dict[str, np.ndarray]]:
    """The facing pairs as the writer saves them: the series' record and the arrays beside it.

    One entry per chosen slice, in the order the route read them, each with its code, reason, bar
    and pairs, every pair carrying the `row` of its gap tiles. The arrays, named
    `<unit>_<field>` as every record's are and stacked as the tile dome's are: `facing_gap_tiles`
    (one row per pair over every slice, slice by slice, in pair order, on the record's grid; no
    rows when the stage examined no pair) and, optionally, `facing_labels` (one grid per slice:
    the dome's territories the pairs name). A slice's stored plane, where the writer saved one, is
    named by that slice's `plane`. A saddle the stage did not read is NaN there and None here.
    """
    rows, columns = (
        (int(size) for size in np.asarray(domes[0].labels).shape) if domes else (0, 0)
    )
    slices: list[dict] = []
    arrays: dict[str, np.ndarray] = {}
    gap_rows: list[np.ndarray] = []
    for number, (facing, plane) in enumerate(zip(facings, planes, strict=True)):
        pairs = []
        for pair in facing.pairs:
            pairs.append(
                {
                    "first": pair.first,
                    "second": pair.second,
                    "first_role": pair.first_role,
                    "second_role": pair.second_role,
                    "code": pair.code,
                    "sites": pair.sites,
                    "gap_sites": pair.gap_sites,
                    "saddle_mm": None if np.isnan(pair.saddle_mm) else pair.saddle_mm,
                    "row": len(gap_rows),
                }
            )
            gap_rows.append(pair.gap_tiles)
        entry = {
            "slice_index": facing.slice_index,
            "border": facing.border,
            "code": facing.code,
            "why": facing.why,
            "minimum_sites": facing.minimum_sites,
            "plane": None,
            "pairs": pairs,
        }
        if plane is not None:
            entry["plane"] = f"facing_plane_{number}"
            arrays[f"facing_plane_{number}"] = plane
        slices.append(entry)
    arrays["facing_gap_tiles"] = (
        np.stack(gap_rows) if gap_rows else np.zeros((0, rows, columns), dtype=bool)
    )
    names: dict[str, str | None] = {"gap_tiles": "facing_gap_tiles", "labels": None}
    if territories and rows * columns and domes:
        arrays["facing_labels"] = np.stack([np.asarray(d.labels) for d in domes])
        names["labels"] = "facing_labels"
    record = {
        "record_code_names": list(FACING_RECORD_CODES),
        "pair_code_names": list(FACING_CODES),
        "axes": (
            "slices in the order the route read them; gap_tiles (N, TR, TC) bool, one row per "
            "pair over every slice in pair order, tile rows then tile columns on the squint "
            "stack's grid; labels (S, TR, TC) int32, the dome's territories, one grid per slice"
        ),
        "tiles_rc": [rows, columns],
        "slices": slices,
        "arrays": names,
    }
    return record, arrays


def _saved_record(
    tmp_path: Path,
    *,
    chosen: tuple[tuple[FacingPairs, ...], tuple[TileDome, ...]] | None = None,
    planes: tuple[np.ndarray | None, ...] | None = None,
    with_facing: bool = True,
    with_walk: bool = True,
    with_stack: bool = True,
    stack_tile_mm: float = TILE_MM,
    territories: bool = True,
    acquired: bool = False,
) -> dict:
    """One series record shaped as the writer saves it, with its arrays on disk."""
    series = _synthetic_series()
    assert series.volume is not None
    facings, domes = chosen if chosen is not None else _default_chosen()
    if planes is None:
        # Only the first chosen slice has a plane of its own; the rest are told by the walk.
        planes = (series.volume[1] + 100, *([None] * (len(facings) - 1)))
    saved: dict[str, np.ndarray] = {}
    entry: dict = {
        "study_uid": "study",
        "series_uid": "series",
        "view": ["Coronal", "1", "1"],
        "code": "measured",
        "slice_index": 1,
        "source_plane": "slice-1.dcm",
        "artifact": "series.npz",
        "study": {
            "slice_codes": ["decoded"] * SLICES,
            "walk_indices": list(series.walk_indices) if with_walk else [],
            "walk_array": "study_walk" if with_walk else None,
        },
    }
    if with_walk:
        assert series.walk is not None
        saved["study_walk"] = series.walk
    if acquired:
        saved["acquired_plane"] = series.volume[1] + 7
    if with_stack:
        stack_record, stack_arrays = _stack_parts(stack_tile_mm)
        saved.update(stack_arrays)
        entry["squint_stack"] = copy.deepcopy(stack_record)
    if with_facing:
        facing_record, facing_arrays = _facing_record(
            facings, domes, planes, territories=territories
        )
        saved.update(facing_arrays)
        entry["facing"] = facing_record
    np.savez_compressed(tmp_path / "series.npz", allow_pickle=False, **saved)
    entry["arrays"] = json.loads(json.dumps(array_table(saved), allow_nan=False))
    return json.loads(json.dumps(entry, allow_nan=False))


def _saved_array(tmp_path: Path, record: dict, name: str) -> np.ndarray:
    with np.load(tmp_path / record["artifact"], allow_pickle=False) as saved:
        return saved[name]


def _resave(tmp_path: Path, record: dict, name: str, array: np.ndarray) -> None:
    """Replace one saved array and its descriptor, as if the writer had saved this instead."""
    path = tmp_path / record["artifact"]
    with np.load(path, allow_pickle=False) as saved:
        arrays = {key: saved[key] for key in saved.files}
    arrays[name] = array
    np.savez_compressed(path, allow_pickle=False, **arrays)
    descriptor = json.loads(json.dumps(array_table({name: array}), allow_nan=False))
    record["arrays"][name] = descriptor[name]


def _slice_of(record: dict, number: int = 0) -> dict:
    return record["facing"]["slices"][number]


def test_the_facing_record_is_plain_data_that_round_trips_the_receipts_json(
    tmp_path: Path,
) -> None:
    record = _saved_record(tmp_path)
    saved = record["facing"]
    assert json.loads(json.dumps(saved, allow_nan=False)) == saved
    assert saved["record_code_names"] == list(FACING_RECORD_CODES)
    assert saved["pair_code_names"] == list(FACING_CODES)
    assert saved["tiles_rc"] == [TILES, TILES]
    assert saved["arrays"] == {
        "gap_tiles": "facing_gap_tiles",
        "labels": "facing_labels",
    }
    assert [entry["slice_index"] for entry in saved["slices"]] == [1, 2, 0]
    assert [entry["code"] for entry in saved["slices"]] == [
        "present",
        "present",
        "no_pair",
    ]
    # Every pair names its row of the stacked gap tiles, over all the slices in order.
    assert [[pair["row"] for pair in entry["pairs"]] for entry in saved["slices"]] == [
        [0],
        [1, 2, 3],
        [],
    ]
    # A saddle the stage did not read is saved as None, never as a number.
    assert [p["saddle_mm"] for p in _slice_of(record, 1)["pairs"]] == [None, 0.0, 0.0]
    assert _slice_of(record, 0)["plane"] == "facing_plane_0"
    assert _slice_of(record, 1)["plane"] is None
    assert record["arrays"]["facing_gap_tiles"]["shape"] == [4, TILES, TILES]
    assert record["arrays"]["facing_labels"]["shape"] == [3, TILES, TILES]


def test_the_reader_reconstitutes_a_writer_shaped_record(tmp_path: Path) -> None:
    record = _saved_record(tmp_path)
    facings, domes = _default_chosen()
    artifact, frame = facing_frames.saved_facing(tmp_path, record)
    assert artifact == tmp_path / "series.npz"
    assert frame.saved
    assert frame.bounds_rc is not None and frame.bounds_rc.shape == (TILES, TILES, 4)
    assert [p.index for p in frame.slices] == [1, 2, 0]
    assert [p.standing for p in frame.slices] == [
        "pairs_drawn",
        "pairs_drawn",
        "no_pair",
    ]
    assert [len(p.pairs) for p in frame.slices] == [1, 3, 0]
    # Every pair arrives with the stage's own values and its own gap tiles.
    for panel, facing in zip(frame.slices, facings, strict=True):
        for saved_pair, pair in zip(panel.pairs, facing.pairs, strict=True):
            assert (saved_pair.first, saved_pair.second) == (pair.first, pair.second)
            assert saved_pair.code == pair.code
            assert (saved_pair.sites, saved_pair.gap_sites) == (
                pair.sites,
                pair.gap_sites,
            )
            np.testing.assert_array_equal(saved_pair.gap_tiles, pair.gap_tiles)
            expected = None if np.isnan(pair.saddle_mm) else pair.saddle_mm
            assert saved_pair.saddle_mm == expected
    for panel, dome in zip(frame.slices, domes, strict=True):
        assert panel.labels is not None
        np.testing.assert_array_equal(panel.labels, dome.labels)
    # The plane under each slice: the record's own, then the walk's, as the adapter chooses; and
    # the stack's tile medians at each slice, whatever the plane.
    assert [p.plane_source for p in frame.slices] == ["own", "walk", "walk"]
    series = _synthetic_series()
    assert series.volume is not None
    own, walked_two, walked_zero = (p.plane for p in frame.slices)
    np.testing.assert_array_equal(own, series.volume[1] + 100)
    np.testing.assert_array_equal(walked_two, series.volume[2])
    np.testing.assert_array_equal(walked_zero, series.volume[0])
    stack_median = _stack_parts(TILE_MM)[1]["squint_stack_median"]
    for panel in frame.slices:
        np.testing.assert_array_equal(panel.median, stack_median[panel.index])


def test_the_reader_says_when_no_facing_was_saved(tmp_path: Path) -> None:
    record = _saved_record(tmp_path, with_facing=False)
    _, frame = facing_frames.saved_facing(tmp_path, record)
    assert not frame.saved
    assert frame.slices == ()
    # A record saved with no chosen slice at all is a different thing: saved, and empty.
    empty = _saved_record(tmp_path, chosen=((), ()), planes=())
    _, none_chosen = facing_frames.saved_facing(tmp_path, empty)
    assert none_chosen.saved and none_chosen.slices == ()


def test_the_reader_falls_back_to_the_selected_plane_where_that_is_the_slice(
    tmp_path: Path,
) -> None:
    chosen = _chosen(PARTED_SIX, ROLES, 1)
    record = _saved_record(
        tmp_path,
        chosen=((chosen[0],), (chosen[1],)),
        planes=(None,),
        with_walk=False,
        acquired=True,
    )
    _, frame = facing_frames.saved_facing(tmp_path, record)
    (panel,) = frame.slices
    assert panel.plane_source == "acquired"
    series = _synthetic_series()
    assert series.volume is not None
    np.testing.assert_array_equal(panel.plane, series.volume[1] + 7)
    # Another slice is not the selected one: no plane is borrowed, and the medians lie under it.
    other = _chosen(PARTED_SIX, ROLES, 2)
    alone = _saved_record(
        tmp_path,
        chosen=((other[0],), (other[1],)),
        planes=(None,),
        with_walk=False,
        acquired=True,
    )
    _, frame = facing_frames.saved_facing(tmp_path, alone)
    assert frame.slices[0].plane is None and frame.slices[0].plane_source == "none"
    assert frame.slices[0].median is not None


def test_a_slice_with_no_dome_needs_no_stack(tmp_path: Path) -> None:
    absent = read_facing(
        _absent_dome("predecessor_absent"), _selection({}, slice_index=-1), 1
    )
    record = _saved_record(
        tmp_path,
        chosen=((absent,), (_absent_dome("predecessor_absent"),)),
        planes=(None,),
        with_stack=False,
    )
    _, frame = facing_frames.saved_facing(tmp_path, record)
    (panel,) = frame.slices
    assert panel.standing == "facing_absent" and panel.index == -1
    assert panel.labels is None and panel.median is None and frame.bounds_rc is None
    assert record["facing"]["tiles_rc"] == [0, 0]


def test_a_slice_the_stack_does_not_hold_is_named_and_hands_on_no_pair(
    tmp_path: Path,
) -> None:
    far = _chosen(PARTED_SIX, ROLES, 7)
    record = _saved_record(tmp_path, chosen=((far[0],), (far[1],)), planes=(None,))
    _, frame = facing_frames.saved_facing(tmp_path, record)
    (panel,) = frame.slices
    assert (panel.index, panel.standing) == (7, "slice_outside_stack")
    assert panel.pairs == () and panel.median is None


def _change_record(key: str, value: object) -> Callable[[dict, Path], None]:
    def change(record: dict, tmp_path: Path) -> None:
        record["facing"][key] = value

    return change


def _change_slice(number: int, key: str, value: object) -> Callable[[dict, Path], None]:
    def change(record: dict, tmp_path: Path) -> None:
        _slice_of(record, number)[key] = value

    return change


def _change_pair(
    number: int, key: str, value: object, pair: int = 0
) -> Callable[[dict, Path], None]:
    def change(record: dict, tmp_path: Path) -> None:
        _slice_of(record, number)["pairs"][pair][key] = value

    return change


def _change_names(key: str, value: object) -> Callable[[dict, Path], None]:
    def change(record: dict, tmp_path: Path) -> None:
        record["facing"]["arrays"][key] = value

    return change


def _drop_a_pair(record: dict, tmp_path: Path) -> None:
    del _slice_of(record, 1)["pairs"][2]


def _list_pairs_on_a_silence(record: dict, tmp_path: Path) -> None:
    _slice_of(record, 2)["pairs"] = copy.deepcopy(_slice_of(record, 0)["pairs"])


def _break_a_digest(record: dict, tmp_path: Path) -> None:
    record["arrays"]["facing_gap_tiles"]["digest"] = "changed"


def _labels_of(tmp_path: Path, record: dict) -> np.ndarray:
    return np.array(_saved_array(tmp_path, record, "facing_labels"))


def _wrong_labels_dtype(record: dict, tmp_path: Path) -> None:
    labels = _labels_of(tmp_path, record).astype(np.int64)
    _resave(tmp_path, record, "facing_labels", labels)


def _wrong_labels_grid(record: dict, tmp_path: Path) -> None:
    _resave(tmp_path, record, "facing_labels", np.zeros((3, 5, 6), dtype=np.int32))


def _labels_for_another_count_of_slices(record: dict, tmp_path: Path) -> None:
    _resave(tmp_path, record, "facing_labels", np.zeros((2, 6, 6), dtype=np.int32))


def _negative_label(record: dict, tmp_path: Path) -> None:
    labels = _labels_of(tmp_path, record)
    labels[0, 5, 5] = -1
    _resave(tmp_path, record, "facing_labels", labels)


def _labels_without_the_pairs(record: dict, tmp_path: Path) -> None:
    _resave(tmp_path, record, "facing_labels", np.zeros((3, 6, 6), dtype=np.int32))


def _territory_under_a_gap_tile(record: dict, tmp_path: Path) -> None:
    labels = _labels_of(tmp_path, record)
    labels[0, 2, 0] = 1
    _resave(tmp_path, record, "facing_labels", labels)


def _plane_that_is_not_a_number(record: dict, tmp_path: Path) -> None:
    _resave(tmp_path, record, "facing_plane_0", np.zeros((24, 24), dtype=bool))


def _plane_of_another_size(record: dict, tmp_path: Path) -> None:
    _resave(tmp_path, record, "facing_plane_0", np.zeros((12, 12), dtype=np.uint16))


def _walk_indices(value: object) -> Callable[[dict, Path], None]:
    def change(record: dict, tmp_path: Path) -> None:
        record["study"]["walk_indices"] = value

    return change


def _drop_the_stack(record: dict, tmp_path: Path) -> None:
    del record["squint_stack"]


REFUSALS: list[tuple[str, Callable[[dict, Path], None], str]] = [
    (
        "not_a_record",
        lambda r, t: r.__setitem__("facing", "yes"),
        "saved_facing_not_a_record",
    ),
    (
        "vocabulary",
        _change_record("record_code_names", ["present"]),
        "saved_facing_vocabulary_mismatch",
    ),
    (
        "pair_vocabulary",
        _change_record("pair_code_names", ["facing"]),
        "saved_facing_vocabulary_mismatch",
    ),
    ("slices_not_a_list", _change_record("slices", {}), "saved_facing_slices_invalid"),
    ("tiles", _change_record("tiles_rc", [6]), "saved_facing_tiles_invalid"),
    ("arrays_missing", _change_record("arrays", "x"), "saved_facing_arrays_missing"),
    (
        "slice_not_a_record",
        lambda r, t: r["facing"]["slices"].__setitem__(0, 5),
        "saved_facing_slice_not_a_record",
    ),
    (
        "slice_index",
        _change_slice(0, "slice_index", "1"),
        "saved_facing_field_invalid:slice_index",
    ),
    ("why", _change_slice(0, "why", 3), "saved_facing_field_invalid:why"),
    ("code", _change_slice(0, "code", "lesion"), "saved_facing_code_unknown:lesion"),
    (
        "bar",
        _change_slice(0, "minimum_sites", -1),
        "saved_facing_field_invalid:minimum_sites",
    ),
    (
        "pairs_not_a_list",
        _change_slice(0, "pairs", "none"),
        "saved_facing_pairs_invalid",
    ),
    (
        "present_without_pairs",
        _change_slice(0, "pairs", []),
        "saved_facing_pairs_disagree_with_the_code",
    ),
    (
        "a_silence_with_pairs",
        _list_pairs_on_a_silence,
        "saved_facing_pairs_disagree_with_the_code",
    ),
    (
        "plane_unnamed",
        _change_slice(0, "plane", 5),
        "saved_facing_array_unnamed:plane",
    ),
    (
        "pair_not_a_record",
        lambda r, t: _slice_of(r)["pairs"].__setitem__(0, 7),
        "saved_facing_pair_not_a_record",
    ),
    (
        "labels_reversed",
        _change_pair(0, "first", 2),
        "saved_facing_pair_labels_invalid",
    ),
    (
        "an_unselected_pair",
        _change_pair(0, "first_role", "unselected"),
        "saved_facing_role_unknown:unselected",
    ),
    (
        "a_role_the_stage_does_not_say",
        _change_pair(0, "second_role", "front_big"),
        "saved_facing_role_unknown:front_big",
    ),
    (
        "pair_code",
        _change_pair(0, "code", "mystery"),
        "saved_facing_pair_code_unknown:mystery",
    ),
    ("sites", _change_pair(0, "sites", -1), "saved_facing_count_invalid:sites"),
    ("row_not_whole", _change_pair(0, "row", -1), "saved_facing_count_invalid:row"),
    ("saddle", _change_pair(0, "saddle_mm", "deep"), "saved_facing_saddle_invalid"),
    (
        "gap_unnamed",
        _change_names("gap_tiles", None),
        "saved_facing_array_unnamed:gap_tiles",
    ),
    (
        "labels_unnamed",
        _change_names("labels", 5),
        "saved_facing_array_unnamed:labels",
    ),
    (
        "gap_array_missing",
        _change_names("gap_tiles", "nowhere"),
        "missing_saved_array:nowhere",
    ),
    ("digest", _break_a_digest, "saved_array_digest_mismatch"),
    ("gap_count", _change_pair(0, "gap_sites", 7), "saved_facing_gap_sites_mismatch"),
    (
        "a_row_that_is_not_the_pairs_place",
        _change_pair(1, "row", 9, pair=1),
        "saved_facing_row_mismatch",
    ),
    ("rows", _drop_a_pair, "saved_facing_rows_mismatch"),
    (
        "grid",
        _change_record("tiles_rc", [5, 6]),
        "saved_facing_shape_mismatch:gap_tiles",
    ),
    ("labels_dtype", _wrong_labels_dtype, "saved_facing_representation_invalid:labels"),
    ("labels_grid", _wrong_labels_grid, "saved_facing_shape_mismatch:labels"),
    (
        "labels_for_another_count_of_slices",
        _labels_for_another_count_of_slices,
        "saved_facing_shape_mismatch:labels",
    ),
    ("labels_negative", _negative_label, "saved_facing_labels_invalid"),
    (
        "labels_without_the_pairs",
        _labels_without_the_pairs,
        "saved_facing_label_missing:1",
    ),
    (
        "a_territory_under_a_gap_tile",
        _territory_under_a_gap_tile,
        "saved_facing_gap_on_a_territory",
    ),
    (
        "a_plane_that_is_not_a_number",
        _plane_that_is_not_a_number,
        "saved_array_representation_invalid:facing_plane_0",
    ),
    (
        "a_plane_of_another_size",
        _plane_of_another_size,
        "saved_facing_covers_another_plane",
    ),
    ("walk_indices_not_whole", _walk_indices(["a"]), "saved_walk_indices_invalid"),
    ("walk_indices_do_not_match", _walk_indices([0]), "saved_walk_indices_mismatch"),
    ("without_a_stack", _drop_the_stack, "saved_facing_without_a_stack"),
]


@pytest.mark.parametrize(
    ("name", "break_it", "message"), REFUSALS, ids=[case[0] for case in REFUSALS]
)
def test_the_reader_refuses_a_saved_record_that_disagrees_with_the_writer(
    tmp_path: Path, name: str, break_it: Callable[[dict, Path], None], message: str
) -> None:
    # MUST NOT: draw a tampered array, a vocabulary or a code the stage does not say, a count
    # that is not its row's, territories that are not the pairs', or a record saved without the
    # stack that places its tiles. Each is named and raised.
    record = _saved_record(tmp_path)
    break_it(record, tmp_path)
    with pytest.raises(ValueError, match=message):
        facing_frames.saved_facing(tmp_path, record)


def test_the_reader_refuses_a_stack_whose_grid_is_not_the_records(
    tmp_path: Path,
) -> None:
    other_grid = _saved_record(tmp_path, stack_tile_mm=4.0)
    with pytest.raises(ValueError, match="saved_facing_grid_mismatch"):
        facing_frames.saved_facing(tmp_path, other_grid)


def test_an_out_directory_outside_data_is_an_argument_refusal(tmp_path: Path) -> None:
    record = _saved_record(tmp_path)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    with pytest.raises(ArgumentRefusal, match="private data directory"):
        facing_frames.draw(tmp_path, "study", tmp_path / "out")
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    with pytest.raises(ArgumentRefusal, match="no saved records for this study"):
        facing_frames.draw(tmp_path, "another-study", out)
    assert not out.exists()


def _receipt_and_out(tmp_path: Path, record: dict) -> Path:
    """Save a hand-built record as the run's receipt, and name a fresh output directory under data/."""
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    return PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex


def test_the_drawer_writes_one_sheet_per_series_with_its_manifest(
    tmp_path: Path,
) -> None:
    """The impure edge, end to end: one image per series under data/, bound to the receipt."""
    record = _saved_record(tmp_path)
    out = _receipt_and_out(tmp_path, record)
    try:
        manifest = facing_frames.draw(tmp_path, "study", out)
        assert manifest["images"] == ["01-coronal-fs1-fat1.png"]
        assert manifest["image"] == "01-coronal-fs1-fat1.png"
        assert (out / manifest["image"]).stat().st_size > 2000
        assert (
            json.loads((out / "manifest.json").read_text())["images"]
            == manifest["images"]
        )
        assert manifest["standings"] == list(SLICE_STANDINGS)
        (series,) = manifest["series"]
        assert (
            series["image_sha256"]
            == sha256((out / series["image"]).read_bytes()).hexdigest()
        )
        assert series["series_uid"] == "series"
        assert series["frame_kind"] == "study"
        assert series["facing"]["tiles_rc"] == [TILES, TILES]
        assert series["facing"]["arrays"]["gap_tiles"]["shape"] == [4, TILES, TILES]
        slices = series["slices"]
        assert [s["index"] for s in slices] == [1, 2, 0]
        assert [s["standing"] for s in slices] == [
            "pairs_drawn",
            "pairs_drawn",
            "no_pair",
        ]
        assert [s["drawn"] for s in slices] == ["drawn", "drawn", "no_pair"]
        assert [s["plane_source"] for s in slices] == ["own", "walk", "walk"]
        assert [s["underlay"] for s in slices] == ["plane", "plane", "plane"]
        assert [s["territories"] for s in slices] == [True, True, True]
        assert slices[0]["own_plane"]["dtype"] == "<u2"
        assert slices[1]["own_plane"] is None
        first = slices[0]
        assert first["pairs"] == [
            {
                "first": 1,
                "second": 2,
                "first_role": "superior_big",
                "second_role": "inferior_big",
                "code": "facing",
                "sites": 0,
                "gap_sites": 6,
                "saddle_mm": 0.0,
            }
        ]
        # The three pairs of the middle slice keep their own codes, and the saddle the stage did
        # not read stays None.
        assert [(p["first"], p["second"], p["code"]) for p in slices[1]["pairs"]] == [
            (1, 2, "too_few_sites"),
            (1, 3, "facing"),
            (2, 3, "facing"),
        ]
        assert slices[1]["pairs"][0]["saddle_mm"] is None
        assert slices[2]["pairs"] == []
        assert (
            manifest["legend"]["gap_when_the_pair_faces"]
            == facing_frames.FACING_GAP_COLOUR
        )
        assert (
            sha256(Path(pictures.__file__).read_bytes()).hexdigest()
            == (manifest["picture_module_sha256"]["facing"])
        )
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_the_drawer_names_a_run_whose_writer_saved_no_facing_pairs(
    tmp_path: Path,
) -> None:
    record = _saved_record(tmp_path, with_facing=False)
    out = _receipt_and_out(tmp_path, record)
    try:
        manifest = facing_frames.draw(tmp_path, "study", out)
        (series,) = manifest["series"]
        assert series["facing"] is None
        assert series["slices"] == []
        assert (out / series["image"]).exists()
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_the_drawer_lays_the_pairs_over_the_stacks_medians_when_no_plane_was_stored(
    tmp_path: Path,
) -> None:
    record = _saved_record(
        tmp_path, planes=(None, None, None), with_walk=False, territories=False
    )
    out = _receipt_and_out(tmp_path, record)
    try:
        manifest = facing_frames.draw(tmp_path, "study", out)
        (series,) = manifest["series"]
        slices = series["slices"]
        assert [s["drawn"] for s in slices] == ["medians", "medians", "no_pair"]
        assert [s["plane_source"] for s in slices] == ["none", "none", "none"]
        assert [s["underlay"] for s in slices] == ["medians", "medians", "medians"]
        assert [s["territories"] for s in slices] == [False, False, False]
        assert series["facing"]["arrays"]["labels"] is None
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_the_drawer_writes_each_silence_in_words_and_draws_no_pair(
    tmp_path: Path,
) -> None:
    absent = read_facing(
        _absent_dome("predecessor_absent"), _selection({}, slice_index=-1), 1
    )
    quiet, quiet_dome = _chosen(PARTED_SIX, {1: "superior_big", 2: "unselected"}, 0)
    far = _chosen(PARTED_SIX, ROLES, 7)
    record = _saved_record(
        tmp_path,
        chosen=((quiet, far[0]), (quiet_dome, far[1])),
        planes=(None, None),
    )
    out = _receipt_and_out(tmp_path, record)
    try:
        manifest = facing_frames.draw(tmp_path, "study", out)
        (series,) = manifest["series"]
        assert [s["standing"] for s in series["slices"]] == [
            "no_pair",
            "slice_outside_stack",
        ]
        assert [s["drawn"] for s in series["slices"]] == [
            "no_pair",
            "slice_outside_stack",
        ]
        assert all(s["pairs"] == [] for s in series["slices"])
    finally:
        shutil.rmtree(out, ignore_errors=True)
    only_absent = _saved_record(
        tmp_path,
        chosen=((absent,), (_absent_dome("predecessor_absent"),)),
        planes=(None,),
        with_stack=False,
    )
    out = _receipt_and_out(tmp_path, only_absent)
    try:
        manifest = facing_frames.draw(tmp_path, "study", out)
        (series,) = manifest["series"]
        assert [s["standing"] for s in series["slices"]] == ["facing_absent"]
        assert series["slices"][0]["index"] == -1
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_a_slice_with_nothing_under_it_is_drawn_on_the_tile_grid_alone() -> None:
    # The reader always hands a drawn slice the stack's medians, so these two ways a slice can
    # reach the drawing are tried on the drawing directly: nothing under the tiles, and no bounds
    # to place them by.
    import matplotlib.pyplot as plt

    bounds = handed_on(
        np.array(
            [[[0, 4, 0, 4], [0, 4, 4, 8]], [[4, 8, 0, 4], [4, 8, 4, 8]]], dtype=np.int64
        )
    )
    pair = pictures.PairPanel(
        first=1,
        second=2,
        first_role="superior_big",
        second_role="inferior_big",
        code="facing",
        sites=0,
        gap_sites=2,
        saddle_mm=0.0,
        gap_tiles=_tiles((2, 2), (0, 0), (0, 1)),
    )
    panel = pictures.SlicePanel(
        index=0,
        standing="pairs_drawn",
        code="present",
        why="by hand",
        minimum_sites=1,
        pairs=(pair,),
        labels=None,
        plane=None,
        plane_source="none",
        median=None,
        border=BORDER,
    )
    placed = pictures.FacingPanels(saved=True, bounds_rc=bounds, slices=(panel,))
    unplaced = pictures.FacingPanels(saved=True, bounds_rc=None, slices=(panel,))
    for frame, word in ((placed, "tiles_alone"), (unplaced, "tiles_not_placed")):
        figure, axis = plt.subplots()
        try:
            assert facing_frames.draw_slice(axis, panel, frame) == word
        finally:
            plt.close(figure)
    assert facing_frames.underlay(panel) == "none"


def test_the_picture_module_is_the_adapter_the_drawer_reads() -> None:
    assert facing_frames.pictures is pictures
    assert set(pictures.SLICE_STANDINGS) <= set(facing_frames.STANDING_WORDS)
    assert set(pictures.PLANE_SOURCES) <= set(facing_frames.SOURCE_WORDS)
