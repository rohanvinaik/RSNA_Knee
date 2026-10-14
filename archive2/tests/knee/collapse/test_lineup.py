"""Intent tests for the line-up's measurement and orchestration (knee.collapse.lineup), both
signs, written from the contract: a partner grid shifted by half a pixel maps every tile to itself
with a distance under half a tile; a partner grid at another pixel size maps each tile to the
partner tile whose native bounds overlap the recipient tile's millimetre footprint; a tile with
no centre is never chosen and asks nothing; an exact tie takes the first partner tile in scan
order; two stacks of one plane line up slice by slice along the recipient's normal and tile by
tile by centre; a stack that is not present, a geometry that is None and a thickness the header
did not give are each the silence or the refusal they are, never a match; nothing of the
caller's is written; the ledger carries the consumption then the production. The CONTRACT's
proof gate."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from knee.collapse.lineup import (
    MATCH_CODES,
    SLAB_CODES,
    LineUp,
    line_up,
    nearest_tiles,
    normal_angle_deg,
    shared_half_thickness_mm,
)
from knee.collapse.physical import PlaneFrame, physical_squint
from knee.collapse.squint_stack import SquintStack, read_squint_stack
from knee.study.series import Series, SeriesGeometry
from knee.study.tables import SeriesRow
from knee.telemetry import recording

#: A coronal-like header: the row direction (the first triplet) is the scanner's +x and the
#: column direction (the second) its -z, so the slice normal is +y and the stack steps along it.
ORIENTATION = np.array([1.0, 0.0, 0.0, 0.0, 0.0, -1.0])
ROW_DIRECTION = np.array([1.0, 0.0, 0.0])
NORMAL = np.array([0.0, 1.0, 0.0])
ORIGIN = np.array([10.0, 20.0, 30.0])
SPACING = (0.5, 0.5)
STEP_MM = 2.0
SLICES, ROWS, COLUMNS = 3, 8, 8
#: Two millimetres is four pixels at half a millimetre: a 2 x 2 grid of 4 x 4 px tiles.
TILE_MM = 2.0
HALF_TILE_MM = TILE_MM / 2.0
#: Half a pixel at half a millimetre: the "scootch" between the two acquisitions.
HALF_PIXEL_MM = 0.25
#: Slices two millimetres apart, each two millimetres thick: half a thickness is one millimetre.
HALF_THICKNESS_MM = 1.0

NOWHERE = Path("/nonexistent/the-funnel/lineup")

MATCHED = MATCH_CODES.index("matched")
BEYOND = MATCH_CODES.index("beyond_half_tile")
UNAVAILABLE = MATCH_CODES.index("partner_unavailable")
INVALID_MATCH = MATCH_CODES.index("invalid_measurement")
IN_SLAB = SLAB_CODES.index("in_slab")
NEAREST_ONLY = SLAB_CODES.index("nearest_only")
NO_PARTNER = SLAB_CODES.index("no_partner")
INVALID_SLAB = SLAB_CODES.index("invalid_measurement")


def _row(uid: str, fat: str) -> SeriesRow:
    return SeriesRow(
        study_uid="study-lineup",
        series_uid=uid,
        fluid_sensitive=fat,
        fat_suppression=fat,
        anatomical_plane="Coronal",
    )


def _geometry(
    slices: int = SLICES,
    origin: np.ndarray = ORIGIN,
    spacing: tuple[float, float] = SPACING,
    step_mm: float = STEP_MM,
) -> SeriesGeometry:
    positions = np.array([origin + z * step_mm * NORMAL for z in range(slices)])
    return SeriesGeometry(
        normal=NORMAL.copy(),
        orientation=np.tile(ORIENTATION, (slices, 1)),
        position=positions,
        spacing=np.tile(np.asarray(spacing, dtype=np.float64), (slices, 1)),
        along_normal=positions @ NORMAL,
        orientation_spread=0.0,
        origin_spread_mm=0.0,
    )


def _volume(
    slices: int = SLICES, rows: int = ROWS, columns: int = COLUMNS
) -> np.ndarray:
    r, c = np.indices((rows, columns))
    return np.stack(
        [(100 + 7 * r + 3 * c + 50 * z).astype(np.uint16) for z in range(slices)]
    )


def _series(
    uid: str,
    fat: str,
    volume: np.ndarray | None,
    geometry: SeriesGeometry | None,
) -> Series:
    return Series(
        row=_row(uid, fat),
        directory=NOWHERE / uid,
        slices=(),
        stack=("stackable",),
        volume=volume,
        geometry=geometry,
    )


def _stack(uid: str, fat: str, volume, geometry) -> SquintStack:
    return read_squint_stack(_series(uid, fat, volume, geometry), TILE_MM)


def _recipient() -> tuple[SquintStack, SeriesGeometry]:
    geometry = _geometry()
    return _stack("series-dark", "1", _volume(), geometry), geometry


def _partner(
    origin: np.ndarray = ORIGIN + HALF_PIXEL_MM * ROW_DIRECTION,
    slices: int = SLICES,
    step_mm: float = STEP_MM,
) -> tuple[SquintStack, SeriesGeometry]:
    geometry = _geometry(slices=slices, origin=origin, step_mm=step_mm)
    return _stack("series-bright", "0", _volume(slices=slices), geometry), geometry


def _frame(origin: np.ndarray = ORIGIN, spacing=SPACING) -> PlaneFrame:
    return PlaneFrame.from_dicom(origin, ORIENTATION, spacing)


def _centres(frame: PlaneFrame, plane: np.ndarray, spacing=SPACING) -> np.ndarray:
    """Tile centres of one plane in LPS, through the stack's own measurement."""
    from knee.collapse.squint_stack import tile_centres_lps

    return tile_centres_lps(frame, physical_squint(plane, spacing, TILE_MM).bounds_rc)


