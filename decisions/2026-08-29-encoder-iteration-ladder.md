# Decision: Encoder iteration ladder — each make-or-break failure names its disease

**Date:** 2026-08-29
**Status:** accepted (running record; update as rungs land)
**Context:** First real make-or-break runs on the Effusion contrast (15 ref /
8 held-out neg / 35 pos, sagittal fluid-sensitive series). Law 5 governs:
when signal is missing, iterate the encoder, never add capacity. Each rung
below was diagnosed from evidence before the next was built.

## The ladder

| Rung | Stack | Verdict (AUC) | Diagnosed disease |
|---|---|---|---|
| v1 | affine only; no N4, no mask | no_separation (0.425) | Interior ~75/81-dense deviant patches in held-out normals; NOT at edges → cross-subject boundary misalignment. Global sparsity GOOD (0.2–4% survive → the S/N collapse premise holds). |
| v2 | + N4 + knee mask + B-spline (mask-aware metric + masked statistic) | no_separation (0.454) | Dense normal patches are UNIFORM-SIGN (0.95–1.0) over FLAT tissue (patch gradient ≤ knee median) → NOT misalignment: regional intensity offsets 4–6σ. Scanner/protocol contrast-ratio mismatch that p2–p98 scaling cannot reconcile. |
| v3 | + histogram matching to template (Nyul-style, background-excluded) | **partial_signal (0.655)** | First crossing of the signal bar. Residual ceiling: 3/8 held-out normals (and many abnormals) still peg density 1.0 — saturation pockets remain, so ranking is capped. Confirms Law 5's prediction: each encoder repair moved AUC (0.425 → 0.454 → 0.655) with the instrument held fixed. |
| v4 | + low-frequency detrend of the diff (mask-aware Gaussian, scale 24; statistic-side, no re-registration) | **partial_signal (0.739)** | Sweep over scales 8–32 gives a broad 0.69–0.74 plateau (robust, not knob-sensitive). Saturation mostly broken: 1/8 normals at 1.0. A wiring bug (ruff reformat broke a string-replace; flag silently defaulted to 0) was caught by refusing to believe a to-the-4th-decimal-identical AUC — verify the flag reaches the computation. |

## The ladder's terminal finding (v4 diagnosis)

The remaining ceiling is substantially a **finding confound, not an encoder
defect**: every one of the 58 labeled studies carries ≥1 positive finding, so
"Effusion-negative" held-out normals contain OTHER pathology — and the
finding-agnostic max-density statistic CORRECTLY fires on it. The 1.0-density
"normal" carries six findings (ACL, Medial Meniscus, Synovitis, Baker's,
Contusion, Fracture). Across all 43 test studies, Spearman(finding burden,
local density) = 0.28.

**True-normal reference upgrade (2026-08-30):** II.7 parser harvested 799
all-negative candidates; 80 fetched (ranged bundle reads), registered into the
ladder-invariant template space; reference rebuilt from 50 TRUE normals, 30
held out as clean negatives (eval n: 43 -> 73). Lens macro: study-level
0.492 -> 0.560, zone-level 0.551 -> 0.579. Gainers: Synovitis (0.55->0.65/0.76),
PF OA, MCL (0.39->0.66), Effusion; losers: Contusion (0.67->0.43), Lateral OA,
study-level Fracture inverted (0.27, n_pos=14 — small-sample prototype noise
suspected, not interpreted). Study-level now competitive with zone-level —
with clean negatives the whole-knee gestalt carries real signal.

