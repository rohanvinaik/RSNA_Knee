# Active task packet

This is the only populated live-state record. FULL_BUILD_PLAN §13 owns the active task ID/path
index and defines the single handoff template used below. NEXT and the worker guide point to
that index. Worker attempts and acceptance packets are dated evidence, not another live queue.

## TASK ID / PACKET REVISION / STATE

- Task ID: `BUILD-WORKFLOW-PLAN-20261018`.
- Packet revision: 3. Revision 2 is preserved verbatim at
  `docs/work/history/BUILD-WORKFLOW-PLAN-20261018-r2.md`; revision 1 (task `GROUNDING-DOC-FIX-20261018`,
  written by the Codex session) at `docs/work/history/GROUNDING-DOC-FIX-20261018.md`.
- State: `PLAN_FOR_REVIEW`.
- Activity: the workflow plan for FULL_BUILD_PLAN P2b–P12 (`BUILD_WORKFLOWS.md`, revision 2 after Codex's
  reading), brought to Rohan; this task's documents committed and pushed; Sonar made part of the gate and
  the gate run on every push to GitHub. No build workflow is launched by this task.

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
- His process choices of 2026-10-18 stand: Claude as the lead and single writer (11:25); pictures at the
  end of each family wave (11:25); the §7 rule review by Codex plus the Fable consult (17:15).

## SOURCE HEAD / DIRTY UNITS / MANIFEST / INPUT IDENTITIES

- Pushed: `origin/main` moved from `f405450` to `d3d697c` (the 262 commits that were only on this
  machine), after the gate (1,103 tests), the lockfile audit (no known vulnerabilities) and a secret scan of
  the full patch of those commits (detect-secrets 1.5.0: 122 high-entropy findings, every one explained as
  a digest, a message ID or a synthetic DICOM test fixture; no key, token or credential detector fired).
  Evidence: `data/readings/collapse-20261017/full-build/targeted-compute-20261018/push-checks-20261018/`
  (the scan report, each finding mapped to its commit and file by `patch_locations.py`, the gate log);
  the patch itself is `git log -p --no-color f405450..d3d697c`.
- This revision and the plan, the gate and CI changes are committed in the commits that follow
  `d3d697c`; `git log` is the record.
- Production source changes in them: two comment lines (`# NOSONAR(S1244)` with its reason above) on two
  deliberate exact-zero checks (`relative.key_plane`, `assignments.lateral_to_the_head`); no behaviour
  changes. One test made explicit (`test_refined_leg.test_the_identity_follows_the_places_and_nothing_else`).

## OWNER / PERMITTED WRITES / WORKER ROUTES

Owner: the lead (Claude, this session), per Rohan's 11:25 choice. Worker routes are the guide's §6 until
Rohan approves `BUILD_WORKFLOWS.md`; on approval, the guide's implementation row and plan §10 change to
workflow agents in isolated worktrees (his 18:46 words).

## CONTRACTS / INPUT AND OUTPUT MEANINGS / REAL CONSUMER

`BUILD_WORKFLOWS.md` executes FULL_BUILD_PLAN §4's order and §§14–15's contracts; it changes no M/F
contract. The gate now ends with a blocking Sonar step (`scripts/sonar_local.py gate`: quality gate OK,
no open bug or vulnerability) and runs on GitHub for every push (`.github/workflows/gate.yml`).

## NEXT SINGLE ACTION / PROPOSED OPERATION / JUSTIFICATION

Bring `BUILD_WORKFLOWS.md` revision 2, Codex's reading and the lead's adjudication, the gate/CI result and
the answer to his tooling question to Rohan. On his approval: the plan's §4 preconditions, then W1.

## OPEN SEMANTIC CHOICE / PREREQUISITES / OTHER OPEN BUILD ITEMS

Rohan's two decisions (`BUILD_WORKFLOWS.md` §1): a failed billed Fable call (retry or collect); Fable
readings for the P2a, P3 and P7 scope sheets.