def _identity(tiles_down: int, tiles_across: int) -> np.ndarray:
    rows, columns = np.indices((tiles_down, tiles_across))
    return np.stack((rows, columns), axis=-1).astype(np.int64)


# --- the measurement: positive --------------------------------------------------------------


def test_a_partner_grid_shifted_by_half_a_pixel_maps_every_tile_to_itself_within_half_a_tile() -> (
    None
):
    plane = _volume()[0]
    recipient = _centres(_frame(), plane)
    partner = _centres(_frame(ORIGIN + HALF_PIXEL_MM * ROW_DIRECTION), plane)
    tiles, distance = nearest_tiles(recipient, partner)
    assert tiles.shape == (2, 2, 2) and tiles.dtype == np.int64
    assert distance.shape == (2, 2) and distance.dtype == np.float64
    np.testing.assert_array_equal(tiles, _identity(2, 2))
    np.testing.assert_allclose(distance, HALF_PIXEL_MM, atol=1e-12)
    assert np.all(distance < HALF_TILE_MM)


def test_a_partner_grid_at_another_pixel_size_maps_each_tile_to_the_tile_whose_bounds_overlap_its_footprint() -> (
    None
):
    # The recipient: 8 x 8 px at 0.5 mm, 4 mm across, a 2 x 2 grid of 2 mm tiles. The partner:
    # 8 x 8 px at 1.0 mm, 8 mm across, a 4 x 4 grid of 2 mm (2 px) tiles over the same corner.
    recipient_frame = _frame()
    recipient_plane = _volume()[0]
    recipient_squint = physical_squint(recipient_plane, SPACING, TILE_MM)
    partner_spacing = (1.0, 1.0)
    partner_frame = _frame(spacing=partner_spacing)
    partner_squint = physical_squint(recipient_plane, partner_spacing, TILE_MM)
    assert partner_squint.bounds_rc.shape == (4, 4, 4)
    tiles, distance = nearest_tiles(
        _centres(recipient_frame, recipient_plane),
        _centres(partner_frame, recipient_plane, partner_spacing),
    )
    np.testing.assert_array_equal(tiles, _identity(2, 2))
    assert np.all(distance < HALF_TILE_MM)
    # Each recipient tile's millimetre footprint, carried into the partner's native frame,
    # overlaps the native bounds of the partner tile it was matched to.
    for i in range(2):
        for j in range(2):
            r0, r1, c0, c1 = recipient_squint.bounds_rc[i, j]
            corners = np.array(
                [[r0, c0], [r0, c1 - 1], [r1 - 1, c0], [r1 - 1, c1 - 1]],
                dtype=np.float64,
            )
            footprint = partner_frame.to_native(recipient_frame.to_patient(corners))
            p0, p1, q0, q1 = partner_squint.bounds_rc[tuple(tiles[i, j])]
            assert footprint[:, 0].min() < p1 and footprint[:, 0].max() >= p0
            assert footprint[:, 1].min() < q1 and footprint[:, 1].max() >= q0


