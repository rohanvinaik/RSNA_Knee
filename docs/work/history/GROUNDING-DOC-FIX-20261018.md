# Active task packet

This is the only populated live-state record. FULL_BUILD_PLAN §13 owns the active task ID/path
index and defines the single handoff template used below. NEXT and the worker guide point to
that index. Worker attempts and acceptance packets are dated evidence, not another live queue.

## TASK ID / PACKET REVISION / STATE

- Task ID: `GROUNDING-DOC-FIX-20261018`.
- Packet revision: 1.
- State: `DOCUMENTATION_COMPLETE`.
- Activity: implement the nine grounding/workflow documentation corrections requested by Rohan.
  This task does not launch a production build or claim new anatomical acceptance.

## CURRENT REQUEST / AUTHORITATIVE EXCHANGES / ACTUAL AUTHORS

Rohan's current instruction: «Please implement these changes, test as needed».
It follows his nine-point relayed audit and the lead's explicit response describing a coordinated
documentation correction. The audit remains relayed agent text, not a quotation authored by him.
The original thesis and the verbatim project conversation records govern meaning; FULL_BUILD_PLAN
§§1–1.2, 7 and 14–15 govern the approved build. Rohan subsequently clarified that the process
listing raises no authorization blocker. No further approval is required for these fixes.

## SOURCE HEAD / DIRTY UNITS / MANIFEST / INPUT IDENTITIES

- Observed HEAD at this task's start: `d3d697c41278053cae25378c547d25faf71ee8c8`.
- Pre-existing edits: FULL_BUILD_PLAN's guide pointer; untracked GROUNDING_AND_WORKER_GUIDE and
  the review under docs/reviews. REPORT.md and VALIDATION_HISTORY.md are unrelated untracked
  files and remain untouched.
- Pre-edit manifest and complete document copies:
  `data/readings/collapse-20261017/full-build/targeted-compute-20261018/grounding-doc-fixes-20261018/before-manifest.json`.
- The same evidence directory holds the global source before-copy/change record and the final
  documentation validation/source manifest. Verify actual live hashes before subsequent work.
- No DICOM/input images, recognition code or production outputs are changed by this task.

## OWNER / PERMITTED WRITES / WORKER ROUTES

This Codex session owns these requested documentation edits. Permitted scope: plan, NEXT, worker
guide, active packet, dated history/review follow-up, and the one stale global routing entry at
its SquishOS owner followed by required sync/check. No commit, push or production-code change.
Evidence/verification helpers are tool-enabled in-session workers; bounded implementation is the
text-only Claude Max route; independent text review is model-only Codex; picture consultation is
Fable API under FULL_BUILD_PLAN §7. This documentation task launches none of those workers.

## CONTRACTS / INPUT AND OUTPUT MEANINGS / REAL CONSUMER

This changes continuation instructions, not anatomical M/F measurements. The consuming agent
must follow plan §0, read the guide whole before dispatch/integration, locate this packet via
§13, and use complete source payloads through the named worker routes. Theory, corrections,
permissions and anatomical definitions stay operative. The single handoff template is in §13;
its populated values and the sole job table are here.

## NEXT SINGLE ACTION / PROPOSED OPERATION / JUSTIFICATION

Report completion to Rohan. The requested documentation fixes and consistency/source-preservation
checks are complete. At the next build continuation, re-ground and verify the actual source/job
basis before using the queued action below.
The next build action retained from the accepted handoff is **P2b increment 2 preflight**: inspect
actual callers/source state, then prepare the refined-leg handoff to `axial_bone_planes` and
`fibula_key_planes` under §14.4. That is queued build work, not a running job or an instruction
to abandon the current documentation request.

## OPEN SEMANTIC CHOICE / PREREQUISITES / OTHER OPEN BUILD ITEMS

Inherited build work, not newly measured status:

- P2a remains OPEN and required. The actual region/consumer capability is not disproved by padded
  rectangles; retain the corrected P2a task in FULL_BUILD_PLAN §5. No replacement rule is chosen here.
- P2b increment 2 remains; inspect changed axial anchors (including AX11/12 when reached) and
  dependent map effects. Increment 1 does not cover those consumers.
- P3 patella/recess/joint context adoption; whether broad sections suit the coarse cut level;
  P4–P11 capacity/structural/output closure in the approved order. P12/P13 retain their explicit
  later-contract/human-specification dependencies.
- Recheck the historical HOW_TO_BUILD owed items before rebuilding: header-free siding, fibula
  transfer to FS sagittal, cross-plane carrying, squint slice choice/compiled twin, repeated fibula
  lens reads and pixel-size duplication. Historical defect descriptions are not live-code findings.
