# The workbench

Work that is real but not production. Kept in the project rather than a scratchpad, because the
findings it produced are cited in the chapter records and a cited reading must be reproducible.

## The three tiers, and what separates them

| tier | where | what it is | the bar |
|---|---|---|---|
| **production** | `src/knee/` | the pipeline itself | lint, format, **types** (`ty`), **tests**, pure decisions Detective-converged, run over real studies |
| **workbench** | here | probes, experiments, one-off measurements | it ran, it produced a finding, the finding is recorded. **Lint and format** apply; **no** types, **no** tests |
| **scratch** | the session scratchpad | genuine throwaway — a thing tried once and abandoned | nothing; it is not kept |

What the gate actually asks of this folder, exactly: `ruff check .` and `ruff format --check .` cover
the whole tree, so a probe here is lint-clean and formatted. `ty check src tests` and
`pytest` (`testpaths = ["tests"]`) do not reach it, so a probe is neither typed nor tested.

One rule is lifted here and nowhere else: **`BLE001`, the blind-except rule**
(`pyproject.toml`). A probe that sweeps all 336 series *must* catch broadly — one unreadable
series is a finding to record, never a reason for the sweep to die. Everything bearing on
**correctness** still applies, `B905`'s silently-truncating `zip` among them: a rough probe is
allowed, a probe with a wrong number is not.

The line between the first two is not polish, it is **obligation**. A production module is
something the pipeline depends on, so it answers to the gate. A workbench script is something a
*reading* depended on, so it answers only for being re-runnable.

The line between the second and third is whether anything cites it. A probe whose number appears
in `docs/chapters/` belongs here. A probe that told me nothing belongs nowhere.

## What is here

### `measure/` — probes that produced recorded findings

| script | the finding it produced | recorded in |
|---|---|---|
| `corpus_shape.py` | six views; fluid-sensitive and fat-suppressed perfectly correlated; only Axial (1,1) in all 58 | `measurements/corpus-shape.md` |
| `geometry_spread.py` | physical extent consistent (~160 mm) while pixel grids differ eightfold | `measurements/geometry-spread.md` |
| `noise_floor.py` | the air-based sigma estimator returns 0.0 where the background is vendor-masked | `measurements/noise-floor.md` |
| `regime_key.py` | laterality absent from 181 of 336 series; only 58 train + 3 test studies on disk | `measurements/regime-key.md` |
| `regime_run.py` | the noise law over all 336 series: 4 concurring | `measurements/the-noise-law-fails-on-real-data.md` |
| `reports.py` | all 58 studies carry a report; 456 of 696 label cells negative | `readings/the-labels-ternary-collapse.md` |

### `render/` — probes that produced the pictures

These are the **impure edge**: they open a study, call a renderer, and write a PNG. The *pure*
part — arranging a stage's values into panels — belongs in `src/knee/pictures/` and is moving
there as each stage's renderer is settled.

Every one writes to **`data/pictures/`**, via `_out.pictures_dir()`. That is deliberate and it is
not a convenience: a rendered knee **is pixels**, so it is derived competition data under the RSNA
MIRA licence and lives under `data/`, which `.gitignore` excludes whole (`AGENTS.md`, override 7).
A picture of this corpus never enters git.

| script | what it showed |
|---|---|
| `look.py` | the first look at actual knees: the squint keeps the knee legible at 8x8 |
| `structure.py` | air by connectivity to the frame's border works where intensity thresholds did not; **the air is nearly all zeros** |
| `objects.py` | the failed attempt to split the bones by an intensity quantile — kept because the failure is the finding |
| `seam.py` | the closed leg and the header-derived superior-inferior axis |
| `axial.py` | the stack walked through Z: tibia, then the joint, then femur and patella |

### `consults/` — the prompts put to the second readers

Kept because a consultant's answer is only as good as what it was asked, and the chapter records
quote those answers. The answers themselves are in `docs/chapters/*/readings/`.

## How to run one

These import `knee`, so they run under the project's interpreter from the project root:

    uv run python workbench/measure/corpus_shape.py
    uv run --with matplotlib python workbench/render/axial.py     # -> data/pictures/axial.png

Rendering needs matplotlib, which is deliberately **not** a project dependency: the pipeline
imports no drawing code (§13.7), so matplotlib stays outside it and is supplied per-run. That
`--with` is the proof of the separation, not a workaround.

A measure script prints its table to stdout; a render script writes its PNG to `data/pictures/`
and prints the path. Neither writes anything else, and neither is imported by `src/knee/`.

## The rule for this folder

A script here may be rough, but it may not be **wrong about what it measured**. If one is
superseded, it is deleted rather than left to rot — a stale probe that still runs is worse than no
probe, because its number looks current. The same rule the project applies to a fix-guiding note
applies here.
