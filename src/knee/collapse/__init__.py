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
This note came back with the code from the second build. The chapter record it named,
`docs/chapters/02-collapse/`, is not in this project. What governs now is `AGENTS.md`, whose
method finds each object's main slice with the squint. Rohan, 2026-10-14: «Is it not obvious which
slice to use? The one that is able to show the anatomical region needed for identification of each
anatomical object, and then for diagnosis.»
----------------------------------------------------------------------------------------------

The modules here, and what each is (SS13.7 keeps the kinds apart):

    noise.py         MEASUREMENTS. The background split per series: the valley after the
                     background's mode in the series' own histogram, the level the lens reads low
                     signal under.
    physical.py      MEASUREMENTS. A slice's plane frame in the scanner's millimetres (its places,
                     the inverse that carries a place onto it, its normal), and one slice's squint.
    squint_stack.py  ORCHESTRATION. The squint over every slice of a series, each tile's centre in
                     the scanner's millimetres: the cheap look at the whole series that points
                     where the expensive work runs.
"""
