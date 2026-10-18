"""A body's whole section on ONE plane, read coarsely from the cortex that encloses it (the key plane's pointer
in any orientation; `docs/RELATIVE_POSITION_MAP.md` §8.8: each object's key plane in each of the three views).

**Why a coarse reading.** A body's carried support (a sagittal or coronal section's places, put in the scanner's
millimetres) meets another orientation's slice as a thin LINE: a location seed, never the body's section. The
section is what the NATIVE image's cortex encloses. The cortex is dark on every sequence (`docs/OBJECTS_AND_
CONDITIONS.md` §3), so marrow is a closed interior: darker than its enclosure where fat is suppressed, brighter
where it is not. The enclosure measurement is the existing erosion reconstruction (`enclosed_darkness`, no grey
cutoff), the same arithmetic in every orientation, and it is read on the 2 mm BLOCK MEDIANS of the plane
(`knee.collapse.profile.block_medians`, the length over which light is read as uniform and not speckled):
a coarse physical sampling, so the work is one small grid per plane and not the whole native plane. A block with
any place unseen is NaN, so an unseen or margin value can never reach a median or read as darkness; in the
measurement an unseen block is an open outlet (it is never a wall) and never part of a section.

**Shared once.** The coarse blocks and their depth belong to the PLANE and its marrow polarity, not to a body:
the femur, the tibia and the patella read the same depth grid (the caller hands it on). A body adds only its seeds.

**The rule** (`coarse_section`). The seeds are the blocks that hold ANY of the body's carried places (a thin
physical seed becomes an any-overlap location block, never a majority owner). Their own enclosed depths say how
deeply enclosed this body's marrow is there: the level is the median of the seed blocks that are enclosed at all.
The section is every connected set of blocks at least that deep which holds a seed, holes filled. If its blocks
also hold another object's seeds it is not attributed (`SHARED`): the line crossed into a body that is not
this one's. No enclosed seed block is a measured empty section (`EMPTY`), not an absence of the body; no seeds
are unknown (`NOT_READ`). The key plane is the plane of the largest section by AREA in mm2; equal areas are a tie
and every tied plane is kept (`key_slices`).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi

from knee.collapse.physical import PlaneFrame
from knee.collapse.profile import BlockReading
from knee.objects.assignments import enclosed_darkness

NOT_READ = "not_read_no_seeds"
SEEDS_UNSEEN = "seeds_only_in_unseen_blocks_unknown"
EMPTY = "measured_no_enclosed_section"
SECTION = "section"
SHARED = "section_holds_another_objects_seeds_not_attributed"
STATUS_CODES = {
    NOT_READ: 0,
    SEEDS_UNSEEN: 1,
    EMPTY: 2,
    SECTION: 3,
    SHARED: 4,
}


@dataclass(frozen=True)
class CoarseSection:
    """One body's reading on one plane: `status` (`STATUS_CODES`), the `body` blocks (the block grid's shape;
    None unless a section), its area in mm2 (NaN unless a section; 0.0 where measured empty), the `level` it
    was cut at (NaN where there was no depth to read) and the `seeds` it was read from."""

    status: str
    body: np.ndarray | None
    area_mm2: float
    level: float
    seeds: np.ndarray


def coarse_depth(median: np.ndarray, marrow_is_dark: bool) -> np.ndarray:
    """How deeply each block of a coarse plane lies inside its enclosure (the shared contrast of the plane).

    `median` holds the block medians (NaN where any place of a block is unseen). Marrow that is bright is
    read on the inverted picture. An unseen block is the picture's darkest here, so it is an outlet to
    the outside and never a wall; its own depth is NaN. Positive rescaling of the light leaves every
    block's enclosed or not, and the sections cut from it, unchanged."""
    values = np.asarray(median, dtype=np.float64)
    if values.ndim != 2:
        raise ValueError("median_must_be_2d")
    seen = np.isfinite(values)
    if not seen.any():
        return np.full(values.shape, np.nan)
    work = values if marrow_is_dark else float(np.max(values[seen])) - values
    work = np.where(seen, work, float(np.min(work[seen])))
    depth = enclosed_darkness(work)
    return np.where(seen, depth, np.nan)


