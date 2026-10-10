# Chapter 2 — symbolic trace of cell_tracking's collapse

Traced via Serena on `cell_tracking/src/cell_tracking/`, 2026-10-10.

## The four lenses — `squint/focus.py`

Four functions, each measuring one thing about one slice:
- `gradient(plane)` (line 46): mean squared brightness gradient (Sobel, down and across)
- `contrast(plane)` (line 64): variance of brightness over its mean
- `split_quality(plane)` (line 82): how cleanly brightness falls into two groups (Otsu)
- `dark_share(plane)` (line 122): share of places at or below camera dark

`FocusRead` (line 154): dataclass holding `z, gradient, contrast, split_quality, dark_share`.
Docstring: "What one plane of the stack looks like. No word: the readings only."

`sharpest_of(scores)` (line 136): which slice reads highest; ties go to the earlier slice.

## The compiled cassette versions — `cassette/focus.py`

`SliceFocus` (line 49): same four fields. `focus_of(stack, dark)` (line 306): reads every slice
of one time point's stack four ways, shallowest first. Called by `cassette/resolve.py` (scores_of,
line 206) and `cassette/box.py` (_box_at, line 309).

## The composite — `squint/composite.py`

- `flat_composite(volume, spots_zyx, slices)` (line 293): each place shows the volume at the
  sharpest slice of its in-plane nearest spot. Territories from nearest-spot partition.
- `frame_composite(volume, frame, slab)` (line 332): step 0 for one frame. Spots read at their
  own depth, then flat_composite. The founder (2026-09-22): "We generate two types of composite in
  stage 0, and the disagreement between them is information about what the boundaries can find."
- `plane_composite(plane, z, light, open_places)` (line 364): any flat picture as its own stage 0.
  The founder (2026-09-23): "each view gets the partition its own light implies. Five different
  partitions, and the disagreement between them is more information."
- `residual_composite(made, open_places, light)` (line 261): the residual's own stage 0.
  Wayfinder thesis: facts pulled out never come back, so territories are redrawn at the residual's
  own density.
- `composite_refusal(...)` (line 64): why no composite can be made, or "ok".

## The pipeline — `squint/run.py`

`composite_through(made, dark, flicker, pass_number, places)` (line 165): steps 1 and 2 on ANY
stage 0. "The stage 0 is a PARAMETER" — the founder (2026-09-23) runs the pass over every kind:
the four in-focus planes, the brightness, and the composite itself. Taking it as a parameter is
what stops a caller reimplementing steps 1 and 2 beside the pipeline.

## Key architectural facts from the code

- The four measures are the cell instance (they measure focus because focus decomposes the
  microscope's depth). The ROLE is "a single lossy reading per slice."
- `sharpest_of` is the collapse in one line: pick the depth where a lens reads highest.
- The composite does not decide. It points (`§4.3: "it never pulls a cell and never decides
  alone: it points"`).
- Five partitions (four lens planes + composite), each with territories its own light implies.
  Disagreement between them is information.
- The residual's composite is a restatement, not a second look — the image stays, only the
  partition is new.
