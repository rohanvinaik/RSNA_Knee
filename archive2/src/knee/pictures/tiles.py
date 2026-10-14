"""What the tile digits resolved, drawn: every tile of the walked slices by its digit, over the acquired planes.

The funnel's operation 3b (`openspec/changes/the-funnel/design.md` R3b, task 3b.3):
`knee.lenses.tiles.read_tile_digits` names every tile of every slice of a series below, at or
above the terciles of the tiles the first lens did not clear, and every other tile silent. Its
picture is the digit grid over the acquired plane at the slices the study stage's own walk
visits (`knee.study.series.walk_indices`, retained on the series as `Series.walk`), each tile
placed in native pixels by the squint stack's saved bounds and every silence drawn as silence,
so a reader can see where the bright, the middle and the dark thirds of the kept tiles lie on
the knee (task 3b.2's check: on the fat-bright coronal, whether the `above` tiles lie inside
the two big bright regions).

Every value here is one the stage computed and the writer saved. Selecting the walked slices
from the saved codes and digits is ARRANGING: it chooses which stored values to show and
alters none of them (as `knee.pictures.first_lens.lens_panels` does with the lens). Nothing
here thresholds, re-reads an edge or recomputes a digit; digits that were not saved, that the
stage did not make, or a walked slice the digits do not hold, is a named silence in words,
never an empty picture. The one decision, `walk_standing`, is pure and total and names what
one walked slice of the picture can be.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from knee.lenses.tiles import TILE_DIGIT_CODES

#: What one walked slice of the picture can be. `named` is a reading drawn: every tile at that
#: slice carries a digit code, whether the oracle read a pair of edges (`present`) or gave none
#: and left every tile silent (`no_edges`, `population_too_small`, `invalid_measurement`),
#: which is drawn as silence. The rest are the silences, each with its own remedy: this run's
#: writer saved no tile digits for the series; the saved code is a word the stage does not
#: say; the stage named no tile (its own code says why: its stack or its lens was absent); the
#: walked slice lies outside the slices the digits hold.
DIGIT_STANDINGS: tuple[str, ...] = (
    "named",
    "digits_not_saved",
    "digits_code_unknown",
    "digits_absent",
    "slice_outside_digits",
)


def walk_standing(code: object, index: object, slices: int) -> str:
    """Name what one walked slice of the picture can show, from the digits' saved code and size.

    `code` is the digits' saved code (`TILE_DIGIT_CODES`), or None when the writer saved no
    digits; `index` the walked slice's stack index; `slices` how many slices the saved codes
    hold. Total: no saved digits is `digits_not_saved`; a code the stage does not say, or one
    that is not text, is `digits_code_unknown`, named and never drawn; digits whose stack or
    lens was absent are `digits_absent`; an index that is not a whole number inside the digits
    is `slice_outside_digits`; else the slice is `named`. It selects nothing and counts nothing.

    post: __return__ in DIGIT_STANDINGS
    """
    if code is None:
        return "digits_not_saved"
    if not isinstance(code, str) or code not in TILE_DIGIT_CODES:
        return "digits_code_unknown"
    if code == "predecessor_absent":
        return "digits_absent"
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < slices:
        return "slice_outside_digits"
    return "named"


@dataclass(frozen=True, slots=True)
class WalkedDigits:
    """One walked slice of the picture: the acquired plane at that slice, and the digits there.

    index: the stack index the walk visits. standing: from `DIGIT_STANDINGS`. plane: (rows,
    columns) in the dtype it was saved in, the study stage's retained walk at this step, or
    None when the writer saved no walk. codes: (tiles_down, tiles_across) uint8 indexing the
    stage's `DIGIT_CODES`, and digits: (tiles_down, tiles_across) int8 (-1, 0, +1, 2 for
    silence), the digits at this slice when `standing` is `named`, else None. Nothing is
    derived.
    """

    index: int
    standing: str
    plane: np.ndarray | None
    codes: np.ndarray | None
    digits: np.ndarray | None


@dataclass(frozen=True, slots=True)
class TileDigitPanels:
    """One series' saved tile digits, AS THE WRITER SAVED THEM, ready for the workbench to draw.

    code, why: the digits' standing as saved, or None when the record carries no digits at all.
    low_edge, high_edge: the terciles the tiles were read against, in the series' own stored
    units; None where the writer saved none (the oracle read no pair). population_count: how
    many tiles were counted; minimum_population: the bar they were read under; None when none
    was saved. counts: the number of tiles under each digit code over every slice, in the
    stage's `DIGIT_CODES` order, as saved; None when none was saved. slices: how many slices
    the saved codes hold (0 when none). codes: (Z, tiles_down, tiles_across) uint8 and digits:
    (Z, tiles_down, tiles_across) int8 over every slice; None when none was saved. bounds_rc:
    (tiles_down, tiles_across, 4) int64, the squint stack's saved half-open native bounds that
    place the tiles; None when none was handed on. walked: one `WalkedDigits` per step of the
    study stage's walk, in walk order. An absent value stays absent, never a zero.
    """

    code: str | None
    why: str | None
    low_edge: float | None
    high_edge: float | None
    population_count: int | None
    minimum_population: int | None
    counts: tuple[int, ...] | None
    slices: int
    codes: np.ndarray | None
    digits: np.ndarray | None
    bounds_rc: np.ndarray | None
    walked: tuple[WalkedDigits, ...]


def digit_panels(
    code: str | None,
    why: str | None,
    low_edge: float | None,
    high_edge: float | None,
    population_count: int | None,
    minimum_population: int | None,
    counts: tuple[int, ...] | None,
    codes: np.ndarray | None,
    digits: np.ndarray | None,
    bounds_rc: np.ndarray | None,
    walk_indices: tuple[int, ...],
    walk: np.ndarray | None,
) -> TileDigitPanels:
    """Hand on one series' saved tile digits beside the study stage's saved walk, reading neither.

    Every argument is a value a stage computed and the writer saved: the digits' code, edges,
    population count, bar and counts, their `codes` and `digits` over every slice, the squint
    stack's saved `bounds_rc`, and the study stage's `walk_indices` with the `walk` of planes
    at them. For each walked step this selects the codes and digits at that index where
    `walk_standing` says the slice is named, and names the silence otherwise. The codes are
    handed on as uint8, the digits as int8 and the bounds as int64; the planes keep their saved
    dtype. Nothing is measured, resampled or derived, and an absent value stays absent.
    """
    named = None if codes is None else np.asarray(codes, dtype=np.uint8)
    values = None if digits is None else np.asarray(digits, dtype=np.int8)
    slices = 0 if named is None else int(named.shape[0])
    walked = []
    for step, index in enumerate(walk_indices):
        standing = walk_standing(code, int(index), slices)
        plane = None if walk is None or step >= len(walk) else np.asarray(walk[step])
        selected = standing == "named" and named is not None and values is not None
        walked.append(
            WalkedDigits(
                index=int(index),
                standing=standing,
                plane=plane,
                codes=named[int(index)] if selected and named is not None else None,
                digits=values[int(index)] if selected and values is not None else None,
            )
        )
    return TileDigitPanels(
        code=code,
        why=why,
        low_edge=None if low_edge is None else float(low_edge),
        high_edge=None if high_edge is None else float(high_edge),
        population_count=None if population_count is None else int(population_count),
        minimum_population=None
        if minimum_population is None
        else int(minimum_population),
        counts=None if counts is None else tuple(int(count) for count in counts),
        slices=slices,
        codes=named,
        digits=values,
        bounds_rc=None if bounds_rc is None else np.asarray(bounds_rc, dtype=np.int64),
        walked=tuple(walked),
    )
