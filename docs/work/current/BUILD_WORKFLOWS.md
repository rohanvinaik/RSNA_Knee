# Build workflows: carrying out FULL_BUILD_PLAN P2b–P12 (the lead's plan for Rohan's review)

Revision 4, 2026-10-19, written by the lead (Claude) at Rohan's request: «plan out workflows that will
complete the specified build of the full project as articulated thus far (Sonnet xhigh effort for the
agents). Come to me with your full plan when you've designed it, consult codex on the plan». Revision 1
went to Codex; its reading (`codex-answer.md`) and the lead's adjudication (`lead-adjudication.md`) are in
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/workflow-plan-review-20261018/`, with
revision 1 as it stood when the answer came (`BUILD_WORKFLOWS-at-codex-answer.md`). Revision 2 went to
Rohan at 22:05 and is in git at `6ddcb55`. Revision 3, at `17a5393`, answered the review he pasted at
23:37 under his words «Feedback on the workflow»; revision 4 answers the review he pasted at 00:25 under
his word «Feedback:», and records his note at 00:35 on the sub-agents' context (§3). Both reviews are agent
text; what each found and what changed are in §10. He approved revision 4 at 01:01 on 2026-10-19: «Good.
I approve, continue setting this up», answering the lead's question, which offered approval with the
reviews' two Fable answers as written and said that on approval the lead does the setup, runs the
rehearsal, then W1; §1 records his answers. The plan itself is committed and pushed («just freaking commit
to git»).

This is an execution design for `docs/FULL_BUILD_PLAN.md`, not another master plan. The order is the
plan's §4: P2b → P2a → P3 → P4 → P5 → P6, with P7 and P9 items folded in as each family is touched and
P9's generic lineage at the first adapter edit (W4); then P8, P9 closure, P10, P11 and P12; P13 waits for
Rohan. Each workflow names its P-task, the §§14–15 contracts it consumes and produces, its real consumer
and the lead gate it ends at. Beyond the plan: the launch preconditions (§4), the re-check of the six
stopped wave-1 packets (W2), and an owed-item inventory begun in W2 and closed in W10.

## 1. Rohan's decisions

Two, both about the Fable consult (the only second reader that can see a picture; it spends API credits).
The reviews he pasted at 23:37 and 00:25 recommended the same answer to each, and he gave those answers at
01:01 on 2026-10-19 by approving revision 4 with them as written (the lead's question, lead text: "reply
"yes" to approve revision 4 with the review's two Fable answers as written, or tell me yours").

1. **A failed billed Fable call.** The consultation reference says it is not retried without his
   decision. His answer: one retry per rule, made only after the technical failure is diagnosed; while a
   required reading has failed, its rule is held and independent work goes on, and a disagreement is
   never a reason to retry.
2. **Fable for the scope sheets.** Plan §7 covers the ~31 P4–P6 anatomy rules: one reading per rule (a
   call may carry an object's views together only if its answer reads each rule separately). P2a's region
   rule, P3's corridor and cavity scopes and P7's consumer scopes are picture-grounded too, and Codex
   cannot see pictures. His answer: yes, one Fable reading per scope decision, shared by every caller that
   implements the same scope decision rather than one per caller.

Settled by your recorded words, stated so you can correct them:

- **Workflow agents implement.** Your 18:46 instruction (workflows, Sonnet at xhigh) makes workflow
  agents the implementers, each in an isolated worktree, with the lead the single integrator. On his
  approval of this plan, the guide's route row "Bounded implementation → text-only Claude Max" and plan
  §10's matching sentence changed to say so.
- **Pacing.** You see each family wave's pictures together at its end (11:25), and plan §7 builds a rule
  both readers agree with without waiting. So the next family does not wait for your look; anything you
  flag stops the affected work through §3's invalidation.
- **Commits, pushes and the gate.** Every gate ends in a commit and a push. The gate includes Sonar and
  runs again on GitHub for every push (your words after the third compaction, recorded in
  `docs/conversations/2026-10-18-build-session-corrections.md`).

## 2. What stays with the lead (never delegated)

- Choosing every rule and scope: the ~31 P4–P6 native rules (drafted from the native pictures with plan
  §1.2's three statements), P2a's region rule, P3's corridor and cavity scopes, each P7 consumer's scope.
- The plan §7 consultations: Codex (model-only; every prompt carries the complete rule, the governing
  theory, correction and contract units and the evidence as text; a reply that could not read its inputs
  is no review) and Fable (each rule's actual picture sheet). Disagreements go to Rohan.
- Image acceptance: every changed native frame and source support, reconstructed from its address.
- Integration into `scripts/run_interiors.py` and the shared modules, one increment at a time; the real
  CLI runs (proof/bursa serial and parallel, public, the cohort where due); the kernel benchmarks'
  recording, refreshed from the integrated source before the final gate when an increment changes a
  benchmarked kernel or what production hands it (plan §9, step 6; a worktree has no data, so the
  recorder stops there); §15.3's six statements; MAP/RESOLVING acceptance records; the active packet; the
  final gate, with its Sonar step and advisory lists, on exactly the tree being committed; commits,
  pushes, and the GitHub gate run on each pushed commit.
- The job table (§3), each script's offline mock and the runtime rehearsal (§4).
- Running the sequence. Launching a workflow runs only that workflow's agents (W1 launches seven); the
  lead carries the sequence from W1 to W12 itself, gate by gate: integrate, inspect, checkpoint and push,
  prepare the next packets, launch the next workflow. After a compaction it grounds again
  (FULL_BUILD_PLAN §0) and continues from the active packet. On this machine a compaction locks the session
  that compacted, the lead's included. The post-compact hook's own message when it refused this session's
  commands (the hook's text, not Rohan's words): "This session is locked after a compaction: it may read and
  report, and change nothing. [...] The lock lifts when he sends his next message, whatever it says." So the
  lead stops at its first compaction after
  Rohan leaves and waits for his next message; what the lock does to a workflow already running has not
  been observed. The agents' own bound is §3's.
- Stop points: family-wave picture sheets to Rohan; any disagreement between Codex, Fable and the lead;
  a step the P12 contract leaves unspecified; P13.

## 3. Rules every workflow follows

- **Agents:** every `agent()` call passes `model: 'sonnet', effort: 'xhigh'` (Rohan's setting), verifiers
  included. Each workflow stays under ten agents; workflows run in sequence with a lead gate between them.
- **Context:** each agent stays under a million tokens, so it never compacts and is never locked by the
  post-compact hook. Rohan, 2026-10-19: «Note the post-compact hook means that each sub-agent in the
  workflow should stay under a million tokens, which should be entirely doable». Packets are sized for
  it: a prompt inlines upstream returns, never files; an agent reads whole units, not a whole file of
  thousands of lines unless the file is the unit; and every prompt says that a task needing more is
  returned `partial`, naming what is left, rather than carried on. The rehearsal reads each agent's token
  use from the runtime's own records (§4), the lead records each agent's use in the job table at each gate,
  and a packet whose agent came near the bound is split before the next launch.
- **Roles (guide §4):** evidence, wiring, implementation of a rule the lead has already chosen and had
  reviewed, and verification. No agent chooses a rule, a threshold, a sample meaning or a scope, and none
  accepts. A wiring packet that finds it would have to choose one stops and returns it named (guide §5,
  STOP).
- **Packets:** every prompt is built from the guide's §5 template (TASK, ROLE, AUTHORITY, INTENT,
  CONTRACTS, MEANINGS, OPERATION, CONSUMER, SCOPE, PRESERVE, FORBIDDEN SUBSTITUTIONS, SOURCE BASIS,
  DEPENDENCIES, VERIFICATION, RETURN, STOP). A packet that changes how an identity, slice, spatial region,
  source eligibility or calibration support is decided first returns a short operation statement (Reads,
  Produces, Consumer, anatomical justification, the specific non-objective), which the lead checks before
  the implementation call (guide §5).
- **Reading law in every prompt:** whole units only; code located with the AST tools in
  `B/workflow-tools/` (`spans.py`, `callsites.py`, `assigned_names.py`); no Grep tool, grep/rg,
  head/tail/sed/awk/cut/wc/jq, pipes or text search of any kind; archives invisible. The setup check
  reports the no-grep hook as declared but unwired and the read-whole hook as an orphan, so the prompt
  carries the law.
- **Writes:** artifacts only in the agent's own attempt directory
  `B/workflows-20261018/<workflow>/<packet>/attempt-<id>/` (B = the plan's readings root), which must not
  exist beforehand; code edits only in the agent's own worktree (implementation and verification roles).
  Never the main tree, canonical outputs or another agent's files; no commit, push, reset or clean.
- **Source basis:** before each workflow the main tree is clean: no modified tracked file and no untracked
  file outside the ignored paths (worktrees are cut from HEAD and agents in the main tree read the main
  tree, so a dirty file anywhere, code or document, would mean an agent reads something that is not
  HEAD's). The lead writes the baseline manifest: the SHA-256, by path, of every file the workflow's agents
  may read, namely every tracked file at HEAD (code, governing documents and the CLAUDE.md imports alike)
  except the active packet and the archives (`archive/` and `archive2/`, 647 tracked files: invisible, so
  no agent may read them, and a read of one is outside the frozen basis and stops its chain); every
  untracked file a prompt names (the notes, packets and receipts under
  `data/` that it cites, and the tools in `B/workflow-tools/`); and the instruction files outside the
  repository that reach an agent (the rehearsal names them, §4). Every prompt carries HEAD, the manifest's
  path and SHA-256 and the packet revision; the script receives the manifest's entries in `args`. Each
  agent has named required inputs: the instruction files, which reach it in its instructions rather than
  through Read (the repository's `CLAUDE.md`, its six imports and the outside files the manifest lists),
  and the files its prompt names, the modules holding the units it names included (found with the AST
  locator at the pinned HEAD). Its prompt lists them, the script holds the same list (`REQUIRED`) and
  refuses to start when the manifest lacks one, and a return that leaves one out ends its chain
  INCOMPLETE. An agent's first step, before any other read and any edit, is to check HEAD and to hash its
  required inputs; it hashes each further input file before reading it, and stops as `stale_input` on any
  mismatch or on an input the manifest lacks. Files written during the workflow (the agent's own, and those named in an upstream
  return inlined in its prompt: attempt directories, notes, a diff, receipts, new files) are not inputs:
  they are not in the manifest and go in no `source_hashes`, except the verifier's copies of the
  candidate's changed files after applying. While a workflow runs, the lead edits no file the manifest
  lists.
- **Worktree agents:** `isolation: 'worktree'`. Run from the worktree root with `PYTHONPATH=<worktree>/src`
  and the main tree's `.venv/bin/python`, after `B/workflow-tools/import_proof.py <worktree>`, which exits
  non-zero unless `knee` and `run_interiors` both import from the worktree (the editable install otherwise
  imports the main tree's `src`). The runner's ROOT is its own file's parent's parent, so in a worktree
  every default built on it points at a tree with no data: a worktree has no `data/`, so files under it
  are read by their absolute paths in the main tree, and every path is passed explicitly (`--root
  <main>/data/raw`, `--run` and `--main-run` inside the attempt directory, accepted receipts by absolute
  path). Candidate CLI runs are serial (`--workers 1`). Agents run the tests and the gate's static checks,
  never its Sonar step: one server holds one project history, and analysing a candidate's tree there would
  make its latest analysis, which the lead's gate prints and reads, describe code that was never
  integrated. Parallel CLI runs and the full gate are the
  lead's, in the main tree, after integration.
- **Candidates:** new files marked intent-to-add (`git add -N`, nothing committed), then `git diff` into
  `candidate.diff` with its SHA-256. The candidate reports the files it read as they were before any edit
  (`source_hashes`, against the baseline) and every file it changed, added or deleted as it is after its
  last edit (`candidate_hashes`, a deleted file as `deleted`: the candidate manifest); `files_changed` lists
  exactly those paths. The verifier, in its own fresh worktree, checks HEAD and the baseline before
  applying anything; then it checks the diff's digest, applies it, confirms every changed and new file is
  present and every deleted one absent, and hashes each: those hashes must equal the candidate manifest,
  and every unchanged file it reads must still equal the baseline. It re-runs the tests and makes its own
  real-CLI runs into its own attempt directory, comparing its receipts with the accepted epoch's and with
  the candidate's.
- **Returns and outcomes:** schema-checked JSON carrying head, packet revision, a completion state
  (`complete`, `partial`, `blocked`, `stale_input`) and the SHA-256 of every file read or changed, with
  facts and their evidence paths, inferences labelled, and not_done. A schema checks shape, not
  sufficiency, and the lead reads every return. The script itself checks every returned hash: a file the
  candidate changed must equal the candidate's own hash; any other file must equal the baseline; a path in
  neither is outside the frozen basis. Each chain ends in exactly one named outcome, decided in this order
  (a chain that threw is INCOMPLETE). For every return:
  1. no return (the agent was skipped, died or was stopped) → INCOMPLETE;
  2. a HEAD, packet revision or baseline hash unlike the pin, a path outside the frozen basis, or the
     agent's own `stale_input` → STALE_INPUT (re-pin and reissue);
  3. a completion other than `complete`, an attempt directory other than its own, or a required input
     with no hash → INCOMPLETE (diagnose and reissue).

  For a fact or candidate return:
  4. required content empty or inconsistent (no facts; a changed file without its hash, a hash for an
     unlisted file, a file listed as changed but equal to the baseline or deleted though the baseline
     lacks it; a malformed diff digest; no consumer call, test, run, comparison or import proof) →
     INCOMPLETE; otherwise the next agent launches.

  For a verifier return:
  5. a file after applying unlike the candidate manifest, a violation, a missing item or an unsupported
     check → VERIFICATION_FAILED (fix or reissue the candidate);
  6. a required check, by its name, not reported supported (absent, or only not_checkable), no run of
     its own where one is required, or a changed file it did not hash after applying → INCOMPLETE;
  7. otherwise READY_FOR_LEAD_REVIEW.

  The run's outcome is the first, in the order STALE_INPUT, VERIFICATION_FAILED, INCOMPLETE,
  READY_FOR_LEAD_REVIEW, that any chain has. Each verifier's required checks have stable names, the same
  in its prompt, its schema and the script (the P2b verifier's: reconstructed_candidate,
  production_callers, context_reuse_and_invalidation, early_readers_preserved, tests, proof_study_run,
  bursa_study_run, receipt_comparisons). A not_checkable item neither fails nor counts as supported; an
  extra check, named `other`, satisfies no required one, though an unsupported one still fails.
  The fields not named here (the files read, inferences, frames, uncertainty) decide no outcome; the lead
  reads them. READY_FOR_LEAD_REVIEW is not acceptance, and a finished worker is not a verified candidate: only the
  lead's gate accepts. The review named three outcomes; STALE_INPUT is the lead's split from INCOMPLETE,
  because re-pinning is a different remedy from diagnosing a stopped agent. Area, coverage, pixel and
  timing figures are observations, never acceptance criteria.
- **Job table:** the lead records each workflow run (its run ID, task ID, packet revision, dependencies,
  output roots, the script's outcome and state: `PREPARING`, `RUNNING`, `RETURNED_UNREVIEWED`, `VERIFIED`,
  `ACCEPTED`, `NEEDS_RULE`, `STALE_INPUT`, `WITHDRAWN`, `FAILED`) in the active packet's single job table at
  launch, at each gate and on any stop. The scripts write nothing to it. The active packet is the one
  tracked file the lead writes while a workflow runs, and no agent reads it: FULL_BUILD_PLAN §0's
  session-start grounding and the packet are the lead's, and every prompt says so. Rohan's words that
  arrive while a workflow runs go into the packet first; the corrections record takes them at the next
  gate, and a premise they change is invalidated at once (below).
- **Invalidation (guide §7):** when a premise, contract or source a workflow depends on changes: stop it
  (TaskStop) and confirm it stopped; mark affected outputs ineligible where they sit (`WITHDRAWN.md` or
  `STALE_INPUT.md`); invalidate the reviews and tests derived from them; correct the packet (a new
  revision) and relaunch with a fresh attempt id. Every prompt carries HEAD, the manifest's digest and the
  packet revision, and a dependent prompt inlines its inputs, so a changed source, contract or upstream
  result changes the prompt: a resume cannot serve a stale cached result.
- **Single writer:** the lead integrates one candidate at a time; a later candidate is rebased onto the
  integrated tree and re-verified before it is integrated.
- **Acceptance (plan §9, §15.3):** the lead integrates, runs the real CLI into new output roots,
  reconstructs every new native support from its address and inspects the actual DICOM frame, and
  compares receipts (equivalent refactors must match; intended scope or semantic changes get a full
  changed-output account). Then everything the checkpoint commits is written before the final gate: the
  kernel benchmarks' recording, refreshed from the integrated source when the increment changes what
  production hands a benchmarked kernel (the gate replays the stored recording and never refreshes it, and
  the first gate after a refresh compares a different call, so its memory figure is information, not a
  regression); the six statements; the MAP/RESOLVING acceptance record; and the active packet, which
  points to the final gate's log under `data/` instead of carrying its numbers. The final gate
  (`scripts/ci_local.sh`, Sonar included) runs last, on exactly that tree; the lead reads its whole output
  and advisories, and nothing tracked changes after it. An earlier gate run during integration is
  diagnostic only. The lead commits exactly that tree and pushes; the pre-push hook finds the gate's stamp,
  runs the secret scan and the advisory lockfile audit, and its whole output is read; then the GitHub gate
  run on the pushed commit, whose results go into the next revision (plan §9, step 6).

## 4. Preconditions (after approval, before W1)

1. Rohan's approval and his two decisions (§1); the route change in the guide and plan §10.
2. Copy `spans.py`, `callsites.py` and `assigned_names.py`, and write `import_proof.py` and the manifest
   writer, in `B/workflow-tools/`; create `B/workflows-20261018/`.
3. `consult-budget`; `anthropic-consult --check` (key readable; value never printed).
4. A clean tree (§3, source basis); pin HEAD; write the baseline manifest, which must list every agent's
   required inputs (the script refuses to start otherwise), and record its path, SHA-256 and HEAD in the
   active packet; open the job table.
5. The offline mock of the workflow's script: the mock takes the script's code block from this document
   itself and runs it with every agent's return mocked, case by case (`w1_mock.mjs`, §10). It checks the
   control flow only: which agents launch, and which outcome each chain and the run end in. Every later
   workflow's script gets its own mock before its launch.
6. The runtime rehearsal R0: a short workflow at W1's settings (Sonnet, xhigh), through the actual workflow
   runtime, before W1:
   - **worktree imports:** a worktree agent runs `import_proof.py`, the test suite and one serial proof CLI
     run with explicit paths, and reports any path the runner wrote under its worktree;
   - **stops:** agents told to return a blocked completion, a wrong HEAD, a wrong packet revision, a hash
     unlike the baseline, a return without one of its required hashes, a verifier violation and a verifier
     that leaves a required check unreported, each checked to end its chain with the outcome the mock
     gives; and an agent given an upstream return that names files written during the workflow
     (attempt directories, a diff, receipts, new files), checked not to end its chain STALE_INPUT;
   - **schemas:** one return that breaks its schema, to see what the runtime does with it;
   - **instructions:** each agent lists the instruction files its context names, path by path, and what it
     read before its task; the manifest's outside entries come from that list;
   - **permissions:** every command an agent runs (hashing, the worktree, `git diff` and `git apply`, the
     tests, the CLI) completes without a prompt it cannot answer;
   - **cancellation:** the lead stops the rehearsal while an agent runs (TaskStop), confirms that it
     stopped and that nothing from the stopped attempt is used, and relaunches with a fresh attempt id;
   - **context:** each agent's token use, read from the runtime's own records (the workflow's journal and
     agent transcripts), recorded; every one under a million (§3).

   What breaks is fixed in the scripts and packets, and the mock re-run, before W1.

## 5. The sequence

| Workflow | Plan task | Contracts (in → out) | Agents (all Sonnet, xhigh) | Ends at the lead gate |
|---|---|---|---|---|
| **W1** | P2b increment 2 (settled wiring) + P2a facts | M07 → M08 → M09/M20 (§14.4); P2a: M01–M04 facts toward M05 | 7: P2b trace; P2b candidate (worktree); P2b verifier (own worktree); P2a consumer trace + its verifier; P2a cheap-data picture packet + its verifier | G1: integrate P2b inc2; CLI epochs; inspect the changed axial anchor frames (AX11/12 where reached) and map/guide effects; gate; commit; push. Choose P2a's consumer; draft the region rule from the pictures with §1.1's statements; Codex (+ Fable if §1.2 is approved) |
| **W2** | Evidence refresh, owed items, P2a implementation | Re-check the six stopped wave-1 packets against the post-W1 source; HOW_TO_BUILD's owed items; P2a M05 → its consumer | 8: five refresh/verify agents (P3 trace; P4 sources and ACL/tibial sheets; P5 attachment frames; P6 posterior and medial frames; P7 runtime trace and profile) regenerating what W1 moved; an owed-item inventory (each "Still owed" item and the sagittal-meniscus adapter's ledger debt: done, with evidence from the current source, or open); P2a candidate (worktree) + verifier. P2a's verification covers dark tissue enclosed by brighter leg tissue, clipped scans, no or partial signal, nonfinite values, anisotropic and ragged tiles and malformed geometry | G2: integrate P2a (its scope passed into the chosen consumer before it computes); inspect the region on native frames; CLI; gate; commit; push. Read the refreshed P3 facts; decide the patella corridor and cavity scopes (semantic check + Codex [+ Fable]) |
| **W3** | P3 (+ the P7/P9 items it touches) | M07–M09, M14 → patella/recess native question; `name_the_joint`'s early leg; the undeclared `leg.identity` read | 5: patella+joint candidate (worktree); recess candidate (worktree; rebased on the first after integration and re-verified); two verifiers; one P4 evidence-sheet update for the context P3 changes | G3: integrate sequentially; CLI; inspect; gate; commit; push. Draft P4's general source-eligibility rule and the ACL AX/COR and tibial AX rules; Codex (one consult, every rule with its full payload) + Fable (one reading per rule) |
| **W4** | P4 compartment + P9 lineage | F08, F09, F10 eligibility → M19/M20; the generic observation lineage | 8: source-eligibility candidate (shared, one owner); ACL candidate (both views: it encodes the reviewed ACL rule only, reusing a shared primitive (source validation, slab profiles, map guide, source window, the single offer) only where that rule names it, never PCL's selector); tibial-cartilage AX candidate; lineage candidate (the conversion/offer declaration made generic over the real family call, replacing the four-family hardcoded one, with the sagittal-meniscus adapter's ledger debt); four verifiers | G4: integrate one at a time; CLI; inspect every changed frame; gate; commit; push. **P4 family-wave sheets to Rohan.** Draft the 10 P5 rules; Codex + Fable |
| **W5a** | Shared readers for P5/P6 | Only where two or more reviewed rules name the same measurement operation; may be empty | ≤4: one candidate per shared reader (worktree) + a verifier | G5a: integrate (existing PCL/meniscus outputs reproduced exactly where they move onto a shared reader); gate; commit; push |
| **W5b** | P5 attachments | F11–F15 missing views → M19/M20 | 8: five object adapters (MCL, LCL, popliteus, ITB, biceps), three verifiers (grouped) | G5b: integrate one object at a time; CLI; inspect; gate; commit; push. **P5 family-wave sheets to Rohan.** Draft the F21/F24/F25 rules (both gastrocnemius heads, popliteal artery and vein, bursa); Codex + Fable |
| **W6a** | P6 posterior/medial, part 1 | F21, F24, F25 SAG/COR | 6: three object adapters + three verifiers | G6a: integrate; CLI; inspect; gate; commit; push. Draft the F22/F23 rules (semimembranosus, semitendinosus, gracilis, sartorius); Codex + Fable |
| **W6b** | P6 posterior/medial, part 2 | F22, F23 SAG/COR | 6: three adapters (semimembranosus + semitendinosus sharing their dark-body readings; gracilis; sartorius) + three verifiers | G6b: integrate; CLI; inspect; gate; commit; push. **P6 family-wave sheets to Rohan** |
| **W7** | P7 remaining older consumers | Each expensive caller → an explicit consumed scope or a recorded reason it needs broader work | ≤8: candidates grouped by consumer (fat-pad candidate reads; own-slice ACL/LCL/biceps/retinacula; joint/tendon planes; native axial territory; posterior lumen/corridor; muscle opening; the three `dark_bands` callers) + verifiers, split into two workflows if needed | G7: per consumer, the scope chosen by the lead (semantic check + Codex [+ Fable]); integrate; changed-output account; CLI; inspect; gate; commit; push |
| **W8** | P8 + P9 closure | Catalogue from production definitions; marrow's output address (F04); residual lineage; shared profile/merge/geometry where semantics match; digests once; persistence | 8: catalogue facts; marrow wiring; residual lineage; shared profiles/merges; digests/persistence; three verifiers | G8: equivalent refactors reproduce receipts exactly; the marrow address is an adjudicated new output; gate; commit; push |
| **W9** | P10 hot kernels | Reprofiled residual work → equivalent kernels | ≤6: one real-CLI profile; two or three kernel candidates with reference twins and equality tests; verifiers | G9: a kernel is kept only if its outputs are identical; paired whole-operation timing; gate; commit; push |
| **W10** | P11 verification | The frozen operation's outputs → per object and orientation: identified / abstained / wrong, uninspected explicit; the owed-item inventory closed (each item shown done with evidence, or carried open); every ordered pair vector resolved or a named partial endpoint; whole-operation cost and fallback accounting (visited pixels and windows, requests, misses and handoffs, fallback work, retained bytes, time and memory) | ≤8: auditors by family reading receipts and addressed images; a completeness critic (the catalogue against every requested concept and view); a source/receipt/address auditor | G10: the lead runs serial, parallel, public and the labelled cohort and the gate; accepts; writes the recognition-completion record; commits; pushes; reports to Rohan |
| **W11** | P12 preparation + P13 preparation | `what_an_object_is.md` §§7, 13 and the retained measurements → what the primary text settles for the MRI place/depth/bank/support layout and what it leaves open; the typed object interface and the twelve documented condition relationships | 3: thesis-section facts; retained-measurement inventory; object-interface and condition-relationship inventory | G11: the lead writes the contract and records the interface and relationships; Codex; a step the text leaves unspecified goes to Rohan |
| **W12** | P12 implementation | What the contract settles → the exact encoding, written from retained measurements | ≤4: candidates with tests of exact bundle, decode and subtraction, order invariance, layout compatibility, silent banks and physical support ownership; verifiers | G12: integrate; gate; commit; push. P13 waits for Rohan's specification; packaging and submission are later requested actions |

Between gates the lead prepares the next workflow's packets while verifiers run, never racing two
implementations of the same unit. Every candidate touches the 23k-line runner, so family logic goes in
modules with thin call-site wiring, and the lead integrates sequentially.

## 6. Per-workflow FORBIDDEN SUBSTITUTIONS (in each packet)

- **P2b inc2:** no erosion or filtering of source sections; no change aimed at AX14's calibration or any
  core size; no repeated whole-study convergence loop; no recognition-rule edits; name the two actual
  consumer calls; keep the bootstrap context where earlier readers need it.
- **P2a facts:** the question is a useful region for a chosen real consumer, available before that
  consumer computes. Do not compute or report region area fractions, tile-coverage shares or
  "lens-leg outside" shares as findings; do not use the lens's own leg as a reference for a region meant
  to precede the lens; do not propose, test or rank any tile or threshold rule; do not read or cite the
  withdrawn `p2a-regions-WITHDRAWN-20261018` packet. Report consumers, their inputs, timing and current
  scope, the cheap values computed before each, and the raw native frames with those cheap readings drawn
  as they are. This restriction belongs to the fact packet, which has no region to measure yet; it is not
  a ban on counts. Once the lead has chosen the consumer and the region, the implementation reports the
  actual places, tiles and context it queries (plan §5, P2a; guide §7), and no area figure, small or
  large, decides usefulness.
- **P2a implementation:** encode exactly the lead's chosen region rule; pass its scope into the consumer
  before it computes (masking afterwards does not count); keep unknown and enclosed dark tissue; count real
  visited work, not a box.
- **P3:** consume the supplied context; no second bone naming for calibration; broaden only for the named
  missing prerequisite; never run the full frame after a local success.
- **P4–P6 adapters:** encode only the lead's reviewed rule on existing shared measurements; a shared
  primitive is reused only where that rule names it, and no family's selector is carried into another's
  (the ACL is not the PCL); no new threshold, variant leaderboard or per-study patch; no promotion of a
  preview; native support kept separate from projected or laid rows; ties, partial scope, measured-empty
  and unavailable named.
- **P7:** each scope is the lead's; masking a full-frame result afterwards is not targeting; a smaller
  first read followed by a redundant broad one is reported, not hidden.
- **P8/P9/P10:** equivalent changes reproduce outputs exactly; no deleted readings, no fake consumers, no
  default-off retention flags; status codes translated explicitly, never merged by number.
- **The gate's Sonar step:** a deliberate construct Sonar misreads gets `# NOSONAR(<rule key>)` on its
  line (nothing may follow it) and its reason in a comment just above; a real finding is fixed. No
  blanket suppression and no rule disabled to turn the gate green.
