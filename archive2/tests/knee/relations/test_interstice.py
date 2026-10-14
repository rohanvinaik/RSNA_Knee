"""The interstice on one chosen slice (the-funnel tasks 8.1 and 8.3), both signs, every call direct.

`read_interstices` is built over hand-made records of the neighbouring stages, because the
interstice is a pure function of them: a 15 x 9 tile grid at 8 mm, one territory above (rows 1 to
4, columns 1 to 7, wider than the overlap) and one below (rows 10 to 13, columns 2 to 6), the five
rows between them dark obstacle tiles except two (one unseeded interior tile the extent must
keep, one tile the first lens cleared that it must never take). The conjunction holds a different
word on every other slice, so a read of the wrong slice shows. The strips are cut by the real
`edge_points` from the same labels and then shuffled, so the wall reading cannot lean on the
strip's order. Every input array is read-only: a write to any of them fails the test. The
function under test is called in each test body itself, never through a helper; helpers only
build its inputs.

The pictures (`knee.pictures.interstice`) and the drawer (`workbench.render.interstice_frames`) are
tested in the second half of this file, over a record shaped as the writer will save it.
"""

from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from knee.collapse.squint_stack import read_squint_stack
from knee.lenses.conjunction import CONJUNCTION_CODES, Conjunction
from knee.objects.strip import TRACE_CODES, Strip, edge_points
from knee.objects.tile_dome import BORDER_CODES, TileDome
from knee.pictures import interstice as pictures
from knee.pictures.interstice import (
    ENTRY_STANDINGS,
    PLANE_STANDINGS,
    entry_standing,
    interstice_panels,
    plane_standing,
    wall_tally,
)
from knee.relations.facing import FacingPair, FacingPairs
from knee.relations.interstice import (
    FILL_CODES,
    INTERSTICE_CODES,
    POSITION_CODES,
    SIDE_CODES,
    WALL_CODES,
    Content,
    InterstitialRecord,
    read_interstices,
)
from knee.study.series import Series, SeriesGeometry, walk_indices
from knee.study.tables import SeriesRow
from knee.telemetry import recording
from workbench.measure.object_analysis import array_table, squint_stack_record
from workbench.render import interstice_frames
from workbench.render._out import PROJECT, ArgumentRefusal

UID = "S"
SLICE = 3
SLICES = 5
TILES_DOWN, TILES_ACROSS = 15, 9
PITCH = 8.0
TILE_PX = 4
OFFSETS = np.arange(-4.0, 4.5, 1.0)  # nine samples; index 4 is the edge itself
#: The two readings of a paired plane's border, both seated by the dome (`BORDER_CODES`). Every
#: record of a scene carries the one it was read under; `BORDER` is the default scene's.
BORDER, OTHER_BORDER = BORDER_CODES
#: A strip holds one profile for every native pixel along each boundary segment, so a segment of a
#: tile `TILE_PX` pixels across is `TILE_PX` profiles. The default scene's upper object has 22
#: boundary segments and its lower one 18; five of each enter the extent.
SEGMENTS = {1: 22, 2: 18}
ENTERING_SEGMENTS = 5
POINTS = {label: count * TILE_PX for label, count in SEGMENTS.items()}
ENTERING = ENTERING_SEGMENTS * TILE_PX

WORD = {word: index for index, word in enumerate(CONJUNCTION_CODES)}
WALL = {word: index for index, word in enumerate(WALL_CODES)}

# The bodies of `below_below` the extent holds, as (row, column) tiles. Column 4 is the axis.
BODY_A = [(6, 2), (7, 2), (7, 3)]  # an L: peripheral, on the side of lower x
BODY_B1 = [(8, 4)]  # on the axis: central, and exactly zero left-right offset
BODY_C = [(8, 6), (9, 6)]  # peripheral, on the side of higher x
BODY_B2 = [(9, 3)]  # exactly on the central boundary, touching B1 only at a corner
#: `below_below` where it must NOT make a content: the cleared tile that would bridge B1 and C,
#: a tile inside the first territory, a tile beyond the overlap on either side, and a tile of
#: the second territory.
DECOYS = [(8, 5), (3, 3), (5, 1), (6, 7), (11, 4)]
INTERIOR_BETWEEN = (6, 3)
CLEARED_BETWEEN = (8, 5)

# What the first wall (the upper territory) and the second wall read, by the tile each profile
# enters. Everything else a strip holds is a decoy and reads as a plate and the fill.
KIND_CODE = {
    "plate_fill": WALL["plate_fill"],
    "plate_layer_fill": WALL["plate_layer_fill"],
    "far_vs_first": WALL["unreadable"],
    "unbracketed": WALL["unreadable"],
    "no_plate": WALL["unreadable"],
}
FIRST_KINDS = {
    (5, 2): "plate_fill",
    (5, 3): "plate_layer_fill",
    (5, 4): "far_vs_first",
    (5, 5): "plate_fill",
    (5, 6): "unbracketed",
}
SECOND_KINDS = {
    (9, 2): "unbracketed",
    (9, 3): "unbracketed",
    (9, 4): "no_plate",
    (9, 5): "unbracketed",
    (9, 6): "unbracketed",
}
# Each kind as the strip stores it: nine native digits along the cast (int8), the band's near and
# far offsets, and the trace word. `far_vs_first` is the witness for where the sequence starts:
# read from the band's far offset (-1 mm) it begins with a layer and is unreadable; read from the
# band's first sample it would be a plate, a layer and the fill.
KIND_STORED = {
    "plate_fill": ([1, 1, 1, 1, -1, 1, 1, 1, 1], (0.0, 0.0), "bracketed"),
    "plate_layer_fill": ([1, 1, 1, 1, -1, 0, 0, 1, 1], (0.0, 0.0), "bracketed"),
    "far_vs_first": ([-1, -1, -1, 0, 1, 1, 1, 1, 1], (-4.0, -1.0), "bracketed"),
    "unbracketed": ([1, 1, 1, 1, -1, 1, 1, 1, 1], (np.nan, np.nan), "no_dark_bracket"),
    "no_plate": ([1, 1, 1, 1, 0, 1, 1, 1, 1], (0.0, 0.0), "bracketed"),
}


def _frozen(array: np.ndarray) -> np.ndarray:
    array.setflags(write=False)
    return array


def _centres() -> np.ndarray:
    """Tile centres in LPS mm, (TR, TC, 3): +x along the columns, z falling down the rows."""
    rows, columns = np.indices((TILES_DOWN, TILES_ACROSS))
    centres = np.zeros((TILES_DOWN, TILES_ACROSS, 3))
    centres[..., 0] = -32.0 + PITCH * columns
    centres[..., 2] = 52.0 - PITCH * rows
    return _frozen(centres)


def _bounds() -> np.ndarray:
    rows, columns = np.indices((TILES_DOWN, TILES_ACROSS))
    low_rows, low_columns = rows * TILE_PX, columns * TILE_PX
    return np.stack(
        (low_rows, low_rows + TILE_PX, low_columns, low_columns + TILE_PX), axis=-1
    ).astype(np.int64)


def _labels() -> np.ndarray:
    labels = np.zeros((TILES_DOWN, TILES_ACROSS), dtype=np.int32)
    # The upper territory is wider than the overlap (columns 1 to 7 against 2 to 6), so the
    # profiles along its facing side are split: five enter the extent and two do not.
    labels[1:5, 1:8] = 1
    labels[10:14, 2:7] = 2
    return labels


def _expected_extent() -> np.ndarray:
    """Rows 5 to 9, columns 2 to 6: the five rows between the faces, within the overlap."""
    extent = np.zeros((TILES_DOWN, TILES_ACROSS), dtype=bool)
    extent[5:10, 2:7] = True
    extent[CLEARED_BETWEEN] = False
    return extent


def _slice_codes() -> np.ndarray:
    codes = np.full((TILES_DOWN, TILES_ACROSS), WORD["above_below"], dtype=np.uint8)
    for tile in BODY_A + BODY_B1 + BODY_C + BODY_B2 + DECOYS:
        codes[tile] = WORD["below_below"]
    codes[INTERIOR_BETWEEN] = WORD["at_at"]
    codes[5, 4] = WORD["self_silent"]
    codes[9, 5] = WORD["partner_silent"]
    codes[9, 4] = WORD["unmatched"]
    return codes


def _strip(
    label: int,
    kinds: dict[tuple[int, int], str],
    labels: np.ndarray | None = None,
    slice_index: int = SLICE,
    border: str = BORDER,
) -> tuple[Strip, list[tuple]]:
    """One object's strip cut by the real `edge_points`, then shuffled; with the tile each profile
    enters and its kind, in the stored order.

    One profile per native pixel along each tile-boundary segment, as `read_strip` makes them. The
    strip's `beyond_tiles` is the tile `edge_points` names beyond each point, shuffled with the
    points; each profile's kind is looked up by that tile, so the wall a profile reads is fixed by
    the record the module reads. (`test_the_tile_a_strip_names_beyond_a_profile_is_the_tile_its_
    point_and_normal_enter` checks the record against the geometry, so the kinds are not leaning on
    an error in `edge_points`.)"""
    grid = _labels() if labels is None else labels
    points, normals, beyond = edge_points(grid, _bounds(), label)
    order = np.random.default_rng(20261013 + label).permutation(len(points))
    points, normals, beyond = (
        points[order].copy(),
        normals[order].copy(),
        beyond[order].copy(),
    )
    stored: list[tuple] = []
    digits, bands, traces = [], [], []
    for tile in beyond:
        kind = kinds.get((int(tile[0]), int(tile[1])), "plate_fill")
        row, band, trace = KIND_STORED[kind]
        stored.append(((int(tile[0]), int(tile[1])), kind))
        digits.append(row)
        bands.append(band)
        traces.append(TRACE_CODES[trace])
    n = len(points)
    strip = Strip(
        series_uid=UID,
        slice_index=slice_index,
        object_index=label,
        code="present",
        why="hand-made",
        strip_mm=4.0,
        edge_points=_frozen(points),
        normals=_frozen(normals),
        offsets_mm=_frozen(OFFSETS.copy()),
        profiles=_frozen(np.zeros((n, len(OFFSETS)))),
        trace_codes=_frozen(np.array(traces, dtype=np.uint8)),
        band_mm=_frozen(np.array(bands, dtype=np.float64)),
        exchange_codes=_frozen(np.zeros(0, dtype=np.uint8)),
        native_digits=_frozen(np.array(digits, dtype=np.int8)),
        low_edge=0.0,
        high_edge=1.0,
        population_count=n,
        strip_mask=_frozen(
            np.zeros((TILES_DOWN * TILE_PX, TILES_ACROSS * TILE_PX), dtype=bool)
        ),
        beyond_tiles=_frozen(beyond),
        border=border,
    )
    return strip, stored


