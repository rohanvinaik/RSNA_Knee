"""What THE COLLAPSE resolved, drawn.

Four panels, left to right, which are the stage's own steps in order:

    1. the series as recorded, at stored fidelity
    2. the leg, closed -- air is what connects to the frame's border, and the enclosed holes are
       filled, so the leg is a contiguous closed body rather than an outline
    3. the squint -- tile medians at the declared scale, inside the leg; the knee stays legible
    4. the profile along the header's superior-inferior axis, where the two objects appear as two
       plateaus and the seam between them as the dip

Every panel arranges values the stage already holds. Nothing here measures, thresholds or
segments: see this package's docstring on why a renderer that computes is a bug.

Units: panels 1-3 are in the series' own stored values; panel 4's horizontal axis is in whatever
units the caller passes its profile in. Arrays out are float64, NaN where a place is outside the
body -- a place not read is never drawn as zero.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class CollapsePanels:
    """The four panels, as arrays. A caller writes them; this makes them.

    recorded: (rows, columns) float64, the slice as stored. leg: (rows, columns) bool, True inside
    the closed body. squint: (tiles_down, tiles_across) float64, tile medians inside the leg, NaN
    outside. profile: (steps,) float64, the median along the superior-inferior axis, superior
    first. axis: which image axis carried superior-inferior, and the sign that put superior first.
    """

    recorded: np.ndarray
    leg: np.ndarray
    squint: np.ndarray
    profile: np.ndarray
    axis: int
    sign: float


def panels(
    recorded: np.ndarray,
    leg: np.ndarray,
    squint: np.ndarray,
    profile: np.ndarray,
    axis: int,
    sign: float,
) -> CollapsePanels:
    """Arrange the collapse's values into its four panels.

    Every argument is a value the stage computed: `recorded` the slice Chapter 1 read, `leg` the
    closed body, `squint` the tile medians, `profile` the reading along the header's axis, and
    `axis`/`sign` the axis the header gave. This function only shapes them.
    """
    return CollapsePanels(
        recorded=np.asarray(recorded, dtype=np.float64),
        leg=np.asarray(leg, dtype=bool),
        squint=np.asarray(squint, dtype=np.float64),
        profile=np.asarray(profile, dtype=np.float64),
        axis=int(axis),
        sign=float(sign),
    )


def over(
    plane: np.ndarray, mask: np.ndarray, colour: tuple[float, float, float]
) -> np.ndarray:
    """`plane` as grey, with `mask`'s places in `colour`: an (rows, columns, 3) float64 array.

    The one drawing primitive this layer needs. Grey comes from the plane's own 99.5th percentile,
    so a series is shown on its own scale and two series are never silently put on one.
    """
    values = np.asarray(plane, dtype=np.float64)
    finite = values[np.isfinite(values)]
    top = float(np.quantile(finite, 0.995)) if finite.size else 1.0
    grey = np.clip(values / top, 0.0, 1.0) if top > 0 else np.zeros_like(values)
    rgb = np.dstack([np.nan_to_num(grey)] * 3)
    rgb[np.asarray(mask, dtype=bool)] = colour
    return rgb


@dataclass(frozen=True, slots=True)
class FieldPanels:
    """One series' field-stage values AS THE WRITER SAVED THEM, ready for the workbench to draw.

    The saved-record form of this stage's picture (task 6.9 of `every-stage-renders`). It holds the
    two things the field computes once per series, the regime key and the squint, and nothing a
    caller would have to measure. `CollapsePanels` above is a different form, built from a leg, a
    profile and an axis this stage does not compute; this class neither uses nor replaces it.

    code, why: the regime's standing as saved, or None when the record carries no regime at all.
    readings: the regime key's readings by name, in the order saved, each value exactly as saved. A
    value of None is a reading the field did not make; an empty tuple is a regime that could not be
    read; neither is ever a zero. median, minimum, maximum, coverage: (tiles_down, tiles_across)
    float64, the squint's maps in the series' own stored values, NaN in a tile with no finite pixel;
    coverage is in [0, 1]. bounds_rc: (tiles_down, tiles_across, 4) int64, each tile's native
    half-open bounds r0, r1, c0, c1. tile_shape_rc: native pixels per tile, (rows, columns). A
    caller whose record saved no squint passes None for all six squint values.
    """

    code: str | None
    why: str | None
    readings: tuple[tuple[str, object], ...]
    median: np.ndarray | None
    minimum: np.ndarray | None
    maximum: np.ndarray | None
    coverage: np.ndarray | None
    bounds_rc: np.ndarray | None
    tile_shape_rc: tuple[int, int] | None


def field_panels(
    readings: Mapping[str, object],
    median: np.ndarray | None,
    minimum: np.ndarray | None,
    maximum: np.ndarray | None,
    coverage: np.ndarray | None,
    bounds_rc: np.ndarray | None,
    tile_shape_rc: tuple[int, int] | None,
    code: str | None,
    why: str | None,
) -> FieldPanels:
    """Hand on one series' saved regime key and saved squint, reading none of them.

    Every argument is a value the field stage computed and the writer saved: `readings` the regime
    key by reading name (a JSON mapping whose values may be None), `median`, `minimum`, `maximum`,
    `coverage` and `bounds_rc` the squint's arrays, `tile_shape_rc` its tile size in native pixels,
    and `code`/`why` the regime's saved standing. The readings keep their saved order and values;
    the arrays are handed on as float64 (the maps) and int64 (the bounds); the tile shape becomes a
    pair of ints. Nothing is measured, thresholded or derived, and an absent value stays absent.
    """
    return FieldPanels(
        code=code,
        why=why,
        readings=tuple(readings.items()),
        median=None if median is None else np.asarray(median, dtype=np.float64),
        minimum=None if minimum is None else np.asarray(minimum, dtype=np.float64),
        maximum=None if maximum is None else np.asarray(maximum, dtype=np.float64),
        coverage=None if coverage is None else np.asarray(coverage, dtype=np.float64),
        bounds_rc=None if bounds_rc is None else np.asarray(bounds_rc, dtype=np.int64),
        tile_shape_rc=None
        if tile_shape_rc is None
        else (int(tile_shape_rc[0]), int(tile_shape_rc[1])),
    )
