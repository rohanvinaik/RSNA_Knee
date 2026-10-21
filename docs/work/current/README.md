# Active task packet

Sole populated current-state record; FULL_BUILD_PLAN §13 owns this pointer. Revision **133**.
Prior revision 132 is preserved verbatim at `docs/work/history/active-task-packet-revision-132.md`.

## TASK ID / PACKET REVISION / STATE

`THIN-OBJECT-BOOTSTRAP-20261021` / `133` / **execution started**. The anatomy-check correction is
recorded; the signed identity memory, the call adapter and the locator-test repair are in the working
tree; the checkpoint gate, commit and push come next, then the parallel integration lanes.

## CURRENT REQUEST / AUTHORITATIVE EXCHANGES / ACTUAL AUTHORS

Rohan, verbatim: «Good! Record this properly in the full project specs and documentation. Then, when
everything is set up formally, for an external reader/other agent/new session context to
understand...let's do it!» Full record, with the relayed agent review and a relayed side note (both agent
text), at the end of `docs/conversations/2026-10-21-ternary-buckets-and-squint-orchestration.md`. The
review is kept verbatim at `data/readings/ai-bootstrap-loop-20261021/relayed-review-anatomy-check-20261021.md`.

What was decided (the lead's agreement with that review, recorded in CLASSICAL_AI_BUILD_DESIGN §7.1,
§13 step 5 and §14, HOW_TO_BUILD's last section and the OpenSpec change):
- The anatomy check is a law check. A pass records where a candidate lies, never what tissue it is.
  Plausible but wrong tissue is stopped by negative cases in joint recall. No standalone anatomy
  classifier is a prerequisite of growth; the map's distances aim the search and are not admission limits.
- Unchanged: a candidate the check could not judge stays a proposal.
- The first growth round's admissions are inspected on their pictures before its child becomes the next
  parent. Later rounds are spot-checked, not held (the side note caught a first draft that held every
  round). A wrong admission returns as a scoped negative; a recurring failure calls for a new rule drafted
  from the pictures through FULL_BUILD_PLAN §7's review.

## SOURCE HEAD / DIRTY UNITS / MANIFEST / INPUT IDENTITIES

HEAD `f4daf63` (branch `squint-upgrade`) plus the uncommitted thin-bootstrap wave, the unified
documentation and OpenSpec change of revision 132, and this revision's work:
- signed memory: `data/readings/ai-bootstrap-loop-20261021/negative-klines/builder/candidate.patch`
  (sha256 `08d0bb1347658edb…`) applied to code and tests; its bootstrap-guide hunks merged by hand,
  because the guide's interim "positive-only" text no longer holds;
- `adapt_recorded_calls` and an optional per-call `reader` in `squint_bootstrap.py`; the `adapt`
  subcommand of `scripts/squint_object_bootstrap.py`; `tests/test_call_adapter_intent.py`;
- `tests/test_squint_locator.py`: the test pinning teaching-case positions as eligibility priors is
  rewritten to the wave's deliberate meaning (the authored map makes the windows; stored teaching
  positions, which could inherit wrongly named locations, do not decide eligibility). It failed on the
  wave and passes at `f4daf63` with that commit's own source.

Call sources for the first full signed memory (M1), all against review `0c6c657366b78980…`:
`catalogue-called-review-r2/calls-root-r3.json` (`6506d4534354e8d7…`, 76 calls, Codex lead) and
`claude-fill-r1/calls-claude.jsonl` (`1ce48c16fc2ce1f6…`, 365 calls, Claude Code lead); 52 candidates
of the review are still uncalled. Automatic catalogue: `data/readings/lead-repair-20261021/bursa-reencode-r1/curated-memory`.

## OWNER / PERMITTED WRITES / WORKER ROUTES

Root (this Claude Code session) owns intent, shared source, integration and acceptance. Workers run in
isolated worktrees branched from the checkpoint commit and return patches; root integrates.

## CONTRACTS / INPUT AND OUTPUT MEANINGS / REAL CONSUMER

Admission: confident joint identity recall, an affirmative applicable anatomical pass (location only),
no known contradiction and no signed conflict. Unknown-only anatomy: proposal. Contradicted: refused.
Scope: the views that spoke, minus any view a negative speaks through; malformed scope: named refusal.
Every child keeps all signed tables, payloads and lineage; held-out exclusion covers every record kind.

Identity consumer binding (CLASSICAL_AI_BUILD_DESIGN §10 step 5, thesis §11.2): an object recognized as
another identity, or spoken against by negative cases alone, is withheld from its proposed tissue's
condition questions with a named reason. Conflict, no precedent or unknown leaves the structure's own
placement standing, flagged. A withheld object reaches the condition contracts as unmeasured, never as
normal.

## NEXT ACTIONS, IN ORDER

1. Full gate on the final tree; commit by concern with explicit paths; push; read the hook and GitHub.
2. In parallel: workers for (a) signed frozen-parent growth, (b) partial-plane anatomical checks,
   (c) the identity consumer in `infer_study`; root: `adapt` the 441 calls, publish M1 and verify its
   readback and preparation; root: the last 52 visual calls.
3. Integrate, gate, commit, push.
4. Local loop demonstration through the real entry point (only the 58 teaching and 3 public studies have
   images locally): parent, admissions, child, next round reading the child with negatives intact.
5. Real first round in the private Kaggle scaling notebook (`kaggle/squint-scaling/`) over training
   studies, writing a picture sheet per admission; inspect them; promote the child; later rounds
   spot-checked.
6. Timed private dry run of the competition notebook. No submission without Rohan's word.

Report reading is the lowest priority: `train.csv` already carries the twelve study-level labels for all
4,407 studies. It runs only in spare capacity.

## OPEN SEMANTIC CHOICE / PREREQUISITES

None needs Rohan. A concrete near-miss binding that the thesis's §8.6 test cannot settle with the exact
decode goes to him with its episode.

## WORKERS

| Task | State | Evidence |
|---|---|---|
| Signed-memory builder (`a59f12296091c35c5`) | returned; patch applied in the working tree | `negative-klines/builder/` |
| Growth, partial planes, identity consumer | to launch after the checkpoint commit | — |

## UNREVIEWED / WITHDRAWN / STALE RESULTS

The worked example's round two stays withdrawn (it dropped negatives and alternatives; its "new" teachers
were already confirmed). Its README carries the withdrawal. The dry-run child `/tmp/negkl-dryrun/child-r3-signed`
holds only the root calls and is superseded by M1 once published.

## VERIFICATION STILL OWED

Gate on the final tree; M1 readback and preparation; the three lanes' integration and two-sign tests;
the local loop; the Kaggle round and its inspection; the identity consumer's effect on real condition
inputs; the private offline resource envelope. Detective's `validate_calls` result must be redone on
the integrated validator; the `_sanity_status` run failed in the tool, not the suite.

## HANDOFF TIME / EVIDENCE LINKS

2026-10-21, about 21:40 UTC. Squint test family 1,198 passed on the working tree before the gate.
Checkpoint gate log: `data/readings/ai-bootstrap-loop-20261021/checkpoint-r133/gate.log`.
The stray `generated/certificates.json` (a Detective scratch copy) is preserved at
`data/readings/ai-bootstrap-loop-20261021/docs-contracts-r1/generated-certificates.json`.
