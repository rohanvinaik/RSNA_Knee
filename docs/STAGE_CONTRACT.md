# The stage contract: what EVERY stage of the pipeline owes

<!-- The standard, settled with the founder 2026-10-11. Three first-order requirements, equal in
rank: the picture, the performance engineering, and the clean modular design. Read with
docs/OBJECT_MODEL.md (what the stages ARE) and docs/TOOLING.md (the commands). -->

The founder, 2026-10-11:

> "image output of each stage should be a requirement. Again, visual reasoning, computer vision. Each
> stage should be clean, modular, and we should be able to see the output visually."

> "telemetry, JIT/C++/Rust, overall performance engineering is also a first-order requirment of the
> pipeline. The SICP-centric design rules should slot in nicely here, **the competition itself scores
> for efficiency**, so that's a first-order consideration, alongside the image output and clean
> modular production-spec design"

> "Note all the tooling we have in the global context model files for telemetry and performance
> engineering. All these, as relevant, including the photo and performance tooling, as
> global/standard requirements for every stage of the whole pipeline"

**Nothing here is a nice-to-have.** A stage that satisfies its numeric contract but cannot show its
work is not finished, and neither is one that draws beautifully and was never measured.

---

## 1. The picture — `ENFORCED`

Every stage renders what it resolved. **A stage is not `built` until it renders**, and
`tests/knee/test_skeleton.py::test_a_stage_is_not_built_until_it_renders` fails the gate if
`knee.pipeline.ROUTE` claims `built` or `partly` for a stage with no module of its name in
`knee.pictures`.

- **One renderer per stage**, named for the stage, in `knee/pictures/`.
- **A renderer may only ARRANGE values the stage already computed.** It may not measure, threshold,
  segment or recompute. A picture that needs work the stage did not do is not a gap in the drawing —
  it is evidence that **the stage is not reasoning visually**, and the fault is in the stage.
- **The dependency runs one way**: pictures import stages, no stage imports pictures (§13.7).
  `test_no_stage_imports_the_drawing_layer` enforces it, so deleting `knee.pictures` cannot change a
  single reading.
- **Matplotlib is supplied per run** (`just render`), never a production dependency.
- Output goes to `data/pictures/`, gitignored: a rendered knee is pixels, hence competition data.

## 2. Performance engineering — `PARTLY ENFORCED`

### The law before the tools
> "These are tools. WE organize." … "Why profile randomly? We have tools for symbolic trace and
> timing and everything." — the operator, 2026-09-25

A run is **named values, each computed once where it becomes known and handed to every consumer**,
with every categorical finding kept as data. That is the SICP discipline, and it is the organisation
the tools merely *check*.

### Every numeric kernel carries a compute contract — `ENFORCED`
`ComputeContract` states `kind · language · reads · writes · allocation · work · parallel_unit ·
reference · proof_gate`. `tests/knee/test_compute_contracts.py` fails the gate on a stub: a contract
that does not name its reference and proof gate licenses nothing, and reads as a guarantee it has not
earned. Contracts are **data attached without a wrapper** (§13.5) — never a decorator on the hot path.

### Language by computation shape, decided at design time
| shape | language |
|---|---|
| orchestration and decisions | Python |
| vectorizable maps | NumPy; SciPy / scikit-image / SimpleITK where library-shaped |
| custom repeated loops on the kernel path | **Numba JIT** — required for hypervector, ledger and voxel work |
| cache-hostile, memory-bound build-time kernels | **C**, explicit allocation, tiles sized to L2 |
| the case-memory scan | **Rust** — bit-level SIMD, exact wide integers, GIL-free threads |

### Reference first, twin second
Every kernel exists first as a plain NumPy reference, pinned. An accelerated twin is admitted **only**
by the decision-preserving SAME harness — codes, assignments, memberships, ties and decisions must
match, boundary cases go to the reference. **A speed-up changes how an answer is computed, never the
answer.** The backend registry records requested *and* effective backend and refuses an unavailable
required backend; it never falls back silently.

### Telemetry
- **structlog** for the run's structured events: its id, inputs, decisions, timings, outcomes.
- **OpenTelemetry spans with a local exporter** once components must be correlated — a finding's id
  logged where it is made *and* where it is consumed.
- **Hamilton** as the dev-side wiring and lineage graph: a value made and never consumed shows as
  **dangling**. It is a development observer around one production run; it does not turn every
  internal kernel operation into a node, and production never imports it.
- Per project, **never on a production import path, never on a Kaggle kernel.**

### Measuring — the instruments, and what each answers
| question | instrument |
|---|---|
| what ran, from where, how often, how long | **VizTracer** (`just trace`) |
| per line: Python vs native vs system time, and memory | **Scalene** (`just profile`) |
| where the big arrays and temporaries are made | **memray** (`just memory`) |
| a timed call tree | **pyinstrument** (`just profile-tree`) |
| one hot function's lines | **line_profiler** (`just profile-lines`) |
| a long run, attached by pid | **py-spy** |
| wall-clock complement to Detective's opcode budget | **pyperf** |
| across the project's history | **asv** |

**A speed claim is a paired measurement** — Detective's opcode budget plus pyperf — never an informal
timing. **Counted work and profiler behaviour are reported separately.**

