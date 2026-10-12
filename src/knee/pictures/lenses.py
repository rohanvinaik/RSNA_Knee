"""Arrange already selected native-plane lens values without interpreting them.

OpenSpec every-stage-renders tasks 2.4 instantiate the static-middle language of
thesis §7 and the picture-layer boundary of §13.7. The workbench writer selects
the native plane from the stage's full-volume maps before calling this adapter;
this module neither slices a volume nor measures a place.

``codes`` is the stage's uint8 map indexing ``DIGIT_CODES``. ``digits`` is its
int8 map of -1, 0 and +1, with 2 naming silence rather than middle. ``code``,
``why``, ``low_edge``, ``high_edge`` and ``normalisation`` are the stage's saved
values. The stage records normalisation as ``none``. No cross-acquisition
correspondence or anatomical class is asserted here.

Every field passes through unchanged, including both arrays by identity. This
adapter performs no validation, coercion, counting, measurement or decision.
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class LensPanels:
    """The selected native-plane reading's unchanged values for display."""

    code: str
    why: str
    codes: np.ndarray
    digits: np.ndarray
    low_edge: float | None
    high_edge: float | None
    normalisation: str


def panels(
    code: str,
    why: str,
    codes: np.ndarray,
    digits: np.ndarray,
    low_edge: float | None,
    high_edge: float | None,
    normalisation: str,
) -> LensPanels:
    """Hand on the supplied plane and metadata without changing any field."""
    return LensPanels(
        code=code,
        why=why,
        codes=codes,
        digits=digits,
        low_edge=low_edge,
        high_edge=high_edge,
        normalisation=normalisation,
    )
