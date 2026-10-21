# Active task packet

Sole populated current-state record; FULL_BUILD_PLAN §13 owns this pointer. Revision **136**.
Prior revision 135 is preserved verbatim at `docs/work/history/active-task-packet-revision-135.md`.

## TASK ID / PACKET REVISION / STATE

`THIN-OBJECT-BOOTSTRAP-20261021` / `136` / **identity handoff being built**. Rohan corrected the identity
mechanism (2026-10-21/22, his words below): the femur and tibia are told apart by their observed ordering in the
scan's known directions, never by appearance; established information is carried forward and conditions every
later question. Lanes A–F and B's follow-up are integrated and pushed (`3995632`). Workers now: H1 (the
conditioned identity handoff), G2 (diagnosis teaching for new admissions, held-out studies), G3 (correctable
admissions). M1b is being published from all 493 calls.

## CURRENT REQUEST / AUTHORITATIVE EXCHANGES / ACTUAL AUTHORS

**The identity correction (governs everything below).** Rohan, verbatim: «The tibia and femur are ABSURDLY easy
to resolve. Both look almost identical—big fucking bones. But one is "up" and one is "down"» · «How the HELL would
a pipeline that resolves objects visually be able to do cosine similarity match that differentiates the tibia and
the femur. They're BOTH BONES. The fact their cosine similarity scores are so similar is fucking PHENOMENAL
validation ... If you try to "fix" this you will DESTROY everything» · «These scans aren't upside-down. They're...
directional». And a pasted message he sent as his instruction (author not stated): «Carry the established
information forward. Each subsequent question is conditioned on what the system already knows ... known structure
removes alternatives and unnecessary computation. It is not another score to add after an unconstrained appearance
competition. Diagnosis asks about the state of the contextually identified object. Growth stores the warranted
object presentation with that context and lineage. Implement that handoff through preparation, recall, diagnosis
and admission. Do not introduce a new tissue-kind classifier, tune bone profiles apart, or replace anatomical
directions with arbitrary "top half of the image" thresholds.» Full record: the end of
`docs/conversations/2026-10-21-ternary-buckets-and-squint-orchestration.md`; Codex exchanges (agent text) and the
relayed reviews in `data/readings/ai-bootstrap-loop-20261021/codex-bones-20261021/`. Withdrawn by the lead: making
remembered cases out-compete look-alikes (any change to who sets a case's bar meant to make appearance name the
bone), and a tissue-kind table.

