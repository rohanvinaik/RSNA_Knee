# Squint-first operation

The competition operation reads raw MRI series, locates anatomy in their cheap physical squints, recalls individual normal and condition-presentation cases, and writes twelve ranked values. Full anatomical reconstruction supplies bootstrap examples. It is not a required inference prefix.

The governing design is [AI_DIAGNOSTIC_DESIGN.md](AI_DIAGNOSTIC_DESIGN.md); the exact implementation interfaces are [SQUINT_PRODUCTION_CONTRACT.md](SQUINT_PRODUCTION_CONTRACT.md). Current acceptance evidence and pending work live only in [the current packet](work/current/README.md).

## Commands and what they exchange

A published memory and a completed run are read-only inputs to every later step. Each command writes to a fresh path of its own; only a teaching round rerun on the same inputs resumes its own root.

| Step | Command | Reads | Writes |
|---|---|---|---|
| Compile bootstrap memory | `scripts/run_interiors.py --diagnostic-mode teach`, or `scripts/compile_squint_memory.py` to choose the profile writer | `train.csv` and the raw studies under `--root`; the full H5 products | the memory directory (`manifest.json` and `recall-preparation.json.xz`) and a bootstrap receipt |
| Raw inference | `scripts/run_interiors.py --diagnostic-mode infer` | the memory, the raw studies and the official submission template | the diagnostics directory: `receipt.json`, `studies/<UID>.json.xz`, `recall-preparation.json.xz`, `submission.csv` |
| Held-out check | `scripts/run_interiors.py --diagnostic-mode capacity`, then `scripts/evaluate_squint_capacity.py` | a prepared memory, labelled raw studies and a template of exactly those UIDs; the labels only in the reporter | a run directory, then the capacity report (JSON and Markdown) |
| Reports for independent readers | `scripts/squint_report_teaching.py export` | `train.csv` | a reader batch of report text without label values |
| Teaching round | `scripts/squint_training_round.py` | a parent memory, a completed run, the report text of `train.csv` and independent call documents | a round root: `round.json`, the child `memory/` with its recall preparation, and `evaluation/` when asked |
| Package for Kaggle | `scripts/package_squint_kaggle.py` | a memory and the source tree | a staging directory: `dataset-metadata.json`, `runtime-bundle.tar` and `RUNTIME_MANIFEST.json` |

Paths below are placeholders. Every flag shown is one the script's own `--help` lists, and the focused tests under [Verify](#verify) go with these commands. Passing them measures neither diagnostic capacity nor the Kaggle route.

## Environment

From the repository root:

```sh
uv sync
export PYTHONPATH="$PWD/src"
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMBA_NUM_THREADS=1
.venv/bin/python -c 'import knee.diagnosis.squint_pipeline as p; print(p.__file__)'
.venv/bin/python scripts/run_interiors.py --help
```

The import must name this checkout. An isolated worker may reuse an interpreter, but must set its own `PYTHONPATH`; it must never run `uv sync` or auto-sync `uv run` against a shared environment.

## Compile bootstrap memory once

Use the existing complete H5 product directory and matching raw studies. All source object supports, identities and silence remain attributed. A product declaring an object without an observed support does not teach that object. The compiler does not rerun anatomy.

```sh
.venv/bin/python scripts/run_interiors.py \
  --labeled --root data/raw --workers 4 \
  --diagnostic-mode teach \
  --squint-bootstrap-products data/readings/hdc-20261020/cohort/attempt-1/encoding \
  --diagnostic-memory /absolute/new/memory-r1 \
  --diagnostic-output /absolute/new/bootstrap-receipt-r1
```

Both output directories must be fresh. Inspect the memory's `manifest.json` and the bootstrap receipt before inference. Cases remain individual, with paired exact full sparse records, coarse/finer profiles, acquisition identity, source windows, calibration and independent calls. Shared context/payload tables make the full profile readable offline. Preserve the immutable original H5 products for inspecting original pixels and arrays; production does not open them to recall cheap cases.

The teaching command publishes both object cases and role-qualified whole-condition configuration cases in that one immutable memory. No second manual memory-expansion step is required. The receipt distinguishes object, configuration and total case counts. Full and cheap descriptions coexist for each object; cheap queries do not fabricate full-only banks.

