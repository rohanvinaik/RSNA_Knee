"""What the tile dome resolved, drawn: each chosen slice's territories on the squint medians, and its height.

The funnel's operation 5 (`openspec/changes/the-funnel/design.md` R5, task 5.3):
`knee.objects.tile_dome.read_tile_domes` reads, at each slice the depth collapse chose, the dome
of the tiles the first lens kept: the obstacles (the cleared air, and the places dark on both
acquisitions or at or below the split), the height rising from them in millimetres, the peaks by
prominence and the territory each peak holds. Its picture is the one the founder checks by eye
(task 5b.6, E3, where the territories become objects by their facts): per chosen slice, the
territories laid over the squint's tile medians over the acquired plane, each tile placed in
native pixels by the squint stack's saved bounds, the peaks marked and numbered by the territory
they hold, the obstacles tinted; and the height beside it.

Every value here is one the stage computed and the writer saved. Selecting a dome's tiles from
the saved stacks, and the slice's medians and acquired plane from the saved stack and planes, is
ARRANGING: it chooses which stored values to show and alters none of them (as
`knee.pictures.first_lens.lens_panels` does with the lens). Nothing here thresholds, labels,
dilates or recomputes a code, a height or a territory. A dome that was not saved, one the stage
did not make, a slice the stack does not hold, and a plane that was not saved at the dome's own
slice are each a named silence in words, never an empty picture. The one decision,
`dome_standing`, is pure and total and names what one saved dome of the picture can be.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from knee.objects.tile_dome import DOME_CODES

#: What one saved dome of the picture can be. `named` is a reading drawn: the dome holds a code the
#: stage says and its slice lies inside the stack that places it, whether the slice holds an
#: interior (`present`) or none (`no_interior`, every tile an obstacle or empty). The rest are
#: the silences, each with its own remedy: this run's writer saved no tile dome for the series;
#: the saved code is a word the stage does not say; the stage made no dome and says why (a
#: predecessor was absent); the dome's slice lies outside the slices the stack holds.
DOME_STANDINGS: tuple[str, ...] = (
    "named",
    "dome_not_saved",
    "dome_code_unknown",
    "dome_absent",
    "slice_outside_stack",
)


def dome_standing(code: object, index: object, slices: int) -> str:
    """Name what one saved dome of the picture can show, from its saved code, slice and the stack's size.

    `code` is the dome's saved code (`DOME_CODES`), or None when the writer saved no dome;
    `index` the stack index of the slice the dome was read at; `slices` how many slices the stack
    that places it holds. Total: no saved dome is `dome_not_saved`; a code the stage does not
    say, or one that is not text, is `dome_code_unknown`, named and never drawn; a dome the stage
    did not make is `dome_absent`; an index that is not a whole number inside the stack is
    `slice_outside_stack`; else the dome is `named`. It selects nothing and counts nothing.

    post: __return__ in DOME_STANDINGS
    """
    if code is None:
        return "dome_not_saved"
    if not isinstance(code, str) or code not in DOME_CODES:
        return "dome_code_unknown"
    if code == "predecessor_absent":
        return "dome_absent"
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < slices:
        return "slice_outside_stack"
    return "named"


@dataclass(frozen=True, slots=True)
class DomePanel:
    """One saved dome of the picture, with the stack's medians and the acquired plane at its slice.

    index: the stack index the dome was read at, as saved. code, why: the dome's own word and
    reason, as saved. standing: from `DOME_STANDINGS`. plane: (rows, columns) in the dtype it was
    saved in, the acquired plane at EXACTLY this stack index, or None where the writer saved none
    there (a named silence: the picture then draws the medians alone). median: (tiles_down,
    tiles_across) float64, the stack's tile medians at this slice. obstacle, cleared, interior:
    (tiles_down, tiles_across) bool as saved. height: float64 (tiles_down, tiles_across)
    millimetres as saved. labels: int32 (tiles_down, tiles_across), 1..P the territory of each
    peak, 0 where none. peaks: int64 (P, 2) tile rc, tallest first; peak_height_mm: float64 (P,).
    Every array but plane and median is None unless `standing` is `named`; nothing is derived.
    border: the word the dome was read under, as saved and never coerced; a dome is identified
    by (border, index), and the picture's reader refuses a word the stage does not say.
    """

    index: object
    code: str | None
    why: str | None
    standing: str
    plane: np.ndarray | None
    median: np.ndarray | None
    obstacle: np.ndarray | None
    cleared: np.ndarray | None
    interior: np.ndarray | None
    height: np.ndarray | None
    labels: np.ndarray | None
    peaks: np.ndarray | None
    peak_height_mm: np.ndarray | None
    border: object


def _silent(
    index: object,
    border: object,
    code: str | None,
    why: str | None,
    standing: str,
) -> DomePanel:
    """A saved dome the picture cannot show: its words, its standing, and nothing drawn."""
    return DomePanel(
        index=index,
        code=code,
        why=why,
        standing=standing,
        plane=None,
        median=None,
        obstacle=None,
        cleared=None,
        interior=None,
        height=None,
        labels=None,
        peaks=None,
        peak_height_mm=None,
        border=border,
    )


@dataclass(frozen=True, slots=True)
class TileDomePanels:
    """One series' saved tile domes, AS THE WRITER SAVED THEM, ready for the workbench to draw.

    code, why: the record's series-level word and reason as saved, or None when the writer saved no
    tile dome at all. prominence_mm: the bar the peaks were read under, None where no dome was made
    to read it from. tile_mm: the bar the squint's grid was made with, None where no stack was
    saved. slices: how many slices the saved stack holds (0 when none). bounds_rc: (tiles_down,
    tiles_across, 4) int64, the half-open native bounds that place the tiles; None when none was
    handed on. domes: one `DomePanel` per saved dome, in saved order. An absent value stays
    absent, never a zero.
    """

    code: str | None
    why: str | None
    prominence_mm: float | None
    tile_mm: float | None
    slices: int
    bounds_rc: np.ndarray | None
    domes: tuple[DomePanel, ...]


def dome_panels(
    code: str | None,
    why: str | None,
    prominence_mm: float | None,
    tile_mm: float | None,
    median: np.ndarray | None,
    bounds_rc: np.ndarray | None,
    indices: Sequence[object],
    borders: Sequence[object],
    codes: Sequence[str | None],
    whys: Sequence[str | None],
    peak_counts: Sequence[int],
    obstacle: np.ndarray | None,
    cleared: np.ndarray | None,
    interior: np.ndarray | None,
    height: np.ndarray | None,
    labels: np.ndarray | None,
    peaks: np.ndarray | None,
    peak_height_mm: np.ndarray | None,
    planes: Mapping[int, np.ndarray],
) -> TileDomePanels:
    """Hand on one series' saved tile domes beside the stack's medians and saved planes, reading none.

    Every argument is a value a stage computed and the writer saved. `indices`, `borders`,
    `codes`, `whys` and `peak_counts` are the saved domes' slice, border, word, reason and number
    of peaks, one each per dome, in the order the writer saved them; `obstacle`, `cleared`,
    `interior`, `height` and `labels` hold one tile grid per dome along their first axis in that
    same order, and `peaks` and `peak_height_mm` every dome's peaks one after the other, split by
    `peak_counts`. A dome's grids are therefore selected by its position among the saved domes,
    never by its slice or its border, which only label it. `median` is the stack's tile medians
    over every slice, and `planes` the acquired planes the writer saved, by the stack index each
    lies at. For each dome this hands the saved index to `dome_standing` AS SAVED, never coerced,
    hands the saved border on as it was saved, and selects that dome's grids, its own peaks, the
    stack's medians at its slice and the plane saved at exactly that index where the standing
    says the dome is named; otherwise it names the silence. A plane is never borrowed from
    another slice. Nothing is measured, resampled or derived, and an absent value stays absent.
    """
    maps = None if median is None else np.asarray(median, dtype=np.float64)
    slices = 0 if maps is None else int(maps.shape[0])
    starts = np.concatenate(([0], np.cumsum(np.asarray(peak_counts, dtype=np.int64))))
    panels = []
    for k, index in enumerate(indices):
        standing = dome_standing(codes[k], index, slices)
        # `dome_standing` says `named` only for a whole number inside the stack; the checks here
        # restate that guarantee for the reader and the checker. They decide nothing.
        if standing != "named" or maps is None or not isinstance(index, int):
            panels.append(_silent(index, borders[k], codes[k], whys[k], standing))
            continue
        first, last = int(starts[k]), int(starts[k + 1])
        panels.append(
            DomePanel(
                index=index,
                code=codes[k],
                why=whys[k],
                standing=standing,
                plane=planes.get(index),
                median=maps[index],
                obstacle=None if obstacle is None else obstacle[k],
                cleared=None if cleared is None else cleared[k],
                interior=None if interior is None else interior[k],
                height=None if height is None else height[k],
                labels=None if labels is None else labels[k],
                peaks=None if peaks is None else peaks[first:last],
                peak_height_mm=None
                if peak_height_mm is None
                else peak_height_mm[first:last],
                border=borders[k],
            )
        )
    return TileDomePanels(
        code=code,
        why=why,
        prominence_mm=None if prominence_mm is None else float(prominence_mm),
        tile_mm=None if tile_mm is None else float(tile_mm),
        slices=slices,
        bounds_rc=None if bounds_rc is None else np.asarray(bounds_rc, dtype=np.int64),
        domes=tuple(panels),
    )
