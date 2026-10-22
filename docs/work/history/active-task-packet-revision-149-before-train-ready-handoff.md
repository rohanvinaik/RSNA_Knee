# Active task packet

Sole populated current-state record; FULL_BUILD_PLAN §13 owns this pointer. Revision **149**.
Previous packet: `docs/work/history/active-task-packet-revision-148-before-normal-object-export.md`.

## TASK / AUTHOR'S OBJECTIVE / CORRECTION

`HAND-GROUNDED-CORPUS-20261022` / **Hand-build the corpus that bootstraps classical AI.**

Rohan explicitly corrected the lead: recognition is a way to isolate individual anatomical
objects, normal and diseased, so their measured bundles can become K-lines and bootstrap the AI.
We are NOT required to deliver perfect or complete automatic recognition across the 58 before
training. The prior packet and GROUNDED_RECOGNITION imposed that gate incorrectly. That was the
agent's substitution, not Rohan's specification. The latest literal clarification is appended to
`docs/conversations/2026-10-21-ternary-buckets-and-squint-orchestration.md`.

Use actual native images, anatomical reasoning and independently scoped labels/reports to make
visual calls. Useful rough supports and partial views suffice. Select an example directly when
the automatic tool misses it. Preserve normal/diseased meanings, signed identity calls, sources,
available scales/views and the original expectation. Do not manufacture a localized lesion from
a study-wide positive label. All correct examples are useful; no arbitrary seed quota is imposed.
Bucket filling enables the custom Society of Mind training; it is not all of that training.

Rohan's latest explicit rule: the labelled teaching studies give diagnosed conditions; correctly
identified anatomical objects not implicated by their positive conditions form a valid normal
object set. No separate normality annotation or automatic-recognition pass is required. The
official label row and confirmed identity views supply that teaching. Unlabelled studies remain
unlabelled; an implicated multi-site condition retains its actual study/site scope.

## SOURCE / ONE NEWEST MEMORY

HEAD advanced in the shared checkout to `ff5615c` while this work was in progress. Corpus integration
and operational documentation remain dirty; do not attribute another client's commit to this run.
Newest memory: `data/readings/grounded-teaching-20261022/integrated-r4-identity/memory`, **909 cases**.
Manifest sha: `a9b632aa06436a6ed00e0976973abd94cf9ad908841ed31d64a3735a7f280298`.
Preparation sha: `a25e66b6b8f7c8c15bbdd24c8f6a386030dd2db0df33996b0115a9bb283a81fa`.
Chain: 852 -> 876 -> 900 -> 904 -> 909. `integrated-r4-identity/publication.json` records the addition.
Every next publication extends this newest child, retaining signed cases and paired payloads.

## AVAILABLE TEACHING / ACTUAL CONSUMERS

- `docs/teaching/seed_categories.json` and `docs/GROUNDED_TEACHING.md`: hand-defined anatomical
  and normal/diagnosed meanings, with 24 visually reviewed regional examples across 12 conditions.
- `data/readings/grounded-teaching-20261022/references-r3/`: actual pictures, profiles, exact arrays,
  provenance and calls. Two additional reviewed coronal MCL presentations are in
  `cohort-expansion-r1/mcl-coronal-workset/`; both are installed in the 904-case child.
- `scripts/grounded_teaching.py`: measure a hand-addressed teaching specification; `--partial`
  accepts a named subset without weakening review/source requirements.
- `scripts/grounded_recognition.py publish --with-configurations`: publish reviewed examples and
  explicitly linked configurations through the existing signed publisher.
- `grounded_recognition.py replay --through-conditions`: checks the ordinary condition consumers
  on supplied reviewed supports. The 24 original and two additional MCL presentations give their
  intended answers through that route; this is addressed teaching, not automatic generalization.
- `docs/GROUNDED_RECOGNITION.md`: reusable teaching, publication and inspection commands.
- `scripts/publish_visual_cases.py`: ordinary source-tree route for independent identity teaching.
  Five directly inspected proof-study supports were measured and published: medial and lateral
  gastrocnemius, muscle, skin and subcutaneous fat. Actual images, scoped calls, exact HDC arrays
  and round-trip checks are in `handfill-identity-r4/`. No condition calls or full profiles were invented.
- `integrated-r4-identity/condition-consumer-readback.json`: all 26 existing reviewed diagnostic
  references still give their intended answers through ordinary condition consumers on the new child.
- `scripts/prepare_squint_training.py`: source-pinned procedure-material preparation from saved runs.
  The real three-study run produced 120 rows (72 independent condition outcomes, 48 unchecked).
  Saved all-58 readings produced **2,478 rows: 1,394 checked, 1,084 unchecked** in
  `integrated-r4-identity/procedure-material-58/`. No new image inference was needed. Inference and
  teaching memory identities remain separate; ambiguous request attribution remains explicit.
