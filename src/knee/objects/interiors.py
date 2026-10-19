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
class InteriorRegions:
    """One plane's geometric interiors before any border is read: the code, the measured low
    signal, which places are available, each place's distance from the surrounding constraints,
    the interior peaks and the territories grown from them. The first half of `read_interiors`,
    for a reader that needs only the territories."""

    code: str
    dark: np.ndarray
    available: np.ndarray
    distance_mm: np.ndarray
    markers: np.ndarray
    labels: np.ndarray


@dataclass(frozen=True, slots=True)
class InteriorReading(InteriorRegions):
    """The territories (`InteriorRegions`) and the border readings across them: every edge between
    two regions, with its outward direction and its kind, and the dark band the profile across it
    shows. The territories' fields come first, so a reader of the territories reads either."""

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
    scope: "LensScope | None" = None,
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
    regions = _regions(plane, spacing, split, prominence_mm, available, scope=scope)
    points, normals, kinds = boundary_edges(
        regions.labels, regions.dark, regions.available, metric
    )
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
        regions.code,
        regions.dark,
        regions.available,
        regions.distance_mm,
        regions.markers,
        regions.labels,
        points,
        normals,
        kinds,
        handed_on(trace),
        handed_on(codes),
    )


def interior_regions(
    plane: np.ndarray,
    spacing_rc: tuple[float, float],
    split: float,
    prominence_mm: float,
    *,
    available: np.ndarray | None = None,
    scope: "LensScope | None" = None,
) -> InteriorRegions:
    """The territories alone, without the border readings `read_interiors` adds to them: for a
    reader that reads only the territories, which then makes nothing it throws away. The same
    arrays `read_interiors` returns for the same plane; `available` as there."""
    numeric_plane(plane)
    spacing = spacing_pair(spacing_rc)
    if not np.isfinite(prominence_mm) or prominence_mm <= 0:
        raise ValueError("invalid_prominence_mm")
    if np.isinf(split):
        raise ValueError("invalid_background_split")
    return _regions(plane, spacing, split, prominence_mm, available, scope=scope)


def _regions(
    plane: np.ndarray,
    spacing: tuple[float, float],
    split: float,
    prominence_mm: float,
    available: np.ndarray | None,
    *,
    scope: "LensScope | None" = None,
) -> InteriorRegions:
    """The geometric interiors of a plane its caller has already checked: the low signal under the
    split, the distance from it, the prominent peaks and the territories grown from them."""
    if scope is not None:
        return _scoped_regions(plane, spacing, split, prominence_mm, available, scope)
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
    return InteriorRegions(
        code,
        handed_on(dark),
        handed_on(available),
        handed_on(distance),
        handed_on(markers),
        handed_on(labels),
    )


@dataclass(frozen=True, slots=True)
class LensScope:
    """Tiles retained for lens work and their bounded native-pixel window.

    `in_scope_tiles` is true for every tile except a fully observed, low tile
    connected to the tile-grid exterior. This is a work prior, not an anatomical
    or air label.
    """

    in_scope_tiles: np.ndarray
    window_rc: tuple[int, int, int, int]
    in_scope_tile_count: int
    code: str = "bounded_scope"
    reason: str | None = None


def _validate_tile_bounds(bounds_rc, tile_shape, plane_shape):
    """Validate SquintStack bounds in (TR, TC, [r0,r1,c0,c1]) layout."""
    try:
        bounds = np.asarray(bounds_rc, dtype=np.float64)
    except (TypeError, ValueError) as error:
        raise ValueError("bounds_rc must contain numeric half-open bounds") from error
    expected = (*tile_shape, 4)
    if bounds.shape != expected:
        raise ValueError(f"bounds_rc must have shape {expected}, got {bounds.shape}")
    if not np.all(np.isfinite(bounds)) or np.any(bounds != np.rint(bounds)):
        raise ValueError("bounds_rc must contain finite integer bounds")
    bounds = bounds.astype(np.int64)
    rows, cols = plane_shape
    if (
        np.any(bounds[..., 0] < 0)
        or np.any(bounds[..., 1] > rows)
        or np.any(bounds[..., 2] < 0)
        or np.any(bounds[..., 3] > cols)
        or np.any(bounds[..., 0] >= bounds[..., 1])
        or np.any(bounds[..., 2] >= bounds[..., 3])
    ):
        raise ValueError("bounds_rc must satisfy 0 <= start < stop <= plane shape")
    row_bounds = bounds[:, 0, :2]
    col_bounds = bounds[0, :, 2:]
    if not np.array_equal(
        bounds[..., :2], np.broadcast_to(row_bounds[:, None, :], bounds[..., :2].shape)
    ):
        raise ValueError("bounds_rc row bounds must be shared across each tile row")
    if not np.array_equal(
        bounds[..., 2:], np.broadcast_to(col_bounds[None, :, :], bounds[..., 2:].shape)
    ):
        raise ValueError(
            "bounds_rc column bounds must be shared across each tile column"
        )
    if np.any(row_bounds[1:, 0] < row_bounds[:-1, 1]):
        raise ValueError("bounds_rc row tiles must be ordered and non-overlapping")
    if np.any(col_bounds[1:, 0] < col_bounds[:-1, 1]):
        raise ValueError("bounds_rc column tiles must be ordered and non-overlapping")
    return row_bounds, col_bounds