**Positives at scale, out-of-sample (2026-08-30):** 335 parser-positive
studies fetched + registered (60-192 prototype positives per finding).
lens_eval2 = label-source split: prototypes from parser-labeled pool + the
50-normal consensus pole; evaluation strictly on gold (43 + 30 true
normals). Zone macro 0.589 / study 0.574 — consistent with the LOO numbers
(0.579/0.560) but now fully out-of-sample: LOO was measuring honestly.
Notables: Contusion 0.757 zone, ACL 0.613 zone (first real ACL signal),
Fracture 0.616, Medial Meniscus 0.607. Persistent weak: MCL (7 eval pos),
PF OA, Medial OA. The residual weakness is anatomical localization — grid
zones don't follow structures — which is the landmark/anatomical-zone rung
(the founder's II.1 open question), authorized as the next step.

**v5 — geometric canonicalization (2026-08-30, in progress):** DICOM tags carry
full spatial geometry + Laterality; pools are ~1/3 L, ~1/3 R, ~1/3 untagged —
**the reference had been squashing mirror-image knees together since v1** (no
warp can fix chirality; prime suspect for Medial/Lateral finding weakness).
Fix, all tag-arithmetic: (a) mm-true patient-space reconstruction via
SimpleITK GDCM series reading (honest oblique geometry, fixed 150x150x110mm
FOV — community evidence: physical crop beats resolution); (b) chirality
normalization — side derived from image-center patient-x sign (97.8% tag
agreement verified on our data; trick surfaced in competition discussion
737597), fallback Laterality tag, mirror L->canonical-R. Validated:
cross-chirality L-onto-R registration now lands at masked |diff| 0.208 =
same-side range. Community scan (founder-directed): NO landmark/registration
work in the competition; a 0.78-OOF practitioner's per-finding difficulty
profile matches ours structurally (localization is everyone's frontier).
Landmark prior-art research fleet dispatched (workflow knee-landmark-prior-art):
classical methods (Hough/atlas/SSM/multi-atlas fusion) with adversarial
constraint verification. registered*_v3bak dirs preserve the v3 space.

**Consequence:** substrate-level encoder repair is exhausted as a same-data
lever. The clean per-finding read is what II.4 (multi-scale HDC encode) +
II.5 (per-finding lens, structure/location-specific) exist to do — the next
work is BUILDING UP the design, not repairing the substrate. Data-side
sharpeners: II.7 report parser to mine true all-negative normals from the
4,349 unlabeled studies; multi-channel values (needs the remaining series
per study — one fresh signed bundle URL).

## Standing findings

- **The global S/N collapse holds on real data**: ≥96% of cells zero out in
  every study after registration + per-cell residual. The founding premise
  is not what is failing; the per-cell LICENSE (what intensity the reference
  tolerates where) is what each rung has been repairing.
- The B-spline mesh is deliberately coarse ([10,10,4] control points):
  condyle-scale correspondence without lesion-scale warps that would erase
  the pathology signal. Do not "fix" a future failure by refining the mesh
  past lesion scale.
- **Levers still in reserve**, in design order: landmark anchors
  (patella/condyles/plateau/notch — the founder's open question in the
  FOUNDING_RECORD); sigma shrinkage / more reference studies (small-N
  t-tails); regime stratification by scanner/protocol (Part III machinery,
  usable at the reference level as per-regime references); multi-channel
  voxel values across sequence x plane (II.4 — currently testing ONE series
  per study).

## ⛔ SUBSTRATE RESET (2026-08-30) — all v1–v4 numbers are DEAD

The v5 diagnosis condemned the substrate every prior number was measured on:
the reference had been squashing mirror-image knees since v1 (~1/3 of every
pool opposite-chirality) on naively slice-stacked, non-mm-true volumes. **All
quantitative results above — every AUC (0.425/0.454/0.655/0.739), every lens
macro (0.551/0.560/0.579/0.589/0.574), every per-finding number, the ≥96%
zero-out, the Spearman-0.28 confound, the "weak findings" list, and the
detrend σ=24 calibration — are readings of that condemned substrate.** They
remain in this file ONLY as the historical record of the diagnostic method
working (each repair moved the number with the instrument fixed). They are
NOT baselines, NOT expectations for v5, and NOT inputs to any design
decision. The detrend scale in particular must be RE-SWEPT on v5, not
assumed; whether detrend is needed at all is open.

**Boundary (from the session transcript, verified):** founder approved the
v5 design 2026-08-30T13:28; the first v5 chain carried an axis-mapping bug,
was killed at 14:37, its partial outputs deleted, and the corrected chain
relaunched at 14:41:42Z. Nothing registered before that timestamp exists in
the live tree (`_v3bak` dirs are archives, consumed by nothing). **The
theory-compliant stack (v5 mm-true chirality-canonical space + anatomical
zones) has produced ZERO evaluation numbers yet.** Its first-ever readings
come from the battery run after the chain + atlas + eye-QC complete.

Substrate-independent results that SURVIVE the reset: the report parser's
77.7% gold gate and the 799-normal harvest (text-only machinery), the
chirality oracle's 97.8% tag agreement (tag arithmetic), the v5 loader's
post-fix validation (L-onto-R masked |diff| 0.175; anatomical layout
checks), all Detective pins, and the fixed make-or-break instrument itself.

## v5 — first readings on the compliant substrate (2026-08-31)

First-ever make-or-break on the v5 space (mm-true, chirality-canonical,
corrected axes), on the TRUE-NORMAL layout (50 true-normal reference /
30 true-normal held-out / 35 Effusion-positive gold — a different contrast
from every pre-reset run; NOT comparable to the dead v1–v4 numbers):

| detrend σ | statistic AUC | verdict |
|---|---|---|
| 0 (off) | 0.58 | no_separation |
| 8 | 0.58 | no_separation |
| 16 | 0.67 | partial_signal |
| 24 | 0.68 | partial_signal |
| 32 | 0.66 | partial_signal |

Freshly derived (the pre-reset σ=24 calibration was discarded, not
inherited): low-frequency detrend is still required on v5, with a robust
σ∈[16,32] plateau; σ=24 is the plateau center. Residual disease at this
rung: several held-out TRUE normals still peg density 1.0 — saturation
pockets survive even with a chirality-clean reference and clean negatives.
The whole-volume finding-agnostic max-density statistic is the coarse
instrument; the zone-conditioned lens layer (atlas built 2026-08-31,
awaiting founder eye-QC) is the designed refinement.

## Consequences

- `data/registered_v1`, `data/registered_v2` are preserved for comparison;
  `data/registered` is always the current rung.
- The make-or-break harness is the fixed instrument across rungs — the
  verdict codes and the AUC statistic do not move between iterations
  (changing the test to fit the rung would invalidate the ladder).
