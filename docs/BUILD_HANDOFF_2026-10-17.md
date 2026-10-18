# RSNA_Knee build handoff — 17 October 2026

**Superseded in part, later on 2026-10-17.** The pending joint review (§5) is done: its findings, the evidence and a
fix design that was not applied are in `data/readings/collapse-20261016/lead-joint-review-20261017/REVIEW.md`. The
"reference-guided search" this handoff describes (§2, §5 and §9: a bone reference first, measured relative positions,
cohort ranges, "the next coherent reference-guided extension") is replaced by the relative position map, whose
understanding is `docs/RELATIVE_POSITION_MAP.md` §0: one 3D map of the whole knee, every object against every other
object as a 3D vector from anatomy and physiology, the 58 studies giving only each pair's range and standard
deviation. Rohan corrected the statistical framing repeatedly that day: «I told you to base this on knee anatomy, NOT
on statistics». §1's grounding, §7's working method and §8's evidence and canonical state still hold.

**This file is a dated handoff snapshot, not the current build scope.** The current map is one 3D all-pairs
representation in shared physical coordinates. Each object's position is constrained by three independently
selected key planes, one per anatomical orientation; their physical constraints jointly establish its position, not
a centroid from one section. There are no sequence-specific anatomy maps. Anatomy and physiology supply the ideal;
the 58 studies measure pair-vector range and standard deviation only. The old statistical-window and single-section
localization directives below are historical evidence. Valid measurement sharing, lens, squint and physical-coordinate
principles remain useful where they serve this map.

Project root: /Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee

This records the work and where to continue. Rohan's actual words and the primary thesis govern intent. Current source, Git and source-matched receipts establish implementation state. This handoff, worker reports and old audits locate evidence; they do not replace it. A note written to guide a fix can describe a defect that has since disappeared. Never revive it as a premise.

## 1. Complete grounding before continuing

At session start and after every compaction, read these complete documents in this order, before proposing or changing the build:

1. docs/conversations/2026-10-13-the-thesis.md — the original conversation, verbatim.
2. docs/THEORY_OF_THE_CASE.md.
3. docs/OBJECTS_AND_CONDITIONS.md — anatomy, sequence context and sources.
4. docs/HOW_TO_BUILD.md — the working loop and corrections that prevent drift.
5. docs/RESOLVING_THE_PARTS.md — views, lenses, combinations, definitions and limits.

Read current AGENTS.md too; do not edit its generated global section. Follow Rohan's latest actual conversation when available. This handoff is not a substitute for grounding.

Then LOOK at actual pictures with the thesis in mind, at useful/native pixels. Numerical records alone are insufficient. Proof study UID:

1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149

Under data/pictures/:

- interiors/<proof UID>/series.png: acquired signal, low signal, distance/peaks, territories and boundaries. The anatomy is already visible through these complementary lossy readings.
- assignments/<proof UID>/series.png and main-slices/<proof UID>/series.png: earlier named anatomy. These canonical pictures belong to the definition pass, not the latest collapse source.
- collapse-20261016/anatomical-reference-first/dev/94649149/reference-71931282-tibia-slice15.png: the actual selected reference on the proof.
- Same folder, patella-search-74719429.png: reference-guided native patella selection and dependent structures.
- collapse-20261016/reference-joint-first/interiors/<proof UID>/joint/71904198-joint.png and 71931282-joint.png: latest joint pictures. The API worker inspected these; the lead has NOT independently reviewed this latest joint implementation or its pictures yet.

Then read docs/DIMENSIONAL_COLLAPSE_PLAN.md, docs/ANCHOR_RELATIVE_SEARCH.md and docs/IDEAL_SLICE_SEARCH_PRIORS.md. Distinguish proposals, historical results and current source. The plan's acceptance clarification from Rohan governs its more ambitious wording. Historical provisional anatomy lists are superseded by the completed definition pass in RESOLVING_THE_PARTS §9.

Primary object thesis:
../cell_tracking/docs/pipeline_thesis/paper/what_an_object_is.md

