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
- `study_side(...) -> code`: chirality, made canonical-right.
- `study_box(...)`: one shared centre and extent for all of a study's series.
- `PlaneGrid` for sagittal, coronal and axial, each sharp in-plane and coarse along its slice normal, over one
  physical box.
- `rigid_align(series, reference_series) -> Transform`: intra-study motion alignment.
- `register(study, template) -> Transform`: affine, then coarse B-spline on a [10, 10, 4] mesh. Kept, written,
  invertible.
- `resample(series, transforms, grid) -> PlaneVolume`.
- Constraint readings:
  - `landmark_ncc(...) -> {landmark: (score, code)}`;
  - `check_registration(...) -> code`, an independent second-plane registration compared at the landmarks;
  - `chirality_check(...) -> code`.
- The bootstrap assets: the v5 single-study template and its landmarks, with their provenance and eye-check
  record.

**Consumers:** K08, K09, K10, K19, K22, K18.

## 3. Mechanism

1. **Chirality.** The side comes from the sign of the image centre's patient-x, with the Laterality tag as a
   fallback (97.8% tag agreement, LADDER v5). Left knees are mirrored.
2. **One box per study.** Every series shares one centre. The legacy loader centred each series on its own centre;
   that is replaced.
3. **Motion.** Each series is rigidly aligned (6 dof, mutual information) to the study's reference series:
   sagittal FS if present, else the first by a declared order. The tag-shared frame of reference is the starting
   point, never assumed to be motion-free.
4. **Template registration.** Affine, then coarse B-spline on the reference series, so that "condyle-scale
   correspondence without lesion-scale warps that would erase the pathology signal" holds (LADDER, standing
   findings). The transform is carried to every series through its rigid alignment.
5. **Resampling contract**, fixed before any SAME:
   - coordinates: physical mm, patient space;
   - interpolation: linear for intensities, nearest for labels;
   - boundary: outside the field is a **status** (`out_of_field`), never a fill value;
   - arithmetic: float64 internally, float32 stored.
6. **Constraint readings.**
   - NCC at the bootstrap landmarks (patch match in a search window);
   - a check registration from a second plane, its disagreement measured in mm at the landmarks;
   - the chirality check.

   Each reading is a named code. None of them ever touches the population axis.
7. **Sharding** across the M1 Max and the Mac Pro by study digest. Registration may differ across architectures,
   so the cross-node SAME contract for this stage is that **decisions and codes match** and landmark positions
   agree within a tolerance stated before the run (mm).

## 4. Contracts

- **Transforms** are ITK transform files plus a manifest giving their direction (fixed: template; moving: study)
  and composition order (rigid ∘ affine ∘ B-spline).
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
  - `n4_correct`, `normalize_intensity` and `histogram_match`: **retired from the main path**, because they
    rescale each series alone and destroy cross-series ratios (KNEE_ARCHITECTURE §3.1). Each gets a
    `MIGRATION.md` row.

## 6. Verification

- **Detective:** `study_side`, the code functions of the constraint readings, and the pure geometry decisions
  are converged.
- **Hypothesis:**
  - a transform composed with its inverse returns each point within a stated tolerance;
  - resampling then sampling is consistent at grid nodes;
  - mirroring is an involution.
- **Known-shift tests on report-negative studies:** a study deliberately shifted by known amounts beyond the
  landmark error must raise the constraint codes, and nothing may be read as pathology. K11 later adds full
  misregistration phantoms.

## 7. Integration

- `just register <shard>` writes plane volumes and transforms into the store.
- The kernel path (K18) calls `knee.run.register` per study.

## 8. Acceptance

- **Behavioural correctness:**
  - transforms are kept and invertible within the tolerance;
  - the known-shift tests raise the constraint codes;
  - the decisions are pinned.
- **Representation fidelity:**
  - chirality is preserved, with its rate against the Laterality tag recorded;
  - status volumes mark every out-of-field voxel.
- **Domain validity:** the landmark disagreement between the bootstrap template and the check registration is
  recorded per study class. It sets K22's frame-step magnitudes.
- **Performance evidence:** seconds per series per node, with the cold and warm phases separated. Scope:
  "SimpleITK on the named node".
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
