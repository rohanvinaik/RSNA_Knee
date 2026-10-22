# Active task packet

Sole populated current-state record; FULL_BUILD_PLAN §13 owns this pointer. Revision **156**.
Previous packet: `docs/work/history/active-task-packet-revision-155-before-r1-r7-completion.md`.

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

## VERIFIED LEARNING-TO-ACTION TRACE ON REAL HELD-OUT PATIENT STUDY

Saved to `docs/work/reviews/learning_to_action_trace.json` and `data/readings/grounded-teaching-20261022/learning_to_action_trace.json`:
- **Teaching experience:** Study `...1839...`, row 037 (`Baker's` / `gastrocnemius_semimembranosus_bursa`, category `confirmed_resolution`, independent outcome: `call: -1` checked against `train.csv`).
- **Real next-study inference:** Live `infer_study` executed on raw held-out patient study `1.2.826.0.1.3680043.8.498.64703506772167798469048460791472465039` from `data/raw`.
- **Query cue:** Natively extracted from the held-out patient's located `gastrocnemius_semimembranosus_bursa` (192 coarse 10mm banks).
- **Under parent memory:** No procedure experience exists (`status: no_precedent`); candidate requests stay in default contract order `['other_tissue', 'gastrocnemius_semimembranosus_bursa']`.
- **Under child memory (live matching cue):** Recalls experience `...037` (`status: recalled_confirmed_resolution`); promotes `gastrocnemius_semimembranosus_bursa` to tier 0 (`['gastrocnemius_semimembranosus_bursa', 'other_tissue']`).
- **Under child memory (incompatible cue control):** Incompatible HDC cue does not match (`status: no_contextual_cue`); request remains unpromoted at default contract order `['other_tissue', 'gastrocnemius_semimembranosus_bursa']`.
- **Study exclusion:** When queried with `study_uid == ...1839...`, the experience is strictly excluded from matching (`exclude_same_study=True`).

This confirms real procedural learning transfer through actual study inference, satisfying the R3 requirement.

## CORPUS EXPANSION CONNECTION

`prepare_squint_training.py` handles runtime procedure experience retention and composes reviewed visual
teaching and carried clinical calls into child memories and `child-training/` exports.
It does NOT replace identity admission, review, or correction:
1. Automatic identity growth uses `scripts/squint_object_bootstrap.py grow`; inspection and
   corrections use that command family's `export-admissions`, `sheets` and `admit` routes.
   `scripts/run_squint_admission.py` does not exist at the reviewed source.
2. Independently reviewed measured visual teaching uses `squint_visual_teaching.py` and its
   publisher or the validated `--visual-additions` format. Do not relabel recognition-derived
   cases as independent visual teaching merely to fit that format.
3. Intermediate growth staging is handled via `scripts/squint_round_composition.py` (`stage_identity_growth`),
   retaining frozen-parent lineage and requiring admission review for new candidates.

## STATUS OF REPAIRS (R1–R7)

All seven repairs specified in the execution plan are completed, verified, and integrated into the working tree:

| Repair | Description | Status | Verification Evidence |
|---|---|---|---|
| **R1** | Applicability contract & opposition floor | **COMPLETE** | `_is_context_compatible` and `_is_opposing_category` in `squint_procedure_memory.py`. 11/11 tests pass in `test_train_ready_repairs_intent.py`. |
| **R2** | Strict identity-action attribution | **COMPLETE** | Per-action snapshots (`before_cue`, `before_state`, `after_state`, `after_identity_consumption`) required. 11/11 tests pass in `test_squint_identity_action_attribution.py`. |
| **R3** | Real next-study action trace | **COMPLETE** | `scripts/record_learning_to_action_trace.py` executes real `infer_study` on held-out study `...647035...`. Trace saved to `docs/work/reviews/learning_to_action_trace.json`. |
| **R4** | Source & ready-study pinning | **COMPLETE** | `src/knee/diagnosis/squint_training_pins.py` integrated into `prepare_squint_training.py`. 26/26 tests pass in `test_squint_training_pins.py`. |
| **R5** | Round composition with existing growth | **COMPLETE** | `scripts/squint_round_composition.py` integrated into `prepare_squint_training.py`. 10/10 tests pass in `test_squint_round_composition.py`. |
| **R6** | Grounded ternary departures reach 12 conditions | **COMPLETE** | Full ternary readout reaches continuous condition probabilities through `combine_condition` and `rank_condition`. |
| **R7** | Lineage reconciliation & verification | **COMPLETE** | Pinned parent `a9b632aa...`, child `e0fbd5f1...`. 80/80 intent/candidate tests pass in 1.89s; 2,360 squint/repair tests pass; Ruff clean. |

## NEXT ACTION: COMMENCE MULTI-COMPUTER TRAINING PASS

With the bootstrap repairs verified and the pipeline grounded:
1. Proceed with training across available machines (SquishHub/Mac Pro, sanjays MacBook, local machine) as SSD extraction finishes.
2. Ingest raw study batches, run grounded squint inference, retain warrants, and admit high-confidence cases into the expanding society.
3. Preserve the single society architecture: support, role, physiological state, and condition diagnosis remain coupled.

Updated 2026-10-22 after completion and verification of training-ready repairs R1–R7.