@dataclass(frozen=True, slots=True)
class Scene:
    facing: FacingPairs
    dome: TileDome
    conjunction: Conjunction
    centres: np.ndarray
    strips: dict[int, Strip]
    stored: dict[int, list[tuple]]


def _scene(
    border: str = BORDER,
    peaks: tuple[tuple[int, int], tuple[int, int]] = ((2, 4), (11, 4)),
) -> Scene:
    """The default scene under one border: every record of it carries that border.

    `peaks` are where the dome grounded the two territories (peak k seeds territory k + 1), the
    tiles a sheet writes each object's wall at."""
    labels = _labels()
    cleared = np.zeros(labels.shape, dtype=bool)
    cleared[0, :] = cleared[-1, :] = True
    cleared[:, 0] = cleared[:, -1] = True
    cleared[CLEARED_BETWEEN] = True
    interior = labels > 0
    interior[INTERIOR_BETWEEN] = True
    obstacle = labels == 0
    obstacle[INTERIOR_BETWEEN] = False
    dome = TileDome(
        series_uid=UID,
        slice_index=SLICE,
        code="present",
        why="hand-made",
        prominence_mm=8.0,
        obstacle=_frozen(obstacle),
        cleared=_frozen(cleared),
        interior=_frozen(interior),
        height=_frozen(np.zeros(labels.shape)),
        peaks=_frozen(np.array(peaks, dtype=np.int64)),
        peak_height_mm=_frozen(np.array([16.0, 16.0])),
        labels=_frozen(labels),
        border=border,
    )
    # The gap the facing stage would cut: the dark tiles between the faces, not the unseeded
    # interior one and not the cleared one. The whole region is one chain touching both.
    gap = _expected_extent()
    gap[INTERIOR_BETWEEN] = False
    pair = FacingPair(
        first=1,
        second=2,
        first_role="superior_big",
        second_role="inferior_big",
        code="facing",
        sites=0,
        gap_sites=int(gap.sum()),
        gap_tiles=_frozen(gap),
        saddle_mm=0.0,
    )
    facing = FacingPairs(
        series_uid=UID,
        slice_index=SLICE,
        code="present",
        why="hand-made",
        minimum_sites=1,
        pairs=(pair,),
        border=border,
    )
    # Every other slice reads `at_at` everywhere: reading the wrong slice changes the fill.
    codes = np.full((SLICES, TILES_DOWN, TILES_ACROSS), WORD["at_at"], dtype=np.uint8)
    codes[SLICE] = _slice_codes()
    conjunction = Conjunction(
        recipient_uid=UID,
        partner_uid="P",
        code="present",
        why="hand-made",
        codes=_frozen(codes),
        counts=tuple(
            int(n) for n in np.bincount(codes.ravel(), minlength=len(CONJUNCTION_CODES))
        ),
    )
    first, first_stored = _strip(1, FIRST_KINDS, border=border)
    second, second_stored = _strip(2, SECOND_KINDS, border=border)
    return Scene(
        facing=facing,
        dome=dome,
        conjunction=conjunction,
        centres=_centres(),
        strips={1: first, 2: second},
        stored={1: first_stored, 2: second_stored},
    )


def _expected_walls(stored: list[tuple], extent: np.ndarray) -> list[int]:
    """The wall codes the stored profiles must read: those entering the extent, in stored order."""
    return [KIND_CODE[kind] for tile, kind in stored if extent[tile]]


def _tiles(content: Content) -> set[tuple[int, int]]:
    return {(int(r), int(c)) for r, c in zip(*np.nonzero(content.tiles), strict=True)}


@pytest.fixture(autouse=True)
def run_ledger():
    """Every test runs with the ledger on, so a NumPy scalar handed to it fails loudly."""
    with recording() as ledger:
        yield ledger


# --- the whole reading -------------------------------------------------------------------------


def test_a_facing_pair_gets_one_interstice_with_its_extent_walls_fill_and_contents() -> (
    None
):
    scene = _scene()
    records = read_interstices(
        scene.facing, scene.dome, scene.conjunction, scene.centres, scene.strips, "left"
    )
    assert len(records) == 1
    record = records[0]
    assert isinstance(record, InterstitialRecord)
    assert (record.series_uid, record.slice_index, record.first, record.second) == (
        UID,
        SLICE,
        1,
        2,
    )
    assert record.code == "present" and record.code in INTERSTICE_CODES
    assert record.extent.dtype == bool
    np.testing.assert_array_equal(record.extent, _expected_extent())
    # Walls: the profiles entering the extent, named, in the strip's own (shuffled) order.
    expected_first = _expected_walls(scene.stored[1], record.extent)
    expected_second = _expected_walls(scene.stored[2], record.extent)
    assert len(expected_first) == ENTERING and len(expected_second) == ENTERING
    assert record.first_wall_codes.dtype == np.uint8
    assert record.first_wall_codes.tolist() == expected_first
    assert record.second_wall_codes.tolist() == expected_second
    # Fill: the words counted over the extent's 24 tiles; the plurality read pair names it.
    assert record.fill_counts == {
        "below_below": 7,
        "at_at": 1,
        "above_below": 13,
        "partner_silent": 1,
        "self_silent": 1,
        "unmatched": 1,
    }
    assert sum(record.fill_counts.values()) == int(record.extent.sum()) == 24
    assert record.fill_code == "above_below"
    # Contents: four bodies, in scan order, named by position and side only.
    assert [content.index for content in record.contents] == [1, 2, 3, 4]
    bodies = [_tiles(content) for content in record.contents]
    assert bodies == [set(BODY_A), set(BODY_B1), set(BODY_C), set(BODY_B2)]
    assert [c.position_code for c in record.contents] == [
        "peripheral",
        "central",
        "peripheral",
        "peripheral",
    ]
    assert [c.side_code for c in record.contents] == [
        "medial",
        "side_abstained",
        "lateral",
        "medial",
    ]
    np.testing.assert_allclose(
        record.contents[0].centre_lps, [-32.0 + 8.0 * 7 / 3, 0.0, 52.0 - 8.0 * 20 / 3]
    )
    np.testing.assert_allclose(
        record.contents[1].centre_lps, [0.0, 0.0, 52.0 - 8.0 * 8]
    )
    # The reason says how each wall was read: how many of the strip's profiles entered.
    assert record.why.startswith("24 extent tiles") and "4 contents" in record.why
    assert f"{ENTERING} of {POINTS[1]} profiles of object 1 entered the extent" in (
        record.why
    )
    assert f"{ENTERING} of {POINTS[2]} profiles of object 2 entered the extent" in (
        record.why
    )


def test_a_pair_that_is_not_facing_gets_no_record() -> None:
    scene = _scene()
    pair = scene.facing.pairs[0]
    other = replace(pair, code="touching_no_gap")
    facing = replace(scene.facing, pairs=(other,))
    assert (
        read_interstices(
            facing, scene.dome, scene.conjunction, scene.centres, scene.strips, "left"
        )
        == ()
    )
    # Mixed: only the facing one is read, and the non-facing one is not even checked against
    # the dome (its labels name nothing here).
    stray = replace(pair, first=7, second=9, code="too_few_sites")
    mixed = replace(scene.facing, pairs=(stray, pair))
    (record,) = read_interstices(
        mixed, scene.dome, scene.conjunction, scene.centres, scene.strips, "left"
    )
    assert (record.first, record.second) == (1, 2)


def test_a_present_record_with_no_pair_and_a_no_pair_record_give_nothing() -> None:
    scene = _scene()
    empty = replace(scene.facing, pairs=())
    none_roled = replace(scene.facing, code="no_pair", pairs=())
    for facing in (empty, none_roled):
        assert (
            read_interstices(
                facing,
                scene.dome,
                scene.conjunction,
                scene.centres,
                scene.strips,
                "left",
            )
            == ()
        )


# --- the extent --------------------------------------------------------------------------------


def test_the_extent_is_the_usable_tiles_between_the_faces_within_the_overlap_and_the_gap() -> (
    None
):
    scene = _scene()
    (record,) = read_interstices(
        scene.facing, scene.dome, scene.conjunction, scene.centres, scene.strips, "left"
    )
    extent = record.extent
    # Positive: the unseeded interior tile between the territories is kept though it is no gap
    # tile; every dark tile between is kept.
    assert (
        extent[INTERIOR_BETWEEN]
        and not scene.facing.pairs[0].gap_tiles[INTERIOR_BETWEEN]
    )
    assert extent[5:10, 2:7].sum() == 24
    # Negative: never a tile the lens cleared, even between the faces and within the overlap.
    assert scene.dome.obstacle[CLEARED_BETWEEN] and not extent[CLEARED_BETWEEN]
    # Negative: not the territories' own tiles, nothing beyond the faces, and nothing beside the
    # overlap of the widths (columns 1 and 7 are usable dark tiles, but outside both widths).
    assert not extent[scene.dome.labels > 0].any()
    assert not extent[:5].any() and not extent[10:].any()
    assert not extent[:, 1].any() and not extent[:, 7].any()
    assert extent.dtype == bool and extent.shape == scene.dome.labels.shape


def test_a_gap_tile_stays_in_the_extent_even_beyond_the_overlap_the_pair_handed_over() -> (
    None
):
    scene = _scene()
    pair = scene.facing.pairs[0]
    gap = pair.gap_tiles.copy()
    gap[12, 7] = True  # a tile no rule of the extent would add; the gap is kept whole
    wide = replace(pair, gap_tiles=_frozen(gap))
    (record,) = read_interstices(
        replace(scene.facing, pairs=(wide,)),
        scene.dome,
        scene.conjunction,
        scene.centres,
        scene.strips,
        "left",
    )
    assert record.extent[12, 7] and int(record.extent.sum()) == 25


def test_a_dark_tile_between_the_territories_is_in_the_extent_though_no_gap_chain_holds_it() -> (
    None
):
    scene = _scene()
    pair = scene.facing.pairs[0]
    gap = pair.gap_tiles.copy()
    # Dark and uncleared, between the faces, but held by no gap chain: the extent still takes it.
    gap[7, 3] = False
    (record,) = read_interstices(
        replace(scene.facing, pairs=(replace(pair, gap_tiles=_frozen(gap)),)),
        scene.dome,
        scene.conjunction,
        scene.centres,
        scene.strips,
        "left",
    )
    assert scene.dome.obstacle[7, 3] and not scene.dome.cleared[7, 3]
    assert record.extent[7, 3] and int(record.extent.sum()) == 24
    np.testing.assert_array_equal(record.extent, _expected_extent())


