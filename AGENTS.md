# RSNA_Knee — agent entry point

Canonical and tool-neutral: `CLAUDE.md` imports this file, and other agents (Codex) read it directly. The
global rules apply in full: `~/.claude/CLAUDE.md` and the SquishOS reference docs it routes to (code
verification, the Detective protocol, the gates, repo hygiene, performance). This file never restates them. It
carries only what is specific to this project: its overrides and its decisions.

## What this is

A classical-AI data-geometry entry for RSNA Knee Abnormality Detection: 12 findings per knee MRI study, scored by
macro-averaged ROC-AUC. **There is no machine learning in the architecture.**
- Each study is registered into a platonic knee's frame and compared, place by place, against a population of
  normal knees.
- Lenses, each measuring one thing, read the deviation and the patient's own anatomy.
- A society of agencies decides each finding by concurrence, or abstains.

The build plan is the book: [`docs/book/`](docs/book/README.md). The design canon is
`docs/THEORY_OF_THE_CASE.md` and `docs/KNEE_ARCHITECTURE.md`. `docs/book/THE_KNEE.md` names exactly which canon
passages the 2026-10-02 accord amends.

## Where truth lives

**Intent** (what the system should do). Highest first; the higher wins:
1. the founder's words: `docs/FOUNDING_RECORD.md`, `docs/book/FOUNDING_PROMPTS.md`;
2. the book: `docs/book/CONSTRAINT_BLOCK.md`, `THE_KNEE.md`, the chapter specs;
3. the canon: THEORY (its Laws 1–8 bind) and KNEE_ARCHITECTURE as amended by the book, plus `docs/canon/`;
4. logs (`decisions/`, `docs/book/provenance/`, git history), never read as status.

**State** (what the system does and how far the build has gone) is **computed, never written as prose**:
- from code, tests, data and their outputs;
- from `git tag -l 'knee-*'` for accepted chapters;
- from `just accept Kxx`, which re-runs a chapter's acceptance at HEAD. A tag attests acceptance at one revision,
  and staleness is computed.

Code is evidence of behaviour, never authority over intent: a bug is not a specification.

## How a session runs

1. Read `docs/book/CONSTRAINT_BLOCK.md`.
2. Run `git tag -l 'knee-*'`. Take the first chapter in the book's table whose dependencies are all accepted and
   which is not. Read it in full, with its substrate. Do this reading yourself: grounding is never delegated to a
   helper that lacks this context (founder, 2026-10-02).
3. Before changing anything the design derives, restate the chapter's mechanism at data-flow level. A fluent
   paraphrase is not the test; the data flow is.
4. Build the whole chapter to its acceptance. A chapter is never a demo slice. Commit messages start
   `knee/Kxx:`.
5. Close: run the gate, get a Codex review (model-only), add a dated status note, then `git tag knee-Kxx`.

## Project laws, each with its reason

1. **Not ML.**
   - The architecture holds no CNN, transformer, fitted weight, learned embedding or "small learned component".
   - THEORY Law 3 sanctions exactly one bounded utility: registration and normalization (II.1). The book builds it
     classically, as an optimizer over a known transform family plus deterministic nuisance measurements.
   - Only the founder places a learned model, there or anywhere: "Maybe I'll end up using some small model
     somewhere for some reason, but NO, the architecture is NOT NOT NOT ML" (FOUNDING_RECORD).
   - The typist (K02a) is a build tool the founder placed (2026-10-02). It types code that checks certify, and it
     is not the architecture.
   - *Reason:* it is the thesis. ML substitution is this project's recorded failure mode (THEORY Part V).
2. **No Popery.** The build is a conclave, not one tuned pipeline:
   - a lens (member) measures one thing about an object and knows no question;
   - an agency (body) holds the signs;
   - truth is assigned by concurrence and refused on disagreement;
   - the harness asks every question of every object, including unclaimed and overlapping material, and reports
     identified / abstained / wrong per class of object and role.
   - *Reason:* one pipeline tuned to one verdict is the ML prior returning as the build's shape.
