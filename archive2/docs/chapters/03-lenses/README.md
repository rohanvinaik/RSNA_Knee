# Chapter 3 — THE LENSES: every place, every acquisition, one language

**Read this first in a new session or after a compaction.** Then `docs/OBJECT_MODEL.md` for where
this stage sits, and `docs/STAGE_CONTRACT.md` for what every stage owes.

## The chapter's task, in one line

Write every place of every acquisition as **balanced-ternary digits against its own edge pair**, so
that a tissue class is a *conjunction of rows* rather than a threshold on one image.

## Why it exists: the failure it answers

Four intensity instruments died on this corpus — a quantile, Otsu, the histogram valley, and the
darkest fifth inside the leg (`chapters/02-collapse/teachings.md`). Each failed for one reason: **an
absolute level cannot survive scanner scaling.**

The lead's first design for this stage would have rebuilt that failure one level up, and both second
readers caught it independently. Fable named the mechanism:

> "Subcutaneous fat sits precisely where the coil is brightest; marrow, Hoffa's fat pad and the
> intercondylar structures sit where it is dimmest … **a per-series scalar is still an absolute level
> with respect to position**."

A surface coil falls off 20–40% across the joint. So a single per-series middle is the same mistake
wearing a new coat. **That diagnosis stands and is why this stage exists.**

### The remedy first proposed for it — SUPERSEDED, 2026-10-11

> Kept as history, because the ruling below is only legible against what it replaced. **Do not build
> from these three bullets**; they describe the witness-tissue middle the founder withdrew
> (`teachings.md`, and *A claim withdrawn* below).

- ~~**a row is a PAIR (acquisition, witness)**~~ — "above fat on PD-FS", "at muscle on T1". *A row
  is a pair of (acquisition, metric); the middle names no tissue.*
- ~~**the band carries the witness's own spread**, `k·sqrt(place_sigma² + witness_spread²)`~~. *There
  is no band: a middle is a low edge and a high edge, and no spread enters it.*
- ~~**three fat witnesses at three radii**, their disagreement measuring the bias field~~. *Refuted
  on physics by Fable before the ruling — marrow fat and subcutaneous fat are not one tissue at two
  radii, so their difference confounds coil bias with tissue offset.*

**The remedy that replaced it**, by the founder's ruling: the spatial problem is solved by a **local
structural normalisation before the digit**, and the middle is then a pair of **tercile edges** over
a structurally selected population — carrying no spatial correction at all. The tissue conjunction
moves out of the middle and into the rows **across acquisitions**.

## How it instantiates the thesis

This stage *is* the bundle of figures H2a2 and H2b, which the founder supplied. The sibling crosses
**scale** (voxel · neighbourhood · lens · plate) with **lens** (Gradient · Contrast · Split Quality ·
Dark Share · Composite), and every row is one ternary digit against a **static middle**, shaded by
how many of an object's places wrote it.

For the knee the **lens axis is the acquisitions**, so "fat = bright(non-FS) ∧ dark(FS)" is one row
of one bank. Nothing new was invented: the fingerprint *is* the bundle, re-derived for a different
instrument.

Two laws carry straight across. §1.12's three readings — **a digit of 0 is "a reading at its middle,
not silence"**, and a row no place writes is a different thing entirely. And lineage is a bank, not
metadata: "how its cell came out" sits *inside* the profile.

## Current contract and evidence

`digit_code(place_value, low_edge, high_edge, population_count, minimum_population)`
uses inclusive low/high edges for the middle. `band_width` and the witness/spread
shape are retired. `places.read_lenses` is consumed by `pipeline.run_study`; it writes
full native-volume codes/digits, saves the selected plane and names silence separately.
It records `normalisation: none`. The current lens renderer and saved-record adapter exist.

The [dated run](../02-collapse/measurements/documentation-reconciliation-20261012.md)
observed two `present` series and three `no_edges` series, with the latter drawn as silence.
This is connected candidate behavior. Numeric-map admission remains open in
`every-stage-renders` §2: Detective returned `UNGATEABLE` and array CrossHair was
`Not confirmed` in the retained audit. No claim of current certification follows from
historical scalar counts or the ordinary gate.

`slabs.py` holds the cross-acquisition support decisions, but is not reached by the
current route. A native map is not yet a matched-place conjunction across acquisitions.

### Historical scalar verification (2026-10-11)

The withdrawn witness-middle implementation recorded `digit_code` 93/95, `band_width`
6/6 and `is_read` 4/4, COMPLETE. Slab decisions recorded `slab_code` 55/55,
`gap_fraction` 21/21, `was_measured` 5/5 and `half_thickness` 7/7, COMPLETE.
These describe those source versions only. The lessons below remain history, not
current-digest standing.

### The slab rule, and where silence comes from

The opening question was whether a conjunction across acquisitions needs a common grid. It does not,
and the reason is a fact about the instrument:

