# Object resolution: the contract and the continuing build

Recorded 2026-10-11 from the founder's conversation; theory is *What an <Object>
Is*, current sibling thesis. This document persists intent. Run receipts,
saved arrays, tests and current source digests compute implementation standing.

## Responsibility and later rulings

This is the measurement/contour substrate contract, not a second route or the
immediate project checklist. `every-stage-renders` owns breadth-first integration;
`knee-object-model` owns the full architecture. Anatomical names below describe
human design intent; production keeps indexed extents and structural facts.
Thin ownership and sampled pairings now exist as separate candidates; C/D’s full
extent/residual scheduling obligations remain. See `../../BUILD_PLAN.md`.

## The idea we are building

The founder: "Don't look at it by trying to count pixels, look at WHERE those
pixels are." The original red background readings already followed anatomical
borders. Resolving the surrounding field is knowledge about where an object can
be; it is not a cosmetic subtraction made before vision starts.

His correction: "confident resolution of 'background' or 'not <object of
interest>' is *itself* informational in the process of resolving where in the
visual field the object *is*." His latest instruction: "if a lens is correct
and able to discriminate in SOME way between elements, we will find a way that
it is useful and able to perform visual reasoning".

The target is every significant anatomical element relevant to the competition's
12 findings, resolved cleanly and deterministically. We are currently building the resolution,
not diagnosing. Femur and tibia are distinguished through their own geometry,
boundaries and relations in a leg; the space between them becomes a measured
relation between resolved objects. Location alone does not create a bone mask.

## Invariants inherited from the thesis and the founder

1. A lens measures one defined property. An implementation defect is not a
   license to call the definition wrong. A measurement knows no finding question.
2. Interpretation combines readings with the structure of this problem space.
   Constructed orthogonality concerns definitions of claims/questions, never
   empirical decorrelation. Coordinate metrics are a separate numerical matter.
3. Every resolved negative has a scope, source and computational consequence.
   Below a signal level is not a universal statement of irrelevance, nor a
   statement that cortex is not bone. Missing support is not a negative.
4. Original samples, peer material, disputes and unclaimed material remain
   reachable. No low-signal region or small territory is deleted as junk.
5. Territory, observed boundary, object identity and ownership are separate
   records. A watershed divide alone does not warrant anatomical ownership.
6. Each additional operation produces a source-linked, color-annotated image
   series of its actual production record. Rendering cannot compute an alternate
   segmentation. Spatial inspection is part of reasoning, not a score target.

Grounding: thesis §§1.1, 1.2, 1.5, 1.9, 1.10, 1.12, 4.6, 5.2–5.5, 6.1, 7.3,
8.5, 10.5 and 14.1; the complete units and symbolic sibling traces are recorded
in `readings/anatomical-lenses-codex.md` and its workshop resolution.

## The composition, and the pictures that each build owes

| build | reading / structural use | actual image series |
|---|---|---|
| surrounding field | acquired support; low-signal readings; connectivity; physical squint; each exclusion constrains its own search | original → red reading → squint → remaining support |
| interiors and borders (B1 below) | distance from the measured surrounding field; persistent interior peaks; separate territories; native normal profiles and bracketed dark intervals | distance → seeds → all territories → supported traces / open divisions |
| contour conversation (B2) | same-orientation readings of the same knee and objects cross-resolve borders; separate boundary lenses; slope/uncertainty bands; connectivity and permissible movement; keep dissention | both original readings → exchanged constraints → each lens's refinement → agreement / gaps / clipping / shed places |
| object relations (C) | containment, orientation, facing surfaces, joint interval, continuation through physical slices, separately acquired views | object traces → facing surfaces → intervening material → neighboring sections / view disagreement |
| ownership / residual (D) | interpret peers jointly; unchanged own signal; re-read unclaimed material with added context | own object → accounted-for peers → disputes / unclaimed field → next round |
| other knee components | each component's visual profile and role relative to the resolved structures, using its own measurements | patella, cartilage, menisci, ligaments and relevant fluid/tissue each receive the same staged visual accounting |

