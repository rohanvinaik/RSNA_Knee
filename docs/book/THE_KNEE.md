# The Knee — the founding design of the build

**What this is.** The founding design of the build, written 2026-10-02. It does six things:
- restates the mechanism at data-flow level (§1);
- names exactly which canon passages the 2026-10-02 accord amends (§2);
- sets the engineering design (§3) and the compute topology (§4);
- sets the measurement regime (§5);
- records each decision with its deduction (§6);
- lists what stays open (§7).

Each chapter in `chapters/` builds one severable module against this document.

**Authority.**
- The founder's words win: `FOUNDING_PROMPTS.md` and `docs/FOUNDING_RECORD.md`.
- This document amends the canon only where §2 says so, explicitly. Everywhere else the canon binds:
  - `docs/THEORY_OF_THE_CASE.md`, whose Laws 1–8 bind unchanged;
  - `docs/KNEE_ARCHITECTURE.md`;
  - `docs/canon/`.
- Status is never written here. It is computed (`AGENTS.md` → *Where truth lives*).

**How it was reached.**
- *The review* (`provenance/review/`): Claude's reading of KNEE_ARCHITECTURE, then three Codex rounds. It ended
  with an accord on ten changes; Q4 was left to the founder.
- *The design* (`provenance/build/`): Claude's reading of the house doctrine (every reference the global rules
  point to, read in full), then two Codex rounds. It ended with an accord; Q4 is again the only open matter.
- Both sides consulted Codex model-only (GPT-6-Astra, medium effort), with Claude's own reading written first.

---

## 1. The mechanism, at data-flow level

One study, from its files to its twelve numbers. Each arrow is a named value, computed once where it becomes
known.

1. **Ingest.** Each series' DICOM headers (an allowlist of 86 tags) give:
   - a header record: timing (TR, TE, echo train), sequence family, fat suppression, field strength, vendor,
     geometry;
   - the stored pixel values, with their rescale;
   - a patient-space affine.

   The study's series give its **inventory**, its **regime key** (field, vendor, sequence family), and its
   **identifiable set**: which physical quantities its contrasts could pin, within a plane and across planes.
2. **Frame and registration** (the one bounded utility, THEORY Law 3).
   - Chirality is made canonical (left knees mirrored to right), and the study's series share one box.
   - The series are rigidly aligned to each other (patient motion).
   - One coarse deformable transform carries the study onto the template. It is **kept**.
   - Every series is resampled onto its own plane's canonical grid.
   - Constraint readings say whether the comparison is valid there: landmark NCC, a check registration from a
     second plane, chirality.
3. **Atlas.** Template-space zones (structures, compartments, recesses, marrow subregions, reference tissues),
   landmarks and attachments. Multi-atlas votes are kept as numerators and denominators.
4. **Population reference.** For each *series class × regime × place*: a robust centre, a spread and a count,
   squashed from report-negative candidate knees. The pool is split by role: reference, nulls, chance, hosts,
   checking.
5. **Deviation** (KneeDiff). At each place, z = (x − μ) / √(σ²_bio + σ²_meas + var(μ̂)).
   - A place the reference licenses is **compatible**, recorded as licensed. Compatible is *never* "excluded":
     a small lesion can sit inside a wide spread.
   - What is left is the **residual**.
6. **Signature.** At each place, the pattern of deviation signs across the co-registered series, read against
   the signs each series' own timing predicts for each tissue. Unnamed patterns are kept.
   - *Optional:* the quantitative law (chapter K24) inverts the MR signal equation only where the series
     identify the quantity.
7. **Delineation.** From robust neighbours (bone surfaces, the notch, attachment sites), a container per
   structure.
   - Identity evidence **I** is read on the *patient's own data*, never on data blended toward the prior.
   - Torn, displaced and signal-altered structures remain admissible.
   - Each structure carries a visibility certificate and its local placement uncertainty.
