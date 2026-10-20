# Offline Linux runtime candidate

This candidate packages only the existing `scripts/run_interiors.py`, `src/knee`, and the locked production dependency closure plus the already-declared `jit` and `hdc` extras. `jit` supplies Numba, which the production local-lightness kernel requires. `hdc` supplies h5py for the opt-in built-in object encoding output. It does not include study data, receipts, tests, development tools, credentials, or profiling tools. The runtime image is built before the offline run; `docker run --network none` performs no package or source downloads.

The checkout declares Python `>=3.11` and `.python-version` `3.14`. The frozen lock includes Linux x86_64 wheels for the production requirements (`numpy`, `scipy`, `scikit-image`, `pydicom`, `python-gdcm`) and the locked `jit` (`numba`) and `hdc` (`h5py`) extras on CPython 3.14. The image smoke check constructs the existing lazy Numba dispatcher and imports the H5 product reader; it does not warm or compile a kernel because no input arrays are passed. This candidate uses CPython 3.14 to match the checked-in runtime selection. The Docker base must be provided explicitly as an OCI digest, so the base image is part of the recorded environment rather than an implicit mutable tag.

## Stage the context

Run from a machine with the checkout and `uv` available. This exports the frozen production dependency closure plus the existing `jit` and `hdc` extras with hashes and stages only the production package and CLI; it never copies `data/` into the build context. Choose a new empty destination each time.

```bash
python3 /path/to/RSNA_Knee/scripts/offline_runtime/prepare_context.py \
  --source-root /path/to/RSNA_Knee \
  --candidate-root /path/to/RSNA_Knee/scripts/offline_runtime \
  --destination /private/tmp/rsna-codex-build-20261019/offline-runtime-context
```

The generated `source-manifest.json` records the checkout revision, every shipped Python file hash, project/lock hashes, and exported requirements hash. The export command selects only the existing `jit` and `hdc` extras in addition to the default production dependencies; it excludes development and profiling groups. Regenerate the context from the final integrated source before the eventual W10 run; the current source pin is only the preparation baseline. The Dockerfile requires `PYTHON_BASE_IMAGE`, `SOURCE_REVISION`, and `SOURCE_TREE_SHA256` build arguments. Resolve the Python base to a digest before building. For example, substitute a verified value for `<base-digest>`; do not use the tag alone for the recorded run.

```bash
docker buildx build --platform linux/amd64 --load \
  --build-arg PYTHON_BASE_IMAGE='python:3.14-slim-bookworm@sha256:<base-digest>' \
  --build-arg SOURCE_REVISION='<source_revision from source-manifest.json>' \
  --build-arg SOURCE_TREE_SHA256='<source_tree_sha256 from source-manifest.json>' \
  --tag rsna-knee-offline:source-pinned \
  --file /path/to/offline-runtime-context/Dockerfile \
  /path/to/offline-runtime-context
```

The candidate has been built and run once on the Apple ARM host with `--platform linux/amd64`; that execution is emulated and establishes compatibility/resource facts only, not Intel Skylake performance. The final integrated source still needs a fresh context, image build and W10 run. Record the built image ID/digest and base digest for each source epoch.

The verified preparation image used source tree `207bb1b92a991f4788609b13a4a4ee755be2fd9a00083164d69f008e8e1f8ecf`, revision `ac141a1ae599585bee7958d2a3983d9dd049f793`, locked `jit` export SHA256 `8c9c81181b6b4a3c8a545d5c7173acdf1c84c0abfb58806303821db32f3e516a`, and base `python:3.14-slim-bookworm@sha256:a66d3a463d0be3cc537c269b0d3418746dda512417a975559a0eaa8a6406baaf`. Its image ID was `sha256:ef6150093aa00fbb677904fb7eb5459052b4388f18a5833e69cb447e2d2b7419`; it installed Numba 0.68.0 and llvmlite 0.50.0. This historical image predates the H5-enabled export and is not evidence that the new `hdc` extra was packaged. The build smoke check constructs the existing lazy dispatcher without arrays, so it does not compile or warm the kernel.

Use the supervisor to run one of the same CLI cases and retain its invocation, image/source checks, resource samples, cgroup snapshot, log, and result. The output and scratch roots must be fresh, distinct, and non-nested. `--workers` defaults to four; the proof/bursa and public cases are also useful with a lower explicit worker count. The source manifest's tree and revision must match the image labels and build metadata; the expected image ID is supplied explicitly.

```bash
python scripts/offline_runtime/supervise_offline.py proof-bursa-parallel \
  --data-root /path/to/data/raw \
  --output-root /path/to/new/proof-bursa-output \
  --scratch-root /path/to/new/proof-bursa-scratch \
  --context /path/to/offline-runtime-context \
  --build-metadata /path/to/build-record.json \
  --image rsna-knee-offline:source-pinned \
  --image-id sha256:<built-image-id> \
  --workers 2
```

Choose `public-test` for `--split test` or `labeled-cohort` for `--labeled`; each invocation needs its own fresh output and scratch roots. The supervisor's optional `--encode-objects` flag enables the production CLI's built-in encoding and writes its H5 product under `/out/encoding` (the mounted output root), so it is included in the supervisor's sampled output budget. It is off by default and does not change ordinary recognition runs.

