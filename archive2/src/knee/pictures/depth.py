"""What the depth collapse resolved, drawn: the four readings over Z, where each lens stands, and the chosen slices.

The funnel's operation 4 (`openspec/changes/the-funnel/design.md` R4, tasks 4.3 and 4.5):
`knee.collapse.depth.read_depth` reads four cheap readings per slice of a series' squint stack
and stands each lens at the slice where its reading peaks; the distinct chosen slices are the
series' flat pictures. Its picture is the four readings as curves over the stack index with each
lens's chosen slice marked on its own curve, and the chosen slices themselves: the acquired plane
at each distinct chosen index where this run saved one (the study stage's saved walk, or the
run's selected slice), else the squint's own tile medians at that slice, which the stack saves
for every slice. So the founder can confirm the slices (task 4.6, E2) and a view sheet can say
whether its own slice is one of them.

Every value here is one the stage computed and the writer saved. Selecting the readings at a
chosen index, the plane at a saved slice and the medians at a chosen slice is ARRANGING: it
chooses which stored values to show and alters none of them. Nothing here reads a tile,
re-reads a share or re-chooses a slice; a collapse that was not saved, that the stage did not
make, or a slice the collapse does not hold, is a named silence in words, never an empty
picture. The two decisions, `sheet_standing` and `plane_source`, are pure and total and name
what one slice of the picture can be and where its plane comes from.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from knee.collapse.depth import CHOICE_CODES, DEPTH_CODES, LENSES

#: What one slice of a view sheet is to the saved depth collapse. `chosen` and `unchosen` are
#: readings drawn: the slice is, or is not, one a lens stands at. The rest are the silences,
#: each with its own remedy: this run's writer saved no collapse for the series; the saved
#: code is a word the stage does not say; the stage stood no lens (its own code says why: the
#: stack or the first lens was absent); the sheet's slice lies outside the slices the collapse
#: read.
SHEET_STANDINGS: tuple[str, ...] = (
    "chosen",
    "unchosen",
    "depth_not_saved",
    "depth_code_unknown",
    "depth_absent",
    "slice_outside_depth",
)

#: Where the acquired plane at a chosen slice comes from in a saved run: the study stage's
#: saved walk, the run's selected slice (the objects stage's saved plane), or nowhere, in which
#: case the squint's saved tile medians at that slice stand in for it, said in words.
PLANE_SOURCES: tuple[str, ...] = ("walk", "selected", "plane_not_saved")


def sheet_standing(
    code: object, index: object, slices: int, chosen_slices: tuple[int, ...]
) -> str:
    """Name what one slice of a view sheet is to the saved collapse, from its code, size and choices.

    `code` is the collapse's saved code (`DEPTH_CODES`), or None when the writer saved no
    collapse; `index` the sheet's own stack index; `slices` how many slices the saved readings
    hold; `chosen_slices` the distinct indices the lenses stand at, as saved. Total: no saved
    collapse is `depth_not_saved`; a code the stage does not say, or one that is not text, is
    `depth_code_unknown`, named and never drawn; a collapse whose stack or lens was absent is
    `depth_absent`; an index that is not a whole number inside the readings is
    `slice_outside_depth`; else the slice is `chosen` when it is among the chosen slices and
    `unchosen` when it is not. It selects nothing and counts nothing.

    post: __return__ in SHEET_STANDINGS
    """
    if code is None:
        return "depth_not_saved"
    if not isinstance(code, str) or code not in DEPTH_CODES:
        return "depth_code_unknown"
    if code == "predecessor_absent":
        return "depth_absent"
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < slices:
        return "slice_outside_depth"
    chosen = any(
        not isinstance(held, bool) and isinstance(held, int) and held == index
        for held in chosen_slices
    )
    return "chosen" if chosen else "unchosen"


def plane_source(
    index: object, walk_indices: tuple[int, ...], selected_index: object
) -> str:
    """Name where a chosen slice's acquired plane comes from in a saved run (pure, total).

    `index` is the chosen stack index; `walk_indices` the study stage's saved walk indices;
    `selected_index` the run's selected slice, or None. The walk is named first, then the
    selected slice; an index that is a whole number in neither, or not a whole number at all,
    is `plane_not_saved`. It reads no plane.

    post: __return__ in PLANE_SOURCES
    """
    if isinstance(index, bool) or not isinstance(index, int):
        return "plane_not_saved"
    if any(
        not isinstance(walked, bool) and isinstance(walked, int) and walked == index
        for walked in walk_indices
    ):
        return "walk"
    if (
        not isinstance(selected_index, bool)
        and isinstance(selected_index, int)
        and selected_index == index
    ):
        return "selected"
    return "plane_not_saved"


@dataclass(frozen=True, slots=True)
class LensStanding:
    """Where one lens stands, as saved: its name, the slice (-1 for nowhere), its word, and its
    reading at that slice (NaN when it stands nowhere). Nothing is derived."""

    lens: str
    index: int
    code: str
    reading: float


@dataclass(frozen=True, slots=True)
class ChosenPlane:
    """One distinct chosen slice of the picture: which lenses stand there, and what the run
    saved of it.

    index: the stack index, as saved. lenses: the lenses standing at it, in `LENSES` order.
    source: from `PLANE_SOURCES`. plane: (rows, columns) in the dtype it was saved in, the
    acquired plane at this slice from the walk or the selected slice, or None when the run saved
    none. median: (tiles_down, tiles_across) float64, the squint stack's saved tile medians at
    this slice, or None when the stack does not hold it. Nothing is derived.
    """

    index: int
    lenses: tuple[str, ...]
    source: str
    plane: np.ndarray | None
    median: np.ndarray | None


@dataclass(frozen=True, slots=True)
class DepthPanels:
    """One series' saved depth collapse, AS THE WRITER SAVED IT, ready for the workbench to draw.

    code, why: the collapse's standing as saved, or None when the record carries no collapse at
    all. minimum_valid: the bar the choices were made under, or None. slices: how many slices
    the saved readings hold (0 when none). readings: one (lens, (Z,) float64) per lens in
    `LENSES` order, NaN for silence, as saved; empty when none was saved. standings: one
    `LensStanding` per lens, in `LENSES` order; empty when none was saved. chosen_slices: the
    distinct chosen indices ascending, as saved. chosen: one `ChosenPlane` per chosen slice, in
    that order. bounds_rc: (tiles_down, tiles_across, 4) int64, the squint stack's saved
    half-open native bounds that place the medians; None when none was handed on. An absent
    value stays absent, never a zero.
    """

    code: str | None
    why: str | None
    minimum_valid: int | None
    slices: int
    readings: tuple[tuple[str, np.ndarray], ...]
    standings: tuple[LensStanding, ...]
    chosen_slices: tuple[int, ...]
    chosen: tuple[ChosenPlane, ...]
    bounds_rc: np.ndarray | None


def _reading_at(reading: np.ndarray | None, index: int) -> float:
    """The saved reading at one slice, or NaN where the lens stands nowhere or the slice is not held."""
    if reading is None or index < 0 or index >= reading.shape[0]:
        return float("nan")
    return float(reading[index])


def _plane_at(
    index: int,
    source: str,
    walk_indices: tuple[int, ...],
    walk: np.ndarray | None,
    acquired_plane: np.ndarray | None,
) -> np.ndarray | None:
    """The saved plane the source names, or None when the run did not save it after all."""
    if source == "walk" and walk is not None:
        for step, walked in enumerate(walk_indices):
            if walked == index and step < len(walk):
                return np.asarray(walk[step])
        return None
    if source == "selected" and acquired_plane is not None:
        return np.asarray(acquired_plane)
    return None


def depth_panels(
    code: str | None,
    why: str | None,
    minimum_valid: int | None,
    kept_share: np.ndarray | None,
    dark_share: np.ndarray | None,
    split_quality: np.ndarray | None,
    above_below_share: np.ndarray | None,
    chosen_index: tuple[int, ...] | None,
    choice_codes: tuple[str, ...] | None,
    chosen_slices: tuple[int, ...] | None,
    median: np.ndarray | None,
    bounds_rc: np.ndarray | None,
    walk_indices: tuple[int, ...],
    walk: np.ndarray | None,
    selected_index: object,
    acquired_plane: np.ndarray | None,
) -> DepthPanels:
    """Hand on one series' saved depth collapse beside the saved planes it can be shown on, reading nothing.

    Every argument is a value a stage computed and the writer saved: the collapse's code, reason
    and bar, its four readings over every slice, where each lens stands and the word it said,
    the distinct chosen slices, the squint stack's saved `median` and `bounds_rc`, the study
    stage's `walk_indices` with the `walk` of planes at them, the run's `selected_index` and the
    objects stage's `acquired_plane` at it. For each chosen slice this names the lenses standing
    there (by equality with the saved choices), where its plane comes from (`plane_source`) and
    hands that plane on, and selects the stack's medians at that index where the stack holds
    it. The readings are handed on as float64 and the bounds as int64; the planes keep their
    saved dtype. Nothing is measured, resampled or derived, and an absent value stays absent.
    """
    saved = (kept_share, dark_share, split_quality, above_below_share)
    readings = tuple(
        (lens, np.asarray(reading, dtype=np.float64))
        for lens, reading in zip(LENSES, saved, strict=True)
        if reading is not None
    )
    by_lens = dict(readings)
    slices = max((int(reading.shape[0]) for _, reading in readings), default=0)
    standings: list[LensStanding] = []
    if chosen_index is not None and choice_codes is not None:
        for lens, index, word in zip(LENSES, chosen_index, choice_codes, strict=True):
            standings.append(
                LensStanding(
                    lens=lens,
                    index=int(index),
                    code=str(word),
                    reading=_reading_at(by_lens.get(lens), int(index)),
                )
            )
    maps = None if median is None else np.asarray(median, dtype=np.float64)
    held = () if chosen_slices is None else tuple(int(index) for index in chosen_slices)
    chosen: list[ChosenPlane] = []
    for index in held:
        source = plane_source(index, walk_indices, selected_index)
        chosen.append(
            ChosenPlane(
                index=index,
                lenses=tuple(
                    standing.lens for standing in standings if standing.index == index
                ),
                source=source,
                plane=_plane_at(index, source, walk_indices, walk, acquired_plane),
                median=maps[index]
                if maps is not None and 0 <= index < maps.shape[0]
                else None,
            )
        )
    return DepthPanels(
        code=code,
        why=why,
        minimum_valid=None if minimum_valid is None else int(minimum_valid),
        slices=slices,
        readings=readings,
        standings=tuple(standings),
        chosen_slices=held,
        chosen=tuple(chosen),
        bounds_rc=None if bounds_rc is None else np.asarray(bounds_rc, dtype=np.int64),
    )


__all__ = [
    "CHOICE_CODES",
    "PLANE_SOURCES",
    "SHEET_STANDINGS",
    "ChosenPlane",
    "DepthPanels",
    "LensStanding",
    "depth_panels",
    "plane_source",
    "sheet_standing",
]
