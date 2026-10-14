"""What the first lens resolved, drawn: every tile of the walked slices by its code, over the acquired planes.

The funnel's operation 2 (`openspec/changes/the-funnel/design.md` R2, task 2.3):
`knee.collapse.first_lens.read_first_lens` names every tile of every slice of a series
background, not_background, undecided or empty under the series' own split, once, and the record is
frozen. Its picture is the one the founder checks by eye (task 2.4, E1): per view, the tiles by
code over the acquired plane at the slices the study stage's own walk visits
(`knee.study.series.walk_indices`, retained on the series as `Series.walk`), each tile placed in
native pixels by the squint stack's saved bounds, so a reader can see whether any background
tile holds a part of the knee and whether the undecided ring sits where the skin is.

Every value here is one the stage computed and the writer saved. Selecting the walked slices
from the saved codes is ARRANGING: it chooses which stored values to show and alters none of
them (as `knee.pictures.squint_stack.stack_panels` does with the stack). Nothing here
thresholds, labels, dilates or recomputes a code; a lens that was not saved, one the stage did
not make, or a walked slice the lens does not hold, is a named silence in words, never an empty
picture. The one decision, `walk_standing`, is pure and total and names what one walked slice
of the picture can be.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from knee.collapse.first_lens import LENS_CODES

#: What one walked slice of the picture can be. `named` is a reading drawn: every tile at that
#: slice carries a code, whether the lens read a valley (`present`) or had none to read and
#: cleared nothing (`split_unavailable`, every tile with a finite pixel not_background). The rest are the
#: silences, each with its own remedy: this run's writer saved no first lens for the series;
#: the saved code is a word the stage does not say; the stage named no tile (its own code says
#: why: its stack was absent); the walked slice lies outside the slices the lens holds.
LENS_STANDINGS: tuple[str, ...] = (
    "named",
    "lens_not_saved",
    "lens_code_unknown",
    "lens_absent",
    "slice_outside_lens",
)


def walk_standing(code: object, index: object, slices: int) -> str:
    """Name what one walked slice of the picture can show, from the lens's saved code and size.

    `code` is the lens's saved code (`LENS_CODES`), or None when the writer saved no lens;
    `index` the walked slice's stack index; `slices` how many slices the saved codes hold.
    Total: no saved lens is `lens_not_saved`; a code the stage does not say, or one that is not
    text, is `lens_code_unknown`, named and never drawn; a lens whose stack was absent is
    `lens_absent`; an index that is not a whole number inside the lens is `slice_outside_lens`;
    else the slice is `named`. It selects nothing and counts nothing.

    post: __return__ in LENS_STANDINGS
    """
    if code is None:
        return "lens_not_saved"
    if not isinstance(code, str) or code not in LENS_CODES:
        return "lens_code_unknown"
    if code == "predecessor_absent":
        return "lens_absent"
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < slices:
        return "slice_outside_lens"
    return "named"


@dataclass(frozen=True, slots=True)
class WalkedLens:
    """One walked slice of the picture: the acquired plane at that slice, and the lens's codes there.

    index: the stack index the walk visits. standing: from `LENS_STANDINGS`. plane: (rows,
    columns) in the dtype it was saved in, the study stage's retained walk at this step, or None
    when the writer saved no walk. codes: (tiles_down, tiles_across) uint8 indexing the stage's
    `TILE_CODES`, the lens's codes at this slice when `standing` is `named`, else None. Nothing
    is derived.
    """

    index: int
    standing: str
    plane: np.ndarray | None
    codes: np.ndarray | None


@dataclass(frozen=True, slots=True)
class FirstLensPanels:
    """One series' saved first lens, AS THE WRITER SAVED IT, ready for the workbench to draw.

    code, why: the lens's standing as saved, or None when the record carries no lens at all.
    split: the valley the rule read, None where the writer saved none (the stage read NaN).
    rule_version: the rule that made the reading, as saved. counts: the number of tiles under
    each code over every slice, in the stage's `TILE_CODES` order, as saved; None when none was
    saved. slices: how many slices the saved codes hold (0 when none). codes: (Z, tiles_down,
    tiles_across) uint8 over every slice; None when none was saved. bounds_rc: (tiles_down,
    tiles_across, 4) int64, the squint stack's saved half-open native bounds that place the
    tiles; None when none was handed on. walked: one `WalkedLens` per step of the study stage's
    walk, in walk order. An absent value stays absent, never a zero.
    """

    code: str | None
    why: str | None
    split: float | None
    rule_version: str | None
    counts: tuple[int, ...] | None
    slices: int
    codes: np.ndarray | None
    bounds_rc: np.ndarray | None
    walked: tuple[WalkedLens, ...]


def lens_panels(
    code: str | None,
    why: str | None,
    split: float | None,
    rule_version: str | None,
    counts: tuple[int, ...] | None,
    codes: np.ndarray | None,
    bounds_rc: np.ndarray | None,
    walk_indices: tuple[int, ...],
    walk: np.ndarray | None,
) -> FirstLensPanels:
    """Hand on one series' saved first lens beside the study stage's saved walk, reading neither.

    Every argument is a value a stage computed and the writer saved: the lens's code, split,
    rule and counts, its `codes` over every slice, the squint stack's saved `bounds_rc`, and the
    study stage's `walk_indices` with the `walk` of planes at them. For each walked step this
    selects the lens's codes at that index where `walk_standing` says the slice is named, and
    names the silence otherwise. The codes are handed on as uint8 and the bounds as int64; the
    planes keep their saved dtype. Nothing is measured, resampled or derived, and an absent
    value stays absent.
    """
    named = None if codes is None else np.asarray(codes, dtype=np.uint8)
    slices = 0 if named is None else int(named.shape[0])
    walked = []
    for step, index in enumerate(walk_indices):
        standing = walk_standing(code, int(index), slices)
        plane = None if walk is None or step >= len(walk) else np.asarray(walk[step])
        walked.append(
            WalkedLens(
                index=int(index),
                standing=standing,
                plane=plane,
                codes=named[int(index)]
                if standing == "named" and named is not None
                else None,
            )
        )
    return FirstLensPanels(
        code=code,
        why=why,
        split=None if split is None else float(split),
        rule_version=rule_version,
        counts=None if counts is None else tuple(int(count) for count in counts),
        slices=slices,
        codes=named,
        bounds_rc=None if bounds_rc is None else np.asarray(bounds_rc, dtype=np.int64),
        walked=tuple(walked),
    )
