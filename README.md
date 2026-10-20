# RSNA Knee: anatomical object recognition

This is a classical-AI computer-vision pipeline grounded in **What an \<Object> Is**. Complementary
lossy measurements describe knee structures; anatomical relations combine those readings into named
objects and one physical knee map. Cheap squint views and known neighbours narrow expensive native
questions. Each useful value is computed once at its valid scope and shared with its consumers.

The anatomical path reports each object's identity with its addressed pixel supports. The diagnostic
memory path stores individual image cases with independent signed calls, then compares compatible
HDC descriptions over each question's declared banks. Normal and damaged cases remain distinct
precedents; no class prototype replaces them. Read [the original conversation](docs/conversations/2026-10-13-the-thesis.md) and
[the theory](docs/THEORY_OF_THE_CASE.md) before proposing changes. Follow
[FULL_BUILD_PLAN §0](docs/FULL_BUILD_PLAN.md#0-grounding-every-session-start-and-every-compaction)
for the complete grounding sequence. The plan's §13 points to the sole current task packet.

## Production requirements

Efficiency and correctness are built together: use anatomical priors and selected native views before
heavy computation, share source-owned measurements, and compile/fuse meaningful residual work with
reference checks. Useful priors need not be perfect. Performance figures never define anatomy.

Finish each study's configured output, then release its decoded images, derived arrays and caches.
Parallel execution bounds submitted and waiting results with the active worker count; completed
studies' working data do not accumulate across the cohort. Retained pixel supports remain addressable
for downstream consumers. Rohan's [competition retention decision](docs/conversations/2026-10-20-competition-object-retention.md)
requires complete final object pixel/HDC outputs, measured values and necessary provenance; consumed
intermediate files can be released after verified final publication. Development retains diagnostic
intermediates. The final diagnostic layer will run before that study's completed boundary.

[The binding competition envelope is FULL_BUILD_PLAN §16.9](docs/FULL_BUILD_PLAN.md#169-competition-resource-envelope-w8b-storage-closure-and-w10-verification):

- Competition notebook: **at most 9 hours**, **internet disabled**.
- Documented CPU route: **4 cores, 30 GB RAM**; saved output in `/kaggle/working`: **20 GB total**.
  Scratch has a separate measured quota and session lifetime. Recheck the selected environment;
  the plan includes GPU-route differences and the official sources.
- **W8b must implement and verify storage closure**, preserving every required reading, decision,
  address and reconstruction contract. Moving durable evidence into disposable scratch is insufficient.
- **W10 must verify the integrated compute envelope**: startup/JIT, decoding, recognition, worker/queue
  memory, IPC, hashing/compression and output. Distinguish target-environment measurements from
  projections for the approximately 1,300-study hidden workload and account for capacity left for
  later stages. One proof study or kernel replay does not establish competition fit.

These are deployment limits, not tunable recognition thresholds. Read §§1.3 and 16.6–16.9 of the plan
and [the build workflow](docs/work/current/BUILD_WORKFLOWS.md) when constructing or reviewing any family.

## Run and verify

Use the locked project environment (`uv sync`). One production entry point serves every mode:

```bash
.venv/bin/python scripts/run_interiors.py --study-uid <uid> --root <data-root> --workers 1 --run <new-interiors-dir> --main-run <new-main-dir>
.venv/bin/python scripts/run_interiors.py --labeled --root <data-root> --workers 2 --run <new-interiors-dir> --main-run <new-main-dir>
.venv/bin/python scripts/run_interiors.py --split test --root <data-root> --workers 1 --run <new-interiors-dir> --main-run <new-main-dir>
bash scripts/ci_local.sh
```

Competition retention uses the same entry point with fresh, mutually disjoint owned output directories:

```bash
.venv/bin/python scripts/run_interiors.py --split test --root <data-root> --workers 2 --competition-output --run <fresh-scratch-interiors> --main-run <fresh-scratch-main> --encoding-run <fresh-retained-objects>
```

`--competition-output` implies the built-in exact H5 encoder and rejects drawing/custom declarations.
It retains the complete object support/value/HDC product, verifies every saved array through the public
reader, stages a compact object receipt in the encoding directory, then releases that study's consumed
intermediate files. Missing dependencies or failed verification prevent cleanup. Previous runs and raw
studies are untouched. The object table distinguishes active final-product references from historical
source provenance. The implementation is exercised separately from W8b/W10 quota/capacity acceptance;
the current packet records those measured results and remaining checks.

Drawing is development-only: add `--draw` to inspect native evidence; production leaves it off.
Saved array bundles use lossless `.npz.xz` archives. Use `knee.array_archive.open_arrays` to read
them (it also reads earlier `.npz` files); plain `numpy.load` cannot open the outer XZ stream.
Receipts retain array digests; archives retain original dtypes and shapes, and object observations address
their actual saved support. The reader decompresses one archive at a time into a bounded memory
spool, spilling larger archives to temporary storage and releasing it on close.
Compare saved receipts with `scripts/compare_receipts.py` under the plan's equivalence/change rules.
Receipt and study-map metadata use standard lossless `.json.xz` sidecars; `knee.json_store.load_json`
accepts both these and legacy `.json` paths. No-draw runs stage recoverable per-study metadata and
publish each aggregate receipt once, keeping completed image data out of the coordinator.
Drawing retains immediate publication. [The object-output guide](docs/OBJECT_OUTPUT.md) explains
the native, inherited and projected pixel addresses and includes a verified saved-artifact example.
The [offline runtime instructions](scripts/offline_runtime/README.md) package the same entry point
with locked production dependencies and provide source-pinned, constrained Linux verification.
The CI gate, ledger, Vulture, recorded-kernel benchmarks and CodSpeed complement native-image and
whole-run acceptance. Their passing does not establish complete anatomical coverage or resource fit.

The public [hosted SonarCloud project](https://sonarcloud.io/project/overview?id=rohanvinaik_RSNA_Knee)
uses the supplied [SonarQube workflow](.github/workflows/build.yml), the `SONAR_TOKEN` repository secret
and the `sonar-project.properties` production scope. Cloud automatic analysis is off to avoid duplicate
analysis. The pinned local/Actions gate remains; see [setup and verification](docs/SONARCLOUD.md).
Its visibility follows the author's explicit public-release decision; the complete production scope remains included.

The same command optionally encodes retained object readings with
`--encode-objects --encoding-run <new-encoding-dir>`, or an explicit
`--encoding-spec <declaration.json> --encoding-run <new-encoding-dir>`. The declaration
names banks, measurements, references and source addresses. Ordinary planes, full-resolution
packed fibula regions, posterior physical traces, slice profiles, coarse grids and sampled
joint readings share the exact Hadamard/count representation;
available acquisition context is inherited by each addressed place. Unread facets remain silent,
and measured numeric values without a supported reference remain named `missing_reference`.

An explicit `"storage": "h5"` in that declaration writes one H5 encoding product.
The built-in declaration selects H5's lossless hybrid row-predicted byte encoding (schema v5). Every original
array name, dtype, shape and decoded byte remains reconstructible; legacy products remain readable.
Authored definition context and measured supports have distinct typed roles, with per-object
ownership links retaining actual source/acquisition coordinates. These links assert no volume.
Production environments need the locked `jit` and `hdc` extras
(`uv sync --no-dev --extra jit --extra hdc`); development
installs already include its storage dependency. `knee.encoding.product.open_product` reads either
H5 or the default lossless JSON/XZ + NPZ/XZ product and verifies arrays lazily. Original measurement
values remain retained at their recognition-artifact addresses in development. Competition output
must carry all necessary object supports/values itself before those intermediate files are released. See [the exact encoding contract](docs/HDC_ENCODING.md).
The MRI-specific healthy profiles and complete spatial ownership/depth representation are still
under construction; the current proof and remaining work are recorded in the plan's live packet.

## Governing documents

The same production command now has explicit `--diagnostic-mode teach`, `infer`, and `capacity`
routes. Select `--diagnostic-products` for retained full descriptions or `--diagnostic-inputs` for
declared acquired-image regions; the latter reads addressed DICOM frames without running full
anatomical reconstruction. The normal `--study-uid`, `--labeled` and `--split test` selectors also
work with diagnostic mode: this full reference route runs recognition and encoding one study at a
time, retains its complete verified product under the diagnostic output's `objects/`, and releases
consumed reconstruction files. `--diagnostic-cases` imports explicitly attributed canonical or
composed-profile calls. `--diagnostic-submission-template` writes an exactly template-ordered
submission using the built-in symbolic/HDC readout: warranted decisions emit 1/0 and uncertainty
retains a graded relative case-resemblance value. Original conflicts, missing evidence and exact
comparison terms remain saved. An optional `--diagnostic-readout module:callable` overrides that
versioned numeric policy. Retained diagnostic source manifests use lossless `.json.xz`, preserving
the canonical metadata and exact arrays; the public reader also accepts legacy plain JSON.
The [diagnostic run guide](docs/DIAGNOSTIC_RUN_GUIDE.md) gives the input
schemas, immutable memory workflow, question declarations, source evidence and failure states.
Capacity mode excludes every case from the queried study. Missing references, silence, disagreement
and unknown trust remain explicit; the graded MVP readout is not a calibrated clinical probability.
Its versioned arithmetic and endpoint contract are in
[AI_DIAGNOSTIC_DESIGN §16](docs/AI_DIAGNOSTIC_DESIGN.md#16-symbolic-decisions-and-graded-uncertainty-implemented-mvp-readout).
MRI reference bindings, justified recall bands and training policy retain their separately
declared design and source requirements.

With an existing taught memory and a fresh output directory, the complete raw-study MVP run is:

```bash
.venv/bin/python scripts/run_interiors.py --split test --root <data-root> --workers 1 --diagnostic-mode infer --diagnostic-memory <immutable-memory-dir> --diagnostic-submission-template <data-root>/sample_submission.csv --diagnostic-output <fresh-diagnostic-dir>
```

This writes `<fresh-diagnostic-dir>/submission.csv`, per-study decision evidence and complete
object products. The offline notebook places the validated CSV at `/kaggle/working/submission.csv`.
The generated route runs full recognition serially; it is not the future automatic cheap-routing path.

`scripts/package_kaggle.py` packages the current production source and immutable memory into
a hash-verified dataset and offline notebook invoking that same runner. It accepts a supplied
Linux wheelhouse and requirements; without them the notebook-image dependencies remain unverified.
It does not upload or submit anything. This packaging capacity and the full reference route do not
establish that the complete hidden workload fits the competition's runtime/storage envelope.

- [AGENTS.md](AGENTS.md): resident project instructions; [CLAUDE.md](CLAUDE.md) imports them and the grounding documents.
- [FULL_BUILD_PLAN.md](docs/FULL_BUILD_PLAN.md): requirements, contracts, ordered work and completion rules.
- [BUILD_WORKFLOWS.md](docs/work/current/BUILD_WORKFLOWS.md): worker routing, verification and integration.
- [OBJECTS_AND_CONDITIONS.md](docs/OBJECTS_AND_CONDITIONS.md): anatomical domain descriptions.
- [RESOLVING_THE_PARTS.md](docs/RESOLVING_THE_PARTS.md): each part's views and complementary measurements.
- [HDC_ENCODING.md](docs/HDC_ENCODING.md): exact representation, source addressing, silence and explicit reference contracts.

`archive/` and `archive2/` are outside the active project and remain unread unless Rohan requests them.
