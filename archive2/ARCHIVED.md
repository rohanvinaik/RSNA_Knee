# The second archive (2026-10-14)

The founder, 2026-10-14: "Just throw everything into a SECOND archive folder in the project and
purge everything. Full archive of the system, but nothing in the "production" path. I will save this
project myself. I will rebuild it from your destruction piece by piece. That also refers to OpenSpec,
any planning documentation, any hooks for this project, sources of context. Save everything in the
archive, then I will save this project by building it completely by hand"

Everything here sits under its old path: `src/…` is now `archive2/src/…`, and so on.

**Moved here:** `src/`, `tests/`, `workbench/`, `scripts/`, `tools/`, `kaggle/`, `docs/`, `openspec/`,
`README.md`, `AGENTS.md`, `CLAUDE.md`, `justfile`, `pyproject.toml`, `uv.lock`,
`vulture_allowlist.py`, and the project's tool folders `.claude/` (its rules and settings),
`.detective/`, `.lintgate/`, `.prism/`, `.serena/`, `.wesker/`. The last four are ignored by git, so
they are kept on disk here but are not in the repository's history.

**Left at the root:** `.git/` and `.gitignore`; `data/` (the competition's files in `data/raw/` and
every run's measurements and pictures, ignored by git); `.venv/` and `.python-version` (the
environment, still usable with `.venv/bin/python`); the first archive, `archive/`; and the tool
caches (`.coverage`, `.hypothesis/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`).

**State at the move:** the last commit before it was `a1ce5a8` ("The funnel, declared"); all the
work after it, uncommitted until now, is in this archive and in the commit that made it. The last
run of the old gate, on the tree just before the move, had three failing tests: one sheet-naming
fault in `workbench/render/tile_dome_frames.py` and two route-composition tests that found
`depth` and `tile_digits` produced but read by no stage.

**Recovered from here, at his word** ("I guess we can recover the study loader and the "squint, the
background lens and the line-up". Fine the joint slice too. But that's it. The rest, I'm rebuilding
by hand"): back at their original paths under `src/knee/`, unchanged, are the study loader
(`study/`, all ten modules), the squint (`collapse/squint_stack.py`, with `collapse/physical.py`),
the background lens (`collapse/first_lens.py`, with the series' own black level from
`collapse/regime.py`, `noise.py`, `units.py` and `codes.py`) and the line-up
(`collapse/lineup.py`), and the modules they import: `collapse/structure.py` (the pairing reads
its `told_sign`, and the joint-line probe its profile helpers; the file comes back whole, with its
old field-stage reading in it), `absence.py`, `compute/contracts.py`, `telemetry/ledger.py` and the
package `__init__` files. Their tests and pictures stay here. The joint-line probe, which seeds the
two halves either side of the deepest enclosed dip and finds the line on every joint slice, is
saved as `probes/probe_halves_plateau.py`; it runs against the recovered pieces with
`PYTHONPATH=src .venv/bin/python archive2/probes/probe_halves_plateau.py <study uid> <out dir>`.
`pyproject.toml` stays here too, so the recovered code runs with `PYTHONPATH=src` and the project's
`.venv`.

**Renamed so they can never load as instructions** (the content is unchanged): `CLAUDE.md` is
`CLAUDE.archived.md`, `AGENTS.md` is `AGENTS.archived.md`, and the project's `.claude/` folder (its
rules and settings) is `dot-claude/`. A file named `CLAUDE.md` or `AGENTS.md`, or a `.claude/`
folder, loads into an agent's context as soon as it reads anything beside it.

**Claude's memory for this project**, the nine notes that were injected into every prompt
(`~/.claude/projects/-Users-rohanvinaik-Projects-Kaggle-Killer-competitions-RSNA-Knee/memory/`), is
in `claude-memory/`; that folder outside the project is now empty.

**Outside the project, untouched:** the shared instruction files one folder up
(`~/Projects/Kaggle_Killer/CLAUDE.md` and `AGENTS.md`, loaded in every session under Kaggle_Killer and
shared by every competition), the global instructions and hooks that apply to every project,
Claude's past session transcripts for this project (read only if a session is resumed), and the
session's scratchpad probes.
