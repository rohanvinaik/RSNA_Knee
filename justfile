# Project verbs. Detective and Wesker resolve to the local checkouts, never PyPI (AGENTS.md, override 1;
# ~/tools/Detective/AGENTS.md, "Standing invocation").

set shell := ["bash", "-uc"]
set positional-arguments := true

pp := env_var("HOME") + "/tools/Detective:" + env_var("HOME") + "/tools/Wesker"

# The test suite, run bare under the project's own interpreter.
test *ARGS:
    PYTHONPATH={{ pp }} .venv/bin/python -m pytest "$@"

# The pinned style gate: ruff check, and the whole-tree format check.
lint:
    .venv/bin/ruff check .
    .venv/bin/ruff format --check .

# The type pass: advisory, never a gate.
types:
    uvx ty check src tests

# The declared pre-commit gate.
gate:
    scripts/ci_local.sh

# Prove Detective and Wesker resolve to the local checkouts (once per session).
detective-resolution:
    PYTHONPATH={{ pp }} .venv/bin/python scripts/detective_resolution.py

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
