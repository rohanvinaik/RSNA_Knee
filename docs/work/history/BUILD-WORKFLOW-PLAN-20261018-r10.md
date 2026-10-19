# Active task packet

This is the only populated live-state record. FULL_BUILD_PLAN §13 owns the active task ID/path
index and defines the single handoff template used below. NEXT and the worker guide point to
that index. Worker attempts and acceptance packets are dated evidence, not another live queue.

## TASK ID / PACKET REVISION / STATE

- Task ID: `BUILD-WORKFLOW-PLAN-20261018`.
- Packet revision: 10. Revision 9, as committed in `afc6f03`, is preserved verbatim at
  `docs/work/history/BUILD-WORKFLOW-PLAN-20261018-r9.md`; revision 8, as committed in `a9714a1`, at
  `docs/work/history/BUILD-WORKFLOW-PLAN-20261018-r8.md`; revision 7, as committed in `17a5393`, at
  `docs/work/history/BUILD-WORKFLOW-PLAN-20261018-r7.md`; revision 6, as committed in `7464de9`, at
  `docs/work/history/BUILD-WORKFLOW-PLAN-20261018-r6.md`; revision 5 at
  `docs/work/history/BUILD-WORKFLOW-PLAN-20261018-r5.md`, revision 4 at
  `docs/work/history/BUILD-WORKFLOW-PLAN-20261018-r4.md`, revision 3 at
  `docs/work/history/BUILD-WORKFLOW-PLAN-20261018-r3.md`, revision 2 at
  `docs/work/history/BUILD-WORKFLOW-PLAN-20261018-r2.md`; revision 1 (task `GROUNDING-DOC-FIX-20261018`,
  written by the Codex session) at `docs/work/history/GROUNDING-DOC-FIX-20261018.md`.
- State: `SETTING_UP`. Rohan approved `BUILD_WORKFLOWS.md` revision 4 at 01:01 on 2026-10-19: «Good. I
  approve, continue setting this up», answering the lead's question, which offered approval with the
  reviews' two Fable answers as written and said that on approval the lead does the setup, runs the
  rehearsal, then W1. The plan's §1 records his answers.
- Activity: the plan's §4 preconditions. Done: 1 (the approval and the route change, `afc6f03`), 2 (the
  tools), 3 (the consult checks), and the script and offline mock of the rehearsal R0 (the plan's new §7a).
  Next: the clean tree, the pin and R0's baseline manifest (4), then R0 through the runtime (6). No build
  workflow is launched yet.

## CURRENT REQUEST / AUTHORITATIVE EXCHANGES / ACTUAL AUTHORS

Rohan, verbatim, all recorded in `docs/conversations/2026-10-18-build-session-corrections.md`:
- 18:46: «Made these changes, please look at them and see if they address your concerns, and plan out
  workflows that will complete the specified build of the full project as articulated thus far (Sonnet
  xhigh effort for the agents). Come to me with your full plan when you've designed it, consult codex on
  the plan:», followed by the Codex session's pasted report (agent text, not his words).
- 18:59: «Also, just freaking commit to git. The repo is private, and you've completely invented this
  "private data" issue. ...» (in full in the record).
- After the third compaction, in order: «Just read the codex chat in full to make sure you're grounded»;
  that chat is `codex-answer.md` «And the prompt that triggered it, obviously»; «Obviously, GitHub is for
  code, not for GB's of data»; «Set up sonar as well, using the local setup guidance with the docker
  image»; «Sonar should be part of the CI gate for this project, and a full CI gate should also run upon
  push to github. Code quality/performance engineering, etc»; «Any other code efficiency tooling/actions
  that might be worth adding to GitHub? Anything new, using cursor, or even a standard code
  efficiency/performance engineering toolkit/gate to add in?»
- 19:53, to the lead's two offers: «Don't do 1, do 2, then wait for the agent you launched to report» (the
  global push rule stays; the `.gitignore` comment was reworded, `def77ff`).
- 19:57: «Are those local smells valid and worth investigating? Is the one on GitHub too parsimonius»,
  with a side agent's note on Sonar's new-code bar (agent text, in the record).
- 20:06, to the lead's 20:03 recommendation and tooling suggestions: «Both git and local should use a sane
  profile of Sonar rules. Yes, agree, don't over-fit to targets, only bare correctness issues should be
  blocking» and «Agree with you suggestions, let's work them in». The suggestions it agreed with are the
  lead's text, quoted in the record.
- 20:21, after the fourth compaction: «You can read the transcript to ground, then let's continue with the
  work.»
- 20:50, mid-turn, of the first benchmark draft (synthetic planes with typed-in shapes, masks and sizes):
  «We shouldn't have hardcoded values, wire in the ones we compute in the production path».
- 21:19, after the fifth compaction, answering the lead's report: «Drop the requirements for study data,
  fully build and push everything to github to make sure everything is set up for performance engineering
  sanity and basic quality checks upon push and the pre-push gate. Then show me the workflow plan».
  Revision 2 was shown to him at 22:05.
- 22:08, answering the lead's report (its lines on the missing pre-push hook and on enabling CodSpeed are
  quoted in the record): «Set it as an automatic hook. Also, I set up CodSpeed. Should be good to go,
  finish up everything on the CI/push gate side of things. I'll get back to you with the workflow
  asessment».
