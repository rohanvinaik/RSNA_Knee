# Proposal: the funnel

## Why

The build runs nine stages that are each total over the whole field at native resolution, and no
stage consumes another's exclusion: the digits are written at every voxel, air included; the
distance transform, the traces, the pairings and the partitions run over the whole plane; the
squint is computed and targets nothing; the readings meet only in the bundles after the compute has
been spent everywhere. The founder, 2026-10-12, over the view sheets: "Literally EVERY analysis
that comes after this is wasting about 40-50% of its compute on places that should be comepltely
removed and NEVER read for ANYTHING, EVER ... Why try and draw boundaries where the bones aren't?
... Why compute vectors and shit where we know the knee isn't?" And the build is not the shape he
specified: "performance engineer, SICP-style, one compute operation per script, paralelizable
compute, shared information, superposition of lenses resolving meaning".

The thesis says what the pipeline is instead: a funnel. "Stage 1 clears what any eye would call
background before anything is drawn ... Each later step works only on what the earlier steps left"
(§4.6); "A coarse view of the whole field is itself a squint ... It narrows where the expensive
work runs" (§5.1); "Where a lens's stage 1/2 clears a place, that lens spends no full analysis
there" (§7.3); "Compute once, keep, consult ... A lens that cannot speak at a depth is not computed
there" (§13.6); and the collapse: "The movie is read as flat two-dimensional stills, one for each
lens at its own depth" (§4).

The founder confirmed the lead's restatement of the funnel on 2026-10-13 as "the correct
epistemology and workflow", answered the five questions the Codex consult left, and set the scope:
"we need to be able to resolve ALL of the relevant anatomical objects to diagnose between the 12
conditions". His words are verbatim in `docs/chapters/02-collapse/teachings.md`, the plan and the
consult in `docs/chapters/02-collapse/readings/the-funnel-plan-*-20261013.md`.

## What changes

- **The route becomes a funnel.** The nine stage names stay. Every stage after the first lens
  computes only inside what the stages before it left; the squint does the localisation; native
  resolution is spent only along an object's edge, or inside an object when a predicate asks;
  objects are found in rounds, each round located by the objects the round before resolved.
- **The first lens is background versus leg, per view, at the squint, frozen.** Its authority is
  being correct, checked by his eye on each of the five views. A tile it did not positively declare
  background stays in play; a tile that straddles the skin line is left undecided.
- **The two acquisitions of one orientation line up by place on the knee**, in the scanner's
  millimetres, at the squint, and their digits are read together; no other view is laid over
  another.
- **Depth collapses as the thesis collapses a movie**: cheap readings over every slice, each a
  lens standing at the one slice where it peaks; only those slices are read in full.
- **The dome at the squint grounds the objects**; selection is by structural facts, never a name;
  the edge is drawn at native resolution in a strip along the tile boundary; facing pairs,
  interstices with their walls, fill and contents, then spans and the envelope follow, each located
  by what is already resolved; the residual is what no object claims.
- **Nothing is removed.** Every whole-field lens that exists stays in the tree, callable and
  drawable from a saved run; the route no longer calls the whole-field forms.
- **The engineering shape he specified** is enforced per unit: one compute operation per module,
  pure, over kept readings, parallel over series, tiles and objects, each rendering what it
  resolved, under `docs/STAGE_CONTRACT.md`'s loop.

## Capabilities

### New capabilities

- `funnel-route`: the route as a funnel, each stage consuming only what the stages before it left,
  with the first lens, the line-up, the depth collapse, the tile dome, the native strip, the facing
  pairs and the rounds as its operations.

### Modified capabilities

- `knee-objects`, `object-relations`, `finding-predicates` (from `knee-object-model`): their
  requirements stand; this change supplies the order, the scale and the scope in which they are
  built. `physical-measurements`, `geometric-interiors` and `same-knee-conversation` (from
  `object-resolution-toolkit`) are reused scoped, not rewritten.

## Impact

`src/knee/` gains one module per operation inside the existing packages; `knee.pipeline.run_study`
is reordered; `AnalysisRequest` gains the funnel's bars; `knee.pictures` and `workbench/render`
gain one arrangement per new record and new panels on the view sheets; `docs/places.json` declares
every new module. `every-stage-renders` is superseded as the active change: its route composition
and rendering obligations are carried here. No competition data is redistributed; pictures stay
under ignored `data/`. No bar is chosen to separate gold (project law 4); every constant is an
argument with its provenance, and the ones the lead proposed are his to change by eye.
