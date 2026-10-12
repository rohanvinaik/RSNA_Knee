# The wiring gaps: what is built, what is connected, and what is neither

> **SUPERSEDED 2026-10-12.** This list was written to guide a repair and the repair landed
> (`openspec/changes/every-stage-renders/tasks.md` §6, `specs/route-composition/spec.md`), so its
> claims about the route are now anti-correlated with the source. `docs/HANDOFF_WIRING.md` §8 names
> this file as one whose characterisations were wrong more than once in a session, and Codex's
> reading (`chapters/02-collapse/readings/wiring-gaps-codex.md`) found one claim in §F false within
> the document itself: Hypothesis HAD run before 2026-10-12 — the preserved record invokes
> `--hypothesis-seed` and a commit records "Hypothesis falsified B1's topology invariant". Recompute
> state with `just unit`, `just places`, `just graph <out>` and the composition test; read nothing
> below as current.

Computed 2026-10-12 at `4412145` plus the working tree, with the tools the founder specified and
which this lead had not been running. Every number below came from a command, not from a reading of
the code. The commands are named so each line can be recomputed.

**The standard this is measured against is the founder's, verbatim:**

> "a single study of images can come into the project in a single entrypoint and compute everything
> we've developed in a single end-to-end production pipeline, with full telemetry and visual output
> and everything, and show the combined sum total of all the analyses we have in conversation with
> one another, able to resolve every significant \<object> in the visual field as a single-command
> pipeline process"

> "agents like you tend to tunnel-vision ... and build out a mountain of code in one arbitrary spot,
> one function at a time, and sort of lose the thread of *why* the code exists, *where* it sits in a
> greater project pipeline. That makes it impossible to work, since there isn't an actual working
> pipeline, just functionalities in islands, entire unto themselves. And it makes efficiency
> terrible, since things computed for one step are completely forgotten about and re-computed from
> scratch for an entirely different step."

**The contract is not the problem.** The founder wrote it over more than ten million tokens, and
every gap below exists *despite* it, not because of it. Each one is a place a prior lead built
something and did not connect it, or connected it and did not keep what it made.

---

## A. Stages that do not do their job (`just unit`, `knee.pipeline.ROUTE`)

Four of nine. The route runs end to end and exits 0; it produces no statement about a knee.

| stage | standing | what is missing |
|---|---|---|
| `relations` | **never constructs an interstice** | returns `construction_absent` on every series of every run. Task 1.3a built a *candidate* that retains 597 sampled pairs across dark on one study, and it is not admitted and not consumed as a construction. **Ten of the twelve findings need the subject this stage would build.** |
| `vectors` | **unbuilt, unreached** | not called by `run_study` at all. `just places` reports it unreached. This is where an `<object>`'s readings across acquisitions would be assembled. |
| `output` | **unbuilt, unreached** | nothing emits a confidence. There is no CSV and no declared numeric projection. |
| `predicates` | runs, **decides nothing** | returns twelve named standings per study; all twelve abstain, because no subject is constructed for ten and no expected correspondence `e` is declared for any. |

## B. Work that exists and is NOT YET CONSUMED (`vulture`, two scopes, unfiltered)

Added to `scripts/ci_local.sh` on 2026-10-12 so this prints on every commit. It had **never been
run on this repository**, which is why nobody knew the list.

**What this measurement is, and what it is not.** `vulture` reports whether a name is *referenced*.
That is a reading about the ROUTE — what the pipeline currently reaches — and it carries **no**
authority about whether the code should exist. An earlier draft of this section called these names
"dead" and filed them under what must be fixed. That was the lead attaching a verdict to a
measurement, which is the move this project forbids: a lens measures and warrants no decision alone
(`AGENTS.md`, the rigid oracle, point 2). **Nothing here is a deletion candidate**, and the founder's
design is not edited on a tool's say-so (law 9).

The correct reading of every line below is: *the consumer that would use this does not exist yet.*
The repair is to build the consumer, or to leave the unit alone until its stage arrives.

**Referenced nowhere, tests included:**

- `knee/pipeline.py::route_state`
- `knee/study/decoders.py::decoder_plugins`
- `knee/pictures/objects.py::parted_more_by`
- `knee/study/corpus.py::KAGGLE_ROOT`
- `workbench/render/structure.py::seed_quantile` (100% confidence)

**Referenced only by tests — "defined, imported and tested with no production caller", which
`AGENTS.md` names as the thing to check before every edit:**