For collapse, read complete relevant sections: §1.3, §4, §5.6, §6.4, §13.4 and §14.1–14.2. For the volume-bearing representation read complete §§7 and 13; do not guess textbook HDC. Prior lead checked those sections against the primary source; copies and reading are in data/readings/collapse-20261016/hdc-volume-sources/. The saved primary hash was c0a0ed4f3e8ce624cc90b0329c40151858d26546ef178b9bc4d7fe92b6dd313e; verify before assuming copies are current.

Finally check actual Git/source/worker state, then the execution evidence below. Do not restart an old worker from a stale queue note.

## 2. The thesis and present task — historical handoff scope; map supersedes search directives

Recognition is hand-built deterministic arithmetic over complementary lossy measurements. Each lens is exact about its own measurement; it need not isolate an anatomical object alone. Domain-grounded combinations of signal, enclosure, position, shape and relationships identify objects. A wrong name on an unusual image is not a false measurement, a refutation of the thesis or a reason to withdraw a competent definition. New simple objective lenses are allowed.

The anatomy definition pass is COMPLETE at Rohan's criterion: a meaningful general rule and a competent measurable demonstration for each object at least once. Current work is dimensional collapse and efficient integration: cheap views select useful native planes for recognition; observations retain physical support and provenance; supplied views jointly describe each anatomical object.

The middle slice is an accepted bootstrap. Cheap profiles may inspect depth; expensive recognition does not run on every slice. One object can have several useful properties/planes: meniscal body versus horns, tendon cross-section versus course. Native identification, warranted same-place transfer, cross-plane location target and candidate reading are different evidence. Unavailable/unvisited sites remain unknown. Do not fabricate anatomy between sampled planes.

The newer efficiency direction: resolve an easy bone reference FIRST, then use physical linkage and measured relative positions to target dependent searches. This must be an actual useful anatomical plane and supported landmark, not a centroid of previously gathered point clouds. Expected locations guide WHERE to ask; definitions decide WHAT is there. Broaden if the reference or expected neighbourhood cannot answer. Additional resolved parts can constrain later searches. Amortize shared work across consumers.

Rohan's explicit acceptance language:

> “Noted, but that's fine. We need the capacity to recognize, accuracy and completeness is for AI. We just need to define these objects as "platonic" versions of them, correct in the general case, not perfect or complete”

> “Exactly. (1) Doesn't have to be perfect, perfection is for the later AI layers, and (2) if the overreach is visible, then there should be a set-theory-like combination of lenses that can resolve it”

> “Also, note that computational efficiency in the production path is a key output. Full compute for building and diagnosis is fine, but the production path should be computationally minimal”

> “One other exponential speed-up--Knee anatomy is physically linked. Get the one that is cheapest to resolve with the squint system (I imagine the tibia/femur?), Get its "key slice", use that as a normalizer, get the statistical slice range and position estimation *relative* to the obvious elements, to make the hard compute, the expensive process, sanely targeted where they likely are”

> “Brilliant! I will accept some gaps--the thesis is sound, I have faith it will justify itself over the full build”

These govern the stopping criteria. Do not impose perfection, exhaustive coverage or universal accuracy. Full idiomatic HDC encoding, later AI and diagnosis remain for Rohan to specify. His thesis bundles measured places and own voxels through their band in exact Sylvester–Hadamard count banks; a bundle of bundles remains a bundle. Do not substitute generic HDC or a separate dense-reconstruction prerequisite.

## 3. What we had done at handoff time — dated status snapshot

| Checkpoint | State |
|---|---|
| 4a126fc, documented by 3bede6a | Completed anatomical definitions: bones/marrow, joint, cartilage, menisci, cruciates/collaterals, fluid/recess/lining/capsule, patella/extensor/pads/retinacula, posterior muscles/tendons, lumens, bursa and lateral complex. Demonstrations and limits: RESOLVING_THE_PARTS §9. |
| af3228c | Approved dimensional-collapse plan after Fable consultation and independent comparison with the primary thesis. |
| a118db8 — current HEAD | Integrated useful selected planes and grouped per-study object output. Replaced costly fibula all-slice territory search. Bone/joint/patella observations feed downstream consumers; posterior tubes have cheap continuation pointers. Lead checked proof and positive-bursa examples and selected pictures. Gate at that checkpoint: 552 tests. |
| Uncommitted statistics / exact sampler | Full labelled cohort collected; descriptive slice positions; exact thinned() lattice optimization with wide-integer fallback. No fitted identity thresholds. Saved locations are not all independently validated ideal slices. |
| Rejected first reference attempt | Median/interval of collected bone clouds plus a fixed 20 mm envelope was not the requested key-plane-first mechanism. Removed by the next worker. Historical evidence remains under search-priors/anchor-relative/. Do not restore it or read its old report as current. |
| Uncommitted reference → patella | Real cheap bone key-plane reference and working relative-location consumer. Independently reviewed and accepted first case; §4. |
| Uncommitted joint follow-up | Latest API worker finished. Gate/cohort exist, but independent source/image/entry-point review is pending. Reference-relative joint targeting is NOT complete; §5. |

