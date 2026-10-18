# Build workflows: carrying out FULL_BUILD_PLAN P2b–P12 (the lead's plan for Rohan's review)

Revision 2, 2026-10-18, written by the lead (Claude) at Rohan's request: «plan out workflows that will
complete the specified build of the full project as articulated thus far (Sonnet xhigh effort for the
agents). Come to me with your full plan when you've designed it, consult codex on the plan». Revision 1
went to Codex; its reading (`codex-answer.md`) and the lead's adjudication (`lead-adjudication.md`) are in
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/workflow-plan-review-20261018/`, with
revision 1 as it stood when the answer came (`BUILD_WORKFLOWS-at-codex-answer.md`). Nothing here is
launched until he approves; the plan itself is committed and pushed («just freaking commit to git»).
Since revision 2 the lead has added one step to every gate (§2, §3), after the kernel benchmarks moved
to recorded production calls at Rohan's 21:19 words (FULL_BUILD_PLAN §9, step 6), and noted the CodSpeed
run each push now starts (§8).

This is an execution design for `docs/FULL_BUILD_PLAN.md`, not another master plan. The order is the
plan's §4: P2b → P2a → P3 → P4 → P5 → P6, with P7 and P9 items folded in as each family is touched and
P9's generic lineage at the first adapter edit (W4); then P8, P9 closure, P10, P11 and P12; P13 waits for
Rohan. Each workflow names its P-task, the §§14–15 contracts it consumes and produces, its real consumer
and the lead gate it ends at. Beyond the plan: the launch preconditions (§4), the re-check of the six
stopped wave-1 packets (W2), and an owed-item inventory begun in W2 and closed in W10.

## 1. Decisions for Rohan

Two, both about the Fable consult (the only second reader that can see a picture; it spends API credits):

1. **A failed billed Fable call.** The consultation reference says it is not retried without your
   decision. Pre-authorise one retry per rule, or have such failures collected for you at the end of the
   family wave?
2. **Fable for the scope sheets.** Plan §7 covers the ~31 P4–P6 anatomy rules: one reading per rule (a
   call may carry an object's views together only if its answer reads each rule separately). P2a's region
   rule, P3's corridor and cavity scopes and P7's consumer scopes are picture-grounded too, and Codex
   cannot see pictures. Add one Fable reading per scope sheet, about a dozen more?

Settled by your recorded words, stated so you can correct them:

- **Workflow agents implement.** Your 18:46 instruction (workflows, Sonnet at xhigh) makes workflow
  agents the implementers, each in an isolated worktree, with the lead the single integrator. On your
  approval of this plan, the guide's route row "Bounded implementation → text-only Claude Max" and plan
  §10's matching sentence change to say so.
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
  CLI runs (proof/bursa serial and parallel, public, the cohort where due); the full gate with its Sonar
  step and advisory lists; the kernel benchmarks' recording, refreshed from the integrated source when an
  increment changes a benchmarked kernel or what production hands it (plan §9, step 6; a worktree has no
  data, so the recorder stops there); §15.3's six statements; MAP/RESOLVING acceptance records; the
  active packet; commits, pushes, and the GitHub gate run on each pushed commit.
- The job table (§3).
- Stop points: family-wave picture sheets to Rohan; any disagreement between Codex, Fable and the lead;
  a step the P12 contract leaves unspecified; P13.

## 3. Rules every workflow follows

- **Agents:** every `agent()` call passes `model: 'sonnet', effort: 'xhigh'` (Rohan's setting), verifiers
  included. Each workflow stays under ten agents; workflows run in sequence with a lead gate between them.
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
- **Source basis:** before each workflow the main tree has no modified or untracked files under
  `scripts/`, `src/` or `tests/` (worktrees are cut from HEAD, so a dirty main tree would mean candidates
  test different code). The lead writes a manifest of each unit's SHA-256 at HEAD. Every prompt carries
  HEAD, the manifest's SHA-256 and the packet revision; every agent checks HEAD and each unit it reads
  against them and stops as `stale_input` on any mismatch.
- **Worktree agents:** `isolation: 'worktree'`. Run from the worktree root with `PYTHONPATH=<worktree>/src`
  and the main tree's `.venv/bin/python`, after `B/workflow-tools/import_proof.py <worktree>`, which exits
  non-zero unless `knee` and `run_interiors` both import from the worktree (the editable install otherwise
  imports the main tree's `src`). The runner's ROOT is its own file's parent's parent, so in a worktree
  every default built on it points at a tree with no data: every path is passed explicitly (`--root
  <main>/data/raw`, `--run` and `--main-run` inside the attempt directory, accepted receipts by absolute
  path). Candidate CLI runs are serial (`--workers 1`). Agents run the tests and the gate's static checks,
  never its Sonar step: one server holds one project history, and analysing a candidate's tree there would
  make its latest analysis, which the lead's gate prints and reads, describe code that was never
  integrated. Parallel CLI runs and the full gate are the
  lead's, in the main tree, after integration.
- **Candidates:** new files marked intent-to-add (`git add -N`, nothing committed), then `git diff` into
  `candidate.diff` with its SHA-256. The verifier applies it in its own fresh worktree, checks the digest
  and that every changed and new file is present, re-runs the tests, and makes its own real-CLI runs into
  its own attempt directory, comparing its receipts with the accepted epoch's and with the candidate's.
- **Returns:** schema-checked JSON carrying head, packet revision, a completion state (`complete`,
  `partial`, `blocked`, `stale_input`) and the SHA-256 of every unit read or changed, with facts and their
  evidence paths, inferences labelled, and not_done. A schema checks shape, not sufficiency: the lead reads
  every return. A dependent agent launches only when its input returned `complete` with content;
  otherwise that chain stops and returns to the lead. Area, coverage, pixel and timing figures are
  observations, never acceptance criteria.
- **Job table:** the lead records each workflow run (its run ID, task ID, packet revision, dependencies,
  output roots and state: `PREPARING`, `RUNNING`, `RETURNED_UNREVIEWED`, `VERIFIED`, `ACCEPTED`,
  `NEEDS_RULE`, `STALE_INPUT`, `WITHDRAWN`, `FAILED`) in the active packet's single job table at launch, at
  each gate and on any stop. The scripts write nothing to it.
- **Invalidation (guide §7):** when a premise, contract or source a workflow depends on changes: stop it
  (TaskStop) and confirm it stopped; mark affected outputs ineligible where they sit (`WITHDRAWN.md` or
  `STALE_INPUT.md`); invalidate the reviews and tests derived from them; correct the packet (a new
  revision) and relaunch with a fresh attempt id. Every prompt carries HEAD, the manifest's digest and the
  packet revision, and a dependent prompt inlines its inputs, so a changed source, contract or upstream
  result changes the prompt: a resume cannot serve a stale cached result.
- **Single writer:** the lead integrates one candidate at a time; a later candidate is rebased onto the
  integrated tree and re-verified before it is integrated.
- **Acceptance (plan §9, §15.3):** the lead integrates, runs the real CLI into new output roots,
  reconstructs every new native support from its address and inspects the actual DICOM frame, compares
  receipts (equivalent refactors must match; intended scope or semantic changes get a full changed-output
  account), runs the full gate (`scripts/ci_local.sh`, Sonar included) and reads its advisories,
  refreshes the kernel benchmarks' recording when the increment changes what production hands a
  benchmarked kernel (plan §9, step 6), writes the six statements, records MAP/RESOLVING acceptance,
  updates the active packet, commits, runs the
  pre-push checks (the lockfile audit, zizmor, a secret scan of the commits being pushed), pushes, and
  reads the GitHub gate run on the pushed commit.

## 4. Preconditions (after approval, before W1)

1. Rohan's two decisions (§1); the route change in the guide and plan §10.
2. Copy `spans.py`, `callsites.py` and `assigned_names.py` and write `import_proof.py` in
   `B/workflow-tools/`; create `B/workflows-20261018/`.
3. `consult-budget`; `anthropic-consult --check` (key readable; value never printed).
4. A clean tree under `scripts/`, `src/` and `tests/`; pin HEAD and the unit manifest; record them in the
   active packet; open the job table.
5. A dry run: one throwaway worktree, `import_proof.py`, the test suite and one proof CLI run with the
   planned environment and explicit paths. Record what breaks (anything the runner derives from its own
   location) and fix the packet text before launch.

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
const B = ROOT + '/data/readings/collapse-20261017/full-build/targeted-compute-20261018'
const TOOLS = B + '/workflow-tools'
const PIN = args && args.sourcePin
if (!PIN || !PIN.head || !PIN.manifest || !PIN.manifestSha256 || !args.attempt || !args.packetRevision) {
  throw new Error('W1 needs args = { sourcePin: { head, manifest, manifestSha256 }, attempt, packetRevision } from the lead')
}
const SONNET = { model: 'sonnet', effort: 'xhigh' }
const PROOF = '1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149'
const BURSA = '1.2.826.0.1.3680043.8.498.13335129881737731410081002627729200903'
const ACCEPTED = B + '/p2b-bone-context-20261018/repair/proof-bursa'
const dirOf = (packet) => B + '/workflows-20261018/w1/' + packet + '/attempt-' + args.attempt
const complete = (r, key) => Boolean(r) && r.completion === 'complete' && Array.isArray(r[key]) && r[key].length > 0

const COMMON = [
  'You are a worker for the lead (Claude, the main session) of RSNA_Knee at ' + ROOT + ': a classical-AI knee-MRI recognition build, deliberately with no machine learning.',
  "Rohan's words and docs/THEORY_OF_THE_CASE.md govern. docs/FULL_BUILD_PLAN.md is the work order and holds the contracts (§§14–15); docs/GROUNDING_AND_WORKER_GUIDE.md governs your role. You return facts or a candidate. You do not decide what Rohan means, choose an anatomical rule, a threshold, a sample meaning or a scope, or accept anything. If finishing would need such a choice, stop and return it named in not_done.",
  'SOURCE BASIS: HEAD ' + PIN.head + '; unit manifest ' + PIN.manifest + ' (SHA-256 ' + PIN.manifestSha256 + '); packet revision ' + args.packetRevision + '. First check HEAD and the hash of every unit you read against the manifest; on any mismatch stop and return completion "stale_input" naming each one.',
  'Read whole units only (whole functions, classes, sections, documents) with the Read tool. Locate code with python3 -I ' + TOOLS + '/spans.py <tree> <names>, ' + TOOLS + '/callsites.py <tree> <names> and ' + TOOLS + '/assigned_names.py <tree> <names>, where <tree> is the tree you work in. Never use the Grep tool, grep, rg, head, tail, sed, awk, cut, wc, jq, pipes or any text search. Do not read archive/ or archive2/.',
  'WRITES: your artifacts (notes, logs, runs, pictures, diffs) go only in your attempt directory, which must not exist before you start (if it does, stop and return completion "blocked"); code edits, where your role allows them, go only in your own worktree. Never edit the main tree, canonical outputs or another agent\'s files. Never commit, push, reset or clean. Never run scripts/ci_local.sh or scripts/sonar_local.py: the Sonar step is the lead\'s.',
  'Report facts with the evidence path you measured or read, inferences labelled as yours, and not_done for anything not done or not measured. Never state the outcome of something you did not measure. Never treat one construction\'s failure as a verdict on a capability. Never attribute words to Rohan unless you quote a file that records them.',
].join(' ')

const WORKTREE = [
  'You work in an isolated git worktree cut from HEAD; call its root <wt>. Run everything from <wt> with PYTHONPATH=<wt>/src and the interpreter ' + ROOT + '/.venv/bin/python.',
  'Before any test or run, run ' + TOOLS + '/import_proof.py <wt> under that same environment and keep its output; it exits non-zero unless knee and run_interiors both import from <wt>. If it fails, stop and return completion "blocked".',
  'The runner\'s ROOT is its own file\'s parent\'s parent, so in a worktree every default built on it points at a tree with no data. Pass every path explicitly: --root ' + ROOT + '/data/raw, --run and --main-run inside your attempt directory, and accepted receipts by absolute path. Run the CLI with --workers 1. List in your return any path the runner wrote under <wt> by itself.',
].join(' ')

const HASHES = { type: 'array', minItems: 1, items: { type: 'object', properties: { path: { type: 'string', minLength: 1 }, sha256: { type: 'string', minLength: 64, maxLength: 64 } }, required: ['path', 'sha256'] } }
const BASIS = {
  head: { type: 'string', minLength: 7 },
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
  ...BASIS, worktree: { type: 'string', minLength: 1 }, diff_path: { type: 'string' }, diff_sha256: { type: 'string' },
  files_changed: STRINGS, consumer_calls: STRINGS, tests: STRINGS, import_proof: { type: 'string' },
  runs: STRINGS, comparisons: STRINGS, changed_frames: STRINGS, uncertainty: STRINGS,
}, required: [...BASIS_KEYS, 'worktree', 'diff_path', 'diff_sha256', 'files_changed', 'consumer_calls', 'tests', 'import_proof', 'runs', 'comparisons', 'changed_frames', 'uncertainty'] }

const VERDICTS = { type: 'object', properties: {
  ...BASIS,
  checked: { type: 'array', items: { type: 'object', properties: { item: { type: 'string', minLength: 1 }, verdict: { type: 'string', enum: ['supported', 'unsupported', 'not_checkable'] }, evidence: { type: 'string', minLength: 1 } }, required: ['item', 'verdict', 'evidence'] } },
  own_runs: STRINGS, violations: STRINGS, missing: STRINGS,
}, required: [...BASIS_KEYS, 'checked', 'own_runs', 'violations', 'missing'] }

const P2B_PACKET = [
  'TASK: FULL_BUILD_PLAN P2b increment 2 (settled wiring; guide §5 example). Read whole: plan §1.2, §14.4, the P2b section, and the packet ' + B + '/p2b-bone-context-20261018/README.md and verification.md.',
  'INTENT: offer the refined leg (refine_leg, already published once after name_the_bones) to the two remaining consumers that run after it, axial_bone_planes (inside build_study_map) and fibula_key_planes, at the right time, keeping the early leg wherever an earlier reader needs it.',
  'CONTRACTS: M07 → M08 → M09/M20. CONSUMER: the bones\' and fibula\'s axial key planes, which set the common map\'s axial zero.',
  'FORBIDDEN SUBSTITUTIONS: no erosion or filtering of source sections; nothing aimed at AX14\'s calibration or any core size; no repeated whole-study convergence loop; no recognition-rule edits; no change beyond these consumers\' arguments, order and cache keys.',
].join(' ')

async function p2bChain() {
  const trace = await agent(COMMON + ' ' + P2B_PACKET + ' ROLE: facts. Attempt directory: ' + dirOf('p2b-trace') + '. Read whole axial_bone_planes, fibula_key_planes, build_study_map, refine_leg, leg_on, native_femur_coarse_context, measure_study and every caller of the first three; report the call order, which leg each receives now, every cache key that would see the leg, and every reader that must keep the early leg.', { ...SONNET, label: 'p2b-trace', phase: 'Facts', schema: FACTS })
  if (!complete(trace, 'facts')) return { trace, candidate: null, verdict: null, stopped: 'trace not complete: the lead decides the reissue' }
  const candidate = await agent(COMMON + ' ' + WORKTREE + ' ' + P2B_PACKET + ' ROLE: implement the settled wiring. Attempt directory: ' + dirOf('p2b-candidate') + '. The trace: ' + JSON.stringify(trace) + ' Make the change in your worktree; add focused tests (context identity reaches both consumers; early-leg readers unchanged; a changed context misses, an identical context reuses); after the import check run them and the full test suite; run the real CLI on the proof (' + PROOF + ') and bursa (' + BURSA + ') studies into your attempt directory, and compare each receipt (interiors and main) with the accepted repair epoch\'s under ' + ACCEPTED + ' using scripts/compare_receipts.py. Mark new files intent-to-add (git add -N <file>; nothing is committed), write git diff to candidate.diff in your attempt directory, and record its SHA-256. Name the two consumer calls; list every changed record and the axial frames (series, slice) whose anchors moved.', { ...SONNET, label: 'p2b-candidate', phase: 'Candidate', schema: CANDIDATE, isolation: 'worktree' })
  if (!complete(candidate, 'files_changed') || candidate.consumer_calls.length === 0 || candidate.diff_sha256.length !== 64) return { trace, candidate, verdict: null, stopped: 'candidate not complete: the lead decides the reissue' }
  const verdict = await agent(COMMON + ' ' + WORKTREE + ' ' + P2B_PACKET + ' ROLE: independent verifier. Attempt directory: ' + dirOf('p2b-verify') + '. The candidate claims: ' + JSON.stringify(candidate) + ' In your own fresh worktree: check that ' + candidate.diff_path + ' has SHA-256 ' + candidate.diff_sha256 + ', apply it with git apply, and confirm every changed and new file is present; read every changed unit whole and check it against §14.4 and the forbidden substitutions; after the import check run its tests and the full test suite; re-check every caller and sibling route of the changed functions; then make your own real-CLI runs on the proof and bursa studies into your attempt directory and compare your receipts with the accepted repair epoch\'s and with the candidate\'s (scripts/compare_receipts.py). List the frames the lead must inspect. Give no anatomical verdict.', { ...SONNET, label: 'p2b-verify', phase: 'Verify', schema: VERDICTS, isolation: 'worktree' })
  return { trace, candidate, verdict }
}

const P2A_FRAME = [
  'TASK: FULL_BUILD_PLAN P2a (OPEN, required). Read whole plan §1.1, the P2a section, §14.2 rows M01–M05 and §15.1\'s P2a row first.',
  'The question is a useful leg/domain region for a chosen real expensive consumer, available before that consumer computes. The lead chooses the consumer and the region rule; you report facts.',
  'FORBIDDEN SUBSTITUTIONS: do not compute or report region area fractions, tile-coverage shares or shares of the lens\'s leg outside a region as findings; do not use the lens\'s own leg as a reference for a region meant to precede the lens; do not propose, test or rank any tile or threshold rule; do not read or cite ' + B + '/wave1-packets-20261018/p2a-regions-WITHDRAWN-20261018.',
].join(' ')

async function p2aConsumers() {
  const facts = await agent(COMMON + ' ' + P2A_FRAME + ' ROLE: facts. You work in the main tree and change no code. Attempt directory: ' + dirOf('p2a-consumers') + '. For each expensive per-slice operation that runs on the middle slices or native frames before any anatomical scope exists (start from lens_of/interior_regions, dark_bands, thick_parts and muscle opening, local_lightness, whole-frame enclosed_darkness, block_medians), read whole the operation and every caller, and report: what it reads, when it runs in measure_study, what scope it receives now, which values are already computed before it (finite and margin maps, background split, squint tiles and their bounds, availability), and what decision consumes its output.', { ...SONNET, label: 'p2a-consumers', phase: 'Facts', schema: FACTS })
  if (!complete(facts, 'facts')) return { facts, verdict: null, stopped: 'facts not complete: the lead decides the reissue' }
  const verdict = await agent(COMMON + ' ' + P2A_FRAME + ' ROLE: independent verifier. You work in the main tree and change no code. Attempt directory: ' + dirOf('p2a-consumers-verify') + '. The packet returned: ' + JSON.stringify(facts) + ' Re-derive at least eight of its facts from the whole units and evidence it cites, and list every statement that breaks the forbidden substitutions, presents inference as measurement, or is missing.', { ...SONNET, label: 'p2a-consumers-verify', phase: 'Verify', schema: VERDICTS })
  return { facts, verdict }
}

async function p2aPictures() {
  const facts = await agent(COMMON + ' ' + P2A_FRAME + ' ROLE: prepare evidence. You work in the main tree and change no code. Attempt directory: ' + dirOf('p2a-pictures') + '. Write your drawing script as a file in your attempt directory (never inline code). It adds the absolute path ' + ROOT + '/scripts to sys.path, imports run_interiors as run, opens the corpus with run.opened(Path("' + ROOT + '/data/raw")), reads each study with run.read_study(corpus, uid), and takes each series\' slice the run reads first (read selected_slice and the Series class whole before using them). For the proof and bursa studies, draw each such raw acquired frame and, beside it, the cheap readings that exist before the lens exactly as the runner computes them (the finite map, the margin, the background split as a two-level map, and the squint\'s tile bounds with each tile\'s median, minimum, maximum and coverage as numbers), with no derived region. Record every series, slice, DICOM path and frame geometry in a manifest. Report what each picture shows, and not_done for anything you could not draw.', { ...SONNET, label: 'p2a-pictures', phase: 'Facts', schema: FACTS })
  if (!complete(facts, 'facts')) return { facts, verdict: null, stopped: 'pictures not complete: the lead decides the reissue' }
  const verdict = await agent(COMMON + ' ' + P2A_FRAME + ' ROLE: independent verifier. You work in the main tree and change no code. Attempt directory: ' + dirOf('p2a-pictures-verify') + '. The packet returned: ' + JSON.stringify(facts) + ' Open each picture, check its manifest against the actual frames (geometry, slice, orientation, nothing transposed), re-derive the drawn cheap readings for at least two frames with your own script file, and list every violation of the forbidden substitutions.', { ...SONNET, label: 'p2a-pictures-verify', phase: 'Verify', schema: VERDICTS })
  return { facts, verdict }
}

const results = await parallel([() => p2bChain(), () => p2aConsumers(), () => p2aPictures()])
return { p2b: results[0], p2aConsumers: results[1], p2aPictures: results[2] }
```

Seven agents at most; a chain stops early when its input is not complete. The lead reads every return and
every picture before G1, and records the run in the job table; nothing from W1 is integrated or cited as
accepted until G1's own checks.

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

## 10. Codex's reading and what changed

Codex (GPT-6.1 Sol, model-only, read-only) read revision 1 with the canonical documents inlined and
found "the overall sequence is faithful, but the draft needs corrections before launch", chiefly W1's
execution guarantees, incomplete rule-review scheduling and P12's reduced scope. The lead adopted every
correction, each recorded with its reading in `lead-adjudication.md`. Three W1 findings were already fixed
in the file after the prompt was assembled, and Codex never saw those fixes. No mechanism, contract or
anatomical rule changed in this revision, so there was no second consultation; Codex itself said the
mechanical repairs are the lead's.
