# K02b — The compute design and the native layer

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K02b'` |
| **Depends on** | K02 (the backend registry, SAME, `just`), K01 (each node's CPU, caches, cores and flags; the Linux build path) |
| **Consumed by** | every kernel chapter: K04, K05, K07, K09–K11, K13, K13a, K15, K19–K25; the kernel (K18, K27) |
| **Commit label / tag** | `knee/K02b` · `knee-K02b` |

## 1. Purpose and authority

To decide, at design time and per operation, the language, the memory layout, the cache and parallel plan, and
the budget. The decisions are made by recognizing each operation's computation shape and reading its counted
cost, and native modules are built in from the start. Every module still keeps a reference, and every one is
admitted only by its gate.

- **The founder:**
  - 15:24:53Z: "the considerations when using python vs rust vs C/C++ for different operations. It's important to
    think through what the best, most effective compute operation is for a task (e.g. for hypervectors,
    cache/memory operations can really speed stuff up, and JIT is basically a requirment). ACTUALLY look into
    it."
  - 17:22:59Z: "considerations about language-specific modules (e.g. C/C++ for memory management, cache hot vs
    cold management, Rust for speed, etc). Those tools should help us build in those considerations and
    implementations from the start".
  - DETERMINISTIC_SICP §1.1: "Code should be written in the proper language and paradigm that appropriately
    executes the operation (e.g. Rust vs Python vs C++)". Parallelization, JIT, one-hit, in-memory compute and
    cache optimization are to be made "not vibes, but a directly optimizable set of decisions".
- **The formal basis is Detective's second half** (DETERMINISTIC_SICP):
  - performance engineering is "template *recognition* over code … followed by deterministic per-template
    transform grammars" (§6). The templates include "vectorizable map", "IO-bound loop", "cache-hostile
    traversal", "memoizable pure recursion" and "batch-able chatty interface";
  - its banks include a **budget** bank and a **language/paradigm fit** bank (§4.1);
  - efficiency is read as "deterministic, countable budgets", "paired arms under the safety constraint" (§7);
  - "No gate, no arc": `rewrite-in-<lang>` needs warranted cross-language emission (§8).

  Built and measured (§12): the template recognizers v1, the budget bank, the controller (`detective plan`), and
  a C-emission gate for scalar functions.
- **THESIS §12.5:** "Every function carries a contract, data that tests read. It names the kind of work, the
  body's language and the measurement that chose it, the encodings read and written, what is allocated and kept,
  and the unit it can run beside others in."
- **THESIS §12.6:** "The system computes a value once, and then measures only the change"; kept values, and a
  lens "not computed" where it cannot speak.
- **The standard is the professional finish everywhere.** The founder, 17:32:09Z: "don't assume too much what is
  and isn't a "cheap" operation "not worth optimizing". (1) you don't know what the full/final design, since I
  don't know it myself, things can change a lot as we experiment, and (2) I want this to be AS clean and
  efficient/professional as possible. This is a demonstration, a BOLD claim about classical AI". And 17:32:17Z:
  "Suit and tie, not just "not naked"". So no operation is exempt from engineering because it measures cheap
  today. Every operation gets the whole treatment: its contract, its shape-derived language, its layout, fusion
  and parallel unit, its gates and its counted budget. A measured cost orders the work, and it never excuses a
  naive path.
- **What this replaces.** The book's earlier D3 was "Numba is the default for hot loops; native code only by
  evidence". That deferred the native layer to a later measurement. Here the language comes from the operation's
  shape at design time. The measurement *verifies* the choice and can refuse it, and it no longer has to
  *discover* it.
- **Non-goals:** no domain decision; no speed claim without a paired budget.

## 2. Dependencies and consumers

**Produced:**
- **The compute contract** (THESIS §12.5), one per kernel, as data that tests read: `ComputeContract{kind
  (template), language, chosen_by, reads (encodings), writes (encodings), allocated_bytes (formula), kept (values
  kept for consumers), working_set_bytes (formula), traversal, block (size, with its cache rationale),
  parallel_unit, numeric_model, cold_inputs (memory-mapped artifacts, with their read order)}`.
- **The native workspace,** `native/`:
  - `native/rust/knee_native`: a Rust crate built with PyO3 and maturin, using rayon. Its first module is K25's
    case-memory scan;
  - `native/c/knee_kernels`: C11 built with CMake and Ninja, behind a plain C ABI loaded through `ctypes`, which
    releases the GIL during the call. Its first module is K09's blocked per-voxel order statistics, with the
    tiling and transposes of the reference build.
