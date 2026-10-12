# Development tooling in this repository

The shared instructions and toolkit have their owners outside this repository:

- [Shared instructions](../../../../SquishOS/ops/agents/global.md) and
  [Codex profile](../../../../SquishOS/ops/agents/codex.md), under
  `~/Projects/SquishOS/ops/agents/`.
- [Toolkit](../../../../SquishOS/docs/home/TOOLKIT.md): roles, package ownership and known limitations.
- [Code verification](../../../../SquishOS/ops/agents/reference/code-verification.md): which tool supports which claim.
- [Performance](../../../../SquishOS/ops/agents/reference/performance.md): tracing and profiling limitations.
- [Project composition](../../../../SquishOS/ops/agents/reference/project-composition.md): graph, specification and template tools.
- [Setup](../../../../SquishOS/docs/spine/12-the-setup.md): instructions, hooks and MCP configuration ownership.

Those relative links resolve from `docs/` to `~/Projects/SquishOS/`. They intentionally point to
the owners rather than copied global instructions. Repository commands live in `justfile`;
dependencies and checker configuration live in `pyproject.toml`, with versions in `uv.lock`.

Serena's machine-local override is `.serena/project.local.yml`: Python plus Markdown language
servers, with `archive/**` excluded from ordinary discovery. The running server caches its
project configuration; restart that server to load a changed override. This directory is
gitignored, so a new checkout needs that local configuration again.

## Environments

`just setup` reproduces the managed VERIFY interpreter from `.python-version`, runtime
dependencies and the dev group. Dev tooling requires Python >= 3.12. The production package's
Python requirement remains separate; this environment is not evidence of Kaggle compatibility.

`just setup-profile` also installs the optional `profiling` group: Memray, VizTracer, Scalene,
Pyinstrument and line_profiler. Profiling commands select that group themselves. These tools
execute the target and must use the project's interpreter. Their global PATH copies are not
the repository's tooling. `just setup` removes the optional group again.

Standalone readers (`ty`, deptry, Import Linter, Pyright, Radon, symbolic mapping tools) use
their global installation. Ruff is the project's pinned exception. Detective and Wesker always
use the local checkouts through the existing `just detective` wrapper.

## Commands

Run from the repository root. `just --list` lists the recipes and their arguments.

| command | purpose |
|---|---|
| `just setup` | reproduce the ordinary development environment |
| `just setup-profile` | also install the optional profiling tools |
| `just test [pytest arguments]` | existing suite, including Detective-generated tests |
| `just lint` | pinned Ruff checks and whole-tree format check |
| `just types` | global ty on `src` and `tests`, advisory |
| `just gate` | existing lint, format and test gate, with advisory types |
| `just coverage [pytest arguments]` | branch coverage of `src/knee`, with missing lines reported |
| `just deps` | dependency declarations versus imports, including workbench scripts |
| `just imports` | enforce production's separation from development and drawing tools |
| `just detective-resolution` | show where Detective and Wesker actually resolve |
| `just detective <verb> ...` | local checkout, with complete run output kept in `.detective/runs/` |
| `just crosshair <target> [arguments]` | symbolic check of a target's explicit contracts |
| `just trace <output.json> <script.py> [arguments]` | VizTracer calls, with script arguments after `--` |
| `just memory <output.bin> <script.py> [arguments]` | Memray allocations |
| `just profile <output.json> <script.py> [arguments]` | Scalene CPU and memory profile |
| `just profile-lines <output.lprof> <script.py> [arguments]` | line_profiler for functions decorated with `@profile` |
| `just profile-tree <output.html> <script.py> [arguments]` | Pyinstrument call tree |
| `just profile-calls <output.prof> <script.py> [arguments]` | stdlib cProfile |
| `just render <script.py> [arguments]` | workbench drawing, supplying Matplotlib per run |
| `just unit` | whole open tasks, declared route metadata and structural place diagnostics |
| `just places` | declared modules versus filesystem/import graph; advisory, not runtime certification |
| `just composition <run>` | a saved run's composition from its receipt's ledger: every produced record consumed, no phantom consumer, the conversation before ownership; advisory, run after every real run |
| `just plan-status [change]` / `just plan-check [change]` | artifact status / strict validation; default `every-stage-renders` |
| `just plan-next [change]` | task checklist, default active breadth-first change; artifact completion is separate |
| `just graph <output>` | static development DAG validation; execution commands with a UID observe an actual run |
| `just analyze-objects [arguments]` | real production route; arrays, receipt, checkpoints and joined drawings by default |
| `just same <run>` | source-linked saved-plane reference/JIT comparison |
| `just packet-status <run>` | recompute and save source/proof/artifact standing for a handoff |
| `just render-packet [arguments]` | saved-record image series and source manifest, with per-run Matplotlib |
| `just interiors-status <run>` / `just same-interiors <run>` | current source standing and exact original B1 reference/JIT/saved-array comparison |
| `just conversation-status <run>` / `just same-conversation <run>` | current B2 standing and exact reference/JIT/saved-array and metadata comparison |
| `just graph-conversation <output> <study UID>` | observe the returned original measurements and conversation in one production run |
| `just render-conversation [arguments]` | five saved-record color stages, all-view overview, per-view focus images and their manifest |
| `just conversation-picture-status <folder>` | recompute photo, renderer, receipt, artifact and source-coordinate integrity; numerical proofs remain separate |

