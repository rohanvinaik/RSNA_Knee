"""What the selection resolved, drawn: each chosen slice's territories tinted by role, over the acquired plane.

The funnel's operation 5b (`openspec/changes/the-funnel/design.md` R5b, task 5b.5):
`knee.objects.selection.read_selection` names every territory of a chosen slice's tile dome by the
view's own rule (`superior_big`, `inferior_big`, `anterior_small`, `lateral_small_ringed`,
`central_big`, or `unselected`) and carries the laterality sign its Coronal witness gives. Its
picture is the one the founder checks by eye (task 5b.6, E3): per chosen slice, the territories
tinted by role code over the acquired plane, each with its index, its role word and its facts
beside it, and the sign in the title. A slice the selection could not read, or read no territory
on, is a named silence in words, never an empty picture.

The territory map is the DOME's labels, not a field of the selection, so the writer saves a copy
beside the selection's record; the dome's peaks are saved the same way, because territory `k` is
the territory of peak `k - 1` (`knee.objects.dome.dome`), which is where an index is written on the
plane. Both are values a stage computed.

Every value here is one the stage computed and the writer saved. Selecting a chosen slice's labels
and plane from the saved stacks is ARRANGING: it chooses which stored values to show and alters
none of them (as `knee.pictures.first_lens.lens_panels` does with the lens's codes). Nothing here
thresholds, labels, dilates, computes a centroid or recomputes a code or a fact; a selection that
was not saved, one the stage did not make, or a slice that held no territory is a named silence.
The one decision, `slice_standing`, is pure and total and names what one chosen slice of the
picture can be.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from knee.objects.selection import SELECTION_CODES

#: What one chosen slice of the picture can be. `named` is a reading drawn: the selection made
#: territories and named each. The rest are the silences, each with its own remedy: this run's
#: writer saved no selection for the series; the saved code is a word the stage does not say; the
#: stage read no dome to select from (its own code says why); the stage read a dome that held no
#: territory.
SELECTION_STANDINGS: tuple[str, ...] = (
    "named",
    "selection_not_saved",
    "selection_code_unknown",
    "selection_absent",
    "no_territory",
)


def slice_standing(code: object) -> str:
    """Name what one chosen slice of the picture can show, from the selection's saved code.

    `code` is the selection's saved code (`SELECTION_CODES`), or None when the writer saved
    none. Total: no saved selection is `selection_not_saved`; a code the stage does not say, or
    one that is not text, is `selection_code_unknown`, named and never drawn; a selection made
    without a dome is `selection_absent`; one that found a dome with no territory is
    `no_territory`; else the slice is `named`. It selects nothing and counts nothing.

    post: __return__ in SELECTION_STANDINGS
    """
    if code is None:
        return "selection_not_saved"
    if not isinstance(code, str) or code not in SELECTION_CODES:
        return "selection_code_unknown"
    if code == "predecessor_absent":
        return "selection_absent"
    if code == "no_territory":
        return "no_territory"
    return "named"


@dataclass(frozen=True, slots=True)
class SavedObject:
    """One territory with its role and its facts, as the writer saved them.

    index: the territory's label in the dome (>= 1). role_code: the stage's role word. tiles: its
    tile count. centre_lps: (x, y, z) in millimetres, the scanner's LPS frame. superior_mm,
    anterior_mm, left_right_mm: that centre's +z, -y and +x. superior_extent_mm: (lowest, highest)
    tile-centre z. anterior_face_mm: the most anterior tile-centre -y. touches_leg_border,
    ringed: the stage's two bools. A fact the stage could not read is None, never a zero.
    """

    index: int
    role_code: str
    tiles: int
    centre_lps: tuple[float | None, float | None, float | None]
    superior_mm: float | None
    anterior_mm: float | None
    left_right_mm: float | None
    superior_extent_mm: tuple[float | None, float | None]
    anterior_face_mm: float | None
    touches_leg_border: bool
    ringed: bool


@dataclass(frozen=True, slots=True)
class SavedSlice:
    """What the writer saved of one chosen slice's selection, apart from its arrays.

    slice_index: the stack index (-1 where the selection was made without a dome). code, why,
    pair_code, lateral_sign: the stage's words, None where the writer saved none. candidate_codes:
    the candidate decision's word per territory ("" for a territory it was not put to), empty on a
    view with no such decision. peaks_rc: the dome's peaks as (tile row, tile column), peak `k`
    the seed of territory `k + 1`. objects: one `SavedObject` per territory, in label order.
    """

    slice_index: int
    code: str | None
    why: str | None
    pair_code: str | None
    lateral_sign: str | None
    candidate_codes: tuple[str, ...]
    peaks_rc: tuple[tuple[int, int], ...]
    objects: tuple[SavedObject, ...]
    #: The dome's border word (`knee.objects.tile_dome.BORDER_CODES`) this selection was read
    #: under. A slice is named by this AND `slice_index`: the two borders' readings of one slice
    #: are two entries, both kept.
    border: str


@dataclass(frozen=True, slots=True)
class ChosenSelection:
    """One chosen slice of the picture: the saved selection, its standing, and the arrays it is drawn on.

    index: the stack index. standing: from `SELECTION_STANDINGS`. code, why, pair_code,
    lateral_sign, candidate_codes, peaks_rc, objects: as `SavedSlice`. labels: (tiles_down,
    tiles_across) int32, the dome's labels at this slice when `standing` is `named` or
    `no_territory`, else None. plane: (rows, columns) in the dtype it was saved in, the acquired
    plane at this slice, or None when the writer saved none. Nothing is derived.
    """

    index: int
    standing: str
    code: str | None
    why: str | None
    pair_code: str | None
    lateral_sign: str | None
    candidate_codes: tuple[str, ...]
    peaks_rc: tuple[tuple[int, int], ...]
    objects: tuple[SavedObject, ...]
    labels: np.ndarray | None
    plane: np.ndarray | None
    #: The border word of the saved slice, handed on as saved (see `SavedSlice.border`).
    border: str


@dataclass(frozen=True, slots=True)
class SelectionPanels:
    """One series' saved selection, AS THE WRITER SAVED IT, ready for the workbench to draw.

    plane_kind: the told plane word the rule was chosen by, None when the record carries no
    selection at all. bounds_rc: (tiles_down, tiles_across, 4) int64, the squint stack's saved
    half-open native bounds that place the tiles; None when none was handed on. chosen: one
    `ChosenSelection` per saved slice, in the order saved. An absent value stays absent, never a
    zero.
    """

    plane_kind: str | None
    bounds_rc: np.ndarray | None
    chosen: tuple[ChosenSelection, ...]


def selection_panels(
    plane_kind: str | None,
    slices: tuple[SavedSlice, ...],
    labels: np.ndarray | None,
    planes: np.ndarray | None,
    bounds_rc: np.ndarray | None,
) -> SelectionPanels:
    """Hand on one series' saved selection beside its saved labels and planes, reading none of them.

    Every argument is a value a stage computed and the writer saved: the view's plane word, the
    per-slice records, the dome's `labels` (Z, tiles_down, tiles_across) with one grid per saved
    slice, the acquired `planes` (Z, rows, columns) with one plane per saved slice, and the
    squint stack's saved `bounds_rc`. For each saved slice this selects the labels at its position
    where `slice_standing` says there is a territory map to show (`named`, `no_territory`), and
    its plane where one was saved, and names the silence otherwise. The labels are handed on as
    int32 and the bounds as int64; the planes keep their saved dtype. Nothing is measured,
    resampled or derived, and an absent value stays absent.
    """
    grids = None if labels is None else np.asarray(labels, dtype=np.int32)
    chosen = []
    for position, saved in enumerate(slices):
        standing = slice_standing(saved.code)
        has_grid = (
            grids is not None
            and position < len(grids)
            and standing in ("named", "no_territory")
        )
        chosen.append(
            ChosenSelection(
                index=saved.slice_index,
                standing=standing,
                code=saved.code,
                why=saved.why,
                pair_code=saved.pair_code,
                lateral_sign=saved.lateral_sign,
                candidate_codes=saved.candidate_codes,
                peaks_rc=saved.peaks_rc,
                objects=saved.objects,
                labels=grids[position] if has_grid and grids is not None else None,
                plane=np.asarray(planes[position])
                if planes is not None and position < len(planes)
                else None,
                border=saved.border,
            )
        )
    return SelectionPanels(
        plane_kind=plane_kind,
        bounds_rc=None if bounds_rc is None else np.asarray(bounds_rc, dtype=np.int64),
        chosen=tuple(chosen),
    )
