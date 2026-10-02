# K15 — The explanation loop and the kept record

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K15'` |
| **Depends on** | K13a (the pairs' dependence statuses, entitlement, the hardness map), K13 (zone lenses), K14 (contracts) |
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
- **Provisional takes:** a body read by at least one witness, with a lawful tissue word and shape. A take whose
  outcome is SINGLE or INSUFFICIENT stays provisional, kept with its cause, and is read again next round (THESIS
  §4.5).
- **Confirmed objects:** provisional takes whose committee outcome is `CONCUR` over K13a's measured independence
  classes. "Commit by gated concurrence" is ARCH §6.6.3's Phase 7, and it follows the gate.
- **Finding decisions** are *not* made here. They are K16's.
- **Explanation records:** reversible masks over the **original** data, `{object_id, footprint, explained_places,
  contribution_model?, nested_in?, overlaps?}`.
- **Post-checks**, by mode (ARCH §4.4 l.2850–2865; THE_KNEE §2 change 4):
  - **mask mode** (the default; nothing inside the footprint changes):
    - `ring`: a same-sign deviation hugging the mask's border outside the footprint and halo;
    - `lobe`: a same-sign residual with its own centre, joined to the mask;
    - `hole` and `impossible` are recorded `not_applicable:mask`. Neither can form without a subtraction.
  - **contribution mode** (only under a stated contribution law): all four, as ARCH writes them. `hole` is an
    opposite-sign deviation inside the footprint after the modelled contribution is removed; `impossible` is a
    value no tissue gives.
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
- **The one lawful contribution model is partial volume** (ARCH Table 4.6's halos). At a border, along a series'
  thick axis, the voxel mixes tissues in proportions given by the slice profile.
  - The headers give SliceThickness and SpacingBetweenSlices, not the profile's shape (ARCH §2.4). So the profile
    is a declared assumption, a rectangle of width SliceThickness, and its sensitivity is measured on K11's
    phantoms.
  - There, and only there, an object's expected contribution may be removed numerically, with the before and
    after both kept.
  - Where SpacingBetweenSlices ≠ SliceThickness, the halo takes ARCH's bound, "no wider than the slice profile
    through-plane" (l.2915–2916), and nothing is subtracted.
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

- **Detective:** each pure decision is converged: speck clearing, the post-check codes per mode, last-look words,
  route codes, nesting admissibility.
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

Written first: `acceptance/K15.toml`.
- **Behavioural correctness:** reversibility; pinned decisions; termination; no confirmation without CONCUR.
- **Representation fidelity:** the phantoms' planted objects map to confirmed or provisional objects with correct
  nesting; post-check rates are reported.
- **Domain validity (discovery):**
  - takes on `checking` normals, recorded by zone (healthy false takes, with bounds);
  - the shares of provisional and confirmed objects;
  - post-check rates per mode on phantoms.
- **Performance evidence:** rounds per study, and places re-read per round, counted; seconds as information.
- **Evidence scope:** the lens set of K13 and K13a's gate. Until the founder writes the bar (ARCH §6.7 item 8),
  every pair reads `bar_unset` and nothing is confirmed. That is a finding, recorded, never routed around.
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
- **2026-10-02, revision 1:**
  - confirmation follows K13a's gate (F06; ARCH §6.6.3);
  - post-checks by mode, with hole and impossible only under a contribution law (F18; ARCH §4.4; THESIS §4.5);
  - the slice profile as a declared assumption (F18; ARCH §2.4).
