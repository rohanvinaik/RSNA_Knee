# The composition repair, 2026-10-12 — what was built, what was measured, what is owed

A dated record. Every number here came from a command run this session, named beside it; recompute
before restating any of it as current. The declared change is `openspec/changes/every-stage-renders`
§6 (`tasks.md`) under `specs/route-composition/spec.md`. The audit this answers is
`docs/HANDOFF_WIRING.md` and its Codex reading (pasted by the founder, 2026-10-12).

## The founder's instruction

> "I need the thing to actually work and be wired right, after which I can actually do the REAL work."

## What changed in the route (`src/knee/pipeline.py`, read whole before and after)

1. **Dependency order.** `run_study` now measures every series (study, collapse, lenses, objects),
   then converses, then per series seats ownership, relations and the bundles with the
   conversation's parse as an input, then runs predicates and output per study. Before: the
   conversation ran LAST, after findings, and reached nothing.
2. **Ownership seats one member per parse** (`knee.ownership.claims.read_ownership_members`):
   solitary, and the conversation's concurrent and conditional subdivisions where it read the
   series; disagreement between solitary and concurrent claims kept as a mask and a count.
3. **Relations carries its pairings** (`knee.relations.shell.read_relations(interiors, spacing_rc)`
   calls `read_pairings` itself); `code` stays `construction_absent` for the unbuilt extent;
   `Interstice` and `KINDS` declared for the construction to fill. `read_pairings` is total over a
   malformed predecessor (`invalid_count`).
4. **Predicates read per-finding construction facts** (`knee.predicates.findings`): each requirement
   names its KIND; candidates are read from every relations record; none → `subject_unconstructed`,
   one → its two extents, several → the new code `dispatch_undeclared`. Population findings carry
   the number of profiles the bundles wrote. `finding_code` takes `candidates: int`.
5. **Consumer-recorded telemetry**: `<producer>.consumed_by.<consumer>` inside lenses, objects,
   conversation, ownership, relations, vectors, predicates and output; the route records only the
   two pinned multi-exit readers. `tests/knee/test_pipeline_composition.py` checks every producer
   has a consumer and every consumer a producer, and the conversation precedes ownership.
