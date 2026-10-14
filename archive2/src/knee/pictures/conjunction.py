"""What the conjunction resolved, drawn: every tile of the recipient's walked slices by its code, over the acquired planes.

The funnel's operation 3c (`openspec/changes/the-funnel/design.md` R3c, task 3c.2):
`knee.lenses.conjunction.read_conjunction` reads the two acquisitions of a paired plane together
at every tile of the fat-dark recipient, through the line-up's partner slices and tiles, as one
named code from `CONJUNCTION_CODES`: the ordered pair of digits `<partner>_<own>`, a silence on
either side named as such, or `unmatched` where no partner tile was named. Its picture is the
code as colour over the recipient's acquired plane at the slices the study stage's own walk
visits (`knee.study.series.walk_indices`, retained on the series as `Series.walk`), each tile
placed in native pixels by the squint stack's saved bounds, so a reader can see where each
ordered pair lies on the knee (task 3c.1's check: on the coronal pair, whether the `above_below`
tiles fill the two big bright regions and the `below_below` tiles trace the dark line between
them). The record rides on the recipient only; a partner and a solitary series carry none, and
that is the silence a sheet of theirs says in words.

Every value here is one the stage computed and the writer saved. Selecting the walked slices
from the saved codes is ARRANGING: it chooses which stored values to show and alters none of
them (as `knee.pictures.tiles.digit_panels` does with the digits). Nothing here reads a digit,
re-reads the line-up or recomputes a code; a conjunction that was not saved, that the stage did
not make, or a walked slice the conjunction does not hold, is a named silence in words, never an
empty picture. The one decision, `walk_standing`, is pure and total and names what one walked
slice of the picture can be.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from knee.lenses.conjunction import CONJUNCTION_RECORD_CODES

#: What one walked slice of the picture can be. `named` is a reading drawn: every tile at that
#: slice carries a conjunction code, whatever the two digit records and the line-up said. The
#: rest are the silences, each with its own remedy: this run's writer saved no conjunction for
#: the series (a partner, a solitary series, or a run that carried none); the saved code is a
#: word the stage does not say; the stage named no tile (its own code says why: the line-up or
#: a digit record was absent); the walked slice lies outside the slices the conjunction holds.
CONJUNCTION_STANDINGS: tuple[str, ...] = (
    "named",
    "conjunction_not_saved",
    "conjunction_code_unknown",
    "conjunction_absent",
    "slice_outside_conjunction",
)


def walk_standing(code: object, index: object, slices: int) -> str:
    """Name what one walked slice of the picture can show, from the conjunction's saved code and size.

    `code` is the conjunction's saved code (`CONJUNCTION_RECORD_CODES`), or None when the writer
    saved no conjunction; `index` the walked slice's stack index; `slices` how many slices the
    saved codes hold. Total: no saved conjunction is `conjunction_not_saved`; a code the stage
    does not say, or one that is not text, is `conjunction_code_unknown`, named and never drawn;
    a conjunction whose line-up or digits were absent is `conjunction_absent`; an index that is
    not a whole number inside the conjunction is `slice_outside_conjunction`; else the slice is
    `named`. It selects nothing and counts nothing.

    post: __return__ in CONJUNCTION_STANDINGS
    """
    if code is None:
        return "conjunction_not_saved"
    if not isinstance(code, str) or code not in CONJUNCTION_RECORD_CODES:
        return "conjunction_code_unknown"
    if code == "predecessor_absent":
        return "conjunction_absent"
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < slices:
        return "slice_outside_conjunction"
    return "named"


@dataclass(frozen=True, slots=True)
class WalkedConjunction:
    """One walked slice of the picture: the acquired plane at that slice, and the codes there.

    index: the stack index the walk visits. standing: from `CONJUNCTION_STANDINGS`. plane:
    (rows, columns) in the dtype it was saved in, the study stage's retained walk at this step,
    or None when the writer saved no walk. codes: (tiles_down, tiles_across) uint8 indexing the
    stage's `CONJUNCTION_CODES`, the codes at this slice when `standing` is `named`, else None.
    Nothing is derived.
    """

    index: int
    standing: str
    plane: np.ndarray | None
    codes: np.ndarray | None


@dataclass(frozen=True, slots=True)
class ConjunctionPanels:
    """One recipient's saved conjunction, AS THE WRITER SAVED IT, ready for the workbench to draw.

    code, why: the conjunction's standing as saved, or None when the record carries no
    conjunction at all. recipient_uid, partner_uid: the pair as saved; None when none was saved.
    counts: the number of tiles under each code over every slice, in the stage's
    `CONJUNCTION_CODES` order, as saved; None when none was saved. slices: how many slices the
    saved codes hold (0 when none). codes: (Z, tiles_down, tiles_across) uint8 over every slice;
    None when none was saved. bounds_rc: (tiles_down, tiles_across, 4) int64, the recipient's
    squint stack's saved half-open native bounds that place the tiles; None when none was handed
    on. walked: one `WalkedConjunction` per step of the study stage's walk, in walk order. An
    absent value stays absent, never a zero.
    """

    code: str | None
    why: str | None
    recipient_uid: str | None
    partner_uid: str | None
    counts: tuple[int, ...] | None
    slices: int
    codes: np.ndarray | None
    bounds_rc: np.ndarray | None
    walked: tuple[WalkedConjunction, ...]


def conjunction_panels(
    code: str | None,
    why: str | None,
    recipient_uid: str | None,
    partner_uid: str | None,
    counts: tuple[int, ...] | None,
    codes: np.ndarray | None,
    bounds_rc: np.ndarray | None,
    walk_indices: tuple[int, ...],
    walk: np.ndarray | None,
) -> ConjunctionPanels:
    """Hand on one recipient's saved conjunction beside the study stage's saved walk, reading neither.

    Every argument is a value a stage computed and the writer saved: the conjunction's code, the
    pair's identifiers and counts, its `codes` over every slice, the recipient's squint stack's
    saved `bounds_rc`, and the study stage's `walk_indices` with the `walk` of planes at them.
    For each walked step this selects the codes at that index where `walk_standing` says the
    slice is named, and names the silence otherwise. The codes are handed on as uint8 and the
    bounds as int64; the planes keep their saved dtype. Nothing is measured, resampled or
    derived, and an absent value stays absent.
    """
    named = None if codes is None else np.asarray(codes, dtype=np.uint8)
    slices = 0 if named is None else int(named.shape[0])
    walked = []
    for step, index in enumerate(walk_indices):
        standing = walk_standing(code, int(index), slices)
        plane = None if walk is None or step >= len(walk) else np.asarray(walk[step])
        walked.append(
            WalkedConjunction(
                index=int(index),
                standing=standing,
                plane=plane,
                codes=named[int(index)]
                if standing == "named" and named is not None
                else None,
            )
        )
    return ConjunctionPanels(
        code=code,
        why=why,
        recipient_uid=recipient_uid,
        partner_uid=partner_uid,
        counts=None if counts is None else tuple(int(count) for count in counts),
        slices=slices,
        codes=named,
        bounds_rc=None if bounds_rc is None else np.asarray(bounds_rc, dtype=np.int64),
        walked=tuple(walked),
    )
