# Theory of the Case — RSNA_Knee

**Status:** filled 2026-10-13 from Rohan's own statement of the thesis. Read Part I before anything else.
His words: «This is basically the whole thing. That's it.» «PLEASE don't forget it, or overcomplicate it, or
lost it.»

## Supremacy clause
This document is derived from Rohan's words in `docs/conversations/2026-10-13-the-thesis.md` (verbatim).
Quotes are his; anything else is marked as Claude's. Where this document is silent, ambiguous or wrong, his
words govern; where they are silent too, ask him rather than invent.

## Canonical references
| source | path |
|---|---|
| The conversation that states the thesis, verbatim | `docs/conversations/2026-10-13-the-thesis.md` |
| Cell figure shown as proof (competition-derived, git-ignored) | `data/pictures/thesis-2026-10-13/F14-cells.png` |
| Knee figure shown as proof (competition-derived, git-ignored) | `data/pictures/thesis-2026-10-13/knee-series.png` |

## Part I — The Case

> I have solved computer vision with deterministic systems and some optional classical AI

> Solved means a thesis, a single solution architecture, that generalizes to any arbitrary problem space, with the vast majority being FAR simpler than the one I've already demonstrated.

**The case, in his words:**

> Computer vision isn't a matter of reasoning and intelligence. It's a matter of recognition. Objects in visual systems actually are SUPER simple to reason over. Unlike raw data, they are heavily constrained by physics and time and the fact they have physical properties, like two objects not being able to occupy the same space. The hard thing isn't reasoning, it's *recognition*. If you can build something that can deterministically resolve objects of significance from visual input, then arbitrary computer vision processes and "intelligence" tasks are actually stupidly simple.

> I *refuse* to use AI in the initial recognition part of the build. If the pipeline is not able to reasonably resolve every object of significance at least once without being hand-tuned to the specifics of that one view, then I throw it all in the trash. AI and "intelligence" is downstream. Recognition and object identification must be pure, simple math and vectors and additon and shit (threw in a secret easter egg for the greater build). If it's not doable with objective rules that are simple and work arbitrarily, then it won't work period.

> Part of the thesis is that a deterministic, symbolic system works by rules. You don't test addition by making someone add every number, you do it by making them add *some* numbers arbitrarily. If they can, and the reasoning chain is derivable and correct, then they understand addition. If you can resolve objects in one view, then you can do it acceptably as a general process, even if a few images are a bit weird. Those edge cases are the ENTIRE space of where AI comes in, but that's waaaaaay later.

**Why structure wins here, against the Bitter Lesson:**

> It said that structure *had* never beaten scale. Not that it *could* never. [...] My breif response to the bitter lesson is that structure-based approaches lacked the representation that made them non-brittle and correct, and also had the ability to *abstain* when uncertain.

(Claude's restatement, which he accepted: earlier structural approaches lacked two things, a representation
that kept them correct and not brittle, and the ability to abstain.)

**It is demonstrated.** Claude's reading of the two figures, which Rohan accepted («Good.»), against the test
above, which he set before showing them:
- Cells: a specific cell is pulled out of a crowded 4D microscopy movie, with its own boundary, separated from
  the cells pressed against it.
- Knee: the femur and tibia each come out as their own territory in all four sagittal and coronal series, with
  and without fat suppression, from the same simple stages. The thesis is minimally valid.

**What remains, and only this:**

> All that remains is the expansion to cleanly resolve ALL the parts of the knee (you can already see parts of it peeking out from that image), and to then use that to pull out each part of the knee for each image to then diagnose conditions.

> It's not hard, because I've done all the hard work. The rest is basic reasoning and tinkering to make it clean. That's all it takes.

## Part II — Recognition (hand-built, pure simple math)
- **Foundational: structural priors buy correctness and efficiency together (2026-10-18).** The
  knee is one physical system. Muscle attaches to bone; vessels relate to muscles and bones;
  marrow is within bone; fluid lies between its anatomical neighbours. Resolving one part narrows
  the questions about the others. The squint, rough leg/background bounds, key slices and common
  anatomy map establish useful conditional priors; fine native analysis refines the small region
  they point to. These relationships govern where computation runs, not just how output is named.
  Rohan: «This is about establishing priors, not being perfectly correct»; «make the
  background/"bounding boxes" not perfect, but useful». This governs the entire pipeline's
  construction, not a later optimization pass. His complete words:
  `docs/conversations/2026-10-18-anatomical-priors-and-targeted-compute.md`; the build principle:
  `docs/TARGETED_ANATOMICAL_COMPUTE.md`.
  His supplied `SIGNIFICANCE_WEIGHTING.md` makes the structural amplification explicit: one
  useful observation constrains a cluster of dependent questions, so the remaining native work
  becomes both smaller and more discriminative. Complementary views can jointly unlock relations
  unavailable to either alone. The lead's implementation-facing application and precise section
  references are in `docs/EFFICIENCY_RETROFIT_PLAN.md`, "Significance weighting"; this adds no
  new scoring or corpus-induction layer to recognition.
