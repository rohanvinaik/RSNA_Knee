# Final design for the diagnostic layer and the competition run (2026-10-21)

Governing words: `docs/conversations/2026-10-21-ternary-buckets-and-squint-orchestration.md` (both of Rohan's messages),
the thesis conversations, *What an <Object> Is* (§§1.3, 1.11–1.12, 1.14, 7, 8, 9, 11, 12.2–12.4, 13.6, 14) and
SIGNIFICANCE_WEIGHTING (§§1–7, 10–14). Second readings: Codex, three turns (`codex/answer*.out`), and a relayed agent
review (`relayed-agent-review-20261021.md`). On Rohan's go this replaces the superseded parts of
`docs/AI_DIAGNOSTIC_DESIGN.md` (numeric reference bindings; question-composite teaching; the full-reconstruction raw
route as the inference path).

## What runs where

- Bootstrap, done: the high-resolution pipeline's products for the 58 labelled studies (58 reader-verified H5
  products). Their remaining job is to supply the buckets.
- Kaggle scaling notebooks (all training data is mounted there): the bootstrapped squint-and-recall over training
  studies, with report calls, to grow the buckets.
- Kaggle competition notebook: squint and recall only. The high-resolution tools run there only as a rare, bounded zoom.

## 1. Representation, as built

Every reading is balanced ternary with its polarity from the scan's own data: dark, bright, or the measured third,
"not significant on this measure". An unread bank is silence, a different fact (§7.3). One object, one profile across
its lenses, views, directions and scales. Each stored case keeps two profiles of the same support: the full one from the
bootstrap and the squint one read from the raw scan, the calibration pair (§7.4, §12.3). The portable memory retains the exact full sparse object record and its required interpretation context; the full reader works without the source H5 and remains lazy during cheap inference. No statistical middle is added.

## 2. The buckets

For each of the 58 studies and each condition, by the SOP's object–condition mapping (anatomy and medical practice;
OBJECTS_AND_CONDITIONS §5):
- the condition's implicated objects are that condition's presentation when its label is 1;
- an object that no positive label implicates is a normal case for the conditions that implicate it (normal for those,
  never "healthy in every respect");
- a blank label gives no call.
Cases stay individual (§8.1). The buckets are precedents for recall, never a reference band for the encoding.

## 3. One study in production

1. Read every series once, many files at a time, and squint every slice (10 mm tiles).
2. Locate objects: the bones first, then their neighbours through the anatomical relations. Candidate windows are
   scored by the cosine of the stored squint presentations against the study's squint vector (§11.1, §12.2).
   Resemblance proposes a location; anatomy and exclusion constrain it. Nothing is carried from another patient.
3. Recall each object's state: cosine against that object's normal and presentation cases over the condition's
   readings. A case speaks only above chance resemblance (the trust radius, §8.4, set on real data before the run it
   judges); near-miss censors veto their own answer (§8.5); competing answers stay a disagreement, never a nearest-case
   win (§11.2). Distinct coexisting conditions are not competing answers.
4. Combine per condition by its written contract (§1.11), drawn from anatomy and medical practice and fixed before any
   run. Each contract states: the condition, its anatomical scope and its alternative presentations; which findings are
   necessary, which combinations are sufficient, which only support; which reading may exclude or assign, and why; what
   counts as an observed negative, unknown, unmeasured or a disagreement; how shared-source evidence counts once; and,
   for each question it can leave open, the one extra look that could settle it. "Necessary" means a necessary finding
   or configuration, not that every constituent tissue must look damaged.
   - An observed clean normal on a necessary finding defeats the condition whatever the other parts say: SnNout, and
     Kleene's strong conjunction, "false whatever its unknown part" (§1.11–1.12; SIGNIFICANCE_WEIGHTING §4 as the
     elimination guide). Silence is never such a negative.
   - Supporting evidence never overrides a defeat.
   - The standing to defeat or assign comes from the contract's domain warrant, never from how cleanly remembered cases
     happened to separate.
   A warranted independently diagnosed whole-condition configuration may itself decide when no necessary anatomical finding contradicts it (Rohan: “Let warranted configuration recall decide”). Clean necessary negatives retain their force; opposing warranted descriptions remain a disagreement. The configuration preserves object-qualified banks and independent label attribution.
