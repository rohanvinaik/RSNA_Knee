# The workbench

Execution and development tools around the production package, plus historical probes. Kept in the project rather than a scratchpad, because the
findings it produced are cited in the chapter records and a cited reading must be reproducible.

## The three tiers, and what separates them

| tier | where | what it is | the bar |
|---|---|---|---|
| **production** | `src/knee/` | the pipeline itself | lint, format, **types** (`ty`), **tests**, pure decisions Detective-converged, run over real studies |
| **workbench** | here | execution/drawing edge, observers and probes | whole-tree lint/format; targeted integration tests where declared; historical probes answer for their recorded measurements |
| **scratch** | the session scratchpad | genuine throwaway — a thing tried once and abandoned | nothing; it is not kept |

What the gate actually asks of this folder, exactly: `ruff check .` and `ruff format --check .` cover
the whole tree, so a probe here is lint-clean and formatted. `ty check src tests` and
`pytest` discovers tests under `tests/`, rather than in this folder. Those tests can and do
exercise execution/graph/rendering adapters here; file location is not evidence of no tests.

The Hamilton and saved-record adapters have explicit integration coverage under `tests/`.
That evidence does not introduce a blanket test/type obligation for historical probes.

One rule is lifted here and nowhere else: **`BLE001`, the blind-except rule**
(`pyproject.toml`). A probe that sweeps all 336 series *must* catch broadly — one unreadable
series is a finding to record, never a reason for the sweep to die. Everything bearing on
**correctness** still applies, `B905`'s silently-truncating `zip` among them: a rough probe is
allowed, a probe with a wrong number is not.

The line between the first two is not polish, it is **obligation**. A production module is
something the pipeline depends on, so it answers to the gate. A historical probe is something a
reading depended on. The joined execution/drawing adapters additionally answer to their
explicit contracts and integration tests, despite living at the development/impure edge.

The line between the second and third is whether anything cites it. A probe whose number appears
in `docs/chapters/` belongs here. A probe that told me nothing belongs nowhere.

## What is here

### `measure/` — execution edge and recorded probes

`object_analysis.py` is the one-command execution edge (`just analyze-objects`): it
calls `run_study`, saves arrays/receipt/checkpoints, and draws saved records by default, every
study's gallery and, once per run, the corpus's shape. Conversation is on by default and
requires explicit prominence. Beside it, `interior_records.py`, `boundary_records.py` and
`conversation_records.py` serialise three stages' returned records.

The eight measurement probes that once sat here (`corpus_shape`, `noise_floor`, `regime_key`,
`regime_run`, `geometry_spread`, `object_toolkit_geometry`, `machinery_facts`, `reports`) are in
`archive/workbench/measure/` since 2026-10-12 (`every-stage-renders` task 7.1a): the founder,
*"I don't run ANY by hand. ALL probes are supposed to be part of production."* What each read by
hand is now read by the one command -- the corpus's shape when the corpus opens
(`knee.study.shape`), the regime key's histogram and second channel count, the geometry's two
spreads -- saved in the receipt and drawn. Their recorded findings stand in the chapter records
they are cited from (`docs/chapters/02-collapse/measurements/`), as historical measurements.

### `render/` — saved-record adapters and earlier probes

`all_frames.py` joins twelve drawings over one saved study (`DRAWINGS`: the study's recorded
plane and walk, the field, the objects four ways, the lens digits, the ownership partition, the
pairings, the findings, the bundles and the output's companion record). Each outcome is retained
in a gallery index, including `not_drawn` with its reason and route stages with `no_drawer`; a
drawer that returns a manifest whose `refusal` is a named code is recorded the same way. It does
not measure missing stage output. `corpus_frames.py` draws the run's corpus shape from the
receipt, once per run, and the writer calls it beside the join. See
[the current route](../docs/PIPELINE.md) for the join’s limits.

These are the **impure edge**: they open a saved run, call a renderer, and write a PNG. The
*pure* part — arranging a stage's values into panels — is in `src/knee/pictures/`, and each
drawer here reads a saved record back through that module, refusing by name a record that
disagrees with its stage's vocabulary.

Every one writes under **`data/pictures/`**: each takes its output directory from the joined pass
or its `--out` and checks it lies under `data/` against `_out.PROJECT`. That is deliberate and it
is not a convenience: a rendered knee **is pixels**, so it is derived competition data under the
RSNA MIRA licence and lives under `data/`, which `.gitignore` excludes whole (`AGENTS.md`,
override 7). A picture of this corpus never enters git.

The five render probes that once sat here (`look`, `structure`, `objects`, `seam`, `axial`) are
in `archive/workbench/render/` since 2026-10-12 (task 7.1): what they drew by hand is drawn by the
one command -- the structural reading (air by connection to the border, the leg closed, the axis
from the header, the profile, the basins and the seam, the darkest places and the bodies) as the
field gallery's second row, the walk through the stack with the superior end named as the study
gallery, the histogram with its split and the squint as the field gallery's first row.

| script | what it draws |
|---|---|
| `object_profiles.py` | a saved production plane, squint, sample locations and profile |
| `object_packet.py` | a saved-record series across views/contrasts, with source/receipt manifest |

The Packet A renderers read saved production records and write under their explicit
`--out` path in `data/pictures/`; they do not compute another segmentation. The
development `graph/` adapter observes one actual production study call and exposes
its measurements and counted work.

### `consults/` — the prompts put to the second readers

Kept because a consultant's answer is only as good as what it was asked, and the chapter records
quote those answers. The answers themselves are in `docs/chapters/*/readings/`.

## How to run one

These import `knee`, so they run under the project's interpreter from the project root:

    just analyze-objects --uid <study> --tile-mm 3 --span-mm 3 --samples 13 --axis superior \
        --backend jit --prominence-mm 3 --out data/measurements/<run>
    uv run --with matplotlib python -m workbench.render.field_frames data/measurements/<run> \
        --study-uid <study> --out data/pictures/<run>/<study>/collapse-field

Rendering needs matplotlib, which is deliberately **not** a project dependency: the pipeline
imports no drawing code (§13.7), so matplotlib stays outside it and is supplied per-run. That
`--with` is the proof of the separation, not a workaround.

`object_analysis.py` saves NPZ records, a receipt and study checkpoints under the explicit
private `data/` run directory, then draws. Each renderer saves PNGs and a manifest under its
`--out` in `data/pictures/`. None is imported by `src/knee/`.

## The rule for this folder

A script here may be rough, but it may not be **wrong about what it measured**. If one is
superseded, it is deleted rather than left to rot — a stale probe that still runs is worse than no
probe, because its number looks current. The same rule the project applies to a fix-guiding note
applies here.
