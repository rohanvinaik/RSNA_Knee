# Design

Full statement: `docs/OBJECT_MODEL.md`. This records the decisions and their provenance.

## Implementation ownership and later rulings

This change owns the full architecture. `every-stage-renders` owns the immediate
breadth-first pass; `object-resolution-toolkit` owns the measurement/contour substrate.
The founder’s later teaching (Chapter 2, `<object>` and Keller sections) locates anatomy
in the design, not production identity labels. Subjects are indexed visual subsets
and relations, selected by retained structural facts. An anatomical inventory is
human design work, not a runtime naming requirement.

One real-entry-point demonstration establishes a structural mechanism; the 58-study
run is engineering. Existing all-58 tasks below still own that later robustness work.
See `docs/BUILD_PLAN.md` and `docs/RECONCILIATION.md`.

## The decision

A finding is a predicate violation on an object, or on a relation between objects. The build is
ordered by the knee's anatomy rather than by Figure 8's transcribed stages.

Provenance: the founder, 2026-10-11, recorded verbatim in
`docs/chapters/02-collapse/teachings.md`.

## Why an interstice is constructed rather than detected

The findings that read as hard — effusion, synovitis, OA, meniscus, ligament — are about the space
between bones. "Interstitial" is a **relative role**: it means "between these two things". So the
space exists as soon as its two bounding objects do, and nothing has to find it.

This also removes the compartment problem. Medial, lateral, intercondylar and patellofemoral are
enumerated by which bone surfaces face each other. A compartment cannot be missed, because the bones
produce it; and none can be hallucinated, because each requires its two walls.

Consequence for the build: **the bones are scaffolding.** **Ten** of the twelve take a non-bone
subject; **Fracture and Contusion take a bone.** All twelve depend on the bones, because the other
ten's subjects are constructed from them, so the bones are resolved first either way.

*(Corrected 2026-10-12. This read "Zero of the twelve findings is about a bone as such", which
contradicts `docs/OBJECT_MODEL.md`'s own predicate table — Fracture is "break in the structural
coherence of its outline/interior" on a bone (T1), Contusion is "interior (marrow) signal anomaly,
boundary intact" on a bone. `OBJECT_MODEL.md` had already been corrected when Codex reported the
contradiction with both passages quoted; the fix never reached this file.)*

## Why recognition stays mechanical

A knee is a fixed anatomy. Cells need recall because you do not know how many there are, where, or
which; the femur is just the superior bone. Identity follows from invariant relations, so the object
parse uses geometry and the patient frame only.

The thesis's memory, buckets and recall (§8) are therefore **not** in the object parse. They arrive at
diagnosis, for presentations a predicate cannot settle alone. Founder, 2026-10-11: "for now, we should
be able to isolate the components of the knee with NO recognition, pure math."

## Why the fibula settles laterality

Medial/lateral decides four findings and the laterality tag is absent from 181 of 336 series
(measured). The DICOM LPS frame already fixes superior/inferior and anterior/posterior; only "which
patient side is lateral" is unknown, and that is equivalent to knowing left knee from right.

The fibula is lateral to the tibia in both legs without exception, so its direction from the tibia is
the lateral direction. This is a checkable external fact about anatomy, used as a measurement — not a
change to the founder's design. Where no warranted laterality sign resolves, the series abstains. Secondary witnesses
are for concurrence under OBJECT_MODEL; their independent authority when the fibula
is absent is unresolved. Do not silently invent a fallback.

## The homology, and where it is re-derived

Deliberate (founder, 2026-10-11: "Yes, deliberate homology"). The thesis's dome gives every place to
its nearest centre, with nothing cut on strength. The mechanism cannot carry over unchanged, because a
nucleus is brightest at its centre by the optics of a fluorescent source and a bone is not an emitter.

Re-derivation: a bone is a solid bounded by dark cortex, so it is **deepest** at its centre. The
distance transform replaces brightness as the dome's height field, and prominence (not a level) keeps
§6.2's law that a thin bone is never silenced by a thick one. The role survives; the field changes.

The residual loop is the cell project's pull-out, with the same justification: what is left is
definitionally not what has already been resolved.

## What is deferred, and why

- **Baker's.** Its subject is a posterior outpouching of the capsule, adjacent to muscle and tendon
  objects not yet resolved. Deferred to the close of the object parse at the founder's word: "We'll
  address baker's when we finalize this stage, the `<object>` parse."
- **Predicate bars.** No level is set here. Project law 4: every bar is written down before the run
  that judges it, and none is chosen to separate gold. Measurements are reported per class and the
  founder supplies the meaning.
- **Compute.** The founder flagged the trade to be managed, not yet decided: "Will need to balance
  resolution and diagnosis quality with computational efficiency for the competition submission
  pipeline." Language by computation shape and the reference/twin contract are unchanged.

## Relation to `object-resolution-toolkit`

That change is this one's substrate and keeps its contracts. Its tasks 4.1 and 5.1 were gated on the
founder recording the knee teaching; that teaching is now recorded, so both are unblocked.

One follow-up it owns: the founder ruled that the conversation's two retained readings "should carry
one name". `SeriesConversation` currently returns `concurrent_*` and `conditional_*` in parallel; the existing design interprets that as a single named ternary reading per place,
while originals, both derivations and dissent remain inspectable. The merge/precedence
rule is not supplied by this reconciliation, so no two-sign evidence is discarded. This changes a saved record's shape, so it is done
deliberately with its SAME comparison, not silently.
