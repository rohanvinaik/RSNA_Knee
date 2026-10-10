"""THE PICTURES: every stage shows what it resolved.

In the thesis the figures ARE the argument. Each section draws what its stage does, and the reader
sees the field actually being decomposed -- the lenses standing at their depths, the black cleared,
the cells taken with their halos, the box emptied round by round. A pipeline that cannot show its
own work has not demonstrated visual reasoning; it has only asserted it.

So every stage of Figure 8's line renders a picture of what it resolved. Put side by side, the
pictures are the story of one study being understood.

HOW THIS LAYER IS BOUND, per SS13.7: "The impure edge is thin: reading a movie, writing the output,
drawing pictures. **A picture is a pure function from the run's values to an image array. The run
asks for no picture and imports no drawing code, so pictures are a layer that can be switched
off.**"

So the dependency runs ONE WAY. `knee.pictures` imports from the stages; no stage imports from
`knee.pictures`. Each renderer takes a stage's finished VALUES and returns an array. Nothing here
decides anything, and deleting this package would not change a single reading the pipeline makes.

**THE COST IS THE TEST.** The founder, 2026-10-10: "if it's genuine computer vision, producing an
image that shows what it does should basically be free; if it's doing visual reasoning, then the
reasoning should be visually obvious."

So a renderer here may do ONE thing: arrange values the stage already computed. It may not measure,
threshold, segment, or recompute. If a picture needs work the stage did not already do, that is not
a gap in this layer -- **it is evidence that the stage is not reasoning visually**, and the fault is
in the stage. Each renderer's docstring therefore names the values it arranges, and any renderer
that computes something is a bug.

One module per stage, named for the stage:

    study.py      the input as it was read: a series at stored fidelity, with its geometry stated
    collapse.py   the leg closed, the squint, the two objects and the seam between them

The rest arrive with their chapters. A stage without a picture is a stage that cannot yet show its
work, and `knee.pipeline.ROUTE` says which those are.
"""
