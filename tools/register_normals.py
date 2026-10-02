"""Register the true-normal pool into the SAME template space as the ladder.

The template is the first sorted Effusion-negative labeled study — identical
to every register_and_export run — so all registered volumes across the
ladder remain in one comparable space. Full v3 stack per study: N4 -> knee
mask -> normalize(inside mask) -> histogram match to template -> affine +
B-spline (mask-aware).

Output: data/registered_normals/<study>.npy (+ reuses the existing
data/registered/template_mask.npy — the template study is unchanged).

Usage: python tools/register_normals.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import SimpleITK as sitk

sys.path.insert(0, str(Path(__file__).resolve().parent))

from register_and_export import (
    histogram_match,
    preprocess_canonical,
    register_full,
)


def build_template() -> tuple:
    """Rebuild the ladder's template image + mask from the SAME study."""
    manifest = json.loads(Path("data/dicom/manifest.json").read_text())
    negatives = sorted(s for s in manifest if manifest[s]["labels"]["Effusion"] == 0)
    template_study = negatives[0]
    img, mimg = preprocess_canonical(
        Path("data/dicom") / template_study / manifest[template_study]["series"]
    )
    return template_study, img, sitk.Cast(mimg > 0.5, sitk.sitkUInt8)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dicom-dir", type=Path, default=Path("data/dicom_normals"))
    p.add_argument("--out-dir", type=Path, default=Path("data/registered_normals"))
    p.add_argument("--workers", type=int, default=1)
    args = p.parse_args()

    manifest = json.loads((args.dicom_dir / "manifest.json").read_text())
    args.out_dir.mkdir(parents=True, exist_ok=True)
    todo = [s for s in sorted(manifest) if not (args.out_dir / f"{s}.npy").exists()]
    print(f"{len(manifest)} studies, {len(todo)} to register, workers={args.workers}")

    if args.workers <= 1:
        template_study, template_img, template_mask = build_template()
        print(f"template study (ladder-invariant): ...{template_study[-12:]}")
        done = failed = 0
        for study in todo:
            rc = _register_one(
                study,
                args.dicom_dir,
                args.out_dir,
                manifest[study]["series"],
                template_img,
                template_mask,
            )
            done += rc == "ok"
            failed += rc != "ok"
            if done % 10 == 0:
                print(f"  {done}/{len(todo)} registered", flush=True)
        print(f"DONE: {done} registered, {failed} failed")
        return 0 if failed == 0 else 1

    from concurrent.futures import ProcessPoolExecutor, as_completed

    done = failed = 0
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = {
            ex.submit(
                _worker_register,
                study,
                str(args.dicom_dir),
                str(args.out_dir),
                manifest[study]["series"],
            ): study
            for study in todo
        }
        for fut in as_completed(futs):
            rc = fut.result()
            done += rc == "ok"
            failed += rc != "ok"
            if (done + failed) % 10 == 0:
                print(f"  {done}/{len(todo)} registered ({failed} failed)", flush=True)
    print(f"DONE: {done} registered, {failed} failed")
    return 0 if failed == 0 else 1


def _register_one(study, dicom_dir, out_dir, series_uid, template_img, template_mask):
    series_dir = Path(dicom_dir) / study / series_uid
    img, _ = preprocess_canonical(series_dir)
    if img is None:
        print(f"WARN unloadable {study}")
        return "unloadable"
    img = histogram_match(img, template_img)
    img = register_full(img, template_img, fixed_mask=template_mask)
    np.save(Path(out_dir) / f"{study}.npy", sitk.GetArrayFromImage(img))
    return "ok"


_PROC_TEMPLATE: dict = {}


def _worker_register(study: str, dicom_dir: str, out_dir: str, series_uid: str) -> str:
    """Process-pool worker: builds the (ladder-invariant) template once per
    process, then registers one study."""
    if "img" not in _PROC_TEMPLATE:
        _, img, mask = build_template()
        _PROC_TEMPLATE["img"] = img
        _PROC_TEMPLATE["mask"] = mask
    try:
        return _register_one(
            study,
            dicom_dir,
            out_dir,
            series_uid,
            _PROC_TEMPLATE["img"],
            _PROC_TEMPLATE["mask"],
        )
    except Exception as e:  # noqa: BLE001 — operational: log, count, continue
        print(f"WARN registration failed {study}: {e}")
        return "failed"


if __name__ == "__main__":
    raise SystemExit(main())
