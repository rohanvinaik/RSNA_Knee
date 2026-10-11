"""Intent tests for the slab rule, both signs.

Positive: what the rule must do -- a place inside a slab IS measured, and the gap IS silence.
Negative: what it must never do -- claim the gap as measured, or let spacing stand in for thickness.

Every test calls the function DIRECTLY. Detective routes by static path, so a local helper would
make the test invisible to the tracer (measured 2026-10-11 on digit_code).
"""

import math

import pytest

from knee.lenses.slabs import (
    SLAB_CODES,
    gap_fraction,
    half_thickness,
    slab_code,
    was_measured,
)

# A routine knee acquisition: 3.5 mm slabs on a 4.0 mm pitch, so a 0.5 mm gap.
THICK = 3.5
PITCH = 4.0


def test_every_outcome_is_a_named_code() -> None:
    assert len(set(SLAB_CODES)) == len(SLAB_CODES)
    assert slab_code(0.0, THICK, PITCH, True) in SLAB_CODES


def test_a_place_inside_the_slab_is_measured() -> None:
    """The load-bearing fact: a voxel measures its whole slab, so this is not interpolation."""
    assert slab_code(0.0, THICK, PITCH, True) == "measured"
    assert slab_code(1.7, THICK, PITCH, True) == "measured"
    assert slab_code(-1.7, THICK, PITCH, True) == "measured"


def test_the_slab_edge_belongs_to_measured() -> None:
    """Exactly half a thickness out is still inside the slab the voxel integrated."""
    assert slab_code(THICK / 2.0, THICK, PITCH, True) == "measured"
    assert slab_code(-THICK / 2.0, THICK, PITCH, True) == "measured"


def test_a_place_in_the_gap_is_silence_and_never_a_reading() -> None:
    """The acquisition did not measure it. That is nothing said, not a dark or middle reading."""
    assert slab_code(1.9, THICK, PITCH, True) == "in_gap"
    assert slab_code(-1.9, THICK, PITCH, True) == "in_gap"
    assert not was_measured(slab_code(1.9, THICK, PITCH, True))


def test_the_gap_must_never_be_claimed_as_measured() -> None:
    """MUST-NOT. Using SpacingBetweenSlices as the half-width would do exactly this.

    Half the pitch is 2.0 mm; half the thickness is 1.75 mm. A place at 1.9 mm is in the gap, and a
    rule written on spacing would have called it measured and read a value that was never acquired.
    """
    assert slab_code(1.9, THICK, PITCH, True) != "measured"
    assert half_thickness(THICK) < PITCH / 2.0


def test_a_farther_place_belongs_to_a_neighbouring_slice() -> None:
    """Distinct from the gap: another slice may well have measured it, so the caller asks that one."""
    assert slab_code(2.5, THICK, PITCH, True) == "not_this_slice"
    assert slab_code(-9.0, THICK, PITCH, True) == "not_this_slice"


def test_outside_the_field_of_view_no_slice_will_help() -> None:
    """A series-level fact: the in-plane rectangle is the same for every slice."""
    assert slab_code(0.0, THICK, PITCH, False) == "outside_frame"
    assert slab_code(99.0, THICK, PITCH, False) == "outside_frame"
    assert not was_measured(slab_code(0.0, THICK, PITCH, False))


def test_overlapping_slabs_have_no_gap_to_fall_into() -> None:
    """Thickness exceeding spacing is a real acquisition, and then `in_gap` is unreachable."""
    for offset in (0.0, 1.0, 2.0, 2.49):
        assert slab_code(offset, 6.0, 5.0, True) == "measured"
    assert slab_code(2.6, 6.0, 5.0, True) == "measured"
    assert gap_fraction(6.0, 5.0) == 0.0


def test_the_three_silences_are_kept_apart() -> None:
    """MUST-NOT: fuse outcomes that have different remedies (law 3)."""
    outside = slab_code(0.0, THICK, PITCH, False)
    gap = slab_code(1.9, THICK, PITCH, True)
    neighbour = slab_code(3.0, THICK, PITCH, True)
    assert len({outside, gap, neighbour}) == 3


def test_geometry_that_cannot_be_an_acquisition_is_refused() -> None:
    assert slab_code(0.0, 0.0, PITCH, True) == "invalid_geometry"
    assert slab_code(0.0, -1.0, PITCH, True) == "invalid_geometry"
    assert slab_code(0.0, THICK, 0.0, True) == "invalid_geometry"
    assert slab_code(0.0, THICK, -1.0, True) == "invalid_geometry"
    assert slab_code(math.nan, THICK, PITCH, True) == "invalid_geometry"
    assert slab_code(math.inf, THICK, PITCH, True) == "invalid_geometry"
    assert slab_code(0.0, math.nan, PITCH, True) == "invalid_geometry"
    assert slab_code(0.0, THICK, math.nan, True) == "invalid_geometry"


