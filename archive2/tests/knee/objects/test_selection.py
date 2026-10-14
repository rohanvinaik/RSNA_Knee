"""The selection by structural facts, both signs (the-funnel tasks 5b.1 to 5b.5).

The facts are measurements from a slice's dome labels, the first lens's codes and the stack's tile
centres in the scanner's LPS millimetres (`territory_facts`); the rules are the lead's four pure
decisions, applied per view by the orchestration (`read_selection`), which also sets the
laterality sign from the Coronal witness. Every call under test is made directly. The scenes are
small grids whose facts are worked by hand; the two column orientations the real series have (a
sagittal's columns run posterior; a coronal's run toward the patient's left) are both drawn, so
the rules are shown to follow LPS and not the image's layout.

Also here: the picture adapter (`knee.pictures.selection`) and the drawer's reader and sheet
(`workbench.render.selection_frames`) on a record shaped as the writer will save it. The writer is
the integrator's; `_selection_record` below is the shape it should save, written out so the
drawer is tested end to end now.
"""

from __future__ import annotations

import dataclasses
import json
import re
import shutil
import sys
import uuid
from hashlib import sha256
from pathlib import Path
from typing import cast

import numpy as np
import pytest

from knee.collapse.first_lens import RULE_VERSION, TILE_CODES, FirstLens
from knee.collapse.squint_stack import SquintStack
from knee.objects.laterality import SIGN_CODES
from knee.objects.selection import (
    ANTERIOR_CODES,
    PAIR_CODES,
    ROLE_CODES,
    SELECTION_CODES,
    WITNESS_CODES,
    ObjectRecord,
    Selection,
    SelectionWithSign,
    TerritoryFacts,
    read_selection,
    territory_facts,
)
from knee.objects.tile_dome import TileDome
from knee.pictures import selection as pictures
from knee.pictures.selection import (
    SELECTION_STANDINGS,
    selection_panels,
    slice_standing,
)
from knee.telemetry import recording
from workbench.render import selection_frames
from workbench.render._out import PROJECT, ArgumentRefusal

BACKGROUND = TILE_CODES.index("background")
NOT_BACKGROUND = TILE_CODES.index("not_background")
UNDECIDED = TILE_CODES.index("undecided")
TILE_EMPTY = TILE_CODES.index("tile_empty")

#: The border every hand-built dome is read under (`knee.objects.tile_dome.BORDER_CODES`); the
#: selection carries on the border of the dome it is made from.
BORDER = "dark_on_both"

#: The words the design uses for the parts of the knee. No record, code, field name, `why` or
#: picture file of this unit may carry one (the lead's law: tile, object, territory, superior,
#: inferior, anterior, interstice, span, envelope, index). The list is assembled from fragments, so
#: a scan of the source for these words finds a violation and not this list.
_ANATOMY_FRAGMENTS = (
    ("fem", "ur"),
    ("femor", "al"),
    ("tib", "ia"),
    ("tibi", "al"),
    ("pat", "ella"),
    ("fib", "ula"),
    ("fibu", "lar"),
    ("bo", "ne"),
    ("mar", "row"),
    ("sk", "in"),
    ("cor", "tex"),
    ("cort", "ical"),
    ("menis", "cus"),
    ("menis", "ci"),
    ("liga", "ment"),
    ("cap", "sule"),
)
ANATOMY = re.compile(
    r"\b(" + "|".join("".join(parts) for parts in _ANATOMY_FRAGMENTS) + ")",
    re.IGNORECASE,
)

# --- the scenes ---------------------------------------------------------------------------------

#: A coronal-like slice, 10 rows by 12 columns, rows running inferior and columns toward the
#: patient's left, 8 mm to a tile. Label 1: rows 0-3, columns 2-9 (32 tiles, centre z 60, x 44).
#: Label 2: rows 5-9, columns 2-8 (35 tiles, centre z 16, x 40, superior face z 32). Label 3:
#: rows 7-8, columns 10-11 (4 tiles, centre z 12, x 84). Everything else is an obstacle.
CORONAL = (
    "001111111100",
    "001111111100",
    "001111111100",
    "001111111100",
    "000000000000",
    "002222222000",
    "002222222000",
    "002222222033",
    "002222222033",
    "002222222000",
)

#: A sagittal-like slice, 10 by 12. Label 1: rows 0-4, columns 3-9 (35 tiles, centre z 56,
#: anterior 48 when columns run anterior). Label 2: rows 6-9, columns 2-8 (28 tiles, centre z 12,
#: superior face z 24). Label 3: rows 4-5, columns 10-11 (4 tiles, centre z 36, anterior 84).
SAGITTAL = (
    "000111111100",
    "000111111100",
    "000111111100",
    "000111111100",
    "000111111133",
    "000000000033",
    "002222222000",
    "002222222000",
    "002222222000",
    "002222222000",
)

#: An axial-like slice, 8 by 8, rows running posterior. Label 1: rows 3-6, columns 2-5 (16
#: tiles, anterior -36). Label 2: rows 0-1, columns 3-4 (4 tiles, anterior -4: in front). Label
#: 3: row 7, columns 0-1 (2 tiles, anterior -56: behind).
AXIAL = (
    "00022000",
    "00022000",
    "00000000",
    "00111100",
    "00111100",
    "00111100",
    "00111100",
    "33000000",
)


def _grid(*rows: str) -> np.ndarray:
    return np.array([[int(ch) for ch in row] for row in rows], dtype=np.int32)


def _centres(rows, cols, row_step, col_step, origin) -> np.ndarray:
    """Tile centres in LPS mm: float64 (rows, cols, 3), each tile `step` from its neighbour."""
    r, c = np.indices((rows, cols))
    moved = (
        np.asarray(row_step, dtype=np.float64) * r[..., None]
        + np.asarray(col_step, dtype=np.float64) * c[..., None]
    )
    return (np.asarray(origin, dtype=np.float64) + moved).astype(np.float64)


def _coronal_centres(rows=10, cols=12) -> np.ndarray:
    return _centres(rows, cols, (0, 0, -8), (8, 0, 0), (0, 0, 8 * (rows - 1)))


def _sagittal_centres(rows=10, cols=12, posterior=False) -> np.ndarray:
    # A real sagittal series is never exactly one x: its plane is tilted a little, so x drifts
    # along the columns (about half a millimetre a tile on the saved study). The drift is here so
    # that a rule which wrongly read a left-right offset on this view would give a sign.
    step = (1.5, 8, 0) if posterior else (1.5, -8, 0)
    return _centres(rows, cols, (0, 0, -8), step, (30, 0, 8 * (rows - 1)))


def _axial_centres(rows=8, cols=8) -> np.ndarray:
    return _centres(rows, cols, (0, 8, 0), (8, 0, 0), (0, 0, 100))


def _frozen(array: np.ndarray) -> np.ndarray:
    array.setflags(write=False)
    return array


def _peaks(labels: np.ndarray) -> np.ndarray:
    """The dome's peaks: peak `k` is the first tile in scan order of territory `k + 1`."""
    top = int(labels.max()) if labels.size else 0
    rows = []
    for label in range(1, top + 1):
        found = np.argwhere(labels == label)
        rows.append(found[0] if len(found) else (0, 0))
    return np.array(rows, dtype=np.int64).reshape(-1, 2)


def _dome(labels, obstacle=None, *, code="present", slice_index=0, uid="s") -> TileDome:
    labels = _frozen(np.asarray(labels, dtype=np.int32))
    blocked = (labels == 0) if obstacle is None else np.asarray(obstacle, dtype=bool)
    peaks = _peaks(labels)
    return TileDome(
        series_uid=uid,
        slice_index=slice_index,
        code=code,
        why="a dome",
        prominence_mm=8.0,
        obstacle=_frozen(blocked.copy()),
        cleared=_frozen(np.zeros(labels.shape, dtype=bool)),
        interior=_frozen(~blocked),
        height=_frozen(np.zeros(labels.shape, dtype=np.float64)),
        peaks=_frozen(peaks),
        peak_height_mm=_frozen(np.zeros(len(peaks), dtype=np.float64)),
        labels=labels,
        border=BORDER,
    )


def _lens(
    shape, *, slices=1, fill=NOT_BACKGROUND, code="present", at=None
) -> FirstLens:
    codes = np.full((slices, *shape), fill, dtype=np.uint8)
    for (z, r, c), value in (at or {}).items():
        codes[z, r, c] = value
    return FirstLens(
        series_uid="s",
        code=code,
        why="a lens",
        split=10.0,
        rule_version=RULE_VERSION,
        codes=_frozen(codes),
        counts=(0, 0, 0, 0),
    )


def _stack(centres, *, slices=1, code="present") -> SquintStack:
    rows, cols = centres.shape[:2]
    cube = _frozen(np.zeros((slices, rows, cols), dtype=np.float64))
    return SquintStack(
        series_uid="s",
        code=code,
        why="a stack",
        tile_mm=8.0,
        tile_shape_rc=(4, 4),
        bounds_rc=_frozen(_bounds(rows, cols)),
        median=cube,
        minimum=cube,
        maximum=cube,
        coverage=cube,
        centres_lps=_frozen(np.broadcast_to(centres, (slices, *centres.shape)).copy()),
    )