- The same real command now exports the reviewed normal/condition object corpus together with
  the experiences. `integrated-r4-identity/bootstrap-training-material-r1/` holds **234 confirmed
  presentations across 37 object categories: 88 normal, 131 condition presentations, 15 unlabelled**.
  Complete official rows supply normality when no positive condition implicates the object;
  unrelated positive conditions do not disqualify it. The command preserves confirmed-view
  profiles, original condition scopes/full-profile references, the signed tables and backing
  memory pin. No localized lesion is fabricated. `verification.json` independently checks every
  exported state against the label table and hashes the output. The same export retains the
  2,478 experiences above. The 15 unlabelled examples retain identity without normality claims.
- `scripts/near_miss_report.py`: actual correction/expectation/difference retention. Its real command
  retained 335 scoped corrections; their original catalogue proposals have no recalled expectation,
  so all remain explicitly unavailable at that field. Five existing admitted objects were traced to
  their actual recorded precedents; all 92 recorded comparison terms reproduced. This is retention
  and a join check, not a newly learned censor or a claim that the five admissions were corrected.

## LATEST INVESTIGATION / LIMITS

The preceding automatic-recognition investigation is parked, not the next task or a training gate.
Its 58-study reports and refusal ledgers remain evidence. Do not restart automatic locator or
identity-envelope repairs merely because those reports contain open answers.

One concrete scope-wiring repair is already in the dirty tree: reviewed regional native supports
can supply location precedents, and unasserted identity views are withheld in both raw and cached
locator callers. Source: `squint_locator.py`, `squint_anatomy_locator.py`; intent tests:
`tests/test_squint_location_teaching_intent.py`. No multiscale refresh or identity-envelope change
was implemented. Useful measured scope is not tissue certification.

Fresh three-study raw run after that repair: `recognition-scope-r4/`, exit 0, 53.406 s, no full
anatomy run. Three previously open answers became correct negatives; one Effusion answer became
a wrong negative; MCL stayed open on all three. These findings do not block direct hand-teaching
or prove training readiness. `scope-comparison.json` and `source-pins.json` retain exact evidence.

Latest focused corpus/material checks: **121 passed**, including both normal/condition export
intent directions, real CLI input boundaries, procedure retention, signed visual publication and
correction retention. The preceding full suite completed: **5,847 passed in 234.83 s**
(`/tmp/rsna-bootstrap-full-tests-r5.log`), before the new object-corpus export. Ruff and the scoped
type check pass on the corpus/CLI integration. The earlier combined teaching/material checks
had 145 passes, including HDC references and replay; counts are not added together.
Earlier focused checks after the scope repair: 84 locator tests and 124 identity/condition/teaching tests passed;
Ruff passed for the two changed source files and new tests. Whole-project type checking has
existing diagnostics. Earlier Detective certificates remain
UNVERIFIED/withheld after proof-basis collection failures. No complete CI, commit or push is claimed.

## WORKERS / CONSULTATION

The earlier independent identity audit was stopped on Rohan's correction. Subsequent native mechanical
workers integrated the existing near-miss, procedure-retention and visual-publisher tools. Their facts
and code do not replace the author's specification. The bounded normal/condition exporter worker
completed; root integrated it into the actual material-preparation CLI and ran that command on the
909-case child and saved 58-study readings. The full test run and all material commands finished.
No automatic-recognition campaign is running. The normal-state pure decision's Detective audit is
in progress; no new Detective certificate is claimed until its complete report is read.
The authenticated Claude Max CLI consultation at `ai-mechanism-audit-r1/` failed on the weekly
usage limit, with zero inference tokens/cost and no answer. It is not a completed review. Do not
retry blindly or claim Fable agreed. No remote jobs, downloads or sibling memories were launched.

## NEXT SINGLE ACTION / TRAINING HANDOFF

The normal/condition object-bucket export on the 909-case child is finished and verified. Use its
scoped profiles, signed cases and retained experiences for useful hand-teaching and the specified
classical learning. Verified reusable commands are in GROUNDED_RECOGNITION.md. Reuse the existing correct
teaching; do not re-prove automatic recognition or make automatic acceptance a condition of a call.

Check that the installed bundle and its signed meaning reach ordinary recall and the intended
agency consumer. Use the growing corpus for the specified classical training operations and
bring a genuinely unspecified custom update to Rohan as one concrete worked example. No new
recognition-completeness gate, generic learner, score target or deployment detour is authorized.
Actual corpus coverage is recorded as evidence, never invented from a count of stored cases.

Kaggle packaging, uploads and submission remain outside this local task. The detailed previous
measurements remain in the revision-146 history and their immutable evidence roots, not a second
live queue.

Recorded 2026-10-22T12:57:34.156215+00:00.
