# Active task packet

Sole populated current-state record; FULL_BUILD_PLAN §13 owns this pointer. Revision **153**.
Previous packet: `docs/work/history/active-task-packet-revision-152-before-trace-and-fresh-round.md`.

## TASK / AUTHOR'S OBJECTIVE / CORRECTION

`HAND-GROUNDED-CORPUS-20261022` / **Hand-build the corpus that bootstraps classical AI.**

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
   - Chain: 852 -> 876 -> 900 -> 904 -> 909 -> demo-round-r1-child -> train-ready-round-r2-child.

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

## VERIFIED LEARNING-TO-ACTION TRACE

Saved to `docs/work/reviews/learning_to_action_trace.json` and `data/readings/grounded-teaching-20261022/learning_to_action_trace.json`:
- **Teaching experience:** Study `...1839...`, row 037 (`Baker's` / `gastrocnemius_semimembranosus_bursa`, category `confirmed_resolution`, independent outcome: `call: -1` checked against `train.csv`).
- **Held-out study:** Study `...7736...` with `exclude_same_study=True`.
- **Under parent memory:** No procedure experience exists (`status: no_precedent`); candidate requests stay in default contract order `['other_tissue', 'gastrocnemius_semimembranosus_bursa']`.
- **Under child memory (matching cue):** Recalls experience `...037` (`status: recalled_confirmed_resolution`); promotes `gastrocnemius_semimembranosus_bursa` to tier 0 (`['gastrocnemius_semimembranosus_bursa', 'other_tissue']`).
- **Under child memory (incompatible cue control):** Incompatible HDC cue does not match (`status: no_contextual_cue`); request remains unpromoted at default contract order `['other_tissue', 'gastrocnemius_semimembranosus_bursa']`.
- **Study exclusion:** When queried with `study_uid == ...1839...`, the experience is strictly excluded from matching (`exclude_same_study=True`).

## CORPUS EXPANSION CONNECTION

`prepare_squint_training.py` handles runtime procedure experience retention and composes reviewed visual
teaching and carried clinical calls into child memories and `child-training/` exports.
It does NOT replace identity admission, review, or correction:
1. Candidate visual additions and identity cases are admitted via `grounded_recognition.py audit` and
   `scripts/run_squint_admission.py`.
2. Reviewed visual teaching is validated via `squint_visual_teaching.py`.
3. Validated additions are passed to `prepare_squint_training.py --visual-additions <path>`, which
   incorporates them into the published child memory and generates the updated `child-training/` corpus.

## VERIFICATION SUITES

- Focused intent suite: **146 passed** in 2.36s (`tests/test_train_ready_repairs_intent.py`,
  `tests/test_prepare_squint_training.py`, `tests/test_squint_procedure_memory.py`,
  `tests/test_squint_memory_view.py`, and `tests/test_squint_pipeline_identity_consumption_intent.py`).
- Full squint test suite: **1,614 passed** in 43.8s.
- Ruff checks: all passed.

Recorded 2026-10-22T16:32:00.000000+00:00.