def _bounds(rows: int, cols: int) -> np.ndarray:
    """Half-open native bounds of tiles four pixels square: (rows, cols, 4) int64."""
    r, c = np.indices((rows, cols))
    return np.stack([4 * r, 4 * r + 4, 4 * c, 4 * c + 4], axis=-1).astype(np.int64)


def _absent_dome(uid="s") -> TileDome:
    empty = np.empty((0, 0))
    return TileDome(
        series_uid=uid,
        slice_index=-1,
        code="predecessor_absent",
        why="no stack",
        prominence_mm=8.0,
        obstacle=empty.astype(bool),
        cleared=empty.astype(bool),
        interior=empty.astype(bool),
        height=empty,
        peaks=np.empty((0, 2), dtype=np.int64),
        peak_height_mm=np.empty(0),
        labels=empty.astype(np.int32),
        border=BORDER,
    )


def _roles(result: SelectionWithSign) -> dict[int, str]:
    return {item.index: item.role_code for item in result.selection.objects}


# --- territory_facts: the measurement, 5b.1 -----------------------------------------------------


def _facts_scene():
    """Two territories on a 6 x 6 grid with label 2 skipped; centres x = 8c, y = 3r, z = 40 - 8r."""
    labels = _grid("000000", "011000", "011030", "000000", "000000", "000000")
    centres = _centres(6, 6, (0, 3, -8), (8, 0, 0), (0, 0, 40))
    obstacle = labels == 0
    obstacle[2, 5] = False  # label 3 has one tile beside it that is not an obstacle
    codes = np.full(labels.shape, NOT_BACKGROUND, dtype=np.uint8)
    codes[0, 1] = BACKGROUND  # a cleared tile above label 1
    return labels, obstacle, codes, centres


def test_each_territory_is_measured_in_lps_millimetres() -> None:
    labels, obstacle, codes, centres = _facts_scene()
    first, third = territory_facts(labels, obstacle, codes, centres)
    assert (first.index, first.tiles) == (1, 4)
    np.testing.assert_allclose(first.centre_lps, (12.0, 4.5, 28.0))
    assert first.superior_mm == pytest.approx(28.0)  # +z, superior
    assert first.anterior_mm == pytest.approx(-4.5)  # -y, anterior
    assert first.left_right_mm == pytest.approx(12.0)  # +x, the patient's left
    assert first.superior_extent_mm == pytest.approx((24.0, 32.0))
    assert first.anterior_face_mm == pytest.approx(
        -3.0
    )  # the most anterior tile centre
    assert (third.index, third.tiles) == (3, 1)
    np.testing.assert_allclose(third.centre_lps, (32.0, 6.0, 24.0))
    assert third.superior_extent_mm == pytest.approx((24.0, 24.0))
    assert third.anterior_face_mm == pytest.approx(-6.0)


def test_a_label_with_no_tile_is_absent_and_the_order_is_label_order() -> None:
    labels, obstacle, codes, centres = _facts_scene()
    facts = territory_facts(labels, obstacle, codes, centres)
    assert [f.index for f in facts] == [1, 3]
    assert (
        territory_facts(np.zeros((6, 6), dtype=np.int32), obstacle, codes, centres)
        == ()
    )
    assert (
        territory_facts(
            np.empty((0, 0), dtype=np.int32),
            np.empty((0, 0), dtype=bool),
            np.empty((0, 0), dtype=np.uint8),
            np.empty((0, 0, 3)),
        )
        == ()
    )


def test_the_facts_are_plain_numbers_and_bools_the_pinned_decisions_can_read() -> None:
    # MUST NOT: hand a decision a numpy scalar. The decisions test `isinstance(x, int)` and
    # `isinstance(ringed, bool)`, and refuse anything else as invalid_measurement, silently.
    labels, obstacle, codes, centres = _facts_scene()
    for fact in territory_facts(labels, obstacle, codes, centres):
        assert type(fact.index) is int and type(fact.tiles) is int
        assert type(fact.ringed) is bool and type(fact.touches_leg_border) is bool
        for number in (
            fact.superior_mm,
            fact.anterior_mm,
            fact.left_right_mm,
            fact.anterior_face_mm,
            *fact.superior_extent_mm,
        ):
            assert type(number) is float
        assert fact.centre_lps.shape == (3,) and fact.centre_lps.dtype == np.float64
        assert not fact.centre_lps.flags.writeable


def test_a_territory_is_ringed_only_when_every_tile_beside_it_is_an_obstacle() -> None:
    labels, obstacle, codes, centres = _facts_scene()
    first, third = territory_facts(labels, obstacle, codes, centres)
    assert first.ringed is True
    assert third.ringed is False  # the tile at (2, 5) beside it is not an obstacle
    # A tile that is not an obstacle opens the ring from any of its four sides ...
    for row, column in ((0, 1), (1, 0), (1, 3), (3, 1)):  # above, left, right, below
        opened = obstacle.copy()
        opened[row, column] = False
        assert territory_facts(labels, opened, codes, centres)[0].ringed is False
    # ... but not from a corner: only the four tiles that share an edge count.
    corner = obstacle.copy()
    corner[0, 0] = False
    assert territory_facts(labels, corner, codes, centres)[0].ringed is True


def test_ringed_counts_tiles_only_so_the_grid_edge_neither_encloses_nor_opens() -> None:
    # The docstring speaks of "every tile four-adjacent to it and outside it", and a position off
    # the grid is no tile. A territory on the frame whose tiles beside it are obstacles is ringed.
    labels = _grid("11000", "11000", "00000")
    centres = _centres(3, 5, (0, 0, -8), (8, 0, 0), (0, 0, 16))
    codes = np.full(labels.shape, NOT_BACKGROUND, dtype=np.uint8)
    (only,) = territory_facts(labels, labels == 0, codes, centres)
    assert only.ringed is True


def test_a_territory_touches_the_leg_border_beside_a_cleared_or_undecided_tile() -> (
    None
):
    labels, obstacle, codes, centres = _facts_scene()
    first, third = territory_facts(labels, obstacle, codes, centres)
    assert first.touches_leg_border is True  # (0, 1) was cleared, above (1, 1)
    assert third.touches_leg_border is False
    buffered = codes.copy()
    buffered[3, 4] = UNDECIDED  # below label 3's tile
    assert territory_facts(labels, obstacle, buffered, centres)[1].touches_leg_border
    # From any of the four sides, cleared or undecided alike; never from a corner.
    plain = np.full(labels.shape, NOT_BACKGROUND, dtype=np.uint8)
    for word in (BACKGROUND, UNDECIDED):
        for row, column in (
            (0, 1),
            (1, 0),
            (1, 3),
            (3, 1),
        ):  # above, left, right, below
            marked = plain.copy()
            marked[row, column] = word
            facts = territory_facts(labels, obstacle, marked, centres)
            assert facts[0].touches_leg_border is True
            assert facts[1].touches_leg_border is False
        corner = plain.copy()
        corner[0, 0] = word
        assert (
            territory_facts(labels, obstacle, corner, centres)[0].touches_leg_border
            is False
        )


def test_an_empty_tile_is_not_the_leg_border_and_a_kept_buffer_inside_a_territory_is() -> (
    None
):
    labels, obstacle, codes, centres = _facts_scene()
    empty = codes.copy()
    empty[3, 4] = TILE_EMPTY
    assert (
        territory_facts(labels, obstacle, empty, centres)[1].touches_leg_border is False
    )
    # The dome keeps the undecided buffer in play, so a territory can hold it: its own tile
    # four-adjacent to another of its tiles is a tile the lens left undecided, beside the tile.
    inside = np.full(labels.shape, NOT_BACKGROUND, dtype=np.uint8)
    inside[1, 2] = UNDECIDED
    first = territory_facts(labels, obstacle, inside, centres)[0]
    assert first.touches_leg_border is True


def test_the_facts_follow_lps_and_not_the_layout_of_the_image() -> None:
    labels, obstacle, codes, _ = _facts_scene()
    # The same grid with the columns running the other way: x falls with the column.
    flipped = _centres(6, 6, (0, 3, -8), (-8, 0, 0), (40, 0, 40))
    first = territory_facts(labels, obstacle, codes, flipped)[0]
    assert first.left_right_mm == pytest.approx(40.0 - 12.0)
    assert first.superior_mm == pytest.approx(28.0)