def test_an_exact_tie_takes_the_first_partner_tile_in_scan_order() -> None:
    partner = np.full((2, 2, 3), np.nan)
    partner[0, 1] = (0.0, 1.0, 0.0)
    partner[1, 0] = (1.0, 0.0, 0.0)
    recipient = np.array([[[0.5, 0.5, 0.0]]])
    tiles, distance = nearest_tiles(recipient, partner)
    assert tuple(tiles[0, 0]) == (0, 1)
    np.testing.assert_allclose(distance[0, 0], math.sqrt(0.5))
    # The same tie with both tiles given: still the first in scan order, (0, 0) before (1, 1).
    partner[0, 0] = (0.0, 1.0, 0.0)
    partner[1, 1] = (1.0, 0.0, 0.0)
    tiles, _ = nearest_tiles(recipient, partner)
    assert tuple(tiles[0, 0]) == (0, 0)


# --- the measurement: negative --------------------------------------------------------------


def test_a_partner_tile_with_no_centre_is_never_chosen() -> None:
    # MUST NOT: choose an empty partner tile, however near its (absent) centre would lie.
    plane = _volume()[0]
    recipient = _centres(_frame(), plane)
    partner = np.array(_centres(_frame(ORIGIN + HALF_PIXEL_MM * ROW_DIRECTION), plane))
    partner[0, 0] = np.nan
    tiles, distance = nearest_tiles(recipient, partner)
    assert tuple(tiles[0, 0]) != (0, 0)
    assert np.isfinite(distance[0, 0]) and distance[0, 0] > HALF_PIXEL_MM
    np.testing.assert_array_equal(tiles[1, 1], (1, 1))
    nothing = np.full(partner.shape, np.nan)
    tiles, distance = nearest_tiles(recipient, nothing)
    assert np.all(tiles == -1) and np.isnan(distance).all()


def test_a_recipient_tile_with_no_centre_asks_nothing() -> None:
    plane = _volume()[0]
    recipient = np.array(_centres(_frame(), plane))
    recipient[1, 0] = np.nan
    partner = _centres(_frame(), plane)
    tiles, distance = nearest_tiles(recipient, partner)
    assert tuple(tiles[1, 0]) == (-1, -1) and np.isnan(distance[1, 0])
    assert tuple(tiles[0, 0]) == (0, 0) and distance[0, 0] == 0.0


@pytest.mark.parametrize(
    ("recipient", "partner", "named"),
    [
        (np.zeros((2, 3)), np.zeros((2, 2, 3)), "invalid_recipient_centres"),
        (np.zeros((2, 2, 2)), np.zeros((2, 2, 3)), "invalid_recipient_centres"),
        (np.zeros((2, 2, 3)), np.zeros((4, 3)), "invalid_partner_centres"),
        (np.zeros((2, 2, 3)), np.zeros((2, 2, 4)), "invalid_partner_centres"),
    ],
)
def test_centres_that_are_not_a_grid_of_points_are_refused_by_name(
    recipient: np.ndarray, partner: np.ndarray, named: str
) -> None:
    with pytest.raises(ValueError, match=named):
        nearest_tiles(recipient, partner)


def test_the_measurement_writes_nothing_of_the_callers_and_freezes_its_own() -> None:
    plane = _volume()[0]
    recipient = np.array(_centres(_frame(), plane))
    partner = np.array(_centres(_frame(ORIGIN + HALF_PIXEL_MM * ROW_DIRECTION), plane))
    before = (recipient.copy(), partner.copy())
    tiles, distance = nearest_tiles(recipient, partner)
    np.testing.assert_array_equal(recipient, before[0])
    np.testing.assert_array_equal(partner, before[1])
    assert recipient.flags.writeable and partner.flags.writeable
    assert not tiles.flags.writeable and not distance.flags.writeable


# --- the orchestration: positive ------------------------------------------------------------


