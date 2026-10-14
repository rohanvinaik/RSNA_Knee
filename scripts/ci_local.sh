#!/usr/bin/env bash
# The declared pre-commit gate (the global verification-gates.md). Run it whole and read its whole output
# before `&& git commit`. Every step runs and its status is kept; ty is advisory and never fails the gate.
# Copied from the previous build's gate on 2026-10-13, without its two steps that ran that build's own
# scripts (places.py, object_graph.py) and without its vulture allowlist. The archives are invisible
# unless Rohan says to look in them, so no step here reads them.
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

# THE LAYER CONTRACT. Blocking: production never imports the development or drawing tools, and a
# run with no contracts configured is not a pass.
echo "== import contract (lint-imports)"
PYTHONPATH=src lint-imports --config pyproject.toml --no-cache || fail=1

# DECLARED DEPENDENCIES AGAINST REAL IMPORTS. Advisory: TOOLING.md records that its unused-package
# findings are leads to inspect and never authority to remove a package from the founder's design.
echo "== deptry (advisory): declared dependencies against what is imported"
deptry . || echo "deptry: the findings above are leads, not a gate"

echo "== ty (advisory)"
ty check src tests || echo "ty: the findings above are leads, not a gate"

# ISLANDS. The founder, 2026-10-12: "I told you that there should be structural guards against
# islands of code that compute but are never called ... they would make unused scripts that are in
# the codebase impossible to miss."
#
# TWO scans, because they answer different questions, and NO --min-confidence: a floor on what the
# tool is allowed to say is a filter on its output, and this gate exists because filtered output is
# how the islands survived in the first place.
#
# It prints rather than failing, for one measured reason: dataclass fields and Hamilton's
# name-resolved nodes are false positives here, so a blocking run would need a whitelist and a
# whitelist is how a guard stops being read.
echo "== vulture (advisory) 1/2: nothing in PRODUCTION calls it -- test-only code shows here"
vulture src scripts ||
    echo "vulture: a name here that is used only by a test is an island (AGENTS.md: defined, imported and tested with no production caller)"

echo "== vulture (advisory) 2/2: nothing ANYWHERE calls it, tests included"
vulture src scripts tests ||
    echo "vulture: every line here is an island whose consumer is owed, or dead code to archive"

if [ "$fail" -ne 0 ]; then
    echo "GATE: FAILED"
    exit 1
fi
echo "GATE: PASSED"