def test_disagreeing_inputs_are_refused_by_name_and_no_input_is_written() -> None:
    labels, obstacle, codes, centres = _facts_scene()
    shapes = {
        "labels": (labels[:5], obstacle, codes, centres),
        "obstacle": (labels, obstacle[:, :5], codes, centres),
        "codes": (labels, obstacle, codes[:4], centres),
        "centres": (labels, obstacle, codes, centres[:, :, :2]),
        "grid": (labels, obstacle, codes, centres[:5]),
    }
    for arguments in shapes.values():
        with pytest.raises(ValueError, match="selection_inputs_disagree"):
            territory_facts(*arguments)
    # A representation the docstring does not declare is the same disagreement.
    with pytest.raises(ValueError, match="selection_inputs_disagree"):
        territory_facts(labels.astype(np.float64), obstacle, codes, centres)
    with pytest.raises(ValueError, match="selection_inputs_disagree"):
        territory_facts(labels, obstacle.astype(np.uint8), codes, centres)
    with pytest.raises(ValueError, match="selection_inputs_disagree"):
        territory_facts(labels, obstacle, codes, centres.astype(np.int64))
    # Read-only inputs go through untouched: a write anywhere would raise.
    territory_facts(
        _frozen(labels.copy()),
        _frozen(obstacle.copy()),
        _frozen(codes.copy()),
        _frozen(centres.copy()),
    )


# --- read_selection: the orchestration, 5b.2 to 5b.4 ----------------------------------------------


def test_the_coronal_takes_the_big_pair_and_the_witness_and_the_sign_is_its_side() -> (
    None
):
    labels = _grid(*CORONAL)
    dome = _dome(labels)
    first, stack = _lens(labels.shape), _stack(_coronal_centres())
    result = read_selection(dome, first, stack, "Coronal", 8)
    assert isinstance(result, SelectionWithSign)
    selection = result.selection
    assert _roles(result) == {
        1: "superior_big",
        2: "inferior_big",
        3: "lateral_small_ringed",
    }
    assert (selection.code, selection.plane_kind, selection.slice_index) == (
        "present",
        "Coronal",
        0,
    )
    assert selection.pair_code == "selected"
    # Per territory, in label order; the pair itself is not put to the candidate decision.
    assert selection.candidate_codes == ("", "", "lateral_small_ringed")
    # The witness is 44 mm toward the patient's left of the inferior big object: left is lateral.
    assert result.lateral_sign == "left"
    assert [o.tiles for o in selection.objects] == [32, 35, 4]
    assert selection.objects[2].facts.left_right_mm == pytest.approx(84.0)


def test_a_witness_on_the_patients_right_gives_the_other_sign() -> None:
    labels = np.fliplr(_grid(*CORONAL)).copy()
    dome = _dome(labels)
    first, stack = _lens(labels.shape), _stack(_coronal_centres())
    result = read_selection(dome, first, stack, "Coronal", 8)
    assert _roles(result)[3] == "lateral_small_ringed"
    assert result.lateral_sign == "right"
    assert result.selection.objects[2].facts.left_right_mm == pytest.approx(4.0)


def test_a_coronal_with_no_witness_abstains_the_sign_and_names_why() -> None:
    labels = _grid(*CORONAL)
    open_beside = labels == 0
    # A tile above the small territory that is not an obstacle opens its ring.
    open_beside[6, 10] = False
    dome = _dome(labels, open_beside)
    first, stack = _lens(labels.shape), _stack(_coronal_centres())
    result = read_selection(dome, first, stack, "Coronal", 8)
    assert _roles(result)[3] == "unselected"
    assert result.selection.candidate_codes == ("", "", "not_ringed")
    assert result.lateral_sign == "side_abstained"
    # The other two roles stand without the witness.
    assert _roles(result)[1] == "superior_big" and _roles(result)[2] == "inferior_big"


def test_a_coronal_with_nothing_else_has_no_witness_and_no_sign() -> None:
    labels = _grid(*CORONAL)
    labels[labels == 3] = 0
    dome = _dome(labels)
    first, stack = _lens(labels.shape), _stack(_coronal_centres())
    result = read_selection(dome, first, stack, "Coronal", 8)
    assert sorted(_roles(result).values()) == ["inferior_big", "superior_big"]
    assert result.selection.candidate_codes == ("", "")
    assert result.lateral_sign == "side_abstained"


def test_the_sagittal_names_the_small_object_in_front_of_the_superior_big_one() -> None:
    labels = _grid(*SAGITTAL)
    dome = _dome(labels)
    first, stack = _lens(labels.shape), _stack(_sagittal_centres())
    result = read_selection(dome, first, stack, "Sagittal", 8)
    assert _roles(result) == {1: "superior_big", 2: "inferior_big", 3: "anterior_small"}
    assert result.selection.plane_kind == "Sagittal"
    assert result.selection.pair_code == "selected"
    assert result.selection.candidate_codes == ("", "", "anterior_small")
    # Only the Coronal has a witness: the sign is never read from a Sagittal.
    assert result.lateral_sign == "side_abstained"


def test_the_sagittal_rule_follows_lps_when_the_columns_run_posterior() -> None:
    # The real sagittal series run posterior along the columns, so the same arrangement of the
    # knee sits mirrored in the image. The roles must not change.
    labels = np.fliplr(_grid(*SAGITTAL)).copy()
    dome = _dome(labels)
    first = _lens(labels.shape)
    stack = _stack(_sagittal_centres(posterior=True))
    result = read_selection(dome, first, stack, "Sagittal", 8)
    assert _roles(result) == {1: "superior_big", 2: "inferior_big", 3: "anterior_small"}
    # The columns run posterior from y = 0: the flipped small territory's centre is at y = 4
    # (anterior_mm -4) and the big one's at y = 40 (anterior_mm -40), so the small one is the
    # more anterior, as before.
    assert result.selection.objects[2].facts.anterior_mm == pytest.approx(-4.0)
    assert result.selection.objects[0].facts.anterior_mm == pytest.approx(-40.0)


def test_a_territory_behind_the_superior_big_one_is_not_the_small_object_in_front() -> (
    None
):
    labels = _grid(*SAGITTAL)
    behind = labels.copy()
    behind[labels == 3] = 0
    behind[4:6, 0:2] = 3  # the same small territory, behind the big one instead
    dome = _dome(behind)
    first, stack = _lens(labels.shape), _stack(_sagittal_centres())
    result = read_selection(dome, first, stack, "Sagittal", 8)
    assert _roles(result)[3] == "unselected"
    assert result.selection.candidate_codes == ("", "", "not_anterior")


def test_a_small_territory_far_from_the_end_is_named_so_and_not_selected() -> None:
    labels = _grid(*SAGITTAL)
    high = labels.copy()
    high[labels == 3] = 0
    high[0:2, 10:12] = 3  # in front, but higher than the superior big object's centre
    dome = _dome(high)
    first, stack = _lens(labels.shape), _stack(_sagittal_centres())
    result = read_selection(dome, first, stack, "Sagittal", 8)
    assert _roles(result)[3] == "unselected"
    assert result.selection.candidate_codes == ("", "", "not_near_the_end")


def test_a_territory_in_front_but_lower_than_the_inferior_objects_face_is_not_near_the_end() -> (
    None
):
    # The bar is the inferior big object's SUPERIOR face (its highest tile centre, z 24), not its
    # lowest: a small territory in front whose centre is at z 4 lies inside that object's own
    # range of heights, below its face, and is not the small object at the end of the big one.
    labels = _grid(*SAGITTAL)
    low = labels.copy()
    low[labels == 3] = 0
    low[8:10, 10:12] = 3
    dome = _dome(low)
    first, stack = _lens(labels.shape), _stack(_sagittal_centres())
    result = read_selection(dome, first, stack, "Sagittal", 8)
    assert _roles(result)[3] == "unselected"
    assert result.selection.candidate_codes == ("", "", "not_near_the_end")


def test_a_third_territory_as_large_as_the_big_one_is_not_small_on_either_view() -> (
    None
):
    # Three territories of 20 tiles: the pair is the two most superior (a tie, said), and the
    # third, the lowest and the one in front, is as large as the object it is measured against.
    # `not_small` answers before any other test of the candidate does.
    labels = np.zeros((12, 14), dtype=np.int32)
    labels[0:4, 2:7] = 1
    labels[4:8, 2:7] = 2
    labels[8:12, 8:13] = 3
    first = _lens(labels.shape)
    sagittal = read_selection(
        _dome(labels), first, _stack(_sagittal_centres(12, 14)), "Sagittal", 8
    )
    assert sagittal.selection.pair_code == "tie"
    assert _roles(sagittal) == {1: "superior_big", 2: "inferior_big", 3: "unselected"}
    assert sagittal.selection.candidate_codes == ("", "", "not_small")
    coronal = read_selection(
        _dome(labels), first, _stack(_coronal_centres(12, 14)), "Coronal", 8
    )
    assert _roles(coronal) == {1: "superior_big", 2: "inferior_big", 3: "unselected"}
    assert coronal.selection.candidate_codes == ("", "", "not_small")
    assert coronal.lateral_sign == "side_abstained"


