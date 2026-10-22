# Active task packet

Sole populated current-state record; FULL_BUILD_PLAN §13 owns this pointer. Revision **137**.
Prior revision 136 is preserved verbatim at `docs/work/history/active-task-packet-revision-136.md`.

## TASK ID / PACKET REVISION / STATE

`THIN-OBJECT-BOOTSTRAP-20261021` / `137` / **finishing the five handoffs; the demonstration comes next**.
Rohan asked that the work adhere to two re-centering accounts he sent (author not stated; acted on as his
request). The deliverable is a usable bootstrap memory and one small, inspectable cycle through the real entry
point: recognition → admission → diagnosis teaching → child publication → reuse. Four workers are building the
remaining handoffs in parallel; root integrates.

## CURRENT REQUEST / AUTHORITATIVE EXCHANGES / ACTUAL AUTHORS

The five handoffs, verbatim from the account Rohan sent:
1. «Carry established anatomical evidence through preparation, recall, diagnosis and admission.»
2. «Let negative cases affect decisions where their actual reason and scope apply.»
3. «Preserve unaffected positive views when another view is corrected.»
4. «Keep held-out studies outside teaching and its relevant lineage.»
5. «Join official clinical teaching to warranted object presentations without widening its scope.»
Then: «demonstrate the bootstrap through the real entry point. Show actual images, recalled precedents and the
resulting object/condition interpretation. Demonstrate a genuinely new warranted admission, inspect the first
round, publish its signed child and show the next round using that child.»