Relayed review bindings adopted (agent text): diagnosis teaching is built alongside identity and both are exercised
in the first real round; wrong admissions are correctable as scoped negatives without a full-resolution rebuild; the
repair stays bounded; geometry work (shared alignment, carrying views) returns only if the loop cannot establish the
relations admission needs; a held-out set never enters growth or teaching; an early timed private Kaggle run sets
the latest safe final launch. Rohan: no more Kaggle data calls from the lead («make sure you're not pinging kaggle
too much. I'll just do a zip download over the GUI»; a 1 TB SSD holds it).


Rohan, verbatim: «Good! Record this properly in the full project specs and documentation. Then, when
everything is set up formally, for an external reader/other agent/new session context to
understand...let's do it!» And: «Note one obvious connection--if a diagnosis is clear in one of the three
views (coronal/saggittal/axial), then IF the object is also present in another view, that is an IMMEDIATE
positive k-line» (bound in CLASSICAL_AI_BUILD_DESIGN §5.1 and the OpenSpec requirement "A diagnosis
carries across the views of its object"; lane E builds it). And: «We can skip the long local gate, just
build, push, and report where we are and what we need to do to train the AI». Full records, with the
relayed agent review and side notes (agent text), at the end of
`docs/conversations/2026-10-21-ternary-buckets-and-squint-orchestration.md`; the review verbatim at
`data/readings/ai-bootstrap-loop-20261021/relayed-review-anatomy-check-20261021.md`.

What was decided (the lead's agreement with that review, recorded in CLASSICAL_AI_BUILD_DESIGN §7.1,
§13 step 5 and §14, HOW_TO_BUILD's last section and the OpenSpec change):
- The anatomy check is a law check. A pass records where a candidate lies, never what tissue it is.
  Plausible but wrong tissue is stopped by negative cases in joint recall. No standalone anatomy
  classifier is a prerequisite of growth; the map's distances aim the search and are not admission limits.
- Unchanged: a candidate the check could not judge stays a proposal.
- The first growth round's admissions are inspected on their pictures before its child becomes the next
  parent. Later rounds are spot-checked, not held. A wrong admission returns as a scoped negative; a
  recurring failure calls for a new rule drafted from the pictures through FULL_BUILD_PLAN §7's review.
- Oblique planes (lead decision, CLASSICAL_AI_BUILD_DESIGN §7.2): where neither a complete reference nor an
  exact-normal partial interval determines an axis, an anchor's interval is the exact projection of its own
  observed tile window, built like a candidate's. It is a scope change, measured before acceptance.

## SOURCE HEAD / DIRTY UNITS / MANIFEST / INPUT IDENTITIES

HEAD `fc33758` (branch `squint-upgrade`, clean, pushed). Since `f4daf63`: `20e37e3` signed identity
memory, call adapter, locator-test repair; `1804e00`, `fca0c77`, `40e722b`, `5a51d20` documentation and
packet; `3ed7546` Sonar correctness fix; `d299fbf` lane C; `b699de0` lane D; `0847ff2` lane B part 1;
`ec882a0` lane B fixture anatomy; `fc33758` the sanity digest's reviewed mark and the oblique binding.
GitHub gate: passed on `3ed7546` and `5a51d20` (later runs superseded and cancelled); the run on `fc33758`
is in progress. The local gate is skipped by Rohan's instruction; the GitHub gate runs the full gate on
every push.

**Push incident, 2026-10-21 about 21:58 UTC (the lead's error).** The secret scan refused the added line
of `0847ff2` (`tests/test_squint_sanity.py`, flagged as a high-entropy hex string). The push command piped
the scan through `tail`, which hid its exit status, so the push went out anyway (`b699de0..ec882a0`). The
line is `COMPLETE_MATRIX_SHA256`, the SHA-256 of the canonical JSON of the sanity matrix outputs captured
at `1804e00`, not a secret. `fc33758` marks it with detect-secrets' reviewed mark; that push's scan
passed. Every push now uses the scan's own exit status, never a pipe:
`.venv/bin/python scripts/push_checks.py scan origin/squint-upgrade..HEAD && git push --no-verify origin squint-upgrade`.

Calls for the next memory (M1b), all against review `0c6c657366b78980…`: `catalogue-called-review-r2/calls-root-r3.json`
(76 calls, Codex lead) and `claude-fill-r1/calls-claude.jsonl` (sha256 `a59b361e4ab9ae11…`, 417 calls,
Claude Code lead); adapted together at `signed-memory-m1b/adapted-calls/` (493 calls). Automatic
catalogue: `data/readings/lead-repair-20261021/bursa-reencode-r1/curated-memory`.

## OWNER / PERMITTED WRITES / WORKER ROUTES

Root (this Claude Code session) owns intent, shared source, integration and acceptance. Workers run in
isolated worktrees, fast-forward to `squint-upgrade`, and return commits or patches; root integrates.

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

Diagnosis across views (CLASSICAL_AI_BUILD_DESIGN §5.1): a diagnosed state carries, positive only, to every
view where the same object's identity holds, with one shared study/object lineage; identity scope decides
diagnosis scope, and a view called other tissue carries nothing.

## INTEGRATION ACCEPTANCE CHECKS (from a relayed review, agent text, adopted)

1. Cross-view teaching: a diagnosed state follows the same object into every view where its identity
   holds, with one shared study/object lineage; those presentations enrich recognition and never count as
   independent confirmations.
2. Configuration rebuild: built from confirmed object facets only, keeping each clinical call's actual
   scope (unlocalized bone positives stay unlocalized) and recording missing constituents; unread tissue is
   never treated as observed.
3. Actual consumers: identity changes both condition evidence and the bounded observation requests; the
   stored-case view restriction reaches prepared comparisons, envelopes and the preparation fingerprint, so
   a stale preparation is never reused.
4. Growth demonstration: genuinely new admissions (named apart from existing teachers), a published child
   keeping all signed evidence, and a next round that actually reads that child; the first round inspected.
   The local demonstration comes before any substantial download; then one small batch exercises the whole
   pull, recognition, inspection and publication cycle, resumable and within bounded storage.

## NEXT ACTIONS, IN ORDER

1. Integrate lane E and lane B's follow-up as each returns, and lane F's two fixes: focused tests, commit,
   scan-gated push, read the GitHub gate.
3. Republish the memory (M1b) from the 493 calls with lane E's configuration rebuild and identity-view
   restriction, with its recall preparation; verify readback and preparation.
4. Local loop demonstration through the real entry point: M1b as parent, the 3 public studies inferred,
   `grow`, `sheets`, inspect every admission, publish the child, a next round reading the child with
   negatives intact.
5. First real round: pull a bounded batch of training studies with lane F's tool into
   `data/raw/train_series/`, infer, grow, sheets, inspect, promote; later rounds spot-checked. No growth runs
   on Kaggle (Rohan: «we do not waste kaggle compute on nonsense. We will pull as much data as we need locally
   when it's time to scale the AI part»).
6. Diagnosis teaching at scale: `train.csv`'s twelve study-level labels joined to recognized objects at their
   actual scope (Fracture and Contusion stay unlocalized), carried across the object's identity views.
7. Held-out capacity replay; timed private Kaggle dry run of the competition notebook. No submission without
   Rohan's word.

Report reading is the lowest priority: `train.csv` already carries the twelve study-level labels for all
4,407 studies. It runs only in spare capacity.

## OPEN SEMANTIC CHOICE / PREREQUISITES

None needs Rohan. A concrete near-miss binding that the thesis's §8.6 test cannot settle with the exact
decode goes to him with its episode.

## WORKERS

| Task | State | Evidence |
|---|---|---|
| Signed-memory builder | returned; integrated in `20e37e3` | `negative-klines/builder/` |
| Lane A: signed frozen-parent growth (`squint_identity_growth.py`: harvest from inference records, admission decisions, child publication), `grow` CLI | integrated `c82ead4`, `58ef9fe` (merged with lane D's `sheets` in `scripts/squint_object_bootstrap.py`; 200 focused tests). States: admitted, proposal, blocked (contradicted), conflict, opposed, duplicate, refused. Its own real rounds against M1: 3 public studies, 51 candidates, 0 admitted (34 conflict, 2 opposed, 15 proposal; every law check unknown); 2 teaching studies, 33 candidates (24 duplicate). A child costs about 28 s to save and 299 MB. Open: an admission has no full profile, so a wrong one cannot yet return as a scoped negative (`build_review` refuses it); admitted regions are not location precedents; run guides and OpenSpec boxes not updated | `/tmp/rsna-growth-worker/` |
| Lane B: partial-plane anatomical checks | part 1 integrated `0847ff2` (exact-normal partial intervals; fixture anatomy corrected `ec882a0`). Follow-up running: anchor-window projection for oblique planes, priority complete > exact-normal partial > anchor-window projection > unknown, provenance per check, and a before/after account over the 61 local studies; it stops and reports if a confirmed case is contradicted or a correct bone pair is quarantined | real planes are oblique (median 7°, max 38°) |
| Lane C: identity governs condition inputs in `infer_study` | integrated `d299fbf` (350 focused tests). Loose ends: dependents placed from an anchor later withheld keep their placement; `scripts/squint_visual_capacity.py` shows withheld objects as not located; OpenSpec task 4.1's wording | `tests/test_squint_pipeline_identity_consumption_intent.py` |
| Lane D: picture sheets for admissions (`sheets` CLI), local only | integrated `b699de0` (30 tests); a real sheet inspected (`/tmp/admission-sheets-real/final-mixed/sheet-002-real-t1_femur-8b20e1f9.png`) | merges with lane A's `grow` in `scripts/squint_object_bootstrap.py`: keep both actions |
| Lane E: diagnosis evidence speaks only through identity views (restriction applied before preparation; fingerprint includes identity teaching); positives carry to every identity view; pure label join (Fracture/Contusion unlocalized); whole-condition cases rebuilt from confirmed objects at seed publication | running, isolated worktree | its regression test: a sagittal-only query must not return Fracture `present` from a rejected sagittal bank |
| Lane F: `scripts/pull_competition_studies.py` (paged resumable index; bounded, resumable, label-blind pull in `train_series.csv` order; receipt; disk margin) | integrated `fad9041` (36 tests). Test pull of one study into `/tmp/rsna_pull_test`: 94 files, 61.6 MB, 9.1 s at 24 workers, every file checked as MR DICOM against its path; a rerun skips it with zero writes. Projected, not measured: the full listing about 50 min, all 819,635 files about 22 h at 24 workers. Two defects reproduced by a reviewer (agent text), fix running before any substantial pull: a resumed staged file is trusted by size alone, and `index` with an already-present selection lists everything | `pull --root data/raw --studies N`; state in `data/raw.pull/` |

## M1 THROUGH THE REAL ENTRY POINT (3 public studies, 2026-10-21)

`data/readings/ai-bootstrap-loop-20261021/m1-infer-public-r1/` (source `fc33758`, clean): exit 0, 66 s wall
with 2 workers, 5.45 GB peak RSS, 0 full-anatomy runs, recall preparation recomputed (no sidecar) in 3.7 s,
identity preparation built once and shared (1.6 s). Twelve questions open in all three studies but one
(Lateral Meniscus defeated once). Identity: 10 objects identified, every one as another object than
proposed (prefemoral fat pad, patella, femoral and trochlear cartilage as femur; meniscus, joint fluid and
capsule as joint; fibula as PCL; trochlear cartilage as joint fluid); 18 objects withheld from their
proposed tissue's questions (10 recognized as other, 8 opposed by negative cases alone). None identified as
itself. Bone anchors: study 1 femur partial (sagittal and axial planes), study 2 tibia partial, study 3 no
usable structural anchor. The femur of study 1 is nearest a tibia case (cosine about 0.80; the nearest
femur case about 0.78), and tibia negatives speak too: a conflict. What tells femur from tibia here is
position, which the law checks supply and which are silent on these partial oblique anchors.

## OBLIQUE ACQUISITIONS: MEASURED, AND WHAT STAYS OPEN

Over the 61 local studies (351 series, DICOM orientation; `/tmp/rsna-oblique/acquisitions.json`, its
script beside it): sagittal series tilt from the scanner axes by a median 7.5° (max 20.3°), coronal 9.0° (max
38.3°), axial 4.7° (max 29.9°). Within a study the sagittal and coronal stay perpendicular to a median 1.9°,
and same-orientation series agree to 0.1°: each study's acquisitions share one rotation. Fitting the authored
map to the bootstrap's complete references does not recover it: only 9 of 27 maps with study maps have two
complete bones (17 of 58 have three covered pairs); the fitted axes miss every acquisition by a median 17–30°,
and the map's directions differ from the observed ones by a median 31° before any rotation, 22° after the
best one. The references mark where each bone is most obvious, not the atlas's sites.

Open, explicitly: the one shared anatomical alignment per knee (the relayed note's operation) is not built.
Lane B's anchor-window projection onto patient axes is partial geometry, kept distinct from it. Also open:
carrying a partially anchored bone's selected planes into its missing views as a bounded look (the first
relayed note; `plane_trace_in_frame` gives the trace). Both wait for the first loop demonstration.

## M1, THE FIRST FULL SIGNED MEMORY (published 2026-10-21)

`data/readings/ai-bootstrap-loop-20261021/signed-memory-m1/memory` (manifest sha256 `506dd4ba71db0543…`),
from the automatic catalogue and the 441 calls then made: 152 confirmed positive cases, 311 negative
identity cases, 30 alternative identities, 0 negatives unwritten. The ordinary loader reads it offline and
`prepare_identity` prepares with all 311 negatives and 30 alternatives. Admit took 247 s and 7.9 GB peak
RSS. It has no recall-preparation sidecar and no whole-condition cases; M1b replaces it.

## CALLS COMPLETE; DATA FOR SCALING

All 417 review candidates left to Claude Code are called (the last 52: 16 confirm, 23 reject, 13 unsure).
With root's 76 calls the 493 calls validate together (`signed-memory-m1b/adapted-calls/`): 168 confirmed,
335 negative cases, 30 alternative identities.

The competition serves images for all 4,407 training studies: 819,635 DICOM files, 569.8 GB (about 129 MB
a study); 58 are local (6.6 GB). This machine has 761 GB free, so pulls come in bounded batches through lane
F's tool, never the whole set at once.

## UNREVIEWED / WITHDRAWN / STALE RESULTS

The worked example's round two stays withdrawn (it dropped negatives and alternatives; its "new" teachers
were already confirmed). Its README carries the withdrawal. The dry-run child `/tmp/negkl-dryrun/child-r3-signed`
holds only the root calls and is superseded by M1.

## VERIFICATION STILL OWED

The M1 public run's reading; lanes A, B (follow-up), E and F integration and their two-sign tests; M1b
readback and preparation; the local loop; the first real round and its inspection; the identity consumer's
effect on real condition inputs; the private offline resource envelope. Detective's `validate_calls` result
must be redone on the integrated validator; the `_sanity_status` run failed in the tool, not the suite.

## HANDOFF TIME / EVIDENCE LINKS

2026-10-21, about 22:55 UTC. The r133 local gate was stopped at 35% when Rohan said to skip it
(`data/readings/ai-bootstrap-loop-20261021/checkpoint-r133/gate.log`). The stray `generated/certificates.json`
(a Detective scratch copy) is preserved at
`data/readings/ai-bootstrap-loop-20261021/docs-contracts-r1/generated-certificates.json`.
