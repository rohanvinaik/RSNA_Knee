"""Geometric interiors and observed dark borders, with no anatomical assignment.

The low-signal predicate is information used to constrain an above-split search.
It is not a claim that cortex is not bone. Every territory and unseeded place is
retained.
"""

import warnings
from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi
from skimage.morphology import h_maxima
from skimage.segmentation import watershed

from knee.collapse.physical import numeric_plane, spacing_pair
from knee.compute.contracts import ComputeContract, contracted, handed_on
from knee.objects.border_codes import border_code
from knee.objects.profiles import sample_profiles

TRACE_CODES = {
    "bracketed": 1,
    "no_dark_bracket": 2,
    "multiple_brackets": 3,
    "missing_profile": 4,
    "frame_clipped": 5,
    "empty_profile": 6,
    "invalid_measurement": 7,
}
EDGE_KINDS = {
    "low_signal": 1,
    "peer_territory": 2,
    "acquisition_missing": 3,
    "frame": 4,
    "unseeded_available": 5,
}
CONTRACT = ComputeContract(
    kind="geometric_interiors_and_native_dark_bands",
    language="NumPy + SciPy EDT + scikit-image morphology/watershed; reference/Numba sampler",
    reads="native (R,C) numeric source; finite split; positive mm spacing/prominence; S offsets; "
    "the source's finite mask when already read",
    writes="owned read-only (R,C) bool/float64/int32 fields; P edges, P×S samples; no labels of anatomy",
    allocation="O(N+P*S), P<=4N; library scratch measured separately; no whole-volume copy",
    work="EDT and watershed per plane; four vectorized neighbor passes; <=4P*S source reads",
    parallel_unit="series (not concurrently enabled); bilinear twin releases GIL",
    reference="read_interiors + profile_samples_reference",
    proof_gate="intent/properties; exact reference/JIT records within one environment; real-entry corpus/pictures",
)


@dataclass(frozen=True, slots=True)
class InteriorReading:
    code: str
    dark: np.ndarray
    available: np.ndarray
    distance_mm: np.ndarray
    markers: np.ndarray
    labels: np.ndarray
    edge_points_rc: np.ndarray
    edge_normals_rc: np.ndarray
    edge_kinds: np.ndarray
    trace_points_rc: np.ndarray
    trace_codes: np.ndarray


def boundary_edges(labels, dark, available, metric):
    """All directed four-neighbor interfaces, preserving frame and missing causes."""
    padded = np.pad(labels, 1)
    padded_dark = np.pad(dark, 1)
    padded_available = np.pad(available, 1)
    points, normals, kinds = [], [], []
    for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
        neighbor = padded[
            1 + dr : 1 + dr + labels.shape[0], 1 + dc : 1 + dc + labels.shape[1]
        ]
        rows, cols = np.nonzero((labels > 0) & (neighbor != labels))
        nr, nc = rows + dr + 1, cols + dc + 1
        frame = (
            (rows + dr < 0)
            | (rows + dr >= labels.shape[0])
            | (cols + dc < 0)
            | (cols + dc >= labels.shape[1])
        )
        kind = np.full(len(rows), EDGE_KINDS["unseeded_available"], dtype=np.uint8)
        kind[padded[nr, nc] > 0] = EDGE_KINDS["peer_territory"]
        kind[padded_dark[nr, nc]] = EDGE_KINDS["low_signal"]
        kind[~padded_available[nr, nc]] = EDGE_KINDS["acquisition_missing"]
        kind[frame] = EDGE_KINDS["frame"]
        direction = np.asarray((dr, dc), dtype=np.float64)
        direction /= np.sqrt(direction @ metric @ direction)
        points.append(np.column_stack((rows + dr / 2, cols + dc / 2)))
        normals.append(np.broadcast_to(direction, (len(rows), 2)))
        kinds.append(kind)
    return tuple(handed_on(np.concatenate(items)) for items in (points, normals, kinds))


def dark_bands(profiles, split, kinds, points, normals, spacing):
    """Measure run counts first; classify unique fact tuples with a named decision."""
    low = profiles.valid & (profiles.samples <= split)
    runs = np.count_nonzero(
        low & ~np.column_stack((np.zeros(len(low), dtype=bool), low[:, :-1])), axis=1
    )
    bounded = ~low[:, 0] & ~low[:, -1]
    facts = np.column_stack(
        (kinds == EDGE_KINDS["frame"], profiles.valid.sum(axis=1), runs, bounded)
    )
    unique, inverse = np.unique(facts, axis=0, return_inverse=True)
    decisions = np.asarray(
        [
            TRACE_CODES[
                border_code(
                    bool(frame), int(valid), low.shape[1], int(count), bool(bound)
                )
            ]
            for frame, valid, count, bound in unique
        ],
        dtype=np.uint8,
    )
    codes = decisions[inverse]
    good = codes == TRACE_CODES["bracketed"]
    first = np.argmax(low, axis=1)
    last = low.shape[1] - 1 - np.argmax(low[:, ::-1], axis=1)
    lower = np.where(good, profiles.distances_mm[first], np.nan)
    upper = np.where(good, profiles.distances_mm[last], np.nan)
    trace = points + ((lower + upper) / 2)[:, None] * normals / spacing
    return handed_on(trace), handed_on(codes)


