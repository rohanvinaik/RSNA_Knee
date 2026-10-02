"""Multi-scale HDC encode of the KneeDiff residual (THEORY II.4) — v1.

"The JSON format for reasoning": the sparse pathological residual becomes an
OTP hypervector, composed multi-scale so the study is more than a bag of
cells. Port provenance (LSP-probed 2026-08-28):

- Sparse-Hadamard position codebook — `production_adaptive_encoder.py`
  (`AdaptiveSparseHadamardCodebook`): each cell gets k active dimensions +
  Hadamard-derived signs from a seeded deterministic RNG; ternary cell
  values accumulate then sign-quantize; magnitude returns at decode as
  similarity strength (margin = confidence).
- Multi-scale composition — GSE THEORY §6 / the OTP synthesis: distinct
  scales in disjoint bank partitions of ONE space, composed by bind
  (role x filler), bundle (majority), never adjacency-linking.

The VALUE encoder is the pixel instantiation: a residual cell is ternary
  +1  unlicensed-bright deviation (z >= +thresh)
  -1  unlicensed-dark deviation  (z <= -thresh)
   0  licensed — the reference absorbs it (informational zero)

Scale ladder v1: cell -> ZONE (deterministic template-space grid — honest
placeholder for named anatomical structures until landmark anchors land)
-> STUDY. Zone-scale and study-scale live in disjoint halves of the space.

No learning anywhere: codebooks are seeded constructions, prototypes are
majority bundles, scores are dot products.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

D = 4096  # dimensions per bank partition
K = 4  # active dims per cell (GV production default for balanced content)
BASE_SEED = 1729


def ternary_cell(z: float, thresh: float) -> int:
    """The pixel value encoder: ternary OTP value of one residual cell.

    +1 unlicensed-bright, -1 unlicensed-dark, 0 licensed (informational
    zero — an active assertion that the reference absorbs this cell, not
    missing data).
    """
    if z >= thresh:
        return 1
    if z <= -thresh:
        return -1
    return 0


@dataclass(frozen=True)
class ZoneGrid:
    """Deterministic template-space zoning: (nz, ny, nx) grid of boxes."""

    nz: int = 3
    ny: int = 4
    nx: int = 4

    @property
    def n_zones(self) -> int:
        return self.nz * self.ny * self.nx

    def zone_of_cell(self, shape: tuple, z: int, y: int, x: int) -> int:
        zi = min(z * self.nz // shape[0], self.nz - 1)
        yi = min(y * self.ny // shape[1], self.ny - 1)
        xi = min(x * self.nx // shape[2], self.nx - 1)
        return (zi * self.ny + yi) * self.nx + xi

    def zone_index_volume(self, shape: tuple) -> np.ndarray:
        """(shape)-shaped int volume of zone ids — vectorized zone_of_cell."""
        zi = np.minimum(np.arange(shape[0]) * self.nz // shape[0], self.nz - 1)
        yi = np.minimum(np.arange(shape[1]) * self.ny // shape[1], self.ny - 1)
        xi = np.minimum(np.arange(shape[2]) * self.nx // shape[2], self.nx - 1)
        return (zi[:, None, None] * self.ny + yi[None, :, None]) * self.nx + xi[
            None, None, :
        ]


class ResidualHDCEncoder:
    """Encode ternary residual volumes into zone- and study-hypervectors."""

    def __init__(
        self,
        shape: tuple,
        grid: ZoneGrid | None = None,
        seed: int = BASE_SEED,
        zone_labels: np.ndarray | None = None,
    ):
        """`zone_labels`: template-space anatomical label volume (anatomy.py)
        — when given it REPLACES the grid zoning (the fleet Rank-1 design:
        zones as constant index masks; the analysis stack above is unchanged
        and inherits the localization gains)."""
        self.shape = shape
        n_cells = int(np.prod(shape))
        rng = np.random.default_rng(seed)
        # per-cell sparse codebook: K active dims + signs (deterministic)
        self.dims = rng.integers(0, D, size=(n_cells, K), dtype=np.int32)
        self.signs = rng.choice(np.array([-1, 1], dtype=np.int8), size=(n_cells, K))
        if zone_labels is not None:
            if zone_labels.shape != tuple(shape):
                raise ValueError("zone_labels shape must match the volume shape")
            self.grid = None
            self._n_zones = int(zone_labels.max()) + 1
            self.zone_ids = zone_labels.ravel().astype(np.int64)
        else:
            self.grid = grid or ZoneGrid()
            self._n_zones = self.grid.n_zones
            self.zone_ids = self.grid.zone_index_volume(shape).ravel()
        # zone-role vectors (dense ternary role per zone, for study-scale bind)
        self.zone_roles = rng.choice(
            np.array([-1, 1], dtype=np.int8), size=(self._n_zones, D)
        )

    def encode_zones(self, ternary: np.ndarray) -> np.ndarray:
        """(n_zones, D) int32 accumulators from a ternary residual volume.

        Vectorized accumulate: each nonzero cell adds value*sign into its K
        dims of its zone's accumulator — the GV accumulation loop, batched.
        """
        vals = ternary.ravel()
        nz = vals != 0
        if not nz.any():
            return np.zeros((self._n_zones, D), dtype=np.int32)
        cells = np.nonzero(nz)[0]
        contrib = (vals[cells, None] * self.signs[cells]).astype(np.int32)
        zones = self.zone_ids[cells]
        acc = np.zeros((self._n_zones, D), dtype=np.int32)
        flat = zones[:, None] * D + self.dims[cells]
        np.add.at(acc.reshape(-1), flat.ravel(), contrib.ravel())
        return acc

    def encode_study(self, ternary: np.ndarray) -> dict:
        """Full multi-scale encode: zone HVs + role-bound study HV.

        Zone scale: sign-quantized zone accumulators (ternary HVs).
        Study scale: bundle of (zone_role * zone_hv) binds — a higher scale
        IS a composition of the one below (THEORY II.4).
        """
        acc = self.encode_zones(ternary)
        zone_hvs = np.sign(acc).astype(np.int8)
        study_acc = (zone_hvs.astype(np.int32) * self.zone_roles.astype(np.int32)).sum(
            axis=0
        )
        study_hv = np.sign(study_acc).astype(np.int8)
        return {"zone_hvs": zone_hvs, "study_hv": study_hv, "zone_acc": acc}


def similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Normalized dot product of two hypervectors (margin channel)."""
    denom = float(np.sqrt((a != 0).sum() * (b != 0).sum()))
    if denom == 0:
        return 0.0
    return float(np.dot(a.astype(np.int32), b.astype(np.int32))) / denom


def bundle_prototype(hvs: list) -> np.ndarray:
    """Majority-bundle a set of hypervectors into a prototype (consensus in
    HV space — the same mechanism as the reference squash, one scale up)."""
    if not hvs:
        return np.zeros(D, dtype=np.int8)
    return np.sign(np.sum([h.astype(np.int32) for h in hvs], axis=0)).astype(np.int8)