Coverage, dependencies, architecture and profiling are separate tools, not additional commit
gates. No coverage percentage bar is introduced. A check with no contracts is not a pass:
CrossHair's `Targets found, but contain no checkable functions` means there was nothing to check.

The import contract enforces the existing development/production separation only. It does not
invent stage ordering, sibling independence or the knee's domain architecture. Missing optional
external modules are allowed in the graph; an import of one is still forbidden.

deptry recognizes `_out` as the workbench's sibling module and Matplotlib as intentionally
supplied via `--with`, per `workbench/README.md`. It still reports unused declared packages;
these are leads to inspect, not authority to remove a package from the founder's design.

## One command, its switches and its limits

`just analyze-objects` requires `--tile-mm`, `--span-mm`, `--samples`, `--axis`,
`--backend` and `--out`; supply `--uid` for one study. Conversation defaults on
and requires `--prominence-mm`; `--no-conversation` explicitly disables it.
Drawing defaults on; `--no-pictures` skips the drawing edge and its import.
This switch alone is not a competition kernel or proof of DEPLOY compatibility: the
submission projection, packaging and private Kaggle dry run remain separate work.

The joiner reads saved records and keeps each drawing outcome. Its current packet
call needs a founder-supplied probe fraction; collapse, vectors and output have no
joined drawer. Renderer-module checks do not prove that actual stage images exist.
See the [dated execution evidence](chapters/02-collapse/measurements/documentation-reconciliation-20261012.md).
Use its parameters only as a reproduction of that recorded request, not new defaults.

## Profiles and pictures

Keep reports from competition studies under `data/`, for example:

```sh
mkdir -p data/profiles
just trace data/profiles/corpus.json workbench/measure/corpus_shape.py
just memory data/profiles/corpus.bin workbench/measure/corpus_shape.py
just profile-tree data/profiles/corpus.html workbench/measure/corpus_shape.py
just profile-calls data/profiles/corpus.prof workbench/measure/corpus_shape.py
just profile data/profiles/corpus-scalene.json workbench/measure/corpus_shape.py
just render workbench/render/axial.py
```

`data/` is already gitignored. Workbench renderers keep their existing output in
`data/pictures/`; Matplotlib remains outside the production dependency list. Do not publish
profiles that expose competition data or paths.