- `knee/absence.py::is_silence` — part of the shared absence vocabulary
- `knee/collapse/noise.py::coil_count`, `::signal_squared` — part of the noise law
- `knee/objects/boundaries.py::carries_prominence` — part of the boundary census
- `knee/study/tables.py::split_uids`
- the whole of `knee/lenses/slabs.py` — `slab_code`, `was_measured`, `gap_fraction`,
  `half_thickness`, `SLAB_CODES`

**`slabs.py` is the clearest case and the reason this section was rewritten.** It is the slab rule:
a 2D multi-slice series is not a lattice of points but a stack of slabs, so a voxel in a 3.5 mm
slice *measures* the whole 3.5 mm slab — reading a place inside a foreign slab is not interpolation
at all — while a place in the inter-slice gap was genuinely not measured and its row is silent. It
is finished, pinned work (Detective COMPLETE at 55/55, 21/21, 7/7). It is unreached because the
operation that would consume it — conjunction across acquisitions — **has not been built**. Calling
that dead would have destroyed a correct account of the instrument.

**One deletion was already made on the wrong reasoning**, and it is recorded rather than hidden:
`knee/lenses/members.py::is_retained` was removed on 2026-10-12 because vulture flagged it. It was
the lead's own code, written the same day, so nothing of the founder's was lost — but the reasoning
was the error above, and it is restorable from git if wanted.

*(Dataclass fields and Hamilton's name-resolved graph nodes are vulture false positives and are not
listed.)*

## C. The 22 modules nothing reaches (`just places`, extended 2026-10-12)

Until today `just places` asked **one** question — is a `route:*` module reached from
`knee.pipeline` — and asked it of 46 modules out of 97. The other 51 were checked by nothing. It now
walks every layer from its own entry point (`knee.pipeline`, `workbench.measure.object_analysis`,
`workbench.render.all_frames`, and every `scripts/*.py`, which the justfile runs by path).

**66 of 97 modules are wired to something. These 22 are not:**

```
src/knee/agencies/__init__.py              src/knee/pictures/collapse.py
src/knee/expert/__init__.py                src/knee/pictures/study.py
src/knee/memory/__init__.py                src/knee/lenses/slabs.py
src/knee/record/__init__.py                src/knee/output/__init__.py
                                           src/knee/vectors/__init__.py

workbench/measure/corpus_shape.py          workbench/render/axial.py
workbench/measure/geometry_spread.py       workbench/render/look.py
workbench/measure/machinery_facts.py       workbench/render/objects.py
workbench/measure/noise_floor.py           workbench/render/seam.py
workbench/measure/object_toolkit_geometry.py   workbench/render/structure.py
workbench/measure/regime_key.py
workbench/measure/regime_run.py
workbench/measure/reports.py
```

**All 22 are gaps.** An earlier draft of this section sorted 20 of them into three buckets —
"deferred by the founder's ruling", "standalone probes run by hand", and "waiting for a consumer
that does not exist" — and reported only the remaining 2 as findings. Every one of those three
justifications was false, and the founder struck all three:

- **"Deferred by his ruling"** for `memory`, `expert`, `agencies`, `record`. **No such ruling
  exists.** What exists is his 2026-10-11 sequencing remark — *"get EVERY \<object> cleanly, then
  work on diagnosis, which is where recall of specific presentations will matter"* — which says when
  recall is used. A prior lead turned that into "deferred" and wrote it into `OBJECT_MODEL.md` and
  `PIPELINE_AS_OBJECT.md`; this lead then repeated it back to him as his own ruling.
- **"Probes run by hand."** Taken from a `"runs_on_import": true` field a prior lead put in
  `places.json`, and from example commands in `TOOLING.md`. His correction, 2026-10-12: *"I don't
  run ANY by hand. ALL probes are supposed to be part of production."* These thirteen do real work
  that the one command does not: `seam.py` finds the joint line as a relation between two basins
  with the axis read from the header; `structure.py` defines air by connectivity to the frame's
  border and asks whether the joint line survives the squint; `objects.py` asks whether femur and
  tibia are there as two bodies; `noise_floor.py`, `regime_key.py`, `regime_run.py` and
  `corpus_shape.py` read the corpus.
- **"Waiting for a consumer."** Circular. His correction: *"the lack of a consumer IS the fucking
  problem."* `slabs.py`, `vectors` and `output` having nothing that calls them is the gap itself.

