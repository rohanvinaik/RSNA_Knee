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

**The scale-filtered estimate** (`scale_filtered_section`, for a reader that needs a bone's section and not every
body its seeds touch). The rule above takes every enclosed body the seeds touch. A carried support is a location
prior: its uncertain edge can touch a thin enclosed body that is not the bone (a strip of enclosure beside the
cortex), and nothing in the rule says such a body is not the section. A femur's or tibia's axial section at the
knee is centimetres across in every direction, so a touched body whose NARROWEST BREADTH (`narrowest_breadth_mm`:
the smallest width of the convex hull of its blocks' corners) is under a floor (`floor_mm`, the project's
`BONE_MM`, "a bone is at least a centimetre across") is left out of the ESTIMATE, whatever it is. Every other
touched body is kept whole, holes filled, and the estimate is `SHARED` where ITS OWN body holds another object's
seeds. This is a lossy scale filter: not the cortex-enclosed section and not a proof of identity. Bone pieces under
the floor are left out (an abstention on a piece, never a mislabel); a curved thin strip whose hull is broad, or a
non-bone body of bone scale the seeds touch, can remain. When every touched body is under the floor the estimate
says so (`NO_BONE_SCALE`), a measured abstention and not an absence. The unfiltered section is returned beside it
exactly as `coarse_section` returns it, made from the same level, labels and touched bodies, and every touched
body's block count and breadth is kept, kept or left out. `coarse_section` and its other readers are unchanged.
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
# Only the scale-filtered estimate's status, never `coarse_section`'s: every body the seeds touch is under
# the floor. A measured abstention, not an absence.
NO_BONE_SCALE = "measured_no_touched_body_of_bone_scale"
STATUS_CODES = {
    NOT_READ: 0,
    SEEDS_UNSEEN: 1,
    EMPTY: 2,
    SECTION: 3,
    SHARED: 4,
    NO_BONE_SCALE: 5,
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


@dataclass(frozen=True)
class TouchedComponent:
    """One body the seeds touch (a 4-connected set of blocks at least as deep as the cut level): its `blocks`
    (how many), its `breadth_mm` (`narrowest_breadth_mm`) and whether the scale filter `kept` it."""

    blocks: int
    breadth_mm: float
    kept: bool


@dataclass(frozen=True)
class ScaleEstimate:
    """The scale-filtered coarse section estimate of one body on one plane, a lossy scale filter and not the
    cortex-enclosed section or a proof of identity (the module note).

    `status` is SECTION; SHARED (the estimate's own body holds another object's seeds); NO_BONE_SCALE (every
    touched body is under `floor_mm`); or the unfiltered status carried over (NOT_READ, SEEDS_UNSEEN, EMPTY,
    where nothing was touched). `body` is the estimate's blocks (the block grid's shape; None unless SECTION):
    the touched bodies whose narrowest breadth is at least `floor_mm`, holes filled, within the seen blocks.
    `area_mm2` follows `CoarseSection`: NaN unless SECTION, 0.0 where measured empty or measured with no touched
    body of bone scale. `omitted` is the blocks of every touched body under the floor, as measured and before
    any hole filling: a body enclosed by a kept one therefore lies in `body` too, as a filled hole.
    `components` is every touched body in label order (the order the cut's labelling meets them), kept and
    omitted alike."""

    status: str
    body: np.ndarray | None
    area_mm2: float
    omitted: np.ndarray
    components: tuple[TouchedComponent, ...]
    floor_mm: float


@dataclass(frozen=True)
class ScaleFilteredSection:
    """Both readings of one body on one plane, made from one level, one labelling and one set of touched
    bodies: the `unfiltered` section exactly as `coarse_section` returns it, and the scale-filtered `estimate`."""

    unfiltered: CoarseSection
    estimate: ScaleEstimate


@dataclass(frozen=True)
class _Touched:
    """What both readings share once the seeds touch something: the seed blocks `marks`, the `seen` blocks,
    the cut `level`, the `labels` of the bodies at least that deep and the label numbers the seeds `touched`."""

    marks: np.ndarray
    seen: np.ndarray
    level: float
    labels: np.ndarray
    touched: np.ndarray


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


def _touched(depth: np.ndarray, seeds: np.ndarray) -> CoarseSection | _Touched:
    """Where both readings begin: the seeds checked against the grid, then either the abstention the seeds
    allow (no seeds, none seen, no enclosed seed block, no touched body: a `CoarseSection` with no body) or the
    cut level, the labelled bodies at least that deep and the label numbers the seeds touch."""
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
    return _Touched(marks, seen, level, labels, touched)


def _holds_another(body: np.ndarray, others: Mapping[str, np.ndarray] | None) -> bool:
    """Whether a body's blocks hold any seed of another object."""
    return any(
        np.any(np.asarray(other, dtype=bool) & body)
        for other in (others or {}).values()
    )


def _unfiltered(
    read: _Touched,
    block_area_mm2: float,
    others: Mapping[str, np.ndarray] | None,
) -> CoarseSection:
    """The section of every body the seeds touched, holes filled; SHARED where it holds another's seeds."""
    body = ndi.binary_fill_holes(np.isin(read.labels, read.touched)) & read.seen
    if _holds_another(body, others):
        return CoarseSection(SHARED, None, float("nan"), read.level, read.marks)
    return CoarseSection(
        SECTION, body, float(body.sum()) * float(block_area_mm2), read.level, read.marks
    )


def coarse_section(
    depth: np.ndarray,
    seeds: np.ndarray,
    block_area_mm2: float,
    others: Mapping[str, np.ndarray] | None = None,
) -> CoarseSection:
    """The enclosed section the `seeds` (a boolean block mask) lie in, on a shared `depth` grid."""
    read = _touched(depth, seeds)
    if isinstance(read, CoarseSection):
        return read
    return _unfiltered(read, block_area_mm2, others)


def _block_pair(block_mm: Sequence[float] | np.ndarray) -> np.ndarray:
    """A block's size in millimetres (rows, columns) as a float pair; ValueError `invalid_block_mm` unless
    both are positive and finite."""
    pitch = np.asarray(block_mm, dtype=np.float64)
    if pitch.shape != (2,) or not np.all(np.isfinite(pitch)) or np.any(pitch <= 0):
        raise ValueError("invalid_block_mm")
    return pitch


def _convex_hull(points: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    """The convex hull of integer points, counter-clockwise, collinear points dropped (Andrew's monotone chain
    in exact integer arithmetic: no rounding decides which points are corners)."""
    ordered = sorted(set(points))
    if len(ordered) <= 2:
        return ordered

    def turn(o: tuple[int, int], a: tuple[int, int], b: tuple[int, int]) -> int:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    chains: list[list[tuple[int, int]]] = []
    for sequence in (ordered, ordered[::-1]):
        chain: list[tuple[int, int]] = []
        for point in sequence:
            while len(chain) >= 2 and turn(chain[-2], chain[-1], point) <= 0:
                chain.pop()
            chain.append(point)
        chains.append(chain[:-1])
    return chains[0] + chains[1]


def narrowest_breadth_mm(
    component: np.ndarray, block_mm: Sequence[float] | np.ndarray
) -> float:
    """The narrowest breadth of one body of blocks, in millimetres: the smallest width of the convex hull of its
    blocks' corners, each block `block_mm[0]` by `block_mm[1]` millimetres (rows, columns). It is the minimum,
    over the hull's edge normals, of the corners' extent along the normal: the body's extent in its thinnest
    direction. A single block's breadth is its shorter side, a straight line of blocks has its width, and a body
    with holes has the breadth of its outline (the hull ignores them), as an L or a curved strip has the breadth
    of its hull and not of its arm. Pure; the hull is found in exact integer block coordinates.

    ValueError for a component that is not 2-D (`component_must_be_2d`), an empty one (`empty_component`) and a
    block size that is not two positive finite numbers (`invalid_block_mm`)."""
    marks = np.asarray(component, dtype=bool)
    if marks.ndim != 2:
        raise ValueError("component_must_be_2d")
    pitch = _block_pair(block_mm)
    if not marks.any():
        raise ValueError("empty_component")
    # Only the two ends of each block row can be corners of the hull, so the hull is found over those.
    rows = np.flatnonzero(marks.any(axis=1))
    first = marks.argmax(axis=1)[rows]
    past = marks.shape[1] - marks[:, ::-1].argmax(axis=1)[rows]
    corners = {
        (int(row) + down, int(column))
        for row, low, high in zip(rows, first, past, strict=True)
        for down in (0, 1)
        for column in (low, high)
    }
    hull = np.asarray(_convex_hull(sorted(corners)), dtype=np.float64) * pitch
    edges = np.roll(hull, -1, axis=0) - hull
    normals = (
        np.column_stack((-edges[:, 1], edges[:, 0]))
        / np.hypot(edges[:, 0], edges[:, 1])[:, None]
    )
    along = hull @ normals.T
    return float((along.max(axis=0) - along.min(axis=0)).min())


def scale_filtered_section(
    depth: np.ndarray,
    seeds: np.ndarray,
    block_area_mm2: float,
    block_mm: Sequence[float],
    floor_mm: float,
    others: Mapping[str, np.ndarray] | None = None,
) -> ScaleFilteredSection:
    """Both readings of the `seeds` on a shared `depth` grid: the unfiltered section exactly as `coarse_section`
    returns it for the same `depth`, `seeds`, `block_area_mm2` and `others`, and the scale-filtered estimate
    (the module note): the touched bodies whose narrowest breadth (`narrowest_breadth_mm`, over blocks of
    `block_mm` = (rows, columns) millimetres) is at least `floor_mm`, holes filled within the seen blocks, SHARED
    judged on the estimate's own body only. The level, the labelling and the touched bodies are made once and
    shared. Where the seeds touch nothing both readings are the same abstention (NOT_READ, SEEDS_UNSEEN, EMPTY).
    Every touched body's block count, breadth and whether it was kept are in `estimate.components`, and the
    blocks of the omitted ones in `estimate.omitted`; nothing is erased.

    ValueError for a seed mask of another shape than the grid (`seeds_must_share_the_block_grid`), a block size
    that is not two positive finite numbers (`invalid_block_mm`) and a floor that is not finite and not
    negative (`invalid_floor_mm`)."""
    pitch = _block_pair(block_mm)
    floor = float(floor_mm)
    if not np.isfinite(floor) or floor < 0:
        raise ValueError("invalid_floor_mm")
    read = _touched(depth, seeds)
    if isinstance(read, CoarseSection):
        nothing = np.zeros(read.seeds.shape, dtype=bool)
        carried = ScaleEstimate(read.status, None, read.area_mm2, nothing, (), floor)
        return ScaleFilteredSection(read, carried)
    unfiltered = _unfiltered(read, block_area_mm2, others)
    windows = ndi.find_objects(read.labels)
    components = []
    for label in read.touched:
        crop = read.labels[windows[int(label) - 1]] == label
        breadth = narrowest_breadth_mm(crop, pitch)
        components.append(
            TouchedComponent(int(crop.sum()), breadth, bool(breadth >= floor))
        )
    keep = np.array([part.kept for part in components], dtype=bool)
    omitted = np.isin(read.labels, read.touched[~keep])
    if not keep.any():
        estimate = ScaleEstimate(
            NO_BONE_SCALE, None, 0.0, omitted, tuple(components), floor
        )
        return ScaleFilteredSection(unfiltered, estimate)
    body = ndi.binary_fill_holes(np.isin(read.labels, read.touched[keep])) & read.seen
    if _holds_another(body, others):
        estimate = ScaleEstimate(
            SHARED, None, float("nan"), omitted, tuple(components), floor
        )
    else:
        area = float(body.sum()) * float(block_area_mm2)
        estimate = ScaleEstimate(SECTION, body, area, omitted, tuple(components), floor)
    return ScaleFilteredSection(unfiltered, estimate)


def key_slices(area_mm2: np.ndarray) -> tuple[int, ...]:
    """The slices of the largest section, every tie kept; empty where no section was measured."""
    values = np.asarray(area_mm2, dtype=np.float64)
    held = np.isfinite(values) & (values > 0)
    if not held.any():
        return ()
    top = float(values[held].max())
    return tuple(int(z) for z in np.flatnonzero(held & (values == top)))


def body_axis_bounds_mm(
    body: np.ndarray,
    reading: BlockReading,
    frame: PlaneFrame,
    axis_lps: Sequence[float],
) -> tuple[float, float] | None:
    """Minimum and maximum patient-axis coordinates of every supported block corner.

    Transform each section through its actual frame before combining bounds across views. None where the body
    holds no block or the axis cannot be one.
    """
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
    return float(along.min()), float(along.max())


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


def pack_estimates(
    readings: Sequence[BlockReading],
    found: Mapping[str, Sequence[ScaleEstimate | None]],
) -> dict[str, np.ndarray]:
    """The scale-filtered estimates of one series as packed arrays, beside `pack_sections` and on the same
    planes (`readings`, one per slice read, in the order of the `slices` and `offsets` it packs). For each body,
    from its `found` list (one entry per reading, None where no estimate was made, because the body was not
    attributed on that slice): `<body>_estimate_made` (n,) bool; `<body>_estimate_status` (n,) int8 of
    `STATUS_CODES` and `<body>_estimate_area_mm2` (n,) float64, which read NOT_READ and NaN where none was made
    (`_estimate_made` says which); the flat boolean `<body>_estimate_body` and `<body>_omitted` over the planes'
    blocks, in the planes' `offsets`; and the touched bodies, ragged, in their own `<body>_component_offsets`
    (n + 1,) int64: flat `<body>_component_blocks` int32, `<body>_component_breadth_mm` float64 and
    `<body>_component_kept` bool. Nothing is expanded to the native plane."""
    count = len(readings)
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

    out: dict[str, np.ndarray] = {}
    for name, rows in found.items():
        if len(rows) != count:
            raise ValueError("estimates_must_match_the_readings")
        out[f"{name}_estimate_made"] = np.array(
            [row is not None for row in rows], dtype=bool
        )
        out[f"{name}_estimate_status"] = np.array(
            [STATUS_CODES[NOT_READ if row is None else row.status] for row in rows],
            dtype=np.int8,
        )
        out[f"{name}_estimate_area_mm2"] = np.array(
            [float("nan") if row is None else row.area_mm2 for row in rows],
            dtype=np.float64,
        )
        out[f"{name}_estimate_body"] = flat(
            [None if row is None else row.body for row in rows], bool
        )
        out[f"{name}_omitted"] = flat(
            [None if row is None else row.omitted for row in rows], bool
        )
        parts = [part for row in rows if row is not None for part in row.components]
        out[f"{name}_component_offsets"] = np.concatenate(
            (
                [0],
                np.cumsum([0 if row is None else len(row.components) for row in rows]),
            )
        ).astype(np.int64)
        out[f"{name}_component_blocks"] = np.array(
            [part.blocks for part in parts], dtype=np.int32
        )
        out[f"{name}_component_breadth_mm"] = np.array(
            [part.breadth_mm for part in parts], dtype=np.float64
        )
        out[f"{name}_component_kept"] = np.array(
            [part.kept for part in parts], dtype=bool
        )
    return out
