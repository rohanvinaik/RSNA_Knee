# The wiring work, written for whoever picks this up next

Written 2026-10-12 by the outgoing lead, at the founder's instruction, for an agent with no prior
context. Everything here was computed with a command rather than recalled, and every command is
named so you can recompute it. Where this document asserts something it could not measure, it says
so.

Read `AGENTS.md` and `docs/OBJECT_MODEL.md` before acting on any of it. Run `just unit` first.

---

## 1. What this project is, stated so you do not import the wrong prior

This is a classical-AI computer-vision entry for RSNA Knee Abnormality Detection. **There is no
machine learning in the architecture, and that is load-bearing rather than a preference.** No CNN,
no transformer, no fitted weight, no learned embedding, no "small learned component for the hard
part". The founder has a track record behind this: a leaderboard-ceiling score with 99.8%
deterministic decisions, money won with under 1% LLM, ARC-AGI on a deterministic story engine.

The system resolves `<object>`s — *"a resolvable sub-set of the visual field presented to a computer
vision pipeline"* — from the data's own geometry, constructs relations between them, and reads
twelve diagnostic findings as predicates on those objects and relations. A finding is a predicate
violation on an object, or on a relation between objects; it is never a pattern searched for in a
field. An interstice is **constructed, not detected**: the moment two bones are objects, the space
between them exists as a relation, with its own extent, walls and fill.

Anatomy informs the **design** of a lens and is never written into a **record**. No stage writes
"femur". You need to hold the anatomy in your head to build the right lens; the pipeline does not
need the word.

The word "Kaggle" and the words "vision", "image" and "competition" all pull hard toward proposing a
model. Do not. That substitution is this project's recorded failure mode and the founder has had to
purge it before.

**The second thing not to do, which is what went wrong today**: do not treat a measurement as a
verdict. `vulture` reporting that a name is unreferenced is a reading about the *route*, not about
the code's worth. The outgoing lead wrote "dead code" into a document and came within one user
intervention of proposing deletion of `knee/lenses/slabs.py`, which is finished, mutation-pinned
work encoding a real fact about MRI acquisition. Unreferenced means *its consumer does not exist
yet*. The repair is always to build the consumer, never to delete the unit.

## 2. The standard the work is measured against

The founder's own sentence, which is the acceptance condition for all of it:

> "a single study of images can come into the project in a single entrypoint and compute everything
> we've developed in a single end-to-end production pipeline, with full telemetry and visual output
> and everything, and show the combined sum total of all the analyses we have in conversation with
> one another, able to resolve every significant \<object> in the visual field as a single-command
> pipeline process"

And the failure he named, which is precisely what the repository currently contains:

> "agents like you tend to tunnel-vision when there's a hard problem, and build out a mountain of
> code in one arbitrary spot, one function at a time, and sort of lose the thread of *why* the code
> exists, *where* it sits in a greater project pipeline. That makes it impossible to work, since
> there isn't an actual working pipeline, just functionalities in islands, entire unto themselves.
> And it makes efficiency terrible, since things computed for one step are completely forgotten
> about and re-computed from scratch for an entirely different step."

Three of his rulings bear directly on the work below and each one struck a justification the
outgoing lead had invented:

- *"I don't run ANY by hand. ALL probes are supposed to be part of production."*
- *"the lack of a consumer IS the fucking problem."*
- *"we always keep information we compute. I'll resolve what we report and how we do it, but the
  pipeline should keep everything, including where things conflict."*

**The contract is not the problem.** He wrote it over more than ten million tokens, and it is good.
Every gap below exists despite it.

## 3. What actually runs today

`just analyze-objects --uid <study> --tile-mm 3 --span-mm 3 --samples 13 --axis superior --backend
jit --prominence-mm 3 --out <dir>` exits 0 on a real study and does a great deal. It reads the
DICOMs at stored fidelity; measures each series' regime key and its squint; resolves geometric
interiors and a boundary census; runs a same-knee conversation that exchanges boundary readings
between same-orientation acquisitions; writes a balanced-ternary digit for every place of every
acquisition against that series' own tercile edges; partitions every place into claimed or
unassigned; retains sampled pairs across dark bands; and prints eight galleries with a receipt that
digests every array and every source file.

The parse genuinely works. On the coronal fat-suppressed series of the one study measured, it
separates the femur, the tibia and the joint line between them as distinct territories, with no
threshold chosen and no anatomical name written anywhere.

