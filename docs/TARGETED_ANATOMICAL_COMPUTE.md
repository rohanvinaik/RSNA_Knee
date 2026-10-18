# Foundational epistemology: anatomical priors target the compute

Rohan's specification, 2026-10-18, is foundational to the entire pipeline's construction: this is
both how recognition becomes more correct and how computation becomes cheaper. It is part of the
`<object>` thesis, not an optional optimization or a requirement limited to the current build stage.
His complete messages are recorded verbatim in
`docs/conversations/2026-10-18-anatomical-priors-and-targeted-compute.md`.
This governs work through the existing production entry point and extends
THREE_VIEW_PRODUCTION_EXECUTION; it does not introduce another pipeline or the later AI layer.

> The solution there is to make the background/"bounding boxes" not perfect, but useful. THAT'S the key--"usefulness" if it CAN do something useful with a symbolic process, that's enough. Later AI layers can handle the rest

> This is about establishing priors, not being perfectly correct

## The mechanism

Resolve useful structure cheaply, then spend finer computation where that structure points.
The knee is one connected physical system. Muscle attaches to bone; vessels relate to muscle and
bone; marrow is within bone; joint fluid lies between the bones and in their recesses. Resolving
one part constrains several other questions. This joint physical structure improves discrimination
at the same time that it reduces the search. Those relationships must restrict the places read by
the next measurement, rather than merely annotate a result after a whole-image analysis.

The squint, rough leg/background distinction, selected native slices and anatomical map establish
the prior. Their bounds need not be exact segmentations. Native measurements refine that prior.
A projected source or a bounding rectangle locates the question; neither is the object's final support.
Keep useful results, their known overreach and unresolved alternatives. A miss can widen or move
the question using the other views and neighbours. Do not require a proof of perfect exclusion,
perfect borders or exhaustive recovery before using a competent prior.

## A failed proxy does not invalidate structural targeting

Rohan's 2026-10-18 correction applies to the whole build. P2a's script measured padded enclosing
rectangles, then an agent asserted that an unbuilt tile-level version would fail and used that
claim to dismiss the required prior. This was an unsupported generalization. The capability
remains open; FULL_BUILD_PLAN §1.1 and P2a give the corrected task.

Keep an actual spatial region separate from the rectangle enclosing it. A broad rectangle can
contain a great deal of irrelevant exterior, and its area does not measure the work an irregular
or tiled domain would visit. A poorly discriminating lens remains a measurement to combine with
other views, geometry and anatomical relations. Diagnose why it failed; resolve the residual with
that structure. Do not respond by abandoning the specified capability, demanding perfection,
fitting a rule per study, or replacing the thesis with a default ML/scoring approach.

A cheap fact can also constrain several later identities and regions even when its first consumer
uses a broad frame. Trace those real consequences before judging usefulness. State which
construction was measured and what it actually establishes; untested alternatives remain
untested. Repetition in plans and commit messages does not strengthen the evidence. Agent
interpretation must retain its authorship and cannot be recast as Rohan's specification.

## A useful representation is not a purified intermediate mask

Rohan's subsequent 2026-10-18 correction makes the priority explicit: the ground layer must be
reasonably competent and faithfully instantiate the computer-vision thesis. Intermediate mask
cleanliness, calibration stability and pixel counts are readings, not optimization targets.
A change in them cannot alone establish improved or reduced anatomical accuracy. Inspect the
native anatomy and the meaning of the operation; correct actual misidentification through its
general definition and complementary context.

Projected support, source uncertainty, native bone evidence, coarse enclosure and marrow-sample
eligibility must keep their distinct meanings at each consumer. If broad location support is
being treated as definitive marrow, repair that conflation. Do not purify the source first as
an assumed prerequisite for using it. "Marrow within bone" supplies a containment relation, not
a universal instruction to erode every section by 2 mm. Any interior/shell measurement needs
its own stated role, independent of whether it restores a preferred calibration or pixel count.

The AX14 seed-variant episode and operational guard are FULL_BUILD_PLAN §1.2 and P2b. Experiments
may compare constructions, but the selection criterion is a justified general measurement and
reasonable native competence. Preserve the lossy descriptions and their disagreements; resolve
the residual jointly. Do not turn a representation task into an intermediate-accuracy campaign.

## The one production operation

1. Read acquisition metadata, finite support, background and the cheap stack measurements once.
2. Use a rough leg field and the obvious anatomical objects to focus the search. Black signal
   inside a tendon or cortex is not background merely because it is dark.