Bootstrap publication also saves `memory/recall-preparation.json.xz`, bound to the manifest, revision and exact case/call/profile/censor fingerprint. Production restores its runtime indices rather than recomputing the fixed pairwise comparisons. Preserve that sidecar when packaging the memory. For an existing memory, public `prepare_recall(memory)` and `save_memory(memory, new_path, prepared_recall=prepared)` publish a prepared revision without rereading anatomy. A stale or missing cache is reported as recomputed, never silently accepted.

A positive official label supplies the implicated object's condition presentation, without claiming that every contextual tissue is damaged. Only an object implicated by no positive label enters the normal bucket; blank conditions never become negative calls. Structural examples can carry no diagnostic call and still help locate anatomy.

The entry point's teach route compiles with the default `squint-v1` profile writer only. `scripts/compile_squint_memory.py` compiles the same bootstrap memory with a chosen writer and keeps a receipt. It is bootstrap tooling that production never imports:

```sh
.venv/bin/python scripts/compile_squint_memory.py \
  --root data/raw \
  --products data/readings/hdc-20261020/cohort/attempt-1/encoding \
  --memory /absolute/new/memory-r1 \
  --writer squint-v1 \
  --receipt /absolute/new/compile-receipt-r1.json
```

`--writer territory-v2` selects the territory writer, whose leg-map producer `--leg-maps module:callable` defaults to `knee.diagnosis.squint_leg:leg_maps`. `--study-uid UID [UID ...]` limits the compile to those studies (default: every fully labelled study), and `--io-workers` sets the I/O workers (default 8). The memory directory must be fresh, `--receipt` refuses an existing file, and one memory holds one writer: a territory memory never mixes with a `squint-v1` one. The receipt (`knee.squint-memory-compile/v1`) is printed, and written to `--receipt` when it is given.

## Run production inference

```sh
.venv/bin/python scripts/run_interiors.py \
  --split test --root data/raw --workers 4 \
  --diagnostic-mode infer \
  --diagnostic-memory /absolute/existing/memory-r1 \
  --diagnostic-submission-template data/raw/sample_submission.csv \
  --diagnostic-output /absolute/new/inference-r1
```

A `knee.squint-memory/v1` manifest selects this route before the reference producer is constructed. Do not pass `--draw`, reference product/input recipes, a label CSV, custom legacy trust/readout declarations, or `--competition-output` to this route. The same `--study-uid UID ...` selector runs selected raw studies; a supplied subset template must contain exactly those UIDs.

Each worker owns one study's decoded series. Squints and scan-local metric codes are shared by its object searches. Object profiles combine available views. A missing reading stays missing. An open question can request a bounded finer reading on a located source region; recall consumes the new banks. Already-read regions are shared across conditions. No open question triggers an automatic full-study reconstruction. The time budget stops discretionary refinement first; it never changes unknown into normal. The default operation budget is 30,000 seconds, with notebook output reserve beneath the nine-hour cap; use `--squint-time-limit SECONDS` to declare a different budget.

The locator proposes finite physical windows from anatomy before scoring them: bones first, then their dependents. Native selected bone planes constrain the current study's search. A partial reference can guide an explicitly partial prior; missing directions remain guided by the weak leg-frame/atlas expectation. It never becomes an observed complete point. Unknown knee side retains both hypotheses. Each proposed window addresses one acquired slice; only bounded coarse finalists are kept, at the cheap reading they were located on. The operation divides remaining time among studies. A study not examined before its budget expires retains twelve open results and an explicit `not_examined_budget` status, not twelve negative findings.

Production locates on the cheap 10 mm reading and recalls from it first. Only a named unresolved question earns its object's 2 mm reading at the same address: read once, shared by later questions that name that object, then consumed by recall beside the 10 mm one. During location, nothing that places an object (candidates, ties, territories, key planes, source addresses, maps, calibration) differs between the deferred and the paired route. A bone territory built from a native mask defers the same way. Its saved record holds the mask as an address and digest alone; the original validated mask is referenced only on the current runtime study, and the question that asks reads over that very mask after its exact serialized identity and mask digest are checked. A mask the study does not hold, or holds as another territory, is refused by name and never read in its place, and no array is saved in the result. The memory is immutable and shared; the decoded series and any referenced mask belong to the current study and are released when it ends.

Each study record's `work` counts the two apart: `location_fine_readings` is the 2 mm readings paired with their 10 mm ones at location, and `paired_fine_readings` is those a named question paired afterwards. With a territory-v2 memory, production should report 0 for the first; a nonzero count shows location paired upfront. Default, direct and reference callers still pair upfront: `refine_finalists` is keyword-only and defaults to `True` on `knee.diagnosis.squint_locator.locate_objects` and the anatomy-first locators beneath it. Production passes `refine_finalists=False`, and only to a locator that declares the keyword; any other is called as before. A v1 memory and the cached-profile route make no 2 mm territory reading, so deferral changes nothing there.

