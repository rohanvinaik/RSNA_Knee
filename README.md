# RSNA Knee: anatomical reasoning and individual-case recall

A classical-AI computer-vision pipeline grounded in **What an \<Object> Is**. Complementary measurements describe anatomical objects; their physical relations constrain recognition. Each object has one HDC representation across its available lenses, views, directions and scales. Independent normal and condition-presentation cases remain individual precedents.

**Current development objective: local bootstrap, corpus growth and classical AI training.**
We are **hand-building the corpus**: recognition tools help isolate anatomical examples,
normal and diseased, whose reviewed bundles become K-lines. A perfect or complete automatic
recognition solution on the 58 teaching studies is not a prerequisite for training the AI.
The teaching labels supply normal examples too: correctly identified objects not implicated by
a study's positive conditions belong in the normal corpus, even when that knee has other injuries.
Visually confirm or correct recognizable examples, add their signed HDC cases to the K-line memory,
use that memory and anatomy to find more, then train the designed Minsky/Winston agencies from
the growing corpus and sourced experiences. This preparation is not a Kaggle deployment task.
The full corpus is on an SSD being extracted, and three computers are available for training math.
[FULL_BUILD_PLAN §18.1](docs/FULL_BUILD_PLAN.md#181-current-phase-local-bootstrap-and-classical-ai-training)
defines the phase boundary; [the active packet](docs/work/current/README.md) records actual progress.

The [train-ready completion handoff](docs/TRAIN_READY_COMPLETION.md) gives the verified gaps,
exact implementation/test requirements and parallel work split. It preserves balanced-ternary
meaning and distinguishes hand-grounded teaching readback from the subsequent classical learning loop.

**Hand-defined teaching references:** [normal/diagnosed picture pairs for all twelve questions](docs/GROUNDED_TEACHING.md),
with [authored categories, measured cases and replay instructions](docs/teaching/README.md).
These establish the explicit starting reference before scaling; teaching replay is distinct from
held-out diagnostic performance. The existing signed parent memory is preserved.

The high-resolution anatomical pipeline supplies bootstrap examples. **Production starts with raw-image squints and case recall.** It locates current-study anatomy, reasons over the recalled object states, and requests a bounded higher-fidelity reading only for a question still open. It does not reconstruct the whole knee before deciding whether reconstruction was needed.

Read [Rohan's latest production explanation](docs/conversations/2026-10-21-ternary-buckets-and-squint-orchestration.md), [the original conversation](docs/conversations/2026-10-13-the-thesis.md), and [the theory](docs/THEORY_OF_THE_CASE.md). [FULL_BUILD_PLAN §0](docs/FULL_BUILD_PLAN.md#0-grounding-every-session-start-and-every-compaction) gives the grounding sequence; §13 points to the sole current task packet. The approved production design and interfaces are [AI_DIAGNOSTIC_DESIGN.md](docs/AI_DIAGNOSTIC_DESIGN.md) and [SQUINT_PRODUCTION_CONTRACT.md](docs/SQUINT_PRODUCTION_CONTRACT.md).

The [full classical-AI design](docs/CLASSICAL_AI_BUILD_DESIGN.md) connects bootstrap recognition,
corpus/training-data construction, agency learning and runtime memory. K-lines serve both initial
recognition and the continuing recall of interpretations/procedures. Confirmed negative examples
are active teaching information; unresolved calls remain silent. Populating the corpus enables the
classical learning process and does not exhaust it. Implementation status remains in the current packet.

## How the complete operation fits together

1. **Bootstrap tools supply candidates.** The existing high-resolution results retain object supports,
   full HDC descriptions and raw source addresses. Automatic object names remain proposals until called.
2. **Visual calls establish the starting memory.** Keep every warranted positive, negative and
   alternative identity at the scope actually established. Useful messy examples are welcome; an
   unasserted view is not a negative. The full and cheap descriptions coexist within each case.
3. **Recognition grows the corpus.** Squint the new study, constrain candidates with its own anatomy,
   and hear both signed sides through the joint available views. Automated new-case admission requires
   confident identity plus affirmative applicable anatomical support and no known contradiction.
   Unknown anatomy alone leaves a proposal; it neither admits nor rejects it. An anatomical pass records
   where the candidate lies, not what tissue it is: plausible but wrong tissue meets the negative cases.
   Not every anatomical check, every view or a perfect outline is required. Each round reads a frozen
   parent memory and publishes a child retaining its signed cases, source scope and recognition lineage;
   the first round's admissions are inspected before its child becomes the next parent.
4. **Training develops the active classical system.** Work problems with that corpus and the available
   tools; retain what was expected, what was tried, the independently established outcome and any
   explanatory difference. Those experiences can add a case, refine or split a K-line's claim, establish
   a scoped censor, or associate a recalled situation with a useful procedure. The governing design
   supplies these mechanisms; filling buckets alone is not the whole training process, and no generic
   episode framework is a prerequisite for getting recognition to work.
5. **Production uses the resulting memory.** Current-study squints and anatomical relations cue
   individual cases and useful procedures. Their interpretations govern the condition questions;
   disagreement or missing evidence remains open. Only a named unresolved question earns a bounded
   additional reading. The run writes the twelve competition values and releases each completed study.

Object identity, object state and clinical diagnosis are distinct questions. A visual “not femur” is
not “no fracture”; a fracture-positive study does not label every bone fractured. Labels, reports and
independent clinical calls retain their actual scope. Recognition-derived examples retain their lineage
and never become independent confirmation of their own ancestry.

## Setup and operation

```sh
uv sync
export PYTHONPATH="$PWD/src"
.venv/bin/python scripts/run_interiors.py --help
```

The [squint run guide](docs/SQUINT_RUN_GUIDE.md) gives bootstrap compilation, inference, retained evidence, memory growth and private Kaggle deployment instructions. Memory is immutable and loaded once. Each active worker finishes and releases one study; decoded arrays do not accumulate across the cohort.

Compile the existing 58 bootstrap products into a fresh **candidate catalogue**:

```sh
.venv/bin/python scripts/run_interiors.py \
  --labeled --root data/raw --workers 4 --diagnostic-mode teach \
  --squint-bootstrap-products data/readings/hdc-20261020/cohort/attempt-1/encoding \
  --diagnostic-memory /absolute/new/candidate-catalogue \
  --diagnostic-output /absolute/new/bootstrap-receipt
```

Then use the [reviewed bootstrap guide](docs/OBJECT_BOOTSTRAP_GUIDE.md) to export the actual pictures,
record calls and publish a reviewed seed. Catalogue compilation is not visual approval of its cases.
The guide publishes signed identity teaching (positive, negative and alternative-identity cases at
their called views) and merges recorded calls from several reviewers without widening any call's scope.

Run the competition operation with an explicitly chosen published memory and a fresh output directory:

```sh
.venv/bin/python scripts/run_interiors.py \
  --split test --root data/raw --workers 4 --diagnostic-mode infer \
  --diagnostic-memory /absolute/existing/reviewed-memory \
  --diagnostic-submission-template data/raw/sample_submission.csv \
  --diagnostic-output /absolute/new/inference
```

The `knee.squint-memory/v1` manifest selects the fast route. Outputs retain located object profiles/regions, per-case comparisons, categorical findings and continuous rankings, with the official template's exact UIDs and twelve columns. Missing evidence stays unknown; disagreement stays visible. The new production policy emits neither hard zero nor hard one. Calls, reports and cohort labels do not become image features or teach during inference.

The 58 existing H5 products are candidate teaching sources, not a claim that every object was observed correctly in every study. The [reviewed object bootstrap guide](docs/OBJECT_BOOTSTRAP_GUIDE.md) exports actual native pictures and publishes correctly called object examples with their full and cheap profiles. Admit all correct candidates; rough borders are acceptable for categorization. Record the actual visual reviewer and the views whose identity was established. Object identity can grow by warranted recognition with anatomical checks; that does not manufacture an independent clinical diagnosis. New report-confirmed clinical calls enter a later memory revision at their stated scope.

The [run guide](docs/SQUINT_RUN_GUIDE.md) also gives the immutable teaching-round command, saved-evidence replay, and explicit retirement of independently reviewed bad teaching cases. A retired case remains preserved for inspection; its evidence cannot keep voting through a derived configuration.

The [run guide's integration boundary](docs/SQUINT_RUN_GUIDE.md#implementation-boundary-and-next-integration)
names the remaining connections. In particular, a saved `identity_recall` record is not yet evidence
that condition reasoning consumed that identity. Neither the current report-teaching command nor
the scratch identity-growth writer is a complete implementation of the classical training process.

## Efficiency and competition requirements

Anatomy narrows the work; shared producers avoid repetition; exact count-space HDC avoids dense per-pixel hypervectors. Useful priors need not be perfect. Performance figures are information about the implementation, never anatomical tuning targets.

Anatomy generates finite candidate windows before scoring; partial native bone planes can guide explicitly partial priors. Each study receives a bounded time share. Location keeps the cheap 10 mm reading and recalls from it first; only a named unresolved question earns its 2 mm reading at the same address, while direct and reference callers still pair upfront (the [run guide](docs/SQUINT_RUN_GUIDE.md#run-production-inference) names the counters). Prepared recall ships with the memory. A whole-condition case may decide only through comparisons that actually include its defining tissue. The [run guide](docs/SQUINT_RUN_GUIDE.md) documents the fully study-excluded capacity check and its per-condition report.

Partial normal evidence still speaks at its observed site. It can oppose an overlapping configuration claim without asserting that every possible site is normal. Context and explicitly restricted readings cannot acquire categorical authority through configuration bundling.

[FULL_BUILD_PLAN §16.9](docs/FULL_BUILD_PLAN.md#169-competition-resource-envelope-w8b-storage-closure-and-w10-verification) owns the source-backed deployment envelope:

- At most **nine hours**, with **internet disabled**.
- Documented CPU route: **four cores, 30 GB RAM**, with **20 GB saved output** in `/kaggle/working`. Recheck the chosen runtime; scratch has its own session lifetime and measured quota.
- **W8b verifies storage closure**: required final object information, original values, addresses and provenance survive release of consumed intermediates.
- **W10 verifies the complete operation**: startup, decoding, location, recall, refinement, worker/queue memory and output, plus capacity for later stages. Measured public-study workload and hidden-scale projections remain separate.

The private Kaggle wrapper requires the release's exact code-bundle and memory-manifest pins before inference. It copies production source to local disk, installs the verified offline CPython 3.13 dependency closure, gives the remaining notebook budget to the study allocator, uses four study workers and writes `/kaggle/working/submission.csv`. The same source runs locally. A private dry run does not submit to the competition. Its actual results and remaining checks belong to [the current packet](docs/work/current/README.md), not a historical microbenchmark.

## Reference tools, images and exact products

High-resolution development remains available through the same entry point:

```sh
.venv/bin/python scripts/run_interiors.py --study-uid <UID> --root <data-root> --workers 1 --draw --run <new-interiors> --main-run <new-main-slices>
```

Drawing is optional and off in competition. The development-only `scripts/squint_visual_capacity.py` pictures what a finished run's recall compared; the [run guide](docs/SQUINT_RUN_GUIDE.md#draw-what-recall-compared-development-only) gives its command. A drawing is never production, and a positive study label does not localize a lesion. `--competition-output` builds verified self-contained H5 object products before releasing consumed intermediates. Retained pixel supports preserve native, inherited and projected provenance; none silently claims a measured 3D volume.

See [OBJECT_OUTPUT.md](docs/OBJECT_OUTPUT.md) for addressed output, [HDC_ENCODING.md](docs/HDC_ENCODING.md) for the exact Hadamard/count representation, and [DIAGNOSTIC_RUN_GUIDE.md](docs/DIAGNOSTIC_RUN_GUIDE.md) for the older explicit full-product/recipe/reference tools. Those legacy routes and their readout remain available as reference behavior; they are not the new production default. Unread facets remain silent; source values without a declared interpretation remain named as such.

## Verification and engineering map

```sh
bash scripts/ci_local.sh
```

The gate includes intent tests, import contracts, Sonar correctness checks, Vulture and performance leads, recorded kernels and CodSpeed. Passing it does not alone establish anatomical or competition capacity. Use real images, source attribution and the real production entry point alongside it. [The Sonar setup](docs/SONARCLOUD.md) documents local/Actions checks and [the hosted project](https://sonarcloud.io/project/overview?id=rohanvinaik_RSNA_Knee).

- [AGENTS.md](AGENTS.md) and [CLAUDE.md](CLAUDE.md): resident instructions and grounding imports.
- [FULL_BUILD_PLAN.md](docs/FULL_BUILD_PLAN.md): requirements, contracts and current packet index.
- [BUILD_WORKFLOWS.md](docs/work/current/BUILD_WORKFLOWS.md): isolated worker ownership, review and integration.
- [OBJECTS_AND_CONDITIONS.md](docs/OBJECTS_AND_CONDITIONS.md): anatomical domain and condition scope.
- [RESOLVING_THE_PARTS.md](docs/RESOLVING_THE_PARTS.md): views and complementary measurements.
- [SQUINT_RUN_GUIDE.md](docs/SQUINT_RUN_GUIDE.md): the production and teaching workflow.
- [OpenSpec integration contract](openspec/changes/complete-signed-bootstrap-loop/proposal.md): the
  remaining signed-loop requirements, named scenarios and parallel tasks; validated planning is not
  completed implementation.
- [Two-sign boundary tests](tests/test_bootstrap_contract_intent.py) and
  [status intent tests](tests/test_anatomical_status_intent.py): executable intent at the
  existing interfaces. Future admission/growth/consumer scenarios remain in OpenSpec until integrated.

`archive/` and `archive2/` are outside the active project and remain unread unless Rohan requests them.

For the current hand-built corpus task, see [the teaching workflow](docs/GROUNDED_RECOGNITION.md):
actual images → reviewed anatomical and normal/diagnosed examples → measured bundles and signed
K-lines → bootstrap and train the Society of Mind. Automatic cohort recognition is not a gate
on this teaching operation.
The same guide gives the verified `prepare_squint_training.py` command to export reviewed
normal/condition object buckets and source-pinned procedure experiences from saved readings,
and `near_miss_report.py` to retain scoped corrections without inventing missing expectations.
The [current packet](docs/work/current/README.md) names the memory and verified state.
