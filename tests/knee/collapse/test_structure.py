"""The field's structural reading, both signs (task 7.1).

Written by the lead BEFORE the body. The synthetic planes below are two bright bodies with a dark
band between them on the anatomy weighting, and the same two bodies dark with the band bright on the
fluid-sensitive weighting, so every reading has a known answer and the told sign can be checked.
Every test calls `read_structure` or a pure decision DIRECTLY by name.
"""

import math

import numpy as np
import pytest

from knee.absence import CODES
from knee.collapse.structure import (
    AXIS_CODES,
    SUPERIOR_CODES,
    StructureBars,
    StructureReading,
    axis_code,
    read_structure,
    structure_code,
    superior_code,
)

BARS = StructureBars()
SPACING = (1.0, 1.0)
TILE = 5.0
# A coronal-like header: the column index increases along +x (patient left), the row index
# increases along -z (inferior), the normal is +y. So superior--inferior runs along the ROWS and
# an increasing row index goes inferior: the first row is superior.
CORONAL = np.array([1.0, 0.0, 0.0, 0.0, 0.0, -1.0])
CORONAL_NORMAL = np.array([0.0, 1.0, 0.0])
# An axial-like header: both in-plane directions have no z; the normal carries it.
AXIAL = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
AXIAL_NORMAL = np.array([0.0, 0.0, 1.0])


def _two_bodies(bodies: float, band: float, air: float = 0.0) -> np.ndarray:
    """A 60x60 plane: air everywhere, a 40x30 body from row 10 to 50, column 15 to 45, with a
    band of ten rows (25 to 34, two whole tiles at tile 5) across it and a 3x3 hole at (20, 20)."""
    plane = np.full((60, 60), air)
    plane[10:50, 15:45] = bodies
    plane[25:35, 15:45] = band
    plane[19:22, 19:22] = air
    return plane


ANATOMY = _two_bodies(bodies=100.0, band=5.0)
FLUID = _two_bodies(bodies=5.0, band=100.0)


def _read(
    plane=ANATOMY, orientation=CORONAL, normal=CORONAL_NORMAL, fluid=False, bars=BARS
):
    return read_structure(plane, orientation, normal, SPACING, TILE, fluid, bars)


# ---------------------------------------------------------------- the pure decisions


def test_the_axis_is_the_direction_with_the_largest_z_cosine() -> None:
    assert axis_code(-1.0, 0.0, 0.0) == "rows"
    assert axis_code(0.0, 0.98, 0.2) == "columns"
    assert axis_code(0.0, 0.0, 1.0) == "normal"
    assert axis_code(0.3, -0.3, 0.1) == "ambiguous"
    assert axis_code(0.0, 0.0, 0.0) == "ambiguous"
    assert axis_code(math.nan, 0.0, 1.0) == "unreadable"
    assert axis_code(0.0, math.inf, 0.0) == "unreadable"


def test_superior_is_the_sign_of_z_and_zero_carries_no_direction() -> None:
    assert superior_code(0.7) == "increasing"
    assert superior_code(-0.7) == "decreasing"
    assert superior_code(0.0) == "unreadable"
    assert superior_code(math.nan) == "unreadable"


def test_the_pure_decisions_are_total_and_speak_only_their_vocabulary() -> None:
    for a in (-1.0, 0.0, 0.5, math.nan, math.inf, -math.inf):
        for b in (-1.0, 0.0, 0.5, math.nan):
            for c in (0.0, 1.0, math.nan):
                assert axis_code(a, b, c) in AXIS_CODES
        assert superior_code(a) in SUPERIOR_CODES
    for returned in (True, False):
        for readable in (True, False):
            for places in (-5, -1, 0, 1, 400):
                assert structure_code(returned, readable, places) in CODES


def test_the_structure_code_names_each_silence_apart() -> None:
    assert structure_code(False, False, 0) == "predecessor_absent"
    assert structure_code(True, False, 0) == "invalid_count"
    assert structure_code(True, True, 0) == "predecessor_empty"
    assert structure_code(True, True, 7) == "present"