def test_two_stacks_of_one_plane_line_up_slice_by_slice_and_tile_by_tile() -> None:
    recipient, recipient_geometry = _recipient()
    partner, partner_geometry = _partner()
    reading = line_up(
        recipient,
        partner,
        recipient_geometry,
        partner_geometry,
        HALF_TILE_MM,
        HALF_THICKNESS_MM,
    )
    assert isinstance(reading, LineUp)
    assert reading.code == "present"
    assert reading.recipient_uid == "series-dark"
    assert reading.partner_uid == "series-bright"
    assert reading.half_tile_mm == HALF_TILE_MM
    assert reading.half_thickness_mm == HALF_THICKNESS_MM
    assert reading.normal_angle_deg == 0.0
    np.testing.assert_array_equal(reading.partner_slice, np.arange(SLICES))
    assert reading.partner_slice.dtype == np.int64
    np.testing.assert_array_equal(reading.slab_codes, np.full(SLICES, IN_SLAB))
    assert reading.slab_codes.dtype == np.uint8
    assert reading.partner_tile.shape == (SLICES, 2, 2, 2)
    for z in range(SLICES):
        np.testing.assert_array_equal(reading.partner_tile[z], _identity(2, 2))
    np.testing.assert_allclose(reading.distance_mm, HALF_PIXEL_MM, atol=1e-12)
    assert reading.distance_mm.shape == (SLICES, 2, 2)
    np.testing.assert_array_equal(
        reading.match_codes, np.full((SLICES, 2, 2), MATCHED, dtype=np.uint8)
    )
    assert reading.match_codes.dtype == np.uint8


def test_a_partner_slice_beyond_half_the_thickness_is_named_nearest_only() -> None:
    recipient, recipient_geometry = _recipient()
    # Two partner slices at 0 and 2 mm against three recipient slices at 0, 2 and 4 mm: the
    # third recipient slice's nearest partner is the second, two millimetres off.
    partner, partner_geometry = _partner(slices=2)
    reading = line_up(
        recipient,
        partner,
        recipient_geometry,
        partner_geometry,
        HALF_TILE_MM,
        HALF_THICKNESS_MM,
    )
    np.testing.assert_array_equal(reading.partner_slice, [0, 1, 1])
    assert [SLAB_CODES[c] for c in reading.slab_codes] == [
        "in_slab",
        "in_slab",
        "nearest_only",
    ]
    # The tiles of a nearest-only slice are still lined up and named: the nearest partner tile
    # is kept, and its distance is the scanner's, which carries the two millimetres along the
    # normal, so against a one-millimetre bar every tile there is beyond half a tile.
    np.testing.assert_array_equal(reading.partner_tile[2], _identity(2, 2))
    np.testing.assert_allclose(
        reading.distance_mm[2], math.hypot(HALF_PIXEL_MM, STEP_MM), atol=1e-12
    )
    np.testing.assert_array_equal(reading.match_codes[2], np.full((2, 2), BEYOND))
    # A partner stack offset along the normal by 0.6 mm against a half thickness of 0.5 mm:
    # every slice is named nearest-only, with its nearest partner slice kept.
    shifted, shifted_geometry = _partner(
        origin=ORIGIN + HALF_PIXEL_MM * ROW_DIRECTION + 0.6 * NORMAL
    )
    reading = line_up(
        recipient, shifted, recipient_geometry, shifted_geometry, HALF_TILE_MM, 0.5
    )
    np.testing.assert_array_equal(reading.partner_slice, [0, 1, 2])
    assert set(reading.slab_codes.tolist()) == {NEAREST_ONLY}


def test_the_half_tile_bar_is_the_callers() -> None:
    recipient, recipient_geometry = _recipient()
    partner, partner_geometry = _partner()
    reading = line_up(
        recipient, partner, recipient_geometry, partner_geometry, 0.1, HALF_THICKNESS_MM
    )
    assert set(reading.match_codes.ravel().tolist()) == {BEYOND}
    np.testing.assert_allclose(reading.distance_mm, HALF_PIXEL_MM, atol=1e-12)
    for z in range(SLICES):
        np.testing.assert_array_equal(reading.partner_tile[z], _identity(2, 2))


