# Active task packet

This is the only populated live-state record. FULL_BUILD_PLAN §13 owns the active task ID/path
index and defines the single handoff template used below. NEXT and the worker guide point to
that index. Worker attempts and acceptance packets are dated evidence, not another live queue.

## TASK ID / PACKET REVISION / STATE

- Task ID: `BUILD-WORKFLOW-PLAN-20261018`.
- Packet revision: 4. Revision 3 is preserved verbatim at
  `docs/work/history/BUILD-WORKFLOW-PLAN-20261018-r3.md`, revision 2 at
  `docs/work/history/BUILD-WORKFLOW-PLAN-20261018-r2.md`; revision 1 (task `GROUNDING-DOC-FIX-20261018`,
  written by the Codex session) at `docs/work/history/GROUNDING-DOC-FIX-20261018.md`.
- State: `PLAN_FOR_REVIEW`; the workflow plan waits for Rohan's approval.
- Activity: the workflow plan for FULL_BUILD_PLAN P2b–P12 (`BUILD_WORKFLOWS.md`, revision 2 after Codex's
  reading) is with Rohan. Meanwhile, at his 20:06 decision, the gate's tooling: Sonar pinned to one server,
  scanner and rule set on both machines and blocking only on bugs and vulnerabilities (this revision);
  then Ruff's PERF and stable FURB rules as an advisory step, benchmarks of the hot kernels with memory
  limits, and a real-data performance job on a self-hosted runner on this Mac. No build workflow is
  launched by this task.

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
- His process choices of 2026-10-18 stand: Claude as the lead and single writer (11:25); pictures at the
  end of each family wave (11:25); the §7 rule review by Codex plus the Fable consult (17:15).

## SOURCE HEAD / DIRTY UNITS / MANIFEST / INPUT IDENTITIES