def test_the_structure_code_never_says_present_without_a_leg() -> None:
    # MUST NOT: a plane that is all air is a reading of emptiness, never a presence.
    assert structure_code(True, True, 0) != "present"
    assert structure_code(True, False, 7) != "present"
    assert structure_code(False, True, 7) != "present"


# ---------------------------------------------------------------- positive, the measurement


def test_air_is_what_connects_to_the_border_and_the_leg_is_closed() -> None:
    reading = _read()
    assert isinstance(reading, StructureReading)
    assert reading.code == "present"
    assert reading.air[0, 0] and reading.air[59, 59] and reading.air[5, 30]
    assert not reading.air[30, 30]
    # the hole at (20, 20) is FILLED: the leg is a contiguous closed body
    assert reading.leg[20, 20]
    assert not reading.air[20, 20]
    assert reading.leg.sum() == 40 * 30
    assert reading.counts["leg_places"] == 40 * 30
    assert reading.counts["air_places"] == 60 * 60 - 40 * 30
    assert reading.counts["unread_places"] == 0
    assert reading.air.dtype == np.bool_ and reading.leg.dtype == np.bool_
    assert not reading.air.flags.writeable and not reading.leg.flags.writeable


def test_the_air_level_is_the_border_rule_with_every_bar_an_argument() -> None:
    border = np.concatenate([ANATOMY[0], ANATOMY[-1], ANATOMY[:, 0], ANATOMY[:, -1]])
    expected = float(np.quantile(border, BARS.border_quantile)) * BARS.level_factor
    assert _read().air_level == expected + BARS.level_offset
    other = StructureBars(level_factor=3.0, level_offset=2.0)
    assert _read(bars=other).air_level == expected / BARS.level_factor * 3.0 + 2.0


def test_the_air_histogram_counts_exactly_the_air_places() -> None:
    reading = _read()
    assert reading.histogram_counts.sum() == reading.counts["air_places"]
    assert reading.histogram_edges.shape == (reading.histogram_counts.shape[0] + 1,)
    assert reading.histogram_counts.shape[0] == BARS.histogram_bins


def test_the_squint_is_read_inside_the_leg_only() -> None:
    reading = _read()
    assert reading.squint is not None
    assert reading.squint.tile_shape_rc == (5, 5)
    assert reading.squint.median.shape == (12, 12)
    # a tile wholly in the air has no finite place: coverage 0, median NaN, not inside
    assert reading.squint.coverage[0, 0] == 0.0
    assert math.isnan(reading.squint.median[0, 0])
    assert not reading.inside[0, 0]
    # a tile wholly in a body: coverage 1, median the body value, inside
    assert reading.squint.coverage[3, 4] == 1.0
    assert reading.squint.median[3, 4] == 100.0
    assert reading.inside[3, 4]
    assert reading.counts["inside_tiles"] == int(reading.inside.sum()) > 0


def test_the_axis_comes_from_the_header_and_the_profile_runs_superior_first() -> None:
    reading = _read()
    assert reading.axis == "rows"
    assert reading.superior == "decreasing"
    # along the rows, superior first: tiles 2..9 are inside; the band is tile 5 and 6
    assert reading.profile.shape == reading.profile_tiles.shape
    assert reading.profile_tiles.tolist() == sorted(reading.profile_tiles.tolist())
    finite = np.isfinite(reading.profile)
    assert finite.any()
    assert reading.profile[reading.dip] == 5.0
    assert reading.profile_tiles[reading.dip] in (5, 6)
    assert set(np.unique(reading.profile[finite]).tolist()) == {5.0, 100.0}


def test_an_increasing_superior_direction_reverses_the_profile() -> None:
    flipped = CORONAL.copy()
    flipped[5] = 1.0  # the row index now increases SUPERIOR
    reading = _read(orientation=flipped)
    assert reading.superior == "increasing"
    assert reading.profile_tiles.tolist() == sorted(
        reading.profile_tiles.tolist(), reverse=True
    )
    assert reading.profile[reading.dip] == 5.0


