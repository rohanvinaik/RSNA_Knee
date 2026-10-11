# The lead's own reading: supported contour chains (OpenSpec task 3.8)

Written **before** opening either second reader's answer for this round, as the working loop requires
(`docs/SPINE.md`, step 3). It builds on one answer already on file — the earlier central-pull round,
`docs/chapters/02-collapse/readings/central-pull-fable.md` — which is cited where it bears, because
re-asking a settled question wastes the reader and the founder's time.

## What the founder settled, verbatim

> "On the 'yellow traces', we need to close the line here. We can find the line correctly but
> imperfectly. We need the cell tracking project implementation, or something like it, to draw a
> smooth, correct, enclosing line, not just a series of dots" (2026-10-11 18:16)

> "You can see it--the line is OBVIOUS. A single lens, a metric, can't discover every single point
> perfectly. but we have ENOUGH points that drawing a line seems like a rather simple
> pattern-completion line drawing task from the information we have, not wild discovery nor making
> shit up either" (18:26)

> "the point is to mimimize length/surface area of the drawn line while keeping the volume within as
> close to the pre-smoothed version as possible, with a preference to pull towards a center mass of
> the 'object' … All of the components of the knee anatomy are bounded by physics and biology. Bones
> don't just randomly grow in arbitrary dimensions. That's cancer, or maybe FOP. They grow out from
> the marrow and push outward radially, so the outer surface is generally determined by a strong
> propensity for a smooth external boundary, stright lines where straight and a low-variance curve
> path where curved, exponential decay of propensity for violations. Not random." (18:45)

> "we should never set arbitrary 'closure' as being correct. The point is to derive objects as
> resolvable elementss produced through computer vision, with the \<object> thesis as a general
> solution to computer vision as a problem type" (20:25)

**The three regimes, which is the whole contract.** Completing a line is licensed where there are
*enough measured points* that completion is pattern completion; it is refused where it would be
"wild discovery"; and the operation reports which of the two each span was. Appearance is never
support. Closure is an outcome, never the bar.

## What the figures establish (read directly, 2026-10-11)

- **Figure 21 (S5), panels C and D.** One body outline holding **two** centres, every place inside
  carrying an arrow — *a place's dome link, toward its own center*. C was called **two cells** by the
  expert and D **one cell**, on structurally identical pictures. Two centres are evidence, never a
  decision.
- **Figure 25 (H2a), panel D, "The Dome Link and the Ring."** The same field, written: each place's
  direction to its main centre, plus which of four **rings** it sits in by distance. Dense near the
  centre; at Ring 3 many places write **nothing at all**.

So the central pull is a **reading**, not a force. This agrees with the earlier round, which put it
sharply: *"the watershed is the central assignment, not a central pull … Calling the watershed 'the
central pull' conflates partition with outline."*

## What is already measured in production

The boundary census (`src/knee/objects/boundaries.py`, wired, rendered, run on the corpus) answers
the first two measurements the earlier round asked for:

1. **Per territory, the share of its loop on a measured dark reading**, the rest being constructed
   divide — `data/pictures/object-toolkit/boundaries/series.png`, middle panel. Coronal
   fat-suppressed: six territories at ~0.88–0.94. Sagittal: nineteen territories at 0.24–0.98.
2. **The relief of every touching pair**: the weaker centre's height above the pass between them,
   with an unread pair **absent, never zero** — the same figure, right panel.

## The contract as I would write it, labelled as mine

1. **An arc carries its own warrant, and there are three.** *Supported*: the arc sits on a measured
   dark reading. *Constructed*: it is a divide against a peer, which is a decision, not a reading.
   *Absent*: neither — a gap. These never merge into one word "boundary".

2. **The pull's licence is the inverse of its freedom, and that is the danger.** `band =
   flicker/slope` gives a **tight** band where the edge is well measured (the pull is nearly inert,
   correctly) and the **ceiling** where no slope falls — which is exactly the constructed divide. So
   the sibling's rule hands maximal freedom precisely where nothing was measured. My inference: for
   the knee a constructed arc should take a band of **zero** — frozen, redrawn only by a later stage
   that has a reading — rather than the ceiling. This inverts the sibling's rule for this one case and
   I want it attacked.

3. **Completion is bounded by the instrument, never by appearance.** A span between two supported
   arcs may be completed when it is shorter than the scale at which the instrument could have missed
   a boundary that was there — a function of in-plane voxel size, slab thickness, and the measured
   spacing of supported places on the flanking arcs. Written down before the run that judges it
   (`AGENTS.md`, law 4). My inference: this may already be the sibling's *"a hole narrower than its
   band closes"*, in which case completion is a consequence of the existing operation and not a new
   one.

4. **The shape prior is a smoothness propensity, not a model of the shape.** The earlier round
   showed the ridge prior is circular (a bone's own axis exists only after the bone is isolated,
   which is after the outline) and that "radial from marrow" fails for the patella (a sesamoid, nearly
   axis-less), at the condyles (a branch point, where a smooth-offset prior fills the intercondylar
   notch exactly as a coastline pull fills a bay) and for an osteophyte (whose radius spike *is* the
   finding). It also showed the founder's exponential decay is **already structurally present** in the
   chord step, which multiplies a perturbation of wavenumber κ by cos²(κ/2) per iteration. My
   inference: the knee's port is the **chord step alone**, under a per-point band, with the oval
   dropped — because the oval encodes "roundish", which is a nucleus's physics and not a bone's.

5. **Closure is reported per chain** — closed, open with its gaps named, or clipped by the picture's
   edge — and an open chain is a correct result.

6. **What refinement sheds is kept**: the original trace, the refined trace, the places the pull shed,
   the spans it refused to complete, and competing subdivisions. The B2 picture's concurrent (9→11,
   6→7, 12→15) and conditional (9→20, 18→48, 12→47) subdivisions are a disagreement to keep, not a
   knob to tune — figure 21 C versus D is the warrant.

## What I am least sure of, and what I want the readers on

- **Q1.** Freezing a constructed arc (band zero) inverts the sibling's "unread slope → maximally
  free". Is the inversion right, or does it hide a case where the divide genuinely should move?
- **Q2.** Is the completion bar above the right *shape*, and is it already the sibling's hole-closing
  behaviour rather than a new operation? What breaks it?
- **Q3.** Is the chord step alone, with the oval dropped and the area-hold kept or dropped, the honest
  knee port of "smooth external boundary, straight where straight, low-variance curve where curved"?
- **Q4.** The intercondylar notch is not an artefact to be smoothed away — it is where the ACL lives
  and it is how the compartments enumerate. The earlier round's protection is "slope shrinks the band,
  a small band is immovable". Does that protection hold where the notch is bounded by a *constructed*
  arc rather than a measured edge?
- **Q5.** The earlier round states the band has no physical width until the Rician VST is composed
  with the sampler. If that is still true, can this contract honestly say "movement bounded by a
  **measured** allowance"? Is the composition a prerequisite of 3.9, or may the contract state the
  band in sigmas and let the implementation follow?
- **Q6.** What must this contract forbid outright — the failure modes in which this operation would be
  inventing anatomy rather than resolving it?
