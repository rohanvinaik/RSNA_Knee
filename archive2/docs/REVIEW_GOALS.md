# What this review is for

**Every file in this diff is in it because nothing calls it, or because it runs and does not do its
job.** This is not a change set. It is the broken surface of a production pipeline, assembled
deliberately so the review has the whole of it in one place.

Do not review these files as a diff. Review them as code that is supposed to be part of one running
system and is not.

## The system, and the standard it is measured against

A classical-AI computer-vision entry for RSNA Knee Abnormality Detection. **There is no machine
learning in the architecture, and that is load-bearing, not a preference.** No CNN, no transformer,
no fitted weight, no learned embedding, no "small learned component". The system resolves
`<object>`s — *"a resolvable sub-set of the visual field presented to a computer vision pipeline"* —
from the data's own geometry, constructs relations between them, and reads twelve diagnostic
findings as predicates on those objects and relations.

**Do not propose a model, a classifier, a learned encoder, or a threshold tuned to data.** That
substitution is this project's recorded failure mode. Anatomy informs the *design* of a lens and is
never written into a *record*: no stage writes "femur".

The founder's standard, verbatim:

> "a single study of images can come into the project in a single entrypoint and compute everything
> we've developed in a single end-to-end production pipeline, with full telemetry and visual output
> and everything, and show the combined sum total of all the analyses we have in conversation with
> one another, able to resolve every significant \<object> in the visual field as a single-command
> pipeline process"

And the failure he named, which is what this diff contains:

> "agents like you tend to tunnel-vision when there's a hard problem, and build out a mountain of
> code in one arbitrary spot, one function at a time, and sort of lose the thread of *why* the code
> exists, *where* it sits in a greater project pipeline. That makes it impossible to work, since
> there isn't an actual working pipeline, just functionalities in islands, entire unto themselves.
> And it makes efficiency terrible, since things computed for one step are completely forgotten
> about and re-computed from scratch for an entirely different step."

> "I don't run ANY by hand. ALL probes are supposed to be part of production."

> "the lack of a consumer IS the fucking problem."

## What runs today

`just analyze-objects --uid <study> …` exits 0 on a real study. It reads the DICOMs at stored
fidelity, measures each series' regime key and squint, resolves geometric interiors and a boundary
census, runs a same-knee conversation between same-orientation acquisitions, writes a
balanced-ternary digit for every place of every acquisition against that series' own tercile edges,
partitions every place into claimed or unassigned, retains sampled pairs across dark bands, and
prints eight galleries with a receipt digesting every array and source file.

**It then says nothing about the knee.** All twelve findings abstain on every study. No diagnosis,
no number, no CSV.

## What is in this diff, and why

**Group 1 — nothing in the repository reaches these.** Computed by walking imports from every entry
point: the production route (`knee.pipeline`), the real entry point
(`workbench.measure.object_analysis`), the joined drawing pass (`workbench.render.all_frames`), and
every `scripts/*.py`, which the justfile runs by path. 66 of 97 modules are reached. These are not.

Several do real work that the one command never performs — finding the joint line as a relation
between two watershed basins with the superior–inferior axis read from the DICOM header; defining
air by connectivity to the frame's border rather than by a threshold; asking whether the femur and
tibia are present as two bodies; reading the corpus's shape, its noise floor, and its regime across
all 58 studies.

Two are picture adapters inside the production package with **zero callers**:
`knee/pictures/collapse.py` carries the field stage's four panels and no drawer exists to call it;
`knee/pictures/study.py` is bypassed by a renderer that goes somewhere else.

**Group 2 — these run and do not do their job.**

- `knee/relations/` — returns `construction_absent` on every series of every run. Ten of the twelve
  findings need a subject this stage would construct. A candidate that retains 597 sampled pairs
  across dark bands on one study exists beside it and is not consumed.
- `knee/predicates/findings.py` — returns twelve named standings per study; all twelve abstain,
  because no subject is constructed for ten of them and no expected correspondence is declared for
  any.
- `knee/pipeline.py` — the route itself: nine stages, four of which do not do their job.
- `workbench/render/all_frames.py` — the joined drawing pass; three route stages have no entry in
  its table at all, so they are never drawn.
- `workbench/measure/object_analysis.py` — the single entry point and the writer.

## What the review is asked to find

1. **For each unreached module: what should consume it, and what is missing between it and that
   consumer?** Name the specific wiring. "It is unused" is already known and is not a finding.
2. **Where is a value computed and then dropped?** The writer computed a sixteen-reading regime key
   per series and persisted one field of it for weeks, inside a fully-reached file. Import
   reachability cannot see that class of defect. Find the others.
3. **Where is the same work done twice** by two paths that do not share a value — the founder's
   "re-computed from scratch for an entirely different step".
4. **Where does a record, a code or a picture assert more than the measurement under it supports** —
   a silence written as a zero, an absence written as a negative, a derived value presented as
   measured.
5. **Where are there two code paths for one job**, one of them the one that actually runs.

## What the review is asked NOT to do

- **Do not propose deletions.** Unreferenced is not dead. `knee/lenses/slabs.py` is finished,
  mutation-pinned work encoding a real fact about the instrument — a 2D multi-slice series is a
  stack of slabs, not a lattice of points — and it is unreached only because the operation that
  would consume it has not been built. Treating "no caller" as "remove" is the error that produced
  this review.
- **Do not propose a redesign, a model, or a new architecture.** The design is the founder's and is
  not under review.
- **Do not grade the abstentions as a quality failure.** The founder: *"Doesn't have to be good, or
  able to diagnose — it has to have the requisite component of the full thesis, and have the
  symbolic capacity to resolve and reason on these `<object>`s."* Abstention with a named reason is
  correct behaviour; the defect is the missing inputs and consumers underneath it.
- **Do not rely on the lead's own claims.** `docs/WIRING_GAPS.md` is included in this diff and its
  characterisations have already been wrong more than once in one session. Check it against the
  code.
