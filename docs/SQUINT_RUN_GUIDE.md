# Squint-first operation

The competition operation reads raw MRI series, locates anatomy in their cheap physical squints, recalls individual normal and condition-presentation cases, and writes twelve ranked values. Full anatomical reconstruction supplies bootstrap examples. It is not a required inference prefix.

The governing design is [AI_DIAGNOSTIC_DESIGN.md](AI_DIAGNOSTIC_DESIGN.md); the exact implementation interfaces are [SQUINT_PRODUCTION_CONTRACT.md](SQUINT_PRODUCTION_CONTRACT.md). Current acceptance evidence and pending work live only in [the current packet](work/current/README.md).

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

A positive official label supplies the implicated object's condition presentation, without claiming that every contextual tissue is damaged. Only an object implicated by no positive label enters the normal bucket; blank conditions never become negative calls. Structural examples can carry no diagnostic call and still help locate anatomy.

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

Output contains:

- `studies/<UID>.json.xz`: losslessly stored located regions/profiles, individual case terms, findings, ranking and bounded observations. `knee.json_store.load_json` reads these files and the older plain JSON form; the report-admission command uses that public reader.
- `recall-preparation.json.xz`: the exact fixed empirical-envelope populations, comparisons and scope, saved once for the operation. Numerical acceleration caches are not additional observations and are not serialized.
- `submission.csv`: the official UID order and twelve exact condition columns when a template is supplied.
- `receipt.json`: source mode, memory identity, envelope-audit hash, per-condition outcomes, actual evidence paths/bytes and measured work.

Each located object's complete recalled `profile` remains directly available. Search candidates retain every tie and native address. Their `profile_ref` refers to that object's `evidence.candidate_profile_catalog`, which in turn shares exact bank and series-context payloads through `candidate_bank_catalog` and `candidate_series_context_catalog`. Use `knee.diagnosis.squint_locator.resolve_candidate_profile(located_object, profile_ref)` to reconstruct the complete original profile. Publication checks that reconstruction before releasing the candidate payload. Sharing data does not merge locations or turn a tie into a decision.

The continuous ranking keeps defeated below open below assigned and uses exact case resemblance within those bands. It emits neither hard zero nor hard one and makes no calibrated-risk claim. Categorical findings remain separate. Silence, conflict and unsupported recall radii remain explicit.

`--diagnostic-mode capacity` excludes the queried study's cases from recall. This is an information check, not a tuning objective. Report identified, abstained and wrong per condition against independently supplied calls; do not collapse those into one success percentage.

## Private Kaggle dry run

Package the integrated source and fixed memory with `scripts/package_squint_kaggle.py`. The package ships production source, a manifest and memory; the verified CPython 3.13 wheels are supplied by `rohanvinaik/rsna-knee-wheels-cp313`. Inspect that command's help and verify the staging manifest before upload.

`kaggle/squint-production/` is the private offline test wrapper. It copies code to local disk, installs the offline wheels into a local target, uses four study workers with one thread per numerical library, invokes the same production entry point and validates the final CSV. `kaggle/squint-scaling/` is the separate training-data orchestration wrapper. It does not silently teach recalled answers.

Keep the dataset and kernel private. A dry run is not a competition submission. Download the actual receipt, per-study evidence, logs and CSV, and compare actual wall time, peak RSS and saved bytes against [FULL_BUILD_PLAN §16.9](FULL_BUILD_PLAN.md). Historical stage timings or sparse-cosine microbenchmarks are not end-to-end acceptance.

## Grow memory separately

Independent report calls retain their exact source sentences, question, anatomical attribution, uncertainty and reader identity. Unmentioned or equivocal findings provide no signed call. The report import/admission interface validates those records and publishes a new memory revision; it never modifies a running inference memory. Predictions do not supply missing teaching calls. Conflicts remain attributed; duplicate sources count once.

## Verify

```sh
.venv/bin/python -m pytest tests/test_squint_profiles.py tests/test_squint_memory.py tests/test_squint_locator.py tests/test_squint_contracts.py tests/test_squint_reports.py tests/test_squint_pipeline.py tests/test_squint_entrypoint.py
bash scripts/ci_local.sh
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
