# K26 — Teaching, and the agencies with recall

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K26'` |
| **Depends on** | K25 (memory), K23 (hardness, dependence, entitlement), K06 (calls, softness) |
| **Consumed by** | K17 (re-run with the full society), K27 |
| **Commit label / tag** | `knee/K26` · `knee-K26` |

## 1. Purpose and authority

H4 for the knee: each agency learns only the residue, from its own clean signal, in its own curriculum, and is
judged by the course of its learning.
- **THESIS §10.3–§10.4:** "Turning a wrong answer into an abstention is progress." "No agency is admitted by
  beating the run without it."
- **The accord:** reports teach, gold establishes, the founder's eye takes the hard sheets; authority matches the
  question's spatial scope (change 8); censors are written from named differences, never from error rates (Codex
  review round 2).

## 2. Dependencies and consumers

**Produced** (`knee.orchestrate.teach`, train-only; `knee.run.agency`, extended):
- **Successor resolution.** A call (zone, finding) attaches to the object or structure reading that holds the
  zone's evidence *by its anatomical and descriptive constraints*. An ambiguous successor stays `unresolved` and
  goes to the founder's sheet. It is never attached by "most deviant mass" alone.
- **Curricula,** one per agency in consumption order: fluid; then marrow and fibrous structures; then
  compartments; then every finding. The certain cases come first (report and gold agree, low softness), then the
  hard sheets.
- **Hard sheets for the founder.** Each tile shows the zone in every entitled series, the residual, the report
  sentence verbatim, the proposed word, the nearest cases on both sides, the exclusion context and the hardness
  status. His calls stand beside the report's, never over it.
- **Near-miss censors.** A confirmed failure of an agency's answer, by its own oracle, is read against the K-line
  that answered, and its **named difference** (K04's decode: bank, row, Δcount) is decided against chance. The
  outcome is a censor of the failed answer, a split K-line, or nothing (the failures wait).
- **The noisy-oracle rule:** censors on soft findings need gold or the founder. A refusal teaches nothing.
- **Agencies with recall:** the case-free path first (K16), then recall (K25), then censors, then the decision
  word (K14's order).
- **Trajectories:** after each teaching step, per agency and finding, on G (in rotation, untaught folds) and R:
  identified, abstained and wrong, with bounds; the bank-by-bank tally of new named differences; the
  structure-alone run beside it. One end-to-end macro-AUC is recorded per step and **chooses nothing**.
- **H2's bridge** on the hard pairs (KNEE_ARCHITECTURE Table 6.2): kept, kept by a confound, or lost.

**Consumers:** K17 (re-run), K27.

## 3. Mechanism

- **A step of teaching** is one batch of T-panel calls entered as cases, or one founder sheet. Agencies are taught
  apart, never from one pooled set.
- **"Accepted by the report"** (the every-finding agency in teaching) adds and never trims: nothing committed is
  removed to match a report.
- **A plateau** is put to the founder: accept, teach further, or build the missing structure.

## 4. Contracts

- **Trajectory record:** `{agency, step, finding, identified, abstained, wrong, n, bounds, new_differences_by_bank,
  structure_alone_triple}`.
- **Censors:** `{answer_vetoed, key_bundle_case_ids, named_difference, radius, source_failures: [ids], decided:
  censor|split|wait}`.

## 5. Implementation choice

- **Python, pure decisions pinned.** Sheets are rendered with matplotlib (dev-only) into `data/sheets/`, since they
  contain competition pixels.
- **Prior art:** THESIS §8 and §10 and KNEE_ARCHITECTURE §5.6–§5.7. **Decision:** adopted under changes 6–8.

## 6. Verification

- **Detective:** successor resolution, censor decision and trajectory arithmetic are converged.
- **Hypothesis:** no case confirms itself; rotation exclusion holds; a censor never vetoes outside its radius.
- **An audit of every case's source** (falsifier 2).

## 7. Integration

The agencies' decision words feed K17 again. Re-run `just firstlight`. The structure-alone triple stays beside
every step.

## 8. Acceptance

- **Behavioural correctness:** the decisions are pinned; the audit is clean; first light is re-run.
- **Representation fidelity:** every case and censor traces to its source.
- **Domain validity:**
  - trajectories per agency show wrong answers falling faster than abstentions rise (falsifier 5), or the plateau
    is put to the founder;
  - H2's bridge results per hard pair;
  - the softness table consulted for every censor.
- **Performance evidence:** cost per study as teaching proceeds (falsifier 6: full analyses should grow fewer).
- **Evidence scope:** the teaching steps taken, and their oracles.
- **Invalidation:** any new teaching step (each is a recorded revision), and any change to K25 or K23.

## 9. Open matters

- **Policy (Q5):** the split of the founder's hours across sheets. His calls are never overwritten.
- **Facts:** whether learning settles (falsifier 5) per agency.

## 10. Provenance and status log

- **Sources:**
  - THESIS §7.5–§7.6, §8, §10;
  - KNEE_ARCHITECTURE §5.5–§5.7, §6.2.1, §6.3;
  - the Codex review rounds 2–3;
  - THE_KNEE §2 (changes 6, 8).
- **2026-10-02:** specified in K00.