def test_equally_large_candidates_go_to_the_lower_label_and_the_selection_says_so() -> (
    None
):
    labels = np.zeros((10, 14), dtype=np.int32)
    labels[0:5, 3:10] = 1
    labels[6:10, 2:9] = 2
    labels[4:6, 10:12] = 3
    labels[4:6, 12:14] = 4
    dome = _dome(labels)
    first = _lens(labels.shape)
    stack = _stack(_sagittal_centres(10, 14))
    result = read_selection(dome, first, stack, "Sagittal", 8)
    assert _roles(result) == {
        1: "superior_big",
        2: "inferior_big",
        3: "anterior_small",
        4: "unselected",
    }
    # Both answered with the word; only one holds the role.
    assert result.selection.candidate_codes == (
        "",
        "",
        "anterior_small",
        "anterior_small",
    )
    assert "equally large" in result.selection.why


def test_the_axial_takes_the_central_object_and_the_one_in_front_and_never_a_big_pair() -> (
    None
):
    labels = _grid(*AXIAL)
    dome = _dome(labels)
    first, stack = _lens(labels.shape), _stack(_axial_centres())
    result = read_selection(dome, first, stack, "Axial", 2)
    assert _roles(result) == {1: "central_big", 2: "anterior_small", 3: "unselected"}
    assert "superior_big" not in _roles(result).values()
    assert "inferior_big" not in _roles(result).values()
    assert result.selection.plane_kind == "Axial"
    assert result.selection.pair_code == "selected"
    # The Axial has its own rule and no candidate decision: nothing is carried between views.
    assert result.selection.candidate_codes == ()
    assert result.lateral_sign == "side_abstained"


def test_the_axial_names_the_central_object_alone_when_nothing_lies_in_front() -> None:
    labels = _grid(*AXIAL)
    labels[labels == 2] = 0
    dome = _dome(labels)
    first, stack = _lens(labels.shape), _stack(_axial_centres())
    result = read_selection(dome, first, stack, "Axial", 2)
    assert _roles(result) == {1: "central_big", 3: "unselected"}
    assert result.selection.pair_code == "one_big_only"


def test_the_axial_with_no_candidate_at_the_bar_selects_nothing() -> None:
    labels = _grid(*AXIAL)
    dome = _dome(labels)
    first, stack = _lens(labels.shape), _stack(_axial_centres())
    result = read_selection(dome, first, stack, "Axial", 100)
    assert result.selection.pair_code == "none"
    assert set(_roles(result).values()) == {"unselected"}
    assert len(result.selection.objects) == 3
    assert result.selection.candidate_codes == ()


def test_one_big_territory_is_named_and_takes_no_big_role() -> None:
    # A lone large territory is not known to be the superior or the inferior one, so it keeps no
    # big role; the pair word says why. The other roles need the pair and so are not read.
    labels = _grid(*CORONAL)
    dome = _dome(labels)
    first, stack = _lens(labels.shape), _stack(_coronal_centres())
    result = read_selection(dome, first, stack, "Coronal", 34)
    assert result.selection.pair_code == "one_big_only"
    assert set(_roles(result).values()) == {"unselected"}
    assert result.selection.candidate_codes == ("", "", "")
    assert result.lateral_sign == "side_abstained"


def test_no_candidate_at_the_bar_selects_nothing() -> None:
    labels = _grid(*CORONAL)
    dome = _dome(labels)
    first, stack = _lens(labels.shape), _stack(_coronal_centres())
    result = read_selection(dome, first, stack, "Coronal", 100)
    assert result.selection.pair_code == "none"
    assert set(_roles(result).values()) == {"unselected"}
    # Every territory is kept, selected or not.
    assert len(result.selection.objects) == 3


def test_a_tie_in_size_is_broken_by_superior_position_and_said() -> None:
    labels = np.zeros((10, 12), dtype=np.int32)
    labels[0:4, 2:10] = 1  # 32 tiles, higher
    labels[5:9, 2:10] = 2  # 32 tiles, lower
    dome = _dome(labels)
    first, stack = _lens(labels.shape), _stack(_coronal_centres())
    result = read_selection(dome, first, stack, "Coronal", 8)
    assert result.selection.pair_code == "tie"
    assert _roles(result) == {1: "superior_big", 2: "inferior_big"}


def test_a_skipped_label_does_not_move_a_role_to_the_wrong_territory() -> None:
    # Labels 1 and 3, with 2 skipped: the pair rule names positions in the facts, and a role
    # must land on the label at that position, not on the label with that number.
    labels = _grid(*CORONAL)
    labels[7:9, 10:12] = 0  # the small territory goes
    labels[labels == 2] = 3  # the lower big one is label 3, and label 2 is skipped
    dome = _dome(labels)
    first, stack = _lens(labels.shape), _stack(_coronal_centres())
    result = read_selection(dome, first, stack, "Coronal", 8)
    assert [o.index for o in result.selection.objects] == [1, 3]
    assert _roles(result) == {1: "superior_big", 3: "inferior_big"}


def test_the_records_hold_the_territory_as_the_stage_defines_it() -> None:
    labels = _grid(*CORONAL)
    dome = _dome(labels, slice_index=3)
    first, stack = _lens(labels.shape, slices=5), _stack(_coronal_centres(), slices=5)
    result = read_selection(dome, first, stack, "Coronal", 8)
    selection = result.selection
    assert selection.slice_index == 3 and selection.series_uid == "s"
    for item in selection.objects:
        assert isinstance(item, ObjectRecord) and isinstance(item.facts, TerritoryFacts)
        assert item.tiles == item.facts.tiles and item.index == item.facts.index
        assert item.role_code in ROLE_CODES
    assert selection.code in SELECTION_CODES and selection.pair_code in PAIR_CODES
    assert result.lateral_sign in SIGN_CODES
    assert all(
        word in ("", *ANTERIOR_CODES, *WITNESS_CODES)
        for word in selection.candidate_codes
    )
    # The facts were read at the dome's slice, not at slice 0.
    assert selection.objects[0].facts.tiles == 32


def test_the_slice_is_read_from_the_stack_and_the_lens_at_the_domes_index() -> None:
    labels = _grid(*CORONAL)
    codes = _lens(labels.shape, slices=2, at={(1, 0, 2): BACKGROUND})
    # Slice 1's lens cleared the tile at row 0, column 2, beside label 1's tile at column 3;
    # slice 0's lens cleared nothing.
    stack = _stack(_coronal_centres(), slices=2)
    zero = read_selection(_dome(labels, slice_index=0), codes, stack, "Coronal", 8)
    one = read_selection(_dome(labels, slice_index=1), codes, stack, "Coronal", 8)
    assert zero.selection.objects[0].facts.touches_leg_border is False
    assert one.selection.objects[0].facts.touches_leg_border is True


def test_a_dome_that_is_not_present_gives_predecessor_absent_and_no_objects() -> None:
    first, stack = (
        _lens((0, 0), slices=0, code="predecessor_absent"),
        _stack(np.empty((0, 0, 3)), slices=0, code="no_stacked_volume"),
    )
    for plane in ("Coronal", "Sagittal", "Axial"):
        result = read_selection(_absent_dome(), first, stack, plane, 8)
        selection = result.selection
        assert selection.code == "predecessor_absent"
        assert selection.objects == () and selection.candidate_codes == ()
        assert selection.slice_index == -1 and selection.plane_kind == plane
        assert selection.pair_code == "none"
        assert result.lateral_sign == "side_abstained"


def test_a_dome_with_no_interior_is_not_present_and_says_which_dome_it_was() -> None:
    labels = np.zeros((10, 12), dtype=np.int32)
    dome = _dome(labels, code="no_interior", slice_index=2)
    first, stack = _lens(labels.shape, slices=3), _stack(_coronal_centres(), slices=3)
    result = read_selection(dome, first, stack, "Coronal", 8)
    assert result.selection.code == "predecessor_absent"
    assert "no_interior" in result.selection.why
    assert result.selection.slice_index == 2


def test_a_present_dome_with_no_territory_is_named_so() -> None:
    labels = np.zeros((10, 12), dtype=np.int32)
    dome = _dome(labels, code="present")
    first, stack = _lens(labels.shape), _stack(_coronal_centres())
    result = read_selection(dome, first, stack, "Coronal", 8)
    assert result.selection.code == "no_territory"
    assert result.selection.objects == ()
    assert result.selection.pair_code == "none"


def test_the_consumption_and_the_production_are_recorded_in_order() -> None:
    labels = _grid(*CORONAL)
    dome = _dome(labels)
    first, stack = _lens(labels.shape), _stack(_coronal_centres())
    with recording() as run_ledger:
        read_selection(dome, first, stack, "Coronal", 8)
    events = run_ledger.events()
    assert [e.name for e in events] == [
        "tile_dome.consumed_by.selection",
        "first_lens.consumed_by.selection",
        "squint_stack.consumed_by.selection",
        "selection.produced",
    ]
    assert [dict(e.counts) for e in events] == [
        {"dome": 1},
        {"lens": 1},
        {"stack": 1},
        {"objects": 3},
    ]


