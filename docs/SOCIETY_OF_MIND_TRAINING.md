# The society of agencies: design binding, build spec and training plan

**Current bootstrap binding, 2026-10-22.** Hand-build the anatomical normal/diagnosed corpus,
measure its bundles and assign the signed K-lines, then use it for the specified classical
training. Automatic recognition of every teaching study is not a prerequisite. Correctly
identified objects not implicated by the study's positive labels are valid normal examples.
The dated L0 critical-path and score comparisons below are historical findings, not a gate on
this hand-teaching operation. Current commands and evidence are in GROUNDED_RECOGNITION and
the sole packet named by FULL_BUILD_PLAN §13.

Written 2026-10-22 at Rohan's request: «Write up a full design document and build spec/training plan
for it. Then let's do it». "It" is the classical Society of Mind training that comes after the bootstrap:
FULL_BUILD_PLAN §18.1 step 5, "Train the designed classical system".

**Standing.** This is the training-stage appendix to FULL_BUILD_PLAN §18.1. It is not another master
plan.
- **What things mean** is set by [CLASSICAL_AI_BUILD_DESIGN.md](CLASSICAL_AI_BUILD_DESIGN.md), cited
  below by section. This file does not restate that meaning. It adds four things:
  - the operation table, one row per agency;
  - the measured facts that set the order of work;
  - the lane contracts;
  - the training plan.
- **Live jobs and state** live only in the active packet named by FULL_BUILD_PLAN §13.
- **Roles.** The root (the Codex lead, per HOW_TO_BUILD "Recall realignment") integrates shared files
  and publishes memory, keeping one chain. The Claude Code lead and workers build isolated pieces
  against pinned inputs and do not publish competing branches.
- **Sources.** The engineering readings this binds are:
  - the root's Fable consultation, `codex-local-loop-r1/brain-design-20261022/fable.md`;
  - the readiness inventory, `training-readiness/READINESS.md`;
  - the cell-code mining, `training-readiness/cell-learning-mining.md`;
  - the thesis source map, `brain-design-20261022/thesis-reader.md`.

  All four are under `data/readings/ai-bootstrap-loop-20261021/`. They are readings, not authority;
  Rohan's words govern.

## 1. The system in one paragraph

A society of bounded classical reasoners shares one exact representation and a living memory of
experience. Anatomy supplies the structure, lenses supply observations, HDC makes observations,
relations and differences computable, K-lines recall interpretations and the procedures they warrant,
and confirmed departures refine the memory.

**Training changes that structured memory and the behaviour that reads it.** The learned state is
individual cases (positive and negative), near-miss censors and splits, and procedure records. There
are no fitted weights and no model-size sweep. HDC width is representational structure, not a learned
quantity. Any new trainable quantity would need its own concrete meaning and update operation, brought
to Rohan before it is built (CLASSICAL_AI_BUILD_DESIGN §15).

Each of these has its own section in CLASSICAL_AI_BUILD_DESIGN; this file does not repeat them:

| Topic | Section |
|---|---|
| Representation | §4 |
| Calls and the three kinds of negative | §5 |
| Diagnosis carried to the same object's other views | §5.1 |
| Bootstrap | §6 |
| Growth and admission | §7 |
| Training material | §8 |
| Agencies | §9 |
| Production | §10 |
| Concurrence and censors | §11 |
| Efficiency | §12 |

## 2. What already works and what is missing