- 22:20, mid-turn, a side agent's note that the hook's lockfile audit, as first written, refused every push
  while any dependency had a reported flaw, or when the flaw lists could not be reached (agent text, in the
  record).
- 22:27, after the sixth compaction, to the lead's message that checked the note against the code, named
  two of the lead's mistakes and recommended an audit that names its result and refuses nothing: «Agree
  with your fixes, implement them so we have a working gate/CI action». The recommendation is the lead's
  text, quoted in the record.
- 23:31, after the seventh compaction, to the lead's report on the push gate: «Good enough, this is
  sufficient. I'd like you to look over the workflow plan you wrote up and get instantiated in that task,
  then I'll provide the feedback».
- 23:37: «Feedback on the workflow», followed by a pasted review: agent text, not his words, whose author
  the message does not name (in the record, and verbatim in
  `data/readings/collapse-20261017/full-build/targeted-compute-20261018/workflow-plan-r3-20261018/relayed-review.md`).
  It recommends answers to the plan's two Fable decisions; they are his only when he gives them.
- 2026-10-19, 00:25, after the eighth compaction's lock: «Feedback:», followed by a pasted review of
  revision 3: agent text whose author the message does not name (in the record, and verbatim in
  `data/readings/collapse-20261017/full-build/targeted-compute-20261018/workflow-plan-r4-20261019/relayed-review.md`).
  It recommends the same answers to the two Fable decisions; they are his only when he gives them.
- 00:35, mid-turn: «Note the post-compact hook means that each sub-agent in the workflow should stay under
  a million tokens, which should be entirely doable».
- 01:01: «Good. I approve, continue setting this up», answering the lead's question (lead text, in the
  record): "reply "yes" to approve revision 4 with the review's two Fable answers as written, or tell me
  yours", followed by the two answers and "On "yes" I do the setup steps, run the rehearsal, then W1."
- His process choices of 2026-10-18 stand: Claude as the lead and single writer (11:25); pictures at the
  end of each family wave (11:25); the §7 rule review by Codex plus the Fable consult (17:15). His other
  words of the day, in order, are in the record.

## SOURCE HEAD / DIRTY UNITS / MANIFEST / INPUT IDENTITIES

