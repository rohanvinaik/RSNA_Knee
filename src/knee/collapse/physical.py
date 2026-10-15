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
    allocation="64 bytes per output tile; per-tile finite mask, gathered values and NumPy median scratch",
    work="per-tile finite scan/extraction, median selection and extrema reductions",
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
        points = np.asarray(points_rc, dtype=np.float64)
        if points.ndim != 2 or points.shape[1] != 2 or not np.all(np.isfinite(points)):
            raise ValueError("invalid_native_points")
        return handed_on(points @ self.basis_lps.T + self.origin_lps)

    def to_native(self, points_lps: np.ndarray) -> np.ndarray:
        points = np.asarray(points_lps, dtype=np.float64)
        if points.ndim != 2 or points.shape[1] != 3 or not np.all(np.isfinite(points)):
            raise ValueError("invalid_patient_points")
        return handed_on((points - self.origin_lps) @ np.linalg.pinv(self.basis_lps).T)


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
    bounds = np.empty((*shape, 4), dtype=np.int64)
    for r in range(shape[0]):
        for c in range(shape[1]):
            r0, c0 = r * tile[0], c * tile[1]
            r1, c1 = (
                min(r0 + tile[0], plane.shape[0]),
                min(c0 + tile[1], plane.shape[1]),
            )
            block = plane[r0:r1, c0:c1]
            values = block[finite[r0:r1, c0:c1]]
            bounds[r, c] = r0, r1, c0, c1
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
