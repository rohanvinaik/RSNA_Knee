# RSNA_Knee — agent entry point

Canonical and tool-neutral: `CLAUDE.md` imports this file, and other agents (Codex) read it directly. The
global rules apply in full: `~/.claude/CLAUDE.md` and the SquishOS reference docs it routes to (code
verification, the Detective protocol, the gates, repo hygiene, performance). This file never restates them. It
carries only what is specific to this project: its overrides and its decisions.

## The structure, settled 2026-10-11 (read `docs/OBJECT_MODEL.md` first)

**A finding is a predicate violation on an object, or on a relation between objects.** Resolve every
element significant to the knee's operation; the twelve findings are then read off those objects by
arithmetic. An interstice is **constructed, not detected** — it exists the moment its two bounding
objects do, which is why the compartments cannot be missed and the "squishy" findings stop being
squishy. Recognition is mechanical: a knee is a fixed anatomy, so identity follows from invariant
relations and no stored case is consulted during the parse. Recall arrives later, at diagnosis.

**Three first-order requirements bind every stage, equal in rank** (`docs/STAGE_CONTRACT.md`): it
**renders** what it resolved (a stage is not `built` until it does, and a test enforces it); it is
**engineered for performance** — a compute contract per kernel, language by computation shape,
reference before twin, structlog and OTel telemetry, measured with the named instruments and never a
one-off profile; and it is **clean and modular**, measurements and decisions and orchestrations kept
apart. The founder, 2026-10-11: "the competition itself scores for efficiency, so that's a
first-order consideration, alongside the image output and clean modular production-spec design".

The full statement is `docs/OBJECT_MODEL.md`; the declared change is
`openspec/changes/knee-object-model/`; the founder's words are verbatim in
`docs/chapters/02-collapse/teachings.md`. This supersedes the chapter table of `docs/SPINE.md`, which
keeps the way of working. Everything below this section still holds.

## The project as of 2026-10-10 (read this first)

The founder, 2026-10-10, verbatim:
- "Set up a project structure that basically lets us build the high-level structure laid out by that ASCII diagram
  in the thesis. Then I'll walk you though every step, explaining everything along the way."
- "I guess..we go in order? The PI-UNdergrad pass, you tell, I teach?"
- "this will be the project and how we build it. Throw everything else into an archive, we'll dig from it as we
  need. I guess a folder for the raw data."
- "the "spine", the step-by-step chapters of the project from the thesis that this computer vision project will
  instantiate and that I will walk you through, and the PI-Undergrad workflow, driven with the thesis and the
  cell-tracking project as an oracle that we'll use to work this project out"

What that makes of this repository:
- **The plan and the way of working** are `docs/SPINE.md`, loaded in every session through `CLAUDE.md`: the
  chapters, Figure 8's stages in order, and the PI–undergrad pass the founder walks each one through, with the
  thesis and the cell-tracking project as the oracle.
- **The build** is `src/knee/`: one package per stage of Figure 8 of *What an \<Object> Is* (§2.8, in
  `~/Projects/Kaggle_Killer/competitions/cell_tracking/docs/pipeline_thesis/paper/what_an_object_is.md`). Each
  package carries the figure's text for its stage and says whether the founder has given the knee's version. Its
  tests are in `tests/`.
- **The competition's files** are in `data/raw/`, in Kaggle's own layout (gitignored).
- **Everything else** that was here is in `archive/`, under its old path: `docs/…` is now `archive/docs/…`,
  `src/RSNA_Knee/` is `archive/src/RSNA_Knee/`, and so on. A path below that names the old layout resolves under
  `archive/`.
- **The book's session procedure, chapter table and `knee-*` tags no longer govern.**

## The rigid oracle: the epistemology (read this next)

The founder's lens principle is the rigid oracle of this project, and it supersedes the architecture document: "The
concept is the rigid oracle, the design is something we're working on building in session" (2026-10-02 23:59:57Z).
His words are verbatim in `archive/docs/book/FOUNDING_PROMPTS.md`. The worked reading, checked with Codex, is
`archive/docs/book/provenance/theory/lens_principle_reading_claude.md`.

1. **A lens measures, and is never wrong.** "A lens is an instrument, an artifact of observation … Properly-designed
   lenses are never wrong, by definition."
2. **No lossy lens warrants a decision alone,** unless the statement is inherently what it measured. "A single lens
   can assign a value (or assign that something is *not* <X>) … only if it is inherently a measurement of truth". A
   set measured as [3,5,7] warrants "only odd primes", never "always only odd primes".
3. **A claim beyond one measurement is a conjunction:** "the truth is a CONJUNCTION of both lenses, with an
   interpretation provided by the structure of the problem space (And me, you with my approval)".
4. **Readings are balanced ternary, in two senses.**
   - For a strict warrant they mean "assignment/abstention/rejection".
   - For a directional reading they mean "evidence for/abstention/evidence against".
   - An assignment is "an explicitly encoded operation in balanced ternary, a strictly defined subset of the truth
     table", often with more than one path to truth.
   - The banks and their arithmetic are "basically a fancy version of a giant truth table".
