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
