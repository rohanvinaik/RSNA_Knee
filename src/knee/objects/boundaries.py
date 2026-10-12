"""What a resolved territory is bounded BY, and how far each centre stands above its valleys.

THE ROLE THIS FILLS. §6 reads an <object> as a relief: "Read as a relief of light, a nucleus is a
peak. Its border is where the peak falls to its surroundings, and a valley is where one <object>
ends and the next begins." The knee re-derives that relief as the distance transform, since a bone
is deepest at its centre rather than brightest (docs/OBJECT_MODEL.md). This module measures the two
things that reading makes available and nothing else:

    WHAT BOUNDS IT    every edge of a territory, counted by what lies across it -- measured dark,
                      a peer territory, missing acquisition, the frame, or unseeded material. B1
                      already names each edge (`interiors.EDGE_KINDS`); this counts them per
                      territory, because a loop's composition is what says how much of it rests on
                      a measurement and how much on a constructed divide.
    HOW HIGH IT STANDS  for every pair of territories that touch, the highest pass between them
                      (the saddle) and each centre's height above it. §9.1 words a candidate noise
                      by "no bright center standing above its valley", so this is that quantity,
                      per pair, in millimetres.

WHAT THIS MODULE MUST NOT DO, and does not. It assigns no anatomy, admits no object and refuses
nothing: a territory is not a bone until something else says so, and a low pass is not a wrong
divide. `pair_code` names only whether a pair's geometry could be READ -- never what the reading
means. The bar `minimum_sites` is an ARGUMENT the caller records before the run that judges it
(project law 4), never a constant in here.

It is a MEASUREMENT in §13.7's sense: it returns numbers and fields with their units and decides
nothing, beside one pure decision that is total over its arguments and returns named codes.

Units: distances are millimetres in the plane's own orthogonal spacing metric, as
`interiors.read_interiors` computes them. Counts are whole directed edges, so an interface between
two territories is counted once in each of their rows.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from knee.compute.contracts import ComputeContract, contracted, handed_on
from knee.objects.interiors import EDGE_KINDS
from knee.telemetry.ledger import ledger

PAIR_CODES = (
    "read",
    "no_divide",
    "too_few_sites",
    "peak_below_saddle",
    "unreadable_relief",
    "invalid_measurement",
)

PAIR_CODE_VALUES = {name: index + 1 for index, name in enumerate(PAIR_CODES)}

KIND_ORDER = tuple(
    name for name, _ in sorted(EDGE_KINDS.items(), key=lambda item: item[1])
)

CONTRACT = ComputeContract(
    kind="boundary_census_and_pairwise_relief",
    language="NumPy; no library segmentation, no SciPy on this path",
    reads="labels int32 (R,C); distance_mm float64 (R,C); edge regions int32 (P,); edge kinds uint8 (P,)",
    writes="owned read-only arrays: (T,) labels and peaks, (T,5) edge counts, (Q,2) pairs, (Q,) sites/saddles/codes",
    allocation="O(R*C) transient neighbour views; O(T*5 + Q) output; no copy of the plane",
    work="two axis passes over the plane, one unique over the touching pairs, one pass over P edges",
    parallel_unit="independent plane",
    reference="boundary_census is itself the reference; no accelerated twin is admitted yet",
    proof_gate="tests/knee/objects/test_boundaries.py two-sign; just crosshair on pair_code",
)


def pair_code(
    sites: int, lower_peak_mm: float, saddle_mm: float, minimum_sites: int
) -> str:
    """Name whether one pair of touching territories has a readable relief. Pure and total.

    `sites` is how many 4-adjacent pixel pairs straddle the divide, `saddle_mm` the highest pass
    across it, and `lower_peak_mm` the lower of the two centres. Every outcome is a different fact
    with a different remedy, so each gets its own code (project law 3):

        read               the pair's relief was read; the prominence is the caller's to use
        no_divide          the two territories never touch. Silence, never a zero prominence
        too_few_sites      they touch, but at fewer places than the caller declared admissible
        peak_below_saddle  a centre lies BELOW its own pass. A watershed basin cannot do this, so
                           this names a wiring fault instead of clamping it away silently
        unreadable_relief  a height was not finite. Silence about the relief, not about the pair
        invalid_measurement  the arguments cannot be a measurement at all

    It carries NO precondition on purpose: a decision in this project is total over its arguments
    (project law 3), so every refusal is a named code rather than a caller obligation. A `pre:`
    here would also stop the symbolic check from ever exploring the refused inputs.

    post: __return__ in ('read', 'no_divide', 'too_few_sites', 'peak_below_saddle', 'unreadable_relief', 'invalid_measurement')
    post: __return__ != 'read' or sites >= minimum_sites
    post: __return__ != 'read' or lower_peak_mm >= saddle_mm
    """
    if sites < 0 or minimum_sites < 0:
        return "invalid_measurement"
    # The pair is read before its heights: two territories that never touch have no relief to
    # report, and that is a different silence from a height that could not be measured.
    if sites == 0:
        return "no_divide"
    if not math.isfinite(lower_peak_mm) or not math.isfinite(saddle_mm):
        return "unreadable_relief"
    if lower_peak_mm < 0.0 or saddle_mm < 0.0:
        return "invalid_measurement"
    if sites < minimum_sites:
        return "too_few_sites"
    if lower_peak_mm < saddle_mm:
        return "peak_below_saddle"
    return "read"


def carries_prominence(code: str) -> bool:
    """Whether a pair code licenses reading a prominence from its heights.

    The one place the distinction is made, so no caller re-derives it and drifts. A pair that is
    not read contributes to no total, no share and no comparison.

    post: __return__ == (code == 'read')
    """
    return code == "read"


@dataclass(frozen=True, slots=True)
class BoundaryCensus:
    """One plane's territories, what bounds each, and the relief between those that touch.

    `labels` (T,) are the territory labels present, ascending; every other array is in that order.
    `peak_mm` (T,) is each territory's greatest distance from its surrounding constraints.
    `edges_by_kind` (T, 5) counts directed edges in `KIND_ORDER`.
    `pair_labels` (Q, 2) are the touching pairs, each ascending and listed once; `pair_sites` (Q,)
    how many adjacencies straddle each divide; `pair_saddle_mm` (Q,) the highest pass across it;
    `pair_codes` (Q,) uint8 values of `PAIR_CODE_VALUES`.
    """

    labels: np.ndarray
    peak_mm: np.ndarray
    edges_by_kind: np.ndarray
    pair_labels: np.ndarray
    pair_sites: np.ndarray
    pair_saddle_mm: np.ndarray
    pair_codes: np.ndarray

    def prominences_mm(self) -> np.ndarray:
        """Each pair's two prominences above its saddle, (Q, 2) float64, NaN where not read.

        An arrangement of values already measured, kept here so that every caller computes it the
        same way and an unread pair stays silent rather than reading as zero.
        """
        where = np.searchsorted(self.labels, self.pair_labels)
        heights = self.peak_mm[where]
        out = heights - self.pair_saddle_mm[:, None]
        # Through `carries_prominence`, the one place the distinction is made (task 7.2): this
        # method compared the stored value directly and was exactly the drift that function's
        # docstring warns of. A code value outside the vocabulary carries nothing.
        names = {value: name for name, value in PAIR_CODE_VALUES.items()}
        unread = np.array(
            [
                not carries_prominence(names.get(int(code), ""))
                for code in self.pair_codes
            ],
            dtype=bool,
        )
        out[unread] = np.nan
        return handed_on(out)


@contracted
def boundary_census(
    labels: np.ndarray,
    distance_mm: np.ndarray,
    edge_regions: np.ndarray,
    edge_kinds: np.ndarray,
    minimum_sites: int = 1,
) -> BoundaryCensus:
    """Count what bounds every territory, and read the relief between those that touch.

    `labels` and `distance_mm` are `InteriorReading.labels` and `.distance_mm`; `edge_regions` and
    `edge_kinds` are its per-edge owner and what lies across. Label 0 is unseeded and owns nothing.

    The saddle is the highest pass: a path leaving one territory for the other crosses BOTH pixels
    of some 4-adjacency, so that crossing costs the lower of their two distances, and the easiest
    crossing is the greatest such value over the divide. That is the quantity §9.1's "standing above
    its valley" asks for, and it is read here and judged nowhere.
    """
    marks = np.asarray(labels)
    relief = np.asarray(distance_mm, dtype=np.float64)
    if marks.ndim != 2 or marks.shape != relief.shape:
        raise ValueError("labels_and_distance_do_not_agree")
    if marks.dtype.kind not in "iu":
        raise ValueError("labels_are_whole_numbers")
    regions = np.asarray(edge_regions)
    kinds = np.asarray(edge_kinds)
    if regions.shape != kinds.shape or regions.ndim != 1:
        raise ValueError("edge_regions_and_kinds_do_not_agree")
    # `type(...) is not int` rather than isinstance: it rejects bool without a second clause,
    # since `type(True)` is `bool`, and a flag silently read as 1 would declare a floor nobody set.
    if type(minimum_sites) is not int or minimum_sites < 0:
        raise ValueError("invalid_minimum_sites")

    present = np.unique(marks[marks > 0]).astype(np.int32)
    territories = len(present)
    # Seeded at -inf, never NaN: `np.maximum` PROPAGATES NaN, so a NaN seed would make every peak
    # unreadable. Every present label holds at least one place by construction, so no -inf survives;
    # a NaN in the relief itself still propagates, which is the honest reading of an unread height.
    peaks = np.full(territories, -np.inf, dtype=np.float64)
    counts = np.zeros((territories, len(KIND_ORDER)), dtype=np.int64)

    if territories:
        held = marks > 0
        at = np.searchsorted(present, marks[held])
        np.maximum.at(peaks, at, relief[held])
        wanted = np.isin(regions, present)
        if wanted.any():
            rows = np.searchsorted(present, regions[wanted])
            columns = kinds[wanted].astype(np.int64) - 1
            inside = (columns >= 0) & (columns < len(KIND_ORDER))
            np.add.at(counts, (rows[inside], columns[inside]), 1)

    lows: list[np.ndarray] = []
    highs: list[np.ndarray] = []
    passes: list[np.ndarray] = []
    for axis in (0, 1):
        taken = np.arange(marks.shape[axis] - 1)
        here, there = marks.take(taken, axis=axis), marks.take(taken + 1, axis=axis)
        touching = (here > 0) & (there > 0) & (here != there)
        if not touching.any():
            continue
        one, other = here[touching], there[touching]
        lows.append(np.minimum(one, other))
        highs.append(np.maximum(one, other))
        passes.append(
            np.minimum(
                relief.take(taken, axis=axis)[touching],
                relief.take(taken + 1, axis=axis)[touching],
            )
        )

    if lows:
        low = np.concatenate(lows).astype(np.int64)
        high = np.concatenate(highs).astype(np.int64)
        crossing = np.concatenate(passes)
        span = int(marks.max()) + 1
        keyed = low * span + high
        unique, inverse = np.unique(keyed, return_inverse=True)
        pairs = np.column_stack((unique // span, unique % span)).astype(np.int32)
        sites = np.bincount(inverse, minlength=len(unique)).astype(np.int64)
        saddles = np.full(len(unique), -np.inf, dtype=np.float64)
        np.maximum.at(saddles, inverse, crossing)
    else:
        pairs = np.zeros((0, 2), dtype=np.int32)
        sites = np.zeros(0, dtype=np.int64)
        saddles = np.zeros(0, dtype=np.float64)

    where = np.searchsorted(present, pairs) if territories else pairs
    lower = (
        np.min(peaks[where], axis=1) if len(pairs) else np.zeros(0, dtype=np.float64)
    )
    codes = np.asarray(
        [
            PAIR_CODE_VALUES[
                pair_code(int(n), float(peak), float(saddle), minimum_sites)
            ]
            for n, peak, saddle in zip(sites, lower, saddles, strict=True)
        ],
        dtype=np.uint8,
    )

    ledger.record(
        "objects.boundary_census",
        territories=territories,
        pairs=len(pairs),
        divide_sites=int(sites.sum()),
        edges=int(regions.size),
    )

    return BoundaryCensus(
        handed_on(present),
        handed_on(peaks),
        handed_on(counts),
        handed_on(pairs),
        handed_on(sites),
        handed_on(saddles),
        handed_on(codes),
    )