5. **We classify definable categories of image, never "lesion" or "normal",** within "*Strict* boundaries of
   knowability, always". A category's name never outruns its warrant: "not-noise not cell" rejected noise and
   abstained on cell.
6. **What a category means is the founder's:** "a question for a fluid-intelligence oracle to rule on". "I ascribe
   meaning to it when I literally see it in action."
7. **The committee looks downwards.** It asks "how many violations of which strength signals is enough to cause an
   assignment to fail?" "a majority *can* be a sufficient contract that decides on a ruling", and it never makes the
   ruling correct. Refusing on disagreement is "not wrong as a principle, it is wrong as a law". Near-miss learning
   names part of it.
8. **Independence is measured and is essential to meaning,** but "correlation isn't damning in and of itself":
   "dissention between lenses that are otherwise positively correlated can be some of the most *valuable* pieces of
   data."
9. **Strict exclusion passes a thorough gate, then is used confidently:** "THOROUGH about what passes the gate … when
   we find one, we can use it *confidently*". The black and speck filters did this for "cell". The gate's criteria
   are established by building.
10. **The enemy is entropy:** "The enemy isn't correctness or noise, it's *entropy*. A thing that is wrong or that is
    noisy with a legible trace of reasoning behind it *is* information."
11. **Principled abstention:** "you know what you know, you know what you don't know, and those are both complete and
    correct assertions of the process of reasoning".
12. **What must be established is established by building:** "Most important is to make the code actually work, to
    be built … "what we have to establish" is itself...something we have to establish".

The habit this guards against, in his words: "finding a set of signals that kinda vibe and jumping to assign a label
to it".

## What this is

A classical-AI data-geometry entry for RSNA Knee Abnormality Detection: 12 findings per knee MRI study, scored by
macro-averaged ROC-AUC. **There is no machine learning in the architecture.**
- Each study is registered into a platonic knee's frame and compared, place by place, against a population of
  normal knees.
- Lenses, each measuring one thing, read the deviation and the patient's own anatomy.
- A society of agencies decides each finding by concurrence, or abstains.

The rigid oracle is the founder's lens principle (`archive/docs/book/FOUNDING_PROMPTS.md`, 2026-10-02 23:50:20Z): a lens measures; intentionally lossy lenses that encode no 1:1 relationship to an element of truth have no authority to warrant a decision alone; interpretation is built on top; meaning is derived from structure; principled abstention. It supersedes the architecture document: "The concept is the rigid
oracle, the design is something we're working on building in session" (23:59:57Z).

The registration into a platonic knee's frame and the population of normal knees come from the earlier design
(`archive/docs/THEORY_OF_THE_CASE.md`, `archive/docs/KNEE_ARCHITECTURE.md`, and the book that planned it,
`archive/docs/book/`). The build now follows Figure 8, chapter by chapter (`docs/SPINE.md`). How much of the
earlier design each chapter keeps is the founder's to say as he teaches it.

## Where truth lives

**Intent** (what the system should do). Highest first; the higher wins:
1. the founder's words: those of 2026-10-10 (this file's opening section and `docs/SPINE.md`), what he teaches at
   each chapter (recorded in that stage's package), and the earlier record (`archive/docs/FOUNDING_RECORD.md`,
   `archive/docs/book/FOUNDING_PROMPTS.md`). First among them is the lens principle, the rigid oracle (23:50:20Z);
2. the oracle each chapter is worked out from: the thesis and the cell-tracking project (`docs/SPINE.md`);
3. the archive (`archive/`: THEORY, KNEE_ARCHITECTURE, the canon, the book, the legacy code and logs), dug from as
   needed and never the plan.

**State** (what the system does and how far the build has gone) is **computed, never written as prose**: from
code, tests, data and their outputs, and from git. Each stage package's docstring says whether the founder has
given the knee's version.

Code is evidence of behaviour, never authority over intent: a bug is not a specification.

## How a session runs

The way of working, the PI–undergrad pass, and the chapters in order are in `docs/SPINE.md`. Do the reading
yourself: grounding is never delegated to a helper that lacks this context (founder, 2026-10-02).

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
   - truth is assigned by concurrence. Refusing on disagreement is "not wrong as a principle, it is wrong as a law"
     (the oracle, point 7): the committee looks downwards, and "a majority *can* be a sufficient contract that
     decides on a ruling";
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
8. **Suit and tie, not just "not naked."** Every operation gets the professional finish whatever it costs today:
   its compute contract, its language by computation shape, its layout, fusion and parallel unit, its gates and
   its counted budget (`docs/book/chapters/K02b-compute-design-and-native-layer.md`). A cheap path is never an
   excuse for a naive one.
   - *Reason:* "This is a demonstration, a BOLD claim about classical AI, I want it to be clothed as
     professionally and impressively as possible". The final design is unknown and will change as we
     experiment (founder, 2026-10-02).