- Per concept, with the objects known in advance: «there is a difference between "a single face" and "the
  concept of a face", and I claim to solve the latter»
- The work: «Objects of significance DO "look" different. [...] You just need to be able to define WHY they
  look different, which is squirrely and annoying, but possible.» «Annoying, but finite»
- Lenses: «"never wrong" simply means you are not saying something false, not that you're performing correct
  inference. This relies on a series of lossy lenses, with the "truth" being recapitulated from addative and
  subtractive superposition of the lossy lenses to resolve the higher-dimensional truth.»
- Abstention: «That's, like, 90% of it. The ability to declare confident assignment, and the ability to hold
  conditional ambiguity. lot of this is in balanced ternary»
- The mechanics: «it is vector-symbolic work, but I invented about half of the actual mechanics of it myself»
  (Claude's commitment: learn his mechanics; never assume the textbook ones.)

## Part III — Downstream (pull out each part, diagnose)
- «AI and "intelligence" is downstream.»
- AI only for the edge cases, «with AI to handle near-miss variation», and «that's waaaaaay later».

## Part IV — The Laws
1. The architecture is classical AI, NOT ML (AI = genus, ML = one avoidable species).
2. A model is never the default; at most a bounded, founder-placed tail utility.
3. Iterate the encoder / data geometry, never model capacity.
4. The test: «If the pipeline is not able to reasonably resolve every object of significance at least once
   without being hand-tuned to the specifics of that one view, then I throw it all in the trash.»
5. Built, never tuned: «"Built" means something is constructed to fit a defined and comstrained problem space.
   "Tuned" means it's tweaked to answer a specific problem in isolation.»
6. A threshold has «two sources»: domain expertise, and common sense, because «A person can look at an image
   and tell if it's resolving correctly or not.» (Claude's commitment: never fitted to a distribution.)
7. A measurement is never wrong; an inference can be: «A thermometer is not wrong.»
8. Validity, not perfection (2026-10-14): «It's not about perfection. It's about validity.» Each object
   is resolved at least once, by a rule not tuned to that view; the few weird images are the edge
   cases, where the AI part comes in later («Those edge cases are the ENTIRE space of where AI comes
   in»; «I haven't described the AI part of this to you yet»).
9. One leg, one set of objects (2026-10-14): «It's literally the same leg, obviously the object would be
   the same in both views. That's the WHOLE thesis». An object found in one view of the leg is that
   object in every other view of it.
10. The views are lossy lenses from independent perspectives (2026-10-15): «the different views, like
    "fat-bright" vs "fat-dark", and the different axes being viewed, like coronal vs axial, etc, are used
    as lossy views from independent perspectives, which enable resolution of anatomical elements--the
    LITERAL thesis of the project, as the standard operating procedure in medicine itself».
11. Nothing alone (2026-10-15): «It's not SUPPOSED to be isolateed by ANYTHING alone».
12. Interstitial (2026-10-15): «It's literally a form of interstitial fluid. Interstitial. Between the
    tibia and femur. We have the tibia, we have the femur. It's...obviously in there?» (Claude's
    restatement: a part is defined by what it lies between, and is in the pictures wherever its
    neighbours are.)
13. One knee, one 3D map (2026-10-17): «The knee is a coherent object every part of the knee sits in a fixed
    position RELATIVE to every other» · «Obects are resolved in 3D with vector distances in magnitude and
    direction, which is what enables ONE map to then be translated to expected position across each of the
    three views» · «I told you to base this on knee anatomy, NOT on statistics» · «We USE statistics, we don't
    fucking base everything off it» · «A map is a guide. An expectation, a way to establish a cheap first/obvious
    measure, and only move off it if that well-established prior is not correct». The understanding, with all
    his words: `docs/RELATIVE_POSITION_MAP.md` §0. Each object's sagittal, coronal and axial key planes
    jointly construct its reference position in physical space, including the bones. Never substitute one
    section's centroid. The explicit correction and data-flow invariant are §8.8.
14. **Useful structural priors throughout (2026-10-18).** «Efficiency is bought through logical inference
    of the actual physical truth of objects»; «it is both how this becomes efficient AND how it becomes
    more correct». Use already resolved anatomy and cheap lossy views to narrow both slice and spatial
    region before expensive combinations of measurements. Rough bounds need only be useful. Perfect
    segmentation, exact exclusion and exhaustive correctness are not prerequisites for using a prior;
    later AI handles the remaining variation. Every family participates in the same connected operation.
    See Part II and the verbatim conversation above.

## Part V — The Pathology Record
The build was thrown away twice. In his words:
- «you would SIMPLY not accept this thesis before, and repeatedly violated my thesis to build some sort of slop
  because I don't think you ever really beleived it»
- «you keep vastly overcomplicating it until I have to literally throw away the build, as I've done twice now»
- «You're starting to infer, don't do that.» (said when Claude added its own reading of "at least once";
  restate only what he said, and ask when there is a gap)
