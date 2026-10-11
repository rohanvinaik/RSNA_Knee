"""Every module's place, declared in docs/places.json, computed against what is observably true.

Why this is a command and not a document. The founder, 2026-10-11, on the failure it exists to
catch: agents "build out a mountain of code in one arbitrary spot, one function at a time, and sort
of lose the thread of *why* the code exists, *where* it sits in a greater project pipeline… just
functionalities in islands". The loop was written down three times in this repository and built
against zero times; what changed behaviour was a tool that answered back.

**It reports only what it can compare to something observed.** Two second readers made the same
cut: a declared field no check reads is a document hidden inside a command, and two declarations of
one fact with nothing comparing them is not risk spread but surface doubled. So a kernel's reads and
writes stay in its ComputeContract and are not copied here; the registry declares the module's
PLACE, whether it carries a contract, and that is all. `role` is the one field nothing can check,
and it is reported as a COUNT of what is still unwritten — never as a pass.

What it cannot do, stated so nobody reads more into it. Reachability here is by IMPORT and at MODULE
level, while the failure the founder names is "one function at a time": a long function inside a
reached module passes. The function-level signal is `just graph`, which reports a value nothing
consumes; this does not duplicate it.

Usage: PYTHONPATH=src .venv/bin/python scripts/places.py [--json]
"""

from __future__ import annotations

import ast
import json
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "docs" / "places.json"

#: Where a module may be declared to sit. The route's own stages come from docs/OBJECT_MODEL.md.
ROUTE_ENTRY = "knee.pipeline"
SCOPES = ("src/knee", "workbench", "scripts")


def modules_on_disk() -> set[str]:
    """Every Python file in scope, as a path relative to the project root."""
    found: set[str] = set()
    for scope in SCOPES:
        for path in (ROOT / scope).rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            found.add(str(path.relative_to(ROOT)))
    return found


def module_name(relative: str) -> str | None:
    """`src/knee/objects/interiors.py` -> `knee.objects.interiors`; None outside the package."""
    if not relative.startswith("src/"):
        return None
    parts = Path(relative[len("src/") :]).with_suffix("").parts
    return ".".join(parts[:-1]) if parts[-1] == "__init__" else ".".join(parts)


def imports_of(path: Path) -> set[str]:
    """The `knee.*` modules this file imports, read from its syntax and never from its text."""
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
    return {name for name in names if name.split(".")[0] == "knee"}


def declares_contract(path: Path) -> bool:
    """Whether the module declares a compute contract, in EITHER of the two idioms the codebase uses.

    There are two, and a check that knew only the first reported two contracted kernels as missing
    theirs on 2026-10-11, which the lead then repeated to the founder as a defect. The literal
    reading of one idiom is not the obligation:

      CONTRACT = ComputeContract(...)        at module level (interiors, boundaries, ledger)
      @contracted(ComputeContract(...))      on the kernel  (profiles, band_raster)
    """
    tree = ast.parse(path.read_text())
    for node in tree.body:
        targets = (
            node.targets
            if isinstance(node, ast.Assign)
            else [node.target]
            if isinstance(node, ast.AnnAssign)
            else []
        )
        if any(isinstance(t, ast.Name) and t.id == "CONTRACT" for t in targets):
            return True
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for decorator in node.decorator_list:
            called = decorator.func if isinstance(decorator, ast.Call) else decorator
            if isinstance(called, ast.Name) and called.id == "contracted":
                return True
            if isinstance(called, ast.Attribute) and called.attr == "contracted":
                return True
    return False


def reached_from_route(on_disk: set[str]) -> set[str]:
    """The `knee.*` modules import-reachable from the route's entry point."""
    by_name = {
        name: relative
        for relative in on_disk
        if (name := module_name(relative)) is not None
    }
    seen, queue = set(), deque([ROUTE_ENTRY])
    while queue:
        name = queue.popleft()
        if name in seen or name not in by_name:
            continue
        seen.add(name)
        for imported in imports_of(ROOT / by_name[name]):
            # An import of `knee.a.b` may name a module or a symbol inside one; try both.
            for candidate in (imported, imported.rsplit(".", 1)[0]):
                if candidate in by_name and candidate not in seen:
                    queue.append(candidate)
    return seen


def main(argv: list[str]) -> int:
    registry = json.loads(REGISTRY.read_text())
    declared: dict[str, dict] = registry["places"]
    on_disk = modules_on_disk()
    reached = reached_from_route(on_disk)

    findings: dict[str, list[str]] = {
        "undeclared": sorted(on_disk - set(declared)),
        "absent": sorted(set(declared) - on_disk),
        "unreached": [],
        "misplaced": [],
        "contract_disagrees": [],
    }
    roles_unwritten: list[str] = []

    for relative, entry in sorted(declared.items()):
        if relative not in on_disk:
            continue
        path = ROOT / relative
        where = entry["where"]
        name = module_name(relative)
        if entry.get("role") is None:
            roles_unwritten.append(relative)
        if declares_contract(path) != bool(entry.get("contract")):
            findings["contract_disagrees"].append(
                f"{relative}: declared contract={entry.get('contract')}, module "
                f"{'defines' if declares_contract(path) else 'does not define'} CONTRACT"
            )
        if name is None:
            continue
        if where.startswith("route:") and name not in reached:
            findings["unreached"].append(
                f"{relative}: declared {where}, not reached from the route"
            )
        if where in ("shelf",) and name in reached:
            findings["misplaced"].append(
                f"{relative}: declared shelf, yet the route reaches it"
            )

    if "--json" in argv:
        print(json.dumps({**findings, "roles_unwritten": roles_unwritten}, indent=2))
        return 1 if any(findings.values()) else 0

    print(f"PLACES, computed against {REGISTRY.relative_to(ROOT)}\n")
    print(f"  modules in scope   {len(on_disk)}")
    print(f"  declared           {len(declared)}")
    print(f"  reached from {ROUTE_ENTRY}  {len(reached)}\n")
    for kind, rows in findings.items():
        if not rows:
            print(f"  {kind:<20} none")
            continue
        print(f"  {kind.upper():<20} {len(rows)}")
        for row in rows:
            print(f"      {row}")
    print(
        f"\n  role unwritten       {len(roles_unwritten)} of {len(declared)} "
        "-- nothing can check a role sentence, so it is counted, never passed"
    )
    print(
        "\n  NOT measured here: whether a reached module's work is consumed (`just graph`),\n"
        "  and anything below module scale -- a long function inside a reached module passes."
    )
    return 1 if any(findings.values()) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
