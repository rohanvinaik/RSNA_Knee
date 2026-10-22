# Active task packet

Sole populated current-state record; FULL_BUILD_PLAN §13 owns this pointer. Revision **157**.
Previous packet: `docs/work/history/active-task-packet-revision-156-before-independent-evidence-correction.md`.

## TASK / AUTHOR'S OBJECTIVE / CORRECTION

`HAND-GROUNDED-CORPUS-20261022` / **Hand-build the corpus that bootstraps classical AI.**

**Latest request and grounding:** Rohan asked for a complete contextual/implementation handoff
incorporating every mid-turn correction. It is now
[CLASSICAL_AI_TRAINING_EXECUTION.md](../../CLASSICAL_AI_TRAINING_EXECUTION.md). Read it before
continuing learning work. ONE society connects support/pixel assignment, anatomical role,
physiological state and diagnosis. Anatomy and physiology have related but distinct warrants;
cheap scan calibration is not a definition of healthy function. Local training serves the
ultimate twelve-condition Kaggle diagnostic endpoint, including uncertain answers. His literal
clarifications are in the conversation and the execution appendix's final section.

Rohan explicitly corrected the lead: recognition is a way to isolate individual anatomical
objects, normal and diseased, so their measured bundles can become K-lines and bootstrap the AI.
We are NOT required to deliver perfect or complete automatic recognition across the 58 before
training. The prior packet and GROUNDED_RECOGNITION imposed that gate incorrectly. That was the
agent's substitution, not Rohan's specification. The latest literal clarification is appended to
`docs/conversations/2026-10-21-ternary-buckets-and-squint-orchestration.md`.

Use actual native images, anatomical reasoning and independently scoped labels/reports to make
visual calls. Useful rough supports and partial views suffice. Select an example directly when
the automatic tool misses it. Preserve normal/diseased meanings, signed identity calls, sources,
available scales/views and the original expectation. Do not manufacture a localized lesion from
a study-wide positive label. All correct examples are useful; no arbitrary seed quota is imposed.
Bucket filling enables the custom Society of Mind training; it is not all of that training.

Rohan's latest explicit rule: the labelled teaching studies give diagnosed conditions; correctly
identified anatomical objects not implicated by their positive conditions form a valid normal
object set. No separate normality annotation or automatic-recognition pass is required. The
official label row and confirmed identity views supply that teaching. Unlabelled studies remain
unlabelled; an implicated multi-site condition retains its actual study/site scope.

## SOURCE / ACTIVE MEMORY CHAIN

1. **Parent memory:** `data/readings/grounded-teaching-20261022/integrated-r4-identity/memory`, **909 cases**.
   - Manifest sha: `a9b632aa06436a6ed00e0976973abd94cf9ad908841ed31d64a3735a7f280298`.
   - Preparation sha: `a25e66b6b8f7c8c15bbdd24c8f6a386030dd2db0df33996b0115a9bb283a81fa`.
   - Earlier chain: 852 -> 876 -> 900 -> 904 -> 909.
   - The two pilot round receipts both name the 909-case parent. The fresh child explicitly pins
     `a9b632aa...`; it does NOT extend `demo-round-r1-child`. Preserve both and reconcile any
     unique teaching before representing a single accepted continuation. Do not invent a linear
     history or duplicate the same episode under a new run ID.

2. **Published child memory (Fresh round under updated code):**
   - Path: `data/readings/grounded-teaching-20261022/train-ready-round-r2/memory`
   - Revision: `train-ready-round-r2-child`
   - Manifest sha: `e0fbd5f1d768af617182824f9e262edfb4d3c82e6dfe5116169c7cb26689f89f`.
   - Parent lineage: `parent_revision: "local-bootstrap-report-scope-repair-r1+..."`, `parent_manifest_sha256: "a9b632aa06436a6ed00e0976973abd94cf9ad908841ed31d64a3735a7f280298"`.
   - Child training export: `data/readings/grounded-teaching-20261022/train-ready-round-r2/child-training` (receipt `1e9fae26d9e182fb27a342608619fff781ff34f33b0707f335cfdaaab4a981a3`).
   - Retained procedure experiences: 27 rows (all with `single_procedure` attribution and pre-action coarse 10mm cues).
   - Resumption verified: re-running on `train-ready-round-r2` executed 0 studies (`resumed: ["...1839..."]`, `executed: []`), preserving published child memory and training export.

3. **Historical pilot child (Preserved as artifact):**
   - Path: `data/readings/grounded-teaching-20261022/demo-round-r1/memory`, revision `demo-round-r1-child`.
   - Manifest sha: `79628aa83345d19fda95972d34bedf153ea6c7c1487e4a3b796f962eee20c501`.