Rohan, verbatim, on how: «All of this already exists and works in the project» · «You just need to find it and wire
it properly, define things according to anatomy and visual reasoning» · «I also restarted serena, plus there's
aider, and the tooling in the CI gate». The identity correction of revision 136 still governs (femur and tibia by
their observed ordering in the scan's known directions; established information conditions every later question).

Relayed reviews (agent text, verbatim) are kept in `data/readings/ai-bootstrap-loop-20261021/codex-bones-20261021/`,
the latest as `relayed-review-negatives-holdout-correction-20261021.md` with the lead's checks against the code.

## SOURCE HEAD / DIRTY UNITS / MANIFEST / INPUT IDENTITIES

HEAD `829df83` on `main`, clean and pushed. There is one branch: `squint-upgrade` was deleted locally and on GitHub,
and `main` holds its work. Since revision 136: `941b29b` production wrapper pinned to the M1b bundle and memory;
`fdd0df4` held-out refusal; `829df83` knee side read from the series headers.

**Privacy repair, 2026-10-21 (the lead's error, at Rohan's request).** The repository is public. Commit messages had
carried session links and co-author lines, and the conversation records had been committed. A message-only history
rewrite removed those lines from every commit message (file trees unchanged), `docs/conversations/` is now ignored
and untracked (the files stay on disk), and `main` was force-pushed. Residue Rohan accepted («Whatever, just
continue with the build»): old commit ids stay reachable on GitHub until GitHub support purges them; PR #1's ref,
Actions run records, CodSpeed and SonarCloud may hold old messages; old versions of the conversation files remain
in history.

**Standing bans (Rohan's global rules).** No AI attribution or session lines in any commit or pull request. No text
search of any kind (grep, rg, git grep, or through another tool or agent) and no head, tail, sed, awk, cut, wc, jq
or pipes. Commit to `main` only. Push with the scan's own exit status:
`.venv/bin/python scripts/push_checks.py scan origin/main..main && git push --no-verify origin main`. The long
local gate is skipped by his instruction; GitHub runs the full gate on every push. Serena indexes the worker
worktrees under `.claude/worktrees/` too: read main's files by absolute path.

Parent memory **M1b**: `data/readings/ai-bootstrap-loop-20261021/signed-memory-m1b/memory`, manifest sha256
`e8169d459a9d3a21…`, 792 cases (168 object, 624 whole-condition), 168 confirmed, 335 negative, 30 alternative
identities, from all 493 calls.

## OWNER / PERMITTED WRITES / WORKER ROUTES

Root (this Claude Code session) owns intent, shared source, integration and acceptance. Workers run in isolated
worktrees on branches based on main (`941b29b` or `829df83`); root cherry-picks their commits onto main and
checks that no message carries an attribution line.

## WHAT IS DONE IN THIS REVISION

- **Held-out integrity (handoff 4), `fdd0df4`.** A held-out study that already teaches the parent (any object,
  configuration, negative or alternative record) is refused by name before the round
  (`held_out_study_teaches_parent`); inherited held-out records are checked too; nothing is dropped to make the
  hold-out true. The reviewer's reproduction is the regression test. 279 focused tests passed.
- **Knee side, `829df83`.** Production never set the knee's side, so every medial/lateral relation stayed unknown
  and every sided dependent (menisci, collaterals, gastrocnemius heads) was proposed on both mirrored sides. The
  anchors already recorded the knee the series headers name (DICOM Laterality). The locator now uses it unless
  the caller supplies a side, and the study evidence names the side and its source. 1,326 squint tests passed.
- **Private Kaggle dry run v6** (M1b, bundle `60c5fb8e…`, 3 public studies, `/tmp/rsna-dryrun-v6-out/`), measured on
  Kaggle: whole notebook 347.9 s (setup 166 s, of which offline wheel install 90 s and import check about 60 s;
  inference 182 s); per study 59.5, 75.3 and 106.9 s with 3 workers; peak RSS 5.49 GB; 0 full-anatomy runs; 6 to
  8 bounded zooms a study; the recall preparation was recomputed (13.9 s) because the bundle did not supply it. 36
  outcomes: 4 assigned, 2 defeated, 30 open. **Projection, not a measurement:** about 80 s a study on 4 workers
  puts about 1,300 hidden studies near 7.2 h of the 9 h cap. **Latest safe final launch: about 13:00 UTC on
  22 October** (deadline 23:59 UTC, less the 9 h notebook cap, less about 2 h for packaging, upload and queueing).
  No submission without Rohan's word.

## RECOGNITION CAPACITY: THE BONE ANCHORS (measured 2026-10-22 on `639b962`)

Over the 63 local studies (`data/readings/ai-bootstrap-loop-20261021/anchor-survey-639b962/survey.json`):
the femur is `conflict` in 54 (51 by the cross-view check), the tibia in 45 (41); the patella is `conflict` in
28, all because it was named in front of a femur whose views disagree; 30 studies keep no usable bone; 34
headers name no knee. Pictures (`/tmp/rsna-crossview/`; script `draw_cross_view.py` beside the survey): in
study `…075652399585` and `…548497591402` the sagittal middle-slice naming takes the posterior thigh soft tissue
for the femur, the very mistake the M1b negative cases record; the cross-view check catches it, and the producer
then discards the correct coronal femur as well. The lead's draft repair (rename a contradicted orientation's
section to the territory the other view's carried section lies in, accepted only if Law 9 then holds both ways)
is under FULL_BUILD_PLAN §7's review: draft `lead-draft-cross-view-rule.md`, Codex and Fable answers beside it.

## STARTING BUCKETS (M1b inventory)

`data/readings/ai-bootstrap-loop-20261021/bucket-inventory-m1b/inventory.json`, with an example sheet per object
and call. Every one of the catalogue's 493 candidates was called (43 unsure). Gaps no existing candidate can fill:
a diagnosed ACL and MCL presentation, a normal bursa (Baker's); thin: patella, fibula, cartilages, fat pads; no
LCL, popliteus or ITB candidates at all. They come from recognition on labelled studies, called on their
pictures, with the official labels at their scope.

## WORKERS

| Task | State | Evidence |
|---|---|---|
| H1: contextual identity through preparation, recall, diagnosis and admission (handoffs 1 and 2) | running. Corrected twice by root: negatives apply where their question is open and their reason holds for the candidate's actual support, judged over object-role banks (a territory's `object` tiles, not its `context` ring); a territory's origin tells a resolved support from a proposal; contested or opposed identities are not admitted and do not decide that identity's questions; under the structural basis the reader's observed ordering is the anatomical support, and the recognition match is heard against every identity outside the structural reader's own bones (femur, tibia, patella, fibula, found in this study or not: a side agent's note, checked against Rohan's «They're BOTH BONES» and «Do not ... tune bone profiles apart»); it measures that on the M1 public readings and reports the numbers; it delivers a branch on main | worktree `agent-a7e32e09526dae3c0` |
| G3: correctable admissions, scoped (handoff 3) | first delivery `lane-g3-main` (`12c278d`, `11f4d87`): export-admissions, reject moves the case to a scoped negative; defect confirmed (a one-view reject removed every positive view and its diagnosis evidence; mixed and alternative call forms refused). Resumed: split by view through the seed path's own mixed form, accept `negative_views` and `also_positive`, reverse the tests that pinned the refusals | worktree `agent-a17bc123853d1ecd7` |
| C2: whole-condition configurations grown from newly admitted objects (handoff 5) | running, branch `lane-c2` at `829df83`; uses the existing builder and lane E's identity-view scoping; parent configurations unchanged | isolated worktree |
| P: each observation request kind gets its own acting consumer (`locate_object_region`, `profile_object_window`, `repeat_object_recall`; `bounded_zoom` unchanged) | running, branch `lane-p` at `829df83`; new module `squint_procedures.py`, one call changed in `infer_study` | isolated worktree |

## NEXT ACTIONS, IN ORDER

1. Integrate H1, G3, C2 and P as each returns: focused tests, cherry-pick onto main, scan-gated push.
2. Baseline through the real entry point on `829df83` (running): M1b, the 2 pulled training studies and the 3
   public studies, `data/readings/ai-bootstrap-loop-20261021/baseline-829df83-r1/`. It checks the knee-side change
   on real studies and records the state before H1.
3. The demonstration on the integrated tree: the same 5 local studies inferred against M1b; `grow` with
   `--labels data/raw/train.csv`; `sheets`; inspect every admission on its picture; correct wrong ones through the
   admission review; publish the signed child; a second round that reads the child; trace identity into the
   condition inputs and bounded observations; check that admitted training objects received correctly scoped
   official teaching. A round that admits nothing names a blocker; it is not growth.
4. Scale with Rohan's download (the competition zip, still downloading): batches into `data/raw/train_series/`,
   a declared held-out set kept out of teaching and growth, later rounds spot-checked, identified/abstained/wrong
   reported per condition.
5. Final memory, package, private dry run and the latest safe launch; submission only on Rohan's word.

## OPEN SEMANTIC CHOICE / PREREQUISITES

None needs Rohan yet. If H1's measurement shows that structural bone cases cannot rise above the non-bone
identities, that goes to him with its numbers rather than any loosening.

## UNREVIEWED / WITHDRAWN / STALE RESULTS

The worked example's round two stays withdrawn. Lane G3's first delivery is superseded by its corrected one.

## VERIFICATION STILL OWED

The four workers' deliveries and their two-sign tests; the baseline's reading; the demonstration cycle and its
inspection; the identity consumer's effect on real condition inputs at scale; the integrated offline resource
envelope after the final memory.

## HANDOFF TIME / EVIDENCE LINKS

2026-10-22, about 00:40 UTC. Dry-run output: `/tmp/rsna-dryrun-v6-out/` (receipt, per-study evidence, logs, CSV).
