"""Physical frames and squints measure geometry and signal; neither assigns an object."""

from dataclasses import dataclass
from math import ceil

import numpy as np

from knee.compute.contracts import ComputeContract, contracted, handed_on

CONTRACT = ComputeContract(
    kind="measurement",
    language="NumPy",
    reads="2D original plane; physical spacing and tile mm; its finite mask when already read",
    writes="4 float64 tile maps and int64 native bounds",
    allocation="64 bytes per output tile; source-dtype gather batches up to 4,194,304 elements (or one larger tile); tile-count intermediates; per-tile fallback masks and median scratch",
    work="finite scan over complete tiles; batched extrema and median reductions for full tiles; per-tile finite extraction for partial and ragged tiles",
    parallel_unit="independent plane",
    reference="physical_squint",
    proof_gate="ragged coverage/extrema/median intent tests; source unchanged",
)


def spacing_pair(spacing_rc: tuple[float, float]) -> tuple[float, float]:
    values = np.asarray(spacing_rc, dtype=np.float64)
    if values.shape != (2,) or not np.all(np.isfinite(values)) or np.any(values <= 0):
        raise ValueError("invalid_spacing")
    return float(values[0]), float(values[1])


def numeric_plane(plane: np.ndarray) -> None:
    if (
        not isinstance(plane, np.ndarray)
        or plane.ndim != 2
        or plane.dtype.kind not in "iuf"
    ):
        raise ValueError("invalid_plane")


@dataclass(frozen=True, slots=True)
class PlaneFrame:
    """Native (row,column) to original DICOM LPS millimetres; no resampling.

    The first DICOM triplet is the direction of increasing COLUMN, the second
    increasing ROW. The 3×2 basis includes spacing. The inverse projects onto
    this plane, so off-plane distances are deliberately not recovered.
    """

    origin_lps: np.ndarray
    basis_lps: np.ndarray
    spacing_rc: tuple[float, float]

    @classmethod
    def from_dicom(cls, position, orientation, spacing_rc) -> "PlaneFrame":
        position = np.asarray(position, dtype=np.float64)
        orientation = np.asarray(orientation, dtype=np.float64)
        spacing = spacing_pair(spacing_rc)
        if position.shape != (3,) or not np.all(np.isfinite(position)):
            raise ValueError("invalid_position")
        if orientation.shape != (6,) or not np.all(np.isfinite(orientation)):
            raise ValueError("invalid_orientation")
        directions = np.column_stack((orientation[3:], orientation[:3]))
        # DICOM decimal direction cosines are rounded. This is a format check,
        # not an anatomical admission bar; preserve the original rounded basis.
        if not np.allclose(directions.T @ directions, np.eye(2), atol=1e-4, rtol=0):
            raise ValueError("degenerate_orientation")
        return cls(handed_on(position.copy()), handed_on(directions * spacing), spacing)

    def to_patient(self, points_rc: np.ndarray) -> np.ndarray:
        """Native (row, column) points (N, 2) in the scanner's millimetres (N, 3): the one statement
        of a slice's places in the scanner's frame."""
        points = np.asarray(points_rc, dtype=np.float64)
        if points.ndim != 2 or points.shape[1] != 2 or not np.all(np.isfinite(points)):
            raise ValueError("invalid_native_points")
        return handed_on(points @ self.basis_lps.T + self.origin_lps)

    def to_native(self, points_lps: np.ndarray) -> np.ndarray:
        """Places in the scanner's millimetres (N, 3) projected onto this plane, as native (row,
        column) points (N, 2): the one statement of the inverse, which every stage that carries a
        place from one slice of the knee onto another reads."""
        points = np.asarray(points_lps, dtype=np.float64)
        if points.ndim != 2 or points.shape[1] != 3 or not np.all(np.isfinite(points)):
            raise ValueError("invalid_patient_points")
        return handed_on((points - self.origin_lps) @ np.linalg.pinv(self.basis_lps).T)

    def normal(self) -> np.ndarray:
        """The plane's unit normal (3,), the rows' direction crossed with the columns': the one
        statement of it, which every stage that asks how far a place lies off the plane reads."""
        normal = np.cross(self.basis_lps[:, 0], self.basis_lps[:, 1])
        return normal / np.linalg.norm(normal)


