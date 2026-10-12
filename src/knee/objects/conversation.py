"""Original same-knee readings converse; derived geometry is never a new donor.

Darkness is a scoped native predicate, not a definition of anatomy. Keep native
concurrence and donor-only constraints separate. Neither subdivision assigns an
anatomical name. Contract: chapters/02-collapse/readings/b2-workshop-resolution.md.
"""

from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi

from knee.compute.contracts import ComputeContract, contracted, handed_on
from knee.objects.analysis import SeriesMeasurement
from knee.objects.band_raster import raster_bands
from knee.objects.exchange_codes import exchange_code
from knee.objects.interiors import TRACE_CODES
from knee.objects.profiles import ProfileReading, sample_profiles

EXCHANGE_CODES = {
    name: index + 1
    for index, name in enumerate(
        (
            "concurrent",
            "peer_only",
            "disagreement",
            "native_missing",
            "native_open",
            "native_multiple",
            "outside_slab",
            "slab_support_unknown",
            "normal_unavailable",
            "empty_profile",
            "invalid_measurement",
        )
    )
}
COVERAGE = {
    "covered": 0,
    "outside_slab": 1,
    "slab_support_unknown": 2,
    "normal_unavailable": 3,
}
CONTRACT = ComputeContract(
    kind="original_same_knee_boundary_conversation",
    language="NumPy geometry/run maps; SciPy four-connected subdivision; strict JIT sampler/raster",
    reads="original B1 per series, original native plane and LPS frame; own split; acquired slab mm",
    writes="source-linked exchanges and two independent connectivity readings; immutable arrays",
    allocation="O(N+P*S) per exchange; P<=4*donor N; retain returned records, no volume copy",
    work="all ordered same-orientation pairs; <=4P*S samples; clipped raster visits counted",
    parallel_unit="recipient (serial); repeated numeric loops release GIL",
    reference="converse + sample_profiles/reference + raster_bands/reference",
    proof_gate="exact same-environment records; original-parent invariants; real-entry pictures",
)


@dataclass(frozen=True, slots=True)
class ConversationInput:
    series_uid: str
    orientation: str
    measurement: SeriesMeasurement | None
    split: float


@dataclass(frozen=True, slots=True)
class BoundaryExchange:
    donor_uid: str
    code: str
    source_edge_indices: np.ndarray
    source_regions: np.ndarray
    points_rc: np.ndarray
    normals_rc: np.ndarray
    donor_quads_rc: np.ndarray
    off_plane_mm: np.ndarray
    coverage_codes: np.ndarray
    normal_angle_degrees: float
    resolution_step_mm: float
    profiles: ProfileReading | None
    dark_runs: np.ndarray
    bounded_matches: np.ndarray
    open_matches: np.ndarray
    band_low_mm: np.ndarray
    band_high_mm: np.ndarray
    derived_trace_rc: np.ndarray
    trace_codes: np.ndarray
    concurrent_quads_rc: np.ndarray
    concurrent_barrier: np.ndarray
    conditional_barrier: np.ndarray
    raster_visits: tuple[int, int]


@dataclass(frozen=True, slots=True)
class SeriesConversation:
    series_uid: str
    code: str
    exchanges: tuple[BoundaryExchange, ...]
    concurrent_barrier: np.ndarray
    conditional_barrier: np.ndarray
    concurrent_labels: np.ndarray
    conditional_labels: np.ndarray
    concurrent_parents: np.ndarray
    conditional_parents: np.ndarray


