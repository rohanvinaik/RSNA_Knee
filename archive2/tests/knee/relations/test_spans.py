"""Round 3, the spans and the envelope (the-funnel tasks 9.1 to 9.3), both signs.

The two orchestrations are called directly over hand-built upstream records (their producers are
other units' and not built yet): a span reaches both big objects outside every interstice and is
never the content of one; a body's side follows the laterality sign and abstains without it; the
envelope is the fluid-like body that touches an interstice, its pouch lies behind both big
objects' most posterior tile centres, and its neck is counted across whichever grid axis carries
posterior position; every silence and every refusal is named; arrays are frozen and no input is
written (every input here is read-only); the ledger names what was read and produced.

Then the picture: its two pure decisions, its arrangement, the drawer's reader against a
writer-shaped record (`spans_record` and `envelope_record` below are the reference shape the
route's writer saves), and the drawer end to end, under data/pictures/_pytest.
"""

from __future__ import annotations

import copy
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
from knee.lenses.digits import DIGIT_CODES
from knee.lenses.tiles import TileDigits
from knee.objects.selection import ObjectRecord, Selection, TerritoryFacts
from knee.objects.tile_dome import TileDome
from knee.pictures.spans import (
    PLANE_SOURCES,
    STANDINGS,
    ChosenSlice,
    plane_source,
    round_three_panels,
    standing,
)
from knee.relations.interstice import SIDE_CODES, InterstitialRecord
from knee.relations.spans import (
    ENVELOPE_CODES,
    POUCH_CODES,
    SPAN_CODES,
    SPANS_RECORD_CODES,
    Envelope,
    Span,
    Spans,
    read_envelope,
    read_spans,
)
from knee.study.series import Series, SeriesGeometry, walk_indices
from knee.study.tables import SeriesRow
from knee.telemetry import recording
from workbench.measure.object_analysis import array_table, squint_stack_record
from workbench.render import spans_frames
from workbench.render._out import PROJECT, ArgumentRefusal

#: The tile grid every hand-built record shares: 12 x 12 tiles of 2 mm, three slices.
ROWS = COLS = 12
TILE_MM = 2.0
TILE_PX = 4
SLICES = 3
AXIAL = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
WALKED = walk_indices(SLICES)
#: The border every hand-built record is read under (`knee.objects.tile_dome.BORDER_CODES`): the
#: selection, the dome and the interstices of a slice must agree on it, and the spans and the
#: envelope carry it on.
BORDER = "dark_on_both"

# --- hand-built upstream records ---------------------------------------------------------------


def _mask(*regions: tuple[int | slice, int | slice]) -> np.ndarray:
    """A (ROWS, COLS) bool mask with each (rows, columns) region set; a region is a slice or an int."""
    mask = np.zeros((ROWS, COLS), dtype=bool)
    for rows, columns in regions:
        mask[rows, columns] = True
    return mask


def _centres(kind: str) -> np.ndarray:
    """Tile centres, (ROWS, COLS, 3) LPS millimetres (+x left, +y posterior, +z superior).

    `coronal`: left along the columns, superior up the rows, posterior through the plane.
    `sagittal`: posterior along the columns (as on the real study's sagittal), superior up the rows.
    """
    rows, columns = np.meshgrid(np.arange(ROWS), np.arange(COLS), indexing="ij")
    centres = np.empty((ROWS, COLS, 3), dtype=np.float64)
    if kind == "coronal":
        centres[..., 0], centres[..., 1], centres[..., 2] = (
            TILE_MM * columns,
            -60.0,
            -TILE_MM * rows,
        )
    else:
        centres[..., 0], centres[..., 1], centres[..., 2] = (
            10.0,
            TILE_MM * columns,
            -TILE_MM * rows,
        )
    return centres


def _lay(array: np.ndarray, layout: str) -> np.ndarray:
    """The same tiles in another layout of the grid, their values travelling with them.

    `transposed`: rows carry what the columns did (as on the axial); `mirrored`: left to right.
    """
    if layout == "transposed":
        return np.swapaxes(array, 0, 1).copy()
    if layout == "mirrored":
        return np.flip(array, axis=1).copy()
    return array.copy()


def _frozen(array: np.ndarray) -> np.ndarray:
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class Scene:
    """One chosen slice's hand-built records, every array read-only so a write would raise."""

    centres: np.ndarray
    dome: TileDome
    selection: Selection
    interstices: tuple[InterstitialRecord, ...]
    conjunction: Conjunction
    digits: TileDigits


def _facts(index: int, labels: np.ndarray, centres: np.ndarray) -> TerritoryFacts:
    mask = labels == index
    points = centres[mask]
    centre = points.mean(axis=0)
    return TerritoryFacts(
        index=index,
        tiles=int(mask.sum()),
        centre_lps=centre,
        superior_mm=float(centre[2]),
        anterior_mm=float(-centre[1]),
        left_right_mm=float(centre[0]),
        superior_extent_mm=(float(points[:, 2].min()), float(points[:, 2].max())),
        anterior_face_mm=float((-points[:, 1]).max()),
        touches_leg_border=False,
        ringed=False,
    )


def _scene(
    kind: str,
    labels: np.ndarray,
    extents: tuple[np.ndarray, ...],
    *,
    roles: dict[int, str],
    plane_kind: str,
    dark: np.ndarray | None = None,
    above: np.ndarray | None = None,
    others: tuple[tuple[int, np.ndarray], ...] = (),
    layout: str = "plain",
    slice_index: int = 1,
    tilt: float = 0.0,
) -> Scene:
    base = _centres(kind)
    base[..., 1] += tilt * np.arange(ROWS)[:, None]
    centres = _lay(base, layout)
    laid = _lay(labels, layout).astype(np.int32)
    series = "recipient"
    objects = tuple(
        ObjectRecord(
            index=int(index),
            role_code=roles.get(int(index), "unselected"),
            facts=_facts(int(index), laid, centres),
            tiles=int((laid == index).sum()),
        )
        for index in sorted(set(laid.flat) - {0})
    )
    selection = Selection(
        series_uid=series,
        slice_index=slice_index,
        plane_kind=plane_kind,
        code="present",
        why="hand-built",
        pair_code="selected",
        objects=objects,
        candidate_codes=(),
        border=BORDER,
    )
    dome = TileDome(
        series_uid=series,
        slice_index=slice_index,
        code="present",
        why="hand-built",
        prominence_mm=8.0,
        obstacle=laid == 0,
        cleared=np.zeros((ROWS, COLS), dtype=bool),
        interior=laid != 0,
        height=np.zeros((ROWS, COLS)),
        peaks=np.zeros((0, 2), dtype=np.int64),
        peak_height_mm=np.zeros(0),
        labels=laid,
        border=BORDER,
    )
    interstices = tuple(
        InterstitialRecord(
            series_uid=series,
            slice_index=slice_index,
            first=1,
            second=2,
            code="present",
            why="hand-built",
            extent=_lay(extent, layout),
            first_wall_codes=np.zeros(0, dtype=np.uint8),
            second_wall_codes=np.zeros(0, dtype=np.uint8),
            fill_counts={},
            fill_code="fill_unread",
            contents=(),
            border=BORDER,
        )
        for extent in extents
    )
    pair_codes = np.full(
        (SLICES, ROWS, COLS), CONJUNCTION_CODES.index("at_at"), dtype=np.uint8
    )
    if dark is not None:
        pair_codes[slice_index][_lay(dark, layout)] = CONJUNCTION_CODES.index(
            "below_below"
        )
    conjunction = Conjunction(
        recipient_uid=series,
        partner_uid="partner",
        code="present",
        why="hand-built",
        codes=pair_codes,
        counts=tuple(
            int(np.count_nonzero(pair_codes == index))
            for index in range(len(CONJUNCTION_CODES))
        ),
    )
    digit_codes = np.full((SLICES, ROWS, COLS), DIGIT_CODES.index("at"), dtype=np.uint8)
    digit_values = np.zeros((SLICES, ROWS, COLS), dtype=np.int8)
    fills = [(value, mask) for value, mask in others]
    if above is not None:
        fills.append((1, above))
    names = {-1: "below", 1: "above", 2: "place_unread"}
    for value, mask in fills:
        digit_values[slice_index][_lay(mask, layout)] = value
        digit_codes[slice_index][_lay(mask, layout)] = DIGIT_CODES.index(names[value])
    digits = TileDigits(
        series_uid=series,
        code="present",
        why="hand-built",
        low_edge=0.0,
        high_edge=1.0,
        population_count=int(digit_values.size),
        minimum_population=8,
        codes=digit_codes,
        digits=digit_values,
        counts=tuple(
            int(np.count_nonzero(digit_codes == index))
            for index in range(len(DIGIT_CODES))
        ),
    )
    for array in (
        centres,
        laid,
        dome.obstacle,
        dome.cleared,
        dome.interior,
        dome.height,
        dome.peaks,
        dome.peak_height_mm,
        pair_codes,
        digit_codes,
        digit_values,
        *(item.extent for item in interstices),
        *(record.facts.centre_lps for record in objects),
    ):
        _frozen(array)
    return Scene(centres, dome, selection, interstices, conjunction, digits)


def _coronal(
    *,
    dark: np.ndarray | None = None,
    roles: dict[int, str] | None = None,
    slice_index: int = 1,
) -> Scene:
    """Two big objects (rows 0-4 and 7-11, columns 3-8) with the gap between them as the interstice.

    Five dark bodies: C at (0, 9) touches only the upper object; A (column 2) and E (column 9),
    rows 3-8, each reach both and lie outside the gap; B (the 2 x 2 at rows 5-6, columns 5-6) lies
    inside the gap and touches both; D at (11, 11) touches nothing.
    """
    labels = np.zeros((ROWS, COLS), dtype=np.int32)
    labels[0:5, 3:9] = 1
    labels[7:12, 3:9] = 2
    extent = _mask((slice(5, 7), slice(3, 9)))
    default = _mask(
        (0, 9),
        (slice(3, 9), 2),
        (slice(3, 9), 9),
        (slice(5, 7), slice(5, 7)),
        (11, 11),
    )
    return _scene(
        "coronal",
        labels,
        (extent,),
        roles={1: "superior_big", 2: "inferior_big"} if roles is None else roles,
        plane_kind="Coronal",
        dark=default if dark is None else dark,
        slice_index=slice_index,
    )


