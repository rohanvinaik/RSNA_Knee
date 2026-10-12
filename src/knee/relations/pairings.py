"""Sample-supported dark-bounded extent pairs, not complete interstices or anatomy."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

import numpy as np

from knee.absence import absence_code
from knee.compute.contracts import ComputeContract, contracted, handed_on
from knee.objects.interiors import InteriorReading
from knee.relations.pair_codes import CODES, pair_code
from knee.telemetry import ledger

CONTRACT = ComputeContract(
    kind="categorical_native_bilinear_footprint",
    language="NumPy vectorized reference",
    reads="int32[R,C] labels; bool[R,C] availability; float64[Q,2] native centre coordinates",
    writes="immutable int32[Q,4], corner order 00/01/10/11; -1 inactive, -2 unread",
    allocation="16Q output bytes; O(Q) coordinate/index/weight/mask scratch; no plane copy",
    work="four positive-weight contributor reads per position at most; no categorical interpolation",
    parallel_unit="vectorized positions within one selected plane; no concurrent series",
    reference="footprint_labels_reference",
    proof_gate="direct two-sign intent; Detective standing; real-entry record and picture",
)


@dataclass(frozen=True, slots=True)
class PairingReading:
    code: str
    why: str
    source_labels: np.ndarray
    far_labels: np.ndarray
    trace_codes: np.ndarray
    outcome_codes: np.ndarray
    positions_rc: np.ndarray
    contributor_labels: np.ndarray
    band_limits_mm: np.ndarray
    counts: Mapping[str, int]
    scope: str = (
        "selected-plane sample-supported pairs; complete interstice extent unresolved"
    )


@contracted(CONTRACT)
def footprint_labels_reference(labels, available, positions_rc):
    """Retain each positive-weight contributor; never interpolate categorical labels.

    pre: labels.ndim == 2 and labels.dtype == np.dtype('int32')
    pre: available.shape == labels.shape and available.dtype == np.dtype('bool')
    pre: positions_rc.ndim == 2 and positions_rc.shape[1] == 2
    post: __return__.shape == (len(positions_rc), 4)
    post: __return__.dtype == np.dtype('int32')
    post: not __return__.flags.writeable
    """
    positions = np.asarray(positions_rc, dtype=np.float64)
    output = np.full((len(positions), 4), -2, dtype=np.int32)
    if not labels.size:
        return handed_on(output)
    bounded = (
        np.all(np.isfinite(positions), axis=1)
        & np.all(positions >= 0, axis=1)
        & np.all(positions <= np.asarray(labels.shape) - 1, axis=1)
    )
    safe = np.where(bounded[:, None], positions, 0)
    base = np.floor(safe).astype(np.int64)
    delta = safe - base
    rows = base[:, 0, None] + np.array([0, 0, 1, 1])
    cols = base[:, 1, None] + np.array([0, 1, 0, 1])
    dr, dc = delta[:, 0], delta[:, 1]
    weights = np.column_stack(
        ((1 - dr) * (1 - dc), (1 - dr) * dc, dr * (1 - dc), dr * dc)
    )
    active = (weights > 0) & bounded[:, None]
    output[bounded] = -1
    # Only active corners are addressed; an inactive final-row corner is not an input read.
    rr, cc = rows[active], cols[active]
    output[active] = np.where(available[rr, cc], labels[rr, cc], -2)
    return handed_on(output)


def unreadable_pairing() -> PairingReading:
    """The record for a predecessor that does not read as an interiors reading at all.

    `invalid_count` is `absence_code`'s own word for an argument that cannot be read, as
    `read_ownership` uses it; it names no silence about the study, and every array is empty
    because no profile row was handed over in a form this unit can count.
    """
    counts = {name: 0 for name in CODES}
    ledger.record(
        "pairings.produced", profiles=0, paired=0, footprint_read_upper_bound=0
    )
    return PairingReading(
        code="invalid_count",
        why="the interiors reading handed over does not read as one",
        source_labels=handed_on(np.zeros(0, dtype=np.int32)),
        far_labels=handed_on(np.zeros(0, dtype=np.int32)),
        trace_codes=handed_on(np.zeros(0, dtype=np.uint8)),
        outcome_codes=handed_on(np.zeros(0, dtype=np.uint8)),
        positions_rc=handed_on(np.full((0, 2, 2), np.nan)),
        contributor_labels=handed_on(np.full((0, 2, 4), -2, dtype=np.int32)),
        band_limits_mm=handed_on(np.full((0, 2), np.nan)),
        counts=MappingProxyType(counts),
    )


def read_pairings(interiors: object, spacing_rc: object) -> PairingReading:
    """Construct flanking samples from existing profile offsets; retain every outcome.

    The intended argument is an `InteriorReading` or None, and the annotation is wider on
    purpose, as in `read_ownership`: the house requires a stage to be total, and a malformed
    record is part of the contract rather than a promise the tests break (`docs/TOOLING.md`).
    Anything that is not an interiors reading is refused by name before a field of it is read.
    """
    if interiors is not None and not isinstance(interiors, InteriorReading):
        return unreadable_pairing()
    return pairings_of(interiors, spacing_rc)


def pairings_of(
    interiors: InteriorReading | None, spacing_rc: object
) -> PairingReading:
    """The pairing reading of one interiors reading, or the silence it met."""
    count = 0 if interiors is None else len(interiors.trace_codes)
    positions = np.full((count, 2, 2), np.nan)
    contributors = np.full((count, 2, 4), -2, dtype=np.int32)
    outcome = np.full(count, CODES.index("item_unread"), dtype=np.uint8)
    source = np.zeros(count, dtype=np.int32)
    far = np.zeros(count, dtype=np.int32)
    traces = np.zeros(count, dtype=np.uint8)
    limits = np.full((count, 2), np.nan)
    schema_read = interiors is not None and (
        interiors.trace_codes.shape == (count,)
        and interiors.trace_codes.dtype == np.dtype("uint8")
        and interiors.edge_regions.shape == (count,)
        and interiors.edge_regions.dtype == np.dtype("int32")
        and interiors.band_low_mm.shape == (count,)
        and interiors.band_low_mm.dtype == np.dtype("float64")
        and interiors.band_high_mm.shape == (count,)
        and interiors.band_high_mm.dtype == np.dtype("float64")
        and interiors.available.dtype == np.dtype("bool")
    )
    readable = (
        interiors is not None
        and spacing_rc is not None
        and interiors.profiles is not None
        and schema_read
    )
    code = absence_code(True, interiors is not None, count, readable)
    if schema_read:
        traces = interiors.trace_codes.copy()
        source = interiors.edge_regions.copy()
        limits = np.column_stack((interiors.band_low_mm, interiors.band_high_mm))
    if readable:
        spacing = np.asarray(spacing_rc, dtype=np.float64)
        offsets = interiors.profiles.distances_mm
        readable = (
            spacing.shape == (2,)
            and np.all(np.isfinite(spacing))
            and np.all(spacing > 0)
            and offsets.ndim == 1
            and len(offsets) > 1
            and np.all(np.isfinite(offsets))
            and np.all(np.diff(offsets) > 0)
            and interiors.labels.dtype == np.dtype("int32")
            and interiors.available.shape == interiors.labels.shape
            and interiors.edge_points_rc.shape == (count, 2)
            and interiors.edge_normals_rc.shape == (count, 2)
            and source.shape == (count,)
            and limits.shape == (count, 2)
        )
        if readable:
            first = np.searchsorted(offsets, limits[:, 0])
            last = np.searchsorted(offsets, limits[:, 1])
            safe_first = np.clip(first, 0, len(offsets) - 1)
            safe_last = np.clip(last, 0, len(offsets) - 1)
            supported = (
                (traces == 1)
                & (first > 0)
                & (last < len(offsets) - 1)
                & (first <= last)
                & (offsets[safe_first] == limits[:, 0])
                & (offsets[safe_last] == limits[:, 1])
            )
            flank = np.column_stack(
                (
                    np.clip(first - 1, 0, len(offsets) - 1),
                    np.clip(last + 1, 0, len(offsets) - 1),
                )
            )
            positions[supported] = (
                interiors.edge_points_rc[supported, None, :]
                + offsets[flank[supported], None]
                * interiors.edge_normals_rc[supported, None, :]
                / spacing
            )
            contributors = footprint_labels_reference(
                interiors.labels, interiors.available, positions.reshape(-1, 2)
            ).reshape(count, 2, 4)
            facts = np.column_stack((source, traces, contributors.reshape(count, 8)))
            unique, inverse = np.unique(facts, axis=0, return_inverse=True)
            decisions = np.asarray(
                [
                    CODES.index(
                        pair_code(
                            int(row[0]),
                            int(row[1]),
                            row[2:6].tolist(),
                            row[6:10].tolist(),
                        )
                    )
                    for row in unique
                ],
                dtype=np.uint8,
            )
            outcome = decisions[inverse]
            paired = outcome == CODES.index("paired")
            far[paired] = np.max(contributors[paired, 1], axis=1)
        else:
            code = "item_unread"
    counts = {
        name: int(np.count_nonzero(outcome == index))
        for index, name in enumerate(CODES)
    }
    ledger.record(
        "pairings.produced",
        profiles=count,
        paired=counts["paired"],
        footprint_read_upper_bound=8 * count,
    )
    return PairingReading(
        code=code,
        why="native categorical footprints; no complete interstice"
        if code == "present"
        else code,
        source_labels=handed_on(source),
        far_labels=handed_on(far),
        trace_codes=handed_on(traces),
        outcome_codes=handed_on(outcome),
        positions_rc=handed_on(positions),
        contributor_labels=handed_on(contributors),
        band_limits_mm=handed_on(limits),
        counts=MappingProxyType(counts),
    )
