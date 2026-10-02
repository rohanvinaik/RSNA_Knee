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
  - A witness is a *per-acquisition* reading, with exactly one source.
  - A joint reading over several series (a tissue word, a joint volume) is never a witness. It is a supportive law
    check carrying its source set (ARCH §2.3 consequence 3; §5.3; `provenance/build/revision_1.md`, §F03).
- **Dependence graph schema:** nodes are series and named shared causes (plane geometry, fat-suppression method,
  short TE, motion, registration, reference cell). Edges are "shares cause X". Each pair has a status, as K13a and
  K23 measure it: `independent_measured | dependent_measured | insufficient | bar_unset | unknown`.
- **`committee_outcome(witnesses, dependence) -> outcome`**, over one finding's question at one place (ARCH Table
  5.5, as change 7 amends it). Dependence is a graph of shared causes, and pairwise dependence is not transitive,
  so no independence classes are formed. Concurrence is a *set*, as ARCH defines it: c₊ and c₋ are "The size of the
  largest set of pairwise-independent acquired series that concur for a finding … or write exclusion marks
  against it" (Glossary). The outcomes are total and exclusive, decided in this order:
  1. **ALL_SILENT:** no witness is entitled (Table 5.5). This is Tier 2, "a question every series is blind to"
     (§5.1, §5.4).
  2. **DISAGREE:** entitled witnesses read both for and against. A dissent is set aside only by entitlement, never
     by dependence: "A majority stands only when its dissenter is set aside so. A tie between entitled voices stays
     a disagreement" (§5.3).
  3. **ALL_ORTHOGONAL:** entitled witnesses read, and none bears for or against. This is not silence: "the place
     was read, and the reading bears neither for nor against the question" (§3.5.3, the third zero). The question
     stays open, with its reads counted. *(A deduction: Table 5.5 has no row for it, and the function must be
     total.)*
  4. **CONCUR:** a set S of at least two entitled witnesses reads one sign, and every pair in S is
     `independent_measured`. The outcome carries the sign and c, the size of the largest such S whose multiway
     status is not `dependent`. That status is measured by K23 (`independent | dependent | unmeasured`; change 7:
     "a graph of shared causes with multiway checks"). A pair is its own multiway check.
  5. **INSUFFICIENT:** two or more entitled witnesses read one sign, and no qualifying S exists, because a pair
     reads `dependent_measured`, `insufficient`, `bar_unset` or `unknown`. Several voices spoke, so this is not
     SINGLE (change 7: "insufficient" where independence is not established).
  6. **SINGLE:** exactly one entitled witness reads a sign ("one class can speak", Table 5.5).

  Only CONCUR commits an object or lets an exclusion stand. SINGLE, INSUFFICIENT and ALL_ORTHOGONAL leave a
  *provisional take*, which is kept and is never an answer (ARCH Glossary, "Concurrence … the only way a
  lesion-object is committed or an answer assigned").
- **Negative knowledge, three tiers:**
  - `impossibility(law) -> veto`: absolute, physical only (P > 0, f ∈ [0, 1], a place outside the body);
  - `observation_exclusion(reading, certificate) -> exclusion`, valid only with a coverage certificate and a
    resolution certificate (the lens could see this there, at this size);
  - `supportive_sign(...) -> support`, which never decides.
- **The four-way split:** `split(constraint_codes, tissue_word, change, variant_checks, deviation,
  population_tightness) -> input_error | instrument | normal_variant | pathology | undetermined`, in the order
  constraint → consistency → variant → what remains (ARCH §5.9).
  - `pathology` is returned only when all four of ARCH Table 5.14's positive conditions are read: a lawful tissue
    word, constraints holding, a deviation where the population is tight, and no variant law explaining it.
  - An object that clears steps 1–3 without all four is `undetermined`, the "unexplained" kept as a finding
    (ARCH Table 1.7).
  - Neither class establishes anything. Both route to recall and the agency, with their causes (Law 4; ARCH
    l.4223: "Only pathology bears on a finding").
- **Decision words:** `PRESENT | ABSENT | DISAGREE | ABSTAIN`, each with its cause. ABSENT requires
  observation-qualified exclusions over the finding's zones, or recalled ABSENT cases. Never a missing positive.
- **The kept-record schema v1:** objects (with stable IDs, nesting links and footprints), readings, witnesses,
  outcomes, decisions, and the provenance of each.

**Consumers:** K15–K17, K13a, K23, K25, K26.

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
- **Totality, by enumeration.** Every committee of up to four witnesses is enumerated: each witness is not
  entitled, or entitled and reading for, against, orthogonal or silent; each pair has one of the five statuses.
  Exactly one outcome must hold for each committee.
- **Hypothesis laws:**
  - an entitled dissent yields DISAGREE, whatever its dependence on the other side;
  - ALL_SILENT arises only when no witness is entitled; an all-orthogonal committee is never ALL_SILENT;
  - c never exceeds the number of entitled witnesses reading that sign, and adding an entitled witness of the same
    sign never lowers it;
  - DISAGREE never becomes PRESENT;
  - unknown, insufficient or bar-unset dependence never yields CONCUR;
  - SINGLE and INSUFFICIENT never yield PRESENT or ABSENT;
  - a joint reading is never counted as a witness;
  - `pathology` never comes without all four positive conditions;
  - ABSENT never arises from silence or from licensed alone;
  - an impossibility veto is absolute;
  - a supportive sign never changes a decision word.

## 7. Integration

K15 calls `committee_outcome` at every commit. K16 composes the decision order. K13a fills the zone questions'
dependence statuses before the loop, and K23 the structure questions'. Until then they read `unknown`, which
gives INSUFFICIENT, never CONCUR.

## 8. Acceptance

Written first: `acceptance/K14.toml`.
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
- **2026-10-02, revision 2:** the committee's outcomes made total and set-based (G05). Grounds, read whole: ARCH
  Table 5.5; §5.3 (only entitlement sets a dissenter aside); the Glossary's c₊ and c₋ (the largest pairwise-
  independent concurring set); §3.5.3 (orthogonal is read, not silent); change 7 (shared causes, multiway checks).
- **2026-10-02, revision 1:**
  - INSUFFICIENT, distinct from SINGLE, with neither ever answering (F46, F23; ARCH Table 5.5, Glossary);
  - per-acquisition witnesses (F03);
  - `pathology` positive and routing only (F26; ARCH §5.9, Table 5.14);
  - the K13a statuses, including `bar_unset` (F06).
