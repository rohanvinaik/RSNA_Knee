"""The squint over the whole stack, in millimetres, with every tile's centre in the scanner's frame.

**Why it exists, against the thesis.** "A coarse view of the whole field is itself a squint ... It
narrows where the expensive work runs" (§5.1); "Reduced to the median light of each 16 × 16 square,
a crowded plate still shows where its cells mass and where its ground is dark" (§4.5); "A tile's
median is exactly that tile's median, with no error in it" (§1.3). The founder, 2026-10-12: "this,
and MANY of the other lenses, should have been computed off the lossy/squint view ... If the raw
image is 256x256, then a 16x16 grid costs literally (n)^(1/2), for EVERYTHING." And 2026-10-13, on
how two acquisitions with different pixel counts lie over each other: "the squint is how you make
it cheap, you just kinda...line it up." A tile is a patch of the knee in millimetres, so its centre
in the scanner's frame is what two acquisitions share.

**What it reuses.** `knee.collapse.physical.physical_squint(plane, spacing_rc, tile_mm)` makes one
slice's grid (each tile at least `tile_mm` wide, rounded up to whole pixels; empty tiles NaN) and
`knee.collapse.physical.PlaneFrame.from_dicom(position, orientation, spacing_rc).to_patient(rc)`
maps a native point to millimetres. This module runs the first over every slice and the second
over every tile centre. It adds one measurement, `tile_centres_lps`, which carries the contract.

This is the funnel's operation 1 (`openspec/changes/the-funnel/design.md` R1, task 1.1). It
measures and decides nothing; the stack's code names the one silence it can meet.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from knee.collapse.physical import PlaneFrame, Squint, physical_squint
from knee.compute.contracts import ComputeContract, contracted, handed_on
from knee.study.corpus import Series
from knee.telemetry import ledger

#: The codes a stack reports. `present` is a reading; the others name why none was made.
STACK_CODES: tuple[str, ...] = ("present", "no_stacked_volume", "geometry_unreadable")

CONTRACT = ComputeContract(
    kind="measurement",
    language="NumPy; no twin, the work is one affine map per tile",
    reads="one slice's PlaneFrame and the tile bounds (TR, TC, 4) int64 half-open native rc",
    writes="centres_lps float64 (TR, TC, 3), millimetres, the scanner's LPS frame",
    allocation="one (TR, TC, 3) float64 array per slice, owned by the stack",
    work="TR * TC affine maps per slice; the stack is Z of them",
    parallel_unit="slice",
    reference="tile_centres_lps",
    proof_gate="tests/knee/collapse/test_squint_stack.py: the corner tile's centre equals the "
    "slice origin offset by half a tile along both in-plane directions; a tile centre maps back "
    "to native within half a pixel",
)


@contracted
def tile_centres_lps(frame: PlaneFrame, bounds_rc: np.ndarray) -> np.ndarray:
    """The centre of every tile of one slice in the scanner's millimetres (measurement).

    A tile's centre in native rc is the midpoint of its half-open bounds: row (r0 + r1 - 1) / 2,
    column (c0 + c1 - 1) / 2, the centre of the pixels it holds. `frame.to_patient` maps those to
    LPS. Returns float64 (TR, TC, 3). A tile with no pixels (r1 == r0 or c1 == c0, which
    `physical_squint` never makes) is NaN.

    pre: bounds_rc.ndim == 3 and bounds_rc.shape[2] == 4
    post: __return__.shape == (bounds_rc.shape[0], bounds_rc.shape[1], 3)
    """
    bounds = np.asarray(bounds_rc)
    if bounds.ndim != 3 or bounds.shape[2] != 4:
        raise ValueError("invalid_bounds")
    tiles_down, tiles_across = int(bounds.shape[0]), int(bounds.shape[1])
    flat = bounds.reshape(-1, 4).astype(np.float64)
    r0, r1, c0, c1 = flat[:, 0], flat[:, 1], flat[:, 2], flat[:, 3]
    # A tile holds pixels only where its half-open bounds enclose at least one; the rest are NaN
    # and never handed to the frame, which refuses a non-finite point.
    held = (r1 > r0) & (c1 > c0)
    centres = np.full((flat.shape[0], 3), np.nan, dtype=np.float64)
    if held.any():
        native = np.column_stack(((r0 + r1 - 1.0) / 2.0, (c0 + c1 - 1.0) / 2.0))
        centres[held] = frame.to_patient(native[held])
    return handed_on(centres.reshape(tiles_down, tiles_across, 3))


@dataclass(frozen=True, slots=True)
class SquintStack:
    """One series' squint over every slice, in millimetres, with each tile's centre in LPS.

    Arrays are in stack order (Z), then tile rows and tile columns (TR, TC). `median`, `minimum`,
    `maximum`, `coverage`: float64 (Z, TR, TC), NaN where a tile holds no finite pixel; coverage is
    the share of a tile's pixels that are finite over its true size, in [0, 1]. `centres_lps`:
    float64 (Z, TR, TC, 3) millimetres. `bounds_rc`: int64 (TR, TC, 4), the half-open native
    bounds r0, r1, c0, c1 shared by every slice (one grid per series, since every slice of a
    stackable series has one shape). `tile_shape_rc`: the tile's size in native pixels.
    `tile_mm`: the bar the grid was made with. `code` is from `STACK_CODES`; when it is not
    `present` the arrays are empty with the right number of axes and `why` says which silence.
    """

    series_uid: str
    code: str
    why: str
    tile_mm: float
    tile_shape_rc: tuple[int, int]
    bounds_rc: np.ndarray
    median: np.ndarray
    minimum: np.ndarray
    maximum: np.ndarray
    coverage: np.ndarray
    centres_lps: np.ndarray


def read_squint_stack(
    series: Series,
    tile_mm: float,
    frame_at: Callable[[int], PlaneFrame | ValueError] | None = None,
    finite: np.ndarray | None = None,
) -> SquintStack:
    """Squint every slice of a series and place every tile's centre in millimetres (orchestration).

    When `series.volume` is None the code is `no_stacked_volume`; when `series.geometry` is None
    it is `geometry_unreadable`; both return empty arrays shaped (0, 0, 0) and (0, 0, 0, 3). Else,
    per slice z: `physical_squint(volume[z], (spacing[z][0], spacing[z][1]), tile_mm)` gives the
    grid, and `tile_centres_lps(PlaneFrame.from_dicom(position[z], orientation[z], spacing),
    bounds_rc)` the centres. Every slice's `bounds_rc` and `tile_shape_rc` are identical for a
    stackable series; the first slice's are kept. Output arrays are frozen with
    `knee.compute.contracts.handed_on`. Records `study.consumed_by.squint_stack` and
    `squint_stack.produced` (slices, tiles) on the ledger. Decides nothing itself.

    `frame_at` gives slice z's frame, or the error its header raised, when the caller makes each
    slice's frame once for every stage that asks; and `finite` is which of the volume's values are
    finite, when the caller has read it once for the series. Each is made here otherwise.
    """
    if not np.isfinite(tile_mm) or tile_mm <= 0:
        raise ValueError("invalid_tile_mm")
    # The consumer records what it read at the point of reading (`specs/route-composition`): the
    # study's series is always handed over, and the counts say what it carried.
    ledger.record(
        "study.consumed_by.squint_stack",
        volume=1 if series.volume is not None else 0,
        geometry=1 if series.geometry is not None else 0,
    )
    stack = _read_squint_stack(series, float(tile_mm), frame_at, finite)
    ledger.record(
        "squint_stack.produced",
        slices=int(stack.median.shape[0]),
        tiles=int(stack.median.size),
    )
    return stack


def _absent(series: Series, tile_mm: float, code: str, why: str) -> SquintStack:
    """The stack of a series no squint was made over: its named silence, and empty arrays with
    the right number of axes, every one frozen."""
    return SquintStack(
        series_uid=series.row.series_uid,
        code=code,
        why=why,
        tile_mm=tile_mm,
        tile_shape_rc=(0, 0),
        bounds_rc=handed_on(np.empty((0, 0, 4), dtype=np.int64)),
        median=handed_on(np.empty((0, 0, 0), dtype=np.float64)),
        minimum=handed_on(np.empty((0, 0, 0), dtype=np.float64)),
        maximum=handed_on(np.empty((0, 0, 0), dtype=np.float64)),
        coverage=handed_on(np.empty((0, 0, 0), dtype=np.float64)),
        centres_lps=handed_on(np.empty((0, 0, 0, 3), dtype=np.float64)),
    )


def _grid_mismatch(
    z: int, squint: Squint, first_bounds: np.ndarray, first_tile: tuple[int, int]
) -> str | None:
    """Why slice z's grid is not the first slice's, in words; None when the two are one grid.

    One grid per series means three things agree with the first slice's: the tile count (the
    bounds' shape), the tile's size in native pixels (`tile_shape_rc`) and every half-open bound.
    All three are compared, because a change of spacing can keep the tile count and still move
    every bound (0.5 mm against 0.45 mm under a 2 mm tile: 2 x 2 tiles of 4 px become 2 x 2 tiles
    of 5 px), and the study stage's stack codes (`knee.study.codes.stack_codes`) check shapes,
    dtypes and positions, never that the spacing is uniform. The words name the slice and which
    of the three disagreed; the code they go under is the one silence the stack has for a
    geometry it cannot read as one, `geometry_unreadable`.
    """
    if squint.bounds_rc.shape != first_bounds.shape:
        return (
            f"slice {z}: its tile grid {squint.bounds_rc.shape[:2]} is not the first "
            f"slice's {first_bounds.shape[:2]}, so the spacing varies through the stack"
        )
    if tuple(squint.tile_shape_rc) != tuple(first_tile):
        return (
            f"slice {z}: its tiles are {squint.tile_shape_rc[0]} x "
            f"{squint.tile_shape_rc[1]} px, not the first slice's {first_tile[0]} x "
            f"{first_tile[1]} px, so the spacing varies through the stack although the "
            f"tile count {first_bounds.shape[:2]} does not"
        )
    if not np.array_equal(squint.bounds_rc, first_bounds):
        return (
            f"slice {z}: its tile bounds are not the first slice's at the same tile count "
            f"{first_bounds.shape[:2]} and tile size, so its grid is not the stack's"
        )
    return None


def _read_squint_stack(
    series: Series,
    tile_mm: float,
    frame_at: Callable[[int], PlaneFrame | ValueError] | None = None,
    finite: np.ndarray | None = None,
) -> SquintStack:
    """The stack itself, the two silences first, then one squint and one set of centres per slice."""
    volume, geometry = series.volume, series.geometry
    if volume is None:
        return _absent(
            series,
            tile_mm,
            "no_stacked_volume",
            "the series has no stacked volume (its stack codes: "
            + ", ".join(series.stack)
            + "), so there is no slice to squint at",
        )
    if geometry is None:
        return _absent(
            series,
            tile_mm,
            "geometry_unreadable",
            "the series has no geometry, so no tile centre can be placed in millimetres",
        )
    medians: list[np.ndarray] = []
    minima: list[np.ndarray] = []
    maxima: list[np.ndarray] = []
    coverages: list[np.ndarray] = []
    centres: list[np.ndarray] = []
    first: tuple[np.ndarray, tuple[int, int]] | None = None
    for z in range(len(volume)):
        frame = (
            _frame_of(
                geometry.position[z], geometry.orientation[z], geometry.spacing[z]
            )
            if frame_at is None
            else frame_at(z)
        )
        if isinstance(frame, ValueError):
            return _absent(
                series,
                tile_mm,
                "geometry_unreadable",
                f"slice {z}: its header does not read as a plane frame ({frame})",
            )
        squint = physical_squint(
            volume[z], frame.spacing_rc, tile_mm, None if finite is None else finite[z]
        )
        if first is None:
            first = (squint.bounds_rc, squint.tile_shape_rc)
        else:
            # A stackable series has one pixel shape, so one grid; a slice whose spacing makes
            # another grid, or another tile size on the same grid, is a geometry the stack
            # cannot read as one. Named with the slice and the difference, never stacked: the
            # record keeps ONE bounds grid and ONE tile shape for every slice, so a slice whose
            # own differ would be misdescribed by them.
            mismatch = _grid_mismatch(z, squint, first[0], first[1])
            if mismatch is not None:
                return _absent(series, tile_mm, "geometry_unreadable", mismatch)
        medians.append(squint.median)
        minima.append(squint.minimum)
        maxima.append(squint.maximum)
        coverages.append(squint.coverage)
        centres.append(tile_centres_lps(frame, squint.bounds_rc))
    if first is None:
        return _absent(
            series, tile_mm, "no_stacked_volume", "the stacked volume holds no slice"
        )
    bounds_rc, tile_shape_rc = first
    tiles_down, tiles_across = bounds_rc.shape[0], bounds_rc.shape[1]
    return SquintStack(
        series_uid=series.row.series_uid,
        code="present",
        why=(
            f"{len(volume)} slices squinted at {tile_mm:g} mm: {tiles_down} x "
            f"{tiles_across} tiles of {tile_shape_rc[0]} x {tile_shape_rc[1]} px each"
        ),
        tile_mm=tile_mm,
        tile_shape_rc=(int(tile_shape_rc[0]), int(tile_shape_rc[1])),
        bounds_rc=bounds_rc,
        median=handed_on(np.stack(medians)),
        minimum=handed_on(np.stack(minima)),
        maximum=handed_on(np.stack(maxima)),
        coverage=handed_on(np.stack(coverages)),
        centres_lps=handed_on(np.stack(centres)),
    )


def _frame_of(position, orientation, spacing) -> PlaneFrame | ValueError:
    """One slice's frame from its header's geometry, or the error the header raised."""
    try:
        return PlaneFrame.from_dicom(position, orientation, spacing)
    except ValueError as error:
        return error
