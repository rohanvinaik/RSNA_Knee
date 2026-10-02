# K15 — The explanation loop and the kept record

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K15'` |
| **Depends on** | K13 (zone lenses), K14 (contracts) |
| **Consumed by** | K16 (decisions from the kept record), K19–K21 (later readings join the loop), K25 (objects become cases), K18 (kernel) |
| **Commit label / tag** | `knee/K15` · `knee-K15` |

## 1. Purpose and authority

H1's third move for the knee is elimination under law, adapted to MRI by the accord.
- **THESIS §1.4:** each object found is explained, and what is left is read again "until nothing \<object>-shaped
  remains".
- **The accord** (change 4): nested and overlapping objects are allowed; explanation records are reversible; there
  is no numerical subtraction without a contribution law.

## 2. Dependencies and consumers

**Produced** (`knee.run.explain`):
- **Bodies:** contiguous same-sign deviant regions per zone. Specks below the lesion law's minimum extent are
  cleared, and the clearing is recorded.
- **Provisional takes:** a body read by at least one witness, with a lawful signature and shape.
- **Confirmed objects:** provisional takes whose committee outcome is `CONCUR` (K14).
- **Finding decisions** are *not* made here. They are K16's.
- **Explanation records:** reversible masks over the **original** data, `{object_id, footprint, explained_places,
  contribution_model?, nested_in?, overlaps?}`.
- **Post-checks** against the population on the explained region, after masking: `ring` (too little explained),
  `hole` (too much), `lobe` (a second object), `impossible` (a value no tissue gives).
- **The site search** where the residual's composite shows a bounded deviation that no lens claims.
- **Reaching inside** a confirmed object for a nested object of another kind: a line inside edema; lining behind
  an effusion.
- **The last look**, which gives one word per object still standing: part of an explained object, too small, no
  sane shape, no deviation of its own, explained by an instrument censor, or a candidate of its own.
- **The emptied box,** a law check that supports and never establishes. A round guard is reported as a safety,
  never as the stopping rule.
- **The kept record** (K14 v1).

**Consumers:** K16, K19–K21, K25, K18.

## 3. Mechanism

- **No subtraction by default.** An explained region is *masked* for later reads, and its values are kept for any
  reader of the original data.
- **The one lawful contribution model is partial volume.** At a structure's border, along a series' thick axis,
  the voxel mixes tissues in proportions given by the slice profile, from header geometry. There, and only there,
  an object's expected contribution may be removed numerically, with the before and after both kept.
- **Edema is not a halo of a fracture line.** The line is a nested object read inside the edema's footprint on
  the original data.
- **Order is by consumption,** per THESIS §10.3 and KNEE_ARCHITECTURE §5.2:
  1. fluid first (an effusion changes how everything else looks);
  2. then marrow;
  3. then reaching inside.

  Fibrous-structure objects come in K19 and K20.
- Each object records its **route**: first pass, site search, reaching inside, or last look. The route is a
  physical fact (THESIS §5.6).

## 4. Contracts

- Explanation records and the kept record: K14 v1.
- Object IDs are stable: a digest of the study, the round and the footprint.
- An object links to the acquired evidence behind it: series IDs and lens readings.

## 5. Implementation choice

- **Python orchestration;** SciPy `ndimage.label` (C) for components; **Numba** for mask operations and
  post-checks over crops. Each is a reference plus a SAME twin.
- **Prior art:** THESIS §4.4–§4.7 (the cell loop) and KNEE_ARCHITECTURE §4.4. **Decision:** the loop's structure is
  adopted. Its "take" semantics are replaced by explanation records (change 4), and its halo table is reduced to
  the partial-volume model.

## 6. Verification

- **Detective:** each pure decision is converged: speck clearing, the post-check codes, last-look words, route
  codes, nesting admissibility.
- **Hypothesis:**
  - explanation is reversible (unmasking restores the input exactly);
  - masks never overlap without a recorded nesting or overlap link;
  - the loop terminates within its guard on every generated case.
- **Phantoms (K11):**
  - an effusion with and without lining thickening;
  - an edema with and without a line;
  - collections with and without a neck.

  Each must yield the expected objects and nesting, with rings and holes measured.

## 7. Integration

`knee.run.explain.run(study_reading, lens_readings, contracts) -> KeptRecord`.

## 8. Acceptance

- **Behavioural correctness:** reversibility; pinned decisions; termination.
- **Representation fidelity:** the phantoms' planted objects map to confirmed or provisional objects with correct
  nesting; post-check rates are reported.
- **Domain validity:** takes on `checking` normals, recorded by zone (healthy false takes, with bounds).
- **Performance evidence:** rounds per study and milliseconds per round, with the scope stated.
- **Evidence scope:** the lens set of K13; dependence still `unknown` (K14), so confirmed objects stay rare until
  K23.
- **Invalidation:** a change to the lens set, to the contracts, or to the partial-volume model.

## 9. Open matters

- **Facts:** rounds to empty the box on normals and on gold. Expected to be few; measured, never assumed.

## 10. Provenance and status log

- **Sources:**
  - THESIS §1.4, §4.1–§4.8, §5.5–§5.6;
  - KNEE_ARCHITECTURE §4.4;
  - Codex review round 1 (C4);
  - THE_KNEE §2 (change 4).
- **2026-10-02:** specified in K00.
