"""Every native place of one acquisition in the static-middle language (thesis §7).

OpenSpec every-stage-renders tasks 2.2–2.4: the existing RegimeKey owns the edge
pair and its exact foreground count. Nothing here repeats quantiles, normalises
spatially, aligns acquisitions or names anatomy. Dispatch is all native places of
the series read by Chapter 1; no structural role or subject kind selects a place.
The explicit normalisation is none. The scalar oracle is digit_code.
"""

from dataclasses import dataclass

import numpy as np

from knee.absence import absence_code
from knee.compute.contracts import ComputeContract, contracted, handed_on
from knee.lenses.digits import DIGIT_CODES, digit_code
from knee.lenses.members import STANDING_CODES, standing_code
from knee.telemetry import ledger

CODE_VALUES = {name: index for index, name in enumerate(DIGIT_CODES)}
SILENT = 2
DIGIT_VALUES = np.asarray([-1, 0, 1, SILENT, SILENT, SILENT, SILENT], dtype=np.int8)
STANDING_VALUES = {name: index for index, name in enumerate(STANDING_CODES)}

#: The seated members, each naming the structurally selected population it reads and the two
#: `RegimeKey` fields that carry it. NEITHER IS A FALLBACK: both are read every time, and a member
#: that cannot place a pair returns its own named silence rather than being filled from the other
#: (`every-stage-renders`, "Every structurally warranted population is a seated member").
MEMBERS: tuple[tuple[str, str, str], ...] = (
    ("noise_law_cut", "terciles", "foreground_count"),
    ("background_split", "split_terciles", "split_population_count"),
)

#: Every (first code, second code) pair's standing, built BY CALLING the pinned scalar on all 49
#: combinations. So the vectorized standing map answers to `standing_code` by construction rather
#: than by a second implementation that could drift from it.
STANDING_TABLE = np.asarray(
    [
        [STANDING_VALUES[standing_code(first, second)] for second in DIGIT_CODES]
        for first in DIGIT_CODES
    ],
    dtype=np.uint8,
)
CONTRACT = ComputeContract(
    kind="native_acquisition_ternary_codes",
    language="NumPy vectorized reference; no custom voxel loop or accelerated twin",
    reads="native real (Z,R,C) stored values; own-series low/high edges and exact foreground count",
    writes="owned readonly uint8 named-code map and int8 digits; 2 is silence, not 0; counts per code",
    allocation="N=Z*R*C; N-byte code output plus N-byte digit output and <=3N bool scratch; no source copy",
    work="fixed vectorized comparisons over N values, seven counted code scans; no repeated quantile",
    parallel_unit="acquisition (not concurrently enabled)",
    reference="place_codes_reference, exact per-place oracle digit_code",
    proof_gate="direct intent and scalar/map agreement; source immutability; real-entry receipt and picture",
)


@dataclass(frozen=True, slots=True)
class LensReading:
    """ONE seated member's reading: native (Z,R,C) maps, codes index DIGIT_CODES, digits -1/0/+1/2.

    `population` names the structural selection this member read, so a consumer can never
    mistake one member for another or for "the" reading of the series. Edges are stored
    units, frame/order inherited unchanged from the Chapter 1 series. counts has one Python
    integer per named code, including silence. Absent metadata is None, never a guessed zero
    population or a fabricated pair. No spatial correction is applied and no cross-acquisition
    correspondence is claimed.
    """

    population: str
    code: str
    why: str
    low_edge: float | None
    high_edge: float | None
    population_count: int | None
    minimum_population: int | None
    normalisation: str
    codes: np.ndarray
    digits: np.ndarray
    counts: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class LensesReading:
    """Every seated member of one series, and what they jointly said about each place.

    There is deliberately NO field here naming a winner, a preferred member or a resolved
    digit. The founder, 2026-10-12: "we always keep information we compute. I'll resolve
    what we report and how we do it, but the pipeline should keep everything, including
    where things conflict." A consumer that wants a single digit per place does not get one
    from this record, and that refusal is the design rather than an omission.

    `standings` indexes STANDING_CODES per place, so a place where the members disagree is
    reachable AS a disagreement -- which is the three-legged stool's informative case, and
    the thing both second readers found missing from the lead's first design.
    """

    members: tuple[LensReading, ...]
    standings: np.ndarray
    standing_counts: tuple[int, ...]


