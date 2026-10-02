# K25 — Memory: cases, a stated null, and recall

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K25'` |
| **Depends on** | K04 (arithmetic), K12 (layout; v2 from K20), K14 (contracts), K15 (objects), K06 (calls), K20 (structure readings) |
| **Consumed by** | K26 (agencies with recall, teaching, censors), K18/K27 (the kernel loads the case memory) |
| **Commit label / tag** | `knee/K25` · `knee-K25` |

## 1. Purpose and authority

H3 for the knee: a remembered case routes to the structure's own tools, by resemblance, inside a trust radius
that chance cannot reach.
- **THESIS §7:** "Cases of one answer … are compared one by one, never summed into one bundle per answer".
- **The accord** (change 6): "a trust radius comes from a specified null mechanism (what it preserves, conditioned
  on visibility and context, with bucket size accounted for)". An opposite-answer selected radius is not chance.
- **Codex** (design round 2, D7): cases retain their acquisition source sets and their visibility and dependence
  context. Where these are incomplete, recall preserves that limitation.

## 2. Dependencies and consumers

**Produced** (`knee.build.memory`, `knee.run.recall`):
- **Cases.** Each holds:
  - its **bundle**: the object's or structure's count table in layout v-current, with its footprint;
  - its **call**: ternary digits, per question, from a report call (T panel), gold (in rotation, teaching folds
    only) or the founder's sheet;
  - its **expectation**: the structure's proposed word, and the named difference where the call corrected it;
  - its **context**: regime, zone class, route, exclusion context, tier, acquisition source set, visibility
    certificates and dependence status;
  - its **source**: the sentence verbatim, the gold row, or the founder's words, with study, step and parser
    version.
- **Buckets:** cases of one answer, per agency, question, zone class and regime.
- **The trust radius's null: ARCH's chance population, as the accord amends it** (`provenance/build/revision_2.md`,
  G03). Two earlier nulls are withdrawn:
  - a cross-study pairing, since "two unrelated knees both carry effusion at its prevalence";
  - an exchange of bank rows within strata. It keeps any one informative bank intact, so it does not build
    profiles that cannot carry the answer (Codex, second read). THESIS §7.4 asks for a radius "set on real data".

  The null, in ARCH §5.5's three steps:
  - **The chance population:** "profiles at the same zone class and regime that cannot carry the bucket's answer,
    by construction" (ARCH §5.5). The accord adds "conditioned on visibility and context" (change 6), so the
    population also shares the visibility pattern, the set of non-silent banks.
    - *For a bucket of a finding:* held-out true normals in N's `chance` role, "never reference members". Their
      impurity is stated beside every radius. N is report-derived, so "an unreported lesion makes a 'normal' false"
      (ARCH Table 6.3), at the rate K09's founder sample measures.
    - *For a bucket of "absent":* phantoms planted in true normals (K11), and positive calls localized by a report
      (noisy, and named so). Gold cannot localize (change 8).
  - **The statistic:** "each member's cosine with its *nearest* case in the bucket", which "charges the bucket for
    its size" (ARCH §5.5).
  - **The radius:** the least level at which the members' reach rate, with its count and bound, is at most a rate
    written before the run.
    - ARCH's "the least level no member reaches" is the case of rate zero. Change 6 amends it ("an opposite-answer
      selected radius is not chance"), so one impure member never sets a radius alone.
    - A population too small to bound the rate reads `insufficient` (ARCH §5.5; THESIS §4.8).
    - The radius is a ratio of whole numbers (THESIS §12.2). It is set on one half of the population, and the
      chance-voice rate is read on the other half (ARCH §5.5, *Measured by*).
  - **Members that reach are hard negatives.** They never move the radius. Each goes either to the founder's sheet,
    as a possible unreported lesion (ARCH §5.5, *Fails*), or, once confirmed normal, to K26 as a near-miss candidate
    (change 6; THESIS §7.6: a near miss is "confirmed by a signal independent of the memory").
  - **The rate is the founder's,** written before the run (Law 6, policy). Until it is written, every bucket reads
    `bar_unset` and recall answers nothing. First light records that as its finding.
- **Recall:** `recall(profile, bucket_set, censors) -> one | disagreement | none`, with the voices' counts and
  sources. "One answer standing is recalled; two or more are a disagreement, kept …; none is an abstention"
  (THESIS §10.2).
- **Routed procedures:** a recalled interpretation brings a procedure (KNEE_ARCHITECTURE Table 5.8), never a
  verdict.

**Consumers:** K26, and K18 and K27 (the kernel loads the case memory).

## 3. Mechanism

- **Comparisons use K04's exact level test,** over the question's named banks, masked identically for the dot
  product and both norms.
- **Scan order** may use the packed signs. A case is dropped only on a proved bound.
- **Provenance rules:**
  - a study is never compared with a case from itself;
  - gold teaches only in rotation, and its own folds are excluded when judged;
  - the memory never confirms itself: routed answers become cases only at a teacher's word.