- Pushed since revision 9 was written: `afc6f03` (the approval record; this packet's revision 9). Its
  pre-push hook found the gate's stamp on that tree, the secret scan found nothing in the lines it adds to
  6 files, and the audit named `no_known_flaws`.
- This revision's commit follows `afc6f03`; `git log` is the record. Its production source changes: none
  (`BUILD_WORKFLOWS.md` §3's source basis and the new §7a, this packet and its history copy). The recording
  in `benchmarks/recorded/` was made from `667e28b`'s production source, unchanged since.
- The workflow tools, untracked under `data/readings/collapse-20261017/full-build/targeted-compute-20261018/workflow-tools/`
  (SHA-256): `spans.py` `017b39c0…`, `callsites.py` `e918add8…`, `assigned_names.py` `67f247d0…` (each
  identical to the lead's scratchpad copy read whole this session), `import_proof.py` `1c39d73c…` and
  `write_manifest.py` `9dd18c8e…` (written for the setup). On a throwaway `git worktree` of `afc6f03`,
  removed after: with `PYTHONPATH=<wt>/src` both `knee` and `run_interiors` import from the worktree
  (exit 0); without it `knee` imports from the main tree through the editable install and the check fails
  (exit 1), the case it exists for.
- The manifest leaves out `archive/` and `archive2/` (166 and 481 tracked files: the writer's dry run
  counted them, and hashed them without reading them; that dry run's file was deleted). The archives are
  invisible, so no agent may read them, and a read of one is outside the frozen basis and stops its chain
  (the plan's §3 now says so).

## OWNER / PERMITTED WRITES / WORKER ROUTES

Owner: the lead (Claude, this session), per Rohan's 11:25 choice. Worker routes are the guide's §6 until
Rohan approves `BUILD_WORKFLOWS.md`; on approval, the guide's implementation row and plan §10 change to
workflow agents in isolated worktrees (his 18:46 words).

## CONTRACTS / INPUT AND OUTPUT MEANINGS / REAL CONSUMER

`BUILD_WORKFLOWS.md` executes FULL_BUILD_PLAN §4's order and §§14–15's contracts; it changes no M/F
contract. Revision 3 added execution rules (its §3): a baseline manifest of every file the agents may read
(every tracked file but this packet, the untracked files the prompts name, and the instruction files that
reach an agent); the instruction files hashed first; the candidate manifest; the script's own check of
every returned HEAD, packet revision and hash; one named outcome per chain and per run
(READY_FOR_LEAD_REVIEW, VERIFICATION_FAILED, INCOMPLETE, STALE_INPUT); the recording, the records and this
packet written before the final gate, which runs last on exactly the tree committed. Revision 4 adds: each
agent's named required inputs, in its prompt and in the script, which refuses to start when the manifest
lacks one and ends a chain INCOMPLETE on a return that leaves one out; each verifier's named required
checks, each to be reported supported; each agent under a million tokens of context (Rohan's 00:35 note);
and the lead carrying the sequence itself through W12 (its §2).

The gate ends with a Sonar step that blocks only on a failed scan or analysis, unread open issues, or an
open bug or vulnerability; its quality gate, smells, coverage and duplication print as information. Its
kernel-costs step (advisory) replays each costly kernel's costliest call from the production run on the
proof study, recorded in `benchmarks/recorded/` by `benchmarks/record_calls.py` (which needs the studies)
and rebuilt exactly by `benchmarks/test_kernels.py` (which needs none). The CodSpeed workflow
(`.github/workflows/codspeed.yml`) runs the same replays under CPU simulation and memory instruments on
every push to main: information, never a required check. Before every push git runs `.githooks/pre-push`
(`scripts/push_checks.py`): the gate unless it passed on exactly the tree being pushed, and a secret scan
of the lines the pushed commits add, either refusing the push when it fails or cannot run; then the
lockfile audit, which names its result and refuses nothing. The GitHub gate runs the same audit before its
gate step, with `continue-on-error`, so the gate always runs.

## NEXT SINGLE ACTION / PROPOSED OPERATION / JUSTIFICATION

The rest of `BUILD_WORKFLOWS.md` §4: a clean tree, the pin and R0's baseline manifest (4: every tracked
file but this packet and the archives, the workflow tools, and the outside instruction file
`~/.claude/CLAUDE.md`), then R0 through the runtime (6: its `runtime` and `stops` parts, then `cancel`, which
the lead stops part-way and relaunches), with what breaks fixed and the mocks re-run; then W1's own pin and
manifest, its outside entries taken from the instruction files R0's agents list, and W1, as his approval
covers. Dropped at his 21:19 words: the self-hosted runner on
this Mac (it existed to give a GitHub job the studies) and downloading the proof study to GitHub's runners.

## OPEN SEMANTIC CHOICE / PREREQUISITES / OTHER OPEN BUILD ITEMS

His two decisions (`BUILD_WORKFLOWS.md` §1) are given, at 01:01: one retry after a diagnosed technical
failure of a billed Fable call; yes to Fable readings of the P2a, P3 and P7 scope sheets, one reading per
scope decision. Before that, his «Agree with you suggestions» (20:06) answered the lead's 20:03 Sonar
recommendation and tooling suggestions, his 21:19 words the study-data question, his 23:31, 23:37 and 00:25
messages asked for and gave feedback on the plan, and his 00:35 note set the sub-agents' context bound.

A fact for running the build while he is away (plan §2): a compaction locks the session that compacted,
the lead's included, until his next message, so an unattended run stops at the lead's first compaction
after he leaves.

The stored recording is the lead's reconciliation of his 20:50 and 21:19 words: production-computed
inputs, no study data needed at check time. It commits 7.29 MiB of arrays derived from the proof study,
and each refresh adds about as much again. The alternative, storing only shapes and parameters and
generating the pixel content, would bring back invented inputs; his call if he prefers it.

Inherited build work, not newly measured: P2a OPEN and required; P2b increment 2 (inspect the changed axial
anchors, including AX11/12 when reached, and map effects); P3; P4–P12 in the approved order; P13 with its
human-specification dependency. The historical HOW_TO_BUILD owed items and the sagittal-meniscus adapter's
ledger declaration debt are rechecked in W2 before anything is rebuilt.

## ACCEPTED CHECKPOINT / RUN ROOTS / EXACT COMMANDS / EXIT STATUS

Unchanged: P0 (`7b61b54`), P1 (`19967cd`, `p1-sartorius-scope-20261018/`), P2b increment 1 (`2b41281`,
`p2b-bone-context-20261018/`).

This task's checks since revision 9, all kept in
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/workflow-setup-20261019/`:
- GitHub, `a9714a1`: the gate (run 39182680126) and CodSpeed (run 39182680061) completed with every step
  succeeding, read from their step summaries (logs kept in `workflow-plan-r4-20261019/github-runs-a9714a1/`).
  GitHub, `afc6f03`: the gate (run 39183934681) and CodSpeed (run 39183934769) completed, success, by the
  watcher's summary (logs kept in `github-runs-afc6f03/`); the push's hook output is `push.log`.
- The consult checks: `consult-budget.txt` (Codex's weekly window 46% used, resetting Saturday 24 October,
  credits 0; Antigravity's weekly quotas untouched) and `anthropic-consult-check.txt` (the key readable from
  its store, 106 characters, its value not printed).
- The offline mocks on the plan with §7a: R0's (`r0_mock.mjs`, SHA-256 `4a79141e…`), 10 of 10 cases as
  expected (`r0-mock.txt`); W1's, 34 of 34 with its script block unchanged (`mock-w1-with-r0.txt`).
- This revision's final gate, `bash scripts/ci_local.sh` on exactly this revision's tree: its whole output
  is kept there as `gate-r0.log`, written after this record, which therefore does not carry its numbers.

## INSPECTED IMAGE ADDRESSES / RESULT AND UNKNOWN SEMANTICS

None new.

## CHANGED OUTPUT ADJUDICATION / LEDGER / PROFILE / GATE ADVISORIES

No recognition output changes. The recording, its same-output checks and its memory figures are as
revision 6 records them
(`docs/work/history/BUILD-WORKFLOW-PLAN-20261018-r6.md`; `benchmarks/recorded/manifest.json`).

## WORKERS

| Task/attempt | Route | Owner | Handle | Dependencies | Output root | Verified state |
|---|---|---|---|---|---|---|
| BUILD-WORKFLOW-PLAN-20261018 | This session | Lead | Current chat | Revision 4, approved 01:01 | `docs/work/current/BUILD_WORKFLOWS.md` | SETTING_UP |
| Codex review of the plan | Model-only Codex consultation (a reader) | Lead | Thread `01a15060-6026-73a2-b841-13cd65b5b0b8`; broker PIDs 46746/46754 stopped and confirmed gone | Revision 1 as inlined in its prompt | `workflow-plan-review-20261018/` | ADJUDICATED (`lead-adjudication.md`) |
| Review of revision 2, pasted at 23:37 | Not attributed: pasted by Rohan; the message does not name its author | Not attributed | Not attributed | Revision 2 | `workflow-plan-r3-20261018/relayed-review.md` | ADJUDICATED (`BUILD_WORKFLOWS.md` §10) |
| Review of revision 3, pasted at 00:25 | Not attributed: pasted by Rohan; the message does not name its author | Not attributed | Not attributed | Revision 3 | `workflow-plan-r4-20261019/relayed-review.md` | ADJUDICATED (`BUILD_WORKFLOWS.md` §10) |
| Research: current CI performance tooling | In-session research helper (Haiku), facts only | Lead | Background agent (finished) | None | Its return, read by the lead and reported at 20:03 | RETURNED, REPORTED |
| GROUNDING-DOC-FIX-20261018 | The Codex session | The Codex session | Not attributed | Revision 1 | `grounding-doc-fixes-20261018/` | DOCUMENTATION_COMPLETE |
| External/earlier workers | Not attributed | Unknown | Not attributed | Unknown | Earlier packet locations only | UNVERIFIED_EXTERNAL |

No build workflow or implementation worker is launched by this task.

## UNREVIEWED / WITHDRAWN / STALE RESULTS

The withdrawn wave-1 P2a packet (`wave1-packets-20261018/p2a-regions-WITHDRAWN-20261018/`) cannot accept,
rank or dismiss P2a; the six other wave-1 packets remain unaccepted until W2 re-checks or regenerates
them; development ACL/tibial-cartilage/attachment previews are evidence, not selectors.

## VERIFICATION STILL OWED / RECHECK BASIS

The GitHub gate run and the CodSpeed run on this revision's commit, read after the push and recorded in the
next revision. The audit has not yet met a reported flaw on GitHub, so how the run page shows a step that
exits 1 under `continue-on-error` is unobserved. The workflow plan is unexecuted: W1's script passes its
offline mock, which checks control flow only; schema enforcement, worktree isolation and imports,
permissions, cancellation, which instruction files reach an agent, and each agent's token use wait for the
runtime rehearsal (its §4), which comes next. Fresh-session loading of the project CLAUDE.md imports remains to be observed.

## HANDOFF TIME / EVIDENCE LINKS

Prepared 2026-10-19T01:10Z. Evidence: this revision's gate log and the setup's records under
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/workflow-setup-20261019/`; revision
4's review, mock, gate log, push and GitHub runs under `.../targeted-compute-20261018/workflow-plan-r4-20261019/`;
revision 3's review, mock, gate log, push and GitHub runs under `.../targeted-compute-20261018/workflow-plan-r3-20261018/`;
the push gate's checks and earlier GitHub runs under `.../targeted-compute-20261018/push-gate-hook-20261018/`;
`docs/work/current/BUILD_WORKFLOWS.md`; the Codex prompt, answer and adjudication under
`.../targeted-compute-20261018/workflow-plan-review-20261018/`; the recording's manifest,
`benchmarks/recorded/manifest.json`, and its evidence under
`.../targeted-compute-20261018/benchmark-recording-20261018/`.