3. **Decide or abstain; unknown is not false.**
   - A decision returns a named code.
   - A missing reading is silence, never a negative.
   - A refusal is a verdict.
4. **Score is information, never a target.**
   - No level, threshold, radius or configuration is chosen to separate gold, to match a prevalence, or to move
     the leaderboard.
   - Every bar is written down before the run it judges.
5. **Design fresh.** Existing code is reused only where a chapter argues it is the best approach, and the
   argument is recorded in the chapter. "Existing" covers this repo's legacy `RSNA_Knee`, the cell-tracking
   project and GenomeVault. *Reason:* founder ruling, 2026-10-02.
6. **Facts are settled by building and observing; policy is the founder's.**
   - A question of fact names the measurement that answers it and the chapter that makes it.
   - A question of policy or meaning is put to the founder with the measurements beside it. Examples are the
     emission rule (Q4) and what a label's scope intends.
7. **Never auto-submit.** Build, validate, dry-run the kernel and surface the expected score; submit only on the
   founder's explicit go (THEORY Law 8).

## Project overrides and decisions (the global doctrine applies; these are additional)

1. **Detective is the local checkout, never the PyPI build** (founder ruling, 2026-10-02).
   - Run it as `just detective <verb> …`. The wrapper runs
     `PYTHONPATH=$HOME/tools/Detective:$HOME/tools/Wesker python -m Detective.cli …` in the VERIFY environment
     and records the checkout's identity.
   - Never use the `detective` on PATH.
   - The SquishOS filter hook does not see the module form (verified 2026-10-02). So the wrapper keeps every run's
     complete output in `.detective/runs/` and preserves its exit status.
   - It does not refuse pipes, because agent tools capture through them (`docs/book/THE_KNEE.md` §3.7, D5).
     Logging is not proof of reading: each run is read whole.
   - Its scope, stated truthfully:
     - input synthesis renders literals and bounded arrays (rank 1–2, ≤ 16 elements, finite bool/int/uint/float);
     - functions over domain objects are reachable only through real arguments captured from tests.
   - "Fully mutant-pinned" means each function's current-digest standing is recorded: complete, incomplete,
     refused, stale, unverified or unpinned. Never a blanket claim.
2. **A reference first, then an accelerated twin that answers to SAME.**
   - Every numeric kernel exists first as a reference, "a plain Python or NumPy function behind the same contract"
     (THESIS §12.5), pinned and property-tested.
   - SAME holds within one environment, never across two. A chapter that changes decisions on purpose records a
     behaviour change with its intent; that is never a SAME failure.
   - An accelerated twin (Numba, Rust, C/C++) is admitted only by the decision-preserving SAME harness: codes,
     assignments, memberships, ties and decisions must match, and boundary cases go to the reference.
   - The backend registry configures before any kernel binds, records the requested and the effective backend,
     and refuses an unavailable backend that is required. It never falls back silently.
3. **Language by operation, chosen by measurement and recorded in the chapter.**
   - Python orchestrates and decides.
   - NumPy, SciPy and SimpleITK where their contracts fit.
   - Numba JIT for custom repeated numeric loops; required for hypervector, ledger and voxel work (founder,
     2026-10-02: "JIT is basically a requirment").
   - Rust or custom C/C++ is admitted per component by evidence. Wheels are built for Linux x86_64 and tested in
     the target environment.
4. **Two environments.**
   - VERIFY: a uv-managed CPython ≥ 3.12, which Detective needs.
   - DEPLOY: Kaggle's actual interpreter and packages.
   - Production imports, kernel contracts and the real entry point run in DEPLOY. A private Kaggle dry run is
     the final proof.
5. **Memory and numerics are contracts.**
   - Every array has a stated shape, dtype, axis order, units and frame.
   - Count limits are declared and integer widths proved from them.
   - Scratch bytes and access order are recorded rather than asserted.
6. **The Kaggle kernel.**
   - Linux x86_64, internet off, at most 9 h.
   - Packages come from the base image plus our attached private datasets.
   - Only `/kaggle/working` and `/tmp` are writable, which matters for the Numba cache and for unpacking.
   - Dev-only tools never enter its import path. No kernel path reaches a remote node: an escalation runs inside
     the kernel's budget, or is skipped and recorded.
