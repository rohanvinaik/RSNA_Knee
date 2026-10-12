# The current pipeline route

This is the interface map, reconciled 2026-10-12 against `knee.pipeline.run_study` and
`ROUTE`. Intent is in [OBJECT_MODEL.md](OBJECT_MODEL.md) and
[PIPELINE_AS_OBJECT.md](PIPELINE_AS_OBJECT.md); the workflow is in [SPINE.md](SPINE.md).
The original 2026-10-10 Figure 8 route is [archived](../archive/docs/planning/20261012/PIPELINE.md).

## Nine stages, ten operations

| route package | intended output | current connection to inspect |
|---|---|---|
| `study` | acquired series, slices and LPS geometry at stored fidelity | `read_study` → `StudyRun.study` |
| `collapse` | regime, physical field and squint | `read_regime`; optional `measure_series` |
| `lenses` | per-place ternary readings per acquisition, silence distinct | `read_lenses` → `SeriesRun.lenses`; candidate native-volume map, `normalisation: none` |
| `objects` | indexed extents, boundaries and role-supported border refinement | optional measurement packet → interiors and boundary census; later same-orientation conversation |
| `relations` | constructed interstices, their extents, walls, fill and contents | shell → `SeriesRun.relations`; sampled dark-bounded pairings retained separately as `SeriesRun.pairings` |
| `ownership` | claims, disputes and unassigned material; residual rounds | `read_ownership` → `SeriesRun.ownership`; partition exists, residual scheduler remains owed |
| `vectors` | bundles as counts over banks, unavailable banks named | route declaration and package; not called by `run_study` |
| `predicates` | twelve subject-scoped named decisions | `read_findings` → `StudyRun.findings`; current implementation emits twelve abstentions |
| `output` | competition-shaped confidences with a companion record | route declaration and package; no numeric submission projection yet |

`field` means `collapse`; `bundles` means `vectors`. Border refinement is work inside
`objects`, not a tenth stage. `ROUTE` is a declaration of stage standing, not an execution trace.
`StudyRun.reached` is a coarse marker and currently does not advance for every invoked stage.
Use source/callers, returned records, ledger events and gallery outcomes together.

## The real entry point and drawing edge

`just analyze-objects` calls `workbench.measure.object_analysis.main`, which calls
`run_study`, saves source-linked arrays, checkpoints and a receipt, then calls
`workbench.render.all_frames.draw_all` by default. It requires explicit physical settings;
conversation is on by default and requires `--prominence-mm`. `--no-conversation` and
`--no-pictures` are explicit execution switches. See [TOOLING.md](TOOLING.md).

The joiner collects eight drawing adapters and lists every route stage either through a
drawing outcome or `no_drawer`. Adapter presence, successful drawing and stage acceptance
are different facts. The latest [dated run](chapters/02-collapse/measurements/documentation-reconciliation-20261012.md)
records seven drawings, a packet failure for the missing probe fraction, and no joined
drawer for collapse, vectors or output. It does not certify full symbolic capacity.

## Values, layers and scope

The route moves retained records; measurements, pure named-code decisions and orchestration
remain separate. `compute` and `telemetry` support the route; `pictures` arranges its values.
Production imports no drawing or development observer. Memory, expert, agencies and record
are diagnosis-stage responsibilities, not recall in the object parse. §12's tracking/following/division
operations are outside this project's recognition scope.

Touching-pair census, sampled pairs across dark and complete interstices are three different
records. The current shell does not consume sampled pairings to construct an extent; predicates
currently count ownership/relation status and do not select subjects from the retained pairs.
Those are open wiring/contract obligations, not evidence that the available pairing record is empty.

The shell’s retained `why` message still broadly says no record names which objects face
across a border. That wording predates the sampled-pair candidate and is not an inventory
of all available evidence: this run retains both touching pairs and sampled dark pairs.
Complete interstice construction and its consumption remain absent. This reconciliation
documents the stale message without changing domain behavior or its source digest.
