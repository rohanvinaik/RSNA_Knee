# Task 4.4: the cell build's own slice rule, traced (the lead, 2026-10-13)

The funnel's unit 4 (`knee.collapse.depth`) stands each cheap lens at the slice where its reading
peaks. Task 4.4 asks for the literal rule by which the cell build's lenses pick their slice, its
tie and abstention handling, recorded here, and any difference from unit 4 put to the founder
before the unit is admitted. The miner of 2026-10-13 (`scratchpad/mine-cell-depth.md`) read four
modules and found no slice rule in them; the modules it named as unread, and the `squint` package
it did not know of (built 2026-09-22 to 26, after `docs/CODE_MAP.md` of 2026-09-21), were read
whole by the lead on 2026-10-13: `squint/__init__.py`, `squint/focus.py`, `squint/composite.py`,
`record/depth.py`, `record/route.py`, `instruments/acquisition.py`, `members/context.py`. Not
read: `squint/column.py`, `squint/movie.py`, `squint/frames.py`, `squint/descent.py`,
`record/frame.py` beyond the miner's facts.

## The facts, with their locations

**Three rules at three scales.** The cell build chooses a slice three ways, and keeps them apart.

1. **Per plane, four cheap readings, one measure at a time** (`src/cell_tracking/squint/focus.py`,
   2026-09-23). `focus_on(volume, dark_level)` reads every plane of one time point four ways,
   shallowest first: `gradient` (the mean squared Sobel gradient, "Tenengrad": "Blur removes sharp
   steps, so this falls away as a plane goes out of focus"), `contrast` (variance over mean: "the
   SHAPE of the brightness, not how much there is"), `split_quality` (Otsu's between-class share
   over a 256-bin histogram of the plane's own range: "1.0 is two perfectly separated humps; toward
   0 is one undivided hump") and `dark_share` (the share of the plane at or under the frame's own
   dark: "The founder's own reading, taken literally"). The module's rule on choosing: "Every
   reading is graded, no level is chosen here, and the three are never combined: which to trust,
   and what their disagreement means, is the founder's." `in_focus_plane(reads, measure)` gives
   the z of the sharpest plane by ONE named measure: "One measure at a time, on purpose: the three
   are orthogonal readings and blending them into a single score would throw away exactly the
   disagreement the pipeline is built to read." The founder's words it rests on (2026-09-23): "The
   'brightest' frame is a messy one, the 'cleanest' view isn't the 'brightest' one" and "If we have
   a clear picture, AND we have a picture that SHOUTS the signal, I think that gives us two neat
   little orthogonal measures for our multi-stage pipeline to chew on."

   Its decision, `sharpest_of(scores)` (pure, pinned): "which reading is the highest, as an index;
   of equals, the earliest. Ties go to the earlier slice so the answer never depends on the order a
   caller happened to walk the stack in. A reading that was never taken cannot win. −1 when
   nothing was read at all, which is a caller's problem and not a slice to stand in for one."

   The same readings over a small box, `around(volume, centre_yx, reach_px)`: "handing them a
   small field is not a different measure, it is the SAME measure asked about a smaller world"
   (the founder, 2026-09-23: "Don't worry about the full grid, just worry about that little box").

2. **Per object, the slices around its detected depth** (`src/cell_tracking/record/depth.py`).
   For one detected object, every slice within a slab (`depth.slab` = 4, provisional) of its
   detected depth; in each, a disc of the nucleus radius read for light, spread and bodies.
   `sharpest_slices(values_by_z, sense)` (pure, pinned): "The slice(s) where a measure is greatest
   ("most") or least ("least"). NaN is ignored (a slice that could not be read is never the
   sharpest); ties are all returned, in ascending order, never broken — which of several equal
   slices matters is not this function's to say. Every value NaN, or none given → ()." Which
   measure decides a cell's sharpest slice is the founder's and was never given:
   `depth.sharpest_measure` = None, "none given, so every measure is reported" (open meaning rt-6).
   The founder's words it rests on (2026-09-21): "for every meaningful cell, build a composite
   image that has the highest resolution, the highest signal per-pixel and least spread, the most
   coherent shape, for each meaningful slice."

   Where one slice must be read, `record/route.py`'s `sharpest_of_ties(ties, detected_z)` (pure,
   pinned) breaks the tie: "The tie nearest the object's detected depth, and the lower slice of two
   equally near — the slice the first composite read took." No slice → −1, "nothing read at its
   own depth". The header reads the depth family at the object's own sharpest slice BY LIGHT
   (`ObjectHeader` docstring).

