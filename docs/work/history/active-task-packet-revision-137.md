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
went through FULL_BUILD_PLAN §7's review. Fable read the pictures the same way (sagittal "femur" = popliteal
fossa; coronal = femur) and, with Codex, rejected choosing by which view escaped contradiction. The rule being
built is r4 (`lead-draft-cross-view-rule-r4.md`): a disagreement leaves only that pair unresolved; the one change
allowed is a swap to the rival when anatomy positively favours it (like the marrow of the other bone's section on
the same fat-bright slice, a reference with a positive cross-view agreement, on the bone's own side of it); nothing
is withdrawn for failing; Law 9 confirms; still-contradicting pairs are withheld from anchoring, the rest anchor.
Codex's answers on r1 and r3, Fable's, and drafts r1–r4 are in the survey folder. A side agent's corrections
(relayed, agent text) on scope and on marrow as evidence only are taken in r4.

## STARTING BUCKETS (M1b inventory r2, read through the identity reader)

`data/readings/ai-bootstrap-loop-20261021/bucket-inventory-m1b/inventory-r2.json` (script `inventory_r2.py`; the
first inventory misreported negative scopes and missed alternative facets). Catalogue: 40 anatomical objects; 21
have a positive seed. No seed: biceps femoris tendon, gracilis, Hoffa's pad, ITB, both gastrocnemius heads, both
patellar retinacula, LCL, the generic meniscus, patellar cartilage, patellar and quadriceps tendons, popliteal
artery and vein, popliteus, sartorius, semitendinosus, suprapatellar fat. Conditions: not all twelve polarities
are covered: ACL and MCL lack a diagnosed presentation of their own tissue, Baker's a normal one; the menisci and
Synovitis are thin. Every one of the catalogue's 493 candidates was called (43 unsure), so the gaps are filled by
direct visual teaching (lane V), not by more calls on old candidates.

## ROHAN'S OTHER AGENT (outside this session; keep in mind)

Rohan, 2026-10-22: «I have another agent pulling some weight, note what it's doing and keep it in mind». It is a
Codex agent working in `data/readings/ai-bootstrap-loop-20261021/` (it does not commit; the relayed reviews come
from it). Seen at about 01:12 UTC:
- `codex-clinical-seeds-r1/`: direct visual teaching, a published child of M1b at `codex-clinical-seeds-r1/memory`
  (manifest `4bcc2c29de1290c7…`, 794 cases = M1b's 792 plus direct-visual ACL and MCL cases from study
  `…12606657226568558340797193167488111973`); parent verified unchanged; configuration extension "pending_C2";
  scripts `build_cases.py`, `publish_visual_cases.py`, `test_publish_visual_cases.py` beside it.
- `codex-normal-bursa-r1/`: the normal gastrocnemius–semimembranosus bursa.
- `codex-lateral-seeds-r1/`: lateral structures.
Coordination: lane V takes the other objects (anterior tendons and fat pads, retinacula, patellar cartilage, medial
gastrocnemius, popliteal vessels, sartorius, gracilis, semitendinosus), matches the other agent's case form and
publishes onto the latest visual child, so there is one lineage. C2's configuration rebuild is made callable by any
publication that adds objects to a study; root applies it to the visual children. The demonstration's parent is the
latest visual child, not M1b.

## WORKERS

| Task | State | Evidence |
|---|---|---|
| H1: contextual identity through preparation, recall, diagnosis and admission (handoffs 1 and 2) | running. Corrected twice by root: negatives apply where their question is open and their reason holds for the candidate's actual support, judged over object-role banks (a territory's `object` tiles, not its `context` ring); a territory's origin tells a resolved support from a proposal; contested or opposed identities are not admitted and do not decide that identity's questions; under the structural basis the reader's observed ordering is the anatomical support, and the recognition match is heard against every identity outside the structural reader's own bones (femur, tibia, patella, fibula, found in this study or not: a side agent's note, checked against Rohan's «They're BOTH BONES» and «Do not ... tune bone profiles apart»); it measures that on the M1 public readings and reports the numbers; it delivers a branch on main | worktree `agent-a7e32e09526dae3c0` |
| G3: correctable admissions, scoped (handoff 3) | **integrated** `877d2af`, `603ea10`, `8d85c2c` (337 focused tests on main): a call applies only where it asserts; the untouched facets keep speaking with their diagnosis evidence; `negative_views` and `also_positive` accepted. Open: an admission corrected in part cannot be reviewed again; the corrected case's carry record still lists its admission-time views (the consumer scopes by the rewritten row) | `tests/test_squint_admission_correction.py` |
| V: direct visual teaching for the empty and thin buckets (the G3 worker, resumed) | running: eligible labelled studies (ACL=1, MCL=1, Baker's=0, and any study for each unseeded object); the reviewer names the lens territory that is the object on the locator's slice; existing writer; existing review, calls and admit; official labels at scope | branch `lane-v` |
| A2: bone anchors decided by anatomy (rule r4) | running, branch `lane-a2` at `8ac5bbc`; validation is the 63-study survey before/after and pictures of every kind of outcome | isolated worktree |
| K: knee side from the fibula when the header names none | running, branch `lane-k` at `639b962`; validated against the headers that name the knee | isolated worktree |
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