**And then it says nothing about the knee.** All twelve findings abstain on every study. There is no
diagnosis, no number and no CSV. That is the gap, and everything below is a part of it.

## 4. The wiring, module by module

Run `just places`. It now walks every layer from the thing that actually calls it: the production
route `knee.pipeline`, the real entry point `workbench.measure.object_analysis`, the joined drawing
pass `workbench.render.all_frames`, and every `scripts/*.py`, which the justfile runs by path.
Before today it asked only whether a `route:*` module was reachable from `knee.pipeline`, which
meant it examined 46 modules out of 97 and 51 were checked by nothing at all.

**66 of 97 modules are reached. These 22 are not, and all 22 are gaps.**

### The two that are plainly defects

`knee/pictures/collapse.py` has **zero callers**. It is the field stage's picture adapter and it
carries four panels: the recorded slice, the leg closed by filling its holes, the squint at tile
scale, and the profile along the superior–inferior axis where the two bones appear as two plateaus
and the seam between them as the dip. That last panel is the picture of the thing the founder
described on 2026-10-10 when he said the knee is two objects that combine. No drawer exists that
calls any of it, so the field has never been drawn, and `all_frames` records `collapse` as
`no_drawer` on every run.

The outgoing lead rewrote this adapter around what the stage computes today, decided the leg and the
profile "described nothing real", and was wrong to do so: those are the founder's design. It has
been restored byte-identical to `92e5b7e`. **Leave it alone and build the drawer that calls it, or
make the stage compute what it asks for.** Which of those two is right is the founder's call and he
has not been asked.

`knee/pictures/study.py` is bypassed. The study stage *is* drawn, but `workbench/render/object_packet.py`
goes to `workbench/render/object_profiles.py` instead, so there are two code paths for one stage's
picture and the declared one is the dead one.

### The three whose consumer has not been built

`knee/lenses/slabs.py` is the slab rule, and it is the most important item in this document to not
mishandle. Its content: a 2D multi-slice knee series is not a lattice of points but a **stack of
slabs**, so a voxel in a 3.5 mm slice measures the whole 3.5 mm slab — reading a place inside a
foreign slab is not interpolation at all — while a place that falls in the inter-slice gap was
genuinely not measured, and its row is silent. The test is `|dot(p − c, n)| ≤ SliceThickness/2`,
using thickness and never `SpacingBetweenSlices`, because spacing includes the gap and using it
would silently claim the gap as measured. Its decisions are Detective-COMPLETE at 55/55, 21/21 and
7/7. It is unreached because the operation that would consume it — conjunction across acquisitions,
which is the `vectors` stage — has not been built.

`knee/vectors/__init__.py` is that stage, and it is a docstring and nothing else. This is where an
`<object>`'s readings across the acquisitions would be assembled, per the thesis's own figures H2a2
and H2b, which the founder attached and said were the design: a profile is **row counts over named
banks**, the knee's lens axis is the acquisitions, every row is one balanced-ternary digit against a
middle, and a bank this build cannot write is carried as a **named absence and never as rows of
zero**, because a zero count asserts a reading was made and found nothing. The capability spec is
written: `openspec/changes/every-stage-renders/specs/object-bundles/spec.md`.

`knee/output/__init__.py` is likewise a docstring. Nothing emits a confidence, and the numeric
projection is undeclared by the founder's deliberate choice (see §7).

### The four packages the route does not reach

`knee/memory`, `knee/expert`, `knee/agencies` and `knee/record` are empty packages nothing calls.
**Be careful with the record here, because the outgoing lead got it wrong.** `docs/OBJECT_MODEL.md`
and `docs/PIPELINE_AS_OBJECT.md` both say these are "deferred to diagnosis, by his ruling". **There
is no such ruling.** What exists is his sequencing remark of 2026-10-11 — *"get EVERY `<object>`
cleanly, then work on diagnosis, which is where recall of specific presentations will matter"* —
which says when recall is used. A prior lead turned that into "deferred" and wrote it into two
architecture documents; the outgoing lead then repeated it back to the founder as his own ruling and
was corrected. Treat their disposition as **open and his to settle**, and fix those two documents.

### The thirteen that do real work outside the one command

These are in `workbench/` and were described in `docs/places.json` as `runs_on_import: true`, which a
prior lead wrote. The founder's correction: *"I don't run ANY by hand. ALL probes are supposed to be
part of production."* So each of these is a gap, and several of them compute things the one command
does not:

`workbench/render/seam.py` closes the leg by filling its holes, reads the superior–inferior axis
from the DICOM header rather than assuming image rows, and finds the seam as the saddle set between
two watershed basins — a relation between two objects rather than a dark band hunted by intensity.
`workbench/render/structure.py` defines air by **connectivity to the frame's border** rather than by
any threshold, then asks whether the joint line survives the squint and where a population of
studies disagrees. `workbench/render/objects.py` asks whether the femur and tibia are present as two
bodies with a space where they meet, on both weightings of one coronal study, because marrow's sign
flips between them while cortex is signal-void on both. `workbench/render/axial.py` and `look.py`
draw the stack and the four basic views.

On the measurement side, `corpus_shape.py` reads the corpus's view structure from the tables with no
pixel decode; `noise_floor.py` asks whether there is imaged air to measure sigma from and whether
the intensity law looks Rician; `regime_key.py` and `regime_run.py` read the regime across the 58
through the real entry point; `geometry_spread.py` reads per-view geometry spread;
`object_toolkit_geometry.py` reads native spacing and projection; `machinery_facts.py` establishes
what the object stage actually produces; `reports.py` reads the report column.

Several of these overlap the `collapse` stage's missing picture. `seam.py` and `structure.py`
between them compute very nearly the four panels that `knee/pictures/collapse.py` asks for. Whether
the right repair is to move that work into the stage, or to have the stage's drawer call it, is a
design question for the founder.

## 5. The four stages that run and do not do their job

`knee.pipeline.ROUTE` declares nine stages. Four of them produce nothing usable.

**`relations` returns `construction_absent` on every series of every run.** It is an honest shell
that names the one unit it waits for. Ten of the twelve findings need a subject this stage would
construct. A candidate exists beside it — `knee/relations/pairings.py`, which retains 597
sample-supported pairs across dark bands on one study, with every refusal kept — and the shell does
**not** consume it. Note carefully what the missing piece is: not "store the far side of a boundary".
`read_interiors` labels only `interior = available & ~dark` and runs watershed with `mask=interior`,
so across a dark cortex the neighbour is a dark place whose label is 0. There is no far-side label to
store. The interstice must be **constructed**, and that is a different and harder operation than a
lookup. The support contract is written at
`openspec/changes/every-stage-renders/specs/dark-bounded-pairing/spec.md`.

**`vectors` is not called by the route at all.** See §4.

**`predicates` runs and decides nothing.** `knee/predicates/findings.py` returns twelve named
standings per study; all twelve abstain, two because the predicate's form has not been given and ten
because no subject is constructed. A dispatch answer written on 2026-10-12 was **deleted rather than
amended**, because it claimed no resolved fact selects any subject while
`measurements.boundaries` sat unread on the same object carrying `pair_labels` — the touching pairs,
each ascending and listed once, with their sites, saddles and codes. Whether the code from that
attempt stays, is rewired, or comes out is the founder's call and he has not made it.

**`output` is unbuilt.** See §7 on why its number is deliberately undeclared.

## 6. Work that is computed and thrown away

This is the class of defect that import reachability cannot see, and it is the one the founder cares
about most: *"things computed for one step are completely forgotten about and re-computed from
scratch for an entirely different step."*

**One instance was found and fixed today.** `read_regime` computes a sixteen-reading regime key per
series — two independent noise estimates with the count each was read from, the channel count, four
named words, the zero share, the foreground share, both tercile pairs, the distribution's spread and
skew, its profile down the stack, and the background split. The writer took `background_split` and
dropped the other fifteen, on every series of every run, for weeks, inside a fully-reached file. It
now serialises every field by enumerating the dataclass, so a reading added later cannot be silently
dropped again.

**The squint is saved and nothing draws it.**

**No counted-work budget exists for any stage**, which `docs/STAGE_CONTRACT.md` item 8 requires. The
lens stage was changed today to read two populations instead of one over the full native volume, and
that cost has not been measured against anything.

**Nobody has looked for the other instances.** The five profiling recipes that would find them —
`just trace`, `just memory`, `just profile`, `just profile-lines`, `just profile-tree` — could not
profile this project at all until today: none of them set `PYTHONPATH`, while every other recipe
that runs project code does, and each profiler runs its target through `runpy.run_path`, which does
not put the repository root on `sys.path` the way `python -m` does. Any target importing `knee` or
`workbench` died with `ModuleNotFoundError` before executing a line. That is fixed; the audit it
enables has not been run.

## 7. What is the founder's to settle, and must not be invented

