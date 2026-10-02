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
- **The key sequence, declared here in full** (ARCH Table 6.1): witness comparability (in c₊'s place, change 9),
  then the s-digit, then H. Keys whose chapters are not yet accepted (H from K21, s from K22) read
  `key_unavailable:<name>` and are skipped: "Until then the sequence skips it" (ARCH §6.1.4, l.4406). They are
  never filled with a default.
- **Each key is compared only with itself across studies** (ARCH §6.1.4, l.4388). A study whose key is silent
  takes its tie group's mean rank at that key, so silence neither raises nor lowers it.
- **The s-digit's place.** ARCH's structural argument puts stability second (l.4427–4430): "independent series are
  different evidence; stability is the same evidence surviving a step either way; H is one statistic of one
  reading". s is read against phantoms of its own size and zone (ARCH l.2779–2781).
  - ARCH also admits s only if it "orders planted phantoms above true normals" (l.4403–4406). That is admission
    by discrimination on one query, which the No Popery law forbids. So the test is *reported* and never gates,
    and the conflict is put to the founder (`provenance/build/revision_1.md`, §F24).
- **The literal variant**, the default:
  - upper and lower are ordered by the key sequence;
  - the middle sits at exactly 0.5.
- **Ordered variants**, *reported only*: the middle ordered by finding-specific partial evidence (the lean digit
  over comparable witness sets; the L5 digit). Ties stand.
- **`witness_comparability(study_inventory, question) -> key`.** Concurrence counts only K13a's
  `independent_measured` classes, normalized to what that study's inventory could have offered for the question,
  so ranks do not reflect protocol richness. This is a measured definition, recorded in its chapter run.
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
  - no header field affects output;
  - an unavailable key changes no order;
  - a silent key leaves its study at its tie group's mean rank.
- **AUC facts 1–3** are reproduced on authored toy columns.

## 7. Integration

`knee.run.emit.columns(words, readings, variant="literal")` feeds the writer. The variant is a recorded
configuration in `docs/book/SELECTION.toml`, which defaults to literal.

## 8. Acceptance

Written first: `acceptance/K17.toml`.
- **Behavioural correctness:** the laws hold; the functions stand pinned; the validator passes on the generated
  files.
- **Representation fidelity:** the submitted variant is the selected one (literal unless the founder rules).
- **Domain validity (discovery):**
  - the Q4 report is produced for the founder, with bounds;
  - when K22 lands, the s-key report: whether s orders P above N where the keys above it tie, and whether s is a
    function of |z|. Both are reported, never gating.
- **Performance evidence:** not applicable.
- **Evidence scope:** the decision words of K16. It is re-run when the society grows (K26).
- **Invalidation:** a change to the decision vocabulary, the keys, the comparability definition, or the selected
  variant.

## 9. Open matters

- **Policy (Q4):** the founder's ruling on the open register. Until then, literal.
- **Policy (the s key):** ARCH §6.1.4's admission test conflicts with the No Popery law. The book follows the law
  and puts the conflict to the founder.

## 10. Provenance and status log

- **Sources:**
  - THEORY Law 7;
  - KNEE_ARCHITECTURE §6.1;
  - the review accord (change 9);
  - Codex design round 2.
- **2026-10-02:** specified in K00.
- **2026-10-02, revision 1:**
  - every key declared early, unavailable keys skipped (F08; ARCH l.4406);
  - like with like, with silence taking the tie group's mean rank (F47; ARCH l.4388);
  - the s key placed by ARCH's structure, its discrimination test reported only (F24);
  - c₊ counts only measured-independent classes (F06).
