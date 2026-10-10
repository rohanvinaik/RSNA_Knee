# Decision: Anatomical zones are template-space label volumes, derived geometrically

**Date:** 2026-08-30
**Status:** accepted
**Context:** Grid zones (3×4×4) capped the lens layer exactly where anatomy is
small or thin (menisci, MCL, PF/compartment OA) — the same localization wall
the CNN field reports (their global pooling ≈ our grid boxes). The founder
directed a research fleet into classical landmark/atlas prior art
(`docs/LANDMARK_PRIOR_ART.md`, 46 agents, adversarially verified) and granted
bounded wiggle: priors/statistics for landmark-anchoring and spatial
normalization ONLY. Founder's framing: image-pinning fidelity buys
multiplicative analysis gains because the possible analysis space shrinks
super-linearly; the analysis stack inherits the improvement as pure gravy.

## Decision

Build order (fleet ranks 1→3 now, 4→5 scheduled):

1. **v5 geometric canonicalization underneath everything** (already running):
   mm-true patient-space reconstruction from DICOM geometry tags; chirality
   normalized to canonical-RIGHT (side from image-center patient-x sign,
   97.8% tag-verified; fallback Laterality tag). All tag arithmetic.
2. **Template-space zone label volume** (Rank 1): zones are CONSTANT INDEX
   MASKS on the canonical grid — annotate/derive once, apply to every study
   with zero transform bookkeeping.
3. **Zones derived geometrically, not hand-clicked** (Rank 3): mean-intensity
   template from v5 normals → template bone masks (Otsu + components,
   eye-QC'd once — the single human-in-the-loop artifact) → joint line as
   the ridge of the femur/tibia distance-transform gap; condyles as extremal
   points of the distal-femur height field; notch as the saddle between
   them; medial/lateral split from principal axes; zones painted from these:
   joint-line slab, retropatellar shell, intercondylar notch, suprapatellar
   recess, popliteal fossa, medial/lateral compartments. The inter-bone gap
   machinery also emits compartment gap-width features (direct OA channel).
4. **NCC patch refinement + QC gate** (Rank 2): template landmark patches
   matched per-study via 3-D normalized cross-correlation
   (`skimage.feature.match_template`, execution-verified); NCC peak is the
   per-study registration-confidence scalar; low-NCC studies fall back to
   propagated positions and get flagged.
5. **Scheduled next** (not built yet): multi-atlas zone label fusion with
   vote-fraction soft boundaries (Rank 4, `sitk.LabelVoting`/STAPLE);
   unbiased iterative mean template (Rank 5, OAI pattern — the current
   single-study template is a known bias, background compute job).

The encoder consumes the zone label volume in place of `ZoneGrid` — the
analysis stack above is unchanged and inherits the localization gains.

## Rationale

- All volumes already live on one template grid, making template-space zones
  nearly free (the fleet's repo-aware reordering of the standard literature).
- Verified precision expectations: template-propagated knee landmarks
  2.05±1.30 mm (92% ≤4 mm); NCC refinement ~1.5–2.5 mm typical.
- Everything is deterministic geometry/statistics; the only human artifact
  is the one-time eye-check of template bone masks.

## Alternatives Considered

- Hand-drawn zone boxes — rejected: unprincipled, unreproducible.
- SSM/ASM surface models — deferred: 1–2 weeks; only if surface precision
  becomes the measured bottleneck.
- Generalized Hough for QC — rejected: redundant with the NCC score.
- Small keypoint network (bounded-ML normalization utility) — permitted by
  Law 3 but not needed: classical machinery meets the precision bar.

## Consequences

- `sitk.WriteTransform` should be added when native-space landmark output is
  ever needed (transforms currently discarded; noted, not built).
- The instrument suite (make-or-break, lens evals) reruns unchanged on v5 +
  zones; ladder comparability maintained via preserved `_v3bak` outputs.