3. **Per place, its own brightest slice** (`src/cell_tracking/squint/composite.py`,
   `own_slices(volume, first, last)`): "Each place's own slice: the plane, from first to last,
   where its own light is brightest"; a place never imaged has −1; `np.argmax` takes the first of
   equals. The founder (2026-09-24): "then settle z (very doable, the "composite" lens can do this
   precisely, with just a little tweaking)"; the lead's restatement he answered "Good." to on
   2026-09-25: each place carries its own slice. `frame_composite` builds the flat picture by
   giving each spot `sharpest_slices(slice_lights(...), "most")` within the slab and
   `sharpest_of_ties(near, spot[0])`, falling back to the detected depth when the slab filter
   leaves none; the founder (2026-09-22): "We generate two types of composite in stage 0, and the
   disagreement between them is information about what the boundaries can find."

**What none of them does.** None combines readings into one score; none chooses the measure; a
NaN never wins; nothing is discarded (a slice with no imaged voxel reads NaN, never zero); the
route's decision of which slices get full processing is the founder's table (`route.preconditions`,
"empty until the founder reads the route packet"), and its own words for that filter: "the
density/veriance/uncertainty in the HDC-centric/primary lenses should be a cheap and dirty filter
to zero in on only the slices that are actually interesting or discriminative vs full processing on
every slice" (2026-09-20).

## Unit 4 against the cell build

| | the cell build | unit 4 as declared and packeted |
|---|---|---|
| scale | per plane (`focus.py`); per object (`depth.py`); per place (`composite.own_slices`) | per series: a few slices for the whole plane |
| readings per plane | gradient, contrast, split_quality (Otsu over a 256-bin histogram), dark_share (share at or under the frame's dark) | kept_share, dark_share (kept tiles with median at or below the split), split_quality (Otsu exact over the sorted kept medians), fat_share (above_below over the read pairs) |
| combination | never: one measure at a time; the disagreement is the information | never: each lens stands at its own slice; the set is deduped |
| the choice | the highest reading | the highest reading |
| NaN | never wins | never wins |
| ties | `focus.py`: the earliest; `depth.py`: all kept, none broken; `route.py`: the nearest to the detected depth, the lower of two equally near | the middle of the tied slices, the lower middle of an even count (`tie_middle`) |
| abstention | −1 when nothing read; no minimum count | `all_silent` when nothing read; `too_few_valid` below `minimum_valid` (8, the lead's) |

**Where unit 4 matches.** The form is the cell build's whole-plane rule: cheap readings per slice,
one measure at a time, the highest wins, NaN never wins, nothing combined. Two readings are the
same measure by name and nature: Split Quality and Dark Share, both the founder's own ("the
founder's own third idea", "The founder's own reading, taken literally"). The exact Otsu over the
sorted medians is the same measure as the cell build's over a binned histogram, computed without
the binning, which at a few hundred tiles a slice is the natural form.

**Where unit 4 differs, each put to the founder.**

1. *Ties.* The cell build never takes the middle: per plane it takes the earliest, per object it
   keeps every tied slice and breaks none, and where one must be read it takes the nearest to the
   detected depth. Unit 4's "middle of the tied run" is the lead's rule from the plan. The lead's
   inference, labelled as such: the knee has no detected depth to be near, and the earliest is a
   stack-order accident; since unit 4's chosen slices are a set anyway, keeping every tied slice
   (the per-object rule) is the form that decides nothing the cell build does not decide. Not
   changed: the decision as packeted returns one index, and the change is his to rule.
2. *The readings.* The cell build reads crispness (gradient) and contrast; unit 4 reads neither.
   At the squint there is no pixel gradient to read, and a tile-median contrast (variance over
   mean of the kept medians) was not declared. Whether either belongs at the squint is his.
3. *The scale.* The thesis's composite is per place and per object (each spot at its own slice);
   unit 4 is per series, the whole plane. The knee's objects (the bones) are large and the stack
   thin, so the lead declared one choice per lens per series. Whether a per-object depth is wanted
   later (each resolved object read at its own best slice, as the cell build reads each spot) is
   his, and would be a later unit, not this one.
4. *The bar.* `minimum_valid` (eight slices with a reading before a lens stands) has no counterpart
   in the cell build. It is the lead's (design §3), declared so a lens does not stand on one lucky
   slice; his to keep or drop.

## For him, in plain words

1. When a lens's reading ties across several slices, should it stand on all of them, on the
   earliest, or in the middle? The cell build keeps them all where it can.
2. Should the squint also read how crisp and how contrasty a slice is, as the cell build's focus
   reading does, or are the four as declared enough?
3. One choice of slices per series, or, later, each object at its own best slice as each cell is?
4. Is eight slices with a reading the right floor before a lens may stand, or is any reading
   enough?
