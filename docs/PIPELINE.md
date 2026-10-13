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
| `study` | acquired series, slices and LPS geometry at stored fidelity | `read_study` → `Study`; the route records `study.produced`. Each `Series` keeps its per-slice codes, its walk indices (one rule, `knee.study.series.walk_indices`) and the walk's slices, which the study drawer arranges; each slice's thickness as stored; and its geometry's `orientation_spread` and `origin_spread_mm`, measured and never judged (task 7.12). `selected_slice` is the ONE rule for which slice the route reads a plane from, shared by the objects stage and the field's structural reading. `open_corpus` counts the corpus's shape from the tables (`knee.study.shape`, task 7.1a) |
| `collapse` | regime, physical field, squint and the field's structure | `read_regime` → `SeriesRun.regime`, which keeps the histogram its valley was read from and seats the moment-ratio channel count beside the robust one (task 7.1a); `read_structure` → `SeriesRun.structure` at the selected slice when an analysis names the tile (task 7.1): air by connection to the border, the leg closed, the axis and the way up from the header as named codes, the profile superior first with its dip, two basins seeded by the axis alone and the seam between them under the told sign, the darkest places and the largest bodies, every bar an argument on `AnalysisRequest.structure_bars`; `collapse.produced` carries both; `measure_series` reads `background_split` and records `collapse.consumed_by.objects` |
| `lenses` | per-place ternary readings per acquisition, silence distinct | `read_lenses` → `SeriesRun.lenses`; records `study.consumed_by.lenses`, `collapse.consumed_by.lenses`; one native-volume map per seated member against that series' own edges, drawn by `lens_frames` and consumed by the bundles, `place_codes_reference` Detective-COMPLETE under the plain contract form (tasks 2.3, 2.4); `normalisation: none`, because the local structural normalisation is the founder's, so the stage stays `partly` |
| `objects` | indexed extents, boundaries, native readings and the same-orientation conversation | `measure_series` → `SeriesRun.measurements`; `converse` → `SeriesRun.conversation` (per series, with `StudyRun.conversations` derived from it) |
| `relations` | constructed interstices, their extents, walls, fill and contents | `read_relations(interiors, spacing_rc)` → `SeriesRun.relations`, which reads and CARRIES `pairings` (the sample-supported pairs) and declares the `Interstice` record; `code` stays `construction_absent` because the extent is unbuilt |
| `ownership` | claims, disputes and unassigned material; residual rounds | `read_ownership_members(interiors, conversation)` → `SeriesRun.ownership`: one `OwnershipReading` per parse (solitary; concurrent and conditional where the conversation read the series) and the disagreement mask between the first two |
| `vectors` | bundles as counts over banks, unavailable banks named | `read_bundles(ownership, lenses, measurements, others, backend)` → `SeriesRun.bundles`; first increment built 2026-10-12 (task 6.7): per indexed extent of the selected plane, the banks `own_reading:<member>`, `lens_standing`, `came_out` (with the seeds row, task 3.2) and `through_plane:<uid>` (the slab rule's first consumer, through its array kernel: the reference applies the scalar `slab_code` per place and the Numba twin is pinned SAME to it, selected by the backend the request names and refused by name, tasks 7.10 and 7.15; the in-plane test is made in the nearest slice's own frame, task 7.12), with the conjunction, composite, dome-link and ring banks carried as named absences, and one gap fraction per other acquisition beside them (`slab_gaps`). Under the plain contract form `count_by_extent` converges 9/10, its last survivor unresolved by an engine crash, so the increment stands as a candidate (`measurements/remaining-gaps-20261012.md`) |
| `predicates` | twelve subject-scoped named decisions | `read_findings(series)` → `StudyRun.findings`; reads constructions by KIND from each relations record, the population from ownership, and the profiles from the bundles; twelve abstentions with the subjects and candidate counts it read |
| `output` | competition-shaped confidences with a companion record | `read_output(findings, projection)` → `StudyRun.output`: the declared index-to-column table, the companion record every run, rows refused with `projection_undeclared` |

`field` means `collapse`; `bundles` means `vectors`. Border refinement is work inside
`objects`, not a tenth stage. `ROUTE` is a declaration of stage standing, not an execution trace.
`StudyRun.attendance` names every stage with the code it returned for the study; `StudyRun.reached`
beside it is a telemetry scalar and nothing more. Use source/callers, returned records, ledger
events and gallery outcomes together.

## Telemetry: who records what

A stage records its own `<stage>.produced`. A CONSUMER records `<producer>.consumed_by.<consumer>`
inside itself at the point it reads the record, and only for a record handed over: a predecessor
handed over as None was not produced, and the consumer records nothing for it, naming the silence
in its own `why` (task 7.14, after the Codex re-review found a phantom conversation consumer with
the conversation off). The route records only for the two pinned multi-exit readers (`read_study`,
`read_regime`). `tests/knee/test_pipeline_composition.py` checks over the synthetic corpus that
every producer has a consumer and every consumer a producer, on the conversing route and on the
default route alike, and that the conversation precedes ownership and relations. Routes that log
consumption right after production — the shape the handoff's Codex reading found — are refused by
that test. `scripts/composition_check.py <run>` (`just composition`) makes the same reading of a
real run's receipt.

## The real entry point and drawing edge

`just analyze-objects` calls `workbench.measure.object_analysis.main`, which calls
`run_study`, saves source-linked arrays, checkpoints and a receipt, then calls
`workbench.render.all_frames.draw_all` per study and `workbench.render.corpus_frames.draw` once
per run over the receipt's corpus entry (task 7.1a), by default. It requires explicit physical
settings; conversation is on by default and requires `--prominence-mm`. `--no-conversation` and
`--no-pictures` are explicit execution switches. See [TOOLING.md](TOOLING.md). The study gallery
names where the superior end lies from the field's two saved header codes
(`knee.pictures.study.superior_end`, a named code over `SUPERIOR_ENDS`), and the field gallery
draws the structural reading's row beneath the squint and regime row for every series.

The writer saves, per series, the study's walk with its indices and per-slice codes, the whole
regime key (its histogram included), the structural reading's codes, levels, profile and tile
maps, every ownership member's masks and the disagreement mask, the pairing reading under its own
key, the relations record with its interstices and pairing code, and the bundles record with the
backend it asked for and the gap fractions; per study, the findings with the subjects, candidate
counts and profiles they read, the attendance roster and the output's companion record with the
refusal of its rows; per run, the corpus's shape and every declared compute contract beside the
ledger's counted work.

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
