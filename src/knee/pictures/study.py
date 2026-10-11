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
    it chooses which stored values to show and alters none of them.
    """
    values = np.asarray(volume, dtype=np.float64)
    if values.ndim != 3:
        raise ValueError("invalid_study_volume")
    if len(codes) != values.shape[0]:
        raise ValueError("codes_do_not_match_slices")
    count = min(walk_count, values.shape[0])
    chosen = np.linspace(0, values.shape[0] - 1, count).round().astype(int)
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