def test_the_side_is_measured_from_the_midpoint_of_the_two_centres_on_an_oblique_axis() -> (
    None
):
    scene = _scene()
    # The lower territory sits one column toward higher x: the axis between the centres is
    # oblique, the overlap of the widths is columns 3 to 6, and the midpoint of the centres is
    # 4 mm toward higher x than the upper one. A body in column 4 is 4 mm toward lower x of that
    # midpoint (medial for the sign "left") though it is exactly under the upper centre.
    labels = np.zeros_like(scene.dome.labels)
    labels[1:5, 2:7] = 1
    labels[10:14, 3:8] = 2
    cleared = np.zeros(labels.shape, dtype=bool)
    cleared[0, :] = cleared[-1, :] = True
    cleared[:, 0] = cleared[:, -1] = True
    dome = replace(
        scene.dome,
        labels=_frozen(labels),
        interior=_frozen(labels > 0),
        obstacle=_frozen(labels == 0),
        cleared=_frozen(cleared),
    )
    between = np.zeros(labels.shape, dtype=bool)
    between[5:10, 3:7] = True
    pair = replace(scene.facing.pairs[0], gap_tiles=_frozen(between))
    codes = np.array(scene.conjunction.codes)
    codes[SLICE] = WORD["above_below"]
    codes[SLICE][7, 4] = WORD["below_below"]
    conjunction = replace(scene.conjunction, codes=_frozen(codes))
    sides = {}
    for sign in ("left", "right", "side_abstained"):
        (record,) = read_interstices(
            replace(scene.facing, pairs=(pair,)),
            dome,
            conjunction,
            scene.centres,
            {},
            sign,
        )
        np.testing.assert_array_equal(record.extent, between)
        (content,) = record.contents
        assert content.position_code == "central"
        sides[sign] = content.side_code
    assert sides == {
        "left": "medial",
        "right": "lateral",
        "side_abstained": "side_abstained",
    }


def test_a_pair_that_leaves_no_tile_between_has_no_extent_and_says_so() -> None:
    scene = _scene()
    labels = np.zeros_like(scene.dome.labels)
    labels[1:5, 2:7] = 1
    labels[5:9, 2:7] = 2  # touching: no tile between the faces
    dome = replace(scene.dome, labels=_frozen(labels))
    pair = replace(
        scene.facing.pairs[0],
        gap_tiles=_frozen(np.zeros(labels.shape, dtype=bool)),
    )
    # Strips were read for both objects, and no profile of either enters an extent of no tile:
    # that is a different silence from no strip, and the reason says so.
    first, _ = _strip(1, {}, labels)
    second, _ = _strip(2, {}, labels)
    (record,) = read_interstices(
        replace(scene.facing, pairs=(pair,)),
        dome,
        scene.conjunction,
        scene.centres,
        {1: first, 2: second},
        "left",
    )
    assert record.code == "no_extent" and record.code in INTERSTICE_CODES
    assert not record.extent.any() and record.contents == ()
    assert record.fill_code == "fill_unread" and record.fill_counts == {}
    assert record.first_wall_codes.shape == (0,)
    # Each object is a block of four tile rows by five columns: 18 boundary segments, and one
    # profile for every native pixel along each.
    profiles = 18 * TILE_PX
    assert f"0 of {profiles} profiles of object 1 entered the extent" in record.why
    assert f"0 of {profiles} profiles of object 2 entered the extent" in record.why
    assert "no strip" not in record.why


# --- the fill and the contents -----------------------------------------------------------------


def test_the_fill_is_counted_over_the_extent_only_and_a_tie_is_a_mix() -> None:
    scene = _scene()
    codes = np.array(scene.conjunction.codes)
    # Outside the extent, a flood of one word changes nothing; inside, a tie is mixed.
    codes[SLICE, 1:5, 2:7] = WORD["above_above"]
    slice_codes = codes[SLICE]
    inside = _expected_extent()
    slice_codes[inside] = WORD["at_at"]
    ties = np.flatnonzero(inside.ravel())
    slice_codes.ravel()[ties[:12]] = WORD["below_at"]
    conjunction = replace(scene.conjunction, codes=_frozen(codes))
    (record,) = read_interstices(
        scene.facing, scene.dome, conjunction, scene.centres, scene.strips, "left"
    )
    assert record.fill_counts == {"below_at": 12, "at_at": 12}
    assert record.fill_code == "fill_mixed"
    assert "above_above" not in record.fill_counts


def test_a_body_is_four_connected_and_only_inside_the_extent() -> None:
    scene = _scene()
    (record,) = read_interstices(
        scene.facing, scene.dome, scene.conjunction, scene.centres, scene.strips, "left"
    )
    bodies = [_tiles(content) for content in record.contents]
    # Positive: the L is one body; B1 and B2 touch at a corner and are two bodies.
    assert set(BODY_A) in bodies and set(BODY_B1) in bodies and set(BODY_B2) in bodies
    # Negative: the cleared tile between B1 and C would have bridged them; it is no part of any
    # body. No decoy is in any body, and no content has a tile outside the extent.
    assert all(set(BODY_B1) | set(BODY_C) != body for body in bodies)
    assert all(not (body & set(DECOYS)) for body in bodies)
    assert all(
        record.extent[tuple(zip(*sorted(body), strict=True))].all() for body in bodies
    )


def test_position_is_central_inside_half_the_half_width_and_peripheral_from_it_outward() -> (
    None
):
    scene = _scene()
    # A single body 4 mm off the axis, then one exactly 8 mm off it: half the overlap's half
    # width is 8 mm, so the first is central and the second, on the boundary, is peripheral.
    cases = {((8, 3), (8, 4)): "central", ((8, 3),): "peripheral", ((8, 4),): "central"}
    for tiles, expected in cases.items():
        codes = np.array(scene.conjunction.codes)
        codes[SLICE] = WORD["above_below"]
        for tile in tiles:
            codes[SLICE][tile] = WORD["below_below"]
        (record,) = read_interstices(
            scene.facing,
            scene.dome,
            replace(scene.conjunction, codes=_frozen(codes)),
            scene.centres,
            scene.strips,
            "left",
        )
        (content,) = record.contents
        assert content.position_code == expected, tiles


def test_the_side_follows_the_sign_and_abstains_without_the_witness() -> None:
    scene = _scene()
    refused = [
        "invalid_measurement"
    ] * 4  # a word that is no sign: refused, not guessed
    expected = {
        "left": ["medial", "side_abstained", "lateral", "medial"],
        "right": ["lateral", "side_abstained", "medial", "lateral"],
        "side_abstained": ["side_abstained"] * 4,
        "invalid_measurement": ["side_abstained"] * 4,
        "lateral": refused,
    }
    for sign, sides in expected.items():
        (record,) = read_interstices(
            scene.facing,
            scene.dome,
            scene.conjunction,
            scene.centres,
            scene.strips,
            sign,
        )
        assert [c.side_code for c in record.contents] == sides, sign
        # The sign speaks of sides only; where the contents are does not move with it.
        assert [c.index for c in record.contents] == [1, 2, 3, 4]


def test_a_lone_column_of_tiles_has_no_plane_so_the_position_is_refused_by_name() -> (
    None
):
    labels = np.array([[1], [0], [2]], dtype=np.int32)
    centres = np.zeros((3, 1, 3))
    centres[:, 0, 2] = [8.0, 0.0, -8.0]
    dome = TileDome(
        series_uid=UID,
        slice_index=0,
        code="present",
        why="hand-made",
        prominence_mm=8.0,
        obstacle=_frozen(labels == 0),
        cleared=_frozen(np.zeros((3, 1), dtype=bool)),
        interior=_frozen(labels > 0),
        height=_frozen(np.zeros((3, 1))),
        peaks=_frozen(np.zeros((0, 2), dtype=np.int64)),
        peak_height_mm=_frozen(np.zeros(0)),
        labels=_frozen(labels),
        border=BORDER,
    )
    pair = FacingPair(1, 2, "a", "b", "facing", 0, 1, _frozen(labels == 0), 0.0)
    facing = FacingPairs(UID, 0, "present", "hand-made", 1, (pair,), BORDER)
    codes = np.full((1, 3, 1), WORD["below_below"], dtype=np.uint8)
    conjunction = Conjunction(
        UID, "P", "present", "hand-made", _frozen(codes), (0,) * 13
    )
    (record,) = read_interstices(
        facing, dome, conjunction, _frozen(centres), {}, "left"
    )
    assert record.code == "present" and record.extent[1, 0]
    (content,) = record.contents
    assert content.position_code == "invalid_measurement"
    assert content.side_code == "side_abstained"  # exactly zero left-right offset


# --- the walls ---------------------------------------------------------------------------------


def test_a_wall_is_read_from_the_bands_far_offset_outward_and_named() -> None:
    scene = _scene()
    (record,) = read_interstices(
        scene.facing, scene.dome, scene.conjunction, scene.centres, scene.strips, "left"
    )
    by_tile = {tile: kind for tile, kind in scene.stored[1] if tile in FIRST_KINDS}
    assert by_tile == FIRST_KINDS
    # The digits are int8 in the strip; reading them as plain ints names the plate and the fill.
    assert scene.strips[1].native_digits.dtype == np.int8
    assert WALL["plate_fill"] in record.first_wall_codes.tolist()
    assert WALL["plate_layer_fill"] in record.first_wall_codes.tolist()
    # The far-vs-first witness: begun at the band's first sample it would read as a plate, a
    # layer and the fill; begun at its far offset, as the spec says, it is unreadable. Every
    # segment that enters the extent is `TILE_PX` profiles of one kind: two plate-and-fill
    # segments, one with a layer and two unreadable.
    assert sorted(record.first_wall_codes.tolist()) == sorted(
        [WALL["plate_fill"]] * (2 * TILE_PX)
        + [WALL["plate_layer_fill"]] * TILE_PX
        + [WALL["unreadable"]] * (2 * TILE_PX)
    )
    assert all(
        code in range(len(WALL_CODES)) for code in record.first_wall_codes.tolist()
    )


