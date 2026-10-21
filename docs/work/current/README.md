# Active task packet

Sole populated current-state record; [FULL_BUILD_PLAN §13](../../FULL_BUILD_PLAN.md#13-context-stable-continuation-and-stop-points) owns this pointer. Revision **108**. Revision 107 is [preserved verbatim](../history/active-task-packet-revision-107.md). Historical instructions are not live jobs.

## TASK ID / PACKET REVISION / STATE

`SQUINT-TRAINING-UPGRADE-20261021` / `108` / building: P1, W2, W4, W8 integrated on `squint-upgrade` (be221ff, 11da75d); others running.

## CURRENT REQUEST / AUTHORITATIVE EXCHANGES / ACTUAL AUTHORS

Rohan: «How can this be built massively parallel with codex over the CLI and your own sub-agents?» Then: «Some feedback. Take what is appropriate, then please launch a full parallel build». The relayed review and a relayed side note are agent text; the lead's adoption of them is [SQUINT_TRAINING_BUILD §9](../../SQUINT_TRAINING_BUILD.md#9-launch-revision-2026-10-21-routes-dependencies-and-the-first-working-slice). Rohan, later the same day: «Right now we're building the recognition bootstrap stage, recall». Work is focused there: the bootstrap cases from the 58 labelled studies over their own outlines, and recall (location, the question's readings, comparison, the bounded step for open questions). Report reading for the 4,349 unlabelled studies and the reading convention for mild findings are parked for the teaching stage; the Kaggle observation run of those studies is not launched. The Claude Code session is lead and sole integrator from this revision; the Codex app session reviewed and made no changes or launches.

Preserve the approved squint-first design, individual cases, one object across views and scales, independent teaching and conditional refinement. No ML, fitted healthy band, arbitrary cutoff, patient-coordinate transplant, self-teaching or mandatory full reconstruction. Warranted configurations keep their authority at the actual defining-tissue scope.

## SOURCE HEAD / DIRTY UNITS / MANIFEST / INPUT IDENTITIES

Integration branch `squint-upgrade`, based on `c4427e7` (main, 5 commits ahead of origin, unpushed). Wave-0 base commit on that branch carries the interfaces, fixtures, their tests and these documents; workers' worktrees start from it. Focused checks only on the base (8 interface tests, Ruff); the full gate runs on the integrated tree before main is moved and pushed.

Inherited memory `data/readings/squint-production-20261021/bootstrap-r6/memory/`, manifest SHA `6642bf6a8bef52594f5b812a36f1d67c24816d841647960af82b2ac47e06addf`, preparation SHA `51b03d1ba9108c90d84d6a2e15e5246dfafad72c48b95702bf22226bede0b1a9`. A changed writer or support meaning gets a new memory revision; the old one stays readable and is never mixed with it.

## OWNER / PERMITTED WRITES / WORKER ROUTES

Lead integrates shared files (pipeline, locator, anatomy locator, runner, plan documents) and is the only committer. Workers write only their assigned files in their own worktree and their own record folder `data/readings/squint-upgrade-20261021/workers/<job>/`. Routes: Codex CLI `codex exec` (workspace-write, its worktree) and Claude Code sub-agents (their worktree). Cross-route review of each candidate.

## CONTRACTS / INPUT AND OUTPUT MEANINGS / REAL CONSUMER

Shapes and named codes: `src/knee/diagnosis/squint_interfaces.py`. Fixtures: `tests/squint_upgrade_fixtures.py`. Meanings: SQUINT_TRAINING_BUILD §§3, 6, 9. A helper without its real consumer patch is unfinished.

## NEXT SINGLE ACTION / PROPOSED OPERATION / JUSTIFICATION

Launch the first batch (§9's table, about twelve workers), then integrate the working slice as its parts return: leg map, anchors, territory, territory profile, rebuilt memory, recall, output through `scripts/run_interiors.py`.

## OPEN SEMANTIC CHOICE / PREREQUISITES / OTHER OPEN BUILD ITEMS

No new founder choice needed. The leg-map and bone-anchor constructions reuse existing producers and are checked by the lead on actual pictures. The 4,349 unlabelled studies' scans exist only on Kaggle; their observation run (K2) waits for the working slice and its location check.

## ACCEPTED CHECKPOINT / RUN ROOTS / EXACT COMMANDS / EXIT STATUS

Inherited: c4427e7 checkpoint (prior gate 4,391 tests on tree 9a899cf…), heldout-capacity-r4 (58 studies, exit 0, chance-level ordering). Lead's label-free air measurement: `data/readings/squint-upgrade-20261021/air-check/` (on the proof study's coronal and axial fat-suppressed scans the dark digit is spent entirely on air).

## INSPECTED IMAGE ADDRESSES / RESULT AND UNKNOWN SEMANTICS

None new in this revision.

## CHANGED OUTPUT ADJUDICATION / LEDGER / PROFILE / GATE ADVISORIES

No production output changed yet.

## WORKERS

Worktrees under `/private/tmp/rsna-upgrade-20261021/<job>` (branch `upgrade/<job>`, base `e7fe990`); records, packets and launchers under `data/readings/squint-upgrade-20261021/workers/`. Launched 2026-10-21 about 06:30 UTC.

| Job | Route | Worktree | Handle | State |
|---|---|---|---|---|
| C1 true-location control | Codex CLI | c1 | b8rp85f3o | INTEGRATED (true-location mode); 58-study result in `workers/c1/run/` |
| P1 push-check false positive | Codex CLI | p1 | background task bz9xdqmzx | VERIFIED by lead (48 focused tests); applied to `squint-upgrade`, not yet committed |
| W1 leg map | Codex CLI | w1 | bofjc34sb, revision w1-r2 bim2wmct2 | INTEGRATED 9295870 (median rule; lead packaged the patch after capacity stop; locator excludes only outside tiles; proof smoke exit 0) |
| W2 territory writer | Codex CLI | w2 | bg3vmootl | INTEGRATED be221ff (38 focused tests) |
| W4 teacher support to territory | Codex CLI | w4 | bfv17yqgc | INTEGRATED be221ff (763 regions unchanged; 568 supports resolved) |
| W8 memory view | Codex CLI | w8 | bxk8eq2m3 | INTEGRATED 11da75d (160 focused tests) |
| R1a report reader (58 labelled) | Codex CLI | none | background task b0gpgap48 | RETURNED: 510 calls, 0 rejected; compared with labels in `workers/r1-batch/README.md` |
| K1 private Kaggle timing of r6 | Claude sub-agent | none | session sub-agent | DONE: kernel v4 COMPLETE, 25.5 CPU-s/study, 3.23 GB peak, valid CSV (`workers/k1/report.md`) |
| K2 Kaggle observation notebook | Claude sub-agent | k2 | session sub-agent | RETURNED, PARKED for the teaching stage: kernel + shard launcher ready, 20-study Kaggle measurement 16.0 CPU-s/study observation-only (`workers/k2/report.md`); full run not launched |
| R1b report reader (58 labelled) | Claude sub-agent | none | session sub-agent | RUNNING |
| W5 memory rebuild | Claude sub-agent | w5 | session sub-agent | RUNNING |
| W6 question selection | Claude sub-agent | w6 | session sub-agent | INTEGRATED c95d61a, with the lead's sourced MCL-surroundings exception (SQUINT_TRAINING_BUILD §10) |
| W9 bones by structure | Claude sub-agent | w9 | session sub-agent | RUNNING |
| W10 dependents from anchors | Codex CLI, then Claude sub-agent | w10 | bc9e3zmt4 FAILED (model at capacity, no edits); reassigned to a session sub-agent | RUNNING |
| W11 location check | Claude sub-agent | w11 | session sub-agent | RUNNING |
| W14 teaching round | Codex CLI, then Claude sub-agent | w14 | b4jecu4qt FAILED (model at capacity, no edits); reassigned to a session sub-agent | RUNNING |
| W12 residual executor | Claude sub-agent | w12 | session sub-agent | RUNNING |
| W7 recall reads only the selection | Codex CLI | w7 | baeddtawc | INTEGRATED (merged onto W8's memory view by the lead); production recall now needs the territory-v2 memory, v1 is refused by name |
| W13 picture sheets | Claude sub-agent | w13 | session sub-agent | RUNNING |

## UNREVIEWED / WITHDRAWN / STALE RESULTS

Staged r6 runtime package belongs to the inherited checkpoint; K1 times it as a baseline only.

## VERIFICATION STILL OWED / RECHECK BASIS

Working slice through the real entry point; location check on 58; held-out capacity with the rebuilt memory; teaching round with independent labels; report calls checked against labels on the 58; K2 observation on Kaggle; rebuilt package and private timing; exact-tree gate; normal push.

## HANDOFF TIME / EVIDENCE LINKS

2026-10-21, launch. Worker records: `data/readings/squint-upgrade-20261021/workers/`.