def test_the_ledger_carries_the_consumption_then_the_production_with_its_counts() -> (
    None
):
    recipient, recipient_geometry = _recipient()
    partner, partner_geometry = _partner(slices=2)
    with recording() as run_ledger:
        line_up(
            recipient,
            partner,
            recipient_geometry,
            partner_geometry,
            HALF_TILE_MM,
            HALF_THICKNESS_MM,
        )
    events = run_ledger.events()
    assert [event.name for event in events] == [
        "squint_stack.consumed_by.lineup",
        "lineup.produced",
    ]
    assert dict(events[0].counts) == {"recipient": 1, "partner": 1}
    # Two slices in the slab with every tile matched; the third slice's tiles lie two
    # millimetres off along the normal and are beyond the bar, so they are not counted.
    assert dict(events[1].counts) == {"matched": 2 * 4, "in_slab": 2}


def test_the_angle_between_the_normals_is_kept_as_measured() -> None:
    geometry = _geometry()
    assert normal_angle_deg(geometry, geometry) == 0.0
    against = SeriesGeometry(
        normal=-NORMAL,
        orientation=geometry.orientation,
        position=geometry.position,
        spacing=geometry.spacing,
        along_normal=geometry.along_normal,
        orientation_spread=0.0,
    )
    assert normal_angle_deg(geometry, against) == pytest.approx(180.0)
    assert math.isnan(normal_angle_deg(None, geometry))
    assert math.isnan(normal_angle_deg(geometry, None))


def test_half_the_shared_thickness_is_the_slab_bar() -> None:
    assert shared_half_thickness_mm((2.0, 2.0, 2.0)) == 1.0
    assert shared_half_thickness_mm((None, 3.0, None)) == 1.5


# --- the orchestration: negative ------------------------------------------------------------


def _assert_silent(reading: LineUp, slices: int, tiles: tuple[int, int]) -> None:
    assert reading.partner_slice.shape == (slices,)
    assert np.all(reading.partner_slice == -1)
    assert reading.slab_codes.shape == (slices,)
    assert np.all(reading.slab_codes == NO_PARTNER)
    assert reading.partner_tile.shape == (slices, *tiles, 2)
    assert np.all(reading.partner_tile == -1)
    assert reading.distance_mm.shape == (slices, *tiles)
    assert np.isnan(reading.distance_mm).all()
    assert reading.match_codes.shape == (slices, *tiles)
    assert np.all(reading.match_codes == UNAVAILABLE)
    assert reading.why


def test_without_a_geometry_every_slice_and_tile_is_a_silence_that_names_it() -> None:
    # MUST NOT: match a tile when a series cannot be placed along the normal.
    recipient, recipient_geometry = _recipient()
    partner, partner_geometry = _partner()
    reading = line_up(
        recipient, partner, None, partner_geometry, HALF_TILE_MM, HALF_THICKNESS_MM
    )
    assert reading.code == "present"
    assert "recipient" in reading.why and "geometry" in reading.why
    assert math.isnan(reading.normal_angle_deg)
    _assert_silent(reading, SLICES, (2, 2))
    reading = line_up(
        recipient, partner, recipient_geometry, None, HALF_TILE_MM, HALF_THICKNESS_MM
    )
    assert reading.code == "present"
    assert "partner" in reading.why and "geometry" in reading.why
    _assert_silent(reading, SLICES, (2, 2))


def test_a_stack_that_is_not_present_is_the_named_silence() -> None:
    recipient, recipient_geometry = _recipient()
    partner, partner_geometry = _partner()
    absent = _stack("series-bright", "0", None, partner_geometry)
    assert absent.code == "no_stacked_volume"
    with recording() as run_ledger:
        reading = line_up(
            recipient, absent, recipient_geometry, partner_geometry, HALF_TILE_MM, 1.0
        )
    assert reading.code == "no_stacked_volume"
    assert "partner" in reading.why
    _assert_silent(reading, SLICES, (2, 2))
    assert dict(run_ledger.events()[0].counts) == {"recipient": 1, "partner": 0}
    assert dict(run_ledger.events()[1].counts) == {"matched": 0, "in_slab": 0}
    # A recipient without a stack has no grid: every array is empty with the right rank.
    gone = _stack("series-dark", "1", _volume(), None)
    assert gone.code == "geometry_unreadable"
    reading = line_up(gone, partner, None, partner_geometry, HALF_TILE_MM, 1.0)
    assert reading.code == "geometry_unreadable"
    _assert_silent(reading, 0, (0, 0))
    assert reading.partner_tile.dtype == np.int64
    assert reading.match_codes.dtype == np.uint8