def test_only_the_profiles_that_enter_the_extent_are_read() -> None:
    scene = _scene()
    (record,) = read_interstices(
        scene.facing, scene.dome, scene.conjunction, scene.centres, scene.strips, "left"
    )
    # The upper object's strip holds one profile for every native pixel along its 22 boundary
    # segments (88) and the lower object's along its 18 (72); five segments of each, 20
    # profiles, enter the extent. The upper object is wider than the overlap, so two of the
    # seven segments along its facing side enter dark tiles beside the overlap, which are not
    # the extent.
    assert len(scene.strips[1].edge_points) == POINTS[1]
    assert len(scene.strips[2].edge_points) == POINTS[2]
    assert record.first_wall_codes.size == ENTERING == record.second_wall_codes.size
    # A tile the lens cleared is not the extent: with the tile beyond one profile cleared, that
    # profile no longer enters it, and it is that profile (the only one that read a layer), not
    # another, that drops out; the other object's wall is unchanged.
    cleared = np.array(scene.dome.cleared)
    cleared[5, 3] = True
    dome = replace(scene.dome, cleared=_frozen(cleared))
    gap = scene.facing.pairs[0].gap_tiles.copy()
    gap[5, 3] = False
    pair = replace(scene.facing.pairs[0], gap_tiles=_frozen(gap))
    (cut,) = read_interstices(
        replace(scene.facing, pairs=(pair,)),
        dome,
        scene.conjunction,
        scene.centres,
        scene.strips,
        "left",
    )
    expected = _expected_extent()
    expected[5, 3] = False
    np.testing.assert_array_equal(cut.extent, expected)
    assert cut.first_wall_codes.tolist() == _expected_walls(scene.stored[1], expected)
    assert cut.first_wall_codes.size == ENTERING - TILE_PX
    assert WALL["plate_layer_fill"] not in cut.first_wall_codes.tolist()
    assert cut.second_wall_codes.tolist() == _expected_walls(scene.stored[2], expected)
    assert cut.second_wall_codes.size == ENTERING
    assert (
        f"{ENTERING - TILE_PX} of {POINTS[1]} profiles of object 1 entered the extent"
        in cut.why
    )


def test_a_pair_with_one_unbracketed_wall_records_it_unreadable_never_a_zero_gap() -> (
    None
):
    scene = _scene()
    (record,) = read_interstices(
        scene.facing, scene.dome, scene.conjunction, scene.centres, scene.strips, "left"
    )
    # The second object's profiles into the extent are unbracketed or have no plate: all of
    # them (five segments, 20 profiles), every one `unreadable`, none missing and none a number
    # of a gap.
    assert record.second_wall_codes.tolist() == [WALL["unreadable"]] * ENTERING
    assert record.second_wall_codes.size == ENTERING


def test_no_strip_means_empty_walls_and_a_strip_without_a_boundary_is_the_same_silence(
    run_ledger,
) -> None:
    scene = _scene()
    (bare,) = read_interstices(
        scene.facing, scene.dome, scene.conjunction, scene.centres, {}, "left"
    )
    for walls in (bare.first_wall_codes, bare.second_wall_codes):
        assert walls.shape == (0,) and walls.dtype == np.uint8
    # The extent, the fill and the contents do not need the walls, and the reason says that no
    # strip was handed over (not that none of its profiles entered).
    assert bare.code == "present" and bare.fill_code == "above_below"
    assert len(bare.contents) == 4
    assert "no strip handed over for object 1" in bare.why
    assert "no strip handed over for object 2" in bare.why
    # A strip that found no boundary reads as no strip at all, for that side only.
    run_ledger.clear()
    empty = replace(scene.strips[1], code="no_boundary")
    (one_side,) = read_interstices(
        scene.facing,
        scene.dome,
        scene.conjunction,
        scene.centres,
        {1: empty, 2: scene.strips[2]},
        "left",
    )
    assert one_side.first_wall_codes.shape == (0,)
    assert one_side.second_wall_codes.size == ENTERING
    assert "the strip of object 1 is no_boundary" in one_side.why
    assert (
        f"{ENTERING} of {POINTS[2]} profiles of object 2 entered the extent"
        in one_side.why
    )
    # Only the strip that held a reading counts as read.
    events = {e.name: dict(e.counts) for e in run_ledger.events()}
    assert events["strip.consumed_by.interstice"] == {"strips": 1}
    # A missing mapping is no strip either.
    no_mapping: Any = None
    (none_held,) = read_interstices(
        scene.facing,
        scene.dome,
        scene.conjunction,
        scene.centres,
        no_mapping,
        "left",
    )
    assert none_held.first_wall_codes.shape == (0,)


# --- what is not there -------------------------------------------------------------------------


def test_with_no_conjunction_the_fill_is_unread_and_there_are_no_contents() -> None:
    scene = _scene()
    (record,) = read_interstices(
        scene.facing, scene.dome, None, scene.centres, scene.strips, "left"
    )
    assert record.code == "present"
    assert record.fill_code == "fill_unread" and record.fill_counts == {}
    assert record.contents == ()
    # The extent and the walls are still read: a solitary plane has an interstice too.
    assert record.extent.sum() == 24 and record.first_wall_codes.size == ENTERING


def test_a_conjunction_handed_over_without_a_reading_is_a_predecessor_absent_record() -> (
    None
):
    scene = _scene()
    silent = replace(
        scene.conjunction,
        code="predecessor_absent",
        why="the line-up was absent",
        codes=_frozen(np.zeros((0, 0, 0), dtype=np.uint8)),
        counts=(0,) * 13,
    )
    records = read_interstices(
        scene.facing, scene.dome, silent, scene.centres, scene.strips, "left"
    )
    assert len(records) == 1
    (record,) = records
    assert record.code == "predecessor_absent" and record.code in INTERSTICE_CODES
    assert (record.first, record.second) == (0, 0)
    assert "conjunction" in record.why and "line-up was absent" in record.why
    assert record.extent.shape == (0, 0) and record.extent.dtype == bool
    assert record.first_wall_codes.shape == (0,) and record.contents == ()
    assert record.fill_code == "fill_unread" and record.fill_counts == {}


def test_an_absent_facing_record_or_dome_gives_one_predecessor_absent_record() -> None:
    scene = _scene()
    absent_facing = replace(scene.facing, code="predecessor_absent", pairs=())
    (record,) = read_interstices(
        absent_facing,
        scene.dome,
        scene.conjunction,
        scene.centres,
        scene.strips,
        "left",
    )
    assert record.code == "predecessor_absent"
    assert (record.series_uid, record.slice_index) == (UID, SLICE)
    assert "facing pairs" in record.why
    empty = np.zeros((0, 0))
    absent_dome = replace(
        scene.dome,
        code="predecessor_absent",
        slice_index=-1,
        obstacle=_frozen(empty.astype(bool)),
        cleared=_frozen(empty.astype(bool)),
        interior=_frozen(empty.astype(bool)),
        height=_frozen(empty),
        labels=_frozen(empty.astype(np.int32)),
    )
    (record,) = read_interstices(
        scene.facing,
        absent_dome,
        scene.conjunction,
        scene.centres,
        scene.strips,
        "left",
    )
    assert record.code == "predecessor_absent" and record.slice_index == -1
    assert "tile dome" in record.why


# --- the ledger and the arrays -----------------------------------------------------------------


def test_the_ledger_records_what_was_read_and_what_was_made(run_ledger) -> None:
    scene = _scene()
    read_interstices(
        scene.facing, scene.dome, scene.conjunction, scene.centres, scene.strips, "left"
    )
    events = [(e.name, dict(e.counts)) for e in run_ledger.events()]
    assert events == [
        ("facing.consumed_by.interstice", {"facing": 1}),
        ("tile_dome.consumed_by.interstice", {"dome": 1}),
        ("conjunction.consumed_by.interstice", {"conjunction": 1}),
        ("strip.consumed_by.interstice", {"strips": 2}),
        ("interstice.produced", {"interstices": 1, "contents": 4}),
    ]
    # Only for a record handed over: no conjunction and no strips record no consumption.
    run_ledger.clear()
    read_interstices(scene.facing, scene.dome, None, scene.centres, {}, "left")
    names = [e.name for e in run_ledger.events()]
    assert names == [
        "facing.consumed_by.interstice",
        "tile_dome.consumed_by.interstice",
        "interstice.produced",
    ]
    # A record that held no reading is consumed with a count of zero, and produces nothing.
    run_ledger.clear()
    absent = replace(scene.facing, code="predecessor_absent", pairs=())
    read_interstices(absent, scene.dome, scene.conjunction, scene.centres, {}, "left")
    events = [(e.name, dict(e.counts)) for e in run_ledger.events()]
    assert events[0] == ("facing.consumed_by.interstice", {"facing": 0})
    assert events[-1] == ("interstice.produced", {"interstices": 0, "contents": 0})


def test_every_array_made_is_frozen_and_every_input_is_left_as_it_was() -> None:
    scene = _scene()
    before = {
        "codes": scene.conjunction.codes.copy(),
        "labels": scene.dome.labels.copy(),
        "gap": scene.facing.pairs[0].gap_tiles.copy(),
        "digits": scene.strips[1].native_digits.copy(),
    }
    (record,) = read_interstices(
        scene.facing, scene.dome, scene.conjunction, scene.centres, scene.strips, "left"
    )
    for array in (record.extent, record.first_wall_codes, record.second_wall_codes):
        assert not array.flags.writeable
    for content in record.contents:
        assert not content.tiles.flags.writeable
        assert not content.centre_lps.flags.writeable
        assert (
            content.centre_lps.shape == (3,) and content.centre_lps.dtype == np.float64
        )
    # The inputs were read-only to begin with, so a write would have raised; they are unchanged.
    np.testing.assert_array_equal(scene.conjunction.codes, before["codes"])
    np.testing.assert_array_equal(scene.dome.labels, before["labels"])
    np.testing.assert_array_equal(scene.facing.pairs[0].gap_tiles, before["gap"])
    np.testing.assert_array_equal(scene.strips[1].native_digits, before["digits"])
    # The record owns its arrays: the extent is no view of the pair's gap.
    assert not np.shares_memory(record.extent, scene.facing.pairs[0].gap_tiles)


# --- records that contradict each other are refused by name -----------------------------------