- **Every workflow:** the guide's §10 failure cases are checked against each draft prompt before launch.

## 7. W1, drafted in full (for review; not run)

```js
export const meta = {
  name: 'rsna-w1-p2b-inc2-and-p2a-facts',
  description: 'P2b increment 2 wiring candidate with an independent check, and P2a fact packets; no production edits',
  phases: [
    { title: 'Facts', detail: 'P2b consumer trace; P2a consumer trace and cheap-data picture packet' },
    { title: 'Candidate', detail: 'P2b increment 2 in an isolated worktree' },
    { title: 'Verify', detail: 'independent checks of the candidate and of each fact packet' },
  ],
}

const ROOT = '/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee'
// The manifest names a file under data/ by its path relative to ROOT; B_REL is the plan's readings root so named.
const B_REL = 'data/readings/collapse-20261017/full-build/targeted-compute-20261018'
const B = ROOT + '/' + B_REL
const TOOLS_REL = B_REL + '/workflow-tools'
const TOOLS = ROOT + '/' + TOOLS_REL
const PIN = args && args.sourcePin
const isHex = (n, value) => new RegExp('^[0-9a-f]{' + n + '}$').test(String(value))
if (!PIN || !isHex(40, PIN.head) || !PIN.manifest || !isHex(64, PIN.manifestSha256) || !PIN.entries ||
    typeof PIN.entries !== 'object' || Object.keys(PIN.entries).length === 0 || !args.attempt || !args.packetRevision) {
  throw new Error('W1 needs args = { sourcePin: { head (40 hex), manifest, manifestSha256 (64 hex), entries: { path: sha256 } }, attempt, packetRevision } from the lead')
}
const REVISION = String(args.packetRevision)
const SONNET = { model: 'sonnet', effort: 'xhigh' }
const PROOF = '1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149'
const BURSA = '1.2.826.0.1.3680043.8.498.13335129881737731410081002627729200903'
const ACCEPTED_REL = B_REL + '/p2b-bone-context-20261018/repair/proof-bursa'
const ACCEPTED = ROOT + '/' + ACCEPTED_REL
const dirOf = (packet) => B + '/workflows-20261018/w1/' + packet + '/attempt-' + args.attempt
const has = (object, key) => Object.prototype.hasOwnProperty.call(object, key)
// The instruction files reach an agent in its instructions, not through Read, so each agent hashes them first.
const INSTRUCTIONS = ['CLAUDE.md', 'AGENTS.md', 'docs/THEORY_OF_THE_CASE.md', 'docs/HOW_TO_BUILD.md', 'docs/FULL_BUILD_PLAN.md',
  'docs/conversations/2026-10-13-the-thesis.md', 'docs/conversations/2026-10-18-anatomical-priors-and-targeted-compute.md']

// Each agent's required inputs (§3): the instruction files, those outside the repository the manifest lists
// by absolute path, and the files its prompt names, the modules holding the units it names included (found
// with the AST locator at the pinned HEAD). Any other file an agent reads it hashes as it reads it, and that
// hash is compared with the baseline too; a required one may not be left out.
const OUTSIDE = Object.keys(PIN.entries).filter((path) => path.startsWith('/'))
const LOCATORS = ['spans.py', 'callsites.py', 'assigned_names.py'].map((name) => TOOLS_REL + '/' + name)
const EVERY = [...INSTRUCTIONS, ...OUTSIDE, 'docs/GROUNDING_AND_WORKER_GUIDE.md', ...LOCATORS, 'scripts/run_interiors.py']
const P2B_READS = [...EVERY, B_REL + '/p2b-bone-context-20261018/README.md', B_REL + '/p2b-bone-context-20261018/verification.md']
const P2B_RUNS = [...P2B_READS, TOOLS_REL + '/import_proof.py', 'scripts/compare_receipts.py',
  ACCEPTED_REL + '/interiors/receipt.json', ACCEPTED_REL + '/main/receipt.json']
const P2A_CONSUMERS = [...EVERY, 'src/knee/objects/interiors.py', 'src/knee/objects/assignments.py', 'src/knee/collapse/profile.py']
const P2A_PICTURES = [...EVERY, 'src/knee/study/corpus.py', 'src/knee/study/series.py', 'src/knee/collapse/noise.py',
  'src/knee/collapse/squint_stack.py', 'src/knee/collapse/physical.py', 'src/knee/objects/assignments.py']
const REQUIRED = {
  'p2b-trace': P2B_READS, 'p2b-candidate': P2B_RUNS, 'p2b-verify': P2B_RUNS,
  'p2a-consumers': P2A_CONSUMERS, 'p2a-consumers-verify': P2A_CONSUMERS,
  'p2a-pictures': P2A_PICTURES, 'p2a-pictures-verify': P2A_PICTURES,
}
const unlisted = [...new Set(Object.values(REQUIRED).flat())].filter((path) => !has(PIN.entries, path))
if (unlisted.length) throw new Error('W1 needs every required input in the manifest, which lacks ' + unlisted.join(', '))
const inputsOf = (stage) => 'REQUIRED INPUTS: ' + REQUIRED[stage].join(', ') +
  '. Hash each of them in your first step and return each in source_hashes; a return that leaves one out is incomplete.'

// Each chain ends in exactly one named outcome, and the run in the first of these, in this order, that any
// chain has (§3). Their remedies differ: re-pin and reissue; fix or reissue the candidate; diagnose and
// reissue. READY_FOR_LEAD_REVIEW is not acceptance: only the lead's gate accepts.
const OUTCOMES = ['STALE_INPUT', 'VERIFICATION_FAILED', 'INCOMPLETE', 'READY_FOR_LEAD_REVIEW']
const ended = (status, stage, reasons) => ({ status, stage, reasons })

// §3, steps 1-3, for every return: present; HEAD, packet revision and every hash as pinned (a file the
// candidate changed is the verifier's to compare with the candidate's own hash; any other must equal the
// baseline; a path in neither is outside the frozen basis); complete, in its own attempt directory, with a
// hash for each of its required inputs. The outcome, or null when it passes.
function screened(stage, r, changed) {
  if (!r) return ended('INCOMPLETE', stage, ['no return: the agent was skipped, died or was stopped'])
  const notDone = r.not_done || []
  const stale = []
  if (r.head !== PIN.head) stale.push('head ' + r.head + ' is not the pinned ' + PIN.head)
  if (String(r.packet_revision) !== REVISION) stale.push('packet revision ' + r.packet_revision + ' is not ' + REVISION)
  for (const entry of r.source_hashes || []) {
    if (changed && has(changed, entry.path)) continue
    if (!has(PIN.entries, entry.path)) stale.push(entry.path + ' is outside the frozen basis')
    else if (PIN.entries[entry.path] !== entry.sha256) stale.push(entry.path + ' differs from the baseline')
  }
  if (r.completion === 'stale_input' && stale.length === 0) stale.push(...(notDone.length ? notDone : ['the agent reported stale input']))
  if (stale.length) return ended('STALE_INPUT', stage, stale)
  if (r.completion !== 'complete') return ended('INCOMPLETE', stage, ['completion is ' + r.completion, ...notDone])
  if (r.attempt_dir !== dirOf(stage)) return ended('INCOMPLETE', stage, ['attempt directory ' + r.attempt_dir + ' is not ' + dirOf(stage)])
  const hashed = new Set((r.source_hashes || []).map((entry) => entry.path))
  const unhashed = REQUIRED[stage].filter((path) => !hashed.has(path))
  if (unhashed.length) return ended('INCOMPLETE', stage, unhashed.map((path) => 'required input ' + path + ' has no hash'))
  return null
}

// §3, step 4, for a fact return.
function factsChecked(stage, r) {
  return screened(stage, r, null) || (r.facts.length === 0 ? ended('INCOMPLETE', stage, ['no facts returned']) : null)
}

// §3, step 4, for the candidate: its manifest names exactly the files it changed, each really changed, and
// its return carries what the verifier and the lead need.
function candidateChecked(stage, c) {
  const early = screened(stage, c, null)
  if (early) return early
  const reasons = []
  const manifest = {}
  for (const entry of c.candidate_hashes) manifest[entry.path] = entry.sha256
  const listed = new Set(c.files_changed)
  if (listed.size === 0) reasons.push('files_changed is empty')
  for (const path of listed) if (!has(manifest, path)) reasons.push(path + ' is listed as changed without a hash')
  for (const path of Object.keys(manifest)) {
    if (!listed.has(path)) reasons.push(path + ' has a hash but is not listed as changed')
    else if (has(PIN.entries, path) && PIN.entries[path] === manifest[path]) reasons.push(path + ' is listed as changed but equals the baseline')
    else if (manifest[path] === 'deleted' && !has(PIN.entries, path)) reasons.push(path + ' is listed as deleted but the baseline has no such file')
  }
  if (!isHex(64, c.diff_sha256)) reasons.push('diff_sha256 is not a SHA-256')
  for (const key of ['consumer_calls', 'tests', 'runs', 'comparisons']) if (c[key].length === 0) reasons.push(key + ' is empty')
  if (!String(c.import_proof).trim()) reasons.push('import_proof is empty')
  return reasons.length ? ended('INCOMPLETE', stage, reasons) : null
}

// §3, steps 5-7, for a verifier: what it found failing, then whether each required check, by its name, is
// reported supported, then ready. A not_checkable item neither fails nor counts as supported; an extra check
// (named "other") satisfies no required one, though an unsupported one still fails.
function verified(stage, v, changed, need) {
  const early = screened(stage, v, changed)
  if (early) return early
  const failed = []
  if (changed) {
    for (const entry of v.source_hashes) {
      if (has(changed, entry.path) && changed[entry.path] !== entry.sha256) failed.push(entry.path + ' after applying is not the candidate\'s file')
    }
  }
  failed.push(...v.violations, ...v.missing.map((item) => 'missing: ' + item))
  failed.push(...v.checked.filter((item) => item.verdict === 'unsupported').map((item) => 'unsupported: ' + item.check + ': ' + item.item))
  if (failed.length) return ended('VERIFICATION_FAILED', stage, failed)
  const short = []
  for (const name of need.checks) {
    if (!v.checked.some((item) => item.check === name && item.verdict === 'supported')) short.push('required check ' + name + ' is not reported supported')
  }
  if (need.ownRuns && v.own_runs.length === 0) short.push('no run of its own')
  if (changed) {
    for (const path of Object.keys(changed)) {
      if (!v.source_hashes.some((entry) => entry.path === path)) short.push(path + ' was not hashed after applying')
    }
  }
  return short.length ? ended('INCOMPLETE', stage, short) : ended('READY_FOR_LEAD_REVIEW', stage, [])
}

const COMMON = [
  'You are a worker for the lead (Claude, the main session) of RSNA_Knee at ' + ROOT + ': a classical-AI knee-MRI recognition build, deliberately with no machine learning.',
  "Rohan's words and docs/THEORY_OF_THE_CASE.md govern. docs/FULL_BUILD_PLAN.md is the work order and holds the contracts (§§14–15); docs/GROUNDING_AND_WORKER_GUIDE.md governs your role. You return facts or a candidate. You do not decide what Rohan means, choose an anatomical rule, a threshold, a sample meaning or a scope, or accept anything. If finishing would need such a choice, stop and return it named in not_done.",
  "FULL_BUILD_PLAN §0's session-start grounding and the active packet (docs/work/current/README.md) are the lead's: do not perform that grounding and never read the packet. Read whole the units this prompt names and any unit you need to understand them.",
  'SOURCE BASIS: HEAD ' + PIN.head + '; packet revision ' + REVISION + '; manifest ' + PIN.manifest + ' (SHA-256 ' + PIN.manifestSha256 + '): the SHA-256 of every input file you may read, a tracked file by its path relative to the repository root (' + ROOT + ', or your worktree\'s root, which holds the same files), a file under data/ by its path relative to ' + ROOT + ', a file outside the repository by its absolute path. Files written during this workflow are not inputs and are not in the manifest: your own, and those named by any agent\'s return inlined in this prompt (its attempt directory, notes, diff, receipts, worktree and new files). Your first step, before any other read and any edit: check that HEAD is ' + PIN.head + ' (the full 40 characters of git rev-parse HEAD), then hash with shasum -a 256, and compare with the manifest, every file under REQUIRED INPUTS at the end of this prompt: the instruction files among them reach you in your instructions rather than through Read, and the rest are the files this prompt names, the modules holding the units it names included. Hash each further input file before you read it; the study images, which the runner reads, are not hashed. On any mismatch, or an input file the manifest does not list, stop and return completion "stale_input" naming each one.',
  'Return in source_hashes every input file you hashed, once, by its manifest path, with its SHA-256 as you read it; files written during this workflow never go in source_hashes unless your role below says so (the verifier reports its copies of the candidate\'s changed files after applying). Return head as the full 40-character SHA, packet_revision exactly as given, and attempt_dir exactly as this prompt gives it.',
  'Read whole units only (whole functions, classes, sections, documents) with the Read tool. Locate code with python3 -I ' + TOOLS + '/spans.py <tree> <names>, ' + TOOLS + '/callsites.py <tree> <names> and ' + TOOLS + '/assigned_names.py <tree> <names>, where <tree> is the tree you work in. Never use the Grep tool, grep, rg, head, tail, sed, awk, cut, wc, jq, pipes or any text search. Do not read archive/ or archive2/.',
  'Keep your context well under a million tokens (a compaction would lock you): read whole units, not a whole file of thousands of lines unless the file is the unit, and read a long output once. If your task would need more, stop and return completion "partial", naming what is left in not_done.',
  'WRITES: your artifacts (notes, logs, runs, pictures, diffs) go only in your attempt directory, which must not exist before you start (if it does, stop and return completion "blocked"); code edits, where your role allows them, go only in your own worktree. Never edit the main tree, canonical outputs or another agent\'s files. Never commit, push, reset or clean. Never run scripts/ci_local.sh or scripts/sonar_local.py: the Sonar step is the lead\'s.',
  'Report facts with the evidence path you measured or read, inferences labelled as yours, and not_done for anything not done or not measured. Never state the outcome of something you did not measure. Never treat one construction\'s failure as a verdict on a capability. Never attribute words to Rohan unless you quote a file that records them.',
].join(' ')

const WORKTREE = [
  'You work in an isolated git worktree cut from HEAD; call its root <wt>. Run everything from <wt> with PYTHONPATH=<wt>/src and the interpreter ' + ROOT + '/.venv/bin/python.',
  'Before any test or run, run ' + TOOLS + '/import_proof.py <wt> under that same environment and keep its output; it exits non-zero unless knee and run_interiors both import from <wt>. If it fails, stop and return completion "blocked".',
  'The runner\'s ROOT is its own file\'s parent\'s parent, so in a worktree every default built on it points at a tree with no data: <wt> has no data/ folder. Read files under data/ by their absolute paths in ' + ROOT + ', and pass every path explicitly: --root ' + ROOT + '/data/raw, --run and --main-run inside your attempt directory, and accepted receipts by absolute path. Run the CLI with --workers 1. List in your return any path the runner wrote under <wt> by itself.',
].join(' ')

const SHA256 = { type: 'string', pattern: '^([0-9a-f]{64}|deleted)$' }
const HASHES = { type: 'array', minItems: 1, items: { type: 'object', properties: { path: { type: 'string', minLength: 1 }, sha256: SHA256 }, required: ['path', 'sha256'] } }
const BASIS = {
  head: { type: 'string', pattern: '^[0-9a-f]{40}$' },
  packet_revision: { type: 'string', minLength: 1 },
  completion: { type: 'string', enum: ['complete', 'partial', 'blocked', 'stale_input'] },
  source_hashes: HASHES,
  attempt_dir: { type: 'string', minLength: 1 },
  not_done: { type: 'array', items: { type: 'string' } },
}
const BASIS_KEYS = ['head', 'packet_revision', 'completion', 'source_hashes', 'attempt_dir', 'not_done']
const STRINGS = { type: 'array', items: { type: 'string' } }
const STATEMENTS = { type: 'array', items: { type: 'object', properties: { statement: { type: 'string', minLength: 1 }, evidence: { type: 'string', minLength: 1 } }, required: ['statement', 'evidence'] } }

const FACTS = { type: 'object', properties: { ...BASIS, files: STRINGS, facts: STATEMENTS, inferences: STRINGS }, required: [...BASIS_KEYS, 'files', 'facts', 'inferences'] }

const CANDIDATE = { type: 'object', properties: {
  ...BASIS, worktree: { type: 'string', minLength: 1 }, diff_path: { type: 'string' }, diff_sha256: { type: 'string', pattern: '^[0-9a-f]{64}$' },
  candidate_hashes: HASHES, files_changed: STRINGS, consumer_calls: STRINGS, tests: STRINGS, import_proof: { type: 'string' },
  runs: STRINGS, comparisons: STRINGS, changed_frames: STRINGS, uncertainty: STRINGS,
}, required: [...BASIS_KEYS, 'worktree', 'diff_path', 'diff_sha256', 'candidate_hashes', 'files_changed', 'consumer_calls', 'tests', 'import_proof', 'runs', 'comparisons', 'changed_frames', 'uncertainty'] }

// A verifier's schema names its required checks; any further check is "other".
const verdictsFor = (checks) => ({ type: 'object', properties: {
  ...BASIS,
  checked: { type: 'array', items: { type: 'object', properties: { check: { type: 'string', enum: [...checks.map(([name]) => name), 'other'] }, item: { type: 'string', minLength: 1 }, verdict: { type: 'string', enum: ['supported', 'unsupported', 'not_checkable'] }, evidence: { type: 'string', minLength: 1 } }, required: ['check', 'item', 'verdict', 'evidence'] } },
  own_runs: STRINGS, violations: STRINGS, missing: STRINGS,
}, required: [...BASIS_KEYS, 'checked', 'own_runs', 'violations', 'missing'] })

// Each verifier's required checks, by stable name, with what each must establish (§3, step 6).
const P2B_CHECKS = [
  ['reconstructed_candidate', 'the diff has the candidate\'s SHA-256, applies with git apply, and every changed, new and deleted file matches the candidate manifest'],
  ['production_callers', 'every caller and sibling route of each changed function, read whole, still receives what it needs'],
  ['context_reuse_and_invalidation', 'a changed leg context misses every cache the leg reaches (leg_on and the coarse context) and an identical context reuses it'],
  ['early_readers_preserved', 'every reader that runs before refine_leg still receives the early leg'],
  ['tests', 'after the import check, the candidate\'s focused tests and the full test suite pass in your worktree'],
  ['proof_study_run', 'your own serial real-CLI run on the proof study, into your attempt directory, completed'],
  ['bursa_study_run', 'your own serial real-CLI run on the bursa study, into your attempt directory, completed'],
  ['receipt_comparisons', 'your receipts compared with the accepted repair epoch\'s and with the candidate\'s (scripts/compare_receipts.py), every difference listed'],
]
const operation = (name, unit) => [name, 'the packet\'s facts about ' + unit + ' (what it reads, when it runs in measure_study, the scope it receives, the values computed before it, the decision that consumes its output), re-derived from the whole units and the evidence it cites']
const P2A_CONSUMER_CHECKS = [
  operation('lens_of_and_interior_regions', 'lens_of and interior_regions'),
  operation('dark_bands', 'dark_bands in src/knee/objects/assignments.py (the reader whose callers are assign_plane, twin_reading and joint_plane, not the function of that name in interiors.py)'),
  operation('thick_parts_and_muscle_opening', 'thick_parts and the muscle opening (muscle_bodies)'),
  operation('local_lightness', 'local_lightness'),
  operation('enclosed_darkness', 'whole-frame enclosed_darkness'),
  operation('block_medians', 'block_medians'),
  ['forbidden_substitutions', 'no statement in the packet breaks the forbidden substitutions above or presents an inference as a measurement'],
]
const P2A_PICTURE_CHECKS = [
  ['manifest_against_frames', 'every picture\'s manifest entry (series, slice, DICOM path, frame geometry, orientation) matches the actual frame, nothing transposed'],
  ['cheap_readings_proof', 'the cheap readings drawn on one proof frame, re-derived with your own script file'],
  ['cheap_readings_bursa', 'the cheap readings drawn on one bursa frame, re-derived with your own script file'],
  ['forbidden_substitutions', 'no picture or statement draws or reports a derived region, an area or coverage share, or a tile or threshold rule'],
]
const checksOf = (checks) => 'REQUIRED CHECKS: one entry each in checked, its check field set to the name (any further check goes in as "other"): ' +
  checks.map(([name, meaning]) => name + ', ' + meaning).join('; ') + '.'
const namesOf = (checks) => checks.map(([name]) => name)

const P2B_PACKET = [
  'TASK: FULL_BUILD_PLAN P2b increment 2 (settled wiring; guide §5 example). Read whole: plan §1.2, §14.4, the P2b section, and the packet notes ' + B + '/p2b-bone-context-20261018/README.md and ' + B + '/p2b-bone-context-20261018/verification.md.',
  'INTENT: offer the refined leg (refine_leg, already published once after name_the_bones) to the two remaining consumers that run after it, axial_bone_planes (inside build_study_map) and fibula_key_planes, at the right time, keeping the early leg wherever an earlier reader needs it.',
  'CONTRACTS: M07 → M08 → M09/M20. CONSUMER: the bones\' and fibula\'s axial key planes, which set the common map\'s axial zero.',
  'FORBIDDEN SUBSTITUTIONS: no erosion or filtering of source sections; nothing aimed at AX14\'s calibration or any core size; no repeated whole-study convergence loop; no recognition-rule edits; no change beyond these consumers\' arguments, order and cache keys.',
].join(' ')

async function p2bChain() {
  const trace = await agent(COMMON + ' ' + P2B_PACKET + ' ROLE: facts. You work in the main tree and change no code. Attempt directory: ' + dirOf('p2b-trace') + '. Read whole axial_bone_planes, fibula_key_planes, build_study_map, refine_leg, leg_on, native_femur_coarse_context, measure_study and every caller of the first three; report the call order, which leg each receives now, every cache key that would see the leg, and every reader that must keep the early leg. ' + inputsOf('p2b-trace'), { ...SONNET, label: 'p2b-trace', phase: 'Facts', schema: FACTS })
  const t = factsChecked('p2b-trace', trace)
  if (t) return { ...t, trace, candidate: null, verdict: null }
  const candidate = await agent(COMMON + ' ' + WORKTREE + ' ' + P2B_PACKET + ' ROLE: implement the settled wiring. Attempt directory: ' + dirOf('p2b-candidate') + '. The trace: ' + JSON.stringify(trace) + ' Make the change in your worktree; add focused tests (context identity reaches both consumers; early-leg readers unchanged; a changed context misses, an identical context reuses); after the import check run them and the full test suite; run the real CLI on the proof (' + PROOF + ') and bursa (' + BURSA + ') studies into your attempt directory, and compare each receipt with the accepted repair epoch\'s (' + ACCEPTED + '/interiors/receipt.json and ' + ACCEPTED + '/main/receipt.json) using scripts/compare_receipts.py. Report in source_hashes the files you read as they were before any edit. Mark new files intent-to-add (git add -N <file>; nothing is committed), write git diff to candidate.diff in your attempt directory and record its SHA-256; after your last edit, hash every file you changed, added or deleted into candidate_hashes (a deleted file as "deleted": the candidate manifest) and list exactly those paths in files_changed. Name the two consumer calls; list every changed record and the axial frames (series, slice) whose anchors moved. ' + inputsOf('p2b-candidate'), { ...SONNET, label: 'p2b-candidate', phase: 'Candidate', schema: CANDIDATE, isolation: 'worktree' })
  const c = candidateChecked('p2b-candidate', candidate)
  if (c) return { ...c, trace, candidate, verdict: null }
  const changed = {}
  for (const entry of candidate.candidate_hashes) changed[entry.path] = entry.sha256
  const verdict = await agent(COMMON + ' ' + WORKTREE + ' ' + P2B_PACKET + ' ROLE: independent verifier. Attempt directory: ' + dirOf('p2b-verify') + '. The candidate claims: ' + JSON.stringify(candidate) + ' In your own fresh worktree, make the SOURCE BASIS checks first, before applying anything. Then check that ' + candidate.diff_path + ' has SHA-256 ' + candidate.diff_sha256 + ', apply it with git apply, confirm every changed and new file is present and every deleted one absent, and hash each: report those in source_hashes as they are after applying (a deleted file as "deleted"); they must equal the candidate manifest above. Every other file you read must still equal the baseline; report it as you read it. Read every changed unit whole and check it against §14.4 and the forbidden substitutions; after the import check run its tests and the full test suite; re-check every caller and sibling route of the changed functions; then make your own real-CLI runs on the proof and bursa studies into your attempt directory and compare your receipts with the accepted repair epoch\'s and with the candidate\'s (scripts/compare_receipts.py). Put each check in checked (supported, unsupported or not_checkable, with its evidence), anything that must block in violations, and anything the candidate lacks in missing. List the frames the lead must inspect. Give no anatomical verdict. ' + checksOf(P2B_CHECKS) + ' ' + inputsOf('p2b-verify'), { ...SONNET, label: 'p2b-verify', phase: 'Verify', schema: verdictsFor(P2B_CHECKS), isolation: 'worktree' })
  return { ...verified('p2b-verify', verdict, changed, { checks: namesOf(P2B_CHECKS), ownRuns: true }), trace, candidate, verdict }
}

const P2A_FRAME = [
  'TASK: FULL_BUILD_PLAN P2a (OPEN, required). Read whole plan §1.1, the P2a section, §14.2 rows M01–M05 and §15.1\'s P2a row first.',
  'The question is a useful leg/domain region for a chosen real expensive consumer, available before that consumer computes. The lead chooses the consumer and the region rule; you report facts.',
  'FORBIDDEN SUBSTITUTIONS: do not compute or report region area fractions, tile-coverage shares or shares of the lens\'s leg outside a region as findings; do not use the lens\'s own leg as a reference for a region meant to precede the lens; do not propose, test or rank any tile or threshold rule; do not read or cite ' + B + '/wave1-packets-20261018/p2a-regions-WITHDRAWN-20261018.',
].join(' ')

async function p2aConsumers() {
  const facts = await agent(COMMON + ' ' + P2A_FRAME + ' ROLE: facts. You work in the main tree and change no code. Attempt directory: ' + dirOf('p2a-consumers') + '. For each expensive per-slice operation that runs on the middle slices or native frames before any anatomical scope exists (start from lens_of/interior_regions, dark_bands in src/knee/objects/assignments.py, the reader whose callers are assign_plane, twin_reading and joint_plane (src/knee/objects/interiors.py has another function of that name), thick_parts and muscle opening, local_lightness, whole-frame enclosed_darkness, block_medians), read whole the operation and every caller, and report: what it reads, when it runs in measure_study, what scope it receives now, which values are already computed before it (finite and margin maps, background split, squint tiles and their bounds, availability), and what decision consumes its output. ' + inputsOf('p2a-consumers'), { ...SONNET, label: 'p2a-consumers', phase: 'Facts', schema: FACTS })
  const f = factsChecked('p2a-consumers', facts)
  if (f) return { ...f, facts, verdict: null }
  const verdict = await agent(COMMON + ' ' + P2A_FRAME + ' ROLE: independent verifier. You work in the main tree and change no code. Attempt directory: ' + dirOf('p2a-consumers-verify') + '. The packet returned: ' + JSON.stringify(facts) + ' Make each required check below from the whole units and the evidence the packet cites, each as an entry in checked (supported, unsupported or not_checkable, with its evidence); list in violations every statement that breaks the forbidden substitutions or presents inference as measurement, and in missing what the packet lacks. ' + checksOf(P2A_CONSUMER_CHECKS) + ' ' + inputsOf('p2a-consumers-verify'), { ...SONNET, label: 'p2a-consumers-verify', phase: 'Verify', schema: verdictsFor(P2A_CONSUMER_CHECKS) })
  return { ...verified('p2a-consumers-verify', verdict, null, { checks: namesOf(P2A_CONSUMER_CHECKS), ownRuns: false }), facts, verdict }
}

async function p2aPictures() {
  const facts = await agent(COMMON + ' ' + P2A_FRAME + ' ROLE: prepare evidence. You work in the main tree and change no code. Attempt directory: ' + dirOf('p2a-pictures') + '. Write your drawing script as a file in your attempt directory (never inline code). It adds the absolute path ' + ROOT + '/scripts to sys.path, imports run_interiors as run, opens the corpus with run.opened(Path("' + ROOT + '/data/raw")), reads each study with run.read_study(corpus, uid), and takes each series\' slice the run reads first (read selected_slice and the Series class whole before using them). For the proof and bursa studies, draw each such raw acquired frame and, beside it, the cheap readings that exist before the lens exactly as the runner computes them (the finite map, the margin, the background split as a two-level map, and the squint\'s tile bounds with each tile\'s median, minimum, maximum and coverage as numbers), with no derived region. Record every series, slice, DICOM path and frame geometry in a manifest. Report what each picture shows, and not_done for anything you could not draw. ' + inputsOf('p2a-pictures'), { ...SONNET, label: 'p2a-pictures', phase: 'Facts', schema: FACTS })
  const f = factsChecked('p2a-pictures', facts)
  if (f) return { ...f, facts, verdict: null }
  const verdict = await agent(COMMON + ' ' + P2A_FRAME + ' ROLE: independent verifier. You work in the main tree and change no code. Attempt directory: ' + dirOf('p2a-pictures-verify') + '. The packet returned: ' + JSON.stringify(facts) + ' Open each picture, check its manifest against the actual frames (geometry, slice, orientation, nothing transposed), re-derive the drawn cheap readings on one proof frame and one bursa frame with your own script file (your runs in own_runs), and list in violations every violation of the forbidden substitutions and in missing what the packet lacks. ' + checksOf(P2A_PICTURE_CHECKS) + ' ' + inputsOf('p2a-pictures-verify'), { ...SONNET, label: 'p2a-pictures-verify', phase: 'Verify', schema: verdictsFor(P2A_PICTURE_CHECKS) })
  return { ...verified('p2a-pictures-verify', verdict, null, { checks: namesOf(P2A_PICTURE_CHECKS), ownRuns: true }), facts, verdict }
}

const CHAINS = ['p2b', 'p2aConsumers', 'p2aPictures']
const results = await parallel([() => p2bChain(), () => p2aConsumers(), () => p2aPictures()])
const chains = {}
CHAINS.forEach((name, i) => {
  const r = results[i]
  chains[name] = r && OUTCOMES.includes(r.status) ? r : ended('INCOMPLETE', name, ['the chain threw or ended without an outcome'])
})
const outcome = OUTCOMES.find((status) => CHAINS.some((name) => chains[name].status === status))
log('W1 ' + outcome + ': ' + CHAINS.map((name) => name + ' ' + chains[name].status + ' at ' + chains[name].stage).join('; '))
return { outcome, pin: { head: PIN.head, manifestSha256: PIN.manifestSha256, packetRevision: REVISION, attempt: args.attempt }, chains }
```

