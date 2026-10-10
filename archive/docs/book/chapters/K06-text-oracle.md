# K06 — The text oracle: localized ternary calls from the reports

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K06'` |
| **Depends on** | K03 (vocabulary, gold, panels) |
| **Consumed by** | K08 and K09 (report-negative candidates), K25 and K26 (calls as teaching), K23 (softness for dependence against reports), K17 (the Q4 report) |
| **Commit label / tag** | `knee/K06` · `knee-K06` |

## 1. Purpose and authority

To read each training report into calls: ternary, localized where the words allow, and carrying their source
sentence.
- **THEORY II.7:** the report parser is a train-only label oracle.
- **The accord:** reports teach and gold establishes; gold is study-level; ambiguous successors stay unresolved;
  the pool is "report-negative candidates" (THE_KNEE §2, change 8).
- **Non-goals:** nothing at test time depends on this chapter; no image reading.

## 2. Dependencies and consumers

**Produced (`knee.orchestrate.text`; train-only, unreachable from the kernel by contract):**
- **`calls(report) -> [Call]`.** Each call carries:
  - a finding;
  - a digit: +1 asserted, −1 negated, or absent, plus a hedge state ("possible", "cannot exclude",
    "suspicious for" give an abstention);
  - location words mapped to vocabulary zones where possible (horn, body, root; medial or lateral; condyle,
    plateau, patella, trochlea; the recesses; ligament segments);
  - morphology (tear planes) and size words (trace, small, moderate, large);
  - the source sentence verbatim, its language, and the parser version.
- **`report_negative(report) -> code`**, one of `negative | positive | no_terms | hedged_only`. Only `negative`
  enters the N pool, and only from T's side (K03).
- **`coverage(report, finding) -> negated | normal_stated | silent`**, per finding. A report-negative is `absent`
  for a finding only where its report negates the finding or states the structure normal. Elsewhere it is
  `silent`, and serves only as a no-mention normal (ARCH Table 5.12: true normals "establish "absent" only as far
  as their reports do"; l.3948: "an unmentioned effusion is no evidence").
- **The softness table:** per finding, report against gold, splitting **parser misses** (the report says it; the
  parser did not read it) from **report–gold disagreements** (the original read and the expert re-read differ).
  Each comes with a rate, a direction and a bound.
  - The split is adjudicated by a reader of the hit sentence (ARCH l.3974–3983, "told apart by reading the hit
    sentence"): the lead, and the founder for soft findings.
  - It is never adjudicated by the parser itself, whose rules gold shaped.
- **L5 co-occurrence** in text: mechanism patterns as found in the reports.
- **The Q3 residue:** how reports word OA marrow lesions against bruises, and how Baker's size is described.

**Consumers:** K08, K09, K23, K25, K26.

## 3. Mechanism

- The existing parser's design is kept: language detection, multilingual term lists, sentence-scoped negation
  windows, conjunction rules, the smallness and reactive-edema rules.
- Its 1/0 collapse is replaced by three states plus hedges.
- Locations are extracted at the sentence scope that negation already uses.
- A call names a zone, never an object. Its successor (an object) is resolved later (K26). An ambiguous successor
  stays unresolved, never guessed.

## 4. Contracts

- `Call`: `{study_id, finding, digit: +1|-1|0, hedge: none|possible|exclude_not|suspicious, zone?, morphology?,
  size?, sentence, language, parser_version}`.
- `Coverage`: `{study_id, finding, coverage: negated|normal_stated|silent}`.
- **Where they live.** Calls and their verbatim sentences are report text, so they stay in `data/text/`, never
  in git. The pool memberships, the coverage codes and the softness table are derived records, and they may
  enter git (AGENTS override 7).
- The authored test sentences are synthetic and written independently: they go in git.

## 5. Implementation choice

- **Python (regular expressions and lexicons).** The NLP is deterministic.
- **Prior art: legacy `RSNA_Knee/report_parser.py`** scores 77.7% against gold and was grown from gold's
  disagreements (`tools/parser_validate.py`).
  - **Decision: reuse it as the base.** The multilingual, error-driven lexicon is unique work, and rewriting it
    would discard measured learning. It moves into `knee.orchestrate.text` with re-convergence.
  - **Recorded dependence:** gold shaped its rules (the "gold gate 2026-08-29" conjunction rule; "gold excludes
    trace/minimal effusions"). So gold is **not** untouched evidence for parser-derived claims. Those are checked
    on R and on the founder's sheets instead.
- **GSE** (`~/Projects/gse`, the house semantic parser) is noted as prior art for later semantic parsing. It is
  not adopted here without a measured case: its coverage of a dozen languages is unknown.

## 6. Verification

- **SAME:** the migrated parser equals the legacy parser on every report where its behaviour is unchanged.
- **Intent tests:** authored multilingual synthetic sentences for each state, hedge, location, size and
  morphology.
- **Detective:** each pure decision (negation window, hedge, location mapping, `report_negative`, `coverage`) is
  converged.
- **The softness table** carries counts and bounds. A parser miss is never counted as softness.

## 7. Integration

`just text` builds calls, pools and the softness table into `data/text/<version>/`. K08 and K09 read the pool by
manifest.

## 8. Acceptance

Written first: `acceptance/K06.toml`.
- **Behavioural correctness:**
  - the SAME against legacy holds;
  - the authored corpus passes, with hedges giving abstentions;
  - the decisions stand pinned.
- **Representation fidelity:** each call's sentence is a verbatim substring of its report.
- **Domain validity:**
  - per-finding agreement with gold is reported descriptively, with bounds and the gold-dependence label;
  - the softness table is complete;
  - the size and composition of the N pool are recorded, with its coverage per finding;
  - the adjudication log of parser misses against report–gold disagreements is kept.
- **Performance evidence:** reports processed, counted; seconds as information.
- **Evidence scope:** the training reports at the parser version.
- **Invalidation:** a lexicon or rule change, or new reports.

## 9. Open matters

- **Facts:**
  - the Q3 residue in the reports' language;
  - the size of the N pool by regime (K09 needs enough per cell).
- **Policy:** whether the founder wants GSE trialled for any language the lexicon handles poorly.

## 10. Provenance and status log

- **Sources:**
  - THEORY II.7;
  - KNEE_ARCHITECTURE §5.7;
  - `RSNA_Knee/report_parser.py` and `tools/parser_validate.py` (prior art);
  - THE_KNEE §2 (change 8).
- **2026-10-02:** specified in K00.
- **2026-10-02, revision 1** (F41): coverage per finding for the N pool; parser errors adjudicated by a reader of
  the sentence, never the parser; N drawn from T only (F20); derived records in git, report text never (R2).