> "a 2D multi-slice knee series is not a lattice of points, it is a stack of **slabs**."

A voxel in a 3.5 mm slice measures the whole 3.5 mm slab. So a place inside a foreign slab **is
measured** by that voxel — reading it is not interpolation at all — and a place in the inter-slice
gap was genuinely not measured, so the row is **silent**. `|dot(p − c, n)| ≤ SliceThickness/2`, using
thickness and never `SpacingBetweenSlices`, which includes the gap. Using spacing would silently
claim the gap as measured.

That is §1.12's "nothing said", made geometric by the acquisition rather than by a convention.

The trap that comes with it: **bilinear blending at a cortex–marrow edge manufactures an
intermediate value from a dark and a bright neighbour — and "intermediate" is exactly the cartilage
class.** So a tissue digit reads the containing pixel; bilinear stays confined to the profile rows,
where blending across an edge *is* the measurement.

## What the verification found that the author did not

**Detective pins behaviour at the inputs it tries; CrossHair reasons over all paths.** Both were
needed here, and each caught what the other could not.

- **Detective routes tests by STATIC path.** Nine of thirteen intent tests for `digit_code` called it
  through a local helper and were invisible to the tracer: it traced 4, called two covered lines
  uncovered, and stopped Incomplete at 75/95. Calling the function directly, with the same intents,
  reached 93/95. *An intent test the tracer cannot route is not a pin.*
- **CrossHair found two real defects at 55/55 killed.** `half_thickness(5e-324)` returned 0.0,
  violating `__return__ > 0`, because the smallest subnormal double halves to zero — a positive
  thickness with no representable half-extent. And `gap_fraction(1.0, inf)` returned **NaN**, because
  `inf > 0` satisfies a bare positivity precondition and `inf/inf` is NaN. A NaN gap fraction is
  neither a gap nor an absence of one, and would have propagated into a conjunction's weighting.
- **A surviving mutant pointed at dead code, and the fix was deletion.** Guarding the underflow made
  `thickness_mm <= 0.0` redundant, since `half_thickness(t) <= 0.0` subsumes it. Removing the clause
  killed all five survivors at once. The same dead-clause pattern exists in `border_code`,
  `exchange_code` and `profile_support_code`, written by another hand — there it was left in place,
  because a behaviour-preserving style change belongs to `detective decompose`, not a pinning pass.
- **`just crosshair` was silent on success**, so a run that verified contracts and one that checked
  *nothing* looked identical — the trap `docs/TOOLING.md` names. It now always passes `--report_all`.

Read honestly, the contracts stand thus: `half_thickness`'s and `was_measured`'s post-conditions are
**"Confirmed over all paths"**; the rest are **"Not confirmed"** — no counterexample found, not
proven, and neither a violation nor a pass.

## A claim withdrawn, 2026-10-11

**`witnesses.py` as designed is withdrawn**, by the founder's ruling *"Your inference is correct"*
(`teachings.md`). The knee's middle is a **pair of edges at the terciles of a structurally selected
population**, read *after* a local structural normalisation — so there is no named tissue witness in
the middle, no three-fat-witness stool, and no per-witness spread entering a band. The tissue
conjunction lives in the rows **across acquisitions** instead.

What survives of that work is small and true: **structure selects which places enter the population;
the distribution's own terciles then set the edges.** Both second readers' corrections stand as
anatomy (`readings/witnesses-{codex,fable}.md`) and are kept — a compartment is not a tissue, marrow
can be drawn from the object carrying the finding — but they no longer describe a component to build.

**The old shape was corrected by the later candidate**, not left as the chapter’s next task.
The scalar now takes low/high edges. Current consumers and admission limits are above.

## What remains open

- Local structural normalisation before digitisation: the ordering is settled, the mechanism
  remains founder-supplied. The candidate explicitly applies none.
- Correspondence/support across acquisitions: place conjunction means overlapping support
  inside a matched territory; object conjunction need not mean the same part. Independent
  bright/dark counts cannot be silently combined into one place’s evidence.
- Bundles and their dispatch contract, named banks and missing readings (`every-stage-renders` §3).
- Numeric candidate admission and full engineering evidence (`every-stage-renders` §2).
- Fat-suppression quality, B0-angle and motion readings discussed in the earlier consultations.
  Their meanings remain design questions rather than automatically supplied pipeline stages.

## The readings behind this chapter

- `chapters/02-collapse/readings/lenses-codex.md` — correspondence as a contract; the cyst that
  satisfies the marrow-edema conjunction exactly; four cache boundaries.
- `chapters/02-collapse/readings/lenses-fable.md` — the slab insight; coil falloff; three fat
  witnesses; magic angle, chemical shift, residual red marrow.
- The lead's own design, written before either was opened: `workbench/consults/lenses.md`.
