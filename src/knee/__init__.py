"""The knee, laid out on Figure 8 of *What an <Object> Is* (§2.8, "Road Map").

Figure 8 is "the whole system, from a movie to its output", in
``cell_tracking/docs/pipeline_thesis/paper/what_an_object_is.md``. Each subpackage holds one stage
of it and carries that stage's text from the figure.

**The names are the figure's ROLES, not the cell instance's content.** The sibling's `<object>` is
a nucleus; the knee's is a BONE (the founder, 2026-10-10: "Knees are two objects that combine...
the tibia and the femur"). A name that says "cell" names the instance, not the role, and the
project's own law forbids it: the thesis's terms are roles in a decomposition, never the cell
instance's content.

The route a study takes, in the figure's order:

    study            A MOVIE (the input). For the knee: a study's files become data points
    collapse         THE COLLAPSE (the squint). For the knee: two objects and the seam between
    loop             THE LOOP, round by round, on what is left
    candidates       THE EMPTIED BOX; THE CANDIDATES
    vectors          THE VECTORS (§7): every place in one language
    cleanup          THE CLEAN-UP, on the residual
    assignment       recall routes each <object>            (was cell_assignment)
    every_object     the completeness check                 (was every_cell)
    output           THE OUTPUT. For the knee: twelve confidences per study

Beside the line, consulted by any stage:

    memory           THE MEMORY AND ITS BUCKETS (§8, §9)
    expert           THE EXPERT: calls become cases
    agencies         the four agencies (§11), each marked in the stage where it acts
    record           the kept record of findings, where the agencies meet

NOT INSTANTIATED HERE, pending the founder's ruling. Three of Figure 8's rows rest on a time axis
or on cell biology, and a knee study has neither. Each package is kept with its figure text and
its reason, and NOTHING is struck: ripping a row out is a change to the founder's design (law 9)
and is his to make.

    anchor           THE ANCHOR RESOLVED. An anchor is a TIME POINT resolved in full. A knee study
                     is a still; Chapter 1 measured no temporal series. The ROLE -- a unit resolved
                     in full against which the rest is carried -- may yet map to something here
    following        FOLLOWING THROUGH TIME (§12). Same: there is no time to follow. The ROLE --
                     carrying a resolved reading cheaply to where it was not resolved in full --
                     may map to carrying across the slices of one stack
    division         DIVISION. Bones do not divide. No role is apparent

`docs/PIPELINE.md` carries the whole route and how each module is built.
"""
