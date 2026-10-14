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

A drawer that cannot arrange its input may also RETURN a manifest whose `refusal` is a named code,
with `why` saying it in words, instead of raising. The index records that as `not_drawn` with the
code and the reason, exactly as it records a drawer that raised, so a manifest is never read as a
drawing merely because nothing was raised.

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
#:
#: What four of them now show, so the index and the pictures can be read against each other:
#:   collapse/field       the squint's four maps and the regime key by name, the whole-series
#:                        histogram with the background split marked, the spread ratio beside the
#:                        Gaussian reference, and the field's structural reading (the air, the
#:                        closed leg, the squint inside it, the profile along the header's axis, the
#:                        two basins and the seam, the darkest places and the bodies, the air's own
#:                        histogram), one block per series
#:   study/recorded       the selected plane and the stage's walk, with the superior end named from
#:                        the field stage's saved header codes
#:   objects/conversation each subdivision with `parted_more_by`, the count the adapter makes of
#:                        the saved concurrent and conditional labels
#:   vectors/bundles      each object's banks, with the backend the stage was asked for and the gap
#:                        fraction of every other acquisition's own stack
#:   study/views          one sheet PER VIEW: the acquired plane under every reading that wrote at
#:                        its places, every stage in route order, a silence said in its own panel
#:                        (the founder, 2026-10-12: "one of each view ... along with every single
#:                        analysis lens view that has something to say ... on the original image")
#:   collapse/squint_stack the funnel's operation 1 (the-funnel task 1.2): per series, the
#:                        squint stack's tile medians at the study stage's walked slices, each
#:                        over the acquired plane at that slice and placed by the stack's own
#:                        saved native bounds
#:   collapse/lineup      the funnel's operation 3a (the-funnel task 3a.2): per paired plane,
#:                        the recipient's tile grid over its acquired plane at the selected
#:                        slice with the partner's tile centres placed in the recipient's own
#:                        native frame, each recipient tile tinted by its match code; and the
#:                        nearest partner slice per recipient slice by its slab code
#:   collapse/first_lens  the funnel's operation 2 (the-funnel task 2.3): ONE SHEET PER VIEW,
#:                        every tile of the study stage's walked slices by its code over the
#:                        acquired plane at that slice, placed by the squint stack's own saved
#:                        bounds: background red at a low alpha, undecided amber, not
#:                        background untouched, a tile with no finite pixel grey -- the
#:                        founder's eye-check (task 2.4, E1)
#:   lenses/tile_digits   the funnel's operation 3b (the-funnel task 3b.3): ONE SHEET PER VIEW,
#:                        every tile of the walked slices by its digit against the series' own
#:                        kept-tile terciles, over the acquired plane at that slice and placed
#:                        by the stack's saved bounds: below, at and above in three colours,
#:                        every silence in one neutral tone named silence
#:   lenses/conjunction   the funnel's operation 3c (the-funnel task 3c.2): ONE SHEET PER
#:                        RECIPIENT (the fat-dark series of a paired plane), every tile of
#:                        the walked slices by its conjunction code, the partner's digit and
#:                        the recipient's own read together as <partner>_<own>, over the
#:                        acquired plane at that slice and placed by the stack's saved bounds:
#:                        the nine pairs in nine colours, the silences and the unmatched tile
#:                        in neutral tones; a study with no recipient says so in words
#:   collapse/depth       the funnel's operation 4 (the-funnel task 4.5): ONE SHEET PER
#:                        SERIES, the four cheap readings per slice as curves over the stack
#:                        with each lens's chosen slice marked on its own curve and named in
#:                        the legend with its word, and the chosen slices themselves: the
#:                        acquired plane where this run saved one, else the squint's tile
#:                        medians at that slice, each titled with the lenses that chose it --
#:                        the founder's eye-check (task 4.6, E2)
DRAWINGS: tuple[tuple[str, str, str], ...] = (
    ("study", "recorded", "study_frames"),
    ("collapse", "field", "field_frames"),
    ("collapse", "squint_stack", "squint_stack_frames"),
    ("collapse", "lineup", "lineup_frames"),
    ("collapse", "first_lens", "first_lens_frames"),
    ("lenses", "tile_digits", "tile_digit_frames"),
    ("lenses", "conjunction", "conjunction_frames"),
    ("collapse", "depth", "depth_frames"),
    ("objects", "packet", "object_packet"),
    ("objects", "interiors", "object_interiors"),
    ("objects", "boundaries", "object_boundaries"),
    ("objects", "conversation", "object_conversation"),
    ("lenses", "digits", "lens_frames"),
    ("ownership", "partition", "partition_frames"),
    ("relations", "pairings", "pair_frames"),
    ("predicates", "findings", "predicate_frames"),
    ("vectors", "bundles", "bundle_frames"),
    ("output", "companion", "output_frames"),
    ("study", "views", "view_frames"),
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
            named = manifest.get("refusal") if isinstance(manifest, dict) else None
            if named is None:
                entry["code"] = "drawn"
                entry["out"] = str(target.relative_to(output))
                entry["image"] = (
                    manifest.get("image") if isinstance(manifest, dict) else None
                )
            else:
                entry["code"] = "not_drawn"
                entry["why"] = f"{named}: {manifest.get('why', '')}"
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