Code facts are from READINESS (source HEAD `252ce28` plus the root's uncommitted integration) and were
spot-checked this session.

| Operation | Producer → real consumer | State |
|---|---|---|
| Direct visual teaching, positive and negative, view-scoped | `publish_visual_cases` / `publish_seed_memory` → memory → identity recall | **works**; the hand-fill reached 852 cases |
| Recognition-derived growth under the admission rule (§7.1) | `grow_identity_memory` → reviewed child → next round | **works**; r2 had 633 candidates: 4 admitted, 192 opposed, 51 conflict, 386 left as proposals |
| Corrections become scoped negatives, and configurations refresh | `publish_admission_corrections` → `_refresh_corrected_configurations` | **works** |
| Labels and report statements at their source scope | `carry_condition_calls`, `rebuild_study_configurations`, report teaching | **works** |
| Identity decides what condition questions may read | `_identity_readings` → `_identity_consumption` → condition queries | **works** |
| Bounded observations for open questions | `infer_study` → `squint_procedures.route_observation_request` | **works**; the dispatch table is static |
| Near-miss retention: correction + recalled precedent + named difference | none; exact decoders exist (`places.decode_count_names`, `compare_named_profiles`) with no callers | **missing** (Lane A) |
| Learned censor | consumer exists (`retrieval.prepare_question` projects supplied censors); producer missing; 0 censors | **missing producer** (waits on §8 decision 2) |
| Split | no producer or consumer | **missing** (only when earned) |
| Procedure memory: request, context and outcome kept under the case, then recalled | inference records hold requests and observations; nothing retains or recalls them | **missing** (Lane C) |
| Replay against a newer memory | `replay_squint_findings` only re-combines saved evidence | **missing** (Lane E) |

The cell project implements the near-miss learner (`engine/nearmiss.py`, CLI-wired in
`scripts/teach_pilot.py`) and remembered agent arrangements (`engine/assembly.py`,
`engine/assisted.py`). These are reference algorithms. Their provisional numbers are not knee policy:
`NEAR_MISS_ALPHA = 0.00135`, the two-movie rule, band narrowing and seat weights.

## 3. Measured facts that set the order (2026-10-22)

1. **Most studies have no established bones.**
   - In r2 (20 SSD studies, 816-case memory), 10 of 20 had no usable structural anchor.
   - Of 640 object identity questions there: established by structure 4, appearance supports 17,
     appearance opposed 223, signed conflict 91, appearance silent 241, placement only 57, missing
     reading 7.
   - **L0 trace, all 86 local studies** (teaching, public and SSD;
     `society-training-r1/l0-bone-ordering/`):

     | Measure | Studies |
     |---|---|
     | Femur established: 7 complete, 8 partial | 15 |
     | Femur `conflict` | 71 |
     | Of those 71, femur and tibia territories in at least one view with the femur above | **all 71** |
     | Any view showing the tibia above | 1 |

   - The femur conflicts are cross-view disagreements: "the other view's section lies mostly in another
     territory" 150 times, "the two slices disagree" 10, tied 3.
   - So the territories named femur and tibia have the expected relative heights nearly everywhere, and
     the cross-view check then sets the anchor aside. The ordering does not show that each territory holds
     the named bone; the pictures show that for the inspected examples.
   - **Count under L0-R2** (`count-r2.*`, from the full conflict records): undisputed sections remain for
     - the femur in 70 of 71 conflicted studies (2+ orientations in 33, 1 in 37);
     - the tibia in 57 of 63 (2+ in 21, 1 in 36).

     7 femur and 9 tibia studies also carry key-plane ties or same-sequence disagreements. Those keep their
     own meanings.
   - **Pictures** (`l0-bone-ordering/pictures/`, the lead's reading):
     - **Reference study `…149`:** every established section sits on its bone.
     - **Conflicted studies `…231`, `…339`, `…260`:** the coronal and axial femur and tibia sections sit
       on the bones. The sagittal sections, and a few off-centre slices, land on posterior thigh or calf
       soft tissue, a tiny posterior fragment, or one territory running through the joint.
     - The check is right to catch those sections. But `squint_anchors._anchor` makes **any** named
       conflict the status of the whole bone, so the good coronal and axial sections are discarded with
       the bad ones.
     - Counting, by orientation and slice, only the sections no check contradicted: 50 of the 71 keep
       femur sections in at least two views, 17 in one view, and 4 in none. This is an estimate from
       the trace, not a re-run.
   - Without established anchors, placement, identity-in-context and trust all fall back to proposals.
2. **Open questions stay open for lack of trusted cases, not for lack of tools.**
   - In r2, 488 condition requests stayed open as "proposal without sourced trust".
   - Every executed observation returned `measured` (391) or `shared_observation_already_available`
     (431); none returned unavailable.
   - So nothing can yet be learned about tools failing. The learnable signal is whether an observation
     *settled* its question, and that is judged by the question's own oracle, not the completion code.
3. **The posterior-femur relation is untestable as built.**
   - It fires on 0 of its 20 failures: 15 have no established femur, and 5 need a same-section
     comparison at the finer scale (worked example, "Measured before implementing").
   - It stays recorded as Rohan's decision and is held unbuilt.

**Consequence:** the critical path is structural (L0), then learning lanes A and C, while the corpus
grows. More cases cannot substitute for anchors the structure fails to establish.

## 4. The agencies: one row each

Order follows dependencies (thesis §11.3): structure, then identity, then state, then orchestration.

| Agency | Question | Oracle (what may teach it) | Learned record and format | Producer | Consumer that reads it before acting | First demonstration, on excluded studies |
|---|---|---|---|---|---|---|
| Placement (structure, not learned yet) | Where are femur and tibia; which is up? | Pictures; known scan directions | none; anchors are structure | `find_anchors` → `study_anchors` (exists) | locator, identity context, sanity checks | L0: the trace, then a picture-checked rule (§5) |
| Identity | What object does this observation support here? | Scoped visual calls; independent report statements bound to a measured identity. Recognition-derived admissions carry lineage and are **not** an oracle. | Positive and negative identity cases (exist). Near-miss records (Lane A). Censors (consumer exists; producer waits). | `publish_*`, `grow_identity_memory` (exist) | `_identity_readings`, `_resolve_identity_contests`, admission | A corrected admission's scoped negative opposes a resembling candidate on another excluded study through the real entry point (milestone, §7) |
| State and diagnosis | Normal, presentation or configuration of condition X at the views where identity holds? | Official labels; report statements at their scope; warranted visual or clinical calls | Normal and presentation cases, role-qualified configurations (exist); exceptions later | `carry_condition_calls`, `rebuild_study_configurations`, report teaching (exist) | `recall_object` → `combine_condition` | Replay on excluded studies: identified / abstained / wrong per question |
| Residual orchestration | Which bounded observation settles this open question here? | The open question's own oracle after the observation, never the completion code | Procedure records under the case: request kind, subject, question, context (anchors, planes, knee side), outcome, settled or not (Lane C) | inference records hold the raw facts (exist); retention to build | `route_observation_request` (exists); a proposer from recalled records (to build, root wiring) | Excluded studies: requests issued, avoided and settled; full-anatomy runs stay zero |

## 5. Build spec: the lanes

**Step 0 (root, first).** Commit the integrated tree. Packet r141 says the root's source repairs are
uncommitted, and `squint_procedures.py` is untracked. Lanes that edit shared files (pipeline, locator,
procedures, identity) branch from that commit. Lanes that only add new files start now. The Claude
Code lead commits it only with Rohan's explicit go.

Every implementer reads thesis §§8.2, 8.5–8.6 and 11.3 whole before writing learning code. The worker
packet uses GROUNDING_AND_WORKER_GUIDE §5's template.

| Lane | Work | Files | Real consumer | Two-sign checks | Demonstration | Starts |
|---|---|---|---|---|---|---|
| **L0 bone anchors** | Trace done and pictures read (§3). §7 review of draft L0-R1 (`l0-bone-ordering/review/REVIEW.md`): Codex judged it too strong ("the central defect is the consumer's whole-bone demotion"). Fable confirmed from the pictures that coronal and axial sit on bone while the sagittal sections are the odd ones out. The lead's mask check found no geometry offset: the sagittal masks name posterior soft tissue. **Revised rule L0-R2:** a conflict applies at the scope it tested. Sections on either side of a contradiction are disputed and held back with their checks; every other section the finder named stays. The bone is usable from its undisputed sections, with the disputes beside it, and stays `conflict` only when every section is disputed. A disputed key plane is withheld. Open risk: an undisputed wrong section stays until recall or a relation refuses it. **Approved by Rohan, 2026-10-22: "Build L0-R2".** Build contract, from the root's review:
- repair evidence scope only, and keep each unaffected section's existing evidence and authority;
- the absence of a contradiction adds no confirmation;
- disputed sections keep their directed checks as evidence and hypotheses, with no culprit named;
- key planes and references are recomputed from eligible sections only;
- unknown, disputed and unavailable stay distinct;
- placement, contextual identity and admission must actually consume the result.

**Measured and NOT integrated (2026-10-22).** Patch `l0-r2/attempt-2/l0-r2b.patch` (both readings, switchable).

On the 58 labelled studies, with each study's own records excluded:

| Variant | Mean AUC | Cross-band reversals | Tied pairs |
|---|---|---|---|
| Current code (HEAD) | 0.5192 | 829 | 772 |
| Strict (i) | 0.4717 | 1125 | 313 |
| Middle (ii) | 0.4678 | 1117 | 383 |

- 3 of the 10 extra sections that (ii) keeps sit on wrong tissue.
- Production stays on HEAD. More anchors produced more confidently wrong evidence.

**Earlier build** (`society-training-r1/l0-r2/attempt-1/`).
- Usable femurs went from 15 to 85 and tibias from 23 to 80 across the 86 studies; the proof study is
  byte-identical.
- But on `…339` the good coronal sections are disputed, because the wrong sagittal ones contradict them,
  while coronal slice 31 (thigh muscle) agrees only with those wrong sections and so is never disputed. The
  femur is then established partly on muscle.
- A refinement decision is needed before integration.

Tests:
- a disputed section cannot erase an unrelated established one;
- removing a disputed key plane removes any reference that depended on it;
- unknown neither confirms nor contradicts;
- cross-view conflicts, key-plane ties and same-sequence disagreements keep their different meanings. | `squint_anchors._anchor` status and territory split (committed file; a worktree from HEAD); consumers unchanged, since withheld sections already flow to hypotheses | locator placement, identity context, sanity | an ordering seen in one view acts; a conflicting pair with no ordering stays a conflict; the conflict is still recorded | anchored studies counted before and after on the same studies; pictures | trace now; rule after pictures and review |
| **A near-miss retention** | For each reviewer correction: join the superseded proposal to the precedents it recalled (inference record); name the difference by exact decode over shared non-silent banks; count how many of that answer's other successes share it. Write a near-miss record; **no censor**. | new `src/knee/diagnosis/squint_near_miss.py`, new script, new tests | the next review packet shows each correction beside its precedent and the named difference; later the censor producer | silent banks never count as a difference; a refusal or unknown makes no record; one shared brightness bank alone is reported, never promoted | the table for the existing corrections (including #8), with picture packet | **now** |
| **B censor/split consumption proof** | Detective intent tests using a hand-built censor record (labelled synthetic) in the format `prepare_question` consumes | new test file only | `recall_object` | a resembling held-out query meets the veto on its one answer; an unrelated question is untouched; a measured-neutral row and a silent bank still differ | test log | **now** |
| **C procedure records** | First measure, read-only: per object, question and context, how often a finer look or bounded zoom changed the question's state (10 mm → resolved scale), from retained inference records. Then retention: keep (request, context, outcome, settled) under the case with whole-study exclusion. Then a proposer that offers a recalled request first. | measurement: new data script; retention: new `squint_procedure_memory.py`; proposer wiring: root, after Step 0 | `route_observation_request` | a record whose source study is excluded never speaks; a remembered "did not settle" never suppresses a different kind; "no record" changes nothing | on studies excluded from the records' sources: requests issued, avoided, settled; work; full-anatomy runs zero | **Measured** (`lane-c/finer-look-transitions.json`, r2): of 314 finer looks, 1 produced support. 161 stayed opposed and 49 stayed in conflict; 57 went from opposed to silent and 31 from conflict to opposed. These are identity-status transitions only. They do not judge whether a look helped answer its question: a look that exposes a wrong identity can be useful, and `appearance_supports` is not an independent success judgment. **Retention keeps moving.** Usefulness is judged by each question's own checked outcome, never by status counts. |
| **D corpus growth** | SSD batches; first-round picture check done; later rounds spot-checked | root's existing commands | next round | existing | per-round receipts | running (root) |
| **E replay against a newer memory** | Re-run recall from retained profiles against a child memory, without reading images | `scripts/replay_squint_findings.py` (after Step 0) | trajectory reading | same memory gives the same results; a held-out study's own cases never speak | the round trajectory without remeasurement | after Step 0 |
| **F clinical reading** | Report statements at source scope | existing | state agency | existing | existing | running |
| **G fleet** | Per-node `squishos-fleet run/put/get`, one shard of studies per node. SquishOS orchestration is not built, and none is improvised. | node folders only | inference records returned to the integrator | a shard's records name their node, source pin and memory sha; a failed study is rerun, never skipped silently | one shard per node completes and its records load in growth | after Step 0 pins the source |

## 6. Training plan

**One round, the same on every machine:**

1. **Freeze.** Pin the parent memory (sha), the source commit and a batch of new SSD studies. Split
   the batch into shards, one per machine.
2. **Infer.** Each machine runs `scripts/run_interiors.py --diagnostic-mode infer` with the frozen
   parent over its shard. Records come back to the integrator (`get`, sha-verified).
3. **Grow.** The root's `grow` decides admissions under §7.1. Spot-check later rounds; inspect any
   first round of a new kind on its pictures.
4. **Teach.**
   - Visual calls: the lead calls, and Rohan settles genuine ambiguity.
   - Report statements at their scope.
   - Labels carried at their scope.
   - Corrections become scoped negatives now.
5. **Learn.**
   - Lane A: near-miss records from every correction.
   - Lane C: procedure records.
   - Censors and splits only once earned, and once §8 decisions 2 and 3 are settled.
6. **Publish.** One child on the one chain, with configurations rebuilt for the studies that changed.
7. **Read the trajectory** on studies excluded from every source and preparation:
   - identified, abstained and wrong, per question and context;
   - which precedents and exceptions spoke;
   - procedures issued, avoided and settled, and work done.

   There is no single score. Turning a wrong answer into an honest abstention is progress. A recurring
   failure is examined for missing structure before more cases are added.
8. **Checkpoint.** A round directory holds its frozen inputs and one completion receipt per study. An
   interrupted round restarts from its frozen parent and pinned inputs and skips completed studies.

**Enough, not everything.** Rohan, 2026-10-22: «Doesn't need to be every bit of data, it just need to be able to
score and perform well. Classical AI doesn't have the cost/data requirement of ML, we don't need to train on
everything. just enough».
- **Teaching studies** are chosen by their official labels (the teaching source) to fill the thin buckets. ACL,
  MCL, Baker's and Synovitis have only one to three cases on their defining tissue.
- **The held-out set** is a fixed set of studies chosen independently and excluded from every source.
- **Stop and freeze** when identified / abstained / wrong per condition on that set stops improving from one
  round to the next. Coverage of the corpus is not the criterion.

**Curricula** grow as their inputs arrive; none waits for a full corpus (CLASSICAL_AI_BUILD_DESIGN §8).
- Identity: visual calls first, then recognition-derived growth.
- State: labels and reports.
- Orchestration: procedure records, once Lane C's measurement shows something to learn.

**Fleet, measured read-only 2026-10-22.**

| Node | State | Notes |
|---|---|---|
| This Mac | runs everything today | — |
| SquishHub | answers; registry identity matches | MacPro6,1, x86_64, 12 threads, 16 GB; new empty 466 GiB SSD at `/Volumes/VSTEPS-SSD`; Python 3.14.3 and uv in `~/.local/bin`; no project or data yet |
| Sanjay's MacBook Pro | answers; registry identity matches; a family device, used at Rohan's word | M1 Pro, 8 cores, 16 GB, 116 GiB free; system Python 3.9.6 only, no uv; never verified |

- Rohan's word, 2026-10-22: «Squishhub should have an SSD now that it can use, and "sanjays" should
  be up now».
- **Set-up for each node:** source at the pinned commit (`git archive` sent with `put`); environment
  with uv; study shards sent as one tarball per shard and checked; outputs under the node's working
  folder.
- **Transfer cost is real:** the recorded paths measured about 4–9 MB/s. Shards are therefore sized so
  the next shard's transfer overlaps the current shard's compute. This is planning, not a measured
  speed-up.

## 7. First milestone: the launch check for full-scale training

1. **Retain a real teaching experience with authority.** A reviewer-corrected admission: its superseded
   proposal, its call and its source.
2. **Run its agency's learning operation.** The ordinary scoped negative now, plus Lane A's near-miss
   record naming its difference from the precedent it recalled.
3. **Publish without losing signed memory.** One child on the chain, with all negatives and
   alternatives kept.
4. **Consume on another excluded study** through the real entry point.
5. **Show the change.** The negative speaks against a resembling candidate and changes that admission
   or identity state, with uncertainty kept.
6. **Resume.** Interrupt the round and restart it from its checkpoint; completed studies are not redone.

Before claiming steps 4–5 as new, check whether the root's next-round trace already shows a corrected
negative acting on another study. Its recorded trace shows a new *positive* tibia speaking on two
other studies.

## 8. Decisions that need Rohan (short)

1. **Fleet: authorized; set-up in progress, not yet shown ready.** Rohan, 2026-10-22: «We can update/add
   things to both as needed. And caffeinate for the macbook pro». Sanjay's laptop runs `caffeinate`. The
   other agent reported that SquishHub's first environment attempts failed: the pinned numba 0.68.0 has
   no binary for that platform. The fleet worker is resolving it without editing the lockfile.
2. **Censor floor and unit.** Asked only once a real cluster of corrected failures against one
   precedent exists. The posterior-thigh group is not that cluster: he resolved it as structure.
3. **Split reading,** through the parent or instead of it. Asked only when a split is earned.
4. **Posterior-femur relation.** Held unbuilt, as the lead recommends, unless he wants it now.
5. **L0 rule.** Asked only if the pictures show discarded usable bones, with those pictures.

## 9. Out of scope here

Kaggle packaging, uploads and runs. Fitted weights, model-size or capacity sweeps. New cosine or
chance thresholds. A universal episode framework. A cross-node orchestrator. A perfect-boundary
campaign. A second memory chain.
