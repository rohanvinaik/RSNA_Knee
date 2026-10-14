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

    normal: (3,) float64, unit, the slice normal the stack is ordered along: that of the first file in file-name
    order. orientation: (n, 6) float64, each slice's row then column direction cosines. position: (n, 3) float64,
    each slice's ImagePositionPatient. spacing: (n, 2) float64, each slice's PixelSpacing (between rows, between
    columns). along_normal: (n,) float64, ascending, each position projected on the normal. orientation_spread:
    the largest absolute difference between any slice's direction cosine and the first slice's, measured and not
    judged. origin_spread_mm: the largest in-plane displacement, in millimetres, of any slice's origin from the
    first slice's -- the part of `position[i] - position[0]` that does not lie along the normal -- measured and
    not judged (task 7.12). Together the two spreads are the precondition under which one slice's frame can
    stand for the stack's; the slab lookup projects against each slice's own origin and shares only the basis.
    NaN where the geometry was built without positions to measure it from.
    """

    normal: np.ndarray
    orientation: np.ndarray
    position: np.ndarray
    spacing: np.ndarray
    along_normal: np.ndarray
    orientation_spread: float
    origin_spread_mm: float = float("nan")


#: How many slices the stage's walk through a stack keeps: the first, the last, and the rest evenly
#: between them. The walk is what this stage's picture shows (`knee.pictures.study`), retained here
#: so the writer can save it and the drawer can arrange it without the whole volume.
WALK_COUNT = 8

#: The per-slice codes this stage records. `stack_codes` counts the second across the series; the
#: per-slice record keeps WHICH slice, so the walk can label each one.
SLICE_CODES: tuple[str, ...] = ("decoded", "pixels_not_2d")


def selected_slice(count: int, requested: int | None) -> int | None:
    """The one slice the route reads a plane from: the middle of the stack unless one is requested.

    `requested` is the caller's explicit index; None selects floor(count / 2) in the stack's
    order. None back when the stack is empty or the request lies outside it, so the caller names
    `slice_unavailable` rather than reading past the end. This is the ONE rule for which slice a
    study is read at (task 7.1); the objects stage and the field's structural reading share it.

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

    Read here, once, by the stage that owns the headers (task 7.2). The slab rule
    (`knee.lenses.slabs`) bounds a slab by THICKNESS and never by spacing, so this is the one
    number it needs from the acquisition, and the objects stage consumes it from the series.
    """
    reader = getattr(header, "get", None)
    if not callable(reader):
        return None
    try:
        value = float(reader("SliceThickness", float("nan")))
    except (TypeError, ValueError):
        return None
    return value if np.isfinite(value) and value > 0.0 else None


def walk_indices(slices: int, walk_count: int = WALK_COUNT) -> tuple[int, ...]:
    """The stack indices a walk through `slices` slices visits: evenly spaced, ends included.

    A stack with at most `walk_count` slices is walked whole. Empty when there is nothing to walk.
    This is the ONE rule for which slices a walk shows; the picture adapter reads it from here.

    post: len(__return__) == min(max(slices, 0), max(walk_count, 0))
    post: all(0 <= i < slices for i in __return__)
    """
    if slices <= 0 or walk_count <= 0:
        return ()
    count = min(walk_count, slices)
    return tuple(
        int(index) for index in np.linspace(0, slices - 1, count).round().astype(int)
    )


@dataclass(frozen=True, slots=True)
class Series:
    """One series, whole.

    row: its row of the series table, as given. directory: where its files are. slices: every .dcm file in the
    directory, in stack order when `geometry` exists, else in file-name order. stack: `codes.stack_codes`.
    volume: when stack is ("stackable",), the slices' pixels stacked in stack order, (n, rows, columns) in the
    stored dtype, axis 0 ascending along the normal; else None. geometry: when every slice's position, orientation
    and pixel spacing are present; else None.

    slice_codes: one of `SLICE_CODES` per slice, in the same order as `slices`. walk_indices and walk: the
    stack indices `walk_indices` visits and the volume's slices at them, (len(walk_indices), rows, columns) in
    the stored dtype -- the stage's own picture content, retained so it is never recomputed from a re-read
    volume; None when there is no volume. slice_thickness_mm: each slice's SliceThickness as stored, in
    the same order as `slices`, None where the tag is absent or not a positive finite number.
    """

    row: SeriesRow
    directory: Path
    slices: tuple[Slice, ...]
    stack: tuple[str, ...]
    volume: np.ndarray | None
    geometry: SeriesGeometry | None
    slice_codes: tuple[str, ...] = ()
    walk_indices: tuple[int, ...] = ()
    walk: np.ndarray | None = None
    slice_thickness_mm: tuple[float | None, ...] = ()


def read_series(directory: Path, row: SeriesRow) -> Series:
    if not directory.is_dir():
        codes = stack_codes(False, 0, 0, [], 0, 0, 0, 0)
        return Series(
            row=row,
            directory=directory,
            slices=(),
            stack=codes,
            volume=None,
            geometry=None,
        )
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
    indices = walk_indices(len(volume)) if volume is not None else ()
    # The per-slice code comes from the stage's own vocabulary (task 7.2), so the record and the
    # declaration cannot drift apart.
    decoded, not_2d = SLICE_CODES
    return Series(
        row=row,
        directory=directory,
        slices=tuple(slices),
        stack=codes,
        volume=volume,
        geometry=geometry,
        slice_codes=tuple(decoded if s.pixels.ndim == 2 else not_2d for s in slices),
        walk_indices=indices,
        walk=volume[list(indices)] if volume is not None else None,
        slice_thickness_mm=tuple(slice_thickness(s.header) for s in slices),
    )


def stack_geometry(
    orientation: np.ndarray, position: np.ndarray, spacing: np.ndarray
) -> tuple[SeriesGeometry, np.ndarray]:
    """The geometry in stack order, and the order (n,) that puts file-name order into stack order.

    orientation (n, 6), position (n, 3) and spacing (n, 2) are in file-name order. The order sorts the positions'
    projections on the first file's normal, ascending; ties keep file-name order.
    """
    normal = slice_normal(orientation[0])
    distance = along(position, normal)
    order = np.argsort(distance, kind="stable")
    ordered = orientation[order]
    # The in-plane part of each slice origin's displacement from the first slice's, in stack order
    # (task 7.12): what remains of `position[i] - position[0]` once its component along the normal is
    # removed. Measured for the record, never judged here.
    displacement = position[order] - position[order][0]
    in_plane = displacement - np.outer(displacement @ normal, normal)
    geometry = SeriesGeometry(
        normal=normal,
        orientation=ordered,
        position=position[order],
        spacing=spacing[order],
        along_normal=distance[order],
        orientation_spread=float(np.abs(ordered - ordered[0]).max()),
        origin_spread_mm=float(np.linalg.norm(in_plane, axis=1).max()),
    )
    return geometry, order
