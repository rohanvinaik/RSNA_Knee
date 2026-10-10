# K07 — Frame and bootstrap registration

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K07'` |
| **Depends on** | K05 (stored values, geometry, inventory) |
| **Consumed by** | K08 (bootstrap-registered normals), K09/K10 (series on plane grids), K22 (registration uncertainty), K18 (kernel path) |
| **Commit label / tag** | `knee/K07` · `knee-K07` |

## 1. Purpose and authority

To put every series of a study into one canonical knee frame, and to say where that placement can be trusted.
- **THEORY Law 3:** registration is the one bounded utility.
- **The accord:** intra-study motion is aligned by default; transforms are kept; constraint readings are separate
  from the population axis (THE_KNEE §1 step 2; §2 changes 2 and 7).
- **Bootstrap ownership.** This chapter owns the bootstrap template and landmarks, with their provenance and
  limited checks. K08 refines and replaces them (Codex design round 2, D1).
- **Non-goals:** zones and atlas building (K08); deviation (K10).

## 2. Dependencies and consumers

**Produced** (`knee.core.frame`, `knee.run.register`, `knee.build.bootstrap`):
- `study_side(patient_x_sign, laterality_tag, fibular_side) -> right | left | chirality_uncertain`: chirality,
  from three witnesses. The fibular head's side is `unread` until K08 builds its landmark.
- `bias_field(series) -> Field`: the N4 bias field, a **measured nuisance** kept beside the stored values. It is
  never applied in place (THEORY II.1; ARCH §3.1).
- `study_box(...)`: one shared centre and extent for all of a study's series.
- `PlaneGrid` for sagittal, coronal and axial, each sharp in-plane and coarse along its slice normal, over one
  physical box.
- `rigid_align(series, reference_series) -> Transform`: intra-study motion alignment.
- `register(study, template) -> Transform`: affine, then coarse B-spline on a [10, 10, 4] mesh. Kept and
  written. It maps template-space points to the study's patient space, which is the direction resampling needs.
- `jacobian_check(transform, region) -> invertible | folded:<where>`: the B-spline family is not invertible by
  construction. The inverse is used only where this check holds, and the code is a constraint reading.
- `resample(series, transforms, grid) -> PlaneVolume`.
- Constraint readings:
  - `landmark_ncc(...) -> {landmark: (score, code)}`;
  - `check_registration(...) -> code`, an independent second-plane registration compared at the landmarks;
  - `chirality_check(...) -> code`.
- The bootstrap assets: the v5 single-study template and its landmarks, with their provenance and eye-check
  record.

**Consumers:** K08, K09, K10, K19, K22, K18.

## 3. Mechanism

1. **Chirality.** ARCH §2.2 consequence 3 reads the side from "the sign of the image center's patient-x, with the
   Laterality tag as fallback" (97.8% tag agreement, LADDER v5), and §1.8 makes chirality a constraint reading.
   A sign is not a proof, so there are three witnesses: the patient-x sign, the tag, and the fibular head's side
   (lateral, once K08 builds it).
   - Agreement mirrors left knees to canonical-right.
   - Disagreement reads `chirality_uncertain`. That study is read on the constraint axis, and never mirrored by
     a guess.
2. **One box per study.** Every series shares one centre. The legacy loader centred each series on its own centre;
   that is replaced.
3. **Motion.** Each series is rigidly aligned (6 dof, mutual information) to the study's reference series:
   sagittal FS if present, else the first by a declared order. The tag-shared frame of reference is the starting
   point, never assumed to be motion-free.
4. **Template registration.** Affine, then coarse B-spline on the reference series, so that "condyle-scale
   correspondence without lesion-scale warps that would erase the pathology signal" holds (LADDER, standing
   findings). The transform is carried to every series through its rigid alignment.
5. **The intensity nuisance.** THEORY II.1 names N4 bias correction "the prerequisite for a clean subtract".
   ARCH §3.1 forbids per-series rescales *before the law*, because they destroy cross-series ratios. Both are
   kept:
   - the N4 field is estimated per series and stored as a nuisance record;
   - the stored values are never divided in place;
   - K09 and K10 apply the field, with the per-series gain γ_s (ARCH §3.3.3; computed in K09 on K08's
     reference-tissue zones), only in the population axis's comparison representation;
   - K24's law, if selected, reads the stored values.
6. **Resampling contract**, fixed before any SAME:
   - coordinates: physical mm, patient space. A series K05 marks `irregular` is placed by its per-slice
     positions, never by one affine;
   - interpolation: linear for intensities, nearest for labels;
   - boundary: outside the field is a **status** (`out_of_field`), never a fill value;
   - arithmetic: float64 internally, float32 stored.
7. **Constraint readings.**
   - NCC at the bootstrap landmarks (patch match in a search window);
   - a check registration from a second plane, its disagreement measured in mm at the landmarks;
   - the chirality check.

   Each reading is a named code. None of them ever touches the population axis.
