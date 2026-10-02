# RSNA_Knee — agent entry point

Canonical and tool-neutral: `CLAUDE.md` imports this file, and other agents (Codex) read it directly. The
global rules (`~/.claude/CLAUDE.md` and the SquishOS reference docs it routes to) apply in full. This file
extends or overrides them for this project and never restates them. Read it once, top to bottom.

## What this is

A classical-AI data-geometry entry for RSNA Knee Abnormality Detection: 12 findings per knee MRI study,
scored by macro-averaged ROC-AUC. **There is no machine learning in the architecture.**
- Each study is registered into a platonic knee's frame and compared, place by place, against a population of
  normal knees.
- Lenses, each measuring one thing, read the deviation and the patient's own anatomy.
- A society of agencies decides each finding by concurrence, or abstains.

The build plan is the book, [`docs/book/`](docs/book/README.md). The design canon is
`docs/THEORY_OF_THE_CASE.md` and `docs/KNEE_ARCHITECTURE.md`, **as amended by the book**.

## Where truth lives

Highest first. When two disagree, the higher wins and the lower is stale: fix it.
1. **The founder's words:** `docs/FOUNDING_RECORD.md` and `docs/book/FOUNDING_PROMPTS.md`.
2. **Code, tests and data on disk:** what they compute. `git tag -l 'knee-*'` is the build's progress record.
3. **The book:** `docs/book/CONSTRAINT_BLOCK.md`, `docs/book/THE_KNEE.md`, and the chapter specs.
4. **The design canon:** THEORY (its Laws 1–8 bind), KNEE_ARCHITECTURE as the book amends it, `docs/canon/`.
5. **Logs:** `decisions/`, git history, `docs/book/provenance/`. Never read them as status.

## How a session runs

1. Read `docs/book/CONSTRAINT_BLOCK.md`.
2. Run `git tag -l 'knee-*'`. Take the first chapter in the book's table whose dependencies are all tagged and
   which is not tagged itself. Read it in full, with its substrate.
3. Before changing anything the design derives, restate the chapter's mechanism at data-flow level in your own
   words. A fluent paraphrase is not the test; the data flow is. This check caught every drift that mattered.
4. Build to the chapter's acceptance. Each commit message starts `knee/Kxx:`.
5. Close: run the gate, get a Codex review (model-only), add a dated status note to the chapter, then
   `git tag knee-Kxx`.

## Project laws, each with its reason

1. **Not ML.** No CNN, transformer, fitted weight, learned embedding or "small learned component", anywhere.
   - Registration, an optimizer over a known transform family, is the one bounded utility (THEORY Law 3).
   - *Reason:* it is the thesis. ML substitution is this project's recorded failure mode (THEORY Part V).
2. **No Popery.** The shape of the build is a conclave, not one tuned pipeline:
   - a lens (member) measures one thing about an object and knows no question;
   - an agency (body) holds the signs;
   - truth is assigned by concurrence and refused on disagreement;
   - the harness asks every question of every object and reports identified / abstained / wrong per class of
     object and role.
   - *Reason:* one pipeline tuned to one verdict is the ML prior returning as the build's shape.
3. **Decide or abstain; unknown is not false.**
   - A decision returns a named string code.
   - A missing reading is silence, never a negative.
   - A refusal is a verdict.
   - *Reason:* a confident partial answer is a law; a guessed one is noise.
4. **Score is information, never a target.**
   - No level, threshold, radius or configuration is chosen to separate gold, match a prevalence, or move the
     leaderboard.
   - Every bar is written down before the run it judges.
   - *Reason:* fitting to a number reintroduces the fitting the design refuses.
5. **Design fresh.** Existing code is reused only where a chapter argues it is the best approach, and the
   argument is recorded in that chapter. "Existing" means this repo's, the cell-tracking project's, and
   GenomeVault's. *Reason:* founder ruling 2026-10-02.