Seven agents at most. Each chain stops at the first return that fails §3's checks and ends in one named
outcome; the run ends in one too. The offline mock runs this block, taken from this document, through 34
cases (§4, §10); it checks the control flow only. The lead reads every return and every picture before
G1, and records the run and its outcome in the job table; nothing from W1 is integrated or cited as
accepted until G1's own checks.

## 7a. R0, the runtime rehearsal (§4, step 6), drafted in full

R0 runs before W1 at W1's settings, in three parts chosen by `args.part`, each with its own fresh attempt id
and pinned manifest; it changes nothing in production. It reuses W1's checking functions, prompt rules and
schemas unchanged, adding to every return the instruction files the agent's context names, what it read
before its task, and any command refused or asking a permission it could not give.

- `runtime` (5 agents): a worktree agent runs the import check, the full test suite and one serial proof
  CLI run with every path explicit, and lists what anything wrote under its worktree; a rehearsal candidate
  makes a harmless edit that is never integrated (a comment line and a new docstring-only file), with its
  diff and candidate manifest, and an independent verifier applies it in its own worktree; one agent tries
  to break its schema (observed, no expected outcome); one agent is handed an upstream return naming files
  written during the workflow and must not end STALE_INPUT.
- `stops` (7 agents): each does the real first step, then returns with one deliberate deviation: blocked,
  a wrong HEAD, a wrong packet revision, a hash unlike the baseline, a missing required hash, a verifier
  violation, a verifier leaving a required check unreported. Each chain must end in the outcome §3 maps.