def coarse_section(
    depth: np.ndarray,
    seeds: np.ndarray,
    block_area_mm2: float,
    others: Mapping[str, np.ndarray] | None = None,
) -> CoarseSection:
    """The enclosed section the `seeds` (a boolean block mask) lie in, on a shared `depth` grid."""
    grid = np.asarray(depth, dtype=np.float64)
    marks = np.asarray(seeds, dtype=bool)
    if marks.shape != grid.shape:
        raise ValueError("seeds_must_share_the_block_grid")
    if not marks.any():
        return CoarseSection(NOT_READ, None, float("nan"), float("nan"), marks)
    seen = np.isfinite(grid)
    held = marks & seen
    if not held.any():
        return CoarseSection(SEEDS_UNSEEN, None, float("nan"), float("nan"), marks)
    inside = held & (grid > 0)
    if not inside.any():
        return CoarseSection(EMPTY, None, 0.0, 0.0, marks)
    level = float(np.median(grid[inside]))
    labels, _ = ndi.label(seen & (np.where(seen, grid, 0.0) >= level))
    touched = np.unique(labels[held])
    touched = touched[touched > 0]
    if not len(touched):
        return CoarseSection(EMPTY, None, 0.0, level, marks)
    body = ndi.binary_fill_holes(np.isin(labels, touched)) & seen
    for other in (others or {}).values():
        if np.any(np.asarray(other, dtype=bool) & body):
            return CoarseSection(SHARED, None, float("nan"), level, marks)
    return CoarseSection(
        SECTION, body, float(body.sum()) * float(block_area_mm2), level, marks
    )


def key_slices(area_mm2: np.ndarray) -> tuple[int, ...]:
    """The slices of the largest section, every tie kept; empty where no section was measured."""
    values = np.asarray(area_mm2, dtype=np.float64)
    held = np.isfinite(values) & (values > 0)
    if not held.any():
        return ()
    top = float(values[held].max())
    return tuple(int(z) for z in np.flatnonzero(held & (values == top)))


def body_extent_mm(
    body: np.ndarray,
    reading: BlockReading,
    frame: PlaneFrame,
    axis_lps: Sequence[float],
) -> float | None:
    """The physical extent of a section along a patient axis (millimetres): its blocks' corners, projected
    through the slice's own frame onto the unit `axis_lps`. This is the breadth of the section itself, never its
    centre. None where the section holds no block or the axis cannot be one."""
    marks = np.asarray(body, dtype=bool)
    axis = np.asarray(axis_lps, dtype=np.float64)
    if (
        not marks.any()
        or axis.shape != (3,)
        or not np.all(np.isfinite(axis))
        or not np.any(axis)
    ):
        return None
    axis = axis / np.linalg.norm(axis)
    r0, _, c0, _ = reading.window_rc
    br, bc = reading.block_px
    rows, cols = np.nonzero(marks)
    top = r0 + rows * br - 0.5
    left = c0 + cols * bc - 0.5
    corners = np.concatenate(
        [
            np.column_stack((top + dr * br, left + dc * bc))
            for dr in (0, 1)
            for dc in (0, 1)
        ]
    )
    along = frame.to_patient(corners) @ axis
    return float(along.max() - along.min())


def pack_sections(
    slices: Sequence[int],
    readings: Sequence[BlockReading],
    depths: Sequence[np.ndarray],
    found: Mapping[str, Sequence[CoarseSection]],
) -> dict[str, np.ndarray]:
    """The coarse readings of one series as packed arrays, nothing expanded to the native plane: `slices` (n,)
    the slices read; `windows_rc` (n, 4), `block_px` (n, 2), `block_mm` (n, 2) and `shapes` (n, 2) each plane's
    block grid; `offsets` (n + 1,) where each starts in the flat arrays; `median` and `depth` (float32; blocks
    with an unseen place are NaN); and for each body `<body>_status` (n,) int8 of `STATUS_CODES`,
    `<body>_area_mm2` and `<body>_level` (n,) float64, and the flat boolean `<body>_seeds` and `<body>_body`."""
    count = len(slices)
    shapes = np.array([r.median.shape for r in readings], dtype=np.int32).reshape(
        count, 2
    )
    sizes = shapes[:, 0].astype(np.int64) * shapes[:, 1]

    def flat(items: Sequence[np.ndarray | None], dtype) -> np.ndarray:
        parts = [
            np.zeros(int(n), dtype) if item is None else np.asarray(item, dtype).ravel()
            for item, n in zip(items, sizes, strict=True)
        ]
        return np.concatenate(parts) if parts else np.empty(0, dtype)

    out: dict[str, np.ndarray] = {
        "slices": np.asarray(slices, dtype=np.int32),
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
        "median": flat([r.median for r in readings], np.float32),
        "depth": flat(list(depths), np.float32),
    }
    for name, rows in found.items():
        out[f"{name}_status"] = np.array(
            [STATUS_CODES[s.status] for s in rows], dtype=np.int8
        )
        out[f"{name}_area_mm2"] = np.array([s.area_mm2 for s in rows], dtype=np.float64)
        out[f"{name}_level"] = np.array([s.level for s in rows], dtype=np.float64)
        out[f"{name}_seeds"] = flat([s.seeds for s in rows], bool)
        out[f"{name}_body"] = flat([s.body for s in rows], bool)
    return out