## 4. Contracts

- **Memory artifact:** a cases × coordinates int32 matrix (row-major), int64 norms, uint64 sign planes, case
  metadata as JSONL, and radii per bucket. Competition-derived: `data/memory/` and a private dataset.

## 5. Implementation choice

- **The scan is Rust from the start** (K02b §3.1, §3.6). Its shape is a batched scan over a large, long-lived,
  indexed store, with bit-level work, exact wide integers and GIL-free threads. Founder, 17:22:59Z: "Rust for
  speed".
  - A popcount prefilter runs over the packed sign planes. It drops a case only where an exact bound proves the case
    cannot reach the level (THESIS §12.2; ARCH §3.5.3: packed signs "order scans … and never decide").
  - The survivors get exact integer dot products and norms and K04's level test in u128, with a checked overflow
    that refuses.
  - The scan is cache-blocked over case blocks, and a rayon pool works over the blocks under `allow_threads`.
  - Built with PyO3 and maturin. The Linux x86_64 wheel is built in Docker by the path K01 measures, inspected with
    auditwheel, and tested in DEPLOY and on Kaggle.
- **The reference is Python and NumPy:** dot products on the backend K04's R·C² rule admits (BLAS float64 where
  R·C² < 2^53, else int64 or Python int), and level tests in exact integers. The Rust scan answers to it under SAME
  within each environment.
- **Prior art:** legacy `tools/lens_eval2.py` (majority-bundled prototypes). **Decision:** retired as a decision
  path, kept only as a historical instrument (THESIS §7.1 forbids prototypes).

## 6. Verification

- **Detective:** the recall outcome, the bucket keying, the stratum and exchange admissibility, and the provenance
  decisions are converged.
- **Hypothesis:**
  - the chance population never holds a reference member, a study of a case it is compared with, or a study
    outside its zone class, regime cell or visibility pattern;
  - the radius never falls as the written rate falls;
  - the prefilter never drops a case the exact test would admit.
- **Hypothesis stateful tests** of the store: insert, recall, no self-recall, rotation exclusion.
- **SAME** for the Rust scan within each environment: equal outcomes, voices, counts and prefilter survivors. Its
  Rust side is `cargo clippy -D warnings`, rustfmt and its own unit tests; Hypothesis drives it through the binding.
- **H3's bridge:** recall against shuffled calls, within and across regimes, on G in rotation and on R.

## 7. Integration

The agencies (K26) consult recall after the case-free path. The structure-alone run stays beside every step.
Re-run `just firstlight`.

## 8. Acceptance

Written first: `acceptance/K25.toml`.
- **Behavioural correctness:** the decisions are pinned; the stateful tests pass; no self-recall; first light is
  re-run.
- **Representation fidelity:** the case metadata carries complete context, or flags its incompleteness.
- **Domain validity (discovery):**
  - the chance-voice rate on each population's checking half, against its bound, with N's impurity beside it;
  - the hard negatives per bucket, and where each went (the founder's sheet, or K26);
  - H3's bridge, reported (recall against shuffled calls);
  - disagreement and abstention rates per finding.
- **Performance evidence:** recalls, cases and coordinates scanned, and prefilter survivors, counted at the memory's
  real size for the reference and for the Rust scan; bytes scanned; seconds as information.
- **Evidence scope:** the T-panel calls, gold teaching folds and founder sheets at this version.
- **Invalidation:** a change to the layout, to the calls, to the null mechanism, or to the bucket keys.

## 9. Open matters

- **Facts:** the memory's real size and the scan's counted work (cases, coordinates, bytes), for the reference and
  for Rust.
- **Policy (founder):** the chance-reach rate, written before the run. Until then, `bar_unset`.

## 10. Provenance and status log

- **Sources:**
  - THESIS §7.1–§7.4, §8.4, §10.2;
  - LAA §6;
  - KNEE_ARCHITECTURE §5.5;
  - the Codex review (C8) and design round 2 (D7);
  - THE_KNEE §2 (change 6).
- **2026-10-02:** specified in K00.
- **2026-10-02, revision 1:**
  - the trust radius's null restated as a label-free exchange of bank rows within strata (F25; ARCH §5.5; THESIS
    §7.1, §7.4, §7.6; THE_KNEE §2 change 6). *Withdrawn in revision 2.*
  - the backend from K04's rule (F16).
- **2026-10-02, revision 2:**
  - the null returns to ARCH §5.5's chance population: true normals in the `chance` role, matched for zone class,
    regime and visibility, with the nearest-case statistic and a radius at a written rate. Hard negatives go to the
    founder's sheet or to K26 (G03; ARCH §5.5, THESIS §7.4 and §7.6 read whole; changes 6 and 8);
  - the scan is Rust from the start (C4; K02b §3.6).
