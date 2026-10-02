# K14 — Society contracts (pure)

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K14'` |
| **Depends on** | K03 (vocabulary, decision words, kept-record v0) |
| **Consumed by** | K15 (commits), K16 (case-free decisions), K17 (emission's inputs), K23 (dependence data plugs in), K25/K26 (recall and censors), K12 (question banks) |
| **Commit label / tag** | `knee/K14` · `knee-K14` |

## 1. Purpose and authority

To fix, as pure and pinned functions, the rules by which the society commits, excludes, splits and decides.
These are fixed early, so the explanation loop and first light integrate against them. The data they consume
(dependence, entitlement, cases) plugs in later.
- **The accord:** per-acquisition witnesses with explicit dependence (change 7); three tiers of negative knowledge
  (change 3); provisional take, confirmed object and finding decision kept distinct (change 10).
- **Codex** (design round 1): "Build pure committee/exclusion contracts early enough for explanation integration".

## 2. Dependencies and consumers

**Produced** (`knee.core.society`, all pure, literal-typed):
- **Witness record:** one per acquired series per question per place: `{series_id, series_class, reading_code:
  for|against|orthogonal|silent, cause?, entitlement: entitled|not_entitled:<reason>|unknown}`.
- **Dependence graph schema:** nodes are series and named shared causes (plane geometry, fat-suppression method,
  short TE, motion, registration, reference cell). Edges are "shares cause X". Plus a status per pair:
  `independent_measured | dependent_measured | unknown`.
- **`committee_outcome(witnesses, dependence) -> CONCUR | SINGLE | DISAGREE | ALL_SILENT`.** Concurrence needs at
  least two entitled witnesses whose pairwise and multiway dependence is *measured* independent. **Unknown
  dependence never yields CONCUR.**
- **Negative knowledge, three tiers:**
  - `impossibility(law) -> veto`: absolute, physical only (P > 0, f ∈ [0, 1], a place outside the body);
  - `observation_exclusion(reading, certificate) -> exclusion`, valid only with a coverage certificate and a
    resolution certificate (the lens could see this there, at this size);
  - `supportive_sign(...) -> support`, which never decides.
- **The four-way split:** `split(constraint_codes, signature, variant_checks, deviation) -> input_error |
  instrument | normal_variant | pathology | undetermined`, in the order constraint → consistency → variant → what
  remains.
- **Decision words:** `PRESENT | ABSENT | DISAGREE | ABSTAIN`, each with its cause. ABSENT requires
  observation-qualified exclusions over the finding's zones, or recalled ABSENT cases. Never a missing positive.
- **The kept-record schema v1:** objects (with stable IDs, nesting links and footprints), readings, witnesses,
  outcomes, decisions, and the provenance of each.

**Consumers:** K15–K17, K23, K25, K26, K12.

## 3. Mechanism

- **The order in which a finding is decided:**
  1. split;
  2. vetoes from impossibility;
  3. committee outcome on the finding's question;
  4. exclusions (observation-qualified only);
  5. the agency's decision word.

  Supportive signs (for example L5 mechanism patterns, or "a fracture lies within edema") enter the record and
  never a decision.
- **Licensed is never excluded.** `observation_exclusion` refuses a reading whose only basis is `licensed`.

## 4. Contracts

- All the functions are total over str, bool, int, list and dict, and return named codes.
- Kept-record v1 is JSONL, with schema version 1.

## 5. Implementation choice

- **Pure Python, fresh.**
- **Prior art:** KNEE_ARCHITECTURE §5.3 (committee outcomes), §5.6 (censors) and §5.9 (the split), and THESIS
  §10.2. **Decision:** adopt the vocabulary, amended by changes 3, 7 and 10. No GenomeVault bar is imported.

## 6. Verification

- **Detective:** every function is converged to a terminal certificate.
- **CrossHair** on the contracts it supports.
- **The authored corpus** (synthetic witness sets with expected outcomes).
- **Hypothesis laws:**
  - DISAGREE never becomes PRESENT;
  - unknown dependence never yields CONCUR;
  - ABSENT never arises from silence or from licensed alone;
  - an impossibility veto is absolute;
  - a supportive sign never changes a decision word.

## 7. Integration

K15 calls `committee_outcome` at every commit. K16 composes the decision order. K23 later fills the dependence
statuses that are `unknown` until then.

## 8. Acceptance

- **Behavioural correctness:** every function `pinned`; the laws hold; the corpus passes.
- **Representation fidelity:** kept-record v1 validates against its schema on the authored records.
- **Domain validity:** reviewed against THE_KNEE §2's changes 3, 7 and 10, recorded in the status log.
- **Performance evidence:** not applicable.
- **Evidence scope:** the pure functions over their input domains.
- **Invalidation:** a change to the vocabulary or to the decision order.

## 9. Open matters

- **Facts:** none. **Policy:** none beyond Q4, which is K17's.

## 10. Provenance and status log

- **Sources:**
  - THESIS §4.4–§4.5, §7.3, §7.5, §10.2;
  - KNEE_ARCHITECTURE §5.1–§5.3, §5.6, §5.9;
  - THE_KNEE §2 (changes 3, 7, 10).
- **2026-10-02:** specified in K00.
