"""The ternary digit: one place's standing against ONE NAMED WITNESS, in one acquisition.

This is the whole of what a lens decides, and it decides nothing about anatomy. A row is a PAIR
(acquisition, witness) -- "above fat on PD-FS", "at muscle on T1" -- never a place against a
series-wide middle. Both second readers reached that independently on 2026-10-11:

  - a series-wide median is dominated by whichever tissue is largest and drifts with body habitus,
    so it is comparable to nothing;
  - and a per-series scalar is still an ABSOLUTE LEVEL WITH RESPECT TO POSITION, because a surface
    coil is brightest at the periphery and dimmest centrally. That is the mechanism that killed four
    intensity instruments on this corpus, in a new coat.

THE BAND CARRIES THE WITNESS'S OWN SPREAD. The question is not "is this place distinguishable from a
number" but "is this place indistinguishable from the witness TISSUE", and the witness tissue has its
own spread -- bias field, partial volume, genuine heterogeneity. So the half-width is

    band = k * sqrt(place_sigma^2 + witness_spread^2)

with `k` the one recorded argument. In flicker units `place_sigma` is 1.0 by construction (the Rician
variance-stabilising transform makes one flicker one sigma at any intensity), so the witness's spread
is what actually sets the band. A band from voxel noise alone would make "at the middle" nearly empty
at the SNR these acquisitions carry -- a degenerate ternary.

WHAT THE DIGITS MEAN (SS1.12, and the founder: "'Silence' is meaningful, not a default negative"):

    below / at / above   a reading was made. `at` is A READING AT ITS MIDDLE, not silence.
    place_unread         the place carries no finite value. Silence, never a negative.
    no_witness           this acquisition admitted no witness of this name. The row is UNWRITTEN;
                         it is not a measured middle, and must never be summed as one.
    witness_too_small    a witness was found but too few places to locate it. Silence with a reason.
    invalid_measurement  the arguments cannot be a measurement at all.

Nothing here is tuned to anything: `band_k` and `minimum_witness` are ARGUMENTS the caller records
before the run that judges them (project law 4).
"""

from __future__ import annotations

import math

DIGIT_CODES = (
    "below",
    "at",
    "above",
    "place_unread",
    "no_witness",
    "witness_too_small",
    "invalid_measurement",
)

READ_CODES = ("below", "at", "above")


def band_width(place_sigma: float, witness_spread: float, band_k: float) -> float:
    """The half-width that separates `at` from `below`/`above`, in the place's own units.

    Both spreads enter, because the comparison's resolution is set by the place's noise AND by how
    tightly the witness population locates its own middle.

    pre: band_k > 0
    pre: place_sigma >= 0
    pre: witness_spread >= 0
    post: __return__ >= 0
    """
    return band_k * math.sqrt(
        place_sigma * place_sigma + witness_spread * witness_spread
    )


def digit_code(
    place_value: float,
    witness_middle: float,
    place_sigma: float,
    witness_spread: float,
    band_k: float,
    witness_count: int,
    minimum_witness: int,
) -> str:
    """Name one place's standing against one witness. Total over its arguments; pure.

    `place_value` and `witness_middle` are in the same stabilised units. A non-finite
    `place_value` is silence about the PLACE; a non-finite `witness_middle` is silence about the
    WITNESS, and the two are different facts with different remedies, so they get different codes.

    post: __return__ in ('below', 'at', 'above', 'place_unread', 'no_witness', 'witness_too_small', 'invalid_measurement')
    post: __return__ not in ('below', 'at', 'above') or witness_count >= minimum_witness
    """
    if (
        not math.isfinite(band_k)
        or band_k <= 0.0
        or not math.isfinite(place_sigma)
        or place_sigma <= 0.0
        or not math.isfinite(witness_spread)
        or witness_spread < 0.0
        or witness_count < 0
        or minimum_witness < 0
    ):
        return "invalid_measurement"
    # The witness is read first: a place cannot be placed against a standard that is not there, and
    # an absent standard is a different fact from an unread place.
    if witness_count <= 0 or not math.isfinite(witness_middle):
        return "no_witness"
    if witness_count < minimum_witness:
        return "witness_too_small"
    if not math.isfinite(place_value):
        return "place_unread"
    band = band_width(place_sigma, witness_spread, band_k)
    difference = place_value - witness_middle
    if difference < -band:
        return "below"
    if difference > band:
        return "above"
    return "at"


def is_read(code: str) -> bool:
    """Whether a digit code carries a reading at all.

    The one place the distinction is made, so no caller re-derives it and drifts. A code that is not
    read is never counted toward a middle, a share or a conjunction.

    post: __return__ == (code in ('below', 'at', 'above'))
    """
    return code in READ_CODES