Output contains:

- `studies/<UID>.json.xz`: losslessly stored located regions/profiles, individual case terms, findings, ranking and bounded observations. Production uses XZ preset 0 for these records to reduce write CPU; other metadata retains its default preset 6. Decompressed information is identical. `knee.json_store.load_json` reads these files and the older plain JSON form; the report-admission command uses that public reader.
- `recall-preparation.json.xz`: for inference, the exact fixed empirical-envelope populations, comparisons and scope. A reused compressed cache is copied byte for byte; its preparation is nested under `preparation` in the `knee.squint-recall-cache/v1` artifact. A freshly computed legacy fallback uses the direct preparation schema. The receipt names the actual schema and hash. Numerical acceleration matrices are rebuilt, not additional observations. Capacity mode instead records each study's excluded-population identity in its own evidence, with no unfiltered operation-wide preparation artifact.
- `submission.csv`: the official UID order and twelve exact condition columns when a template is supplied.
- `receipt.json`: source mode, memory identity, envelope-audit hash, per-condition outcomes, actual evidence paths/bytes and measured work.

Each located object's complete recalled `profile` remains directly available. Search candidates retain every tie and native address. Their `profile_ref` refers to that object's `evidence.candidate_profile_catalog`, which in turn shares exact bank and series-context payloads through `candidate_bank_catalog` and `candidate_series_context_catalog`. Use `knee.diagnosis.squint_locator.resolve_candidate_profile(located_object, profile_ref)` to reconstruct the complete original profile. Publication checks that reconstruction before releasing the candidate payload. Sharing data does not merge locations or turn a tie into a decision.

The continuous ranking keeps defeated below open below assigned and uses exact case resemblance within those bands. It emits neither hard zero nor hard one and makes no calibrated-risk claim. Categorical findings remain separate. Silence, conflict and unsupported recall radii remain explicit.

A configuration voice can decide only when that individual case's actually compared banks cover the condition's defining tissue. Supporting-only comparisons may grade an open result. For a negative multi-site condition, every alternative site must be covered in the same comparison; separate partial negative cases do not supply that coverage.

A warranted partial normal comparison remains counterevidence at its observed defining site. If a positive configuration compared that same site, their competition keeps an otherwise open question open. This also applies to a warranted object-normal reading. It does not erase a separately warranted localized positive at another site. An explicit caller restriction of `grade_only` survives both object and configuration consumers; it is not imposed merely because a cheap reading lacks a native outline.

Recall terms retain each case's per-question `call_scope`. For Fracture and Contusion, `positive_condition_presentation` means the object was observed in a diagnosed study; it does not localize injury to that bone. Those terms remain available for retrieval and ranking, but alone do not supply a local positive bone predicate. Independently covered whole-condition recall can still decide. Source-scope uncertainty stays named and does not trigger an image zoom that cannot repair the label's attribution.

`--diagnostic-mode capacity` excludes the queried study before location examples, direct recall, censors and opposing-envelope preparation. Cached comparison rows are projected onto the remaining population; exact maxima and counts are recomputed without repeating pairwise measurements. Context-only objects remain available for location without requiring a diagnostic envelope. This is an information check, not a tuning objective.

Use a fresh output directory and an official-format template containing exactly the selected labelled UIDs. The template supplies identifiers and column order, not inference features:

```python
import csv
from pathlib import Path
from knee.diagnosis.submission import SUBMISSION_COLUMNS
from knee.study.tables import LABELS

with Path("data/raw/train.csv").open(newline="", encoding="utf-8-sig") as stream:
    labelled = [
        row["StudyInstanceUID"]
        for row in csv.DictReader(stream)
        if all(row.get(label) in ("0", "1") for label in LABELS)
    ]
with Path("/absolute/new/heldout-template.csv").open("x", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(SUBMISSION_COLUMNS)
    writer.writerows((uid, *([""] * len(LABELS))) for uid in labelled)
```

```sh
.venv/bin/python scripts/run_interiors.py \
  --labeled --root data/raw --workers 4 --diagnostic-mode capacity \
  --diagnostic-memory /absolute/existing/prepared-memory \
  --diagnostic-submission-template /absolute/existing/heldout-template.csv \
  --diagnostic-output /absolute/new/heldout-run

.venv/bin/python scripts/evaluate_squint_capacity.py \
  --run /absolute/existing/heldout-run --labels data/raw/train.csv \
  --output /absolute/new/capacity-report.json \
  --markdown /absolute/new/capacity-report.md
```

