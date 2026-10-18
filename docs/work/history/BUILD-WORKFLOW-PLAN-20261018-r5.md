# Active task packet

This is the only populated live-state record. FULL_BUILD_PLAN §13 owns the active task ID/path
index and defines the single handoff template used below. NEXT and the worker guide point to
that index. Worker attempts and acceptance packets are dated evidence, not another live queue.

## TASK ID / PACKET REVISION / STATE

- Task ID: `BUILD-WORKFLOW-PLAN-20261018`.
- Packet revision: 5. Revision 4, as committed in `667e28b`, is preserved verbatim at
  `docs/work/history/BUILD-WORKFLOW-PLAN-20261018-r4.md`; revision 3 at
  `docs/work/history/BUILD-WORKFLOW-PLAN-20261018-r3.md`, revision 2 at
  `docs/work/history/BUILD-WORKFLOW-PLAN-20261018-r2.md`; revision 1 (task `GROUNDING-DOC-FIX-20261018`,
  written by the Codex session) at `docs/work/history/GROUNDING-DOC-FIX-20261018.md`.
- State: `PLAN_FOR_REVIEW`; the workflow plan waits for Rohan's approval and is shown to him after this
  revision's commit.
- Activity: the gate's performance and quality tooling, at his 20:06 decision and his 21:19 words, is
  built (this revision's commit); then the workflow plan (`BUILD_WORKFLOWS.md`, revision 2 with one gate
  step added) goes to Rohan. No build workflow is launched by this task.

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
- His process choices of 2026-10-18 stand: Claude as the lead and single writer (11:25); pictures at the
  end of each family wave (11:25); the §7 rule review by Codex plus the Fable consult (17:15).

## SOURCE HEAD / DIRTY UNITS / MANIFEST / INPUT IDENTITIES

- Pushed earlier today: `f405450..d3d697c` (the 262 commits that were only on this machine; evidence in
  `data/readings/collapse-20261017/full-build/targeted-compute-20261018/push-checks-20261018/`), then
  `bb6fe7a`, `dbd36b0`, `def77ff`, `9722caf` (one pinned Sonar on both machines, blocking only on bugs and
  vulnerabilities) and `667e28b` (Ruff's PERF and stable FURB rules, advisory).
- This revision's commit follows `667e28b`; `git log` is the record. Its production source changes: none
  (`benchmarks/`, the gate, the workflows and the documents). The recording in `benchmarks/recorded/` was
  made from `667e28b`'s production source; its manifest lists the uncommitted files at the time, none of
  them production code.

## OWNER / PERMITTED WRITES / WORKER ROUTES

Owner: the lead (Claude, this session), per Rohan's 11:25 choice. Worker routes are the guide's §6 until
Rohan approves `BUILD_WORKFLOWS.md`; on approval, the guide's implementation row and plan §10 change to
workflow agents in isolated worktrees (his 18:46 words).

## CONTRACTS / INPUT AND OUTPUT MEANINGS / REAL CONSUMER

`BUILD_WORKFLOWS.md` executes FULL_BUILD_PLAN §4's order and §§14–15's contracts; it changes no M/F
contract. The gate ends with a Sonar step that blocks only on a failed scan or analysis, unread open
issues, or an open bug or vulnerability; its quality gate, smells, coverage and duplication print as
information. Its kernel-costs step (advisory) replays each costly kernel's costliest call from the
production run on the proof study, recorded in `benchmarks/recorded/` by `benchmarks/record_calls.py`
(which needs the studies) and rebuilt exactly by `benchmarks/test_kernels.py` (which needs none), with
memray's memory at the peak and `--fail-on-increase` against the last successful run on this machine.
The CodSpeed workflow (`.github/workflows/codspeed.yml`) runs the same replays under CPU simulation and
memory instruments on every push to main and compares commits: information, never a required check.

## NEXT SINGLE ACTION / PROPOSED OPERATION / JUSTIFICATION

Done: the Sonar piece (`9722caf`); Ruff's PERF and stable FURB rules (`667e28b`); the kernel benchmarks
on recorded production calls, the memory check and the CodSpeed workflow (this revision's commit; its
GitHub runs are read after the push). Dropped at his 21:19 words: the self-hosted runner on this Mac (it
existed to give a GitHub job the studies) and downloading the proof study to GitHub's runners. Next:
show Rohan the workflow plan. For Rohan: CodSpeed accepts uploads once the repository is enabled on
codspeed.io, a one-time step with his account.

## OPEN SEMANTIC CHOICE / PREREQUISITES / OTHER OPEN BUILD ITEMS

Rohan's approval of `BUILD_WORKFLOWS.md` and its two decisions (§1): a failed billed Fable call (retry or
collect); Fable readings for the P2a, P3 and P7 scope sheets. His «Agree with you suggestions» answered
the lead's 20:03 Sonar recommendation and tooling suggestions, and his 21:19 words the study-data
question; neither is the plan's approval.

The stored recording is the lead's reconciliation of his 20:50 and 21:19 words: production-computed
inputs, no study data needed at check time. It commits 7.29 MiB of arrays derived from the proof study.
The alternative, storing only shapes and parameters and generating the pixel content, would bring back
invented inputs; his call if he prefers it.

Inherited build work, not newly measured: P2a OPEN and required; P2b increment 2 (inspect the changed axial
anchors, including AX11/12 when reached, and map effects); P3; P4–P12 in the approved order; P13 with its
human-specification dependency. The historical HOW_TO_BUILD owed items and the sagittal-meniscus adapter's
ledger declaration debt are rechecked in W2 before anything is rebuilt.