def _sagittal(
    *,
    above: np.ndarray | None = None,
    extents: tuple[np.ndarray, ...] | None = None,
    roles: dict[int, str] | None = None,
    layout: str = "plain",
    plane_kind: str = "Sagittal",
    slice_index: int = 1,
    tilt: float = 0.0,
) -> Scene:
    """Two big objects (rows 0-4 and 7-11, columns 2-6; posterior is +column) round a gap.

    The default fluid-like body fills the gap (rows 5-6, columns 2-6), runs on through ONE tile
    at (5, 7) and widens into a body at rows 4-7, columns 8-9: the envelope is 19 tiles, the
    pouch (centres posterior of column 6) is 9 and the neck is the one tile. Two more tiles at
    (0, 11) and (1, 11) touch nothing. Tiles whose digit is below, or silent, sit beside the gap.
    """
    labels = np.zeros((ROWS, COLS), dtype=np.int32)
    labels[0:5, 2:7] = 1
    labels[7:12, 2:7] = 2
    gap = _mask((slice(5, 7), slice(2, 7)))
    default = _mask(
        (slice(5, 7), slice(2, 7)),
        (5, 7),
        (slice(4, 8), slice(8, 10)),
        (0, 11),
        (1, 11),
    )
    return _scene(
        "sagittal",
        labels,
        (gap,) if extents is None else extents,
        roles={1: "superior_big", 2: "inferior_big"} if roles is None else roles,
        plane_kind=plane_kind,
        above=default if above is None else above,
        others=((-1, _mask((4, slice(2, 4)))), (2, _mask((7, 2)))),
        layout=layout,
        slice_index=slice_index,
        tilt=tilt,
    )


def _at(reading: Spans, row: int, column: int) -> Span:
    """The one body that holds the tile at (row, column)."""
    (found,) = [body for body in reading.spans if body.tiles[row, column]]
    return found


# --- 9.1 the spans -----------------------------------------------------------------------------


def test_a_dark_body_reaching_both_big_objects_outside_every_interstice_is_a_span() -> (
    None
):
    s = _coronal()
    reading = read_spans(
        s.conjunction, s.selection, s.interstices, s.dome, s.centres, "left"
    )
    assert (reading.code, reading.slice_index, reading.series_uid) == (
        "present",
        1,
        "recipient",
    )
    assert _at(reading, 5, 2).code == "span"
    assert _at(reading, 5, 9).code == "span"
    assert sorted(body.code for body in reading.spans) == [
        "inside_interstice",
        "span",
        "span",
        "touches_none",
        "touches_one",
    ]


def test_a_body_inside_an_interstice_is_its_content_and_never_a_span() -> None:
    s = _coronal()
    inside = read_spans(
        s.conjunction, s.selection, s.interstices, s.dome, s.centres, "left"
    )
    # It touches both big objects: only the extent keeps it from being a span.
    assert _at(inside, 5, 5).code == "inside_interstice"
    # With no interstice handed over the stage reads nothing: without a space, a body inside one
    # cannot be told from a span, so no body is called a span and the silence is named.
    outside = read_spans(s.conjunction, s.selection, (), s.dome, s.centres, "left")
    assert outside.code == "predecessor_absent" and outside.spans == ()
    assert "no interstice is present among the 0" in outside.why


def test_a_body_with_any_tile_in_an_extent_is_inside_even_where_it_reaches_out() -> (
    None
):
    crossing = _mask((5, 2), (5, 3))  # (5, 3) lies in the gap, (5, 2) does not
    s = _coronal(dark=crossing)
    reading = read_spans(
        s.conjunction, s.selection, s.interstices, s.dome, s.centres, "left"
    )
    assert [body.code for body in reading.spans] == ["inside_interstice"]
    assert reading.code == "present"  # a dark tile lies outside every extent


def test_a_body_reaching_one_object_or_none_is_named_so() -> None:
    s = _coronal()
    reading = read_spans(
        s.conjunction, s.selection, s.interstices, s.dome, s.centres, "left"
    )
    assert _at(reading, 0, 9).code == "touches_one"
    assert _at(reading, 11, 11).code == "touches_none"


def test_only_a_present_interstice_contributes_an_extent() -> None:
    s = _coronal()
    # The first would swallow the body in column 9 if its extent counted; the second holds no
    # grid at all. Neither is present.
    quiet = replace(
        s.interstices[0],
        code="no_extent",
        extent=_frozen(_mask((slice(3, 9), 9))),
    )
    unread = replace(
        s.interstices[0],
        code="predecessor_absent",
        extent=_frozen(np.zeros((0, 0), dtype=bool)),
    )
    # With no present interstice among those handed over the stage reads nothing: without a
    # space, a body inside one cannot be told from a span.
    none = read_spans(
        s.conjunction, s.selection, (quiet, unread), s.dome, s.centres, "left"
    )
    assert none.code == "predecessor_absent" and none.spans == ()
    assert "no interstice is present among the 2" in none.why
    # Beside a present one they add nothing: the gap's extent alone makes the 2 x 2 body its
    # content, and the body in column 9 lies in no present extent.
    reading = read_spans(
        s.conjunction,
        s.selection,
        (s.interstices[0], quiet, unread),
        s.dome,
        s.centres,
        "left",
    )
    assert _at(reading, 5, 5).code == "inside_interstice"
    assert _at(reading, 5, 9).code == "span"
    assert "1 present interstice" in reading.why


def test_the_extents_of_every_present_interstice_count_together() -> None:
    s = _coronal()
    beside = replace(
        s.interstices[0], extent=_frozen(_mask((slice(3, 9), 2))), first=1, second=2
    )
    reading = read_spans(
        s.conjunction,
        s.selection,
        (s.interstices[0], beside),
        s.dome,
        s.centres,
        "left",
    )
    # Column 2 now lies in the second interstice's extent as the 2 x 2 does in the first's.
    assert _at(reading, 5, 2).code == "inside_interstice"
    assert _at(reading, 5, 5).code == "inside_interstice"
    assert _at(reading, 5, 9).code == "span"
    assert "2 present interstices" in reading.why


def test_bodies_are_four_connected_never_joined_at_a_corner() -> None:
    apart = _coronal(dark=_mask((2, 0), (3, 1), (8, 0), (8, 1)))
    reading = read_spans(
        apart.conjunction,
        apart.selection,
        apart.interstices,
        apart.dome,
        apart.centres,
        "left",
    )
    assert (
        len(reading.spans) == 3
    )  # the two diagonal tiles, and the one pair side by side
    assert _at(reading, 8, 0) is _at(reading, 8, 1)
    assert _at(reading, 2, 0) is not _at(reading, 3, 1)


def test_bodies_are_indexed_from_one_in_the_scan_order_of_their_first_tile() -> None:
    s = _coronal()
    reading = read_spans(
        s.conjunction, s.selection, s.interstices, s.dome, s.centres, "left"
    )
    assert [body.index for body in reading.spans] == [1, 2, 3, 4, 5]
    firsts = [tuple(np.argwhere(body.tiles)[0]) for body in reading.spans]
    assert firsts == sorted(firsts)


def test_the_side_follows_the_sign_and_the_pairs_centre() -> None:
    s = _coronal()
    left = read_spans(
        s.conjunction, s.selection, s.interstices, s.dome, s.centres, "left"
    )
    right = read_spans(
        s.conjunction, s.selection, s.interstices, s.dome, s.centres, "right"
    )
    # Column 2 lies at x 4 mm and column 9 at 18 mm; the pair's centre is at x 11 mm.
    assert (_at(left, 5, 2).side_code, _at(left, 5, 9).side_code) == (
        "medial",
        "lateral",
    )
    assert (_at(right, 5, 2).side_code, _at(right, 5, 9).side_code) == (
        "lateral",
        "medial",
    )
    # The 2 x 2 body sits exactly on the pair's centre: on neither side.
    assert _at(left, 5, 5).side_code == "side_abstained"
    assert _at(right, 5, 5).side_code == "side_abstained"


def test_the_pairs_centre_is_the_midpoint_of_both_big_objects_centres() -> None:
    labels = np.zeros((ROWS, COLS), dtype=np.int32)
    labels[0:5, 3:9] = 1  # centre at x 11 mm
    labels[7:12, 4:10] = 2  # one tile (2 mm) further left: centre at x 13 mm
    s = _scene(
        "coronal",
        labels,
        (_mask((slice(5, 7), slice(3, 5))),),
        roles={1: "superior_big", 2: "inferior_big"},
        plane_kind="Coronal",
        # Two bodies across the gap rows, each reaching both objects and outside the gap's
        # extent (columns 3-4): one at x 12 mm (column 6), one at x 16 mm (column 8).
        dark=_mask((slice(5, 7), 6), (slice(5, 7), 8)),
    )
    reading = read_spans(
        s.conjunction, s.selection, s.interstices, s.dome, s.centres, "left"
    )
    # The midpoint is x 12 mm: a body exactly on it is on neither side, and one 4 mm beyond it
    # lies on the lateral side of a left-lateral knee.
    assert _at(reading, 5, 6).code == "span"
    assert _at(reading, 5, 6).side_code == "side_abstained"
    assert _at(reading, 5, 8).code == "span"
    assert _at(reading, 5, 8).side_code == "lateral"


def test_without_a_sign_every_side_abstains_and_a_wrong_sign_is_refused_not_guessed() -> (
    None
):
    s = _coronal()
    quiet = read_spans(
        s.conjunction, s.selection, s.interstices, s.dome, s.centres, "side_abstained"
    )
    assert {body.side_code for body in quiet.spans} == {"side_abstained"}
    wrong = read_spans(
        s.conjunction, s.selection, s.interstices, s.dome, s.centres, "lateral"
    )
    assert {body.side_code for body in wrong.spans} == {"invalid_measurement"}
    absent = read_spans(
        s.conjunction,
        s.selection,
        s.interstices,
        s.dome,
        s.centres,
        None,  # ty: ignore[invalid-argument-type]
    )
    assert {body.side_code for body in absent.spans} == {"invalid_measurement"}


def test_with_no_big_pair_every_body_touches_none_and_no_side_is_guessed() -> None:
    for roles in ({1: "superior_big"}, {1: "central_big", 2: "anterior_small"}, {}):
        s = _coronal(roles=roles)
        reading = read_spans(
            s.conjunction, s.selection, s.interstices, s.dome, s.centres, "left"
        )
        assert sorted(body.code for body in reading.spans) == [
            "inside_interstice",
            "touches_none",
            "touches_none",
            "touches_none",
            "touches_none",
        ]
        assert {body.side_code for body in reading.spans} == {"side_abstained"}
        assert "names no superior_big and inferior_big pair" in reading.why


