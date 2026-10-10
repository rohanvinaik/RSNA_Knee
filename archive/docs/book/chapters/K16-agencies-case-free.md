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
- **Codex** (design round 2, D4): "unknown dependence cannot become concurrence". The fresh read added that a
  single voice cannot either.
- **ARCH Glossary:** "Concurrence. Agreement among independent voices: the only way a lesion-object is committed or
  an answer assigned; refused on disagreement." THESIS §4.4: "never by one tuned pipeline or one voice".

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

**The case-free warrants a decision may rest on.** No answer rests on one voice
(`provenance/build/revision_1.md`, §F23):
- **PRESENT:** a confirmed object (`CONCUR` over K13a's measured independence classes) whose split is `pathology`,
  in the finding's zones.
- **ABSENT:** observation-qualified exclusions that *concur* (ARCH Table 5.5: under CONCUR, "the exclusion
  stands"), covering the finding's zones. Examples: an empty recess at full coverage, read by independent
  acquisitions; fatty marrow at full coverage on the sensitive pathway. ABSENT never comes from silence, from
  `licensed` alone, or from one voice.
- **Otherwise `ABSTAIN`,** with its cause:
  - `single_voice`: a SINGLE take is kept provisional;
  - `dependence_unknown`: an INSUFFICIENT outcome, or `bar_unset`;
  - `no_warrant`;
  - `tier2_blind`;
  - `unverifiable_placement`.

  Or `DISAGREE`, which is kept.
- **The warrants and checks per agency** come from ARCH Table 5.2's "Its check (supports only)" column. Checks
  support and never decide (Table 5.1 rule 3):
  - **fluid:** fluid lies only in recesses and bursae; a Baker's cyst is posteromedial, with its neck; a take
    leaves no ring, and a lobe is a second object;
  - **marrow:** edema lies inside bone; a line reaching cortex inside edema supports Fracture, and edema context
    is a field (THE_KNEE §2 change 3); a contusion belongs to a mechanism pattern or to OA's compartment, or is
    flagged unexplained;
  - **fibrous structures:** a meniscal tear touches a surface on two or more slices; a ligament tear breaks
    continuity or course; one lesion lands in one place on every plane that covers it;
  - **compartments:** OA's signs co-locate in one compartment;
  - **every finding:** each reported finding is explained by a committed object (teaching only); the emptied box.
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
  - no PRESENT or ABSENT from SINGLE or INSUFFICIENT;
  - dependence `unknown`, `insufficient` or `bar_unset` never yields CONCUR-based PRESENT;
  - a supportive check never changes a decision word.
- **The authored corpus:** synthetic kept records, each with its expected words, abstentions included.

## 7. Integration

`knee.run.agency.decide_all(kept_record) -> [DecisionWord]` is consumed by K17.

## 8. Acceptance

Written first: `acceptance/K16.toml`.
- **Behavioural correctness:** the laws hold; the corpus passes; the functions stand pinned.
- **Representation fidelity:** every word traces to its readings and warrants.
- **Domain validity (discovery):** the recognition table (K03) on G in rotation and on N, abstentions included,
  with each abstention's cause counted. The structure-alone table is recorded as **the** baseline. Before the
  founder's bar, it is mostly `dependence_unknown`, and that is its honest finding (R1).
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
- **2026-10-02, revision 1:**
  - no answer from one voice; ABSENT needs concurring exclusions; causes `single_voice` and `dependence_unknown`
    (F23, F46; ARCH Glossary, Table 5.5; THESIS §4.4);
  - the agencies' checks listed from ARCH Table 5.2 (F21).
