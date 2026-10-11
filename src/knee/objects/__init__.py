"""THE OBJECTS: every element of the knee significant to its operation, resolved from geometry.

Figure 8's stage, and the heart of the object model (docs/OBJECT_MODEL.md). The founder, 2026-10-11:

    "Our goal here is to resolve every single element that is significant in any way to the operation
    of the knee, and thus carries diagnostic relevance."

    "we should be able to isolate the components of the knee with NO recognition, pure math"

So nothing here consults a stored case. A knee is a fixed anatomy: the femur is just the superior
bone, and identity follows from invariant relations in the patient frame. Recall belongs to the
diagnosis stage, for presentations a predicate cannot settle alone.

Split out of `knee.collapse` on 2026-10-11 at the founder's word -- "I was pretty sure collapse was
starting to be a central dump we should refactor, parse it out into the modular sub-components in a
design/SICP-appropriate way." `knee.collapse` keeps the field it stands on: what a series IS, and the
squint. This package consumes that and never the reverse.

What lives here:

    interiors.py      B1: the dome re-derived for bone. A cell is brightest at its centre because it
                      emits; a bone is a solid bounded by dark cortex, so it is DEEPEST at its
                      centre. The distance transform replaces brightness as the dome's height field,
                      and prominence (never a level) keeps SS6.2's law that nothing is cut on
                      strength, so a thin bone is never silenced by a thick one.
    conversation.py   B2: two series of the SAME orientation read the same knee, so one's bounded
                      dark band is transported into the other's frame and read natively there.
                      Agreement bars; silence may bar conditionally; contradiction never bars.
    profiles.py       the native profile sampler and its accelerated twin, along stated normals
    band_raster.py    rasterising a band into the plane it was measured in
    analysis.py       the per-series orchestration: it moves values and decides nothing (SS13.7)
    border_codes.py   | the pure decisions, each total over its arguments and returning a named
    exchange_codes.py | code -- never a bool where two outcomes need different remedies. Every bar
    profile_codes.py  | they read is an ARGUMENT, never a constant inside them.

What is still owed: the residual pull-out, until every element in docs/OBJECT_MODEL.md's inventory
is resolved or explicitly abstained on. Founder: "the roles that are still unassigned in the visual
field are a lot easier to figure out, since they're definitionally NOT the things you already DO know
how to resolve."

Every stage owes a picture, a compute contract per kernel, and telemetry: docs/STAGE_CONTRACT.md.
"""
