"""Registration front-end v2 — the FULL II.1 stack (THEORY II.1).

Mirrors the founder's brain-scan pipeline:
  assemble    DICOM series -> 3D volume (slices sorted by position along the
              slice normal; InstanceNumber fallback)
  N4          bias-field correction (t1_n4corrected analogue) — removes
              scanner intensity inhomogeneity so the subtract is clean
              across the international scanner mix
  mask        deterministic knee mask (skull-strip analogue): Otsu threshold
              -> largest 3D component -> morphological close/fill. Off-knee
              cells are zeroed BEFORE diffing and excluded from statistics
  normalize   robust per-volume intensity scaling (p2..p98 -> [0,1]),
              computed INSIDE the mask
  register    affine then B-SPLINE DEFORMABLE (Mattes MI, multi-resolution,
              mask-aware metric) to a template study — THE one sanctioned
              bounded-ML utility (Law 3); nothing else in the pipeline learns
  export      registered volumes as .npy into data/registered/ plus
              template_mask.npy (the knee mask in template space)
                reference/  Effusion=0 studies used to squash the reference
                normal/     held-out Effusion=0 studies
                abnormal/   Effusion=1 studies

v1 (affine-only, no N4, no mask) is recorded in the 2026-08-29 make-or-break:
verdict no_separation, saturated by interior boundary-misalignment patches —
the measured cost of the deferrals. Landmark anchors (patella/condyles/
plateau/notch — the founder's open question) remain the next lever if v2's
correspondence is still insufficient.

The first REAL make-or-break contrast is per-finding (Effusion) rather than
platonic-normal-vs-abnormal: the 58 explicitly-labeled studies contain ZERO
all-negative knees, so a true normal pool needs the report parser (II.7).
Effusion-negative vs Effusion-positive keeps both groups' OTHER findings
balanced and uses only clean explicit labels. Effusion is the strongest
physical signal on fluid-sensitive sequences (fluid = bright).

Usage:
  python tools/register_and_export.py [--finding Effusion] [--n-reference 15]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pydicom
import SimpleITK as sitk

CANON_SHAPE = (32, 224, 224)  # (slices, rows, cols) canonical grid


def load_series_volume(series_dir: Path) -> np.ndarray | None:
    """Assemble a sorted 3D volume from one series' DICOM slices."""
    slices = []
    for f in series_dir.glob("*.dcm"):
        try:
            ds = pydicom.dcmread(f)
            slices.append(ds)
        except Exception as e:  # noqa: BLE001 — operational: skip corrupt slice, log
            print(f"WARN unreadable slice {f.name}: {e}")
    if len(slices) < 5:
        return None

    def sort_key(ds):
        try:
            # project position onto the slice normal for true spatial order
            ori = np.array(ds.ImageOrientationPatient, dtype=float)
            normal = np.cross(ori[:3], ori[3:])
            return float(np.dot(np.array(ds.ImagePositionPatient, dtype=float), normal))
        except Exception:  # noqa: BLE001
            return float(getattr(ds, "InstanceNumber", 0))

    slices.sort(key=sort_key)
    vol = np.stack([s.pixel_array.astype(np.float32) for s in slices])
    return vol


CANON_FOV_MM = (110.0, 150.0, 150.0)  # (M-L, S-I, A-P) physical box


def derive_side(series_dir: Path) -> str:
    """Deterministic knee side: sign of the image-center patient-x (LPS: +x =
    patient LEFT), falling back to the Laterality tag. Community-verified at
    97.8% tag agreement on this dataset (2026-08-30). Returns "L"/"R"."""
    f = next(series_dir.glob("*.dcm"))
    ds = pydicom.dcmread(f, stop_before_pixels=True)
    try:
        ipp = np.array(ds.ImagePositionPatient, dtype=float)
        iop = np.array(ds.ImageOrientationPatient, dtype=float)
        sp = [float(x) for x in ds.PixelSpacing]
        center = (
            ipp
            + iop[:3] * sp[1] * int(ds.Columns) / 2
            + iop[3:] * sp[0] * int(ds.Rows) / 2
        )
        return "L" if center[0] > 0 else "R"
    except Exception:  # noqa: BLE001 — geometry missing: fall back to the tag
        tag = str(getattr(ds, "Laterality", "")).strip().upper()
        return "L" if tag.startswith("L") else "R"


