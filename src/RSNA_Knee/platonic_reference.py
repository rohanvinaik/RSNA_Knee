"""The platonic knee reference — squash + superposition (THEORY II.2).

Byzantine weighted consensus over N registered reference knees, position by
position, generalized base->pixel: each reference cell is a DISTRIBUTION over
intensity across the squashed references, not a single value. The cell's
spread IS its per-cell tolerance — normal anatomical variation is absorbed
into the reference and zeros out in the KneeDiff residual; only deviation the
reference does not license survives.

Port provenance (Serena/LSP-probed 2026-08-28):
- `ByzantineConsensusBuilder.compute_consensus_base` — weighted vote,
  confidence = winning weight fraction. Here the discrete symbol vote becomes
  weighted mean/std over continuous intensity; confidence generalizes to
  1/(1+sigma) implicitly via the tolerance in `residual_z`.
- `ConsensusBase` struct (value . confidence . entropy . disagreements .
  p-value) — carried as per-cell (mu, sigma, n) arrays; entropy of a
  continuous cell is monotone in sigma, so sigma is stored directly.
- NOT ported: the consecutive-disagreement exponential decay (a genomics
  SNP-frequency model, wrong physics for pixels) and the IUPAC ambiguity
  codes (discrete-alphabet machinery).

This module is the ARRAY SHELL: it vectorizes the pure per-cell definitions
in `kneediff.py` without re-deriving them. Every array op mirrors the scalar
function of the same meaning.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ReferenceCells:
    """Per-cell distribution of the platonic reference.

    mu, sigma have the study shape; n is the number of references squashed.
    A cell with sigma near zero is a strong claim ("all references agree
    here"); a wide-sigma cell licenses normal anatomical variation.
    """

    mu: np.ndarray
    sigma: np.ndarray
    n: int


def build_reference(stack: np.ndarray, weights: list | None = None) -> ReferenceCells:
    """Squash N registered normal studies into the platonic reference.

    stack: (N, *study_shape) array of intensity values, ALREADY registered
    into the canonical space (II.1) — the subtract is only valid cell-to-cell.
    weights: optional per-reference weights (Byzantine weighted vote).
    """
    if stack.ndim < 2 or stack.shape[0] < 2:
        raise ValueError(
            "need at least 2 registered reference studies stacked on axis 0"
        )
    if weights is None:
        mu = stack.mean(axis=0)
        sigma = stack.std(axis=0, ddof=1)
    else:
        w = np.asarray(weights, dtype=np.float64)
        if w.shape[0] != stack.shape[0]:
            raise ValueError("one weight per reference study required")
        w = w / w.sum()
        mu = np.tensordot(w, stack, axes=(0, 0))
        var = np.tensordot(w, (stack - mu) ** 2, axes=(0, 0))
        # unbiased-ish correction for weighted variance
        var = var / max(1.0 - float((w**2).sum()), np.finfo(np.float64).eps)
        sigma = np.sqrt(var)
    return ReferenceCells(mu=mu, sigma=sigma, n=int(stack.shape[0]))


def residual_map(
    study: np.ndarray, ref: ReferenceCells, sigma_floor: float
) -> np.ndarray:
    """Vectorized `kneediff.residual_z` over every cell of a registered study."""
    if study.shape != ref.mu.shape:
        raise ValueError("study is not in the reference space (register first — II.1)")
    spread = np.maximum(ref.sigma, sigma_floor)
    return (study - ref.mu) / spread


def _gaussian_smooth_2d(field: np.ndarray, sigma: float) -> np.ndarray:
    """FFT Gaussian smoothing of a 2-D field (no scipy dependency)."""
    fy = np.fft.fftfreq(field.shape[0])[:, None]
    fx = np.fft.fftfreq(field.shape[1])[None, :]
    kernel = np.exp(-2.0 * (np.pi**2) * (sigma**2) * (fy**2 + fx**2))
    return np.real(np.fft.ifft2(np.fft.fft2(field) * kernel))


def detrend_diff(
    diff: np.ndarray, knee: np.ndarray, spatial_sigma: float
) -> np.ndarray:
    """Remove the LOW-FREQUENCY component of a difference field, per slice.

    The v3 diagnosis (decisions/2026-08-29-encoder-iteration-ladder.md):
    residual saturation pockets are uniform-sign offsets over whole tissue
    compartments — protocol contrast residue that global histogram matching
    cannot reconcile locally. Those offsets are LARGE-SCALE; pathology is
    LESION-SCALE. Subtracting a mask-aware Gaussian trend (sigma set well
    above lesion scale) removes the nuisance field and keeps the signal.

    Mask-aware: trend = smooth(diff*knee)/smooth(knee), so background zeros
    do not bleed into the tissue trend. Off-knee cells return 0.
    """
    out = np.zeros_like(diff)
    for zi in range(diff.shape[0]):
        k = knee[zi].astype(np.float64)
        if not k.any():
            continue
        num = _gaussian_smooth_2d(diff[zi] * k, spatial_sigma)
        den = _gaussian_smooth_2d(k, spatial_sigma)
        trend = np.where(den > 1e-6, num / np.maximum(den, 1e-6), 0.0)
        out[zi] = np.where(knee[zi], diff[zi] - trend, 0.0)
    return out


def detrended_residual_map(
    study: np.ndarray,
    ref: ReferenceCells,
    sigma_floor: float,
    knee: np.ndarray,
    spatial_sigma: float,
) -> np.ndarray:
    """Residual map with low-frequency nuisance removal (encoder rung v4).

    Same per-cell license as `residual_map` (spread IS tolerance), applied to
    the DETRENDED difference: deviation the reference does not license AND
    that is not explained by a smooth protocol-residue field.
    """
    if study.shape != ref.mu.shape:
        raise ValueError("study is not in the reference space (register first — II.1)")
    diff = detrend_diff(study - ref.mu, knee, spatial_sigma)
    spread = np.maximum(ref.sigma, sigma_floor)
    return diff / spread


def surviving_mask(z_map: np.ndarray, z_thresh: float) -> np.ndarray:
    """Vectorized `kneediff.classify_cell`: True where the residual survives."""
    return np.abs(z_map) >= z_thresh


def study_survival_fraction(z_map: np.ndarray, z_thresh: float) -> float:
    """Vectorized `kneediff.survival_fraction` for one study."""
    if z_map.size == 0:
        return 0.0
    return float(surviving_mask(z_map, z_thresh).mean())


def _integral(m: np.ndarray) -> np.ndarray:
    ii = np.zeros((m.shape[0] + 1, m.shape[1] + 1), dtype=np.int64)
    ii[1:, 1:] = np.cumsum(np.cumsum(m.astype(np.int64), axis=0), axis=1)
    return ii


def _window_sums(ii: np.ndarray, k: int) -> np.ndarray:
    return ii[k:, k:] - ii[:-k, k:] - ii[k:, :-k] + ii[:-k, :-k]


def max_masked_window_density(
    dev_mask: np.ndarray,
    knee_mask: np.ndarray,
    window: int,
    min_knee_frac: float = 0.75,
) -> float:
    """Peak local deviant density measured over KNEE TISSUE only.

    Vectorizes `kneediff.window_is_scorable`: density = deviants / knee-cells
    per window; windows with knee coverage below `min_knee_frac` are skipped
    (a mostly-air window with 3 deviant cells is not a dense lesion). Returns
    0.0 when no window is scorable.
    """
    if dev_mask.ndim != 2 or knee_mask.shape != dev_mask.shape:
        raise ValueError("expected matching 2-D masks")
    h, w = dev_mask.shape
    if h < window or w < window:
        knee = int(knee_mask.sum())
        if knee < min_knee_frac * dev_mask.size:
            return 0.0
        return float((dev_mask & knee_mask).sum()) / max(knee, 1)
    k = window
    dev_counts = _window_sums(_integral(dev_mask & knee_mask), k)
    knee_counts = _window_sums(_integral(knee_mask), k)
    scorable = knee_counts >= min_knee_frac * (k * k)
    if not scorable.any():
        return 0.0
    density = dev_counts[scorable] / knee_counts[scorable]
    return float(density.max())


def max_window_density(mask: np.ndarray, window: int) -> float:
    """Peak LOCAL concentration of surviving cells: the max fraction of True
    cells inside any `window`-sized box (2-D sliding window via integral image).

    This is the statistic the theory's claim actually predicts — pathology is a
    LOCALIZED cluster of unlicensed deviation, so a lesion that is invisible in
    the global survival fraction (diluted over the study) is a spike here,
    while scattered scanner noise is not. It is also what the per-finding lens
    (II.5) will consume: a candidate region, not a global scalar.
    """
    if mask.ndim != 2:
        raise ValueError("max_window_density expects a 2-D mask (per-slice)")
    h, w = mask.shape
    if h < window or w < window:
        return float(mask.mean()) if mask.size else 0.0
    ii = np.zeros((h + 1, w + 1), dtype=np.int64)
    ii[1:, 1:] = np.cumsum(np.cumsum(mask.astype(np.int64), axis=0), axis=1)
    k = window
    counts = ii[k:, k:] - ii[:-k, k:] - ii[k:, :-k] + ii[:-k, :-k]
    return float(np.max(counts)) / float(k * k)