def test_no_dark_tile_outside_the_spaces_is_no_candidate_and_the_bodies_inside_are_kept() -> (
    None
):
    none = _coronal(dark=_mask())
    empty = read_spans(
        none.conjunction,
        none.selection,
        none.interstices,
        none.dome,
        none.centres,
        "left",
    )
    assert (empty.code, empty.spans) == ("no_candidate", ())
    inside = _coronal(dark=_mask((slice(5, 7), slice(5, 7))))
    kept = read_spans(
        inside.conjunction,
        inside.selection,
        inside.interstices,
        inside.dome,
        inside.centres,
        "left",
    )
    # Every dark tile lies in the gap: no candidate for a span, and nothing is dropped.
    assert kept.code == "no_candidate"
    assert [body.code for body in kept.spans] == ["inside_interstice"]
    # The same tiles with no interstice handed over are no candidate for the stage to name: it
    # reads nothing, because without a space a body inside one cannot be told from a span.
    open_ = read_spans(
        inside.conjunction, inside.selection, (), inside.dome, inside.centres, "left"
    )
    assert open_.code == "predecessor_absent" and open_.spans == ()


def test_a_predecessor_that_is_not_there_gives_predecessor_absent_and_says_which() -> (
    None
):
    s = _coronal()
    cases = (
        (
            read_spans(None, s.selection, s.interstices, s.dome, s.centres, "left"),
            "no conjunction",
        ),
        (
            read_spans(
                replace(s.conjunction, code="predecessor_absent"),
                s.selection,
                s.interstices,
                s.dome,
                s.centres,
                "left",
            ),
            "conjunction is predecessor_absent",
        ),
        (
            read_spans(
                s.conjunction,
                replace(s.selection, code="no_territory", objects=()),
                s.interstices,
                s.dome,
                s.centres,
                "left",
            ),
            "selection is no_territory",
        ),
        (
            read_spans(
                s.conjunction,
                s.selection,
                s.interstices,
                replace(s.dome, code="no_interior"),
                s.centres,
                "left",
            ),
            "dome is no_interior",
        ),
    )
    for reading, said in cases:
        assert reading.code == "predecessor_absent"
        assert reading.spans == ()
        assert said in reading.why


def test_the_spans_arrays_are_frozen_and_no_input_is_written() -> None:
    s = _coronal()
    before = s.conjunction.codes.copy()
    reading = read_spans(
        s.conjunction, s.selection, s.interstices, s.dome, s.centres, "left"
    )
    for body in reading.spans:
        assert not body.tiles.flags.writeable
        assert not body.centre_lps.flags.writeable
        assert body.tiles.dtype == np.bool_ and body.tiles.shape == (ROWS, COLS)
        assert body.centre_lps.dtype == np.float64 and body.centre_lps.shape == (3,)
    # The inputs are read-only, so any write would have raised; nothing changed either.
    assert np.array_equal(s.conjunction.codes, before)
    assert not s.conjunction.codes.flags.writeable and not s.centres.flags.writeable


def test_a_body_centre_is_the_mean_of_its_tiles_centres_and_a_blind_body_is_refused_a_side() -> (
    None
):
    s = _coronal()
    reading = read_spans(
        s.conjunction, s.selection, s.interstices, s.dome, s.centres, "left"
    )
    body = _at(reading, 5, 2)  # column 2, rows 3-8
    assert np.allclose(body.centre_lps, [4.0, -60.0, -11.0])
    blind = s.centres.copy()
    blind[11, 11] = np.nan  # the lone dark tile of body D has no centre
    refused = read_spans(
        s.conjunction, s.selection, s.interstices, s.dome, blind, "left"
    )
    lone = _at(refused, 11, 11)
    assert np.isnan(lone.centre_lps).all()
    assert lone.side_code == "invalid_measurement"
    assert lone.code == "touches_none"


def test_the_spans_ledger_names_what_was_read_and_what_was_produced() -> None:
    s = _coronal()
    with recording() as run_ledger:
        reading = read_spans(
            s.conjunction, s.selection, s.interstices, s.dome, s.centres, "left"
        )
    events = {event.name: dict(event.counts) for event in run_ledger.events()}
    assert list(events) == [
        "conjunction.consumed_by.spans",
        "selection.consumed_by.spans",
        "interstice.consumed_by.spans",
        "tile_dome.consumed_by.spans",
        "spans.produced",
    ]
    assert events["conjunction.consumed_by.spans"] == {"conjunction": 1}
    assert events["selection.consumed_by.spans"] == {"selection": 1}
    assert events["interstice.consumed_by.spans"] == {"interstices": 1}
    assert events["tile_dome.consumed_by.spans"] == {"dome": 1}
    assert events["spans.produced"] == {
        "spans": sum(1 for body in reading.spans if body.code == "span")
    }
    assert events["spans.produced"] == {"spans": 2}


def test_a_conjunction_that_is_none_is_never_named_and_an_absent_one_counts_zero() -> (
    None
):
    s = _coronal()
    with recording() as run_ledger:
        read_spans(None, s.selection, s.interstices, s.dome, s.centres, "left")
        read_spans(
            replace(s.conjunction, code="predecessor_absent"),
            s.selection,
            (),
            s.dome,
            s.centres,
            "left",
        )
    named = [
        (event.name, dict(event.counts))
        for event in run_ledger.events()
        if event.name.startswith("conjunction.")
    ]
    assert named == [("conjunction.consumed_by.spans", {"conjunction": 0})]
    produced = [
        dict(event.counts)
        for event in run_ledger.events()
        if event.name == "spans.produced"
    ]
    assert produced == [{"spans": 0}, {"spans": 0}]


def test_records_that_cannot_be_one_slices_are_refused_by_name_before_anything_is_produced() -> (
    None
):
    s = _coronal()
    with (
        recording() as run_ledger,
        pytest.raises(ValueError, match="spans_inputs_disagree"),
    ):
        read_spans(
            s.conjunction,
            s.selection,
            s.interstices,
            replace(s.dome, slice_index=2),
            s.centres,
            "left",
        )
    names = [event.name for event in run_ledger.events()]
    assert "selection.consumed_by.spans" in names
    assert "spans.produced" not in names

    refusals = {
        "an empty tile grid": (
            replace(
                s.conjunction, codes=_frozen(np.zeros((SLICES, 0, 0), dtype=np.uint8))
            ),
            s.selection,
            s.interstices,
            replace(s.dome, labels=_frozen(np.zeros((0, 0), dtype=np.int32))),
            _frozen(np.zeros((0, 0, 3))),
        ),
        "another grid": (
            replace(
                s.conjunction, codes=_frozen(np.zeros((SLICES, 10, 10), dtype=np.uint8))
            ),
            s.selection,
            s.interstices,
            s.dome,
            s.centres,
        ),
        # Every record agrees on slice 3 of a conjunction that holds slices 0 to 2: only the
        # conjunction's own range can refuse it.
        "a slice the conjunction lacks": (
            s.conjunction,
            replace(s.selection, slice_index=SLICES),
            (replace(s.interstices[0], slice_index=SLICES),),
            replace(s.dome, slice_index=SLICES),
            s.centres,
        ),
        "centres of another grid": (
            s.conjunction,
            s.selection,
            s.interstices,
            s.dome,
            s.centres[:10],
        ),
        "another series": (
            replace(s.conjunction, recipient_uid="another"),
            s.selection,
            s.interstices,
            s.dome,
            s.centres,
        ),
        "a dome of another series": (
            s.conjunction,
            s.selection,
            s.interstices,
            replace(s.dome, series_uid="another"),
            s.centres,
        ),
        "an interstice of another series": (
            s.conjunction,
            s.selection,
            (replace(s.interstices[0], series_uid="another"),),
            s.dome,
            s.centres,
        ),
        "an interstice of another slice": (
            s.conjunction,
            s.selection,
            (replace(s.interstices[0], slice_index=0),),
            s.dome,
            s.centres,
        ),
        "an extent of another grid": (
            s.conjunction,
            s.selection,
            (replace(s.interstices[0], extent=_frozen(np.zeros((5, 5), dtype=bool))),),
            s.dome,
            s.centres,
        ),
    }
    for what, (conjunction, selection, interstices, dome, centres) in refusals.items():
        with pytest.raises(ValueError, match="spans_inputs_disagree") as caught:
            read_spans(conjunction, selection, interstices, dome, centres, "left")
        assert caught.value.__notes__, what


# --- 9.2 the envelope --------------------------------------------------------------------------

#: What the default sagittal scene's envelope, pouch and neck are, in the plain layout.
ENVELOPE_TILES = _mask((slice(5, 7), slice(2, 7)), (5, 7), (slice(4, 8), slice(8, 10)))
POUCH_TILES = _mask((5, 7), (slice(4, 8), slice(8, 10)))


@pytest.mark.parametrize("layout", ["plain", "transposed", "mirrored"])
def test_the_envelope_is_the_fluid_like_body_touching_an_interstice_with_its_pouch_and_neck(
    layout: str,
) -> None:
    s = _sagittal(layout=layout)
    reading = read_envelope(
        s.digits, s.selection, s.interstices, s.centres, dome=s.dome
    )
    assert reading.code == "present"
    assert (reading.series_uid, reading.slice_index) == ("recipient", 1)
    assert np.array_equal(reading.tiles, _lay(ENVELOPE_TILES, layout))
    # The pouch is what lies posterior of both big objects' most posterior tile centre; the tiles
    # AT that centre (column 6 in the plain layout) are not behind it.
    assert np.array_equal(reading.pouch_tiles, _lay(POUCH_TILES, layout))
    assert (reading.pouch_count, reading.neck_tiles) == (9, 1)
    assert reading.pouch_code == "pouch"
    assert "21 above tiles in 2 components, 1 four-adjacent" in reading.why
    assert "kept beside the envelope as unjoined: 1 component;" in reading.why
    assert "behind it, 9 tiles of the envelope; neck, 1 tile" in reading.why


def test_the_neck_is_counted_across_the_axis_that_carries_posterior_position() -> None:
    plain = _sagittal()
    tilted = _sagittal(
        tilt=0.3
    )  # y also drifts 0.3 mm a row: the columns still carry it
    for scene in (plain, tilted):
        reading = read_envelope(
            scene.digits,
            scene.selection,
            scene.interstices,
            scene.centres,
            dome=scene.dome,
        )
        assert (reading.pouch_count, reading.neck_tiles) == (9, 1)
    # On the transposed grid the same millimetres run along the rows, and the answer is the same.
    axial = _sagittal(layout="transposed", tilt=0.3)
    along_rows = read_envelope(
        axial.digits, axial.selection, axial.interstices, axial.centres, dome=axial.dome
    )
    assert (along_rows.pouch_count, along_rows.neck_tiles) == (9, 1)