def test_two_basins_from_two_seeds_and_the_seam_between_them_on_the_anatomy_weighting() -> (
    None
):
    reading = _read(fluid=False)
    assert set(np.unique(reading.basins).tolist()) == {0, 1, 2}
    assert reading.basins.dtype == np.int8
    assert reading.seam.any()
    assert reading.seam.dtype == np.bool_
    # the seam is where the two basins meet, at the band
    rows = np.nonzero(reading.seam)[0]
    assert set(rows.tolist()) <= {4, 5, 6, 7}
    # the upper body is basin 1 and the lower basin 2 (seeds first, then last, along the axis)
    assert reading.basins[3, 4] == 1
    assert reading.basins[8, 4] == 2
    assert not reading.basins[reading.inside == 0].any()


def test_the_told_sign_gives_the_same_basins_on_the_fluid_weighting() -> None:
    """Two weightings, one algorithm, a told sign: with the band bright and the bodies dark, the
    fluid-sensitive flag negates the field and the basins and seam come out the same."""
    anatomy = _read(plane=ANATOMY, fluid=False)
    fluid = _read(plane=FLUID, fluid=True)
    np.testing.assert_array_equal(fluid.basins, anatomy.basins)
    np.testing.assert_array_equal(fluid.seam, anatomy.seam)


def test_the_darkest_fifth_and_the_largest_bodies_are_ranked_not_named() -> None:
    reading = _read()
    inside_values = reading.squint.median[reading.inside]
    assert reading.dark_level == float(np.quantile(inside_values, BARS.dark_quantile))
    assert reading.dark[5, 4] and reading.dark[6, 4]
    assert not reading.dark[3, 4]
    assert reading.bodies.dtype == np.int32
    assert set(np.unique(reading.bodies).tolist()) == {0, 1, 2}
    assert reading.counts["bodies_total"] == 2
    assert reading.bodies[3, 4] in (1, 2) and reading.bodies[8, 4] in (1, 2)
    assert reading.bodies[3, 4] != reading.bodies[8, 4]


def test_every_array_is_handed_on_read_only() -> None:
    reading = _read()
    for name in (
        "air",
        "leg",
        "histogram_counts",
        "histogram_edges",
        "inside",
        "profile",
        "profile_tiles",
        "basins",
        "seam",
        "dark",
        "bodies",
    ):
        assert not getattr(reading, name).flags.writeable, name


# ---------------------------------------------------------------- negative


def test_no_plane_is_a_named_absence_over_empty_arrays() -> None:
    reading = _read(plane=None)
    assert reading.code == "predecessor_absent"
    assert reading.air.shape == reading.leg.shape == (0, 0)
    assert reading.squint is None
    assert reading.profile.shape == (0,) and reading.dip == -1
    assert reading.basins.shape == (0, 0) and reading.seam.shape == (0, 0)
    assert math.isnan(reading.air_level) and math.isnan(reading.dark_level)


def test_a_plane_that_is_all_air_is_empty_never_present() -> None:
    reading = _read(plane=np.zeros((60, 60)))
    assert reading.code == "predecessor_empty"
    assert reading.counts["leg_places"] == 0
    assert reading.profile.shape == (0,)
    assert not reading.basins.any()


def test_a_plane_with_no_finite_place_is_empty_and_nothing_is_substituted() -> None:
    reading = _read(plane=np.full((60, 60), np.nan))
    assert reading.code == "predecessor_empty"
    assert reading.counts["unread_places"] == 60 * 60
    assert reading.counts["leg_places"] == 0
    assert math.isnan(reading.air_level)