8. **Lenses.** Questionless measurements, each of one thing: a recess's fluid volume, a marrow edema-signature
   extent, the slices on which signal touches a meniscal surface, a ligament's longest run without fibrous
   signature, an angle, a neck path, a line, a share, a gap. Each emits a value, a quantized digit, silences
   with their causes, and the series that produced it. A lens states no sign: the agencies hold the signs.
9. **Readers of health.**
   - The **hardness map** says where each lens reads falsely or goes blind in health. It is built from
     observations on normals and admitted only with a law-named predictor.
   - **Perturbation** (frame and quantizer steps) gives each reading its stability and flip axis.
   - The **identity–conflict reader** combines I with D, the windowed deviation energy, and names the four
     legacy words.
10. **Explanation loop.** Candidate bodies are taken as provisional takes, become confirmed objects only by
    concurrence of independent witnesses, and are explained by reversible explanation records. Objects nest
    (a line inside edema) and overlap. Numerical subtraction happens only where a contribution law exists
    (partial volume). Post-checks find rings, holes and lobes. The site search and reaching inside follow,
    then the last look; the kept record is what results.
11. **The society.**
    - **Committee:** one witness per acquired series, with an explicit dependence graph (shared causes).
    - **Memory:** cases with their sources, recalled within trust radii set by a *stated null mechanism*.
    - **Negative knowledge** in three tiers: physical impossibility; exclusion qualified by what the series
      could see; supportive sign.
    - **The split:** input error, instrument, normal variant, pathology.
    - **Five agencies** (fluid, marrow, fibrous structures, compartments, every finding), plus placement
      records. Each decides or abstains per finding.
12. **Emission.** Registers: decided present; open; decided absent.
    - The open register is **exactly 0.5**, by Law 7, until the founder rules on Q4.
    - Ordered variants are computed and *reported*, never submitted unruled.
    - A pure function writes the twelve columns of `submission.csv`.

## 2. The accord: exactly what it amends

The ten agreed changes (`provenance/review/codex_round3_answer.md`), each with the canon passage it amends, what
replaces it, and the chapter that builds it. Anything not listed stands.