B1 does not settle the later anatomy or ownership contracts. Those contracts
must encode the actual conjunctions as we build, not promote the output of one
measurement to a final label. Successful negatives are used confidently within
their scope. An unresolved reading remains information, not a failed project.

## B1: geometric interiors and native border evidence

This is the lead's concrete implementation of the founder's surrounding-field
reasoning, recorded before the production build. It introduces no new intensity
classifier. It consumes the existing whole-series background split once.

**Inputs:** selected native 2D plane, its finite support, DICOM frame, existing
split, explicit physical peak prominence and increasing native-profile offsets
containing zero. Demonstration settings are 3 mm prominence and −3…3 mm offsets
at 0.5 mm intervals. These are declared instrument settings, not minimum lesion
sizes or anatomical acceptance bars. Every size remains available in the record.

**Reading 1 — low signal.** `finite & (value <= split)` is exactly that measured
predicate. It constrains the search for an above-split *interior*. It does not
exclude those pixels from a bone, any finding or future reading. Unavailable
split returns `split_unavailable`; its complement is not asserted.

**Reading 2 — distance.** For each available above-split pixel, Euclidean distance
in the orthogonal row/column spacing metric to a low-signal, unavailable or
virtual outside pixel. The virtual guard bounds the computation at acquisition
edges; it is not observed darkness. This metric is explicitly an approximation
to rounded DICOM axes. The record gives the full patient basis and a conservative
distance-error bound. Native profiles use the retained DICOM metric exactly.

**Reading 3 — prominence / connectivity.** Regional h-maxima at the declared
physical prominence produce markers. Four-connected watershed of negative
distance, restricted to available above-split support, yields territories. All
territories and zero/unseeded places are kept. The operation distinguishes broad
interiors connected through narrow passages; it does not classify intensity as
bone, select the largest two, or force a femur/tibia split on axial images.

**Reading 4 — native boundaries.** Enumerate every directed dual-grid edge of
every territory. Record the owner, native midpoint, outward physical-unit normal
and whether it faces measured low signal, another territory, missing acquisition,
unseeded available material, or the frame. No artificial frame closure is an
observed anatomical contour.

**Reading 5 — observed dark intervals.** Sample each edge's native normal within
the requested band using the existing reference / exact JIT twin. A trace is
bracketed only when the entire profile is available and exactly one contiguous
below-split interval has strictly above-split samples on both sides. Save both
interval ends and its midpoint trace. Multiple intervals, unbounded intervals,
missing samples and frame clipping remain distinct. This is a dark-border
measurement, not the only possible border lens. Unsupported divisions remain
visible and available; no contour shortening, forced closure or pixel ownership
transfer is performed by B1.

**Consumers:** Chapter 1's `run_study` reads the series once, obtains the regime,
then supplies its split to `measure_series`. The returned `InteriorReading`
feeds receipts, Hamilton observer nodes, saved-record rendering and SAME.
Separately requested profile direction being unavailable must not suppress this
in-plane geometric reading (including axial).

**Compute:** NumPy performs vectorized edge construction, SciPy EDT and
scikit-image morphology/watershed are library-shaped operations. The repeated
bilinear sample loop uses the already admitted plain reference / Numba twin.
No native C/Rust kernel is warranted by an unmeasured bottleneck. Scratch scales
with N plane pixels and P×S requested samples, P≤4N. Keep shape, dtype, frame,
units, work counts, returned bytes, library versions and source digests. No
whole-volume float64 copy is introduced by this operation.

