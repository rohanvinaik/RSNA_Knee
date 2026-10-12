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

#: EVERY layer's entry point, because every layer has one and each was previously unchecked.
#:
#: Until 2026-10-12 this file asked one question -- is a `route:*` module reached from
#: `knee.pipeline` -- and asked it of 46 modules out of 97. The other 51 were never checked by
#: anything, which is how `knee/pictures/collapse.py` sat with ZERO callers while describing a
#: stage shape that has never existed, and how three stages ended up with no drawer at all.
#:
#: Reachability from `knee.pipeline` is the WRONG question for the drawing and workbench layers:
#: production must never import a picture (that is the layer contract, and `just imports` gates
#: it), and the workbench imports the route rather than the reverse. So each layer is walked from
#: the thing that actually calls it.
ENTRY_POINTS: tuple[tuple[str, str], ...] = (
    ("knee.pipeline", "the production route"),
    ("workbench.measure.object_analysis", "the real entry point"),
    ("workbench.render.all_frames", "the joined drawing pass"),
)


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


def importable_name(relative: str) -> str | None:
    """Any importable module's dotted name: `knee.*` under src/, `workbench.*` at the root.

    `scripts/` is deliberately None: those are run by path from the justfile, never imported, so
    import reachability is not the question to ask of them.
    """
    if relative.startswith("src/"):
        return module_name(relative)
    if relative.startswith("workbench/"):
        parts = Path(relative).with_suffix("").parts
        return ".".join(parts[:-1]) if parts[-1] == "__init__" else ".".join(parts)
    return None


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
    # `workbench` as well as `knee`: the drawing layer and the entry point are imported from the
    # workbench, so a walk restricted to `knee` cannot see whether a renderer is ever called.
    return {name for name in names if name.split(".")[0] in ("knee", "workbench")}


def reached_from(entries: tuple[str, ...], on_disk: set[str]) -> set[str]:
    """Every module import-reachable from any of `entries`, across `knee` and `workbench`.

    `all_frames` imports each renderer lazily inside its loop, from a table of module names rather
    than with an `import` statement, so a renderer it drives is NOT reachable by syntax. Those
    names are read from the table itself below, which is why a stage with no entry there shows up
    here as unwired -- which is exactly the state `collapse`, `vectors` and `output` are in.
    """
    by_name = {
        name: relative
        for relative in on_disk
        if (name := importable_name(relative)) is not None
    }
    seen, queue = set(), deque(entries)
    # `scripts/*.py` are entry points too: the justfile runs them by PATH, so they are never
    # imported and carry no dotted name, yet what they import is wired. Seeding the walk with
    # their imports is the difference between `object_measurements.py` reading as an island and
    # reading as what it is -- the development graph that `scripts/object_graph.py` drives.
    for relative in sorted(on_disk):
        if relative.startswith("scripts/"):
            queue.extend(imports_of(ROOT / relative))
    while queue:
        name = queue.popleft()
        if name in seen or name not in by_name:
            continue
        seen.add(name)
        path = ROOT / by_name[name]
        imported_names = imports_of(path)
        if name == "workbench.render.all_frames":
            imported_names |= {
                f"workbench.render.{module}" for module in drawing_table(path)
            }
        for imported in imported_names:
            for candidate in (imported, imported.rsplit(".", 1)[0]):
                if candidate in by_name and candidate not in seen:
                    queue.append(candidate)
    return seen


def drawing_table(path: Path) -> set[str]:
    """The renderer module names `all_frames.DRAWINGS` drives, read from its syntax.

    They are imported by name at run time, not with an `import` statement, so nothing else can see
    them. Read here so a renderer that IS driven counts as wired and one that is not shows plainly.
    """
    tree = ast.parse(path.read_text())
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else []
        if isinstance(node, ast.AnnAssign):
            targets = [node.target]
        if not any(isinstance(t, ast.Name) and t.id == "DRAWINGS" for t in targets):
            continue
        return {
            element.elts[-1].value
            for element in ast.walk(node)
            if isinstance(element, ast.Tuple)
            and len(element.elts) == 3
            and isinstance(element.elts[-1], ast.Constant)
            and isinstance(element.elts[-1].value, str)
        }
    return set()