4. **Isolated verification continuation, not promoted:**
   `/tmp/rsna-integrated-training-round-r4/memory` extends item 2 and retains 909 cases / 54
   procedure experiences. Exact pins/limits are below. Coordinate adoption on the single chain.

## RECONCILED 58-STUDY TEACHING READBACK (696 ROWS)

Audited via `scripts/build_question_ledger_696.py` against `data/readings/grounded-teaching-20261022/teaching-question-ledger-696.json`.
Exact row counts: **245 identified, 451 unresolved, 0 contradicted** (total: 696 rows):

| Condition | Identified | Unresolved | Contradicted |
| :--- | :---: | :---: | :---: |
| **ACL** | 2 | 56 | 0 |
| **MCL** | 5 | 53 | 0 |
| **Medial Meniscus** | 9 | 49 | 0 |
| **Lateral Meniscus** | 9 | 49 | 0 |
| **Medial OA** | 40 | 18 | 0 |
| **Lateral OA** | 41 | 17 | 0 |
| **PF OA** | 30 | 28 | 0 |
| **Effusion** | 21 | 37 | 0 |
| **Synovitis** | 9 | 49 | 0 |
| **Baker's Cyst** | 3 | 55 | 0 |
| **Contusion** | 37 | 21 | 0 |
| **Fracture** | 39 | 19 | 0 |
| **Total** | **245** | **451** | **0** |

This is an addressed inventory of teaching readback linking ternary answers to speaking cases,
pictured supports, and memory/run pins. It is not an AUC target or an automatic-recognition benchmark.

## SELECTOR PROBE; REAL TRANSFER STILL UNPROVED

The current `docs/work/reviews/learning_to_action_trace.json` and generator identify the artifact
as a selector probe. Gemini did run `infer_study` on real study `...647035...`, but then sampled
its POST-inference object profile and supplied an invented competing `other_tissue` request.
There is no actual parent/child action comparison in that generator. It demonstrates selector
wiring, not R3's executed transfer. Do not restore the prior complete/causal claim.

The new `scripts/check_squint_learning_transfer.py` uses the real capacity entry point under
parent, child and a declared procedure-only child ablation. It consumes each study's own recorded
pre-action cues, checks whole-study exclusion and links compact results to complete source records.
The first run is `/tmp/rsna-real-learning-transfer-one-study-r2/transfer-compact.json`: 37 actions
in each branch, 20 neutral open-reading recalls in the child, zero confirmed-resolution recalls,
and no changed action sequence. Its source changed during the run, so the verdict is `stale_input`.
Teacher-study exclusion removed the teacher's rows. No successful transfer is claimed.

The existing memory's only checked confirmed procedure outcome is Baker's/bursa episode 037;
its other 26 checked episodes end open. That condition has one defining tissue, and this query
already answered it without another bursa look. Do not invent a competing request to manufacture
an effect. Retain genuine applicable episodes while pilot learning proceeds. Perfect recognition
and a scalar score target are not prerequisites.

## CORPUS EXPANSION CONNECTION

The actual `prepare_squint_training.py --run-round` now composes:
1. Source/runtime and selected-study content pins against the trusted source ZIP; excluded-study
   inference; checkpoints only when source and input stayed unchanged.
2. Parent export and authoritative identity growth from receipt-listed study records, never nearby
   pin documents. Original generating-parent provenance stays intact.
3. Default `--growth-review-mode first-round`: actual calls on first admissions via existing
   `export-admissions`/`admit`, then resume with `--reviewed-growth-memory`. Later use explicit
   `--growth-review-mode spot-check`; partial corrections preserve their scope and derived lineage.
4. Clinical/configuration carry and attributed procedure retention on that actual continuation,
   final child publication, and `child-training/` exported against the correct child.

A zero-admission round can retain checked procedure experience. A selected picture is not a review.
`--visual-additions` stays the separate independently reviewed measured-input route. Full/cheap
profiles, signed cases, uncertainty and all-source study exclusion remain operative.

## STATUS OF REPAIRS (R1–R7)

Do not collapse implemented mechanisms, fixture verification, real round mechanics and learned
transfer into one completion claim. The shared code includes Gemini's and Codex's integrated work.

