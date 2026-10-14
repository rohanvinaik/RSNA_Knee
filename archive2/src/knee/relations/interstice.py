"""The interstice: the space between two facing objects, constructed from them, with its walls, fill and contents.

**Why it exists, against the settled record.** "Interstitial space...is the space between the two
bones we resolve as objects! That's LITERALLY what the term means ... the role is definitionally
defined as a relative one, because that's literally how the physical object works. Its shape, the
forces that are acting on it, the shear or crush force, the over-fill of fluid or tear or wear in
the space is defined by how it interfaces with the bones it is "interstitial" to" (the founder,
2026-10-11). So nothing here is detected: given a facing pair, the space between exists, and
what is read is its extent, its two walls, what fills it, and what lies in it. The things in it
(the design's glosses: menisci at the periphery, cruciates at the centre) are round-2 objects,
named by position and side, never by anatomy. "Synovitis ... Once you know what the "capsule" is
... then just look at the contrast data. Bam."

**The rule, at tile scale, on one chosen slice.** The extent is the gap tiles of the facing pair
together with every tile that lies between the two objects' territories along the pair's axis
(the line from the first object's centre to the second's), interior or dark obstacle but never a
tile the lens cleared: a tile whose projection on that axis lies between the two territories'
nearest faces and whose projection across it lies within the overlap of the two territories'
widths. Each wall is read from the
strip of the object on that side, along the profiles whose normals point into the extent: the
native digits from the object's dark band outward make a sequence, and `wall_code` names it. The
fill is the conjunction codes over the extent's tiles, named by `fill_code`. The contents are the
four-connected bodies of `below_below` tiles inside the extent, each a round-2 object with
`position_code` by its offset from the pair's axis and `side_code` by its left-right offset and
the laterality sign.

This is the funnel's operation 8 (`openspec/changes/the-funnel/design.md` R8, tasks 8.1 to
8.3). The pure decisions are `wall_code`, `fill_code`, `position_code` and `side_code`;
`read_interstices` is orchestration; task 8.2, replacing the shell `knee.relations.shell` while
keeping its `Interstice` and `KINDS`, is the integrator's.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
from scipy import ndimage

from knee.compute.contracts import handed_on
from knee.lenses.conjunction import CONJUNCTION_CODES, READ_CONJUNCTIONS, Conjunction
from knee.lenses.places import SILENT
from knee.objects.laterality import SIGN_CODES
from knee.objects.strip import TRACE_CODES, Strip
from knee.objects.tile_dome import TileDome
from knee.relations.facing import FacingPair, FacingPairs, between_region
from knee.telemetry import ledger

#: What one wall of an interstice reads as, from the object's dark band outward: a plate (the
#: dark band) then a layer (an intermediate run at the middle) then the fill; a plate then the
#: fill directly; or a sequence that cannot be read so.
WALL_CODES: tuple[str, ...] = ("plate_layer_fill", "plate_fill", "unreadable")

#: What fills an interstice: the one read pair that holds most of its tiles, a mix with no one
#: pair ahead, no read tile at all, or a refusal.
FILL_CODES: tuple[str, ...] = (
    *READ_CONJUNCTIONS,
    "fill_mixed",
    "fill_unread",
    "invalid_measurement",
)

#: Where a content lies across the pair's axis.
POSITION_CODES: tuple[str, ...] = ("peripheral", "central", "invalid_measurement")

#: Which side of the knee a content or a span lies on, given the laterality sign.
SIDE_CODES: tuple[str, ...] = (
    "medial",
    "lateral",
    "side_abstained",
    "invalid_measurement",
)

#: What one facing pair's interstice reports as a whole.
INTERSTICE_CODES: tuple[str, ...] = ("present", "no_extent", "predecessor_absent")


def wall_code(sequence: tuple[int, ...]) -> str:
    """What one wall reads as, from the object's dark band outward (pure -- pinned).

    `sequence` is the native digits along one profile from the first sample of the object's
    dark band outward into the space: -1 below, 0 at, +1 above the object's own terciles, 2
    silence. Not a tuple or list of those values, or empty, is "unreadable". The plate is the
    leading run of -1: a sequence that does not begin with -1 is "unreadable" (no band to read
    from). After the plate: nothing left, or a silence, is "unreadable"; a run of 0 followed by
    a non-silent digit is "plate_layer_fill" (a layer lies between the plate and the fill); a run
    of 0 followed by nothing or a silence is "unreadable"; any other digit is "plate_fill".

    post: __return__ in WALL_CODES
    """
    if not isinstance(sequence, (tuple, list)) or not sequence:
        return "unreadable"
    digits = []
    for value in sequence:
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value not in (-1, 0, 1, 2)
        ):
            return "unreadable"
        digits.append(value)
    if digits[0] != -1:
        return "unreadable"
    i = 0
    while i < len(digits) and digits[i] == -1:
        i += 1
    rest = digits[i:]
    if not rest or rest[0] == 2:
        return "unreadable"
    if rest[0] == 0:
        j = 0
        while j < len(rest) and rest[j] == 0:
            j += 1
        after = rest[j:]
        if not after or after[0] == 2:
            return "unreadable"
        return "plate_layer_fill"
    return "plate_fill"


def fill_code(counts: Mapping[str, int]) -> str:
    """What fills the extent, from the conjunction codes counted over its tiles (pure -- pinned).

    `counts` maps conjunction words to tile counts. Not a mapping, a key that is not a word of
    the conjunction's read pairs or silences, or a count that is not a non-negative int, is
    "invalid_measurement" (silences and `unmatched` may be present and are ignored). No read
    pair with a count above zero is "fill_unread". The read pair with the largest count is the
    fill; two or more read pairs tied for the largest is "fill_mixed".

    post: __return__ in FILL_CODES
    """
    if not isinstance(counts, Mapping):
        return "invalid_measurement"
    allowed = (*READ_CONJUNCTIONS, "partner_silent", "self_silent", "unmatched")
    best, best_count, tied = None, 0, False
    for word, count in counts.items():
        if (
            word not in allowed
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count < 0
        ):
            return "invalid_measurement"
        if word not in READ_CONJUNCTIONS or count == 0:
            continue
        if count > best_count:
            best, best_count, tied = word, count, False
        elif count == best_count:
            tied = True
    if best is None:
        return "fill_unread"
    return "fill_mixed" if tied else best


def position_code(offset_mm: float, half_width_mm: float) -> str:
    """Where a content lies across the pair's axis (pure -- pinned).

    `offset_mm` is the content's centre's distance from the pair's axis, across it;
    `half_width_mm` half the overlap of the two objects' widths across that axis. A bool, a
    non-number, a NaN, or a half width that is not positive is "invalid_measurement". A centre
    within the inner half of the width (|offset| < half_width / 2) is "central"; else
    "peripheral". The lead's rule; the founder changes the fraction by eye.

    post: __return__ in POSITION_CODES
    """
    if any(
        isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
        for v in (offset_mm, half_width_mm)
    ):
        return "invalid_measurement"
    if half_width_mm <= 0.0:
        return "invalid_measurement"
    return "central" if abs(offset_mm) < half_width_mm / 2.0 else "peripheral"


def side_code(left_right_offset_mm: float, lateral_sign: str) -> str:
    """Which side of the knee a thing lies on, from its offset and the laterality sign (pure -- pinned).

    `left_right_offset_mm` is the thing's centre minus the pair's centre along LPS +x (the
    patient's left); `lateral_sign` is `knee.objects.laterality.SIGN_CODES`' word for which way
    the outer side lies. A sign outside that vocabulary, or an offset that is not a finite
    number, is "invalid_measurement". A sign of `side_abstained` or `invalid_measurement`, or an
    offset of exactly zero, is "side_abstained": nothing is guessed. With the sign "left", a
    positive offset is "lateral" and a negative one "medial"; with "right", the reverse.

    post: __return__ in SIDE_CODES
    """
    if (
        isinstance(left_right_offset_mm, bool)
        or not isinstance(left_right_offset_mm, (int, float))
        or not math.isfinite(left_right_offset_mm)
        or lateral_sign not in SIGN_CODES
    ):
        return "invalid_measurement"
    if (
        lateral_sign in ("side_abstained", "invalid_measurement")
        or left_right_offset_mm == 0.0
    ):
        return "side_abstained"
    outward = (
        left_right_offset_mm > 0.0
        if lateral_sign == "left"
        else left_right_offset_mm < 0.0
    )
    return "lateral" if outward else "medial"


@dataclass(frozen=True, slots=True)
class Content:
    """One thing inside an interstice: a round-2 object, named by position and side only.

    `index`: 1.. within its interstice. `tiles`: bool (TR, TC). `centre_lps`: float64 (3,) mm.
    `position_code` from `POSITION_CODES`; `side_code` from `SIDE_CODES`.
    """

    index: int
    tiles: np.ndarray
    centre_lps: np.ndarray
    position_code: str
    side_code: str


@dataclass(frozen=True, slots=True)
class InterstitialRecord:
    """One facing pair's interstice on one chosen slice.

    `first`, `second`: the pair's territory labels. `extent`: bool (TR, TC). `first_wall_codes`,
    `second_wall_codes`: uint8 (N,) indexing `WALL_CODES`, one per profile of that object's
    strip whose normal points into the extent; empty where no strip was handed over.
    `fill_counts`: the conjunction words counted over the extent; `fill_code` from `FILL_CODES`.
    `contents`: the round-2 objects. `code` from `INTERSTICE_CODES`: `present`; `no_extent`
    when the pair faces across no tile at all; `predecessor_absent` when the facing pairs, the
    dome or the conjunction was not present. `border`: the dome's border word
    (`knee.objects.tile_dome.BORDER_CODES`) the pair was read under. Nothing here names anatomy.
    """

    series_uid: str
    slice_index: int
    first: int
    second: int
    code: str
    why: str
    extent: np.ndarray
    first_wall_codes: np.ndarray
    second_wall_codes: np.ndarray
    fill_counts: dict[str, int]
    fill_code: str
    contents: tuple[Content, ...]
    border: str


#: The stored index of the one conjunction word whose bodies are contents.
_BELOW_BELOW: int = CONJUNCTION_CODES.index("below_below")

#: A tile touches the four tiles it shares an edge with, never a corner.
_FOUR_CONNECTED: np.ndarray = ndimage.generate_binary_structure(2, 1)


@dataclass(frozen=True, slots=True)
class _Slice:
    """Everything one chosen slice supplies to its pairs, checked to agree once.

    `labels` int32 (TR, TC) and `usable` bool (TR, TC): the dome's territories, and the tiles an
    extent may hold beyond the gap (interior or obstacle, never cleared). `origin` float64 (3,):
    the first tile's centre in LPS mm; `relative` float64 (TR, TC, 3): every tile centre minus it
    (all geometry below is done in this frame, so tiles on one line share exactly one coordinate);
    `normal` float64 (3,): the grid's unit normal from its own row and column steps, None when
    the grid is a single row or column. `codes` uint8 (TR, TC): the conjunction at this slice,
    None when no conjunction was handed over. `border`: the dome's border word.
    """

    series_uid: str
    slice_index: int
    border: str
    labels: np.ndarray
    usable: np.ndarray
    origin: np.ndarray
    relative: np.ndarray
    normal: np.ndarray | None
    codes: np.ndarray | None
    strips: Mapping[int, Strip]
    lateral_sign: str


@dataclass(frozen=True, slots=True)
class _Pair:
    """One pair's geometry on its slice (measurement).

    `extent` bool (TR, TC). `first_centre` and `pair_centre` float64 (3,) in the slice's relative
    frame: the first territory's centre (a point on the axis) and the midpoint of the two centres.
    `across` float64 (3,): the unit direction in the slice plane perpendicular to the axis, None
    when the axis or the plane is undefined. `half_width_mm`: half the overlap of the two
    territories' widths across the axis, in mm; not positive when they do not overlap or when
    `across` is None.
    """

    extent: np.ndarray
    first_centre: np.ndarray
    pair_centre: np.ndarray
    across: np.ndarray | None
    half_width_mm: float


def _plane_normal(relative: np.ndarray) -> np.ndarray | None:
    """The unit normal of the tile grid from its own first row step and column step (measurement).

    `relative` float64 (TR, TC, 3). None when the grid is a single row or a single column, or its
    two steps do not span a plane.
    """
    if relative.shape[0] < 2 or relative.shape[1] < 2:
        return None
    normal = np.cross(relative[1, 0] - relative[0, 0], relative[0, 1] - relative[0, 0])
    length = float(np.linalg.norm(normal))
    if not math.isfinite(length) or length <= 0.0:
        return None
    return normal / length


def _pair_geometry(scene: _Slice, gap: np.ndarray, first: int, second: int) -> _Pair:
    """The extent of one pair, and the axis geometry its contents are placed by (measurement).

    The extent is the pair's gap tiles together with every usable tile between the territories
    along the line joining their centres: `knee.relations.facing.between_region`, the one rule the
    gap itself is cut from, held exactly in grid units. The axis, the across direction and the
    overlap of the widths are millimetre quantities from the tile centres, which any readings of
    position and side need.
    """
    in_first = scene.labels == first
    in_second = scene.labels == second
    first_centre = scene.relative[in_first].mean(axis=0)
    second_centre = scene.relative[in_second].mean(axis=0)
    pair_centre = (first_centre + second_centre) / 2.0
    extent = gap | (scene.usable & between_region(in_first, in_second))
    axis = second_centre - first_centre
    length = float(np.linalg.norm(axis))
    if scene.normal is None or not math.isfinite(length) or length <= 0.0:
        return _Pair(extent, first_centre, pair_centre, None, 0.0)
    across = np.cross(scene.normal, axis / length)
    width = float(np.linalg.norm(across))
    if not math.isfinite(width) or width <= 0.0:
        return _Pair(extent, first_centre, pair_centre, None, 0.0)
    across = across / width
    s = (scene.relative - first_centre) @ across
    low = max(float(s[in_first].min()), float(s[in_second].min()))
    high = min(float(s[in_first].max()), float(s[in_second].max()))
    return _Pair(extent, first_centre, pair_centre, across, (high - low) / 2.0)


def _neighbour_tiles(
    labels: np.ndarray, index: int, strip: Strip
) -> tuple[np.ndarray, np.ndarray]:
    """The tile each of an object's profiles enters, as the strip recorded it (measurement).

    `strip.beyond_tiles` int64 (N, 2) names, per profile, the tile (row, column) beyond the
    boundary segment the profile crosses (`knee.objects.strip.edge_points` writes it beside each
    point, one point per native pixel of boundary). Each must lie inside the grid and must not be
    the object's own tile, or the strip was not made from these labels: refused by name
    (`strip_disagrees_with_labels`). Returns the tile rows and tile columns, int64 (N,) each.
    """
    beyond = np.asarray(strip.beyond_tiles)
    count = np.shape(strip.edge_points)[0]
    if beyond.shape != (count, 2) or beyond.dtype.kind not in "iu":
        raise ValueError("strip_disagrees_with_labels")
    rows = beyond[:, 0].astype(np.int64)
    columns = beyond[:, 1].astype(np.int64)
    tiles_down, tiles_across = labels.shape
    inside = (
        (rows >= 0) & (rows < tiles_down) & (columns >= 0) & (columns < tiles_across)
    )
    if not inside.all() or (labels[rows, columns] == index).any():
        raise ValueError("strip_disagrees_with_labels")
    return rows, columns


def _wall_sequences(strip: Strip, into: np.ndarray) -> list[tuple[int, ...]]:
    """The digits each selected profile reads, from its band's far offset outward (measurement).

    `into` bool (N,): the profiles whose normals enter the extent. The far offset is the larger
    of the band's two offsets, the end of the band along the outward normal, found by exact match
    in `offsets_mm` (the band is cut from that very grid). A profile whose band was not
    bracketed reads silence along its whole length. Digits are plain ints.
    """
    offsets = np.asarray(strip.offsets_mm, dtype=np.float64)
    bracketed = TRACE_CODES["bracketed"]
    sequences: list[tuple[int, ...]] = []
    for n in np.flatnonzero(into):
        digits = strip.native_digits[n]
        band = np.asarray(strip.band_mm[n], dtype=np.float64)
        if int(strip.trace_codes[n]) != bracketed or not np.isfinite(band).all():
            sequences.append((SILENT,) * int(digits.size))
            continue
        starts = np.flatnonzero(offsets == float(band.max()))
        if starts.size != 1:
            raise ValueError("strip_band_off_the_offsets")
        sequences.append(tuple(int(value) for value in digits[int(starts[0]) :]))
    return sequences


def _check_strip(strip: Strip, key: int, scene: _Slice) -> None:
    """A strip must be this object's, on this slice, with arrays that agree in length (refusal)."""
    n = np.shape(strip.edge_points)[0]
    k = np.shape(strip.offsets_mm)[0]
    agree = (
        strip.object_index == key
        and strip.slice_index == scene.slice_index
        and strip.series_uid == scene.series_uid
        and strip.border == scene.border
        and np.shape(strip.edge_points) == (n, 2)
        and np.shape(strip.normals) == (n, 2)
        and np.shape(strip.band_mm) == (n, 2)
        and np.shape(strip.trace_codes) == (n,)
        and np.shape(strip.native_digits) == (n, k)
    )
    if not agree:
        raise ValueError("strip_disagrees_with_the_slice")


def _wall_codes(scene: _Slice, key: int, extent: np.ndarray) -> np.ndarray:
    """One object's wall, named profile by profile; empty where no strip was read (orchestration).

    Applies `wall_code` to each profile of the object's strip that enters the extent, in the
    strip's own order. Returns a newly owned, frozen uint8 (N,) indexing `WALL_CODES`.
    """
    strip = scene.strips.get(key)
    if strip is None or strip.code != "present":
        return handed_on(np.zeros(0, dtype=np.uint8))
    _check_strip(strip, key, scene)
    rows, columns = _neighbour_tiles(scene.labels, key, strip)
    sequences = _wall_sequences(strip, extent[rows, columns])
    names = [WALL_CODES.index(wall_code(sequence)) for sequence in sequences]
    return handed_on(np.array(names, dtype=np.uint8))


def _fill_counts(codes: np.ndarray | None, extent: np.ndarray) -> dict[str, int]:
    """The conjunction words counted over the extent's tiles; only words that occur (measurement)."""
    if codes is None:
        return {}
    tallied = np.bincount(
        codes[extent].astype(np.int64), minlength=len(CONJUNCTION_CODES)
    )
    return {
        word: int(tallied[k])
        for k, word in enumerate(CONJUNCTION_CODES)
        if tallied[k] > 0
    }


def _contents(scene: _Slice, geometry: _Pair) -> tuple[Content, ...]:
    """The four-connected bodies of `below_below` inside the extent, placed (orchestration).

    Each body's centre is the mean of its tiles' centres; its offset across the axis is the
    centre's component along `across` (not a number where the axis is undefined, which the
    position decision refuses by name); its left-right offset is the centre's LPS x minus the
    pair centre's. Both are plain floats. Arrays frozen; none when no conjunction.
    """
    if scene.codes is None:
        return ()
    labelled, count = ndimage.label(
        (scene.codes == _BELOW_BELOW) & geometry.extent, structure=_FOUR_CONNECTED
    )
    made = []
    for number in range(1, int(count) + 1):
        body = labelled == number
        centre = scene.relative[body].mean(axis=0)
        across = (
            float((centre - geometry.first_centre) @ geometry.across)
            if geometry.across is not None
            else math.nan
        )
        left_right = float(centre[0] - geometry.pair_centre[0])
        made.append(
            Content(
                index=number,
                tiles=handed_on(body),
                centre_lps=handed_on(scene.origin + centre),
                position_code=position_code(across, geometry.half_width_mm),
                side_code=side_code(left_right, scene.lateral_sign),
            )
        )
    return tuple(made)


def _wall_phrase(scene: _Slice, key: int, codes: np.ndarray) -> str:
    """Why an object's wall holds the profiles it does, in words (measurement).

    A wall with no profile is one of two silences: no strip was handed over for the object (or it
    held none), or a strip was read and no profile of it entered the extent. The words keep them
    apart, since the pinned record has one empty array for both.
    """
    strip = scene.strips.get(key)
    if strip is None:
        return f"no strip handed over for object {key}"
    if strip.code != "present":
        return f"the strip of object {key} is {strip.code}"
    return (
        f"{codes.size} of {len(strip.edge_points)} profiles of object {key} "
        "entered the extent"
    )


def _interstice(pair: FacingPair, scene: _Slice) -> InterstitialRecord:
    """One facing pair's interstice: extent, walls, fill and contents (orchestration)."""
    first, second = pair.first, pair.second
    gap = np.asarray(pair.gap_tiles)
    if (
        gap.shape != scene.labels.shape
        or gap.dtype != np.bool_
        or first == second
        or not (scene.labels == first).any()
        or not (scene.labels == second).any()
    ):
        raise ValueError("facing_disagrees_with_the_dome")
    geometry = _pair_geometry(scene, gap, first, second)
    extent = geometry.extent
    first_walls = _wall_codes(scene, first, extent)
    second_walls = _wall_codes(scene, second, extent)
    counts = _fill_counts(scene.codes, extent)
    fill = fill_code(counts)
    contents = _contents(scene, geometry)
    tiles = int(np.count_nonzero(extent))
    return InterstitialRecord(
        series_uid=scene.series_uid,
        slice_index=scene.slice_index,
        first=int(first),
        second=int(second),
        code="present" if tiles else "no_extent",
        why=(
            f"{tiles} extent tiles ({int(np.count_nonzero(gap))} of them gap tiles); walls: "
            f"{_wall_phrase(scene, first, first_walls)}, "
            f"{_wall_phrase(scene, second, second_walls)}; "
            f"fill {fill}; {len(contents)} contents"
        ),
        extent=handed_on(extent),
        first_wall_codes=first_walls,
        second_wall_codes=second_walls,
        fill_counts=counts,
        fill_code=fill,
        contents=contents,
        border=scene.border,
    )


def _scene(
    dome: TileDome,
    conjunction: Conjunction | None,
    centres_lps: np.ndarray,
    strips: Mapping[int, Strip],
    lateral_sign: str,
) -> _Slice:
    """The slice's records, checked to describe one grid, one series and one slice (refusals by name).

    A dome whose arrays are not one non-empty tile grid, centres that are not finite
    (TR, TC, 3) of that grid, or a conjunction of another series, another grid, or without this
    slice, or holding a code the vocabulary does not have, are contradictions between records,
    refused by name.
    """
    labels = np.asarray(dome.labels)
    arrays = (dome.obstacle, dome.cleared, dome.interior)
    if (
        labels.ndim != 2
        or labels.size == 0
        or any(np.shape(array) != labels.shape for array in arrays)
    ):
        raise ValueError("dome_arrays_disagree")
    centres = np.asarray(centres_lps, dtype=np.float64)
    if centres.shape != (*labels.shape, 3) or not np.isfinite(centres).all():
        raise ValueError("centres_lps_disagree_with_the_dome")
    codes = None
    if conjunction is not None:
        stored = np.asarray(conjunction.codes)
        if (
            conjunction.recipient_uid != dome.series_uid
            or stored.ndim != 3
            or not 0 <= dome.slice_index < stored.shape[0]
            or stored.shape[1:] != labels.shape
        ):
            raise ValueError("conjunction_disagrees_with_the_dome")
        codes = stored[dome.slice_index]
        if int(codes.max()) >= len(CONJUNCTION_CODES):
            raise ValueError("conjunction_code_unknown")
    origin = centres[0, 0].copy()
    relative = centres - origin
    usable = (
        np.asarray(dome.interior, dtype=bool) | np.asarray(dome.obstacle, dtype=bool)
    ) & ~np.asarray(dome.cleared, dtype=bool)
    return _Slice(
        series_uid=dome.series_uid,
        slice_index=int(dome.slice_index),
        border=dome.border,
        labels=labels,
        usable=usable,
        origin=origin,
        relative=relative,
        normal=_plane_normal(relative),
        codes=codes,
        strips=strips,
        lateral_sign=lateral_sign,
    )


def _absent_reasons(
    facing: FacingPairs, dome: TileDome, conjunction: Conjunction | None
) -> list[str]:
    """Which predecessor was not there to read, in words; empty when each was (measurement).

    The facing pairs and the dome are absent when their code says so; a conjunction is absent
    only when it was handed over and its code is not `present` (none handed over is a plane
    with no pair, whose fill is unread, not an absence).
    """
    reasons = []
    if facing.code not in ("present", "no_pair"):
        reasons.append(f"the facing pairs are {facing.code} ({facing.why})")
    if dome.code not in ("present", "no_interior"):
        reasons.append(f"the tile dome is {dome.code} ({dome.why})")
    if conjunction is not None and conjunction.code != "present":
        reasons.append(f"the conjunction is {conjunction.code} ({conjunction.why})")
    return reasons


def _absent(dome: TileDome, reasons: list[str]) -> InterstitialRecord:
    """The record of a slice with a predecessor missing: its named silence, empty arrays of rank."""
    return InterstitialRecord(
        series_uid=dome.series_uid,
        slice_index=int(dome.slice_index),
        first=0,
        second=0,
        code="predecessor_absent",
        why="; ".join(reasons) + "; no pair was examined",
        extent=handed_on(np.zeros((0, 0), dtype=np.bool_)),
        first_wall_codes=handed_on(np.zeros(0, dtype=np.uint8)),
        second_wall_codes=handed_on(np.zeros(0, dtype=np.uint8)),
        fill_counts={},
        fill_code=fill_code({}),
        contents=(),
        border=dome.border,
    )


def read_interstices(
    facing: FacingPairs,
    dome: TileDome,
    conjunction: Conjunction | None,
    centres_lps: np.ndarray,
    strips: Mapping[int, Strip],
    lateral_sign: str,
) -> tuple[InterstitialRecord, ...]:
    """One interstice per facing pair of one chosen slice (orchestration).

    `centres_lps` is the slice's tile centres, float64 (TR, TC, 3); `strips` maps an object
    label to its strip where one was read; `lateral_sign` is the selection's sign. Records
    `facing.consumed_by.interstice`, `tile_dome.consumed_by.interstice`, and, only when handed
    over, `conjunction.consumed_by.interstice` and `strip.consumed_by.interstice`, each at the
    point of reading. For each pair whose code is `facing`: the extent as the module docstring
    defines it, from the pair's gap tiles, the dome's labels and the tile centres; the walls from
    the strips of the two objects, the profiles whose normals point into the extent, each
    profile's digits from its band's far offset outward (silence where the band was not
    bracketed), named by `wall_code`; the fill from the conjunction codes over the extent
    (`fill_unread` throughout when no conjunction was handed over); the contents as the
    four-connected bodies of `below_below` tiles inside the extent (none when no conjunction),
    each with its centre, `position_code` against the pair's axis and the overlap of the two
    objects' widths across it, and `side_code` with the sign. A pair that is not `facing` gets no
    record. Arrays frozen. Then records `interstice.produced` (interstices: how many are
    `present`; contents: how many in all). Decides nothing beyond applying the four decisions.
    """
    held = {} if strips is None else strips
    # The consumer records what it read at the point of reading (`specs/route-composition`): the
    # facing pairs and the dome are always handed over and the count says whether each held a
    # reading; the conjunction and the strips are recorded only when handed over.
    ledger.record(
        "facing.consumed_by.interstice", facing=1 if facing.code == "present" else 0
    )
    ledger.record(
        "tile_dome.consumed_by.interstice", dome=1 if dome.code == "present" else 0
    )
    if conjunction is not None:
        ledger.record(
            "conjunction.consumed_by.interstice",
            conjunction=1 if conjunction.code == "present" else 0,
        )
    if held:
        ledger.record(
            "strip.consumed_by.interstice",
            strips=sum(1 for strip in held.values() if strip.code == "present"),
        )
    reasons = _absent_reasons(facing, dome, conjunction)
    if reasons:
        records: tuple[InterstitialRecord, ...] = (_absent(dome, reasons),)
    else:
        records = _interstices(
            facing, dome, conjunction, centres_lps, held, lateral_sign
        )
    ledger.record(
        "interstice.produced",
        interstices=sum(1 for record in records if record.code == "present"),
        contents=sum(len(record.contents) for record in records),
    )
    return records


def _interstices(
    facing: FacingPairs,
    dome: TileDome,
    conjunction: Conjunction | None,
    centres_lps: np.ndarray,
    strips: Mapping[int, Strip],
    lateral_sign: str,
) -> tuple[InterstitialRecord, ...]:
    """The interstices themselves, once every predecessor is there: one per facing pair."""
    if (
        facing.series_uid != dome.series_uid
        or facing.slice_index != dome.slice_index
        or facing.border != dome.border
    ):
        raise ValueError("facing_and_dome_disagree")
    pairs = tuple(pair for pair in facing.pairs if pair.code == "facing")
    if not pairs:
        return ()
    scene = _scene(dome, conjunction, centres_lps, strips, lateral_sign)
    return tuple(_interstice(pair, scene) for pair in pairs)


__all__ = [
    "FILL_CODES",
    "INTERSTICE_CODES",
    "POSITION_CODES",
    "SIDE_CODES",
    "WALL_CODES",
    "Content",
    "InterstitialRecord",
    "fill_code",
    "position_code",
    "read_interstices",
    "side_code",
    "wall_code",
]
