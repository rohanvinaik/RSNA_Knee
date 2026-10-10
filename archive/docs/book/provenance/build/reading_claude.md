# Claude's design reading: the exact build of the knee (written before Codex sees it)

Date: 2026-10-02. This builds on the review accord of the same day (Claude + Codex, three rounds) on
`docs/KNEE_ARCHITECTURE.md`, and on the founder's rulings of 2026-10-02 listed in §0. It proposes the
**engineering design**:
- the module decomposition;
- the language and compute choice per module;
- interop and data formats;
- the pinning strategy;
- the build book's chapters and their order.

Labels: **[E]** evidence I checked, **[I]** my inference, **[F]** the founder's words.

## 0. The founder's directives this design must satisfy (verbatim, 2026-10-02)

- [F] "The questions should be resolved by building and observing, but your recommendations are generally in
  line with the intent. The bad stubs should be retired."
- [F] "In global CLAUDE.md, there's a whole list of tools for digging into how a function works, how code is
  written, code quality, and the considerations when using python vs rust vs C/C++ for different operations.
  It's important to think through what the best, most effective compute operation is for a task (e.g. for
  hypervectors, cache/memory operations can really speed stuff up, and JIT is basically a requirment). ACTUALLY
  look into it. Don't read the pointers in global CLAUDE and feel all satisfied--they're POINTERS, you READ what
  they point to. I'd also like to note that detective is a load-bearing tool to use, but use the one that's
  local, not the one that's installed from PyPI. Still follow the same instructions that global CLAUDE.md
  points you to. Lastly, in the "SquishOS" project, a full build plan is persisted past a session by writing
  it out as a "book", with each severable module as a "chapter", with the full intent and context laid out
  cleanly and persistently. I'd like us to use that. Once you read up on and understand what I mean by all
  the things I've said in this paragraph, I'd like you to write the key/useful rules that you can derive from
  it in a robust CLAUDE.md file in this project level, so you keep in mind the key apprach and how we should
  generally operate when working here to build a nice, best-language, interoperable, and clean, SICP-style
  codebase that's well-organized and fully mutant-pinned through Detective."
- [F] "Consult with codex on the exact design, then I think we can build out the plan, with each module in its
  best language, everything guided by the right tooling, and it all set up to be persistent past this
  session's context!"
- [F] "Cell tracking isn't always perfect, but it's a good start"
- [F] "We should design things fresh, only use older stuff when it's genuinely the best approach"
- [F] "Also get Codex to read your "chapters" and grounding context. If you've done it right, then
  codex--literally a different agent--should agree with you about how things should be done"
- And earlier, 2026-08-31, quoted in Detective's DETERMINISTIC_SICP §1.1: "Code should be small per function.
  Functions should be disentangled and independent. Code should be organized cleanly by intended function and
  type of operation. Computational efficiency should be optimized. Code should be written in the proper
  language and paradigm that appropriately executes the operation (e.g. Rust vs Python vs C++). There should be
  clean commenting and type-checking. Linters should have little to bite on."

## 1. What I read and what it says (the pointers followed) [E]

- **SquishOS `code-verification.md`.** The two-step: Serena diagnoses, Detective pins. `ty` after edits. Verify
  end to end and adversarially. The toolkit:
  - Hypothesis for laws of an abstraction;
  - Detective plus CrossHair for pure decisions;
  - Import Linter for layers;
  - deptry for dependencies;
  - py-spy, memray, viztracer and scalene to investigate;
  - Detective budgets plus pyperf for speed claims;
  - just for project verbs;
  - Rust through rustup, PyO3 + maturin "per experiment";
  - C/C++ with clang;
  - Racket `#lang sicp` and SWI-Prolog as the SICP workshop.
- **SquishOS `performance.md`.** "These are tools. WE organize." A run is written as named values, each
  computed once where it becomes known and handed to every consumer. Hamilton draws that graph, dev-side.
  Numba is a probe: whatever compiles under `@njit` is a candidate. "A candidate is kept only if a run-against-run
  check says the answers are the SAME."
- **SquishOS `detective-protocol.md`.** Detective is the scientist, I am the hands. Read the whole output. A
  refusal is a verdict. Extract the pure decision, total over literals, returning named codes. A generated suite
  is a characterization, so pair it with an intent test. Then ask what feeds the thing pinned.
