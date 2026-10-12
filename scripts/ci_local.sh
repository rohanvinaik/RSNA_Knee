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

# THE LAYER CONTRACT. Blocking: production never imports the development or drawing tools, and a
# run with no contracts configured is not a pass.
echo "== import contract (lint-imports)"
PYTHONPATH=src lint-imports --config pyproject.toml --no-cache || fail=1

# EVERY MODULE'S DECLARED PLACE. Advisory on purpose, and the justfile says why: a stage being
# built is unreached for as long as it is being built, and gating there would teach the next
# session to misdeclare a place to go green.
echo "== places (advisory): declared modules against the real import graph"
PYTHONPATH=src .venv/bin/python scripts/places.py ||
    echo "places: unreached modules above are advisory, never a gate"

# THE DEVELOPMENT GRAPH. A value nothing consumes shows as dangling.
echo "== graph (advisory): the production route as a graph of named values"
HAMILTON_TELEMETRY_ENABLED=false PYTHONPATH=.:src .venv/bin/python scripts/object_graph.py \
    --out "$(mktemp -t knee-graph-XXXXXX).json" ||
    echo "graph: the findings above are leads, not a gate"

# DECLARED DEPENDENCIES AGAINST REAL IMPORTS. Advisory: TOOLING.md records that its unused-package
# findings are leads to inspect and never authority to remove a package from the founder's design.
echo "== deptry (advisory): declared dependencies against what is imported"
deptry . || echo "deptry: the findings above are leads, not a gate"

echo "== ty (advisory)"
ty check src tests || echo "ty: the findings above are leads, not a gate"

# ISLANDS. The founder, 2026-10-12: "I told you that there should be structural guards against
# islands of code that compute but are never called ... they would make unused scripts that are in
# the codebase impossible to miss." `just places` only checks whether a route MODULE is reachable;
# it says nothing about a function, and nothing at all about the drawing layer. This does, and it
# runs every time so it is not something anyone has to remember.
#
# TWO scans, because they answer different questions, and NO --min-confidence: a floor on what the
# tool is allowed to say is a filter on its output, and this gate exists because filtered output is
# how the islands survived in the first place.
#
# It prints rather than failing, for one measured reason: dataclass fields and Hamilton's
# name-resolved nodes are false positives here, so a blocking run would need a whitelist and a
# whitelist is how a guard stops being read. Amended 2026-10-12 (task 7.2): `vulture_allowlist.py`
# admits ONLY names whose consumer exists and vulture cannot see, each with that consumer's
# location beside it, so what this prints is shorter and every line of it is an island or a
# consumer still owed. A name whose consumer is owed is deliberately NOT in the allowlist.
echo "== vulture (advisory) 1/2: nothing in PRODUCTION calls it -- test-only code shows here"
vulture src workbench scripts vulture_allowlist.py ||
    echo "vulture: a name here that is used only by a test is an island (AGENTS.md: defined, imported and tested with no production caller)"

echo "== vulture (advisory) 2/2: nothing ANYWHERE calls it, tests included"
vulture src workbench scripts tests vulture_allowlist.py ||
    echo "vulture: every line here is an island whose consumer is owed, or dead code to archive; the allowlist names the dynamic consumers"

if [ "$fail" -ne 0 ]; then
    echo "GATE: FAILED"
    exit 1
fi
echo "GATE: PASSED"
