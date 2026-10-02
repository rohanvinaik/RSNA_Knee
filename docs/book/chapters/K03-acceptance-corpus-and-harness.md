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
- **Panels:**
  - **G**: the 58 gold studies, study-level labels only, in deterministic rotation folds.
  - **N**: report-negative candidates. Membership is filled by K06. Roles come from a deterministic partition
    by study-UID digest and declared proportions: `reference`, `null`, `chance`, `host`, `checking`,
    `template_build`, `template_check`.
  - **T**: report-labeled *teaching* studies, the only report-labeled studies that build anything (cases in K25,
    quantizer edges in K12).
  - **R**: report-labeled studies held out of every store, T included, and used only to judge. T and R are
    disjoint, by a deterministic partition of the report-labeled studies.
  - **P**: phantoms (K11).
- **The recognition table:** per object class × role: identified, abstained, wrong. Each count carries an exact
  binomial bound, or reads `insufficient`.
- **The authored acceptance corpus** (`tests/corpus/`, in git): synthetic kept records and decisions, written
  independently of any data, each with its expected table, **expected abstentions included**.
- **The scorer and writer:**
  - `roc_auc` and `macro_auc` (rank-based, ties averaged, with the named `auc_status` codes);
  - the submission writer, with its validator: columns, the ID set, no NaN or inf, range.

**Consumers:** all measuring chapters; K17 and K18 (writer and validator).

## 3. Mechanism

- **The partition** is `role_of(study_digest, proportions) -> role`: a pure, total function with declared
  proportions. It is written down before any run and versioned.
- **Rotation** is `fold_of(study_digest, k) -> int`, likewise.
- **The recognition table** is computed from kept records (K14's schema; its v0 is defined here and extended
  there) against the oracle each role allows: gold at study level; phantom truth; report calls, marked noisy.
- No sum across classes is ever computed.

## 4. Contracts

- Study lists and memberships are competition-derived. They live in `data/panels/` (gitignored) with a manifest
  whose digest is committed.
- The table's schema: `{object_class, role, oracle, identified, abstained, wrong, n, bound_low, bound_high,
  status: measured|insufficient}`.

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
  - the bounds are monotone in n;
  - the partition is stable under re-ordering of input;
  - the fold sizes are balanced within one.
- **The scorer:** SAME against the legacy scorer on toy columns (exact equality), plus §6.1.5 of KNEE_ARCHITECTURE
  (AUC facts 1–3) reproduced on authored columns.
- **The validator, adversarially:** a missing column, an extra ID, NaN, inf, an out-of-range value, a duplicate
  ID, a reordered header.

## 7. Integration

`just accept K03` runs the corpus, the laws and the scorer's SAME. The writer is the only producer of
`submission.csv`.

## 8. Acceptance

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

- **Policy:** the role proportions of the N pool. Proposed: reference 40%, null 15%, chance 15%, host 10%,
  checking 10%, template_build 5%, template_check 5%. The founder may amend before K08 builds templates.

## 10. Provenance and status log

- **Sources:**
  - THE_KNEE §5;
  - KNEE_ARCHITECTURE §6.2.5 (panels) and §6.1.5 (AUC facts);
  - the global `no-popery.md`.
- **2026-10-02:** specified in K00.