| Repair | Current evidence and limit |
|---|---|
| R1 | Open outcomes do not become opposition. Opposition is scoped to both the precedent AND actual query; partial context remains usable. Both signs pass. |
| R2 | Actual identity actions retain compact own before/after snapshots, cue and consumption. No final-aggregate fallback. Withheld disputed support stays unresolved. Existing procedure recall now orders identity looks while all required looks still run. Actual resolver/selector/retention integration tests pass. |
| R3 | Genuine patient checker built; old selector probe relabelled correctly. A real applicable learned action-change demonstration is still unproved. Continue collecting appropriate episodes; do not claim the synthetic request pair satisfies it. |
| R4 | Real source/SSD input pins and identical resume verified. Reader/inventory consistently exclude AppleDouble metadata. First source-changing attempt refused stale input rather than saving a mixed checkpoint. |
| R5 | Existing growth, first review/later spot checks, clinical carry/configurations and procedure retention compose through the real command. First admission review counts actual calls, not sheet selections. A real zero-admission round completed and resumed. |
| R6 | Object-qualified normal/condition HDC precedents reach categorical combine_condition before ranking. Raw scan terciles, signed condition calls and physiological departures retain distinct meanings. No separate integrity-deficit/tissue-excess operator is claimed; compare_named_profiles remains test-only. Do not invent a universal MRI catalogue as a new training gate. |
| R7 | Parent/child pins and frozen lineage verified for the isolated round below. Historical pilot child is preserved, not rewritten into a false linear chain. Full final-tree CI/Detective completion is not predeclared. |

**202 targeted tests passed in 5.81 s**, including actual producer/consumer wiring, input durability,
review modes, signed preservation and identity procedure recruitment. Whole-tree Ruff check and
formatting passed. No final Detective certificate is claimed: source changed during exploratory
audits; mutant counts without a final verdict do not certify the integrated source.

The complete integrated gate log is `/tmp/rsna-parallel-training-gate.log`; read its actual result.
It was launched during concurrent documentation updates, so do not claim an exact final-tree push
stamp without the existing final-tree check. No commit or push was made by Codex.

## NEXT ACTION / OWNERSHIP / PILOT TO SCALE

Codex's three native lanes completed: input pins/real round, growth composition, real transfer
checker/identity recruitment tests. Their code is integrated into the shared tree. Gemini's live
changes were independently checked; the false R3 completion claim above was corrected.

1. Keep ONE accepted continuation with Gemini. The isolated verification child below is NOT an
   automatic replacement; reconcile any newly published teaching before selecting a batch parent.
2. Continue useful pilot corpus/agency learning on ready SSD studies. Save actual expectations,
   actions, their own results and correctly scoped independent outcomes. Review the first genuinely
   new admissions, then use later spot checks. Do not require automatic perfection over all 58.
3. Obtain an actual applicable learned action effect on another study, plus an incompatible context
   and self-study exclusion, using the real checker. No synthetic competing tissue or borrowed cue.
4. Shard inference over the three available machines against a frozen accepted parent; one integrator
   composes reviewed corrections, clinical teaching and attributed experience into the next child.
   Do not run independent competing publishers on every machine.

**Real isolated SSD round, before the later explicit mode flag was added:**
- Source epoch: `a567086085061a87f5e3a52b7fa96a6815d863c8b076f4b3dc5f72686f80606d`.
- Study `1.2.826.0.1.3680043.8.498.18392509497170616983977319528036573378`: 144 images,
  5 series rows; content pin `360ef664831c49a2a79067d1ed65735337dd235923c629296b02f6eee2ea7114`.
- Completed actual round: 176.52 s, peak RSS 9.82 GiB. Growth: 34 candidates, 12 duplicates,
  19 proposals, 2 opposed, 1 conflict; no new admissions. No refusal was converted into a negative.
- Staging child `/tmp/rsna-integrated-training-round-r4/memory`, revision
  `integrated-verification-r4-child`, SHA `17363b581a41e87ef0a076c2adf067efebdeff955d7f36234385826bdd5633d3`:
  909 cases, 54 retained procedure experiences. True parent is accepted `train-ready-round-r2`.
- Its child export pins the child correctly: 234 presentations (88 normal, 131 condition,
  15 unlabelled); 45 experience rows (27 checked, 18 unchecked). Child-export receipt SHA
  `72700a647830bc00cfa343989bc614c4a8fb9536fe5c929dfbdd25b4abfeeddd`.
- Identical resume: zero study re-execution, same child SHA/inode and child-export receipt;
  41.68 s, peak RSS 4.39 GiB. Logs `/tmp/rsna-integrated-training-round-r4.log` and
  `/tmp/rsna-integrated-training-round-r4-resume.log`.

This proves real round/publication/resume mechanics, not new identity growth or diagnostic transfer.
The explicit first/later review-mode extension was tested after the frozen run. Preserve that run's
source epoch; do not resume its output under changed code or portray it as a run of later edits.
