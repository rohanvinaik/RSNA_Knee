# Final design for the diagnostic layer and the competition run (2026-10-21)

**Later full-stack clarification:** [CLASSICAL_AI_BUILD_DESIGN.md](CLASSICAL_AI_BUILD_DESIGN.md)
connects this production contract to bootstrap, recognition-derived corpus growth, task-specific
training and continuing K-line/censor memory. Read it whole before implementing those stages.
“Bootstrap, done” below refers to the existing anatomical products, not a claim that their signed
recognition memory or the complete agency-learning process is finished. The canonical admission
policy is CLASSICAL_AI_BUILD_DESIGN §§7.1–7.2: unknown stays neutral when answering, but
unknown-only anatomy cannot justify automated new-memory admission. Live state remains only
in [the current packet](work/current/README.md), reached from FULL_BUILD_PLAN §13.

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

## 1. Shared representation

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
The automatic anatomical products are identity proposals until an actual scoped call or authorized
recognition-derived admission establishes them. Positive, negative and alternative-identity cases
remain usable with their original full/cheap bundles; adapting an existing reject must preserve its
exact negative-view scope. CLASSICAL_AI_BUILD_DESIGN §§5–7 owns that signed teaching contract.

## 3. One study in production

1. Read every series once, many files at a time, and squint every slice (10 mm tiles).
2. Locate objects: establish useful current-study bone anchors structurally, then generate a small useful set of
   neighbour candidates through anatomical relations before computing their case scores (§11.1, §12.2). Partial
   native planes constrain whichever directions they actually establish; a complete three-plane reference and
   perfect outline are not prerequisites. Resemblance selects among anatomically meaningful candidates. Nothing
   copies another patient's coordinates, and overlapping windows alone establish no tissue-occupancy contradiction.
3. Recall each object's state: cosine against that object's normal and presentation cases over the condition's
   readings. A case speaks only above chance resemblance (the trust radius, §8.4, set on real data before the run it
   judges); near-miss censors veto their own answer (§8.5); competing answers stay a disagreement, never a nearest-case
   win (§11.2). Distinct coexisting conditions are not competing answers.
4. Let recognized identity govern which tissue can answer a condition question. A region known not to be the
   proposed tissue cannot remain evidence for that tissue; unresolved identity does not mean disease absent.
   Combine per condition by its written contract (§1.11), drawn from anatomy and medical practice and fixed before any
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

A clinical case needs its appropriately sourced report/label call under the SOP mapping and at the
scope that source actually establishes. A memory's own diagnosis is not an independent clinical
teaching call. Separately, Rohan explicitly authorizes high-confidence object-identity recognition
with anatomical common sense to grow the identity corpus. Automatic new-case admission needs
high-confidence joint identity, affirmative applicable current-study anatomical support and no
known contradiction or unresolved signed identity conflict. If all applicable anatomy is unknown,
keep a proposal without admission or a negative. This does not demand all rules, all three planes
or exact outlines, and does not block independently warranted visual teaching. Those admitted
cases retain recognition-derived seed lineage and cannot be laundered as independent clinical or
visual confirmation. This authorized growth supplies material for the larger classical learning process; it does not replace that process.
Duplicate sources count once; conflicting calls stand side by side; abstentions create neither cases
nor censors (§1.14, §9.4, §11.3; SIGNIFICANCE_WEIGHTING §14). Confirmed positive AND negative calls
must remain usable in the appropriate memory, not merely audit notes. See the full-stack clarification
above for frozen-round admission, task-specific learning and runtime use. A child memory keeps
all signed cases and paired full/cheap payloads; study exclusion covers positive, negative and
alternative-identity sources. No new case speaks in its generating round. Ordinary corrected
negatives teach immediately; a specialized near-miss censor requires the thesis's named-difference
test against the recalled K-line's successes, not a count of changed banks or failures. The memory's
trajectory is read as identified, abstained and wrong per question on studies it was not taught on, with no same-study
leakage (§11.4); early thin-memory results do not block supplying the teaching corpus.

## 5. Kaggle notebook

The verified offline wheels (CPython 3.13, python-gdcm and the locked closure), code copied to local disk, concurrent
reads, four study workers, memory loaded once, a time guard that leaves open questions open, values written as studies
finish, a private dry run on the public studies, and a submission only on Rohan's word.

## 6. Measured basis (recorded)

Squint 0.17–0.68 s and reads 0.14–0.40 s per study locally, five labelled studies (`squint-timing/`); Kaggle CPU
2.2–2.9× slower per core; exact sparse cosine 3.3 ms per query against 2,000 synthetic cases on Kaggle; the full pipeline
about 113 CPU-seconds per study on Kaggle, bootstrap only (`../kaggle-hardware-20261021/`). These are stage measurements, not whole squint-first inference costs. The current packet links source-pinned integrated runs and their resources; neither these stage costs nor a valid CSV alone establishes hidden-scale capacity.

## 7. Build lanes (parallel; one integrator)

[CLASSICAL_AI_BUILD_DESIGN §13](CLASSICAL_AI_BUILD_DESIGN.md#13-concrete-build-order-and-parallel-ownership)
owns the detailed integration order and lane contracts: signed teaching and exact call adaptation;
frozen-parent growth preserving every signed record; partial-geometry anatomical support; identity
consumers in condition reasoning; visual calls and report reading; task-specific learning and verification.
One integrator owns the shared coordinator and real entry point. The next demonstration is one
actual signed growth round and its next-round consumer, not a new universal episode framework.
The earlier worked-example round two is withdrawn because it changed the signed comparison; it
proves neither improvement through growth nor a causal propagation error.

Held-out recognition and diagnosis checks report identified, abstained and wrong by question.
The private Kaggle run verifies the full integrated offline deployment, not an inference drawn
from isolated squint timings. Report reading and remaining visual calls proceed in parallel.

The 12 condition contracts are domain content: the lead drafts them from the SOP sources, Codex and Fable check them
(FULL_BUILD_PLAN §7's rule review), and only disagreements go to Rohan.

## Approved execution and implementation

Rohan explicitly approved and ordered the wide build and private Kaggle dry run. The frozen worker interfaces, production integration and verification contracts are in [SQUINT_PRODUCTION_CONTRACT.md](SQUINT_PRODUCTION_CONTRACT.md). FULL_BUILD_PLAN §17 governs this execution. Earlier hard-endpoint output, cohort healthy-band requirements, and unconditional full-reference inference are superseded for production. Historical interfaces and checks remain in docs/history/AI_DIAGNOSTIC_DESIGN.before-squint-20261021.md. The current packet owns live state.
