# Chapter 2 — my reading, written before consulting Fable and Codex

2026-10-10. Written before opening either consultant's output, per the consultation protocol.

## What the founder corrected

I said the four cell-tracking lenses "measured focus." Wrong. His words: "none of them were trying
to measure 'focus'. That's not a thing that has a measure. There isn't an objective measure of
'in focus' for every possible interpretation of that word." They measured **simple metrics** —
variance in pixel intensity, black/white balance, intensity/coverage — "for the sake of finding a
local minima state that can resolve a single view of cells that was analytically useful. That is
all. Finding a single slice in each of the four to start the first loop of the pipeline."

They are lenses in the epistemological sense (a lossy measure, inherently correct because it only
measures; interpretation disclaimed), but their measurement "isn't really a point for
interpretation." They are a *selection device*: pick a z-plane worth processing.

I also said the knee's lenses might measure "deviation from normal." Wrong for the same reason:
"what is 'deviation from normal'? What is an objective metric to measure 'deviation' or 'normal'?
There isn't."

## What Chapter 2 actually is (his words)

"The point of the knee project at THIS stage is to find an analysis frame that allows dimensional
collapse. Essentially — what is the format of the data we are presented? What are we shown, and
what about it is categorically something small and resolvable as largely static? Basically, the
point is to establish the information-theoretic ground here. What is the way that we can do a
pure, mathematical operation or search or what have you, to produce a single, resolvable starting
ground that highlights what ACTUALLY matters?"

## The KneeDiff mechanism (his words, paraphrased in order)

1. Knee scans must look really similar for them to mean anything: roughly same size, roughly same
   orientation, the femur/tibia boundary is a giant dark line in the middle, "most of the rest is
   just undifferentiated slop."
2. Basic alignment tools exist. Or use the squint — "intentional lossy representation of data to
   better resolve S/N for significant elements and patterns, like how humans squint to allow
   gestalt priors to better help resolve an ambiguous view." Cell tracking's instance: the 16x16
   tile medians. "Yes, very lossy. But...you see the cells, right?"
3. Take a cheap lossy view, squint at a whole stack of knee studies, line up each specific view
   they provide, shift them around a bit, "then just...subtract."
4. Produce a single "platonic" study set: each view, each image in the study, "as an amalgamation
   of ALL the views lined up then subtracted."

## What he expects, and why the mess is the point

Most of the data subtracts to near-noise: "low variance, largely drift, very obviously not
something useful for diagnosis." The diagnostic places come out "kinda messy and blobby."

That looks like failure. It is not. "There is no noise" applies. What comes out is **two
different profiles of 'blah'**:

| profile | character | what it is |
|---|---|---|
| spiky, small | per-study variance — different people, different scanners, different times | **entropy** |
| stubborn, persistent pockets | "a definable region of clear and obvious uncertainty, places where the studies and images have GENUINE differences in what they show" | **the diagnostic sites** |

"It LITERALLY should produce an amalgamation that explicitly preserves exactly the sites of high
variance as resolvable points of analysis, places that are diagnostically-significant."

## The discriminating criterion — persistence under stacking

His two conditions for variance that is actually diagnostic:

1. "a profile of discrete variance — where does this knee look NOTABLY different from other knees,
   with a clean and obvious profile (e.g. a giant-ass fracture that shows as a big freaking line
   that is an entropic abnormality that is unmistakable)"
2. "variance that SPECIFICALLY shows up in places that have distinct pockets of discrete variance
   that is stubborn and unmistakable"

The contrast he draws:
- Unimportant parts have "a spiky profile of variance — some per-study variance, each image is
  taken by different people, of different people, at different times."
- Diagnostic places "will have stubborn and persistent pockets of differential presentation that
  will NOT simply go away when you stack many of these study images on top of one another. The
  variance isn't in one random study at a few random spots, it's PERSISTENT and consistent and
  shows up repeatedly in the same general ways and in the same general places."

**"The baseline isn't noisiness; it's *entropy*."**

## My reading of the mechanism

The operation is a **population-level variance structure read**, not a per-study comparison. The
key move is that stacking many studies *discriminates* entropy from structure without any fitting:

- Acquisition noise, patient-to-patient anatomic variation, scanner differences → these are
  independent across studies. Stacked, they average toward a smooth drift. Their spatial signature
  is spiky and non-reproducible.
- Diagnostic variation → it is *not* independent across studies, because pathology occurs at
  anatomically constrained sites (the ACL sits in the notch; the menisci sit at the joint line;
  effusion collects in the suprapatellar pouch). Stacked, the variance does not wash out; it
  concentrates in the same places.

So the output of Chapter 2 is **a map of where diagnostic information can live**, computed from
the population's own geometry. Not a diagnosis, not a classification — a resolved starting ground.
Its complement is the knee's "black": positively named as the space that never carries any of the
12 findings.

This parallels stage 0 + stage 1 of cell tracking exactly in role: stage 0 produced an analytically
useful starting picture; stage 1 cleared the black, positively named. Here the squint-align-subtract
produces the starting picture and the low-variance field is the black.

## What I believe is label-free vs label-aware

The variance-structure read appears **label-free**: he says "maybe we can even throw in the others
from the competition that aren't labeled" and "we just want to get an average, a vibe-y
representation of the sites that actually matter or are useful." Nothing in the mechanism needs an
annotation — the discrimination is persistence under stacking.

But his earlier teaching on the platonic knee was label-aware: "The 'normal' knee is the 'normal'
parts of each of the 58 movies, which are all the parts not labeled or impacted by the category of
issue they are labeled as having."

These may be two distinct artifacts (a label-free variance map; a label-aware normal reference), or
one with two passes. **This is a question for him.**

## What this makes of "how each instrument can serve as a lens"

His earlier question. The instruments are the series: each plane (sagittal/coronal/axial) and each
weighting (fluid-sensitive, fat-suppressed) is a different lossy view of the same knee. Each is a
lens in the epistemological sense — it measures, it is inherently correct as a measurement, and it
shows some structures and not others. The alignment and subtraction happen *within* a view type
("line up each specific view that they provide"), because only like views are comparable.