No commit or push was made during this handoff. Preserve all existing uncommitted changes. Archives remain invisible.

## 4. Historical evidence: independently reviewed reference-to-patella case

Worker directory beneath data/readings/collapse-20261016/api-build-and-search-priors/:
child-reference-patella-implementation/

API-only Sonnet 5.5, medium effort, exit 0; actual cost $11.8662232. Source-matched gate passed 585 tests. The lead read complete reference/patella units and production references, inspected actual output, checked hashes and ran the real CLI on proof plus positive-bursa studies.

select_reference uses shared cheap femur/tibia marrow-support profiles, asks native confirmation where they point, retains ties and widens when necessary. It saves actual bone support, key slice/frame, outcomes and reason. bone_plane_read shares confirmations with later bone consumers. reference_position projects supported geometry onto the target's normal, distinguishing parallel depth from an in-plane landmark. patella_neighbourhood uses the measured physical relation BEFORE profile/native work. read_patella searches that neighbourhood, extends a rising edge to its local peak, confirms through the existing rule, stops redundant exploration when answered and broadens when needed. Other sites remain pointers/unknowns; dependent tendons, pads, recesses and retinacula retain their wiring.

Proof: tibia sagittal key slice 15 → patella native slice 21. Patella cheap readings 36→9; distinct detailed lenses 37→34; fields 30→27. Parent/worker match: all 10 series records, 14 main records, both grouped object outputs, decisions and saved-array digests across two studies. Positive bursa remains identified. Evidence:
data/readings/collapse-20261016/parent-reference-cli-review.json

Across 58 studies / 336 series: patella cheap readings 1899→1243 (−34.5%); patella detailed readings 111→67 (−39.6%); all cheap readings 10977→10189 (−7.2%); all distinct lenses 1461→1493 (+2.2%) because confirming the reference widens on some studies. Reference confirmed in 54/58 studies.

Known limits: widened-reference overreach into soft tissue, incomplete sampling, and one lost retinacula main record when changed patella observations shift its centre. These were stated; Rohan accepts gaps. No trustworthy overall runtime acceleration is established. Reuse the reference across consumers; do not perfect every reference first.

## 5. Latest joint pass: historical snapshot; review status superseded

Worker directory:
data/readings/collapse-20261016/api-build-and-search-priors/child-reference-joint-implementation/

Launch metadata: exit 0, success, actual API cost $4.2800429. It is FINISHED, not an active writer. Its six saved source hashes match current files at handoff. Saved gate: 607 tests passed; import contract, lint/format/dependency/type checks passed. Vulture remains advisory: existing contract declarations/fields and unused fake-callback test parameters. A gate does not validate the anatomical selections.

Worker changes include joint_profile(visit=), merge_joint_profiles, joint_questions, joint_answers, joint_neighbourhood, rewritten read_joint, reference passed through name_the_joint/measure_study, a posterior-axis convention, analysis scripts and 22 tests. It reports view-specific questions and stopping once each is answered, tracking both menisci separately, keeping existing reading-versus-resolved gates, and supporting partial visits/merge/fallback.

IMPORTANT: JOINT_FROM_REFERENCE_MM is currently an EMPTY dictionary, checked in current source. No production reference-relative joint window is active. The worker explains this by sparse non-middle native observations and weak concentration within the bone-gated sample. That is a reported finding to REVIEW, not a refutation of the mechanism or authority to abandon it. Its unsupported-window scratch demonstration is a demo, not a production result.

Saved cohort counts, independently summed by the lead from receipts at handoff:

| Work | Reference/patella baseline | Latest joint |
|---|---:|---:|
| Joint detailed lens readings | 135 | 102 |
| All distinct lenses | 1493 | 1460 |
| Fields | 727 | 686 |
| Joint cheap readings | 798 | 798 |

Savings are stopping/gating, not relative targeting. Worker comparison reports 23 series asking fewer planes; 17 lose native joint rows: 57 reading rows and 10 resolved rows, none gained. On proof, coronal FS slice 17 is skipped because the middle already answers the questions. Review anatomical/downstream effects; do not blindly accept or reject different receipts. The criterion is competent capacity and useful observations, not retention of every redundant sample.

The worker admitted skipping the five full grounding-document reads and substituting other documents. Do NOT inherit that exception. The lead had grounded fully, but has NOT independently reviewed this latest source or pictures.

Next: review actual joint source, stopping criteria, useful non-middle contributions, observation addresses/twins and downstream recess/other consumers. Compare with the source-matched reference/patella baseline. Run proof+bursa into NEW scratch paths and inspect changed output. Fix concrete integration/capacity failures; do not chase every unusual study or perfect borders.

Then choose the smallest real reference-guided extension. Reference-guided bone selection, which feeds the joint's existing bone-confirmation prerequisite, is a candidate to examine, not an architectural command from Sonnet. Keep key-plane-first targeting and minimal production compute as the task.

## 6. Historical statistical evidence and provenance correction

Original descriptive analysis: 58 labelled studies, 336 series, 7960 observation rows, 377 groups. Parent arithmetic check found no discrepancies. Fixed middle, useful native profile plane, continuation pointer, transferred mask and projected target are distinct. Whole-stack fractions alone do not answer the newer relative-reference question. Statistics of deterministic outputs describe those outputs, not independent anatomical ground truth.

Helper evidence:
data/readings/collapse-20261016/search-priors/joint-reference-helper/

Corrected compute.py, native-offsets.json, summary.json and parent-arithmetic-audit.json retain physical offsets, artifact, row, label and selection roles. 173 native resolved sections: 141 bootstrap, 28 profile-selected, 4 own-slice. 156 representatives: 134 bootstrap, 18 profile-selected, 4 own-slice. Parent recomputed all 40 arithmetic groups with zero discrepancies.

The helper initially called all representatives bootstrap and equated a1_objects with the middle. Corrected: ACL own-slice observations are indexed in the interiors receipt but address separate -ACL.npz artifacts. Numeric label is not an object-property definition. Do not repeat superseded provenance claims. Helpers supply facts, not intent or build authority.

## 7. Economical API building and working method

Rohan explicitly authorized cheap subagents and Anthropic API implementation with full needed project context and knee images:

> “Do use that Anthropic API connection. I authorize you to allow it full access, not consult-only”

Recorded payload approval: “Approve full project context and images”.

That expands the default reader-only consultation role for this work. Use the current session's actual tools/permissions; ordinary continuation within the approved scope does not need another payload question.

Read /Users/rohanvinaik/Projects/SquishOS/ops/agents/reference/anthropic-consultation.md before using the route. Never print, put in a prompt or commit credentials. Existing launcher reads the registered key internally, stripping subscription/OAuth alternatives; no keys are in these packets.

Implementation launcher:
data/readings/collapse-20261016/api-build-and-search-priors/launch_implementation.py

It uses API-only Sonnet 5.5, medium effort, restricted tools, explicit dollar cap, no nested workers/API calls, and saves prompt/events/result/metadata/cost. Inspect the complete launcher before reuse. launch_family.py is the low-effort counterpart. Use a NEW unique child directory and concrete bounded assignment. Never automatically retry a failed billed call or relaunch a completed directory. No API writer is currently assigned/running from this session.

Prior packets retain prompt.md, grounding.md, source-units.md, CONTROL.md, work/status/progress, results/usage and hashes. Give meaning/intent DOWNWARD from Rohan's words. Helpers return facts, not what he meant. One production source writer at a time; independent factual helpers are economical. Lead checks source, actual images, real entry point and measurements before acceptance.