- `cancel` (1 agent): a long task the lead stops part-way (TaskStop), confirms stopped, marks its attempt
  `WITHDRAWN.md`, and relaunches with a fresh attempt id to completion.

The script returns each chain's expected and actual outcome and every mismatch. The lead reads every
return, records each agent's token use from the runtime's own records (§3's context rule), takes the
manifest's outside entries for W1 from the instruction files the agents list, and fixes what breaks in the
scripts and packets, re-running the mocks, before W1. Its offline mock is `r0_mock.mjs` in the setup's
evidence folder.

```js
export const meta = {
  name: 'rsna-r0-runtime-rehearsal',
  description: 'R0 before W1 (BUILD_WORKFLOWS §4): rehearse worktree imports, a candidate and its verifier, schema handling, instruction files, permissions, stops and cancellation through the real runtime; no production edits',
  phases: [
    { title: 'Runtime', detail: 'a worktree agent, a rehearsal candidate and its verifier, a schema break, an inlined upstream return' },
    { title: 'Stops', detail: 'agents told to return each stop case the checks must catch' },
    { title: 'Cancel', detail: 'one long agent, stopped by the lead and relaunched' },
  ],
}

const ROOT = '/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee'
// The manifest names a file under data/ by its path relative to ROOT; B_REL is the plan's readings root so named.
const B_REL = 'data/readings/collapse-20261017/full-build/targeted-compute-20261018'
const B = ROOT + '/' + B_REL
const TOOLS_REL = B_REL + '/workflow-tools'
const TOOLS = ROOT + '/' + TOOLS_REL
const PIN = args && args.sourcePin
const isHex = (n, value) => new RegExp('^[0-9a-f]{' + n + '}$').test(String(value))
const PARTS = ['runtime', 'stops', 'cancel']
if (!PIN || !isHex(40, PIN.head) || !PIN.manifest || !isHex(64, PIN.manifestSha256) || !PIN.entries ||
    typeof PIN.entries !== 'object' || Object.keys(PIN.entries).length === 0 || !args.attempt || !args.packetRevision ||
    !PARTS.includes(args.part)) {
  throw new Error('R0 needs args = { sourcePin: { head (40 hex), manifest, manifestSha256 (64 hex), entries: { path: sha256 } }, attempt, packetRevision, part (runtime, stops or cancel) } from the lead')
}
const REVISION = String(args.packetRevision)
const SONNET = { model: 'sonnet', effort: 'xhigh' }
const PROOF = '1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149'
const dirOf = (packet) => B + '/workflows-20261018/r0/' + packet + '/attempt-' + args.attempt
const has = (object, key) => Object.prototype.hasOwnProperty.call(object, key)
// The instruction files reach an agent in its instructions, not through Read, so each agent hashes them first.
const INSTRUCTIONS = ['CLAUDE.md', 'AGENTS.md', 'docs/THEORY_OF_THE_CASE.md', 'docs/HOW_TO_BUILD.md', 'docs/FULL_BUILD_PLAN.md',
  'docs/conversations/2026-10-13-the-thesis.md', 'docs/conversations/2026-10-18-anatomical-priors-and-targeted-compute.md']

// Each agent's required inputs, built as W1 builds them (§3).
const OUTSIDE = Object.keys(PIN.entries).filter((path) => path.startsWith('/'))
const LOCATORS = ['spans.py', 'callsites.py', 'assigned_names.py'].map((name) => TOOLS_REL + '/' + name)
const EVERY = [...INSTRUCTIONS, ...OUTSIDE, 'docs/GROUNDING_AND_WORKER_GUIDE.md', ...LOCATORS, 'scripts/run_interiors.py']
const IN_WORKTREE = [...EVERY, TOOLS_REL + '/import_proof.py']
const STAGES = ['r0-worktree', 'r0-candidate', 'r0-verify', 'r0-schema', 'r0-upstream', 'r0-stop-blocked', 'r0-stop-head',
  'r0-stop-revision', 'r0-stop-hash', 'r0-stop-missing', 'r0-stop-violation', 'r0-stop-unreported', 'r0-cancel']
const WORKTREE_STAGES = ['r0-worktree', 'r0-candidate', 'r0-verify']
const REQUIRED = Object.fromEntries(STAGES.map((stage) => [stage, WORKTREE_STAGES.includes(stage) ? IN_WORKTREE : EVERY]))
const unlisted = [...new Set(Object.values(REQUIRED).flat())].filter((path) => !has(PIN.entries, path))
if (unlisted.length) throw new Error('R0 needs every required input in the manifest, which lacks ' + unlisted.join(', '))
const inputsOf = (stage) => 'REQUIRED INPUTS: ' + REQUIRED[stage].join(', ') +
  '. Hash each of them in your first step and return each in source_hashes; a return that leaves one out is incomplete.'

// W1's outcomes and checks (§3, §7), unchanged.
const OUTCOMES = ['STALE_INPUT', 'VERIFICATION_FAILED', 'INCOMPLETE', 'READY_FOR_LEAD_REVIEW']
const ended = (status, stage, reasons) => ({ status, stage, reasons })

function screened(stage, r, changed) {
  if (!r) return ended('INCOMPLETE', stage, ['no return: the agent was skipped, died or was stopped'])
  const notDone = r.not_done || []
  const stale = []
  if (r.head !== PIN.head) stale.push('head ' + r.head + ' is not the pinned ' + PIN.head)
  if (String(r.packet_revision) !== REVISION) stale.push('packet revision ' + r.packet_revision + ' is not ' + REVISION)
  for (const entry of r.source_hashes || []) {
    if (changed && has(changed, entry.path)) continue
    if (!has(PIN.entries, entry.path)) stale.push(entry.path + ' is outside the frozen basis')
    else if (PIN.entries[entry.path] !== entry.sha256) stale.push(entry.path + ' differs from the baseline')
  }
  if (r.completion === 'stale_input' && stale.length === 0) stale.push(...(notDone.length ? notDone : ['the agent reported stale input']))
  if (stale.length) return ended('STALE_INPUT', stage, stale)
  if (r.completion !== 'complete') return ended('INCOMPLETE', stage, ['completion is ' + r.completion, ...notDone])
  if (r.attempt_dir !== dirOf(stage)) return ended('INCOMPLETE', stage, ['attempt directory ' + r.attempt_dir + ' is not ' + dirOf(stage)])
  const hashed = new Set((r.source_hashes || []).map((entry) => entry.path))
  const unhashed = REQUIRED[stage].filter((path) => !hashed.has(path))
  if (unhashed.length) return ended('INCOMPLETE', stage, unhashed.map((path) => 'required input ' + path + ' has no hash'))
  return null
}

function factsChecked(stage, r) {
  return screened(stage, r, null) || (r.facts.length === 0 ? ended('INCOMPLETE', stage, ['no facts returned']) : null)
}

function candidateChecked(stage, c) {
  const early = screened(stage, c, null)
  if (early) return early
  const reasons = []
  const manifest = {}
  for (const entry of c.candidate_hashes) manifest[entry.path] = entry.sha256
  const listed = new Set(c.files_changed)
  if (listed.size === 0) reasons.push('files_changed is empty')
  for (const path of listed) if (!has(manifest, path)) reasons.push(path + ' is listed as changed without a hash')
  for (const path of Object.keys(manifest)) {
    if (!listed.has(path)) reasons.push(path + ' has a hash but is not listed as changed')
    else if (has(PIN.entries, path) && PIN.entries[path] === manifest[path]) reasons.push(path + ' is listed as changed but equals the baseline')
    else if (manifest[path] === 'deleted' && !has(PIN.entries, path)) reasons.push(path + ' is listed as deleted but the baseline has no such file')
  }
  if (!isHex(64, c.diff_sha256)) reasons.push('diff_sha256 is not a SHA-256')
  for (const key of ['consumer_calls', 'tests', 'runs', 'comparisons']) if (c[key].length === 0) reasons.push(key + ' is empty')
  if (!String(c.import_proof).trim()) reasons.push('import_proof is empty')
  return reasons.length ? ended('INCOMPLETE', stage, reasons) : null
}

function verified(stage, v, changed, need) {
  const early = screened(stage, v, changed)
  if (early) return early
  const failed = []
  if (changed) {
    for (const entry of v.source_hashes) {
      if (has(changed, entry.path) && changed[entry.path] !== entry.sha256) failed.push(entry.path + ' after applying is not the candidate\'s file')
    }
  }
  failed.push(...v.violations, ...v.missing.map((item) => 'missing: ' + item))
  failed.push(...v.checked.filter((item) => item.verdict === 'unsupported').map((item) => 'unsupported: ' + item.check + ': ' + item.item))
  if (failed.length) return ended('VERIFICATION_FAILED', stage, failed)
  const short = []
  for (const name of need.checks) {
    if (!v.checked.some((item) => item.check === name && item.verdict === 'supported')) short.push('required check ' + name + ' is not reported supported')
  }
  if (need.ownRuns && v.own_runs.length === 0) short.push('no run of its own')
  if (changed) {
    for (const path of Object.keys(changed)) {
      if (!v.source_hashes.some((entry) => entry.path === path)) short.push(path + ' was not hashed after applying')
    }
  }
  return short.length ? ended('INCOMPLETE', stage, short) : ended('READY_FOR_LEAD_REVIEW', stage, [])
}

// W1's shared prompt rules, unchanged, then the rehearsal's own lines.
const COMMON = [
  'You are a worker for the lead (Claude, the main session) of RSNA_Knee at ' + ROOT + ': a classical-AI knee-MRI recognition build, deliberately with no machine learning.',
  "Rohan's words and docs/THEORY_OF_THE_CASE.md govern. docs/FULL_BUILD_PLAN.md is the work order and holds the contracts (§§14–15); docs/GROUNDING_AND_WORKER_GUIDE.md governs your role. You return facts or a candidate. You do not decide what Rohan means, choose an anatomical rule, a threshold, a sample meaning or a scope, or accept anything. If finishing would need such a choice, stop and return it named in not_done.",
  "FULL_BUILD_PLAN §0's session-start grounding and the active packet (docs/work/current/README.md) are the lead's: do not perform that grounding and never read the packet. Read whole the units this prompt names and any unit you need to understand them.",
  'SOURCE BASIS: HEAD ' + PIN.head + '; packet revision ' + REVISION + '; manifest ' + PIN.manifest + ' (SHA-256 ' + PIN.manifestSha256 + '): the SHA-256 of every input file you may read, a tracked file by its path relative to the repository root (' + ROOT + ', or your worktree\'s root, which holds the same files), a file under data/ by its path relative to ' + ROOT + ', a file outside the repository by its absolute path. Files written during this workflow are not inputs and are not in the manifest: your own, and those named by any agent\'s return inlined in this prompt (its attempt directory, notes, diff, receipts, worktree and new files). Your first step, before any other read and any edit: check that HEAD is ' + PIN.head + ' (the full 40 characters of git rev-parse HEAD), then hash with shasum -a 256, and compare with the manifest, every file under REQUIRED INPUTS at the end of this prompt: the instruction files among them reach you in your instructions rather than through Read, and the rest are the files this prompt names, the modules holding the units it names included. Hash each further input file before you read it; the study images, which the runner reads, are not hashed. On any mismatch, or an input file the manifest does not list, stop and return completion "stale_input" naming each one.',
  'Return in source_hashes every input file you hashed, once, by its manifest path, with its SHA-256 as you read it; files written during this workflow never go in source_hashes unless your role below says so (the verifier reports its copies of the candidate\'s changed files after applying). Return head as the full 40-character SHA, packet_revision exactly as given, and attempt_dir exactly as this prompt gives it.',
  'Read whole units only (whole functions, classes, sections, documents) with the Read tool. Locate code with python3 -I ' + TOOLS + '/spans.py <tree> <names>, ' + TOOLS + '/callsites.py <tree> <names> and ' + TOOLS + '/assigned_names.py <tree> <names>, where <tree> is the tree you work in. Never use the Grep tool, grep, rg, head, tail, sed, awk, cut, wc, jq, pipes or any text search. Do not read archive/ or archive2/.',
  'Keep your context well under a million tokens (a compaction would lock you): read whole units, not a whole file of thousands of lines unless the file is the unit, and read a long output once. If your task would need more, stop and return completion "partial", naming what is left in not_done.',
  'WRITES: your artifacts (notes, logs, runs, pictures, diffs) go only in your attempt directory, which must not exist before you start (if it does, stop and return completion "blocked"); code edits, where your role allows them, go only in your own worktree. Never edit the main tree, canonical outputs or another agent\'s files. Never commit, push, reset or clean. Never run scripts/ci_local.sh or scripts/sonar_local.py: the Sonar step is the lead\'s.',
  'Report facts with the evidence path you measured or read, inferences labelled as yours, and not_done for anything not done or not measured. Never state the outcome of something you did not measure. Never treat one construction\'s failure as a verdict on a capability. Never attribute words to Rohan unless you quote a file that records them.',
].join(' ')

const WORKTREE = [
  'You work in an isolated git worktree cut from HEAD; call its root <wt>. Run everything from <wt> with PYTHONPATH=<wt>/src and the interpreter ' + ROOT + '/.venv/bin/python.',
  'Before any test or run, run ' + TOOLS + '/import_proof.py <wt> under that same environment and keep its output; it exits non-zero unless knee and run_interiors both import from <wt>. If it fails, stop and return completion "blocked".',
  'The runner\'s ROOT is its own file\'s parent\'s parent, so in a worktree every default built on it points at a tree with no data: <wt> has no data/ folder. Read files under data/ by their absolute paths in ' + ROOT + ', and pass every path explicitly: --root ' + ROOT + '/data/raw, --run and --main-run inside your attempt directory, and accepted receipts by absolute path. Run the CLI with --workers 1. List in your return any path the runner wrote under <wt> by itself.',
].join(' ')

const REHEARSAL = 'This is R0, the runtime rehearsal before W1 (BUILD_WORKFLOWS §4): your role is a rehearsal that changes nothing in production, and a deliberate deviation your role names is part of it, to be done exactly as named.'
const LISTS = 'INSTRUCTION FILES AND PERMISSIONS: in instruction_files list the path of every instruction file your context names (each "Contents of <path>" block, and any other file your instructions say was loaded for you); in read_before_task, every file you read before starting the task; in refused_commands, every command that was refused or asked for a permission you could not give, with its text (none is a finding too).'
const prompt = (stage, role) => [COMMON, REHEARSAL, role, LISTS, inputsOf(stage)].join(' ')

// W1's schemas, with the rehearsal's three lists added to every return.
const SHA256 = { type: 'string', pattern: '^([0-9a-f]{64}|deleted)$' }
const HASHES = { type: 'array', minItems: 1, items: { type: 'object', properties: { path: { type: 'string', minLength: 1 }, sha256: SHA256 }, required: ['path', 'sha256'] } }
const STRINGS = { type: 'array', items: { type: 'string' } }
const BASIS = {
  head: { type: 'string', pattern: '^[0-9a-f]{40}$' },
  packet_revision: { type: 'string', minLength: 1 },
  completion: { type: 'string', enum: ['complete', 'partial', 'blocked', 'stale_input'] },
  source_hashes: HASHES,
  attempt_dir: { type: 'string', minLength: 1 },
  not_done: STRINGS,
  instruction_files: STRINGS,
  read_before_task: STRINGS,
  refused_commands: STRINGS,
}
const BASIS_KEYS = Object.keys(BASIS)
const STATEMENTS = { type: 'array', items: { type: 'object', properties: { statement: { type: 'string', minLength: 1 }, evidence: { type: 'string', minLength: 1 } }, required: ['statement', 'evidence'] } }
const FACTS = { type: 'object', properties: { ...BASIS, files: STRINGS, facts: STATEMENTS, inferences: STRINGS }, required: [...BASIS_KEYS, 'files', 'facts', 'inferences'] }
const CANDIDATE = { type: 'object', properties: {
  ...BASIS, worktree: { type: 'string', minLength: 1 }, diff_path: { type: 'string' }, diff_sha256: { type: 'string', pattern: '^[0-9a-f]{64}$' },
  candidate_hashes: HASHES, files_changed: STRINGS, consumer_calls: STRINGS, tests: STRINGS, import_proof: { type: 'string' },
  runs: STRINGS, comparisons: STRINGS, changed_frames: STRINGS, uncertainty: STRINGS,
}, required: [...BASIS_KEYS, 'worktree', 'diff_path', 'diff_sha256', 'candidate_hashes', 'files_changed', 'consumer_calls', 'tests', 'import_proof', 'runs', 'comparisons', 'changed_frames', 'uncertainty'] }
const verdictsFor = (checks) => ({ type: 'object', properties: {
  ...BASIS,
  checked: { type: 'array', items: { type: 'object', properties: { check: { type: 'string', enum: [...checks.map(([name]) => name), 'other'] }, item: { type: 'string', minLength: 1 }, verdict: { type: 'string', enum: ['supported', 'unsupported', 'not_checkable'] }, evidence: { type: 'string', minLength: 1 } }, required: ['check', 'item', 'verdict', 'evidence'] } },
  own_runs: STRINGS, violations: STRINGS, missing: STRINGS,
}, required: [...BASIS_KEYS, 'checked', 'own_runs', 'violations', 'missing'] })
const R0_VERIFY_CHECKS = [
  ['reconstructed_candidate', 'the diff has the candidate\'s SHA-256, applies with git apply, and both changed files match the candidate manifest'],
  ['tests', 'after the import check, tests/test_receipt.py passes in your worktree'],
]
const checksOf = (checks) => 'REQUIRED CHECKS: one entry each in checked, its check field set to the name (any further check goes in as "other"): ' +
  checks.map(([name, meaning]) => name + ', ' + meaning).join('; ') + '.'
const namesOf = (checks) => checks.map(([name]) => name)
const READY = 'READY_FOR_LEAD_REVIEW'
const factsOutcome = (stage, r) => factsChecked(stage, r) || ended(READY, stage, [])

async function worktreeChain() {
  const run = dirOf('r0-worktree') + '/run'
  const r = await agent(prompt('r0-worktree', WORKTREE + ' ROLE: rehearse a worktree agent. Attempt directory: ' + dirOf('r0-worktree') + '. After your first step and the import check, run the full test suite from <wt> (PYTHONPATH=<wt>/src ' + ROOT + '/.venv/bin/python -m pytest -q) and keep its summary; then one serial run of the real CLI on the proof study with every path explicit: PYTHONPATH=<wt>/src ' + ROOT + '/.venv/bin/python scripts/run_interiors.py --study-uid ' + PROOF + ' --root ' + ROOT + '/data/raw --workers 1 --run ' + run + '/interiors --main-run ' + run + '/main, keeping its exit status and output in your attempt directory; then list, with git -C <wt> status --porcelain --ignored, every path anything you ran wrote under <wt>. Report each as a fact with its evidence path: the import check\'s output, the test summary, the CLI\'s exit and the receipts it wrote, and the paths written under <wt> (none is a finding too).'), { ...SONNET, label: 'r0-worktree', phase: 'Runtime', schema: FACTS, isolation: 'worktree' })
  return { ...factsOutcome('r0-worktree', r), returned: r }
}

async function candidateChain() {
  const candidate = await agent(prompt('r0-candidate', WORKTREE + ' ROLE: rehearse an implementation candidate with a harmless edit that is never integrated. Attempt directory: ' + dirOf('r0-candidate') + '. After your first step and the import check: append the line "# R0 rehearsal edit: never integrated" at the end of tests/test_receipt.py; create tests/r0_rehearsal_marker.py holding only the docstring """R0 rehearsal marker: never integrated."""; run PYTHONPATH=<wt>/src ' + ROOT + '/.venv/bin/python -m pytest -q tests/test_receipt.py and keep its summary. Mark the new file intent-to-add (git add -N tests/r0_rehearsal_marker.py; nothing is committed), write git diff to candidate.diff in your attempt directory and record its SHA-256; after your last edit, hash both changed files into candidate_hashes and list exactly those two paths in files_changed. Fill consumer_calls with "none: a rehearsal edit with no production consumer", tests with the pytest summary, runs with "none: no CLI run in this rehearsal candidate", comparisons with "none: nothing to compare", import_proof with the import check\'s output, changed_frames with nothing, and uncertainty with anything you could not do. Report in source_hashes the files you read as they were before any edit.'), { ...SONNET, label: 'r0-candidate', phase: 'Runtime', schema: CANDIDATE, isolation: 'worktree' })
  const c = candidateChecked('r0-candidate', candidate)
  if (c) return { ...c, returned: candidate, verdict: null }
  const changed = {}
  for (const entry of candidate.candidate_hashes) changed[entry.path] = entry.sha256
  const verdict = await agent(prompt('r0-verify', WORKTREE + ' ROLE: rehearse an independent verifier of the candidate below in your own fresh worktree. Attempt directory: ' + dirOf('r0-verify') + '. The candidate claims: ' + JSON.stringify(candidate) + ' Make the SOURCE BASIS checks first, before applying anything. Then check that ' + candidate.diff_path + ' has SHA-256 ' + candidate.diff_sha256 + ', apply it with git apply, confirm both changed files are present, and hash each: report those in source_hashes as they are after applying; they must equal the candidate manifest above. Every other file you read must still equal the baseline; report it as you read it. After the import check, run PYTHONPATH=<wt>/src ' + ROOT + '/.venv/bin/python -m pytest -q tests/test_receipt.py and put that run in own_runs. Put anything that must block in violations and anything the candidate lacks in missing. ' + checksOf(R0_VERIFY_CHECKS)), { ...SONNET, label: 'r0-verify', phase: 'Runtime', schema: verdictsFor(R0_VERIFY_CHECKS), isolation: 'worktree' })
  return { ...verified('r0-verify', verdict, changed, { checks: namesOf(R0_VERIFY_CHECKS), ownRuns: true }), returned: candidate, verdict }
}

async function schemaChain() {
  const r = await agent(prompt('r0-schema', 'ROLE: rehearse a return that breaks its schema. You work in the main tree and change no code. Attempt directory: ' + dirOf('r0-schema') + '. After your first step, return your structured output with head as the number 0 instead of a string and without the field not_done. If the output tool refuses that, return what it accepts, and say in not_done what it refused and how.'), { ...SONNET, label: 'r0-schema', phase: 'Runtime', schema: FACTS })
  return { ...factsOutcome('r0-schema', r), returned: r }
}

async function upstreamChain() {
  const upstream = {
    attempt_dir: dirOf('r0-candidate'),
    diff_path: dirOf('r0-candidate') + '/candidate.diff',
    receipts: [dirOf('r0-worktree') + '/run/interiors/receipt.json', dirOf('r0-worktree') + '/run/main/receipt.json'],
    notes: dirOf('r0-worktree') + '/notes.md',
    new_files: ['tests/r0_rehearsal_marker.py'],
  }
  const r = await agent(prompt('r0-upstream', 'ROLE: rehearse an agent whose prompt inlines an upstream return. You work in the main tree and change no code. Attempt directory: ' + dirOf('r0-upstream') + '. An upstream agent of this workflow returned: ' + JSON.stringify(upstream) + ' The files it names were written during this workflow, and some may not exist yet: they are not inputs. Do your first step, then report as facts which files you treated as inputs and hashed, and which as written during the workflow, without opening the latter.'), { ...SONNET, label: 'r0-upstream', phase: 'Runtime', schema: FACTS })
  return { ...factsOutcome('r0-upstream', r), returned: r }
}

const STOPS = [
  { stage: 'r0-stop-blocked', verdict: false, deviation: 'return completion "blocked", with not_done ["rehearsal: told to return blocked"]' },
  { stage: 'r0-stop-head', verdict: false, deviation: 'return head as 0000000000000000000000000000000000000000 instead of the real HEAD' },
  { stage: 'r0-stop-revision', verdict: false, deviation: 'return packet_revision as "r0-wrong" instead of the one given' },
  { stage: 'r0-stop-hash', verdict: false, deviation: 'in source_hashes, give scripts/run_interiors.py the SHA-256 0000000000000000000000000000000000000000000000000000000000000000 instead of the one you computed' },
  { stage: 'r0-stop-missing', verdict: false, deviation: 'leave scripts/run_interiors.py out of source_hashes' },
  { stage: 'r0-stop-violation', verdict: true, deviation: 'put "rehearsal: a deliberate violation" in violations' },
  { stage: 'r0-stop-unreported', verdict: true, deviation: 'leave the required check tests out of checked' },
]

async function stopChain(s) {
  const role = 'ROLE: rehearse a stop case. You work in the main tree and change no code. Attempt directory: ' + dirOf(s.stage) + '. Do your first step exactly as SOURCE BASIS says, then do no other work and return at once, true in every field but this one deliberate deviation: ' + s.deviation + '.' +
    (s.verdict
      ? ' You are in the verifier\'s role with no candidate. ' + checksOf(R0_VERIFY_CHECKS) + ' Report each as supported, with the evidence "rehearsal stop case", except as your deviation says; put "rehearsal stop case: no run" in own_runs and leave missing empty.'
      : ' Put one fact in facts: that this is a rehearsal stop case, with your attempt directory as its evidence.')
  const r = await agent(prompt(s.stage, role), { ...SONNET, label: s.stage, phase: 'Stops', schema: s.verdict ? verdictsFor(R0_VERIFY_CHECKS) : FACTS })
  const outcome = s.verdict ? verified(s.stage, r, null, { checks: namesOf(R0_VERIFY_CHECKS), ownRuns: false }) : factsOutcome(s.stage, r)
  return { ...outcome, returned: r }
}

async function cancelChain() {
  const r = await agent(prompt('r0-cancel', 'ROLE: rehearse a long task the lead stops part-way. You work in the main tree and change no code. Attempt directory: ' + dirOf('r0-cancel') + '. After your first step, write started.txt in your attempt directory, run the full test suite from ' + ROOT + ' (' + ROOT + '/.venv/bin/python -m pytest -q) keeping its output in your attempt directory, then write finished.txt there and report the test summary as a fact.'), { ...SONNET, label: 'r0-cancel', phase: 'Cancel', schema: FACTS })
  return { ...factsOutcome('r0-cancel', r), returned: r }
}

// Each chain's expected outcome (§3), or OBSERVE where the rehearsal records what happens.
const EXPECTED = {
  worktree: READY, candidate: READY, schema: 'OBSERVE', upstream: READY,
  'r0-stop-blocked': 'INCOMPLETE', 'r0-stop-head': 'STALE_INPUT', 'r0-stop-revision': 'STALE_INPUT',
  'r0-stop-hash': 'STALE_INPUT', 'r0-stop-missing': 'INCOMPLETE', 'r0-stop-violation': 'VERIFICATION_FAILED',
  'r0-stop-unreported': 'INCOMPLETE', cancel: READY,
}
const PART_CHAINS = {
  runtime: [['worktree', worktreeChain], ['candidate', candidateChain], ['schema', schemaChain], ['upstream', upstreamChain]],
  stops: STOPS.map((s) => [s.stage, () => stopChain(s)]),
  cancel: [['cancel', cancelChain]],
}
const chosen = PART_CHAINS[args.part]
const results = await parallel(chosen.map(([, run]) => () => run()))
const chains = {}
chosen.forEach(([name], i) => {
  const r = results[i]
  const outcome = r && OUTCOMES.includes(r.status) ? r : ended('INCOMPLETE', name, ['the chain threw or ended without an outcome'])
  chains[name] = { expected: EXPECTED[name], ...outcome }
})
const mismatches = Object.entries(chains)
  .filter(([, c]) => c.expected !== 'OBSERVE' && c.status !== c.expected)
  .map(([name, c]) => name + ' ended ' + c.status + ' at ' + c.stage + ', expected ' + c.expected)
log('R0 ' + args.part + ': ' + (mismatches.length ? mismatches.join('; ') : 'every chain as expected'))
return { part: args.part, pin: { head: PIN.head, manifestSha256: PIN.manifestSha256, packetRevision: REVISION, attempt: args.attempt }, chains, mismatches }
```

## 8. Cost and capacity

- About 90–100 agents over W1–W12 at Sonnet xhigh, each loading the project CLAUDE.md (about 231 KB of
  imports: AGENTS, THEORY, HOW_TO_BUILD, the plan and two conversations) plus its packet: the dominant
  fixed cost per agent.
- Codex: one consultation per decision batch (P2a; P3 scopes; the P4, P5 and P6 rules; P7 scopes; P12)
  with complete inlined payloads of about 150–300 KB, from the model-only home; `consult-budget` before and
  after each; the broker closed after each.
- Fable: one reading per rule, about 31 for P4–P6, plus about a dozen scope sheets if §1.2 is approved;
  usage recorded per call (API credits, not shown by `consult-budget`).
- Real-CLI runs: proof/bursa serial at every gate and in parallel by the lead, the public split at every
  gate; the labelled cohort at family-wave ends and P11.
- The gate's Sonar step adds about three minutes per gate on this machine (the scanner image runs under
  emulation here); each push also runs the whole gate on a GitHub runner, and each push to main the
  kernel benchmarks under CodSpeed (`.github/workflows/codspeed.yml`).