@pytest.mark.parametrize("layout", ["plain", "transposed", "mirrored"])
def test_the_neck_may_lie_at_either_end_of_the_range(layout: str) -> None:
    # The rest narrows to ONE tile at its most posterior line (column 6) before a wider pouch.
    gap = _mask((slice(5, 7), slice(2, 6)))
    above = gap | _mask((5, 6), (slice(5, 7), slice(7, 9)))
    s = _sagittal(above=above, extents=(gap,), layout=layout)
    reading = read_envelope(
        s.digits, s.selection, s.interstices, s.centres, dome=s.dome
    )
    assert reading.pouch_count == 4
    assert reading.neck_tiles == 1


def test_a_pouch_that_the_rest_does_not_reach_has_a_neck_of_zero() -> None:
    gap = _mask((slice(5, 7), slice(2, 7)))
    far = _mask((slice(5, 7), slice(9, 11)))
    s = _sagittal(above=gap | far, extents=(gap, far))
    reading = read_envelope(
        s.digits, s.selection, s.interstices, s.centres, dome=s.dome
    )
    # Two bodies, each touching its own interstice, with two columns holding no envelope between.
    assert np.array_equal(reading.tiles, gap | far)
    assert (reading.pouch_count, reading.neck_tiles) == (4, 0)
    assert reading.pouch_code == "pouch"


def test_an_envelope_wholly_behind_the_big_objects_or_wholly_before_them_has_no_neck() -> (
    None
):
    behind = _mask((slice(5, 7), slice(8, 10)))
    s = _sagittal(above=behind, extents=(behind,))
    whole = read_envelope(s.digits, s.selection, s.interstices, s.centres, dome=s.dome)
    assert (whole.pouch_count, whole.neck_tiles, whole.pouch_code) == (4, 0, "pouch")
    gap = _mask((slice(5, 7), slice(2, 7)))
    t = _sagittal(above=gap, extents=(gap,))
    before = read_envelope(t.digits, t.selection, t.interstices, t.centres, dome=t.dome)
    assert (before.pouch_count, before.neck_tiles, before.pouch_code) == (
        0,
        0,
        "no_pouch",
    )
    assert before.code == "present" and before.tiles.sum() == 10


def test_a_component_not_four_adjacent_to_an_extent_is_left_out_and_counted() -> None:
    s = _sagittal()
    reading = read_envelope(
        s.digits, s.selection, s.interstices, s.centres, dome=s.dome
    )
    assert not reading.tiles[0, 11] and not reading.tiles[1, 11]
    # They are kept beside the envelope as unjoined, never inside it.
    assert np.array_equal(reading.unjoined, _mask((0, 11), (1, 11)))
    # The tiles beside the gap whose digit is below or silent are not above, so not envelope.
    assert not reading.tiles[4, 2] and not reading.tiles[7, 2]
    far = _sagittal(above=_mask((0, 11), (1, 11)))
    nothing = read_envelope(
        far.digits, far.selection, far.interstices, far.centres, dome=far.dome
    )
    assert nothing.code == "no_fluid_like"
    assert nothing.tiles.sum() == 0 and nothing.pouch_count == 0
    assert np.array_equal(nothing.unjoined, _mask((0, 11), (1, 11)))
    assert "no above tile touches an interstice" in nothing.why


def test_adjacency_counts_overlap_so_a_fluid_like_tile_inside_the_gap_touches_it() -> (
    None
):
    inside = _sagittal(above=_mask((5, 3)))
    reading = read_envelope(
        inside.digits,
        inside.selection,
        inside.interstices,
        inside.centres,
        dome=inside.dome,
    )
    assert reading.code == "present"
    assert np.array_equal(reading.tiles, _mask((5, 3)))
    beside = _sagittal(above=_mask((4, 3)))  # next to the gap, above it, in no extent
    touching = read_envelope(
        beside.digits,
        beside.selection,
        beside.interstices,
        beside.centres,
        dome=beside.dome,
    )
    assert touching.code == "present"
    assert np.array_equal(touching.tiles, _mask((4, 3)))
    away = _sagittal(above=_mask((3, 3)))
    apart = read_envelope(
        away.digits, away.selection, away.interstices, away.centres, dome=away.dome
    )
    assert apart.code == "no_fluid_like"


def test_where_posterior_runs_through_the_plane_nothing_lies_behind_the_big_objects() -> (
    None
):
    # A coronal grid with no tilt: every tile centre has the same y, so there is no axis that
    # carries it and no tile whose y exceeds the big objects'. No pouch, and no neck to count.
    labels = np.zeros((ROWS, COLS), dtype=np.int32)
    labels[0:5, 3:9] = 1
    labels[7:12, 3:9] = 2
    gap = _mask((slice(5, 7), slice(3, 9)))
    s = _scene(
        "coronal",
        labels,
        (gap,),
        roles={1: "superior_big", 2: "inferior_big"},
        plane_kind="Coronal",
        above=gap | _mask((5, 9), (5, 10)),
    )
    reading = read_envelope(
        s.digits, s.selection, s.interstices, s.centres, dome=s.dome
    )
    assert reading.code == "present" and reading.tiles.sum() == 14
    assert (reading.pouch_count, reading.neck_tiles) == (0, 0)
    assert reading.pouch_code == "no_pouch"


def test_a_rest_with_no_known_posterior_position_cannot_be_ordered_so_its_neck_is_zero() -> (
    None
):
    near = _mask(
        (5, 0), (5, 1)
    )  # the rest: two tiles, in columns that have no centre at all
    gap = _mask((slice(5, 7), slice(8, 10)))  # the pouch, behind both big objects
    s = _sagittal(above=near | gap, extents=(_mask((slice(5, 7), slice(0, 2))), gap))
    blind = s.centres.copy()
    blind[:, 0:2] = np.nan
    reading = read_envelope(s.digits, s.selection, s.interstices, blind, dome=s.dome)
    assert reading.tiles[5, 0] and reading.tiles[5, 1]
    assert reading.pouch_count == 4
    # The lines the rest lies on have no mean y, so no line can be its most posterior one.
    assert reading.neck_tiles == 0


def test_a_blind_tile_is_envelope_but_never_behind_the_big_objects() -> None:
    s = _sagittal()
    blind = s.centres.copy()
    blind[5, 7] = np.nan  # the one-tile neck has no centre
    reading = read_envelope(s.digits, s.selection, s.interstices, blind, dome=s.dome)
    # It joins the body that touches the gap, so it is envelope; it has no y, so it is not behind.
    assert reading.tiles[5, 7] and not reading.pouch_tiles[5, 7]
    assert (reading.pouch_count, reading.neck_tiles) == (8, 1)
    assert reading.pouch_code == "pouch"


def test_a_tile_exactly_at_the_big_objects_posterior_centre_is_not_behind_it() -> None:
    at_the_face = _mask(
        (5, 6), (5, 7)
    )  # column 6 is the objects' most posterior centre
    s = _sagittal(above=at_the_face, extents=(_mask((5, 6)),))
    reading = read_envelope(
        s.digits, s.selection, s.interstices, s.centres, dome=s.dome
    )
    assert np.array_equal(reading.pouch_tiles, _mask((5, 7)))
    assert reading.neck_tiles == 1


def test_with_no_big_pair_there_is_no_pouch_with_or_without_a_dome() -> None:
    roles = {1: "central_big", 2: "anterior_small"}
    s = _sagittal(roles=roles)
    without = read_envelope(s.digits, s.selection, s.interstices, s.centres)
    with_dome = read_envelope(
        s.digits, s.selection, s.interstices, s.centres, dome=s.dome
    )
    for reading in (without, with_dome):
        assert reading.code == "present" and reading.tiles.sum() == 19
        assert (reading.pouch_count, reading.neck_tiles) == (0, 0)
        assert reading.pouch_code == "no_pouch"
        assert "no pouch is read" in reading.why


def test_a_big_pair_without_the_dome_is_refused_by_name_never_answered_no_pouch() -> (
    None
):
    s = _sagittal()
    with pytest.raises(ValueError, match="envelope_pouch_needs_the_dome") as caught:
        read_envelope(s.digits, s.selection, s.interstices, s.centres)
    assert caught.value.__notes__
    # Nothing was read there, so the silence is still the silence it is.
    absent = read_envelope(
        replace(s.digits, code="predecessor_absent"),
        s.selection,
        s.interstices,
        s.centres,
    )
    assert absent.code == "predecessor_absent"


def test_a_predecessor_that_is_not_there_gives_predecessor_absent_and_the_grid_of_nothing() -> (
    None
):
    s = _sagittal()
    gap = s.interstices[0]
    cases = (
        (
            read_envelope(
                replace(s.digits, code="no_edges"),
                s.selection,
                s.interstices,
                s.centres,
                dome=s.dome,
            ),
            "tile digits are no_edges",
        ),
        (
            read_envelope(
                s.digits,
                replace(s.selection, code="no_territory", objects=()),
                s.interstices,
                s.centres,
            ),
            "selection is no_territory",
        ),
        (
            read_envelope(s.digits, s.selection, (), s.centres, dome=s.dome),
            "no interstice is present among the 0",
        ),
        (
            read_envelope(
                s.digits,
                s.selection,
                (replace(gap, code="no_extent"),),
                s.centres,
                dome=s.dome,
            ),
            "no interstice is present among the 1",
        ),
        (
            read_envelope(
                s.digits,
                s.selection,
                (replace(gap, code="predecessor_absent"),),
                s.centres,
                dome=s.dome,
            ),
            "no interstice is present among the 1",
        ),
    )
    for reading, said in cases:
        assert reading.code == "predecessor_absent"
        assert said in reading.why
        assert reading.tiles.shape == (ROWS, COLS) and not reading.tiles.any()
        assert reading.pouch_tiles.shape == (ROWS, COLS)
        assert (reading.pouch_count, reading.neck_tiles) == (0, 0)


def test_only_digits_of_plus_one_make_the_envelope() -> None:
    s = _sagittal()
    values = np.asarray(s.digits.digits)
    assert (values == -1).any() and (values == 2).any() and (values == 0).any()
    reading = read_envelope(
        s.digits, s.selection, s.interstices, s.centres, dome=s.dome
    )
    assert reading.tiles.sum() == int(((values[1] == 1) & ENVELOPE_TILES).sum())