def lens_scope(maximum, coverage, bounds_rc, split, plane_shape) -> LensScope:
    """Build the 4-connected exterior-low exclusion for one SquintStack slice.

    Only finite maxima from fully covered tiles at or below a finite split are
    low candidates. The connected components touching the tile-grid rim are the
    low border; all other tiles remain in scope. The window is the tile-aligned
    in-scope bounding box plus one neighboring tile on each side, clamped by the
    native bounds. If there are no exterior-low tiles, the frame remains in
    scope; if all tiles are exterior low, the window is empty.
    """
    try:
        maximum = np.asarray(maximum, dtype=np.float64)
        coverage = np.asarray(coverage, dtype=np.float64)
    except (TypeError, ValueError) as error:
        raise ValueError("maximum and coverage must be numeric") from error
    if maximum.ndim != 2 or maximum.size == 0:
        raise ValueError(
            f"maximum must be a non-empty 2-D tile grid, got {maximum.shape}"
        )
    if coverage.shape != maximum.shape:
        raise ValueError(
            f"coverage shape {coverage.shape} does not match maximum {maximum.shape}"
        )
    if (
        np.isinf(coverage).any()
        or np.any(coverage[np.isfinite(coverage)] < 0)
        or np.any(coverage[np.isfinite(coverage)] > 1)
    ):
        raise ValueError("finite coverage values must be within [0, 1]")
    try:
        plane_shape = tuple(plane_shape)
    except TypeError as error:
        raise ValueError("plane_shape must be a pair of positive integers") from error
    if (
        len(plane_shape) != 2
        or not all(
            isinstance(v, (int, np.integer)) and not isinstance(v, bool)
            for v in plane_shape
        )
        or min(plane_shape) <= 0
    ):
        raise ValueError(
            f"plane_shape must be a pair of positive integers, got {plane_shape!r}"
        )
    plane_shape = tuple(map(int, plane_shape))
    row_bounds, col_bounds = _validate_tile_bounds(
        bounds_rc, maximum.shape, plane_shape
    )
    try:
        split = float(split)
    except (TypeError, ValueError) as error:
        raise ValueError("split must be a real scalar") from error
    low = (
        np.isfinite(coverage)
        # Coverage is validated <= 1 above: this admits only the exact endpoint.
        & (coverage >= 1.0)
        & np.isfinite(maximum)
        & (maximum <= split)
        if np.isfinite(split)
        else np.zeros(maximum.shape, dtype=bool)
    )
    components, count = ndi.label(low, structure=ndi.generate_binary_structure(2, 1))
    exterior = np.zeros(maximum.shape, dtype=bool)
    if count:
        rim = np.concatenate(
            (components[0], components[-1], components[:, 0], components[:, -1])
        )
        exterior = np.isin(components, np.unique(rim[rim > 0]))
    in_scope = ~exterior
    in_scope_count = int(np.count_nonzero(in_scope))
    row_tiles_cover_frame = (
        row_bounds[0, 0] == 0
        and row_bounds[-1, 1] == plane_shape[0]
        and np.array_equal(row_bounds[1:, 0], row_bounds[:-1, 1])
    )
    col_tiles_cover_frame = (
        col_bounds[0, 0] == 0
        and col_bounds[-1, 1] == plane_shape[1]
        and np.array_equal(col_bounds[1:, 0], col_bounds[:-1, 1])
    )
    grid_covers_frame = row_tiles_cover_frame and col_tiles_cover_frame
    if not grid_covers_frame:
        window = (0, plane_shape[0], 0, plane_shape[1])
        code = "full_frame_tile_bounds_incomplete"
        reason = "tile bounds do not cover the native frame continuously"
    elif not exterior.any():
        window = (0, plane_shape[0], 0, plane_shape[1])
        code = "full_frame_no_exterior_low_border"
        reason = "no fully observed exterior-connected low tile was measured"
    elif not in_scope_count:
        window = (0, 0, 0, 0)
        code = "empty_scope_all_exterior_low"
        reason = None
    else:
        hit_rows = np.flatnonzero(in_scope.any(axis=1))
        hit_cols = np.flatnonzero(in_scope.any(axis=0))
        row_lo, row_hi = int(hit_rows[0]), int(hit_rows[-1])
        col_lo, col_hi = int(hit_cols[0]), int(hit_cols[-1])
        row_lo = max(row_lo - 1, 0)
        row_hi = min(row_hi + 1, len(row_bounds) - 1)
        col_lo = max(col_lo - 1, 0)
        col_hi = min(col_hi + 1, len(col_bounds) - 1)
        window = (
            int(row_bounds[row_lo, 0]),
            int(row_bounds[row_hi, 1]),
            int(col_bounds[col_lo, 0]),
            int(col_bounds[col_hi, 1]),
        )
        code = "bounded_scope"
        reason = None
    in_scope = handed_on(in_scope)
    return LensScope(in_scope, window, in_scope_count, code, reason)