| # | change | canon passage amended | replacement | chapter |
|---|---|---|---|---|
| 1 | Layer 1 is not the general substrate | KNEE_ARCHITECTURE Part 3 §3.3 (the law as the computation) and §3.4 (KneeDiff in physics space) | per-series-class references and signatures carry the substrate; the quantitative law runs only where a declared forward operator has rank and conditioning, and its empirical offsets are named as offsets, never as physical coefficients | K09, K10, K24 |
| 2 | patient-specific delineation | KNEE_ARCHITECTURE §1.5 and §2.2 item 2 ("Structures are found for free"); §2.10's zones as boundaries | the atlas proposes search regions; containers come from robust neighbours; identity evidence comes from patient data | K07, K08, K19 |
| 3 | negative knowledge in three tiers | Table 1.7 and §2.8 rule 3 (the licensed 0 as "exclusion"); §4.1 (T1-bright marrow as the *senior* excluder of edema); Table 2.8b (the "Counts" and "Rules out" columns); Table 5.10 ("a fracture lies within edema" and "no neck, no Baker's" as absolute) | physical impossibility (absolute); observation-qualified exclusion (coverage and resolution certificates required); supportive sign. T1 confirms edema and, together with the suppression map, rejects the fat explanation. Fat-suppressed fluid-sensitive series are the sensitive pathway, and mild bruises can be T1-occult. "Licensed" never means "excluded". With the official labels, an intact band cannot exclude ACL or MCL *injury* | K14, K20, K23 |
| 4 | nested and overlapping objects; explanation records | L1's "one tissue and at most one lesion per voxel" (§1.4, §2.2); §4.4 (the take subtracts the object's signal; Table 4.6's halos) | ownership of measured contribution kept apart from membership in findings; reversible explanation masks; subtraction only under a stated contribution law; edema is not a halo of a fracture line | K15 |
| 5 | identity separated from conflict | §4.5 (the closed form as the detector; the words as bands of ‖z‖²/p̂_S; the placement margin as identity); THEORY II.5 ("Peak height = confidence") | the four words are legacy routing codes for cells of (I, D). I is identity evidence on patient data (K19). D is the windowed reference-conflict energy, named honestly. The \|z\| survival profile from the thresholded sweep is a reading in its own right. Corrections: sampled MONO_DOWN needs E > 10p̂, not 5p̂; "fidelity" exceeds 1 when E < p̂; the SURE remark is a conditional fixed-shrinkage analogy | K21 |
| 6 | questionless members | §2.8 rule 4 (a lens declares its direction); Table 2.8b; §5.8 (lens families chosen by prevalence-error minimization); §5.5 (the trust radius set to exclude every opposite-answer example) | lenses emit measurements and visibility; agencies hold the signs; no seating by prevalence; a trust radius comes from a specified null mechanism (what it preserves, conditioned on visibility and context, with bucket size accounted for); hard negatives become near-miss censors | K13, K20, K25 |
| 7 | per-acquisition witnesses; explicit dependence | §5.3 (pairwise gate; independence classes; GenomeVault's φ < 0.25 bar); §6.2.2 ("κ against reports is an upper bound") | witnesses stay per acquisition, upstream of any joint reconstruction; dependence is a graph of shared causes with multiway checks; no imported bar; "insufficient" where independence is not established | K14, K23 |
| 8 | provenance and roles | §5.5's "gold positives localized to the zone"; §5.7 (a successor is whoever holds the most deviant mass); §6.2.5; "true normals" | gold is study-level only; localized authority comes from report calls (noisy) or the founder; an ambiguous successor stays unresolved; the pool is "report-negative candidates", split by role; gold already shaped the parser's rules and is not untouched evidence for parser-derived claims | K03, K06, K09 |
| 9 | emission keys | §6.1.4 (c₊ as the first key); §6.1.1 ("strictly monotone") | witness-set comparability, never a raw series count (that would rank protocol richness); "strictly increasing"; Law 7's literal 0.5 as the submitted default | K17 |
| 10 | contracts and build order | §6.6 (Phases 0–9: Phase 5 gated on products of Phases 6–7); the Glossary's "concurrence is the only commit" against §5.3's SINGLE; falsifier 7's wording; §3.4.2's variance arithmetic; a structure-alone run with no decision path | this book: chapters in dependency order, with first light early; provisional take, confirmed object and finding decision kept distinct; falsifier 7 tests stable meaning within a regime; a coherent variance decomposition including the centre's uncertainty; K16's case-free decision path | all |

**What stands.**
- THEORY Laws 1–8.
- The two references, never merged (KNEE_ARCHITECTURE §1.8).
- The three zeros (§3.5.3) and the exact ledger (§3.5).
- Cases, never prototypes (§5.5).
- Disagreement kept open, never tie-broken (§5.3).
- The hardness map's law-named admission (§4.2).
- The exact AUC accounting of the open register (§6.1.5, facts 1–3).
- The falsifiers (§6.4), with falsifier 7 reworded.

**Facts the accord added** (`provenance/review/reading_claude.md` §3):
- *The official label definitions:* Meniscus means **tear**; ACL and MCL mean **injury**; Contusion means
  **bone contusion / bone bruise**. The definitions do not say whether OA marrow lesions count, nor give a Baker's
  size.
- *The submission columns*, which are bound.
- *The 86-tag allowlist.*
- *The series inventory.*
- *The method that produced the test labels is not published* (Q11: unknowable from the data).

## 3. The engineering design

### 3.1 One fresh package, four areas, enforced layers

- **The package.** New code lives in `src/knee/` (import `knee`). Legacy `src/RSNA_Knee/` is quarantined.
  - A **migration ledger** (`docs/book/MIGRATION.md`) carries one row per legacy unit: the old symbol, its
    production consumers, its replacement, the reuse-or-retire decision with its argument, and the retirement
    acceptance.
  - An Import Linter contract forbids `knee` from importing `RSNA_Knee`.
  - The Kaggle kernel imports only `knee`.
- **Four areas, kept apart:**
  1. *schemas and pure operations*: types, vocabularies, decisions, kernels' references;
  2. *runtime readers and decision bodies*: what the kernel runs per study;
  3. *offline artifact builders*: atlas, references, hardness map, case memory, built from many studies and
     loaded at run time;
  4. *orchestration and verification*: runners, the harness, teaching, report reading.

  The orchestrator injects committee outcomes and recalled procedures downward as records. Nothing imports
  upward.
- **Train-only code is unreachable from the kernel.** Teaching, report reading and the harness can never be
  reached from the kernel's import graph, transitively; Import Linter's forbidden contracts enforce it.
- **Decisions** live in cohesive named modules, beside the code they serve. Each is a total function over
  literals, returning a named code.
- **Functions are named for the value they return** and take the values they consume, so the run's graph can be
  drawn dev-side (Hamilton plus Graphviz) without production importing Hamilton.

### 3.2 The best language per operation

The founder, 2026-10-02: "the best, most effective compute operation is for a task (e.g. for hypervectors,
cache/memory operations can really speed stuff up, and JIT is basically a requirment)".

