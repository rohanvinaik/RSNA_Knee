# Landmark & Anatomical-Zone Prior Art — verified research fleet synthesis

**Provenance:** 46-agent research workflow (knee-landmark-prior-art, run
wf_ec83a461-6dd, 2026-08-30), founder-directed. Five parallel literature/
tooling sweeps (classical landmarks, atlas/multi-atlas, SSM/priors,
offline tooling, Kaggle prior art) with per-method ADVERSARIAL verification:
constraint gate = classical-or-bounded-normalization-only, offline-runnable
in a Kaggle kernel, knee-specific evidence with verified citations. API
calls were executed in scratch venvs, not trusted from docs. The synthesis
below inspected this repo's actual state before ranking.

**Constraint frame (the founder's wiggle-room grant):** rigorous classical
adherence everywhere; priors and/or statistics permitted ONLY for the
landmark-anchoring of anatomical zones and spatial/anatomical normalization
of the scans.

---

(see raw task output)
Ranked implementation plan follows. Grounding facts (from the verified verdicts + repo state at `/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee`): analysis already lives on the canonical 32×224×224 template grid (`data/registered/`, `data/registered_v2/` — warped `.npy` volumes, `template_mask.npy`); `tools/register_and_export.py` registers with fixed=template / moving=study, so the in-memory transform maps template→study points FORWARD (no inversion needed for landmark push-out), but transforms are currently discarded (no `WriteTransform`). This makes template-space methods nearly free and de-prioritizes anything needing per-study native-space transforms.

---

## 1) Ranked methods (value/effort for THIS pipeline)

**Rank 1 — Template-space zone + landmark annotation, consumed directly in template space** (sweep: classical-landmarks #1 / atlas-multiatlas #1 / kaggle-prior-art #1). Effort: hours–1 day. Value: highest — because all volumes already sit on the template grid, zone masks are *constant index masks* requiring zero transform bookkeeping and zero per-study error beyond the existing registration residual (2–4 mm at bone surfaces; Shan et al. Med Image Anal 2014, PMID 25128683; Grammens et al. J Imaging 2024, PMC11051533: 2.05±1.30 mm, 92% within 4 mm for template-based knee landmark transfer). Every verifier flagged the same correction: do NOT follow the recipes' inversion steps — for template→study points use `tx.TransformPoint` directly (ITK fixed→moving convention), and for template-space consumption no transform at all.

**Rank 2 — NCC patch matching for per-study landmark refinement + registration-QC gate** (classical-landmarks #2 / tooling-offline match_template / kaggle-prior-art #3). Effort: ~1 day. Value: converts registration-limited accuracy into locally-optimal accuracy AND yields the per-study confidence scalar that flags the failed-registration tail of a 4400-study run. `skimage.feature.match_template` is verified 3-D NCC (executed: planted-patch recovery at exact voxel, peak=1.0, invariant to linear intensity transforms). Precision: plan for 2–4 mm on hard landmarks, ~1.5–2.5 mm typical (analogue: Xue et al. JMRI 2015, PMID 24431181, 1.64±1.03 mm — note that figure came from a partly learned pipeline; ours is pure NCC, so calibrate on held-out annotations). The NCC<~0.5 fallback-to-propagated-position gate bounds worst case at current registration accuracy.

**Rank 3 — Deterministic geometric landmark/zone extraction from template bone geometry** (moments, extremal points, distance transforms; kaggle-prior-art #4 / atlas-multiatlas #5). Effort: 1–2 days, all template-side (per-study cost zero). Value: makes the Rank-1 annotation *principled and reproducible* rather than hand-clicked — joint line = ridge of femur/tibia distance-transform gap, condyles = extremal points of the distal femur height field, notch = saddle between condyle minima, plateau = orientation-filtered marching-cubes normals (extremal-point definitions per Grammens PMC11051533; condyle-tangent geometry per US8428688). The joint-gap distance-transform machinery *also directly emits compartment gap-width features* — double duty for the OA findings.

**Rank 4 — Multi-atlas zone-label fusion with vote-fraction confidence maps** (classical-landmarks #6 / ssm-priors #5). Effort: 2–4 days, dominated by hand-correcting K≈10–15 propagated zone labelings. Value: replaces hard single-template zone cuts with soft consensus boundaries (`P(zone|voxel)` as weights, not cuts) and averages out per-study registration error (multi-atlas beats single-atlas on knee MRI: Lee et al. Med Phys 2014, PMC4149695; Shan PMID 25128683). All calls verified in stock SimpleITK 2.5.6 (`LabelVoting`, `MultiLabelSTAPLEImageFilter`); vote fraction = trivial numpy mean over binarized warped labels. Do this AFTER Ranks 1–3 prove the zones matter.

**Rank 5 — Unbiased iterative template refinement + probabilistic zone atlas** (atlas-multiatlas #7, the OAI pattern; Joshi NeuroImage 2004, PMID 15501084; OAI femoral-cartilage atlas PMC3142327). Effort: 2–3 days, compute-dominated. Value: current template is a single Effusion-negative study (verifier-confirmed from `tools/register_normals.py`) — a biased reference. 3–4 iterations of register-all → mean-intensity → debias-by-inverse-mean-deformation sharpens the template, improving TRE ~10–30% and lifting *every* method above it. Schedule as a background compute job once Ranks 1–3 are producing features.

**Deferred:** SSM/ASM (1–2 weeks, only if surface precision becomes the measured bottleneck — the sweep's own recommendation), GHT (QC-only, redundant with the NCC QC score at higher effort), CPD (only needed for SSM correspondence, and registration-propagated correspondence is cheaper anyway).

---

## 2) Concrete recipes for the top 2

### Recipe A — Template zones + landmarks (Rank 1, with Rank 3's geometry defining them)

**Step 1. Build the mean intensity template** (sharper annotation substrate than the single-subject reference; also Rank-2's patch source):
```python
import numpy as np, glob
vols = [np.load(p) for p in glob.glob("data/registered_v2/normal/*.npy")]
template_mean = np.mean(np.stack(vols), axis=0).astype(np.float32)   # (32, 224, 224)
np.save("data/atlas/template_mean.npy", template_mean)
```

**Step 2. Template bone masks** (one-time, visually QC'd — Otsu is acceptable ONLY here because it's checked by eye once; marrow polarity varies by sequence):
```python
from skimage.filters import threshold_otsu
import scipy.ndimage as ndi
mask = template_mean > threshold_otsu(template_mean)
mask = ndi.binary_fill_holes(ndi.binary_opening(mask, iterations=2))
lbl, n = ndi.label(mask)
sizes = ndi.sum(mask, lbl, range(1, n+1))
# keep 3 largest; assign femur/tibia/patella by centroid: patella = most anterior (min x on sagittal), femur = most superior
```
Hand-fix in any viewer if Otsu misbehaves — this is the single human-in-the-loop artifact.

**Step 3. Geometric landmark + zone definitions** (all numpy/scipy, verified-by-execution APIs):
```python
# Joint line: ridge of the inter-bone gap
df = ndi.distance_transform_edt(~femur_mask)
dt = ndi.distance_transform_edt(~tibia_mask)
gap = df + dt                      # joint line = argmin ridge of gap in the inter-bone region
joint_line_z = np.median(...)      # median of per-column midpoints between inferior femur / superior tibia

# Condyles: distal femur height field h(x,z) = min-y of femur mask per column
# -> two local minima (scipy.signal.argrelextrema) = medial/lateral condyle distal points
# -> notch apex = max of h between them (the saddle)

# Principal axes for medial/lateral split and zone boxes:
coords = np.argwhere(femur_mask); com = coords.mean(0)
evals, evecs = np.linalg.eigh(np.cov((coords - com).T))   # fix signs by anatomical convention

# Zones (paint as integer label volume, 32x224x224 uint8):
# 1 joint line slab; 2 retropatellar shell (dilated posterior patella surface ∩ femoral trochlea gap);
# 3 intercondylar notch (inter-lobe gap region); 4 suprapatellar recess (superior to patella
# centroid, anterior to femoral shaft axis); 5 popliteal fossa (posterior to condyle centroid at
# joint-line level); 6/7 medial/lateral compartments (joint slab split by mid-sagittal plane)
np.save("data/atlas/zones.npy", zone_labels)
np.save("data/atlas/landmarks_template.npy", landmark_array)  # (L, 3) voxel coords + names JSON
```

**Step 4. Per-study consumption — no transforms:**
```python
vol = np.load(study_path)                     # already on template grid
for zid in range(1, 8):
    zvals = vol[zone_labels == zid]           # zone intensity/residual stats -> features
```

**Step 5 (only if native-space landmarks ever needed).** One-line fix in `tools/register_and_export.py`: after the registration `Execute`, `sitk.WriteTransform(final_tx, out_dir / f"{study_id}.tfm")`. Then `p_study = tx.TransformPoint(p_template)` — forward, NO inversion (fixed=template convention; verifiers confirmed following the sweep recipes' inversion literally gives grossly wrong points).

### Recipe B — NCC landmark refinement + registration QC (Rank 2)

**Step 1. Patch bank** (from `template_mean`, anisotropic: z is slices):
```python
d_z, d_y, d_x = 3, 8, 8      # ~patch 7x17x17
patches = {name: template_mean[z-d_z:z+d_z+1, y-d_y:y+d_y+1, x-d_x:x+d_x+1]
           for name, (z, y, x) in landmarks.items()}
np.savez("data/atlas/ncc_patches.npz", **patches)
```

**Step 2. Per-study refinement:**
```python
from skimage.feature import match_template
w_z, w_y, w_x = 4, 10, 10    # search window ±; must exceed patch dims — holds here
box = vol[z-w_z:z+w_z+1, y-w_y:y+w_y+1, x-w_x:x+w_x+1]
resp = match_template(box, patch, pad_input=True)   # true 3-D NCC via FFT (verified)
pk = np.unravel_index(np.argmax(resp), resp.shape)
conf = resp.max()
refined = pk_in_volume_coords if conf > THRESH else propagated_position  # fail-safe gate
```

**Step 3. Sub-voxel:** quadratic fit on the 3×3×3 neighborhood of the peak (~10 lines numpy); apply in y/x only (z too coarse at 32 slices).

**Step 4. Calibrate + QC:** hand-annotate landmarks on ~10 held-out studies; set `THRESH` per-landmark from the confidence distribution (start 0.5). Registration-QC: `study_score = np.median([conf per landmark])`; flag studies below the cohort 5th percentile → re-register with `sitk.CenteredTransformInitializer(fixed, moving, sitk.Euler3Transform(), sitk.CenteredTransformInitializerFilter.MOMENTS)` init, or exclude their zone features (near-miss censor for spatial normalization).

---

## 3) What each buys the weak findings

- **Menisci:** Rank 1/3's joint-line slab + medial/lateral compartment split gives *meniscal corner sub-zones* (posterior/anterior horn boxes at the compartment periphery of the joint slab). Residual-energy stats become zone-conditioned — meniscal signal is no longer diluted across the whole joint. Rank 2's QC keeps mis-registered studies from polluting these thin zones (menisci are the most localization-sensitive finding).
- **MCL:** a medial-peripheral band zone (medial edge of the medial compartment, spanning the joint line along the medial cortex) isolates exactly where MCL signal lives — currently invisible in whole-volume statistics. Pure Rank-1 addition; no landmark precision needed beyond zone-level.
- **PF OA:** retropatellar shell (zone 2) + suprapatellar recess (zone 4) + patella landmarks. Buys: retropatellar cartilage-interface residuals, patella-position features (alta/baja from patella centroid vs joint-line distance — closed-form from Rank 3), and recess effusion volume as a correlated signal.
- **Compartment OA:** medial vs lateral compartment masks + the distance-transform joint-gap machinery emits *per-compartment gap-width statistics* (min/median gap per compartment = the classical joint-space-narrowing measurement, JLCA lineage PMC12107965) plus osteophyte-region residuals at compartment margins. Rank 4's soft boundaries matter most here — OA anatomy is precisely where hard zone cuts mis-assign voxels; and Rank 5's per-study Jacobian determinants (`sitk.DisplacementFieldJacobianDeterminant`) are direct shape-deformation features for OA.

## 4) Artifacts from competition data (all Kaggle-dataset-shippable, no license issues)

| Artifact | Built how | Feeds |
|---|---|---|
| `template_mean.npy` | mean of registered normal volumes (Recipe A step 1) | annotation substrate, NCC patch source |
| template bone masks (femur/tibia/patella) | Otsu+morphology, one-time visual QC (A step 2) | all Rank-3 geometry |
| `landmarks_template.npy` + names JSON | geometric extraction + manual verification (A step 3) | NCC refinement, features |
| `zones.npy` (uint8 label volume) | geometric rules on bone masks (A step 3) | all zone-conditioned features |
| `ncc_patches.npz` | patches from template_mean (B step 1) | refinement + QC |
| ~10 held-out annotated studies | manual, once | THRESH calibration + honest precision measurement |
| K≈10–15 atlas zone labelings (Rank 4) | propagate `zones.npy` (identity on template grid), hand-correct | LabelVoting / vote-fraction soft zones |
| refined unbiased template + probabilistic zone atlas (Rank 5) | 3–4 register-all/average/debias iterations reusing existing pipeline | everything upstream |

The critical cross-cutting fix: every sweep recipe that says "apply the inverse transform" is wrong for this codebase (fixed=template registration direction), and per-study transforms don't exist on disk — but the highest-value path (template-space zones on already-registered volumes) needs neither. The only code change to the existing pipeline is the optional `WriteTransform` one-liner in `/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/tools/register_and_export.py`.

---

*n_passed adversarial verification: 33 · n_failed: 7 · agents: 46 · full per-agent journal: subagents/workflows/wf_ec83a461-6dd/journal.jsonl*