def test_an_absent_predecessor_is_recorded_as_a_zero_not_skipped() -> None:
    first = _lens((0, 0), slices=0, code="predecessor_absent")
    stack = _stack(np.empty((0, 0, 3)), slices=0, code="geometry_unreadable")
    with recording() as run_ledger:
        read_selection(_absent_dome(), first, stack, "Axial", 8)
    assert [(e.name, dict(e.counts)) for e in run_ledger.events()] == [
        ("tile_dome.consumed_by.selection", {"dome": 0}),
        ("first_lens.consumed_by.selection", {"lens": 0}),
        ("squint_stack.consumed_by.selection", {"stack": 0}),
        ("selection.produced", {"objects": 0}),
    ]


def test_produced_counts_only_the_territories_that_took_a_role() -> None:
    labels = _grid(*AXIAL)
    dome = _dome(labels)
    first, stack = _lens(labels.shape), _stack(_axial_centres())
    with recording() as run_ledger:
        read_selection(dome, first, stack, "Axial", 2)
    (produced,) = [e for e in run_ledger.events() if e.name == "selection.produced"]
    assert dict(produced.counts) == {"objects": 2}  # three territories, two with a role


def test_a_plane_kind_the_selection_does_not_know_is_refused_before_any_event() -> None:
    labels = _grid(*CORONAL)
    dome = _dome(labels)
    first, stack = _lens(labels.shape), _stack(_coronal_centres())
    for kind in ("Oblique", "coronal", "", None, 3, ["Coronal"]):
        with (
            recording() as run_ledger,
            pytest.raises(ValueError, match="invalid_plane_kind"),
        ):
            read_selection(dome, first, stack, cast("str", kind), 8)
        assert run_ledger.events() == ()


def test_a_bar_that_is_not_a_whole_non_negative_number_is_refused_before_any_event() -> (
    None
):
    labels = _grid(*CORONAL)
    dome = _dome(labels)
    first, stack = _lens(labels.shape), _stack(_coronal_centres())
    for bar in (-1, True, 2.0, None, "8"):
        with (
            recording() as run_ledger,
            pytest.raises(ValueError, match="invalid_minimum_tiles"),
        ):
            read_selection(dome, first, stack, "Coronal", cast("int", bar))
        assert run_ledger.events() == ()
    # Zero is a bar: every territory is a candidate.
    assert read_selection(dome, first, stack, "Coronal", 0).selection.code == "present"


def test_inputs_that_do_not_describe_one_slice_are_refused_by_name() -> None:
    labels = _grid(*CORONAL)
    dome = _dome(labels, slice_index=1)
    first, stack = _lens(labels.shape, slices=2), _stack(_coronal_centres(), slices=2)
    other_grid = _stack(_coronal_centres(9, 12), slices=2)
    with pytest.raises(ValueError, match="selection_inputs_disagree"):
        read_selection(dome, first, other_grid, "Coronal", 8)
    with pytest.raises(ValueError, match="selection_inputs_disagree"):
        read_selection(_dome(labels, slice_index=2), first, stack, "Coronal", 8)
    with pytest.raises(ValueError, match="selection_inputs_disagree"):
        read_selection(dome, _lens(labels.shape, slices=1), stack, "Coronal", 8)
    gone = _lens((0, 0), slices=0, code="predecessor_absent")
    with pytest.raises(ValueError, match="selection_inputs_disagree"):
        read_selection(dome, gone, stack, "Coronal", 8)
    # The refusal is never an IndexError, however far out the index is.
    with pytest.raises(ValueError, match="selection_inputs_disagree"):
        read_selection(_dome(labels, slice_index=99), first, stack, "Coronal", 8)


def test_the_selection_is_repeatable_and_writes_none_of_its_inputs() -> None:
    # Every input array here is read-only: a write anywhere in the orchestration would raise.
    labels = _grid(*CORONAL)
    dome = _dome(labels)
    first, stack = _lens(labels.shape), _stack(_coronal_centres())
    one = read_selection(dome, first, stack, "Coronal", 8)
    two = read_selection(dome, first, stack, "Coronal", 8)
    assert one.selection.why == two.selection.why
    assert _roles(one) == _roles(two) and one.lateral_sign == two.lateral_sign
    assert one.selection.candidate_codes == two.selection.candidate_codes


def test_no_record_field_code_or_sentence_carries_an_anatomical_word() -> None:
    names = [
        *(
            f.name
            for cls in (Selection, SelectionWithSign, ObjectRecord, TerritoryFacts)
            for f in dataclasses.fields(cls)
        ),
        *ROLE_CODES,
        *SELECTION_CODES,
        *PAIR_CODES,
        *ANTERIOR_CODES,
        *WITNESS_CODES,
        *SIGN_CODES,
    ]
    sentences = []
    for rows, centres, kind, bar in (
        (CORONAL, _coronal_centres(), "Coronal", 8),
        (SAGITTAL, _sagittal_centres(), "Sagittal", 8),
        (AXIAL, _axial_centres(), "Axial", 2),
    ):
        labels = _grid(*rows)
        result = read_selection(
            _dome(labels), _lens(labels.shape), _stack(centres), kind, bar
        )
        sentences.append(result.selection.why)
    absent = read_selection(
        _absent_dome(),
        _lens((0, 0), slices=0, code="predecessor_absent"),
        _stack(np.empty((0, 0, 3)), slices=0, code="no_stacked_volume"),
        "Coronal",
        8,
    )
    sentences.append(absent.selection.why)
    for text in (*names, *sentences):
        assert not ANATOMY.search(text), text
    # The unit's new files: the arrangement and the drawer say tile, object, territory, index.
    for path in (
        Path(pictures.__file__ or ""),
        Path(selection_frames.__file__ or ""),
    ):
        assert not ANATOMY.search(path.read_text()), path.name