def test_a_thickness_the_header_did_not_give_is_a_refusal_per_slice_and_never_a_slab() -> (
    None
):
    recipient, recipient_geometry = _recipient()
    partner, partner_geometry = _partner()
    reading = line_up(
        recipient,
        partner,
        recipient_geometry,
        partner_geometry,
        HALF_TILE_MM,
        float("nan"),
    )
    assert reading.code == "present"
    assert set(reading.slab_codes.tolist()) == {INVALID_SLAB}
    # The nearest partner slice is still named, and the tiles are still matched.
    np.testing.assert_array_equal(reading.partner_slice, np.arange(SLICES))
    assert set(reading.match_codes.ravel().tolist()) == {MATCHED}
    assert math.isnan(shared_half_thickness_mm(()))
    assert math.isnan(shared_half_thickness_mm((None, None)))
    assert math.isnan(shared_half_thickness_mm((2.0, 3.0)))
    assert math.isnan(shared_half_thickness_mm((0.0,)))
    assert math.isnan(shared_half_thickness_mm((-2.0, -2.0)))
    assert math.isnan(shared_half_thickness_mm((float("nan"),)))


def test_an_empty_recipient_tile_is_an_invalid_measurement_never_a_match() -> None:
    volume = _volume().astype(np.float64)
    volume[:, 0:4, 0:4] = np.nan
    recipient_geometry = _geometry()
    recipient = _stack("series-dark", "1", volume, recipient_geometry)
    partner, partner_geometry = _partner()
    reading = line_up(
        recipient,
        partner,
        recipient_geometry,
        partner_geometry,
        HALF_TILE_MM,
        HALF_THICKNESS_MM,
    )
    # The stack still places an empty tile's centre, so the search still runs there; the
    # tile's median is NaN but its centre is finite, and that is the stack's own reading.
    assert reading.match_codes[0, 0, 0] in (MATCHED, INVALID_MATCH)
    assert reading.match_codes[0, 1, 1] == MATCHED


def test_a_geometry_whose_slices_disagree_with_the_stack_is_refused_by_name() -> None:
    recipient, recipient_geometry = _recipient()
    partner, partner_geometry = _partner()
    with pytest.raises(ValueError, match="recipient_geometry_does_not_match_stack"):
        line_up(
            recipient,
            partner,
            _geometry(slices=2),
            partner_geometry,
            HALF_TILE_MM,
            HALF_THICKNESS_MM,
        )
    with pytest.raises(ValueError, match="partner_geometry_does_not_match_stack"):
        line_up(
            recipient,
            partner,
            recipient_geometry,
            _geometry(slices=4),
            HALF_TILE_MM,
            HALF_THICKNESS_MM,
        )


def test_every_array_is_frozen_and_the_callers_stacks_are_unwritten() -> None:
    recipient, recipient_geometry = _recipient()
    partner, partner_geometry = _partner()
    before = (recipient.centres_lps.copy(), partner.centres_lps.copy())
    reading = line_up(
        recipient,
        partner,
        recipient_geometry,
        partner_geometry,
        HALF_TILE_MM,
        HALF_THICKNESS_MM,
    )
    np.testing.assert_array_equal(recipient.centres_lps, before[0])
    np.testing.assert_array_equal(partner.centres_lps, before[1])
    for array in (
        reading.partner_slice,
        reading.slab_codes,
        reading.partner_tile,
        reading.distance_mm,
        reading.match_codes,
    ):
        assert not array.flags.writeable


def test_every_code_is_in_its_vocabulary() -> None:
    recipient, recipient_geometry = _recipient()
    partner, partner_geometry = _partner(slices=2)
    reading = line_up(
        recipient, partner, recipient_geometry, partner_geometry, 0.1, float("nan")
    )
    assert reading.code == "present"
    assert set(reading.slab_codes.tolist()) <= set(range(len(SLAB_CODES)))
    assert set(reading.match_codes.ravel().tolist()) <= set(range(len(MATCH_CODES)))