**Two of the 22 are picture adapters in the production package that nothing calls.**
`pictures/collapse.py` carries the field's four panels — the recorded slice, the closed leg, the
squint, and the profile along the superior–inferior axis where the two bones read as two plateaus
with the seam as the dip between them — and no drawer exists to call it. `pictures/study.py` is
bypassed: the study stage is drawn, but `object_packet` goes to `object_profiles` instead.

**What this check still cannot see.** It reads imports between modules. It cannot see a value
computed inside a reached module and then dropped — which is exactly how the regime key was binned
for weeks inside a fully reached file. That question belongs to `just graph` (a value nothing
consumes) and to `vulture` (a name nothing calls). Three questions, three tools; they are not
interchangeable and were being reported as if they were.

## D. Work computed every run and thrown away

- **The regime key.** `read_regime` computes sixteen readings per series. Until today the writer
  took `background_split` and dropped the other fifteen — recomputed on every run of every series,
  and never reaching the record or any picture. *Fixed in the working tree; every field is now
  serialised by enumerating the dataclass, so a new reading cannot be silently dropped again.*
- **The squint.** Saved, and nothing has ever drawn it.
- **`collapse` has no drawer**, so the field — regime and squint — appears in no picture.
  `vectors` and `output` have none either; the joined index names all three as `no_drawer`.

## E. Proof standing that is open, stated rather than claimed

- `knee/lenses/places.py::place_codes_reference` — Detective **`UNGATEABLE`**, 42 behaviours /
  30 pinned, 12 unclassified because mutants could not be BUILT. Per the founder this is a floor and
  not a blocker; the decision surface is pinned through `digit_code` (COMPLETE 93/95) plus an exact
  scalar/map agreement test.
- `knee/relations/pairings.py::footprint_labels_reference` — Detective **`UNGATEABLE`**, same shape.
- `places.py`'s three array post-conditions — CrossHair **`Not confirmed`**: neither a violation nor
  a pass.
- **No counted-work budget exists for any stage.** `STAGE_CONTRACT` item 8 requires one. The lens
  stage now does twice the work it did this morning (two populations over the full native volume)
  and that cost has not been measured against anything.

## F. Tooling that was specified and was not being used

The founder: *"you're supposed to use every single one for every single commit and every single
non-trivial change of the code. As I've specified dozens of times."*

Never run before 2026-10-12: `vulture`, `just deps` (deptry), `just trace`, `just memory`,
`just profile`, `just profile-tree`, `just profile-lines`, `just profile-calls`, py-spy, pyperf,
asv, Hypothesis, `just coverage`, radon, symbex, semgrep, aider-map, LintGate, Prism.

**Two tooling defects found the moment they were used:**

1. **Five profiling recipes could not profile this project at all.** `just trace`, `just memory`,
   `just profile`, `just profile-lines` and `just profile-tree` never set `PYTHONPATH`, while every
   other recipe that runs project code does. Each profiler runs its target through
   `runpy.run_path`, which does not put the repository root on `sys.path` the way `python -m` does,
   so any target importing `knee` or `workbench` died with `ModuleNotFoundError` before executing a
   line. *Fixed in the working tree.*
2. **`scripts/ci_local.sh` ran four checks.** It now runs the import contract (blocking), places,
   the Hamilton graph, deptry and vulture at both scopes, so the toolkit runs on every commit
   instead of depending on a lead remembering it.

## G. Declared dependencies nothing imports (`just deps`)

`pandas` and `SimpleITK`. `docs/TOOLING.md` records that these are leads and never authority to
remove a package from the founder's design.

## H. Open rulings that are the founder's and cannot be built around

1. the expected correspondence **`e`** — hand-given, with author and date; the one thing the Helen
   Keller argument says must be supplied and cannot be derived
2. the **numeric abstention projection**, which he said resolves experientially after inspection
3. the **local structural normalisation** before the digits
4. the **laterality fallback** when the primary witness is absent
5. the conversation's **one-name merge** rule (`object-resolution-toolkit` 3.13)
6. the scope of the **"every decision reads a relation"** clause against `Fracture` and `Contusion`,
   which take a single bone
7. whether the `21f6b41` predicate code **stays, is rewired, or comes out**

---

## What this list is for

It is the input to a review, and it is the repair order. It is **not** a proposal: which of A–G is
repaired, and in what order, is the founder's call. The one thing it asserts is that the distance
between this repository and his standard is not cleanup — it is `relations` constructing, `vectors`
existing, `predicates` receiving real subjects, and `output` emitting.
