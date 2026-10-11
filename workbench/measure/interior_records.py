"""Serialize the returned production interior reading without another analysis."""

from dataclasses import asdict

import numpy as np

from knee.collapse.interiors import CONTRACT, EDGE_KINDS, TRACE_CODES, InteriorReading


def interior_record(reading: InteriorReading) -> tuple[dict, dict]:
    arrays = {
        f"b1_{name}": getattr(reading, name)
        for name in (
            "dark",
            "available",
            "distance_mm",
            "distance_guard",
            "markers",
            "labels",
            "edge_points_rc",
            "edge_normals_rc",
            "edge_regions",
            "edge_kinds",
            "band_low_mm",
            "band_high_mm",
            "trace_points_rc",
            "trace_codes",
        )
    }
    if reading.profiles is not None:
        arrays.update(
            {
                f"b1_{name}": getattr(reading.profiles, name)
                for name in ("samples", "valid", "slopes", "distances_mm")
            }
        )
    count = int(reading.labels.max(initial=0))
    metadata = {
        "code": reading.code,
        "territories": count,
        "territory_pixels": np.bincount(
            reading.labels.ravel(), minlength=count + 1
        ).tolist(),
        "edge_counts": {
            name: int(np.count_nonzero(reading.edge_kinds == value))
            for name, value in EDGE_KINDS.items()
        },
        "trace_counts": {
            name: int(np.count_nonzero(reading.trace_codes == value))
            for name, value in TRACE_CODES.items()
        },
        "distance_guard_codes": {
            "not_in_search": 0,
            "low_signal": 1,
            "missing": 2,
            "virtual_frame": 3,
        },
        "distance_error_bound_mm": reading.distance_error_bound_mm,
        "coordinate_evaluations": 0
        if reading.profiles is None
        else reading.profiles.samples.size,
        "array_bytes": sum(a.nbytes for a in arrays.values()),
        "requested_backend": None
        if reading.profiles is None
        else reading.profiles.requested_backend,
        "effective_backend": "not_invoked"
        if reading.profiles is None
        else reading.profiles.effective_backend,
        "edge_kind_codes": EDGE_KINDS,
        "trace_codes": TRACE_CODES,
        "compute_contract": asdict(CONTRACT),
        "scope": "above-split territories and native axis-profile dark intervals; anatomy/ownership unassigned",
        "tie_rule": "recorded SciPy EDT nearest-index tie; skimage h-maxima >= h whole plateaus; ndi.label C-order four-connectivity; watershed priority value then insertion time",
    }
    return metadata, arrays