The reporter checks the run and per-study memory identities, own-study exclusion, exact ranking fractions and exported CSV. It refuses budget-unexamined studies as an incomplete evaluation. It reports identified, abstained and wrong per condition, split by positive/negative truth, plus exact ordering/AUC and ties. Missing labels remain unavailable. Do not collapse these into one success percentage or tune anatomy toward them.

## Package the runtime offline

`scripts/package_squint_kaggle.py` stages the private runtime dataset from the integrated source and a fixed memory. It uses only the standard library and never touches the network, uploads, submits, runs the pipeline or edits its inputs.

```sh
.venv/bin/python scripts/package_squint_kaggle.py \
  --memory /absolute/existing/memory-r1 \
  --output /absolute/new/staging-r1 \
  --verify
```

A build needs an `--output` that does not exist yet and lies outside both the source checkout and the input memory. Use a fresh external location such as `/tmp/rsna-knee-runtime-r1`; placing staging under the repository (including `data/`) is refused. Real paths are checked: output may neither equal, contain nor sit inside either input. It receives exactly `dataset-metadata.json` (dataset `rohanvinaik/rsna-knee-squint-runtime`), `runtime-bundle.tar` and `RUNTIME_MANIFEST.json`. The tar holds every `.py` file of `src/knee`, `scripts/run_interiors.py`, the memory byte for byte and an inner copy of the manifest. Tests, archives, caches, study data and anything under `src/` that is not Python are left out and listed under `source.excluded` in the manifest. The same inputs give a byte-identical staging. `--root-source REPO` packages another checkout (default: the repository holding the script), `--extra-script scripts/<name>.py` (repeatable) adds a runtime script the runner needs, and `--scaling-selection FILE` adds the scaling notebook's study-UID list. Exit 0 prints a JSON summary (`bundle_id`, `tar_sha256`, `file_count`, the `memory` block with its `tree_sha256`, `source_checks`). Exit 2 is a refusal, with the reason on stderr and nothing left behind.

`--verify` re-reads the staging it just built. It also re-reads a staging that already exists; this verifies its contents rather than repeating the new-build path-overlap check. Given both `--memory` and `--root-source` it then compares that staging with those sources to prove it is not stale; without them it compares nothing, and `compared_with_sources` is empty:

```sh
.venv/bin/python scripts/package_squint_kaggle.py \
  --output /absolute/existing/staging-r1 --verify \
  --memory /absolute/existing/memory-r1 --root-source .
```

It refuses a memory without the exact top-level `knee.squint-memory/v1` schema, and any symlink, pickle or model artifact, object-dtype array, credential-like name, DICOM pixel data, teaching label file or secret-like string. Two source checks catch at packaging time what Kaggle would otherwise show late, or not at all:

- Every shipped Python file must parse as the offline runtime's Python, 3.13 (the cp313 wheels). This is a best-effort grammar check, `ast.parse(..., feature_version=(3, 13))`: it refuses the newer syntax CPython's parser version-gates (template strings and an unparenthesised `except A, B:` are tested), it is not a compatibility proof, shipped code is parsed, never imported or run, and library behaviour is not checked.
- No shipped file may import a `knee` module, or a name a `knee` package's `__init__` binds, that the bundle does not hold. Every import counts, including those inside functions and behind `except ImportError`: the production code reaches several modules lazily, a missing one there is a quiet degrade to open results after hours of work, and the wrappers' import check cannot see it. Attributes of a plain module, other packages and the standard library are not checked, and a package that star-imports or defines a module `__getattr__` is not guessed at.

`source_checks` in the summary records the grammar version and how many Python files and `knee` imports were checked.

### Rehearse without a real memory

A tiny published memory is enough to exercise the packager, the bundle's own imports and its recall-preparation readback on the real source tree. No study is decoded and nothing leaves the machine: Choose fresh memory and staging paths outside the checkout; the placeholders below must obey the same input/output separation as a release.