9. **The design is the founder's.**
   - No agent changes the original design (THEORY, KNEE_ARCHITECTURE, the founder's words) unless the change is
     provably correct, or warranted by his explicit words, quoted with their source.
   - "Provably correct" means logic, arithmetic, an internal contradiction shown by quoting both passages, an
     order that cannot execute, or a checkable external fact. An external fact means the competition's literal
     data and framing, or a file format. It is admissible as a fact, and never as an implicit warrant on design
     or conception (founder, 23:22:50Z).
   - Everything else returns to the original design, or goes to him as a question with the argument beside it.
   - A second reader's critique (Codex, Antigravity) is never warrant. It may report a provable error with its
     proof, or ask a question. It never proposes the design.
   - Nothing is built. No codebase meets the design and there is no evidence of what works, so nothing is judged
     by how it looks: something that looks wrong may be critically important.
   - His general approval is not open authority: "my warrant was general and high-level, not open authority"
     (23:22:50Z).
   - The lens principle (23:50:20Z) is "the rigid oracle" and supersedes KNEE_ARCHITECTURE (23:59:57Z). So a change
     that brings the design into line with it is warranted by his words. A reading of the principle is not: its
     open terms ("direction", "exclusion", "lenses") are his to define.
   - *Reason:* the founder, 2026-10-02: "*I* am the authority on what works or doesn't … You do not have the
     authority to change the design *I* built based on a random guess, when you don't know the intent"; "Make
     SURE you are not changing anything other than that which is definitevely/provably correct, or warranted by
     my explicit words"; "Not just this session--EVERY change to the original design".

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
3. **Language by computation shape, decided at design time and verified by budget**
   (`docs/book/chapters/K02b-compute-design-and-native-layer.md`; DETERMINISTIC_SICP §6–§8):
   - Python orchestrates and decides.
   - NumPy for vectorizable maps; SciPy, scikit-image and SimpleITK for library-shaped operations.
   - Numba JIT for custom repeated loops on the kernel path; required for hypervector, ledger and voxel work
     (founder, 2026-10-02: "JIT is basically a requirment").
   - C for cache-hostile, memory-bound build-time kernels, with explicit allocation and tiles sized to L2.
   - Rust for the case-memory scan: bit-level SIMD, exact wide integers, GIL-free threads. (Founder,
     17:22:59Z: "C/C++ for memory management, cache hot vs cold management, Rust for speed … from the start".)
   - Every kernel carries a compute contract (THESIS §12.5) and keeps its reference. Native artifacts are built
     for every environment, Linux x86_64 included, and tested there.
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
9. **Acceptance is discovery.**
   - A chapter's bars are written down before the run that judges them.
   - Engineering checks gate the commit (`just gate`).
   - Domain readings never gate. A miss opens a problem to solve, never a reason to discard or work around the
     design (founder, 2026-10-02 16:29:22Z).

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

Repository tooling commands and environment setup: `docs/TOOLING.md` (global owners linked there).

| If the task is… | read first | then |
|---|---|---|
| **building anything** | **`docs/OBJECT_MODEL.md`** — the project's structure: objects → relations → predicates → output | `openspec/changes/knee-object-model/` for the declared change and its tasks; then the stage's package in `src/knee/` |
| which thesis section a stage instantiates, and what it still owes | `docs/INSTANTIATION.md` — the section → stage → package join, the three first-order requirements, what a sub-agent may build, and every open ruling that is the founder's | `docs/THESIS_AS_IDEAS.md` for what each section IS in his own words |
| the way of working | `docs/SPINE.md` — the PI–undergrad pass, the working loop, the oracles, the corpus. **Its chapter table is superseded** | the thesis sections it names, when a stage needs the oracle |
| the earlier design, dug from as needed | `archive/docs/THEORY_OF_THE_CASE.md` | `archive/docs/book/THE_KNEE.md`, `archive/docs/KNEE_ARCHITECTURE.md` |
| a tool choice: properties, contracts, layers, profiling, Rust/C, SICP | the global `code-verification.md` → *The toolkit* | `~/Projects/SquishOS/docs/home/TOOLKIT.md` |
| a performance question | the global `performance.md` | Detective's `docs/theory/deterministic_sicp/DETERMINISTIC_SICP.md` §7–§8 |
| pinning | the global `detective-protocol.md` | `~/tools/Detective/ARCHITECTURE.md` §11 |
| a harness or an evaluation | the global `no-popery.md` | `archive/docs/book/chapters/K03-acceptance-corpus-and-harness.md`, dug from as needed |
| the typist, or any local-model call | `archive/docs/book/chapters/K02a-the-typist.md` | SquishOS `docs/theory/THE_DYAD.md`, `CONSTRAINED_OUTPUT_AND_REASONING.md`; Uroboros `docs/ARCHITECTURE.md` |
| the Kaggle kernel or submission | `../../CLAUDE.md` (the Kaggle submission protocol) | `archive/docs/book/chapters/K18-kernel-and-first-light.md` and `K27-final-kernel.md`, dug from as needed |
| a commit or a push | the global `verification-gates.md` | the global `repo-hygiene.md` |