| operation kind | default | admitted alternative, by evidence |
|---|---|---|
| decisions, orchestration, records, serializers, report parsing | Python | — |
| whole-array math with no custom loop; established image and geometry operations | NumPy, SciPy, SimpleITK (their contracts written down first) | — |
| custom repeated numeric loops: voxel lenses, component laws, windowed sums, the ledger's scatter-adds and packing, robust per-voxel statistics | **Numba JIT** (`njit`, `nogil`, `cache`, `fastmath=False`); required for hypervector, ledger and voxel work | — |
| long-lived indexed stores and scans where bit-level SIMD, exact wide integers, GIL-free threads or explicit memory layout are *measured* to matter (the case memory is the candidate) | Numba plus BLAS first | **Rust** (PyO3 + maturin), or custom C/C++; Linux x86_64 wheels built and tested in the target |
| DICOM decoding | pydicom with the native codec the target image has, chosen by transfer-syntax UID | — |

A kernel's chapter records: the measurement that chose its language; its memory layout (dtype, contiguity, axis
order); its scratch bytes and bytes scanned; its block rationale; and its concurrency (process × thread
ownership, with nested ITK, BLAS and Numba threads declared). No absolutes like "no temporaries" are claimed;
the bytes are measured.

### 3.3 Reference first, then the accelerated twin

- **Every kernel exists first as a plain Python reference with an explicit operation order.** It is pinned
  through the local Detective where its inputs are reachable, and carries Hypothesis laws.
- **The backend registry** decides how kernels run:
  - the backend is configured before any kernel binds;
  - the requested and the effective backend are recorded in every run's provenance;
  - a required backend that is unavailable refuses with a named code, never a silent fallback;
  - JIT compilation happens at a declared warm-up, and its cost is measured apart from warm execution.

  It is built fresh. Cell-tracking's `accel.py` was the starting point, and its four defects were found in
  review: decoration captured the mode too early; the "compiled" flag was set before compiling; it fell back
  silently; and error-model differences were unmentioned.
- **SAME is decision-preserving.**
  - Codes, row assignments, case membership, ties, witnesses and decisions must match exactly.
  - A float tolerance, stated before the run, may cover intermediate values only. It never authorizes a changed
    threshold outcome. Values within the stated error of a threshold are routed to the reference.
  - Each kernel's SAME spec states NaN, ±inf, signed-zero, overflow, exception and mutation behaviour.
  - A SAME result is bounded evidence over its exercised inputs. It is never called a Detective cross-language
    receipt; Detective's C gate covers scalar signatures only.

### 3.4 Numeric contracts

- **The exact ledger** (THESIS §6, §12).
  - Each layout declares the coordinates R included in a comparison (every row of every bank the question
    reads), a per-coordinate count limit C, and level numerators and denominators |a|, |b| ≤ 2^10.
  - With non-negative integer counts, R ≤ 2^9 and C ≤ 2^20, dot ≤ R·C² ≤ 2^49 < 2^53. So binary64 products and
    partial sums are exact in any order, and the backend must provide IEEE binary64 semantics.
  - The level test b²·dot² ≥ a²·‖u‖²·‖v‖² stays ≤ 2^118, so it runs in i128 or Python int.
  - Limits are checked on the integer inputs *before* conversion to float, never by an assertion after rounding.
  - A missing-bank mask selects the same coordinates for the dot product and both norms.
  - Packed sign planes may *order* scans. They drop a case only on a proved bound.