## ACCEPTED CHECKPOINT / RUN ROOTS / EXACT COMMANDS / EXIT STATUS

Unchanged: P0 (`7b61b54`), P1 (`19967cd`, `p1-sartorius-scope-20261018/`), P2b increment 1 (`2b41281`,
`p2b-bone-context-20261018/`). This task's only production runs are the recording's own run of the proof
study (`.venv/bin/python benchmarks/record_calls.py`, into a temporary folder) and the same-output checks
behind it: runs wrapped as the recorder wraps them, inside pytest and outside it, made the same records as
a plain run of the CLI (`scripts/compare_receipts.py`: 5 middle-slice and 12 own-slice records each, none
differing). The replays passed in two separate processes under memray with `--fail-on-increase`, the
second comparing each replay with the first, once plain, and once as CodSpeed's job calls them
(`--codspeed`, walltime mode on this Mac). zizmor at its auditor level found three things in the
workflows (a permission without a comment, two jobs without names), all fixed. The receipts, comparisons
and logs are in `data/readings/collapse-20261017/full-build/targeted-compute-20261018/benchmark-recording-20261018/`
(its `README.md` lists each with its command). The
local gate on this revision: `bash scripts/ci_local.sh`, exit 0 (GATE: PASSED): 1,111 tests passed;
zizmor found nothing in either workflow; the kernel costs passed (9 replays, the third successive run
with `--fail-on-increase`); Sonar 0 open bugs or vulnerabilities and, for information, the same 705
smells by rule; Ruff's PERF/FURB leads the same 7 PERF401; vulture's lists unchanged; deptry and ty
clean.

## INSPECTED IMAGE ADDRESSES / RESULT AND UNKNOWN SEMANTICS

None new.

## CHANGED OUTPUT ADJUDICATION / LEDGER / PROFILE / GATE ADVISORIES

No recognition output changes. The recording (`benchmarks/recorded/manifest.json`): for each kernel the
call that took longest when replayed, out of the run's calls (interior_regions 1 of 53, physical_squint 52
of 164, block_medians 145 of 276, coarse_depth 1 of 46, enclosed_darkness 51 of 63, dark_bands 3 of 5,
local_lightness 1 of 1, thick_parts 68 of 207, background_split 1 of 5); 18 arrays, three of them float64
stored as uint16 because their values are whole numbers that come back with the same digest. Memory at the
replays' peaks, as information (MiB): interior_regions 19.3, enclosed_darkness 16.2, block_medians 4.7,
dark_bands 3.5, thick_parts 2.6, background_split 2.2, local_lightness 1.3, coarse_depth 0.74,
physical_squint 0.28. The kernels call one another, so these overlap and do not add up.

## WORKERS

| Task/attempt | Route | Owner | Handle | Dependencies | Output root | Verified state |
|---|---|---|---|---|---|---|
| BUILD-WORKFLOW-PLAN-20261018 | This session | Lead | Current chat | Revision 2's sources | `docs/work/current/BUILD_WORKFLOWS.md` | PLAN_FOR_REVIEW |
| Codex review of the plan | Model-only Codex consultation (a reader) | Lead | Thread `01a15060-6026-73a2-b841-13cd65b5b0b8`; broker PIDs 46746/46754 stopped and confirmed gone | Revision 1 as inlined in its prompt | `workflow-plan-review-20261018/` | ADJUDICATED (`lead-adjudication.md`) |
| Research: current CI performance tooling | In-session research helper (Haiku), facts only | Lead | Background agent (finished) | None | Its return, read by the lead and reported at 20:03 | RETURNED, REPORTED |
| GROUNDING-DOC-FIX-20261018 | The Codex session | The Codex session | Not attributed | Revision 1 | `grounding-doc-fixes-20261018/` | DOCUMENTATION_COMPLETE |
| External/earlier workers | Not attributed | Unknown | Not attributed | Unknown | Earlier packet locations only | UNVERIFIED_EXTERNAL |

No build workflow or implementation worker is launched by this task.

## UNREVIEWED / WITHDRAWN / STALE RESULTS

The withdrawn wave-1 P2a packet (`wave1-packets-20261018/p2a-regions-WITHDRAWN-20261018/`) cannot accept,
rank or dismiss P2a; the six other wave-1 packets remain unaccepted until W2 re-checks or regenerates
them; development ACL/tibial-cartilage/attachment previews are evidence, not selectors. The earlier
benchmark design (the production run repeated inside pytest, which needed the studies) was replaced before
it was committed.

## VERIFICATION STILL OWED / RECHECK BASIS

The GitHub gate run and the CodSpeed run on this revision's commit. The workflow plan is unexecuted and
W1's script is a draft for review (it parses). Before W1: the plan's §4 preconditions, including the
dry-run worktree. Fresh-session loading of the project CLAUDE.md imports remains to be observed.

## HANDOFF TIME / EVIDENCE LINKS

Prepared 2026-10-18T21:49:45Z. Evidence: `docs/work/current/BUILD_WORKFLOWS.md`; the Codex prompt, answer
and adjudication under `data/readings/collapse-20261017/full-build/targeted-compute-20261018/workflow-plan-review-20261018/`;
the Sonar reports under `.../targeted-compute-20261018/sonar-setup-20261018/`; the recording's manifest,
`benchmarks/recorded/manifest.json`, and its evidence under
`.../targeted-compute-20261018/benchmark-recording-20261018/`.
