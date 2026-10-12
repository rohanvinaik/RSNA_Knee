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
from knee.telemetry import ledger

CODE_VALUES = {name: index for index, name in enumerate(DIGIT_CODES)}
SILENT = 2
DIGIT_VALUES = np.asarray([-1, 0, 1, SILENT, SILENT, SILENT, SILENT], dtype=np.int8)
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
    """Native (Z,R,C) maps: codes index DIGIT_CODES, digits contain -1/0/+1 or silent 2.

    Edges are stored units, frame/order inherited unchanged from the Chapter 1 series.
    counts has one Python integer per named code, including silence. Absent metadata
    is None, never a guessed zero population or a fabricated pair. No spatial correction
    is applied and no cross-acquisition correspondence is claimed.
    """

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


def read_lenses(volume: object, regime: object) -> LensReading:
    """Read supplied native values and edge metadata, returning named absence on missing input.

    This orchestration names existing input facts; digit_code owns the scalar decisions.
    Never reconstruct a population from foreground_share, never recompute a missing pair.
    """
    numeric = (
        isinstance(volume, np.ndarray)
        and volume.ndim == 3
        and volume.dtype.kind in "iuf"
    )
    shape = volume.shape if numeric else (0, 0, 0)
    count = getattr(regime, "foreground_count", None)
    minimum = getattr(regime, "tercile_minimum_population", None)
    edges = getattr(regime, "terciles", None)
    metadata_read = (
        isinstance(count, int)
        and not isinstance(count, bool)
        and isinstance(minimum, int)
        and not isinstance(minimum, bool)
        and isinstance(edges, tuple)
        and len(edges) == 2
        and all(isinstance(edge, (int, float)) for edge in edges)
    )
    input_code = absence_code(
        construction_built=True,
        predecessor_returned=volume is not None and regime is not None,
        item_count=int(np.prod(shape)) if numeric else 1,
        item_read=numeric and metadata_read,
    )
    if input_code == "present":
        low, high = edges
        codes = place_codes_reference(volume, low, high, count, minimum)
        probe = digit_code(float("nan"), low, high, count, minimum)
        code = "present" if probe == "place_unread" else probe
        why = "own-series foreground terciles; no spatial correction"
    else:
        low, high = edges if metadata_read else (None, None)
        count = count if metadata_read else None
        minimum = minimum if metadata_read else None
        codes = handed_on(np.full(shape, CODE_VALUES["no_edges"], dtype=np.uint8))
        code = input_code
        why = (
            "native volume or exact edge-population record was absent, empty or unread"
        )
    digits = handed_on(DIGIT_VALUES[codes])
    counts = tuple(
        int(np.count_nonzero(codes == index)) for index in range(len(DIGIT_CODES))
    )
    ledger.record(
        "lenses.produced",
        places=int(codes.size),
        output_bytes=int(codes.nbytes + digits.nbytes),
    )
    return LensReading(
        code, why, low, high, count, minimum, "none", codes, digits, counts
    )