- The runtime rehearsal (§4): about eight agents at W1's settings, each loading the project instructions.
  The offline mock costs no agent.

## 9. Risks this plan guards against

- Worktree agents testing the main tree's code (an import check that fails the run).
- Defaults derived from the runner's own location pointing at a tree with no data (explicit paths; the
  dry run before W1).
- Stale or mismatched sources (a clean tree before each workflow; the pin carried and checked in every
  prompt).
- Runner conflicts between parallel candidates (modules plus thin wiring; sequential integration with
  rebase and re-verification).
- Proxy objectives in P2a and the scope work (question first, forbidden substitutions, the operation check
  before implementation, Codex on every scope).
- A primitive deciding a selector (rules reviewed before shared readers; the ACL never inherits the PCL's
  rule).
- Wave-1 results used unchecked (W2 re-checks or regenerates them; nothing cited before that).
- A changed premise mid-workflow (stop, confirm, quarantine, revise, relaunch with fresh attempt ids).
- A candidate's analysis replacing the Sonar server's record of the integrated tree (agents never run
  the Sonar step).
- An unenforced reading law (stated in every prompt; the hook wiring is a SquishOS repair for Rohan to
  decide separately).
- A returned HEAD, revision or hash unlike the pin while the chain goes on (the script compares them and
  ends that chain as STALE_INPUT; the mock covers each case).
