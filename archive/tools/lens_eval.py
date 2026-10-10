"""II.5 v1 — per-finding lens read of the HDC-encoded residual, all 12 findings.

Lens v1 = prototype similarity in HV space, leave-one-out:
  prototype_pos(f, s) = majority-bundle of study/zone HVs of f-positive
                        studies excluding s (consensus, not training)
  score(s, f)         = sim(s, proto_pos) - sim(s, proto_neg)   [margin]

Two reads per finding:
  study — margin on the study-scale HV (whole-knee gestalt)
  zone  — max over zones of the per-zone margin (location-specific read;
          the v1 stand-in for "apply the lens to a region")

Evaluated on the 43 non-reference labeled studies (reference members are
excluded — their residual against a reference containing themselves is
biased). AUC per finding via the pinned scorer; degenerate labels skip via
auc_status. No learning: bundling + dot products only.

Usage:
  python tools/lens_eval.py [--detrend-sigma 24] [--z-thresh 3.0]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from RSNA_Knee.hdc_encoder import (
    ResidualHDCEncoder,
    bundle_prototype,
    similarity,
)
from RSNA_Knee.platonic_reference import (
    build_reference,
    detrended_residual_map,
)
from RSNA_Knee.scoring import auc_status, macro_auc

FINDINGS = [
    "ACL",
    "MCL",
    "Medial Meniscus",
    "Lateral Meniscus",
    "Medial OA",
    "Lateral OA",
    "PF OA",
    "Effusion",
    "Synovitis",
    "Baker's",
    "Contusion",
    "Fracture",
]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", type=Path, default=Path("data/registered"))
    p.add_argument("--z-thresh", type=float, default=3.0)
    p.add_argument("--sigma-floor", type=float, default=0.05)
    p.add_argument("--detrend-sigma", type=float, default=24.0)
    p.add_argument(
        "--reference-dir",
        type=Path,
        default=None,
        help="override reference squash dir (e.g. true normals)",
    )
    p.add_argument(
        "--extra-negatives",
        type=Path,
        default=None,
        help="dir of registered true-normal .npy volumes: added as "
        "all-finding-negative studies (parser-certified)",
    )
    args = p.parse_args()

    manifest = json.loads(Path("data/dicom/manifest.json").read_text())
    ref_dir = args.reference_dir if args.reference_dir else args.data_dir / "reference"
    ref = build_reference(np.stack([np.load(f) for f in sorted(ref_dir.glob("*.npy"))]))
    print(f"reference squash: {ref_dir} ({ref.n} studies)")
    kmask = np.load(args.data_dir / "template_mask.npy")

    studies, encs = [], []
    enc = None
    for group in ("normal", "abnormal"):
        for f in sorted((args.data_dir / group).glob("*.npy")):
            vol = np.load(f)
            z = detrended_residual_map(
                vol, ref, args.sigma_floor, kmask, args.detrend_sigma
            )
            ternary = np.where(
                z >= args.z_thresh, 1, np.where(z <= -args.z_thresh, -1, 0)
            ).astype(np.int8)
            ternary[~kmask] = 0
            if enc is None:
                enc = ResidualHDCEncoder(vol.shape)
            encs.append(enc.encode_study(ternary))
            studies.append(f.stem)
    print(
        f"encoded {len(studies)} studies "
        f"(z_thresh={args.z_thresh}, detrend={args.detrend_sigma})"
    )

    labels = {
        f: [int(manifest[s]["labels"][f] or 0) for s in studies] for f in FINDINGS
    }
    if args.extra_negatives:
        extra = sorted(args.extra_negatives.glob("*.npy"))
        for fpath in extra:
            vol = np.load(fpath)
            z = detrended_residual_map(
                vol, ref, args.sigma_floor, kmask, args.detrend_sigma
            )
            ternary = np.where(
                z >= args.z_thresh, 1, np.where(z <= -args.z_thresh, -1, 0)
            ).astype(np.int8)
            ternary[~kmask] = 0
            encs.append(enc.encode_study(ternary))
            studies.append(fpath.stem)
            for f in FINDINGS:
                labels[f].append(0)
        print(f"added {len(extra)} parser-certified normals as negatives")

    def loo_scores(finding: str, level: str) -> list:
        y = labels[finding]
        out = []
        rng = np.random.default_rng(1729)
        for i, e in enumerate(encs):
            pos_i = [j for j in range(len(encs)) if j != i and y[j] == 1]
            neg_i = [j for j in range(len(encs)) if j != i and y[j] == 0]
            # balanced prototypes: equal bundle sizes per side (seeded
            # subsample of the majority) — unequal bundles bias similarity
            # toward the smoother prototype (measures typicality, not the
            # finding)
            m = min(len(pos_i), len(neg_i))
            if m == 0:
                out.append(0.0)
                continue
            pos_i = (
                list(rng.choice(pos_i, size=m, replace=False))
                if len(pos_i) > m
                else pos_i
            )
            neg_i = (
                list(rng.choice(neg_i, size=m, replace=False))
                if len(neg_i) > m
                else neg_i
            )
            if level == "study":
                proto_p = bundle_prototype([encs[j]["study_hv"] for j in pos_i])
                proto_n = bundle_prototype([encs[j]["study_hv"] for j in neg_i])
                out.append(
                    similarity(e["study_hv"], proto_p)
                    - similarity(e["study_hv"], proto_n)
                )
            else:
                n_zones = e["zone_hvs"].shape[0]
                margins = []
                for zn in range(n_zones):
                    pp = bundle_prototype([encs[j]["zone_hvs"][zn] for j in pos_i])
                    pn = bundle_prototype([encs[j]["zone_hvs"][zn] for j in neg_i])
                    margins.append(
                        similarity(e["zone_hvs"][zn], pp)
                        - similarity(e["zone_hvs"][zn], pn)
                    )
                out.append(max(margins))
        return out

    for level in ("study", "zone"):
        scores = {}
        usable = {}
        for f in FINDINGS:
            if auc_status(labels[f]) != "ok":
                continue
            usable[f] = labels[f]
            scores[f] = loo_scores(f, level)
        result = macro_auc(usable, scores)
        print(f"\n=== {level}-level lens read ===")
        for f in sorted(result["per_finding"], key=lambda k: -result["per_finding"][k]):
            n_pos = sum(usable[f])
            print(
                f"  {f:18s} AUC {result['per_finding'][f]:.3f}  ({n_pos} pos / {len(usable[f]) - n_pos} neg)"
            )
        print(
            f"  MACRO {result['score']:.3f} over {result['n_scored']} findings"
            + (f" (skipped: {result['skipped']})" if result["skipped"] else "")
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
