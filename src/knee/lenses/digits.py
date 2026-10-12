"""One place against a pair of static edges in its acquisition, never a tissue verdict.

Thesis §7.2 and the founder's 2026-10-11 ruling (chapters/03-lenses/teachings.md):
the middle is two tercile edges; both edges belong to the middle row. This replaces
the withdrawn witness-middle/spread-band proposal under every-stage-renders task 2.1.
Edges and the population bar are supplied, never selected by this decision. Silence
is distinct from the measured middle, and no spatial normalisation is asserted here.
"""

from __future__ import annotations

import math

DIGIT_CODES = (
    "below",
    "at",
    "above",
    "place_unread",
    "no_edges",
    "population_too_small",
    "invalid_measurement",
)
READ_CODES = ("below", "at", "above")


def digit_code(
    place_value: float | None,
    low_edge: float | None,
    high_edge: float | None,
    population_count: int,
    minimum_population: int,
) -> str:
    """Name the reading, with a distinct remedy for each silence; total on typed arguments.

    Invalid counts or reversed finite edges outrank absence. An absent edge pair
    outranks an unread place: there is no standard against which to place it.
    Equal edges are a legitimate middle containing that one value. None/NaN/infinity
    supply no reading. No witness, noise spread or learned parameter is consulted.

    post: __return__ in DIGIT_CODES
    post: __return__ not in READ_CODES or population_count >= minimum_population
    post: __return__ not in READ_CODES or population_count > 0
    """
    if population_count < 0 or minimum_population < 0:
        return "invalid_measurement"
    low_ok = low_edge is not None and math.isfinite(low_edge)
    high_ok = high_edge is not None and math.isfinite(high_edge)
    if low_ok and high_ok and low_edge > high_edge:
        return "invalid_measurement"
    if population_count == 0 or not low_ok or not high_ok:
        return "no_edges"
    if population_count < minimum_population:
        return "population_too_small"
    if place_value is None or not math.isfinite(place_value):
        return "place_unread"
    if place_value < low_edge:
        return "below"
    if place_value > high_edge:
        return "above"
    return "at"


def is_read(code: str) -> bool:
    """Whether a digit code carries a reading, including the middle, rather than silence.

    post: __return__ == (code in ('below', 'at', 'above'))
    """
    return code in READ_CODES