- A finished worker read as a verified candidate (one named outcome per chain and per run;
  READY_FOR_LEAD_REVIEW is not acceptance).
- A verifier reading the candidate's own edits as stale (the baseline is checked before applying, the
  candidate manifest after).
- Governing documents, CLAUDE.md imports or named data inputs changing under an unchanged prompt (all in
  the manifest and hashed first; no edit to a listed file while a workflow runs).
- A recording committed without the gate having replayed it (it is refreshed before the final gate, and
  nothing tracked changes after that gate).
- What the mock cannot show: schema enforcement, isolation, imports, permissions and cancellation (the
  runtime rehearsal, §4).
- A return that leaves out a required input's hash while its chain goes on (each agent's required inputs
  are named in its prompt and in the script, which checks every one; the mock covers it).
- A verifier passing on any one check (its required checks are named, and each must be reported
  supported; the mock covers it).
- An agent compacting mid-task and being locked (each stays under a million tokens, §3; the rehearsal
  measures it). The lead's own compaction stops it until Rohan's next message (§2).

## 10. The reviews and what changed

Codex (GPT-6.1 Sol, model-only, read-only) read revision 1 with the canonical documents inlined and
found "the overall sequence is faithful, but the draft needs corrections before launch", chiefly W1's
execution guarantees, incomplete rule-review scheduling and P12's reduced scope. The lead adopted every
correction, each recorded with its reading in `lead-adjudication.md`. Three W1 findings were already fixed
in the file after the prompt was assembled, and Codex never saw those fixes. No mechanism, contract or
anatomical rule changed in revision 2, so there was no second consultation; Codex itself said the
mechanical repairs are the lead's.