def load_canonical_volume(series_dir: Path) -> np.ndarray | None:
    """mm-true, chirality-normalized volume in canonical patient space (v5).

    SimpleITK reads the series with full DICOM geometry (orientation, spacing,
    position — honest oblique handling, unlike naive slice stacking); the
    volume is resampled into an axis-aligned patient-space box of fixed
    physical size (CANON_FOV_MM) centered on the volume's physical center,
    on the CANON_SHAPE grid; LEFT knees are mirrored along patient-x so every
    study is canonical-RIGHT. All tag arithmetic — no learning.
    """
    reader = sitk.ImageSeriesReader()
    ids = reader.GetGDCMSeriesIDs(str(series_dir))
    if not ids:
        return None
    reader.SetFileNames(reader.GetGDCMSeriesFileNames(str(series_dir), ids[0]))
    try:
        img = reader.Execute()
    except RuntimeError as e:
        print(f"WARN series read failed {series_dir.name[-12:]}: {e}")
        return None

    # axis-aligned patient-space reference box centered on the image center.
    # LPS axis semantics: x = patient L-R (MEDIAL-LATERAL for a knee),
    # y = A-P, z = S-I. The M-L axis is the sagittal through-slice direction
    # (native ~3mm), so it gets the 32-sample/110mm assignment; A-P and S-I
    # are the native in-plane axes (~0.5mm) and get 224 samples / 150mm.
    # (An earlier draft swapped x and z, crushing in-plane resolution 5x —
    # caught before the atlas build; axis semantics are load-bearing there.)
    size_mm = np.array(
        [CANON_FOV_MM[0], CANON_FOV_MM[2], CANON_FOV_MM[1]]
    )  # x=M-L, y=A-P, z=S-I
    out_size = (CANON_SHAPE[0], CANON_SHAPE[2], CANON_SHAPE[1])  # (x, y, z) samples
    spacing = size_mm / np.array(out_size)
    center = np.array(
        img.TransformContinuousIndexToPhysicalPoint(
            [(s - 1) / 2 for s in img.GetSize()]
        )
    )
    ref = sitk.Image(out_size, sitk.sitkFloat32)
    ref.SetSpacing(tuple(spacing))
    ref.SetDirection((1, 0, 0, 0, 1, 0, 0, 0, 1))
    ref.SetOrigin(tuple(center - size_mm / 2 + spacing / 2))
    res = sitk.Resample(
        sitk.Cast(img, sitk.sitkFloat32), ref, sitk.Transform(), sitk.sitkLinear, 0.0
    )
    arr = sitk.GetArrayFromImage(res)  # (z=S-I, y=A-P, x=M-L)
    vol = np.ascontiguousarray(
        arr.transpose(2, 1, 0)
    )  # -> (M-L, A-P, S-I) = CANON_SHAPE

    if derive_side(series_dir) == "L":
        vol = vol[::-1, :, :].copy()  # mirror along M-L to canonical-RIGHT
    return vol


def n4_correct(vol: np.ndarray) -> np.ndarray:
    """N4 bias-field correction (t1_n4corrected analogue).

    Runs on a 2x-shrunk copy for speed; the estimated log-bias field is
    upsampled and applied at full resolution (the standard N4 recipe).
    """
    img = sitk.GetImageFromArray(vol.astype(np.float32))
    small = sitk.Shrink(img, [2, 2, 1])
    mask_small = sitk.OtsuThreshold(small, 0, 1)
    n4 = sitk.N4BiasFieldCorrectionImageFilter()
    n4.SetMaximumNumberOfIterations([40, 30, 20])
    try:
        n4.Execute(small, mask_small)
        log_bias = n4.GetLogBiasFieldAsImage(img)
        corrected = img / sitk.Exp(log_bias)
        return sitk.GetArrayFromImage(corrected)
    except RuntimeError as e:
        print(f"WARN N4 failed ({e}); using uncorrected volume")
        return vol


def knee_mask(vol: np.ndarray) -> np.ndarray:
    """Deterministic knee mask (skull-strip analogue).

    Otsu threshold -> largest connected 3D component -> per-slice binary
    closing + hole fill. Off-knee (air, off-field, other leg) is excluded
    BEFORE diffing — THEORY II.1's background mask.
    """
    img = sitk.GetImageFromArray(vol.astype(np.float32))
    binary = sitk.OtsuThreshold(img, 0, 1)
    cc = sitk.ConnectedComponent(binary)
    largest = sitk.RelabelComponent(cc, sortByObjectSize=True) == 1
    closed = sitk.BinaryMorphologicalClosing(largest, [4, 4, 1])
    filled = sitk.BinaryFillhole(closed)
    return sitk.GetArrayFromImage(filled).astype(bool)


def normalize_intensity(vol: np.ndarray, mask: np.ndarray | None = None) -> np.ndarray:
    """Robust p2..p98 scaling to [0,1], computed inside the mask when given."""
    sample = vol[mask] if mask is not None and mask.any() else vol
    lo, hi = np.percentile(sample, [2.0, 98.0])
    if hi <= lo:
        return np.zeros_like(vol)
    return np.clip((vol - lo) / (hi - lo), 0.0, 1.0)


