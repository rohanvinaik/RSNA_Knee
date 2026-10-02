# K16 — Agencies, case-free: the structure-alone decision path

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K16'` |
| **Depends on** | K15 (kept record), K14 (contracts) |
| **Consumed by** | K17 (decision words), K18 (first light), K26 (the structure-alone run kept beside every teaching step) |
| **Commit label / tag** | `knee/K16` · `knee-K16` |

## 1. Purpose and authority

To decide each finding, or abstain, from structure alone. No case memory and no teaching are involved yet.
- **THESIS §10.4:** "No agency is admitted by beating the run without it; that run is kept to show what the
  structure does alone."
- **The accord:** a case-free agency decision path exists early (change 10; Codex design round 1).
- **Codex** (design round 2, D4): before dependence is measured (K23), "unknown dependence cannot become
  concurrence". First light's coverage is honestly limited.

## 2. Dependencies and consumers

**Produced** (`knee.run.agency`):
- **Five agencies,** each with its questions:
  - **fluid:** Effusion, Baker's, Synovitis;
  - **marrow:** Contusion, Fracture;
  - **fibrous structures:** ACL, MCL, Medial Meniscus, Lateral Meniscus. Here they abstain until K19 and K20
    supply structure readings;
  - **compartments:** Medial, Lateral and PF OA;
  - **every finding:** in a run, a site search over half-seen places only. It never trims.
- **Placement records:** the constraint readings aggregated per study and zone (K07). They route; they never
  decide pathology.
- **`decide(agency, question, kept_record, contracts) -> DecisionWord`** with its cause and the readings behind it.

**Consumers:** K17, K18, K26.

## 3. Mechanism

**The decision order is K14's:** split, then vetoes, then the committee, then exclusions, then the word.

**The case-free warrants a decision may rest on:**
- **PRESENT:**
  - a confirmed object (`CONCUR`, which needs measured independence and so is rare before K23);
  - or a `SINGLE` provisional take whose own persistence test the law names (a volume beyond the healthy
    interval at every sane value; contact on at least the lawful slice count) **and** whose split is
    `pathology`.

  The cause records `single_witness` either way.
- **ABSENT:** observation-qualified exclusions covering the finding's zones (an empty recess at full coverage;
  fatty marrow at full coverage on the sensitive pathway). Never from silence or from `licensed` alone.
- **Otherwise:** `ABSTAIN` with its cause (`no_warrant`, `dependence_unknown`, `tier2_blind`,
  `unverifiable_placement`) or `DISAGREE`.
- **The fibrous-structures agency** abstains with cause `structure_unread` until K19 and K20.
- **The compartments agency** requires co-located signs from its own lenses (gap, plus the marrow and fluid it
  consumes). Until K20 supplies cartilage and margin it mostly abstains.

## 4. Contracts

- Decision words follow K14.
- Each word carries `{finding, word, cause, readings: [ids], warrants: [codes]}`.

## 5. Implementation choice

- **Pure Python, pinned.**
- **Prior art:** KNEE_ARCHITECTURE §5.2 (agencies) and THESIS §10.1. **Decision:** adopt the questions; the
  case-free warrants are new, under change 10.

## 6. Verification

- **Detective:** every warrant rule and `decide` are converged.
- **Hypothesis laws:**
  - no PRESENT without a warrant;
  - no ABSENT from silence;
  - dependence `unknown` never yields CONCUR-based PRESENT.
- **The authored corpus:** synthetic kept records, each with its expected words, abstentions included.

## 7. Integration

`knee.run.agency.decide_all(kept_record) -> [DecisionWord]` is consumed by K17.

## 8. Acceptance

- **Behavioural correctness:** the laws hold; the corpus passes; the functions stand pinned.
- **Representation fidelity:** every word traces to its readings and warrants.
- **Domain validity:** the recognition table (K03) on G in rotation and on N, abstentions included. The
  structure-alone table is recorded as **the** baseline.
- **Performance evidence:** not applicable.
- **Evidence scope:** the K13 lens set, with dependence unknown.
- **Invalidation:** any new warrant, any lens added, or dependence data (K23). K23 re-runs this chapter's
  acceptance through first light.

## 9. Open matters

- **Facts:** how much the structure alone decides (the baseline). It is a finding, never a target.

## 10. Provenance and status log

- **Sources:**
  - THESIS §10.1–§10.5;
  - KNEE_ARCHITECTURE §5.2;
  - Codex design round 2 (D4);
  - THE_KNEE §1 step 11 and §5.
- **2026-10-02:** specified in K00.
