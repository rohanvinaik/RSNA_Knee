# K03 — The acceptance corpus, the panels and the harness

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K03'` |
| **Depends on** | K02 |
| **Consumed by** | every measuring chapter (panels, roles, rotation, the recognition table); K05 (vocabulary); K06 (gold); K17 (scorer, writer) |
| **Commit label / tag** | `knee/K03` · `knee-K03` |

## 1. Purpose and authority

To build the judge before the judged: the vocabulary, the measurement panels and their roles, and the
all-questions recognition table, plus an authored corpus of known answers and known abstentions.
- **No Popery** (`AGENTS.md`, Law 2): "a harness asks every question of every object and reports identified /
  abstained / wrong per class of object and role".
- **The accord:** "a small authored acceptance corpus before implementation" (design round 1).
- **Non-goals:** no lens, no decision about a finding.

## 2. Dependencies and consumers

**Produced (`knee.core.vocab`, `knee.orchestrate.harness`, `knee.core.score`):**
- **The vocabulary,** one owner for each:
  - the 12 finding columns, exactly as `sample_submission.csv` and the Evaluation page spell them:
    `ACL, MCL, Medial Meniscus, Lateral Meniscus, Medial OA, Lateral OA, PF OA, Effusion, Synovitis, Baker's,
    Contusion, Fracture`;
  - the official definitions;
  - series classes (plane × contrast family × suppression);
  - tissue words, object classes, roles, decision words and causes. Object classes include lesion-object kinds,
    structures, input error, instrument, variant, unclaimed and overlapping material.
- **Panels.** The training studies are G and the report-labeled rest. The rest is first split, by a deterministic
  partition, into T and R, and N is drawn from T's side only. So R is held out of everything (ARCH Table 6.3:
  "held out of every store"; rule 1, "One role per study per measurement").
  - **G**: the 58 gold studies, study-level labels only, in deterministic rotation folds. No gold study is
    all-negative, so none is in N.
  - **T**: report-labeled *teaching* studies, the only report-labeled studies that build anything: cases in K25,
    and the quantizer edges set once readings exist (K12, K13).
  - **N** ⊂ T: report-negative candidates. Membership is filled by K06, with its coverage per finding: negated,
    or silent (§F41). Roles come from a deterministic partition by study-UID digest and declared proportions:
    `reference`, `null`, `chance`, `host`, `checking`, `hardness_build`, `hardness_check`, `template_build`,
    `template_check`.
  - **R**: report-labeled studies held out of every store: references, templates, quantizers, nulls, maps and
    case memory. They are used only to judge.
    - Only R's triples are read, to replicate a direction (ARCH §6.3). Its objects are never inspected to design
      a change, or R would become development evidence.
    - R's report-negatives serve only as R's own clean negatives.
  - **P**: phantoms (K11), with their stated assumptions.
- **The recognition table:** every question of every object, per object class × role × question: identified,
  abstained, wrong, or `oracle_unavailable`.
  - Each cell names its oracle and the truth it asserts.
  - Each count carries an exact binomial bound over its *independent unit*, the study, never voxels or objects
    within one study, or reads `insufficient`.
- **The authored acceptance corpus** (`tests/corpus/`, in git): synthetic kept records and decisions, written
  independently of any data, each with its expected table, **expected abstentions included**.
- **The scorer and writer:**
  - `roc_auc` and `macro_auc` (rank-based, ties averaged, with the named `auc_status` codes);
  - the submission writer, with its validator: columns, the ID set, no NaN or inf, range.

**Consumers:** all measuring chapters; K17 and K18 (writer and validator).

## 3. Mechanism

- **The partition** is `role_of(study_digest, proportions) -> role`: a pure, total function with declared
  proportions. It is written down before any run and versioned.
- **Rotation** is `fold_of(sorted_digests, k) -> {digest: fold}`. Studies are dealt round-robin over their sorted
  digests, which is deterministic and balanced within one by construction. A hash alone guarantees no balance
  (§F12).