- **The backend registry, extended** (K02): backends `reference | numba | c | rust`. The requested and effective
  backends and the CPU-feature dispatch (NEON, AVX, AVX2, AVX-512) are recorded per run. A required backend that
  is missing refuses, never falls back silently.
- **Builds per environment:**
  - VERIFY, on the dev seat (arm64 macOS): debug builds with sanitizers (ASan and UBSan for C; Rust debug
    assertions) that run the property suites, and release builds for counting;
  - the Mac Pro (x86_64 macOS): builds targeting its measured ISA (AVX, no AVX2);
  - DEPLOY (Linux x86_64): a manylinux wheel for the crate (maturin, checked with auditwheel) and the C shared
    library. They are built by the Linux path K01 measures, never inside the competition kernel, and attached as
    a private dataset. The CPU baseline comes from K01's measured Kaggle flags.

**Consumers:** every kernel chapter, through the registry and the contracts.

## 3. Mechanism

### 3.1 The rule: language by computation shape

| computation shape (template) | what dominates its cost | language and paradigm | why |
|---|---|---|---|
| a decision, a record, an orchestration | branching on named codes | **Python**, pure, pinned | THESIS §12.7: "Functions are of three kinds, kept apart"; Detective pins behaviour |
| a vectorizable map, no custom loop | whole-array arithmetic | **NumPy** | it already runs natively. Scalene says whether compiling would pay ("whether compiling pays or NumPy already does the work") |
| a library-shaped operation: registration, resampling, N4, morphology, components, geodesic paths, codecs | an established C/C++ library | **SimpleITK, SciPy, scikit-image, pydicom codecs** | their contracts written down first; reimplementing them buys nothing |
| a custom repeated loop on the kernel path: fused passes, lenses, windows, scatter-adds, planting | loop overhead, and traversals that fusion makes one-hit | **Numba JIT** (`njit`, `nogil`, `cache`, `fastmath=False`; `prange` where the iterations are independent) | "JIT is basically a requirment"; it runs on Kaggle with no wheel |
| a cache-hostile traversal, or memory-bound selection over large build-time arrays: per-voxel order statistics over members; tiled transposes | memory traffic and layout | **C** (C11): explicit allocation, voxel-major tiles sized to L2, quickselect, SIMD where it pays | "C/C++ for memory management, cache hot vs cold management": layout and allocation under explicit control |
| a batched scan over a large, long-lived indexed store, with bit-level SIMD, exact wide integers and GIL-free threads (the case memory) | bandwidth, popcount, u128, threads | **Rust** (PyO3 + maturin; rayon) | "Rust for speed", with memory-safe concurrency and native u128 |
| a scalar exact core a native kernel shares (the level test, the digit rule) | exactness | Python reference; a C emission certified by Detective's C gate | DETERMINISTIC_SICP §8 and Wave 5: the cross-language receipt Detective issues, for scalars |

A shape no row covers is AMBIGUOUS (DETERMINISTIC_SICP §5.1). It escalates to the lead with its signature, and
is never guessed.

### 3.2 Memory: hot and cold, one-hit, in memory

- **Hot and cold.**
  - The study's plane volumes are the hot working set. A plane grid is 32 × 224 × 224 ≈ 1.6 M voxels (ARCH §2.4,
    consequence 4): 6.4 MB per float32 volume, about 35 MB for a study's ~5.5 series.
  - References, the atlas, the hardness map and the case memory are cold. They are memory-mapped and read in the
    order of their consumer's traversal. A reference is stored slice-major, because K10's pass walks
    slice-major.
- **One-hit.** Passes over hot data are fused so each input is read once. K10's x̃ is computed in the pass and
  never materialized. A value is computed once where it becomes known and kept for its consumers (THESIS §12.6).
  A lens that cannot speak somewhere is not computed there.
- **In memory.** The kernel keeps a study in RAM from ingest to emission. Artifacts are memory-mapped from the
  attached datasets. Nothing intermediate is written to disk.
- **Layout contracts.** These are C order, a stated dtype per array (THE_KNEE §3.4), and:
  - slice-major for plane passes;
  - voxel-major tiles for per-voxel statistics;
  - int32 count tables and uint64 bit planes (ARCH §3.5.2: "whole numbers stored in 32 bits and summed in 64");
  - output buffers allocated by Python and filled by native code, so each buffer has one owner.