def test_the_selection_record_keeps_exactly_the_fields_the_lead_declared() -> None:
    # The sign rides beside the Selection in a record of its own; the Selection gained only the
    # border of the dome it is made from.
    assert [f.name for f in dataclasses.fields(Selection)] == [
        "series_uid",
        "slice_index",
        "plane_kind",
        "code",
        "why",
        "pair_code",
        "objects",
        "candidate_codes",
        "border",
    ]
    assert [f.name for f in dataclasses.fields(SelectionWithSign)] == [
        "selection",
        "lateral_sign",
    ]
    labels = _grid(*CORONAL)
    result = read_selection(
        _dome(labels), _lens(labels.shape), _stack(_coronal_centres()), "Coronal", 8
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.lateral_sign = "right"  # ty: ignore[invalid-assignment]


# --- the arrangement, 5b.5 ---------------------------------------------------------------------


def _object_record(item: ObjectRecord) -> dict:
    facts = item.facts

    def number(value: float) -> float | None:
        return float(value) if np.isfinite(value) else None

    return {
        "index": item.index,
        "role_code": item.role_code,
        "tiles": item.tiles,
        "centre_lps": [number(v) for v in facts.centre_lps],
        "superior_mm": number(facts.superior_mm),
        "anterior_mm": number(facts.anterior_mm),
        "left_right_mm": number(facts.left_right_mm),
        "superior_extent_mm": [number(v) for v in facts.superior_extent_mm],
        "anterior_face_mm": number(facts.anterior_face_mm),
        "touches_leg_border": facts.touches_leg_border,
        "ringed": facts.ringed,
    }


def _slice_record(result: SelectionWithSign, dome: TileDome) -> dict:
    selection = result.selection
    return {
        "slice_index": selection.slice_index,
        "border": selection.border,
        "code": selection.code,
        "why": selection.why,
        "pair_code": selection.pair_code,
        "lateral_sign": result.lateral_sign,
        "candidate_codes": list(selection.candidate_codes),
        "peaks_rc": [[int(r), int(c)] for r, c in dome.peaks],
        "objects": [_object_record(item) for item in selection.objects],
    }


def _saved_slice(result: SelectionWithSign, dome: TileDome) -> pictures.SavedSlice:
    """The adapter's input for one slice, built from the stage's own records."""
    selection = result.selection
    return pictures.SavedSlice(
        slice_index=selection.slice_index,
        code=selection.code,
        why=selection.why,
        pair_code=selection.pair_code,
        lateral_sign=result.lateral_sign,
        candidate_codes=selection.candidate_codes,
        peaks_rc=tuple((int(r), int(c)) for r, c in dome.peaks),
        objects=tuple(
            pictures.SavedObject(
                index=item.index,
                role_code=item.role_code,
                tiles=item.tiles,
                centre_lps=(
                    float(item.facts.centre_lps[0]),
                    float(item.facts.centre_lps[1]),
                    float(item.facts.centre_lps[2]),
                ),
                superior_mm=item.facts.superior_mm,
                anterior_mm=item.facts.anterior_mm,
                left_right_mm=item.facts.left_right_mm,
                superior_extent_mm=item.facts.superior_extent_mm,
                anterior_face_mm=item.facts.anterior_face_mm,
                touches_leg_border=item.facts.touches_leg_border,
                ringed=item.facts.ringed,
            )
            for item in selection.objects
        ),
        border=selection.border,
    )


def _three_slices():
    """Three chosen slices of one series on the Coronal scene's grid: named, no territory, absent.

    A series' domes share one grid, so the slice with no territory and the slice read from a dome
    with no interior both carry an all-zero map of the same shape.
    """
    centres = _coronal_centres()
    coronal = _grid(*CORONAL)
    zeros = np.zeros_like(coronal)
    domes = (
        _dome(coronal, slice_index=3),
        _dome(zeros, code="present", slice_index=7),
        _dome(zeros, code="no_interior", slice_index=11),
    )
    first = _lens(coronal.shape, slices=12)
    stack = _stack(centres, slices=12)
    results = tuple(read_selection(d, first, stack, "Coronal", 8) for d in domes)
    return domes, results, stack


def test_the_standing_names_a_made_selection_and_every_silence_apart() -> None:
    assert slice_standing("present") == "named"
    assert slice_standing(None) == "selection_not_saved"
    assert slice_standing("predecessor_absent") == "selection_absent"
    assert slice_standing("no_territory") == "no_territory"
    assert slice_standing("lesion") == "selection_code_unknown"
    assert slice_standing(3) == "selection_code_unknown"


def test_the_standing_is_total_and_never_named_without_the_stage_saying_present() -> (
    None
):
    # MUST NOT: name a slice from a code the stage does not say, or from one that is not text;
    # and every answer is one of the declared standings.
    for code in (*SELECTION_CODES, None, "", "Present", 1, b"present", ("present",)):
        standing = slice_standing(code)
        assert standing in SELECTION_STANDINGS, code
        if standing == "named":
            assert code == "present"


def test_the_adapter_selects_labels_and_planes_and_alters_nothing() -> None:
    domes, results, stack = _three_slices()
    slices = tuple(_saved_slice(r, d) for r, d in zip(results, domes, strict=True))
    labels = np.stack([d.labels for d in domes])
    planes = np.arange(3 * 40 * 48, dtype=np.uint16).reshape(3, 40, 48)
    panels = selection_panels("Coronal", slices, labels, planes, stack.bounds_rc)
    assert panels.plane_kind == "Coronal"
    assert [c.standing for c in panels.chosen] == [
        "named",
        "no_territory",
        "selection_absent",
    ]
    assert [c.index for c in panels.chosen] == [3, 7, 11]
    named, quiet, absent = panels.chosen
    np.testing.assert_array_equal(named.labels, domes[0].labels)
    assert named.labels is not None and named.labels.dtype == np.int32
    assert quiet.labels is not None and not quiet.labels.any()
    # A slice the stage made no selection for has no map to tint; its plane is still handed on.
    assert absent.labels is None
    for position, chosen in enumerate(panels.chosen):
        assert chosen.plane is not None and chosen.plane.dtype == np.uint16
        np.testing.assert_array_equal(chosen.plane, planes[position])
    assert panels.bounds_rc is not None and panels.bounds_rc.dtype == np.int64
    assert named.lateral_sign == "left" and named.pair_code == "selected"
    assert [o.role_code for o in named.objects] == [
        "superior_big",
        "inferior_big",
        "lateral_small_ringed",
    ]
    assert named.peaks_rc == tuple(tuple(map(int, p)) for p in domes[0].peaks)


def test_the_adapter_keeps_every_absence_absent() -> None:
    nothing = selection_panels(None, (), None, None, None)
    assert nothing.plane_kind is None and nothing.chosen == ()
    assert nothing.bounds_rc is None
    domes, results, _ = _three_slices()
    slices = tuple(_saved_slice(r, d) for r, d in zip(results, domes, strict=True))
    bare = selection_panels("Coronal", slices, None, None, None)
    assert all(c.labels is None and c.plane is None for c in bare.chosen)
    assert bare.chosen[0].standing == "named"
    assert bare.bounds_rc is None


# --- the drawer, 5b.5 ---------------------------------------------------------------------------

STACK_ARRAYS = ("median", "minimum", "maximum", "coverage", "centres_lps", "bounds_rc")


def _descriptor(array: np.ndarray) -> dict:
    return {
        "shape": array.shape,
        "dtype": array.dtype.str,
        "digest": sha256(
            array.dtype.str.encode() + str(array.shape).encode() + array.tobytes()
        ).hexdigest(),
        "bytes": array.nbytes,
    }


def _stack_record(stack: SquintStack) -> tuple[dict, dict]:
    """The squint stack's record as the writer saves it (`squint_stack_record`), written out."""
    record = {
        "code": stack.code,
        "why": stack.why,
        "code_names": ["present", "no_stacked_volume", "geometry_unreadable"],
        "tile_mm": stack.tile_mm,
        "tile_shape_rc": [int(size) for size in stack.tile_shape_rc],
        "slices": int(stack.median.shape[0]),
        "tiles_rc": [int(size) for size in stack.median.shape[1:]],
        "arrays": {name: f"squint_stack_{name}" for name in STACK_ARRAYS},
    }
    return record, {
        f"squint_stack_{name}": getattr(stack, name) for name in STACK_ARRAYS
    }


def _selection_record(plane_kind, results, domes, planes) -> tuple[dict, dict]:
    """The selection as the writer should save it: one record, two arrays.

    Per series: `record["selection"]` with the told `plane_kind`, the stage's vocabularies, the
    grid, one entry per chosen slice in the order of the series' domes, and the names of its
    arrays; and the arrays `selection_labels` (the domes' labels stacked, int32, one grid per
    slice) and, when the plane at each chosen slice is kept, `selection_planes`.
    """
    labels = np.stack([d.labels for d in domes]).astype(np.int32)
    record = {
        "plane_kind": plane_kind,
        "code_names": list(SELECTION_CODES),
        "role_code_names": list(ROLE_CODES),
        "pair_code_names": list(PAIR_CODES),
        "anterior_code_names": list(ANTERIOR_CODES),
        "witness_code_names": list(WITNESS_CODES),
        "sign_code_names": list(SIGN_CODES),
        "tiles_rc": [int(size) for size in labels.shape[1:]],
        "slices": [_slice_record(r, d) for r, d in zip(results, domes, strict=True)],
        "arrays": {
            "labels": "selection_labels",
            "planes": None if planes is None else "selection_planes",
        },
    }
    arrays = {"selection_labels": labels}
    if planes is not None:
        arrays["selection_planes"] = planes
    return record, arrays


def _saved_record(
    tmp_path: Path,
    *,
    with_selection: bool = True,
    with_stack: bool = True,
    with_planes: bool = True,
    stack_rows: int = 10,
) -> dict:
    """One series record shaped as the writer saves it, with its arrays on disk."""
    domes, results, stack = _three_slices()
    if stack_rows != 10:
        stack = _stack(_coronal_centres(stack_rows, 12), slices=12)
    plane = np.arange(40 * 48, dtype=np.uint16).reshape(40, 48)
    planes = np.stack([plane, plane + 1, plane + 2]) if with_planes else None
    saved: dict[str, np.ndarray] = {}
    entry: dict = {
        "study_uid": "study",
        "series_uid": "series",
        "view": ["Coronal", "1", "1"],
        "artifact": "series.npz",
    }
    if with_stack:
        entry["squint_stack"], arrays = _stack_record(stack)
        saved.update(arrays)
    if with_selection:
        entry["selection"], arrays = _selection_record(
            "Coronal", results, domes, planes
        )
        saved.update(arrays)
    np.savez_compressed(tmp_path / "series.npz", allow_pickle=False, **saved)
    entry["arrays"] = {name: _descriptor(array) for name, array in saved.items()}
    return json.loads(json.dumps(entry, allow_nan=False))


def test_the_reader_reconstitutes_a_writer_shaped_record(tmp_path: Path) -> None:
    record = _saved_record(tmp_path)
    artifact, panels = selection_frames.saved_selection(tmp_path, record)
    assert artifact == tmp_path / "series.npz"
    assert panels.plane_kind == "Coronal"
    assert [c.standing for c in panels.chosen] == [
        "named",
        "no_territory",
        "selection_absent",
    ]
    named = panels.chosen[0]
    assert [o.index for o in named.objects] == [1, 2, 3]
    assert [o.tiles for o in named.objects] == [32, 35, 4]
    assert named.lateral_sign == "left" and named.candidate_codes == (
        "",
        "",
        "lateral_small_ringed",
    )
    assert named.labels is not None and named.labels.shape == (10, 12)
    assert named.plane is not None and named.plane.shape == (40, 48)
    assert panels.bounds_rc is not None and panels.bounds_rc.shape == (10, 12, 4)
    assert named.objects[2].left_right_mm == pytest.approx(84.0)
    assert named.objects[2].ringed is True


def test_the_reader_says_when_no_selection_was_saved(tmp_path: Path) -> None:
    record = _saved_record(tmp_path, with_selection=False)
    _, panels = selection_frames.saved_selection(tmp_path, record)
    assert panels.plane_kind is None and panels.chosen == ()
    assert panels.bounds_rc is None


def test_the_reader_draws_tiles_alone_when_the_plane_was_not_saved(
    tmp_path: Path,
) -> None:
    record = _saved_record(tmp_path, with_planes=False)
    _, panels = selection_frames.saved_selection(tmp_path, record)
    assert all(c.plane is None for c in panels.chosen)
    assert panels.chosen[0].standing == "named" and panels.chosen[0].labels is not None


def _rewrite(tmp_path: Path, record: dict, name: str, array: np.ndarray) -> None:
    """Replace one array of the saved artifact and give it the descriptor the writer would."""
    with np.load(tmp_path / "series.npz", allow_pickle=False) as artifact:
        arrays = {key: artifact[key] for key in artifact.files}
    arrays[name] = array
    np.savez_compressed(tmp_path / "series.npz", allow_pickle=False, **arrays)
    record["arrays"][name] = json.loads(json.dumps(_descriptor(array)))


def _recast(tmp_path: Path, record: dict, name: str, dtype: type) -> None:
    """Save the same array again in another representation."""
    with np.load(tmp_path / "series.npz", allow_pickle=False) as artifact:
        array = artifact[name]
    _rewrite(tmp_path, record, name, array.astype(dtype))


def _relabel(
    tmp_path: Path, record: dict, position: int, row: int, column: int, value: int
) -> None:
    """Save the labels again with one tile of one slice given another label."""
    with np.load(tmp_path / "series.npz", allow_pickle=False) as artifact:
        labels = artifact["selection_labels"].copy()
    labels[position, row, column] = value
    _rewrite(tmp_path, record, "selection_labels", labels)


def _slice(record: dict, position: int = 0) -> dict:
    return record["selection"]["slices"][position]


#: Every way a saved selection can disagree with the writer, each with the name it is refused by.
#: The Coronal scene's peaks are [[0, 2], [5, 2], [7, 10]]: peak k is the seed of territory k + 1.
#: A case is (how to spoil the record, the refusal, the options `_saved_record` is built with).
REFUSALS = [
    pytest.param(
        lambda r, t: r["arrays"]["selection_labels"].update(digest="changed"),
        "saved_array_digest_mismatch",
        {},
        id="tampered array",
    ),
    pytest.param(
        lambda r, t: _slice(r).update(code="lesion"),
        "saved_selection_code_unknown:lesion",
        {},
        id="code",
    ),
    pytest.param(
        lambda r, t: _slice(r)["objects"][0].update(role_code="lesion"),
        "saved_selection_role_unknown:lesion",
        {},
        id="role",
    ),
    pytest.param(
        lambda r, t: _slice(r).update(lateral_sign="medial"),
        "saved_selection_sign_unknown:medial",
        {},
        id="sign",
    ),
    pytest.param(
        lambda r, t: _slice(r).update(pair_code="pair"),
        "saved_selection_pair_code_unknown:pair",
        {},
        id="pair word",
    ),
    pytest.param(
        lambda r, t: _slice(r).update(candidate_codes=["", "", "mystery"]),
        "saved_selection_candidate_code_unknown:mystery",
        {},
        id="candidate word",
    ),
    pytest.param(
        lambda r, t: r["selection"].update(plane_kind="Oblique"),
        "saved_selection_plane_kind_unknown:Oblique",
        {},
        id="plane word",
    ),
    pytest.param(
        lambda r, t: r["selection"].update(role_code_names=["a"]),
        "saved_selection_vocabulary_mismatch",
        {},
        id="role vocabulary",
    ),
    pytest.param(
        lambda r, t: r["selection"].update(sign_code_names=[]),
        "saved_selection_vocabulary_mismatch",
        {},
        id="sign vocabulary",
    ),
    pytest.param(
        lambda r, t: _slice(r)["objects"][0].update(superior_mm="up"),
        "saved_selection_not_a_number:superior_mm",
        {},
        id="fact not a number",
    ),
    pytest.param(
        lambda r, t: _slice(r)["objects"][0].update(index=True),
        "saved_selection_not_a_whole_number:index",
        {},
        id="index a bool",
    ),
    pytest.param(
        lambda r, t: _slice(r).update(slice_index=1.5),
        "saved_selection_not_a_whole_number:slice_index",
        {},
        id="slice index not whole",
    ),
    pytest.param(
        lambda r, t: _slice(r)["objects"][0].update(centre_lps=[1.0, 2.0]),
        "saved_selection_not_a_list:centre_lps",
        {},
        id="centre not three numbers",
    ),
    pytest.param(
        lambda r, t: _slice(r)["objects"][0].update(ringed=1),
        "saved_selection_object_not_a_bool:ringed",
        {},
        id="ringed not a bool",
    ),
    pytest.param(
        lambda r, t: _slice(r)["objects"][0].update(touches_leg_border="yes"),
        "saved_selection_object_not_a_bool:touches_leg_border",
        {},
        id="border not a bool",
    ),
    pytest.param(
        lambda r, t: _slice(r)["objects"][0].pop("tiles"),
        "saved_selection_object_field_missing:tiles",
        {},
        id="object field missing",
    ),
    pytest.param(
        lambda r, t: _slice(r)["objects"].__setitem__(0, "x"),
        "saved_selection_object_not_a_record",
        {},
        id="object not a record",
    ),
    pytest.param(
        lambda r, t: r["selection"]["slices"].__setitem__(0, 3),
        "saved_selection_slice_not_a_record",
        {},
        id="slice not a record",
    ),
    pytest.param(
        lambda r, t: _slice(r).update(why=3),
        "saved_selection_slice_field_invalid:why",
        {},
        id="why not text",
    ),
    pytest.param(
        lambda r, t: _slice(r).update(candidate_codes="x"),
        "saved_selection_slice_field_invalid:candidate_codes",
        {},
        id="candidate codes not a list",
    ),
    pytest.param(
        lambda r, t: _slice(r).update(peaks_rc=[[0]]),
        "saved_selection_slice_field_invalid:peaks_rc",
        {},
        id="peak not a pair",
    ),
    pytest.param(
        lambda r, t: _slice(r).update(peaks_rc=[[-1, 0]]),
        "saved_selection_slice_field_invalid:peaks_rc",
        {},
        id="peak below the grid",
    ),
    pytest.param(
        lambda r, t: _slice(r).update(objects={}),
        "saved_selection_slice_field_invalid:objects",
        {},
        id="objects not a list",
    ),
    pytest.param(
        lambda r, t: _slice(r)["objects"][1].update(tiles=34),
        "saved_selection_tiles_mismatch:2",
        {},
        id="tile count",
    ),
    pytest.param(
        lambda r, t: _slice(r)["objects"].pop(),
        "saved_selection_objects_labels_mismatch",
        {},
        id="object missing for a label",
    ),
    pytest.param(
        lambda r, t: _slice(r).update(peaks_rc=[[0, 2]]),
        "saved_selection_peak_missing:2",
        {},
        id="peak missing",
    ),
    pytest.param(
        lambda r, t: _slice(r).update(peaks_rc=[[5, 2], [0, 2], [7, 10]]),
        "saved_selection_peak_outside_territory:1",
        {},
        id="peak in another territory",
    ),
    pytest.param(
        lambda r, t: _slice(r).update(peaks_rc=[[0, 2], [5, 2], [99, 10]]),
        "saved_selection_peak_outside_territory:3",
        {},
        id="peak off the grid",
    ),
    pytest.param(
        lambda r, t: _slice(r).update(candidate_codes=["", ""]),
        "saved_selection_candidate_codes_mismatch",
        {},
        id="candidate codes short",
    ),
    pytest.param(
        lambda r, t: _slice(r, 1).update(objects=_slice(r)["objects"]),
        "saved_selection_objects_without_territory",
        {},
        id="objects on a slice with no territory",
    ),
    pytest.param(
        lambda r, t: _relabel(t, r, 1, 0, 0, 1),
        "saved_selection_labels_without_objects",
        {},
        id="labels on a slice with no objects",
    ),
    pytest.param(
        lambda r, t: _relabel(t, r, 1, 0, 0, -1),
        "saved_selection_label_negative",
        {},
        id="negative label",
    ),
    pytest.param(
        lambda r, t: _slice(r).update(slice_index=12),
        "saved_selection_slice_outside_stack",
        {},
        id="slice outside the stack",
    ),
    pytest.param(
        lambda r, t: r["selection"]["slices"].pop(),
        "saved_selection_slices_mismatch",
        {},
        id="slice count",
    ),
    pytest.param(
        lambda r, t: _rewrite(
            t, r, "selection_planes", np.zeros((2, 40, 48), dtype=np.uint16)
        ),
        "saved_selection_slices_mismatch",
        {},
        id="plane count",
    ),
    pytest.param(
        lambda r, t: r["selection"].update(tiles_rc=[9, 12]),
        "saved_selection_shape_mismatch:labels",
        {},
        id="grid size",
    ),
    pytest.param(
        lambda r, t: r["selection"].update(tiles_rc=[10]),
        "saved_selection_tiles_invalid",
        {},
        id="grid not a pair",
    ),
    pytest.param(
        lambda r, t: r["selection"].update(slices="x"),
        "saved_selection_slices_invalid",
        {},
        id="slices not a list",
    ),
    pytest.param(
        lambda r, t: r.update(selection="yes"),
        "saved_selection_not_a_record",
        {},
        id="selection not a record",
    ),
    pytest.param(
        lambda r, t: r["selection"].update(arrays={"labels": None}),
        "saved_selection_array_unnamed:labels",
        {},
        id="labels unnamed",
    ),
    pytest.param(
        lambda r, t: r["selection"]["arrays"].update(planes=5),
        "saved_selection_array_unnamed:planes",
        {},
        id="planes unnamed",
    ),
    pytest.param(
        lambda r, t: _recast(t, r, "selection_labels", np.int64),
        "saved_selection_representation_invalid:labels",
        {},
        id="labels not int32",
    ),
    pytest.param(
        lambda r, t: _recast(t, r, "selection_planes", np.bool_),
        "saved_selection_representation_invalid:planes",
        {},
        id="planes not numbers",
    ),
    pytest.param(
        lambda r, t: _rewrite(
            t,
            r,
            "selection_planes",
            np.zeros((3, 36, 48), dtype=np.uint16),
        ),
        "saved_selection_covers_another_plane",
        {},
        id="plane the tiles do not cover",
    ),
    pytest.param(
        lambda r, t: None,
        "saved_selection_without_a_stack",
        {"with_stack": False},
        id="no stack",
    ),
    pytest.param(
        lambda r, t: None,
        "saved_selection_grid_mismatch",
        {"stack_rows": 9},
        id="stack over another grid",
    ),
]


@pytest.mark.parametrize(("spoil", "message", "options"), REFUSALS)
def test_the_reader_refuses_a_saved_record_that_disagrees_with_the_writer(
    tmp_path: Path, spoil, message: str, options: dict
) -> None:
    # MUST NOT: draw a tampered array, a code or role or sign or plane word the stage does not
    # say, a vocabulary that is not the stage's, a fact that is not a number, objects that are
    # not the labels' territories, a peak outside its territory, a selection saved without its
    # stack or over another grid, or a plane the stack's tiles do not cover; each is named.
    record = _saved_record(tmp_path, **options)
    spoil(record, tmp_path)
    with pytest.raises(ValueError, match=message):
        selection_frames.saved_selection(tmp_path, record)


def test_a_fact_the_stage_could_not_read_comes_back_as_none_and_never_as_zero(
    tmp_path: Path,
) -> None:
    record = _saved_record(tmp_path)
    _slice(record)["objects"][0].update(
        superior_mm=None, centre_lps=[None, 1.0, 2.0], superior_extent_mm=[None, 3.0]
    )
    _, panels = selection_frames.saved_selection(tmp_path, record)
    first = panels.chosen[0].objects[0]
    assert first.superior_mm is None
    assert first.centre_lps == (None, 1.0, 2.0)
    assert first.superior_extent_mm == (None, 3.0)


def test_a_series_with_no_chosen_slice_is_read_without_a_stack_and_drawn_in_words(
    tmp_path: Path,
) -> None:
    record = _saved_record(tmp_path, with_stack=False)
    _rewrite(tmp_path, record, "selection_labels", np.zeros((0, 10, 12), np.int32))
    record["selection"]["slices"] = []
    record["selection"]["arrays"]["planes"] = None
    _, panels = selection_frames.saved_selection(tmp_path, record)
    assert panels.plane_kind == "Coronal" and panels.chosen == ()
    assert panels.bounds_rc is None
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = selection_frames.draw(tmp_path, "study", out)
        (series,) = manifest["series"]
        assert series["selection"]["slices"] == 0 and series["chosen"] == []
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_an_out_directory_outside_data_is_an_argument_refusal(tmp_path: Path) -> None:
    record = _saved_record(tmp_path)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    with pytest.raises(ArgumentRefusal, match="private data directory"):
        selection_frames.draw(tmp_path, "study", tmp_path / "out")
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    with pytest.raises(ArgumentRefusal, match="no saved records"):
        selection_frames.draw(tmp_path, "another-study", out)
    assert not out.exists()


def test_the_drawer_writes_one_sheet_per_series_with_its_manifest(
    tmp_path: Path,
) -> None:
    """The impure edge, end to end: one image per series under data/, bound to the receipt."""
    record = _saved_record(tmp_path)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = selection_frames.draw(tmp_path, "study", out)
        assert manifest["images"] == ["01-coronal-fs1-fat1.png"]
        assert manifest["image"] == "01-coronal-fs1-fat1.png"
        assert (out / "01-coronal-fs1-fat1.png").stat().st_size > 0
        assert (out / "manifest.json").exists()
        assert manifest["standings"] == list(SELECTION_STANDINGS)
        assert set(manifest["legend"]["role_colours"]) == set(ROLE_CODES)
        (series,) = manifest["series"]
        assert series["selection"]["plane_kind"] == "Coronal"
        assert series["selection"]["slices"] == 3
        assert [c["drawn"] for c in series["chosen"]] == [
            "named",
            "no_territory",
            "selection_absent",
        ]
        assert [c["lateral_sign"] for c in series["chosen"]] == [
            "left",
            "side_abstained",
            "side_abstained",
        ]
        assert series["chosen"][0]["roles"] == {
            "superior_big": 1,
            "inferior_big": 1,
            "lateral_small_ringed": 1,
        }
        assert series["chosen"][0]["lateral_sign"] == "left"
        assert json.loads((out / "manifest.json").read_text()) == manifest
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_the_drawer_says_tiles_alone_when_no_plane_was_saved(tmp_path: Path) -> None:
    record = _saved_record(tmp_path, with_planes=False)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = selection_frames.draw(tmp_path, "study", out)
        (series,) = manifest["series"]
        assert series["chosen"][0]["drawn"] == "tiles_alone"
        assert series["selection"]["arrays"].keys() == {"labels"}
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_the_drawer_names_a_series_with_no_selection_saved(tmp_path: Path) -> None:
    record = _saved_record(tmp_path, with_selection=False)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = selection_frames.draw(tmp_path, "study", out)
        (series,) = manifest["series"]
        assert series["selection"] is None and series["chosen"] == []
        assert (out / manifest["image"]).exists()
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_the_command_draws_the_sheets_and_prints_where_they_are(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    record = _saved_record(tmp_path)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    arguments = ["selection_frames", str(tmp_path), "--study-uid", "study"]
    monkeypatch.setattr(sys, "argv", [*arguments, "--out", str(out)])
    try:
        selection_frames.main()
        printed = json.loads(capsys.readouterr().out)
        assert printed["images"] == [str(out.resolve() / "01-coronal-fs1-fat1.png")]
        assert Path(printed["manifest"]).exists()
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_the_command_turns_a_wrong_argument_into_a_usage_error_and_nothing_else(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    record = _saved_record(tmp_path)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    arguments = ["selection_frames", str(tmp_path), "--study-uid", "study"]
    monkeypatch.setattr(sys, "argv", [*arguments, "--out", str(tmp_path / "out")])
    with pytest.raises(SystemExit) as stop:
        selection_frames.main()
    assert stop.value.code == 2
    assert "private data directory" in capsys.readouterr().err
    # A record that disagrees with the writer is corruption, not a mistyped flag: it propagates.
    record["selection"]["slices"][0]["code"] = "lesion"
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    monkeypatch.setattr(sys, "argv", [*arguments, "--out", str(out)])
    with pytest.raises(ValueError, match="saved_selection_code_unknown"):
        selection_frames.main()
    assert not out.exists()


def test_the_drawer_refuses_before_drawing_when_it_has_no_words_or_colours_for_the_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # MUST NOT: draw a standing nobody wrote words for, a role nobody coloured, or from a picture
    # module whose source cannot be bound into the manifest; nothing is made on the way.
    record = _saved_record(tmp_path)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    with monkeypatch.context() as patch:
        patch.delitem(selection_frames.STANDING_WORDS, "no_territory")  # type: ignore[attr-defined]
        with pytest.raises(RuntimeError, match="selection_standing_unworded:no_ter"):
            selection_frames.draw(tmp_path, "study", out)
    with monkeypatch.context() as patch:
        patch.delitem(selection_frames.ROLE_COLOURS, "central_big")  # type: ignore[attr-defined]
        with pytest.raises(
            RuntimeError, match="selection_vocabulary_uncoloured:central"
        ):
            selection_frames.draw(tmp_path, "study", out)
    with monkeypatch.context() as patch:
        patch.setattr(pictures, "__file__", None)
        with pytest.raises(RuntimeError, match="picture_module_source_unavailable"):
            selection_frames.draw(tmp_path, "study", out)
    assert not out.exists()


def test_the_picture_module_is_the_adapter_the_drawer_reads() -> None:
    assert selection_frames.pictures is pictures
    assert set(selection_frames.ROLE_COLOURS) == set(ROLE_CODES)
    assert set(selection_frames.ROLE_ALPHAS) == set(ROLE_CODES)
    assert set(selection_frames.STANDING_WORDS) == set(SELECTION_STANDINGS)