- **Deviation.** z is float32 for storage and float64 in the reference arithmetic. The threshold test follows the
  SAME routing rule.
- **Integer widths.** Every count, integral sum and reference sample count declares its width and its overflow
  behaviour.

### 3.5 Artifacts, caches and the data policy

- **Every artifact declares** its shape, dtype, endianness, axis order, units, coordinate frame, transform
  direction and composition order. Status fields are explicit: never NaN as "unknown". Stable IDs link each
  finding to the acquired evidence behind it.
- **Storage.** Arrays are `.npy`, memory-mappable. Records are JSONL with a schema version, in canonical
  serialization. Publishing is atomic and detects interrupted writes; manifests are validated.
- **Two kinds of storage.** The store is `data/store/<stage>/<stage_version>/<key>/` for immutable artifacts.
  Writable caches live elsewhere.
- **Cache keys** include input contents, parameters, reference and layout versions, the code digest, the
  relevant library, backend and node environment, and seeds.
- **The data policy** follows the competition rules (4.a: any purpose under the RSNA MIRA license; 4.b.1: never
  available to non-participants; no private sharing outside the team).
  - Nothing derived from competition data enters git: no pixels, report text, study lists, references, maps,
    fixtures, traces or Detective captures built from it.
  - Synthetic, independently authored fixtures do go in git.
  - Derived artifacts live in `data/` and in private Kaggle datasets attached to our own kernels, each with a
    content inventory, lineage and checksums.

### 3.6 Two environments

- **VERIFY:** a uv-managed CPython ≥ 3.12 (Detective needs it), with dev tooling, pinned.
- **DEPLOY:** Kaggle's actual interpreter and package versions, measured in K01 and reproduced locally with uv
  where possible, pinned separately.

Production imports, kernel contracts and the real entry point run in DEPLOY. The private Kaggle dry run is
deployment acceptance on the environment and inputs it exercised; it is not proof of general correctness.
`target-version` is a lint setting, never a compatibility claim.

### 3.7 Pinning and verification

**The local Detective** (`AGENTS.md`, override 1):
- `just detective` runs `PYTHONPATH=$HOME/tools/Detective:$HOME/tools/Wesker python -m Detective.cli` in VERIFY
  and records the checkout's identity (`detective 1.1.1 (Wesker 1.1.1)` plus the git revisions).
- It keeps complete stdout and stderr and preserves the exit status. It does not refuse pipes, since agent tools
  capture through pipes. Logging is not proof of reading: reading the whole output remains the protocol.
- It never runs alongside a pytest gate or another converge.
- It runs with the backend registry in reference mode.

**The scope, stated truthfully** (`provenance/build/codex_round2_answer.md` A3):
- input synthesis renders literals and bounded arrays (rank 1–2, ≤ 16 elements, finite bool/int/uint/float);
- functions over domain objects are reached through real arguments captured from tests, and reachable does not
  mean pinned;
- standing uses Detective's own vocabulary: pinned, pinned_incomplete, refused, pinned_stale,
  pinned_unverified, unpinned. The terminal converge verdict is recorded separately from the current
  behaviour status.

**Beside every generated suite:**
- hand-written intent tests;
- Hypothesis laws, with stateful tests for stores and caches;
- CrossHair on supported pure contracts;
- adversarial integration tests through the real entry point, covering null, empty, malformed and boundary
  inputs;
- a collection check that the generated suites actually run.

**The gate** is `just gate`: pinned ruff for check and format, with generated suites and the canon docs
excluded from format; pytest; lint-imports; deptry; ty, advisory; cargo fmt, clippy and test once `native/`
exists. Before a push, the global supply-chain checks also run.

### 3.8 Instruments