- **Cache sizes, per node, measured:**
  - the dev seat (M1 Max): performance-core L1d 128 KB, L2 12 MB per performance cluster, a 128-byte line, 64 GB
    of RAM (`sysctl`, 2026-10-02);
  - the Mac Pro and Kaggle: K01's probe.

  Tiles are sized to half of a core's share of L2. On the Mac Pro's CPU model (256 KB L2 per core, to be
  confirmed), a voxel-major tile of N = 150 float32 members holds about 200 voxels.

### 3.3 Parallelism

- **The unit,** per THESIS §12.5's "the unit it can run beside others in":
  - in the kernel, a process per study;
  - at build time, a process per shard, a tile, a perturbation or a block of cases.
- **Threads inside a study** only for kernels that release the GIL: Numba `nogil`, C through `ctypes`, Rust
  through `allow_threads`.
- **No oversubscription:** workers × (ITK, BLAS, Numba and rayon threads) ≤ cores, declared per node.
- **Parallelize-map gates** (DETERMINISTIC_SICP §8). Scheduling nondeterminism outside the value channel is
  fenced or reported, never absorbed. Exact integer merges are order-invariant by construction (THESIS §12.5:
  "Whole numbers remove the question").

### 3.4 The kernel's budget, designed from the start

- **The budget.** Kaggle allows at most 9 h. With c cores (K01 measures them) and ~1,300 test studies, the budget
  is ≈ 9 · 3600 · c / 1300 core-seconds per study, about 100 at c = 4.
- **The budget is a constraint, never a licence.** Today's sizes (1.6 M-voxel grids, ARCH §2.4) say nothing
  about tomorrow's: layers, lenses, resolutions, perturbation counts and memory size will change as the design is
  explored. So every stage is engineered to the same finish whatever its share of the budget:
  - **registration and N4,** library-shaped: one deformable transform per study carried to its series (ARCH
    §3.1); a pyramid; metric sampling with a fixed seed; declared iteration caps; N4 on a shrunk image, with its
    field evaluated at full resolution; ITK's threads declared;
  - **every custom loop:** fused and one-hit, cache-aware in its layout, parallel over its declared unit,
    compiled with explicit signatures (eager compilation, no object mode, no reflection), and twinned and
    counted;
  - **every native module:** SIMD where its shape allows, with runtime CPU dispatch; sanitized in VERIFY; lint-
    and format-clean in its own language.
- **The apportionment** per stage is an expectation written first (R1). It is measured on K01's probe and K18's
  dry run. A stage over budget is redesigned at its chapter, never discovered at K27.
- **Memory per worker** ≤ RAM / workers.

### 3.5 The instruments: which tool answers which question

Each instrument is read from its pointer (founder, 17:14:12Z): the global `performance.md` and
`code-verification.md`, SquishOS `docs/home/TOOLKIT.md`, Detective's DETERMINISTIC_SICP.

| question | instrument | source |
|---|---|---|
| is this function's behaviour pinned? | `just detective diagnose` / `converge` | `detective-protocol.md` |
| what could a pinned region safely become, priced and gated? | `just detective plan` | DETERMINISTIC_SICP §5; Wave 4 |
| which computation shape is it? | Detective's template recognizers v1, and §3.1's table | DETERMINISTIC_SICP §6; Wave 3 |
| how complex is it? | Radon (cyclomatic complexity, maintainability) and Detective's parsimony lenses, two independent channels, read as information and never a target | founder, 17:29:45Z and 17:30:14Z; DETERMINISTIC_SICP §4.1 |
| what does it cost, deterministically? | the budget bank: opcode counts over a size ladder, as a growth class, paired at behaviour delta 0. It counts Python instructions only, so native work is invisible to it. A native kernel therefore counts its own declared work and bytes until Detective's named C-call axis exists | DETERMINISTIC_SICP §7; Wave 2 |
| did a rewrite preserve behaviour? | `receipt` + `verify-rewrite` for Python; SAME for arrays, any backend, within one environment (K02); Detective's C gate for scalar C emissions | DETERMINISTIC_SICP §8; Wave 5 |
| where does time go: Python, native or system? | Scalene; py-spy (`--native`, `--gil`); VizTracer (cProfile where it is blind); pyinstrument; line_profiler | `performance.md` |
| where do bytes and temporaries go? | memray | `performance.md` |
| what is computed, handed on and consumed? | Hamilton, where "a value made and never consumed shows as dangling" | `performance.md`; THESIS §12.7 |
| are shapes and dtypes right at a boundary? | beartype + jaxtyping | `performance.md` |
| does compiling pay? | Numba as a probe; `cython -a`; ruff `PERF` | `performance.md` |
| an optimization proposal | Codeflash, kept only under SAME | `performance.md` |
| a speed claim | Detective's paired budget first, with pyperf as the complement | `code-verification.md`; TOOLKIT |
| a law of an abstraction | Hypothesis, which also drives the Rust and C kernels through their bindings | TOOLKIT |
| a pure decision's contract | Detective + CrossHair | TOOLKIT |
| a layer boundary; a dependency | Import Linter; deptry | TOOLKIT |
| C | clang (with `-fsanitize=address,undefined` in VERIFY), clang-tidy, clang-format, lldb; CMake + Ninja | TOOLKIT |
| Rust | rustup, `cargo clippy -D warnings`, rustfmt, rust-analyzer; PyO3 + maturin | TOOLKIT |

