# Chapter 3 — THE LENSES: every place, every acquisition, one language

**Read this first in a new session or after a compaction.** Then `docs/OBJECT_MODEL.md` for where
this stage sits, and `docs/STAGE_CONTRACT.md` for what every stage owes.

## The chapter's task, in one line

Write every place of every acquisition as **balanced-ternary digits against named witnesses**, so
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
wearing a new coat. The correction, which both readers reached independently:

- **a row is a PAIR (acquisition, witness)** — "above fat on PD-FS", "at muscle on T1" — never a
  place against a series-wide median, which is dominated by whichever tissue is largest and drifts
  with body habitus;
- **the band carries the witness's own spread**, `k·sqrt(place_sigma² + witness_spread²)`, because
  the question is not "is this distinguishable from a number" but "is this indistinguishable from
  the witness *tissue*";
- **three fat witnesses at three radii** — subcutaneous, marrow (a B1 dome's interior), Hoffa's pad
  (constructible as an interstice) — and **their disagreement is the bias-field measurement**.

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

## What is built

| module | what it decides | standing |
|---|---|---|
| `digits.py` | one place's standing against one named witness | `digit_code` 93/95 · `band_width` 6/6 · `is_read` 4/4, all COMPLETE |
| `slabs.py` | did THIS slice measure THAT place | `slab_code` 55/55 · `gap_fraction` 21/21 · `was_measured` 5/5 · `half_thickness` 7/7, all COMPLETE |

Both are pure decisions returning named codes, pinned two-sign: an intent test for what the function
must do, and an enforced must-not for what it must never do.

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

**Consequently `digit_code` has the wrong shape** and is the chapter's first correction: it takes a
`witness_middle` plus a band computed from spreads where §7.2 says a low edge and a high edge, both
in the 0 row. Nothing consumes it (`find_referencing_symbols`: test callers only), so the cost is one
pinned module.

## What is open
2. **`rows.py`** — assembling (acquisition, witness) rows, and Codex's **correspondence contract**:
   a *place* conjunction (overlapping support inside one matched territory) versus an *object*
   conjunction (same object, not necessarily the same part). Without it, one part of an object
   writing "bright on non-FS" and another writing "dark on FS" combine into false evidence that some
   place showed both.
3. **`knee/pictures/lenses.py`** — the stage cannot claim anything but `not_built` without it
   (`docs/STAGE_CONTRACT.md`; enforced by `tests/knee/test_skeleton.py`).
4. **Three rows neither the lead nor the thesis had**: fat-suppression quality per slice, the B0
   angle (magic-angle collagen reads intermediate on short-TE and dark on T2 — the same signature as
   mucoid degeneration, so the angle is "a witness that exonerates"), and the motion offset, which
   point-wise sampling silently bets is zero.

## The readings behind this chapter

- `chapters/02-collapse/readings/lenses-codex.md` — correspondence as a contract; the cyst that
  satisfies the marrow-edema conjunction exactly; four cache boundaries.
- `chapters/02-collapse/readings/lenses-fable.md` — the slab insight; coil falloff; three fat
  witnesses; magic angle, chemical shift, residual red marrow.
- The lead's own design, written before either was opened: `workbench/consults/lenses.md`.