def test_it_never_raises_however_malformed_the_arguments() -> None:
    for plane in (object(), "plane", 3, np.zeros(5), np.zeros((2, 2, 2)), b""):
        reading = read_structure(
            plane, CORONAL, CORONAL_NORMAL, SPACING, TILE, False, BARS
        )
        assert reading.code == "invalid_count"
        assert reading.air.shape == (0, 0)
    for orientation, normal in ((None, None), ("x", 3), (np.zeros(2), np.zeros(3))):
        reading = read_structure(
            ANATOMY, orientation, normal, SPACING, TILE, False, BARS
        )
        assert reading.code == "present"
        assert reading.axis == "unreadable" and reading.superior == "unreadable"
    for fluid in (None, "1", 1, 0):
        reading = read_structure(
            ANATOMY, CORONAL, CORONAL_NORMAL, SPACING, TILE, fluid, BARS
        )
        assert reading.code == "present"
        assert reading.basins.shape == reading.inside.shape
        assert not reading.basins.any() and not reading.seam.any()
        assert "fluid" in reading.why


def test_a_missing_header_leaves_the_leg_read_and_the_profile_silent() -> None:
    """MUST NOT: assume image rows are superior--inferior when the header is missing."""
    reading = _read(orientation=None, normal=None)
    assert reading.code == "present"
    assert reading.leg.sum() == 40 * 30
    assert reading.axis == "unreadable"
    assert reading.profile.shape == (0,) and reading.dip == -1
    assert not reading.basins.any() and not reading.seam.any()
    assert "header" in reading.why or "axis" in reading.why


def test_an_axis_along_the_normal_gives_no_in_plane_profile() -> None:
    """MUST NOT: profile an axial plane in-plane; superior--inferior runs through the stack."""
    reading = _read(orientation=AXIAL, normal=AXIAL_NORMAL)
    assert reading.axis == "normal"
    assert reading.superior == "increasing"
    assert reading.profile.shape == (0,) and reading.dip == -1
    assert not reading.basins.any() and not reading.seam.any()
    assert reading.leg.sum() == 40 * 30
    assert "normal" in reading.why


def test_the_values_are_never_filled_only_the_mask() -> None:
    """MUST NOT: fill the hole's VALUES. The leg mask is filled; the plane is untouched and the
    squint still sees the hole's air value inside that tile."""
    plane = _two_bodies(bodies=100.0, band=5.0)
    before = plane.copy()
    reading = _read(plane=plane)
    np.testing.assert_array_equal(plane, before)
    assert reading.leg[20, 20]
    # tile (3, 3) holds rows 15..19 and cols 15..19 -> no hole; tile (4, 4) rows 20..24 cols 20..24
    # holds hole places (20,20),(20,21),(21,20),(21,21): its minimum is the air value, not 100
    assert reading.squint.minimum[4, 4] == 0.0


def test_no_record_field_or_code_names_anatomy() -> None:
    reading = _read()
    words = " ".join(
        [reading.code, reading.why, reading.axis, reading.superior]
        + list(reading.counts)
        + list(StructureReading.__slots__)
        + list(AXIS_CODES)
        + list(SUPERIOR_CODES)
    ).lower()
    for word in ("femur", "tibia", "patella", "bone", "cartilage", "meniscus", "joint"):
        assert word not in words


def test_an_unknown_bar_cannot_be_smuggled_in_as_a_literal() -> None:
    """MUST NOT: read a bar from anywhere but the arguments. Changing a bar changes the reading."""
    narrow = _read(bars=StructureBars(dark_quantile=0.05))
    wide = _read(bars=StructureBars(dark_quantile=0.5))
    assert narrow.dark_level <= wide.dark_level
    assert narrow.dark.sum() <= wide.dark.sum()
    fewer = _read(bars=StructureBars(bodies=1))
    assert set(np.unique(fewer.bodies).tolist()) == {0, 1}
    assert fewer.counts["bodies_total"] == 2


@pytest.mark.parametrize("fluid", [True, False])
def test_the_reading_is_deterministic(fluid) -> None:
    plane = FLUID if fluid else ANATOMY
    first = _read(plane=plane, fluid=fluid)
    second = _read(plane=plane, fluid=fluid)
    np.testing.assert_array_equal(first.basins, second.basins)
    np.testing.assert_array_equal(first.profile, second.profile)
    assert first.counts == second.counts