### 3.6 The plan, per operation

Designed here; each row is built and verified in its chapter.

| operation (chapter) | shape | size; hot and cold | language; layout | parallel unit; where |
|---|---|---|---|---|
| decode (K05) | IO-bound loop; codec | ~30 slices per series; disk-cold, one series hot | pydicom + native codecs; int16/uint16 C order | series per process; build and kernel |
| registration, resampling, N4 (K07, K08) | library-shaped optimization | a pyramid of 1.6 M-voxel grids | SimpleITK (C++); one deformable per study; N4 shrunk | ITK threads × workers declared; build and kernel |
| γ_s (K09) | masked reduction | reference-tissue zone voxels | NumPy | per series; kernel |
| reference build: median and MAD over N members per voxel (K09) | cache-hostile traversal, then memory-bound selection | N × 1.6 M × 4 B per series class (N = 150: ~1 GB); members cold, one tile hot | **C**: voxel-major tiles sized to L2, quickselect for the median then the MAD, both on the tile while hot; NumPy reference; Numba twin as a cross-check | tiles × cores; build (Mac Pro shards) |
| the fused deviation, identity and window pass (K10) | fused map + prefix sums | ~35 MB of study hot; references cold and slice-major | **Numba**, fused one-hit (x̃ never materialized) | slices (`prange`); kernel |
| zone lenses (K13); structure lenses (K20) | masked reductions; run scans along centerlines | zone crops | **Numba**; distance transforms in SciPy | per crop; kernel |
| hardness map and gate counts (K13a, K23) | privatized scatter-add | int32 counts per zone place × category over many normals | **Numba** with per-thread privatized counts and an exact merge; Rust if the privatized memory exceeds its contract | normals × shards; build |
| ledger writes and packed signs (K04, K12) | scatter-add; bit packing | under 200 rows per zone (ARCH §3.5.5) | **Numba** | per zone; kernel |
| components and morphology (K15) | library-shaped | crops | SciPy (C) | per study; kernel |
| geodesic centerlines (K19) | shortest path | crops | scikit-image's minimum-cost-path (Cython) | per structure; kernel |
| λ windows (K21) | summed-area tables | structure crops | **Numba**, one pass | per structure; kernel |
| perturbations (K22) | parallelize-map | K re-reads of crops | **Numba** `nogil` kernels under threads | perturbations; kernel (the R1–R3 and QZ families; R4 and R5 on escalation) |
| phantom planting (K11) | per-voxel forward model | host crops | **Numba** | phantoms; build |
| case-memory recall (K25) | batched scan of an indexed store | cases × coordinates int32 (~100 MB for the corpus, ARCH §3.5.5) plus bit planes; planes hot, rows cold | **Rust**: a popcount prefilter over the bit planes, then exact integer dot products and norms with the u128 level test on the survivors; cache-blocked over case blocks; NumPy/Python reference | case blocks (rayon); kernel and build |
| the level test's scalar core (K04) | exact integer predicate | scalars | Python reference; a C emission certified by Detective's C gate where a C kernel needs it | n/a |
| emission (K17); report parsing (K06) | ranking; regular expressions | 1,300 × 12; text | Python and NumPy; Python | n/a; kernel; build |

## 4. Contracts

- **`ComputeContract`,** as in §2. A contract test checks that every registered kernel has one, and that its
  declared encodings match its beartype and jaxtyping annotations.
