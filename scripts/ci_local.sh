#!/usr/bin/env bash
# The declared pre-commit gate (the global verification-gates.md). Run it whole and read its whole output
# before `&& git commit`. Every step runs and its status is kept; ty is advisory and never fails the gate.
set -u
cd "$(dirname "$0")/.."
PP="$HOME/tools/Detective:$HOME/tools/Wesker"
fail=0

echo "== ruff check (pinned)"
.venv/bin/ruff check . || fail=1

echo "== ruff format --check (pinned, whole tree)"
.venv/bin/ruff format --check . || fail=1

echo "== pytest"
PYTHONPATH="$PP" .venv/bin/python -m pytest || fail=1

echo "== ty (advisory)"
uvx ty check src tests || echo "ty: the findings above are leads, not a gate"

if [ "$fail" -ne 0 ]; then
    echo "GATE: FAILED"
    exit 1
fi
echo "GATE: PASSED"