3. Use physical relations and the common map to select each object's native slice and local region.
   The same knee has one map; native acquisition geometry supplies each image's coordinates.
4. Apply the needed complementary measurements inside that region, sharing identical inputs and
   overlapping family contexts. The anatomical question determines what is worth measuring.
5. Retain the actual native support, window offset, source addresses, codes and uncertainty; hand
   the new description to the common map before the next dependent family.

New native descriptions should start with this targeted operation. An existing full-frame reader
is not the default template to copy. If a local enclosure is measured, name its local scope rather
than claiming it equals a full-image enclosure. Restricting a lens to a useful region does not redefine the property it measures. Boundary
conditions can change the local distances, basins or components; that is expected scope behavior,
not a reason to demand whole-frame reproduction or abandon targeting. Retain the actual local
scope and inspect the native anatomical result. No separate replacement lens or exception is
required to authorize bounded execution. Changes specifically presented as equivalent
implementations (compiled twins, pure extractions, cache deduplication) still require unchanged
answers. This equivalence check must never become a whole-frame-only rule.

## Immediate build order

- Finish the source-pinned femoral axial increment: accepted at RELATIVE_POSITION_MAP §8.26.
- Sagittal meniscus descriptions are accepted at RELATIVE_POSITION_MAP §8.27: original local
  enclosure/body measurements in useful full-extent windows around native coronal source points.
  A source point is not an object centre. The paired-source native axial menisci are now accepted
  at §8.28. Keep component identification separate from window completeness: unavailable
  background elsewhere does not withdraw a positive body on available samples. Continue tibial
  axial cartilage and cruciates with actual geometry, local scope and common map handoff.
- Carry this same relational targeting into the remaining cartilage, cruciate, attachment and
  posterior families. Their different tissue relations determine their local measurements.
- Bring earlier full-frame consumers onto shared useful domains incrementally. The leg field is
  currently derived after the interior lens; moving cheap useful spatial guidance earlier remains
  work. Do not claim that cache reuse alone has completed spatial targeting.

Record actual pixels/windows visited and shared contexts, as well as ordinary cache counts.
Profile production without drawing. A reduction in visited pixels is not itself a measured runtime
speedup. Development may use full compute to inspect and diagnose the rule.

## Grounding and consultation

The original thesis, RELATIVE_POSITION_MAP §0/§8.8 and the object's thesis §§1.3, 4, 5.1–5.2,
13.3–13.7 explain the mechanism. Rohan also requested a whole read of
`/Users/rohanvinaik/Projects/rohan-vinaik.github.io/papers/Core Documents/SIGNIFICANCE_WEIGHTING.md`.
The lead's application is structural amplification: a useful fact narrows a cluster of related
unknowns. This does not add that paper's corpus-induction machinery or transfer its numerical
constants into knee recognition.

The complete paper has now been read. Sections4–5 describe cluster-wide marginal coverage;
§13 describes complementary bridges; §16 starts with the cheap step that can settle the most.
In this pipeline, each shared anatomical reading must propagate into dependent identity and
measurement questions before their expensive work runs. Newly derived map information also
changes which later questions are worth asking (§16.4). The acquired image supplies fresh native
evidence; an expectation derived from earlier evidence does not independently confirm itself.
See EFFICIENCY_RETROFIT_PLAN's "Significance weighting" section for the concrete construction check.

The direct Fable consultation, prior independent lead readings, full answer and usage are retained
in `data/readings/collapse-20261017/full-build/targeted-compute-20261018/`.
Fable distinguishes caching from reducing visited space and identifies the late leg-field dependency.
Its proposed exact-crop proof sequence is advisory. Rohan's subsequent explicit correction above
sets the criterion: useful priors, not perfect bounds. The lead's comparison records both agreement
and corrections to Fable's incomplete view of the source.


The concrete retroactive fixes and continuing construction rules are `docs/EFFICIENCY_RETROFIT_PLAN.md` (E01–E24). Update their measured state after acceptance; do not infer completion from this checklist. Rohan explicitly authorized Claude CLI subscription implementation workers on2026-10-18.


Rohan's latest clarification is foundational: structural/classical/symbolic resolution should improve correctness and computational efficiency together across the whole operation. Read EFFICIENCY_RETROFIT_PLAN's "Why efficiency and correctness arise together" and the literal human record. Information from known anatomy must become usable constraints on dependent identities and measurement domains. A small crop saving, cache refactor or fast kernel does not complete this mechanism. Root has reread the object's thesis §§1.3–1.6,2.1–2.3,3.5 for this connection; remaining relevant collapse/mechanics sections are indexed in RESOLVING§8.
