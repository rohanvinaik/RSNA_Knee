"""Build the template atlas: mean template, bone masks, landmarks, zones.

Fleet Ranks 1+3 (docs/LANDMARK_PRIOR_ART.md; ADR 2026-08-30): mean-intensity
template from the registered true normals -> dark-marrow bone extraction ->
geometric landmarks (distance-transform joint line, condyle extremal points,
notch saddle) -> zone label volume painted from the geometry.

Outputs under data/atlas/:
  template_mean.npy   mean intensity template
  zones.npy           uint8 zone label volume (anatomy.ZONE_NAMES)
  landmarks.json      landmark voxel coordinates + joint line
  qc_*.png            THE one human-in-the-loop artifact: eye-check renders

Usage: python tools/build_atlas.py [--normals-dir data/registered_normals]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from RSNA_Knee.anatomy import ZONE_NAMES, bone_masks, build_zone_labels


def render_qc(template, bones, labels, lm, out_dir: Path) -> list:
    """Save eye-QC PNGs at bone-bearing slices: lateral condyle, patella,
    notch, medial condyle. Bones as channel overlays; zones alpha-blended
    on the anatomy with a fixed color LUT."""
    from PIL import Image

    lut = np.array(
        [
            (0, 0, 0),  # 0 background
            (255, 255, 0),  # 1 joint_line_slab (unused; compartments cover it)
            (0, 255, 255),  # 2 retropatellar — cyan
            (255, 0, 255),  # 3 notch — magenta
            (0, 128, 255),  # 4 suprapatellar — azure
            (255, 128, 0),  # 5 popliteal — orange
            (255, 0, 0),  # 6 medial compartment — red
            (0, 255, 0),  # 7 lateral compartment — green
            (128, 128, 255),  # 8 femur bone — pale blue
            (128, 255, 128),  # 9 tibia bone — pale green
            (255, 128, 128),  # 10 patella bone — pale red
            (90, 90, 90),  # 11 other knee tissue — dim gray
        ],
        dtype=np.float32,
    )

    def base_rgb(sl):
        g = (np.clip(sl, 0, 1) * 255).astype(np.float32)
        return np.stack([g] * 3, axis=-1)

    def save(arr, path):
        img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
        img.resize((448, 448), Image.NEAREST).save(path)

    files = []
    slices = (
        ("latcondyle", lm["lateral_condyle"][0]),
        ("patella", int(np.argwhere(bones["patella"])[:, 0].mean())),
        ("notch", lm["notch"][0]),
        ("medcondyle", lm["medial_condyle"][0]),
    )
    for name, ml_idx in slices:
        sl = template[ml_idx].T[::-1]  # (S-I up, A-P right) for viewing
        rgb = base_rgb(sl)
        f = out_dir / f"qc_template_{name}.png"
        save(rgb, f)
        files.append(f)

        rgb = base_rgb(sl)
        for ch, mask in (
            (0, bones["femur"][ml_idx].T[::-1]),
            (1, bones["tibia"][ml_idx].T[::-1]),
            (2, bones["patella"][ml_idx].T[::-1]),
        ):
            rgb[..., ch] = np.where(mask, 255, rgb[..., ch])
        f = out_dir / f"qc_bones_{name}.png"
        save(rgb, f)
        files.append(f)

        zsl = labels[ml_idx].T[::-1].astype(int)
        rgb = base_rgb(sl)
        zc = lut[zsl]
        blend = np.where((zsl > 0)[..., None], 0.55 * rgb + 0.45 * zc, rgb)
        f = out_dir / f"qc_zones_{name}.png"
        save(blend, f)
        files.append(f)
    return files


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--normals-dir", type=Path, default=Path("data/registered_normals"))
    p.add_argument("--out-dir", type=Path, default=Path("data/atlas"))
    p.add_argument("--dark-pct", type=float, default=30.0)
    args = p.parse_args()

    vols = [np.load(f) for f in sorted(args.normals_dir.glob("*.npy"))]
    print(f"mean template from {len(vols)} registered true normals")
    template = np.mean(np.stack(vols), axis=0).astype(np.float32)
    kmask = np.load("data/registered/template_mask.npy")

    # Bone geometry comes from the TEMPLATE STUDY volume, not the mean:
    # the study defines template space (identity by construction) and its
    # marrow is crisp, while the single-study-template mean blurs marrow
    # to mid-gray (measured 2026-08-31 — registration spread; the Rank-5
    # bias showing up early). The mean is still saved for NCC patches and
    # the scheduled unbiased-template iteration.
    manifest = json.loads(Path("data/dicom/manifest.json").read_text())
    tstudy = sorted(s for s in manifest if manifest[s]["labels"]["Effusion"] == 0)[0]
    bone_src = np.load(f"data/registered/reference/{tstudy}.npy")
    print(f"bone substrate: template study ...{tstudy[-12:]}")

    bones = bone_masks(bone_src, kmask, dark_pct=args.dark_pct)
    labels, lm = build_zone_labels(bone_src, kmask, bones)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    np.save(args.out_dir / "template_mean.npy", template)
    np.save(args.out_dir / "zones.npy", labels)
    (args.out_dir / "landmarks.json").write_text(
        json.dumps(
            {k: list(v) if isinstance(v, tuple) else v for k, v in lm.items()}, indent=1
        )
    )
    counts = {ZONE_NAMES[z]: int((labels == z).sum()) for z in np.unique(labels)}
    print("landmarks:", lm)
    print("zone voxel counts:", json.dumps(counts, indent=1))

    files = render_qc(bone_src, bones, labels, lm, args.out_dir)
    print("QC renders:", [str(f) for f in files])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
