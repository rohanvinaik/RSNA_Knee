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
    judged.
    """

    normal: np.ndarray
    orientation: np.ndarray
    position: np.ndarray
    spacing: np.ndarray
    along_normal: np.ndarray
    orientation_spread: float


#: How many slices the stage's walk through a stack keeps: the first, the last, and the rest evenly
#: between them. The walk is what this stage's picture shows (`knee.pictures.study`), retained here
#: so the writer can save it and the drawer can arrange it without the whole volume.
WALK_COUNT = 8

#: The per-slice codes this stage records. `stack_codes` counts the second across the series; the
#: per-slice record keeps WHICH slice, so the walk can label each one.
SLICE_CODES: tuple[str, ...] = ("decoded", "pixels_not_2d")


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
    volume; None when there is no volume.
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
    return Series(
        row=row,
        directory=directory,
        slices=tuple(slices),
        stack=codes,
        volume=volume,
        geometry=geometry,
        slice_codes=tuple(
            "decoded" if s.pixels.ndim == 2 else "pixels_not_2d" for s in slices
        ),
        walk_indices=indices,
        walk=volume[list(indices)] if volume is not None else None,
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
    geometry = SeriesGeometry(
        normal=normal,
        orientation=ordered,
        position=position[order],
        spacing=spacing[order],
        along_normal=distance[order],
        orientation_spread=float(np.abs(ordered - ordered[0]).max()),
    )
    return geometry, order