- **The recognition table** is computed from kept records (K14's schema; its v0 is defined here and extended
  there). Each cell's oracle is one of four:
  - `G_study`: gold, study-level only. It never grades where an object is;
  - `report_localized`: a localized report call, marked noisy (K06);
  - `phantom`: truth by construction;
  - `none`, where the cell reads `oracle_unavailable`, never wrong.

  Report silence is `oracle_unavailable` for that question, never a negative. Localization is graded only by
  `phantom` or `report_localized` (ARCH §5.3, l.3417–3419).
- No sum across classes is ever computed.

## 4. Contracts

- **Where the records live.** Panel memberships, role assignments and their manifest digests are derived
  records, and they enter git (AGENTS override 7; founder, 2026-10-02). The pixels and report text never do.
- **The table's schema:** `{object_class, role, question, oracle: G_study|report_localized|phantom|none,
  truth: positive|negative|none, identified, abstained, wrong, oracle_unavailable, n_studies, bound_low,
  bound_high, status: measured|insufficient}`.

## 5. Implementation choice

- **Python, pure.**
- **The scorer reuses `RSNA_Knee/scoring.py`.** It is the best approach: the metric is fixed by the competition,
  the module is pure, it carries 16 intent tests, and Detective pins `auc_status` and `macro_auc`. It is migrated
  into `knee.core.score` (`MIGRATION.md`), re-converged with the local Detective, and the legacy module is
  retired once its ledger row is accepted.

## 6. Verification

- **Detective:** every pure function (partition, fold, table arithmetic, the writer's validator decisions) is
  converged.
- **Hypothesis laws:**
  - each class's counts sum to its n;
  - every bound contains its rate, and no monotone claim is made (§F15);
  - the partition is stable under re-ordering of input;
  - the fold sizes are balanced within one, which holds by construction of the round-robin;
  - no R study holds any building role;
  - N ⊂ T.
- **The scorer:** SAME against the legacy scorer on toy columns (exact equality), plus §6.1.5 of KNEE_ARCHITECTURE
  (AUC facts 1–3) reproduced on authored columns.
- **The validator, adversarially:** a missing column, an extra ID, NaN, inf, an out-of-range value, a duplicate
  ID, a reordered header.

## 7. Integration

`just accept K03` runs the corpus, the laws and the scorer's SAME. The writer is the only producer of
`submission.csv`.

## 8. Acceptance

Written first: `acceptance/K03.toml`.
- **Behavioural correctness:**
  - the authored corpus passes: answers **and abstentions** as expected;
  - the validator rejects every malformed case.
- **Representation fidelity:** the column names equal `sample_submission.csv`'s header, compared as bytes.
- **Domain validity:** the panel definitions are reviewed against `THE_KNEE.md` §5.
- **Performance evidence:** not applicable.
- **Evidence scope:** the authored corpus and toy columns.
- **Invalidation:** a change to the vocabulary, the role proportions, the fold count, or the competition's
  column header.

## 9. Open matters

- **Policy:** the role proportions of the N pool. Proposed:
  - reference 35%;
  - null 10%, chance 10%, host 10%, checking 10%;
  - hardness_build 10%, hardness_check 5%;
  - template_build 5%, template_check 5%.

  The founder may amend them before K08 builds templates. The T : R split of the report-labeled rest is proposed
  at 1 : 1.

## 10. Provenance and status log

- **Sources:**
  - THE_KNEE §5;
  - KNEE_ARCHITECTURE §6.2.5 (panels) and §6.1.5 (AUC facts);
  - the global `no-popery.md`.
- **2026-10-02:** specified in K00.
- **2026-10-02, revision 1:**
  - the oracle contract, `oracle_unavailable` and bounds over studies (F19);
  - R held out of every store, with N ⊂ T and the hardness roles named (F20);
  - round-robin folds (F12);
  - no monotone bound (F15);
  - panel records in git (F33, R2).
