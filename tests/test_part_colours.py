"""Each part's colour in the pictures, and the word the legend calls it by, are that part's alone: a
part is told from its neighbours by its colour (`OBJECT_COLOURS` in `scripts/object_assignments.py`,
the renderer, a script beside the run, loaded here from its path). Whether two colours can be told
apart on the scans is read off the pictures themselves; these tests keep a word or a colour from
being given to two parts."""

import importlib.util
from itertools import combinations
from pathlib import Path

import numpy as np

from knee.objects.assignments import OBJECT_CODES

RENDERER = Path(__file__).resolve().parent.parent / "scripts" / "object_assignments.py"


def part_colours() -> dict[str, tuple[str, tuple[float, float, float, float]]]:
    spec = importlib.util.spec_from_file_location("object_assignments", RENDERER)
    assert spec is not None and spec.loader is not None
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    return renderer.OBJECT_COLOURS


def test_no_two_parts_share_a_word() -> None:
    words = [word for word, _ in part_colours().values()]
    assert sorted({word for word in words if words.count(word) > 1}) == []


def test_no_two_parts_share_a_colour() -> None:
    colours = [tuple(rgba[:3]) for _, rgba in part_colours().values()]
    assert sorted({colour for colour in colours if colours.count(colour) > 1}) == []


def test_no_two_colours_are_nearly_the_same() -> None:
    # Two colours nearer than this, in red, green and blue, read as one: the clashes this guards
    # against were 0.05 to 0.15 apart (the capsule's orange and the femur's 0.11), and the nearest
    # two earlier colours that read as two on the pictures, Hoffa's apricot and the suprapatellar
    # fat's lemon, are 0.21 apart (Claude's reading of the measured table, 2026-10-16). The colours
    # are compared as given, not as drawn over the scan; the pictures are the check of that.
    least = 0.2
    colours = {name: np.asarray(rgba[:3]) for name, (_, rgba) in part_colours().items()}
    near = [
        (first, second)
        for first, second in combinations(colours, 2)
        if np.linalg.norm(colours[first] - colours[second]) < least
    ]
    assert near == []


def test_every_coloured_part_is_a_part_the_run_names() -> None:
    # the renderer looks each part up in the run's codes where a slice saves no mask of its own
    assert sorted(set(part_colours()) - set(OBJECT_CODES)) == []