**Checks before adoption:** synthetic disconnected and neck-connected interiors;
null/empty/all-dark/all-missing/missing split; anisotropic and rounded geometry;
clipped frames; multiple/unbounded dark intervals; immutable original samples;
affine intensity invariance when the split undergoes the same transform; exact
reference/JIT profiles, bands and trace codes. Execute through the real study
entry over the 58, inspect all five view types, and retain misses for the next
structural reading rather than tune to gold or discard them.

## Resumption

Start at `RESUME.md`, then this contract. New receipts/checkpoints and visual
manifests identify the exact source version. OpenSpec records each build as a
declared capability and bounded tasks; Hamilton shows actual consumers. The
next step is read from incomplete tasks and the measured pictures, not invented
from a remembered count. The two oracles and the founder's corrections remain
the authority; Fable's response is an independent reading, never warrant.

## B2 teaching: different readings of the same knee

The founder's 2026-10-11 correction is explicit: "These aren't \"near\", they're
the same, if they're of the same axis of orientation, since they're the same
scan of the same knee." The organizing relation is the shared knee and its
objects. Do not import the cell instance's depth-nearness test as a knee
correspondence or admission rule.

An illustrative case is `interiors-b1-preview/02-interiors.png`: row 3's blue
territory 1 supplies the separation that row 2's orange territory 3 does not
resolve alone. The two coronal weightings are measurements of the same anatomy.
The unresolved border is a place to exchange information, not a reason to
discard either territory. IDs remain local to a reading; the picture and the
shared anatomical context supply this case's meaning, as taught by the founder.

The cell analogy is the **conversation**, not its particular z-distance rule:
thesis §5.4 keeps separate readings, corrects borders where readings agree,
retains a solitary reading and preserves dissent. The live cell route is
`cassette.resolve.one_round → lenses_talk.conversation`; the latter retains
each lens's own `shapes` and `shed`, and `counted_once` separately reasons over
overlap and depth. Its stacked-cell depth mechanism solves the microscope's
problem; it is not a requirement for these same-knee readings.

Next build's contract: carry both sequence records into one production study
conversation; exchange their resolved boundaries in the shared patient frame;
re-read each sequence's native profiles under those constraints; retain original
and refined traces, independent measurements, disputes and missing acquisition.
Coordinate mapping is bookkeeping for expressing the shared object in each
array, not a statistical test of whether the objects are the same. Neither
equal array indices nor equal territory numbers establish pixel correspondence.
No new proximity cutoff, majority label, or final anatomical assignment is
introduced by this teaching.

The founder emphasized that this case is a pointer, not the algorithm. Derive
the general conversation from the thesis and live cell implementation; apply it
to the available readings of the study. Never hard-code this pair, its region
numbers, colors, or an anatomical conclusion drawn just for this picture.

The required B2 pictures show participating readings before conversation, the
boundary information exchanged, and each resulting refinement side by side.
Include the coronal example so the general operation can be inspected there.
Save source series/plane coordinates and the constraint provenance with it.
The complete source trace and the lead's reading are in
`readings/same-knee-conversation-codex.md`.

## B2 implementation boundary and next operation

The checked, pre-run contract is `readings/b2-workshop-resolution.md`; its
production evidence and current-standing commands are in
`measurements/same-knee-conversation-b2.md`. Original bounded bands are exchanged
across every ordered same-orientation pair. Recipient native readings retain
their own split. Acquisition coverage, bounded concurrence, donor-only evidence,
open or multiple runs, disagreement and missing support remain named separately.
Derived intersections stay within their measured sample envelopes and never
become donors in this pass. Both concurrent-only and conditional subdivisions
retain original-parent identities, every piece and explicit barrier cells.

This operation supplies constraints to the subsequent contour build. It neither
bridges unsupported gaps nor declares a territory to be an anatomical object.
Task 3.8 must specify supported connectivity and permissible shortening before
implementation, report closure per chain, and show the original/refined/shed
and unresolved material. Facing surfaces, extent and ownership follow under
their own contracts. Each component in the full anatomy goal receives this
same visual and provenance accounting.
