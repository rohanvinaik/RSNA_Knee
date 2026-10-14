# Task 4.1: the dispatch answer, and what the predicates stage may decide

The lead's own reading, written before opening either second reader's answer.
Date: 2026-10-12. Unit: `every-stage-renders` task 4.1.

## The question the task forces

`tasks.md` binds 2.4, 3.1 and 4.1 to a recorded dispatch answer, from Codex 2026-10-12:
*"Removing anatomical words from records does not establish that anatomical classification is
absent from dispatch."* For 4.1 the literal question is: **how does a predicate come to receive
`<object>` 3 and 7 rather than 4 and 9 — and which earlier stage computed that fact?** If the
selector is a kind-label, the task stops.

## What the route actually computes today (read whole, this session)

- `knee.ownership.claims.read_ownership` → `claims`/`residual` bool masks over
  `InteriorReading.labels`, plus `claimed_places`, `residual_places`, `unavailable_places`,
  `objects`. Its own docstring: *"A partition, never an identification... the extent is an integer
  index here."* It names no object.
- `knee.relations.pairings.read_pairings` → per profile row `source_labels[P]`, `far_labels[P]`,
  `outcome_codes[P]`, flanking positions and contributor labels. `pair_code` returns `paired` only
  when the near footprint unanimously carries the source extent and the far footprint one
  different positive extent.
- `knee.relations.shell.read_relations` → always `construction_absent`; no interstice is
  constructed.

So the route holds a **relation between two indexed extents**, established at sampled positions
across a dark band. One study, five series: 597 supported pairs.

## My answer, and it is a refusal

`read_pairings` establishes **that** extent *i* faces extent *j*. It does not establish **which
finding's subject that pair is.** Nothing orders the 597 pairs, and nothing distinguishes the pair
that would be Medial OA's subject from Lateral OA's or PF OA's.

The fact that would select it is femur/tibia identity plus the anatomical lateral sign. Identity is
`knee-object-model` task 2.1 — *the founder's to teach*, explicitly stated before any round runs
against it. The lateral sign is task 2.2, unbuilt, and `OBJECT_MODEL.md` records that the frame can
never supply it: in LPS, `S × A = (1,0,0)` is patient-left, which is lateral for a left knee and
**medial for a right one**, so the fibula is the sign and not a cross-check.

**Therefore: no resolved fact in this build selects any finding's subject.** No pair is routed to
any finding. Each of the twelve abstains with a reason naming the subject it required and did not
receive.

That is not a workaround; it is the spec's own scenario. `abstaining-findings`: *"WHEN a finding's
subject is an element no stage has resolved THEN the abstention names the missing subject, rather
than reporting the finding as absent."*

Capacity property 3 — *"the decision reads a RELATION between its subjects, not a property of
one"* — is then carried by `finding_code`'s relational signature and exercised by direct intent
tests, not by a routed production pair. I record that limit rather than letting a built stage imply
a routing it does not perform.

## Two design consequences I believe follow, labelled as my inference

**1. Subjects are named by TIER, never anatomically.** `stage-totality` is explicit: *"A record
schema SHALL NOT contain a field whose values are anatomical names."* The twelve subjects as
written ("a bone", "femur↔tibia medial", "the capsule") are anatomical. `OBJECT_MODEL.md` already
supplies a structural vocabulary — T1 object, T2 interstice of a facing pair, T3 span, T4 envelope
— and keying each finding by **index 0..11** keeps the record clean. The competition's column names
belong to `output`'s serialiser, where the foreign schema is met. Tier also differentiates the
twelve reasons, which the spec requires ("the reason is not the same for every finding unless the
same thing was missing").

**2. The decision's range is named abstentions only — I will not write a violated/within branch.**
Three grounds:
- `predicates/__init__.py` records that the finer form of each predicate is the founder's to teach
  as the subjects become resolvable.
- His words, 2026-10-11: *"LITERALLY, reasoning off objects, mostly as a ternary operation
  (sub-normal/normal/super-normal)."* A binary violated/within collapses two outcomes whose
  remedies differ, which law 3 forbids.
- `e`, the expected correspondence, is hand-given and has not been supplied. Writing the comparison
  would either invent a bar (law 4) or create a path the route never runs.

So `e`'s **declaration** (author and date present or absent) is an argument, and its absence
returns `correspondence_undeclared`. The bars stay arguments; nothing is a constant.

## What I will build

`src/knee/predicates/findings.py`: `finding_code`, total over its arguments, returning named codes,
every bar an argument, reading the relation between two subjects. Then PEP 316 contracts, two-sign
intent tests calling it directly, `just detective converge` with every survivor judged,
`just crosshair --report_all`, wiring into `run_study` **per study** (after the series loop),
a renderer at `knee/pictures/predicates.py` arranging only what the stage computed, a
`places.json` declaration with frame = pipeline state, ledger `predicates.produced`/`consumed`,
a real-study run, the gate, then the record.

A must-not test for the spec's refusal requirement: a gold label or a prior score offered to the
stage is refused, not merely absent from the signature.

## Where I am uncertain, and what is the founder's

1. **May a predicate record carry the competition's column names** (Medial Meniscus, ACL, MCL), or
   must those live only in the serialiser? I have assumed the latter, on `stage-totality`'s literal
   text. His to rule.
2. Whether the twelve should be keyed by index with the mapping deferred, as I propose.
3. Whether `relation_unresolved` and `subject_unresolved` are genuinely two remedies or one.
4. I am **not** asking whether a violated/within branch should exist; I have refused to write it
   absent his teaching. If that refusal is wrong, it is wrong in the conservative direction.