```sh
.venv/bin/python - <<'PY'
from pathlib import Path

from knee.diagnosis.squint_locator import prepare_recall
from knee.diagnosis.squint_memory import SCHEMA, save_memory
from knee.study.tables import LABELS

memory = {"schema": SCHEMA, "revision": "smoke-r1", "questions": list(LABELS), "cases": []}
save_memory(memory, Path("/absolute/new/smoke-memory"), prepared_recall=prepare_recall(memory))
PY
.venv/bin/python scripts/package_squint_kaggle.py \
  --memory /absolute/new/smoke-memory --output /absolute/new/smoke-staging --verify
.venv/bin/python -m pytest tests/test_package_squint_kaggle.py tests/test_portable_sparse_packaging.py tests/test_kaggle_runtime_pins.py
```

`tests/test_package_squint_kaggle.py` stages the real tree with an empty published memory of this kind and selects it through the production wrapper under explicit pins taken from that staging. It copies the bundle to local disk as the wrapper does, imports the bundle's own `knee` in a fresh process, restores the bundle's recall preparation (a preparation bound to another memory is recomputed, never trusted) and runs the shipped runner's `--help` for every flag the wrapper passes. A rehearsal staging is not a release: its identities are not the wrapper's pins, and it is never uploaded.

## Private Kaggle dry run

Package the integrated source and fixed memory as above. The package ships production source, a manifest and memory; the verified CPython 3.13 wheels are supplied by `rohanvinaik/rsna-knee-wheels-cp313`. Verify the staging manifest before upload.

`kaggle/squint-production/` is the private offline test wrapper. It copies code to local disk, installs the offline wheels into a local target, uses four study workers with one thread per numerical library, invokes the same production entry point and validates the final CSV. `kaggle/squint-scaling/` is the separate training-data orchestration wrapper. It does not silently teach recalled answers.

Before launching, set the production wrapper's `EXPECTED_RUNTIME_BUNDLE_ID` and `EXPECTED_MEMORY_MANIFEST_SHA256` to the verified staging manifest's bundle identity and its `memory/manifest.json` digest (the summary's `bundle_id`, and the SHA-256 of the memory's own `manifest.json`, which `RUNTIME_MANIFEST.json` also lists as the `memory/manifest.json` entry). Run the gate on that exact wrapper and source. Uploading a dataset version is asynchronous: wait for that version to become ready, download its current runtime manifest and verify both identities against staging, then push the private kernel. The wrapper independently checks both pins before inference and records all observed and excluded mounts; an older internally consistent bundle is not a fallback. The remaining notebook budget is passed to the entry point's per-study allocator.

The envelope that run is held to is recorded in [FULL_BUILD_PLAN §16.9](FULL_BUILD_PLAN.md), verified 2026-10-19 UTC against the competition and Kaggle notebook pages. Recheck those pages and the selected environment at final packaging.