def test_a_coronal_slice_says_that_posterior_runs_through_its_plane() -> None:
    coronal = _sagittal(plane_kind="Coronal")
    sagittal = _sagittal(plane_kind="Sagittal")
    said = read_envelope(
        coronal.digits,
        coronal.selection,
        coronal.interstices,
        coronal.centres,
        dome=coronal.dome,
    )
    quiet = read_envelope(
        sagittal.digits,
        sagittal.selection,
        sagittal.interstices,
        sagittal.centres,
        dome=sagittal.dome,
    )
    assert "Coronal slice" in said.why and "Coronal" not in quiet.why
    assert (said.pouch_count, said.neck_tiles) == (quiet.pouch_count, quiet.neck_tiles)


def test_the_envelope_arrays_are_frozen_and_no_input_is_written() -> None:
    s = _sagittal()
    before = np.asarray(s.digits.digits).copy()
    reading = read_envelope(
        s.digits, s.selection, s.interstices, s.centres, dome=s.dome
    )
    for array in (reading.tiles, reading.pouch_tiles, reading.unjoined):
        assert not array.flags.writeable
        assert array.dtype == np.bool_ and array.shape == (ROWS, COLS)
    assert np.array_equal(s.digits.digits, before)
    assert not np.asarray(s.digits.digits).flags.writeable


def test_the_envelope_ledger_names_what_was_read_and_what_was_produced() -> None:
    s = _sagittal()
    with recording() as run_ledger:
        read_envelope(s.digits, s.selection, s.interstices, s.centres, dome=s.dome)
    events = {event.name: dict(event.counts) for event in run_ledger.events()}
    assert list(events) == [
        "tile_digits.consumed_by.envelope",
        "selection.consumed_by.envelope",
        "interstice.consumed_by.envelope",
        "tile_dome.consumed_by.envelope",
        "envelope.produced",
    ]
    assert events["tile_digits.consumed_by.envelope"] == {"digits": 1}
    assert events["interstice.consumed_by.envelope"] == {"interstices": 1}
    assert events["tile_dome.consumed_by.envelope"] == {"dome": 1}
    assert events["envelope.produced"] == {"tiles": 19}
    unpaired = _sagittal(roles={})
    with recording() as run_ledger:
        read_envelope(
            unpaired.digits, unpaired.selection, unpaired.interstices, unpaired.centres
        )
    # No dome was handed over, so none is named.
    assert not [
        event.name
        for event in run_ledger.events()
        if event.name.startswith("tile_dome.")
    ]


def test_records_that_cannot_be_one_slices_are_refused_by_name_before_the_envelope_is_produced() -> (
    None
):
    s = _sagittal()
    with (
        recording() as run_ledger,
        pytest.raises(ValueError, match="envelope_inputs_disagree"),
    ):
        read_envelope(
            s.digits,
            s.selection,
            s.interstices,
            s.centres,
            dome=replace(s.dome, slice_index=2),
        )
    assert "envelope.produced" not in [event.name for event in run_ledger.events()]
    emptied = replace(s.dome, labels=_frozen(np.zeros((ROWS, COLS), dtype=np.int32)))
    refusals = {
        "a dome without the big territories": {"dome": emptied},
        "a dome that is not present": {"dome": replace(s.dome, code="no_interior")},
        "centres of another grid": {"centres": s.centres[:10]},
        "centres that are not a tile grid": {"centres": s.centres[..., :2]},
        "a dome of another series": {"dome": replace(s.dome, series_uid="x")},
        "an interstice of another series": {
            "interstices": (replace(s.interstices[0], series_uid="x"),)
        },
        "an interstice of another slice": {
            "interstices": (replace(s.interstices[0], slice_index=0),)
        },
        "digits of another series": {"digits": replace(s.digits, series_uid="x")},
        "digits of another grid": {
            "digits": replace(
                s.digits,
                digits=_frozen(np.zeros((SLICES, 10, 10), dtype=np.int8)),
            )
        },
        "a slice the digits lack": {
            "selection": replace(s.selection, slice_index=SLICES),
            "interstices": (replace(s.interstices[0], slice_index=SLICES),),
            "dome": replace(s.dome, slice_index=SLICES),
        },
        "an extent of another grid": {
            "interstices": (
                replace(s.interstices[0], extent=_frozen(np.zeros((4, 4), dtype=bool))),
            )
        },
    }
    for what, changed in refusals.items():
        arguments: dict[str, Any] = {
            "digits": s.digits,
            "selection": s.selection,
            "interstices": s.interstices,
            "centres": s.centres,
            "dome": s.dome,
        } | changed
        with pytest.raises(ValueError, match="envelope_inputs_disagree") as caught:
            read_envelope(
                arguments["digits"],
                arguments["selection"],
                arguments["interstices"],
                arguments["centres"],
                dome=arguments["dome"],
            )
        assert caught.value.__notes__, what


def test_every_code_the_orchestrations_return_is_in_its_vocabulary() -> None:
    s = _coronal()
    t = _sagittal()
    spans = read_spans(
        s.conjunction, s.selection, s.interstices, s.dome, s.centres, "left"
    )
    envelope = read_envelope(
        t.digits, t.selection, t.interstices, t.centres, dome=t.dome
    )
    assert spans.code in SPANS_RECORD_CODES
    assert all(
        body.code in SPAN_CODES and body.side_code in SIDE_CODES for body in spans.spans
    )
    assert envelope.code in ENVELOPE_CODES and envelope.pouch_code in POUCH_CODES


# --- 9.3 the picture: two decisions and the arrangement ----------------------------------------


def test_the_standing_names_a_reading_and_every_silence_apart() -> None:
    assert standing("present", SPANS_RECORD_CODES, "no_candidate") == "named"
    assert standing(None, SPANS_RECORD_CODES, "no_candidate") == "not_saved"
    assert standing("lesion", SPANS_RECORD_CODES, "no_candidate") == "code_unknown"
    assert standing(3, SPANS_RECORD_CODES, "no_candidate") == "code_unknown"
    assert (
        standing("predecessor_absent", ENVELOPE_CODES, "no_fluid_like")
        == "predecessor_absent"
    )
    assert standing("no_candidate", SPANS_RECORD_CODES, "no_candidate") == "none_found"
    assert standing("no_fluid_like", ENVELOPE_CODES, "no_fluid_like") == "none_found"
    # A word of the other record is a word this one does not say.
    assert (
        standing("no_fluid_like", SPANS_RECORD_CODES, "no_candidate") == "code_unknown"
    )


def test_the_standing_is_total_and_never_named_without_a_reading() -> None:
    # MUST NOT: draw a record whose code is not the vocabulary's, or whose stage read nothing.
    for vocabulary, none_code in (
        (SPANS_RECORD_CODES, "no_candidate"),
        (ENVELOPE_CODES, "no_fluid_like"),
    ):
        for code in (*vocabulary, None, "", "lesion", 1, True, ("present",)):
            answer = standing(code, vocabulary, none_code)
            assert answer in STANDINGS, (code, vocabulary)
            if answer == "named":
                assert code == "present"


def test_the_plane_comes_from_the_nearest_source_and_nowhere_is_a_silence() -> None:
    assert plane_source(5, True, (5,), 5, True) == "saved_for_slice"
    assert plane_source(5, False, (0, 5, 9), 5, True) == "study_walk"
    assert plane_source(5, False, (0, 9), 5, True) == "selected_plane"
    assert plane_source(5, False, (0, 9), 4, True) == "plane_not_saved"
    assert plane_source(5, False, (0, 9), 5, False) == "plane_not_saved"
    assert plane_source(5, False, (), 4, False) == "plane_not_saved"


def test_the_plane_source_is_total_and_never_a_plane_for_a_slice_that_is_not_a_number() -> (
    None
):
    for index in (0, 1, -1, 2.0, True, None, "1"):
        for saved in (True, False):
            for selected in (0, 1, True, None):
                answer = plane_source(index, saved, (0, 1, 2.0, True), selected, True)
                assert answer in PLANE_SOURCES
                if type(index) is not int:
                    assert answer == "plane_not_saved", index


def _bare_spans(index: int, code: str = "present") -> Spans:
    return Spans("series", index, code, "why", (), BORDER)


def _bare_envelope(index: int, code: str = "present") -> Envelope:
    tiles = np.zeros((ROWS, COLS), dtype=bool)
    return Envelope(
        "series", index, code, "why", tiles, tiles, 0, 0, "no_pouch", tiles, BORDER
    )


def test_the_arrangement_pairs_the_records_by_slice_and_hands_them_on_untouched() -> (
    None
):
    spans = (_bare_spans(3), _bare_spans(1, "no_candidate"))
    envelopes = (_bare_envelope(1), _bare_envelope(7, "predecessor_absent"))
    bounds = np.zeros((ROWS, COLS, 4), dtype=np.int32)
    panels = round_three_panels(spans, envelopes, bounds, {}, (), None, None, None)
    # The spans' slices first, then any the envelope names alone.
    assert [chosen.index for chosen in panels.slices] == [3, 1, 7]
    by_index = {chosen.index: chosen for chosen in panels.slices}
    assert by_index[1].spans is spans[1] and by_index[1].envelope is envelopes[0]
    assert (by_index[1].spans_standing, by_index[1].envelope_standing) == (
        "none_found",
        "named",
    )
    assert (by_index[3].envelope, by_index[3].envelope_standing) == (None, "not_saved")
    assert (by_index[7].spans, by_index[7].spans_standing) == (None, "not_saved")
    assert by_index[7].envelope_standing == "predecessor_absent"
    assert panels.bounds_rc is not None and panels.bounds_rc.dtype == np.int64


def test_the_arrangement_selects_each_slices_plane_from_its_source_and_alters_nothing() -> (
    None
):
    saved = np.full((4, 4), 7, dtype=np.uint16)
    walk = np.stack([np.full((4, 4), step, dtype=np.uint16) for step in (10, 20, 30)])
    selected = np.full((4, 4), 99, dtype=np.uint16)
    spans = tuple(_bare_spans(index) for index in (5, 20, 4, 8))
    panels = round_three_panels(
        spans, (), None, {5: saved}, (0, 20, 40), walk, 4, selected
    )
    by_index = {chosen.index: chosen for chosen in panels.slices}
    assert by_index[5].plane_source == "saved_for_slice" and by_index[5].plane is saved
    assert by_index[20].plane_source == "study_walk"
    assert by_index[20].plane is not None and by_index[20].plane[0, 0] == 20
    assert (
        by_index[4].plane_source == "selected_plane" and by_index[4].plane is selected
    )
    assert by_index[8].plane_source == "plane_not_saved" and by_index[8].plane is None
    assert saved.dtype == np.uint16 and (saved == 7).all()


