# K13 — Zone lenses: the volumetric, questionless measurements

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K13'` |
| **Depends on** | K12 (layout v1), K11 (phantoms), K08 (zones and votes), K10 (deviation, signatures) |
| **Consumed by** | K13a (healthy false readings, the gate), K15 (bodies and objects), K16 (structure-alone decisions), K22 (perturbed re-reads), K23 |
| **Commit label / tag** | `knee/K13` · `knee-K13` |

## 1. Purpose and authority

To measure what the atlas's zones can support without patient-specific boundaries.
- **THESIS §3.2:** "a cheap, deliberately lossy view that measures one thing and knows no question".
- **The accord:** members are questionless (THE_KNEE §2, change 6). Readings that need patient-specific
  boundaries are deferred to K20 behind K19's delineation (Codex design round 2, D5).
- **Non-goals:** no sign, no finding, no exclusion. K14 and K16 hold those.

## 2. Dependencies and consumers

**Produced** (`knee.run.lens.zone`): one lens per law term that zones support. Each returns `LensReading`s in two
forms, kept apart (`provenance/build/revision_1.md`, §F03):
- **per acquisition:** read on one series from its own tissue level and z (K10). This is a *voice*, counted with the
  pairs' dependence statuses K13a measures (K14's set-based concurrence);
- **joint:** read from the tissue word, whose sources are all its series. This is one dependent reading of all
  its sources, a law check that supports and never votes (ARCH §2.3 consequence 3; §5.3, "the committee is the
  series").

| lens | measures (one thing) | reads | open quantity (sane values: **each reported, none selected**) |
|---|---|---|---|
| recess fluid volume | mm³ of fluid inside each recess zone, the MCL's periligamentous shell included (ARCH lens 12), by vote-weighted membership. Per acquisition: the series' fluid level. Joint: the `fluid` word | tissue levels and words, zones, series coverage | none |
| marrow edema-signature extent | mm³ and depth band of edema per marrow subregion. Per acquisition: the series' edema level. Joint: the `edema_like` word | tissue levels and words, zones | minimum extent {3, 5} mm |
| fat-pad share | share of Hoffa's pad places reading fluid-sensitive bright where fat is expected | signatures, deviation | none |
| compartment gap | femur–tibia distance per compartment (median, with the minimum beside it), from bone surfaces in the zone | plane volumes, zones | sampling step {0.5, 1} mm |
| coverage | effective slices crossing each zone along its question's axis, per series | geometry, zones | obliquity tolerance {15°, 30°} |

**Consumers:** K15, K16, K22, K23.

## 3. Mechanism

- **Zone membership is uncertain.** Each reading is computed under the zone's vote fractions (K08) and the study's
  local placement uncertainty (K07), and carries an **uncertainty interval**, never a bare value. These are the
  visibility and uncertainty contract.
- **The inputs' uncertainty travels with the reading** (ARCH §3.3.7: σ goes into z, MISFIT and emission). It
  carries the σ of the z it read, and its silences with their causes. K22 later adds its stability. No σ is
  invented here.
- **Silences carry causes:** `out_of_field`, `insufficient_coverage`, `reference_silent`, `below_noise_floor`,
  `series_absent`, `placement_unverified` (from the K07 constraint codes).
- **Provenance:** the series, plane and contrast that produced each reading.
- **No reading is signed.** "For" and "against" belong to the agencies (K14 and K16).

## 4. Contracts

- `LensReading`: `{lens, zone, form: per_acquisition|joint, value, interval, input_sigma, digit (K12 quantizer),
  silence?: cause, source_series_ids, layout_id}`. A per-acquisition reading has exactly one source. A joint
  reading lists all of its sources.
- **The edges** for these metrics are computed here, once the readings exist, as layout v1.1 (K12's rule).
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

Written first: `acceptance/K13.toml`.
- **Behavioural correctness:** SAME; pinned decisions; every reading has a value or a silence with its cause.
- **Representation fidelity:** the intervals contain the phantom truth for planted effusions and edemas (K11) at
  the stated coverage rate.
- **Domain validity (discovery):**
  - the healthy distribution of every lens and form on `checking` normals, per regime, with bounds;
  - the phantom response curves per family, which rise with amplitude.
- **Performance evidence:** places scanned and crops, counted per study per lens, for the reference and for
  Numba; seconds as information.
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
- **2026-10-02, revision 1:**
  - per-acquisition and joint forms, with sources (F03);
  - input σ carried (F45; ARCH §3.3.7);
  - the MCL shell named (F21, F49);
  - edges landing here as v1.1 (F04);
  - work counted (F39).