def test_invalid_geometry_outranks_being_outside_the_frame() -> None:
    """A measurement that could not have been made is not a statement about where the place is."""
    assert slab_code(0.0, -1.0, PITCH, False) == "invalid_geometry"


def test_a_vanishingly_thin_slab_must_not_be_refused() -> None:
    """MUST-NOT: refuse a real acquisition. A thin slice is a sharp instrument, not an invalid one."""
    assert slab_code(0.0, 0.05, PITCH, True) == "measured"
    assert slab_code(0.0, 1e-6, PITCH, True) == "measured"


def test_a_fine_slice_pitch_must_not_be_refused() -> None:
    """MUST-NOT: refuse a real acquisition.

    A sub-millimetre pitch is a 3D or high-resolution acquisition, not an invalid one. A guard at
    `spacing_mm <= 0.1` would silently refuse every one of them.
    """
    assert slab_code(0.0, 0.05, 0.05, True) == "measured"
    assert slab_code(0.0, 1e-5, 1e-5, True) != "invalid_geometry"


def test_a_slice_must_not_adjudicate_beyond_its_own_half_of_the_pitch() -> None:
    """MUST-NOT: claim a place that belongs to a neighbour.

    Half the centre-to-centre spacing is exactly where the next slice's claim begins. A boundary set
    any wider -- `spacing_mm / 1.9` rather than `/ 2.0` -- lets this slice answer for places the
    neighbour is nearer to, which is this slice speaking about a reading it has no standing to make.
    """
    # Pitch 4.0: this slice's share ends at 2.0, and the neighbour at 4.0 is nearer to 2.05.
    assert slab_code(2.05, THICK, PITCH, True) == "not_this_slice"
    assert slab_code(-2.05, THICK, PITCH, True) == "not_this_slice"
    # Exactly at the halfway point the slice still answers; one step past it defers.
    assert slab_code(PITCH / 2.0, THICK, PITCH, True) == "in_gap"
    assert slab_code(PITCH / 2.0 + 1e-6, THICK, PITCH, True) == "not_this_slice"


def test_a_thickness_whose_half_cannot_be_represented_is_refused() -> None:
    """MUST-NOT: claim a slab extent the machine cannot hold.

    Found by CrossHair, not by mutation: `half_thickness(5e-324)` returns 0.0, because the smallest
    subnormal double halves to zero. A slab with no representable half-extent would measure only the
    exact centre plane, which is a false precision about where the instrument looked, so the
    geometry is refused instead.
    """
    assert half_thickness(5e-324) == 0.0
    assert slab_code(0.0, 5e-324, PITCH, True) == "invalid_geometry"
    assert slab_code(0.0, 5e-324, 5e-324, True) == "invalid_geometry"
    # A thickness one step larger still has a representable half, and is a real acquisition.
    assert slab_code(0.0, 1e-300, PITCH, True) == "measured"


def test_a_non_finite_pitch_is_refused_rather_than_returning_nan() -> None:
    """MUST-NOT: let a NaN into a conjunction's weighting.

    Found by CrossHair: `gap_fraction(1.0, inf)` returned NaN, because `inf > 0` satisfies a bare
    positivity precondition and `inf / inf` is NaN. A NaN gap fraction is neither a gap nor an
    absence of one, and it would propagate silently.

    The refusal must also NAME what went wrong. A bare or empty message would leave a caller with a
    raise it cannot act on, which is the same fault as a bool where a named code belongs (law 3).
    """
    for thickness, spacing in (
        (1.0, math.inf),
        (math.inf, 4.0),
        (math.nan, 4.0),
        (1.0, math.nan),
    ):
        with pytest.raises(ValueError, match="invalid_slab_geometry"):
            gap_fraction(thickness, spacing)


def test_was_measured_names_exactly_the_one_reading() -> None:
    for name in SLAB_CODES:
        assert was_measured(name) == (name == "measured")


def test_the_gap_fraction_is_the_share_the_acquisition_missed() -> None:
    assert gap_fraction(THICK, PITCH) == pytest.approx(0.125)
    assert gap_fraction(4.0, 4.0) == 0.0
    assert gap_fraction(1.0, 4.0) == pytest.approx(0.75)


def test_the_gap_fraction_is_never_one_because_a_slab_has_extent() -> None:
    """MUST-NOT: report that an acquisition measured nothing at all. It always measured its slabs."""
    assert 0.0 <= gap_fraction(1e-9, 1000.0) < 1.0


def test_half_thickness_is_the_slabs_half_extent() -> None:
    assert half_thickness(THICK) == pytest.approx(1.75)
    assert half_thickness(1e-6) > 0.0