@dataclass(frozen=True, slots=True)
class Squint:
    """Float64 maps (tile rows, tile columns), coverage in [0,1], native half-open bounds.

    All nonfinite pixels are missing. Empty-support tiles retain NaN extrema and
    median. Bounds have shape (tile rows,tile columns,4): r0,r1,c0,c1, int64.
    """

    median: np.ndarray
    minimum: np.ndarray
    maximum: np.ndarray
    coverage: np.ndarray
    bounds_rc: np.ndarray
    tile_shape_rc: tuple[int, int]


_BATCH_ELEMENTS = 1 << 22
_PLAIN_ARRAYS = (np.ndarray, np.memmap)


@contracted
def physical_squint(
    plane: np.ndarray,
    spacing_rc: tuple[float, float],
    tile_mm: float,
    finite: np.ndarray | None = None,
) -> Squint:
    """`finite` is which of the plane's pixels are finite, when the caller has read it once for
    the series; it is read here otherwise."""
    numeric_plane(plane)
    spacing = spacing_pair(spacing_rc)
    if not np.isfinite(tile_mm) or tile_mm <= 0:
        raise ValueError("invalid_tile_mm")
    finite = np.isfinite(plane) if finite is None else finite
    tile = tuple(max(1, ceil(tile_mm / step)) for step in spacing)
    shape = tuple(
        ceil(size / step) for size, step in zip(plane.shape, tile, strict=True)
    )
    median, minimum, maximum = (np.full(shape, np.nan) for _ in range(3))
    coverage = np.zeros(shape, dtype=np.float64)
    rows, cols = plane.shape
    starts_r = [r * tile[0] for r in range(shape[0])]
    starts_c = [c * tile[1] for c in range(shape[1])]
    bounds = np.empty((*shape, 4), dtype=np.int64)
    bounds[..., 0] = np.array(starts_r, dtype=np.int64)[:, None]
    bounds[..., 1] = np.array(
        [min(r0 + tile[0], rows) for r0 in starts_r], dtype=np.int64
    )[:, None]
    bounds[..., 2] = np.array(starts_c, dtype=np.int64)[None, :]
    bounds[..., 3] = np.array(
        [min(c0 + tile[1], cols) for c0 in starts_c], dtype=np.int64
    )[None, :]
    todo: list[tuple[int, int]] | None = None
    nr, nc = rows // tile[0], cols // tile[1]
    if (
        type(plane) in _PLAIN_ARRAYS
        and type(finite) in _PLAIN_ARRAYS
        and finite.dtype == np.bool_
        and finite.shape == plane.shape
        and nr
        and nc
    ):
        t0, t1 = tile
        size = t0 * t1
        span = (slice(0, nr * t0), slice(0, nc * t1))
        grid = (nr, t0, nc, t1)
        tiles = np.asarray(plane)[span].reshape(grid).transpose(0, 2, 1, 3)
        counts = np.asarray(finite)[span].reshape(grid).sum(axis=(1, 3))
        full = counts == size
        coverage[:nr, :nc][full] = 1.0
        grid_r, grid_c = np.nonzero(full)
        per = max(1, _BATCH_ELEMENTS // size)
        for s in range(0, grid_r.size, per):
            a, b = grid_r[s : s + per], grid_c[s : s + per]
            gathered = tiles[a, b].reshape(a.size, size)
            minimum[a, b] = gathered.min(axis=1)
            maximum[a, b] = gathered.max(axis=1)
            median[a, b] = np.median(gathered, axis=1, overwrite_input=True)
        todo = [(int(r), int(c)) for r, c in np.argwhere((counts > 0) & ~full)]
        todo += [(r, c) for r in range(nr, shape[0]) for c in range(shape[1])]
        todo += [(r, c) for r in range(nr) for c in range(nc, shape[1])]
    if todo is None:
        todo = [(r, c) for r in range(shape[0]) for c in range(shape[1])]
    for r, c in todo:
        r0, c0 = r * tile[0], c * tile[1]
        r1, c1 = (
            min(r0 + tile[0], plane.shape[0]),
            min(c0 + tile[1], plane.shape[1]),
        )
        block = plane[r0:r1, c0:c1]
        values = block[finite[r0:r1, c0:c1]]
        coverage[r, c] = values.size / block.size
        if values.size:
            median[r, c] = np.median(values)
            minimum[r, c], maximum[r, c] = np.min(values), np.max(values)
    return Squint(
        handed_on(median),
        handed_on(minimum),
        handed_on(maximum),
        handed_on(coverage),
        handed_on(bounds),
        (tile[0], tile[1]),
    )