**Two limits measured 2026-10-12, on `knee.ownership.claims`, both recorded rather than worked
around.** First: `just crosshair` on a FILE whose function is annotated with a project dataclass
(`InteriorReading | None`) crashes with `crosshair.auditwall.SideEffectDetected: A "glob.glob/2"
operation was detected`. CrossHair walks the subclass map for the annotation, which imports
`skimage.io`, which globs for plugin `.ini` files at import, which its audit wall refuses. It
suggests `--unblock`; that was NOT used, because disabling the side-effect wall to check our own
contracts trades the guarantee for the result.

**The actual repair, found the same day: widen the annotation.** `read_ownership` is total over
anything and its own adversarial tests pass it malformed records, so `InteriorReading | None` was
a promise the tests broke — `ty` said so independently. Annotating `interiors: object` is both
more honest and the thing that stops CrossHair walking the subclass map, and the file then checks
end to end. So this is **not** a standing limit on array-shaped functions: it is a limit on
annotating a total function with a domain type it does not actually require. Where the narrow
annotation is genuinely right, naming the pure decision directly
(`just crosshair knee.ownership.claims.ownership_code`) still works.

Note what the check then said: `ownership_code`'s two contracts `Confirmed over all paths`,
`read_ownership`'s two **`Not confirmed`** — which is neither a violation nor a pass, but "no
counterexample found and not proven over all paths". Read the words exactly.

Second: `just detective converge` on that same array-shaped function returns `⚠ UNGATEABLE`, in its
own words *"one or more mutants could not be BUILT, so they say nothing about any test — this
measures the engine, not your suite; it is a defect to report, not a gap to close"*. The pure
decision beside it converged `✓ COMPLETE`. `AGENTS.md` override 1 separately records Detective's
stated scope — functions over domain objects are reachable only through real arguments captured
from tests — and that is a recorded fact placed beside this one, **not** a claim that it explains
the refusal; Detective says the refusal is an engine defect, and theorising past a refusal is the
failure the protocol names.

The Scalene recipe explicitly names its output rather than writing its default file in the
repository root. The shared performance guide records
a macOS SIGTRAP on a real workload; a small installation check does not resolve that failure.
VizTracer also has recorded blind spots on Python 3.14, especially worker threads and live
Detective/Wesker runs. Use the documented cProfile path for those cases. These tools investigate;
they do not establish deterministic budget claims or decision-preserving SAME.

## Other tools and global checks

The shared toolkit also covers Hypothesis, additional type/mutation readers, native C/Rust
toolchains and sanitizers, SICP/Prolog, symbolic algebra, graph and grammar libraries, process
inspection, benchmarks, requirements and graph/specification tools. Use its role-specific
instructions when a chapter needs one. Python libraries that execute project code go in a
development group or through `uv run --with`; keep native and standalone tools with their
declared global owner.

The accepted build uses OpenSpec for atomic packet contracts/tasks and Hamilton as a
development observer around one production study call. Neither replaces the founder's
chapter structure. Their telemetry is disabled in the recipes. Kedro, Spec Kit and
Copier remain available choices, not additional adopted project layouts.

See [BUILD_PLAN.md](BUILD_PLAN.md) for the packet index and
[the resume entry](chapters/02-collapse/RESUME.md) for exact evidence and next work.
`just setup` includes the optional JIT backend; production refuses a required backend
that is absent. LintGate's exposed check reports the intentional per-run Matplotlib
import as missing in the ordinary environment; actual renderer execution is separate
evidence. The exposed API has no requested strictness argument. Dependency inspection
currently flags declared pandas and SimpleITK as unused; their planned roles are not
authority to remove them. Re-run those readers to establish current state.

To check the global record without changing it:

```sh
uv run --project ~/Projects/SquishOS squishos-setup check
```

That check measures configuration and command reachability, not tool execution or exposure in
an existing agent session. The session's actual tool inventory remains authoritative. Shared
instruction repairs happen at SquishOS's owners, followed by `squishos-setup sync` and `check`;
MCP repairs happen in `~/.config/mcp/servers.json` followed by its sync. Do not duplicate those
configs in this repo to hide global drift.