def histogram_match(img: sitk.Image, template: sitk.Image) -> sitk.Image:
    """Deterministic intensity standardization to the template (Nyul-style).

    The international scanner/protocol mix maps the same tissue to different
    normalized intensities (contrast-ratio differences p2..p98 scaling cannot
    reconcile). Diagnosed 2026-08-29: held-out normals showed uniform-sign
    4-6 sigma offsets over FLAT tissue — an intensity disease, not a
    registration one. Histogram matching aligns the intensity distributions;
    ThresholdAtMeanIntensity excludes the zeroed background from the match.
    """
    matcher = sitk.HistogramMatchingImageFilter()
    matcher.SetNumberOfHistogramLevels(128)
    matcher.SetNumberOfMatchPoints(7)
    matcher.ThresholdAtMeanIntensityOn()
    return matcher.Execute(img, template)


def to_canonical_grid(vol: np.ndarray) -> sitk.Image:
    """Resample a volume to the canonical grid via linear interpolation.

    The canonical grid IS the shared physical space: every output volume gets
    identical unit spacing, zero origin, and identity direction, so downstream
    registration operates in one consistent coordinate frame. (v1 keeps
    per-study voxel-scale differences as part of what the affine absorbs; an
    earlier variant that carried per-study spacing into the output put every
    volume in a DIFFERENT physical space and broke registration outright.)
    """
    img = sitk.GetImageFromArray(vol)
    img.SetSpacing(
        (
            CANON_SHAPE[2] / float(vol.shape[2]),
            CANON_SHAPE[1] / float(vol.shape[1]),
            CANON_SHAPE[0] / float(vol.shape[0]),
        )
    )
    ref = sitk.Image(CANON_SHAPE[::-1], sitk.sitkFloat32)  # sitk size = (x, y, z)
    ref.SetSpacing((1.0, 1.0, 1.0))
    out = sitk.Resample(img, ref, sitk.Transform(), sitk.sitkLinear, 0.0)
    out.SetSpacing((1.0, 1.0, 1.0))
    out.SetOrigin((0.0, 0.0, 0.0))
    return out


def preprocess_canonical(series_dir: Path) -> tuple:
    """v5 front half: mm-true chirality-normalized load -> N4 -> mask ->
    normalize -> background zeroed. Returns (image, mask_image) as unit-spacing
    sitk images on the canonical grid, or (None, None)."""
    vol = load_canonical_volume(series_dir)
    if vol is None:
        return None, None
    vol = n4_correct(vol)
    mask = knee_mask(vol)
    vol = normalize_intensity(vol, mask)
    vol[~mask] = 0.0
    img = sitk.GetImageFromArray(vol.astype(np.float32))
    img.SetSpacing((1.0, 1.0, 1.0))
    mimg = sitk.GetImageFromArray(mask.astype(np.float32))
    mimg.SetSpacing((1.0, 1.0, 1.0))
    return img, mimg