### Measured gotchas, which are facts and not cautions
- **Never `uv tool install`** a tool that imports its target: the isolated venv cannot see the
  target's packages (measured — `ModuleNotFoundError: numpy` under a uv-tool VizTracer that traced
  90,184 entries under an env holding its target).
- **VizTracer on 3.14 has three blind spots**: it records no `threading.Thread` worker; handed a
  console-script path it records none of the package's calls; inside a Detective converge it saves
  only metadata. **Use stdlib cProfile there** (`just profile-calls`) — on 3.12+ it is
  `sys.monitoring`-based and records every thread.
- **Scalene 2.3.0 on macOS 27** SIGTRAPs within seconds on a real production path. Undiagnosed; use
  VizTracer for calls and pyinstrument for a timed tree.
- **The runtime trace checks the static one.** Serena says who *references*; a trace says what *ran*.
  Agreement is the completeness check; a reference that never runs is a question. A trace taken with
  `--min_duration` omits shorter calls, so an absence there is **not** evidence.

## 3. Clean, modular, production-spec — `PARTLY ENFORCED`

- **One stage consumes only the stage below it**, through an interface narrow enough to state in a
  sentence. The route is `docs/OBJECT_MODEL.md`; `knee.pipeline.ROUTE` is its table of contents and
  reports each stage's state honestly.
- **Measurements, decisions and orchestrations are kept apart** (§13.7): a measurement returns a
  number or a field and decides nothing; a decision returns a **named code**, is pure and total, and
  every bar it reads is an **argument** rather than a constant; an orchestration moves values and
  decides nothing.
- **Nothing is deleted.** Unclaimed, disputed and abstained places stay reachable with their readings.
- **Every array states** shape, dtype, axis order, units and frame. Newly owned outputs are frozen
  (`handed_on`); a caller's source array is never written to.
- **Import Linter** keeps production clear of development and drawing tools (`just imports`); a run
  with no contracts is not a pass.
- **Pure decisions are pinned** with `just detective`, standing recorded per current digest.
- **`just gate` before every commit** — and a green gate rules nothing in. It is a law check: "a
  failure rules the answer out, and a pass settles nothing. Only the oracles establish" (§11.5).

## How a UNIT gets built — the loop, kept because it worked

Founder, 2026-10-11, on the `knee.lenses` build: *"this is a REALLY good workflow here. SICP-style
modular, atomic code, detective two-sign, CrossHair, the record of reasoning against the computer
vision '\<object>' thesis … I'd like to persist this workflow."*

A unit is **one idea**: a pure decision and the handful of helpers it needs, in one module, that a
sentence can describe. Not a stage, not a file of conveniences.

1. **Say why it exists, in the module docstring, against the thesis.** Which failure it answers,
   which section it instantiates, and the founder's words where they settled it. A module whose
   docstring cannot name the thesis role it fills is a module that drifted.
2. **Write the pure decision first.** Total over its arguments, returning a **named code**; every bar
   it reads is an **argument**, never a constant. Keep the named codes distinct wherever the remedies
   differ — three silences that mean different things are three codes.
3. **Declare the contracts** as PEP 316 `pre:`/`post:` lines. State the real requirement: positive
   does not imply finite, and a post-condition you cannot hold for every input the `pre:` admits is
   a defect in one of the two.
4. **Write intent tests, BOTH SIGNS, calling the function DIRECTLY.**
   - positive: what it must do;
   - negative: what it must never do.
   - Never through a local helper: Detective routes by static path, and a test it cannot route is
     not a pin (measured here — 9 of 13 invisible, `Incomplete` where `COMPLETE` was available).
5. **`just detective converge <file>::<func>`, then judge EVERY survivor.** Prove equivalence and
   record the proof in the `--note`, or name the must-not and enforce it with a test — a test is
   better than a `--fence`, because the mutant dies instead of being bookkept. A cluster of
   boundary/value survivors on one `if` is usually **dead code**: prove it by case analysis over the
   sibling clauses and delete it.
6. **`just crosshair <file>`.** It reasons over all paths where mutation samples inputs, and it finds
   different defects — measured here, two real post-condition violations at 55/55 mutants killed.
   Read the words exactly: `Not confirmed` is neither a violation nor a pass.
7. **Re-pin whatever step 6 changed**, then `just gate`, reading the **exit status** rather than the
   tail. A pipe hands `&&` the filter's status, not the gate's.
8. **Record the chapter's reasoning** in `docs/chapters/NN-<stage>/README.md`: why the unit exists,
   how it instantiates the thesis, **what the verification found that the author did not**, and what
   is open. A compaction then costs one unit, not the session.

Consult Codex and Fable where the design is genuinely open, with the lead's own reading **written
first** — and treat agreement reached independently as evidence, disagreement as a question for the
founder (`docs/SPINE.md`, the working loop).

## What a stage owes, as a checklist

1. its role and the founder's teaching, in the package docstring
2. a renderer in `knee.pictures`, arranging only values it computed
3. a `ComputeContract` for each numeric kernel, naming its reference and proof gate
4. a plain reference implementation, pinned, before any accelerated twin
5. structlog events; OTel spans where it must be correlated
6. a run over all 58 through Chapter 1's real entry point, with its image series saved
7. `just detective` standing for each pure decision
8. a counted-work budget, reported separately from profiler behaviour

A stage that has only seen synthetic data is not built — measured the hard way, when the noise law
passed every unit test and then concurred on 4 of 336 real series.