Inherited build work, not newly measured: P2a OPEN and required; P2b increment 2 (inspect the changed axial
anchors, including AX11/12 when reached, and map effects); P3; P4–P12 in the approved order; P13 with its
human-specification dependency. The historical HOW_TO_BUILD owed items and the sagittal-meniscus adapter's
ledger declaration debt are rechecked in W2 before anything is rebuilt.

## ACCEPTED CHECKPOINT / RUN ROOTS / EXACT COMMANDS / EXIT STATUS

Unchanged: P0 (`7b61b54`), P1 (`19967cd`, `p1-sartorius-scope-20261018/`), P2b increment 1 (`2b41281`,
`p2b-bone-context-20261018/`). No real-CLI run is made by this task. Gate and CI results: below.

## INSPECTED IMAGE ADDRESSES / RESULT AND UNKNOWN SEMANTICS

None new.

## CHANGED OUTPUT ADJUDICATION / LEDGER / PROFILE / GATE ADVISORIES

No recognition output changes (comment lines and a test only). Sonar's first analysis of the code as it
stood (report `sonar-setup-20261018/report-1.json`): 0 vulnerabilities, 0 security hotspots, 3 bugs (a
test assertion comparing an expression with itself, and two float equality checks), 726 code smells,
88.9% coverage, 1.8% duplication, 31,395 lines of code. The two float checks are deliberate exact-zero
tests (read whole: only an all-zero normal cannot be scaled; only the sign of `along` is used) and carry
`# NOSONAR(S1244)` with the reason above; the test now asserts its two legs are distinct objects before
comparing their identities. Vulture's advisory lists are unchanged (22 production names, the P9 leads).

## WORKERS

| Task/attempt | Route | Owner | Handle | Dependencies | Output root | Verified state |
|---|---|---|---|---|---|---|
| BUILD-WORKFLOW-PLAN-20261018 | This session | Lead | Current chat | Revision 2's sources | `docs/work/current/BUILD_WORKFLOWS.md` | PLAN_FOR_REVIEW |
| Codex review of the plan | Model-only Codex consultation (a reader) | Lead | Thread `01a15060-6026-73a2-b841-13cd65b5b0b8`; broker PIDs 46746/46754 stopped and confirmed gone | Revision 1 as inlined in its prompt | `workflow-plan-review-20261018/` | ADJUDICATED (`lead-adjudication.md`) |
| Research: current CI performance tooling | In-session research helper (Haiku), facts only | Lead | Background agent | None | Its return, read by the lead | RUNNING |
| GROUNDING-DOC-FIX-20261018 | The Codex session | The Codex session | Not attributed | Revision 1 | `grounding-doc-fixes-20261018/` | DOCUMENTATION_COMPLETE |
| External/earlier workers | Not attributed | Unknown | Not attributed | Unknown | Earlier packet locations only | UNVERIFIED_EXTERNAL |

No build workflow or implementation worker is launched by this task.

## UNREVIEWED / WITHDRAWN / STALE RESULTS

The withdrawn wave-1 P2a packet (`wave1-packets-20261018/p2a-regions-WITHDRAWN-20261018/`) cannot accept,
rank or dismiss P2a; the six other wave-1 packets remain unaccepted until W2 re-checks or regenerates
them; development ACL/tibial-cartilage/attachment previews are evidence, not selectors.

## VERIFICATION STILL OWED / RECHECK BASIS

The workflow plan is unexecuted and W1's script is a draft for review (it parses). Before W1: the plan's
§4 preconditions, including the dry-run worktree. Fresh-session loading of the project CLAUDE.md imports
remains to be observed.

## HANDOFF TIME / EVIDENCE LINKS

Prepared 2026-10-18T19:46:16Z. Evidence: `docs/work/current/BUILD_WORKFLOWS.md`; the Codex prompt, answer
and adjudication under `data/readings/collapse-20261017/full-build/targeted-compute-20261018/workflow-plan-review-20261018/`;
the Sonar reports under `.../targeted-compute-20261018/sonar-setup-20261018/`.
