# Project verbs. Detective and Wesker resolve to the local checkouts, never PyPI (AGENTS.md, override 1;
# ~/tools/Detective/AGENTS.md, "Standing invocation").

set shell := ["bash", "-uc"]
set positional-arguments := true

pp := env_var("HOME") + "/tools/Detective:" + env_var("HOME") + "/tools/Wesker"

# The test suite, run bare under the project's own interpreter.
test *ARGS:
    PYTHONPATH={{ pp }} .venv/bin/python -m pytest "$@"

# Reproduce VERIFY from the lock; profiling is an explicit, development-only opt-in.
setup:
    uv sync --locked --extra jit

setup-profile:
    uv sync --locked --group profiling --extra jit

# The pinned style gate: ruff check, and the whole-tree format check.
lint:
    .venv/bin/ruff check .
    .venv/bin/ruff format --check .

# The type pass: advisory, never a gate.
types:
    ty check src tests

# Coverage is information, with no percentage bar.
coverage *ARGS:
    PYTHONPATH={{ pp }} .venv/bin/python -m coverage run -m pytest "$@"
    .venv/bin/python -m coverage report

# These checks are independent of the existing commit gate.
deps:
    deptry .

imports:
    PYTHONPATH=src lint-imports --config pyproject.toml --no-cache

# Name a target with checkable contracts; a no-contract run is not evidence.
#
# --report_all is passed ALWAYS, and that is the point: `crosshair check` is SILENT on success, so a
# bare run cannot be told apart from one that checked nothing at all -- the exact trap docs/TOOLING.md
# names ("Targets found, but contain no checkable functions" is not a pass). With it, every contract
# reports either "Confirmed over all paths" or "Not confirmed", and silence means the file had no
# contract to check. Note what the words mean: "Not confirmed" is NOT a violation and NOT a pass; it
# says the search found no counterexample and could not prove the condition over all paths.
crosshair TARGET *ARGS:
    PYTHONPATH={{ pp }} .venv/bin/python -m crosshair check --report_all "$1" "${@:2}"

# Put profiles derived from studies under data/, which is already gitignored.
#
# PYTHONPATH=.:src on every one of these, added 2026-10-12, and without it they could not profile
# this project at all. Each profiler runs its target through `runpy.run_path`, which does NOT put
# the repository root on `sys.path` the way `python -m` does, so a target importing `workbench` or
# `knee` died with ModuleNotFoundError before it executed a line. Every other recipe that runs
# project code already sets it; these five did not, which is why the production route had never
# been profiled with them.
trace OUT SCRIPT *ARGS:
    PYTHONPATH=.:src uv run --locked --group profiling python -m viztracer -o "$1" -- "$2" "${@:3}"

memory OUT SCRIPT *ARGS:
    PYTHONPATH=.:src uv run --locked --group profiling python -m memray run -o "$1" "$2" "${@:3}"

profile OUT SCRIPT *ARGS:
    PYTHONPATH=.:src uv run --locked --group profiling python -m scalene run -o "$1" "$2" --- "${@:3}"

# Line profiling requires functions decorated with @profile in the target.
profile-lines OUT SCRIPT *ARGS:
    PYTHONPATH=.:src uv run --locked --group profiling python -m kernprof -l -o "$1" "$2" "${@:3}"

profile-tree OUT SCRIPT *ARGS:
    PYTHONPATH=.:src uv run --locked --group profiling python -m pyinstrument -o "$1" "$2" "${@:3}"

# Stdlib fallback, including the Detective/Wesker paths VizTracer cannot observe reliably.
profile-calls OUT SCRIPT *ARGS:
    PYTHONPATH=.:src:{{ pp }} .venv/bin/python -m cProfile -o "$1" "$2" "${@:3}"

# Workbench drawing remains supplied per run, as specified in workbench/README.md.
render SCRIPT *ARGS:
    uv run --locked --with matplotlib python "$1" "${@:2}"

# The declared pre-commit gate.
gate:
    scripts/ci_local.sh

# Prove Detective and Wesker resolve to the local checkouts (once per session).
detective-resolution:
    PYTHONPATH={{ pp }} .venv/bin/python scripts/detective_resolution.py

# START HERE before writing code. The build loop, with this project's live state filled in.
#
# It is a COMMAND and not a document on purpose. The loop is also written in docs/STAGE_CONTRACT.md
# and docs/SPINE.md, and on 2026-10-11 the lead had both in context and built against neither. What
# changed its behaviour that day was never prose -- plan-status printing 3/23, Detective refusing to
# call two survivors equivalent, ruff failing the gate, an intent test failing. Commands answer back.
unit:
    PYTHONPATH=src .venv/bin/python scripts/unit_loop.py
    @echo
    @just plan-status every-stage-renders
    @echo
    @just plan-status object-resolution-toolkit
    @echo
    @just plan-status knee-object-model
    @echo
    -@just places