def declares_contract(path: Path) -> bool:
    """Whether the module declares a compute contract at all.

    The codebase now uses ONE form, settled by the founder 2026-10-12 ("I guess only one? … the
    bigger risk is you forgetting that there are two formats"):

      CONTRACT = ComputeContract(...)        named at module level, where a reader meets it
      @contracted(CONTRACT)                  applied to the kernel its `reference` field names

    Both halves are still recognised here, deliberately, because this check must keep seeing a
    module that has only one of them -- that is the half-built state, not a passing one. It is
    MODULE-scale and therefore blind to the defect that mattered: a CONTRACT declared and attached
    to nothing, which three modules carried in production. `tests/knee/test_compute_contracts.py`
    is what refuses that, and it gates.
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


def stage_package(relative: str, where: str) -> bool:
    """Whether a declared module is the `__init__.py` of a route stage's package."""
    return where.startswith("route:") and relative.endswith("__init__.py")


def stage_count(declared: dict[str, dict]) -> int:
    """How many route stages the registry declares, counted over every declared entry."""
    return sum(
        1
        for relative, entry in declared.items()
        if stage_package(relative, entry["where"])
    )


def contract_disagrees_rows(relative: str, entry: dict, path: Path) -> list[str]:
    """The `contract_disagrees` row of one module: empty when its declaration and source agree."""
    if declares_contract(path) != bool(entry.get("contract")):
        return [
            (
                f"{relative}: declared contract={entry.get('contract')}, module "
                f"{'defines' if declares_contract(path) else 'does not define'} CONTRACT"
            )
        ]
    return []


def unwired_rows(
    relative: str, where: str, entries: tuple[str, ...], wired: set[str]
) -> list[str]:
    """The `unwired` row of one module: empty unless it is importable and no entry point reaches it."""
    # EVERY layer, against its own entry point. `script` is excluded because the justfile runs
    # those by path rather than importing them, so import reachability asks the wrong thing.
    importable = importable_name(relative)
    if (
        importable is not None
        and where != "script"
        and importable not in entries
        and importable not in wired
    ):
        return [f"{relative}: declared {where}, nothing reaches it"]
    return []


def unreached_rows(
    relative: str, where: str, name: str, reached: set[str]
) -> list[str]:
    """The `unreached` row of one module: empty unless it is declared on the route and unreached."""
    if where.startswith("route:") and name not in reached:
        return [f"{relative}: declared {where}, not reached from the route"]
    return []


def misplaced_rows(
    relative: str, where: str, name: str, reached: set[str]
) -> list[str]:
    """The `misplaced` row of one module: empty unless it is declared shelf and the route reaches it."""
    if where in ("shelf",) and name in reached:
        return [f"{relative}: declared shelf, yet the route reaches it"]
    return []


def renders_missing_rows(
    relative: str, entry: dict, declared: dict[str, dict], on_disk: set[str]
) -> list[str]:
    """The `renders_missing` row of one stage: empty unless its named picture module is missing or misplaced."""
    drawn = entry.get("renders")
    if drawn is None:
        return []
    picture = f"src/knee/pictures/{drawn}.py"
    if picture not in on_disk:
        return [f"{relative}: declares renders={drawn}, but {picture} does not exist"]
    if declared.get(picture, {}).get("where") != "pictures":
        return [f"{relative}: {picture} is not declared in the drawing layer"]
    return []


