"""Serialize the returned production boundary census without another analysis."""

from dataclasses import asdict

import numpy as np

from knee.objects.boundaries import (
    CONTRACT,
    KIND_ORDER,
    PAIR_CODE_VALUES,
    PAIR_CODES,
    BoundaryCensus,
)


def _finite(value: float) -> float | None:
    """A value for JSON, or None where it was not read: the receipt refuses NaN by design."""
    number = float(value)
    return number if np.isfinite(number) else None


def boundary_record(census: BoundaryCensus) -> tuple[dict, dict]:
    arrays = {
        f"b1_census_{name}": getattr(census, name)
        for name in (
            "labels",
            "peak_mm",
            "edges_by_kind",
            "pair_labels",
            "pair_sites",
            "pair_saddle_mm",
            "pair_codes",
        )
    }
    # The prominences are a value the stage itself arranges, kept beside the heights so a reader
    # never re-derives them and an unread pair stays NaN rather than reading as zero.
    arrays["b1_census_prominence_mm"] = census.prominences_mm()
    totals = census.edges_by_kind.sum(axis=0)
    metadata = {
        "territories": len(census.labels),
        "touching_pairs": len(census.pair_labels),
        "divide_sites": int(census.pair_sites.sum()),
        "edges_by_kind": {
            name: int(count) for name, count in zip(KIND_ORDER, totals, strict=True)
        },
        "pair_code_counts": {
            name: int(np.count_nonzero(census.pair_codes == value))
            for name, value in PAIR_CODE_VALUES.items()
        },
        "peak_mm_range": [
            _finite(census.peak_mm.min(initial=np.inf)),
            _finite(census.peak_mm.max(initial=-np.inf)),
        ],
        "saddle_mm_range": [
            _finite(census.pair_saddle_mm.min(initial=np.inf)),
            _finite(census.pair_saddle_mm.max(initial=-np.inf)),
        ],
        "array_bytes": sum(a.nbytes for a in arrays.values()),
        "pair_codes": PAIR_CODE_VALUES,
        "pair_code_order": list(PAIR_CODES),
        "kind_order": list(KIND_ORDER),
        "compute_contract": asdict(CONTRACT),
        "scope": "what bounds each territory and the relief between those that touch; no anatomy, no admission",
        "tie_rule": "a divide's pass is the lower of its two pixels; the saddle is the greatest pass over the divide",
    }
    return metadata, arrays