1. **The expected correspondence `e`.** The hand-given correspondence between a reading and what it
   means — the water written on the hand, in his Helen Keller argument. It must be declared with its
   author and date, and it cannot be derived. If it is ever supplied from `memory` rather than
   declared, that is the door a fitted value re-enters the architecture through.
2. **The numeric abstention projection.** His correction: *"I don't know, that should resolve
   experientially, when actually running and seeing it in action."* Named decisions run and render
   without it; CSV emission is refused while it is undeclared.
3. **The local structural normalisation** that must precede the digits. He settled the *ordering* —
   local structural normalisation, then tercile edges, then conjunction across acquisitions — and
   has not given the normalisation itself. The lens stage therefore records `normalisation: none`,
   honestly, and **is not complete**; do not let any document imply otherwise.
4. **The laterality fallback** when the primary witness (the fibula) is absent. Secondary witnesses
   are for concurrence and are not silently promoted.
5. **The conversation's one-name merge rule** (`object-resolution-toolkit` task 3.13).
6. **The disposition of the four diagnosis packages** (§4).
7. **Whether the probe fraction, the `21f6b41` predicate code, and the four `pictures/collapse.py`
   panels stay, move or change.**

He has also said what he will do once the machinery exists, and it is worth knowing because it
shapes what "done" means: *"If you build it and show me how each stage works, I am your fluid
intelligence oracle 'Advisor' you can call, I will tell you how to get the good numbers."* The
pictures are the channel through which he supplies the next lens. A stage that does not render is
not merely unfinished — it is closed to the only input that can improve it.

## 8. Errors in the record, left by the outgoing lead, that you will otherwise inherit

- `docs/OBJECT_MODEL.md` and `docs/PIPELINE_AS_OBJECT.md` say `memory`, `expert`, `agencies` and
  `record` are deferred "by his ruling". **No such ruling exists** (§4).
- `docs/places.json` marks thirteen workbench modules `runs_on_import: true`, which was read as "run
  by hand" and is wrong (§4).
- `docs/PIPELINE_AS_OBJECT.md` contains a capacity property reading *"every decision reads a
  RELATION between its subjects rather than a property of one"*. That clause was written by a lead,
  not by the founder, and his own words contradict it: a fracture is *"a break in the structural
  coherence of a 'bone' object"* — a predicate on one object. Fable identified this; it is not an
  open ruling, it is a clause to remove.
- `docs/chapters/02-collapse/readings/wiring-gaps-fable.md` contains a question Q2 whose premise is
  false — it treats a population containing air as disqualified from the three-legged stool. Every
  lens is correct by definition (the rigid oracle, point 1), and air is a positively assigned
  structural class rather than contamination. **Strike Q2**; the rest of that reading stands and is
  very good.
- `docs/WIRING_GAPS.md` was written by the outgoing lead and its characterisations were wrong more
  than once in a single session. Check it against the code rather than believing it.

## 9. Where things are, and how to recompute all of it

`main` holds the real history. The branch `review/wiring-gaps` holds a deliberately assembled commit
— an empty base `b854662`, then `7d9a52f` adding 55 files, 7,012 lines: the 22 unreached modules,
the four stages that do not work, their potential consumers, and `docs/REVIEW_GOALS.md`. It was
built as the target for a cloud review that did not run. It is a partial checkout and is not a
working tree; `git switch main` restores everything.

Nothing has been deleted this session. Zero files removed.

To recompute every number in this document:

```
just unit                     the build loop, the route's declared standing, the open tasks
just places                   66 of 97 wired; the 22; the three unreached route modules
just graph <out>              the development DAG; a value nothing consumes shows as dangling
just imports                  the layer contract: production never imports drawing or dev tools
just gate                     ruff, pytest, imports, places, graph, deptry, ty, vulture at two scopes
vulture src workbench scripts            names nothing in production calls
vulture src workbench scripts tests      names nothing anywhere calls
```

`scripts/ci_local.sh` now runs the whole toolkit on every commit rather than depending on anyone
remembering it. The vulture scopes are deliberately unfiltered: a `--min-confidence` floor is a
filter on a tool's output, and filtered output is how the islands survived.

Three readings from independent second readers are worth reading before you start, in
`docs/chapters/02-collapse/readings/`: `wiring-gaps-fable.md` and `wiring-gaps-codex.md` on this
material, and `the-conclave-{fable,codex}.md` on the pipeline's shape. They were given the founder's
complete preserved prompts as the oracle and they corrected the lead on most of what he claimed.
