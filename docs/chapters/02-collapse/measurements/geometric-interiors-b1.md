# B1: surrounding-field information, interiors and native border evidence

Recorded 2026-10-11. This is an evidence index for a particular run, not a
handwritten current-status report. Recompute standing with:

```sh
just interiors-status data/measurements/object-interiors-b1-v1
```

Intent: [the continuing contract](../object-resolution-contract.md). The
founder's latest same-knee / general-conversation teaching and the live cell
trace are in [the conversation reading](../readings/same-knee-conversation-codex.md).
The [Fable workshop resolution](../readings/b1-workshop-resolution.md) records
the lead's independent reading and the checked conceptual critique; its scope
is a workshop, not a source audit of this later code snapshot.

## Production route and exact run

`knee.pipeline.run_study` consumes the Chapter 1 study and already decoded
series. Its existing `read_regime` supplies the split to
`collapse.analysis.measure_series → interiors.read_interiors`. The returned
record is observed by the writer, Hamilton, SAME and renderer. There is no
second workbench segmentation or decoder producing these pictures.

The full corpus invocation was:

```sh
just analyze-objects --tile-mm 3 --span-mm 3 --samples 13 --axis superior --backend jit --prominence-mm 3 --out data/measurements/object-interiors-b1-v1
just same-interiors data/measurements/object-interiors-b1-v1
```

Run artifacts:

- `data/measurements/object-interiors-b1-v1/receipt.json`: requests, source
  snapshot, writer/serializer identities, all saved-array descriptions,
  original planes and source lineage, metric guard/error records, native
  profiles, named trace outcomes, counts and returned bytes.
- `.../checkpoints/<study_uid>.json`: atomic per-study evidence for resumption.
- `.../interiors-same.json` and `interiors-same.log`: exact saved/reference/JIT
  comparisons of every B1 array, named outcome and declared scalar, with
  environment, receipt, verifier and artifact identities.
- `.../interiors-status.json`: computed current/stale checks across those links.
- `data/measurements/object-interiors-b1-corpus.log`: complete production log.

The run recorded 58 studies / 336 series and no failed studies. All 336 carried
a B1 reading, including the two whose separately requested patient-axis profile
was unavailable. The saved geometric outcomes were 333 `measured` and three
`no_interior_seeds`. All 1,945 proposed territories were retained. These are
the run's counts, not anatomical accuracy scores. SAME exercised 38,596,038
native boundary samples. A later source/environment change can make this
snapshot stale; the command above determines that, not this paragraph.

## The staged visual series

Canonical output: `data/pictures/object-toolkit/interiors-b1/`.

1. `01-surrounding-field.png`: original signal and the actual saved red
   low-signal reading; missing support remains magenta.
2. `02-interiors.png`: distance from the measured surrounding constraints,
   cyan prominence markers, and every colored proposed interior with local IDs.
3. `03-native-traces.png`: original native territory edges beside observed
   dark-band midpoint traces. Cyan is the complete unique bounded interval;
   yellow is open, orange multiple, magenta missing/clipped.
4. `series.png` and individual six-column series: the complete progression for
   each selected view, preserving the native signal beside its readings.

`manifest.json` binds the receipt, saved artifacts, renderer identity and every
PNG digest. Rendering checks every saved-array descriptor before drawing.
Stage rows identify view, fluid/fat flags and slice. The renderer can be run as:

```sh
just render-interiors data/measurements/object-interiors-b1-v1 --study-uid 1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149
```

The renderer supplies Matplotlib in an ad hoc environment with `--no-sync`, so
drawing saved arrays does not resynchronize the production environment. During
this run a network-disabled attempt to resynchronize needed an uncached Z3
wheel; the successful cached `--no-sync --offline` rendering is recorded in
`.../render.log`. No production dependency was added for drawing.

Spatial inspection: the borders of the main structures are legible in the
native traces; artificial territory divisions remain visible with their actual
support outcomes. The founder identified useful cross-resolution between the
two coronal weightings. His example illustrates why retaining the adjacent
structure and the unresolved division gives the next conversation information.
It must not become a rule tied to those colors or IDs. These are geometric
readings from which the subsequent build resolves objects and ownership.

## Engineering evidence

- Intent/property cases: `tests/knee/collapse/test_interiors.py`,
  `test_border_codes.py`, and `tests/knee/test_pipeline_interiors.py`; empty,
  nonfinite, invalid settings, disconnected interiors, frame clipping, multiple
  bands, immutable samples and positive affine intensity invariance are covered.
- Gate: `.../gate.log` names its exact collected tests and outcomes. The first
  completed B1 gate recorded 265 passed / one platform-specific skip; consult
  the final log for current test execution.
- `.../crosshair.log`: with `--report_all`, CrossHair reported the two PEP 316
  postconditions confirmed over its paths. This applies to those predicates,
  not every property of the geometric algorithm.
- Detective: `.detective/reports/converge_border_code.txt` and the associated
  full logs report `border_code` complete modulo two unproven-equivalent
  mutants, 61/63 killed. Do not call those two proven equivalent or claim that
  the numeric array kernels are automatically mutant-pinned. The explicit
  scalar inputs' advisory style region was read and recorded as `judged_leave`;
  `.detective/reports/plan_src_knee_collapse_border_codes_py__border_code.txt`
  records that choice.
- Hamilton: `.../graph.svg`, `graph.execution.json`, `graph.log` come from
  `just graph-interiors`. One production study run feeds measurements,
  `interior_counts` and `work_counts`; the graph validates and executes those
  consumers. Its counted work is structural evidence, not anatomical warrant.
- Import Linter checks the production/development direction. Deptry's
  `.../deps.log` retains two existing unused declarations (`pandas`,
  `SimpleITK`); they were not removed or suppressed to make a green report.
  The adjacent SAME verifier module is correctly classified as first-party.

## Telemetry through the same entry

Original artifacts:
`data/measurements/object-interiors-b1-calls.prof`,
`object-interiors-b1-memory.bin`, their logs and representative-study receipts.
Readable reports: `data/measurements/object-interiors-b1-telemetry/`.

- `pstats-top30-cumulative.txt` and `pstats-knee-collapse-functions.json`:
  cProfile's call statistics, including all 73 recorded collapse functions.
  In that instrumented five-series run, `read_interiors` was called five times,
  with 0.883 s cumulative time; native sampling was called ten times. These are
  observations of that run, not a paired speed claim.
- `memray-stats.log` / `.json`: 315,621,850 B peak tracked allocation in the
  representative run, distinct from RSS. Total bytes allocated are cumulative
  churn, not live memory. The statistics include existing regime/decoding work.
- `memray-flamegraph.html` / `.log`: offline graph. Memray reports missing Python
  interpreter symbols, so native stack attribution is qualified accordingly.

The repeated custom sampler uses the reference/Numba twin; distance and
morphology are library-shaped NumPy/SciPy/scikit-image work. There is no measured
crossover here warranting a new Rust/C kernel. Linux/Kaggle remains its own
deployment check; this run establishes the declared same-environment behavior.

## Continuing build

OpenSpec tasks 3.6 onward cover the general same-knee conversation and supported
chain refinement. Follow the thesis and live cell route, work out the operation
with Fable, and then show production before / exchanged constraints / refined
readings images. Keep original and refined readings, disagreements and missing
support. The founder's example guides inspection; it does not replace either
oracle or define a bespoke production shortcut.