Revision 3 answers the review Rohan pasted at 23:37 under his words «Feedback on the workflow». The
message does not name the review's author; it is agent text, kept verbatim with the lead's checks in
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/workflow-plan-r3-20261018/`. It
found the plan "substantially sound and faithful to the thesis" and four execution details to fix before
launch. The lead checked each against the file before changing anything:

| The review's finding | What the lead found | Change |
|---|---|---|
| Returned identities are never compared with the expected inputs; in its offline mock a trace with the wrong HEAD and revision still launched the candidate | W1's `complete()` read only `completion` and one nonempty field; the lead's own mock of revision 2 launches the candidate after a wrong HEAD and after a wrong revision | The script compares every return's HEAD, packet revision and hashes with the pin (`args.sourcePin.entries`); a mismatch ends the chain as STALE_INPUT before anything depends on it |
| No explicit outcome: blocking verifier findings came back without a failed or blocked state | Each chain returned `{trace, candidate, verdict}` and nothing more; the mock of revision 2 shows the run naming no outcome | One named outcome per chain and one for the run, with the full mapping in §3: the review's three, and STALE_INPUT, the lead's split |
| Baseline and candidate hashes are not told apart, and the governing documents are outside the frozen basis | The shared prompt told every agent to check "every unit you read" against HEAD, which a verifier holding the applied candidate would fail on the candidate's own edits; the clean-tree rule covered `scripts/`, `src/` and `tests/` only | A manifest of every file agents may read, the CLAUDE.md imports and governing documents included; the instruction files hashed first; the candidate manifest; the verifier checks the baseline before applying and the candidate manifest after; the script classifies every returned hash |
| The recording is refreshed after the gate, which never refreshes it | `scripts/ci_local.sh` replays the stored recording and never records; both this plan's §3 and FULL_BUILD_PLAN §9 step 6, the lead's own wording, put the refresh after the gate | The recording, the records and the packet are written first; the final gate runs last on exactly the tree being committed, and nothing tracked changes after it; FULL_BUILD_PLAN §9 step 6 now says the same |
| The launch rehearsal should exercise the actual workflow runtime | Precondition 5 was a dry run in a hand-made worktree | Each script's offline mock (control flow only) and the runtime rehearsal R0 (§4) |

Added when the lead checked revision 3 with its advisor: the untracked inputs the prompts name and the
instruction files that reach an agent are in the manifest; files written during the workflow (an agent's
own, and those named in an upstream return inlined in its prompt) are not inputs, so they neither stop an
agent nor go in its hashes, and an agent returns its attempt directory exactly as given, which the script
checks; the active packet is the one tracked file the
lead writes while a workflow runs, no agent reads it, and Rohan's words that arrive mid-workflow go there
first; the first gate after a recording refresh reads its memory figure as information. The review's
recommendations on the two Fable decisions are in §1, for Rohan to answer. No anatomical mechanism,
contract or rule changed: these are execution repairs, which Codex's earlier reading leaves to the lead,
so there was no new Codex consultation.

Revision 4 answers the review Rohan pasted at 00:25 on 2026-10-19 under his word «Feedback:». The message
does not name its author; it is agent text, kept verbatim with the lead's checks in
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/workflow-plan-r4-20261019/`. It found
the plan "faithful to the thesis and substantially ready" and two execution checks to tighten before an
unattended build, each shown by an omission case it added to the offline mock. The lead checked both against
the file before changing anything:

| The review's finding | What the lead found | Change |
|---|---|---|
| Required input hashes can be omitted: a trace that returns only the runner's hash still launches implementation | `screened()` compared each returned hash with the pin but required none to be there, and the schema asks for one hash at least. Run on revision 3, the lead's mock launches the candidate and the verifier after such a trace, and the run ends READY_FOR_LEAD_REVIEW | Each agent's required inputs are named in its prompt and in the script (`REQUIRED`): the instruction files, the guide, the code locators, the runner, and each packet's notes, tools, receipts and the modules holding the units it names (located with the AST locator at `17a5393`). A return that leaves one out ends its chain INCOMPLETE, and the script refuses to start when the manifest lacks one |
| Verifier completeness is counted, not identified: the P2b verifier passes with one unrelated supported check | `verified()` compared a count of supported checks with a number (1 for P2b, 8 and 2 for the P2a verifiers). Run on revision 3, the mock passes the P2b verifier on one unrelated check | Each verifier's required checks have stable names, the same in its prompt, its schema and the script, and each must be reported supported: for P2b the review's list, with the two study runs as two checks; for the P2a verifiers, one per named operation or picture check, and the forbidden substitutions |

The revised mock (`w1_mock.mjs` there) runs 34 cases: the 31 before, with every complete return now carrying
its required hashes and named checks, the review's two omission cases, and a manifest that lacks a required
input. On revision 4 all 34 end as §3 maps them; on revision 3 exactly those three fail.

The review's other points: the runtime rehearsal R0 stays as planned (§4), after approval, and now also
checks the two new stops and each agent's context; the two Fable policies stay Rohan's to give (§1), with
the same recommendation; the lead carries the sequence through W12 itself (§2), which now says that a
compaction locks the lead until his next message; and P11 stays the finish line for recognition, with P12's
unspecified details and P13 not blocking it. Rohan's note at 00:35, that each sub-agent should stay under a
million tokens, is §3's context rule. No anatomical mechanism, contract or rule changed, so there was no new
Codex consultation.