def test_the_arrangement_keeps_every_absence_absent() -> None:
    nothing = round_three_panels(None, None, None, {}, (), None, None, None)
    assert nothing.slices == () and nothing.bounds_rc is None
    empty = round_three_panels((), (), None, {}, (), None, None, None)
    assert empty.slices == ()
    quiet = round_three_panels((_bare_spans(2),), None, None, {}, (2,), None, 2, None)
    (only,) = quiet.slices
    # A walk the writer did not save holds no plane, however its indices read.
    assert only.plane_source == "plane_not_saved"
    assert (only.envelope, only.envelope_standing) == (None, "not_saved")
    assert isinstance(only, ChosenSlice)


# --- 9.3 the drawer: a writer-shaped record, read and drawn -----------------------------------


def spans_record(
    slices: tuple[Spans, ...],
    grid: tuple[int, int],
    planes: dict[int, np.ndarray] | None = None,
) -> tuple[dict, dict[str, np.ndarray]]:
    """The spans of every chosen slice as the route's writer saves them: a record and its arrays.

    One entry in `slices` per chosen slice and border, in the order handed in (the depth
    collapse's), each with the stage's `slice_index`, `border`, `code` and `why` and its bodies'
    `index`, `code` and `side_code` as a list. The arrays are STACKED over the entries, one name per field as the
    other funnel records do: `spans_tiles` bool (B, TR, TC) and `spans_centre_lps` float64
    (B, 3), every body of every slice one after the other, B the bodies listed in all; and,
    where `planes` (slice index to the native plane) is given, `spans_planes` (K, R, C), one
    plane per entry in entry order. `arrays` names them.
    """
    bodies = [body for spans in slices for body in spans.spans]
    arrays: dict[str, np.ndarray] = {
        "spans_tiles": (
            np.stack([body.tiles for body in bodies])
            if bodies
            else np.zeros((0, *grid), dtype=np.bool_)
        ),
        "spans_centre_lps": (
            np.stack([body.centre_lps for body in bodies])
            if bodies
            else np.zeros((0, 3), dtype=np.float64)
        ),
    }
    names = {"tiles": "spans_tiles", "centre_lps": "spans_centre_lps"}
    if planes is not None:
        arrays["spans_planes"] = np.stack([planes[s.slice_index] for s in slices])
        names["planes"] = "spans_planes"
    record = {
        "code_names": list(SPANS_RECORD_CODES),
        "span_code_names": list(SPAN_CODES),
        "side_code_names": list(SIDE_CODES),
        "tiles_rc": list(grid),
        "slices": [
            {
                "slice_index": spans.slice_index,
                "border": spans.border,
                "code": spans.code,
                "why": spans.why,
                "spans": [
                    {"index": b.index, "code": b.code, "side_code": b.side_code}
                    for b in spans.spans
                ],
            }
            for spans in slices
        ],
        "axes": (
            "tiles (B, TR, TC) bool, one tile map per body, every slice's bodies one after the "
            "other in slice order; centre_lps (B, 3) float64 millimetres in the scanner's LPS "
            "frame, NaN where a body has no centre; planes (K, R, C), one per slice entry"
        ),
        "arrays": names,
    }
    return record, arrays


def envelope_record(
    slices: tuple[Envelope, ...],
    grid: tuple[int, int],
    planes: dict[int, np.ndarray] | None = None,
) -> tuple[dict, dict[str, np.ndarray]]:
    """The envelope of every chosen slice as the route's writer saves it: a record and its arrays.

    One entry in `slices` per chosen slice and border, in the order handed in, with the stage's
    `slice_index`, `border`, `code`, `why`, `pouch_code` and the three counts (`tiles`,
    `pouch_count`, `neck_tiles`). The arrays are STACKED over the entries, one name per field:
    `envelope_tiles`, `envelope_pouch_tiles` and `envelope_unjoined` bool (K, TR, TC), one tile
    map per entry in entry order; and, where `planes` is given, `envelope_planes` (K, R, C).
    `arrays` names them.
    """
    arrays: dict[str, np.ndarray] = {
        "envelope_tiles": np.stack([e.tiles for e in slices])
        if slices
        else np.zeros((0, *grid), dtype=np.bool_),
        "envelope_pouch_tiles": np.stack([e.pouch_tiles for e in slices])
        if slices
        else np.zeros((0, *grid), dtype=np.bool_),
        "envelope_unjoined": np.stack([e.unjoined for e in slices])
        if slices
        else np.zeros((0, *grid), dtype=np.bool_),
    }
    names = {
        "tiles": "envelope_tiles",
        "pouch_tiles": "envelope_pouch_tiles",
        "unjoined": "envelope_unjoined",
    }
    if planes is not None:
        arrays["envelope_planes"] = np.stack([planes[e.slice_index] for e in slices])
        names["planes"] = "envelope_planes"
    record = {
        "code_names": list(ENVELOPE_CODES),
        "pouch_code_names": list(POUCH_CODES),
        "tiles_rc": list(grid),
        "slices": [
            {
                "slice_index": envelope.slice_index,
                "border": envelope.border,
                "code": envelope.code,
                "why": envelope.why,
                "pouch_code": envelope.pouch_code,
                "pouch_count": envelope.pouch_count,
                "neck_tiles": envelope.neck_tiles,
                "tiles": int(np.count_nonzero(envelope.tiles)),
            }
            for envelope in slices
        ],
        "axes": (
            "tiles and pouch_tiles (K, TR, TC) bool over the squint stack's own grid, one tile "
            "map per slice entry in entry order; the pouch lies inside the envelope; planes "
            "(K, R, C), one per slice entry"
        ),
        "arrays": names,
    }
    return record, arrays


def _series() -> Series:
    """The synthetic series the drawer's squint stack is made over: three slices, a 12 x 12 grid."""
    size = ROWS * TILE_PX
    rows, columns = np.mgrid[0:size, 0:size]
    plane = (100 + 4 * rows + 2 * columns).astype(np.uint16)
    volume = np.stack([plane + 50 * z for z in range(SLICES)])
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
        directory=Path("/nonexistent/the-funnel/spans-wiring"),
        slices=(),
        stack=("stackable",),
        volume=volume,
        geometry=geometry,
        slice_codes=("decoded",) * SLICES,
        walk_indices=WALKED,
        walk=volume[list(WALKED)],
    )


def _round_three() -> tuple[tuple[Spans, ...], tuple[Envelope, ...]]:
    """Slice 1 read in full; slice 2 with no conjunction and nothing fluid-like touching a gap."""
    one, two = _coronal(slice_index=1), _coronal(slice_index=2)
    wet, dry = (
        _sagittal(slice_index=1),
        _sagittal(above=_mask((0, 11), (1, 11)), slice_index=2),
    )
    spans = (
        read_spans(
            one.conjunction,
            one.selection,
            one.interstices,
            one.dome,
            one.centres,
            "left",
        ),
        read_spans(None, two.selection, two.interstices, two.dome, two.centres, "left"),
    )
    envelopes = (
        read_envelope(
            wet.digits, wet.selection, wet.interstices, wet.centres, dome=wet.dome
        ),
        read_envelope(
            dry.digits, dry.selection, dry.interstices, dry.centres, dome=dry.dome
        ),
    )
    return spans, envelopes


def _saved_record(
    tmp_path: Path,
    *,
    with_spans: bool = True,
    with_envelope: bool = True,
    with_stack: bool = True,
    with_walk: bool = True,
    planes: dict[int, np.ndarray] | None = None,
    selected: np.ndarray | None = None,
    readings: tuple[tuple[Spans, ...], tuple[Envelope, ...]] | None = None,
) -> dict:
    """One series record shaped as the writer saves it, with its arrays on disk."""
    series = _series()
    spans, envelopes = _round_three() if readings is None else readings
    grid = (ROWS, COLS)
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
            "walk_indices": list(WALKED) if with_walk else [],
            "walk_array": "study_walk" if with_walk else None,
        },
    }
    if with_walk:
        assert series.walk is not None
        saved["study_walk"] = series.walk
    if selected is not None:
        saved["acquired_plane"] = selected
    if with_stack:
        record, arrays = squint_stack_record(read_squint_stack(series, TILE_MM))
        entry["squint_stack"] = record
        saved.update(arrays)
    if with_spans:
        entry["spans"], arrays = spans_record(spans, grid, planes)
        saved.update(arrays)
    if with_envelope:
        entry["envelope"], arrays = envelope_record(envelopes, grid, planes)
        saved.update(arrays)
    np.savez_compressed(tmp_path / "series.npz", allow_pickle=False, **saved)
    entry["arrays"] = json.loads(json.dumps(array_table(saved), allow_nan=False))
    return json.loads(json.dumps(entry, allow_nan=False))


def test_the_reader_reconstitutes_the_stages_own_records_from_a_writer_shaped_record(
    tmp_path: Path,
) -> None:
    spans, envelopes = _round_three()
    record = _saved_record(tmp_path)
    artifact, panels = spans_frames.saved_round_three(tmp_path, record)
    assert artifact == tmp_path / "series.npz"
    assert [chosen.index for chosen in panels.slices] == [1, 2]
    first, second = panels.slices
    assert (first.spans_standing, first.envelope_standing) == ("named", "named")
    assert (second.spans_standing, second.envelope_standing) == (
        "predecessor_absent",
        "none_found",
    )
    # The records are the stage's own, value for value.
    assert first.spans is not None and first.envelope is not None
    assert first.spans.code == spans[0].code and first.spans.why == spans[0].why
    assert [(b.index, b.code, b.side_code) for b in first.spans.spans] == [
        (b.index, b.code, b.side_code) for b in spans[0].spans
    ]
    for saved_body, body in zip(first.spans.spans, spans[0].spans, strict=True):
        assert np.array_equal(saved_body.tiles, body.tiles)
        assert np.allclose(saved_body.centre_lps, body.centre_lps, equal_nan=True)
    assert np.array_equal(first.envelope.tiles, envelopes[0].tiles)
    assert np.array_equal(first.envelope.pouch_tiles, envelopes[0].pouch_tiles)
    assert (first.envelope.pouch_count, first.envelope.neck_tiles) == (9, 1)
    assert first.envelope.pouch_code == "pouch"
    assert second.spans is not None and second.spans.spans == ()
    # Every slice is one the study stage walks, so its plane is the walk's.
    assert (first.plane_source, second.plane_source) == ("study_walk", "study_walk")
    assert panels.bounds_rc is not None and panels.bounds_rc.shape == (ROWS, COLS, 4)


