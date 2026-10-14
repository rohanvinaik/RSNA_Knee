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

**Outside the project, untouched:** Claude's memory for this project
(`~/.claude/projects/-Users-rohanvinaik-Projects-Kaggle-Killer-competitions-RSNA-Knee/memory/`), the
global instructions and hooks that apply to every project, and the session's scratchpad probes.