- **SquishOS `verification-gates.md` and `repo-hygiene.md`.**
  - The gate is ruff, ty, pytest, plus pylint as a Sonar proxy.
  - Detective-pinned code reads ~100% on its decision core and lower overall; that is reported honestly.
  - Before a push: pip-audit with all extras, zizmor, a secret scan.
  - On setup: sp-repo-review and deptry.
- **SquishOS `context-maintenance.md`.** `AGENTS.md` is canonical; `CLAUDE.md` is `@AGENTS.md` plus Claude-only
  lines; the global rules are never restated.
- **SquishOS `docs/home/` (the build book).** It has:
  - a README with the module table in dependency order (*"one build, in dependency order; never slices"*);
  - commits labelled `home/Mxx` and a tag `home-Mxx` on acceptance ("status is computed, not written");
  - a CONSTRAINT_BLOCK that passes the Remove-X check;
  - the founding design; FOUNDING_PROMPTS (the operator's words, verbatim);
  - `modules/`: purpose, place in the thesis, substrate, prior art, the build, acceptance, open questions, status
    log;
  - `provenance/`: Claude's reading and the Codex rounds;
  - a checksummed REFERENCE_MANIFEST.

  Its forbidden moves include "Building a slice to 'prove' it" and "Status written as prose".
- **SquishOS `docs/home/TOOLKIT.md`.** One owner per role. Pyright is not a gate (ty is), mutmut is not used
  (Detective is), Radon is not used. The SICP reading is *Composing Programs* and *Software Design for
  Flexibility*.
- **Detective `README`, `ARCHITECTURE` §11 and `DETERMINISTIC_SICP.md` (+ constraint block).**
  - The local pair runs as `PYTHONPATH=<Detective>:<Wesker> python -m Detective.cli converge "PATH::FUNC"
    --project-root ROOT` [E: works from this repo; `--help`'s first block is binding: "NEW REPO? START HERE:
    detective regime"].
  - Style after behaviour, strictly. A style or port move is admissible only on a `pinned` region (a terminal
    COMPLETE certificate in `tests/detective/certificates.json`).
  - Efficiency means deterministic budgets: operation counts, a size ladder, paired arms at behaviour delta
    exactly 0. Never wall-clock.
  - `rewrite-in-<lang>` is gated by "warranted cross-language emission". It is built for C (`run_c_gate`), and
    its codec covers scalars only: containers are "codec v2, named", not built.
  - The bounded array domain: `np.ndarray`-annotated parameters, rank 1–2, ≤16 elements, finite b/i/u/f dtypes
    (`array_inputs.array_source_disposition`) [E].
- **The cell-tracking project** [E], "a good start, not perfect" [F]:
  - `accel.py`: a process-local `reference|jit` mode; `jit(fn)` returns `fn` itself in reference mode,
    otherwise `numba.njit(cache, nogil=True, fastmath=False, error_model="numpy")`; `serial_map` as the
    reference mapper.
  - `hdc/banks.py`: 16 banks × 512 Sylvester-Hadamard rows via `(-1)^popcount(i&j)`, a per-bank seeded
    permutation, `row_presence` as the exact decode.
  - A `tools` extra (Hamilton, viztracer, scalene, memray, pyinstrument, line_profiler, beartype, jaxtyping).
  - Detective from PyPI as a dev dependency. That last point is what the founder now overrides: use the local
    checkout.

## 2. Measured facts the design rests on [E]

- **Tags.** The competition strips every DICOM to an 86-tag allowlist. On 45 sampled series:
  - TR, TE, echo train length, ScanningSequence, SequenceVariant, ScanOptions and MagneticFieldStrength are
    present in 39 of 45;
  - vendor, geometry and FrameOfReferenceUID are present in 45 of 45;
  - InversionTime is on the allowlist but empty in the sample.

  All sampled spin-echo series are 2-D fast spin echo; one axial "FS fluid" series is a 3-D DESS gradient echo.
  The transfer syntaxes mix uncompressed, JPEG Lossless and JPEG 2000.
- **Inventory**, over all 4,407 training studies and 24,371 series (flags):
  - The flags take only two contrast classes, FS fluid-sensitive and non-fluid non-FS.
  - 57% of studies have exactly sagittal FS, sagittal non-FS, coronal FS, coronal non-FS and axial FS.
  - 100% have all three planes; 100% have axial FS; 94% sagittal FS; 96% coronal FS.
  - 23% have a same-plane pair of FS series.
- **Labels (official).** ACL and MCL mean "injury". The menisci mean "tear". Contusion means "bone contusion /
  bone bruise". How the test labels were produced is not stated.
- **Machine.** Dev is an M1 Max with 64 GB; Python is uv-managed (3.11–3.14 available); Numba 0.68 runs on 3.12,
  3.13 and 3.14; the Rust toolchain (cargo 1.99) is in the login-shell PATH; Docker 29 is present; `just`
  1.58.
- **Kaggle.** The kernel is Linux x86_64, internet off, at most 9 h. Its Python, NumPy, Numba, pydicom codecs and
  SimpleITK availability are **not yet measured**.
- **The current repo.**
  - `src/RSNA_Knee/` holds `scoring`, `kneediff`, `platonic_reference`, `anatomy`, `hdc_encoder` and
    `report_parser`. Detective pins exist on seven pure functions; 45 tests pass.
  - The venv is built on conda's Python 3.14.6, which Detective's EP-C4 says to replace with a uv-managed
    interpreter.
  - The gate is not configured: generated suites and docs are not excluded from ruff, and there are no dev
    dependencies.

## 3. The engineering design

### 3.1 A fresh package, legacy quarantined

New code goes in a fresh package `src/knee/` (import name `knee`). The old `src/RSNA_Knee/` is legacy. Each
chapter decides, with an argument, whether a legacy unit is reused (moved into `knee`, re-converged and
re-certified) or retired. When `RSNA_Knee` is empty it is deleted. The Kaggle kernel imports only `knee`.

*Why:* founder, "design things fresh"; a module's name and docstring are a contract later agents read (THESIS
§12.5).

### 3.2 The layers (an abstraction barrier per layer; Import Linter contracts)

Bottom to top. A layer imports only layers below it.

```
 kernel                      the Kaggle entry (production path only)
 harness · teach · text      evaluation, teaching, report reading: TRAIN-ONLY, never imported by kernel
 emit                        ranks from decision words (pure)
 agency                      the bodies: decide or abstain per finding
 committee · memory · censor witnesses & dependence · cases & recall · negative knowledge & the split
 explain                     the explanation loop and the kept record
 reader · perturb · hardness · lens   identity/conflict words · stability · blindness in health · questionless measurements
 delineate                   patient-specific containers and identity evidence
 ledger · law · signature · deviation  one language · quantitative branch · sign patterns · KneeDiff
 reference · atlas           population references · templates, zones, landmarks (built offline, loaded at test)
 register · frame            the bounded utility · study frame and plane grids
 ingest · store              DICOM headers/pixels/geometry/inventory · content-addressed artifacts
 accel · vocab               reference|jit mode, SAME harness · closed vocabularies and codes (one owner each)
```

- Every package with decisions has a `decisions.py`: total functions over literals returning named codes.
- Plain functions are named for the value they return and take as parameters the values they consume, so the
  run's graph can be drawn dev-side (Hamilton) without production importing Hamilton.

### 3.3 The best language per operation (the rule, then the per-module choice)

**The rule:**
- Python orchestrates and decides.
- NumPy/SciPy does whole-array math.
- Numba JIT does every custom numeric loop. It is the default for hot paths and required for the ledger and
  voxel kernels. It compiles on Kaggle, so no binary ships.
- Rust (PyO3 + maturin, abi3, a manylinux x86_64 wheel built in Docker) only where a measured budget shows
  Numba falls short: bit-level SIMD, exact 128-bit integer tests at scale, GIL-free threads over long-lived
  stores.
- C/C++ only as existing libraries: ITK via SimpleITK, the DICOM codecs.

Every kernel is first a Python reference with an explicit operation order. Its cores take rank-1 or rank-2
`np.ndarray` arguments so Detective's bounded array domain can pin them; volume wrappers are thin loops over
those cores. The accelerated twin must pass the differential SAME harness: Hypothesis-generated inputs plus
recorded real frames, with integer and ordinal outputs equal, and float outputs bit-equal or within a stated ULP
bound written before the run.

**Per module (initial choice, each confirmed by the chapter's measurement):**

| module | dominant operation | language / compute | memory layout |
|---|---|---|---|
| ingest | header parse; JPEG-LS/J2K decode; geometry | Python + pydicom with native codecs (pylibjpeg-openjpeg / -libjpeg, or gdcm: whichever the Kaggle image has, measured); process pool per series | stored ints as int16/uint16; per-series affine float64 |
| frame | resample to plane grids | SimpleITK (C++) or `scipy.ndimage.map_coordinates`, chosen by a SAME check and a budget | C-contiguous float32 volumes, memory-mapped `.npy` |
| register | rigid intra-study alignment; affine + coarse B-spline to template; NCC check | SimpleITK (C++), Python orchestration; ITK threads | transforms kept as files, keyed by content |
| atlas | template building, zone painting, landmarks, multi-atlas vote | Python + NumPy/SciPy, offline | uint8 zone labels; uint8 vote fractions ×255 |
| reference | per-voxel robust center/spread over N normals | Numba kernel over slabs (selection-based median/MAD), offline | voxel-major blocks sized to L2; float32 outputs, int16 n |
| deviation | z, licensed record, windowed sums | Numba fused single pass (no temporaries); integral sums | float32 z, uint8 codes, int32 running sums |
| signature | per-place sign pattern across co-registered series | Numba pass + pure Python decision table | uint8 pattern codes |
| law | closed-form inversions where identifiable; delta-method σ | NumPy closed forms; Numba for per-voxel iterative solves | float32 parameters + σ |
| ledger | scatter-add rows into count tables; pack sign planes; cosine; decode | Numba (scatter-add, packing); BLAS float64 GEMM for dot products (exact below 2^53, asserted); exact integer level test in Python ints on the borderline | int32 count tables (rows contiguous per zone), uint64 sign planes, float64 norms cached |
| delineate | containers from bones, notch and attachments; geodesic and region operations inside them | Numba + SciPy ndimage | uint8 masks, bounding-box crops |
| lens | contact counts, centerline runs, angles, volumes, neck paths, lines, shares | one Numba kernel per lens core + Python decisions | crops of the residual; int32 counts |
| hardness | accumulate per-place rates over normals | Numba scatter-add, offline | per-place int32 count volumes per lens × class × regime |
| perturb | re-read structures and candidates under steps | reuses lens kernels; nogil threads | crop-local |
| reader | windowed energy Q; identity evidence | Numba windowed sums; pure decisions | — |
| explain | bodies, masks, nested objects, post-checks | SciPy ndimage.label (C) + Numba masks; Python orchestration | uint8/int32 label crops |
| committee, censor, agency, emit | decisions | Python (pure, pinned) | — |
| memory | recall of a profile against many cases | BLAS GEMM + exact level test first; **Rust admitted on measurement** (popcount prefilter over packed signs, i128 exact tests, rayon) | cases × rows int32 matrix (row-major), uint64 sign planes |
| text | multilingual report → localized ternary calls | Python (regex and lexicon), train-only | JSONL |
| kernel | the run over test studies | Python, study-parallel processes, JIT warmed once | streams; nothing kept in RAM beyond one study |

### 3.4 Data and artifacts

- **The store.** `data/store/<stage>/<stage_version>/<key>/…`, content-addressed by the input digests plus the
  stage version, with a `manifest.json` per artifact: inputs, code digest, parameters, what produced it.
  Resolved at call time, never hardcoded.
- **Arrays** are `.npy`, memory-mappable, with explicit dtypes.
- **Records** (the kept record, cases, calls) are JSONL with a schema version.
- **No zarr and no Parquet** unless a chapter measures the need (one dependency per proven role).
- **Kaggle artifacts**, each a private dataset with its digest manifest: atlas, references, hardness map, case
  memory, frozen bars and levels, and wheels.

### 3.5 Pinning (fully mutant-pinned through the local Detective)

- Every `decisions.py` function is converged to a COMPLETE certificate and paired with an intent test.
- Every kernel core is converged in reference mode, inside the bounded array domain. Where that domain cannot
  express it, Hypothesis laws and small characterization tests carry it, labelled as such.
- JIT and Rust twins answer to the SAME harness.
- I/O shells get tiny synthetic-fixture integration tests through the real entry point.
- `tests/detective/certificates.json` is versioned.
- Detective runs in accel reference mode.
- The gate (`just gate`) runs ruff (pinned version; `tests/detective` and the canon docs excluded from format),
  pytest, lint-imports, with ty advisory, plus cargo fmt/clippy/test when `native/` exists.

### 3.6 Python version

Measure the Kaggle image first (K01). Dev runs a uv-managed CPython of the same minor version if ≥ 3.12,
which Detective requires; otherwise 3.12 with `target-version` set to Kaggle's minor version and a kernel smoke
test as the proof.

## 4. The book: chapters in dependency order (never slices)

| chapter | delivers | depends on |
|---|---|---|
| K00 | founding record: the book, the rules, the manifest | — |
| K01 | toolchain and runtime: uv env, gate, `just`, Import Linter, local-Detective `regime`, accel mode, SAME harness, `native/` skeleton and a manylinux wheel, **the Kaggle runtime measured** by a private dry-run kernel | K00 |
| K02 | panels, harness and scorer: the 12 columns bound; study roles and rotation; the all-questions recognition table with bounds; macro-AUC (reuse decision on `scoring.py`) | K01 |
| K03 | corpus and ingest: the store; fetch (API, bundle); headers for all series; tag survival; inventory, regime keys and identifiable sets (within plane and across planes); pixel decode to stored values | K02 |
| K04 | frame and registration: chirality, shared box, plane grids, intra-study rigid alignment, template registration with kept transforms, NCC landmark check, check registration, constraint readings | K03 |
| K05 | atlas: templates per plane, zones, landmarks and attachments, multi-atlas vote fractions; the founder's eye-check | K04 |
| K06 | text oracle: parser (reuse decision on `report_parser.py`), localized ternary calls, hedges, morphology, sizes; the softness table; L5 co-occurrence in text | K02 |
| K07 | population references: the report-negative pool, the founder's sample check, role partition; robust references per class × regime × place with fallback; the historical make-or-break rerun | K04, K06 |
| K08 | deviation and signatures | K07 |
| K09 | the law: the quantitative branch where identifiable; named offsets; typed misfit; leave-one-series-out | K08 |
| K10 | phantoms: forward-modeled lesions, near misses, artifacts, misregistrations; amplitude response | K09, K05 |
| K11 | the ledger: carrier, layout, count tables, packed signs, exact cosine, decode, zone words | K01 |
| K12 | delineation: containers, identity evidence I, visibility certificates, placement uncertainty | K05, K08 |
| K13 | lenses: the questionless set, with common silences and provenance | K11, K12, K10 |
| K14 | perturbation: families, magnitudes from measured error, stability, flip axis, sandwich, honest limits | K13 |
| K15 | hardness map: building and checking halves; rates with bounds; law-named admission; statuses | K14, K07 |
| K16 | identity–conflict reader: (I, D) words; sweep twin; the \|z\| survival profile; shapes in health | K12, K08, K10 |
| K17 | committee: per-acquisition witnesses, dependence graph, multiway checks, entitlement, outcomes | K13, K15 |
| K18 | explanation loop: provisional take, confirmed object and finding decision distinguished; explanation masks; nested objects; the post-check; the kept record | K16, K17 |
| K19 | memory: cases, buckets, a specified null mechanism for radii, recall, routed procedures; the recall kernel (Rust by measurement) | K11, K18, K06 |
| K20 | censors and the split: three tiers of negative knowledge; near misses; the four-way split | K19, K15 |
| K21 | agencies and teaching: five agencies plus placement records; curricula; sheets; trajectories in rotation; H2's bridge on the hard pairs | K20, K06 |
| K22 | emission: registers; Law 7 literal by default; ordered variants computed and measured (Q4 resolved by observation, ruled by the founder) | K21 |
| K23 | the kernel and dry run: packaging, the private full run, the runtime budget, the expected score surfaced; never auto-submit | K22, K01 |

**Parallelism:** K06 with K03–K05; K11 with K03–K10.

**The open questions, each owned by a measurement:**
- Q2 (λ): K16.
- Q3 residue (OA marrow lesions, Baker's size): K06, from report language and gold.
- Q4: K22.
- Q5: K21.
- Q6: K03.
- Q8 (independence bar): K17.
- Q11: unknowable from the data; reported.
- Q12: K07.
- Q13: K13.
- Q14: K09, K14, K15, K10.
- Q15: K04 and K17 records.
- Q16: K11 (share the carrier with cell-tracking only if the contracts match).

## 5. Where I am least sure [U]

1. **Chapter granularity.** 24 chapters may be too fine: K08 and K09 might merge, and K14–K16 might merge.
2. **Whether Rust earns a place at all.** The case memory may be small enough for BLAS plus a Python-int border
   test. The measurement decides.
3. **The SquishOS "never slices" law against the review's "vertical slices".** I follow the founder's book
   convention, whole modules in dependency order, and let each chapter's acceptance run on real data. Is that
   enough to exercise the joints early?
4. **Whether Detective's bounded array domain** (rank ≤ 2, ≤ 16 elements) is enough to pin the kernel cores
   meaningfully, or whether property tests must carry most of the kernel layer.
5. **Python version parity with Kaggle,** which is unknown until K01.