def test_the_reader_finds_a_plane_for_each_chosen_slice_from_the_nearest_source(
    tmp_path: Path,
) -> None:
    size = ROWS * TILE_PX
    own = {
        1: np.full((size, size), 321, dtype=np.uint16),
        2: np.full((size, size), 322, dtype=np.uint16),
    }
    chosen = _saved_record(tmp_path, planes=own)
    _, panels = spans_frames.saved_round_three(tmp_path, chosen)
    first, second = panels.slices
    # The writer saved a plane for each slice: it comes before the walk, which holds them too.
    assert first.plane_source == "saved_for_slice" and first.plane is not None
    assert second.plane_source == "saved_for_slice" and second.plane is not None
    assert (first.plane == 321).all() and (second.plane == 322).all()
    selected = np.full((size, size), 55, dtype=np.uint16)
    no_walk = _saved_record(tmp_path, with_walk=False, selected=selected)
    _, panels = spans_frames.saved_round_three(tmp_path, no_walk)
    first, second = panels.slices
    # Slice 1 is the objects stage's selected slice; slice 2 is neither it nor walked.
    assert first.plane_source == "selected_plane" and first.plane is not None
    assert (first.plane == 55).all()
    assert second.plane_source == "plane_not_saved" and second.plane is None


def test_the_reader_says_when_nothing_was_saved_and_keeps_each_record_apart(
    tmp_path: Path,
) -> None:
    neither = _saved_record(tmp_path, with_spans=False, with_envelope=False)
    _, panels = spans_frames.saved_round_three(tmp_path, neither)
    assert panels.slices == () and panels.bounds_rc is None
    only_envelope = _saved_record(tmp_path, with_spans=False)
    _, panels = spans_frames.saved_round_three(tmp_path, only_envelope)
    assert [(c.spans_standing, c.envelope_standing) for c in panels.slices] == [
        ("not_saved", "named"),
        ("not_saved", "none_found"),
    ]
    only_spans = _saved_record(tmp_path, with_envelope=False)
    _, panels = spans_frames.saved_round_three(tmp_path, only_spans)
    assert [(c.spans_standing, c.envelope_standing) for c in panels.slices] == [
        ("named", "not_saved"),
        ("predecessor_absent", "not_saved"),
    ]


def test_the_reader_accepts_the_unmade_record_the_stage_returns_for_no_slice_at_all(
    tmp_path: Path,
) -> None:
    """A slice index of -1 is how an absent dome names no slice; the entry saves it as it is."""
    absent_spans = Spans("series", -1, "predecessor_absent", "no dome", (), BORDER)
    absent_envelope = _bare_envelope(-1, "predecessor_absent")
    record = _saved_record(tmp_path, with_spans=False, with_envelope=False)
    spans_part, spans_arrays = spans_record((absent_spans,), (ROWS, COLS))
    envelope_part, envelope_arrays = envelope_record((absent_envelope,), (ROWS, COLS))
    record["spans"], record["envelope"] = spans_part, envelope_part
    with np.load(tmp_path / "series.npz", allow_pickle=False) as old:
        saved = {name: old[name] for name in old.files}
    saved.update(spans_arrays | envelope_arrays)
    np.savez_compressed(tmp_path / "series.npz", allow_pickle=False, **saved)
    record["arrays"] = json.loads(json.dumps(array_table(saved), allow_nan=False))
    _, panels = spans_frames.saved_round_three(tmp_path, record)
    (only,) = panels.slices
    assert only.index == -1
    assert (only.spans_standing, only.envelope_standing) == (
        "predecessor_absent",
        "predecessor_absent",
    )
    assert only.plane_source == "plane_not_saved"


