# K12 — The measurement layout, v1

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K12'` |
| **Depends on** | K04 (carrier arithmetic, limits), K10 (the readings to quantize), K03 (vocabulary, teaching roles) |
| **Consumed by** | K13 (lens digits), K20 (layout v2), K22 (the quantizer families perturb these edges), K25 (profiles, recall), K26 (named differences) |
| **Commit label / tag** | `knee/K12` · `knee-K12` |

## 1. Purpose and authority

To fix, before any consumer, how every reading is written in the one language. That means the schema (which
banks, which rows), the edge *rule* and the limits. The edges themselves are computed only once a metric's readings
exist: K13 for the zone lenses, giving layout v1.1; K20 and K21 for theirs, giving v2. A metric cannot be
calibrated before it is computed (`provenance/build/revision_1.md`, §F04; ARCH §3.5.6: "A change of rung is a new
layout version").
- **THESIS §6.2:** "The static middle … is set once … It never moves per movie or per plate, and is never chosen
  to separate confirmed cases."
- **Codex** (design round 2, D6): the measurement layout comes before K12–K16, is extended for the structure
  lenses, and K22 depends on its versioned quantizer.

## 2. Dependencies and consumers

**Produced** (`knee.core.layout`):
- **`Layout v1`:** banks by facet:
  - tissue signature;
  - deviation (licensed, bright 1..m, dark 1..m, per series class);
  - zone-lens values (filled by K13);
  - questions (present, excluded) per agency question. The rows are declared here. They are written later, by
    the agencies (K16), only from concurring readings and observation-qualified exclusions;
  - orientation;
  - coverage (read, per series class, per question);
  - context (zone, regime, route words).
- **The question → banks map:** which banks each question reads, declared here, before any run (ARCH §3.5.4:
  "The banks a question reads are named before the run"). It is a layout fact, so K12 needs no rule from K14.
- **The edge rule:** per metric, a low and a high edge at the **terciles over residual cells of the teaching
  roles** (the N pool's `reference` role and T; never G, never R, never `checking`).
  - The digit is −1 strictly below the low edge, +1 strictly above the high edge, and 0 between (THESIS §6.2).
  - Tied mass at an edge falls in the middle, so the three digits are equal only up to ties. The achieved shares
    are reported.
  - Finer levels exist only where measured as needed.
- **Declared limits** per question, for K04's proofs: the coordinates R in the comparison mask, the count limit C,
  and the level bounds |a|, |b|.
- **`write(readings, layout) -> CountTable`,** with the footprint kept beside it (THESIS §6.5).

**Consumers:** K13, K20, K22, K25, K26.

## 3. Mechanism

**The three zeros are kept apart** (THESIS §6.2–§6.3, §7.3):
- *the middle* is a written row;
- *silence* writes nothing, and is out of the dot product and both norms;
- *orthogonal* writes only the coverage bank's "read" row, never a question row.

Further rules:
- **Questions carry signs; lenses do not.** Question banks are declared here and written by the agencies (K16).
  Lenses write their own value banks, unsigned.
- **Versioning.** Every table carries its layout ID. A comparison across layouts refuses (`layout_mismatch`, K04).
- **Quantizer edges** are versioned with the teaching studies' manifest digest and fixed before the runs they
  serve. Edges computed for a new metric make a new layout version.

## 4. Contracts

- **Layout:** `{id, banks: [{name, rows, facet, metric?}], quantizers: {metric: edges}, limits: {question: {R, C,
  a_max, b_max}}, teaching_manifest_digest}`.
- **Count tables:** K04's contract.

## 5. Implementation choice

- **Pure Python** for the layout and quantizers. **Numba** for the per-place writer (K04's scatter-add).
- **Prior art:** KNEE_ARCHITECTURE Table 3.7 (layout v1, designed) and THESIS §6.1's facets. **Decision:** adopt
  its structure, revised for change 3 (licensed ≠ excluded; question banks written only from observation-qualified
  exclusions) and change 6 (lenses unsigned).

## 6. Verification

- **Detective:** quantizer assignment and the three-zero writing rules are converged.
- **Hypothesis:**
  - the digit rule is strict at both edges, and tied mass at an edge reads 0;
  - the achieved shares are reported, never asserted (§F13);
  - writing is order-invariant;
  - silence never appears in a mask.
- **Provenance:** the edges are computed only from the declared teaching roles. A test injects a G study and
  expects a refusal.
- **Limit proofs:** every question's limits satisfy K04's bound.

## 7. Integration

Every reader writes through `knee.core.layout.write`. K22 perturbs `quantizers` by a fraction of a level.

## 8. Acceptance

Written first: `acceptance/K12.toml`.
- **Behavioural correctness:** the three zeros are pinned; mismatched layouts refuse; the decisions are pinned.
- **Representation fidelity:** decoding a written table recovers the per-row counts exactly (K04).
- **Domain validity (discovery):** each metric's edges (recorded as they land in later layout versions) with their
  achieved shares and teaching provenance.
- **Performance evidence:** places and rows written, counted for Numba and for the reference; seconds as
  information.
- **Evidence scope:** layout v1 and the teaching manifest.
- **Invalidation:** a new metric, a changed teaching manifest, or changed limits. Any of these makes a new layout
  version, never an edit in place.

## 9. Open matters

- **Facts:** whether any metric needs more than three levels (measured on K26's hard pairs: H2's bridge). Whether
  cumulative writing (level L lights rows 1..L) is needed for graded nearness.

## 10. Provenance and status log

- **Sources:**
  - THESIS §6.1–§6.7 and §12.4;
  - KNEE_ARCHITECTURE §3.5;
  - Codex design round 2 (D6);
  - THE_KNEE §2 (changes 3, 6).
- **2026-10-02:** specified in K00.
- **2026-10-02, revision 1:**
  - the schema and the edge rule here, the edges landing as readings exist (F04; ARCH §3.5.4, §3.5.6);
  - the question → banks map declared here (F05);
  - strict edges, with ties falling in the middle (F13; THESIS §6.2).