def full_frame_scope(plane_shape, *, reason: str, tile_shape=None) -> LensScope:
    """Named full-frame scope when no usable squint grid can constrain lens work.

    Zero-sized dimensions are retained so the interior reader can preserve its
    existing `empty_plane` result.
    """
    try:
        shape = tuple(plane_shape)
    except TypeError as error:
        raise ValueError("plane_shape must be a pair of positive integers") from error
    if (
        len(shape) != 2
        or not all(
            isinstance(value, (int, np.integer)) and not isinstance(value, bool)
            for value in shape
        )
        or min(shape) < 0
    ):
        raise ValueError(
            f"plane_shape must be a pair of positive integers, got {plane_shape!r}"
        )
    shape = tuple(map(int, shape))
    if tile_shape is None:
        in_scope_tiles = np.zeros((0, 0), dtype=bool)
    else:
        try:
            tile_shape = tuple(tile_shape)
        except TypeError as error:
            raise ValueError(
                "tile_shape must be a pair of non-negative integers"
            ) from error
        if (
            len(tile_shape) != 2
            or not all(
                isinstance(value, (int, np.integer)) and not isinstance(value, bool)
                for value in tile_shape
            )
            or min(tile_shape) < 0
        ):
            raise ValueError("tile_shape must be a pair of non-negative integers")
        in_scope_tiles = np.ones(tuple(map(int, tile_shape)), dtype=bool)
    in_scope_tiles = handed_on(in_scope_tiles)
    return LensScope(
        in_scope_tiles,
        (0, shape[0], 0, shape[1]),
        int(np.count_nonzero(in_scope_tiles)),
        "full_frame_squint_unavailable",
        str(reason),
    )


def _scope_window(scope: LensScope, plane_shape) -> tuple[int, int, int, int]:
    """Check the cached scope before allowing it to restrict geometric work."""
    if not isinstance(scope, LensScope):
        raise TypeError("scope must be a LensScope")
    tiles = scope.in_scope_tiles
    if not isinstance(tiles, np.ndarray) or tiles.dtype != np.bool_ or tiles.ndim != 2:
        raise ValueError("scope.in_scope_tiles must be a 2-D bool array")
    if int(np.count_nonzero(tiles)) != scope.in_scope_tile_count:
        raise ValueError("scope.in_scope_tile_count does not match in_scope_tiles")
    try:
        values = tuple(scope.window_rc)
    except TypeError as error:
        raise ValueError("scope.window_rc must contain four integers") from error
    if len(values) != 4 or any(
        not isinstance(v, (int, np.integer)) or isinstance(v, bool) for v in values
    ):
        raise ValueError("scope.window_rc must contain four integers")
    r0, r1, c0, c1 = map(int, values)
    if r0 > r1 or c0 > c1:
        raise ValueError(f"invalid scope window {values!r}")
    if np.prod(plane_shape) and (
        r0 < 0 or c0 < 0 or r1 > plane_shape[0] or c1 > plane_shape[1]
    ):
        raise ValueError(f"scope window {values!r} lies outside plane {plane_shape}")
    return r0, r1, c0, c1


def _scoped_regions(plane, spacing, split, prominence_mm, available, scope):
    """Shared scoped core for drawn and undrawn interior readings."""
    r0, r1, c0, c1 = _scope_window(scope, plane.shape)
    if available is not None and np.shape(available) != plane.shape:
        raise ValueError(
            f"available shape {np.shape(available)} does not match plane {plane.shape}"
        )
    # A full-frame scope needs no scatter buffers or duplicate local reading.
    if (r0, r1, c0, c1) == (0, plane.shape[0], 0, plane.shape[1]):
        safe_available = (
            None if available is None else np.asarray(available, dtype=bool)
        )
        # Preserve caller ownership; production already supplies an immutable shared finite mask.
        if safe_available is not None and safe_available.flags.writeable:
            safe_available = safe_available.copy()
        return _regions(plane, spacing, split, prominence_mm, safe_available)
    full_available = (
        np.isfinite(plane)
        if available is None
        else np.array(available, dtype=bool, copy=True)
    )
    dark = (
        full_available & (plane <= split)
        if np.isfinite(split)
        else np.zeros(plane.shape, dtype=bool)
    )
    if not plane.size or not np.any(full_available) or not np.isfinite(split):
        return _regions(plane, spacing, split, prominence_mm, full_available)

    distance = np.zeros(plane.shape, dtype=np.float64)
    markers = np.zeros(plane.shape, dtype=np.int32)
    labels = np.zeros(plane.shape, dtype=np.int32)
    code = "no_interior_seeds"
    if r1 > r0 and c1 > c0:
        window = (slice(r0, r1), slice(c0, c1))
        inner = _regions(
            plane[window], spacing, split, prominence_mm, full_available[window]
        )
        code = inner.code if inner.code != "no_finite_support" else "no_interior_seeds"
        distance[window] = inner.distance_mm
        markers[window] = inner.markers
        labels[window] = inner.labels
    return InteriorRegions(
        code,
        handed_on(dark),
        handed_on(full_available),
        handed_on(distance),
        handed_on(markers),
        handed_on(labels),
    )