# Every module's declared place, computed against what is observably true (docs/places.json).
# Reports only what a check can compare to something observed; a role sentence is counted when
# unwritten, never passed. It does NOT gate: a stage being built is unreached for as long as it is
# being built, and a gate there would teach the next session to misdeclare place to go green.
places:
    PYTHONPATH=src .venv/bin/python scripts/places.py

# A saved run's composition, from its receipt's ledger: every produced record has a consumer, no consumer
# lacks a producer, the conversation precedes ownership. Advisory like `places`: it reports, never gates.
composition RUN:
    PYTHONPATH=.:src .venv/bin/python scripts/composition_check.py "$1"

# Declared work lives in OpenSpec; client instruction generation is deliberately off. The change
# defaults to every-stage-renders, the active breadth-first build. Name knee-object-model
# for the full architecture or object-resolution-toolkit for its measurement/contour substrate.
plan-status CHANGE="every-stage-renders":
    OPENSPEC_TELEMETRY=0 openspec status --change "$1"

plan-next CHANGE="every-stage-renders":
    OPENSPEC_TELEMETRY=0 openspec instructions apply --change "$1" --json

plan-check CHANGE="every-stage-renders":
    OPENSPEC_TELEMETRY=0 openspec validate "$1" --strict

# The graph observes the real production route, and never imports into knee.
graph OUT:
    HAMILTON_TELEMETRY_ENABLED=false PYTHONPATH=.:src .venv/bin/python scripts/object_graph.py --out "$1"

# THE ONE COMMAND: a study in, the whole analysis out, every stage drawn on the way past.
# Explicit physical settings go in the receipt. Output must stay under private data/.
#
# Matplotlib is supplied PER RUN here, exactly as the drawing recipes do it, so the single command
# can print what it resolved while `knee` still imports no drawing code and `just imports` holds.
# `--no-pictures` skips the drawing edge and its import. Submission projection and DEPLOY
# packaging/dry-run proof remain separate obligations; this flag is not a competition kernel.
analyze-objects *ARGS:
    uv run --no-sync --with matplotlib python -m workbench.measure.object_analysis "$@"

# Recompute a saved packet's source standing and proof linkage when resuming.
packet-status RUN:
    .venv/bin/python scripts/object_status.py "$1"

same RUN:
    .venv/bin/python scripts/verify_profiles_same.py "$1"

render-packet *ARGS:
    uv run --locked --with matplotlib python -m workbench.render.object_packet "$@"

# B1 observes the same saved production route; photos stay in data/pictures/.
interiors-status RUN:
    PYTHONPATH=.:src .venv/bin/python scripts/verify_interiors_same.py "$1" --status-only

same-interiors RUN:
    PYTHONPATH=.:src .venv/bin/python scripts/verify_interiors_same.py "$1"

render-interiors *ARGS:
    uv run --no-sync --with matplotlib python -m workbench.render.object_interiors "$@"

graph-interiors OUT UID:
    HAMILTON_TELEMETRY_ENABLED=false PYTHONPATH=.:src .venv/bin/python scripts/object_graph.py --out "$1" --study-uid "$2" --prominence-mm 3 --backend jit

# B2 exchanges original measurements through that same production route.
conversation-status RUN:
    PYTHONPATH=.:src .venv/bin/python scripts/verify_conversation_same.py "$1" --status-only

same-conversation RUN:
    PYTHONPATH=.:src .venv/bin/python scripts/verify_conversation_same.py "$1"

render-conversation *ARGS:
    uv run --no-sync --with matplotlib python -m workbench.render.object_conversation "$@"

conversation-picture-status FOLDER:
    .venv/bin/python scripts/verify_conversation_visuals.py "$1"

graph-conversation OUT UID:
    HAMILTON_TELEMETRY_ENABLED=false PYTHONPATH=.:src .venv/bin/python scripts/object_graph.py --out "$1" --study-uid "$2" --prominence-mm 3 --backend jit --conversation

# Detective from the local checkout, in this venv. Every run's complete output is kept in .detective/runs/
# and Detective's exit status is returned; read each run's log whole.
detective *ARGS:
    #!/usr/bin/env bash
    set -u
    mkdir -p .detective/runs
    verb="${1:-bare}"
    log=".detective/runs/$(date -u +%Y%m%dT%H%M%SZ)_${verb//[^A-Za-z0-9_-]/_}.log"
    {
        printf '# just detective'; printf ' %q' "$@"; printf '\n'
        echo "# Detective $(git -C "$HOME/tools/Detective" describe --always --dirty --abbrev=12)"
        echo "# Wesker    $(git -C "$HOME/tools/Wesker" describe --always --dirty --abbrev=12)"
        echo "# python    $(.venv/bin/python --version 2>&1)"
    } > "$log"
    PYTHONPATH={{ pp }} .venv/bin/python -m Detective.cli "$@" >> "$log" 2>&1
    status=$?
    echo "exit $status; the complete output is $log (read it whole)"
    exit "$status"
