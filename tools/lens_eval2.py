"""II.5 v2 — OUT-OF-SAMPLE per-finding lens read.

Design (label-source split, no LOO needed):
  prototypes  <- parser-labeled positive pool (data/registered_positives,
                 labels from its manifest, source report_parser_v3) and, as
                 the negative prototype, the 50 reference true normals
  evaluation  <- gold only: the 43 explicitly-labeled studies + the 30
                 held-out true normals (all-negative)

Honest caveats, stated: prototype positives carry ~78%-accurate parser
labels (bundling is majority-tolerant); the negative prototype's members
also built the residual reference, so their own residuals are biased low —
they serve as the "clean consensus" pole, which is the E16 reading.

Usage:
  python tools/lens_eval2.py [--detrend-sigma 24]
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
    p.add_argument("--z-thresh", type=float, default=3.0)
    p.add_argument("--sigma-floor", type=float, default=0.05)
    p.add_argument("--detrend-sigma", type=float, default=24.0)
    p.add_argument(
        "--positives-dir", type=Path, default=Path("data/registered_positives")
    )
    args = p.parse_args()

    gold_manifest = json.loads(Path("data/dicom/manifest.json").read_text())
    pos_manifest = json.loads(Path("data/dicom_positives/manifest.json").read_text())

    ref_files = sorted(Path("data/registered_true/reference").glob("*.npy"))
    ref = build_reference(np.stack([np.load(f) for f in ref_files]))
    kmask = np.load("data/registered/template_mask.npy")
    print(f"reference squash: {len(ref_files)} true normals")

    enc = None

    def encode(path: Path):
        nonlocal enc
        vol = np.load(path)
        z = detrended_residual_map(
            vol, ref, args.sigma_floor, kmask, args.detrend_sigma
        )
        t = np.where(
            z >= args.z_thresh, 1, np.where(z <= -args.z_thresh, -1, 0)
        ).astype(np.int8)
        t[~kmask] = 0
        if enc is None:
            enc = ResidualHDCEncoder(vol.shape)
        return enc.encode_study(t)

    # --- prototype side (parser-labeled positives + reference normals) ---
    proto_encs, proto_labels = [], []
    for f in sorted(args.positives_dir.glob("*.npy")):
        proto_encs.append(encode(f))
        proto_labels.append(pos_manifest[f.stem]["labels"])
    neg_proto_encs = [encode(f) for f in ref_files]
    print(
        f"prototype pool: {len(proto_encs)} parser-positives + {len(neg_proto_encs)} reference normals"
    )

    # --- evaluation side (gold only) ---
    eval_encs, eval_names = [], []
    for group in ("normal", "abnormal"):
        for f in sorted(Path(f"data/registered/{group}").glob("*.npy")):
            eval_encs.append(encode(f))
            eval_names.append(("gold", f.stem))
    for f in sorted(Path("data/registered_true/normal").glob("*.npy")):
        eval_encs.append(encode(f))
        eval_names.append(("true_normal", f.stem))
    print(f"eval set: {len(eval_encs)} studies (gold 43 + true normals 30)")

    labels = {}
    for fnd in FINDINGS:
        labels[fnd] = [
            int(gold_manifest[name]["labels"][fnd] or 0) if src == "gold" else 0
            for src, name in eval_names
        ]

    rng = np.random.default_rng(1729)
    for level in ("study", "zone"):
        scores, usable = {}, {}
        for fnd in FINDINGS:
            if auc_status(labels[fnd]) != "ok":
                continue
            pos_i = [i for i, pl in enumerate(proto_labels) if pl[fnd] == 1]
            m = min(len(pos_i), len(neg_proto_encs))
            pos_sel = (
                list(rng.choice(pos_i, size=m, replace=False))
                if len(pos_i) > m
                else pos_i
            )
            neg_sel = list(range(len(neg_proto_encs)))[:m]
            if level == "study":
                pp = bundle_prototype([proto_encs[i]["study_hv"] for i in pos_sel])
                pn = bundle_prototype([neg_proto_encs[i]["study_hv"] for i in neg_sel])
                scores[fnd] = [
                    similarity(e["study_hv"], pp) - similarity(e["study_hv"], pn)
                    for e in eval_encs
                ]
            else:
                n_zones = proto_encs[0]["zone_hvs"].shape[0]
                pz = [
                    bundle_prototype([proto_encs[i]["zone_hvs"][z] for i in pos_sel])
                    for z in range(n_zones)
                ]
                nz = [
                    bundle_prototype(
                        [neg_proto_encs[i]["zone_hvs"][z] for i in neg_sel]
                    )
                    for z in range(n_zones)
                ]
                scores[fnd] = [
                    max(
                        similarity(e["zone_hvs"][z], pz[z])
                        - similarity(e["zone_hvs"][z], nz[z])
                        for z in range(n_zones)
                    )
                    for e in eval_encs
                ]
            usable[fnd] = labels[fnd]
        result = macro_auc(usable, scores)
        print(f"\n=== {level}-level out-of-sample lens read ===")
        for fnd in sorted(
            result["per_finding"], key=lambda k: -result["per_finding"][k]
        ):
            n_pos = sum(usable[fnd])
            n_proto = sum(1 for pl in proto_labels if pl[fnd] == 1)
            print(
                f"  {fnd:18s} AUC {result['per_finding'][fnd]:.3f}  "
                f"(eval {n_pos}p/{len(usable[fnd]) - n_pos}n | proto {n_proto}p)"
            )
        print(f"  MACRO {result['score']:.3f} over {result['n_scored']} findings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
