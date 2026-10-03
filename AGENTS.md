# RSNA_Knee — agent entry point

Canonical and tool-neutral: `CLAUDE.md` imports this file, and other agents (Codex) read it directly. The
global rules apply in full: `~/.claude/CLAUDE.md` and the SquishOS reference docs it routes to (code
verification, the Detective protocol, the gates, repo hygiene, performance). This file never restates them. It
carries only what is specific to this project: its overrides and its decisions.

## The rigid oracle: the epistemology (read this first)

The founder's lens principle is the rigid oracle of this project, and it supersedes the architecture document: "The
concept is the rigid oracle, the design is something we're working on building in session" (2026-10-02 23:59:57Z).
His words are verbatim in `docs/book/FOUNDING_PROMPTS.md`. The worked reading, checked with Codex, is
`docs/book/provenance/theory/lens_principle_reading_claude.md`.

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

The rigid oracle is the founder's lens principle (`docs/book/FOUNDING_PROMPTS.md`, 2026-10-02 23:50:20Z): a lens measures; intentionally lossy lenses that encode no 1:1 relationship to an element of truth have no authority to warrant a decision alone; interpretation is built on top; meaning is derived from structure; principled abstention. It supersedes the architecture document: "The concept is the rigid
oracle, the design is something we're working on building in session" (23:59:57Z). The design is the founder's
`docs/THEORY_OF_THE_CASE.md` and `docs/KNEE_ARCHITECTURE.md`, being built in session. The book,
[`docs/book/`](docs/book/README.md), plans how it is built. `docs/book/THE_KNEE.md` lists the canon passages that
the 2026-10-02 accord and revision 1 amend. Each amendment stands only if it is provably correct or warranted by
the founder's explicit words (law 9). Until `docs/book/provenance/build/audit_against_original.md` has classified
it, it is unverified.

## Where truth lives

**Intent** (what the system should do). Highest first; the higher wins:
1. the founder's words: `docs/FOUNDING_RECORD.md`, `docs/book/FOUNDING_PROMPTS.md`. First among them is the lens
   principle, the rigid oracle (23:50:20Z), which supersedes the architecture document (23:59:57Z);
2. the founder's design: THEORY (its Laws 1–8 bind), KNEE_ARCHITECTURE, and `docs/canon/`. It is being built in
   session, and where it conflicts with the principle, the principle wins;
3. the book: `docs/book/CONSTRAINT_BLOCK.md`, `THE_KNEE.md`, the chapter specs. The book implements the design.
   Where it departs from the design, the departure stands only if it is provably correct or warranted by the
   founder's explicit words (law 9); otherwise the design wins;
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
