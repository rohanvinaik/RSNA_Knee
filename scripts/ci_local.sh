#!/usr/bin/env bash
# The declared pre-commit gate (the global verification-gates.md). Run it whole and read its whole output
# before `&& git commit`. Every step runs and its status is kept; ty is advisory and never fails the gate.
# Copied from the previous build's gate on 2026-10-13, without its two steps that ran that build's own
# scripts (places.py, object_graph.py) and without its vulture allowlist. The archives are invisible
# unless Rohan says to look in them, so no step here reads them.
#
# The same gate runs on every push to GitHub (.github/workflows/gate.yml). Rohan, 2026-10-18: «Sonar
# should be part of the CI gate for this project, and a full CI gate should also run upon push to
# github». So every tool runs from the locked environment (.venv), and a missing one fails the gate
# rather than letting its advisory step pass unread.
set -u
cd "$(dirname "$0")/.."
# Detective's and Wesker's source checkouts on this machine, where they exist; elsewhere the locked
# releases installed in .venv are imported.
PP=""
for tool in "$HOME/tools/Detective" "$HOME/tools/Wesker"; do
    if [ -d "$tool" ]; then PP="${PP:+$PP:}$tool"; fi
done
fail=0

for tool in ruff lint-imports deptry ty vulture; do
    if [ ! -x ".venv/bin/$tool" ]; then
        echo "missing .venv/bin/$tool: run uv sync"
        fail=1
    fi
done

echo "== ruff check (pinned)"
.venv/bin/ruff check . || fail=1

echo "== ruff format --check (pinned, whole tree)"
.venv/bin/ruff format --check . || fail=1

# Under coverage, once: its coverage.xml is what the Sonar step reads.
echo "== pytest (under coverage)"
PYTHONPATH="$PP" .venv/bin/python -m coverage run -m pytest || fail=1
.venv/bin/python -m coverage xml -q -o coverage.xml || fail=1

# THE WORKFLOWS. Blocking: zizmor (SquishOS repo-hygiene.md) on the GitHub workflows: unpinned actions,
# broad token permissions, persisted credentials, template injection. Pinned to the version that first
# audited them.
echo "== zizmor (blocking): the GitHub workflows"
uvx zizmor@1.31.1 --offline .github/workflows || fail=1

# THE LAYER CONTRACT. Blocking: production never imports the development or drawing tools, and a
# run with no contracts configured is not a pass.
echo "== import contract (lint-imports)"
PYTHONPATH=src .venv/bin/lint-imports --config pyproject.toml --no-cache || fail=1

# DECLARED DEPENDENCIES AGAINST REAL IMPORTS. Advisory: TOOLING.md records that its unused-package
# findings are leads to inspect and never authority to remove a package from the founder's design.
echo "== deptry (advisory): declared dependencies against what is imported"
.venv/bin/deptry . || echo "deptry: the findings above are leads, not a gate"

echo "== ty (advisory)"
.venv/bin/ty check src tests || echo "ty: the findings above are leads, not a gate"

# SPEED LEADS. Advisory: Ruff's performance rules (PERF) and its stable refurbishing rules (FURB; no
# --preview, so no preview rules), agreed by Rohan on 2026-10-18 as the lead suggested: "Start them as
# advisory, like vulture". The command-line selection replaces the configured one for this run only;
# the archives stay excluded. The whole list prints and the step never fails the gate: a finding is a
# lead to read where the code is hot, never a count to drive down.
echo "== ruff PERF + stable FURB (advisory): performance and refurbishing leads"
.venv/bin/ruff check --select PERF,FURB --exit-zero --output-format concise . ||
    echo "ruff PERF/FURB: the run above did not complete; its findings are leads, not a gate"

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
.venv/bin/vulture src scripts ||
    echo "vulture: a name here that is used only by a test is an island (AGENTS.md: defined, imported and tested with no production caller)"

echo "== vulture (advisory) 2/2: nothing ANYWHERE calls it, tests included"
.venv/bin/vulture src scripts tests ||
    echo "vulture: every line here is an island whose consumer is owed, or dead code to archive"

# KERNEL COSTS. Advisory: each costly kernel's costliest call from the production run on the proof
# study, recorded in benchmarks/recorded/ by benchmarks/record_calls.py (where the competition's files
# are; refreshed when the production path changes what it hands a kernel, FULL_BUILD_PLAN §9) and
# rebuilt exactly (benchmarks/test_kernels.py), so it needs no study data and runs on GitHub too. Rohan,
# 2026-10-18: «We shouldn't have hardcoded values, wire in the ones we compute in the production path»;
# «Drop the requirements for study data». It prints the commit the recording was made from, each
# replay's duration and its memory at the peak (memray). One call per kernel, not a kernel's whole
# cost on the study; and the kernels call one another, so their figures overlap and do not add up.
# A replay holding more memory at its peak than at its last successful run on this machine fails the
# step (--fail-on-increase; pytest keeps the runs in .pytest_cache/, so on GitHub, where every run
# starts fresh, it never fires, and CodSpeed compares commits there instead). After a deliberate
# increase, one run without the flag sets the new baseline:
#     .venv/bin/python -m pytest benchmarks -q --memray
# and `pytest --cache-clear` anywhere in the project clears it. Not under coverage. Information, never
# a target: it never fails the gate.
echo "== kernel costs (advisory): each kernel's costliest production call on the proof study, replayed"
.venv/bin/python -m pytest benchmarks -q -rP --durations=0 --memray --most-allocations=0 --fail-on-increase ||
    echo "kernel costs: a replay above failed or held more memory than at its last run here; information, not a gate"

# SONAR. Blocking, bare correctness only: the scan and its analysis ran, the open bugs and
# vulnerabilities were read, and none is open. Rohan, 2026-10-18: «Both git and local should use a sane
# profile of Sonar rules. Yes, agree, don't over-fit to targets, only bare correctness issues should be
# blocking». One pinned SonarQube and scanner with the full "Sonar way comprehensive" rules, here and on
# GitHub. The quality gate and its new-code conditions, the code smells by rule, coverage and
# duplication print as information, read like vulture's lists. A deliberate construct Sonar misreads
# gets `# NOSONAR(<rule key>)` on its line (the only form Sonar accepts: nothing may follow it) and its
# reason in a comment just above; a real finding is fixed.
echo "== sonar (blocking: no open bug or vulnerability; the rest is information)"
.venv/bin/python scripts/sonar_local.py gate || fail=1

if [ "$fail" -ne 0 ]; then
    echo "GATE: FAILED"
    exit 1
fi
echo "GATE: PASSED"
