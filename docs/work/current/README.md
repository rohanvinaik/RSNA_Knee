# Active task packet

Sole populated current-state record; FULL_BUILD_PLAN §13 owns this pointer. Revision **138**.
Prior revision 137 is preserved verbatim at `docs/work/history/active-task-packet-revision-137.md`.

## TASK ID / PACKET REVISION / STATE

`THIN-OBJECT-BOOTSTRAP-20261021` / `138` / **integrating the last handoffs; the demonstration waits on H1**.
The deliverable (from the re-centering accounts Rohan sent, author not stated, acted on as his request) is a usable
bootstrap memory and one small, inspectable cycle through the real entry point: recognition → admission → diagnosis
teaching → child publication → reuse. Rohan's other agent (Codex, outside this session) states the same order in a
note he pasted (agent text): finish the connections under construction, keep direct teaching going in parallel,
demonstrate one genuine growth cycle locally, scale over the downloaded studies, then classical agency training.

## CURRENT REQUEST / AUTHORITATIVE EXCHANGES / ACTUAL AUTHORS

The five handoffs and the demonstration request of revision 137 stand. Since then, Rohan, verbatim:
- «Send a small sub-agent to read the parts of the "what an <object> is" thesis on object recognition. We shouldn't
  be fucking up discriminating between anatomical objects» · «Like, this image is pretty clear» (the full/cheap
  profile figure) · «Yes, continue with your reading task». The reader's report and the lead's own reading of
  §§1.7, 1.12, 6.2–6.3, 7, 8, 9, 11.1–11.3, 12.2–12.4, 13.2 are done and reported to him.
- «Look in on what you've done and what the other agent that is building has done, make sure it's aligned with the
  build plan and stated, explicit goals». Reported: the other agent's work is aligned; the lead's r5 bone rule and
  lane V's second publisher were not, and both were corrected.
- A relayed side-agent note on the knee's side (agent text): about half the scans' headers name no knee; decide
  whether a working side test is worth the time. Decided and built (below).

**Open question put to Rohan (no answer yet):** for growth over his downloaded studies, run the existing
high-resolution pipeline locally on each study (bootstrap tooling, never Kaggle; about 45 CPU-s a study) so every
admitted case keeps its full and its cheap description, as in his figure, and admission compares full with full as
well as cheap with cheap; or grow cheap-only cases through the squint route as the plan describes. The lead
recommended the full route for scaling; the first demonstration runs through the squint route either way.

## SOURCE HEAD / DIRTY UNITS / MANIFEST / INPUT IDENTITIES

`main` at `234883c` plus this packet: `a208a33` reversed-anchor-pair scoping, `ebcbfc1` knee side by position,
`5a018a2` `5545a22` `234883c` lane C2. 1,451 squint tests passed on `234883c`
(`tests/test_squint_*.py`, `test_bootstrap_contract_intent.py`, `test_curate_squint_memory.py`). Standing bans as in
revision 137: no AI attribution or session lines; no text search, no head/tail/sed/awk/cut/wc/jq and no pipes; commit
to `main` only; push with `.venv/bin/python scripts/push_checks.py scan origin/main..main && git push --no-verify
origin main`.

