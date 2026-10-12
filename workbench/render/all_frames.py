"""Draw EVERY stage of one saved run, in one pass, and index what was drawn.

Task 4b.2 of `openspec/changes/every-stage-renders`. The founder, 2026-10-12: *"this is a
production pipeline. Everything connected properly as a coherent instantiation of the thesis, as
the thesis itself lays out."* And on scope: *"there is no such thing as a 'small piece' of a single
object. All of it."*

**Why this exists.** Measured on 2026-10-12: the one compute command, with every switch enabled,
produced **zero images**, while fourteen drawing scripts sat in this directory waiting to be typed
by hand with their own run directory, study identifier and output directory. That is the shape the
founder named at 23:28 on 2026-10-11 — *"just functionalities in islands, entire unto
themselves."* Each renderer now exposes one `draw(run, study_uid, out)`; this module calls them.

**Nothing here draws anything itself.** It imports each renderer lazily, calls its `draw`, and
collects the manifests. Matplotlib is reached only through those imports, so a run with pictures
switched off never loads it and `knee` still never imports it at all.

**One renderer failing never fails the run.** The founder's rule is that a missing reading is a
named silence, never a negative, and the same holds for a missing picture: a stage whose drawer
raises is recorded as `not_drawn` with the reason, the remaining stages still draw, and the index
says which is which. A half-drawn gallery that says so is worth more than no gallery.

**Every route stage is named, drawn or not.** A stage with no drawer at all appears as
`no_drawer`, so the index is a complete map of the route rather than a list of successes.
"""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path

#: Each drawing this run produces: the name it is filed under, and the module whose `draw` makes
#: it. Several belong to one route stage -- `objects` is drawn four ways, because four different
#: things were resolved there and one picture cannot show them.
DRAWINGS: tuple[tuple[str, str, str], ...] = (
    ("study", "packet", "object_packet"),
    ("objects", "interiors", "object_interiors"),
    ("objects", "boundaries", "object_boundaries"),
    ("objects", "conversation", "object_conversation"),
    ("lenses", "digits", "lens_frames"),
    ("ownership", "partition", "partition_frames"),
    ("relations", "pairings", "pair_frames"),
    ("predicates", "findings", "predicate_frames"),
)


def route_stages() -> tuple[str, ...]:
    """The route's own stage names, so the index is a map of the route and not of this file."""
    from knee.pipeline import ROUTE

    return tuple(stage for stage, _ in ROUTE)


def draw_all(run: Path, study_uid: str, out: Path) -> dict:
    """Draw every stage of one saved run; return the index of what was drawn and what was not.

    Total over the renderers: one that raises is recorded with its named reason and the rest still
    draw. The index carries every route stage, including those no drawer covers.
    """
    data_root = Path(__file__).resolve().parents[2] / "data"
    output = out.resolve()
    if not output.is_relative_to(data_root.resolve()):
        raise ValueError("out must be under the project's private data directory")
    output.mkdir(parents=True, exist_ok=True)

    drawings: list[dict] = []
    for stage, name, module_name in DRAWINGS:
        target = output / f"{stage}-{name}"
        entry: dict = {"stage": stage, "drawing": name, "renderer": module_name}
        try:
            module = importlib.import_module(f"workbench.render.{module_name}")
            manifest = module.draw(run, study_uid, target)
            entry["code"] = "drawn"
            entry["out"] = str(target.relative_to(output))
            entry["image"] = (
                manifest.get("image") if isinstance(manifest, dict) else None
            )
        except Exception as refusal:
            # A drawer that cannot draw is a named silence, never a failed run.
            entry["code"] = "not_drawn"
            entry["why"] = f"{type(refusal).__name__}: {refusal}"
        drawings.append(entry)

    covered = {stage for stage, _, _ in DRAWINGS}
    uncovered = [
        {"stage": stage, "code": "no_drawer"}
        for stage in route_stages()
        if stage not in covered
    ]
    index = {
        "schema": "all-frames-v1",
        "study_uid": study_uid,
        "run": str(run),
        "drawn": sum(1 for d in drawings if d["code"] == "drawn"),
        "not_drawn": sum(1 for d in drawings if d["code"] == "not_drawn"),
        "route_stages_without_a_drawer": uncovered,
        "drawings": drawings,
    }
    (output / "index.json").write_text(
        json.dumps(index, indent=2, allow_nan=False) + "\n"
    )
    return index


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--study-uid", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        index = draw_all(args.run, args.study_uid, args.out)
    except ValueError as refusal:
        parser.error(str(refusal))
    print(
        json.dumps(
            {
                "drawn": index["drawn"],
                "not_drawn": index["not_drawn"],
                "index": str(args.out.resolve() / "index.json"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