- **To investigate:** py-spy, memray, viztracer (its thread and filter blind spots acknowledged; cProfile where
  it cannot see), and pyinstrument. They live in a dev-only extra.
- **To claim:** Detective's deterministic budgets, paired against the incumbent at behaviour delta 0, with
  pyperf as the complement. A budget names its scope: Python opcode counts miss native work, so it also records
  deterministic work and byte counts, or says "unmeasured".
- **Run events:** local structured events carrying finding IDs. OpenTelemetry stays deferred, per TOOLKIT.

## 4. Compute topology

| node | role | measured facts |
|---|---|---|
| the M1 Max (dev seat) | interactive work, VERIFY environment, the lead's Serena | 64 GB; arm64; macOS |
| **squishhub, the Mac Pro** (founder, 2026-10-02: "for heavy compute, I have the Mac Pro sitting around") | always-on batch worker: header census, fetch and decode, registration of the corpus, reference, hardness-map and perturbation builds | MacPro6,1; Xeon E5-1650 v2, 6 cores / 12 threads, x86_64 with **AVX but no AVX2**; 16 GB ECC; ~152 GB free; macOS 12.7.6; root; tailnet and LAN paths (`squishos-fleet card squishhub`, measured 2026-09-26; its verification is stale until re-run) |
| Kaggle | DEPLOY: the kernel | Linux x86_64, internet off, ≤ 9 h; packages and versions measured in K01 |

How the Mac Pro is used, through SquishOS only:
- `squishos-fleet card | identify | verify | run | put | get`, and `squishos-compute run | jobs | logs | status`
  (`~/Projects/SquishOS/docs/runbooks/fleet.md` and `compute.md`, which are authoritative).
- There is no cross-node scheduler (SquishOS marks orchestration NOT-BUILT). So batch stages are **shardable by a
  deterministic study partition**, node-agnostic, and content-addressed with the node's environment in the key.
- Shards from different architectures (arm64 and x86_64) are merged only after a measured cross-node SAME check
  on a sample. Registration optimizers, libm and BLAS may differ across architectures.
- Its 16 GB bounds the per-worker residency, so the concurrency is declared per node.
- No secret is copied to the node without the founder's word at that moment. The Kaggle token's placement there
  is a K01 step put to the founder.

## 5. The measurement regime

- **Panels** (K03):
  - **G**, gold: the 58 expert re-reads, study-level only, in rotation folds;
  - **N**, report-negative candidates, split by role (reference, nulls, chance, hosts, checking, and
    template-building versus template-checking);
  - **T**, report-labeled *teaching* studies: the only report-labeled studies that build anything (cases,
    quantizer edges);
  - **R**, report-labeled studies held out of every store, T included, and used only to judge. R and T are
    disjoint;
  - **P**, phantoms: their truth defined by a generator independent of the readers (K11).
- **One role per study per measurement.** Bars are written before the runs they judge. Every rate carries its
  count and bound, or reads "insufficient".
- **The recognition table** (No Popery): every question of every object, across all object classes (unclaimed
  and overlapping material included), reported as identified / abstained / wrong per class and role. It is read
  as the domain's own science, never summed into one number.
- **Acceptance is reported in four kinds, none substituting for another:** behavioural correctness,
  representation fidelity, domain validity, and performance evidence. Each acceptance also states its *evidence
  scope* and its *invalidation rules*.
- **First light** (K18) produces the **structure-alone run**: the scoped end-to-end recognition table and AUC.
  It is kept for the rest of the build: "No agency is admitted by beating the run without it; that run is kept
  to show what the structure does alone" (THESIS §10.4). Every integration-changing chapter after K18 re-runs it,
  with its SAME and decision checks.
- **The falsifiers** are KNEE_ARCHITECTURE §6.4's nine, with falsifier 7 re-worded: stable meaning within the
  intended regime, and transfer of the recovered quantities.

## 6. Decisions, each with its deduction

