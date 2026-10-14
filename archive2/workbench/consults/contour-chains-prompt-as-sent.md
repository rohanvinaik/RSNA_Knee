# Consult: what licenses drawing a line between measured points, for bone

READ-ONLY. Answer from this text alone. Do not run any command, do not read any file, do not search
the web. If something here is undetermined, say so plainly rather than filling it in.

## The architecture, so you do not import the wrong prior

This is a **classical-AI, no-machine-learning** computer-vision pipeline for knee MRI. There is no
model, no fitted weight, no learned embedding, and none is wanted — that is the thesis, not a
limitation. Nothing may be tuned to a label, a score or a leaderboard. Every bar is written down
before the run that judges it. A decision returns **named codes**, never a bool. A missing reading is
**silence**, never a negative. If your answer's load-bearing step is "fit", "learn", "train",
"calibrate on the data" or "choose the threshold that separates the classes", it is wrong here; say
what deterministic or measured quantity would do the job instead, or say that none would.

The governing claim: **a finding is a predicate violation on an object, or on a relation between
objects.** Resolve the knee's elements as objects and the twelve diagnoses are read off them by
arithmetic. So the operation below is not "segment the bone" — it is "resolve an element so that a
predicate can be evaluated on it".

## The founder's words, verbatim — the oracle of intent

These are the project lead's own words and they outrank any reading of them, including his.

> "On the 'yellow traces', we need to close the line here. We can find the line correctly but
> imperfectly. We need the cell tracking project implementation, or something like it, to draw a
> smooth, correct, enclosing line, not just a series of dots" (2026-10-11)

> "You can see it--the line is OBVIOUS. A single lens, a metric, can't discover every single point
> perfectly. but we have ENOUGH points that drawing a line seems like a rather simple
> pattern-completion line drawing task from the information we have, not wild discovery nor making
> shit up either"

> "one thing you should look into from the cell-tracking project … (1) the 'coastline paradox'
> smoothing--because while we measure/identify a spiky cell body looking literally at the data, we
> understand that our lenses are lossy vs the image and the image itself is lossy vs reality, and we
> know that cells have a generally smooth, not infinitely spiky shape because of basic physics of
> cell membranes. So, the coastline paradox solution comes into play--the point is to mimimize
> length/surface area of the drawn line while keeping the volume within as close to the pre-smoothed
> version as possible, with a preference to pull towards a center mass of the 'object' … Same here.
> All of the components of the knee anatomy are bounded by physics and biology. Bones don't just
> randomly grow in arbitrary dimensions. That's cancer, or maybe FOP. They grow out from the marrow
> and push outward radially, so the outer surface is generally determined by a strong propensity for
> a smooth external boundary, stright lines where straight and a low-variance curve path where
> curved, exponential decay of propensity for violations. Not random. I'm not saying that every bone
> has a perfect angle of measurement to the degree and minute, but it's *intentional*. Then (2) …
> the 'central pull'."

> "we should never set arbitrary 'closure' as being correct. The point is to derive objects as
> resolvable elementss produced through computer vision, with the \<object> thesis as a general
> solution to computer vision as a problem type"

> "\"Fat-bright\" and \"fat supressed\" … the same view, with slightly different 'lenses' put on it,
> enables clean discrimination between elements. The 'three-legged stool'--where two lenses are both
> representations of the same truth and are both correct, agreement is strongly confirmatory and
> addative, but *disagreement* is actually an *incredibly* powerful source of information! … So the
> different parse of the same coronal site isn't a problem, it's a *gift*!"

## The sibling build's mechanism, as it actually is

A prior project (cell tracking) instantiates the same thesis on fluorescence microscopy. Its outline
machinery, traced in its source:

- `borders_of`: every boundary place of a binary mask, from marching squares at level 0.5 on the mask
  padded by one empty place, so **each loop closes by construction**. Loops under four points are
  dropped.
- `border_band(flicker, slope, floor, ceiling)`: how far a traced border point may move — the
  **flicker of the light there over how steeply the light falls across the border**, clamped to
  [half a place, half a speck]. **A flicker or slope not read, or a slope that does not fall (≤ 0),
  leaves the point free as far as the ceiling.**
- `pulled_taut`: until no point moves, each point goes halfway onto the chord between its two
  neighbours; halfway toward an **oval round two centres** set by the loop's own area and second
  moments; the whole loop eased along its normal to hold the area it was traced with; then every
  point clamped back inside its band **of where it was traced**.
- Pinned by test: a sub-band wiggle comes off; a lobe longer than the band stays; **a hole narrower
  than its band closes**, a wider ring hole stays; two lobes keep their neck and leave the waist open.
- Stated in the thesis: *"Of all loops enclosing one area, the circle's is the shortest, so shortening
  the trace at a fixed area rounds the shape as far as the data allow. The knowledge that a nucleus is
  roundish is thus applied as a pull, never imposed."* And: *"No border is known more finely than the
  flicker, so none is moved farther than its flicker."* And: *"What a body drew outside its outline is
  kept as a finding, never discarded."*
- **No bridging of non-touching gaps exists anywhere in that code.** Fragments are stitched only when
  they already touch.

## Two figures of the thesis, read directly

