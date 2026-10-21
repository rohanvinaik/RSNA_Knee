# RSNA Knee: anatomical reasoning and individual-case recall

A classical-AI computer-vision pipeline grounded in **What an \<Object> Is**. Complementary measurements describe anatomical objects; their physical relations constrain recognition. Each object has one HDC representation across its available lenses, views, directions and scales. Independent normal and condition-presentation cases remain individual precedents.

The high-resolution anatomical pipeline supplies bootstrap examples. **Production starts with raw-image squints and case recall.** It locates current-study anatomy, reasons over the recalled object states, and requests a bounded higher-fidelity reading only for a question still open. It does not reconstruct the whole knee before deciding whether reconstruction was needed.

Read [Rohan's latest production explanation](docs/conversations/2026-10-21-ternary-buckets-and-squint-orchestration.md), [the original conversation](docs/conversations/2026-10-13-the-thesis.md), and [the theory](docs/THEORY_OF_THE_CASE.md). [FULL_BUILD_PLAN §0](docs/FULL_BUILD_PLAN.md#0-grounding-every-session-start-and-every-compaction) gives the grounding sequence; §13 points to the sole current task packet. The approved production design and interfaces are [AI_DIAGNOSTIC_DESIGN.md](docs/AI_DIAGNOSTIC_DESIGN.md) and [SQUINT_PRODUCTION_CONTRACT.md](docs/SQUINT_PRODUCTION_CONTRACT.md).

## Setup and operation

```sh
uv sync
export PYTHONPATH="$PWD/src"
.venv/bin/python scripts/run_interiors.py --help
```

The [squint run guide](docs/SQUINT_RUN_GUIDE.md) gives bootstrap compilation, inference, retained evidence, memory growth and private Kaggle deployment instructions. Memory is immutable and loaded once. Each active worker finishes and releases one study; decoded arrays do not accumulate across the cohort.

Compile the existing 58 bootstrap products into a fresh memory:

```sh
.venv/bin/python scripts/run_interiors.py \
  --labeled --root data/raw --workers 4 --diagnostic-mode teach \
  --squint-bootstrap-products data/readings/hdc-20261020/cohort/attempt-1/encoding \
  --diagnostic-memory /absolute/new/squint-memory \
  --diagnostic-output /absolute/new/bootstrap-receipt
```

Run the competition operation with that memory and a fresh output directory:

```sh
.venv/bin/python scripts/run_interiors.py \
  --split test --root data/raw --workers 4 --diagnostic-mode infer \
  --diagnostic-memory /absolute/existing/squint-memory \
  --diagnostic-submission-template data/raw/sample_submission.csv \
  --diagnostic-output /absolute/new/inference
```

The `knee.squint-memory/v1` manifest selects the fast route. Outputs retain located object profiles/regions, per-case comparisons, categorical findings and continuous rankings, with the official template's exact UIDs and twelve columns. Missing evidence stays unknown; disagreement stays visible. The new production policy emits neither hard zero nor hard one. Calls, reports and cohort labels do not become image features or teach during inference.

The 58 existing H5 products are teaching sources, not a claim that every object was observed in every study. The compiler retains usable addressed evidence and records coverage. New report-confirmed cases enter a later memory revision; recalled answers cannot label themselves.

## Efficiency and competition requirements

Anatomy narrows the work; shared producers avoid repetition; exact count-space HDC avoids dense per-pixel hypervectors. Useful priors need not be perfect. Performance figures are information about the implementation, never anatomical tuning targets.

[FULL_BUILD_PLAN §16.9](docs/FULL_BUILD_PLAN.md#169-competition-resource-envelope-w8b-storage-closure-and-w10-verification) owns the source-backed deployment envelope:

- At most **nine hours**, with **internet disabled**.
- Documented CPU route: **four cores, 30 GB RAM**, with **20 GB saved output** in `/kaggle/working`. Recheck the chosen runtime; scratch has its own session lifetime and measured quota.
- **W8b verifies storage closure**: required final object information, original values, addresses and provenance survive release of consumed intermediates.
- **W10 verifies the complete operation**: startup, decoding, location, recall, refinement, worker/queue memory and output, plus capacity for later stages. Measured public-study workload and hidden-scale projections remain separate.

The private Kaggle wrapper copies production source to local disk, installs the verified offline CPython 3.13 dependency closure, uses four study workers and writes `/kaggle/working/submission.csv`. The same source runs locally. A private dry run does not submit to the competition. Its actual results and remaining checks belong to [the current packet](docs/work/current/README.md), not a historical microbenchmark.

## Reference tools, images and exact products

High-resolution development remains available through the same entry point:

```sh
.venv/bin/python scripts/run_interiors.py --study-uid <UID> --root <data-root> --workers 1 --draw --run <new-interiors> --main-run <new-main-slices>
```

Drawing is optional and off in competition. `--competition-output` builds verified self-contained H5 object products before releasing consumed intermediates. Retained pixel supports preserve native, inherited and projected provenance; none silently claims a measured 3D volume.

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

`archive/` and `archive2/` are outside the active project and remain unread unless Rohan requests them.