- **The FFI conventions:**
  - arrays are passed C-contiguous, with their dtype and shape checked in Python before the call;
  - native code writes only into buffers it is handed, and allocates nothing it returns;
  - there is no global state;
  - errors come back as integer codes, mapped to named Python codes;
  - the GIL is released for the call.
- **The native numeric model:**
  - integer widths follow K04: u128 in Rust, and `__int128` in clang C for the squared level test;
  - floats use no fast-math and no FMA contraction (`-ffp-contract=off`) wherever a result enters SAME. The twin
    "sums in the reference's order, with strict floating-point arithmetic" (THESIS §12.5).
- **Cross-environment concordance.** Results across nodes or environments are compared as concordance, never as
  SAME, which holds within one environment. Decisions are equal except for listed boundary cases. FMA and
  vectorization differ between the Mac Pro (no FMA) and newer CPUs.

## 5. Implementation choice

- **Rust:** PyO3 + maturin (TOOLKIT), with rayon for the pool and the `numpy` crate for array views.
- **C:** C11 with clang; CMake + Ninja; `ctypes` for the binding, which is the standard library and releases the
  GIL. The toolkit vets no C++ binder, and the kernels need none.
  - C rather than C++, because Detective's emission gate speaks C, the ABI is plain, and the quickselect and
    tiling need no library.
- **Prior art:**
  - cell-tracking's `accel.py` was the registry's starting point; its four defects are avoided (K02);
  - Detective's Wave 5 `c_harness` and `run_c_gate` give the shape of the cross-language gate.

## 6. Verification

- **Every native kernel** has a reference (Python or NumPy) and SAME within each environment. It has Hypothesis
  properties driven through its binding, and sanitizer builds that run the property suite in VERIFY. Its gate
  is `clippy -D warnings` or clang-tidy, clean.
- **The contract test** covers every registered kernel.
- **The budget:**
  - Python-level paths: Detective's budget bank, as a growth class over a size ladder;
  - native kernels: their declared work and bytes, counted;
  - a speed claim: paired arms at behaviour delta 0, with pyperf as the complement;
  - Scalene and memray are investigators, never claims.
- **The registry's refusal paths** are tested.

## 7. Integration

- `just native` builds in VERIFY.
- `just native-linux` builds the DEPLOY artifacts by K01's measured path.
- `just same <kernel> --backend <b>` runs SAME.
- `just budget <kernel>` runs the paired budget.
- The kernel (K18) loads the native artifacts from its attached dataset, and the registry stamps the effective
  backends.

## 8. Acceptance

Written first: `acceptance/K02b.toml`.
- **Behavioural correctness:**
  - the toolchains build in VERIFY;
  - a skeleton C kernel and a skeleton Rust kernel each pass SAME against their references on generated inputs.
    K09's order statistics and K25's scan are the first real ones, built in their own chapters;
  - the sanitizer runs are clean;
  - the registry refuses a missing required backend;
  - the contract test passes.
- **Representation fidelity:** the DEPLOY artifacts import and run in a private Kaggle dry run, with the CPU
  baseline recorded.
- **Domain validity:** not applicable.
- **Performance evidence:** each node's cache sizes, CPU flags and cores, recorded (K01); the skeleton kernels'
  work and bytes, counted; no speed claim.
- **Evidence scope:** the toolchain versions and the three nodes.
- **Invalidation:** a toolchain version, a CPU baseline, or a Kaggle image change.

## 9. Open matters

- **Facts** (K01 measures them):
  - the Linux build path: Docker on the dev seat under emulation, a Kaggle utility notebook with the internet
    on, or another node;
  - Kaggle's CPU flags, cores and RAM;
  - the Mac Pro's L2 per core;
  - whether Numba's cache works under `/kaggle/working`.
- **Policy:** none.

## 10. Provenance and status log

- **Sources:**
  - DETERMINISTIC_SICP §1.1, §3.1, §4.1, §5–§8 and §12 (`detective-deterministic-sicp`);
  - THESIS §12.4–§12.7;
  - the global `performance.md` and `code-verification.md`;
  - SquishOS `docs/home/TOOLKIT.md`;
  - ARCH §2.4, §3.1, §3.2.6, §3.5.2 and §3.5.5;
  - the founder (15:24:53Z, 17:14:12Z, 17:22:59Z).
- **2026-10-02:** specified in revision 2, at the founder's request ("it's worth considering properly").
