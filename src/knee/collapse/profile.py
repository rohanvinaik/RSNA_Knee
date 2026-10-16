"""Cheap local readings through depth, and the physical support they keep: measurements only, no
anatomy and no names (`docs/DIMENSIONAL_COLLAPSE_PLAN.md` Steps 2 and 4).

**Why it exists.** The thesis's collapse reads cheap views of the whole field and runs the
expensive work only where they point: "a reading that is poor at finding a signal can be reliable
at saying where the signal is not" (§4.6), and the composite "never pulls a cell and never decides
alone: it points" (§4.3). The squint (`squint_stack`) is the first cheap view, at 10 mm: a tile's
median is exactly that tile's median, but a thin structure can hide inside it, so a finer local
reading is owed where the tiles cannot say. `block_medians` is that finer reading over a native
window: the median light of each block of pixels, NaN wherever any pixel of a block is not seen,
since an unseen place is unknown and never zero. `could_hold_level` is the exclusion one tile's own
extrema make exactly: a tile whose maximum is under a level, or whose minimum is over it, holds no
pixel at that level. It is NOT an exclusion of a finer block: a block median is a median over the
pixels of its footprint, and a footprint that crosses a tile boundary reads pixels of two tiles
(two constant tiles 0.3 and 0.7 both miss [0.4, 0.6], and a 2 x 2 block across their boundary has
median 0.5). So a finer block is excluded only by the extrema of every tile its footprint can
touch (`footprint_reach`, `could_hold_level_in_reach`): a block with a pixel in a tile lies within
one block's width less one pixel of that tile's bounds, and its median is between the least
minimum and the greatest maximum of the tiles it touches. The tile-level reading itself is
unchanged; only the tiles it is taken over are widened to the footprint.

**What it keeps.** A profile through depth is one reading per slice with its status; the runs of
slices that hold support (`positive_runs`), the slice or slices of each run that reach its maximum,
every tie kept (`run_maxima`), what each run's two ends touch (`run_neighbours`: the scan's edge, a
slice measured empty, a slice not read or not readable), and the run's extent in the scanner's
millimetres along the series' normal (`depth_offsets_mm`, `support_intervals_mm`): the planes'
own thickness at its two ends, with nothing interpolated between slices. That interval is an
ENVELOPE of the sampled slabs and never dense occupancy: the slabs themselves and the gaps between
them are kept (`run_slabs_mm`, `slab_gaps_mm`), so what was sampled and what lies between samples
stay distinct. The finer readings are kept at their own small resolution, one per read slice,
as ragged native windows (`FineReading`, `pack_fine_readings`): each slice's window, block size and
shape stated, nothing padded to the volume. It decides nothing: a plateau is not broken, and two
runs are two runs, not one object and not two.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import ceil

import numpy as np

from knee.collapse.physical import spacing_pair
from knee.compute.contracts import ComputeContract, contracted, handed_on

CONTRACT = ComputeContract(
    kind="measurement",
    language="NumPy; the blocks are one reshape and one median, no Python loop over blocks",
    reads="one native plane (R, C), the places it has no light for (R, C), its pixel pitch, a block "
    "size in millimetres and a native window",
    writes="float64 (BR, BC) block medians, NaN where any pixel of the block is unseen; the block "
    "size in pixels and millimetres and the window it was read over",
    allocation="one (BR, BC, block pixels) float64 gather over the window, never the plane",
    work="one median per fully seen block of the window; the window is the corridor, not the slice",
    parallel_unit="independent plane",
    reference="block_medians",
    proof_gate="tests/test_collapse_profile.py: a thin bright cord a tile median hides is read by "
    "the finer blocks; a block with any unseen pixel is NaN, never a dark median; the window moves "
    "no block off the pixels it names; empty, nonfinite and wrong-shaped input is refused by name",
)

# What a run's end touches that is not a slice read as empty: the scan's own edge.
CLIPPED_BY_THE_SCAN = -1


@dataclass(frozen=True, slots=True)
class BlockReading:
    """The finer reading of a native window: `median` (BR, BC) float64, NaN where any pixel of the
    block is unseen (a block cut by the window's far edge counts the pixels it has not as unseen);
    `block_px` the block's size in native pixels (rows, columns); `block_mm` its size in
    millimetres, which the pixel pitch rounds up to whole pixels; `window_rc` the native half-open
    window (r0, r1, c0, c1) the blocks tile from its first pixel."""

    median: np.ndarray
    block_px: tuple[int, int]
    block_mm: tuple[float, float]
    window_rc: tuple[int, int, int, int]


def block_pixels(spacing_rc: tuple[float, float], block_mm: float) -> tuple[int, int]:
    """A block's size in native pixels (rows, columns): `block_mm` rounded up to whole pixels on each
    axis, as the squint's tiles are. Raises ValueError for a pitch or block size that is not
    positive and finite (`invalid_spacing`, `invalid_block_mm`)."""
    pitch = spacing_pair(spacing_rc)
    if not np.isfinite(block_mm) or block_mm <= 0:
        raise ValueError("invalid_block_mm")
    return (max(1, ceil(block_mm / pitch[0])), max(1, ceil(block_mm / pitch[1])))


@contracted
def block_medians(
    plane: np.ndarray,
    unseen: np.ndarray,
    spacing_rc: tuple[float, float],
    block_mm: float,
    window: tuple[int, int, int, int] | None = None,
) -> BlockReading:
    """The median light of each block of `block_mm` (rounded up to whole pixels, as the squint's
    tiles are) over a native `window`, the whole plane when None (measurement).

    A block is read only when every pixel of it is seen: a pixel that is `unseen`, or not finite,
    makes its block NaN, never a median over the places that remain, which would read a missing
    place as no light. Blocks tile the window from its first pixel; the last ones are cut by the
    window's far edge, and a block cut so counts the missing pixels as unseen. Raises ValueError
    for a plane that is not 2-D numeric (`invalid_plane`), an `unseen` of another shape or kind
    (`invalid_unseen`), a pitch or block size that is not positive and finite (`invalid_spacing`,
    `invalid_block_mm`) and a window that is empty or outside the plane (`invalid_window`).

    pre: window is None or (0 <= window[0] < window[1] and 0 <= window[2] < window[3])
    post: __return__.median.ndim == 2
    """
    values = np.asarray(plane)
    if values.ndim != 2 or values.dtype.kind not in "iuf":
        raise ValueError("invalid_plane")
    hidden = np.asarray(unseen)
    if hidden.shape != values.shape or hidden.dtype != np.bool_:
        raise ValueError("invalid_unseen")
    block = block_pixels(spacing_rc, block_mm)
    pitch = spacing_pair(spacing_rc)
    rows, cols = values.shape
    r0, r1, c0, c1 = (0, rows, 0, cols) if window is None else window
    if not (0 <= r0 < r1 <= rows and 0 <= c0 < c1 <= cols):
        raise ValueError("invalid_window")
    crop = values[r0:r1, c0:c1].astype(np.float64)
    seen = np.where(hidden[r0:r1, c0:c1] | ~np.isfinite(crop), np.nan, crop)
    down, across = ceil(crop.shape[0] / block[0]), ceil(crop.shape[1] / block[1])
    padded = np.full((down * block[0], across * block[1]), np.nan)
    padded[: crop.shape[0], : crop.shape[1]] = seen
    gathered = padded.reshape(down, block[0], across, block[1]).transpose(0, 2, 1, 3)
    gathered = gathered.reshape(down, across, -1)
    whole = ~np.isnan(gathered).any(axis=-1)
    median = np.full((down, across), np.nan)
    if whole.any():
        median[whole] = np.median(gathered[whole], axis=-1)
    return BlockReading(
        handed_on(median),
        block,
        (block[0] * pitch[0], block[1] * pitch[1]),
        (int(r0), int(r1), int(c0), int(c1)),
    )


def block_centres_rc(reading: BlockReading) -> np.ndarray:
    """The native (row, column) centre of every block (BR, BC, 2), in pixels: the middle of the
    pixels the block holds, so a frame's `to_patient` places it in the scanner's millimetres."""
    r0, _, c0, _ = reading.window_rc
    down, across = reading.median.shape
    rows = r0 + (np.arange(down) + 0.5) * reading.block_px[0] - 0.5
    cols = c0 + (np.arange(across) + 0.5) * reading.block_px[1] - 0.5
    return np.stack(np.meshgrid(rows, cols, indexing="ij"), axis=-1)


def block_holds(mask: np.ndarray, reading: BlockReading) -> np.ndarray:
    """Which blocks of a reading hold at least one place of a native `mask` (R, C): how a part's
    places, carried on the same pixel grid, are put on the finer reading's blocks. Places of the
    window's partial last blocks beyond the picture are not places."""
    places = np.asarray(mask, dtype=bool)
    r0, r1, c0, c1 = reading.window_rc
    crop = places[r0:r1, c0:c1]
    down, across = reading.median.shape
    padded = np.zeros((down * reading.block_px[0], across * reading.block_px[1]), bool)
    padded[: crop.shape[0], : crop.shape[1]] = crop
    blocks = padded.reshape(down, reading.block_px[0], across, reading.block_px[1])
    return blocks.any(axis=(1, 3))


def could_hold_level(
    minimum: np.ndarray, maximum: np.ndarray, low: float, high: float
) -> tuple[np.ndarray, np.ndarray]:
    """Which tiles hold a pixel whose light could lie in [low, high], and which have nothing seen.

    A tile whose maximum is under `low`, or whose minimum is over `high`, holds no pixel at the
    level: the exact exclusion one tile's own extrema make, never a decision that the level is
    there. It says nothing of a finer block whose footprint crosses into a neighbouring tile: that
    block's median can lie in the level though neither tile's extrema do. For a block, take the
    extrema over every tile its footprint can touch (`could_hold_level_in_reach`). A tile with no
    finite pixel (NaN extrema) is unseen, so it excludes nothing and is returned apart:
    (could, unseen), both shaped as the tiles.
    """
    low_tiles, high_tiles = np.asarray(minimum, float), np.asarray(maximum, float)
    if low_tiles.shape != high_tiles.shape:
        raise ValueError("extrema_must_share_a_shape")
    unseen = ~np.isfinite(low_tiles) | ~np.isfinite(high_tiles)
    could = ~unseen & (high_tiles >= low) & (low_tiles <= high)
    return could, unseen


@dataclass(frozen=True, slots=True)
class TileReach:
    """For each tile row and each tile column, the inclusive range of tiles a finer block with a
    pixel in that tile can touch: `rows` (TR, 2) and `cols` (TC, 2) as (first, last) tile indices."""

    rows: np.ndarray
    cols: np.ndarray


def footprint_reach(bounds_rc: np.ndarray, block_px: tuple[int, int]) -> TileReach:
    """The tiles a block can touch, for each tile: a block of `block_px` pixels with at least one
    pixel in a tile lies within `block - 1` pixels of that tile's bounds, so it touches only the
    tiles that range overlaps, whatever window it was cut from. `bounds_rc` (TR, TC, 4) is the
    squint's half-open native tile bounds; its rows and columns must form a grid (every tile of a
    row shares the row's bounds, as the squint's do), else ValueError `tile_grid_is_not_regular`.
    Raises `invalid_bounds` and `invalid_block_px` for what it cannot place."""
    bounds = np.asarray(bounds_rc)
    if bounds.ndim != 3 or bounds.shape[2] != 4 or min(bounds.shape[:2]) < 1:
        raise ValueError("invalid_bounds")
    if min(block_px) < 1:
        raise ValueError("invalid_block_px")
    r0, r1 = bounds[:, 0, 0], bounds[:, 0, 1]
    c0, c1 = bounds[0, :, 2], bounds[0, :, 3]
    if not (
        (bounds[:, :, 0] == r0[:, None]).all()
        and (bounds[:, :, 1] == r1[:, None]).all()
        and (bounds[:, :, 2] == c0[None, :]).all()
        and (bounds[:, :, 3] == c1[None, :]).all()
    ):
        raise ValueError("tile_grid_is_not_regular")

    def span(first: np.ndarray, stop: np.ndarray, block: int) -> np.ndarray:
        # tiles j with first_j < stop_i + block - 1 and stop_j > first_i - (block - 1)
        before = np.searchsorted(stop, first - (block - 1), side="right")
        after = np.searchsorted(first, stop + (block - 1), side="left") - 1
        return np.column_stack((before, after)).astype(np.int64)

    return TileReach(span(r0, r1, block_px[0]), span(c0, c1, block_px[1]))


def over_reach(values: np.ndarray, reach: TileReach, how: np.ufunc) -> np.ndarray:
    """`how` (np.fmin, np.fmax or np.logical_or) reduced over each tile's reach, (TR, TC): the
    greatest, least or any of what its footprint can touch. fmin and fmax ignore a NaN tile and
    are NaN only where every tile in reach is."""
    grid = np.asarray(values)
    if grid.shape != (len(reach.rows), len(reach.cols)):
        raise ValueError("values_must_be_the_tile_grid")
    rows = np.stack([how.reduce(grid[a : b + 1], axis=0) for a, b in reach.rows])
    return np.stack(
        [how.reduce(rows[:, a : b + 1], axis=1) for a, b in reach.cols], axis=1
    )


def could_hold_level_in_reach(
    minimum: np.ndarray,
    maximum: np.ndarray,
    low: float,
    high: float,
    reach: TileReach,
) -> tuple[np.ndarray, np.ndarray]:
    """Which tiles a finer block with a pixel in them could read at a median in [low, high], and
    which of them a block could also touch an unseen tile from: (could, blind), shaped as the tiles.

    A block's median lies between the least minimum and the greatest maximum of the tiles its
    footprint touches, so a tile is excluded only when the extrema over its whole reach exclude
    the level (`could_hold_level` over `over_reach`'s extrema). The reading of each tile is the
    squint's own; only the set of tiles it is taken over is widened to the footprint. A tile with no
    finite pixel contributes no extremum, since a block over an unseen pixel is not read at all;
    `blind` marks where one lies in the reach, so an exclusion there is an unknown and never an
    absence."""
    lows, highs = np.asarray(minimum, float), np.asarray(maximum, float)
    could, _ = could_hold_level(
        over_reach(lows, reach, np.fmin), over_reach(highs, reach, np.fmax), low, high
    )
    nothing_seen = ~np.isfinite(lows) | ~np.isfinite(highs)
    return could, over_reach(nothing_seen, reach, np.logical_or)


def positive_runs(values: np.ndarray) -> list[tuple[int, int]]:
    """The runs of consecutive indices whose value is finite and positive, half-open (start, stop),
    in index order. NaN (not read, not readable) and zero (measured empty) both end a run."""
    held = np.isfinite(np.asarray(values, float)) & (np.asarray(values, float) > 0)
    edges = np.diff(np.concatenate(([0], held.astype(np.int8), [0])))
    starts, stops = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    return [(int(a), int(b)) for a, b in zip(starts, stops, strict=True)]


def run_maxima(values: np.ndarray, runs: list[tuple[int, int]]) -> list[np.ndarray]:
    """For each run, every index of it that reaches the run's maximum, in index order: a plateau
    keeps all of its slices and a tie is never broken here."""
    series = np.asarray(values, float)
    return [
        start + np.flatnonzero(series[start:stop] == series[start:stop].max())
        for start, stop in runs
    ]


def confirmations(
    runs: list[tuple[int, int]],
    maxima: list[np.ndarray],
    status: np.ndarray,
    unresolved: tuple[int, ...],
) -> list[int]:
    """The slices a profile cannot rule out and so points to native confirmation: where a run's
    maximum lies at an end of the run and the slice beyond it was neither read as empty nor beyond
    the scan but unresolved (its status is one of `unresolved`: not readable, or cut), the larger
    body the profile cannot see may lie there. Index order, each slice once; a maximum inside a run
    or beside a measured-empty slice, a run's end at the scan's edge and a slice that was never
    read (outside the corridor) point nowhere."""
    codes = np.asarray(status)
    found: set[int] = set()
    for (start, stop), peaks in zip(runs, maxima, strict=True):
        if start in peaks and start > 0 and int(codes[start - 1]) in unresolved:
            found.add(start - 1)
        if stop - 1 in peaks and stop < len(codes) and int(codes[stop]) in unresolved:
            found.add(stop)
    return sorted(found)


def run_neighbours(runs: list[tuple[int, int]], status: np.ndarray) -> np.ndarray:
    """What each run's two ends touch, (n, 2) int: the status of the slice before the run and of
    the slice after it, or `CLIPPED_BY_THE_SCAN` where the run reaches the first or the last slice
    and the scan ends there. The statuses' meanings are the profile's own."""
    codes = np.asarray(status)
    found = np.full((len(runs), 2), CLIPPED_BY_THE_SCAN, dtype=np.int64)
    for i, (start, stop) in enumerate(runs):
        if start > 0:
            found[i, 0] = int(codes[start - 1])
        if stop < len(codes):
            found[i, 1] = int(codes[stop])
    return found


def depth_offsets_mm(
    origins_lps: np.ndarray, normal: np.ndarray, at: int
) -> np.ndarray:
    """Each slice's place along the series' normal in millimetres, from slice `at`'s plane: the
    physical depth of the profile (positive toward the normal's direction), whatever order the
    stack runs in and however unequal its spacing. Refuses origins that are not (Z, 3) finite and
    a normal that is not a finite, nonzero 3-vector."""
    origins = np.asarray(origins_lps, dtype=np.float64)
    axis = np.asarray(normal, dtype=np.float64)
    if origins.ndim != 2 or origins.shape[1] != 3 or not np.all(np.isfinite(origins)):
        raise ValueError("invalid_slice_origins")
    if axis.shape != (3,) or not np.all(np.isfinite(axis)) or not np.any(axis):
        raise ValueError("invalid_series_normal")
    if not 0 <= at < len(origins):
        raise ValueError("invalid_slice_index")
    return (origins - origins[at]) @ (axis / np.linalg.norm(axis))


def support_intervals_mm(
    offsets_mm: np.ndarray, thickness_mm: np.ndarray, runs: list[tuple[int, int]]
) -> np.ndarray:
    """Each run's physical ENVELOPE (n, 2), [low, high] along the normal: from the lowest slice
    plane's lower face to the highest one's upper face, each face half its slice's thickness from
    its centre. It is an envelope over the sampled slabs, never dense occupancy: slices are not
    interpolated and nothing is claimed between them (`run_slabs_mm` and `slab_gaps_mm` keep the
    slabs and what lies between them). NaN where a thickness is not known, since a face cannot be
    placed without it."""
    offsets = np.asarray(offsets_mm, float)
    thick = np.asarray(thickness_mm, float)
    if offsets.shape != thick.shape:
        raise ValueError("thickness_must_match_the_slices")
    found = np.full((len(runs), 2), np.nan)
    for i, (start, stop) in enumerate(runs):
        low = offsets[start:stop] - thick[start:stop] / 2.0
        high = offsets[start:stop] + thick[start:stop] / 2.0
        found[i] = (low.min(), high.max())
    return found


def run_slabs_mm(
    offsets_mm: np.ndarray, thickness_mm: np.ndarray, runs: list[tuple[int, int]]
) -> list[np.ndarray]:
    """The sampled slabs of each run, (k, 2) [low, high] along the normal, in physical order
    whatever the stack's order: each slice's plane is a slab half its thickness either side of its
    offset. NaN where a thickness is not known. These are the planes that were measured; the
    run's envelope (`support_intervals_mm`) lies over them and over the gaps between them."""
    offsets = np.asarray(offsets_mm, float)
    thick = np.asarray(thickness_mm, float)
    if offsets.shape != thick.shape:
        raise ValueError("thickness_must_match_the_slices")
    found = []
    for start, stop in runs:
        order = np.argsort(offsets[start:stop], kind="stable")
        centre, half = offsets[start:stop][order], thick[start:stop][order] / 2.0
        found.append(np.column_stack((centre - half, centre + half)))
    return found


def slab_gaps_mm(slabs: np.ndarray) -> np.ndarray:
    """The distance from each sampled slab's upper face to the next one's lower face, (k - 1,), in
    physical order: positive where nothing was sampled between two slices (the envelope spans it
    unmeasured), zero where they touch and negative where they overlap. NaN where unknown."""
    faces = np.asarray(slabs, float)
    if faces.ndim != 2 or faces.shape[1] != 2:
        raise ValueError("slabs_are_low_high_pairs")
    return faces[1:, 0] - faces[:-1, 1]


@dataclass(frozen=True, slots=True)
class FineReading:
    """One slice's finer reading as it was made, at its own small resolution: the slice `index`, the
    native half-open `window_rc` it was read over, `block_px` and `block_mm` the block's size,
    `median` (BR, BC) the block medians (NaN where unseen), and the two bodies the pointer drew on
    that block grid, `body` the largest whole candidate and `tibia` the reference body, both
    (BR, BC) bool. Windows differ slice to slice: nothing here is padded to a common shape."""

    index: int
    window_rc: tuple[int, int, int, int]
    block_px: tuple[int, int]
    block_mm: tuple[float, float]
    median: np.ndarray
    body: np.ndarray
    tibia: np.ndarray


def pack_fine_readings(readings: Sequence[FineReading]) -> dict[str, np.ndarray]:
    """The ragged finer readings as arrays for one record, with every per-slice fact explicit:
    `slices` (n,) the native slice of each reading; `windows_rc` (n, 4), `block_px` (n, 2),
    `block_mm` (n, 2) and `shapes` (n, 2) the window, block size and block-grid shape of each;
    `offsets` (n + 1,) where each reading starts in the flat arrays; and the flat row-major
    concatenations `median` (float64), `pointer_body` and `tibia_reference` (bool), each reading
    `shapes[i]` blocks at `offsets[i]:offsets[i + 1]`. Nothing is padded to the volume or to a
    common window. (The inverse lives with the tests; production only writes.)"""
    count = len(readings)
    shapes = np.array([r.median.shape for r in readings], dtype=np.int32).reshape(
        count, 2
    )
    sizes = shapes[:, 0].astype(np.int64) * shapes[:, 1]
    return {
        "slices": np.array([r.index for r in readings], dtype=np.int32),
        "windows_rc": np.array([r.window_rc for r in readings], dtype=np.int32).reshape(
            count, 4
        ),
        "block_px": np.array([r.block_px for r in readings], dtype=np.int32).reshape(
            count, 2
        ),
        "block_mm": np.array([r.block_mm for r in readings], dtype=np.float64).reshape(
            count, 2
        ),
        "shapes": shapes,
        "offsets": np.concatenate(([0], np.cumsum(sizes))).astype(np.int64),
        "median": np.concatenate(
            [np.asarray(r.median, dtype=np.float64).ravel() for r in readings]
            or [np.empty(0)]
        ),
        "pointer_body": np.concatenate(
            [np.asarray(r.body, dtype=bool).ravel() for r in readings]
            or [np.empty(0, bool)]
        ),
        "tibia_reference": np.concatenate(
            [np.asarray(r.tibia, dtype=bool).ravel() for r in readings]
            or [np.empty(0, bool)]
        ),
    }
