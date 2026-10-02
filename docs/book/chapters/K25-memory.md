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
- **The null mechanism for trust radii,** specified (`provenance/build/revision_1.md`, §F25). An earlier
  cross-study pairing claimed "no shared answer by construction". That was false: two unrelated knees both carry
  effusion at its prevalence.
  - **The hypothesis:** a resemblance is chance when it arises from what each bank says *alone*, without the
    co-occurrence of readings that a case carries. THESIS §7.1: cases are "compared one by one, never summed …,
    since a sum would lose which readings occurred together in each case".
  - **The exchange mechanism.** Within a stratum (zone class × regime × visibility pattern, the set of non-silent
    banks), each bank's row is exchanged at random among the stratum's real objects.
    - It preserves each bank's marginal distribution and the visibility pattern ("set on real data", THESIS §7.4).
    - It breaks the co-occurrence within an object.
    - So a null profile carries no answer by construction, and no label is used.
  - **What chance reach bounds.** The statistic is each null profile's cosine with its *nearest* case, which
    charges the bucket for its size (ARCH §5.5). The radius is the least level at which the chance-reach rate is
    at most a rate written before the run. It is computed on one half of the null draws and checked on the other.
  - **Hard negatives** (opposite answers) are **not** the null. A true normal that reaches a case is a near miss
    (THESIS §7.6): evidence for K26's censors, or a founder's sheet (ARCH l.3785–3786).
  - **Its calibration is measured, never tuned.** The rate at which `null`-role normals reach cases is reported
    beside the exchange's rate. An excess names correlated structure the exchange broke, which belongs in the
    stratum key (Law 5), and it never moves the radius.
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

- **Recall in Python.** Dot products run on the backend K04's R·C² rule admits: BLAS float64 where R·C² < 2^53,
  else int64 or Python int. Level tests use exact integers.
- **Rust (PyO3, maturin)** is admitted only if the measured budget at the memory's real size shows it is needed:
  bit-plane popcount prefilter scans, exact wide-integer tests, GIL-free threads. The decision is recorded here
  with the measurement. If admitted, the Linux x86_64 wheel is built in Docker, inspected with auditwheel, and
  tested in DEPLOY and on Kaggle.
- **Prior art:** legacy `tools/lens_eval2.py` (majority-bundled prototypes). **Decision:** retired as a decision
  path, kept only as a historical instrument (THESIS §7.1 forbids prototypes).

## 6. Verification

- **Detective:** the recall outcome, the bucket keying, the stratum and exchange admissibility, and the provenance
  decisions are converged.
- **Hypothesis:** the exchange preserves every bank's marginal counts within its stratum, and never moves a row
  across strata.
- **Hypothesis stateful tests** of the store: insert, recall, no self-recall, rotation exclusion.
- **SAME** for any native twin: equal outcomes, voices and counts.
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
  - the chance-reach rate on the exchange's checking half, against its bound;
  - the `null`-role normals' reach rate, reported beside it;
  - H3's bridge, reported (recall against shuffled calls);
  - disagreement and abstention rates per finding.
- **Performance evidence:** recalls and coordinates scanned, counted at the memory's real size, for Python and for
  any native twin; bytes scanned; seconds as information.
- **Evidence scope:** the T-panel calls, gold teaching folds and founder sheets at this version.
- **Invalidation:** a change to the layout, to the calls, to the null mechanism, or to the bucket keys.

## 9. Open matters

- **Facts:** whether Rust earns a place, by measurement.
- **Policy:** the chance-reach bound, written before the run.

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
    §7.1, §7.4, §7.6; THE_KNEE §2 change 6);
  - the backend from K04's rule (F16).