| Limit | Published | Set by the repository |
|---|---|---|
| Notebook time | 9 hours (32,400 s) for the whole offline notebook: environment preparation, imports and JIT, discovery, decoding, recognition, serialization and final output | the production wrapper's `KAGGLE_LIMIT_S`; it passes `--squint-time-limit` as that limit less a 20-minute reserve (`RESERVE_S`) less the time setup has already used. The entry point's own default is 30,000 s |
| CPU route | 4 CPU cores, advertised 30 GB RAM | four study workers (`WORKERS`, the only count the wrapper's argument check allows), one thread per numerical library |
| Saved output | advertised 20 GB under `/kaggle/working` for all saved files combined | the whole diagnostics directory, logs and receipts stay there; the wrapper records output bytes and peak process-tree memory |
| Scratch | session-local space outside `/kaggle/working`; its quota is measured, not assumed | the local code copy, the wheel target, temporary files and the numba cache, under `/kaggle/tmp` when it exists, else `/tmp` |
| Network | internet disabled | code and memory from the runtime dataset, wheels installed with `pip --no-index` from the cp313 wheels dataset; the kernel's GPU, TPU and internet are off |
| Workload | about 1,300 hidden test studies, the host's approximation | the notebook runs the studies actually mounted; no count is assumed |

The sizes are Kaggle's advertised GB. Record the byte quotas the run actually reports instead of treating GB as GiB.

Keep the dataset and kernel private. A dry run is not a competition submission. Download the actual receipt, per-study evidence, logs and CSV, and compare actual wall time, peak RSS and saved bytes against that envelope. Historical stage timings or sparse-cosine microbenchmarks are not end-to-end acceptance. A figure measured on a development machine, or scaled to the host's study count, is a local projection and is labelled as one beside any measured Kaggle figure; only the dry run's receipt measures the Kaggle route. This guide makes no claim about the current source's or memory's fit in the envelope.

## Grow memory separately

Independent report calls retain their exact source sentences, question, anatomical attribution, uncertainty and reader identity. Unmentioned or equivocal findings provide no signed call. The report import/admission interface validates those records and publishes a new memory revision; it never modifies a running inference memory. Predictions do not supply missing teaching calls. Conflicts remain attributed; duplicate sources count once.

`scripts/squint_report_teaching.py export --train-csv data/raw/train.csv --output /absolute/new/reader-batch.json` (optionally `--study-uid UID [UID ...]`) writes each report's text and SHA-256, with no label values, for independent readers. Their calls come back as documents in the `knee.squint-report-calls/v1` schema, bound to those reports. `scripts/squint_report_teaching.py admit` (`--train-csv`, `--calls`, `--findings-dir`, `--memory`, `--revision`, `--output-memory`) publishes a revision through the same admission, but with the manifest only: it saves no recall preparation beside it, so inference on that memory recomputes the preparation. The teaching round below publishes a prepared, read-back child.

### One teaching round

`scripts/squint_training_round.py` teaches one immutable child revision from independent calls and, if asked, evaluates it. It consumes three inputs and pins each by SHA-256: a published parent memory; a completed squint run (`receipt.json` and `studies/<UID>.json[.xz]`, from `infer` or `capacity`) whose records hold the located objects; and call documents bound to the report text of `train.csv`, of which only the Report column is read. A round requires independent calls and publishes a new immutable child; the parent is never written. What the child can do is read only from the self-excluded capacity evaluation (`--evaluate`, below), in which each study is left out of its own memory. Nothing measured on the parent or on the observing run says anything about the child.

```sh
.venv/bin/python scripts/squint_training_round.py \
  --parent-memory /absolute/existing/memory-r1 \
  --expect-parent-sha256 PARENT_MANIFEST_SHA256 \
  --observations /absolute/existing/inference-r1 \
  --reports data/raw/train.csv \
  --calls /absolute/existing/calls-reader-1.json \
  --calls /absolute/existing/calls-reader-2.json \
  --revision memory-r2 \
  --out /absolute/new/round-r2
```

`--parent-memory`, `--observations`, `--reports`, `--calls`, `--revision` and `--out` are required; `--calls`, `--study-uid` and `--evaluate-study-uid` repeat. `--expect-parent-sha256` pins the parent's `manifest.json` bytes, and `--study-uid` limits a small round to those studies. `--note` is recorded with the round. `--use` is `teaching` (the default) or `mechanical_loop_test`, which marks a child made only to exercise the loop: it is refused as a later parent and is never for inference, further teaching or any capacity claim.

Admission is the existing `admit_report_cases`; it alone decides what an independent call may teach. The round hands it findings read off the run's records: a called object's own cheap profile and regions when the object was `proposal` or `located`, or a called question's composite (`diagnosis/<Question>`) composed as the inference composed it. An object the run did not locate is not offered as a finding. A record's verdicts, values and recall evidence are never read as calls, and `train.csv` labels are never calls here.

The round root receives `round-inputs.json` (the pinned inputs), `round.json`, the child `memory/` and, with `--evaluate`, `evaluation/`. `round.json` (`knee.squint-teaching-round/v1`) holds the status (`published`, `evaluated`, `refused` or `incomplete`), the parent, each call source's digest and counts, the admission summary (added cases, rejections by reason, needs-review, held and unmatched calls), the child's identity and readback, and the digests of the code the round ran on. The child is published with its recall preparation (the parent's is reused when the recall inputs are unchanged, otherwise computed), read back through the ordinary loader and the production preparation consumer, and only then marked published. The parent, the run, the reports and the calls are never written, and a child is never published over an existing path. A parent that is an earlier round's `memory/` must come from a completed teaching round. Running the same command on the same round root resumes from its pinned inputs; changed inputs are refused (`round_root_inputs_mismatch`) and leave the round as it was.

`--evaluate` adds a held-out evaluation of the child and needs `--root` (the raw competition files), `--labels` (the official `train.csv`) and studies from `--evaluate-study-uid` (default: the `--study-uid` scope). It runs the production capacity route with each study left out of its own memory, reports identified, abstained and wrong per condition with the reporter of `scripts/evaluate_squint_capacity.py`, and checks each study's excluded population against the one memory view the other consumers use. A population that disagrees is kept as `exclusion_mismatch`, not as an evaluation. `--workers` takes 1 to 3 (default 2) and `--time-limit` is the operation budget in seconds (default 1800). A completed evaluation of the same request on the same child is kept and reused, never rerun, and a failed attempt stays under `evaluation/<request digest prefix>/attempt-N/` as evidence. When the parent round was evaluated over the same studies, labels and source, the two evaluations are laid side by side as a trajectory and never summed.

The command prints one JSON line and exits 0 only when the round reached the state it was asked for: `published`, or `evaluated` with `--evaluate`. A published child whose evaluation failed or disagreed exits 2, and the child stays published. `tests/test_squint_training_round.py` uses invented fixtures and a stand-in for the capacity route. It pins the join to observations, publication, readback, resume, the parent checks and the evaluation checks; the real capacity route inside a round is not exercised there, and none of it measures diagnostic capacity.

## Review saved evidence without rerunning vision

```sh
.venv/bin/python scripts/replay_squint_findings.py \
  --run /absolute/existing/heldout-run \
  --output /absolute/new/replay.json \
  --markdown /absolute/new/replay.md \
  --labels data/raw/train.csv --require-complete
```

This is old evidence through the current combiner, not fresh recognition. It replays the current combiner and ranking over the saved case terms and scope marks, and records both code and input identities, named changes, and per-condition identified/abstained/wrong counts. It does not rerun location, recall, scope assignment, or image measurements, and it opens no image and no memory. A saved inference run is not made held-out by replaying it; the original run owns that population. Missing older scope fields remain missing and are counted. The labels are opened only after the replay is finished, to count outcomes, and are never features. A dataset whose receipt does not account for every study, or that holds an unexamined study, is reported as partial and tallied apart from the complete studies; the two are never pooled. `--require-complete` exits 1 after writing when the dataset is partial, and `--expected-uids FILE` (one study UID per line) names the studies the run was meant to cover. Use this paired control to isolate decision changes, and use the real capacity entry point for current vision and runtime evidence.

## Draw what recall compared (development only)

`scripts/squint_visual_capacity.py` pictures a finished run for a person to inspect. It is development tooling: production never imports it, and it never locates, recalls or decides. It reads the run's saved records, the memory the run recalled from, and the native DICOM slices of the studies and precedents it draws, so it needs the dataset root. Its drawing layer (matplotlib) loads only when a sheet is drawn.

```sh
.venv/bin/python scripts/squint_visual_capacity.py \
  --run /absolute/existing/heldout-run \
  --memory /absolute/existing/prepared-memory \
  --root data/raw \
  --study-uid STUDY_UID \
  --label heldout-r1 \
  --output /absolute/new/visual-capacity
```

`--run` is a completed capacity or inference output: its diagnostics directory (`receipt.json` and `studies/`) or the run root holding `diagnostics/`. `--memory` must be the exact memory that run recalled from, as a directory or its `manifest.json`; any other memory is refused by name. `--study-uid` names a study of the run and repeats for several. `--label` is the run's name on every sheet, not a condition label. `--question NAME` (repeatable) draws only the named questions, spelled as the record names them; `--io-workers` and `--dpi` default to 2 and 120. Sheets go to `<output>/<label>/<study uid>/NN-<question>.png` with a `manifest.json` per study and `<output>/<label>/run-manifest.json`. Nothing is overwritten: an existing sheet directory or run manifest is refused by name, so give a fresh `--output`.

`--run-source-pin FILE` supplies the JSON of repository-relative paths and the SHA-256 digests the run was made with (or a run invocation record holding them as `source_before`), and the drawing code's digests are compared with it; `--require-same-source` refuses when they differ. Without a pin the code is not compared.

Each sheet draws what was recorded and nothing more: the native-slice regions the query's profile was counted over, the nearest precedent called normal and the nearest called a presentation, each over its own places, the banks each comparison read, and the largest named differences between those banks decoded from the exact counts. A bank a profile did not write is drawn as unread, never as a middle, and a profile that cannot reproduce the recorded terms is marked unverified and draws nothing as compared. A precedent called positive carries a study-level label only: it does not localize a lesion in that object or window, and each sheet says so. A drawing helps inspect the actual run's recorded measurements; by itself it establishes neither diagnostic capacity nor the production inference path.

## Retire an independently reviewed teaching case

`scripts/curate_squint_memory.py` is explicit, hash-pinned adjudication, not an automatic label or score cleanup. It acts only on decisions authored independently from source inspection, each pinned to the parent manifest's SHA-256 and to the profile fingerprint of the exact object reading its author inspected; a different parent or reading is refused. It does not automatically choose a case from labels, a score, a threshold or overlap; the reviewer authors each decision from source inspection. First obtain the exact parent-manifest SHA-256 and the inspected object's profile fingerprint:

```sh
shasum -a 256 /absolute/existing/memory-r1/manifest.json
.venv/bin/python scripts/curate_squint_memory.py fingerprints \
  --memory /absolute/existing/memory-r1 \
  --expected-manifest-sha256 PARENT_MANIFEST_SHA256 \
  --case-id 'squint-case:STUDY_UID:OBJECT_SUBJECT'
```

Write a decision document with the returned fingerprint and the actual inspection evidence:

```json
{
  "schema": "knee.squint-memory-curation-decisions/v1",
  "decisions": [{
    "case_id": "squint-case:STUDY_UID:OBJECT_SUBJECT",
    "expected_profile_fingerprint": "EXACT_64_CHARACTER_PROFILE_SHA256",
    "disposition": "retire_whole_case",
    "evidence": "Inspected image address and source identity",
    "reason": "Why this named teaching case is withdrawn",
    "reviewer": "Identity of the independent reviewer"
  }]
}
```

```sh
.venv/bin/python scripts/curate_squint_memory.py curate \
  --memory /absolute/existing/memory-r1 \
  --expected-manifest-sha256 PARENT_MANIFEST_SHA256 \
  --decisions /absolute/existing/decisions.json \
  --output-memory /absolute/new/curated-memory
```

The parent stays unchanged. The new memory preserves each retired case and its decision, rebuilds affected canonical configurations from remaining objects, prepares recall, and verifies publication through the public loader. An unmappable configuration retaining retired-role evidence refuses publication. This is whole-case retirement pending adjudication; it neither withdraws an anatomical definition nor pretends to repair one facet. Re-evaluate the child before adopting it. Curations do not stack silently: revise decisions against the original parent.

## Verify

```sh
.venv/bin/python -m pytest tests/test_squint_profiles.py tests/test_squint_memory.py tests/test_squint_locator.py tests/test_squint_contracts.py tests/test_squint_reports.py tests/test_squint_pipeline.py tests/test_squint_entrypoint.py
bash scripts/ci_local.sh
```

The packaging, report, held-out, teaching, replay, curation and drawing commands above, and the deferred fine reading, have their own focused tests:

```sh
.venv/bin/python -m pytest tests/test_package_squint_kaggle.py tests/test_portable_sparse_packaging.py tests/test_kaggle_runtime_pins.py tests/test_squint_report_cli.py tests/test_evaluate_squint_capacity.py tests/test_squint_memory_territory.py tests/test_squint_training_round.py tests/test_replay_squint_findings.py tests/test_curate_squint_memory.py tests/test_squint_visual_capacity.py tests/test_squint_deferred_native.py
```

Use the real entry point for runtime verification. Inspect source provenance and actual output coverage alongside test/gate results. The older [diagnostic guide](DIAGNOSTIC_RUN_GUIDE.md) describes explicit full-reference tools; the anatomy development path and drawing remain available there and in [OBJECT_OUTPUT.md](OBJECT_OUTPUT.md).

## Read both descriptions offline

The full representation remains sparse on disk. Reconstruct only the requested object:

```python
from pathlib import Path
from knee.diagnosis.squint_memory import load_memory, full_profile_from_case

memory = load_memory(Path("/absolute/existing/memory-r1"))
case = next(c for c in memory["cases"] if c.get("full_profile"))
cheap = case["profile"]
full = full_profile_from_case(memory, case)
assert cheap["subject"] == full.subject == case["subject"]
```

For a condition configuration, pass the anatomical role explicitly with `subject="femur"` (or another retained role). The configuration links to that object's original full payload rather than copying or blending it. Source H5 files are not needed for this sparse-count reader. Layout/reference identity and missing banks keep their meanings; these two descriptions are not interchangeable numerical arrays.

An older identity-only memory can be upgraded once from its exact retained products, without raw-image reads or recognition:

```python
from knee.diagnosis.squint_memory import hydrate_full_profiles, save_memory

old = load_memory(Path("/absolute/existing/old-memory"))
portable = hydrate_full_profiles(old, Path("/absolute/existing/h5-products"))
save_memory(portable, Path("/absolute/new/portable-memory"))
```

Hydration checks the products against their previously retained digests and identities. Saving checks every available full payload through the public reader before atomic publication; failure preserves existing memory. Ordinary bootstrap compilation already performs this retention and needs no migration step.
