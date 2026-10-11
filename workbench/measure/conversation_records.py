"""Serialize a returned B2 conversation without recomputing its readings."""

from dataclasses import asdict
from math import isfinite

import numpy as np

from knee.collapse.conversation import (
    CONTRACT,
    COVERAGE,
    EXCHANGE_CODES,
    SeriesConversation,
)


def _json_float(value: float) -> float | None:
    value = float(value)
    return value if isfinite(value) else None


def conversation_record(
    reading: SeriesConversation, requested_backend: str | None = None
) -> tuple[dict, dict]:
    """Return complete JSON-safe decisions/metadata and the exact B2 arrays.

    Exchange array names retain their donor relationship by exchange index; the
    corresponding ``exchanges`` metadata entry carries the donor series UID.
    """
    arrays: dict[str, np.ndarray] = {}
    for name in (
        "concurrent_barrier",
        "conditional_barrier",
        "concurrent_labels",
        "conditional_labels",
        "concurrent_parents",
        "conditional_parents",
    ):
        arrays[f"b2_{name}"] = getattr(reading, name)

    exchange_metadata = []
    sample_evaluations = 0
    raster_visits = [0, 0]
    for index, exchange in enumerate(reading.exchanges):
        prefix = f"b2_exchange{index}_"
        fields = (
            "source_edge_indices",
            "source_regions",
            "points_rc",
            "normals_rc",
            "donor_quads_rc",
            "off_plane_mm",
            "coverage_codes",
            "dark_runs",
            "bounded_matches",
            "open_matches",
            "band_low_mm",
            "band_high_mm",
            "derived_trace_rc",
            "trace_codes",
            "concurrent_quads_rc",
            "concurrent_barrier",
            "conditional_barrier",
        )
        for name in fields:
            arrays[prefix + name] = getattr(exchange, name)
        profile_metadata = None
        if exchange.profiles is not None:
            profile = exchange.profiles
            for name in ("samples", "valid", "slopes", "distances_mm"):
                arrays[prefix + "profile_" + name] = getattr(profile, name)
            profile_metadata = {
                "support_code": profile.support_code,
                "support_codes": list(profile.support_codes),
                "requested_backend": profile.requested_backend,
                "effective_backend": profile.effective_backend,
            }
            sample_evaluations += int(profile.samples.size)
        raster_visits[0] += int(exchange.raster_visits[0])
        raster_visits[1] += int(exchange.raster_visits[1])
        exchange_metadata.append(
            {
                "donor_uid": exchange.donor_uid,
                "code": exchange.code,
                "normal_angle_degrees": _json_float(exchange.normal_angle_degrees),
                "resolution_step_mm": _json_float(exchange.resolution_step_mm),
                "profile": profile_metadata,
                "raster_visits": [int(x) for x in exchange.raster_visits],
            }
        )

    metadata = {
        "series_uid": reading.series_uid,
        "code": reading.code,
        "exchanges": exchange_metadata,
        "requested_backend": requested_backend,
        "effective_backends": sorted(
            {
                exchange.profiles.effective_backend
                for exchange in reading.exchanges
                if exchange.profiles is not None
            }
        ),
        "coverage_codes": COVERAGE,
        "exchange_codes": EXCHANGE_CODES,
        "compute_contract": asdict(CONTRACT),
        "sample_evaluations": sample_evaluations,
        "sample_source_read_upper_bound": 4 * sample_evaluations,
        "raster_visits": raster_visits,
        "array_bytes": sum(array.nbytes for array in arrays.values()),
    }
    return metadata, arrays