8. **Sharding** across the M1 Max and the Mac Pro by study digest. Registration may differ across architectures,
   so the cross-node SAME contract for this stage is that **decisions and codes match** and landmark positions
   agree within a tolerance stated before the run (mm).

## 4. Contracts

- **Transforms** are ITK transform files plus a manifest. The manifest records:
  - the direction: fixed is the template, moving is the study. The transform maps a template-space point into
    the study's patient space, and resampling pulls study values onto the template grid through it;
  - the composition order (rigid ∘ affine ∘ B-spline) and each component's domain;
  - the Jacobian check's result per region.
- **The bias field:** float32 per series on the series' own grid, with its N4 parameters and its version.
- **Plane volumes** are float32 in C order, axis order (slice, row, col) per grid, with a uint8 status volume
  (`in_field | out_of_field`).
- **Bootstrap assets** live in `data/atlas/bootstrap/`, competition-derived and so never in git, with a manifest
  and the eye-check record.

## 5. Implementation choice

- **SimpleITK** (ITK, C++) for registration and resampling, with Python orchestration.
- **Concurrency is declared:** ITK threads per worker × workers ≤ cores. The Mac Pro gets 2 workers × 6 threads
  on 16 GB.
- **Prior art, in legacy `tools/register_and_export.py`:**
  - `derive_side` and `load_canonical_volume` (mm-true, chirality): reused as logic after review, re-pinned,
    with the per-series centring replaced;
  - `register_full`: rewritten so that its transform is kept (it is discarded today; ZONES, Consequences) and so
    that it takes the stored values;
  - `n4_correct`: **rewritten as a measured field.** The field is estimated and kept, and it is never divided
    in place. ARCH §3.1's objection, cross-series ratios destroyed, is about the law's input, which keeps the
    stored values.
  - `normalize_intensity` (p2–p98) and `histogram_match`: **retired.** ARCH §3.4.1, quoting LADDER, records
    their diseases: "regional intensity offsets 4–6σ", a "contrast-ratio mismatch that p2–p98 scaling cannot
    reconcile", and histogram matching "blind to which tissue was where". They are replaced by the gain
    specialist's γ_s on reference tissue (ARCH §3.3.3, §3.3.9 Table 3.5).
  - Each gets a `MIGRATION.md` row.

## 6. Verification

- **Detective:** `study_side`, the code functions of the constraint readings, and the pure geometry decisions
  are converged.
- **Hypothesis:**
  - where `jacobian_check` holds, a transform composed with its inverse returns each point within a stated
    tolerance;
  - `study_side` never mirrors on disagreement;
  - resampling then sampling is consistent at grid nodes;
  - mirroring is an involution.
- **Known-shift tests on report-negative studies:** a study deliberately shifted by known amounts beyond the
  landmark error must raise the constraint codes, and nothing may be read as pathology. K11 later adds full
  misregistration phantoms.

## 7. Integration

- `just register <shard>` writes plane volumes and transforms into the store.
- The kernel path (K18) calls `knee.run.register` per study.

## 8. Acceptance

Written first: `acceptance/K07.toml`.
- **Behavioural correctness:**
  - transforms are kept, and their invertibility is a recorded constraint reading;
  - the known-shift tests raise the constraint codes;
  - the decisions are pinned.
- **Representation fidelity:**
  - chirality is preserved, with its rate against the Laterality tag and the share `chirality_uncertain`
    recorded;
  - status volumes mark every out-of-field voxel.
- **Domain validity:** the landmark disagreement between the bootstrap template and the check registration is
  recorded per study class. It sets K22's frame-step magnitudes.
- **Performance evidence:** series registered and metric evaluations counted per node; seconds as information,
  with the cold and warm phases separated. Scope: "SimpleITK on the named node".
- **Evidence scope:** the corpus shards registered, and the nodes named.
- **Invalidation:**
  - a change to the bootstrap assets, the SimpleITK version, the mesh or the metric;
  - K08's refined template, after which K08 re-runs this chapter's procedure.

## 9. Open matters

- **Facts:** cross-architecture registration agreement, which K07 measures before shards merge.

## 10. Provenance and status log

- **Sources:**
  - THEORY II.1;
  - ZONES (Ranks 1–5);
  - LADDER (v5; the standing findings);
  - KNEE_ARCHITECTURE §2.4 and §3.1;
  - PRIORART;
  - THE_KNEE §3.5 and §4.
- **2026-10-02:** specified in K00.
- **2026-10-02, revision 1:**
  - chirality from three witnesses, with `chirality_uncertain` (F17; ARCH §2.2, §1.8);
  - the transform's direction and the Jacobian check (F17);
  - per-slice placement (F17, F40);
  - N4 kept as a measured field, and p2–p98 and histogram matching retired for γ_s (F01; THEORY II.1; ARCH §3.1,
    §3.3.3, §3.4.1).
