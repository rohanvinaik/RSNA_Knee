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
  - `SELECTION.toml` is checked: whether K24 is selected and accepted, or its absence recorded; the emission
    variant (literal unless the founder has ruled on Q4); the artifact versions;
  - every dependency's acceptance re-run (`just accept` for K01–K26) to detect staleness.
- **The full DEPLOY run** on the local panels.
- **The private Kaggle dry run,** read whole.
- **The expected-score report:**
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
- DEPLOY and VERIFY are SAME on the local sample.
- The Kaggle dry run reaches `COMPLETE`.

## 7. Integration

The submit step follows `../../CLAUDE.md`: `create_code_competition_submission` through the Kaggle MCP. It is
**only** run on the founder's explicit go, and it uses one of the daily quota.

## 8. Acceptance

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
