# K27 — The final kernel

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K27'` |
| **Depends on** | K26, K18, and K24 if selected |
| **Consumed by** | the founder's submission decision |
| **Commit label / tag** | `knee/K27` · `knee-K27` |

## 1. Purpose and authority

To run the selected configuration end to end, privately on Kaggle, and to put the expected score before the
founder beside the structure-alone score and the floor of confident joint errors. **Never auto-submit.**
- **THEORY Law 8:** "Build + CV-validate + dry-run the kernel; surface the expected score honestly; submit only on
  the founder's explicit go."
- **`../../CLAUDE.md`'s Kaggle protocol.**

## 2. Dependencies and consumers

**Produced:**
- **The validated selection:**
  - `SELECTION.toml` is checked:
    - whether K24 and K02a are selected and accepted, or their absence recorded explicitly. An unselected
      optional chapter is *skipped*, never run;
    - the emission variant (literal unless the founder has ruled on Q4);
    - the artifact versions;
  - every dependency's acceptance is re-run (`just accept` over the table), *version-aware*. It replays the
    versions the selection names, computes staleness recursively, and reads each chapter's recorded
    behaviour-change diffs against their intent records (`provenance/build/revision_1.md`, §F11).
- **Tier 0** (ARCH §3.2.5, Table 3.2). The zone word may skip quiet zones only once its skip-miss rate, on gold
  finding-bearing zones and on planted phantoms, is near zero (ARCH l.1749–1751: "Tier 0 is switched on only when
  the rate is near zero"). Otherwise it stays off, and that is recorded.
- **The full DEPLOY run** on the local panels.
- **The private Kaggle dry run,** read whole.
- **The expected-score report, stated conditionally** (ARCH §6.1.5), never as one number:
  - per finding: the open shares o₊/n₊ and o₋/n₋, and the decided accuracy with bounds. If every decision is
    right, AUC = 1 − ½·(o₊/n₊)·(o₋/n₋) (fact 1), and fact 3 holds: abstention after a wrong decision never costs;
  - per-finding AUC on G (rotation) and R, with bounds;
  - the structure-alone score beside it;
  - the recognition table;
  - the counted floor of confident joint errors per finding, each named (KNEE_ARCHITECTURE §6.5);
  - the runtime budget against 9 h;
  - the Q4 report if still open.

**Consumer:** the founder.

## 3. Mechanism

K18's kernel, with the full society and the selected variant. Every artifact is attached as a private dataset with
its manifest. Packaged wheels, if K25 admitted native code, are installed offline from the attached dataset.

## 4. Contracts

- `submission.csv` passes K03's validator.
- The report names its evidence scope: the panels and the exercised Kaggle environment.

## 5. Implementation choice

The K18 machinery, unchanged.

## 6. Verification

- Every chapter's acceptance re-runs green at HEAD.
- DEPLOY and VERIFY agree on the local sample: decisions equal, with boundary cases listed (THESIS §12.5: the same
  answer within an environment, never across two).
- The Kaggle dry run reaches `COMPLETE`.

## 7. Integration

The submit step follows `../../CLAUDE.md`: `create_code_competition_submission` through the Kaggle MCP. It is
**only** run on the founder's explicit go, and it uses one of the daily quota.

## 8. Acceptance

Written first: `acceptance/K27.toml`.
- **Behavioural correctness:** all re-run acceptances are green; the selection is validated; the dry run reaches
  `COMPLETE`; **no submission is made without the founder's go.**
- **Representation fidelity:** the report's numbers trace to the recorded runs.
- **Domain validity:** the report is complete, as above.
- **Performance evidence:** the projected runtime for the full test, from the dry run's measured per-study cost.
- **Evidence scope:** the panels and the exercised environment. The hidden test runs only at submission.
- **Invalidation:** any change after the report.

## 9. Open matters

- **Policy:** the submission decision. Q4, if still open.

## 10. Provenance and status log

- **Sources:**
  - THEORY Law 8;
  - `../../CLAUDE.md`;
  - THE_KNEE §5.
- **2026-10-02:** specified in K00.
- **2026-10-02, revision 1:**
  - version-aware replay, with unselected optional chapters skipped (F11, F54);
  - the score stated through ARCH §6.1.5's identities (F54);
  - Tier 0 behind its skip-miss rate (F21; ARCH §3.2.6);
  - DEPLOY against VERIFY within environments (F11).