5. Value per condition, by one fixed, written mapping from the evidence: defeated below open, open below assigned, and
   within each band ordered by the cosine evidence itself. No hard 0 or 1, no averaging that lets partial matches erase
   a clean negative, no artificial tie-breaking. The score ranks studies within each condition, so only that ordering
   matters. The categorical finding and its evidence are kept beside the submitted value.
6. Zoom: only for a question still open whose contract names a bounded, higher-fidelity look at one region in one view,
   and only within the time budget. Recall then runs again.
7. Nothing is taught at run time (§13.6).

## 4. Growing the corpus

Steps 1–3 run over the training studies on Kaggle. The lead and sub-agents read each report into ternary calls per
condition: stated present +1; stated absent or normal −1, only for what the report actually declares; unmentioned or
equivocal, no call. The sentence is kept verbatim, with its anatomical attribution, negation, uncertainty and scope.
Unclear readings go to Rohan and the lead. A proposal may organise that review; it never supplies a missing assertion.

A located object becomes a case only with its report call, under the SOP mapping that ties the condition to that object.
The memory's own answers stay findings under their own source and can never enter the teaching store; duplicate sources
count once; conflicting calls stand side by side; abstentions create neither cases nor censors (§1.14, §9.4, §11.3;
SIGNIFICANCE_WEIGHTING §14). Each round enlarges the buckets. The memory is judged by identified, abstained and wrong per
condition on studies it was not taught on, with no same-study leakage (§11.4).

## 5. Kaggle notebook

The verified offline wheels (CPython 3.13, python-gdcm and the locked closure), code copied to local disk, concurrent
reads, four study workers, memory loaded once, a time guard that leaves open questions open, values written as studies
finish, a private dry run on the public studies, and a submission only on Rohan's word.

## 6. Measured basis (recorded)

Squint 0.17–0.68 s and reads 0.14–0.40 s per study locally, five labelled studies (`squint-timing/`); Kaggle CPU
2.2–2.9× slower per core; exact sparse cosine 3.3 ms per query against 2,000 synthetic cases on Kaggle; the full pipeline
about 113 CPU-seconds per study on Kaggle, bootstrap only (`../kaggle-hardware-20261021/`). These are stage measurements, not whole squint-first inference costs. The current packet links source-pinned integrated runs and their resources; neither these stage costs nor a valid CSV alone establishes hidden-scale capacity.

## 7. Build lanes (parallel; one integrator)

1. Bucket compiler (object-level teaching by the SOP mapping).
2. Shared squint-profile writer, with the calibration pairs for the 58.
3. Locator (bones first, then neighbours; squint search under anatomical relations).
4. Coordinator (trust-radius recall, censors, concurrence, the condition contracts, the value mapping, the bounded zoom).
5. Report reader (4,349 reports into ternary calls, with flags).
6. Kaggle notebooks (competition and scaling).
7. The held-out check on the 58, as information.

The 12 condition contracts are domain content: the lead drafts them from the SOP sources, Codex and Fable check them
(FULL_BUILD_PLAN §7's rule review), and only disagreements go to Rohan.

## Approved execution and implementation

Rohan explicitly approved and ordered the wide build and private Kaggle dry run. The frozen worker interfaces, production integration and verification contracts are in [SQUINT_PRODUCTION_CONTRACT.md](SQUINT_PRODUCTION_CONTRACT.md). FULL_BUILD_PLAN §17 governs this execution. Earlier hard-endpoint output, cohort healthy-band requirements, and unconditional full-reference inference are superseded for production. Historical interfaces and checks remain in docs/history/AI_DIAGNOSTIC_DESIGN.before-squint-20261021.md. The current packet owns live state.