def test_records_that_contradict_each_other_are_refused_by_name() -> None:
    scene = _scene()
    facing, dome, conjunction = scene.facing, scene.dome, scene.conjunction
    centres, strips = scene.centres, scene.strips
    with pytest.raises(ValueError, match="facing_and_dome_disagree"):
        read_interstices(
            replace(facing, slice_index=SLICE + 1),
            dome,
            conjunction,
            centres,
            strips,
            "left",
        )
    with pytest.raises(ValueError, match="facing_and_dome_disagree"):
        read_interstices(
            replace(facing, series_uid="other"),
            dome,
            conjunction,
            centres,
            strips,
            "left",
        )
    with pytest.raises(ValueError, match="centres_lps_disagree_with_the_dome"):
        read_interstices(
            facing,
            dome,
            conjunction,
            _frozen(np.zeros((TILES_DOWN, TILES_ACROSS))),
            strips,
            "left",
        )
    nan_centres = np.array(centres)
    nan_centres[2, 2, 0] = np.nan
    with pytest.raises(ValueError, match="centres_lps_disagree_with_the_dome"):
        read_interstices(
            facing, dome, conjunction, _frozen(nan_centres), strips, "left"
        )
    with pytest.raises(ValueError, match="conjunction_disagrees_with_the_dome"):
        read_interstices(
            facing,
            dome,
            replace(conjunction, recipient_uid="other"),
            centres,
            strips,
            "left",
        )
    with pytest.raises(ValueError, match="conjunction_disagrees_with_the_dome"):
        read_interstices(
            facing,
            dome,
            replace(conjunction, codes=_frozen(conjunction.codes[:SLICE])),
            centres,
            strips,
            "left",
        )
    with pytest.raises(ValueError, match="conjunction_disagrees_with_the_dome"):
        read_interstices(
            facing,
            dome,
            replace(conjunction, codes=_frozen(conjunction.codes[:, :-1])),
            centres,
            strips,
            "left",
        )
    unknown = np.array(conjunction.codes)
    unknown[SLICE, 0, 0] = len(CONJUNCTION_CODES)
    with pytest.raises(ValueError, match="conjunction_code_unknown"):
        read_interstices(
            facing,
            dome,
            replace(conjunction, codes=_frozen(unknown)),
            centres,
            strips,
            "left",
        )
    with pytest.raises(ValueError, match="dome_arrays_disagree"):
        read_interstices(
            facing,
            replace(dome, cleared=_frozen(np.zeros((2, 2), dtype=bool))),
            conjunction,
            centres,
            strips,
            "left",
        )
    stray = replace(facing.pairs[0], second=9)
    with pytest.raises(ValueError, match="facing_disagrees_with_the_dome"):
        read_interstices(
            replace(facing, pairs=(stray,)),
            dome,
            conjunction,
            centres,
            strips,
            "left",
        )
    shaped = replace(facing.pairs[0], gap_tiles=_frozen(np.zeros((2, 2), dtype=bool)))
    with pytest.raises(ValueError, match="facing_disagrees_with_the_dome"):
        read_interstices(
            replace(facing, pairs=(shaped,)),
            dome,
            conjunction,
            centres,
            strips,
            "left",
        )


def test_a_strip_that_was_not_cut_from_these_labels_is_refused_by_name() -> None:
    scene = _scene()
    facing, dome, conjunction = scene.facing, scene.dome, scene.conjunction
    centres = scene.centres
    strip = scene.strips[1]
    with pytest.raises(ValueError, match="strip_disagrees_with_the_slice"):
        read_interstices(
            facing,
            dome,
            conjunction,
            centres,
            {1: replace(strip, object_index=2), 2: scene.strips[2]},
            "left",
        )
    with pytest.raises(ValueError, match="strip_disagrees_with_the_slice"):
        read_interstices(
            facing,
            dome,
            conjunction,
            centres,
            {1: replace(strip, slice_index=SLICE + 1), 2: scene.strips[2]},
            "left",
        )
    # The tile each profile enters is the strip's own record, `beyond_tiles` (the stage no longer
    # derives it from the normals, so a normal that is no tile step is not what it refuses): a
    # tile outside the grid, or the object's own tile, is a strip cut from other labels.
    off_the_grid = np.array(strip.beyond_tiles)
    off_the_grid[0] = (TILES_DOWN, 0)
    with pytest.raises(ValueError, match="strip_disagrees_with_labels"):
        read_interstices(
            facing,
            dome,
            conjunction,
            centres,
            {1: replace(strip, beyond_tiles=_frozen(off_the_grid)), 2: scene.strips[2]},
            "left",
        )
    its_own = np.array(strip.beyond_tiles)
    its_own[0] = np.argwhere(np.asarray(dome.labels) == 1)[0]
    with pytest.raises(ValueError, match="strip_disagrees_with_labels"):
        read_interstices(
            facing,
            dome,
            conjunction,
            centres,
            {1: replace(strip, beyond_tiles=_frozen(its_own)), 2: scene.strips[2]},
            "left",
        )
    # One profile fewer in a direction than the labels replay: it was cut from other labels.
    short = {
        name: _frozen(np.array(getattr(strip, name))[1:])
        for name in (
            "edge_points",
            "normals",
            "profiles",
            "trace_codes",
            "band_mm",
            "native_digits",
        )
    }
    with pytest.raises(ValueError, match="strip_disagrees_with_labels"):
        read_interstices(
            facing,
            dome,
            conjunction,
            centres,
            {1: replace(strip, **short), 2: scene.strips[2]},
            "left",
        )
    off = np.array(strip.band_mm)
    # A bracketed band whose far offset is no sample of the grid, on a profile that enters the
    # extent (a profile that does not is never read, so its band is never matched).
    entering = [
        n
        for n, (tile, kind) in enumerate(scene.stored[1])
        if tile in FIRST_KINDS and kind == "plate_fill"
    ]
    off[entering[0]] = (0.25, 0.25)
    with pytest.raises(ValueError, match="strip_band_off_the_offsets"):
        read_interstices(
            facing,
            dome,
            conjunction,
            centres,
            {1: replace(strip, band_mm=_frozen(off)), 2: scene.strips[2]},
            "left",
        )


# --- the pictures: the standings and the adapter ----------------------------------------------

TILE_MM = 2.0  # at half a millimetre a pixel, 4 px: the grid is 15 x 9 tiles
AXIAL = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
PLANE_ROWS, PLANE_COLUMNS = TILES_DOWN * TILE_PX, TILES_ACROSS * TILE_PX
#: The study stage's saved walk: slices 0 and 2. Slice 3 is the series' selected slice and has
#: its own saved plane; slices 1 and 4 have no walked or selected plane at all.
WALKED = (0, 2)


def test_the_entry_standing_names_each_stage_code_and_a_word_the_stage_does_not_say() -> (
    None
):
    assert entry_standing("present") == "named"
    assert entry_standing("no_extent") == "no_extent"
    assert entry_standing("predecessor_absent") == "predecessor_absent"
    for code in ("lesion", "", "Present", None, 1, b"present", ("present",)):
        assert entry_standing(code) == "code_unknown", code
    for code in (*INTERSTICE_CODES, "lesion", None, 3):
        assert entry_standing(code) in ENTRY_STANDINGS


def test_the_plane_standing_takes_the_saved_plane_then_a_walked_slice_then_the_selected_one() -> (
    None
):
    assert plane_standing(4, (4, 2), WALKED, 3, True) == "saved"
    assert (
        plane_standing(2, (4, 2), WALKED, 3, True) == "saved"
    )  # saved wins over the walk
    assert (
        plane_standing(3, (3,), WALKED, 3, True) == "saved"
    )  # and over the selected plane
    assert plane_standing(2, (), WALKED, 3, True) == "walk"
    assert plane_standing(3, (4,), WALKED, 3, True) == "selected"
    assert plane_standing(3, (), (0, 3), 3, True) == "walk"  # a walked slice wins
    assert plane_standing(1, (4,), WALKED, 3, True) == "tiles_alone"
    # The selected plane counts only if it was saved; an index that is no whole number is no slice.
    assert plane_standing(3, (), WALKED, 3, False) == "tiles_alone"
    assert plane_standing(3, (), (), None, True) == "tiles_alone"
    for index in (True, 2.0, "2", None, -1):
        assert plane_standing(index, (4, 2), WALKED, 2, True) == "tiles_alone", index
    for index in (0, 2, 3, 4, True, None):
        assert plane_standing(index, (4,), WALKED, 3, True) in PLANE_STANDINGS


def test_the_wall_tally_counts_the_saved_codes_by_their_words_and_is_silent_without_any() -> (
    None
):
    codes = np.array([0, 1, 1, 2, 2, 2], dtype=np.uint8)
    assert wall_tally(codes) == (
        ("plate_layer_fill", 1),
        ("plate_fill", 2),
        ("unreadable", 3),
    )
    assert wall_tally(np.zeros(0, dtype=np.uint8)) == ()
    assert wall_tally(None) == ()


def _series() -> Series:
    """A synthetic series whose squint at 2 mm tiles is the 15 x 9 grid the interstices are over."""
    base = 20 + (np.arange(PLANE_ROWS * PLANE_COLUMNS) % 180).reshape(
        PLANE_ROWS, PLANE_COLUMNS
    )
    volume = np.stack([(base + 7 * z).astype(np.uint16) for z in range(SLICES)])
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
    return Series(
        row=SeriesRow("study", "series", "1", "1", "Coronal"),
        directory=Path("/nonexistent/the-funnel/interstice-wiring"),
        slices=(),
        stack=("stackable",),
        volume=volume,
        geometry=geometry,
        slice_codes=("decoded",) * SLICES,
        walk_indices=walk_indices(SLICES),
        walk=volume[list(walk_indices(SLICES))],
    )


