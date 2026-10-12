# The current pipeline route

This is the interface map, reconciled 2026-10-12 against `knee.pipeline.run_study` and
`ROUTE` after the composition repairs (`openspec/changes/every-stage-renders/tasks.md` §6,
`specs/route-composition/spec.md`). Intent is in [OBJECT_MODEL.md](OBJECT_MODEL.md) and
[PIPELINE_AS_OBJECT.md](PIPELINE_AS_OBJECT.md); the workflow is in [SPINE.md](SPINE.md).
The original 2026-10-10 Figure 8 route is [archived](../archive/docs/planning/20261012/PIPELINE.md).

## Nine stages, in dependency order

`run_study` runs in four passes: every series is measured (study, collapse, lenses, objects); the
same-orientation acquisitions converse; every series is then partitioned, related and bundled
with the conversation's parse as an input; then the study's predicates and output run once.
Until 2026-10-12 the conversation ran LAST and its refined parse reached nothing.

| route package | intended output | current connection to inspect |
|---|---|---|
| `study` | acquired series, slices and LPS geometry at stored fidelity | `read_study` → `Study`; the route records `study.produced`. Each `Series` keeps its per-slice codes, its walk indices (one rule, `knee.study.series.walk_indices`) and the walk's slices, which the study drawer arranges |
| `collapse` | regime, physical field and squint | `read_regime` → `SeriesRun.regime`; `measure_series` reads `background_split` and records `collapse.consumed_by.objects` |
| `lenses` | per-place ternary readings per acquisition, silence distinct | `read_lenses` → `SeriesRun.lenses`; records `study.consumed_by.lenses`, `collapse.consumed_by.lenses`; candidate native-volume map, `normalisation: none` |
| `objects` | indexed extents, boundaries, native readings and the same-orientation conversation | `measure_series` → `SeriesRun.measurements`; `converse` → `SeriesRun.conversation` (per series, with `StudyRun.conversations` derived from it) |
| `relations` | constructed interstices, their extents, walls, fill and contents | `read_relations(interiors, spacing_rc)` → `SeriesRun.relations`, which reads and CARRIES `pairings` (the sample-supported pairs) and declares the `Interstice` record; `code` stays `construction_absent` because the extent is unbuilt |
| `ownership` | claims, disputes and unassigned material; residual rounds | `read_ownership_members(interiors, conversation)` → `SeriesRun.ownership`: one `OwnershipReading` per parse (solitary; concurrent and conditional where the conversation read the series) and the disagreement mask between the first two |
| `vectors` | bundles as counts over banks, unavailable banks named | `read_bundles(ownership, lenses, measurements, others)` → `SeriesRun.bundles`; first increment built 2026-10-12 (task 6.7): per indexed extent of the selected plane, the banks `own_reading:<member>`, `lens_standing`, `came_out` and `through_plane:<uid>` (the slab rule's first consumer), with the conjunction, composite, dome-link and ring banks carried as named absences. Its kernel `count_by_extent` is Detective-UNGATEABLE, so the increment stands as a candidate, like the native digits map |
| `predicates` | twelve subject-scoped named decisions | `read_findings(series)` → `StudyRun.findings`; reads constructions by KIND from each relations record, the population from ownership, and the profiles from the bundles; twelve abstentions with the subjects and candidate counts it read |
| `output` | competition-shaped confidences with a companion record | `read_output(findings, projection)` → `StudyRun.output`: the declared index-to-column table, the companion record every run, rows refused with `projection_undeclared` |

`field` means `collapse`; `bundles` means `vectors`. Border refinement is work inside
`objects`, not a tenth stage. `ROUTE` is a declaration of stage standing, not an execution trace.
`StudyRun.attendance` names every stage with the code it returned for the study; `StudyRun.reached`
beside it is a telemetry scalar and nothing more. Use source/callers, returned records, ledger
events and gallery outcomes together.

## Telemetry: who records what

A stage records its own `<stage>.produced`. A CONSUMER records `<producer>.consumed_by.<consumer>`
inside itself at the point it reads the record; the route records only for the two pinned
multi-exit readers (`read_study`, `read_regime`). `tests/knee/test_pipeline_composition.py` checks
over the synthetic corpus that every producer has a consumer and every consumer a producer, and
that the conversation precedes ownership and relations. Routes that log consumption right after
production — the shape the handoff's Codex reading found — are refused by that test.

## The real entry point and drawing edge

`just analyze-objects` calls `workbench.measure.object_analysis.main`, which calls
`run_study`, saves source-linked arrays, checkpoints and a receipt, then calls
`workbench.render.all_frames.draw_all` by default. It requires explicit physical settings;
conversation is on by default and requires `--prominence-mm`. `--no-conversation` and
`--no-pictures` are explicit execution switches. See [TOOLING.md](TOOLING.md).

The writer saves, per series, the study's walk with its indices and per-slice codes, every
ownership member's masks and the disagreement mask, the pairing reading under its own key, the
relations record with its interstices and pairing code, and the bundles record; per study, the
findings with the subjects, candidate counts and profiles they read, the attendance roster and the
output's companion record with the refusal of its rows.

## Values, layers and scope

The route moves retained records; measurements, pure named-code decisions and orchestration
remain separate. `compute` and `telemetry` support the route; `pictures` arranges its values.
Production imports no drawing or development observer. The disposition of `memory`, `expert`,
`agencies` and `record` is open and the founder's (`docs/HANDOFF_WIRING.md` §8). §12's
tracking/following/division operations are outside this project's recognition scope.

Touching-pair census, sampled pairs across dark and complete interstices are three different
records. Relations now carries the second; the third remains unconstructed, and the predicates
read the relations record's constructions by kind — none today — rather than a flag. Pairings
under the conversed parses are declared (task 6.3a) and not built.