def _refused(tmp_path: Path, record: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        spans_frames.saved_round_three(tmp_path, record)


def test_the_reader_refuses_a_saved_record_that_disagrees_with_the_writer(
    tmp_path: Path,
) -> None:
    # MUST NOT: draw a tampered array, a vocabulary or a code that is not the stage's, a grid that
    # is not the stack's, a slice outside the stack or named twice, a count that is not its
    # array's, a pouch outside its envelope, a plane of another shape, or a record with no stack;
    # each is named and raised.
    good = _saved_record(tmp_path)

    tampered = copy.deepcopy(good)
    tampered["arrays"]["spans_tiles"]["digest"] = "changed"
    _refused(tmp_path, tampered, "saved_array_digest_mismatch")

    shaped = copy.deepcopy(good)
    shaped["spans"] = "yes"
    _refused(tmp_path, shaped, "saved_spans_not_a_record")

    worded = copy.deepcopy(good)
    worded["spans"]["span_code_names"] = ["span"]
    _refused(tmp_path, worded, "saved_spans_vocabulary_mismatch")

    unsaid = copy.deepcopy(good)
    unsaid["envelope"]["slices"][0]["code"] = "lesion"
    _refused(tmp_path, unsaid, "saved_envelope_code_unknown")

    bodied = copy.deepcopy(good)
    bodied["spans"]["slices"][0]["spans"][0]["code"] = "tendon"
    _refused(tmp_path, bodied, "saved_spans_body_code_unknown")

    sided = copy.deepcopy(good)
    sided["spans"]["slices"][0]["spans"][0]["side_code"] = "inner"
    _refused(tmp_path, sided, "saved_spans_side_unknown")

    grid = copy.deepcopy(good)
    grid["spans"]["tiles_rc"] = [4, 4]
    _refused(tmp_path, grid, "saved_spans_grid_mismatch")

    outside = copy.deepcopy(good)
    outside["envelope"]["slices"][1]["slice_index"] = SLICES
    _refused(tmp_path, outside, "saved_envelope_slice_outside_stack")

    twice = copy.deepcopy(good)
    twice["spans"]["slices"][1]["slice_index"] = 1
    _refused(tmp_path, twice, "saved_spans_slice_repeated")

    negative = copy.deepcopy(good)
    negative["spans"]["slices"][0]["slice_index"] = -1
    _refused(tmp_path, negative, "saved_spans_slice_index_invalid")

    counted = copy.deepcopy(good)
    counted["envelope"]["slices"][0]["tiles"] += 1
    _refused(tmp_path, counted, "saved_envelope_count_mismatch")

    pouched = copy.deepcopy(good)
    pouched["envelope"]["slices"][0]["pouch_code"] = "lump"
    _refused(tmp_path, pouched, "saved_envelope_pouch_code_unknown")

    bodies = copy.deepcopy(good)
    bodies["spans"]["slices"][0]["spans"].pop()
    _refused(tmp_path, bodies, "saved_spans_shape_mismatch")

    unnamed = copy.deepcopy(good)
    del unnamed["spans"]["arrays"]["centre_lps"]
    _refused(tmp_path, unnamed, "saved_spans_array_unnamed")

    missing = copy.deepcopy(good)
    del missing["envelope"]["arrays"]
    _refused(tmp_path, missing, "saved_envelope_arrays_missing")

    planeless = copy.deepcopy(good)
    planeless["envelope"]["arrays"]["planes"] = 3
    _refused(tmp_path, planeless, "saved_envelope_array_unnamed")

    alone = _saved_record(tmp_path, with_stack=False)
    _refused(tmp_path, alone, "saved_round_three_without_a_stack")

    zeros = np.zeros((5, 5), dtype=np.uint16)
    foreign = _saved_record(tmp_path, planes={1: zeros, 2: zeros})
    _refused(tmp_path, foreign, "saved_round_three_covers_another_plane")


def test_the_reader_refuses_a_malformed_shell_by_name(tmp_path: Path) -> None:
    good = _saved_record(tmp_path)

    def edited(change) -> dict:
        record = copy.deepcopy(good)
        change(record)
        return record

    cases = {
        "saved_spans_tiles_invalid": lambda r: r["spans"].update(tiles_rc="ten"),
        "saved_spans_slices_invalid": lambda r: r["spans"].update(slices="none"),
        "saved_spans_slice_not_a_record": lambda r: r["spans"]["slices"].__setitem__(
            0, "slice"
        ),
        "saved_spans_slice_index_invalid": lambda r: r["spans"]["slices"][0].update(
            slice_index="1"
        ),
        "saved_spans_field_invalid:why": lambda r: r["spans"]["slices"][0].update(
            why=None
        ),
        "saved_spans_bodies_invalid": lambda r: r["spans"]["slices"][0].update(
            spans="bodies"
        ),
        "saved_spans_body_not_a_record": lambda r: r["spans"]["slices"][0][
            "spans"
        ].__setitem__(0, "body"),
        "saved_spans_body_index_invalid": lambda r: r["spans"]["slices"][0]["spans"][
            0
        ].update(index="1"),
        "saved_envelope_count_invalid:neck_tiles": lambda r: r["envelope"]["slices"][
            0
        ].update(neck_tiles=-1),
        "saved_envelope_count_invalid:tiles": lambda r: r["envelope"]["slices"][
            0
        ].update(tiles=True),
        "saved_walk_indices_not_a_list": lambda r: r["study"].update(
            walk_indices="0,1,2"
        ),
        "saved_walk_indices_mismatch": lambda r: r["study"].update(walk_indices=[0, 1]),
    }
    for message, change in cases.items():
        _refused(tmp_path, edited(change), message)


def test_the_reader_refuses_arrays_of_a_representation_the_stage_does_not_return(
    tmp_path: Path,
) -> None:
    record = _saved_record(tmp_path)
    with np.load(tmp_path / "series.npz", allow_pickle=False) as old:
        saved = {name: old[name] for name in old.files}
    cases = {
        "saved_spans_representation_invalid:tiles": dict(
            saved, spans_tiles=saved["spans_tiles"].astype(np.uint8)
        ),
        "saved_envelope_representation_invalid:pouch_tiles": dict(
            saved, envelope_pouch_tiles=saved["envelope_pouch_tiles"].astype(np.uint8)
        ),
        "saved_array_representation_invalid:acquired_plane": dict(
            saved, acquired_plane=np.zeros((ROWS * TILE_PX, ROWS * TILE_PX), dtype=bool)
        ),
    }
    for message, changed in cases.items():
        np.savez_compressed(tmp_path / "series.npz", allow_pickle=False, **changed)
        edited = copy.deepcopy(record)
        edited["arrays"] = json.loads(json.dumps(array_table(changed), allow_nan=False))
        _refused(tmp_path, edited, message)


def test_the_reader_refuses_stacked_arrays_whose_length_is_not_what_the_entries_list(
    tmp_path: Path,
) -> None:
    record = _saved_record(tmp_path)
    with np.load(tmp_path / "series.npz", allow_pickle=False) as old:
        saved = {name: old[name] for name in old.files}
    # One envelope tile map short of the two entries; one extra body beyond the five listed;
    # planes for one slice of the two.
    short = dict(saved, envelope_tiles=saved["envelope_tiles"][:1])
    long = dict(saved, spans_tiles=np.concatenate([saved["spans_tiles"]] * 2))
    for changed, message in ((short, "saved_envelope_"), (long, "saved_spans_")):
        np.savez_compressed(tmp_path / "series.npz", allow_pickle=False, **changed)
        edited = copy.deepcopy(record)
        edited["arrays"] = json.loads(json.dumps(array_table(changed), allow_nan=False))
        _refused(tmp_path, edited, f"{message}shape_mismatch")
    stacked = dict(
        saved,
        spans_planes=np.zeros((1, ROWS * TILE_PX, ROWS * TILE_PX), dtype=np.uint16),
    )
    np.savez_compressed(tmp_path / "series.npz", allow_pickle=False, **stacked)
    edited = copy.deepcopy(record)
    edited["spans"]["arrays"]["planes"] = "spans_planes"
    edited["arrays"] = json.loads(json.dumps(array_table(stacked), allow_nan=False))
    _refused(tmp_path, edited, "saved_spans_shape_mismatch:planes")
    textual = dict(saved, spans_planes=np.zeros((2, 4, 4), dtype=np.bool_))
    np.savez_compressed(tmp_path / "series.npz", allow_pickle=False, **textual)
    edited = copy.deepcopy(record)
    edited["spans"]["arrays"]["planes"] = "spans_planes"
    edited["arrays"] = json.loads(json.dumps(array_table(textual), allow_nan=False))
    _refused(tmp_path, edited, "saved_spans_representation_invalid:planes")


def test_the_reader_refuses_a_pouch_that_the_envelope_does_not_hold(
    tmp_path: Path,
) -> None:
    record = _saved_record(tmp_path)
    with np.load(tmp_path / "series.npz", allow_pickle=False) as old:
        saved = {name: old[name] for name in old.files}
    saved["envelope_pouch_tiles"] = np.ones((2, ROWS, COLS), dtype=np.bool_)
    np.savez_compressed(tmp_path / "series.npz", allow_pickle=False, **saved)
    record["arrays"] = json.loads(json.dumps(array_table(saved), allow_nan=False))
    record["envelope"]["slices"][0]["pouch_count"] = ROWS * COLS
    _refused(tmp_path, record, "saved_envelope_pouch_outside_envelope")


def test_an_out_directory_outside_data_is_an_argument_refusal(tmp_path: Path) -> None:
    record = _saved_record(tmp_path)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    with pytest.raises(ArgumentRefusal, match="private data directory"):
        spans_frames.draw(tmp_path, "study", tmp_path / "out")
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    with pytest.raises(ArgumentRefusal, match="no saved records"):
        spans_frames.draw(tmp_path, "another study", out)
    assert not out.exists()


def test_the_drawer_writes_one_sheet_per_series_with_its_manifest(
    tmp_path: Path,
) -> None:
    """The impure edge, end to end: one image per series under data/, bound to the receipt."""
    record = _saved_record(tmp_path)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = spans_frames.draw(tmp_path, "study", out)
        assert manifest["images"] == ["01-coronal-fs1-fat1.png"]
        assert manifest["image"] == "01-coronal-fs1-fat1.png"
        assert (out / "01-coronal-fs1-fat1.png").exists()
        assert (out / "manifest.json").exists()
        assert manifest["standings"] == list(STANDINGS)
        assert manifest["plane_sources"] == list(PLANE_SOURCES)
        assert (
            manifest["legend"]["span_codes"]["span"]
            == spans_frames.SPAN_COLOURS["span"]
        )
        (series,) = manifest["series"]
        assert series["image"] == "01-coronal-fs1-fat1.png"
        assert [
            (c["index"], c["plane_source"], c["spans_standing"], c["envelope_standing"])
            for c in series["chosen"]
        ] == [
            (1, "study_walk", "named", "named"),
            (2, "study_walk", "predecessor_absent", "none_found"),
        ]
        first_spans, second_spans = series["spans"]["slices"]
        assert first_spans["counts"] == {
            "span": 2,
            "touches_one": 1,
            "touches_none": 1,
            "inside_interstice": 1,
        }
        assert (
            second_spans["code"] == "predecessor_absent"
            and second_spans["bodies"] == []
        )
        first_envelope, second_envelope = series["envelope"]["slices"]
        assert (
            first_envelope["tiles"],
            first_envelope["pouch_count"],
            first_envelope["neck_tiles"],
            first_envelope["pouch_code"],
        ) == (19, 9, 1, "pouch")
        assert (
            second_envelope["code"] == "no_fluid_like" and second_envelope["tiles"] == 0
        )
        # The arrays it drew from are the stacked ones, with the writer's own descriptors: five
        # bodies in all (slice 1's, slice 2 having none), one tile map per envelope entry.
        assert list(series["spans"]["arrays"]) == ["tiles", "centre_lps"]
        assert series["spans"]["arrays"]["tiles"]["shape"] == [5, ROWS, COLS]
        assert series["spans"]["arrays"]["centre_lps"]["shape"] == [5, 3]
        assert list(series["envelope"]["arrays"]) == [
            "tiles",
            "pouch_tiles",
            "unjoined",
        ]
        assert series["envelope"]["arrays"]["pouch_tiles"]["shape"] == [2, ROWS, COLS]
        assert series["envelope"]["arrays"]["unjoined"]["shape"] == [2, ROWS, COLS]
        assert series["envelope"]["arrays"]["pouch_tiles"]["dtype"] == "|b1"
        # The manifest is JSON that refuses NaN, and binds the sheet to the receipt.
        again = json.loads((out / "manifest.json").read_text())
        assert again["receipt_sha256"] == manifest["receipt_sha256"]
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_the_drawer_draws_a_slice_with_no_plane_and_every_standing_in_words(
    tmp_path: Path,
) -> None:
    inside = _coronal(dark=_mask((slice(5, 7), slice(5, 7))))
    wet, away = _sagittal(), _sagittal(slice_index=2)
    readings = (
        # The spans name slice 1 alone; the envelope names slices 1 and 2.
        (
            read_spans(
                inside.conjunction,
                inside.selection,
                inside.interstices,
                inside.dome,
                inside.centres,
                "right",
            ),
        ),
        (
            read_envelope(
                wet.digits, wet.selection, wet.interstices, wet.centres, dome=wet.dome
            ),
            read_envelope(
                replace(away.digits, code="predecessor_absent"),
                away.selection,
                away.interstices,
                away.centres,
                dome=away.dome,
            ),
        ),
    )
    # No walk and no selected plane are saved, so no slice has a plane to lie over.
    record = _saved_record(tmp_path, with_walk=False, readings=readings)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = spans_frames.draw(tmp_path, "study", out)
        (series,) = manifest["series"]
        assert [
            (c["index"], c["plane_source"], c["spans_standing"], c["envelope_standing"])
            for c in series["chosen"]
        ] == [
            (1, "plane_not_saved", "none_found", "named"),
            (2, "plane_not_saved", "not_saved", "predecessor_absent"),
        ]
        # The bodies inside the gap are kept and counted although no span was found. The spans'
        # record names slice 1 alone, so slice 2 carries no code, no bodies and no counts: not
        # saved, which is not a zero.
        first_spans, second_spans = series["spans"]["slices"]
        assert first_spans["counts"] == {"inside_interstice": 1}
        assert first_spans["code"] == "no_candidate"
        assert (second_spans["standing"], second_spans["code"]) == ("not_saved", None)
        assert second_spans["bodies"] == [] and second_spans["counts"] == {}
        assert (out / series["image"]).exists()
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_the_drawer_refuses_a_vocabulary_it_has_no_words_or_colour_for(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # MUST NOT: draw a standing with no words or a span code with no colour, which would be
    # drawn in none; each is refused by name before anything is drawn.
    record = _saved_record(tmp_path)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    with monkeypatch.context() as patched:
        patched.setattr(spans_frames, "SPAN_COLOURS", {})
        with pytest.raises(RuntimeError, match="round_three_vocabulary_uncoloured"):
            spans_frames.draw(tmp_path, "study", out)
    with monkeypatch.context() as patched:
        patched.setattr(spans_frames, "PLANE_WORDS", {})
        with pytest.raises(RuntimeError, match="round_three_unworded"):
            spans_frames.draw(tmp_path, "study", out)
    assert not out.exists()


def test_the_drawer_draws_a_series_whose_record_names_no_chosen_slice(
    tmp_path: Path,
) -> None:
    record = _saved_record(tmp_path, readings=((), ()))
    assert record["spans"]["slices"] == [] and record["envelope"]["slices"] == []
    _, panels = spans_frames.saved_round_three(tmp_path, record)
    assert panels.slices == () and panels.bounds_rc is not None
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = spans_frames.draw(tmp_path, "study", out)
        (series,) = manifest["series"]
        assert series["chosen"] == []
        assert series["spans"]["slices"] == [] and series["envelope"]["slices"] == []
        assert (out / series["image"]).exists()
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_a_series_the_writer_saved_no_round_three_for_draws_its_silence_in_words(
    tmp_path: Path,
) -> None:
    record = _saved_record(tmp_path, with_spans=False, with_envelope=False)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = spans_frames.draw(tmp_path, "study", out)
        (series,) = manifest["series"]
        assert series["spans"] is None and series["envelope"] is None
        assert series["chosen"] == []
        assert (out / series["image"]).exists()
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_the_picture_module_is_the_adapter_the_drawer_reads() -> None:
    assert spans_frames.pictures.standing is standing
    assert spans_frames.pictures.round_three_panels is round_three_panels
    assert set(STANDINGS) <= set(spans_frames.SPANS_WORDS)
    assert set(STANDINGS) <= set(spans_frames.ENVELOPE_WORDS)
    assert set(PLANE_SOURCES) <= set(spans_frames.PLANE_WORDS)
    assert set(SPAN_CODES) <= set(spans_frames.SPAN_COLOURS)
    assert set(SIDE_CODES) <= set(spans_frames.SIDE_WORDS)
