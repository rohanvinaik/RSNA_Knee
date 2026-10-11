"""Did THIS slice measure THAT place? The through-plane rule, and where silence comes from.

WHY THIS EXISTS. A row of the bundle is a conjunction across acquisitions -- "fat is bright on
non-FS AND dark on FS" -- and a conjunction is only evidence if its readings concern the same
tissue. Two series of different orientation sample different physical planes, so a place resolved in
one may fall between slices in another. The lead's first design asked whether a common grid was
needed. It is not, and the reason is a fact about the instrument rather than a convention:

    A 2D multi-slice series is not a lattice of points. It is a stack of SLABS.

A voxel in a 3.5 mm slice is a measurement of the whole 3.5 mm slab, not of its centre plane. So
when a place falls inside some slab, that voxel IS a measurement of that place and reading it is not
interpolation at all. When it falls in the inter-slice gap, the acquisition genuinely did not measure
it, and the row is SILENT. Nothing is invented and nothing is resampled; the instrument's own
geometry says where it was blind.

That is the thesis's law made geometric (SS1.12, and the founder: "'Silence' is meaningful, not a
default negative score"). A gap is not a dark reading and not a middle reading. It is nothing said,
and it must stay distinguishable from every reading all the way to the output.

THICKNESS, NEVER SPACING. `SliceThickness` is the slab's extent; `SpacingBetweenSlices` is
centre-to-centre and INCLUDES the gap. Using spacing as the half-width would silently claim the gap
as measured, which is exactly the error this module exists to prevent. Both are read here, because
their difference is what a gap IS, but only thickness bounds the slab.

WHAT A SUPPORT IS WORTH. A slab reading is weaker than a grid-identical one: a place 0.4 mm wide
read by a 3.5 mm slab is being averaged against everything else in that slab, so a structure thinner
than the slab reads intermediate in that lens even where it is pure in another. This module reports
WHICH it is; what that costs a conjunction is the caller's to weigh, and must never be silently
averaged away.
"""

from __future__ import annotations

import math

SLAB_CODES = (
    "measured",
    "in_gap",
    "not_this_slice",
    "outside_frame",
    "invalid_geometry",
)


def half_thickness(thickness_mm: float) -> float:
    """The slab's half-extent: the largest offset a place may have and still be measured.

    The post-condition is `>= 0`, not `> 0`, and that is a measured fact rather than caution:
    CrossHair found that `half_thickness(5e-324)` returns 0.0, because the smallest subnormal double
    halves to zero. A positive thickness can therefore have a half-extent that is not representable,
    and `slab_code` refuses that geometry rather than claiming an extent it cannot hold.

    pre: thickness_mm > 0
    post: __return__ >= 0
    """
    return thickness_mm / 2.0


def slab_code(
    offset_mm: float,
    thickness_mm: float,
    spacing_mm: float,
    in_plane: bool,
) -> str:
    """Name what one slice did about one place. Total over its arguments; pure.

    `offset_mm` is the place's signed distance from this slice's centre plane along the slice
    normal -- `dot(place - centre, normal)` -- and only its magnitude matters here. `in_plane` says
    the place falls inside the slice's in-plane rectangle, which is a property of the field of view
    and so is the same for every slice of the series.

    The three not-measured outcomes are kept apart because they have different remedies: a place
    `outside_frame` is outside the acquisition entirely and no slice will help; a place `in_gap` sits
    between this series' slabs and no slice of THIS series measured it; a place `not_this_slice`
    belongs to a neighbour, and the caller should ask that one instead.

    Slabs may overlap (thickness exceeding spacing is a real acquisition), in which case `in_gap` is
    simply unreachable -- an overlapping stack has no gap to fall into.

    post: __return__ in ('measured', 'in_gap', 'not_this_slice', 'outside_frame', 'invalid_geometry')
    post: __return__ != 'measured' or (in_plane and abs(offset_mm) <= thickness_mm / 2.0)
    post: __return__ != 'in_gap' or in_plane
    """
    if (
        not math.isfinite(offset_mm)
        or not math.isfinite(thickness_mm)
        or not math.isfinite(spacing_mm)
        or spacing_mm <= 0.0
        # Subsumes `thickness_mm <= 0.0`, which was removed as dead: half_thickness is t/2.0, so
        # this is true for every non-positive thickness AND for a positive one whose half-extent
        # underflows to zero. Such a slab cannot be described, so the geometry is refused rather
        # than silently measuring only the centre plane. The underflow was found by CrossHair at
        # 5e-324, not by mutation -- the suite had killed every mutant at the time.
        or half_thickness(thickness_mm) <= 0.0
    ):
        return "invalid_geometry"
    if not in_plane:
        return "outside_frame"
    distance = abs(offset_mm)
    if distance <= half_thickness(thickness_mm):
        return "measured"
    # Beyond the slab but inside this slice's share of the stack: the gap between slabs. Half the
    # centre-to-centre spacing is where a neighbour's claim begins.
    if distance <= spacing_mm / 2.0:
        return "in_gap"
    return "not_this_slice"


def was_measured(code: str) -> bool:
    """Whether a slab code means the acquisition read this place at all.

    The one place the distinction is made, so no caller re-derives it and drifts. Everything that is
    not `measured` is silence, and silence never becomes a value.

    post: __return__ == (code == 'measured')
    """
    return code == "measured"


def gap_fraction(thickness_mm: float, spacing_mm: float) -> float:
    """How much of the stack this series did not measure, as a fraction of its own pitch.

    Zero when the slabs touch or overlap. This is a property of the ACQUISITION, not of any place,
    and it belongs beside a conjunction as the prior probability that a foreign place falls into
    nothing. It is a measurement and decides nothing.

    `spacing_mm` must be FINITE, which positivity does not imply: CrossHair found that
    `gap_fraction(1.0, inf)` returns NaN, because `inf > 0` satisfies a bare positivity precondition
    and `inf / inf` is NaN. A NaN here would enter a conjunction's weighting as neither a gap nor an
    absence of one. The guard is in the code and not only in the contract, because this sits on a
    measurement path where a header supplies the number.

    pre: thickness_mm > 0
    pre: spacing_mm > 0
    pre: math.isfinite(thickness_mm)
    pre: math.isfinite(spacing_mm)
    post: 0.0 <= __return__ < 1.0
    """
    if not math.isfinite(thickness_mm) or not math.isfinite(spacing_mm):
        raise ValueError("invalid_slab_geometry")
    if thickness_mm >= spacing_mm:
        return 0.0
    return (spacing_mm - thickness_mm) / spacing_mm
