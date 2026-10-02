# K17 — Emission

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K17'` |
| **Depends on** | K16 (decision words), K03 (scorer, writer, validator) |
| **Consumed by** | K18 (the kernel writes `submission.csv`), K27 |
| **Commit label / tag** | `knee/K17` · `knee-K17` |

## 1. Purpose and authority

To project the decision words and their readings onto the twelve ranked columns that macro-AUC reads.
- **THEORY Law 7:** "where the evidence is open, abstain (→ 0.5)".
- **The accord:** the literal 0.5 is the submitted default. Ordered variants are computed and **reported** for the
  founder (Q4). Witness-set comparability replaces a raw series count (change 9).
- **Q4 is the founder's:** "whether unresolved findings remain exactly 0.5 or receive an explicitly authorized
  evidence ordering" (Codex design round 2).

## 2. Dependencies and consumers

**Produced** (`knee.run.emit`, pure):
- **`register(word) -> upper | middle | middle_fixed | lower`.**
  - `middle_fixed` is Tier 2 and unverifiable cases: exactly 0.5 in every variant.
- **The literal variant**, the default:
  - upper and lower are ordered by keys of *comparable* evidence;
  - the middle sits at exactly 0.5.
- **Ordered variants**, *reported only*: the middle ordered by finding-specific partial evidence (the lean digit
  over comparable witness sets; the L5 digit). Ties stand.
- **`witness_comparability(study_inventory, question) -> key`.** Concurrence is normalized to what that study's
  inventory could have offered for the question, so ranks do not reflect protocol richness. This is a measured
  definition, recorded in its chapter run.
- **The Q4 report:** for each finding, AUC under both variants on G (rotation) and R, the stake
  (o₊·o₋)/(n₊·n₋)·(A_mid − ½) (KNEE_ARCHITECTURE §6.1.5, fact 2), and its bound.

**Consumers:** K18, K27.

## 3. Mechanism

- **Registers:** decided present (0.55, 1); open (0.5, or (0.45, 0.55) in an ordered variant); decided absent
  (0, 0.45).
- **Within a register,** a fixed key sequence, each key compared only with itself. A strictly increasing map turns
  ranks into values.
- **No weighted sum.** No header word is an input (a contract test checks this).
- **The σ guard:** a decision resting on an under-determined reading drops to the middle and is flagged.

## 4. Contracts

- Inputs: decision words and named readings.
- Outputs: twelve floats per study, written only through K03's writer and passing its validator.

## 5. Implementation choice

- **Pure Python, pinned.**
- **Prior art:** KNEE_ARCHITECTURE §6.1. **Decision:** adopt the registers and the AUC facts; replace c₊ with
  witness comparability; the literal middle is the default.

## 6. Verification

- **Detective:** `register`, the key functions, the map and `witness_comparability` are converged.
- **Hypothesis:**
  - the map is strictly increasing within registers;
  - ties stay ties;
  - no header field affects output.
- **AUC facts 1–3** are reproduced on authored toy columns.

## 7. Integration

`knee.run.emit.columns(words, readings, variant="literal")` feeds the writer. The variant is a recorded
configuration in `docs/book/SELECTION.toml`, which defaults to literal.

## 8. Acceptance

- **Behavioural correctness:** the laws hold; the functions stand pinned; the validator passes on the generated
  files.
- **Representation fidelity:** the submitted variant is the selected one (literal unless the founder rules).
- **Domain validity:** the Q4 report is produced for the founder, with bounds.
- **Performance evidence:** not applicable.
- **Evidence scope:** the decision words of K16. It is re-run when the society grows (K26).
- **Invalidation:** a change to the decision vocabulary, the keys, the comparability definition, or the selected
  variant.

## 9. Open matters

- **Policy (Q4):** the founder's ruling on the open register. Until then, literal.

## 10. Provenance and status log

- **Sources:**
  - THEORY Law 7;
  - KNEE_ARCHITECTURE §6.1;
  - the review accord (change 9);
  - Codex design round 2.
- **2026-10-02:** specified in K00.
