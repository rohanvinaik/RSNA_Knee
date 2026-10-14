"""What the strip resolved, drawn: one object's edge points, bands and footprint over the acquired plane.

The funnel's operation 6 (`openspec/changes/the-funnel/design.md` R6, task 6.5; the taut outline
of task 6.4 is a later unit and is not here): `knee.objects.strip.read_strip` casts a profile
across each midpoint of an object's tile boundary at native resolution, reads each for its dark
band, and names the outcome with a word of `TRACE_CODES`. Its picture is the one the founder
checks by eye (task 6.6, E4: "the lines are where the bones end"), per object, over the plane at
the object's own chosen slice and at native resolution: every edge point coloured by its trace
code, the bracketed bands' midpoints as their own points, the strip's footprint tinted, and, where
a partner's bands were carried to the points, the exchange code of each point.

Every value here is one the stage computed and the writer saved. Selecting an object's saved
arrays is ARRANGING: it chooses which stored values to show and alters none of them. The one
placement the picture needs is the band midpoints: the stage keeps each bracketed band as a near
and a far offset in millimetres along the saved outward normal, and the plane's own spacing, saved
beside them, turns the midpoint offset into native pixels with the very sum `dark_bands` made
for its own `trace`, `point + midpoint * normal / spacing`. It is a coordinate placement, as
`knee.pictures.lineup` places the partner's tile centres through the recipient's frame, and it
reads no pixel and decides nothing. Nothing here measures, thresholds, searches or recomputes a
code; a strip that was not saved, one the stage did not make, an object with no boundary, and a
plane the writer did not save at the strip's slice, are each a named silence in words, never an
empty picture. The one decision, `strip_standing`, is pure and total and names what one saved
strip can show.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from knee.compute.contracts import handed_on
from knee.objects.strip import STRIP_CODES

#: What one saved strip of the picture can be. `named` is a reading drawn over its plane. The rest
#: each have their own remedy: this run's writer saved no strip for the series; the saved code is a
#: word the stage does not say; the stage made no strip (its own code says why: a plane, labels or
#: bounds were absent); the object has no tile boundary, so no cast was made; or the strip was made
#: and the writer saved no plane at its slice, so its points are drawn alone.
STRIP_STANDINGS: tuple[str, ...] = (
    "named",
    "strip_not_saved",
    "strip_code_unknown",
    "strip_absent",
    "strip_has_no_boundary",
    "plane_not_saved",
)


def strip_standing(code: object, plane_held: object) -> str:
    """Name what one saved strip can show, from its saved code and whether its plane was saved.

    `code` is the strip's saved code (`STRIP_CODES`), or None when the writer saved no strip;
    `plane_held` whether the writer saved the plane at the strip's slice. Total: no saved strip is
    `strip_not_saved`; a code the stage does not say, or one that is not text, is
    `strip_code_unknown`, named and never drawn; a strip made over absent predecessors is
    `strip_absent`; an object with no boundary segment is `strip_has_no_boundary`; a strip whose
    plane was not saved is `plane_not_saved`, its points drawn alone; else the strip is `named`.
    It selects nothing and counts nothing.

    post: __return__ in STRIP_STANDINGS
    """
    if code is None:
        return "strip_not_saved"
    if not isinstance(code, str) or code not in STRIP_CODES:
        return "strip_code_unknown"
    if code == "predecessor_absent":
        return "strip_absent"
    if code == "no_boundary":
        return "strip_has_no_boundary"
    if plane_held is not True:
        return "plane_not_saved"
    return "named"


@dataclass(frozen=True, slots=True)
class StripPanel:
    """One object's saved strip, AS THE WRITER SAVED IT, ready for the workbench to draw.

    series_uid, slice_index, object_index: whose strip it is, as saved (None where unsaved).
    standing: from `STRIP_STANDINGS`. code, why: the strip's own standing and reason as saved.
    strip_mm: the strip's half-width as saved. low_edge, high_edge, population_count: the
    terciles of the object's own pixels and their population as saved, None where the stage read
    none. spacing_rc: the plane's pixel spacing (rows, columns) in millimetres as saved, None where
    unsaved. plane: (R, C) in the dtype it was saved in, the acquired plane at the strip's slice,
    None where not saved. edge_points: float64 (N, 2) native (row, column). trace_codes: uint8
    (N,) in `TRACE_CODES` values. band_centres_rc: float64 (N, 2) native (row, column), each
    bracketed band's midpoint placed on the plane, NaN where the point's band is not bracketed;
    None where no spacing was saved. exchange_codes: uint8 (N,) in `EXCHANGE_CODES` values with 0
    for a point no partner band was carried to, or empty (0,) where no partner was handed over.
    strip_mask: bool (R, C), the pixels any cast read. Nothing is derived beyond the placement.
    border: the dome's border word the strip was read under, as saved (None where unsaved): the
    two borders' strips of one slice are two panels, and each panel's title names its border.
    """

    series_uid: str | None
    slice_index: int | None
    object_index: int | None
    standing: str
    code: str | None
    why: str | None
    strip_mm: float | None
    low_edge: float | None
    high_edge: float | None
    population_count: int | None
    spacing_rc: tuple[float, float] | None
    plane: np.ndarray | None
    edge_points: np.ndarray | None
    trace_codes: np.ndarray | None
    band_centres_rc: np.ndarray | None
    exchange_codes: np.ndarray | None
    strip_mask: np.ndarray | None
    border: str | None


def band_centres_rc(
    edge_points: np.ndarray,
    normals: np.ndarray,
    band_mm: np.ndarray,
    spacing_rc: tuple[float, float],
) -> np.ndarray:
    """Each bracketed band's midpoint in native (row, column), placed on the plane.

    The stage kept the band as its near and far offsets in millimetres along the outward normal.
    The midpoint offset is their mean, and `point + midpoint * normal / spacing` puts it in native
    pixels, exactly the sum `knee.objects.interiors.dark_bands` makes for its own `trace`. A band
    that is NaN (not bracketed) gives a NaN centre, never a point at the edge. Returns float64
    (N, 2), newly owned and frozen with `handed_on`; the saved arrays are never written. No pixel
    is read.
    """
    points = np.asarray(edge_points, dtype=np.float64)
    steps = np.asarray(normals, dtype=np.float64)
    bands = np.asarray(band_mm, dtype=np.float64)
    spacing = np.asarray(spacing_rc, dtype=np.float64)
    midpoint = (bands[:, 0] + bands[:, 1]) / 2
    return handed_on(points + midpoint[:, None] * steps / spacing)


def strip_panel(
    series_uid: str | None,
    slice_index: int | None,
    object_index: int | None,
    code: str | None,
    why: str | None,
    strip_mm: float | None,
    low_edge: float | None,
    high_edge: float | None,
    population_count: int | None,
    spacing_rc: tuple[float, float] | None,
    plane: np.ndarray | None,
    edge_points: np.ndarray | None,
    normals: np.ndarray | None,
    trace_codes: np.ndarray | None,
    band_mm: np.ndarray | None,
    exchange_codes: np.ndarray | None,
    strip_mask: np.ndarray | None,
    border: str | None,
) -> StripPanel:
    """Hand on one object's saved strip, reading nothing of the study.

    Every argument is a value a stage computed and the writer saved: the strip's identity, code
    and reason, its half-width and terciles, the plane's spacing and the plane at the strip's
    slice, and its arrays (`normals` and `band_mm` are read only to place the band midpoints, and
    are not carried). `strip_standing` names what the strip can show. The band midpoints are
    placed through `band_centres_rc` where the points, normals, bands and spacing were all
    handed on. The arrays are handed on in their saved dtypes; nothing is measured, resampled or
    derived, and an absent value stays absent. `border`, the last argument, is the dome's border
    word the strip was read under, handed on as saved; it names the panel and decides nothing.
    """
    points = None if edge_points is None else np.asarray(edge_points, dtype=np.float64)
    placed = None
    if (
        points is not None
        and normals is not None
        and band_mm is not None
        and spacing_rc is not None
    ):
        placed = band_centres_rc(points, normals, band_mm, spacing_rc)
    return StripPanel(
        series_uid=series_uid,
        slice_index=slice_index,
        object_index=object_index,
        standing=strip_standing(code, plane is not None),
        code=code,
        why=why,
        strip_mm=None if strip_mm is None else float(strip_mm),
        low_edge=None if low_edge is None else float(low_edge),
        high_edge=None if high_edge is None else float(high_edge),
        population_count=None if population_count is None else int(population_count),
        spacing_rc=None
        if spacing_rc is None
        else (float(spacing_rc[0]), float(spacing_rc[1])),
        plane=None if plane is None else np.asarray(plane),
        edge_points=points,
        trace_codes=None
        if trace_codes is None
        else np.asarray(trace_codes, dtype=np.uint8),
        band_centres_rc=placed,
        exchange_codes=None
        if exchange_codes is None
        else np.asarray(exchange_codes, dtype=np.uint8),
        strip_mask=None if strip_mask is None else np.asarray(strip_mask, dtype=bool),
        border=border,
    )