def register_full(
    moving: sitk.Image, fixed: sitk.Image, fixed_mask: sitk.Image | None = None
) -> sitk.Image:
    """Affine then B-spline deformable registration (Mattes MI, multi-res,
    mask-aware metric) — the bounded utility, full II.1 fidelity.

    Returns the moving image resampled into the fixed (template) space.
    Falls back progressively: deformable failure -> affine result; affine
    failure -> canonical-grid-only input.
    """
    # --- stage 1: affine ---
    reg = sitk.ImageRegistrationMethod()
    reg.SetMetricAsMattesMutualInformation(numberOfHistogramBins=32)
    reg.SetMetricSamplingStrategy(reg.RANDOM)
    reg.SetMetricSamplingPercentage(0.2, seed=1729)
    if fixed_mask is not None:
        reg.SetMetricFixedMask(fixed_mask)
    reg.SetInterpolator(sitk.sitkLinear)
    reg.SetOptimizerAsRegularStepGradientDescent(
        learningRate=1.0, minStep=1e-4, numberOfIterations=150
    )
    reg.SetOptimizerScalesFromPhysicalShift()
    initial = sitk.CenteredTransformInitializer(
        fixed,
        moving,
        sitk.AffineTransform(3),
        sitk.CenteredTransformInitializerFilter.GEOMETRY,
    )
    reg.SetInitialTransform(initial, inPlace=False)
    reg.SetShrinkFactorsPerLevel([4, 2, 1])
    reg.SetSmoothingSigmasPerLevel([2.0, 1.0, 0.0])
    try:
        affine_tx = reg.Execute(fixed, moving)
    except RuntimeError as e:
        print(f"WARN affine registration failed ({e}); canonical-grid only")
        return moving
    affine_out = sitk.Resample(moving, fixed, affine_tx, sitk.sitkLinear, 0.0)

    # --- stage 2: B-spline deformable, initialized from the affine result ---
    breg = sitk.ImageRegistrationMethod()
    breg.SetMetricAsMattesMutualInformation(numberOfHistogramBins=32)
    breg.SetMetricSamplingStrategy(breg.RANDOM)
    breg.SetMetricSamplingPercentage(0.15, seed=1729)
    if fixed_mask is not None:
        breg.SetMetricFixedMask(fixed_mask)
    breg.SetInterpolator(sitk.sitkLinear)
    # coarse control-point mesh: enough to bend condyle-scale anatomy into
    # correspondence without hallucinating lesion-scale warps (which would
    # erase the very pathology signal the residual must keep)
    bspline_init = sitk.BSplineTransformInitializer(fixed, [10, 10, 4])
    breg.SetInitialTransform(bspline_init, inPlace=True)
    breg.SetOptimizerAsLBFGSB(gradientConvergenceTolerance=1e-5, numberOfIterations=60)
    breg.SetShrinkFactorsPerLevel([2, 1])
    breg.SetSmoothingSigmasPerLevel([1.0, 0.0])
    try:
        bspline_tx = breg.Execute(fixed, affine_out)
    except RuntimeError as e:
        print(f"WARN deformable stage failed ({e}); keeping affine result")
        return affine_out
    return sitk.Resample(affine_out, fixed, bspline_tx, sitk.sitkLinear, 0.0)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--finding", default="Effusion")
    p.add_argument("--n-reference", type=int, default=15)
    p.add_argument("--dicom-dir", type=Path, default=Path("data/dicom"))
    p.add_argument("--out-dir", type=Path, default=Path("data/registered"))
    args = p.parse_args()

    manifest = json.loads((args.dicom_dir / "manifest.json").read_text())

    # split by finding label; deterministic order (sorted UIDs) for reproducibility
    negatives, positives = [], []
    for study in sorted(manifest):
        label = manifest[study]["labels"].get(args.finding)
        if label == 0:
            negatives.append(study)
        elif label == 1:
            positives.append(study)
    print(f"{args.finding}: {len(negatives)} negative, {len(positives)} positive")

    template_img = None
    template_mask_img = None
    exported = {"reference": 0, "normal": 0, "abnormal": 0, "failed": 0}

    def process(study: str) -> sitk.Image | None:
        nonlocal template_img, template_mask_img
        series = manifest[study]["series"]
        series_dir = args.dicom_dir / study / series
        have = len(list(series_dir.glob("*.dcm")))
        want = manifest[study]["n_slices"]
        if have != want:
            # a partial series must never masquerade as a volume
            print(f"WARN incomplete series for {study}: {have}/{want} slices — skipped")
            return None
        img, mimg = preprocess_canonical(series_dir)
        if img is None:
            print(f"WARN unloadable {study}")
            return None
        if template_img is None:
            template_img = img  # first reference study IS the template
            template_mask_img = mimg
            tmask = sitk.GetArrayFromImage(template_mask_img) > 0.5
            args.out_dir.mkdir(parents=True, exist_ok=True)
            np.save(args.out_dir / "template_mask.npy", tmask)
            return img
        img = histogram_match(img, template_img)
        fixed_mask = (
            sitk.Cast(template_mask_img > 0.5, sitk.sitkUInt8)
            if template_mask_img is not None
            else None
        )
        return register_full(img, template_img, fixed_mask=fixed_mask)

    for group, studies in (
        ("reference", negatives[: args.n_reference]),
        ("normal", negatives[args.n_reference :]),
        ("abnormal", positives),
    ):
        out = args.out_dir / group
        out.mkdir(parents=True, exist_ok=True)
        for study in studies:
            img = process(study)
            if img is None:
                exported["failed"] += 1
                continue
            np.save(out / f"{study}.npy", sitk.GetArrayFromImage(img))
            exported[group] += 1
            print(f"  {group}: {study[-12:]} exported")

    print(f"EXPORTED: {exported}")
    with open(args.out_dir / "export_meta.json", "w") as f:
        json.dump(
            {
                "finding": args.finding,
                "n_reference": args.n_reference,
                "canonical_shape": CANON_SHAPE,
                "counts": exported,
                "registration": "v3 full II.1: N4 + knee mask + histogram match + affine + B-spline (Mattes MI, mask-aware)",
            },
            f,
            indent=1,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
