"""The bones' cheap marrow-body readings and the naming of their territory on a pointed plane:
measurements and the established majority rule only (`docs/DIMENSIONAL_COLLAPSE_PLAN.md` Step 5,
the bones, marrow and joint frame).

**Why it exists.** The femur and the tibia are named on each series' middle slice (the accepted
bootstrap). The collapse reads the rest of their stacks cheaply and asks the expensive question,
which lens territory is the bone, only on the planes where the cheap reading points. The cheap
reading is the SUPPORTED BROAD MARROW-BODY AREA of a slice: the area, in square millimetres, of the
marrow-like blocks (2 mm medians within the quarter of the bone's own light that every bone's
marrow is read at, `LIKE_THE_TIBIA`) that form a body at least a bone across (`BONE_MM`) and that
belong to the bone. It is a property of the marrow BODY, never a best view of everything: where a
bone's section is broad the area is large, and where only a cortical sliver or soft tissue lies the
area is zero.

**Identity is never the coarse tiles'.** Marrow-like tiles of the squint join the femur and the
tibia through every coarse connection, so a component of them is not a bone. A piece of marrow-like
blocks belongs to a bone when most of its places lie on the bone's carried places on that slice
(`carried_bone`, the rule that already carries a bone from the middle slice to its neighbour); the
places of the OTHER bone are never counted for it, and a piece that holds blocks of both is `merged`:
only its blocks outside the other bone's places count. A bone's separate pieces (a femur's two
condyles) are one bone's body, summed, never two objects.

On a pointed plane the lens's territories are named against the same carried places
(`name_territory`): `identified` where `carried_bone` names territories, `ambiguous` where a
territory is as much the other bone's, and only readings (`territory_holding_most`, `tie`) where no
territory is mostly the bone's. Nothing unseen is absence: no place the lens never saw, and no
tile it never saw, is read as empty.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi

from knee.objects.assignments import BONE_MM, carried_bone

# What a pointed plane's naming can be, kept apart: the first is a name, the rest are not.
IDENTIFIED = "identified"
AMBIGUOUS = "ambiguous_shared_with_the_other_bone"
HOLDING_MOST = "territory_holding_most"
TIE = "tie"
NO_TERRITORY = "no_territory_under_the_places"
UNAVAILABLE = "unavailable"
NO_PLACES = "no_places_on_the_plane"
BODY_ELSEWHERE = "marrow_body_lies_outside_the_named_territory"
NOT_MARROW = "territory_is_mostly_not_marrow"
OUTCOMES = (
    IDENTIFIED,
    AMBIGUOUS,
    HOLDING_MOST,
    TIE,
    NO_TERRITORY,
    UNAVAILABLE,
    NO_PLACES,
    BODY_ELSEWHERE,
    NOT_MARROW,
)


def tiles_touched(places: np.ndarray, bounds_rc: np.ndarray) -> np.ndarray:
    """Which tiles of the squint's grid hold at least one of the native `places` (R, C): one
    integral image, so a plane costs a few array passes and no loop over tiles. `bounds_rc`
    (TR, TC, 4) are the half-open tile bounds."""
    held = np.asarray(places, dtype=bool)
    total = np.zeros((held.shape[0] + 1, held.shape[1] + 1), dtype=np.int64)
    total[1:, 1:] = held.cumsum(axis=0).cumsum(axis=1)
    r0, r1, c0, c1 = (bounds_rc[..., k] for k in range(4))
    return (total[r1, c1] - total[r0, c1] - total[r1, c0] + total[r0, c0]) > 0


def tiles_around(tiles: np.ndarray) -> np.ndarray:
    """The tiles and every tile beside them (one tile, the squint's 10 mm, is the bone's width
    `BONE_MM` of context)."""
    return ndi.binary_dilation(tiles, structure=np.ones((3, 3), dtype=bool))


@dataclass(frozen=True, slots=True)
class MarrowBody:
    """One slice's marrow body of one bone: `body` (BR, BC) the blocks of the pieces that belong to
    it, `area_mm2` their area, `pieces` how many separate pieces (a femur's condyles are several),
    `merged` whether a piece also held blocks of the other bone's places, `cut` whether a kept
    piece reaches a window edge that is not the picture's own."""

    body: np.ndarray
    area_mm2: float
    pieces: int
    merged: bool
    cut: bool


def marrow_body(
    median: np.ndarray,
    block_mm: tuple[float, float],
    light: float,
    level: tuple[float, float],
    own: np.ndarray,
    other: np.ndarray,
    open_edge: np.ndarray,
) -> MarrowBody:
    """The marrow body of a bone in a window of block medians (BR, BC; NaN where unseen).

    The blocks whose median lies in `level` times the bone's own `light` are the marrow-like
    blocks; their connected pieces are kept for the bone by `carried_bone` against `own` (the bone's
    carried places on the block grid), never by size or by touching the tiles; a kept piece must
    hold a disc `BONE_MM` across (the largest distance from its edge, in millimetres, is at least
    half of it). A piece that also holds blocks of `other` (the other bone's carried places) is
    `merged`, and only its blocks outside them count. `open_edge` (BR, BC) marks the blocks on a
    window side that is not the picture's own edge: a kept piece reaching one is `cut`. A light
    that is not positive and finite leaves nothing readable and is refused by the caller."""
    values = np.asarray(median, dtype=np.float64)
    low, high = level[0] * light, level[1] * light
    held = np.isfinite(values) & (values >= low) & (values <= high)
    pieces, count = ndi.label(held)
    kept = carried_bone(pieces, np.asarray(own, dtype=bool))
    # a bone-sized body: the piece's widest place is at least a disc's radius from its edge
    pitch = float(np.mean(block_mm))
    reach = ndi.distance_transform_edt(np.pad(kept, 1))[1:-1, 1:-1] * pitch
    labels = np.arange(1, count + 1)
    widest = (
        np.asarray(ndi.maximum(reach, pieces, index=labels)) if count else np.zeros(0)
    )
    wide = labels[widest >= BONE_MM / 2.0] if count else labels
    body = kept & np.isin(pieces, wide)
    others = np.asarray(other, dtype=bool)
    shared = body & others
    merged = bool(shared.any())
    body = body & ~others
    found = int(ndi.label(body)[1])
    area = float(body.sum() * block_mm[0] * block_mm[1])
    cut = bool((body & np.asarray(open_edge, dtype=bool)).any())
    return MarrowBody(body, area, found, merged, cut)


@dataclass(frozen=True, slots=True)
class Naming:
    """The territories of a lens reading against one bone's carried places on a plane: the `code`
    (`OUTCOMES`), the `region` named (empty unless `identified` or `territory_holding_most`), its
    territory labels (`labels`), the seen places each territory holds (`hits`), the territories
    sharing the most places where none was chosen (`tied`) and those shared with the other bone
    (`shared`)."""

    code: str
    region: np.ndarray
    labels: tuple[int, ...]
    hits: dict[int, int]
    tied: tuple[int, ...]
    shared: tuple[int, ...]


def name_territory(
    lens_labels: np.ndarray,
    available: np.ndarray,
    own: np.ndarray,
    other: np.ndarray,
    body: np.ndarray | None = None,
) -> Naming:
    """Name the lens territories that are one bone on a plane, from the bone's carried places there
    (`own`, native pixels of the plane; `other` the other bone's), by `carried_bone`: the territories
    most of whose places were the bone. A territory that is as much the other bone's is `shared` and
    names neither: the bone's other territories stay named, and where none remain the code is
    `AMBIGUOUS`. Where no territory is mostly the bone's, the territory holding the most of its seen
    places is only a reading (`HOLDING_MOST`), several holding equally a `TIE` with none chosen, and
    no seen place on any territory `NO_TERRITORY`; no place the lens saw is `UNAVAILABLE` and no
    place on the plane `NO_PLACES`. Given the bone's marrow `body` on the plane (pixels), the territory
    holding most of it must be one named, else `BODY_ELSEWHERE`: the carried places alone can lie on
    soft tissue that the bone's projected outline covers. A bone with several territories (a femur's condyles) is one
    region."""
    labels = np.asarray(lens_labels)
    none = np.zeros(labels.shape, dtype=bool)
    places = np.asarray(own, dtype=bool)
    if not places.any():
        return Naming(NO_PLACES, none, (), {}, (), ())
    seen = places & np.asarray(available, dtype=bool)
    if not seen.any():
        return Naming(UNAVAILABLE, none, (), {}, (), ())
    held = labels[seen & (labels > 0)]
    counts = np.bincount(held) if held.size else np.zeros(0, dtype=np.int64)
    hits = {int(k): int(v) for k, v in enumerate(counts) if v}
    region = carried_bone(labels, seen)
    if region.any():
        theirs = carried_bone(
            labels, np.asarray(other, dtype=bool) & np.asarray(available, dtype=bool)
        )
        shared = tuple(int(k) for k in np.unique(labels[region & theirs]))
        region &= ~theirs
        named = tuple(int(k) for k in np.unique(labels[region]))
        if not region.any():
            return Naming(AMBIGUOUS, none, (), hits, (), shared)
        if body is not None:
            # two independent measurements must agree: the territory holding the bone's marrow
            # body (the profile's) is one the carried places named
            inside = labels[
                np.asarray(body, dtype=bool)
                & np.asarray(available, dtype=bool)
                & (labels > 0)
            ]
            if inside.size and int(np.argmax(np.bincount(inside))) not in named:
                return Naming(BODY_ELSEWHERE, none, (), hits, (), shared)
            # and a bone is its marrow inside its cortex: most of the places of a named territory
            # are the marrow body (the same "most" as `carried_bone`), else the territory is a lens
            # territory leaking over soft tissue that holds the body (seen on the lateral planes)
            marrow = int(np.count_nonzero(region & np.asarray(body, dtype=bool)))
            if 2 * marrow <= int(np.count_nonzero(region)):
                return Naming(NOT_MARROW, none, (), hits, (), shared)
        return Naming(IDENTIFIED, region, named, hits, (), shared)
    if not held.size:
        return Naming(NO_TERRITORY, none, (), hits, (), ())
    tied = tuple(int(k) for k in np.flatnonzero(counts == np.max(counts)))
    if len(tied) > 1:
        return Naming(TIE, none, (), hits, tied, ())
    return Naming(HOLDING_MOST, labels == tied[0], (tied[0],), hits, (), ())


def section_extent(
    mask: np.ndarray, up_mm: np.ndarray, available: np.ndarray, pitch_mm: float
) -> tuple[float, float, str, str] | None:
    """The physical extent of a named section along the leg: the lowest and highest `up_mm` (each
    native pixel's height in the scanner's millimetres, (R, C)) of the `mask`'s pixels, and what
    each end touches. An end is `clipped_by_the_scan` where the section reaches the picture's edge
    within one pixel of it, `unresolved` where a place the lens never saw (`available` False) lies
    beside it there, else `observed`: the section ends inside the picture with seen places beyond.
    None for an empty mask. The tolerance is the pixel `pitch_mm`, not a fitted number."""
    held = np.asarray(mask, dtype=bool)
    if not held.any():
        return None
    height = np.asarray(up_mm, dtype=np.float64)
    heights = height[held]
    low, high = float(heights.min()), float(heights.max())
    edge = np.zeros(held.shape, dtype=bool)
    edge[0], edge[-1], edge[:, 0], edge[:, -1] = True, True, True, True
    clipped = height[held & edge]
    beside = ndi.binary_dilation(held) & ~held & ~np.asarray(available, dtype=bool)
    unseen = height[beside]

    def end(value: float, sign: float) -> str:
        if clipped.size and np.any(sign * (clipped - value) >= -pitch_mm):
            return "clipped_by_the_scan"
        if unseen.size and np.any(sign * (unseen - value) >= -pitch_mm):
            return "unresolved"
        return "observed"

    return low, high, end(low, -1.0), end(high, 1.0)