Follow the reading law: whole coherent documents/sections/functions/classes; no grep/rg/ag/ack/git grep/head/tail/sed/awk/cut/jq/pipes or fragment substitutes. Filename inventories, AST structure, complete symbols and structured JSON queries are useful. Lead reads Serena's manual and checks references before production edits; helpers use lightweight AST maps and complete units. Find consumers and sibling paths before changing behaviour. Saving is not consuming; keep the ledger honest. Preserve computed information. No new framework or rule machinery.

## 8. Durable source, evidence and canonical state

HEAD: a118db8, with UNCOMMITTED source/docs/tests for statistics, exact sampler, reference/patella and latest joint work. No push. A durable snapshot of then-uncommitted files, previous execution notes, Git state, source hashes, latest worker result/metadata and the independent parent CLI evidence is:

data/readings/collapse-20261016/handoff-20261017-031552/manifest.json

Formerly temporary parent proof+bursa outputs are copied to:
data/readings/collapse-20261016/handoff-20261017-031552/parent-reference-cli/{interiors,main}

Under data/readings/collapse-20261016/search-priors/:

| Output tree | Role |
|---|---|
| cohort-run-final/{interiors,main} | Frozen useful-view baseline plus exact sampler. 336 series / 58 studies; 44 main records / 20 studies. Independent target observations for relative statistics. |
| anatomical-reference-first/cohort-window/{interiors,main} | Reviewed reference→patella source. 336 series / 58 studies; 43 main records / 19 studies. BEFORE for latest joint review. |
| reference-joint-first/cohort-window/{interiors,main} | Latest joint worker source. 336 series / 58 studies; 43 main records / 19 studies. NOT independently accepted yet. |
| reference-joint-first/ | Joint offset/pointer tables/statistics, work comparison, gate log, proof/bursa and drawing runs; unsupported-window demo is separate. |

Canonical data/measurements/interiors and data/measurements/main-slices STILL hold the earlier definition-pass outputs. They have NOT been refreshed with collapse changes. Complete backup:
data/readings/collapse-20261016/canonical-before-collapse/{interiors,main}

Old canonical pictures can disagree with current source without proving a regression. Use scratch outputs for review. Preserve all previous runs; never delete a cohort to reuse its path. Do not repeat 58 studies for a wording change.

After final source is reviewed, reuse compatible cohorts for promotion through the existing receipt/merge path, preserving other studies; refresh proof/test as necessary; run appropriate checks; save a coherent local commit. No push without authorization. No AI attribution or session links in commits/PRs.

## 9. Entry point and ordered continuation — dated snapshot, not current scope

One production entry point: .venv/bin/python scripts/run_interiors.py

Drawing: --draw, off by default; picture-only work stays off the competition path.
--labeled runs labelled studies; --split test runs public/test examples; local --root is data/raw.

Positive-bursa UID:
1.2.826.0.1.3680043.8.498.13335129881737731410081002627729200903

For bounded review use both full study UIDs with --study-uid, --workers 1, --root data/raw, and NEW explicit --run <scratch>/interiors --main-run <scratch>/main. Add --draw for pictures. Omitting scratch arguments risks overwriting canonical outputs.

scripts/compare_receipts.py compares decisions and saved-array digests; --borders-aside applies if only one run drew. Selected-study comparison suppresses top-level object comparison: explicitly compare objects[study_uid] too. Intentional changed selections need anatomical reasoning, not forced equality.

Gate: scripts/ci_local.sh. Report actual results and advisory type/Vulture findings; source-match saved checks via hashes. Performance uses existing ledger/runtime tools: fewer reads are measured work savings, not a proven runtime or exponential bound.

First actions for the next agent:

1. Complete §1 grounding and picture inspection; explain the mechanism plainly. Approval is recorded; do not ask to reconfirm the whole thesis.
2. Verify current Git/source/worker state against §8. Latest joint writer finished; nothing needs waiting on or relaunching.
3. Independently review §5 source, pictures, real entry point and downstream effects. Keep valid reference/patella work and established anatomy. Record evidence and unresolved points.
4. Continue the smallest useful reference-guided extension. Empty joint ranges are unfinished targeting with a reported sample limitation, not completion or grounds to abandon the mechanism. Use anatomy and additional objective lenses where needed. No exhaustive recovery or one-study tuning.
5. Keep work economical with bounded API builders, one source writer and independent lead checks. Update execution state when workers exit.

The latest user request was to save this handoff for a new session. No next build was launched during preparation.
