# K08 — The atlas and refined registration

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K08'` |
| **Depends on** | K07 (bootstrap registration), K03 (roles: `template_build`, `template_check`), K06 (report-negative candidates) |
| **Consumed by** | K09 (places), K10–K13 (zones), K19 (search regions, attachments), K11 (phantom placement), K18 (kernel artifacts) |
| **Commit label / tag** | `knee/K08` · `knee-K08` |

## 1. Purpose and authority

To build, per plane, an unbiased template and the atlas the lenses need: zones, landmarks, attachments and
multi-atlas votes. Then to re-register the corpus against it.
- **ZONES** Ranks 4–5: multi-atlas fusion, and an unbiased template.
- **The accord:** the atlas *proposes search regions*; it never delineates the patient (THE_KNEE §2, change 2).
- **Codex** (design round 2, D2): template convergence is not enough. Acceptance requires anatomical
  correspondence, chirality preservation, deformation checks, and template-building subjects kept separate from
  checking subjects.

## 2. Dependencies and consumers

**Produced** (`knee.build.atlas`; `knee.core.atlas` for the loaders):
- **Templates** per plane class.
- **A zone label volume** per plane, with vote numerators and denominators kept per voxel.
- **Landmarks and attachment sites:** patella, condyles, notch, tibial eminence, fibular head, the femoral and
  tibial attachments of the ACL and PCL, the MCL's femoral and tibial insertions.
- **The atlas manifest.**

**Re-registration** of the corpus runs against the refined templates, through K07's procedure.

**Consumers:** K09–K13, K18, K19, K11.

## 3. Mechanism

1. **Subjects.** `template_build` subjects (K03 roles, drawn from K06's report-negative candidates) build the
   template. `template_check` subjects judge it. No subject is both.
2. **The unbiased template, per plane, in one frame.** Every plane's template is defined over K07's one physical box,
   in the same template mm frame, so the plane grids share coordinates by construction. ARCH §2.10 leaves two
   routes open:
   - (a) paint each plane's zones from its own template's bone masks, by the same rules;
   - (b) paint once on a fine atlas and resample to every grid.

   Route (b) is tried first, because it gives one set of boundaries. The cross-plane agreement decides it, and
   that agreement is itself an L1/L3 check (ARCH l.1488). Starting from the bootstrap template, iterate:
   - register every building subject to the current template (K07's procedure);
   - average in template space;
   - re-centre so that the mean deformation is ~0.

   The stop criterion is declared before the run (a change of mean intensity and of mean deformation below
   stated levels), and so is the guard on the number of iterations.
3. **Checks on the template, against truth independent of the registration** (ARCH §1.8 l.604–608 measures with
   deliberate misregistration; §2.10 l.1458 names the founder's eye-check):
   - **known transforms:** checking subjects warped by known transforms. The recovery error at the landmarks is
     truth by construction;
   - **the founder's landmark sheet:** a sample of checking subjects whose landmarks he marks, without the
     registration's output shown. These positions are the operator's truth;
   - the registration's own output is never its truth;
   - **chirality preserved:** no mirrored subject enters;
   - **deformation:** the Jacobian determinant is > 0 everywhere, with no folding, and its distribution is
     recorded.
4. **Zones**, painted geometrically from the template's bone masks and landmarks by deterministic rules. The bone
   masks get the founder's eye-check, the one human artifact. The zones:
   - meniscal horns and bodies (the peripheral joint-space wedge between condyle and plateau);
   - ACL and PCL tubes (attachment to attachment) and the notch roof line;
   - the MCL band and its shell; the LCL band;
   - cartilage plates, per MOAKS subregion;
   - compartments;
   - recesses: suprapatellar, posterior, gutters;
   - Hoffa's pad;
   - the Baker's region and the medial gastrocnemius and semimembranosus tendons;
   - marrow subregions, including the L5 sites;
   - pseudotear sites;
   - reference tissues (muscle, subcutaneous fat), for the gain specialist's γ_s (ARCH §2.10 l.1478, §3.3.3);
   - a cortical shell.
5. **Multi-atlas votes.** Labels propagated from several checked templates, or from leave-one-out subject atlases,
   are fused. Each voxel keeps every zone's vote numerator and the denominator; the fraction is never rounded
   into a decision.

## 4. Contracts

- **Zone volumes:** uint8 label of the plurality zone, plus int16 vote numerators per zone (sparse, only where
  > 0), plus the denominator. Per plane grid. With a manifest.
- **Landmarks:** template mm coordinates, each with its derivation rule and checking-subject error statistics.
- **Atlas artifacts** are competition-derived: they live in `data/atlas/v<k>/` and in a private Kaggle dataset
  for the kernel.

## 5. Implementation choice

- **Python, NumPy and SciPy** for painting, offline. **SimpleITK** for registration. **Numba** for any per-voxel
  vote accumulation that measures as hot.
- **Prior art:** legacy `RSNA_Knee/anatomy.py` (bone masks, landmarks, the 12-label zone volume from one study)
  and `tools/build_atlas.py`.
  - **Decision:** the rule logic (joint line, condyles and notch from the height field, `classify_bone_groups`'
    refusal to fabricate a split) is reused after review and re-pinned.
  - The single-study template is superseded by the unbiased template.
  - The zone set is extended.
  - Each unit gets a `MIGRATION.md` row.

## 6. Verification

- **Detective:** the zone-painting decisions, the landmark rules and the vote fusion's pure functions are
  converged.
- **Hypothesis:**
  - the plurality label is consistent with the votes;
  - numerators never exceed the denominator;
  - painting is deterministic.
- **Cross-plane:** a structure's zone agrees across the sagittal, coronal and axial grids within a stated mm
  tolerance (an L1/L3 check).

## 7. Integration

- `just atlas` builds templates and zones, then re-registers the corpus.
- The kernel loads the atlas from its private dataset (K18).

## 8. Acceptance

Written first: `acceptance/K08.toml`.
- **Behavioural correctness:**
  - the stop criterion was met, or the run is reported as having hit its guard;
  - there is no folding;
  - the decisions are pinned.
- **Representation fidelity:** votes are kept as numerators and denominators; cross-plane zone agreement is within
  tolerance.
- **Domain validity (discovery):**
  - the landmark error on checking subjects, against both independent truths, with bounds, beside the prior
    figure of 2.05 ± 1.30 mm (ZONES);
  - the cross-plane agreement per structure, and the route it chose;
  - the founder's eye-check, recorded.
- **Performance evidence:** template iterations and registrations counted per node; seconds as information.
- **Evidence scope:** the building and checking subjects at this version.
- **Invalidation:** a change to the subject roles, the registration procedure, the zone rules, or the pool (K06).

## 9. Open matters

- **Policy:** the founder's eye-check of bone masks and zones, which is required.
- **Fact:** whether one template per plane class suffices, or regime-specific templates are needed. Measured by
  the landmark error per regime.

## 10. Provenance and status log

- **Sources:**
  - ZONES;
  - PRIORART (Recipes A and B);
  - KNEE_ARCHITECTURE §2.10;
  - LADDER;
  - THE_KNEE §2 (change 2).
- **2026-10-02:** specified in K00.
- **2026-10-02, revision 1:**
  - landmark truth from known transforms and the founder's sheet, never the registration's own output (F42);
  - one template frame for every plane, with ARCH §2.10's routes decided by cross-plane agreement (F42);
  - the reference-tissue zones serve γ_s (F01);
  - work counted (F39).