6. **Attendance roster** `StudyRun.attendance`; `reached` kept as a telemetry scalar.
7. **Bundles stage body** (`knee.vectors.bundles`, built by a scoped Sonnet builder against the
   lead's contract and intent tests, read whole and admitted): per indexed extent of the selected
   plane, banks `own_reading:<member>`, `lens_standing`, `came_out`, `through_plane:<uid>` (the
   slab rule's first consumer), and the four unavailable banks carried by name. Kernel
   `count_by_extent` with its `ComputeContract`; pure decisions `stage_code`, `bank_status_code`.
8. **Output stage** (`knee.output.projection`): `COLUMN_BY_INDEX` checked as a bijection onto
   `LABELS`; companion record every run; rows refused with `projection_undeclared`.
9. **Study stage retains its walk** (`Series.walk`, `Series.walk_indices`, `Series.slice_codes`;
   one rule `knee.study.series.walk_indices`, read by `knee.pictures.study.panels`).
10. **Every stage draws.** `DRAWINGS` has twelve entries over the nine stages; new renderers
    `study_frames`, `field_frames`, `bundle_frames`, `output_frames`; `partition_frames` draws every
    member and the disagreement; the three new picture adapters only pass values through.
11. **Record corrections** (handoff §8): the four diagnosis packages are "disposition open", not
    "deferred by his ruling"; the relational clause scoped by his Fracture sentence; `places.json`
    without `runs_on_import`; `WIRING_GAPS.md` marked superseded with its false Hypothesis claim
    corrected; `wiring-gaps-fable.md` Q2 struck with the reason.

## Measured on the real study, through the one command

`just analyze-objects --uid 1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149
--tile-mm 3 --span-mm 3 --samples 13 --axis superior --backend jit --prominence-mm 3 --out
data/measurements/composition-20261012` (pictures on; receipt and gallery under those names; facts
computed with the scratch probe `receipt_facts.py` over the receipt).

| measured | value |
|---|---|
| series measured / failures | 5 / none |
| ledger order | `conversation.produced` at index 47, first `ownership.produced` at 53 |
| producers with no consumer | `output` only (the file is its consumer, outside the ledger) |
| consumers with no producer | none |
| attendance | study, collapse, lenses, objects, ownership, vectors, predicates `present`; relations `construction_absent`; output `projection_undeclared` |
| ownership members per series | 3 on all five (the axial series' conversation is `solitary`; its three members agree) |
| disagreeing places, solitary vs concurrent | 225, 464, 290, 215, 0 |
| sample-supported pairs | 114, 116, 231, 41, 95 (597, identical to the audit's count) |
| profiles written by the bundles | 18, 9, 6, 12, 6 (51) |
| findings | 10 `subject_unconstructed`, 2 `form_not_given`; subjects (0,0), candidates 0; the two object findings carry 51 profiles |
| output | `projection_undeclared`, rows None, 12 companion rows in the declared column order |
| gallery | 12 drawn, 0 not drawn, `route_stages_without_a_drawer` empty |

The field, study, ownership, output and bundles frames were viewed; each arranges saved values and
labels every silence. The bundles frame is 51 tables; the builder flagged that the squint
coverage panel is 1.0 everywhere on real data because stored planes are integers.

## Verification standing (each log read whole, `.detective/runs/`)

| unit | Detective | CrossHair |
|---|---|---|
| `findings.finding_code` | COMPLETE 112/112 | all contracts `Not confirmed` (file run) |
| `claims.members_code` | COMPLETE 17/17 after the must-not `test_the_stages_silence_is_the_solitary_members_never_a_later_ones` | `Not confirmed` |
| `claims.comparison_code` | COMPLETE 35/35 | Confirmed over all paths |
| `projection.output_code` | COMPLETE 13/13 | Confirmed over all paths (named run) |
| `bundles.stage_code` | COMPLETE modulo 1 flagged equivalent (`-1`/`-2` both `invalid_count` in `absence_code`) | `Not confirmed` |
| `bundles.bank_status_code` | COMPLETE 4/4 | Confirmed over all paths |
| `bundles.count_by_extent` | **UNGATEABLE** — "one or more mutants could not be BUILT … a defect to report, not a gap to close"; no retry, no waiver, as for every array kernel here | audit wall crash (skimage import while walking the array annotation's subclass map) |
| `shell.read_relations` | COMPLETE modulo 7 unproven + 7 crash-only; 10 flagged with proofs (6 unread `absence_code` arguments, 2 identity `int()`, 2 unused dict defaults) | audit wall crash while realizing a message |
| `series.walk_indices` | not converged this session | `Not confirmed` (file run); the named run cannot import `pydicom` under the audit wall |

The 7 unproven survivors of `read_relations` are ledger event names and counts (`''`, `-1`) that
raise under an enabled ledger, which `test_the_ledger_records_exactly_what_the_stage_read_and_produced`
exercises; Detective's search did not distinguish them and they were NOT flagged, because the lead
cannot prove them equivalent — they are not. Lead's inference, labelled as such: Detective's
isolated observation does not share the process-wide ledger my tests enable. Reported, not acted on.

Both `detective audit` runs propose `--remove` of intent tests redundant for kills and lines. Declined:
intent tests are the specification, and removal is never automatic.

## The gate and the graph

`just places`: 105 declared, none undeclared, none unreached, **17 unwired** (down from 22): the four
diagnosis packages and the thirteen workbench probes. `just graph`: valid. The gate run that
preceded commit `6a98d97`: 760 passed, 1 skipped (the commit message says 759, which was the
full-suite count before the walk tests were added). `ruff` clean. `ty`: 5 advisory diagnostics, all
pre-existing patterns. The gate's own log is scratchpad-kept per run and read whole before each
commit.

Profile: `just profile-tree data/profiles/composition-20261012.html …` on the one command, pictures
off, exit 0. Counted work per stage is the ledger in the receipt; no budget is declared, because a
budget is a bar and bars are the founder's.

## Owed, in the order the loop names

- **6.3a** pairings under the conversed parses (edge-to-piece translation), declared and not built.
- **1.3a's second obligation**: the interstice extent; `Interstice` is the shape it fills.
- The 7 unproven `read_relations` survivors and the two `UNGATEABLE` kernels, as standing.
- `walk_indices` converge; CrossHair for the array kernels needs a route past the audit wall.
- A shared home for the writer's digest check, now copied in six renderers (builder's flag).
- The thirteen workbench probes and the four diagnosis packages: the founder's dispositions.

## What the run leaves open, and shows

These are not asks. Each is a place the running pipeline exposes by name, where the build stops
short by law and the picture carries the question. They resolve the way the founder said the
projection would, "experientially, when actually running and seeing it in action", and not by a
ruling taken in the abstract. (Rewritten 2026-10-12 after the founder struck the earlier heading,
which listed these as rulings for him to issue.)

1. Several constructions of one kind for one finding would return `dispatch_undeclared`, drawn in
   the predicate frame. None arises today, because nothing is constructed.
2. The expected correspondence `e` is carried undeclared in the companion record.
3. The numeric projection is refused by name in the output frame.
4. Every digit map is written with `normalisation: none`.
5. The leg and profile panels of `pictures/collapse.py` stay uncalled until the field stage
   computes what they ask for; the seam and structure probes compute it today outside the route.
6. `memory`, `expert`, `agencies` and `record` are empty packages nothing reaches.
7. Where ownership's members disagree, the disagreement mask is drawn and no member is preferred.
