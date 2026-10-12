"""What CHAPTER 1 read, drawn: a study as it arrived, at stored fidelity.

Three panels, which are the stage's own claims in order:

    1. the middle slice of a series, exactly as stored -- no window, no rescale beyond the display
       normalisation every panel shares
    2. the stack walked through Z, so the series is seen as a volume rather than a picture
    3. the places the reader could NOT read, which is the stage's real contribution: every zero has
       a named code, and a slice that was never decoded is not drawn as black

Every panel arranges values `knee.study` already holds. Nothing here decodes, windows, segments or
measures: see this package's docstring on why a renderer that computes is a bug and is evidence
against the stage, not against the drawing.

Units: panels are in the series' own stored values; `spacing_mm` and `thickness_mm` are carried as
stated numbers so a caller can label the picture in millimetres rather than in places. Arrays out are
float64, NaN where a place was not read -- a place not read is never drawn as zero.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from knee.study.series import walk_indices


@dataclass(frozen=True, slots=True)
class StudyPanels:
    """One series as Chapter 1 read it. A caller writes these; this only makes them.

    recorded: (rows, columns) float64, the middle slice as stored. walk: (n, rows, columns) float64,
    slices sampled through the stack in order, superior first where the header gave an order.
    unread: (n,) bool, True where that slice carried no decoded pixels. codes: one named code per
    slice, in the same order, so a gap in the walk is legible as a reason rather than a hole.
    spacing_mm, thickness_mm: the geometry the header stated, carried for labelling.
    """

    recorded: np.ndarray
    walk: np.ndarray
    unread: np.ndarray
    codes: tuple[str, ...]
    spacing_mm: tuple[float, float]
    thickness_mm: float


def panels(
    volume: np.ndarray,
    codes: tuple[str, ...],
    spacing_mm: tuple[float, float],
    thickness_mm: float,
    *,
    walk_count: int = 8,
) -> StudyPanels:
    """Arrange one series' read values into its three panels.

    `volume` is the stacked series as Chapter 1 returned it, `codes` one named code per slice in the
    same order. Selecting the middle slice and sampling `walk_count` slices evenly is ARRANGING --
    it chooses which stored values to show and alters none of them -- and WHICH slices the walk
    visits is the study stage's own rule, `knee.study.series.walk_indices`, read from there so the
    stage's retained walk and this picture can never disagree.
    """
    values = np.asarray(volume, dtype=np.float64)
    if values.ndim != 3:
        raise ValueError("invalid_study_volume")
    if len(codes) != values.shape[0]:
        raise ValueError("codes_do_not_match_slices")
    chosen = list(walk_indices(values.shape[0], walk_count))
    unread = np.asarray(
        [not np.any(np.isfinite(values[index])) for index in range(values.shape[0])],
        dtype=bool,
    )
    return StudyPanels(
        recorded=values[values.shape[0] // 2].copy(),
        walk=values[chosen].copy(),
        unread=unread,
        codes=tuple(codes),
        spacing_mm=(float(spacing_mm[0]), float(spacing_mm[1])),
        thickness_mm=float(thickness_mm),
    )


@dataclass(frozen=True, slots=True)
class RecordedPanels:
    """The one stored plane a saved record holds, with the geometry that record states.

    The saved-record form of this stage's picture (task 6.9 of `every-stage-renders`), beside
    `StudyPanels`, which needs the whole stacked volume and per-slice codes that no saved record
    carries yet. plane: (rows, columns) in the dtype it was saved in, exactly as stored (no window,
    no rescale, not converted), or None when the record saved no plane. spacing_mm: (between rows,
    between columns) in millimetres as the record states it, or None. thickness_mm: the slice
    thickness the header stated, or None. slice_index: the plane's index in the stack's order, or
    None. codes: the named codes the record carries that bear on this plane, in the order the
    caller gives them, each already labelled by the caller with the stage that produced it. A value
    the record does not carry is None or empty, never zero.
    """

    plane: np.ndarray | None
    spacing_mm: tuple[float, float] | None
    thickness_mm: float | None
    slice_index: int | None
    codes: tuple[str, ...]
    walk: np.ndarray | None = None
    walk_indices: tuple[int, ...] = ()
    slice_codes: tuple[str, ...] = ()


def recorded_panels(
    plane: np.ndarray | None,
    spacing_mm: tuple[float, float] | None,
    thickness_mm: float | None,
    slice_index: int | None,
    codes: tuple[str, ...],
    walk: np.ndarray | None = None,
    walk_indices: tuple[int, ...] = (),
    slice_codes: tuple[str, ...] = (),
) -> RecordedPanels:
    """Hand on one series' saved plane, its saved walk and the geometry the record states.

    Every argument is a value a stage computed and the writer saved. This function packages them,
    keeps the plane and the walk in their saved dtype, turns the saved pair and numbers into float
    and int, and leaves an absent value absent. It selects nothing, windows nothing and derives no
    geometry: `walk` is the study stage's own retained walk (`Series.walk`), `walk_indices` the
    stack indices it visits and `slice_codes` the stage's code for every slice of the stack.
    """
    return RecordedPanels(
        plane=None if plane is None else np.asarray(plane),
        spacing_mm=None
        if spacing_mm is None
        else (float(spacing_mm[0]), float(spacing_mm[1])),
        thickness_mm=None if thickness_mm is None else float(thickness_mm),
        slice_index=None if slice_index is None else int(slice_index),
        codes=tuple(str(code) for code in codes),
        walk=None if walk is None else np.asarray(walk),
        walk_indices=tuple(int(index) for index in walk_indices),
        slice_codes=tuple(str(code) for code in slice_codes),
    )
