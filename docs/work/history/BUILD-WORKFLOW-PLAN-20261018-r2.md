# Active task packet

This is the only populated live-state record. FULL_BUILD_PLAN §13 owns the active task ID/path
index and defines the single handoff template used below. NEXT and the worker guide point to
that index. Worker attempts and acceptance packets are dated evidence, not another live queue.

## TASK ID / PACKET REVISION / STATE

- Task ID: `BUILD-WORKFLOW-PLAN-20261018`.
- Packet revision: 2. Revision 1 (task `GROUNDING-DOC-FIX-20261018`, written by the Codex session,
  state `DOCUMENTATION_COMPLETE`) is preserved verbatim at `docs/work/history/GROUNDING-DOC-FIX-20261018.md`.
- State: `PLAN_FOR_REVIEW`.
- Activity: plan the workflows that carry out FULL_BUILD_PLAN P2b–P11 and prepare P12, consult Codex
  on the plan, and bring it to Rohan. This task launches no workflow and commits nothing.

## CURRENT REQUEST / AUTHORITATIVE EXCHANGES / ACTUAL AUTHORS

Rohan, verbatim: «Made these changes, please look at them and see if they address your concerns, and
plan out workflows that will complete the specified build of the full project as articulated thus far
(Sonnet xhigh effort for the agents). Come to me with your full plan when you've designed it, consult
codex on the plan:». It was followed by a pasted summary of the nine documentation fixes, written by
the Codex session (agent text, not his words). His process choices of 2026-10-18 are recorded
verbatim in `docs/conversations/2026-10-18-build-session-corrections.md`: Claude as the lead and single
writer (11:25 UTC); pictures at the end of each family wave (11:25 UTC); the §7 rule review by Codex
plus the Fable consult (17:15 UTC); «Yes, change that, Codex is the main consult interface».

## SOURCE HEAD / DIRTY UNITS / MANIFEST / INPUT IDENTITIES

- HEAD `d3d697c41278053cae25378c547d25faf71ee8c8`. No production source has changed since `2b41281`.
- Uncommitted: `docs/FULL_BUILD_PLAN.md` and `docs/NEXT_SESSION_PROMPT.md` (the Codex session's edits,
  plus this task's §13 task line); untracked `docs/GROUNDING_AND_WORKER_GUIDE.md`, `docs/reviews/`,
  `docs/history/CONTINUATION_STATE_2026-10-18.md` and `docs/work/` (this packet, its history copy and
  `BUILD_WORKFLOWS.md`). `REPORT.md` and `VALIDATION_HISTORY.md` are unrelated and untouched.
- The Codex session's documentation evidence:
  `data/readings/collapse-20261017/full-build/targeted-compute-20261018/grounding-doc-fixes-20261018/`.

## OWNER / PERMITTED WRITES / WORKER ROUTES

Owner: the lead (Claude, this session), per Rohan's 11:25 choice. Permitted writes for this task:
this packet, §13's task line, `docs/work/current/BUILD_WORKFLOWS.md` and the Codex review evidence.
Worker routes are the guide's §6, with one open decision: whether workflow agents (Sonnet, xhigh,
in isolated worktrees) or the text-only Claude Max worker produce implementation candidates
(BUILD_WORKFLOWS §1.1).

## CONTRACTS / INPUT AND OUTPUT MEANINGS / REAL CONSUMER

BUILD_WORKFLOWS.md executes FULL_BUILD_PLAN §4's order and §§14–15's contracts; it changes no M/F
contract. Its consumer is the build, once Rohan approves.

## NEXT SINGLE ACTION / PROPOSED OPERATION / JUSTIFICATION

Bring BUILD_WORKFLOWS.md and Codex's reading of it to Rohan, with the decisions in its §1. On his
approval: the preconditions in its §4 (the docs-only commit first), then W1.

## OPEN SEMANTIC CHOICE / PREREQUISITES / OTHER OPEN BUILD ITEMS

Rohan's decisions (BUILD_WORKFLOWS §1): implementation route; the docs-only commit; family-wave
pacing; Fable spending and retries; Fable beyond P4–P6.

Inherited build work, not newly measured: P2a OPEN and required; P2b increment 2 (inspect the changed
axial anchors, including AX11/12 when reached, and map effects); P3 (patella, recess and joint context;
whether broad sections suit the coarse cut level); P4–P11 in the approved order; P12/P13 with their
explicit later-contract/human-specification dependencies. Recheck the historical HOW_TO_BUILD owed
items and the sagittal-meniscus adapter's ledger declaration debt before rebuilding anything.

## ACCEPTED CHECKPOINT / RUN ROOTS / EXACT COMMANDS / EXIT STATUS

Unchanged: P0 (`7b61b54`, p0-inventory packet), P1 (`19967cd`, `p1-sartorius-scope-20261018/`), P2b
increment 1 (`2b41281`, `p2b-bone-context-20261018/` README, `verification.md`, `comparisons/`; gate
1,103 tests). Packet paths use the root
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/`. No run is made by this task.

## INSPECTED IMAGE ADDRESSES / RESULT AND UNKNOWN SEMANTICS

None new.

## CHANGED OUTPUT ADJUDICATION / LEDGER / PROFILE / GATE ADVISORIES

None; no production change. The setup check recorded in revision 1 reports the no-grep hook declared
but unwired for Claude Code and the read-whole hook as an orphan: the reading law currently holds by
instruction, which BUILD_WORKFLOWS puts in every agent prompt.

## WORKERS

| Task/attempt | Route | Owner | Handle | Dependencies | Output root | Verified state |
|---|---|---|---|---|---|---|
| BUILD-WORKFLOW-PLAN-20261018 | This session | Lead | Current chat | Revision 1's sources | `docs/work/current/BUILD_WORKFLOWS.md` | PLAN_FOR_REVIEW |
| Codex review of the plan | Model-only Codex consultation (a reader, not a worker) | Lead | Recorded with its answer | BUILD_WORKFLOWS.md as inlined in its prompt | `workflow-plan-review-20261018/` under the root above | PREPARING |
| GROUNDING-DOC-FIX-20261018 | The Codex session | The Codex session | Not attributed | Revision 1 | `grounding-doc-fixes-20261018/` under the root above | DOCUMENTATION_COMPLETE |
| External/earlier workers | Not attributed | Unknown | Not attributed | Unknown | Earlier packet locations only | UNVERIFIED_EXTERNAL |

No workflow or worker is launched by this task.

## UNREVIEWED / WITHDRAWN / STALE RESULTS

As revision 1: the withdrawn wave-1 P2a packet (`wave1-packets-20261018/p2a-regions-WITHDRAWN-20261018/`)
cannot accept, rank or dismiss P2a; the six other wave-1 packets remain unaccepted until W2 re-checks
or regenerates them; development ACL/tibial-cartilage/attachment previews are evidence, not selectors.

## VERIFICATION STILL OWED / RECHECK BASIS

The workflow plan is unexecuted and W1's script is a draft for review. Fresh-session loading of the
project CLAUDE.md imports remains to be observed. Before W1: re-ground, pin the source, and check the
job table against actual handles.

## HANDOFF TIME / EVIDENCE LINKS

Prepared 2026-10-18T18:56:31Z. Evidence: `docs/work/current/BUILD_WORKFLOWS.md`; the Codex prompt and
answer under `data/readings/collapse-20261017/full-build/targeted-compute-20261018/workflow-plan-review-20261018/`.