7. **Data and secrets.**
   - Competition data may be used for any purpose under the RSNA MIRA license, but never made available to a
     non-participant, and nothing is shared privately outside the team (the competition rules, 4.a–4.b and
     Private Sharing).
   - The data itself (pixels, report text) and bulk derived artifacts (references, atlas, maps, case memory) live
     in `data/` and in private Kaggle datasets attached to our own kernels, each with its lineage and checksums.
   - Derived records may enter git (founder, 2026-10-02: "I'm fine adding stuff to git"). These are digests,
     manifests, panel and role assignments, and measurement tables. The GitHub repository is private (checked
     2026-10-02), and it stays private while it holds them, since the rules forbid making competition data
     available to non-participants.
   - The Kaggle token is `KAGGLE_API_TOKEN` in `~/Projects/Kaggle_Killer/.env`. Load it into the environment;
     never print, copy or commit it.

8. **The typist (K02a, optional).** A small local model types *eligible* bodies:
   - twins of pinned references;
   - pure decisions with a finite named-code return.

   It runs only through `squishos-harness`. It never drives, never chooses what to type, and never types intent,
   tests, bars, contracts, references or impure code. A body enters the codebase only with its certificate and
   after the lead has read it. It is selected only on the founder's word, after its qualification run.
9. **Acceptance is written first and is discovery.**
   - Each chapter's first act writes `acceptance/<K>.toml`.
   - Engineering checks gate the tag.
   - Domain readings never gate. A miss opens a problem to solve, never a reason to discard or work around the
     design (founder, 2026-10-02 16:29:22Z; ARCH §6.6.3).

## Stop — I can explain (when it looks like the model is missing)

- **"Where is the model?"** There isn't one, by design (Law 1). The founder's track record is the existence
  proof: a leaderboard-ceiling score with 99.8% deterministic decisions; money won with under 1% LLM; ARC-AGI on a
  deterministic story engine.
- **"Pixels need a learned encoder."** No. Registration puts every study in one frame. The population reference
  licenses normal variation place by place. Lenses measure geometry and signal in what it does not license, and
  in structures delineated in the patient's own anatomy.
- **"HDC is a neural embedding."** No. It is the exact ledger: Hadamard rows, whole-number count tables, one
  cosine, an exact decode. No weight is trained.
- **"Recall is kNN, so it is ML."** No.
  - A case is one confirmed example, kept with its source.
  - A trust radius is set by a stated null mechanism, never tuned to labels.
  - One answer standing is recalled; two are a disagreement, kept; none is an abstention.
- **"The data layer decides the findings."** No. Layers narrow, encode and propose; only agencies decide (THEORY
  Law 4).

## Routing: from task to first read

| If the task is… | read first | then |
|---|---|---|
| building anything | `docs/book/README.md` → the chapter | its substrate and prior art |
| what the design is, and which canon it amends | `docs/book/THE_KNEE.md` | `docs/KNEE_ARCHITECTURE.md` (the deep derivations) |
| a tool choice: properties, contracts, layers, profiling, Rust/C, SICP | the global `code-verification.md` → *The toolkit* | `~/Projects/SquishOS/docs/home/TOOLKIT.md` |
| a performance question | the global `performance.md` | Detective's `docs/theory/deterministic_sicp/DETERMINISTIC_SICP.md` §7–§8 |
| pinning | the global `detective-protocol.md` | `~/tools/Detective/ARCHITECTURE.md` §11 |
| a harness or an evaluation | the global `no-popery.md` | the harness chapter (K03) |
| the typist, or any local-model call | `docs/book/chapters/K02a-the-typist.md` | SquishOS `docs/theory/THE_DYAD.md`, `CONSTRAINED_OUTPUT_AND_REASONING.md`; Uroboros `docs/ARCHITECTURE.md` |
| the Kaggle kernel or submission | `../../CLAUDE.md` (the Kaggle submission protocol) | the kernel chapters (K18, K27) |
| a commit or a push | the global `verification-gates.md` | the global `repo-hygiene.md` |