def prominent_peaks(distance: np.ndarray, prominence_mm: float) -> np.ndarray:
    """Library morphology; suppress only its NumPy 2.5 deprecated shape setter."""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Setting the shape on a NumPy array has been deprecated.*",
            category=DeprecationWarning,
            module=r"skimage\.morphology\.grayreconstruct",
        )
        return h_maxima(
            distance, prominence_mm, footprint=ndi.generate_binary_structure(2, 1)
        )


@contracted
def read_interiors(
    plane: np.ndarray,
    spacing_rc: tuple[float, float],
    split: float,
    prominence_mm: float,
    offsets_mm: np.ndarray,
    backend: str = "reference",
    *,
    metric_rc: np.ndarray | None = None,
    available: np.ndarray | None = None,
) -> InteriorReading:
    """Consume measured exclusions within their scope; preserve unresolved places.

    EDT uses the explicitly orthogonal spacing metric; profiles use the original
    retained DICOM basis metric. `available` is which of the plane's places are
    finite, when the caller has read it once for the series; it is read here otherwise.
    """
    numeric_plane(plane)
    spacing = spacing_pair(spacing_rc)
    offsets = np.asarray(offsets_mm, dtype=np.float64)
    metric = np.eye(2) if metric_rc is None else np.asarray(metric_rc, dtype=np.float64)
    if not np.isfinite(prominence_mm) or prominence_mm <= 0:
        raise ValueError("invalid_prominence_mm")
    if (
        offsets.ndim != 1
        or not len(offsets)
        or not np.all(np.isfinite(offsets))
        or np.any(np.diff(offsets) <= 0)
        or not np.any(offsets == 0)
    ):
        raise ValueError("invalid_border_offsets")
    if (
        metric.shape != (2, 2)
        or not np.all(np.isfinite(metric))
        or not np.array_equal(metric, metric.T)
        or np.any(np.linalg.eigvalsh(metric) <= 0)
    ):
        raise ValueError("invalid_profile_metric")
    if backend not in ("reference", "jit"):
        raise ValueError("invalid_backend")
    if np.isinf(split):
        raise ValueError("invalid_background_split")
    available = np.isfinite(plane) if available is None else available
    dark = (
        available & (plane <= split)
        if np.isfinite(split)
        else np.zeros(plane.shape, dtype=bool)
    )
    distance = np.zeros(plane.shape, dtype=np.float64)
    markers = np.zeros(plane.shape, dtype=np.int32)
    labels = np.zeros(plane.shape, dtype=np.int32)
    code = "measured"
    if not plane.size:
        code = "empty_plane"
    elif not np.any(available):
        code = "no_finite_support"
    elif not np.isfinite(split):
        code = "split_unavailable"
    else:
        interior = available & ~dark
        padded = np.pad(interior, 1)
        distances = np.asarray(ndi.distance_transform_edt(padded, sampling=spacing))
        distance = distances[1:-1, 1:-1].copy()
        peaks = (
            prominent_peaks(distance, prominence_mm) & interior
            if distance.max() >= prominence_mm
            else np.zeros(plane.shape, dtype=bool)
        )
        markers, count = ndi.label(peaks)
        if not count:
            code = "no_interior_seeds"
        else:
            labels = watershed(
                -distance, markers, mask=interior, connectivity=1
            ).astype(np.int32)
    points, normals, kinds = boundary_edges(labels, dark, available, metric)
    trace = np.full(points.shape, np.nan)
    codes = np.zeros(len(points), dtype=np.uint8)
    if len(points):
        profiles = sample_profiles(
            plane, points, normals, offsets, spacing, backend, metric_rc=metric
        )
        trace, codes = dark_bands(
            profiles, split, kinds, points, normals, np.asarray(spacing)
        )
    return InteriorReading(
        code,
        handed_on(dark),
        handed_on(available),
        handed_on(distance),
        handed_on(markers),
        handed_on(labels),
        points,
        normals,
        kinds,
        handed_on(trace),
        handed_on(codes),
    )