- Pushed earlier today: `f405450..d3d697c` (the 262 commits that were only on this machine; evidence in
  `data/readings/collapse-20261017/full-build/targeted-compute-20261018/push-checks-20261018/`), then
  `bb6fe7a` (plan, docs, Sonar gate, CI), `dbd36b0` (a worker's historical report) and `def77ff`
  (zizmor in the gate, manual gate runs, grouped Dependabot updates, the `.gitignore` comment).
- This revision's commit follows `def77ff`; `git log` is the record. Its production source changes: none
  (the gate's Sonar tool, its settings and the documents only).

## OWNER / PERMITTED WRITES / WORKER ROUTES

Owner: the lead (Claude, this session), per Rohan's 11:25 choice. Worker routes are the guide's §6 until
Rohan approves `BUILD_WORKFLOWS.md`; on approval, the guide's implementation row and plan §10 change to
workflow agents in isolated worktrees (his 18:46 words).

## CONTRACTS / INPUT AND OUTPUT MEANINGS / REAL CONSUMER

`BUILD_WORKFLOWS.md` executes FULL_BUILD_PLAN §4's order and §§14–15's contracts; it changes no M/F
contract. The gate ends with a Sonar step (`scripts/sonar_local.py gate`) that blocks only when the scan
or its analysis fails, when the open bugs and vulnerabilities cannot be read, or when one is open; the
quality gate, smells by rule, coverage and duplication print as information. SonarQube 26.10.0.133078
and the SonarScanner CLI 8.1.0.6389 image are pinned by digest, with the "Sonar way comprehensive" rules
set on the project and read back, on this machine and on GitHub (`.github/workflows/gate.yml`, every
push).

## NEXT SINGLE ACTION / PROPOSED OPERATION / JUSTIFICATION

Push this revision's commit and read its GitHub gate run (the same images and rule set must show
there). Then the rest of his 20:06 agreement, each its own gated commit, push and GitHub run: Ruff's PERF
and stable FURB rules as an advisory gate step; benchmarks of the hot kernels (pytest-codspeed, a
CodSpeed job off until its GitHub app is connected, pytest-memray memory limits), all information; a
self-hosted runner on this Mac running the real CLI on the proof and bursa studies after a push to main.

## OPEN SEMANTIC CHOICE / PREREQUISITES / OTHER OPEN BUILD ITEMS

Rohan's approval of `BUILD_WORKFLOWS.md` revision 2 and its two decisions (§1): a failed billed Fable call
(retry or collect); Fable readings for the P2a, P3 and P7 scope sheets. His «Agree with you suggestions»
answered the lead's 20:03 Sonar recommendation and tooling suggestions; it is not the plan's approval.

Inherited build work, not newly measured: P2a OPEN and required; P2b increment 2 (inspect the changed axial
anchors, including AX11/12 when reached, and map effects); P3; P4–P12 in the approved order; P13 with its
human-specification dependency. The historical HOW_TO_BUILD owed items and the sagittal-meniscus adapter's
ledger declaration debt are rechecked in W2 before anything is rebuilt.

## ACCEPTED CHECKPOINT / RUN ROOTS / EXACT COMMANDS / EXIT STATUS

Unchanged: P0 (`7b61b54`), P1 (`19967cd`, `p1-sartorius-scope-20261018/`), P2b increment 1 (`2b41281`,
`p2b-bone-context-20261018/`). No real-CLI run is made by this task. The local gate on this revision:
`bash scripts/ci_local.sh`, exit 0, 1,111 tests passed (the 1,103 before and the 8 of
`tests/test_sonar_gate.py`).

## INSPECTED IMAGE ADDRESSES / RESULT AND UNKNOWN SEMANTICS

None new.

## CHANGED OUTPUT ADJUDICATION / LEDGER / PROFILE / GATE ADVISORIES

No recognition output changes. The local Sonar server was rebuilt on the pinned image (`sonar_local.py
rebuild`: the 26.8 container, its data volume and its credentials removed; new credentials minted outside
the repo). Its first analysis with the comprehensive rules (407): 0 open bugs, 0 vulnerabilities, 0
security hotspots; for information, quality gate OK, 88.9% coverage, 1.8% duplication, 31,395 lines of
code and 705 code smells (520 S9073 composite asserts in tests, 103 S3776 cognitive complexity, 51 S3358
nested conditional expressions, 9 S5778, 4 S6796, 3 each S1192/S1172/S1515, 2 each S1854/S5886, 1 each
S7500/S7508/S7516/S3516/S1940). Vulture's advisory lists are unchanged (22 production names, the P9
leads); deptry and ty clean.

Why the 0 is a reading and not a silence: it is the open-issue search's own total (HTTP 200), and the
same issue-type filter returned the 705 code smells, so the type field is filled on 26.10. The blocking
decision is the pure `blocking_failures`, pinned by `tests/test_sonar_gate.py`: open issues, a refused
search and an answer with no issue list each block, as do a failed scan or analysis. Run on the real 26.8
answer with its 3 open bugs (`sonar-setup-20261018/report-1.json`), it blocks: "3 open bugs or
vulnerabilities".

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
them; development ACL/tibial-cartilage/attachment previews are evidence, not selectors.

## VERIFICATION STILL OWED / RECHECK BASIS

The GitHub gate run on this revision's commit. The workflow plan is unexecuted and W1's script is a draft
for review (it parses). Before W1: the plan's §4 preconditions, including the dry-run worktree.
Fresh-session loading of the project CLAUDE.md imports remains to be observed.

## HANDOFF TIME / EVIDENCE LINKS

Prepared 2026-10-18T20:34:43Z. Evidence: `docs/work/current/BUILD_WORKFLOWS.md`; the Codex prompt, answer
and adjudication under `data/readings/collapse-20261017/full-build/targeted-compute-20261018/workflow-plan-review-20261018/`;
the Sonar reports under `.../targeted-compute-20261018/sonar-setup-20261018/`.
