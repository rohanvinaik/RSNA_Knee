# Active task packet

Sole populated current-state record; FULL_BUILD_PLAN §13 owns this pointer. Revision **151**.
Previous packet: `docs/work/history/active-task-packet-revision-150-before-train-ready-repairs.md`.

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

## SOURCE / ONE NEWEST MEMORY

Parent memory: `data/readings/grounded-teaching-20261022/integrated-r4-identity/memory`, **909 cases**.
Manifest sha: `a9b632aa06436a6ed00e0976973abd94cf9ad908841ed31d64a3735a7f280298`.
Preparation sha: `a25e66b6b8f7c8c15bbdd24c8f6a386030dd2db0df33996b0115a9bb283a81fa`.
Chain: 852 -> 876 -> 900 -> 904 -> 909 -> demo-round-r1-child.
Published child memory from local pilot round:
`data/readings/grounded-teaching-20261022/demo-round-r1/memory`, revision `demo-round-r1-child`.
Manifest sha: `79628aa83345d19fda95972d34bedf153ea6c7c1487e4a3b796f962eee20c501`.
Contains 909 cases + 27 retained procedure experiences (with full pre-action cues, action attribution, and independent outcomes).

## IMPLEMENTED REPAIRS (R1-R4)

All four mechanical repairs from `docs/TRAIN_READY_COMPLETION.md` are implemented and verified:

1. **R1 (Signed-label boundary repair):** `prepare_squint_training._compose_round_teaching` now
   correctly handles signed labels (-1, +1) from `read_label_table`, converting known calls to
   (0, 1) for `carry_condition_calls` and configuration rebuilding while preserving balanced
   ternary semantics internally. Complete official rows properly carry condition calls to confirmed
   object cases and rebuild study configurations.
2. **R2 (Scoped procedure opposition and observed cue):** In `squint_procedure_memory._empirical_opposition_floor`,
   opposition is strictly scoped to actual opposing procedure experiences of the same
   `(subject, kind, question)`. Same-subject normal clinical cases (`condition_calls: {question: -1}`)
   and negative identity cases are no longer treated as procedural opposition. `_row_cue_banks`
   extracts observed pre-action HDC cues without arbitrary fallback. Removed the brittle dominant-bin
   matching gate.
3. **R3 (Per-action causal attribution):** In `infer_study` (`src/knee/diagnosis/squint_pipeline.py`),
   each routed observation now records `before_cue`, `before_state`, `after_state`, and `attribution_scope: "single_procedure"`,
   capturing the specific effect of that look rather than overwriting it with the batch or final question outcome.
4. **R4 (Pin-complete resume and child verification):** `prepare_squint_training.py` pins all 12
   participating source modules. On resume, checkpoint validation checks study hashes and code identities.
   Child publication verifies content against expected parent and cases, and reuses the published child
   without deleting or overwriting it.

## VERIFIED READBACK AND PILOT DEMONSTRATION

1. **Focused intent suite:** **145 passed** in 2.07s across `test_prepare_squint_training.py`,
   `test_squint_procedure_memory.py`, `test_squint_memory_view.py`, `test_train_ready_repairs_intent.py`,
   and `test_squint_pipeline_identity_consumption_intent.py`. Full squint suite:
   **1,614 passed** in 43.8s.
2. **58-Study Addressed Teaching Readback:** Replayed retained readings through real condition
   consumers against `integrated-r4-identity/memory` (`grounded_replay.py --teacher-supports`).
   Audited via `grounded_recognition.py audit`. Generated the complete 696-row ledger in
   `data/readings/grounded-teaching-20261022/teaching-question-ledger-696.json`:
   - **ACL:** 2 identified, 56 unresolved, 0 contradicted
   - **MCL:** 5 identified, 53 unresolved, 0 contradicted
   - **Medial Meniscus:** 9 identified, 49 unresolved, 0 contradicted
   - **Lateral Meniscus:** 9 identified, 49 unresolved, 0 contradicted
   - **Medial OA:** 40 identified, 18 unresolved, 0 contradicted
   - **Lateral OA:** 41 identified, 17 unresolved, 0 contradicted
   - **PF OA:** 30 identified, 28 unresolved, 0 contradicted
   - **Effusion:** 21 identified, 37 unresolved, 0 contradicted
   - **Synovitis:** 9 identified, 49 unresolved, 0 contradicted
   - **Baker's:** 3 identified, 55 unresolved, 0 contradicted
   - **Contusion:** 37 identified, 21 unresolved, 0 contradicted
   - **Fracture:** 39 identified, 19 unresolved, 0 contradicted
   - **Total:** 247 identified, 449 unresolved, **0 contradicted**.
3. **Real Training Round Execution:** Executed `prepare_squint_training.py --run-round` on ready local
   study `1.2.826.0.1.3680043.8.498.18392509497170616983977319528036573378` using native series slices.
   Published verified child memory `demo-round-r1-child` with 27 retained procedure experiences.
4. **Resumable Round Verification:** Re-ran the identical round command on `demo-round-r1`.
   Reported `{"executed": [], "requested": ["...1839..."], "resumed": ["...1839..."]}` with 0 studies
   re-executed, reusing verified checkpoints and preserving the published child manifest.
5. **Learning-to-Action Demonstration:** On an excluded study (`...7736...` excluded from memory):
   - Under parent memory: default request order was `['other_tissue', 'gastrocnemius_semimembranosus_bursa']`.
   - Under child memory: contextual recall identified the taught confirmed look from `...1839...`
     (`recalled_confirmed_resolution`) and promoted `gastrocnemius_semimembranosus_bursa` to tier 0
     (order: `['gastrocnemius_semimembranosus_bursa', 'other_tissue']`).
   - Incompatible cue / different context control remained at neutral tier 1 and was not promoted.

Recorded 2026-10-22T16:11:00.000000+00:00.
