"""What THE OBJECTS stage resolved, drawn: territories, the conversation, and the subdivisions.

Five panels, left to right, which are the stage's own steps in order:

    1. the original B1 territories, each a label, over the acquired plane
    2. the donor's bounded dark bands transported into this series' frame, coloured by what this
       series' OWN plane said at the same place
    3. the native outcomes with the derived intersections marked -- where two independent readings
       of the same knee concur
    4. the CONCURRENT subdivision: territories parted only where both readings agreed
    5. the CONDITIONAL subdivision: parted also where the donor claimed a band and this series was
       silent. Contradiction parts nothing, in either.

Panels 4 and 5 are shown side by side on purpose. Their difference is not noise to be collapsed: it
is the measured size of what one view asserts where its partner says nothing, and the stage keeps
both readings rather than averaging them into one verdict.

Every panel arranges values `knee.objects` already holds. Nothing here measures, thresholds,
segments or rasterises: see this package's docstring on why a renderer that computes is a bug and is
evidence against the stage rather than the drawing.

Units: panels are in the series' own stored values and native (row, column) places. Arrays out are
float64 or int32 as stated, NaN or 0 where a place was not read or not claimed -- an unclaimed place
is never drawn as background.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class ObjectPanels:
    """One series' object parse, as arrays. A caller writes them; this makes them.

    acquired: (rows, columns) float64, the plane as read. territories: (rows, columns) int32, B1's
    labels, 0 where unseeded. donor_points/donor_codes: (P, 2) float64 places and (P,) uint8 named
    exchange codes for the transported bands. traces: (P, 2) float64, the derived midpoint trace,
    NaN where no unique bounded interval was found. concurrent/conditional: (rows, columns) int32
    child labels. parents: (children + 1,) int32 mapping each child to its original territory, so a
    subdivision is always traceable back to what it parted.
    """

    acquired: np.ndarray
    territories: np.ndarray
    donor_points: np.ndarray
    donor_codes: np.ndarray
    traces: np.ndarray
    concurrent: np.ndarray
    conditional: np.ndarray
    concurrent_parents: np.ndarray
    conditional_parents: np.ndarray


def panels(
    acquired: np.ndarray,
    territories: np.ndarray,
    donor_points: np.ndarray,
    donor_codes: np.ndarray,
    traces: np.ndarray,
    concurrent: np.ndarray,
    conditional: np.ndarray,
    concurrent_parents: np.ndarray,
    conditional_parents: np.ndarray,
) -> ObjectPanels:
    """Arrange the object stage's values into its five panels.

    Every argument is a value the stage computed: `territories` are B1's labels, `donor_points` and
    `donor_codes` the transported bands with their named outcomes, and the two subdivisions with
    their parent maps. This function only shapes them.
    """
    shaped = ObjectPanels(
        acquired=np.asarray(acquired, dtype=np.float64),
        territories=np.asarray(territories, dtype=np.int32),
        donor_points=np.asarray(donor_points, dtype=np.float64),
        donor_codes=np.asarray(donor_codes, dtype=np.uint8),
        traces=np.asarray(traces, dtype=np.float64),
        concurrent=np.asarray(concurrent, dtype=np.int32),
        conditional=np.asarray(conditional, dtype=np.int32),
        concurrent_parents=np.asarray(concurrent_parents, dtype=np.int32),
        conditional_parents=np.asarray(conditional_parents, dtype=np.int32),
    )
    if shaped.territories.shape != shaped.acquired.shape:
        raise ValueError("territories_do_not_match_the_plane")
    if shaped.concurrent.shape != shaped.acquired.shape:
        raise ValueError("concurrent_subdivision_does_not_match_the_plane")
    if shaped.conditional.shape != shaped.acquired.shape:
        raise ValueError("conditional_subdivision_does_not_match_the_plane")
    if len(shaped.donor_codes) != len(shaped.donor_points):
        raise ValueError("donor_codes_do_not_match_their_places")
    return shaped


@dataclass(frozen=True, slots=True)
class CensusPanels:
    """The boundary census drawn: what bounds each territory, and the relief between neighbours.

    territories: (rows, columns) int32, B1's labels. edge_points/edge_kinds: (E, 2) float64 places
    and (E,) uint8 named kinds, so each edge is drawn in the colour of what lies ACROSS it rather
    than by which side owns it. edges_by_kind: (T, 5) int64, each territory's loop composition --
    the share resting on a measured dark reading versus on a constructed divide. saddle_mm (Q,) and
    prominence_mm (Q, 2) with pair_codes (Q,) are the relief per touching pair, NaN where the pair
    was not read, so an unread pair is drawn as absent and never as a zero.
    """

    territories: np.ndarray
    edge_points: np.ndarray
    edge_kinds: np.ndarray
    edges_by_kind: np.ndarray
    saddle_mm: np.ndarray
    prominence_mm: np.ndarray
    pair_codes: np.ndarray


def census_panels(
    territories: np.ndarray,
    edge_points: np.ndarray,
    edge_kinds: np.ndarray,
    edges_by_kind: np.ndarray,
    saddle_mm: np.ndarray,
    prominence_mm: np.ndarray,
    pair_codes: np.ndarray,
) -> CensusPanels:
    """Arrange the census's values into its four panels.

    Every argument is a value `knee.objects.boundaries` already returned: B1's labels and edges,
    the per-territory composition, and the per-pair saddle, prominences and codes. This shapes
    them and checks they agree; it measures nothing, and it never maps a pair back onto pixels,
    because the stage does not compute that and a renderer may not invent it.
    """
    shaped = CensusPanels(
        territories=np.asarray(territories, dtype=np.int32),
        edge_points=np.asarray(edge_points, dtype=np.float64),
        edge_kinds=np.asarray(edge_kinds, dtype=np.uint8),
        edges_by_kind=np.asarray(edges_by_kind, dtype=np.int64),
        saddle_mm=np.asarray(saddle_mm, dtype=np.float64),
        prominence_mm=np.asarray(prominence_mm, dtype=np.float64),
        pair_codes=np.asarray(pair_codes, dtype=np.uint8),
    )
    if len(shaped.edge_kinds) != len(shaped.edge_points):
        raise ValueError("edge_kinds_do_not_match_their_places")
    if shaped.edges_by_kind.ndim != 2:
        raise ValueError("edges_by_kind_is_one_row_per_territory")
    if shaped.prominence_mm.shape != (len(shaped.saddle_mm), 2):
        raise ValueError("prominences_do_not_match_their_pairs")
    if len(shaped.pair_codes) != len(shaped.saddle_mm):
        raise ValueError("pair_codes_do_not_match_their_pairs")
    return shaped


def measured_share(panels_: CensusPanels) -> np.ndarray:
    """Each territory's share of boundary facing a measured dark reading, (T,) float64.

    A COUNT of values the stage already produced, divided by their own total: the fraction of a
    loop that rests on a measurement rather than on a constructed divide. A territory with no edges
    reads NaN, never 0 -- an absent loop is not a loop resting on nothing.
    """
    counts = panels_.edges_by_kind
    totals = counts.sum(axis=1)
    out = np.full(len(counts), np.nan, dtype=np.float64)
    seen = totals > 0
    out[seen] = counts[seen, 0] / totals[seen]
    return out


def parted_more_by(panels_: ObjectPanels) -> int:
    """How many more children the conditional subdivision made than the concurrent one.

    This is a COUNT of values the stage already produced, not a measurement of the image: the
    difference is what one view asserted where its partner was silent, and reporting it is how the
    picture carries that quantity rather than hiding it in a colour.
    """
    return int(len(panels_.conditional_parents) - len(panels_.concurrent_parents))
