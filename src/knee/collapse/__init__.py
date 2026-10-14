"""THE COLLAPSE (the squint), Figure 8 (§2.8).

From the figure, verbatim:

    In depth:  Four lenses (Gradient, Contrast, Split Quality, Dark Share), each standing
               at its own sharpest depth, read the volume as flat stills; the composite,
               a fifth flat picture, keeps each place's depth as a number
    In time:   Three anchor time points (t/3, t/2, 2t/3), dividing the movie into a third,
               a sixth, a sixth and a third, are resolved in full; every other time point
               is followed

THE KNEE'S VERSION, given by the founder 2026-10-10: **the knee is two objects that combine.**

Cell tracking collapsed depth and time. The knee collapses neither. Its field splits into two
<object>s -- the femur and the tibia -- sitting into one another with the joint space between, and
an injury is a reasoned deviation in how they sit. So this chapter resolves the femur, resolves the
tibia, resolves the space, structurally and deterministically; diagnosis is then reasoning over the
relation. Every one of the twelve findings is a deviation in it: a break in an object, a signal
change within one, the space lost or flooded or inflamed, the spacers and restraints that hold the
relation, or fluid escaping behind.

What makes the two objects two is the gap between them, and the mechanism is the sibling's own:
a valley is where one <object> ends and the next begins, and a waist deeper than one flicker keeps
its two centres (§6, §6.1). Markers come from anatomy rather than from maxima, the superior-
inferior axis is read from the header rather than the pixels, and a basin is evidence and never
identity.

----------------------------------------------------------------------------------------------
THE CHAPTER'S RECORD IS `docs/chapters/02-collapse/`. Read `README.md` there FIRST in a new
session or after a compaction: what is built, what is not working and the traced reason, what is
open and the founder's to rule, and a claim withdrawn. Then `teachings.md` for his words verbatim,
then `design.md`.
----------------------------------------------------------------------------------------------

The modules here, and what each is (SS13.7 keeps the three kinds apart):

    codes.py    DECISIONS. Pure, total over their arguments, returning named codes. Every bar a
                decision reads is an argument, never a constant inside it.
    noise.py    MEASUREMENTS. The noise law per series: the background population, the channel
                count, and two independent estimators of sigma that must concur.
    units.py    MEASUREMENTS. The variance-stabilizing transform, so one unit is one sigma at any
                intensity -- which is what makes a seam's depth meaningful.
    regime.py   ORCHESTRATION. The regime key: the cheap whole-field readings taken once per
                series, which say what a series IS before any expensive work runs.

Naming, so the next chapter does not inherit a collision: the parts of this chapter are NAMED, not
numbered -- the noise law, the transform, the regime key, the objects and the seam. "Stage 0-4" is
the thesis's numbering for the LOOP's stages (SS5) and belongs to chapter 3, not here.
"""