@pytest.fixture
def stage():
    """Four interstices of one series as the stage makes them, one of each standing a sheet shows.

    Slice 3 is the selected slice, slice 2 a walked one, slice 4 a pair that faces across no
    tile and slice 1 a slice whose facing pairs were absent. Slice 2 has its own strips, which
    read other walls than slice 3's, and holds other bodies (not the first one), so a record cut
    from the stacked arrays at the wrong offset shows. The dome that grounded the objects is
    returned beside them: its saved peaks are where the walls are written.
    """
    scene = _scene()
    codes = np.array(scene.conjunction.codes)
    codes[2] = codes[SLICE]
    for tile in BODY_A:
        codes[2][tile] = WORD[
            "above_below"
        ]  # slice 2 holds the other three bodies only
    conjunction = replace(scene.conjunction, codes=_frozen(codes))
    kept = read_interstices(
        scene.facing, scene.dome, conjunction, scene.centres, scene.strips, "left"
    )
    # Slice 2's walls: every profile that enters reads a plate, a layer and the fill on the upper
    # object, a plate and the fill on the lower one.
    upper, _ = _strip(1, dict.fromkeys(FIRST_KINDS, "plate_layer_fill"), None, 2)
    lower, _ = _strip(2, dict.fromkeys(SECOND_KINDS, "plate_fill"), None, 2)
    # And on slice 2 the lens cleared one tile beside the upper object's facing side, so its
    # wall holds four profiles against the lower object's five: the two walls differ in length.
    cleared = np.array(scene.dome.cleared)
    cleared[5, 2] = True
    gap = scene.facing.pairs[0].gap_tiles.copy()
    gap[5, 2] = False
    narrowed = replace(scene.facing.pairs[0], gap_tiles=_frozen(gap))
    walked = read_interstices(
        replace(scene.facing, slice_index=2, pairs=(narrowed,)),
        replace(scene.dome, slice_index=2, cleared=_frozen(cleared)),
        conjunction,
        scene.centres,
        {1: upper, 2: lower},
        "left",
    )
    touching = np.zeros_like(scene.dome.labels)
    touching[1:5, 2:7] = 1
    touching[5:9, 2:7] = 2
    shut = replace(
        scene.facing.pairs[0],
        gap_tiles=_frozen(np.zeros(touching.shape, dtype=bool)),
    )
    faceless = read_interstices(
        replace(scene.facing, slice_index=4, pairs=(shut,)),
        replace(scene.dome, slice_index=4, labels=_frozen(touching)),
        conjunction,
        scene.centres,
        {},
        "left",
    )
    absent = read_interstices(
        replace(scene.facing, slice_index=1, code="predecessor_absent", pairs=()),
        replace(scene.dome, slice_index=1),
        conjunction,
        scene.centres,
        {},
        "left",
    )
    return scene.dome, kept + walked + faceless + absent


def _interstice_record(
    records, dome, plane_slices: tuple[int, ...] = ()
) -> tuple[dict, dict[str, np.ndarray]]:
    """The saved shape of a series' interstices, as the drawer documents it, from the stage's own.

    One entry per record; the arrays stacked in record order, with each record's wall length and
    content count in its entry; a record with no extent saves an all-False map of the grid; the
    territory tiles the walls are written at are the dome's saved peaks, `peaks[label - 1]`
    (`knee.objects.dome.dome` makes territory k + 1 peak k's); the acquired plane at each slice
    of `plane_slices` is saved beside them, an empty stack when there is none.
    """
    tiles = (TILES_DOWN, TILES_ACROSS)
    volume = _series().volume
    assert volume is not None

    def peak(label: int):
        if 1 <= label <= len(dome.peaks):
            return [int(v) for v in dome.peaks[label - 1]]
        return None

    entries, extents, firsts, seconds, bodies = [], [], [], [], []
    for record in records:
        entries.append(
            {
                "slice_index": int(record.slice_index),
                "first": int(record.first),
                "second": int(record.second),
                "code": record.code,
                "why": record.why,
                "fill_code": record.fill_code,
                "fill_counts": {w: int(n) for w, n in record.fill_counts.items()},
                "first_wall_count": int(record.first_wall_codes.size),
                "second_wall_count": int(record.second_wall_codes.size),
                "first_at_rc": peak(record.first),
                "second_at_rc": peak(record.second),
                "contents": [
                    {
                        "index": int(c.index),
                        "position_code": c.position_code,
                        "side_code": c.side_code,
                        "centre_lps": [float(v) for v in c.centre_lps],
                    }
                    for c in record.contents
                ],
            }
        )
        extents.append(
            record.extent
            if record.extent.shape == tiles
            else np.zeros(tiles, dtype=bool)
        )
        firsts.append(record.first_wall_codes)
        seconds.append(record.second_wall_codes)
        bodies.extend(c.tiles for c in record.contents)
    names = {
        short: f"interstice_{short}"
        for short in (
            "extent",
            "first_wall_codes",
            "second_wall_codes",
            "content_tiles",
            "planes",
        )
    }
    arrays = {
        names["extent"]: np.stack(extents),
        names["first_wall_codes"]: np.concatenate(firsts).astype(np.uint8),
        names["second_wall_codes"]: np.concatenate(seconds).astype(np.uint8),
        names["content_tiles"]: np.stack(bodies)
        if bodies
        else np.zeros((0, *tiles), dtype=bool),
        names["planes"]: volume[list(plane_slices)]
        if plane_slices
        else np.zeros((0, PLANE_ROWS, PLANE_COLUMNS), dtype=np.uint16),
    }
    saved = {
        "code_names": list(INTERSTICE_CODES),
        "wall_code_names": list(WALL_CODES),
        "fill_code_names": list(FILL_CODES),
        "position_code_names": list(POSITION_CODES),
        "side_code_names": list(SIDE_CODES),
        "conjunction_code_names": list(CONJUNCTION_CODES),
        "tiles_rc": list(tiles),
        "plane_slices": list(plane_slices),
        "interstices": entries,
        "arrays": names,
    }
    return saved, arrays


def _saved_record(
    tmp_path: Path,
    records,
    dome,
    *,
    with_interstice: bool = True,
    with_stack: bool = True,
    stack_tile_mm: float = TILE_MM,
    plane: np.ndarray | None = None,
    saved_planes: tuple[int, ...] = (),
    arrays_hook=None,
) -> dict:
    """One series record shaped as the writer will save it, with its arrays on disk."""
    series = _series()
    volume = series.volume
    assert volume is not None
    saved: dict[str, np.ndarray] = {
        "study_walk": volume[list(WALKED)],
        "acquired_plane": volume[SLICE] if plane is None else plane,
    }
    entry: dict = {
        "study_uid": "study",
        "series_uid": "series",
        "view": ["Coronal", "1", "1"],
        "code": "measured",
        "slice_index": SLICE,
        "source_plane": "slice-3.dcm",
        "artifact": "series.npz",
        "study": {
            "slice_codes": ["decoded"] * SLICES,
            "walk_indices": list(WALKED),
            "walk_array": "study_walk",
        },
    }
    if with_stack:
        stack_record, stack_arrays = squint_stack_record(
            read_squint_stack(series, stack_tile_mm)
        )
        saved.update(stack_arrays)
        entry["squint_stack"] = stack_record
    if with_interstice:
        record, arrays = _interstice_record(records, dome, saved_planes)
        saved.update(arrays)
        entry["interstice"] = record
    if arrays_hook is not None:
        arrays_hook(saved)
    np.savez_compressed(tmp_path / "series.npz", allow_pickle=False, **saved)
    entry["arrays"] = json.loads(json.dumps(array_table(saved), allow_nan=False))
    return json.loads(json.dumps(entry, allow_nan=False))


def test_the_adapter_cuts_the_stacked_arrays_back_into_records_and_alters_nothing(
    stage,
) -> None:
    dome, records = stage
    saved, arrays = _interstice_record(records, dome)
    series = _series()
    volume = series.volume
    assert volume is not None
    bounds = read_squint_stack(series, TILE_MM).bounds_rc
    frame = interstice_panels(
        saved["interstices"],
        arrays["interstice_extent"],
        arrays["interstice_first_wall_codes"],
        arrays["interstice_second_wall_codes"],
        arrays["interstice_content_tiles"],
        (TILES_DOWN, TILES_ACROSS),
        bounds,
        saved["plane_slices"],
        arrays["interstice_planes"],
        WALKED,
        volume[list(WALKED)],
        SLICE,
        volume[SLICE],
    )
    assert frame.saved and frame.tiles_rc == (TILES_DOWN, TILES_ACROSS)
    assert frame.bounds_rc is bounds and len(frame.panels) == 4
    assert [p.standing for p in frame.panels] == [
        "named",
        "named",
        "no_extent",
        "predecessor_absent",
    ]
    assert [p.plane_standing for p in frame.panels] == [
        "selected",
        "walk",
        "tiles_alone",
        "tiles_alone",
    ]
    first, second = frame.panels[0], frame.panels[1]
    assert (first.slice_index, first.first, first.second) == (SLICE, 1, 2)
    np.testing.assert_array_equal(first.extent, records[0].extent)
    assert first.fill_code == "above_below"
    assert dict(first.fill_counts) == records[0].fill_counts
    assert first.first_walls == (
        ("plate_layer_fill", TILE_PX),
        ("plate_fill", 2 * TILE_PX),
        ("unreadable", 2 * TILE_PX),
    )
    assert first.second_walls == (
        ("plate_layer_fill", 0),
        ("plate_fill", 0),
        ("unreadable", ENTERING),
    )
    assert (first.first_at_rc, first.second_at_rc) == ((2, 4), (11, 4))
    assert [c.index for c in first.contents] == [1, 2, 3, 4]
    for panel_content, made in zip(first.contents, records[0].contents, strict=True):
        np.testing.assert_array_equal(panel_content.tiles, made.tiles)
        assert (panel_content.position_code, panel_content.side_code) == (
            made.position_code,
            made.side_code,
        )
        np.testing.assert_allclose(panel_content.centre_lps, made.centre_lps)
    # The second record sits later in every stacked array and differs from the first in its
    # walls and its bodies: both must be cut from the right offsets, not the first record's.
    assert second.slice_index == 2 and [c.index for c in second.contents] == [1, 2, 3]
    assert dict(second.fill_counts) == records[1].fill_counts != dict(first.fill_counts)
    assert second.first_walls == (
        ("plate_layer_fill", ENTERING - TILE_PX),
        ("plate_fill", 0),
        ("unreadable", 0),
    )
    assert second.second_walls == (
        ("plate_layer_fill", 0),
        ("plate_fill", ENTERING),
        ("unreadable", 0),
    )
    assert [
        {(int(r), int(c)) for r, c in np.argwhere(content.tiles)}
        for content in second.contents
    ] == [set(BODY_B1), set(BODY_C), set(BODY_B2)]
    for panel_content, made in zip(second.contents, records[1].contents, strict=True):
        np.testing.assert_array_equal(panel_content.tiles, made.tiles)
        assert panel_content.index == made.index
        np.testing.assert_allclose(panel_content.centre_lps, made.centre_lps)
    # The planes are the saved ones, in the dtype they were saved in.
    assert first.plane is not None and first.plane.dtype == np.uint16
    np.testing.assert_array_equal(first.plane, volume[SLICE])
    np.testing.assert_array_equal(second.plane, volume[2])
    assert frame.panels[2].plane is None and frame.panels[3].plane is None
    # The silences stay silences: a pair across no tile has no walls, no fill and no contents.
    assert not frame.panels[2].extent.any()
    assert frame.panels[2].first_walls == () and frame.panels[2].contents == ()
    assert frame.panels[3].code == "predecessor_absent"
    assert (frame.panels[3].first_at_rc, frame.panels[3].second_at_rc) == (None, None)


