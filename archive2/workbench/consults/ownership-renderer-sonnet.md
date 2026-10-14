"""Ownership picture panels: the residual map, arranged from the run's own values.

Implements OpenSpec every-stage-renders task1.3 under thesis §13.7: a picture
arranges the run's values, the production run imports no drawing code, and a
renderer may not measure, threshold, count or infer. This module therefore
only carries the ownership reading's attributes across unchanged. It does no
arithmetic, validation, copying or I/O.

The residual map is the readonly boolean (R, C) mask of places that were read
and that no object claimed. It is shown beside the claims mask. A place whose
state could not be read is not residual. Residual means "read and unclaimed",
while unread means "no reading exists". The reading records only how many
places are unavailable (``unavailable_places``), not where they are, so no
unread mask exists here and none is invented. The unavailable count is
carried as the reading computed it.

When the reading is missing or malformed, the masks are empty (0, 0) arrays
and ``code`` names the reason. When ``code`` is predecessor_empty, the masks
are still real masks.
"""

from dataclasses import dataclass

import numpy as np

from knee.ownership.claims import OwnershipReading


@dataclass(frozen=True, slots=True)
class OwnershipPanels:
    """Values arranged for the ownership picture, exactly as the reading holds them.

    ``claims`` and ``residual`` are the reading's own boolean (R, C) arrays,
    passed through by identity. ``residual`` marks places that were read and
    left unclaimed. Places that could not be read are not residual. Only their
    count, ``unavailable_places``, is known, so no mask of them is carried.
    ``code`` and ``why`` are the reading's authoritative status and reason.
    The counts are the reading's computed values, never recomputed here.
    """

    code: str
    why: str
    claims: np.ndarray
    residual: np.ndarray
    claimed_places: int
    residual_places: int
    unavailable_places: int
    objects: int


def panels(reading: OwnershipReading) -> OwnershipPanels:
    """Return the reading's eight attributes unchanged as ownership panels.

    The residual map is read straight from ``reading.residual``. Unread
    places are not residual and are reported only through the reading's
    ``unavailable_places`` count. Nothing is measured, thresholded, counted,
    inferred, copied or validated here.
    """
    return OwnershipPanels(
        code=reading.code,
        why=reading.why,
        claims=reading.claims,
        residual=reading.residual,
        claimed_places=reading.claimed_places,
        residual_places=reading.residual_places,
        unavailable_places=reading.unavailable_places,
        objects=reading.objects,
    )