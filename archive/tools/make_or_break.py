"""The make-or-break test (THEORY Part III closing note, AGENTS.md working method).

Question under test: does the entropy-weighted superposition reference absorb
normal anatomical variation and leave ONLY pathology in the KneeDiff residual?
Everything downstream assumes it; this harness answers it and prints a named
verdict, never a vibe.

Two modes:

  --synthetic   Validates the MACHINERY, not the anatomy: N synthetic "normal
                knees" (shared structure + smooth per-study variation + noise),
                held-out normals, and abnormals with a localized lesion.
                Expected: verdict "reference_absorbs" WITH the lesion and
                "no_separation" WITHOUT it (the adversarial control — if the
                verdict can't fail on data with no signal, it isn't a test).

  --data-dir    The REAL test, runnable once competition DICOMs are registered
                (II.1) and exported as .npy in canonical space:
                  <dir>/reference/*.npy    registered normal studies (squash)
                  <dir>/normal/*.npy       held-out normal studies
                  <dir>/abnormal/*.npy     studies with a labeled finding
                The verdict on THIS data is the actual make-or-break call.

Usage:
  python tools/make_or_break.py --synthetic
  python tools/make_or_break.py --data-dir data/registered --z-thresh 3.0
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from RSNA_Knee.kneediff import make_or_break_verdict
from RSNA_Knee.platonic_reference import (
    build_reference,
    detrended_residual_map,
    max_masked_window_density,
    max_window_density,
    residual_map,
    study_survival_fraction,
    surviving_mask,
)
from RSNA_Knee.scoring import auc_status, roc_auc

SHAPE = (64, 64)


def _smooth_field(rng: np.random.Generator, shape: tuple, scale: float) -> np.ndarray:
    """Smooth low-frequency random field (Fourier low-pass of white noise) —
    per-study anatomical variation, the thing the reference must LICENSE.

    Deliberately NOT block-constant (an earlier kron-based fixture made all 64
    cells of a block share one draw, so correlated sigma-estimation error lit
    up whole blocks in held-out normals — a fixture artifact, not machinery).
    Design lesson carried to the REAL test: per-cell sigma from few references
    is noisy; use enough reference studies, and expect sigma shrinkage to be
    the pixel analogue of ConsensusBase.confidence if N stays small."""
    noise = rng.normal(0.0, 1.0, size=shape)
    fy = np.fft.fftfreq(shape[0])[:, None]
    fx = np.fft.fftfreq(shape[1])[None, :]
    lowpass = np.exp(-((fy**2 + fx**2) / (2 * 0.04**2)))
    field = np.real(np.fft.ifft2(np.fft.fft2(noise) * lowpass))
    sd = field.std()
    return field * (scale / sd) if sd > 0 else field


def synth_normal(rng: np.random.Generator) -> np.ndarray:
    """One synthetic 'normal knee': shared structure + licensed variation + noise."""
    yy, xx = np.mgrid[0 : SHAPE[0], 0 : SHAPE[1]]
    structure = np.sin(yy / 7.0) + np.cos(xx / 5.0)  # the shared anatomy
    variation = _smooth_field(rng, SHAPE, scale=0.30)  # normal anatomical variation
    noise = rng.normal(0.0, 0.05, size=SHAPE)  # scanner noise
    return structure + variation + noise


def synth_abnormal(rng: np.random.Generator, lesion_amp: float = 1.5) -> np.ndarray:
    """A normal study plus one localized lesion blob (the pathology)."""
    study = synth_normal(rng)
    cy, cx = rng.integers(12, SHAPE[0] - 12), rng.integers(12, SHAPE[1] - 12)
    yy, xx = np.mgrid[0 : SHAPE[0], 0 : SHAPE[1]]
    blob = np.exp(-((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * 3.0**2))
    return study + lesion_amp * blob


def run_split(
    reference_stack: np.ndarray,
    normals: list,
    abnormals: list,
    z_thresh: float,
    sigma_floor: float,
    min_studies: int,
    knee_mask: np.ndarray | None = None,
    detrend_sigma: float = 0.0,
) -> dict:
    """Build reference, compute survival fractions, return verdict + evidence.

    When `knee_mask` (template-space, from register_and_export v2) is given,
    local density is measured over knee tissue only and windows without
    sufficient knee coverage are skipped (II.1's background mask applied to
    the statistic, not just the subtract).
    """
    ref = build_reference(reference_stack)
    window = 9

    def local_density(mask2d: np.ndarray, kmask2d: np.ndarray | None) -> float:
        if kmask2d is not None:
            return max_masked_window_density(mask2d, kmask2d, window)
        return max_window_density(mask2d, window)

    def stats(study: np.ndarray) -> tuple:
        if detrend_sigma > 0 and knee_mask is not None:
            z_map = detrended_residual_map(
                study, ref, sigma_floor, knee_mask, detrend_sigma
            )
        else:
            z_map = residual_map(study, ref, sigma_floor)
        mask = surviving_mask(z_map, z_thresh)
        if mask.ndim == 3:
            # 3-D volume: peak local density over all slices — pathology is
            # localized in-plane and across a few slices
            local = max(
                local_density(mask[z], knee_mask[z] if knee_mask is not None else None)
                for z in range(mask.shape[0])
            )
        else:
            local = local_density(mask, knee_mask)
        return (study_survival_fraction(z_map, z_thresh), local)

    normal_stats = [stats(s) for s in normals]
    abnormal_stats = [stats(s) for s in abnormals]
    # The verdict keys on the AUC of LOCAL survivor density (the theory's
    # claim is that pathology is a localized cluster of unlicensed deviation;
    # a global fraction dilutes it). AUC is rank-based, so the small-N sigma
    # noise that shifts absolute levels barely moves it — and it is the
    # competition's own metric. Global fraction stays as evidence.
    normal_local = [d for _, d in normal_stats]
    abnormal_local = [d for _, d in abnormal_stats]
    labels = [0] * len(normal_local) + [1] * len(abnormal_local)
    scores = normal_local + abnormal_local
    auc = roc_auc(labels, scores) if auc_status(labels) == "ok" else 0.5
    verdict = make_or_break_verdict(
        auc, len(normal_local), len(abnormal_local), min_studies
    )
    return {
        "verdict": verdict,
        "statistic_auc": round(auc, 4),
        "statistic": f"max survivor density in {window}x{window} window",
        "normal_local_density": [round(d, 4) for d in normal_local],
        "abnormal_local_density": [round(d, 4) for d in abnormal_local],
        "normal_global_frac": [round(f, 5) for f, _ in normal_stats],
        "abnormal_global_frac": [round(f, 5) for f, _ in abnormal_stats],
        "n_reference": int(reference_stack.shape[0]),
        "z_thresh": z_thresh,
        "sigma_floor": sigma_floor,
        "detrend_sigma": detrend_sigma,
    }


def run_synthetic(z_thresh: float, sigma_floor: float) -> int:
    """Machinery wiring check + amplitude response curve.

    In this synthetic world 'normal variation' and 'lesion' are BOTH smooth
    bumps — the same kind of object, differing only in amplitude — so
    separation here is amplitude-driven BY CONSTRUCTION and says nothing about
    real anatomy (that is what --data-dir is for). What this validates:
      wiring    — a decisive lesion (amp >> variation) must yield
                  "reference_absorbs"; the no-lesion control must sit at
                  chance ("no_separation").
      response  — AUC as a function of lesion amplitude, printed as evidence
                  (a detector whose AUC does not rise with amplitude is wired
                  wrong even if end points pass).
    """
    rng = np.random.default_rng(1729)
    reference_stack = np.stack([synth_normal(rng) for _ in range(20)])
    held_out_normals = [synth_normal(rng) for _ in range(8)]
    controls = [synth_normal(rng) for _ in range(8)]  # "abnormals" with no lesion

    print(
        "=== SYNTHETIC make-or-break (machinery wiring + response curve, NOT anatomy) ==="
    )
    curve = {}
    strongest = None
    for amp in (0.5, 1.0, 1.5, 2.0, 3.0):
        abnormals = [synth_abnormal(rng, lesion_amp=amp) for _ in range(8)]
        res = run_split(
            reference_stack, held_out_normals, abnormals, z_thresh, sigma_floor, 3
        )
        curve[f"amp_{amp}"] = {"auc": res["statistic_auc"], "verdict": res["verdict"]}
        strongest = res
    control = run_split(
        reference_stack, held_out_normals, controls, z_thresh, sigma_floor, 3
    )

    print(
        json.dumps(
            {
                "response_curve": curve,
                "control_no_lesion": {
                    "auc": control["statistic_auc"],
                    "verdict": control["verdict"],
                },
                "strongest_split_detail": strongest,
            },
            indent=2,
        )
    )

    aucs = [
        curve[k]["auc"] for k in sorted(curve, key=lambda s: float(s.split("_")[1]))
    ]
    monotone_rising = all(b >= a - 0.05 for a, b in itertools.pairwise(aucs))
    ok = (
        strongest is not None
        and strongest["verdict"] == "reference_absorbs"
        and control["verdict"] == "no_separation"
        and monotone_rising
    )
    print(
        f"\nMACHINERY {'VALIDATED' if ok else 'FAILED'}: "
        f"strongest lesion -> {strongest['verdict'] if strongest else '?'} (want reference_absorbs); "
        f"control -> {control['verdict']} (want no_separation); "
        f"response curve {'rises' if monotone_rising else 'DOES NOT rise'} with amplitude {aucs}"
    )
    return 0 if ok else 1


def run_real(
    data_dir: Path, z_thresh: float, sigma_floor: float, detrend_sigma: float = 0.0
) -> int:
    def load_dir(sub: str) -> list:
        files = sorted((data_dir / sub).glob("*.npy"))
        return [np.load(f) for f in files]

    reference = load_dir("reference")
    normals = load_dir("normal")
    abnormals = load_dir("abnormal")
    if not reference or not normals or not abnormals:
        print(
            f"ERROR: expected {data_dir}/{{reference,normal,abnormal}}/*.npy "
            f"(got {len(reference)}/{len(normals)}/{len(abnormals)})"
        )
        return 2

    mask_file = data_dir / "template_mask.npy"
    knee_mask = np.load(mask_file) if mask_file.exists() else None
    print(
        f"knee mask: {'loaded (mask-aware statistic)' if knee_mask is not None else 'ABSENT (unmasked statistic)'}"
    )

    result = run_split(
        np.stack(reference),
        normals,
        abnormals,
        z_thresh,
        sigma_floor,
        3,
        knee_mask=knee_mask,
        detrend_sigma=detrend_sigma,
    )
    print("=== REAL make-or-break (registered competition studies) ===")
    print(json.dumps(result, indent=2))
    print(f"\nVERDICT: {result['verdict']}")
    return 0 if result["verdict"] == "reference_absorbs" else 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--synthetic", action="store_true", help="run the machinery smoke test"
    )
    p.add_argument("--data-dir", type=Path, help="directory of registered .npy studies")
    p.add_argument("--z-thresh", type=float, default=3.0)
    p.add_argument("--sigma-floor", type=float, default=0.05)
    p.add_argument(
        "--detrend-sigma",
        type=float,
        default=0.0,
        help="v4 encoder rung: low-frequency nuisance removal scale (0=off)",
    )
    args = p.parse_args()

    if args.synthetic:
        return run_synthetic(args.z_thresh, args.sigma_floor)
    if args.data_dir:
        return run_real(
            args.data_dir, args.z_thresh, args.sigma_floor, args.detrend_sigma
        )
    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