def test_the_adapter_puts_the_plane_saved_with_the_interstices_under_its_extent(
    stage,
) -> None:
    dome, records = stage
    saved, arrays = _interstice_record(records, dome, (4, 2))
    series = _series()
    volume = series.volume
    assert volume is not None
    bounds = read_squint_stack(series, TILE_MM).bounds_rc
    planes = arrays["interstice_planes"].copy()
    planes[1] += (
        1  # slice 2's saved plane is not the walked one: the saved one must win
    )
    frame = interstice_panels(
        saved["interstices"],
        arrays["interstice_extent"],
        arrays["interstice_first_wall_codes"],
        arrays["interstice_second_wall_codes"],
        arrays["interstice_content_tiles"],
        (TILES_DOWN, TILES_ACROSS),
        bounds,
        saved["plane_slices"],
        planes,
        WALKED,
        volume[list(WALKED)],
        SLICE,
        volume[SLICE],
    )
    assert [p.plane_standing for p in frame.panels] == [
        "selected",
        "saved",
        "saved",
        "tiles_alone",
    ]
    np.testing.assert_array_equal(frame.panels[1].plane, volume[2] + 1)
    np.testing.assert_array_equal(frame.panels[2].plane, volume[4])
    # Slice indices whose planes were not handed on name no plane: with no stack of planes the
    # same slices fall back to the walked plane, then to the tiles alone.
    bare = interstice_panels(
        saved["interstices"],
        arrays["interstice_extent"],
        arrays["interstice_first_wall_codes"],
        arrays["interstice_second_wall_codes"],
        arrays["interstice_content_tiles"],
        (TILES_DOWN, TILES_ACROSS),
        bounds,
        saved["plane_slices"],
        None,
        WALKED,
        volume[list(WALKED)],
        SLICE,
        volume[SLICE],
    )
    assert [p.plane_standing for p in bare.panels] == [
        "selected",
        "walk",
        "tiles_alone",
        "tiles_alone",
    ]


def test_the_adapter_keeps_every_absence_absent() -> None:
    frame = interstice_panels(
        None, None, None, None, None, None, None, (), None, WALKED, None, None, None
    )
    assert not frame.saved and frame.panels == () and frame.tiles_rc is None
    # A walked slice whose plane was not saved is tiles alone, never a plane borrowed from another.
    dome_free = [
        {
            "slice_index": 2,
            "first": 1,
            "second": 2,
            "code": "present",
            "why": "w",
            "fill_code": "fill_unread",
            "fill_counts": {},
            "first_wall_count": 0,
            "second_wall_count": 0,
            "contents": [],
        }
    ]
    frame = interstice_panels(
        dome_free,
        np.ones((1, 3, 3), dtype=bool),
        np.zeros(0, dtype=np.uint8),
        np.zeros(0, dtype=np.uint8),
        np.zeros((0, 3, 3), dtype=bool),
        (3, 3),
        None,
        (2,),
        None,
        WALKED,
        None,
        None,
        None,
    )
    (panel,) = frame.panels
    assert panel.plane is None and panel.plane_standing == "tiles_alone"
    assert panel.first_walls == () and panel.first_at_rc is None


# --- the drawer ----------------------------------------------------------------------------------


def test_every_word_the_stage_says_has_its_words_and_its_colour_in_the_drawer() -> None:
    assert set(interstice_frames.POSITION_COLOURS) == set(POSITION_CODES)
    assert set(ENTRY_STANDINGS) == set(interstice_frames.STANDING_WORDS)
    assert set(PLANE_STANDINGS) == set(interstice_frames.PLANE_WORDS)
    assert set(interstice_frames.VOCABULARIES) == {
        "code_names",
        "wall_code_names",
        "fill_code_names",
        "position_code_names",
        "side_code_names",
        "conjunction_code_names",
    }
    assert interstice_frames.pictures is pictures


def test_an_outline_runs_only_where_the_tile_mask_ends() -> None:
    # Tile edges of a 4 x 4 grid of unit tiles: columns, then rows.
    edges = (np.arange(5.0), np.arange(5.0))
    single = np.zeros((4, 4), dtype=bool)
    single[1, 1] = True
    assert len(interstice_frames.outline_segments(single, edges)) == 4
    # An L of three tiles has eight sides facing outside it, not twelve: the edges the tiles
    # share are inside the body and are not drawn.
    ell = np.zeros((4, 4), dtype=bool)
    ell[1, 1] = ell[2, 1] = ell[2, 2] = True
    assert len(interstice_frames.outline_segments(ell, edges)) == 8
    # Two tiles that meet only at a corner share no edge: each is outlined whole.
    corner = np.zeros((4, 4), dtype=bool)
    corner[0, 0] = corner[1, 1] = True
    assert len(interstice_frames.outline_segments(corner, edges)) == 8
    # A tile on the frame has its frame sides too: beyond the grid is outside the mask.
    framed = np.zeros((4, 4), dtype=bool)
    framed[0, 0] = True
    assert len(interstice_frames.outline_segments(framed, edges)) == 4
    # No tile, no outline.
    assert interstice_frames.outline_segments(np.zeros((4, 4), dtype=bool), edges) == []
    # Every segment is one tile edge long, between whole native coordinates.
    for (x0, y0), (x1, y1) in interstice_frames.outline_segments(ell, edges):
        assert abs(x1 - x0) + abs(y1 - y0) == 1.0


def test_the_drawers_words_say_a_silence_as_a_silence_and_a_count_as_a_count() -> None:
    assert interstice_frames.words((), "nothing counted") == "nothing counted"
    assert (
        interstice_frames.words((("at_at", 2), ("above_below", 5)), "x")
        == "at_at 2 · above_below 5"
    )
    assert (
        interstice_frames.wall_text("object 1's wall", ())
        == "object 1's wall\nno profile read"
    )
    assert (
        interstice_frames.wall_text("w", (("plate_fill", 2), ("unreadable", 0)))
        == "w\nplate_fill 2\nunreadable 0"
    )
    # A tile's place is the middle of its saved edges: column 1 spans 4 to 8, row 0 spans 0 to 4.
    edges = (np.array([0.0, 4.0, 8.0]), np.array([0.0, 4.0]))
    assert interstice_frames.place(edges, (0, 1)) == (6.0, 2.0)


def test_the_reader_reconstitutes_a_writer_shaped_record(stage, tmp_path: Path) -> None:
    dome, records = stage
    record = _saved_record(tmp_path, records, dome)
    artifact, frame = interstice_frames.saved_interstices(tmp_path, record)
    assert artifact == tmp_path / "series.npz"
    assert frame.saved and frame.tiles_rc == (TILES_DOWN, TILES_ACROSS)
    assert frame.bounds_rc is not None
    assert frame.bounds_rc.shape == (TILES_DOWN, TILES_ACROSS, 4)
    assert [p.standing for p in frame.panels] == [
        "named",
        "named",
        "no_extent",
        "predecessor_absent",
    ]
    assert [p.plane_standing for p in frame.panels] == [
        "selected",
        "walk",
        "tiles_alone",
        "tiles_alone",
    ]
    first, second = frame.panels[0], frame.panels[1]
    np.testing.assert_array_equal(first.extent, records[0].extent)
    assert [c.position_code for c in first.contents] == [
        "peripheral",
        "central",
        "peripheral",
        "peripheral",
    ]
    assert first.second_walls == (
        ("plate_layer_fill", 0),
        ("plate_fill", 0),
        ("unreadable", ENTERING),
    )
    assert len(second.contents) == 3 and second.first_walls == (
        ("plate_layer_fill", ENTERING - TILE_PX),
        ("plate_fill", 0),
        ("unreadable", 0),
    )
    assert first.plane is not None and first.plane.shape == (PLANE_ROWS, PLANE_COLUMNS)


def test_the_reader_says_when_no_interstice_was_saved(stage, tmp_path: Path) -> None:
    dome, records = stage
    record = _saved_record(tmp_path, records, dome, with_interstice=False)
    _, frame = interstice_frames.saved_interstices(tmp_path, record)
    assert not frame.saved and frame.panels == () and frame.bounds_rc is None


def test_a_plane_saved_with_the_interstices_lies_under_its_extent_before_any_other(
    stage, tmp_path: Path
) -> None:
    dome, records = stage

    def brighter(arrays: dict) -> None:
        arrays["interstice_planes"][1] += (
            1  # slice 2's saved plane is not the walked one
        )

    record = _saved_record(
        tmp_path, records, dome, saved_planes=(4, 2), arrays_hook=brighter
    )
    _, frame = interstice_frames.saved_interstices(tmp_path, record)
    assert [p.plane_standing for p in frame.panels] == [
        "selected",
        "saved",
        "saved",
        "tiles_alone",
    ]
    volume = _series().volume
    assert volume is not None
    np.testing.assert_array_equal(frame.panels[0].plane, volume[SLICE])
    np.testing.assert_array_equal(frame.panels[1].plane, volume[2] + 1)
    np.testing.assert_array_equal(frame.panels[2].plane, volume[4])
    assert frame.panels[3].plane is None


def test_a_writer_that_saves_no_planes_with_the_interstices_is_a_silence_not_a_refusal(
    stage, tmp_path: Path
) -> None:
    dome, records = stage
    # Neither key: the planes fall back to the walked plane, the selected plane, or tiles alone.
    absent = _saved_record(tmp_path, records, dome)
    del absent["interstice"]["plane_slices"]
    del absent["interstice"]["arrays"]["planes"]
    _, frame = interstice_frames.saved_interstices(tmp_path, absent)
    assert frame.saved and len(frame.panels) == 4
    assert [p.plane_standing for p in frame.panels] == [
        "selected",
        "walk",
        "tiles_alone",
        "tiles_alone",
    ]
    # Null for both says the same as neither.
    nulled = _saved_record(tmp_path, records, dome)
    nulled["interstice"]["plane_slices"] = None
    nulled["interstice"]["arrays"]["planes"] = None
    _, frame = interstice_frames.saved_interstices(tmp_path, nulled)
    assert [p.plane_standing for p in frame.panels] == [
        "selected",
        "walk",
        "tiles_alone",
        "tiles_alone",
    ]