For the authorized complete-object retention mode, pass `--competition-output` to the supervisor.
It selects the same production CLI flag, places temporary recognition outputs at `/scratch/interiors`
and `/scratch/main`, and retains independently verified final object products and their compact receipt
at `/out/encoding`. The supervisor records these paths and the declared lifetime; actual release is
performed by the CLI after its last consumer and complete public-reader verification. Its output and
scratch sampling includes the corresponding peaks. `--encode-objects` alone remains the development
retention route. This wiring does not itself close W8b/W10; run the final-source cases and retain their
measured evidence before claiming capacity.

## Offline production invocations

Set explicit host paths. `DATA_ROOT` must contain the competition tables and series directories. `RUN_ROOT` and `SCRATCH_ROOT` must be new, writable directories on measured host mounts; data is mounted read-only. Separate `RUN_ROOT` for every comparison run. These examples invoke the same production CLI with drawing off. `--cpus 4` and `--memory 24000000000` stay below the published 4-core/30-GB envelope; this exact byte value is the supervisor default (`--memory-bytes 24000000000`) and can be overridden. Docker enforces it as the container memory limit (with swap limited to the same value). The historical 12 GiB runs and their OOM evidence remain historical; they are not the current default and do not establish that the full workload fits at either limit. Native numerical libraries are constrained to one thread. `TMPDIR=/tmp` sends multiprocessing sockets to the writable tmpfs; caches and Numba cache stay under scratch. Do not override `HOME`.

```bash
DATA_ROOT=/path/to/data/raw
IMAGE=rsna-knee-offline:source-pinned
MEMORY_BYTES=24000000000
run_cli() {
  RUN_ROOT="$1"
  SCRATCH_ROOT="$2"
  shift 2
  mkdir -p "$RUN_ROOT" "$SCRATCH_ROOT/home" "$SCRATCH_ROOT/cache" \
    "$SCRATCH_ROOT/numba-cache"
  docker run --rm --platform linux/amd64 --network none --cpus 4 \
    --memory "$MEMORY_BYTES" --memory-swap "$MEMORY_BYTES" --read-only \
    --tmpfs /tmp:rw,nosuid,nodev,size=512m \
    --mount "type=bind,src=$DATA_ROOT,dst=/data,readonly" \
    --mount "type=bind,src=$RUN_ROOT,dst=/out" \
    --mount "type=bind,src=$SCRATCH_ROOT,dst=/scratch" \
    --user "$(id -u):$(id -g)" \
    -e TMPDIR=/tmp -e XDG_CACHE_HOME=/scratch/cache \
    -e NUMBA_CACHE_DIR=/scratch/numba-cache \
    -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 \
    -e MKL_NUM_THREADS=1 -e NUMBA_NUM_THREADS=1 -e NUMEXPR_NUM_THREADS=1 -e BLIS_NUM_THREADS=1 \
    "$IMAGE" "$@" --root /data --run /out/interiors --main-run /out/main
}

# Proof and bursa together, serial.
run_cli /path/to/proof-bursa-serial /path/to/proof-bursa-serial-scratch \
  --study-uid \
  1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149 \
  1.2.826.0.1.3680043.8.498.13335129881737731410081002627729200903 \
  --workers 1

# The same two studies in parallel, for receipt equivalence. Use new roots.
run_cli /path/to/proof-bursa-parallel /path/to/proof-bursa-parallel-scratch \
  --study-uid \
  1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149 \
  1.2.826.0.1.3680043.8.498.13335129881737731410081002627729200903 \
  --workers 2

# Public test split through the same CLI.
run_cli /path/to/public-test /path/to/public-test-scratch --split test --workers 4

# Available labelled cohort through the same CLI.
run_cli /path/to/labelled-cohort /path/to/labelled-cohort-scratch --labeled --workers 4
```

For supervised runs, `--output-budget-bytes` defaults to 20,000,000,000 bytes and is configurable. The supervisor samples recursive output-file sizes at `--interval` (default one second), including run metadata, logs, receipts and pending `.part` files; if a sample exceeds the budget it stops the run. This is sampled monitoring, not a hard filesystem quota: output can cross the budget between samples, and the mounted filesystem’s free space is a separate measurement. `filesystem_capacity` reports visible capacity; `hard_quota` remains unknown unless the environment supplies and verifies one. Direct `docker run` examples above enforce Docker memory limits but do not run this output-budget sampler. For each run, retain the exact invocation, source manifest, base and final image IDs, host/kernel architecture, whether emulation was active, exit status, receipt hashes, actual study count, elapsed time, cgroup CPU/memory high-water values, output bytes, and scratch high-water/quota. Compare serial/parallel receipts using the existing `scripts/compare_receipts.py`; preserve all named refusals and unknowns. W10 stays incomplete until the real offline container runs on the selected evidence set and the measured output/scratch/runtime account leaves headroom for later stages. A successful image build or a passing proof invocation alone does not establish W10.