- **D1 — a fresh package; legacy quarantined; reuse argued.**
  - *Because* the founder said "design things fresh, only use older stuff when it's genuinely the best
    approach".
  - *And because* a second package invites the sibling-path hazard. The migration ledger and an Import Linter
    contract make the hazard mechanical, not a matter of discipline.
- **D2 — whole chapters, first light early; never a demo slice.**
  - *Because* the founder asked to use the SquishOS book, whose forbidden move is "building a slice to 'prove'
    it", and because the review accord asked for the joints to be exercised early.
  - *So* every chapter is complete against its declared scope, honest abstentions included, and the order puts
    a complete path at K18.
  - First light establishes integration and the scoped structure-alone behaviour; it never stands in for domain
    acceptance. Codex agreed (design round 2, C).
- **D3 — Numba is the default for hot loops; native code only by evidence.**
  - *Because* the founder ruled "JIT is basically a requirment".
  - *Because* Numba 0.68 runs on Python 3.12–3.14 (measured) and compiles on the Kaggle image, so no binary
    ships.
  - *And because* a native wheel brings costs abi3 does not cover: NumPy ABI, glibc, CPU features, offline
    installation. Those must earn their place by measurement.
- **D4 — two environments.**
  - *Because* Detective needs CPython ≥ 3.12 while the deployment target is whatever Kaggle runs.
  - *Because* `target-version` proves nothing about runtime compatibility.
  - *And because* the existing venv sits on conda's Python, which Detective's EP-C4 warns against.
- **D5 — the local Detective, logged, never piped away.**
  - *Because* the founder said "use the one that's local, not the one that's installed from PyPI".
  - *Because* the filter hook does not see the module form (measured).
  - *And because* refusing pipes would block legitimate agent capture (Codex, design round 2, B).
- **D6 — nothing derived from competition data in git; private datasets for artifacts.**
  - *Because of* the competition rules (4.a, 4.b.1, Private Sharing).
  - *And because* fixtures, traces and Detective captures can carry pixels or report text.
- **D7 — the Mac Pro as the batch worker, through SquishOS only.**
  - *Because* the founder said so ("SquishOS has it registered, including how to access and use").
  - *Because* SquishOS's runbook is authoritative and states that orchestration is NOT-BUILT.
  - *And because* 16 GB and AVX-only set its limits.
- **D8 — exact arithmetic is proved from declared limits.**
  - *Because* an assertion after rounding cannot establish exactness (Codex, design round 1).
- **D9 — a SAME pass is bounded evidence, never a receipt.**
  - *Because* Detective's cross-language gate covers scalar C signatures only (DETERMINISTIC_SICP, Wave 5).
- **D10 — acceptance can go stale.**
  - *Because* a tag attests one revision. So `just accept Kxx` re-runs a chapter's acceptance at HEAD, and its
    invalidation rules name what makes it stale.

## 7. What stays open

**Facts, each settled by a chapter's measurement:**
- the Kaggle runtime (K01);
- the Mac Pro's environment and node SAME (K01, K05);
- the tags and transfer syntaxes across all series (K05);
- the identifiable sets, within and across planes, and whether "T1-like" ever means PD without fat suppression
  (K05, Q6);
- the residual label scope, i.e. whether reports treat OA marrow lesions as bruises and what Baker's size is
  meant (K06, Q3);
- the report-negative pool's purity (K09, Q12, with the founder's sample check);
- the λ shapes in health (K21, Q2's measurement);
- dependence (K23, Q8);
- the two-slice rule across planes (K20, Q13);
- the law's feasibility (K24, Q14);
- whether the carrier's contracts match the cell project's (K04, Q16).

**Policy, the founder's:**
- **Q4:** does the open register stay at exactly 0.5, or receive an explicitly authorized evidence ordering? K17
  computes both and reports the stake.
- **Q2's naming:** the four λ words are kept as legacy routing codes for cells of (I, D). They are not a sweep's
  shape.
- **The SquishOS filter hook:** should it be extended at its source (SquishOS `ops/agents/hooks/`) to cover
  `python -m Detective.cli` and `just detective`? Offered, not done.

**Unknowable from the data:** how the test labels were produced (Q11).