def subdivide(labels: np.ndarray, barrier: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Four-connected components inside each original label; keep every piece.

    Barrier cells remain in the original label map and explicit mask. Refined
    zero means constrained/unclaimed, never deletion of a source pixel.
    """
    if (
        labels.ndim != 2
        or labels.dtype != np.int32
        or np.any(labels < 0)
        or barrier.shape != labels.shape
        or barrier.dtype != np.bool_
    ):
        raise ValueError("invalid_subdivision_fields")
    if labels.size > np.iinfo(np.int32).max or int(labels.max(initial=0)) > labels.size:
        raise ValueError("subdivision_count_overflow")
    result = np.zeros(labels.shape, dtype=np.int32)
    parents = [0]
    total = 0
    if not labels.size:
        return handed_on(result), handed_on(np.asarray(parents, dtype=np.int32))
    for original, bounds in enumerate(ndi.find_objects(labels), start=1):
        if bounds is None:
            continue
        pieces, count = ndi.label(
            (labels[bounds] == original) & ~barrier[bounds],
            structure=ndi.generate_binary_structure(2, 1),
        )
        destination = result[bounds]
        selected = pieces > 0
        destination[selected] = pieces[selected] + total
        parents.extend([original] * count)
        total += count
    return handed_on(result), handed_on(np.asarray(parents, dtype=np.int32))


def selected_runs(profiles: ProfileReading, split: float, donor_low, donor_high):
    """Read every native run, then name the donor-selected intersection.

    Run endpoints are sample centres. Envelopes include half the declared maximum
    sample step; these are representation cells, not tissue thickness estimates.
    Raw samples/validity remain attached to the returned exchange.
    """
    values, offsets = profiles.samples, profiles.distances_mm
    rows, samples = values.shape
    step = float(np.max(np.diff(offsets), initial=0))
    dark = profiles.valid & (values <= split)
    begins = dark & ~np.column_stack((np.zeros(rows, dtype=bool), dark[:, :-1]))
    ends = dark & ~np.column_stack((dark[:, 1:], np.zeros(rows, dtype=bool)))
    run_row, first = np.nonzero(begins)
    end_row, last = np.nonzero(ends)
    if not np.array_equal(run_row, end_row):
        raise RuntimeError("run_endpoint_invariant")
    lower, upper = offsets[first] - step / 2, offsets[last] + step / 2
    overlap = (upper >= donor_low[run_row]) & (lower <= donor_high[run_row])
    bounded = (first > 0) & (last < samples - 1)
    counts = np.bincount(run_row, minlength=rows)
    bounded_counts = np.bincount(run_row[overlap & bounded], minlength=rows)
    open_counts = np.bincount(run_row[overlap & ~bounded], minlength=rows)
    low, high = np.full(rows, np.nan), np.full(rows, np.nan)
    unique = (
        overlap & bounded & (bounded_counts[run_row] == 1) & (open_counts[run_row] == 0)
    )
    chosen = run_row[unique]
    low[chosen] = np.maximum(lower[unique], donor_low[chosen])
    high[chosen] = np.minimum(upper[unique], donor_high[chosen])
    return counts, bounded_counts, open_counts, low, high


def band_quads(points, displacement, tangent, low, high):
    """Ordered convex sample-band corners in one retained affine frame."""
    start = points + low[:, None] * displacement
    end = points + high[:, None] * displacement
    return np.stack(
        (start - tangent, start + tangent, end + tangent, end - tangent), axis=1
    )


def empty_exchange(uid: str, code: str, shape: tuple[int, int]) -> BoundaryExchange:
    def empty(*dimensions, dtype=np.float64):
        return handed_on(np.empty(dimensions, dtype=dtype))

    mask = handed_on(np.zeros(shape, dtype=bool))
    return BoundaryExchange(
        uid,
        code,
        empty(0, dtype=np.int64),
        empty(0, dtype=np.int32),
        empty(0, 2),
        empty(0, 2),
        empty(0, 4, 2),
        empty(0, 4),
        empty(0, dtype=np.uint8),
        float("nan"),
        0.0,
        None,
        empty(0, dtype=np.int64),
        empty(0, dtype=np.int64),
        empty(0, dtype=np.int64),
        empty(0),
        empty(0),
        empty(0, 2),
        empty(0, dtype=np.uint8),
        empty(0, 4, 2),
        mask,
        mask,
        (0, 0),
    )


def exchange(
    donor: ConversationInput,
    recipient: ConversationInput,
    offsets: np.ndarray,
    backend: str,
) -> BoundaryExchange:
    """Transport original bounded bands and read the unchanged recipient plane."""
    target, source = recipient.measurement, donor.measurement
    shape = (
        (0, 0)
        if target is None or target.acquired_plane is None
        else target.acquired_plane.shape
    )
    if (
        source is None
        or source.frame is None
        or source.interiors is None
        or source.interiors.profiles is None
    ):
        return empty_exchange(donor.series_uid, "donor_unavailable", shape)
    if (
        target is None
        or target.frame is None
        or target.acquired_plane is None
        or not np.isfinite(recipient.split)
    ):
        return empty_exchange(donor.series_uid, "recipient_unavailable", shape)
    interior = source.interiors
    assert interior.profiles is not None  # established by donor availability above
    edges = np.flatnonzero(interior.trace_codes == TRACE_CODES["bracketed"])
    if not len(edges):
        return empty_exchange(donor.series_uid, "no_bounded_donor_bands", shape)
    source_frame, target_frame = source.frame, target.frame
    source_axes = source_frame.basis_lps / source_frame.spacing_rc
    target_axes = target_frame.basis_lps / target_frame.spacing_rc
    source_step = float(np.max(np.diff(interior.profiles.distances_mm), initial=0))
    target_step = float(np.max(np.diff(offsets), initial=0))
    points = interior.edge_points_rc[edges]
    direction = interior.edge_normals_rc[edges] @ source_axes.T
    center_offset = (interior.band_low_mm[edges] + interior.band_high_mm[edges]) / 2
    center_lps = source_frame.to_patient(points) + center_offset[:, None] * direction
    native_points = target_frame.to_native(center_lps)
    projected = direction @ np.linalg.pinv(target_axes).T
    projection_norm = np.linalg.norm(projected @ target_axes.T, axis=1)
    usable = projection_norm > np.finfo(np.float64).eps
    normals = projected / np.where(usable, projection_norm, 1)[:, None]
    # Placeholder solely allows the sampler to retain unsupported rows. Those
    # rows are explicitly normal_unavailable and cannot become constraints.
    normals[~usable] = np.array((1.0, 0.0)) / np.linalg.norm(target_axes[:, 0])
    tangent = np.zeros_like(points)
    row_edge = points[:, 0] != np.floor(points[:, 0])
    tangent[row_edge, 1] = 0.5
    tangent[~row_edge, 0] = 0.5
    tangent_lps = tangent @ source_frame.basis_lps.T
    source_half = (
        interior.band_high_mm[edges] - interior.band_low_mm[edges] + source_step
    ) / 2
    source_quads = band_quads(
        center_lps, direction, tangent_lps, -source_half, source_half
    )
    donor_quads = target_frame.to_native(source_quads.reshape(-1, 3)).reshape(-1, 4, 2)
    target_normal = np.cross(target_axes[:, 0], target_axes[:, 1])
    target_normal /= np.linalg.norm(target_normal)
    source_normal = np.cross(source_axes[:, 0], source_axes[:, 1])
    source_normal /= np.linalg.norm(source_normal)
    angle = float(
        np.degrees(np.arccos(np.clip(abs(source_normal @ target_normal), 0, 1)))
    )
    off_plane = (source_quads - target_frame.origin_lps) @ target_normal
    coverage = np.full(len(edges), COVERAGE["covered"], dtype=np.uint8)
    thickness = target.slice_thickness_mm
    if thickness is None:
        coverage[:] = COVERAGE["slab_support_unknown"]
    else:
        coverage[np.any(np.abs(off_plane) > thickness / 2, axis=1)] = COVERAGE[
            "outside_slab"
        ]
    coverage[~usable] = COVERAGE["normal_unavailable"]
    profiles = sample_profiles(
        target.acquired_plane,
        native_points,
        normals,
        offsets,
        target_frame.spacing_rc,
        backend,
        metric_rc=target_axes.T @ target_axes,
    )
    half = source_half * projection_norm
    runs, bounded, opened, low, high = selected_runs(
        profiles, recipient.split, -half, half
    )
    facts = np.column_stack(
        (coverage, profiles.valid.sum(axis=1), runs, bounded, opened)
    )
    unique, inverse = np.unique(facts, axis=0, return_inverse=True)
    coverage_names = {value: name for name, value in COVERAGE.items()}
    decisions = np.asarray(
        [
            EXCHANGE_CODES[
                exchange_code(
                    coverage_names[int(c)], int(v), len(offsets), int(r), int(b), int(o)
                )
            ]
            for c, v, r, b, o in unique
        ],
        dtype=np.uint8,
    )
    codes = decisions[inverse]
    concurrent = codes == EXCHANGE_CODES["concurrent"]
    peer_only = codes == EXCHANGE_CODES["peer_only"]
    low[~concurrent], high[~concurrent] = np.nan, np.nan
    displacement = normals / target_frame.spacing_rc
    trace = native_points + ((low + high) / 2)[:, None] * displacement
    target_tangent = tangent_lps @ np.linalg.pinv(target_frame.basis_lps).T
    # Inert finite placeholders allow one strict raster contract for every row.
    quads = band_quads(
        native_points,
        displacement,
        target_tangent,
        np.where(concurrent, low, 0),
        np.where(concurrent, high, 0),
    )
    shared_mask, shared_visits = raster_bands(quads, concurrent, shape, backend)
    peer_mask, peer_visits = raster_bands(donor_quads, peer_only, shape, backend)
    conditional = handed_on(shared_mask | peer_mask)
    arrays = (
        edges.astype(np.int64),
        interior.edge_regions[edges].copy(),
        native_points.copy(),
        normals,
        donor_quads.copy(),
        off_plane,
        coverage,
        runs,
        bounded,
        opened,
        low,
        high,
        trace,
        codes,
        quads,
    )
    for array in arrays:
        handed_on(array)
    return BoundaryExchange(
        donor_uid=donor.series_uid,
        code="measured",
        source_edge_indices=arrays[0],
        source_regions=arrays[1],
        points_rc=arrays[2],
        normals_rc=arrays[3],
        donor_quads_rc=arrays[4],
        off_plane_mm=arrays[5],
        coverage_codes=arrays[6],
        normal_angle_degrees=angle,
        resolution_step_mm=max(source_step, target_step),
        profiles=profiles,
        dark_runs=arrays[7],
        bounded_matches=arrays[8],
        open_matches=arrays[9],
        band_low_mm=arrays[10],
        band_high_mm=arrays[11],
        derived_trace_rc=arrays[12],
        trace_codes=arrays[13],
        concurrent_quads_rc=arrays[14],
        concurrent_barrier=shared_mask,
        conditional_barrier=conditional,
        raster_visits=(shared_visits, peer_visits),
    )


@contracted(CONTRACT)
def converse(
    inputs: tuple[ConversationInput, ...],
    offsets_mm: np.ndarray,
    backend: str = "reference",
) -> tuple[SeriesConversation, ...]:
    """All ordered original same-orientation readings in one study, once."""
    offsets = np.asarray(offsets_mm, dtype=np.float64)
    if (
        offsets.ndim != 1
        or not len(offsets)
        or not np.all(np.isfinite(offsets))
        or np.any(np.diff(offsets) <= 0)
        or not np.any(offsets == 0)
    ):
        raise ValueError("invalid_border_offsets")
    if backend not in ("reference", "jit"):
        raise ValueError("invalid_backend")
    if len({item.series_uid for item in inputs}) != len(inputs):
        raise ValueError("duplicate_series_identity")
    results = []
    for recipient in inputs:
        measurement = recipient.measurement
        if measurement is None or measurement.interiors is None:
            shape = (0, 0)
            if measurement is not None and measurement.acquired_plane is not None:
                shape = measurement.acquired_plane.shape
            mask = handed_on(np.zeros(shape, dtype=bool))
            labels = handed_on(np.zeros(shape, dtype=np.int32))
            parents = handed_on(np.zeros(1, dtype=np.int32))
            results.append(
                SeriesConversation(
                    recipient.series_uid,
                    "recipient_unavailable",
                    (),
                    mask,
                    mask,
                    labels,
                    labels,
                    parents,
                    parents,
                )
            )
            continue
        labels = measurement.interiors.labels
        peers = tuple(
            exchange(donor, recipient, offsets, backend)
            for donor in inputs
            if donor.series_uid != recipient.series_uid
            and donor.orientation == recipient.orientation
        )
        shared, conditional = (
            np.zeros(labels.shape, dtype=bool),
            np.zeros(labels.shape, dtype=bool),
        )
        for peer in peers:
            shared |= peer.concurrent_barrier
            conditional |= peer.conditional_barrier
        shared_labels, shared_parents = subdivide(labels, shared)
        conditional_labels, conditional_parents = subdivide(labels, conditional)
        results.append(
            SeriesConversation(
                recipient.series_uid,
                "measured" if peers else "solitary",
                peers,
                handed_on(shared),
                handed_on(conditional),
                shared_labels,
                conditional_labels,
                shared_parents,
                conditional_parents,
            )
        )
    return tuple(results)