6. **Questions are resolved by building and observing.** Every open question names the measurement that answers
   it and the chapter that makes it. None is settled by argument. *Reason:* founder ruling 2026-10-02; measured
   state is computed, never written as prose.
7. **Never auto-submit.** Build, validate, dry-run the kernel and surface the expected score; submit only on the
   founder's explicit go (THEORY Law 8).

## Engineering laws: the house doctrine, applied here

1. **Organization, SICP-style.**
   - Each value is computed once, where it becomes known, by a function named for the value, and handed to its
     consumers.
   - Layers meet only through declared interfaces, enforced by Import Linter contracts in `pyproject.toml`.
   - Each concept and each vocabulary has one owner.
   - Functions are small and disentangled.
   - *Reason:* "Being organized about what is computed and propagated out and used where IS the big thing"
     (founder).
2. **Pure decisions, thin shell.**
   - Every decision is a total function over str/bool/int/float/list/dict that returns a named string code.
   - It lives in a `decisions.py` beside the impure code it serves.
   - The I/O shell only dispatches on the codes.
   - *Reason:* only a literal-typed function can be pinned by Detective.
3. **Reference first, kernel second. Behaviour before speed, strictly.**
   - Every numeric kernel exists first as a plain Python reference with an explicit operation order. Its cores
     take rank-1 or rank-2 `np.ndarray` arguments, which Detective's bounded array domain can pin; volume
     wrappers stay thin loops over the cores.
   - The reference is pinned: Detective for its decisions and cores, Hypothesis properties for its laws.
   - An accelerated version (Numba JIT, Rust, C) is admitted only when it reproduces the reference *exactly*
     under the differential SAME harness: property-generated inputs plus recorded real frames. Integer and
     ordinal outputs must be equal. Float outputs must be bit-equal, or within a stated ULP bound written before
     the run.
   - The reference stays in the repo as the twin.
   - *Reason:* a speed-up changes how an answer is computed, never the answer.