def scan_declared(
    declared: dict[str, dict],
    on_disk: set[str],
    reached: set[str],
    wired: set[str],
    entries: tuple[str, ...],
) -> tuple[dict[str, list[str]], list[str], list[str]]:
    """Every finding list, then the modules with no role sentence and the stages with no frame."""
    findings: dict[str, list[str]] = {
        "undeclared": sorted(on_disk - set(declared)),
        "absent": sorted(set(declared) - on_disk),
        "unreached": [],
        "unwired": [],
        "misplaced": [],
        "contract_disagrees": [],
        "renders_missing": [],
    }
    roles_unwritten: list[str] = []
    frames_unwritten: list[str] = []

    for relative, entry in sorted(declared.items()):
        if relative not in on_disk:
            continue
        path = ROOT / relative
        where = entry["where"]
        name = module_name(relative)
        if entry.get("role") is None:
            roles_unwritten.append(relative)
        findings["contract_disagrees"].extend(
            contract_disagrees_rows(relative, entry, path)
        )
        findings["unwired"].extend(unwired_rows(relative, where, entries, wired))

        if name is None:
            continue
        findings["unreached"].extend(unreached_rows(relative, where, name, reached))
        findings["misplaced"].extend(misplaced_rows(relative, where, name, reached))
        if not stage_package(relative, where):
            continue
        # A stage names the picture module that draws it. The name is checkable; whether that
        # picture arranges STUDY values or PIPELINE state is not, so `frame` is counted below.
        if entry.get("frame") is None:
            frames_unwritten.append(relative)
        findings["renders_missing"].extend(
            renders_missing_rows(relative, entry, declared, on_disk)
        )
    return findings, roles_unwritten, frames_unwritten


def exit_code(findings: dict[str, list[str]]) -> int:
    """The check's exit status: 1 when any finding kind holds a row, else 0."""
    return 1 if any(findings.values()) else 0


def print_json(
    findings: dict[str, list[str]],
    roles_unwritten: list[str],
    frames_unwritten: list[str],
) -> None:
    """Print the findings and the two unwritten lists as JSON."""
    print(
        json.dumps(
            {
                **findings,
                "roles_unwritten": roles_unwritten,
                "frames_unwritten": frames_unwritten,
            },
            indent=2,
        )
    )


def print_scope(
    declared: dict[str, dict], on_disk: set[str], reached: set[str], wired: set[str]
) -> None:
    """Print the report's header: what it was computed against and how far each walk reached."""
    print(f"PLACES, computed against {REGISTRY.relative_to(ROOT)}\n")
    print(f"  modules in scope   {len(on_disk)}")
    print(f"  declared           {len(declared)}")
    print(f"  reached from {ROUTE_ENTRY}  {len(reached)}")
    print(f"  wired to ANY entry point    {len(wired)}")
    for entry, what in ENTRY_POINTS:
        print(f"      {entry}  ({what})")
    print()


def print_findings(findings: dict[str, list[str]]) -> None:
    """Print each finding kind with its rows, or `none` when it holds no row."""
    for kind, rows in findings.items():
        if not rows:
            print(f"  {kind:<20} none")
            continue
        print(f"  {kind.upper():<20} {len(rows)}")
        for row in rows:
            print(f"      {row}")


def print_unwritten(
    declared: dict[str, dict],
    roles_unwritten: list[str],
    frames_unwritten: list[str],
    stages: int,
) -> None:
    """Print the two counts that are never passed, and what the check does not measure."""
    print(
        f"\n  role unwritten       {len(roles_unwritten)} of {len(declared)} "
        "-- nothing can check a role sentence, so it is counted, never passed"
    )
    print(
        f"  frame unwritten      {len(frames_unwritten)} of {stages} stages "
        "-- whether a stage's picture arranges STUDY values or PIPELINE state;\n"
        "                       also uncheckable, so also counted and never passed"
    )
    print(
        "\n  NOT measured here: whether a reached module's work is consumed (`just graph`),\n"
        "  and anything below module scale -- a long function inside a reached module passes."
    )


def main(argv: list[str]) -> int:
    """Compute the findings against the registry, print them, and return the exit status."""
    registry = json.loads(REGISTRY.read_text())
    declared: dict[str, dict] = registry["places"]
    on_disk = modules_on_disk()
    reached = reached_from_route(on_disk)
    entries = tuple(entry for entry, _ in ENTRY_POINTS)
    wired = reached_from(entries, on_disk)
    stages = stage_count(declared)
    findings, roles_unwritten, frames_unwritten = scan_declared(
        declared, on_disk, reached, wired, entries
    )

    if "--json" in argv:
        print_json(findings, roles_unwritten, frames_unwritten)
        return exit_code(findings)

    print_scope(declared, on_disk, reached, wired)
    print_findings(findings)
    print_unwritten(declared, roles_unwritten, frames_unwritten, stages)
    return exit_code(findings)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
