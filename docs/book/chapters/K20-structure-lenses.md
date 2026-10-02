# K20 — Structure lenses

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K20'` |
| **Depends on** | K19 (containers, certificates), K12 (layout, extended here to v2), K11 (phantoms) |
| **Consumed by** | K15 (objects inside structures), K16 (the fibrous and compartment agencies now read), K22, K23, K25 |
| **Commit label / tag** | `knee/K20` · `knee-K20` |

## 1. Purpose and authority

The questionless measurements that need the patient's own boundaries.
- **THESIS recipe step 2:** "Name one lens per term of the law."
- **The accord:** lenses are unsigned (change 6). An intact band cannot exclude ACL or MCL *injury* under the
  official labels (change 3).

## 2. Dependencies and consumers

**Produced** (`knee.run.lens.structure`), each lens measuring one thing inside K19's containers:

| lens | measures | open quantity (each sane value reported, none selected) |
|---|---|---|
| surface contact | per plane, the slices on which a deviant component inside the meniscus touches its femoral or tibial surface (not the capsular side). Per-plane counts and cross-plane concurrence are kept **apart** (Q13) | — |
| bow tie | the contiguous sagittal slices on which the body is one band joining the horns | — |
| extrusion | mm of meniscus beyond the plateau margin, at the coronal mid-body | — |
| continuity | the longest run along a ligament's centerline without fibrous signature, read against that ligament's own reference (the ACL is striated) | sampling step {0.5, 1} mm |
| angle | the angle between the ACL band's principal axis and the notch roof line | segment {distal half, whole} |
| neck | whether a fluid path joins a posteromedial collection to the joint between the medial gastrocnemius and semimembranosus tendons | — |
| line | the length of a linear dark component inside a confirmed edema object, reaching cortex (T1 and fluid-sensitive) | minimum length {3, 5} mm |
| cartilage | the share of a plate's shell where cartilage gives way to fluid or bone | shell depth {2, 3} mm |
| margin | bone-signature volume beyond the reference bone surface at compartment and patellar margins | — |

**Layout v2** (K12 extended): new banks for these values. It gets a new layout ID; v1 profiles are never compared
with v2.

**Consumers:** K15, K16, K22, K23, K25.

## 3. Mechanism

- **Each reading carries** its value, its interval from the container uncertainty, its digit, its silences with
  causes (including `insufficient` from the visibility certificate), and its provenance (series, plane, contrast).
- **Magic angle and failed suppression** are law-qualified *instrument* explanations (K14's tiers):
  - fibrous signal brightening on short-TE series only, at θ ≈ 54.7° to B0 (B0's axis from the header and the
    magnet class), is marked `instrument_candidate:magic_angle` on that reading;
  - fluid-sensitive-bright signal that is T1-bright in fat, inside the suppression-failure field, is marked
    `instrument_candidate:suppression`.

  Agencies consume these marks. The lens itself never vetoes.

## 4. Contracts

- `LensReading`, as in K13, plus `structure_id` and `container_uncertainty_mm`.

## 5. Implementation choice

- **One Numba core per lens,** on container crops. Each has a reference and a SAME twin.
- **Prior art:** KNEE_ARCHITECTURE Table 2.8a, lenses 4, 7–11, 13, 15, 17 and 19. **Decision:** specifications
  adopted, made unsigned; exclusions are moved to the agencies under K14's tiers.

## 6. Verification

- **Detective:** silence and instrument-candidate decisions are converged.
- **Hypothesis:**
  - contact counts are invariant to slice ordering;
  - continuity runs are additive over disjoint segments;
  - the angle is invariant under mirroring.
- **Phantoms (K11):** contact on k slices reads k; intrasubstance signal without contact reads 0; a gap of length L
  reads a run consistent with L; the magic-angle phantom is marked as an instrument candidate.

## 7. Integration

The readings join the kept record (K15). The fibrous agency now has readings (K16's rules apply). Re-run
`just firstlight`.

## 8. Acceptance

- **Behavioural correctness:** SAME; the decisions are pinned; the phantom readings are as specified; first light
  is re-run and passes its checks.
- **Representation fidelity:** layout v2 versioning refuses a cross-layout comparison.
- **Domain validity:** the healthy distributions on `checking` normals per lens, sane value and regime, with
  bounds; the phantom response curves; the false-contact rate per meniscal subregion on normals (K23's input).
- **Performance evidence:** milliseconds per study per lens.
- **Evidence scope:** the K19 containers and the series classes present.
- **Invalidation:** a change to the containers, the signatures, layout v2, or the B0 and magnet-class rules.

## 9. Open matters

- **Facts:**
  - Q13 (two slices across planes): both counts are reported; the agency rule that consumes them is cited to the
    clinical source's exact definition;
  - which magnet models are vertical-field (B0 across the leg), from header model names, with "unknown" kept.

## 10. Provenance and status log

- **Sources:**
  - KNEE_ARCHITECTURE §2.3.1, §2.5 and §2.8;
  - De Smet and Tuite 2006;
  - Helms et al. 1998;
  - Peterfy et al. 1994;
  - THE_KNEE §2 (changes 3, 6).
- **2026-10-02:** specified in K00.