@contracted(CONTRACT)
def place_codes_reference(
    values: np.ndarray,
    low_edge: float | None,
    high_edge: float | None,
    population_count: int,
    minimum_population: int,
) -> np.ndarray:
    """Apply the scalar oracle's vocabulary by vectorized comparisons, without a source copy.

    values is a real numeric ndarray. An unavailable edge pair writes only silence.
    The result is an owned readonly uint8 array of the same shape. No input is written.

    post: __return__.shape == values.shape
    post: __return__.dtype == np.dtype("uint8")
    post: not __return__.flags.writeable
    """
    base = digit_code(
        float("nan"), low_edge, high_edge, population_count, minimum_population
    )
    array = np.full(values.shape, CODE_VALUES[base], dtype=np.uint8)
    if CODE_VALUES[base] == CODE_VALUES["place_unread"]:
        finite = np.isfinite(values)
        array[finite] = CODE_VALUES["at"]
        array[finite & (values < low_edge)] = CODE_VALUES["below"]
        array[finite & (values > high_edge)] = CODE_VALUES["above"]
    return handed_on(array)


def read_member(
    volume: object, regime: object, population: str, edges_field: str, count_field: str
) -> LensReading:
    """One seated member's reading of every native place, against ITS OWN population's pair.

    This orchestration names existing input facts; digit_code owns the scalar decisions.
    Never reconstruct a population from a share, never recompute a missing pair, and never
    read another member's pair -- a member that cannot place its own edges says so, and the
    silence is its own. Filling it from the other member would be a default (law 3).
    """
    numeric = (
        isinstance(volume, np.ndarray)
        and volume.ndim == 3
        and volume.dtype.kind in "iuf"
    )
    shape = volume.shape if isinstance(volume, np.ndarray) and numeric else (0, 0, 0)
    count = getattr(regime, count_field, None)
    minimum = getattr(regime, "tercile_minimum_population", None)
    edges = getattr(regime, edges_field, None)
    pair = edges if isinstance(edges, tuple) and len(edges) == 2 else None
    readable_pair = pair is not None and all(
        isinstance(edge, (int, float)) and not isinstance(edge, bool) for edge in pair
    )
    readable_count = isinstance(count, int) and not isinstance(count, bool)
    readable_minimum = isinstance(minimum, int) and not isinstance(minimum, bool)
    metadata_read = readable_pair and readable_count and readable_minimum
    # A NaN edge is a readable pair carrying no pair -- which is how a member whose population
    # could not be placed reports itself. `digit_code` then names it `no_edges`, per place.
    low = float(pair[0]) if metadata_read and pair is not None else None
    high = float(pair[1]) if metadata_read and pair is not None else None
    population_count = int(count) if isinstance(count, int) else None
    minimum_population = int(minimum) if isinstance(minimum, int) else None
    input_code = absence_code(
        construction_built=True,
        predecessor_returned=volume is not None and regime is not None,
        item_count=int(np.prod(shape)) if numeric else 1,
        item_read=numeric and metadata_read,
    )
    if (
        input_code == "present"
        and population_count is not None
        and minimum_population is not None
    ):
        codes = place_codes_reference(
            volume, low, high, population_count, minimum_population
        )
        probe = digit_code(
            float("nan"), low, high, population_count, minimum_population
        )
        code = "present" if probe == "place_unread" else probe
        why = f"{population} population's own terciles; no spatial correction"
    else:
        low, high = (low, high) if metadata_read else (None, None)
        population_count = population_count if metadata_read else None
        minimum_population = minimum_population if metadata_read else None
        codes = handed_on(np.full(shape, CODE_VALUES["no_edges"], dtype=np.uint8))
        code = input_code
        why = (
            "native volume or exact edge-population record was absent, empty or unread"
        )
    digits = handed_on(DIGIT_VALUES[codes])
    counts = tuple(
        int(np.count_nonzero(codes == index)) for index in range(len(DIGIT_CODES))
    )
    return LensReading(
        population,
        code,
        why,
        low,
        high,
        population_count,
        minimum_population,
        "none",
        codes,
        digits,
        counts,
    )


def read_lenses(volume: object, regime: object) -> LensesReading:
    """Seat every member, read each, and keep what they jointly said about every place.

    Each member is read UNCONDITIONALLY, whether or not another resolved: a body does not
    wait on an absent member (`chapters/02-collapse/teachings.md`, THE CONCLAVE). Nothing
    here chooses between them, and `LensesReading` has no field in which a choice could be
    recorded.
    """
    # Recorded by the CONSUMER at the point of reading (`specs/route-composition`): what this
    # stage took from Chapter 1 and from the field, before it reads either.
    ledger.record("study.consumed_by.lenses", volume=1 if volume is not None else 0)
    ledger.record("collapse.consumed_by.lenses", regime=1 if regime is not None else 0)
    members = tuple(read_member(volume, regime, *member) for member in MEMBERS)
    first, second = members[0], members[1]
    standings = handed_on(STANDING_TABLE[first.codes, second.codes])
    standing_counts = tuple(
        int(np.count_nonzero(standings == index))
        for index in range(len(STANDING_CODES))
    )
    ledger.record(
        "lenses.produced",
        members=len(members),
        places=int(standings.size),
        output_bytes=int(
            sum(m.codes.nbytes + m.digits.nbytes for m in members) + standings.nbytes
        ),
    )
    return LensesReading(members, standings, standing_counts)