- **Figure 21, panels C and D.** One body outline holding **two centres**, every place inside carrying
  an arrow — *a place's dome link, toward its own centre*. Panel C was called **two cells** by the
  human expert; panel D, structurally identical, was called **one cell**. Two centres are evidence,
  never a decision.
- **Figure 25, panel D, "The Dome Link and the Ring".** The same field written into the object's
  profile: each place's direction to its main centre (eight compass directions) and which of four
  **rings** it sits in by distance. Dense and coherent near the centre; at the outermost ring many
  places write **nothing at all**.

## What the knee build has measured, in production, today

Bones are resolved as **territories**: a watershed on the negative Euclidean distance transform of
the imaged interior, seeded by prominence markers (a bone is *deepest* at its centre, where a nucleus
is *brightest*, so the distance transform replaces brightness as the dome's height field; prominence,
never a level, so a thin bone is never silenced by a thick one).

A boundary census then types every place of every territory's loop:

- **supported** — the arc sits on a **measured dark reading** (a cortical surface found by a profile
  cast across the border);
- **constructed** — the arc is a **divide against a peer territory**, i.e. a decision of the
  watershed, not a reading;
- and per touching pair, the **relief**: the weaker centre's height above the pass between them, with
  an **unread pair absent, never zero**.

Measured on real studies: a coronal fat-suppressed series gives **six territories, each 0.88–0.94 of
its loop supported**. A sagittal series of the same knee gives **nineteen territories, 0.24–0.98**.
The supported arcs are visibly a **broken necklace of points** along the cortex, with scattered
speckle outside the leg. That is the founder's "series of dots".

## What an earlier reader already established, which you should not re-derive

- On a constructed divide in continuous tissue there is **no falling slope along the normal**, so
  `band = ceiling` — *maximally free*. The chord and oval steps act there **unopposed**. At a
  well-measured cortical edge the band is small and the prior is nearly inert. So the sibling's rule
  grants the most freedom exactly where nothing was measured.
- A medial-axis / ridge prior for bone is **circular**: a bone's own axis exists only once the bone is
  isolated, which is after the outline. The axis is also differentially unstable — its spurs are
  generated by the very staircase noise the pull exists to remove.
- "Radial growth from marrow" fails as geometry for the **patella** (a sesamoid, nearly axis-less),
  at the **condyles** (a branch point: a smooth-offset prior fills the intercondylar notch exactly as
  a coastline pull fills a bay), and for an **osteophyte** (whose radius spike *is* the finding).
- The founder's "exponential decay of propensity for violations" is **already structurally present**
  in the chord step: moving each point halfway onto the chord multiplies a boundary perturbation of
  wavenumber κ by cos²(κ/2) per iteration, so high-curvature violations decay geometrically and
  low-curvature ones barely move. What is not measured is the rate (the ½).
- A displaced fracture is a step in the surface: high slope, therefore the **tightest** band in the
  loop, therefore the hardest to move. It survives because it is well measured, not by topology. But
  **a notch narrower than the local band is erased by the pull, provably.**
- The band presently has **no physical width**, because the variance-stabilising transform is not yet
  composed with the sampler; `flicker/slope` is raw intensity over raw slope.

## The questions

1. **Freezing the constructed arcs.** The lead's inference is that a constructed arc should take a
   band of **zero** — frozen, moved only by a later stage that has a reading — inverting the sibling's
   "unread slope → maximally free" for this one case. Is that inversion right? What case does it hide
   where a divide genuinely should move? Is there a third option that is better than both?

2. **The completion bar.** A span between two supported arcs may be completed when it is shorter than
   the scale at which the instrument could have missed a boundary that was there — derived from
   in-plane voxel size, through-plane slab thickness, and the measured spacing of supported places on
   the flanking arcs. Is that the right *shape* of bar? Is it already just the sibling's "a hole
   narrower than its band closes", making completion a consequence of the existing operation rather
   than a new one? What breaks it? Be concrete about what would have to be measured.

3. **The admissible shape prior.** Given that the ridge is circular and "roundish" is a nucleus's
   physics, is the honest knee port the **chord step alone** — with the oval dropped, and the
   area-hold kept or dropped — under a per-point band? If not that, what deterministic form expresses
   "straight where straight, low-variance curve where curved" without fitting anything or imposing a
   global shape model?

4. **The notch.** The intercondylar notch is not noise: it is where the ACL sits and it is how the
   knee's compartments enumerate. The stated protection is "slope shrinks the band, a small band is
   immovable". Does that protection survive where the notch's mouth is bounded by a **constructed**
   arc rather than a measured edge? If not, what does protect it, without special-casing the anatomy?

5. **Ordering.** Does the missing variance-stabilising composition block this work? Can a contract
   honestly promise "movement bounded by a **measured** allowance" while the band is in raw units, or
   is composing the transform a prerequisite? Answer for the contract, not for the implementation.

6. **What must be forbidden.** Name the failure modes in which this operation stops resolving anatomy
   and starts inventing it, and say what the contract must say to make each one impossible rather than
   merely discouraged.

Answer each question in order. Mark anything you cannot determine from this text as undetermined.
Separate what follows from the stated mechanism from what is your own inference, and label the latter
as yours. Do not propose a redesign of the project; report provable errors with their proof, or ask a
question.
