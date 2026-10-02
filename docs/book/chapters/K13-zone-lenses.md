# K13 — Zone lenses: the volumetric, questionless measurements

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K13'` |
| **Depends on** | K12 (layout v1), K11 (phantoms), K08 (zones and votes), K10 (deviation, signatures) |
| **Consumed by** | K15 (bodies and objects), K16 (structure-alone decisions), K22 (perturbed re-reads), K23 (healthy false readings) |
| **Commit label / tag** | `knee/K13` · `knee-K13` |

## 1. Purpose and authority

To measure what the atlas's zones can support without patient-specific boundaries.
- **THESIS §3.2:** "a cheap, deliberately lossy view that measures one thing and knows no question".
- **The accord:** members are questionless (THE_KNEE §2, change 6). Readings that need patient-specific
  boundaries are deferred to K20 behind K19's delineation (Codex design round 2, D5).
- **Non-goals:** no sign, no finding, no exclusion. K14 and K16 hold those.

## 2. Dependencies and consumers

**Produced** (`knee.run.lens.zone`): one lens per law term that zones support. Each returns a `LensReading`.

| lens | measures (one thing) | reads | open quantity (sane values: **each reported, none selected**) |
|---|---|---|---|
| recess fluid volume | mm³ of `fluid` signature inside each recess zone, by vote-weighted membership | signatures, zones, series coverage | none |
| marrow edema-signature extent | mm³ and depth band of `edema_like` signature per marrow subregion | signatures, zones | minimum extent {3, 5} mm |
| fat-pad share | share of Hoffa's pad places reading fluid-sensitive bright where fat is expected | signatures, deviation | none |
| compartment gap | femur–tibia distance per compartment (median, with the minimum beside it), from bone surfaces in the zone | plane volumes, zones | sampling step {0.5, 1} mm |
| coverage | effective slices crossing each zone along its question's axis, per series | geometry, zones | obliquity tolerance {15°, 30°} |

**Consumers:** K15, K16, K22, K23.

## 3. Mechanism

- **Zone membership is uncertain.** Each reading is computed under the zone's vote fractions (K08) and the study's
  local placement uncertainty (K07), and carries an **uncertainty interval**, never a bare value. These are the
  visibility and uncertainty contract.
- **Silences carry causes:** `out_of_field`, `insufficient_coverage`, `reference_silent`, `below_noise_floor`,
  `series_absent`, `placement_unverified` (from the K07 constraint codes).
- **Provenance:** the series, plane and contrast that produced each reading.
- **No reading is signed.** "For" and "against" belong to the agencies (K14 and K16).

## 4. Contracts

- `LensReading`: `{lens, zone, value, interval, digit (K12 quantizer), silence?: cause, series_ids,
  layout_id}`.
- Units are mm³, mm, share in [0, 1], and slice counts.

## 5. Implementation choice

- **One Numba core per lens,** operating on zone-cropped arrays. Each has a Python reference with an explicit order
  and is admitted by SAME.
- **Crops:** the bounding box of the zone, padded by its placement uncertainty. Bytes scanned are recorded.
- **Prior art:** KNEE_ARCHITECTURE Table 2.8a (lenses 6, 12, 14, 16, 18) and `anatomy.joint_line` (legacy).
  **Decision:** specifications adopted, revised so the lenses are unsigned; the code is fresh. `joint_line`'s logic
  is reviewed for reuse in the gap lens and recorded in `MIGRATION.md`.

## 6. Verification

- **Detective:** each lens's pure decisions (silence causes, interval rules) are converged. The cores are reached
  by captured arguments.
- **Hypothesis:**
  - volumes are additive over disjoint subzones;
  - the gap is symmetric under mirroring;
  - coverage is monotone in the obliquity tolerance.
- **SAME** for every Numba core.

## 7. Integration

- `knee.run.lens.zone.read_all(study_reading, atlas, layout) -> [LensReading]`.
- Readings are written through K12.

## 8. Acceptance

- **Behavioural correctness:** SAME; pinned decisions; every reading has a value or a silence with its cause.
- **Representation fidelity:** the intervals contain the phantom truth for planted effusions and edemas (K11) at
  the stated coverage rate.
- **Domain validity:** the healthy distribution of every lens on `checking` normals, per regime, with bounds; the
  phantom response curves, which rise with amplitude.
- **Performance evidence:** milliseconds per study per lens, reference against Numba.
- **Evidence scope:** layout v1, atlas v-current, phantoms v-current.
- **Invalidation:** a change to the atlas, the references, the signatures, or the layout.

## 9. Open matters

- **No selection of sane values.** Where several values of a lens's open quantity are physically sane, the lens
  reports a reading at **each** of them. Choosing one by how well it separates phantoms from normals, or gold from
  anything, would seat a member by discrimination on one query, a No Popery tell (`AGENTS.md`, Law 2). An agency
  rule names which reading it consumes, and why. A sane value comes from the law (for example, a minimum extent at
  least the series' slice spacing), never from a fit.
- **Facts:** each lens's healthy distribution per sane value (K23 consumes these).

## 10. Provenance and status log

- **Sources:**
  - THESIS §3.2;
  - KNEE_ARCHITECTURE §2.8;
  - Codex design round 2 (D5);
  - THE_KNEE §2 (change 6).
- **2026-10-02:** specified in K00.