- Recheck the sagittal-meniscus adapter's recorded ledger declaration debt during its next
  applicable family edit; retain it open until evidence settles it.

## ACCEPTED CHECKPOINT / RUN ROOTS / EXACT COMMANDS / EXIT STATUS

Inherited acceptance records: P0 (`7b61b54`, p0-inventory packet), P1 (`19967cd`,
`p1-sartorius-scope-20261018/`), and P2b increment 1 (`2b41281`,
`p2b-bone-context-20261018/README.md` and `verification.md`). Packet paths here use the common root
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/`.

P2b's exact production commands, run roots, exit statuses and receipt comparisons remain in its
source-pinned packet. Its commit records a 1,103-test gate; this task has not rerun it. MAP
§§8.35–8.36 retain the accepted PCL anatomy epoch and its limits. No new production run is made
or acceptance independently repeated here. This task's `global-sync.json` records exit 0 and
`global-check.json` records exit 1. The check reports fresh generated instructions and zero dangling
routes, but separate hook-wiring/inventory findings prevent an overall pass; see global-check.log.
The global owner changed only the one stale unattended-coding route. Documentation preservation/
route checks passed; results are in documentation-checks.json in the evidence directory below.

## INSPECTED IMAGE ADDRESSES / RESULT AND UNKNOWN SEMANTICS

No new anatomical image acceptance in this documentation task. The previous review looked again
at the two canonical thesis figures; its limits remain in docs/reviews/2026-10-18-grounding-review.md.
Missing, uninspected and measured-empty remain distinct. Existing P2b evidence records no refined
consumer at AX11/12 in increment 1. Projected places are location priors, not definitive native
bone/marrow; the component calibration is an anatomical inference, with its changed refusal order.

## CHANGED OUTPUT ADJUDICATION / LEDGER / PROFILE / GATE ADVISORIES

No production output, compute graph, ledger, profiling result or CI advisory is changed/re-measured.
Former NEXT and populated §13 are preserved verbatim in
`docs/history/CONTINUATION_STATE_2026-10-18.md`. Continuing rules/contracts are retained in their
operative homes. Documentation-only checks establish source preservation and route consistency,
not anatomy, throughput or universal drift resistance. The full setup check's hook-wiring findings
(one declared-unwired hook and one orphan), archive manifest gaps and undeclared inventory entries
were recorded without unrelated repair. No recognition CI result is implied.

## WORKERS

The sole current job table follows. Immutable attempts/logs, if later launched, are linked here.

| Task/attempt | Route | Owner | Handle | Dependencies | Output root | Verified state |
|---|---|---|---|---|---|---|
| GROUNDING-DOC-FIX-20261018 | Current tool-enabled session | This session | Current chat; no child handle | Preserved before-manifest | grounding-doc-fixes-20261018 evidence directory | DOCUMENTATION_COMPLETE |
| External/earlier workers | Not attributed | Unknown | Not attributed | Unknown | Earlier packet locations only | UNVERIFIED_EXTERNAL; verify with the owning lead before dispatch/integration |

No worker was launched by this task. This is not a claim that no other process or agent exists.
The broad process listing did not establish project ownership; its output is not retained here.

## UNREVIEWED / WITHDRAWN / STALE RESULTS

The malformed wave-1 P2a packet remains withdrawn at
`wave1-packets-20261018/p2a-regions-WITHDRAWN-20261018/WITHDRAWN.md` under the common readings
root above. Its output cannot accept, rank or dismiss P2a. The six other old wave-1 packets had
interrupted independent checks and remain unaccepted according to the inherited handoff. Recheck
sources, addresses and verification before using any result; presence of a README is not acceptance.
Development ACL/tibial-cartilage/attachment previews remain evidence, not accepted missing selectors.

## VERIFICATION STILL OWED / RECHECK BASIS

Completed for this task: structural consistency, exact historical preservation, unchanged operative
correction/measurement/family contract units, pointer/path checks, global owner sync and its required
check (recorded accurately as an overall failure for separate setup findings). Global generated
instruction renders are verified fresh. Fresh project-client loading of CLAUDE.md and dependency/
preflight automation remain unverified/unimplemented; this task does
not claim to build the guide's proposed G1–G5 enforcement. Before the next build, re-ground and
check actual source/job identities using the current primary record, not this task's old snapshot.

## HANDOFF TIME / EVIDENCE LINKS

Prepared at `2026-10-18T18:35:16.603726+00:00` (UTC). Completed at `2026-10-18T18:38:43.721382+00:00` (UTC).
Evidence root:
`data/readings/collapse-20261017/full-build/targeted-compute-20261018/grounding-doc-fixes-20261018/`.
