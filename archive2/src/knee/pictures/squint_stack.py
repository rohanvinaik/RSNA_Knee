"""What the squint over the stack resolved, drawn: tile medians at the walked slices, over the acquired planes.

The funnel's operation 1 (`openspec/changes/the-funnel/design.md` R1, task 1.2):
`knee.collapse.squint_stack.read_squint_stack` squints every slice of a series in millimetres and
places every tile's centre in the scanner's frame. Its picture is the squint's medians at the
slices the study stage's own walk visits (`knee.study.series.walk_indices`, retained on the
series as `Series.walk`), each laid over the acquired plane at that slice by the stack's saved
native bounds, so a reader sees the coarse view sit on the knee it was taken from.

Every value here is one the stage computed and the writer saved. Selecting the walked slices
from the stack is ARRANGING: it chooses which stored values to show and alters none of them
(as `knee.pictures.study.panels` says of the walk). Nothing here measures, thresholds, squints
or recomputes a centre; a stack that was not made, or a walked slice the stack does not hold, is
a named silence in words, never an empty picture. The one decision, `walk_standing`, is pure and
total and names what one walked slice of the picture can be.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from knee.collapse.squint_stack import STACK_CODES

#: What one walked slice of the picture can be. `squinted` is a reading drawn; the rest are the
#: silences, each with its own remedy: this run's writer saved no stack, the stage made none
#: (its own code says why), the walked slice lies outside the stack the stage squinted, or the
#: saved code is a word the stage does not say.
WALK_STANDINGS: tuple[str, ...] = (
    "squinted",
    "stack_not_saved",
    "stack_absent",
    "slice_outside_stack",
    "stack_code_unknown",
)


def walk_standing(code: object, index: object, slices: int) -> str:
    """Name what one walked slice of the picture can show, from the stack's saved code and size.

    `code` is the stack's saved code (`STACK_CODES`), or None when the writer saved no stack;
    `index` the walked slice's stack index; `slices` how many slices the saved stack holds.
    Total: no saved stack is `stack_not_saved`; a code the stage does not say, or one that is not
    text, is `stack_code_unknown`, named and never drawn; a stack the stage did not make is
    `stack_absent`; an index that is not a whole number inside the stack is
    `slice_outside_stack`; else the slice is `squinted`. It selects nothing and counts nothing.

    post: __return__ in WALK_STANDINGS
    """
    if code is None:
        return "stack_not_saved"
    if not isinstance(code, str) or code not in STACK_CODES:
        return "stack_code_unknown"
    if code != "present":
        return "stack_absent"
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < slices:
        return "slice_outside_stack"
    return "squinted"


@dataclass(frozen=True, slots=True)
class WalkedSquint:
    """One walked slice of the picture: the acquired plane at that slice, and the stack's squint there.

    index: the walked index AS THE WRITER SAVED IT, handed through unchanged: an int inside the
    stack when `standing` is `squinted`, else whatever was saved (a number that is not whole, a
    word), which the standing names rather than rounds. standing: from `WALK_STANDINGS`. plane:
    (rows, columns) in the dtype it was saved in, the study stage's retained walk at this step,
    or None when the writer saved no walk. median, coverage: (tiles_down, tiles_across) float64,
    the stack's maps at this slice when `standing` is `squinted`, else None. Nothing is derived.
    """

    index: object
    standing: str
    plane: np.ndarray | None
    median: np.ndarray | None
    coverage: np.ndarray | None


@dataclass(frozen=True, slots=True)
class SquintStackPanels:
    """One series' saved squint stack, AS THE WRITER SAVED IT, ready for the workbench to draw.

    code, why: the stack's standing as saved, or None when the record carries no stack at all.
    tile_mm: the bar the grid was made with. tile_shape_rc: native pixels per tile (rows,
    columns). slices: how many slices the saved stack holds (0 when none). median, coverage:
    (Z, tiles_down, tiles_across) float64, the stack's maps over every slice, NaN in a tile with
    no finite pixel; None when none was saved. bounds_rc: (tiles_down, tiles_across, 4) int64,
    the half-open native bounds every slice shares; None when none was saved. walked: one
    `WalkedSquint` per step of the study stage's walk, in walk order. An absent value stays
    absent, never a zero.
    """

    code: str | None
    why: str | None
    tile_mm: float | None
    tile_shape_rc: tuple[int, int] | None
    slices: int
    median: np.ndarray | None
    coverage: np.ndarray | None
    bounds_rc: np.ndarray | None
    walked: tuple[WalkedSquint, ...]


def _at(maps: np.ndarray | None, index: object, standing: str) -> np.ndarray | None:
    """The stack's map at one walked slice, or None: a selection made only where the standing
    says the slice is squinted, which `walk_standing` says only for a whole number inside the
    stack. The `isinstance` restates that guarantee for the reader and the checker; it decides
    nothing."""
    if standing != "squinted" or maps is None or not isinstance(index, int):
        return None
    return maps[index]


def stack_panels(
    code: str | None,
    why: str | None,
    tile_mm: float | None,
    tile_shape_rc: tuple[int, int] | None,
    median: np.ndarray | None,
    coverage: np.ndarray | None,
    bounds_rc: np.ndarray | None,
    walk_indices: tuple[object, ...],
    walk: np.ndarray | None,
) -> SquintStackPanels:
    """Hand on one series' saved squint stack beside the study stage's saved walk, reading neither.

    Every argument is a value a stage computed and the writer saved: the stack's code, bar and
    grid, its `median` and `coverage` over every slice and its `bounds_rc`, and the study stage's
    `walk_indices` with the `walk` of planes at them. For each walked step this hands the saved
    index to `walk_standing` AS SAVED, never coerced, so an index that is not a whole number
    inside the stack (2.7, a word, None) is named `slice_outside_stack` rather than rounded into
    a slice or raised; it selects the stack's maps at that index where the standing says the
    slice is squinted, and names the silence otherwise. The maps are handed on as float64 and
    the bounds as int64; the planes keep their saved dtype. Nothing is measured, resampled or
    derived, and an absent value stays absent.
    """
    maps = None if median is None else np.asarray(median, dtype=np.float64)
    shares = None if coverage is None else np.asarray(coverage, dtype=np.float64)
    slices = 0 if maps is None else int(maps.shape[0])
    walked = []
    for step, index in enumerate(walk_indices):
        standing = walk_standing(code, index, slices)
        plane = None if walk is None or step >= len(walk) else np.asarray(walk[step])
        walked.append(
            WalkedSquint(
                index=index,
                standing=standing,
                plane=plane,
                median=_at(maps, index, standing),
                coverage=_at(shares, index, standing),
            )
        )
    return SquintStackPanels(
        code=code,
        why=why,
        tile_mm=None if tile_mm is None else float(tile_mm),
        tile_shape_rc=None
        if tile_shape_rc is None
        else (int(tile_shape_rc[0]), int(tile_shape_rc[1])),
        slices=slices,
        median=maps,
        coverage=shares,
        bounds_rc=None if bounds_rc is None else np.asarray(bounds_rc, dtype=np.int64),
        walked=tuple(walked),
    )
