"""Print the build loop with this project's live state filled in.

Why this is a command and not a paragraph. The loop is written in `docs/STAGE_CONTRACT.md` and the
way of working in `docs/SPINE.md`, and on 2026-10-11 the lead had both in context and built against
neither. What changed its behaviour that day was never prose: `just plan-status` printing 3/23,
Detective refusing to call two survivors equivalent, ruff failing the gate, an intent test failing.
Commands answer back; paragraphs do not. So the loop is something you RUN.

State here is computed, never written down (`AGENTS.md`, "Where truth lives"): the route reports
itself, and the renderers are read off the drawing package.

Every multi-line string below is parenthesised on purpose: an implicit concatenation inside a
collection turns one missing comma into two silently merged entries (ruff ISC004).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from knee.pictures import __file__ as pictures_file
from knee.pipeline import ROUTE

STEPS = (
    (
        "DECLARE IT",
        (
            "`just plan-status`, then add the task to the OpenSpec change before writing "
            "code. A change absorbed silently is the failure OpenSpec exists to stop -- and "
            "the declared tasks may already answer the question, or say another comes first."
        ),
    ),
    (
        "SAY WHY IT EXISTS",
        (
            "In the module docstring, against the thesis: which failure it answers, which "
            "section it instantiates, the founder's words where they settled it."
        ),
    ),
    (
        "WRITE THE PURE DECISION FIRST",
        (
            "Total over its arguments, returning NAMED CODES. Every bar it reads is an "
            "ARGUMENT, never a constant. Keep codes distinct wherever the remedies differ."
        ),
    ),
    (
        "DECLARE THE CONTRACTS",
        (
            "PEP 316 `pre:`/`post:`. State the real requirement: positive does not imply "
            "finite, and a `pre:` on a function the house requires to be TOTAL is a contract "
            "that contradicts itself."
        ),
    ),
    (
        "INTENT TESTS, BOTH SIGNS, CALLING DIRECTLY",
        (
            "Positive: what it must do. Negative: what it must never do. Never through a "
            "local helper -- Detective routes by STATIC path, and a test it cannot route is "
            "not a pin."
        ),
    ),
    (
        "CONVERGE, AND JUDGE EVERY SURVIVOR",
        (
            "`just detective converge <file>::<func>`. Prove equivalence in the --note, or "
            "name the must-not and enforce it with a test. A survivor is a verdict owed, "
            "never a line in a summary; 'candidate-equivalent' often means 'needs an input'."
        ),
    ),
    (
        "CROSSHAIR",
        (
            "`just crosshair <file>`. It reasons over paths where mutation samples inputs. "
            "Read the words exactly: `Not confirmed` is neither a violation nor a pass."
        ),
    ),
    (
        "WIRE IT",
        (
            "Into the production route, so something CONSUMES it. Then `just graph <out>` -- "
            "a value nothing consumes shows as dangling -- and `just imports` for the layer "
            "contract."
        ),
    ),
    (
        "RENDER IT",
        (
            "A stage is not `built` until it renders. The renderer only ARRANGES values the "
            "stage already computed; one that has to measure is evidence against the STAGE."
        ),
    ),
    (
        "RUN IT ON REAL DATA",
        (
            "Through Chapter 1's real entry point (`just analyze-objects`). A unit that has "
            "only seen synthetic data is not built -- measured the hard way, when the noise "
            "law passed every unit test and then concurred on 4 of 336 real series."
        ),
    ),
    (
        "GATE, THEN RECORD",
        (
            "`scripts/ci_local.sh > log 2>&1 && git add && git commit`, nothing between: a "
            "pipe hands `&&` the filter's status. Then the chapter's README, so a compaction "
            "costs one unit."
        ),
    ),
)

MEASURED = (
    (
        "An intent test caught a NaN seed that a characterization suite would have pinned as "
        "CORRECT: `np.maximum` propagates NaN, so a NaN-seeded accumulator made every "
        "reading unreadable."
    ),
    (
        "Writing the contract for CrossHair exposed a `pre:` that contradicted the totality "
        "law and stopped the symbolic check from ever exploring the refused path."
    ),
    (
        "Two 'candidate-equivalent' survivors were KILLABLE: a guard crept from `< 0.0` to "
        "`< -0.1`, and no synthesised input landed in the gap until a must-not declared one."
    ),
)


GROUNDING = (
    (
        "DISCARD THE SUMMARY",
        (
            "An auto-compaction summary is ANTI-CORRELATED with the truth and is never a source. "
            "Nothing in it is a premise. The verifiable record is git, the pre-compact snapshot "
            "the SessionStart hook names, and the files themselves."
        ),
    ),
    (
        "READ THE SNAPSHOT'S PROMPTS, WHOLE",
        (
            "The founder's words verbatim, mid-turn ones included, in consecutive parts. They are "
            "the one thing a summary cannot re-derive, and intent lives only there."
        ),
    ),
    (
        "READ THE ACTIVE WORK'S INDEX",
        (
            "docs/OBJECT_MODEL.md first -- the project's structure -- then "
            "docs/chapters/02-collapse/RESUME.md for the agreed sequence, and the chapter "
            "teachings.md files for the founder's rulings verbatim."
        ),
    ),
    (
        "THEN GIT",
        (
            "`git log` for what actually landed. A commit message in this repository states what "
            "was verified and what was left undone; prose elsewhere may be stale, git is not."
        ),
    ),
    (
        "COMPUTE THE STATE, NEVER RECALL IT",
        (
            "The route below, `just plan-status`, `just graph <out>`, `just gate`. Measured state "
            "is computed; a past measurement restated as current is not evidence."
        ),
    ),
)


def open_tasks() -> list[tuple[str, str]]:
    """The first open task of each declared change, read from its own checklist."""
    found: list[tuple[str, str]] = []
    changes = sorted((ROOT / "openspec" / "changes").glob("*/tasks.md"))
    for path in changes:
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("- [ ]"):
                found.append((path.parent.name, stripped[5:].strip()))
                break
    return found


def main() -> None:
    print("ENTERING A NEW SESSION -- do these first, in this order.\n")
    for number, (name, detail) in enumerate(GROUNDING, start=1):
        print(f"  {number}. {name}\n     {detail}\n")

    todo = open_tasks()
    if todo:
        print("THE NEXT OPEN TASK OF EACH DECLARED CHANGE, from its own checklist:\n")
        for change, task in todo:
            print(f"  {change}\n     {task[:300]}\n")

    print("THE BUILD LOOP -- run this, do not remember it.\n")
    for number, (name, detail) in enumerate(STEPS):
        print(f"  {number}. {name}\n     {detail}\n")

    print("MEASURED ON THIS PROJECT, each a thing that happened:\n")
    for note in MEASURED:
        print(f"  - {note}\n")

    print("THE ROUTE, as it reports itself:\n")
    drawn = {
        path.stem
        for path in Path(pictures_file).parent.glob("*.py")
        if path.stem != "__init__"
    }
    for stage, state in ROUTE:
        mark = "renders" if stage in drawn else "NO RENDERER"
        print(f"  {stage:<16} {state:<12} {mark}")
    print(
        f"\n  {len(drawn)} renderer(s) in knee.pictures; a stage may not claim built or "
        "partly without one\n"
    )
    print("NEXT, in this order:")
    print("  just plan-status        the declared change and what remains")
    print("  just plan-next          the task list, with what is already done")
    print("  just graph <out>        is anything dangling")
    print("  just gate               before every commit")


if __name__ == "__main__":
    main()