**The memory chain (one lineage; every publication extends the newest child, pinned just before publishing):**
1. M1b `signed-memory-m1b/memory`, `e8169d45…`, 792 cases (335 negative, 30 alternative identities).
2. `codex-clinical-seeds-r1/memory`, `4bcc2c29…`, 794: direct-visual ACL and MCL (study `…111973`), the other agent.
3. `codex-visual-union-r2/memory`, `dcfc6264…`, 797: bursa (Baker's −1), ITB, LCL (same study), the other agent.
4. `visual-union-r3/memory`, `f500cdb3…`, 806: lane V's nine proof-study seeds (patellar and quadriceps tendons,
   Hoffa's, suprapatellar fat, patellar cartilage with PF OA +1, both retinacula, popliteal artery and vein), sheets
   reviewed by root (`visual-union-r3/review.json`), published with the other agent's maintained utility.
5. **`visual-union-r4-configurations/memory`, `06d28478242441d6…`, 806: the newest parent.** C2's public rebuild of
   all 24 whole-condition configurations of studies `…111973` and `…520594649149` (ACL, MCL and Baker's gain acl,
   mcl and the bursa; PF OA gains patellar cartilage); replaced versions kept whole; `configuration_extensions`
   completes the three "pending_C2" markers. Recall preparation ships with it.

## WHAT IS DONE IN THIS REVISION

- **Reversed anchor pair, `a208a33`.** Lane K found a wrong-side "fibula" (fat) reversing «fibula lateral_to tibia»
  and setting aside the tibia too. Now, when exactly one member of a reversed pair has a section another view of the
  same bone agreed with, only the other is set aside and the kept one records the overruled relation; both or
  neither: both set aside, as before.
- **Knee side by position, `ebcbfc1`.** The table moves only head to foot, so a right knee lies at negative x of the
  patient frame and a left knee at positive x. Checked over all 63 local studies
  (`knee-side-position-r1/side-by-position.json`): 28 of the 29 headers that name a knee agree; the 29th (`…174803`)
  says left, and its coronal slices show the fibula on the patient's right
  (`knee-side-position-r1/disagreement-910529174803-coronal.png`), so the header is wrong and the position right.
  It names 30 of the 34 header-less studies; 4 within half a knee's breadth (50 mm) of the bore's axis stay unknown;
  header and position disagreeing chooses neither (`knee_position.conflict`). Read from the squint's own tile
  centres over the leg. This matters for both meniscus conditions, medial and lateral OA, and the MCL.
- **C2 integrated** (above). Its readings, confirmed by root: an admitted study with a ledger row is rebuilt even
  without a label file; every configuration of a changed study is rebuilt; carried train.csv rows join the
  ledger, and a row differing from the parent's is refused. Storage: each rebuild keeps the study's previous
  configurations (about 2.8 MB per study on a 440 MB manifest); kept in the memory for now, to be looked at again
  when the competition package is built. Still open from C2: a corrected admission (G3) must call the same rebuild;
  `memory_view` does not drop excluded studies' superseded records (they never speak).
- **Alignment review** (Rohan's request). The other agent's two children are aligned: named reviewers, scoped
  views, official labels at their scope, every parent record kept, no unmeasured full profile claimed. The lead's
  r5 bone rule decided "is this bone?" by one brightness test borrowed from the fibula (same height as the tibia)
  and used across the joint, where the scanner's shading makes a real femur read 2–3× the tibia: soft tissue
  anchored in 6 of 11 pictured cases. Withdrawn. Lane V's second publisher was removed in favour of the other
  agent's tested one.
- **Thesis reading** (`what_an_object_is.md`). Recognition is one cosine over a question's named banks against
  confirmed cases, one at a time, like with like (full with full, cheap with cheap), over every scale a profile
  carries (3056–3065, 3919–3920, 4182–4185). Look-alikes are told apart by the structure around them, never by
  which they resemble more; a contest left open settles neither (3940, 3949–3952). A −1 is a confirmed fact and a
  voice within its trust radius; only a censor from a near miss vetoes (3200, 3247–3249). A disagreement or
  abstention returns the question to the structure's own word (3780–3782). Two carries can agree on the same
  wrong neighbour (4027–4031).

## WORKERS

| Task | State | Evidence |
|---|---|---|
| H1: contextual identity (handoffs 1 and 2) | running on `lane-h1-rebase-trial`. Root's ruling: a 10 mm speaking negative opens the identity question only; the bounded 2 mm look decides; admission waits for it. Refined after the thesis reading: after the look, one cosine over both scales together (10 mm + 2 mm), not 2 mm alone, with trust radii prepared for the bank set compared; a disagreement leaves a structural identity standing as the structure's word with the disagreement kept, and leaves a map/prior-only identity open | worktree `agent-a7e32e09526dae3c0` |
| A2: bone anchors, cross-view contest | running r7. r5 withdrawn (above). r6 (warrant = agreement with a section outside the pair) stopped by its own condition: 8 of 27 warranted anchors were soft tissue because two views misnamed the same posterior thigh and agreed (the thesis's two-carries warning). r7: no cross-view warrant; members of a contradicted pair are withheld as evidence; sections outside every contested pair anchor and keep the bone usable; stop if any newly anchoring section is soft tissue. Contested tissue is identity recall's job (H1) | `/tmp/a2-lane/`, branch `lane-a2` (last commit `ccb7b35`, r4+r5, not to be merged) |
| V: direct visual teaching | running: the nine proof-study cases are published (r3); now the remaining buckets in other studies (sartorius, gracilis, semitendinosus, both gastrocnemius heads, biceps femoris, popliteus, more tendons and fat pads), drawing supports from native slices where a product's support is wrong; hands additions to root, never publishes | branch `lane-v` (`140aecc`, `e581a59`) |
| P: acting consumers for observation requests | delivered on `lane-p` (`30a9a85`, `84667ac` on `829df83`); held until H1 lands, then: drop the consumer's own recall, keep the identity rerun after re-profiling, unlocated objects become `not_observed`, share the per-subject location step | branch `lane-p` |
| K: knee side from the fibula | closed, not merged: 5 of 19 decided inferences right; the existing fibula picker takes marrow-bright fat; superseded by the position check | `lane-k-fibula-side-evidence/` |
| C2 | integrated (above) | main `5a018a2` `5545a22` `234883c` |

## NEXT ACTIONS, IN ORDER

1. Push main (scan-gated).
2. Read the pre-H1 shakeout run through the real entry point with the newest parent on the five demonstration
   studies (`data/readings/ai-bootstrap-loop-20261021/demo-pre-h1-r4/`): knee side and position evidence, anchors
   after `a208a33`, whether the new visual cases are recalled, and a decisions-only growth round to see what blocks.
3. Integrate H1, then P; A2 r7 only if its stop condition holds.
4. The demonstration on the integrated tree, parent = the newest child: infer the five studies; `grow --labels
   data/raw/train.csv`; `sheets`; inspect every admission on its picture; correct through `export-admissions` /
   `admit`; publish the signed child; a second round reading it; check identity reaching condition inputs and the
   official teaching's scope. A round that admits nothing names a blocker.
5. Scale with Rohan's download (still downloading; `/Volumes/Untitled` empty so far), then the final memory,
   package, private dry run (latest safe launch about 13:00 UTC on 22 October). No submission without his word.

## OPEN SEMANTIC CHOICE / PREREQUISITES

The full-or-cheap growth question above is Rohan's. Censor and split induction from near misses stays unspecified;
it goes to him as one concrete worked example when the first corrected admission exists.

## UNREVIEWED / WITHDRAWN / STALE RESULTS

Withdrawn: the worked example's round two; the r5 bone rule (and r4's brightness test); r6's cross-view warrant.
Superseded: lane G3's first delivery; lane K.

## VERIFICATION STILL OWED

H1's and P's deliveries with their two-sign tests; A2 r7's survey and pictures; the shakeout run's reading; the
demonstration cycle and its inspection; the integrated offline resource envelope after the final memory.

## HANDOFF TIME / EVIDENCE LINKS

2026-10-22, about 03:15 UTC. Memory chain receipts: each child's `publication.json` and `HANDOFF.md`. Thesis
reader's report: in this session (teammate `thesis-recognition-reader`). Dry-run v6: `/tmp/rsna-dryrun-v6-out/`.
