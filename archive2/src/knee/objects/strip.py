"""The strip: the exact edge of an object, read at native resolution only along its tile boundary.

**Why it exists, against the thesis.** The founder, 2026-10-12: "We are doing two things--(1)
high-level localization and targeting, and (2) fine-grained targeting and boundary-drawing. The
"squint" view is WAAAAY cheaper ... you only spend expensive compute to try and find the exact
boundary of things in the places where they actually look like they might exist." And on what the
expensive reading is (the same day, of the two high-resolution lenses): "When it comes to the
high-level resolution of the boundaries of the bones, the expensive stuff, this is REFINED. I
mean, LOOK at the boundary there." The native machinery exists (`knee.objects.profiles.
sample_profiles`, the profiles cast across a border; `knee.objects.interiors.dark_bands`, the
bracketed dark band a profile crosses); what changes is WHERE it runs: only in a strip along each
selected object's tile boundary, never over the whole plane.

**The rule.** For one object of one chosen slice: a point at every native pixel along each of its
tile boundary segments, with the segment's outward normal (one cast per pixel of boundary, so the
edge is drawn at native resolution and a break between two tile midpoints is not missed: the Codex
check of 2026-10-13 and the strip builder both caught the first wording, one cast per segment,
which put the casts a tile apart); at each, a profile cast across the boundary at native
resolution over offsets spanning plus and minus `strip_mm`; each profile read for its dark band by
the existing rule, its outcome a word of `TRACE_CODES` and the band's extent in millimetres; the
strip's own samples read as digits against the terciles of the object's own pixels (the founder,
2026-10-13: "then each object's own places"); and the strip's footprint on the plane. Nothing
outside the strip is read at native resolution.

**What it does not do, yet.** The partner's bands carried to the same points (task 6.2) is not
built: `knee.objects.conversation.exchange` needs both planes' frames, the partner's own split and
its slab thickness, and its design is open; until it is, a partner handed over is refused by name
and `exchange_codes` is always empty. It does not pull the outline taut (task 6.4, the thesis
§6.1's three pulls, a later unit with its own contract after the lead reads §6.1 whole), and it
reads nothing inside the object except the object's own pixels for its terciles.

This is the funnel's operation 6 (`openspec/changes/the-funnel/design.md` R6, tasks 6.1 to 6.3).
`edge_points` is the first measurement (it carries the contract), `read_strip` the orchestration
over the existing profile, band and digit machinery.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from knee.collapse.physical import numeric_plane, spacing_pair
from knee.collapse.regime import tercile_edges
from knee.compute.contracts import ComputeContract, contracted, handed_on
from knee.lenses.places import DIGIT_VALUES, place_codes_reference
from knee.objects.interiors import EDGE_KINDS, TRACE_CODES, dark_bands
from knee.objects.profiles import ProfileReading, sample_profiles
from knee.objects.tile_dome import BORDER_CODES
from knee.telemetry import ledger

#: What one object's strip reports as a whole.
STRIP_CODES: tuple[str, ...] = ("present", "no_boundary", "predecessor_absent")

CONTRACT = ComputeContract(
    kind="measurement",
    language="NumPy over the tile label grid and the saved native bounds; no twin",
    reads="labels int32 (TR, TC), bounds_rc int64 (TR, TC, 4), object_index",
    writes="edge_points float64 (N, 2) native rc, normals float64 (N, 2), beyond int64 (N, 2) "
    "tile rc",
    allocation="one (N, 2) float64 pair, N the native pixels along the object's boundary "
    "segments",
    work="one four-neighbour comparison over TR * TC tiles, then one point per boundary pixel",
    parallel_unit="object",
    reference="edge_points",
    proof_gate="tests/knee/objects/test_strip.py: a 2 x 2 block of tiles in a 4 x 4 grid gives "
    "eight boundary segments and one point at every native pixel along each, lying on the "
    "block's native edges, with normals pointing away from the block and the tile beyond named "
    "for each; a tile on the picture's frame has no segment on the frame side; an object with no "
    "tile gives no point; no input is written",
)


@contracted
def edge_points(
    labels: np.ndarray, bounds_rc: np.ndarray, object_index: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """A point at every native pixel along one object's tile boundary segments, with outward normals.

    A boundary segment is the shared edge between a tile labelled `object_index` and a
    four-neighbour tile not so labelled (the picture's frame is not a segment: the lens's
    cleared air lies between the knee and the frame, so every object edge has a tile beyond
    it). Native coordinates are pixel-centre coordinates: a tile holds the pixels r0 .. r1 - 1
    and c0 .. c1 - 1 of `bounds_rc`'s half-open bounds, and the edge it shares with the tile
    beyond lies half a pixel past its last (or before its first) pixel. A segment above or below
    the tile gives one point at each of its pixel columns c0 .. c1 - 1, at row r0 - 0.5 or
    r1 - 0.5; a segment left or right of it one point at each of its pixel rows r0 .. r1 - 1, at
    column c0 - 0.5 or c1 - 0.5. Each point's normal is the unit vector from the object's tile
    into the neighbour's, (±1, 0) or (0, ±1), and `beyond` names that neighbour tile, (tile row,
    tile column), so a later stage knows which tile each profile enters without replaying the
    segments. Points in scan order of the object's tiles, then up, down, left, right, then along
    the segment in increasing pixel order. Returned float64 (N, 2), float64 (N, 2) and int64
    (N, 2), frozen. An `object_index` that is not a positive int, or shapes that disagree, is
    refused by name (`invalid_object_index`, `strip_inputs_disagree`).

    pre: labels.ndim == 2 and bounds_rc.ndim == 3
    post: __return__[0].shape == __return__[1].shape == __return__[2].shape
    """
    index = _object_index(object_index)
    grid, bounds = _agreeing_grids(labels, bounds_rc)
    mine = grid == index
    # One flag per tile side, in the order up, down, left, right. A side is a segment when the
    # tile is the object's and its neighbour on that side exists and is not. A tile on the
    # picture's frame has no neighbour there, so the slices leave the frame side False.
    sides = np.zeros((*mine.shape, 4), dtype=bool)
    sides[1:, :, 0] = mine[1:, :] & ~mine[:-1, :]
    sides[:-1, :, 1] = mine[:-1, :] & ~mine[1:, :]
    sides[:, 1:, 2] = mine[:, 1:] & ~mine[:, :-1]
    sides[:, :-1, 3] = mine[:, :-1] & ~mine[:, 1:]
    # `nonzero` walks the array in C order: tiles in scan order, then the four sides in turn.
    tile_row, tile_column, side = np.nonzero(sides)
    r0, r1, c0, c1 = bounds[tile_row, tile_column].astype(np.int64).T
    # A segment above or below runs along the tile's pixel columns; one left or right along its
    # pixel rows. One point per pixel along it, in increasing pixel order.
    lengths = np.where(side < 2, c1 - c0, r1 - r0).clip(min=0)
    segment = np.repeat(np.arange(side.size), lengths)
    step = np.arange(int(lengths.sum())) - np.repeat(
        np.cumsum(lengths) - lengths, lengths
    )
    s = side[segment]
    rows = np.where(
        s == 0,
        r0[segment] - 0.5,
        np.where(s == 1, r1[segment] - 0.5, r0[segment] + step),
    ).astype(np.float64)
    columns = np.where(
        s == 2,
        c0[segment] - 0.5,
        np.where(s == 3, c1[segment] - 0.5, c0[segment] + step),
    ).astype(np.float64)
    normals = _SIDE_STEPS[s]
    beyond = np.column_stack((tile_row[segment], tile_column[segment])).astype(
        np.int64
    ) + normals.astype(np.int64)
    return (
        handed_on(np.column_stack((rows, columns))),
        handed_on(normals),
        handed_on(beyond),
    )


@dataclass(frozen=True, slots=True)
class Strip:
    """One object's strip on one chosen slice, under one border.

    `series_uid`, `slice_index`: the series and the chosen slice the object's territory is on.
    `edge_points`, `normals`: float64 (N, 2). `beyond_tiles`: int64 (N, 2), the tile (row,
    column) each profile enters across its boundary segment. `offsets_mm`: float64 (K,), the native offsets the
    profiles were cast at, from -strip_mm to +strip_mm at the plane's pixel pitch. `profiles`:
    float64 (N, K), the plane's values along each cast, NaN where the cast leaves the plane.
    `trace_codes`: uint8 (N,) indexing `TRACE_CODES`; `band_mm`: float64 (N, 2), the bracketed
    dark band's near and far offsets, NaN where not bracketed. `exchange_codes`: uint8 (0,), empty
    until the partner's bands are brought to the points (task 6.2, not built). `native_digits`:
    int8 (N, K), each profile sample against the terciles of the object's own pixels (-1, 0, +1,
    2 silence); `low_edge`, `high_edge`, `population_count`: those terciles and their population.
    `strip_mask`: bool (R, C), the native pixels any cast touched. `code` from `STRIP_CODES`:
    `present`; `no_boundary` when the object has no boundary segment; `predecessor_absent` when
    the plane, the labels or the bounds were not there. Arrays empty with the right rank where
    absent. `border`: the dome's border word (`knee.objects.tile_dome.BORDER_CODES`) whose
    territory this object is.
    """

    series_uid: str
    slice_index: int
    object_index: int
    code: str
    why: str
    strip_mm: float
    edge_points: np.ndarray
    normals: np.ndarray
    offsets_mm: np.ndarray
    profiles: np.ndarray
    trace_codes: np.ndarray
    band_mm: np.ndarray
    exchange_codes: np.ndarray
    native_digits: np.ndarray
    low_edge: float
    high_edge: float
    population_count: int
    strip_mask: np.ndarray
    beyond_tiles: np.ndarray
    border: str


def read_strip(
    plane: np.ndarray,
    spacing_rc: tuple[float, float],
    labels: np.ndarray,
    bounds_rc: np.ndarray,
    object_index: int,
    strip_mm: float,
    split: float,
    prominence_native_mm: float,
    minimum_population: int,
    partner_plane: np.ndarray | None,
    partner_spacing_rc: tuple[float, float] | None,
    *,
    series_uid: str,
    slice_index: int,
    border: str,
) -> Strip:
    """One object's native edge, read only in the strip along its tile boundary (orchestration).

    Refused by name before any ledger event: `strip_mm` or `prominence_native_mm` that is not a
    finite positive number (`invalid_strip_mm`, `invalid_prominence_native_mm`); a
    `minimum_population` that is not a non-negative int (`invalid_minimum_population`); an
    `object_index` that is not a positive int (`invalid_object_index`); a `split` that is not a
    finite number (`invalid_split`: no valley, no band to read under); a `series_uid` that is not
    text, a `slice_index` that is not a non-negative int, or a `border` outside
    `knee.objects.tile_dome.BORDER_CODES` (`invalid_series_uid`, `invalid_slice_index`,
    `invalid_border`); a `partner_plane` or `partner_spacing_rc` that is not None
    (`partner_exchange_not_built`: task 6.2 is open, so nothing pretends to carry a partner).
    Records `tile_dome.consumed_by.strip` (labels: 1) at the point of reading, and
    `study.consumed_by.strip` (plane: 1), each only for a record handed over. `edge_points` gives
    the points and normals; `no_boundary` when none. The profiles are cast by
    `knee.objects.profiles.sample_profiles` with the offsets every pixel pitch (the finer axis's)
    from -strip_mm to +strip_mm; each is read for its dark band by
    `knee.objects.interiors.dark_bands` under `split`, giving `trace_codes` and `band_mm` (a cast
    that leaves the plane is `frame_clipped`). `prominence_native_mm` is validated and unused,
    because `dark_bands` takes no prominence; the record's `why` says so. The object's own pixels
    are the finite native pixels inside its tiles' bounds; their terciles by
    `knee.collapse.regime.tercile_edges(values, minimum_population)` give the edges, and
    `native_digits = DIGIT_VALUES[place_codes_reference(profiles, low, high, count,
    minimum_population)]`. `strip_mask` marks every native pixel any cast sampled. The strip
    carries `series_uid`, `slice_index` and `border` as given. Arrays frozen. Then records
    `strip.produced` (points: N; bracketed: how many trace codes are `bracketed`). Decides
    nothing itself.
    """
    # Every refusal comes before the first ledger event: a refused call read nothing.
    strip_width = _finite_positive(strip_mm, "invalid_strip_mm")
    _finite_positive(prominence_native_mm, "invalid_prominence_native_mm")
    minimum = _non_negative_int(minimum_population, "invalid_minimum_population")
    index = _object_index(object_index)
    split_value = _split_value(split)
    if type(series_uid) is not str:
        raise ValueError("invalid_series_uid")
    slice_number = _non_negative_int(slice_index, "invalid_slice_index")
    if not isinstance(border, str) or border not in BORDER_CODES:
        raise ValueError("invalid_border")
    if partner_plane is not None or partner_spacing_rc is not None:
        raise ValueError("partner_exchange_not_built")
    held_plane, held_labels, held_bounds = (
        _held(plane),
        _held(labels),
        _held(bounds_rc),
    )
    spacing = offsets = None
    if held_plane:
        numeric_plane(plane)
        spacing = spacing_pair(spacing_rc)
        offsets = _offsets(strip_width, spacing)
    if held_labels and held_bounds:
        _agreeing_grids(labels, bounds_rc)
    # The consumer records what it read at the point of reading, and only for a record that was
    # handed over: not for a None, and not for an empty array.
    if held_labels:
        ledger.record("tile_dome.consumed_by.strip", labels=1)
    if held_plane:
        ledger.record("study.consumed_by.strip", plane=1)
    where = _Where(series_uid, slice_number, border)
    if spacing is None or offsets is None or not (held_labels and held_bounds):
        strip = _absent_strip(
            where, index, strip_width, held_plane, held_labels, held_bounds
        )
    else:
        strip = _read_strip(
            where,
            plane,
            spacing,
            offsets,
            labels,
            bounds_rc,
            index,
            strip_width,
            split_value,
            float(prominence_native_mm),
            minimum,
        )
    ledger.record(
        "strip.produced",
        points=len(strip.edge_points),
        bracketed=int(np.count_nonzero(strip.trace_codes == TRACE_CODES["bracketed"])),
    )
    return strip


#: The unit step from a tile into the neighbour beyond each of its four sides, (row, column), in
#: the order `edge_points` emits the sides: up, down, left, right. These are the outward normals.
_SIDE_STEPS: np.ndarray = handed_on(
    np.array([[-1.0, 0.0], [1.0, 0.0], [0.0, -1.0], [0.0, 1.0]])
)


@dataclass(frozen=True, slots=True)
class _Where:
    """The series, the chosen slice and the border a strip is read for, as `read_strip` was given them."""

    series_uid: str
    slice_index: int
    border: str


def _finite_positive(value: object, name: str) -> float:
    """The value as a float when it is a finite positive number that is not a bool, else refused by name."""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float, np.integer, np.floating))
        or not np.isfinite(value)
        or value <= 0
    ):
        raise ValueError(name)
    return float(value)


def _non_negative_int(value: object, name: str) -> int:
    """The value as an int when it is a whole number at or above zero that is not a bool, else refused."""
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < 0:
        raise ValueError(name)
    return int(value)


def _object_index(value: object) -> int:
    """The object index when it is a positive int that is not a bool, else `invalid_object_index`."""
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < 1:
        raise ValueError("invalid_object_index")
    return int(value)


def _agreeing_grids(labels: object, bounds_rc: object) -> tuple[np.ndarray, np.ndarray]:
    """The label grid and the bounds as arrays when they describe one tile grid, else `strip_inputs_disagree`.

    The grid is two-dimensional (TR, TC), the bounds (TR, TC, 4), both integers as the contract
    reads them (labels int32, bounds int64: a half-open pixel bound is a whole number, and a
    float one could carry a NaN into a point), and the tile counts agree. Nothing is copied or
    written.
    """
    grid, bounds = np.asarray(labels), np.asarray(bounds_rc)
    if (
        grid.ndim != 2
        or bounds.ndim != 3
        or bounds.shape[2] != 4
        or bounds.shape[:2] != grid.shape
        or grid.dtype.kind not in "iu"
        or bounds.dtype.kind not in "iu"
    ):
        raise ValueError("strip_inputs_disagree")
    return grid, bounds


def _held(value: object) -> bool:
    """Whether a predecessor was handed over: a non-empty array, neither None nor an empty one."""
    return isinstance(value, np.ndarray) and value.size > 0


def _split_value(split: object) -> float:
    """The split as a float when it is a finite number that is not a bool, else `invalid_split`."""
    if (
        isinstance(split, (bool, np.bool_))
        or not isinstance(split, (int, float, np.integer, np.floating))
        or not np.isfinite(split)
    ):
        raise ValueError("invalid_split")
    return float(split)


def _offsets(strip_width: float, spacing: tuple[float, float]) -> np.ndarray:
    """The cast offsets in millimetres, symmetric about the boundary and containing 0, float64 (K,).

    Every pixel pitch from -strip_mm to +strip_mm: `pitch * arange(-n, n + 1)` for the largest
    n with n * pitch within the strip, so 0 is exact and the two sides are mirror images. The
    pitch is the finer of the two axes' spacings, which never undersamples either axis.
    """
    pitch = min(spacing)
    ratio = strip_width / pitch
    if not np.isfinite(ratio):
        raise ValueError("invalid_strip_mm")
    # Rounding in the quotient must not drop the last whole pitch inside the strip.
    reach = int(np.floor(ratio + 8 * np.finfo(np.float64).eps * max(1.0, ratio)))
    return handed_on(pitch * np.arange(-reach, reach + 1, dtype=np.float64))


def _cast_coordinates(
    points: np.ndarray,
    normals: np.ndarray,
    offsets: np.ndarray,
    spacing: tuple[float, float],
) -> tuple[np.ndarray, np.ndarray]:
    """Where every sample of every cast lies in native pixel coordinates, each float64 (N, K).

    The sampler's own expression, `point + offset * normal / spacing`, in the same order, so the
    coordinates are the ones `sample_profiles` evaluates and not a second reckoning of them.
    """
    rows = points[:, 0, None] + offsets[None, :] * normals[:, 0, None] / spacing[0]
    columns = points[:, 1, None] + offsets[None, :] * normals[:, 1, None] / spacing[1]
    return rows, columns


def _inside(
    rows: np.ndarray, columns: np.ndarray, shape: tuple[int, ...]
) -> np.ndarray:
    """Which samples lie on the plane, bool (N, K): the sampler's own bounds, 0 to size - 1."""
    return (
        (rows >= 0)
        & (columns >= 0)
        & (rows <= shape[0] - 1)
        & (columns <= shape[1] - 1)
    )


def _footprint(
    rows: np.ndarray, columns: np.ndarray, inside: np.ndarray, shape: tuple[int, ...]
) -> np.ndarray:
    """Every native pixel a cast reads, bool (R, C): the sampler's positive-weight corners.

    A sample at (row, column) reads the pixel at the floor of each and, where the fraction is
    not zero, the one beyond it; a corner with weight 0 is not read. Samples off the plane read
    nothing. The mask is the read set and carries no value from the plane.
    """
    row, column = rows[inside], columns[inside]
    row0, column0 = np.floor(row).astype(np.int64), np.floor(column).astype(np.int64)
    row_part, column_part = row - row0, column - column0
    mask = np.zeros(shape, dtype=bool)
    for row_step in (0, 1):
        for column_step in (0, 1):
            weight = (row_part if row_step else 1.0 - row_part) * (
                column_part if column_step else 1.0 - column_part
            )
            used = weight > 0
            mask[row0[used] + row_step, column0[used] + column_step] = True
    return handed_on(mask)


def _own_pixels(
    plane: np.ndarray, labels: np.ndarray, bounds_rc: np.ndarray, index: int
) -> np.ndarray:
    """The finite native pixels inside the object's tiles' bounds, float64 (M,), and nothing outside."""
    tile_row, tile_column = np.nonzero(np.asarray(labels) == index)
    parts = []
    for i, j in zip(tile_row.tolist(), tile_column.tolist(), strict=True):
        r0, r1, c0, c1 = (max(int(bound), 0) for bound in bounds_rc[i, j])
        block = plane[r0:r1, c0:c1]
        parts.append(block[np.isfinite(block)])
    if not parts:
        return np.empty(0, dtype=np.float64)
    return np.concatenate(parts).astype(np.float64)


def _read_bands(
    profiles: ProfileReading,
    split: float,
    clipped: np.ndarray,
    points: np.ndarray,
    normals: np.ndarray,
    spacing: tuple[float, float],
) -> tuple[np.ndarray, np.ndarray]:
    """Each cast's dark band (near and far offsets, mm) and its `TRACE_CODES` outcome.

    A cast that leaves the plane is named `frame_clipped`: `dark_bands` names that only for a row
    whose kind is the frame, so the kind is set from the samples that fell off the plane. The
    split is finite here: `read_strip` refused any other.
    """
    kinds = np.where(clipped, EDGE_KINDS["frame"], 0).astype(np.uint8)
    lower, upper, _centres, codes = dark_bands(
        profiles, split, kinds, points, normals, np.asarray(spacing)
    )
    return handed_on(np.column_stack((lower, upper))), codes


def _empty_strip(
    where: _Where,
    code: str,
    why: str,
    index: int,
    strip_width: float,
    offsets: np.ndarray,
    shape: tuple[int, ...],
    terciles: tuple[float, float, int],
) -> Strip:
    """A strip with no cast: every array empty with the right rank, every one frozen."""
    width = int(offsets.size)
    low, high, count = terciles
    return Strip(
        series_uid=where.series_uid,
        slice_index=where.slice_index,
        object_index=index,
        code=code,
        why=why,
        strip_mm=strip_width,
        edge_points=handed_on(np.empty((0, 2))),
        normals=handed_on(np.empty((0, 2))),
        offsets_mm=offsets,
        profiles=handed_on(np.empty((0, width))),
        trace_codes=handed_on(np.empty(0, dtype=np.uint8)),
        band_mm=handed_on(np.empty((0, 2))),
        exchange_codes=handed_on(np.empty(0, dtype=np.uint8)),
        native_digits=handed_on(np.empty((0, width), dtype=np.int8)),
        low_edge=low,
        high_edge=high,
        population_count=count,
        strip_mask=handed_on(np.zeros(shape, dtype=bool)),
        beyond_tiles=handed_on(np.empty((0, 2), dtype=np.int64)),
        border=where.border,
    )


def _absent_strip(
    where: _Where,
    index: int,
    strip_width: float,
    held_plane: bool,
    held_labels: bool,
    held_bounds: bool,
) -> Strip:
    """The strip of an object whose plane, labels or bounds were not there, naming which."""
    missing = [
        name
        for name, held in (
            ("plane", held_plane),
            ("labels", held_labels),
            ("bounds", held_bounds),
        )
        if not held
    ]
    return _empty_strip(
        where,
        "predecessor_absent",
        f"no {', '.join(missing)} was handed over, so no cast was made",
        index,
        strip_width,
        handed_on(np.empty(0)),
        (0, 0),
        (float("nan"), float("nan"), 0),
    )


def _number(value: float) -> str:
    """A reading as text; NaN is how a reading not made reads."""
    return "not read" if np.isnan(value) else f"{value:g}"


def _read_strip(
    where: _Where,
    plane: np.ndarray,
    spacing: tuple[float, float],
    offsets: np.ndarray,
    labels: np.ndarray,
    bounds_rc: np.ndarray,
    index: int,
    strip_width: float,
    split: float,
    prominence: float,
    minimum: int,
) -> Strip:
    """The strip itself, once the plane, the labels and the bounds were all handed over."""
    points, normals, beyond = edge_points(labels, bounds_rc, index)
    terciles = tercile_edges(_own_pixels(plane, labels, bounds_rc, index), minimum)
    low, high, count = terciles
    if not len(points):
        return _empty_strip(
            where,
            "no_boundary",
            f"object {index} has no boundary segment on this grid (no tile of it, or it "
            "fills every tile), so no cast was made",
            index,
            strip_width,
            offsets,
            plane.shape,
            terciles,
        )
    profiles = sample_profiles(plane, points, normals, offsets, spacing)
    rows, columns = _cast_coordinates(points, normals, offsets, spacing)
    inside = _inside(rows, columns, plane.shape)
    band_mm, trace_codes = _read_bands(
        profiles, split, ~inside.all(axis=1), points, normals, spacing
    )
    native_digits = handed_on(
        DIGIT_VALUES[place_codes_reference(profiles.samples, low, high, count, minimum)]
    )
    bracketed = int(np.count_nonzero(trace_codes == TRACE_CODES["bracketed"]))
    why = (
        f"{len(points)} edge points of object {index} (one per native pixel along its tile "
        f"boundary), each cast at {offsets.size} offsets every {min(spacing):g} mm out to "
        f"{offsets[-1]:g} mm on either side; bands read under split {split:g}, {bracketed} "
        f"bracketed; native terciles ({_number(low)}, {_number(high)}) of {count} own pixels "
        f"(minimum {minimum}); no partner band is carried (task 6.2 is not built); "
        f"prominence_native_mm {prominence:g} is validated and unused, because dark_bands "
        "takes no prominence"
    )
    return Strip(
        series_uid=where.series_uid,
        slice_index=where.slice_index,
        object_index=index,
        code="present",
        why=why,
        strip_mm=strip_width,
        edge_points=points,
        normals=normals,
        offsets_mm=offsets,
        profiles=profiles.samples,
        trace_codes=trace_codes,
        band_mm=band_mm,
        exchange_codes=handed_on(np.empty(0, dtype=np.uint8)),
        native_digits=native_digits,
        low_edge=low,
        high_edge=high,
        population_count=count,
        strip_mask=_footprint(rows, columns, inside, plane.shape),
        beyond_tiles=beyond,
        border=where.border,
    )


__all__ = [
    "CONTRACT",
    "STRIP_CODES",
    "TRACE_CODES",
    "Strip",
    "edge_points",
    "read_strip",
]