def test_the_reader_refuses_a_saved_record_that_disagrees_with_the_writer(
    stage, tmp_path: Path
) -> None:
    # MUST NOT: draw a tampered array, a code, fill, position or side the stage does not say, a
    # vocabulary that is not the stage's, lengths that are not the saved counts, a wall code
    # outside the vocabulary, a tile outside the grid, planes that are not the saved slices' or
    # not numeric, an interstice saved without its stack, over another grid than the stack's, or
    # over a plane of another size; each is named and raised.
    dome, records = stage

    def saved(**options) -> dict:
        return _saved_record(tmp_path, records, dome, **options)

    tampered = saved()
    tampered["arrays"]["interstice_extent"]["digest"] = "changed"
    with pytest.raises(ValueError, match="saved_array_digest_mismatch"):
        interstice_frames.saved_interstices(tmp_path, tampered)
    for key, value, name in (
        ("code", "lesion", "saved_interstice_code_unknown"),
        ("fill_code", "water", "saved_interstice_fill_unknown"),
        ("fill_counts", {"fat": 3}, "saved_interstice_counts_invalid"),
        ("first_wall_count", 99, "saved_interstice_shape_mismatch:first_wall_codes"),
        ("first_at_rc", [99, 0], "saved_interstice_tile_invalid"),
        ("slice_index", "3", "saved_interstice_not_a_whole_number"),
        ("why", 7, "saved_interstice_field_invalid"),
    ):
        record = saved()
        record["interstice"]["interstices"][0][key] = value
        with pytest.raises(ValueError, match=name):
            interstice_frames.saved_interstices(tmp_path, record)
    for key, value, name in (
        ("position_code", "inner", "saved_interstice_position_unknown"),
        ("side_code", "up", "saved_interstice_side_unknown"),
        ("centre_lps", [0.0, 0.0], "saved_interstice_centre_invalid"),
        ("index", 0, "saved_interstice_not_a_whole_number"),
    ):
        record = saved()
        record["interstice"]["interstices"][0]["contents"][0][key] = value
        with pytest.raises(ValueError, match=name):
            interstice_frames.saved_interstices(tmp_path, record)
    lost = saved()
    lost["interstice"]["interstices"][0]["contents"].pop()
    with pytest.raises(
        ValueError, match="saved_interstice_shape_mismatch:content_tiles"
    ):
        interstice_frames.saved_interstices(tmp_path, lost)
    worded = saved()
    worded["interstice"]["wall_code_names"] = ["plate_fill"]
    with pytest.raises(ValueError, match="saved_interstice_vocabulary_mismatch"):
        interstice_frames.saved_interstices(tmp_path, worded)
    shaped = saved()
    shaped["interstice"] = "yes"
    with pytest.raises(ValueError, match="saved_interstice_not_a_record"):
        interstice_frames.saved_interstices(tmp_path, shaped)
    unnamed = saved()
    del unnamed["interstice"]["arrays"]["extent"]
    with pytest.raises(ValueError, match="saved_interstice_array_unnamed:extent"):
        interstice_frames.saved_interstices(tmp_path, unnamed)
    # The planes are an optional pair; one key without the other disagrees with itself.
    unplaned = saved()
    del unplaned["interstice"]["arrays"]["planes"]
    with pytest.raises(ValueError, match="saved_interstice_planes_incomplete"):
        interstice_frames.saved_interstices(tmp_path, unplaned)
    misnamed = saved(saved_planes=(4,))
    misnamed["interstice"]["arrays"]["planes"] = 7
    with pytest.raises(ValueError, match="saved_interstice_array_unnamed:planes"):
        interstice_frames.saved_interstices(tmp_path, misnamed)
    gridded = saved()
    gridded["interstice"]["tiles_rc"] = [TILES_DOWN]
    with pytest.raises(ValueError, match="saved_interstice_tiles_invalid"):
        interstice_frames.saved_interstices(tmp_path, gridded)
    walked = saved()
    walked["study"]["walk_indices"] = [0]
    with pytest.raises(ValueError, match="saved_walk_indices_mismatch"):
        interstice_frames.saved_interstices(tmp_path, walked)
    # The saved planes: slices that repeat or are not whole numbers, a count that is not the
    # planes', planes of another size, and planes that are not numbers.
    repeated = saved(saved_planes=(4,))
    repeated["interstice"]["plane_slices"] = [4, 4]
    with pytest.raises(ValueError, match="saved_interstice_plane_slices_invalid"):
        interstice_frames.saved_interstices(tmp_path, repeated)
    unsliced = saved()
    del unsliced["interstice"]["plane_slices"]
    with pytest.raises(ValueError, match="saved_interstice_planes_incomplete"):
        interstice_frames.saved_interstices(tmp_path, unsliced)
    mislisted = saved(saved_planes=(4,))
    mislisted["interstice"]["plane_slices"] = "4"
    with pytest.raises(ValueError, match="saved_interstice_plane_slices_invalid"):
        interstice_frames.saved_interstices(tmp_path, mislisted)
    counted = saved(saved_planes=(4,))
    counted["interstice"]["plane_slices"] = [4, 2]
    with pytest.raises(ValueError, match="saved_interstice_planes_mismatch"):
        interstice_frames.saved_interstices(tmp_path, counted)

    def smaller(arrays: dict) -> None:
        arrays["interstice_planes"] = np.zeros((1, 4, 4), dtype=np.uint16)

    with pytest.raises(ValueError, match="saved_interstice_covers_another_plane"):
        interstice_frames.saved_interstices(
            tmp_path, saved(saved_planes=(4,), arrays_hook=smaller)
        )

    def truthy(arrays: dict) -> None:
        arrays["interstice_planes"] = np.ones(
            (1, PLANE_ROWS, PLANE_COLUMNS), dtype=bool
        )

    with pytest.raises(
        ValueError, match="saved_interstice_representation_invalid:planes"
    ):
        interstice_frames.saved_interstices(
            tmp_path, saved(saved_planes=(4,), arrays_hook=truthy)
        )

    def outside(arrays: dict) -> None:
        arrays["interstice_first_wall_codes"][0] = len(WALL_CODES)

    with pytest.raises(ValueError, match="saved_interstice_wall_code_unknown"):
        interstice_frames.saved_interstices(tmp_path, saved(arrays_hook=outside))
    with pytest.raises(ValueError, match="saved_interstice_without_a_stack"):
        interstice_frames.saved_interstices(tmp_path, saved(with_stack=False))
    with pytest.raises(ValueError, match="saved_interstice_grid_mismatch"):
        interstice_frames.saved_interstices(tmp_path, saved(stack_tile_mm=4.0))
    with pytest.raises(ValueError, match="saved_interstice_covers_another_plane"):
        interstice_frames.saved_interstices(
            tmp_path, saved(plane=np.zeros((4, 4), dtype=np.uint16))
        )


def test_an_out_directory_outside_data_is_an_argument_refusal(
    stage, tmp_path: Path
) -> None:
    dome, records = stage
    record = _saved_record(tmp_path, records, dome)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    with pytest.raises(ArgumentRefusal, match="private data directory"):
        interstice_frames.draw(tmp_path, "study", tmp_path / "out")
    with pytest.raises(ArgumentRefusal, match="no saved records"):
        interstice_frames.draw(
            tmp_path, "nobody", PROJECT / "data" / "pictures" / "_pytest" / "x"
        )


def test_the_drawer_writes_one_sheet_per_series_with_its_manifest(
    stage, tmp_path: Path
) -> None:
    """The impure edge, end to end: one image per series under data/, bound to the receipt."""
    dome, records = stage
    record = _saved_record(tmp_path, records, dome)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = interstice_frames.draw(tmp_path, "study", out)
        assert manifest["images"] == ["01-coronal-fs1-fat1.png"]
        assert manifest["image"] == "01-coronal-fs1-fat1.png"
        assert (out / "01-coronal-fs1-fat1.png").stat().st_size > 0
        assert (out / "manifest.json").exists()
        assert manifest["standings"] == list(ENTRY_STANDINGS)
        assert manifest["plane_standings"] == list(PLANE_STANDINGS)
        (series,) = manifest["series"]
        assert series["interstice"]["tiles_rc"] == [TILES_DOWN, TILES_ACROSS]
        panels = series["panels"]
        assert [p["standing"] for p in panels] == [
            "named",
            "named",
            "no_extent",
            "predecessor_absent",
        ]
        assert [p["plane_standing"] for p in panels] == [
            "selected",
            "walk",
            "tiles_alone",
            "tiles_alone",
        ]
        # The silence the stage made is drawn as that silence, and the readings as readings.
        assert [p["drawn"] for p in panels] == [
            "drawn",
            "drawn",
            "drawn",
            "predecessor_absent",
        ]
        assert panels[0]["extent_tiles"] == 24 and panels[2]["extent_tiles"] == 0
        assert panels[0]["fill_code"] == "above_below"
        assert panels[0]["walls"]["first"] == {
            "plate_layer_fill": TILE_PX,
            "plate_fill": 2 * TILE_PX,
            "unreadable": 2 * TILE_PX,
        }
        assert panels[0]["contents"][1] == {
            "index": 2,
            "position_code": "central",
            "side_code": "side_abstained",
        }
        assert len(panels[1]["contents"]) == 3
        assert set(manifest["legend"]["content_outline_by_position"]) == set(
            POSITION_CODES
        )
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_the_drawer_draws_the_extent_over_the_plane_saved_at_its_slice(
    stage, tmp_path: Path
) -> None:
    dome, records = stage
    record = _saved_record(tmp_path, records, dome, saved_planes=(4, 2))
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = interstice_frames.draw(tmp_path, "study", out)
        (series,) = manifest["series"]
        assert [p["plane_standing"] for p in series["panels"]] == [
            "selected",
            "saved",
            "saved",
            "tiles_alone",
        ]
        assert [p["drawn"] for p in series["panels"]] == [
            "drawn",
            "drawn",
            "drawn",
            "predecessor_absent",
        ]
        assert series["interstice"]["arrays"]["planes"]["shape"] == [
            2,
            PLANE_ROWS,
            PLANE_COLUMNS,
        ]
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_a_series_with_no_saved_interstice_still_gets_its_sheet_naming_the_silence(
    stage, tmp_path: Path
) -> None:
    dome, records = stage
    record = _saved_record(tmp_path, records, dome, with_interstice=False)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = interstice_frames.draw(tmp_path, "study", out)
        (series,) = manifest["series"]
        assert series["interstice"] is None and series["panels"] == []
        assert (out / series["image"]).stat().st_size > 0
    finally:
        shutil.rmtree(out, ignore_errors=True)
