"""One series, assembled from every file in its directory: nothing compressed, rescaled, resampled or dropped."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pydicom

from knee.study.codes import stack_codes, tag_reasons
from knee.study.geometry import (
    Reading,
    along,
    orientation_of,
    position_of,
    slice_normal,
    spacing_of,
)
from knee.study.slices import Slice, read_slice
from knee.study.tables import SeriesRow

GEOMETRY_TAGS: tuple[tuple[str, Callable[[pydicom.Dataset], Reading]], ...] = (
    ("position", position_of),
    ("orientation", orientation_of),
    ("spacing", spacing_of),
)


@dataclass(frozen=True, slots=True)
class SeriesGeometry:
    """Each slice's geometry, in stack order, exactly as its tags give it (DICOM LPS, millimetres).

    orientation: (n, 6) float64, each slice's row then column direction cosines. position: (n, 3) float64,
    each slice's ImagePositionPatient. spacing: (n, 2) float64, each slice's PixelSpacing (between rows,
    between columns). The stack is ordered along the first file's slice normal (`stack_geometry`).
    """

    orientation: np.ndarray
    position: np.ndarray
    spacing: np.ndarray


def selected_slice(count: int, requested: int | None) -> int | None:
    """The one slice a series' middle plane is read from: the middle of the stack unless one is requested.

    `requested` is the caller's explicit index; None selects floor(count / 2) in the stack's
    order. None back when the stack is empty or the request lies outside it, so the caller names
    `slice_unavailable` rather than reading past the end.

    post: __return__ is None or (0 <= __return__ < count)
    """
    if count <= 0:
        return None
    index = count // 2 if requested is None else requested
    if not isinstance(index, int) or isinstance(index, bool):
        return None
    return index if 0 <= index < count else None


def slice_thickness(header: object) -> float | None:
    """One slice's SliceThickness as stored, in millimetres: finite and positive, else None.

    Read here, once, by the stage that owns the headers. A slice holds the places within half its
    thickness of its plane, so this is the number the run reads to carry a part from one slice of
    the knee onto another (`knee.objects.assignments.places_on_slice`, `places_from`).
    """
    reader = getattr(header, "get", None)
    if not callable(reader):
        return None
    try:
        value = float(reader("SliceThickness", float("nan")))
    except (TypeError, ValueError):
        return None
    return value if np.isfinite(value) and value > 0.0 else None


@dataclass(frozen=True, slots=True)
class Series:
    """One series, whole.

    row: its row of the series table, as given. slices: every .dcm file in its directory, in stack order when
    `geometry` exists, else in file-name order. stack: `codes.stack_codes`. volume: when stack is
    ("stackable",), the slices' pixels stacked in stack order, (n, rows, columns) in the stored dtype, axis 0
    ascending along the normal; else None. geometry: when every slice's position, orientation and pixel spacing
    are present; else None. slice_thickness_mm: each slice's SliceThickness as stored, in the same order as
    `slices`, None where the tag is absent or not a positive finite number.
    """

    row: SeriesRow
    slices: tuple[Slice, ...]
    stack: tuple[str, ...]
    volume: np.ndarray | None
    geometry: SeriesGeometry | None
    slice_thickness_mm: tuple[float | None, ...] = ()


def read_series(directory: Path, row: SeriesRow) -> Series:
    if not directory.is_dir():
        codes = stack_codes(False, 0, 0, [], 0, 0, 0, 0)
        return Series(row=row, slices=(), stack=codes, volume=None, geometry=None)
    slices = [read_slice(path) for path in sorted(directory.glob("*.dcm"))]
    readings = {
        tag: [reader(s.header) for s in slices] for tag, reader in GEOMETRY_TAGS
    }
    reasons: list[str] = []
    for tag, _ in GEOMETRY_TAGS:
        kinds = Counter(status for status, _ in readings[tag])
        reasons += tag_reasons(
            tag,
            kinds["absent"],
            kinds["empty"],
            kinds["malformed"],
            kinds["degenerate"],
        )
    present = {
        tag: [values for _, values in readings[tag] if values is not None]
        for tag, _ in GEOMETRY_TAGS
    }
    codes = stack_codes(
        True,
        len(slices),
        sum(s.pixels.ndim != 2 for s in slices),
        reasons,
        len({s.pixels.shape for s in slices}),
        len({s.pixels.dtype.str for s in slices}),
        len(present["position"]),
        len({tuple(p.tolist()) for p in present["position"]}),
    )
    geometry = None
    if slices and all(len(values) == len(slices) for values in present.values()):
        geometry, order = stack_geometry(
            np.stack(present["orientation"]),
            np.stack(present["position"]),
            np.stack(present["spacing"]),
        )
        slices = [slices[i] for i in order]
    volume = np.stack([s.pixels for s in slices]) if codes == ("stackable",) else None
    return Series(
        row=row,
        slices=tuple(slices),
        stack=codes,
        volume=volume,
        geometry=geometry,
        slice_thickness_mm=tuple(slice_thickness(s.header) for s in slices),
    )


def stack_geometry(
    orientation: np.ndarray, position: np.ndarray, spacing: np.ndarray
) -> tuple[SeriesGeometry, np.ndarray]:
    """The geometry in stack order, and the order (n,) that puts file-name order into stack order.

    orientation (n, 6), position (n, 3) and spacing (n, 2) are in file-name order. The order sorts the positions'
    projections on the first file's normal, ascending; ties keep file-name order.
    """
    order = np.argsort(along(position, slice_normal(orientation[0])), kind="stable")
    geometry = SeriesGeometry(
        orientation=orientation[order],
        position=position[order],
        spacing=spacing[order],
    )
    return geometry, order