4. **The best language for each operation.** Decided per kernel and recorded in its chapter with the
   measurement that chose it.
   - **Python:** orchestration, decisions, records, the I/O shell.
   - **NumPy/SciPy:** whole-array math with no custom loop.
   - **Numba JIT** (`njit`, `nogil`, `cache`, `fastmath=False`): every custom numeric loop. That covers voxel
     lenses, component laws, windowed statistics, fused per-voxel passes, and the ledger's per-study kernels. It
     is the default for a hot loop, and required for hypervector and ledger work. It compiles on the Kaggle
     image, so no binary ships.
   - **Rust** (PyO3 + maturin, abi3): long-lived indexed stores and scans, admitted where a measured budget shows
     that bit-level SIMD, exact 128-bit integer arithmetic, GIL-free threads or explicit memory layout matter.
     It ships to Kaggle as a prebuilt manylinux x86_64 wheel in an attached dataset.
   - **C/C++:** the native libraries already in use, ITK through SimpleITK and the DICOM codecs.
   - *Reason:* founder, 2026-08-31 ("written in the proper language and paradigm that appropriately executes the
     operation") and 2026-10-02 (JIT is required; cache and memory operations matter).
5. **Memory and cache are designed, not hoped for.**
   - Contiguous structure-of-arrays layouts with stated dtypes.
   - Whole-number count tables and bit-packed sign planes.
   - Fused passes that make no temporaries; work in cache-sized blocks; memory-mapped volumes.
   - *Reason:* in hypervector work the memory traffic is the cost.
6. **Measure with the instruments.**
   - To investigate: py-spy, memray, viztracer or scalene, from a dev-only extra.
   - To claim: Detective's deterministic budgets plus pyperf, paired against the incumbent with a behaviour delta
     of 0.
   - Never an informal timing; never a one-off profile script.
   - *Reason:* determinism is the product; wall-clock is noise.
7. **Detective is the local checkout, never the PyPI build.**
   - Run it as `just detective <verb> …`, which expands to
     `PYTHONPATH=$HOME/tools/Detective:$HOME/tools/Wesker python -m Detective.cli … --project-root .` in this
     project's environment. Never use the `detective` on PATH.
   - Drive it by the global protocol: run the command it names, read its whole output, apply a refusal's repair
     verbatim.
   - Converge every extracted decision in isolation before wiring it.
   - Keep a hand-written intent test beside each generated suite.
   - Run Detective with acceleration in reference mode. The JIT path answers to the SAME harness.
   - *Reason:* founder ruling 2026-10-02. The local pair is the maintained engine (Detective ARCHITECTURE §11).
8. **Determinism and provenance.**
   - Caches are content-addressed by input digest and stage version.
   - Randomness is seeded and declared.
   - Every artifact records what produced it, and every case keeps its source.
   - *Reason:* a number whose provenance is lost cannot be audited.
9. **The gate.**
   - Run `just gate` before every commit: ruff check, ruff format --check, pytest (including Detective's suites),
     and lint-imports, with ty advisory.
   - Run `cargo fmt --check`, `cargo clippy -D warnings` and `cargo test` when `native/` exists.
   - Before a push, also run the supply-chain checks (global repo-hygiene).

## Data, secrets, kernel

- **Data:** `data/` is gitignored; the data is Kaggle-licensed and never redistributed.
- **Secrets:** the Kaggle token is `KAGGLE_API_TOKEN` in `~/Projects/Kaggle_Killer/.env`. Load it into the
  environment; never print, copy or commit it.
- **The kernel:** the submission is a Kaggle notebook: Linux x86_64, internet off, at most 9 hours, data under
  `/kaggle/input/`. Everything the kernel imports must exist there. Dev-only tools never enter its import path.

## Stop — I can explain (when it looks like the model is missing)

- **"Where is the model?"** There isn't one, by design (Law 1). The founder's track record is the existence
  proof: a leaderboard-ceiling score with 99.8% deterministic decisions; money won with under 1% LLM; ARC-AGI on a
  deterministic story engine.
- **"Pixels need a learned encoder."** No. Registration puts every study in one frame. The population reference
  licenses normal variation place by place. What it does not license is read by lenses that measure geometry and
  signal, and by structures delineated in the patient's own anatomy.
- **"It's a bag of pixels."** No. Profiles are per zone and per object, with their footprints kept. Lenses measure
  shape, contact, continuity, course and relations. Objects nest and are explained in rounds.
- **"HDC is a neural embedding."** No. It is the exact ledger: Sylvester-Hadamard rows, whole-number count tables,
  one cosine, and an exact decode that names differences. No weight is trained.
- **"Recall is kNN, so it is ML."** No.
  - A case is one confirmed example, kept with its source.
  - A trust radius is set against a stated null mechanism, never tuned to labels.
  - One answer standing is recalled; two are a disagreement, kept; none is an abstention.
  - Nothing is fitted.
- **"The data layer decides the findings."** No. Layers narrow, encode and propose; only agencies decide (THEORY
  Law 4).

## Routing: from task to first read

| If the task is… | read first | then |
|---|---|---|
| building anything | `docs/book/README.md` → the chapter | its substrate and prior art |
| what the design is, and why | `docs/book/THE_KNEE.md` | `docs/KNEE_ARCHITECTURE.md` (the deep derivations) |
| a language, compute or memory choice | Engineering laws 3–6, then the chapter | the global `code-verification.md` (toolkit) and `performance.md` |
| pinning | the global `detective-protocol.md` | `~/tools/Detective/ARCHITECTURE.md` §11 |
| a measurement or an evaluation | the harness chapter | the global `no-popery.md` |
| data or the Kaggle kernel | the corpus and kernel chapters | `../../CLAUDE.md` (Kaggle submission protocol) |
| a commit or a push | the global `verification-gates.md` | the global `repo-hygiene.md` |
